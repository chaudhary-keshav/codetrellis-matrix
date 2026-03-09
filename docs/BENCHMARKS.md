# CodeTrellis Performance Benchmarks

Measured on CodeTrellis v4.96, macOS (Apple Silicon), Python 3.14.

## Project Stats

| Metric          | Value   |
| --------------- | ------- |
| Source files    | 756     |
| Total LOC       | 319,519 |
| Language        | Python  |
| Matrix sections | 33      |
| Types extracted | 1,531   |

## Parse Performance

Single-threaded regex-based parsing of all 756 Python source files:

| Metric           | Value        |
| ---------------- | ------------ |
| Total parse time | 5.59s        |
| Per file         | 7.4ms        |
| Per KLOC         | 17.5ms       |
| Throughput       | 57,158 LOC/s |

### Scaling Estimates

Based on measured throughput (~57K LOC/s single-threaded):

| Project Size      | Files | LOC  | Est. Parse Time |
| ----------------- | ----- | ---- | --------------- |
| Small             | <100  | ~5K  | <1s             |
| Medium            | ~500  | ~50K | ~1s             |
| Large (this repo) | 756   | 320K | ~6s             |
| Very Large        | 5,000 | 1M+  | ~20s            |

Note: These are parse-only times. Full `codetrellis scan` includes file I/O,
compression, BPL selection, and matrix output, which adds overhead.
Parallel mode (`--optimal`) uses multiple processes for large projects.

## Matrix Output Size

| Format        | Size   | Compression vs JSON |
| ------------- | ------ | ------------------- |
| matrix.json   | 3.1 MB | 1× (baseline)       |
| matrix.prompt | 644 KB | 4.9× compressed     |
| Source code   | ~12 MB | 18.6× compressed    |

The prompt format compresses 12 MB of source into a 644 KB AI-ready context.

## MatrixBench Quality Score

| Category       | Score     |
| -------------- | --------- |
| Completeness   | 100%      |
| Accuracy       | 100%      |
| Compression    | 100%      |
| Cross-language | 100%      |
| Navigation     | 50%       |
| **Overall**    | **90.0%** |

G7 quality gate: **PASSED** (deterministic ±0%, JSON export verified)

## Test Suite Performance

| Metric        | Value |
| ------------- | ----- |
| Total tests   | 6,775 |
| Passed        | 6,775 |
| Skipped       | 101   |
| Errors        | 0     |
| Suite runtime | ~28s  |
