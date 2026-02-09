#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.types module - MMS enum types.

All tests use hardcoded fallback values (no C library needed).
"""

import logging
import unittest
from enum import IntEnum

logging.disable(logging.CRITICAL)


class TestMmsTypeEnum(unittest.TestCase):
    """Test MmsType enum has correct values matching mms_common.h."""

    def test_import(self):
        from pyiec61850.mms.types import MmsType

        self.assertIsNotNone(MmsType)
        self.assertTrue(issubclass(MmsType, IntEnum))

    def test_values_match_header(self):
        """Values must match mms_common.h MmsType enum."""
        from pyiec61850.mms.types import MmsType

        self.assertEqual(MmsType.ARRAY, 0)
        self.assertEqual(MmsType.STRUCTURE, 1)
        self.assertEqual(MmsType.BOOLEAN, 2)
        self.assertEqual(MmsType.BIT_STRING, 3)
        self.assertEqual(MmsType.INTEGER, 4)
        self.assertEqual(MmsType.UNSIGNED, 5)
        self.assertEqual(MmsType.FLOAT, 6)
        self.assertEqual(MmsType.OCTET_STRING, 7)
        self.assertEqual(MmsType.VISIBLE_STRING, 8)
        self.assertEqual(MmsType.BINARY_TIME, 10)
        self.assertEqual(MmsType.STRING, 13)
        self.assertEqual(MmsType.UTC_TIME, 14)
        self.assertEqual(MmsType.DATA_ACCESS_ERROR, 15)

    def test_all_members_present(self):
        from pyiec61850.mms.types import MmsType

        expected = {
            "ARRAY",
            "STRUCTURE",
            "BOOLEAN",
            "BIT_STRING",
            "INTEGER",
            "UNSIGNED",
            "FLOAT",
            "OCTET_STRING",
            "VISIBLE_STRING",
            "BINARY_TIME",
            "STRING",
            "UTC_TIME",
            "DATA_ACCESS_ERROR",
        }
        self.assertEqual(set(MmsType.__members__.keys()), expected)

    def test_int_comparison(self):
        """Enum members should compare equal to their int values."""
        from pyiec61850.mms.types import MmsType

        self.assertEqual(MmsType.BOOLEAN, 2)
        self.assertTrue(MmsType.FLOAT == 6)

    def test_import_from_mms_package(self):
        from pyiec61850.mms import MmsType

        self.assertEqual(MmsType.BOOLEAN, 2)


class TestFCEnum(unittest.TestCase):
    """Test FC (Functional Constraint) enum."""

    def test_import(self):
        from pyiec61850.mms.types import FC

        self.assertIsNotNone(FC)
        self.assertTrue(issubclass(FC, IntEnum))

    def test_values_match_header(self):
        """Values must match iec61850_common.h FunctionalConstraint enum."""
        from pyiec61850.mms.types import FC

        self.assertEqual(FC.ST, 0)
        self.assertEqual(FC.MX, 1)
        self.assertEqual(FC.SP, 2)
        self.assertEqual(FC.SV, 3)
        self.assertEqual(FC.CF, 4)
        self.assertEqual(FC.DC, 5)
        self.assertEqual(FC.SG, 6)
        self.assertEqual(FC.SE, 7)
        self.assertEqual(FC.SR, 8)
        self.assertEqual(FC.OR, 9)
        self.assertEqual(FC.BL, 10)
        self.assertEqual(FC.EX, 11)
        self.assertEqual(FC.CO, 12)
        self.assertEqual(FC.US, 13)
        self.assertEqual(FC.MS, 14)
        self.assertEqual(FC.RP, 15)
        self.assertEqual(FC.BR, 16)
        self.assertEqual(FC.LG, 17)
        self.assertEqual(FC.GO, 18)

    def test_all_members_present(self):
        from pyiec61850.mms.types import FC

        expected = {
            "ST",
            "MX",
            "SP",
            "SV",
            "CF",
            "DC",
            "SG",
            "SE",
            "SR",
            "OR",
            "BL",
            "EX",
            "CO",
            "US",
            "MS",
            "RP",
            "BR",
            "LG",
            "GO",
        }
        self.assertEqual(set(FC.__members__.keys()), expected)

    def test_import_from_mms_package(self):
        from pyiec61850.mms import FC

        self.assertEqual(FC.ST, 0)
        self.assertEqual(FC.CO, 12)


class TestACSIClassEnum(unittest.TestCase):
    """Test ACSIClass enum."""

    def test_import(self):
        from pyiec61850.mms.types import ACSIClass

        self.assertIsNotNone(ACSIClass)
        self.assertTrue(issubclass(ACSIClass, IntEnum))

    def test_values_match_header(self):
        """Values must match iec61850_common.h ACSIClass enum."""
        from pyiec61850.mms.types import ACSIClass

        self.assertEqual(ACSIClass.DATA_OBJECT, 0)
        self.assertEqual(ACSIClass.DATA_SET, 1)
        self.assertEqual(ACSIClass.BRCB, 2)
        self.assertEqual(ACSIClass.URCB, 3)
        self.assertEqual(ACSIClass.LCB, 4)
        self.assertEqual(ACSIClass.LOG, 5)
        self.assertEqual(ACSIClass.SGCB, 6)
        self.assertEqual(ACSIClass.GoCB, 7)
        self.assertEqual(ACSIClass.GsCB, 8)
        self.assertEqual(ACSIClass.MSVCB, 9)
        self.assertEqual(ACSIClass.USVCB, 10)

    def test_all_members_present(self):
        from pyiec61850.mms.types import ACSIClass

        expected = {
            "DATA_OBJECT",
            "DATA_SET",
            "BRCB",
            "URCB",
            "LCB",
            "LOG",
            "SGCB",
            "GoCB",
            "GsCB",
            "MSVCB",
            "USVCB",
        }
        self.assertEqual(set(ACSIClass.__members__.keys()), expected)

    def test_import_from_mms_package(self):
        from pyiec61850.mms import ACSIClass

        self.assertEqual(ACSIClass.GoCB, 7)


class TestEnumUsability(unittest.TestCase):
    """Test that enums work correctly as IntEnum values."""

    def test_mms_type_in_dict_key(self):
        from pyiec61850.mms.types import MmsType

        d = {MmsType.BOOLEAN: "bool", MmsType.INTEGER: "int"}
        self.assertEqual(d[2], "bool")
        self.assertEqual(d[MmsType.BOOLEAN], "bool")

    def test_fc_as_function_arg(self):
        """FC values should be usable as integer arguments."""
        from pyiec61850.mms.types import FC

        self.assertIsInstance(FC.ST, int)
        self.assertIsInstance(FC.CO + 1, int)

    def test_acsi_class_iteration(self):
        """Should be able to iterate over enum members."""
        from pyiec61850.mms.types import ACSIClass

        members = list(ACSIClass)
        self.assertEqual(len(members), 11)
        self.assertIn(ACSIClass.GoCB, members)


if __name__ == "__main__":
    unittest.main()
