#!/usr/bin/env python3
"""
Minimal IEC 61850 server from a model config file.

Updates a simulated measurement every second until Ctrl+C.

Usage:
    python 14_server.py <model_cfg>
"""

import math
import sys
import time

from pyiec61850.server import IedServer, ServerConfig, ServerError


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <model_cfg>")
        sys.exit(1)

    port = 102
    with IedServer(sys.argv[1], ServerConfig(port=port, max_connections=5)) as server:
        server.start(port)
        t = 0
        try:
            while True:
                value = 230.0 + 10.0 * math.sin(t * 0.1)
                server.lock_data_model()
                try:
                    server.update_float("simpleIOGenericIO/MMXU1.TotW.mag.f", value)
                finally:
                    server.unlock_data_model()
                t += 1
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    try:
        main()
    except ServerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
