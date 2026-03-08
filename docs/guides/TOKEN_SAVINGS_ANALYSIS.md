# CodeTrellis Token Savings Analysis — Cache Optimization (A5.1)

## Executive Summary

CodeTrellis A5.1 introduces **prompt cache optimization** that reorders matrix sections by stability to maximize LLM prompt caching (Anthropic `cache_control`, Google `cached_content`). This document analyzes real-world token savings across 7 production-scale projects.

**Key Finding**: Projects with larger static/structural sections (dependencies, schemas, best practices) see **7–16% cost savings** on repeated prompts. Projects dominated by semantic code sections see modest gains (~1–3%) from reordering alone but benefit from cache break placement for future cache-aware API calls.

---

## How It Works

### Section Stability Classification

The cache optimizer classifies every matrix section into 4 stability tiers:

| Tier | Description | Change Frequency | Examples |
| --- | --- | --- | --- |
| **STATIC** | Never changes between scans | Rarely | `AI_INSTRUCTION`, `PROJECT`, `RUNBOOK`, `BEST_PRACTICES`, `BUSINESS_DOMAIN` |
| **STRUCTURAL** | Changes only with major refactors | Infrequently | `OVERVIEW`, `PROJECT_PROFILE`, `DATABASE`, `*_DEPENDENCIES`, `SUB_PROJECTS` |
| **SEMANTIC** | Changes with code modifications | Frequently | `*_TYPES`, `*_API`, `*_FUNCTIONS`, `HOOKS`, `MIDDLEWARE`, `ROUTES` |
| **VOLATILE** | Changes every scan | Always | `PROGRESS`, `ACTIONABLE_ITEMS`, `ERROR_HANDLING` |

### Optimization Strategy

1. **Reorder sections**: Static → Structural → Semantic → Volatile
2. **Insert cache breaks**: `# [CACHE_BREAK]` markers at tier boundaries
3. **Generate Anthropic messages**: Split prompt into cacheable/non-cacheable blocks with `cache_control: {"type": "ephemeral"}`

The LLM provider can then cache the prefix (static + structural) across requests, only re-processing semantic + volatile sections when they change.

---

## Real-World Analysis

### 7-Project Benchmark

| Project | Total Tokens | Static | Structural | Semantic | Volatile | Cacheable % | Cost Savings (10 req) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Cal.com** (302K chars) | 75,352 | 6,672 | 10,848 | 47,774 | 9,994 | **23.3%** | **16.3%** |
| **Ever Gauzy** (513K chars) | 128,283 | 5,621 | 9,385 | 101,289 | 11,946 | **11.7%** | **7.0%** |
| **Apollo Client** (638K chars) | 159,416 | 2,198 | 5,302 | 142,528 | 9,326 | **4.7%** | **1.3%** |
| **Hatchet** (674K chars) | 168,311 | 1,095 | 4,378 | 146,165 | 16,605 | **3.3%** | **0.1%** |
| **CodeTrellis** (242K chars) | 60,483 | 485 | 1,516 | 58,077 | 362 | **3.3%** | **0.2%** |
| **Supabase** (746K chars) | 186,418 | 2,761 | 3,142 | 174,166 | 6,312 | **3.2%** | **0.1%** |
| **Gitea** (655K chars) | 163,424 | 1,406 | 1,614 | 147,911 | 12,455 | **1.8%** | —* |

*Gitea: Overhead from cache break markers slightly exceeds savings at this cacheable ratio.

### Section Distribution

```
Cal.com:       ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ (23% cacheable)
Ever Gauzy:    ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (12% cacheable)
Apollo Client: ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (5% cacheable)
Hatchet:       ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (3% cacheable)
CodeTrellis:   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (3% cacheable)
Supabase:      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (3% cacheable)
Gitea:         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (2% cacheable)

█ = static + structural (cacheable)  ░ = semantic + volatile (refreshed)
```

---

## Cost Model

### Anthropic Claude Pricing (as of 2025)

| Component | Cost per 1M tokens |
| --- | --- |
| Input tokens (no cache) | $3.00 |
| Cache write | $3.75 |
| Cache read (hit) | $0.30 |
| Output tokens | $15.00 |

