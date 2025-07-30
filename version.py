#!/usr/bin/env python3
"""
Version management for pyiec61850-ng.

Format: LIBIEC61850_VERSION.REVISION
- LIBIEC61850_VERSION: The exact libiec61850 version we build against (1.6.0)
- REVISION: Our package revision for that libiec61850 version

Example: 1.6.0.1 (libiec61850 v1.6.0, first package revision)
"""

import subprocess
import os
import sys

# Fallback version configuration (used when no git tag available)
LIBIEC61850_VERSION = "1.6.0"  # Static libiec61850 version we build against
PACKAGE_REVISION = 5           # Our package revision - increment for bug fixes, rebuilds, etc.

def get_git_tag_version():
    """Extract version from git tag if available."""
    try:
        # Get the current git tag
        result = subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL
        )
        tag = result.decode().strip()
        
        # Remove 'v' prefix if present (v1.6.0.2 -> 1.6.0.2)
        if tag.startswith('v'):
            return tag[1:]
        return tag
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None

def get_version():
    """Generate the package version string: libiec61850_version.revision"""
    # Try to get version from git tag first
    git_version = get_git_tag_version()
    if git_version:
        return git_version
    
    # Fallback to hardcoded version
    return f"{LIBIEC61850_VERSION}.{PACKAGE_REVISION}"

def get_libiec61850_version():
    """Get the libiec61850 version (for Docker build arg)."""
    return f"v{LIBIEC61850_VERSION}"

def get_libiec61850_version_string():
    """Get the libiec61850 version as string (for descriptions)."""
    return LIBIEC61850_VERSION

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--libiec61850":
            print(get_libiec61850_version())
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python version.py              # Package version (1.6.0.1)")  
            print("  python version.py --libiec61850 # libiec61850 version (v1.6.0)")
            print("")
            print("To release a new version:")
            print("  1. For libiec61850 upgrade: Update LIBIEC61850_VERSION")
            print("  2. For package fixes/rebuilds: Increment PACKAGE_REVISION")
        else:
            print("Unknown option. Use --help for usage.")
    else:
        print(get_version())