#!/usr/bin/env bash
# ============================================================================
# CodeTrellis Appendices — Smoke Test Suite (PART J)
# ============================================================================
# Fast sanity checks for all PART J deliverables:
#   J1 — Token Budget Validator
#   J2 — File Manifest Auditor
#   J3 — Cross-Topic Synergy (basic import check)
#   J4 — Citations document
#
# Target: Complete in < 5 seconds, exit code 0.
#
# Usage:
#   ./scripts/smoke_test_appendices.sh
#   bash scripts/smoke_test_appendices.sh
#
# Reference: CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md — PART J
# Author: Keshav Chaudhary
# Created: 20 February 2026
# ============================================================================

set -euo pipefail

# Resolve project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Use venv python if available, else system
PYTHON="${PROJECT_ROOT}/.venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

PASS=0
FAIL=0
TOTAL=0
START_TIME=$(date +%s)
ERRORS=""

# Helper: run a smoke check
smoke_check() {
    local name="$1"
    local code="$2"
    TOTAL=$((TOTAL + 1))
    if output=$($PYTHON -c "$code" 2>&1); then
        PASS=$((PASS + 1))
        printf "  ✅ PASS: %s\n" "$name"
    else
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n  ❌ FAIL: ${name}: ${output}"
        printf "  ❌ FAIL: %s\n" "$name"
    fi
}

# Helper: check file exists
check_file() {
    local name="$1"
    local filepath="$2"
    TOTAL=$((TOTAL + 1))
    if [ -f "$filepath" ]; then
        PASS=$((PASS + 1))
        printf "  ✅ PASS: %s\n" "$name"
    else
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n  ❌ FAIL: ${name}: File not found: ${filepath}"
        printf "  ❌ FAIL: %s\n" "$name"
    fi
}

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  CodeTrellis — Appendices Smoke Tests (PART J: J1-J4)          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# J1: Token Counter — Can count tokens for a small file
# ============================================================================
echo "--- J1: Token Counter Smoke ---"

smoke_check "J1: tiktoken import or fallback" \
    "
try:
    import tiktoken
    enc = tiktoken.encoding_for_model('gpt-4o')
    tokens = len(enc.encode('Hello CodeTrellis'))
    assert tokens > 0, 'Zero tokens'
    print(f'OK (tiktoken): {tokens} tokens')
