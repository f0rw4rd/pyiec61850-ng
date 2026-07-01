#!/usr/bin/env python3
"""
Sampled Values (IEC 61850-9-2) Example

Subscribe to Sampled Value streams on a network interface.
Requires root/admin privileges for raw socket access.

Usage:
    sudo python 11_sampled_values.py <interface>
"""

import sys
import time

from pyiec61850.sv import SVError, SVSubscriber


def on_sample(msg):
    print(f"smpCnt={msg.smp_cnt} confRev={msg.conf_rev} values={msg.values[:4]}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <interface>")
        sys.exit(1)

    with SVSubscriber(sys.argv[1]) as sub:
        sub.set_listener(on_sample)
        sub.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    try:
        main()
    except SVError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
