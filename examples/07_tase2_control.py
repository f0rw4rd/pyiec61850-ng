#!/usr/bin/env python3
"""
TASE.2/ICCP SBO Control with CheckBack Demonstration

Demonstrates Select-Before-Operate control with CheckBack ID:
1. Read device status
2. Select device (SBO) - captures CheckBack ID
3. Verify selection
4. Operate device (echoes CheckBack ID)
5. Verify operation result
"""

import sys
from unittest.mock import MagicMock, patch

import pyiec61850.tase2.client as tase2_client
from pyiec61850.tase2 import (
    TASE2Client,
    CMD_ON, CMD_OFF,
    TAG_NONE, TAG_OPEN_AND_CLOSE_INHIBIT,
    SBOState,
)


def create_mock_connection():
    """Create a mock connection with control support."""
    mock = MagicMock()
    mock.is_connected = True
    mock.state = 2
    mock.host = "192.168.1.100"
    mock.port = 102
    mock.register_state_callback = MagicMock()

    mock.get_domain_names.return_value = ["VCC", "ICC1"]
    mock.get_domain_variables.return_value = [
        "Breaker_A", "Breaker_A_SBO", "Breaker_A_TAG",
        "Breaker_B", "Breaker_B_SBO", "Breaker_B_TAG",
        "VoltageSetpoint", "VoltageSetpoint_SBO",
    ]
    mock.get_data_set_names.return_value = []

    checkback_counter = [0]

    def read_var(domain, name):
        values = {
            ("ICC1", "Breaker_A"): 1,  # CLOSED
            ("ICC1", "Breaker_A_SBO"): checkback_counter[0],
            ("ICC1", "Breaker_B"): 0,  # OPEN
            ("ICC1", "Breaker_B_SBO"): checkback_counter[0],
            ("ICC1", "VoltageSetpoint"): 115.0,
            ("ICC1", "VoltageSetpoint_SBO"): checkback_counter[0],
        }
        if (domain, name) in values:
            return values[(domain, name)]
        raise Exception(f"Not found: {domain}/{name}")

    def write_var(domain, name, value):
        if "_SBO" in name:
            checkback_counter[0] += 1
        return True

    mock.read_variable.side_effect = read_var
    mock.write_variable.side_effect = write_var
    mock.connect.return_value = True
    mock.get_server_identity.return_value = ("Demo", "TASE2-Sim", "2.0")

    return mock


def main():
    print("=" * 70)
    print("TASE.2 SBO Control with CheckBack Demo")
    print("=" * 70)
    print()

    with patch.object(tase2_client, 'MmsConnectionWrapper') as MockWrapper:
        MockWrapper.return_value = create_mock_connection()

        client = TASE2Client(
            local_ap_title="1.1.1.999",
            remote_ap_title="1.1.1.998"
        )
        client.connect("192.168.1.100", port=102)
        print("[*] Connected to server")
        print()

        # ---- Command Control (Binary) ----
        print("[1] COMMAND CONTROL - Breaker A")
        print("-" * 40)

        # Read current status
        pv = client.read_point("ICC1", "Breaker_A")
        status = "CLOSED" if pv.value == 1 else "OPEN"
        print(f"    Current status: {status} ({pv.value})")

        # Select
        print("    Selecting Breaker_A for control...")
        result = client.select_device("ICC1", "Breaker_A")
        print(f"    Select result: {result}")

        # Show SBO state
        sbo = client._sbo_states.get("ICC1/Breaker_A")
        if sbo:
            print(f"    CheckBack ID: {sbo.checkback_id}")
            print(f"    Select time: {sbo.select_time:.1f}")

        # Operate - send OPEN command
        print("    Operating: sending OPEN command...")
        result = client.operate_device("ICC1", "Breaker_A", CMD_OFF)
        print(f"    Operate result: {result}")
        print(f"    SBO state cleared: {'ICC1/Breaker_A' not in client._sbo_states}")
        print()

        # ---- Setpoint Control ----
        print("[2] SETPOINT CONTROL - Voltage")
        print("-" * 40)

        pv = client.read_point("ICC1", "VoltageSetpoint")
        print(f"    Current setpoint: {pv.value}")

        print("    Selecting VoltageSetpoint...")
        client.select_device("ICC1", "VoltageSetpoint")

        sbo = client._sbo_states.get("ICC1/VoltageSetpoint")
        if sbo:
            print(f"    CheckBack ID: {sbo.checkback_id}")

        print("    Setting voltage to 120.0...")
        client.send_setpoint_real("ICC1", "VoltageSetpoint", 120.0)
        print("    Setpoint written successfully")
        print()

        # ---- Device Tagging ----
        print("[3] DEVICE TAGGING")
        print("-" * 40)

        print("    Setting INHIBIT tag on Breaker_B...")
        client.set_tag(
            "ICC1", "Breaker_B",
            TAG_OPEN_AND_CLOSE_INHIBIT,
            "Scheduled maintenance"
        )
        print("    Tag set: OPEN_AND_CLOSE_INHIBIT")

        print("    Removing tag from Breaker_B...")
        client.set_tag("ICC1", "Breaker_B", TAG_NONE)
        print("    Tag removed")
        print()

        # ---- SBO Timeout ----
        print("[4] SBO TIMEOUT HANDLING")
        print("-" * 40)
        import time
        print("    Selecting Breaker_B...")
        client.select_device("ICC1", "Breaker_B")
        print("    Simulating timeout (setting select time 31s ago)...")
        client._sbo_select_times["ICC1/Breaker_B"] = time.time() - 31

        try:
            client.operate_device("ICC1", "Breaker_B", CMD_ON)
        except Exception as e:
            print(f"    Expected error: {e}")
        print()

        client.disconnect()
        print("[*] Disconnected")
        print()
        print("=" * 70)
        print("CONTROL DEMO COMPLETE")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
