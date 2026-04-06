import threading
import socket
from sample.opcua import opcua_update
import time

class TCPConnectionManager:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        self.sock = None
        self.lock = threading.Lock()
        self.connected = threading.Event()
        self.stop_event = threading.Event()

    def _create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.settimeout(3)  # important so recv does not block forever
        return s

    def connect(self):
        while not self.stop_event.is_set():
            if self.connected.is_set():
                time.sleep(1)
                continue

            try:
                print(f"Trying TCP connection to {self.server_ip}:{self.server_port} ...")
                new_sock = self._create_socket()
                new_sock.connect((self.server_ip, self.server_port))

                with self.lock:
                    if self.sock:
                        try:
                            self.sock.close()
                        except:
                            pass
                    self.sock = new_sock

                self.connected.set()
                print("TCP connected")

            except Exception as e:
                print(f"TCP connect failed: {e}")
                time.sleep(2)

    def get_socket(self):
        with self.lock:
            return self.sock

    def mark_disconnected(self):
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None

        if self.connected.is_set():
            print("TCP disconnected. Reconnecting...")
        self.connected.clear()

    def close(self):
        self.stop_event.set()
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
        self.connected.clear()
    
    def opcua_update_worker(opc, conn_mgr):
        while not conn_mgr.stop_event.is_set():
            if not conn_mgr.connected.wait(timeout=1):
                continue

            sock = conn_mgr.get_socket()
            if sock is None:
                continue

            try:
                opcua_update.update_opc_elements(opc, sock)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                print(f"OPCUA update lost TCP connection: {e}")
                conn_mgr.mark_disconnected()
            except Exception as e:
                print(f"OPCUA update error: {e}")
                time.sleep(0.2)