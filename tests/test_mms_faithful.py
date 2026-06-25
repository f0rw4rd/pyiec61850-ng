"""MMS client tests against a *faithful* fake binding (see tests/support.py).

These lock down the contract bugs that ad-hoc mocks let slip through:
 - Bug 1: write_value FC handling + (None, error) tuple return
 - Bug 2: get_server_identity must use MmsConnection_identify (the binding has
          no IedConnection_identify)
 - Bug 3: read_value must map MMS_DATA_ACCESS_ERROR to None

Every test here runs on a plain source checkout (no native extension): the
faithful fake supplies the binding and reports the library as present.
"""

import types
import unittest

from pyiec61850.mms.exceptions import WriteError

from .support import binding_symbols, connected_client, make_binding


class TestBindingContract(unittest.TestCase):
    """The fake mirrors the real binding's symbol surface and return shapes."""

    def test_iedconnection_identify_does_not_exist(self):
        """The binding exposes no IedConnection_identify (the Bug 2 trap)."""
        self.assertNotIn("IedConnection_identify", binding_symbols())
        self.assertIn("MmsConnection_identify", binding_symbols())
        self.assertIn("IedConnection_getMmsConnection", binding_symbols())

    def test_fake_rejects_phantom_function(self):
        """Referencing a non-existent binding function raises AttributeError."""
        binding = make_binding()
        with self.assertRaises(AttributeError):
            _ = binding.IedConnection_identify

    def test_write_object_default_return_is_a_tuple(self):
        """IedConnection_writeObject returns (value, error), not a scalar."""
        binding = make_binding()
        result = binding.IedConnection_writeObject(object(), "ref", 0, object())
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[1], binding.IED_ERROR_OK)


class TestWriteValueFaithful(unittest.TestCase):
    def test_write_under_explicit_fc_passes_fc_through(self):
        """write_value(fc='CO') must call writeObject under FC_CO, not FC_ST."""
        client, binding = connected_client(self)
        binding.IedConnection_writeObject.return_value = (None, binding.IED_ERROR_OK)

        self.assertTrue(client.write_value("LD/GGIO1.SPCSO1.Oper.ctlVal", True, fc="CO"))

        fc_arg = binding.IedConnection_writeObject.call_args[0][2]
        self.assertEqual(fc_arg, binding.IEC61850_FC_CO)

    def test_bracket_suffix_selects_fc(self):
        client, binding = connected_client(self)
        binding.IedConnection_writeObject.return_value = (None, binding.IED_ERROR_OK)

        client.write_value("LD/GGIO1.SPCSO1.Oper.ctlVal[CO]", True)

        fc_arg = binding.IedConnection_writeObject.call_args[0][2]
        self.assertEqual(fc_arg, binding.IEC61850_FC_CO)

    def test_success_tuple_returns_true(self):
        """(None, OK) must be read as success — not a spurious WriteError."""
        client, binding = connected_client(self)
        binding.IedConnection_writeObject.return_value = (None, binding.IED_ERROR_OK)
        self.assertTrue(client.write_value("LD/x.SPCSO1.stVal", True, fc="SP"))

    def test_error_tuple_raises_write_error(self):
        """(None, <error>) must raise — the scalar-mock bug would not catch this."""
        client, binding = connected_client(self)
        binding.IedConnection_writeObject.return_value = (None, binding.IED_ERROR_ACCESS_DENIED)
        with self.assertRaises(WriteError):
            client.write_value("LD/x.SPCSO1.stVal", True, fc="CO")


class TestGetServerIdentityFaithful(unittest.TestCase):
    def test_uses_mms_layer_identify(self):
        """get_server_identity must use MmsConnection_identify and populate fields.

        Against the buggy code (which called the non-existent
        IedConnection_identify) the spec'd fake raises AttributeError, the
        broad except swallows it, and the identity comes back empty — so this
        test fails, exactly as it should.
        """
        client, binding = connected_client(self)
        binding.MmsConnection_identify.return_value = types.SimpleNamespace(
            vendorName="MZ", modelName="basic io", revision="1.6.0"
        )

        identity = client.get_server_identity()

        self.assertEqual(identity.vendor, "MZ")
        self.assertEqual(identity.model, "basic io")
        self.assertEqual(identity.revision, "1.6.0")
        binding.MmsConnection_identify.assert_called_once()


class TestReadValueFaithful(unittest.TestCase):
    def test_data_access_error_maps_to_none(self):
        """A read that yields MMS_DATA_ACCESS_ERROR must return None, not a
        truthy placeholder (Bug 3)."""
        client, binding = connected_client(self)
        sentinel = object()
        binding.IedConnection_readObject.return_value = (sentinel, binding.IED_ERROR_OK)
        binding.MmsValue_getType.return_value = binding.MMS_DATA_ACCESS_ERROR

        self.assertIsNone(client.read_value("LD/GGIO1.AnIn1.mag.f", fc="ST"))

    def test_boolean_round_trips(self):
        client, binding = connected_client(self)
        sentinel = object()
        binding.IedConnection_readObject.return_value = (sentinel, binding.IED_ERROR_OK)
        binding.MmsValue_getType.return_value = binding.MMS_BOOLEAN
        binding.MmsValue_getBoolean.return_value = True

        self.assertIs(client.read_value("LD/GGIO1.SPCSO1.stVal"), True)


if __name__ == "__main__":
    unittest.main()
