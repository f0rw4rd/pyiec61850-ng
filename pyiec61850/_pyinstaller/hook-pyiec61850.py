"""PyInstaller hook for pyiec61850.

Collects all binary extensions (.pyd, .dll, .so), pure-Python submodules,
and data files needed to run pyiec61850 in a frozen executable.

The package's own __init__.py handles DLL loading at runtime, so no
runtime hook is needed for the common case.  If you encounter DLL loading
issues in a frozen build, add the companion runtime hook manually::

    a = Analysis(
        ...
        runtime_hooks=['path/to/pyi_rth_pyiec61850.py'],
    )
"""

import glob
import os

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    get_package_paths,
)

# ---------------------------------------------------------------------------
# Hidden imports: all submodules that may not be discovered by static analysis
# because of try/except ImportError guards or lazy imports.
# ---------------------------------------------------------------------------
hiddenimports = collect_submodules("pyiec61850")

# ---------------------------------------------------------------------------
# Binary extensions and shared libraries
# ---------------------------------------------------------------------------
binaries = collect_dynamic_libs("pyiec61850")

# Also explicitly grab .dll / .pyd files that collect_dynamic_libs may miss
# (it sometimes skips files that aren't named according to standard patterns).
_, pkg_dir = get_package_paths("pyiec61850")

for pattern in ("*.dll", "*.pyd", "*.so", "*.so.*"):
    for fpath in glob.glob(os.path.join(pkg_dir, pattern)):
        dest = os.path.join("pyiec61850", "")
        entry = (fpath, dest)
        if entry not in binaries:
            binaries.append(entry)

# ---------------------------------------------------------------------------
# Data files: .py source files that the SWIG wrapper loads at runtime,
# plus any other data shipped with the package.
# ---------------------------------------------------------------------------
datas = collect_data_files("pyiec61850", include_py_files=True)
