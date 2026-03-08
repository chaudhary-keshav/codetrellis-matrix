#!/usr/bin/env python3
"""
Run All PART F PoC Scripts
============================
Orchestrator that runs all 6 PoC scripts and summarises results.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

POCS = [
    ("F1 — JSON-LD", "poc_jsonld.py"),
    ("F2 — Embeddings", "poc_embeddings.py"),
    ("F3 — JSON Patch", "poc_json_patch.py"),
    ("F4 — Compression", "poc_compression.py"),
    ("F5 — Cross-Language", "poc_cross_language.py"),
    ("F6 — Navigator", "poc_navigator.py"),
]


def main():
    print("=" * 60)
    print("PART F: Run All PoC Scripts")
    print("=" * 60)

    results = []
    total_start = time.monotonic()

    for label, script in POCS:
        script_path = SCRIPTS_DIR / script
        print(f"\n{'—' * 50}")
        print(f"Running: {label} ({script})")
        print(f"{'—' * 50}")

        start = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(ROOT),
            )
            elapsed = (time.monotonic() - start) * 1000
            passed = result.returncode == 0
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            results.append((label, passed, elapsed))
        except subprocess.TimeoutExpired:
            elapsed = (time.monotonic() - start) * 1000
            print(f"  TIMEOUT after {elapsed:.0f}ms")
            results.append((label, False, elapsed))
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            print(f"  ERROR: {e}")
            results.append((label, False, elapsed))

    total_elapsed = (time.monotonic() - total_start) * 1000

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for label, passed, elapsed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {label}  ({elapsed:.0f}ms)")

    total_passed = sum(1 for _, p, _ in results if p)
    print(f"\nTotal: {total_passed}/{len(results)} passed in {total_elapsed:.0f}ms")

    return 0 if total_passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
