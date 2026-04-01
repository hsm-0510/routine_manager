from sample.utils import config_loader

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

# TCP Payload of Waveshare Module
# Any changes made to tcp_payload.json must be reflected in the waveshare firmware as well
tcp_payload = config_loader.tcp_payload_config_load()