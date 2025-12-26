#!/usr/bin/env python3
"""
Tests for TASE.2/ICCP module (pyiec61850.tase2)

These tests verify the TASE.2 client, types, constants, and exceptions
without requiring an actual TASE.2 server connection.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestTASE2Imports(unittest.TestCase):
    """Test module imports and availability."""

    def test_client_import(self):
        """Test TASE2Client can be imported."""
        from pyiec61850.tase2 import TASE2Client
        self.assertIsNotNone(TASE2Client)

    def test_types_import(self):
        """Test data types can be imported."""
        from pyiec61850.tase2 import (
            Domain,
            Variable,
            PointValue,
            ControlPoint,
            DataSet,
            TransferSet,
            BilateralTable,
            ServerInfo,
        )
        self.assertIsNotNone(Domain)
        self.assertIsNotNone(Variable)
        self.assertIsNotNone(PointValue)
        self.assertIsNotNone(ControlPoint)
        self.assertIsNotNone(DataSet)
        self.assertIsNotNone(TransferSet)
        self.assertIsNotNone(BilateralTable)
        self.assertIsNotNone(ServerInfo)

    def test_constants_import(self):
        """Test constants can be imported."""
        from pyiec61850.tase2 import (
            DEFAULT_PORT,
            DEFAULT_TIMEOUT,
            POINT_TYPES,
            CONFORMANCE_BLOCKS,
            QUALITY_GOOD,
            QUALITY_INVALID,
            BLOCK_1,
            BLOCK_2,
            BLOCK_5,
        )
        self.assertEqual(DEFAULT_PORT, 102)
        self.assertIsInstance(POINT_TYPES, dict)
        self.assertEqual(len(CONFORMANCE_BLOCKS), 5)
        self.assertEqual(QUALITY_GOOD, "GOOD")
        self.assertEqual(QUALITY_INVALID, "INVALID")

    def test_exceptions_import(self):
        """Test exceptions can be imported."""
        from pyiec61850.tase2 import (
            TASE2Error,
            LibraryError,
            LibraryNotFoundError,
            ConnectionError,
            ConnectionFailedError,
            NotConnectedError,
            ReadError,
            WriteError,
            ControlError,
            SelectError,
            OperateError,
        )
        self.assertTrue(issubclass(LibraryError, TASE2Error))
        self.assertTrue(issubclass(ConnectionError, TASE2Error))
        self.assertTrue(issubclass(ControlError, TASE2Error))

    def test_is_available_function(self):
        """Test is_available function exists."""
        from pyiec61850.tase2 import is_available
        # Should return True since pyiec61850 is installed
        result = is_available()
        self.assertIsInstance(result, bool)


class TestTASE2Types(unittest.TestCase):
    """Test data type classes."""

    def test_domain_creation(self):
        """Test Domain dataclass creation."""
        from pyiec61850.tase2 import Domain

        domain = Domain(name="ICC1", is_vcc=False)
        self.assertEqual(domain.name, "ICC1")
        self.assertEqual(domain.is_vcc, False)
        self.assertEqual(domain.domain_type, "ICC")

    def test_vcc_domain(self):
        """Test VCC domain type."""
        from pyiec61850.tase2 import Domain

        domain = Domain(name="VCC", is_vcc=True)
        self.assertEqual(domain.domain_type, "VCC")

    def test_domain_with_variables(self):
        """Test Domain with variables list."""
        from pyiec61850.tase2 import Domain

        domain = Domain(
            name="ICC1",
            is_vcc=False,
            variables=["Voltage", "Current", "Power"],
            data_sets=["DS1", "DS2"],
        )
        self.assertEqual(len(domain.variables), 3)
        self.assertEqual(len(domain.data_sets), 2)

    def test_point_value_creation(self):
        """Test PointValue dataclass creation."""
        from pyiec61850.tase2 import PointValue

        pv = PointValue(value=230.5, quality="GOOD")
        self.assertEqual(pv.value, 230.5)
        self.assertEqual(pv.quality, "GOOD")
        self.assertTrue(pv.is_valid)

    def test_point_value_invalid(self):
        """Test invalid PointValue."""
        from pyiec61850.tase2 import PointValue

        pv = PointValue(value=None, quality="INVALID")
        self.assertIsNone(pv.value)
        self.assertFalse(pv.is_valid)

    def test_point_value_with_timestamp(self):
        """Test PointValue with timestamp."""
        from pyiec61850.tase2 import PointValue

        ts = datetime.now()
        pv = PointValue(value=100.0, quality="GOOD", timestamp=ts)
        self.assertEqual(pv.timestamp, ts)

    def test_transfer_set_creation(self):
        """Test TransferSet dataclass creation."""
        from pyiec61850.tase2 import TransferSet

        ts = TransferSet(
            name="TS1",
            domain="ICC1",
            data_set="DS1",
            interval=5000,
            rbe_enabled=True,
        )
        self.assertEqual(ts.name, "TS1")
        self.assertEqual(ts.domain, "ICC1")
        self.assertTrue(ts.rbe_enabled)

    def test_bilateral_table_creation(self):
        """Test BilateralTable dataclass creation."""
        from pyiec61850.tase2 import BilateralTable

        blt = BilateralTable(
            table_id="BLT001",
            ap_title="1.1.1.999",
        )
        self.assertEqual(blt.table_id, "BLT001")
        self.assertEqual(blt.ap_title, "1.1.1.999")

    def test_server_info_creation(self):
        """Test ServerInfo dataclass creation."""
        from pyiec61850.tase2 import ServerInfo

        info = ServerInfo(
            vendor="TestVendor",
            model="TestModel",
            revision="1.0",
            bilateral_table_count=2,
            bilateral_table_id="BLT001",
        )
        self.assertEqual(info.vendor, "TestVendor")
        self.assertEqual(info.bilateral_table_count, 2)

    def test_data_flags_creation(self):
        """Test DataFlags dataclass creation."""
        from pyiec61850.tase2 import (
            DataFlags,
            QUALITY_VALIDITY_VALID,
            QUALITY_VALIDITY_SUSPECT,
            QUALITY_SOURCE_TELEMETERED,
        )

        # Default flags (valid, telemetered)
        flags = DataFlags()
        self.assertEqual(flags.validity, QUALITY_VALIDITY_VALID)
        self.assertEqual(flags.source, QUALITY_SOURCE_TELEMETERED)
        self.assertTrue(flags.is_valid)
        self.assertFalse(flags.is_suspect)

        # Suspect flags
        flags_suspect = DataFlags(validity=QUALITY_VALIDITY_SUSPECT)
        self.assertFalse(flags_suspect.is_valid)
        self.assertTrue(flags_suspect.is_suspect)

    def test_data_flags_from_raw(self):
        """Test DataFlags.from_raw class method."""
        from pyiec61850.tase2 import DataFlags

        # Raw value: VALID(0) | TELEMETERED(0) | NORMAL_VALUE(64) = 64
        flags = DataFlags.from_raw(64)
        self.assertTrue(flags.is_valid)
        self.assertTrue(flags.normal_value)
        self.assertEqual(flags.raw_value, 64)

        # Raw value: SUSPECT(8) | CALCULATED(32) = 40
        flags2 = DataFlags.from_raw(40)
        self.assertTrue(flags2.is_suspect)
        self.assertEqual(flags2.source, 32)  # CALCULATED

    def test_data_flags_round_trip(self):
        """Test DataFlags round-trip (from_raw -> raw_value)."""
        from pyiec61850.tase2 import (
            DataFlags,
            QUALITY_VALIDITY_VALID,
            QUALITY_VALIDITY_SUSPECT,
            QUALITY_VALIDITY_HELD,
            QUALITY_VALIDITY_NOT_VALID,
            QUALITY_SOURCE_TELEMETERED,
            QUALITY_SOURCE_ENTERED,
            QUALITY_SOURCE_CALCULATED,
            QUALITY_SOURCE_ESTIMATED,
        )

        # Test all validity/source combinations
        test_values = [
            QUALITY_VALIDITY_VALID | QUALITY_SOURCE_TELEMETERED,          # 0
            QUALITY_VALIDITY_HELD | QUALITY_SOURCE_ENTERED,               # 4 | 16 = 20
            QUALITY_VALIDITY_SUSPECT | QUALITY_SOURCE_CALCULATED,         # 8 | 32 = 40
            QUALITY_VALIDITY_NOT_VALID | QUALITY_SOURCE_ESTIMATED,        # 12 | 48 = 60
            64,   # Normal value flag
            128,  # Timestamp quality flag
            64 | 128,  # Both flags
        ]

        for raw in test_values:
            flags = DataFlags.from_raw(raw)
            # Round-trip should preserve the value
            self.assertEqual(flags.raw_value, raw, f"Round-trip failed for raw={raw}")

    def test_transfer_set_conditions(self):
        """Test TransferSetConditions dataclass."""
        from pyiec61850.tase2 import TransferSetConditions

        # Test creation
        cond = TransferSetConditions(interval_timeout=True, object_change=True)
        self.assertTrue(cond.interval_timeout)
        self.assertTrue(cond.object_change)
        self.assertEqual(cond.raw_value, 3)  # 1 + 2

        # Test from_raw
        cond2 = TransferSetConditions.from_raw(5)  # INTERVAL(1) + OPERATOR_REQUEST(4)
        self.assertTrue(cond2.interval_timeout)
        self.assertFalse(cond2.object_change)
        self.assertTrue(cond2.operator_request)

    def test_protection_event(self):
        """Test ProtectionEvent dataclass."""
        from pyiec61850.tase2 import ProtectionEvent

        # Test creation with flags
        event = ProtectionEvent(
            event_flags=0b110,  # Phase A and Phase B
            operating_time=50,
        )
        self.assertFalse(event.has_general_fault)
        self.assertTrue(event.has_phase_a_fault)
        self.assertTrue(event.has_phase_b_fault)
        self.assertFalse(event.has_phase_c_fault)
        self.assertEqual(event.operating_time, 50)

    def test_point_value_with_flags(self):
        """Test PointValue with DataFlags."""
        from pyiec61850.tase2 import PointValue, DataFlags, QUALITY_VALIDITY_SUSPECT

        flags = DataFlags(validity=QUALITY_VALIDITY_SUSPECT)  # SUSPECT = 8
        pv = PointValue(value=123.45, flags=flags)

        self.assertEqual(pv.value, 123.45)
        self.assertFalse(pv.is_valid)  # Uses flags.is_valid
        self.assertEqual(pv.quality_flags.validity_name, "SUSPECT")


class TestTASE2Client(unittest.TestCase):
    """Test client without connection."""

    def setUp(self):
        """Set up test fixtures with mocked connection."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = False
        self.mock_connection.state = 0  # STATE_DISCONNECTED
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_client_creation(self):
        """Test TASE2Client creation."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertFalse(client.is_connected)

    def test_client_with_ap_titles(self):
        """Test TASE2Client with AP titles."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(
            local_ap_title="1.1.1.999",
            remote_ap_title="1.1.1.998"
        )
        self.assertEqual(client._local_ap_title, "1.1.1.999")
        self.assertEqual(client._remote_ap_title, "1.1.1.998")

    def test_not_connected_error(self):
        """Test NotConnectedError when not connected."""
        from pyiec61850.tase2 import TASE2Client, NotConnectedError

        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.get_domains()

    def test_client_state(self):
        """Test client state property."""
        from pyiec61850.tase2 import TASE2Client, STATE_DISCONNECTED

        client = TASE2Client()
        self.assertEqual(client.state, STATE_DISCONNECTED)

    def test_client_context_manager(self):
        """Test client as context manager."""
        from pyiec61850.tase2 import TASE2Client

        with TASE2Client() as client:
            self.assertFalse(client.is_connected)


