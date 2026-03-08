# CodeTrellis: Matrix + CLI Fusion — Future Enhancement Plan

> **Version:** 1.0.0  
> **Date:** 19 February 2026  
> **Author:** Keshav Chaudhary  
> **Status:** ROADMAP  
> **Applies to:** CodeTrellis v4.9.0+ (Python), vscode-codetrellis-chat v0.1.0+ (TypeScript)

---

## Vision

**Make every AI interaction—CLI, IDE, or API—start with complete project awareness, not a blank slate.**

Today, AI CLI tools (Claude Code, Gemini CLI, aider, Copilot CLI) work blind: they read files one-by-one, spending 30-60% of their token budget just *discovering* the project before they can help. CodeTrellis Matrix solves this by pre-computing a structured, compressed project map. The future is combining both: **Matrix as the knowledge layer, CLI tools as the action layer.**

```
┌──────────────────────────────────────────────────────────────────┐
│                         THE VISION                                │
│                                                                   │
│   Matrix (Pre-computed Knowledge)  +  CLI (Live Execution)       │
│   ═══════════════════════════════     ════════════════════        │
│   • 94K tokens of structured context  • File read/write           │
│   • Every schema, route, API          • Terminal commands          │
│   • Business domain & patterns        • Test execution             │
│   • TODOs, FIXMEs, progress           • Git operations             │
│   • Best practices                    • Package management         │
│   • Cross-file relationships          • Live debugging             │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │              AI with FULL project awareness             │    │
│   │              + LIVE editing capabilities                │    │
│   │              = 10x more accurate responses              │    │
│   └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Current State (February 2026)

### What Exists Today

| Component | Status | Location |
|-----------|--------|----------|
| **Matrix Generator** (Python CLI) | ✅ Production | `codetrellis/` — 484 files, 60+ parsers, 34 sections |
| **VS Code Chat Extension** | ✅ v0.1.0 | `vscode-codetrellis-chat/` — Chat participant, inline completions, tools |
| **Prompt Renderer** | ✅ Built | `src/platform/prompt/promptRenderer.ts` — Token budgeting, section priority |
| **Memory Context Injector** | ✅ Built | `src/platform/memory/memoryContextInjector.ts` — Relevance scoring, tag filtering |
| **Tool Execution Engine** | ✅ Built | `src/platform/tools/toolExecutionEngine.ts` — Sandboxed tool calls |
| **Plugin Command Discovery** | ✅ Built | Reads `.codetrellis/commands/` for custom tools |
| **Agent Skill Provider** | ✅ Built | Reads `.codetrellis/agents/` for workspace agents |
| **Watcher** | ⚠️ Stub | `codetrellis/watcher.py` — watchdog events but full rescan |
| **Incremental Build** | ❌ Missing | Two TODOs in cli.py |
| **Matrix ↔ Extension Bridge** | ❌ Missing | No integration between Python matrix and TS extension |

### The Gap

The Python matrix generator and the VS Code extension are **two disconnected systems**. The extension has its own context discovery (workspace search, file reading, git context, diagnostics) but doesn't know about the matrix. The matrix has deep project knowledge but can't act on files.

---

## Competitive Landscape: How AI CLIs Handle Context

### Context Strategy Comparison

| Capability | Claude Code | Gemini CLI | GitHub Copilot CLI | aider | **Matrix + CLI (Target)** |
|------------|-------------|------------|-------------------|-------|---------------------------|
| **Initial context loading** | Reads CLAUDE.md + ~5-10 files | Reads Gemini rules + workspace index | Reads .github/copilot-instructions.md | Reads .aider conventions | **94K tokens of structured matrix — every file pre-analyzed** |
| **Context tokens at start** | ~5-15K | ~10-20K | ~5-10K | ~5-10K | **~94K (matrix.prompt)** |
| **Discovery method** | `cat`, `grep`, `find` (reactive) | Workspace indexing + search | Workspace index + semantic search | git-aware file listing | **Pre-computed: 0 tool calls needed** |
| **Cross-file awareness** | Low (reads one file at a time) | Medium (workspace index) | Medium (semantic index) | Low-Medium (repo map) | **High — all relationships pre-extracted** |
| **Business domain knowledge** | None | None | None | None | **`[BUSINESS_DOMAIN]` section built-in** |
| **Architecture awareness** | Inferred, often incomplete | Partial via indexing | Partial via semantic search | Repo map (tree-sitter) | **`[OVERVIEW]`, `[PROJECT_STRUCTURE]`, patterns detected** |
| **Best practices enforcement** | Generic LLM knowledge | Generic | Generic | None | **`[BEST_PRACTICES]` — project-specific rules** |
| **TODO/Progress tracking** | Must grep | None | None | None | **`[ACTIONABLE_ITEMS]`, `[PROGRESS]` pre-indexed** |
| **Runbook (build/test/deploy)** | Must find README/Makefile | None | None | None | **`[RUNBOOK]` with exact commands, env vars** |
| **Dependency graph** | Reads package.json on demand | Partial | Partial | None | **Full dependency tree with versions** |
| **Data model awareness** | Reads schema files on demand | None | Partial | None | **1,275 dataclasses, all interfaces, all types** |
| **API endpoint map** | None until reads routes | None | None | None | **All endpoints, routes, WebSocket events** |
| **Infrastructure context** | None | None | None | None | **Docker, Terraform, CI/CD pipelines** |
| **Watch/incremental** | Live (always current) | Live | Live | git diff tracking | **Target: incremental matrix with <2s update** |
| **File editing** | ✅ Direct edits | ✅ Direct edits | ✅ (via Copilot Edits) | ✅ Direct edits + git | **✅ Via VS Code extension tools** |
| **Terminal execution** | ✅ Shell access | ✅ Shell access | ⚠️ Limited | ✅ Shell access | **✅ Via toolExecutionEngine** |

### Token Efficiency Analysis

For a project the size of CodeTrellis (484 files, 8.78 MB source):

| Approach | Tokens to achieve full awareness | Tool calls needed | Time to full context |
|----------|----------------------------------|-------------------|---------------------|
| Claude Code (reactive) | ~200K+ (reading files one by one) | ~100+ tool calls | 3-5 minutes |
| Gemini CLI (indexed) | ~50-80K (workspace index) | ~20-30 tool calls | 1-2 minutes |
| aider (repo map) | ~30-50K (tree-sitter map) | ~10-15 calls | 30-60 seconds |
| **Matrix prompt (pre-computed)** | **94K (one injection)** | **0 tool calls** | **0 seconds** |
| **Matrix + CLI (target)** | **94K + targeted reads** | **2-5 tool calls** | **<10 seconds** |

---

## Enhancement Phases

### Phase 1: Matrix Bridge (Months 1-2)
**Connect the Python matrix to the VS Code extension.**

#### 1.1 Matrix File Watcher in Extension

```
vscode-codetrellis-chat/src/platform/matrix/
├── matrixFileWatcher.ts         # Watch .codetrellis/cache/ for changes
├── matrixFileWatcher.spec.ts
├── matrixParser.ts              # Parse matrix.prompt sections
├── matrixParser.spec.ts
├── matrixContextProvider.ts     # Provide matrix as PromptSection
├── matrixContextProvider.spec.ts
└── index.ts
```

**What it does:**
- Watch `.codetrellis/cache/{VER}/{project}/matrix.prompt` for changes
- Parse the 34 sections into a structured TypeScript object
- Expose as an `IMatrixContextProvider` service via DI
- Register as a `PromptSection` with `SectionPriority.High` in the prompt renderer
- Token budget: configurable, default 8,000 tokens from matrix

**Key integration point — `promptRenderer.ts`:**
```typescript
// New section injected automatically when matrix exists:
{
  identifier: "codetrellis_matrix",
  role: "system",
  content: matrixContextProvider.getCompressedContext(),
  priority: SectionPriority.High,
  maxTokens: 8_000,
  trimmable: true,
}
```

#### 1.2 Auto-Scan Trigger

- On workspace open: check if `.codetrellis/cache/` exists
- If stale (>1 hour) or missing: offer to run `codetrellis scan`
- If Python not installed: show guidance
- Status bar indicator: "Matrix: ✅ Fresh" or "Matrix: ⚠️ Stale (2h ago)"

#### 1.3 Matrix-Aware Chat Commands

| Command | Behavior |
|---------|----------|
| `@codetrellis /scan` | Trigger `codetrellis scan . --optimal` via terminal |
| `@codetrellis /architecture` | Show project architecture from `[OVERVIEW]` section |
| `@codetrellis /todos` | Show actionable items from `[ACTIONABLE_ITEMS]` |
| `@codetrellis /runbook` | Show build/test/deploy commands from `[RUNBOOK]` |
| `@codetrellis /practices` | Show best practices from `[BEST_PRACTICES]` |
| `@codetrellis /domain` | Show business domain context from `[BUSINESS_DOMAIN]` |

**Complexity:** Medium  
**Files touched:** `chatParticipantAdapter.ts`, new `matrixCommandHandler.ts`  
**Tests:** Unit + integration  
**Rollback:** Feature flag `codetrellis.chat.matrixIntegration`

---

### Phase 2: Intelligent Context Fusion (Months 3-4)
**Make the matrix and live context work together, not separately.**

#### 2.1 Context Priority Engine

Current problem: The extension has multiple context sources (active file, diagnostics, git diff, semantic search, memory). Adding matrix creates overlap. Solution: a priority engine that deduplicates and ranks.

```
┌─────────────────────────────────────────────────────┐
│            Context Priority Engine                   │
│                                                      │
│  Source               Priority   Max Tokens  Scope   │
│  ─────────────────    ────────   ──────────  ─────   │
│  System prompt        Critical   500         Always  │
│  User instructions    Critical   1,000       Always  │
│  Matrix: relevant     High       4,000       Auto    │
│  Active file          High       3,000       Always  │
│  Diagnostics          High       1,000       Auto    │
│  Git diff             Medium     2,000       Auto    │
│  Semantic search      Medium     3,000       Query   │
│  Memory               Medium     2,000       Auto    │
│  Matrix: full         Low        8,000       On-ask  │
│  Conversation history Low        4,000       Always  │
│                                                      │
│  Total budget: ~30K tokens (adjustable per model)    │
└─────────────────────────────────────────────────────┘
```

**Key insight:** Don't dump the entire matrix into every prompt. Use the matrix as a **lookup table** — inject only the sections relevant to the user's query.

#### 2.2 Query-Aware Matrix Slicing

When the user asks "add caching to the scanner", the engine should:
1. Parse the query for domain terms: `caching`, `scanner`
2. Look up matrix sections mentioning those terms
3. Inject relevant slices: scanner's implementation logic, streaming config, cache config
4. Skip irrelevant sections: Dart parser, Ruby parser, Less CSS, etc.

```typescript
interface MatrixSlice {
  section: string;       // e.g., "[IMPLEMENTATION_LOGIC]"
  relevance: number;     // 0.0 - 1.0
  tokenCost: number;     // estimated tokens
  content: string;       // the slice content
}

