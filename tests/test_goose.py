#!/usr/bin/env python3
"""
Tests for pyiec61850.goose module - GOOSE publish/subscribe.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestGooseImports(unittest.TestCase):
    """Test GOOSE module imports."""

    def test_import_module(self):
        from pyiec61850 import goose

        self.assertIsNotNone(goose)

    def test_import_subscriber(self):
        from pyiec61850.goose import GooseSubscriber

        self.assertIsNotNone(GooseSubscriber)

    def test_import_publisher(self):
        from pyiec61850.goose import GoosePublisher

        self.assertIsNotNone(GoosePublisher)

    def test_import_types(self):
        from pyiec61850.goose import GooseMessage, GoosePublisherConfig, GooseSubscriberConfig

        self.assertIsNotNone(GooseMessage)
        self.assertIsNotNone(GoosePublisherConfig)
        self.assertIsNotNone(GooseSubscriberConfig)

    def test_import_exceptions(self):
        from pyiec61850.goose import (
            GooseError,
            InterfaceError,
            PublishError,
        )

        self.assertTrue(issubclass(InterfaceError, GooseError))
        self.assertTrue(issubclass(PublishError, GooseError))


class TestGooseMessage(unittest.TestCase):
    """Test GooseMessage dataclass."""

    def test_default_creation(self):
        from pyiec61850.goose import GooseMessage

        msg = GooseMessage()
        self.assertEqual(msg.go_cb_ref, "")
        self.assertTrue(msg.is_valid)
        self.assertEqual(msg.st_num, 0)
        self.assertEqual(msg.values, [])

    def test_creation_with_values(self):
        from pyiec61850.goose import GooseMessage

        msg = GooseMessage(
            go_cb_ref="myIED/LLN0$GO$gcb01",
            st_num=5,
            sq_num=10,
            app_id=0x1000,
            values=[True, 42, 3.14],
        )
        self.assertEqual(msg.go_cb_ref, "myIED/LLN0$GO$gcb01")
        self.assertEqual(msg.st_num, 5)
        self.assertEqual(len(msg.values), 3)

    def test_to_dict(self):
        from pyiec61850.goose import GooseMessage

        msg = GooseMessage(go_cb_ref="test", st_num=1)
        d = msg.to_dict()
        self.assertEqual(d["go_cb_ref"], "test")
        self.assertEqual(d["st_num"], 1)


class TestGooseSubscriber(unittest.TestCase):
    """Test GooseSubscriber class."""

    def test_raises_without_library(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", False):
            from pyiec61850.goose import GooseSubscriber, LibraryNotFoundError

            with self.assertRaises(LibraryNotFoundError):
                GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")

    def test_raises_on_empty_interface(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import ConfigurationError, GooseSubscriber

                with self.assertRaises(ConfigurationError):
                    GooseSubscriber("", "myIED/LLN0$GO$gcb01")

    def test_raises_on_empty_go_cb_ref(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import ConfigurationError, GooseSubscriber

                with self.assertRaises(ConfigurationError):
                    GooseSubscriber("eth0", "")

    def test_creation_success(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")
                self.assertEqual(sub.interface, "eth0")
                self.assertEqual(sub.go_cb_ref, "myIED/LLN0$GO$gcb01")
                self.assertFalse(sub.is_running)

    def test_set_app_id_valid(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub.set_app_id(0x1000)
                self.assertEqual(sub._app_id, 0x1000)

    def test_set_app_id_out_of_range(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import ConfigurationError, GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_app_id(0x10000)

    def test_set_app_id_while_running(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import AlreadyStartedError, GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.set_app_id(0x1000)

    def test_set_dst_mac_valid(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                mac = b"\x01\x0c\xcd\x01\x00\x00"
                sub.set_dst_mac(mac)
                self.assertEqual(sub._dst_mac, mac)

    def test_set_dst_mac_invalid(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import ConfigurationError, GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_dst_mac(b"\x01\x02")  # Too short

    def test_set_listener(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                callback = Mock()
                sub.set_listener(callback)
                self.assertEqual(sub._listener, callback)

    def test_set_listener_not_callable(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import ConfigurationError, GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_listener("not_callable")

    def test_start_success(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = True

                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub.start()
                self.assertTrue(sub.is_running)

                mock_iec.GooseReceiver_start.assert_called_once()

    def test_start_subscriber_create_returns_null(self):
        """GooseSubscriber_create returning NULL must raise SubscriptionError."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = None

                from pyiec61850.goose import GooseSubscriber, SubscriptionError

                sub = GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")
                with self.assertRaises(SubscriptionError):
                    sub.start()

    def test_start_receiver_create_returns_null(self):
        """GooseReceiver_create returning NULL must raise SubscriptionError."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = None

                from pyiec61850.goose import GooseSubscriber, SubscriptionError

                sub = GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")
                with self.assertRaises(SubscriptionError):
                    sub.start()

    def test_start_already_running(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import AlreadyStartedError, GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.start()

    def test_start_receiver_failed(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = False

                from pyiec61850.goose import GooseSubscriber, InterfaceError

                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(InterfaceError):
                    sub.start()

    def test_stop(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_receiver = Mock()
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = mock_receiver
                mock_iec.GooseReceiver_isRunning.return_value = True

                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub.start()
                sub.stop()

                self.assertFalse(sub.is_running)
                mock_iec.GooseReceiver_stop.assert_called_once()
                mock_iec.GooseReceiver_destroy.assert_called_once()

    def test_stop_when_not_running(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test")
                sub.stop()  # Should not raise
                self.assertFalse(sub.is_running)

    def test_context_manager(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = True

                from pyiec61850.goose import GooseSubscriber

                with GooseSubscriber("eth0", "test") as sub:
                    sub.start()
                    self.assertTrue(sub.is_running)

                # Should be stopped after exiting context
                self.assertFalse(sub.is_running)


class TestGoosePublisher(unittest.TestCase):
    """Test GoosePublisher class."""

    def test_raises_without_library(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", False):
            from pyiec61850.goose import GoosePublisher, LibraryNotFoundError

            with self.assertRaises(LibraryNotFoundError):
                GoosePublisher("eth0")

    def test_creation_success(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                self.assertEqual(pub.interface, "eth0")
                self.assertFalse(pub.is_running)

    def test_set_app_id(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub.set_app_id(0x2000)
                self.assertEqual(pub._app_id, 0x2000)

    def test_set_vlan(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub.set_vlan(100, 6)
                self.assertEqual(pub._vlan_id, 100)
                self.assertEqual(pub._vlan_priority, 6)

    def test_set_vlan_out_of_range(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import ConfigurationError, GoosePublisher

                pub = GoosePublisher("eth0")
                with self.assertRaises(ConfigurationError):
                    pub.set_vlan(5000)  # Over 4095

    def test_start_success(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_iec.GoosePublisher_createEx.return_value = Mock()

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub.set_go_cb_ref("test")
                pub.start()

                self.assertTrue(pub.is_running)

    def test_start_already_running(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import AlreadyStartedError, GoosePublisher

                pub = GoosePublisher("eth0")
                pub._running = True
                with self.assertRaises(AlreadyStartedError):
                    pub.start()

    def test_publish_not_started(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher, NotStartedError

                pub = GoosePublisher("eth0")
                with self.assertRaises(NotStartedError):
                    pub.publish([True, 42])

    def test_stop(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_pub = Mock()
                mock_iec.GoosePublisher_createEx.return_value = mock_pub

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub.start()
                pub.stop()

                self.assertFalse(pub.is_running)
                mock_iec.GoosePublisher_destroy.assert_called_once()

    def test_context_manager(self):
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_iec.GoosePublisher_createEx.return_value = Mock()

                from pyiec61850.goose import GoosePublisher

                with GoosePublisher("eth0") as pub:
                    pub.start()

                mock_iec.GoosePublisher_destroy.assert_called()


class TestGoosePublisherConfig(unittest.TestCase):
    """Test GoosePublisherConfig dataclass."""

    def test_default_values(self):
        from pyiec61850.goose import GoosePublisherConfig

        cfg = GoosePublisherConfig()
        self.assertEqual(cfg.interface, "eth0")
        self.assertEqual(cfg.app_id, 0x1000)
        self.assertEqual(cfg.vlan_priority, 4)

    def test_to_dict(self):
        from pyiec61850.goose import GoosePublisherConfig

        cfg = GoosePublisherConfig(interface="eth1", app_id=0x2000)
        d = cfg.to_dict()
        self.assertEqual(d["interface"], "eth1")
        self.assertEqual(d["app_id"], 0x2000)


class TestGooseSubscriberTriggerCrashPaths(unittest.TestCase):
    """Test _PyGooseHandler.trigger() crash paths.

    trigger() runs in C++ context -- any unhandled exception = segfault.
    These tests verify all paths are guarded.
    """

    def _make_handler(self, callback=None):
        """Create a _PyGooseHandler with mocked base class."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose.subscriber import _PyGooseHandler

                handler = _PyGooseHandler(callback or Mock(), "test/GO$gcb01")
                return handler

    def test_trigger_with_null_subscriber_no_crash(self):
        """trigger() must not crash when _libiec61850_goose_subscriber is missing."""
        handler = self._make_handler()
        # Do NOT set _libiec61850_goose_subscriber -- simulates NULL subscriber
        handler.trigger()  # Must not raise

    def test_trigger_with_subscriber_attribute_error_no_crash(self):
        """trigger() must survive AttributeError on subscriber access."""
        handler = self._make_handler()
        # Accessing self._libiec61850_goose_subscriber will raise AttributeError
        handler.trigger()  # Must not raise

    def test_trigger_callback_exception_no_crash(self):
        """trigger() must catch callback exceptions (not propagate to C++)."""
        callback = Mock(side_effect=RuntimeError("user callback exploded"))
        handler = self._make_handler(callback)
        mock_sub = Mock()
        handler._libiec61850_goose_subscriber = mock_sub

        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_getStNum.return_value = 1
                mock_iec.GooseSubscriber_getSqNum.return_value = 0
                mock_iec.GooseSubscriber_isValid.return_value = True
                mock_iec.GooseSubscriber_getConfRev.return_value = 1
                mock_iec.GooseSubscriber_needsCommissioning.return_value = False
                mock_iec.GooseSubscriber_getTimeAllowedToLive.return_value = 2000
                mock_iec.GooseSubscriber_getNumberOfDataSetEntries.return_value = 0
                mock_iec.GooseSubscriber_getGoId.return_value = ""
                mock_iec.GooseSubscriber_getDataSet.return_value = ""
                mock_iec.GooseSubscriber_getDataSetValues.return_value = None
                handler.trigger()  # Must not raise despite callback crash

    def test_trigger_with_null_callback_no_crash(self):
        """trigger() must handle None callback gracefully."""
        handler = self._make_handler(callback=None)
        handler._callback = None
        mock_sub = Mock()
        handler._libiec61850_goose_subscriber = mock_sub

        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_getStNum.return_value = 1
                mock_iec.GooseSubscriber_getSqNum.return_value = 0
                mock_iec.GooseSubscriber_isValid.return_value = True
                mock_iec.GooseSubscriber_getConfRev.return_value = 1
                mock_iec.GooseSubscriber_needsCommissioning.return_value = False
                mock_iec.GooseSubscriber_getTimeAllowedToLive.return_value = 2000
                mock_iec.GooseSubscriber_getNumberOfDataSetEntries.return_value = 0
                mock_iec.GooseSubscriber_getGoId.return_value = ""
                mock_iec.GooseSubscriber_getDataSet.return_value = ""
                mock_iec.GooseSubscriber_getDataSetValues.return_value = None
                handler.trigger()  # Must not raise

    def test_trigger_extracts_data_set_values(self):
        """trigger() must extract MMS values from data set without crash."""
        callback = Mock()
        handler = self._make_handler(callback)
        mock_sub = Mock()
        handler._libiec61850_goose_subscriber = mock_sub

        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_getStNum.return_value = 1
                mock_iec.GooseSubscriber_getSqNum.return_value = 0
                mock_iec.GooseSubscriber_isValid.return_value = True
                mock_iec.GooseSubscriber_getConfRev.return_value = 1
                mock_iec.GooseSubscriber_needsCommissioning.return_value = False
                mock_iec.GooseSubscriber_getTimeAllowedToLive.return_value = 2000
                mock_iec.GooseSubscriber_getNumberOfDataSetEntries.return_value = 2
                mock_iec.GooseSubscriber_getGoId.return_value = "test"
                mock_iec.GooseSubscriber_getDataSet.return_value = "ds"
                mock_ds = Mock()
                mock_iec.GooseSubscriber_getDataSetValues.return_value = mock_ds
                mock_elem = Mock()
                mock_iec.MmsValue_getElement.return_value = mock_elem
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MmsValue_getType.return_value = 2
                mock_iec.MmsValue_getBoolean.return_value = True
                handler.trigger()

                callback.assert_called_once()
                msg = callback.call_args[0][0]
                self.assertEqual(len(msg.values), 2)

    def test_trigger_null_data_set_values_no_crash(self):
        """trigger() with NULL getDataSetValues must not crash."""
        callback = Mock()
        handler = self._make_handler(callback)
        mock_sub = Mock()
        handler._libiec61850_goose_subscriber = mock_sub

        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_getStNum.return_value = 0
                mock_iec.GooseSubscriber_getSqNum.return_value = 0
                mock_iec.GooseSubscriber_isValid.return_value = True
                mock_iec.GooseSubscriber_getConfRev.return_value = 1
                mock_iec.GooseSubscriber_needsCommissioning.return_value = False
                mock_iec.GooseSubscriber_getTimeAllowedToLive.return_value = 2000
                mock_iec.GooseSubscriber_getNumberOfDataSetEntries.return_value = 0
                mock_iec.GooseSubscriber_getGoId.return_value = ""
                mock_iec.GooseSubscriber_getDataSet.return_value = ""
                mock_iec.GooseSubscriber_getDataSetValues.return_value = None
                handler.trigger()

                callback.assert_called_once()
                msg = callback.call_args[0][0]
                self.assertEqual(msg.values, [])

    def test_trigger_null_element_skipped(self):
        """trigger() must skip NULL elements in data set."""
        callback = Mock()
        handler = self._make_handler(callback)
        mock_sub = Mock()
        handler._libiec61850_goose_subscriber = mock_sub

        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_getStNum.return_value = 0
                mock_iec.GooseSubscriber_getSqNum.return_value = 0
                mock_iec.GooseSubscriber_isValid.return_value = True
                mock_iec.GooseSubscriber_getConfRev.return_value = 1
                mock_iec.GooseSubscriber_needsCommissioning.return_value = False
                mock_iec.GooseSubscriber_getTimeAllowedToLive.return_value = 2000
                mock_iec.GooseSubscriber_getNumberOfDataSetEntries.return_value = 2
                mock_iec.GooseSubscriber_getGoId.return_value = ""
                mock_iec.GooseSubscriber_getDataSet.return_value = ""
                mock_ds = Mock()
                mock_iec.GooseSubscriber_getDataSetValues.return_value = mock_ds
                # First element is NULL, second is valid
                mock_iec.MmsValue_getElement.side_effect = [None, Mock()]
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MmsValue_getType.return_value = 2
                mock_iec.MmsValue_getBoolean.return_value = True
                handler.trigger()

                callback.assert_called_once()
                msg = callback.call_args[0][0]
                # Only the valid (non-NULL) element should be extracted
                self.assertEqual(len(msg.values), 1)


