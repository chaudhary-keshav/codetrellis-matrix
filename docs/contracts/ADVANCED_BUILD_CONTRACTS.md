# CodeTrellis Advanced Build Contracts — PART H

## Overview

This document defines the formal I/O contracts for all 7 advanced research
modules (H1–H7) as specified in PART H of the
[CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md](../plan/auotcompile-plan/CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md).

Each contract specifies:

- **Inputs**: Required data and their types
- **Outputs**: Expected output format and structure
- **Error Behavior**: Exit code and error conditions
- **Caching Rules**: When to invalidate cached results
- **Determinism**: Reproducibility guarantees

## Exit Code Registry

| Code | Name                          | Module                        | Description                         |
| ---- | ----------------------------- | ----------------------------- | ----------------------------------- |
| 0    | SUCCESS                       | —                             | All outputs written successfully    |
| 1    | PARTIAL_FAILURE               | —                             | Some extractors failed              |
| 2    | CONFIGURATION_ERROR           | —                             | Configuration error                 |
| 3    | FATAL_ERROR                   | —                             | No outputs written                  |
| 41   | JSONLD_VALIDATION_FAILED      | `matrix_jsonld.py`            | JSON-LD output invalid              |
| 42   | EMBEDDING_GENERATION_FAILED   | `matrix_embeddings.py`        | Embedding index build failed        |
| 43   | JSON_PATCH_INTEGRITY_MISMATCH | `matrix_diff.py`              | Patch application hash mismatch     |
| 44   | COMPRESSION_AST_NODE_LOSS     | `matrix_compressor_levels.py` | Critical AST nodes dropped at L1/L2 |
| 45   | CROSS_LANGUAGE_ORPHANED_NODES | `cross_language_types.py`     | Orphaned cross-language references  |
| 46   | NAVIGATOR_QUERY_PARSE_FAILED  | `matrix_navigator.py`         | Query parsing/validation failed     |
| 47   | MATRIXBENCH_VARIANCE_EXCEEDED | `matrixbench_scorer.py`       | Benchmark variance > threshold      |
| 124  | TIMEOUT                       | —                             | Operation timed out                 |

---

## H1: JSON-LD Build Contract

**Module**: `codetrellis/matrix_jsonld.py`  
**Contract Class**: `JsonLdBuildContract`  
**Exit Code**: 41

### Inputs

| Parameter     | Type             | Required | Description               |
| ------------- | ---------------- | -------- | ------------------------- |
| matrix_json   | `Dict[str, Any]` | Yes      | Parsed matrix.json object |
| jsonld_output | `Dict[str, Any]` | Yes      | JSON-LD encoded output    |

### Output Schema

```json
{
  "@context": { "ct": "https://codetrellis.dev/", ... },
  "@type": "ct:Matrix",
  "@id": "ct:<project_name>",
  "@graph": [
    { "@id": "ct:<section>", "@type": "ct:<Type>", ... }
  ]
}
```

### Validation Rules

1. Output must be a valid JSON object (dict)
2. Must contain `@context` with `ct` namespace
3. Must contain `@type`
4. Must contain `@id` starting with `ct:`
5. Must contain `@graph` as a list
6. Every `@graph` node must have a unique `@id`
7. All `ct:depends` references must point to valid `@id`s
8. Token overhead ≤ 15% (warning if exceeded)

### Cache Key

- Hash of `matrix_json` + hash of `context_schema`
- Invalidates when either input changes

---

## H2: Embedding Index Build Contract

**Module**: `codetrellis/matrix_embeddings.py`  
**Contract Class**: `EmbeddingBuildContract`  
**Exit Code**: 42

### Inputs

| Parameter | Type                    | Required | Description                  |
| --------- | ----------------------- | -------- | ---------------------------- |
| sections  | `Dict[str, str]`        | Yes      | Section ID → content mapping |
| metadata  | `EmbeddingMetadata`     | Yes      | Build metadata from index    |
| vectors   | `Dict[str, np.ndarray]` | No       | Section ID → vector mapping  |

### Validation Rules

1. Metadata must not be `None`
2. `section_count` must match number of input sections
3. All vectors must be `numpy.ndarray` (not lists)
4. No `NaN` or `Inf` values in any vector
5. Vector dtype should be float (warning if not)
6. L2 norm should be ≈ 1.0 (warning if not normalized)

### Cache Key

- Per-section: hash of `section_id` + `content`
- Invalidates when section content changes

---

## H3: JSON Patch Build Contract

**Module**: `codetrellis/matrix_diff.py`  
**Contract Class**: `JsonPatchBuildContract`  
**Exit Code**: 43

### Inputs

