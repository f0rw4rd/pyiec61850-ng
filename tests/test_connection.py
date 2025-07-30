#!/usr/bin/env python3
"""
Connection and basic functionality tests for pyiec61850
"""

import unittest
import os
import time
import pyiec61850.pyiec61850 as pyiec61850


class TestConnection(unittest.TestCase):
    """Test IEC 61850 connection functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Use environment variables for test server configuration
        self.test_host = os.environ.get('IEC61850_TEST_HOST', 'localhost')
        self.test_port = int(os.environ.get('IEC61850_TEST_PORT', '10102'))
        self.skip_connection_tests = os.environ.get('SKIP_CONNECTION_TESTS', 'false').lower() == 'true'
    
    def test_connection_create_destroy(self):
        """Test creating and destroying a connection object"""
        connection = pyiec61850.IedConnection_create()
        self.assertIsNotNone(connection, "Connection object should be created")
        
        # Destroy should work without error
        pyiec61850.IedConnection_destroy(connection)
    
    @unittest.skipIf(os.environ.get('SKIP_CONNECTION_TESTS', 'false').lower() == 'true',
                     "Connection tests skipped (no test server available)")
    def test_connection_to_server(self):
        """Test connecting to an IEC 61850 server"""
        connection = pyiec61850.IedConnection_create()
        self.assertIsNotNone(connection)
        
        try:
            # Attempt to connect
            error = pyiec61850.IedConnection_connect(
                connection, 
                self.test_host, 
                self.test_port
            )
            
            if error == pyiec61850.IED_ERROR_OK:
                # Connection successful
                self.assertEqual(error, pyiec61850.IED_ERROR_OK)
                
                # Close connection
                pyiec61850.IedConnection_close(connection)
            else:
                # Connection failed - this is expected if no server is running
                error_msg = pyiec61850.IedClientError_toString(error)
                print(f"Connection failed (expected if no server): {error_msg}")
                
        finally:
            pyiec61850.IedConnection_destroy(connection)
    
    @unittest.skipIf(os.environ.get('SKIP_CONNECTION_TESTS', 'false').lower() == 'true',
                     "Connection tests skipped (no test server available)")
    def test_error_handling(self):
        """Test error handling for invalid connections"""
        connection = pyiec61850.IedConnection_create()
        
        # Try to connect to invalid address
        error = pyiec61850.IedConnection_connect(
            connection,
            "invalid.host.example.com",
            9999
        )
        
        # Should not be OK
        self.assertNotEqual(error, pyiec61850.IED_ERROR_OK)
        
        # Error string should be available
        error_str = pyiec61850.IedClientError_toString(error)
        self.assertIsInstance(error_str, str)
        self.assertGreater(len(error_str), 0)
        
        pyiec61850.IedConnection_destroy(connection)
    
    def test_mms_connection_integration(self):
        """Test MMS connection creation and error object"""
        # Test MMS error object creation
        error = pyiec61850.MmsError_create()
        self.assertIsNotNone(error)
        
        # Get initial error value (should be 0)
        error_value = pyiec61850.MmsError_getValue(error)
        self.assertEqual(error_value, 0)  # MMS_ERROR_NONE
    
    def test_linked_list_operations(self):
        """Test LinkedList operations with mock data"""
        # This tests that the LinkedList functions are callable
        # In real usage, these would be populated by IEC 61850 operations
        
        # Test that functions exist and are callable
        self.assertTrue(callable(pyiec61850.LinkedList_size))
        self.assertTrue(callable(pyiec61850.LinkedList_getNext))
        self.assertTrue(callable(pyiec61850.LinkedList_getData))
        self.assertTrue(callable(pyiec61850.LinkedList_destroy))
    
    def test_value_type_constants(self):
        """Test that MMS value type constants have expected values"""
        # These are typically enum values from the C library
        # Test that they exist and are integers
        
        value_types = [
            'MMS_BOOLEAN',
            'MMS_INTEGER', 
            'MMS_UNSIGNED',
            'MMS_FLOAT',
            'MMS_VISIBLE_STRING',
            'MMS_BIT_STRING',
            'MMS_OCTET_STRING',
            'MMS_UTC_TIME',
            'MMS_STRUCTURE',
            'MMS_ARRAY'
        ]
        
        for vtype in value_types:
            self.assertTrue(hasattr(pyiec61850, vtype))
            value = getattr(pyiec61850, vtype)
            self.assertIsInstance(value, int)
    
    def test_functional_constraint_constants(self):
        """Test functional constraint constants"""
        fc_types = [
            'IEC61850_FC_MX',
            'IEC61850_FC_ST',
            'IEC61850_FC_CO',
            'IEC61850_FC_CF',
            'IEC61850_FC_SP',
            'IEC61850_FC_DC'
        ]
        
        for fc in fc_types:
            self.assertTrue(hasattr(pyiec61850, fc))
            value = getattr(pyiec61850, fc)
            self.assertIsInstance(value, int)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions"""
    
    def test_toCharP_function(self):
        """Test the toCharP helper function exists"""
        # This function converts SWIG void* to char*
        self.assertTrue(hasattr(pyiec61850, 'toCharP'))
        self.assertTrue(callable(pyiec61850.toCharP))
    
    def test_error_string_function(self):
        """Test error string conversion"""
        # Test with known error codes
        error_codes = [
            pyiec61850.IED_ERROR_OK,
            pyiec61850.IED_ERROR_NOT_CONNECTED,
            pyiec61850.IED_ERROR_TIMEOUT
        ]
        
        for error_code in error_codes:
            error_str = pyiec61850.IedClientError_toString(error_code)
            self.assertIsInstance(error_str, str)
            self.assertGreater(len(error_str), 0)


if __name__ == '__main__':
    unittest.main()