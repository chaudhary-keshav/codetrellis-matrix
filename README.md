# CodeTrellis — Give AI Full Project Awareness

> Scan your codebase, compress to ~1K tokens, inject into every AI prompt.

[![PyPI](https://img.shields.io/pypi/v/codetrellis)](https://pypi.org/project/codetrellis/)
[![Python](https://img.shields.io/pypi/pyversions/codetrellis)](https://pypi.org/project/codetrellis/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-7264%20passing-brightgreen)]()

**Works with:** GitHub Copilot | Claude | Cursor | Windsurf | any MCP-compatible AI

---

## The Problem

- AI assistants read files one at a time — they never see your full project
- They don't know about existing components, schemas, or patterns
- You explain your project structure repeatedly in every conversation
- AI lacks business domain understanding — doesn't know _why_ code exists

## Quick Start

```bash
pip install codetrellis
codetrellis scan /path/to/project --optimal
codetrellis init . --ai   # sets up Copilot/Claude/Cursor integration
```

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

## Top Features

- **120+ language/framework parsers** — Python, TypeScript, Go, Rust, Java, C#, and more
- **MCP server** for real-time AI context injection (JSON-RPC 2.0)
- **JIT context engine** — delivers only relevant sections for the file you're editing
- **Incremental builds** — only re-extract changed files
- **Best Practices Library** — 4,500+ practices auto-selected for your stack
- **Output tiers** — from ~800 tokens (compact) to full code context (logic)
- **CI/CD mode** — deterministic, parallel builds for pipelines
- **AI integration** — auto-generates Copilot, Claude, Cursor, Windsurf configs

📋 [Full feature list](https://github.com/chaudhary-keshav/codetrellis-matrix/blob/main/docs/FEATURES.md)

## Installation

```bash
pip install codetrellis

# Optional extras
pip install codetrellis[all]     # AST parsing, YAML, color, token counting
pip install codetrellis[ast]     # Tree-sitter AST parsing only
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

## CLI Commands

```bash
# Scanning
codetrellis scan [path]              # Scan project
codetrellis scan [path] --optimal    # Maximum quality (recommended)
codetrellis scan [path] --incremental  # Only changed files
codetrellis scan [path] --ci         # CI/CD mode (deterministic + parallel)
codetrellis scan --remote <url>      # Scan a remote git repo

# AI Integration
codetrellis init . --ai              # Generate Copilot/Claude/Cursor configs
codetrellis init . --update-ai       # Regenerate AI files (no re-scan)
codetrellis mcp --stdio              # Start MCP server
codetrellis context path/to/file.py  # JIT context for a file
codetrellis skills                   # Generate AI-executable skills

# View & Export
codetrellis show                     # Show full matrix
codetrellis prompt                   # Print prompt-ready matrix
codetrellis export --json            # Export as JSON

# Quality & Maintenance
codetrellis verify [path]            # Build quality gate
codetrellis validate [path]          # Validate extraction completeness
codetrellis coverage [path]          # Show extraction coverage
codetrellis watch                    # Auto-sync on file changes
codetrellis clean [path]             # Clean caches
```

## Contributing

See [CONTRIBUTING.md](https://github.com/chaudhary-keshav/codetrellis-matrix/blob/main/CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License — Keshav Chaudhary 2026
