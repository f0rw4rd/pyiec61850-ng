import os
from setuptools import setup, find_packages
from setuptools.dist import Distribution

# Get version from environment or default
version = os.environ.get('PACKAGE_VERSION', '1.6.0.7')

# Read README
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

class BinaryDistribution(Distribution):
    """Mark this as a binary distribution."""
    def has_ext_modules(self):
        return True

setup(
    name="pyiec61850-ng",
    version=version,
    description="Python bindings for libiec61850 - IEC 61850 protocol implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="f0rw4rd",
    author_email="pyiec61850@example.com",
    url="https://github.com/f0rw4rd/pyiec61850-ng",
    packages=find_packages(),
    package_data={
        "pyiec61850": ["*.so", "*.py", "lib*.so*"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.8",
    keywords="iec61850 mms goose iec-61850 power-systems substation-automation smart-grid scada tase2 iccp iec60870-6",
    project_urls={
        "Bug Reports": "https://github.com/f0rw4rd/pyiec61850-ng/issues",
        "Source": "https://github.com/f0rw4rd/pyiec61850-ng",
        "Documentation": "https://github.com/f0rw4rd/pyiec61850-ng#readme",
    },
    license="GPLv3",
    distclass=BinaryDistribution,
)