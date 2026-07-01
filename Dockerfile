# Build manylinux wheels for pyiec61850-ng.
#
# One wheel per CPython version (cp39..cp314), each repaired with auditwheel so
# it carries an honest `cpXY-cpXY-manylinux_2_28_x86_64` tag, a clean $ORIGIN
# RPATH, and the bundled libiec61850.so relocated into pyiec61850.libs/.
#
# Previously this produced a single `py3-none-linux_x86_64` wheel (later renamed
# to manylinux1 in CI) whose _pyiec61850.so was a CPython-3.12-specific binary
# advertised as compatible with every Python/glibc -> segfaults / load failures
# on mismatched interpreters and older glibc (see issue #15).
ARG MANYLINUX_IMAGE=quay.io/pypa/manylinux_2_28_x86_64
FROM ${MANYLINUX_IMAGE} AS builder

ARG LIBIEC61850_VERSION=v1.6.1
ARG LIBIEC61850_PINNED_SHA=
ARG MBEDTLS_SHA256=
ARG PACKAGE_VERSION=0.0.0
ARG SWIG_VERSION=4.1.1
# Space-separated CPython tags to build (must exist under /opt/python/<tag>).
ARG PYTHON_BUILDS="cp39-cp39 cp310-cp310 cp311-cp311 cp312-cp312 cp313-cp313 cp314-cp314"

# Build dependencies (manylinux_2_28 == AlmaLinux 8; modern gcc on PATH).
RUN dnf install -y --setopt=install_weak_deps=False \
        git wget tar make gcc gcc-c++ cmake pcre2-devel \
    && dnf clean all

# Build SWIG from source so the wrapper matches upstream's 4.x typemaps
# (AlmaLinux 8 ships swig 3.0.x which cannot parse patches/iec61850.i).
RUN wget -q -O "swig-${SWIG_VERSION}.tar.gz" "https://downloads.sourceforge.net/swig/swig-${SWIG_VERSION}.tar.gz" && \
    tar -xzf "swig-${SWIG_VERSION}.tar.gz" && \
    cd "swig-${SWIG_VERSION}" && \
    ./configure --prefix=/usr/local >/dev/null && \
    make -j"$(nproc)" >/dev/null && \
    make install >/dev/null && \
    swig -version && \
    cd / && rm -rf "swig-${SWIG_VERSION}" "swig-${SWIG_VERSION}.tar.gz"

WORKDIR /build

# Clone libiec61850 at the pinned ref and verify integrity.
RUN git clone --depth 50 --branch "${LIBIEC61850_VERSION}" https://github.com/mz-automation/libiec61850.git && \
    cd libiec61850 && \
    if [ -n "${LIBIEC61850_PINNED_SHA}" ]; then \
      ACTUAL_SHA=$(git rev-parse HEAD); \
      if [ "${ACTUAL_SHA}" != "${LIBIEC61850_PINNED_SHA}" ]; then \
        echo "ERROR: SHA mismatch! Expected ${LIBIEC61850_PINNED_SHA}, got ${ACTUAL_SHA}"; \
        exit 1; \
      fi; \
      echo "Verified: libiec61850 commit SHA matches pinned value"; \
    fi

# Download mbedTLS 3.6.0 and verify checksum. The presence of the
# third_party/mbedtls/mbedtls-3.6.0 directory makes upstream cmake enable
# WITH_MBEDTLS3 automatically.
RUN cd libiec61850/third_party/mbedtls && \
    wget -q https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v3.6.0.tar.gz && \
    if [ -n "${MBEDTLS_SHA256}" ]; then \
      echo "${MBEDTLS_SHA256}  v3.6.0.tar.gz" | sha256sum -c -; \
    fi && \
    tar -xzf v3.6.0.tar.gz && rm v3.6.0.tar.gz

# Replace upstream SWIG interface with our enhanced version
# (NULL-safety typemaps, file download helpers, IedClientError typemap).
COPY patches/iec61850.i /build/libiec61850/pyiec61850/iec61850.i
COPY patches/informationReportHandler.hpp /build/libiec61850/pyiec61850/eventHandlers/informationReportHandler.hpp
COPY patches/svHandler.hpp /build/libiec61850/pyiec61850/eventHandlers/svHandler.hpp

