# BPL Architecture

> Best Practices Library — Technical Architecture Document
> **Version:** v1.4 | **Updated:** 7 February 2026

## Overview

The BPL is a rule-based, context-aware best practices injection system nested within CodeTrellis (Project Self-Awareness System). It analyzes project structure and dependencies to select relevant coding practices, which are appended to the `matrix.prompt` output for AI consumption.

## System Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  CodeTrellis CLI   │────▶│  ProjectContext   │────▶│ PracticeSelector│
│  (cli.py)   │     │  .from_matrix()   │     │   .select()     │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                    ┌──────────────────┐               │
                    │  BPL Repository  │◀──────────────┘
                    │  (YAML loading)  │
                    └────────┬─────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    ▼              ▼         ▼         ▼              ▼
python_core    angular    react     nestjs      django
typescript     fastapi    flask    database     devops
design_patterns   solid_patterns   python_3_10/11/12
```

## Module Structure

```
codetrellis/bpl/
├── __init__.py          # Lazy imports, public API (+ count_tokens, OutputFormat)
├── models.py            # Core data models (~735 lines)
├── repository.py        # YAML loading, caching, querying (~675 lines)
├── selector.py          # Context-aware selection (~977 lines, includes tiktoken)
└── practices/           # 16 YAML files, 407 practices total
    ├── python_core.yaml          (17 practices)
    ├── python_core_expanded.yaml (60 practices)
    ├── python_3_10.yaml          (12 practices)
    ├── python_3_11.yaml          (12 practices)
    ├── python_3_12.yaml          (12 practices)
    ├── typescript_core.yaml      (45 practices)
    ├── angular.yaml              (45 practices)
    ├── fastapi.yaml              (10 practices)
    ├── design_patterns.yaml      (30 practices)
    ├── solid_patterns.yaml        (9 practices)
    ├── react.yaml                (40 practices) — NEW v1.2
    ├── nestjs.yaml               (30 practices) — NEW v1.2
    ├── django.yaml               (30 practices) — NEW v1.3
    ├── flask.yaml                (20 practices) — NEW v1.3
    ├── database.yaml             (20 practices) — NEW v1.3
    └── devops.yaml               (15 practices) — NEW v1.3
```

## Core Classes

### `BestPractice` (models.py)

The primary data model. Each practice has:

- **id**: Unique prefix-based identifier (PY*, TS*, NG*, FAST*, DP*, SOLID*, REACT*, NEST*, DJANGO*, FLASK*, DB*, DEVOPS*)
- **category**: One of 50+ `PracticeCategory` enum values
- **level**: beginner → intermediate → advanced → expert
- **priority**: critical → high → medium → low → optional
- **content**: Description, examples, rationale, tags
- **applicability**: Framework/dependency/pattern matching rules
  - `frameworks`, `patterns`, `file_patterns`, `has_dependencies`, `project_types`, `excluded_patterns`
  - `min_python`: Minimum Python version required (e.g., `"3.10"`) — _added v1.1_
  - `contexts`: Usage contexts for relevance (e.g., `["async", "concurrent-io"]`) — _added v1.1_
- **complexity_score**: Implementation complexity 1-10 (1-3 simple, 4-6 moderate, 7-10 complex) — _added v1.3_
- **anti_pattern_id**: Cross-reference to related anti-pattern practice — _added v1.3_
- **python_version**: `VersionConstraint` for version-specific practices

### `BestPracticesRepository` (repository.py)

Loads practices from YAML, builds indexes, provides query methods.

- Indexes: by_category, by_level, by_framework
- Cache: JSON-based with mtime invalidation
- Query: `get_by_*()`, `search()`, `get_applicable()`, `get_statistics()`

### `PracticeSelector` (selector.py)

Context-aware selection pipeline:

1. `_filter_applicable()` — Framework matching via ID prefix + applicability rules
2. `_filter_by_criteria()` — Category/level/priority/framework filters
3. `_score_practices()` — Relevance scoring (priority + match counts)
4. `_enforce_token_budget()` — Token limit enforcement using tiktoken or char/4 fallback

### `ProjectContext` (selector.py)

Built from `ProjectMatrix` via `from_matrix()`:

- Weighted artifact counting with `SIGNIFICANCE_THRESHOLD=5`
- `DOMINANCE_RATIO=0.1` for multi-language projects
- Framework detection from dependencies and artifact types

### `SelectionCriteria` (selector.py)

User-configurable filters:

- `categories`, `levels`, `min_priority`, `frameworks`
- `max_practices` (count limit), `max_tokens` (budget limit)
- `include_generic` (design patterns), `python_version`

### Token Utilities (selector.py) — _NEW v1.4_

- `count_tokens(text)` — Uses tiktoken (cl100k_base) if available, else char/4 heuristic
- `is_tiktoken_available()` — Check if accurate token counting is available
- `OutputFormat` — Dynamic format selection based on token budget:
  - `OutputFormat.select_format_for_budget(practices, max_tokens)` — Returns best format
  - Tiers: `full` → `prompt` → `compact` → `minimal`

## Data Flow

```
1. CLI: codetrellis scan . --include-practices --practices-format standard
2. Scanner produces ProjectMatrix
3. _generate_practices_section(matrix, ...)
4. PracticeSelector.select_for_project(matrix, criteria)
   a. ProjectContext.from_matrix(matrix) → detect frameworks
   b. Repository.iter_practices() → all 407 practices
   c. _filter_applicable() → 407 → ~120 (language match)
   d. _filter_by_criteria() → ~120 → ~60 (priority/category)
   e. _score_practices() → sort by relevance
   f. _enforce_token_budget() → optional trim (uses tiktoken if available)
   g. limit to max_practices → 15 (standard)
