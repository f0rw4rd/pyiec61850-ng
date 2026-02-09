#!/usr/bin/env python3
"""
Tests for TASE.2/ICCP module (pyiec61850.tase2)

These tests verify the TASE.2 client, types, constants, and exceptions
without requiring an actual TASE.2 server connection.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestTASE2Imports(unittest.TestCase):
    """Test module imports and availability."""

    def test_client_import(self):
        """Test TASE2Client can be imported."""
        from pyiec61850.tase2 import TASE2Client

        self.assertIsNotNone(TASE2Client)

    def test_types_import(self):
        """Test data types can be imported."""
        from pyiec61850.tase2 import (
            BilateralTable,
            ControlPoint,
            DataSet,
            Domain,
            PointValue,
            ServerInfo,
            TransferSet,
            Variable,
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
            CONFORMANCE_BLOCKS,
            DEFAULT_PORT,
            POINT_TYPES,
            QUALITY_GOOD,
            QUALITY_INVALID,
        )

        self.assertEqual(DEFAULT_PORT, 102)
        self.assertIsInstance(POINT_TYPES, dict)
        self.assertEqual(len(CONFORMANCE_BLOCKS), 9)
        self.assertEqual(QUALITY_GOOD, "GOOD")
        self.assertEqual(QUALITY_INVALID, "INVALID")

    def test_exceptions_import(self):
        """Test exceptions can be imported."""
        from pyiec61850.tase2 import (
            ConnectionError,
            ControlError,
            LibraryError,
            TASE2Error,
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
            QUALITY_SOURCE_TELEMETERED,
            QUALITY_VALIDITY_SUSPECT,
            QUALITY_VALIDITY_VALID,
            DataFlags,
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

        # Raw value: SUSPECT(4) | CALCULATED(32) = 36
        # Per libtase2: SUSPECT = 4 (HI bit only at bit 2)
        flags2 = DataFlags.from_raw(36)
        self.assertTrue(flags2.is_suspect)
        self.assertEqual(flags2.source, 32)  # CALCULATED

    def test_data_flags_round_trip(self):
        """Test DataFlags round-trip (from_raw -> raw_value)."""
        from pyiec61850.tase2 import (
            QUALITY_SOURCE_CALCULATED,
            QUALITY_SOURCE_ENTERED,
            QUALITY_SOURCE_ESTIMATED,
            QUALITY_SOURCE_TELEMETERED,
            QUALITY_VALIDITY_HELD,
            QUALITY_VALIDITY_NOT_VALID,
            QUALITY_VALIDITY_SUSPECT,
            QUALITY_VALIDITY_VALID,
            DataFlags,
        )

        # Test all validity/source combinations
        # Per libtase2: SUSPECT=4, HELD=8, NOT_VALID=12
        test_values = [
            QUALITY_VALIDITY_VALID | QUALITY_SOURCE_TELEMETERED,  # 0
            QUALITY_VALIDITY_SUSPECT | QUALITY_SOURCE_ENTERED,  # 4 | 16 = 20
            QUALITY_VALIDITY_HELD | QUALITY_SOURCE_CALCULATED,  # 8 | 32 = 40
            QUALITY_VALIDITY_NOT_VALID | QUALITY_SOURCE_ESTIMATED,  # 12 | 48 = 60
            64,  # Normal value flag
            128,  # Timestamp quality flag
            64 | 128,  # Both flags
        ]

        for raw in test_values:
            flags = DataFlags.from_raw(raw)
            # Round-trip should preserve the value
            self.assertEqual(flags.raw_value, raw, f"Round-trip failed for raw={raw}")

    def test_data_flags_reserved_bits_ignored(self):
        """Test DataFlags.from_raw ignores reserved bits 0-1 per IEC 60870-6."""
        from pyiec61850.tase2 import QUALITY_VALIDITY_VALID, DataFlags

        # Bits 0-1 are reserved and should be ignored during extraction.
        # A raw value with reserved bits set should still extract
        # validity=0 (VALID) since bits 2-3 are clear.
        flags_with_reserved = DataFlags.from_raw(0b00000011)  # Only reserved bits set
        self.assertEqual(flags_with_reserved.validity, QUALITY_VALIDITY_VALID)
        self.assertTrue(flags_with_reserved.is_valid)

        # Reserved bits should NOT pollute the validity field
        # Per libtase2: SUSPECT=4 (bit 2 only), so 0b00000111 = SUSPECT(4) + reserved bits(3)
        flags_with_suspect_and_reserved = DataFlags.from_raw(0b00000111)  # SUSPECT(4) + reserved(3)
        self.assertEqual(flags_with_suspect_and_reserved.validity, 4)  # SUSPECT
        self.assertTrue(flags_with_suspect_and_reserved.is_suspect)

    def test_transfer_set_conditions(self):
        """Test TransferSetConditions dataclass per IEC 60870-6-503 Section 8.1.7."""
        from pyiec61850.tase2 import (
            DS_CONDITIONS_CHANGE,
            DS_CONDITIONS_EXTERNAL_EVENT,
            DS_CONDITIONS_INTEGRITY,
            DS_CONDITIONS_INTERVAL,
            DS_CONDITIONS_OPERATOR_REQUEST,
            TransferSetConditions,
        )

        # Verify DSConditions bit positions per standard Section 8.1.7
        self.assertEqual(DS_CONDITIONS_INTERVAL, 1)  # bit 0
        self.assertEqual(DS_CONDITIONS_INTEGRITY, 2)  # bit 1
        self.assertEqual(DS_CONDITIONS_CHANGE, 4)  # bit 2
        self.assertEqual(DS_CONDITIONS_OPERATOR_REQUEST, 8)  # bit 3
        self.assertEqual(DS_CONDITIONS_EXTERNAL_EVENT, 16)  # bit 4

        # Test creation: INTERVAL(1) + CHANGE(4) = 5
        cond = TransferSetConditions(interval_timeout=True, object_change=True)
        self.assertTrue(cond.interval_timeout)
        self.assertTrue(cond.object_change)
        self.assertEqual(cond.raw_value, 5)  # 1 + 4

        # Test integrity_timeout field (bit 1)
        cond_int = TransferSetConditions(integrity_timeout=True)
        self.assertTrue(cond_int.integrity_timeout)
        self.assertEqual(cond_int.raw_value, 2)

        # Test from_raw: 9 = INTERVAL(1) + OPERATOR_REQUEST(8)
        cond2 = TransferSetConditions.from_raw(9)
        self.assertTrue(cond2.interval_timeout)
        self.assertFalse(cond2.integrity_timeout)
        self.assertFalse(cond2.object_change)
        self.assertTrue(cond2.operator_request)

        # Test from_raw with all conditions: 31 = all bits set
        cond3 = TransferSetConditions.from_raw(31)
        self.assertTrue(cond3.interval_timeout)
        self.assertTrue(cond3.integrity_timeout)
        self.assertTrue(cond3.object_change)
        self.assertTrue(cond3.operator_request)
        self.assertTrue(cond3.external_event)
        self.assertEqual(cond3.raw_value, 31)

        # Test round-trip
        for raw in [0, 1, 2, 4, 8, 16, 31, 5, 10, 21]:
            cond_rt = TransferSetConditions.from_raw(raw)
            self.assertEqual(cond_rt.raw_value, raw, f"Round-trip failed for raw={raw}")

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
        from pyiec61850.tase2 import QUALITY_VALIDITY_SUSPECT, DataFlags, PointValue

        flags = DataFlags(validity=QUALITY_VALIDITY_SUSPECT)  # SUSPECT = 8
        pv = PointValue(value=123.45, flags=flags)

        self.assertEqual(pv.value, 123.45)
        self.assertFalse(pv.is_valid)  # Uses flags.is_valid
        self.assertEqual(pv.quality_flags.validity_name, "SUSPECT")


class TestTASE2Client(unittest.TestCase):
    """Test client without connection."""

    def setUp(self):
        """Set up test fixtures with mocked connection."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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

        client = TASE2Client(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
        self.assertEqual(client._local_ap_title, "1.1.1.999")
        self.assertEqual(client._remote_ap_title, "1.1.1.998")

    def test_not_connected_error(self):
        """Test NotConnectedError when not connected."""
        from pyiec61850.tase2 import NotConnectedError, TASE2Client

        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.get_domains()

    def test_client_state(self):
        """Test client state property."""
        from pyiec61850.tase2 import STATE_DISCONNECTED, TASE2Client

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
        from pyiec61850.tase2 import ConnectionError, TASE2ConnectionError

        # TASE2ConnectionError should be the base class
        self.assertTrue(
            issubclass(ConnectionError, TASE2ConnectionError)
            or ConnectionError is TASE2ConnectionError
        )

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
            OperateError,
            SelectError,
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
            POINT_TYPE_DISCRETE,
            POINT_TYPE_REAL,
            POINT_TYPE_STATE,
            POINT_TYPE_STATE_SUPPLEMENTAL,
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
            CONTROL_TYPES,
        )

        self.assertEqual(CONTROL_TYPE_COMMAND, 1)
        self.assertIn(CONTROL_TYPE_COMMAND, CONTROL_TYPES)

    def test_conformance_blocks(self):
        """Test conformance block constants."""
        from pyiec61850.tase2 import (
            BLOCK_1,
            BLOCK_2,
            BLOCK_5,
            CONFORMANCE_BLOCKS,
        )

        self.assertEqual(BLOCK_1, 1)
        self.assertEqual(BLOCK_2, 2)
        self.assertEqual(BLOCK_5, 5)
        self.assertEqual(len(CONFORMANCE_BLOCKS), 9)

    def test_quality_flags(self):
        """Test quality flag constants."""
        from pyiec61850.tase2 import (
            QUALITY_GOOD,
            QUALITY_INVALID,
        )

        self.assertEqual(QUALITY_GOOD, "GOOD")
        self.assertEqual(QUALITY_INVALID, "INVALID")

    def test_tag_values(self):
        """Test tag value constants per libtase2 Tase2_TagValue."""
        from pyiec61850.tase2 import (
            TAG_CLOSE_ONLY_INHIBIT,
            TAG_INVALID,
            TAG_NONE,
            TAG_OPEN_AND_CLOSE_INHIBIT,
        )

        # Per libtase2: NO_TAG=0, OPEN_AND_CLOSE_INHIBIT=1, CLOSE_ONLY_INHIBIT=2, INVALID=3
        self.assertEqual(TAG_NONE, 0)
        self.assertEqual(TAG_OPEN_AND_CLOSE_INHIBIT, 1)
        self.assertEqual(TAG_CLOSE_ONLY_INHIBIT, 2)
        self.assertEqual(TAG_INVALID, 3)

    def test_command_values(self):
        """Test command value constants."""
        from pyiec61850.tase2 import CMD_OFF, CMD_ON

        self.assertEqual(CMD_OFF, 0)
        self.assertEqual(CMD_ON, 1)

    def test_client_states(self):
        """Test client state constants."""
        from pyiec61850.tase2 import (
            CLIENT_STATES,
            STATE_CONNECTED,
            STATE_DISCONNECTED,
        )

        self.assertEqual(STATE_DISCONNECTED, 0)
        self.assertEqual(STATE_CONNECTED, 2)
        self.assertIn(STATE_CONNECTED, CLIENT_STATES)

    def test_protocol_limits(self):
        """Test protocol limit constants."""
        from pyiec61850.tase2 import (
            MAX_DATA_SET_SIZE,
            MAX_POINT_NAME_LENGTH,
            SBO_TIMEOUT,
        )

        # Per IEC 60870-6
        self.assertEqual(MAX_DATA_SET_SIZE, 500)
        self.assertEqual(SBO_TIMEOUT, 30)
        self.assertEqual(MAX_POINT_NAME_LENGTH, 32)


class TestPointNameValidation(unittest.TestCase):
    """Test data point name validation per IEC 60870-6-503."""

    def test_valid_names(self):
        """Test valid TASE.2 point names per IEC 60870-6-503 Section 8.1.2."""
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
            "Device$SBO",  # $ is valid per ISO 9506-2 Section 2.6.2
            "TS1$Interval",  # Common TASE.2 naming pattern
            "$GlobalVar",  # $ at start is valid (not a digit)
        ]

        for name in valid_names:
            self.assertTrue(_validate_point_name(name), f"'{name}' should be valid")

    def test_invalid_names(self):
        """Test invalid TASE.2 point names."""
        from pyiec61850.tase2.client import _validate_point_name

        invalid_names = [
            "",  # Empty
            "1Point",  # Starts with digit
            "123",  # All digits
            "Point-1",  # Contains hyphen
            "Point.1",  # Contains dot
            "Point 1",  # Contains space
            "Point@1",  # Contains special char
            "a" * 33,  # Too long
        ]

        for name in invalid_names:
            self.assertFalse(_validate_point_name(name), f"'{name}' should be invalid")


class TestTASE2ClientMethods(unittest.TestCase):
    """Test client methods with mocked connection."""

    def setUp(self):
        """Set up test fixtures."""
        # Patch the MmsConnectionWrapper
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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
        self.mock_connection.connect.assert_called_once_with("192.168.1.100", 102, 10000)

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
        self.mock_connection.read_variable.assert_called_once_with("ICC1", "Voltage")


class TestTASE2ControlOperations(unittest.TestCase):
    """Test Block 5 control operations."""

    def setUp(self):
        """Set up test fixtures with mocked connection."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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
        from pyiec61850.tase2 import NotConnectedError, TASE2Client

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
        import time

        from pyiec61850.tase2 import OperateError, TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        # Manually set an expired select time (more than SBO_TIMEOUT ago)
        client._sbo_select_times["ICC1/Breaker1"] = time.time() - 31  # 31 seconds ago

        with self.assertRaises(OperateError) as ctx:
            client.operate_device("ICC1", "Breaker1", 1)

        self.assertIn("expired", str(ctx.exception).lower())

    def test_send_command_on(self):
        """Test sending ON command."""
        from pyiec61850.tase2 import CMD_ON, TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_command("ICC1", "Switch1", CMD_ON)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with("ICC1", "Switch1", CMD_ON)

    def test_send_command_off(self):
        """Test sending OFF command."""
        from pyiec61850.tase2 import CMD_OFF, TASE2Client

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
        self.mock_connection.write_variable.assert_called_with("ICC1", "VoltageSetpoint", 115.5)

    def test_send_setpoint_discrete(self):
        """Test sending discrete setpoint value."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_setpoint_discrete("ICC1", "TapPosition", 5)

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with("ICC1", "TapPosition", 5)

    def test_set_tag(self):
        """Test setting device tag."""
        from pyiec61850.tase2 import TAG_OPEN_AND_CLOSE_INHIBIT, TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.set_tag("ICC1", "Breaker1", TAG_OPEN_AND_CLOSE_INHIBIT, "Maintenance")

        self.assertTrue(result)

    def test_device_blocked_error(self):
        """Test OperateError when device write fails."""
        from pyiec61850.tase2 import OperateError, TASE2Client

        self.mock_connection.write_variable.side_effect = Exception("Access denied")

        client = TASE2Client()
        with self.assertRaises(OperateError):
            client.operate_device("ICC1", "Breaker1", 1)


