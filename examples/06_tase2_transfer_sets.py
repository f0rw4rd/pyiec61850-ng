#!/usr/bin/env python3
"""
TASE.2/ICCP Transfer Set Lifecycle Demonstration

Demonstrates the full transfer set lifecycle:
1. Create a data set
2. Configure a DS Transfer Set
3. Start receiving reports
4. Enable the transfer set
5. Receive and process reports
6. Send Transfer Report ACK
7. Disable the transfer set
8. Stop receiving reports
9. Delete the data set
"""

import sys
import time
from unittest.mock import MagicMock, patch

import pyiec61850.tase2.client as tase2_client
from pyiec61850.tase2 import (
    TASE2Client,
    DSTransferSetConfig,
    TransferSetConditions,
    TransferReport,
    PointValue,
    QUALITY_GOOD,
)


def create_mock_connection():
    """Create a mock connection with transfer set support."""
    mock = MagicMock()
    mock.is_connected = True
    mock.state = 2
    mock.host = "192.168.1.100"
    mock.port = 102
    mock.register_state_callback = MagicMock()

    mock.get_domain_names.return_value = ["VCC", "ICC1"]
    mock.get_domain_variables.return_value = [
        "Voltage_A", "Voltage_B", "Voltage_C",
        "Frequency", "Power_Real",
    ]
    mock.get_data_set_names.return_value = []

    def read_var(domain, name):
        values = {
            ("ICC1", "Voltage_A"): 230.5,
            ("ICC1", "Voltage_B"): 231.0,
            ("ICC1", "Voltage_C"): 229.8,
            ("ICC1", "Frequency"): 50.01,
            ("ICC1", "Power_Real"): 10500.0,
        }
        if (domain, name) in values:
            return values[(domain, name)]
        raise Exception(f"Not found: {domain}/{name}")

    mock.read_variable.side_effect = read_var
    mock.write_variable.return_value = True
    mock.create_data_set.return_value = True
    mock.delete_data_set.return_value = True
    mock.connect.return_value = True
    mock.get_server_identity.return_value = ("Demo", "TASE2-Sim", "2.0")

    return mock


def main():
    print("=" * 70)
    print("TASE.2 Transfer Set Lifecycle Demo")
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

        # Step 1: Create data set
        print("[1] CREATING DATA SET")
        print("-" * 40)
        members = ["Voltage_A", "Voltage_B", "Voltage_C", "Frequency"]
        client.create_data_set("ICC1", "MyAnalogDS", members)
        print(f"    Created data set 'MyAnalogDS' with {len(members)} members:")
        for m in members:
            print(f"      - {m}")
        print()

        # Step 2: Configure transfer set
        print("[2] CONFIGURING TRANSFER SET")
        print("-" * 40)
        config = DSTransferSetConfig(
            data_set_name="MyAnalogDS",
            interval=10,
            integrity_check=60,
            buffer_time=2,
            rbe=True,
            ds_conditions=TransferSetConditions(
                interval_timeout=True,
                object_change=True,
                integrity_timeout=True,
            ),
        )
        client.configure_transfer_set("ICC1", "TS_Analog", config)
        print(f"    Data Set: {config.data_set_name}")
        print(f"    Interval: {config.interval}s")
        print(f"    Integrity Check: {config.integrity_check}s")
        print(f"    Buffer Time: {config.buffer_time}s")
        print(f"    RBE: {config.rbe}")
        print(f"    DS Conditions: interval={config.ds_conditions.interval_timeout}, "
              f"change={config.ds_conditions.object_change}")
        print()

        # Step 3: Start receiving reports
        print("[3] STARTING REPORT RECEIVER")
        print("-" * 40)
        client.start_receiving_reports()
        print("    Report queue initialized")
        print()

        # Step 4: Enable transfer set
        print("[4] ENABLING TRANSFER SET")
        print("-" * 40)
        client.enable_transfer_set("ICC1", "TS_Analog")
        print("    Transfer set enabled - server will now push reports")
        print()

        # Step 5: Simulate receiving reports
        print("[5] PROCESSING REPORTS")
        print("-" * 40)
        for i in range(3):
            # Simulate server pushing a report
            report = TransferReport(
                domain="ICC1",
                transfer_set_name="TS_Analog",
                values=[
                    PointValue(value=230.5 + i * 0.1, name="Voltage_A", quality=QUALITY_GOOD),
                    PointValue(value=231.0 + i * 0.1, name="Voltage_B", quality=QUALITY_GOOD),
                    PointValue(value=229.8 + i * 0.1, name="Voltage_C", quality=QUALITY_GOOD),
                    PointValue(value=50.01, name="Frequency", quality=QUALITY_GOOD),
                ],
                sequence_number=i + 1,
            )
            client._report_queue.put(report)

            # Process report
            received = client.get_next_report(timeout=1.0)
            if received:
                print(f"    Report #{received.sequence_number}:")
                for pv in received.values:
                    print(f"      {pv.name}: {pv.value}")

                # Step 6: ACK
                client.send_transfer_report_ack("ICC1")
                print(f"      -> ACK sent")
                print()

        # Step 7: Disable transfer set
        print("[7] DISABLING TRANSFER SET")
        print("-" * 40)
        client.disable_transfer_set("ICC1", "TS_Analog")
        print("    Transfer set disabled")
        print()

        # Step 8: Stop receiving
        print("[8] STOPPING REPORT RECEIVER")
        print("-" * 40)
        client.stop_receiving_reports()
        print("    Report receiver stopped")
        print()

        # Step 9: Delete data set
        print("[9] DELETING DATA SET")
        print("-" * 40)
        client.delete_data_set("ICC1", "MyAnalogDS")
        print("    Data set 'MyAnalogDS' deleted")
        print()

        client.disconnect()
        print("[*] Disconnected")
        print()
        print("=" * 70)
        print("TRANSFER SET LIFECYCLE COMPLETE")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
