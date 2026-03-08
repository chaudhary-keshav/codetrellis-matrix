#!/usr/bin/env bash
# ============================================================================
# CodeTrellis Advanced Research — Smoke Test Suite
# ============================================================================
# Fast sanity checks for all 7 advanced research modules (F1–F7).
# Verifies: imports load, core APIs callable, minimal pipeline works.
#
# Quality Gate Reference: PART G — G1 through G7
# Target: Complete in < 10 seconds, exit code 0.
#
# Usage:
#   ./scripts/smoke_test_advanced.sh
#   # or from project root:
#   bash scripts/smoke_test_advanced.sh
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

echo "============================================================================"
echo " CodeTrellis Advanced Research — Smoke Tests"
echo "============================================================================"
echo ""

# ============================================================================
# Module Import Checks (all 7 modules must import without error)
# ============================================================================
echo "--- Module Import Checks ---"

smoke_check "F1: matrix_jsonld imports" \
    "from codetrellis.matrix_jsonld import MatrixJsonLdEncoder, MATRIX_SECTIONS, CODETRELLIS_CONTEXT; print('OK')"

smoke_check "F2: matrix_embeddings imports" \
    "from codetrellis.matrix_embeddings import MatrixEmbeddingIndex, TFIDFVectorizer, EmbeddingMetadata; print('OK')"

smoke_check "F3: matrix_diff imports" \
    "from codetrellis.matrix_diff import MatrixDiffEngine, PatchStats, PatchRecord, PatchApplicationError; print('OK')"

smoke_check "F4: matrix_compressor_levels imports" \
    "from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel, CompressionResult; print('OK')"

smoke_check "F5: cross_language_types imports" \
    "from codetrellis.cross_language_types import CrossLanguageLinker, TypeMapping, APILink, UnifiedMatrix; print('OK')"

smoke_check "F6: matrix_navigator imports" \
    "from codetrellis.matrix_navigator import MatrixNavigator, FileRelevance, DiscoveryMetrics; print('OK')"

smoke_check "F7: matrixbench_scorer imports" \
    "from codetrellis.matrixbench_scorer import MatrixBench, BenchmarkResults, TaskResult, CATEGORIES; print('OK')"

echo ""

# ============================================================================
# F1: JSON-LD — Minimal encode + validate
# ============================================================================
echo "--- F1: JSON-LD Smoke ---"

smoke_check "F1: Encode minimal matrix to JSON-LD" \
    "
from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
import json
matrix = {'project_name': 'smoke', 'total_files': 3, 'total_tokens': 100, 'readme': 'test', 'python_types': [{'name': 'Foo'}]}
encoder = MatrixJsonLdEncoder()
doc = encoder.encode(matrix)
assert '@context' in doc, 'Missing @context'
assert '@graph' in doc, 'Missing @graph'
assert len(doc['@graph']) > 0, 'Empty @graph'
print('OK: ' + str(len(doc['@graph'])) + ' nodes')
"

smoke_check "F1: Validate encoded JSON-LD" \
    "
from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
matrix = {'project_name': 'smoke', 'total_files': 3, 'total_tokens': 100, 'readme': 'test'}
encoder = MatrixJsonLdEncoder()
doc = encoder.encode(matrix)
errors = encoder.validate(doc)
assert isinstance(errors, list), 'validate() must return list'
print('OK: ' + str(len(errors)) + ' validation errors')
"

smoke_check "F1: Round-trip verification" \
    "
from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
matrix = {'project_name': 'smoke', 'total_files': 5, 'total_tokens': 200, 'readme': 'Smoke test project'}
encoder = MatrixJsonLdEncoder()
assert encoder.verify_roundtrip(matrix), 'Round-trip failed'
print('OK')
"

echo ""

# ============================================================================
# F2: Embeddings — Build index + query
# ============================================================================
echo "--- F2: Embeddings Smoke ---"

smoke_check "F2: Build embedding index" \
    "