// For "add caching to scanner":
// → [IMPLEMENTATION_LOGIC] scanner.py slice   (relevance: 0.95)
// → [IMPLEMENTATION_LOGIC] streaming.py slice  (relevance: 0.85)
// → [IMPLEMENTATION_LOGIC] cache references    (relevance: 0.80)
// → [PYTHON_TYPES] StreamingConfig             (relevance: 0.75)
// → [ACTIONABLE_ITEMS] cache TODOs             (relevance: 0.70)
```

#### 2.3 Live + Matrix Hybrid Tools

Extend the tool registry with matrix-powered tools:

| Tool | What it does | Matrix data used |
|------|-------------|-----------------|
| `findRelatedFiles` | Given a file, find all related files (imports, cross-references) | `[IMPLEMENTATION_LOGIC]` dependency info |
| `getApiEndpoints` | List all API endpoints matching a pattern | `[PYTHON_API]`, `[ROUTES_SEMANTIC]` |
| `getDataModel` | Show schema/model for an entity | `[PYTHON_TYPES]` dataclasses, `[TS_TYPES]` interfaces |
| `getArchitectureContext` | Show how a module fits in the architecture | `[OVERVIEW]`, `[PROJECT_STRUCTURE]` |
| `suggestPractice` | Recommend a best practice for the current context | `[BEST_PRACTICES]` |
| `checkProgress` | Show completion status of current file/module | `[PROGRESS]`, `[ACTIONABLE_ITEMS]` |

**Complexity:** Large  
**Files touched:** `toolRegistry.ts`, `builtinTools.ts`, new matrix tool providers  
**Tests:** Unit + integration + E2E  
**Rollback:** Tools are additive; disable via config

---

### Phase 3: Auto-Compilation Pipeline (Months 5-6)
**Matrix generation becomes invisible — always fresh, always fast.**

#### 3.1 Incremental Matrix in the Extension

Instead of running the full Python CLI every time:

```
File saved → Extension detects change → 
  Sends changed file path to Python background process →
    Python does incremental extractor run (only affected extractors) →
      Extension receives updated JSON patch →
        Merges into in-memory matrix →
          Next AI query uses fresh context
