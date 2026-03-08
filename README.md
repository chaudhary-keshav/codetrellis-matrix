# 🧠 CodeTrellis - Project Self-Awareness System

> **Version:** 4.16.0
> **Created:** 31 January 2026
> **Updated:** Session 59 — Infrastructure Hardening (Watcher + Builder + Compressor)
> **Author:** Keshav Chaudhary

## What is CodeTrellis?

CodeTrellis (Project Self-Awareness System) is a tool that scans your entire codebase, compresses it into a minimal token format, and injects it into every AI prompt - giving AI **complete project awareness** in every interaction.

### The Problem

- AI assistants read files one at a time (50-100 lines per read)
- They don't know about existing components, schemas, or patterns
- You have to explain your project structure repeatedly
- AI creates duplicate code instead of reusing existing components
- **AI lacks business domain understanding** - doesn't know WHY code exists

### The Solution

CodeTrellis creates a compressed "matrix" of your entire project that:

- Fits in ~800-15000 tokens (configurable tiers!)
- Contains ALL schemas, DTOs, components, endpoints
- Gets injected into EVERY prompt automatically
- Keeps AI aware of your full codebase
- **Extensible plugin architecture** for languages and frameworks
- **Supports Python, TypeScript, Go, and more** out of the box
- **AI/ML awareness** - understands PyTorch, HuggingFace, LangChain codebases
- **Infrastructure context** - Docker, Terraform, CI/CD, MongoDB, Redis, Kafka
- **LSP-powered** 99% accurate type extraction
- **Business domain extraction** with data flows and architectural decisions
- **447+ best practices** automatically selected for your tech stack
  | **NEW in v4.9.0:** Plugin architecture, Go support, AI/ML extractors, 447+ best practices, A5.x AI prompt optimization suite (cache optimizer, MCP server, JIT context, skills generator)
  | **NEW in v4.16.0:** Auto-compilation pipeline, incremental builds, deterministic output, `codetrellis clean`, `codetrellis verify`, `--incremental`, `--deterministic`, `--ci` flags
  | **NEW in v4.69:** IMPLEMENTATION_LOGIC in default PROMPT tier, BEST_PRACTICES auto-detected for 15+ languages & 20+ frameworks, thread-safe watcher (Lock + 2s debounce + batch callbacks), broken incremental hydration removed

## Features (v4.16.0)

