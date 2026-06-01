import time, sqlite3, os
from sample.core import scheduler
from sample.serialInterface import commands
from sample.serialInterface import parser
from sample.serialInterface import serial_client
from sample.utils import config_loader
from sample.opcua import opcua_client
from sample.opcua import opcua_update
from sample.core import localDB

def routine1(opc):
    totalActiveDevices, dev1_status, dev2_status = serial_client.checkActiveDevices()
    print(f"Total Devices: {totalActiveDevices}, dev1_status: {dev1_status}, dev2_status: {dev2_status}")
    if totalActiveDevices == 0:
        print("No Active Devices")
        opc.write_tag("Entrance_XK3190_DS8", "gross_weight_entranceWB1", "0")
        opc.write_tag("Exit_XK3190_DS8", "gross_weight_exitWB2", "0")
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
        
def process_automation1_entrance(opc):
    triggered = False
    # Entrance Routine
    while True:
        # Conditions for Entrance Routine to Initiate
        entrance_conditions = {
            "ir1_ent": opc.read_tag("Waveshare_Monitoring", "irSens_01_entranceLB", "string"),
            "ir2_ent": opc.read_tag("Waveshare_Monitoring", "irSens_02_entranceLB", "string"),
            "ir3_ent": opc.read_tag("Waveshare_Monitoring", "irSens_03_entranceLB", "string"),
            "driver_absent_entrance": opc.read_tag("Camera_Detection", "driver_absence_status_camera_ent", "string"),
            "vehicle_alignment_entrance": opc.read_tag("Camera_Detection", "vehicle_alignment_status_camera_ent", "string"),
            "kiosk_entrance_button": opc.read_tag("KIOSK", "kiosk_button_entrance", "string")
        }
        # Conditions for Entrance Routine to Close Lane Barrier
        laneB_conditions = {
            "ir1_ent": opc.read_tag("Waveshare_Monitoring", "irSens_01_entranceLB", "string"),
            "ir2_ent": opc.read_tag("Waveshare_Monitoring", "irSens_02_entranceLB", "string"),
            "ir3_ent": opc.read_tag("Waveshare_Monitoring", "irSens_03_entranceLB", "string"),
        }
        # RDY Status for Entrance Routine Initiation
        entrance_rdy = all(val == "1" for val in entrance_conditions.values())
        # RDY Status for Entrance Routine Lane Barrier Close
        laneB_close = all(val == "0" for val in laneB_conditions.values())
        
        print(f"[PROCESS_AUTOMATION_ENT]: Conditions Not Met Yet")
        if entrance_rdy and not triggered:
            triggered = True
            print(f"[PROCESS_AUTOMATION_ENT]: Entrance Conditions Met")
            # Tare Weight, RFID Data and Card Data from OPC Server
            tare_weight = opc.read_tag("Entrance_XK3190_DS8", "gross_weight_entranceWB1", "string")
            print(f"[PROCESS_AUTOMATION_ENT]: Tare Weight: {tare_weight}")
            rfidData = opc.read_tag("RFID_Scanner", "dataRFID_Entrance", "string")
            print(f"[PROCESS_AUTOMATION_ENT]: RFID Data: {rfidData}")
            cardData = opc.read_tag("KIOSK", "cardData_entrance", "string")
            print(f"[PROCESS_AUTOMATION_ENT]: Card Data: {cardData}")
            
            # Maintain Local Excel for locally managing net fuel weight calculation at exit
            # localDB.dataEntry(df, tare_weight, rfidData, cardData)
            # print(f"[EXCEL_ENTRY]: Tare Weight: {tare_weight}, RFID Data: {rfidData}, Card Data: {cardData}")
            # Save in SQL Database
            localDB.save_tare(rfidData, cardData, tare_weight)
            print(f"[DATABASE_ENTRY]: Tare Weight: {tare_weight}, RFID Data: {rfidData}, Card Data: {cardData}")
            
            # Generate Entrance Receipt
            opc.write_tag("KIOSK", "receiptData_1", f"ID. No: {rfidData}")
            opc.write_tag("KIOSK", "receiptData_2", f"Tare Weight: {tare_weight}")
            time.sleep(1)
            # Print Entrance Receipt
            opc.write_tag("KIOSK", "kiosk_print_control_entrance", "1")
            print(f"[ENTRANCE_ROUTINE]: Receipt Printed")
            time.sleep(1.5)
            opc.write_tag("KIOSK", "kiosk_print_control_entrance", "0")
            # Open Entrance Lane Barrier
            opc.write_tag("Waveshare_Controlling", "open_entranceLB", "1")
            opc.write_tag("Waveshare_Controlling", "close_entranceLB", "0")
            print("[ENTRANCE_ROUTINE]: Entrance Lane Barrier Openned")
            
        # Close Entrance Lane Barrier (Safe)
        if laneB_close:
            # Wait for 3 Seconds After Lorry Exit
            time.sleep(3)
            # Open Entrance Lane Barrier
            opc.write_tag("Waveshare_Controlling", "open_entranceLB", "0")
            opc.write_tag("Waveshare_Controlling", "close_entranceLB", "1")
            print("[ENTRANCE_ROUTINE]: Entrance Lane Barrier Closed")
            triggered = False
        time.sleep(1)

