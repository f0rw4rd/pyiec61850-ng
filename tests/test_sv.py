#!/usr/bin/env python3
"""
Tests for pyiec61850.sv module - Sampled Values publish/subscribe.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

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
        from pyiec61850.sv import SVMessage

        self.assertIsNotNone(SVMessage)

    def test_import_exceptions(self):
        from pyiec61850.sv import (
            PublishError,
            SVError,
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
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", False):
            from pyiec61850.sv import LibraryNotFoundError, SVSubscriber

            with self.assertRaises(LibraryNotFoundError):
                SVSubscriber("eth0")

    def test_raises_on_empty_interface(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import ConfigurationError, SVSubscriber

                with self.assertRaises(ConfigurationError):
                    SVSubscriber("")

    def test_creation_success(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                self.assertEqual(sub.interface, "eth0")
                self.assertFalse(sub.is_running)

    def test_set_app_id_valid(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.set_app_id(0x4000)
                self.assertEqual(sub._app_id, 0x4000)

    def test_set_app_id_out_of_range(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import ConfigurationError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(ConfigurationError):
                    sub.set_app_id(-1)

    def test_set_listener(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                cb = Mock()
                sub.set_listener(cb)
                self.assertEqual(sub._listener, cb)

    def test_start_success(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.start()
                self.assertTrue(sub.is_running)

    def test_start_already_running(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import AlreadyStartedError, SVSubscriber

                sub = SVSubscriber("eth0")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.start()

    def test_start_receiver_failed(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = False

                from pyiec61850.sv import InterfaceError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(InterfaceError):
                    sub.start()

    def test_read_current_values_not_started(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import NotStartedError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(NotStartedError):
                    sub.read_current_values()

    def test_stop(self):
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
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
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
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
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", False):
            from pyiec61850.sv import LibraryNotFoundError, SVPublisher

            with self.assertRaises(LibraryNotFoundError):
                SVPublisher("eth0")

    def test_creation_success(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850"):
                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                self.assertEqual(pub.interface, "eth0")
                self.assertFalse(pub.is_running)

    def test_set_sv_id(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850"):
                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.set_sv_id("myMU/MSVCB01")
                self.assertEqual(pub._sv_id, "myMU/MSVCB01")

    def test_start_success(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_asdu = Mock()
                mock_iec.SVPublisher_addASDU.return_value = mock_asdu

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.start()
                self.assertTrue(pub.is_running)

    def test_publish_not_started(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850"):
                from pyiec61850.sv import NotStartedError, SVPublisher

                pub = SVPublisher("eth0")
                with self.assertRaises(NotStartedError):
                    pub.publish_samples([1, 2, 3, 4])

    def test_stop(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.start()
                pub.stop()

                self.assertFalse(pub.is_running)
                mock_iec.SVPublisher_destroy.assert_called_once()

    def test_context_manager(self):
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher

                with SVPublisher("eth0") as pub:
                    pub.start()
                mock_iec.SVPublisher_destroy.assert_called()


class TestSVSubscriberCrashPaths(unittest.TestCase):
    """Test SVSubscriber crash paths: start, cleanup, NULL returns."""

    def test_start_receiver_create_null(self):
        """SVReceiver_create returning NULL must raise SubscriptionError."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = None

                from pyiec61850.sv import SubscriptionError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(SubscriptionError):
                    sub.start()

    def test_start_subscriber_create_null(self):
        """SVSubscriber_create returning NULL must raise SubscriptionError."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = None

                from pyiec61850.sv import SubscriptionError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(SubscriptionError):
                    sub.start()

    def test_start_with_app_id_filter(self):
        """start() with app_id set must pass it to SVSubscriber_create."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.set_app_id(0x4000)
                sub.start()

                mock_iec.SVSubscriber_create.assert_called_once_with(None, 0x4000)

    def test_start_with_listener_registers(self):
        """start() with listener set must register in _sv_listener_registry."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber
                from pyiec61850.sv.subscriber import _sv_listener_registry

                sub = SVSubscriber("eth0")
                cb = Mock()
                sub.set_listener(cb)
                sub.start()

                self.assertIn(id(sub), _sv_listener_registry)

                sub.stop()
                self.assertNotIn(id(sub), _sv_listener_registry)

    def test_start_unexpected_exception_triggers_cleanup(self):
        """Unexpected exception during start must trigger _cleanup."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_addSubscriber.side_effect = RuntimeError("boom")

                from pyiec61850.sv import SubscriptionError, SVSubscriber

                sub = SVSubscriber("eth0")
                with self.assertRaises(SubscriptionError):
                    sub.start()

                self.assertIsNone(sub._receiver)
                self.assertIsNone(sub._subscriber)

    def test_cleanup_destroy_exception_still_clears(self):
        """If SVReceiver_destroy throws, references must still be cleared."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub._running = True
                sub._receiver = Mock()
                sub._subscriber = Mock()

                sub.stop()  # Must not raise

                self.assertIsNone(sub._receiver)
                self.assertIsNone(sub._subscriber)
                self.assertFalse(sub.is_running)

    def test_stop_receiver_stop_exception_still_cleans_up(self):
        """If SVReceiver_stop throws, cleanup must still happen."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_stop.side_effect = RuntimeError("stop failed")

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub._running = True
                sub._receiver = Mock()
                sub._subscriber = Mock()

                sub.stop()  # Must not raise

                self.assertFalse(sub.is_running)
                mock_iec.SVReceiver_destroy.assert_called_once()

    def test_double_stop_no_crash(self):
        """Calling stop() twice must not crash."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.start()
                sub.stop()
                sub.stop()  # Must be no-op
                self.assertFalse(sub.is_running)

    def test_read_current_values_success(self):
        """read_current_values must return SVMessage with data."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True
                mock_iec.SVSubscriber_getSmpCnt.return_value = 42
                mock_iec.SVSubscriber_getConfRev.return_value = 1
                mock_iec.SVSubscriber_getSmpSynch.return_value = 0
                mock_asdu = Mock()
                mock_iec.SVSubscriber_getASDU.return_value = mock_asdu
                mock_iec.SVClientASDU_getINT32.side_effect = [100, 200, 300, 400, 0, 0, 0, 0]

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.start()
                msg = sub.read_current_values()

                self.assertEqual(msg.smp_cnt, 42)
                self.assertEqual(len(msg.values), 8)

    def test_read_current_values_null_asdu(self):
        """read_current_values with NULL ASDU must not crash."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850") as mock_iec:
                mock_iec.SVReceiver_create.return_value = Mock()
                mock_iec.SVSubscriber_create.return_value = Mock()
                mock_iec.SVReceiver_isRunning.return_value = True
                mock_iec.SVSubscriber_getSmpCnt.return_value = 0
                mock_iec.SVSubscriber_getConfRev.return_value = 0
                mock_iec.SVSubscriber_getSmpSynch.return_value = 0
                mock_iec.SVSubscriber_getASDU.return_value = None

                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.start()
                msg = sub.read_current_values()

                self.assertEqual(msg.values, [])

    def test_set_sv_id(self):
        """set_sv_id must store the SV ID."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import SVSubscriber

                sub = SVSubscriber("eth0")
                sub.set_sv_id("testSVID")
                self.assertEqual(sub._sv_id, "testSVID")

    def test_set_sv_id_while_running(self):
        """set_sv_id while running must raise AlreadyStartedError."""
        with patch("pyiec61850.sv.subscriber._HAS_IEC61850", True):
            with patch("pyiec61850.sv.subscriber.iec61850"):
                from pyiec61850.sv import AlreadyStartedError, SVSubscriber

                sub = SVSubscriber("eth0")
                sub._running = True
                with self.assertRaises(AlreadyStartedError):
                    sub.set_sv_id("test")


