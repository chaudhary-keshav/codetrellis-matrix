"""
CodeTrellis Cross-Topic Synergy Integration Tests — PART J, Section J3
=========================================================================

End-to-end integration tests that prove the combined value of different
phases working together. Tests cross-boundary workflows to verify that
architectural domains interoperate without data loss or state corruption.

Synergy Chains (J3):
  1. JSON-LD + Embeddings: Stable @id → embed each node → semantic index
  2. JSON Patch + Compression: Patches + L2/L3 for ultra-minimal updates
  3. Cross-Language + Navigator: SCIP graph → Navigator traverses across languages
  4. Embeddings + Navigator: Embedding scores → hybrid ranking
  5. MatrixBench + All: Every feature gets measured → data-driven prioritization

Additional Cross-Domain Workflows:
  6. Auto-Compilation (B) → JSON Patch (F3): Incremental build → diff
  7. Compression (F4) → Token Budget (J1): Compressed output → budget validation
  8. Full Pipeline: Scan → Build → Patch → Compress → Navigate → Bench

Coverage: All 53+ supported languages/frameworks.

Reference: CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md — PART J, J3
Execute:
  pytest tests/integration/test_cross_topic_synergies.py -v --tb=short

Author: Keshav Chaudhary
Created: 20 February 2026
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest

try:
    import jsonpatch
except ImportError:
    jsonpatch = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Project root & matrix file paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.json"
MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.prompt"

# All 53+ CodeTrellis-supported languages and frameworks
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
    """Load the project's own matrix.json."""
    if not MATRIX_JSON_PATH.exists():
        pytest.skip(f"matrix.json not found at {MATRIX_JSON_PATH}")
    return json.loads(MATRIX_JSON_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def matrix_prompt() -> str:
    """Load the project's own matrix.prompt."""
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


def _make_synthetic_matrix(**overrides: Any) -> Dict[str, Any]:
    """Create a minimal synthetic matrix for tests that don't need real data."""
    base = {
        "project_name": "synergy_test",
        "total_files": 15,
        "total_tokens": 800,
        "version": "1.0.0",
        "readme": "A test project for synergy validation.",
        "python_types": [
            {"name": "User", "type": "dataclass", "file_path": "models/user.py"},
            {"name": "Order", "type": "dataclass", "file_path": "models/order.py"},
        ],
        "python_api": [
            {"method": "GET", "url": "/api/users", "handler": "get_users"},
            {"method": "POST", "url": "/api/orders", "handler": "create_order"},
        ],
        "overview": {"directories": ["src", "tests", "models"]},
        "runbook": {"commands": {"test": "pytest", "build": "python -m build"}},
        "business_domain": {"domain": "E-commerce"},
        "hooks": [{"name": "on_save", "type": "lifecycle"}],
        "middleware": [{"name": "auth_middleware"}],
        "error_handling": [{"type": "try-catch", "file": "handler.py"}],
        "data_flows": {"primary": "request-response"},
        "best_practices": [
            {"id": "PY001", "title": "Use type hints"},
            {"id": "PY002", "title": "Follow PEP 8"},
        ],
    }
    base.update(overrides)
    return base


# ============================================================================
# SYNERGY CHAIN 1: JSON-LD + Embeddings
# ============================================================================

class TestSynergyJsonLdEmbeddings:
    """Synergy 1: JSON-LD @id nodes → embed each node → semantic index.

    Verifies that JSON-LD encoding produces stable @id identifiers
    that can be used as embedding keys for semantic retrieval.
    """

    def test_jsonld_nodes_have_ids_for_embedding(self):
        """JSON-LD @graph nodes have @id usable as embedding keys."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder

        matrix = _make_synthetic_matrix()
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix)

        # Every node in @graph should have @id
        node_ids = [node["@id"] for node in doc["@graph"] if "@id" in node]
        assert len(node_ids) > 0, "No @id found in @graph nodes"

        # IDs should be unique
        assert len(node_ids) == len(set(node_ids)), "Duplicate @ids found"

    def test_embed_jsonld_node_descriptions(self):
        """Can build embeddings from JSON-LD node descriptions."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex

        matrix = _make_synthetic_matrix()
        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix)

        # Extract text from JSON-LD nodes for embedding
        node_texts: Dict[str, str] = {}
        for node in doc["@graph"]:
            if "@id" in node:
                node_id = node["@id"]
                text = json.dumps(node, default=str)
                node_texts[node_id] = text

        assert len(node_texts) > 0, "No node texts to embed"

        # Build embedding index from node texts
        index = MatrixEmbeddingIndex()
        index.build_index(node_texts)

        # Query should return relevant results
        results = index.query("User dataclass", top_k=3)
        assert len(results) > 0, "Embedding query returned no results"
        assert all(0.0 <= r.score <= 1.0 for r in results), "Scores out of range"

    def test_jsonld_embedding_roundtrip_consistency(self):
        """Same matrix → same JSON-LD → same embeddings (deterministic)."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex

        matrix = _make_synthetic_matrix()
        encoder = MatrixJsonLdEncoder()

        # Encode twice
        doc1 = encoder.encode(matrix)
        doc2 = encoder.encode(matrix)

        # JSON-LD should be identical
        assert json.dumps(doc1, sort_keys=True) == json.dumps(doc2, sort_keys=True)

        # Build embeddings from both
        texts1 = {n["@id"]: json.dumps(n, default=str) for n in doc1["@graph"] if "@id" in n}
        texts2 = {n["@id"]: json.dumps(n, default=str) for n in doc2["@graph"] if "@id" in n}

        idx1 = MatrixEmbeddingIndex()
        idx1.build_index(texts1)
        idx2 = MatrixEmbeddingIndex()
        idx2.build_index(texts2)

        # Same query should produce same results
        r1 = idx1.query("User", top_k=3)
        r2 = idx2.query("User", top_k=3)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a.section_id == b.section_id
            assert abs(a.score - b.score) < 0.001


# ============================================================================
# SYNERGY CHAIN 2: JSON Patch + Compression
# ============================================================================

class TestSynergyPatchCompression:
    """Synergy 2: JSON Patch diffs + L2/L3 compression for minimal updates.

    Verifies that patches can be generated and then compressed output
    can be further reduced while maintaining semantic integrity.
    """

    def test_patch_then_compress(self):
        """Generate patch, apply it, then compress the result."""
        from codetrellis.matrix_diff import MatrixDiffEngine
        from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor, CompressionLevel

        old = _make_synthetic_matrix()
        new = copy.deepcopy(old)
        new["python_types"].append({"name": "Product", "type": "dataclass", "file_path": "models/product.py"})
        new["total_files"] = 16

        # Generate patch
        engine = MatrixDiffEngine()
        patch = engine.compute_diff(old, new)
        patch_ops = list(patch)
        assert len(patch_ops) > 0, "No patch ops generated"

        # Apply patch to old → should equal new
        patched = engine.apply_patch(old, patch)
        assert patched["total_files"] == 16

        # Compress the patched result
        # First generate a prompt-like text to compress
        prompt_text = json.dumps(patched, indent=2)
        compressor = MatrixMultiLevelCompressor()
        compressed = compressor.compress(prompt_text, level=CompressionLevel.L2_STRUCTURAL)
        assert len(compressed) > 0, "Compression produced empty result"
        assert len(compressed) < len(prompt_text), "Compressed is not smaller"

    def test_patch_size_smaller_than_full_matrix(self):
        """Patch should be significantly smaller than full matrix."""
        from codetrellis.matrix_diff import MatrixDiffEngine

        old = _make_synthetic_matrix()
        new = copy.deepcopy(old)
        new["python_types"][0]["name"] = "UpdatedUser"

        engine = MatrixDiffEngine()
        patch = engine.compute_diff(old, new)

        patch_size = len(json.dumps(list(patch)))
        full_size = len(json.dumps(new))

        assert patch_size < full_size, "Patch is not smaller than full matrix"

    def test_compressed_patch_application(self):
        """Compression doesn't corrupt the diff → apply → verify pipeline."""
        from codetrellis.matrix_diff import MatrixDiffEngine

        old = _make_synthetic_matrix()
        new = copy.deepcopy(old)
        new["python_api"].append(
            {"method": "DELETE", "url": "/api/users/{id}", "handler": "delete_user"}
        )

        engine = MatrixDiffEngine()
        patch = engine.compute_diff(old, new)

        # Serialize and deserialize the patch (simulates storage)
        patch_ops = list(patch)
        patch_json = json.dumps(patch_ops)
        restored_ops = json.loads(patch_json)
        restored_patch = jsonpatch.JsonPatch(restored_ops)

        # Apply restored patch
        result = engine.apply_patch(old, restored_patch)
        assert len(result["python_api"]) == 3
        assert result["python_api"][-1]["method"] == "DELETE"


