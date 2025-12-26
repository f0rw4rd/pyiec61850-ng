#!/usr/bin/env python3
"""
Tests for pyiec61850.mms module - Safe MMS wrappers.

These tests verify the safety wrappers work correctly without
requiring the actual C library (uses mocks).
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

# Suppress logging during tests
logging.disable(logging.CRITICAL)


class TestMmsImports(unittest.TestCase):
    """Test that mms module imports correctly."""

    def test_import_module(self):
        """Test basic module import."""
        from pyiec61850 import mms
        self.assertIsNotNone(mms)

    def test_import_client(self):
        """Test MMSClient import."""
        from pyiec61850.mms import MMSClient
        self.assertIsNotNone(MMSClient)

    def test_import_utils(self):
        """Test utility functions import."""
        from pyiec61850.mms import (
            safe_to_char_p,
            safe_linked_list_iter,
            safe_linked_list_destroy,
            safe_mms_error_destroy,
            safe_mms_value_delete,
            safe_identity_destroy,
        )
        self.assertIsNotNone(safe_to_char_p)

    def test_import_guards(self):
        """Test context manager guards import."""
        from pyiec61850.mms import (
            LinkedListGuard,
            MmsValueGuard,
            MmsErrorGuard,
            IdentityGuard,
        )
        self.assertIsNotNone(LinkedListGuard)

    def test_import_exceptions(self):
        """Test exception classes import."""
        from pyiec61850.mms import (
            MMSError,
            LibraryNotFoundError,
            ConnectionFailedError,
            NotConnectedError,
            NullPointerError,
        )
        self.assertTrue(issubclass(ConnectionFailedError, MMSError))


class TestSafeToCharP(unittest.TestCase):
    """Test safe_to_char_p function (Issue #2 fix)."""

    def test_none_input_returns_none(self):
        """NULL pointer should return None, not crash."""
        from pyiec61850.mms.utils import safe_to_char_p
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                result = safe_to_char_p(None)
                self.assertIsNone(result)
                # toCharP should NOT be called with None
                mock_iec.toCharP.assert_not_called()

    def test_zero_input_returns_none(self):
        """Zero (NULL in C) should return None."""
        from pyiec61850.mms.utils import safe_to_char_p
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                result = safe_to_char_p(0)
                self.assertIsNone(result)
                mock_iec.toCharP.assert_not_called()

    def test_valid_pointer_calls_toCharP(self):
        """Valid pointer should call toCharP."""
        from pyiec61850.mms.utils import safe_to_char_p
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.toCharP.return_value = "test_string"
                mock_ptr = Mock()
                result = safe_to_char_p(mock_ptr)
                self.assertEqual(result, "test_string")
                mock_iec.toCharP.assert_called_once_with(mock_ptr)

    def test_toCharP_exception_returns_none(self):
        """Exception in toCharP should return None, not crash."""
        from pyiec61850.mms.utils import safe_to_char_p
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.toCharP.side_effect = Exception("Segfault avoided!")
                mock_ptr = Mock()
                result = safe_to_char_p(mock_ptr)
                self.assertIsNone(result)


class TestSafeLinkedListIter(unittest.TestCase):
    """Test safe_linked_list_iter function (Issue #2 & #3 fix)."""

    def test_none_list_yields_nothing(self):
        """NULL list should yield nothing."""
        from pyiec61850.mms.utils import safe_linked_list_iter
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850'):
                result = list(safe_linked_list_iter(None))
                self.assertEqual(result, [])

    def test_iterates_valid_elements(self):
        """Should iterate and convert valid elements."""
        from pyiec61850.mms.utils import safe_linked_list_iter
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                # Setup mock linked list with 3 elements
                mock_list = Mock()
                elem1, elem2, elem3 = Mock(), Mock(), Mock()
                data1, data2, data3 = Mock(), Mock(), Mock()

                # LinkedList_getNext chain
                mock_iec.LinkedList_getNext.side_effect = [elem1, elem2, elem3, None]
                # LinkedList_getData for each element
                mock_iec.LinkedList_getData.side_effect = [data1, data2, data3]
                # toCharP conversion
                mock_iec.toCharP.side_effect = ["Device1", "Device2", "Device3"]

                result = list(safe_linked_list_iter(mock_list))
                self.assertEqual(result, ["Device1", "Device2", "Device3"])

    def test_skips_null_data_elements(self):
        """NULL data elements should be skipped (Issue #2)."""
        from pyiec61850.mms.utils import safe_linked_list_iter
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_list = Mock()
                elem1, elem2 = Mock(), Mock()

                mock_iec.LinkedList_getNext.side_effect = [elem1, elem2, None]
                # Second element has NULL data
                mock_iec.LinkedList_getData.side_effect = [Mock(), None]
                mock_iec.toCharP.return_value = "ValidDevice"

                result = list(safe_linked_list_iter(mock_list))
                # Should only have one result, NULL was skipped
                self.assertEqual(len(result), 1)


class TestLinkedListGuard(unittest.TestCase):
    """Test LinkedListGuard context manager (Issue #3 fix)."""

    def test_destroys_list_on_exit(self):
        """List should be destroyed when exiting context."""
        from pyiec61850.mms.utils import LinkedListGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_list = Mock()

                with LinkedListGuard(mock_list) as guard:
                    self.assertEqual(guard.list, mock_list)

                mock_iec.LinkedList_destroy.assert_called_once_with(mock_list)

    def test_nullifies_after_destroy(self):
        """Reference should be None after destroy (prevents double-free)."""
        from pyiec61850.mms.utils import LinkedListGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850'):
                mock_list = Mock()
                guard = LinkedListGuard(mock_list)

                with guard:
                    pass

                self.assertIsNone(guard.list)

    def test_handles_none_list(self):
        """Should handle None list gracefully."""
        from pyiec61850.mms.utils import LinkedListGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                with LinkedListGuard(None) as guard:
                    self.assertIsNone(guard.list)

                # destroy should not be called for None
                mock_iec.LinkedList_destroy.assert_not_called()

    def test_iterable(self):
        """Guard should be directly iterable."""
        from pyiec61850.mms.utils import LinkedListGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_list = Mock()
                mock_iec.LinkedList_getNext.side_effect = [Mock(), None]
                mock_iec.LinkedList_getData.return_value = Mock()
                mock_iec.toCharP.return_value = "Test"

                with LinkedListGuard(mock_list) as guard:
                    result = list(guard)

                self.assertEqual(result, ["Test"])


class TestMmsValueGuard(unittest.TestCase):
    """Test MmsValueGuard context manager (Issue #5 fix)."""

    def test_deletes_value_on_exit(self):
        """MmsValue should be deleted when exiting context."""
        from pyiec61850.mms.utils import MmsValueGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_value = Mock()

                with MmsValueGuard(mock_value) as guard:
                    self.assertEqual(guard.value, mock_value)

                mock_iec.MmsValue_delete.assert_called_once_with(mock_value)

    def test_nullifies_after_delete(self):
        """Reference should be None after delete."""
        from pyiec61850.mms.utils import MmsValueGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850'):
                mock_value = Mock()
                guard = MmsValueGuard(mock_value)

                with guard:
                    pass

                self.assertIsNone(guard.value)


class TestMmsErrorGuard(unittest.TestCase):
    """Test MmsErrorGuard context manager (Issue #1 fix)."""

    def test_uses_correct_destroy_function(self):
        """Should use MmsError_destroy (2 r's), not MmsErrror_destroy (3 r's)."""
        from pyiec61850.mms.utils import MmsErrorGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.MmsError_destroy = Mock()
                mock_error = Mock()

                with MmsErrorGuard(mock_error):
                    pass

                # Correct function name (2 r's)
                mock_iec.MmsError_destroy.assert_called_once_with(mock_error)


class TestIdentityGuard(unittest.TestCase):
    """Test IdentityGuard context manager (Issue #4 fix)."""

    def test_destroys_identity_on_exit(self):
        """Identity should be destroyed when exiting context."""
        from pyiec61850.mms.utils import IdentityGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_identity = Mock()

                with IdentityGuard(mock_identity) as guard:
                    self.assertEqual(guard.identity, mock_identity)

                mock_iec.MmsServerIdentity_destroy.assert_called_once_with(mock_identity)

    def test_handles_none_identity(self):
        """Should handle None identity (Issue #4)."""
        from pyiec61850.mms.utils import IdentityGuard
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                with IdentityGuard(None) as guard:
                    self.assertIsNone(guard.identity)

                mock_iec.MmsServerIdentity_destroy.assert_not_called()


class TestMMSClient(unittest.TestCase):
    """Test MMSClient class."""

    def test_client_creation(self):
        """Client should be creatable when library available."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850'):
                from pyiec61850.mms import MMSClient
                client = MMSClient()
                self.assertIsNotNone(client)
                self.assertFalse(client.is_connected)

    def test_client_raises_without_library(self):
        """Client should raise LibraryNotFoundError if library missing."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', False):
            from pyiec61850.mms import MMSClient, LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                MMSClient()

    def test_connect_success(self):
        """Successful connection."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850') as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_create.return_value = mock_conn
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_connect.return_value = 0  # Use actual value

                from pyiec61850.mms import MMSClient
                client = MMSClient()
                result = client.connect("192.168.1.100", 102)

                self.assertTrue(result)
                self.assertTrue(client.is_connected)
                self.assertEqual(client.host, "192.168.1.100")
                self.assertEqual(client.port, 102)

    def test_connect_failure(self):
        """Connection failure should raise ConnectionFailedError."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850') as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_create.return_value = mock_conn
                mock_iec.IedConnection_connect.return_value = 1  # Error
                mock_iec.IED_ERROR_OK = 0

                from pyiec61850.mms import MMSClient, ConnectionFailedError
                client = MMSClient()

                with self.assertRaises(ConnectionFailedError):
                    client.connect("192.168.1.100", 102)

    def test_disconnect_cleanup(self):
        """Disconnect should clean up resources."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850') as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_create.return_value = mock_conn
                mock_iec.IedConnection_connect.return_value = 0
                mock_iec.IED_ERROR_OK = 0

                from pyiec61850.mms import MMSClient
                client = MMSClient()
                client.connect("192.168.1.100", 102)
                client.disconnect()

                mock_iec.IedConnection_close.assert_called_once()
                mock_iec.IedConnection_destroy.assert_called_once()
                self.assertFalse(client.is_connected)

    def test_context_manager(self):
        """Context manager should auto-disconnect."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850') as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_create.return_value = mock_conn
                mock_iec.IedConnection_connect.return_value = 0
                mock_iec.IED_ERROR_OK = 0

                from pyiec61850.mms import MMSClient
                with MMSClient() as client:
                    client.connect("192.168.1.100", 102)

                # Should be disconnected after exiting context
                mock_iec.IedConnection_destroy.assert_called()

    def test_get_logical_devices_uses_guard(self):
        """get_logical_devices should use safe LinkedList handling."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
                with patch('pyiec61850.mms.client.iec61850') as mock_iec:
                    with patch('pyiec61850.mms.utils.iec61850', mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0

                        # Mock the device list result
                        mock_list = Mock()
                        mock_iec.IedConnection_getLogicalDeviceList.return_value = (mock_list, 0)

                        # Mock LinkedList iteration
                        elem1 = Mock()
                        mock_iec.LinkedList_getNext.side_effect = [elem1, None]
                        mock_iec.LinkedList_getData.return_value = Mock()
                        mock_iec.toCharP.return_value = "TestDevice"

                        from pyiec61850.mms import MMSClient
                        client = MMSClient()
                        client.connect("192.168.1.100", 102)
                        devices = client.get_logical_devices()

                        self.assertEqual(devices, ["TestDevice"])
                        # LinkedList should be destroyed
                        mock_iec.LinkedList_destroy.assert_called_once_with(mock_list)

    def test_not_connected_error(self):
        """Operations without connection should raise NotConnectedError."""
        with patch('pyiec61850.mms.client._HAS_IEC61850', True):
            with patch('pyiec61850.mms.client.iec61850'):
                from pyiec61850.mms import MMSClient, NotConnectedError
                client = MMSClient()

                with self.assertRaises(NotConnectedError):
                    client.get_logical_devices()


class TestUnpackResult(unittest.TestCase):
    """Test unpack_result helper function."""

    def test_tuple_result(self):
        """Should unpack (value, error) tuples."""
        from pyiec61850.mms.utils import unpack_result
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0

                value, error, ok = unpack_result(("data", 0))
                self.assertEqual(value, "data")
                self.assertEqual(error, 0)
                self.assertTrue(ok)

    def test_tuple_result_with_error(self):
        """Should detect error in tuple result."""
        from pyiec61850.mms.utils import unpack_result
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0

                value, error, ok = unpack_result(("data", 5))
                self.assertEqual(value, "data")
                self.assertEqual(error, 5)
                self.assertFalse(ok)

    def test_single_value_result(self):
        """Should handle single value (non-tuple) results."""
        from pyiec61850.mms.utils import unpack_result
        with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils.iec61850') as mock_iec:
                mock_iec.IED_ERROR_OK = 0

                value, error, ok = unpack_result("just_data")
                self.assertEqual(value, "just_data")
                self.assertTrue(ok)


class TestCleanupAll(unittest.TestCase):
    """Test cleanup_all helper function."""

    def test_cleans_multiple_resources(self):
        """Should call all cleanup functions."""
        from pyiec61850.mms.utils import cleanup_all

        cleanup1 = Mock()
        cleanup2 = Mock()
        resource1 = Mock()
        resource2 = Mock()

        cleanup_all(
            (resource1, cleanup1),
            (resource2, cleanup2),
        )

        cleanup1.assert_called_once_with(resource1)
        cleanup2.assert_called_once_with(resource2)

    def test_skips_none_resources(self):
        """Should skip None resources."""
        from pyiec61850.mms.utils import cleanup_all

        cleanup1 = Mock()
        cleanup_all((None, cleanup1))
        cleanup1.assert_not_called()

    def test_continues_after_error(self):
        """Should continue cleaning even if one fails."""
        from pyiec61850.mms.utils import cleanup_all

        cleanup1 = Mock(side_effect=Exception("Cleanup failed"))
        cleanup2 = Mock()
        resource1 = Mock()
        resource2 = Mock()

        # Should not raise
        cleanup_all(
            (resource1, cleanup1),
            (resource2, cleanup2),
        )

        # Second cleanup should still be called
        cleanup2.assert_called_once_with(resource2)


if __name__ == '__main__':
    unittest.main()
