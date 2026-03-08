# CodeTrellis Validation Findings — 60-Repository Quality Audit

> **Generated:** 2026-02-09 13:24
> **CodeTrellis Version:** 4.1.2 (Phase D — WS-8)
> **Repos Scanned:** 60
> **Purpose:** Comprehensive quality analysis of CodeTrellis scan output across diverse public repositories
> **Action:** Use this document to prioritize extractor development and quality fixes for future phases

---

## 1. Executive Summary

| Metric | Value |
|---|---|
| Total repos scanned | 60 |
| Scan success | 59/60 (98.3%) |
| Scan failures | 1 (timeouts: 0, clone failures: 0) |
| Domain accuracy | 1/59 (1.7%) |
| Tracebacks | 1 |
| Target pass rate | >70% |
| Target met | 🎉 YES |

## 2. Top Issues (By Frequency)

| # | Issue | Repos Affected |
|---|---|---|
| 1 | Domain misdetection: detected '...' but should be '...' | 59 |
| 2 | Zero entities extracted from N files — expected TS/JS entities from package.json project | 26 |
| 3 | Domain vocabulary is wrong for this project type | 16 |
| 4 | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis | 6 |
| 5 | Enum duplication detected (same enum listed multiple times) | 1 |
| 6 | Python traceback in scan stderr | 1 |
| 7 | Missing [RUNBOOK] section — AI cannot know how to run project | 1 |
| 8 | Missing [BEST_PRACTICES] — no BPL practices selected | 1 |
| 9 | No business domain detected | 1 |
| 10 | Possible TODO contamination: N TODOs for N files | 1 |

## 3. Missing Extractors & Unsupported Frameworks

| Framework/Language | Repos Needing It | Priority |
|---|---|---|
| Svelte | 3 | 🟢 Medium |
| Prisma | 2 | 🟢 Medium |
| tRPC | 2 | 🟢 Medium |
| SQLAlchemy | 1 | 🟢 Medium |

## 4. Per-Category Analysis

### 4.1 AI/ML Projects

**Pass rate:** 10/10 | **Domain accuracy:** 1/10

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `langchain-ai/langchain` | ✅ | 863 | 11s | — | ❌ Trading/Finance→AI/LLM Framework | Domain misdetection: detected 'Trading/Finance' but should be 'AI/LLM Framewo... |
| `openai/openai-cookbook` | ✅ | 541 | 0s | — | ❌ General Application→AI Documentation/Tutorials | Domain misdetection: detected 'General Application' but should be 'AI Documen... |
| `run-llama/llama_index` | ✅ | 961 | 10s | — | ✅ AI/ML Platform→AI/RAG Framework | — |
| `huggingface/transformers` | ✅ | 1212 | 51s | — | ❌ Trading/Finance→ML Framework | Domain misdetection: detected 'Trading/Finance' but should be 'ML Framework';... |
| `mlflow/mlflow` | ✅ | 1310 | 15s | — | ❌ Trading/Finance→ML Experiment Tracking | Domain misdetection: detected 'Trading/Finance' but should be 'ML Experiment ... |
| `bentoml/BentoML` | ✅ | 652 | 2s | — | ❌ AI/ML Platform→ML Model Serving | Domain misdetection: detected 'AI/ML Platform' but should be 'ML Model Serving' |
| `ray-project/ray` | ✅ | 1046 | 11s | — | ❌ General Application→Distributed Computing | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis; Domain misdetection: ... |
| `qdrant/qdrant` | ✅ | 278 | 0s | — | ❌ AI/ML Platform→Vector Database | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis; Domain misdetection: ... |
| `chroma-core/chroma` | ✅ | 942 | 2s | — | ❌ Trading/Finance→Vector Database | Domain misdetection: detected 'Trading/Finance' but should be 'Vector Databas... |
| `open-webui/open-webui` | ✅ | 1395 | 4s | — | ❌ General Application→AI Chat Interface | Domain misdetection: detected 'General Application' but should be 'AI Chat In... |

### 4.2 DevTools & Infrastructure

**Pass rate:** 10/10 | **Domain accuracy:** 0/10

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `grafana/grafana` | ✅ | 7677 | 28s | — | ❌ Analytics/BI→Observability Platform | Domain misdetection: detected 'Analytics/BI' but should be 'Observability Pla... |
| `prometheus/prometheus` | ✅ | 490 | 1s | — | ❌ Developer Tools→Monitoring System | Domain misdetection: detected 'Developer Tools' but should be 'Monitoring Sys... |
| `traefik/traefik` | ✅ | 365 | 0s | — | ❌ General Application→Reverse Proxy/Load Balancer | Domain misdetection: detected 'General Application' but should be 'Reverse Pr... |
| `hashicorp/terraform` | ✅ | 346 | 1s | — | ❌ Trading/Finance→Infrastructure as Code | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis; Domain misdetection: ... |
| `docker/compose` | ✅ | 288 | 0s | — | ❌ General Application→Container Orchestration | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis; Domain misdetection: ... |
| `pulumi/pulumi` | ✅ | 879 | 107s | — | ❌ General Application→Infrastructure as Code | Domain misdetection: detected 'General Application' but should be 'Infrastruc... |
| `n8n-io/n8n` | ✅ | 1234 | 31s | — | ❌ Trading/Finance→Workflow Automation | Domain misdetection: detected 'Trading/Finance' but should be 'Workflow Autom... |
| `nocodb/nocodb` | ✅ | 1012 | 13s | Monorepo | ❌ AI/ML Platform→Database UI/Airtable Alternative | Domain misdetection: detected 'AI/ML Platform' but should be 'Database UI/Air... |
| `strapi/strapi` | ✅ | 794 | 7s | — | ❌ General Application→Headless CMS | Domain misdetection: detected 'General Application' but should be 'Headless C... |
| `directus/directus` | ✅ | 753 | 4s | — | ❌ General Application→Data Platform/Headless CMS | Domain misdetection: detected 'General Application' but should be 'Data Platf... |

### 4.3 Frontend Frameworks

