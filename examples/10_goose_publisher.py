#!/usr/bin/env python3
"""
GOOSE Publisher Example

Publish GOOSE messages on a network interface.
Requires root/admin privileges for raw socket access.

Usage:
    sudo python 10_goose_publisher.py <interface>
    sudo python 10_goose_publisher.py eth0
"""

import sys
import time

from pyiec61850.goose import GoosePublisher


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <interface>")
        print(f"Example: {sys.argv[0]} eth0")
        sys.exit(1)

    interface = sys.argv[1]

    with GoosePublisher(interface) as pub:
        pub.set_go_cb_ref("simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        pub.set_app_id(0x1000)
        pub.set_conf_rev(1)
        pub.set_time_allowed_to_live(2000)

        print(f"Starting GOOSE publisher on {interface}")
        pub.start()

        print("Publishing GOOSE messages (Ctrl+C to stop)...")
        try:
            counter = 0
            while True:
                values = [True, counter, 3.14 * counter, "status_ok"]
                pub.publish(values)
                print(f"  Published: {values}")

                # Increment state number when values change
                counter += 1
                pub.increase_st_num()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

    print("Done.")


if __name__ == "__main__":
    main()
