# SuperMemory, Mem0, Zep, Cognee, Greptile vs CodeTrellis — Deep Competitive Analysis

> **Date:** 20 February 2026  
> **Analyst:** Research Session (Keshav Chaudhary)  
> **Sources:** Product websites, documentation, GitHub repos, pricing pages, research papers  
> **Scope:** AI context/memory infrastructure products compared against CodeTrellis Matrix

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Product Profiles](#2-product-profiles)
  - [2.1 SuperMemory AI](#21-supermemory-ai)
  - [2.2 Mem0](#22-mem0)
  - [2.3 Zep AI](#23-zep-ai)
  - [2.4 Cognee](#24-cognee)
  - [2.5 Greptile](#25-greptile)
  - [2.6 CodeTrellis Matrix](#26-codetrellis-matrix)
- [3. Architecture Comparison](#3-architecture-comparison)
- [4. Feature Matrix](#4-feature-matrix)
- [5. The Fundamental Category Distinction](#5-the-fundamental-category-distinction)
- [6. Pricing Comparison](#6-pricing-comparison)
- [7. Head-to-Head: Where Each Wins and Loses](#7-head-to-head-where-each-wins-and-loses)
- [8. What CodeTrellis Can Learn](#8-what-codetrellis-can-learn)
- [9. Strategic Positioning](#9-strategic-positioning)
- [10. The Convergence Opportunity](#10-the-convergence-opportunity)

---

## 1. Executive Summary

The AI context/memory space has exploded into several distinct product categories. After deep research into SuperMemory, Mem0, Zep, Cognee, and Greptile, a critical insight emerges:

**These tools solve fundamentally different problems than CodeTrellis, but they are all converging toward the same meta-problem: "How do you give AI the right context at the right time?"**

```
┌──────────────────────────────────────────────────────────────────┐
│                    THE CONTEXT PROBLEM                           │
│                                                                  │
│  SuperMemory / Mem0 / Zep      │  CodeTrellis Matrix             │
│  ─────────────────────────     │  ──────────────────             │
│  "Remember the USER"           │  "Understand the CODE"          │
│                                │                                  │
│  User preferences, history,    │  Project architecture, types,    │
│  behavior, relationships       │  APIs, patterns, logic flow      │
│                                │                                  │
│  Cognee                        │  Greptile                        │
│  ─────                         │  ────────                        │
│  "Learn from DATA"             │  "Understand PRs"                │
│  Knowledge graphs from any     │  Codebase graph for             │
│  document type                 │  code review                    │
│                                │                                  │
│              ALL ARE CONTEXT LAYERS.                              │
│              NONE DOES WHAT CODETRELLIS DOES.                     │
└──────────────────────────────────────────────────────────────────┘
```

### The Headline

| Product         | What It Remembers                         | For Whom                              | Core Tech                              | CodeTrellis Overlap                                |
| --------------- | ----------------------------------------- | ------------------------------------- | -------------------------------------- | -------------------------------------------------- |
| **SuperMemory** | User interactions, preferences, profiles  | App builders (chatbots, assistants)   | Vector-Graph hybrid engine             | **0%** — different problem                         |
| **Mem0**        | User memory across LLM sessions           | App builders (agents, chatbots)       | Memory compression + graph             | **0%** — different problem                         |
| **Zep**         | User facts, relationships, temporal state | Enterprise agent builders             | Temporal knowledge graph               | **5%** — fact extraction concept similar           |
| **Cognee**      | Knowledge from any documents              | Developers building knowledge systems | Knowledge graph + ontology             | **15%** — graph-based understanding overlaps       |
| **Greptile**    | Codebase structure for PR review          | Engineering teams                     | Codebase graph                         | **40%** — closest competitor in code understanding |
| **CodeTrellis** | Everything about a codebase, pre-computed | Developers using ANY AI tool          | Deterministic multi-parser compression | **Unique** — only full-codebase pre-computation    |

---

## 2. Product Profiles

### 2.1 SuperMemory AI

**Website:** supermemory.ai  
**Founded by:** Dhravya Shah  
**Funding:** YC-backed, 70+ YC companies as customers  
**Tagline:** "The context engineering infrastructure for your AI agent"

#### What It Does

SuperMemory is a **user memory API** for AI applications. It stores, evolves, and retrieves memories about individual users across AI conversations and interactions.

```
Developer's App → SuperMemory API → User Memory Store
     ↕                                    ↕
User talks to chatbot              Memory is recalled
"I prefer dark mode"               next time user returns
```

#### Technical Architecture

| Component            | Details                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------- |
| **Storage**          | Postgres + custom vector engine on Cloudflare Durable Objects                            |
| **Scale**            | 50M tokens per user, 5B tokens daily globally                                            |
| **Retrieval**        | Sub-300ms recall, semantic + keyword hybrid search                                       |
| **Data Processing**  | Ingest → Embed → Enrich (graph links) → Index → Recall → Evolve                          |
| **Connectors**       | Google Drive, Notion, OneDrive, custom integrations                                      |
| **Memory vs RAG**    | Distinguishes between Documents (static RAG) and Memories (stateful, temporal, personal) |
| **SDKs**             | TypeScript, Python, cURL; OpenAI SDK, Anthropic, AI SDK, Claude Agents SDK               |
| **Memory Evolution** | Memories update, extend, derive, and expire over time                                    |

#### Pricing

| Tier       | Price   | Tokens          | Queries          |
| ---------- | ------- | --------------- | ---------------- |
| Free       | $0/mo   | 1M processed    | 10K searches     |
| Pro        | $19/mo  | 2M processed    | 100K searches    |
| Scale      | $399/mo | 80M processed   | 20M searches     |
| Enterprise | Custom  | Unlimited       | Unlimited        |
| Overages   | —       | $0.01/1K tokens | $0.10/1K queries |

#### Key Differentiator

Their Memory vs RAG distinction is intelligent:

- **RAG**: "What do I know?" (static documents, universal)
- **Memory**: "What do I remember about YOU?" (stateful, temporal, personal)

Example: Day 1: "I love Adidas." Day 30: "My Adidas broke." Day 45: "Recommend sneakers?" → RAG returns Adidas (most similar), Memory returns Nike (knows context shifted).

#### Relevance to CodeTrellis

**Almost zero.** SuperMemory is for remembering **users** in consumer/enterprise apps (chatbots, e-commerce, healthcare). CodeTrellis is for understanding **codebases** to help developers write better code. The only conceptual overlap is "structured context injection into AI" — but the what, when, and for whom are entirely different.

---

### 2.2 Mem0

**Website:** mem0.ai  
**Funding:** $24M Series A led by Basis Set Ventures (YC-backed)  
**GitHub:** 40K+ stars, 100K+ developers  
**Tagline:** "AI Agents Forget. Mem0 Remembers."

#### What It Does

Mem0 is a **self-improving memory layer for LLM applications**. It compresses chat histories into optimized memory representations, reducing token usage by up to 80% while preserving context fidelity.

```
Conversation → Mem0 Memory Compression → Compact Representation
                                              ↓
Next Conversation → Recall relevant memory → Better response
```

#### Technical Architecture

| Component         | Details                                                                               |
| ----------------- | ------------------------------------------------------------------------------------- |
| **Core**          | Memory compression engine (extracts facts from conversations)                         |
| **Products**      | Mem0 Platform (managed), Mem0 Open Source (self-host), OpenMemory (team workspace)    |
| **Research**      | ECAI-accepted paper; 26% higher response quality than OpenAI memory, 90% fewer tokens |
| **Integrations**  | LangChain, CrewAI, Vercel AI SDK, 20+ partner frameworks                              |
| **SDKs**          | Python, JavaScript                                                                    |
| **Deployment**    | Kubernetes, air-gapped, private cloud; SOC 2 & HIPAA compliant                        |
| **Observability** | Track TTL, size, access for every memory; timestamped, versioned, exportable          |

#### Use Cases

- Healthcare: Patient history across visits
- Education: Student learning style adaptation
- Sales/CRM: Persistent prospect context
- Customer Support: Issue history recall

#### Key Differentiator

**Memory compression** — Mem0 doesn't just store conversations, it distills them into facts. "Cuts prompt tokens by up to 80%" while retaining essential details. Their research paper shows they outperform OpenAI's built-in memory on benchmarks.

#### Relevance to CodeTrellis

**Minimal direct overlap.** Mem0 compresses _user conversations_ into memory. CodeTrellis compresses _codebases_ into structured context. However, the **compression** concept is philosophically aligned:

```
Mem0:        Long conversation → Compressed user facts (~80% token reduction)
CodeTrellis: Large codebase    → Compressed project context (~23:1 compression)
```

**Potential synergy:** Mem0 could compress developer session history (what they worked on, decisions made), while CodeTrellis compresses the codebase itself. Together they'd give an AI both user memory AND project context.

---

### 2.3 Zep AI

**Website:** getzep.com  
**Core Product:** Context engineering platform (Agent Memory + Graph RAG + Agent Context)  
**Open Source:** Graphiti (temporal knowledge graph library) — open source on GitHub  
**Tagline:** "Zep assembles the right context from chat history, business data, and user behavior."

#### What It Does

Zep is the most architecturally sophisticated in this group. It builds a **temporal knowledge graph** from chat messages, business data (JSON), and documents. Facts change over time — old ones are invalidated. It assembles context for LLMs in <200ms.

```
Data Sources (Chat, JSON, Docs) → Zep Graph Construction → Temporal Knowledge Graph
                                                                     ↓
Agent Needs Context → Zep Context Assembly → Token-efficient context block
```

#### Technical Architecture

| Component            | Details                                                                    |
| -------------------- | -------------------------------------------------------------------------- |
| **Engine**           | Temporal knowledge graph (entities, relationships, facts with time ranges) |
| **Ingestion**        | Chat messages, JSON business data, documents                               |
| **Extraction**       | Automatic entity recognition, relationship building, fact extraction       |
| **Context Assembly** | Customizable context templates with token budgets                          |
| **Benchmark**        | 80.32% accuracy @ 189ms on LoCoMo benchmark (single-shot retrieval)        |
| **Custom Models**    | Define custom entity types and relationship models per domain              |
| **Deployment**       | Cloud, BYOK, BYOM, BYOC options                                            |
| **Open Source**      | Graphiti library (temporal knowledge graph)                                |
| **SDKs**             | TypeScript, Python, Go                                                     |

#### Context Template System (Interesting Parallel)

```typescript
await client.context.createContextTemplate({
  templateId: "template1",
  template: `# USER PROFILE
%{user_summary}

# RELEVANT FACTS
%{edges limit=10}

# RELEVANT ENTITIES
%{entities limit=2 types=[person,organization]}`,
});
```

This is architecturally similar to how CodeTrellis Matrix sections work — structured, token-budgeted context blocks.

#### Pricing

| Tier       | Price            | Details                                                 |
| ---------- | ---------------- | ------------------------------------------------------- |
| Free       | 1,000 credits/mo | Basic access                                            |
| Flex       | $25/mo           | 20,000 credits, 600 RPM                                 |
| Flex Plus  | $475/mo          | 300,000 credits, 1,000 RPM, webhooks, custom extraction |
| Enterprise | Custom           | SOC 2 Type II, HIPAA, BYOC                              |

#### Key Differentiator

**Temporal facts with invalidation.** Zep doesn't just store facts — it knows _when_ they became true and _when_ they expired. "Robbie loves Adidas" (Sept 2024 → Oct 2024, INVALIDATED). "Robbie switching to Nike" (Oct 2024 → present).

#### Relevance to CodeTrellis

**Moderate conceptual overlap.** Zep's approach to structured, template-based context assembly with token budgets is conceptually similar to CodeTrellis's matrix sections. Key parallels:

| Zep Concept                          | CodeTrellis Equivalent                                      |
| ------------------------------------ | ----------------------------------------------------------- |
| Context templates with `%{entities}` | Matrix sections `[PYTHON_TYPES]`, `[IMPLEMENTATION_LOGIC]`  |
| Token-budgeted assembly              | `--optimal` tier with 94K target                            |
| Entity extraction from data          | Type/function extraction from code                          |
| Temporal fact invalidation           | File-change-triggered matrix regeneration (`watch` command) |
| Custom entity models                 | Custom parsers (`IParser`, `IExtractor` interfaces)         |

**Key difference:** Zep extracts from _conversations and business data_. CodeTrellis extracts from _source code_. Zep is runtime (evolves during app usage). CodeTrellis is pre-computed (snapshot of codebase state).

---

### 2.4 Cognee

**Website:** cognee.ai  
**GitHub:** 12.4K stars, 103 contributors, Apache-2.0 license  
**Funding:** $7.5M seed led by Pebblebed  
**Tagline:** "Knowledge engine that learns — AI Agents that adapt and learn from your feedback"

#### What It Does

Cognee transforms raw data (PDFs, docs, images, audio, conversations) into a **living knowledge graph** that combines vector search and graph databases. It self-improves by learning from feedback.

```python
await cognee.add("Cognee turns documents into AI memory.")
await cognee.cognify()    # Build knowledge graph
await cognee.memify()     # Add memory algorithms
results = await cognee.search("What does Cognee do?")
```

#### Technical Architecture

| Component                | Details                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| **Core**                 | Pythonic data pipelines for ingestion → cognify → memify → search |
| **Data Sources**         | 30+ types: PDF, DOCX, XLSX, MP3, PNG, SQL, data warehouses        |
| **Graph DBs**            | Neo4j, NetworkX, Kuzu, FalkorDB                                   |
| **Vector DBs**           | Qdrant, LanceDB, Milvus, Redis                                    |
| **LLM Providers**        | OpenAI, Ollama, Gemini, Anyscale                                  |
| **Agentic Integrations** | Cursor, RooCode, LangGraph, CrewAI, Claude, Continue              |
| **Self-Improvement**     | Learns from feedback, updates concepts, auto-tunes over time      |
| **MCP Server**           | Has `cognee-mcp` for integration with MCP-compatible tools        |
| **Deployment**           | Open source (self-host), Platform (managed cloud)                 |

#### Use Cases

- Vertical AI agents (domain-smart copilots)
- Unifying data silos into a single knowledge graph
- Local agent memory with feedback loops
- Research: Published at arXiv on "Optimizing Knowledge Graphs for LLM Reasoning"

#### Key Differentiator

**Self-improvement through feedback + ontology mapping.** Cognee doesn't just build a graph — it learns which parts matter, updates its understanding, and improves over time. This is the closest to "living documentation" concept.

#### Relevance to CodeTrellis

**Moderate technical overlap.** Cognee's knowledge graph approach has parallels:

| Cognee Concept                   | CodeTrellis Equivalent                                    |
| -------------------------------- | --------------------------------------------------------- |
| `cognee.add()` → ingest data     | `codetrellis scan .` → ingest codebase                    |
| `cognee.cognify()` → build graph | Compressor → build matrix sections                        |
| `cognee.search()` → query graph  | Matrix sections queried by AI prompt                      |
| Ontology mapper                  | Framework-aware extractors (NestJS, Angular, Flask, etc.) |
| Self-improvement                 | ❌ CodeTrellis doesn't learn yet                          |
| MCP server                       | CodeTrellis MCP planned                                   |
| 30+ data sources                 | 60+ language/framework parsers                            |

**Key differences:**

1. Cognee is **domain-agnostic** (any data); CodeTrellis is **code-specific** (deep code understanding)
2. Cognee is **LLM-dependent** (uses LLM for extraction); CodeTrellis is **deterministic** (parsers, no LLM cost for scanning)
3. Cognee builds a **runtime graph** (requires a running service); CodeTrellis produces a **static file** (works anywhere)

---

### 2.5 Greptile

**Website:** greptile.com  
**Customers:** Brex, Substack, Scale AI, PostHog, Klaviyo, WorkOS, Browserbase, Mintlify  
**Tagline:** "AI Agents That Catch Bugs in Your Pull Requests With Full Context of Your Codebase"

#### What It Does

Greptile is an **AI code reviewer** that generates a detailed graph of your codebase and understands how everything fits together. It reviews PRs in GitHub/GitLab with full codebase context, catches bugs, enforces custom coding standards, and learns from your team's PR comments.

```
Repository → Greptile Codebase Graph → AI PR Review
                                            ↓
                                    In-line comments, bug detection,
                                    anti-pattern flagging, security issues
```

#### Technical Architecture

| Component        | Details                                                                 |
| ---------------- | ----------------------------------------------------------------------- |
| **Core**         | Codebase graph generation (understands how everything connects)         |
| **Input**        | GitHub/GitLab repositories                                              |
| **Output**       | In-line PR comments, summaries, mermaid diagrams, confidence scores     |
| **Custom Rules** | Describe coding standards in English, scope to repos/paths/patterns     |
| **Learning**     | Infers team standards from engineer PR comments; tracks 👍/👎 reactions |
| **Languages**    | Python, JS, TS, Go, Elixir, Java, C, C++, C#, Swift, PHP, Rust (30+)    |
| **Deployment**   | Cloud or self-hosted (air-gapped)                                       |
| **Results**      | Median merge time: 20hrs → 1.8hrs (11x improvement)                     |

#### Pricing

| Tier        | Price             | Details                                |
| ----------- | ----------------- | -------------------------------------- |
| Cloud       | $30/active dev/mo | Unlimited repos, reviews, users        |
| Enterprise  | Custom            | Self-host, SSO/SAML, GitHub Enterprise |
| Open Source | Free              | 100% off for qualified OSS projects    |
| Startups    | 50% off           | Pre-Series A                           |

#### Key Differentiator

**Codebase graph + learning from human feedback.** Greptile doesn't just do static analysis — it reads your team's actual PR comments to learn what matters. Over time, it learns your coding standards organically.

#### Relevance to CodeTrellis

**Highest overlap (40%).** Greptile is the closest competitor in the code-understanding space:

| Dimension                  | Greptile                    | CodeTrellis                                        |
| -------------------------- | --------------------------- | -------------------------------------------------- |
| **Core function**          | Code review (PR-focused)    | Code context (AI prompt-focused)                   |
| **When it runs**           | On PR creation              | On `scan` or file change                           |
| **Output format**          | PR comments (ephemeral)     | matrix.prompt file (persistent)                    |
| **Codebase understanding** | Graph-based                 | Multi-parser extraction                            |
| **Custom standards**       | English rules + learning    | `[BEST_PRACTICES]` section (447+ rules)            |
| **Multi-language**         | 30+                         | 60+                                                |
| **Architecture awareness** | Yes (graph)                 | Yes (deeper — types, APIs, logic flow, data flows) |
| **AI model used**          | Internal (not configurable) | Any model (matrix is text)                         |
| **Pricing model**          | Per developer per month     | One-time scan (free CLI)                           |
| **Works outside IDE**      | Yes (GitHub/GitLab)         | Yes (any tool, any AI)                             |

**Critical difference:** Greptile's understanding is **locked inside their service** — you can't export it. CodeTrellis Matrix is a **portable text file** that works with any AI tool.

---

### 2.6 CodeTrellis Matrix

**Version:** 4.9.0  
**Repository:** 490 source files, 60+ language parsers  
**Core Product:** Deterministic codebase scanner → matrix.prompt (AI-optimized project representation)

#### What It Does

CodeTrellis scans an entire codebase and compresses it into a single `matrix.prompt` file — a token-efficient, structured representation containing architecture, types, APIs, implementation logic, best practices, actionable items, and more.

```
Full Codebase → codetrellis scan . --optimal → matrix.prompt (25KB-94KB)
                                                       ↓
                                             Inject into ANY AI tool
                                             Claude, GPT, Gemini, Llama...
```

#### Technical Architecture

| Component          | Details                                                                 |
| ------------------ | ----------------------------------------------------------------------- |
| **Core**           | Python-based multi-parser scanner + compressor                          |
| **Parsers**        | 60+ language/framework extractors (IParser, IExtractor interfaces)      |
| **Output**         | 34 section types: PROJECT, TYPES, APIs, LOGIC, BEST_PRACTICES, etc.     |
| **Compression**    | 23:1 ratio (8.78MB → 94K tokens at --optimal)                           |
| **Tiers**          | minimal (1K), basic (3K), standard (10K), detailed (30K), optimal (94K) |
| **Best Practices** | 447+ framework-specific practices (3,081 in database)                   |
| **Watch**          | File-change triggered regeneration                                      |
| **CLI**            | scan, watch, sync, export, prompt commands                              |
| **Extension**      | vscode-codetrellis-chat (50+ tools, inline completions, agents)         |

#### Key Differentiator

1. **Deterministic** — No LLM cost for scanning; parsers are rule-based
2. **Portable** — matrix.prompt is a text file; works with ANY AI
3. **Pre-computed** — Zero discovery cost at AI interaction time
4. **Deep** — Not just signatures (like aider) but implementation logic, data flows, business domain
5. **Empirically proven** — SWE-bench style experiment: +400% improvement on cross-file tasks

---

## 3. Architecture Comparison

### 3.1 How Each System Processes Context

```
SuperMemory:
  User Interaction → Embed → Graph Enrich → Vector+Graph Store → Recall
  (runtime, per-user, evolving)

Mem0:
  Conversation → Memory Compression → Fact Extraction → Store → Recall
  (runtime, per-user, compressing)

Zep:
  Chat + Business Data → Entity Recognition → Temporal Knowledge Graph → Context Assembly
  (runtime, per-user/entity, temporal)

Cognee:
  Any Document → Chunk → Cognify (graph) → Memify (memory) → Search
  (batch or runtime, per-dataset, learning)

Greptile:
  Repository → Codebase Graph → PR Analysis → Comments
  (on PR event, per-repo, learning from feedback)

CodeTrellis:
  Source Code → Parse (60+ parsers) → Compress → matrix.prompt → Inject into AI
  (pre-computed, per-project, deterministic)
```

### 3.2 Context Generation — LLM-Dependent vs Deterministic

This is a **fundamental architectural divide**:

| Product         | Needs LLM to Generate Context? | Cost to Index          | Consistency         |
| --------------- | ------------------------------ | ---------------------- | ------------------- |
| **SuperMemory** | Yes (embedding + enrichment)   | $0.01/1K tokens        | Varies              |
| **Mem0**        | Yes (compression + extraction) | Per API call           | Varies              |
| **Zep**         | Yes (entity recognition)       | Credits                | Varies              |
| **Cognee**      | Yes (cognify uses LLM)         | LLM API cost           | Varies              |
| **Greptile**    | Yes (graph construction)       | Included in $30/dev/mo | Varies              |
| **CodeTrellis** | **No** (deterministic parsers) | **$0** (CPU only)      | **100% consistent** |

**This is CodeTrellis's most underappreciated advantage.** Every other tool in this space pays LLM costs to _understand_ your data. CodeTrellis uses deterministic parsers — zero LLM cost, zero variability, zero hallucination risk in the scanning phase.

### 3.3 Context Delivery — Runtime vs Pre-Computed

| Product         | When Context Is Built | When Context Is Delivered | Latency |
| --------------- | --------------------- | ------------------------- | ------- |
| **SuperMemory** | On each interaction   | On each query (API call)  | <300ms  |
| **Mem0**        | On each conversation  | On each recall            | ~100ms  |
| **Zep**         | On ingestion          | On context assembly       | <200ms  |
| **Cognee**      | On cognify()          | On search()               | Varies  |
| **Greptile**    | On repo index         | On PR creation            | Seconds |
| **CodeTrellis** | On `scan` (once)      | **Pre-loaded in prompt**  | **0ms** |

CodeTrellis has **zero runtime latency** because the context is already in the prompt. No API call, no retrieval, no assembly.

---

## 4. Feature Matrix

### 4.1 Comprehensive Feature Comparison

| Feature                       | SuperMemory     | Mem0            | Zep                  | Cognee            | Greptile          | CodeTrellis                |
| ----------------------------- | --------------- | --------------- | -------------------- | ----------------- | ----------------- | -------------------------- |
| **Core Focus**                | User memory     | User memory     | Context engineering  | Knowledge engine  | Code review       | Code context               |
| **Code Understanding**        | ❌              | ❌              | ❌                   | ⚠️ Partial        | ✅                | ✅✅ Deep                  |
| **User Memory**               | ✅✅            | ✅✅            | ✅✅                 | ⚠️                | ❌                | ❌                         |
| **Document Understanding**    | ✅              | ⚠️              | ✅                   | ✅✅              | ❌                | ❌ (code only)             |
| **Architecture Extraction**   | ❌              | ❌              | ❌                   | ❌                | ✅ (graph)        | ✅✅ (34 sections)         |
| **Type/Interface Extraction** | ❌              | ❌              | ❌                   | ❌                | ⚠️                | ✅✅                       |
| **API Route Extraction**      | ❌              | ❌              | ❌                   | ❌                | ⚠️                | ✅✅                       |
| **Implementation Logic**      | ❌              | ❌              | ❌                   | ❌                | ❌                | ✅✅ (307+ snippets)       |
| **Best Practices**            | ❌              | ❌              | ❌                   | ❌                | ✅ (custom rules) | ✅✅ (447+ built-in)       |
| **Business Domain Detection** | ❌              | ❌              | ❌                   | ⚠️ (ontology)     | ❌                | ✅                         |
| **CI/CD Extraction**          | ❌              | ❌              | ❌                   | ❌                | ❌                | ✅                         |
| **Temporal Memory**           | ✅ (evolves)    | ✅              | ✅✅ (best)          | ⚠️                | ✅ (learns)       | ❌                         |
| **Self-Improvement**          | ✅              | ✅              | ⚠️                   | ✅✅              | ✅ (PR feedback)  | ❌                         |
| **Knowledge Graph**           | ✅              | ⚠️              | ✅✅                 | ✅✅              | ✅                | ❌ (structured text)       |
| **Deterministic (no LLM)**    | ❌              | ❌              | ❌                   | ❌                | ❌                | ✅✅                       |
| **Portable Output**           | ❌ (API-locked) | ❌ (API-locked) | ❌ (API-locked)      | ⚠️ (OSS)          | ❌ (SaaS-locked)  | ✅✅ (text file)           |
| **Multi-AI Compatible**       | Via SDK         | Via SDK         | Via SDK              | Via MCP           | Internal          | ✅✅ (any AI)              |
| **Open Source**               | ✅ (GitHub)     | ✅ (40K stars)  | ✅ (Graphiti)        | ✅ (12.4K stars)  | ❌                | ⚠️ (CLI OSS, ext. private) |
| **Self-Hosted**               | ✅              | ✅              | ✅                   | ✅                | ✅ (enterprise)   | ✅ (CLI is local)          |
| **MCP Server**                | ❌              | ❌              | ✅                   | ✅                | ❌                | 🔄 (planned)               |
| **IDE Integration**           | ❌              | ❌              | ❌                   | ✅ (Cursor, etc.) | GitHub/GitLab     | ✅ (VS Code extension)     |
| **Watch/Auto-Update**         | Realtime        | Realtime        | Realtime             | On demand         | On PR             | ✅ (`watch` command)       |
| **60+ Language Support**      | ❌              | ❌              | ❌                   | ❌                | 30+               | ✅ (60+)                   |
| **Token Compression**         | ❌              | ✅ (80%)        | ✅ (budgeted)        | ❌                | ❌                | ✅ (23:1)                  |
| **Compliance**                | SOC 2           | SOC 2, HIPAA    | SOC 2 Type II, HIPAA | EU (heyData)      | SOC 2             | ❌ (local only)            |

### 4.2 The Unique Dimensions Only CodeTrellis Covers

These features exist in **no other product** in this landscape:

1. **`[IMPLEMENTATION_LOGIC]`** — 307+ function-level control flow summaries (`flow:[if×11,elif×5,for×5]`)
2. **`[BUSINESS_DOMAIN]`** — Automatic business domain classification
3. **`[INFRASTRUCTURE]`** — CI/CD pipeline extraction (GitHub Actions, Docker, Terraform)
4. **`[BEST_PRACTICES]`** — 447+ framework-specific coding standards auto-matched
5. **`[ACTIONABLE_ITEMS]`** — TODOs, FIXMEs, PLACEHOLDERs with severity
6. **`[DATA_FLOWS]`** — Primary architectural pattern detection (Request-Response, Event-Driven, etc.)
7. **`[RUNBOOK]`** — Build/test/deploy commands, env vars, version requirements
8. **Deterministic scanning** — Zero LLM cost, 100% reproducible results
9. **Model-agnostic portable output** — Same matrix.prompt works with Claude, GPT, Gemini, Llama, local models

---

## 5. The Fundamental Category Distinction

After analyzing all five competitors, the AI context space breaks into **four distinct categories**:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  CATEGORY 1: USER MEMORY LAYERS                                 │
│  SuperMemory, Mem0                                              │
│  ───────────────────                                            │
│  Problem: "My AI chatbot forgets users between sessions"        │
│  Solution: Memory API that stores user preferences/history      │
│  Customer: App builders (chatbots, assistants, SaaS apps)       │
│  Revenue model: API usage (per token, per query)                │
│                                                                 │
│  CATEGORY 2: CONTEXT ENGINEERING PLATFORMS                      │
│  Zep                                                            │
│  ───                                                            │
│  Problem: "My agent needs business data + chat history + facts" │
│  Solution: Temporal knowledge graph + context assembly          │
│  Customer: Enterprise agent builders                            │
│  Revenue model: Credits (ingestion + retrieval)                 │
│                                                                 │
│  CATEGORY 3: KNOWLEDGE GRAPH ENGINES                            │
│  Cognee                                                         │
│  ──────                                                         │
│  Problem: "I need to make my documents AI-queryable"            │
│  Solution: Auto-build knowledge graphs from any data source     │
│  Customer: Data-heavy enterprises, research teams               │
│  Revenue model: Open source + managed platform                  │
│                                                                 │
│  CATEGORY 4: CODE UNDERSTANDING                                 │
│  Greptile, CodeTrellis                                          │
│  ──────────────────────                                         │
│  Problem: "AI doesn't understand my codebase deeply enough"     │
│  Solution: Codebase graph/matrix for AI-powered development     │
│  Customer: Engineering teams                                    │
│  Revenue model: Per-dev (Greptile) / CLI (CodeTrellis)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CodeTrellis is in Category 4 but with characteristics of Category 3** (the pre-computation and compression aspects). The key insight: **none of the Category 1/2/3 tools even attempt code understanding.**

---

## 6. Pricing Comparison

### 6.1 Cost for a 10-Developer Team (Monthly)

| Product                   | Monthly Cost | What You Get                                      |
| ------------------------- | ------------ | ------------------------------------------------- |
| **SuperMemory Pro**       | $19/mo total | 2M tokens, 100K queries (for app users, not devs) |
| **Mem0 Platform**         | ~$50-200/mo  | Per API usage (for app users, not devs)           |
| **Zep Flex**              | $25-475/mo   | 20K-300K credits                                  |
| **Cognee Cloud**          | ~$100-500/mo | Managed platform                                  |
| **Greptile Cloud**        | **$300/mo**  | $30/dev × 10 devs                                 |
| **CodeTrellis CLI**       | **$0**       | Free CLI scanning                                 |
| **CodeTrellis Extension** | TBD          | AI chat + completions                             |

### 6.2 Cost Per "Context Unit" (Apples-to-Apples)

Normalizing to "cost per 1M tokens of context delivered":

| Product         | Cost per 1M Context Tokens | Method                     |
| --------------- | -------------------------- | -------------------------- |
| SuperMemory     | $10.00                     | $0.01/1K tokens processed  |
| Mem0            | ~$5-15                     | Varies by plan             |
| Zep             | ~$8-25                     | Credits-based              |
| Greptile        | N/A (fixed per dev)        | Not token-based            |
| **CodeTrellis** | **$0.00**                  | Deterministic, local, free |

---

## 7. Head-to-Head: Where Each Wins and Loses

### 7.1 SuperMemory vs CodeTrellis

| Dimension            | SuperMemory Wins                       | CodeTrellis Wins      |
| -------------------- | -------------------------------------- | --------------------- |
| User personalization | ✅ Designed for it                     | ❌ Not applicable     |
| Code understanding   | ❌ No capability                       | ✅ Deep (60+ parsers) |
| Connector ecosystem  | ✅ Google Drive, Notion, OneDrive      | ❌ Code repos only    |
| Model agnostic       | ⚠️ Via SDKs (still API-locked)         | ✅ Pure text file     |
| Cost                 | ❌ Ongoing API cost                    | ✅ Free scanning      |
| **Verdict**          | Different product for different market | —                     |

### 7.2 Mem0 vs CodeTrellis

| Dimension                  | Mem0 Wins                             | CodeTrellis Wins                           |
| -------------------------- | ------------------------------------- | ------------------------------------------ |
| Community                  | ✅ 40K GitHub stars, $24M funding     | ⚠️ Smaller community                       |
| Compression innovation     | ✅ 80% conversation compression       | ✅ 23:1 codebase compression               |
| Framework integrations     | ✅ LangChain, CrewAI, 20+             | ⚠️ Standalone CLI                          |
| Code-specific intelligence | ❌ None                               | ✅ Types, APIs, logic, patterns            |
| Reproducibility            | ❌ LLM-dependent extraction varies    | ✅ Deterministic, 100% consistent          |
| **Verdict**                | Better for agent memory (user-facing) | Better for code context (developer-facing) |

### 7.3 Zep vs CodeTrellis

| Dimension                 | Zep Wins                            | CodeTrellis Wins                      |
| ------------------------- | ----------------------------------- | ------------------------------------- |
| Temporal reasoning        | ✅ Facts with time ranges           | ❌ Snapshot-based                     |
| Business data integration | ✅ JSON, chat, docs                 | ❌ Code only                          |
| Context templates         | ✅ Token-budgeted templates         | ✅ 5-tier output (1K-94K)             |
| Benchmarking              | ✅ LoCoMo 80.32%                    | ✅ SWE-bench +400% on cross-file      |
| Portability               | ❌ API-locked                       | ✅ Portable text file                 |
| Code depth                | ❌ No code understanding            | ✅ 34 section types for code          |
| **Verdict**               | Better for enterprise agent context | Better for developer codebase context |

### 7.4 Cognee vs CodeTrellis

| Dimension           | Cognee Wins                             | CodeTrellis Wins                              |
| ------------------- | --------------------------------------- | --------------------------------------------- |
| Data source variety | ✅ 30+ (PDF, audio, video, etc.)        | ❌ Code only                                  |
| Self-improvement    | ✅ Learns from feedback                 | ❌ Not yet                                    |
| Graph depth         | ✅ Full knowledge graph                 | ⚠️ Structured text (no graph DB)              |
| Research rigor      | ✅ Published at arXiv                   | ✅ SWE-bench experiment                       |
| Code specificity    | ❌ Generic knowledge extraction         | ✅ Code-aware (controllers, decorators, DTOs) |
| LLM cost to scan    | ❌ Requires LLM API                     | ✅ $0 (deterministic)                         |
| **Verdict**         | Better for general knowledge management | Better for codebase intelligence              |

### 7.5 Greptile vs CodeTrellis (THE KEY COMPARISON)

This is the most important comparison because Greptile is the **closest competitor**:

| Dimension                  | Greptile Wins                         | CodeTrellis Wins                      |
| -------------------------- | ------------------------------------- | ------------------------------------- |
| **Market traction**        | ✅ Brex, Substack, Scale AI, PostHog  | ⚠️ Earlier stage                      |
| **Revenue model**          | ✅ Proven ($30/dev/mo × 1000+ teams)  | ⚠️ Monetization TBD                   |
| **PR integration**         | ✅ Deep GitHub/GitLab integration     | ❌ Not PR-focused                     |
| **Team learning**          | ✅ Learns from PR comments, 👍/👎     | ❌ Static extraction                  |
| **Custom rules UX**        | ✅ "Describe standards in English"    | ⚠️ Best practices are auto-selected   |
| **Merge time impact**      | ✅ Proven 20hrs → 1.8hrs              | Not measured                          |
| **Context portability**    | ❌ Locked in Greptile SaaS            | ✅ matrix.prompt is a file            |
| **Context depth**          | ⚠️ Graph-based (what connects)        | ✅ Multi-dimensional (what, how, why) |
| **Multi-AI support**       | ❌ Uses internal model                | ✅ Any model, any tool                |
| **Language coverage**      | ⚠️ 30+ (quality varies)               | ✅ 60+ (framework-aware)              |
| **Framework awareness**    | ⚠️ Code structure only                | ✅ NestJS, Angular, Flask decorators  |
| **Implementation logic**   | ❌ No function-level flow analysis    | ✅ 307+ `flow:[if×N,for×N]`           |
| **Infrastructure context** | ❌ No CI/CD extraction                | ✅ GitHub Actions, Docker, Terraform  |
| **Best practices**         | ⚠️ Custom rules only                  | ✅ 447+ built-in + framework-specific |
| **Cost**                   | ❌ $30/dev/mo ($3,600/yr for 10 devs) | ✅ Free CLI                           |
| **Offline/air-gapped**     | ⚠️ Enterprise only                    | ✅ Always local                       |
| **SWE-bench proven**       | ❌ Not tested                         | ✅ +400% on cross-file tasks          |

**Verdict:** Greptile has market traction and PR workflow. CodeTrellis has deeper code understanding and portability. **They are complementary more than competitive** — Greptile reviews PRs, CodeTrellis powers any AI interaction.

---

## 8. What CodeTrellis Can Learn

### 8.1 From SuperMemory & Mem0: Memory Evolution

**Concept:** Memories that _evolve_ — facts become outdated, preferences change, new patterns emerge.

**CodeTrellis Application:**

- Track how the codebase changes over time (architectural drift detection)
- "This endpoint used to be REST, now it's GraphQL" — temporal code memory
- Session memory: "Developer worked on auth module yesterday, continue from there"

### 8.2 From Zep: Context Templates with Token Budgets

**Concept:** Pre-defined context templates that assemble exactly the right context with token constraints.

**CodeTrellis Application:**

- Already has 5 tiers (1K-94K). Could add:
  - Query-aware section selection (inject only relevant sections)
  - Per-section token budgets in the prompt renderer
  - Custom templates: "I only need types + APIs + logic for auth module"

### 8.3 From Cognee: Self-Improvement / Feedback Loops

**Concept:** System learns from feedback — which answers were helpful, which knowledge was relevant.

**CodeTrellis Application:**

- Track which matrix sections the AI actually uses (via tool invocation logs)
- If AI never references `[DATABASE]` section, reduce its priority
- If AI frequently references `[IMPLEMENTATION_LOGIC]`, increase its detail level
- A/B test matrix configurations and track code fix quality

### 8.4 From Greptile: Learning from Human Behavior

**Concept:** Infer coding standards from actual PR comments rather than static rule databases.

**CodeTrellis Application:**

- Analyze git commit messages for patterns
- Learn from code review comments (if integrated with GitHub)
- Auto-generate best practices from the team's actual codebase patterns (not from a generic database)
- Learn what developers ask about most → prioritize those sections

### 8.5 From All: MCP Server Distribution

**Every competitor** either has or is building MCP integration. CodeTrellis MUST ship as an MCP server to be discoverable in the MCP ecosystem (Claude Desktop, Cursor, Cline, Continue, etc.).

---

## 9. Strategic Positioning

### 9.1 The Three-Layer Context Stack (Industry Vision)

```
┌────────────────────────────────────────────────────────┐
│ LAYER 3: USER MEMORY (SuperMemory / Mem0 / Zep)       │
│ "What does the AI remember about THIS DEVELOPER?"     │
│ Session history, preferences, past decisions           │
├────────────────────────────────────────────────────────┤
│ LAYER 2: PROJECT CONTEXT (CodeTrellis Matrix)          │
│ "What does the AI know about THIS CODEBASE?"          │
│ Architecture, types, APIs, logic, patterns, practices  │
├────────────────────────────────────────────────────────┤
│ LAYER 1: KNOWLEDGE BASE (Cognee / RAG)                │
│ "What does the AI know about THE DOMAIN?"             │
│ Documentation, API references, standards, specs        │
└────────────────────────────────────────────────────────┘
```

**CodeTrellis owns Layer 2 — the most critical layer for developer productivity.** Layer 1 (documentation) is commoditized. Layer 3 (user memory) is valuable but secondary to code understanding. Layer 2 (project context) is where AI makes or breaks code quality.

### 9.2 The Positioning Statement

> **CodeTrellis is the only pre-computed, deterministic, model-agnostic codebase context engine for AI-assisted development.**
>
> While memory layers (SuperMemory, Mem0) remember users, and knowledge engines (Cognee) understand documents, CodeTrellis understands _your code_ — architecture, types, APIs, implementation logic, patterns, and practices — and delivers that understanding to any AI tool at zero runtime cost.

### 9.3 Why CodeTrellis Wins the Code Context Category

| Competition Axis         | Why CodeTrellis Wins                                                      |
| ------------------------ | ------------------------------------------------------------------------- |
| **vs Memory Layers**     | They don't even attempt code understanding                                |
| **vs Knowledge Engines** | CodeTrellis is code-native; Cognee is document-native                     |
| **vs Greptile**          | Deeper (34 sections vs graph), portable (file vs SaaS), free (vs $30/dev) |
| **vs Cursor/Copilot**    | Pre-computed vs JIT; 67x more contextual; model-agnostic                  |
| **vs aider**             | 8x more dimensions; implementation logic, not just signatures             |
| **vs Claude Code**       | 0% discovery cost vs 60% discovery cost                                   |

---

## 10. The Convergence Opportunity

### 10.1 The Ultimate Developer Context Stack

The market is converging. Every tool is building toward "right context, right time." CodeTrellis has the opportunity to become the **Layer 2 standard** — the codebase context that every AI tool consumes:

```
┌──────────────────────────────────────────────────────────┐
│                   DEVELOPER AI STACK                     │
│                                                          │
│  IDE (Cursor / VS Code / CodeTrellis Code)               │
│    ↓                                                     │
│  Memory Layer (Mem0/SuperMemory/Zep for session memory)  │
│    ↓                                                     │
│  ★ CODE CONTEXT LAYER (CodeTrellis Matrix) ★            │
│    ↓                                                     │
│  Knowledge Layer (Cognee for documentation/specs)        │
│    ↓                                                     │
│  AI Model (Claude / GPT / Gemini / Local)                │
│    ↓                                                     │
│  Output (code completions, reviews, refactors, tests)    │
└──────────────────────────────────────────────────────────┘
```

### 10.2 Strategic Integration Partnerships

| Partner      | Integration                            | Value                                         |
| ------------ | -------------------------------------- | --------------------------------------------- |
| **Mem0**     | Matrix as a "code memory" type in Mem0 | Mem0 handles session, Matrix handles codebase |
| **Zep**      | Matrix sections as Zep entity types    | Zep's temporal engine tracks code evolution   |
| **Cognee**   | Matrix as a Cognee data source         | Cognee builds cross-project knowledge graphs  |
| **Greptile** | Matrix injected before PR review       | Greptile gets deeper context for reviews      |

### 10.3 Immediate Action Items

| Priority | Action                                                          | Timeframe |
| -------- | --------------------------------------------------------------- | --------- |
| 🔴 P0    | Ship MCP Server — Matrix as an MCP resource/tool                | 2 weeks   |
| 🔴 P0    | Complete matrix → prompt pipeline in extension                  | 4 weeks   |
| 🟡 P1    | Publish SWE-bench experiment results (market proof)             | 2 weeks   |
| 🟡 P1    | Query-aware section filtering (don't inject ALL 94K every time) | 3 weeks   |
| 🟢 P2    | Self-improvement: track which sections AI uses most             | 6 weeks   |
| 🟢 P2    | Temporal diffs: "what changed since last scan"                  | 6 weeks   |
| 🔵 P3    | Integration SDK for Mem0/Zep/Cognee                             | 8 weeks   |
| 🔵 P3    | Greptile-compatible output (markdown rules format)              | 4 weeks   |

---

## Appendix: Quick Reference Card

### One-Line Descriptions

| Product         | One-Line                                                         |
| --------------- | ---------------------------------------------------------------- |
| **SuperMemory** | "Memory API — your chatbot remembers each user"                  |
| **Mem0**        | "Memory compression — 80% fewer tokens, same recall"             |
| **Zep**         | "Temporal knowledge graph — facts that evolve over time"         |
| **Cognee**      | "Knowledge engine — turns any data into queryable memory"        |
| **Greptile**    | "AI code reviewer — catches bugs with full codebase context"     |
| **CodeTrellis** | "Codebase X-ray — pre-computed context for any AI, any tool, $0" |

### The Killer Stat for Each

| Product         | Killer Stat                                                          |
| --------------- | -------------------------------------------------------------------- |
| **SuperMemory** | 5B tokens daily, 50M tokens/user, sub-300ms recall                   |
| **Mem0**        | 90% fewer tokens vs OpenAI memory, 26% higher quality (ECAI paper)   |
| **Zep**         | 80.32% accuracy @ 189ms single-shot retrieval (LoCoMo)               |
| **Cognee**      | 12.4K GitHub stars, 30+ data source types                            |
| **Greptile**    | 20hrs → 1.8hrs median merge time (11x faster)                        |
| **CodeTrellis** | **+400% improvement on cross-file tasks, 23:1 compression, $0 cost** |

---

_Research conducted: 20 February 2026_  
_Sources: supermemory.ai, mem0.ai, getzep.com, cognee.ai, greptile.com, GitHub repos_  
_Analyst: Keshav Chaudhary (CodeTrellis Creator)_  
_For internal strategic planning_
