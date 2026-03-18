# CodeTrellis — Product Vision & Roadmap

> From **Context Engine** to **AI Development Partner**
>
> Created: 17 March 2026 | Author: Keshav Chaudhary

---

## Executive Summary

CodeTrellis today is the **most comprehensive AI context injection system** in the market — scanning 19 languages, 100+ frameworks, extracting 2268+ types, and delivering the entire project's knowledge in ~15K tokens. No other tool comes close to this depth.

But context alone isn't enough. As demonstrated by a real production failure (version mismatch breaking CI after a release), **knowing a project** and **following a project's process** are two different things. The AI understood the codebase perfectly but didn't verify quality gates after making changes.

This document lays out the evolution from **Context Engine** → **Workflow Engine** → **AI Development Partner** — a system where no developer and no AI can forget a step.

---

## Table of Contents

1. [What CodeTrellis Is Today](#1-what-codetrellis-is-today)
2. [The Gap: Why Context Isn't Enough](#2-the-gap-why-context-isnt-enough)
3. [Vision: The Three Pillars](#3-vision-the-three-pillars)
4. [Pillar 1: Workflow Engine](#pillar-1-workflow-engine)
5. [Pillar 2: Active Safety Net](#pillar-2-active-safety-net)
6. [Pillar 3: Intelligence Layer](#pillar-3-intelligence-layer)
7. [New Matrix Sections](#4-new-matrix-sections)
8. [AI Integration File Enhancements](#5-ai-integration-file-enhancements)
9. [New CLI Commands](#6-new-cli-commands)
10. [New MCP Tools](#7-new-mcp-tools)
11. [Competitive Landscape & Differentiation](#8-competitive-landscape--differentiation)
12. [Implementation Roadmap](#9-implementation-roadmap)
13. [Success Metrics](#10-success-metrics)

---

## 1. What CodeTrellis Is Today

### Current Architecture (Strengths)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeTrellis v1.0.x                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCAN ──→ EXTRACT ──→ COMPRESS ──→ INJECT                     │
│                                                                 │
│  • 19 languages        • 32 extractors     • ~15K tokens       │
│  • 100+ frameworks     • 108 BPL practices • Prompt-cached     │
│  • 133 parsers         • Build contracts   • MCP server        │
│  • Plugin system       • Skills generator  • JIT per-file      │
│                                                                 │
│  Output: matrix.prompt, matrix.json, copilot-instructions.md,  │
│          CLAUDE.md, .cursorrules, .vscode/mcp.json             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What It Does Exceptionally Well

| Capability              | Depth                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| **Type extraction**     | Every class, interface, model, DTO, enum across 19 languages                               |
| **API surface**         | REST routes, GraphQL schemas, gRPC services, WebSocket events                              |
| **Framework awareness** | 100+ frameworks with dedicated parsers and best practices                                  |
| **Compression**         | Full project in ~15K tokens (from millions of LOC)                                         |
| **Caching**             | SHA-256 incremental, prompt caching optimization (79% cost reduction)                      |
| **Multi-AI support**    | Copilot, Claude, Cursor, Gemini, Windsurf, Aider, Continue                                 |
| **MCP server**          | 7 tools, real-time matrix queries, auto-reload                                             |
| **Best practices**      | 108 YAML practice files, auto-selected by detected stack                                   |
| **Build contracts**     | C1-C6 (input validation, output schema, determinism, error contract, cache, compatibility) |

### What's Missing (The Honest Assessment)

| Gap                                         | Impact                                                       |
| ------------------------------------------- | ------------------------------------------------------------ |
| **No post-change workflow**                 | AI makes changes but never verifies them                     |
| **No quality gate enforcement**             | AI doesn't know what CI checks or how to simulate them       |
| **No release process**                      | Version bumps happen without verification                    |
| **CI pipeline = opaque metadata**           | `job:build\|steps:8` tells AI nothing actionable             |
| **`infrastructure` extracted but unused**   | MatrixContext extracts it, templates never inject it         |
| **`actionable_items` extracted but unused** | Same - extracted into context, never shown to AI             |
| **No change impact analysis**               | AI doesn't know which CI gates a specific change might break |
| **No test coverage awareness**              | AI doesn't know if changed code has tests                    |
| **No PR readiness check**                   | No "is this ready to merge?" verification                    |
| **No onboarding workflow**                  | `codetrellis onboard` exists but is minimal                  |

---

## 2. The Gap: Why Context Isn't Enough

### The Failure Case (Real Incident)

```
Developer asks AI to make a change
  → AI reads matrix, understands the codebase perfectly
  → AI makes the code change correctly
  → AI says "done!"
  → Developer commits, tags, pushes
  → CI FAILS: "Version mismatch: pyproject.toml=1.0.2, __init__.py=unknown"
  → Release is broken
```

### Why It Happened

The matrix told the AI:

```
ci:github-actions|triggers:push|jobs:test,build,publish-test,publish-pypi
```

But it never told the AI:

```
AFTER any change that touches version-sensitive code:
  1. Run: pip install -e .
  2. Verify: python -c "from codetrellis import __version__; print(__version__)"
  3. Check: does pyproject.toml version == __version__?
```

**The gap: CodeTrellis describes the project but doesn't prescribe the process.**

### The Philosophy

> A junior developer reads documentation and MIGHT forget a step.
> A senior developer has internalized the process and RARELY forgets.
> An AI with CodeTrellis should NEVER forget — it has ALL the instructions.
>
> But today, the instructions only say "here's what exists" —
> not "here's what you must DO."

---

## 3. Vision: The Three Pillars

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CodeTrellis v2.0 Vision                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   PILLAR 1              PILLAR 2              PILLAR 3                 │
│   Workflow Engine       Active Safety Net     Intelligence Layer       │
│                                                                         │
│   • Post-change         • Pre-commit hooks    • Impact analysis        │
│     checklists          • Quality gates       • Change risk scoring    │
│   • Release process     • Test coverage       • Auto-fix suggestions   │
│   • CI gate semantics     awareness           • Learning from CI       │
│   • Task lifecycle      • PR readiness          failures               │
│     management          • Dependency audit    • Cross-session memory   │
│                                                                         │
│   "What to DO"          "What NOT to miss"    "What MIGHT go wrong"    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pillar 1: Workflow Engine

### P1.1 — `[QUALITY_GATES]` Section (Auto-Generated from CI)

**What:** Parse CI workflow files (GitHub Actions, GitLab CI, CircleCI, Jenkins, etc.) and extract **actionable gate specifications** — not just job names but what each step validates and how to replicate it locally.

**Example matrix output:**

```
[QUALITY_GATES]
# CI pipeline: .github/workflows/ci.yml
# These gates MUST pass. AI MUST verify locally after any code change.

gate:lint
  command: ruff check codetrellis/
  triggers-on: any .py file change
  ci-job: lint (step 4 of 6)

gate:typecheck
  command: mypy codetrellis/ --ignore-missing-imports
  triggers-on: any .py file change
  ci-job: lint (step 5 of 6)
  severity: advisory (continue-on-error)

gate:test
  command: pytest tests/ -x -q --timeout=120
  triggers-on: any code change
  ci-job: test (matrix: python 3.9, 3.10, 3.11, 3.12)

gate:version-consistency
  command: |
    pip install -e . --quiet
    PYPROJECT_VER=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
    INIT_VER=$(python3 -c "from codetrellis import __version__; print(__version__)")
    test "$PYPROJECT_VER" = "$INIT_VER"
  triggers-on: pyproject.toml change, __init__.py change, release tag
  ci-job: build (step 4 of 8), lint (step 6 of 6)

gate:build
  command: python -m build && twine check dist/*
  triggers-on: release tag
  ci-job: build (steps 5-6 of 8)
```

**Implementation:**

- Enhance `cicd_extractor.py` to parse individual CI steps (not just job names)
- Extract `run:` blocks, map them to local equivalents
- Detect `continue-on-error` vs hard failure
- Connect steps to file-change triggers via glob patterns in CI config

### P1.2 — `[POST_CHANGE_CHECKLIST]` Section

**What:** An imperative, ordered checklist that AI MUST execute after completing any code change. Auto-generated from quality gates + project conventions.

**Example matrix output:**

```
[POST_CHANGE_CHECKLIST]
# AI MUST execute these steps IN ORDER after ANY code change.
# Do NOT declare task complete until ALL steps pass.

1. LINT: ruff check codetrellis/ --fix
2. TEST: pytest tests/ -x -q
3. IF version-sensitive change:
   a. pip install -e . --quiet
   b. Verify: pyproject.toml version == importlib.metadata version
4. IF new public API or feature:
   a. Verify test exists for the new code
   b. Verify docstring/type hints on public functions
5. IF CI workflow file changed:
   a. Validate YAML syntax
   b. Verify all referenced actions exist
```

**Implementation:**

- New extractor: `workflow_extractor.py`
- Input: quality gates + detected test framework + project conventions
- Output: ordered checklist with conditional steps
- Inject into AI integration files as **imperative** instructions

### P1.3 — `[RELEASE_PROCESS]` Section

**What:** Auto-detected release workflow — version management strategy, tagging convention, publish pipeline.

**Example matrix output:**

```
[RELEASE_PROCESS]
# How releases work in this project:

version-source: pyproject.toml (line 7) → version = "X.Y.Z"
version-consumers: codetrellis/__init__.py (via importlib.metadata)
version-strategy: manual bump in pyproject.toml → pip install -e . → verify

release-trigger: git tag v* → .github/workflows/release.yml
release-pipeline:
  1. test (matrix: python 3.9-3.12)
  2. build (version-consistency check → sdist+wheel → twine validate)
  3. publish-test (TestPyPI via trusted publishing)
  4. publish-pypi (PyPI via trusted publishing, tag-only)

pre-release-checklist:
  1. Update version in pyproject.toml
  2. pip install -e . --quiet
  3. Verify: python -c "import codetrellis; print(codetrellis.__version__)"
  4. Update CHANGELOG.md
  5. Commit: "chore: bump version to X.Y.Z"
  6. Tag: git tag vX.Y.Z
  7. Push: git push && git push --tags
```

**Implementation:**

- Enhance `runbook_extractor.py` or create `release_extractor.py`
- Detect: version source files, tagging patterns, publish workflows
- Detect version strategy: semver, calver, auto (semantic-release), manual
- Map the full release → CI → publish chain

### P1.4 — Task Lifecycle Awareness

**What:** AI should understand where the current task fits in the development lifecycle and what comes next.

**Example:**

```
[TASK_LIFECYCLE]
# Task types and their required steps:

bugfix:
  1. Reproduce (understand the bug)
  2. Fix (minimal change)
  3. Test (add regression test)
  4. Verify (run quality gates)
  5. Document (update CHANGELOG if user-facing)

feature:
  1. Understand scope
  2. Implement
  3. Add tests
  4. Update docs (if public API change)
  5. Verify quality gates
  6. Version bump (if warranted)

refactor:
  1. Verify existing tests pass
  2. Refactor
  3. Verify tests still pass
  4. No version bump needed
```

---

## Pillar 2: Active Safety Net

### P2.1 — Change Impact Analysis

**What:** When AI edits a file, automatically determine which quality gates, tests, and downstream consumers are affected.

**How it works (via MCP tool):**

```
MCP Tool: get_change_impact(file_path)

Input:  codetrellis/__init__.py
Output:
  affected-gates: [version-consistency, test, build]
  affected-tests: [tests/test_init.py]
  downstream: [cli.py (imports __version__), mcp_server.py (reports version)]
  risk-level: HIGH (version-sensitive file)
  recommendation: "After editing, run: pip install -e . && pytest tests/ -x -q"
```

**Implementation:**

- Build import/dependency graph from parsed ASTs
- Map files → CI steps via glob/trigger analysis
- Map files → test files via naming convention + import analysis
- Score risk based on: public API surface, version sensitivity, CI triggers

### P2.2 — Test Coverage Awareness

**What:** Extract which files/functions have test coverage and which don't. When AI creates new code, flag if tests are missing.

**Matrix section:**

```
[TEST_COVERAGE]
# Test mapping (source → test):
codetrellis/cli.py → tests/test_cli.py (exists)
codetrellis/scanner.py → tests/test_scanner.py (missing!)
codetrellis/compressor.py → tests/test_compressor.py (missing!)
codetrellis/__init__.py → tests/test_init.py (exists)

coverage-gaps:
  HIGH: scanner.py (27K lines, 0 test files)
  HIGH: compressor.py (30K lines, 0 test files)
  MEDIUM: builder.py (605 lines, 0 test files)
```

**Implementation:**

- New extractor: `test_coverage_extractor.py`
- Scan `tests/` directory, match test files to source files
- Parse test files for function/class coverage
- Optional: integrate with `coverage.py` report if available

### P2.3 — PR Readiness Gate

**What:** A single MCP tool that answers: "Is this set of changes ready to be a PR?"

```
MCP Tool: check_pr_readiness()

Output:
  ✅ Lint: passed
  ✅ Tests: 42 passed, 0 failed
  ✅ Version: consistent (1.0.2)
  ⚠️  CHANGELOG: not updated (version changed)
  ❌ Missing tests: new function `parse_workflow()` in ci_extractor.py has no test

  Verdict: NOT READY (1 blocker, 1 warning)
```

**Implementation:**

- Aggregate results from all applicable quality gates
- Run them locally (lint, test, version check)
- Check for missing test coverage on changed files
- Check for changelog updates if version changed
- Return structured pass/fail with actionable recommendations

### P2.4 — Dependency & Security Audit

**What:** Surface known vulnerabilities, outdated dependencies, and license issues.

```
[DEPENDENCY_AUDIT]
# Auto-detected from requirements.txt, pyproject.toml, package.json, go.mod

outdated:
  watchdog: 3.0.0 → 4.0.2 (major)
  tomli: 2.0.1 → 2.0.2 (patch)

advisories:
  None detected

license-conflicts:
  None detected
```

**Implementation:**

- Parse dependency files (already done in `config_extractor.py`)
- Cross-reference with PyPI/npm/crates.io API for latest versions
- Integrate with GitHub Advisory Database or OSV for vulnerability data
- Generate `[DEPENDENCY_AUDIT]` section

---

## Pillar 3: Intelligence Layer

### P3.1 — Learning from CI Failures

**What:** When a CI build fails, CodeTrellis can ingest the failure log and add it to project knowledge — preventing the same mistake from happening again.

```bash
codetrellis learn-failure --ci-log=build.log

# Adds to matrix:
[KNOWN_PITFALLS]
pitfall:version-mismatch
  cause: "pip install -e ." not run after pyproject.toml version change
  symptom: "Version mismatch: pyproject.toml=X.Y.Z, __init__.py=unknown"
  prevention: Always run "pip install -e ." after editing pyproject.toml
  added: 2026-03-17 (from CI run #67393552740)
```

**Implementation:**

- New CLI command: `codetrellis learn-failure`
- Parse CI log output (GitHub Actions, GitLab CI log formats)
- Extract: failed step, error message, exit code
- Match to known patterns or prompt user for cause/prevention
- Store in `.codetrellis/knowledge/pitfalls.yaml`
- Inject into matrix as `[KNOWN_PITFALLS]` section

### P3.2 — Change Risk Scoring

**What:** Before applying changes, score the risk level based on project knowledge.

```
MCP Tool: assess_risk(changes: [{file, diff}])

Output:
  overall-risk: MEDIUM
  factors:
    - __init__.py modified → version-sensitive (HIGH)
    - cli.py modified → 5 CI steps depend on this (MEDIUM)
    - tests/ not modified → risk of untested changes (HIGH)
    - similar change previously caused CI failure #67393552740 (HIGH)
  recommendation: "Run full test suite. Verify version consistency."
```

### P3.3 — Auto-Fix Suggestions

**What:** When a quality gate fails, suggest the exact fix based on project knowledge.

```
Gate FAILED: version-consistency

Auto-fix suggestion:
  The version in pyproject.toml (1.0.3) doesn't match importlib.metadata (1.0.2).
  This happens because the package was not reinstalled after the version bump.

  Fix: Run these commands:
    pip install -e . --quiet
    python -c "import codetrellis; print(codetrellis.__version__)"

  Root cause: __init__.py uses importlib.metadata.version() which reads
  from the installed package metadata, not from pyproject.toml directly.
```

### P3.4 — Cross-Session Knowledge Persistence

**What:** Store insights from each AI session that can inform future sessions.

```
.codetrellis/knowledge/
  pitfalls.yaml       # Known failure patterns and fixes
  decisions.yaml      # Architectural decisions made and why
  patterns.yaml       # Detected coding patterns and conventions
  workarounds.yaml    # Known workarounds for project-specific issues
```

This knowledge is:

- Auto-extracted from CI failures, code reviews, and AI sessions
- Injected into matrix as `[PROJECT_KNOWLEDGE]` section
- Available via MCP: `get_project_knowledge(topic)`

### P3.5 — Smart Onboarding Flow

**What:** An interactive, guided onboarding experience that goes beyond listing files.

```bash
codetrellis onboard --interactive

Welcome to codetrellis-matrix!

📋 Project: Python Library | Developer Tools
🔧 Stack: Python 3.9+ | pytest | ruff | GitHub Actions
📦 Package: codetrellis (PyPI)

Let me walk you through:

1. Architecture
   - Scanner (133 parsers) → Compressor → Matrix output
   - MCP server for real-time queries
   - Plugin system for extensibility

2. Development Workflow
   - Edit code → Run tests (pytest tests/ -x -q) → Lint (ruff check)
   - Version bump: edit pyproject.toml → pip install -e . → verify

3. Release Process
   - Bump version → Commit → Tag (vX.Y.Z) → Push
   - CI: test → build (version check) → TestPyPI → PyPI

4. Quality Gates
   - Lint: ruff check codetrellis/
   - Type check: mypy codetrellis/ (advisory)
   - Test: pytest tests/ -x -q
   - Version: pyproject.toml == importlib.metadata

5. Known Pitfalls
   - Always pip install -e . after version bumps
   - CI release.yml requires package installed for version check

Ready to start? [Y/n]
```

### P3.6 — Architecture Decision Records (ADR) Extraction

**What:** Parse existing code comments, PRs, and commit messages to build an ADR registry.

```
[ARCHITECTURE_DECISIONS]
adr:001 "Use importlib.metadata for version"
  context: Need single source of truth for version
  decision: pyproject.toml is source, __init__.py reads via importlib.metadata
  consequence: Package must be installed for version to resolve
  files: pyproject.toml, codetrellis/__init__.py

adr:002 "Compress to ~15K tokens"
  context: LLM context windows are limited, cost scales with tokens
  decision: Lossy compression preserving types, APIs, and structure
  consequence: Implementation details are summarized, not included verbatim
```

---

## 4. New Matrix Sections

| Section                    | Purpose                               | Auto-Generated From               |
| -------------------------- | ------------------------------------- | --------------------------------- |
| `[QUALITY_GATES]`          | Actionable CI gate specifications     | CI workflow files (.yml)          |
| `[POST_CHANGE_CHECKLIST]`  | Ordered verification steps            | Quality gates + conventions       |
| `[RELEASE_PROCESS]`        | Version management + publish pipeline | CI workflows + version files      |
| `[TASK_LIFECYCLE]`         | Required steps per task type          | Conventions + CI + test framework |
| `[TEST_COVERAGE]`          | Source → test file mapping + gaps     | tests/ directory analysis         |
| `[KNOWN_PITFALLS]`         | Learned failure patterns              | CI logs + manual input            |
| `[PROJECT_KNOWLEDGE]`      | Cross-session insights                | Knowledge files                   |
| `[DEPENDENCY_AUDIT]`       | Version status + security             | Dependency files + APIs           |
| `[CHANGE_IMPACT_MAP]`      | File → gate → test mapping            | AST imports + CI triggers         |
| `[ARCHITECTURE_DECISIONS]` | ADR registry                          | Code comments + commit history    |

---

## 5. AI Integration File Enhancements

### Current vs. Proposed: copilot-instructions.md

**Currently generated:**

```markdown
## Key Conventions

1. Follow existing patterns
2. Follow error handling
3. Run tests with pytest tests/ -x -q

## Version Bump

(hand-added, not auto-generated)
```

**Proposed auto-generated additions:**

```markdown
## Quality Gates (Auto-Verified by CI)

After ANY code change, verify these gates pass before declaring done:

| Gate    | Command                                 | Trigger               |
| ------- | --------------------------------------- | --------------------- |
| Lint    | `ruff check codetrellis/`               | Any .py change        |
| Test    | `pytest tests/ -x -q`                   | Any code change       |
| Version | `pip install -e . && verify`            | pyproject.toml change |
| Build   | `python -m build && twine check dist/*` | Release               |

## Post-Change Checklist

After completing any task, execute IN ORDER:

1. Run lint: `ruff check codetrellis/`
2. Run tests: `pytest tests/ -x -q`
3. If version-sensitive: verify version consistency
4. If new public API: verify tests exist

## Release Process

1. Edit `pyproject.toml` line 7: `version = "X.Y.Z"`
2. Run: `pip install -e . --quiet`
3. Verify: `python -c "import codetrellis; print(codetrellis.__version__)"`
4. Update CHANGELOG.md
5. Commit → Tag (vX.Y.Z) → Push

## Known Pitfalls

- importlib.metadata requires package to be installed; always `pip install -e .`
- CI release.yml version check fails if package not installed in build step
```

### Current vs. Proposed: AI_INSTRUCTION Header in matrix.prompt

**Currently:**

```
# REFERENCE the RUNBOOK section for how to run, build, test, and deploy.
# FOLLOW the best practices listed in the BEST_PRACTICES section.
```

**Proposed additions:**

```
# AFTER completing any code change, EXECUTE steps in POST_CHANGE_CHECKLIST.
# VERIFY all QUALITY_GATES pass before declaring the task complete.
# CHECK KNOWN_PITFALLS before making changes to version-sensitive files.
# CONSULT CHANGE_IMPACT_MAP to understand which gates your changes affect.
# FOLLOW RELEASE_PROCESS when version bumps or releases are involved.
# DO NOT skip any step in POST_CHANGE_CHECKLIST — treat them as mandatory.
```

### Use Extracted but Currently Unused Fields

Fix the existing gap where `infrastructure` and `actionable_items` are extracted into `MatrixContext` but never injected:

```python
# In init_integrations.py generate_copilot_instructions():
# ADD: infrastructure section (CI/CD, Docker, etc.)
# ADD: actionable_items (TODOs, FIXMEs for AI to prioritize)
```

---

## 6. New CLI Commands

| Command                                  | Purpose                                                       |
| ---------------------------------------- | ------------------------------------------------------------- |
| `codetrellis gates`                      | Show quality gates extracted from CI, with local run commands |
| `codetrellis checklist`                  | Print the post-change checklist for this project              |
| `codetrellis release-check`              | Run all pre-release gates and report pass/fail                |
| `codetrellis learn-failure --log=<file>` | Ingest CI failure log into project knowledge                  |
| `codetrellis impact <file>`              | Show change impact analysis for a file                        |
| `codetrellis test-map`                   | Show source → test file mapping and coverage gaps             |
| `codetrellis audit`                      | Run dependency audit (versions, security, licenses)           |
| `codetrellis knowledge`                  | Show/manage cross-session project knowledge                   |
| `codetrellis pr-ready`                   | Check if current changes are PR-ready                         |

---

## 7. New MCP Tools

| Tool                            | Purpose                                             |
| ------------------------------- | --------------------------------------------------- |
| `get_quality_gates()`           | Return all quality gates with commands              |
| `get_post_change_checklist()`   | Return ordered checklist for the current change     |
| `get_change_impact(file_path)`  | Return impact analysis: affected gates, tests, risk |
| `get_release_process()`         | Return release workflow steps                       |
| `check_pr_readiness()`          | Run gates and return pass/fail report               |
| `get_known_pitfalls(topic?)`    | Return known failure patterns                       |
| `get_test_coverage(file_path?)` | Return test mapping and gaps                        |
| `assess_risk(files)`            | Return risk score for proposed changes              |
| `get_project_knowledge(topic?)` | Return cross-session knowledge                      |

---

## 8. Competitive Landscape & Differentiation

### What Exists Today (March 2026)

| Tool                            | What It Does                                     | Gap                                           |
| ------------------------------- | ------------------------------------------------ | --------------------------------------------- |
| **GitHub Copilot Instructions** | `.github/copilot-instructions.md` — static rules | Manual, no auto-generation from code analysis |
| **Cursor Rules**                | `.cursorrules` — static context                  | Manual, no quality gates                      |
| **Claude Memory**               | `CLAUDE.md` — session memory                     | Manual, per-project only                      |
| **AGENTS.md**                   | Agent modes and instructions                     | Manual, no workflow automation                |
| **Continue.dev**                | IDE plugin with context                          | No project scanning, no matrix                |
| **Aider**                       | CLI coding assistant                             | No persistent project context                 |
| **Sourcegraph Cody**            | Codebase search + chat                           | Search-focused, no workflow                   |
| **Greptile**                    | Codebase understanding API                       | API-only, no local workflow                   |

### CodeTrellis Differentiation

| Dimension           | Others                | CodeTrellis Today                              | CodeTrellis v2.0                 |
| ------------------- | --------------------- | ---------------------------------------------- | -------------------------------- |
| **Context depth**   | Surface-level         | Deep (19 langs, 100+ frameworks, types + APIs) | Same + workflow                  |
| **Auto-generation** | Manual or LLM-guessed | Code-analysis-based                            | + CI analysis + failure learning |
| **Quality gates**   | None                  | Build contracts (internal)                     | Exposed to AI + enforced         |
| **Workflow**        | None                  | None                                           | Full task lifecycle              |
| **Multi-AI**        | Usually one tool      | 6+ AI tools                                    | 6+ with workflow injection       |
| **Learning**        | None                  | None                                           | CI failure ingestion             |
| **MCP**             | None/basic            | 7 tools                                        | 16 tools + workflow              |
| **Persistence**     | None                  | Matrix cache                                   | + cross-session knowledge        |

### The Moat

No other tool combines:

1. **Deep code analysis** (133 parsers, not just file listing)
2. **CI pipeline understanding** (not just "CI exists" but "here's what it checks")
3. **Workflow enforcement** (imperative checklists, not just reference docs)
4. **Failure learning** (ingesting CI logs into project knowledge)
5. **Multi-AI injection** (same context to Copilot, Claude, Cursor, etc.)

**CodeTrellis becomes the project's "senior developer brain" that every AI uses.**

---

## 9. Implementation Roadmap

### Phase 1: Workflow Foundation (v1.1)

**Focus: The features that would have prevented the version mismatch incident.**

| Item                                        | Priority | Effort | Files to Modify                              |
| ------------------------------------------- | -------- | ------ | -------------------------------------------- |
| P1.1: `[QUALITY_GATES]` section             | CRITICAL | Medium | `cicd_extractor.py`, `compressor.py`         |
| P1.2: `[POST_CHANGE_CHECKLIST]` section     | CRITICAL | Medium | New `workflow_extractor.py`, `compressor.py` |
| Inject `infrastructure` into AI templates   | HIGH     | Small  | `init_integrations.py`                       |
| Inject `actionable_items` into AI templates | HIGH     | Small  | `init_integrations.py`                       |
| Add imperative `AI_INSTRUCTION` lines       | HIGH     | Small  | `compressor.py`                              |
| `codetrellis gates` command                 | MEDIUM   | Small  | `cli.py`                                     |
| `codetrellis checklist` command             | MEDIUM   | Small  | `cli.py`                                     |

### Phase 2: Release & Safety (v1.2)

**Focus: Never break a release again.**

| Item                                  | Priority | Effort | Files to Modify                                              |
| ------------------------------------- | -------- | ------ | ------------------------------------------------------------ |
| P1.3: `[RELEASE_PROCESS]` section     | HIGH     | Medium | New `release_extractor.py` or enhance `runbook_extractor.py` |
| P2.2: `[TEST_COVERAGE]` section       | HIGH     | Medium | New `test_coverage_extractor.py`                             |
| P2.3: `check_pr_readiness()` MCP tool | HIGH     | Medium | `mcp_server.py`                                              |
| `codetrellis release-check` command   | MEDIUM   | Medium | `cli.py`                                                     |
| `codetrellis pr-ready` command        | MEDIUM   | Medium | `cli.py`                                                     |
| `codetrellis test-map` command        | LOW      | Small  | `cli.py`                                                     |

### Phase 3: Intelligence (v1.3)

**Focus: The system learns and gets smarter over time.**

| Item                                 | Priority | Effort | Files to Modify                           |
| ------------------------------------ | -------- | ------ | ----------------------------------------- |
| P3.1: `codetrellis learn-failure`    | HIGH     | Large  | New `failure_learner.py`                  |
| P3.4: Cross-session knowledge        | HIGH     | Large  | New `knowledge_manager.py`                |
| P2.1: `get_change_impact()` MCP tool | MEDIUM   | Large  | `mcp_server.py`, new `impact_analyzer.py` |
| P3.2: Change risk scoring            | MEDIUM   | Medium | `impact_analyzer.py`                      |
| P3.5: Interactive onboarding         | LOW      | Medium | `cli.py`, enhance existing `onboard`      |

### Phase 4: Advanced Features (v2.0)

**Focus: Full AI Development Partner.**

| Item                                | Priority | Effort | Files to Modify                             |
| ----------------------------------- | -------- | ------ | ------------------------------------------- |
| P3.3: Auto-fix suggestions          | MEDIUM   | Large  | `mcp_server.py`, knowledge system           |
| P3.6: ADR extraction                | LOW      | Large  | New `adr_extractor.py`                      |
| P2.4: Dependency audit              | LOW      | Medium | Enhance `config_extractor.py`               |
| Path-specific instructions          | LOW      | Medium | `init_integrations.py` (`.instructions.md`) |
| Agent mode (`AGENTS.md`) generation | LOW      | Medium | `init_integrations.py`                      |

---

## 10. Success Metrics

### Quantitative

| Metric                                     | Baseline (v1.0)       | Target (v2.0)            |
| ------------------------------------------ | --------------------- | ------------------------ |
| CI failures after AI-assisted changes      | Unknown (no tracking) | < 5%                     |
| Quality gates verified by AI per session   | 0                     | 100% of applicable gates |
| Seconds to understand a new project        | ~300s (AI explores)   | < 5s (matrix + workflow) |
| Developer interventions to fix AI mistakes | ~30% of sessions      | < 10%                    |
| New developer onboarding time              | Hours                 | Minutes                  |

### Qualitative

- **No more "AI made a change but forgot to verify"** — post-change checklist is mandatory
- **No more broken releases** — release process is auto-documented and enforced
- **No more rediscovering the project** — cross-session knowledge persists
- **No more "works on my machine"** — CI gates are replicable locally
- **Every AI (Copilot, Claude, Cursor) behaves the same** — identical workflow injection

---

## Appendix A: Existing Extension Points

The current codebase already has hooks for most of these features:

| Extension Point       | Location                                       | Ready For                                     |
| --------------------- | ---------------------------------------------- | --------------------------------------------- |
| New matrix sections   | `compressor.py` section renderer               | Quality gates, release process, test coverage |
| New extractors        | `extractors/` directory                        | Workflow, release, test coverage, ADR         |
| New MCP tools         | `mcp_server.py` `list_tools()` + `call_tool()` | All new tools                                 |
| New CLI commands      | `cli.py` argparse subparsers                   | All new commands                              |
| AI template injection | `init_integrations.py` template f-strings      | Infrastructure, actionable items, workflows   |
| AI instruction header | `compressor.py` `[AI_INSTRUCTION]` block       | Imperative workflow lines                     |
| Knowledge storage     | `.codetrellis/` directory                      | Pitfalls, decisions, patterns                 |
| Plugin system         | `plugins/` directory, entry points             | Third-party extractors                        |
| Build contracts       | `build_contract.py` C1-C6                      | New contracts C7+                             |
| BPL practices         | `bpl/practices/*.yaml`                         | Workflow practices                            |

## Appendix B: Token Budget

Current matrix: ~15K tokens. Adding workflow sections:

| New Section               | Est. Tokens | Stability  |
| ------------------------- | ----------- | ---------- |
| `[QUALITY_GATES]`         | ~200-500    | STATIC     |
| `[POST_CHANGE_CHECKLIST]` | ~150-300    | STATIC     |
| `[RELEASE_PROCESS]`       | ~200-400    | STATIC     |
| `[TEST_COVERAGE]`         | ~100-300    | STRUCTURAL |
| `[KNOWN_PITFALLS]`        | ~100-500    | VOLATILE   |
| `[TASK_LIFECYCLE]`        | ~100-200    | STATIC     |

**Total addition: ~850-2200 tokens** (~6-15% overhead)

Since these are mostly STATIC sections, they benefit from prompt caching (placed at the top of matrix, covered by cache prefix). Net cost impact over 10-request session: **< $0.05 incremental**.

---

> _"CodeTrellis doesn't just tell AI what the project is — it tells AI how to work in it."_