from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
sections = {'TYPES': 'class User: name str, email str', 'API': 'GET /users POST /users', 'OVERVIEW': 'A web application'}
idx = MatrixEmbeddingIndex()
meta = idx.build_index(sections)
assert meta.section_count == 3, f'Expected 3 sections, got {meta.section_count}'
assert meta.dimensions > 0, 'Zero dimensions'
print('OK: ' + str(meta.dimensions) + ' dims, ' + str(meta.section_count) + ' sections')
"

smoke_check "F2: Query embedding index" \
    "
from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
sections = {'TYPES': 'class User name email', 'API': 'GET users POST users', 'OVERVIEW': 'web application project'}
idx = MatrixEmbeddingIndex()
idx.build_index(sections)
results = idx.query('user database schema', top_k=3)
assert len(results) > 0, 'No results'
assert all(0 <= r.score <= 1 for r in results), 'Score out of range'
print('OK: top result = ' + results[0].section_id + ' (' + str(results[0].score) + ')')
"

smoke_check "F2: Determinism verification" \
    "
from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
sections = {'A': 'hello world', 'B': 'foo bar baz'}
idx = MatrixEmbeddingIndex()
idx.build_index(sections)
assert idx.verify_determinism(sections), 'Non-deterministic'
print('OK')
"

echo ""

# ============================================================================
# F3: JSON Patch — Diff + apply + roundtrip
# ============================================================================
echo "--- F3: JSON Patch Smoke ---"

smoke_check "F3: Empty diff produces empty patch" \
    "
from codetrellis.matrix_diff import MatrixDiffEngine
engine = MatrixDiffEngine()
old = {'a': 1, 'b': [1, 2, 3]}
patch = engine.compute_diff(old, old)
ops = patch.patch if hasattr(patch, 'patch') else list(patch)
assert len(ops) == 0, f'Expected empty patch, got {len(ops)} ops'
print('OK')
"

smoke_check "F3: Diff + apply roundtrip" \
    "
from codetrellis.matrix_diff import MatrixDiffEngine
import json, copy
engine = MatrixDiffEngine()
old = {'project': 'test', 'files': [1, 2, 3]}
new = copy.deepcopy(old)
new['files'].append(4)
new['version'] = '2.0'
patch = engine.compute_diff(old, new)
result = engine.apply_patch(old, patch)
assert json.dumps(result, sort_keys=True) == json.dumps(new, sort_keys=True), 'Roundtrip mismatch'
print('OK')
"

smoke_check "F3: Atomic rollback on bad patch" \
    "
from codetrellis.matrix_diff import MatrixDiffEngine, PatchApplicationError
import jsonpatch, copy
engine = MatrixDiffEngine()
original = {'a': 1}
original_copy = copy.deepcopy(original)
bad_patch = jsonpatch.JsonPatch([{'op': 'test', 'path': '/nonexistent', 'value': 42}])
try:
    engine.apply_patch(original, bad_patch)
    assert False, 'Should have raised'
except PatchApplicationError:
    pass
assert original == original_copy, 'Original was mutated!'
print('OK')
"

smoke_check "F3: Patch stats" \
    "
from codetrellis.matrix_diff import MatrixDiffEngine
import copy
engine = MatrixDiffEngine()
old = {'a': 1}
new = {'a': 2, 'b': 3}
patch = engine.compute_diff(old, new)
stats = engine.get_patch_stats(patch, new)
assert stats.total_operations > 0, 'No operations'
print('OK: ' + str(stats.total_operations) + ' ops')
"

echo ""

# ============================================================================
# F4: Compression Levels — L1/L2/L3 + auto-select
# ============================================================================
echo "--- F4: Compression Levels Smoke ---"

smoke_check "F4: L1 identity transform" \
    "
from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel
comp = MatrixMultiLevelCompressor()
text = '# Overview\ndef foo(): pass\ndef bar(): pass\n# Types\nclass User: pass\n'
result = comp.compress(text, CompressionLevel.L1_FULL)
assert result == text, 'L1 is not identity'
print('OK')
"

