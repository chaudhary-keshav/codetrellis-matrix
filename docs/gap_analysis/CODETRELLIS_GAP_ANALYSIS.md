# CodeTrellis Gap Analysis — Complete Before & After Report

> **Date:** 2026-02-07
> **CodeTrellis Version:** 4.4.0 (Phase A–E remediation applied & CLI-tested)
> **Repository:** ns-brain (build-for-test)
> **Branch:** Simulator-testing-phase-2
> **Analyst Level:** Principal Solution Architect
> **Phase A Status:** ✅ Complete & Verified — G-01, G-02, G-03, G-04, G-05, G-10, G-11, G-12, G-21 resolved + 6 bugs fixed during testing + `[AI_INSTRUCTION]` prompt header added
> **Phase B Status:** ✅ Complete & Verified — G-06, G-07, G-08, G-09, G-19, G-20 resolved (Dedup Engine + Service Attribution + SERVICE_MAP) + 3 issues fixed during re-verification (FastAPI endpoint dedup, Python type/API service prefix)
> **Phase C Status:** ✅ Complete & Verified — G-13, G-14, G-15, G-18, G-22, G-23 resolved (Docker/Terraform/CI-CD/NestJS Extractors + IMPLEMENTATION_LOGIC smart truncation) + 1 bug fixed during testing (Terraform provider format)
> **Phase D Status:** ✅ Complete & Verified — WS-8 Public Repository Validation Framework implemented (.codetrellis validate-repos` CLI, validation_runner.sh, quality_scorer.py, analyze_results.py, 60-repo repos.txt) + CLI-verified on calcom/cal.com (1,073 lines, 21s, PASS)
> **Phase E Status:** ✅ Complete & Verified — Self-scan quality fixes: pattern contamination (G-05 deepened), regex leakage in ACTIONABLE_ITEMS, domain misdetection (G-12 deepened) with weighted scoring, G-16 Makefile enhancement with .PHONY/variables/includes/prerequisites — CLI-verified on CodeTrellis self-scan + trading-ui regression test

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scan Coverage — Before vs After](#2-scan-coverage--before-vs-after)
3. [Per-Project Analysis](#3-per-project-analysis)
   - 3.1 [CodeTrellis Tool (Self-Scan)](#31.codetrellis-tool-self-scan)
   - 3.2 [Trading UI (Angular)](#32-trading-ui-angular)
   - 3.3 [Trading Platform (NestJS)](#33-trading-platform-nestjs)
   - 3.4 [Sparse Reasoning AI (Python/ML)](#34-sparse-reasoning-ai-pythonml)
   - 3.5 [Trading AI (Python/Flask) — NEW SCAN](#35-trading-ai-pythonflask--new-scan)
   - 3.6 [AI Service (Python/FastAPI) — NEW SCAN](#36-ai-service-pythonfastapi--new-scan)
   - 3.7 [API Gateway (NestJS) — NEW SCAN](#37-api-gateway-nestjs--new-scan)
   - 3.8 [NexuShield (NestJS) — NEW SCAN](#38-nexushield-nestjs--new-scan)
   - 3.9 [NexuTalk (NestJS) — NEW SCAN](#39-nexutalk-nestjs--new-scan)
   - 3.10 [NexuEdge (NestJS) — NEW SCAN](#310-nexuedge-nestjs--new-scan)
   - 3.11 [NexuChat UI (Angular) — NEW SCAN](#311-nexuchat-ui-angular--new-scan)
   - 3.12 [NexuCore, NexuScan, NexuSight — NEW SCAN (Skeleton)](#312-nexucore-nexuscan-nexusight--new-scan-skeleton)
   - 3.13 [Kimi K2 Local — NEW SCAN](#313-kimi-k2-local--new-scan)
4. [Cross-Project Context Gaps](#4-cross-project-context-gaps)
5. [CodeTrellis Tool Deficiencies (Extractor-Level)](#5.codetrellis-tool-deficiencies-extractor-level)
6. [Quantitative Gap Summary — Before vs After](#6-quantitative-gap-summary--before-vs-after)
7. [Priority Remediation Roadmap](#7-priority-remediation-roadmap)
8. [Root-Level Scan Findings (Phase 3 → Phase 5)](#8-root-level-scan-findings-phase-3--phase-5)

---

> **📋 Phase 3 Update:** A root-level monorepo scan was performed and analyzed.
> **📋 Phase 5 Update:** Root `--optimal` confirmed working — produces [LOGIC] tier, 18,728 lines.
> Full comparison: [`docs/CodeTrellis_ROOT_VS_INDIVIDUAL_ANALYSIS.md`](./CodeTrellis_ROOT_VS_INDIVIDUAL_ANALYSIS.md)

---

## 1. Executive Summary

### What Was Done

| Phase                        | Action                                  | Result                                                                                                                                                                      |
| ---------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 1 (Previous)**       | Analyzed 4 existing matrix.prompt files | Found gaps in CodeTrellis self-scan, sparse-ai duplication, missing projects                                                                                                       |
| **Phase 2 (Current)**        | Ran CodeTrellis on **11 uncovered projects**   | Generated new matrix files; total coverage now **15 projects**                                                                                                              |
| **Phase 2 Analysis**         | Read & compared all 15 matrix files     | Identified persistent CodeTrellis tool gaps, new findings                                                                                                                          |
| **Phase 3 (Root Scan)**      | Ran CodeTrellis at **monorepo root level**     | 19,502 lines [FULL] tier; captures cross-service gRPC map but PROGRESS contaminated                                                                                         |
| **Phase 5 (Root --optimal)** | User ran `--optimal` on root            | **18,728 lines [LOGIC] tier**; 15 BPL practices, 11,857 functions — corrects Phase 4's "hangs" finding                                                                      |
| **Phase A (Implementation)** | Implemented 9 gap fixes across 7 files  | RunbookExtractor, filtering, bug fixes for ACTIONABLE_ITEMS/type/domain                                                                                                     |
| **Phase A (Testing)**        | CLI-tested on ai-service + nexu-shield  | Found 6 additional bugs, all fixed; verified [RUNBOOK], [ACTIONABLE_ITEMS], domain detection, [AI_INSTRUCTION] prompt                                                       |
| **Phase B (Implementation)** | Implemented 6 gap fixes across 2 files  | Dedup engine (gRPC/Flask/Python types), service attribution, `[SERVICE_MAP]` section                                                                                        |
| **Phase B (Testing)**        | CLI-tested on ns-brain monorepo root    | 3 issues found & fixed (FastAPI dedup, Python type/API prefix); gRPC 24→14, Flask 213→101, FastAPI deduped, 669 Python types + 3086 entities tagged, 10 service connections |

### Key Findings After Full Scan

| Finding                                      | Severity    | Detail                                                                                                                                                                                                                        |
| -------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CodeTrellis self-scan still polluted**            | 🔴 Critical | Test fixture data from `test_on_trading_ui.py` contaminates all sections                                                                                                                                                      |
| **3 services are skeleton-only**             | 🟡 Medium   | nexu-core, nexu-scan, nexu-sight — only README captured (24 lines each)                                                                                                                                                       |
| **Business domain misdetection**             | 🟡 Medium   | nexu-shield detected as "Trading/Finance" instead of "Security/Auth"                                                                                                                                                          |
| **Trading-ai has massive type duplication**  | ✅ Fixed    | ~~`TradingSignal` defined 5x, `TFTPrediction` 4x, API routes duplicated 2x~~ Phase B dedup: Python types 902→837, Flask routes 213→101, FastAPI dedup (5× `GET:/` → 1×), 669 Python types + all endpoints with service prefix |
| **Zero cross-service communication mapping** | ✅ Fixed    | ~~No matrix captures the inter-service gRPC/WebSocket dependency graph~~ Phase B `[SERVICE_MAP]` maps 10 gRPC connections                                                                                                     |
| **Infrastructure completely absent**         | 🔴 Critical | 11 Terraform files, 10+ Dockerfiles, docker-compose = 0% coverage                                                                                                                                                             |
| **Root scan: PROGRESS contamination**        | ✅ Fixed    | ~~61,645 TODOs from node_modules~~ Path-segment filtering applied (G-04)                                                                                                                                                      |
| **Root scan: correct domain detection**      | 🟢 Positive | Trading/Finance correctly identified at root (vs 20% accuracy individually)                                                                                                                                                   |
| **Root scan: 24 gRPC sections captured**     | ✅ Improved | ~~24 raw sections with duplicates~~ Phase B dedup: 14 unique services with `defined-in:` / `consumed-by:` attribution                                                                                                         |
| **Root `--optimal` WORKS**                   | 🟢 Positive | Phase 5 confirmed: 18,728 lines [LOGIC] tier with 15 BPL practices                                                                                                                                                            |
| **Proto definitions not linked**             | ✅ Fixed    | ~~46 RPC methods across 3 proto files — captured per-service but not unified~~ Phase B: `defined-in:` + `consumed-by:` per gRPC service                                                                                       |
| **Phase A: 6 bugs found in CLI testing**     | ✅ Fixed    | type=monorepo hardcoded, progress/actionable conflict, wrong dict keys, missing shell scripts, missing AI_ML/DEVTOOLS domains                                                                                                 |
| **Phase A: [AI_INSTRUCTION] prompt added**   | 🟢 Positive | Every matrix.prompt now starts with instructions for AI to read full context                                                                                                                                                  |

---

## 2. Scan Coverage — Before vs After

### Projects Scanned

| Project             | Category          | Before (Phase 1) | After (Phase 2) | Matrix Lines |  Tokens |
| ------------------- | ----------------- | :--------------: | :-------------: | -----------: | ------: |
| CodeTrellis Tool           | Python (Dev Tool) |    ✅ Existed    |   ✅ Existed    |          905 |  ~5,500 |
| Trading UI          | Angular 20        |    ✅ Existed    |   ✅ Existed    |          677 |  ~4,800 |
| Trading Platform    | NestJS 10         |    ✅ Existed    |   ✅ Existed    |          870 |  ~6,200 |
| Sparse Reasoning AI | Python/ML         |    ✅ Existed    |   ✅ Existed    |        3,167 | ~18,000 |
| **Trading AI**      | Python/Flask      |    ❌ Missing    |   ✅ **NEW**    |          239 |  ~4,527 |
| **AI Service**      | Python/FastAPI    |    ❌ Missing    |   ✅ **NEW**    |          131 |  ~1,712 |
| **API Gateway**     | NestJS 10         |    ❌ Missing    |   ✅ **NEW**    |          163 |  ~2,003 |
| **NexuShield**      | NestJS 10         |    ❌ Missing    |   ✅ **NEW**    |          131 |  ~2,003 |
| **NexuTalk**        | NestJS 10         |    ❌ Missing    |   ✅ **NEW**    |          142 |  ~2,823 |
| **NexuEdge**        | NestJS 10         |    ❌ Missing    |   ✅ **NEW**    |           90 |  ~1,030 |
| **NexuChat UI**     | Angular 20        |    ❌ Missing    |   ✅ **NEW**    |           68 |    ~651 |
| **NexuCore**        | NestJS (stub)     |    ❌ Missing    |   ✅ **NEW**    |           24 |    ~153 |
| **NexuScan**        | NestJS (stub)     |    ❌ Missing    |   ✅ **NEW**    |           24 |    ~153 |
| **NexuSight**       | NestJS (stub)     |    ❌ Missing    |   ✅ **NEW**    |           24 |    ~153 |
| **Kimi K2 Local**   | Python            |    ❌ Missing    |   ✅ **NEW**    |           24 |    ~160 |

### File Coverage

| Metric                 |   Before |    After |      Delta |
| ---------------------- | -------: | -------: | ---------: |
| Projects scanned       |        4 |       15 |  **+275%** |
| Matrix files generated |        4 |       15 |    +11 new |
| Total matrix lines     |   ~5,619 |   ~6,679 |     +1,060 |
| Source files covered   |     ~900 |  ~1,232+ |       +332 |
| **Estimated coverage** | **~50%** | **~88%** | **+38 pp** |

### What's STILL Missing (Not Scannable by CodeTrellis)

| Asset                    |  Files | Why Not Covered                                            |
| ------------------------ | -----: | ---------------------------------------------------------- |
| Terraform infrastructure |     11 | No `.tf` parser in CodeTrellis                                    |
| Proto definitions (root) |      4 | Proto parser exists but not run at root level              |
| Docker/docker-compose    |    10+ | ✅ Partially covered by RunbookExtractor (G-01)            |
| Shell scripts            |     40 | ✅ Root-level scripts extracted by RunbookExtractor (G-01) |
| Documentation (docs/)    |    216 | Markdown partially captured via README only                |
| Fine-tuning data         | 41,265 | Data files, not source code                                |

---

## 3. Per-Project Analysis

### 3.1 CodeTrellis Tool (Self-Scan)

**Matrix:** `tools.codetrellis/.codetrellis/cache/4.1.2.codetrellis/matrix.prompt` (905 lines)

#### ✅ What CodeTrellis Captured Correctly

- `[PYTHON_TYPES]`: 120+ real dataclasses, Pydantic models, Protocols, Enums — accurate
- `[PYTHON_API]`: No APIs (correct — CodeTrellis is a CLI tool, not a server)
- `[PYTHON_FUNCTIONS]`: Some functions captured

#### ~~🔴 Critical Issues — Test Fixture Contamination~~ ✅ RESOLVED (Phase E)

> **Phase E (2026-02-10):** All contamination issues below have been fixed. See Phase E Implementation Summary in CodeTrellis_REMEDIATION_PLAN.md.

The matrix was previously **polluted by test fixture data** from `tests/test_on_trading_ui.py` and `lsp/extract-types.ts`. Phase E fixes:

| Issue                                            | Before Phase E                                                                   | After Phase E                            |
| ------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------- |
| Angular pattern contamination from test fixtures | `stack:Python Library,Lazy Loading,Signal Store,OnPush CD,Standalone Components` | `stack:Python Library` ✅                |
| BLOCKER regex self-match in ACTIONABLE_ITEMS     | Contained `BLOCKER\|...\s*(.+?)(?:\` regex garbage                               | Clean: 3 TODO, 2 PLACEHOLDER, 1 FIXME ✅ |
| Business domain misdetection                     | `domain:Trading/Finance`                                                         | `domain:Developer Tools` ✅              |

**Fixes applied:**

1. `architecture_extractor.py` — `_detect_patterns()` now uses `PATTERN_IGNORE_SEGMENTS` + `_is_pattern_scan_ignored()` to skip `tests/`, `fixtures/`, `lsp/`, `scripts/` directories during `.ts` file scanning
2. `progress_extractor.py` — `_is_inside_string_literal()` guard prevents regex pattern definitions from being detected as real progress markers
3. `business_domain_extractor.py` — `_detect_domain_category()` now uses 3-pool weighted scoring (code artifacts: 3×, file system: 2×, README: 1×) and skips `practices/`, `bpl/`, `data/` directories

#### 🟡 Missing Context (Real CodeTrellis Code Not Captured)

| Missing Item             | Files                                                  | Impact                             |
| ------------------------ | ------------------------------------------------------ | ---------------------------------- |
| 20 TypeScript extractors | `extractors/*.py`                                      | Core scanning logic invisible      |
| 18 Python extractors     | `extractors/python/*.py`                               | Python analysis logic invisible    |
| Core modules             | `scanner.py`, `compressor.py`, `cli.py` (1674 LOC)     | Architecture invisible             |
| Plugin system            | `base.py`, `builtin.py`, `discovery.py`, `registry.py` | Extensibility invisible            |
| AST Parser               | `ast_parser.py`                                        | Deep analysis capability invisible |
| LSP Client               | `lsp_client.py`                                        | 99% accuracy mode invisible        |
| BPL System               | Best Practices Library (407+ practices)                | Quality feature invisible          |
| Streaming/Parallel       | `streaming.py`, `parallel.py`                          | Performance features invisible     |

#### Root Cause

CodeTrellis scans ALL Python files including test files. Test fixtures containing Angular code snippets are parsed by TypeScript extractors (which run on string content within Python files).

#### Recommended Fix

```
Option A: Add test exclusion to .codetrellis/config.json:
  { "exclude": ["tests/", "test_*"] }

Option B: Filter at extractor level — skip TypeScript extraction on .py files
```

---

### 3.2 Trading UI (Angular)

**Matrix:** `ai/trading-ui/.codetrellis/cache/4.1.2/trading-ui/matrix.prompt` (677 lines)

#### ✅ Well Captured

| Section          | Count | Quality                                 |
| ---------------- | ----: | --------------------------------------- |
| Components       |    82 | ✅ Complete with inputs/outputs/signals |
| Interfaces       |   90+ | ✅ Full property definitions            |
| Routes           |    38 | ✅ With guards, lazy loading            |
| Signal Stores    |    10 | ✅ With state/computed/methods          |
| Services         |     4 | ✅ With injection & methods             |
| WebSocket Events |    51 | ✅ Emit/listen pairs                    |
| HTTP API         |   45+ | ✅ With base URLs                       |

#### 🟡 Still Missing After Scan

| Missing Item          | Reason                                                  | Impact                        |
| --------------------- | ------------------------------------------------------- | ----------------------------- |
| Guard implementations | CodeTrellis extracts guard _usage_ in routes, not guard _code_ | Can't understand auth logic   |
| Interceptors          | No interceptor extractor                                | HTTP middleware invisible     |
| Pipes                 | No pipe extractor                                       | Data transformation invisible |
| `shared/` utilities   | Files exist but no utility extractor                    | Shared logic invisible        |
| Environment configs   | `environment.ts` not parsed                             | Runtime config invisible      |
| Test coverage info    | No test file analyzer                                   | Quality metrics absent        |
| Animation definitions | No animation extractor                                  | UX behavior invisible         |

---

### 3.3 Trading Platform (NestJS)

**Matrix:** `ai/trading-platform/.codetrellis/cache/4.1.2/trading-platform/matrix.prompt` (870 lines)

#### ✅ Well Captured

| Section            | Count | Quality                      |
| ------------------ | ----: | ---------------------------- |
| Schemas (Mongoose) |   70+ | ✅ With field types, indexes |
| Enums              |  100+ | ✅ Complete values           |
| DTOs               |   65+ | ✅ With decorators           |
| Controllers        |    48 | ✅ Routes with HTTP methods  |
| gRPC Services      |     7 | ✅ Methods listed            |
| Interfaces         |  100+ | ✅ Props and methods         |

#### 🟡 Still Missing After Scan

| Missing Item                   | Reason                             | Impact                           |
| ------------------------------ | ---------------------------------- | -------------------------------- |
| NestJS Module dependency graph | No module extractor                | Can't see DI container structure |
| Middleware                     | Not extracted                      | Request pipeline invisible       |
| Guards (implementations)       | Only usage in routes, not code     | Auth flow invisible              |
| WebSocket Gateway events       | Only partial — no event names      | Real-time comms incomplete       |
| Cron/Scheduler jobs            | `@Cron()` decorators not extracted | Automated tasks invisible        |
| Database connections           | MongoDB/Redis connection strings   | Infra config invisible           |
| `.env.example`                 | Not parsed                         | Required env vars invisible      |
| Database indexes               | Only partial in schemas            | Query optimization invisible     |
| Pipes (validation)             | Not extracted                      | Input validation invisible       |

---

### 3.4 Sparse Reasoning AI (Python/ML)

**Matrix:** `ai/sparse-reasoning-ai/.codetrellis/cache/4.1.2/sparse-reasoning-ai/matrix.prompt` (3,167 lines)

#### ✅ Well Captured

| Section       |                          Count | Quality                   |
| ------------- | -----------------------------: | ------------------------- |
| Python Types  |               120+ dataclasses | ✅ But heavily duplicated |
| API Endpoints | Multiple Flask/FastAPI servers | ✅                        |
| Functions     |                      Extensive | ✅ With decorators        |

#### 🔴 Critical Issue — Type Duplication

The same dataclass appears multiple times because it's defined in different files:

| Dataclass       | Occurrences |   Should Be   |
| --------------- | :---------: | :-----------: |
| `TradingSignal` |      5      | 1 (canonical) |
| `TFTPrediction` |      4      |       1       |
| `Position`      |      3      |       1       |
| `MarketData`    |      3      |       1       |
| `LLMAnalysis`   |      2      |       1       |
| `RegimeInfo`    |      2      |       1       |

**Impact:** 3,167 lines could be reduced to ~1,800 with deduplication — saving ~7,000 tokens per injection.

#### 🟡 Still Missing

| Missing Item                 | Reason                                           | Impact                          |
| ---------------------------- | ------------------------------------------------ | ------------------------------- |
| Neural network architectures | No PyTorch model extractor                       | ML model structure invisible    |
| Training pipelines           | Training loops not extracted as functions        | Can't understand training flow  |
| Evaluation benchmarks        | HumanEval/MBPP results not in matrix             | Model quality invisible         |
| gRPC service definitions     | Server endpoints not captured                    | Service communication invisible |
| VS Code extension            | `vscode-extension/` directory completely missing | IDE integration invisible       |
| Data pipeline                | Data loading/preprocessing not structured        | ETL flow invisible              |

---

### 3.5 Trading AI (Python/Flask) — NEW SCAN

**Matrix:** `ai/trading-ai/.codetrellis/cache/4.1.2/trading-ai/matrix.prompt` (239 lines)
**Files Scanned:** 62 | **Tokens:** ~4,527

#### ✅ What CodeTrellis Captured

| Section                    | Count | Quality              |
| -------------------------- | ----: | -------------------- |
| Python Types (dataclasses) |    66 | ⚠️ Heavy duplication |
| Flask API endpoints        |    92 | ⚠️ Duplicated 2x     |
| Python Functions           |    21 | ✅ With decorators   |
| Enums                      |    16 | ✅ Complete          |

#### 🔴 Issues Discovered

**1. Massive Type Duplication (Same as Sparse AI)**

| Dataclass        | Occurrences | Root Cause                                          |
| ---------------- | :---------: | --------------------------------------------------- |
| `TradingSignal`  |      5      | Same class in multiple server files                 |
| `TFTPrediction`  |      4      | Used in api_server.py, server.py, unified_server.py |
| `GrowwPosition`  |      3      | Broker integration files share types                |
| `GrowwOrder`     |      3      | Same as above                                       |
| `PaperPortfolio` |      2      | Duplicated across server files                      |

**2. API Route Duplication**

The `[PYTHON_API]` section lists 92 routes, but **~30 are duplicates** because `api_server.py` and `server.py` define identical endpoints. Unique routes: ~62.

**3. Missing Content**

| Missing Item             | Detail                                                                 |
| ------------------------ | ---------------------------------------------------------------------- |
| Broker integration logic | `groww_broker.py` (61KB!) functions not in `[PYTHON_FUNCTIONS]`        |
| ML model training        | `intraday_ml_trainer.py`, `advanced_intraday_trainer.py` not extracted |
| Strategy logic           | 9 strategy files in `strategies/` dir — none captured                  |
| Data collector           | `data_collector.py` (24KB) — collection logic invisible                |
| Configuration            | `config/` directory not parsed                                         |
| Hybrid analyzer          | `hybrid_analyzer.py` (28KB) analysis logic missing                     |

**4. Business Domain Misdetection**

Detected as "General Application" — should be **"Algorithmic Trading / Quantitative Finance"**

#### Overview Section (Good)

```
dirs:core(10),strategies(9),ml_models(4),utils(3),brokers(2),api(1)
patterns:grpc
```

This correctly identifies the project structure, but the directory contents aren't extracted.

---

### 3.6 AI Service (Python/FastAPI) — NEW SCAN

**Matrix:** `ai/ai-service/.codetrellis/cache/4.1.2/ai-service/matrix.prompt` (131 lines)
**Files Scanned:** 48 | **Tokens:** ~1,712

#### ✅ What CodeTrellis Captured

| Section           | Count | Quality                   |
| ----------------- | ----: | ------------------------- |
| Pydantic Models   |    28 | ✅ Clean, no duplication  |
| FastAPI Endpoints |    17 | ✅ With response types    |
| Functions         |    51 | ⚠️ Includes test fixtures |
| README context    |    ✅ | Good description          |

#### 🟡 Issues

| Issue                      | Detail                                                                                                           |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Test functions in matrix   | `test_rag_pipeline.py`, `test_model_manager.py` fixtures appear as project functions                             |
| Missing service classes    | `ModelManager`, `RAGPipeline`, `VectorStore`, `TenantManager`, `LLMService` — core service classes not extracted |
| Missing middleware         | FastAPI middleware/dependencies not captured                                                                     |
| Missing Ollama integration | No extraction of LLM provider configuration                                                                      |
| Missing Docker context     | `Dockerfile`, `Dockerfile.optimized` not parsed                                                                  |
| Business domain wrong      | "General Application" → should be **"AI/ML Platform - LLM Serving & RAG"**                                       |
| Completion at 50%          | 110 TODOs, 32 FIXMEs — correctly captured ✅                                                                     |

#### ✅ Good: Overview Section

```
dirs:services(11),routers(5),core(4),utils(2),models(2)
deps:fastapi
```

---

### 3.7 API Gateway (NestJS) — NEW SCAN

**Matrix:** `services/api-gateway/.codetrellis/cache/4.1.2/api-gateway/matrix.prompt` (163 lines)
**Files Scanned:** 76 | **Tokens:** ~2,003

#### ✅ Excellent Coverage

| Section            |        Count | Quality                                               |
| ------------------ | -----------: | ----------------------------------------------------- |
| Schemas (Mongoose) |            3 | ✅ Tenant, User, AnalyticsEvent                       |
| DTOs               |           28 | ✅ Comprehensive                                      |
| Controllers        |            8 | ✅ With full route mapping                            |
| gRPC Services      |            4 | ✅ AIService, TalkService, TenantService, AuthService |
| Interfaces         |           20 | ✅ Full props                                         |
| Error Handling     |     15 files | ✅ try-catch counts                                   |
| TODOs              | 5 in 4 files | ✅                                                    |

#### 🟡 Issues

| Issue                 | Detail                                                                                             |
| --------------------- | -------------------------------------------------------------------------------------------------- |
| Business domain wrong | "Trading/Finance" → should be **"API Gateway / Multi-Tenant Platform"**                            |
| Missing module graph  | NestJS `@Module()` imports/exports not captured                                                    |
| Missing guards        | `AuthGuard`, `TenantGuard` — usage visible in routes, implementation invisible                     |
| Missing interceptors  | `grpc-error.interceptor`, `grpc-auth.interceptor` — error handling counted but logic not extracted |
| Missing strategies    | `jwt.strategy.ts` — Passport strategy not extracted                                                |

#### ✅ Good: Cross-Service Visibility

The API Gateway matrix shows ALL 4 gRPC service definitions with method signatures, making it the **most complete cross-service view** of any single matrix.

---

### 3.8 NexuShield (NestJS) — NEW SCAN

**Matrix:** `services/nexu-shield/.codetrellis/cache/4.1.2/nexu-shield/matrix.prompt` (131 lines)
**Files Scanned:** 72 | **Tokens:** ~2,003

#### ✅ Good Coverage

| Section        |    Count | Quality                                                           |
| -------------- | -------: | ----------------------------------------------------------------- |
| Schemas        |        4 | ✅ ApiKey, User, AuditLog, Session                                |
| Enums          |        6 | ✅ Complete values                                                |
| DTOs           |       11 | ✅                                                                |
| Controllers    |        6 | ✅ Auth, Password, MFA, ApiKey, Health, Audit                     |
| gRPC Services  |        4 | ✅ AuthService (10 methods), AuditService (5), Health, Reflection |
| Interfaces     |        8 | ✅                                                                |
| Error Handling | 13 files | ✅                                                                |

#### 🟡 Issues

| Issue                     | Detail                                                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Business domain WRONG** | "Trading/Finance" → should be **"Security & Authentication"**                                                              |
| Missing guards            | Rate limiting, auth guards implementation not captured                                                                     |
| Missing interceptors      | `logging.interceptor`, `rate-limit.interceptor`, `error.interceptor`, `auth.interceptor` — counted but logic not extracted |
| Missing circuit breaker   | `CircuitConfig` interface captured but `CircuitBreakerService` logic not extracted                                         |
| MFA flow invisible        | `MfaController` routes captured but TOTP/backup-code flow not in functions                                                 |
| Audit streaming           | `audit-stream.service.ts` — real-time audit streaming logic not extracted                                                  |

---

### 3.9 NexuTalk (NestJS) — NEW SCAN

**Matrix:** `services/nexu-talk/.codetrellis/cache/4.1.2/nexu-talk/matrix.prompt` (142 lines)
**Files Scanned:** 90 | **Tokens:** ~2,823

#### ✅ Excellent Coverage — Best New Scan

| Section        |        Count | Quality                                                                         |
| -------------- | -----------: | ------------------------------------------------------------------------------- |
| Schemas        |            2 | ✅ Conversation, Message                                                        |
| DTOs           |           12 | ✅                                                                              |
| Controllers    |            7 | ✅ Full route mapping                                                           |
| gRPC Services  |            3 | ✅ AIService (6), TalkService (18), AuthService (21 methods!)                   |
| Interfaces     |           32 | ✅ **Best interface coverage** — UserMemory, ConversationMemory, ServiceMetrics |
| Error Handling |     15 files | ✅                                                                              |
| TODOs          | 6 in 4 files | ✅                                                                              |

#### 🟡 Issues

| Issue             | Detail                                                                                              |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| WebSocket gateway | `chat-websocket.gateway.ts` exists but gateway events not listed                                    |
| Memory service    | `memory.service.ts` — UserMemory/ConversationMemory interfaces captured but service logic invisible |
| Event streaming   | `event-streaming.service.ts`, `event-processor.service.ts` — complex event processing not extracted |
| Service discovery | `service-discovery.service.ts` — microservice discovery logic not extracted                         |
| Brain client      | `brain-client.service.ts` — the actual LLM integration service not extracted as functions           |

#### ✅ Good: Business Domain

Correctly detected as "Communication/Messaging" ✅

---

### 3.10 NexuEdge (NestJS) — NEW SCAN

**Matrix:** `services/nexu-edge/.codetrellis/cache/4.1.2/nexu-edge/matrix.prompt` (90 lines)
**Files Scanned:** 34 | **Tokens:** ~1,030

#### ✅ Good Coverage

| Section       | Count | Quality                                     |
| ------------- | ----: | ------------------------------------------- |
| Schemas       |     1 | ✅ Tenant with plan/status                  |
| Enums         |     2 | ✅ TenantPlan, TenantStatus                 |
| DTOs          |     3 | ✅                                          |
| Controllers   |     4 | ✅ Tenant, Health, DevPortal, Chat          |
| gRPC Services |     3 | ✅ AIService, TalkService, AuthService      |
| Interfaces    |     6 | ✅ ServiceHealth, ChatMessage, ProxyRequest |

#### 🟡 Issues

| Issue                       | Detail                                                                          |
| --------------------------- | ------------------------------------------------------------------------------- |
| Business domain wrong       | "Communication/Messaging" → should be **"Developer Portal / API Gateway Edge"** |
| Missing gateway proxy logic | `gateway.service.ts` — request proxying not extracted                           |
| Missing rate limiting       | Tenant rate limiting per plan not visible                                       |

---

### 3.11 NexuChat UI (Angular) — NEW SCAN

**Matrix:** `services/nexu-chat-ui/.codetrellis/cache/4.1.2/nexu-chat-ui/matrix.prompt` (68 lines)
**Files Scanned:** 17 | **Tokens:** ~651

#### ✅ Good for Size

| Section          |       Count | Quality                              |
| ---------------- | ----------: | ------------------------------------ |
| Components       |           3 | ✅ App, NexubrainExpert, Chat        |
| Angular Services |           1 | ✅ ChatService with signals, methods |
| HTTP API         | 5 endpoints | ✅ With base URL                     |

#### 🟡 Issues

| Issue                      | Detail                                                |
| -------------------------- | ----------------------------------------------------- |
| Missing interfaces/models  | `models/` directory exists but no types extracted     |
| Missing environment config | API_URL hardcoded — not captured as config            |
| Missing Angular routing    | No routes extracted (small app but still has routing) |

---

### 3.12 NexuCore, NexuScan, NexuSight — NEW SCAN (Skeleton)

**Matrix:** 24 lines each | **Tokens:** ~153 each

These three services are **stub/skeleton projects** — they have only a README and no source code yet:

| Service   | README Title                     | Description                         | Source Files |
| --------- | -------------------------------- | ----------------------------------- | :----------: |
| NexuCore  | ⚙️ Automation & Reasoning Logic  | Workflow automation, business rules |      2       |
| NexuScan  | 📄 Document & Data Understanding | OCR, parsing, entity extraction     |      2       |
| NexuSight | 📊 Analytics & Insight Engine    | Real-time analytics, predictions    |      2       |

**Assessment:** CodeTrellis correctly identified these as empty projects. The README context is captured. No action needed until these services get implemented.

---

### 3.13 Kimi K2 Local — NEW SCAN

**Matrix:** 24 lines | **Tokens:** ~160

Minimal project — local LLM setup scripts. 8 files scanned, mostly configuration. No significant code to extract.

---

## 4. Cross-Project Context Gaps

### 4.1 Inter-Service Communication Map — MISSING EVERYWHERE

No matrix captures the full service dependency graph. Based on scanning all projects, here is the **actual** communication map that should exist:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CROSS-SERVICE gRPC MAP                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  nexu-chat-ui (Angular) ──HTTP──► nexu-edge ──gRPC──┐           │
│                                                      │           │
│  trading-ui (Angular) ──HTTP/WS──► trading-platform   │           │
│                                                      ▼           │
│                                              ┌─── nexu-talk     │
│  api-gateway ──gRPC──► nexu-shield (Auth)    │    (port 50052)  │
│      │                  (port 50051)         │        │          │
│      │                                       │        ▼          │
│      └──gRPC──► nexu-talk ──gRPC──► ai-service (HTTP/REST)     │
│      │          (port 50052)                                     │
│      └──gRPC──► ai-service (future: port 50053)                 │
│                                                                  │
│  trading-ai (Flask) ◄──HTTP──► trading-platform                 │
│      │                                                           │
│      └──uses──► sparse-reasoning-ai (symlinked files)           │
│                                                                  │
│  Proto Definitions:                                              │
│    auth.proto → AuthService (22 RPCs) → nexu-shield             │
│    talk.proto → TalkService (18 RPCs) → nexu-talk               │
│    ai.proto   → AIService (6 RPCs)   → ai-service (future)     │
│    common.proto → Shared types                                   │
└─────────────────────────────────────────────────────────────────┘
```

**This map exists NOWHERE in any matrix file.** Each service only knows about the gRPC services it _consumes_, not the full graph.

### 4.2 Shared Proto Definitions — NOT UNIFIED

| Proto File     |  RPC Methods   | Consumed By                       | Implemented By      |
| -------------- | :------------: | --------------------------------- | ------------------- |
| `auth.proto`   |       22       | api-gateway, nexu-talk, nexu-edge | nexu-shield         |
| `talk.proto`   |       18       | api-gateway, nexu-edge            | nexu-talk           |
| `ai.proto`     |       6        | api-gateway, nexu-talk, nexu-edge | ai-service (future) |
| `common.proto` | 0 (types only) | All                               | Shared              |

The proto files at `/proto/` define the **canonical contracts**, but:

- Each service's matrix shows its OWN gRPC definitions (which may drift from proto)
- No validation that service implementations match proto definitions
- CodeTrellis has a `proto.py` parser but it's not run on the root `/proto/` directory

### 4.3 Infrastructure Context — 0% Coverage

| File               | Purpose                       | Why It Matters          |
| ------------------ | ----------------------------- | ----------------------- |
| `main.tf`          | Provider config (AWS)         | Cloud platform          |
| `networking.tf`    | VPC, subnets, security groups | Network isolation       |
| `ecs.tf`           | ECS cluster config            | Container orchestration |
| `ecs-services.tf`  | Service definitions, ports    | **Service discovery**   |
| `database.tf`      | RDS, ElastiCache              | Database configs        |
| `load-balancer.tf` | ALB rules, targets            | Traffic routing         |
| `autoscaling.tf`   | Scaling policies              | Performance bounds      |
| `monitoring.tf`    | CloudWatch, alerts            | Observability           |
| `storage.tf`       | S3 buckets                    | File storage            |
| `variables.tf`     | All configurable params       | Environment config      |
| `outputs.tf`       | Exposed endpoints             | Service URLs            |

**Impact:** AI assistants have zero knowledge of deployment topology, ports, scaling limits, or database configurations.

### 4.4 Docker/Deployment Context — ~~0% Coverage~~ Partial (Phase A)

> **Phase A Update:** The new `RunbookExtractor` (G-01/G-02/G-03) now parses Dockerfiles, docker-compose.yml, .env.example, CI/CD configs (GitHub Actions, GitLab CI, Jenkins), and README setup sections. Run commands from package.json/pyproject.toml/Makefile are also extracted. Remaining gap: no deep Terraform extraction.

| File                   | Location               | What It Defines                            |
| ---------------------- | ---------------------- | ------------------------------------------ |
| `docker-compose.yml`   | `environments/dev/`    | Prometheus, Grafana, Jaeger, OTEL, MailHog |
| `docker-compose.yml`   | `ai/trading-platform/` | Full trading stack                         |
| `docker-compose.yml`   | `ai/kimi-k2-local/`    | Local LLM setup                            |
| `Dockerfile`           | `ai/ai-service/`       | Python FastAPI container                   |
| `Dockerfile`           | `ai/trading-ui/`       | Angular container                          |
| `Dockerfile.optimized` | `ai/ai-service/`       | Optimized build                            |

---

## 5. CodeTrellis Tool Deficiencies (Extractor-Level)

### Missing Extractors Needed

| Extractor                       | Language   | What It Would Capture                                  | Priority  |
| ------------------------------- | ---------- | ------------------------------------------------------ | :-------: |
| `nestjs_module_extractor`       | TypeScript | `@Module()` imports/exports/providers dependency graph |  🔴 High  |
| `nestjs_guard_extractor`        | TypeScript | `@Injectable() CanActivate` implementations            |  🔴 High  |
| `nestjs_interceptor_extractor`  | TypeScript | `@Injectable() NestInterceptor` implementations        | 🟡 Medium |
| `nestjs_middleware_extractor`   | TypeScript | `NestMiddleware` implementations                       | 🟡 Medium |
| `nestjs_pipe_extractor`         | TypeScript | `PipeTransform` implementations                        | 🟡 Medium |
| `nestjs_cron_extractor`         | TypeScript | `@Cron()` decorated methods                            | 🟡 Medium |
| `websocket_gateway_extractor`   | TypeScript | `@WebSocketGateway` events (emit/listen)               |  🔴 High  |
| `angular_guard_extractor`       | TypeScript | `CanActivate` guard implementations                    | 🟡 Medium |
| `angular_interceptor_extractor` | TypeScript | HTTP interceptor implementations                       | 🟡 Medium |
| `angular_pipe_extractor`        | TypeScript | Custom pipe implementations                            |  🟢 Low   |
| `python_class_extractor`        | Python     | Class methods (not just functions/dataclasses)         |  🔴 High  |
| `pytorch_model_extractor`       | Python     | `nn.Module` subclass architectures                     | 🟡 Medium |
| `training_pipeline_extractor`   | Python     | Training loops, optimizers, schedulers                 | 🟡 Medium |
| `terraform_extractor`           | HCL        | Service definitions, ports, configs                    | 🟡 Medium |
| `dockerfile_extractor`          | Dockerfile | Base images, ports, env vars                           | 🟡 Medium |
| `env_extractor`                 | .env       | Required environment variables                         |  🔴 High  |
| `cross_service_extractor`       | Multi      | Inter-service dependency mapping                       |  🔴 High  |

### Existing Extractors — Behavioral Issues

| Extractor                          | Issue                                                                                                                         | Impact                                                                                                                                       | Phase A Status  |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | :-------------: |
| `business_domain_extractor`        | Detects "Trading/Finance" even for auth/gateway services                                                                      | Wrong domain classification for 5+ services                                                                                                  |     ✅ G-12     |
| `type_extractor` (Python)          | ~~No deduplication — same dataclass extracted N times~~ Phase B: Dedup by (name, field_sig) + FastAPI dedup by (method, path) | ✅ G-07/08 Fixed — 902→837 dataclasses, 50→44 pydantic, Flask 213→101 routes, FastAPI 5× `GET:/` → 1× + 669 Python types with service prefix |   ✅ G-07/08    |
| TypeScript extractors on .py files | Parses string content in Python test files as TypeScript                                                                      | False positive components/interfaces                                                                                                         | ⚠️ G-05 partial |
| `function_extractor` (Python)      | Includes test fixtures (`@pytest.fixture`) as project functions                                                               | Pollutes function list                                                                                                                       | ⚠️ G-05 partial |
| `progress_extractor`               | Inconsistent — shows "100%" for some projects that have TODOs                                                                 | Misleading completion data                                                                                                                   |       ❌        |

---

## 6. Quantitative Gap Summary — Before vs After

### Coverage Table

| Metric                       | Before (Phase 1) | After (Phase 2) |     Gap Remaining |
| ---------------------------- | ---------------: | --------------: | ----------------: |
| Projects scanned             |                4 |              15 |   0 (all scanned) |
| Python files analyzed        |             ~438 |            ~548 |  ~0 (all covered) |
| TypeScript files analyzed    |             ~460 |            ~751 |  ~0 (all covered) |
| Total source files in matrix |             ~900 |          ~1,232 |   ~0 source files |
| Infrastructure files         |                0 |               0 |  **11 Terraform** |
| Docker/Compose files         |                0 |               0 |     **10+ files** |
| Proto files (root)           |                0 |               0 | **4 proto files** |
| Shell scripts                |                0 |               0 |    **40 scripts** |
| Cross-service flows          |                0 |               0 |     **All flows** |

### Quality Table

| Quality Metric               |          Before |                       After |              Target |
| ---------------------------- | --------------: | --------------------------: | ------------------: |
| Business domain accuracy     |       1/4 (25%) | ✅ Phase E weighted scoring |                100% |
| Type deduplication           |         ❌ None |             ✅ Phase B done |   Unique types only |
| Test fixture exclusion       | ❌ Not filtered |   ✅ Phase E PATTERN_IGNORE |      Tests excluded |
| NestJS module graph          |              ❌ |             ✅ Phase C done |        Full DI tree |
| Guard/Interceptor extraction |              ❌ |             ✅ Phase C done | All implementations |
| WebSocket events (NestJS)    |         Partial |                     Partial |      Full event map |
| Python class methods         |              ❌ |                          ❌ | All service classes |

### Token Efficiency

| Project              | Current Tokens | After Dedup (Est.) |                Savings |
| -------------------- | -------------: | -----------------: | ---------------------: |
| Sparse Reasoning AI  |        ~18,000 |            ~10,000 |                    44% |
| Trading AI           |         ~4,527 |             ~3,000 |                    34% |
| CodeTrellis Tool            |         ~5,500 |             ~2,500 | 55% (remove test data) |
| **Total across all** |    **~46,000** |        **~33,000** |               **~28%** |

---

## 7. Priority Remediation Roadmap

### 🔴 Priority 1 — Critical (Week 1)

| #   | Task                                                                           | Impact                                                            | Effort  |
| --- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ------- |
| 1.1 | ~~**Fix CodeTrellis self-scan** — Exclude test directories from scanning~~            | ✅ Phase E: PATTERN_IGNORE_SEGMENTS + \_is_pattern_scan_ignored() | Done    |
| 1.2 | ~~**Implement type deduplication** in `compressor.py`~~                        | ✅ Phase B: 902→837 dataclasses, 213→101 routes                   | Done    |
| 1.3 | ~~**Fix business domain detection** — Add keyword-based domain overrides~~     | ✅ Phase E: 3-pool weighted scoring (code:3×, fs:2×, README:1×)   | Done    |
| 1.4 | **Exclude test fixtures** from `[PYTHON_FUNCTIONS]` — Filter `@pytest.fixture` | ai-service shows test functions as project code                   | 2 hours |

### 🟡 Priority 2 — High (Week 2-3)

| #   | Task                                     | Impact                                                      | Effort  |
| --- | ---------------------------------------- | ----------------------------------------------------------- | ------- |
| 2.1 | **Build `nestjs_module_extractor`**      | Capture NestJS DI container for all 5 NestJS services       | 8 hours |
| 2.2 | **Build `python_class_extractor`**       | Capture class methods for FastAPI services, ML models       | 6 hours |
| 2.3 | **Build `env_extractor`**                | Parse `.env.example` files for required configuration       | 3 hours |
| 2.4 | ~~**Build `cross_service_extractor`**~~  | ✅ Phase B: `[SERVICE_MAP]` with 10 gRPC connections mapped | Done    |
| 2.5 | **Enhance WebSocket gateway extraction** | Capture `@SubscribeMessage()` events in NestJS gateways     | 4 hours |

### 🟢 Priority 3 — Medium (Week 4+)

| #   | Task                                                  | Impact                                          | Effort  |
| --- | ----------------------------------------------------- | ----------------------------------------------- | ------- |
| 3.1 | Build `nestjs_guard_extractor`                        | Capture CanActivate implementations             | 4 hours |
| 3.2 | Build `nestjs_interceptor_extractor`                  | Capture NestInterceptor implementations         | 4 hours |
| 3.3 | Build `dockerfile_extractor`                          | Parse Dockerfiles for base images, ports, envs  | 6 hours |
| 3.4 | Build `terraform_extractor`                           | Parse .tf files for infrastructure context      | 8 hours |
| 3.5 | Build `pytorch_model_extractor`                       | Extract nn.Module architectures for ML projects | 6 hours |
| 3.6 | Run CodeTrellis at **monorepo root level** with proto parser | Capture shared proto definitions                | 2 hours |
| 3.7 | ~~Add API route deduplication~~                       | ✅ Phase B: Flask routes 213→101 (53% dedup)    | Done    |

---

## Appendix A: All Matrix Files Generated

| File Path                                                                    | Lines | Generated            |
| ---------------------------------------------------------------------------- | ----: | -------------------- |
| `tools.codetrellis/.codetrellis/cache/4.1.2.codetrellis/matrix.prompt`                            |   905 | Pre-existing         |
| `ai/trading-ui/.codetrellis/cache/4.1.2/trading-ui/matrix.prompt`                   |   677 | Pre-existing         |
| `ai/trading-platform/.codetrellis/cache/4.1.2/trading-platform/matrix.prompt`       |   870 | Pre-existing         |
| `ai/sparse-reasoning-ai/.codetrellis/cache/4.1.2/sparse-reasoning-ai/matrix.prompt` | 3,167 | Pre-existing         |
| `ai/trading-ai/.codetrellis/cache/4.1.2/trading-ai/matrix.prompt`                   |   239 | **New (2026-02-07)** |
| `ai/ai-service/.codetrellis/cache/4.1.2/ai-service/matrix.prompt`                   |   131 | **New (2026-02-07)** |
| `ai/kimi-k2-local/.codetrellis/cache/4.1.2/kimi-k2-local/matrix.prompt`             |    24 | **New (2026-02-07)** |
| `services/api-gateway/.codetrellis/cache/4.1.2/api-gateway/matrix.prompt`           |   163 | **New (2026-02-07)** |
| `services/nexu-shield/.codetrellis/cache/4.1.2/nexu-shield/matrix.prompt`           |   131 | **New (2026-02-07)** |
| `services/nexu-talk/.codetrellis/cache/4.1.2/nexu-talk/matrix.prompt`               |   142 | **New (2026-02-07)** |
| `services/nexu-edge/.codetrellis/cache/4.1.2/nexu-edge/matrix.prompt`               |    90 | **New (2026-02-07)** |
| `services/nexu-chat-ui/.codetrellis/cache/4.1.2/nexu-chat-ui/matrix.prompt`         |    68 | **New (2026-02-07)** |
| `services/nexu-core/.codetrellis/cache/4.1.2/nexu-core/matrix.prompt`               |    24 | **New (2026-02-07)** |
| `services/nexu-scan/.codetrellis/cache/4.1.2/nexu-scan/matrix.prompt`               |    24 | **New (2026-02-07)** |
| `services/nexu-sight/.codetrellis/cache/4.1.2/nexu-sight/matrix.prompt`             |    24 | **New (2026-02-07)** |

## Appendix B: gRPC Service Registry (Compiled from All Matrices)

> **Phase B Update:** gRPC deduplication now active. Root scan shows 14 unique services (down from 24 raw entries). Each service includes `defined-in:` and `consumed-by:` attribution.

| Service          | Port  | Methods | Defined In (Proto)            | Consumed By                                    |
| ---------------- | :---: | ------: | ----------------------------- | ---------------------------------------------- |
| AuthService      | 50051 |      24 | proto/auth.proto              | nexu-talk, api-gateway, nexu-shield, nexu-edge |
| TalkService      | 50052 |      18 | proto/talk.proto              | nexu-talk, api-gateway, nexu-edge              |
| AIService        | 50053 |       9 | proto/ai.proto                | nexu-talk, api-gateway, nexu-edge              |
| AuditService     |   —   |       5 | nexu-shield/proto/audit.proto | (internal)                                     |
| Health           |   —   |       2 | nexu-shield                   | (internal)                                     |
| ServerReflection |   —   |       1 | nexu-shield                   | (debug)                                        |

## Appendix C: Correct Business Domains

| Project             | CodeTrellis Detected              | Correct Domain                             |
| ------------------- | -------------------------- | ------------------------------------------ |
| CodeTrellis Tool           | Trading/Finance ❌         | Developer Tools / Code Analysis            |
| Trading UI          | Trading/Finance ✅         | Trading/Finance                            |
| Trading Platform    | Trading/Finance ✅         | Trading/Finance                            |
| Sparse Reasoning AI | General ⚠️                 | AI/ML Research & Quantitative Trading      |
| Trading AI          | General Application ❌     | Algorithmic Trading / Quantitative Finance |
| AI Service          | General Application ❌     | AI/ML Platform — LLM Serving & RAG         |
| API Gateway         | Trading/Finance ❌         | Multi-Tenant API Gateway                   |
| NexuShield          | Trading/Finance ❌         | Security & Authentication                  |
| NexuTalk            | Communication/Messaging ✅ | Conversational AI Platform                 |
| NexuEdge            | Communication/Messaging ⚠️ | Developer Portal / API Gateway Edge        |
| NexuChat UI         | Communication/Messaging ✅ | Chat Interface                             |
| NexuCore            | General Application ⚠️     | Automation & Reasoning Logic (stub)        |

---

## 8. Root-Level Scan Findings (Phase 3 → Phase 5)

> Full analysis: [`docs/CodeTrellis_ROOT_VS_INDIVIDUAL_ANALYSIS.md`](./CodeTrellis_ROOT_VS_INDIVIDUAL_ANALYSIS.md)

### 8.1 Root Scan Statistics

| Metric             | Phase 3 ([FULL] tier)                               | Phase 5 ([LOGIC] --optimal) |
| ------------------ | --------------------------------------------------- | --------------------------- |
| Files Analyzed     | 9,695 (inflated)                                    | 1,357 (IMPL_LOGIC)          |
| Output Size        | 19,502 lines                                        | **18,728 lines**            |
| Tier               | [FULL]                                              | **[LOGIC]**                 |
| Schemas Found      | 123                                                 | 123                         |
| Controllers Found  | 91                                                  | 91                          |
| gRPC Sections      | 24                                                  | 24                          |
| Interfaces         | 575                                                 | 575                         |
| Enums              | 94                                                  | 94                          |
| Functions Analyzed | N/A                                                 | **11,857** (3,789 complex)  |
| BPL Practices      | 3 lines (stub)                                      | **86 lines (15 practices)** |
| Command Used       | `--tier full --include-progress --include-overview` | **`--optimal`**             |

### 8.2 What Root Scan Solved

1. **✅ Cross-service gRPC mapping** — 24 gRPC sections show all inter-service communication
2. **✅ Complete API surface** — 91 controllers cataloged in one place
3. **✅ Correct domain detection** — "Trading/Finance" at root (vs 20% accuracy individually)
4. **✅ Architectural decisions captured** — Signal Store, WebSocket, Event-Driven patterns
5. **✅ Unified schema view** — All 123 schemas visible together
6. **✅ Best Practices (Phase 5)** — 15 multi-framework practices (NestJS, Flask, FastAPI, TypeScript)
7. **✅ Function complexity analysis (Phase 5)** — 11,857 functions with complexity ratings

### 8.3 Persistent Issues (Updated After Phase A — v4.2.0)

1. **✅ PROGRESS contamination** — ~~61,645 TODOs from node_modules~~ **FIXED (G-04):** `_path_contains_ignored_segment()` now filters all path segments; expanded DEFAULT_IGNORE covers node_modules, test dirs, caches
2. **❌ No service attribution** — Can't tell which `HealthController` belongs to which service
3. **❌ Massive duplication** — gRPC services listed 3-5x (AuthService 5×), Flask routes duplicated 3-4x
4. **❌ 15,730 lines of IMPLEMENTATION_LOGIC** — 84% of output
5. **✅ Broken ACTIONABLE_ITEMS** — ~~Shows 0% despite 48 TODOs found~~ **FIXED (G-10):** New `_compress_actionable_items()` synthesizes high-priority TODOs + FIXMEs + blockers
6. **✅ Overview type: "Unknown"** — ~~Should detect as "monorepo"~~ **FIXED (G-11):** Enhanced `_detect_project_type()` with monorepo detection (workspaces, lerna/nx/turbo, services/ dir)

### 8.4 Recommended Strategy: 3-Tier Hierarchical Scanning

```
Tier 1: ROOT MATRIX → Cross-domain service map, complete API catalog, architecture
Tier 2: DOMAIN MATRICES → ai/, services/, infrastructure/ domain-level context
Tier 3: PROJECT MATRICES → Per-service schemas, functions, TODOs, internal structure
```

Required CodeTrellis enhancements:

- `--exclude-deps` hard exclude for node_modules recursively
- Service attribution (`[service-name]` prefix on all entities)
- Deduplication engine for gRPC/route merging
- `[SERVICE_MAP]` section for inter-service dependency graph
- `codetrellis scan --rollup` mode that aggregates Tier 3 into Tier 1
- Infrastructure extractors (Terraform, Docker, CI/CD)

| NexuScan | General Application ⚠️ | Document Processing & OCR (stub) |
| NexuSight | General Application ⚠️ | Analytics & Insights (stub) |

**Accuracy: 3/15 correct (20%) → Target: 100%**
**Phase A (G-12) improvement:** Enhanced `_detect_domain_category()` with filesystem scanning, README parsing, and minimum score threshold. Expected accuracy: ~70%+

---

---

## 9. Phase 4 & 5 Update: Optimal Command Re-Analysis (2026-02-07)

All projects were re-scanned with `--optimal` flag (= `--tier logic --deep --parallel --include-progress --include-overview --include-practices`), producing **+238% more content** on average.

**Phase 5 Correction:** Root `--optimal` was initially reported as hanging/timing out (Phase 4). User's direct run proved it completes successfully — producing 18,728-line [LOGIC] tier output. The recommended root command is now simply `codetrellis scan <root> --optimal`.

### Key Improvements Over Phase 2 Scans

| Metric                       | Phase 2  | Phase 4                | Change        |
| ---------------------------- | -------- | ---------------------- | ------------- |
| Average lines per project    | ~370     | ~1,250                 | **+238%**     |
| Average sections per project | ~10      | ~22                    | **+120%**     |
| Quality score                | 33.7/100 | 82.4/100               | **+48.8 pts** |
| BPL practices included       | 0        | 15 per project         | **New**       |
| Implementation logic         | None     | Full control flow maps | **New**       |
| LSP deep types               | None     | Resolved types/classes | **New**       |

### Root Scan Quality Progression

| Phase       | Command                                             |      Lines | Tier        | BPL                         |   Quality   |
| ----------- | --------------------------------------------------- | ---------: | ----------- | --------------------------- | :---------: |
| Phase 3     | `--tier full --include-progress --include-overview` |     19,502 | [FULL]      | 3-line stub                 |   ~55/100   |
| **Phase 5** | **`--optimal`**                                     | **18,728** | **[LOGIC]** | **86 lines (15 practices)** | **~85/100** |

### New Sections Discovered

- `[IMPLEMENTATION_LOGIC]` — Maps every function's control flow, API calls, transforms, complexity
- `[BEST_PRACTICES]` — Context-aware selection from 407-practice BPL library
- `[ACTIONABLE_ITEMS]` — Aggregated TODOs/FIXMEs with completion % (currently broken: shows 0%)
- `[PROJECT_STRUCTURE]` — Directory tree with detected patterns
- `:LSP` sections — Deep type resolution via TypeScript Language Server

### Cross-Reference

For the complete CLI audit, command comparison, and detailed findings, see:

- **[CodeTrellis Optimal Command Analysis](./CodeTrellis_OPTIMAL_COMMAND_ANALYSIS.md)** — Phase 4 + Phase 5 corrections
- **[Root vs Individual Analysis](./CodeTrellis_ROOT_VS_INDIVIDUAL_ANALYSIS.md)** — Phase 3 + Phase 5 updates

---

_Generated by Principal Solution Architect analysis on 2026-02-07_
_Phase 1-2: 15 projects, ~6,679 matrix lines, ~46,000 tokens, 1,232+ source files_
_Phase 3: Root monorepo scan, 19,502 lines [FULL] tier, 9,695 files_
_Phase 4: Optimal re-scans, ~12,830 lines across 9 projects, 407 BPL practices, 188 distributed .codetrellis files_
_Phase 5: Root --optimal confirmed working, 18,728 lines [LOGIC] tier, 11,857 functions, 15 BPL practices_
_Phase A (v4.2.0): RunbookExtractor (G-01/02/03), Filtering fixes (G-04/05/21), Bug fixes (G-10/11/12) — 9 gaps resolved_
_Phase A Testing: 6 additional bugs found & fixed during CLI testing on ai-service + nexu-shield, [AI_INSTRUCTION] prompt header added to all matrix.prompt output_
_Phase D (2026-02-09): WS-8 Public Repository Validation Framework — .codetrellis validate-repos` CLI command, validation_runner.sh, quality_scorer.py, analyze_results.py, 60-repo repos.txt, CLI-verified on calcom/cal.com (1,073 lines, 21s, PASS)_
_Phase E (2026-02-10): Self-scan quality fixes — PATTERN_IGNORE_SEGMENTS (G-05), regex leakage guard (BLOCKER self-match), 3-pool weighted domain scoring (G-12), G-16 Makefile enhancement (.PHONY/vars/includes/prerequisites) — CLI-verified on CodeTrellis self-scan + trading-ui regression_
_Phase F (v4.5–4.6, 2026-02-09): Go Language Support (G-17) + Generic Semantic Extraction + PocketBase Validation_

---

## Phase F: Go Language & Generic Semantic Extraction (v4.5–v4.6)

### What Was Done

| Area                                  | Action                                                                                      | Result                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Go Extractors (v4.5)**              | Created 4 extractors: GoTypeExtractor, GoFunctionExtractor, GoEnumExtractor, GoAPIExtractor | Structs, interfaces, functions, methods, const blocks, HTTP routes, gRPC |
| **Go Parser**                         | Created `go_parser_enhanced.py` with framework detection                                    | Gin, Echo, Chi, Gorilla, gRPC, GORM, Cobra, Fiber, Protobuf              |
| **Scanner Integration**               | Added go\_\* fields to ProjectMatrix, `.go` file scanning, `vendor` ignore                  | [GO_TYPES], [GO_API], [GO_FUNCTIONS] sections                            |
| **Compressor**                        | Added Go compression methods with receiver-grouped methods                                  | Methods grouped by receiver type (e.g., `(*PocketBase).Start()`)         |
| **BPL Go Practices**                  | Created `go_core.yaml` with 40 practices (GO001–GO040)                                      | Error handling, concurrency, interfaces, testing, performance            |
| **Project Type Detection**            | Added GO_CLI/GO_LIBRARY/GO_WEB_SERVICE/GO_FRAMEWORK to ArchitectureExtractor                | Reads go.mod, checks cmd/, main.go, apis/, plugins/                      |
| **`can_extract()` fix**               | Added go.mod, Cargo.toml, pom.xml, build.gradle to detection                                | Go/Rust/Java/Kotlin projects now detected                                |
| **Go Logic Extraction (v4.6)**        | Added `extract_go()` to LogicExtractor                                                      | Go control flow, API calls, goroutines, channels, context patterns       |
| **go.mod Parsing**                    | Added go.mod dependency extraction to `_extract_dependencies()`                             | Module name, Go version, categorized direct dependencies                 |
| **Minified JS Filter**                | Added `.min.js`/`.min.ts` skip in `_extract_logic()`                                        | Prevents minified JS from dominating IMPLEMENTATION_LOGIC                |
| **Generic Semantic Extractor (v4.6)** | Created `semantic_extractor.py` — language-agnostic                                         | Hooks, middleware, routes, plugins, lifecycle detection                  |
| **Enhanced Go API**                   | Added generic route detection, path validation, handler signatures                          | Catches custom routers (PocketBase), filters false positives             |

### PocketBase Validation Results

Scan command: `python3 -m.codetrellis.cli scan /tmp.codetrellis-validation/pocketbase --optimal`

| Metric            | Before (User Report) | After (v4.6)                  |
| ----------------- | -------------------- | ----------------------------- |
| Project Type      | Unknown              | **Go Framework** ✅           |
| Structs           | 0                    | **169** ✅                    |
| Interfaces        | 0                    | **24** ✅                     |
| Functions/Methods | 0                    | **1762** ✅                   |
| API Endpoints     | 0                    | **41** ✅                     |
| Hooks/Events      | 0                    | **64** ✅                     |
| Middleware        | 0                    | **1** ✅                      |
| Semantic Routes   | 0                    | **45** ✅                     |
| Dependencies      | 0                    | **21 direct** ✅              |
| Logic Snippets    | JS minified          | **1942 from 249 Go files** ✅ |
| Lifecycle Methods | 0                    | **33** ✅                     |
| Const Blocks      | 0                    | **41** ✅                     |
| Total Sections    | 5                    | **18** ✅                     |

### New Sections Added

| Section             | Purpose                                                                    |
| ------------------- | -------------------------------------------------------------------------- |
| `[GO_TYPES]`        | Structs with fields/tags/embedding, interfaces with methods, type aliases  |
| `[GO_API]`          | HTTP routes (generic + framework-specific), gRPC services                  |
| `[GO_FUNCTIONS]`    | Methods grouped by receiver type, exported functions grouped by file       |
| `[GO_DEPENDENCIES]` | go.mod module, Go version, categorized dependencies (web/db/auth/grpc/cli) |
| `[HOOKS]`           | Language-agnostic hook/event detection (lifecycle, event, observer)        |
| `[MIDDLEWARE]`      | Middleware registrations (auth, logging, cors, rate-limit, generic)        |
| `[ROUTES_SEMANTIC]` | Generically detected routes (deduped against GO_API)                       |
| `[LIFECYCLE]`       | Lifecycle methods by phase (init, start, run, stop, cleanup)               |

### Files Created/Modified

**New files (8):**

- .codetrellis/extractors/go/__init__.py`, `type_extractor.py`, `function_extractor.py`, `enum_extractor.py`, `api_extractor.py`
- .codetrellis/go_parser_enhanced.py`
- .codetrellis/bpl/practices/go_core.yaml`
- .codetrellis/extractors/semantic_extractor.py`

**Modified files (7):**

- .codetrellis/scanner.py` — go*\* + semantic*\* fields, `_parse_go()`, `_extract_semantics()`, go.mod parsing, Go logic scanning, .min.js filter
- .codetrellis/compressor.py` — Go sections, [GO_DEPENDENCIES], [HOOKS], [MIDDLEWARE], [ROUTES_SEMANTIC], [LIFECYCLE]
- .codetrellis/extractors/logic_extractor.py` — `extract_go()`, Go control flow keywords, `_analyze_go_logic()`
- .codetrellis/extractors/architecture_extractor.py` — GO\_\* ProjectType enum values, Go detection block, `can_extract()` fix
- .codetrellis/extractors/__init__.py` — Go + Semantic extractor exports
- .codetrellis/bpl/selector.py` — Go artifact counting, "golang" framework detection
- .codetrellis/extractors/nestjs_extractor.py` — NestJSGatewayInfo, `_parse_gateway_file()` (Gap 2.5)
