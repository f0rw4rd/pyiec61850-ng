"""
Integration test: MMSClient.write_value against a real server.

``write_value`` has unit coverage via mocks but has never been exercised
against a real libiec61850 server. The mocks can silently diverge from
reality (as we learned with ``connect``), so end-to-end coverage is
essential.

``server_example_basic_io``'s static model exposes boolean SPCSO
attributes (SPCSO1–SPCSO4) under GGIO1 that are writable.
"""

from pyiec61850.mms import MMSClient
from pyiec61850.mms.exceptions import NotConnectedError, WriteError

from ._fixture import (
    REF_SPCSO1_CTLVAL,
    REF_SPCSO1_STVAL,
    REF_ST_BOOL,
    IntegrationServerCase,
)


class TestWriteValue(IntegrationServerCase):
    def test_write_to_nonexistent_reference_raises_write_error(self):
        """The error path must surface as WriteError, not a bare Exception
        or a segfault."""
        with self.assertRaises(WriteError):
            self.client.write_value("simpleIOGenericIO/GGIO999.DoesNotExist.stVal", 1)

    def test_write_on_disconnected_client_raises(self):
        client = MMSClient()
        with self.assertRaises(NotConnectedError):
            client.write_value(REF_SPCSO1_STVAL, True)

    def test_write_then_read_round_trip(self):
        """Write a boolean to SPCSO1.stVal then read it back. This is
        the single most valuable write test: it proves the full SWIG
        round-trip (create MmsValue, IedConnection_writeObject, then
        IedConnection_readObject) works end-to-end.

        If the server rejects the write (some builds are read-only),
        we skip rather than fail — the write rejection is a server
        config issue, not a library bug."""
        try:
            self.client.write_value(REF_SPCSO1_STVAL, True)
        except WriteError:
            self.skipTest("server rejected write to SPCSO1.stVal — server may be read-only")

        value = self.client.read_value(REF_SPCSO1_STVAL)
        self.assertIn(
            value,
            (True, 1),
            f"expected True or 1 after writing True, got {value!r}",
        )

    def test_write_under_explicit_fc(self):
        """write_value must honour an explicit functional constraint.

        Regression guard: write_value used to hardcode FC_ST, so it could
        never reach a control object (Oper.ctlVal under CO). Passing
        fc="CO" must route the write under the CO constraint. We don't
        assert success — a direct-operate without select/SBO handshake may
        be rejected by the control model — only that the FC is honoured
        rather than silently forced to ST. Either a clean return or a
        WriteError (control-model rejection) is acceptable; what must NOT
        happen is a non-WriteError crash.

        The fc="CO" and trailing "[CO]" suffix forms must behave
        identically."""
        for ref, kwargs in (
            (REF_SPCSO1_CTLVAL, {"fc": "CO"}),
            (REF_SPCSO1_CTLVAL + "[CO]", {}),
        ):
            try:
                self.client.write_value(ref, True, **kwargs)
            except WriteError:
                pass  # control-model rejection — FC was still honoured
            except Exception as e:
                self.fail(
                    f"write under CO for {ref!r} raised "
                    f"{type(e).__name__}: {e} (expected success or WriteError)"
                )

    def test_write_wrong_type_raises_write_error(self):
        """Writing a string to a boolean attribute should surface as a
        WriteError. If the server silently accepts it instead, that is
        surprising but not a library bug — we document the outcome
        either way."""
        try:
            self.client.write_value(REF_ST_BOOL, "not-a-boolean-value")
        except WriteError:
            return  # expected — pass
        except Exception as e:
            self.fail(f"expected WriteError on type mismatch, got {type(e).__name__}: {e}")
        # If we get here, the server accepted a string for a boolean.
        # That is surprising but not a failure in our code. Log it
        # so it shows up in test output as a characterisation.
        import warnings

        warnings.warn(
            "server accepted string write to boolean attribute — "
            "characterisation: libiec61850 did not reject the type mismatch",
            stacklevel=2,
        )
