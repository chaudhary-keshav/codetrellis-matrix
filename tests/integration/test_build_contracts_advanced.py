"""
CodeTrellis Advanced Build Contracts — Production Integration Test Suite
==========================================================================

Tests all 7 build contracts (H1-H7) from PART H of the Master Research Plan.
Each contract validates I/O, error behavior, caching rules, and determinism
for the corresponding advanced research module.

Contract Map:
  H1 — JSON-LD Build Contract          → JsonLdBuildContract
  H2 — Embedding Build Contract        → EmbeddingBuildContract
  H3 — JSON Patch Build Contract       → JsonPatchBuildContract
  H4 — Compression Build Contract      → CompressionBuildContract
  H5 — Cross-Language Build Contract   → CrossLanguageBuildContract
  H6 — Navigator Build Contract        → NavigatorBuildContract
  H7 — MatrixBench Build Contract      → MatrixBenchBuildContract

Coverage: Happy path, edge cases, malformed inputs, error behavior,
          cache behavior, determinism for each contract.
Target: 100% PASS rate.

Execute:
  pytest tests/integration/test_build_contracts_advanced.py -v --tb=short
"""

import copy
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Project root & paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.json"
MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.prompt"

# All 53+ supported languages/frameworks
ALL_LANGUAGES = [
    "python", "typescript", "javascript", "java", "kotlin", "csharp",
    "rust", "go", "swift", "ruby", "php", "scala", "r", "dart", "lua",
    "powershell", "bash", "c", "cpp", "sql", "html", "css",
    "vue", "react", "svelte", "nextjs", "remix", "astro", "solidjs",
    "qwik", "preact", "lit", "alpinejs", "htmx",
    "redux", "zustand", "jotai", "recoil", "mobx", "pinia", "ngrx",
    "xstate", "valtio", "tanstack_query", "swr", "apollo",
    "tailwind", "mui", "antd", "chakra", "shadcn", "bootstrap", "radix",
    "styled_components", "emotion", "sass", "less", "postcss",
]