```

**Implementation:**
- Python side: `codetrellis scan --incremental --json-patch --file <path>`
- Extension side: `matrixIncrementalUpdater.ts` — receives JSON patch, merges
- Latency target: <500ms for single file change

#### 3.2 Background Matrix Service

A persistent Python process that:
- Starts when workspace opens
- Maintains file hash table in memory
- Listens for file change events from the extension
- Runs incremental extractions immediately
- Pushes updates to the extension via stdout JSON-RPC

```
┌──────────────────┐     JSON-RPC     ┌──────────────────┐
│  VS Code Extension│ ◄──────────────► │ Python Matrix    │
│  (TypeScript)     │   stdin/stdout   │ Service (daemon) │
│                   │                  │                   │
│  matrixBridge.ts  │  "fileChanged"   │ matrix_server.py  │
│                   │  ────────────►   │                   │
│                   │                  │  incremental_scan()│
│                   │  "matrixPatch"   │                   │
│                   │  ◄────────────   │                   │
└──────────────────┘                  └──────────────────┘
```

#### 3.3 Matrix Freshness Indicator

VS Code status bar item:
```
CodeTrellis: 🟢 Live (484 files, 94K tokens, updated 3s ago)
CodeTrellis: 🟡 Syncing... (2 files changed)
CodeTrellis: 🔴 Stale (last scan 2h ago — click to refresh)
CodeTrellis: ⚪ Not scanned (click to initialize)
```

**Complexity:** Large  
**New files:** `matrix_server.py` (Python), `matrixBridge.ts`, `matrixStatusBar.ts`  
**Tests:** Integration tests with mock Python process  
**Rollback:** Fall back to file-based matrix reading

---

### Phase 4: Multi-AI CLI Integration (Months 7-9)
**Make matrix context available to any AI CLI tool, not just CodeTrellis Chat.**

#### 4.1 Universal Context File (`.codetrellis/context.md`)

Generate a Markdown file designed to be auto-detected by any AI CLI:

```markdown
<!-- .codetrellis/context.md — Auto-generated by CodeTrellis v4.16.0 -->
<!-- This file provides project context for AI assistants -->
<!-- Recognized by: Claude Code (CLAUDE.md), aider (.aider.conf), Copilot -->

