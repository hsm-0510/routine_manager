from sample.utils import config_loader
import os
import json

# Settings and Response of Loadcell Indicator Device 1
response_device_1 = {
    "deviceName": config_loader.serial_config_load("deviceName", 0),
    "isActive:": config_loader.serial_config_load("isActive", 0),
    "deviceID": config_loader.serial_config_load("deviceID", 0),
    "comPort": config_loader.serial_config_load("comPort", 0),
    "baudrate": config_loader.serial_config_load("baudrate", 0),
    "timeout": config_loader.serial_config_load("timeout", 0),
    "pollingInterval": config_loader.serial_config_load("pollingInterval", 0),
    "signBit": "+",
    "handshakeResponse": "AA00",
    "grossWeight": 0,
    "tareWeight": 0,
    "netWeight": 0,
    "decimalPoints": 0,
    "xorCheck1": "0",
    "xorCheck2": "0"
}

# Settings and Response of Loadcell Indicator Device 2
response_device_2 = {
    "deviceName": config_loader.serial_config_load("deviceName", 1),
    "isActive:": config_loader.serial_config_load("isActive", 1),
    "deviceID": config_loader.serial_config_load("deviceID", 1),
    "comPort": config_loader.serial_config_load("comPort", 1),
    "baudrate": config_loader.serial_config_load("baudrate", 1),
    "timeout": config_loader.serial_config_load("timeout", 1),
    "pollingInterval": config_loader.serial_config_load("pollingInterval", 1),
    "signBit": "+",
    "handshakeResponse": "AA00",
    "grossWeight": 0,
    "tareWeight": 0,
    "netWeight": 0,
    "decimalPoints": 0,
    "xorCheck1": "0",
    "xorCheck2": "0"
}

# Other Tags
misc_tags = {
            "RFID_Scanner": [
                {"dataRFID_Entrance": "00000000"},
                {"dataRFID_Exit": "0000000"},
                {"scan_status_rfid1": 0},
                {"scan_status_rfid2": 0}
            ],
            "KIOSK": [
                {"kiosk_button_entrance": 0},
                {"kiosk_button_exit": 0},
                {"kiosk_print_control_entrance": 0},
                {"kiosk_print_control_exit": 0},
                {"cardData_entrance": "00000000"},
                {"cardData_exit": "00000000"},
                {"receiptData_1": "00000000"},
                {"receiptData_2": "00000000"},
                {"receiptData_3": "00000000"},
                {"receiptData_4": "00000000"},
                {"receiptData_5": "00000000"},
                {"receiptData_6": "00000000"}
            ]
}

# TCP Payload of Waveshare Module (Dictionary)
# Any changes made to tcp_payload.json must be reflected in the waveshare firmware as well
tcp_payload = config_loader.tcp_payload_config_load()

# System Configuration (Dictionary)
system_config = config_loader.system_config_load()

def state_manager_update(config, key, value, idNum=0):
    for section in config:  # system config dictionary
        if key in config[section]:
            config[section][key][idNum] = value
            return True  # update successful
    return False  # key not found

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