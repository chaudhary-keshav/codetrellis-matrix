# Modularization Design Note — scanner.py & compressor.py

> Phase 5.1 of the v5.0 Improvement Plan
> Date: 9 March 2026

## Current Size

| Module          | LOC    | Methods | Core Methods          |
| --------------- | ------ | ------- | --------------------- |
| `scanner.py`    | 25,919 | 143     | 107 `_parse_*`        |
| `compressor.py` | 28,415 | 449     | 419 `_compress_*`     |
| **Total**       | 54,334 | 592     | 526 language-dispatch |

Both exceed the 10K LOC threshold by 2.5–2.8×.

## Internal Seams

Both modules follow the same structural pattern: a thin orchestration layer
that dispatches to **per-language/framework private methods**.

### scanner.py

```
ProjectScanner
├── scan()                     # orchestrator (~200 LOC)
├── _parse_file()              # file-type dispatcher (~300 LOC)
├── _parse_python()            # ┐
├── _parse_typescript()        # │
├── _parse_java()              # │ 107 language-specific methods
├── _parse_csharp()            # │ each ~100-300 LOC
├── _parse_go()                # │
├── ...                        # ┘
└── _scan_*() / _extract_*()   # cross-cutting extraction
```

### compressor.py

```
MatrixCompressor
├── compress()                 # orchestrator (~400 LOC)
├── _compress_python_*()       # ┐
├── _compress_typescript_*()   # │ 419 compression methods
├── _compress_java_*()         # │ each ~20-60 LOC
├── ...                        # ┘
└── _compress_single_*()       # shared helpers
```

## Lowest-Risk Extraction Candidates

### Tier 1: Mechanical, per-language split (lowest risk)

Each `_parse_<lang>()` in scanner.py and `_compress_<lang>_*()` group in
compressor.py are self-contained with no cross-language dependencies.
The split would be:

```
codetrellis/
├── scanner.py              → core orchestration only (~500 LOC)
├── scanners/
│   ├── __init__.py
│   ├── python.py           ← _parse_python()
│   ├── typescript.py       ← _parse_typescript()
│   ├── java.py             ← _parse_java()
│   └── ...                 ← one file per language
├── compressor.py           → core orchestration only (~800 LOC)
├── compressors/
│   ├── __init__.py
│   ├── python.py           ← _compress_python_*()
│   ├── typescript.py       ← _compress_typescript_*()
│   └── ...
```

**Risk**: Low. Methods are already isolated. Main risk is getting the
`ProjectMatrix` imports right and ensuring the dispatcher still calls
methods correctly.

**Effort**: Mechanical — each language group is a cut-paste into a new file
with a class or module-level functions. Could be partially automated.

### Tier 2: Cross-cutting extractors (medium risk)

Methods like `_parse_schema()`, `_parse_dto()`, `_parse_controller()`,
`_parse_routes()` handle generic patterns across multiple languages.
These should stay in the core scanner until language-specific methods
are extracted first.

### Tier 3: Orchestration refactor (higher risk, not recommended now)

Rewriting the `scan()` / `compress()` dispatch logic. Not worth the risk
given the current test coverage and stable behavior.

## Recommendation

**Do not split now.** The current monolith structure is stable with 6,775
passing tests and no merge-conflict pressure (single-developer workflow).

### Trigger for future modularization

Split when **any** of these conditions are met:

1. **Multi-contributor**: 2+ developers regularly editing scanner/compressor
2. **LOC growth**: Either file exceeds 35K LOC (current: 26K / 28K)
3. **New language batch**: Adding 10+ new languages in one release
4. **IDE performance**: Editor tooling becomes slow on 25K+ LOC files

### First slice when triggered

Start with **Tier 1** for the 5 largest language groups by method count:
Python, TypeScript/JavaScript, Java, C#, Go. This covers ~40% of the
methods and can be validated with the existing test suite per-language.

The matrixbench scorer (baseline: 90.0%) should be run before and after
any split to verify no quality regression.
