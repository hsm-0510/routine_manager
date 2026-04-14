# Routine Manager

A modular Python integration project for managing routine data flow between serial weighing devices, an OPC UA server, and a TCP-based Waveshare payload. The repository is organized around a configuration-driven architecture so device details, tag names, and connection settings can be changed without editing core logic.

## Overview

The project is built to:

- read data from one or two serial weighing indicators
- parse device responses into usable weight values
- publish values to an OPC UA server
- synchronize a JSON payload over TCP for external hardware such as Waveshare modules
- keep runtime settings outside the codebase in JSON configuration files

The main package under `sample/` contains the application logic, while `config/` stores deployment settings and payload templates.

## Key Capabilities

- Serial communication with one or two weighbridge indicators
- Device availability detection before selecting single- or dual-device polling
- Parsing of serial responses for handshake, sign bit, decimal places, and gross weight
- OPC UA client support for reading and writing tags
- TCP payload update and exchange using JSON messages
- Centralized state and configuration loading from external files
- Basic test modules for serial, parser, OPC UA, TCP, and multi-serial flows

## Project Structure

```text
routine_manager/
├── config/
│   ├── system_config.json
│   └── tcp_payload.json
├── docs/
│   ├── conf.py
│   └── index.rst
├── sample/
│   ├── core/
│   │   ├── controller.py
│   │   ├── scheduler.py
│   │   └── state_manager.py
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
│   ├── utils/
│   │   ├── config_loader.py
│   │   └── logger.py
│   └── main.py
├── tests/
│   ├── test_multi_serial.py
│   ├── test_opcua.py
│   ├── test_parser.py
│   ├── test_serial.py
│   ├── test_tcp_client.py
│   └── test_tcp_opc.py
├── requirements.txt
├── setup.py
└── LICENSE
```

## How It Works

### 1. Configuration loading
`sample/utils/config_loader.py` reads runtime settings from `config/system_config.json` and `config/tcp_payload.json`.

### 2. Serial device handling
`sample/serialInterface/serial_client.py` loads serial settings for each indicator, opens the COM port, checks which devices are active, and sends commands to the scale controller.

### 3. Parsing
`sample/serialInterface/parser.py` interprets device responses and extracts values such as:

- handshake response
- indicator address
- sign bit
- decimal point count
- gross weight

### 4. Scheduling
`sample/core/scheduler.py` contains the main polling logic:

- `scheduler1(...)` handles a single active device
- `scheduler2(...)` handles both devices together

It continuously reads serial responses, parses weight values, updates the TCP payload, and writes values into OPC UA tags.

### 5. OPC UA integration
`sample/opcua/opcua_client.py` wraps the OPC UA connection and provides helper methods to read and write tags under the namespace used by the project.

### 6. Payload synchronization
`sample/tcpClient/tcp_client.py` keeps a JSON payload in sync and sends/receives newline-delimited JSON over TCP.  
`sample/opcua/opcua_update.py` bridges OPC UA values into the payload and updates status fields from external inputs.

## Configuration

### `config/system_config.json`
This file stores the runtime settings for:

- `serial_device`
- `waveshare_device`
- `opc_server`

Example values already defined in the repository include:

- entrance weighbridge serial port: `COM5`
- exit weighbridge serial port: `COM8`
- baud rate: `9600`
- OPC UA endpoint: `opc.tcp://127.0.0.1:5501/pso/weighbridge/`

### `config/tcp_payload.json`
This file defines the structured TCP payload used by the Waveshare integration.

## Installation

```bash
git clone https://github.com/hsm-0510/routine_manager.git
cd routine_manager
pip install -r requirements.txt
pip install -e .
```

## Usage

The project is organized as a Python package under `sample/`.  
A typical integration flow is:

1. load the configuration
2. create an OPC UA client
3. connect to the OPC UA server
4. call the controller or scheduler logic
5. keep the process running while serial, OPC UA, and TCP data are synchronized

Example pattern:

```python
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.core.controller import routine1

opc = PSOWeighbridgeClient("opc.tcp://127.0.0.1:5501/pso/weighbridge/")
opc.connect()
routine1(opc)
```

## Testing

The `tests/` folder contains module-level test scripts for validating individual parts of the system:

- serial communication
- parser behavior
- OPC UA connectivity
- TCP client behavior
- multi-serial handling

Run tests with your preferred Python test runner or execute the scripts directly, depending on how you want to validate the modules.

## Notes

- The repository is configuration-driven, which makes it easier to deploy across different environments.
- Several modules are tightly coupled to the expected JSON keys in `config/system_config.json` and `config/tcp_payload.json`.
- The project appears to be intended for a weighbridge-style integration workflow with OPC UA and TCP synchronization.

## License

See `LICENSE` for licensing details.
