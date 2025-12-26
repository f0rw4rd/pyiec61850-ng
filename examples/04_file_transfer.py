#!/usr/bin/env python3
"""
IEC 61850 File Transfer Example

This example demonstrates how to use the MMS file transfer capabilities
to download files from an IEC 61850 server.

Note: File transfer uses the raw pyiec61850 bindings with safe cleanup
utilities, as this functionality is not yet wrapped in MMSClient.

Usage:
    python 04_file_transfer.py <server_ip> <remote_file> <local_file>
    python 04_file_transfer.py 192.168.1.100 "/COMTRADE/fault_001.cfg" "fault_001.cfg"
"""

import sys
import os

# Try to import raw bindings for file transfer (not yet in MMSClient)
try:
    import pyiec61850.pyiec61850 as pyiec61850
    _HAS_RAW_BINDINGS = True
except ImportError:
    _HAS_RAW_BINDINGS = False

# Import safe utilities for cleanup
from pyiec61850.mms import (
    MMSClient,
    ConnectionFailedError,
    MMSError,
)
from pyiec61850.mms.utils import (
    safe_mms_error_destroy,
    MmsErrorGuard,
)


def list_files_info():
    """Display information about file listing capabilities."""
    print("\nFile Listing:")
    print("  The file listing functionality requires a specific callback handler")
    print("  implementation that is not fully exposed in the current SWIG bindings.")
    print()
    print("  For production use, you would typically:")
    print("  1. Know the exact file paths you need to download")
    print("  2. Use a higher-level IEC 61850 library with complete file listing support")
    print()
    print("  This example focuses on the file download functionality.")


def download_file_raw(connection, remote_path, local_path):
    """
    Download a file using raw pyiec61850 bindings with safe cleanup.

    This function demonstrates how to use MmsErrorGuard for safe
    memory management when using raw bindings.

    Args:
        connection: Active IED connection (raw)
        remote_path: Path to file on server
        local_path: Local path to save file

    Returns:
        True if successful, False otherwise
    """
    if not _HAS_RAW_BINDINGS:
        print("  ERROR: Raw pyiec61850 bindings not available")
        return False

    print(f"\nDownloading file:")
    print(f"  Remote: {remote_path}")
    print(f"  Local:  {local_path}")

    try:
        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir)
            print(f"  Created local directory: {local_dir}")

        # Get MMS connection from IED connection
        mms_connection = pyiec61850.IedConnection_getMmsConnection(connection)
        if not mms_connection:
            print("  ERROR: Failed to get MMS connection")
            return False

        # Create error object with safe cleanup using MmsErrorGuard
        # This ensures the error object is properly destroyed even if
        # an exception occurs (fixes Issue #1 from stability analysis)
        if hasattr(pyiec61850, 'MmsError_create'):
            error = pyiec61850.MmsError_create()

            # Use context manager for automatic cleanup
            with MmsErrorGuard(error):
                print("  Starting download...")
                success = pyiec61850.MmsConnection_downloadFile(
                    mms_connection,
                    error,
                    remote_path,
                    local_path
                )

                error_code = pyiec61850.MmsError_getValue(error) if hasattr(pyiec61850, 'MmsError_getValue') else 0

                if success and error_code == 0:
                    print("  SUCCESS: File downloaded")

                    if os.path.exists(local_path):
                        file_size = os.path.getsize(local_path)
                        print(f"  File saved: {local_path} ({file_size} bytes)")

                    return True
                else:
                    print(f"  ERROR: Download failed - Error code: {error_code}")
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    return False
        else:
            print("  ERROR: MmsError_create not available in bindings")
            return False

    except Exception as e:
        print(f"  ERROR: Exception during download - {e}")
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
        return False


def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [remote_file] [local_file]")
        print(f"Example 1: {sys.argv[0]} 192.168.1.100")
        print(f"Example 2: {sys.argv[0]} localhost 10102")
        print(f'Example 3: {sys.argv[0]} 192.168.1.100 102 "/COMTRADE/fault.cfg" "fault.cfg"')
        sys.exit(1)

    hostname = sys.argv[1]

    # Parse optional arguments
    port = 102
    remote_file = None
    local_file = None

    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
            remote_file = sys.argv[3] if len(sys.argv) > 3 else None
            local_file = sys.argv[4] if len(sys.argv) > 4 else None
        except ValueError:
            remote_file = sys.argv[2]
            local_file = sys.argv[3] if len(sys.argv) > 3 else None

    if remote_file and not local_file:
        local_file = os.path.basename(remote_file) or "downloaded_file"

    # For file transfer, we need the raw connection
    # MMSClient doesn't expose file transfer yet
    if not _HAS_RAW_BINDINGS:
        print("ERROR: pyiec61850 raw bindings not available")
        print("       File transfer requires the C library bindings.")
        print("       Build with: ./build.sh")
        sys.exit(1)

    print(f"Connecting to IEC 61850 server at {hostname}:{port}")

    connection = pyiec61850.IedConnection_create()
    if not connection:
        print("ERROR: Failed to create connection object")
        sys.exit(1)

    try:
        error = pyiec61850.IedConnection_connect(connection, hostname, port)

        if error != pyiec61850.IED_ERROR_OK:
            error_msg = pyiec61850.IedClientError_toString(error)
            print(f"ERROR: Connection failed - {error_msg}")
            sys.exit(1)

        print("SUCCESS: Connected to server")

        if remote_file:
            success = download_file_raw(connection, remote_file, local_file)
            if not success:
                sys.exit(1)
        else:
            print("\nNo file specified for download.")
            list_files_info()

            print("\nExample usage:")
            print(f"  {sys.argv[0]} <server> <port> <remote_file> <local_file>")
            print(f"  {sys.argv[0]} localhost 10102 /COMTRADE/fault.cfg fault.cfg")

    finally:
        print("\nClosing connection...")
        pyiec61850.IedConnection_close(connection)
        pyiec61850.IedConnection_destroy(connection)
        print("Done")


if __name__ == "__main__":
    main()
