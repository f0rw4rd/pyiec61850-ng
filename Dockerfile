FROM python:3.12-slim-bookworm AS builder

ARG LIBIEC61850_VERSION=v1.6.0
ARG LIBIEC61850_PINNED_SHA=
ARG MBEDTLS_SHA256=
ARG PACKAGE_VERSION=0.0.0

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        cmake \
        swig \
        python3-dev \
        python3-setuptools \
        python3-wheel \
        python3-pip \
        wget tar \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Clone libiec61850 at pinned ref and verify integrity
RUN git clone --depth 50 --branch ${LIBIEC61850_VERSION} https://github.com/mz-automation/libiec61850.git && \
    cd libiec61850 && \
    if [ -n "${LIBIEC61850_PINNED_SHA}" ]; then \
      ACTUAL_SHA=$(git rev-parse HEAD); \
      if [ "${ACTUAL_SHA}" != "${LIBIEC61850_PINNED_SHA}" ]; then \
        echo "ERROR: SHA mismatch! Expected ${LIBIEC61850_PINNED_SHA}, got ${ACTUAL_SHA}"; \
        exit 1; \
      fi; \
      echo "Verified: libiec61850 commit SHA matches pinned value"; \
    fi

# Download mbedTLS and verify checksum
RUN cd libiec61850/third_party/mbedtls && \
    wget -q https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v3.6.0.tar.gz && \
    if [ -n "${MBEDTLS_SHA256}" ]; then \
      echo "${MBEDTLS_SHA256}  v3.6.0.tar.gz" | sha256sum -c -; \
    fi && \
    tar -xzf v3.6.0.tar.gz

# Copy and apply patches
COPY patches/ /build/patches/
RUN cd /build/libiec61850 && \
    if [ -f /build/patches/iec61850.i.patch ]; then \
        IEC_FILE=$(find . -name "iec61850.i") && \
        echo "Applying patch to ${IEC_FILE}" && \
        patch -p1 ${IEC_FILE} < /build/patches/iec61850.i.patch; \
    fi

# Build libiec61850 with Python bindings
WORKDIR /build/libiec61850
RUN mkdir -p build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr \
          -DBUILD_PYTHON_BINDINGS=ON \
          .. && \
    make WITH_MBEDTLS3=1 -j$(nproc) && \
    make install

# Create Python package directory
WORKDIR /build/pyiec61850-package
RUN mkdir -p pyiec61850

# Copy project files for wheel building
COPY setup_wheel.py LICENSE NOTICE README.md /build/pyiec61850-package/
RUN mv setup_wheel.py setup.py

# Copy pure-Python subpackages from repo source
COPY pyiec61850/ /build/repo-pyiec61850/

# Copy SWIG build artifacts (compiled C extension + shared library)
RUN cp /build/libiec61850/build/pyiec61850/_pyiec61850.so pyiec61850/ && \
    cp /build/libiec61850/build/pyiec61850/pyiec61850.py pyiec61850/ && \
    cp /build/libiec61850/build/src/libiec61850.so* pyiec61850/

# Copy pure-Python subpackages alongside the compiled extension
RUN for subpkg in mms tase2 goose sv server _pyinstaller; do \
        if [ -d /build/repo-pyiec61850/$subpkg ]; then \
            cp -r /build/repo-pyiec61850/$subpkg pyiec61850/$subpkg && \
            find pyiec61850/$subpkg -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
            echo "Included subpackage: $subpkg"; \
        fi; \
    done && \
    ls -la pyiec61850/

# Create __init__.py: load C library first, then import submodules
RUN cat > pyiec61850/__init__.py << 'INITEOF'
import os, sys, ctypes
_package_dir = os.path.dirname(os.path.abspath(__file__))
for _f in os.listdir(_package_dir):
    if _f.startswith('libiec61850.so'):
        try:
            ctypes.CDLL(os.path.join(_package_dir, _f))
            break
        except Exception as _e:
            print(f'Warning: Failed to load {_f}: {_e}')
try:
    from . import tase2
except ImportError:
    pass
try:
    from . import mms
except ImportError:
    pass
try:
    from . import goose
except ImportError:
    pass
try:
    from . import sv
except ImportError:
    pass
try:
    from . import server
except ImportError:
    pass
__all__ = ['tase2', 'mms', 'goose', 'sv', 'server']
INITEOF

# Build wheel and retag as universal py3 (SWIG .so has no version suffix from cmake)
RUN pip install build wheel setuptools && \
    PACKAGE_VERSION=${PACKAGE_VERSION} python setup.py bdist_wheel && \
    echo "=== Wheel contents ===" && \
    python -c "import zipfile, sys; [print(f.filename) for f in zipfile.ZipFile(sys.argv[1]).filelist]" dist/*.whl && \
    wheel tags --python-tag=py3 --abi-tag=none --platform-tag=linux_x86_64 \
      --remove dist/*.whl

# Generate SHA256 checksums
RUN cd dist && sha256sum *.whl > SHA256SUMS

# Test stage: install the wheel and verify both ctypes and SWIG imports work
FROM python:3.12-slim-bookworm AS tester
COPY --from=builder /build/pyiec61850-package/dist/*.whl /tmp/wheels/
RUN pip install /tmp/wheels/*.whl && \
    python -c "import pyiec61850; print('pyiec61850 import OK')" && \
    python -c "import pyiec61850.pyiec61850; print('SWIG bindings OK')" && \
    python -c "from pyiec61850 import mms; print(f'mms {mms.__version__} OK')" && \
    python -c "from pyiec61850 import tase2; print(f'tase2 {tase2.__version__} OK')" && \
    python -c "from pyiec61850 import goose; print(f'goose {goose.__version__} OK')" && \
    python -c "from pyiec61850 import sv; print(f'sv {sv.__version__} OK')" && \
    python -c "from pyiec61850 import server; print(f'server {server.__version__} OK')"

# Final output stage
FROM python:3.12-slim-bookworm
WORKDIR /wheels
COPY --from=builder /build/pyiec61850-package/dist/*.whl /wheels/
COPY --from=builder /build/pyiec61850-package/dist/SHA256SUMS /wheels/
