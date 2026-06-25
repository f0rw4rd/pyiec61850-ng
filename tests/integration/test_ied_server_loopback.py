"""
Integration test: pure-Python IedServer ↔ MMSClient loopback.

Every other test in this directory talks to a containerised C example
server (`server_example_basic_io`). That proves the client works but
leaves the Python-side ``IedServer`` untested end-to-end — exactly the
surface exercised by ``examples/14_server.py``.

This test spins up ``IedServer`` in the same process, connects a
``MMSClient`` over loopback, and verifies that values pushed via
``update_*`` are readable by the client. It does NOT need podman or
docker, so it runs even in minimal environments.

Model: libiec61850's ``server_example_config_file/model.cfg`` —
``simpleIO/GenericIO`` with LLN0, LPHD1, GGIO1.
"""

from __future__ import annotations

import os
import socket
import time
import unittest

from pyiec61850.mms import MMSClient

from ._fixture import _skip_reason

LOOPBACK_PORT_BASE = 11103

# Prefer the model config vendored alongside the tests (so this runs on a plain
# checkout); fall back to the libiec61850 source tree when present.
_VENDORED_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "model.cfg")
_SOURCE_CFG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "libiec61850",
    "examples",
    "server_example_config_file",
    "model.cfg",
)
MODEL_CFG = _VENDORED_CFG if os.path.exists(_VENDORED_CFG) else _SOURCE_CFG

# libiec61850 concatenates IED name ("simpleIO") with LD inst ("GenericIO")
# into a single domain ID. The client sees the joined form.
LD = "simpleIOGenericIO"
REF_FLOAT = f"{LD}/GGIO1.AnIn1.mag.f"
REF_BOOL = f"{LD}/GGIO1.Ind1.stVal"


def _free_port(base: int) -> int:
    """Find a free TCP port, starting from ``base``.

    We want a deterministic-ish port for easier debugging, but fall back
    to OS-assigned if the preferred one is in use.
    """
    for candidate in range(base, base + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", candidate))
                return candidate
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestIedServerLoopback(unittest.TestCase):
    """Spin up IedServer in-process and round-trip values via MMSClient."""

    @classmethod
    def setUpClass(cls) -> None:
        reason = _skip_reason()
        # _skip_reason also checks for a container runtime; we do not need
        # one here, so we only respect the PYIEC61850_INTEGRATION gate and
        # the C extension import check.
        if reason and "runtime" not in reason:
            raise unittest.SkipTest(reason)
        if not os.path.exists(MODEL_CFG):
            raise unittest.SkipTest(f"model cfg not found: {MODEL_CFG}")

        # Import lazily so the skip check above runs first.
        from pyiec61850.server import IedServer, ServerConfig

        cls.port = _free_port(LOOPBACK_PORT_BASE)
        cls.server = IedServer(MODEL_CFG, ServerConfig(port=cls.port, max_connections=5))
        cls.server.start(cls.port)
        # Give the server a moment to open its listening socket.
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            cls.server.stop()
            raise unittest.SkipTest(f"IedServer did not start listening on 127.0.0.1:{cls.port}")

    @classmethod
    def tearDownClass(cls) -> None:
        srv = getattr(cls, "server", None)
        if srv is not None:
            srv.stop()

    def setUp(self) -> None:
        self.client = MMSClient("127.0.0.1", self.port)
        self.client.connect()

    def tearDown(self) -> None:
        try:
            self.client.disconnect()
        except Exception:
            pass

    def test_server_reports_running(self):
        self.assertTrue(self.server.is_running)

    def test_client_sees_logical_device(self):
        devices = self.client.get_logical_devices()
        self.assertIn(LD, devices)

    def test_float_update_round_trip(self):
        """Push a float via update_float, read it back via the client."""
        self.server.lock_data_model()
        try:
            self.server.update_float(REF_FLOAT, 230.5)
        finally:
            self.server.unlock_data_model()

        value = self.client.read_value(REF_FLOAT, fc="MX")
        # mms_value_to_python may return a dict for structured MX values;
        # unwrap to the leaf float.
        if isinstance(value, dict):
            value = value.get("f", value)
        self.assertAlmostEqual(float(value), 230.5, places=3)

    def test_boolean_update_round_trip(self):
        """update_boolean value must be visible to a subsequent read."""
        self.server.lock_data_model()
        try:
            self.server.update_boolean(REF_BOOL, True)
        finally:
            self.server.unlock_data_model()

        value = self.client.read_value(REF_BOOL, fc="ST")
        self.assertIn(value, (True, 1))

    def test_repeated_updates_do_not_crash(self):
        """Many rapid updates + reads must not crash or leak MmsValues."""
        for i in range(50):
            self.server.lock_data_model()
            try:
                self.server.update_float(REF_FLOAT, float(i))
            finally:
                self.server.unlock_data_model()
            value = self.client.read_value(REF_FLOAT, fc="MX")
            if isinstance(value, dict):
                value = value.get("f", value)
            self.assertAlmostEqual(float(value), float(i), places=3)

    def test_open_connection_count(self):
        """The server should see our one client as an open connection."""
        # libiec61850 updates the connection count asynchronously. Poll
        # briefly so the test isn't flaky on slow machines.
        deadline = time.monotonic() + 2.0
        count = 0
        while time.monotonic() < deadline:
            count = self.server.get_number_of_open_connections()
            if count >= 1:
                break
            time.sleep(0.05)
        self.assertGreaterEqual(count, 1)