| Feature                     | Description                                                                     |
| --------------------------- | ------------------------------------------------------------------------------- |
| **Output Tiers**            | COMPACT, PROMPT, FULL, JSON, LOGIC - control usage                              |
| **No Truncation**           | PROMPT/FULL tiers have ZERO truncation                                          |
| **Plugin Architecture**     | Extensible language & framework plugins                                         |
| **Go Support**              | Structs, interfaces, methods, routes (Gin/Echo/Chi)                             |
| **Python Enhanced Parsing** | Dataclasses, Pydantic, Protocols, TypedDicts, Enums                             |
| **AI/ML Extractors**        | PyTorch, HuggingFace, LangChain, MLflow support                                 |
| **Data Infrastructure**     | MongoDB, Redis, Kafka, Vector DB extraction                                     |
| **Pipeline Orchestration**  | Airflow, Prefect, Dagster DAG/flow/asset extraction                             |
| **JSDoc Extraction**        | Captures @param, @returns, @example                                             |
| **README Parsing**          | Extracts project documentation                                                  |
| **Config Extraction**       | package.json, tsconfig, angular.json, pyproject.toml                            |
| **LSP Deep Mode**           | 99% accurate TypeScript types (--deep flag)                                     |
| **Business Domain**         | Auto-detects domain (Trading, E-commerce, etc.)                                 |
| **Data Flow Analysis**      | Maps data flows through WebSocket/HTTP                                          |
| **Arch Decisions**          | Infers architectural decisions with rationale                                   |
| **Domain Vocabulary**       | Extracts domain-specific terms and definitions                                  |
| **Logic Extraction**        | Captures function bodies and control flow                                       |
| **Error Boundaries**        | Resilient extraction with proper error isolation                                |
| **Parallel Processing**     | Multi-threaded scanning with `--parallel` flag                                  |
| **Streaming**               | Memory-efficient extraction for large projects                                  |
| **Optimal Mode**            | Maximum quality with `--optimal` flag                                           |
| **Tree-sitter AST**         | AST-based parsing for Python/TypeScript                                         |
| **Docker/Compose**          | Dockerfile & docker-compose.yml extraction                                      |
| **Terraform**               | Resources, variables, outputs, modules                                          |
| **CI/CD Pipelines**         | GitHub Actions, GitLab CI, Jenkins, CircleCI                                    |
| **NestJS Support**          | Modules, guards, interceptors, pipes, gateways                                  |
| **Distributed Generation**  | Generate .codetrellis files in each component folder                            |
| **Best Practices Library**  | 447+ coding practices across languages                                          |
| **Context-Aware Selection** | Auto-selects practices based on detected stack                                  |
| **Multi-Level Compression** | Minimal/Standard/Comprehensive formats                                          |
| **Cache Optimization**      | LLM KV-cache-aware section reordering (NEW A5.1)                                |
| **MCP Server**              | JSON-RPC 2.0 Model Context Protocol server (NEW A5.2)                           |
| **JIT Context**             | File-aware context injection (NEW A5.3)                                         |
| **AI Skills Generation**    | Auto-generated AI-executable skills (NEW A5.5)                                  |
| **Incremental Builds**      | Only re-extract changed files (NEW v4.16.0 `--incremental`)                     |
| **Deterministic Output**    | Byte-identical outputs across runs (NEW v4.16.0 `--deterministic`)              |
| **CI/CD Mode**              | Deterministic + parallel for pipelines (NEW v4.16.0 `--ci`)                     |
| **Build Verification**      | Quality gate verification (NEW v4.16.0 `codetrellis verify`)                    |
| **Cache Management**        | Content-addressed SHA-256 caching with `codetrellis clean`                      |
| **AI Integration Init**     | Auto-generates enriched Copilot, Claude, Cursor configs (NEW v4.68 `init --ai`) |
| **AI Config Update**        | Regenerate AI files from existing matrix without re-scan (`init --update-ai`)   |
| **JSON-LD Export**          | Schema.org/CodeAction structured data (NEW PART F – v4.67)                      |
| **Semantic Embeddings**     | TF-IDF vector embeddings for code search (NEW PART F – v4.67)                   |
| **Matrix Diff**             | JSON Patch diffs between matrix versions (NEW PART F – v4.67)                   |
| **Multi-Level Compression** | L0–L3 AST-aware compression levels (NEW PART F – v4.67)                         |
| **Cross-Language Types**    | Unified type graph across 53+ languages (NEW PART F – v4.67)                    |
| **Matrix Navigator**        | Structural query engine (`fn:*`, `dep:*`) (NEW PART F – v4.67)                  |
| **MatrixBench Scorer**      | Automated quality benchmarking suite (NEW PART F – v4.67)                       |
| **Quality Gates (G1–G7)**   | 7 formal quality gates for advanced modules (NEW PART G – v4.67)                |
| **Build Contracts (H1–H7)** | Formal I/O contracts with exit codes 41–47 (NEW PART H – v4.67)                 |
| **IMPLEMENTATION_LOGIC**    | Function bodies & control flow in default PROMPT tier (NEW v4.69)               |
| **Best Practices 15+ Lang** | Auto-detected for 15 languages + 20+ frameworks (NEW v4.69)                     |
| **Thread-Safe Watcher**     | threading.Lock, 2s debounce, batch callbacks (NEW v4.69)                        |

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         CodeTrellis WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. SCAN              2. COMPRESS           3. INJECT          │
│   ─────────            ───────────           ────────           │
│                                                                 │
│   Read every     →    Convert to      →    Add to every        │
│   file in             minimal              AI prompt            │
│   project             tokens                                    │
│                                                                 │
│   187 lines      →    30 tokens       →    Full awareness      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Install from source
pip install -e .

# Or install dependencies only
pip install -r requirements.txt

# For LSP deep mode (optional)
cd lsp && npm install

