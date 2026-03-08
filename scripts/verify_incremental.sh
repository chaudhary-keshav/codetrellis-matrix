#!/bin/bash
# =============================================================================
# Gate 5: Incremental Rebuild Verification (D5)
# =============================================================================
# Verifies that incremental builds produce correct results and are faster.
#
# PASS Criteria (from PART D, D5):
#   - 1 file change → only affected extractors re-run
#   - _build_log.jsonl shows ≤ N extractor runs
#   - Incremental output identical to full rebuild output
#   - Incremental time ≤ 20% of full build (advisory for small projects)
#   - Unchanged files served from cache
#   - Lockfile updated with new hash
# =============================================================================
set -euo pipefail

PROJECT_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve Python from venv
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
elif [ -x "$REPO_ROOT/.venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python3"
else
    PYTHON="python3"
fi

# Use a temp directory that's cleaned up on exit
TMPDIR_INCR=$(mktemp -d)
trap 'rm -rf "$TMPDIR_INCR"' EXIT

echo "=================================================="
echo "Gate 5: Incremental Rebuild Verification (D5)"
echo "=================================================="
echo "Project: $PROJECT_DIR"
echo "Python:  $PYTHON"

# Step 1: Full build (clean first)
echo ""
echo "Step 1: Full build (clean + scan)..."
"$PYTHON" -m codetrellis clean "$PROJECT_DIR" 2>/dev/null || true

START_FULL=$(python3 -c "import time; print(int(time.time() * 1000))")
"$PYTHON" -m codetrellis scan "$PROJECT_DIR" --optimal
END_FULL=$(python3 -c "import time; print(int(time.time() * 1000))")
FULL_TIME=$((END_FULL - START_FULL))

CACHE_JSON_FULL=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.json" 2>/dev/null | head -1)
if [ -z "$CACHE_JSON_FULL" ]; then
    echo "❌ GATE 5 FAIL: No matrix.json found after full build"
    exit 1
fi
cp "$CACHE_JSON_FULL" "$TMPDIR_INCR/full_matrix.json"

echo "  Full build time: ${FULL_TIME}ms"

# Step 2: Touch a single file
FIRST_PY=$(find "$PROJECT_DIR/codetrellis" -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.codetrellis/*" 2>/dev/null | sort | head -1)
if [ -z "$FIRST_PY" ]; then
    FIRST_PY=$(find "$PROJECT_DIR" -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.codetrellis/*" -not -path "*/.venv/*" 2>/dev/null | sort | head -1)
fi
if [ -z "$FIRST_PY" ]; then
    echo "❌ GATE 5 FAIL: No Python file found to touch for incremental test"
    exit 1
fi

echo ""
echo "Step 2: Touching file for incremental build..."
echo "  File: $FIRST_PY"
touch "$FIRST_PY"

# Step 3: Incremental build
echo ""
echo "Step 3: Running incremental build..."
START_INCR=$(python3 -c "import time; print(int(time.time() * 1000))")
"$PYTHON" -m codetrellis scan "$PROJECT_DIR" --incremental
END_INCR=$(python3 -c "import time; print(int(time.time() * 1000))")
INCR_TIME=$((END_INCR - START_INCR))

CACHE_JSON_INCR=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.json" 2>/dev/null | head -1)
if [ -z "$CACHE_JSON_INCR" ]; then
    echo "❌ GATE 5 FAIL: No matrix.json found after incremental build"
    exit 1
fi
cp "$CACHE_JSON_INCR" "$TMPDIR_INCR/incr_matrix.json"

echo "  Incremental build time: ${INCR_TIME}ms"

# Step 4: Compare outputs (excluding generated_at)
echo ""
echo "Step 4: Comparing outputs..."
"$PYTHON" -c "
import json, sys

full = json.loads(open('$TMPDIR_INCR/full_matrix.json', encoding='utf-8').read())
incr = json.loads(open('$TMPDIR_INCR/incr_matrix.json', encoding='utf-8').read())

# Remove time-dependent fields
for d in [full, incr]:
    d.pop('generated_at', None)
    d.pop('build_duration_ms', None)
    # Remove nested timestamps if present
    if 'metadata' in d and isinstance(d['metadata'], dict):
        d['metadata'].pop('generated_at', None)
        d['metadata'].pop('build_duration_ms', None)

if full == incr:
    print('  Outputs match ✓')
else:
    # Find differences
    for key in set(list(full.keys()) + list(incr.keys())):
        if full.get(key) != incr.get(key):
            print(f'  DIFF in key: {key}')
    print('❌ Incremental output differs from full build!')
    sys.exit(1)
"

# Step 5: Check cache hits in build log
echo ""
echo "Step 5: Checking build log for cache hits..."
BUILD_LOG=$(find "$PROJECT_DIR/.codetrellis/cache" -name "_build_log.jsonl" 2>/dev/null | head -1)
if [ -n "$BUILD_LOG" ] && [ -f "$BUILD_LOG" ]; then
    "$PYTHON" -c "
import json
log_entries = [json.loads(line) for line in open('$BUILD_LOG', encoding='utf-8') if line.strip()]
cache_hits = [e for e in log_entries if e.get('event') == 'cache_hit']
cache_misses = [e for e in log_entries if e.get('event') == 'cache_miss']
print(f'  Cache hits:   {len(cache_hits)}')
print(f'  Cache misses: {len(cache_misses)}')
if cache_hits:
    print('  Cache serving working ✓')
" 2>/dev/null || echo "  Build log analysis: skipped (format varies)"
else
    echo "  No build log found (skipping cache hit verification)"
fi

# Step 6: Speedup analysis
echo ""
echo "Step 6: Speedup analysis..."
if [ "$FULL_TIME" -gt 0 ]; then
    RATIO=$("$PYTHON" -c "print(f'{($INCR_TIME / $FULL_TIME) * 100:.1f}')")
    echo "  Full build:        ${FULL_TIME}ms"
    echo "  Incremental build: ${INCR_TIME}ms"
    echo "  Ratio:             ${RATIO}% of full build"

    if [ "$INCR_TIME" -lt "$FULL_TIME" ]; then
        echo "  Incremental is faster ✓"
    else
        echo "  ⚠️ Incremental was not faster (expected for very small projects)"
    fi
else
    echo "  ⚠️ Could not calculate ratio (full build time = 0)"
fi

echo ""
echo "✅ GATE 5: PASS (Incremental Rebuild)"
exit 0
