"""
F4 — Matrix Compression Levels (L1 / L2 / L3).

Production multi-level compressor for CodeTrellis matrix prompts.
Uses *tiktoken* (cl100k_base) for accurate token counting.

Level descriptions
------------------
* **L1 FULL**       — Identity transform, complete matrix.
* **L2 STRUCTURAL** — Signatures + hierarchies + dependency graph.
                      Target ≤ 30 000 tokens.
* **L3 SKELETON**   — Module names + public function signatures only.
                      Target ≤ 10 000 tokens.

Quality Gate G4 targets
-----------------------
- L1 == identity
- L2 ≤ 30K tokens; preserves ALL function/class signatures (zero loss)
- L3 ≤ 10K tokens; preserves all public function names + module names
- auto_select_level() picks L1/L2/L3 by context-window size
- --model flag selects correct level for known models
- --token-budget N → output ≤ N tokens
- Compressed output is valid parseable matrix format
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Token counter — mirrors codetrellis.bpl.selector.count_tokens()
# ---------------------------------------------------------------------------

try:
    import tiktoken as _tiktoken

    _ENC = _tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        """Count tokens using tiktoken cl100k_base."""
        return len(_ENC.encode(text))
except Exception:  # pragma: no cover — fallback if tiktoken unavailable
    def count_tokens(text: str) -> int:  # type: ignore[misc]
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Enums & data classes
# ---------------------------------------------------------------------------

class CompressionLevel(enum.Enum):
    L1_FULL = "L1"
    L2_STRUCTURAL = "L2"
    L3_SKELETON = "L3"


@dataclass(frozen=True)
class CompressionResult:
    """Statistics returned by ``get_stats``."""

    compression_ratio: float
    original_tokens: int
    compressed_tokens: int
    sections_preserved: int
    sections_removed: int
    signatures_preserved: int
    level: CompressionLevel


# ---------------------------------------------------------------------------
# Model → context-window map
# ---------------------------------------------------------------------------

_MODEL_CONTEXT_WINDOWS: Dict[str, int] = {
    # ≥ 200K → L1
    "gemini-2": 200_000,
    "gemini-2.5-pro": 1_000_000,
    "gemini-1.5-pro": 1_000_000,
    "gemini-pro": 200_000,
    "claude-3-opus": 200_000,
    "claude-3.5-sonnet": 200_000,
    "claude-3.7-sonnet": 200_000,
    "claude-4-sonnet": 200_000,
    # 128K → L2
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "claude-3-sonnet": 128_000,
    "claude-3-haiku": 128_000,
    "deepseek-coder": 128_000,
    "codestral": 128_000,
    # ≤ 32K → L3
    "gpt-4": 32_000,
    "gpt-3.5-turbo": 16_000,
    "mistral-7b": 32_000,
    "codellama-34b": 16_000,
    "llama-3-8b": 8_000,
}


# ---------------------------------------------------------------------------
# Section-level helpers
# ---------------------------------------------------------------------------

_SECTION_HEADER_RE = re.compile(
    r"^(#{1,4})\s+(.+)$", re.MULTILINE
)

# Patterns that indicate a function / method / class signature line
_SIGNATURE_RE = re.compile(
    r"^\s*(?:"
    r"(?:def|class|async\s+def)\s+\w+"           # Python
    r"|(?:function|const|let|var|export)\s+\w+"   # JS/TS
    r"|(?:fun|suspend\s+fun)\s+\w+"               # Kotlin
    r"|(?:func)\s+\w+"                            # Go / Swift
    r"|(?:pub\s+)?fn\s+\w+"                       # Rust
    r"|(?:public|private|protected|internal|static|abstract|override|virtual|async)\s+" # Java/C#/TS modifiers
    r"|(?:impl)\s+"                                # Rust impl
    r"|(?:interface|trait|protocol|struct|enum)\s+\w+"
    r")",
    re.MULTILINE,
)

_PUBLIC_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:pub\s+)?(?:public\s+)?(?:static\s+)?(?:async\s+)?"
    r"(?:def|function|fn|fun|func)\s+(\w+)",
    re.MULTILINE,
)

_MODULE_HEADER_RE = re.compile(
    r"^#{1,3}\s+(?:Module|File|Package|Namespace|Crate):\s*(.+)$",
    re.MULTILINE,
)


def _split_sections(text: str) -> List[Tuple[str, str, int]]:
    """
    Split *text* into ``(header, body, level)`` triples.

    ``level`` is the Markdown heading depth (1–4).
    """
    positions = [(m.start(), m.group(1), m.group(2)) for m in _SECTION_HEADER_RE.finditer(text)]
    if not positions:
        return [("", text, 0)]

    sections: List[Tuple[str, str, int]] = []
    for idx, (start, hashes, title) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        body = text[start:end]
        sections.append((title.strip(), body, len(hashes)))
    return sections


def _extract_signatures(body: str) -> List[str]:
    """Return all signature lines from a section body."""
    return _SIGNATURE_RE.findall(body)


def _extract_signature_block(body: str) -> str:
    """Return only the signature lines (plus module headers) from a body."""
    lines = body.splitlines(keepends=True)
    kept: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            # keep single blank between blocks
            if kept and kept[-1].strip():
                kept.append("\n")
            continue
        if stripped.startswith("#"):
            kept.append(line)
            continue
        if _SIGNATURE_RE.match(stripped):
            kept.append(line)
            continue
        # Keep decorator / attribute lines directly before signatures
        if stripped.startswith("@") or stripped.startswith("//") or stripped.startswith("///"):
            kept.append(line)
            continue
    return "".join(kept)


def _extract_skeleton(body: str) -> str:
    """Return module headers + public function names only."""
    lines = body.splitlines(keepends=True)
    kept: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            kept.append(line)
            continue
        m = _PUBLIC_FUNC_RE.match(stripped)
        if m:
            # Keep just the function name line, trimmed
            kept.append(line)
    return "".join(kept)


# ---------------------------------------------------------------------------
# Compressor
# ---------------------------------------------------------------------------

class MatrixMultiLevelCompressor:
    """
    Production multi-level compressor.

    Usage::

        comp = MatrixMultiLevelCompressor()
        l2 = comp.compress(prompt, CompressionLevel.L2_STRUCTURAL)
        stats = comp.get_stats(prompt, l2, CompressionLevel.L2_STRUCTURAL)
    """

    # ------------------------------------------------------------------
    # compress
    # ------------------------------------------------------------------

    def compress(
        self,
        text: str,
        level: CompressionLevel,
        *,
        token_budget: Optional[int] = None,
    ) -> str:
        """
        Compress *text* to the requested *level*.

        Parameters
        ----------
        text : str
            The full matrix prompt.
        level : CompressionLevel
            Target compression level.
        token_budget : int, optional
            If given, further trim to fit within *token_budget* tokens.
        """
        if level == CompressionLevel.L1_FULL:
            result = text
        elif level == CompressionLevel.L2_STRUCTURAL:
            result = self._compress_l2(text)
        elif level == CompressionLevel.L3_SKELETON:
            result = self._compress_l3(text)
        else:
            result = text

        if token_budget is not None:
            result = self._enforce_budget(result, token_budget)

        return result

    # ------------------------------------------------------------------
    # L2 — structural (signatures + hierarchies + deps)
    # ------------------------------------------------------------------

    def _compress_l2(self, text: str) -> str:
        sections = _split_sections(text)
        parts: List[str] = []
        for title, body, level in sections:
            sig_block = _extract_signature_block(body)
            if sig_block.strip():
                parts.append(sig_block)
            elif level <= 2:
                # Keep top-level headers even if no signatures
                header_line = f"{'#' * max(level, 1)} {title}\n" if title else ""
                parts.append(header_line)
        return "\n".join(parts).strip() + "\n"

    # ------------------------------------------------------------------
    # L3 — skeleton (module names + public function names)
    # ------------------------------------------------------------------

    def _compress_l3(self, text: str) -> str:
        sections = _split_sections(text)
        parts: List[str] = []
        for title, body, level in sections:
            skel = _extract_skeleton(body)
            if skel.strip():
                parts.append(skel)
            elif level == 1:
                parts.append(f"# {title}\n" if title else "")
        return "\n".join(parts).strip() + "\n"

    # ------------------------------------------------------------------
    # Token budget enforcement
    # ------------------------------------------------------------------

    @staticmethod
    def _enforce_budget(text: str, budget: int) -> str:
        """Truncate *text* section-by-section until within *budget*."""
        if count_tokens(text) <= budget:
            return text

        lines = text.splitlines(keepends=True)
        # Binary search for max lines within budget
        lo, hi = 0, len(lines)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            candidate = "".join(lines[:mid])
            if count_tokens(candidate) <= budget:
                lo = mid
            else:
                hi = mid - 1
        return "".join(lines[:lo])

    # ------------------------------------------------------------------
    # Auto-select
    # ------------------------------------------------------------------

    def auto_select_level(self, context_window: int) -> CompressionLevel:
        """
        Pick the best compression level for a given context-window size.

        * ≥ 200 000 → L1
        * ≥ 64 000  → L2
        * otherwise → L3
        """
        if context_window >= 200_000:
            return CompressionLevel.L1_FULL
        if context_window >= 64_000:
            return CompressionLevel.L2_STRUCTURAL
        return CompressionLevel.L3_SKELETON

    def auto_select_for_model(self, model: str) -> CompressionLevel:
        """
        Select level based on a known model identifier.

        Falls back to L2 for unrecognised models.
        """
        key = model.lower().strip()
        # Try exact match first
        if key in _MODEL_CONTEXT_WINDOWS:
            return self.auto_select_level(_MODEL_CONTEXT_WINDOWS[key])
        # Prefix match
        for name, window in _MODEL_CONTEXT_WINDOWS.items():
            if key.startswith(name) or name.startswith(key):
                return self.auto_select_level(window)
        # Default to L2 (safe for most modern models ≥128K)
        return CompressionLevel.L2_STRUCTURAL

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(
        self,
        original: str,
        compressed: str,
        level: CompressionLevel,
    ) -> CompressionResult:
        """
        Compute compression statistics.

        ``compression_ratio`` = original_tokens / compressed_tokens.
        """
        orig_tok = count_tokens(original)
        comp_tok = count_tokens(compressed)
        ratio = orig_tok / comp_tok if comp_tok > 0 else float("inf")

        # Count preserved / removed sections
        orig_sections = _split_sections(original)
        comp_text_lower = compressed.lower()
        preserved = sum(
            1 for title, _, _ in orig_sections
            if title and title.lower() in comp_text_lower
        )
        removed = len(orig_sections) - preserved

        # Count preserved signatures
        orig_sigs = set()
        for _, body, _ in orig_sections:
            for m in _PUBLIC_FUNC_RE.finditer(body):
                orig_sigs.add(m.group(1))
        comp_sigs = set()
        for m in _PUBLIC_FUNC_RE.finditer(compressed):
            comp_sigs.add(m.group(1))
        sigs_preserved = len(orig_sigs & comp_sigs)

        return CompressionResult(
            compression_ratio=ratio,
            original_tokens=orig_tok,
            compressed_tokens=comp_tok,
            sections_preserved=preserved,
            sections_removed=removed,
            signatures_preserved=sigs_preserved,
            level=level,
        )

    # ------------------------------------------------------------------
    # Quality gate self-check
    # ------------------------------------------------------------------

    def validate_gate_g4(self, prompt: str) -> Tuple[bool, List[str]]:
        """Run all G4 quality checks. Returns (passed, errors)."""
        errors: List[str] = []

        # L1 identity
        l1 = self.compress(prompt, CompressionLevel.L1_FULL)
        if l1 != prompt:
            errors.append("L1 is not identity")

        # L2 token limit
        l2 = self.compress(prompt, CompressionLevel.L2_STRUCTURAL)
        l2_tok = count_tokens(l2)
        if l2_tok > 30_000:
            errors.append(f"L2 has {l2_tok} tokens (limit 30K)")

        # L3 token limit
        l3 = self.compress(prompt, CompressionLevel.L3_SKELETON)
        l3_tok = count_tokens(l3)
        if l3_tok > 10_000:
            errors.append(f"L3 has {l3_tok} tokens (limit 10K)")

        # L2 < L1 < L3
        if len(l2) >= len(l1):
            errors.append("L2 is not smaller than L1")
        if len(l3) >= len(l2):
            errors.append("L3 is not smaller than L2")

        # Signature preservation in L2
        orig_sigs = set(_PUBLIC_FUNC_RE.findall(prompt))
        l2_sigs = set(_PUBLIC_FUNC_RE.findall(l2))
        missing = orig_sigs - l2_sigs
        if missing:
            errors.append(
                f"L2 lost {len(missing)} signatures: "
                + ", ".join(sorted(list(missing)[:10]))
            )

        # auto_select_level
        if self.auto_select_level(200_000) != CompressionLevel.L1_FULL:
            errors.append("auto_select_level(200K) != L1")
        if self.auto_select_level(128_000) != CompressionLevel.L2_STRUCTURAL:
            errors.append("auto_select_level(128K) != L2")
        if self.auto_select_level(32_000) != CompressionLevel.L3_SKELETON:
            errors.append("auto_select_level(32K) != L3")

        # token_budget
        budget = 1000
        budgeted = self.compress(
            prompt, CompressionLevel.L2_STRUCTURAL, token_budget=budget
        )
        if count_tokens(budgeted) > budget:
            errors.append(f"token_budget={budget} exceeded")

        return (len(errors) == 0, errors)
