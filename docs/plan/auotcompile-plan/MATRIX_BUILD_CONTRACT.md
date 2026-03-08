# Matrix Build Contract

> **Version:** 1.0.0  
> **Date:** 19 February 2026  
> **Status:** DRAFT  
> **Applies to:** CodeTrellis v4.9.0+

---

## 1. Purpose

This document defines the formal build contract for CodeTrellis matrix generation. Any implementation of the matrix build pipeline MUST conform to this contract. Consumers of matrix outputs (AI prompts, CI pipelines, IDE extensions) MAY rely on the guarantees defined here.

---

## 2. Definitions

| Term                  | Definition                                                                                               |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| **Matrix**            | The complete project analysis output, consisting of `matrix.json`, `matrix.prompt`, and `_metadata.json` |
| **Build**             | A single execution of the matrix generation pipeline                                                     |
| **Incremental Build** | A build that reuses cached results for unchanged inputs                                                  |
| **Full Build**        | A build that ignores all caches and processes all inputs from scratch                                    |
| **Lockfile**          | `_lockfile.json` — a manifest of all input hashes used in the build                                      |
| **Build Key**         | A composite hash uniquely identifying a set of build inputs                                              |

---

## 3. Inputs

### 3.1 Source Files

- **Scope:** All files under `{project_root}/` matching supported extensions
- **Extensions:** `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.kt`, `.cs`, `.go`, `.rs`, `.rb`, `.php`, `.scala`, `.r`, `.dart`, `.lua`, `.ps1`, `.sh`, `.bash`, `.sql`, `.html`, `.css`, `.scss`, `.sass`, `.less`, `.vue`, `.svelte`, `.astro`, `.json`, `.yaml`, `.yml`, `.toml`, `.proto`, `.graphql`, `.gql`
- **Exclusions:** Defined by `.codetrellis/config.json` `ignore` array and `.gitignore`
- **Hash:** SHA-256 of file content (first 16 hex chars)

### 3.2 Configuration Files

| File                       | Purpose                                                          | Required                |
| -------------------------- | ---------------------------------------------------------------- | ----------------------- |
| `.codetrellis/config.json` | Build configuration (ignore patterns, parser flags, compression) | Auto-created if missing |
| `package.json`             | Node.js dependencies, scripts                                    | Optional                |
| `pyproject.toml`           | Python project metadata, dependencies                            | Optional                |
| `tsconfig.json`            | TypeScript configuration (required for `--deep` mode)            | Optional                |
| `.gitignore`               | File exclusion patterns                                          | Optional                |

### 3.3 Environment Variables

| Variable                      | Purpose                                               | Default                      |
| ----------------------------- | ----------------------------------------------------- | ---------------------------- |
| `CODETRELLIS_BUILD_TIMESTAMP` | Override `generated_at` for deterministic builds      | `datetime.now().isoformat()` |
| `CODETRELLIS_CI`              | Enable CI mode (deterministic, no interactive output) | unset                        |
| `CODETRELLIS_CACHE_DIR`       | Override cache directory location                     | `.codetrellis/cache/`        |
| `JAVA_HOME`                   | Java SDK path for Java/Kotlin parsing                 | System default               |
| `JDT_LS_PATH`                 | Eclipse JDT Language Server path                      | None                         |
| `NODE_ENV`                    | Node.js environment                                   | None                         |

### 3.4 CLI Flags (Build Parameters)

| Flag                                      | Effect on Output                                                                                         |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `--tier {compact,prompt,full,logic,json}` | Controls compression level of `matrix.prompt`                                                            |
| `--deep`                                  | Enables LSP type extraction, adds `lsp_stats` to metadata                                                |
| `--parallel`                              | Enables parallel processing (affects performance, not output content)                                    |
| `--workers N`                             | Number of parallel workers                                                                               |
| `--optimal`                               | Shorthand for `--tier logic --deep --parallel --include-progress --include-overview --include-practices` |
| `--incremental`                           | Use cached results for unchanged files (Phase 2)                                                         |
| `--deterministic`                         | Force deterministic output (freeze timestamp, sort keys)                                                 |
| `--ci`                                    | CI profile: `--deterministic --parallel --tier logic`                                                    |

