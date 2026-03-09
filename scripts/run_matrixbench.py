#!/usr/bin/env python3
"""Run MatrixBench baseline scoring and save results."""
import json
from pathlib import Path
from codetrellis.matrixbench_scorer import MatrixBench

cache_dir = Path(".codetrellis/cache/4.16.0/codetrellis-matrix")
matrix_json = json.loads((cache_dir / "matrix.json").read_text(encoding="utf-8"))
matrix_prompt = (cache_dir / "matrix.prompt").read_text(encoding="utf-8")

bench = MatrixBench(matrix_json=matrix_json, matrix_prompt=matrix_prompt)
results = bench.run_all()

# Print summary
print(f"Total tasks: {results.total_tasks}")
print(f"Passed: {results.passed_tasks}/{results.total_tasks}")
print(f"Failed: {results.failed_tasks}")
print(f"Avg score: {results.avg_improvement_pct:.1f}%")
print()
for cat, score in sorted(results.category_scores.items()):
    print(f"  {cat}: {score:.2%}")

# Export
bench.export_results(results, "docs/matrixbench_baseline.json")
report = bench.generate_report(results)
Path("docs/matrixbench_baseline.md").write_text(report, encoding="utf-8")
print("\nBaseline saved to docs/matrixbench_baseline.json and docs/matrixbench_baseline.md")

# Run G7 gate
passed, errors = bench.validate_gate_g7()
print(f"\nG7 gate: {'PASSED' if passed else 'FAILED'}")
if errors:
    for e in errors:
        print(f"  - {e}")
