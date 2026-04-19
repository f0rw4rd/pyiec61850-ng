#!/usr/bin/env python3
"""
Walk the IEC 61850 data model: logical devices -> nodes -> data objects.

Usage:
    python 02_device_discovery.py <host>
"""

import sys

from pyiec61850.mms import MMSClient


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)

    with MMSClient(sys.argv[1]) as client:
        for device in client.get_logical_devices():
            print(f"LD: {device}")
            for node in client.get_logical_nodes(device)[:10]:
                print(f"  LN: {node}")
                for obj in client.get_data_objects(device, node)[:5]:
                    print(f"    DO: {device}/{node}.{obj}")


if __name__ == "__main__":
    main()