class TestSVPublisherCrashPaths(unittest.TestCase):
    """Test SVPublisher crash paths: start, publish, stop, cleanup."""

    def test_start_publisher_create_null(self):
        """SVPublisher_create returning NULL must raise PublishError."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = None

                from pyiec61850.sv import PublishError, SVPublisher

                pub = SVPublisher("eth0")
                with self.assertRaises(PublishError):
                    pub.start()

    def test_start_asdu_create_null(self):
        """SVPublisher_addASDU returning NULL must raise PublishError."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = None

                from pyiec61850.sv import PublishError, SVPublisher

                pub = SVPublisher("eth0")
                with self.assertRaises(PublishError):
                    pub.start()

    def test_start_unexpected_exception_triggers_cleanup(self):
        """Unexpected exception during start must trigger _cleanup."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()
                mock_iec.SVPublisher_ASDU_addINT32.side_effect = RuntimeError("boom")

                from pyiec61850.sv import PublishError, SVPublisher

                pub = SVPublisher("eth0")
                with self.assertRaises(PublishError):
                    pub.start()

                self.assertIsNone(pub._publisher)

    def test_publish_success(self):
        """Successful publish path."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.start()
                pub.publish_samples([1000, 2000, 3000, 4000])

                mock_iec.SVPublisher_publish.assert_called_once()
                # smp_cnt should wrap
                self.assertEqual(pub._smp_cnt, 1)

    def test_publish_sample_count_wraps(self):
        """Sample count must wrap at smp_rate."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.set_smp_rate(3)
                pub.start()
                pub.publish_samples([1])
                pub.publish_samples([2])
                pub.publish_samples([3])

                self.assertEqual(pub._smp_cnt, 0)

    def test_publish_exception_raises_publish_error(self):
        """Exception during publish must raise PublishError."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()
                mock_iec.SVPublisher_ASDU_setINT32.side_effect = RuntimeError("fail")

                from pyiec61850.sv import PublishError, SVPublisher

                pub = SVPublisher("eth0")
                pub.start()
                with self.assertRaises(PublishError):
                    pub.publish_samples([1])

    def test_cleanup_destroy_exception_still_clears(self):
        """If SVPublisher_destroy throws, references must still be cleared."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub._running = True
                pub._publisher = Mock()
                pub._asdu = Mock()

                pub.stop()  # Must not raise

                self.assertIsNone(pub._publisher)
                self.assertIsNone(pub._asdu)
                self.assertFalse(pub.is_running)

    def test_double_stop_no_crash(self):
        """Calling stop() twice must not crash."""
        with patch("pyiec61850.sv.publisher._HAS_IEC61850", True):
            with patch("pyiec61850.sv.publisher.iec61850") as mock_iec:
                mock_iec.SVPublisher_create.return_value = Mock()
                mock_iec.SVPublisher_addASDU.return_value = Mock()

                from pyiec61850.sv import SVPublisher

                pub = SVPublisher("eth0")
                pub.start()
                pub.stop()
                pub.stop()  # Must be no-op
                self.assertFalse(pub.is_running)


if __name__ == "__main__":
    unittest.main()
