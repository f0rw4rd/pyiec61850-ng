#!/usr/bin/env python3
"""
TASE.2/ICCP Client Demonstration with Mock Server

This script demonstrates all TASE.2 client functionality using a mock
connection, allowing testing without a real TASE.2 server.
"""

import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import the module first so we can patch it
import pyiec61850.tase2.client as tase2_client
from pyiec61850.tase2 import (
    TASE2Client,
    CMD_ON, CMD_OFF,
    STATE_ON, STATE_OFF,
    TAG_NONE, TAG_OPEN_AND_CLOSE_INHIBIT,
    QUALITY_GOOD,
)


def create_mock_connection():
    """Create a mock MMS connection with simulated TASE.2 server responses."""
    mock = MagicMock()
    mock.is_connected = True
    mock.state = 2  # STATE_CONNECTED
    mock.host = "192.168.1.100"
    mock.port = 102

    # Domain discovery
    mock.get_domain_names.return_value = ["VCC", "ICC1", "ICC2"]

    # Variables per domain
    def get_vars(domain):
        if domain == "VCC":
            return [
                "Bilateral_Table_ID",
                "Server_Bilateral_Table_Count",
                "Version",
            ]
        elif domain == "ICC1":
            return [
                "Voltage_A", "Voltage_B", "Voltage_C",
                "Current_A", "Current_B", "Current_C",
                "Power_Real", "Power_Reactive",
                "Frequency",
                "Breaker_Status",
                "Breaker_Control",
                "DS_TransferSet_Analog",
            ]
        else:
            return ["Status_Point1", "Control_Point1"]

    mock.get_domain_variables.side_effect = get_vars

    # Data sets
    def get_data_sets(domain):
        if domain == "ICC1":
            return ["DS_TransferSet_Analog", "DS_TransferSet_Digital"]
        return []

    mock.get_data_set_names.side_effect = get_data_sets

    # Read variable values
    def read_var(domain, name):
        values = {
            ("VCC", "Bilateral_Table_ID"): "BLT_DEMO_001",
            ("VCC", "Server_Bilateral_Table_Count"): 1,
            ("VCC", "Version"): "2000-08",
            ("ICC1", "Voltage_A"): 230.5,
            ("ICC1", "Voltage_B"): 231.2,
            ("ICC1", "Voltage_C"): 229.8,
            ("ICC1", "Current_A"): 15.3,
            ("ICC1", "Current_B"): 14.9,
            ("ICC1", "Current_C"): 15.1,
            ("ICC1", "Power_Real"): 10500.0,
            ("ICC1", "Power_Reactive"): 3200.0,
            ("ICC1", "Frequency"): 50.01,
            ("ICC1", "Breaker_Status"): 1,  # CLOSED
            ("ICC1", "Breaker_Control"): 0,
            ("ICC2", "Status_Point1"): 1,
            ("ICC2", "Control_Point1"): 0,
        }
        if (domain, name) in values:
            return values[(domain, name)]
        raise Exception(f"Variable not found: {domain}/{name}")

    mock.read_variable.side_effect = read_var

    # Write variable
    mock.write_variable.return_value = True

    # Server identity
    mock.get_server_identity.return_value = ("Demo Vendor", "TASE2-Sim", "1.0.0")

    # Data set values
    mock.read_data_set_values.return_value = [230.5, 231.2, 229.8, 15.3, 14.9, 15.1]

    # Connect/disconnect
    mock.connect.return_value = True
    mock.disconnect.return_value = None

    return mock


