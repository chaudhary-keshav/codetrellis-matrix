# Matrix Quality Gates

> **Version:** 1.0.0  
> **Date:** 19 February 2026  
> **Purpose:** Define PASS/FAIL criteria for every stage of matrix generation

---

## Gate 1: Build Gate

**When:** After every `codetrellis scan` execution  
**Command:** `codetrellis verify .`

### PASS Criteria

- [ ] Exit code is 0 or 1 (success or partial success)
- [ ] `matrix.prompt` exists and is non-empty (>100 bytes)
- [ ] `matrix.json` exists and is valid JSON
- [ ] `_metadata.json` exists and is valid JSON
- [ ] `_metadata.json` contains all required fields: `version`, `project`, `generated`, `stats`
- [ ] `_metadata.json.stats.totalFiles` > 0
- [ ] `matrix.json` can be deserialized without errors
- [ ] `matrix.prompt` contains at least `[PROJECT]` section header
- [ ] Version in `_metadata.json` matches `codetrellis.__version__`

### FAIL Criteria

- Any required output file is missing
- Exit code ≥ 2 (configuration or fatal error)
- `_metadata.json` is invalid JSON
- `_metadata.json.stats.totalFiles` is 0 when project has files
- Version mismatch between `_metadata.json.version` and installed CodeTrellis version

### Verification Script

```python
import json
from pathlib import Path

def verify_build(cache_dir: Path) -> tuple[bool, list[str]]:
    """Verify build gate. Returns (passed, errors)."""
    errors = []

    # Check files exist
    for fname in ['matrix.prompt', 'matrix.json', '_metadata.json']:
        fpath = cache_dir / fname
        if not fpath.exists():
            errors.append(f"MISSING: {fname}")
        elif fpath.stat().st_size == 0:
            errors.append(f"EMPTY: {fname}")

    # Check JSON validity
    for fname in ['matrix.json', '_metadata.json']:
        fpath = cache_dir / fname
        if fpath.exists():
            try:
                json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"INVALID_JSON: {fname}: {e}")

    # Check metadata fields
    meta_path = cache_dir / '_metadata.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for field in ['version', 'project', 'generated', 'stats']:
            if field not in meta:
                errors.append(f"MISSING_FIELD: _metadata.json.{field}")

        stats = meta.get('stats', {})
        if stats.get('totalFiles', 0) == 0:
            errors.append("ZERO_FILES: No files scanned")

    # Check prompt has sections
    prompt_path = cache_dir / 'matrix.prompt'
    if prompt_path.exists():
        content = prompt_path.read_text()
        if '[PROJECT]' not in content:
            errors.append("MISSING_SECTION: [PROJECT] not found in matrix.prompt")

    return (len(errors) == 0, errors)
```

---

## Gate 2: Lint/Typecheck Gate

**When:** Before committing changes to CodeTrellis source  
**Applies to:** CodeTrellis development, not matrix consumers

### PASS Criteria

- [ ] `ruff check codetrellis/` exits with 0 errors
- [ ] `mypy codetrellis/ --ignore-missing-imports` exits with 0 errors
- [ ] No unused imports in modified files
- [ ] No `# type: ignore` without justification comment

### FAIL Criteria

- Any `ruff` error (not warning)
- Any `mypy` error (not note)
- New `# type: ignore` without `# reason: ...` comment

### Commands

```bash
# Lint
ruff check codetrellis/ --select E,F,W

# Type check
mypy codetrellis/ --ignore-missing-imports --no-error-summary

# Auto-fix safe issues
ruff check codetrellis/ --fix
```

---

## Gate 3: Test Gate

**When:** Before merging PRs, in CI  
**Command:** `pytest tests/ -v --tb=short`

### PASS Criteria

- [ ] All existing tests pass (0 failures)
- [ ] New code has ≥80% line coverage
- [ ] No test takes longer than 30 seconds
- [ ] No test depends on external network (mocked)
- [ ] No test depends on specific file system paths (uses `tmp_path` fixture)

### FAIL Criteria

- Any test failure
- Coverage of new code <80%
- Test timeout >30s
- Flaky test detected (passes/fails non-deterministically)

### Commands

```bash
# Run all tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ -v --cov=codetrellis --cov-report=term-missing

# Run specific test file
pytest tests/test_scanner.py -v

# Run with coverage threshold
pytest tests/ --cov=codetrellis --cov-fail-under=80
```

---

## Gate 4: Determinism Gate

**When:** Phase 1+ (after deterministic build support is implemented)  
**Command:** `codetrellis verify --determinism .`

### PASS Criteria

- [ ] Two consecutive builds with identical inputs produce byte-identical `matrix.json`
- [ ] Two consecutive builds with identical inputs produce byte-identical `matrix.prompt`
- [ ] Two consecutive builds with identical inputs produce byte-identical `_metadata.json` (with `CODETRELLIS_BUILD_TIMESTAMP` set)
- [ ] JSON keys are sorted (`sort_keys=True`)
- [ ] File traversal order is deterministic
- [ ] No random/time-dependent values in output (except `generated_at` which is overridable)

### FAIL Criteria

- Any byte-level difference between two builds with same inputs and fixed timestamp
- Unsorted JSON keys
- Non-deterministic list ordering

### Verification Script

