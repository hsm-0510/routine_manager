import socket
import json
import threading
import time
from sample.utils import config_loader
from sample.core import state_manager

SERVER_IP = config_loader.waveshare_config_load("serverIp", 0)
SERVER_PORT = config_loader.waveshare_config_load("serverPort", 0)

# Establish TCP Socket
def connect_tcp_socket(sock, serverIP, serverPort):
    try:
        sock.connect((serverIP, serverPort))
        print(f"Connected to {serverIP}:{serverPort}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

# Update Payload
def update_payload(payload, key, value):
    for section in payload:  # "outputs", "status"
        if key in payload[section]:
            payload[section][key] = value
            return True  # update successful
    return False  # key not found

# Inquire Payload
def get_payload_value(payload, key):
    for section in payload:  # "outputs", "status"
        if key in payload[section]:
            return payload[section][key]
    return None  # key not found

# Send Function
def send_data(sock, payload):
    while True:
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
                        
                        # 🔥 UPDATE PAYLOAD HERE
                        for section in parsed:  # "inputs"
                            if section in state_manager.tcp_payload:
                                for key, value in parsed[section].items():
                                    updated = update_payload(state_manager.tcp_payload, key, value)
                                    if updated:
                                        print(f"[UPDATED] {key} = {value}")
                                    else:
                                        print(f"[WARNING] Key not found: {key}")

                        print(f"[CURRENT PAYLOAD]\n{json.dumps(state_manager.tcp_payload, indent=2)}")
                        
                    except json.JSONDecodeError:
                        print("[INVALID JSON], line")
            time.sleep(1)
        except Exception as e:
            print(f"[RECV ERROR] {e}")
            break