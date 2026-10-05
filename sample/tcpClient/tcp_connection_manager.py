import threading, socket, json, time
from sample.opcua import opcua_update
from sample.core.state_manager import write_tcp_status, TCP_BEACON_INTERVAL

class TCPConnectionManager:
    def __init__(self, server_ip, server_port, heartbeat_timeout=15):
        self.server_ip = server_ip
        self.server_port = server_port
        self.heartbeat_timeout = heartbeat_timeout

        self.sock = None
        self.lock = threading.Lock()
        self.connected = threading.Event()
        self.stop_event = threading.Event()
        self.last_heartbeat_time = time.time()
        self.connect_epoch = 0
        self.payload_ref = None

        # Publish "disconnected" immediately so a restart never inherits a
        # stale "connected" from the previous run, then keep the beacon fresh
        # for as long as this process lives.
        write_tcp_status(False)
        self.status_thread = threading.Thread(target=self._status_beacon, daemon=True)
        self.status_thread.start()

    def _status_beacon(self):
        while not self.stop_event.is_set():
            write_tcp_status(self.connected.is_set())
            self.stop_event.wait(TCP_BEACON_INTERVAL)

    def _create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.settimeout(3)  # important so recv does not block forever
        return s

    def connect(self):
        while not self.stop_event.is_set():
            if self.connected.is_set():
                if time.time() - self.last_heartbeat_time > self.heartbeat_timeout:
                    print(f"[ALARM] Heartbeat timeout ({self.heartbeat_timeout}s) — forcing reconnection")
                    self.mark_disconnected()
                    continue
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
                self.last_heartbeat_time = time.time()
                self.connect_epoch += 1
                write_tcp_status(True)
                print("TCP connected")

                try:
                    if self.payload_ref is not None:
                        init_msg = json.dumps(self.payload_ref) + "\n"
                        new_sock.sendall(init_msg.encode())
                        print(f"[SENT] {init_msg.strip()}")
                except Exception:
                    pass

            except Exception as e:
                print(f"[ALARM] TCP connection failed: {e}")
                time.sleep(2)

    def update_heartbeat(self):
        self.last_heartbeat_time = time.time()

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
        write_tcp_status(False)

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
        write_tcp_status(False)
    
    def opcua_update_worker(opc, conn_mgr):
        while not conn_mgr.stop_event.is_set():
            if not conn_mgr.connected.wait(timeout=1):
                continue

            sock = conn_mgr.get_socket()
            if sock is None:
                continue

            try:
                opcua_update.update_opc_elements(opc)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                print(f"OPCUA update lost TCP connection: {e}")
                conn_mgr.mark_disconnected()
            except Exception as e:
                print(f"OPCUA update error: {e}")
                time.sleep(0.2)