# CodeTrellis Build Contract (PART C: C1–C6)

**Version**: 4.16.0
**Implemented**: Session 55
**Module**: `codetrellis/build_contract.py`

---

## Overview

The Build Contract defines the formal I/O contract for matrix generation. It guarantees **stability**, **determinism**, and **predictable caching** across all 53+ supported languages and frameworks.

Every `codetrellis scan` invocation obeys this contract. Violations are reported via structured errors and standardized exit codes.

---

## C1: Input Contract

### C1.1 — Source Files

- Project root **must exist** and be a **readable directory**
- File extensions are filtered against `SUPPORTED_EXTENSIONS` (35+ extensions)
- Unsupported files are silently skipped

### C1.2 — Configuration

- `.codetrellis/config.json` is optional (auto-created if missing)
- If present, it **must** be valid JSON and a JSON object
- Invalid config → exit code **2** (Configuration Error)

### C1.3 — Environment Variables

| Variable                      | Purpose                                   | Default                      |
| ----------------------------- | ----------------------------------------- | ---------------------------- |
| `CODETRELLIS_BUILD_TIMESTAMP` | Override `generated_at` timestamp         | `datetime.now().isoformat()` |
| `CODETRELLIS_CI`              | Enable CI mode (deterministic + parallel) | unset                        |
| `CODETRELLIS_CACHE_DIR`       | Override cache location                   | `.codetrellis/cache/`        |
| `JAVA_HOME`                   | Java SDK path for Java/Kotlin parsing     | System default               |
| `JDT_LS_PATH`                 | Eclipse JDT Language Server path          | None                         |
| `NODE_ENV`                    | Node.js environment                       | None                         |

### C1.4 — CLI Flags

All CLI flags are hashed into `flags_hash` for cache invalidation. Changing any flag invalidates the cache (C5 Rule 4).

---

## C2: Output Schema Contract

### Required Outputs

| File               | Format                                                                         | Required |
| ------------------ | ------------------------------------------------------------------------------ | -------- |
| `matrix.prompt`    | UTF-8 text with `[SECTION]` headers                                            | ✅       |
| `matrix.json`      | JSON object with sorted keys                                                   | ✅       |
| `_metadata.json`   | JSON with `version`, `project`, `generated`, `stats`                           | ✅       |
| `_lockfile.json`   | JSON with `build_key`, `codetrellis_version`, `config_hash`, `env_fingerprint` | Optional |
| `_build_log.jsonl` | JSONL structured log entries                                                   | Optional |

### Schema Rules

- `matrix.prompt` must contain `[PROJECT]` section and be ≥100 bytes
- `matrix.json` root must be a JSON object with **sorted top-level keys**
- `_metadata.json.stats.totalFiles` must be > 0
- `_metadata.json.version` must match the running CodeTrellis version
- `_lockfile.json` must have `build_key`, `codetrellis_version`, `config_hash`

---

## C3: Determinism Contract

| #   | Rule                  | Implementation                                                                   |
| --- | --------------------- | -------------------------------------------------------------------------------- |
| 1   | Sorted file traversal | `sorted(Path.rglob(...))` in scanner                                             |
| 2   | Sorted JSON keys      | `json.dumps(..., sort_keys=True, default=str)`                                   |
| 3   | Timestamp control     | `CODETRELLIS_BUILD_TIMESTAMP` env var                                            |
| 4   | Set→sorted list       | `DeterminismEnforcer._prepare_for_json()` converts `set`/`frozenset` recursively |
| 5   | SHA-256 consistently  | All hashes use SHA-256 (first 16 hex chars), never MD5                           |

### Verification

```bash
# Two consecutive scans with fixed timestamp must produce identical output
CODETRELLIS_BUILD_TIMESTAMP="2026-02-20T10:00:00" codetrellis scan /path/to/project > run1.txt
CODETRELLIS_BUILD_TIMESTAMP="2026-02-20T10:00:00" codetrellis scan /path/to/project > run2.txt
shasum -a 256 run1.txt run2.txt  # Must match
```

---

## C4: Error Contract

### Exit Codes

| Code    | Name                | Meaning                                        |
| ------- | ------------------- | ---------------------------------------------- |
| **0**   | SUCCESS             | All outputs written successfully               |
| **1**   | PARTIAL_FAILURE     | Some extractors failed, partial output written |
| **2**   | CONFIGURATION_ERROR | Invalid config, env vars, or CLI flags         |
| **3**   | FATAL_ERROR         | No outputs written                             |
| **124** | TIMEOUT             | Build exceeded time limit                      |

