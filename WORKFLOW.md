# CodeTrellis — Daily Workflow & Next Steps

> **For:** Keshav Chaudhary  
> **Date:** 20 February 2026  
> **Version:** v4.69

---

## Part 1: Integration Setup (One-Time)

Run `codetrellis init . --ai` to automatically scan your project and generate enriched AI integration files. This command runs an optimal scan first, then uses the resulting matrix data (business domain, architecture, commands) to populate the AI configs.

### ✅ GitHub Copilot (VS Code) — DONE

| File                              | Purpose                                                       | Status     |
| --------------------------------- | ------------------------------------------------------------- | ---------- |
| `.github/copilot-instructions.md` | Copilot reads this for every chat + inline completion         | ✅ Created |
| `.vscode/mcp.json`                | Registers CodeTrellis as an MCP server that Copilot can query | ✅ Created |
| `.vscode/tasks.json`              | One-click tasks: Watch, Scan, Verify, Test, Show              | ✅ Created |

**How it works with Copilot:**

1. **Copilot Chat** reads `.github/copilot-instructions.md` automatically — it now knows your project architecture, conventions, and rules.
2. **MCP Server** (`.vscode/mcp.json`) — Copilot can call `search_matrix()`, `get_section()`, `get_context_for_file()` directly. Start by clicking "Start" on the MCP server in VS Code's MCP panel, or it starts automatically when Copilot queries it.
3. **Watch Task** — Set to `runOn: folderOpen`, so the matrix auto-rebuilds when you open the workspace.

> **MCP Data Flow (v4.69):** `codetrellis scan` → `scanner.scan()` → `ProjectMatrix` → `MatrixCompressor.compress()` → `matrix.prompt` → MCP server reads `matrix.prompt` → `_parse_into_sections()` splits on `[SECTION_NAME]` headers → each section served via `get_section(name)` / `search_matrix(query)` / `get_context_for_file(path)`. The default PROMPT tier now includes **IMPLEMENTATION_LOGIC** (function bodies, control flow, ~2,300 lines) and expanded **BEST_PRACTICES** (auto-detected for 15+ languages and 20+ frameworks). **⚠️ Critical: Never round-trip `ProjectMatrix` through JSON without a proper `from_dict()` deserializer — the compressor requires a live object.**

### ✅ Claude Code — DONE

| File        | Purpose                                 | Status     |
| ----------- | --------------------------------------- | ---------- |
| `CLAUDE.md` | Claude Code reads this at session start | ✅ Created |

### ✅ Claude Desktop — DONE

| File                               | Purpose                                            | Status     |
| ---------------------------------- | -------------------------------------------------- | ---------- |
| `docs/CLAUDE_DESKTOP_MCP_SETUP.md` | Copy JSON config into `claude_desktop_config.json` | ✅ Created |

### ✅ Cursor — DONE

| File           | Purpose                                 | Status     |
| -------------- | --------------------------------------- | ---------- |
| `.cursorrules` | Cursor reads this for every interaction | ✅ Created |

---

## Part 2: Daily Workflow Checklist

### Morning (Start of Session)

```
1. Open VS Code in the CodeTrellis workspace
   └── Watch task auto-starts (rebuilds matrix on file save)

2. If starting a Copilot Chat session:
   └── The MCP server is available — Copilot already has your instructions
   └── For maximum context, attach matrix.prompt to chat:
       codetrellis prompt | pbcopy
       (then paste into chat, or attach the file directly)

3. If using Claude Desktop:
   └── MCP server is running — Claude can query sections directly
   └── Ask: "Search the matrix for [topic]" and it will use search_matrix()

4. If using Claude Code:
   └── CLAUDE.md is auto-loaded — Claude knows commands, conventions, architecture
```

### During Development

