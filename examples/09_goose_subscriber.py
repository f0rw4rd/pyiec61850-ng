#!/usr/bin/env python3
"""
GOOSE Subscriber Example

Subscribe to GOOSE messages on a network interface and print received data.
Requires root/admin privileges for raw socket access.

Usage:
    sudo python 09_goose_subscriber.py <interface> <go_cb_ref> [app_id]
    sudo python 09_goose_subscriber.py eth0 simpleIOGenericIO/LLN0$GO$gcbAnalogValues
    sudo python 09_goose_subscriber.py eth0 simpleIOGenericIO/LLN0$GO$gcbAnalogValues 0x1000
"""

import sys
import time

from pyiec61850.goose import GooseSubscriber


def on_goose_message(msg):
    """Called for each received GOOSE message."""
    print(f"  stNum={msg.st_num} sqNum={msg.sq_num} valid={msg.is_valid} "
          f"values={msg.values}")


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <interface> <go_cb_ref> [app_id]")
        print(f"Example: {sys.argv[0]} eth0 simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        sys.exit(1)

    interface = sys.argv[1]
    go_cb_ref = sys.argv[2]
    app_id = int(sys.argv[3], 0) if len(sys.argv) > 3 else None

    with GooseSubscriber(interface, go_cb_ref) as sub:
        if app_id is not None:
            sub.set_app_id(app_id)
        sub.set_listener(on_goose_message)

        print(f"Subscribing to GOOSE on {interface} for {go_cb_ref}")
        sub.start()
        print("Listening for GOOSE messages (Ctrl+C to stop)...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

    print("Done.")


if __name__ == "__main__":
    main()