# Building an extension needs only the Python headers (Development.Module), not
# an embeddable libpython. manylinux interpreters ship no shared libpython, so
# upstream's `Development` (== Module + Embed) cannot be satisfied.
RUN sed -i \
    's/find_package(Python COMPONENTS Interpreter Development REQUIRED)/find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)/' \
    /build/libiec61850/pyiec61850/CMakeLists.txt && \
    grep -n 'find_package(Python' /build/libiec61850/pyiec61850/CMakeLists.txt

# Project files for wheel building.
COPY setup_wheel.py LICENSE NOTICE README.md /build/pkg-src/
COPY pyiec61850/ /build/pkg-src/pyiec61850/
COPY scripts/check_wheel.py /build/scripts/check_wheel.py

# Build one wheel per CPython: configure libiec61850 + bindings against that
# interpreter, stage the package, build the wheel, then repair with auditwheel.
RUN set -eux; \
    mkdir -p /wheels; \
    for tag in ${PYTHON_BUILDS}; do \
        PYBIN="/opt/python/${tag}/bin/python"; \
        if [ ! -x "${PYBIN}" ]; then echo "skip ${tag}: no interpreter"; continue; fi; \
        echo "=================== building for ${tag} ==================="; \
        bdir="/build/libiec61850/build-${tag}"; \
        cmake -S /build/libiec61850 -B "${bdir}" \
              -DCMAKE_BUILD_TYPE=Release \
              -DBUILD_PYTHON_BINDINGS=ON \
              -DBUILD_EXAMPLES=OFF \
              -DPython_EXECUTABLE="${PYBIN}"; \
        cmake --build "${bdir}" --target pyiec61850 -j"$(nproc)"; \
        \
        stage="/build/stage-${tag}"; \
        rm -rf "${stage}"; \
        cp -r /build/pkg-src "${stage}"; \
        ( cd "${stage}" && mv setup_wheel.py setup.py ); \
        find "${stage}/pyiec61850" -name '__pycache__' -type d -prune -exec rm -rf {} + ; \
        # Name the extension with the interpreter's ABI suffix so CPython refuses
        # to load it under the wrong version (defense in depth on top of the tag).
        SUF=$("${PYBIN}" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))'); \
        cp "${bdir}/pyiec61850/_pyiec61850.so" "${stage}/pyiec61850/_pyiec61850${SUF}"; \
        cp "${bdir}/pyiec61850/pyiec61850.py" "${stage}/pyiec61850/pyiec61850.py"; \
        \
        "${PYBIN}" -m pip install -q --upgrade pip setuptools wheel; \
        ( cd "${stage}" && PACKAGE_VERSION="${PACKAGE_VERSION}" "${PYBIN}" setup.py bdist_wheel ); \
        \
        # auditwheel bundles libiec61850.so into pyiec61850.libs/, rewrites RPATH
        # to $ORIGIN, strips the /build RUNPATH, and applies the manylinux tag.
        LD_LIBRARY_PATH="${bdir}/src" auditwheel repair \
            --plat manylinux_2_28_x86_64 \
            -w /wheels \
            "${stage}/dist/"*.whl; \
        \
        rm -rf "${bdir}" "${stage}"; \
    done; \
    echo "=== repaired wheels ==="; ls -la /wheels

# Guard against tag/ABI/RPATH/vendoring regressions (the issue #15 failure mode).
RUN set -eux; \
    for tag in ${PYTHON_BUILDS}; do \
        [ -x "/opt/python/${tag}/bin/python" ] && PYBIN="/opt/python/${tag}/bin/python" && break; \
    done; \
    "${PYBIN}" /build/scripts/check_wheel.py /wheels/*.whl

# Smoke-test each wheel under its matching interpreter.
RUN set -eux; \
    for tag in ${PYTHON_BUILDS}; do \
        PYBIN="/opt/python/${tag}/bin/python"; \
        [ -x "${PYBIN}" ] || continue; \
        abi="${tag#*-}"; \
        whl=$(ls /wheels/*-"${abi}"-*.whl 2>/dev/null | head -n1 || true); \
        [ -n "${whl}" ] || { echo "no wheel for ${tag}"; exit 1; }; \
        echo "=== testing ${whl} on ${tag} ==="; \
        "${PYBIN}" -m pip install -q "${whl}"; \
        "${PYBIN}" -X faulthandler -c "import pyiec61850, pyiec61850.pyiec61850; from pyiec61850 import mms, goose, sv, server, tase2; print('import OK', '${tag}')"; \
    done

RUN cd /wheels && sha256sum *.whl > SHA256SUMS
# `builder` is the final stage: the wheels live in /wheels and the image keeps a
# runnable config, so CI extracts them with `docker create` + `docker cp`.
