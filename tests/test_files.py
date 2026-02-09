#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.files module - MMS file services.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestFilesImports(unittest.TestCase):
    """Test files module imports."""

    def test_import_file_client(self):
        from pyiec61850.mms.files import FileClient

        self.assertIsNotNone(FileClient)

    def test_import_types(self):
        from pyiec61850.mms.files import FileInfo

        self.assertIsNotNone(FileInfo)

    def test_import_exceptions(self):
        from pyiec61850.mms.exceptions import MMSError
        from pyiec61850.mms.files import FileError, FileNotFoundError

        self.assertTrue(issubclass(FileError, MMSError))
        self.assertTrue(issubclass(FileNotFoundError, FileError))


class TestFileInfo(unittest.TestCase):
    """Test FileInfo dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.files import FileInfo

        info = FileInfo()
        self.assertEqual(info.name, "")
        self.assertEqual(info.size, 0)

    def test_with_values(self):
        from pyiec61850.mms.files import FileInfo

        info = FileInfo(name="test.log", size=1024, last_modified=1704067200000)
        self.assertEqual(info.name, "test.log")
        self.assertEqual(info.size, 1024)
        self.assertIsNotNone(info.last_modified_datetime)

    def test_to_dict(self):
        from pyiec61850.mms.files import FileInfo

        info = FileInfo(name="test.log", size=1024)
        d = info.to_dict()
        self.assertEqual(d["name"], "test.log")
        self.assertEqual(d["size"], 1024)


class TestFileClient(unittest.TestCase):
    """Test FileClient class."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_raises_without_library(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", False):
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            from pyiec61850.mms.files import FileClient

            with self.assertRaises(LibraryNotFoundError):
                FileClient(Mock())

    def test_creation_success(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850"):
                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                self.assertIsNotNone(fc)

    def test_list_files_not_connected(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850"):
                from pyiec61850.mms.exceptions import NotConnectedError
                from pyiec61850.mms.files import FileClient

                client = Mock()
                client.is_connected = False
                fc = FileClient(client)
                with self.assertRaises(NotConnectedError):
                    fc.list_files("/")

    def test_list_files_empty(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_getFileDirectory.return_value = (None, 0)

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")
                self.assertEqual(files, [])

    def test_list_files_with_entries(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_getFileDirectory.return_value = (mock_list, 0)

                # Mock LinkedList with one entry
                mock_elem = Mock()
                mock_data = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_elem, None]
                mock_iec.LinkedList_getData.return_value = mock_data
                mock_iec.FileDirectoryEntry_getFileName.return_value = "test.log"
                mock_iec.FileDirectoryEntry_getFileSize.return_value = 512
                mock_iec.FileDirectoryEntry_getLastModified.return_value = 0

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")

                self.assertEqual(len(files), 1)
                self.assertEqual(files[0].name, "test.log")
                self.assertEqual(files[0].size, 512)

    def test_list_files_error(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_getFileDirectory.return_value = (None, 5)

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.list_files("/")

    def test_delete_file_success(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_deleteFile.return_value = 0

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                result = fc.delete_file("test.log")
                self.assertTrue(result)

    def test_delete_file_error(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_deleteFile.return_value = 3

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.delete_file("test.log")

    def test_rename_file_success(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_renameFile.return_value = 0

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                result = fc.rename_file("old.log", "new.log")
                self.assertTrue(result)

    def test_rename_file_error(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_renameFile.return_value = 3

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.rename_file("old.log", "new.log")

    def test_delete_file_not_connected(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850"):
                from pyiec61850.mms.exceptions import NotConnectedError
                from pyiec61850.mms.files import FileClient

                client = Mock()
                client.is_connected = False
                fc = FileClient(client)
                with self.assertRaises(NotConnectedError):
                    fc.delete_file("test.log")

    def test_context_manager(self):
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850"):
                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                with FileClient(client) as fc:
                    self.assertIsNotNone(fc)


class TestFileClientCrashPaths(unittest.TestCase):
    """Test FileClient crash paths: NULL returns, download, rename."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_list_files_null_data_skipped(self):
        """list_files must skip entries with NULL data."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_getFileDirectory.return_value = (mock_list, 0)

                mock_elem1 = Mock()
                mock_elem2 = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_elem1, mock_elem2, None]
                # First entry has NULL data, second has valid data
                mock_iec.LinkedList_getData.side_effect = [None, Mock()]
                mock_iec.FileDirectoryEntry_getFileName.return_value = "valid.log"
                mock_iec.FileDirectoryEntry_getFileSize.return_value = 100
                mock_iec.FileDirectoryEntry_getLastModified.return_value = 0

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")

                self.assertEqual(len(files), 1)
                self.assertEqual(files[0].name, "valid.log")

    def test_list_files_non_tuple_result(self):
        """list_files with non-tuple result (direct return) must work."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                # Direct return (not tuple)
                mock_iec.IedConnection_getFileDirectory.return_value = None

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")
                self.assertEqual(files, [])

    def test_list_files_linked_list_destroy_exception(self):
        """If LinkedList_destroy throws, list_files must still return results."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_getFileDirectory.return_value = (mock_list, 0)
                mock_elem = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_elem, None]
                mock_iec.LinkedList_getData.return_value = Mock()
                mock_iec.FileDirectoryEntry_getFileName.return_value = "test.log"
                mock_iec.FileDirectoryEntry_getFileSize.return_value = 50
                mock_iec.FileDirectoryEntry_getLastModified.return_value = 0
                mock_iec.LinkedList_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")
                self.assertEqual(len(files), 1)

    def test_download_file_null_mms_connection(self):
        """download_file with NULL MMS connection must raise FileError."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IedConnection_getMmsConnection.return_value = None

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.download_file("test.log")

    def test_download_file_open_returns_negative(self):
        """download_file with negative FRSM ID must raise FileNotFoundError."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_mms_conn = Mock()
                mock_iec.IedConnection_getMmsConnection.return_value = mock_mms_conn
                mock_iec.MmsConnection_fileOpen.return_value = (-1,)

                from pyiec61850.mms.files import FileClient
                from pyiec61850.mms.files import FileNotFoundError as FNF

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FNF):
                    fc.download_file("nonexistent.log")

    def test_download_file_open_success(self):
        """download_file with valid FRSM ID returns bytes (empty due to missing callback)."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_mms_conn = Mock()
                mock_iec.IedConnection_getMmsConnection.return_value = mock_mms_conn
                mock_iec.MmsConnection_fileOpen.return_value = (5, 0)

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                data = fc.download_file("test.log")

                self.assertEqual(data, b"")
                mock_iec.MmsConnection_fileClose.assert_called()

    def test_download_file_close_exception_no_crash(self):
        """If fileClose throws during finally, download_file must not crash."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_mms_conn = Mock()
                mock_iec.IedConnection_getMmsConnection.return_value = mock_mms_conn
                mock_iec.MmsConnection_fileOpen.return_value = (5, 0)
                mock_iec.MmsConnection_fileClose.side_effect = RuntimeError("close failed")

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                data = fc.download_file("test.log")  # Must not crash
                self.assertEqual(data, b"")

    def test_delete_file_tuple_error(self):
        """delete_file with tuple error return must be handled."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_deleteFile.return_value = (0,)

                from pyiec61850.mms.files import FileClient

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                result = fc.delete_file("test.log")
                self.assertTrue(result)

    def test_rename_file_no_api_available(self):
        """rename_file without IedConnection_renameFile must raise FileError."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                del mock_iec.IedConnection_renameFile

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.rename_file("old.log", "new.log")

    def test_rename_file_tuple_error(self):
        """rename_file with tuple error return."""
        with patch("pyiec61850.mms.files._HAS_IEC61850", True):
            with patch("pyiec61850.mms.files.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_renameFile.return_value = (5,)

                from pyiec61850.mms.files import FileClient, FileError

                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.rename_file("old.log", "new.log")


if __name__ == "__main__":
    unittest.main()