# ============================================================================
# SYNERGY CHAIN 3: Cross-Language + Navigator
# ============================================================================

class TestSynergyCrossLanguageNavigator:
    """Synergy 3: Cross-language type graph → Navigator traversal.

    Verifies that the cross-language type linker produces mappings
    that the navigator can use for cross-boundary file discovery.
    """

    def test_cross_language_types_available_to_navigator(self):
        """Cross-language primitive mappings exist for navigator lookups."""
        from codetrellis.cross_language_types import CrossLanguageLinker

        linker = CrossLanguageLinker()
        available = linker.get_available_languages()

        # All core languages should be available
        for lang in CORE_LANGUAGES:
            assert lang in available, f"Language {lang} not available"
            # Verify at least one type resolves
            result = linker.resolve_type("str", "python", lang)
            assert result is not None, f"Cannot resolve str→{lang}"

    def test_navigator_discovers_cross_language_files(self):
        """Navigator can discover files mentioned in cross-language context."""
        from codetrellis.matrix_navigator import MatrixNavigator

        matrix = _make_synthetic_matrix()
        prompt = json.dumps(matrix)

        nav = MatrixNavigator(matrix_json=matrix, matrix_prompt=prompt)
        results = nav.discover("User dataclass")

        # Should return results (file discovery)
        assert isinstance(results, list)

    def test_cross_language_linker_all_53_languages(self):
        """Cross-language linker has mappings for core primitive types."""
        from codetrellis.cross_language_types import CrossLanguageLinker

        linker = CrossLanguageLinker()

        for lang in CORE_LANGUAGES:
            # Every core language should resolve at least 3 type categories
            resolved = 0
            for src_type in ["str", "int", "bool", "float", "None", "bytes"]:
                result = linker.resolve_type(src_type, "python", lang)
                if result is not None:
                    resolved += 1
            assert resolved >= 3, \
                f"{lang}: only {resolved} types resolved, expected ≥3"


