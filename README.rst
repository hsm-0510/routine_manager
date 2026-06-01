# Routine Manager

## PSO Smart Weighbridge Automation Platform

Routine Manager is a modular industrial automation framework designed to manage and coordinate the complete workflow of a smart weighbridge installation. The system integrates industrial weighing equipment, OPC UA infrastructure, TCP-connected field devices, SAP transaction data, RFID systems, kiosk operations, and machine-learning based anomaly detection into a single orchestrated platform.

---

# Table of Contents

1. Introduction
2. System Architecture
3. Core Responsibilities
4. Project Structure
5. Runtime Components
6. Communication Layers
7. Weighbridge Integration
8. OPC UA Integration
9. TCP Device Integration
10. Machine Learning Pipeline
11. Data Flow
12. State Management
13. Configuration
14. Installation
15. Development Workflow
16. Testing
17. Deployment Notes
18. Troubleshooting
19. Future Enhancements

---

# Introduction

The project acts as the central coordinator between multiple subsystems operating within a smart weighbridge environment.

The primary goals are:

- Continuous weight acquisition
- Equipment monitoring
- Industrial communication
- Process automation
- SAP transaction validation
- RFID and kiosk coordination
- ML-based anomaly detection
- OPC UA publishing for SCADA visibility

The architecture is intentionally modular to allow independent development and testing of each subsystem.

---

# System Architecture

```text
                   SAP Transactions
                          |
                          v
+--------------------------------------------------+
|                  Routine Manager                 |
|--------------------------------------------------|
| Controller                                       |
| Scheduler                                        |
| State Manager                                    |
|--------------------------------------------------|
| Serial Layer     OPC UA Layer     TCP Layer      |
|--------------------------------------------------|
| ML Inference Engine                              |
+--------------------------------------------------+
      |                |                |
      v                v                v

 Weighbridge      OPC UA Server     Waveshare I/O
 Devices                              Devices

                          |
                          v
                     SCADA System
```

---

# Core Responsibilities

The application is responsible for:

- Polling weighbridge devices
- Parsing incoming serial data
- Maintaining process state
- Synchronizing field I/O
- Updating OPC UA variables
- Processing SAP transactions
- Running machine-learning predictions
- Publishing operational status

---

# Project Structure

```text
routine_manager/

├── config/
│   ├── system_config.json
│   └── tcp_payload.json
│
├── docs/
│
├── sample/
│   ├── core/
│   │   ├── controller.py
│   │   ├── scheduler.py
│   │   ├── state_manager.py
│   │   └── localDB.py
│   │
│   ├── serialInterface/
│   │
│   ├── opcua/
│   │
│   ├── tcpClient/
│   │
│   ├── inferenceEngineML/
│   │
│   ├── modelsML/
│   │
│   └── utils/
│
├── tests/
├── requirements.txt
└── setup.py
```

---

# Runtime Components

## Controller

Primary orchestration component.

Responsibilities:

- Startup initialization
- Device registration
- Communication setup
- Scheduler management
- Process coordination

The controller acts as the central entry point for the entire application.

---

## Scheduler

Responsible for recurring execution tasks.

Functions include:

- Serial polling
- Device health checks
- OPC updates
- TCP synchronization
- Scheduled processing jobs

Benefits:

- Deterministic execution
- Centralized polling
- Reduced communication conflicts

---

## State Manager

Central repository for runtime information.

Stores:

- Current weights
- Device status
- RFID information
- SAP transaction data
- Kiosk status
- Barrier state
- TCP payload data

The state manager allows modules to exchange information without direct coupling.

---

## Local Database

Provides persistent storage for:

- Transactions
- Historical records
- Runtime snapshots
- Offline buffering

Allows operation even when external systems are unavailable.

---

# Communication Layers

## Serial Communication Layer

Used for weighbridge communication.

Responsibilities:

- COM port management
- Command transmission
- Response handling
- Packet parsing
- Error recovery

Features:

- Multiple devices
- Independent connections
- Automatic reconnection

---

## OPC UA Layer

Industrial interoperability layer.

Capabilities:

- Read OPC UA nodes
- Write OPC UA nodes
- Namespace browsing
- Process variable publishing

Used for:

- SCADA visibility
- Automation integration
- Third-party connectivity

---

## TCP Layer

Responsible for communication with external network devices.

