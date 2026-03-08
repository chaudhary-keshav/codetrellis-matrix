#!/usr/bin/env python3
"""
PoC: TF-IDF Matrix Embeddings (F2)
=====================================
Builds a lightweight TF-IDF embedding index over matrix.prompt sections.
"""

import re
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / "4.16.0" / "codetrellis" / "matrix.prompt"


def parse_sections(prompt: str) -> Dict[str, str]:
    """Parse matrix.prompt into {section_name: content}."""
    sections: Dict[str, str] = {}
    current = ""
    lines: list[str] = []
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


def main():
    print("=" * 60)
    print("F2 PoC: TF-IDF Matrix Embeddings")
    print("=" * 60)

    if not MATRIX_PROMPT_PATH.exists():
        print(f"ERROR: matrix.prompt not found at {MATRIX_PROMPT_PATH}")
        return 1

    from codetrellis.matrix_embeddings import MatrixEmbeddingIndex

    prompt = MATRIX_PROMPT_PATH.read_text()
    print(f"Matrix prompt: {len(prompt):,} chars, {len(prompt.split()):,} words")

    sections = parse_sections(prompt)
    print(f"Sections found: {len(sections)}")

    idx = MatrixEmbeddingIndex()
    idx.build_index(sections)
    print(f"Index built: {len(idx._index)} sections indexed")

    queries = [
        "Python type system and dataclasses",
        "REST API endpoints",
        "project build and deployment",
        "error handling patterns",
        "React component lifecycle",
    ]

    for q in queries:
        results = idx.query(q, top_k=3)
        print(f"\nQuery: '{q}'")
        for r in results:
            print(f"  [{r.score:.3f}] {r.section_id}")

    savings = idx.get_token_savings(len(prompt.split()), top_k=3, query="Python")
    print(f"\nToken savings: {savings['savings_percent']:.1f}%")

    print("\n✅ F2 PoC PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