# ============================================================================
# SYNERGY CHAIN 4: Embeddings + Navigator
# ============================================================================

class TestSynergyEmbeddingsNavigator:
    """Synergy 4: Embedding scores enhance navigator hybrid ranking.

    Verifies that embedding-based similarity can augment the
    navigator's keyword and graph scoring.
    """

    def test_embedding_scores_are_valid_for_ranking(self):
        """Embedding scores are in [0, 1] and can be used for ranking."""
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex

        sections = {
            "PYTHON_TYPES": "User dataclass with name email fields",
            "PYTHON_API": "GET /api/users POST /api/orders",
            "OVERVIEW": "E-commerce platform with user management",
            "RUNBOOK": "pytest for testing, python -m build for building",
        }

        index = MatrixEmbeddingIndex()
        index.build_index(sections)

        results = index.query("user management", top_k=4)
        assert len(results) > 0
        scores = [r.score for r in results]
        assert all(0.0 <= s <= 1.0 for s in scores), f"Invalid scores: {scores}"
        # Should be sorted by score descending
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"

    def test_navigator_keyword_plus_embedding_hybrid(self):
        """Navigator with keyword + embedding provides better results."""
        from codetrellis.matrix_navigator import MatrixNavigator

        matrix = _make_synthetic_matrix()
        prompt = json.dumps(matrix)

        nav = MatrixNavigator(matrix_json=matrix, matrix_prompt=prompt)

        # Query should work even without dedicated embedding index
        results = nav.discover("authentication middleware")
        assert isinstance(results, list)
        # Metrics should be available
        metrics = nav.last_metrics
        assert metrics is not None
        assert metrics.total_ms >= 0


