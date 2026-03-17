#!/usr/bin/env python3
"""
PoC: JSON-LD Semantic Encoder (F1)
====================================
Encodes matrix.json as a W3C JSON-LD 1.1 knowledge graph.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / "codetrellis" / "matrix.json"


def main():
    print("=" * 60)
    print("F1 PoC: JSON-LD Semantic Encoder")
    print("=" * 60)

    if not MATRIX_JSON_PATH.exists():
        print(f"ERROR: matrix.json not found at {MATRIX_JSON_PATH}")
        return 1

    from codetrellis.matrix_jsonld import MatrixJsonLdEncoder

    matrix = json.loads(MATRIX_JSON_PATH.read_text())
    encoder = MatrixJsonLdEncoder()

    # Full encode
    ld_full = encoder.encode(matrix)
    full_size = len(json.dumps(ld_full))
    print(f"Full JSON-LD: {full_size:,} bytes, {len(ld_full.get('@graph', []))} nodes")

    # Compact encode
    ld_compact = encoder.encode_compact(matrix)
    compact_size = len(json.dumps(ld_compact))
    print(f"Compact JSON-LD: {compact_size:,} bytes")
    print(f"Reduction: {(1 - compact_size / full_size) * 100:.1f}%")

    # Frame by Module
    ld_full_doc = encoder.encode(matrix)
    framed = encoder.frame(ld_full_doc, {"@type": "ct:Module"})
    print(f"Framed (Module only): {len(framed.get('@graph', []))} nodes")

    # Validate
    valid = encoder.validate(ld_full)
    print(f"✅ Validation: {'PASS' if valid else 'FAIL'}")

    # Stats
    stats = encoder.get_stats(matrix, ld_full)
    print(f"Nodes: {stats.total_nodes}, Edges: {stats.total_edges}, Sections: {stats.sections_encoded}")

    print("\n✅ F1 PoC PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
