#!/usr/bin/env python3
"""
IEC 61850 Data Reading Example

This example demonstrates how to read different types of data values from
an IEC 61850 server using the safe MMSClient wrapper.

The client handles MmsValue memory management automatically, preventing
memory leaks and use-after-free crashes.

Usage:
    python 03_read_data_values.py <server_ip> <object_reference>
    python 03_read_data_values.py 192.168.1.100 "TEMPLATE1LD0/MMXU1.TotW.mag.f"
"""

import sys

from pyiec61850.mms import (
    MMSClient,
    ConnectionFailedError,
    ReadError,
    MMSError,
)


def read_and_display(client, object_reference):
    """
    Read a data object and display its value.

    The MMSClient.read_value() method handles MmsValue cleanup
    automatically using MmsValueGuard.

    Args:
        client: Connected MMSClient instance
        object_reference: Full reference to the data object

    Returns:
        The value read, or None if failed
    """
    print(f"\nReading: {object_reference}")

    try:
        value = client.read_value(object_reference)
        print(f"  Value: {value}")
        return value

    except ReadError as e:
        print(f"  Failed: {e}")
        return None


def discover_and_read(client):
    """
    Discover devices and read sample values from each.

    Args:
        client: Connected MMSClient instance
    """
    print("\n" + "=" * 60)
    print("DISCOVERING AND READING DATA VALUES")
    print("=" * 60)

    # Get logical devices
    devices = client.get_logical_devices()
    if not devices:
        print("No logical devices found!")
        return

    print(f"\nFound {len(devices)} device(s)")

    # For each device, try to read some values
    for device in devices[:2]:  # Limit to first 2 devices
        print(f"\n--- Device: {device} ---")

        # Get logical nodes
        nodes = client.get_logical_nodes(device)
        if not nodes:
            print("  No logical nodes found")
            continue

        # For each node, get data objects and try reading
        for node in nodes[:3]:  # Limit to first 3 nodes
            data_objects = client.get_data_objects(device, node)

            for obj in data_objects[:3]:  # Limit to first 3 objects
                reference = f"{device}/{node}.{obj}"
                read_and_display(client, reference)


def read_specific_objects(client, references):
    """
    Read specific object references.

    Args:
        client: Connected MMSClient instance
        references: List of object references to read
    """
    print("\n" + "=" * 60)
    print("READING SPECIFIC DATA OBJECTS")
    print("=" * 60)

    successful = 0
    failed = 0

    for ref in references:
        value = read_and_display(client, ref)
        if value is not None:
            successful += 1
        else:
            failed += 1

    print(f"\nSummary: {successful} successful, {failed} failed")


def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [object_reference...]")
        print(f"Example 1: {sys.argv[0]} 192.168.1.100")
        print(f"Example 2: {sys.argv[0]} localhost 10102")
        print(f'Example 3: {sys.argv[0]} 192.168.1.100 102 "LD0/MMXU1.TotW"')
        sys.exit(1)

    hostname = sys.argv[1]

    # Parse optional port and object references
    port = 102
    specific_objects = []

    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
            specific_objects = sys.argv[3:]
        except ValueError:
            # Second argument is not a port, treat as object reference
            specific_objects = sys.argv[2:]

    # Connect and read
    with MMSClient() as client:
        try:
            print(f"Connecting to IEC 61850 server at {hostname}:{port}")
            client.connect(hostname, port)
            print("SUCCESS: Connected to server")

            if specific_objects:
                # Read specific objects provided by user
                read_specific_objects(client, specific_objects)
            else:
                # Discover and read sample values
                discover_and_read(client)

        except ConnectionFailedError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

        except MMSError as e:
            print(f"ERROR: MMS operation failed - {e}")
            sys.exit(1)

    print("\nConnection closed. Done.")


if __name__ == "__main__":
    main()
