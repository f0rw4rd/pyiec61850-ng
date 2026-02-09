#!/usr/bin/env python3
"""
IEC 61850 Control Operations Example

Demonstrates Direct Operate and Select-Before-Operate (SBO) patterns.

Usage:
    python 13_control.py <server_ip> [port] [object_ref]
    python 13_control.py localhost 10102 simpleIOGenericIO/CSWI1.Pos
"""

import sys

from pyiec61850.mms import (
    MMSClient, ConnectionFailedError,
    ControlClient, ControlError, SelectError, OperateError,
)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [object_ref]")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102
    object_ref = sys.argv[3] if len(sys.argv) > 3 else "simpleIOGenericIO/CSWI1.Pos"

    with MMSClient() as client:
        try:
            print(f"Connecting to {hostname}:{port}")
            client.connect(hostname, port)

            ctrl = ControlClient(client)
            model = ctrl.get_control_model(object_ref)
            print(f"Control model for {object_ref}: {model}")

            # Direct operate
            print(f"\nDirect operate: {object_ref} = True")
            try:
                ctrl.direct_operate(object_ref, True)
                print("  SUCCESS")
            except OperateError as e:
                print(f"  {e}")

            # Select-before-operate
            print(f"\nSBO: select {object_ref}")
            try:
                ctrl.select(object_ref)
                print("  Selected.")
                ctrl.operate(object_ref, False)
                print("  Operated: False")
            except (SelectError, OperateError) as e:
                print(f"  {e}")

            ctrl.release_all()

        except (ConnectionFailedError, ControlError) as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
