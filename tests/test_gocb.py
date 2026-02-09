#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.gocb module - GOOSE Control Block client.

All tests use mocks (no C library needed).
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import logging

logging.disable(logging.CRITICAL)


class TestGoCBImports(unittest.TestCase):
    """Test gocb module imports."""

    def test_import_gocb_client(self):
        from pyiec61850.mms.gocb import GoCBClient
        self.assertIsNotNone(GoCBClient)

    def test_import_gocb_info(self):
        from pyiec61850.mms.gocb import GoCBInfo
        self.assertIsNotNone(GoCBInfo)

    def test_import_gocb_error(self):
        from pyiec61850.mms.gocb import GoCBError
        from pyiec61850.mms.exceptions import MMSError
        self.assertTrue(issubclass(GoCBError, MMSError))

    def test_import_from_mms_package(self):
        from pyiec61850.mms import GoCBClient, GoCBInfo, GoCBError
        self.assertIsNotNone(GoCBClient)
        self.assertIsNotNone(GoCBInfo)
        self.assertIsNotNone(GoCBError)


class TestGoCBInfo(unittest.TestCase):
    """Test GoCBInfo dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.gocb import GoCBInfo
        info = GoCBInfo()
        self.assertEqual(info.gocb_ref, "")
        self.assertEqual(info.goose_id, "")
        self.assertEqual(info.dataset, "")
        self.assertFalse(info.enabled)
        self.assertEqual(info.conf_rev, 0)
        self.assertEqual(info.min_time, 0)
        self.assertEqual(info.max_time, 0)
        self.assertFalse(info.fixed_offs)
        self.assertFalse(info.nds_comm)
        self.assertEqual(info.appid, 0)
        self.assertEqual(info.vlan_id, 0)
        self.assertEqual(info.vlan_priority, 0)
        self.assertEqual(info.dst_mac, "")

    def test_creation_with_values(self):
        from pyiec61850.mms.gocb import GoCBInfo
        info = GoCBInfo(
            gocb_ref="LD/LLN0$GO$gcb01",
            goose_id="GOOSE_ID_1",
            dataset="LD/LLN0$DataSet1",
            enabled=True,
            conf_rev=3,
            min_time=10,
            max_time=5000,
            fixed_offs=True,
            nds_comm=False,
            appid=0x1000,
            vlan_id=100,
            vlan_priority=4,
            dst_mac="01:0c:cd:01:00:00",
        )
        self.assertEqual(info.goose_id, "GOOSE_ID_1")
        self.assertTrue(info.enabled)
        self.assertEqual(info.conf_rev, 3)
        self.assertEqual(info.appid, 0x1000)
        self.assertEqual(info.dst_mac, "01:0c:cd:01:00:00")


class TestGoCBClient(unittest.TestCase):
    """Test GoCBClient class."""

    def test_creation_without_library_raises(self):
        from pyiec61850.mms.gocb import GoCBClient
        from pyiec61850.mms.exceptions import LibraryNotFoundError
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', False):
            with self.assertRaises(LibraryNotFoundError):
                GoCBClient(Mock())

    def test_creation_with_library(self):
        from pyiec61850.mms.gocb import GoCBClient
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850'):
                client = GoCBClient(Mock())
                self.assertIsNotNone(client)

    def test_read_not_connected_raises(self):
        from pyiec61850.mms.gocb import GoCBClient
        from pyiec61850.mms.exceptions import NotConnectedError
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850'):
                mock_mms = Mock()
                mock_mms.is_connected = False
                client = GoCBClient(mock_mms)
                with self.assertRaises(NotConnectedError):
                    client.read("LD/LLN0$GO$gcb01")

    def test_read_success(self):
        """Successful GoCB read should return populated GoCBInfo."""
        from pyiec61850.mms.gocb import GoCBClient
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_mms = Mock()
                mock_mms.is_connected = True
                mock_mms._connection = Mock()
                mock_iec.IED_ERROR_OK = 0

                # Mock getGoCBValues returning (handle, 0)
                gocb_handle = Mock()
                mock_iec.IedConnection_getGoCBValues.return_value = (gocb_handle, 0)

                # Mock all getters
                mock_iec.ClientGooseControlBlock_getGoID.return_value = "GOOSE1"
                mock_iec.ClientGooseControlBlock_getDatSet.return_value = "LD/LLN0$DS1"
                mock_iec.ClientGooseControlBlock_getGoEna.return_value = True
                mock_iec.ClientGooseControlBlock_getConfRev.return_value = 5
                mock_iec.ClientGooseControlBlock_getMinTime.return_value = 4
                mock_iec.ClientGooseControlBlock_getMaxTime.return_value = 1000
                mock_iec.ClientGooseControlBlock_getFixedOffs.return_value = False
                mock_iec.ClientGooseControlBlock_getNdsComm.return_value = True
                mock_iec.ClientGooseControlBlock_getDstAddress_appid.return_value = 0x3000
                mock_iec.ClientGooseControlBlock_getDstAddress_vid.return_value = 0
                mock_iec.ClientGooseControlBlock_getDstAddress_priority.return_value = 4
                mock_mac = Mock()
                mock_iec.ClientGooseControlBlock_getDstAddress_addr.return_value = mock_mac
                mock_iec.MmsValue_getOctetStringSize.return_value = 6
                mock_iec.MmsValue_getOctetStringOctet.side_effect = [0x01, 0x0C, 0xCD, 0x01, 0x00, 0x00]

                client = GoCBClient(mock_mms)
                info = client.read("LD/LLN0$GO$gcb01")

                self.assertEqual(info.gocb_ref, "LD/LLN0$GO$gcb01")
                self.assertEqual(info.goose_id, "GOOSE1")
                self.assertEqual(info.dataset, "LD/LLN0$DS1")
                self.assertTrue(info.enabled)
                self.assertEqual(info.conf_rev, 5)
                self.assertEqual(info.min_time, 4)
                self.assertEqual(info.max_time, 1000)
                self.assertFalse(info.fixed_offs)
                self.assertTrue(info.nds_comm)
                self.assertEqual(info.appid, 0x3000)
                self.assertEqual(info.dst_mac, "01:0c:cd:01:00:00")

                # Verify cleanup
                mock_iec.ClientGooseControlBlock_destroy.assert_called_once_with(gocb_handle)

    def test_read_error_raises(self):
        """Read failure should raise ReadError."""
        from pyiec61850.mms.gocb import GoCBClient
        from pyiec61850.mms.exceptions import ReadError
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_mms = Mock()
                mock_mms.is_connected = True
                mock_mms._connection = Mock()
                mock_iec.IED_ERROR_OK = 0

                # Return error code
                mock_iec.IedConnection_getGoCBValues.return_value = (None, 5)

                client = GoCBClient(mock_mms)
                with self.assertRaises(ReadError):
                    client.read("LD/LLN0$GO$bad_ref")

    def test_read_null_response_raises(self):
        """Null response from getGoCBValues should raise ReadError."""
        from pyiec61850.mms.gocb import GoCBClient
        from pyiec61850.mms.exceptions import ReadError
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_mms = Mock()
                mock_mms.is_connected = True
                mock_mms._connection = Mock()
                mock_iec.IED_ERROR_OK = 0

                mock_iec.IedConnection_getGoCBValues.return_value = (None, 0)

                client = GoCBClient(mock_mms)
                with self.assertRaises(ReadError):
                    client.read("LD/LLN0$GO$gcb01")

    def test_read_cleanup_on_exception(self):
        """GoCB handle should be destroyed even if parsing raises."""
        from pyiec61850.mms.gocb import GoCBClient
        from pyiec61850.mms.exceptions import ReadError
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_mms = Mock()
                mock_mms.is_connected = True
                mock_mms._connection = Mock()
                mock_iec.IED_ERROR_OK = 0

                gocb_handle = Mock()
                mock_iec.IedConnection_getGoCBValues.return_value = (gocb_handle, 0)
                # Make a getter blow up
                mock_iec.ClientGooseControlBlock_getGoID.side_effect = Exception("boom")
                # getDatSet etc still need to work for the rest of _parse_gocb
                mock_iec.ClientGooseControlBlock_getDatSet.return_value = ""
                mock_iec.ClientGooseControlBlock_getGoEna.return_value = False
                mock_iec.ClientGooseControlBlock_getConfRev.return_value = 0
                mock_iec.ClientGooseControlBlock_getMinTime.return_value = 0
                mock_iec.ClientGooseControlBlock_getMaxTime.return_value = 0
                mock_iec.ClientGooseControlBlock_getFixedOffs.return_value = False
                mock_iec.ClientGooseControlBlock_getNdsComm.return_value = False
                mock_iec.ClientGooseControlBlock_getDstAddress_appid.return_value = 0
                mock_iec.ClientGooseControlBlock_getDstAddress_vid.return_value = 0
                mock_iec.ClientGooseControlBlock_getDstAddress_priority.return_value = 0
                mock_iec.ClientGooseControlBlock_getDstAddress_addr.return_value = None

                client = GoCBClient(mock_mms)
                # Should not raise -- getter exception is caught in _parse_gocb
                info = client.read("LD/LLN0$GO$gcb01")
                # goose_id should be empty since getter failed
                self.assertEqual(info.goose_id, "")
                mock_iec.ClientGooseControlBlock_destroy.assert_called_once_with(gocb_handle)

    def test_context_manager(self):
        from pyiec61850.mms.gocb import GoCBClient
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850'):
                mock_mms = Mock()
                with GoCBClient(mock_mms) as client:
                    self.assertIsNotNone(client)

    def test_enumerate_discovers_gocbs(self):
        """Enumerate should walk LD/LN/GoCB and read each."""
        from pyiec61850.mms.gocb import GoCBClient
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.utils._HAS_IEC61850', True):
                with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                    with patch('pyiec61850.mms.utils.iec61850', mock_iec):
                        mock_mms = Mock()
                        mock_mms.is_connected = True
                        mock_mms._connection = Mock()
                        mock_iec.IED_ERROR_OK = 0
                        mock_iec.ACSI_CLASS_GoCB = 7

                        # getLogicalDeviceList
                        ld_list = Mock()
                        mock_iec.IedConnection_getLogicalDeviceList.return_value = (ld_list, 0)

                        # Linked list iteration for LD list: one device "LD1"
                        ld_elem = Mock()
                        ld_data = Mock()

                        # getLogicalNodeList
                        ln_list = Mock()
                        mock_iec.IedConnection_getLogicalNodeList.return_value = (ln_list, 0)

                        ln_elem = Mock()
                        ln_data = Mock()

                        # getLogicalNodeDirectory (GoCB class)
                        dir_list = Mock()
                        mock_iec.IedConnection_getLogicalNodeDirectory.return_value = (dir_list, 0)

                        dir_elem = Mock()
                        dir_data = Mock()

                        # Setup LinkedList_getNext chains:
                        # LD list: ld_elem -> None
                        # LN list: ln_elem -> None
                        # Dir list: dir_elem -> None
                        def get_next_side_effect(lst):
                            if lst is ld_list:
                                return ld_elem
                            if lst is ld_elem:
                                return None
                            if lst is ln_list:
                                return ln_elem
                            if lst is ln_elem:
                                return None
                            if lst is dir_list:
                                return dir_elem
                            if lst is dir_elem:
                                return None
                            return None

                        mock_iec.LinkedList_getNext.side_effect = get_next_side_effect

                        def get_data_side_effect(elem):
                            if elem is ld_elem:
                                return ld_data
                            if elem is ln_elem:
                                return ln_data
                            if elem is dir_elem:
                                return dir_data
                            return None

                        mock_iec.LinkedList_getData.side_effect = get_data_side_effect

                        def to_char_p_side_effect(data):
                            if data is ld_data:
                                return "LD1"
                            if data is ln_data:
                                return "LLN0"
                            if data is dir_data:
                                return "gcb01"
                            return None

                        mock_iec.toCharP.side_effect = to_char_p_side_effect

                        # Mock the read() call for the discovered GoCB
                        gocb_handle = Mock()
                        mock_iec.IedConnection_getGoCBValues.return_value = (gocb_handle, 0)
                        mock_iec.ClientGooseControlBlock_getGoID.return_value = "GOOSE1"
                        mock_iec.ClientGooseControlBlock_getDatSet.return_value = "LD1/LLN0$DS1"
                        mock_iec.ClientGooseControlBlock_getGoEna.return_value = False
                        mock_iec.ClientGooseControlBlock_getConfRev.return_value = 1
                        mock_iec.ClientGooseControlBlock_getMinTime.return_value = 0
                        mock_iec.ClientGooseControlBlock_getMaxTime.return_value = 0
                        mock_iec.ClientGooseControlBlock_getFixedOffs.return_value = False
                        mock_iec.ClientGooseControlBlock_getNdsComm.return_value = False
                        mock_iec.ClientGooseControlBlock_getDstAddress_appid.return_value = 0
                        mock_iec.ClientGooseControlBlock_getDstAddress_vid.return_value = 0
                        mock_iec.ClientGooseControlBlock_getDstAddress_priority.return_value = 0
                        mock_iec.ClientGooseControlBlock_getDstAddress_addr.return_value = None

                        client = GoCBClient(mock_mms)
                        results = client.enumerate()

                        self.assertEqual(len(results), 1)
                        self.assertEqual(results[0].gocb_ref, "LD1/LLN0$GO$gcb01")
                        self.assertEqual(results[0].goose_id, "GOOSE1")


class TestFormatMac(unittest.TestCase):
    """Test _format_mac helper."""

    def test_valid_mac(self):
        from pyiec61850.mms.gocb import _format_mac
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_iec.MmsValue_getOctetStringSize.return_value = 6
                mock_iec.MmsValue_getOctetStringOctet.side_effect = [
                    0x01, 0x0C, 0xCD, 0x01, 0x00, 0x01
                ]
                result = _format_mac(Mock())
                self.assertEqual(result, "01:0c:cd:01:00:01")

    def test_none_value(self):
        from pyiec61850.mms.gocb import _format_mac
        result = _format_mac(None)
        self.assertEqual(result, "")

    def test_short_mac(self):
        from pyiec61850.mms.gocb import _format_mac
        with patch('pyiec61850.mms.gocb._HAS_IEC61850', True):
            with patch('pyiec61850.mms.gocb.iec61850') as mock_iec:
                mock_iec.MmsValue_getOctetStringSize.return_value = 3
                result = _format_mac(Mock())
                self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
