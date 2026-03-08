# CodeTrellis Root-Level vs Individual Scan: Comparative Analysis

**Generated:** 2026-02-07 (Updated Phase 5: Root --optimal confirmed working | Phase A: v4.2.0 remediation applied & CLI-tested | Phase B: v4.3.0 dedup + attribution + SERVICE_MAP applied & CLI-tested | Phase C: v4.4.0 Infrastructure extractors + NestJS DI + Smart truncation applied & CLI-tested | Phase D: v4.4.0 Public Repository Validation Framework implemented & CLI-verified on calcom/cal.com | Phase E: v4.4.0 Self-scan quality fixes — pattern contamination, regex leakage, domain misdetection, G-16 Makefile enhancement — CLI-verified on CodeTrellis self-scan + trading-ui regression | Phase F: v4.6.0 Go language support + SemanticExtractor + PocketBase validated)
**CodeTrellis Version:** 4.6.0
**Repository:** ns-brain (monorepo)

---

## 1. Executive Summary

We ran CodeTrellis at the **monorepo root level** (`/ns-brain`) and compared the output against **15 individual project-level scans** to understand what a holistic scan captures that per-project scans miss, and vice versa.

> **Phase 5 Update:** Root `--optimal` (= `--tier logic --deep --parallel --include-progress --include-overview --include-practices`) now confirmed working. Earlier testing in Phase 4 reported timeouts — disproved by user's direct run. Root matrix.prompt is now **~3,546 lines at [LOGIC] tier** (down from 18,728 after Phase C smart truncation) with 15 BPL practices, 59,269 functions analyzed (top 500 by complexity shown), 2 new infrastructure-aware sections (`[INFRASTRUCTURE]`, `[NESTJS_MODULES]`).

### Key Findings

| Metric             | Root Scan (Phase 5 --optimal) | All Individual Scans (sum)            | Delta           |
| ------------------ | ----------------------------- | ------------------------------------- | --------------- |
| **Output Size**    | 18,728 lines                  | 5,774 lines (+905 CodeTrellis) = 6,679 lines | **+180% more**  |
| **Tier**           | [LOGIC]                       | [LOGIC] per project                   | Same            |
| **Files Analyzed** | 1,357 (IMPL_LOGIC)            | ~1,232 (estimated)                    | +10%            |
| **Schemas**        | 123                           | ~45                                   | +173%           |
| **DTOs**           | 119                           | ~38                                   | +213%           |
| **Controllers**    | 91                            | ~18                                   | +406%           |
| **Components**     | 89                            | ~17                                   | +424%           |
| **Interfaces**     | 575                           | ~102                                  | +464%           |
| **gRPC Services**  | 24                            | ~4                                    | +500%           |
| **Enums**          | 94                            | ~30                                   | +213%           |
| **Stores**         | 12                            | ~3                                    | +300%           |
| **Functions**      | 11,857                        | ~2,800 (estimated)                    | +323%           |
| **BPL Practices**  | 15 (STANDARD)                 | varies per project                    | Multi-framework |

### Verdict

The root scan captures **dramatically more context** but suffers from **critical quality problems**. Individual scans are focused but miss cross-project relationships. **Neither alone is sufficient. A hierarchical approach is needed.**

---

## 2. What Root Scan Captures That Individual Scans Miss

### 2.1 ✅ Cross-Service gRPC Map (MAJOR WIN)

The root scan produced a **complete gRPC service catalog** across all services:

```
[GRPC:AIService]         → port:50053 | 6 methods (from proto + 3 service implementations)
[GRPC:TalkService]       → port:50052 | 18 methods (from proto + 3 service implementations)
[GRPC:AuthService]       → port:50051 | 22 methods (from proto + 4 service implementations)
[GRPC:MarketDataService] → 8 methods (internal, trading-platform)
[GRPC:SignalAggregatorService] → 7 methods
[GRPC:DecisionTrackerService]  → 7 methods
[GRPC:TradeExecutorService]    → 8 methods
[GRPC:PortfolioService]        → 7 methods
[GRPC:BrokerService]           → 5 methods
[GRPC:MarketSimulatorService]  → 10 methods
[GRPC:TenantService]           → 10 methods (api-gateway internal)
[GRPC:ServerReflection]        → 1 method
[GRPC:AuditService]            → 5 methods
[GRPC:Health]                  → 2 methods (standard gRPC health)
```