| Parameter | Type                   | Required | Description               |
| --------- | ---------------------- | -------- | ------------------------- |
| base      | `Dict[str, Any]`       | Yes      | Base (old) matrix         |
| target    | `Dict[str, Any]`       | Yes      | Target (new) matrix       |
| patch_ops | `List[Dict[str, Any]]` | Yes      | RFC 6902 patch operations |

### Validation Rules

1. Identical inputs → empty patch (warning if non-empty)
2. Different inputs → non-empty patch
3. Each op must have valid `op` field (add/remove/replace/move/copy/test)
4. Each op must have `path` field
5. **Determinism**: `apply(base, patch) == target` verified by SHA-256
6. Hash mismatch → exit code 43

### Cache Key

- No caching — always computed from two inputs

### Determinism Guarantee

```
SHA-256(canonical(apply(base, patch))) == SHA-256(canonical(target))
```

---

## H4: Compression Levels Build Contract

**Module**: `codetrellis/matrix_compressor_levels.py`  
**Contract Class**: `CompressionBuildContract`  
**Exit Code**: 44

### Inputs

| Parameter  | Type  | Required | Description                         |
| ---------- | ----- | -------- | ----------------------------------- |
| original   | `str` | Yes      | Original matrix.prompt content      |
| compressed | `str` | Yes      | Compressed output                   |
| level      | `str` | Yes      | Compression level: "L1", "L2", "L3" |

### Validation Rules

1. **L1** (Full): Must be byte-identical to original
2. **L2** (Structural): All function/class signatures preserved; target ≤ 30,000 tokens
3. **L3** (Skeleton): Section headers preserved; target ≤ 10,000 tokens
4. Output must not be empty or whitespace-only

### Critical AST Patterns Checked

```
def <name>    class <name>    function <name>    interface <name>
struct <name>  enum <name>    trait <name>       protocol <name>
```

### Cache Key

- Hash of `prompt` + `level` + `config`
- Invalidates when any input changes

---

## H5: Cross-Language Merging Build Contract

**Module**: `codetrellis/cross_language_types.py`  
**Contract Class**: `CrossLanguageBuildContract`  
**Exit Code**: 45

### Inputs

| Parameter | Type                        | Required | Description                   |
| --------- | --------------------------- | -------- | ----------------------------- |
| fragments | `Dict[str, Dict[str, Any]]` | Yes      | Per-language matrix fragments |
| unified   | `UnifiedMatrix` or `Dict`   | Yes      | Merged matrix output          |

### Validation Rules

1. Must have ≥ 2 input fragments
2. Unified output must contain keys from all input fragments
3. Overhead ratio ≤ 150% (warning if exceeded)
4. Orphaned cross-language references → warning
5. Empty or missing links → warning

### Supported Languages

All 19 core languages + 53+ total languages/frameworks:

```
python, typescript, javascript, java, kotlin, csharp, rust, go, swift,
ruby, php, scala, dart, lua, r, c, cpp, powershell, bash
```

### Cache Key

- Combined hash of all fragment hashes (sorted by language key)
- Invalidates when any fragment changes

---

## H6: Matrix Navigator Build Contract

**Module**: `codetrellis/matrix_navigator.py`  
**Contract Class**: `NavigatorBuildContract`  
**Exit Code**: 46

### Inputs

| Parameter | Type           | Required | Description                   |
| --------- | -------------- | -------- | ----------------------------- |
| query     | `str`          | Yes      | User query (file/symbol name) |
| results   | `List[Result]` | Yes      | Ranked discovery results      |
| metrics   | `Metrics`      | No       | Performance metrics           |

### Validation Rules

1. Empty/whitespace query → must return empty results (not crash)
2. Results must be sorted by composite score (descending)
3. Each result must have a score field (`composite_score` or `score`)
4. Each result must have an ID field (`file_path` or `section_id`)
5. Latency > 300ms → warning
6. Score ≤ 0 → warning

### Cache Key

- Read-only against cached matrix.json (no write caching)

---

## H7: MatrixBench Build Contract

**Module**: `codetrellis/matrixbench_scorer.py`  
**Contract Class**: `MatrixBenchBuildContract`  
**Exit Code**: 47

### Inputs

| Parameter          | Type           | Required | Description                          |
| ------------------ | -------------- | -------- | ------------------------------------ |
| results_run1       | `BenchResults` | Yes      | First benchmark run results          |
| results_run2       | `BenchResults` | Yes      | Second benchmark run results         |
| variance_threshold | `float`        | No       | Max allowed variance (default: 2.0%) |

### Required Report Fields

