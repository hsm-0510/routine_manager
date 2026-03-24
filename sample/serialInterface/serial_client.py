from sample.serialInterface import commands
from sample.serialInterface import parser
import time
import serial
from sample.utils import config_loader

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
    # print(f"Sending: {cmd.hex(' ')}")
    ser.write(cmd)
    time.sleep(0.2)
    response = ser.read_all()
    # print(f"Received (hex):", response)
    return response

def checkActiveDevices():
    dev1 = config_loader.serial_config_load("isActive", 0)
    dev2 = config_loader.serial_config_load("isActive", 1)
    port1 = config_loader.serial_config_load("comPort", 0)
    baudrate1 = config_loader.serial_config_load("baudrate", 0)
    timeout1 = config_loader.serial_config_load("timeout", 0)
    port2 = config_loader.serial_config_load("comPort", 1)
    baudrate2 = config_loader.serial_config_load("baudrate", 1)
    timeout2 = config_loader.serial_config_load("timeout", 1)
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

def main():
    print("null")

if __name__ == "__main__":
    main()