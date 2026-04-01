import socket
import json
import threading
import time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.tcpClient import tcp_client
from sample.utils import config_loader

def main():
    # Keep main thread alive
    try:
        # Establish OPC Connection as Client
        opc.connect()
        while True: # TCP/OPCUA Data-transfer
            # Update Time
            time.sleep(1)
            #
            
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        sock.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        opc.disconnect()
    
    # Miscellaneous
    try:
        opc.connect()

        # -----------------------------
        # READ examples
        # -----------------------------
        opc.read_tag("Entrance_XK3190_DS8", "gross_weight_WB1")
        opc.read_tag("Exit_XK3190_DS8", "gross_weight_WB2")
        opc.read_tag("Waveshare_Monitoring", "entranceLB_status")
        opc.read_tag("RFID Scanner", "dataRFID_Entrance")
        opc.read_tag("Camera_Detection", "driver_absence_status")

        # -----------------------------
        # WRITE examples
        # Since your server created these tags as strings,
        # write string values unless you later change tag types.
        # -----------------------------
        opc.write_tag("Entrance_XK3190_DS8", "gross_weight_WB1", "24560")
        opc.write_tag("Entrance_XK3190_DS8", "weight_capture_status1", "CAPTURED")
        opc.write_tag("Waveshare_Controlling", "control_entranceLB", "OPEN")
        opc.write_tag("KIOSK", "kiosk_button_entrance", "PRESSED")
        opc.write_tag("RFID Scanner", "dataRFID_Entrance", "E2000017221101441890ABCD")

        # Read back after write
        opc.read_tag("Entrance_XK3190_DS8", "gross_weight_WB1")
        opc.read_tag("Waveshare_Controlling", "control_entranceLB")

        # Browse all tags in one category
        opc.browse_category("KIOSK")

        # Optional loop example
        print("\nPolling some values...")
        for _ in range(3):
            opc.read_tag("Entrance_XK3190_DS8", "gross_weight_WB1")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        opc.disconnect()

if __name__ == "__main__":
    # Match your server config
    # ENDPOINT = config_loader.opc_config_load("endpoint", 0)
    # NAMESPACE_URI = config_loader.opc_config_load("namespaceUri", 0)
    # SERVER_OBJECT_NAME = config_loader.opc_config_load("serverObjectName", 0)

    # OPCUA Client Object
    opc = PSOWeighbridgeClient(
        endpoint=config_loader.opc_config_load("endpoint", 0),
        namespace_uri=config_loader.opc_config_load("namespaceUri", 0),
        server_object_name=config_loader.opc_config_load("serverObjectName", 0)
    )
    
    # Establish TCP Socket Connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_client.connect_tcp_socket(sock, tcp_client.SERVER_IP, tcp_client.SERVER_PORT)
    
    # TCP send & receive threads
    threading.Thread(target=tcp_client.send_data, args=(sock,), daemon=True).start()
    threading.Thread(target=tcp_client.receive_data, args=(sock,), daemon=True).start()
    
    #Run Main()
    main()