**Pass rate:** 9/10 | **Domain accuracy:** 0/9

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `angular/angular` | ❌ | 30 | 17s | — | ❌ Not detected→Frontend Framework | Python traceback in scan stderr; Missing [RUNBOOK] section — AI cannot know h... |
| `vercel/next.js` | ✅ | 1120 | 62s | — | ❌ Developer Tools→React Meta-Framework | Domain misdetection: detected 'Developer Tools' but should be 'React Meta-Fra... |
| `vuejs/core` | ✅ | 1445 | 3s | — | ❌ General Application→Frontend Framework | Domain misdetection: detected 'General Application' but should be 'Frontend F... |
| `sveltejs/svelte` | ✅ | 740 | 3s | — | ❌ Trading/Finance→Frontend Framework/Compiler | Domain misdetection: detected 'Trading/Finance' but should be 'Frontend Frame... |
| `shadcn-ui/ui` | ✅ | 1118 | 11s | — | ❌ General Application→UI Component Library | Domain misdetection: detected 'General Application' but should be 'UI Compone... |
| `ionic-team/ionic-framework` | ✅ | 2060 | 5s | Monorepo | ❌ General Application→Cross-Platform UI Framework | Domain misdetection: detected 'General Application' but should be 'Cross-Plat... |
| `ant-design/ant-design` | ✅ | 2391 | 5s | — | ❌ General Application→UI Component Library | Domain misdetection: detected 'General Application' but should be 'UI Compone... |
| `storybookjs/storybook` | ✅ | 739 | 7s | — | ❌ General Application→UI Component Development | Domain misdetection: detected 'General Application' but should be 'UI Compone... |
| `excalidraw/excalidraw` | ✅ | 1500 | 30s | — | ❌ General Application→Drawing/Whiteboard Tool | Domain misdetection: detected 'General Application' but should be 'Drawing/Wh... |
| `TanStack/query` | ✅ | 721 | 2s | Monorepo | ❌ Developer Tools→Data Fetching Library | Domain misdetection: detected 'Developer Tools' but should be 'Data Fetching ... |

### 4.4 Full-Stack Applications

**Pass rate:** 10/10 | **Domain accuracy:** 0/10

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `calcom/cal.com` | ✅ | 1072 | 22s | Monorepo | ❌ E-Commerce→Scheduling/Calendar | Domain misdetection: detected 'E-Commerce' but should be 'Scheduling/Calendar... |
| `medusajs/medusa` | ✅ | 674 | 27s | — | ❌ General Application→E-Commerce | Domain misdetection: detected 'General Application' but should be 'E-Commerce... |
| `formbricks/formbricks` | ✅ | 733 | 5s | — | ❌ General Application→Survey/Forms | Domain misdetection: detected 'General Application' but should be 'Survey/For... |
| `documenso/documenso` | ✅ | 699 | 4s | — | ❌ General Application→Document Signing | Domain misdetection: detected 'General Application' but should be 'Document S... |
| `twentyhq/twenty` | ✅ | 1439 | 31s | Monorepo | ❌ AI/ML Platform→CRM | Domain misdetection: detected 'AI/ML Platform' but should be 'CRM' |
| `hoppscotch/hoppscotch` | ✅ | 981 | 4s | Monorepo | ❌ Trading/Finance→API Development Tool | Domain misdetection: detected 'Trading/Finance' but should be 'API Developmen... |
| `immich-app/immich` | ✅ | 1230 | 4s | Monorepo | ❌ Trading/Finance→Photo Management | Domain misdetection: detected 'Trading/Finance' but should be 'Photo Manageme... |
| `maybe-finance/maybe` | ✅ | 582 | 1s | — | ❌ Trading/Finance→Personal Finance | Domain misdetection: detected 'Trading/Finance' but should be 'Personal Finan... |
| `appwrite/appwrite` | ✅ | 273 | 4s | — | ❌ General Application→Backend-as-a-Service | Missing [IMPLEMENTATION_LOGIC] — no code flow analysis; Domain misdetection: ... |
| `logto-io/logto` | ✅ | 706 | 12s | — | ❌ General Application→Authentication/Identity | Domain misdetection: detected 'General Application' but should be 'Authentica... |

### 4.5 Microservices & Backend

**Pass rate:** 10/10 | **Domain accuracy:** 0/10

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `nestjs/nest` | ✅ | 2385 | 4s | Monorepo | ❌ AI/ML Platform→Backend Framework | Domain misdetection: detected 'AI/ML Platform' but should be 'Backend Framework' |
| `fastapi/fastapi` | ✅ | 830 | 1s | — | ❌ Trading/Finance→Backend Framework | Domain misdetection: detected 'Trading/Finance' but should be 'Backend Framew... |
| `pallets/flask` | ✅ | 464 | 0s | — | ❌ Developer Tools→Backend Framework | Domain misdetection: detected 'Developer Tools' but should be 'Backend Framew... |
| `tiangolo/full-stack-fastapi-template` | ✅ | 716 | 0s | — | ❌ General Application→Full-Stack Template | Domain misdetection: detected 'General Application' but should be 'Full-Stack... |
| `GoogleCloudPlatform/microservices-demo` | ✅ | 382 | 0s | — | ❌ E-Commerce→Microservices Demo | Domain misdetection: detected 'E-Commerce' but should be 'Microservices Demo'... |
| `dotnet/eShop` | ✅ | 213 | 0s | — | ❌ Trading/Finance→E-Commerce Microservices | Domain misdetection: detected 'Trading/Finance' but should be 'E-Commerce Mic... |
| `gothinkster/realworld` | ✅ | 247 | 0s | — | ❌ General Application→Full-Stack Spec/Demo | Domain misdetection: detected 'General Application' but should be 'Full-Stack... |
| `amplication/amplication` | ✅ | 970 | 5s | Monorepo | ❌ Developer Tools→Code Generation Platform | Domain misdetection: detected 'Developer Tools' but should be 'Code Generatio... |
| `backstage/backstage` | ✅ | 5215 | 17s | — | ❌ Trading/Finance→Developer Portal | Domain misdetection: detected 'Trading/Finance' but should be 'Developer Port... |
| `supabase/supabase` | ✅ | 5911 | 58s | Monorepo | ❌ General Application→Backend-as-a-Service | Domain misdetection: detected 'General Application' but should be 'Backend-as... |