```bash
#!/bin/bash
set -euo pipefail

TIMESTAMP="2026-01-01T00:00:00"
PROJECT_DIR="${1:-.}"
CACHE_DIR=$(python -c "from codetrellis.cli import get_cache_dir; from pathlib import Path; print(get_cache_dir(Path('$PROJECT_DIR').resolve()))")

# Build 1
CODETRELLIS_BUILD_TIMESTAMP="$TIMESTAMP" codetrellis scan "$PROJECT_DIR" --deterministic
cp "$CACHE_DIR/matrix.json" /tmp/ct_det_1.json
cp "$CACHE_DIR/matrix.prompt" /tmp/ct_det_1.prompt
cp "$CACHE_DIR/_metadata.json" /tmp/ct_det_1_meta.json

# Build 2
CODETRELLIS_BUILD_TIMESTAMP="$TIMESTAMP" codetrellis scan "$PROJECT_DIR" --deterministic
cp "$CACHE_DIR/matrix.json" /tmp/ct_det_2.json
cp "$CACHE_DIR/matrix.prompt" /tmp/ct_det_2.prompt
cp "$CACHE_DIR/_metadata.json" /tmp/ct_det_2_meta.json

# Compare
PASS=true
for suffix in json prompt _meta.json; do
    if ! diff -q "/tmp/ct_det_1.$suffix" "/tmp/ct_det_2.$suffix" > /dev/null 2>&1; then
        # Handle the filename mapping
        f1="/tmp/ct_det_1.${suffix}"
        f2="/tmp/ct_det_2.${suffix}"
        if [ -f "$f1" ] && [ -f "$f2" ]; then
            echo "❌ FAIL: $suffix differs"
            diff "$f1" "$f2" | head -20
            PASS=false
        fi
    fi
done

if [ "$PASS" = true ]; then
    echo "✅ DETERMINISM GATE: PASS"
    exit 0
else
    echo "❌ DETERMINISM GATE: FAIL"
    exit 1
fi
```

---

## Gate 5: Incremental Rebuild Gate

**When:** Phase 2+ (after incremental build support is implemented)  
**Command:** `codetrellis verify --incremental .`

### PASS Criteria

- [ ] Changing 1 file triggers rebuild of only affected extractors
- [ ] Build log (`_build_log.jsonl`) shows ≤ N extractor runs (where N = extractors applicable to the changed file's type)
- [ ] Incremental output is identical to full rebuild output
- [ ] Incremental build time is ≤ 20% of full build time for single-file changes
- [ ] Unchanged files are served from cache (build log shows `from_cache: true`)
- [ ] Lockfile is updated with new file hash after incremental build

### FAIL Criteria

- Full rescan triggered on single-file change
- Incremental output differs from full rebuild output (correctness violation)
- All extractors re-run for a single-file change
- Cache misses for unchanged files
- Lockfile not updated

### Verification Script

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
CACHE_DIR=$(python -c "from codetrellis.cli import get_cache_dir; from pathlib import Path; print(get_cache_dir(Path('$PROJECT_DIR').resolve()))")

# Full build (baseline)
codetrellis scan "$PROJECT_DIR" --optimal
cp "$CACHE_DIR/matrix.json" /tmp/ct_full.json

# Touch one file
FIRST_PY=$(find "$PROJECT_DIR" -name "*.py" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" | head -1)
touch "$FIRST_PY"

# Incremental build
# <<REPLACE_HERE: Use --incremental flag once implemented>>
codetrellis scan "$PROJECT_DIR" --incremental

# Compare output
cp "$CACHE_DIR/matrix.json" /tmp/ct_incr.json

# The outputs should be functionally equivalent
# (may differ in build timing metadata)
python3 -c "
import json
full = json.loads(open('/tmp/ct_full.json').read())
incr = json.loads(open('/tmp/ct_incr.json').read())
# Remove timing fields
for d in [full, incr]:
    d.pop('generated_at', None)
assert full == incr, 'Incremental output differs from full build!'
print('✅ INCREMENTAL GATE: PASS')
"
```

---

## Gate Summary Matrix

| Gate           | Phase   | Automated | CI Required    | Blocking                    |
| -------------- | ------- | --------- | -------------- | --------------------------- |
| Build          | 0 (now) | Yes       | Yes            | Yes                         |
| Lint/Typecheck | 0 (now) | Yes       | Yes            | Yes                         |
| Tests          | 0 (now) | Yes       | Yes            | Yes                         |
| Determinism    | 1       | Yes       | Yes            | No (advisory until Phase 3) |
| Incremental    | 2       | Yes       | No (local dev) | No (advisory until Phase 4) |

---

## CI Integration

### GitHub Actions Example

```yaml
name: CodeTrellis Quality Gates
on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install
        run: pip install -e ".[dev]"

      - name: Gate 2 - Lint
        run: ruff check codetrellis/ --select E,F,W

      - name: Gate 2 - Typecheck
        run: mypy codetrellis/ --ignore-missing-imports

      - name: Gate 3 - Tests
        run: pytest tests/ -v --cov=codetrellis --cov-fail-under=80

      - name: Gate 1 - Build (self-scan)
        run: |
          CODETRELLIS_BUILD_TIMESTAMP="2026-01-01T00:00:00" codetrellis scan . --optimal
          codetrellis verify .

      - name: Gate 4 - Determinism
        run: |
          # Second build should be identical
          CODETRELLIS_BUILD_TIMESTAMP="2026-01-01T00:00:00" codetrellis scan . --optimal
          # <<REPLACE_HERE: codetrellis verify --determinism . once implemented>>
```
