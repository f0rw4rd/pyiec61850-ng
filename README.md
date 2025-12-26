# pyiec61850-ng

Next Generation Python bindings for libiec61850, packaged as a Python wheel.

[![Build and Test](https://github.com/f0rw4rd/pyiec61850-ng/actions/workflows/build-wheel.yml/badge.svg)](https://github.com/f0rw4rd/pyiec61850-ng/actions/workflows/build-wheel.yml)
[![PyPI version](https://badge.fury.io/py/pyiec61850-ng.svg)](https://badge.fury.io/py/pyiec61850-ng)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyiec61850-ng.svg)](https://pypi.org/project/pyiec61850-ng/)

This repository provides Python bindings for the [libiec61850](https://github.com/mz-automation/libiec61850) library, which is an open-source implementation of the IEC 61850 standard for communication networks and systems in substations.

## Installation

### Install from PyPI (Recommended)

```bash
pip install pyiec61850-ng
```

### Install from GitHub Release

```bash
pip install pyiec61850-ng --find-links https://github.com/f0rw4rd/pyiec61850-ng/releases/latest/download/
```

### Install directly from GitHub

```bash
pip install git+https://github.com/f0rw4rd/pyiec61850-ng.git
```

### Install from local wheel

```bash
pip install pyiec61850-ng-*.whl
```

## Usage

### Quick Start (Recommended - Safe API)

```python
from pyiec61850.mms import MMSClient

# Use context manager for automatic cleanup
with MMSClient() as client:
    client.connect("192.168.1.100", 102)
    print("Connected successfully!")

    # Get server identity
    identity = client.get_server_identity()
    print(f"Server: {identity.vendor} {identity.model}")

    # Discover logical devices
    devices = client.get_logical_devices()
    for device in devices:
        print(f"Device: {device}")

        # Get logical nodes
        nodes = client.get_logical_nodes(device)
        for node in nodes:
            print(f"  Node: {node}")

# Connection automatically closed
```

### Low-Level API

For advanced use cases, you can use the raw bindings directly:

```python
import pyiec61850.pyiec61850 as pyiec61850

# Create and connect to an IEC 61850 server
connection = pyiec61850.IedConnection_create()
error = pyiec61850.IedConnection_connect(connection, "192.168.1.100", 102)

if error == pyiec61850.IED_ERROR_OK:
    print("Connected successfully!")
    # Perform operations...
    pyiec61850.IedConnection_close(connection)

pyiec61850.IedConnection_destroy(connection)
```

### Examples

For comprehensive examples, see the [examples directory](https://github.com/f0rw4rd/pyiec61850-ng/tree/main/examples):

- [**Basic Connection**](https://github.com/f0rw4rd/pyiec61850-ng/blob/main/examples/01_basic_connection.py) - Connect to an IEC 61850 server
- [**Device Discovery**](https://github.com/f0rw4rd/pyiec61850-ng/blob/main/examples/02_device_discovery.py) - Discover logical devices, nodes, and data objects
- [**Reading Data**](https://github.com/f0rw4rd/pyiec61850-ng/blob/main/examples/03_read_data_values.py) - Read values from data objects
- [**File Transfer**](https://github.com/f0rw4rd/pyiec61850-ng/blob/main/examples/04_file_transfer.py) - Download files using MMS file services

Run examples:
```bash
python examples/01_basic_connection.py 192.168.1.100
python examples/02_device_discovery.py 192.168.1.100
```

## Building from Source

The wheel package is built using Docker:

```bash
docker build -t pyiec61850-builder --build-arg LIBIEC61850_VERSION=v1.6 .
```

To extract the wheel file:

```bash
mkdir -p ./dist
docker create --name wheel-container pyiec61850-builder
docker cp wheel-container:/wheels/. ./dist/
docker rm wheel-container
```

## Versioning

This package uses the format: `LIBIEC61850_VERSION.REVISION`
- **Example**: `1.6.0.1` = libiec61850 v1.6.0, first package revision
- **1.6.0**: The exact libiec61850 version included (static)
- **.1**: Package revision for bug fixes, rebuilds, binding improvements

This clearly shows which libiec61850 version you're getting and our package iteration.

Check current version:
```bash
python version.py        # Package version: 1.6.0.1
python version.py --libiec61850  # libiec61850 version: v1.6.0
```

## TASE.2/ICCP Support (Highly Experimental)

> **Warning**: TASE.2 support is highly experimental and may change significantly.

pyiec61850-ng includes support for TASE.2 (IEC 60870-6), also known as ICCP
(Inter-Control Center Communications Protocol), used for real-time data exchange
between control centers in the electric utility industry.

### TASE.2 Quick Start

```python
from pyiec61850.tase2 import TASE2Client

client = TASE2Client(
    local_ap_title="1.1.1.999",
    remote_ap_title="1.1.1.998"
)
client.connect("192.168.1.100", port=102)

# Discover domains (VCC/ICC)
domains = client.get_domains()
for domain in domains:
    print(f"Domain: {domain.name} ({domain.domain_type})")

# Read a data point
value = client.read_point("ICC1", "Voltage")
print(f"Value: {value.value}, Quality: {value.quality}")

# Security analysis
security = client.analyze_security()
print(f"Readable points: {security['readable_points']}")
print(f"Concerns: {security['concerns']}")

client.disconnect()
```

### TASE.2 Features

- **Domain Discovery**: VCC (Virtual Control Center) and ICC (Indication Control Center)
- **Variable Enumeration**: List and read data points with quality information
- **Data Point Access**: Read/write individual points or bulk enumeration
- **Transfer Sets (Block 2)**: RBE (Report-by-Exception) management
- **Device Control (Block 5)**: Select-Before-Operate, commands, setpoints
- **Bilateral Tables**: Access control configuration queries
- **Security Analysis**: Automated security assessment and recommendations

### TASE.2 Data Types

```python
from pyiec61850.tase2 import (
    Domain,          # VCC/ICC domain
    PointValue,      # Data point with value and quality
    TransferSet,     # Block 2 transfer set
    BilateralTable,  # Access control table
    ServerInfo,      # Server information
)
```

## MMS Module (Safe Wrappers)

The `pyiec61850.mms` module provides safe Python wrappers around the raw SWIG bindings,
preventing common crashes from NULL pointer dereferences and memory leaks.

### Why Use the Safe Wrappers?

The raw pyiec61850 bindings require careful memory management:
- `LinkedList_destroy()` must be called after iteration
- `MmsValue_delete()` must be called after reading values
- `toCharP()` crashes on NULL pointers

The MMS module handles all of this automatically.

### MMS Client Example

```python
from pyiec61850.mms import MMSClient, ConnectionFailedError

with MMSClient() as client:
    try:
        client.connect("192.168.1.100", 102)

        # All memory management is automatic
        for device in client.get_logical_devices():
            for node in client.get_logical_nodes(device):
                print(f"{device}/{node}")

    except ConnectionFailedError as e:
        print(f"Connection failed: {e}")
```

### Safe Utilities for Raw Bindings

If you need to use raw bindings, use the safe utilities:

```python
from pyiec61850.mms.utils import (
    safe_to_char_p,        # NULL-safe string conversion
    LinkedListGuard,       # Auto-cleanup context manager
    MmsValueGuard,         # Auto-cleanup for MmsValue
)
import pyiec61850.pyiec61850 as iec61850

# Safe iteration with automatic cleanup
result = iec61850.IedConnection_getLogicalDeviceList(connection)
device_list, error = result

with LinkedListGuard(device_list) as guard:
    for device_name in guard:  # NULL pointers automatically skipped
        print(device_name)
# LinkedList automatically destroyed
```

