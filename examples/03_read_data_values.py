#!/usr/bin/env python3
"""
IEC 61850 Data Reading Example

This example demonstrates how to read different types of data values from
an IEC 61850 server, including handling different data types and functional
constraints.

Usage:
    python 03_read_data_values.py <server_ip> <object_reference>
    python 03_read_data_values.py 192.168.1.100 "TEMPLATE1LD0/MMXU1.TotW.mag.f"
"""

import sys
import ctypes
import pyiec61850.pyiec61850 as pyiec61850


def extract_mms_value(mms_value):
    """
    Extract Python value from MMS value based on its type
    
    Args:
        mms_value: MMS value object
    
    Returns:
        Python representation of the value
    """
    if not mms_value:
        return None
    
    try:
        value_type = pyiec61850.MmsValue_getType(mms_value)
        type_string = pyiec61850.MmsValue_getTypeString(mms_value)
        
        print(f"  Value type: {type_string}")
        
        if value_type == pyiec61850.MMS_BOOLEAN:
            return bool(pyiec61850.MmsValue_getBoolean(mms_value))
            
        elif value_type == pyiec61850.MMS_INTEGER:
            return pyiec61850.MmsValue_toInt64(mms_value)
            
        elif value_type == pyiec61850.MMS_UNSIGNED:
            return pyiec61850.MmsValue_toUint32(mms_value)
            
        elif value_type == pyiec61850.MMS_FLOAT:
            return pyiec61850.MmsValue_toFloat(mms_value)
            
        elif value_type == pyiec61850.MMS_VISIBLE_STRING:
            return pyiec61850.MmsValue_toString(mms_value)
            
        elif value_type == pyiec61850.MMS_BIT_STRING:
            size = pyiec61850.MmsValue_getBitStringSize(mms_value)
            return f"BitString({size} bits)"
            
        elif value_type == pyiec61850.MMS_OCTET_STRING:
            size = pyiec61850.MmsValue_getOctetStringSize(mms_value)
            return f"OctetString({size} bytes)"
            
        elif value_type == pyiec61850.MMS_UTC_TIME:
            # UTC time in milliseconds
            time_val = pyiec61850.MmsValue_getUtcTimeInMs(mms_value)
            return f"UTCTime({time_val}ms)"
            
        elif value_type == pyiec61850.MMS_STRUCTURE:
            # Structure contains multiple elements
            size = pyiec61850.MmsValue_getArraySize(mms_value)
            return f"Structure({size} elements)"
            
        elif value_type == pyiec61850.MMS_ARRAY:
            size = pyiec61850.MmsValue_getArraySize(mms_value)
            return f"Array({size} elements)"
            
        else:
            return f"UnknownType({value_type})"
            
    except Exception as e:
        print(f"  ERROR extracting value: {e}")
        return None


def read_data_object(connection, object_reference, fc=None):
    """
    Read a data object from the server
    
    Args:
        connection: Active IED connection
        object_reference: Full reference to the data object (e.g., "LD0/MMXU1.TotW.mag.f")
        fc: Functional constraint (default: try common ones)
    
    Returns:
        Value or None if failed
    """
    print(f"\nReading data object: {object_reference}")
    
    # Common functional constraints to try
    fc_list = [fc] if fc else [
        pyiec61850.IEC61850_FC_MX,  # Measured values
        pyiec61850.IEC61850_FC_ST,  # Status
        pyiec61850.IEC61850_FC_CF,  # Configuration
        pyiec61850.IEC61850_FC_SP,  # Set points
        pyiec61850.IEC61850_FC_DC,  # Description
    ]
    
    fc_names = {
        pyiec61850.IEC61850_FC_MX: "MX (Measured values)",
        pyiec61850.IEC61850_FC_ST: "ST (Status)",
        pyiec61850.IEC61850_FC_CF: "CF (Configuration)",
        pyiec61850.IEC61850_FC_SP: "SP (Set points)",
        pyiec61850.IEC61850_FC_DC: "DC (Description)",
    }
    
    for fc_try in fc_list:
        print(f"\nTrying functional constraint: {fc_names.get(fc_try, fc_try)}")
        
        # IedConnection_readObject returns [MmsValue, error_code]
        result = pyiec61850.IedConnection_readObject(
            connection,
            object_reference,
            fc_try
        )
        
        if len(result) != 2:
            print(f"  ERROR: Unexpected result from readObject")
            continue
            
        value, error = result
        
        if error == pyiec61850.IED_ERROR_OK and value:
            # Successfully read value
            extracted_value = extract_mms_value(value)
            print(f"  SUCCESS: Value = {extracted_value}")
            
            # Clean up
            pyiec61850.MmsValue_delete(value)
            return extracted_value
        else:
            error_msg = pyiec61850.IedClientError_toString(error)
            print(f"  Failed: {error_msg}")
    
    print(f"\nERROR: Could not read {object_reference} with any functional constraint")
    return None