# For AST parsing (optional but recommended)
pip install tree-sitter tree-sitter-python tree-sitter-typescript
```

## Quick Start

```bash
# Initialize AI integrations (Copilot, Claude, Cursor) with enriched matrix data
codetrellis init . --ai

# Update AI files after upgrading CodeTrellis (uses existing matrix, no re-scan)
codetrellis init . --update-ai

# Scan your project (creates .codetrellis/ directory)
codetrellis scan /path/to/your/project

# OPTIMAL MODE - Maximum quality (RECOMMENDED)
codetrellis scan /path/to/project --optimal

# Scan with specific tier
codetrellis scan /path/to/project --tier full

# Scan with LSP for 99% accurate types (requires Node.js)
codetrellis scan /path/to/project --deep

# Parallel scanning for speed
codetrellis scan /path/to/project --parallel --workers 8

# Incremental build (only re-process changed files)
codetrellis scan /path/to/project --incremental

# Deterministic build (byte-identical output, CI-ready)
codetrellis scan /path/to/project --deterministic

# CI/CD mode (deterministic + parallel)
codetrellis scan /path/to/project --ci

# View compressed matrix
codetrellis show

# Watch for changes (auto-sync with incremental builds)
codetrellis watch

# Get prompt-ready matrix
codetrellis prompt > matrix.txt

# Verify build quality
codetrellis verify /path/to/project

# Clean all caches
codetrellis clean /path/to/project

# Clean specific version cache
codetrellis clean /path/to/project --version 4.15.0
```

## Output Tiers

| Tier      | Truncation | Tokens      | Use Case                                    |
| --------- | ---------- | ----------- | ------------------------------------------- |
| `compact` | Yes        | ~800-2000   | Quick overview                              |
| `prompt`  | **NO**     | ~8000-15000 | Default AI injection (includes code logic!) |
| `full`    | **NO**     | ~15000+     | Detailed analysis                           |
| `logic`   | **NO**     | ~30000+     | Full code context                           |
| `json`    | **NO**     | Variable    | Machine processing                          |

```bash
# Use tiers
codetrellis scan ./project --tier compact   # Minimal
codetrellis scan ./project --tier prompt    # Default (recommended)
codetrellis scan ./project --tier full      # Everything
codetrellis scan ./project --tier logic     # With function bodies
```

## Optimal Mode (NEW in v4.1.2) 🚀

**Optimal mode** combines all the best options for **maximum AI prompt quality**:

```bash
# RECOMMENDED: Maximum quality scan
codetrellis scan ./project --optimal
```

This is equivalent to:

```bash
codetrellis scan ./project --tier logic --deep --parallel --include-progress --include-overview
```

### What `--optimal` enables:

| Feature              | Description                        |
| -------------------- | ---------------------------------- |
| `--tier logic`       | Full function bodies and code flow |
| `--deep`             | LSP type extraction (if available) |
| `--parallel`         | Multi-core processing for speed    |
| `--include-progress` | TODOs, FIXMEs, completion %        |
| `--include-overview` | Project structure and architecture |

### Optimal Mode Output Sections:

1. **[AI_INSTRUCTION]** - Instructions for AI on how to use the context
2. **[PROJECT]** - Name, type, version
3. **[CONTEXT]** - README summary
4. **[ERROR_HANDLING]** - Try-catch patterns and error classes
5. **[ACTIONABLE_ITEMS]** - Priority TODOs/FIXMEs with severity
6. **[PROGRESS]** - Completion %, TODOs, FIXMEs, deprecated items
7. **[OVERVIEW]** - Directory structure and stack detection
8. **[RUNBOOK]** - Commands, version requirements
9. **[BUSINESS_DOMAIN]** - Domain detection, purpose, vocabulary
10. **[DATA_FLOWS]** - Primary data patterns
11. **[PYTHON_TYPES]** - Dataclasses, Pydantic, Protocols, TypedDicts, Enums
12. **[PYTHON_API]** - SQLAlchemy models, Celery tasks, FastAPI/Flask routes
13. **[HOOKS]** - Event hooks, lifecycle callbacks, observer patterns
14. **[MIDDLEWARE]** - Middleware patterns (auth, generic)
15. **[ROUTES_SEMANTIC]** - Routes from generic pattern matching
16. **[LIFECYCLE]** - Init, start, stop phases
17. **[CLI_COMMANDS]** - argparse, click, cobra commands
18. **[IMPLEMENTATION_LOGIC]** - Function bodies, control flow, complexity
19. **[PROGRESS_DETAIL]** - Per-file completion tracking
20. **[PROJECT_STRUCTURE]** - Directory tree with file counts
21. **[BEST_PRACTICES]** - Context-aware coding practices

## Parallel Processing (NEW in v4.1.1)

Speed up scanning with multi-core processing:

```bash
# Auto-detect optimal worker count
codetrellis scan ./project --parallel