```json
{
  "total_tasks": 20,
  "passed_tasks": 18,
  "total_latency_ms": 1234.5,
  "avg_improvement_pct": 50.0,
  "category_scores": {
    "completeness": 0.85,
    "accuracy": 0.9,
    "navigation": 0.8,
    "compression": 0.88,
    "cross_language": 0.75
  }
}
```

### Validation Rules

1. Both runs must produce non-None results
2. Results must contain `total_tasks`, `passed_tasks`, `total_latency_ms`
3. Results should contain `category_scores` with all 5 categories
4. **Determinism**: Variance between runs must be < threshold (default 2%)
5. Variance > threshold → exit code 47

### Cache Key

- No caching — benchmarks are always fresh runs

---

## Contract Suite Runner

The `AdvancedBuildContractSuite` class runs all 7 contracts end-to-end:

```python
from codetrellis.build_contracts_advanced import AdvancedBuildContractSuite

suite = AdvancedBuildContractSuite()
result = suite.run_all(
    matrix_json=matrix_json,
    matrix_prompt=matrix_prompt,
)

print(f"All passed: {result.all_passed}")
print(f"Duration: {result.total_duration_ms:.1f}ms")
for r in result.results:
    status = "PASS" if r.passed else "FAIL"
    print(f"  {status} {r.contract_id} (exit={r.exit_code})")
```

### CLI Entry Point

```bash
python -c "
from codetrellis.build_contracts_advanced import validate_advanced_contracts
import sys
sys.exit(validate_advanced_contracts(
    'path/to/matrix.json',
    'path/to/matrix.prompt',
))
"
```

---

## Smoke Tests (Phase 1)

Script: `scripts/smoke_test_build_contracts.sh`

| Check | Description                          | Target |
| ----- | ------------------------------------ | ------ |
| S1    | All modules importable               | < 2s   |
| S2    | JSON-LD contract with synthetic data | < 2s   |
| S3    | Embedding contract with synthetic    | < 2s   |
| S4    | JSON Patch contract with synthetic   | < 2s   |
| S5    | Compression contract with synthetic  | < 2s   |
| S6    | Cross-language contract              | < 2s   |
| S7    | Navigator contract                   | < 2s   |
| S8    | MatrixBench contract                 | < 2s   |

**Total target**: < 15 seconds

---

## Integration Tests (Phase 2)

Test file: `tests/integration/test_build_contracts_advanced.py`

### Test Classes

| Class                          | Contract | Tests |
| ------------------------------ | -------- | ----- |
| TestContractTypes              | Shared   | 6     |
| TestH1JsonLdContract           | H1       | 15    |
| TestH2EmbeddingContract        | H2       | 13    |
| TestH3JsonPatchContract        | H3       | 15    |
| TestH4CompressionContract      | H4       | 16    |
| TestH5CrossLanguageContract    | H5       | 12+19 |
| TestH6NavigatorContract        | H6       | 14    |
| TestH7MatrixBenchContract      | H7       | 13    |
| TestAdvancedBuildContractSuite | Suite    | 11    |
| TestExitCodeRegistry           | Codes    | 5     |
| TestCrossContractIntegration   | All      | 6     |

**Total**: 130+ tests (including parameterized per-language)

### Test Coverage Areas

- ✅ Happy path (valid inputs → pass)
- ✅ Edge cases (empty, minimal, boundary)
- ✅ Malformed inputs (missing fields, wrong types)
- ✅ Error behavior (correct exit codes)
- ✅ Cache behavior (determinism, invalidation)
- ✅ Determinism (SHA-256 verification)
- ✅ All 53+ languages (parameterized)

---

## File Map

```
codetrellis/
├── build_contract.py                  # ExitCode enum (codes 41-47 added)
├── build_contracts_advanced.py        # 7 contract validators + suite runner
├── matrix_jsonld.py                   # F1: JSON-LD encoder
├── matrix_embeddings.py               # F2: Embedding index
├── matrix_diff.py                     # F3: JSON Patch engine
├── matrix_compressor_levels.py        # F4: Multi-level compressor
├── cross_language_types.py            # F5: Cross-language linker
├── matrix_navigator.py               # F6: Matrix navigator
└── matrixbench_scorer.py              # F7: Benchmark suite

scripts/
└── smoke_test_build_contracts.sh      # Phase 1 smoke tests (S1-S8)

tests/integration/
├── test_advanced_gates.py             # Quality gates G1-G7 (existing)
└── test_build_contracts_advanced.py   # Build contracts H1-H7 (new)

docs/contracts/
└── ADVANCED_BUILD_CONTRACTS.md        # This document
```

---

_Created: Session 55 — PART H Implementation_  
_Author: Keshav Chaudhary_  
_CodeTrellis v4.67_
