#!/usr/bin/env python3
"""
Tests for pyiec61850.sv module - Sampled Values publish/subscribe.

All tests use mocks since the C library isn't available in dev.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

logging.disable(logging.CRITICAL)


class TestSVImports(unittest.TestCase):
    """Test SV module imports."""

    def test_import_module(self):
        from pyiec61850 import sv
        self.assertIsNotNone(sv)

    def test_import_subscriber(self):
        from pyiec61850.sv import SVSubscriber
        self.assertIsNotNone(SVSubscriber)

    def test_import_publisher(self):
        from pyiec61850.sv import SVPublisher
        self.assertIsNotNone(SVPublisher)

    def test_import_types(self):
        from pyiec61850.sv import SVMessage, SVPublisherConfig, SVSubscriberConfig
        self.assertIsNotNone(SVMessage)

    def test_import_exceptions(self):
        from pyiec61850.sv import (
            SVError, LibraryNotFoundError, InterfaceError,
            SubscriptionError, PublishError, ConfigurationError,
            NotStartedError, AlreadyStartedError,
        )
        self.assertTrue(issubclass(PublishError, SVError))


class TestSVMessage(unittest.TestCase):
    """Test SVMessage dataclass."""

    def test_default_creation(self):
        from pyiec61850.sv import SVMessage
        msg = SVMessage()
        self.assertEqual(msg.sv_id, "")
        self.assertEqual(msg.smp_cnt, 0)
        self.assertEqual(msg.values, [])

    def test_creation_with_values(self):
        from pyiec61850.sv import SVMessage
        msg = SVMessage(sv_id="test", smp_cnt=42, values=[1.0, 2.0, 3.0])
        self.assertEqual(msg.sv_id, "test")
        self.assertEqual(len(msg.values), 3)

    def test_to_dict(self):
        from pyiec61850.sv import SVMessage
        msg = SVMessage(sv_id="test", smp_cnt=42)
        d = msg.to_dict()
        self.assertEqual(d["sv_id"], "test")
        self.assertEqual(d["smp_cnt"], 42)


class TestSVSubscriber(unittest.TestCase):
    """Test SVSubscriber class."""

    def test_raises_without_library(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', False):
            from pyiec61850.sv import SVSubscriber, LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                SVSubscriber("eth0")

    def test_raises_on_empty_interface(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber, ConfigurationError
                with self.assertRaises(ConfigurationError):
                    SVSubscriber("")

    def test_creation_success(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber
                sub = SVSubscriber("eth0")
                self.assertEqual(sub.interface, "eth0")
                self.assertFalse(sub.is_running)

    def test_set_app_id_valid(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber
                sub = SVSubscriber("eth0")
                sub.set_app_id(0x4000)
                self.assertEqual(sub._app_id, 0x4000)

    def test_set_app_id_out_of_range(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber, ConfigurationError
                sub = SVSubscriber("eth0")
                with self.assertRaises(ConfigurationError):
                    sub.set_app_id(-1)

    def test_set_listener(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber
                sub = SVSubscriber("eth0")
                cb = Mock()
                sub.set_listener(cb)
                self.assertEqual(sub._listener, cb)

    def test_start_success(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850') as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber
                sub = SVSubscriber("eth0")
                sub.start()
                self.assertTrue(sub.is_running)

    def test_start_already_running(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber, AlreadyStartedError
                sub = SVSubscriber("eth0")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.start()

    def test_start_receiver_failed(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850') as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = False

                from pyiec61850.sv import SVSubscriber, InterfaceError
                sub = SVSubscriber("eth0")
                with self.assertRaises(InterfaceError):
                    sub.start()

    def test_read_current_values_not_started(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850'):
                from pyiec61850.sv import SVSubscriber, NotStartedError
                sub = SVSubscriber("eth0")
                with self.assertRaises(NotStartedError):
                    sub.read_current_values()

    def test_stop(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850') as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber
                sub = SVSubscriber("eth0")
                sub.start()
                sub.stop()

                self.assertFalse(sub.is_running)
                mock_iec.SVReceiver_stop.assert_called_once()

    def test_context_manager(self):
        with patch('pyiec61850.sv.subscriber._HAS_IEC61850', True):
            with patch('pyiec61850.sv.subscriber.iec61850') as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber
                with SVSubscriber("eth0") as sub:
                    sub.start()
                self.assertFalse(sub.is_running)


class TestSVPublisher(unittest.TestCase):
    """Test SVPublisher class."""

    def test_raises_without_library(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', False):
            from pyiec61850.sv import SVPublisher, LibraryNotFoundError
            with self.assertRaises(LibraryNotFoundError):
                SVPublisher("eth0")

    def test_creation_success(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850'):
                from pyiec61850.sv import SVPublisher
                pub = SVPublisher("eth0")
                self.assertEqual(pub.interface, "eth0")
                self.assertFalse(pub.is_running)

    def test_set_sv_id(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850'):
                from pyiec61850.sv import SVPublisher
                pub = SVPublisher("eth0")
                pub.set_sv_id("myMU/MSVCB01")
                self.assertEqual(pub._sv_id, "myMU/MSVCB01")

    def test_start_success(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850') as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_asdu = Mock()
                mock_iec.SVPublisher_addASDU.return_value = mock_asdu

                from pyiec61850.sv import SVPublisher
                pub = SVPublisher("eth0")
                pub.start()
                self.assertTrue(pub.is_running)

    def test_publish_not_started(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850'):
                from pyiec61850.sv import SVPublisher, NotStartedError
                pub = SVPublisher("eth0")
                with self.assertRaises(NotStartedError):
                    pub.publish_samples([1, 2, 3, 4])

    def test_stop(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850') as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher
                pub = SVPublisher("eth0")
                pub.start()
                pub.stop()

                self.assertFalse(pub.is_running)
                mock_iec.SVPublisher_destroy.assert_called_once()

    def test_context_manager(self):
        with patch('pyiec61850.sv.publisher._HAS_IEC61850', True):
            with patch('pyiec61850.sv.publisher.iec61850') as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher
                with SVPublisher("eth0") as pub:
                    pub.start()
                mock_iec.SVPublisher_destroy.assert_called()


if __name__ == '__main__':
    unittest.main()
