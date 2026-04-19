#!/usr/bin/env python3
"""
Basic connection to an IEC 61850 server.

Usage:
    python 01_basic_connection.py <host>
"""

import sys

from pyiec61850.mms import MMSClient


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)

    with MMSClient(sys.argv[1]) as client:
        identity = client.get_server_identity()
        print(f"Vendor:   {identity.vendor}")
        print(f"Model:    {identity.model}")
        print(f"Revision: {identity.revision}")


if __name__ == "__main__":
    main()
