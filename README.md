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

### Quick Start

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