# Project: codetrellis
Type: Python Library | Version: 4.16.0 | Python >=3.9

## Architecture
- 484 source files across 6 key directories
- 60+ language parsers (Python, TypeScript, Go, Rust, Java, ...)
- Pattern: CLI → Scanner → Extractors → Compressor → Output
- Entry point: `codetrellis.cli:main`

## Key Types (1,275 dataclasses)
[Top 20 most-referenced types listed here]

## Commands
- `codetrellis scan . --optimal` — Full analysis
- `pytest tests/ -v` — Run tests
- `pip install -e .` — Install for development

## Current Work
- 9 TODOs, 1 FIXME, 90 placeholders
- Priority: incremental sync (cli.py:718)

## Best Practices
- Use type hints, docstrings, pytest
- Avoid print(), global state, mutable defaults
```

This file serves as a **universal adapter** — Claude Code reads it as CLAUDE.md content, aider picks it up as project context, and any future AI CLI can consume it.

#### 4.2 CLI Tool Adapters

| Tool | Integration Method | Config File |
|------|-------------------|-------------|
| **Claude Code** | Symlink `.codetrellis/context.md` → `CLAUDE.md` | Auto-generate `CLAUDE.md` |
| **Gemini CLI** | Symlink → `.gemini/style_guide.md` | Auto-generate Gemini rules |
| **aider** | Generate `.aider.conf.yml` with matrix refs | `.aider.conf.yml` template |
| **Copilot CLI** | Use `.github/copilot-instructions.md` | Auto-generate from matrix |
| **Cursor** | Use `.cursor/rules` directory | Auto-generate rules files |
| **Windsurf** | Use `.windsurfrules` | Auto-generate rules file |

**New CLI command:**
```bash
# Generate context files for all detected AI tools
codetrellis export-context . --all