### 4.6 Specialized & Edge Cases

**Pass rate:** 10/10 | **Domain accuracy:** 0/10

| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |
|---|---|---|---|---|---|---|
| `prisma/prisma` | ✅ | 2254 | 5s | — | ❌ General Application→ORM / Database Toolkit | Domain misdetection: detected 'General Application' but should be 'ORM / Data... |
| `trpc/trpc` | ✅ | 1700 | 3s | — | ❌ General Application→Type-Safe API Framework | Domain misdetection: detected 'General Application' but should be 'Type-Safe ... |
| `dagger/dagger` | ✅ | 621 | 2s | — | ❌ Trading/Finance→CI/CD Engine | Domain misdetection: detected 'Trading/Finance' but should be 'CI/CD Engine';... |
| `minio/minio` | ✅ | 314 | 0s | — | ❌ General Application→Object Storage | Domain misdetection: detected 'General Application' but should be 'Object Sto... |
| `pocketbase/pocketbase` | ✅ | 334 | 5s | — | ❌ General Application→Backend-as-a-Service (Go) | Domain misdetection: detected 'General Application' but should be 'Backend-as... |
| `tailwindlabs/tailwindcss` | ✅ | 782 | 2s | — | ❌ General Application→CSS Framework | Domain misdetection: detected 'General Application' but should be 'CSS Framew... |
| `denoland/deno` | ✅ | 556 | 76s | — | ❌ General Application→JavaScript Runtime | Domain misdetection: detected 'General Application' but should be 'JavaScript... |
| `gitbutler/gitbutler` | ✅ | 770 | 0s | — | ❌ General Application→Git Client | Domain misdetection: detected 'General Application' but should be 'Git Client... |
| `juspay/hyperswitch` | ✅ | 604 | 6s | — | ❌ General Application→Payment Switch | Domain misdetection: detected 'General Application' but should be 'Payment Sw... |
| `chartdb/chartdb` | ✅ | 984 | 7s | — | ❌ General Application→Database Visualization | Domain misdetection: detected 'General Application' but should be 'Database V... |

## 5. Detailed Per-Repo Findings

### 5.1 `calcom/cal.com` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 22s) |
| **Files** | 9799 |
| **Output** | 1072 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:10.4.20 |
| **Domain** | E-Commerce (correct: Scheduling/Calendar) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, DTOS, ENUMS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:8 Controllers:0 Interfaces:8 Types:41 Enums:2 |
| **Runbook** | 13 commands, 62 CI/CD, 1 env var sections |
| **Logic** | 15915 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'E-Commerce' but should be 'Scheduling/Calendar'
- ❌ Domain vocabulary is wrong for this project type
- ❌ Enum duplication detected (same enum listed multiple times)

**Missing Extractors:**
- 🔧 Prisma: Prisma ORM models not extracted
- 🔧 tRPC: tRPC routers/procedures not extracted

**Suggested Improvements:**
- 💡 Add extractors for: Prisma, tRPC
- 💡 Add domain keywords for 'Scheduling/Calendar' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.2 `medusajs/medusa` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 27s) |
| **Files** | 19642 |
| **Output** | 674 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: E-Commerce) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 18 commands, 17 CI/CD, 0 env var sections |
| **Logic** | 9808 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'E-Commerce'
- ❌ Zero entities extracted from 19642 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'E-Commerce' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.3 `formbricks/formbricks` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 2771 |
| **Output** | 733 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Survey/Forms) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 23 commands, 19 CI/CD, 1 env var sections |
| **Logic** | 3272 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Survey/Forms'
- ❌ Zero entities extracted from 2771 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Survey/Forms' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.4 `documenso/documenso` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 2203 |
| **Output** | 699 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Document Signing) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 21 commands, 16 CI/CD, 1 env var sections |
| **Logic** | 2250 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Document Signing'
- ❌ Zero entities extracted from 2203 files — expected TS/JS entities from package.json project

**Missing Extractors:**
- 🔧 Prisma: Prisma ORM models not extracted
- 🔧 tRPC: tRPC routers/procedures not extracted

**Suggested Improvements:**
- 💡 Add extractors for: Prisma, tRPC
- 💡 Add domain keywords for 'Document Signing' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.5 `twentyhq/twenty` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 31s) |
| **Files** | 14856 |
| **Output** | 1439 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:11.1.9 |
| **Domain** | AI/ML Platform (correct: CRM) ❌ |
| **Sections** | 23 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, CONTROLLERS, DATA_FLOWS, DTOS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, NESTJS_MODULES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_TYPES, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:2 Controllers:26 Interfaces:6 Types:108 Enums:0 |
| **Runbook** | 14 commands, 24 CI/CD, 0 env var sections |
| **Logic** | 14599 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'AI/ML Platform' but should be 'CRM'

**Suggested Improvements:**
- 💡 Add domain keywords for 'CRM' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor

---

### 5.6 `hoppscotch/hoppscotch` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 2047 |
| **Output** | 981 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:11.1.12 |
| **Domain** | Trading/Finance (correct: API Development Tool) ❌ |
| **Sections** | 21 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, CONTROLLERS, DATA_FLOWS, DTOS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, NESTJS_MODULES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:4 Controllers:2 Interfaces:10 Types:41 Enums:0 |
| **Runbook** | 21 commands, 5 CI/CD, 1 env var sections |
| **Logic** | 2833 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'API Development Tool'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'API Development Tool' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor

---

