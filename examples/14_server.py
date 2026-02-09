#!/usr/bin/env python3
"""
Minimal IEC 61850 Server Example

Creates an IEC 61850 server from a model config file, updates data
values periodically, and serves MMS clients.

Usage:
    python 14_server.py <model_cfg> [port]
    python 14_server.py model.cfg
    python 14_server.py model.cfg 10102
"""

import sys
import time
import math

from pyiec61850.server import IedServer, ServerConfig, ModelError, ServerError


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <model_cfg> [port]")
        print(f"Example: {sys.argv[0]} model.cfg 10102")
        sys.exit(1)

    model_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 102

    config = ServerConfig(port=port, max_connections=5)

    try:
        with IedServer(model_path, config) as server:
            server.start(port)
            print(f"IEC 61850 server running on port {port}")
            print("Press Ctrl+C to stop...")

            t = 0
            try:
                while True:
                    # Update a float value (e.g., simulated measurement)
                    value = 230.0 + 10.0 * math.sin(t * 0.1)
                    try:
                        server.lock_data_model()
                        server.update_float(
                            "simpleIOGenericIO/MMXU1.TotW.mag.f", value
                        )
                        server.unlock_data_model()
                    except Exception:
                        pass  # Node may not exist in the model

                    clients = server.get_number_of_open_connections()
                    print(f"  t={t} value={value:.1f} clients={clients}")

                    t += 1
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")

    except ModelError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ServerError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Server stopped.")


if __name__ == "__main__":
    main()
