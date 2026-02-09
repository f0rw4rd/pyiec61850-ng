#!/usr/bin/env python3
"""
Tests for mms_value_to_python and python_to_mms_value.

All tests use mocks (no C library needed).
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestMmsValueToPython(unittest.TestCase):
    """Test mms_value_to_python conversion function."""

    def _call(self, mock_iec, mms_value):
        """Helper to call mms_value_to_python with mocked library."""
        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                from pyiec61850.mms.utils import mms_value_to_python

                return mms_value_to_python(mms_value)

    def test_none_returns_none(self):
        """None input returns None."""
        mock_iec = Mock()
        result = self._call(mock_iec, None)
        self.assertIsNone(result)

    def test_zero_returns_none(self):
        """Zero (C NULL) returns None."""
        mock_iec = Mock()
        result = self._call(mock_iec, 0)
        self.assertIsNone(result)

    def test_boolean_true(self):
        mock_iec = Mock()
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MmsValue_getType.return_value = 2
        mock_iec.MmsValue_getBoolean.return_value = True
        result = self._call(mock_iec, Mock())
        self.assertIs(result, True)

    def test_boolean_false(self):
        mock_iec = Mock()
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MmsValue_getType.return_value = 2
        mock_iec.MmsValue_getBoolean.return_value = False
        result = self._call(mock_iec, Mock())
        self.assertIs(result, False)

    def test_integer(self):
        mock_iec = Mock()
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MmsValue_getType.return_value = 4
        mock_iec.MmsValue_toInt64.return_value = -42
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, -42)
        self.assertIsInstance(result, int)

    def test_unsigned(self):
        mock_iec = Mock()
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MmsValue_getType.return_value = 5
        mock_iec.MmsValue_toUint32.return_value = 65535
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, 65535)
        self.assertIsInstance(result, int)

    def test_float(self):
        mock_iec = Mock()
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MmsValue_getType.return_value = 6
        mock_iec.MmsValue_toFloat.return_value = 3.14
        result = self._call(mock_iec, Mock())
        self.assertAlmostEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_visible_string(self):
        mock_iec = Mock()
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MmsValue_getType.return_value = 8
        mock_iec.MmsValue_toString.return_value = "hello"
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, "hello")
        self.assertIsInstance(result, str)

    def test_mms_string(self):
        mock_iec = Mock()
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MmsValue_getType.return_value = 13
        mock_iec.MmsValue_toString.return_value = "mms_string"
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, "mms_string")

    def test_bit_string(self):
        mock_iec = Mock()
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MmsValue_getType.return_value = 3
        mock_iec.MmsValue_getBitStringAsInteger.return_value = 0xFF
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, 255)

    def test_octet_string(self):
        mock_iec = Mock()
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MmsValue_getType.return_value = 7
        mock_iec.MmsValue_getOctetStringSize.return_value = 3
        mock_iec.MmsValue_getOctetStringBuffer.return_value = Mock()
        mock_iec.MmsValue_getOctetStringOctet.side_effect = [0xDE, 0xAD, 0xBE]
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, b"\xde\xad\xbe")
        self.assertIsInstance(result, bytes)

    def test_octet_string_empty(self):
        mock_iec = Mock()
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MmsValue_getType.return_value = 7
        mock_iec.MmsValue_getOctetStringSize.return_value = 0
        mock_iec.MmsValue_getOctetStringBuffer.return_value = None
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, b"")

    def test_utc_time(self):
        mock_iec = Mock()
        mock_iec.MMS_UTC_TIME = 14
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_STRUCTURE = 1
        mock_iec.MMS_ARRAY = 0
        mock_iec.MMS_BINARY_TIME = 10
        mock_iec.MmsValue_getType.return_value = 14
        mock_iec.MmsValue_getUtcTimeInMs.return_value = 1700000000000
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, 1700000000000)

    def test_binary_time(self):
        mock_iec = Mock()
        mock_iec.MMS_BINARY_TIME = 10
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_STRUCTURE = 1
        mock_iec.MMS_ARRAY = 0
        mock_iec.MMS_UTC_TIME = 14
        mock_iec.MmsValue_getType.return_value = 10
        mock_iec.MmsValue_getBinaryTimeAsUtcMs.return_value = 1700000000000
        result = self._call(mock_iec, Mock())
        self.assertEqual(result, 1700000000000)

    def test_data_access_error(self):
        mock_iec = Mock()
        mock_iec.MMS_DATA_ACCESS_ERROR = 15
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_STRUCTURE = 1
        mock_iec.MMS_ARRAY = 0
        mock_iec.MMS_UTC_TIME = 14
        mock_iec.MMS_BINARY_TIME = 10
        mock_iec.MmsValue_getType.return_value = 15
        result = self._call(mock_iec, Mock())
        self.assertIsNone(result)

    def test_array_recursive(self):
        """Arrays should be recursively converted."""
        mock_iec = Mock()
        mock_iec.MMS_ARRAY = 0
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_STRUCTURE = 1
        mock_iec.MMS_UTC_TIME = 14
        mock_iec.MMS_BINARY_TIME = 10
        mock_iec.MMS_DATA_ACCESS_ERROR = 15

        arr_val = Mock(name="array")
        elem0 = Mock(name="elem0")
        elem1 = Mock(name="elem1")

        # First call: array, then element calls: int, bool
        mock_iec.MmsValue_getType.side_effect = [0, 4, 2]
        mock_iec.MmsValue_getArraySize.return_value = 2
        mock_iec.MmsValue_getElement.side_effect = [elem0, elem1]
        mock_iec.MmsValue_toInt64.return_value = 99
        mock_iec.MmsValue_getBoolean.return_value = True

        result = self._call(mock_iec, arr_val)
        self.assertEqual(result, [99, True])

    def test_structure_recursive(self):
        """Structures should be recursively converted to dict."""
        mock_iec = Mock()
        mock_iec.MMS_STRUCTURE = 1
        mock_iec.MMS_BOOLEAN = 2
        mock_iec.MMS_INTEGER = 4
        mock_iec.MMS_UNSIGNED = 5
        mock_iec.MMS_FLOAT = 6
        mock_iec.MMS_VISIBLE_STRING = 8
        mock_iec.MMS_STRING = 13
        mock_iec.MMS_BIT_STRING = 3
        mock_iec.MMS_OCTET_STRING = 7
        mock_iec.MMS_ARRAY = 0
        mock_iec.MMS_UTC_TIME = 14
        mock_iec.MMS_BINARY_TIME = 10
        mock_iec.MMS_DATA_ACCESS_ERROR = 15

        struct_val = Mock(name="struct")
        field0 = Mock(name="field0")

        mock_iec.MmsValue_getType.side_effect = [1, 6]
        mock_iec.MmsValue_getArraySize.return_value = 1
        mock_iec.MmsValue_getElement.return_value = field0
        mock_iec.MmsValue_toFloat.return_value = 2.71

        result = self._call(mock_iec, struct_val)
        self.assertEqual(result, {0: 2.71})

    def test_library_not_found(self):
        """Should raise LibraryNotFoundError when library missing."""
        from pyiec61850.mms.exceptions import LibraryNotFoundError
        from pyiec61850.mms.utils import mms_value_to_python

        with patch("pyiec61850.mms.utils._HAS_IEC61850", False):
            with self.assertRaises(LibraryNotFoundError):
                mms_value_to_python(Mock())


class TestPythonToMmsValue(unittest.TestCase):
    """Test python_to_mms_value conversion function."""

    def _call(self, mock_iec, value):
        """Helper to call python_to_mms_value with mocked library."""
        with patch("pyiec61850.mms.utils._HAS_IEC61850", True):
            with patch("pyiec61850.mms.utils.iec61850", mock_iec):
                from pyiec61850.mms.utils import python_to_mms_value

                return python_to_mms_value(value)

    def test_bool_true(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newBoolean.return_value = "bool_handle"
        result = self._call(mock_iec, True)
        mock_iec.MmsValue_newBoolean.assert_called_once_with(True)
        self.assertEqual(result, "bool_handle")

    def test_bool_false(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newBoolean.return_value = "bool_handle"
        self._call(mock_iec, False)
        mock_iec.MmsValue_newBoolean.assert_called_once_with(False)

    def test_bool_before_int(self):
        """bool is subclass of int -- must create boolean, not integer."""
        mock_iec = Mock()
        mock_iec.MmsValue_newBoolean.return_value = "bool_handle"
        self._call(mock_iec, True)
        mock_iec.MmsValue_newBoolean.assert_called_once()
        mock_iec.MmsValue_newIntegerFromInt64.assert_not_called()

    def test_int(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newIntegerFromInt64.return_value = "int_handle"
        result = self._call(mock_iec, 42)
        mock_iec.MmsValue_newIntegerFromInt64.assert_called_once_with(42)
        self.assertEqual(result, "int_handle")

    def test_negative_int(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newIntegerFromInt64.return_value = "int_handle"
        self._call(mock_iec, -100)
        mock_iec.MmsValue_newIntegerFromInt64.assert_called_once_with(-100)

    def test_float(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newFloat.return_value = "float_handle"
        result = self._call(mock_iec, 3.14)
        mock_iec.MmsValue_newFloat.assert_called_once_with(3.14)
        self.assertEqual(result, "float_handle")

    def test_string(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newVisibleString.return_value = "str_handle"
        result = self._call(mock_iec, "hello")
        mock_iec.MmsValue_newVisibleString.assert_called_once_with("hello")
        self.assertEqual(result, "str_handle")

    def test_empty_string(self):
        mock_iec = Mock()
        mock_iec.MmsValue_newVisibleString.return_value = "str_handle"
        self._call(mock_iec, "")
        mock_iec.MmsValue_newVisibleString.assert_called_once_with("")

    def test_unsupported_type_raises_type_error(self):
        mock_iec = Mock()
        with self.assertRaises(TypeError) as ctx:
            self._call(mock_iec, [1, 2, 3])
        self.assertIn("list", str(ctx.exception))

    def test_unsupported_type_dict(self):
        mock_iec = Mock()
        with self.assertRaises(TypeError):
            self._call(mock_iec, {"key": "val"})

    def test_unsupported_type_bytes(self):
        mock_iec = Mock()
        with self.assertRaises(TypeError):
            self._call(mock_iec, b"\x00")

    def test_library_not_found(self):
        from pyiec61850.mms.exceptions import LibraryNotFoundError
        from pyiec61850.mms.utils import python_to_mms_value

        with patch("pyiec61850.mms.utils._HAS_IEC61850", False):
            with self.assertRaises(LibraryNotFoundError):
                python_to_mms_value(42)


if __name__ == "__main__":
    unittest.main()