# Generate for specific tool
codetrellis export-context . --claude
codetrellis export-context . --aider
codetrellis export-context . --cursor
codetrellis export-context . --copilot
```

#### 4.3 MCP Server (Model Context Protocol)

Implement CodeTrellis as an MCP server that any MCP-compatible client can query:

```json
{
  "name": "codetrellis-mcp",
  "tools": [
    {
      "name": "getProjectContext",
      "description": "Get complete project context from CodeTrellis matrix",
      "parameters": { "sections": ["OVERVIEW", "PYTHON_TYPES", "BEST_PRACTICES"] }
    },
    {
      "name": "getFileContext",
      "description": "Get matrix context for a specific file",
      "parameters": { "filePath": "string" }
    },
    {
      "name": "searchContext",
      "description": "Search matrix for relevant context by query",
      "parameters": { "query": "string", "maxTokens": "number" }
    },
    {
      "name": "getActionableItems",
      "description": "Get TODOs, FIXMEs, and placeholders",
      "parameters": { "priority": "HIGH|NORMAL|LOW" }
    }
  ]
}
```

This makes matrix context available to Claude Desktop, VS Code Copilot, Cline, Continue, and any future MCP client.

**Complexity:** Large  
**New files:** `codetrellis/mcp_server.py`, `codetrellis/context_exporter.py`  
**Tests:** MCP protocol compliance tests  
**Rollback:** MCP server is a separate entry point; doesn't affect core

---

### Phase 5: Intelligent Agent Mode (Months 10-12)
**The AI doesn't just read the matrix — it maintains it.**

#### 5.1 Self-Healing Matrix

After the AI makes code changes, automatically:
1. Detect which files were modified
2. Run incremental matrix extraction on those files
3. Update matrix context for the next interaction
4. Verify the changes don't break quality gates

```
User: "Add Redis caching to the user service"
  ↓
AI reads matrix → understands full architecture
  ↓
AI writes code changes to 3 files
  ↓
Matrix auto-updates (incremental, <500ms)
  ↓
