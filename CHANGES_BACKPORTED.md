# Backport: changes copied from the colleague's working copy

**Date:** 2026-10-05
**Source (NEW):** `9. Talha Work\WEIGHBRIDGE_06232026\WEIGHBRIDGE_06232026\Routine_Manager_Master3_V1\routine_manager-master3\routine_manager-master3`
**Target (OLD):** `7. Yaohua XK3190-DS8\Dev\routine_manager`

Both trees use LF line endings and identical folder layout, so every change was
applied by copying the file across verbatim and then layering the fixes in
"Loose end problems" on top.

---

## 1. Changes copied (verbatim)

| # | Change | File | Notes |
|---|---|---|---|
| 1 | Separate Entrance/Exit receipt pages replacing the combined KIOSK receipt card | `dashboard/templates/index.html` | New SPA pages + 2 sidebar nav items |
| 2 | Receipt print (`printReceipt`) and OK→Overview (`navigateTo`) actions | `dashboard/templates/index.html` | Popup window + `win.print()` |
| 3 | Receipt renderers split into `updateEntranceReceipt` / `updateExitReceipt`, larger card | `dashboard/templates/index.html` | Both added to `updateAll()` |
| 4 | "Download XLS" button + `downloadWeighments()` | `dashboard/templates/index.html` | Blob download, spinner, error toast |
| 5 | Waveshare TCP status dot in the header bar | `dashboard/templates/index.html` | 3rd status indicator |
| 6 | WebSocket handler consumes `waveshareTcp` | `dashboard/templates/index.html` | |
| 7 | `.btn-print` / `.btn-ok` CSS | `dashboard/templates/index.html` | |
| 8 | `GET /api/weighments/download` XLSX export | `dashboard/app.py` | openpyxl → xlsxwriter → CSV fallback |
| 9 | `tcp_status_poller()` thread reading `dashboard/tcp_status.json` | `dashboard/app.py` | Started from `lifespan` |
| 10 | `waveshareTcp` added to WS `update` + `init` payloads | `dashboard/app.py` | |
| 11 | `pandas` / `io` imports | `dashboard/app.py` | |
| 12 | Commented-out `heartbeat_task()` stub | `dashboard/app.py` | Dead code, left as received |
| 13 | New OPC category **"Syncing Check"** (`WaveShare_Heartbeat`, `RoutineManager_Heartbeat`, int) | `config/weighbridgeConfig.json` | See loose end #3 |
| 14 | `created_at` column + `ALTER TABLE` migration | `sample/core/localDB.py` | |
| 15 | `save_tare()` now timestamps each weighment | `sample/core/localDB.py` | |
| 16 | New `delete_old_records(days=1)` helper | `sample/core/localDB.py` | Was dead code, see loose end #1 |
| 17 | Heartbeat watchdog (15 s) forces reconnect | `sample/tcpClient/tcp_connection_manager.py` | |
| 18 | Full payload pushed on every (re)connect | `sample/tcpClient/tcp_connection_manager.py` | Needs `payload_ref` |
| 19 | `update_heartbeat()` + `tcp_status.json` writes on connect/disconnect | `sample/tcpClient/tcp_connection_manager.py` | Extended, see fix #3 |
| 20 | Connect failures logged as `[ALARM]` | `sample/tcpClient/tcp_connection_manager.py` | |
| 21 | Heartbeat detection on receive | `sample/tcpClient/tcp_client.py` | |
| 22 | Reconnect-aware send/receive buffers (`connect_epoch`) | `sample/tcpClient/tcp_client.py` | |
| 23 | `isinstance(parsed[section], dict)` guard on payload merge | `sample/tcpClient/tcp_client.py` | |
| 24 | `conn_mgr.payload_ref = state_manager.tcp_payload` | `tests/test7_sap_opc.py` | Required by #18 |
| 25 | `write_tcp_status()` helper writing `dashboard/tcp_status.json` | `sample/core/state_manager.py` | Hardened, see fix #3 |
| 26 | `pandas==2.2.0`, `openpyxl==3.1.2` | `dashboard/requirements.txt` | |
| 27 | `pipe_reader()` null-guard in the launcher | `main.py` | |
| 28 | Retention sweep thread registration | `tests/test7_sap_opc.py` | Added by fix #1 |

## 2. Deliberately **not** copied

| Item | Reason |
|---|---|
| `Install Instructions.txt` rewrite | Explicitly excluded by request — the original manual `python -m venv` steps are kept. |
| `sample/core/weighbridge.db` | Runtime data, not source. The `created_at` column is added by the `ALTER TABLE` migration on next start. Copying it would import another machine's test weighments. |
| `dashboard/tcp_status.json` | Runtime beacon, not source. It is now generated at start-up and git-ignored; the colleague's copy was frozen at `"connected": true`. |
| `sample/main.py` | Empty 0-byte placeholder. |
| `dashboard/static/` | Empty directory in the colleague's tree. |

---

## 3. Loose end problems

| # | Problem | Severity | Status |
|---|---|---|---|
| 1 | `delete_old_records()` was dead code — retention only ran as a side effect of the download | High | **Fixed** |
| 2 | `GET /api/weighments/download` deleted data (a GET with a destructive side effect; prefetch/double-click loses weighments) | High | **Fixed** |
| 3 | "Syncing Check" tags are orphaned — declared in config and polled, but nothing writes them (the only writer is the commented-out `heartbeat_task`) and no page displays them | Medium | Open |
| 4 | `downloadWeighments()` hardcodes `a.download = 'weighments.xlsx'` although the server may return `.csv` | Low | Open |
| 5 | Pre-existing in **both** copies: write API mismatch — the browser posts `?value=…` as a query param while FastAPI expects `value` in the JSON body, so every ON/OFF/SET returns HTTP 422 | High | Open |

