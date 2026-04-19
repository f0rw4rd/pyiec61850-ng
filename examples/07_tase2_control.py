#!/usr/bin/env python3
"""
TASE.2 Select-Before-Operate control and device tagging.

Usage:
    python 07_tase2_control.py <host> <domain> <device>
"""

import sys

from pyiec61850.tase2 import CMD_OFF, CMD_ON, TAG_NONE, TAG_OPEN_AND_CLOSE_INHIBIT, TASE2Client


def main() -> None:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host> <domain> <device>")
        sys.exit(1)

    host, domain, device = sys.argv[1:]

    client = TASE2Client(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
    client.connect(host, port=102)

    # Read current status
    pv = client.read_point(domain, device)
    print(f"{device} status: {pv.value}")

    # Select-Before-Operate
    client.select_device(domain, device)
    client.operate_device(domain, device, CMD_OFF)
    print(f"{device} commanded OFF")

    # Tag the device, then clear
    client.set_tag(domain, device, TAG_OPEN_AND_CLOSE_INHIBIT, "maintenance")
    print(f"{device} tagged")
    client.set_tag(domain, device, TAG_NONE)
    print(f"{device} tag cleared")

    client.disconnect()


if __name__ == "__main__":
    main()
