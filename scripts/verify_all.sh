#!/bin/bash
# =============================================================================
# CodeTrellis Quality Gates — Master Verification Script (D6)
# =============================================================================
# Runs ALL quality gates (D1-D5) in sequence.
# Any gate failure stops the pipeline and reports the failing gate.
#
# Usage:
#   ./scripts/verify_all.sh [PROJECT_DIR]
#   ./scripts/verify_all.sh .
#   ./scripts/verify_all.sh --skip-lint     # Skip Gate 2 (useful locally)
#   ./scripts/verify_all.sh --skip-tests    # Skip Gate 3 (for quick checks)
#   ./scripts/verify_all.sh --gates 1,4,5   # Run only specific gates
#
# Exit Codes:
#   0 = All gates passed
#   1 = One or more gates failed
# =============================================================================
set -euo pipefail

PROJECT_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse flags
SKIP_LINT=false
SKIP_TESTS=false
SPECIFIC_GATES=""

for arg in "$@"; do
    case "$arg" in
        --skip-lint) SKIP_LINT=true ;;
        --skip-tests) SKIP_TESTS=true ;;
        --gates=*) SPECIFIC_GATES="${arg#--gates=}" ;;
        --gates) shift; SPECIFIC_GATES="${2:-}" ;;
    esac
done

# Helper: check if a gate should run
should_run_gate() {
    local gate_num="$1"
    if [ -n "$SPECIFIC_GATES" ]; then
        echo "$SPECIFIC_GATES" | grep -q "$gate_num"
        return $?
    fi
    return 0
}

TOTAL_GATES=0
PASSED_GATES=0
FAILED_GATES=0
SKIPPED_GATES=0
RESULTS=()

echo "================================================================"
echo " CodeTrellis Quality Gates — Master Verification (D1-D5)"
echo "================================================================"
echo " Project:  $PROJECT_DIR"
echo " Date:     $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================"
echo ""

# ── Gate 1: Build (D1) ──────────────────────────────────────────────
if should_run_gate 1; then
    TOTAL_GATES=$((TOTAL_GATES + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running Gate 1: Build (D1)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if bash "$SCRIPT_DIR/verify_build.sh" "$PROJECT_DIR"; then
        PASSED_GATES=$((PASSED_GATES + 1))
        RESULTS+=("Gate 1 (Build):       ✅ PASS")
    else
        FAILED_GATES=$((FAILED_GATES + 1))
        RESULTS+=("Gate 1 (Build):       ❌ FAIL")
        echo ""
        echo "❌ Gate 1 failed — stopping pipeline."
        # Print summary before exit
        echo ""
        echo "================================================================"
        echo " QUALITY GATES SUMMARY"
        echo "================================================================"
        for r in "${RESULTS[@]}"; do echo " $r"; done
        echo "================================================================"
        exit 1
    fi
    echo ""
fi

# ── Gate 2: Lint/Typecheck (D2) ─────────────────────────────────────
if should_run_gate 2 && [ "$SKIP_LINT" = false ]; then
    TOTAL_GATES=$((TOTAL_GATES + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running Gate 2: Lint/Typecheck (D2)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if bash "$SCRIPT_DIR/verify_lint.sh"; then
        PASSED_GATES=$((PASSED_GATES + 1))
        RESULTS+=("Gate 2 (Lint):        ✅ PASS")
    else
        FAILED_GATES=$((FAILED_GATES + 1))
        RESULTS+=("Gate 2 (Lint):        ❌ FAIL")
    fi
    echo ""
else
    SKIPPED_GATES=$((SKIPPED_GATES + 1))
    RESULTS+=("Gate 2 (Lint):        ⏭️ SKIP")
fi

# ── Gate 3: Tests (D3) ──────────────────────────────────────────────
if should_run_gate 3 && [ "$SKIP_TESTS" = false ]; then
    TOTAL_GATES=$((TOTAL_GATES + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running Gate 3: Tests (D3)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if bash "$SCRIPT_DIR/verify_tests.sh"; then
        PASSED_GATES=$((PASSED_GATES + 1))
        RESULTS+=("Gate 3 (Tests):       ✅ PASS")
    else
        FAILED_GATES=$((FAILED_GATES + 1))
        RESULTS+=("Gate 3 (Tests):       ❌ FAIL")
    fi
    echo ""
else
    SKIPPED_GATES=$((SKIPPED_GATES + 1))
    RESULTS+=("Gate 3 (Tests):       ⏭️ SKIP")
fi

# ── Gate 4: Determinism (D4) ────────────────────────────────────────
if should_run_gate 4; then
    TOTAL_GATES=$((TOTAL_GATES + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running Gate 4: Determinism (D4)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if bash "$SCRIPT_DIR/verify_determinism.sh" "$PROJECT_DIR"; then
        PASSED_GATES=$((PASSED_GATES + 1))
        RESULTS+=("Gate 4 (Determinism): ✅ PASS")
    else
        FAILED_GATES=$((FAILED_GATES + 1))
        RESULTS+=("Gate 4 (Determinism): ❌ FAIL")
    fi
    echo ""
fi

# ── Gate 5: Incremental Rebuild (D5) ────────────────────────────────
if should_run_gate 5; then
    TOTAL_GATES=$((TOTAL_GATES + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Running Gate 5: Incremental Rebuild (D5)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if bash "$SCRIPT_DIR/verify_incremental.sh" "$PROJECT_DIR"; then
        PASSED_GATES=$((PASSED_GATES + 1))
        RESULTS+=("Gate 5 (Incremental): ✅ PASS")
    else
        FAILED_GATES=$((FAILED_GATES + 1))
        RESULTS+=("Gate 5 (Incremental): ❌ FAIL")
    fi
    echo ""
fi

# ── Summary ─────────────────────────────────────────────────────────
echo "================================================================"
echo " QUALITY GATES SUMMARY"
echo "================================================================"
for r in "${RESULTS[@]}"; do
    echo " $r"
done
echo ""
echo " Total:   $TOTAL_GATES  |  Passed: $PASSED_GATES  |  Failed: $FAILED_GATES  |  Skipped: $SKIPPED_GATES"
echo "================================================================"

if [ "$FAILED_GATES" -gt 0 ]; then
    echo ""
    echo "❌ $FAILED_GATES gate(s) FAILED"
    exit 1
fi

echo ""
echo "🎉 ALL QUALITY GATES PASSED SUCCESSFULLY!"
exit 0