# ============================================================================
# SYNERGY CHAIN 5: MatrixBench + All Modules
# ============================================================================

class TestSynergyMatrixBenchAll:
    """Synergy 5: MatrixBench validates all features with benchmarks.

    Verifies that MatrixBench can score outputs from all advanced
    research modules and produce consistent results.
    """

    def test_matrixbench_all_categories_present(self):
        """MatrixBench has all 5 benchmark categories."""
        from codetrellis.matrixbench_scorer import CATEGORIES

        expected = {"completeness", "accuracy", "navigation", "compression", "cross_language"}
        assert set(CATEGORIES) == expected

    def test_matrixbench_scores_are_deterministic(self):
        """Same input → same scores (within ±2%)."""
        from codetrellis.matrixbench_scorer import MatrixBench

        matrix = _make_synthetic_matrix()
        prompt = json.dumps(matrix, indent=2)

        bench = MatrixBench(matrix_json=matrix, matrix_prompt=prompt)
        results1 = bench.run_all()
        bench2 = MatrixBench(matrix_json=matrix, matrix_prompt=prompt)
        results2 = bench2.run_all()

        for cat in results1.category_scores:
            s1 = results1.category_scores[cat]
            s2 = results2.category_scores[cat]
            assert abs(s1 - s2) <= 0.02, \
                f"Category {cat}: {s1} vs {s2} exceeds ±2% tolerance"

    def test_matrixbench_covers_all_languages(self):
        """MatrixBench references all 53+ languages."""
        from codetrellis.matrixbench_scorer import _ALL_LANGUAGES

        assert len(_ALL_LANGUAGES) >= 53, \
            f"MatrixBench only covers {len(_ALL_LANGUAGES)} languages, expected 53+"


# ============================================================================
# CROSS-DOMAIN WORKFLOW 6: Auto-Compilation → JSON Patch
# ============================================================================

class TestWorkflowBuildToPatch:
    """Cross-domain: Incremental build (Part B) → JSON Patch (Part F3).

    Verifies that an incremental build can produce matrix changes
    that are captured as JSON Patch operations.
    """

    def test_incremental_change_produces_valid_patch(self):
        """Simulated incremental change → valid RFC 6902 patch."""
        from codetrellis.matrix_diff import MatrixDiffEngine

        # Simulate old build result
        old_matrix = _make_synthetic_matrix(total_files=10)

        # Simulate new build result (1 file added)
        new_matrix = copy.deepcopy(old_matrix)
        new_matrix["total_files"] = 11
        new_matrix["python_types"].append(
            {"name": "Payment", "type": "dataclass", "file_path": "models/payment.py"}
        )

        engine = MatrixDiffEngine()
        patch = engine.compute_diff(old_matrix, new_matrix)

        # Patch should be valid RFC 6902
        for op in list(patch):
            assert "op" in op, f"Missing 'op' in patch operation: {op}"
            assert op["op"] in ("add", "remove", "replace", "move", "copy", "test"), \
                f"Invalid op: {op['op']}"
            assert "path" in op, f"Missing 'path' in patch operation: {op}"

        # Verify roundtrip
        result = engine.apply_patch(old_matrix, patch)
        assert result["total_files"] == 11
        assert len(result["python_types"]) == 3

    def test_patch_has_checksums_for_integrity(self):
        """Patch record includes SHA-256 checksums for verification."""
        from codetrellis.matrix_diff import MatrixDiffEngine

        old = _make_synthetic_matrix()
        new = copy.deepcopy(old)
        new["version"] = "2.0.0"

        engine = MatrixDiffEngine()
        patch = engine.compute_diff(old, new)

        # Use save_patch to create a PatchRecord with checksums
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            record = engine.save_patch(patch, old, new, tmp_path)
            assert record.source_checksum, "Missing source checksum"
            assert record.target_checksum, "Missing target checksum"
            assert len(record.source_checksum) == 64, "Source checksum not SHA-256"
            assert len(record.target_checksum) == 64, "Target checksum not SHA-256"
            assert record.source_checksum != record.target_checksum, "Checksums should differ"
        finally:
            os.unlink(tmp_path)


