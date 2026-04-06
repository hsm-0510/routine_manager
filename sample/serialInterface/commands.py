from sample.utils import config_loader

# Commands dictionary (hex -> bytes)
commands = {
    "handshake": bytes.fromhex("02 41 41 30 30 03"),
    "gross_weight": bytes.fromhex("02 41 42 30 33 03"),
    "tare_weight": bytes.fromhex("02 41 43 30 32 03"),
    "net_weight": bytes.fromhex("02 41 44 30 35 03")
}
# Settings and Response of Device 1
response_device_1 = {
    "deviceName_entranceWB1": config_loader.serial_config_load("deviceName_entranceWB1", 0),
    "isActive_entranceWB1:": config_loader.serial_config_load("isActive_entranceWB1", 0),
    "deviceID_entranceWB1": config_loader.serial_config_load("deviceID_entranceWB1", 0),
    "comPort_entranceWB1": config_loader.serial_config_load("comPort_entranceWB1", 0),
    "baudrate_entranceWB1": config_loader.serial_config_load("baudrate_entranceWB1", 0),
    "timeout_entranceWB1": config_loader.serial_config_load("timeout_entranceWB1", 0),
    "pollingInterval_entranceWB1": config_loader.serial_config_load("pollingInterval_entranceWB1", 0),
    "signBit": "+",
    "handshakeResponse": "AA00",
    "grossWeight": 0,
    "tareWeight": 0,
    "netWeight": 0,
    "decimalPoints": 0,
    "xorCheck1": "0",
    "xorCheck2": "0"
}

# Settings and Response of Device 2
response_device_2 = {
    "deviceName_exitWB2": config_loader.serial_config_load("deviceName_exitWB2", 1),
    "isActive_exitWB2:": config_loader.serial_config_load("isActive_exitWB2", 1),
    "deviceID_exitWB2": config_loader.serial_config_load("deviceID_exitWB2", 1),
    "comPort_exitWB2": config_loader.serial_config_load("comPort_exitWB2", 1),
    "baudrate_exitWB2": config_loader.serial_config_load("baudrate_exitWB2", 1),
    "timeout_exitWB2": config_loader.serial_config_load("timeout_exitWB2", 1),
    "pollingInterval_exitWB2": config_loader.serial_config_load("pollingInterval_exitWB2", 1),
    "signBit": "+",
    "handshakeResponse": "AA00",
    "grossWeight": 0,
    "tareWeight": 0,
    "netWeight": 0,
    "decimalPoints": 0,
    "xorCheck1": "0",
    "xorCheck2": "0"
}