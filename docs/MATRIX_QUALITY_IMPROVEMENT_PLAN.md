# Multi-Agent Plan Validation: Matrix Quality Improvements

# ======================================

# Created: 2026-03-06

# Author: CodeTrellis Team

# Project: CodeTrellis Matrix Quality — Feedback-Driven Improvements

---

# ═══════════════════════════════════════════════════════════════

# SECTION A: THE PLAN (v1.0 — Draft for Review)

# ═══════════════════════════════════════════════════════════════

## Plan Name: Matrix Section Quality Improvements v1.0

## Executive Summary

Fix 10 quality issues reported by users scanning real Angular/NestJS projects.
The matrix sections output incomplete, truncated, or structurally flat data that
prevents AI from understanding the scanned project's architecture. These fixes
improve output fidelity across **all supported frameworks**, not just Angular.

## Problem Statement

1. **TAILWIND_UTILITIES** `@apply` values are empty — shows `@apply |n=0` instead of actual utility classes
2. **HTTP_API** shows only method + "url" — missing actual endpoint paths and response types
3. **No ANGULAR_GUARDS / ANGULAR_PIPES / ANGULAR_DIRECTIVES** sections — scattered across other sections
4. **BUSINESS_DOMAIN** truncated — entities cut off with `...`
5. **DATA_FLOWS** nearly empty — just `primary-pattern:Request-Response`
6. **No FORMS / REACTIVE_FORMS** section — despite extensive reactive form usage
7. **COMPONENTS** listed flat — no hierarchy/nesting information
8. **INTERFACES** section 39KB and overwhelming — no domain grouping
9. **Section naming inconsistency** — `ANGULAR_SERVICES` exists but no `ANGULAR_GUARDS`/etc
10. **PROGRESS** section lacks detail — doesn't show what placeholders are

## Proposed Solution

Fix each issue in `compressor.py` (section formatting), `scanner.py` (data model),
and relevant extractors. All changes are backward-compatible.

## Implementation Phases

### Phase 1: Data Fidelity Fixes — Immediate (compressor.py only)

Fix output formatting in existing compress methods where data exists but isn't rendered.

- Fix 1: TAILWIND_UTILITIES @apply values
- Fix 2: HTTP_API endpoint paths
- Fix 4: BUSINESS_DOMAIN truncation limits
- Fix 8: INTERFACES domain grouping
- Fix 10: PROGRESS placeholder details

### Phase 2: New Sections — Scanner + Compressor

Add new fields to ProjectMatrix and corresponding compress methods.

- Fix 3/9: ANGULAR_GUARDS, ANGULAR_PIPES, ANGULAR_DIRECTIVES
- Fix 6: ANGULAR_FORMS / REACTIVE_FORMS
- Fix 7: Component hierarchy in COMPONENTS

### Phase 3: Deep Enrichment — Extractors

Improve extraction quality for data flow chains and form structures.

- Fix 5: DATA_FLOWS enrichment with actual flow chains

## Success Metrics

| Metric                        | Target                                          | How Measured                         |
| ----------------------------- | ----------------------------------------------- | ------------------------------------ |
| @apply shows actual classes   | 100% of @apply entries show class list          | Scan Tailwind project, verify output |
| HTTP_API shows full paths     | All endpoints show URL pattern + response type  | Scan Angular project, verify output  |
| Angular sections complete     | Guards/Pipes/Directives have dedicated sections | Section count check                  |
| BUSINESS_DOMAIN not truncated | Full entity list visible                        | Character count check                |
| DATA_FLOWS shows chains       | ≥3 flow chains per project                      | Scan Angular project                 |
| INTERFACES grouped            | Groups visible in output                        | Visual inspection                    |
| Component hierarchy           | Parent→Child relationships shown                | Scan Angular project                 |

## Risks

| Risk                   | Impact                                     | Mitigation               |
| ---------------------- | ------------------------------------------ | ------------------------ |
| Token budget increase  | More verbose sections = higher token usage | Apply tier-based limits  |
| Backward compatibility | Existing matrix consumers break            | Additive changes only    |
| Regex complexity       | New extractors may have false positives    | Unit tests per extractor |

---

# ═══════════════════════════════════════════════════════════════

# SECTION B: ROUND 1 — INDEPENDENT AGENT REVIEWS

# ═══════════════════════════════════════════════════════════════