class TestTASE2TransferSets(unittest.TestCase):
    """Test Block 2 transfer set operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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
        from pyiec61850.tase2 import TASE2Client

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
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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
        self.mock_connection.write_variable.assert_called_with("ICC1", "Setpoint1", 100.5)

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
        from pyiec61850.tase2 import QUALITY_INVALID, TASE2Client

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
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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
        from pyiec61850.tase2 import DomainNotFoundError, TASE2Client

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
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_connection_timeout(self):
        """Test connection timeout handling."""
        from pyiec61850.tase2 import ConnectionFailedError, TASE2Client

        self.mock_connection.connect.side_effect = ConnectionFailedError(
            "192.168.1.100", 102, "timeout"
        )

        client = TASE2Client()
        with self.assertRaises(ConnectionFailedError):
            client.connect("192.168.1.100")

    def test_read_error_access_denied(self):
        """Test ReadError when access denied."""
        from pyiec61850.tase2 import ReadError, TASE2Client

        self.mock_connection.is_connected = True
        self.mock_connection.read_variable.side_effect = Exception("Access denied")

        client = TASE2Client()
        with self.assertRaises(ReadError) as ctx:
            client.read_point("ICC1", "SecretVar")

        self.assertIn("ICC1/SecretVar", str(ctx.exception))

    def test_invalid_parameter_handling(self):
        """Test handling of invalid parameters."""
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
                MmsConnectionWrapper(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
        else:
            # Library available, test normal creation
            wrapper = MmsConnectionWrapper(local_ap_title="1.1.1.999", remote_ap_title="1.1.1.998")
            self.assertFalse(wrapper.is_connected)

    def test_wrapper_is_available(self):
        """Test is_available function."""
        from pyiec61850.tase2.connection import is_available

        result = is_available()
        self.assertIsInstance(result, bool)

    def test_wrapper_state_disconnected(self):
        """Test wrapper state when disconnected."""
        from pyiec61850.tase2 import STATE_DISCONNECTED
        from pyiec61850.tase2.connection import MmsConnectionWrapper, is_available
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
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
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


class TestConnectionStateTracking(unittest.TestCase):
    """Test Phase 1: Connection state tracking and callbacks."""

    def test_state_callback_registration(self):
        """Test registering and unregistering state callbacks."""
        from pyiec61850.tase2.connection import MmsConnectionWrapper, is_available
        from pyiec61850.tase2.exceptions import LibraryNotFoundError

        if not is_available():
            with self.assertRaises(LibraryNotFoundError):
                MmsConnectionWrapper()
            return

        wrapper = MmsConnectionWrapper()
        callback_calls = []

        def on_state_change(old, new):
            callback_calls.append((old, new))

        wrapper.register_state_callback(on_state_change)
        self.assertEqual(len(wrapper._state_callbacks), 1)

        # Fire manually
        wrapper._fire_state_callbacks(2, 0)
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(callback_calls[0], (2, 0))

        wrapper.unregister_state_callback(on_state_change)
        self.assertEqual(len(wrapper._state_callbacks), 0)

    def test_state_callback_error_handling(self):
        """Test that callback errors don't crash state tracking."""
        from pyiec61850.tase2.connection import MmsConnectionWrapper, is_available

        if not is_available():
            self.skipTest("pyiec61850 not available")

        wrapper = MmsConnectionWrapper()

        def bad_callback(old, new):
            raise RuntimeError("Callback error")

        wrapper.register_state_callback(bad_callback)
        # Should not raise
        wrapper._fire_state_callbacks(2, 0)


class TestConnectionLossNotification(unittest.TestCase):
    """Test Phase 1: Connection loss notification in client."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.state = 2
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_connection_lost_callback_fires(self):
        """Test user callback fires on connection loss."""
        from pyiec61850.tase2 import STATE_CONNECTED, STATE_DISCONNECTED, TASE2Client

        callback_fired = []
        client = TASE2Client()
        client.on_connection_lost = lambda: callback_fired.append(True)

        # Simulate connection loss
        client._handle_state_change(STATE_CONNECTED, STATE_DISCONNECTED)

        self.assertEqual(len(callback_fired), 1)

    def test_connection_lost_clears_sbo(self):
        """Test connection loss clears SBO state."""
        from pyiec61850.tase2 import STATE_CONNECTED, STATE_DISCONNECTED, TASE2Client

        client = TASE2Client()
        client._sbo_select_times["ICC1/Breaker1"] = 12345.0

        client._handle_state_change(STATE_CONNECTED, STATE_DISCONNECTED)

        self.assertEqual(len(client._sbo_select_times), 0)

    def test_on_connection_lost_property(self):
        """Test on_connection_lost property getter/setter."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertIsNone(client.on_connection_lost)

        def handler():
            return None

        client.on_connection_lost = handler
        self.assertEqual(client.on_connection_lost, handler)


class TestErrorMapping(unittest.TestCase):
    """Test Phase 1: IED error code mapping."""

    def test_map_access_denied(self):
        """Test ACCESS_DENIED maps to AccessDeniedError."""
        from pyiec61850.tase2.exceptions import AccessDeniedError, map_ied_error

        try:
            import pyiec61850.pyiec61850 as iec61850

            code = getattr(iec61850, "IED_ERROR_ACCESS_DENIED", 3)
        except ImportError:
            code = 3

        err = map_ied_error(code, "test/var")
        self.assertIsInstance(err, AccessDeniedError)

    def test_map_timeout(self):
        """Test TIMEOUT maps to TASE2TimeoutError."""
        from pyiec61850.tase2.exceptions import TASE2TimeoutError, map_ied_error

        try:
            import pyiec61850.pyiec61850 as iec61850

            code = getattr(iec61850, "IED_ERROR_TIMEOUT", 7)
        except ImportError:
            code = 7

        err = map_ied_error(code, "read op")
        self.assertIsInstance(err, TASE2TimeoutError)

    def test_map_connection_lost(self):
        """Test CONNECTION_LOST maps to ConnectionClosedError."""
        from pyiec61850.tase2.exceptions import ConnectionClosedError, map_ied_error

        try:
            import pyiec61850.pyiec61850 as iec61850

            code = getattr(iec61850, "IED_ERROR_CONNECTION_LOST", 10)
        except ImportError:
            code = 10

        err = map_ied_error(code, "")
        self.assertIsInstance(err, ConnectionClosedError)

    def test_map_object_not_found(self):
        """Test OBJECT_DOES_NOT_EXIST maps to VariableNotFoundError."""
        from pyiec61850.tase2.exceptions import VariableNotFoundError, map_ied_error

        try:
            import pyiec61850.pyiec61850 as iec61850

            code = getattr(iec61850, "IED_ERROR_OBJECT_DOES_NOT_EXIST", 5)
        except ImportError:
            code = 5

        err = map_ied_error(code, "ICC1/NonExistent")
        self.assertIsInstance(err, VariableNotFoundError)

    def test_map_unknown_error(self):
        """Test unknown error code returns TASE2Error."""
        from pyiec61850.tase2.exceptions import TASE2Error, map_ied_error

        err = map_ied_error(999, "unknown op")
        self.assertIsInstance(err, TASE2Error)
        self.assertIn("999", str(err))


class TestDataSetLifecycle(unittest.TestCase):
    """Test Phase 2: Data set create/delete operations."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_create_data_set(self):
        """Test creating a data set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.create_data_set.return_value = True

        client = TASE2Client()
        result = client.create_data_set("ICC1", "MyDS", ["Var1", "Var2", "Var3"])

        self.assertTrue(result)
        self.mock_connection.create_data_set.assert_called_once_with(
            "ICC1", "MyDS", ["Var1", "Var2", "Var3"]
        )

    def test_create_data_set_empty_members(self):
        """Test creating data set with empty members raises error."""
        from pyiec61850.tase2 import TASE2Client, TASE2Error

        client = TASE2Client()
        with self.assertRaises(TASE2Error):
            client.create_data_set("ICC1", "MyDS", [])

    def test_create_data_set_exceeds_limit(self):
        """Test creating data set exceeding TASE.2 limit raises error."""
        from pyiec61850.tase2 import MAX_DATA_SET_SIZE, TASE2Client, TASE2Error

        client = TASE2Client()
        members = [f"Var{i}" for i in range(MAX_DATA_SET_SIZE + 1)]
        with self.assertRaises(TASE2Error):
            client.create_data_set("ICC1", "BigDS", members)

    def test_delete_data_set(self):
        """Test deleting a data set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.delete_data_set.return_value = True

        client = TASE2Client()
        result = client.delete_data_set("ICC1", "MyDS")

        self.assertTrue(result)
        self.mock_connection.delete_data_set.assert_called_once_with("ICC1", "MyDS")


class TestTransferSetStandard(unittest.TestCase):
    """Test Phase 2: Standard TASE.2 transfer set variable names."""

    def test_standard_variable_names_defined(self):
        """Test standard DSTS variable names are defined."""
        from pyiec61850.tase2 import (
            DSTS_VAR_DATA_SET_NAME,
            DSTS_VAR_INTERVAL,
            DSTS_VAR_RBE,
            DSTS_VAR_STATUS,
            TRANSFER_REPORT_ACK,
            TRANSFER_REPORT_NACK,
        )

        self.assertEqual(DSTS_VAR_DATA_SET_NAME, "DSTransferSet_DataSetName")
        self.assertEqual(DSTS_VAR_INTERVAL, "DSTransferSet_Interval")
        self.assertEqual(DSTS_VAR_RBE, "DSTransferSet_RBE")
        self.assertEqual(DSTS_VAR_STATUS, "DSTransferSet_Status")
        self.assertEqual(TRANSFER_REPORT_ACK, "Transfer_Report_ACK")
        self.assertEqual(TRANSFER_REPORT_NACK, "Transfer_Report_NACK")

    def test_enable_transfer_set_tries_standard_first(self):
        """Test enable_transfer_set tries DSTransferSet_Status first."""
        from pyiec61850.tase2 import TASE2Client

        patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        mock_wrapper_class = patcher.start()
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.register_state_callback = MagicMock()
        mock_conn.write_variable.return_value = True
        mock_wrapper_class.return_value = mock_conn

        try:
            client = TASE2Client()
            client.enable_transfer_set("ICC1", "TS1")

            # First call should be to standard variable
            first_call = mock_conn.write_variable.call_args_list[0]
            self.assertEqual(first_call[0][1], "DSTransferSet_Status")
        finally:
            patcher.stop()


class TestDSTransferSetConfig(unittest.TestCase):
    """Test Phase 2: DSTransferSetConfig dataclass."""

    def test_config_creation(self):
        """Test DSTransferSetConfig creation."""
        from pyiec61850.tase2 import DSTransferSetConfig, TransferSetConditions

        config = DSTransferSetConfig(
            data_set_name="MyDS",
            interval=10,
            rbe=True,
            ds_conditions=TransferSetConditions(interval_timeout=True, object_change=True),
        )

        self.assertEqual(config.data_set_name, "MyDS")
        self.assertEqual(config.interval, 10)
        self.assertTrue(config.rbe)
        self.assertTrue(config.ds_conditions.interval_timeout)

    def test_config_serialization(self):
        """Test DSTransferSetConfig to_dict."""
        from pyiec61850.tase2 import DSTransferSetConfig

        config = DSTransferSetConfig(
            data_set_name="DS1",
            interval=5,
            buffer_time=2,
        )

        d = config.to_dict()
        self.assertEqual(d["data_set_name"], "DS1")
        self.assertEqual(d["interval"], 5)
        self.assertEqual(d["buffer_time"], 2)

    def test_configure_transfer_set(self):
        """Test configure_transfer_set writes standard variables."""
        from pyiec61850.tase2 import DSTransferSetConfig, TASE2Client

        patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        mock_wrapper_class = patcher.start()
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.register_state_callback = MagicMock()
        mock_conn.write_variable.return_value = True
        mock_wrapper_class.return_value = mock_conn

        try:
            client = TASE2Client()
            config = DSTransferSetConfig(
                data_set_name="MyDS",
                interval=10,
            )
            result = client.configure_transfer_set("ICC1", "TS1", config)
            self.assertTrue(result)
            # Should have written at least 2 variables
            self.assertGreaterEqual(mock_conn.write_variable.call_count, 2)
        finally:
            patcher.stop()


class TestReportQueue(unittest.TestCase):
    """Test Phase 3: Report queue and callback."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_get_next_report_empty(self):
        """Test get_next_report returns None when queue is empty."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        report = client.get_next_report(timeout=0.01)
        self.assertIsNone(report)

    def test_get_next_report_nonblocking(self):
        """Test non-blocking get_next_report."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        report = client.get_next_report()
        self.assertIsNone(report)

    def test_report_queue_put_and_get(self):
        """Test putting and getting reports from queue."""
        from pyiec61850.tase2 import TASE2Client, TransferReport

        client = TASE2Client()
        report = TransferReport(
            domain="ICC1",
            transfer_set_name="TS1",
            values=[],
        )
        client._report_queue.put(report)

        result = client.get_next_report(timeout=1.0)
        self.assertIsNotNone(result)
        self.assertEqual(result.domain, "ICC1")
        self.assertEqual(result.transfer_set_name, "TS1")

    def test_set_report_callback(self):
        """Test setting report callback."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()

        def callback(report):
            return None

        client.set_report_callback(callback)
        self.assertEqual(client._report_callback, callback)

        client.set_report_callback(None)
        self.assertIsNone(client._report_callback)


class TestTransferReport(unittest.TestCase):
    """Test Phase 3: TransferReport dataclass."""

    def test_transfer_report_creation(self):
        """Test TransferReport creation."""
        from pyiec61850.tase2 import PointValue, TransferReport

        report = TransferReport(
            domain="ICC1",
            transfer_set_name="TS1",
            values=[
                PointValue(value=230.5, name="Voltage"),
                PointValue(value=50.0, name="Frequency"),
            ],
            sequence_number=42,
        )

        self.assertEqual(report.domain, "ICC1")
        self.assertEqual(len(report.values), 2)
        self.assertEqual(report.sequence_number, 42)

    def test_transfer_report_serialization(self):
        """Test TransferReport to_dict."""
        from datetime import datetime, timezone

        from pyiec61850.tase2 import TransferReport

        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        report = TransferReport(
            domain="ICC1",
            transfer_set_name="TS1",
            values=[],
            timestamp=ts,
            sequence_number=1,
        )

        d = report.to_dict()
        self.assertEqual(d["domain"], "ICC1")
        self.assertIn("timestamp", d)
        self.assertEqual(d["sequence_number"], 1)


class TestTransferReportACK(unittest.TestCase):
    """Test Phase 3: Transfer Report ACK."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_send_transfer_report_ack(self):
        """Test ACK written to correct variable."""
        from pyiec61850.tase2 import TRANSFER_REPORT_ACK, TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_transfer_report_ack("ICC1")

        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_with("ICC1", TRANSFER_REPORT_ACK, 1)


