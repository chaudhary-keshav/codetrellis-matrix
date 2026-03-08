# Matrix Auto-Compilation Plan

> **Version:** 1.0.0  
> **Date:** 19 February 2026  
> **Author:** CodeTrellis Build Automation  
> **Applies to:** CodeTrellis v4.9.0 → v5.x

---

## 1. Executive Summary

- **Current state:** Matrix generation is a single-pass, full-rescan operation driven by `cli.py → scan_project()` → `scanner.scan()` → sequential extractor pipeline → `compressor.compress()` → write 3 files (`matrix.prompt`, `matrix.json`, `_metadata.json`) to `.codetrellis/cache/{VERSION}/{project}/`.
- **No incremental rebuild exists today.** The `watch` command triggers a full `scan_project()` on every detected change (see `cli.py:718` — `# TODO: Implement incremental sync`). The `sync` command is also a full scan (see `cli.py:727` — `# TODO: Implement incremental sync using hashes`).
- **Version mismatch detected:** `__init__.py` declares v4.9.0, `pyproject.toml` declares v4.16.0. Cache paths use the `__init__.py` version, meaning outputs land under `4.9.0/` even though the published package claims 4.16.0.
- **Watcher exists but is a stub.** `watcher.py` uses `watchdog` for file events, has MD5 hash tracking and debouncing (500ms), but every change triggers a full rescan — no dependency graph, no selective invalidation.
- **Streaming/parallel infrastructure exists** (`streaming.py`, `parallel.py`) with batching, caching flags, and worker pools, but the cache layer (`use_cache`, `from_cache`) is **not wired to persistent storage** — it's a placeholder.
- **Scanner is monolithic.** `scanner.py` is ~18,800 lines, instantiates 60+ parsers/extractors in `__init__`, and runs them all sequentially in `scan()`. No extractor-level dependency graph exists.
- **Top risks:** (a) version string mismatch breaking cache paths, (b) 18K-line scanner resists incremental changes, (c) no hash-based invalidation keys for extractor outputs, (d) no determinism guarantees (timestamps in output).
- **Why Angular 21-style principles apply:** Angular's builder architecture separates _targets_ (build, serve, test), uses _persistent caching_ with content-hash invalidation, supports _incremental compilation_ via dependency graphs, and provides _watch mode_ with selective rebuild — exactly the pattern needed here.
- **Opportunity:** The existing `watcher.py` hash infrastructure + `streaming.py` cache config + `parallel.py` workers provide 60% of the plumbing; the missing piece is an orchestrator/builder layer that connects them with a dependency graph.

---

## 2. Build Contract

### 2.1 Inputs

| Input                             | Location                                                       | Invalidation Key                 |
| --------------------------------- | -------------------------------------------------------------- | -------------------------------- |
| Source files                      | `{project_root}/**/*.{py,ts,tsx,js,jsx,java,go,rs,rb,php,...}` | SHA-256 content hash per file    |
| Config                            | `.codetrellis/config.json`                                     | SHA-256 of config file           |
| `.gitignore`                      | `{project_root}/.gitignore`                                    | SHA-256 of gitignore             |
| `package.json` / `pyproject.toml` | Project root                                                   | SHA-256 of dependency files      |
| Extractor versions                | `codetrellis/__init__.py` → `__version__`                      | Version string                   |
| Environment vars                  | `JAVA_HOME`, `JDT_LS_PATH`, `NODE_ENV`                         | Fingerprint of relevant env vars |
| Python version                    | `sys.version`                                                  | Major.minor string               |
| CLI flags                         | `--tier`, `--deep`, `--parallel`, `--optimal`, etc.            | Canonical flag hash              |

### 2.2 Outputs