## 🔴 AGENT 1: THE SKEPTIC

### Verdict: CONDITIONAL PASS

### ✅ Agreements

- Phase 1 fixes are purely formatting — low risk, high reward
- The feedback is from real users scanning real projects — not theoretical

### ⚠️ Concerns

- Phase 2 adds new fields to ProjectMatrix — dataclass changes ripple to `to_dict()`, JSON serialization, lockfile compat
- "Fix all supported frameworks" scope creep — should focus on Angular first, generalize later

### ❌ Won't Work

- DATA_FLOWS enrichment (Fix 5) requires semantic understanding of component→service→API chains that regex can't do reliably

### 💡 Alternatives

- For DATA_FLOWS: infer chains from import graphs + HTTP call analysis rather than semantic parsing
- Implement Phase 1 first, ship, then iterate on Phase 2/3

## 🟢 AGENT 2: THE ARCHITECT

### Verdict: PASS

### ✅ Agreements

- Consistent naming (ANGULAR_GUARDS matching ANGULAR_SERVICES) is critical for API consumers
- Component hierarchy adds genuine architectural insight
- INTERFACES grouping reduces cognitive load

### ⚠️ Concerns

- Component hierarchy detection needs a clear algorithm — template analysis or import-based?
- INTERFACES grouping heuristic (by domain) may not work for all projects

### 💡 Alternatives

- Component hierarchy: use template `<app-*>` tag analysis + import graph
- INTERFACES grouping: group by file directory (which maps to domain in well-structured projects)

## 🔵 AGENT 3: THE USER ADVOCATE

### Verdict: PASS

### ✅ Agreements

- Every fix directly addresses user-reported pain points
- Zero configuration — improvements should be automatic

### ⚠️ Concerns

- 39KB INTERFACES section becoming even larger with grouping headers
- Users won't know these fixes exist without changelog

### 💡 Alternatives

- Add `# Summary: 142 interfaces across 6 domains` header before detailed listing
- COMPACT tier should show summary-only, PROMPT/FULL show details

## 🟡 AGENT 4: THE BUSINESS STRATEGIST

### Verdict: PASS

### ✅ Agreements

- Matrix quality is the core product differentiator
- Every fix improves AI code generation accuracy for downstream users

### 💡 Alternatives

- Track "section completeness score" as a quality metric in \_metadata.json

## 🟣 AGENT 5: THE DOMAIN EXPERT (CodeTrellis Matrix Expert)

### Verdict: CONDITIONAL PASS

### ✅ Agreements

- `_compress_tailwind_utilities` already extracts `classes` from apply_directives — the bug is likely in how scanner populates `tailwind_apply_directives[].classes`
- HTTP_API extractor already has `url`, `responseType`, `requestBodyType` in `HttpApiCall.to_codetrellis_format()` — the compressor just doesn't use all fields

### ⚠️ Concerns

- Scanner populates `tailwind_apply_directives` from `TailwindUtilityExtractor._extract_apply_directives()` which correctly extracts utilities — need to verify the scanner→matrix pipeline
- Angular guards/pipes/directives are already extracted by `semantic_extractor.py` and `controller_extractor.py` into the MIDDLEWARE section — need to split, not re-extract

### ❌ Won't Work

- Creating brand new extractors for Angular guards — the data is already in `nestjs_guards`, `nestjs_pipes` which are shared with NestJS. Need framework-aware routing.

### 💡 Alternatives

- For Angular: detect Angular vs NestJS and route guard/pipe/interceptor data to framework-specific section names
- `_compress_http_api` already exists — just fix the format string to include URL and responseType

## 🟠 AGENT 6: THE SECURITY & RELIABILITY AGENT

### Verdict: PASS

### ✅ Agreements

- No security implications — all changes are output formatting
- Backward compatible — additive fields only

### ⚠️ Concerns

- Token budget: more verbose output could exceed LLM context windows
- Must respect COMPACT tier limits everywhere

### 💡 Alternatives

- Add token estimate per section to \_metadata.json for monitoring

---

# ROUND 1 SUMMARY TABLE

| Agent            | Verdict          | Key Demand                     |
| ---------------- | ---------------- | ------------------------------ |
| 🔴 Skeptic       | CONDITIONAL PASS | Ship Phase 1 first, iterate    |
| 🟢 Architect     | PASS             | Clear hierarchy algorithm      |
| 🔵 User Advocate | PASS             | Summary-first for INTERFACES   |
| 🟡 Strategist    | PASS             | Track quality metrics          |
| 🟣 Domain Expert | CONDITIONAL PASS | Fix pipeline, don't re-extract |
| 🟠 Security      | PASS             | Respect token budgets          |

