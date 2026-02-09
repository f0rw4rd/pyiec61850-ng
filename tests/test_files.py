#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.files module - MMS file services.

All tests use mocks since the C library isn't available in dev.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

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
        from pyiec61850.mms.files import FileError, FileNotFoundError, FileAccessError
        from pyiec61850.mms.exceptions import MMSError
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
        with patch('pyiec61850.mms.files._HAS_IEC61850', False):
            from pyiec61850.mms.files import FileClient
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                FileClient(Mock())

    def test_creation_success(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850'):
                from pyiec61850.mms.files import FileClient
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                self.assertIsNotNone(fc)

    def test_list_files_not_connected(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850'):
                from pyiec61850.mms.files import FileClient
                from pyiec61850.mms.exceptions import NotConnectedError
                client = Mock()
                client.is_connected = False
                fc = FileClient(client)
                with self.assertRaises(NotConnectedError):
                    fc.list_files("/")

    def test_list_files_empty(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_getFileDirectory.return_value = (None, 0)

                from pyiec61850.mms.files import FileClient
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                files = fc.list_files("/")
                self.assertEqual(files, [])

    def test_list_files_with_entries(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
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
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_getFileDirectory.return_value = (None, 5)

                from pyiec61850.mms.files import FileClient, FileError
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.list_files("/")

    def test_delete_file_success(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_deleteFile.return_value = 0

                from pyiec61850.mms.files import FileClient
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                result = fc.delete_file("test.log")
                self.assertTrue(result)

    def test_delete_file_error(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_deleteFile.return_value = 3

                from pyiec61850.mms.files import FileClient, FileError
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.delete_file("test.log")

    def test_rename_file_success(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_renameFile.return_value = 0

                from pyiec61850.mms.files import FileClient
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                result = fc.rename_file("old.log", "new.log")
                self.assertTrue(result)

    def test_rename_file_error(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_renameFile.return_value = 3

                from pyiec61850.mms.files import FileClient, FileError
                client = self._make_mock_mms_client()
                fc = FileClient(client)
                with self.assertRaises(FileError):
                    fc.rename_file("old.log", "new.log")

    def test_delete_file_not_connected(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850'):
                from pyiec61850.mms.files import FileClient
                from pyiec61850.mms.exceptions import NotConnectedError
                client = Mock()
                client.is_connected = False
                fc = FileClient(client)
                with self.assertRaises(NotConnectedError):
                    fc.delete_file("test.log")

    def test_context_manager(self):
        with patch('pyiec61850.mms.files._HAS_IEC61850', True):
            with patch('pyiec61850.mms.files.iec61850'):
                from pyiec61850.mms.files import FileClient
                client = self._make_mock_mms_client()
                with FileClient(client) as fc:
                    self.assertIsNotNone(fc)


if __name__ == '__main__':
    unittest.main()
