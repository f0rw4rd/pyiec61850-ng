# IEC 61850 Python Examples

This directory contains practical examples demonstrating how to use the pyiec61850 library for various IEC 61850 operations.

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
Demonstrates the fundamentals of connecting to an IEC 61850 server.

**Usage:**
```bash
python 01_basic_connection.py <server_ip>
python 01_basic_connection.py 192.168.1.100
```

**Key concepts:**
- Creating IED connection objects
- Establishing connections
- Error handling
- Proper cleanup

### [02_device_discovery.py](02_device_discovery.py)
Shows how to discover the data model hierarchy of an IEC 61850 server.

**Usage:**
```bash
python 02_device_discovery.py <server_ip>
python 02_device_discovery.py 192.168.1.100
```

**Key concepts:**
- Discovering logical devices
- Enumerating logical nodes
- Listing data objects
- Using LinkedList operations
- Memory management with ctypes

### [03_read_data_values.py](03_read_data_values.py)
Demonstrates reading different types of data values from the server.

**Usage:**
```bash
# Read common objects
python 03_read_data_values.py <server_ip>

# Read specific object
python 03_read_data_values.py <server_ip> <object_reference>
python 03_read_data_values.py 192.168.1.100 "TEMPLATE1LD0/MMXU1.TotW.mag.f"
```

**Key concepts:**
- Reading data objects with functional constraints
- Handling different MMS data types
- Extracting values from MmsValue objects
- Common object references

### [04_file_transfer.py](04_file_transfer.py)
Shows how to download files from an IEC 61850 server using MMS file services.

**Usage:**
```bash
# List files in root directory
python 04_file_transfer.py <server_ip>

# Download specific file
python 04_file_transfer.py <server_ip> <remote_file> <local_file>
python 04_file_transfer.py 192.168.1.100 "/COMTRADE/fault_001.cfg" "fault_001.cfg"
```

**Key concepts:**
- MMS connection vs IED connection
- File download operations
- Error handling with MmsError
- File directory operations

## Common Patterns

### Error Handling
All examples demonstrate proper error handling:
```python
error = pyiec61850.IedConnection_connect(connection, hostname, port)
if error != pyiec61850.IED_ERROR_OK:
    error_msg = pyiec61850.IedClientError_toString(error)
    print(f"Connection failed: {error_msg}")
```

### Memory Management
Proper cleanup is essential:
```python
# Always destroy objects when done
pyiec61850.IedConnection_close(connection)
pyiec61850.IedConnection_destroy(connection)
pyiec61850.MmsValue_delete(value)
pyiec61850.LinkedList_destroy(list)
```

### Using ctypes
Many operations require ctypes for proper C interop:
```python
import ctypes

error = ctypes.c_int()
device_list = pyiec61850.IedConnection_getLogicalDeviceList(
    connection, ctypes.byref(error)
)
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