| Output             | Path                                               | Format            | Determinism                                 |
| ------------------ | -------------------------------------------------- | ----------------- | ------------------------------------------- |
| `matrix.prompt`    | `.codetrellis/cache/{VER}/{name}/matrix.prompt`    | Text (compressed) | Deterministic after timestamp normalization |
| `matrix.json`      | `.codetrellis/cache/{VER}/{name}/matrix.json`      | JSON              | Deterministic after timestamp normalization |
| `_metadata.json`   | `.codetrellis/cache/{VER}/{name}/_metadata.json`   | JSON              | Deterministic after timestamp normalization |
| `_lockfile.json`   | `.codetrellis/cache/{VER}/{name}/_lockfile.json`   | JSON (NEW)        | Content-hash manifest of all inputs         |
| `_build_log.jsonl` | `.codetrellis/cache/{VER}/{name}/_build_log.jsonl` | JSONL (NEW)       | Append-only build trace                     |

### 2.3 Determinism Requirements

1. Given identical inputs (file contents, config, env, flags), outputs MUST be byte-identical (excluding `generated_at` timestamp).
2. `generated_at` MUST be overridable via `CODETRELLIS_BUILD_TIMESTAMP` env var for CI reproducibility.
3. Dict/list ordering in JSON output MUST use `sort_keys=True`.
4. File traversal order MUST be deterministic (`sorted()` on all `os.walk` / `Path.rglob` results).

### 2.4 Error Modes & Retry Policy

| Error                     | Behavior                                                 | Retry           |
| ------------------------- | -------------------------------------------------------- | --------------- |
| Single file parse failure | Log error, skip file, continue                           | No retry (skip) |
| Extractor crash           | Catch, log to `_build_log.jsonl`, produce partial output | No retry        |
| Timeout (per-file)        | 30s default, configurable                                | No retry        |
| OOM / memory limit        | Reduce batch size, retry once with `gc.collect()`        | 1 retry         |
| Lock contention           | Wait up to 5s for `.codetrellis/.lock`                   | 3 retries       |
| Full pipeline failure     | Exit code 1, write error to `_metadata.json`             | Full retry      |

### 2.5 Success Criteria

- Exit code 0
- All 3 output files written
- `_metadata.json` contains `"success": true`
- `_lockfile.json` matches input manifest
- No `ERROR`-level entries in `_build_log.jsonl`

---

## 3. Gap Analysis Table

| Area                          | Current                                                  | Target                                                   | Change Needed                                           | Priority           |
| ----------------------------- | -------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------- | ------------------ | ------------------ | ----- |
| **Incremental rebuild**       | None — full rescan every time                            | File-hash-based selective extractor re-run               | Add lockfile, per-extractor input tracking, diff engine | 🔴 P0              |
| **Caching strategy**          | `StreamingConfig.use_cache` flag exists but is not wired | Content-addressed cache per extractor per file           | Implement `ExtractorCache` with hash-keyed storage      | 🔴 P0              |
| **Dependency graph**          | None — extractors run in hardcoded order                 | DAG of extractors with declared inputs/outputs           | Add `ExtractorManifest` dataclass, topological sort     | 🟡 P1              |
| **Parallelism model**         | `parallel.py` exists but optional, not used by default   | Default parallel with configurable workers               | Wire `ParallelExtractor` into main `scan()` path        | 🟡 P1              |
| **Watch mode**                | `watcher.py` triggers full rescan                        | Debounced incremental rebuild using hash diff            | Connect watcher → incremental engine                    | 🟡 P1              |
| **CI ergonomics**             | `--optimal` flag, `validate-repos` command               | `--ci` flag with deterministic output, exit codes, SARIF | Add CI profile, `CODETRELLIS_CI=1` env var              | 🟡 P1              |
| **Determinism**               | Timestamps in output, no sorted keys guaranteed          | Reproducible builds, overridable timestamp               | Normalize `generated_at`, `sort_keys=True`              | 🟡 P1              |
| **Observability**             | `print()` statements throughout                          | Structured logging, `_build_log.jsonl`, progress API     | Replace prints with `logging`, add JSONL sink           | 🟢 P2              |
| **Clean rebuild**             | Delete cache dir manually                                | `codetrellis clean` command                              | Add CLI command                                         | 🟢 P2              |
| **Version consistency**       | `__init__.py`=4.9.0 vs `pyproject.toml`=4.16.0           | Single source of truth                                   | Read version from `pyproject.toml` or sync              | 🔴 P0              |
| **Profile modes**             | `--optimal` flag only                                    | `--profile dev                                           | ci                                                      | deep` with presets | Add profile system | 🟢 P2 |
| **Plugin/extractor boundary** | Extractors tightly coupled in scanner.py                 | `IExtractor` protocol with manifest                      | Extract interface, register extractors                  | 🟢 P2              |
| **Lockfile**                  | None                                                     | `_lockfile.json` with input manifest                     | New module                                              | 🔴 P0              |
| **Error budget**              | `ErrorCollector` exists but not aggregated               | Error budget per build (max N errors)                    | Wire into build orchestrator                            | 🟢 P2              |

