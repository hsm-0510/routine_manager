import socket
import json
import threading
import time

SERVER_IP = "192.168.10.60"
SERVER_PORT = 80

# Send Function
def send_data(sock):
    while True:    
        payload = {
            "outputs": {
                "control_entranceLB": 1,
                "control_exitLB": 1
            },
            "status": {
                "vehicle_alignment_status": 1,
                "driver_absence_status": 1
            }
        }
    
        try:
            message = json.dumps(payload) + "\n"
            sock.sendall(message.encode())
            print(f"[SENT] {message.strip()}")
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            # break
        time.sleep(1)
        
# Receive Function
def receive_data(sock):
    buffer = ""
    
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("[DISCONNECTED]")
                break
            
            buffer += data.decode()
            
            # Process newline-delimited JSON
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    try:
                        parsed = json.loads(line)
                        print(f"[RECEIVED] {json.dumps(parsed, indent=2)}")
                    except json.JSONDecodeError:
                        print("[INVALID JSON], line")
            time.sleep(1)
        except Exception as e:
            print(f"[RECV ERROR] {e}")
            break