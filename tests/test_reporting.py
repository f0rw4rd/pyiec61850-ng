#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.reporting module - Report Control Block client.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestReportingImports(unittest.TestCase):
    """Test reporting module imports."""

    def test_import_report_client(self):
        from pyiec61850.mms.reporting import ReportClient

        self.assertIsNotNone(ReportClient)

    def test_import_types(self):
        from pyiec61850.mms.reporting import RCBConfig, Report, ReportEntry

        self.assertIsNotNone(Report)
        self.assertIsNotNone(ReportEntry)
        self.assertIsNotNone(RCBConfig)

    def test_import_exceptions(self):
        from pyiec61850.mms.exceptions import MMSError
        from pyiec61850.mms.reporting import ReportConfigError, ReportError

        self.assertTrue(issubclass(ReportError, MMSError))
        self.assertTrue(issubclass(ReportConfigError, ReportError))

    def test_import_constants(self):
        from pyiec61850.mms.reporting import (
            TRG_OPT_DATA_CHANGED,
            TRG_OPT_GI,
        )

        self.assertEqual(TRG_OPT_DATA_CHANGED, 1)
        self.assertEqual(TRG_OPT_GI, 16)


class TestReport(unittest.TestCase):
    """Test Report dataclass."""

    def test_default_creation(self):
        from pyiec61850.mms.reporting import Report

        report = Report()
        self.assertEqual(report.rcb_reference, "")
        self.assertEqual(report.entries, [])
        self.assertEqual(report.seq_num, 0)

    def test_to_dict(self):
        from pyiec61850.mms.reporting import Report

        report = Report(rcb_reference="myLD/LLN0$BR$brcb01", seq_num=5)
        d = report.to_dict()
        self.assertEqual(d["rcb_reference"], "myLD/LLN0$BR$brcb01")
        self.assertEqual(d["seq_num"], 5)


class TestRCBConfig(unittest.TestCase):
    """Test RCBConfig dataclass."""

    def test_default_values(self):
        from pyiec61850.mms.reporting import RCBConfig

        cfg = RCBConfig()
        self.assertIsNone(cfg.rpt_id)
        self.assertIsNone(cfg.data_set)
        self.assertIsNone(cfg.rpt_ena)

    def test_to_dict(self):
        from pyiec61850.mms.reporting import RCBConfig

        cfg = RCBConfig(rpt_id="rpt01", data_set="ds01", rpt_ena=True)
        d = cfg.to_dict()
        self.assertEqual(d["rpt_id"], "rpt01")
        self.assertEqual(d["data_set"], "ds01")
        self.assertTrue(d["rpt_ena"])