# Specify worker count
codetrellis scan ./project --parallel --workers 8
```

## Business Domain Extraction (NEW in v3.1)

CodeTrellis now automatically infers your project's **business domain** and generates semantic context that helps AI understand not just the code, but the **purpose and design decisions** behind it.

### What it detects:

| Category              | Example Output                                           |
| --------------------- | -------------------------------------------------------- |
| **Domain Category**   | Trading/Finance, E-Commerce, Healthcare, Analytics, etc. |
| **Core Entities**     | Trade, Position, Portfolio, Signal, Order                |
| **Domain Vocabulary** | PnL=Profit and Loss, StopLoss=Auto exit price            |
| **Data Flows**        | Backend→Frontend State via WebSocket                     |
| **Arch Decisions**    | "NgRx Signal Store for reactive state management"        |
| **External Systems**  | Broker API, Yahoo Finance API, Groww Trading API         |

### Generated Sections:

```
[BUSINESS_DOMAIN]
domain:Trading/Finance
purpose:A trading application that handles market data, trade execution...
core-entities:Trade,Position,Signal,Portfolio,Order
vocabulary:PnL=Profit and Loss,StopLoss=Auto exit price,Regime=Market condition

[DATA_FLOWS]
primary-pattern:Real-time Streaming
flow:Backend/WebSocket→Frontend State|events:price_update,signal_update

[ARCHITECTURAL_DECISIONS]
decision:State Management|NgRx Signal Store|rationale:Fine-grained reactivity
  evidence:[WorkerTileStore,ExecutionStore,PipelineStore]
decision:Real-time|WebSocket|rationale:Server-push for live updates
```

### Why this matters:

- **AI understands WHY** code exists, not just what it does
- **Better code generation** that matches your domain patterns
- **Accurate terminology** in AI responses
- **Informed refactoring** that preserves design intent

## LSP Deep Mode

Use TypeScript Language Server for 99% accurate type extraction:

```bash
# Enable LSP extraction
codetrellis scan ./project --deep

# Combine with tier
codetrellis scan ./project --deep --tier full
```

**Requirements:** Node.js 18+ must be installed.

**What LSP provides:**

- Fully resolved union types: `"BUY" | "SELL" | "HOLD"`
- Complete generic types
- Class extraction with decorators
- Cross-file type references

## Best Practices Library (BPL) - NEW in v4.2.0 🆕

CodeTrellis includes a **Best Practices Library** with 447+ coding practices that are automatically selected based on your project's detected tech stack.

### Quick Start

```bash
# Include best practices in scan output
codetrellis scan ./project --optimal --include-practices

