"""Authentication and hardening helpers for the dashboard.

Design goals, in order: fail closed, no new dependencies, small enough to audit
at a glance. A single shared secret (DASHBOARD_AUTH_TOKEN) is exchanged for a
signed, HttpOnly session cookie; non-browser clients may send the same secret
as a bearer token instead. Cookie-authenticated writes additionally require a
double-submit CSRF token.

Nothing in this module talks to OPC-UA, the ESP32 or the database.
"""

import base64
import hashlib
import hmac
import os
import secrets
import sys
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, WebSocket, WebSocketException
from starlette.datastructures import MutableHeaders

# Importable both as "python dashboard/app.py" and "uvicorn dashboard.app:app".
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dashboard.config import SETTINGS

SESSION_COOKIE = "wb_session"
CSRF_COOKIE = "wb_csrf"
CSRF_HEADER = "X-CSRF-Token"
WS_CLOSE_UNAUTHORIZED = 1008


# --------------------------------------------------------------------------
# secret comparison
# --------------------------------------------------------------------------

def token_matches(candidate):
    """Constant-time comparison against the configured shared secret."""
    if not SETTINGS.auth_token:
        return True
    if not candidate:
        return False
    return hmac.compare_digest(
        candidate.encode("utf-8"), SETTINGS.auth_token.encode("utf-8")
    )


# --------------------------------------------------------------------------
# stateless signed session cookie (stdlib hmac only)
# --------------------------------------------------------------------------

def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _session_key():
    # Derived from the shared token so rotating the token also invalidates
    # every issued session, without storing anything new.
    return hashlib.sha256(("wb-dashboard-session:" + SETTINGS.auth_token).encode("utf-8")).digest()


def issue_session():
    # The nonce is not decoration: without it two logins inside the same
    # second would produce byte-identical sessions, so logging out of one
    # device would revoke the other one's session too.
    payload = f"{int(time.time())}.{secrets.token_urlsafe(8)}"
    signature = hmac.new(_session_key(), payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_b64(signature)}"


# Signing alone cannot make a cookie stop working, so logout records the
# session id here until it would have expired anyway. In-memory on purpose: a
# restart re-opens nothing, it just forgets that a logout happened, and the
# cookie's own Max-Age still bounds the exposure.
_REVOKED_SESSIONS = {}
_REVOKED_LOCK = threading.Lock()
MAX_REVOKED_SESSIONS = 512


def revoke_session(value, max_age_s=None):
    if not value:
        return
    if max_age_s is None:
        max_age_s = SETTINGS.session_max_age_s
    expires_at = time.time() + max_age_s
    with _REVOKED_LOCK:
        expired = [k for k, v in _REVOKED_SESSIONS.items() if v <= time.time()]
        for key in expired:
            del _REVOKED_SESSIONS[key]
        while len(_REVOKED_SESSIONS) >= MAX_REVOKED_SESSIONS:
            del _REVOKED_SESSIONS[min(_REVOKED_SESSIONS, key=_REVOKED_SESSIONS.get)]
        _REVOKED_SESSIONS[value] = expires_at


def is_revoked(value):
    with _REVOKED_LOCK:
        return value in _REVOKED_SESSIONS


def verify_session(value, max_age_s=None):
    if max_age_s is None:
        max_age_s = SETTINGS.session_max_age_s
    try:
        issued, _nonce, signature = value.split(".", 2)
        expected = hmac.new(
            _session_key(), f"{issued}.{_nonce}".encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_unb64(signature), expected):
            return False
        age = time.time() - int(issued)
    except Exception:
        return False
    # -60 tolerates small clock skew; the upper bound is the session lifetime.
    if not -60 <= age <= max_age_s:
        return False
    return not is_revoked(value)


# --------------------------------------------------------------------------
# request authentication
# --------------------------------------------------------------------------

def _bearer_from_headers(headers):
    authorization = headers.get("authorization", "")
    if authorization[:7].lower() == "bearer ":
        return authorization[7:].strip()
    api_token = headers.get("x-api-token")
    return api_token.strip() if api_token else None


def session_is_valid(source):
    """Cookie-based session check. Works for Request and WebSocket."""
    if not SETTINGS.auth_required:
        return True
    raw = source.cookies.get(SESSION_COOKIE)
    return bool(raw) and verify_session(raw)


def authenticated_via_cookie(source):
    return bool(source.cookies.get(SESSION_COOKIE)) and session_is_valid(source)


