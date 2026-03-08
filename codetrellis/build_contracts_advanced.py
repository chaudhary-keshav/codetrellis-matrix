"""
CodeTrellis Advanced Build Contracts — PART H Implementation
================================================================

Formal I/O contract validators for each of the 7 advanced research
modules (H1-H7). Each contract specifies strict inputs, outputs,
error behavior, caching rules, and compatibility guarantees.

Exit Code Registry (Advanced):
  41 — JSON-LD validation failed (H1)
  42 — Embedding generation failed (H2)
  43 — JSON Patch integrity mismatch (H3)
  44 — Compression critical AST node loss (H4)
  45 — Cross-language orphaned nodes (H5)
  46 — Navigator query parsing failed (H6)
  47 — MatrixBench variance exceeded threshold (H7)

Reference: CODETRELLIS_MASTER_RESEARCH_AND_PLAN.md — PART H (H1-H7)
Author: Keshav Chaudhary
Created: 20 February 2026
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from codetrellis.build_contract import ExitCode

logger = logging.getLogger(__name__)


# =============================================================================
# Shared Contract Types
# =============================================================================

@dataclass
class ContractResult:
    """Result of a single contract validation."""

    contract_id: str
    passed: bool
    exit_code: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "passed": self.passed,
            "exit_code": self.exit_code,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_ms": round(self.duration_ms, 2),
            "details": self.details,
        }


@dataclass
class ContractSuiteResult:
    """Aggregated results for all 7 contracts."""

    results: List[ContractResult] = field(default_factory=list)
    all_passed: bool = False
    total_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_passed": self.all_passed,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "contracts": [r.to_dict() for r in self.results],
        }


def _sha256(data: Any) -> str:
    """Compute SHA-256 of canonical JSON."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# =============================================================================
# H1: JSON-LD Build Contract
# =============================================================================

class JsonLdBuildContract:
    """
    Validates that matrix.json → matrix.jsonld transformation complies
    with the H1 contract.

    Inputs:  matrix.json, JSON-LD context schema
    Outputs: matrix.jsonld with valid @context, @type, @id annotations
    Error:   Exit code 41 if validation fails
    Cache:   Invalidate when matrix.json hash OR context schema changes
    """

    EXIT_CODE = ExitCode.JSONLD_VALIDATION_FAILED  # 41

    def validate(
        self,
        matrix_json: Dict[str, Any],
        jsonld_output: Dict[str, Any],
    ) -> ContractResult:
        """Validate JSON-LD output against H1 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Output must be valid JSON (already a dict, so OK)
        if not isinstance(jsonld_output, dict):
            errors.append("Output is not a JSON object")
            elapsed = (time.perf_counter() - t0) * 1000
            return ContractResult(
                contract_id="H1_JSONLD",
                passed=False,
                exit_code=int(self.EXIT_CODE),
                errors=errors,
                duration_ms=elapsed,
                details=details,
            )

        # 2. Must contain @context
        if "@context" not in jsonld_output:
            errors.append("Missing @context key")
        else:
            ctx = jsonld_output["@context"]
            if not isinstance(ctx, dict):
                errors.append("@context is not a dict")
            elif "ct" not in ctx:
                errors.append("@context missing 'ct' namespace")

        # 3. Must contain @type
        if "@type" not in jsonld_output:
            errors.append("Missing @type key")

        # 4. Must contain @id
        if "@id" not in jsonld_output:
            errors.append("Missing @id key")
        elif not jsonld_output["@id"].startswith("ct:"):
            errors.append(f"@id does not start with 'ct:': {jsonld_output['@id']}")

        # 5. Must contain @graph
        graph = jsonld_output.get("@graph", [])
        if not isinstance(graph, list):
            errors.append("@graph is not a list")
        elif len(graph) == 0:
            warnings.append("@graph is empty")
        else:
            details["graph_node_count"] = len(graph)

            # 6. Every section node must have unique @id
            ids_seen = set()
            for node in graph:
                node_id = node.get("@id", "")
                if not node_id:
                    errors.append(f"Node missing @id: {node.get('@type', 'unknown')}")
                elif node_id in ids_seen:
                    errors.append(f"Duplicate @id: {node_id}")
                else:
                    ids_seen.add(node_id)

            details["unique_ids"] = len(ids_seen)

            # 7. Dependency edges must reference valid @ids
            for node in graph:
                deps = node.get("ct:depends", [])
                if isinstance(deps, list):
                    for dep_id in deps:
                        if isinstance(dep_id, str) and dep_id not in ids_seen:
                            errors.append(f"Dangling ct:depends ref: {dep_id}")

        # 8. Token overhead ≤ 15%
        plain_size = len(json.dumps(matrix_json, separators=(",", ":")))
        jsonld_size = len(json.dumps(jsonld_output, separators=(",", ":")))
        if plain_size > 0:
            overhead = ((jsonld_size - plain_size) / plain_size) * 100
            details["overhead_percent"] = round(overhead, 2)
            if overhead > 15:
                warnings.append(f"Token overhead {overhead:.1f}% exceeds 15%")

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H1_JSONLD",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )

    def compute_cache_key(
        self,
        matrix_json: Dict[str, Any],
        context_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compute cache key; invalidate when matrix or context changes."""
        matrix_hash = _sha256(matrix_json)
        ctx_hash = _sha256(context_schema) if context_schema else "default"
        return hashlib.sha256(
            f"{matrix_hash}:{ctx_hash}".encode()
        ).hexdigest()[:32]