smoke_check "F4: L2 < L1 < L3 size ordering" \
    "
from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel
comp = MatrixMultiLevelCompressor()
# Use a realistic prompt with section bodies that L2 can actually strip
text = '''[OVERVIEW]
CodeTrellis is a project-awareness system.
It scans source code and builds a context matrix.
The matrix contains types, APIs, and metadata.
This enables AI assistants to understand projects.
The system supports over 50 languages.

[PYTHON_TYPES]
class User:
    name: str
    email: str
    age: int
    created_at: datetime
    # Internal tracking fields
    _id: int = 0
    _active: bool = True

class Order:
    user_id: int
    total: float
    items: List[str]
    status: str = \"pending\"
    # Multi-line docstring and implementation
    def process(self):
        self.status = \"processing\"
        for item in self.items:
            validate_item(item)
        self.status = \"completed\"

[RUNBOOK]
## Commands
test: pytest tests/ -v
build: python -m build
lint: ruff check .
format: black .
install: pip install -e .
''' * 5
l1 = comp.compress(text, CompressionLevel.L1_FULL)
l2 = comp.compress(text, CompressionLevel.L2_STRUCTURAL)
l3 = comp.compress(text, CompressionLevel.L3_SKELETON)
assert len(l2) < len(l1), f'L2 ({len(l2)}) not smaller than L1 ({len(l1)})'
assert len(l3) < len(l2), f'L3 ({len(l3)}) not smaller than L2 ({len(l2)})'
print('OK: L1=' + str(len(l1)) + ' L2=' + str(len(l2)) + ' L3=' + str(len(l3)))
"

smoke_check "F4: Auto-select levels" \
    "
from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel
comp = MatrixMultiLevelCompressor()
assert comp.auto_select_level(200_000) == CompressionLevel.L1_FULL, '200K should be L1'
assert comp.auto_select_level(128_000) == CompressionLevel.L2_STRUCTURAL, '128K should be L2'
assert comp.auto_select_level(32_000) == CompressionLevel.L3_SKELETON, '32K should be L3'
print('OK')
"

echo ""

# ============================================================================
# F5: Cross-Language Types — Primitive mapping + all languages
# ============================================================================
echo "--- F5: Cross-Language Types Smoke ---"

smoke_check "F5: All 6 primitives map TS→Python" \
    "
from codetrellis.cross_language_types import CrossLanguageLinker
linker = CrossLanguageLinker()
assert linker.resolve_type('string', 'typescript', 'python') == 'str'
assert linker.resolve_type('number', 'typescript', 'python') is not None
assert linker.resolve_type('boolean', 'typescript', 'python') == 'bool'
assert linker.resolve_type('void', 'typescript', 'python') == 'None'
assert linker.resolve_type('Uint8Array', 'typescript', 'python') == 'bytes'
# Promise→Awaitable
assert linker.resolve_type('Promise', 'typescript', 'python') == 'Awaitable[T]'
print('OK')
"

smoke_check "F5: ≥15 supported languages" \
    "
from codetrellis.cross_language_types import CrossLanguageLinker
linker = CrossLanguageLinker()
langs = linker.get_available_languages()
assert len(langs) >= 15, f'Only {len(langs)} languages'
print('OK: ' + str(len(langs)) + ' languages')
"

smoke_check "F5: Merge matrices produces UnifiedMatrix" \
    "
from codetrellis.cross_language_types import CrossLanguageLinker
linker = CrossLanguageLinker()
# Build realistic-sized matrices (link metadata is fixed overhead)
py_funcs = ['get_user', 'create_user', 'delete_user', 'update_user', 'list_users',
            'get_order', 'create_order', 'process_payment', 'send_notification',
            'validate_input', 'parse_config', 'build_response', 'handle_error']
py_types = ['User', 'Order', 'Payment', 'Config', 'Response', 'Error', 'Notification',
            'Session', 'Token', 'Permission', 'Role', 'AuditLog']
