#!/usr/bin/env python3
"""
IEC 61850 Device Discovery Example

This example demonstrates how to discover the logical devices, logical nodes,
and data objects in an IEC 61850 server using the safe MMSClient wrapper.

The MMSClient handles memory management automatically, preventing crashes
from NULL pointer dereferences and memory leaks.

Usage:
    python 02_device_discovery.py <server_ip>
    python 02_device_discovery.py 192.168.1.100
"""

import sys

# Use the safe MMS client
from pyiec61850.mms import (
    MMSClient,
    ConnectionFailedError,
    NotConnectedError,
    MMSError,
)


def discover_complete_model(client):
    """
    Discover the complete data model of the server.

    The MMSClient methods handle LinkedList iteration and cleanup
    automatically, preventing the segfaults that can occur with
    manual memory management.

    Args:
        client: Connected MMSClient instance
    """
    print("\n" + "=" * 60)
    print("DISCOVERING IEC 61850 DATA MODEL")
    print("=" * 60)

    # Discover logical devices
    # The client uses LinkedListGuard internally for safe iteration
    print("\nDiscovering logical devices...")
    devices = client.get_logical_devices()

    if not devices:
        print("No logical devices found!")
        return

    print(f"Found {len(devices)} logical device(s)")
    for device in devices:
        print(f"  - Logical Device: {device}")

    # For each device, discover logical nodes
    for device in devices:
        print(f"\n  Discovering logical nodes for device '{device}'...")
        nodes = client.get_logical_nodes(device)

        if not nodes:
            print(f"    No logical nodes found in {device}")
            continue

        print(f"    Found {len(nodes)} logical node(s)")
        for node in nodes[:10]:  # Limit display for readability
            print(f"    - Logical Node: {node}")

        if len(nodes) > 10:
            print(f"    ... and {len(nodes) - 10} more logical nodes")

        # For the first few nodes, discover data objects as examples
        for node in nodes[:3]:
            print(f"\n    Discovering data objects for node '{device}/{node}'...")
            data_objects = client.get_data_objects(device, node)

            if data_objects:
                print(f"      Found {len(data_objects)} data object(s)")
                for obj in data_objects[:5]:
                    print(f"      - Data Object: {device}/{node}.{obj}")

                if len(data_objects) > 5:
                    print(f"      ... and {len(data_objects) - 5} more objects")

    print("\n" + "=" * 60)
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

    # Use context manager for automatic cleanup
    with MMSClient() as client:
        try:
            print(f"Connecting to IEC 61850 server at {hostname}:{port}")
            client.connect(hostname, port)
            print("SUCCESS: Connected to server")

            # Discover the complete data model
            discover_complete_model(client)

        except ConnectionFailedError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

        except MMSError as e:
            print(f"ERROR: MMS operation failed - {e}")
            sys.exit(1)

        except Exception as e:
            print(f"ERROR: Unexpected exception - {e}")
            sys.exit(1)

    print("\nConnection closed. Done.")


if __name__ == "__main__":
    main()
