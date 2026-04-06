import socket
import json
import threading
import time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.tcpClient import tcp_client
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def update_opc_elements(opc):
    # Update System Configurations Entrance Weighbridge
    for required_dictionary in state_manager.system_config["serial_device"]:
        for key in required_dictionary:
            print(f"[KEY:VALUE]: {key}:{required_dictionary[key]}")
            if "_entranceWB1" in key:
                opc.write_tag("Entrance_XK3190_DS8",
                                str(key),
                                str(required_dictionary[key]))
    
    # Update System Configurations Exit Weighbridge
    for required_dictionary in state_manager.system_config["serial_device"]:
        for key in required_dictionary:
            if "_exitWB2" in key:
                opc.write_tag("Exit_XK3190_DS8",
                            str(key),
                            str(required_dictionary[key]))
    
    # Update OPCUA Waveshare Digital Inputs Status
    for section in state_manager.tcp_payload:
        for key in state_manager.tcp_payload["inputs"]:
            opc.write_tag("Waveshare_Monitoring",
                          key,
                          str(tcp_client.get_payload_value(state_manager.tcp_payload, key)))
    
    # Update TCP_Payload (WAVESHARE RELAY OUTPUTS)
    for section in state_manager.tcp_payload:
        for key in state_manager.tcp_payload["outputs"]:
            tcp_client.update_payload(state_manager.tcp_payload,
                                        key,
                                        int(opc.read_tag("Waveshare_Controlling", key)))
    
    # Update TCP_Payload (WAVESHARE STATUSES)
    # for section in state_manager.tcp_payload:
    #     for key in state_manager.tcp_payload["status"]:
    #         tcp_client.update_payload(state_manager.tcp_payload,
    #                                   key,
    #                                   int(opc.read_tag()))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "vehicle_alignment_status_camera",
                                int(opc.read_tag("Camera_Detection", "vehicle_alignment_status_camera")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "driver_absence_status_camera",
                                int(opc.read_tag("Camera_Detection", "driver_absence_status_camera")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "weight_capture_entranceControl1",
                                int(opc.read_tag("Entrance_XK3190_DS8", "weight_capture_entranceControl1")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "weight_capture_exitControl2",
                                int(opc.read_tag("Exit_XK3190_DS8", "weight_capture_exitControl2")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "scan_status_rfid1",
                                int(opc.read_tag("RFID_Scanner", "scan_status_rfid1")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "scan_status_rfid2",
                                int(opc.read_tag("RFID_Scanner", "scan_status_rfid2")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_print_control_entrance",
                                int(opc.read_tag("KIOSK", "kiosk_print_control_entrance")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_print_control_exit",
                                int(opc.read_tag("KIOSK", "kiosk_print_control_exit")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_button_entrance",
                                int(opc.read_tag("KIOSK", "kiosk_button_entrance")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_button_exit",
                                int(opc.read_tag("KIOSK", "kiosk_button_exit")))