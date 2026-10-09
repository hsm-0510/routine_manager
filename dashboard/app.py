import asyncio
import io
import json
import os
import sqlite3
import sys
import threading
import time
from datetime import datetime
from contextlib import asynccontextmanager

import pandas as pd

from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from opcua import Client, ua

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# main.py launches this file as a script (python dashboard/app.py), so the
# project root is not on sys.path yet and "dashboard.config" would not resolve.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.config import SETTINGS
from dashboard.security import (
    LOGIN_THROTTLE,
    SESSION_COOKIE,
    SecurityHeadersMiddleware,
    clear_session_cookies,
    client_id_for,
    cookies_must_be_secure,
    require_auth,
    require_write_auth,
    revoke_session,
    session_is_valid,
    set_session_cookies,
    token_matches,
    websocket_authorized,
)

# Refuse to start in a configuration that would leave the OPC-UA write proxy
# reachable without a password.
SETTINGS.validate()

def _get_config_path(name):
    # Prefer external config folder next to exe or in CWD
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), 'config', name))
    candidates.append(os.path.join(os.getcwd(), 'config', name))
    candidates.append(os.path.join(PROJECT_ROOT, 'config', name))
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.join(PROJECT_ROOT, 'config', name)

with open(_get_config_path('system_config.json')) as f:
    SYSTEM_CONFIG = json.load(f)

with open(_get_config_path('weighbridgeConfig.json')) as f:
    WEIGHBRIDGE_CONFIG = json.load(f)

OPC_CFG = SYSTEM_CONFIG["opc_server"][0]
DB_PATH = os.path.join(PROJECT_ROOT, "sample", "core", "weighbridge.db")

tag_values = {}
ws_clients = set()
tag_lock = threading.Lock()
event_loop = None

WAVESHARE_TCP_STATUS = {"connected": False, "stale": True, "age": None}
tcp_status_lock = threading.Lock()
TCP_STATUS_PATH = os.path.join(PROJECT_ROOT, "dashboard", "tcp_status.json")
# The routine manager refreshes dashboard/tcp_status.json every
# TCP_BEACON_INTERVAL seconds; a newer gap means the writer died.
TCP_BEACON_INTERVAL = 2.0
TCP_STATUS_STALE_SECONDS = TCP_BEACON_INTERVAL * 4

# Only tags declared in config/weighbridgeConfig.json may be written. Without
# this the {category}/{tag} path is handed straight to node.set_value(), so any
# client that can reach the API could address an arbitrary node in the OPC
# tree. The allowlist is derived from the same config the UI is built from.
WRITE_ALLOWLIST = {
    category["name"]: {tag["name"] for tag in category["tags"]}
    for category in WEIGHBRIDGE_CONFIG["categories"]
}
MAX_WRITE_VALUE_LENGTH = 64
MAX_WEIGHMENT_ROWS = 500
# A client that stops reading its socket must not be able to stall the
# broadcast loop and freeze live data for every other viewer.
WS_SEND_TIMEOUT = 5.0
SQLITE_TIMEOUT = 5.0

class OPCClient:
    def __init__(self):
        self.client = Client(OPC_CFG["endpoint"])
        self.idx = None
        self.root = None
        self.connected = False

    def connect(self):
        try:
            self.client.connect()
            self.root = self.client.get_root_node()
            self.idx = self.client.get_namespace_index(OPC_CFG["namespaceUri"])
            self.connected = True
            print(f"[OPC] Connected to {OPC_CFG['endpoint']}")
        except Exception as e:
            print(f"[OPC] Connection failed: {e}")
            self.connected = False

    def disconnect(self):
        try:
            self.client.disconnect()
        except Exception:
            pass
        self.connected = False

    # def get_tag_node(self, category, tag):
    #     path = [
    #         "0:Objects",
    #         f"{self.idx}:{OPC_CFG['serverObjectName']}",
    #         f"{self.idx}:{category}",
    #         f"{self.idx}:{tag}",
    #     ]
    #     return self.root.get_child(path)
    def get_tag_node(self, category_name, tag_name):
            node_id = f"ns=2;s=WEIGHBRIDGE/{category_name}/{tag_name}"
            return self.client.get_node(node_id)

    def read_tag(self, category, tag):
        try:
            node = self.get_tag_node(category, tag)
            value = node.get_value()
            return str(value) if value is not None else ""
        except Exception as e:
            return ""

    def write_tag(self, category, tag, value):
        try:
            node = self.get_tag_node(category, tag)
            node.set_value(value)
            return True
        except Exception as e:
            print(f"[OPC] Write error {category}.{tag}: {e}")
            return False


