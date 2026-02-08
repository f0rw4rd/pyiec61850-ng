import os
import subprocess
import sys
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from version import get_version, get_libiec61850_version


class BuildExtInDocker(build_ext):
    """Build the extension inside Docker and extract the wheel."""

    def run(self):
        # Check if Docker is available
        try:
            subprocess.check_call(["docker", "--version"], stdout=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            print(
                "Docker is required to build this package. Please install Docker and try again."
            )
            sys.exit(1)

        # Define libiec61850 version (static, independent of git tags)
        libiec61850_version = get_libiec61850_version()

        # Build Docker image
        subprocess.check_call(
            [
                "docker",
                "build",
                "-t",
                "pyiec61850-builder",
                "--build-arg",
                f"LIBIEC61850_VERSION={libiec61850_version}",
                ".",
            ]
        )

        # Create container
        container_id = (
            subprocess.check_output(["docker", "create", "pyiec61850-builder"])
            .decode("utf-8")
            .strip()
        )

        try:
            # Create dist directory
            os.makedirs("dist", exist_ok=True)

            # Copy wheel from container
            subprocess.check_call(
                ["docker", "cp", f"{container_id}:/wheels/.", "dist/"]
            )

            # Find the wheel file
            wheel_file = None
            for file in os.listdir("dist"):
                if file.endswith(".whl"):
                    wheel_file = os.path.join("dist", file)
                    break

            if wheel_file:
                print(f"Built wheel: {wheel_file}")
                # No need to install the extensions as we've built the wheel
                self.extensions = []
            else:
                print("No wheel file found in the Docker container.")
                sys.exit(1)

        finally:
            # Remove container
            subprocess.check_call(["docker", "rm", container_id])


# Read long description from README
long_description = ""
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="pyiec61850-ng",
    version=get_version(),  # Auto-generated: libiec61850_version.build_number
    description="Python bindings for libiec61850 - IEC 61850 protocol implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="f0rw4rd",
    author_email="pyiec61850@example.com",
    url="https://github.com/f0rw4rd/pyiec61850-ng",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.9",
    cmdclass={
        "build_ext": BuildExtInDocker,
    },
    ext_modules=[
        Extension(name="dummy", sources=["dummy.c"]),
    ],
    package_data={
        "pyiec61850": ["*.so", "*.py", "lib*.so*", "*.pyd", "*.dll"],
        "pyiec61850._pyinstaller": ["*.py"],
    },
    entry_points={
        "pyinstaller40": [
            "hook-dirs = pyiec61850._pyinstaller:get_hook_dirs",
        ],
    },
    data_files=[("", ["LICENSE", "NOTICE"])],
    keywords="iec61850 mms goose iec-61850 power-systems substation-automation smart-grid scada",
    project_urls={
        "Bug Reports": "https://github.com/f0rw4rd/pyiec61850-ng/issues",
        "Source": "https://github.com/f0rw4rd/pyiec61850-ng",
        "Documentation": "https://github.com/f0rw4rd/pyiec61850-ng#readme",
    },
    license="GPLv3",
)