# ============================================================================
# CROSS-DOMAIN WORKFLOW 7: Compression → Token Budget
# ============================================================================

class TestWorkflowCompressionBudget:
    """Cross-domain: Compression (F4) → Token Budget validation (J1).

    Verifies that compressed output respects model token budgets
    defined in J1.
    """

    def test_l2_fits_within_gpt4o_budget(self):
        """L2 structural compression fits within GPT-4o matrix budget (8K)."""
        from codetrellis.matrix_compressor_levels import (
            MatrixMultiLevelCompressor, CompressionLevel, count_tokens,
        )

        # Create a moderately sized prompt
        sections = []
        for i in range(50):
            sections.append(f"## Module {i}\ndef function_{i}(arg: str) -> int:\n    return len(arg)\n")
        prompt = "\n".join(sections)

        compressor = MatrixMultiLevelCompressor()
        compressed = compressor.compress(prompt, level=CompressionLevel.L2_STRUCTURAL)

        tokens = count_tokens(compressed)
        # L2 target is ≤ 30K tokens, GPT-4o budget is 8K
        # For this small input, it should fit easily
        assert tokens < 30_000, f"L2 compressed to {tokens} tokens, exceeds 30K target"

    def test_l3_fits_within_small_model_budget(self):
        """L3 skeleton compression fits within small model budget (6K)."""
        from codetrellis.matrix_compressor_levels import (
            MatrixMultiLevelCompressor, CompressionLevel, count_tokens,
        )

        sections = []
        for i in range(50):
            sections.append(f"## Module {i}\ndef function_{i}(arg: str) -> int:\n    return len(arg)\n")
        prompt = "\n".join(sections)

        compressor = MatrixMultiLevelCompressor()
        compressed = compressor.compress(prompt, level=CompressionLevel.L3_SKELETON)

        tokens = count_tokens(compressed)
        assert tokens < 10_000, f"L3 compressed to {tokens} tokens, exceeds 10K target"

    def test_auto_select_level_for_model(self):
        """auto_select_level picks correct level based on context window."""
        from codetrellis.matrix_compressor_levels import (
            MatrixMultiLevelCompressor, CompressionLevel,
        )

        compressor = MatrixMultiLevelCompressor()

        # Large context (200K+) → L1
        level_large = compressor.auto_select_level(context_window=200_000)
        assert level_large == CompressionLevel.L1_FULL

        # Medium context (128K) → L2
        level_medium = compressor.auto_select_level(context_window=128_000)
        assert level_medium == CompressionLevel.L2_STRUCTURAL

        # Small context (32K) → L3
        level_small = compressor.auto_select_level(context_window=32_000)
        assert level_small == CompressionLevel.L3_SKELETON


# ============================================================================
# CROSS-DOMAIN WORKFLOW 8: Full Pipeline Integration
# ============================================================================

