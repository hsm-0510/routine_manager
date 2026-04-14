# Routine Manager

A modular Python application for industrial data acquisition, protocol handling, OPC UA publishing, TCP synchronization, and machine-learning-based prediction workflows.

The repository is organized as a package-based application under `sample/` with separate layers for:

- serial device communication,
- OPC UA server/client operations,
- TCP connection management,
- runtime configuration loading,
- logging utilities,
- and an ML inference pipeline for trailer/event classification.

## Overview

`routine_manager` is designed around a clean separation of responsibilities:

- **Serial layer** handles low-level device communication and command/response parsing.
- **Core layer** coordinates polling, state management, and runtime orchestration.
- **OPC UA layer** exposes structured data to OPC UA clients and updates tags as data changes.
- **TCP layer** manages resilient socket connectivity and payload updates.
- **ML layer** buffers events, builds features, loads a trained model, and produces predictions.
- **Config layer** keeps deployment-specific settings outside the codebase.

## Key Capabilities

- Serial communication through reusable client helpers
- Centralized command definitions for device requests
- Parsing helpers for handshake, address, sign, and weight extraction
- OPC UA node browsing and tag updates
- Runtime configuration loading from JSON files
- TCP socket connection management with reconnect logic
- Buffered ML inference using a saved model and label encoder
- Test modules for module-level validation
- Documentation assets for architecture and requirements

## Project Structure

```text

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
```

## Runtime Configuration

The repository keeps runtime settings outside the code in `config/` to avoid hard-coding deployment details. The included configuration notes describe these goals explicitly:

- change serial port or baud rate without code changes,
- change OPC UA tags without code changes,
- support multiple deployments more easily.

### Configuration files

- `system_config.json` — serial device, OPC server, and other runtime configuration
- `tcp_payload.json` — TCP payload structure and values
- `config_loader.py` — shared loader utilities for reading config values

## Serial Communication

The serial interface is centered around reusable helpers:

- `serial_client.py` opens, closes, and talks to the device
- `commands.py` stores command bytes in one place
- `parser.py` converts raw device responses into usable values

The command set includes at least:

- handshake
- gross weight
- tare weight
- net weight

The parser includes helpers for extracting the handshake response, indicator address, sign bit, and gross weight value.

## OPC UA Layer

The OPC UA package wraps server/client behavior and tag updates.

### `opcua_client.py`

This module provides an OPC UA client wrapper that connects to the server, resolves the namespace index, browses the node tree, and reads individual tag values.

### `opcua_update.py`

This module updates OPC UA elements from shared application state. The code maps structured runtime data into OPC UA tags and keeps the server-side values synchronized with the latest device or SAP data.

## TCP Layer

The TCP subsystem is built for persistent connectivity and payload manipulation.

- `tcp_connection_manager.py` maintains the socket connection, keeps it alive, and reconnects on failure.
- `tcp_client.py` provides payload helpers such as updating and reading nested values.

This is a good fit for upstream systems that exchange structured transaction or SAP-related data over TCP.

## Core Orchestration

The core package contains the application control flow:

- `controller.py` coordinates serial reads, parsing, and OPC UA updates
- `scheduler.py` handles the polling loop and device-level execution timing
- `state_manager.py` stores shared runtime state and includes locking for safe SAP state updates

The state manager is especially important because it centralizes shared dictionaries and versioning logic for concurrent updates.

## ML Inference Pipeline

The ML pipeline is organized as a compact event-processing workflow:

- `buffer_manager.py` groups events by trailer code and prevents duplicate predictions
- `feature_builder.py` converts raw rows into model-ready features
- `model_runner.py` loads the saved model and label encoder, then returns a predicted class and probability map
- `prediction.py` connects the ML flow to shared application state and runs the inference worker

The prediction layer normalizes SAP-style input keys into ML features such as:

- trailer code
- ordered quantity
- gross quantity
- density
- compartment number
- transformed net weight
- expected net weight
- compartment name

The model runner loads serialized artifacts from `sample/modelsML/`, including:

- `xgboost_trailer_model.pkl`
- `label_encoder.pkl`

## Testing

The `tests/` directory contains module-focused tests for the major layers of the project, including:

- serial communication
- parser behavior
- OPC UA integration
- TCP client behavior
- multi-serial handling
- TCP-to-OPC scenarios
- SAP-to-OPC scenarios

## Requirements

The repository currently lists the following Python dependencies in `requirements.txt`:

```text
pyserial
opcua
time
```

## Getting Started

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Install the package

```bash
pip install .
```

### 3) Configure the system

Edit the JSON files in `config/` to match your deployment:

- serial port
- baud rate
- timeouts
- OPC UA server settings
- TCP payload schema

### 4) Run the application

The project is structured so that the main runtime flow is expected to start from the package entrypoint under `sample/main.py`, with the core scheduler, OPC UA server, and device connections wired together there.

## Data Flow

A typical flow through the system is:

1. Read raw data from the serial device.
2. Parse the device response into structured values.
3. Update runtime state.
4. Push values into OPC UA tags.
5. Optionally forward or synchronize data over TCP.
6. Feed event data into the ML inference pipeline when applicable.
7. Publish prediction results back into the shared state / OPC layer.

## Documentation

Additional project notes are stored under `docs/`, including receipt-related requirements and software requirement references.

## License

This repository includes a license file. Refer to `LICENSE` for the full terms.
