#!/usr/bin/env python3
"""Fail-fast auditor for built pyiec61850-ng Linux wheels.

Guards against the packaging regressions behind issue #15:

  * a generic ``py3-none``/``linux_x86_64``/``manylinux1`` tag on a wheel that
    actually contains a version-specific CPython extension (pip would install it
    on the wrong interpreter/glibc -> segfault or load failure);
  * an extension module without its ``.cpython-3XX`` ABI suffix (CPython would
    load it under any version);
  * a leftover ``/build`` RPATH instead of a relocatable ``$ORIGIN`` one;
  * the native ``libiec61850`` not vendored into ``*.libs/``.

Usage:  python scripts/check_wheel.py dist/*.whl
Exits non-zero (with a report) if any wheel fails a check.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

EXT_RE = re.compile(r"pyiec61850/_pyiec61850\.cpython-3\d+-[^/]+\.so$")
BARE_EXT_RE = re.compile(r"pyiec61850/_pyiec61850\.so$")
LIBDIR_RE = re.compile(r"^pyiec61850_ng\.libs/libiec61850.*\.so")


def _readelf_dynamic(data: bytes) -> str:
    """Return `readelf -d` output for an ELF blob (readelf needs a seekable file)."""
    with tempfile.NamedTemporaryFile(suffix=".so") as tmp:
        tmp.write(data)
        tmp.flush()
        proc = subprocess.run(
            ["readelf", "-d", tmp.name],
            capture_output=True,
        )
    return proc.stdout.decode("utf-8", "replace")


def check_wheel(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.name

    # 1. Filename tag: must be cpXY-cpXY-manylinux_*, never py3/none/linux/manylinux1.
    if "-py3-none-" in name or "-none-" in name:
        errors.append(f"abi tag is generic (py3/none): {name}")
    if "linux_x86_64.whl" in name and "manylinux" not in name:
        errors.append(f"platform tag is bare linux_x86_64 (not manylinux): {name}")
    if "manylinux1_" in name:
        errors.append(f"platform tag is dishonest manylinux1 (glibc 2.5): {name}")
    if "manylinux" not in name:
        errors.append(f"no manylinux platform tag: {name}")
    if not re.search(r"-cp3\d+-cp3\d+-", name):
        errors.append(f"missing version-specific cpXY-cpXY tag: {name}")

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()

        # 2. Extension module must carry its ABI suffix; the bare name is a trap.
        ext = [n for n in names if EXT_RE.search(n)]
        bare = [n for n in names if BARE_EXT_RE.search(n)]
        if bare:
            errors.append(f"bare _pyiec61850.so present (loads on any Python): {bare}")
        if not ext:
            errors.append("no ABI-suffixed _pyiec61850.cpython-3XX-*.so found")

        # 3. RPATH of the extension must be $ORIGIN-relative, never /build/...
        for n in ext:
            elf = _readelf_dynamic(zf.read(n))
            paths = re.findall(r"\((?:RPATH|RUNPATH)\)\s+Library r(?:un)?path:\s+\[([^\]]*)\]", elf)
            joined = ";".join(paths)
            if "/build" in joined:
                errors.append(f"{n}: leftover build RPATH: {joined!r}")
            if "$ORIGIN" not in joined:
                errors.append(f"{n}: no $ORIGIN RPATH (got {joined!r})")

        # 4. Native libiec61850 must be vendored into *.libs/ by auditwheel.
        if not any(LIBDIR_RE.search(n) for n in names):
            errors.append("libiec61850 not vendored into pyiec61850_ng.libs/")

    return errors


def main(argv: list[str]) -> int:
    wheels = [Path(p) for p in argv[1:]]
    if not wheels:
        print("usage: check_wheel.py <wheel> [wheel ...]", file=sys.stderr)
        return 2

    failed = False
    for whl in wheels:
        errs = check_wheel(whl)
        if errs:
            failed = True
            print(f"FAIL {whl.name}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"ok   {whl.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
