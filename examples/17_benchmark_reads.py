#!/usr/bin/env python3
"""
Compare single-attribute reads vs bulk dataset reads.

Shows why read_dataset() is usually the right answer when you need many
values: per-request overhead is paid once instead of once per member.

Append [FC] to attribute refs for non-ST values (e.g. ".mag.f[MX]") —
wrong-FC reads are a common latency trap on real devices.

Usage:
    python 17_benchmark_reads.py <host> <dataset_ref> [attr_ref ...]
"""

import sys
import time

from pyiec61850.mms import MMSClient


def time_ms(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000.0


def bench(label: str, fn, iterations: int = 20) -> None:
    samples = [time_ms(fn) for _ in range(iterations)]
    print(
        f"  {label:<22s}  min={min(samples):6.1f}  "
        f"med={sorted(samples)[len(samples) // 2]:6.1f}  "
        f"max={max(samples):6.1f}  ms"
    )


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <host> <dataset_ref> [attr_ref ...]")
        sys.exit(1)

    host, dataset_ref, attrs = sys.argv[1], sys.argv[2], sys.argv[3:]

    with MMSClient(host) as client:
        client.read_dataset(dataset_ref)  # warm-up

        bench("read_dataset", lambda: client.read_dataset(dataset_ref))

        for ref in attrs:
            bench(f"read_value {ref[:12]}", lambda r=ref: client.read_value(r))


if __name__ == "__main__":
    main()
