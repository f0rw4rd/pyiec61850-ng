#!/usr/bin/env python3
"""
Subscribe to reports from a Report Control Block (RCB).

Usage:
    python 12_reporting.py <host> <rcb_ref>
"""

import sys
import time

from pyiec61850.mms import MMSClient, ReportClient


def on_report(report):
    print(f"rptId={report.rpt_id} seqNum={report.seq_num} entries={len(report.entries)}")
    for entry in report.entries[:5]:
        print(f"  {entry.reference}: {entry.value}")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <rcb_ref>")
        sys.exit(1)

    host, rcb_ref = sys.argv[1], sys.argv[2]
    with MMSClient(host) as client:
        reports = ReportClient(client)
        reports.install_report_handler(rcb_ref, "rpt_01", on_report)
        reports.enable_reporting(rcb_ref)
        reports.trigger_gi_report(rcb_ref)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        reports.disable_reporting(rcb_ref)
        reports.uninstall_all_handlers()


if __name__ == "__main__":
    main()