---

## 4. Target Architecture (Angular 21-Inspired)

### 4.1 Conceptual Mapping

| Angular Concept                          | CodeTrellis Equivalent                                          |
| ---------------------------------------- | --------------------------------------------------------------- |
| `angular.json` workspace                 | `.codetrellis/config.json`                                      |
| Builder/Executor                         | `MatrixBuilder` (new orchestrator)                              |
| Targets (build, serve, test)             | Targets: `scan`, `compile-matrix`, `verify`, `package`, `watch` |
| Persistent cache (`node_modules/.cache`) | `.codetrellis/cache/{VER}/`                                     |
| Incremental TS compilation               | Hash-based extractor cache                                      |
| `ng serve --watch`                       | `codetrellis watch` with incremental engine                     |
| `nx affected`                            | `codetrellis scan --incremental`                                |

### 4.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (cli.py)                        │
│  scan | watch | sync | clean | verify | compile             │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│               MatrixBuilder (NEW: builder.py)               │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  │
│  │  Target   │  │  Target   │  │  Target    │  │  Target    │ │
│  │  SCAN     │  │  COMPILE  │  │  VERIFY    │  │  PACKAGE   │ │
│  │ (discover │  │ (run      │  │ (validate  │  │ (compress  │ │
│  │  files)   │  │  extract) │  │  outputs)  │  │  outputs)  │ │
│  └─────┬────┘  └─────┬────┘  └─────┬─────┘  └─────┬─────┘ │
│        │             │             │              │         │
│  ┌─────▼─────────────▼─────────────▼──────────────▼──────┐  │
│  │              Build Graph / DAG Scheduler               │  │
│  │  (topological sort of extractor dependencies)          │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │              Cache Manager (NEW: cache.py)             │  │
│  │  ┌────────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ InputHash   │  │ Lockfile │  │ ExtractorCache   │   │  │
│  │  │ Calculator  │  │ Manager  │  │ (per-file,       │   │  │
│  │  │ (SHA-256)   │  │          │  │  per-extractor)  │   │  │
│  │  └─────┬──────┘  └────┬─────┘  └────────┬─────────┘   │  │
│  │        │              │                  │              │  │
│  │        ▼              ▼                  ▼              │  │
│  │   .codetrellis/cache/{VER}/{project}/                   │  │
│  │     ├── _lockfile.json                                  │  │
│  │     ├── _build_log.jsonl                                │  │
│  │     ├── _extractor_cache/                               │  │
│  │     │    ├── {extractor_name}/{file_hash}.json          │  │
│  │     ├── matrix.prompt                                   │  │
│  │     ├── matrix.json                                     │  │
│  │     └── _metadata.json                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│             Extractor Layer (extractors/ + parsers)          │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Python  │ │ TypeScript│ │ Go       │ │ Framework        │ │
│  │ Parser  │ │ Parser   │ │ Parser   │ │ Extractors       │ │
│  │         │ │          │ │          │ │ (NestJS, Angular  │ │
│  │         │ │          │ │          │ │  React, Next...)  │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────────┬──────────┘ │
│       │           │           │               │             │
│  ┌────▼───────────▼───────────▼───────────────▼──────────┐  │
│  │         IExtractor Protocol (interfaces.py)            │  │
│  │  name: str                                             │  │
│  │  version: str                                          │  │
│  │  input_patterns: List[str]  # file globs              │  │
│  │  depends_on: List[str]      # other extractor names   │  │
│  │  extract(file, ctx) → Dict                            │  │
│  │  cache_key(file) → str                                │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│             Watch Engine (watcher.py — enhanced)            │
│  watchdog events → hash diff → affected extractors →       │
│  incremental rebuild → merge into existing matrix          │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Invalidation Keys