### 5.7 `immich-app/immich` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 3597 |
| **Output** | 1230 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:11.0.4 |
| **Domain** | Trading/Finance (correct: Photo Management) ❌ |
| **Sections** | 23 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, CONTROLLERS, DATA_FLOWS, DTOS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:206 Controllers:35 Interfaces:15 Types:16 Enums:0 |
| **Runbook** | 0 commands, 23 CI/CD, 0 env var sections |
| **Logic** | 4694 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Photo Management'
- ❌ Domain vocabulary is wrong for this project type

**Missing Extractors:**
- 🔧 Svelte: Svelte components not extracted

**Suggested Improvements:**
- 💡 Add extractors for: Svelte
- 💡 Add domain keywords for 'Photo Management' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor

---

### 5.8 `maybe-finance/maybe` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 1s) |
| **Files** | 1348 |
| **Output** | 582 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Personal Finance) ❌ |
| **Sections** | 12 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROJECT, PROJECT_STRUCTURE, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 2 commands, 3 CI/CD, 1 env var sections |
| **Logic** | 1660 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Personal Finance'
- ❌ Domain vocabulary is wrong for this project type
- ❌ Zero entities extracted from 1348 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Personal Finance' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.9 `appwrite/appwrite` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 51545 |
| **Output** | 273 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Backend-as-a-Service) ❌ |
| **Sections** | 11 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROJECT, PROJECT_STRUCTURE, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 16 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Domain misdetection: detected 'General Application' but should be 'Backend-as-a-Service'
- ❌ Zero entities extracted from 51545 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend-as-a-Service' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.10 `logto-io/logto` (Full-Stack Applications)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 12s) |
| **Files** | 6130 |
| **Output** | 706 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Authentication/Identity) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 22 commands, 19 CI/CD, 0 env var sections |
| **Logic** | 3655 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Authentication/Identity'
- ❌ Zero entities extracted from 6130 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Authentication/Identity' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.11 `nestjs/nest` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 1708 |
| **Output** | 2385 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:11.1.12 |
| **Domain** | AI/ML Platform (correct: Backend Framework) ❌ |
| **Sections** | 25 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, CONTROLLERS, DATA_FLOWS, DTOS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, NESTJS_MODULES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, SCHEMAS, TODOS, TYPES |
| **Entities** | Schemas:1 DTOs:25 Controllers:35 Interfaces:4 Types:4 Enums:0 |
| **Runbook** | 9 commands, 2 CI/CD, 0 env var sections |
| **Logic** | 1895 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'AI/ML Platform' but should be 'Backend Framework'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend Framework' to BusinessDomainExtractor

---

### 5.12 `fastapi/fastapi` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 1s) |
| **Files** | 2107 |
| **Output** | 830 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Backend Framework) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 19 CI/CD, 0 env var sections |
| **Logic** | 865 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Backend Framework'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.13 `pallets/flask` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 166 |
| **Output** | 464 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Developer Tools (correct: Backend Framework) ❌ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 4 CI/CD, 0 env var sections |
| **Logic** | 307 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Developer Tools' but should be 'Backend Framework'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.14 `tiangolo/full-stack-fastapi-template` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 200 |
| **Output** | 716 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Full-Stack Template) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 3 commands, 12 CI/CD, 0 env var sections |
| **Logic** | 302 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Full-Stack Template'
- ❌ Zero entities extracted from 200 files — expected TS/JS entities from package.json project

**Missing Extractors:**
- 🔧 SQLAlchemy: SQLAlchemy models not extracted

**Suggested Improvements:**
- 💡 Add extractors for: SQLAlchemy
- 💡 Add domain keywords for 'Full-Stack Template' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.15 `GoogleCloudPlatform/microservices-demo` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 356 |
| **Output** | 382 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | E-Commerce (correct: Microservices Demo) ❌ |
| **Sections** | 13 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, PYTHON_API, RUNBOOK |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 7 CI/CD, 0 env var sections |
| **Logic** | 111 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'E-Commerce' but should be 'Microservices Demo'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Microservices Demo' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.16 `dotnet/eShop` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 1015 |
| **Output** | 213 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: E-Commerce Microservices) ❌ |
| **Sections** | 13 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROJECT, PROJECT_STRUCTURE, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 4 CI/CD, 0 env var sections |
| **Logic** | 2 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'E-Commerce Microservices'
- ❌ Domain vocabulary is wrong for this project type
- ❌ Zero entities extracted from 1015 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'E-Commerce Microservices' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.17 `gothinkster/realworld` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 180 |
| **Output** | 247 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Full-Stack Spec/Demo) ❌ |
| **Sections** | 14 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, PROGRESS, PROGRESS_DETAIL, PROJECT, RUNBOOK, TODOS |
| **Missing Sections** | ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:5 Types:0 Enums:0 |
| **Runbook** | 10 commands, 3 CI/CD, 0 env var sections |
| **Logic** | 8 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Full-Stack Spec/Demo'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Full-Stack Spec/Demo' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.18 `amplication/amplication` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 4120 |
| **Output** | 970 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:9.4.0 |
| **Domain** | Developer Tools (correct: Code Generation Platform) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, CONTROLLERS, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, NESTJS_MODULES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:19 Interfaces:2 Types:19 Enums:0 |
| **Runbook** | 9 commands, 16 CI/CD, 0 env var sections |
| **Logic** | 3590 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Developer Tools' but should be 'Code Generation Platform'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Code Generation Platform' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor

---

### 5.19 `backstage/backstage` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 17s) |
| **Files** | 9538 |
| **Output** | 5215 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Developer Portal) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:199 Types:18 Enums:0 |
| **Runbook** | 15 commands, 45 CI/CD, 0 env var sections |
| **Logic** | 9608 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Developer Portal'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Developer Portal' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.20 `supabase/supabase` (Microservices & Backend)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 58s) |
| **Files** | 13990 |
| **Output** | 5911 lines |
| **Type** | Monorepo |
| **Stack** | angular:21.1.1 |
| **Domain** | General Application (correct: Backend-as-a-Service) ❌ |
| **Sections** | 21 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, COMPONENTS, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:1 Types:0 Enums:0 |
| **Runbook** | 15 commands, 39 CI/CD, 0 env var sections |
| **Logic** | 29073 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Backend-as-a-Service'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend-as-a-Service' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.21 `langchain-ai/langchain` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 11s) |
| **Files** | 1900 |
| **Output** | 863 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: AI/LLM Framework) ❌ |
| **Sections** | 14 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 15 CI/CD, 0 env var sections |
| **Logic** | 3991 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'AI/LLM Framework'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'AI/LLM Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.22 `openai/openai-cookbook` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=-1, 0s) |
| **Files** | 2730 |
| **Output** | 541 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: AI Documentation/Tutorials) ❌ |
| **Sections** | 14 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 3 CI/CD, 0 env var sections |
| **Logic** | 599 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'AI Documentation/Tutorials'

