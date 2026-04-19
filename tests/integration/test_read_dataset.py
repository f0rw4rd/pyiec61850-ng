"""
Integration test: MMSClient.read_dataset against a real server.

Regression coverage for two bugs surfaced during discussion #13:

1. The SWIG typemap ``%typemap(check) ClientDataSet`` rejects NULL,
   which is the "allocate for me" sentinel that
   ``IedConnection_readDataSetValues`` needs. ``read_dataset`` works
   around this by calling ``MmsConnection_readNamedVariableListValues``.

2. Dataset references in dot form (``LLN0.Events``) must be normalised
   to dollar form (``LLN0$Events``) before hitting the MMS layer.

The ``server_example_basic_io`` static datasets:
    simpleIOGenericIO/LLN0$Events          — 4 members, mixed types
    simpleIOGenericIO/LLN0$Measurements    — 4 members, mostly floats
"""

from pyiec61850.mms import ReadError

from ._fixture import (
    IntegrationServerCase,
    DATASET_EVENTS,
    DATASET_EVENTS_SIZE,
    DATASET_MEASUREMENTS,
    DATASET_MEASUREMENTS_SIZE,
)


class TestReadDataset(IntegrationServerCase):
    def test_read_events_dataset_returns_correct_count(self):
        values = self.client.read_dataset(DATASET_EVENTS)
        self.assertIsInstance(values, list)
        self.assertEqual(len(values), DATASET_EVENTS_SIZE)

    def test_read_measurements_dataset_returns_correct_count(self):
        values = self.client.read_dataset(DATASET_MEASUREMENTS)
        self.assertIsInstance(values, list)
        self.assertEqual(len(values), DATASET_MEASUREMENTS_SIZE)

    def test_measurements_contain_numeric_values(self):
        """Measurement members are analog floats — verify types."""
        values = self.client.read_dataset(DATASET_MEASUREMENTS)
        non_none = [v for v in values if v is not None]
        self.assertGreater(len(non_none), 0, "all measurement values were None")
        for v in non_none:
            # mms_value_to_python can return dicts for structures;
            # the leaf values inside are numeric.
            if isinstance(v, dict):
                continue
            self.assertIsInstance(
                v, (int, float),
                f"expected numeric, got {type(v).__name__}: {v!r}",
            )

    def test_dot_and_dollar_forms_return_same_data(self):
        dot = self.client.read_dataset("simpleIOGenericIO/LLN0.Events")
        dollar = self.client.read_dataset("simpleIOGenericIO/LLN0$Events")
        self.assertEqual(len(dot), len(dollar))
        # Same dataset — values must be identical.
        self.assertEqual(dot, dollar)

    def test_read_nonexistent_dataset_raises_read_error(self):
        with self.assertRaises(ReadError):
            self.client.read_dataset("simpleIOGenericIO/LLN0.DoesNotExist")

    def test_malformed_reference_raises_read_error(self):
        with self.assertRaises(ReadError):
            self.client.read_dataset("no-slash-here")

    def test_empty_domain_raises_read_error(self):
        with self.assertRaises(ReadError):
            self.client.read_dataset("/LLN0.Events")

    def test_repeated_reads_do_not_crash(self):
        """Stress test: repeated reads on the same connection must not
        crash from double-free or leaked MmsValue pointers. This is a
        crash detector, not a leak detector — true leak detection would
        require RSS measurement over thousands of iterations."""
        for _ in range(100):
            values = self.client.read_dataset(DATASET_EVENTS)
            self.assertEqual(len(values), DATASET_EVENTS_SIZE)
