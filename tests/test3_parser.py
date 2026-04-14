from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader

port = config_loader.serial_config_load("comPort")
print(f"Port: ", port)
baudrate = config_loader.serial_config_load("baudrate")
print(f"Baudrate: ", baudrate)
timeout = config_loader.serial_config_load("timeout")
print(f"Timeout: ", timeout)

def main():
    ser = serial_client.connect_serial(port, baudrate, timeout)
    responseA = serial_client.send_command(ser, commands.commands["handshake"])
    responseB = serial_client.send_command(ser, commands.commands["gross_weight"])
    responseC = serial_client.send_command(ser, commands.commands["tare_weight"])
    responseD = serial_client.send_command(ser, commands.commands["net_weight"])
    print(f"Handshake Response: ", parser.parse_handshakeResponse(responseA))
    print(f"Indicator Address: ", parser.parse_indicatorAddress(responseB))
    print(f"Sign Bit: ", parser.parse_signBit(responseB))
    print(f"Gross Weight: ", parser.parse_grossWeight(responseB,
                                                      parser.parse_signBit(responseB),
                                                      parser.parse_decimalPoints(responseB)))
    print(f"Decimal Point: ", parser.parse_decimalPoints(responseB))
    serial_client.disconnect_serial(ser)

if __name__ == "__main__":
    main()