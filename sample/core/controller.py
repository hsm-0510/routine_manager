from sample.core import scheduler
from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader
from sample.opcua import opcua_client
from sample.opcua import opcua_update

def routine1():
    totalActiveDevices, dev1_status, dev2_status = serial_client.checkActiveDevices()
    print(f"Total Devices: {totalActiveDevices}, dev1_status: {dev1_status}, dev2_status: {dev2_status}")
    if totalActiveDevices == 0:
        print("No Active Devices")
    elif totalActiveDevices == 1 and dev1_status == 1:
        print("Device 1 is Active")
        port = config_loader.serial_config_load("comPort", 0)
        baudrate = config_loader.serial_config_load("baudrate", 0)
        timeout = config_loader.serial_config_load("timeout", 0)
        scheduler.scheduler1(port, baudrate, timeout, 0)
    elif totalActiveDevices == 1 and dev2_status == 1:
        print("Device 2 is Active")
        port = config_loader.serial_config_load("comPort", 1)
        baudrate = config_loader.serial_config_load("baudrate", 1)
        timeout = config_loader.serial_config_load("timeout", 1)
        scheduler.scheduler1(port, baudrate, timeout, 1)
    else:
        print("Device 1 is Active")
        print("Device 2 is Active")
        port1 = config_loader.serial_config_load("comPort", 0)
        baudrate1 = config_loader.serial_config_load("baudrate", 0)
        timeout1 = config_loader.serial_config_load("timeout", 0)
        port2 = config_loader.serial_config_load("comPort", 1)
        baudrate2 = config_loader.serial_config_load("baudrate", 1)
        timeout2 = config_loader.serial_config_load("timeout", 1)
        scheduler.scheduler2(port1, baudrate1, timeout1,
                                port2, baudrate2, timeout2)