---

## 4. Outputs

### 4.1 Required Outputs

#### `matrix.prompt`

- **Format:** Plain text, CodeTrellis compressed format
- **Encoding:** UTF-8
- **Location:** `.codetrellis/cache/{VERSION}/{project_name}/matrix.prompt`
- **Content:** Section-delimited text with `[SECTION_NAME]` headers
- **Sections (guaranteed):** `[AI_INSTRUCTION]`, `[PROJECT]`, `[CONTEXT]`, `[OVERVIEW]`, `[BEST_PRACTICES]`

#### `matrix.json`

- **Format:** JSON (pretty-printed, 2-space indent)
- **Encoding:** UTF-8
- **Location:** `.codetrellis/cache/{VERSION}/{project_name}/matrix.json`
- **Schema:** `ProjectMatrix.to_dict()` output
- **Key ordering:** `sort_keys=True` (deterministic)
- **Timestamp format:** ISO 8601 (`YYYY-MM-DDTHH:MM:SS.ffffff`)

#### `_metadata.json`

- **Format:** JSON (pretty-printed, 2-space indent)
- **Encoding:** UTF-8
- **Location:** `.codetrellis/cache/{VERSION}/{project_name}/_metadata.json`
- **Required fields:**
  ```json
  {
    "version": "string",
    "project": "string",
    "generated": "ISO 8601 timestamp",
    "deep_mode": "boolean",
    "lsp_stats": "object | null",
    "stats": {
      "totalFiles": "integer",
      "schemas": "integer",
      "dtos": "integer",
      "controllers": "integer",
      "components": "integer",
      "services": "integer",
      "grpcServices": "integer",
      "enums": "integer",
      "interfaces": "integer",
      "types": "integer",
      "angularServices": "integer",
      "stores": "integer"
    },
    "dependencies": "object"
  }
  ```

### 4.2 Optional Outputs (Phase 1+)

#### `_lockfile.json`

- **Format:** JSON
- **Location:** `.codetrellis/cache/{VERSION}/{project_name}/_lockfile.json`
- **Content:**
  ```json
  {
    "build_key": "string (SHA-256)",
    "codetrellis_version": "string",
    "config_hash": "string",
    "env_fingerprint": "string",
    "flags_hash": "string",
    "file_manifest": {
      "relative/path/to/file.py": "sha256_hash",
      ...
    },
    "extractor_versions": {
      "extractor_name": "version_string",
      ...
    },
    "generated": "ISO 8601 timestamp"
  }
  ```

#### `_build_log.jsonl`

- **Format:** JSON Lines (one JSON object per line)
- **Location:** `.codetrellis/cache/{VERSION}/{project_name}/_build_log.jsonl`
- **Entry schema:**
  ```json
  {
    "timestamp": "ISO 8601",
    "level": "INFO | WARN | ERROR",
    "event": "string",
    "extractor": "string | null",
    "file": "string | null",
    "duration_ms": "number | null",
    "message": "string"
  }
  ```

---

## 5. Determinism Guarantees

### 5.1 Strong Determinism (when `--deterministic` or `CODETRELLIS_CI=1`)

Given:

- Identical file contents (by SHA-256)
- Identical `.codetrellis/config.json`
- Identical CLI flags
- Identical `CODETRELLIS_BUILD_TIMESTAMP`
- Identical CodeTrellis version
- Identical Python version (major.minor)

Then:

- `matrix.json` MUST be byte-identical across runs
- `matrix.prompt` MUST be byte-identical across runs
- `_metadata.json` MUST be byte-identical across runs

### 5.2 Weak Determinism (default mode)

