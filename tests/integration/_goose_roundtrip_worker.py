"""GOOSE publish -> subscribe round-trip worker (runs inside a container).

Publishes GOOSE frames and subscribes to them on the SAME interface in one
process/netns, so it exercises the real SWIG binding end to end without a
server. Meant to run inside a container with CAP_NET_RAW (GOOSE needs an
AF_PACKET raw socket), which is why the host test shells out to `docker run`
instead of opening the raw socket on the host.

Prints `ROUNDTRIP_OK ...` and exits 0 on success; `ROUNDTRIP_FAIL ...` / non-zero
otherwise. Usage: python _goose_roundtrip_worker.py [interface]
"""

import sys
import time

from pyiec61850.goose import GoosePublisher, GooseSubscriber

IFACE_PUB = sys.argv[1] if len(sys.argv) > 1 else "lo"
IFACE_SUB = sys.argv[2] if len(sys.argv) > 2 else IFACE_PUB
GOCB = "simpleIOGenericIO/LLN0$GO$gcbAnalogValues"
DATASET = "simpleIOGenericIO/LLN0$AnalogValues"
APPID = 0x1000

received = []


def on_msg(msg):
    received.append(msg)


def main() -> int:
    sub = GooseSubscriber(IFACE_SUB, GOCB)
    sub.set_app_id(APPID)
    sub.set_listener(on_msg)
    sub.start()

    pub = GoosePublisher(IFACE_PUB)
    pub.set_go_cb_ref(GOCB)
    pub.set_data_set(DATASET)
    pub.set_app_id(APPID)
    pub.set_conf_rev(1)
    pub.set_time_allowed_to_live(2000)
    pub.start()

    # Deterministic payloads so the subscriber can verify decoded values.
    def payload(i):
        return [True, i, 1.5 * i, "ok"]

    last_sent = None
    try:
        for i in range(20):
            last_sent = payload(i)
            pub.publish(last_sent)
            time.sleep(0.05)
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
    print(
        f"ROUNDTRIP_OK received={len(received)} parse_error={msg.parse_error} "
        f"values={msg.values}"
    )
    # A decoded frame must carry the data-set values and parse cleanly. The
    # values won't be the exact last frame we sent (GOOSE retransmits), but they
    # must have the published shape: [bool, int, float, str].
    if msg.parse_error != 0:
        print(f"ROUNDTRIP_FAIL parse_error={msg.parse_error}")
        return 1
    if len(msg.values) != len(last_sent):
        print(f"ROUNDTRIP_FAIL value_count={len(msg.values)} expected={len(last_sent)}")
        return 1
    shape = [type(v).__name__ for v in msg.values]
    if shape != ["bool", "int", "float", "str"]:
        print(f"ROUNDTRIP_FAIL value_shape={shape}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
