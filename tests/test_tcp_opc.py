import socket
import json
import threading
import time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.opcua import opcua_update
from sample.tcpClient import tcp_client
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def main():
    # Keep main thread alive
    try:
        while True: # TCP/OPCUA Data-transfer
            opcua_update.update_opc_elements(opc, sock)
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        sock.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        opc.disconnect()

if __name__ == "__main__":
    # OPCUA Client Object
    opc = PSOWeighbridgeClient(
        endpoint=config_loader.opc_config_load("endpoint", 0),
        namespace_uri=config_loader.opc_config_load("namespaceUri", 0),
        server_object_name=config_loader.opc_config_load("serverObjectName", 0)
    )
    
    # Establish OPC Connection as Client
    opc.connect()
    
    # Establish TCP Socket Connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_client.connect_tcp_socket(sock, tcp_client.SERVER_IP, tcp_client.SERVER_PORT)
    
    # Serial Data-in Thread
    threading.Thread(target=controller.routine1, args=(opc,), daemon=True).start()
    
    # TCP send & receive threads
    threading.Thread(target=tcp_client.send_data, args=(sock, state_manager.tcp_payload,), daemon=True).start()
    threading.Thread(target=tcp_client.receive_data, args=(sock,), daemon=True).start()
    
    # OPCUA Update Thread
    threading.Thread(target=opcua_update.update_opc_elements, args=(opc, sock,), daemon=True).start()
    
    #Run Main()
    main()