#!/usr/bin/env python3
"""
Tests for SWIG NULL-safety typemaps.

These tests verify that the SWIG-level guards in iec61850.i raise
Python exceptions instead of segfaulting when called with NULL/invalid args.

REQUIRES the built C extension (pyiec61850.pyiec61850). Skipped in dev
environments where only the pure-Python wrappers are available.
"""

import unittest

try:
    import pyiec61850.pyiec61850 as iec

    _HAS_SWIG = True
except ImportError:
    _HAS_SWIG = False

SKIP_MSG = "Requires built C extension (run ./build.sh first)"


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestGooseSubscriberSafety(unittest.TestCase):
    """GOOSE subscriber NULL/empty guards."""

    def test_create_empty_gocbref_raises(self):
        with self.assertRaises((ValueError, RuntimeError)):
            iec.GooseSubscriber_create("", None)

    def test_create_valid_gocbref(self):
        sub = iec.GooseSubscriber_create("test/LLN0$GO$gcb", None)
        self.assertIsNotNone(sub)
        iec.GooseSubscriber_destroy(sub)

    def test_destroy_null_is_noop(self):
        # Should not segfault
        iec.GooseSubscriber_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestGooseReceiverSafety(unittest.TestCase):
    """GOOSE receiver NULL/state guards."""

    def test_create_returns_valid(self):
        recv = iec.GooseReceiver_create()
        self.assertIsNotNone(recv)
        iec.GooseReceiver_destroy(recv)

    def test_destroy_null_is_noop(self):
        iec.GooseReceiver_destroy(None)

    def test_double_start_raises(self):
        recv = iec.GooseReceiver_create()
        sub = iec.GooseSubscriber_create("test/LLN0$GO$gcb", None)
        iec.GooseReceiver_addSubscriber(recv, sub)
        iec.GooseReceiver_setInterfaceId(recv, "lo")

        try:
            iec.GooseReceiver_startThreadless(recv)
        except Exception:
            # May fail if lo not available, that's OK for this test
            iec.GooseReceiver_destroy(recv)
            return

        with self.assertRaises(RuntimeError):
            iec.GooseReceiver_start(recv)

        iec.GooseReceiver_stop(recv)
        iec.GooseReceiver_destroy(recv)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestIedConnectionSafety(unittest.TestCase):
    """IedConnection NULL guards."""

    def test_create_returns_valid(self):
        conn = iec.IedConnection_create()
        self.assertIsNotNone(conn)
        iec.IedConnection_destroy(conn)

    def test_destroy_null_is_noop(self):
        iec.IedConnection_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestMmsConnectionSafety(unittest.TestCase):
    """MmsConnection NULL guards."""

    def test_create_returns_valid(self):
        conn = iec.MmsConnection_create()
        self.assertIsNotNone(conn)
        iec.MmsConnection_destroy(conn)

    def test_destroy_null_is_noop(self):
        iec.MmsConnection_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestLinkedListSafety(unittest.TestCase):
    """LinkedList NULL guards."""

    def test_create_returns_valid(self):
        ll = iec.LinkedList_create()
        self.assertIsNotNone(ll)
        iec.LinkedList_destroy(ll)

    def test_destroy_null_is_noop(self):
        iec.LinkedList_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestMmsValueSafety(unittest.TestCase):
    """MmsValue NULL guards."""

    def test_delete_null_is_noop(self):
        iec.MmsValue_delete(None)

    def test_new_integer(self):
        val = iec.MmsValue_newInteger(32)
        self.assertIsNotNone(val)
        iec.MmsValue_delete(val)

    def test_new_boolean(self):
        val = iec.MmsValue_newBoolean(True)
        self.assertIsNotNone(val)
        iec.MmsValue_delete(val)

    def test_new_float(self):
        val = iec.MmsValue_newFloat(3.14)
        self.assertIsNotNone(val)
        iec.MmsValue_delete(val)

    def test_new_visible_string(self):
        val = iec.MmsValue_newVisibleString("hello")
        self.assertIsNotNone(val)
        iec.MmsValue_delete(val)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestGoosePublisherSafety(unittest.TestCase):
    """GoosePublisher NULL guards."""

    def test_destroy_null_is_noop(self):
        iec.GoosePublisher_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestControlObjectSafety(unittest.TestCase):
    """ControlObjectClient NULL guards."""

    def test_destroy_null_is_noop(self):
        iec.ControlObjectClient_destroy(None)


@unittest.skipUnless(_HAS_SWIG, SKIP_MSG)
class TestClientReportControlBlockSafety(unittest.TestCase):
    """ClientReportControlBlock NULL guards."""

    def test_create_valid(self):
        rcb = iec.ClientReportControlBlock_create("test/LLN0$BR$brcb01")
        self.assertIsNotNone(rcb)
        iec.ClientReportControlBlock_destroy(rcb)

    def test_destroy_null_is_noop(self):
        iec.ClientReportControlBlock_destroy(None)


if __name__ == "__main__":
    unittest.main()
