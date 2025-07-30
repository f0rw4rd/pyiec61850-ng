#!/usr/bin/env python3
"""
IEC 61850 Device Discovery Example

This example demonstrates how to discover the logical devices, logical nodes,
and data objects in an IEC 61850 server.

Usage:
    python 02_device_discovery.py <server_ip>
    python 02_device_discovery.py 192.168.1.100
"""

import sys
import ctypes
import pyiec61850.pyiec61850 as pyiec61850


def discover_logical_devices(connection):
    """
    Discover all logical devices on the server
    
    Args:
        connection: Active IED connection
    
    Returns:
        List of logical device names
    """
    devices = []
    
    print("\nDiscovering logical devices...")
    
    # Get logical device list - returns [LinkedList, error_code]
    result = pyiec61850.IedConnection_getLogicalDeviceList(connection)
    
    if len(result) != 2:
        print("ERROR: Unexpected result from getLogicalDeviceList")
        return devices
        
    device_list, error = result
    
    if error != pyiec61850.IED_ERROR_OK or not device_list:
        error_msg = pyiec61850.IedClientError_toString(error) if error else "Unknown error"
        print(f"ERROR: Failed to get device list - {error_msg}")
        return devices
    
    # Count devices
    device_count = pyiec61850.LinkedList_size(device_list)
    print(f"Found {device_count} logical device(s)")
    
    # Iterate through devices
    element = pyiec61850.LinkedList_getNext(device_list)
    while element:
        device_name = pyiec61850.LinkedList_getData(element)
        if device_name:
            # Convert SWIG void* to char*
            char_ptr = pyiec61850.toCharP(device_name)
            if char_ptr:
                devices.append(char_ptr)
                print(f"  - Logical Device: {char_ptr}")
        element = pyiec61850.LinkedList_getNext(element)
    
    # Clean up
    pyiec61850.LinkedList_destroy(device_list)
    
    return devices


def discover_logical_nodes(connection, device_name):
    """
    Discover logical nodes for a specific device
    
    Args:
        connection: Active IED connection
        device_name: Name of the logical device
    
    Returns:
        List of logical node names
    """
    nodes = []
    
    print(f"\n  Discovering logical nodes for device '{device_name}'...")
    
    # Get logical device directory - returns [LinkedList, error_code]
    result = pyiec61850.IedConnection_getLogicalDeviceDirectory(
        connection, device_name
    )
    
    if len(result) != 2:
        print(f"  ERROR: Unexpected result from getLogicalNodeList")
        return nodes
        
    node_list, error = result
    
    if error != pyiec61850.IED_ERROR_OK or not node_list:
        error_msg = pyiec61850.IedClientError_toString(error) if error else "Unknown error"
        print(f"  ERROR: Failed to get logical nodes - {error_msg}")
        return nodes
    
    # Iterate through logical nodes
    element = pyiec61850.LinkedList_getNext(node_list)
    while element:
        node_name = pyiec61850.LinkedList_getData(element)
        if node_name:
            # Convert SWIG void* to char*
            name_str = pyiec61850.toCharP(node_name)
            nodes.append(name_str)
            print(f"    - Logical Node: {name_str}")
        element = pyiec61850.LinkedList_getNext(element)
    
    # Clean up
    pyiec61850.LinkedList_destroy(node_list)
    
    return nodes


def discover_data_objects(connection, device_name, node_name, max_objects=10):
    """
    Discover data objects for a specific logical node
    
    Args:
        connection: Active IED connection
        device_name: Name of the logical device
        node_name: Name of the logical node
        max_objects: Maximum number of objects to display
    
    Returns:
        List of data object names
    """
    objects = []
    
    # Construct logical node reference
    ln_ref = f"{device_name}/{node_name}"
    
    print(f"\n    Discovering data objects for node '{ln_ref}'...")
    
    # Get data object list - returns [LinkedList, error_code]
    result = pyiec61850.IedConnection_getLogicalNodeDirectory(
        connection, ln_ref, pyiec61850.ACSI_CLASS_DATA_OBJECT
    )
    
    if len(result) != 2:
        print(f"    ERROR: Unexpected result from getLogicalNodeDirectory")
        return objects
        
    object_list, error = result
    
    if error != pyiec61850.IED_ERROR_OK or not object_list:
        error_msg = pyiec61850.IedClientError_toString(error) if error else "Unknown error"
        print(f"    ERROR: Failed to get data objects - {error_msg}")
        return objects
    
    # Iterate through data objects (limit display for readability)
    count = 0
    element = pyiec61850.LinkedList_getNext(object_list)
    while element and count < max_objects:
        object_name = pyiec61850.LinkedList_getData(element)
        if object_name:
            # Convert SWIG void* to char*
            name_str = pyiec61850.toCharP(object_name)
            objects.append(name_str)
            full_ref = f"{ln_ref}.{name_str}"
            print(f"      - Data Object: {full_ref}")
            count += 1
        element = pyiec61850.LinkedList_getNext(element)
    
    # Check if there are more objects
    total_objects = pyiec61850.LinkedList_size(object_list)
    if total_objects > max_objects:
        print(f"      ... and {total_objects - max_objects} more objects")
    
    # Clean up
    pyiec61850.LinkedList_destroy(object_list)
    
    return objects


def discover_complete_model(connection):
    """
    Discover the complete data model of the server
    
    Args:
        connection: Active IED connection
    """
    print("\n" + "="*60)
    print("DISCOVERING IEC 61850 DATA MODEL")
    print("="*60)
    
    # Discover logical devices
    devices = discover_logical_devices(connection)
    
    if not devices:
        print("\nNo logical devices found!")
        return
    
    # For each device, discover logical nodes
    for device in devices:
        nodes = discover_logical_nodes(connection, device)
        
        # For the first few nodes, discover data objects as examples
        for i, node in enumerate(nodes[:3]):  # Limit to first 3 nodes for brevity
            discover_data_objects(connection, device, node, max_objects=5)
            
        if len(nodes) > 3:
            print(f"\n  ... and {len(nodes) - 3} more logical nodes in {device}")
    
    print("\n" + "="*60)
    print("Discovery complete!")


def main():
    # Check command line arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <server_ip> [port]")
        print(f"Example: {sys.argv[0]} 192.168.1.100")
        print(f"Example: {sys.argv[0]} localhost 10102")
        sys.exit(1)
    
    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102
    
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
        # Discover the complete data model
        discover_complete_model(connection)
        
    except Exception as e:
        print(f"\nERROR: Exception during discovery - {e}")
        
    finally:
        # Clean up
        print("\nClosing connection...")
        pyiec61850.IedConnection_close(connection)
        pyiec61850.IedConnection_destroy(connection)
        print("Done")


if __name__ == "__main__":
    main()