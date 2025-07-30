#!/usr/bin/env python3
"""
IEC 61850 File Transfer Example

This example demonstrates how to use the MMS file transfer capabilities
to download files from an IEC 61850 server.

Usage:
    python 04_file_transfer.py <server_ip> <remote_file> <local_file>
    python 04_file_transfer.py 192.168.1.100 "/COMTRADE/fault_001.cfg" "fault_001.cfg"
"""

import sys
import os
import pyiec61850.pyiec61850 as pyiec61850


def list_files_info():
    """
    Display information about file listing capabilities
    """
    print("\nFile Listing:")
    print("  The file listing functionality requires a specific callback handler")
    print("  implementation that is not fully exposed in the current SWIG bindings.")
    print("  ")
    print("  For production use, you would typically:")
    print("  1. Know the exact file paths you need to download")
    print("  2. Use a higher-level IEC 61850 library with complete file listing support")
    print("  3. Implement custom SWIG wrappers for the file directory callbacks")
    print("  ")
    print("  This example focuses on the file download functionality.")


def download_file(connection, remote_path, local_path):
    """
    Download a file from the IEC 61850 server
    
    Args:
        connection: Active IED connection
        remote_path: Path to file on server
        local_path: Local path to save file
    
    Returns:
        True if successful, False otherwise
    """
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
        
        # Create error object
        error = pyiec61850.MmsError_create()
        
        # Download the file using MmsConnection_downloadFile
        print("  Starting download...")
        success = pyiec61850.MmsConnection_downloadFile(
            mms_connection,
            error,
            remote_path,
            local_path
        )
        
        error_code = pyiec61850.MmsError_getValue(error)
        
        if success and error_code == 0:  # MMS_ERROR_NONE = 0
            print("  SUCCESS: File downloaded")
            
            # Check if file exists and get size
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print(f"  File saved: {local_path} ({file_size} bytes)")
            
            return True
        else:
            print(f"  ERROR: Download failed - Error code: {error_code}")
            # Remove partial file
            if os.path.exists(local_path):
                os.remove(local_path)
            return False
                
    except Exception as e:
        print(f"  ERROR: Exception during download - {e}")
        # Remove partial file
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass
        return False


def connect_to_server(hostname, port=102):
    """
    Create and establish IED connection
    
    Args:
        hostname: Server IP or hostname
        port: Port number (default 102)
    
    Returns:
        IED connection object or None
    """
    print(f"Creating IED connection to {hostname}:{port}")
    
    try:
        # Create IED connection
        connection = pyiec61850.IedConnection_create()
        
        if not connection:
            print("ERROR: Failed to create connection object")
            return None
        
        # Connect
        error = pyiec61850.IedConnection_connect(connection, hostname, port)
        
        if error == pyiec61850.IED_ERROR_OK:
            print("SUCCESS: Connection established")
            return connection
        else:
            error_msg = pyiec61850.IedClientError_toString(error)
            print(f"ERROR: Connection failed - {error_msg}")
            pyiec61850.IedConnection_destroy(connection)
            return None
            
    except Exception as e:
        print(f"ERROR: Exception creating connection - {e}")
        return None


def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [remote_file] [local_file]")
        print(f"Example 1: {sys.argv[0]} 192.168.1.100")
        print(f"Example 2: {sys.argv[0]} localhost 10102")
        print(f'Example 3: {sys.argv[0]} 192.168.1.100 102 "/COMTRADE/fault_001.cfg" "fault_001.cfg"')
        sys.exit(1)
    
    hostname = sys.argv[1]
    
    # Parse optional arguments
    port = 102
    remote_file = None
    local_file = None
    
    if len(sys.argv) > 2:
        # Check if second argument is a port number
        try:
            port = int(sys.argv[2])
            remote_file = sys.argv[3] if len(sys.argv) > 3 else None
            local_file = sys.argv[4] if len(sys.argv) > 4 else None
        except ValueError:
            # Second argument is not a number, treat as remote file
            remote_file = sys.argv[2]
            local_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # If local file not specified, use basename of remote file
    if remote_file and not local_file:
        local_file = os.path.basename(remote_file)
        if not local_file:
            local_file = "downloaded_file"
    
    # Create IED connection
    connection = connect_to_server(hostname, port)
    
    if not connection:
        print("Failed to establish connection")
        sys.exit(1)
    
    try:
        if remote_file:
            # Download specific file
            success = download_file(connection, remote_file, local_file)
            if not success:
                sys.exit(1)
        else:
            # Show info about file listing
            print("\nNo file specified for download.")
            list_files_info()
            
            # Show example usage
            print("\nExample usage:")
            print(f"  {sys.argv[0]} <server> <port> <remote_file> <local_file>")
            print(f"  {sys.argv[0]} localhost 10102 /COMTRADE/fault.cfg fault.cfg")
            print(f"  {sys.argv[0]} 192.168.1.100 102 /reports/event.rpt event.rpt")
                
    except Exception as e:
        print(f"\nERROR: Exception during file operations - {e}")
        
    finally:
        # Clean up
        print("\nClosing connection...")
        pyiec61850.IedConnection_close(connection)
        pyiec61850.IedConnection_destroy(connection)
        print("Done")


if __name__ == "__main__":
    main()