# Choose format level
codetrellis scan ./project --include-practices --practices-format minimal      # 25 practices, IDs only
codetrellis scan ./project --include-practices --practices-format standard     # 15 practices, brief descriptions
codetrellis scan ./project --include-practices --practices-format comprehensive # 8 practices, full examples
```

### Context-Aware Selection

BPL automatically detects your project's frameworks and selects relevant practices:

| Detected Stack       | Practices Included                                            |
| -------------------- | ------------------------------------------------------------- |
| Angular + TypeScript | NG* (Angular) + TS* (TypeScript) + DP\* (Design Patterns)     |
| NestJS + TypeScript  | TS* (TypeScript) + DP* (Design Patterns)                      |
| Python + FastAPI     | PY* + PYE* (Python) + FAST* (FastAPI) + DP* (Design Patterns) |
| Python + Django      | PY* + PYE* (Python) + DP\* (Design Patterns)                  |
| Python + Flask       | PY* + PYE* (Python) + DP\* (Design Patterns)                  |
| Python + PyTorch     | PY* + PYE* (Python) + DP\* (Design Patterns)                  |
| React + TypeScript   | TS* (TypeScript) + DP* (Design Patterns)                      |
| Go projects          | GO* (Go) + DP* (Design Patterns)                              |
| Python only          | PY* + PYE* (Python) + DP\* (Design Patterns)                  |

### Practice Categories

| Category             | Count | Description                                  |
| -------------------- | ----- | -------------------------------------------- |
| **Python Core**      | 55+   | Type hints, error handling, async, security  |
| **Python 3.10-3.12** | 36    | Version-specific features (match, @override) |
| **TypeScript**       | 42    | Type safety, generics, utility types         |
| **Angular**          | 45    | Signals, standalone components, OnPush       |
| **Design Patterns**  | 30    | Creational, structural, behavioral patterns  |
| **FastAPI**          | 10+   | Authentication, CORS, async DB operations    |
| **Django**           | 10+   | ORM, middleware, views                       |
| **Flask**            | 10+   | Blueprints, extensions, error handling       |
| **PyTorch**          | 10+   | Model architecture, training, data loading   |
| **Pandas**           | 10+   | DataFrames, groupby, merge, I/O              |
| **SQLAlchemy**       | 10+   | Models, relationships, queries               |
| **Pydantic**         | 10+   | Validation, settings, computed fields        |
| **Celery**           | 10+   | Tasks, beat scheduling, retries              |
| **DevOps**           | 15+   | Monitoring, logging, containers, deployment  |
| **Security**         | 15+   | Auth, sanitization, secrets management       |

### Output Formats

#### Minimal Format (25 practices)

Best for token-constrained prompts. IDs and titles only:

```
[BEST_PRACTICES]
# Context: trading-ui | frameworks=[angular, typescript]
# Practices: 25 selected (from 447 available)
## TYPE_SAFETY
  TS037|intermediate|Type Narrowing Techniques
  TS034|intermediate|Built-in Utility Types
  NG001|beginner|Standalone Components by Default
```

#### Standard Format (15 practices) - Default

Balanced detail with brief descriptions:

```
[BEST_PRACTICES]
## TYPE_SAFETY
  TS037|intermediate|Type Narrowing Techniques
    Use typeof, instanceof, in operator for narrowing
  NG001|beginner|Standalone Components by Default
    Use standalone:true instead of NgModules
```

#### Comprehensive Format (8 practices)

Full detail with examples, tags, and references:

```
[BEST_PRACTICES]
## TYPE_SAFETY
  TS037|intermediate|Type Narrowing Techniques
    Description:
      Use various type narrowing techniques: typeof, instanceof...
    Good Examples (1):
      Example 1:
        > if (typeof value === 'string') { ... }
    Tags: type-narrowing, control-flow, type-safety
```

### Practice Filtering

```bash
# Filter by expertise level
codetrellis scan ./project --include-practices --practices-level intermediate

# Filter by categories
codetrellis scan ./project --include-practices --practices-categories type_safety,security

# Combined filtering
codetrellis scan ./project --include-practices \
  --practices-format comprehensive \
  --practices-level advanced \
  --practices-categories architecture,patterns