### Fix #1 — retention now runs on a schedule

`sample/core/localDB.py`

```python
RETENTION_DAYS = 1
RETENTION_INTERVAL_S = 3600

def retention_worker(stop_event=None):
    delete_old_records(RETENTION_DAYS)          # sweep at start-up
    while True:
        if stop_event is not None:
            if stop_event.wait(RETENTION_INTERVAL_S):
                return
        else:
            time.sleep(RETENTION_INTERVAL_S)
        delete_old_records(RETENTION_DAYS)
```

`tests/test7_sap_opc.py` starts it as a daemon thread, reusing the TCP manager's
`stop_event` so it shuts down with the rest of the routine:

```python
threading.Thread(target=localDB.retention_worker, args=(conn_mgr.stop_event,), daemon=True).start()
```

The sweep now runs at start-up and hourly, instead of only when a spreadsheet is
downloaded. Tune `RETENTION_DAYS` / `RETENTION_INTERVAL_S` at the top of
`localDB.py` (or move them into `config/system_config.json` if site-specific
retention is ever needed).

Note: rows whose `created_at` is `NULL` are still never deleted. That is
deliberate — a record of unknown age is not safe to expire — but it means
records written before the migration accumulate indefinitely and need a one-off
manual clear.

### Fix #2 — the export endpoint is now read-only

`dashboard/app.py` — the `DELETE FROM weighments …` block and the unused
`timedelta` import were removed from `download_weighments()`. The endpoint now
only reads and streams the export; retention is owned solely by the scheduled
job above. A missing/unreadable DB is reported instead of silently swallowed:

```python
except Exception as e:
    print(f"[DB EXPORT ERROR] {e}")
```

### Fix #3 — the Waveshare TCP indicator is no longer static

**Why it was stuck.** The dashboard only attached `waveshareTcp` to OPC tag
change broadcasts, so if no OPC value moved the header kept whatever the last
message said. Nothing detected a stale file either, so a routine manager that
died (or never started) left `"connected": true` on screen forever.

**Writer side** — `sample/core/state_manager.py`, `sample/tcpClient/tcp_connection_manager.py`

1. `write_tcp_status()` writes atomically (temp file + `fsync` + `os.replace`),
   so the reader can never see a half-written document and keep a stale value.
2. `TCPConnectionManager.__init__` immediately publishes `connected: false`, so
   a restart never inherits a stale `true`, then starts a 2 s beacon thread that
   republishes the live `connected` state for the life of the process.
   `close()` publishes `false` as well.
3. The beacon doubles as a liveness signal: if the process dies the timestamp
   stops advancing and the dashboard can tell.

**Dashboard side** — `dashboard/app.py`

1. `TCP_BEACON_INTERVAL = 2.0`, `TCP_STATUS_STALE_SECONDS = 8.0` (4× the
   writer interval, tolerant of GC/scheduling jitter).
2. `read_tcp_status()` returns `(connected, stale, age)`; a missing file or an
   age over the threshold reports **not connected**, so a dead writer cannot
   leave a green light on.
3. `tcp_status_poller()` pushes to WebSocket clients **on every transition**,
   independent of OPC tag activity — this is what unsticks the indicator.
4. New diagnostic endpoint `GET /api/tcp/status` →
   `{"connected", "stale", "ageSeconds", "source"}`.
5. `_schedule_broadcast()` extracted so both pollers share one snapshot path;
   `init` and `update` frames both carry `waveshareTcpStale`.

**Frontend** — `dashboard/templates/index.html`

Three states instead of two: `Connected` (green) / `Disconnected` (red) /
`No Signal` (red, beacon stale or absent). The header starts at
`Connecting...`, and `refreshTcpStatus()` polls `/api/tcp/status` every 5 s so
the indicator stays correct even with the WebSocket down.

---

## 4. Verification performed

- `python -m py_compile` on every changed Python file.
- Retention: seeded a scratch DB with fresh / 2-day-old / `NULL`-`created_at`
  rows and confirmed only the old dated row is swept.
- Download endpoint: confirmed it returns a workbook and leaves row count
  unchanged.
- TCP status: confirmed the writer creates the beacon at start-up, that a
  missing file reports `(False, stale)`, that an old timestamp flips to
  `stale` while a fresh `true` stays connected, and that a partial/torn file
  cannot be produced (atomic replace).

## 5. Still open

- Loose end #3 (orphaned "Syncing Check" tags), #4 (`.csv` filename), #5
  (write endpoint 422) are untouched — they were outside the requested scope.
- Not previously flagged, still present: the frontend interpolates OPC tag
  values with `innerHTML` (only receipt lines are escaped), and Bootstrap /
  Chart.js load from a CDN, so the dashboard renders blank without internet.

## 6. Incidental observations

- `sample/core/localDB.py:13` builds the DB path with `"sample\core"` inside a
  normal string. Python 3.12 emits `SyntaxWarning: invalid escape sequence
  '\c'` and the path is Windows-only — it breaks if this ever runs on Linux.
  Pre-existing in both copies, not touched here.
- `__pycache__/*.pyc` files are **tracked** in git (the old `.gitignore` only
  had `/.venv`), so recompiling shows them as modified. `__pycache__/` and
  `*.pyc` are now in `.gitignore`, which does not untrack them. To clean that
  up: `git rm -r --cached --quiet` on the `__pycache__` directories, then commit.
- `main.py` imports `tcp_client` but never uses it; the `pipe_reader` threads
  are always handed `None` because the `Popen` calls request no `PIPE`. Both
  are harmless and were left as received.