class TestReportClient(unittest.TestCase):
    """Test ReportClient class."""

    def _make_mock_mms_client(self):
        client = Mock()
        client.is_connected = True
        client._connection = Mock()
        return client

    def test_raises_without_library(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", False):
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            from pyiec61850.mms.reporting import ReportClient

            with self.assertRaises(LibraryNotFoundError):
                ReportClient(Mock())

    def test_creation_success(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850"):
                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                self.assertFalse(reports.is_active)

    def test_get_rcb_values(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_rcb = Mock()
                mock_iec.IedConnection_getRCBValues.return_value = (mock_rcb, 0)
                mock_iec.ClientReportControlBlock_getRptId.return_value = "rpt01"
                mock_iec.ClientReportControlBlock_getDataSetName.return_value = "ds01"
                mock_iec.ClientReportControlBlock_getTrgOps.return_value = 5
                mock_iec.ClientReportControlBlock_getRptEna.return_value = True

                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                config = reports.get_rcb_values("myLD/LLN0$BR$brcb01")

                self.assertEqual(config.rpt_id, "rpt01")
                self.assertEqual(config.data_set, "ds01")
                self.assertTrue(config.rpt_ena)

    def test_get_rcb_values_not_connected(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850"):
                from pyiec61850.mms.exceptions import NotConnectedError
                from pyiec61850.mms.reporting import ReportClient

                client = Mock()
                client.is_connected = False
                reports = ReportClient(client)
                with self.assertRaises(NotConnectedError):
                    reports.get_rcb_values("test")

    def test_get_rcb_values_error(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_iec.IedConnection_getRCBValues.return_value = (None, 5)

                from pyiec61850.mms.exceptions import ReadError
                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                with self.assertRaises(ReadError):
                    reports.get_rcb_values("test")

    def test_enable_reporting(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_rcb = Mock()
                mock_iec.IedConnection_getRCBValues.return_value = (mock_rcb, 0)
                mock_iec.IedConnection_setRCBValues.return_value = 0

                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                reports.enable_reporting("myLD/LLN0$BR$brcb01")

                mock_iec.ClientReportControlBlock_setRptEna.assert_called()

    def test_disable_reporting(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_rcb = Mock()
                mock_iec.IedConnection_getRCBValues.return_value = (mock_rcb, 0)
                mock_iec.IedConnection_setRCBValues.return_value = 0

                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                reports.disable_reporting("myLD/LLN0$BR$brcb01")

                mock_iec.ClientReportControlBlock_setRptEna.assert_called_with(mock_rcb, False)

    def test_trigger_gi_report(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850") as mock_iec:
                mock_iec.IED_ERROR_OK = 0
                mock_rcb = Mock()
                mock_iec.IedConnection_getRCBValues.return_value = (mock_rcb, 0)
                mock_iec.IedConnection_setRCBValues.return_value = 0

                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                reports.trigger_gi_report("myLD/LLN0$BR$brcb01")

                mock_iec.ClientReportControlBlock_setGI.assert_called()

    def test_install_report_handler_not_callable(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850"):
                from pyiec61850.mms.reporting import ReportClient, ReportError

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                with self.assertRaises(ReportError):
                    reports.install_report_handler("test", "rpt01", "not_callable")

    def test_uninstall_report_handler(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850"):
                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                reports = ReportClient(client)
                reports._handlers["test"] = Mock()
                reports._callbacks["test"] = Mock()
                reports.uninstall_report_handler("test")
                self.assertNotIn("test", reports._handlers)
                self.assertNotIn("test", reports._callbacks)

    def test_context_manager(self):
        with patch("pyiec61850.mms.reporting._HAS_IEC61850", True):
            with patch("pyiec61850.mms.reporting.iec61850"):
                from pyiec61850.mms.reporting import ReportClient

                client = self._make_mock_mms_client()
                with ReportClient(client) as reports:
                    reports._handlers["test"] = Mock()
                # All handlers should be cleared after exit
                self.assertEqual(len(reports._handlers), 0)


class TestPyRCBHandlerDirectorInheritance(unittest.TestCase):
    """_PyRCBHandler must properly inherit from RCBHandler for SWIG director."""

    def test_base_class_is_dynamic(self):
        """_RCBHandlerBase must exist as module-level dynamic base class."""
        from pyiec61850.mms import reporting

        self.assertTrue(
            hasattr(reporting, "_RCBHandlerBase"),
            "_RCBHandlerBase not defined — handler won't inherit from RCBHandler",
        )

    def test_handler_uses_dynamic_base(self):
        """_PyRCBHandler must inherit from _RCBHandlerBase, not plain object."""
        from pyiec61850.mms.reporting import _PyRCBHandler, _RCBHandlerBase

        self.assertTrue(
            issubclass(_PyRCBHandler, _RCBHandlerBase),
            "_PyRCBHandler does not inherit from _RCBHandlerBase",
        )

    def test_handler_calls_super_init(self):
        """__init__ must call super().__init__(), not iec61850.X.__init__(self)."""
        import inspect

        from pyiec61850.mms.reporting import _PyRCBHandler

        source = inspect.getsource(_PyRCBHandler.__init__)
        self.assertIn("super().__init__", source)
        self.assertNotIn("RCBHandler.__init__(self)", source)


if __name__ == "__main__":
    unittest.main()