5. BPLOutput.to.codetrellis_format(tier="prompt" or "minimal")
6. Appended to matrix.prompt as [BEST_PRACTICES] section
```

## ID Prefix Convention

| Prefix    | Language/Framework | Example   | Count |
| --------- | ------------------ | --------- | :---: |
| `PY*`     | Python core        | PY001     |  35   |
| `PYE*`    | Python expanded    | PYE001    |  30   |
| `TS*`     | TypeScript         | TS001     |  50   |
| `NG*`     | Angular            | NG001     |  50   |
| `FAST*`   | FastAPI            | FAST001   |  32   |
| `DP*`     | Design Patterns    | DP001     |  30   |
| `SOLID*`  | SOLID Principles   | SOLID001  |   5   |
| `NEST*`   | NestJS             | NEST001   |  30   |
| `REACT*`  | React              | REACT001  |  40   |
| `DB*`     | Database           | DB001     |  20   |
| `DJANGO*` | Django             | DJANGO001 |  30   |
| `FLASK*`  | Flask              | FLASK001  |  20   |
| `DEVOPS*` | DevOps             | DEVOPS001 |  15   |

## Output Formats

| Format          | Max Practices | Detail Level                     | Use Case                     |
| --------------- | :-----------: | -------------------------------- | ---------------------------- |
| `minimal`       |      25       | ID + level + title only          | Large prompts, tight budgets |
| `compact`       |      20       | ID + level + title + brief desc  | Medium budgets               |
| `standard`      |      15       | Description + truncated examples | Default for AI prompts       |
| `comprehensive` |       8       | Full detail + all examples       | Learning, documentation      |

### Dynamic Format Selection (v1.4)

Use `OutputFormat.select_format_for_budget()` to automatically choose the best format:

```python
from.codetrellis.bpl import OutputFormat

# Returns "minimal", "compact", "prompt", or "full" based on budget
best_format = OutputFormat.select_format_for_budget(practices, max_tokens=1000)
```

## Observability

- **Timing**: `time.perf_counter()` in `load_all()` and `select()`
- **Filter-stage logging**: Practice counts at each pipeline stage (DEBUG level)
- **Selection summary**: Final count + context logged at INFO level
- **Validation**: `scripts/validate_practices.py` for CI/pre-commit

## Testing

- **125 unit tests** across 3 files:
  - `test_bpl_models.py` — Models, enums, version constraints, applicability rules
  - `test_bpl_repository.py` — Loading, querying, search, cache lifecycle, error handling
  - `test_bpl_selector.py` — Context building, selection, scoring, token budget

---

## Session Log

### Current Session (v1.4 Release)

**Validated Status:**

- ✅ 407 practices validated (0 errors, 0 warnings)
- ✅ 125 tests passing (15.80s runtime)
- ✅ CLI integration working (`python -m codetrellis scan . --include-practices`)
- ✅ All 4 output formats functional (minimal/compact/standard/comprehensive)
- ✅ Token budget enforcement working with `--max-practice-tokens`
- ✅ tiktoken integration (optional) with char/4 fallback

**New Features (v1.4):**

- `count_tokens()` — Accurate token counting with tiktoken
- `is_tiktoken_available()` — Check tiktoken availability
- `OutputFormat.select_format_for_budget()` — Dynamic format selection
- "minimal" output tier — ID + level + title only
- `complexity_score` field — 1-10 difficulty rating
- `anti_pattern_id` field — Cross-reference to anti-patterns

**New Practice Files:**

- `database.yaml` — 20 database practices (DB001-DB020)
- `devops.yaml` — 15 DevOps practices (DEVOPS001-DEVOPS015)
- `django.yaml` — 30 Django practices (DJANGO001-DJANGO030)
- `flask.yaml` — 20 Flask practices (FLASK001-FLASK020)
- `nestjs.yaml` — 30 NestJS practices (NEST001-NEST030)
- `react.yaml` — 40 React practices (REACT001-REACT040)

---

### 6 February 2026 (Afternoon Session)

**Validated Status:**

- ✅ 252 practices validated (0 errors, 0 warnings)
- ✅ 125 tests passing (8.00s runtime)
- ✅ CLI integration working (`python -m codetrellis scan . --include-practices`)
- ✅ All 3 output formats functional (minimal/standard/comprehensive)

**Verified Components:**

- .codetrellis/bpl/models.py` — Core data models with `ApplicabilityRule.min_python` and `contexts`
- .codetrellis/bpl/repository.py` — YAML loading with timing metrics
- .codetrellis/bpl/selector.py` — Context-aware selection with token budget enforcement
- `scripts/validate_practices.py` — Schema validation (0 warnings achieved)
- .codetrellis/__main__.py` — Module entry point for `python -m.codetrellis`

**Documentation Updated:**

- This file (ARCHITECTURE.md)
- ROADMAP.md — Phase 2 checklist items marked complete
- BPL_BUSINESS_STRATEGY.md — Session update section added
- ENTERPRISE_BEST_PRACTICES_LIBRARY.md — Status tables updated
