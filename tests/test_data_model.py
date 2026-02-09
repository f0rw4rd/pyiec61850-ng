#!/usr/bin/env python3
"""
Data model and discovery tests for pyiec61850
"""

import os
import unittest

import pyiec61850.pyiec61850 as pyiec61850


class TestDataModel(unittest.TestCase):
    """Test IEC 61850 data model discovery and access"""

    def setUp(self):
        """Set up test environment"""
        self.test_host = os.environ.get("IEC61850_TEST_HOST", "localhost")
        self.test_port = int(os.environ.get("IEC61850_TEST_PORT", "10102"))
        self.skip_tests = os.environ.get("SKIP_CONNECTION_TESTS", "false").lower() == "true"

        if not self.skip_tests:
            # Create connection for tests
            self.connection = pyiec61850.IedConnection_create()
            error = pyiec61850.IedConnection_connect(
                self.connection, self.test_host, self.test_port
            )
            if error != pyiec61850.IED_ERROR_OK:
                pyiec61850.IedConnection_destroy(self.connection)
                self.connection = None
                self.skip_tests = True
        else:
            self.connection = None

    def tearDown(self):
        """Clean up after tests"""
        if self.connection:
            pyiec61850.IedConnection_close(self.connection)
            pyiec61850.IedConnection_destroy(self.connection)

    @unittest.skipIf(
        os.environ.get("SKIP_CONNECTION_TESTS", "false").lower() == "true",
        "Connection tests skipped",
    )
    def test_logical_device_discovery(self):
        """Test discovering logical devices"""
        if not self.connection:
            self.skipTest("No connection available")

        # Get logical device list
        result = pyiec61850.IedConnection_getLogicalDeviceList(self.connection)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        device_list, error = result
        self.assertEqual(error, pyiec61850.IED_ERROR_OK)

        if device_list:
            # Count devices
            device_count = pyiec61850.LinkedList_size(device_list)
            self.assertGreaterEqual(device_count, 0)

            # Iterate through devices
            devices = []
            element = pyiec61850.LinkedList_getNext(device_list)
            while element:
                device_data = pyiec61850.LinkedList_getData(element)
                if device_data:
                    device_name = pyiec61850.toCharP(device_data)
                    self.assertIsInstance(device_name, str)
                    devices.append(device_name)
                element = pyiec61850.LinkedList_getNext(element)

            # Clean up
            pyiec61850.LinkedList_destroy(device_list)

            # Should have found at least one device on a test server
            if device_count > 0:
                self.assertGreater(len(devices), 0)

    @unittest.skipIf(
        os.environ.get("SKIP_CONNECTION_TESTS", "false").lower() == "true",
        "Connection tests skipped",
    )
    def test_logical_node_discovery(self):
        """Test discovering logical nodes"""
        if not self.connection:
            self.skipTest("No connection available")

        # First get a logical device
        device_list, error = pyiec61850.IedConnection_getLogicalDeviceList(self.connection)

        if error == pyiec61850.IED_ERROR_OK and device_list:
            element = pyiec61850.LinkedList_getNext(device_list)
            if element:
                device_data = pyiec61850.LinkedList_getData(element)
                device_name = pyiec61850.toCharP(device_data) if device_data else None

                if device_name:
                    # Get logical nodes for this device
                    ln_list, ln_error = pyiec61850.IedConnection_getLogicalDeviceDirectory(
                        self.connection, device_name
                    )

                    self.assertEqual(ln_error, pyiec61850.IED_ERROR_OK)

                    if ln_list:
                        # Count nodes
                        node_count = pyiec61850.LinkedList_size(ln_list)
                        self.assertGreaterEqual(node_count, 0)

                        # Clean up
                        pyiec61850.LinkedList_destroy(ln_list)

            pyiec61850.LinkedList_destroy(device_list)

    @unittest.skipIf(
        os.environ.get("SKIP_CONNECTION_TESTS", "false").lower() == "true",
        "Connection tests skipped",
    )
    def test_read_object_returns_tuple(self):
        """Test that readObject returns a tuple [value, error]"""
        if not self.connection:
            self.skipTest("No connection available")

        # Try to read a common object (may not exist on all servers)
        result = pyiec61850.IedConnection_readObject(
            self.connection, "simpleIOGenericIO/GGIO1.AnIn1.mag.f", pyiec61850.IEC61850_FC_MX
        )

        # Should return a tuple
        self.assertIsInstance(result, (list, tuple))
        self.assertEqual(len(result), 2)

        value, error = result

        # Error should be an integer
        self.assertIsInstance(error, int)

        # If successful, clean up the value
        if error == pyiec61850.IED_ERROR_OK and value:
            pyiec61850.MmsValue_delete(value)

    def test_mms_value_type_extraction(self):
        """Test MMS value type functions exist"""
        # These functions should exist even without a connection

        # Value type functions
        self.assertTrue(callable(pyiec61850.MmsValue_getType))
        self.assertTrue(callable(pyiec61850.MmsValue_getTypeString))

        # Value extraction functions
        self.assertTrue(callable(pyiec61850.MmsValue_toFloat))
        self.assertTrue(callable(pyiec61850.MmsValue_toInt64))
        self.assertTrue(callable(pyiec61850.MmsValue_toUint32))
        self.assertTrue(callable(pyiec61850.MmsValue_toString))
        self.assertTrue(callable(pyiec61850.MmsValue_getBoolean))

        # Value utility functions
        self.assertTrue(callable(pyiec61850.MmsValue_getBitStringSize))
        self.assertTrue(callable(pyiec61850.MmsValue_getOctetStringSize))
        self.assertTrue(callable(pyiec61850.MmsValue_getArraySize))
        self.assertTrue(callable(pyiec61850.MmsValue_getUtcTimeInMs))

        # Cleanup function
        self.assertTrue(callable(pyiec61850.MmsValue_delete))


class TestFileOperations(unittest.TestCase):
    """Test file transfer operations"""

    def test_file_operation_functions_exist(self):
        """Test that file operation functions are available"""
        # IED file functions
        self.assertTrue(hasattr(pyiec61850, "IedConnection_getFile"))
        self.assertTrue(hasattr(pyiec61850, "IedConnection_getFileDirectory"))
        self.assertTrue(hasattr(pyiec61850, "IedConnection_deleteFile"))

        # MMS file functions
        self.assertTrue(hasattr(pyiec61850, "MmsConnection_downloadFile"))
        self.assertTrue(hasattr(pyiec61850, "MmsConnection_getFileDirectory"))

        # File directory entry functions
        self.assertTrue(hasattr(pyiec61850, "FileDirectoryEntry_getFileName"))
        self.assertTrue(hasattr(pyiec61850, "FileDirectoryEntry_getFileSize"))
        self.assertTrue(hasattr(pyiec61850, "FileDirectoryEntry_getLastModified"))
        self.assertTrue(hasattr(pyiec61850, "FileDirectoryEntry_destroy"))

    def test_mms_connection_from_ied(self):
        """Test getting MMS connection from IED connection"""
        self.assertTrue(hasattr(pyiec61850, "IedConnection_getMmsConnection"))
        self.assertTrue(callable(pyiec61850.IedConnection_getMmsConnection))


if __name__ == "__main__":
    unittest.main()