| Key Component       | Hash Algorithm                                                        | Scope           |
| ------------------- | --------------------------------------------------------------------- | --------------- |
| File content        | SHA-256 (first 8 chars)                                               | Per source file |
| Config              | SHA-256 of `.codetrellis/config.json`                                 | Global          |
| Extractor version   | `{extractor.name}:{extractor.version}`                                | Per extractor   |
| CLI flags           | Canonical sorted JSON of flags                                        | Per build       |
| Environment         | SHA-256 of `{JAVA_HOME}:{NODE_ENV}:{sys.version}`                     | Global          |
| Composite build key | SHA-256 of `config_hash + extractor_versions + env_hash + flags_hash` | Per build       |

### 4.4 Profile Modes

| Profile | Flags                                      | Use Case                         |
| ------- | ------------------------------------------ | -------------------------------- |
| `dev`   | `--tier prompt --incremental`              | Local development, fast feedback |
| `ci`    | `--tier logic --deterministic --parallel`  | CI/CD pipelines                  |
| `deep`  | `--tier logic --deep --parallel --optimal` | Full deep analysis               |

---

## 5. Phased Implementation Plan

### Phase 0: Stabilization (Week 1)

**Goal:** Fix version mismatch, ensure deterministic baseline.

| Task                                                                         | Files/Modules                   | Complexity | Acceptance Test                                                                                   |
| ---------------------------------------------------------------------------- | ------------------------------- | ---------- | ------------------------------------------------------------------------------------------------- |
| Sync version: read from `pyproject.toml` or make `__init__.py` authoritative | `__init__.py`, `pyproject.toml` | S          | `python -c "import codetrellis; print(codetrellis.__version__)"` matches `pyproject.toml`         |
| Ensure deterministic file traversal in `scanner._walk_files()`               | `scanner.py`                    | S          | Two consecutive scans produce identical `matrix.json` (after timestamp normalization)             |
| Normalize `generated_at` — support `CODETRELLIS_BUILD_TIMESTAMP` env var     | `cli.py`, `scanner.py`          | S          | `CODETRELLIS_BUILD_TIMESTAMP=2026-01-01T00:00:00 codetrellis scan .` → fixed timestamp in outputs |
| Add `sort_keys=True` to all `json.dumps()` calls in output paths             | `cli.py`                        | S          | JSON output is key-sorted                                                                         |
| Add `codetrellis clean` CLI command                                          | `cli.py`                        | S          | `codetrellis clean .` removes cache dir, returns exit 0                                           |

**Rollback:** Revert commits. No schema changes.  
**Estimated effort:** 2-3 days.

### Phase 1: Deterministic Compiler Core (Weeks 2-3)

**Goal:** Introduce builder/orchestrator, lockfile, per-extractor caching.