**Individual scans captured:** Only 4 gRPC sections (in api-gateway)
**Root scan captured:** 24 gRPC sections showing ALL inter-service communication
**Impact:** This is the single biggest win — you can now see which services talk to which via gRPC

### 2.2 ✅ Complete Controller Catalog (91 Controllers)

The root scan found **91 controllers** across the entire platform:

- **Trading Platform:** 35+ controllers (StockAnalysis, Portfolio, Position, Trading, etc.)
- **API Gateway:** 10 controllers (Auth, Tenant, AI, Talk, etc.)
- **NexuShield:** 5 controllers (Auth, ApiKey, Audit, Tenant, Health)
- **NexuTalk:** 5 controllers (Conversation, Brain, Analytics, etc.)
- **NexuEdge:** 3 controllers (Gateway, DeveloperPortal, Health)
- **Trading-AI (Python/Flask):** Routes captured as Flask endpoints

Individual scans typically found 5-10 controllers each, but **never showed the complete API surface** together.

### 2.3 ✅ Unified Schema View (123 Schemas)

All Mongoose/TypeORM schemas from all services in one place:

- Trading domain: 65+ schemas (Position, Trade, Signal, Decision, StockAnalysis, etc.)
- Auth domain: 5 schemas (User, Session, ApiKey, AuditLog, Tenant)
- Talk domain: 3 schemas (Conversation, Message, Analytics)
- Overlapping schemas visible: **User** appears twice (shield + gateway)

### 2.4 ✅ Business Domain Detection (CORRECT at Root Level!)

```
domain: Trading/Finance
purpose: A trading/financial application that handles market data,
         trade execution, portfolio management, and risk analysis
```

**Individual scans:** 12 of 15 projects detected as "General Application" (20% accuracy)
**Root scan:** Correctly identified as Trading/Finance (100% accuracy at root)
**Why:** Aggregated file content has enough trading keywords to trigger proper domain detection

### 2.5 ✅ Architectural Decisions Captured

```
State Management: NgRx Signal Store for reactive state management
Real-time Communication: WebSocket for real-time data streaming
Primary Data Flow Pattern: Event-Driven
```

Individual scans never captured these cross-cutting decisions.

### 2.6 ✅ Complete Python API Surface (192+ Endpoints)

Root scan captured ALL Flask + FastAPI endpoints across:

- `trading-ai`: 90+ Flask routes
- `ai-service`: 17+ FastAPI endpoints
- `kimi-k2-local`: 10+ FastAPI endpoints
- Test fixtures and examples included (contamination)

### 2.7 ✅ Research Code Included

The Collatz conjecture research (`research/collatz/`) was fully captured:

- 20+ Python modules with mathematical functions
- ~16,500 lines of implementation logic from research code
- All extracted function signatures, complexity analysis

### 2.8 ✅ Best Practices Auto-Detected

```
nestjs:10 | use: DI, DTOs, Guards, Logger | avoid: any, console.log
angular:19 | use: Signals, StandaloneComponents, @if/@for, OnPush | avoid: *ngIf, subscribe-without-cleanup
```

---

## 3. What Root Scan Gets WRONG (Critical Problems)

### 3.1 ❌ node_modules Contamination (MASSIVE)

**The #1 problem:** Despite `.codetrellis/config.json` having `node_modules` in ignore patterns, the root scan processed **9,695 files** (vs ~1,232 actual source files). This means ~8,463 files (~87%!) were from `node_modules`, `dist`, or other dependency folders.

Evidence of contamination:

