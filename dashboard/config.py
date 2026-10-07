"""Dashboard configuration.

All settings come from environment variables, optionally seeded from
dashboard/.env so that no secret is ever committed to source control.

Nothing here touches OPC-UA, the routine manager or any industrial logic -
this module only decides how the HTTP/WebSocket surface is exposed.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
MIN_TOKEN_LENGTH = 16


def load_env_file(path=ENV_PATH):
    """Minimal .env reader (KEY=VALUE, # comments, optional quotes).

    Real environment variables always win, so a systemd unit or a shell
    export can override anything committed as a template.
    """
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)
    return True


def _get(name, default=""):
    return os.environ.get(name, default).strip()


# Must happen before Settings() reads the environment, otherwise .env values
# would only be visible to code that runs after startup.
ENV_FILE_LOADED = load_env_file()


def _get_bool(name, default=False):
    value = _get(name).lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def _get_int(name, default):
    raw = _get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        print(f"[CONFIG] {name}={raw!r} is not a number, using {default}")
        return default


def _get_list(name):
    return [item.strip() for item in _get(name).split(",") if item.strip()]


class Settings:
    """Runtime configuration for the dashboard HTTP surface."""

    def __init__(self):
        # Where the dashboard listens. Loopback by default: cloudflared runs on
        # this same machine, so there is no reason to expose an OPC-UA write
        # proxy to the plant LAN.
        self.host = _get("DASHBOARD_HOST", "127.0.0.1")
        self.port = _get_int("DASHBOARD_PORT", 8000)

        # Shared secret for login. Empty means "no auth", which is only
        # allowed on a loopback bind.
        self.auth_token = _get("DASHBOARD_AUTH_TOKEN")
        self.session_max_age_s = _get_int("DASHBOARD_SESSION_HOURS", 12) * 3600

        # Browser origins allowed to call the API cross-origin. Empty (the
        # default) means no CORS headers at all, which is what a tunnel
        # deployment wants: everything is same-origin.
        self.allowed_origins = _get_list("DASHBOARD_ALLOWED_ORIGINS")

        # Force the Secure cookie flag when TLS is terminated upstream but the
        # proxy headers cannot be trusted to say so.
        self.force_secure_cookies = _get_bool("DASHBOARD_SECURE_COOKIES", False)

        # Uvicorn only honours X-Forwarded-* from these peers. Never use "*".
        self.trusted_proxy_ips = _get_list("DASHBOARD_TRUSTED_PROXY_IPS") or ["127.0.0.1"]

        # Brute-force protection for the login endpoint.
        self.login_max_attempts = _get_int("DASHBOARD_LOGIN_MAX_ATTEMPTS", 5)
        self.login_window_s = _get_int("DASHBOARD_LOGIN_WINDOW_SECONDS", 300)

        # /docs and /openapi.json publish the whole API, including the OPC-UA
        # write endpoint. Off unless explicitly requested.
        self.enable_docs = _get_bool("DASHBOARD_ENABLE_DOCS", False)

        # Set to a custom value only if the default policy breaks the CDN
        # assets; empty disables the header.
        self.csp = _get("DASHBOARD_CSP") or (
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'; object-src 'none'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "img-src 'self' data:; connect-src 'self' ws: wss:"
        )

    @property
    def is_loopback(self):
        return self.host in LOOPBACK_HOSTS

    @property
    def auth_required(self):
        return bool(self.auth_token)

    def public_origin(self):
        """Best-effort origin hint for operators; never used for access control."""
        return f"http://{self.host}:{self.port}"

    def validate(self):
        """Fail closed: refuse to start in a configuration that leaks the API."""
        problems = []
        if not self.auth_required and not self.is_loopback:
            problems.append(
                f"DASHBOARD_HOST={self.host!r} is not a loopback address but "
                "DASHBOARD_AUTH_TOKEN is empty. Anyone able to reach this port "
                "could read tags and write OPC-UA values. Either set "
                "DASHBOARD_AUTH_TOKEN, or bind DASHBOARD_HOST=127.0.0.1."
            )
        if self.auth_required and len(self.auth_token) < MIN_TOKEN_LENGTH:
            problems.append(
                f"DASHBOARD_AUTH_TOKEN is shorter than {MIN_TOKEN_LENGTH} "
                "characters and would be trivial to brute force. Generate one "
                'with: python -c "import secrets;print(secrets.token_urlsafe(32))"'
            )
        if problems:
            for problem in problems:
                print(f"[CONFIG ERROR] {problem}", file=sys.stderr)
            raise SystemExit(2)
        return True

    def describe(self):
        lines = [
            f"[CONFIG] listen            : {self.host}:{self.port}",
            f"[CONFIG] authentication    : "
            f"{'enabled (shared token)' if self.auth_required else 'DISABLED (loopback only)'}",
            f"[CONFIG] session lifetime  : {self.session_max_age_s // 3600}h",
            f"[CONFIG] allowed origins   : {', '.join(self.allowed_origins) or 'none (same-origin only)'}",
            f"[CONFIG] trusted proxies   : {', '.join(self.trusted_proxy_ips)}",
            f"[CONFIG] API docs          : {'enabled at /docs' if self.enable_docs else 'disabled'}",
            f"[CONFIG] OPC-UA endpoint   : reachable from this process only, never proxied",
        ]
        if ENV_FILE_LOADED:
            lines.append(f"[CONFIG] env file          : {ENV_PATH}")
        if not self.auth_required:
            lines.append("")
            lines.append("[CONFIG WARNING] No DASHBOARD_AUTH_TOKEN is set.")
            lines.append(
                "[CONFIG WARNING] The dashboard serves unauthenticated read AND "
                "OPC-UA write access."
            )
            lines.append(
                "[CONFIG WARNING] That is acceptable on a localhost-only bind, "
                "but if cloudflared"
            )
            lines.append(
                "[CONFIG WARNING] forwards this port to the Internet, set a token "
                "first."
            )
        return "\n".join(lines)


SETTINGS = Settings()