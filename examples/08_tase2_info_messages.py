#!/usr/bin/env python3
"""
Example 08: TASE.2 Block 4 - Information Messages

Demonstrates the Block 4 (Information Messages) API:
- Enabling/disabling the IM Transfer Set
- Sending information messages
- Receiving information messages via the queue
- Querying information buffers
- File directory operations

Uses a mock connection for demonstration without a real server.
"""

import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Import the module first so we can patch it
import pyiec61850.tase2.client as tase2_client
from pyiec61850.tase2 import (
    TASE2Client,
    InformationMessage,
    IMTransferSetConfig,
    InformationBuffer,
    BLOCK_4,
    IMTS_VAR_STATUS,
)


def create_mock_connection():
    """Create a mock MMS connection with simulated Block 4 responses."""
    mock = MagicMock()
    mock.is_connected = True
    mock.state = 2  # STATE_CONNECTED
    mock.host = "192.168.1.100"
    mock.port = 102

    # Domain discovery
    mock.get_domain_names.return_value = ["VCC", "ICC1"]
    mock.get_domain_variables.side_effect = lambda domain: {
        "VCC": [
            "Bilateral_Table_ID",
            "Supported_Features",
            "IM_Transfer_Set_Status",
        ],
        "ICC1": [
            "Voltage",
            "Current",
            "Power",
            "Information_Buffer_1",
            "InfoRef",
            "LocalRef",
            "MsgId",
            "InfoContent",
        ],
    }.get(domain, [])

    mock.get_data_set_names.return_value = []

    # Read variable responses
    def mock_read(domain, variable):
        reads = {
            ("VCC", "IM_Transfer_Set_Status"): True,
            ("VCC", "Supported_Features"): 0x1B,  # Blocks 1,2,4,5
            ("ICC1", "InfoRef"): 42,
            ("ICC1", "LocalRef"): 1,
            ("ICC1", "MsgId"): 100,
            ("ICC1", "InfoContent"): "System status: nominal",
        }
        key = (domain, variable)
        if key in reads:
            return reads[key]
        raise Exception(f"Variable not found: {domain}/{variable}")

    mock.read_variable.side_effect = mock_read

    # Write always succeeds
    mock.write_variable.return_value = True

    # File directory
    mock.get_file_directory.return_value = [
        {"name": "event_log.txt", "size": 4096, "last_modified": 0},
        {"name": "config.bin", "size": 1024, "last_modified": 0},
    ]

    # Delete file
    mock.delete_file.return_value = True

    return mock


def demo():
    """Run Block 4 demonstration."""
    print("=" * 60)
    print("TASE.2 Block 4 - Information Messages Demo")
    print("=" * 60)
    print()

    mock_conn = create_mock_connection()

    with patch.object(tase2_client, 'MmsConnectionWrapper', return_value=mock_conn):
        client = TASE2Client(
            local_ap_title="1.1.1.999",
            remote_ap_title="1.1.1.998",
        )

        # -- Data Types --
        print("--- Information Message Data Types ---")
        print()

        text_msg = InformationMessage(
            info_ref=1, local_ref=100, msg_id=1001,
            content=b"ALARM: Voltage deviation at Substation A",
            timestamp=datetime.now(tz=timezone.utc),
        )
        print(f"  Text Message:  info_ref={text_msg.info_ref}, "
              f"size={text_msg.size}B")
        print(f"    text: {text_msg.text}")
        print(f"    dict: {text_msg.to_dict()}")
        print()

        binary_msg = InformationMessage(
            info_ref=2, local_ref=200, msg_id=1002,
            content=bytes([0x01, 0x02, 0xFF, 0xFE]),
        )
        print(f"  Binary Message: info_ref={binary_msg.info_ref}, "
              f"size={binary_msg.size}B")
        print(f"    hex: {binary_msg.content.hex()}")
        print()

        config = IMTransferSetConfig(enabled=True, name="IM_TS_1")
        print(f"  IM Transfer Set Config: {config.to_dict()}")
        print()

        buf = InformationBuffer(
            name="InfoBuffer_1", domain="ICC1",
            max_size=64, entry_count=2,
            messages=[text_msg, binary_msg],
        )
        print(f"  Information Buffer: name={buf.name}, "
              f"max_size={buf.max_size}, entries={buf.entry_count}")
        print()

        # -- IM Transfer Set --
        print("--- IM Transfer Set Operations ---")
        print()

        status = client.get_im_transfer_set_status("VCC")
        print(f"  Status before: enabled={status.enabled}")

        result = client.enable_im_transfer_set("VCC")
        print(f"  Enable result: {result}")

        # -- Send Message --
        print()
        print("--- Send Information Message ---")
        print()

        result = client.send_info_message(
            "ICC1", info_ref=10, local_ref=1, msg_id=50,
            content=b"Operator note: check breaker status"
        )
        print(f"  Send result: {result}")

        # -- Receive Messages --
        print()
        print("--- Receive Information Messages ---")
        print()

        # Simulate server pushing messages into the queue
        for i in range(3):
            msg = InformationMessage(
                info_ref=i + 1, local_ref=1, msg_id=i + 100,
                content=f"Status report #{i+1}: All nominal".encode(),
                timestamp=datetime.now(tz=timezone.utc),
            )
            client._im_message_queue.put(msg)

        # Read via callback
        received = []
        client.set_im_message_callback(lambda m: received.append(m))

        while True:
            msg = client.get_next_info_message()
            if msg is None:
                break
            print(f"  Received: info_ref={msg.info_ref}, "
                  f"msg_id={msg.msg_id}, text='{msg.text}'")

        # -- Query by reference --
        print()
        print("--- Query Message by Reference ---")
        print()

        msg = client.get_info_message_by_ref("ICC1", info_ref=42)
        if msg:
            print(f"  Found: info_ref={msg.info_ref}, "
                  f"content='{msg.text}'")
        else:
            print("  Not found (expected in mock)")

        # -- Information Buffers --
        print()
        print("--- Information Buffers ---")
        print()

        buffers = client.get_info_buffers("ICC1")
        print(f"  Found {len(buffers)} buffer(s)")
        for b in buffers:
            print(f"    {b.name}: domain={b.domain}, "
                  f"max_size={b.max_size}")

        # -- File Operations --
        print()
        print("--- File Operations ---")
        print()

        files = client.get_file_directory()
        print(f"  Files on server: {len(files)}")
        for f in files:
            print(f"    {f['name']}: {f['size']} bytes")

        result = client.delete_file("old_log.txt")
        print(f"  Delete 'old_log.txt': {result}")

        # -- Disable --
        print()
        print("--- Disable IM Transfer Set ---")
        print()

        result = client.disable_im_transfer_set("VCC")
        print(f"  Disable result: {result}")
        print(f"  IM state: enabled={client._im_transfer_set_enabled}")

    print()
    print("=" * 60)
    print("Block 4 demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
