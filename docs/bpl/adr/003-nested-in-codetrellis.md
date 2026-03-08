# ADR-003: BPL Nested in CodeTrellis

**Status**: Accepted  
**Date**: 2024-12-01  
**Context**: BPL v1.0

## Decision

BPL is a sub-module within CodeTrellis (.codetrellis/bpl/`) rather than a standalone package.

## Context

We needed to decide the deployment model for the Best Practices Library. Options considered:

1. **Standalone pip package** — Separate `pip install bpl`
2. **CodeTrellis sub-module** — Nested at .codetrellis/bpl/` (chosen)
3. **External service** — API-based practice lookup

## Rationale

- **Single install**: Users get BPL automatically with `pip install.codetrellis`
- **Tight integration**: BPL consumes `ProjectMatrix` directly; no serialization boundary
- **Shared versioning**: BPL version tracks CodeTrellis version; no compatibility matrix
- **Lazy loading**: BPL only imports when `--include-practices` is used (via `__init__.py` lazy imports)
- **No network dependency**: All practices bundled; works offline

## Consequences

- BPL cannot be used independently of CodeTrellis (acceptable — it's designed for CodeTrellis context)
- Practice YAML files are bundled in the package, increasing package size by ~100KB
- Changes to BPL require a CodeTrellis release (coupling accepted for simplicity)
- Future: if BPL grows significantly, can extract to a plugin architecture