Capabilities:

- Client connections
- JSON payload transfer
- Heartbeat monitoring
- Automatic reconnect

Primary use:

- Waveshare ESP32-S3 communication

---

# Weighbridge Integration

Supported equipment includes XK3190 DS8 weighbridge indicators.

Typical workflow:

1. Open serial connection
2. Poll weight value
3. Parse response
4. Validate data
5. Update state manager
6. Publish to OPC UA

Collected values:

- Gross weight
- Tare weight
- Net weight
- Device status

---

# OPC UA Integration

The OPC UA subsystem exposes process information to external systems.

Example information published:

- Current weight
- Vehicle status
- Barrier state
- RFID information
- Transaction state
- ML prediction results

Benefits:

- Vendor-neutral communication
- SCADA compatibility
- Standardized industrial integration

---

# TCP Device Integration

The TCP client subsystem manages communication with Waveshare devices.

Typical functions:

- Sensor monitoring
- Digital inputs
- Digital outputs
- Status synchronization
- Command execution

Features:

- Reconnect handling
- Connection monitoring
- Payload validation

---

# Machine Learning Pipeline

The repository contains a dedicated ML inference engine.

Model artifacts:

```text
modelsML/
├── xgboost_trailer_model.pkl
└── label_encoder.pkl
```

## Workflow

```text
SAP Data
   |
   v
Feature Builder
   |
   v
Buffer Manager
   |
   v
XGBoost Model
   |
   v
Prediction
   |
   v
OPC UA Publication
```

## Prediction Categories

- NORMAL
- DRIFT
- THEFT
- MISSING

Potential use cases:

- Trailer anomaly detection
- Transaction verification
- Fraud detection
- Operational analysis

---

# Data Flow

## Weighbridge Data

```text
Weighbridge
     |
     v
Serial Client
     |
     v
Parser
     |
     v
Scheduler
     |
     v
State Manager
     |
     v
OPC UA
     |
     v
SCADA
```

## SAP + ML Data

```text
SAP Transaction
       |
       v
Feature Builder
       |
       v
Inference Engine
       |
       v
Prediction
       |
       v
OPC UA
```

---

# State Management

The State Manager acts as the shared memory layer of the application.

Example categories:

- Device states
- Weight values
- Sensor values
- SAP records
- RFID events
- Kiosk workflow state
- ML outputs

Advantages:

- Centralized data ownership
- Reduced module coupling
- Easier debugging

---

# Configuration

## system_config.json

Contains:

- Device definitions
- COM ports
- Baud rates
- OPC UA settings
- TCP settings
- Polling parameters

## tcp_payload.json

Defines the TCP payload structure exchanged with external devices.

Important:

Changes to payload structures should remain synchronized with firmware implementations.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/hsm-0510/routine_manager.git
cd routine_manager
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Install Package

```bash
pip install -e .
```

---

# Development Workflow

Recommended workflow:

```bash
git checkout -b feature/new-feature
```

Implement changes.

Run tests.

Commit changes.

Create pull request.

---

# Testing

The repository includes test modules covering:

- Serial communication
- Parser validation
- TCP communication
- OPC UA integration
- Multi-device scenarios
- SAP integration

Testing goals:

- Communication validation
- Regression prevention
- Integration verification

---

# Deployment Notes

Recommended production environment:

- Windows Industrial PC or Linux Industrial PC
- Dedicated serial ports
- Reliable OPC UA infrastructure
- Stable network connectivity
- Local database backup strategy

Operational recommendations:

- Enable logging
- Monitor device health
- Validate OPC UA connectivity
- Backup configuration files

---

# Troubleshooting

## No Weighbridge Data

Check:

- COM port
- Baud rate
- Cable connection
- Device power

## OPC UA Not Updating

Check:

- OPC UA endpoint
- Namespace configuration
- Firewall settings

## TCP Device Offline

Check:

- Device IP
- Network connectivity
- Firewall rules

## ML Prediction Errors

Check:

- Model files exist
- Feature generation logic
- Input data integrity

---

# Future Enhancements

Potential roadmap:

- MQTT integration
- REST API
- Docker deployment
- Web dashboard
- Centralized monitoring
- Multi-site synchronization
- Predictive maintenance analytics

---

# License

Refer to the repository license information for licensing terms and usage restrictions.
