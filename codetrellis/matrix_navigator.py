"""
F6 — Matrix-Guided File Discovery & Directed Retrieval.

Production three-phase navigator that discovers relevant files using:
1. **Keyword matching** against the matrix prompt (fast, ≤ 100 ms)
2. **Graph traversal** of the dependency DAG in matrix JSON
3. **Embedding similarity** (optional, via F2 EmbeddingIndex)

Composite score = 0.5 × keyword + 0.3 × graph + 0.2 × embedding.

Quality Gate G6 targets
-----------------------
- Keyword accuracy ≥ 90 %
- P@5 ≥ 85 %
- ≤ 100 ms without embeddings, ≤ 300 ms with
- Framework-aware queries
- Empty / malformed query → graceful empty result
- max_depth respected in graph traversal
- Reverse dependency tracking
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileRelevance:
    """A single file discovery result."""

    file_path: str
    composite_score: float
    keyword_score: float = 0.0
    graph_score: float = 0.0
    embedding_score: float = 0.0
    reached_via: str = "keyword"  # "keyword", "dependency", "embedding"


@dataclass(frozen=True)
class RetrievalResult:
    """A section-level retrieval result."""

    section_id: str
    score: float
    snippet: str = ""


@dataclass
class DiscoveryMetrics:
    """Timing and quality metrics for a single discover() call."""

    total_ms: float = 0.0
    keyword_ms: float = 0.0
    graph_ms: float = 0.0
    embedding_ms: float = 0.0
    files_evaluated: int = 0
    files_returned: int = 0


# ---------------------------------------------------------------------------
# Keyword index (Phase 1)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Framework-aware keyword expansions
_FRAMEWORK_KEYWORDS: Dict[str, List[str]] = {
    "react": ["component", "jsx", "tsx", "hook", "useState", "useEffect", "props"],
    "vue": ["component", "vue", "composition", "setup", "ref", "computed", "pinia"],
    "angular": ["component", "service", "module", "directive", "pipe", "injectable"],
    "svelte": ["component", "svelte", "store", "writable", "readable"],
    "nextjs": ["page", "layout", "getServerSideProps", "getStaticProps", "app"],
    "fastapi": ["router", "endpoint", "pydantic", "depends", "fastapi"],
    "django": ["view", "model", "serializer", "urlpatterns", "admin"],
    "flask": ["route", "blueprint", "app", "request", "response"],
    "express": ["router", "middleware", "app", "req", "res"],
    "nestjs": ["controller", "service", "module", "guard", "interceptor"],
    "redux": ["reducer", "action", "store", "dispatch", "selector", "slice"],
    "tailwind": ["className", "tailwind", "tw", "utility", "responsive"],
}


def _tokenise(text: str) -> List[str]:
    """Split text into lowercase identifier tokens."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _expand_query(tokens: List[str]) -> List[str]:
    """Add framework-specific expansions."""
    extra: List[str] = []
    for tok in tokens:
        if tok in _FRAMEWORK_KEYWORDS:
            extra.extend(_FRAMEWORK_KEYWORDS[tok])
    return list(dict.fromkeys(tokens + extra))  # dedup, preserve order


# ---------------------------------------------------------------------------
# Navigator
# ---------------------------------------------------------------------------