def opc_poller(opc: OPCClient):
    global event_loop
    retry_count = 0
    while True:
        if not opc.connected:
            retry_count += 1
            if retry_count == 1 or retry_count % 15 == 0:
                print(f"[Poller] OPC not connected (attempt #{retry_count})...")
            try:
                opc.connect()
                if opc.connected:
                    retry_count = 0
            except Exception:
                pass
            time.sleep(4)
            continue

        changed = False
        try:
            for cat in WEIGHBRIDGE_CONFIG["categories"]:
                category = cat["name"]
                for tag_info in cat["tags"]:
                    tag = tag_info["name"]
                    val = opc.read_tag(category, tag)
                    with tag_lock:
                        old = tag_values.get(category, {}).get(tag)
                        if old != val:
                            tag_values.setdefault(category, {})[tag] = val
                            changed = True
        except Exception as e:
            print(f"[Poller] Error: {e}")
            opc.connected = False

        if changed:
            _schedule_broadcast()

        time.sleep(0.5)

# def heartbeat_task(opc: OPCClient):
#     heartbeat = 0

#     while True:
#         try:
#             if opc.connected:
#                 heartbeat += 1

#                 opc.write_tag(
#                     "System",
#                     "RoutineHeartbeat",
#                     heartbeat
#                 )

#         except Exception as e:
#             print(f"[Heartbeat] Error: {e}")

#         time.sleep(1)


def read_tcp_status():
    """Read the routine manager's TCP beacon file.

    Returns (connected, stale, age_seconds). A beacon that is missing or
    older than TCP_STATUS_STALE_SECONDS means the routine manager is not
    refreshing it, so the link is reported as down no matter what the file
    says - otherwise a crashed process leaves the GUI stuck on "connected".
    """
    try:
        with open(TCP_STATUS_PATH) as f:
            st = json.load(f)
        age = max(0.0, time.time() - float(st.get("timestamp") or 0))
    except FileNotFoundError:
        return False, True, None
    except Exception:
        return False, True, None
    stale = age > TCP_STATUS_STALE_SECONDS
    return (bool(st.get("connected", False)) and not stale), stale, age


def get_tcp_status():
    with tcp_status_lock:
        return {
            "connected": WAVESHARE_TCP_STATUS["connected"],
            "stale": WAVESHARE_TCP_STATUS["stale"],
            "ageSeconds": WAVESHARE_TCP_STATUS["age"],
            "source": TCP_STATUS_PATH,
        }


def tcp_status_poller():
    while True:
        connected, stale, age = read_tcp_status()
        with tcp_status_lock:
            changed = WAVESHARE_TCP_STATUS["connected"] != connected
            WAVESHARE_TCP_STATUS["connected"] = connected
            WAVESHARE_TCP_STATUS["stale"] = stale
            WAVESHARE_TCP_STATUS["age"] = age
        # Push on transition even if no OPC tag moved, otherwise the header
        # indicator keeps whatever value the last tag update carried.
        if changed:
            _schedule_broadcast()
        time.sleep(TCP_BEACON_INTERVAL)


def _schedule_broadcast():
    """Thread-safe: push the current snapshot to WebSocket clients."""
    loop = event_loop
    if loop is None:
        return
    with tag_lock:
        snapshot = {k: dict(v) for k, v in tag_values.items()}
    asyncio.run_coroutine_threadsafe(_broadcast(snapshot), loop)


async def _broadcast(data):
    dead = set()
    with tcp_status_lock:
        tcp_connected = WAVESHARE_TCP_STATUS["connected"]
        tcp_stale = WAVESHARE_TCP_STATUS["stale"]
    for ws in ws_clients:
        try:
            await asyncio.wait_for(
                ws.send_json({
                    "type": "update",
                    "data": data,
                    "waveshareTcp": tcp_connected,
                    "waveshareTcpStale": tcp_stale,
                }),
                timeout=WS_SEND_TIMEOUT,
            )
        except Exception:
            # Slow, half-open or gone: drop it rather than block the loop.
            dead.add(ws)
    ws_clients.difference_update(dead)