- **Error handling section** includes `undici`, `mongodb`, `webpack` internal error classes
- **TODO section** includes TODOs from `tiktoken`, `Pillow`, `scipy` (Python deps)
- **Progress section** shows: `61,645 TODOs, 5,640 FIXMEs, 361 deprecated, 25,618 placeholders` — these are overwhelmingly from dependencies
- **SQLAlchemy models** from CodeTrellis test fixtures appear in output
- **Python functions** from 365+ files include test fixtures

### 3.2 ~~❌ Massive Duplication in gRPC Sections~~ ✅ Fixed (Phase B)

~~The same gRPC services are listed **multiple times**:~~

~~- `AuthService` appears **5 times** (from proto + each consuming service's client code)~~
~~- `AIService` appears **4 times**~~
~~- `TalkService` appears **4 times**~~

~~No deduplication or attribution (which service defines vs consumes).~~

**Phase B Fix:** `_deduplicate_grpc()` in `compressor.py` now groups by service name, merges methods (union), and resolves provider vs consumer from proto duplication patterns. Root scan: **24 raw → 14 unique** gRPC services. Each entry shows `defined-in:` (canonical proto file) and `consumed-by:` (consumer services).

### 3.3 ~~❌ Flask Route Duplication (3-4x)~~ ✅ Fixed (Phase B)

~~Flask routes from `trading-ai` are duplicated 3-4 times:~~

```
GET:/api/status          ← was 4 times, now 1×
GET:/api/signals         ← was 4 times, now 1×
GET:/api/groww/holdings  ← was 4 times, now 1×
```

**Phase B Fix:** `_deduplicate_flask_routes()` deduplicates by `(sorted_methods, path)` tuple. Root scan: **213 raw → 101 unique** Flask routes (53% reduction). Additionally, `_deduplicate_fastapi_endpoints()` deduplicates FastAPI endpoints by `(method, path)` tuple, preferring entries with `response_model` (e.g., `GET:/` 5→1, `GET:/info` 2→1).

### 3.4 ❌ IMPLEMENTATION_LOGIC Section is 15,730 Lines

Lines 2903–18633 = **~15,730 lines** of implementation logic, making up **84% of the entire output** (18,728 total). This includes:

- 11,857 functions analyzed (3,789 complex, 4,829 moderate)
- 1,357 files processed
- CodeTrellis tool's own code functions (~400 functions)
- Research/Collatz mathematical functions (~200 functions)
- Some node_modules internal code contamination
- Massively over-detailed for a "context prompt"

> **Phase 5 Note:** Compared to Phase 3's [FULL] tier (16,467 lines), the [LOGIC] tier is slightly smaller (15,730 lines) but contains richer function-level analysis with complexity ratings.

### 3.5 ~~❌ No Service Attribution~~ ✅ Fixed (Phase B)

~~Schemas, controllers, DTOs have no service prefix. You can't tell:~~

~~- Which `HealthController` belongs to which service (there are 7!)~~
~~- Which `User` schema is from nexu-shield vs api-gateway~~
~~- Which `AuthController` is the canonical one~~

~~Only DTOs have attribution: `[DTOS:ai/trading-platform]`, `[DTOS:nexu-talk]`, etc.~~

**Phase B Fix:** `_service_prefix()` in `compressor.py` now adds `source_service:` prefix to schemas, controllers, enums, components, Python types (Pydantic models, dataclasses, TypedDicts), and Python API (FastAPI endpoints, Flask routes) in monorepo scans. `_tag_source_services()` in `scanner.py` derives the service name from file paths (`services/<name>/...`, `ai/<name>/...`, `apps/<name>/...`). Root scan: **3,086 entities tagged** with source service.

### 3.6 ❌ Project Type: "Unknown"

Despite detecting the business domain correctly, the project type is "Unknown" instead of "monorepo" (which it correctly shows in [PROJECT] section but not in [OVERVIEW]).

### 3.7 ❌ ACTIONABLE_ITEMS Empty

```
# Completion: 0% | TODOs: 0 | FIXMEs: 0
```

Despite finding 48 TODOs in the [TODOS] section, the [ACTIONABLE_ITEMS] shows zero. This is a CodeTrellis bug where the two sections don't sync.

---

## 4. What Individual Scans Capture That Root Misses

### 4.1 Per-Service Module Maps

Individual scans show clean module organization:

```
# nexu-talk individual scan:
modules: websocket, memory, grpc, auth, health, discovery, integrations, brain, events, analytics, conversation
```

Root scan has this in [SERVICES] but loses the internal structure of each module.

### 4.2 Focused TODO/FIXME Context

- `ai-service` individual scan: 110 TODOs, 32 FIXMEs (all from actual source code)
- Root scan: 48 TODOs but heavily contaminated by node_modules/dependency TODOs

### 4.3 Clean Function Lists

Individual scans produce clean, focused function/method lists per service without cross-contamination from test fixtures or research code.

### 4.4 Per-Project Business Domain (When Correct)

The 3 projects with correct domain detection show focused domain context:

- `trading-platform`: Trading/Finance with 20 core entities
- `trading-ai`: Should be Trading/Finance (detected wrong individually too)
- `sparse-reasoning-ai`: ML/AI with sparse reasoning context

---

## 5. Quantitative Comparison by Section

| Section                    | Root Scan Lines   | All Individual Scans Lines | Notes                                                                                 |
| -------------------------- | ----------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| **[PROJECT]**              | 6                 | ~15×4 = 60                 | Root: one entry; Individual: 15 separate headers                                      |
| **[SERVICES]**             | 9                 | 0                          | Root only - lists all services with modules                                           |
| **[SCHEMAS]**              | 165               | ~80                        | Root wins - unified view                                                              |
| **[ENUMS]**                | 96                | ~50                        | Root wins - complete enum catalog                                                     |
| **[DTOS]**                 | 57                | ~35                        | Root wins - attributed by project                                                     |
| **[CONTROLLERS]**          | 92                | ~40                        | Root wins - complete API surface                                                      |
| **[GRPC]**                 | 49                | ~10                        | Root wins — 14 deduplicated services (was 24 raw) with `defined-in:` + `consumed-by:` |
| **[COMPONENTS]**           | 91                | ~70                        | Similar - mostly from trading-ui                                                      |
| **[INTERFACES]**           | 493               | ~180                       | Root wins - 575 total                                                                 |
| **[TYPES]**                | 45                | ~15                        | Root wins                                                                             |
| **[WEBSOCKET_EVENTS]**     | 48                | ~30                        | Root slightly better                                                                  |
| **[HTTP_API]**             | 60                | ~20                        | Root wins                                                                             |
| **[BUSINESS_DOMAIN]**      | 8                 | ~15×3 = 45                 | Root: correct; Individual: mostly wrong                                               |
| **[PYTHON_TYPES]**         | ~700              | ~200                       | Root wins - captures all Python models                                                |
| **[PYTHON_API]**           | ~280              | ~100                       | Root wins — deduplicated (213 raw → 101 unique Flask routes)                          |
| **[IMPLEMENTATION_LOGIC]** | **~15,730**       | ~1,500                     | Root: 84% of output, massively bloated                                                |
| **[PROGRESS]**             | 16                | ~15×2 = 30                 | Root: contaminated by deps                                                            |
| **[TODOS]**                | 25                | ~150                       | Individual wins - focused per-project                                                 |
| **[BEST_PRACTICES]**       | 86 (15 practices) | varies                     | Root: multi-framework BPL (NestJS, Flask, FastAPI, TS)                                |

---

## 6. Root Scan Quality Score

> **Updated for Phase 5 (root `--optimal` = [LOGIC] tier with BPL)**

| Dimension              | Score            | Rationale                                                                                              |
| ---------------------- | ---------------- | ------------------------------------------------------------------------------------------------------ |
| **Completeness**       | ⭐⭐⭐⭐⭐ (5/5) | Captures everything across all projects                                                                |
| **Cross-Service View** | ⭐⭐⭐⭐⭐ (5/5) | gRPC map excellent with service attribution + SERVICE_MAP                                              |
| **Signal-to-Noise**    | ⭐⭐ (2/5)       | PROGRESS contaminated by node_modules TODOs (61,645)                                                   |
| **Deduplication**      | ⭐⭐⭐⭐ (4/5)   | gRPC deduped (24→14), Flask deduped (213→101), FastAPI deduped (e.g., GET:/ 5→1), Python types deduped |
| **Attribution**        | ⭐⭐⭐⭐⭐ (5/5) | All entity types attributed with source_service prefix incl. Python types & API (3,086 entities)       |
| **Size Efficiency**    | ⭐⭐ (2/5)       | 18,728 lines; 84% is IMPLEMENTATION_LOGIC (improved from 19,502)                                       |
| **Best Practices**     | ⭐⭐⭐⭐ (4/5)   | 15 practices, multi-framework (NestJS, Flask, FastAPI, TS)                                             |
| **Function Analysis**  | ⭐⭐⭐⭐ (4/5)   | 11,857 functions with complexity ratings (3,789 complex)                                               |
| **Actionability**      | ⭐⭐⭐ (3/5)     | Good for understanding total API surface, ACTIONABLE_ITEMS still broken (0%)                           |

**Overall: 3.9/5** — Improved from 3.0/5 (Phase 5). Phase B added deduplication engine (gRPC, Flask, FastAPI endpoints, Python types), service attribution across all entity types (schemas, controllers, enums, components, Python types, Python API), and SERVICE_MAP cross-reference section. Remaining improvements: PROGRESS contamination fix, size efficiency (IMPLEMENTATION_LOGIC bloat), rollup mode.

---

## 7. The Interlinking Problem: What's Still Missing

Even with the root scan, we **still can't see**:

### 7.1 ~~Service Dependency Graph~~ ✅ Partially Resolved (Phase B)

```
Phase B SERVICE_MAP now shows inter-service connections:
  api-gateway → nexu-shield (AuthService via gRPC)
  api-gateway → nexu-talk (TalkService via gRPC)
  api-gateway → ai-service (AIService via gRPC)
  ... 10 connections total detected from proto duplication + docker-compose depends_on
```

> Remaining gap: port numbers and transport types (gRPC vs REST vs WebSocket) not yet resolved from infrastructure files.
> nexu-talk → ai-service (for LLM completions)
> nexu-edge → api-gateway (proxies requests)

```

### 7.2 Shared Schema Ownership

```

User schema exists in both nexu-shield and api-gateway.
Which is the source of truth? Root scan shows both but doesn't indicate.

```

### 7.3 ~~Proto → Service → Controller Flow~~ ✅ Partially Resolved (Phase B)

```

auth.proto defines 22 RPCs
→ nexu-shield implements them ← Phase B: defined-in: shows proto source
→ api-gateway consumes them ← Phase B: consumed-by: lists consumers
→ api-gateway exposes via REST ← NOT YET: controller-to-gRPC mapping still missing

Phase B provides proto→service mapping via gRPC dedup.
Full end-to-end proto→service→controller flow requires
controller-to-gRPC client detection (Phase C scope).

```

### 7.4 Infrastructure Context

```

- Terraform files (12 .tf files) → Zero coverage
- Docker configs → Partial coverage (Phase A: RunbookExtractor parses Dockerfile + docker-compose.yml)
- CI/CD pipeline → Partial coverage (Phase A: RunbookExtractor parses GitHub Actions, GitLab CI, Jenkins)
- Environment configs → Partial coverage (Phase A: RunbookExtractor parses .env.example files)

```

---

## 8. Recommended Hierarchical Scanning Strategy

### 8.1 Three-Tier Architecture

```

Tier 1: ROOT MATRIX (Aggregated)
├── Tier 2: DOMAIN MATRICES (Per Domain)
│ ├── ai/ domain matrix
│ ├── services/ domain matrix
│ ├── infrastructure/ domain matrix
│ └── proto/ domain matrix
└── Tier 3: PROJECT MATRICES (Per Service)
├── services/api-gateway/matrix.prompt
├── services/nexu-shield/matrix.prompt
├── ai/trading-platform/matrix.prompt
└── ... (15 individual matrices)

```

### 8.2 What Each Tier Should Contain

**Tier 3 (Project Level) — Current Individual Scans:**

- Schemas, DTOs, Controllers, Services, Functions
- Per-project TODOs, Progress, Error Handling
- Internal module structure
- Focus: "How does THIS service work?"

**Tier 2 (Domain Level) — NEW:**

- Service registry within the domain
- Shared interfaces/types across services in the domain
- Inter-service gRPC client/server mapping
- Domain-specific vocabulary and entities
- Focus: "How do services in this domain interact?"

**Tier 1 (Root Level) — REFINED:**

- Cross-domain service dependency graph
- Complete API surface catalog (REST + gRPC + WebSocket)
- Shared proto definitions
- Infrastructure topology (Terraform → ECS → Services)
- Business domain context and architectural decisions
- Focus: "How does the entire platform fit together?"

### 8.3 Implementation Requirements

To make this work, CodeTrellis needs:

1. **~~`--exclude-deps` flag~~ ✅ Phase A (G-04)** — `_path_contains_ignored_segment()` now hard-excludes node_modules, dist, .venv, **pycache** via path-segment filtering
2. **~~Service attribution~~ ✅ Phase B (G-09)** — `_service_prefix()` adds `source_service:` prefix to all entity types in monorepo scans (3,086 entities tagged)
3. **~~Deduplication engine~~ ✅ Phase B (G-06/07/08)** — `_deduplicate_grpc()`, `_deduplicate_flask_routes()`, `_deduplicate_python_types()` merge identical definitions, keep attribution
4. **~~Cross-reference section~~ ✅ Phase B (G-19/G-20)** — `[SERVICE_MAP]` section shows service→service dependencies from proto duplication patterns + docker-compose
5. **Rollup mode** — `codetrellis scan --rollup` that reads Tier 3 matrices and produces Tier 1 _(Remaining — Phase C)_
6. **~~Infrastructure extractors~~ ⚠️ Phase A (G-01/02/03) partial** — RunbookExtractor handles Dockerfile, docker-compose, CI/CD, .env.example, **shell scripts**. Terraform extractor still needed.
7. **✅ AI Context Header (Phase A Testing)** — `[AI_INSTRUCTION]` prompt at top of every matrix.prompt so AI consumers auto-read full context

### 8.4 ~~Proposed~~ New Sections for Root Matrix

```

[SERVICE_MAP] ← ✅ IMPLEMENTED (Phase B v4.3.0)
api-gateway → nexu-shield:AuthService(gRPC:50051)
api-gateway → nexu-talk:TalkService(gRPC:50052)
api-gateway → ai-service:AIService(gRPC:50053)
nexu-talk → ai-service:AIService(gRPC:50053)
nexu-edge → api-gateway:REST(HTTP:3001)
trading-platform → trading-ai:REST(HTTP:5001)
trading-ui → trading-platform:REST+WebSocket(HTTP:3000)

[INFRASTRUCTURE]
terraform:ecs-services → api-gateway,nexu-shield,nexu-talk,nexu-edge,ai-service
terraform:database → MongoDB(Atlas),Redis
terraform:networking → VPC,ALB,Target Groups
terraform:monitoring → CloudWatch,Prometheus

[PROTO_CONTRACTS]
auth.proto → 22 RPCs → implemented-by:nexu-shield → consumed-by:api-gateway,nexu-talk
talk.proto → 18 RPCs → implemented-by:nexu-talk → consumed-by:api-gateway
ai.proto → 6 RPCs → implemented-by:ai-service → consumed-by:api-gateway,nexu-talk

[SHARED_TYPES]
User → nexu-shield(source), api-gateway(copy) → DIVERGENCE DETECTED
Session → nexu-shield(source), api-gateway(reference)

````

---

## 9. Conclusion

### Current State (Phase 5 — Root --optimal Confirmed)

| Approach                    | Pros                                                                                          | Cons                                                        |
| --------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Individual Scans**        | Clean, focused, per-service context                                                           | No cross-service view, domain misdetection                  |
| **Root Scan (`--optimal`)** | Complete coverage, correct domain, gRPC map, [LOGIC] tier, 15 BPL practices, 11,857 functions, **deduped gRPC/Flask/types, SERVICE_MAP, service attribution** | PROGRESS contamination, size bloat (IMPLEMENTATION_LOGIC 84%) |

### Phase 5 Key Correction

> Root `--optimal` **WORKS** on the monorepo. Earlier Phase 4 testing reported hangs/timeouts — this has been disproved. The recommended command for root-level scanning is now simply:
>
> ```
> codetrellis scan <root> --optimal
> ```

### Recommended Next Steps

1. ~~**Immediate:** Fix `.codetrellis/config.json` ignore patterns to properly exclude node_modules recursively~~ ✅ **Done (Phase A, G-04)** — `_path_contains_ignored_segment()` filters all dependency/test/cache dirs
2. ~~**Short-term:** Add service attribution to root scan output; fix ACTIONABLE_ITEMS bug~~ ✅ **Done (Phase A + B)** — ACTIONABLE_ITEMS fixed (G-10), service attribution implemented (G-09, 3,086 entities tagged), 6 additional bugs fixed during Phase A testing
3. ~~**Medium-term:** Build deduplication engine and `[SERVICE_MAP]` section~~ ✅ **Done (Phase B, G-06/07/08/19/20)** — gRPC dedup (24→14), Flask dedup (213→101), Python type dedup, SERVICE_MAP with 10 connections
4. **Long-term:** Implement full 3-tier hierarchical scanning with rollup mode _(Phase C scope)_
5. **Phase D (DONE):** Public Repository Validation Framework — .codetrellis validate-repos` CLI command, 60-repo corpus, quality_scorer.py, analyze_results.py, validation_runner.sh — CLI-verified on calcom/cal.com (1,073 lines, 21s, PASS)

### The Core Insight

> **Running CodeTrellis `--optimal` at root level produces the highest-quality monorepo analysis** — 18,728 lines at [LOGIC] tier with 15 BPL practices, 11,857 function analyses, correct Trading/Finance domain detection, and complete 14-service deduplicated gRPC map with provider/consumer attribution. **Phase A (v4.2.0) resolved** the node_modules contamination in PROGRESS (G-04), broken ACTIONABLE_ITEMS (G-10), and "Unknown" project type detection (G-11). **Phase A Testing** uncovered and fixed 6 additional bugs (hardcoded project type, progress/actionable section conflict, wrong dict keys, missing shell scripts, missing AI_ML/DEVTOOLS domains) and added the `[AI_INSTRUCTION]` prompt header so AI consumers auto-read and follow the full matrix context. **Phase B (v4.3.0) resolved** the three biggest remaining quality gaps: gRPC deduplication (24→14 unique services with `defined-in:`/`consumed-by:`), Flask route deduplication (213→101), Python type deduplication, service attribution across 3,086 entities, and the new `[SERVICE_MAP]` cross-reference section with 10 inter-service connections. The **remaining quality improvements** are: PROGRESS section noise reduction, IMPLEMENTATION_LOGIC size optimization (84% of output), and 3-tier hierarchical rollup mode. Additionally, the `[RUNBOOK]` section (G-01/02/03) surfaces run commands, CI/CD pipelines, env variables, shell scripts, and Docker configuration. **Phase D (2026-02-09)** completed WS-8 by implementing a full Public Repository Validation Framework — .codetrellis validate-repos` CLI command orchestrates 60-repo validation with automated quality scoring (`quality_scorer.py`) and Gap Analysis Round 2 generation (`analyze_results.py`). CLI-verified on calcom/cal.com: 10,517 files, 1,073-line output, 21s scan time, PASS.
````