class TestTASE2Exceptions(unittest.TestCase):
    """Test exception hierarchy."""

    def test_base_exception(self):
        """Test TASE2Error base exception."""
        from pyiec61850.tase2 import TASE2Error

        err = TASE2Error("test error")
        self.assertEqual(str(err), "test error")

    def test_connection_failed_error(self):
        """Test ConnectionFailedError."""
        from pyiec61850.tase2 import ConnectionFailedError

        err = ConnectionFailedError("localhost", 102, "timeout")
        self.assertIn("localhost", str(err))
        self.assertIn("102", str(err))

    def test_not_connected_error(self):
        """Test NotConnectedError."""
        from pyiec61850.tase2 import NotConnectedError

        err = NotConnectedError()
        self.assertIn("not connected", str(err).lower())

    def test_tase2_connection_error(self):
        """Test TASE2ConnectionError (non-shadowing exception name)."""
        from pyiec61850.tase2 import TASE2ConnectionError, ConnectionError

        # TASE2ConnectionError should be the base class
        self.assertTrue(issubclass(ConnectionError, TASE2ConnectionError) or
                       ConnectionError is TASE2ConnectionError)

    def test_tase2_timeout_error(self):
        """Test TASE2TimeoutError (non-shadowing exception name)."""
        from pyiec61850.tase2 import TASE2TimeoutError, TimeoutError

        # TimeoutError should be alias for TASE2TimeoutError
        self.assertTrue(TimeoutError is TASE2TimeoutError)

    def test_domain_not_found_error(self):
        """Test DomainNotFoundError."""
        from pyiec61850.tase2 import DomainNotFoundError

        err = DomainNotFoundError("ICC1")
        self.assertIn("ICC1", str(err))

    def test_read_error(self):
        """Test ReadError."""
        from pyiec61850.tase2 import ReadError

        err = ReadError("ICC1/Voltage", "access denied")
        self.assertIn("ICC1/Voltage", str(err))

    def test_control_error_hierarchy(self):
        """Test control error inheritance."""
        from pyiec61850.tase2 import (
            ControlError,
            SelectError,
            OperateError,
            TagError,
        )
        self.assertTrue(issubclass(SelectError, ControlError))
        self.assertTrue(issubclass(OperateError, ControlError))
        self.assertTrue(issubclass(TagError, ControlError))


