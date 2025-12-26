# pyiec61850 API Reference

This document provides a comprehensive reference for the pyiec61850 Python bindings to libiec61850.

## Table of Contents

1. [Connection Management](#connection-management)
2. [Authentication](#authentication)
3. [Data Model Browsing](#data-model-browsing)
4. [Reading and Writing Values](#reading-and-writing-values)
5. [File Services](#file-services)
6. [Control Operations](#control-operations)
7. [Reporting](#reporting)
8. [GOOSE](#goose)
9. [Error Handling](#error-handling)
10. [Constants and Enumerations](#constants-and-enumerations)

## Connection Management

### IedConnection

The main class for connecting to IEC 61850 servers.

```python
# Create a connection
connection = pyiec61850.IedConnection_create()

# Connect to server
error = pyiec61850.IedConnection_connect(connection, hostname, port)

# Close connection
pyiec61850.IedConnection_close(connection)

# Destroy connection object
pyiec61850.IedConnection_destroy(connection)

# Get MMS connection for low-level operations
mms_connection = pyiec61850.IedConnection_getMmsConnection(connection)
```

### Connection States

```python
# Check if connected
state = pyiec61850.IedConnection_getState(connection)
# Returns: IED_STATE_CLOSED, IED_STATE_CONNECTING, IED_STATE_CONNECTED
```

## Authentication

### Password Authentication

```python
# Create authentication parameter
auth_param = pyiec61850.AcseAuthenticationParameter_create()

# Set authentication mechanism
pyiec61850.AcseAuthenticationParameter_setAuthMechanism(auth_param, pyiec61850.ACSE_AUTH_PASSWORD)

# Set password
pyiec61850.AcseAuthenticationParameter_setPassword(auth_param, "password123")

# Apply to connection
mms_connection = pyiec61850.IedConnection_getMmsConnection(connection)
iso_params = pyiec61850.MmsConnection_getIsoConnectionParameters(mms_connection)
pyiec61850.IsoConnectionParameters_setAcseAuthenticationParameter(iso_params, auth_param)

# Clean up
pyiec61850.AcseAuthenticationParameter_destroy(auth_param)
```

### Certificate Authentication

```python
# Set authentication mechanism to certificate
pyiec61850.AcseAuthenticationParameter_setAuthMechanism(auth_param, pyiec61850.ACSE_AUTH_CERTIFICATE)

# TLS configuration would be set separately
```

## Data Model Browsing

### Browse Server Directory

```python
# Get logical devices
error, device_list = pyiec61850.IedConnection_getServerDirectory(connection, True)

if error == pyiec61850.IED_ERROR_OK:
    for device in device_list:
        print(f"Logical Device: {device}")
```

### Browse Logical Device

```python
# Get logical nodes in a device
error, node_list = pyiec61850.IedConnection_getLogicalDeviceDirectory(connection, "DEVICE1")

if error == pyiec61850.IED_ERROR_OK:
    for node in node_list:
        print(f"Logical Node: {node}")
```

### Browse Data Objects

```python
# Get data objects in a logical node
error, object_list = pyiec61850.IedConnection_getLogicalNodeDirectory(
    connection, 
    "DEVICE1/LLN0",
    pyiec61850.ACSI_CLASS_DATA_OBJECT
)

# Get data attributes
error, attributes = pyiec61850.IedConnection_getLogicalNodeDirectory(
    connection,
    "DEVICE1/LLN0", 
    pyiec61850.ACSI_CLASS_DATA_ATTRIBUTE
)
```

## Reading and Writing Values

### Read Values

```python
# Read a single value
error, value = pyiec61850.IedConnection_readObject(connection, "DEVICE1/LLN0.Mod.stVal")

if error == pyiec61850.IED_ERROR_OK:
    # Get value based on type
    if pyiec61850.MmsValue_getType(value) == pyiec61850.MMS_INTEGER:
        int_val = pyiec61850.MmsValue_toInt32(value)
    elif pyiec61850.MmsValue_getType(value) == pyiec61850.MMS_FLOAT:
        float_val = pyiec61850.MmsValue_toFloat(value)
    elif pyiec61850.MmsValue_getType(value) == pyiec61850.MMS_BOOLEAN:
        bool_val = pyiec61850.MmsValue_getBoolean(value)
    elif pyiec61850.MmsValue_getType(value) == pyiec61850.MMS_STRING:
        str_val = pyiec61850.MmsValue_toString(value)
    
    # Clean up
    pyiec61850.MmsValue_delete(value)
```

### Write Values

```python
# Create value to write
value = pyiec61850.MmsValue_newIntegerFromInt32(1)

# Write value
error = pyiec61850.IedConnection_writeObject(connection, "DEVICE1/LLN0.Mod.stVal", value)

# Clean up
pyiec61850.MmsValue_delete(value)
```

### Read Multiple Values

```python
# Create dataset or list of variables
error, dataset = pyiec61850.IedConnection_readDataSetValues(connection, "DEVICE1/LLN0.Dataset1", None)

if error == pyiec61850.IED_ERROR_OK:
    # Access individual values in dataset
    count = pyiec61850.MmsValue_getArraySize(dataset)
    for i in range(count):
        element = pyiec61850.MmsValue_getElement(dataset, i)
        # Process element
```

## File Services

### List Files

```python
# Get file directory
error, file_list = pyiec61850.IedConnection_getFileDirectory(connection, directory_path)

if error == pyiec61850.IED_ERROR_OK:
    for file_entry in file_list:
        filename = pyiec61850.FileDirectoryEntry_getFileName(file_entry)
        filesize = pyiec61850.FileDirectoryEntry_getFileSize(file_entry)
        print(f"{filename} - {filesize} bytes")
```

### Download File

```python
# Using MmsConnection for file download
mms_connection = pyiec61850.IedConnection_getMmsConnection(connection)
mms_error = pyiec61850.MmsError_create()

success = pyiec61850.MmsConnection_downloadFile(
    mms_connection,
    mms_error,
    remote_filename,
    local_filename
)

error_code = pyiec61850.MmsError_getValue(mms_error)
```

### Download with Callback

```python
# Define callback function
def file_handler(parameter, buffer, bytes_read):
    # Process received bytes
    if bytes_read > 0:
        # Save to file or process data
        pass
    return True  # Continue download

# Download file with callback
error = pyiec61850.IedConnection_getFile(
    connection,
    remote_filename,
    file_handler,
    user_parameter
)
```

### Upload File

```python
# Upload file
error = pyiec61850.IedConnection_setFile(
    connection,
    remote_filename,
    local_filename
)
```

## Control Operations

### Direct Control

```python
# Create control value
control_value = pyiec61850.MmsValue_newBoolean(True)

# Execute direct control
error = pyiec61850.IedConnection_writeObject(
    connection,
    "DEVICE1/CTRL/GGIO1.SPCSO1.Oper.ctlVal",
    control_value
)

pyiec61850.MmsValue_delete(control_value)
```

### Select Before Operate (SBO)

```python
# Create control object
control = pyiec61850.ControlObjectClient_create("DEVICE1/CTRL/GGIO1.SPCSO1", connection)

# Select
success = pyiec61850.ControlObjectClient_select(control)

if success:
    # Operate
    control_value = pyiec61850.MmsValue_newBoolean(True)
    success = pyiec61850.ControlObjectClient_operate(control, control_value, 0)
    pyiec61850.MmsValue_delete(control_value)
    
    # Cancel selection if needed
    pyiec61850.ControlObjectClient_cancel(control)

# Clean up
pyiec61850.ControlObjectClient_destroy(control)
```

### Control with Enhanced Security

```python
# Select with value
control_value = pyiec61850.MmsValue_newBoolean(True)
success = pyiec61850.ControlObjectClient_selectWithValue(control, control_value)

# Operate with same value
if success:
    success = pyiec61850.ControlObjectClient_operate(control, control_value, 0)
```

## Reporting

### Browse Report Control Blocks

```python
# Get RCBs in a logical node
error, rcb_list = pyiec61850.IedConnection_getLogicalNodeDirectory(
    connection,
    "DEVICE1/LLN0",
    pyiec61850.ACSI_CLASS_URCB  # or ACSI_CLASS_BRCB for buffered
)
```

### Read RCB Values

```python
# Create RCB client
rcb = pyiec61850.ClientReportControlBlock_create("DEVICE1/LLN0.RP.Report01")

# Read RCB values
error = pyiec61850.IedConnection_getRCBValues(connection, rcb)

if error == pyiec61850.IED_ERROR_OK:
    # Get RCB parameters
    rpt_id = pyiec61850.ClientReportControlBlock_getRptId(rcb)
    enabled = pyiec61850.ClientReportControlBlock_getRptEna(rcb)
    dataset = pyiec61850.ClientReportControlBlock_getDataSetReference(rcb)
```

### Enable Reporting

```python
# Set report handler
def report_handler(parameter, report):
    # Get report details
    rpt_id = pyiec61850.ClientReport_getRptId(report)
    reason = pyiec61850.ClientReport_getReasonForInclusion(report, 0)
    
    # Get data values
    values = pyiec61850.ClientReport_getDataSetValues(report)
    # Process values
    
    return True  # Continue receiving reports

# Install handler
pyiec61850.IedConnection_installReportHandler(connection, "DEVICE1/LLN0.RP.Report01", report_handler, None)

# Enable reporting
pyiec61850.ClientReportControlBlock_setRptEna(rcb, True)
error = pyiec61850.IedConnection_setRCBValues(connection, rcb, pyiec61850.RCB_ELEMENT_RPT_ENA)
```

## GOOSE

### GOOSE Subscriber

```python
# Create GOOSE subscriber
subscriber = pyiec61850.GooseSubscriber_create("ethInterface", None)

# Set GOOSE received handler
def goose_handler(subscriber, parameter):
    # Process GOOSE message
    values = pyiec61850.GooseSubscriber_getDataSetValues(subscriber)
    # Process values

pyiec61850.GooseSubscriber_setListener(subscriber, goose_handler, None)

# Start subscriber
pyiec61850.GooseSubscriber_start(subscriber)

# Stop and destroy
pyiec61850.GooseSubscriber_stop(subscriber)
pyiec61850.GooseSubscriber_destroy(subscriber)
```

## Error Handling

### IED Error Codes

```python
# Common error codes
pyiec61850.IED_ERROR_OK                    # No error
pyiec61850.IED_ERROR_NOT_CONNECTED         # Not connected
pyiec61850.IED_ERROR_ALREADY_CONNECTED     # Already connected
pyiec61850.IED_ERROR_CONNECTION_LOST       # Connection lost
pyiec61850.IED_ERROR_SERVICE_NOT_SUPPORTED # Service not supported
pyiec61850.IED_ERROR_CONNECTION_REJECTED   # Connection rejected
pyiec61850.IED_ERROR_TIMEOUT               # Operation timeout
pyiec61850.IED_ERROR_ACCESS_DENIED         # Access denied

# Get error string
error_str = pyiec61850.IedClientError_toString(error)
```

### MMS Error Codes

```python
# Create MMS error object
mms_error = pyiec61850.MmsError_create()

# Get error value after operation
error_code = pyiec61850.MmsError_getValue(mms_error)

# Common MMS errors
pyiec61850.MMS_ERROR_NONE                  # No error
pyiec61850.MMS_ERROR_CONNECTION_REJECTED   # Connection rejected
pyiec61850.MMS_ERROR_CONNECTION_LOST       # Connection lost
pyiec61850.MMS_ERROR_SERVICE_TIMEOUT       # Service timeout
pyiec61850.MMS_ERROR_PARSING_RESPONSE      # Parse error
pyiec61850.MMS_ERROR_ACCESS_DENIED         # Access denied
```

## Constants and Enumerations

### Functional Constraints (FC)

```python
pyiec61850.FC_ST   # Status
pyiec61850.FC_MX   # Measurands
pyiec61850.FC_SP   # Setpoints
pyiec61850.FC_SV   # Substitution values
pyiec61850.FC_CF   # Configuration
pyiec61850.FC_DC   # Description
pyiec61850.FC_SG   # Setting groups
pyiec61850.FC_SE   # Setting group editable
pyiec61850.FC_CO   # Control
```

### MMS Value Types

```python
pyiec61850.MMS_BOOLEAN
pyiec61850.MMS_INTEGER
pyiec61850.MMS_UNSIGNED
pyiec61850.MMS_FLOAT
pyiec61850.MMS_BIT_STRING
pyiec61850.MMS_OCTET_STRING
pyiec61850.MMS_VISIBLE_STRING
pyiec61850.MMS_UTC_TIME
pyiec61850.MMS_ARRAY
pyiec61850.MMS_STRUCTURE
```

### Trigger Options for Reports

```python
pyiec61850.TRG_OPT_DATA_CHANGED    # Data change
pyiec61850.TRG_OPT_QUALITY_CHANGED # Quality change
pyiec61850.TRG_OPT_DATA_UPDATE     # Data update
pyiec61850.TRG_OPT_INTEGRITY       # Integrity scan
pyiec61850.TRG_OPT_GI              # General interrogation
```

## Best Practices

1. **Always check error codes** - Every operation returns an error code
2. **Clean up resources** - Use destroy/delete functions for all created objects
3. **Handle connection loss** - Implement reconnection logic
4. **Use callbacks for async operations** - File transfers, reports, GOOSE
5. **Thread safety** - Most functions are not thread-safe, use proper synchronization
6. **Use safe wrappers** - Prefer `pyiec61850.mms.MMSClient` over raw bindings

## MMS Module (Safe Wrappers)

The `pyiec61850.mms` module provides safe Python wrappers that handle memory
management automatically, preventing crashes and memory leaks.

### MMSClient

High-level client with automatic resource cleanup:

```python
from pyiec61850.mms import MMSClient, ConnectionFailedError, MMSError

# Context manager ensures cleanup even on exceptions
with MMSClient() as client:
    client.connect("192.168.1.100", 102)

    # Get server identity
    identity = client.get_server_identity()
    print(f"Vendor: {identity.vendor}")
    print(f"Model: {identity.model}")

    # Discover devices (LinkedList handled automatically)
    devices = client.get_logical_devices()
    for device in devices:
        nodes = client.get_logical_nodes(device)
        for node in nodes:
            objects = client.get_data_objects(device, node)

    # Read values (MmsValue cleaned up automatically)
    value = client.read_value("DEVICE1/LLN0.Mod.stVal")
```

### MMSClient Methods

```python
# Connection
client.connect(host, port=102, timeout=10000)
client.disconnect()
client.is_connected  # Property

# Server info
identity = client.get_server_identity()
# Returns: ServerIdentity(vendor, model, revision)

# Discovery
devices = client.get_logical_devices()      # List[str]
nodes = client.get_logical_nodes(device)    # List[str]
objects = client.get_data_objects(device, node)  # List[str]
attrs = client.get_data_attributes(device, node, obj)  # List[str]

# Data access
value = client.read_value(reference)        # Any
success = client.write_value(reference, value)  # bool
```

### Safe Utility Functions

For use with raw bindings when MMSClient doesn't cover your use case:

```python
from pyiec61850.mms.utils import (
    # NULL-safe string conversion (prevents segfault on NULL)
    safe_to_char_p,

    # Safe LinkedList iteration (skips NULL entries)
    safe_linked_list_iter,
    safe_linked_list_to_list,
    safe_linked_list_destroy,

    # Correct cleanup functions (fixes typo bugs)
    safe_mms_error_destroy,    # Uses MmsError_destroy (not MmsErrror)
    safe_mms_value_delete,
    safe_identity_destroy,

    # Context managers for automatic cleanup
    LinkedListGuard,
    MmsValueGuard,
    MmsErrorGuard,
    IdentityGuard,

    # Helper for tuple results
    unpack_result,
)
```

### Context Managers

```python
import pyiec61850.pyiec61850 as iec61850
from pyiec61850.mms.utils import LinkedListGuard, MmsValueGuard

# LinkedListGuard - auto-destroys list on exit
result = iec61850.IedConnection_getLogicalDeviceList(connection)
device_list, error = result

with LinkedListGuard(device_list) as guard:
    for name in guard:  # Iterates safely, skips NULL
        print(name)
# List automatically destroyed, reference nullified

# MmsValueGuard - auto-deletes value on exit
result = iec61850.IedConnection_readObject(connection, ref, fc)
value, error = result

with MmsValueGuard(value) as guard:
    if guard.value:
        print(iec61850.MmsValue_toFloat(guard.value))
# Value automatically deleted
```

### MMS Exceptions

```python
from pyiec61850.mms import (
    MMSError,              # Base exception
    LibraryNotFoundError,  # pyiec61850 not available
    ConnectionFailedError, # Connection failed
    NotConnectedError,     # Operation requires connection
    ReadError,             # Read operation failed
    WriteError,            # Write operation failed
    NullPointerError,      # NULL pointer detected
)
```

## Example: Complete Client

```python
import pyiec61850

def main():
    # Create and configure connection
    connection = pyiec61850.IedConnection_create()
    
    # Set up authentication if needed
    mms_connection = pyiec61850.IedConnection_getMmsConnection(connection)
    iso_params = pyiec61850.MmsConnection_getIsoConnectionParameters(mms_connection)
    
    auth = pyiec61850.AcseAuthenticationParameter_create()
    pyiec61850.AcseAuthenticationParameter_setAuthMechanism(auth, pyiec61850.ACSE_AUTH_PASSWORD)
    pyiec61850.AcseAuthenticationParameter_setPassword(auth, "password")
    pyiec61850.IsoConnectionParameters_setAcseAuthenticationParameter(iso_params, auth)
    
    # Connect
    error = pyiec61850.IedConnection_connect(connection, "localhost", 102)
    
    if error == pyiec61850.IED_ERROR_OK:
        print("Connected successfully")
        
        # Browse and read data
        error, devices = pyiec61850.IedConnection_getServerDirectory(connection, True)
        
        # ... perform operations ...
        
        # Disconnect
        pyiec61850.IedConnection_close(connection)
    else:
        print(f"Connection failed: {pyiec61850.IedClientError_toString(error)}")
    
    # Clean up
    pyiec61850.AcseAuthenticationParameter_destroy(auth)
    pyiec61850.IedConnection_destroy(connection)

if __name__ == "__main__":
    main()
```