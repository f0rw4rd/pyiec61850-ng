#!/usr/bin/env python3
"""
Download a file from an IEC 61850 server via MMS file transfer.

Usage:
    python 04_file_transfer.py <host> <remote_path> <local_path>
"""

import os
import sys

from pyiec61850.mms import MMSClient, MMSError


def main() -> None:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host> <remote_path> <local_path>")
        sys.exit(1)

    host, remote_path, local_path = sys.argv[1:]
    with MMSClient(host) as client:
        client.download_file(remote_path, local_path)
    print(f"Downloaded {remote_path} -> {local_path} ({os.path.getsize(local_path)} bytes)")


if __name__ == "__main__":
    try:
        main()
    except MMSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
