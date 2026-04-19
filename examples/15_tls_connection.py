#!/usr/bin/env python3
"""
Connect to an IEC 61850 server over TLS using certificate-based auth.

Usage:
    python 15_tls_connection.py <host> <cert> <key> <ca_cert>
"""

import sys

from pyiec61850.mms import MMSClient, TLSConfig


def main() -> None:
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <host> <cert> <key> <ca_cert>")
        sys.exit(1)

    host, cert, key, ca = sys.argv[1:]
    tls = TLSConfig(own_cert=cert, own_key=key, ca_certs=[ca])

    with MMSClient(host, tls=tls) as client:
        for device in client.get_logical_devices():
            print(device)


if __name__ == "__main__":
    main()