def get_weighments(limit=20):
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM weighments ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Error: {e}")
        return []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_loop
    event_loop = asyncio.get_event_loop()
    opc = OPCClient()
    opc.connect()
    app.state.opc = opc
    t1 = threading.Thread(target=opc_poller, args=(opc,), daemon=True)
    t1.start()
    t2 = threading.Thread(target=tcp_status_poller, daemon=True)
    t2.start()
    yield
    opc.disconnect()


app = FastAPI(
    title="Weighbridge Dashboard",
    lifespan=lifespan,
    # These publish the entire API surface, including the OPC-UA write
    # endpoint, so they stay off unless explicitly enabled.
    docs_url="/docs" if SETTINGS.enable_docs else None,
    redoc_url="/redoc" if SETTINGS.enable_docs else None,
    openapi_url="/openapi.json" if SETTINGS.enable_docs else None,
)

# Cross-origin access is off by default. Through Cloudflare Tunnel everything
# is same-origin, and a wildcard would let any site open in an operator's
# browser drive an OPC-UA write proxy. Set DASHBOARD_ALLOWED_ORIGINS only if a
# separate front-end genuinely needs it.
if SETTINGS.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SETTINGS.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization", "X-API-Token", "X-CSRF-Token"],
    )

# Added last, therefore outermost: headers reach CORS preflights too.
app.add_middleware(SecurityHeadersMiddleware, csp=SETTINGS.csp)


@app.get("/")
async def index():
    # Public on purpose: the login form has to load before a session exists.
    with open(os.path.join(SCRIPT_DIR, "templates", "index.html")) as f:
        return HTMLResponse(f.read())


async def _read_json(request):
    """Tolerant body reader: a malformed login must not become a 500."""
    try:
        payload = await request.json()
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


@app.get("/healthz")
async def healthz():
    """Liveness probe for Cloudflare / the service manager.

    Deliberately reveals nothing about the weighbridge, so it needs no token.
    """
    return {"status": "ok"}


@app.get("/api/auth/status")
async def auth_status(request: Request):
    return {
        "authRequired": SETTINGS.auth_required,
        "authenticated": session_is_valid(request),
    }


@app.post("/api/auth/login")
async def login(request: Request):
    client_id = client_id_for(request)
    retry_after = LOGIN_THROTTLE.retry_after(client_id)
    if retry_after:
        return JSONResponse(
            {"detail": "Too many failed login attempts. Try again later."},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )

    payload = await _read_json(request)
    supplied = payload.get("token", "") if payload else ""
    if not isinstance(supplied, str) or not token_matches(supplied):
        LOGIN_THROTTLE.record_failure(client_id)
        # Same message and status whether the token is wrong or missing, so the
        # endpoint cannot be used to probe for valid tokens.
        raise HTTPException(401, "Invalid credentials")

    LOGIN_THROTTLE.reset(client_id)
    response = JSONResponse({"status": "ok", "authRequired": SETTINGS.auth_required})
    set_session_cookies(response, cookies_must_be_secure(request))
    return response


@app.post("/api/auth/logout")
async def logout(request: Request):
    # Unauthenticated and idempotent so it also clears an already-dead cookie,
    # but the presented session is revoked server-side: deleting the cookie in
    # the browser must be enough to actually end the session.
    revoke_session(request.cookies.get(SESSION_COOKIE))
    response = JSONResponse({"status": "ok"})
    clear_session_cookies(response)
    return response


@app.get("/api/config", dependencies=[Depends(require_auth)])
async def get_config():
    return WEIGHBRIDGE_CONFIG


@app.get("/api/tags", dependencies=[Depends(require_auth)])
async def get_tags():
    with tag_lock:
        return {k: dict(v) for k, v in tag_values.items()}