def process_automation1_exit(opc):
    triggered = False
    # Exit Routine
    while True:
        # Conditions for Exit Routine to Initiate
        exit_conditions = {
            "ir1_ext": opc.read_tag("Waveshare_Monitoring", "irSens_01_exitLB", "string"),
            "ir2_ext": opc.read_tag("Waveshare_Monitoring", "irSens_02_exitLB", "string"),
            "ir3_ext": opc.read_tag("Waveshare_Monitoring", "irSens_03_exitLB", "string"),
            "driver_absent_exit": opc.read_tag("Camera_Detection", "driver_absence_status_camera_ext", "string"),
            "vehicle_alignment_exit": opc.read_tag("Camera_Detection", "vehicle_alignment_status_camera_ext", "string"),
            "kiosk_exit_button": opc.read_tag("KIOSK", "kiosk_button_exit", "string")
        }
        # Conditions for Entrance Routine to Close Lane Barrier
        laneB_conditions = {
            "ir1_ext": opc.read_tag("Waveshare_Monitoring", "irSens_01_exitLB", "string"),
            "ir2_ext": opc.read_tag("Waveshare_Monitoring", "irSens_02_exitLB", "string"),
            "ir3_ext": opc.read_tag("Waveshare_Monitoring", "irSens_03_exitLB", "string"),
        }
        # RDY Status for Exit Routine Initiation
        exit_rdy = all(val == "1" for val in exit_conditions.values())
        # RDY Status for Entrance Routine Lane Barrier Close
        laneB_close = all(val == "0" for val in laneB_conditions.values())
        
        print(f"[PROCESS_AUTOMATION_EXT]: Conditions Not Met Yet")
        # Exit Routine
        if exit_rdy and not triggered:
            triggered = True
            # Gross Weight, RFID Data and Card Data from OPC Server
            gross_weight = opc.read_tag("Exit_XK3190_DS8", "gross_weight_exitWB2", "string")
            print(f"[PROCESS_AUTOMATION_EXT]: Gross Weight: {gross_weight}")
            rfidData = opc.read_tag("RFID_Scanner", "dataRFID_Exit", "string")
            print(f"[PROCESS_AUTOMATION_EXT]: RFID Data: {rfidData}")
            cardData = opc.read_tag("KIOSK", "cardData_exit", "string")
            print(f"[PROCESS_AUTOMATION_EXT]: Card Data: {cardData}")
            
            # # Extract Tare Weight Details from Local Excel
            # tare_weight = int(localDB.extractData(df, rfidData, cardData, "Tare Weight"))
            # print(f"[EXCEL_EXTRACT]: Tare Weight: {tare_weight}, RFID Data: {rfidData}, Card Data: {cardData}")
            # Extract Data from SQL Database  
            tare_weight = localDB.get_tare(rfidData)
            print(f"[DATABASE_EXTRACT]: Tare Weight: {tare_weight}, RFID Data: {rfidData}, Card Data: {cardData}")
            
            # Net Weight Calculation
            net_weight = int(gross_weight) - int(tare_weight)
            print(f"[EXIT_ROUTINE]: Gross Weight: {gross_weight}, Net Weight: {net_weight}")
            # Generate Exit Receipt
            opc.write_tag("KIOSK", "receiptData_1", f"ID No.: {rfidData}")
            opc.write_tag("KIOSK", "receiptData_2", f"Tare Weight: {tare_weight}")
            opc.write_tag("KIOSK", "receiptData_3", f"Gross Weight: {gross_weight}")
            opc.write_tag("KIOSK", "receiptData_4", f"Net Weight: {net_weight}")
            time.sleep(1)
            
            # # Update Local Excel
            # localDB.updateData(df, rfidData, cardData, gross_weight, net_weight)
            # print(f"[EXCEL_UPDATE]: RFID DATA: {rfidData}, CARD DATA: {cardData}, TARE WEIGHT: {tare_weight}, GROSS WEIGHT: {gross_weight}, NET WEIGHT: {net_weight}")
            # Update SQL Database
            localDB.save_gross(rfidData, cardData, tare_weight, gross_weight)
            print(f"[DATABASE_UPDATE]: RFID DATA: {rfidData}, CARD DATA: {cardData}, TARE WEIGHT: {tare_weight}, GROSS WEIGHT: {gross_weight}, NET WEIGHT: {net_weight}")
            
            # Print Exit Receipt
            opc.write_tag("KIOSK", "kiosk_print_control_exit", "1")
            time.sleep(1.5)
            print(f"[EXIT_ROUTINE]: Receipt Printed")
            opc.write_tag("KIOSK", "kiosk_print_control_exit", "0")
            # Open Exit Lane Barrier
            opc.write_tag("Waveshare_Controlling", "open_exitLB", "1")
            opc.write_tag("Waveshare_Controlling", "close_exitLB", "0")
            print("[EXIT_ROUTINE]: Exit Lane Barrier Openned")
            
            # Update sap data with trailer net weight at exit
            opc.write_tag("SAP_DATA", "SAP_trailer_net_weight", str(net_weight))
            
        # Close Exit Lane Barrier (Safe)
        if laneB_close:
            # Wait for 3 Seconds After Lorry Exit
            time.sleep(3)
            # Open Entrance Lane Barrier
            opc.write_tag("Waveshare_Controlling", "open_exitLB", "0")
            opc.write_tag("Waveshare_Controlling", "close_exitLB", "1")
            print("[EXIT_ROUTINE]: Exit Lane Barrier Closed")
            triggered = False
        time.sleep(1)