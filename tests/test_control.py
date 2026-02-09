#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.control module - Control operations client.

All tests use mocks since the C library isn't available in dev.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

logging.disable(logging.CRITICAL)


class TestControlImports(unittest.TestCase):
    """Test control module imports."""

    def test_import_control_client(self):
        from pyiec61850.mms.control import ControlClient
        self.assertIsNotNone(ControlClient)

    def test_import_types(self):
        from pyiec61850.mms.control import ControlResult
        self.assertIsNotNone(ControlResult)

    def test_import_exceptions(self):
        from pyiec61850.mms.control import (
            ControlError, SelectError, OperateError, CancelError,
        )
        from pyiec61850.mms.exceptions import MMSError
        self.assertTrue(issubclass(ControlError, MMSError))
        self.assertTrue(issubclass(SelectError, ControlError))
        self.assertTrue(issubclass(OperateError, ControlError))
        self.assertTrue(issubclass(CancelError, ControlError))

    def test_import_constants(self):
        from pyiec61850.mms.control import (
            CONTROL_MODEL_STATUS_ONLY,
            CONTROL_MODEL_DIRECT_NORMAL,
            CONTROL_MODEL_SBO_NORMAL,
            CONTROL_MODEL_DIRECT_ENHANCED,
            CONTROL_MODEL_SBO_ENHANCED,
        )
        self.assertEqual(CONTROL_MODEL_STATUS_ONLY, 0)
        self.assertEqual(CONTROL_MODEL_SBO_ENHANCED, 4)


class TestControlResult(unittest.TestCase):
    """Test ControlResult dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.control import ControlResult
        result = ControlResult()
        self.assertFalse(result.success)
        self.assertEqual(result.object_ref, "")

    def test_to_dict(self):
        from pyiec61850.mms.control import ControlResult
        result = ControlResult(success=True, object_ref="myLD/CSWI1.Pos")
        d = result.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(d["object_ref"], "myLD/CSWI1.Pos")


class TestControlClient(unittest.TestCase):
    """Test ControlClient class."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_raises_without_library(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', False):
            from pyiec61850.mms.control import ControlClient
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                ControlClient(Mock())

    def test_creation_success(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850'):
                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                self.assertFalse(ctrl.is_active)

    def test_select_success(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_select.return_value = True

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.select("myLD/CSWI1.Pos")
                self.assertTrue(result)

    def test_select_failure(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_select.return_value = False
                mock_iec.ControlObjectClient_getLastApplError.return_value = 1

                from pyiec61850.mms.control import ControlClient, SelectError
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(SelectError):
                    ctrl.select("myLD/CSWI1.Pos")

    def test_select_not_connected(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850'):
                from pyiec61850.mms.control import ControlClient
                from pyiec61850.mms.exceptions import NotConnectedError
                client = Mock()
                client.is_connected = False
                ctrl = ControlClient(client)
                with self.assertRaises(NotConnectedError):
                    ctrl.select("test")

    def test_operate_success(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_operate.return_value = True
                mock_iec.MmsValue_newBoolean.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.operate("myLD/CSWI1.Pos", True)
                self.assertTrue(result)

    def test_operate_failure(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_operate.return_value = False
                mock_iec.ControlObjectClient_getLastApplError.return_value = 2
                mock_iec.MmsValue_newBoolean.return_value = Mock()

                from pyiec61850.mms.control import ControlClient, OperateError
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(OperateError):
                    ctrl.operate("myLD/CSWI1.Pos", True)

    def test_cancel_success(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_cancel.return_value = True

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.cancel("myLD/CSWI1.Pos")
                self.assertTrue(result)

    def test_cancel_failure(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_cancel.return_value = False

                from pyiec61850.mms.control import ControlClient, CancelError
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(CancelError):
                    ctrl.cancel("myLD/CSWI1.Pos")

    def test_direct_operate(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_operate.return_value = True
                mock_iec.MmsValue_newIntegerFromInt32.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.direct_operate("myLD/CSWI1.Pos", 42)
                self.assertTrue(result)

    def test_select_with_value(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_selectWithValue.return_value = True
                mock_iec.MmsValue_newFloat.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.select_with_value("myLD/CSWI1.Pos", 3.14)
                self.assertTrue(result)

    def test_release(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                # Create a control object
                ctrl._get_or_create_control("test")
                self.assertTrue(ctrl.is_active)
                # Release it
                ctrl.release("test")
                self.assertFalse(ctrl.is_active)
                mock_iec.ControlObjectClient_destroy.assert_called_once()

    def test_release_all(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                ctrl._get_or_create_control("test1")
                ctrl._get_or_create_control("test2")
                self.assertEqual(len(ctrl._control_objects), 2)
                ctrl.release_all()
                self.assertEqual(len(ctrl._control_objects), 0)

    def test_context_manager(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                with ControlClient(client) as ctrl:
                    ctrl._get_or_create_control("test")
                # Should be released after exit
                self.assertFalse(ctrl.is_active)

    def test_reuses_existing_control_object(self):
        with patch('pyiec61850.mms.control._HAS_IEC61850', True):
            with patch('pyiec61850.mms.control.iec61850') as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient
                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                obj1 = ctrl._get_or_create_control("test")
                obj2 = ctrl._get_or_create_control("test")
                self.assertIs(obj1, obj2)
                # Should only be created once
                mock_iec.ControlObjectClient_create.assert_called_once()


if __name__ == '__main__':
    unittest.main()
