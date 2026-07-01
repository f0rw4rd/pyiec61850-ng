"""
Integration test: GOOSE publish -> subscribe round-trip, inside Docker.

GOOSE uses an AF_PACKET raw socket (needs CAP_NET_RAW), so instead of requiring
raw-socket privileges on the host/CI runner we run the publisher AND subscriber
together in one container (same netns, on `lo`) with ``--cap-add=NET_RAW``. The
worker (``_goose_roundtrip_worker.py``) publishes GOOSE frames and subscribes to
them, printing ``ROUNDTRIP_OK`` only when the subscriber receives them, parses
cleanly (``getParseError()==0``), and decodes the data-set values.

This is the real-binding coverage that was missing when issue #20 shipped:
``GoosePublisher.start()`` crashed item-assigning the SWIG ``dstAddress`` array,
and no integration test ever started a real publisher. It also guards the
value-decode fix (passing NULL data-set values to ``GooseSubscriber_create`` so
libiec61850 auto-builds the data set instead of overflowing a zero-length
template).
"""

import os
import shutil
import subprocess
import unittest

from ._fixture import INTEGRATION_ENV

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WORKER = "tests/integration/_goose_roundtrip_worker.py"


class TestGooseRoundtripDocker(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if os.environ.get(INTEGRATION_ENV) != "1":
            raise unittest.SkipTest(f"{INTEGRATION_ENV}=1 not set")
        if shutil.which("docker") is None:
            raise unittest.SkipTest("docker not available")
        # The container mounts this repo and runs it via PYTHONPATH, so the
        # native extension must already be built here.
        try:
            import pyiec61850.pyiec61850  # noqa: F401
        except ImportError as e:
            raise unittest.SkipTest(f"native extension not built in repo: {e}")

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
            "lo",
            "lo",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self.fail("GOOSE round-trip container timed out")
        self.assertIn(
            "ROUNDTRIP_OK",
            proc.stdout,
            msg=f"publisher/subscriber did not round-trip.\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        self.assertIn("parse_error=0", proc.stdout, msg=proc.stdout)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)


if __name__ == "__main__":
    unittest.main()