def main():
    """Run TASE.2 client demonstration."""
    print("=" * 70)
    print("TASE.2/ICCP Client Demonstration")
    print("=" * 70)
    print()

    # Patch the MmsConnectionWrapper
    with patch.object(tase2_client, 'MmsConnectionWrapper') as MockWrapper:
        MockWrapper.return_value = create_mock_connection()

        # Create client
        client = TASE2Client(
            local_ap_title="1.1.1.999",
            remote_ap_title="1.1.1.998"
        )

        print("[1] CONNECTING TO SERVER")
        print("-" * 40)
        client.connect("192.168.1.100", port=102)
        print(f"    Connected: {client.is_connected}")
        print(f"    Host: {client.host}:{client.port}")
        print()

        # Server Info
        print("[2] SERVER INFORMATION")
        print("-" * 40)
        info = client.get_server_info()
        print(f"    Vendor: {info.vendor}")
        print(f"    Model: {info.model}")
        print(f"    Revision: {info.revision}")
        print(f"    Bilateral Table ID: {info.bilateral_table_id}")
        print()

        # Domain Discovery
        print("[3] DOMAIN DISCOVERY")
        print("-" * 40)
        domains = client.get_domains()
        for domain in domains:
            print(f"    {domain.domain_type}: {domain.name}")
            print(f"        Variables: {len(domain.variables)}")
            print(f"        Data Sets: {len(domain.data_sets)}")
        print()

        # Read Data Points
        print("[4] READING DATA POINTS")
        print("-" * 40)
        points_to_read = [
            ("ICC1", "Voltage_A"),
            ("ICC1", "Voltage_B"),
            ("ICC1", "Voltage_C"),
            ("ICC1", "Current_A"),
            ("ICC1", "Power_Real"),
            ("ICC1", "Frequency"),
        ]

        for domain, name in points_to_read:
            pv = client.read_point(domain, name)
            unit = ""
            if "Voltage" in name:
                unit = "V"
            elif "Current" in name:
                unit = "A"
            elif "Power" in name:
                unit = "kW"
            elif "Frequency" in name:
                unit = "Hz"
            print(f"    {name}: {pv.value:.2f} {unit} (Quality: {pv.quality})")
        print()

        # Batch Read
        print("[5] BATCH READ")
        print("-" * 40)
        batch_points = [
            ("ICC1", "Voltage_A"),
            ("ICC1", "Voltage_B"),
            ("ICC1", "Voltage_C"),
        ]
        results = client.read_points(batch_points)
        print(f"    Read {len(results)} points in batch")
        for pv in results:
            print(f"        {pv.name}: {pv.value}")
        print()

        # Transfer Sets (Block 2)
        print("[6] TRANSFER SETS (Block 2)")
        print("-" * 40)
        transfer_sets = client.get_transfer_sets("ICC1")
        print(f"    Found {len(transfer_sets)} transfer sets:")
        for ts in transfer_sets:
            print(f"        - {ts.name}")

        if transfer_sets:
            print(f"    Enabling transfer set: {transfer_sets[0].name}")
            client.enable_transfer_set("ICC1", transfer_sets[0].name)
            print("    Transfer set enabled")
        print()

        # Control Operations (Block 5)
        print("[7] CONTROL OPERATIONS (Block 5)")
        print("-" * 40)

        # Select-Before-Operate
        print("    Selecting breaker for control...")
        selected = client.select_device("ICC1", "Breaker_Control")
        print(f"    Select result: {selected}")

        # Send command
        print("    Sending OPEN command...")
        result = client.send_command("ICC1", "Breaker_Control", CMD_OFF)
        print(f"    Command result: {result}")

        # Setpoint
        print("    Sending setpoint value...")
        result = client.send_setpoint_real("ICC1", "Power_Real", 11000.0)
        print(f"    Setpoint result: {result}")
        print()

        # Tagging
        print("[8] DEVICE TAGGING")
        print("-" * 40)
        print("    Setting maintenance tag on breaker...")
        tagged = client.set_tag(
            "ICC1", "Breaker_Control",
            TAG_OPEN_AND_CLOSE_INHIBIT,
            "Scheduled maintenance"
        )
        print(f"    Tag result: {tagged}")
        print()

        # Data Sets
        print("[9] DATA SETS")
        print("-" * 40)
        data_sets = client.get_data_sets("ICC1")
        print(f"    Found {len(data_sets)} data sets:")
        for ds in data_sets:
            print(f"        - {ds.name}")

        if data_sets:
            values = client.get_data_set_values("ICC1", data_sets[0].name)
            print(f"    Values in {data_sets[0].name}: {len(values)} points")
        print()

        # Security Analysis
        print("[10] SECURITY ANALYSIS")
        print("-" * 40)
        analysis = client.analyze_security()
        print(f"    Domains found: {analysis.get('domain_count', 0)}")
        print(f"    Readable points: {analysis['readable_points']}")
        print(f"    Control points: {analysis['control_points']}")
        print(f"    Transfer sets: {analysis['transfer_sets']}")
        print(f"    Access control: {analysis['access_control']}")
        print()
        print("    Conformance Blocks:")
        for block in analysis['conformance_blocks']:
            print(f"        - {block}")
        print()
        print("    Security Concerns:")
        for concern in analysis['concerns'][:3]:
            print(f"        ! {concern}")
        print()

        # Disconnect
        print("[11] DISCONNECTING")
        print("-" * 40)
        client.disconnect()
        print(f"    Connected: {client.is_connected}")
        print()

        print("=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)

        return 0


if __name__ == "__main__":
    sys.exit(main())