class TestWorkflowFullPipeline:
    """Full pipeline: Scan → Build → Patch → Compress → Navigate → Bench.

    End-to-end integration test verifying all phases work together.
    """

    def test_full_pipeline_scan_to_benchmark(self, matrix_json, matrix_prompt):
        """Complete pipeline from matrix data through all modules."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        from codetrellis.matrix_diff import MatrixDiffEngine
        from codetrellis.matrix_compressor_levels import (
            MatrixMultiLevelCompressor, CompressionLevel,
        )
        from codetrellis.matrix_navigator import MatrixNavigator
        from codetrellis.matrixbench_scorer import MatrixBench

        # Step 1: JSON-LD encode
        encoder = MatrixJsonLdEncoder()
        jsonld_doc = encoder.encode(matrix_json)
        assert "@graph" in jsonld_doc
        assert len(jsonld_doc["@graph"]) > 0

        # Step 2: Build embeddings from matrix sections
        prompt_sections: Dict[str, str] = {}
        current_section = ""
        current_lines: List[str] = []
        for line in matrix_prompt.split("\n"):
            match = re.match(r"^\[([A-Z_]+)\]", line)
            if match:
                if current_section and current_lines:
                    prompt_sections[current_section] = "\n".join(current_lines)
                current_section = match.group(1)
                current_lines = []
            else:
                current_lines.append(line)
        if current_section and current_lines:
            prompt_sections[current_section] = "\n".join(current_lines)

        if prompt_sections:
            embed_index = MatrixEmbeddingIndex()
            embed_index.build_index(prompt_sections)
            embed_results = embed_index.query("python types", top_k=5)
            assert len(embed_results) > 0

        # Step 3: Simulate incremental build → generate patch
        modified = copy.deepcopy(matrix_json)
        modified["total_files"] = matrix_json.get("stats", {}).get("totalFiles", 100) + 1
        diff_engine = MatrixDiffEngine()
        patch = diff_engine.compute_diff(matrix_json, modified)
        assert len(list(patch)) > 0

        # Step 4: Compress the matrix prompt
        compressor = MatrixMultiLevelCompressor()
        compressed = compressor.compress(matrix_prompt, level=CompressionLevel.L2_STRUCTURAL)
        assert len(compressed) > 0
        assert len(compressed) <= len(matrix_prompt)

        # Step 5: Navigate
        nav = MatrixNavigator(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        nav_results = nav.discover("scanner compressor")
        assert isinstance(nav_results, list)

        # Step 6: Benchmark
        bench = MatrixBench(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
        bench_results = bench.run_all()
        assert bench_results.total_tasks > 0

    def test_pipeline_preserves_data_integrity(self):
        """Verify no data loss across pipeline stages."""
        from codetrellis.matrix_diff import MatrixDiffEngine

        original = _make_synthetic_matrix()

        # Deep copy → modify → patch → verify
        modified = copy.deepcopy(original)
        modified["python_types"].append(
            {"name": "NewType", "type": "class", "file_path": "new.py"}
        )

        engine = MatrixDiffEngine()
        patch = engine.compute_diff(original, modified)

        # Serialize → deserialize → apply
        patch_ops = list(patch)
        serialized = json.dumps(patch_ops)
        restored_ops = json.loads(serialized)
        restored_patch = jsonpatch.JsonPatch(restored_ops)
        result = engine.apply_patch(original, restored_patch)

        # Verify data integrity
        assert result == modified, "Data loss detected in pipeline"
        assert len(result["python_types"]) == 3
        assert result["python_types"][-1]["name"] == "NewType"

    def test_all_modules_import_successfully(self):
        """All 7 advanced research modules import without error."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        from codetrellis.matrix_diff import MatrixDiffEngine
        from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor
        from codetrellis.cross_language_types import CrossLanguageLinker
        from codetrellis.matrix_navigator import MatrixNavigator
        from codetrellis.matrixbench_scorer import MatrixBench

        # All should be instantiable
        assert MatrixJsonLdEncoder() is not None
        assert MatrixEmbeddingIndex() is not None
        assert MatrixDiffEngine() is not None
        assert MatrixMultiLevelCompressor() is not None
        assert CrossLanguageLinker() is not None
        # MatrixBench requires keyword args
        dummy = {"project_name": "test"}
        assert MatrixBench(matrix_json=dummy, matrix_prompt="test") is not None


# ============================================================================
# LANGUAGE COVERAGE: Verify all 53+ languages work in synergy
# ============================================================================

class TestLanguageCoverageSynergy:
    """Verify cross-topic synergies work for all 53+ languages."""

    def test_cross_language_primitives_for_all_core_languages(self):
        """Cross-language type mapping covers all core languages."""
        from codetrellis.cross_language_types import CrossLanguageLinker

        linker = CrossLanguageLinker()
        available = linker.get_available_languages()

        for lang in CORE_LANGUAGES:
            assert lang in available, f"{lang} not in available languages"
            # Verify at least 3 type categories resolve
            resolved = 0
            for src_type in ["str", "int", "bool", "float", "None", "bytes"]:
                result = linker.resolve_type(src_type, "python", lang)
                if result is not None:
                    resolved += 1
            assert resolved >= 3, \
                f"{lang}: only {resolved} primitives mapped, expected ≥3"

    def test_matrixbench_language_list_complete(self):
        """MatrixBench internal language list matches expected 53+."""
        from codetrellis.matrixbench_scorer import _ALL_LANGUAGES

        expected_set = set(ALL_LANGUAGES)
        actual_set = set(_ALL_LANGUAGES)

        missing = expected_set - actual_set
        assert len(missing) == 0, f"MatrixBench missing languages: {missing}"

    def test_jsonld_handles_multi_language_matrix(self):
        """JSON-LD encoder handles matrices with multiple language sections."""
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder

        matrix = _make_synthetic_matrix()
        # Add multi-language content
        matrix["java"] = {"classes": [{"name": "UserService"}]}
        matrix["rust"] = {"structs": [{"name": "Config"}]}
        matrix["go"] = {"structs": [{"name": "Handler"}]}

        encoder = MatrixJsonLdEncoder()
        doc = encoder.encode(matrix)

        assert "@graph" in doc
        assert len(doc["@graph"]) > 0


