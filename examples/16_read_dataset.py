#!/usr/bin/env python3
"""
Dataset bulk read example.

Reads an entire dataset in one MMS request via MMSClient.read_dataset().
Much faster than polling members one by one, because the round-trip is
paid once per dataset instead of once per member.

Dataset references accept both forms:
    "LDName/LNName.DataSetName"
    "LDName/LNName$DataSetName"

Usage:
    python 16_read_dataset.py <host> <dataset_ref>
"""

import sys

from pyiec61850.mms import MMSClient


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <dataset_ref>")
        sys.exit(1)

    host, dataset_ref = sys.argv[1], sys.argv[2]

    with MMSClient(host) as client:
        values = client.read_dataset(dataset_ref)
        for i, v in enumerate(values):
            print(f"[{i}] {v!r}")


if __name__ == "__main__":
    main()
