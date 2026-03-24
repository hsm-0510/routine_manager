Purpose:
-> This is the software package

# sample/core

Purpose:
-> Contains main application code
-> responsible for data flow through the system

controller.py:
-> connects serial -> parser -> opc ua
-> objectives:
    1. Send commands to the device
    2. Receive responses
    3. Parse them
    4. Update OPC UA variables

scheduler.py:
-> controls when actions occur
-> objective:
    1. create the polling loop

# sample/serial/

Purpose:
-> related to device communication (handles device protocol only, no info on opc)

serial_client.py:
-> low-level device communication
-> objective:
    1. open serial port 
    2. send bytes
    3. receive bytes
    4. create a reusable serial communication class

commands.py:
-> centralize all device commands
-> why? : because protocols vary with different devices, and don't want hex codes scattered
-> objective:
    1. store commands as COMMANDS["gross_weight"]

parser.py:
-> translate raw device responses to usable values
-> objective:
    1. separate communication from interpretation

# sample/opcua

Purpose:
-> everything related to opc ua server
-> this layer musn't know anything about serial communication
-> only exposes data to OPC clients

server.py:
-> creates and starts the opc ua server
-> objectives:
    1. set endpoint
    2. start server
    3. stop server
    4. external clients are able to connect

node_manager.py
-> creates opc ua nodes automatically using json configs
-> transform json to opc ua node tree

updater.py
-> update opc ua variables when new data arrives

# sample/utils

Purpose:
-> common helper utilities
-> general tools used by multiple modules

config_loader.py:
-> load confuguraiton files
-> function must be reusable for:
    1. serial module
    2. opc ua module
    3. main application

logger.py:
-> provide consistent logging accross the project
-> makes debugging easier and logs more professional

# sample/main.py

Purpose:
-> entry point of entire application
-> everything must run when this is run

Objective:
1. load configuration
2. start opc ua server
3. create opc nodes
4. connect serial device
5. start polling scheduler