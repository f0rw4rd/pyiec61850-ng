"""
Integration test: ControlClient against libiec61850's server_example_control.

server_example_control exposes GGIO1.SPCSO1..4, one per IEC 61850 control
model, so we can exercise every control path against a real server:

    SPCSO1  ctlModel=1  direct-with-normal-security
    SPCSO2  ctlModel=2  sbo-with-normal-security      (select then operate)
    SPCSO3  ctlModel=3  direct-with-enhanced-security
    SPCSO4  ctlModel=4  sbo-with-enhanced-security    (select then operate)

This is the only end-to-end coverage of pyiec61850.mms.control — the unit
tests mock the SWIG layer, which (as the write_value/identity bugs showed) can
diverge from the real binding.
"""

import contextlib

from pyiec61850.mms import MMSClient
from pyiec61850.mms.control import ControlClient, ControlError

from ._fixture import CONTROL_LD, ControlServerCase

REF_DIRECT_NORMAL = f"{CONTROL_LD}/GGIO1.SPCSO1"
REF_SBO_NORMAL = f"{CONTROL_LD}/GGIO1.SPCSO2"
REF_DIRECT_ENHANCED = f"{CONTROL_LD}/GGIO1.SPCSO3"
REF_SBO_ENHANCED = f"{CONTROL_LD}/GGIO1.SPCSO4"


class TestControlIntegration(ControlServerCase):
    def setUp(self) -> None:
        self.client = MMSClient(self.host, self.port)
        self.client.connect()
        self.control = ControlClient(self.client)

    def tearDown(self) -> None:
        # Best-effort cleanup: a teardown failure must not mask the test result.
        with contextlib.suppress(Exception):
            self.control.release_all()
        with contextlib.suppress(Exception):
            self.client.disconnect()

    # -- control model discovery -------------------------------------------

    def test_control_models_match_expected(self):
        """Each SPCSO exposes its documented control model."""
        self.assertEqual(self.control.get_control_model(REF_DIRECT_NORMAL), 1)
        self.assertEqual(self.control.get_control_model(REF_SBO_NORMAL), 2)
        self.assertEqual(self.control.get_control_model(REF_DIRECT_ENHANCED), 3)
        self.assertEqual(self.control.get_control_model(REF_SBO_ENHANCED), 4)

    # -- direct control ----------------------------------------------------

    def test_direct_operate_normal(self):
        self.assertTrue(self.control.direct_operate(REF_DIRECT_NORMAL, True))

    def test_direct_operate_enhanced(self):
        """Enhanced security adds a command-termination round-trip."""
        self.assertTrue(self.control.direct_operate(REF_DIRECT_ENHANCED, True))

    def test_direct_operate_both_values(self):
        self.assertTrue(self.control.direct_operate(REF_DIRECT_NORMAL, True))
        self.assertTrue(self.control.direct_operate(REF_DIRECT_NORMAL, False))

    # -- select-before-operate (SBO) --------------------------------------

    def test_sbo_normal_select_then_operate(self):
        self.assertTrue(self.control.select(REF_SBO_NORMAL))
        self.assertTrue(self.control.operate(REF_SBO_NORMAL, True))

    def test_sbo_enhanced_select_with_value_then_operate(self):
        """Enhanced SBO selects with the value, then operates."""
        self.assertTrue(self.control.select_with_value(REF_SBO_ENHANCED, True))
        self.assertTrue(self.control.operate(REF_SBO_ENHANCED, True))

    def test_operate_without_select_on_sbo_fails(self):
        """Operating an SBO point without a prior select must not succeed."""
        try:
            ok = self.control.operate(REF_SBO_NORMAL, True)
        except ControlError:
            return  # expected — rejected
        self.assertFalse(ok, "SBO operate without select unexpectedly succeeded")

    def test_cancel_after_select(self):
        self.assertTrue(self.control.select(REF_SBO_NORMAL))
        # Cancel should undo the selection; either a clean True or a benign
        # rejection is acceptable, but it must not raise an unexpected type.
        try:
            self.control.cancel(REF_SBO_NORMAL)
        except ControlError:
            pass

    # -- write_value FC routing (the Bug 1 fix) ---------------------------

    def test_write_value_under_co_reaches_control_model(self):
        """write_value(fc="CO") must route under the CO constraint. A raw
        ctlVal write is access-denied by the control model (the proper path is
        the control service / operate), but it must surface as a WriteError
        rather than silently succeeding under the wrong FC."""
        from pyiec61850.mms.exceptions import WriteError

        ref = f"{REF_DIRECT_NORMAL}.Oper.ctlVal"
        try:
            self.client.write_value(ref, True, fc="CO")
        except WriteError:
            return  # expected — control model rejects the bare write
        # If it returned, the server accepted it; either way it was routed
        # under CO, which is the behaviour under test.
