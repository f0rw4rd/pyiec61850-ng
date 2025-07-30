#!/bin/bash

# Test script for building wheels locally
set -e

PYTHON_VERSION=${1:-"3.11"}
LIBIEC61850_VERSION=${2:-"v1.6"}

echo "Testing build for Python ${PYTHON_VERSION} with libiec61850 ${LIBIEC61850_VERSION}"

# Determine base image
if [[ "$PYTHON_VERSION" == "3.6" || "$PYTHON_VERSION" == "3.7" ]]; then
    BASE_IMAGE="python:${PYTHON_VERSION}-slim-buster"
else
    BASE_IMAGE="python:${PYTHON_VERSION}-slim-bullseye"
fi

echo "Using base image: $BASE_IMAGE"

# Create test Dockerfile
cat > Dockerfile.test-py${PYTHON_VERSION} << EOF
FROM $BASE_IMAGE AS builder

# Set libiec61850 version as a build argument
ARG LIBIEC61850_VERSION=v1.6

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    build-essential \\
    cmake \\
    swig \\
    python3-dev \\
    python3-setuptools \\
    python3-wheel \\
    python3-pip \\
    wget tar \\
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Clone libiec61850 with specified version
RUN echo "Building libiec61850 version: \$LIBIEC61850_VERSION" && \\
    git clone --depth 1 --branch \$LIBIEC61850_VERSION https://github.com/mz-automation/libiec61850.git

# Download mbedTLS directly
RUN cd libiec61850/third_party/mbedtls && \\
    wget https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v3.6.0.tar.gz --no-check-certificate && \\
    tar -xzf v3.6.0.tar.gz

# Copy patch files
COPY patches/ /build/patches/

# Apply patches
RUN cd /build/libiec61850 && \\
    if [ -f /build/patches/iec61850.i.patch ]; then \\
        IEC_FILE=\$(find . -name "iec61850.i") && \\
        echo "Applying patch to \$IEC_FILE" && \\
        patch -p1 \$IEC_FILE < /build/patches/iec61850.i.patch; \\
    fi

# Build libiec61850 with Python bindings
WORKDIR /build/libiec61850
RUN mkdir -p build && \\
    cd build && \\
    cmake -DCMAKE_INSTALL_PREFIX=/usr \\
          -DBUILD_PYTHON_BINDINGS=ON \\
          .. && \\
    make WITH_MBEDTLS3=1 -j\$(nproc) && \\
    make install

# Create a Python package for pyiec61850
WORKDIR /build/pyiec61850-package
RUN mkdir -p pyiec61850

# Create setup.py file with version
RUN PACKAGE_VERSION=\$(echo \$LIBIEC61850_VERSION | sed 's/^v//').0 && \\
    echo 'from setuptools import setup, find_packages' > setup.py && \\
    echo 'from setuptools.dist import Distribution' >> setup.py && \\
    echo '' >> setup.py && \\
    echo 'class BinaryDistribution(Distribution):' >> setup.py && \\
    echo '    def has_ext_modules(self):' >> setup.py && \\
    echo '        return True' >> setup.py && \\
    echo '' >> setup.py && \\
    echo 'setup(' >> setup.py && \\
    echo '    name="pyiec61850",' >> setup.py && \\
    echo "    version=\"\$PACKAGE_VERSION\"," >> setup.py && \\
    echo '    packages=find_packages(),' >> setup.py && \\
    echo '    package_data={' >> setup.py && \\
    echo '        "pyiec61850": ["*.so", "*.py", "lib*.so*"],' >> setup.py && \\
    echo '    },' >> setup.py && \\
    echo '    include_package_data=True,' >> setup.py && \\
    echo "    description=\"Python bindings for libiec61850 \$LIBIEC61850_VERSION\"," >> setup.py && \\
    echo '    python_requires=">=${PYTHON_VERSION}",' >> setup.py && \\
    echo '    distclass=BinaryDistribution,' >> setup.py && \\
    echo ')' >> setup.py

# Copy Python modules and libraries
RUN cp -r /build/libiec61850/build/pyiec61850/* pyiec61850/ && \\
    cp /build/libiec61850/build/src/libiec61850.so* pyiec61850/

# Create package initialization file
RUN echo "import os, sys, ctypes" > pyiec61850/__init__.py && \\
    echo "_package_dir = os.path.dirname(os.path.abspath(__file__))" >> pyiec61850/__init__.py && \\
    echo "for lib_file in os.listdir(_package_dir):" >> pyiec61850/__init__.py && \\
    echo "    if lib_file.startswith('libiec61850.so'):" >> pyiec61850/__init__.py && \\
    echo "        try:" >> pyiec61850/__init__.py && \\
    echo "            lib_path = os.path.join(_package_dir, lib_file)" >> pyiec61850/__init__.py && \\
    echo "            ctypes.CDLL(lib_path)" >> pyiec61850/__init__.py && \\
    echo "            break" >> pyiec61850/__init__.py && \\
    echo "        except Exception as e:" >> pyiec61850/__init__.py && \\
    echo "            print(f'Warning: Failed to load {lib_file}: {e}')" >> pyiec61850/__init__.py

# Build wheel and test import
RUN pip install wheel && \\
    python setup.py bdist_wheel && \\
    pip install dist/*.whl && \\
    python -c "import pyiec61850; print('SUCCESS: pyiec61850 imported successfully')"

# Final stage
FROM scratch
COPY --from=builder /build/pyiec61850-package/dist/*.whl /wheels/
EOF

# Build and test
echo "Building Docker image..."
docker build -f Dockerfile.test-py${PYTHON_VERSION} -t pyiec61850-test-py${PYTHON_VERSION} --build-arg LIBIEC61850_VERSION=${LIBIEC61850_VERSION} .

echo "Extracting wheel..."
mkdir -p ./test-dist-py${PYTHON_VERSION}
docker create --name test-wheel-container-py${PYTHON_VERSION} pyiec61850-test-py${PYTHON_VERSION}
docker cp test-wheel-container-py${PYTHON_VERSION}:/wheels/. ./test-dist-py${PYTHON_VERSION}/
docker rm test-wheel-container-py${PYTHON_VERSION}

echo "Built wheel files:"
ls -la ./test-dist-py${PYTHON_VERSION}/

# Test the wheel
echo "Testing wheel installation..."
docker run --rm -v "$(pwd)/test-dist-py${PYTHON_VERSION}:/wheels" $BASE_IMAGE sh -c "
    pip install /wheels/*.whl && 
    python -c 'import pyiec61850; print(\"SUCCESS: Wheel works on Python ${PYTHON_VERSION}!\")'
"

echo "✅ Test completed successfully for Python ${PYTHON_VERSION}"

# Cleanup
rm -f Dockerfile.test-py${PYTHON_VERSION}