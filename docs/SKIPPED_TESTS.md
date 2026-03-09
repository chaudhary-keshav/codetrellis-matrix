# Skipped Tests Audit

> Generated as part of the v5.0 Improvement Plan — Phase 1 (Reliability & Test Health)
> Baseline: 6742 passed, 101 skipped, 0 errors (Python 3.14, macOS)
> Updated: 6790 passed, 86 skipped, 0 errors, 0 warnings (with venv + watchdog + pytest-timeout)

## Summary

| Category                                                 | Count | Files                                                                                                           |
| -------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------- |
| (a) Missing optional dependency (watchdog)               | 0\*   | `tests/test_watcher.py` — 15 tests now pass when `watchdog` is installed via venv                               |
| (a) Missing build artifact (requires `codetrellis scan`) | 86    | `tests/integration/test_advanced_gates.py`, `test_build_contracts_advanced.py`, `test_cross_topic_synergies.py` |
| (b) Platform-specific                                    | 0     | —                                                                                                               |
| (c) Broken / needs fix                                   | 0     | —                                                                                                               |

**Total: 86 skipped** (all with documented, valid skip reasons)

\* With `watchdog` installed (included in project dependencies), the 15 watcher tests pass.

## Category (a): Missing Optional Dependency

### `tests/test_watcher.py` — 15 tests

**Skip reason:** `watchdog not installed`

The `watchdog` library is an optional dependency for the file watcher feature.
Tests are correctly guarded with `pytest.mark.skipif(not HAS_WATCHDOG, ...)`.

**To run:** `pip install watchdog && pytest tests/test_watcher.py -v`

**Status:** Working as intended. No fix needed.

## Category (a): Missing Build Artifact

### `tests/integration/test_advanced_gates.py` — ~53 tests

**Skip reason:** `matrix.json not found` or `matrix.prompt not found`

These integration tests validate advanced build contract gates against a real
matrix output. They require `codetrellis scan .` to have been run against the
project first, producing `.codetrellis/cache/<version>/<project>/matrix.json`
and `matrix.prompt`.

**To run:** `codetrellis scan . --optimal && pytest tests/integration/test_advanced_gates.py -v`

**Status:** Working as intended — integration tests that depend on build artifacts.

### `tests/integration/test_build_contracts_advanced.py` — ~32 tests

**Skip reason:** Same as above (`matrix.json` / `matrix.prompt` not found).

**To run:** `codetrellis scan . --optimal && pytest tests/integration/test_build_contracts_advanced.py -v`

**Status:** Working as intended.

### `tests/integration/test_cross_topic_synergies.py` — 1 test

**Skip reason:** `matrix.json not found`

**To run:** `codetrellis scan . --optimal && pytest tests/integration/test_cross_topic_synergies.py -v`

**Status:** Working as intended.

## Conclusion

All 86 skipped tests have valid, documented skip reasons:

- **0** require optional `watchdog` dependency (now installed in venv; 15 tests pass)
- **86** require `codetrellis scan` build artifacts (integration tests, correctly guarded)
- **0** are platform-specific
- **0** are broken or need fixing

No action required beyond this documentation. The skip count is expected and acceptable.
