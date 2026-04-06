from sample.core import scheduler
from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader
from sample.opcua import opcua_client
from sample.opcua import opcua_update

def routine1(opc):
    totalActiveDevices, dev1_status, dev2_status = serial_client.checkActiveDevices()
    print(f"Total Devices: {totalActiveDevices}, dev1_status: {dev1_status}, dev2_status: {dev2_status}")
    if totalActiveDevices == 0:
        print("No Active Devices")
    elif totalActiveDevices == 1 and dev1_status == 1:
        print("Device 1 is Active")
        scheduler.scheduler1(opc, serial_client.port1, serial_client.baudrate1, serial_client.timeout1, 0)
    elif totalActiveDevices == 1 and dev2_status == 1:
        print("Device 2 is Active")
        scheduler.scheduler1(opc, serial_client.port2, serial_client.baudrate2, serial_client.timeout2, 1)
    else:
        print("Device 1 is Active")
        print("Device 2 is Active")
        scheduler.scheduler2(opc, serial_client.port1, serial_client.baudrate1, serial_client.timeout1,
                                serial_client.port2, serial_client.baudrate2, serial_client.timeout2)