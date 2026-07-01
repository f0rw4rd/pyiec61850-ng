#!/usr/bin/env python3
"""
Unit tests for pyiec61850.tase2.connection.MmsConnectionWrapper.

These tests drive the low-level MMS connection wrapper used by the TASE.2
client. They mock the SWIG ``iec61850`` binding entirely so no native library
or server is required.

Mocking strategy (mirrors tests/test_mms.py crash-path tests and
tests/test_tase2.py):

* ``pyiec61850._libload.have_library`` -> True so ``require_library()`` lets
  the wrapper construct.
* ``pyiec61850.tase2.connection.iec61850`` -> a MagicMock standing in for the
  SWIG module, with concrete int constants (IED_ERROR_OK etc.) so the
  production code's ``== iec61850.IED_ERROR_OK`` comparisons behave.
* ``pyiec61850.tase2.connection._HAS_IEC61850`` -> True.

The error-returning raw calls in libiec61850's SWIG bindings return
``(value, error)`` tuples; the mocks below return faithful tuples to exercise
both the success and the error/NULL branches.
"""

import unittest
from unittest.mock import MagicMock, patch

# IED error code constants used by the mocked binding.
#
# These MUST match the real libiec61850 IedClientError enum values, because
# ``exceptions.map_ied_error`` re-imports the real ``pyiec61850.pyiec61850``
# module (not our mock) to build its code->exception table. Using the wrong
# numbers there would silently fall through to a generic TASE2Error.
IED_ERROR_OK = 0
IED_ERROR_ACCESS_DENIED = 21
IED_ERROR_OBJECT_DOES_NOT_EXIST = 22
IED_ERROR_TIMEOUT = 20
IED_STATE_CONNECTED = 2

# MmsValue type tags (match constants.py / libiec61850 defaults).
MMS_BOOLEAN = 2
MMS_INTEGER = 4
MMS_UNSIGNED = 5
MMS_FLOAT = 6
MMS_VISIBLE_STRING = 8
MMS_STRING = 13


def _make_iec_mock():
    """Build a MagicMock SWIG binding with concrete numeric constants.

    Constants must be plain ints (not child Mocks) so the production code's
    ``error != iec61850.IED_ERROR_OK`` comparisons resolve to real booleans.
    """
    m = MagicMock(name="iec61850")
    m.IED_ERROR_OK = IED_ERROR_OK
    m.IED_ERROR_ACCESS_DENIED = IED_ERROR_ACCESS_DENIED
    m.IED_ERROR_OBJECT_DOES_NOT_EXIST = IED_ERROR_OBJECT_DOES_NOT_EXIST
    m.IED_ERROR_TIMEOUT = IED_ERROR_TIMEOUT
    m.IED_STATE_CONNECTED = IED_STATE_CONNECTED
    m.ACSI_CLASS_DATA_SET = 1
    m.MMS_BOOLEAN = MMS_BOOLEAN
    m.MMS_INTEGER = MMS_INTEGER
    m.MMS_UNSIGNED = MMS_UNSIGNED
    m.MMS_FLOAT = MMS_FLOAT
    m.MMS_VISIBLE_STRING = MMS_VISIBLE_STRING
    m.MMS_STRING = MMS_STRING
    return m


class _WrapperTestBase(unittest.TestCase):
    """Base class wiring up the patches shared by every wrapper test."""

    def setUp(self):
        # Let the wrapper construct without a real native lib.
        self._have_lib_patcher = patch("pyiec61850._libload.have_library", return_value=True)
        self._have_lib_patcher.start()

        self.iec = _make_iec_mock()
        self._iec_patcher = patch("pyiec61850.tase2.connection.iec61850", self.iec)
        self._iec_patcher.start()

        # tase2 routes LinkedList iteration/cleanup through mms.utils' guards
        # (LinkedListGuard), which use mms.utils' own iec61850 reference — point
        # it at the same mock so wired LinkedList_* side effects are honoured.
        self._utils_iec_patcher = patch("pyiec61850.mms.utils.iec61850", self.iec)
        self._utils_iec_patcher.start()

        self._has_patcher = patch("pyiec61850.tase2.connection._HAS_IEC61850", True)
        self._has_patcher.start()

    def tearDown(self):
        self._has_patcher.stop()
        self._utils_iec_patcher.stop()
        self._iec_patcher.stop()
        self._have_lib_patcher.stop()

    def _new_wrapper(self, **kwargs):
        from pyiec61850.tase2.connection import MmsConnectionWrapper

        return MmsConnectionWrapper(**kwargs)

    def _connected_wrapper(self, **kwargs):
        """Return a wrapper forced into the CONNECTED state with a fake handle.

        ``_ensure_connected`` checks ``is_connected`` (state == CONNECTED and
        ``_connection is not None``) and then queries the library state, which
        we make report CONNECTED.
        """
        from pyiec61850.tase2.constants import STATE_CONNECTED

        w = self._new_wrapper(**kwargs)
        w._connection = object()  # truthy, non-mock handle
        w._state = STATE_CONNECTED
        self.iec.IedConnection_getState.return_value = IED_STATE_CONNECTED
        return w


