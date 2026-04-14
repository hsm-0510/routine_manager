import socket, json, threading, time
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.tcpClient import tcp_client
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller

def is_valid(v):
    if v is None:
        return False
    if isinstance(v, str) and v.strip() == "":
        return False
    try:
        if float(v) == 0:
            # only reject if truly zero AND you expect non-zero
            return False
    except:
        pass
    return True

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
                                        int(opc.read_tag("Waveshare_Controlling", key, "int")))
    # Update SAP Data
    # for key in state_manager.misc_tags["SAP_DATA"]:
    #     state_manager.state_manager_update("SAP_DATA",
    #                                 key,
    #                                 opc.read_tag("SAP_DATA", key))
    changed = False

    for key in state_manager.misc_tags["SAP_DATA"]:
        if not key.startswith("SAP_"):
            continue

        new_val = opc.read_tag("SAP_DATA", key, "string")
        print(f"SAP_DATA: {key}: {opc.read_tag("SAP_DATA", key, "string")}")
        old_val = state_manager.misc_tags["SAP_DATA"].get(key)

        if is_valid(new_val) and new_val != old_val:
            state_manager.state_manager_update("SAP_DATA", key, new_val)
            changed = True

    print(f"[SPECIAL PRINT: SAP_batch_start_time: {opc.read_tag("SAP_DATA", "SAP_batch_start_time", "string")}]")
    print(f"[SPECIAL PRINT: SAP_batch_end_time: {opc.read_tag("SAP_DATA", "SAP_batch_end_time", "string")}]")
    print(f"[SPECIAL PRINT: SAP_compartment_name: {opc.read_tag("SAP_DATA", "SAP_compartment_name", "string")}]")
    print(f"[SPECIAL PRINT: SAP_expected_net_weight: {opc.read_tag("SAP_DATA", "SAP_expected_net_weight", "string")}]")
    print(f"[SPECIAL PRINT: SAP_trailer_net_weight: {opc.read_tag("SAP_DATA", "SAP_trailer_net_weight", "string")}]")
    
    # 🔥 ONLY mark update when real change happened
    if changed:
        state_manager.mark_sap_update()
    
    # Update TCP_Payload (WAVESHARE STATUSES)
    tcp_client.update_payload(state_manager.tcp_payload,
                                "vehicle_alignment_status_camera",
                                int(opc.read_tag("Camera_Detection", "vehicle_alignment_status_camera", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "driver_absence_status_camera",
                                int(opc.read_tag("Camera_Detection", "driver_absence_status_camera", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "weight_capture_entranceControl1",
                                int(opc.read_tag("Entrance_XK3190_DS8", "weight_capture_entranceControl1", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "weight_capture_exitControl2",
                                int(opc.read_tag("Exit_XK3190_DS8", "weight_capture_exitControl2", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "scan_status_rfid1",
                                int(opc.read_tag("RFID_Scanner", "scan_status_rfid1", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "scan_status_rfid2",
                                int(opc.read_tag("RFID_Scanner", "scan_status_rfid2", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_print_control_entrance",
                                int(opc.read_tag("KIOSK", "kiosk_print_control_entrance", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_print_control_exit",
                                int(opc.read_tag("KIOSK", "kiosk_print_control_exit", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_button_entrance",
                                int(opc.read_tag("KIOSK", "kiosk_button_entrance", "int")))
    tcp_client.update_payload(state_manager.tcp_payload,
                                "kiosk_button_exit",
                                int(opc.read_tag("KIOSK", "kiosk_button_exit", "int")))
    
    # UPDATE MISC TAGS OF STATUS MANAGER:
    state_manager.state_manager_update("KIOSK",
                                       "kiosk_print_control_entrance",
                                       opc.read_tag("KIOSK", "kiosk_print_control_entrance", "int"))
    state_manager.state_manager_update("KIOSK",
                                       "kiosk_print_control_exit",
                                       opc.read_tag("KIOSK", "kiosk_print_control_exit", "int"))
    state_manager.state_manager_update("KIOSK",
                                       "kiosk_button_entrance",
                                       opc.read_tag("KIOSK", "kiosk_button_entrance", "int"))
    state_manager.state_manager_update("KIOSK",
                                       "kiosk_button_exit",
                                       opc.read_tag("KIOSK", "kiosk_button_exit", "int"))
    state_manager.state_manager_update("KIOSK",
                                       "cardData_entrance",
                                       opc.read_tag("KIOSK", "cardData_entrance", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "cardData_exit",
                                       opc.read_tag("KIOSK", "cardData_exit", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_1",
                                       opc.read_tag("KIOSK", "receiptData_1", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_2",
                                       opc.read_tag("KIOSK", "receiptData_2", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_3",
                                       opc.read_tag("KIOSK", "receiptData_3", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_4",
                                       opc.read_tag("KIOSK", "receiptData_4", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_5",
                                       opc.read_tag("KIOSK", "receiptData_5", "string"))
    state_manager.state_manager_update("KIOSK",
                                       "receiptData_6",
                                       opc.read_tag("KIOSK", "receiptData_6", "string"))
    state_manager.state_manager_update("RFID_Scanner",
                                       "dataRFID_Entrance",
                                       opc.read_tag("RFID_Scanner", "dataRFID_Entrance", "string"))
    state_manager.state_manager_update("RFID_Scanner",
                                       "dataRFID_Exit",
                                       opc.read_tag("RFID_Scanner", "dataRFID_Exit", "string"))
    state_manager.state_manager_update("RFID_Scanner",
                                       "scan_status_rfid1",
                                       opc.read_tag("RFID_Scanner", "scan_status_rfid1", "int"))
    state_manager.state_manager_update("RFID_Scanner",
                                       "scan_status_rfid2",
                                       opc.read_tag("RFID_Scanner", "scan_status_rfid2", "int"))
    
    