```

### How Detection Works

CodeTrellis uses **weighted artifact counting** to determine your project's dominant stack:

1. **Counts Python artifacts**: dataclasses, pydantic models, FastAPI endpoints, functions
2. **Counts TypeScript artifacts**: interfaces, types, components, controllers
3. **Applies thresholds**: Only includes a language if it has ≥5 artifacts AND is ≥30% of dominant count
4. **Filters practices**: Uses ID prefix (NG*, TS*, PY\*) to select relevant practices

This ensures:

- A Python project with 2 test TS fixtures → **Python practices only**
- A mixed NestJS + Python project → **Both TS and Python practices**
- An Angular project → **Angular + TypeScript practices**

## Go Language Support (NEW in v4.9.0)

CodeTrellis now fully supports Go projects with enhanced parsing:

### What it extracts:

| Element          | Description                                   |
| ---------------- | --------------------------------------------- |
| **Structs**      | Fields, tags, embedded types, comments        |
| **Interfaces**   | Methods, embedded interfaces, exported status |
| **Functions**    | Parameters (including variadic), return types |
| **Methods**      | Receiver type, pointer receivers              |
| **Constants**    | Const blocks, iota detection, exported values |
| **Type Aliases** | Underlying types                              |
| **Routes**       | Gin, Echo, Chi, net/http route extraction     |
| **gRPC**         | Service interfaces, methods                   |
| **Handlers**     | HTTP handler patterns                         |

```bash
# Scan a Go project
codetrellis scan /path/to/go-project --optimal
```

## AI/ML Extractors (NEW in v4.9.0)

CodeTrellis can now understand AI/ML codebases with dedicated extractors:

### PyTorch Extractor

Extracts model architectures, layers, forward signatures, data loaders, training configs, and Lightning modules.

### HuggingFace Extractor

Extracts models (AutoModel, custom), tokenizers, training args, Trainer configs, pipelines, datasets, and LoRA configs.

### LangChain Extractor

Extracts LLMs, prompt templates, chains (including LCEL), agents, tools, vector stores, retrievers, and memory.

### MLflow Extractor

Extracts experiments, runs, parameter/metric logging, model registration, and autolog configurations.

## Data Infrastructure Extractors (NEW in v4.9.0)

### MongoDB Extractor

Extracts Beanie documents, collections, indexes, aggregation pipelines, and connection configs.

### Redis Extractor

Extracts clients, cache patterns (key/TTL), pub/sub channels, data structures (lists, sets, streams), and cluster configs.

### Kafka Extractor

Extracts producers, consumers, topics, schemas (Avro/JSON/Protobuf), and stream processing.

### Vector Database Extractor

Extracts collections, indexes, queries, and embedding models for Pinecone, Chroma, Qdrant, Weaviate, FAISS, and Milvus.

### Pipeline Orchestration Extractor

Extracts DAGs/flows/assets for Airflow, Prefect, and Dagster with task dependencies and scheduling.

## Plugin Architecture (NEW in v4.9.0)

CodeTrellis now supports a plugin system for extensible language and framework support:

### Plugin Types

| Type        | Description                                 |
| ----------- | ------------------------------------------- |
| `LANGUAGE`  | Adds support for a new programming language |
| `FRAMEWORK` | Adds framework-specific extraction          |
| `EXTRACTOR` | Adds a new extraction capability            |
| `FORMATTER` | Adds a new output format                    |

### Plugin Capabilities

Plugins can provide 21 different capabilities including: interfaces, types, classes, functions, enums, components, services, stores, routes, modules, HTTP API, WebSocket, gRPC, GraphQL, JSDoc, docstrings, README, config, errors, TODOs, and tests.

### Plugin Interfaces

```python
# Language Plugin
class ILanguagePlugin:
    def metadata(self) -> PluginMetadata: ...
    def file_extensions(self) -> list[str]: ...
    def can_parse(self, file_path: str) -> bool: ...
    def parse(self, content: str) -> dict: ...
    def get_extractors(self) -> list[IExtractor]: ...

# Framework Plugin
class IFrameworkPlugin:
    def metadata(self) -> PluginMetadata: ...
    def detect_project(self, path: str) -> bool: ...
    def get_file_patterns(self) -> list[str]: ...
    def get_extractors(self) -> list[IExtractor]: ...
    def get_output_sections(self) -> list[str]: ...