| Task                                                                                                                            | Files/Modules                  | Complexity | Acceptance Test                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ---------- | --------------------------------------------------------------------------------------- |
| Create `builder.py` — `MatrixBuilder` orchestrator class                                                                        | `codetrellis/builder.py` (NEW) | M          | `MatrixBuilder(project_root).build()` produces same outputs as current `scan_project()` |
| Create `cache.py` — `CacheManager`, `InputHashCalculator`, `LockfileManager`                                                    | `codetrellis/cache.py` (NEW)   | M          | Lockfile written with SHA-256 manifest of all inputs                                    |
| Define `IExtractor` protocol in `interfaces.py` — `name`, `version`, `input_patterns`, `depends_on`, `extract()`, `cache_key()` | `codetrellis/interfaces.py`    | M          | All existing extractors can be adapted to protocol                                      |
| Implement `_lockfile.json` generation and comparison                                                                            | `cache.py`                     | M          | `codetrellis scan` writes lockfile; second scan with no changes reads from cache        |
| Create `_build_log.jsonl` structured logging                                                                                    | `builder.py`                   | S          | JSONL file produced with build events                                                   |
| Wire `MatrixBuilder` into `cli.py scan_project()` as opt-in (`--use-builder`)                                                   | `cli.py`                       | S          | `codetrellis scan --use-builder .` produces correct output                              |

**Rollback:** Remove `--use-builder` flag; old path remains default.  
**Estimated effort:** 5-7 days.

### Phase 2: Incremental/Watch (Weeks 4-5)

**Goal:** Hash-based incremental rebuild, smart watch mode.

| Task                                                                             | Files/Modules | Complexity | Acceptance Test                                                                     |
| -------------------------------------------------------------------------------- | ------------- | ---------- | ----------------------------------------------------------------------------------- |
| Implement per-file hash tracking in `CacheManager`                               | `cache.py`    | M          | Cache stores `{file_path: {hash, extractors_run, results}}`                         |
| Implement diff engine — compare current file hashes vs lockfile                  | `cache.py`    | M          | `cache.get_changed_files()` returns only modified files                             |
| Implement selective extractor re-run — only run extractors for changed files     | `builder.py`  | L          | Changing 1 file re-runs only affected extractors, merges into existing matrix       |
| Implement matrix merge — patch existing `matrix.json` with new extractor results | `builder.py`  | M          | Merged output matches full-scan output for same inputs                              |
| Enhance `watcher.py` — connect to incremental builder instead of full scan       | `watcher.py`  | M          | Watch mode detects change, runs incremental, updates outputs in <2s for single file |
| Add `codetrellis scan --incremental` flag                                        | `cli.py`      | S          | Flag triggers incremental path                                                      |

**Rollback:** `--incremental` defaults to off; watch falls back to full scan.  
**Estimated effort:** 7-10 days.

### Phase 3: CI/CD + Quality Gates (Week 6)

**Goal:** CI-friendly modes, quality gates, SARIF-compatible output.

| Task                                                               | Files/Modules                        | Complexity | Acceptance Test                                                  |
| ------------------------------------------------------------------ | ------------------------------------ | ---------- | ---------------------------------------------------------------- |
| Add `--ci` profile flag (deterministic, parallel, exit codes)      | `cli.py`, `builder.py`               | S          | `codetrellis scan --ci .` exits 0/1 with machine-readable status |
| Add `--deterministic` flag that freezes timestamp and sorts output | `cli.py`                             | S          | Two runs produce byte-identical outputs                          |
| Implement quality gates — PASS/FAIL checks (see Section 9)         | `codetrellis/quality_gates.py` (NEW) | M          | `codetrellis verify .` runs gates, exits 0 on PASS, 1 on FAIL    |
| Add `codetrellis verify` CLI command                               | `cli.py`                             | S          | Command exists, runs quality checks                              |
| Generate `_build_report.json` with gate results                    | `quality_gates.py`                   | S          | Report file written with PASS/FAIL per gate                      |

**Rollback:** Remove `--ci` and `verify` commands.  
**Estimated effort:** 3-5 days.

### Phase 4: Performance Hardening (Week 7-8)

**Goal:** Default parallelism, memory optimization, profile presets.