class TestTASE2Constants(unittest.TestCase):
    """Test TASE.2 constants."""

    def test_point_types(self):
        """Test point type constants (IEC 60870-6 compliant ordering)."""
        from pyiec61850.tase2 import (
            POINT_TYPE_STATE,
            POINT_TYPE_STATE_SUPPLEMENTAL,
            POINT_TYPE_DISCRETE,
            POINT_TYPE_REAL,
            POINT_TYPES,
        )
        # IEC 60870-6 ordering: STATE=1, STATE_SUPPLEMENTAL=2, DISCRETE=3, REAL=4
        self.assertEqual(POINT_TYPE_STATE, 1)
        self.assertEqual(POINT_TYPE_STATE_SUPPLEMENTAL, 2)
        self.assertEqual(POINT_TYPE_DISCRETE, 3)
        self.assertEqual(POINT_TYPE_REAL, 4)
        self.assertIn(POINT_TYPE_REAL, POINT_TYPES)

    def test_control_types(self):
        """Test control type constants."""
        from pyiec61850.tase2 import (
            CONTROL_TYPE_COMMAND,
            CONTROL_TYPE_SETPOINT_REAL,
            CONTROL_TYPE_SETPOINT_DISCRETE,
            CONTROL_TYPES,
        )
        self.assertEqual(CONTROL_TYPE_COMMAND, 1)
        self.assertIn(CONTROL_TYPE_COMMAND, CONTROL_TYPES)

    def test_conformance_blocks(self):
        """Test conformance block constants."""
        from pyiec61850.tase2 import (
            BLOCK_1,
            BLOCK_2,
            BLOCK_3,
            BLOCK_4,
            BLOCK_5,
            CONFORMANCE_BLOCKS,
        )
        self.assertEqual(BLOCK_1, 1)
        self.assertEqual(BLOCK_2, 2)
        self.assertEqual(BLOCK_5, 5)
        self.assertEqual(len(CONFORMANCE_BLOCKS), 5)

    def test_quality_flags(self):
        """Test quality flag constants."""
        from pyiec61850.tase2 import (
            QUALITY_GOOD,
            QUALITY_INVALID,
            QUALITY_HELD,
            QUALITY_SUSPECT,
        )
        self.assertEqual(QUALITY_GOOD, "GOOD")
        self.assertEqual(QUALITY_INVALID, "INVALID")

    def test_command_values(self):
        """Test command value constants."""
        from pyiec61850.tase2 import CMD_OFF, CMD_ON
        self.assertEqual(CMD_OFF, 0)
        self.assertEqual(CMD_ON, 1)

    def test_client_states(self):
        """Test client state constants."""
        from pyiec61850.tase2 import (
            STATE_DISCONNECTED,
            STATE_CONNECTING,
            STATE_CONNECTED,
            STATE_CLOSING,
            CLIENT_STATES,
        )
        self.assertEqual(STATE_DISCONNECTED, 0)
        self.assertEqual(STATE_CONNECTED, 2)
        self.assertIn(STATE_CONNECTED, CLIENT_STATES)

    def test_protocol_limits(self):
        """Test protocol limit constants."""
        from pyiec61850.tase2 import (
            MAX_DATA_SET_SIZE,
            SBO_TIMEOUT,
            MAX_POINT_NAME_LENGTH,
        )
        # Per IEC 60870-6
        self.assertEqual(MAX_DATA_SET_SIZE, 500)
        self.assertEqual(SBO_TIMEOUT, 30)
        self.assertEqual(MAX_POINT_NAME_LENGTH, 32)