```

## Output Files

```
your-project/
├── .codetrellis/                              # CodeTrellis directory (like .git)
│   ├── config.json                     # Configuration
│   ├── cache/
│   │   └── <version>/
│   │       └── your-project/
│   │           ├── _metadata.json      # Master index with hashes
│   │           ├── matrix.prompt       # THE KEY FILE - inject this!
│   │           └── files/              # Individual file matrices
│   │               └── *.matrix
│   └── hashes.json                     # Change tracking
```

## File Extensions

| Extension | Purpose                                 |
| --------- | --------------------------------------- |
| `.matrix` | Individual file compressed data         |
| `.prompt` | Full project matrix ready for injection |

## Compression Format

### Original (187 lines):

```typescript
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
export enum UserRole {
  SUPER_ADMIN = "super_admin",
  ADMIN = "admin",
  USER = "user",
  VIEWER = "viewer",
}
@Schema({ timestamps: true })
export class User {
  @Prop({ required: true, unique: true })
  email: string;
  // ... 180 more lines
}
```

### Compressed (30 tokens):

```
User|collection:users|fields:email!u,password!,roles[UserRole],status[UserStatus],mfa{},security{}|timestamps|indexes:email
```

## Supported File Types

| Type             | Extension            | Parser                                                    |
| ---------------- | -------------------- | --------------------------------------------------------- |
| TypeScript       | `.ts`                | Schemas, DTOs, Controllers, Services, Guards              |
| Python           | `.py`                | Classes, Functions, Flask/FastAPI routes                  |
| Go               | `.go`                | Structs, Interfaces, Methods, Routes (Gin/Echo/Chi), gRPC |
| Protocol Buffers | `.proto`             | Services, Messages, RPCs                                  |
| Angular          | `.component.ts`      | Components, Inputs, Outputs, Signals                      |
| NestJS           | `.ts`                | Modules, Guards, Interceptors, Pipes, Gateways            |
| JSON             | `.json`              | package.json, tsconfig.json                               |
| TOML             | `.toml`              | pyproject.toml                                            |
| Dockerfile       | `Dockerfile`         | Stages, ports, env vars, healthchecks                     |
| Docker Compose   | `docker-compose.yml` | Services, networks, volumes                               |
| Terraform        | `.tf`                | Resources, variables, outputs, modules                    |
| CI/CD            | `.yml`               | GitHub Actions, GitLab CI, Jenkins, CircleCI              |
| YAML             | `.yaml`              | Hydra configs, structured configs                         |

## CLI Commands

```bash
# Full scan
codetrellis scan [path]           # Scan entire project

# OPTIMAL MODE - Maximum quality (RECOMMENDED)
codetrellis scan [path] --optimal

# Distributed generation
codetrellis distribute [path]     # Generate .codetrellis files in each component folder

# Initialize
codetrellis init [path]           # Initialize CodeTrellis in directory
codetrellis init --ai             # + generate AI integration files (Copilot, Claude, Cursor)
codetrellis init --ai --force     # Overwrite existing AI integration files
codetrellis init --update-ai      # Regenerate AI files from existing matrix (no re-scan)

# Incremental sync
codetrellis sync                  # Sync only changed files
codetrellis sync --file path.ts   # Sync specific file

# View matrix
codetrellis show                  # Show full matrix
codetrellis show --service nexu-shield  # Show service only
codetrellis show --schemas        # Show schemas only

# Watch mode
codetrellis watch                 # Auto-sync on file changes

# Export
codetrellis prompt                # Print prompt-ready matrix
codetrellis prompt --tokens       # Show token count
codetrellis export --json         # Export as JSON

# Validation & Coverage
codetrellis validate [path]       # Validate extraction completeness
codetrellis coverage [path]       # Show extraction coverage

# Progress & Overview
codetrellis progress [path]       # Show project progress (TODOs, completion, blockers)
codetrellis overview [path]       # Show project overview for onboarding
codetrellis onboard [path]        # Interactive onboarding guide

# Plugin Management
codetrellis plugins               # Manage plugins

# A5.x: Cache Optimization (NEW)
codetrellis scan . --cache-optimize  # Scan with cache-optimized section ordering
codetrellis cache-optimize --stats   # Show section stability statistics

# A5.x: MCP Server (NEW)
codetrellis mcp --stdio              # Start MCP server (JSON-RPC 2.0 over stdio)

# A5.x: JIT Context (NEW)
codetrellis context path/to/file.py  # Get file-relevant context
codetrellis context path/to/file.py --sections-only  # Show section names only