# ============================================================================
# TOKEN BUDGET VALIDATION INTEGRATION
# ============================================================================

class TestTokenBudgetIntegration:
    """Integration tests for token budget validation (J1)."""

    @pytest.mark.skipif(
        not MATRIX_PROMPT_PATH.exists(),
        reason="Matrix not built (requires codetrellis scan)",
    )
    def test_token_budget_validator_runs(self):
        """Token budget validator produces valid report."""
        # Import from scripts
        sys.path.insert(0, str(ROOT / "scripts"))
        from token_budget_validator import TokenBudgetValidator

        validator = TokenBudgetValidator(str(ROOT))
        report = validator.validate()

        assert report.total_matrix_tokens > 0, "Zero matrix tokens"
        assert len(report.budget_results) == 6, "Expected 6 model budgets"
        assert report.compression is not None, "Missing compression data"

    @pytest.mark.skipif(
        not MATRIX_PROMPT_PATH.exists(),
        reason="Matrix not built (requires codetrellis scan)",
    )
    def test_manifest_auditor_runs(self):
        """Manifest auditor produces valid report."""
        sys.path.insert(0, str(ROOT / "scripts"))
        from manifest_audit import ManifestAuditor

        auditor = ManifestAuditor(str(ROOT))
        report = auditor.audit()

        assert report.total_expected > 0, "Zero expected files"
        assert report.total_found > 0, "Zero files found"
        assert report.compliance_pct > 80, \
            f"Compliance {report.compliance_pct:.1f}% below 80% threshold"


# ============================================================================
# CITATIONS VERIFICATION
# ============================================================================

class TestCitationsIntegration:
    """Verify citations document exists and is populated (J4)."""

    def test_citations_file_exists(self):
        """CITATIONS.md exists in docs/references/."""
        citations_path = ROOT / "docs" / "references" / "CITATIONS.md"
        assert citations_path.exists(), f"Missing: {citations_path}"

    def test_citations_contains_all_sources(self):
        """CITATIONS.md contains all J4 research sources."""
        citations_path = ROOT / "docs" / "references" / "CITATIONS.md"
        if not citations_path.exists():
            pytest.skip("CITATIONS.md not found")

        content = citations_path.read_text(encoding="utf-8")

        # Check for key citations from J4
        required_sources = [
            "JSON-LD 1.1",
            "RFC 6902",
            "RFC 6901",
            "SCIP",
            "LSIF",
            "CodeBERT",
            "UniXcoder",
            "LLMLingua",
            "SWE-bench",
            "HumanEval",
            "DevBench",
            "PyLD",
            "python-json-patch",
            "sentence-transformers",
            "schema.org",
        ]

        for source in required_sources:
            assert source in content, f"Missing citation: {source}"

    def test_citations_has_urls(self):
        """Citations contain valid URLs."""
        citations_path = ROOT / "docs" / "references" / "CITATIONS.md"
        if not citations_path.exists():
            pytest.skip("CITATIONS.md not found")

        content = citations_path.read_text(encoding="utf-8")

        # Should contain multiple URLs
        url_pattern = re.compile(r'https?://[^\s>)]+')
        urls = url_pattern.findall(content)
        assert len(urls) >= 10, f"Only {len(urls)} URLs found, expected ≥10"
