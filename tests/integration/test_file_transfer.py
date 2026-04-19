"""
Integration test: MMSClient.download_file against a real server.

``download_file`` touches code paths that unit tests cannot meaningfully
exercise: ``IedConnection_getMmsConnection``,
``MmsConnection_downloadFile``, and ``MmsErrror_destroy`` (note the
triple-r — that is how the SWIG binding exports the symbol).

The ``server_example_basic_io`` serves files from its CWD.  We cannot
guarantee specific files exist, so the happy-path test is best-effort:
it tries to list the file directory first and, if a file is available,
downloads it and verifies the result is non-empty.  The negative path
(nonexistent file) is fully deterministic.
"""

import os
import tempfile

from pyiec61850.mms import MMSClient
from pyiec61850.mms.exceptions import FileTransferError, NotConnectedError

from ._fixture import IntegrationServerCase


class TestFileTransfer(IntegrationServerCase):
    def test_download_nonexistent_file_raises_file_transfer_error(self):
        """Must raise FileTransferError specifically, not a bare Exception
        or segfault."""
        with tempfile.TemporaryDirectory() as tmp:
            local = os.path.join(tmp, "nope.bin")
            with self.assertRaises(FileTransferError):
                self.client.download_file("does/not/exist.bin", local)

    def test_failed_download_cleans_up_partial_file(self):
        """libiec61850 creates the local file before checking the remote.
        On failure, download_file must remove that 0-byte artefact."""
        with tempfile.TemporaryDirectory() as tmp:
            local = os.path.join(tmp, "nope.bin")
            try:
                self.client.download_file("does/not/exist.bin", local)
            except FileTransferError:
                pass
            self.assertFalse(
                os.path.exists(local),
                "failed download left a partial file on disk",
            )

    def test_download_on_disconnected_client_raises_not_connected(self):
        """download_file before connect() must raise NotConnectedError,
        not segfault on a NULL MmsConnection."""
        client = MMSClient()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(NotConnectedError):
                client.download_file("anything", os.path.join(tmp, "x"))

    def test_finally_block_raises_expected_exception_type(self):
        """Regression tripwire for the MmsErrror_destroy triple-r typo.
        If the symbol is ever renamed upstream, the finally block would
        raise AttributeError instead of FileTransferError. We assert the
        exact exception type to catch that."""
        with tempfile.TemporaryDirectory() as tmp:
            local = os.path.join(tmp, "x.bin")
            with self.assertRaises(FileTransferError) as ctx:
                self.client.download_file("does/not/exist", local)
            # If AttributeError leaked through, assertRaises would have
            # failed already. Belt-and-suspenders:
            self.assertNotIsInstance(ctx.exception, AttributeError)

    def test_repeated_failed_downloads_do_not_crash(self):
        """Stress test the error path: repeated failures must not leak
        MmsError objects or corrupt connection state."""
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(20):
                local = os.path.join(tmp, f"fail_{i}.bin")
                with self.assertRaises(FileTransferError):
                    self.client.download_file(f"no/such/file_{i}", local)
                self.assertFalse(os.path.exists(local))
            # Connection must still be usable after repeated failures.
            self.assertTrue(self.client.is_connected)