def read_common_objects(connection):
    """
    Try to read some common IEC 61850 data objects
    
    Args:
        connection: Active IED connection
    """
    print("\n" + "="*60)
    print("READING COMMON DATA OBJECTS")
    print("="*60)
    
    # Common object references to try (adjust based on your server)
    common_objects = [
        # Measurement objects
        ("TEMPLATE1LD0/MMXU1.TotW.mag.f", pyiec61850.IEC61850_FC_MX),
        ("TEMPLATE1LD0/MMXU1.TotVAr.mag.f", pyiec61850.IEC61850_FC_MX),
        ("TEMPLATE1LD0/MMXU1.Hz.mag.f", pyiec61850.IEC61850_FC_MX),
        
        # Status objects
        ("TEMPLATE1LD0/GGIO1.Ind1.stVal", pyiec61850.IEC61850_FC_ST),
        ("TEMPLATE1LD0/XCBR1.Pos.stVal", pyiec61850.IEC61850_FC_ST),
        
        # Configuration objects
        ("TEMPLATE1LD0/LLN0.NamPlt.vendor", pyiec61850.IEC61850_FC_DC),
        ("TEMPLATE1LD0/LLN0.NamPlt.swRev", pyiec61850.IEC61850_FC_DC),
    ]
    
    successful_reads = 0
    failed_reads = 0
    
    for obj_ref, fc in common_objects:
        value = read_data_object(connection, obj_ref, fc)
        if value is not None:
            successful_reads += 1
        else:
            failed_reads += 1
    
    print("\n" + "="*60)
    print(f"Read summary: {successful_reads} successful, {failed_reads} failed")


def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [object_reference]")
        print(f"Example 1: {sys.argv[0]} 192.168.1.100")
        print(f"Example 2: {sys.argv[0]} localhost 10102")
        print(f'Example 3: {sys.argv[0]} 192.168.1.100 102 "TEMPLATE1LD0/MMXU1.TotW.mag.f"')
        sys.exit(1)
    
    hostname = sys.argv[1]
    
    # Parse optional port and object reference
    port = 102
    specific_object = None
    
    if len(sys.argv) > 2:
        # Check if second argument is a port number
        try:
            port = int(sys.argv[2])
            specific_object = sys.argv[3] if len(sys.argv) > 3 else None
        except ValueError:
            # Second argument is not a number, treat as object reference
            specific_object = sys.argv[2]
    
    # Create and connect to server
    print(f"Connecting to IEC 61850 server at {hostname}:{port}")
    connection = pyiec61850.IedConnection_create()
    
    if not connection:
        print("ERROR: Failed to create connection object")
        sys.exit(1)
    
    error = pyiec61850.IedConnection_connect(connection, hostname, port)
    
    if error != pyiec61850.IED_ERROR_OK:
        error_msg = pyiec61850.IedClientError_toString(error)
        print(f"ERROR: Connection failed - {error_msg}")
        pyiec61850.IedConnection_destroy(connection)
        sys.exit(1)
    
    print("SUCCESS: Connected to server")
    
    try:
        if specific_object:
            # Read specific object provided by user
            read_data_object(connection, specific_object)
        else:
            # Try reading common objects
            read_common_objects(connection)
            
    except Exception as e:
        print(f"\nERROR: Exception during reading - {e}")
        
    finally:
        # Clean up
        print("\nClosing connection...")
        pyiec61850.IedConnection_close(connection)
        pyiec61850.IedConnection_destroy(connection)
        print("Done")


if __name__ == "__main__":
    main()