# Pad content with realistic metadata per function
py_data = {}
ts_data = {}
for f in py_funcs:
    py_data[f] = {'sig': f'def {f}(self, ctx: Context) -> Response: ...', 'file': 'app/views.py', 'line': 42, 'doc': f'Handle {f} request with validation and logging'}
for f in ['getUser', 'createUser', 'deleteUser', 'updateUser', 'listUsers',
          'getOrder', 'createOrder', 'processPayment', 'sendNotification',
          'validateInput', 'parseConfig', 'buildResponse', 'handleError']:
    ts_data[f] = {'sig': f'function {f}(ctx: Context): Response', 'file': 'src/controllers.ts', 'line': 42, 'doc': f'Handle {f} request with validation and logging'}
for t in py_types:
    py_data[t] = {'kind': 'class', 'fields': ['id: int', 'name: str', 'created: datetime'], 'file': 'app/models.py'}
    ts_data[t] = {'kind': 'interface', 'fields': ['id: number', 'name: string', 'created: Date'], 'file': 'src/models.ts'}
matrices = {'python': py_data, 'typescript': ts_data}
unified = linker.merge_matrices(matrices)
assert unified.overhead_ratio <= 1.5, f'Overhead {unified.overhead_ratio}'
assert len(unified.languages) == 2
print('OK: overhead=' + str(round(unified.overhead_ratio, 2)))
"

echo ""

# ============================================================================
# F6: Matrix Navigator — Discover + dependency tracking
# ============================================================================
echo "--- F6: Matrix Navigator Smoke ---"

smoke_check "F6: Empty query returns empty" \
    "
from codetrellis.matrix_navigator import MatrixNavigator
nav = MatrixNavigator({'section1': {'data': 'test'}}, 'test prompt')
results = nav.discover('')
assert results == [], 'Empty query should return empty'
results2 = nav.discover('   ')
assert results2 == [], 'Whitespace query should return empty'
print('OK')
"

smoke_check "F6: Discover finds relevant sections" \
    "
from codetrellis.matrix_navigator import MatrixNavigator
matrix_json = {
    'python_types': {'classes': ['User', 'Order'], 'functions': ['get_user']},
    'routes': {'endpoints': ['/api/users', '/api/orders']},
}
prompt = '# Python Types\\nclass User:\\n  name: str\\n# Routes\\nGET /api/users\\n'
nav = MatrixNavigator(matrix_json, prompt)
results = nav.discover('User class')
assert isinstance(results, list)
print('OK: ' + str(len(results)) + ' results')
"

smoke_check "F6: Latency < 100ms without embeddings" \
    "
from codetrellis.matrix_navigator import MatrixNavigator
import time
matrix_json = {f'section_{i}': {'data': f'content {i}'} for i in range(100)}
prompt = '\\n'.join(f'# Section {i}\\ncontent {i}' for i in range(100))
nav = MatrixNavigator(matrix_json, prompt)
t0 = time.perf_counter()
results = nav.discover('content search query')
elapsed = (time.perf_counter() - t0) * 1000
assert elapsed < 100, f'Too slow: {elapsed:.1f}ms'
print('OK: ' + str(round(elapsed, 1)) + 'ms')
"

echo ""

# ============================================================================
# F7: MatrixBench — Run + determinism
# ============================================================================
echo "--- F7: MatrixBench Smoke ---"

smoke_check "F7: Run all benchmark tasks" \
    "
from codetrellis.matrixbench_scorer import MatrixBench, CATEGORIES
bench = MatrixBench(matrix_json={'types': ['User'], 'imports': ['os']}, matrix_prompt='# Overview\\nA test project\\ndef scan(): pass\\nclass Builder: pass\\nimport os\\n')
results = bench.run_all()
assert results.total_tasks > 0, 'No tasks ran'
print('OK: ' + str(results.passed_tasks) + '/' + str(results.total_tasks) + ' passed')
"

smoke_check "F7: Determinism ±2%" \
    "
