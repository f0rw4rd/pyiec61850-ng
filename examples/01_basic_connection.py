#!/usr/bin/env python3
"""
Basic IEC 61850 Connection Example

This example demonstrates how to establish a connection to an IEC 61850 server
and handle connection errors properly.

Usage:
    python 01_basic_connection.py <server_ip>
    python 01_basic_connection.py 192.168.1.100
"""

import sys
import pyiec61850.pyiec61850 as pyiec61850


def connect_to_server(hostname, port=102):
    """
    Establish connection to IEC 61850 server
    
    Args:
        hostname: IP address or hostname of the IEC 61850 server
        port: Port number (default 102)
    
    Returns:
        connection object or None if failed
    """
    print(f"Connecting to IEC 61850 server at {hostname}:{port}")
    
    # Create IED connection object
    connection = pyiec61850.IedConnection_create()
    
    if not connection:
        print("ERROR: Failed to create connection object")
        return None
    
    # Attempt to connect
    error = pyiec61850.IedConnection_connect(connection, hostname, port)
    
    if error != pyiec61850.IED_ERROR_OK:
        error_msg = pyiec61850.IedClientError_toString(error)
        print(f"ERROR: Connection failed - {error_msg} (code: {error})")
        
        # Clean up
        pyiec61850.IedConnection_destroy(connection)
        return None
    
    print("SUCCESS: Connected to IEC 61850 server")
    return connection


def main():
    # Check command line arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <server_ip> [port]")
        print(f"Example: {sys.argv[0]} 192.168.1.100")
        print(f"Example: {sys.argv[0]} localhost 10102")
        sys.exit(1)
    
    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102
    
    # Connect to server
    connection = connect_to_server(hostname, port)
    
    if connection:
        try:
            print("\nConnection established successfully!")
            print("You can now perform IEC 61850 operations...")
            
            # In a real application, you would perform operations here
            # For example: discover devices, read values, etc.
            
        finally:
            # Always close and clean up the connection
            print("\nClosing connection...")
            pyiec61850.IedConnection_close(connection)
            pyiec61850.IedConnection_destroy(connection)
            print("Connection closed")
    else:
        print("\nFailed to establish connection")
        sys.exit(1)


if __name__ == "__main__":
    main()