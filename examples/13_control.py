#!/usr/bin/env python3
"""
Direct Operate and Select-Before-Operate control.

Usage:
    python 13_control.py <host> <object_ref>
"""

import sys

from pyiec61850.mms import ControlClient, MMSClient, OperateError, SelectError


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <object_ref>")
        sys.exit(1)

    host, ref = sys.argv[1], sys.argv[2]
    with MMSClient(host) as client:
        ctrl = ControlClient(client)
        print(f"control model: {ctrl.get_control_model(ref)}")

        try:
            ctrl.direct_operate(ref, True)
            print("direct operate: ok")
        except OperateError as e:
            print(f"direct operate: {e}")

        try:
            ctrl.select(ref)
            ctrl.operate(ref, False)
            print("SBO: ok")
        except (SelectError, OperateError) as e:
            print(f"SBO: {e}")

        ctrl.release_all()


if __name__ == "__main__":
    main()
