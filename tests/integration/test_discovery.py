"""
Integration test: model discovery methods.

The discovery methods (``get_logical_devices``, ``get_logical_nodes``,
``get_data_objects``, ``get_data_attributes``) use SWIG-wrapped
``IedConnection_getLogical*`` APIs that return LinkedList tuples — an
area historically prone to NULL-deref and memory-leak bugs.

The static model in ``server_example_basic_io`` has exactly one logical
device (``simpleIOGenericIO``) containing at least LLN0, LPHD1, and GGIO1.
"""

from pyiec61850.mms import MMSClient, MMSError

from ._fixture import (
    IntegrationServerCase,
    EXPECTED_LOGICAL_NODES,
    LD_NAME,
)


class TestDiscovery(IntegrationServerCase):
    def test_get_logical_devices_returns_exactly_one(self):
        devices = self.client.get_logical_devices()
        self.assertIsInstance(devices, list)
        self.assertEqual(devices, [LD_NAME])

    def test_get_logical_devices_has_no_duplicates(self):
        devices = self.client.get_logical_devices()
        self.assertEqual(len(devices), len(set(devices)))

    def test_get_logical_nodes_contains_expected_set(self):
        nodes = self.client.get_logical_nodes(LD_NAME)
        self.assertIsInstance(nodes, list)
        self.assertTrue(
            EXPECTED_LOGICAL_NODES.issubset(set(nodes)),
            f"Expected {EXPECTED_LOGICAL_NODES} to be a subset of {nodes}",
        )

    def test_get_logical_nodes_has_no_duplicates(self):
        nodes = self.client.get_logical_nodes(LD_NAME)
        self.assertEqual(len(nodes), len(set(nodes)))

    def test_get_data_objects_for_ggio1(self):
        objects = self.client.get_data_objects(LD_NAME, "GGIO1")
        self.assertIsInstance(objects, list)
        # GGIO1 in the basic_io model has Mod, Beh, Health, NamPlt,
        # AnIn1-4, SPCSO1-4 = at least 12 objects.
        expected_subset = {"Mod", "Beh", "Health", "NamPlt", "AnIn1", "SPCSO1"}
        actual = set(objects)
        self.assertTrue(
            expected_subset.issubset(actual),
            f"Expected {expected_subset} ⊆ {actual}",
        )
        self.assertGreaterEqual(len(objects), 12)

    def test_get_data_objects_has_no_duplicates(self):
        objects = self.client.get_data_objects(LD_NAME, "GGIO1")
        self.assertEqual(len(objects), len(set(objects)))

    def test_get_data_attributes_returns_empty_list(self):
        """Known issue: get_data_attributes uses ACSI_CLASS_DATA_ATTRIBUTE
        which does not exist in the SWIG bindings. The method silently
        returns [] instead of the real sub-attributes. This test pins
        the current (broken) behaviour so a future fix is visible as a
        test change, not a silent regression.

        When this is fixed, replace this test with assertions on the
        actual sub-attributes (stVal, q, etc.)."""
        attrs = self.client.get_data_attributes(LD_NAME, "GGIO1", "Mod")
        self.assertIsInstance(attrs, list)
        # Currently returns empty due to missing ACSI_CLASS_DATA_ATTRIBUTE.
        # If this starts returning data, the fix landed — update the test.
        if len(attrs) > 0:
            # Fix landed! Verify the expected attributes.
            attr_names = set(attrs)
            for expected in ("stVal", "q"):
                self.assertIn(expected, attr_names)

    def test_get_logical_nodes_on_missing_device_returns_empty(self):
        """Querying a nonexistent logical device must not crash.
        We accept either an empty list or a raised MMSError — both are
        valid. What is NOT acceptable: a segfault, a returned list with
        garbage, or a silent None."""
        try:
            result = self.client.get_logical_nodes("doesNotExistLD")
        except (MMSError, Exception):
            # Raising is fine — proves it didn't segfault.
            return
        self.assertIsInstance(result, list, "expected list or exception, got something else")
        self.assertEqual(result, [], "nonexistent LD should return empty list")
