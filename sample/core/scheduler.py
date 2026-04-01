import time
from sample.core import scheduler
from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader
from sample.opcua import opcua_client
from sample.opcua import opcua_update
from sample.tcpClient import tcp_client
from sample.core import state_manager

def scheduler1(opc, port, baudrate, timeout, idNum):
    # Establishing Device Connection
    try:
        ser = serial_client.connect_serial(port, baudrate, timeout)
        print("Established Connection with Device 1")
    except:
        print(f"Could Not Open Serial Port {port}")
        serial_client.disconnect_serial(ser)
    
    # while True:
    try:
        # Command / Response Record
        responseA = serial_client.send_command(ser, commands.commands["handshake"])
        responseB = serial_client.send_command(ser, commands.commands["gross_weight"])
        responseC = serial_client.send_command(ser, commands.commands["tare_weight"])
        responseD = serial_client.send_command(ser, commands.commands["net_weight"])
        # Updating Device Dictionary
        if idNum == 0:
            commands.response_device_1["handshakeResponse"] = parser.parse_handshakeResponse(responseB)
            commands.response_device_1["signBit"] = parser.parse_signBit(responseB)
            commands.response_device_1["grossWeight"] = parser.parse_grossWeight(responseB,
                                                                                parser.parse_signBit(responseB),
                                                                                parser.parse_decimalPoints(responseB))
            tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_WB1", commands.response_device_1["grossWeight"])
            opc.write_tag("Entrance_XK3190_DS8",
                          "gross_weight_WB1",
                          str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB1")))
            commands.response_device_1["decimalPoints"] = parser.parse_decimalPoints(responseB)
            # Terminal Output
            print(f"Gross Weight Device 1: {parser.parse_grossWeight(responseB, commands.response_device_1["signBit"],
                commands.response_device_1["decimalPoints"])} kg")
        else:
            commands.response_device_2["handshakeResponse"] = parser.parse_handshakeResponse(responseB)
            commands.response_device_2["signBit"] = parser.parse_signBit(responseB)
            commands.response_device_2["grossWeight"] = parser.parse_grossWeight(responseB,
                                                                                parser.parse_signBit(responseB),
                                                                                parser.parse_decimalPoints(responseB))
            tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_WB2", commands.response_device_2["grossWeight"])
            opc.write_tag("Exit_XK3190_DS8",
                          "gross_weight_WB2",
                          str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB2")))
            commands.response_device_2["decimalPoints"] = parser.parse_decimalPoints(responseB)
            # Terminal Output
            print(f"Gross Weight Device 1: {parser.parse_grossWeight(responseB, commands.response_device_2["signBit"],
                commands.response_device_2["decimalPoints"])} kg")
        # Loop Delay
        time.sleep(0.1)
    except Exception as e:
        print("[SCHEDULER 1 ERROR]: {e}")

def scheduler2(opc, port1, baudrate1, timeout1, port2, baudrate2, timeout2):
    # Establishing Connection with Device 1
    try:
        ser1 = serial_client.connect_serial(port1, baudrate1, timeout1)
        print("Established Connection with Device 1")
    except:
        print("Could Not Connect with Device 1")
        serial_client.disconnect_serial(port1, baudrate1, timeout1)
    # Establishing Connection with Device 2       
    try:
        ser2 = serial_client.connect_serial(port2, baudrate2, timeout2)
        print("Established Connection with Device 2")
    except:
        print("Could Not Connect with Device 2")
        serial_client.disconnect_serial(port2, baudrate2, timeout2)
    
    # while True:
    try:
        # Command / Response Record for Device 1
        responseA1 = serial_client.send_command(ser1, commands.commands["handshake"])
        responseB1 = serial_client.send_command(ser1, commands.commands["gross_weight"])
        responseC1 = serial_client.send_command(ser1, commands.commands["tare_weight"])
        responseD1 = serial_client.send_command(ser1, commands.commands["net_weight"])
        # Updating Device 1 Dictionary
        commands.response_device_1["handshakeResponse"] = parser.parse_handshakeResponse(responseB1)
        commands.response_device_1["signBit"] = parser.parse_signBit(responseB1)
        commands.response_device_1["grossWeight"] = parser.parse_grossWeight(responseB1,
                                                                            parser.parse_signBit(responseB1),
                                                                            parser.parse_decimalPoints(responseB1))
        tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_WB1", commands.response_device_1["grossWeight"])
        opc.write_tag("Entrance_XK3190_DS8",
                          "gross_weight_WB1",
                          str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB1")))
        commands.response_device_1["decimalPoints"] = parser.parse_decimalPoints(responseB1) 
        # Command / Response Record for Device 2
        responseA2 = serial_client.send_command(ser2, commands.commands["handshake"])
        responseB2 = serial_client.send_command(ser2, commands.commands["gross_weight"])
        responseC2 = serial_client.send_command(ser2, commands.commands["tare_weight"])
        responseD2 = serial_client.send_command(ser2, commands.commands["net_weight"])
        # Updating Device 2 Dictionary
        commands.response_device_2["handshakeResponse"] = parser.parse_handshakeResponse(responseB2)
        commands.response_device_2["signBit"] = parser.parse_signBit(responseB2)
        commands.response_device_2["grossWeight"] = parser.parse_grossWeight(responseB2,
                                                                            parser.parse_signBit(responseB2),
                                                                            parser.parse_decimalPoints(responseB2))
        tcp_client.update_payload(state_manager.tcp_payload, "gross_weight_WB2", commands.response_device_2["grossWeight"])
        opc.write_tag("Exit_XK3190_DS8",
                          "gross_weight_WB2",
                          str(tcp_client.get_payload_value(state_manager.tcp_payload, "gross_weight_WB2")))
        commands.response_device_2["decimalPoints"] = parser.parse_decimalPoints(responseB2)
        # Terminal Output
        print(f"Gross Weight Device 1: {parser.parse_grossWeight(responseB1, commands.response_device_1["signBit"],
            commands.response_device_1["decimalPoints"])} kg, Gross Weight Device 2: {parser.parse_grossWeight(responseB2,
            commands.response_device_2["signBit"], commands.response_device_2["decimalPoints"])} kg")
        # Loop Delay
        #time.sleep(0.1)
    except Exception as e:
        print("[SCHEDULER 2 ERROR: {e}]")