### Savings Formula

For a prompt with $C$ cacheable tokens and $V$ volatile tokens, over $N$ requests:

$$\text{Uncached cost} = N \times (C + V) \times \$3.00/\text{M}$$

$$\text{Cached cost} = (C \times \$3.75/\text{M}) + ((N-1) \times C \times \$0.30/\text{M}) + (N \times V \times \$3.00/\text{M})$$

$$\text{Savings \%} = 1 - \frac{\text{Cached cost}}{\text{Uncached cost}}$$

### Break-Even Analysis

Cache write costs 25% more than normal input. The break-even point is:

$$N_{\text{break-even}} = \frac{C \times 3.75}{C \times (3.00 - 0.30)} = \frac{3.75}{2.70} \approx 1.4 \text{ requests}$$

**After just 2 requests, caching saves money.** Every additional request saves 90% on cached tokens.

### Projected Savings at Scale

| Requests | Cal.com (23% cacheable) | Ever Gauzy (12% cacheable) | Average Project (5% cacheable) |
| ---: | ---: | ---: | ---: |
| 2 | 8.5% | 4.8% | 2.0% |
| 5 | 14.5% | 8.3% | 3.5% |
| 10 | 16.3% | 9.4% | 3.9% |
| 50 | 17.5% | 10.1% | 4.3% |
| 100 | 17.7% | 10.2% | 4.3% |

---

## What Drives Higher Savings

Projects with higher cacheable ratios share these characteristics:

1. **Rich best practices** — Large `BEST_PRACTICES` section (Cal.com: 6K+ tokens)
2. **Detailed runbooks** — `RUNBOOK` with build/test/deploy commands
3. **Many dependencies** — Multiple `*_DEPENDENCIES` sections (structural tier)
4. **Database schemas** — `DATABASE` section with table definitions
5. **Sub-project structure** — Monorepo with `SUB_PROJECTS` / `SUB_PROJECTS_DETAIL`

Projects with lower cacheable ratios tend to:
- Have most content in semantic sections (types, APIs, functions)
- Be single-language projects with fewer dependency sections
- Have sparse or missing `BEST_PRACTICES` / `RUNBOOK` sections

---

## Recommendations

### For Maximum Savings

1. **Generate comprehensive best practices**: Run `codetrellis scan` with BPL enabled — the `BEST_PRACTICES` section is classified as STATIC and directly boosts cacheability
2. **Include runbook information**: Projects with `RUNBOOK` content get more static tokens
3. **Use `--cache-optimize` on every scan**: Ensure sections are always optimally ordered

### For API Integration

```bash
# Get Anthropic-formatted messages with cache_control
codetrellis cache-optimize --anthropic-messages > messages.json

# Use in API calls
python -c "
import json, anthropic
messages = json.load(open('messages.json'))
client = anthropic.Anthropic()
response = client.messages.create(
    model='claude-sonnet-4-20250514',
    max_tokens=4096,
    system=messages,
    messages=[{'role': 'user', 'content': 'Explain the project architecture'}]
)
"
```

### For Google Gemini

Use `cached_content` API with the static+structural prefix:

```python
import google.generativeai as genai

# Cache the stable prefix
cache = genai.caching.CachedContent.create(
    model="gemini-1.5-pro",
    contents=[{"parts": [{"text": static_structural_prefix}]}],
    ttl="3600s",
)
```

---

## CLI Usage

```bash
# View cache optimization stats
codetrellis cache-optimize --stats

# Optimize in-place
codetrellis cache-optimize

# Output to file
codetrellis cache-optimize --output optimized.prompt

# Get Anthropic API format
codetrellis cache-optimize --anthropic-messages

# Scan with automatic optimization
codetrellis scan . --cache-optimize
```

---

## Conclusion

Prompt cache optimization provides **meaningful cost savings** (7–17%) for projects with substantial static content (best practices, runbooks, schemas, dependencies). For code-heavy projects, savings are modest (1–4%) but the section reordering ensures optimal cache utilization whenever provider-side caching is available.

The optimization is **zero-cost to apply** — it only reorders sections and inserts markers without changing content. Every project should enable `--cache-optimize` as a default.