except ImportError:
    # Fallback: char/4 heuristic
    tokens = max(1, len('Hello CodeTrellis') // 4)
    assert tokens > 0, 'Zero tokens with fallback'
    print(f'OK (char/4 fallback): {tokens} tokens')
"

smoke_check "J1: Count tokens for matrix.prompt" \
    "
import os
matrix_path = os.path.join('$PROJECT_ROOT', '.codetrellis', 'cache', 'codetrellis', 'matrix.prompt')
if not os.path.exists(matrix_path):
    print('SKIP: matrix.prompt not found (run codetrellis scan first)')
    exit(0)
with open(matrix_path) as f:
    content = f.read()
try:
    import tiktoken
    enc = tiktoken.encoding_for_model('gpt-4o')
    tokens = len(enc.encode(content))
except ImportError:
    tokens = max(1, len(content) // 4)
assert tokens > 0, 'Zero tokens for matrix.prompt'
print(f'OK: matrix.prompt = {tokens:,} tokens ({len(content):,} chars)')
"

smoke_check "J1: Token budget validator imports" \
    "
import sys; sys.path.insert(0, '$PROJECT_ROOT/scripts')
from token_budget_validator import TokenBudgetValidator, MODEL_BUDGETS, ALL_LANGUAGES
assert len(MODEL_BUDGETS) == 6, f'Expected 6 models, got {len(MODEL_BUDGETS)}'
assert len(ALL_LANGUAGES) >= 53, f'Expected 53+ languages, got {len(ALL_LANGUAGES)}'
print(f'OK: {len(MODEL_BUDGETS)} models, {len(ALL_LANGUAGES)} languages')
"

echo ""

# ============================================================================
# J2: Manifest Check — Verify critical core files exist
# ============================================================================
echo "--- J2: Manifest Check Smoke ---"

check_file "J2: scanner.py exists" "$PROJECT_ROOT/codetrellis/scanner.py"
check_file "J2: compressor.py exists" "$PROJECT_ROOT/codetrellis/compressor.py"
check_file "J2: builder.py exists" "$PROJECT_ROOT/codetrellis/builder.py"
check_file "J2: cache.py exists" "$PROJECT_ROOT/codetrellis/cache.py"
check_file "J2: interfaces.py exists" "$PROJECT_ROOT/codetrellis/interfaces.py"
check_file "J2: matrix_jsonld.py (F1)" "$PROJECT_ROOT/codetrellis/matrix_jsonld.py"
check_file "J2: matrix_embeddings.py (F2)" "$PROJECT_ROOT/codetrellis/matrix_embeddings.py"
check_file "J2: matrix_diff.py (F3)" "$PROJECT_ROOT/codetrellis/matrix_diff.py"
check_file "J2: matrix_compressor_levels.py (F4)" "$PROJECT_ROOT/codetrellis/matrix_compressor_levels.py"
check_file "J2: cross_language_types.py (F5)" "$PROJECT_ROOT/codetrellis/cross_language_types.py"
check_file "J2: matrix_navigator.py (F6)" "$PROJECT_ROOT/codetrellis/matrix_navigator.py"
check_file "J2: matrixbench_scorer.py (F7)" "$PROJECT_ROOT/codetrellis/matrixbench_scorer.py"
check_file "J2: build_contracts_advanced.py (H)" "$PROJECT_ROOT/codetrellis/build_contracts_advanced.py"

smoke_check "J2: Manifest auditor imports" \
    "
import sys; sys.path.insert(0, '$PROJECT_ROOT/scripts')
from manifest_audit import ManifestAuditor, LANGUAGE_PARSER_FILES
assert len(LANGUAGE_PARSER_FILES) >= 50, f'Expected 50+ parsers, got {len(LANGUAGE_PARSER_FILES)}'
print(f'OK: {len(LANGUAGE_PARSER_FILES)} parser files in manifest')
"

echo ""

# ============================================================================
# J3: Synergy Check — Cross-domain module interaction
# ============================================================================
echo "--- J3: Synergy Check Smoke ---"

smoke_check "J3: JSON-LD + Embeddings synergy" \
    "
from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
import json

matrix = {'project_name': 'smoke', 'total_files': 3, 'total_tokens': 100, 'readme': 'test'}
encoder = MatrixJsonLdEncoder()
doc = encoder.encode(matrix)
assert '@graph' in doc

# Extract node texts for embedding
texts = {}
for node in doc['@graph']:
    if '@id' in node:
        texts[node['@id']] = json.dumps(node, default=str)

if texts:
    idx = MatrixEmbeddingIndex()
    idx.build_index(texts)
    results = idx.query('project', top_k=2)
    assert len(results) > 0
    print(f'OK: {len(texts)} nodes embedded, {len(results)} results')
else:
    print('OK: Synergy pipeline complete (no nodes to embed)')
"

smoke_check "J3: Patch + Compression synergy" \
    "
import copy, json
from codetrellis.matrix_diff import MatrixDiffEngine
from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel

old = {'name': 'test', 'files': 5}
new = copy.deepcopy(old)
new['files'] = 6

engine = MatrixDiffEngine()
patch = engine.compute_diff(old, new)
assert len(list(patch)) > 0

patched = engine.apply_patch(old, patch)
assert patched == new

prompt = json.dumps(patched, indent=2)
compressor = MatrixMultiLevelCompressor()
compressed = compressor.compress(prompt, level=CompressionLevel.L2_STRUCTURAL)
assert len(compressed) > 0
print(f'OK: {len(list(patch))} ops, compressed {len(prompt)} → {len(compressed)} chars')
"

smoke_check "J3: Cross-language + Navigator synergy" \
    "
from codetrellis.cross_language_types import CrossLanguageLinker
from codetrellis.matrix_navigator import MatrixNavigator
import json

linker = CrossLanguageLinker()
langs = linker.get_available_languages()
assert len(langs) > 0

matrix = {'project_name': 'test', 'python_types': [{'name': 'User'}]}
nav = MatrixNavigator(matrix_json=matrix, matrix_prompt=json.dumps(matrix))
results = nav.discover('User type')
print(f'OK: {len(langs)} languages available, navigator returned {len(results)} results')
"

echo ""

# ============================================================================
# J4: Citations — Check docs exist and are populated
# ============================================================================
echo "--- J4: Citations Check Smoke ---"

check_file "J4: CITATIONS.md exists" "$PROJECT_ROOT/docs/references/CITATIONS.md"

smoke_check "J4: CITATIONS.md has required sources" \
    "
import os
path = os.path.join('$PROJECT_ROOT', 'docs', 'references', 'CITATIONS.md')
if not os.path.exists(path):
    print('SKIP: CITATIONS.md not yet created')
    exit(0)
with open(path) as f:
    content = f.read()
required = ['JSON-LD', 'RFC 6902', 'SCIP', 'CodeBERT', 'LLMLingua', 'SWE-bench', 'HumanEval']
missing = [s for s in required if s not in content]
assert len(missing) == 0, f'Missing citations: {missing}'
print(f'OK: All {len(required)} key citations found')
"

smoke_check "J4: CITATIONS.md has URLs" \
    "
import os, re
path = os.path.join('$PROJECT_ROOT', 'docs', 'references', 'CITATIONS.md')
if not os.path.exists(path):
    print('SKIP: CITATIONS.md not yet created')
    exit(0)
with open(path) as f:
    content = f.read()
urls = re.findall(r'https?://[^\s>)]+', content)
assert len(urls) >= 10, f'Only {len(urls)} URLs found, expected >= 10'
print(f'OK: {len(urls)} URLs in citations')
"

echo ""

# ============================================================================
# Summary
# ============================================================================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  PART J Appendices Smoke Test Results                          ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
printf "║  Total:  %3d  │  Pass:  %3d  │  Fail:  %3d  │  Time: %2ds      ║\n" "$TOTAL" "$PASS" "$FAIL" "$ELAPSED"
echo "╚══════════════════════════════════════════════════════════════════╝"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "FAILURES:"
    printf "$ERRORS\n"
    echo ""
    exit 1
fi

echo ""
echo "  ✅ All PART J smoke tests passed in ${ELAPSED}s"
exit 0
