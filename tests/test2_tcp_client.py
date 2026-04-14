import socket, json, threading, time
from sample.tcpClient import tcp_client

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((tcp_client.SERVER_IP, tcp_client.SERVER_PORT))
        print(f"Connected to {tcp_client.SERVER_IP}:{tcp_client.SERVER_PORT}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return
    
    # Start send & receive threads
    threading.Thread(target=tcp_client.send_data, args=(sock,), daemon=True).start()
    threading.Thread(target=tcp_client.receive_data, args=(sock,), daemon=True).start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        sock.close()

if __name__ == "__main__":
    main()