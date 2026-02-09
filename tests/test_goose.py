#!/usr/bin/env python3
"""
Tests for pyiec61850.goose module - GOOSE publish/subscribe.

All tests use mocks since the C library isn't available in dev.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import logging

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
            LibraryNotFoundError,
            InterfaceError,
            SubscriptionError,
            PublishError,
            ConfigurationError,
            NotStartedError,
            AlreadyStartedError,
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
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', False):
            from pyiec61850.goose import GooseSubscriber, LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")

    def test_raises_on_empty_interface(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, ConfigurationError
                with self.assertRaises(ConfigurationError):
                    GooseSubscriber("", "myIED/LLN0$GO$gcb01")

    def test_raises_on_empty_go_cb_ref(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, ConfigurationError
                with self.assertRaises(ConfigurationError):
                    GooseSubscriber("eth0", "")

    def test_creation_success(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01")
                self.assertEqual(sub.interface, "eth0")
                self.assertEqual(sub.go_cb_ref, "myIED/LLN0$GO$gcb01")
                self.assertFalse(sub.is_running)

    def test_set_app_id_valid(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "test")
                sub.set_app_id(0x1000)
                self.assertEqual(sub._app_id, 0x1000)

    def test_set_app_id_out_of_range(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, ConfigurationError
                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_app_id(0x10000)

    def test_set_app_id_while_running(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, AlreadyStartedError
                sub = GooseSubscriber("eth0", "test")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.set_app_id(0x1000)

    def test_set_dst_mac_valid(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "test")
                mac = b"\x01\x0c\xcd\x01\x00\x00"
                sub.set_dst_mac(mac)
                self.assertEqual(sub._dst_mac, mac)

    def test_set_dst_mac_invalid(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, ConfigurationError
                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_dst_mac(b"\x01\x02")  # Too short

    def test_set_listener(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "test")
                callback = Mock()
                sub.set_listener(callback)
                self.assertEqual(sub._listener, callback)

    def test_set_listener_not_callable(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, ConfigurationError
                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(ConfigurationError):
                    sub.set_listener("not_callable")

    def test_start_success(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850') as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = True

                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "test")
                sub.start()
                self.assertTrue(sub.is_running)

                mock_iec.GooseReceiver_start.assert_called_once()

    def test_start_already_running(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber, AlreadyStartedError
                sub = GooseSubscriber("eth0", "test")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.start()

    def test_start_receiver_failed(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850') as mock_iec:
                mock_iec.GooseSubscriber_create.return_value = Mock()
                mock_iec.GooseReceiver_create.return_value = Mock()
                mock_iec.GooseReceiver_isRunning.return_value = False

                from pyiec61850.goose import GooseSubscriber, InterfaceError
                sub = GooseSubscriber("eth0", "test")
                with self.assertRaises(InterfaceError):
                    sub.start()

    def test_stop(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850') as mock_iec:
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
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850'):
                from pyiec61850.goose import GooseSubscriber
                sub = GooseSubscriber("eth0", "test")
                sub.stop()  # Should not raise
                self.assertFalse(sub.is_running)

    def test_context_manager(self):
        with patch('pyiec61850.goose.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.goose.subscriber.iec61850') as mock_iec:
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
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', False):
            from pyiec61850.goose import GoosePublisher, LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                GoosePublisher("eth0")

    def test_creation_success(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher
                pub = GoosePublisher("eth0")
                self.assertEqual(pub.interface, "eth0")
                self.assertFalse(pub.is_running)

    def test_set_app_id(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher
                pub = GoosePublisher("eth0")
                pub.set_app_id(0x2000)
                self.assertEqual(pub._app_id, 0x2000)

    def test_set_vlan(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher
                pub = GoosePublisher("eth0")
                pub.set_vlan(100, 6)
                self.assertEqual(pub._vlan_id, 100)
                self.assertEqual(pub._vlan_priority, 6)

    def test_set_vlan_out_of_range(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher, ConfigurationError
                pub = GoosePublisher("eth0")
                with self.assertRaises(ConfigurationError):
                    pub.set_vlan(5000)  # Over 4095

    def test_start_success(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850') as mock_iec:
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
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher, AlreadyStartedError
                pub = GoosePublisher("eth0")
                pub._running = True
                with self.assertRaises(AlreadyStartedError):
                    pub.start()

    def test_publish_not_started(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850'):
                from pyiec61850.goose import GoosePublisher, NotStartedError
                pub = GoosePublisher("eth0")
                with self.assertRaises(NotStartedError):
                    pub.publish([True, 42])

    def test_stop(self):
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850') as mock_iec:
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
        with patch('pyiec61850.goose.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.goose.publisher.iec61850') as mock_iec:
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


if __name__ == '__main__':
    unittest.main()
