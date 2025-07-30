FROM python:3.11-slim-bookworm AS builder

# Set libiec61850 version as a build argument with default value
ARG LIBIEC61850_VERSION=v1.6

# Install build dependencies with retry logic for network issues
RUN apt-get update && \
    for i in 1 2 3; do \
        apt-get install -y --fix-missing --no-install-recommends \
            git \
            build-essential \
            cmake \
            swig \
            python3-dev \
            python3-setuptools \
            python3-wheel \
            python3-pip \
            wget tar \
        && break || { echo "Attempt $i failed, retrying in 10s..."; sleep 10; }; \
    done && \
    rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Clone libiec61850 with specified version
RUN echo "Building libiec61850 version: $LIBIEC61850_VERSION" && \
    git clone --depth 1 --branch $LIBIEC61850_VERSION https://github.com/mz-automation/libiec61850.git

# Download mbedTLS directly
RUN cd libiec61850/third_party/mbedtls && \
    wget https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v3.6.0.tar.gz --no-check-certificate && \
    tar -xzf v3.6.0.tar.gz

# Copy patch files
COPY patches/ /build/patches/

# Apply patches
RUN cd /build/libiec61850 && \
    if [ -f /build/patches/iec61850.i.patch ]; then \
        # Find the actual path to the iec61850.i file
        IEC_FILE=$(find . -name "iec61850.i") && \
        echo "Applying patch to $IEC_FILE" && \
        patch -p1 $IEC_FILE < /build/patches/iec61850.i.patch; \
    fi

# Build libiec61850 with Python bindings
WORKDIR /build/libiec61850
RUN mkdir -p build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr \
          -DBUILD_PYTHON_BINDINGS=ON \
          .. && \
    make WITH_MBEDTLS3=1 -j$(nproc) && \
    make install && \
    make test

# Show where the library files are located
RUN find /usr -name "libiec61850.so*" | sort && \
    find /build -name "libiec61850.so*" | sort && \
    ldconfig && \
    ls -la /build/libiec61850/build/src/

# Show where the Python bindings are located
RUN find /usr -name "pyiec61850" -type d | sort && \
    find /build -name "pyiec61850" -type d | sort

# Extract version number without 'v' prefix for Python package
RUN PACKAGE_VERSION=$(echo $LIBIEC61850_VERSION | sed 's/^v//').0 && \
    echo "Python package version: $PACKAGE_VERSION"

# Create a Python package for pyiec61850
WORKDIR /build/pyiec61850-package

# Create package structure
RUN mkdir -p pyiec61850

# Create setup.py file with version extracted from build arg
RUN PACKAGE_VERSION=$(echo $LIBIEC61850_VERSION | sed 's/^v//').0 && \
    echo 'from setuptools import setup, find_packages' > setup.py && \
    echo 'from setuptools.dist import Distribution' >> setup.py && \
    echo '' >> setup.py && \
    echo 'class BinaryDistribution(Distribution):' >> setup.py && \
    echo '    def has_ext_modules(self):' >> setup.py && \
    echo '        return True' >> setup.py && \
    echo '' >> setup.py && \
    echo 'setup(' >> setup.py && \
    echo '    name="pyiec61850-ng",' >> setup.py && \
    echo "    version=\"$PACKAGE_VERSION\"," >> setup.py && \
    echo '    packages=find_packages(),' >> setup.py && \
    echo '    package_data={' >> setup.py && \
    echo '        "pyiec61850": ["*.so", "*.py", "lib*.so*"],' >> setup.py && \
    echo '    },' >> setup.py && \
    echo '    include_package_data=True,' >> setup.py && \
    echo "    description=\"Python bindings for libiec61850 $LIBIEC61850_VERSION\"," >> setup.py && \
    echo '    author="Your Name",' >> setup.py && \    
    echo '    url="https://github.com/f0rw4rd/pyiec61850-ng",' >> setup.py && \
    echo '    python_requires=">=3.6",' >> setup.py && \
    echo '    distclass=BinaryDistribution,' >> setup.py && \
    echo ')' >> setup.py