**Suggested Improvements:**
- 💡 Add domain keywords for 'AI Documentation/Tutorials' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.23 `run-llama/llama_index` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 10s) |
| **Files** | 9059 |
| **Output** | 961 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | AI/ML Platform (correct: AI/RAG Framework) ✅ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 12 CI/CD, 0 env var sections |
| **Logic** | 7698 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Suggested Improvements:**
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.24 `huggingface/transformers` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 51s) |
| **Files** | 3972 |
| **Output** | 1212 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: ML Framework) ❌ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 53 CI/CD, 0 env var sections |
| **Logic** | 20783 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'ML Framework'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'ML Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.25 `mlflow/mlflow` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 15s) |
| **Files** | 4812 |
| **Output** | 1310 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: ML Experiment Tracking) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 46 CI/CD, 0 env var sections |
| **Logic** | 13092 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'ML Experiment Tracking'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'ML Experiment Tracking' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.26 `bentoml/BentoML` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 2s) |
| **Files** | 674 |
| **Output** | 652 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | AI/ML Platform (correct: ML Model Serving) ❌ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | ERROR_HANDLING, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 5 CI/CD, 0 env var sections |
| **Logic** | 5268 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'AI/ML Platform' but should be 'ML Model Serving'

**Suggested Improvements:**
- 💡 Add domain keywords for 'ML Model Serving' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.27 `ray-project/ray` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 11s) |
| **Files** | 7311 |
| **Output** | 1046 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Distributed Computing) ❌ |
| **Sections** | 14 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, GRPC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, CONTEXT, ERROR_HANDLING, IMPLEMENTATION_LOGIC, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 2 commands, 3 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Domain misdetection: detected 'General Application' but should be 'Distributed Computing'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Distributed Computing' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.28 `qdrant/qdrant` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=-1, 0s) |
| **Files** | 1108 |
| **Output** | 278 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | AI/ML Platform (correct: Vector Database) ❌ |
| **Sections** | 10 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, GRPC, INFRASTRUCTURE, PROGRESS, PROJECT, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 14 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Domain misdetection: detected 'AI/ML Platform' but should be 'Vector Database'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Vector Database' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.29 `chroma-core/chroma` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 2s) |
| **Files** | 2028 |
| **Output** | 942 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Vector Database) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 21 CI/CD, 0 env var sections |
| **Logic** | 2313 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Vector Database'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Vector Database' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.30 `open-webui/open-webui` (AI/ML Projects)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 4824 |
| **Output** | 1395 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: AI Chat Interface) ❌ |
| **Sections** | 22 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_API, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 8 commands, 6 CI/CD, 1 env var sections |
| **Logic** | 571 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'AI Chat Interface'
- ❌ Zero entities extracted from 4824 files — expected TS/JS entities from package.json project

**Missing Extractors:**
- 🔧 Svelte: Svelte components not extracted

**Suggested Improvements:**
- 💡 Add extractors for: Svelte
- 💡 Add domain keywords for 'AI Chat Interface' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.31 `grafana/grafana` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 28s) |
| **Files** | 19701 |
| **Output** | 7677 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Analytics/BI (correct: Observability Platform) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 10 commands, 81 CI/CD, 0 env var sections |
| **Logic** | 18392 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Analytics/BI' but should be 'Observability Platform'
- ❌ Zero entities extracted from 19701 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Observability Platform' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.32 `prometheus/prometheus` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 1s) |
| **Files** | 1575 |
| **Output** | 490 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Developer Tools (correct: Monitoring System) ❌ |
| **Sections** | 12 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, RUNBOOK, TODOS |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 13 CI/CD, 0 env var sections |
| **Logic** | 550 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Developer Tools' but should be 'Monitoring System'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Monitoring System' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.33 `traefik/traefik` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 2145 |
| **Output** | 365 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Reverse Proxy/Load Balancer) ❌ |
| **Sections** | 13 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, RUNBOOK |
| **Missing Sections** | CONTEXT, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 13 CI/CD, 0 env var sections |
| **Logic** | 214 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Reverse Proxy/Load Balancer'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Reverse Proxy/Load Balancer' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.34 `hashicorp/terraform` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 1s) |
| **Files** | 4278 |
| **Output** | 346 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Infrastructure as Code) ❌ |
| **Sections** | 10 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, GRPC, INFRASTRUCTURE, PROGRESS, PROJECT, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 10 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Infrastructure as Code'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Infrastructure as Code' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.35 `docker/compose` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 664 |
| **Output** | 288 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Container Orchestration) ❌ |
| **Sections** | 9 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, INFRASTRUCTURE, PROGRESS, PROJECT, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 5 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Domain misdetection: detected 'General Application' but should be 'Container Orchestration'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Container Orchestration' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.36 `pulumi/pulumi` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 107s) |
| **Files** | 20229 |
| **Output** | 879 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Infrastructure as Code) ❌ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS |
| **Missing Sections** | OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 28 CI/CD, 0 env var sections |
| **Logic** | 22904 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Infrastructure as Code'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Infrastructure as Code' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.37 `n8n-io/n8n` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 31s) |
| **Files** | 10832 |
| **Output** | 1234 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Workflow Automation) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:45 Types:58 Enums:0 |
| **Runbook** | 13 commands, 50 CI/CD, 0 env var sections |
| **Logic** | 33085 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Workflow Automation'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'Workflow Automation' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.38 `nocodb/nocodb` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 13s) |
| **Files** | 3625 |
| **Output** | 1012 lines |
| **Type** | Monorepo |
| **Stack** | nestjs:10.4.17 |
| **Domain** | AI/ML Platform (correct: Database UI/Airtable Alternative) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, CONTROLLERS, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, NESTJS_MODULES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:1 Interfaces:9 Types:5 Enums:0 |
| **Runbook** | 11 commands, 31 CI/CD, 0 env var sections |
| **Logic** | 17794 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'AI/ML Platform' but should be 'Database UI/Airtable Alternative'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Database UI/Airtable Alternative' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor

---

### 5.39 `strapi/strapi` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 7s) |
| **Files** | 4384 |
| **Output** | 794 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Headless CMS) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 10 commands, 21 CI/CD, 0 env var sections |
| **Logic** | 5033 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Headless CMS'
- ❌ Zero entities extracted from 4384 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Headless CMS' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.40 `directus/directus` (DevTools & Infrastructure)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 4s) |
| **Files** | 2876 |
| **Output** | 753 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Data Platform/Headless CMS) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 17 commands, 15 CI/CD, 0 env var sections |
| **Logic** | 3995 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Data Platform/Headless CMS'
- ❌ Zero entities extracted from 2876 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Data Platform/Headless CMS' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.41 `angular/angular` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ❌ Failed (exit=1, 17s) |
| **Files** | 0 |
| **Output** | 30 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Not detected (correct: Frontend Framework) ❌ |
| **Sections** | 1 found: CodeTrellis |
| **Missing Sections** | ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, ERROR_HANDLING, IMPLEMENTATION_LOGIC, OVERVIEW, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 0 CI/CD, 0 env var sections |
| **Logic** | 0 snippets |
| **BPL** | 0 practices |
| **Traceback** | ⚠️ YES |

**Issues:**
- ❌ Python traceback in scan stderr
- ❌ Missing [RUNBOOK] section — AI cannot know how to run project
- ❌ Missing [IMPLEMENTATION_LOGIC] — no code flow analysis
- ❌ Missing [BEST_PRACTICES] — no BPL practices selected
- ❌ No business domain detected
- ❌ Domain misdetection: detected 'Not detected' but should be 'Frontend Framework'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Frontend Framework' to BusinessDomainExtractor

---

### 5.42 `vercel/next.js` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 62s) |
| **Files** | 9530 |
| **Output** | 1120 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Developer Tools (correct: React Meta-Framework) ❌ |
| **Sections** | 20 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, PYTHON_TYPES, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 23 commands, 33 CI/CD, 0 env var sections |
| **Logic** | 67060 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Developer Tools' but should be 'React Meta-Framework'
- ❌ Zero entities extracted from 9530 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'React Meta-Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.43 `vuejs/core` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 3s) |
| **Files** | 455 |
| **Output** | 1445 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Frontend Framework) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 13 commands, 9 CI/CD, 0 env var sections |
| **Logic** | 1394 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Frontend Framework'
- ❌ Zero entities extracted from 455 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Frontend Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.44 `sveltejs/svelte` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 3s) |
| **Files** | 609 |
| **Output** | 740 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: Frontend Framework/Compiler) ❌ |
| **Sections** | 15 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Missing Sections** | ERROR_HANDLING |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 9 commands, 4 CI/CD, 0 env var sections |
| **Logic** | 2056 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'Frontend Framework/Compiler'
- ❌ Domain vocabulary is wrong for this project type
- ❌ Zero entities extracted from 609 files — expected TS/JS entities from package.json project

**Missing Extractors:**
- 🔧 Svelte: Svelte components not extracted

**Suggested Improvements:**
- 💡 Add extractors for: Svelte
- 💡 Add domain keywords for 'Frontend Framework/Compiler' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.45 `shadcn-ui/ui` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 11s) |
| **Files** | 9308 |
| **Output** | 1118 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: UI Component Library) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 16 commands, 8 CI/CD, 0 env var sections |
| **Logic** | 7402 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'UI Component Library'
- ❌ Zero entities extracted from 9308 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'UI Component Library' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.46 `ionic-team/ionic-framework` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 1102 |
| **Output** | 2060 lines |
| **Type** | Monorepo |
| **Stack** | angular:19.0.0 |
| **Domain** | General Application (correct: Cross-Platform UI Framework) ❌ |
| **Sections** | 21 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, COMPONENTS, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 14 commands, 12 CI/CD, 0 env var sections |
| **Logic** | 3306 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Cross-Platform UI Framework'
- ❌ Zero entities extracted from 1102 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Cross-Platform UI Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.47 `ant-design/ant-design` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 3754 |
| **Output** | 2391 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: UI Component Library) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 12 commands, 33 CI/CD, 0 env var sections |
| **Logic** | 2750 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'UI Component Library'
- ❌ Zero entities extracted from 3754 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'UI Component Library' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.48 `storybookjs/storybook` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 7s) |
| **Files** | 4887 |
| **Output** | 739 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: UI Component Development) ❌ |
| **Sections** | 18 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, COMPONENTS, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 8 commands, 14 CI/CD, 0 env var sections |
| **Logic** | 7272 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'UI Component Development'
- ❌ Zero entities extracted from 4887 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'UI Component Development' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.49 `excalidraw/excalidraw` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 30s) |
| **Files** | 1071 |
| **Output** | 1500 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Drawing/Whiteboard Tool) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 6 commands, 11 CI/CD, 0 env var sections |
| **Logic** | 2088 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Drawing/Whiteboard Tool'
- ❌ Zero entities extracted from 1071 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Drawing/Whiteboard Tool' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.50 `TanStack/query` (Frontend Frameworks)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 2s) |
| **Files** | 1698 |
| **Output** | 721 lines |
| **Type** | Monorepo |
| **Stack** | angular:20.0.0 |
| **Domain** | Developer Tools (correct: Data Fetching Library) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, ANGULAR_SERVICES, BEST_PRACTICES, BUSINESS_DOMAIN, COMPONENTS, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:4 Types:0 Enums:0 |
| **Runbook** | 11 commands, 4 CI/CD, 0 env var sections |
| **Logic** | 926 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Developer Tools' but should be 'Data Fetching Library'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Data Fetching Library' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.51 `prisma/prisma` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 1360 |
| **Output** | 2254 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: ORM / Database Toolkit) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 24 commands, 17 CI/CD, 0 env var sections |
| **Logic** | 3091 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'ORM / Database Toolkit'
- ❌ Zero entities extracted from 1360 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'ORM / Database Toolkit' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.52 `trpc/trpc` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 3s) |
| **Files** | 1081 |
| **Output** | 1700 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Type-Safe API Framework) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 21 commands, 11 CI/CD, 0 env var sections |
| **Logic** | 663 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Type-Safe API Framework'
- ❌ Zero entities extracted from 1081 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Type-Safe API Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.53 `dagger/dagger` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 2s) |
| **Files** | 5739 |
| **Output** | 621 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | Trading/Finance (correct: CI/CD Engine) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, PYTHON_FUNCTIONS, PYTHON_TYPES, RUNBOOK, TODOS |
| **Missing Sections** | CONTEXT, OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 1 commands, 11 CI/CD, 0 env var sections |
| **Logic** | 2337 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'Trading/Finance' but should be 'CI/CD Engine'
- ❌ Domain vocabulary is wrong for this project type

