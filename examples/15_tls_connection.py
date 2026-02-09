#!/usr/bin/env python3
"""
TLS Connection Example

Connect to an IEC 61850 server over TLS using certificate-based
authentication.

Usage:
    python 15_tls_connection.py <server_ip> <cert> <key> <ca_cert> [port]
    python 15_tls_connection.py 192.168.1.100 client.pem client-key.pem ca.pem
    python 15_tls_connection.py 192.168.1.100 client.pem client-key.pem ca.pem 3782
"""

import sys

from pyiec61850.mms.tls import TLSConfig, create_tls_configuration, destroy_tls_configuration

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_RAW = True
except ImportError:
    _HAS_RAW = False


def main():
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} <server_ip> <cert> <key> <ca_cert> [port]")
        print(f"Example: {sys.argv[0]} 192.168.1.100 client.pem client-key.pem ca.pem")
        sys.exit(1)

    hostname = sys.argv[1]
    cert_path = sys.argv[2]
    key_path = sys.argv[3]
    ca_path = sys.argv[4]
    port = int(sys.argv[5]) if len(sys.argv) > 5 else 3782

    if not _HAS_RAW:
        print("ERROR: pyiec61850 C bindings not available. Build with: ./build.sh")
        sys.exit(1)

    tls = TLSConfig(
        own_cert=cert_path,
        own_key=key_path,
        ca_certs=[ca_path],
        chain_validation=True,
    )

    print(f"Creating TLS configuration...")
    tls_config = create_tls_configuration(tls)

    try:
        conn = iec61850.IedConnection_createWithTlsSupport(tls_config)
        error = iec61850.IedConnection_connect(conn, hostname, port)

        if error != iec61850.IED_ERROR_OK:
            print(f"ERROR: TLS connection failed (error {error})")
            sys.exit(1)

        print(f"Connected to {hostname}:{port} with TLS")

        # Discover logical devices
        devices = iec61850.IedConnection_getLogicalDeviceList(conn)
        print(f"Logical devices found: {devices}")

        iec61850.IedConnection_close(conn)
        iec61850.IedConnection_destroy(conn)
        print("Connection closed.")

    finally:
        destroy_tls_configuration(tls_config)

    print("Done.")


if __name__ == "__main__":
    main()
