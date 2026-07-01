"""Static contract check: wrappers must not call binding functions that do not
exist.

The Python wrappers under ``pyiec61850/`` call into the SWIG binding via a local
alias (``import pyiec61850.pyiec61850 as iec61850``). If a wrapper references a
function the binding does not export, it fails at runtime with ``AttributeError``
— usually swallowed by a broad ``except`` or invisible until a real call. This
is the bug class behind issue #20, the dead SV module, the GOOSE subscriber
value bug, and the TLS cert path.

This test enumerates every ``<alias>.Name`` attribute access in the wrappers
(AST, alias-scoped — so it is not fooled by the dotted import path) and asserts
the set is a subset of the real binding symbols snapshot
(``tests/_binding_symbols.txt``), minus names that are ``hasattr``-guarded in the
same module and minus an explicit, justified allowlist.

It runs WITHOUT the native extension (it reads the snapshot; it never imports
``pyiec61850.pyiec61850``). Regenerate the snapshot from a freshly built wheel:

    python -c "import pyiec61850.pyiec61850 as p; \
        print('\\n'.join(sorted(n for n in dir(p) if not n.startswith('__'))))" \
        > tests/_binding_symbols.txt

and bump ``version.py`` PACKAGE_REVISION whenever the snapshot changes (the
native ABI changed).
"""

from __future__ import annotations

import ast
import os
import unittest

from .support import binding_symbols

_PKG_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyiec61850")
_BINDING_MODULE = "pyiec61850.pyiec61850"

# Names the wrappers reference that are NOT in the binding but are KNOWN and
# accepted, each with a one-line justification. Remove an entry once the
# underlying gap is fixed (e.g. SV symbols appear once SV is wrapped).
_SV_REASON = (
    "SV L2 API not wrapped in patches/iec61850.i yet; enabled + subscriber "
    "refactored to the callback/ASDU model in a follow-up (see plan Phase 4)."
)
_TLS_REASON = (
    "TLS cert/key configuration needs a libiec61850 build with TLS support; "
    "guarded at runtime by hasattr(iec61850, 'TLSConfiguration_create'). "
    "Unsupported in the shipped build."
)
KNOWN_OPTIONAL: dict[str, str] = dict.fromkeys(
    (
        "SVPublisher_create",
        "SVPublisher_addASDU",
        "SVPublisher_ASDU_addINT32",
        "SVPublisher_ASDU_setSmpCntWrap",
        "SVPublisher_setupComplete",
        "SVPublisher_ASDU_setINT32",
        "SVPublisher_ASDU_setSmpCnt",
        "SVPublisher_publish",
        "SVPublisher_destroy",
        "SVReceiver_create",
        "SVReceiver_setInterfaceId",
        "SVSubscriber_create",
        "SVReceiver_addSubscriber",
        "SVReceiver_start",
        "SVReceiver_isRunning",
        "SVSubscriber_getSmpCnt",
        "SVSubscriber_getConfRev",
        "SVSubscriber_getSmpSynch",
        "SVSubscriber_getASDU",
        "SVClientASDU_getINT32",
        "SVReceiver_stop",
        "SVReceiver_destroy",
    ),
    _SV_REASON,
)
KNOWN_OPTIONAL.update(
    dict.fromkeys(
        (
            "TLSConfiguration_setOwnCertificateFromFile",
            "TLSConfiguration_setOwnKeyFromFile",
            "TLSConfiguration_addCACertificateFromFile",
            "TLSConfiguration_setChainValidation",
            "TLSConfiguration_setAllowOnlyKnownCertificates",
        ),
        _TLS_REASON,
    )
)


def _iter_wrapper_files():
    for dirpath, _dirs, files in os.walk(_PKG_ROOT):
        if os.sep + "_pyinstaller" in dirpath:
            continue
        for fname in files:
            if not fname.endswith(".py"):
                continue
            # The generated SWIG shim itself is not a wrapper.
            if fname == "pyiec61850.py":
                continue
            yield os.path.join(dirpath, fname)


def _binding_aliases(tree: ast.AST) -> set[str]:
    """Local names bound to the SWIG binding module in this file."""
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == _BINDING_MODULE and a.asname:
                    aliases.add(a.asname)
    return aliases


def _references_and_guards(tree: ast.AST, aliases: set[str]):
    """Return (references, guarded) for one file.

    references: list of (name, lineno) for every ``<alias>.name`` attribute
    access. guarded: set of names X protected by ``hasattr(<alias>, "X")``.
    """
    references = []
    guarded: set[str] = set()
    for node in ast.walk(tree):
        # <alias>.Name
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in aliases
        ):
            references.append((node.attr, node.lineno))
        # hasattr(<alias>, "Name")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in aliases
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            guarded.add(node.args[1].value)
    return references, guarded


class TestBindingContract(unittest.TestCase):
    def test_wrappers_only_call_existing_binding_functions(self):
        symbols = binding_symbols()
        phantoms = []  # (relpath, lineno, name)

        for path in _iter_wrapper_files():
            with open(path) as f:
                tree = ast.parse(f.read(), filename=path)
            aliases = _binding_aliases(tree)
            if not aliases:
                continue
            references, guarded = _references_and_guards(tree, aliases)
            for name, lineno in references:
                if name in symbols or name in guarded or name in KNOWN_OPTIONAL:
                    continue
                rel = os.path.relpath(path, os.path.dirname(_PKG_ROOT))
                phantoms.append((rel, lineno, name))

        if phantoms:
            lines = "\n".join(f"  {p}:{ln} -> iec61850.{n}" for p, ln, n in sorted(phantoms))
            self.fail(
                f"{len(phantoms)} wrapper call(s) reference binding functions that do "
                f"not exist in tests/_binding_symbols.txt.\nEither fix the call to a "
                f"real symbol, guard it with hasattr(iec61850, ...), or add it to "
                f"KNOWN_OPTIONAL with a justification:\n{lines}"
            )


if __name__ == "__main__":
    unittest.main()