```
1. Code normally — matrix auto-updates via watch mode
   └── Watch mode now uses threading.Lock + 2s debounce + batch callbacks (v4.69 fix)
   └── Thread-safe: no more "Set changed size during iteration" crashes

2. Before asking AI a complex question:
   └── The AI already knows your codebase (no need to explain)
   └── Just ask directly: "Add a new extractor for Zig language"
   └── The AI knows the pattern: {language}_parser_enhanced.py,
       scanner.py integration, compressor.py sections, bpl/selector.py

3. After major changes (new module, refactor):
   └── Run: codetrellis scan . --optimal
   └── This does a full rescan (not just incremental)

4. Before committing:
   └── Run: codetrellis verify .
   └── Ensures matrix quality gates pass
```

### End of Session

```
1. Matrix is already up-to-date (watch mode kept it current)
2. Commit the matrix files if you want teammates to benefit:
   └── git add .codetrellis/cache/4.16.0/codetrellis/matrix.prompt
   └── (optional — .gitignore if matrix is personal)
```

---

## Part 3: Next Steps — 3 High-Value Projects

### 🥇 Project 1: `codetrellis-vscode` Extension (Highest Impact)

**What:** A proper VS Code extension that wraps CodeTrellis into a first-class editor experience.

**Why:** Right now you run CLI commands. An extension would:

- Show matrix sections in a sidebar tree view
- Auto-inject context into Copilot via the Extension API
- Provide "Explain this file" commands that pull JIT context
- Show inline decorations (TODOs, complexity, type coverage)
- Offer a "Matrix Explorer" webview with search

**Effort:** ~2 weeks for MVP. You already have the MCP server, JIT context, and skills generator — the extension just wraps them.

**First step:** `yo code` → TypeScript extension → register TreeDataProvider for matrix sections → register commands for `search_matrix` and `get_context_for_file`.

---

### 🥈 Project 2: Scan Other People's Projects & Publish Results

**What:** Use CodeTrellis to scan popular open-source projects (FastAPI, Next.js, Rust Servo, Django) and publish the matrices as "AI-ready project profiles."

**Why:** This demonstrates CodeTrellis's value to the world. Developers could download a matrix.prompt for any major OSS project and immediately have full AI awareness without cloning the repo. It becomes a **marketing + credibility play**.

**Effort:** ~2 days. You just run `codetrellis scan /path/to/fastapi --optimal` and curate the output.

**First step:** Pick 5 popular repos across different languages. Scan each. Write a blog post comparing the matrix quality. Share on X/Reddit/HN.

---

### 🥉 Project 3: Multi-Project Matrix Federation

**What:** A "meta-matrix" that aggregates matrices from multiple related projects (e.g., a frontend + backend + shared library monorepo) into a single unified context.

**Why:** Real-world companies have 5–50 repos. The AI needs to understand how they connect — shared types across repos, API contracts between frontend and backend, shared CI/CD pipelines. No one does this today.

**Effort:** ~1 week. Build a `codetrellis federation` command that:

1. Loads `matrix.json` from multiple projects
2. Resolves cross-project type references (using `cross_language_types.py`)
3. Generates a federated `meta-matrix.prompt` with cross-repo dependency graph

**First step:** Create `codetrellis/federation.py` with a `FederatedMatrix` dataclass that merges multiple `matrix.json` files.

---

## Summary: What We Created Today

| File                               | For                | Purpose                                            |
| ---------------------------------- | ------------------ | -------------------------------------------------- |
| `.vscode/mcp.json`                 | **GitHub Copilot** | MCP server registration — Copilot can query matrix |
| `.github/copilot-instructions.md`  | **GitHub Copilot** | Auto-loaded project context for every chat         |
| `.vscode/tasks.json`               | **VS Code**        | One-click Watch, Scan, Verify, Test tasks          |
| `CLAUDE.md`                        | **Claude Code**    | Auto-loaded project memory                         |
| `.cursorrules`                     | **Cursor**         | Auto-loaded project context                        |
| `docs/CLAUDE_DESKTOP_MCP_SETUP.md` | **Claude Desktop** | MCP server setup instructions                      |
| `WORKFLOW.md`                      | **You**            | This file — daily checklist + next steps           |

**You are now wired into every major AI coding tool.** The matrix is your single source of truth, and every AI reads it automatically.
