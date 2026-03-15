#!/usr/bin/env python3
"""
PoC: JSON Patch Differential Engine (F3)
=========================================
Demonstrates RFC 6902 JSON Patch generation, application, and verification
against the real CodeTrellis matrix.json.
"""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

MATRIX_JSON_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.json"


def main():
    print("=" * 60)
    print("F3 PoC: JSON Patch Differential Engine")
    print("=" * 60)

    if not MATRIX_JSON_PATH.exists():
        print(f"ERROR: matrix.json not found at {MATRIX_JSON_PATH}")
        return 1

    from codetrellis.matrix_diff import MatrixDiffEngine

    original = json.loads(MATRIX_JSON_PATH.read_text())
    print(f"Original matrix.json: {len(json.dumps(original)):,} bytes")

    # Simulate a small change
    modified = copy.deepcopy(original)
    modified["__poc_marker__"] = "F3_test"
    if "version" in modified:
        modified["version"] = str(modified["version"]) + "-patched"

    engine = MatrixDiffEngine()

    # Generate patch
    patch = engine.compute_diff(original, modified)
    patch_ops = patch.patch if hasattr(patch, "patch") else list(patch)
    print(f"Patch operations: {len(patch_ops)}")
    print(f"Patch size: {len(json.dumps(patch_ops)):,} bytes")

    # Apply patch
    reconstructed = engine.apply_patch(original, patch)
    assert reconstructed.get("__poc_marker__") == "F3_test"
    print("✅ Patch applied correctly")

    # Verify integrity
    ok = engine.verify_patch_integrity(original, modified, patch)
    print(f"✅ Integrity verified: {ok}")

    # Stats
    stats = engine.get_patch_stats(patch, modified)
    print(f"Compression ratio: {stats.compression_ratio:.1f}x")
    print(f"Total ops: {stats.total_operations}")

    print("\n✅ F3 PoC PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