AI reads updated matrix → verifies consistency
  ↓
AI: "Done. Matrix updated. No quality gate violations."
```

#### 5.2 Predictive Context Loading

Based on:
- The file the user is editing
- Recent git history
- The user's question pattern

Pre-load relevant matrix slices before the user asks:

```
User opens scanner.py
  → Matrix engine pre-loads:
    • scanner.py implementation logic (90 functions)
    • Related files: streaming.py, parallel.py, watcher.py
    • scanner TODOs and FIXMEs
    • Scanner's dependencies in the extractor graph
    • Relevant best practices for Python code quality
  → All ready before the user types anything
```

#### 5.3 Cross-Project Matrix Federation

For monorepos or multi-repo setups:

```
workspace/
├── frontend/      → matrix: Angular app (components, routes, stores)
├── backend/       → matrix: NestJS API (controllers, schemas, DTOs)
├── shared/        → matrix: Shared library (interfaces, types)
└── infra/         → matrix: Terraform + Docker (resources, pipelines)

Federated query: "How does the user profile flow from frontend to database?"
  → Reads frontend matrix: UserProfileComponent → UserService → API calls
  → Reads backend matrix: UserController → UserService → UserRepository
  → Reads shared matrix: UserDTO, UserSchema interfaces
  → Reads infra matrix: PostgreSQL setup, Redis cache
  → Complete end-to-end answer
