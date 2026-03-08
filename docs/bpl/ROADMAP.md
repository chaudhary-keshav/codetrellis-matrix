# BPL Roadmap

> Best Practices Library — Future Development Plan

## Current State (v1.4)

- ✅ 407 practices across 16 YAML files
- ✅ Rule-based context-aware selection
- ✅ CLI integration with 4 output formats (minimal, compact, prompt, full)
- ✅ 389+ unit tests (models, repository, selector)
- ✅ Token budget management (`--max-practice-tokens`)
- ✅ Structured logging & timing metrics
- ✅ YAML validation script
- ✅ JSON Schema for YAML files (`practices/schema/practice.schema.json`)
- ✅ Pre-commit hooks configured (`.pre-commit-config.yaml`)
- ✅ CI pipeline integration (`.github/workflows/bpl-ci.yml`)
- ✅ New schema fields: `complexity_score`, `anti_pattern_id`
- ✅ New categories: `automation`, `containers`, `deployment`, `infrastructure`
- ✅ tiktoken integration for accurate GPT token counting (with fallback)
- ✅ Dynamic format selection (`OutputFormat.select_format_for_budget()`)

## Phase 2: Expansion (v1.3) ✅ COMPLETE

### More Practices

- [x] React practices (REACT001–REACT040) — 40 practices _(Done 6 Feb 2026)_
- [x] NestJS practices (NEST001–NEST030) — 30 practices _(Done 6 Feb 2026)_
- [x] Django practices (DJANGO001–DJANGO030) — 30 practices _(Done 7 Feb 2026)_
- [x] Flask practices (FLASK001–FLASK020) — 20 practices _(Done 7 Feb 2026)_
- [x] Database/ORM practices (DB001–DB020) — 20 practices _(Done 7 Feb 2026)_
- [x] DevOps/CI practices (DEVOPS001–DEVOPS015) — 15 practices _(Done 7 Feb 2026)_

### Schema Improvements

- [x] Formalize `min_python` and `contexts` in `ApplicabilityRule` _(Done 6 Feb 2026)_
- [x] Added new categories: `validation`, `monitoring`, `reliability`, `accessibility`, `user_experience` _(Done 6 Feb 2026)_
- [x] Add `complexity_score` field to practices for better scoring _(Done 7 Feb 2026)_
- [x] Add `anti_pattern_id` cross-references between good/bad examples _(Done 7 Feb 2026)_

### Validation

- [x] Reduce YAML validation warnings to 0 _(Done 6 Feb 2026 — was 44, now 0)_
- [x] JSON Schema for YAML files _(Done 6 Feb 2026 — `practices/schema/practice.schema.json`)_
- [x] Pre-commit hook for practice validation _(Done 6 Feb 2026 — `.pre-commit-config.yaml`)_
- [x] CI pipeline integration _(Done 6 Feb 2026 — `.github/workflows/bpl-ci.yml`)_

### Quality

- [x] Fix duplicate `[BEST_PRACTICES]` header in CLI output _(Done 6 Feb 2026)_
- [x] Add `__main__.py` for `python -m.codetrellis` support _(Done 6 Feb 2026)_

## Phase 3: Intelligence (v1.4) 🔄 IN PROGRESS

### Token Optimization ✅ COMPLETE

- [x] Actual tokenizer integration (tiktoken) _(Done 7 Feb 2026 — uses cl100k_base encoding with char/4 fallback)_
- [x] Dynamic format selection based on remaining token budget _(Done 7 Feb 2026 — `OutputFormat.select_format_for_budget()`)_
- [x] Practice compression levels (progressive detail) _(Done 7 Feb 2026 — 4 tiers: minimal, compact, prompt, full)_

### Smarter Selection (Future)

- [ ] Usage-weighted scoring (track which practices users apply)
- [ ] Project-history-aware selection (remember past scans)
- [ ] Conflict detection between practices
- [ ] Practice dependency graph (practice A requires B)

## Phase 4: Ecosystem (v2.0)

### Custom Practices

- [ ] User-defined practice YAML files (`.codetrellis/practices/`)
- [ ] Organization-level practice libraries
- [ ] Practice inheritance/overrides

### Analytics

- [ ] Practice adoption metrics dashboard
- [ ] Most/least applied practices report
- [ ] Team-level practice compliance scoring

### Integration

- [ ] VS Code extension: inline practice suggestions
- [ ] PR review integration: suggest practices for changed code
- [ ] IDE quick-fix integration via practice examples

## Non-Goals

These are explicitly out of scope:

- **ML-based selection**: Rule-based is more predictable and debuggable
- **Real-time practice updates**: Practices are versioned with CodeTrellis releases
- **Language-specific AST analysis**: CodeTrellis scanner handles this; BPL only consumes context
