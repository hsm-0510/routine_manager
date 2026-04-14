import time, serial
from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.tcpClient import tcp_client
from sample.core import state_manager
from sample.utils import config_loader

# Load active_status, port and baudrate of indicator 1:
dev1 = config_loader.serial_config_load("isActive_entranceWB1", 0)
port1 = config_loader.serial_config_load("comPort_entranceWB1", 0)
baudrate1 = config_loader.serial_config_load("baudrate_entranceWB1", 0)
timeout1 = config_loader.serial_config_load("timeout_entranceWB1", 0)
# Load active_status, port an baudrate of indicator 2:
dev2 = config_loader.serial_config_load("isActive_exitWB2", 1)
port2 = config_loader.serial_config_load("comPort_exitWB2", 1)
baudrate2 = config_loader.serial_config_load("baudrate_exitWB2", 1)
timeout2 = config_loader.serial_config_load("timeout_exitWB2", 1)

def connect_serial(port, baudrate, timeout):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("Serial Port Openned")
        return ser
    except:
        print(f"Could Not Open Serial Port: {port}")
        return None

def disconnect_serial(ser):
    try:
        ser.close()
        print("Serial Port Closed")
    except:
        print("Could Not Close Serial Port")

def send_command(ser, cmd):
    try:
        # print(f"Sending: {cmd.hex(' ')}")
        ser.write(cmd)
        time.sleep(0.1)
        response = ser.read_all()
        # print(f"Received (hex):", response)
        return response
    except Exception as e:
        print(f"Could not send command: {cmd} to {ser}, error: {e}")

def checkActiveDevices():
    try:
        ser1 = connect_serial(port1, baudrate1, timeout1)
        if ser1.is_open:
            dev1 = 1
        else:
            dev1 = 0
        disconnect_serial(ser1)
    except:
        print(f"Could Not Connect with {port1}")
        dev1 = 0
    try:
        ser2 = connect_serial(port2, baudrate2, timeout2)
        if ser2.is_open:
            dev2 = 1
        else:
            dev2 = 0
        disconnect_serial(ser2)
    except:
        print(f"Could Not Connect with {port2}")
        dev2 = 0
    return dev1+dev2, dev1, dev2

def record_serial_response(ser, device, opc):
    # Command / Response Record
    responseA = send_command(ser, commands.commands["handshake"])
    responseB = send_command(ser, commands.commands["gross_weight"])
    responseC = send_command(ser, commands.commands["tare_weight"])
    responseD = send_command(ser, commands.commands["net_weight"]) 
    
    if device == "device1":
        # Updating Device 1 Dictionary
        commands.response_device_1["handshakeResponse"] = parser.parse_handshakeResponse(responseA)
        commands.response_device_1["signBit"] = parser.parse_signBit(responseB)
        commands.response_device_1["grossWeight"] = parser.parse_grossWeight(responseB,
                                                                            parser.parse_signBit(responseB),
                                                                            parser.parse_decimalPoints(responseB))
        tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_entranceWB1", commands.response_device_1["grossWeight"])
        opc.write_tag("Entrance_XK3190_DS8",
                        "gross_weight_entranceWB1",
                        str(commands.response_device_1["grossWeight"]))
        commands.response_device_1["decimalPoints"] = parser.parse_decimalPoints(responseB)
    elif device == "device2":
        # Updating Device 2 Dictionary
        commands.response_device_2["handshakeResponse"] = parser.parse_handshakeResponse(responseA)
        commands.response_device_2["signBit"] = parser.parse_signBit(responseB)
        commands.response_device_2["grossWeight"] = parser.parse_grossWeight(responseB,
                                                                            parser.parse_signBit(responseB),
                                                                            parser.parse_decimalPoints(responseB))
        tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_exitWB2", commands.response_device_2["grossWeight"])
        opc.write_tag("Exit_XK3190_DS8",
                        "gross_weight_exitWB2",
                        str(commands.response_device_2["grossWeight"]))
        commands.response_device_2["decimalPoints"] = parser.parse_decimalPoints(responseB)
    else:
        print("[RECORD ERROR]: Wrong Device Being Accessed!")
    
    