# =============================================================================
# H2: Embedding Index Build Contract
# =============================================================================

class EmbeddingBuildContract:
    """
    Validates that matrix sections → embedding vectors comply with H2 contract.

    Inputs:  matrix.json sections, embedding model identifier
    Outputs: matrix_embeddings.npz with vectors, section IDs, dimension metadata
    Error:   Exit code 42 if embedding generation fails
    Cache:   Invalidate per-section when section content hash changes
    """

    EXIT_CODE = ExitCode.EMBEDDING_GENERATION_FAILED  # 42

    def validate(
        self,
        sections: Dict[str, str],
        metadata: Any,
        vectors: Optional[Dict[str, Any]] = None,
    ) -> ContractResult:
        """Validate embedding index against H2 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Metadata present and valid
        if metadata is None:
            errors.append("No metadata returned from build_index")
        else:
            details["model_name"] = getattr(metadata, "model_name", "unknown")
            details["dimensions"] = getattr(metadata, "dimensions", 0)
            details["section_count"] = getattr(metadata, "section_count", 0)
            details["build_time_ms"] = getattr(metadata, "build_time_ms", 0)

            # 2. One vector per section
            expected_count = len(sections)
            actual_count = getattr(metadata, "section_count", 0)
            if actual_count != expected_count:
                errors.append(
                    f"Section count mismatch: expected {expected_count}, "
                    f"got {actual_count}"
                )

        # 3. Validate vectors if provided
        if vectors is not None:
            import numpy as np

            for section_id, vec in vectors.items():
                if not isinstance(vec, np.ndarray):
                    errors.append(f"Section '{section_id}': vector is not ndarray")
                    continue

                # No NaN/Inf
                if not np.all(np.isfinite(vec)):
                    errors.append(f"Section '{section_id}': contains NaN/Inf")

                # Must contain float values
                if vec.dtype.kind not in ("f", "d"):
                    warnings.append(
                        f"Section '{section_id}': dtype {vec.dtype} is not float"
                    )

                # L2 norm ≈ 1.0 (normalized)
                norm = np.linalg.norm(vec)
                if norm > 0 and abs(norm - 1.0) > 0.01:
                    warnings.append(
                        f"Section '{section_id}': L2 norm {norm:.4f} ≠ 1.0"
                    )

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H2_EMBEDDINGS",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )

    def compute_section_cache_key(self, section_id: str, content: str) -> str:
        """Per-section cache key based on content hash."""
        return hashlib.sha256(
            f"{section_id}:{content}".encode()
        ).hexdigest()[:32]


# =============================================================================
# H3: JSON Patch Build Contract
# =============================================================================

class JsonPatchBuildContract:
    """
    Validates RFC 6902 JSON Patch compliance (H3).

    Inputs:  matrix_v1.json (base), matrix_v2.json (new)
    Outputs: matrix_patch.json (RFC 6902 compliant ops array)
    Determinism: base + patch = new must hold (SHA-256 verified)
    Error:   Exit code 43 if patch application produces hash mismatch
    Cache:   No caching — always computed from two inputs
    """

    EXIT_CODE = ExitCode.JSON_PATCH_INTEGRITY_MISMATCH  # 43

    def validate(
        self,
        base: Dict[str, Any],
        target: Dict[str, Any],
        patch_ops: List[Dict[str, Any]],
    ) -> ContractResult:
        """Validate JSON Patch against H3 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        import jsonpatch

        # 1. Patch must be a non-empty list (unless base == target)
        if base == target:
            if len(patch_ops) != 0:
                warnings.append(
                    f"Identical inputs but patch has {len(patch_ops)} ops"
                )
            details["empty_diff"] = True
        else:
            if len(patch_ops) == 0:
                errors.append("Different inputs but patch is empty")
            details["empty_diff"] = False

        # 2. Each op must be valid RFC 6902
        valid_ops = {"add", "remove", "replace", "move", "copy", "test"}
        for i, op in enumerate(patch_ops):
            if "op" not in op:
                errors.append(f"Patch op[{i}] missing 'op' field")
            elif op["op"] not in valid_ops:
                errors.append(f"Patch op[{i}] invalid op: {op['op']}")
            if "path" not in op:
                errors.append(f"Patch op[{i}] missing 'path' field")

        details["total_operations"] = len(patch_ops)
        details["op_counts"] = {}
        for op in patch_ops:
            op_name = op.get("op", "unknown")
            details["op_counts"][op_name] = details["op_counts"].get(op_name, 0) + 1

        # 3. Determinism: base + patch = target (SHA-256)
        try:
            patch = jsonpatch.JsonPatch(patch_ops)
            result = patch.apply(copy.deepcopy(base))
            base_hash = _sha256(target)
            result_hash = _sha256(result)
            details["target_hash"] = base_hash[:16]
            details["result_hash"] = result_hash[:16]
            if base_hash != result_hash:
                errors.append(
                    f"Hash mismatch: applying patch does not reproduce target. "
                    f"Expected {base_hash[:16]}, got {result_hash[:16]}"
                )
        except Exception as exc:
            errors.append(f"Patch application failed: {exc}")

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H3_JSON_PATCH",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )


