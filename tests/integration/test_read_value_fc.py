"""
Integration test: read_value functional constraint handling.

``read_value`` now supports FC override via kwarg and ``[FC]`` suffix.
These tests pin down the behaviour against a real server.

Characterisation note: ``server_example_basic_io`` returns a value even
when the wrong FC is used. This is server-specific — real devices may
reject wrong-FC reads. The tests document the current reality so any
future change is a deliberate decision, not a surprise.
"""

from pyiec61850.mms import MMSClient, ReadError

from ._fixture import IntegrationServerCase, REF_MX_FLOAT, REF_ST_BOOL


class TestReadValueFC(IntegrationServerCase):
    def test_mx_attribute_with_explicit_fc_kwarg(self):
        value = self.client.read_value(REF_MX_FLOAT, fc="MX")
        self.assertIsInstance(value, (int, float))

    def test_mx_attribute_with_bracket_suffix(self):
        value = self.client.read_value(f"{REF_MX_FLOAT}[MX]")
        self.assertIsInstance(value, (int, float))

    def test_kwarg_and_suffix_return_same_value(self):
        """Both FC-specification forms must produce the same result."""
        via_kwarg = self.client.read_value(REF_MX_FLOAT, fc="MX")
        via_suffix = self.client.read_value(f"{REF_MX_FLOAT}[MX]")
        self.assertEqual(via_kwarg, via_suffix)

    def test_st_attribute_default_fc(self):
        """Status attributes read under the default FC (ST) must work."""
        value = self.client.read_value(REF_ST_BOOL)
        self.assertIsNotNone(value)

    def test_fc_string_is_case_insensitive(self):
        v_upper = self.client.read_value(REF_MX_FLOAT, fc="MX")
        v_lower = self.client.read_value(REF_MX_FLOAT, fc="mx")
        self.assertEqual(v_upper, v_lower)

    def test_invalid_fc_string_falls_back_to_st(self):
        """An unrecognised FC string like 'ZZ' silently falls back to
        FC_ST via getattr default. This is a characterisation test — the
        silent fallback is arguably a bug, but we pin the current
        behaviour so any change is intentional."""
        # Should not raise — falls back to ST.
        value = self.client.read_value(REF_ST_BOOL, fc="ZZ")
        # Compare with explicit ST read.
        value_st = self.client.read_value(REF_ST_BOOL, fc="ST")
        self.assertEqual(value, value_st)

    def test_wrong_fc_does_not_raise_on_basic_io_server(self):
        """Characterisation: the basic_io server returns a value when an
        MX attribute is read under FC_ST. We freeze this so any future
        server-side change is visible as a test failure."""
        value = self.client.read_value(REF_MX_FLOAT, fc="ST")
        self.assertIsNotNone(value)

    def test_bracket_suffix_is_stripped_from_reference(self):
        """After parsing [FC], the suffix must not be sent to the server.
        If it were, the server would reject the reference."""
        value = self.client.read_value(f"{REF_ST_BOOL}[ST]")
        value_plain = self.client.read_value(REF_ST_BOOL, fc="ST")
        self.assertEqual(value, value_plain)