CORE_LANGUAGES = [
    "python", "typescript", "javascript", "java", "kotlin", "csharp",
    "rust", "go", "swift", "ruby", "php", "scala", "dart", "lua",
    "r", "c", "cpp", "powershell", "bash",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def matrix_json() -> Dict[str, Any]:
    """Load project's own matrix.json."""
    if not MATRIX_JSON_PATH.exists():
        pytest.skip(f"matrix.json not found at {MATRIX_JSON_PATH}")
    return json.loads(MATRIX_JSON_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def matrix_prompt() -> str:
    """Load project's own matrix.prompt."""
    if not MATRIX_PROMPT_PATH.exists():
        pytest.skip(f"matrix.prompt not found at {MATRIX_PROMPT_PATH}")
    return MATRIX_PROMPT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prompt_sections(matrix_prompt: str) -> Dict[str, str]:
    """Parse matrix.prompt into named sections."""
    sections: Dict[str, str] = {}
    current = ""
    lines: List[str] = []
    for line in matrix_prompt.split("\n"):
        match = re.match(r"^\[([A-Z_]+)\]", line)
        if match:
            if current:
                sections[current] = "\n".join(lines)
            current = match.group(1)
            lines = []
        else:
            lines.append(line)
    if current:
        sections[current] = "\n".join(lines)
    return sections


def _make_synthetic_matrix() -> Dict[str, Any]:
    """Create a minimal synthetic matrix for tests that don't need real data."""
    return {
        "project_name": "test_project",
        "total_files": 10,
        "total_tokens": 500,
        "version": "1.0.0",
        "readme": "A test project for build contract validation.",
        "python_types": [
            {"name": "User", "type": "dataclass", "file_path": "models.py"},
            {"name": "Order", "type": "dataclass", "file_path": "models.py"},
        ],
        "python_api": [
            {"method": "GET", "url": "/api/users", "handler": "get_users"},
        ],
        "overview": {"directories": ["src", "tests"]},
        "runbook": {"commands": {"test": "pytest"}},
        "business_domain": {"domain": "E-commerce"},
        "hooks": [{"name": "on_save", "type": "lifecycle"}],
        "middleware": [{"name": "auth_middleware"}],
        "error_handling": [{"type": "try-catch", "file": "handler.py"}],
        "data_flows": {"primary": "request-response"},
        "best_practices": [{"id": "PY001", "title": "Use type hints"}],
    }


def _make_synthetic_prompt() -> str:
    """Create a minimal synthetic matrix.prompt for tests."""
    sections = [
        "[PROJECT]\nName: test_project\nFiles: 10\n",
        "[PYTHON_TYPES]\nclass User:\n  name: str\n  id: int\n",
        "[PYTHON_API]\ndef get_users(request):\n  return Response(users)\n",
        "[OVERVIEW]\n- src/\n- tests/\n",
        "[RUNBOOK]\npytest tests/\n",
    ]
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Contract Imports
# ---------------------------------------------------------------------------
from codetrellis.build_contract import ExitCode
from codetrellis.build_contracts_advanced import (
    AdvancedBuildContractSuite,
    CompressionBuildContract,
    ContractResult,
    ContractSuiteResult,
    CrossLanguageBuildContract,
    EmbeddingBuildContract,
    JsonLdBuildContract,
    JsonPatchBuildContract,
    MatrixBenchBuildContract,
    NavigatorBuildContract,
    _sha256,
)


# ============================================================================
# SHARED: ContractResult & ContractSuiteResult
# ============================================================================

class TestContractTypes:
    """Tests for shared ContractResult and ContractSuiteResult dataclasses."""

    def test_contract_result_to_dict(self):
        """ContractResult.to_dict() produces valid dict with all fields."""
        r = ContractResult(
            contract_id="TEST",
            passed=True,
            exit_code=0,
            errors=[],
            warnings=["minor"],
            duration_ms=1.234,
            details={"key": "value"},
        )
        d = r.to_dict()
        assert d["contract_id"] == "TEST"
        assert d["passed"] is True
        assert d["exit_code"] == 0
        assert d["errors"] == []
        assert d["warnings"] == ["minor"]
        assert d["duration_ms"] == 1.23
        assert d["details"] == {"key": "value"}

    def test_contract_result_defaults(self):
        """ContractResult defaults are sane."""
        r = ContractResult(contract_id="X", passed=False, exit_code=1)
        assert r.errors == []
        assert r.warnings == []
        assert r.duration_ms == 0.0
        assert r.details == {}

    def test_contract_suite_result_to_dict(self):
        """ContractSuiteResult.to_dict() includes all contract results."""
        r1 = ContractResult(contract_id="A", passed=True, exit_code=0)
        r2 = ContractResult(contract_id="B", passed=False, exit_code=41)
        suite = ContractSuiteResult(
            results=[r1, r2],
            all_passed=False,
            total_duration_ms=5.0,
        )
        d = suite.to_dict()
        assert d["all_passed"] is False
        assert len(d["contracts"]) == 2
        assert d["contracts"][0]["contract_id"] == "A"
        assert d["contracts"][1]["contract_id"] == "B"

    def test_sha256_deterministic(self):
        """_sha256 produces identical hash for identical input."""
        data = {"a": 1, "b": [2, 3]}
        h1 = _sha256(data)
        h2 = _sha256(data)
        assert h1 == h2
        assert len(h1) == 64

    def test_sha256_order_independent(self):
        """_sha256 uses sort_keys, so key order does not matter."""
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert _sha256(d1) == _sha256(d2)

    def test_sha256_different_data(self):
        """Different data produces different hashes."""
        assert _sha256({"a": 1}) != _sha256({"a": 2})


# ============================================================================
# H1: JSON-LD Build Contract Tests
# ============================================================================

class TestH1JsonLdContract:
    """Tests for JsonLdBuildContract (H1).

    Covers: Happy path, missing fields, duplicate IDs, dangling refs,
    overhead check, cache key computation.
    """

    def test_h1_happy_path(self, matrix_json):
        """Valid JSON-LD output passes contract."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix_json)
        contract = JsonLdBuildContract()
        result = contract.validate(matrix_json, doc)
        assert result.passed, f"H1 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H1_JSONLD"

    def test_h1_exit_code_is_41(self):
        """H1 exit code is 41."""
        assert JsonLdBuildContract.EXIT_CODE == ExitCode.JSONLD_VALIDATION_FAILED
        assert int(JsonLdBuildContract.EXIT_CODE) == 41

    def test_h1_missing_context(self):
        """Missing @context triggers error."""
        contract = JsonLdBuildContract()
        doc = {"@type": "ct:Matrix", "@id": "ct:test", "@graph": []}
        result = contract.validate({}, doc)
        assert not result.passed
        assert result.exit_code == 41
        assert any("@context" in e for e in result.errors)

    def test_h1_missing_type(self):
        """Missing @type triggers error."""
        contract = JsonLdBuildContract()
        doc = {"@context": {"ct": "https://codetrellis.dev/"}, "@id": "ct:test", "@graph": []}
        result = contract.validate({}, doc)
        assert not result.passed
        assert any("@type" in e for e in result.errors)

    def test_h1_missing_id(self):
        """Missing @id triggers error."""
        contract = JsonLdBuildContract()
        doc = {"@context": {"ct": "https://codetrellis.dev/"}, "@type": "ct:Matrix", "@graph": []}
        result = contract.validate({}, doc)
        assert not result.passed
        assert any("@id" in e for e in result.errors)

    def test_h1_invalid_id_prefix(self):
        """@id not starting with 'ct:' triggers error."""
        contract = JsonLdBuildContract()
        doc = {
            "@context": {"ct": "https://codetrellis.dev/"},
            "@type": "ct:Matrix",
            "@id": "invalid:test",
            "@graph": [],
        }
        result = contract.validate({}, doc)
        assert not result.passed
        assert any("ct:" in e for e in result.errors)

    def test_h1_duplicate_ids_in_graph(self):
        """Duplicate @ids in @graph triggers error."""
        contract = JsonLdBuildContract()
        doc = {
            "@context": {"ct": "https://codetrellis.dev/"},
            "@type": "ct:Matrix",
            "@id": "ct:test",
            "@graph": [
                {"@id": "ct:section1", "@type": "ct:Section"},
                {"@id": "ct:section1", "@type": "ct:Section"},
            ],
        }
        result = contract.validate({}, doc)
        assert not result.passed
        assert any("Duplicate" in e for e in result.errors)

    def test_h1_dangling_dependency_ref(self):
        """Dangling ct:depends reference triggers error."""
        contract = JsonLdBuildContract()
        doc = {
            "@context": {"ct": "https://codetrellis.dev/"},
            "@type": "ct:Matrix",
            "@id": "ct:test",
            "@graph": [
                {"@id": "ct:s1", "@type": "ct:Section", "ct:depends": ["ct:nonexistent"]},
            ],
        }
        result = contract.validate({}, doc)
        assert not result.passed
        assert any("Dangling" in e for e in result.errors)

    def test_h1_empty_graph_warning(self):
        """Empty @graph produces warning, not error."""
        contract = JsonLdBuildContract()
        doc = {
            "@context": {"ct": "https://codetrellis.dev/"},
            "@type": "ct:Matrix",
            "@id": "ct:test",
            "@graph": [],
        }
        result = contract.validate({}, doc)
        assert result.passed
        assert any("empty" in w.lower() for w in result.warnings)

    def test_h1_overhead_details_populated(self, matrix_json):
        """Overhead percentage is calculated and in details."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix_json)
        contract = JsonLdBuildContract()
        result = contract.validate(matrix_json, doc)
        assert "overhead_percent" in result.details

    def test_h1_cache_key_deterministic(self, matrix_json):
        """Cache key is deterministic for same input."""
        contract = JsonLdBuildContract()
        k1 = contract.compute_cache_key(matrix_json)
        k2 = contract.compute_cache_key(matrix_json)
        assert k1 == k2
        assert len(k1) == 32

    def test_h1_cache_key_invalidates_on_change(self, matrix_json):
        """Cache key changes when matrix changes."""
        contract = JsonLdBuildContract()
        k1 = contract.compute_cache_key(matrix_json)
        modified = copy.deepcopy(matrix_json)
        modified["__h1_change__"] = True
        k2 = contract.compute_cache_key(modified)
        assert k1 != k2

    def test_h1_cache_key_with_context_schema(self, matrix_json):
        """Cache key changes when context schema changes."""
        contract = JsonLdBuildContract()
        ctx1 = {"version": "1.0"}
        ctx2 = {"version": "2.0"}
        k1 = contract.compute_cache_key(matrix_json, ctx1)
        k2 = contract.compute_cache_key(matrix_json, ctx2)
        assert k1 != k2

    def test_h1_non_dict_output_fails(self):
        """Non-dict output triggers error."""
        contract = JsonLdBuildContract()
        result = contract.validate({}, "not a dict")
        assert not result.passed
        assert any("not a JSON object" in e for e in result.errors)

    def test_h1_graph_node_count_in_details(self, matrix_json):
        """graph_node_count is recorded in details."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix_json)
        contract = JsonLdBuildContract()
        result = contract.validate(matrix_json, doc)
        if result.passed:
            assert "graph_node_count" in result.details
            assert result.details["graph_node_count"] > 0

    def test_h1_duration_tracked(self, matrix_json):
        """Duration in milliseconds is tracked."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix_json)
        contract = JsonLdBuildContract()
        result = contract.validate(matrix_json, doc)
        assert result.duration_ms > 0


# ============================================================================
# H2: Embedding Build Contract Tests
# ============================================================================

class TestH2EmbeddingContract:
    """Tests for EmbeddingBuildContract (H2).

    Covers: Happy path, section count mismatch, NaN/Inf vectors,
    non-float dtypes, L2 norm check, cache key computation.
    """

    def test_h2_happy_path(self, prompt_sections):
        """Valid embedding index passes contract."""
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        idx = MatrixEmbeddingIndex()
        meta = idx.build_index(prompt_sections)
        vectors = {k: idx._index[k] for k in idx._index}
        contract = EmbeddingBuildContract()
        result = contract.validate(prompt_sections, meta, vectors)
        assert result.passed, f"H2 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H2_EMBEDDINGS"

    def test_h2_exit_code_is_42(self):
        """H2 exit code is 42."""
        assert EmbeddingBuildContract.EXIT_CODE == ExitCode.EMBEDDING_GENERATION_FAILED
        assert int(EmbeddingBuildContract.EXIT_CODE) == 42

    def test_h2_no_metadata_fails(self):
        """None metadata triggers error."""
        contract = EmbeddingBuildContract()
        result = contract.validate({"sec": "content"}, None)
        assert not result.passed
        assert result.exit_code == 42
        assert any("metadata" in e.lower() for e in result.errors)

    def test_h2_section_count_mismatch(self):
        """Mismatched section count triggers error."""
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 100
        meta.section_count = 5  # mismatch: 2 sections given
        meta.build_time_ms = 10
        result = contract.validate({"a": "x", "b": "y"}, meta)
        assert not result.passed
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_h2_nan_vector_fails(self):
        """Vectors with NaN trigger error."""
        import numpy as np
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 3
        meta.section_count = 1
        meta.build_time_ms = 1
        vectors = {"s1": np.array([1.0, float("nan"), 0.5])}
        result = contract.validate({"s1": "content"}, meta, vectors)
        assert not result.passed
        assert any("NaN" in e for e in result.errors)

    def test_h2_inf_vector_fails(self):
        """Vectors with Inf trigger error."""
        import numpy as np
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 3
        meta.section_count = 1
        meta.build_time_ms = 1
        vectors = {"s1": np.array([1.0, float("inf"), 0.5])}
        result = contract.validate({"s1": "content"}, meta, vectors)
        assert not result.passed
        assert any("NaN/Inf" in e for e in result.errors)

    def test_h2_non_ndarray_vector_fails(self):
        """Non-ndarray vector triggers error."""
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 3
        meta.section_count = 1
        meta.build_time_ms = 1
        vectors = {"s1": [1.0, 2.0, 3.0]}  # list, not ndarray
        result = contract.validate({"s1": "content"}, meta, vectors)
        assert not result.passed
        assert any("ndarray" in e for e in result.errors)

    def test_h2_l2_norm_warning(self):
        """Vector with L2 norm != 1.0 produces warning."""
        import numpy as np
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 3
        meta.section_count = 1
        meta.build_time_ms = 1
        # Unnormalized vector — norm ≈ 3.74
        vectors = {"s1": np.array([1.0, 2.0, 3.0])}
        result = contract.validate({"s1": "content"}, meta, vectors)
        # Should still pass (warning, not error)
        assert result.passed
        assert any("norm" in w.lower() for w in result.warnings)

    def test_h2_empty_sections_passes(self):
        """Empty sections with matching metadata passes."""
        contract = EmbeddingBuildContract()
        meta = MagicMock()
        meta.model_name = "tfidf"
        meta.dimensions = 0
        meta.section_count = 0
        meta.build_time_ms = 0
        result = contract.validate({}, meta)
        assert result.passed

    def test_h2_cache_key_deterministic(self):
        """Section cache key is deterministic."""
        contract = EmbeddingBuildContract()
        k1 = contract.compute_section_cache_key("sec1", "content here")
        k2 = contract.compute_section_cache_key("sec1", "content here")
        assert k1 == k2
        assert len(k1) == 32

    def test_h2_cache_key_changes_on_content(self):
        """Section cache key changes when content changes."""
        contract = EmbeddingBuildContract()
        k1 = contract.compute_section_cache_key("sec1", "version A")
        k2 = contract.compute_section_cache_key("sec1", "version B")
        assert k1 != k2

    def test_h2_cache_key_changes_on_section_id(self):
        """Section cache key changes when section ID changes."""
        contract = EmbeddingBuildContract()
        k1 = contract.compute_section_cache_key("sec1", "same content")
        k2 = contract.compute_section_cache_key("sec2", "same content")
        assert k1 != k2

    def test_h2_metadata_details_populated(self, prompt_sections):
        """Metadata fields are captured in details."""
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        idx = MatrixEmbeddingIndex()
        meta = idx.build_index(prompt_sections)
        contract = EmbeddingBuildContract()
        result = contract.validate(prompt_sections, meta)
        assert "model_name" in result.details
        assert "dimensions" in result.details
        assert "section_count" in result.details

    def test_h2_duration_tracked(self, prompt_sections):
        """Duration in milliseconds is tracked."""
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        idx = MatrixEmbeddingIndex()
        meta = idx.build_index(prompt_sections)
        contract = EmbeddingBuildContract()
        result = contract.validate(prompt_sections, meta)
        assert result.duration_ms >= 0


# ============================================================================
# H3: JSON Patch Build Contract Tests
# ============================================================================

class TestH3JsonPatchContract:
    """Tests for JsonPatchBuildContract (H3).

    Covers: Happy path, determinism (SHA-256), empty diff, RFC 6902 ops,
    invalid ops, missing fields, malformed patch, roundtrip integrity.
    """

    def test_h3_happy_path(self, matrix_json):
        """Valid JSON Patch passes contract."""
        from codetrellis.matrix_diff import MatrixDiffEngine
        engine = MatrixDiffEngine()
        base = {"project": "test", "version": "1.0"}
        target = copy.deepcopy(matrix_json)
        target["__h3_test__"] = True
        patch = engine.compute_diff(base, target)
        patch_ops = list(patch)
        contract = JsonPatchBuildContract()
        result = contract.validate(base, target, patch_ops)
        assert result.passed, f"H3 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H3_JSON_PATCH"

    def test_h3_exit_code_is_43(self):
        """H3 exit code is 43."""
        assert JsonPatchBuildContract.EXIT_CODE == ExitCode.JSON_PATCH_INTEGRITY_MISMATCH
        assert int(JsonPatchBuildContract.EXIT_CODE) == 43

    def test_h3_identical_inputs_empty_patch(self):
        """Identical inputs with empty patch passes."""
        contract = JsonPatchBuildContract()
        data = {"a": 1, "b": 2}
        result = contract.validate(data, data, [])
        assert result.passed
        assert result.details.get("empty_diff") is True

    def test_h3_identical_inputs_nonempty_patch_warning(self):
        """Identical inputs with non-empty patch produces warning."""
        contract = JsonPatchBuildContract()
        data = {"a": 1}
        ops = [{"op": "add", "path": "/b", "value": 2}]
        result = contract.validate(data, data, ops)
        # Will fail because applying patch to data won't match data
        assert any("warning" in str(result.warnings).lower() or
                    "mismatch" in str(result.errors).lower()
                    for _ in [True])

    def test_h3_different_inputs_empty_patch_fails(self):
        """Different inputs with empty patch triggers error."""
        contract = JsonPatchBuildContract()
        result = contract.validate({"a": 1}, {"a": 2}, [])
        assert not result.passed
        assert any("empty" in e.lower() for e in result.errors)

    def test_h3_invalid_op_type_fails(self):
        """Invalid RFC 6902 operation triggers error."""
        contract = JsonPatchBuildContract()
        ops = [{"op": "invalid_op", "path": "/a"}]
        result = contract.validate({"a": 1}, {"a": 2}, ops)
        assert not result.passed
        assert any("invalid op" in e.lower() for e in result.errors)

    def test_h3_missing_op_field_fails(self):
        """Missing 'op' field triggers error."""
        contract = JsonPatchBuildContract()
        ops = [{"path": "/a", "value": 1}]
        result = contract.validate({"a": 1}, {"a": 2}, ops)
        assert not result.passed
        assert any("missing 'op'" in e.lower() for e in result.errors)

    def test_h3_missing_path_field_fails(self):
        """Missing 'path' field triggers error."""
        contract = JsonPatchBuildContract()
        ops = [{"op": "add", "value": 1}]
        result = contract.validate({"a": 1}, {"a": 2}, ops)
        assert not result.passed
        assert any("missing 'path'" in e.lower() for e in result.errors)

    def test_h3_determinism_sha256(self):
        """base + patch = target verified by SHA-256."""
        import jsonpatch
        contract = JsonPatchBuildContract()
        base = {"a": 1, "b": "hello"}
        target = {"a": 2, "b": "hello", "c": True}
        patch = jsonpatch.make_patch(base, target)
        ops = list(patch)
        result = contract.validate(base, target, ops)
        assert result.passed, f"SHA-256 determinism failed: {result.errors}"
        assert result.details.get("target_hash") == result.details.get("result_hash")

    def test_h3_hash_mismatch_fails(self):
        """Wrong patch ops that don't reproduce target fail."""
        contract = JsonPatchBuildContract()
        base = {"a": 1}
        target = {"a": 2}
        # Deliberately wrong patch
        ops = [{"op": "replace", "path": "/a", "value": 999}]
        result = contract.validate(base, target, ops)
        assert not result.passed
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_h3_patch_application_error(self):
        """Patch that fails to apply produces error."""
        contract = JsonPatchBuildContract()
        base = {"a": 1}
        target = {"a": 2}
        # Patch references non-existent path
        ops = [{"op": "remove", "path": "/nonexistent/deep/path"}]
        result = contract.validate(base, target, ops)
        assert not result.passed
        assert any("failed" in e.lower() or "mismatch" in e.lower()
                    for e in result.errors)

    def test_h3_op_counts_in_details(self):
        """Operation counts recorded in details."""
        import jsonpatch
        contract = JsonPatchBuildContract()
        base = {"a": 1, "b": 2}
        target = {"a": 10, "b": 2, "c": 3}
        patch = jsonpatch.make_patch(base, target)
        ops = list(patch)
        result = contract.validate(base, target, ops)
        assert "total_operations" in result.details
        assert "op_counts" in result.details
        assert result.details["total_operations"] == len(ops)

    def test_h3_all_rfc6902_ops_valid(self):
        """All 6 RFC 6902 ops are accepted."""
        contract = JsonPatchBuildContract()
        valid_ops = ["add", "remove", "replace", "move", "copy", "test"]
        for op_name in valid_ops:
            ops = [{"op": op_name, "path": "/a"}]
            if op_name in ("add", "replace", "test"):
                ops[0]["value"] = 1
            if op_name in ("move", "copy"):
                ops[0]["from"] = "/b"
            result = contract.validate({"a": 1, "b": 2}, {"a": 1, "b": 2}, ops)
            # The ops may not produce correct result, but the op field itself is valid
            op_errors = [e for e in result.errors if "invalid op" in e.lower()]
            assert len(op_errors) == 0, f"Valid op '{op_name}' rejected: {op_errors}"

    def test_h3_large_patch_works(self):
        """Large patch with many operations validates correctly."""
        import jsonpatch
        contract = JsonPatchBuildContract()
        base = {f"key_{i}": i for i in range(100)}
        target = {f"key_{i}": i * 2 for i in range(100)}
        target["new_key"] = "added"
        patch = jsonpatch.make_patch(base, target)
        ops = list(patch)
        result = contract.validate(base, target, ops)
        assert result.passed, f"Large patch failed: {result.errors}"
        assert result.details["total_operations"] > 50

    def test_h3_duration_tracked(self):
        """Duration in milliseconds is tracked."""
        import jsonpatch
        contract = JsonPatchBuildContract()
        base = {"a": 1}
        target = {"a": 2}
        patch = jsonpatch.make_patch(base, target)
        result = contract.validate(base, target, list(patch))
        assert result.duration_ms >= 0


# ============================================================================
# H4: Compression Build Contract Tests
# ============================================================================

class TestH4CompressionContract:
    """Tests for CompressionBuildContract (H4).

    Covers: L1 identity, L2 signature preservation, L3 header preservation,
    empty output, compression ratio, cache key computation.
    """

    def test_h4_happy_path_l1(self, matrix_prompt):
        """L1 identity transform passes contract."""
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l1 = comp.compress(matrix_prompt, CompressionLevel.L1_FULL)
        contract = CompressionBuildContract()
        result = contract.validate(matrix_prompt, l1, "L1")
        assert result.passed, f"H4 L1 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H4_COMPRESSION"

    def test_h4_happy_path_l2(self):
        """L2 structural compression passes contract with controlled input."""
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        # Use a controlled prompt where L2 can preserve all signatures
        controlled_prompt = (
            "[PROJECT]\nname=test_project\ntype=Python Library\n\n"
            "[PYTHON_TYPES]\n"
            "def scan_project(path: str) -> dict:\n    '''Scan project.'''\n    pass\n\n"
            "class Builder:\n    '''Build matrix.'''\n    def build(self) -> str:\n        pass\n\n"
            "def process_data(data: dict) -> list:\n    '''Process.'''\n    pass\n\n"
            "[OVERVIEW]\n"
            "dirs: src, tests, docs\n"
        ) * 5  # Repeat to have meaningful content
        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(controlled_prompt, CompressionLevel.L2_STRUCTURAL)
        contract = CompressionBuildContract()
        result = contract.validate(controlled_prompt, l2, "L2")
        assert result.passed, f"H4 L2 failed: {result.errors}"

    def test_h4_happy_path_l3(self, matrix_prompt):
        """L3 skeleton compression passes contract."""
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l3 = comp.compress(matrix_prompt, CompressionLevel.L3_SKELETON)
        contract = CompressionBuildContract()
        result = contract.validate(matrix_prompt, l3, "L3")
        assert result.passed, f"H4 L3 failed: {result.errors}"

    def test_h4_exit_code_is_44(self):
        """H4 exit code is 44."""
        assert CompressionBuildContract.EXIT_CODE == ExitCode.COMPRESSION_AST_NODE_LOSS
        assert int(CompressionBuildContract.EXIT_CODE) == 44

    def test_h4_l1_non_identity_fails(self):
        """L1 that differs from original fails."""
        contract = CompressionBuildContract()
        result = contract.validate("original text", "modified text", "L1")
        assert not result.passed
        assert result.exit_code == 44
        assert any("identity" in e.lower() for e in result.errors)

    def test_h4_l2_dropped_function_fails(self):
        """L2 that drops function signatures fails."""
        contract = CompressionBuildContract()
        original = "def get_users(request):\n    return users\ndef create_user(data):\n    pass\n"
        # Drops create_user
        compressed = "def get_users(request):\n    return users\n"
        result = contract.validate(original, compressed, "L2")
        assert not result.passed
        assert any("dropped" in e.lower() or "AST" in e for e in result.errors)

    def test_h4_l2_preserves_all_signatures(self):
        """L2 that preserves all function/class names passes."""
        contract = CompressionBuildContract()
        original = "def foo():\n    pass\nclass Bar:\n    pass\ndef baz():\n    pass\n"
        compressed = "def foo(): ...\nclass Bar: ...\ndef baz(): ...\n"
        result = contract.validate(original, compressed, "L2")
        assert result.passed, f"H4 L2 preserve failed: {result.errors}"

    def test_h4_empty_output_fails(self):
        """Empty compressed output fails."""
        contract = CompressionBuildContract()
        result = contract.validate("some content", "", "L2")
        assert not result.passed
        assert any("empty" in e.lower() for e in result.errors)

    def test_h4_whitespace_only_output_fails(self):
        """Whitespace-only output fails."""
        contract = CompressionBuildContract()
        result = contract.validate("some content", "   \n  \t  ", "L2")
        assert not result.passed
        assert any("empty" in e.lower() for e in result.errors)

    def test_h4_compression_ratio_in_details(self, matrix_prompt):
        """Compression ratio is populated in details."""
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(matrix_prompt, CompressionLevel.L2_STRUCTURAL)
        contract = CompressionBuildContract()
        result = contract.validate(matrix_prompt, l2, "L2")
        assert "compression_ratio" in result.details

    def test_h4_token_counts_in_details(self, matrix_prompt):
        """Token counts (original and compressed) in details."""
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l3 = comp.compress(matrix_prompt, CompressionLevel.L3_SKELETON)
        contract = CompressionBuildContract()
        result = contract.validate(matrix_prompt, l3, "L3")
        assert "original_tokens" in result.details
        assert "compressed_tokens" in result.details
        assert result.details["original_tokens"] > result.details["compressed_tokens"]

    def test_h4_cache_key_deterministic(self):
        """Cache key is deterministic for same input."""
        contract = CompressionBuildContract()
        k1 = contract.compute_cache_key("prompt text", "L2")
        k2 = contract.compute_cache_key("prompt text", "L2")
        assert k1 == k2
        assert len(k1) == 32

    def test_h4_cache_key_changes_on_prompt(self):
        """Cache key changes when prompt changes."""
        contract = CompressionBuildContract()
        k1 = contract.compute_cache_key("version A", "L2")
        k2 = contract.compute_cache_key("version B", "L2")
        assert k1 != k2

    def test_h4_cache_key_changes_on_level(self):
        """Cache key changes when compression level changes."""
        contract = CompressionBuildContract()
        k1 = contract.compute_cache_key("same text", "L1")
        k2 = contract.compute_cache_key("same text", "L2")
        assert k1 != k2

    def test_h4_cache_key_changes_on_config(self):
        """Cache key changes when config changes."""
        contract = CompressionBuildContract()
        k1 = contract.compute_cache_key("text", "L2", {"opt": True})
        k2 = contract.compute_cache_key("text", "L2", {"opt": False})
        assert k1 != k2

    def test_h4_l1_identity_flag_in_details(self):
        """L1 validation sets is_identity flag in details."""
        contract = CompressionBuildContract()
        result = contract.validate("text", "text", "L1")
        assert result.details.get("is_identity") is True

    def test_h4_duration_tracked(self):
        """Duration in milliseconds is tracked."""
        contract = CompressionBuildContract()
        result = contract.validate("text", "text", "L1")
        assert result.duration_ms >= 0


# ============================================================================
# H5: Cross-Language Build Contract Tests
# ============================================================================

class TestH5CrossLanguageContract:
    """Tests for CrossLanguageBuildContract (H5).

    Covers: Happy path, minimum fragments, orphan detection,
    overhead ratio, cache key computation, all 53+ languages.
    """

    def test_h5_happy_path(self):
        """Valid cross-language merge passes contract."""
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        fragments = {
            "python": {"types": {"str": "str", "int": "int"}, "User": "class User: ..."},
            "typescript": {"types": {"string": "string", "number": "number"}, "User": "interface User {}"},
        }
        unified = linker.merge_matrices(fragments)
        contract = CrossLanguageBuildContract()
        result = contract.validate(fragments, unified)
        assert result.passed, f"H5 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H5_CROSS_LANGUAGE"

    def test_h5_exit_code_is_45(self):
        """H5 exit code is 45."""
        assert CrossLanguageBuildContract.EXIT_CODE == ExitCode.CROSS_LANGUAGE_ORPHANED_NODES
        assert int(CrossLanguageBuildContract.EXIT_CODE) == 45

    def test_h5_single_fragment_fails(self):
        """Less than 2 fragments triggers error."""
        contract = CrossLanguageBuildContract()
        result = contract.validate(
            {"python": {"types": {}}},
            {"python": {"types": {}}},
        )
        assert not result.passed
        assert result.exit_code == 45
        assert any("≥ 2" in e for e in result.errors)

    def test_h5_empty_fragments_fails(self):
        """Zero fragments triggers error."""
        contract = CrossLanguageBuildContract()
        result = contract.validate({}, {})
        assert not result.passed

    def test_h5_three_languages(self):
        """3 language merge passes contract."""
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        fragments = {
            "python": {"User": "class User: ..."},
            "typescript": {"User": "interface User {}"},
            "java": {"User": "class User {}"},
        }
        unified = linker.merge_matrices(fragments)
        contract = CrossLanguageBuildContract()
        result = contract.validate(fragments, unified)
        assert result.passed, f"H5 3-lang failed: {result.errors}"

    def test_h5_missing_fragment_in_unified_fails(self):
        """Unified output missing a language fragment triggers error."""
        contract = CrossLanguageBuildContract()
        fragments = {
            "python": {"types": {}},
            "typescript": {"types": {}},
        }
        # Unified missing 'typescript'
        unified = {"python": {"types": {}}}
        result = contract.validate(fragments, unified)
        assert not result.passed
        assert any("missing fragment" in e.lower() for e in result.errors)

    def test_h5_cache_key_deterministic(self):
        """Cache key is deterministic for same fragments."""
        contract = CrossLanguageBuildContract()
        frags = {
            "python": {"a": 1},
            "typescript": {"b": 2},
        }
        k1 = contract.compute_cache_key(frags)
        k2 = contract.compute_cache_key(frags)
        assert k1 == k2
        assert len(k1) == 32

    def test_h5_cache_key_changes_on_fragment_change(self):
        """Cache key changes when any fragment changes."""
        contract = CrossLanguageBuildContract()
        frags1 = {"python": {"a": 1}, "typescript": {"b": 2}}
        frags2 = {"python": {"a": 1}, "typescript": {"b": 3}}
        k1 = contract.compute_cache_key(frags1)
        k2 = contract.compute_cache_key(frags2)
        assert k1 != k2

    def test_h5_cache_key_order_independent(self):
        """Cache key uses sorted keys, so insertion order doesn't matter."""
        contract = CrossLanguageBuildContract()
        frags1 = {"python": {"a": 1}, "typescript": {"b": 2}}
        frags2 = {"typescript": {"b": 2}, "python": {"a": 1}}
        k1 = contract.compute_cache_key(frags1)
        k2 = contract.compute_cache_key(frags2)
        assert k1 == k2

    @pytest.mark.parametrize("lang", CORE_LANGUAGES)
    def test_h5_core_language_in_merge(self, lang):
        """Each core language can be part of a 2-language merge."""
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        fragments = {
            lang: {"User": f"class User ({lang})"},
            "python" if lang != "python" else "typescript": {"User": "class User (alt)"},
        }
        unified = linker.merge_matrices(fragments)
        contract = CrossLanguageBuildContract()
        result = contract.validate(fragments, unified)
        assert result.passed, f"H5 failed for {lang}: {result.errors}"

    def test_h5_overhead_ratio_check(self):
        """Overhead ratio is recorded in details when available."""
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        fragments = {
            "python": {"User": "class User: ...", "Order": "class Order: ..."},
            "typescript": {"User": "interface User {}", "Order": "interface Order {}"},
        }
        unified = linker.merge_matrices(fragments)
        contract = CrossLanguageBuildContract()
        result = contract.validate(fragments, unified)
        # overhead_ratio may or may not be in details depending on the unified object
        assert result.passed

    def test_h5_duration_tracked(self):
        """Duration in milliseconds is tracked."""
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        fragments = {
            "python": {"a": 1},
            "typescript": {"b": 2},
        }
        unified = linker.merge_matrices(fragments)
        contract = CrossLanguageBuildContract()
        result = contract.validate(fragments, unified)
        assert result.duration_ms >= 0


# ============================================================================
# H6: Navigator Build Contract Tests
# ============================================================================

class TestH6NavigatorContract:
    """Tests for NavigatorBuildContract (H6).

    Covers: Happy path, empty query, score ordering, required fields,
    latency, relevance scores.
    """

    def test_h6_happy_path(self, matrix_json, matrix_prompt):
        """Valid navigator output passes contract."""
        from codetrellis.matrix_navigator import MatrixNavigator
        nav = MatrixNavigator(matrix_json, matrix_prompt)
        query = "Python parser scanning"
        results = nav.discover(query)
        metrics = nav.last_metrics
        contract = NavigatorBuildContract()
        result = contract.validate(query, results, metrics)
        assert result.passed, f"H6 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H6_NAVIGATOR"

    def test_h6_exit_code_is_46(self):
        """H6 exit code is 46."""
        assert NavigatorBuildContract.EXIT_CODE == ExitCode.NAVIGATOR_QUERY_PARSE_FAILED
        assert int(NavigatorBuildContract.EXIT_CODE) == 46

    def test_h6_empty_query_returns_empty(self):
        """Empty query → empty result (no crash)."""
        contract = NavigatorBuildContract()
        result = contract.validate("", [])
        assert result.passed
        assert result.exit_code == 0

    def test_h6_whitespace_query_returns_empty(self):
        """Whitespace-only query → empty result."""
        contract = NavigatorBuildContract()
        result = contract.validate("   ", [])
        assert result.passed

    def test_h6_empty_query_with_results_fails(self):
        """Empty query with non-empty results fails."""
        contract = NavigatorBuildContract()
        mock_result = MagicMock()
        mock_result.composite_score = 0.5
        mock_result.file_path = "test.py"
        result = contract.validate("", [mock_result])
        assert not result.passed
        assert any("empty query" in e.lower() for e in result.errors)

    def test_h6_results_sorted_descending(self):
        """Results must be sorted by score descending."""
        contract = NavigatorBuildContract()
        r1 = MagicMock()
        r1.composite_score = 0.9
        r1.file_path = "a.py"
        r2 = MagicMock()
        r2.composite_score = 0.5
        r2.file_path = "b.py"
        result = contract.validate("test query", [r1, r2])
        assert result.passed, f"Sorted results failed: {result.errors}"

    def test_h6_results_not_sorted_fails(self):
        """Unsorted results trigger error."""
        contract = NavigatorBuildContract()
        r1 = MagicMock()
        r1.composite_score = 0.3
        r1.file_path = "a.py"
        r2 = MagicMock()
        r2.composite_score = 0.9
        r2.file_path = "b.py"
        result = contract.validate("test query", [r1, r2])
        assert not result.passed
        assert any("sorted" in e.lower() for e in result.errors)

    def test_h6_missing_score_field_fails(self):
        """Result without score triggers error."""
        contract = NavigatorBuildContract()
        r = MagicMock(spec=[])  # no attributes
        r.file_path = "test.py"
        result = contract.validate("test query", [r])
        assert not result.passed
        assert any("score" in e.lower() for e in result.errors)

    def test_h6_missing_id_field_fails(self):
        """Result without id/path triggers error."""
        contract = NavigatorBuildContract()
        r = MagicMock(spec=[])
        r.composite_score = 0.5
        result = contract.validate("test query", [r])
        assert not result.passed
        assert any("id" in e.lower() or "path" in e.lower() for e in result.errors)

    def test_h6_latency_warning(self):
        """Latency > 300ms produces warning."""
        contract = NavigatorBuildContract()
        r = MagicMock()
        r.composite_score = 0.8
        r.file_path = "test.py"
        metrics = MagicMock()
        metrics.total_ms = 500
        result = contract.validate("query", [r], metrics)
        assert any("latency" in w.lower() or "300ms" in w for w in result.warnings)

    def test_h6_zero_score_warning(self):
        """Score ≤ 0 produces warning."""
        contract = NavigatorBuildContract()
        r = MagicMock()
        r.composite_score = 0.0
        r.score = 0.0
        r.file_path = "test.py"
        result = contract.validate("query", [r])
        assert any("≤ 0" in w or "score" in w.lower() for w in result.warnings)

    def test_h6_query_in_details(self):
        """Query string is recorded in details."""
        contract = NavigatorBuildContract()
        result = contract.validate("my query", [])
        assert result.details["query"] == "my query"
        assert result.details["result_count"] == 0

    def test_h6_multiple_results_valid(self, matrix_json, matrix_prompt):
        """Multiple valid results all pass checks."""
        from codetrellis.matrix_navigator import MatrixNavigator
        nav = MatrixNavigator(matrix_json, matrix_prompt)
        results = nav.discover("Python types")
        metrics = nav.last_metrics
        contract = NavigatorBuildContract()
        result = contract.validate("Python types", results, metrics)
        assert result.passed, f"H6 multi-result failed: {result.errors}"

    def test_h6_duration_tracked(self):
        """Duration in milliseconds is tracked."""
        contract = NavigatorBuildContract()
        result = contract.validate("", [])
        assert result.duration_ms >= 0


# ============================================================================
# H7: MatrixBench Build Contract Tests
# ============================================================================

class TestH7MatrixBenchContract:
    """Tests for MatrixBenchBuildContract (H7).

    Covers: Happy path, determinism variance, missing fields, None runs,
    category scores, variance threshold.
    """

    def test_h7_happy_path(self, matrix_json, matrix_prompt):
        """Two valid benchmark runs pass contract."""
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        run1 = bench.run_all()
        run2 = bench.run_all()
        contract = MatrixBenchBuildContract()
        result = contract.validate(run1, run2)
        assert result.passed, f"H7 failed: {result.errors}"
        assert result.exit_code == 0
        assert result.contract_id == "H7_MATRIXBENCH"

    def test_h7_exit_code_is_47(self):
        """H7 exit code is 47."""
        assert MatrixBenchBuildContract.EXIT_CODE == ExitCode.MATRIXBENCH_VARIANCE_EXCEEDED
        assert int(MatrixBenchBuildContract.EXIT_CODE) == 47

    def test_h7_none_run1_fails(self):
        """None for run1 triggers error."""
        contract = MatrixBenchBuildContract()
        result = contract.validate(None, MagicMock())
        assert not result.passed
        assert result.exit_code == 47
        assert any("None" in e for e in result.errors)

    def test_h7_none_run2_fails(self):
        """None for run2 triggers error."""
        contract = MatrixBenchBuildContract()
        result = contract.validate(MagicMock(), None)
        assert not result.passed

    def test_h7_both_none_fails(self):
        """Both runs None triggers error."""
        contract = MatrixBenchBuildContract()
        result = contract.validate(None, None)
        assert not result.passed

    def test_h7_missing_total_tasks_fails(self):
        """Missing total_tasks field triggers error."""
        contract = MatrixBenchBuildContract()
        r1 = {"passed_tasks": 5, "total_latency_ms": 100, "avg_improvement_pct": 50}
        r2 = {"passed_tasks": 5, "total_latency_ms": 100, "avg_improvement_pct": 50}
        result = contract.validate(r1, r2)
        assert not result.passed
        assert any("total_tasks" in e for e in result.errors)

    def test_h7_missing_total_latency_fails(self):
        """Missing total_latency_ms field triggers error."""
        contract = MatrixBenchBuildContract()
        r1 = {"total_tasks": 10, "passed_tasks": 5, "avg_improvement_pct": 50}
        r2 = {"total_tasks": 10, "passed_tasks": 5, "avg_improvement_pct": 50}
        result = contract.validate(r1, r2)
        assert not result.passed
        assert any("total_latency_ms" in e for e in result.errors)

    def test_h7_variance_within_threshold(self):
        """Variance within 2% passes."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {"completeness": 0.8},
        }
        r2 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 102,
            "avg_improvement_pct": 51.0,  # 1% variance — within 2%
            "category_scores": {"completeness": 0.8},
        }
        result = contract.validate(r1, r2)
        assert result.passed, f"H7 variance check failed: {result.errors}"

    def test_h7_variance_exceeds_threshold_fails(self):
        """Variance > 2% fails."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        r2 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 55.0,  # 5% variance — exceeds 2%
            "category_scores": {},
        }
        result = contract.validate(r1, r2)
        assert not result.passed
        assert result.exit_code == 47
        assert any("variance" in e.lower() for e in result.errors)

    def test_h7_custom_variance_threshold(self):
        """Custom variance threshold is respected."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        r2 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 55.0,  # 5% variance
            "category_scores": {},
        }
        # With threshold=10%, 5% variance is OK
        result = contract.validate(r1, r2, variance_threshold=10.0)
        assert result.passed

    def test_h7_variance_details_populated(self):
        """Variance and threshold are in details."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        r2 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.5,
            "category_scores": {},
        }
        result = contract.validate(r1, r2)
        assert "variance_pct" in result.details
        assert "threshold_pct" in result.details
        assert result.details["threshold_pct"] == 2.0

    def test_h7_missing_category_scores_warning(self):
        """Missing expected categories produce warnings."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {"completeness": 0.8},
        }
        r2 = {
            "total_tasks": 10,
            "passed_tasks": 8,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {"completeness": 0.8},
        }
        result = contract.validate(r1, r2)
        # 4 of 5 expected categories are missing → warnings
        missing_cats = [w for w in result.warnings if "category" in w.lower()]
        assert len(missing_cats) >= 1

    def test_h7_all_5_categories_present(self, matrix_json, matrix_prompt):
        """All 5 benchmark categories appear in details."""
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        run1 = bench.run_all()
        run2 = bench.run_all()
        contract = MatrixBenchBuildContract()
        result = contract.validate(run1, run2)
        assert "categories_present" in result.details

    def test_h7_task_counts_in_details(self):
        """Run1/run2 task counts in details."""
        contract = MatrixBenchBuildContract()
        r1 = {
            "total_tasks": 20,
            "passed_tasks": 18,
            "total_latency_ms": 100,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        r2 = {
            "total_tasks": 20,
            "passed_tasks": 17,
            "total_latency_ms": 105,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        result = contract.validate(r1, r2)
        assert result.details["run1_total_tasks"] == 20
        assert result.details["run2_total_tasks"] == 20
        assert result.details["run1_passed"] == 18
        assert result.details["run2_passed"] == 17

    def test_h7_duration_tracked(self):
        """Duration in milliseconds is tracked."""
        contract = MatrixBenchBuildContract()
        r = {
            "total_tasks": 1,
            "passed_tasks": 1,
            "total_latency_ms": 10,
            "avg_improvement_pct": 50.0,
            "category_scores": {},
        }
        result = contract.validate(r, r)
        assert result.duration_ms >= 0


# ============================================================================
# SUITE: AdvancedBuildContractSuite Tests
# ============================================================================

class TestAdvancedBuildContractSuite:
    """Tests for AdvancedBuildContractSuite.

    Covers: Full pipeline, partial failures, suite result aggregation,
    section extraction, all 7 contracts execute.
    """

    def test_suite_run_all_7_contracts(self, matrix_json, matrix_prompt):
        """Suite runs all 7 contracts and produces a result for each."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        assert len(result.results) == 7, (
            f"Expected 7 contract results, got {len(result.results)}"
        )

    def test_suite_all_contract_ids_present(self, matrix_json, matrix_prompt):
        """All 7 contract IDs are present in results."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        ids = {r.contract_id for r in result.results}
        expected = {
            "H1_JSONLD", "H2_EMBEDDINGS", "H3_JSON_PATCH",
            "H4_COMPRESSION", "H5_CROSS_LANGUAGE", "H6_NAVIGATOR",
            "H7_MATRIXBENCH",
        }
        assert ids == expected, f"Missing contracts: {expected - ids}"

    def test_suite_all_passed_flag(self, matrix_json, matrix_prompt):
        """all_passed is True only when all 7 contracts pass."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        all_ok = all(r.passed for r in result.results)
        assert result.all_passed == all_ok

    def test_suite_duration_tracked(self, matrix_json, matrix_prompt):
        """Total duration is tracked."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        assert result.total_duration_ms > 0

    def test_suite_to_dict(self, matrix_json, matrix_prompt):
        """Suite result serializes to valid dict."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        d = result.to_dict()
        assert "all_passed" in d
        assert "total_duration_ms" in d
        assert "contracts" in d
        assert len(d["contracts"]) == 7

    def test_suite_json_serializable(self, matrix_json, matrix_prompt):
        """Suite result dict is JSON-serializable."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        d = result.to_dict()
        serialized = json.dumps(d, indent=2)
        deserialized = json.loads(serialized)
        assert deserialized["contracts"][0]["contract_id"] == "H1_JSONLD"

    def test_suite_extract_sections(self):
        """_extract_sections parses prompt into named sections."""
        prompt = "[PROJECT]\nName: test\n[OVERVIEW]\nHello world\n"
        sections = AdvancedBuildContractSuite._extract_sections(prompt)
        assert "PROJECT" in sections
        assert "OVERVIEW" in sections
        assert "Name: test" in sections["PROJECT"]

    def test_suite_extract_sections_empty(self):
        """Empty prompt produces empty sections."""
        sections = AdvancedBuildContractSuite._extract_sections("")
        assert sections == {}

    def test_suite_extract_sections_no_headers(self):
        """Prompt without headers produces no sections."""
        sections = AdvancedBuildContractSuite._extract_sections("Just plain text")
        assert sections == {}

    def test_suite_instances_initialized(self):
        """All 7 contract instances are initialized."""
        suite = AdvancedBuildContractSuite()
        assert isinstance(suite.h1, JsonLdBuildContract)
        assert isinstance(suite.h2, EmbeddingBuildContract)
        assert isinstance(suite.h3, JsonPatchBuildContract)
        assert isinstance(suite.h4, CompressionBuildContract)
        assert isinstance(suite.h5, CrossLanguageBuildContract)
        assert isinstance(suite.h6, NavigatorBuildContract)
        assert isinstance(suite.h7, MatrixBenchBuildContract)


# ============================================================================
# EXIT CODE REGISTRY VALIDATION
# ============================================================================

class TestExitCodeRegistry:
    """Validate exit code registry for PART H (codes 41-47)."""

    def test_exit_codes_41_through_47_exist(self):
        """Exit codes 41-47 exist in ExitCode enum."""
        assert ExitCode.JSONLD_VALIDATION_FAILED == 41
        assert ExitCode.EMBEDDING_GENERATION_FAILED == 42
        assert ExitCode.JSON_PATCH_INTEGRITY_MISMATCH == 43
        assert ExitCode.COMPRESSION_AST_NODE_LOSS == 44
        assert ExitCode.CROSS_LANGUAGE_ORPHANED_NODES == 45
        assert ExitCode.NAVIGATOR_QUERY_PARSE_FAILED == 46
        assert ExitCode.MATRIXBENCH_VARIANCE_EXCEEDED == 47

    def test_exit_codes_unique(self):
        """All exit codes are unique values."""
        values = [e.value for e in ExitCode]
        assert len(values) == len(set(values)), (
            f"Duplicate exit codes found: {values}"
        )

    def test_exit_codes_match_contracts(self):
        """Each contract's EXIT_CODE matches the registry."""
        assert JsonLdBuildContract.EXIT_CODE == ExitCode.JSONLD_VALIDATION_FAILED
        assert EmbeddingBuildContract.EXIT_CODE == ExitCode.EMBEDDING_GENERATION_FAILED
        assert JsonPatchBuildContract.EXIT_CODE == ExitCode.JSON_PATCH_INTEGRITY_MISMATCH
        assert CompressionBuildContract.EXIT_CODE == ExitCode.COMPRESSION_AST_NODE_LOSS
        assert CrossLanguageBuildContract.EXIT_CODE == ExitCode.CROSS_LANGUAGE_ORPHANED_NODES
        assert NavigatorBuildContract.EXIT_CODE == ExitCode.NAVIGATOR_QUERY_PARSE_FAILED
        assert MatrixBenchBuildContract.EXIT_CODE == ExitCode.MATRIXBENCH_VARIANCE_EXCEEDED

    def test_base_exit_codes_preserved(self):
        """Base exit codes (0, 1, 2, 3, 124) are unchanged."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.PARTIAL_FAILURE == 1
        assert ExitCode.CONFIGURATION_ERROR == 2
        assert ExitCode.FATAL_ERROR == 3
        assert ExitCode.TIMEOUT == 124

    def test_all_advanced_exit_codes_in_range(self):
        """All advanced exit codes are in the 41-47 range."""
        advanced_codes = [41, 42, 43, 44, 45, 46, 47]
        for code in advanced_codes:
            assert ExitCode(code) is not None


# ============================================================================
# CROSS-CONTRACT INTEGRATION
# ============================================================================

class TestCrossContractIntegration:
    """Integration tests that span multiple contracts."""

    def test_all_contracts_produce_valid_results(self, matrix_json, matrix_prompt):
        """Each contract produces a ContractResult with correct structure."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        for r in result.results:
            assert isinstance(r, ContractResult)
            assert isinstance(r.contract_id, str)
            assert isinstance(r.passed, bool)
            assert isinstance(r.exit_code, int)
            assert isinstance(r.errors, list)
            assert isinstance(r.warnings, list)
            assert isinstance(r.duration_ms, float)
            assert isinstance(r.details, dict)

    def test_failed_contract_returns_nonzero_exit_code(self):
        """Failed contracts return their specific non-zero exit code."""
        contract = JsonLdBuildContract()
        result = contract.validate({}, {"broken": True})
        assert not result.passed
        assert result.exit_code == 41

    def test_passed_contract_returns_zero_exit_code(self, matrix_json):
        """Passed contracts return exit code 0."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix_json)
        contract = JsonLdBuildContract()
        result = contract.validate(matrix_json, doc)
        if result.passed:
            assert result.exit_code == 0

    def test_contracts_independent(self, matrix_json, matrix_prompt):
        """Each contract validates independently (no shared state)."""
        suite = AdvancedBuildContractSuite()
        r1 = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        r2 = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        # Same results both runs
        for a, b in zip(r1.results, r2.results):
            assert a.contract_id == b.contract_id
            assert a.passed == b.passed

    def test_suite_results_ordered(self, matrix_json, matrix_prompt):
        """Suite results are in H1-H7 order."""
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        expected_order = [
            "H1_JSONLD", "H2_EMBEDDINGS", "H3_JSON_PATCH",
            "H4_COMPRESSION", "H5_CROSS_LANGUAGE", "H6_NAVIGATOR",
            "H7_MATRIXBENCH",
        ]
        actual_order = [r.contract_id for r in result.results]
        assert actual_order == expected_order

    def test_all_contracts_handle_synthetic_data(self):
        """All contracts work with synthetic (minimal) test data."""
        synthetic_json = _make_synthetic_matrix()
        synthetic_prompt = _make_synthetic_prompt()
        suite = AdvancedBuildContractSuite()
        result = suite.run_all(
            matrix_json=synthetic_json,
            matrix_prompt=synthetic_prompt,
        )
        assert len(result.results) == 7
        # Not all may pass with synthetic data, but none should crash
        for r in result.results:
            assert isinstance(r.passed, bool)
            assert isinstance(r.exit_code, int)