class MatrixNavigator:
    """
    Three-phase file discovery engine.

    Parameters
    ----------
    matrix_json : dict
        The parsed ``matrix.json`` dictionary.
    matrix_prompt : str
        The full ``matrix.prompt`` text.
    embedding_index : object, optional
        An ``EmbeddingIndex`` instance (F2) with a ``query()`` method.
    """

    def __init__(
        self,
        matrix_json: Dict[str, Any],
        matrix_prompt: str,
        embedding_index: Optional[Any] = None,
    ) -> None:
        self._json = matrix_json
        self._prompt = matrix_prompt
        self._embedding_index = embedding_index

        # Pre-compute keyword index and dependency graph
        self._file_tokens: Dict[str, Set[str]] = {}
        self._dep_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self._build_indices()

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def _build_indices(self) -> None:
        """Build the keyword index and dependency graph from matrix_json."""
        for section_key, section_data in self._json.items():
            if not isinstance(section_data, dict):
                continue
            # Collect all string content as keywords
            text = self._flatten_to_text(section_data)
            self._file_tokens[section_key] = set(_tokenise(text))

            # Extract dependencies
            deps = self._extract_deps(section_data)
            self._dep_graph[section_key] = deps
            for dep in deps:
                self._reverse_deps[dep].add(section_key)

        # Also index sections from the prompt text
        self._prompt_sections = self._split_prompt_sections(self._prompt)

    @staticmethod
    def _flatten_to_text(data: Any, _depth: int = 0) -> str:
        """Recursively flatten a dict/list to a text blob for keyword indexing."""
        if _depth > 8:
            return ""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            parts = []
            for k, v in data.items():
                parts.append(str(k))
                parts.append(MatrixNavigator._flatten_to_text(v, _depth + 1))
            return " ".join(parts)
        if isinstance(data, (list, tuple)):
            return " ".join(
                MatrixNavigator._flatten_to_text(item, _depth + 1)
                for item in data
            )
        return str(data) if data is not None else ""

    @staticmethod
    def _extract_deps(section: Dict[str, Any]) -> Set[str]:
        """Extract dependency references from a section dict."""
        deps: Set[str] = set()
        for key in ("imports", "dependencies", "requires", "uses"):
            val = section.get(key)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        deps.add(item)
                    elif isinstance(item, dict) and "module" in item:
                        deps.add(item["module"])
            elif isinstance(val, dict):
                deps.update(val.keys())
        return deps

    @staticmethod
    def _split_prompt_sections(prompt: str) -> Dict[str, str]:
        """Split the prompt into named sections by markdown headers."""
        sections: Dict[str, str] = {}
        current_name = "__preamble__"
        current_lines: List[str] = []
        for line in prompt.splitlines():
            m = re.match(r"^#{1,4}\s+(.+)$", line)
            if m:
                if current_lines:
                    sections[current_name] = "\n".join(current_lines)
                current_name = m.group(1).strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            sections[current_name] = "\n".join(current_lines)
        return sections

    # ------------------------------------------------------------------
    # Phase 1: Keyword matching
    # ------------------------------------------------------------------

    def _keyword_scores(self, query_tokens: List[str]) -> Dict[str, float]:
        """Return normalised keyword overlap scores per section."""
        if not query_tokens:
            return {}
        qt = set(query_tokens)
        scores: Dict[str, float] = {}
        for section, tokens in self._file_tokens.items():
            overlap = len(qt & tokens)
            if overlap > 0:
                scores[section] = overlap / len(qt)

        # Also search prompt sections
        for name, body in self._prompt_sections.items():
            body_tokens = set(_tokenise(body))
            overlap = len(qt & body_tokens)
            if overlap > 0:
                key = name
                existing = scores.get(key, 0.0)
                scores[key] = max(existing, overlap / len(qt))

        return scores

    # ------------------------------------------------------------------
    # Phase 2: Graph traversal
    # ------------------------------------------------------------------

    def _graph_scores(
        self,
        seed_files: Set[str],
        max_depth: int = 2,
    ) -> Dict[str, float]:
        """BFS from *seed_files*, decaying score by depth."""
        scores: Dict[str, float] = {}
        visited: Set[str] = set()
        frontier = list(seed_files)
        depth = 0
        while frontier and depth <= max_depth:
            score = 1.0 / (1 + depth)
            next_frontier: List[str] = []
            for f in frontier:
                if f in visited:
                    continue
                visited.add(f)
                scores[f] = max(scores.get(f, 0.0), score)
                for dep in self._dep_graph.get(f, set()):
                    if dep not in visited:
                        next_frontier.append(dep)
                for rev in self._reverse_deps.get(f, set()):
                    if rev not in visited:
                        next_frontier.append(rev)
            frontier = next_frontier
            depth += 1
        return scores

    # ------------------------------------------------------------------
    # Phase 3: Embedding similarity
    # ------------------------------------------------------------------

    def _embedding_scores(self, query: str) -> Dict[str, float]:
        """Use the optional EmbeddingIndex for semantic similarity."""
        if self._embedding_index is None:
            return {}
        try:
            results = self._embedding_index.query(query, top_k=20)
            return {r.section_id: r.score for r in results}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(
        self,
        query: str,
        *,
        max_files: int = 10,
        depth: int = 2,
        keyword_weight: float = 0.5,
        graph_weight: float = 0.3,
        embedding_weight: float = 0.2,
    ) -> List[FileRelevance]:
        """
        Discover relevant files for *query*.

        Parameters
        ----------
        query : str
            Natural-language or keyword query.
        max_files : int
            Maximum results to return.
        depth : int
            Max dependency graph traversal depth.

        Returns
        -------
        list[FileRelevance]
            Sorted by composite score (descending).
        """
        if not query or not query.strip():
            return []

        metrics = DiscoveryMetrics()
        t0 = time.perf_counter()

        # Phase 1 — keywords
        t1 = time.perf_counter()
        tokens = _expand_query(_tokenise(query))
        kw_scores = self._keyword_scores(tokens)
        metrics.keyword_ms = (time.perf_counter() - t1) * 1000

        # Phase 2 — graph
        t2 = time.perf_counter()
        seed = {k for k, v in sorted(kw_scores.items(), key=lambda x: -x[1])[:5]}
        gr_scores = self._graph_scores(seed, max_depth=depth) if seed else {}
        metrics.graph_ms = (time.perf_counter() - t2) * 1000

        # Phase 3 — embeddings
        t3 = time.perf_counter()
        em_scores = self._embedding_scores(query)
        metrics.embedding_ms = (time.perf_counter() - t3) * 1000

        # Merge
        all_files = set(kw_scores) | set(gr_scores) | set(em_scores)
        metrics.files_evaluated = len(all_files)

        results: List[FileRelevance] = []
        for fp in all_files:
            kw = kw_scores.get(fp, 0.0)
            gr = gr_scores.get(fp, 0.0)
            em = em_scores.get(fp, 0.0)
            composite = (
                keyword_weight * kw
                + graph_weight * gr
                + embedding_weight * em
            )
            # Determine primary source
            if em > kw and em > gr:
                via = "embedding"
            elif gr > kw:
                via = "dependency"
            else:
                via = "keyword"

            results.append(FileRelevance(
                file_path=fp,
                composite_score=round(composite, 6),
                keyword_score=round(kw, 6),
                graph_score=round(gr, 6),
                embedding_score=round(em, 6),
                reached_via=via,
            ))

        results.sort(key=lambda r: -r.composite_score)
        results = results[:max_files]
        metrics.files_returned = len(results)
        metrics.total_ms = (time.perf_counter() - t0) * 1000
        self._last_metrics = metrics
        return results

    # ------------------------------------------------------------------
    # Dependency queries
    # ------------------------------------------------------------------

    def get_dependencies(self, file_path: str) -> Set[str]:
        """Return direct dependencies of *file_path*."""
        return set(self._dep_graph.get(file_path, set()))

    def get_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Return files that depend on *file_path*."""
        return set(self._reverse_deps.get(file_path, set()))

    def get_dependency_chain(
        self,
        file_path: str,
        *,
        max_depth: int = 5,
    ) -> Dict[str, int]:
        """
        Return transitive dependencies with depth.

        Returns ``{dep_path: depth}`` for all reachable nodes.
        """
        chain: Dict[str, int] = {}
        frontier = [file_path]
        depth = 0
        visited: Set[str] = set()
        while frontier and depth <= max_depth:
            next_frontier: List[str] = []
            for f in frontier:
                if f in visited:
                    continue
                visited.add(f)
                if f != file_path:
                    chain[f] = depth
                for dep in self._dep_graph.get(f, set()):
                    if dep not in visited:
                        next_frontier.append(dep)
            frontier = next_frontier
            depth += 1
        return chain

    # ------------------------------------------------------------------
    # Section retrieval
    # ------------------------------------------------------------------

    def retrieve_sections(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        Retrieve the most relevant prompt sections for *query*.

        Uses keyword matching against ``self._prompt_sections``.
        """
        if not query or not query.strip():
            return []
        qt = set(_tokenise(query))
        scored: List[Tuple[str, float, str]] = []
        for name, body in self._prompt_sections.items():
            body_tokens = set(_tokenise(body))
            overlap = len(qt & body_tokens)
            if overlap > 0:
                score = overlap / len(qt)
                snippet = body[:300]
                scored.append((name, score, snippet))
        scored.sort(key=lambda x: -x[1])
        return [
            RetrievalResult(section_id=name, score=round(s, 6), snippet=snip)
            for name, s, snip in scored[:top_k]
        ]

    # ------------------------------------------------------------------
    # Metrics access
    # ------------------------------------------------------------------

    @property
    def last_metrics(self) -> Optional[DiscoveryMetrics]:
        return getattr(self, "_last_metrics", None)

    # ------------------------------------------------------------------
    # Quality gate self-check
    # ------------------------------------------------------------------

    def validate_gate_g6(self, queries: List[str]) -> Tuple[bool, List[str]]:
        """
        Run G6 quality gate checks against *queries*.

        Returns (passed, errors).
        """
        errors: List[str] = []

        for q in queries:
            results = self.discover(q)
            m = self.last_metrics
            if m is None:
                errors.append(f"NO_METRICS for query: {q}")
                continue

            # Latency
            if self._embedding_index is None:
                if m.total_ms > 100:
                    errors.append(
                        f"SLOW_NO_EMB: {m.total_ms:.1f}ms > 100ms for '{q}'"
                    )
            else:
                if m.total_ms > 300:
                    errors.append(
                        f"SLOW_WITH_EMB: {m.total_ms:.1f}ms > 300ms for '{q}'"
                    )

        # Empty query safety
        empty_results = self.discover("")
        if empty_results:
            errors.append("EMPTY_QUERY returned results")
        none_results = self.discover("   ")
        if none_results:
            errors.append("WHITESPACE_QUERY returned results")

        return (len(errors) == 0, errors)
