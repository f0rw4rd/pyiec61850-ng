#!/usr/bin/env python3
"""
Basic import and functionality tests for pyiec61850
"""

import unittest
import sys
import os


class TestImport(unittest.TestCase):
    """Test basic module import and availability of key functions"""
    
    def test_import_module(self):
        """Test that the module can be imported"""
        try:
            import pyiec61850.pyiec61850 as pyiec61850
            self.assertTrue(True, "Module imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import module: {e}")
    
    def test_core_functions_exist(self):
        """Test that core IEC 61850 functions are available"""
        import pyiec61850.pyiec61850 as pyiec61850
        
        # Connection functions
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_create'))
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_connect'))
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_close'))
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_destroy'))
        
        # Discovery functions
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_getLogicalDeviceList'))
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_getLogicalDeviceDirectory'))
        
        # Data access functions
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_readObject'))
        self.assertTrue(hasattr(pyiec61850, 'IedConnection_writeObject'))
        
        # MMS functions
        self.assertTrue(hasattr(pyiec61850, 'MmsConnection_create'))
        self.assertTrue(hasattr(pyiec61850, 'MmsConnection_downloadFile'))
        self.assertTrue(hasattr(pyiec61850, 'MmsError_create'))
        self.assertTrue(hasattr(pyiec61850, 'MmsError_getValue'))
        
        # Value functions
        self.assertTrue(hasattr(pyiec61850, 'MmsValue_getType'))
        self.assertTrue(hasattr(pyiec61850, 'MmsValue_toFloat'))
        self.assertTrue(hasattr(pyiec61850, 'MmsValue_toInt64'))
        self.assertTrue(hasattr(pyiec61850, 'MmsValue_toString'))
        self.assertTrue(hasattr(pyiec61850, 'MmsValue_delete'))
        
        # LinkedList functions
        self.assertTrue(hasattr(pyiec61850, 'LinkedList_size'))
        self.assertTrue(hasattr(pyiec61850, 'LinkedList_getNext'))
        self.assertTrue(hasattr(pyiec61850, 'LinkedList_getData'))
        self.assertTrue(hasattr(pyiec61850, 'LinkedList_destroy'))
        
        # Helper functions
        self.assertTrue(hasattr(pyiec61850, 'toCharP'))
        self.assertTrue(hasattr(pyiec61850, 'IedClientError_toString'))
    
    def test_constants_exist(self):
        """Test that important constants are defined"""
        import pyiec61850.pyiec61850 as pyiec61850
        
        # Error codes
        self.assertTrue(hasattr(pyiec61850, 'IED_ERROR_OK'))
        self.assertTrue(hasattr(pyiec61850, 'IED_ERROR_NOT_CONNECTED'))
        self.assertTrue(hasattr(pyiec61850, 'IED_ERROR_TIMEOUT'))
        self.assertTrue(hasattr(pyiec61850, 'IED_ERROR_ACCESS_DENIED'))
        
        # MMS value types
        self.assertTrue(hasattr(pyiec61850, 'MMS_BOOLEAN'))
        self.assertTrue(hasattr(pyiec61850, 'MMS_INTEGER'))
        self.assertTrue(hasattr(pyiec61850, 'MMS_FLOAT'))
        self.assertTrue(hasattr(pyiec61850, 'MMS_VISIBLE_STRING'))
        
        # Functional constraints
        self.assertTrue(hasattr(pyiec61850, 'IEC61850_FC_MX'))
        self.assertTrue(hasattr(pyiec61850, 'IEC61850_FC_ST'))
        self.assertTrue(hasattr(pyiec61850, 'IEC61850_FC_CF'))
        self.assertTrue(hasattr(pyiec61850, 'IEC61850_FC_SP'))
        self.assertTrue(hasattr(pyiec61850, 'IEC61850_FC_DC'))
        
        # ACSI classes
        self.assertTrue(hasattr(pyiec61850, 'ACSI_CLASS_DATA_OBJECT'))
    
    def test_library_version_info(self):
        """Test that version information is available"""
        import pyiec61850
        
        # Check Python version compatibility
        py_version = sys.version_info
        self.assertGreaterEqual(py_version.major, 3)
        self.assertGreaterEqual(py_version.minor, 8)
        
        # Note: Version info would come from setup.py in a proper package


if __name__ == '__main__':
    unittest.main()