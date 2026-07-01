#!/usr/bin/env python3
"""Worker: publish + subscribe IEC 61850-9-2 Sampled Values on one interface.

Runs inside the NET_RAW container started by test_sv_roundtrip.py. Publishes
INT32 sample sets and subscribes to them on the same netns (``lo``), then prints
``ROUNDTRIP_OK`` with the decoded values when the subscriber's callback fires.

libiec61850's default SV APPID (used when SVPublisher_create gets NULL comm
parameters) is 0x4000, so the subscriber filters on 0x4000 to match.
"""

import sys
import time

from pyiec61850.sv import SVPublisher, SVSubscriber

IFACE = "lo"
APPID = 0x4000  # libiec61850 default SV APPID
SVID = "svRoundTrip"
N_ENTRIES = 4

received = []


def on_msg(msg):
    received.append(msg)


def main() -> int:
    sub = SVSubscriber(IFACE)
    sub.set_app_id(APPID)
    sub.set_listener(on_msg)
    sub.start()

    pub = SVPublisher(IFACE)
    pub.set_sv_id(SVID)
    pub.set_app_id(APPID)
    pub.set_conf_rev(1)
    pub.set_smp_rate(4000)
    pub.set_num_entries(N_ENTRIES)
    pub.start()

    def payload(i):
        return [i, i + 1, i + 2, i + 3]

    last_sent = None
    try:
        for i in range(50):
            last_sent = payload(i)
            pub.publish_samples(last_sent)
            time.sleep(0.02)
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and not received:
            time.sleep(0.1)
    finally:
        try:
            pub.stop()
        finally:
            sub.stop()

    if not received:
        print("ROUNDTRIP_FAIL received=0")
        return 1

    msg = received[-1]
    print(f"ROUNDTRIP_OK received={len(received)} smp_cnt={msg.smp_cnt} values={msg.values}")
    if len(msg.values) != len(last_sent):
        print(f"ROUNDTRIP_FAIL value_count={len(msg.values)} expected={len(last_sent)}")
        return 1
    if not all(isinstance(v, int) for v in msg.values):
        print(f"ROUNDTRIP_FAIL value_types={[type(v).__name__ for v in msg.values]}")
        return 1
    # Every payload is a consecutive run [v, v+1, v+2, v+3]; a faithful decode
    # must reproduce that shape (catches byte-offset / endianness regressions).
    v0 = msg.values[0]
    if msg.values != [v0 + k for k in range(len(msg.values))]:
        print(f"ROUNDTRIP_FAIL values_not_consecutive={msg.values}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
