"""Shared unit-test support: a *faithful* fake of the pyiec61850 binding.

Why this exists
---------------
The unit tests mock the SWIG layer. Ad-hoc mocks let two whole classes of bug
pass unit tests while failing against the real binding (both happened — see the
``write_value`` / ``get_server_identity`` fixes):

1. **Phantom functions.** ``MagicMock`` invents any attribute, so a test for
   ``iec61850.IedConnection_identify`` (which does not exist in the binding)
   passes happily. :func:`make_binding` uses ``spec`` built from a snapshot of
   the *real* binding symbols (``_binding_symbols.txt``), so referencing a
   function the binding does not export raises ``AttributeError`` — in the test,
   where it belongs.

2. **Wrong return shapes.** The error-returning ``IedConnection_*`` calls return
   an ``(value, error)`` *tuple* in this binding, not a bare error code. A mock
   returning scalar ``0`` masks code that mishandles the tuple. :func:`make_binding`
   pre-seeds those functions with faithful tuple returns.

Constants (``IED_ERROR_*``, ``IEC61850_FC_*``, ``MMS_*``) carry their real
integer values so functional-constraint resolution and type dispatch behave as
they do against the binding.

The helpers also patch ``_libload.have_library`` so the wrappers'
``require_library()`` gate is satisfied without the native extension present —
i.e. these tests run on a plain source checkout — and register cleanup so a
mock connection is torn down while the fake is still installed (no GC hang).
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

_SYMBOLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_binding_symbols.txt")

# Real constant values, captured from the binding. Kept here (not read live)
# so the fake is faithful even on a checkout with no native extension.
_CONSTANTS = {
    "IED_ERROR_OK": 0,
    "IED_ERROR_NOT_CONNECTED": 1,
    "IED_ERROR_ALREADY_CONNECTED": 2,
    "IED_ERROR_CONNECTION_LOST": 3,
    "IED_ERROR_TIMEOUT": 20,
    "IED_ERROR_ACCESS_DENIED": 21,
    "IED_ERROR_OBJECT_DOES_NOT_EXIST": 22,
    "IED_ERROR_TYPE_INCONSISTENT": 25,
    "IED_ERROR_UNKNOWN": 99,
    # Functional constraints.
    "IEC61850_FC_ST": 0,
    "IEC61850_FC_MX": 1,
    "IEC61850_FC_SP": 2,
    "IEC61850_FC_SV": 3,
    "IEC61850_FC_CF": 4,
    "IEC61850_FC_DC": 5,
    "IEC61850_FC_SG": 6,
    "IEC61850_FC_SE": 7,
    "IEC61850_FC_SR": 8,
    "IEC61850_FC_OR": 9,
    "IEC61850_FC_BL": 10,
    "IEC61850_FC_EX": 11,
    "IEC61850_FC_CO": 12,
    "IEC61850_FC_US": 13,
    "IEC61850_FC_MS": 14,
    "IEC61850_FC_RP": 15,
    "IEC61850_FC_BR": 16,
    "IEC61850_FC_LG": 17,
    "IEC61850_FC_GO": 18,
    "IEC61850_FC_ALL": 99,
    "IEC61850_FC_NONE": -1,
    # MMS value types.
    "MMS_ARRAY": 0,
    "MMS_STRUCTURE": 1,
    "MMS_BOOLEAN": 2,
    "MMS_BIT_STRING": 3,
    "MMS_INTEGER": 4,
    "MMS_UNSIGNED": 5,
    "MMS_FLOAT": 6,
    "MMS_OCTET_STRING": 7,
    "MMS_VISIBLE_STRING": 8,
    "MMS_GENERALIZED_TIME": 9,
    "MMS_BINARY_TIME": 10,
    "MMS_BCD": 11,
    "MMS_OBJ_ID": 12,
    "MMS_STRING": 13,
    "MMS_UTC_TIME": 14,
    "MMS_DATA_ACCESS_ERROR": 15,
}

# Functions whose real return is an ``(value, error)`` tuple (the SWIG typemap
# turns the C ``IedClientError*`` out-parameter into the 2nd tuple element).
# Seeded with a success tuple so tests don't accidentally rely on a scalar.
_TUPLE_RETURN_OK = (
    "IedConnection_connect",
    "IedConnection_writeObject",
    "IedConnection_readObject",
    "IedConnection_getLogicalDeviceList",
    "IedConnection_getLogicalDeviceDirectory",
    "IedConnection_getServerDirectory",
    "IedConnection_getDataDirectory",
    "IedConnection_getDataDirectoryFC",
    "IedConnection_getDataSetDirectory",
)

_cached_symbols: frozenset[str] | None = None


def binding_symbols() -> frozenset[str]:
    """The set of public symbols the real binding exports (from the snapshot)."""
    global _cached_symbols
    if _cached_symbols is None:
        syms = set()
        with open(_SYMBOLS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    syms.add(line)
        _cached_symbols = frozenset(syms)
    return _cached_symbols


def make_binding(**overrides) -> MagicMock:
    """Return a MagicMock spec'd to the real binding's symbols.

    - Accessing a name the binding does not export raises ``AttributeError``.
    - Constants carry real integer values.
    - Tuple-returning ``IedConnection_*`` calls default to a success tuple
      ``(None, IED_ERROR_OK)`` so a scalar return cannot sneak in.

    ``overrides`` set ``return_value`` on named functions, e.g.
    ``make_binding(IedConnection_writeObject=(None, 25))``.
    """
    binding = MagicMock(spec=sorted(binding_symbols()))

    for name, value in _CONSTANTS.items():
        setattr(binding, name, value)

    ok = _CONSTANTS["IED_ERROR_OK"]
    for name in _TUPLE_RETURN_OK:
        getattr(binding, name).return_value = (None, ok)

    for name, return_value in overrides.items():
        getattr(binding, name).return_value = return_value

    return binding


# Wrapper modules whose ``iec61850`` / ``_HAS_IEC61850`` the default install
# patches. Pass ``modules=[...]`` to install_binding to cover others
# (e.g. "pyiec61850.goose.subscriber", "pyiec61850.mms.tls").
_DEFAULT_MODULES = ("pyiec61850.mms.client", "pyiec61850.mms.utils")


def install_binding(
    testcase,
    binding: MagicMock | None = None,
    modules=None,
    **overrides,
) -> MagicMock:
    """Patch wrapper modules to use a faithful fake binding for one test.

    For each module in ``modules`` (default: the MMS client + utils), patches
    ``<module>.iec61850`` to the fake and flips ``<module>._HAS_IEC61850`` True,
    and reports the library as present so ``require_library()`` is satisfied
    without the native extension. All patches are torn down via
    ``testcase.addCleanup``.
    """
    binding = binding if binding is not None else make_binding(**overrides)
    targets = [patch("pyiec61850._libload.have_library", return_value=True)]
    for mod in modules if modules is not None else _DEFAULT_MODULES:
        targets.append(patch(f"{mod}.iec61850", binding))
        targets.append(patch(f"{mod}._HAS_IEC61850", True))
    for p in targets:
        p.start()
        testcase.addCleanup(p.stop)
    return binding


def connected_client(testcase, **overrides):
    """Return ``(client, binding)`` for a connected MMSClient on the fake.

    Registers ``client.disconnect`` as a cleanup *after* the patch teardowns so
    it runs first (LIFO) — i.e. while the fake is still installed — leaving the
    client with no native handle before garbage collection.
    """
    from pyiec61850.mms import MMSClient

    binding = install_binding(testcase, **overrides)
    client = MMSClient()
    client.connect("host", 102)
    testcase.addCleanup(client.disconnect)
    return client, binding
