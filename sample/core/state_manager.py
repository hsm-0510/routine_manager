from sample.utils import config_loader
import os
import json

# Other Tags
misc_tags = {
    "RFID_Scanner": {
        "dataRFID_Entrance": "00000000",
        "dataRFID_Exit": "00000000",
        "scan_status_rfid1": 0,
        "scan_status_rfid2": 0
    },
    "KIOSK": {
        "kiosk_button_entrance": 0,
        "kiosk_button_exit": 0,
        "kiosk_print_control_entrance": 0,
        "kiosk_print_control_exit": 0,
        "cardData_entrance": "00000000",
        "cardData_exit": "00000000",
        "receiptData_1": "00000000",
        "receiptData_2": "00000000",
        "receiptData_3": "00000000",
        "receiptData_4": "00000000",
        "receiptData_5": "00000000",
        "receiptData_6": "00000000"
    }
}

# TCP Payload of Waveshare Module (Dictionary)
# Any changes made to tcp_payload.json must be reflected in the waveshare firmware as well
tcp_payload = config_loader.tcp_payload_config_load()

# System Configuration (Dictionary)
system_config = config_loader.system_config_load()

def state_manager_update(section, key, value):
    misc_tags[section][key] = value

def state_manager_inquire(key=None, idNum=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/system_config.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            opcServer = data.get("serial_device", [])
            
            if opcServer:
                device_info = opcServer[idNum]
                return device_info.get(key, f"Error: Key '{key}' not fount")
            else:
                return "Error: 'opc_server' list is empty"
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."