Routine Manager
===============

A modular Python application for industrial data acquisition, protocol handling, OPC UA publishing, TCP synchronization, and machine-learning-based prediction workflows.

Overview
--------

``routine_manager`` is designed around a clean separation of responsibilities:

- **Serial layer** handles low-level device communication and command/response parsing.
- **Core layer** coordinates polling, state management, and runtime orchestration.
- **OPC UA layer** exposes structured data to OPC UA clients and updates tags as data changes.
- **TCP layer** manages resilient socket connectivity and payload updates.
- **ML layer** buffers events, builds features, loads a trained model, and produces predictions.
- **Config layer** keeps deployment-specific settings outside the codebase.

Key Capabilities
----------------

- Serial communication through reusable client helpers
- Centralized command definitions for device requests
- Parsing helpers for handshake, address, sign, and weight extraction
- OPC UA node browsing and tag updates
- Runtime configuration loading from JSON files
- TCP socket connection management with reconnect logic
- Buffered ML inference using a saved model and label encoder
- Test modules for module-level validation
- Documentation assets for architecture and requirements

Project Structure
-----------------

::

    routine_manager/
    ├── config/
    │   ├── readme.txt
    │   ├── system_config.json
    │   └── tcp_payload.json
    ├── docs/
    │   ├── conf.py
    │   ├── index.rst
    │   ├── readme.txt
    │   ├── receipt_printing.png
    │   └── software_requirements.png
    ├── sample/
    │   ├── core/
    │   │   ├── controller.py
    │   │   ├── scheduler.py
    │   │   └── state_manager.py
    │   ├── inferenceEngineML/
    │   │   ├── buffer_manager.py
    │   │   ├── feature_builder.py
    │   │   ├── model_runner.py
    │   │   └── prediction.py
    │   ├── modelsML/
    │   │   ├── label_encoder.pkl
    │   │   └── xgboost_trailer_model.pkl
    │   ├── opcua/
    │   │   ├── opcua_client.py
    │   │   └── opcua_update.py
    │   ├── serialInterface/
    │   │   ├── commands.py
    │   │   ├── parser.py
    │   │   └── serial_client.py
    │   ├── tcpClient/
    │   │   ├── tcp_client.py
    │   │   └── tcp_connection_manager.py
    │   └── utils/
    │       ├── config_loader.py
    │       └── logger.py
    ├── tests/
    │   ├── readme.txt
    │   ├── simulation/
    │   │   ├── sample_test1.xlsx
    │   │   └── sim1_sap_opc.py
    │   ├── test1_serial.py
    │   ├── test2_tcp_client.py
    │   ├── test3_parser.py
    │   ├── test4_opcua.py
    │   ├── test5_multi_serial.py
    │   ├── test6_tcp_opc.py
    │   └── test7_sap_opc.py
    ├── LICENSE
    ├── requirements.txt
    ├── setup.py
    └── README.rst

Runtime Configuration
---------------------

The repository keeps runtime settings outside the code in ``config/`` to avoid hard-coding deployment details.

Goals include:

- Changing serial port or baud rate without code changes
- Modifying OPC UA tags without code changes
- Supporting multiple deployments easily

Configuration files:

- ``system_config.json`` — serial device, OPC server, and runtime configuration
- ``tcp_payload.json`` — TCP payload structure and values
- ``config_loader.py`` — shared loader utilities

Serial Communication
--------------------

The serial interface is built using reusable helpers:

- ``serial_client.py`` — handles connection lifecycle
- ``commands.py`` — stores command bytes
- ``parser.py`` — parses raw device responses

Supported commands include:

- Handshake
- Gross weight
- Tare weight
- Net weight

OPC UA Layer
------------

- ``opcua_client.py`` — OPC UA client wrapper for connection and browsing
- ``opcua_update.py`` — updates OPC UA nodes from runtime state

TCP Layer
---------

- ``tcp_connection_manager.py`` — maintains persistent connection and reconnect logic
- ``tcp_client.py`` — handles payload updates and nested data manipulation

Core Orchestration
------------------

- ``controller.py`` — coordinates data flow between modules
- ``scheduler.py`` — manages polling loop and execution timing
- ``state_manager.py`` — maintains shared runtime state with thread safety

ML Inference Pipeline
---------------------

- ``buffer_manager.py`` — groups and buffers events
- ``feature_builder.py`` — prepares model-ready features
- ``model_runner.py`` — loads model and performs predictions
- ``prediction.py`` — integrates ML output into application state

Model artifacts:

- ``xgboost_trailer_model.pkl``
- ``label_encoder.pkl``

Testing
-------

The ``tests/`` directory includes validation modules for:

- Serial communication
- Parser logic
- OPC UA integration
- TCP communication
- SAP-to-OPC workflows

Requirements
------------

Dependencies listed in ``requirements.txt``:

::

    pyserial
    opcua
    time

Getting Started
---------------

1. Install dependencies:

::

    pip install -r requirements.txt

2. Install the package:

::

    pip install .

3. Configure the system:

Edit JSON files in ``config/``:

- Serial settings
- OPC UA server configuration
- TCP payload schema

4. Run the application:

The main runtime starts from ``sample/main.py``.

Data Flow
---------

Typical system flow:

1. Read data from serial device
2. Parse raw responses
3. Update internal state
4. Push values to OPC UA
5. Optionally send via TCP
6. Run ML inference
7. Publish predictions

Documentation
-------------

Additional documentation is available under ``docs/``.

License
-------

Refer to the ``LICENSE`` file for full terms.