def require_auth(request: Request):
    """FastAPI dependency protecting every data endpoint."""
    bearer = _bearer_from_headers(request.headers)
    if bearer is not None:
        if not token_matches(bearer):
            raise HTTPException(
                401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}
            )
        return {"method": "bearer"}
    if session_is_valid(request):
        return {"method": "cookie"}
    raise HTTPException(
        401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
    )


def _enforce_csrf(request: Request):
    header_token = request.headers.get(CSRF_HEADER, "")
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    if not header_token or not cookie_token:
        raise HTTPException(403, "CSRF token missing")
    if not hmac.compare_digest(header_token.encode("utf-8"), cookie_token.encode("utf-8")):
        raise HTTPException(403, "CSRF token mismatch")


def require_write_auth(request: Request):
    """Cookie sessions are CSRF-protected; bearer tokens are not (no ambient authority).

    CSRF is skipped entirely when no token is configured: that is the
    localhost-only mode, where the browser holds no session cookie and
    therefore no CSRF token either. Requiring one there would break every
    write on the local dashboard.
    """
    context = require_auth(request)
    if SETTINGS.auth_required and context["method"] == "cookie":
        _enforce_csrf(request)
    return context


def websocket_authorized(websocket: WebSocket):
    """Authorise a WebSocket handshake, or raise to reject it.

    Browsers cannot set headers on a WebSocket, but they do send same-origin
    cookies on the handshake, so the session cookie is the normal path. The
    token query parameter exists for scripted clients.
    """
    if not SETTINGS.auth_required:
        return True
    if session_is_valid(websocket):
        return True
    bearer = _bearer_from_headers(websocket.headers)
    if bearer and token_matches(bearer):
        return True
    query_token = websocket.query_params.get("token")
    if query_token and token_matches(query_token):
        return True
    raise WebSocketException(code=WS_CLOSE_UNAUTHORIZED)


# --------------------------------------------------------------------------
# login throttling (in-process, per client IP)
# --------------------------------------------------------------------------

class LoginThrottle:
    def __init__(self, max_attempts, window_s):
        self.max_attempts = max(1, max_attempts)
        self.window_s = max(1, window_s)
        self._failures = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, now):
        for key in list(self._failures):
            recent = self._failures[key]
            while recent and now - recent[0] > self.window_s:
                recent.popleft()
            if not recent:
                del self._failures[key]

    def retry_after(self, client_id):
        """Seconds the client must wait, 0 when a login attempt is allowed."""
        now = time.time()
        with self._lock:
            self._prune(now)
            recent = self._failures.get(client_id)
            if not recent or len(recent) < self.max_attempts:
                return 0
            return max(1, int(self.window_s - (now - recent[0])))

    def record_failure(self, client_id):
        now = time.time()
        with self._lock:
            self._prune(now)
            self._failures[client_id].append(now)

    def reset(self, client_id):
        with self._lock:
            self._failures.pop(client_id, None)


LOGIN_THROTTLE = LoginThrottle(SETTINGS.login_max_attempts, SETTINGS.login_window_s)


def client_id_for(request: Request):
    """Identify the caller for throttling.

    Only X-Forwarded-For is consulted, and only because uvicorn has already
    verified the peer is a trusted proxy (see forwarded_allow_ips).
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --------------------------------------------------------------------------
# response helpers
# --------------------------------------------------------------------------

def set_session_cookies(response, secure):
    response.set_cookie(
        SESSION_COOKIE,
        issue_session(),
        max_age=SETTINGS.session_max_age_s,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
    )
    # Readable by JavaScript on purpose: this is the double-submit CSRF token.
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_urlsafe(24),
        max_age=SETTINGS.session_max_age_s,
        httponly=False,
        secure=secure,
        samesite="strict",
        path="/",
    )


def clear_session_cookies(response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def cookies_must_be_secure(request: Request):
    """Set Secure when the public request is HTTPS (terminated at the tunnel)."""
    return SETTINGS.force_secure_cookies or request.url.scheme == "https"


# --------------------------------------------------------------------------
# middleware
# --------------------------------------------------------------------------

class SecurityHeadersMiddleware:
    """Pure-ASGI so it also covers non-HTTP scopes without surprises."""

    def __init__(self, app, csp, hsts_max_age=31536000):
        self.app = app
        self.csp = csp
        self.hsts_max_age = hsts_max_age

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_https = scope.get("scheme") == "https"

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                self._apply(headers, is_https)
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _apply(self, headers, is_https):
        defaults = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # Live plant data must never sit in a shared proxy cache.
            "Cache-Control": "no-store",
        }
        if self.csp:
            defaults["Content-Security-Policy"] = self.csp
        if is_https:
            defaults["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )
        for key, value in defaults.items():
            if key not in headers:
                headers[key] = value