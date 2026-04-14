import socket, json, threading, time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.opcua import opcua_update
from sample.tcpClient import tcp_client
from sample.tcpClient import tcp_connection_manager
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def main():
    # Keep main thread alive
    try:
        # Establish OPC Connection as Client
        opc.connect()
        
        # Start reconnect manager
        threading.Thread(target=conn_mgr.connect, daemon=True).start()
        
        # Serial Data-in Thread
        threading.Thread(target=controller.routine1, args=(opc,), daemon=True).start()
        
        # TCP send & receive threads
        threading.Thread(target=tcp_client.send_data, args=(conn_mgr, state_manager.tcp_payload,), daemon=True).start()
        threading.Thread(target=tcp_client.receive_data, args=(conn_mgr,), daemon=True).start()
        
        while True: # TCP/OPCUA Data-transfer
            opcua_update.update_opc_elements(opc)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        conn_mgr.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn_mgr.close()
        opc.disconnect()

if __name__ == "__main__":
    # OPCUA Client Object
    opc = PSOWeighbridgeClient(
        endpoint=config_loader.opc_config_load("endpoint", 0),
        namespace_uri=config_loader.opc_config_load("namespaceUri", 0),
        server_object_name=config_loader.opc_config_load("serverObjectName", 0)
    )
    
    # Establishing TCP Connection Manager
    conn_mgr = tcp_connection_manager.TCPConnectionManager(tcp_client.SERVER_IP, tcp_client.SERVER_PORT)
    
    # OPCUA Update Thread
    # threading.Thread(target=opcua_update.update_opc_elements, args=(opc, sock,), daemon=True).start()
    
    #Run Main()
    main()