#!/usr/bin/env python3
"""
TASE.2 transfer set lifecycle: create dataset, configure, enable, receive, tear down.

Usage:
    python 06_tase2_transfer_sets.py <host> <domain> <member> [member ...]
"""

import sys

from pyiec61850.tase2 import (
    DSTransferSetConfig,
    TASE2Client,
    TransferSetConditions,
)


def main() -> None:
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <domain> <member> [member ...]")
        sys.exit(1)

    host, domain, *members = sys.argv[1:]

    client = TASE2Client(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
    client.connect(host, port=102)

    ds_name = "MyAnalogDS"
    ts_name = "TS_Analog"

    client.create_data_set(domain, ds_name, members)

    config = DSTransferSetConfig(
        data_set_name=ds_name,
        interval=10,
        integrity_check=60,
        buffer_time=2,
        rbe=True,
        ds_conditions=TransferSetConditions(
            interval_timeout=True, object_change=True, integrity_timeout=True,
        ),
    )
    client.configure_transfer_set(domain, ts_name, config)
    client.start_receiving_reports()
    client.enable_transfer_set(domain, ts_name)

    print("Waiting for reports (Ctrl+C to stop) ...")
    try:
        while True:
            report = client.get_next_report(timeout=5.0)
            if report:
                print(f"report #{report.sequence_number}: "
                      f"{[(pv.name, pv.value) for pv in report.values]}")
                client.send_transfer_report_ack(domain)
    except KeyboardInterrupt:
        pass

    client.disable_transfer_set(domain, ts_name)
    client.stop_receiving_reports()
    client.delete_data_set(domain, ds_name)
    client.disconnect()


if __name__ == "__main__":
    main()