### Error Budget

The `ErrorBudget` class tracks successes, failures, skips, and warnings across all extractors:

- **All succeed** → exit 0
- **Some fail, some succeed** → exit 1
- **All fail** → exit 3
- **Invalid config** → exit 2 (before extraction)

### Retry Policy

- File read error → skip file, log warning
- Extractor exception → catch, log, continue with other extractors
- Config error → fail immediately with exit 2
- Fatal error → exit 3

### Structured Error Reporting

```json
{
  "error": "Build completed with errors",
  "exit_code": 1,
  "exit_code_name": "PARTIAL_FAILURE",
  "violations": ["SyntaxError in broken.py"],
  "timestamp": "2026-02-20T10:00:00"
}
```

---

## C5: Cache Contract

### Cache Structure

```
.codetrellis/cache/{VERSION}/{project_name}/
├── matrix.prompt
├── matrix.json
├── _metadata.json
├── _lockfile.json
├── _build_log.jsonl
├── _extractor_cache/
└── files/          (legacy scanner)
```

### Invalidation Rules

| Rule | Trigger                         | Check                                             |
| ---- | ------------------------------- | ------------------------------------------------- |
| 1    | File content hash changes       | `_lockfile.json.file_manifest[file].content_hash` |
| 2    | CodeTrellis version changes     | `_lockfile.json.codetrellis_version`              |
| 3    | Config hash changes             | `_lockfile.json.config_hash`                      |
| 4    | CLI flags change                | `_lockfile.json.cli_flags_hash`                   |
| 5    | Extractor version changes       | `_lockfile.json.extractor_versions`               |
| 6    | Environment fingerprint changes | `_lockfile.json.env_fingerprint`                  |

### Environment Fingerprint (Rule 6)

SHA-256 of: `python={version}|platform={platform}|codetrellis={version}|{env_vars...}`

First 16 hex chars stored in `_lockfile.json.env_fingerprint`.

### Directory Resolution

`CODETRELLIS_CACHE_DIR` env var overrides the default `.codetrellis/cache/` location.

---

## C6: Compatibility Contract

- **Additive only**: New fields in `_lockfile.json` are added with defaults; old lockfiles missing new fields are handled gracefully
- **SemVer**: Version follows `MAJOR.MINOR.PATCH` format
- **Section header stability**: Required prompt sections (`[PROJECT]`) never change names
- **Backward compat**: `Lockfile.from_dict()` ignores unknown fields and defaults missing optional fields

---

## Usage

### Verify Command

```bash
codetrellis verify /path/to/project
```

Runs all C1-C6 checks and reports pass/fail:

```
[CodeTrellis] Build Contract Gate: ✅ PASS
  Checks: C1_inputs, C2_outputs, C3_determinism, C5_cache
```

### CI Mode

```bash
CODETRELLIS_CI=1 codetrellis scan /path/to/project
# Equivalent to: codetrellis scan --deterministic --parallel /path/to/project
```

### Programmatic Use

```python
from codetrellis.build_contract import (
    InputValidator,
    OutputSchemaValidator,
    DeterminismEnforcer,
    ErrorBudget,
    EnvironmentFingerprint,
    CacheInvalidator,
    BuildContractVerifier,
    ExitCode,
)

# Validate inputs
validator = InputValidator("/path/to/project")
errors = validator.validate()

# Track errors
budget = ErrorBudget()
budget.record_success("python_parser", "cli.py")
budget.record_failure("parser", "broken.py", "SyntaxError")
print(budget.exit_code)  # ExitCode.PARTIAL_FAILURE (1)

# Verify cache validity
fp = EnvironmentFingerprint.compute()
invalidator = CacheInvalidator(
    current_version="4.16.0",
    current_config_hash="abc123",
    current_flags_hash="def456",
    current_env_fingerprint=fp,
)
reasons = invalidator.invalidation_reasons(lockfile_data)
```

---

## Test Coverage

- **115 tests** in `tests/unit/test_build_contract.py`
- **93% line coverage** on `build_contract.py`
- All C1-C6 clauses explicitly tested
- Integration tests verify cross-cutting behavior
- Determinism gate: SHA-256 identical across consecutive runs ✅
- Error contract gate: Malformed config → exit code 2 ✅
