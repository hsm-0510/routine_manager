import subprocess
import sys
import os
import time
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
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

# 1. Main project
main_proj = subprocess.Popen(
    [sys.executable, "-u", "-m", "tests.test7_sap_opc"],
    cwd=BASE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
procs.append(main_proj)

# 2. Dashboard
dashboard = subprocess.Popen(
    [sys.executable, "-u", "app.py"],
    cwd=os.path.join(BASE, "dashboard"),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
procs.append(dashboard)

print(f"[LAUNCHER] Main project started (PID: {main_proj.pid})")
print(f"[LAUNCHER] Dashboard started (PID: {dashboard.pid})")
print(f"[LAUNCHER] Dashboard at http://localhost:8000")
print("[LAUNCHER] Press Ctrl+C to stop all\n")

def pipe_reader(stream, prefix):
    for line in iter(stream.readline, ""):
        print(f"[{prefix}] {line}", end="", flush=True)

threading.Thread(target=pipe_reader, args=(main_proj.stdout, "MAIN"), daemon=True).start()
threading.Thread(target=pipe_reader, args=(dashboard.stdout, "DASH"), daemon=True).start()

time.sleep(3)

if main_proj.poll() is not None:
    print("\n[LAUNCHER] Main project exited prematurely. It may need:")
    print("         - OPC UA server running on opc.tcp://127.0.0.1:5501")
    print("         - Required hardware (COM ports) or skip by configuring")
    print("         - Check output above for error details")
    print("[LAUNCHER] Dashboard is still running at http://localhost:8000")
    print("[LAUNCHER] Press Ctrl+C to stop\n")

try:
    while True:
        time.sleep(1)
        if main_proj.poll() is not None and dashboard.poll() is not None:
            print("[LAUNCHER] All processes exited.")
            break
except KeyboardInterrupt:
    cleanup()