def _linked_list(items):
    """Build a mock LinkedList traversal returning the given string items.

    Production code iterates with ``LinkedList_getNext`` starting from the head
    (header node is skipped), reading ``LinkedList_getData`` then
    ``toCharP(data)`` for each element. We model the head as a list object and
    each subsequent node as an index, so getNext walks head -> 0 -> 1 -> ... ->
    None.
    """
    # Each node is a distinct truthy sentinel object (a real LinkedList node is
    # an opaque pointer). Using truthy sentinels matters because production
    # loops with ``while element:`` — a falsy node (e.g. integer 0) would end
    # the traversal prematurely.
    head = object()
    nodes = [object() for _ in items]
    node_index = {id(n): i for i, n in enumerate(nodes)}

    def get_next(node):
        if node is head:
            return nodes[0] if nodes else None
        idx = node_index[id(node)]
        return nodes[idx + 1] if idx + 1 < len(nodes) else None

    def get_data(node):
        return items[node_index[id(node)]]

    return head, get_next, get_data


# ---------------------------------------------------------------------------
# Construction / state / properties
# ---------------------------------------------------------------------------


class TestConstructionAndState(_WrapperTestBase):
    def test_initial_state_disconnected(self):
        from pyiec61850.tase2.constants import DEFAULT_PORT, STATE_DISCONNECTED

        w = self._new_wrapper(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertFalse(w.is_connected)
        self.assertIsNone(w.host)
        self.assertEqual(w.port, DEFAULT_PORT)
        self.assertEqual(w._local_ap_title, "1.1.1.999")
        self.assertEqual(w._remote_ap_title, "1.1.1.998")

    def test_is_available(self):
        from pyiec61850.tase2.connection import is_available

        self.assertIsInstance(is_available(), bool)

    def test_is_connected_requires_handle(self):
        from pyiec61850.tase2.constants import STATE_CONNECTED

        w = self._new_wrapper()
        w._state = STATE_CONNECTED
        w._connection = None
        self.assertFalse(w.is_connected)  # state right, handle missing

    def test_construction_raises_without_library(self):
        # Override the have_library patch to simulate a missing extension.
        from pyiec61850.tase2.exceptions import LibraryNotFoundError

        with patch("pyiec61850._libload.have_library", return_value=False):
            with self.assertRaises(LibraryNotFoundError):
                self._new_wrapper()


# ---------------------------------------------------------------------------
# State callbacks
# ---------------------------------------------------------------------------


class TestStateCallbacks(_WrapperTestBase):
    def test_register_and_fire(self):
        w = self._new_wrapper()
        calls = []
        cb = lambda old, new: calls.append((old, new))  # noqa: E731
        w.register_state_callback(cb)
        self.assertEqual(len(w._state_callbacks), 1)
        w._fire_state_callbacks(2, 0)
        self.assertEqual(calls, [(2, 0)])

    def test_register_is_idempotent(self):
        w = self._new_wrapper()
        cb = lambda *a: None  # noqa: E731
        w.register_state_callback(cb)
        w.register_state_callback(cb)
        self.assertEqual(len(w._state_callbacks), 1)

    def test_unregister(self):
        w = self._new_wrapper()
        cb = lambda *a: None  # noqa: E731
        w.register_state_callback(cb)
        w.unregister_state_callback(cb)
        self.assertEqual(len(w._state_callbacks), 0)
        # Unregistering an unknown callback is a no-op.
        w.unregister_state_callback(cb)

    def test_callback_error_is_swallowed(self):
        w = self._new_wrapper()

        def bad(old, new):
            raise RuntimeError("boom")

        good_calls = []
        w.register_state_callback(bad)
        w.register_state_callback(lambda o, n: good_calls.append(1))
        # Must not raise; the good callback still runs.
        w._fire_state_callbacks(2, 0)
        self.assertEqual(good_calls, [1])


# ---------------------------------------------------------------------------
# check_connection_state
# ---------------------------------------------------------------------------


class TestCheckConnectionState(_WrapperTestBase):
    def test_not_connected_returns_false(self):
        w = self._new_wrapper()
        self.assertFalse(w.check_connection_state())

    def test_still_connected(self):
        w = self._connected_wrapper()
        self.assertTrue(w.check_connection_state())

    def test_connection_lost_fires_callback(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED

        w = self._connected_wrapper()
        fired = []
        w.register_state_callback(lambda o, n: fired.append((o, n)))
        self.iec.IedConnection_getState.return_value = 0  # not CONNECTED
        self.assertFalse(w.check_connection_state())
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertEqual(len(fired), 1)

    def test_state_query_exception_returns_false(self):
        w = self._connected_wrapper()
        self.iec.IedConnection_getState.side_effect = RuntimeError("native boom")
        self.assertFalse(w.check_connection_state())


# ---------------------------------------------------------------------------
# connect / disconnect / cleanup
# ---------------------------------------------------------------------------


class TestConnectDisconnect(_WrapperTestBase):
    def test_connect_success(self):
        from pyiec61850.tase2.constants import STATE_CONNECTED

        self.iec.IedConnection_create.return_value = object()
        self.iec.IedConnection_connect.return_value = (None, IED_ERROR_OK)

        w = self._new_wrapper()
        # Avoid spinning the real monitor thread.
        with patch.object(w, "_start_state_monitor"):
            result = w.connect("10.0.0.1", port=102, timeout=5000)

        self.assertTrue(result)
        self.assertEqual(w.state, STATE_CONNECTED)
        self.assertEqual(w.host, "10.0.0.1")
        self.iec.IedConnection_setConnectTimeout.assert_called_once()

    def test_connect_create_returns_null(self):
        from pyiec61850.tase2.exceptions import ConnectionFailedError

        self.iec.IedConnection_create.return_value = None
        w = self._new_wrapper()
        with self.assertRaises(ConnectionFailedError):
            w.connect("10.0.0.1")

    def test_connect_error_code_cleans_up(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED
        from pyiec61850.tase2.exceptions import ConnectionFailedError

        self.iec.IedConnection_create.return_value = object()
        self.iec.IedConnection_connect.return_value = (None, IED_ERROR_TIMEOUT)
        self.iec.IedClientError_toString.return_value = "timeout"

        w = self._new_wrapper()
        with self.assertRaises(ConnectionFailedError):
            w.connect("10.0.0.1")
        # _cleanup should have destroyed the connection and reset state.
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertIsNone(w._connection)
        self.iec.IedConnection_destroy.assert_called_once()

    def test_connect_configures_iso_params_when_ap_title_set(self):
        self.iec.IedConnection_create.return_value = object()
        self.iec.IedConnection_connect.return_value = (None, IED_ERROR_OK)
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_getIsoConnectionParameters.return_value = object()

        w = self._new_wrapper(local_ap_title="1.1.1.999")
        with patch.object(w, "_start_state_monitor"):
            w.connect("10.0.0.1")
        self.iec.IsoConnectionParameters_setLocalApTitle.assert_called_once()

    def test_connect_reconnects_when_already_connected(self):
        self.iec.IedConnection_create.return_value = object()
        self.iec.IedConnection_connect.return_value = (None, IED_ERROR_OK)

        w = self._connected_wrapper()
        with patch.object(w, "disconnect") as mock_disc, patch.object(w, "_start_state_monitor"):
            w.connect("10.0.0.2")
        mock_disc.assert_called_once()

    def test_connect_unexpected_exception_wrapped(self):
        from pyiec61850.tase2.exceptions import ConnectionFailedError

        self.iec.IedConnection_create.side_effect = RuntimeError("oops")
        w = self._new_wrapper()
        with self.assertRaises(ConnectionFailedError):
            w.connect("10.0.0.1")

    def test_disconnect_when_already_disconnected_is_noop(self):
        w = self._new_wrapper()
        w.disconnect()  # STATE_DISCONNECTED -> early return
        self.iec.IedConnection_close.assert_not_called()

    def test_disconnect_closes_and_cleans_up(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED

        w = self._connected_wrapper()
        w.disconnect()
        self.iec.IedConnection_close.assert_called_once()
        self.iec.IedConnection_destroy.assert_called_once()
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertIsNone(w._connection)

    def test_disconnect_close_error_still_cleans_up(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED

        w = self._connected_wrapper()
        self.iec.IedConnection_close.side_effect = RuntimeError("close fail")
        w.disconnect()
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertIsNone(w._connection)

    def test_cleanup_destroy_error_swallowed(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED

        w = self._connected_wrapper()
        self.iec.IedConnection_destroy.side_effect = RuntimeError("destroy fail")
        w._cleanup()
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertIsNone(w._connection)

    def test_get_error_string_fallback(self):
        w = self._new_wrapper()
        self.iec.IedClientError_toString.side_effect = RuntimeError("no str")
        self.assertIn("Error code: 7", w._get_error_string(7))


# ---------------------------------------------------------------------------
# ISO parameters
# ---------------------------------------------------------------------------


class TestIsoParameters(_WrapperTestBase):
    def test_configure_no_connection(self):
        w = self._new_wrapper(local_ap_title="1.1.1.1")
        w._connection = None
        # Should return early without touching the binding.
        w._configure_iso_parameters()
        self.iec.IedConnection_getMmsConnection.assert_not_called()

    def test_configure_no_mms_conn(self):
        w = self._new_wrapper(local_ap_title="1.1.1.1")
        w._connection = object()
        self.iec.IedConnection_getMmsConnection.return_value = None
        w._configure_iso_parameters()
        self.iec.MmsConnection_getIsoConnectionParameters.assert_not_called()

    def test_configure_no_iso_params(self):
        w = self._new_wrapper(local_ap_title="1.1.1.1")
        w._connection = object()
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_getIsoConnectionParameters.return_value = None
        w._configure_iso_parameters()
        self.iec.IsoConnectionParameters_setLocalApTitle.assert_not_called()

    def test_configure_sets_both_titles(self):
        w = self._new_wrapper(local_ap_title="1.1.1.1", remote_ap_title="1.1.1.2")
        w._connection = object()
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_getIsoConnectionParameters.return_value = object()
        w._configure_iso_parameters()
        self.iec.IsoConnectionParameters_setLocalApTitle.assert_called_once()
        self.iec.IsoConnectionParameters_setRemoteApTitle.assert_called_once()

    def test_configure_swallows_exception(self):
        w = self._new_wrapper(local_ap_title="1.1.1.1")
        w._connection = object()
        self.iec.IedConnection_getMmsConnection.side_effect = RuntimeError("boom")
        # Must not raise.
        w._configure_iso_parameters()

    def test_set_ap_title_invalid_format_skipped(self):
        w = self._new_wrapper()
        w._set_ap_title(object(), "not.an.oid", is_local=True)
        self.iec.IsoConnectionParameters_setLocalApTitle.assert_not_called()

    def test_set_ap_title_local(self):
        w = self._new_wrapper()
        w._set_ap_title(object(), "1.1.1.999", is_local=True)
        self.iec.IsoConnectionParameters_setLocalApTitle.assert_called_once()

    def test_set_ap_title_remote(self):
        w = self._new_wrapper()
        w._set_ap_title(object(), "1.1.1.998", is_local=False)
        self.iec.IsoConnectionParameters_setRemoteApTitle.assert_called_once()

    def test_set_ap_title_api_missing(self):
        # del the attribute so hasattr() is False on the mock module.
        del self.iec.IsoConnectionParameters_setLocalApTitle
        w = self._new_wrapper()
        # Should not raise even though the API is unavailable.
        w._set_ap_title(object(), "1.1.1.999", is_local=True)

    def test_set_ap_title_swallows_exception(self):
        w = self._new_wrapper()
        self.iec.IsoConnectionParameters_setLocalApTitle.side_effect = RuntimeError("boom")
        # Must not raise.
        w._set_ap_title(object(), "1.1.1.999", is_local=True)


# ---------------------------------------------------------------------------
# _ensure_connected
# ---------------------------------------------------------------------------


class TestEnsureConnected(_WrapperTestBase):
    def test_raises_when_not_connected(self):
        from pyiec61850.tase2.exceptions import NotConnectedError

        w = self._new_wrapper()
        with self.assertRaises(NotConnectedError):
            w._ensure_connected()

    def test_passes_when_connected(self):
        w = self._connected_wrapper()
        w._ensure_connected()  # no raise

    def test_raises_connection_closed_when_state_lost(self):
        from pyiec61850.tase2.exceptions import ConnectionClosedError

        w = self._connected_wrapper()
        self.iec.IedConnection_getState.return_value = 0
        with self.assertRaises(ConnectionClosedError):
            w._ensure_connected()

    def test_state_check_failure_proceeds(self):
        w = self._connected_wrapper()
        self.iec.IedConnection_getState.side_effect = RuntimeError("boom")
        # State check itself fails -> log and proceed (no raise).
        w._ensure_connected()


# ---------------------------------------------------------------------------
# get_domain_names / get_domain_variables / get_data_set_names
# ---------------------------------------------------------------------------


class TestDomainOperations(_WrapperTestBase):
    def _wire_linked_list(self, items):
        head, get_next, get_data = _linked_list(items)
        self.iec.LinkedList_getNext.side_effect = get_next
        self.iec.LinkedList_getData.side_effect = get_data
        self.iec.toCharP.side_effect = lambda d: d
        return head

    def test_get_domain_names_success(self):
        head = self._wire_linked_list(["VCC", "ICC1"])
        self.iec.IedConnection_getLogicalDeviceList.return_value = (head, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.get_domain_names(), ["VCC", "ICC1"])
        self.iec.LinkedList_destroy.assert_called_once_with(head)

    def test_get_domain_names_error_tuple(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getLogicalDeviceList.return_value = (
            None,
            IED_ERROR_TIMEOUT,
        )
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_domain_names()

    def test_get_domain_names_empty_list(self):
        self.iec.IedConnection_getLogicalDeviceList.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.get_domain_names(), [])

    def test_get_domain_names_non_tuple_return(self):
        head = self._wire_linked_list(["VCC"])
        self.iec.IedConnection_getLogicalDeviceList.return_value = head
        w = self._connected_wrapper()
        self.assertEqual(w.get_domain_names(), ["VCC"])

    def test_get_domain_names_not_connected(self):
        from pyiec61850.tase2.exceptions import NotConnectedError

        w = self._new_wrapper()
        with self.assertRaises(NotConnectedError):
            w.get_domain_names()

    def test_get_domain_names_unexpected_exception(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getLogicalDeviceList.side_effect = RuntimeError("boom")
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_domain_names()

    def test_get_domain_variables_success(self):
        head = self._wire_linked_list(["Var1", "Var2"])
        self.iec.IedConnection_getLogicalDeviceDirectory.return_value = (head, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.get_domain_variables("ICC1"), ["Var1", "Var2"])

    def test_get_domain_variables_error(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getLogicalDeviceDirectory.return_value = (
            None,
            IED_ERROR_ACCESS_DENIED,
        )
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_domain_variables("ICC1")

    def test_get_data_set_names_success(self):
        head = self._wire_linked_list(["DS1", "DS2"])
        self.iec.IedConnection_getLogicalNodeDirectory.return_value = (
            head,
            IED_ERROR_OK,
        )
        w = self._connected_wrapper()
        self.assertEqual(w.get_data_set_names("ICC1"), ["DS1", "DS2"])

    def test_get_data_set_names_error_returns_empty(self):
        # Error tuple => returns [] (data sets may not exist), not a raise.
        self.iec.IedConnection_getLogicalNodeDirectory.return_value = (
            None,
            IED_ERROR_OBJECT_DOES_NOT_EXIST,
        )
        w = self._connected_wrapper()
        self.assertEqual(w.get_data_set_names("ICC1"), [])

    def test_get_data_set_names_non_tuple(self):
        head = self._wire_linked_list(["DS1"])
        self.iec.IedConnection_getLogicalNodeDirectory.return_value = head
        w = self._connected_wrapper()
        self.assertEqual(w.get_data_set_names("ICC1"), ["DS1"])

    def test_get_data_set_names_unexpected_exception(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getLogicalNodeDirectory.side_effect = RuntimeError("x")
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_data_set_names("ICC1")


# ---------------------------------------------------------------------------
# read_data_set_values
# ---------------------------------------------------------------------------


class TestReadDataSetValues(_WrapperTestBase):
    def test_success(self):
        data_set = object()
        self.iec.IedConnection_readDataSetValues.return_value = (data_set, IED_ERROR_OK)
        self.iec.ClientDataSet_getDataSetSize.return_value = 3
        all_values = object()
        self.iec.ClientDataSet_getValues.return_value = all_values
        self.iec.MmsValue_getElement.side_effect = lambda av, i: f"m{i}"

        w = self._connected_wrapper()
        vals = w.read_data_set_values("ICC1", "DS1")
        self.assertEqual(vals, ["m0", "m1", "m2"])

    def test_error_tuple(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_readDataSetValues.return_value = (None, IED_ERROR_TIMEOUT)
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.read_data_set_values("ICC1", "DS1")

    def test_null_data_set_returns_empty(self):
        self.iec.IedConnection_readDataSetValues.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.read_data_set_values("ICC1", "DS1"), [])

    def test_oversize_warns_but_returns(self):
        from pyiec61850.tase2.constants import MAX_DATA_SET_SIZE

        data_set = object()
        self.iec.IedConnection_readDataSetValues.return_value = (data_set, IED_ERROR_OK)
        self.iec.ClientDataSet_getDataSetSize.return_value = MAX_DATA_SET_SIZE + 1
        self.iec.ClientDataSet_getValues.return_value = None  # no values array
        w = self._connected_wrapper()
        # No values array -> empty result, but the oversize branch is exercised.
        self.assertEqual(w.read_data_set_values("ICC1", "DS1"), [])

    def test_extract_error_wrapped(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        data_set = object()
        self.iec.IedConnection_readDataSetValues.return_value = (data_set, IED_ERROR_OK)
        self.iec.ClientDataSet_getDataSetSize.side_effect = RuntimeError("size boom")
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.read_data_set_values("ICC1", "DS1")


# ---------------------------------------------------------------------------
# read_variable / _create_mms_value / write_variable
# ---------------------------------------------------------------------------


class TestReadWriteVariable(_WrapperTestBase):
    def test_read_variable_success(self):
        self.iec.IedConnection_readObject.return_value = (230.5, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.read_variable("ICC1", "Voltage"), 230.5)

    def test_read_variable_error_maps(self):
        from pyiec61850.tase2.exceptions import VariableNotFoundError

        self.iec.IedConnection_readObject.return_value = (
            None,
            IED_ERROR_OBJECT_DOES_NOT_EXIST,
        )
        w = self._connected_wrapper()
        with self.assertRaises(VariableNotFoundError):
            w.read_variable("ICC1", "Nope")

    def test_read_variable_non_tuple(self):
        self.iec.IedConnection_readObject.return_value = 42
        w = self._connected_wrapper()
        self.assertEqual(w.read_variable("ICC1", "V"), 42)

    def test_read_variable_unexpected_exception(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_readObject.side_effect = RuntimeError("boom")
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.read_variable("ICC1", "V")

    def test_create_mms_value_bool(self):
        w = self._new_wrapper()
        w._create_mms_value(True)
        self.iec.MmsValue_newBoolean.assert_called_once_with(True)

    def test_create_mms_value_int(self):
        w = self._new_wrapper()
        w._create_mms_value(7)
        self.iec.MmsValue_newIntegerFromInt32.assert_called_once_with(7)

    def test_create_mms_value_float(self):
        w = self._new_wrapper()
        w._create_mms_value(3.5)
        self.iec.MmsValue_newFloat.assert_called_once_with(3.5)

    def test_create_mms_value_str(self):
        w = self._new_wrapper()
        w._create_mms_value("hi")
        self.iec.MmsValue_newVisibleString.assert_called_once_with("hi")

    def test_create_mms_value_unsupported_passthrough(self):
        w = self._new_wrapper()
        sentinel = [1, 2, 3]
        self.assertIs(w._create_mms_value(sentinel), sentinel)

    def test_create_mms_value_already_mms(self):
        # An object whose type repr contains "MmsValue" passes through.
        class MmsValue:  # noqa: N801
            pass

        w = self._new_wrapper()
        v = MmsValue()
        self.assertIs(w._create_mms_value(v), v)
        self.iec.MmsValue_newBoolean.assert_not_called()

    def test_create_mms_value_error_wrapped(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.MmsValue_newFloat.side_effect = RuntimeError("boom")
        w = self._new_wrapper()
        with self.assertRaises(TASE2Error):
            w._create_mms_value(1.0)

    def test_write_variable_success_deletes_created_value(self):
        created = object()
        self.iec.MmsValue_newFloat.return_value = created
        self.iec.IedConnection_writeObject.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertTrue(w.write_variable("ICC1", "SP", 1.0))
        self.iec.MmsValue_delete.assert_called_once_with(created)

    def test_write_variable_error_maps(self):
        from pyiec61850.tase2.exceptions import AccessDeniedError

        self.iec.MmsValue_newFloat.return_value = object()
        self.iec.IedConnection_writeObject.return_value = (None, IED_ERROR_ACCESS_DENIED)
        w = self._connected_wrapper()
        with self.assertRaises(AccessDeniedError):
            w.write_variable("ICC1", "SP", 1.0)
        # Even on error, a created value is deleted in the finally block.
        self.iec.MmsValue_delete.assert_called_once()

    def test_write_variable_passthrough_value_not_deleted(self):
        # Pre-built MmsValue passes through unchanged -> not deleted by us.
        class MmsValue:  # noqa: N801
            pass

        self.iec.IedConnection_writeObject.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertTrue(w.write_variable("ICC1", "SP", MmsValue()))
        self.iec.MmsValue_delete.assert_not_called()

    def test_write_variable_delete_error_swallowed(self):
        self.iec.MmsValue_newFloat.return_value = object()
        self.iec.IedConnection_writeObject.return_value = (None, IED_ERROR_OK)
        self.iec.MmsValue_delete.side_effect = RuntimeError("delete fail")
        w = self._connected_wrapper()
        # delete error in finally is swallowed.
        self.assertTrue(w.write_variable("ICC1", "SP", 1.0))


# ---------------------------------------------------------------------------
# create_data_set / delete_data_set
# ---------------------------------------------------------------------------


class TestDataSetCreateDelete(_WrapperTestBase):
    def test_create_success(self):
        self.iec.LinkedList_create.return_value = object()
        self.iec.IedConnection_createDataSet.return_value = IED_ERROR_OK
        w = self._connected_wrapper()
        self.assertTrue(w.create_data_set("ICC1", "DS1", ["A", "ICC1/B"]))
        self.iec.LinkedList_destroy.assert_called_once()
        # Two members added (one bare, one fully-qualified).
        self.assertEqual(self.iec.LinkedList_add.call_count, 2)

    def test_create_no_members(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.create_data_set("ICC1", "DS1", [])

    def test_create_too_many_members(self):
        from pyiec61850.tase2.constants import MAX_DATA_SET_SIZE
        from pyiec61850.tase2.exceptions import TASE2Error

        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.create_data_set("ICC1", "DS1", ["m"] * (MAX_DATA_SET_SIZE + 1))

    def test_create_error_code_maps(self):
        from pyiec61850.tase2.exceptions import AccessDeniedError

        self.iec.LinkedList_create.return_value = object()
        self.iec.IedConnection_createDataSet.return_value = IED_ERROR_ACCESS_DENIED
        w = self._connected_wrapper()
        with self.assertRaises(AccessDeniedError):
            w.create_data_set("ICC1", "DS1", ["A"])
        # member_list still destroyed in finally.
        self.iec.LinkedList_destroy.assert_called_once()

    def test_create_error_tuple_unpacked(self):
        from pyiec61850.tase2.exceptions import AccessDeniedError

        self.iec.LinkedList_create.return_value = object()
        self.iec.IedConnection_createDataSet.return_value = (
            None,
            IED_ERROR_ACCESS_DENIED,
        )
        w = self._connected_wrapper()
        with self.assertRaises(AccessDeniedError):
            w.create_data_set("ICC1", "DS1", ["A"])

    def test_delete_success_scalar(self):
        self.iec.IedConnection_deleteDataSet.return_value = True
        w = self._connected_wrapper()
        self.assertTrue(w.delete_data_set("ICC1", "DS1"))

    def test_delete_success_tuple(self):
        self.iec.IedConnection_deleteDataSet.return_value = (True, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertTrue(w.delete_data_set("ICC1", "DS1"))

    def test_delete_error_tuple_maps(self):
        from pyiec61850.tase2.exceptions import AccessDeniedError

        self.iec.IedConnection_deleteDataSet.return_value = (
            False,
            IED_ERROR_ACCESS_DENIED,
        )
        w = self._connected_wrapper()
        with self.assertRaises(AccessDeniedError):
            w.delete_data_set("ICC1", "DS1")

    def test_delete_refused_scalar_false(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_deleteDataSet.return_value = False
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.delete_data_set("ICC1", "DS1")


# ---------------------------------------------------------------------------
# get_server_identity
# ---------------------------------------------------------------------------


class TestServerIdentity(_WrapperTestBase):
    # get_server_identity uses the MMS Identify service via the underlying
    # MmsConnection (IedConnection_identify does not exist in this binding).
    # A plain object (not MagicMock) is used for the identity so a failing
    # assertion never introspects unset child mocks.
    @staticmethod
    def _identity(vendor, model, rev):
        return type("_Id", (), {"vendorName": vendor, "modelName": model, "revision": rev})()

    def test_success(self):
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_identify.return_value = self._identity("ABB", "RTU560", "1.0")
        w = self._connected_wrapper()
        self.assertEqual(w.get_server_identity(), ("ABB", "RTU560", "1.0"))

    def test_no_mms_connection_returns_none_tuple(self):
        self.iec.IedConnection_getMmsConnection.return_value = None
        w = self._connected_wrapper()
        self.assertEqual(w.get_server_identity(), (None, None, None))

    def test_null_identity_returns_none_tuple(self):
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_identify.return_value = None
        w = self._connected_wrapper()
        self.assertEqual(w.get_server_identity(), (None, None, None))

    def test_unexpected_exception_wrapped(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_identify.side_effect = RuntimeError("boom")
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_server_identity()


# ---------------------------------------------------------------------------
# File services
# ---------------------------------------------------------------------------


class TestFileServices(_WrapperTestBase):
    def test_get_file_directory_success(self):
        head, get_next, get_data = _linked_list(["fileA", "fileB"])
        self.iec.LinkedList_getNext.side_effect = get_next
        self.iec.LinkedList_getData.side_effect = get_data
        self.iec.IedConnection_getFileDirectory.return_value = (head, IED_ERROR_OK)
        self.iec.FileDirectoryEntry_getFileName.side_effect = lambda d: d
        self.iec.FileDirectoryEntry_getFileSize.side_effect = lambda d: 100
        self.iec.FileDirectoryEntry_getLastModified.side_effect = lambda d: 12345

        w = self._connected_wrapper()
        files = w.get_file_directory("")
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["name"], "fileA")
        self.assertEqual(files[0]["size"], 100)
        self.assertEqual(files[0]["last_modified"], 12345)

    def test_get_file_directory_error(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getFileDirectory.return_value = (None, IED_ERROR_TIMEOUT)
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.get_file_directory("")

    def test_get_file_directory_entry_accessor_errors_default(self):
        head, get_next, get_data = _linked_list(["fileA"])
        self.iec.LinkedList_getNext.side_effect = get_next
        self.iec.LinkedList_getData.side_effect = get_data
        self.iec.IedConnection_getFileDirectory.return_value = (head, IED_ERROR_OK)
        self.iec.FileDirectoryEntry_getFileName.side_effect = RuntimeError("x")
        self.iec.FileDirectoryEntry_getFileSize.side_effect = RuntimeError("x")
        self.iec.FileDirectoryEntry_getLastModified.side_effect = RuntimeError("x")

        w = self._connected_wrapper()
        files = w.get_file_directory("")
        self.assertEqual(files[0]["size"], 0)
        self.assertEqual(files[0]["last_modified"], 0)

    def test_get_file_directory_empty(self):
        self.iec.IedConnection_getFileDirectory.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertEqual(w.get_file_directory(""), [])

    def test_delete_file_success_scalar(self):
        self.iec.IedConnection_deleteFile.return_value = IED_ERROR_OK
        w = self._connected_wrapper()
        self.assertTrue(w.delete_file("f.txt"))

    def test_delete_file_success_tuple(self):
        self.iec.IedConnection_deleteFile.return_value = (None, IED_ERROR_OK)
        w = self._connected_wrapper()
        self.assertTrue(w.delete_file("f.txt"))

    def test_delete_file_error(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_deleteFile.return_value = IED_ERROR_ACCESS_DENIED
        self.iec.IedClientError_toString.return_value = "denied"
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.delete_file("f.txt")


# ---------------------------------------------------------------------------
# download_file / _download_file_mms
# ---------------------------------------------------------------------------


class TestDownloadFile(_WrapperTestBase):
    def test_download_no_mms_conn(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getMmsConnection.return_value = None
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.download_file("f.txt")

    def test_download_fileopen_missing(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getMmsConnection.return_value = object()
        del self.iec.MmsConnection_fileOpen
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.download_file("f.txt")

    def test_download_returns_empty_via_mms(self):
        # fileOpen succeeds, fileRead branch breaks and returns what we have.
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_fileOpen.return_value = (1, 100, 0, 0)
        w = self._connected_wrapper()
        result = w.download_file("f.txt")
        self.assertEqual(result, b"")
        self.iec.MmsConnection_fileClose.assert_called_once()

    def test_download_fileopen_error_in_tuple(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_fileOpen.return_value = (0, 5)  # last elem != 0 -> error
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.download_file("f.txt")

    def test_download_fileopen_scalar_frsm(self):
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_fileOpen.return_value = 2  # scalar frsmId
        w = self._connected_wrapper()
        self.assertEqual(w.download_file("f.txt"), b"")
        self.iec.MmsConnection_fileClose.assert_called_once_with(
            self.iec.IedConnection_getMmsConnection.return_value, 2
        )

    def test_download_invalid_frsm(self):
        from pyiec61850.tase2.exceptions import TASE2Error

        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_fileOpen.return_value = -1
        w = self._connected_wrapper()
        with self.assertRaises(TASE2Error):
            w.download_file("f.txt")

    def test_download_fileclose_missing_no_crash(self):
        self.iec.IedConnection_getMmsConnection.return_value = object()
        self.iec.MmsConnection_fileOpen.return_value = (1, 100, 0, 0)
        del self.iec.MmsConnection_fileClose
        w = self._connected_wrapper()
        # fileClose absent -> finally skips it without raising.
        self.assertEqual(w.download_file("f.txt"), b"")


# ---------------------------------------------------------------------------
# set_max_outstanding_calls / set_request_timeout
# ---------------------------------------------------------------------------


class TestTuning(_WrapperTestBase):
    def test_set_max_outstanding_calls(self):
        w = self._connected_wrapper()
        w.set_max_outstanding_calls(5, 5)
        self.iec.IedConnection_setMaxOutstandingCalls.assert_called_once_with(w._connection, 5, 5)

    def test_set_max_outstanding_calls_not_connected(self):
        from pyiec61850.tase2.exceptions import NotConnectedError

        w = self._new_wrapper()
        with self.assertRaises(NotConnectedError):
            w.set_max_outstanding_calls(5, 5)

    def test_set_request_timeout(self):
        w = self._connected_wrapper()
        w.set_request_timeout(3000)
        self.iec.IedConnection_setRequestTimeout.assert_called_once_with(w._connection, 3000)

    def test_set_request_timeout_not_connected(self):
        from pyiec61850.tase2.exceptions import NotConnectedError

        w = self._new_wrapper()
        with self.assertRaises(NotConnectedError):
            w.set_request_timeout(3000)


# ---------------------------------------------------------------------------
# Information report handler install/uninstall
# ---------------------------------------------------------------------------


class TestInformationReportHandler(_WrapperTestBase):
    def test_install_no_mms_conn(self):
        import queue

        self.iec.IedConnection_getMmsConnection.return_value = None
        w = self._connected_wrapper()
        self.assertFalse(w.install_information_report_handler(queue.Queue()))

    def test_install_handler_api_missing(self):
        import queue

        self.iec.IedConnection_getMmsConnection.return_value = object()
        del self.iec.InformationReportHandler
        w = self._connected_wrapper()
        self.assertFalse(w.install_information_report_handler(queue.Queue()))

    def test_install_exception_returns_false(self):
        import queue

        self.iec.IedConnection_getMmsConnection.side_effect = RuntimeError("boom")
        w = self._connected_wrapper()
        self.assertFalse(w.install_information_report_handler(queue.Queue()))

    def test_uninstall(self):
        w = self._new_wrapper()
        w._info_report_handler = object()
        w._info_report_subscriber = object()
        w.uninstall_information_report_handler()
        self.assertIsNone(w._info_report_handler)
        self.assertIsNone(w._info_report_subscriber)


# ---------------------------------------------------------------------------
# Context manager / destructor
# ---------------------------------------------------------------------------


class TestContextManager(_WrapperTestBase):
    def test_enter_returns_self(self):
        w = self._new_wrapper()
        self.assertIs(w.__enter__(), w)

    def test_exit_calls_disconnect(self):
        w = self._new_wrapper()
        with patch.object(w, "disconnect") as mock_disc:
            self.assertFalse(w.__exit__(None, None, None))
        mock_disc.assert_called_once()

    def test_del_swallows_errors(self):
        w = self._new_wrapper()
        with patch.object(w, "disconnect", side_effect=RuntimeError("boom")):
            w.__del__()  # must not raise


# ---------------------------------------------------------------------------
# State monitor loop (single-iteration, no real thread)
# ---------------------------------------------------------------------------


class TestStateMonitorLoop(_WrapperTestBase):
    def test_loop_detects_loss_then_stops(self):
        from pyiec61850.tase2.constants import STATE_DISCONNECTED

        w = self._connected_wrapper()
        fired = []
        w.register_state_callback(lambda o, n: fired.append((o, n)))
        self.iec.IedConnection_getState.return_value = 0  # connection lost

        # Make the loop run exactly once: stop is "not set" on the while check,
        # then "set" when wait() is reached.
        states = iter([False, True])
        w._state_monitor_stop.is_set = lambda: next(states)
        w._state_monitor_stop.wait = lambda interval: None

        w._state_monitor_loop()
        self.assertEqual(w.state, STATE_DISCONNECTED)
        self.assertEqual(len(fired), 1)

    def test_loop_exception_swallowed(self):
        w = self._connected_wrapper()
        self.iec.IedConnection_getState.side_effect = RuntimeError("boom")
        states = iter([False, True])
        w._state_monitor_stop.is_set = lambda: next(states)
        w._state_monitor_stop.wait = lambda interval: None
        # Must not raise.
        w._state_monitor_loop()


if __name__ == "__main__":
    unittest.main()
