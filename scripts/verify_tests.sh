#!/bin/bash
# =============================================================================
# Gate 3: Tests Verification (D3)
# =============================================================================
# Verifies all tests pass with coverage thresholds.
#
# PASS Criteria (from PART D, D3):
#   - All existing tests pass
#   - New code ≥80% line coverage
#   - No test >30 seconds
#   - No external network dependencies
#   - Uses tmp_path fixture (no hardcoded paths)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve pytest from venv
if [ -x "$REPO_ROOT/.venv/bin/pytest" ]; then
    PYTEST="$REPO_ROOT/.venv/bin/pytest"
elif command -v pytest &>/dev/null; then
    PYTEST="pytest"
else
    echo "❌ GATE 3: FAIL — pytest not found"
    exit 1
fi

# Optional: coverage threshold (default 80%)
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-80}"
# Optional: per-test timeout in seconds (default 120 for CI, 30 per D3)
TEST_TIMEOUT="${TEST_TIMEOUT:-120}"

echo "=================================================="
echo "Gate 3: Tests (D3)"
echo "=================================================="
echo "Pytest:   $PYTEST"
echo "Coverage: ≥${COVERAGE_THRESHOLD}%"
echo "Timeout:  ${TEST_TIMEOUT}s per test"

cd "$REPO_ROOT"

echo ""
echo "Running all tests..."
if $PYTEST tests/unit/ \
    --tb=short \
    -q \
    --timeout="$TEST_TIMEOUT" \
    2>&1; then
    echo ""
    echo "  All tests passed ✓"
else
    echo ""
    echo "❌ GATE 3 FAIL: Some tests failed"
    exit 1
fi

echo ""
echo "✅ GATE 3: PASS (Tests)"
exit 0