class TestPointNameValidation(unittest.TestCase):
    """Test data point name validation per IEC 60870-6-503."""

    def test_valid_names(self):
        """Test valid TASE.2 point names."""
        from pyiec61850.tase2.client import _validate_point_name

        valid_names = [
            "Voltage",
            "voltage",
            "VOLTAGE",
            "Point_1",
            "Point1",
            "P",
            "ABC_123_xyz",
            "a" * 32,  # Max length
        ]

        for name in valid_names:
            self.assertTrue(_validate_point_name(name), f"'{name}' should be valid")

    def test_invalid_names(self):
        """Test invalid TASE.2 point names."""
        from pyiec61850.tase2.client import _validate_point_name

        invalid_names = [
            "",           # Empty
            "1Point",     # Starts with digit
            "123",        # All digits
            "Point-1",    # Contains hyphen
            "Point.1",    # Contains dot
            "Point 1",    # Contains space
            "Point@1",    # Contains special char
            "a" * 33,     # Too long
        ]

        for name in invalid_names:
            self.assertFalse(_validate_point_name(name), f"'{name}' should be invalid")


class TestTASE2ClientMethods(unittest.TestCase):
    """Test client methods with mocked connection."""

    def setUp(self):
        """Set up test fixtures."""
        # Patch the MmsConnectionWrapper
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_connect(self):
        """Test connect method."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.connect.return_value = True
        self.mock_connection.is_connected = True

        client = TASE2Client()
        result = client.connect("192.168.1.100", port=102)

        self.assertTrue(result)
        self.mock_connection.connect.assert_called_once_with(
            "192.168.1.100", 102, 10000
        )

    def test_disconnect(self):
        """Test disconnect method."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.disconnect()

        self.mock_connection.disconnect.assert_called_once()

    def test_get_domains(self):
        """Test get_domains method."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.is_connected = True
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = ["Var1", "Var2"]
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        domains = client.get_domains()

        self.assertEqual(len(domains), 2)
        self.assertTrue(domains[0].is_vcc)

    def test_read_point(self):
        """Test read_point method."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.is_connected = True
        self.mock_connection.read_variable.return_value = 230.5

        client = TASE2Client()
        pv = client.read_point("ICC1", "Voltage")

        self.assertEqual(pv.value, 230.5)
        self.mock_connection.read_variable.assert_called_once_with(
            "ICC1", "Voltage"
        )


