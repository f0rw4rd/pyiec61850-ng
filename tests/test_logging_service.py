#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.logging_service module - Log/Journal queries.

All tests use mocks since the C library isn't available in dev.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

logging.disable(logging.CRITICAL)


class TestLoggingImports(unittest.TestCase):
    """Test logging service module imports."""

    def test_import_log_client(self):
        from pyiec61850.mms.logging_service import LogClient
        self.assertIsNotNone(LogClient)

    def test_import_types(self):
        from pyiec61850.mms.logging_service import (
            JournalEntry, JournalEntryData, LogQueryResult,
        )
        self.assertIsNotNone(JournalEntry)
        self.assertIsNotNone(JournalEntryData)
        self.assertIsNotNone(LogQueryResult)

    def test_import_exceptions(self):
        from pyiec61850.mms.logging_service import LogError, LogQueryError
        from pyiec61850.mms.exceptions import MMSError
        self.assertTrue(issubclass(LogError, MMSError))
        self.assertTrue(issubclass(LogQueryError, LogError))


class TestJournalEntry(unittest.TestCase):
    """Test JournalEntry dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.logging_service import JournalEntry
        entry = JournalEntry()
        self.assertEqual(entry.entry_id, "")
        self.assertEqual(entry.values, [])
        self.assertIsNone(entry.timestamp)

    def test_to_dict(self):
        from pyiec61850.mms.logging_service import JournalEntry
        entry = JournalEntry(entry_id="001")
        d = entry.to_dict()
        self.assertEqual(d["entry_id"], "001")
        self.assertEqual(d["value_count"], 0)


class TestLogQueryResult(unittest.TestCase):
    """Test LogQueryResult dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.logging_service import LogQueryResult
        result = LogQueryResult()
        self.assertEqual(result.entries, [])
        self.assertFalse(result.more_follows)

    def test_to_dict(self):
        from pyiec61850.mms.logging_service import LogQueryResult
        result = LogQueryResult(entry_count=5, more_follows=True)
        d = result.to_dict()
        self.assertEqual(d["entry_count"], 5)
        self.assertTrue(d["more_follows"])


class TestLogClient(unittest.TestCase):
    """Test LogClient class."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_raises_without_library(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', False):
            from pyiec61850.mms.logging_service import LogClient
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                LogClient(Mock())

    def test_creation_success(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850'):
                from pyiec61850.mms.logging_service import LogClient
                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                self.assertIsNotNone(log_client)

    def test_query_log_after_not_connected(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850'):
                from pyiec61850.mms.logging_service import LogClient
                from pyiec61850.mms.exceptions import NotConnectedError
                client = Mock()
                client.is_connected = False
                log_client = LogClient(client)
                with self.assertRaises(NotConnectedError):
                    log_client.query_log_after("test", "001", 0)

    def test_query_log_after_success(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                # Return empty list (no entries)
                mock_iec.IedConnection_queryLogAfter.return_value = (None, 0)

                from pyiec61850.mms.logging_service import LogClient
                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("myLD/LLN0$log01", "001", 1000)

                self.assertEqual(result.entry_count, 0)
                self.assertEqual(result.entries, [])

    def test_query_log_after_error(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogAfter.return_value = (None, 7)

                from pyiec61850.mms.logging_service import LogClient, LogQueryError
                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                with self.assertRaises(LogQueryError):
                    log_client.query_log_after("test", "001", 0)

    def test_query_log_by_time_success(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogByTime.return_value = (None, 0)

                from pyiec61850.mms.logging_service import LogClient
                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_by_time("myLD/LLN0$log01", 1000, 2000)

                self.assertEqual(result.entry_count, 0)

    def test_query_log_by_time_error(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogByTime.return_value = (None, 5)

                from pyiec61850.mms.logging_service import LogClient, LogQueryError
                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                with self.assertRaises(LogQueryError):
                    log_client.query_log_by_time("test", 1000, 2000)

    def test_context_manager(self):
        with patch('pyiec61850.mms.logging_service._HAS_IEC61850', True):
            with patch('pyiec61850.mms.logging_service.iec61850'):
                from pyiec61850.mms.logging_service import LogClient
                client = self._make_mock_mms_client()
                with LogClient(client) as log_client:
                    self.assertIsNotNone(log_client)


if __name__ == '__main__':
    unittest.main()
