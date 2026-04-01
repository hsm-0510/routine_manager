import socket
import json
import threading
import time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.tcpClient import tcp_client
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def main():
    # Keep main thread alive
    try:
        # Establish OPC Connection as Client
        opc.connect()
        while True: # TCP/OPCUA Data-transfer
            # Update Time
            time.sleep(1)
            
            # # Write OPC Tags
            # opc.write_tag("Entrance_XK3190_DS8",
            #               "gross_weight_WB1",
            #               str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB1")))
            # opc.write_tag("Exit_XK3190_DS8",
            #               "gross_weight_WB2",
            #               str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB2")))
            
            # Update TCP_Payload (WAVESHARE RELAY OUTPUTS)
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "control_entranceLB",
                                      int(opc.read_tag("Waveshare_Controlling", "control_entranceLB")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "control_exitLB",
                                      int(opc.read_tag("Waveshare_Controlling", "control_exitLB")))
            
            # Update TCP_Payload (WAVESHARE STATUSES)
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "vehicle_alignment_status",
                                      int(opc.read_tag("Camera_Detection", "vehicle_alignment_status")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "driver_absence_status",
                                      int(opc.read_tag("Camera_Detection", "driver_absence_status")))
            # tcp_client.update_payload(state_manager.tcp_payload,
            #                           "gross_weight_WB1",
            #                           int(opc.read_tag("Entrance_XK3190_DS8", "gross_weight_WB1")))
            # tcp_client.update_payload(state_manager.tcp_payload,
            #                           "gross_weight_WB2",
            #                           int(opc.read_tag("Exit_XK3190_DS8", "gross_weight_WB2")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "weight_capture_status1",
                                      int(opc.read_tag("Entrance_XK3190_DS8", "weight_capture_status1")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "weight_capture_status2",
                                      int(opc.read_tag("Exit_XK3190_DS8", "weight_capture_status2")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "scan_status_rfid1",
                                      int(opc.read_tag("RFID_Scanner", "scan_status_rfid1")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "scan_status_rfid2",
                                      int(opc.read_tag("RFID_Scanner", "scan_status_rfid2")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "print_status_entrance",
                                      int(opc.read_tag("KIOSK", "print_status_entrance")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "print_status_exit",
                                      int(opc.read_tag("KIOSK", "print_status_exit")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "kiosk_button_entrance",
                                      int(opc.read_tag("KIOSK", "kiosk_button_entrance")))
            tcp_client.update_payload(state_manager.tcp_payload,
                                      "kiosk_button_exit",
                                      int(opc.read_tag("KIOSK", "kiosk_button_exit")))
            
            
            
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        sock.close()
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
    
    # Serial Data-in Thread
    threading.Thread(target=controller.routine1(opc), daemon=True).start()
    
    # TCP send & receive threads
    threading.Thread(target=tcp_client.send_data, args=(sock, state_manager.tcp_payload,), daemon=True).start()
    threading.Thread(target=tcp_client.receive_data, args=(sock,), daemon=True).start()
    
    #Run Main()
    main()