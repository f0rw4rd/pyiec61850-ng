"""
Integration test: Sampled Values publish -> subscribe round-trip, inside Docker.

Like the GOOSE round-trip, SV uses an AF_PACKET raw socket (needs CAP_NET_RAW),
so the publisher AND subscriber run together in one container (same netns, on
``lo``) with ``--cap-add=NET_RAW``. The worker (``_sv_roundtrip_worker.py``)
publishes SV ASDUs and subscribes to them, printing ``ROUNDTRIP_OK`` with the
decoded INT32 sample values only when the subscriber's callback decodes them.

This exercises the SV enablement (Phase 4): the SV L2 API wrapped in
patches/iec61850.i, the SVHandler director in patches/svHandler.hpp, and the
callback/ASDU refactor of sv/subscriber.py. It skips unless the native extension
in this repo actually exports the SV symbols (i.e. the wheel was rebuilt from the
SV-enabled interface).
"""

import os
import shutil
import subprocess
import unittest

from ._fixture import INTEGRATION_ENV

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WORKER = "tests/integration/_sv_roundtrip_worker.py"


class TestSVRoundtripDocker(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get(INTEGRATION_ENV) != "1":
            raise unittest.SkipTest(f"{INTEGRATION_ENV}=1 not set")
        if shutil.which("docker") is None:
            raise unittest.SkipTest("docker not available")
        # The container mounts this repo and runs it via PYTHONPATH, so the
        # native extension must already be built here — and it must be an
        # SV-enabled build (older wheels don't export the SV symbols).
        try:
            import pyiec61850.pyiec61850 as _p
        except ImportError as e:
            raise unittest.SkipTest(f"native extension not built in repo: {e}")
        if not hasattr(_p, "SVReceiver_create"):
            raise unittest.SkipTest(
                "native extension has no SV support; rebuild the wheel from the "
                "SV-enabled patches/iec61850.i"
            )

    def test_publish_subscribe_roundtrip(self):
        cmd = [
            "docker",
            "run",
            "--rm",
            "--cap-add=NET_RAW",
            "-v",
            f"{_REPO_ROOT}:/repo",
            "-w",
            "/repo",
            "-e",
            "PYTHONPATH=/repo",
            "python:3.13-slim",
            "python",
            _WORKER,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self.fail("SV round-trip container timed out")
        self.assertIn(
            "ROUNDTRIP_OK",
            proc.stdout,
            msg=f"publisher/subscriber did not round-trip.\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
