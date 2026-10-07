import subprocess
import sys
import os
import time
import threading

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    BASE = sys._MEIPASS
    PYTHON = sys.executable  # this is the exe
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
    PYTHON = sys.executable

procs = []

def cleanup():
    print("\n[LAUNCHER] Shutting down all processes...")
    for p in procs:
        if p.poll() is None:
            p.terminate()
    for p in procs:
        try:
            p.wait(timeout=5)
        except:
            p.kill()
    sys.exit(0)

print("=" * 60)
print("  Weighbridge System Launcher")
print("=" * 60)

# For frozen exe, DO NOT spawn the exe as subprocess (fork bomb)
# Instead, run modules in separate Python processes using the real python if available?
# Or just avoid spawning when frozen and run inline? But we need separate processes.
# Alternative: when frozen, spawn with pythonw/python from PATH? Not reliable.
# Better: detect frozen and run both modules in threads (single process) - simpler and safe for exe.

if IS_FROZEN:
    # Run in same process but in threads for safety
    import importlib
    def run_main():
        try:
            import tests.test7_sap_opc  # blocks
        except Exception as e:
            print(f"[MAIN ERR] {e}")
    def run_dash():
        try:
            import sys as _sys
            dash_path = os.path.join(BASE, "dashboard")
            if dash_path not in _sys.path:
                _sys.path.insert(0, dash_path)
            import uvicorn
            from dashboard import app as dash_app
            uvicorn.run(dash_app.app, host="127.0.0.1", port=8000, log_level="info")
        except Exception as e:
            print(f"[DASH ERR] {e}")
    threading.Thread(target=run_main, daemon=True).start()
    threading.Thread(target=run_dash, daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()
else:
    # Source mode - separate processes as before
    main_proj = subprocess.Popen([PYTHON, "-m", "tests.test7_sap_opc"], cwd=BASE)
    procs.append(main_proj)
    dashboard_dir = os.path.join(BASE, "dashboard")
    dashboard = subprocess.Popen([PYTHON, "app.py"], cwd=dashboard_dir)
    procs.append(dashboard)
    try:
        while True:
            time.sleep(1)
            if main_proj.poll() is not None and dashboard.poll() is not None:
                break
    except KeyboardInterrupt:
        cleanup()