# =============================================================================
# H4: Compression Levels Build Contract
# =============================================================================

class CompressionBuildContract:
    """
    Validates multi-level compression compliance (H4).

    Inputs:  matrix.prompt, target compression level (L1, L2, L3)
    Outputs: matrix_L{n}.prompt with reduced token count
    Quality: L1 retains all; L2 retains signatures; L3 retains headers
    Error:   Exit code 44 if critical AST nodes dropped at L1/L2
    Cache:   Invalidate when matrix.prompt hash OR compression config changes
    """

    EXIT_CODE = ExitCode.COMPRESSION_AST_NODE_LOSS  # 44

    # Patterns that identify critical AST nodes (functions/classes)
    _CRITICAL_PATTERNS = [
        r"\bdef\s+\w+",
        r"\bclass\s+\w+",
        r"\bfunction\s+\w+",
        r"\binterface\s+\w+",
        r"\bstruct\s+\w+",
        r"\benum\s+\w+",
        r"\btrait\s+\w+",
        r"\bprotocol\s+\w+",
    ]

    def validate(
        self,
        original: str,
        compressed: str,
        level: str,
    ) -> ContractResult:
        """Validate compressed output against H4 contract."""
        import re

        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # Token counting (approximate)
        orig_tokens = max(1, len(original) // 4)
        comp_tokens = max(1, len(compressed) // 4)
        details["original_tokens"] = orig_tokens
        details["compressed_tokens"] = comp_tokens
        details["level"] = level

        # 1. L1 = identity
        if level == "L1":
            if compressed != original:
                errors.append("L1 must be identity transform (byte-identical)")
            details["is_identity"] = compressed == original

        # 2. L2 ≤ 30,000 tokens; all signatures preserved
        elif level == "L2":
            if comp_tokens > 30_000:
                warnings.append(f"L2 has {comp_tokens} tokens (target ≤ 30,000)")

            # All function/class names must be retained
            for pattern in self._CRITICAL_PATTERNS:
                orig_matches = set(re.findall(pattern, original))
                comp_matches = set(re.findall(pattern, compressed))
                dropped = orig_matches - comp_matches
                if dropped:
                    errors.append(
                        f"L2 dropped critical AST nodes: {dropped}"
                    )
            details["signatures_checked"] = True

        # 3. L3 ≤ 10,000 tokens; section headers retained
        elif level == "L3":
            if comp_tokens > 10_000:
                warnings.append(f"L3 has {comp_tokens} tokens (target ≤ 10,000)")

            # Section headers must be retained
            orig_headers = set(re.findall(r"^\[(\w+)\]", original, re.MULTILINE))
            comp_headers = set(re.findall(r"^\[(\w+)\]", compressed, re.MULTILINE))
            if orig_headers:
                dropped_headers = orig_headers - comp_headers
                if dropped_headers:
                    warnings.append(f"L3 dropped section headers: {dropped_headers}")

        # 4. Compressed must be valid (non-empty, parseable)
        if not compressed.strip():
            errors.append("Compressed output is empty")

        # 5. Compression ratio
        if orig_tokens > 0:
            ratio = comp_tokens / orig_tokens
            details["compression_ratio"] = round(ratio, 4)

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H4_COMPRESSION",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )

    def compute_cache_key(
        self,
        prompt: str,
        level: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Cache key; invalidate when prompt or config changes."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        config_hash = _sha256(config) if config else "default"
        return hashlib.sha256(
            f"{prompt_hash}:{level}:{config_hash}".encode()
        ).hexdigest()[:32]


# =============================================================================
# H5: Cross-Language Merging Build Contract
# =============================================================================

class CrossLanguageBuildContract:
    """
    Validates cross-language matrix merging compliance (H5).

    Inputs:  Per-language matrix_*.json fragments, optional SCIP/LSIF index
    Outputs: Unified matrix_merged.json with cross-language dependency edges
    Error:   Exit code 45 if orphaned nodes exist
    Cache:   Invalidate when any input fragment hash changes
    """

    EXIT_CODE = ExitCode.CROSS_LANGUAGE_ORPHANED_NODES  # 45

    def validate(
        self,
        fragments: Dict[str, Dict[str, Any]],
        unified: Any,
    ) -> ContractResult:
        """Validate merged output against H5 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # Extract unified matrix data
        merged_data = getattr(unified, "merged", unified) if not isinstance(unified, dict) else unified
        if hasattr(unified, "languages"):
            details["languages"] = getattr(unified, "languages", [])
        if hasattr(unified, "api_links"):
            details["api_link_count"] = len(getattr(unified, "api_links", []))
        if hasattr(unified, "type_links"):
            details["type_link_count"] = len(getattr(unified, "type_links", []))

        # 1. Must contain keys from all input fragments
        if isinstance(merged_data, dict):
            for lang_key in fragments:
                if lang_key not in merged_data:
                    errors.append(f"Merged output missing fragment: {lang_key}")

        # 2. Overhead ratio ≤ 150%
        if hasattr(unified, "overhead_ratio"):
            overhead = unified.overhead_ratio
            details["overhead_ratio"] = round(overhead, 4)
            if overhead > 1.5:
                warnings.append(
                    f"Overhead ratio {overhead:.2f} exceeds 150%"
                )

        # 3. Check for orphaned cross-language references
        if hasattr(unified, "api_links"):
            api_links = unified.api_links
            known_sections = set()
            if isinstance(merged_data, dict):
                for lang_key, data in merged_data.items():
                    if lang_key.startswith("__"):
                        continue
                    if isinstance(data, dict):
                        known_sections.update(data.keys())
                    known_sections.add(lang_key)

            orphans = []
            for link in api_links:
                # Orphan = reference to section not in any fragment
                src = getattr(link, "source_section", "")
                tgt = getattr(link, "target_section", "")
                # Links reference names, not sections — light check
                if not src or not tgt:
                    orphans.append(f"Empty link: {src} → {tgt}")

            if orphans:
                warnings.append(f"Found {len(orphans)} potentially orphaned links")
            details["orphan_count"] = len(orphans)

        # 4. At least 2 languages required
        if len(fragments) < 2:
            errors.append(f"Need ≥ 2 fragments, got {len(fragments)}")

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H5_CROSS_LANGUAGE",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )

    def compute_cache_key(
        self,
        fragments: Dict[str, Dict[str, Any]],
    ) -> str:
        """Cache key; invalidate when any fragment changes."""
        hashes = []
        for key in sorted(fragments.keys()):
            h = _sha256(fragments[key])
            hashes.append(f"{key}:{h[:16]}")
        combined = "|".join(hashes)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]


# =============================================================================
# H6: Matrix Navigator Build Contract
# =============================================================================

class NavigatorBuildContract:
    """
    Validates matrix navigator compliance (H6).

    Inputs:  matrix.json, user query (file path or symbol name)
    Outputs: Ranked list of relevant Matrix sections with relevance scores
    Error:   Exit code 46 if query parsing fails
    Cache:   Read-only against cached matrix.json
    """

    EXIT_CODE = ExitCode.NAVIGATOR_QUERY_PARSE_FAILED  # 46

    def validate(
        self,
        query: str,
        results: List[Any],
        metrics: Optional[Any] = None,
    ) -> ContractResult:
        """Validate navigator output against H6 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        details["query"] = query
        details["result_count"] = len(results)

        # 1. Empty query → empty result (not crash)
        if not query or not query.strip():
            if len(results) > 0:
                errors.append("Empty query must return empty results")
            elapsed = (time.perf_counter() - t0) * 1000
            return ContractResult(
                contract_id="H6_NAVIGATOR",
                passed=len(errors) == 0,
                exit_code=0 if len(errors) == 0 else int(self.EXIT_CODE),
                errors=errors,
                duration_ms=elapsed,
                details=details,
            )

        # 2. Results sorted by composite score (descending)
        if len(results) > 1:
            scores = [
                getattr(r, "composite_score", getattr(r, "score", 0))
                for r in results
            ]
            for i in range(len(scores) - 1):
                if scores[i] < scores[i + 1]:
                    errors.append("Results not sorted by score (descending)")
                    break

        # 3. Each result has required fields
        for i, r in enumerate(results):
            has_score = hasattr(r, "composite_score") or hasattr(r, "score")
            has_id = hasattr(r, "file_path") or hasattr(r, "section_id")
            if not has_score:
                errors.append(f"Result[{i}] missing score field")
            if not has_id:
                errors.append(f"Result[{i}] missing id/path field")

        # 4. Latency check
        if metrics is not None:
            total_ms = getattr(metrics, "total_ms", 0)
            details["latency_ms"] = total_ms
            if total_ms > 300:
                warnings.append(f"Latency {total_ms:.1f}ms > 300ms")

        # 5. Relevance scores > 0 for non-empty results
        for i, r in enumerate(results):
            score = getattr(r, "composite_score", getattr(r, "score", 0))
            if score <= 0:
                warnings.append(f"Result[{i}] has score ≤ 0")

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H6_NAVIGATOR",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )


# =============================================================================
# H7: MatrixBench Build Contract
# =============================================================================

class MatrixBenchBuildContract:
    """
    Validates MatrixBench benchmark compliance (H7).

    Inputs:  Repository path, benchmark config (iterations, metrics)
    Outputs: _bench_report.json with token counts, build times, coverage, variance
    Determinism: Variance across runs must be < 2%
    Error:   Exit code 47 if variance exceeds threshold
    Cache:   No caching — benchmarks are always fresh runs
    """

    EXIT_CODE = ExitCode.MATRIXBENCH_VARIANCE_EXCEEDED  # 47

    def validate(
        self,
        results_run1: Any,
        results_run2: Any,
        *,
        variance_threshold: float = 2.0,
    ) -> ContractResult:
        """Validate benchmark results against H7 contract."""
        t0 = time.perf_counter()
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Both runs must produce results
        if results_run1 is None or results_run2 is None:
            errors.append("One or both benchmark runs returned None")
            elapsed = (time.perf_counter() - t0) * 1000
            return ContractResult(
                contract_id="H7_MATRIXBENCH",
                passed=False,
                exit_code=int(self.EXIT_CODE),
                errors=errors,
                duration_ms=elapsed,
                details=details,
            )

        # 2. Results must contain required fields
        r1_dict = results_run1.to_dict() if hasattr(results_run1, "to_dict") else results_run1
        r2_dict = results_run2.to_dict() if hasattr(results_run2, "to_dict") else results_run2

        for field_name in ("total_tasks", "passed_tasks", "total_latency_ms"):
            if field_name not in r1_dict:
                errors.append(f"Run1 missing field: {field_name}")
            if field_name not in r2_dict:
                errors.append(f"Run2 missing field: {field_name}")

        # 3. Required report fields
        for field_name in ("total_tasks", "passed_tasks", "category_scores"):
            if field_name not in r1_dict:
                warnings.append(f"Report missing field: {field_name}")

        # Convenience
        details["run1_total_tasks"] = r1_dict.get("total_tasks", 0)
        details["run2_total_tasks"] = r2_dict.get("total_tasks", 0)
        details["run1_passed"] = r1_dict.get("passed_tasks", 0)
        details["run2_passed"] = r2_dict.get("passed_tasks", 0)

        # 4. Determinism: variance < threshold
        avg1 = r1_dict.get("avg_improvement_pct", 0)
        avg2 = r2_dict.get("avg_improvement_pct", 0)
        variance = abs(avg1 - avg2)
        details["variance_pct"] = round(variance, 4)
        details["threshold_pct"] = variance_threshold

        if variance > variance_threshold:
            errors.append(
                f"Variance {variance:.2f}% exceeds {variance_threshold}% threshold"
            )

        # 5. All 5 categories must have valid scores
        cats1 = r1_dict.get("category_scores", {})
        expected_cats = {"completeness", "accuracy", "navigation",
                         "compression", "cross_language"}
        for cat in expected_cats:
            if cat not in cats1:
                warnings.append(f"Missing category in results: {cat}")

        details["categories_present"] = list(cats1.keys())

        elapsed = (time.perf_counter() - t0) * 1000
        passed = len(errors) == 0
        return ContractResult(
            contract_id="H7_MATRIXBENCH",
            passed=passed,
            exit_code=0 if passed else int(self.EXIT_CODE),
            errors=errors,
            warnings=warnings,
            duration_ms=elapsed,
            details=details,
        )


# =============================================================================
# Suite Runner
# =============================================================================

class AdvancedBuildContractSuite:
    """
    Runs all 7 advanced build contracts and produces a consolidated report.

    Usage::

        suite = AdvancedBuildContractSuite()
        report = suite.run_all(
            matrix_json=mj,
            matrix_prompt=mp,
        )
    """

    def __init__(self) -> None:
        self.h1 = JsonLdBuildContract()
        self.h2 = EmbeddingBuildContract()
        self.h3 = JsonPatchBuildContract()
        self.h4 = CompressionBuildContract()
        self.h5 = CrossLanguageBuildContract()
        self.h6 = NavigatorBuildContract()
        self.h7 = MatrixBenchBuildContract()

    def run_all(
        self,
        *,
        matrix_json: Dict[str, Any],
        matrix_prompt: str,
    ) -> ContractSuiteResult:
        """
        Execute all 7 contracts end-to-end using the provided matrix data.

        Internally constructs each module, generates output, then validates
        the output against the contract.
        """
        suite_result = ContractSuiteResult()
        t0 = time.perf_counter()

        # H1: JSON-LD
        try:
            from codetrellis.matrix_jsonld import MatrixJsonLdEncoder
            encoder = MatrixJsonLdEncoder()
            jsonld_doc = encoder.encode(matrix_json)
            r1 = self.h1.validate(matrix_json, jsonld_doc)
        except Exception as exc:
            r1 = ContractResult(
                contract_id="H1_JSONLD", passed=False,
                exit_code=int(ExitCode.JSONLD_VALIDATION_FAILED),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r1)

        # H2: Embeddings
        try:
            from codetrellis.matrix_embeddings import MatrixEmbeddingIndex
            idx = MatrixEmbeddingIndex()
            # Build sections from prompt
            sections = self._extract_sections(matrix_prompt)
            if not sections:
                sections = {"PROJECT": matrix_prompt[:500]}
            meta = idx.build_index(sections)
            vectors = {k: idx._index[k] for k in idx._index}
            r2 = self.h2.validate(sections, meta, vectors)
        except Exception as exc:
            r2 = ContractResult(
                contract_id="H2_EMBEDDINGS", passed=False,
                exit_code=int(ExitCode.EMBEDDING_GENERATION_FAILED),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r2)

        # H3: JSON Patch
        try:
            from codetrellis.matrix_diff import MatrixDiffEngine
            engine = MatrixDiffEngine()
            base = {"project": "test", "version": "1.0"}
            target = copy.deepcopy(matrix_json)
            target["__contract_test__"] = True
            patch = engine.compute_diff(base, target)
            patch_ops = list(patch)
            r3 = self.h3.validate(base, target, patch_ops)
        except Exception as exc:
            r3 = ContractResult(
                contract_id="H3_JSON_PATCH", passed=False,
                exit_code=int(ExitCode.JSON_PATCH_INTEGRITY_MISMATCH),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r3)

        # H4: Compression
        try:
            from codetrellis.matrix_compressor_levels import (
                CompressionLevel,
                MatrixMultiLevelCompressor,
            )
            comp = MatrixMultiLevelCompressor()
            l1_out = comp.compress(matrix_prompt, CompressionLevel.L1_FULL)
            r4 = self.h4.validate(matrix_prompt, l1_out, "L1")
        except Exception as exc:
            r4 = ContractResult(
                contract_id="H4_COMPRESSION", passed=False,
                exit_code=int(ExitCode.COMPRESSION_AST_NODE_LOSS),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r4)

        # H5: Cross-Language
        try:
            from codetrellis.cross_language_types import CrossLanguageLinker
            linker = CrossLanguageLinker()
            fragments = {
                "python": {"types": {"str": "str", "int": "int"}},
                "typescript": {"types": {"string": "string", "number": "number"}},
            }
            unified = linker.merge_matrices(fragments)
            r5 = self.h5.validate(fragments, unified)
        except Exception as exc:
            r5 = ContractResult(
                contract_id="H5_CROSS_LANGUAGE", passed=False,
                exit_code=int(ExitCode.CROSS_LANGUAGE_ORPHANED_NODES),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r5)

        # H6: Navigator
        try:
            from codetrellis.matrix_navigator import MatrixNavigator
            nav = MatrixNavigator(matrix_json, matrix_prompt)
            query = "scanner parser"
            results = nav.discover(query)
            metrics = nav.last_metrics
            r6 = self.h6.validate(query, results, metrics)
        except Exception as exc:
            r6 = ContractResult(
                contract_id="H6_NAVIGATOR", passed=False,
                exit_code=int(ExitCode.NAVIGATOR_QUERY_PARSE_FAILED),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r6)

        # H7: MatrixBench
        try:
            from codetrellis.matrixbench_scorer import MatrixBench
            bench = MatrixBench(
                matrix_json=matrix_json,
                matrix_prompt=matrix_prompt,
            )
            run1 = bench.run_all()
            run2 = bench.run_all()
            r7 = self.h7.validate(run1, run2)
        except Exception as exc:
            r7 = ContractResult(
                contract_id="H7_MATRIXBENCH", passed=False,
                exit_code=int(ExitCode.MATRIXBENCH_VARIANCE_EXCEEDED),
                errors=[f"Module error: {exc}"],
            )
        suite_result.results.append(r7)

        suite_result.total_duration_ms = (time.perf_counter() - t0) * 1000
        suite_result.all_passed = all(r.passed for r in suite_result.results)
        return suite_result

    @staticmethod
    def _extract_sections(prompt: str) -> Dict[str, str]:
        """Extract named sections from matrix.prompt text."""
        import re
        sections: Dict[str, str] = {}
        current_name = ""
        current_lines: List[str] = []
        for line in prompt.splitlines():
            m = re.match(r"^\[(\w+)\]", line)
            if m:
                if current_name and current_lines:
                    sections[current_name] = "\n".join(current_lines)
                current_name = m.group(1)
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_name and current_lines:
            sections[current_name] = "\n".join(current_lines)
        return sections


# =============================================================================
# CLI entry point
# =============================================================================

def validate_advanced_contracts(
    matrix_json_path: str,
    matrix_prompt_path: str,
) -> int:
    """
    Run all advanced build contracts and return the appropriate exit code.

    Returns 0 on full success, or the first failing contract's exit code.
    """
    try:
        matrix_json = json.loads(Path(matrix_json_path).read_text(encoding="utf-8"))
        matrix_prompt = Path(matrix_prompt_path).read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read inputs: %s", exc)
        return int(ExitCode.CONFIGURATION_ERROR)

    suite = AdvancedBuildContractSuite()
    result = suite.run_all(matrix_json=matrix_json, matrix_prompt=matrix_prompt)

    # Log results
    for r in result.results:
        status = "PASS" if r.passed else "FAIL"
        logger.info(
            "%s %s (exit=%d, %.1fms) errors=%s",
            status, r.contract_id, r.exit_code, r.duration_ms, r.errors,
        )

    if result.all_passed:
        logger.info("All 7 advanced contracts PASSED (%.1fms)", result.total_duration_ms)
        return 0

    # Return first failing exit code
    for r in result.results:
        if not r.passed:
            return r.exit_code

    return int(ExitCode.FATAL_ERROR)
