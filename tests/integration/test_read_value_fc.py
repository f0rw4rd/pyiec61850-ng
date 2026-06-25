"""
Integration test: read_value functional constraint handling.

``read_value`` now supports FC override via kwarg and ``[FC]`` suffix.
These tests pin down the behaviour against a real server.

Characterisation note: ``server_example_basic_io`` answers a wrong-FC
read (an MX attribute read under FC_ST) with an MMS data-access-error
rather than a value. ``read_value`` maps that to ``None`` (via
``mms_value_to_python``) instead of raising, so callers can detect the
failed read by ``is None``. The tests document the current reality so
any future change is a deliberate decision, not a surprise.
"""

from ._fixture import REF_MX_FLOAT, REF_ST_BOOL, IntegrationServerCase


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
        """Characterisation: reading an MX attribute under the wrong FC (ST)
        does not raise — the basic_io server answers with an MMS
        data-access-error, which read_value maps to None (Bug 3 fix: the
        old converter masked this as a truthy "<MmsValue type=15>"
        placeholder). We freeze this so any future change is visible."""
        value = self.client.read_value(REF_MX_FLOAT, fc="ST")
        self.assertIsNone(value)

    def test_bracket_suffix_is_stripped_from_reference(self):
        """After parsing [FC], the suffix must not be sent to the server.
        If it were, the server would reject the reference."""
        value = self.client.read_value(f"{REF_ST_BOOL}[ST]")
        value_plain = self.client.read_value(REF_ST_BOOL, fc="ST")
        self.assertEqual(value, value_plain)