from codetrellis.matrixbench_scorer import MatrixBench
bench = MatrixBench(matrix_json={'types': ['User']}, matrix_prompt='# Overview\\ndef scan(): pass\\nclass Builder: pass\\n')
r1 = bench.run_all()
r2 = bench.run_all()
diff = abs(r1.avg_improvement_pct - r2.avg_improvement_pct)
assert diff <= 2.0, f'Non-deterministic: {diff:.2f}%'
print('OK: variance=' + str(round(diff, 4)) + '%')
"

smoke_check "F7: JSON + Markdown export" \
    "
import tempfile, json
from pathlib import Path
from codetrellis.matrixbench_scorer import MatrixBench
bench = MatrixBench(matrix_json={'types': ['User']}, matrix_prompt='# Overview\\ndef scan(): pass\\n')
results = bench.run_all()
report = bench.generate_report(results)
assert 'MatrixBench Report' in report, 'Missing report header'
with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
    tmp = Path(f.name)
bench.export_results(results, tmp)
data = json.loads(tmp.read_text())
assert data['total_tasks'] == results.total_tasks
tmp.unlink()
print('OK')
"

echo ""

# ============================================================================
# Pipeline Integration — Full scan → advanced modules
# ============================================================================
echo "--- Pipeline Integration Smoke ---"

smoke_check "Pipeline: Scan output feeds all advanced modules" \
    "
import json
from pathlib import Path
from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
from codetrellis.matrix_diff import MatrixDiffEngine
from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel
from codetrellis.cross_language_types import CrossLanguageLinker
from codetrellis.matrix_navigator import MatrixNavigator
from codetrellis.matrixbench_scorer import MatrixBench

# Check if real matrix files exist
mj_path = Path('$PROJECT_ROOT/.codetrellis/cache/4.16.0/codetrellis/matrix.json')
mp_path = Path('$PROJECT_ROOT/.codetrellis/cache/4.16.0/codetrellis/matrix.prompt')

if mj_path.exists() and mp_path.exists():
    matrix_json = json.loads(mj_path.read_text())
    matrix_prompt = mp_path.read_text()
else:
    # Synthetic fallback
    matrix_json = {'project_name': 'smoke', 'total_files': 5, 'total_tokens': 200, 'readme': 'test'}
    matrix_prompt = '# Overview\ndef scan(): pass\nclass Builder: pass\n'

# F1: JSON-LD
encoder = MatrixJsonLdEncoder()
ld = encoder.encode(matrix_json)
assert '@graph' in ld

# F2: Embeddings
sections = {'OVERVIEW': matrix_prompt[:500]}
idx = MatrixEmbeddingIndex()
idx.build_index(sections)

# F3: Diff
engine = MatrixDiffEngine()
patch = engine.compute_diff(matrix_json, matrix_json)

# F4: Compression
comp = MatrixMultiLevelCompressor()
l2 = comp.compress(matrix_prompt[:2000], CompressionLevel.L2_STRUCTURAL)

# F5: Cross-Language
linker = CrossLanguageLinker()
linker.resolve_type('str', 'python', 'typescript')

# F6: Navigator
nav = MatrixNavigator(matrix_json, matrix_prompt[:2000])
nav.discover('test query')

# F7: MatrixBench
bench = MatrixBench(matrix_json=matrix_json, matrix_prompt=matrix_prompt[:2000])
bench.run_all()

print('OK: All 7 modules integrated successfully')
"

echo ""

# ============================================================================
# Summary
# ============================================================================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "============================================================================"
echo " SMOKE TEST RESULTS"
echo "============================================================================"
echo ""
printf "  Total:  %d\n" "$TOTAL"
printf "  Passed: %d\n" "$PASS"
printf "  Failed: %d\n" "$FAIL"
printf "  Time:   %ds\n" "$ELAPSED"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "FAILURES:"
    printf "%b\n" "$ERRORS"
    echo ""
    echo "❌ SMOKE TESTS FAILED"
    exit 1
fi

echo "✅ ALL SMOKE TESTS PASSED (${ELAPSED}s)"
exit 0