class TestExtractMmsValue(unittest.TestCase):
    """Test _extract_mms_value with various MMS types and NULL."""

    def test_extract_null_returns_none(self):
        """NULL MmsValue must return None."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            from pyiec61850.goose.subscriber import _extract_mms_value

            result = _extract_mms_value(None)
            self.assertIsNone(result)

    def test_extract_no_library_returns_none(self):
        """Without library must return None."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", False):
            from pyiec61850.goose.subscriber import _extract_mms_value

            result = _extract_mms_value(Mock())
            self.assertIsNone(result)

    def test_extract_boolean_value(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MmsValue_getType.return_value = 2
                mock_iec.MmsValue_getBoolean.return_value = True

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertTrue(result)

    def test_extract_integer_value(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MMS_INTEGER = 4
                mock_iec.MmsValue_getType.return_value = 4
                mock_iec.MmsValue_toInt32.return_value = 42

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertEqual(result, 42)

    def test_extract_float_value(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MMS_INTEGER = 4
                mock_iec.MMS_UNSIGNED = 5
                mock_iec.MMS_FLOAT = 6
                mock_iec.MmsValue_getType.return_value = 6
                mock_iec.MmsValue_toFloat.return_value = 3.14

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertAlmostEqual(result, 3.14)

    def test_extract_string_value(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MMS_INTEGER = 4
                mock_iec.MMS_UNSIGNED = 5
                mock_iec.MMS_FLOAT = 6
                mock_iec.MMS_BIT_STRING = 3
                mock_iec.MMS_VISIBLE_STRING = 8
                mock_iec.MMS_STRING = 13
                mock_iec.MmsValue_getType.return_value = 8
                mock_iec.MmsValue_toString.return_value = "hello"

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertEqual(result, "hello")

    def test_extract_unknown_type_returns_none(self):
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MMS_BOOLEAN = 2
                mock_iec.MMS_INTEGER = 4
                mock_iec.MMS_UNSIGNED = 5
                mock_iec.MMS_FLOAT = 6
                mock_iec.MMS_BIT_STRING = 3
                mock_iec.MMS_VISIBLE_STRING = 8
                mock_iec.MMS_STRING = 13
                mock_iec.MmsValue_getType.return_value = 99

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertIsNone(result)

    def test_extract_exception_returns_none(self):
        """If getType() throws, return None instead of crashing."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.MmsValue_getType.side_effect = RuntimeError("segfault avoided")

                from pyiec61850.goose.subscriber import _extract_mms_value

                result = _extract_mms_value(Mock())
                self.assertIsNone(result)


class TestGooseSubscriberCleanupOrdering(unittest.TestCase):
    """Test _cleanup() ordering -- destroy after unsubscribe, no double-free."""

    def test_cleanup_after_partial_start_subscriber_only(self):
        """If receiver creation fails, cleanup must free the subscriber."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = None

                from pyiec61850.goose import GooseSubscriber, SubscriptionError

                sub = GooseSubscriber("eth0", "test/GO$gcb01")
                with self.assertRaises(SubscriptionError):
                    sub.start()

                # Both receiver and subscriber must be cleaned up
                self.assertIsNone(sub._receiver)
                self.assertIsNone(sub._subscriber)

    def test_cleanup_severs_director_link_before_destroy(self):
        """Director link (deleteEventHandler) must be severed before receiver destroy."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = True
                mock_iec.GooseHandler = type("GooseHandler", (), {"__init__": lambda self: None})

                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test/GO$gcb01")
                sub.set_listener(Mock())
                # Manually set SWIG handler references to test cleanup ordering
                mock_goose_sub_py = Mock()
                sub._goose_subscriber_py = mock_goose_sub_py
                mock_handler = Mock()
                mock_handler.thisown = 1
                sub._goose_handler = mock_handler
                sub._running = True
                sub._receiver = Mock()

                sub.stop()

                # deleteEventHandler should have been called
                mock_goose_sub_py.deleteEventHandler.assert_called_once()
                self.assertIsNone(sub._goose_subscriber_py)
                self.assertIsNone(sub._goose_handler)

    def test_cleanup_handles_delete_event_handler_exception(self):
        """If deleteEventHandler raises, cleanup must continue."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850"):
                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test/GO$gcb01")
                sub._running = True
                sub._receiver = Mock()
                sub._subscriber = Mock()
                mock_goose_sub_py = Mock()
                mock_goose_sub_py.deleteEventHandler.side_effect = RuntimeError("boom")
                sub._goose_subscriber_py = mock_goose_sub_py

                sub.stop()  # Must not raise

                self.assertFalse(sub.is_running)
                self.assertIsNone(sub._receiver)

    def test_stop_receiver_stop_exception_still_cleans_up(self):
        """If GooseReceiver_stop throws, cleanup must still happen."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseReceiver_stop.side_effect = RuntimeError("stop failed")

                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test/GO$gcb01")
                sub._running = True
                sub._receiver = Mock()
                sub._subscriber = Mock()

                sub.stop()  # Must not raise

                self.assertFalse(sub.is_running)
                mock_iec.GooseReceiver_destroy.assert_called_once()

    def test_double_stop_no_crash(self):
        """Calling stop() twice must not crash."""
        with patch("pyiec61850.goose.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.goose.subscriber.iec61850") as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = True

                from pyiec61850.goose import GooseSubscriber

                sub = GooseSubscriber("eth0", "test/GO$gcb01")
                sub.start()
                sub.stop()
                sub.stop()  # Second stop must be no-op

                self.assertFalse(sub.is_running)


class TestGoosePublisherCrashPaths(unittest.TestCase):
    """Test GoosePublisher crash paths: start, publish, stop, cleanup."""

    def test_start_comm_params_returns_null(self):
        """CommParameters() returning NULL must raise PublishError."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_iec.CommParameters.return_value = None

                from pyiec61850.goose import GoosePublisher, PublishError

                pub = GoosePublisher("eth0")
                with self.assertRaises(PublishError):
                    pub.start()

    def test_start_publisher_create_returns_null(self):
        """GoosePublisher_createEx returning NULL must raise PublishError."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_iec.GoosePublisher_createEx.return_value = None

                from pyiec61850.goose import GoosePublisher, PublishError

                pub = GoosePublisher("eth0")
                with self.assertRaises(PublishError):
                    pub.start()

    def test_start_unexpected_exception_triggers_cleanup(self):
        """Unexpected exception during start must trigger _cleanup."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_iec.GoosePublisher_createEx.return_value = Mock()
                mock_iec.GoosePublisher_setGoCbRef.side_effect = RuntimeError("boom")

                from pyiec61850.goose import GoosePublisher, PublishError

                pub = GoosePublisher("eth0")
                pub.set_go_cb_ref("test")
                with self.assertRaises(PublishError):
                    pub.start()

                self.assertIsNone(pub._publisher)

    def test_publish_linked_list_create_null(self):
        """LinkedList_create returning NULL must raise PublishError."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_iec.LinkedList_create.return_value = None

                from pyiec61850.goose import GoosePublisher, PublishError

                pub = GoosePublisher("eth0")
                pub._running = True
                pub._publisher = Mock()
                with self.assertRaises(PublishError):
                    pub.publish([True, 42])

    def test_publish_success(self):
        """Successful publish path."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_list = Mock()
                mock_iec.LinkedList_create.return_value = mock_list
                mock_iec.MmsValue_newBoolean.return_value = Mock()
                mock_iec.MmsValue_newIntegerFromInt32.return_value = Mock()
                mock_iec.GoosePublisher_publish.return_value = 0

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub._running = True
                pub._publisher = Mock()
                pub.publish([True, 42])

                mock_iec.LinkedList_destroyDeep.assert_called_once()

    def test_publish_error_code_from_c(self):
        """GoosePublisher_publish returning non-zero must raise PublishError."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_list = Mock()
                mock_iec.LinkedList_create.return_value = mock_list
                mock_iec.MmsValue_newBoolean.return_value = Mock()
                mock_iec.GoosePublisher_publish.return_value = -1

                from pyiec61850.goose import GoosePublisher, PublishError

                pub = GoosePublisher("eth0")
                pub._running = True
                pub._publisher = Mock()
                with self.assertRaises(PublishError):
                    pub.publish([True])

    def test_publish_cleanup_falls_back_to_shallow_destroy(self):
        """If destroyDeep fails, must fall back to LinkedList_destroy."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_list = Mock()
                mock_iec.LinkedList_create.return_value = mock_list
                mock_iec.MmsValue_newBoolean.return_value = Mock()
                mock_iec.GoosePublisher_publish.return_value = 0
                mock_iec.LinkedList_destroyDeep.side_effect = RuntimeError("no deep destroy")

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub._running = True
                pub._publisher = Mock()
                pub.publish([True])  # Must not raise

                mock_iec.LinkedList_destroy.assert_called_once_with(mock_list)

    def test_cleanup_destroy_exception_still_clears(self):
        """If GoosePublisher_destroy throws, references must still be cleared."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_iec.GoosePublisher_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub._running = True
                pub._publisher = Mock()

                pub.stop()  # Must not raise

                self.assertIsNone(pub._publisher)
                self.assertFalse(pub.is_running)

    def test_create_mms_value_unsupported_type(self):
        """_create_mms_value with unsupported type must return None."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                result = pub._create_mms_value({"unsupported": True})
                self.assertIsNone(result)

    def test_increase_st_num_not_started(self):
        """increase_st_num when not started must raise NotStartedError."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850"):
                from pyiec61850.goose import GoosePublisher, NotStartedError

                pub = GoosePublisher("eth0")
                with self.assertRaises(NotStartedError):
                    pub.increase_st_num()

    def test_double_stop_no_crash(self):
        """Calling stop() twice must not crash."""
        with patch("pyiec61850.goose.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.goose.publisher.iec61850") as mock_iec:
                mock_comm = Mock()
                mock_comm.dstAddress = [0] * 6
                mock_iec.CommParameters.return_value = mock_comm
                mock_iec.GoosePublisher_createEx.return_value = Mock()

                from pyiec61850.goose import GoosePublisher

                pub = GoosePublisher("eth0")
                pub.start()
                pub.stop()
                pub.stop()  # Must be no-op
                self.assertFalse(pub.is_running)


if __name__ == "__main__":
    unittest.main()