| Task                                                                   | Files/Modules                | Complexity | Acceptance Test                                 |
| ---------------------------------------------------------------------- | ---------------------------- | ---------- | ----------------------------------------------- | --- | --------------------------------------------------------------------------- |
| Make parallel default for builds with >100 files                       | `builder.py`, `parallel.py`  | M          | Large projects auto-parallelize                 |
| Implement profile presets (`--profile dev                              | ci                           | deep`)     | `cli.py`, `builder.py`                          | M   | `--profile ci` equivalent to `--ci --parallel --deterministic --tier logic` |
| Memory-bounded extraction with `streaming.py` for projects >1000 files | `builder.py`, `streaming.py` | M          | Memory stays under 512MB for large projects     |
| Implement extractor dependency DAG with topological sort               | `builder.py`                 | L          | Extractors run in correct dependency order      |
| Cache warming — pre-populate cache for CI                              | `cache.py`                   | S          | `codetrellis cache-warm .` pre-hashes all files |
| Performance benchmarks                                                 | `tests/bench_*.py` (NEW)     | M          | Benchmark suite with timing assertions          |

**Rollback:** Disable parallelism default, revert to sequential.  
**Estimated effort:** 7-10 days.

---

## 6. Prioritized File-Level Actions

### 6.1 `cli.py` (1923 lines)

| #   | Why                       | Change                                                    | Test                                                 | Risk   |
| --- | ------------------------- | --------------------------------------------------------- | ---------------------------------------------------- | ------ |
| 1   | Version mismatch          | Sync `VERSION` import with `pyproject.toml` or vice versa | `assert __version__ == toml_version`                 | Low    |
| 2   | TODO on line 718          | Implement incremental sync in `watch_project()`           | Watch mode doesn't full-rescan on single file change | Medium |
| 3   | TODO on line 727          | Implement hash-based incremental in `sync_project()`      | `sync` command uses hashes                           | Medium |
| 4   | No `clean` command        | Add `codetrellis clean` subcommand                        | `clean` removes cache, exits 0                       | Low    |
| 5   | No `--ci` profile         | Add CI profile flag with deterministic output             | CI produces reproducible output                      | Low    |
| 6   | Timestamp non-determinism | Support `CODETRELLIS_BUILD_TIMESTAMP` env var             | Env var overrides `datetime.now()`                   | Low    |

### 6.2 `scanner.py` (18,797 lines)

| #   | Why                              | Change                                         | Test                                        | Risk   |
| --- | -------------------------------- | ---------------------------------------------- | ------------------------------------------- | ------ |
| 1   | Non-deterministic file order     | `sorted()` on `_walk_files()` output           | Two scans produce same order                | Low    |
| 2   | Monolithic `scan()` method       | Extract into `MatrixBuilder.build()` pipeline  | Builder produces same output                | High   |
| 3   | 60+ parsers instantiated eagerly | Lazy-load parsers based on detected file types | Only relevant parsers loaded                | Medium |
| 4   | No per-extractor caching         | Add cache check before each extractor call     | Cached results returned for unchanged files | Medium |

### 6.3 `progress_extractor.py`

| #   | Why             | Change                                           | Test                         | Risk   |
| --- | --------------- | ------------------------------------------------ | ---------------------------- | ------ |
| 1   | FIXME in file   | Address the FIXME (likely incomplete extraction) | Progress section is complete | Medium |
| 2   | 2 TODOs in file | Implement TODO items                             | Feature completeness         | Low    |

### 6.4 `todo_extractor.py`

| #   | Why             | Change               | Test                        | Risk |
| --- | --------------- | -------------------- | --------------------------- | ---- |
| 1   | 3 TODOs in file | Implement TODO items | All TODO patterns extracted | Low  |

### 6.5 `streaming.py` (661 lines)

| #   | Why                       | Change                                | Test                               | Risk   |
| --- | ------------------------- | ------------------------------------- | ---------------------------------- | ------ |
| 1   | Cache flag not wired      | Connect `use_cache` to `CacheManager` | Cached results used when available | Medium |
| 2   | `from_cache` field unused | Set `from_cache=True` on cache hits   | Stats show cache hit rate          | Low    |

### 6.6 `watcher.py` (284 lines)

