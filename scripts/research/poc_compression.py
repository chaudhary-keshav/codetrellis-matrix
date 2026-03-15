#!/usr/bin/env python3
"""
PoC: Multi-Level Compression (F4)
====================================
Demonstrates L1/L2/L3 matrix compression with metrics.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from codetrellis import __version__ as VERSION

MATRIX_PROMPT_PATH = ROOT / ".codetrellis" / "cache" / VERSION / "codetrellis" / "matrix.prompt"


def main():
    print("=" * 60)
    print("F4 PoC: Multi-Level Compression")
    print("=" * 60)

    if not MATRIX_PROMPT_PATH.exists():
        print(f"ERROR: matrix.prompt not found at {MATRIX_PROMPT_PATH}")
        return 1

    from codetrellis.matrix_compressor_levels import (
        CompressionLevel,
        MatrixMultiLevelCompressor,
    )

    prompt = MATRIX_PROMPT_PATH.read_text()
    comp = MatrixMultiLevelCompressor()

    print(f"\nOriginal: {len(prompt):,} chars, ~{len(prompt.split()):,} tokens")

    for level in CompressionLevel:
        compressed = comp.compress(prompt, level)
        stats = comp.get_stats(prompt, compressed, level)
        retention = stats.compressed_tokens / stats.original_tokens if stats.original_tokens > 0 else 1.0
        print(
            f"\n{level.name}:"
            f"\n  Size: {len(compressed):,} chars"
            f"\n  Tokens: ~{stats.compressed_tokens:,}"
            f"\n  Ratio: {stats.compression_ratio:.2f}x"
            f"\n  Retention: {retention:.1%}"
        )

    # Auto-select for various models
    models = ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "deepseek-chat", "o1-mini"]
    print("\nAuto-selected levels per model:")
    for model in models:
        level = comp.auto_select_for_model(model)
        print(f"  {model}: {level.name}")

    print("\n✅ F4 PoC PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