**Suggested Improvements:**
- 💡 Add domain keywords for 'CI/CD Engine' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.54 `minio/minio` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 0s) |
| **Files** | 1364 |
| **Output** | 314 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Object Storage) ❌ |
| **Sections** | 12 found: AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROJECT, PYTHON_API, PYTHON_FUNCTIONS, RUNBOOK |
| **Missing Sections** | ACTIONABLE_ITEMS, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 17 CI/CD, 0 env var sections |
| **Logic** | 14 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Object Storage'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Object Storage' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.55 `pocketbase/pocketbase` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 5s) |
| **Files** | 761 |
| **Output** | 334 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Backend-as-a-Service (Go)) ❌ |
| **Sections** | 12 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, DATA_FLOWS, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, RUNBOOK, TODOS |
| **Missing Sections** | CONTEXT, ERROR_HANDLING, OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 1 CI/CD, 0 env var sections |
| **Logic** | 1018 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Backend-as-a-Service (Go)'

**Suggested Improvements:**
- 💡 Add domain keywords for 'Backend-as-a-Service (Go)' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.56 `tailwindlabs/tailwindcss` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 2s) |
| **Files** | 404 |
| **Output** | 782 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: CSS Framework) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 21 commands, 5 CI/CD, 0 env var sections |
| **Logic** | 618 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'CSS Framework'
- ❌ Zero entities extracted from 404 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'CSS Framework' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.57 `denoland/deno` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 76s) |
| **Files** | 1366 |
| **Output** | 556 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: JavaScript Runtime) ❌ |
| **Sections** | 14 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, PROGRESS, PROGRESS_DETAIL, PROJECT, RUNBOOK, TODOS |
| **Missing Sections** | OVERVIEW, PROJECT_STRUCTURE |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 10 CI/CD, 0 env var sections |
| **Logic** | 17507 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'JavaScript Runtime'

**Suggested Improvements:**
- 💡 Add domain keywords for 'JavaScript Runtime' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.58 `gitbutler/gitbutler` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=-1, 0s) |
| **Files** | 2059 |
| **Output** | 770 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Git Client) ❌ |
| **Sections** | 16 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 12 commands, 8 CI/CD, 0 env var sections |
| **Logic** | 2616 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Git Client'
- ❌ Zero entities extracted from 2059 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Git Client' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.59 `juspay/hyperswitch` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 6s) |
| **Files** | 13018 |
| **Output** | 604 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Payment Switch) ❌ |
| **Sections** | 17 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CONTEXT, DATA_FLOWS, ERROR_HANDLING, GRPC, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 0 commands, 17 CI/CD, 0 env var sections |
| **Logic** | 287 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Payment Switch'
- ❌ Zero entities extracted from 13018 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Payment Switch' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

### 5.60 `chartdb/chartdb` (Specialized & Edge Cases)

| Metric | Value |
|---|---|
| **Scan Status** | ✅ Success (exit=0, 7s) |
| **Files** | 630 |
| **Output** | 984 lines |
| **Type** | Not detected |
| **Stack** | Not detected |
| **Domain** | General Application (correct: Database Visualization) ❌ |
| **Sections** | 19 found: ACTIONABLE_ITEMS, AI_INSTRUCTION, BEST_PRACTICES, BUSINESS_DOMAIN, CLASSES, CONTEXT, DATA_FLOWS, ERROR_HANDLING, IMPLEMENTATION_LOGIC, INFRASTRUCTURE, INTERFACES, OVERVIEW, PROGRESS, PROGRESS_DETAIL, PROJECT, PROJECT_STRUCTURE, RUNBOOK, TODOS, TYPES |
| **Entities** | Schemas:0 DTOs:0 Controllers:0 Interfaces:0 Types:0 Enums:0 |
| **Runbook** | 7 commands, 4 CI/CD, 0 env var sections |
| **Logic** | 528 snippets |
| **BPL** | 15 practices |
| **Traceback** | ✅ No |

**Issues:**
- ❌ Domain misdetection: detected 'General Application' but should be 'Database Visualization'
- ❌ Possible TODO contamination: 503 TODOs for 630 files
- ❌ Zero entities extracted from 630 files — expected TS/JS entities from package.json project

**Suggested Improvements:**
- 💡 Add domain keywords for 'Database Visualization' to BusinessDomainExtractor
- 💡 Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor
- 💡 Investigate why 0 controllers — may need tRPC router or framework-specific extractor

---

## 6. Improvement Roadmap

Based on the findings above, here is the prioritized improvement roadmap:

### 6.1 New Extractors Needed

