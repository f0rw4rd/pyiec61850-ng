#!/usr/bin/env python3
"""
GOOSE Subscriber Example

Subscribe to GOOSE messages on a network interface and print received data.
Requires root/admin privileges for raw socket access.

Usage:
    sudo python 09_goose_subscriber.py <interface> <go_cb_ref>
"""

import sys
import time

from pyiec61850.goose import GooseSubscriber


def on_goose_message(msg):
    print(f"stNum={msg.st_num} sqNum={msg.sq_num} valid={msg.is_valid} "
          f"values={msg.values}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <interface> <go_cb_ref>")
        sys.exit(1)

    with GooseSubscriber(sys.argv[1], sys.argv[2]) as sub:
        sub.set_listener(on_goose_message)
        sub.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
