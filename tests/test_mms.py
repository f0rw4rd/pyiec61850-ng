#!/usr/bin/env python3
"""
Tests for pyiec61850.mms module - Safe MMS wrappers.

These tests verify the safety wrappers work correctly without
requiring the actual C library (uses mocks).
"""

import logging
import unittest
from unittest.mock import Mock, patch

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
        )

        self.assertIsNotNone(safe_to_char_p)

    def test_import_guards(self):
        """Test context manager guards import."""
        from pyiec61850.mms import (
            LinkedListGuard,
        )

        self.assertIsNotNone(LinkedListGuard)

    def test_import_exceptions(self):
        """Test exception classes import."""
        from pyiec61850.mms import (
            ConnectionFailedError,
            MMSError,
        )

        self.assertTrue(issubclass(ConnectionFailedError, MMSError))


class TestSafeToCharP(unittest.TestCase):
    """Test safe_to_char_p function (Issue #2 fix)."""

    def test_none_input_returns_none(self):
        """NULL pointer should return None, not crash."""
        from pyiec61850.mms.utils import safe_to_char_p

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                result = safe_to_char_p(None)
                self.assertIsNone(result)
                # toCharP should NOT be called with None
                mock_iec.toCharP.assert_not_called()

    def test_zero_input_returns_none(self):
        """Zero (NULL in C) should return None."""
        from pyiec61850.mms.utils import safe_to_char_p

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                result = safe_to_char_p(0)
                self.assertIsNone(result)
                mock_iec.toCharP.assert_not_called()

    def test_valid_pointer_calls_toCharP(self):
        """Valid pointer should call toCharP."""
        from pyiec61850.mms.utils import safe_to_char_p

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_iec.toCharP.return_value = "test_string"
                mock_ptr = Mock()
                result = safe_to_char_p(mock_ptr)
                self.assertEqual(result, "test_string")
                mock_iec.toCharP.assert_called_once_with(mock_ptr)

    def test_toCharP_exception_returns_none(self):
        """Exception in toCharP should return None, not crash."""
        from pyiec61850.mms.utils import safe_to_char_p

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_iec.toCharP.side_effect = Exception("Segfault avoided!")
                mock_ptr = Mock()
                result = safe_to_char_p(mock_ptr)
                self.assertIsNone(result)


class TestSafeLinkedListIter(unittest.TestCase):
    """Test safe_linked_list_iter function (Issue #2 & #3 fix)."""

    def test_none_list_yields_nothing(self):
        """NULL list should yield nothing."""
        from pyiec61850.mms.utils import safe_linked_list_iter

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850"):
                result = list(safe_linked_list_iter(None))
                self.assertEqual(result, [])

    def test_iterates_valid_elements(self):
        """Should iterate and convert valid elements."""
        from pyiec61850.mms.utils import safe_linked_list_iter

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
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

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
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

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_list = Mock()

                with LinkedListGuard(mock_list) as guard:
                    self.assertEqual(guard.list, mock_list)

                mock_iec.LinkedList_destroy.assert_called_once_with(mock_list)

    def test_nullifies_after_destroy(self):
        """Reference should be None after destroy (prevents double-free)."""
        from pyiec61850.mms.utils import LinkedListGuard

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850"):
                mock_list = Mock()
                guard = LinkedListGuard(mock_list)

                with guard:
                    pass

                self.assertIsNone(guard.list)

    def test_handles_none_list(self):
        """Should handle None list gracefully."""
        from pyiec61850.mms.utils import LinkedListGuard

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                with LinkedListGuard(None) as guard:
                    self.assertIsNone(guard.list)

                # destroy should not be called for None
                mock_iec.LinkedList_destroy.assert_not_called()

    def test_iterable(self):
        """Guard should be directly iterable."""
        from pyiec61850.mms.utils import LinkedListGuard

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
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

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_value = Mock()

                with MmsValueGuard(mock_value) as guard:
                    self.assertEqual(guard.value, mock_value)

                mock_iec.MmsValue_delete.assert_called_once_with(mock_value)

    def test_nullifies_after_delete(self):
        """Reference should be None after delete."""
        from pyiec61850.mms.utils import MmsValueGuard

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850"):
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

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
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

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_identity = Mock()

                with IdentityGuard(mock_identity) as guard:
                    self.assertEqual(guard.identity, mock_identity)

                mock_iec.MmsServerIdentity_destroy.assert_called_once_with(mock_identity)

    def test_handles_none_identity(self):
        """Should handle None identity (Issue #4)."""
        from pyiec61850.mms.utils import IdentityGuard

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                with IdentityGuard(None) as guard:
                    self.assertIsNone(guard.identity)

                mock_iec.MmsServerIdentity_destroy.assert_not_called()


