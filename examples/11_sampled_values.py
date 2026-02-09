#!/usr/bin/env python3
"""
Sampled Values (IEC 61850-9-2) Example

Subscribe to Sampled Value streams on a network interface.
Requires root/admin privileges for raw socket access.

Usage:
    sudo python 11_sampled_values.py <interface> [app_id]
    sudo python 11_sampled_values.py eth0
    sudo python 11_sampled_values.py eth0 0x4000
"""

import sys
import time

from pyiec61850.sv import SVSubscriber


def on_sample(msg):
    """Called for each received SV message."""
    print(f"  smpCnt={msg.smp_cnt} confRev={msg.conf_rev} "
          f"values={msg.values[:4]}...")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <interface> [app_id]")
        print(f"Example: {sys.argv[0]} eth0 0x4000")
        sys.exit(1)

    interface = sys.argv[1]
    app_id = int(sys.argv[2], 0) if len(sys.argv) > 2 else None

    with SVSubscriber(interface) as sub:
        if app_id is not None:
            sub.set_app_id(app_id)
        sub.set_listener(on_sample)

        print(f"Subscribing to Sampled Values on {interface}")
        sub.start()
        print("Listening for SV streams (Ctrl+C to stop)...")

        try:
            while True:
                # Poll current values
                msg = sub.read_current_values()
                if msg.smp_cnt > 0:
                    print(f"  [poll] smpCnt={msg.smp_cnt} values={msg.values[:4]}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

    print("Done.")


if __name__ == "__main__":
    main()
