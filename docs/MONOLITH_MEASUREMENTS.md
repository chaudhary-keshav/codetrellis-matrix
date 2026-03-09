# Monolith Module Measurements

> Generated as part of the v5.0 Improvement Plan — Phase 2.8
> For Phase 5 modularization planning

## Measurements

| Module          | LOC    | Total Methods | Core Methods                          | Threshold (10K LOC) |
| --------------- | ------ | ------------- | ------------------------------------- | ------------------- |
| `scanner.py`    | 25,919 | 143           | 118 `_parse_*`/`_scan_*`/`_extract_*` | **Exceeds**         |
| `compressor.py` | 28,415 | 449           | 419 `_compress_*`                     | **Exceeds**         |
| `streaming.py`  | 668    | 32            | —                                     | Within limit        |

## Assessment

Both `scanner.py` and `compressor.py` significantly exceed the 10K LOC threshold
proposed by the Architect agent review. They are 2.5-2.8x the threshold.

However, per the validated plan consensus (5/6 agents agree):

- The monolith structure works for single-developer workflow
- 6747+ tests pass against the current structure
- Splitting introduces import complexity and potential circular dependencies
- The primary risk is merge conflicts, which only matter with multiple contributors

## Recommendation

**Defer modularization to Phase 5 (Release Readiness)** when preparing for public release.
If the project moves to multi-contributor development, modularization becomes higher priority.

The most natural split would be per-language modules:

- `scanner.py` → `scanners/{python,typescript,java,csharp,...}.py`
- `compressor.py` → `compressors/{python,typescript,java,csharp,...}.py`

Each `_parse_*` / `_compress_*` method group corresponds to a language, making the split mechanical.