| #   | Why                         | Change                                       | Test                                     | Risk |
| --- | --------------------------- | -------------------------------------------- | ---------------------------------------- | ---- |
| 1   | Full rescan on every change | Connect to incremental builder               | Single file change → incremental rebuild | High |
| 2   | Hardcoded extensions        | Use `FileClassifier` for extension detection | All supported extensions watched         | Low  |
| 3   | Test files excluded         | Make configurable via config.json            | Config-driven exclusion                  | Low  |

### 6.7 `runbook_extractor.py`

| #   | Why                                         | Change                                                       | Test                               | Risk |
| --- | ------------------------------------------- | ------------------------------------------------------------ | ---------------------------------- | ---- |
| 1   | Runbook may miss `codetrellis` own commands | Extract CLI commands from `pyproject.toml [project.scripts]` | Self-referential commands detected | Low  |

### 6.8 Cache/Version handling

| #   | Why                                                                         | Change                     | Test                            | Risk   |
| --- | --------------------------------------------------------------------------- | -------------------------- | ------------------------------- | ------ |
| 1   | Cache keyed by `__init__.__version__` (4.9.0) not `pyproject.toml` (4.16.0) | Unify version source       | Cache path uses correct version | High   |
| 2   | No lockfile                                                                 | Implement `_lockfile.json` | Lockfile written and validated  | Medium |
| 3   | No cache eviction                                                           | Add TTL or max-size policy | Old caches cleaned up           | Low    |

---

## 7. Runtime Upstream Prompt

See `docs/UPSTREAM_ANALYSIS_PROMPT.md` (separate file).

---

## 8. Save-Ready Artifacts

The following documents are produced alongside this plan:

1. `docs/MATRIX_AUTO_COMPILATION_PLAN.md` — this file
2. `docs/MATRIX_BUILD_CONTRACT.md` — formal build contract
3. `docs/UPSTREAM_ANALYSIS_PROMPT.md` — reusable AI prompt
4. `docs/MATRIX_QUALITY_GATES.md` — PASS/FAIL gate definitions

---

## 9. Quality Gates (Summary)

| Gate               | Criteria                                                           | PASS                                                                   | FAIL                               |
| ------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------- |
| **Build**          | All 3 output files written, exit code 0                            | Files exist, `_metadata.json` has `"success": true`                    | Any file missing or exit ≠ 0       |
| **Lint/Typecheck** | `ruff check`, `mypy` clean                                         | 0 errors                                                               | Any error                          |
| **Tests**          | `pytest` passes, >80% coverage on new code                         | All tests pass, coverage ≥ 80%                                         | Any test failure or coverage < 80% |
| **Determinism**    | Two consecutive builds with same inputs produce identical outputs  | `diff matrix.json matrix.json.2` exits 0                               | Any diff                           |
| **Incremental**    | Changing 1 file and rebuilding only touches that file's extractors | Build log shows ≤ N extractor runs (N = extractors for that file type) | Full rescan triggered              |

See `docs/MATRIX_QUALITY_GATES.md` for full definitions.

---

## 10. Command Matrix

```bash
# ── Local Full Compile ──
codetrellis scan . --optimal
# Or with explicit flags:
codetrellis scan . --tier logic --deep --parallel --include-progress --include-overview --include-practices

# ── Incremental Compile (Phase 2+) ──
codetrellis scan . --incremental
# <<REPLACE_HERE: Once builder.py is implemented, this will use hash-based diffing>>

# ── Watch Mode ──
codetrellis watch .
# <<REPLACE_HERE: Phase 2+ will use incremental engine instead of full rescan>>

# ── CI Mode (Phase 3+) ──
CODETRELLIS_CI=1 CODETRELLIS_BUILD_TIMESTAMP=2026-02-19T00:00:00 codetrellis scan . --ci
# <<REPLACE_HERE: --ci flag to be implemented in Phase 3>>
# Fallback until --ci exists:
CODETRELLIS_BUILD_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S) codetrellis scan . --optimal --parallel

# ── Deterministic Verification (Phase 3+) ──
codetrellis scan . --deterministic && cp .codetrellis/cache/*/*/matrix.json /tmp/m1.json
codetrellis scan . --deterministic && diff .codetrellis/cache/*/*/matrix.json /tmp/m1.json
# <<REPLACE_HERE: codetrellis verify --determinism will automate this in Phase 3>>

# ── Clean Rebuild ──
rm -rf .codetrellis/cache && codetrellis scan . --optimal
# <<REPLACE_HERE: codetrellis clean && codetrellis scan . in Phase 0+>>

# ── Validate Extraction ──
codetrellis validate .

# ── Show Progress ──
codetrellis progress . --detailed
```