class TestMMSClient(unittest.TestCase):
    """Test MMSClient class."""

    def test_client_creation(self):
        """Client should be creatable when library available."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850"):
                from pyiec61850.mms import MMSClient

                client = MMSClient()
                self.assertIsNotNone(client)
                self.assertFalse(client.is_connected)

    def test_client_raises_without_library(self):
        """Client should raise LibraryNotFoundError if library missing."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", False):
            from pyiec61850.mms import LibraryNotFoundError, MMSClient

            with self.assertRaises(LibraryNotFoundError):
                MMSClient()

    def test_connect_success(self):
        """Successful connection."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_create.return_value = mock_conn
                mock_iec.IedConnection_connect.return_value = 1  # Error
                mock_iec.IED_ERROR_OK = 0

                from pyiec61850.mms import ConnectionFailedError, MMSClient

                client = MMSClient()

                with self.assertRaises(ConnectionFailedError):
                    client.connect("192.168.1.100", 102)

    def test_disconnect_cleanup(self):
        """Disconnect should clean up resources."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
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
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850"):
                from pyiec61850.mms import MMSClient, NotConnectedError

                client = MMSClient()

                with self.assertRaises(NotConnectedError):
                    client.get_logical_devices()


class TestUnpackResult(unittest.TestCase):
    """Test unpack_result helper function."""

    def test_tuple_result(self):
        """Should unpack (value, error) tuples."""
        from pyiec61850.mms.utils import unpack_result

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0

                value, error, ok = unpack_result(("data", 0))
                self.assertEqual(value, "data")
                self.assertEqual(error, 0)
                self.assertTrue(ok)

    def test_tuple_result_with_error(self):
        """Should detect error in tuple result."""
        from pyiec61850.mms.utils import unpack_result

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0

                value, error, ok = unpack_result(("data", 5))
                self.assertEqual(value, "data")
                self.assertEqual(error, 5)
                self.assertFalse(ok)

    def test_single_value_result(self):
        """Should handle single value (non-tuple) results."""
        from pyiec61850.mms.utils import unpack_result

        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850") as mock_iec:
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