### Unanimous Agreements (LOCKED ✅)

1. Phase 1 formatting fixes are safe and should ship immediately
2. HTTP_API already has the data — just fix the format string
3. All changes must respect COMPACT/PROMPT/FULL tier limits

### Disagreements (FLAGGED for Round 2)

1. DATA_FLOWS: regex vs import-graph approach
2. Angular sections: new extractors vs framework-aware routing

---

# ═══════════════════════════════════════════════════════════════

# SECTION C: ROUND 2 — RESOLUTION

# ═══════════════════════════════════════════════════════════════

## DEBATE 1: DATA_FLOWS approach

### 🤝 RESOLUTION: Infer chains from existing HTTP_API + service injection + WebSocket data.

Don't do semantic parsing. Use what we already have.

## DEBATE 2: Angular guard/pipe/directive sections

### 🤝 RESOLUTION: Add angular_guards, angular_pipes, angular_directives fields to ProjectMatrix.

Populate from existing semantic_extractor patterns. Add framework detection to route
@UseGuards → ANGULAR_GUARDS (Angular) or NESTJS_GUARDS (NestJS).

---

# ═══════════════════════════════════════════════════════════════

# SECTION D: THE PLAN (v2.0 — FINAL VALIDATED)

# ═══════════════════════════════════════════════════════════════

## Implementation: All 10 fixes in compressor.py + scanner.py

### Fix 1: TAILWIND_UTILITIES @apply — show actual classes ✅

**File:** `compressor.py:_compress_tailwind_utilities`
**Change:** The format `{sel}|@apply {cls_str}|n={count}` already includes `cls_str`. The issue is
`classes` key might be empty from scanner. Fix: also try `utilities` key (from TailwindApplyInfo).

### Fix 2: HTTP_API — show full endpoints ✅

**File:** `compressor.py:_compress_http_api`
**Change:** Show each endpoint on its own line: `  GET /api/properties/:id → Property[]`

### Fix 3+9: Angular Guard/Pipe/Directive sections ✅

**Files:** `scanner.py` (add fields), `compressor.py` (add sections)
**Change:** Add `angular_guards`, `angular_pipes`, `angular_directives` to ProjectMatrix.
Add `[ANGULAR_GUARDS]`, `[ANGULAR_PIPES]`, `[ANGULAR_DIRECTIVES]` compress methods.

### Fix 4: BUSINESS_DOMAIN no truncation ✅

**File:** `compressor.py:_compress_business_domain`
**Change:** Increase entity limits. PROMPT tier: 20 entities. FULL: unlimited.
Remove `[:5]` limit on supporting entities.

### Fix 5: DATA_FLOWS enrichment ✅

**File:** `compressor.py:_compress_data_flows`
**Change:** Infer flow chains from HTTP_API + angular_services + websocket data.
Generate synthetic flows when `dataFlows` is empty.

### Fix 6: ANGULAR_FORMS section ✅

**Files:** `scanner.py`, `compressor.py`
**Change:** Add `angular_forms` field. Extract from FormBuilder/FormGroup/FormControl patterns.
Add `[ANGULAR_FORMS]` section with form structure, validators, form-builder patterns.

### Fix 7: Component hierarchy ✅

**File:** `compressor.py:_compress_component`
**Change:** Show children components. Format: `ComponentName|@in:x,y|children:ChildA,ChildB`

### Fix 8: INTERFACES domain grouping ✅

**File:** `compressor.py` compress method for INTERFACES
**Change:** Add summary header, group by directory/domain prefix.

### Fix 10: PROGRESS enrichment ✅

**File:** `cli.py:_generate_progress_section`
**Change:** List actual placeholder locations and incomplete areas.

## Validation Summary

| Agent            | Final Verdict |
| ---------------- | ------------- |
| 🔴 Skeptic       | PASS          |
| 🟢 Architect     | PASS          |
| 🔵 User Advocate | PASS          |
| 🟡 Strategist    | PASS          |
| 🟣 Domain Expert | PASS          |
| 🟠 Security      | PASS          |

**Consensus: 6/6 agents approve.**