class TestBilateralValidation(unittest.TestCase):
    """Test Phase 4: Post-connect bilateral table reading."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_parse_supported_features(self):
        """Test parsing Supported_Features bitstring."""
        from pyiec61850.tase2 import BLOCK_1, BLOCK_2, BLOCK_5, TASE2Client

        client = TASE2Client()
        # Per ASN.1 BITSTRING: Block 1=0x80, Block 2=0x40, Block 5=0x08
        # Block 1 + Block 2 + Block 5 = 0x80 | 0x40 | 0x08 = 0xC8
        client._parse_supported_features(0xC8)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertIn(BLOCK_1, blocks)
        self.assertIn(BLOCK_2, blocks)
        self.assertIn(BLOCK_5, blocks)

    def test_check_block_support_warning(self):
        """Test _check_block_support logs warning for unsupported blocks."""
        import logging

        from pyiec61850.tase2 import BLOCK_5, TASE2Client

        client = TASE2Client()
        client._server_capabilities["supported_blocks"] = [1, 2]

        # Reset global logging.disable() set by test_mms.py at module level
        logger = logging.getLogger("pyiec61850.tase2.client")
        old_manager_disable = logging.root.manager.disable
        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs(logger, level="WARNING") as cm:
                client._check_block_support(BLOCK_5, "select_device")
            self.assertTrue(any("Block 5" in msg for msg in cm.output))
        finally:
            logging.root.manager.disable = old_manager_disable

    def test_check_block_support_no_warning_when_no_info(self):
        """Test _check_block_support does nothing when no capabilities."""

        from pyiec61850.tase2 import BLOCK_5, TASE2Client

        client = TASE2Client()
        # No capabilities loaded - should not warn
        # This should not raise
        client._check_block_support(BLOCK_5, "test")


class TestSBOCheckBack(unittest.TestCase):
    """Test Phase 4: SBO CheckBack ID capture and echo."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.write_variable.return_value = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_select_captures_sbo_state(self):
        """Test select_device captures SBOState."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.return_value = 42

        client = TASE2Client()
        result = client.select_device("ICC1", "Breaker1")

        self.assertTrue(result)
        self.assertIn("ICC1/Breaker1", client._sbo_states)
        state = client._sbo_states["ICC1/Breaker1"]
        self.assertEqual(state.domain, "ICC1")
        self.assertEqual(state.device, "Breaker1")

    def test_operate_clears_sbo_state(self):
        """Test operate_device clears SBOState."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.select_device("ICC1", "Breaker1")
        client.operate_device("ICC1", "Breaker1", 1)

        self.assertNotIn("ICC1/Breaker1", client._sbo_states)

    def test_sbo_state_dataclass(self):
        """Test SBOState dataclass."""
        from pyiec61850.tase2 import SBOState

        state = SBOState(
            select_time=12345.0,
            domain="ICC1",
            device="Breaker1",
            checkback_id=42,
        )
        self.assertEqual(state.checkback_id, 42)
        self.assertEqual(state.domain, "ICC1")


class TestStructuredValueSizes(unittest.TestCase):
    """Test Phase 4: Structured value parsing for all sizes 1-4."""

    def test_point_value_with_flags_and_timestamp(self):
        """Test PointValue with flags and timestamp."""
        from datetime import datetime, timezone

        from pyiec61850.tase2 import QUALITY_VALIDITY_VALID, DataFlags, PointValue

        ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        flags = DataFlags(validity=QUALITY_VALIDITY_VALID)
        pv = PointValue(
            value=230.5,
            flags=flags,
            timestamp=ts,
            cov_counter=5,
            name="Voltage",
            domain="ICC1",
        )

        self.assertEqual(pv.value, 230.5)
        self.assertTrue(pv.is_valid)
        self.assertEqual(pv.timestamp, ts)
        self.assertEqual(pv.cov_counter, 5)

        d = pv.to_dict()
        self.assertIn("cov_counter", d)
        self.assertEqual(d["cov_counter"], 5)