@app.get("/api/weighments", dependencies=[Depends(require_auth)])
async def get_weighments_api(limit: int = Query(50, ge=1, le=MAX_WEIGHMENT_ROWS)):
    return get_weighments(limit)


@app.get("/api/tcp/status", dependencies=[Depends(require_auth)])
async def get_tcp_status_api():
    return get_tcp_status()


@app.get("/api/weighments/download", dependencies=[Depends(require_auth)])
async def download_weighments():
    """Export weighments. Read-only: retention is handled by the scheduled
    job in localDB.retention_worker, never as a side effect of a GET."""
    output = io.BytesIO()
    df = pd.DataFrame()
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT)
            df = pd.read_sql_query("SELECT * FROM weighments ORDER BY id DESC", conn)
            conn.close()
        except Exception as e:
            print(f"[DB EXPORT ERROR] {e}")
    # Try openpyxl, fall back to xlsxwriter, fall back to csv
    ext = ".xlsx"
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Weighments")
    except Exception:
        try:
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Weighments")
        except Exception:
            output = io.StringIO()
            df.to_csv(output, index=False)
            ext = ".csv"
            media = "text/csv"
    output.seek(0)
    from fastapi.responses import StreamingResponse
    fname = f"weighments_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    return StreamingResponse(
        iter([output.getvalue().encode() if isinstance(output, io.StringIO) else output.getvalue()]),
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={fname}"}
    )


@app.post("/api/tags/{category}/{tag}", dependencies=[Depends(require_write_auth)])
async def write_tag(
    category: str,
    tag: str,
    value: str = Query(..., description="New value to write to the OPC-UA tag"),
):
    """Write a single OPC-UA tag.

    This is the one endpoint that changes plant behaviour, so it requires a
    session (plus CSRF proof), and the target must be a tag declared in
    config/weighbridgeConfig.json. The UI sends the value as a query
    parameter (?value=...); declaring it as Query(...) keeps that contract
    instead of silently 422-ing on a missing JSON body.
    """
    allowed_tags = WRITE_ALLOWLIST.get(category)
    if not allowed_tags or tag not in allowed_tags:
        raise HTTPException(404, f"Unknown tag {category}.{tag}")
    if len(value) > MAX_WRITE_VALUE_LENGTH:
        raise HTTPException(422, f"Value exceeds {MAX_WRITE_VALUE_LENGTH} characters")

    opc = getattr(app.state, "opc", None)
    if not opc or not opc.connected:
        raise HTTPException(503, "OPC UA not connected")
    success = opc.write_tag(category, tag, value)
    if not success:
        raise HTTPException(500, "Write failed")
    return {"status": "ok", "category": category, "tag": tag, "value": value}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Authorise before accept(); a browser cannot set headers on a WebSocket,
    # so this normally resolves via the same-origin session cookie.
    websocket_authorized(websocket)
    await websocket.accept()
    ws_clients.add(websocket)
    with tag_lock:
        snapshot = {k: dict(v) for k, v in tag_values.items()}
    with tcp_status_lock:
        tcp_connected = WAVESHARE_TCP_STATUS["connected"]
        tcp_stale = WAVESHARE_TCP_STATUS["stale"]
    try:
        await websocket.send_json({
            "type": "init",
            "data": snapshot,
            "waveshareTcp": tcp_connected,
            "waveshareTcpStale": tcp_stale,
        })
    except Exception:
        ws_clients.discard(websocket)
        return
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        ws_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    print(SETTINGS.describe())
    print(
        f"[STARTUP] Dashboard on {SETTINGS.public_origin()}"
        f" | local: http://localhost:{SETTINGS.port}"
    )
    if SETTINGS.auth_required:
        print(
            "[STARTUP] Open the dashboard and enter the DASHBOARD_AUTH_TOKEN "
            "when prompted. OPC-UA remains local-only on port 5501."
        )
    uvicorn.run(
        app,
        host=SETTINGS.host,
        port=SETTINGS.port,
        # cloudflared connects from loopback and sets X-Forwarded-Proto, which
        # is how request.url.scheme (and therefore Secure cookies and HSTS)
        # knows the public request was HTTPS.
        proxy_headers=True,
        forwarded_allow_ips=",".join(SETTINGS.trusted_proxy_ips),
        server_header=False,
    )