class TestMMSClientCrashPaths(unittest.TestCase):
    """Test MMSClient crash paths: connect, read, write, discover."""

    def test_connect_null_connection_create(self):
        """IedConnection_create returning NULL must raise ConnectionFailedError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedConnection_create.return_value = None

                from pyiec61850.mms import ConnectionFailedError, MMSClient

                client = MMSClient()
                with self.assertRaises(ConnectionFailedError):
                    client.connect("192.168.1.100", 102)

    def test_connect_unexpected_exception(self):
        """Unexpected exception during connect must cleanup and raise ConnectionFailedError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedConnection_create.return_value = Mock()
                mock_iec.IedConnection_setConnectTimeout.side_effect = RuntimeError("boom")

                from pyiec61850.mms import ConnectionFailedError, MMSClient

                client = MMSClient()
                with self.assertRaises(ConnectionFailedError):
                    client.connect("192.168.1.100", 102)

                self.assertFalse(client.is_connected)

    def test_connect_when_already_connected_disconnects_first(self):
        """connect() when already connected must disconnect first."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedConnection_create.return_value = Mock()
                mock_iec.IedConnection_connect.return_value = 0
                mock_iec.IED_ERROR_OK = 0

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                client.connect("host1", 102)
                client.connect("host2", 102)

                # Close should have been called for the first connection
                mock_iec.IedConnection_close.assert_called()

    def test_disconnect_when_not_connected(self):
        """disconnect() when not connected must be no-op."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                from pyiec61850.mms import MMSClient

                client = MMSClient()
                client.disconnect()  # Must not raise

                mock_iec.IedConnection_close.assert_not_called()

    def test_disconnect_close_exception_still_destroys(self):
        """If IedConnection_close throws, destroy must still be called."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedConnection_create.return_value = Mock()
                mock_iec.IedConnection_connect.return_value = 0
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_close.side_effect = RuntimeError("close failed")

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                client.connect("host", 102)
                client.disconnect()  # Must not raise

                mock_iec.IedConnection_destroy.assert_called()
                self.assertFalse(client.is_connected)

    def test_read_value_success(self):
        """read_value must convert MmsValue and clean up."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IEC61850_FC_ST = 0
                        mock_mms_val = Mock()
                        mock_iec.IedConnection_readObject.return_value = (mock_mms_val, 0)
                        mock_iec.MmsValue_getType.return_value = 0
                        mock_iec.MmsValue_getBoolean.return_value = True

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)

                        with patch("pyiec61850.mms.client.MMS_BOOLEAN", 0):
                            result = client.read_value("myLD/LN.DO.DA")

                        self.assertTrue(result)

    def test_read_value_error(self):
        """read_value with error result must raise ReadError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IEC61850_FC_ST = 0
                        mock_iec.IedConnection_readObject.return_value = (None, 5)

                        from pyiec61850.mms import MMSClient
                        from pyiec61850.mms.exceptions import ReadError

                        client = MMSClient()
                        client.connect("host", 102)
                        with self.assertRaises(ReadError):
                            client.read_value("bad/ref")

    def test_read_value_not_connected(self):
        """read_value when not connected must raise NotConnectedError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850"):
                from pyiec61850.mms import MMSClient, NotConnectedError

                client = MMSClient()
                with self.assertRaises(NotConnectedError):
                    client.read_value("test")

    def test_write_value_success(self):
        """write_value must create MmsValue and clean up."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IEC61850_FC_ST = 0
                        mock_iec.MmsValue_newBoolean.return_value = Mock()
                        mock_iec.IedConnection_writeObject.return_value = 0

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        result = client.write_value("myLD/LN.DO.DA", True)

                        self.assertTrue(result)

    def test_write_value_error(self):
        """write_value with error must raise WriteError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IEC61850_FC_ST = 0
                        mock_iec.MmsValue_newBoolean.return_value = Mock()
                        mock_iec.IedConnection_writeObject.return_value = 5

                        from pyiec61850.mms import MMSClient
                        from pyiec61850.mms.exceptions import WriteError

                        client = MMSClient()
                        client.connect("host", 102)
                        with self.assertRaises(WriteError):
                            client.write_value("test", True)

    def test_write_value_unsupported_type(self):
        """write_value with unsupported type must raise WriteError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IEC61850_FC_ST = 0

                        from pyiec61850.mms import MMSClient
                        from pyiec61850.mms.exceptions import WriteError

                        client = MMSClient()
                        client.connect("host", 102)
                        with self.assertRaises(WriteError):
                            client.write_value("test", {"unsupported": True})

    def test_write_value_not_connected(self):
        """write_value when not connected must raise NotConnectedError."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850"):
                from pyiec61850.mms import MMSClient, NotConnectedError

                client = MMSClient()
                with self.assertRaises(NotConnectedError):
                    client.write_value("test", True)

    def test_get_logical_nodes(self):
        """get_logical_nodes must return node names."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0

                        mock_list = Mock()
                        mock_iec.IedConnection_getLogicalNodeList.return_value = (mock_list, 0)
                        elem = Mock()
                        mock_iec.LinkedList_getNext.side_effect = [elem, None]
                        mock_iec.LinkedList_getData.return_value = Mock()
                        mock_iec.toCharP.return_value = "LLN0"

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        nodes = client.get_logical_nodes("myLD")

                        self.assertEqual(nodes, ["LLN0"])

    def test_get_data_objects(self):
        """get_data_objects must return object names."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.ACSI_CLASS_DATA_OBJECT = 0

                        mock_list = Mock()
                        mock_iec.IedConnection_getLogicalNodeDirectory.return_value = (
                            mock_list,
                            0,
                        )
                        elem = Mock()
                        mock_iec.LinkedList_getNext.side_effect = [elem, None]
                        mock_iec.LinkedList_getData.return_value = Mock()
                        mock_iec.toCharP.return_value = "TotW"

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        objs = client.get_data_objects("myLD", "MMXU1")

                        self.assertEqual(objs, ["TotW"])

    def test_get_data_objects_error_returns_empty(self):
        """get_data_objects with error must return empty list."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.ACSI_CLASS_DATA_OBJECT = 0
                        mock_iec.IedConnection_getLogicalNodeDirectory.return_value = (None, 5)

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        objs = client.get_data_objects("myLD", "LN")

                        self.assertEqual(objs, [])

    def test_get_server_identity(self):
        """get_server_identity must return identity info."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0

                        mock_identity = Mock()
                        mock_identity.vendorName = "TestVendor"
                        mock_identity.modelName = "TestModel"
                        mock_identity.revision = "1.0"
                        mock_iec.IedConnection_identify.return_value = (mock_identity, 0)

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        identity = client.get_server_identity()

                        self.assertEqual(identity.vendor, "TestVendor")
                        self.assertEqual(identity.model, "TestModel")

    def test_get_server_identity_null_result(self):
        """get_server_identity with NULL result must return empty identity."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
                with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                    with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                        mock_conn = Mock()
                        mock_iec.IedConnection_create.return_value = mock_conn
                        mock_iec.IedConnection_connect.return_value = 0
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.IedConnection_identify.return_value = (None, 0)

                        from pyiec61850.mms import MMSClient

                        client = MMSClient()
                        client.connect("host", 102)
                        identity = client.get_server_identity()

                        self.assertIsNone(identity.vendor)

    def test_convert_mms_value_null(self):
        """_convert_mms_value with NULL must return None."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850"):
                from pyiec61850.mms import MMSClient

                client = MMSClient()
                result = client._convert_mms_value(None)
                self.assertIsNone(result)

    def test_convert_mms_value_unknown_type(self):
        """_convert_mms_value with unknown type must return type info string."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.MmsValue_getType.return_value = 99

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                with (
                    patch("pyiec61850.mms.client.MMS_BOOLEAN", 0),
                    patch("pyiec61850.mms.client.MMS_INTEGER", 1),
                    patch("pyiec61850.mms.client.MMS_UNSIGNED", 2),
                    patch("pyiec61850.mms.client.MMS_FLOAT", 3),
                    patch("pyiec61850.mms.client.MMS_VISIBLE_STRING", 7),
                    patch("pyiec61850.mms.client.MMS_BIT_STRING", 4),
                ):
                    result = client._convert_mms_value(Mock())

                self.assertIn("99", str(result))

    def test_convert_mms_value_exception(self):
        """_convert_mms_value with exception must return None."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.MmsValue_getType.side_effect = RuntimeError("crash")

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                result = client._convert_mms_value(Mock())
                self.assertIsNone(result)

    def test_create_mms_value_types(self):
        """_create_mms_value must handle all supported types."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.MmsValue_newBoolean.return_value = Mock()
                mock_iec.MmsValue_newIntegerFromInt32.return_value = Mock()
                mock_iec.MmsValue_newFloat.return_value = Mock()
                mock_iec.MmsValue_newVisibleString.return_value = Mock()

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                self.assertIsNotNone(client._create_mms_value(True))
                self.assertIsNotNone(client._create_mms_value(42))
                self.assertIsNotNone(client._create_mms_value(3.14))
                self.assertIsNotNone(client._create_mms_value("hello"))
                self.assertIsNone(client._create_mms_value([1, 2, 3]))

    def test_cleanup_destroy_exception(self):
        """If IedConnection_destroy throws during cleanup, must not crash."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedConnection_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                client._connection = Mock()
                client._cleanup()  # Must not raise

                self.assertIsNone(client._connection)

    def test_get_error_string_with_api(self):
        """_get_error_string must use IedClientError_toString if available."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                mock_iec.IedClientError_toString.return_value = "timeout"

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                result = client._get_error_string(5)
                self.assertEqual(result, "timeout")

    def test_get_error_string_fallback(self):
        """_get_error_string must fallback to error code if API not available."""
        with patch("pyiec61850.mms.client._HAS_IEC61850", True):
            with patch("pyiec61850.mms.client.iec61850") as mock_iec:
                del mock_iec.IedClientError_toString

                from pyiec61850.mms import MMSClient

                client = MMSClient()
                result = client._get_error_string(5)
                self.assertIn("5", result)


if __name__ == "__main__":
    unittest.main()
