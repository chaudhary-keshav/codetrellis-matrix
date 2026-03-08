# ADR-001: Flat YAML Files Over Nested Structures

**Status**: Accepted  
**Date**: 2024-12-01  
**Context**: BPL v1.0

## Decision

Best practices are stored as flat YAML files (one file per technology/category) rather than deeply nested hierarchical structures.

## Context

We needed to decide how to organize 252+ best practices for efficient loading, authoring, and maintenance. Options considered:

1. **Single monolithic YAML** — All practices in one file
2. **Deeply nested hierarchy** — Category → Level → Framework → Practice
3. **Flat files by technology** — One file per tech (chosen)
4. **Database** — SQLite or similar

## Rationale

- **Authoring simplicity**: Contributors add practices to the relevant technology file without navigating complex hierarchies
- **Git-friendly**: Changes to Python practices don't conflict with TypeScript practice changes
- **Partial loading**: Can load only relevant files for faster startup (future optimization)
- **Validation**: Each file can be independently validated
- **Human-readable**: Easy to review in PRs

## Consequences

- Repository must build its own indexes (by_category, by_level, by_framework) at load time
- Cross-technology practice relationships must use IDs (`related_practices` field)
- Practice ID prefixes (PY*, TS*, NG*) encode file membership, creating a soft coupling
- Total load time: ~0.5s for 252 practices (acceptable)
