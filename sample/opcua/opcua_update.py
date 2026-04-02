import socket
import json
import threading
import time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.tcpClient import tcp_client
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def update_opc_elements(opc, sock):
    # Update Time
    time.sleep(1)
    
    # Update System Configurations Entrance Weigh Bridge
    opc.write_tag("Entrance_XK3190_DS8",
                    "deviceName_entranceWB1",
                    str(state_manager.state_manager_inquire("deviceName", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "isActive_entranceWB1",
                    str(state_manager.state_manager_inquire("isActive", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "deviceID_entranceWB1",
                    str(state_manager.state_manager_inquire("deviceID", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "comPort_entranceWB1",
                    str(state_manager.state_manager_inquire("comPort", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "baudrate_entranceWB1",
                    str(state_manager.state_manager_inquire("baudrate", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "timeout_entranceWB1",
                    str(state_manager.state_manager_inquire("timeout", 0)))
    opc.write_tag("Entrance_XK3190_DS8",
                    "pollingInterval_entranceWB1",
                    str(state_manager.state_manager_inquire("pollingInterval", 0)))
    
    # Update System Configurations Entrance Weigh Bridge
    opc.write_tag("Exit_XK3190_DS8",
                    "deviceName_exitWB2",
                    str(state_manager.state_manager_inquire("deviceName", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "isActive_exitWB2",
                    str(state_manager.state_manager_inquire("isActive", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "deviceID_exitWB2",
                    str(state_manager.state_manager_inquire("deviceID", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "comPort_exitWB2",
                    str(state_manager.state_manager_inquire("comPort", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "baudrate_exitWB2",
                    str(state_manager.state_manager_inquire("baudrate", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "timeout_exitWB2",
                    str(state_manager.state_manager_inquire("timeout", 1)))
    opc.write_tag("Exit_XK3190_DS8",
                    "pollingInterval_exitWB2",
                    str(state_manager.state_manager_inquire("pollingInterval", 1)))
    
    
    # Update OPCUA Waveshare Digital Inputs Status
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_01_entranceLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_01_entranceLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_02_entranceLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_02_entranceLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_03_entranceLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_03_entranceLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_01_exitLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_01_exitLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_02_exitLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_02_exitLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "irSens_03_exitLB",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "irSens_03_exitLB")))
    opc.write_tag("Waveshare_Monitoring",
                    "entranceLB_status",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "entranceLB_status")))
    opc.write_tag("Waveshare_Monitoring",
                    "exitLB_status",
                    str(tcp_client.get_payload_value(state_manager.tcp_payload, "exitLB_status")))
    
    
    # Update TCP_Payload (WAVESHARE RELAY OUTPUTS)
    tcp_client.update_payload(state_manager.tcp_payload,
                                "control_entranceLB",
                                int(opc.read_tag("Waveshare_Controlling", "control_entranceLB")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "control_exitLB",
                                int(opc.read_tag("Waveshare_Controlling", "control_exitLB")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_3",
                                int(opc.read_tag("Waveshare_Controlling", "channel_3")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_4",
                                int(opc.read_tag("Waveshare_Controlling", "channel_4")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_5",
                                int(opc.read_tag("Waveshare_Controlling", "channel_5")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_6",
                                int(opc.read_tag("Waveshare_Controlling", "channel_6")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_7",
                                int(opc.read_tag("Waveshare_Controlling", "channel_7")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "channel_8",
                                int(opc.read_tag("Waveshare_Controlling", "channel_8")))
    
    # Update TCP_Payload (WAVESHARE STATUSES)
    tcp_client.update_payload(state_manager.tcp_payload,
                                "vehicle_alignment_status",
                                int(opc.read_tag("Camera_Detection", "vehicle_alignment_status")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "driver_absence_status",
                                int(opc.read_tag("Camera_Detection", "driver_absence_status")))
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