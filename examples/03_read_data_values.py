#!/usr/bin/env python3
"""
Read one or more data values from an IEC 61850 server.

Usage:
    python 03_read_data_values.py <host> <ref> [ref ...]
"""

import sys

from pyiec61850.mms import MMSClient, ReadError


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <host> <ref> [ref ...]")
        sys.exit(1)

    host, *refs = sys.argv[1:]
    with MMSClient(host) as client:
        for ref in refs:
            try:
                print(f"{ref} = {client.read_value(ref)!r}")
            except ReadError as e:
                print(f"{ref}: FAILED ({e})")


if __name__ == "__main__":
    main()
