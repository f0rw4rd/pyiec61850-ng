#!/usr/bin/env python3
"""
Basic IEC 61850 Connection Example

This example demonstrates how to establish a connection to an IEC 61850 server
using the safe MMSClient wrapper that handles memory management automatically.

Usage:
    python 01_basic_connection.py <server_ip>
    python 01_basic_connection.py 192.168.1.100
"""

import sys

# Use the safe MMS client
from pyiec61850.mms import MMSClient, ConnectionFailedError


def main():
    # Check command line arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <server_ip> [port]")
        print(f"Example: {sys.argv[0]} 192.168.1.100")
        print(f"Example: {sys.argv[0]} localhost 10102")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102

    # Use context manager for automatic cleanup
    # This ensures connection is properly closed even if an error occurs
    with MMSClient() as client:
        try:
            print(f"Connecting to IEC 61850 server at {hostname}:{port}")
            client.connect(hostname, port)
            print("SUCCESS: Connected to IEC 61850 server")

            # Get server identity
            identity = client.get_server_identity()
            if identity.vendor or identity.model:
                print(f"\nServer Identity:")
                print(f"  Vendor: {identity.vendor}")
                print(f"  Model: {identity.model}")
                print(f"  Revision: {identity.revision}")

            print("\nConnection established successfully!")
            print("You can now perform IEC 61850 operations...")

            # In a real application, you would perform operations here
            # For example: discover devices, read values, etc.

        except ConnectionFailedError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    # Connection is automatically closed when exiting the context manager
    print("\nConnection closed")


if __name__ == "__main__":
    main()
