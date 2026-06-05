import asyncio
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from opcua import Client, ua

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

with open(os.path.join(PROJECT_ROOT, "config/system_config.json")) as f:
    SYSTEM_CONFIG = json.load(f)

with open(os.path.join(PROJECT_ROOT, "weighbridgeConfig.json")) as f:
    WEIGHBRIDGE_CONFIG = json.load(f)

OPC_CFG = SYSTEM_CONFIG["opc_server"][0]
DB_PATH = os.path.join(PROJECT_ROOT, "sample", "core", "weighbridge.db")

tag_values = {}
ws_clients = set()
tag_lock = threading.Lock()
event_loop = None


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

    def get_tag_node(self, category, tag):
        path = [
            "0:Objects",
            f"{self.idx}:{OPC_CFG['serverObjectName']}",
            f"{self.idx}:{category}",
            f"{self.idx}:{tag}",
        ]
        return self.root.get_child(path)

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

        if changed and event_loop is not None:
            with tag_lock:
                snapshot = {k: dict(v) for k, v in tag_values.items()}
            asyncio.run_coroutine_threadsafe(_broadcast(snapshot), event_loop)

        time.sleep(0.5)


async def _broadcast(data):
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json({"type": "update", "data": data})
        except Exception:
            dead.add(ws)
    ws_clients.difference_update(dead)


def get_weighments(limit=20):
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
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
    t = threading.Thread(target=opc_poller, args=(opc,), daemon=True)
    t.start()
    yield
    opc.disconnect()


app = FastAPI(title="Weighbridge Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    with open(os.path.join(SCRIPT_DIR, "templates", "index.html")) as f:
        return HTMLResponse(f.read())


@app.get("/api/config")
async def get_config():
    return WEIGHBRIDGE_CONFIG


@app.get("/api/tags")
async def get_tags():
    with tag_lock:
        return {k: dict(v) for k, v in tag_values.items()}


@app.get("/api/weighments")
async def get_weighments_api(limit: int = 50):
    return get_weighments(limit)


@app.post("/api/tags/{category}/{tag}")
async def write_tag(category: str, tag: str, value: str):
    opc = getattr(app.state, "opc", None)
    if not opc or not opc.connected:
        raise HTTPException(503, "OPC UA not connected")
    success = opc.write_tag(category, tag, value)
    if not success:
        raise HTTPException(500, "Write failed")
    return {"status": "ok", "category": category, "tag": tag, "value": value}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    with tag_lock:
        snapshot = {k: dict(v) for k, v in tag_values.items()}
    await websocket.send_json({"type": "init", "data": snapshot})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(websocket)
    except Exception:
        ws_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