| Priority | Extractor | Repos Affected | Effort Estimate |
|---|---|---|---|
| 🟡 P2 | Svelte extractor | 3 repos | Medium (8-16h) |
| 🟡 P2 | Prisma extractor | 2 repos | Medium (8-16h) |
| 🟡 P2 | tRPC extractor | 2 repos | Medium (8-16h) |
| 🟢 P3 | SQLAlchemy extractor | 1 repos | TBD |

### 6.2 Domain Detection Improvements

| Domain | Currently Detected As | Repos | Fix |
|---|---|---|---|
| Backend-as-a-Service | General Application | `appwrite/appwrite`, `supabase/supabase` | Add domain keywords |
| UI Component Library | General Application | `shadcn-ui/ui`, `ant-design/ant-design` | Add domain keywords |
| Scheduling/Calendar | E-Commerce | `calcom/cal.com` | Add domain keywords |
| E-Commerce | General Application | `medusajs/medusa` | Add domain keywords |
| Survey/Forms | General Application | `formbricks/formbricks` | Add domain keywords |
| Document Signing | General Application | `documenso/documenso` | Add domain keywords |
| CRM | AI/ML Platform | `twentyhq/twenty` | Add domain keywords |
| API Development Tool | Trading/Finance | `hoppscotch/hoppscotch` | Add domain keywords |
| Photo Management | Trading/Finance | `immich-app/immich` | Add domain keywords |
| Personal Finance | Trading/Finance | `maybe-finance/maybe` | Add domain keywords |
| Authentication/Identity | General Application | `logto-io/logto` | Add domain keywords |
| Backend Framework | AI/ML Platform | `nestjs/nest` | Add domain keywords |
| Backend Framework | Trading/Finance | `fastapi/fastapi` | Add domain keywords |
| Backend Framework | Developer Tools | `pallets/flask` | Add domain keywords |
| Full-Stack Template | General Application | `tiangolo/full-stack-fastapi-template` | Add domain keywords |
| Microservices Demo | E-Commerce | `GoogleCloudPlatform/microservices-demo` | Add domain keywords |
| E-Commerce Microservices | Trading/Finance | `dotnet/eShop` | Add domain keywords |
| Full-Stack Spec/Demo | General Application | `gothinkster/realworld` | Add domain keywords |
| Code Generation Platform | Developer Tools | `amplication/amplication` | Add domain keywords |
| Developer Portal | Trading/Finance | `backstage/backstage` | Add domain keywords |
| AI/LLM Framework | Trading/Finance | `langchain-ai/langchain` | Add domain keywords |
| AI Documentation/Tutorials | General Application | `openai/openai-cookbook` | Add domain keywords |
| ML Framework | Trading/Finance | `huggingface/transformers` | Add domain keywords |
| ML Experiment Tracking | Trading/Finance | `mlflow/mlflow` | Add domain keywords |
| ML Model Serving | AI/ML Platform | `bentoml/BentoML` | Add domain keywords |
| Distributed Computing | General Application | `ray-project/ray` | Add domain keywords |
| Vector Database | AI/ML Platform | `qdrant/qdrant` | Add domain keywords |
| Vector Database | Trading/Finance | `chroma-core/chroma` | Add domain keywords |
| AI Chat Interface | General Application | `open-webui/open-webui` | Add domain keywords |
| Observability Platform | Analytics/BI | `grafana/grafana` | Add domain keywords |
| Monitoring System | Developer Tools | `prometheus/prometheus` | Add domain keywords |
| Reverse Proxy/Load Balancer | General Application | `traefik/traefik` | Add domain keywords |
| Infrastructure as Code | Trading/Finance | `hashicorp/terraform` | Add domain keywords |
| Container Orchestration | General Application | `docker/compose` | Add domain keywords |
| Infrastructure as Code | General Application | `pulumi/pulumi` | Add domain keywords |
| Workflow Automation | Trading/Finance | `n8n-io/n8n` | Add domain keywords |
| Database UI/Airtable Alternative | AI/ML Platform | `nocodb/nocodb` | Add domain keywords |
| Headless CMS | General Application | `strapi/strapi` | Add domain keywords |
| Data Platform/Headless CMS | General Application | `directus/directus` | Add domain keywords |
| React Meta-Framework | Developer Tools | `vercel/next.js` | Add domain keywords |
| Frontend Framework | General Application | `vuejs/core` | Add domain keywords |
| Frontend Framework/Compiler | Trading/Finance | `sveltejs/svelte` | Add domain keywords |
| Cross-Platform UI Framework | General Application | `ionic-team/ionic-framework` | Add domain keywords |
| UI Component Development | General Application | `storybookjs/storybook` | Add domain keywords |
| Drawing/Whiteboard Tool | General Application | `excalidraw/excalidraw` | Add domain keywords |
| Data Fetching Library | Developer Tools | `TanStack/query` | Add domain keywords |
| ORM / Database Toolkit | General Application | `prisma/prisma` | Add domain keywords |
| Type-Safe API Framework | General Application | `trpc/trpc` | Add domain keywords |
| CI/CD Engine | Trading/Finance | `dagger/dagger` | Add domain keywords |
| Object Storage | General Application | `minio/minio` | Add domain keywords |
| Backend-as-a-Service (Go) | General Application | `pocketbase/pocketbase` | Add domain keywords |
| CSS Framework | General Application | `tailwindlabs/tailwindcss` | Add domain keywords |
| JavaScript Runtime | General Application | `denoland/deno` | Add domain keywords |
| Git Client | General Application | `gitbutler/gitbutler` | Add domain keywords |
| Payment Switch | General Application | `juspay/hyperswitch` | Add domain keywords |
| Database Visualization | General Application | `chartdb/chartdb` | Add domain keywords |

---

_Generated by CodeTrellis Phase D Validation Framework on 2026-02-09 13:24_
_Total repos: 60 | Passed: 59 | Failed: 1 | Domain accuracy: 1.7%_
_Use .codetrellis validate-repos --score-only` for automated scoring_
_Use .codetrellis validate-repos --analyze-only` for Gap Analysis Round 2_