class TestFullTransferSetLifecycle(unittest.TestCase):
    """Test Phase 3: Full transfer set lifecycle (mocked)."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.write_variable.return_value = True
        self.mock_connection.create_data_set.return_value = True
        self.mock_connection.delete_data_set.return_value = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_full_lifecycle(self):
        """Test create -> configure -> enable -> receive -> disable -> delete."""
        from pyiec61850.tase2 import (
            DSTransferSetConfig,
            PointValue,
            TASE2Client,
            TransferReport,
            TransferSetConditions,
        )

        client = TASE2Client()

        # 1. Create data set
        result = client.create_data_set("ICC1", "MyDS", ["Var1", "Var2"])
        self.assertTrue(result)

        # 2. Configure transfer set
        config = DSTransferSetConfig(
            data_set_name="MyDS",
            interval=10,
            rbe=True,
            ds_conditions=TransferSetConditions(interval_timeout=True, object_change=True),
        )
        result = client.configure_transfer_set("ICC1", "TS1", config)
        self.assertTrue(result)

        # 3. Start receiving reports
        client.start_receiving_reports()

        # 4. Enable transfer set
        result = client.enable_transfer_set("ICC1", "TS1")
        self.assertTrue(result)

        # 5. Simulate receiving a report (put in queue)
        report = TransferReport(
            domain="ICC1",
            transfer_set_name="TS1",
            values=[PointValue(value=100.0, name="Var1")],
        )
        client._report_queue.put(report)

        # 6. Get report from queue
        received = client.get_next_report(timeout=1.0)
        self.assertIsNotNone(received)
        self.assertEqual(received.domain, "ICC1")

        # 7. Send ACK
        result = client.send_transfer_report_ack("ICC1")
        self.assertTrue(result)

        # 8. Disable transfer set
        result = client.disable_transfer_set("ICC1", "TS1")
        self.assertTrue(result)

        # 9. Stop receiving
        client.stop_receiving_reports()

        # 10. Delete data set
        result = client.delete_data_set("ICC1", "MyDS")
        self.assertTrue(result)


class TestNewImports(unittest.TestCase):
    """Test that all new types and constants are importable."""

    def test_new_types_import(self):
        """Test new data types can be imported."""
        from pyiec61850.tase2 import (
            DSTransferSetConfig,
            SBOState,
            TransferReport,
        )

        self.assertIsNotNone(DSTransferSetConfig)
        self.assertIsNotNone(TransferReport)
        self.assertIsNotNone(SBOState)

    def test_new_constants_import(self):
        """Test new constants can be imported."""
        from pyiec61850.tase2 import (
            DSTS_VAR_DATA_SET_NAME,
            STATE_CHECK_INTERVAL,
            SUPPORTED_FEATURES_BLOCK_1,
        )

        self.assertEqual(STATE_CHECK_INTERVAL, 5.0)
        self.assertIsInstance(DSTS_VAR_DATA_SET_NAME, str)
        self.assertIsInstance(SUPPORTED_FEATURES_BLOCK_1, int)

    def test_map_ied_error_import(self):
        """Test map_ied_error can be imported."""
        from pyiec61850.tase2 import map_ied_error

        self.assertTrue(callable(map_ied_error))

    def test_version_updated(self):
        """Test version was updated."""
        from pyiec61850.tase2 import __version__

        self.assertEqual(__version__, "0.4.0")


class TestInformationReportParsing(unittest.TestCase):
    """Test Phase 3: InformationReport MmsValue parsing."""

    def test_py_info_report_handler_creation(self):
        """Test _PyInfoReportHandler can be created."""
        import queue

        from pyiec61850.tase2.connection import _PyInfoReportHandler

        q = queue.Queue()
        handler = _PyInfoReportHandler(q)
        self.assertIsNotNone(handler)

    def test_py_info_report_handler_with_callback(self):
        """Test _PyInfoReportHandler with callback."""
        import queue

        from pyiec61850.tase2.connection import _PyInfoReportHandler

        q = queue.Queue()
        received = []
        handler = _PyInfoReportHandler(q, report_callback=lambda r: received.append(r))

        # Trigger without SWIG data (should create a report with empty values)
        handler.trigger()

        self.assertEqual(q.qsize(), 1)
        report = q.get_nowait()
        self.assertEqual(report.domain, "")
        self.assertEqual(len(report.values), 0)
        self.assertEqual(len(received), 1)

    def test_py_info_report_handler_trigger_queues_report(self):
        """Test that trigger() puts a TransferReport into the queue."""
        import queue

        from pyiec61850.tase2.connection import _PyInfoReportHandler

        q = queue.Queue()
        handler = _PyInfoReportHandler(q)
        handler.trigger()

        self.assertFalse(q.empty())
        report = q.get_nowait()
        self.assertIsNotNone(report.timestamp)


class TestReportCallback(unittest.TestCase):
    """Test Phase 3: Report callback invocation."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_report_callback_called_on_queue_report(self):
        """Test report callback is stored and accessible."""
        from pyiec61850.tase2 import TASE2Client

        received = []
        client = TASE2Client()
        client.set_report_callback(lambda r: received.append(r))

        self.assertIsNotNone(client._report_callback)

    def test_report_callback_clear(self):
        """Test clearing report callback."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.set_report_callback(lambda r: None)
        self.assertIsNotNone(client._report_callback)

        client.set_report_callback(None)
        self.assertIsNone(client._report_callback)


class TestNewConstantExports(unittest.TestCase):
    """Test that newly added constant exports are importable."""

    def test_new_dsts_constants_import(self):
        """Test new DSTS variable name exports."""
        from pyiec61850.tase2 import (
            DS_CONDITIONS_DETECTED,
            DSTS_VAR_BLOCK_DATA,
            DSTS_VAR_CRITICAL,
            DSTS_VAR_EVENT_CODE_REQUESTED,
            DSTS_VAR_START_TIME,
            DSTS_VAR_TLE,
            NEXT_DS_TRANSFER_SET,
            TRANSFER_SET_TIMESTAMP,
        )

        self.assertEqual(DSTS_VAR_START_TIME, "DSTransferSet_StartTime")
        self.assertEqual(DSTS_VAR_TLE, "DSTransferSet_TLE")
        self.assertEqual(DSTS_VAR_CRITICAL, "DSTransferSet_Critical")
        self.assertEqual(DSTS_VAR_BLOCK_DATA, "DSTransferSet_BlockData")
        self.assertEqual(DSTS_VAR_EVENT_CODE_REQUESTED, "DSTransferSet_EventCodeRequested")
        self.assertEqual(NEXT_DS_TRANSFER_SET, "Next_DSTransfer_Set")
        self.assertEqual(DS_CONDITIONS_DETECTED, "DSConditions_Detected")
        self.assertEqual(TRANSFER_SET_TIMESTAMP, "Transfer_Set_Time_Stamp")


class TestInformationMessage(unittest.TestCase):
    """Test Block 4: InformationMessage dataclass."""

    def test_creation_with_text(self):
        """Test InformationMessage with text content."""
        from pyiec61850.tase2 import InformationMessage

        msg = InformationMessage(
            info_ref=1,
            local_ref=2,
            msg_id=100,
            content=b"Hello from Control Center A",
        )
        self.assertEqual(msg.info_ref, 1)
        self.assertEqual(msg.local_ref, 2)
        self.assertEqual(msg.msg_id, 100)
        self.assertEqual(msg.text, "Hello from Control Center A")
        self.assertEqual(msg.size, 27)

    def test_creation_with_string_content(self):
        """Test InformationMessage with string content."""
        from pyiec61850.tase2 import InformationMessage

        msg = InformationMessage(
            info_ref=1,
            local_ref=1,
            msg_id=1,
            content="ASCII text message",
        )
        self.assertEqual(msg.text, "ASCII text message")
        self.assertEqual(msg.size, 18)

    def test_creation_with_binary_content(self):
        """Test InformationMessage with binary content."""
        from pyiec61850.tase2 import InformationMessage

        binary_data = bytes([0x00, 0x01, 0xFF, 0xFE])
        msg = InformationMessage(
            info_ref=3,
            local_ref=4,
            msg_id=200,
            content=binary_data,
        )
        self.assertEqual(msg.size, 4)
        self.assertEqual(msg.content, binary_data)

    def test_default_values(self):
        """Test InformationMessage default values."""
        from pyiec61850.tase2 import InformationMessage

        msg = InformationMessage()
        self.assertEqual(msg.info_ref, 0)
        self.assertEqual(msg.local_ref, 0)
        self.assertEqual(msg.msg_id, 0)
        self.assertEqual(msg.content, b"")
        self.assertEqual(msg.size, 0)
        self.assertIsNone(msg.timestamp)

    def test_with_timestamp(self):
        """Test InformationMessage with timestamp."""
        from datetime import datetime, timezone

        from pyiec61850.tase2 import InformationMessage

        ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        msg = InformationMessage(
            info_ref=1,
            local_ref=1,
            msg_id=1,
            content=b"test",
            timestamp=ts,
        )
        self.assertEqual(msg.timestamp, ts)

    def test_serialization(self):
        """Test InformationMessage to_dict."""
        from datetime import datetime, timezone

        from pyiec61850.tase2 import InformationMessage

        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        msg = InformationMessage(
            info_ref=5,
            local_ref=6,
            msg_id=42,
            content=b"Test message",
            timestamp=ts,
        )
        d = msg.to_dict()
        self.assertEqual(d["info_ref"], 5)
        self.assertEqual(d["local_ref"], 6)
        self.assertEqual(d["msg_id"], 42)
        self.assertEqual(d["text"], "Test message")
        self.assertIn("timestamp", d)

    def test_serialization_binary(self):
        """Test InformationMessage to_dict with binary content."""
        from pyiec61850.tase2 import InformationMessage

        msg = InformationMessage(
            info_ref=1,
            local_ref=1,
            msg_id=1,
            content=bytes([0xFF, 0xFE, 0x80]),
        )
        d = msg.to_dict()
        self.assertTrue(d.get("binary", False))


class TestIMTransferSetConfig(unittest.TestCase):
    """Test Block 4: IMTransferSetConfig dataclass."""

    def test_creation(self):
        """Test IMTransferSetConfig creation."""
        from pyiec61850.tase2 import IMTransferSetConfig

        config = IMTransferSetConfig(enabled=True, name="IM_TS")
        self.assertTrue(config.enabled)
        self.assertEqual(config.name, "IM_TS")

    def test_default_values(self):
        """Test IMTransferSetConfig defaults."""
        from pyiec61850.tase2 import IMTransferSetConfig

        config = IMTransferSetConfig()
        self.assertFalse(config.enabled)
        self.assertIsNone(config.name)

    def test_serialization(self):
        """Test IMTransferSetConfig to_dict."""
        from pyiec61850.tase2 import IMTransferSetConfig

        config = IMTransferSetConfig(enabled=True, name="MyIMTS")
        d = config.to_dict()
        self.assertTrue(d["enabled"])
        self.assertEqual(d["name"], "MyIMTS")


class TestInformationBuffer(unittest.TestCase):
    """Test Block 4: InformationBuffer dataclass."""

    def test_creation(self):
        """Test InformationBuffer creation."""
        from pyiec61850.tase2 import InformationBuffer

        buf = InformationBuffer(
            name="InfoBuf1",
            domain="ICC1",
            max_size=64,
            entry_count=3,
        )
        self.assertEqual(buf.name, "InfoBuf1")
        self.assertEqual(buf.domain, "ICC1")
        self.assertEqual(buf.max_size, 64)
        self.assertEqual(buf.entry_count, 3)

    def test_with_messages(self):
        """Test InformationBuffer with messages."""
        from pyiec61850.tase2 import InformationBuffer, InformationMessage

        msgs = [
            InformationMessage(info_ref=1, content=b"msg1"),
            InformationMessage(info_ref=2, content=b"msg2"),
        ]
        buf = InformationBuffer(
            name="InfoBuf1",
            domain="ICC1",
            messages=msgs,
        )
        self.assertEqual(len(buf.messages), 2)

    def test_serialization(self):
        """Test InformationBuffer to_dict."""
        from pyiec61850.tase2 import InformationBuffer, InformationMessage

        buf = InformationBuffer(
            name="Buf1",
            domain="ICC1",
            max_size=128,
            entry_count=1,
            messages=[InformationMessage(info_ref=1, content=b"test")],
        )
        d = buf.to_dict()
        self.assertEqual(d["name"], "Buf1")
        self.assertEqual(d["domain"], "ICC1")
        self.assertEqual(d["max_size"], 128)
        self.assertEqual(len(d["messages"]), 1)


class TestBlock4Constants(unittest.TestCase):
    """Test Block 4 constants."""

    def test_im_transfer_set_vars(self):
        """Test IM Transfer Set variable name constants."""
        from pyiec61850.tase2 import IMTS_VAR_NAME, IMTS_VAR_STATUS

        self.assertEqual(IMTS_VAR_NAME, "IM_Transfer_Set")
        self.assertEqual(IMTS_VAR_STATUS, "IM_Transfer_Set_Status")

    def test_info_buffer_vars(self):
        """Test Information Buffer variable name constants."""
        from pyiec61850.tase2 import (
            INFO_BUFF_VAR_ENTRIES,
            INFO_BUFF_VAR_NAME,
            INFO_BUFF_VAR_NEXT_ENTRY,
            INFO_BUFF_VAR_SIZE,
        )

        self.assertEqual(INFO_BUFF_VAR_NAME, "Information_Buffer_Name")
        self.assertEqual(INFO_BUFF_VAR_SIZE, "Information_Buffer_Size")
        self.assertEqual(INFO_BUFF_VAR_NEXT_ENTRY, "Next_Buffer_Entry")
        self.assertEqual(INFO_BUFF_VAR_ENTRIES, "Buffer_Entry_Count")

    def test_info_message_vars(self):
        """Test Information Message variable name constants."""
        from pyiec61850.tase2 import (
            INFO_MSG_VAR_CONTENT,
            INFO_MSG_VAR_INFO_REF,
            INFO_MSG_VAR_LOCAL_REF,
            INFO_MSG_VAR_MSG_ID,
        )

        self.assertEqual(INFO_MSG_VAR_INFO_REF, "InfoRef")
        self.assertEqual(INFO_MSG_VAR_LOCAL_REF, "LocalRef")
        self.assertEqual(INFO_MSG_VAR_MSG_ID, "MsgId")
        self.assertEqual(INFO_MSG_VAR_CONTENT, "InfoContent")

    def test_block4_limits(self):
        """Test Block 4 limit constants."""
        from pyiec61850.tase2 import DEFAULT_INFO_BUFFER_SIZE, MAX_INFO_MESSAGE_SIZE

        self.assertEqual(MAX_INFO_MESSAGE_SIZE, 65535)
        self.assertEqual(DEFAULT_INFO_BUFFER_SIZE, 64)

    def test_supported_features_block4(self):
        """Test SUPPORTED_FEATURES_BLOCK_4 constant."""
        from pyiec61850.tase2 import SUPPORTED_FEATURES_BLOCK_4

        # Per ASN.1 BITSTRING: Block 4 = bit 3 = 0x10
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_4, 0x10)


class TestBlock4Exceptions(unittest.TestCase):
    """Test Block 4 exception hierarchy."""

    def test_information_message_error(self):
        """Test InformationMessageError."""
        from pyiec61850.tase2 import InformationMessageError, TASE2Error

        self.assertTrue(issubclass(InformationMessageError, TASE2Error))
        err = InformationMessageError("test error")
        self.assertIn("test error", str(err))

    def test_im_transfer_set_error(self):
        """Test IMTransferSetError."""
        from pyiec61850.tase2 import IMTransferSetError, InformationMessageError

        self.assertTrue(issubclass(IMTransferSetError, InformationMessageError))
        err = IMTransferSetError("enable failed")
        self.assertIn("enable failed", str(err))

    def test_im_not_supported_error(self):
        """Test IMNotSupportedError."""
        from pyiec61850.tase2 import IMNotSupportedError, InformationMessageError

        self.assertTrue(issubclass(IMNotSupportedError, InformationMessageError))
        err = IMNotSupportedError()
        self.assertIn("Block 4", str(err))


class TestBlock4Imports(unittest.TestCase):
    """Test Block 4 imports from main package."""

    def test_types_import(self):
        """Test Block 4 types can be imported."""
        from pyiec61850.tase2 import (
            IMTransferSetConfig,
            InformationBuffer,
            InformationMessage,
        )

        self.assertIsNotNone(InformationMessage)
        self.assertIsNotNone(IMTransferSetConfig)
        self.assertIsNotNone(InformationBuffer)

    def test_exceptions_import(self):
        """Test Block 4 exceptions can be imported."""
        from pyiec61850.tase2 import (
            IMNotSupportedError,
            IMTransferSetError,
            InformationMessageError,
        )

        self.assertIsNotNone(InformationMessageError)
        self.assertIsNotNone(IMTransferSetError)
        self.assertIsNotNone(IMNotSupportedError)

    def test_constants_import(self):
        """Test Block 4 constants can be imported."""
        from pyiec61850.tase2 import (
            IMTS_VAR_NAME,
            IMTS_VAR_STATUS,
            INFO_BUFF_VAR_ENTRIES,
            INFO_BUFF_VAR_NAME,
            INFO_BUFF_VAR_NEXT_ENTRY,
            INFO_BUFF_VAR_SIZE,
            INFO_MSG_VAR_CONTENT,
            INFO_MSG_VAR_INFO_REF,
            INFO_MSG_VAR_LOCAL_REF,
            INFO_MSG_VAR_MSG_ID,
        )

        # All should be non-None
        for const in [
            IMTS_VAR_NAME,
            IMTS_VAR_STATUS,
            INFO_BUFF_VAR_NAME,
            INFO_BUFF_VAR_SIZE,
            INFO_BUFF_VAR_NEXT_ENTRY,
            INFO_BUFF_VAR_ENTRIES,
            INFO_MSG_VAR_INFO_REF,
            INFO_MSG_VAR_LOCAL_REF,
            INFO_MSG_VAR_MSG_ID,
            INFO_MSG_VAR_CONTENT,
        ]:
            self.assertIsNotNone(const)

    def test_version_updated(self):
        """Test version was updated for Block 4."""
        from pyiec61850.tase2 import __version__

        self.assertEqual(__version__, "0.4.0")


class TestIMTransferSet(unittest.TestCase):
    """Test Block 4: IM Transfer Set client operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_enable_im_transfer_set(self):
        """Test enabling IM Transfer Set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        result = client.enable_im_transfer_set("VCC")
        self.assertTrue(result)
        self.assertTrue(client._im_transfer_set_enabled)

    def test_enable_im_transfer_set_searches_domains(self):
        """Test IM Transfer Set enable searches VCC then ICC."""
        from pyiec61850.tase2 import TASE2Client

        # First call fails, second succeeds
        call_count = [0]

        def mock_write(domain, var, value):
            call_count[0] += 1
            if domain == "VCC":
                raise Exception("Not found on VCC")
            return True

        self.mock_connection.write_variable.side_effect = mock_write
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        result = client.enable_im_transfer_set()
        self.assertTrue(result)

    def test_enable_im_transfer_set_failure(self):
        """Test IM Transfer Set enable failure raises error."""
        from pyiec61850.tase2 import IMTransferSetError, TASE2Client

        self.mock_connection.write_variable.side_effect = Exception("Write failed")
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        with self.assertRaises(IMTransferSetError):
            client.enable_im_transfer_set("VCC")

    def test_disable_im_transfer_set(self):
        """Test disabling IM Transfer Set."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        client._im_transfer_set_enabled = True
        result = client.disable_im_transfer_set("VCC")
        self.assertTrue(result)
        self.assertFalse(client._im_transfer_set_enabled)

    def test_disable_im_transfer_set_failure(self):
        """Test IM Transfer Set disable failure raises error."""
        from pyiec61850.tase2 import IMTransferSetError, TASE2Client

        self.mock_connection.write_variable.side_effect = Exception("Write failed")
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        with self.assertRaises(IMTransferSetError):
            client.disable_im_transfer_set("VCC")

    def test_get_im_transfer_set_status(self):
        """Test reading IM Transfer Set status."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = ["IM_Transfer_Set_Status"]
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        status = client.get_im_transfer_set_status("VCC")
        self.assertTrue(status.enabled)

    def test_get_im_transfer_set_status_default(self):
        """Test IM Transfer Set status returns default when not readable."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.side_effect = Exception("Not found")
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []

        client = TASE2Client()
        status = client.get_im_transfer_set_status("VCC")
        self.assertFalse(status.enabled)

    def test_not_connected_raises_error(self):
        """Test IM Transfer Set operations require connection."""
        from pyiec61850.tase2 import NotConnectedError, TASE2Client

        self.mock_connection.is_connected = False

        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.enable_im_transfer_set("VCC")

    def test_disconnect_clears_im_state(self):
        """Test disconnect clears IM Transfer Set state."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._im_transfer_set_enabled = True
        client.disconnect()
        self.assertFalse(client._im_transfer_set_enabled)


class TestInfoMessageOperations(unittest.TestCase):
    """Test Block 4: Information message send/receive operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_send_info_message_text(self):
        """Test sending a text information message."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_info_message(
            "ICC1", info_ref=1, local_ref=2, msg_id=100, content=b"System status: normal"
        )
        self.assertTrue(result)
        # Should have written reference fields + content
        self.assertGreaterEqual(self.mock_connection.write_variable.call_count, 1)

    def test_send_info_message_string_content(self):
        """Test sending string content (auto-encodes to bytes)."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.write_variable.return_value = True

        client = TASE2Client()
        result = client.send_info_message(
            "ICC1", info_ref=1, local_ref=1, msg_id=1, content="Text message"
        )
        self.assertTrue(result)

    def test_send_info_message_too_large(self):
        """Test sending oversized message raises error."""
        from pyiec61850.tase2 import InformationMessageError, TASE2Client

        client = TASE2Client()
        big_content = b"x" * 70000
        with self.assertRaises(InformationMessageError):
            client.send_info_message("ICC1", info_ref=1, local_ref=1, msg_id=1, content=big_content)

    def test_send_info_message_all_writes_fail(self):
        """Test send_info_message raises error when all writes fail."""
        from pyiec61850.tase2 import InformationMessageError, TASE2Client

        self.mock_connection.write_variable.side_effect = Exception("Write failed")

        client = TASE2Client()
        with self.assertRaises(InformationMessageError):
            client.send_info_message("ICC1", info_ref=1, local_ref=1, msg_id=1, content=b"test")

    def test_get_info_messages_empty(self):
        """Test get_info_messages returns empty list when no messages."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        messages = client.get_info_messages("ICC1")
        self.assertEqual(len(messages), 0)

    def test_get_info_messages_from_queue(self):
        """Test get_info_messages returns queued messages."""
        from pyiec61850.tase2 import InformationMessage, TASE2Client

        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        # Pre-queue some messages
        client._im_message_queue.put(InformationMessage(info_ref=1, content=b"msg1"))
        client._im_message_queue.put(InformationMessage(info_ref=2, content=b"msg2"))

        messages = client.get_info_messages("ICC1")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].info_ref, 1)
        self.assertEqual(messages[1].info_ref, 2)

    def test_get_info_message_by_ref_found(self):
        """Test get_info_message_by_ref finds queued message."""
        from pyiec61850.tase2 import InformationMessage, TASE2Client

        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        client._im_message_queue.put(InformationMessage(info_ref=42, content=b"target message"))

        msg = client.get_info_message_by_ref("ICC1", info_ref=42)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.info_ref, 42)
        self.assertEqual(msg.text, "target message")

    def test_get_info_message_by_ref_not_found(self):
        """Test get_info_message_by_ref returns None when not found."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        msg = client.get_info_message_by_ref("ICC1", info_ref=999)
        self.assertIsNone(msg)

    def test_get_next_info_message_empty(self):
        """Test get_next_info_message returns None when queue empty."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        msg = client.get_next_info_message()
        self.assertIsNone(msg)

    def test_get_next_info_message_with_timeout(self):
        """Test get_next_info_message with timeout."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        msg = client.get_next_info_message(timeout=0.01)
        self.assertIsNone(msg)

    def test_get_next_info_message_queued(self):
        """Test get_next_info_message returns queued message."""
        from pyiec61850.tase2 import InformationMessage, TASE2Client

        client = TASE2Client()
        client._im_message_queue.put(InformationMessage(info_ref=5, content=b"queued msg"))

        msg = client.get_next_info_message(timeout=1.0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.info_ref, 5)

    def test_set_im_message_callback(self):
        """Test setting IM message callback."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()

        def callback(msg):
            return None

        client.set_im_message_callback(callback)
        self.assertEqual(client._im_message_callback, callback)

        client.set_im_message_callback(None)
        self.assertIsNone(client._im_message_callback)

    def test_not_connected_send(self):
        """Test send_info_message raises NotConnectedError."""
        from pyiec61850.tase2 import NotConnectedError, TASE2Client

        self.mock_connection.is_connected = False

        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.send_info_message("ICC1", info_ref=1, local_ref=1, msg_id=1, content=b"test")


class TestInfoBufferOperations(unittest.TestCase):
    """Test Block 4: Information buffer operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_info_buffers(self):
        """Test discovering information buffers."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_variables.return_value = [
            "Information_Buffer_1",
            "Information_Buffer_2",
            "Regular_Var",
        ]
        self.mock_connection.read_variable.side_effect = Exception("Not found")

        client = TASE2Client()
        buffers = client.get_info_buffers("ICC1")

        # Should find buffers matching information_buffer pattern
        self.assertGreaterEqual(len(buffers), 1)
        for buf in buffers:
            self.assertEqual(buf.domain, "ICC1")

    def test_get_info_buffers_empty(self):
        """Test get_info_buffers returns empty when no buffers found."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_domain_variables.return_value = ["Voltage", "Current", "Power"]

        client = TASE2Client()
        buffers = client.get_info_buffers("ICC1")
        self.assertEqual(len(buffers), 0)


