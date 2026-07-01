# Changelog

All notable changes to this project are documented here. Versioning follows
`LIBIEC61850_VERSION.REVISION` (see `version.py`).

## 1.6.1.6

### Added
- **Sampled Values (IEC 61850-9-2) now works.** The SV L2 API was never wrapped,
  so every `SVPublisher`/`SVSubscriber` raised on `start()`, and the subscriber
  called functions that exist in neither the binding nor libiec61850. Now:
  - `patches/iec61850.i` wraps `sv_publisher.h` + `sv_subscriber.h` with the same
    NULL-safety typemaps / destroy no-ops / create-NULL checks as GOOSE, and
    `%ignore`s the deprecated header aliases (`SampledValuesPublisher_*`,
    `SV_ASDU_*`) that aren't compiled into the library (they caused an
    `undefined symbol` at import).
  - `patches/svHandler.hpp` adds a SWIG director (`SVHandler` +
    `SVSubscriberForPython`) for the callback-based `SVUpdateListener` API, and
    `sv/subscriber.py` is rebuilt around the callback/ASDU model.
  - Verified with a Docker `--cap-add=NET_RAW` publish→subscribe round-trip that
    asserts the decoded INT32 samples match what was published.

### Fixed
- **SV publisher wrote garbage samples.** `SVPublisher_ASDU_setINT32` is keyed by
  the entry's **byte offset** (as returned by `addINT32`), but the wrapper passed
  the entry **index** (0, 1, 2, …) — misaligned, overlapping writes. It now uses
  the offsets returned by `addINT32`.

## 1.6.1.5

### Fixed
- **GOOSE publisher crash (issue #20).** `GoosePublisher.start()` item-assigned
  `CommParameters.dstAddress` — a SWIG `uint8_t[6]` that has no item assignment
  — raising `TypeError` and making GOOSE publishing unusable. Now uses the
  `CommParameters_setDstAddress` helper.
- **GOOSE subscriber never returned values.** Two bugs: `trigger()` counted
  data-set entries with the non-existent `GooseSubscriber_getNumberOfDataSetEntries`
  (`AttributeError` swallowed → count 0; now `MmsValue_getArraySize`), and
  `start()` passed a zero-length template to `GooseSubscriber_create`, which made
  libiec61850 overflow (`getParseError()==4`) on the received `allData` so nothing
  decoded. It now passes NULL data-set values so libiec61850 auto-builds the data
  set from each frame; values round-trip correctly.
- **More calls to binding functions that don't exist** (same class as the two
  above), found by a new contract test and fixed: `MMSClient.get_data_attributes`
  used a phantom ACSI class and always returned `[]` (now uses
  `IedConnection_getDataDirectory`); the TASE.2 `get_server_identity` called the
  non-existent `IedConnection_identify` (now the MMS Identify service);
  `GoCBClient` and the TASE.2 connection called `IedConnection_getLogicalNodeList`
  (now `IedConnection_getLogicalDeviceDirectory`); reporting used
  `ClientReportControlBlock_getDataSetName`/`_setDataSetName` (now `…Reference`)
  and a misspelled `ClientReport_getMoreSegementsFollow`; the GOOSE subscriber
  used `GooseSubscriber_needsCommissioning` (now `…needsCommission`).

### Tests
- Docker-based GOOSE publish→subscribe round-trip (publisher + subscriber in one
  `--cap-add=NET_RAW` container), so raw-socket coverage needs no host privileges.
- New static contract test (`tests/test_binding_contract.py`): AST-scans the
  wrappers and fails if any call a binding function absent from
  `tests/_binding_symbols.txt` (unless `hasattr`-guarded or allowlisted) — the
  guardrail for the whole "phantom function" bug class. Runs without the native
  extension. (SV and the TLS cert path are allowlisted as known-unsupported.)
- The Docker GOOSE round-trip now verifies decoded data-set values and
  `parse_error==0`, not just frame delivery.

## 1.6.1.4

### Fixed — MMS client (high-level `MMSClient`)
- **`write_value()` can now write any functional constraint.** It gained an
  optional `fc` parameter (an `int`, a two-letter string like `"SP"`/`"CO"`, or
  a trailing `[FC]` reference suffix), mirroring `read_value()`. It was
  previously hardcoded to `FC_ST`, so it could not write setpoints (SP),
  controls (CO), etc. — every real write target failed on a conformant server.
- **`write_value()` return handling.** `IedConnection_writeObject` returns a
  `(value, error)` tuple in this binding; the old code compared the tuple to a
  scalar and raised `WriteError` even on a *successful* write. It now unpacks
  the result correctly.
- **`get_server_identity()` now returns the real identity.** It called the
  non-existent `IedConnection_identify` and always returned an empty
  `ServerIdentity`; it now uses the MMS-layer Identify service
  (`IedConnection_getMmsConnection` + `MmsConnection_identify`).
- **`read_value()` no longer loses information.** It now uses the full
  `mms_value_to_python` converter: `MMS_DATA_ACCESS_ERROR` maps to `None`
  (so a failed/not-applicable read is detectable via `is None`) and structures
  become dicts, matching `read_dataset()`. The old converter returned a truthy
  `"<MmsValue type=N>"` placeholder for those cases.

### Fixed — native SWIG layer (`patches/iec61850.i`)
- **`*_destroy(None)` / `MmsValue_delete(None)` are now safe no-ops**, as the
  code always intended. The opaque-pointer NULL-check typemap previously fired
  before the destroy no-op `%exception`, turning `destroy(None)` into a
  `ValueError`. The check is now skipped for `*_destroy` functions (via
  `$symname`).
- **`GooseSubscriber_create(ref, None)` accepts a NULL dataset.** The
  `MmsValue*` NULL-check no longer rejects the optional `dataSetValues`
  argument (NULL means "auto-create the dataset").

### Tests & tooling
- Added a faithful fake binding for unit tests (`tests/support.py` +
  `tests/_binding_symbols.txt`): a `spec`'d mock built from a snapshot of the
  real binding symbols, so a test referencing a function that does not exist
  (e.g. `IedConnection_identify`) fails in the test, and tuple return shapes are
  honoured. New `tests/test_mms_faithful.py` locks the fixes above.
- `tests/conftest.py`: a mock-safe native guard (Mock arguments short-circuit
  instead of wedging the SWIG typemap at GC) and a collection hook that skips
  the SWIG-director crash-path tests when the native extension is importable —
  so the unit suite (mocked, no extension) and integration suite (real
  extension) can coexist without hanging.
- Vendored `tests/integration/data/model.cfg` so the in-process `IedServer`
  loopback integration tests run on a plain checkout (no libiec61850 source
  tree required).
- Migrated stale `*_raises_without_library` tests to gate on the real
  `_libload.have_library()` check rather than the no-op `_HAS_IEC61850` flag,
  and re-synced `test_server.py` mocks to the current model-loading /
  `IedServer_create` code paths.

### Known notes
- A benign `swig/python detected a memory leak of type 'EthernetSocket *', no
  destructor found.` message may print to stderr during GOOSE/SV receiver
  tests. SWIG has no destructor bound for the standalone `EthernetSocket`
  proxy; the socket is owned and freed by its `GooseReceiver`, so this is not a
  functional leak in the Python wrappers.

## 1.6.1.3 and earlier

See git history; per-CPython manylinux wheels and packaging fixes (issue #15).