class TestTASE2ControlOperations(unittest.TestCase):
    """Test Block 5 control operations."""

    def setUp(self):
        """Set up test fixtures with mocked connection."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.state = 2  # STATE_CONNECTED
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_select_device_success(self):
        """Test successful device selection."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.select_device("ICC1", "Breaker1")

        self.assertTrue(result)
        # Should record select time for SBO tracking
        self.assertIn("ICC1/Breaker1", client._sbo_select_times)

    def test_select_device_not_connected(self):
        """Test select_device raises error when not connected."""
        from pyiec61850.tase2 import TASE2Client, NotConnectedError

        self.mock_connection.is_connected = False

        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.select_device("ICC1", "Breaker1")

    def test_operate_device_success(self):
        """Test successful device operation."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        # First select, then operate
        client.select_device("ICC1", "Breaker1")
        result = client.operate_device("ICC1", "Breaker1", 1)

        self.assertTrue(result)
        # Select time should be cleared after operate
        self.assertNotIn("ICC1/Breaker1", client._sbo_select_times)

    def test_operate_device_sbo_timeout(self):
        """Test operate_device raises error when SBO select has timed out."""
        from pyiec61850.tase2 import TASE2Client, OperateError
        import time

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        # Manually set an expired select time (more than SBO_TIMEOUT ago)
        client._sbo_select_times["ICC1/Breaker1"] = time.time() - 31  # 31 seconds ago

        with self.assertRaises(OperateError) as ctx:
            client.operate_device("ICC1", "Breaker1", 1)

        self.assertIn("expired", str(ctx.exception).lower())

    def test_send_command_on(self):
        """Test sending ON command."""
        from pyiec61850.tase2 import TASE2Client, CMD_ON

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_command("ICC1", "Switch1", CMD_ON)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with("ICC1", "Switch1", CMD_ON)

    def test_send_command_off(self):
        """Test sending OFF command."""
        from pyiec61850.tase2 import TASE2Client, CMD_OFF

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_command("ICC1", "Switch1", CMD_OFF)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with("ICC1", "Switch1", CMD_OFF)

    def test_send_setpoint_real(self):
        """Test sending real setpoint value."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_setpoint_real("ICC1", "VoltageSetpoint", 115.5)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with(
            "ICC1", "VoltageSetpoint", 115.5
        )

    def test_send_setpoint_discrete(self):
        """Test sending discrete setpoint value."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_setpoint_discrete("ICC1", "TapPosition", 5)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with(
            "ICC1", "TapPosition", 5
        )

    def test_set_tag(self):
        """Test setting device tag."""
        from pyiec61850.tase2 import TASE2Client, TAG_OPEN_AND_CLOSE_INHIBIT

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.set_tag("ICC1", "Breaker1", TAG_OPEN_AND_CLOSE_INHIBIT, "Maintenance")

        self.assertTrue(result)

    def test_device_blocked_error(self):
        """Test OperateError when device write fails."""
        from pyiec61850.tase2 import TASE2Client, OperateError

        self.mock_connection.write_variable.side_effect = Exception("Access denied")

        client = TASE2Client()
        with self.assertRaises(OperateError):
            client.operate_device("ICC1", "Breaker1", 1)


class TestTASE2TransferSets(unittest.TestCase):
    """Test Block 2 transfer set operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_transfer_sets(self):
        """Test discovering transfer sets."""
        from pyiec61850.tase2 import TASE2Client

        # Mock data set names with transfer set patterns
        self.mock_connection.get_data_set_names.return_value = [
            "DS_TransferSet_1",
            "DSTS_Analog",
            "RegularDataSet",
        ]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        ts_list = client.get_transfer_sets("ICC1")

        # Should find 2 transfer sets (matching patterns)
        self.assertEqual(len(ts_list), 2)
        self.assertEqual(ts_list[0].name, "DS_TransferSet_1")
        self.assertEqual(ts_list[1].name, "DSTS_Analog")

    def test_get_transfer_set_details(self):
        """Test reading transfer set configuration."""
        from pyiec61850.tase2 import TASE2Client, PointValue

        # Mock reading config variables
        def mock_read(domain, name):
            if "Interval" in name:
                return 5000  # 5 seconds
            if "RBE" in name:
                return 1  # True
            raise Exception("Not found")

        self.mock_connection.read_variable.side_effect = mock_read

        client = TASE2Client()
        ts = client.get_transfer_set_details("ICC1", "TS1")

        self.assertEqual(ts.name, "TS1")
        self.assertEqual(ts.domain, "ICC1")

    def test_enable_transfer_set(self):
        """Test enabling a transfer set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.enable_transfer_set("ICC1", "TS1")

        self.assertTrue(result)

    def test_disable_transfer_set(self):
        """Test disabling a transfer set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.disable_transfer_set("ICC1", "TS1")

        self.assertTrue(result)

    def test_transfer_set_not_found(self):
        """Test when no transfer sets found."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.get_domain_variables.return_value = []

        client = TASE2Client()
        ts_list = client.get_transfer_sets("ICC1")

        self.assertEqual(len(ts_list), 0)


class TestTASE2DataOperations(unittest.TestCase):
    """Test data point read/write operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_write_point_success(self):
        """Test successful data point write."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.write_point("ICC1", "Setpoint1", 100.5)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with(
            "ICC1", "Setpoint1", 100.5
        )

    def test_write_point_failure(self):
        """Test write failure raises WriteError."""
        from pyiec61850.tase2 import TASE2Client, WriteError

        self.mock_connection.write_variable.side_effect = Exception("Write failed")

        client = TASE2Client()
        with self.assertRaises(WriteError):
            client.write_point("ICC1", "Setpoint1", 100.5)

    def test_read_points_batch(self):
        """Test batch reading multiple points."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.return_value = 230.5

        client = TASE2Client()
        points = [("ICC1", "Voltage"), ("ICC1", "Current"), ("ICC1", "Power")]
        results = client.read_points(points)

        self.assertEqual(len(results), 3)
        for pv in results:
            self.assertEqual(pv.value, 230.5)

    def test_read_points_partial_failure(self):
        """Test batch read with some failures."""
        from pyiec61850.tase2 import TASE2Client, QUALITY_INVALID

        def mock_read(domain, name):
            if name == "Current":
                raise Exception("Read failed")
            return 100.0

        self.mock_connection.read_variable.side_effect = mock_read

        client = TASE2Client()
        points = [("ICC1", "Voltage"), ("ICC1", "Current"), ("ICC1", "Power")]
        results = client.read_points(points)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].value, 100.0)
        self.assertIsNone(results[1].value)  # Failed read
        self.assertEqual(results[1].quality, QUALITY_INVALID)
        self.assertEqual(results[2].value, 100.0)

    def test_get_data_sets(self):
        """Test getting data sets."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_data_set_names.return_value = ["DS1", "DS2"]
        self.mock_connection.get_domain_names.return_value = ["ICC1"]
        self.mock_connection.get_domain_variables.return_value = []

        client = TASE2Client()
        data_sets = client.get_data_sets("ICC1")

        self.assertEqual(len(data_sets), 2)
        self.assertEqual(data_sets[0].name, "DS1")
        self.assertEqual(data_sets[0].domain, "ICC1")

    def test_get_data_set_values(self):
        """Test reading data set values."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_data_set_values.return_value = [100.0, 200.0, 300.0]

        client = TASE2Client()
        values = client.get_data_set_values("ICC1", "DS1")

        self.assertEqual(len(values), 3)