class TestBlock4FileOperations(unittest.TestCase):
    """Test Block 4: File service operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_file_directory(self):
        """Test get_file_directory delegates to connection."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_file_directory.return_value = [
            {"name": "report.txt", "size": 1024, "last_modified": 0},
        ]

        client = TASE2Client()
        files = client.get_file_directory()

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "report.txt")
        self.mock_connection.get_file_directory.assert_called_once_with("")

    def test_get_file_directory_with_path(self):
        """Test get_file_directory with subdirectory."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.get_file_directory.return_value = []

        client = TASE2Client()
        client.get_file_directory("/logs")

        self.mock_connection.get_file_directory.assert_called_once_with("/logs")

    def test_delete_file(self):
        """Test delete_file delegates to connection."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.delete_file.return_value = True

        client = TASE2Client()
        result = client.delete_file("old_report.txt")

        self.assertTrue(result)
        self.mock_connection.delete_file.assert_called_once_with("old_report.txt")


class TestBlock4SupportedFeatures(unittest.TestCase):
    """Test Block 4 integration with Supported_Features parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_parse_supported_features_with_block4(self):
        """Test Supported_Features parsing includes Block 4."""
        from pyiec61850.tase2 import BLOCK_1, BLOCK_4, TASE2Client

        client = TASE2Client()
        # Per ASN.1 BITSTRING: Block 1=0x80, Block 4=0x10
        # Block 1 + Block 4 = 0x80 | 0x10 = 0x90
        client._parse_supported_features(0x90)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertIn(BLOCK_1, blocks)
        self.assertIn(BLOCK_4, blocks)

    def test_parse_all_blocks(self):
        """Test Supported_Features parsing with all first-octet blocks."""
        from pyiec61850.tase2 import BLOCK_1, BLOCK_2, BLOCK_4, BLOCK_5, TASE2Client

        client = TASE2Client()
        # Per ASN.1 BITSTRING: Block 1=0x80, Block 2=0x40, Block 4=0x10, Block 5=0x08
        # Blocks 1+2+4+5: 0x80 | 0x40 | 0x10 | 0x08 = 0xD8
        client._parse_supported_features(0xD8)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertIn(BLOCK_1, blocks)
        self.assertIn(BLOCK_2, blocks)
        self.assertIn(BLOCK_4, blocks)
        self.assertIn(BLOCK_5, blocks)


class TestBlock4FullLifecycle(unittest.TestCase):
    """Test Block 4: Full information message lifecycle (mocked)."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.write_variable.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_full_lifecycle(self):
        """Test enable -> receive -> query -> disable lifecycle."""
        from pyiec61850.tase2 import InformationMessage, TASE2Client

        client = TASE2Client()

        # 1. Enable IM Transfer Set
        result = client.enable_im_transfer_set("ICC1")
        self.assertTrue(result)
        self.assertTrue(client._im_transfer_set_enabled)

        # 2. Set callback
        received = []
        client.set_im_message_callback(lambda msg: received.append(msg))
        self.assertIsNotNone(client._im_message_callback)

        # 3. Simulate receiving messages (put in queue)
        client._im_message_queue.put(
            InformationMessage(
                info_ref=1, local_ref=1, msg_id=1, content=b"Alarm: Voltage out of range"
            )
        )
        client._im_message_queue.put(
            InformationMessage(info_ref=2, local_ref=1, msg_id=2, content=b"Status: System normal")
        )

        # 4. Get messages from queue
        msg1 = client.get_next_info_message(timeout=1.0)
        self.assertIsNotNone(msg1)
        self.assertEqual(msg1.info_ref, 1)
        self.assertIn("Voltage", msg1.text)

        msg2 = client.get_next_info_message(timeout=1.0)
        self.assertIsNotNone(msg2)
        self.assertEqual(msg2.info_ref, 2)

        # 5. No more messages
        msg3 = client.get_next_info_message()
        self.assertIsNone(msg3)

        # 6. Send a message
        self.mock_connection.read_variable.side_effect = Exception("Not found")
        result = client.send_info_message(
            "ICC1", info_ref=10, local_ref=1, msg_id=50, content=b"Operator note: check breaker"
        )
        self.assertTrue(result)

        # 7. Disable IM Transfer Set
        result = client.disable_im_transfer_set("ICC1")
        self.assertTrue(result)
        self.assertFalse(client._im_transfer_set_enabled)


# =========================================================================
# Tests for v0.4.0 Feature Gaps
# =========================================================================


class TestTagStateDataclass(unittest.TestCase):
    """Test TagState data class."""

    def test_tag_state_defaults(self):
        """Test TagState default values."""
        from pyiec61850.tase2 import TagState

        ts = TagState()
        self.assertEqual(ts.tag_value, 0)
        self.assertEqual(ts.reason, "")
        self.assertEqual(ts.device, "")
        self.assertEqual(ts.domain, "")

    def test_tag_state_is_tagged_false(self):
        """Test is_tagged returns False when no tag."""
        from pyiec61850.tase2 import TagState

        ts = TagState(tag_value=0)
        self.assertFalse(ts.is_tagged)

    def test_tag_state_is_tagged_true(self):
        """Test is_tagged returns True with tag."""
        from pyiec61850.tase2 import TagState

        ts = TagState(tag_value=1)
        self.assertTrue(ts.is_tagged)
        ts2 = TagState(tag_value=2)
        self.assertTrue(ts2.is_tagged)

    def test_tag_state_tag_name(self):
        """Test tag_name returns correct names per libtase2 Tase2_TagValue."""
        from pyiec61850.tase2 import TagState

        self.assertEqual(TagState(tag_value=0).tag_name, "NO_TAG")
        self.assertEqual(TagState(tag_value=1).tag_name, "OPEN_AND_CLOSE_INHIBIT")
        self.assertEqual(TagState(tag_value=2).tag_name, "CLOSE_ONLY_INHIBIT")
        self.assertEqual(TagState(tag_value=3).tag_name, "INVALID")
        self.assertEqual(TagState(tag_value=99).tag_name, "UNKNOWN(99)")

    def test_tag_state_to_dict(self):
        """Test TagState to_dict serialization."""
        from pyiec61850.tase2 import TagState

        ts = TagState(tag_value=2, reason="Maintenance", device="BRK1", domain="ICC1")
        d = ts.to_dict()
        self.assertEqual(d["tag_value"], 2)
        self.assertEqual(d["tag_name"], "CLOSE_ONLY_INHIBIT")
        self.assertTrue(d["is_tagged"])
        self.assertEqual(d["reason"], "Maintenance")
        self.assertEqual(d["device"], "BRK1")
        self.assertEqual(d["domain"], "ICC1")

    def test_tag_state_to_dict_minimal(self):
        """Test TagState to_dict with no optional fields."""
        from pyiec61850.tase2 import TagState

        ts = TagState(tag_value=0)
        d = ts.to_dict()
        self.assertEqual(d["tag_value"], 0)
        self.assertNotIn("reason", d)
        self.assertNotIn("device", d)
        self.assertNotIn("domain", d)


class TestClientStatisticsDataclass(unittest.TestCase):
    """Test ClientStatistics data class."""

    def test_defaults(self):
        """Test ClientStatistics default values."""
        from pyiec61850.tase2 import ClientStatistics

        cs = ClientStatistics()
        self.assertEqual(cs.total_reads, 0)
        self.assertEqual(cs.total_writes, 0)
        self.assertEqual(cs.total_errors, 0)
        self.assertEqual(cs.reports_received, 0)
        self.assertEqual(cs.control_operations, 0)
        self.assertIsNone(cs.connect_time)
        self.assertIsNone(cs.disconnect_time)

    def test_uptime_seconds_no_connect(self):
        """Test uptime_seconds returns 0 when not connected."""
        from pyiec61850.tase2 import ClientStatistics

        cs = ClientStatistics()
        self.assertEqual(cs.uptime_seconds, 0.0)

    def test_uptime_seconds_with_connect(self):
        """Test uptime_seconds calculates duration."""
        from pyiec61850.tase2 import ClientStatistics

        now = datetime.now()
        cs = ClientStatistics(connect_time=now)
        # Should be a small positive number (just connected)
        self.assertGreaterEqual(cs.uptime_seconds, 0.0)

    def test_uptime_seconds_with_disconnect(self):
        """Test uptime_seconds uses disconnect_time if available."""

        from pyiec61850.tase2 import ClientStatistics

        start = datetime(2025, 1, 1, 12, 0, 0)
        end = datetime(2025, 1, 1, 12, 5, 0)
        cs = ClientStatistics(connect_time=start, disconnect_time=end)
        self.assertAlmostEqual(cs.uptime_seconds, 300.0, places=1)

    def test_to_dict(self):
        """Test ClientStatistics to_dict serialization."""
        from pyiec61850.tase2 import ClientStatistics

        cs = ClientStatistics(
            total_reads=100,
            total_writes=50,
            total_errors=2,
            reports_received=75,
            control_operations=10,
        )
        d = cs.to_dict()
        self.assertEqual(d["total_reads"], 100)
        self.assertEqual(d["total_writes"], 50)
        self.assertEqual(d["total_errors"], 2)
        self.assertEqual(d["reports_received"], 75)
        self.assertEqual(d["control_operations"], 10)
        self.assertIn("uptime_seconds", d)

    def test_to_dict_with_connect_time(self):
        """Test to_dict includes connect_time when set."""
        from pyiec61850.tase2 import ClientStatistics

        cs = ClientStatistics(connect_time=datetime(2025, 1, 1, 12, 0, 0))
        d = cs.to_dict()
        self.assertIn("connect_time", d)


class TestNewConstantsImport(unittest.TestCase):
    """Test new constants added in v0.4.0 can be imported."""

    def test_edition_constants(self):
        """Test TASE.2 edition constants."""
        from pyiec61850.tase2 import (
            TASE2_EDITION_1996,
            TASE2_EDITION_2000,
            TASE2_EDITION_AUTO,
        )

        self.assertEqual(TASE2_EDITION_1996, "1996.08")
        self.assertEqual(TASE2_EDITION_2000, "2000.08")
        self.assertEqual(TASE2_EDITION_AUTO, "auto")

    def test_tag_constants(self):
        """Test tag variable name suffixes."""
        from pyiec61850.tase2 import TAG_REASON_VAR_SUFFIX, TAG_VAR_SUFFIX

        self.assertEqual(TAG_VAR_SUFFIX, "_TAG")
        self.assertEqual(TAG_REASON_VAR_SUFFIX, "_TagReason")

    def test_file_download_limit(self):
        """Test file download size limit."""
        from pyiec61850.tase2 import MAX_FILE_DOWNLOAD_SIZE

        self.assertEqual(MAX_FILE_DOWNLOAD_SIZE, 10 * 1024 * 1024)

    def test_transfer_set_chain_limit(self):
        """Test transfer set chain iteration limit."""
        from pyiec61850.tase2 import MAX_TRANSFER_SET_CHAIN

        self.assertEqual(MAX_TRANSFER_SET_CHAIN, 100)

    def test_new_types_import(self):
        """Test new data types can be imported."""
        from pyiec61850.tase2 import ClientStatistics, TagState

        self.assertIsNotNone(TagState)
        self.assertIsNotNone(ClientStatistics)


