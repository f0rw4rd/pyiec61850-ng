#!/usr/bin/env python3
"""
IEC 61850 Reporting Example

Subscribe to reports from a Report Control Block (RCB).

Usage:
    python 12_reporting.py <server_ip> [port] [rcb_reference]
    python 12_reporting.py localhost 10102 simpleIOGenericIO/LLN0$BR$brcb01
"""

import sys
import time

from pyiec61850.mms import MMSClient, ConnectionFailedError, ReportClient, ReportError


def on_report(report):
    """Called for each received report."""
    print(f"  Report: rptId={report.rpt_id} seqNum={report.seq_num} "
          f"entries={len(report.entries)}")
    for entry in report.entries[:5]:
        print(f"    {entry.reference}: {entry.value}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <server_ip> [port] [rcb_reference]")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102
    rcb_ref = sys.argv[3] if len(sys.argv) > 3 else "simpleIOGenericIO/LLN0$BR$brcb01"

    with MMSClient() as client:
        try:
            print(f"Connecting to {hostname}:{port}")
            client.connect(hostname, port)

            reports = ReportClient(client)
            reports.install_report_handler(rcb_ref, "rpt_01", on_report)
            reports.enable_reporting(rcb_ref)
            reports.trigger_gi_report(rcb_ref)
            print(f"Listening for reports on {rcb_ref} (Ctrl+C to stop)...")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")

            reports.disable_reporting(rcb_ref)
            reports.uninstall_all_handlers()

        except (ConnectionFailedError, ReportError) as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
