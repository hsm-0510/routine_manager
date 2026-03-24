Purpose:
Store all runtime configuraitons outside of code
-> preventing hard-coding device details / OPC UA tags in the python files

Objectives:
Should be able to:
1. Change serial port or baudrate without code modification
2. Change OPC UA tags without code modification
3. Support multiple deployments easily

# Serial_Config

Purpose:
-> defines how to connect to the serial device

Responsibilities:
1. COM port
2. baudrate
3. timeout
4. polling interval

# OPC UA tags config

Purpose:
-> defines what variables appear in OPC UA server (the data model)

Structure:
Objects
    |- Category
    |       |- Tag 
            |- Tag