# Copy Python modules from the build directory
RUN cp -r /build/libiec61850/build/pyiec61850/* pyiec61850/ && \
    ls -la pyiec61850/

# Copy the shared libraries from the build directory
RUN cp /build/libiec61850/build/src/libiec61850.so* pyiec61850/ && \
    ls -la pyiec61850/

# Create package initialization file with library loader
RUN echo "\"\"\"Python bindings for libiec61850 $LIBIEC61850_VERSION\"\"\"" > pyiec61850/__init__.py && \
    echo "import os" >> pyiec61850/__init__.py && \
    echo "import sys" >> pyiec61850/__init__.py && \
    echo "import ctypes" >> pyiec61850/__init__.py && \
    echo "" >> pyiec61850/__init__.py && \
    echo "# Get the directory where this package is installed" >> pyiec61850/__init__.py && \
    echo "_package_dir = os.path.dirname(os.path.abspath(__file__))" >> pyiec61850/__init__.py && \
    echo "" >> pyiec61850/__init__.py && \
    echo "# Pre-load the shared library from our package directory" >> pyiec61850/__init__.py && \
    echo "for lib_file in os.listdir(_package_dir):" >> pyiec61850/__init__.py && \
    echo "    if lib_file.startswith('libiec61850.so'):" >> pyiec61850/__init__.py && \
    echo "        try:" >> pyiec61850/__init__.py && \
    echo "            lib_path = os.path.join(_package_dir, lib_file)" >> pyiec61850/__init__.py && \
    echo "            ctypes.CDLL(lib_path)" >> pyiec61850/__init__.py && \
    echo "            break" >> pyiec61850/__init__.py && \
    echo "        except Exception as e:" >> pyiec61850/__init__.py && \
    echo "            print(f'Warning: Failed to load {lib_file}: {e}')" >> pyiec61850/__init__.py && \
    echo "" >> pyiec61850/__init__.py && \
    echo "# Also add the package directory to the PATH and LD_LIBRARY_PATH for good measure" >> pyiec61850/__init__.py && \
    echo "os.environ['PATH'] = _package_dir + os.pathsep + os.environ.get('PATH', '')" >> pyiec61850/__init__.py && \
    echo "os.environ['LD_LIBRARY_PATH'] = _package_dir + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')" >> pyiec61850/__init__.py

# Create wheel package - use pip wheel instead of setup.py bdist_wheel to ensure platform tags
RUN pip install wheel setuptools && \
    pip wheel . --no-deps --wheel-dir=dist/

# Create final stage to collect the wheel package
FROM python:3.11-slim-bullseye

# Pass the version through to the final stage
ARG LIBIEC61850_VERSION=v1.6

WORKDIR /wheels

# Copy wheel package from builder stage
COPY --from=builder /build/pyiec61850-package/dist/*.whl /wheels/

# Create a simple installation test script
RUN echo '#!/bin/bash' > /wheels/test_install.sh && \
    echo 'pip install --force-reinstall pyiec61850*.whl && \\' >> /wheels/test_install.sh && \
    echo "python -c \"import pyiec61850; print('pyiec61850 $LIBIEC61850_VERSION successfully installed and imported!')\"" >> /wheels/test_install.sh && \
    chmod +x /wheels/test_install.sh

# Create README
RUN echo "Python Wheel for libiec61850 $LIBIEC61850_VERSION" > /wheels/README.txt && \
    echo '' >> /wheels/README.txt && \
    echo 'Installation:' >> /wheels/README.txt && \
    echo '   pip install pyiec61850-*.whl' >> /wheels/README.txt && \
    echo '' >> /wheels/README.txt && \
    echo 'Or run the test script:' >> /wheels/README.txt && \
    echo '   ./test_install.sh' >> /wheels/README.txt

CMD ["bash", "-c", "echo 'Python wheel for libiec61850 is available in /wheels directory. Run: ./test_install.sh to verify installation.'"]