class TestTASE2Discovery(unittest.TestCase):
    """Test domain and variable discovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_domain_by_name(self):
        """Test get_domain returns specific domain."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = ["Var1"]
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        domain = client.get_domain("ICC1")

        self.assertEqual(domain.name, "ICC1")
        self.assertFalse(domain.is_vcc)

    def test_get_domain_not_found(self):
        """Test DomainNotFoundError when domain doesn't exist."""
        from pyiec61850.tase2 import TASE2Client, DomainNotFoundError

        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        with self.assertRaises(DomainNotFoundError):
            client.get_domain("NonExistent")

    def test_get_vcc_variables(self):
        """Test get_vcc_variables returns VCC domain variables."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.side_effect = lambda d: (
            ["VCC_Var1", "VCC_Var2"] if d == "VCC" else ["ICC_Var1"]
        )
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        vcc_vars = client.get_vcc_variables()

        self.assertEqual(len(vcc_vars), 2)
        self.assertIn("VCC_Var1", vcc_vars)

    def test_get_domain_variables(self):
        """Test get_domain_variables returns domain variables."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_variables.return_value = ["Var1", "Var2", "Var3"]

        client = TASE2Client()
        variables = client.get_domain_variables("ICC1")

        self.assertEqual(len(variables), 3)
        self.mock_connection.get_domain_variables.assert_called_with("ICC1")

    def test_get_server_info(self):
        """Test get_server_info returns ServerInfo."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_server_identity.return_value = ("ABB", "RTU560", "1.0")
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        info = client.get_server_info()

        self.assertEqual(info.vendor, "ABB")
        self.assertEqual(info.model, "RTU560")
        self.assertEqual(info.revision, "1.0")

    def test_get_bilateral_table_id(self):
        """Test get_bilateral_table_id."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = ["Bilateral_Table_ID"]
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.read_variable.return_value = "BLT_001"

        client = TASE2Client()
        blt_id = client.get_bilateral_table_id()

        self.assertEqual(blt_id, "BLT_001")


