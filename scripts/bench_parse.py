#!/usr/bin/env python3
"""Benchmark parser performance on real project files."""
import os
import time
from codetrellis.python_parser_enhanced import EnhancedPythonParser

py_parser = EnhancedPythonParser()

# Collect Python source files
py_files = []
for root, dirs, files in os.walk('codetrellis'):
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(root, f))

print(f"Found {len(py_files)} Python files")

# Benchmark: parse all files
total_loc = 0
t0 = time.perf_counter()
for pf in py_files:
    content = open(pf).read()
    total_loc += content.count('\n')
    py_parser.parse(content, pf)
elapsed = time.perf_counter() - t0

print(f"Parsed {len(py_files)} files ({total_loc:,} LOC) in {elapsed:.2f}s")
print(f"  Per file: {elapsed/len(py_files)*1000:.1f}ms")
print(f"  Per KLOC: {elapsed/(total_loc/1000)*1000:.1f}ms")
print(f"  Throughput: {total_loc/elapsed:,.0f} LOC/s")