class TestGetTag(unittest.TestCase):
    """Test get_tag() method (Block 5 tag reading)."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_tag_success(self):
        """Test successful tag read."""
        from pyiec61850.tase2 import PointValue, TagState, TASE2Client

        client = TASE2Client()

        # Mock read_point to return tag value and reason
        def mock_read_point(domain, name):
            if name == "BRK1_TAG":
                return PointValue(value=2, quality="GOOD", name=name, domain=domain)
            elif name == "BRK1_TagReason":
                return PointValue(
                    value="Under maintenance", quality="GOOD", name=name, domain=domain
                )
            raise Exception("Not found")

        client.read_point = MagicMock(side_effect=mock_read_point)

        tag = client.get_tag("ICC1", "BRK1")
        self.assertIsInstance(tag, TagState)
        self.assertEqual(tag.tag_value, 2)
        self.assertEqual(tag.reason, "Under maintenance")
        self.assertEqual(tag.device, "BRK1")
        self.assertEqual(tag.domain, "ICC1")
        self.assertTrue(tag.is_tagged)

    def test_get_tag_no_reason(self):
        """Test tag read without reason string."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()

        def mock_read_point(domain, name):
            if name == "BRK1_TAG":
                return PointValue(value=1, quality="GOOD", name=name, domain=domain)
            raise Exception("Not found")

        client.read_point = MagicMock(side_effect=mock_read_point)

        tag = client.get_tag("ICC1", "BRK1")
        self.assertEqual(tag.tag_value, 1)
        self.assertEqual(tag.reason, "")
        self.assertEqual(tag.tag_name, "OPEN_AND_CLOSE_INHIBIT")

    def test_get_tag_not_connected(self):
        """Test get_tag raises when not connected."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import NotConnectedError

        self.mock_connection.is_connected = False
        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.get_tag("ICC1", "BRK1")

    def test_get_tag_read_fails(self):
        """Test get_tag raises ReadError when tag variable cannot be read."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import ReadError

        client = TASE2Client()
        # All read attempts fail
        client.read_point = MagicMock(side_effect=Exception("Not found"))

        with self.assertRaises(ReadError):
            client.get_tag("ICC1", "BRK1")


class TestReadPointsBatch(unittest.TestCase):
    """Test read_points_batch() method (batch reads via temp data set)."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_batch_empty_list(self):
        """Test batch read with empty list returns empty."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        result = client.read_points_batch("ICC1", [])
        self.assertEqual(result, [])

    def test_batch_single_point(self):
        """Test batch read with single point delegates to read_point."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()
        pv = PointValue(value=42.0, quality="GOOD", name="Voltage", domain="ICC1")
        client.read_point = MagicMock(return_value=pv)

        result = client.read_points_batch("ICC1", ["Voltage"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, 42.0)
        client.read_point.assert_called_once_with("ICC1", "Voltage")

    def test_batch_exceeds_limit(self):
        """Test batch read raises when exceeding MAX_DATA_SET_SIZE."""
        from pyiec61850.tase2 import MAX_DATA_SET_SIZE, TASE2Client
        from pyiec61850.tase2.exceptions import TASE2Error

        client = TASE2Client()
        names = [f"Point_{i}" for i in range(MAX_DATA_SET_SIZE + 1)]
        with self.assertRaises(TASE2Error):
            client.read_points_batch("ICC1", names)

    def test_batch_creates_and_deletes_temp_dataset(self):
        """Test batch read creates and cleans up temp data set."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # Mock read_data_set_values to return raw values
        self.mock_connection.read_data_set_values.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        # Mock _parse_point_value
        from pyiec61850.tase2 import PointValue

        client._parse_point_value = MagicMock(
            return_value=PointValue(value=1.0, quality="GOOD", name="P", domain="D")
        )

        result = client.read_points_batch("ICC1", ["V1", "V2", "V3"])
        self.assertEqual(len(result), 3)

        # Verify create_data_set was called
        self.mock_connection.create_data_set.assert_called_once()
        call_args = self.mock_connection.create_data_set.call_args
        self.assertEqual(call_args[0][0], "ICC1")  # domain
        # Verify temp name starts with _pyiec_batch_
        self.assertTrue(call_args[0][1].startswith("_pyiec_batch_"))
        # Verify member refs
        self.assertEqual(call_args[0][2], ["ICC1/V1", "ICC1/V2", "ICC1/V3"])

        # Verify delete_data_set was called (cleanup)
        self.mock_connection.delete_data_set.assert_called_once()

    def test_batch_fallback_on_failure(self):
        """Test batch read falls back to sequential on data set failure."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()
        # Make create_data_set fail
        self.mock_connection.create_data_set.side_effect = Exception("Not supported")

        # Mock read_points (fallback method)
        pv = PointValue(value=1.0, quality="GOOD", name="V", domain="ICC1")
        client.read_points = MagicMock(return_value=[pv, pv])

        result = client.read_points_batch("ICC1", ["V1", "V2"])
        self.assertEqual(len(result), 2)
        client.read_points.assert_called_once()

    def test_batch_not_connected(self):
        """Test batch read raises when not connected."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import NotConnectedError

        self.mock_connection.is_connected = False
        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.read_points_batch("ICC1", ["V1", "V2"])


class TestGetTransferSetsNative(unittest.TestCase):
    """Test get_transfer_sets_native() Next_DSTransfer_Set chain iteration."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_native_discovery_chain(self):
        """Test following Next_DSTransfer_Set chain."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()

        call_count = [0]

        def mock_read_point(domain, name):
            call_count[0] += 1
            if name == "Next_DSTransfer_Set":
                return PointValue(value="TS1", quality="GOOD", name=name, domain=domain)
            elif name == "TS1_Next_DSTransfer_Set":
                return PointValue(value="TS2", quality="GOOD", name=name, domain=domain)
            elif name == "TS2_Next_DSTransfer_Set":
                return PointValue(value="", quality="GOOD", name=name, domain=domain)
            elif name.endswith("_Status"):
                return PointValue(value=1, quality="GOOD", name=name, domain=domain)
            raise Exception("Not found")

        client.read_point = MagicMock(side_effect=mock_read_point)

        result = client.get_transfer_sets_native("ICC1")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "TS1")
        self.assertEqual(result[1].name, "TS2")
        self.assertEqual(result[0].domain, "ICC1")

    def test_native_discovery_fallback(self):
        """Test fallback to pattern matching when Next_DSTransfer_Set missing."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # All reads fail -> no Next_DSTransfer_Set
        client.read_point = MagicMock(side_effect=Exception("Not found"))
        client.get_transfer_sets = MagicMock(return_value=[])

        result = client.get_transfer_sets_native("ICC1")
        self.assertEqual(result, [])
        client.get_transfer_sets.assert_called_once_with("ICC1")

    def test_native_discovery_circular_detection(self):
        """Test circular reference detection in chain."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()

        def mock_read_point(domain, name):
            if name == "Next_DSTransfer_Set":
                return PointValue(value="TS1", quality="GOOD", name=name, domain=domain)
            elif name == "TS1_Next_DSTransfer_Set":
                # Circular: points back to TS1
                return PointValue(value="TS1", quality="GOOD", name=name, domain=domain)
            elif name.endswith("_Status"):
                return PointValue(value=0, quality="GOOD", name=name, domain=domain)
            raise Exception("Not found")

        client.read_point = MagicMock(side_effect=mock_read_point)

        result = client.get_transfer_sets_native("ICC1")
        # Should find TS1 once but not loop
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "TS1")

    def test_native_discovery_not_connected(self):
        """Test raises when not connected."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import NotConnectedError

        self.mock_connection.is_connected = False
        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.get_transfer_sets_native("ICC1")


class TestDownloadFile(unittest.TestCase):
    """Test download_file() method (MMS file services)."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_download_file_success(self):
        """Test successful file download."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        test_data = b"file content here"
        self.mock_connection.download_file.return_value = test_data

        result = client.download_file("config.txt")
        self.assertEqual(result, test_data)
        self.mock_connection.download_file.assert_called_once()

    def test_download_file_with_local_path(self):
        """Test file download saves to local path."""
        import os
        import tempfile

        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        test_data = b"saved file content"
        self.mock_connection.download_file.return_value = test_data

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            result = client.download_file("config.txt", local_path=temp_path)
            self.assertEqual(result, test_data)
            with open(temp_path, "rb") as f:
                self.assertEqual(f.read(), test_data)
        finally:
            os.unlink(temp_path)

    def test_download_file_not_connected(self):
        """Test download_file raises when not connected."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import NotConnectedError

        self.mock_connection.is_connected = False
        client = TASE2Client()
        with self.assertRaises(NotConnectedError):
            client.download_file("config.txt")

    def test_download_file_connection_error(self):
        """Test download_file wraps errors in TASE2Error."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import TASE2Error

        client = TASE2Client()
        self.mock_connection.download_file.side_effect = RuntimeError("IO error")

        with self.assertRaises(TASE2Error):
            client.download_file("bad_file.txt")


class TestClientStatistics(unittest.TestCase):
    """Test statistics/diagnostics tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_statistics_initial(self):
        """Test initial statistics are zero."""
        from pyiec61850.tase2 import ClientStatistics, TASE2Client

        client = TASE2Client()
        stats = client.get_statistics()
        self.assertIsInstance(stats, ClientStatistics)
        self.assertEqual(stats.total_reads, 0)
        self.assertEqual(stats.total_writes, 0)
        self.assertEqual(stats.total_errors, 0)
        self.assertEqual(stats.reports_received, 0)
        self.assertEqual(stats.control_operations, 0)

    def test_statistics_returns_copy(self):
        """Test get_statistics returns a copy, not the internal object."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        stats1 = client.get_statistics()
        stats1.total_reads = 999
        stats2 = client.get_statistics()
        # The modification to stats1 should not affect internal state
        self.assertEqual(stats2.total_reads, 0)

    def test_statistics_read_increments(self):
        """Test read operations increment statistics."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # Simulate a successful read by directly incrementing
        client._statistics.total_reads += 1
        client._statistics.total_reads += 1
        stats = client.get_statistics()
        self.assertEqual(stats.total_reads, 2)

    def test_statistics_connect_time(self):
        """Test connect sets connect_time in statistics."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.mock_connection.connect.return_value = True
        client.connect("192.168.1.1")
        stats = client.get_statistics()
        self.assertIsNotNone(stats.connect_time)

    def test_statistics_disconnect_time(self):
        """Test disconnect sets disconnect_time in statistics."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.disconnect()
        stats = client.get_statistics()
        self.assertIsNotNone(stats.disconnect_time)


class TestLocalIdentity(unittest.TestCase):
    """Test set_local_identity() and get_local_identity()."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_identity_not_set_initially(self):
        """Test local identity is None initially."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertIsNone(client.get_local_identity())

    def test_set_and_get_identity(self):
        """Test setting and getting local identity."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.set_local_identity("ACME Corp", "EMS-2000", "3.1.0")
        identity = client.get_local_identity()
        self.assertEqual(identity, ("ACME Corp", "EMS-2000", "3.1.0"))

    def test_identity_overwrite(self):
        """Test overwriting local identity."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.set_local_identity("Vendor1", "Model1", "1.0")
        client.set_local_identity("Vendor2", "Model2", "2.0")
        identity = client.get_local_identity()
        self.assertEqual(identity, ("Vendor2", "Model2", "2.0"))