class TestTASE2ErrorHandling(unittest.TestCase):
    """Test error conditions and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_connection_timeout(self):
        """Test connection timeout handling."""
        from pyiec61850.tase2 import TASE2Client, ConnectionFailedError

        self.mock_connection.connect.side_effect = ConnectionFailedError(
            "192.168.1.100", 102, "timeout"
        )

        client = TASE2Client()
        with self.assertRaises(ConnectionFailedError):
            client.connect("192.168.1.100")

    def test_read_error_access_denied(self):
        """Test ReadError when access denied."""
        from pyiec61850.tase2 import TASE2Client, ReadError

        self.mock_connection.is_connected = True
        self.mock_connection.read_variable.side_effect = Exception("Access denied")

        client = TASE2Client()
        with self.assertRaises(ReadError) as ctx:
            client.read_point("ICC1", "SecretVar")

        self.assertIn("ICC1/SecretVar", str(ctx.exception))

    def test_invalid_parameter_handling(self):
        """Test handling of invalid parameters."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.client import _validate_point_name

        # Invalid point names
        self.assertFalse(_validate_point_name(""))
        self.assertFalse(_validate_point_name("123abc"))  # Starts with digit
        self.assertFalse(_validate_point_name("var-name"))  # Contains hyphen
        self.assertFalse(_validate_point_name("a" * 33))  # Too long

    def test_protocol_error_handling(self):
        """Test protocol error handling."""
        from pyiec61850.tase2 import TASE2Client, TASE2Error

        self.mock_connection.is_connected = True
        self.mock_connection.get_domain_names.side_effect = Exception("Protocol error")

        client = TASE2Client()
        with self.assertRaises(TASE2Error):
            client.get_domains()


