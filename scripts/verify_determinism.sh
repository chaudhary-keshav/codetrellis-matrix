#!/bin/bash
# =============================================================================
# Gate 4: Determinism Verification (D4)
# =============================================================================
# Verifies two consecutive builds with identical inputs produce
# byte-identical outputs (SHA-256 match).
#
# PASS Criteria (from PART D, D4):
#   - Two consecutive builds with identical inputs → byte-identical outputs
#   - JSON keys sorted
#   - File traversal deterministic
#   - No random/time-dependent values (except overridable generated_at)
# =============================================================================
set -euo pipefail

PROJECT_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP="2026-01-01T00:00:00"

# Resolve Python from venv
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
elif [ -x "$REPO_ROOT/.venv/bin/python3" ]; then
    PYTHON="$REPO_ROOT/.venv/bin/python3"
else
    PYTHON="python3"
fi

# Use a temp directory that's cleaned up on exit
TMPDIR_DET=$(mktemp -d)
trap 'rm -rf "$TMPDIR_DET"' EXIT

echo "=================================================="
echo "Gate 4: Determinism Verification (D4)"
echo "=================================================="
echo "Project:   $PROJECT_DIR"
echo "Python:    $PYTHON"
echo "Timestamp: $TIMESTAMP"

# Build 1
echo ""
echo "Build 1: Clean + scan..."
"$PYTHON" -m codetrellis clean "$PROJECT_DIR" 2>/dev/null || true
CODETRELLIS_BUILD_TIMESTAMP="$TIMESTAMP" \
    "$PYTHON" -m codetrellis scan "$PROJECT_DIR" --deterministic --optimal

CACHE_JSON_1=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.json" 2>/dev/null | head -1)
CACHE_PROMPT_1=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.prompt" 2>/dev/null | head -1)

if [ -z "$CACHE_JSON_1" ]; then
    echo "❌ GATE 4 FAIL: No matrix.json found after Build 1"
    exit 1
fi

cp "$CACHE_JSON_1" "$TMPDIR_DET/build1_matrix.json"
cp "$CACHE_PROMPT_1" "$TMPDIR_DET/build1_matrix.prompt"

# Build 2
echo ""
echo "Build 2: Clean + scan..."
"$PYTHON" -m codetrellis clean "$PROJECT_DIR" 2>/dev/null || true
CODETRELLIS_BUILD_TIMESTAMP="$TIMESTAMP" \
    "$PYTHON" -m codetrellis scan "$PROJECT_DIR" --deterministic --optimal

CACHE_JSON_2=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.json" 2>/dev/null | head -1)
CACHE_PROMPT_2=$(find "$PROJECT_DIR/.codetrellis/cache" -name "matrix.prompt" 2>/dev/null | head -1)

if [ -z "$CACHE_JSON_2" ]; then
    echo "❌ GATE 4 FAIL: No matrix.json found after Build 2"
    exit 1
fi

cp "$CACHE_JSON_2" "$TMPDIR_DET/build2_matrix.json"
cp "$CACHE_PROMPT_2" "$TMPDIR_DET/build2_matrix.prompt"

# Compare matrix.json (SHA-256)
echo ""
echo "Comparing matrix.json..."
SHA_JSON_1=$(shasum -a 256 "$TMPDIR_DET/build1_matrix.json" | awk '{print $1}')
SHA_JSON_2=$(shasum -a 256 "$TMPDIR_DET/build2_matrix.json" | awk '{print $1}')
echo "  Build 1 SHA-256: $SHA_JSON_1"
echo "  Build 2 SHA-256: $SHA_JSON_2"

if [ "$SHA_JSON_1" != "$SHA_JSON_2" ]; then
    echo "❌ GATE 4 FAIL: matrix.json SHA-256 mismatch!"
    echo ""
    echo "Diff (first 30 lines):"
    diff "$TMPDIR_DET/build1_matrix.json" "$TMPDIR_DET/build2_matrix.json" | head -30
    exit 1
fi
echo "  matrix.json: MATCH ✓"

# Compare matrix.prompt (SHA-256)
echo ""
echo "Comparing matrix.prompt..."
SHA_PROMPT_1=$(shasum -a 256 "$TMPDIR_DET/build1_matrix.prompt" | awk '{print $1}')
SHA_PROMPT_2=$(shasum -a 256 "$TMPDIR_DET/build2_matrix.prompt" | awk '{print $1}')
echo "  Build 1 SHA-256: $SHA_PROMPT_1"
echo "  Build 2 SHA-256: $SHA_PROMPT_2"

if [ "$SHA_PROMPT_1" != "$SHA_PROMPT_2" ]; then
    echo "❌ GATE 4 FAIL: matrix.prompt SHA-256 mismatch!"
    echo ""
    echo "Diff (first 30 lines):"
    diff "$TMPDIR_DET/build1_matrix.prompt" "$TMPDIR_DET/build2_matrix.prompt" | head -30
    exit 1
fi
echo "  matrix.prompt: MATCH ✓"

# Verify JSON keys are sorted
echo ""
echo "Verifying JSON key ordering..."
"$PYTHON" -c "
import json, sys
data = json.loads(open('$TMPDIR_DET/build2_matrix.json', encoding='utf-8').read())
if isinstance(data, dict):
    keys = list(data.keys())
    if keys != sorted(keys):
        print(f'  ERROR: Top-level keys not sorted: {keys[:5]}...')
        sys.exit(1)
    print('  JSON keys sorted ✓')
"

echo ""
echo "✅ GATE 4: PASS (Determinism)"
echo "  matrix.json SHA-256:  $SHA_JSON_1"
echo "  matrix.prompt SHA-256: $SHA_PROMPT_1"
exit 0