# A5.x: AI Skills (NEW)
codetrellis skills                   # Generate AI-executable skills from matrix
```

## A5.x: AI Prompt Optimization Suite (NEW)

CodeTrellis now includes 4 advanced modules that optimize how compressed context is delivered to AI models:

### Cache Optimizer (A5.1)

Reorders sections by stability tier for maximum LLM KV-cache reuse. Stable content (types, schemas, dependencies) appears first, volatile content (implementation logic, progress) appears last.

```bash
# Scan with cache-optimized ordering
codetrellis scan ./project --cache-optimize

# View stability statistics for all sections
codetrellis cache-optimize --stats
```

**Stability tiers:** STATIC → STRUCTURAL → SEMANTIC → VOLATILE

This can reduce token costs by 30-50% on repeated prompts because the LLM's KV-cache retains stable prefix sections across requests.

### MCP Server (A5.2)

Exposes project context via the [Model Context Protocol](https://modelcontextprotocol.io/) (JSON-RPC 2.0). AI tools can query specific aggregate resources instead of loading the full matrix.

```bash
# Start MCP server
codetrellis mcp --stdio
```

**Aggregate resources (8 categories):**

| Resource         | Description                                   |
| ---------------- | --------------------------------------------- |
| `types`          | All type/class/interface definitions          |
| `api`            | All API endpoints and routes (52 sections)    |
| `state`          | State management (Redux, Zustand, MobX, etc.) |
| `components`     | UI components (React, Vue, Svelte, etc.)      |
| `styling`        | CSS, Sass, Tailwind, styled-components        |
| `routing`        | File-based & programmatic routing             |
| `overview`       | Project metadata, domain, runbook             |
| `infrastructure` | Dependencies, Docker, Terraform, CI/CD        |

### JIT Context Provider (A5.3)

Selects only the most relevant sections based on the file currently being edited. Instead of loading the entire matrix (~15K tokens), the JIT provider delivers ~3-5K tokens of targeted context.

```bash
# Get context relevant to a specific file
codetrellis context src/components/UserCard.tsx

# See which sections would be selected
codetrellis context src/components/UserCard.tsx --sections-only
```

**How it works:**

- Maps file extensions to relevant sections (`.py` → Python sections, `.tsx` → React + TypeScript + state management)
- Matches path patterns to framework sections (`/components/` → component sections, `/store/` → state sections)
- Always includes universal sections: PROJECT, BEST_PRACTICES, RUNBOOK

### AI Skills Generator (A5.5)

Auto-generates AI-executable skill definitions from your project's detected capabilities. Skills are context-aware actions that an AI can perform.

```bash
# Generate skills from project matrix
codetrellis skills
```

**Example output:**

```
Found 10 skills for this project:
  1. add-component  - Add a new UI component (React, Vue, Svelte detected)
  2. add-endpoint   - Add a new API endpoint (Express, FastAPI detected)
  3. add-store      - Add a new state store (Zustand, Redux detected)
  4. add-model      - Add a new data model (Prisma, TypeORM detected)
  5. add-test       - Add a new test file
  6. add-style      - Add a new stylesheet (Tailwind, CSS detected)
  7. add-route      - Add a new route/page (Next.js detected)
  ...
```

**17 skill templates** covering components, stores, endpoints, models, hooks, styles, routes, data fetching, tests, migrations, configs, types, middleware, plugins, pages, guards, and interceptors.

---

## Integration

### VS Code Extension

Coming soon - automatically injects matrix into Copilot prompts.

### Manual Injection

Copy the content of `.codetrellis/cache/<version>/project/matrix.prompt` and paste at the start of your prompt.

### CI/CD Hook

```yaml
# .github/workflows.codetrellis.yml
- name: Update CodeTrellis Matrix
  run: codetrellis sync
```

## Configuration

`.codetrellis/config.json`:

```json
{
  "version": "1.0.0",
  "project": "ns-brain",
  "ignore": ["node_modules", "dist", ".git", "__pycache__", "*.spec.ts"],
  "parsers": {
    "typescript": true,
    "python": true,
    "proto": true,
    "angular": true
  },
  "maxTokens": 2000,
  "compression": "high"
}
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit PR

## License

MIT License - Keshav Chaudhary 2026
