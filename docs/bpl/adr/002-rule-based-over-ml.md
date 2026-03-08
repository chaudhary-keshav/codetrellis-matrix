# ADR-002: Rule-Based Selection Over ML

**Status**: Accepted  
**Date**: 2024-12-01  
**Context**: BPL v1.0

## Decision

Practice selection uses deterministic rule-based matching (framework prefix, applicability rules, priority scoring) rather than ML models.

## Context

We needed to select relevant practices from 252+ options based on detected project context. Options considered:

1. **ML/embedding-based** — Vector similarity between project features and practice descriptions
2. **Rule-based with scoring** — Deterministic filtering + weighted scoring (chosen)
3. **Hybrid** — Rules for filtering, ML for ranking

## Rationale

- **Determinism**: Same project → same practices, every time. Critical for reproducible AI prompts
- **Debuggability**: Each filter stage logs counts; easy to trace why a practice was included/excluded
- **Zero dependencies**: No ML libraries, no model files, no GPU requirements
- **Speed**: Selection completes in <10ms for 252 practices
- **Explainability**: `filters_applied` in BPLOutput shows exactly what criteria were used

## Selection Pipeline

```
252 practices → _filter_applicable (framework match) → ~80
    → _filter_by_criteria (category/level/priority) → ~40
    → _score_practices (relevance sort) → ranked
    → max_practices limit → 15
    → _enforce_token_budget → final set
```

## Consequences

- Cannot learn from user feedback or practice adoption patterns (accepted trade-off)
- Adding new selection heuristics requires code changes (vs. retraining a model)
- Scoring function is simple (priority + match count); may need refinement for complex projects