class TestMmsConnectionWrapper(unittest.TestCase):
    """Test low-level MMS connection operations."""

    def test_wrapper_creation(self):
        """Test MmsConnectionWrapper creation."""
        from pyiec61850.tase2.connection import MmsConnectionWrapper, is_available
        from pyiec61850.tase2.exceptions import LibraryNotFoundError

        if not is_available():
            # Library not available, verify it raises appropriate error
            with self.assertRaises(LibraryNotFoundError):
                MmsConnectionWrapper(
                    local_ap_title="1.1.1.999",
                    remote_ap_title="1.1.1.998"
                )
        else:
            # Library available, test normal creation
            wrapper = MmsConnectionWrapper(
                local_ap_title="1.1.1.999",
                remote_ap_title="1.1.1.998"
            )
            self.assertFalse(wrapper.is_connected)

    def test_wrapper_is_available(self):
        """Test is_available function."""
        from pyiec61850.tase2.connection import is_available

        result = is_available()
        self.assertIsInstance(result, bool)

    def test_wrapper_state_disconnected(self):
        """Test wrapper state when disconnected."""
        from pyiec61850.tase2.connection import MmsConnectionWrapper, is_available
        from pyiec61850.tase2 import STATE_DISCONNECTED
        from pyiec61850.tase2.exceptions import LibraryNotFoundError

        if not is_available():
            # Library not available, verify it raises appropriate error
            with self.assertRaises(LibraryNotFoundError):
                MmsConnectionWrapper()
        else:
            # Library available, test normal state
            wrapper = MmsConnectionWrapper()
            self.assertEqual(wrapper.state, STATE_DISCONNECTED)


class TestTASE2SecurityAnalysis(unittest.TestCase):
    """Test security analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('pyiec61850.tase2.client.MmsConnectionWrapper')
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_enumerate_data_points(self):
        """Test enumerate_data_points."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_names.return_value = ["ICC1"]
        self.mock_connection.get_domain_variables.return_value = ["Var1", "Var2"]
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.read_variable.return_value = 100.0

        client = TASE2Client()
        points = client.enumerate_data_points(max_points=10)

        self.assertGreater(len(points), 0)

    def test_test_control_access(self):
        """Test test_control_access."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True
        self.mock_connection.read_variable.return_value = 0

        client = TASE2Client()
        result = client.test_control_access("ICC1", "Breaker1")

        self.assertTrue(result)

    def test_test_rbe_capability(self):
        """Test test_rbe_capability."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_data_set_names.return_value = ["DS_TransferSet_1"]
        self.mock_connection.get_domain_variables.return_value = []

        client = TASE2Client()
        result = client.test_rbe_capability("ICC1")

        self.assertTrue(result)

    def test_analyze_security(self):
        """Test analyze_security returns analysis dict."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = ["Control_Point1"]
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.read_variable.return_value = 100.0

        client = TASE2Client()
        analysis = client.analyze_security()

        self.assertIsInstance(analysis, dict)
        self.assertIn("readable_points", analysis)
        self.assertIn("concerns", analysis)
        self.assertIn("recommendations", analysis)
        self.assertIsInstance(analysis["concerns"], list)
        self.assertIsInstance(analysis["recommendations"], list)


if __name__ == '__main__':
    unittest.main()
