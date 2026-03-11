# CodeTrellis vs. Augment — Competitive Positioning

> Internal positioning document. Last updated: March 2026.

---

## Hero Tagline

**Your AI assistant is only as smart as the context it gets — CodeTrellis makes every prompt complete.**

---

## Positioning Statement

CodeTrellis is an open-source, local-only context layer that scans your entire codebase and compresses it into a deterministic artifact — the matrix — injected into every AI prompt automatically. Unlike full-stack AI platforms that bundle context with their own assistant, CodeTrellis works with the tools you already use — Copilot, Claude, Cursor, or any MCP-capable agent — giving them complete project understanding without cloud dependencies, accounts, or vendor lock-in.

---

## Why CodeTrellis

- **Assistant-agnostic by design.** Compatible with Copilot, Claude, Cursor, and any MCP-capable or text-consuming AI tool. Your context layer shouldn't force you onto a single assistant — CodeTrellis decouples context from completion.

- **Zero data residency risk.** CodeTrellis runs entirely locally with zero network calls — your code never leaves your machine. No accounts, no telemetry, no cloud index. Verified: the codebase contains zero network imports.

- **Deep, multi-language understanding.** 120+ parsers covering 24+ languages and 96+ frameworks extract types, routes, schemas, and implementation logic. A cross-language type graph connects your entire stack. 3,900+ best practices are auto-selected by detected stack.

- **Deterministic, portable artifacts.** The matrix is a build artifact, not ephemeral state. `--deterministic` and `--ci` flags produce bit-identical output. Build contracts (H1–H7) and quality gates (G1–G7) guarantee extraction completeness. Check it into CI, diff it across commits, share it with your team.

- **Compressed efficiency — full project in every prompt.** An entire codebase compressed into ~800–15,000 tokens means no retrieval latency, no RAG misses, no stale embeddings. Every AI interaction starts with complete project context, every time.

---

## Comparison Table

| Dimension                   | CodeTrellis                                                      | Augment                                                                                  |
| --------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **What it is**              | Open-source context layer (CLI + MCP server)                     | Commercial full-stack AI coding platform                                                 |
| **Licensing**               | MIT — free, no vendor lock-in                                    | Paid per-seat SaaS                                                                       |
| **AI assistant**            | None — works _with_ your existing assistant                      | Bundled (completion, chat, multi-file edits, agents)                                     |
| **Assistant compatibility** | Copilot, Claude, Cursor, any MCP or text-consuming tool          | Primarily its own platform; Context Engine MCP serves third-party agents                 |
| **Data residency**          | Fully local — zero network calls, zero telemetry                 | Cloud-based with local indexer; requires account                                         |
| **Context delivery**        | Deterministic matrix artifact injected into every prompt         | Proprietary context engine (details per Augment's website)                               |
| **Language coverage**       | 120+ parsers, 24+ languages, 96+ frameworks                      | According to Augment's website, supports major languages (scope not publicly enumerated) |
| **Best practices**          | 3,900+ auto-selected by stack                                    | Not a stated feature                                                                     |
| **Build integration**       | `--deterministic`, `--ci` flags; build contracts & quality gates | According to Augment's website, integrates into CI via remote agents                     |
| **Enterprise compliance**   | Self-hosted, air-gappable, no data leaves the machine            | According to Augment's website, SOC 2 and ISO/IEC 42001 certified                        |

---

## When to Choose

### Choose CodeTrellis when you want to:

- **Keep your current AI tool** and just make it smarter with better context
- **Eliminate data residency concerns** — regulated industries, air-gapped environments, or teams that cannot send code to third-party clouds
- **Treat context as a build artifact** — deterministic, diffable, version-controlled
- **Avoid per-seat costs** — MIT-licensed, free for teams of any size
- **Support a polyglot codebase** — 24+ languages and 96+ frameworks in a single unified matrix
- **Run in CI** — quality gates and build contracts enforce extraction completeness on every commit

### Augment may be a better fit when you want:

- **A turnkey AI assistant platform** — completion, chat, multi-file edits, code review, and multi-agent orchestration in one product
- **Managed infrastructure** — cloud-hosted with enterprise support, SOC 2, and dedicated account management (according to Augment's website)
- **Slack integration and team collaboration features** built into the AI layer (according to Augment's website)

> CodeTrellis and Augment are not mutually exclusive. Teams using Augment's Context Engine MCP can layer CodeTrellis matrices as an additional context source — getting deterministic, local-first project understanding alongside Augment's proprietary indexing.

---

## Elevator Pitch (30 seconds)

CodeTrellis is an open-source CLI that scans your codebase — all 24+ languages, 96+ frameworks — and compresses it into a single artifact called a matrix. That matrix gets injected into every AI prompt automatically, so Copilot, Claude, or Cursor understands your entire project without you pasting context manually. It runs locally, makes zero network calls, costs nothing, and produces deterministic output you can check into CI. It's not a replacement for your AI assistant — it's the context layer that makes any assistant actually useful on real codebases.

---

## One-Liner (for GitHub / README)

**Open-source context layer that makes any AI coding assistant understand your entire codebase — locally, deterministically, for free.**
