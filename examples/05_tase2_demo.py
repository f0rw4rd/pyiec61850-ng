#!/usr/bin/env python3
"""
TASE.2/ICCP client walkthrough: connect, discover, read, control, disconnect.

Usage:
    python 05_tase2_demo.py <host>
"""

import sys

from pyiec61850.tase2 import TASE2Client, TASE2Error


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)

    client = TASE2Client(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
    client.connect(sys.argv[1], port=102)

    info = client.get_server_info()
    print(f"Server: {info.vendor} / {info.model} / {info.revision}")

    for domain in client.get_domains():
        print(
            f"  {domain.domain_type}: {domain.name} "
            f"({len(domain.variables)} vars, {len(domain.data_sets)} ds)"
        )

    # Read a couple of points (adjust names to match your server's model)
    for d, n in [("ICC1", "Voltage_A"), ("ICC1", "Power_Real")]:
        try:
            pv = client.read_point(d, n)
            print(f"  {n} = {pv.value} (q={pv.quality})")
        except Exception as e:
            print(f"  {n}: {e}")

    # Control / tagging — uncomment and adjust for your server
    # client.select_device("ICC1", "Breaker_Control")
    # client.send_command("ICC1", "Breaker_Control", CMD_OFF)
    # client.send_setpoint_real("ICC1", "Power_Real", 11000.0)
    # client.set_tag("ICC1", "Breaker_Control", TAG_OPEN_AND_CLOSE_INHIBIT, "maint")

    analysis = client.analyze_security()
    print(f"Security: {analysis['readable_points']} readable, {analysis['control_points']} control")

    client.disconnect()


if __name__ == "__main__":
    try:
        main()
    except TASE2Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