- Outputs are structurally equivalent but may differ in:
  - `generated_at` / `generated` timestamps
  - Ordering of dict keys (unless `sort_keys=True` is enforced)

### 5.3 Implementation Requirements

1. **File traversal:** `sorted(Path.rglob(...))` or `sorted(os.walk(...))`
2. **JSON output:** `json.dumps(..., sort_keys=True, default=str)`
3. **Timestamp:** Use `CODETRELLIS_BUILD_TIMESTAMP` if set, else `datetime.now()`
4. **Set/dict iteration:** Convert to sorted lists before output
5. **Hash stability:** Use SHA-256 consistently (not MD5)

---

## 6. Error Contract

### 6.1 Exit Codes

| Code | Meaning                                                             |
| ---- | ------------------------------------------------------------------- |
| 0    | Success — all outputs written                                       |
| 1    | Partial failure — some extractors failed, outputs written with gaps |
| 2    | Configuration error — invalid config, missing required input        |
| 3    | Fatal error — no outputs written                                    |
| 124  | Timeout                                                             |

### 6.2 Error Reporting

- All errors MUST be logged to `_build_log.jsonl` (when available)
- Fatal errors MUST be written to `_metadata.json` as `"error": "message"`
- Per-file errors MUST NOT abort the entire build
- Per-extractor errors MUST be counted in `_metadata.json` `stats`

### 6.3 Retry Policy

| Scenario                        | Strategy                                         |
| ------------------------------- | ------------------------------------------------ |
| File read error (ENOENT, EPERM) | Skip file, log warning                           |
| Extractor exception             | Catch, log error, continue with other extractors |
| Memory pressure                 | Reduce batch size, force GC, retry once          |
| Concurrent access               | File lock with 5s timeout, 3 retries             |

---

## 7. Cache Contract

### 7.1 Cache Location

```
.codetrellis/
└── cache/
    └── {VERSION}/
        └── {project_name}/
            ├── matrix.prompt
            ├── matrix.json
            ├── _metadata.json
            ├── _lockfile.json          (Phase 1+)
            ├── _build_log.jsonl        (Phase 1+)
            └── _extractor_cache/       (Phase 2+)
                └── {extractor_name}/
                    └── {file_content_hash}.json
```

### 7.2 Cache Invalidation Rules

A cached result is INVALID when any of these change:

1. File content hash differs from lockfile manifest
2. CodeTrellis version changes
3. `.codetrellis/config.json` hash changes
4. CLI flags change (different tier, deep mode, etc.)
5. Extractor version changes
6. Environment fingerprint changes

### 7.3 Cache Eviction

- Cache is keyed by `{VERSION}` — upgrading CodeTrellis automatically uses a new cache namespace
- No automatic eviction of old version caches
- `codetrellis clean` removes the entire `.codetrellis/cache/` directory
- `codetrellis clean --version X.Y.Z` removes a specific version cache

---

## 8. Compatibility

### 8.1 Backward Compatibility

- New fields in `_metadata.json` MUST be additive (no removal of existing fields)
- `matrix.json` schema changes MUST be backward-compatible (new optional fields only)
- `matrix.prompt` section headers MUST NOT be renamed (consumers parse by `[SECTION_NAME]`)

### 8.2 Forward Compatibility

- Consumers MUST ignore unknown fields in JSON outputs
- Consumers MUST ignore unknown sections in `matrix.prompt`
- Version field MUST follow SemVer

---

## 9. Verification

### 9.1 Self-Verification Command

```bash
codetrellis verify .
```

Checks:

1. All 3 required output files exist
2. `_metadata.json` is valid JSON with required fields
3. `matrix.json` is valid JSON
4. Version in outputs matches CodeTrellis version
5. (Phase 1+) Lockfile matches current inputs
6. (Phase 3+) Determinism check passes

### 9.2 CI Verification

```bash
CODETRELLIS_CI=1 codetrellis scan . --ci && codetrellis verify .
echo "Exit code: $?"  # 0 = PASS, non-zero = FAIL
```