---

## 11. Assumptions & Open Questions

### Assumptions

1. `__init__.py` version (4.9.0) is the runtime version; `pyproject.toml` (4.16.0) is the publish version. One must be corrected.
2. The 60+ parsers in `scanner.py` are all safe to run in parallel (no shared mutable state).
3. `watchdog` is an optional dependency — the plan preserves this.
4. The existing `parallel.py` `ProcessPoolExecutor` approach is sufficient (no need for async/multiprocess).
5. CI environments have Python ≥ 3.9 and no `JAVA_HOME`/`JDT_LS_PATH` unless `--deep` is used.

### Open Questions

1. **Q:** Should the lockfile include extractor _output_ hashes (for verification) or only _input_ hashes (for invalidation)?  
   **Recommendation:** Both — input hashes for invalidation, output hashes for determinism verification.
2. **Q:** Should the cache be shared across version upgrades (e.g., 4.9 → 4.10)?  
   **Recommendation:** No — version is part of the cache key, preventing stale data.
3. **Q:** What is the maximum acceptable incremental rebuild time?  
   **Recommendation:** <2s for single file change, <10s for batch of 50 files.
4. **Q:** Should `matrix.prompt` be generated from `matrix.json` (derived) or independently?  
   **Recommendation:** Derived — `matrix.json` is the source of truth, `matrix.prompt` is a compressed view.

---

## Immediate Next 3 Actions

1. **Fix version mismatch** — Update `codetrellis/__init__.py` to `__version__ = "4.16.0"` (or update `pyproject.toml` to `4.9.0`) and ensure cache paths are consistent.
2. **Add deterministic file traversal** — Wrap `_walk_files()` in `sorted()` in `scanner.py` and add `sort_keys=True` to JSON output.
3. **Create `codetrellis clean` command** — Simple CLI command to remove `.codetrellis/cache/` directory.

---

## 48-Hour Execution Checklist

- [ ] **Hour 0-2:** Fix version mismatch (`__init__.py` ↔ `pyproject.toml`)
- [ ] **Hour 2-4:** Add `sorted()` to `scanner._walk_files()`, add `sort_keys=True` to `json.dumps()` calls in `cli.py`
- [ ] **Hour 4-6:** Support `CODETRELLIS_BUILD_TIMESTAMP` env var for deterministic timestamps
- [ ] **Hour 6-8:** Add `codetrellis clean` CLI command
- [ ] **Hour 8-12:** Write `CacheManager` skeleton in `cache.py` with `InputHashCalculator`
- [ ] **Hour 12-16:** Implement `_lockfile.json` generation in `cache.py`
- [ ] **Hour 16-20:** Write `MatrixBuilder` skeleton in `builder.py` wrapping existing `scan_project()` flow
- [ ] **Hour 20-24:** Wire `MatrixBuilder` into CLI with `--use-builder` flag
- [ ] **Hour 24-30:** Write unit tests for `cache.py` and `builder.py`
- [ ] **Hour 30-36:** Run determinism verification (two builds, diff outputs)
- [ ] **Hour 36-42:** Address FIXME in `progress_extractor.py`, TODOs in `todo_extractor.py`
- [ ] **Hour 42-48:** Documentation review, commit, PR