class TestEditionAwareTimestamps(unittest.TestCase):
    """Test TASE.2 edition property and timestamp conversion."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_default_edition_is_auto(self):
        """Test default edition is 'auto'."""
        from pyiec61850.tase2 import TASE2_EDITION_AUTO, TASE2Client

        client = TASE2Client()
        self.assertEqual(client.tase2_edition, TASE2_EDITION_AUTO)

    def test_set_edition_1996(self):
        """Test setting edition to 1996."""
        from pyiec61850.tase2 import TASE2_EDITION_1996, TASE2Client

        client = TASE2Client()
        client.tase2_edition = TASE2_EDITION_1996
        self.assertEqual(client.tase2_edition, TASE2_EDITION_1996)

    def test_set_edition_2000(self):
        """Test setting edition to 2000."""
        from pyiec61850.tase2 import TASE2_EDITION_2000, TASE2Client

        client = TASE2Client()
        client.tase2_edition = TASE2_EDITION_2000
        self.assertEqual(client.tase2_edition, TASE2_EDITION_2000)

    def test_set_invalid_edition_raises(self):
        """Test setting invalid edition raises ValueError."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        with self.assertRaises(ValueError):
            client.tase2_edition = "invalid"

    def test_convert_timestamp_1996_seconds(self):
        """Test timestamp conversion with 1996 edition (seconds)."""
        from pyiec61850.tase2 import TASE2_EDITION_1996, TASE2Client

        client = TASE2Client()
        client.tase2_edition = TASE2_EDITION_1996
        # 2025-01-01 00:00:00 UTC = 1735689600 seconds
        result = client._convert_timestamp(1735689600)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_convert_timestamp_2000_milliseconds(self):
        """Test timestamp conversion with 2000 edition (milliseconds)."""
        from pyiec61850.tase2 import TASE2_EDITION_2000, TASE2Client

        client = TASE2Client()
        client.tase2_edition = TASE2_EDITION_2000
        # 2025-01-01 00:00:00 UTC = 1735689600000 milliseconds
        result = client._convert_timestamp(1735689600000)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_convert_timestamp_auto_large_value(self):
        """Test auto-detect with large value (milliseconds)."""
        from pyiec61850.tase2 import TASE2_EDITION_AUTO, TASE2Client

        client = TASE2Client()
        client.tase2_edition = TASE2_EDITION_AUTO
        # A value > 32503680000 should be treated as milliseconds
        ts_ms = 1735689600000  # 2025-01-01 in ms
        result = client._convert_timestamp(ts_ms)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)

    def test_convert_timestamp_overflow(self):
        """Test timestamp conversion with overflow value returns None."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # Extremely large value that would overflow datetime
        result = client._convert_timestamp(99999999999999999999)
        self.assertIsNone(result)


class TestMaxOutstandingCalls(unittest.TestCase):
    """Test max_outstanding_calls configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.connect.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_default_none(self):
        """Test max_outstanding_calls defaults to None."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertIsNone(client.max_outstanding_calls)

    def test_constructor_param(self):
        """Test max_outstanding_calls set via constructor."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(max_outstanding_calls=5)
        self.assertEqual(client.max_outstanding_calls, 5)

    def test_applied_at_connect(self):
        """Test max_outstanding_calls applied after connect."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(max_outstanding_calls=10)
        client.connect("192.168.1.1")
        self.mock_connection.set_max_outstanding_calls.assert_called_with(10, 10)

    def test_property_setter_when_connected(self):
        """Test setting max_outstanding_calls while connected applies immediately."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.max_outstanding_calls = 8
        self.assertEqual(client.max_outstanding_calls, 8)
        self.mock_connection.set_max_outstanding_calls.assert_called_with(8, 8)

    def test_property_setter_when_not_connected(self):
        """Test setting max_outstanding_calls while disconnected stores for later."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.is_connected = False
        client = TASE2Client()
        client.max_outstanding_calls = 5
        self.assertEqual(client.max_outstanding_calls, 5)
        # Should NOT call set_max_outstanding_calls since not connected
        self.mock_connection.set_max_outstanding_calls.assert_not_called()


class TestRequestTimeout(unittest.TestCase):
    """Test set_request_timeout() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_set_timeout_when_connected(self):
        """Test setting request timeout when connected."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.set_request_timeout(5000)
        self.mock_connection.set_request_timeout.assert_called_once_with(5000)

    def test_set_timeout_when_not_connected(self):
        """Test setting request timeout when not connected logs warning."""
        from pyiec61850.tase2 import TASE2Client

        self.mock_connection.is_connected = False
        client = TASE2Client()
        # Should not raise, just warn
        client.set_request_timeout(5000)
        self.mock_connection.set_request_timeout.assert_not_called()


class TestV040VersionUpdated(unittest.TestCase):
    """Test version was bumped to 0.4.0."""

    def test_version_is_040(self):
        """Test module version is 0.4.0."""
        from pyiec61850.tase2 import __version__

        self.assertEqual(__version__, "0.4.0")

    def test_new_exports_in_all(self):
        """Test new types are in __all__."""
        from pyiec61850.tase2 import __all__

        for name in [
            "TagState",
            "ClientStatistics",
            "TASE2_EDITION_1996",
            "TASE2_EDITION_2000",
            "TASE2_EDITION_AUTO",
            "TAG_VAR_SUFFIX",
            "TAG_REASON_VAR_SUFFIX",
            "MAX_FILE_DOWNLOAD_SIZE",
            "MAX_TRANSFER_SET_CHAIN",
        ]:
            self.assertIn(name, __all__, f"{name} missing from __all__")


class TestServerAddress(unittest.TestCase):
    """Test ServerAddress dataclass."""

    def test_creation_defaults(self):
        """Test ServerAddress with default values."""
        from pyiec61850.tase2 import ServerAddress

        addr = ServerAddress("192.168.1.100")
        self.assertEqual(addr.host, "192.168.1.100")
        self.assertEqual(addr.port, 102)
        self.assertEqual(addr.priority, "primary")

    def test_creation_full(self):
        """Test ServerAddress with all values specified."""
        from pyiec61850.tase2 import ServerAddress

        addr = ServerAddress("10.0.0.1", 5000, priority="backup")
        self.assertEqual(addr.host, "10.0.0.1")
        self.assertEqual(addr.port, 5000)
        self.assertEqual(addr.priority, "backup")

    def test_is_primary(self):
        """Test is_primary property."""
        from pyiec61850.tase2 import ServerAddress

        primary = ServerAddress("host1", priority="primary")
        backup = ServerAddress("host2", priority="backup")
        self.assertTrue(primary.is_primary)
        self.assertFalse(primary.is_backup)
        self.assertFalse(backup.is_primary)
        self.assertTrue(backup.is_backup)

    def test_str_representation(self):
        """Test string representation of ServerAddress."""
        from pyiec61850.tase2 import ServerAddress

        addr = ServerAddress("192.168.1.100", 102, priority="primary")
        s = str(addr)
        self.assertIn("192.168.1.100", s)
        self.assertIn("102", s)
        self.assertIn("primary", s)


class TestMultiServerFailover(unittest.TestCase):
    """Test multi-server failover (connect with server list)."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.connect.return_value = True
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_connect_single_host(self):
        """Test connect with a single host string works as before."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        result = client.connect("192.168.1.100", port=102)
        self.assertTrue(result)
        self.mock_connection.connect.assert_called_once_with("192.168.1.100", 102, 10000)

    def test_connect_with_server_list(self):
        """Test connect with list of (host, port) tuples."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        servers = [
            ("192.168.1.100", 102),
            ("192.168.1.101", 102),
        ]
        result = client.connect(servers, failover=True)
        self.assertTrue(result)
        # Should have connected to first server
        self.mock_connection.connect.assert_called_once_with("192.168.1.100", 102, 10000)

    def test_connect_server_list_failover_to_second(self):
        """Test failover connects to second server when first fails."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import ConnectionFailedError

        # First call fails, second succeeds
        self.mock_connection.connect.side_effect = [
            ConnectionFailedError("host1", 102, "refused"),
            True,
        ]

        client = TASE2Client()
        servers = [
            ("192.168.1.100", 102),
            ("192.168.1.101", 102),
        ]
        result = client.connect(servers, failover=True, retry_count=0)
        self.assertTrue(result)
        self.assertEqual(self.mock_connection.connect.call_count, 2)

    def test_connect_server_list_all_fail(self):
        """Test raises when all servers in list fail."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import ConnectionFailedError

        self.mock_connection.connect.side_effect = ConnectionFailedError("host", 102, "refused")

        client = TASE2Client()
        servers = [
            ("192.168.1.100", 102),
            ("192.168.1.101", 102),
        ]
        with self.assertRaises(ConnectionFailedError):
            client.connect(servers, failover=True, retry_count=0)

    def test_add_server(self):
        """Test add_server builds server list."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.add_server("192.168.1.100", 102, priority="primary")
        client.add_server("10.0.0.100", 102, priority="backup")
        client.add_server("192.168.1.101", 102, priority="primary")

        sl = client.server_list
        self.assertEqual(len(sl), 3)
        # Primaries should be first
        self.assertTrue(sl[0].is_primary)
        self.assertTrue(sl[1].is_primary)
        self.assertTrue(sl[2].is_backup)

    def test_add_server_and_connect_with_failover(self):
        """Test add_server followed by connect with failover=True."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.add_server("192.168.1.100", 102, priority="primary")
        client.add_server("192.168.1.101", 102, priority="primary")

        result = client.connect("192.168.1.100", failover=True)
        self.assertTrue(result)

    def test_server_list_property_returns_copy(self):
        """Test server_list returns a copy."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.add_server("192.168.1.100")
        sl = client.server_list
        sl.clear()
        # Internal list should be unchanged
        self.assertEqual(len(client.server_list), 1)

    def test_failover_on_connection_lost(self):
        """Test connection loss triggers failover to next server."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        servers = [
            ("192.168.1.100", 102),
            ("192.168.1.101", 102),
        ]
        client.connect(servers, failover=True)

        # Reset mock to track failover connection
        self.mock_connection.connect.reset_mock()
        self.mock_connection.connect.return_value = True

        # Simulate connection loss
        client._handle_connection_lost()

        # Should have tried to reconnect (failover attempt)
        self.assertTrue(self.mock_wrapper_class.call_count >= 2)

    def test_failover_disabled_calls_callback(self):
        """Test connection loss without failover calls callback."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        callback = MagicMock()
        client.on_connection_lost = callback

        # Not failover enabled, should call callback
        client._handle_connection_lost()
        callback.assert_called_once()


class TestConsecutiveErrorCounting(unittest.TestCase):
    """Test consecutive error counting and threshold detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_default_max_consecutive_errors(self):
        """Test default max_consecutive_errors is 10."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertEqual(client.max_consecutive_errors, 10)

    def test_custom_max_consecutive_errors(self):
        """Test custom max_consecutive_errors via constructor."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(max_consecutive_errors=5)
        self.assertEqual(client.max_consecutive_errors, 5)

    def test_initial_consecutive_errors_zero(self):
        """Test initial consecutive error count is zero."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.assertEqual(client.consecutive_errors, 0)

    def test_record_success_resets_count(self):
        """Test _record_success resets consecutive error count."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._consecutive_errors = 5
        client._record_success()
        self.assertEqual(client.consecutive_errors, 0)

    def test_record_error_increments_count(self):
        """Test _record_error increments consecutive error count."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._record_error()
        self.assertEqual(client.consecutive_errors, 1)
        client._record_error()
        self.assertEqual(client.consecutive_errors, 2)

    def test_record_error_increments_total_errors(self):
        """Test _record_error increments total errors in statistics."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._record_error()
        client._record_error()
        stats = client.get_statistics()
        self.assertEqual(stats.total_errors, 2)

    def test_threshold_triggers_connection_lost(self):
        """Test reaching threshold triggers _handle_connection_lost."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(max_consecutive_errors=3)
        callback = MagicMock()
        client.on_connection_lost = callback

        # Record errors up to threshold
        client._record_error()
        client._record_error()
        callback.assert_not_called()  # Not yet at threshold

        client._record_error()  # Reaches threshold (3)
        callback.assert_called_once()

    def test_success_between_errors_resets_count(self):
        """Test success between errors resets the counter."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client(max_consecutive_errors=3)
        callback = MagicMock()
        client.on_connection_lost = callback

        client._record_error()
        client._record_error()
        client._record_success()  # Resets
        client._record_error()
        client._record_error()
        # Should NOT have triggered - only 2 consecutive after reset
        callback.assert_not_called()

    def test_read_point_records_success(self):
        """Test successful read_point calls _record_success."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        self.mock_connection.read_variable.return_value = 42.0
        self.mock_connection.get_variable_type.return_value = 6  # FLOAT

        client._consecutive_errors = 3
        client.read_point("ICC1", "Voltage")
        self.assertEqual(client.consecutive_errors, 0)

    def test_read_point_records_error(self):
        """Test failed read_point calls _record_error."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import ReadError

        client = TASE2Client()
        self.mock_connection.read_variable.side_effect = Exception("read fail")

        with self.assertRaises(ReadError):
            client.read_point("ICC1", "Voltage")
        self.assertEqual(client.consecutive_errors, 1)


class TestDataSetTransferMetadata(unittest.TestCase):
    """Test create_data_set with include_transfer_metadata."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.create_data_set.return_value = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_create_data_set_no_metadata(self):
        """Test create_data_set without transfer metadata."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        members = ["Voltage", "Current"]
        client.create_data_set("ICC1", "DS1", members)

        self.mock_connection.create_data_set.assert_called_once_with(
            "ICC1", "DS1", ["Voltage", "Current"]
        )

    def test_create_data_set_with_metadata(self):
        """Test create_data_set with include_transfer_metadata=True."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        members = ["Voltage", "Current"]
        client.create_data_set("ICC1", "DS1", members, include_transfer_metadata=True)

        call_args = self.mock_connection.create_data_set.call_args
        created_members = call_args[0][2]

        # First 3 should be transfer metadata
        self.assertEqual(created_members[0], "Transfer_Set_Name")
        self.assertEqual(created_members[1], "Transfer_Set_Time_Stamp")
        self.assertEqual(created_members[2], "DSConditions_Detected")
        # Then the user-provided members
        self.assertEqual(created_members[3], "Voltage")
        self.assertEqual(created_members[4], "Current")
        self.assertEqual(len(created_members), 5)

    def test_create_data_set_metadata_preserves_originals(self):
        """Test include_transfer_metadata does not modify input list."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        members = ["Voltage", "Current"]
        original_len = len(members)
        client.create_data_set("ICC1", "DS1", members, include_transfer_metadata=True)

        # Original list should be unchanged
        self.assertEqual(len(members), original_len)
        self.assertEqual(members, ["Voltage", "Current"])


class TestEnableTransferSetInitialRead(unittest.TestCase):
    """Test enable_transfer_set with initial_read parameter."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.write_variable.return_value = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_enable_without_initial_read(self):
        """Test enable_transfer_set returns bool without initial_read."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        result = client.enable_transfer_set("ICC1", "TS1")
        self.assertTrue(result)
        self.assertIsInstance(result, bool)

    def test_enable_with_initial_read(self):
        """Test enable_transfer_set returns tuple with initial_read=True."""
        from pyiec61850.tase2 import PointValue, TASE2Client

        client = TASE2Client()
        mock_values = [
            PointValue(value=42.0, quality="GOOD", name="Voltage", domain="ICC1"),
            PointValue(value=10.5, quality="GOOD", name="Current", domain="ICC1"),
        ]
        client.get_data_set_values = MagicMock(return_value=mock_values)

        result = client.enable_transfer_set("ICC1", "TS1", initial_read=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0])
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(result[1][0].value, 42.0)

    def test_enable_initial_read_uses_data_set_name(self):
        """Test initial_read uses data_set_name when provided."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.get_data_set_values = MagicMock(return_value=[])

        client.enable_transfer_set("ICC1", "TS1", initial_read=True, data_set_name="MyDS")
        client.get_data_set_values.assert_called_once_with("ICC1", "MyDS")

    def test_enable_initial_read_uses_ts_name_as_default_ds(self):
        """Test initial_read uses transfer set name as default ds name."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.get_data_set_values = MagicMock(return_value=[])

        client.enable_transfer_set("ICC1", "TS1", initial_read=True)
        client.get_data_set_values.assert_called_once_with("ICC1", "TS1")

    def test_enable_initial_read_failure_returns_empty(self):
        """Test initial_read failure returns empty list, not error."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client.get_data_set_values = MagicMock(side_effect=Exception("read failed"))

        result = client.enable_transfer_set("ICC1", "TS1", initial_read=True)
        self.assertIsInstance(result, tuple)
        self.assertTrue(result[0])
        self.assertEqual(result[1], [])


class TestReportAckViaInformationReport(unittest.TestCase):
    """Test send_transfer_report_ack with InformationReport fallback."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_connection.get_domain_names.return_value = ["VCC", "ICC1"]
        self.mock_connection.get_domain_variables.return_value = []
        self.mock_connection.get_data_set_names.return_value = []
        self.mock_connection.write_variable.return_value = True
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_ack_without_transfer_set_name(self):
        """Test ACK without transfer_set_name uses write-variable fallback."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        result = client.send_transfer_report_ack("ICC1")
        self.assertTrue(result)
        self.mock_connection.write_variable.assert_called_once()

    def test_ack_with_transfer_set_name_fallback(self):
        """Test ACK with transfer_set_name falls back to write when no SWIG method."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # sendUnconfirmedPDU is not available in the SWIG bindings
        result = client.send_transfer_report_ack("ICC1", transfer_set_name="TS1")
        self.assertTrue(result)
        # Should have fallen through to write-variable
        self.mock_connection.write_variable.assert_called_once()

    def test_ack_write_failure_raises(self):
        """Test ACK raises WriteError when write fails."""
        from pyiec61850.tase2 import TASE2Client
        from pyiec61850.tase2.exceptions import WriteError

        client = TASE2Client()
        self.mock_connection.write_variable.side_effect = RuntimeError("fail")

        with self.assertRaises(WriteError):
            client.send_transfer_report_ack("ICC1")


