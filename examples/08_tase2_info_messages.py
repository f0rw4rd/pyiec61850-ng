#!/usr/bin/env python3
"""
TASE.2 Block 4 (Information Messages): enable IM transfer set, send and
receive messages, list files.

Usage:
    python 08_tase2_info_messages.py <host>
"""

import sys

from pyiec61850.tase2 import TASE2Client, TASE2Error


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)

    client = TASE2Client(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
    client.connect(sys.argv[1], port=102)

    client.enable_im_transfer_set("VCC")

    client.send_info_message(
        "ICC1",
        info_ref=10,
        local_ref=1,
        msg_id=50,
        content=b"operator note",
    )

    # Drain any queued messages
    while (msg := client.get_next_info_message()) is not None:
        print(f"recv info_ref={msg.info_ref} msg_id={msg.msg_id} text={msg.text!r}")

    for f in client.get_file_directory():
        print(f"file: {f['name']} ({f['size']} bytes)")

    client.disable_im_transfer_set("VCC")
    client.disconnect()


if __name__ == "__main__":
    try:
        main()
    except TASE2Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