```

**Complexity:** Very Large  
**New modules:** `codetrellis/federation/`, `matrixFederator.ts`  
**Tests:** Multi-project integration tests  
**Rollback:** Federation is opt-in; each project works standalone

---

## Metrics & Success Criteria

### Quantitative Targets

| Metric | Current (CLI only) | Phase 1 | Phase 3 | Phase 5 |
|--------|-------------------|---------|---------|---------|
| Tokens to full awareness | ~200K (reactive) | 94K (matrix) | 94K (always fresh) | 94K + predictive |
| Tool calls before first useful answer | 5-10 | 0-2 | 0 | 0 |
| Time to full context | 60-180s | 0s (pre-loaded) | 0s (live) | 0s (predicted) |
| Cross-file accuracy | ~40% | ~85% | ~90% | ~95% |
| Architecture-aware responses | ~20% | ~80% | ~90% | ~95% |
| Stale context risk | Low (live) | Medium (snapshot) | Low (incremental) | Very Low (live) |
| Project-specific best practices | 0% | 100% | 100% | 100% |

### Qualitative Targets

- **Developer survey:** "AI understood my project" score ≥ 4/5
- **First-interaction accuracy:** AI's first response addresses the right files ≥ 90% of the time
- **Zero hallucinated file paths** in responses when matrix is loaded
- **Correct framework version usage** in generated code (e.g., Angular 20 signals, not Angular 14 modules)

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Matrix becomes stale mid-session | Medium | High (today) | Phase 3: incremental updates, freshness indicator |
| Token budget overflow (matrix too large for model context) | High | Medium | Phase 2: query-aware slicing, configurable budget |
| Python not installed in user's environment | Medium | Medium | Phase 4: pre-built binaries, WASM port, or TS-native scanner |
| MCP protocol changes | Low | Low | Phase 4: abstraction layer over MCP |
| Performance regression from always-on matrix service | Medium | Medium | Phase 3: configurable, can disable; lazy startup |
| Privacy concerns with matrix content | High | Low | Phase 1: `.codetrellis-ignore` support, no secrets scanning |

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Matrix ↔ Extension communication | JSON-RPC over stdin/stdout | Standard, used by LSP; no network port needed |
| Incremental update format | JSON Patch (RFC 6902) | Standard, minimal payload, merge-friendly |
| MCP server runtime | Python (same as matrix generator) | Reuse existing extractors; no duplication |
| Universal context format | Markdown (`.codetrellis/context.md`) | Human-readable, consumed by all AI CLIs |
| Cache invalidation | Content-addressed (SHA-256) | Deterministic, no timestamp-based staleness |
| Extension ↔ Matrix token budget | Configurable per model | GPT-4o (128K) vs Claude Haiku (200K) need different budgets |

---

## Immediate Next Steps

### This Week (Days 1-7)

1. **Create `matrixParser.ts`** — Parse `matrix.prompt` sections into a TypeScript map
2. **Create `matrixContextProvider.ts`** — Register matrix as a `PromptSection` in the prompt renderer
3. **Add `@codetrellis /scan` command** — Trigger Python CLI from the chat participant

### This Month (Days 8-30)

4. **Wire matrix into prompt renderer** — Auto-inject relevant matrix sections into every chat prompt
5. **Add status bar indicator** — Show matrix freshness
6. **Implement query-aware slicing** — Don't dump all 94K tokens; pick relevant sections
7. **Add `codetrellis export-context --claude` command** — Generate CLAUDE.md from matrix

### This Quarter (Days 31-90)

8. **Build incremental matrix update pipeline** — Python daemon + extension bridge
9. **Implement MCP server** — Expose matrix as MCP tools
10. **Multi-AI CLI adapters** — Export context for Cursor, aider, Gemini CLI

---

## Appendix A: Token Budget Models

### Model-Specific Budgets

| Model | Context Window | Matrix Budget | Live Context | Conversation | Safety Margin |
|-------|---------------|---------------|--------------|--------------|---------------|
| GPT-4o | 128K | 8,000 | 6,000 | 8,000 | 20% |
| GPT-4o-mini | 128K | 6,000 | 4,000 | 6,000 | 20% |
| o3-mini | 128K | 8,000 | 6,000 | 8,000 | 20% |
| Claude 3.5 Sonnet | 200K | 12,000 | 8,000 | 10,000 | 20% |
| Claude 3.5 Haiku | 200K | 10,000 | 6,000 | 8,000 | 20% |
| Gemini 2.0 Flash | 1M | 30,000 | 15,000 | 15,000 | 20% |
| Gemini 1.5 Pro | 2M | 50,000 | 20,000 | 20,000 | 20% |

### Budget Allocation Strategy

For Gemini's 1M+ context window, inject the *full* matrix.prompt (94K tokens). For smaller windows, use query-aware slicing to pick the most relevant ~8K tokens.

---

## Appendix B: File Manifest (New Files)

### Python (codetrellis/)

| File | Phase | Purpose |
|------|-------|---------|
| `codetrellis/matrix_server.py` | 3 | Background daemon for incremental matrix |
| `codetrellis/context_exporter.py` | 4 | Export context for Claude/aider/Cursor/etc. |
| `codetrellis/mcp_server.py` | 4 | MCP protocol server |
| `codetrellis/builder.py` | 1 | Build orchestrator (from auto-compilation plan) |
| `codetrellis/cache.py` | 1 | Cache manager with lockfile |
| `codetrellis/federation/` | 5 | Cross-project matrix federation |

### TypeScript (vscode-codetrellis-chat/src/)

| File | Phase | Purpose |
|------|-------|---------|
| `platform/matrix/matrixParser.ts` | 1 | Parse matrix.prompt sections |
| `platform/matrix/matrixContextProvider.ts` | 1 | Provide matrix as prompt context |
| `platform/matrix/matrixFileWatcher.ts` | 1 | Watch matrix files for changes |
| `platform/matrix/matrixQuerySlicer.ts` | 2 | Query-aware section selection |
| `platform/matrix/matrixBridge.ts` | 3 | JSON-RPC bridge to Python daemon |
| `platform/matrix/matrixStatusBar.ts` | 3 | Status bar freshness indicator |
| `platform/matrix/matrixFederator.ts` | 5 | Cross-project federation client |
| `extension/matrixCommandHandler.ts` | 1 | Chat commands for matrix operations |
