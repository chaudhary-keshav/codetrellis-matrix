#!/bin/bash
# =============================================================================
# Gate 1: Build Verification (D1)
# =============================================================================
# Verifies that `codetrellis scan` produces valid, non-empty outputs.
#
# PASS Criteria (from PART D, D1):
#   - Exit code is 0 or 1
#   - matrix.prompt exists and is non-empty (>100 bytes)
#   - matrix.json is valid JSON
#   - _metadata.json is valid JSON with version, project, generated, stats
#   - _metadata.json.stats.totalFiles > 0
#   - matrix.prompt contains [PROJECT] section header
#   - Version in _metadata.json matches codetrellis.__version__
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

echo "=================================================="
echo "Gate 1: Build Verification (D1)"
echo "=================================================="
echo "Project: $PROJECT_DIR"
echo "Python:  $PYTHON"

# Step 1: Run build
echo ""
echo "Step 1: Running codetrellis scan..."
CODETRELLIS_BUILD_TIMESTAMP="2026-01-01T00:00:00" \
    "$PYTHON" -m codetrellis scan "$PROJECT_DIR" --optimal
SCAN_EXIT=$?

if [ "$SCAN_EXIT" -gt 1 ]; then
    echo "❌ GATE 1 FAIL: codetrellis scan exited with code $SCAN_EXIT (expected 0 or 1)"
    exit 1
fi
echo "  scan exit code: $SCAN_EXIT ✓"

# Step 2: Verify outputs exist
echo ""
echo "Step 2: Verifying output files..."

CACHE_DIR=$(find "$PROJECT_DIR/.codetrellis/cache" -type d -mindepth 2 -maxdepth 2 2>/dev/null | head -1)
if [ -z "$CACHE_DIR" ]; then
    echo "❌ GATE 1 FAIL: No cache directory found"
    exit 1
fi
echo "  Cache dir: $CACHE_DIR"

# Step 3: Run Python verification
echo ""
echo "Step 3: Running contract verification..."
"$PYTHON" -c "
import json, sys
from pathlib import Path

cache_dir = Path('$CACHE_DIR')
errors = []

# Check files exist and are non-empty
for fname in ['matrix.prompt', 'matrix.json', '_metadata.json']:
    fpath = cache_dir / fname
    if not fpath.exists():
        errors.append(f'MISSING: {fname}')
    elif fpath.stat().st_size == 0:
        errors.append(f'EMPTY: {fname}')

# matrix.prompt > 100 bytes
prompt_path = cache_dir / 'matrix.prompt'
if prompt_path.exists() and prompt_path.stat().st_size <= 100:
    errors.append(f'TOO_SMALL: matrix.prompt is {prompt_path.stat().st_size} bytes (need >100)')

# JSON validity
for fname in ['matrix.json', '_metadata.json']:
    fpath = cache_dir / fname
    if fpath.exists():
        try:
            json.loads(fpath.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            errors.append(f'INVALID_JSON: {fname}: {e}')

# _metadata.json fields
meta_path = cache_dir / '_metadata.json'
if meta_path.exists():
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    for field in ['version', 'project', 'generated', 'stats']:
        if field not in meta:
            errors.append(f'MISSING_FIELD: _metadata.json.{field}')
    if meta.get('stats', {}).get('totalFiles', 0) == 0:
        errors.append('ZERO_FILES: No files scanned')

    # Version match
    try:
        import codetrellis
        if meta.get('version') != codetrellis.__version__:
            errors.append(f'VERSION_MISMATCH: metadata={meta.get(\"version\")} vs package={codetrellis.__version__}')
    except ImportError:
        pass  # Skip if not importable

# [PROJECT] section header
if prompt_path.exists():
    content = prompt_path.read_text(encoding='utf-8')
    if '[PROJECT]' not in content:
        errors.append('MISSING_SECTION: [PROJECT] not found in matrix.prompt')

if errors:
    for e in errors:
        print(f'  ERROR: {e}')
    sys.exit(1)
else:
    print('  All checks passed ✓')
"

echo ""
echo "✅ GATE 1: PASS (Build)"
exit 0
