# IEC 61850 Python Examples

This directory contains practical examples demonstrating how to use the pyiec61850 library for various IEC 61850 operations.

All examples use the **safe `MMSClient` wrapper** which handles memory management automatically, preventing crashes from NULL pointer dereferences and memory leaks.

## Prerequisites

Before running these examples, make sure you have:

1. Built and installed the pyiec61850 wheel:
   ```bash
   python setup.py build_ext
   pip install dist/pyiec61850-*.whl
   ```

2. Access to an IEC 61850 server (real device, simulator, or use the provided Docker test server)

## Quick Start with Docker Test Server

This directory includes a Docker setup to run a libiec61850 test server:

### Starting the Test Server

```bash
# Start the IEC 61850 test server
docker-compose up -d

# Check that it's running
docker-compose ps

# View server logs
docker-compose logs -f iec61850-server
```

The test server will be available at `localhost:10102` (mapped from container port 102).

### Running Examples Against the Test Server

```bash
# Basic connection test
python 01_basic_connection.py localhost 10102

# Discover devices
python 02_device_discovery.py localhost 10102

# Read data values
python 03_read_data_values.py localhost 10102

# File transfer (if supported by the server)
python 04_file_transfer.py localhost 10102
```

### Stopping the Test Server

```bash
docker-compose down
```

### Using Different Test Servers

The Docker image includes several example servers. To use a different one, edit `docker-compose.yml` and change the command:

- `server_example_basic_io` - Basic I/O operations (default)
- `server_example_goose` - GOOSE publisher (requires NET_RAW capability)
- `server_example_control` - Control operations
- `server_example_61400_25` - Wind power plant data model

Or uncomment one of the alternative service definitions in `docker-compose.yml`.

## Examples

### [01_basic_connection.py](01_basic_connection.py)
Demonstrates the fundamentals of connecting to an IEC 61850 server using the safe `MMSClient`.

**Usage:**
```bash
python 01_basic_connection.py <server_ip>
python 01_basic_connection.py 192.168.1.100
```

**Key concepts:**
- Using `MMSClient` with context manager for automatic cleanup
- Establishing connections with error handling
- Getting server identity information

### [02_device_discovery.py](02_device_discovery.py)
Shows how to discover the data model hierarchy of an IEC 61850 server.

**Usage:**
```bash
python 02_device_discovery.py <server_ip>
python 02_device_discovery.py 192.168.1.100
```

**Key concepts:**
- Discovering logical devices with `get_logical_devices()`
- Enumerating logical nodes with `get_logical_nodes()`
- Listing data objects with `get_data_objects()`
- Automatic LinkedList cleanup (no manual memory management needed)

### [03_read_data_values.py](03_read_data_values.py)
Demonstrates reading different types of data values from the server.

**Usage:**
```bash
# Discover and read sample values
python 03_read_data_values.py <server_ip>

# Read specific object
python 03_read_data_values.py <server_ip> <object_reference>
python 03_read_data_values.py 192.168.1.100 "TEMPLATE1LD0/MMXU1.TotW.mag.f"
```

**Key concepts:**
- Reading values with `read_value()`
- Automatic MmsValue conversion to Python types
- Automatic cleanup of MmsValue objects

### [04_file_transfer.py](04_file_transfer.py)
Shows how to download files from an IEC 61850 server using MMS file services.

**Usage:**
```bash
# Show file transfer info
python 04_file_transfer.py <server_ip>

# Download specific file
python 04_file_transfer.py <server_ip> <remote_file> <local_file>
python 04_file_transfer.py 192.168.1.100 "/COMTRADE/fault_001.cfg" "fault_001.cfg"
```

**Key concepts:**
- Using raw bindings with safe `MmsErrorGuard` for cleanup
- File download operations
- Mixing raw bindings with safe utilities

### [05_tase2_demo.py](05_tase2_demo.py)
Demonstrates TASE.2/ICCP client functionality with a mock server.

**Usage:**
```bash
python 05_tase2_demo.py
```

**Key concepts:**
- TASE.2 domain discovery (VCC/ICC)
- Reading data points with quality
- Transfer sets and control operations
- Security analysis

## Common Patterns

### Using MMSClient (Recommended)

The `MMSClient` handles all memory management automatically:

```python
from pyiec61850.mms import MMSClient, ConnectionFailedError

with MMSClient() as client:
    try:
        client.connect(hostname, port)
        devices = client.get_logical_devices()
        # No manual cleanup needed!
    except ConnectionFailedError as e:
        print(f"Connection failed: {e}")
# Connection automatically closed
```

### Error Handling

With MMSClient, use exception handling:
```python
from pyiec61850.mms import (
    MMSClient,
    ConnectionFailedError,
    NotConnectedError,
    MMSError,
)

try:
    client.connect(hostname, port)
    devices = client.get_logical_devices()
except ConnectionFailedError as e:
    print(f"Connection failed: {e}")
except MMSError as e:
    print(f"MMS error: {e}")
```

### Using Raw Bindings with Safe Utilities

If you need raw bindings, use the safe utilities:
```python
from pyiec61850.mms.utils import LinkedListGuard, safe_to_char_p
import pyiec61850.pyiec61850 as iec61850

# Automatic LinkedList cleanup
with LinkedListGuard(device_list) as guard:
    for name in guard:
        print(name)  # NULL entries automatically skipped
# List destroyed automatically
```

## Troubleshooting

1. **Import Error**: Make sure pyiec61850 is installed:
   ```bash
   pip list | grep pyiec61850
   ```

2. **Connection Failed**: Verify:
   - Server IP and port (default 102)
   - Network connectivity
   - Server is running and accepting connections

3. **Object Not Found**: The object references may vary by server. Use the discovery example to find valid references.

## Additional Resources

- [IEC 61850 Standard Documentation](https://webstore.iec.ch/publication/6028)
- [libiec61850 Documentation](https://libiec61850.com/libiec61850/documentation/)
- [pyiec61850 GitHub Repository](https://github.com/f0rw4rd/pyiec61850-ng)