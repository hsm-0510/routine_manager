Routine Manager
===============

A modular Python integration project for managing routine data flow between
serial weighing devices, an OPC UA server, and a TCP-based Waveshare payload.

The repository follows a configuration-driven architecture so device details,
tag names, and connection settings can be changed without modifying the core
application logic.

Overview
========

The project is designed to:

* Read data from one or two serial weighing indicators
* Parse device responses into usable weight values
* Publish values to an OPC UA server
* Synchronize a JSON payload over TCP for external hardware such as Waveshare modules
* Keep runtime settings outside the codebase in JSON configuration files

The main package under ``sample/`` contains the application logic, while
``config/`` stores deployment settings and payload templates.

Key Features
============

* Serial communication with one or two weighbridge indicators
* Device availability detection for automatic polling mode selection
* Parsing of handshake, sign bit, decimal places, and gross weight
* OPC UA client support for reading and writing tags
* TCP payload update and exchange using JSON messages
* External configuration loading from JSON files
* Test modules for serial, parser, OPC UA, TCP, and multi-device flows

Project Structure
=================

.. code-block:: text

    routine_manager/
    ├── config/
    │   ├── system_config.json
    │   └── tcp_payload.json
    ├── docs/
    │   ├── conf.py
    │   └── index.rst
    ├── sample/
    │   ├── core/
    │   ├── opcua/
    │   ├── serialInterface/
    │   ├── tcpClient/
    │   ├── utils/
    │   └── main.py
    ├── tests/
    ├── requirements.txt
    ├── setup.py
    └── LICENSE

How It Works
============

1. Configuration Loading
------------------------

``sample/utils/config_loader.py`` loads runtime settings from:

* ``config/system_config.json``
* ``config/tcp_payload.json``

2. Serial Device Handling
-------------------------

``sample/serialInterface/serial_client.py``:

* Loads serial settings
* Opens COM ports
* Detects active devices
* Sends commands to indicators

3. Data Parsing
---------------

``sample/serialInterface/parser.py`` extracts:

* Handshake response
* Indicator address
* Sign bit
* Decimal point count
* Gross weight

4. Scheduling
-------------

``sample/core/scheduler.py`` contains the polling logic:

* ``scheduler1(...)`` for a single active device
* ``scheduler2(...)`` for dual-device operation

The scheduler continuously:

* Reads serial data
* Parses values
* Updates the TCP payload
* Writes values to OPC UA tags

5. OPC UA Integration
---------------------

``sample/opcua/opcua_client.py`` manages:

* OPC UA connection
* Tag reading
* Tag writing

6. Payload Synchronization
--------------------------

``sample/tcpClient/tcp_client.py`` handles:

* JSON payload updates
* TCP communication
* Newline-delimited JSON transmission

``sample/opcua/opcua_update.py`` bridges OPC UA values into the payload.

Configuration
=============

system_config.json
------------------

Stores runtime settings for:

* ``serial_device``
* ``waveshare_device``
* ``opc_server``

Example values:

* Entrance serial port: ``COM5``
* Exit serial port: ``COM8``
* Baud rate: ``9600``
* OPC UA endpoint:

  ``opc.tcp://127.0.0.1:5501/pso/weighbridge/``

tcp_payload.json
----------------

Defines the structured TCP payload used by the external device integration.

Installation
============

.. code-block:: bash

    git clone https://github.com/hsm-0510/routine_manager.git
    cd routine_manager
    pip install -r requirements.txt
    pip install -e .

Usage
=====

Example usage:

.. code-block:: python

    from sample.opcua.opcua_client import PSOWeighbridgeClient
    from sample.core.controller import routine1

    opc = PSOWeighbridgeClient("opc.tcp://127.0.0.1:5501/pso/weighbridge/")
    opc.connect()
    routine1(opc)

Testing
=======

The ``tests/`` directory includes scripts for:

* Serial communication
* Parser validation
* OPC UA connectivity
* TCP client testing
* Multi-device handling

Run tests using:

.. code-block:: bash

    python -m tests.test_serial

or your preferred Python test framework.

Notes
=====

* The repository is configuration-driven for easier deployment
* Several modules depend on expected JSON keys
* Intended for weighbridge integration with OPC UA and TCP synchronization

License
=======

See the ``LICENSE`` file for licensing details.