class TestNewConstantsExported(unittest.TestCase):
    """Test that new constants are importable from pyiec61850.tase2."""

    def test_failover_constants(self):
        """Test failover-related constants are importable."""
        from pyiec61850.tase2 import (
            DEFAULT_FAILOVER_DELAY,
            DEFAULT_FAILOVER_RETRY_COUNT,
            SERVER_PRIORITY_BACKUP,
            SERVER_PRIORITY_PRIMARY,
        )

        self.assertEqual(DEFAULT_FAILOVER_RETRY_COUNT, 1)
        self.assertEqual(DEFAULT_FAILOVER_DELAY, 1.0)
        self.assertEqual(SERVER_PRIORITY_PRIMARY, "primary")
        self.assertEqual(SERVER_PRIORITY_BACKUP, "backup")

    def test_consecutive_error_constant(self):
        """Test consecutive error constant is importable."""
        from pyiec61850.tase2 import DEFAULT_MAX_CONSECUTIVE_ERRORS

        self.assertEqual(DEFAULT_MAX_CONSECUTIVE_ERRORS, 10)

    def test_transfer_set_metadata_constants(self):
        """Test transfer set metadata constants are importable."""
        from pyiec61850.tase2 import (
            TRANSFER_SET_METADATA_MEMBERS,
            TRANSFER_SET_METADATA_OFFSET,
        )

        self.assertEqual(len(TRANSFER_SET_METADATA_MEMBERS), 3)
        self.assertIn("Transfer_Set_Name", TRANSFER_SET_METADATA_MEMBERS)
        self.assertIn("Transfer_Set_Time_Stamp", TRANSFER_SET_METADATA_MEMBERS)
        self.assertIn("DSConditions_Detected", TRANSFER_SET_METADATA_MEMBERS)
        self.assertEqual(TRANSFER_SET_METADATA_OFFSET, 3)

    def test_server_address_in_all(self):
        """Test ServerAddress is in __all__."""
        from pyiec61850.tase2 import __all__

        self.assertIn("ServerAddress", __all__)

    def test_new_constants_in_all(self):
        """Test all new constants are in __all__."""
        from pyiec61850.tase2 import __all__

        for name in [
            "DEFAULT_FAILOVER_RETRY_COUNT",
            "DEFAULT_FAILOVER_DELAY",
            "SERVER_PRIORITY_PRIMARY",
            "SERVER_PRIORITY_BACKUP",
            "DEFAULT_MAX_CONSECUTIVE_ERRORS",
            "TRANSFER_SET_METADATA_MEMBERS",
            "TRANSFER_SET_METADATA_OFFSET",
        ]:
            self.assertIn(name, __all__, f"{name} missing from __all__")


class TestSupportedFeaturesAllBlocks(unittest.TestCase):
    """Test full 9-block Supported_Features parsing and get_server_blocks."""

    def setUp(self):
        self.patcher = patch("pyiec61850.tase2.client.MmsConnectionWrapper")
        self.mock_wrapper_class = self.patcher.start()
        self.mock_connection = MagicMock()
        self.mock_connection.is_connected = True
        self.mock_connection.register_state_callback = MagicMock()
        self.mock_wrapper_class.return_value = self.mock_connection

    def tearDown(self):
        self.patcher.stop()

    def test_all_9_blocks_decoded(self):
        """Test that all 9 block bits are decoded from a 2-octet bitstring."""
        from pyiec61850.tase2 import (
            BLOCK_1,
            BLOCK_2,
            BLOCK_3,
            BLOCK_4,
            BLOCK_5,
            BLOCK_6,
            BLOCK_7,
            BLOCK_8,
            BLOCK_9,
            TASE2Client,
        )

        client = TASE2Client()
        # All 9 blocks set:
        # Octet 1: 0xFF (blocks 1-8, bits 0-7)
        # Octet 2 MSB: 0x80 shifted to 0x8000 (block 9, bit 8)
        # Total: 0xFF | 0x8000 = 0x80FF
        client._parse_supported_features(0x80FF)

        blocks = client._server_capabilities["supported_blocks"]
        for block in [
            BLOCK_1,
            BLOCK_2,
            BLOCK_3,
            BLOCK_4,
            BLOCK_5,
            BLOCK_6,
            BLOCK_7,
            BLOCK_8,
            BLOCK_9,
        ]:
            self.assertIn(block, blocks, f"Block {block} should be present")
        self.assertEqual(len(blocks), 9)

    def test_single_block_bits(self):
        """Test each block bit individually."""
        from pyiec61850.tase2 import (
            SUPPORTED_FEATURES_BLOCK_1,
            SUPPORTED_FEATURES_BLOCK_2,
            SUPPORTED_FEATURES_BLOCK_3,
            SUPPORTED_FEATURES_BLOCK_4,
            SUPPORTED_FEATURES_BLOCK_5,
            SUPPORTED_FEATURES_BLOCK_6,
            SUPPORTED_FEATURES_BLOCK_7,
            SUPPORTED_FEATURES_BLOCK_8,
            SUPPORTED_FEATURES_BLOCK_9,
            TASE2Client,
        )

        expected = [
            (SUPPORTED_FEATURES_BLOCK_1, 1),
            (SUPPORTED_FEATURES_BLOCK_2, 2),
            (SUPPORTED_FEATURES_BLOCK_3, 3),
            (SUPPORTED_FEATURES_BLOCK_4, 4),
            (SUPPORTED_FEATURES_BLOCK_5, 5),
            (SUPPORTED_FEATURES_BLOCK_6, 6),
            (SUPPORTED_FEATURES_BLOCK_7, 7),
            (SUPPORTED_FEATURES_BLOCK_8, 8),
            (SUPPORTED_FEATURES_BLOCK_9, 9),
        ]

        for bitmask, block_num in expected:
            client = TASE2Client()
            client._parse_supported_features(bitmask)
            blocks = client._server_capabilities["supported_blocks"]
            self.assertEqual(
                blocks, [block_num], f"Bitmask 0x{bitmask:04X} should decode to block {block_num}"
            )

    def test_block_bit_values(self):
        """Test SUPPORTED_FEATURES constants have correct bit values."""
        from pyiec61850.tase2 import (
            SUPPORTED_FEATURES_BLOCK_1,
            SUPPORTED_FEATURES_BLOCK_2,
            SUPPORTED_FEATURES_BLOCK_3,
            SUPPORTED_FEATURES_BLOCK_4,
            SUPPORTED_FEATURES_BLOCK_5,
            SUPPORTED_FEATURES_BLOCK_6,
            SUPPORTED_FEATURES_BLOCK_7,
            SUPPORTED_FEATURES_BLOCK_8,
            SUPPORTED_FEATURES_BLOCK_9,
        )

        self.assertEqual(SUPPORTED_FEATURES_BLOCK_1, 0x80)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_2, 0x40)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_3, 0x20)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_4, 0x10)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_5, 0x08)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_6, 0x04)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_7, 0x02)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_8, 0x01)
        self.assertEqual(SUPPORTED_FEATURES_BLOCK_9, 0x8000)

    def test_blocks_6_through_8_first_octet(self):
        """Test blocks 6-8 in the low bits of the first octet."""
        from pyiec61850.tase2 import BLOCK_6, BLOCK_7, BLOCK_8, TASE2Client

        client = TASE2Client()
        # Blocks 6+7+8 = 0x04 | 0x02 | 0x01 = 0x07
        client._parse_supported_features(0x07)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertIn(BLOCK_6, blocks)
        self.assertIn(BLOCK_7, blocks)
        self.assertIn(BLOCK_8, blocks)
        self.assertEqual(len(blocks), 3)

    def test_no_blocks_set(self):
        """Test parsing with zero features bitstring."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0x00)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertEqual(blocks, [])

    def test_typical_d2000_bitstring(self):
        """Test parsing the typical D2000 bitstring (0xC0 = blocks 1+2)."""
        from pyiec61850.tase2 import BLOCK_1, BLOCK_2, TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0xC0)

        blocks = client._server_capabilities["supported_blocks"]
        self.assertEqual(blocks, [BLOCK_1, BLOCK_2])

    def test_supported_blocks_summary(self):
        """Test human-readable summary is stored."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0xC8)  # blocks 1, 2, 5

        summary = client._server_capabilities["supported_blocks_summary"]
        self.assertIn("Block 1", summary)
        self.assertIn("BASIC", summary)
        self.assertIn("Block 2", summary)
        self.assertIn("RBE", summary)
        self.assertIn("Block 5", summary)
        self.assertIn("CONTROL", summary)

    def test_supported_blocks_summary_empty(self):
        """Test summary when no blocks are supported."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0x00)

        summary = client._server_capabilities["supported_blocks_summary"]
        self.assertEqual(summary, "none")

    def test_get_server_blocks_with_capabilities(self):
        """Test get_server_blocks returns all 9 blocks with support status."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # Parse blocks 1, 2, 5 (0xC8)
        client._parse_supported_features(0xC8)

        result = client.get_server_blocks()

        self.assertEqual(len(result), 9)

        # Block 1 should be supported
        self.assertEqual(result[1]["name"], "BASIC")
        self.assertTrue(result[1]["supported"])
        self.assertIn("Basic services", result[1]["description"])

        # Block 2 should be supported
        self.assertEqual(result[2]["name"], "RBE")
        self.assertTrue(result[2]["supported"])

        # Block 3 should NOT be supported
        self.assertEqual(result[3]["name"], "BLOCKED_TRANSFERS")
        self.assertFalse(result[3]["supported"])

        # Block 5 should be supported
        self.assertEqual(result[5]["name"], "CONTROL")
        self.assertTrue(result[5]["supported"])

        # Block 6-9 should NOT be supported
        for block_num in [6, 7, 8, 9]:
            self.assertFalse(
                result[block_num]["supported"], f"Block {block_num} should not be supported"
            )

    def test_get_server_blocks_no_capabilities(self):
        """Test get_server_blocks returns None for supported when no data."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        # Don't parse any features

        result = client.get_server_blocks()

        self.assertEqual(len(result), 9)
        for block_num in range(1, 10):
            self.assertIsNone(
                result[block_num]["supported"],
                f"Block {block_num} should be None when no capabilities read",
            )

    def test_get_server_blocks_all_supported(self):
        """Test get_server_blocks when all 9 blocks are supported."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0x80FF)  # all 9 blocks

        result = client.get_server_blocks()

        for block_num in range(1, 10):
            self.assertTrue(
                result[block_num]["supported"], f"Block {block_num} should be supported"
            )

    def test_get_server_blocks_informative_descriptions(self):
        """Test that blocks 6-9 have informative-since-2014 descriptions."""
        from pyiec61850.tase2 import TASE2Client

        client = TASE2Client()
        client._parse_supported_features(0x00)

        result = client.get_server_blocks()

        self.assertEqual(result[6]["name"], "PROGRAMS")
        self.assertIn("informative", result[6]["description"].lower())
        self.assertEqual(result[7]["name"], "EVENTS")
        self.assertIn("informative", result[7]["description"].lower())
        self.assertEqual(result[8]["name"], "ACCOUNTS")
        self.assertIn("informative", result[8]["description"].lower())
        self.assertEqual(result[9]["name"], "TIME_SERIES")
        self.assertIn("informative", result[9]["description"].lower())

    def test_conformance_blocks_has_9_entries(self):
        """Test CONFORMANCE_BLOCKS dict has all 9 blocks."""
        from pyiec61850.tase2 import CONFORMANCE_BLOCKS

        self.assertEqual(len(CONFORMANCE_BLOCKS), 9)
        for block_num in range(1, 10):
            self.assertIn(
                block_num, CONFORMANCE_BLOCKS, f"Block {block_num} missing from CONFORMANCE_BLOCKS"
            )

    def test_block_3_renamed_from_reserved(self):
        """Test Block 3 was renamed from RESERVED to BLOCKED_TRANSFERS."""
        from pyiec61850.tase2 import BLOCK_3, CONFORMANCE_BLOCKS

        name, description = CONFORMANCE_BLOCKS[BLOCK_3]
        self.assertEqual(name, "BLOCKED_TRANSFERS")
        self.assertIn("Blocked data transfers", description)

    def test_new_block_constants_importable(self):
        """Test BLOCK_6 through BLOCK_9 are importable."""
        from pyiec61850.tase2 import BLOCK_6, BLOCK_7, BLOCK_8, BLOCK_9

        self.assertEqual(BLOCK_6, 6)
        self.assertEqual(BLOCK_7, 7)
        self.assertEqual(BLOCK_8, 8)
        self.assertEqual(BLOCK_9, 9)

    def test_new_supported_features_constants_importable(self):
        """Test SUPPORTED_FEATURES_BLOCK_6 through _9 are importable."""
        from pyiec61850.tase2 import (
            SUPPORTED_FEATURES_BLOCK_6,
            SUPPORTED_FEATURES_BLOCK_7,
            SUPPORTED_FEATURES_BLOCK_8,
            SUPPORTED_FEATURES_BLOCK_9,
        )

        self.assertIsInstance(SUPPORTED_FEATURES_BLOCK_6, int)
        self.assertIsInstance(SUPPORTED_FEATURES_BLOCK_7, int)
        self.assertIsInstance(SUPPORTED_FEATURES_BLOCK_8, int)
        self.assertIsInstance(SUPPORTED_FEATURES_BLOCK_9, int)

    def test_new_constants_in_all(self):
        """Test new block constants are in __all__."""
        from pyiec61850.tase2 import __all__

        for name in [
            "BLOCK_6",
            "BLOCK_7",
            "BLOCK_8",
            "BLOCK_9",
            "SUPPORTED_FEATURES_BLOCK_6",
            "SUPPORTED_FEATURES_BLOCK_7",
            "SUPPORTED_FEATURES_BLOCK_8",
            "SUPPORTED_FEATURES_BLOCK_9",
        ]:
            self.assertIn(name, __all__, f"{name} missing from __all__")


if __name__ == "__main__":
    unittest.main()
