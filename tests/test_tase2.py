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


class TestTASE2Client(unittest.TestCase):
    """Test client without connection."""

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
        """Test point type constants."""
        from pyiec61850.tase2 import (
            POINT_TYPE_REAL,
            POINT_TYPE_STATE,
            POINT_TYPE_DISCRETE,
            POINT_TYPES,
        )
        self.assertEqual(POINT_TYPE_REAL, 1)
        self.assertEqual(POINT_TYPE_STATE, 2)
        self.assertEqual(POINT_TYPE_DISCRETE, 3)
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


if __name__ == '__main__':
    unittest.main()
