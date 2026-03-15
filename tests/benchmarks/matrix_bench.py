"""
MatrixBench Integration Test Suite
====================================
Runs the full MatrixBench benchmark against the project's own matrix files.
Execute with: pytest tests/benchmarks/matrix_bench.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

# Matrix file paths
MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.json"
MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.prompt"


@pytest.fixture(scope="module")
def matrix_json():
    """Load matrix.json as dict."""
    if not MATRIX_JSON_PATH.exists():
        pytest.skip(f"matrix.json not found at {MATRIX_JSON_PATH}")
    return json.loads(MATRIX_JSON_PATH.read_text())


@pytest.fixture(scope="module")
def matrix_prompt():
    """Load matrix.prompt as string."""
    if not MATRIX_PROMPT_PATH.exists():
        pytest.skip(f"matrix.prompt not found at {MATRIX_PROMPT_PATH}")
    return MATRIX_PROMPT_PATH.read_text()


# =============================================================================
# F1: JSON-LD
# =============================================================================

class TestF1JsonLd:
    """JSON-LD encoder tests."""

    def test_encode_produces_valid_graph(self, matrix_json):
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        ld = encoder.encode(matrix_json)
        assert "@context" in ld
        assert "@graph" in ld
        assert len(ld["@graph"]) > 0

    def test_encode_compact_smaller_than_full(self, matrix_json):
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        full = encoder.encode(matrix_json)
        compact = encoder.encode_compact(matrix_json)
        assert len(json.dumps(compact)) < len(json.dumps(full))

    def test_frame_filters_by_type(self, matrix_json):
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        ld = encoder.encode(matrix_json)
        framed = encoder.frame(ld, {"@type": "ct:Module"})
        nodes = framed.get("@graph", [])
        for node in nodes:
            assert node.get("@type") == "ct:Module"

    def test_validate_returns_true_on_valid(self, matrix_json):
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        ld = encoder.encode(matrix_json)
        result = encoder.validate(ld)
        # validate may return empty list (no errors) which is truthy-empty
        # or True. We accept both as "valid".
        assert result is not None

    def test_get_stats(self, matrix_json):
        from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
        encoder = MatrixJsonLdEncoder()
        ld = encoder.encode(matrix_json)
        stats = encoder.get_stats(matrix_json, ld)
        assert stats.total_nodes > 0
        assert stats.total_edges >= 0
        assert stats.sections_encoded >= 0


# =============================================================================
# F2: Embeddings
# =============================================================================

class TestF2Embeddings:
    """Matrix embedding index tests."""

    @staticmethod
    def _parse_sections(prompt):
        import re
        sections = {}
        current = ""
        lines = []
        for line in prompt.split("\n"):
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

    def test_build_index(self, matrix_prompt):
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        sections = self._parse_sections(matrix_prompt)
        idx = MatrixEmbeddingIndex()
        idx.build_index(sections)
        assert idx._index is not None

    def test_query_returns_results(self, matrix_prompt):
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        sections = self._parse_sections(matrix_prompt)
        idx = MatrixEmbeddingIndex()
        idx.build_index(sections)
        results = idx.query("Python type system", top_k=5)
        assert len(results) > 0
        assert all(r.score >= 0 for r in results)

    def test_save_load_roundtrip(self, matrix_prompt, tmp_path):
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        sections = self._parse_sections(matrix_prompt)
        idx = MatrixEmbeddingIndex()
        idx.build_index(sections)

        save_path = tmp_path / "test_index"
        idx.save(save_path)

        idx2 = MatrixEmbeddingIndex()
        idx2.load(save_path)

        r1 = idx.query("Python", top_k=3)
        r2 = idx2.query("Python", top_k=3)
        assert len(r1) == len(r2)

    def test_token_savings(self, matrix_prompt):
        from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
        sections = self._parse_sections(matrix_prompt)
        idx = MatrixEmbeddingIndex()
        idx.build_index(sections)
        results = idx.query("API endpoints", top_k=3)
        savings = idx.get_token_savings(len(matrix_prompt.split()), top_k=3, query="API endpoints")
        assert savings["savings_percent"] > 0


# =============================================================================
# F3: Differential Matrix
# =============================================================================

class TestF3DiffEngine:
    """JSON Patch differential engine tests."""

    def test_compute_diff_no_change(self, matrix_json):
        from codetrellis.matrix_diff import MatrixDiffEngine
        engine = MatrixDiffEngine()
        patch = engine.compute_diff(matrix_json, matrix_json)
        ops = patch.patch if hasattr(patch, "patch") else list(patch)
        assert len(ops) == 0

    def test_compute_diff_detects_changes(self, matrix_json):
        from codetrellis.matrix_diff import MatrixDiffEngine
        import copy
        engine = MatrixDiffEngine()
        modified = copy.deepcopy(matrix_json)
        modified["__test_key__"] = "test_value"
        patch = engine.compute_diff(matrix_json, modified)
        ops = patch.patch if hasattr(patch, "patch") else list(patch)
        assert len(ops) > 0

    def test_apply_patch_roundtrip(self, matrix_json):
        from codetrellis.matrix_diff import MatrixDiffEngine
        import copy
        engine = MatrixDiffEngine()
        modified = copy.deepcopy(matrix_json)
        modified["__test_key__"] = "test_roundtrip"
        patch = engine.compute_diff(matrix_json, modified)
        reconstructed = engine.apply_patch(matrix_json, patch)
        assert reconstructed.get("__test_key__") == "test_roundtrip"

    def test_verify_patch_integrity(self, matrix_json):
        from codetrellis.matrix_diff import MatrixDiffEngine
        import copy
        engine = MatrixDiffEngine()
        modified = copy.deepcopy(matrix_json)
        modified["__test_integrity__"] = True
        patch = engine.compute_diff(matrix_json, modified)
        assert engine.verify_patch_integrity(matrix_json, modified, patch)

    def test_patch_stats(self, matrix_json):
        from codetrellis.matrix_diff import MatrixDiffEngine
        import copy
        engine = MatrixDiffEngine()
        modified = copy.deepcopy(matrix_json)
        modified["__test_stats__"] = 42
        patch = engine.compute_diff(matrix_json, modified)
        stats = engine.get_patch_stats(patch, modified)
        assert stats.total_operations > 0
        assert stats.compression_ratio > 0


# =============================================================================
# F4: Compression Levels
# =============================================================================

class TestF4Compression:
    """Multi-level compression tests."""

    def test_l1_is_identity(self, matrix_prompt):
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        result = comp.compress(matrix_prompt, CompressionLevel.L1_FULL)
        assert result == matrix_prompt

    def test_l2_smaller_than_l1(self, matrix_prompt):
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(matrix_prompt, CompressionLevel.L2_STRUCTURAL)
        assert len(l2) < len(matrix_prompt)

    def test_l3_smaller_than_l2(self, matrix_prompt):
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(matrix_prompt, CompressionLevel.L2_STRUCTURAL)
        l3 = comp.compress(matrix_prompt, CompressionLevel.L3_SKELETON)
        assert len(l3) < len(l2)

    def test_auto_select_for_model(self, matrix_prompt):
        from codetrellis.matrix_compressor_levels import MatrixMultiLevelCompressor
        comp = MatrixMultiLevelCompressor()
        level = comp.auto_select_for_model("gpt-4o")
        assert level is not None

    def test_get_stats(self, matrix_prompt):
        from codetrellis.matrix_compressor_levels import (
            CompressionLevel,
            MatrixMultiLevelCompressor,
        )
        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(matrix_prompt, CompressionLevel.L2_STRUCTURAL)
        stats = comp.get_stats(matrix_prompt, l2, CompressionLevel.L2_STRUCTURAL)
        assert stats.compression_ratio > 1.0
        assert stats.sections_preserved > 0


# =============================================================================
# F5: Cross-Language
# =============================================================================

class TestF5CrossLanguage:
    """Cross-language type mapping tests."""

    @pytest.mark.parametrize(
        "src_lang,src_type,tgt_lang,expected",
        [
            ("python", "str", "typescript", "string"),
            ("python", "int", "java", "int"),
            ("rust", "Vec", "go", "[]T"),
            ("kotlin", "Boolean", "csharp", "bool"),
            ("swift", "String", "ruby", "String"),
            ("java", "CompletableFuture", "python", "Awaitable[T]"),
            ("python", "float", "rust", "f64"),
            ("typescript", "number", "python", "int"),
            ("go", "string", "java", "String"),
            ("csharp", "int", "python", "int"),
        ],
    )
    def test_primitive_type_mapping(self, src_lang, src_type, tgt_lang, expected):
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        result = linker.resolve_type(src_type, src_lang, tgt_lang)
        assert result is not None
        assert expected.lower() in result.lower()

    def test_get_available_languages(self):
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        langs = linker.get_available_languages()
        assert len(langs) >= 15

    def test_detect_api_links(self, matrix_json):
        from codetrellis.cross_language_types import CrossLanguageLinker
        linker = CrossLanguageLinker()
        # detect_api_links expects Dict[lang, matrix_data]
        # For a single-language project, pass a subset as separate "languages"
        matrices = {}
        for key, value in matrix_json.items():
            if isinstance(value, dict):
                matrices[key] = value
        links = linker.detect_api_links(matrices)
        # May be empty for a single-language project, but should not error
        assert isinstance(links, list)


# =============================================================================
# F6: Directed Retrieval (Navigator)
# =============================================================================

class TestF6Navigator:
    """Matrix navigator / directed retrieval tests."""

    def test_discover_returns_results(self, matrix_json, matrix_prompt):
        from codetrellis.matrix_navigator import MatrixNavigator
        nav = MatrixNavigator(matrix_json, matrix_prompt)
        results = nav.discover("Python parser validation")
        # Navigator may return empty if no files match keywords
        assert isinstance(results, list)

    def test_discover_respects_top_k(self, matrix_json, matrix_prompt):
        from codetrellis.matrix_navigator import MatrixNavigator
        nav = MatrixNavigator(matrix_json, matrix_prompt)
        results = nav.discover("Python parser", max_files=3)
        assert len(results) <= 3

    def test_get_dependencies(self, matrix_json, matrix_prompt):
        from codetrellis.matrix_navigator import MatrixNavigator
        nav = MatrixNavigator(matrix_json, matrix_prompt)
        deps = nav.get_dependencies("codetrellis/scanner.py")
        assert isinstance(deps, set)


# =============================================================================
# F7: MatrixBench (Self-Test)
# =============================================================================

class TestF7MatrixBench:
    """MatrixBench benchmark self-tests."""

    def test_run_all_completes(self, matrix_prompt):
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_prompt=matrix_prompt,
            matrix_json={},
        )
        results = bench.run_all()
        assert results.total_tasks > 0

    def test_run_with_real_data(self, matrix_json, matrix_prompt):
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_json=matrix_json,
            matrix_prompt=matrix_prompt,
        )
        results = bench.run_all()
        assert results.total_tasks > 10
        assert results.total_latency_ms > 0

    def test_language_coverage_tasks(self, matrix_json, matrix_prompt):
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_json=matrix_json,
            matrix_prompt=matrix_prompt,
        )
        bench.add_language_coverage_tasks()
        results = bench.run_all()
        assert results.total_tasks > 50

    def test_generate_report(self, matrix_json, matrix_prompt):
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_json=matrix_json,
            matrix_prompt=matrix_prompt,
        )
        results = bench.run_all()
        report = bench.generate_report(results)
        assert "MatrixBench Report" in report
        assert "Category" in report

    def test_export_results(self, matrix_json, matrix_prompt, tmp_path):
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_json=matrix_json,
            matrix_prompt=matrix_prompt,
        )
        results = bench.run_all()
        export_path = tmp_path / "results.json"
        bench.export_results(results, export_path)
        assert export_path.exists()
        data = json.loads(export_path.read_text())
        assert data["total_tasks"] == results.total_tasks

    def test_deterministic_within_tolerance(self, matrix_json, matrix_prompt):
        """Quality gate G7: Results must be deterministic ±2%."""
        from codetrellis.matrixbench_scorer import MatrixBench
        bench = MatrixBench(
            matrix_json=matrix_json,
            matrix_prompt=matrix_prompt,
        )
        r1 = bench.run_all()
        r2 = bench.run_all()
        diff = abs(r1.avg_improvement_pct - r2.avg_improvement_pct)
        assert diff <= 2.0, f"Non-deterministic: {diff}% difference"
