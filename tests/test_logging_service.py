#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.logging_service module - Log/Journal queries.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestLoggingImports(unittest.TestCase):
    """Test logging service module imports."""

    def test_import_log_client(self):
        from pyiec61850.mms.logging_service import LogClient

        self.assertIsNotNone(LogClient)

    def test_import_types(self):
        from pyiec61850.mms.logging_service import (
            JournalEntry,
            JournalEntryData,
            LogQueryResult,
        )

        self.assertIsNotNone(JournalEntry)
        self.assertIsNotNone(JournalEntryData)
        self.assertIsNotNone(LogQueryResult)

    def test_import_exceptions(self):
        from pyiec61850.mms.exceptions import MMSError
        from pyiec61850.mms.logging_service import LogError, LogQueryError

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
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", False):
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            from pyiec61850.mms.logging_service import LogClient

            with self.assertRaises(LibraryNotFoundError):
                LogClient(Mock())

    def test_creation_success(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850"):
                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                self.assertIsNotNone(log_client)

    def test_query_log_after_not_connected(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850"):
                from pyiec61850.mms.exceptions import NotConnectedError
                from pyiec61850.mms.logging_service import LogClient

                client = Mock()
                client.is_connected = False
                log_client = LogClient(client)
                with self.assertRaises(NotConnectedError):
                    log_client.query_log_after("test", "001", 0)

    def test_query_log_after_success(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogAfter.return_value = (None, 7)

                from pyiec61850.mms.logging_service import LogClient, LogQueryError

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                with self.assertRaises(LogQueryError):
                    log_client.query_log_after("test", "001", 0)

    def test_query_log_by_time_success(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogByTime.return_value = (None, 0)

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_by_time("myLD/LLN0$log01", 1000, 2000)

                self.assertEqual(result.entry_count, 0)

    def test_query_log_by_time_error(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_queryLogByTime.return_value = (None, 5)

                from pyiec61850.mms.logging_service import LogClient, LogQueryError

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                with self.assertRaises(LogQueryError):
                    log_client.query_log_by_time("test", 1000, 2000)

    def test_context_manager(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850"):
                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                with LogClient(client) as log_client:
                    self.assertIsNotNone(log_client)


class TestLogClientCrashPaths(unittest.TestCase):
    """Test LogClient crash paths: NULL returns, journal parsing."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_query_log_after_with_entries(self):
        """query_log_after with valid entries must parse them."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogAfter.return_value = (mock_list, 0)

                # Mock journal entry iteration
                mock_entry_elem = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_entry_elem, None]
                mock_entry_data = Mock()
                mock_iec.LinkedList_getData.return_value = mock_entry_data
                mock_iec.MmsJournalEntry_getEntryID.return_value = "entry001"
                mock_iec.MmsJournalEntry_getOccurenceTime.return_value = 1704067200000
                mock_iec.MmsJournalEntry_getJournalVariables.return_value = None

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("myLD/LLN0$log01", "000", 1000)

                self.assertEqual(result.entry_count, 1)
                self.assertEqual(result.entries[0].entry_id, "entry001")

    def test_query_log_by_time_with_entries(self):
        """query_log_by_time with valid entries must parse them."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogByTime.return_value = (mock_list, 0)

                mock_entry_elem = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_entry_elem, None]
                mock_entry_data = Mock()
                mock_iec.LinkedList_getData.return_value = mock_entry_data
                mock_iec.MmsJournalEntry_getEntryID.return_value = "entry002"
                mock_iec.MmsJournalEntry_getOccurenceTime.return_value = 0
                mock_iec.MmsJournalEntry_getJournalVariables.return_value = None

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_by_time("myLD/LLN0$log01", 1000, 2000)

                self.assertEqual(result.entry_count, 1)

    def test_parse_journal_entries_null_data_skipped(self):
        """NULL data entries must be skipped in journal parsing."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogAfter.return_value = (mock_list, 0)

                mock_elem1 = Mock()
                mock_elem2 = Mock()
                mock_iec.LinkedList_getNext.side_effect = [mock_elem1, mock_elem2, None]
                # First entry has NULL data, second has valid data
                mock_iec.LinkedList_getData.side_effect = [None, Mock()]
                mock_iec.MmsJournalEntry_getEntryID.return_value = "entry"
                mock_iec.MmsJournalEntry_getOccurenceTime.return_value = 0
                mock_iec.MmsJournalEntry_getJournalVariables.return_value = None

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("test", "000", 0)

                self.assertEqual(result.entry_count, 1)

    def test_parse_journal_variables(self):
        """Journal variables must be parsed with tag and value."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogAfter.return_value = (mock_list, 0)

                mock_entry_elem = Mock()
                mock_var_elem = Mock()
                mock_var_data = Mock()

                # Entry linked list iteration
                mock_entry_data = Mock()
                # We need separate side_effects for the two linked list iterations
                mock_iec.LinkedList_getNext.side_effect = [
                    mock_entry_elem,  # First call: entry list
                    mock_var_elem,  # Second call: variable list
                    None,  # Third call: end of variable list
                    None,  # Fourth call: end of entry list
                ]
                mock_iec.LinkedList_getData.side_effect = [mock_entry_data, mock_var_data]
                mock_iec.MmsJournalEntry_getEntryID.return_value = "entry"
                mock_iec.MmsJournalEntry_getOccurenceTime.return_value = 0
                mock_var_list = Mock()
                mock_iec.MmsJournalEntry_getJournalVariables.return_value = mock_var_list
                mock_iec.MmsJournalVariable_getTag.return_value = "myTag"
                mock_mms_val = Mock()
                mock_iec.MmsJournalVariable_getValue.return_value = mock_mms_val
                mock_iec.MMS_INTEGER = 4
                mock_iec.MmsValue_getType.return_value = 4
                mock_iec.MmsValue_toInt32.return_value = 99

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("test", "000", 0)

                self.assertEqual(result.entry_count, 1)
                entry = result.entries[0]
                self.assertEqual(len(entry.values), 1)
                self.assertEqual(entry.values[0].tag, "myTag")
                self.assertEqual(entry.values[0].value, 99)

    def test_parse_journal_entries_exception_returns_partial(self):
        """Exception during parsing must return what was parsed so far."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogAfter.return_value = (mock_list, 0)

                # LinkedList_getNext raises on first call
                mock_iec.LinkedList_getNext.side_effect = RuntimeError("parse crash")

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("test", "000", 0)

                # Should return empty result, not crash
                self.assertEqual(result.entry_count, 0)

    def test_query_log_by_time_non_tuple_result(self):
        """query_log_by_time with non-tuple result (direct return)."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                # Direct return (not a tuple)
                mock_iec.IedConnection_queryLogByTime.return_value = None

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_by_time("test", 0, 1000)

                self.assertEqual(result.entry_count, 0)

    def test_journal_variable_null_value_no_crash(self):
        """NULL journal variable value must not crash."""
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_list = Mock()
                mock_iec.IedConnection_queryLogAfter.return_value = (mock_list, 0)

                mock_entry_elem = Mock()
                mock_var_elem = Mock()
                mock_var_data = Mock()
                mock_entry_data = Mock()

                mock_iec.LinkedList_getNext.side_effect = [
                    mock_entry_elem,
                    mock_var_elem,
                    None,
                    None,
                ]
                mock_iec.LinkedList_getData.side_effect = [mock_entry_data, mock_var_data]
                mock_iec.MmsJournalEntry_getEntryID.return_value = "entry"
                mock_iec.MmsJournalEntry_getOccurenceTime.return_value = 0
                mock_var_list = Mock()
                mock_iec.MmsJournalEntry_getJournalVariables.return_value = mock_var_list
                mock_iec.MmsJournalVariable_getTag.return_value = "tag"
                mock_iec.MmsJournalVariable_getValue.return_value = None

                from pyiec61850.mms.logging_service import LogClient

                client = self._make_mock_mms_client()
                log_client = LogClient(client)
                result = log_client.query_log_after("test", "000", 0)

                self.assertEqual(result.entry_count, 1)
                self.assertEqual(len(result.entries[0].values), 1)


class TestLoggingExtractMmsValue(unittest.TestCase):
    """Test _extract_mms_value in logging_service module."""

    def test_null_returns_none(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            from pyiec61850.mms.logging_service import _extract_mms_value

            self.assertIsNone(_extract_mms_value(None))

    def test_no_library_returns_none(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", False):
            from pyiec61850.mms.logging_service import _extract_mms_value

            self.assertIsNone(_extract_mms_value(Mock()))

    def test_exception_returns_none(self):
        with patch("pyiec61850.mms.logging_service._HAS_IEC61850", True):
            with patch("pyiec61850.mms.logging_service.iec61850") as mock_iec:
                mock_iec.MmsValue_getType.side_effect = RuntimeError("crash")

                from pyiec61850.mms.logging_service import _extract_mms_value

                self.assertIsNone(_extract_mms_value(Mock()))


if __name__ == "__main__":
    unittest.main()
