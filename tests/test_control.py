#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.control module - Control operations client.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

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
            CancelError,
            ControlError,
            OperateError,
            SelectError,
        )
        from pyiec61850.mms.exceptions import MMSError

        self.assertTrue(issubclass(ControlError, MMSError))
        self.assertTrue(issubclass(SelectError, ControlError))
        self.assertTrue(issubclass(OperateError, ControlError))
        self.assertTrue(issubclass(CancelError, ControlError))

    def test_import_constants(self):
        from pyiec61850.mms.control import (
            CONTROL_MODEL_SBO_ENHANCED,
            CONTROL_MODEL_STATUS_ONLY,
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", False):
            from pyiec61850.mms.control import ControlClient
            from pyiec61850.mms.exceptions import LibraryNotFoundError

            with self.assertRaises(LibraryNotFoundError):
                ControlClient(Mock())

    def test_creation_success(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850"):
                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                self.assertFalse(ctrl.is_active)

    def test_select_success(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_select.return_value = True

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.select("myLD/CSWI1.Pos")
                self.assertTrue(result)

    def test_select_failure(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850"):
                from pyiec61850.mms.control import ControlClient
                from pyiec61850.mms.exceptions import NotConnectedError

                client = Mock()
                client.is_connected = False
                ctrl = ControlClient(client)
                with self.assertRaises(NotConnectedError):
                    ctrl.select("test")

    def test_operate_success(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_cancel.return_value = True

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                result = ctrl.cancel("myLD/CSWI1.Pos")
                self.assertTrue(result)

    def test_cancel_failure(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_control = Mock()
                mock_iec.ControlObjectClient_create.return_value = mock_control
                mock_iec.ControlObjectClient_cancel.return_value = False

                from pyiec61850.mms.control import CancelError, ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(CancelError):
                    ctrl.cancel("myLD/CSWI1.Pos")

    def test_direct_operate(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
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
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                with ControlClient(client) as ctrl:
                    ctrl._get_or_create_control("test")
                # Should be released after exit
                self.assertFalse(ctrl.is_active)

    def test_reuses_existing_control_object(self):
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                obj1 = ctrl._get_or_create_control("test")
                obj2 = ctrl._get_or_create_control("test")
                self.assertIs(obj1, obj2)
                # Should only be created once
                mock_iec.ControlObjectClient_create.assert_called_once()


class TestPyCommandTermHandlerDirectorInheritance(unittest.TestCase):
    """_PyCommandTermHandler must properly inherit from CommandTermHandler."""

    def test_base_class_is_dynamic(self):
        """_CommandTermHandlerBase must exist as module-level dynamic base class."""
        from pyiec61850.mms import control

        self.assertTrue(
            hasattr(control, "_CommandTermHandlerBase"),
            "_CommandTermHandlerBase not defined — handler won't inherit",
        )

    def test_handler_uses_dynamic_base(self):
        """_PyCommandTermHandler must inherit from _CommandTermHandlerBase."""
        from pyiec61850.mms.control import (
            _CommandTermHandlerBase,
            _PyCommandTermHandler,
        )

        self.assertTrue(
            issubclass(_PyCommandTermHandler, _CommandTermHandlerBase),
        )

    def test_handler_calls_super_init(self):
        """__init__ must call super().__init__(), not iec61850.X.__init__(self)."""
        import inspect

        from pyiec61850.mms.control import _PyCommandTermHandler

        source = inspect.getsource(_PyCommandTermHandler.__init__)
        self.assertIn("super().__init__", source)
        self.assertNotIn("CommandTermHandler.__init__(self)", source)


class TestPyCommandTermHandlerTriggerCrashPaths(unittest.TestCase):
    """Test _PyCommandTermHandler.trigger() crash paths."""

    def _make_handler(self, callback=None):
        from pyiec61850.mms.control import _PyCommandTermHandler

        return _PyCommandTermHandler(callback or Mock(), "myLD/CSWI1.Pos")

    def test_trigger_with_null_control_object_no_crash(self):
        """trigger() must not crash when _libiec61850_control_object_client is missing."""
        handler = self._make_handler()
        handler.trigger()  # Must not raise (AttributeError caught)

    def test_trigger_callback_exception_no_crash(self):
        """trigger() must catch callback exceptions."""
        callback = Mock(side_effect=RuntimeError("callback crashed"))
        handler = self._make_handler(callback)
        handler._libiec61850_control_object_client = Mock()

        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_getLastApplError.return_value = 0
                handler.trigger()  # Must not raise

    def test_trigger_with_null_callback_no_crash(self):
        """trigger() with None callback must not crash."""
        handler = self._make_handler()
        handler._callback = None
        handler.trigger()  # Must not raise

    def test_trigger_delivers_result_to_callback(self):
        """trigger() must deliver ControlResult to callback."""
        callback = Mock()
        handler = self._make_handler(callback)
        handler._libiec61850_control_object_client = Mock()

        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_getLastApplError.return_value = 0
                handler.trigger()

                callback.assert_called_once()
                result = callback.call_args[0][0]
                self.assertTrue(result.success)
                self.assertEqual(result.object_ref, "myLD/CSWI1.Pos")

    def test_trigger_with_nonzero_error(self):
        """trigger() with non-zero lastApplError must set success=False."""
        callback = Mock()
        handler = self._make_handler(callback)
        handler._libiec61850_control_object_client = Mock()

        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_getLastApplError.return_value = 3
                handler.trigger()

                result = callback.call_args[0][0]
                self.assertFalse(result.success)
                self.assertEqual(result.last_error, 3)


class TestControlClientCrashPaths(unittest.TestCase):
    """Test ControlClient crash paths."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_get_or_create_control_null_return(self):
        """ControlObjectClient_create returning NULL must raise ControlError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = None

                from pyiec61850.mms.control import ControlClient, ControlError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(ControlError):
                    ctrl._get_or_create_control("test")

    def test_operate_unsupported_value_type(self):
        """operate() with unsupported value type must raise OperateError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient, OperateError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(OperateError):
                    ctrl.operate("test", {"unsupported": True})

    def test_select_with_value_unsupported_type(self):
        """select_with_value() with unsupported value type must raise SelectError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient, SelectError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(SelectError):
                    ctrl.select_with_value("test", {"unsupported": True})

    def test_select_with_value_server_rejects(self):
        """select_with_value() rejected by server must raise SelectError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.MmsValue_newBoolean.return_value = Mock()
                mock_iec.ControlObjectClient_selectWithValue.return_value = False

                from pyiec61850.mms.control import ControlClient, SelectError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(SelectError):
                    ctrl.select_with_value("test", True)

    def test_get_control_model_success(self):
        """get_control_model must return model from C function."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.ControlObjectClient_getControlModel.return_value = 2

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                model = ctrl.get_control_model("test")
                self.assertEqual(model, 2)

    def test_get_control_model_exception(self):
        """get_control_model exception must raise ControlError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.ControlObjectClient_getControlModel.side_effect = RuntimeError("fail")

                from pyiec61850.mms.control import ControlClient, ControlError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(ControlError):
                    ctrl.get_control_model("test")

    def test_set_command_term_handler_not_callable(self):
        """set_command_termination_handler with non-callable must raise ControlError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()

                from pyiec61850.mms.control import ControlClient, ControlError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(ControlError):
                    ctrl.set_command_termination_handler("test", "not callable")

    def test_set_command_term_handler_with_director(self):
        """set_command_termination_handler with director classes."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.CommandTermHandler = type(
                    "CommandTermHandler", (), {"__init__": lambda self: None}
                )
                mock_subscriber_instance = Mock()
                mock_subscriber_instance.subscribe.return_value = True
                mock_iec.CommandTermSubscriber.return_value = mock_subscriber_instance

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                ctrl.set_command_termination_handler("test", Mock())

                self.assertIn("test", ctrl._command_term_handlers)

    def test_set_command_term_handler_subscribe_fails(self):
        """subscribe() returning False must raise ControlError."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.CommandTermHandler = type(
                    "CommandTermHandler", (), {"__init__": lambda self: None}
                )
                mock_subscriber_instance = Mock()
                mock_subscriber_instance.subscribe.return_value = False
                mock_iec.CommandTermSubscriber.return_value = mock_subscriber_instance

                from pyiec61850.mms.control import ControlClient, ControlError

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                with self.assertRaises(ControlError):
                    ctrl.set_command_termination_handler("test", Mock())

    def test_release_destroy_exception_still_removes(self):
        """If ControlObjectClient_destroy throws, object must still be removed."""
        with patch("pyiec61850.mms.control._HAS_IEC61850", True):
            with patch("pyiec61850.mms.control.iec61850") as mock_iec:
                mock_iec.ControlObjectClient_create.return_value = Mock()
                mock_iec.ControlObjectClient_destroy.side_effect = RuntimeError("fail")

                from pyiec61850.mms.control import ControlClient

                client = self._make_mock_mms_client()
                ctrl = ControlClient(client)
                ctrl._get_or_create_control("test")
                ctrl.release("test")  # Must not raise

                self.assertNotIn("test", ctrl._control_objects)


class TestServerControlHandler(unittest.TestCase):
    """Test _PyControlHandler in server module."""

    def test_trigger_with_missing_attributes_no_crash(self):
        """trigger() must not crash with missing C++ attributes."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                del mock_iec.ControlHandlerForPython

                from pyiec61850.server.server import _PyControlHandler

                callback = Mock(return_value=0)
                handler = _PyControlHandler(callback, "myLD/CSWI1.Pos")
                handler.trigger()  # Must not crash

                callback.assert_called_once()

    def test_trigger_callback_exception_no_crash(self):
        """trigger() must catch callback exceptions."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                del mock_iec.ControlHandlerForPython

                from pyiec61850.server.server import _PyControlHandler

                callback = Mock(side_effect=RuntimeError("boom"))
                handler = _PyControlHandler(callback, "test")
                handler.trigger()  # Must not raise

    def test_trigger_null_callback_no_crash(self):
        """trigger() with None callback must not crash."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                del mock_iec.ControlHandlerForPython

                from pyiec61850.server.server import _PyControlHandler

                handler = _PyControlHandler(None, "test")
                handler._callback = None
                handler.trigger()  # Must not raise


if __name__ == "__main__":
    unittest.main()
