#!/usr/bin/env python3
"""
PoC: Matrix Navigator / Directed Retrieval (F6)
==================================================
Three-phase file discovery: keyword → graph → embedding.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / "4.16.0" / "codetrellis" / "matrix.json"
MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / "4.16.0" / "codetrellis" / "matrix.prompt"


def main():
    print("=" * 60)
    print("F6 PoC: Matrix Navigator / Directed Retrieval")
    print("=" * 60)

    if not MATRIX_JSON_PATH.exists() or not MATRIX_PROMPT_PATH.exists():
        print("ERROR: matrix files not found")
        return 1

    from codetrellis.matrix_navigator import MatrixNavigator

    matrix = json.loads(MATRIX_JSON_PATH.read_text())
    prompt = MATRIX_PROMPT_PATH.read_text()

    nav = MatrixNavigator(matrix, prompt)

    queries = [
        "scanner and file discovery",
        "Python AST parsing",
        "CLI argument handling",
        "caching and performance",
        "matrix compression",
    ]

    for q in queries:
        print(f"\nQuery: '{q}'")
        results = nav.discover(q, max_files=5)
        for r in results:
            print(f"  [{r.composite_score:.3f}] {r.file_path} ({r.reached_via})")

    # Dependency graph
    print("\nDependency graph for scanner.py:")
    deps = nav.get_dependencies("codetrellis/scanner.py")
    for d in list(deps)[:5]:
        print(f"  → {d}")

    print("\n✅ F6 PoC PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
