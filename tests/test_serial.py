from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader

port = config_loader.serial_config_load("comPort", 0)
print(f"Port: ", port)
baudrate = config_loader.serial_config_load("baudrate", 0)
print(f"Baudrate: ", baudrate)
timeout = config_loader.serial_config_load("timeout", 0)
print(f"Timeout: ", timeout)
deviceID = config_loader.serial_config_load("deviceID", 0)
print(f"Device ID: ", deviceID)

def main():
    ser = serial_client.connect_serial(port, baudrate, timeout)
    responseA = serial_client.send_command(ser, commands.commands["handshake"])
    # responseB = serial_client.send_command(ser, commands.commands["gross_weight"])
    # responseC = serial_client.send_command(ser, commands.commands["tare_weight"])
    # responseD = serial_client.send_command(ser, commands.commands["net_weight"])
    serial_client.disconnect_serial(ser)

if __name__ == "__main__":
    main()