"""
Shared fixture for integration tests against a real libiec61850 server.

Tests in this directory talk to an actual ``server_example_basic_io``
running in a podman (or docker) container. They are gated behind the
``PYIEC61850_INTEGRATION`` environment variable so ``python run_tests.py``
stays fast for everyone who does not have a container runtime.

Enable with::

    PYIEC61850_INTEGRATION=1 python -m unittest discover -s tests/integration -t .

The fixture assumes:
  * ``podman`` (or ``docker``) is on ``$PATH``
  * ``examples/Dockerfile.testserver`` can build
  * ``pyiec61850-ng`` is importable (real SWIG extension, not mocks)

Any of those missing causes the suite to be *skipped*, not failed — an
unavailable environment is not a regression in the library under test.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import socket
import subprocess
import time
import unittest
from typing import Optional

from pyiec61850.mms import MMSClient

INTEGRATION_ENV = "PYIEC61850_INTEGRATION"
TESTSERVER_OVERRIDE_ENV = "PYIEC61850_TESTSERVER"  # "host:port" to skip container mgmt
IMAGE_TAG = "local/iec61850-testserver"
CONTAINER_NAME = "pyiec61850-integration-testsrv"
HOST_PORT = 11102  # avoid clashing with local services
CONTAINER_PORT = 102
STARTUP_TIMEOUT_SEC = 15

# ---------------------------------------------------------------------------
# Static model constants for server_example_basic_io (libiec61850 v1.6).
# These are hard-coded in libiec61850's example sources.
# ---------------------------------------------------------------------------
LD_NAME = "simpleIOGenericIO"

# Logical nodes always present under LD_NAME.
EXPECTED_LOGICAL_NODES = {"LLN0", "LPHD1", "GGIO1"}

# Static datasets defined in LLN0.
DATASET_EVENTS = f"{LD_NAME}/LLN0.Events"
DATASET_MEASUREMENTS = f"{LD_NAME}/LLN0.Measurements"
DATASET_EVENTS_SIZE = 4
DATASET_MEASUREMENTS_SIZE = 8

# Individual attribute references.
REF_MX_FLOAT = f"{LD_NAME}/GGIO1.AnIn1.mag.f"
REF_ST_BOOL = f"{LD_NAME}/GGIO1.Mod.stVal"

# Writable boolean control point (SPCSO1).  The basic_io model exposes
# SPCSO1–SPCSO4 under GGIO1, each with a boolean stVal writable via CO.
REF_SPCSO1_STVAL = f"{LD_NAME}/GGIO1.SPCSO1.stVal"

# The controllable value of the same point lives under the CO functional
# constraint at Oper.ctlVal — the proper target for write_value(fc="CO").
REF_SPCSO1_CTLVAL = f"{LD_NAME}/GGIO1.SPCSO1.Oper.ctlVal"


def _which_runtime() -> Optional[str]:
    """Return the first available container runtime CLI, or None."""
    for cmd in ("podman", "docker"):
        if shutil.which(cmd):
            return cmd
    return None


def _run(runtime: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [runtime, *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, deadline: float) -> None:
    """Wait until the server accepts a full MMS association, not just TCP.

    libiec61850's server starts listening on TCP before it is ready to
    negotiate MMS associations; if we return as soon as the TCP socket
    accepts, early ``MMSClient.connect()`` calls can race and be
    rejected with ``connection-rejected``. Probe with an actual MMS
    handshake so the caller gets a truly ready server.
    """
    while time.monotonic() < deadline:
        if _port_open(host, port):
            # TCP is up — try a full MMS association.
            try:
                probe = MMSClient(host, port)
                probe.connect(timeout=1000)
                probe.disconnect()
                return
            except Exception:
                time.sleep(0.3)
                continue
        time.sleep(0.3)
    raise TimeoutError(f"{host}:{port} did not open within deadline")


def _skip_reason() -> Optional[str]:
    """Return a human-readable skip reason, or None if we should run."""
    if os.environ.get(INTEGRATION_ENV) != "1":
        return f"{INTEGRATION_ENV}=1 not set"

    try:
        import pyiec61850.pyiec61850  # noqa: F401
    except ImportError as e:
        return f"pyiec61850 C extension not importable: {e}"

    # If the caller has already brought up a server and pointed us at it
    # via PYIEC61850_TESTSERVER=host:port, we do not need a container
    # runtime at all.
    if os.environ.get(TESTSERVER_OVERRIDE_ENV):
        return None

    runtime = _which_runtime()
    if runtime is None:
        return "no container runtime (podman/docker) on PATH"

    return None


def _parse_override() -> Optional[tuple]:
    """Parse PYIEC61850_TESTSERVER=host:port into (host, port) or None."""
    raw = os.environ.get(TESTSERVER_OVERRIDE_ENV)
    if not raw:
        return None
    if ":" not in raw:
        raise ValueError(f"{TESTSERVER_OVERRIDE_ENV} must be 'host:port', got {raw!r}")
    host, port_str = raw.rsplit(":", 1)
    return host, int(port_str)


class IntegrationServerCase(unittest.TestCase):
    """Base test case that brings up the libiec61850 test server once per class.

    Subclasses get:
        cls.host    — host the test server is reachable on (usually localhost)
        cls.port    — port the test server is reachable on
        self.client — a connected MMSClient, created fresh per test method
    """

    host: str = "127.0.0.1"
    port: int = HOST_PORT
    runtime: Optional[str] = None
    _own_container: bool = True

    # Subclasses may override to exercise different servers.
    image: str = IMAGE_TAG
    container_name: str = CONTAINER_NAME
    # Optional container entrypoint override (None -> image default = basic_io).
    server_entrypoint: Optional[str] = None
    # Whether this case honours the PYIEC61850_TESTSERVER override env. Cases
    # that need a specific (non-basic_io) server set this False so they always
    # manage their own container.
    use_testserver_override: bool = True

    _build_context: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "examples",
    )

    @classmethod
    def setUpClass(cls) -> None:
        reason = _skip_reason()
        if reason:
            raise unittest.SkipTest(reason)

        override = _parse_override() if cls.use_testserver_override else None
        if override is not None:
            cls.host, cls.port = override
            cls._own_container = False
            _wait_for_port(
                cls.host,
                cls.port,
                deadline=time.monotonic() + STARTUP_TIMEOUT_SEC,
            )
            return

        cls._own_container = True
        cls.runtime = _which_runtime()
        assert cls.runtime is not None  # guarded by _skip_reason

        cls._ensure_image_built()
        cls._start_container()
        try:
            _wait_for_port(
                cls.host,
                cls.port,
                deadline=time.monotonic() + STARTUP_TIMEOUT_SEC,
            )
        except TimeoutError:
            logs = _run(cls.runtime, "logs", cls.container_name, check=False).stdout
            cls._stop_container()
            raise unittest.SkipTest(
                f"test server did not accept connections in time. Logs:\n{logs}"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._own_container and cls.runtime is not None:
            cls._stop_container()

    # ------------------------------------------------------------------
    # Per-test connected client
    # ------------------------------------------------------------------

    def setUp(self) -> None:
        self.client = MMSClient(self.host, self.port)
        self.client.connect()

    def tearDown(self) -> None:
        # Best-effort cleanup: a teardown failure must not mask the test result.
        with contextlib.suppress(Exception):
            self.client.disconnect()

    # ------------------------------------------------------------------
    # Container management
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_image_built(cls) -> None:
        assert cls.runtime is not None
        # `image inspect` works on both docker and podman ("image exists" is
        # podman-only and errors on docker, forcing a needless rebuild).
        images = _run(
            cls.runtime,
            "image",
            "inspect",
            cls.image,
            check=False,
        )
        if images.returncode == 0:
            return
        # Build — quiet-ish, let stderr flow through so failures are visible.
        _run(
            cls.runtime,
            "build",
            "-f",
            os.path.join(cls._build_context, "Dockerfile.testserver"),
            "-t",
            cls.image,
            cls._build_context,
        )

    @classmethod
    def _start_container(cls) -> None:
        assert cls.runtime is not None
        # Remove any leftover container from a previous aborted run.
        _run(cls.runtime, "rm", "-f", cls.container_name, check=False)
        args = [
            "run",
            "-d",
            "--name",
            cls.container_name,
            "-p",
            f"{cls.port}:{CONTAINER_PORT}",
        ]
        if cls.server_entrypoint:
            args += ["--entrypoint", cls.server_entrypoint]
        args.append(cls.image)
        _run(cls.runtime, *args)

    @classmethod
    def _stop_container(cls) -> None:
        assert cls.runtime is not None
        _run(cls.runtime, "rm", "-f", cls.container_name, check=False)


# ---------------------------------------------------------------------------
# Control server (libiec61850 server_example_control) — a separate binary in
# the same image, exercised by the ControlClient integration tests.
# ---------------------------------------------------------------------------
CONTROL_HOST_PORT = 11107
# server_example_control exposes GGIO1.SPCSO1..4 controllable points
# (control model "direct-with-normal-security").
CONTROL_LD = "simpleIOGenericIO"
REF_SPCSO1 = f"{CONTROL_LD}/GGIO1.SPCSO1"
REF_SPCSO2 = f"{CONTROL_LD}/GGIO1.SPCSO2"


class ControlServerCase(IntegrationServerCase):
    """Brings up libiec61850's ``server_example_control`` once per class.

    Same image as the basic_io fixture, but launched with the control-server
    entrypoint and its own name/port, so it can run alongside the basic_io
    container. Always manages its own container (ignores PYIEC61850_TESTSERVER,
    which points at the basic_io server).
    """

    container_name = "pyiec61850-integration-control"
    port = CONTROL_HOST_PORT
    server_entrypoint = "/usr/local/bin/server_example_control"
    use_testserver_override = False
