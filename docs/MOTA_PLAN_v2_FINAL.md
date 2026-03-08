# MOTA: Matrix-Orchestrated Tool Agents — Implementation Plan v2.0 (FINAL)

> **Status:** VALIDATED by 6-Agent Review (2 rounds)
> **Date:** 27 February 2026
> **Author:** CodeTrellis Team
> **Internal Name:** MOTA
> **External Name:** CodeTrellis Agents
> **Validation:** See MOTA_AGENT_REVIEW_ROUND1.md and MOTA_AGENT_REVIEW_ROUND2.md

---

## 1. Executive Summary

**CodeTrellis Agents** (internally: MOTA — Matrix-Orchestrated Tool Agents) is an
architecture where the pre-computed CodeTrellis Matrix acts as a **deterministic
orchestrator** for LLM-powered tool agents.

**The 10x Moment (60-second demo):**

```
User: "Add a new /api/orders endpoint with pagination"

CodeTrellis Agents automatically:
1. Detects intent: add-endpoint (deterministic, <10ms)
2. Spawns 🔧 Implementor with ONLY relevant matrix sections
3. Agent sees existing route patterns, types, middleware (from matrix)
4. Creates endpoint following YOUR project's patterns
5. ToolGuard ensures only safe tools are used
6. Auto-verifies: type-check ✅ lint ✅ tests ✅
7. Done in ONE interaction. No back-and-forth.
```

**Why this beats the current approach:**
| | Current | MOTA |
|---|---------|------|
| Tool selection | LLM guesses | Matrix determines |
| Context | Everything dumped | Precise sections per task |
| Verification | None | Automatic (type + lint + test) |
| Trust | LLM decides permissions | ToolGuard enforces |
| Cost | Multiple LLM coordination calls | 1 LLM call + free verification |

---

## 2. Architecture

### 2.1 System Overview

```
User Message
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    MOTA Orchestrator                     │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │   Input    │  │   Intent   │  │   Agent    │       │
│  │ Sanitizer  │→ │ Classifier │→ │  Factory   │       │
│  └────────────┘  └────────────┘  └────────────┘       │
│                                        │               │
│                                        ▼               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Context   │  │   Tool     │  │  Tool      │       │
│  │ Assembler  │← │  Selector  │← │  Guard     │       │
│  └────────────┘  └────────────┘  └────────────┘       │
│                                                         │
│  Powered by: CodeTrellis Matrix (33 sections, local)   │
└──────────────────────┬──────────────────────────────────┘
                       │ AgentSession
                       ▼
              ┌──────────────────┐
              │    LLM Agent     │
              │  (executes within│     ┌──────────────┐
              │   constrained    │────→│  Audit Log   │
              │   frame)         │     └──────────────┘
              └────────┬─────────┘
                       │ output
                       ▼
              ┌──────────────────┐
              │  Verification    │
              │  Engine          │
              │  (deterministic) │
              └────────┬─────────┘
                       │
                ┌──────┴──────┐
                │             │
             ✅ Pass       ❌ Fail
                │             │
                ▼             ▼
            Complete    Feedback Loop
                       (max 5 retries)
```

### 2.2 Core Data Types

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PersonaType(Enum):
    """Phase 1: 3 personas. Phase 4: +3 more."""
    # Phase 1
    IMPLEMENTOR = "implementor"   # Write/edit code
    REVIEWER = "reviewer"         # Review/check code
    PLANNER = "planner"           # Plan multi-step tasks
    # Phase 4
    DEBUGGER = "debugger"         # Debug issues
    TESTER = "tester"             # Write/run tests
    ARCHITECT = "architect"       # Design decisions


class SessionState(Enum):
    INITIALIZING = "initializing"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    COMPLETE = "complete"
    FAILED = "failed"


class FailureAction(Enum):
    RETRY = "retry"
    ESCALATE = "escalate"  # Ask user for help
    ABORT = "abort"


@dataclass
class TokenBudgetConfig:
    """Simple config per model — NOT a separate system."""
    system_prompt: int = 2000
    matrix_context: int = 8000
    conversation: int = 4000
    tool_results: int = 6000


@dataclass
class VerificationStrategy:
    """Composable verification — not a flat list."""
    steps: List[str]             # ["type_check", "lint", "test"]
    required_pass_count: str     # "ALL", "ANY", or specific number
    max_retries: int = 3
    on_failure: FailureAction = FailureAction.RETRY
    languages: List[str] = field(default_factory=lambda: ["python", "typescript"])


@dataclass
class AgentBlueprint:
    """Extension of Skill — the complete agent configuration."""
    # From existing Skill
    name: str
    description: str
    trigger: str
    context_sections: List[str]
    instructions: str
    category: str
    priority: int
    # MOTA additions
    persona: PersonaType
    tools_allowed: List[str]
    tools_denied: List[str]
    verification: VerificationStrategy
    token_budget: TokenBudgetConfig
    max_iterations: int = 5
    slash_command: Optional[str] = None  # e.g., "/implement"


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    was_allowed: bool = True
    timestamp: Optional[datetime] = None


@dataclass
class AgentIteration:
    iteration_number: int
    tool_calls: List[ToolCall]
    llm_response: str
    verification_result: Optional[Dict[str, Any]] = None
    token_usage: int = 0


@dataclass
class AgentSession:
    """Tracks the full lifecycle of an agent's work."""
    blueprint: AgentBlueprint
    state: SessionState = SessionState.INITIALIZING
    iterations: List[AgentIteration] = field(default_factory=list)
    total_tokens: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    audit_events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MOTAAuditEvent:
    """Structured audit logging for every MOTA decision."""
    timestamp: datetime
    event_type: str   # "intent", "blueprint", "tool_call", "tool_denied",
                      # "verification", "retry", "complete", "fail"
    details: Dict[str, Any]
    session_id: str
    user_message_hash: str  # Privacy: hash, not content


@dataclass
class MatrixFreshness:
    """Check if matrix is current before orchestrating."""
    is_fresh: bool
    stale_files: List[str]
    matrix_age_seconds: float
    recommendation: str  # "ok", "incremental", "rescan"


@dataclass
class AgentPipeline:
    """Phase 3: Multi-agent orchestration."""
    stages: List[AgentBlueprint]
    handoff_strategy: str  # "sequential", "parallel", "conditional"
    shared_context: Dict[str, Any] = field(default_factory=dict)
```

### 2.3 Agent Personas

**Phase 1 (3 personas):**

| Persona            | Trigger Patterns                                        | Matrix Sections                                               | Tools Allowed                                   | Tools Denied                        | Verification                        |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------- | ----------------------------------- | ----------------------------------- |
| 🔧 **Implementor** | "add", "create", "implement", "fix", "update", "change" | TYPES, ROUTES, IMPL_LOGIC (filtered), BEST_PRACTICES, RUNBOOK | read, write, terminal (build/test only), search | delete_project, git_push, git_force | type_check + lint + test (ALL pass) |
| 🔍 **Reviewer**    | "review", "check", "audit", PR events                   | BEST_PRACTICES, SECURITY, TYPES, IMPL_LOGIC                   | read, search, comment                           | ALL write tools, terminal           | best_practice checklist             |
| 📋 **Planner**     | "plan", "design", "estimate", "how should"              | OVERVIEW, PROGRESS, ACTIONABLE, BUSINESS_DOMAIN, TYPES        | read, search                                    | ALL write tools, terminal           | feasibility score                   |

**Phase 4 (3 more personas):**

| Persona          | Trigger Patterns                               | Matrix Sections                         |
| ---------------- | ---------------------------------------------- | --------------------------------------- |
| 🐛 **Debugger**  | "debug", "error", stack traces                 | ERROR_HANDLING, IMPL_LOGIC, TYPES       |
| 🧪 **Tester**    | "test", "coverage", "spec"                     | TYPES, IMPL_LOGIC, RUNBOOK              |
| 🏗️ **Architect** | "architecture", "restructure", "design system" | OVERVIEW, TYPES, ROUTES, INFRASTRUCTURE |

### 2.4 Skill → Blueprint Mapping (All 11 Skills)

| Existing Skill        | Persona        | Slash Command |
| --------------------- | -------------- | ------------- |
| fix-issue             | 🔧 Implementor | /fix          |
| add-endpoint          | 🔧 Implementor | /implement    |
| add-model             | 🔧 Implementor | /implement    |
| add-store             | 🔧 Implementor | /implement    |
| add-test              | 🔧 Implementor | /test         |
| add-route             | 🔧 Implementor | /implement    |
| add-hook              | 🔧 Implementor | /implement    |
| update-config         | 🔧 Implementor | /implement    |
| update-infrastructure | 🔧 Implementor | /implement    |
| refactor-code         | 🔍 Reviewer    | /review       |
| add-migration         | 🔧 Implementor | /implement    |

---

## 3. UX Contract

### 3.1 What Users See (Progressive Disclosure)

**Level 1 — Basic (Default):**
MOTA works silently. User just gets better results. No visible change.

**Level 2 — Standard (Opt-in via settings):**

```
┌─────────────────────────────────────────┐
│ 🔧 Implementor Agent                   │
│ Context: TYPES, ROUTES, BEST_PRACTICES  │
│                                         │
│ I'll add the /api/orders endpoint...    │
│                                         │
│ > Reading existing routes...            │
│ > Creating orders.controller.ts...      │
│ > Running verification...               │
│                                         │
│ ✅ Verification Passed:                 │
│   ✅ Type check: 0 errors              │
│   ✅ Lint: 0 warnings                  │
│   ✅ Tests: 5/5 passed                 │
│                                         │
│ [Switch Persona ▾]  [Show Details]      │
└─────────────────────────────────────────┘
```

**Level 3 — Advanced (Developer settings):**
Full orchestration trace: intent confidence, tools considered, token usage,
matrix sections loaded, audit log.

### 3.2 Slash Commands

| Command      | Effect                      |
| ------------ | --------------------------- |
| `/implement` | Force 🔧 Implementor        |
| `/review`    | Force 🔍 Reviewer           |
| `/plan`      | Force 📋 Planner            |
| `/auto`      | Let MOTA decide (default)   |
| `/debug`     | Force 🐛 Debugger (Phase 4) |
| `/test`      | Force 🧪 Tester (Phase 4)   |

### 3.3 Failure UX

When verification fails:

```
│ ⚠️ Verification Failed (attempt 2/5):   │
│   ✅ Type check: 0 errors               │
│   ❌ Lint: 2 warnings                   │
│   ✅ Tests: 5/5 passed                  │
│                                          │
│ Fixing lint issues...                    │
```

When max retries exceeded:

```
│ ❌ Could not fully verify after 5 attempts │
│   Last issue: lint warning on line 42      │
│                                            │
│ [Accept Anyway] [Show Issues] [Retry]      │
```

---

## 4. Security & Trust

### 4.1 ToolGuard (Phase 1 Core Deliverable)

```python
class ToolGuard:
    """Runtime enforcement of tool permissions. NOT prompt-only."""

    def __init__(self, blueprint: AgentBlueprint, audit_log: AuditLog):
        self.allowed = set(blueprint.tools_allowed)
        self.denied = set(blueprint.tools_denied)
        self.audit = audit_log

    def can_execute(self, tool_name: str, session: AgentSession) -> bool:
        # Explicit deny list takes priority
        if tool_name in self.denied:
            self.audit.log("tool_denied", {
                "tool": tool_name, "reason": "in_deny_list",
                "persona": session.blueprint.persona.value
            })
            return False

        # If allow list exists, tool must be in it
        if self.allowed and tool_name not in self.allowed:
            self.audit.log("tool_denied", {
                "tool": tool_name, "reason": "not_in_allow_list",
                "persona": session.blueprint.persona.value
            })
            return False

        return True
```

### 4.2 Input Sanitization (Before Intent Classification)

```python
SUSPICIOUS_PATTERNS = [
    r"(?i)ignore\s+(previous|above|all)\s+(instructions?|prompts?)",
    r"(?i)you\s+are\s+(now|actually)\s+",
    r"(?i)system\s*:\s*",
    r"(?i)override\s+(persona|mode|agent)",
]

def sanitize_input(message: str) -> tuple[str, List[str]]:
    """Remove injection attempts. Return cleaned message + warnings."""
    warnings = []
    cleaned = message
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, cleaned):
            warnings.append(f"Suspicious pattern removed: {pattern}")
            cleaned = re.sub(pattern, "[FILTERED]", cleaned)
    return cleaned, warnings
```

### 4.3 Audit Logging

Every MOTA decision is logged with structured events:

```python
# Example audit trail for a single task:
[
  {"event": "input_sanitized", "warnings": [], "timestamp": "..."},
  {"event": "intent_classified", "intent": "add-endpoint", "confidence": 0.92},
  {"event": "blueprint_selected", "persona": "implementor", "tools": 8},
  {"event": "matrix_freshness", "is_fresh": true, "age_seconds": 120},
  {"event": "context_assembled", "sections": 5, "tokens": 6200},
  {"event": "tool_call", "tool": "read_file", "allowed": true},
  {"event": "tool_call", "tool": "edit_file", "allowed": true},
  {"event": "tool_denied", "tool": "git_push", "reason": "in_deny_list"},
  {"event": "verification_started", "strategy": "type_check+lint+test"},
  {"event": "verification_passed", "results": {"type": "ok", "lint": "ok", "test": "5/5"}},
  {"event": "session_complete", "iterations": 1, "total_tokens": 12400},
]
```

---

## 5. Implementation Phases

### Phase 1: Core (3 weeks)

**Goal:** Intent → Blueprint → ToolGuard → Session tracking

| #   | Task              | Description                            | File                             |
| --- | ----------------- | -------------------------------------- | -------------------------------- |
| 1.1 | Core types        | All dataclasses from Section 2.2       | `codetrellis/mota/types.py`      |
| 1.2 | Intent Classifier | Regex + keyword → intent (no LLM)      | `codetrellis/mota/intent.py`     |
| 1.3 | Agent Factory     | Intent + Matrix → AgentBlueprint       | `codetrellis/mota/factory.py`    |
| 1.4 | Blueprints        | Convert 11 skills → 11 AgentBlueprints | `codetrellis/mota/blueprints.py` |
| 1.5 | ToolGuard         | Runtime tool permission enforcement    | `codetrellis/mota/guard.py`      |
| 1.6 | Audit Logger      | Structured event logging               | `codetrellis/mota/audit.py`      |
| 1.7 | Input Sanitizer   | Pre-classification input cleaning      | `codetrellis/mota/sanitize.py`   |
| 1.8 | Session Manager   | AgentSession lifecycle                 | `codetrellis/mota/session.py`    |
| 1.9 | Unit tests        | Full coverage of Phase 1               | `tests/test_mota/test_phase1.py` |

**Deliverable:** Given a user message, deterministically produce an AgentBlueprint
with enforced tool permissions and audit logging.

**Exit Criteria:**

- [ ] 200 labeled test messages → >90% intent accuracy
- [ ] ToolGuard blocks all denied tools in tests
- [ ] Audit log captures all decision points

### Phase 2: Intelligence (4 weeks)

**Goal:** Smart context + deterministic verification

| #   | Task                | Description                               | File                                |
| --- | ------------------- | ----------------------------------------- | ----------------------------------- |
| 2.1 | Context Assembler   | Blueprint sections + JIT + conversation   | `codetrellis/mota/context.py`       |
| 2.2 | IMPL_LOGIC filter   | Subset 4053 snippets → ~20 relevant       | `codetrellis/mota/logic_filter.py`  |
| 2.3 | Matrix Freshness    | Check matrix age before orchestrating     | `codetrellis/mota/freshness.py`     |
| 2.4 | Prompt Generator    | Persona + context + tools → system prompt | `codetrellis/mota/prompt.py`        |
| 2.5 | Verification Engine | Type-check + lint + test (Python + TS)    | `codetrellis/mota/verify.py`        |
| 2.6 | Verification Parser | Parse tool output into structured results | `codetrellis/mota/verify_parser.py` |
| 2.7 | Feedback Loop       | Failure → add error context → retry       | `codetrellis/mota/feedback.py`      |
| 2.8 | Integration tests   | End-to-end: message → blueprint → verify  | `tests/test_mota/test_phase2.py`    |

**Deliverable:** Complete single-agent flow: message → smart context → LLM →
verification → pass/retry.

**Exit Criteria:**

- [ ] Context relevance >80% (human evaluation on 50 samples)
- [ ] Verification catches >70% of introduced bugs
- [ ] Token usage 30% less than "dump everything" baseline

### Phase 3: Platform (3 weeks)

**Goal:** MCP integration + Extension integration + multi-agent

| #   | Task                     | Description                       | File                           |
| --- | ------------------------ | --------------------------------- | ------------------------------ |
| 3.1 | MCP `orchestrate` tool   | User message → full MOTA flow     | `codetrellis/mcp_server.py`    |
| 3.2 | MCP `get_blueprint` tool | Show what MOTA would do           | `codetrellis/mcp_server.py`    |
| 3.3 | MCP `verify_output` tool | Run verification independently    | `codetrellis/mcp_server.py`    |
| 3.4 | Agent Pipeline           | Multi-agent sequential workflows  | `codetrellis/mota/pipeline.py` |
| 3.5 | Extension integration    | Wire MOTA into chat handler       | Extension `src/mota/`          |
| 3.6 | Chat UI: persona badge   | Show 🔧/🔍/📋 in chat             | Extension webview              |
| 3.7 | Chat UI: verification    | Show ✅/❌ after each task        | Extension webview              |
| 3.8 | Slash commands           | /implement, /review, /plan, /auto | Extension chat                 |
| 3.9 | E2E tests                | Full flow through extension       | `tests/test_mota/test_e2e.py`  |

**Deliverable:** Any MCP client + CodeTrellis Chat uses MOTA. Multi-agent possible.

**Exit Criteria:**

- [ ] MCP tools work in Claude Desktop, Cursor, Cline
- [ ] Slash commands functional in extension
- [ ] Pipeline handles Planner → Implementor → Reviewer sequence

### Phase 4: Scale (2 weeks)

**Goal:** More personas + more languages + analytics

| #   | Task                             | Description                                    |
| --- | -------------------------------- | ---------------------------------------------- |
| 4.1 | Add Debugger persona             | Stack trace analysis + reproduction test       |
| 4.2 | Add Tester persona               | Test generation + coverage analysis            |
| 4.3 | Add Architect persona            | Design document generation                     |
| 4.4 | Verification: Go, Rust, Java, C# | Language-specific verifiers                    |
| 4.5 | Analytics dashboard              | Usage metrics, success rates, token savings    |
| 4.6 | Performance optimization         | Cache blueprint selections, batch matrix reads |

---

## 6. File Structure

```
codetrellis/mota/
├── __init__.py           # Public API
├── types.py              # All dataclasses (AgentBlueprint, Session, etc.)
├── intent.py             # Intent classification (regex + keywords)
├── factory.py            # Intent + Matrix → AgentBlueprint
├── blueprints.py         # 11 pre-defined AgentBlueprints from skills
├── guard.py              # ToolGuard — runtime permission enforcement
├── audit.py              # Structured audit event logging
├── sanitize.py           # Input sanitization before classification
├── session.py            # AgentSession lifecycle management
├── context.py            # Context assembly (JIT + Blueprint + conversation)
├── logic_filter.py       # IMPLEMENTATION_LOGIC subsetting
├── freshness.py          # Matrix staleness detection
├── prompt.py             # System prompt generation
├── verify.py             # Verification engine (type-check, lint, test)
├── verify_parser.py      # Parse verification tool output
├── feedback.py           # Failure → retry with error context
├── pipeline.py           # Multi-agent sequential workflows (Phase 3)
└── mcp.py                # MCP tool registrations for MOTA

tests/test_mota/
├── __init__.py
├── test_phase1.py        # Intent, factory, guard, audit tests
├── test_phase2.py        # Context, verification, feedback tests
├── test_e2e.py           # Full pipeline tests
├── fixtures/
│   ├── test_messages.json  # 200 labeled messages for intent testing
│   └── test_matrices/     # Sample matrices for testing
```

---

## 7. Success Metrics (Outcome-Based)

| Metric                         | Target     | Measurement                        |
| ------------------------------ | ---------- | ---------------------------------- |
| **First-attempt success rate** | >60%       | Tasks completed without retry      |
| **Time to complete task**      | 30% faster | vs baseline (no MOTA)              |
| **Token cost per task**        | 40% less   | Precise context vs dump-everything |
| **Verification catch rate**    | >70%       | Bugs caught by auto-verify         |
| **Intent accuracy**            | >90%       | 200 labeled test messages          |
| **Tool selection precision**   | >85%       | Correct tools vs human baseline    |
| **User satisfaction**          | >4/5 stars | In-extension feedback              |

---

## 8. Risks & Mitigations (Validated by Security Agent)

| Risk                         | Impact                   | Mitigation                                      | Owner   |
| ---------------------------- | ------------------------ | ----------------------------------------------- | ------- |
| Intent misclassification     | Wrong agent              | Fallback to Implementor; slash command override | Phase 1 |
| Prompt injection             | Malicious tool execution | Input sanitizer + ToolGuard                     | Phase 1 |
| Matrix stale                 | Wrong context            | Freshness check + staleness warning             | Phase 2 |
| Tool bypass                  | Security breach          | ToolGuard middleware (not just prompt)          | Phase 1 |
| Verification false positives | Wasted retries           | Configurable strictness; "Accept Anyway" UX     | Phase 2 |
| No audit trail               | Can't debug issues       | Structured audit logging from day 1             | Phase 1 |
| Agent runaway loop           | Token burn               | Max 5 iterations + exponential backoff          | Phase 2 |
| IMPL_LOGIC too large         | Context overflow         | Filter to ~20 relevant snippets                 | Phase 2 |

---

## 9. Timeline

| Phase                 | Duration | Cumulative | Key Deliverable                   |
| --------------------- | -------- | ---------- | --------------------------------- |
| Phase 1: Core         | 3 weeks  | 3 weeks    | Intent → Blueprint → ToolGuard    |
| Phase 2: Intelligence | 4 weeks  | 7 weeks    | Context + Verification + Feedback |
| Phase 3: Platform     | 3 weeks  | 10 weeks   | MCP + Extension + Pipeline        |
| Phase 4: Scale        | 2 weeks  | 12 weeks   | +3 personas + analytics           |

**Total: 12 weeks**

---

## 10. Dependencies (Existing — No New External Deps)

| Dependency                           | Status    | Used By                 |
| ------------------------------------ | --------- | ----------------------- |
| CodeTrellis Matrix (33 sections)     | ✅ Exists | All phases              |
| MCP Server (mcp_server.py)           | ✅ Exists | Phase 3                 |
| JIT Context (jit_context.py)         | ✅ Exists | Phase 2                 |
| Skills System (11 skills)            | ✅ Exists | Phase 1                 |
| Cache Optimizer (cache_optimizer.py) | ✅ Exists | Phase 2 (token budgets) |
| VS Code Extension (52 tools)         | ✅ Exists | Phase 3                 |

**Note (from Skeptic):** Verification across languages requires language-specific
tools installed in the user's environment (mypy, ruff, tsc, etc.). Phase 2 starts
with Python + TypeScript only. Phase 4 adds Go, Rust, Java, C#.

---

## 11. Validated Agent Consensus

This plan was validated by 6 agent personas across 2 rounds of review:

| Agent             | Final Verdict                                                                |
| ----------------- | ---------------------------------------------------------------------------- |
| 🔴 Skeptic        | ✅ PASS — "12 weeks is realistic. 4 phases is right. Start with 3 personas." |
| 🟢 Architect      | ✅ PASS — "AgentSession + VerificationStrategy + Pipeline types included."   |
| 🔵 User Advocate  | ✅ PASS — "UX contract defined. Slash commands. Progressive disclosure."     |
| 🟡 Strategist     | ✅ PASS — "10x moment defined. Outcome metrics. Platform play via MCP."      |
| 🟣 Matrix Expert  | ✅ PASS — "Extends existing systems. IMPL_LOGIC filtering added."            |
| 🟠 Security Agent | ✅ PASS — "ToolGuard Phase 1. Audit logging. Input sanitization."            |

**Unanimous: 6/6 agents approve this plan.**

---

## 12. Session-by-Session Implementation Guide

> **Approach:** Each "session" = one AI chat session (Copilot/Claude/Cursor).
> Sessions are designed to be **self-contained** — each one produces working,
> tested code that you can commit before starting the next.
>
> **Why sessions?** AI assistants work best when given a focused, bounded task
> with clear inputs and outputs. Trying to build everything in one session leads
> to context overflow and lost quality. Each session below is scoped to fit
> within a single AI context window (~100K tokens).
>
> **How to use:** Copy the "What to Ask" prompt into your AI chat. The AI will
> have enough context from the codebase + the prompt to complete the session.
> Review the output, run the exit check, commit, and move to the next session.

### Legend

| Icon | Meaning                                               |
| ---- | ----------------------------------------------------- |
| 🤖   | **AI-heavy** — AI writes most of the code, you review |
| 🤝   | **Collaborative** — You guide, AI implements          |
| 👤   | **Human-heavy** — You design/decide, AI assists       |
| ⚡   | **Quick session** — Under 30 minutes                  |
| 🔨   | **Build session** — 30-60 minutes                     |
| 🏗️   | **Deep session** — 60-90 minutes                      |

---

### PHASE 1: CORE (Sessions 1-8) — Week 1-3

---

#### Session 1 ⚡🤖 — Core Types & Package Setup

**Duration:** ~20 min | **Depends on:** Nothing (start here)

**What you build:**

- `codetrellis/mota/__init__.py` — Public API exports
- `codetrellis/mota/types.py` — All dataclasses from Section 2.2

**What to ask the AI:**

> "Create the `codetrellis/mota/` package. Start with `__init__.py` and `types.py`.
> The types are defined in the MOTA plan Section 2.2. Include: PersonaType,
> SessionState, FailureAction, TokenBudgetConfig, VerificationStrategy,
> AgentBlueprint, ToolCall, AgentIteration, AgentSession, MOTAAuditEvent,
> MatrixFreshness, AgentPipeline. Follow existing project conventions.
> Add full docstrings. Add `__all__` exports in `__init__.py`."

**Exit check:**

```bash
python -c "from codetrellis.mota.types import AgentBlueprint, AgentSession, PersonaType; print('✅ Types OK')"
pytest tests/test_mota/test_types.py -x -q  # AI should create this too
```

**Commit:** `feat(mota): add core types and package structure`

---

#### Session 2 ⚡🤖 — Input Sanitizer

**Duration:** ~20 min | **Depends on:** Session 1

**What you build:**

- `codetrellis/mota/sanitize.py` — Input sanitization (Section 4.2)
- `tests/test_mota/test_sanitize.py` — Tests for sanitization

**What to ask the AI:**

> "Create `codetrellis/mota/sanitize.py` with the `sanitize_input()` function.
> It should detect and filter prompt injection patterns (ignore previous
> instructions, override persona, system: prefix, etc.). Return cleaned message
>
> - list of warnings. Include at least 10 suspicious patterns. Also create
>   comprehensive tests in `tests/test_mota/test_sanitize.py` — test clean
>   messages pass through unchanged, test each injection pattern is caught,
>   test edge cases (empty string, unicode, very long input)."

**Exit check:**

```bash
pytest tests/test_mota/test_sanitize.py -x -q  # All pass
```

**Commit:** `feat(mota): add input sanitizer with injection detection`

---

#### Session 3 🔨🤖 — Audit Logger

**Duration:** ~30 min | **Depends on:** Session 1

**What you build:**

- `codetrellis/mota/audit.py` — Structured audit event logging (Section 4.3)
- `tests/test_mota/test_audit.py`

**What to ask the AI:**

> "Create `codetrellis/mota/audit.py` with an `AuditLog` class that:
>
> 1. Accepts MOTAAuditEvent from types.py
> 2. Stores events in-memory with optional file persistence
> 3. Has `log(event_type, details, session_id)` method
> 4. Has `get_trail(session_id)` to retrieve full audit trail
> 5. Hashes user messages for privacy (SHA-256, first 12 chars)
> 6. Supports JSON serialization for export
>    Create tests covering: event creation, trail retrieval, privacy hashing,
>    serialization, multiple sessions."

**Exit check:**

```bash
pytest tests/test_mota/test_audit.py -x -q
```

**Commit:** `feat(mota): add structured audit logging`

---

#### Session 4 🔨🤖 — Intent Classifier

**Duration:** ~40 min | **Depends on:** Session 1

**What you build:**

- `codetrellis/mota/intent.py` — Regex + keyword intent classification
- `tests/test_mota/test_intent.py`
- `tests/test_mota/fixtures/test_messages.json` — Labeled test messages

**What to ask the AI:**

> "Create `codetrellis/mota/intent.py` with an `IntentClassifier` class.
> Requirements:
>
> 1. Pure regex + keyword matching (NO LLM calls)
> 2. Map user messages to intents: add-endpoint, add-model, add-store,
>    add-test, add-route, add-hook, update-config, update-infrastructure,
>    fix-issue, refactor-code, add-migration, review, plan, debug, test-gen
> 3. Return intent name + confidence score (0.0-1.0)
> 4. Fallback to 'implementor' for ambiguous messages
> 5. Support slash command override (/implement, /review, /plan, /auto)
>
> Also create `tests/test_mota/fixtures/test_messages.json` with 200 labeled
> test messages (diverse phrasing). Create tests asserting >90% accuracy
> on these messages. Reference persona trigger patterns from the plan."

**Exit check:**

```bash
pytest tests/test_mota/test_intent.py -x -q  # >90% accuracy on 200 messages
```

**Commit:** `feat(mota): add intent classifier with 200 labeled test messages`

---

#### Session 5 🔨🤖 — Blueprints (Skill → AgentBlueprint)

**Duration:** ~30 min | **Depends on:** Sessions 1, 4

**What you build:**

- `codetrellis/mota/blueprints.py` — 11 pre-defined AgentBlueprints
- `tests/test_mota/test_blueprints.py`

**What to ask the AI:**

> "Create `codetrellis/mota/blueprints.py` that converts the existing 11
> CodeTrellis skills into AgentBlueprints. Use the mapping from Section 2.4
> of the MOTA plan. Each blueprint must define:
>
> - persona (Implementor/Reviewer/Planner)
> - tools_allowed / tools_denied
> - verification strategy
> - token budget
> - slash command mapping
> - context_sections (which matrix sections to load)
>
> Include a `get_blueprint(intent_name: str) -> AgentBlueprint` function
> and a `list_blueprints() -> List[AgentBlueprint]` function.
> Also create `get_default_blueprint() -> AgentBlueprint` for fallback.
> Create tests validating every blueprint has valid persona, non-empty tools,
> and valid verification strategy."

**Exit check:**

```bash
pytest tests/test_mota/test_blueprints.py -x -q
python -c "from codetrellis.mota.blueprints import list_blueprints; print(f'✅ {len(list_blueprints())} blueprints loaded')"
```

**Commit:** `feat(mota): add 11 skill-based agent blueprints`

---

#### Session 6 🔨🤖 — ToolGuard

**Duration:** ~30 min | **Depends on:** Sessions 1, 3

**What you build:**

- `codetrellis/mota/guard.py` — Runtime tool permission enforcement (Section 4.1)
- `tests/test_mota/test_guard.py`

**What to ask the AI:**

> "Create `codetrellis/mota/guard.py` with a `ToolGuard` class.
> Requirements (from MOTA plan Section 4.1):
>
> 1. Takes an AgentBlueprint + AuditLog in constructor
> 2. `can_execute(tool_name, session) -> bool` — enforces allow/deny lists
> 3. Deny list takes priority over allow list
> 4. Every decision (allow/deny) is logged to AuditLog
> 5. `get_denied_attempts(session_id) -> List[ToolCall]` for reporting
> 6. Thread-safe (use threading.Lock)
>
> Create comprehensive tests: test deny list blocks, test allow list enforces,
> test deny overrides allow, test audit logging happens, test each persona's
> tool permissions from the plan (Implementor, Reviewer, Planner)."

**Exit check:**

```bash
pytest tests/test_mota/test_guard.py -x -q
```

**Commit:** `feat(mota): add ToolGuard runtime permission enforcement`

---

#### Session 7 🔨🤝 — Agent Factory

**Duration:** ~40 min | **Depends on:** Sessions 1, 2, 3, 4, 5, 6

**What you build:**

- `codetrellis/mota/factory.py` — Intent + Matrix → AgentBlueprint
- `tests/test_mota/test_factory.py`

**What to ask the AI:**

> "Create `codetrellis/mota/factory.py` with an `AgentFactory` class.
> This is the main orchestrator that ties everything together:
>
> 1. Takes a user message
> 2. Sanitizes input (using sanitize.py)
> 3. Classifies intent (using intent.py)
> 4. Selects blueprint (using blueprints.py)
> 5. Creates ToolGuard (using guard.py)
> 6. Logs all decisions to AuditLog (using audit.py)
> 7. Returns a fully configured AgentSession ready for execution
>
> Method: `create_session(user_message: str, matrix: Optional[dict] = None) -> AgentSession`
>
> Create integration tests that test the full pipeline: message → session.
> Test with various message types, slash command overrides, injection attempts."

**Exit check:**

```bash
pytest tests/test_mota/test_factory.py -x -q
```

**Commit:** `feat(mota): add agent factory — full Phase 1 pipeline`

---

#### Session 8 🔨🤝 — Session Manager + Phase 1 Integration

**Duration:** ~45 min | **Depends on:** Session 7

**What you build:**

- `codetrellis/mota/session.py` — AgentSession lifecycle management
- `tests/test_mota/test_session.py`
- `tests/test_mota/test_phase1_integration.py` — Full Phase 1 integration tests

**What to ask the AI:**

> "Create `codetrellis/mota/session.py` with a `SessionManager` class.
> Requirements:
>
> 1. Manage AgentSession state transitions (INITIALIZING → EXECUTING →
>    VERIFYING → COMPLETE/FAILED)
> 2. Track iterations (add_iteration, get_current_iteration)
> 3. Enforce max_iterations from blueprint
> 4. Calculate total token usage
> 5. Timestamps for started_at / completed_at
> 6. `to_dict()` for JSON serialization of full session
>
> Then create `tests/test_mota/test_phase1_integration.py` — end-to-end tests
> that: take a user message → AgentFactory creates session → SessionManager
> tracks state → ToolGuard enforces permissions → AuditLog captures everything.
> Test at least 10 different scenarios including edge cases."

**Exit check:**

```bash
pytest tests/test_mota/ -x -q  # ALL Phase 1 tests pass
python -c "
from codetrellis.mota.factory import AgentFactory
factory = AgentFactory()
session = factory.create_session('Add a new /api/users endpoint')
print(f'✅ Phase 1 complete: {session.blueprint.persona.value} agent, {len(session.blueprint.tools_allowed)} tools allowed')
"
```

**Commit:** `feat(mota): complete Phase 1 — intent → blueprint → guard → session`

---

### PHASE 2: INTELLIGENCE (Sessions 9-16) — Week 4-7

---

#### Session 9 🏗️🤝 — Context Assembler

**Duration:** ~60 min | **Depends on:** Phase 1, existing `jit_context.py`

**What you build:**

- `codetrellis/mota/context.py` — Blueprint sections + JIT + conversation context

**What to ask the AI:**

> "Create `codetrellis/mota/context.py` with a `ContextAssembler` class.
> It should:
>
> 1. Read matrix sections specified in the AgentBlueprint.context_sections
> 2. Use existing JIT context system (jit_context.py) for file-specific context
> 3. Merge blueprint context + JIT context + conversation history
> 4. Respect TokenBudgetConfig limits — truncate intelligently if over budget
> 5. Return a structured ContextResult with sections loaded, token counts,
>    and whether any truncation happened
>
> Study the existing `codetrellis/jit_context.py` to understand JITContextResult
> and EXTENSION_TO_SECTIONS mapping. Reuse existing infrastructure, don't
> duplicate. Create tests with mock matrix data."

**Exit check:**

```bash
pytest tests/test_mota/test_context.py -x -q
```

**Commit:** `feat(mota): add context assembler with JIT integration`

---

#### Session 10 🏗️🤝 — IMPL_LOGIC Filter

**Duration:** ~60 min | **Depends on:** Session 9

**What you build:**

- `codetrellis/mota/logic_filter.py` — Subset 4053 snippets → ~20 relevant

**What to ask the AI:**

> "Create `codetrellis/mota/logic_filter.py` with a `LogicFilter` class.
> The IMPLEMENTATION_LOGIC section contains 4053 code snippets. This filter
> must reduce them to ~20 most relevant for the current task.
> Filtering strategies:
>
> 1. File path relevance (same directory, same module)
> 2. Function/class name matching against intent keywords
> 3. Import/dependency overlap with target files
> 4. Priority by complexity tags ([complex] > [simple])
> 5. Configurable max_snippets (default 20)
>
> Study the existing matrix IMPLEMENTATION_LOGIC section format.
> Create tests with sample IMPL_LOGIC data."

**Exit check:**

```bash
pytest tests/test_mota/test_logic_filter.py -x -q
```

**Commit:** `feat(mota): add IMPL_LOGIC filtering (4053 → ~20 snippets)`

---

#### Session 11 ⚡🤖 — Matrix Freshness Check

**Duration:** ~20 min | **Depends on:** Session 1

**What you build:**

- `codetrellis/mota/freshness.py` — Matrix staleness detection

**What to ask the AI:**

> "Create `codetrellis/mota/freshness.py` with a `check_freshness()` function.
> It should:
>
> 1. Check matrix file modification time vs source files
> 2. Return MatrixFreshness (from types.py) with is_fresh, stale_files,
>    age_seconds, recommendation ('ok', 'incremental', 'rescan')
> 3. Threshold: <5 min = ok, 5-30 min = incremental, >30 min = rescan
> 4. Also check if specific files mentioned in user message have changed
>    since last scan
>
> Study existing `codetrellis/cache.py` and `codetrellis/cache_optimizer.py`
> for how the cache/matrix files are stored. Create tests."

**Exit check:**

```bash
pytest tests/test_mota/test_freshness.py -x -q
```

**Commit:** `feat(mota): add matrix freshness detection`

---

#### Session 12 🔨🤝 — Prompt Generator

**Duration:** ~45 min | **Depends on:** Sessions 9, 10

**What you build:**

- `codetrellis/mota/prompt.py` — Persona + context + tools → system prompt

**What to ask the AI:**

> "Create `codetrellis/mota/prompt.py` with a `PromptGenerator` class.
> It should generate a system prompt for the LLM agent that includes:
>
> 1. Persona instructions (from AgentBlueprint — what the agent IS)
> 2. Context from ContextAssembler (relevant code, types, patterns)
> 3. Tool list (only allowed tools from ToolGuard)
> 4. Verification expectations (what checks will run after)
> 5. Output format instructions (structured for verification)
> 6. Constraint reminders (don't use denied tools, follow patterns)
>
> The prompt must fit within TokenBudgetConfig.system_prompt limit.
> Create tests that verify prompt stays within token budget, includes
> persona instructions, and lists only allowed tools."

**Exit check:**

```bash
pytest tests/test_mota/test_prompt.py -x -q
```

**Commit:** `feat(mota): add persona-aware prompt generator`

---

#### Session 13 🏗️🤝 — Verification Engine

**Duration:** ~75 min | **Depends on:** Session 1

**What you build:**

- `codetrellis/mota/verify.py` — Type-check + lint + test (Python + TS)
- `codetrellis/mota/verify_parser.py` — Parse verification tool output

**What to ask the AI:**

> "Create `codetrellis/mota/verify.py` with a `VerificationEngine` class.
> It runs deterministic checks on agent output:
>
> 1. Python: mypy (type check) + ruff (lint) + pytest (tests)
> 2. TypeScript: tsc (type check) + eslint (lint) + vitest/jest (tests)
> 3. Execute each step as subprocess, capture output
> 4. Use VerificationStrategy from blueprint to determine which steps
>    and how many must pass (ALL, ANY, or N)
> 5. Return structured VerificationResult with per-step pass/fail + details
>
> Also create `codetrellis/mota/verify_parser.py` that parses raw output
> from mypy, ruff, tsc, eslint, pytest, vitest into structured results
> (errors count, warnings count, test pass/fail counts).
>
> Handle tool-not-installed gracefully (skip with warning, don't fail).
> Create tests with mock subprocess outputs."

**Exit check:**

```bash
pytest tests/test_mota/test_verify.py tests/test_mota/test_verify_parser.py -x -q
```

**Commit:** `feat(mota): add verification engine (Python + TypeScript)`

---

#### Session 14 🔨🤖 — Feedback Loop

**Duration:** ~30 min | **Depends on:** Session 13

**What you build:**

- `codetrellis/mota/feedback.py` — Failure → add error context → retry

**What to ask the AI:**

> "Create `codetrellis/mota/feedback.py` with a `FeedbackLoop` class.
> When verification fails:
>
> 1. Parse the verification errors
> 2. Create a focused error context (specific lines, specific errors)
> 3. Generate a retry prompt: 'Verification failed: [errors]. Fix these
>    specific issues: [details]. Attempt 2/5.'
> 4. Track retry count, enforce max_retries from VerificationStrategy
> 5. Support FailureAction: RETRY, ESCALATE (ask user), ABORT
> 6. Exponential backoff hint for token budgets (reduce context on retry)
>
> Create tests for: retry prompt generation, max retry enforcement,
> escalation trigger, abort trigger."

**Exit check:**

```bash
pytest tests/test_mota/test_feedback.py -x -q
```

**Commit:** `feat(mota): add verification feedback loop with retry`

---

#### Session 15 🔨🤝 — Phase 2 Integration: Single-Agent Flow

**Duration:** ~45 min | **Depends on:** Sessions 9-14

**What you build:**

- `tests/test_mota/test_phase2_integration.py` — End-to-end single-agent flow
- Update `codetrellis/mota/__init__.py` — Export Phase 2 APIs

**What to ask the AI:**

> "Create comprehensive integration tests for the complete single-agent flow:
>
> 1. User message → sanitize → classify intent → select blueprint
> 2. Blueprint → assemble context (with IMPL_LOGIC filtering)
> 3. Context → generate system prompt
> 4. (Mock) LLM response → verification engine
> 5. If verification fails → feedback loop → retry
> 6. Track everything in AgentSession + AuditLog
>
> Test scenarios:
>
> - Happy path: message → verified output in 1 iteration
> - Retry path: first attempt fails lint, second attempt passes
> - Max retry exceeded: escalation triggered
> - Stale matrix: warning logged but proceeds
> - Injection attempt: sanitized then processed normally
>
> Also update `__init__.py` to export all Phase 2 public APIs."

**Exit check:**

```bash
pytest tests/test_mota/ -x -q  # ALL Phase 1 + Phase 2 tests pass
```

**Commit:** `feat(mota): complete Phase 2 — single-agent flow with verification`

---

#### Session 16 👤⚡ — Phase 2 Review & Metrics Baseline

**Duration:** ~30 min | **Depends on:** Session 15

**What you build:**

- Manual testing with real matrix data
- Metrics baseline document

**What to ask the AI:**

> "Help me run the MOTA pipeline against the actual CodeTrellis matrix.
>
> 1. Load the real matrix from `.codetrellis/cache/`
> 2. Run 10 sample messages through AgentFactory + ContextAssembler
> 3. Print: intent detected, persona selected, context sections loaded,
>    token count, IMPL_LOGIC snippets selected
> 4. Summarize: average token usage, intent accuracy on these 10, time taken
>
> Messages to test:
>
> - 'Add a new parser for Svelte 5 runes'
> - 'Fix the bug in cache_optimizer.py where stale entries aren't cleaned'
> - 'Review the security of mcp_server.py'
> - 'Plan the migration from dataclasses to pydantic'
> - 'How should we restructure the parser modules?'
> - 'Create tests for the intent classifier'
> - 'Update the README to include MOTA documentation'
> - 'Debug why the Java parser fails on annotations'
> - 'Add pagination to the skills API'
> - 'Refactor the builder.py to reduce cyclomatic complexity'"

**Exit check:**

- Human review: Do the intents/personas/context sections look correct?
- Note any misclassifications for intent classifier tuning

**Commit:** `docs(mota): Phase 2 metrics baseline`

---

### PHASE 3: PLATFORM (Sessions 17-22) — Week 8-10

---

#### Session 17 🏗️🤝 — MCP Tools (orchestrate, get_blueprint, verify_output)

**Duration:** ~75 min | **Depends on:** Phase 2, existing `mcp_server.py`

**What to ask the AI:**

> "Add 3 new MCP tools to the existing `codetrellis/mcp_server.py`:
>
> 1. `orchestrate(message)` — Full MOTA flow: sanitize → intent → blueprint
>    → context → prompt. Returns the assembled context + prompt ready for LLM.
> 2. `get_blueprint(message)` — Preview: show what MOTA would do without
>    executing. Returns persona, tools, sections, verification strategy.
> 3. `verify_output(file_paths, language)` — Run verification independently.
>    Returns structured pass/fail results.
>
> Study existing mcp_server.py patterns for tool registration. Follow
> the same MCPTool/MCPToolResult patterns. Add tests."

**Exit check:**

```bash
pytest tests/test_mota/test_mcp.py -x -q
codetrellis mcp --list-tools  # Should show new tools
```

**Commit:** `feat(mota): add MCP tools — orchestrate, get_blueprint, verify_output`

---

#### Session 18 🔨🤖 — Agent Pipeline (Multi-Agent)

**Duration:** ~45 min | **Depends on:** Phase 2

**What to ask the AI:**

> "Create `codetrellis/mota/pipeline.py` with an `AgentPipeline` class.
> Multi-agent sequential workflows:
>
> 1. Define a pipeline as a list of AgentBlueprint stages
> 2. Support strategies: sequential, parallel, conditional
> 3. Handoff: previous agent's output becomes next agent's context
> 4. Example: Planner → Implementor → Reviewer
> 5. Shared context dict that all agents can read/write
> 6. Pipeline-level audit trail (which agent did what)
>
> Create tests for: sequential pipeline, context handoff, pipeline abort
> when a stage fails."

**Exit check:**

```bash
pytest tests/test_mota/test_pipeline.py -x -q
```

**Commit:** `feat(mota): add multi-agent pipeline orchestration`

---

#### Session 19 🏗️🤝 — Extension Integration (src/mota/)

**Duration:** ~90 min | **Depends on:** Sessions 17-18 | **Workspace:** VS Code Extension

> ⚠️ **Switch to the CodeTrellis Chat extension workspace for this session.**

**What to ask the AI:**

> "Wire MOTA into the CodeTrellis Chat extension. Create `src/mota/` with:
>
> 1. `MOTAService` — calls MCP tools (orchestrate, get_blueprint, verify_output)
> 2. `MOTAChatHandler` — intercepts chat messages, runs through MOTA pipeline
> 3. Register MOTAService in the DI container
> 4. Feature flag: `codetrellis.mota.enabled` (default: false for Phase 3)
>
> Follow existing extension patterns — check DI registrations, service interfaces,
> chat handler patterns. This should be a clean integration, not a rewrite."

**Exit check:**

```bash
npm run build  # Compiles without errors
npm run test   # Existing tests still pass
```

**Commit:** `feat(extension): wire MOTA service into chat handler`

---

#### Session 20 🔨🤝 — Chat UI: Persona Badge + Verification Display

**Duration:** ~45 min | **Depends on:** Session 19 | **Workspace:** VS Code Extension

**What to ask the AI:**

> "Add MOTA UI elements to the CodeTrellis Chat extension:
>
> 1. Persona badge: Show 🔧/🔍/📋 emoji + persona name at the top of
>    agent responses when MOTA is enabled
> 2. Verification panel: Show ✅/❌ results after task completion
>    (type check, lint, test results)
> 3. Progressive disclosure: Level 1 (silent), Level 2 (badge + verify),
>    Level 3 (full trace) — controlled by settings
> 4. Failure UX: Show retry progress, 'Accept Anyway' button
>
> Follow existing webview/chat rendering patterns."

**Exit check:**

```bash
npm run build && npm run test
```

**Commit:** `feat(extension): add MOTA persona badges and verification UI`

---

#### Session 21 🔨🤝 — Slash Commands

**Duration:** ~30 min | **Depends on:** Session 19 | **Workspace:** VS Code Extension

**What to ask the AI:**

> "Add MOTA slash commands to CodeTrellis Chat:
> /implement — Force Implementor persona
> /review — Force Reviewer persona
> /plan — Force Planner persona
> /auto — Let MOTA decide (default)
> /debug — Force Debugger (Phase 4, disabled for now)
> /test — Force Tester (Phase 4, disabled for now)
>
> Register as chat participant commands. Pass the forced persona to
> MOTAChatHandler. Show in autocomplete with descriptions."

**Exit check:**

```bash
npm run build && npm run test
```

**Commit:** `feat(extension): add MOTA slash commands`

---

#### Session 22 🏗️🤝 — Phase 3 E2E Tests

**Duration:** ~60 min | **Depends on:** Sessions 17-21

**What to ask the AI:**

> "Create end-to-end tests for the full MOTA platform:
>
> 1. MCP tool tests: orchestrate, get_blueprint, verify_output
> 2. Pipeline test: Planner → Implementor → Reviewer sequence
> 3. Extension integration test: chat message → MOTA → response with badge
> 4. Slash command test: /review overrides MOTA's auto-detection
> 5. Feature flag test: disabled MOTA = vanilla behavior
>
> Create `tests/test_mota/test_e2e.py` for Python-side tests.
> Extension tests in the extension workspace."

**Exit check:**

```bash
pytest tests/test_mota/ -x -q  # ALL tests pass
# In extension workspace:
npm run test
```

**Commit:** `feat(mota): complete Phase 3 — platform integration + E2E tests`

---

### PHASE 4: SCALE (Sessions 23-26) — Week 11-12

---

#### Session 23 🔨🤖 — Add Debugger + Tester + Architect Personas

**Duration:** ~40 min | **Depends on:** Phase 3

**What to ask the AI:**

> "Add 3 new persona blueprints to `codetrellis/mota/blueprints.py`:
>
> 1. 🐛 Debugger: triggers on 'debug', 'error', stack traces. Sections:
>    ERROR_HANDLING, IMPL_LOGIC, TYPES. Verification: reproduction test.
> 2. 🧪 Tester: triggers on 'test', 'coverage', 'spec'. Sections:
>    TYPES, IMPL_LOGIC, RUNBOOK. Verification: coverage increase.
> 3. 🏗️ Architect: triggers on 'architecture', 'restructure', 'design system'.
>    Sections: OVERVIEW, TYPES, ROUTES, INFRASTRUCTURE. Verification: feasibility.
>
> Update intent classifier to handle new triggers. Update tests. Enable
> /debug and /test slash commands in extension."

**Exit check:**

```bash
pytest tests/test_mota/ -x -q
python -c "from codetrellis.mota.blueprints import list_blueprints; print(f'✅ {len(list_blueprints())} blueprints')"  # Should show more
```

**Commit:** `feat(mota): add Debugger, Tester, Architect personas`

---

#### Session 24 🔨🤝 — Multi-Language Verifiers (Go, Rust, Java, C#)

**Duration:** ~45 min | **Depends on:** Session 13

**What to ask the AI:**

> "Extend `codetrellis/mota/verify.py` with language-specific verifiers:
>
> 1. Go: `go vet` + `golangci-lint` + `go test`
> 2. Rust: `cargo check` + `cargo clippy` + `cargo test`
> 3. Java: `javac` (or maven/gradle) + checkstyle + JUnit
> 4. C#: `dotnet build` + `dotnet format` + `dotnet test`
>
> Extend verify_parser.py to parse output from each tool.
> Handle tool-not-installed gracefully. Create tests with mock outputs."

**Exit check:**

```bash
pytest tests/test_mota/test_verify.py -x -q
```

**Commit:** `feat(mota): add Go, Rust, Java, C# verifiers`

---

#### Session 25 🔨🤝 — Analytics Dashboard

**Duration:** ~45 min | **Depends on:** Phase 3

**What to ask the AI:**

> "Create analytics for MOTA using the AuditLog data:
>
> 1. `codetrellis/mota/analytics.py` — Aggregate audit events into metrics:
>    - Success rate per persona
>    - Average iterations to completion
>    - Token usage trends
>    - Most common intents
>    - Tool denial frequency
>    - Verification pass/fail rates
> 2. Add `analytics` MCP tool to expose metrics
> 3. Create a simple CLI command: `codetrellis mota stats`
>
> Create tests with sample audit data."

**Exit check:**

```bash
pytest tests/test_mota/test_analytics.py -x -q
codetrellis mota stats  # Shows sample output
```

**Commit:** `feat(mota): add analytics dashboard`

---

#### Session 26 ⚡🤝 — Performance Optimization + Final Polish

**Duration:** ~30 min | **Depends on:** Sessions 23-25

**What to ask the AI:**

> "Optimize MOTA performance:
>
> 1. Cache blueprint selections (same intent → same blueprint, skip re-computation)
> 2. Batch matrix section reads (one disk read, not N)
> 3. Lazy-load IMPL_LOGIC (only when persona needs it)
> 4. Add timing decorators to measure each pipeline stage
> 5. Run full test suite, fix any regressions
> 6. Update `codetrellis/mota/__init__.py` with final public API
> 7. Add docstrings to all public methods
>
> Run final metrics: time per pipeline stage, total test count, coverage."

**Exit check:**

```bash
pytest tests/test_mota/ -x -q --tb=short  # ALL tests pass
python -c "
from codetrellis.mota import AgentFactory
import time
f = AgentFactory()
start = time.time()
s = f.create_session('Add a new /api/orders endpoint')
elapsed = (time.time() - start) * 1000
print(f'✅ Pipeline: {elapsed:.0f}ms (target: <100ms)')
"
```

**Commit:** `feat(mota): performance optimization + final polish`

---

### Session Summary Dashboard

| Session         | Phase | Duration | Type | Key Deliverable               | Files                        |
| --------------- | ----- | -------- | ---- | ----------------------------- | ---------------------------- |
| 1               | P1    | 20m      | ⚡🤖 | Core types + package          | types.py                     |
| 2               | P1    | 20m      | ⚡🤖 | Input sanitizer               | sanitize.py                  |
| 3               | P1    | 30m      | 🔨🤖 | Audit logger                  | audit.py                     |
| 4               | P1    | 40m      | 🔨🤖 | Intent classifier             | intent.py + fixtures         |
| 5               | P1    | 30m      | 🔨🤖 | Blueprints                    | blueprints.py                |
| 6               | P1    | 30m      | 🔨🤖 | ToolGuard                     | guard.py                     |
| 7               | P1    | 40m      | 🔨🤝 | Agent Factory                 | factory.py                   |
| 8               | P1    | 45m      | 🔨🤝 | Session Manager + integration | session.py                   |
| **P1 Total**    |       | **~4h**  |      | **Phase 1 Complete**          | **8 modules + tests**        |
| 9               | P2    | 60m      | 🏗️🤝 | Context assembler             | context.py                   |
| 10              | P2    | 60m      | 🏗️🤝 | IMPL_LOGIC filter             | logic_filter.py              |
| 11              | P2    | 20m      | ⚡🤖 | Matrix freshness              | freshness.py                 |
| 12              | P2    | 45m      | 🔨🤝 | Prompt generator              | prompt.py                    |
| 13              | P2    | 75m      | 🏗️🤝 | Verification engine           | verify.py + verify_parser.py |
| 14              | P2    | 30m      | 🔨🤖 | Feedback loop                 | feedback.py                  |
| 15              | P2    | 45m      | 🔨🤝 | Phase 2 integration           | integration tests            |
| 16              | P2    | 30m      | 👤⚡ | Metrics baseline              | manual testing               |
| **P2 Total**    |       | **~6h**  |      | **Phase 2 Complete**          | **7 modules + tests**        |
| 17              | P3    | 75m      | 🏗️🤝 | MCP tools                     | mcp_server.py update         |
| 18              | P3    | 45m      | 🔨🤖 | Agent pipeline                | pipeline.py                  |
| 19              | P3    | 90m      | 🏗️🤝 | Extension integration         | src/mota/ (extension)        |
| 20              | P3    | 45m      | 🔨🤝 | Chat UI                       | extension webview            |
| 21              | P3    | 30m      | 🔨🤝 | Slash commands                | extension chat               |
| 22              | P3    | 60m      | 🏗️🤝 | E2E tests                     | test_e2e.py                  |
| **P3 Total**    |       | **~6h**  |      | **Phase 3 Complete**          | **MCP + Extension**          |
| 23              | P4    | 40m      | 🔨🤖 | +3 personas                   | blueprints.py update         |
| 24              | P4    | 45m      | 🔨🤝 | Multi-lang verifiers          | verify.py update             |
| 25              | P4    | 45m      | 🔨🤝 | Analytics                     | analytics.py                 |
| 26              | P4    | 30m      | ⚡🤝 | Performance + polish          | optimization                 |
| **P4 Total**    |       | **~3h**  |      | **Phase 4 Complete**          | **Scaling + analytics**      |
| **GRAND TOTAL** |       | **~19h** |      | **MOTA Complete**             | **17 modules + tests**       |

---

### Tips for AI-Assisted Sessions

1. **Start each session fresh.** Open a new AI chat. Paste the "What to Ask"
   prompt. The AI reads the codebase and has all the context it needs.

2. **One commit per session.** This gives you clean rollback points. If a
   session goes sideways, `git reset --hard` and retry.

3. **Run tests before AND after.** Before: confirm nothing is broken. After:
   confirm the session's work is solid.

4. **Sessions 1-6 can be parallelized.** They have minimal dependencies on
   each other (only Session 1's types). If you have multiple AI windows,
   run Sessions 2, 3, 4, 5, 6 in parallel after Session 1.

5. **Sessions 7-8 are integration points.** These tie everything together.
   Expect more back-and-forth with the AI here.

6. **Phase 3 requires workspace switching.** Sessions 19-21 are in the VS Code
   extension workspace, not the Python workspace.

7. **Session 16 is your checkpoint.** After Phase 2, you have a working
   single-agent pipeline. Stop and evaluate before committing to Phase 3.

8. **Use `/review` on your own code.** Once Phase 3 is done, use MOTA's
   Reviewer persona to review the MOTA code itself. Meta-validation!

---

## 13. Execution Strategy: Session-by-Session vs Marathon

### The Question

Can you do all 19 hours in one go instead of 26 separate sessions?

### The Honest Answer

**Not in a single continuous AI chat.** But you CAN do it in **one sitting** (one day/weekend)
with a structured approach. Here's why and how:

### Why a Single AI Chat Won't Work for 19 Hours

```
Hour 0-2:   ✅ AI has full context, output is excellent
Hour 3-5:   ⚠️ Context window filling up, AI starts summarizing older code
Hour 6-8:   ❌ Session 1's types.py is pushed out of context
Hour 9-12:  💀 AI "forgets" half the codebase, generates inconsistent code
Hour 13-19: 🔥 Fighting the AI more than building — worse than manual coding
```

The AI context window is like a whiteboard. After ~2-3 hours of dense coding,
the whiteboard is full. New information pushes old information off the edge.

### ✅ Recommended: Marathon with Fresh Chats (Best of Both Worlds)

**Do it in one sitting, but open a NEW chat for each phase (or batch of sessions).**

The trick: each new chat reads your **committed code on disk**, not the conversation
history. So it always sees the real, current state — perfectly fresh context.

```
┌─────────────────────────────────────────────────────────────┐
│                    ONE-DAY MARATHON PLAN                     │
│                                                              │
│  Morning (4h):  Phase 1 — Core                              │
│  ├─ Chat 1: Sessions 1-3 (types + sanitize + audit) ~1h     │
│  ├─ Chat 2: Sessions 4-6 (intent + blueprints + guard) ~1.5h│
│  ├─ Chat 3: Sessions 7-8 (factory + session + integration)  │
│  └─ ☕ Break + git log review                               │
│                                                              │
│  Afternoon (6h): Phase 2 — Intelligence                     │
│  ├─ Chat 4: Sessions 9-11 (context + filter + freshness)    │
│  ├─ Chat 5: Sessions 12-14 (prompt + verify + feedback)     │
│  ├─ Chat 6: Sessions 15-16 (integration + manual test)      │
│  └─ 🍕 Break + full test suite review                       │
│                                                              │
│  Evening (6h): Phase 3 — Platform                           │
│  ├─ Chat 7: Sessions 17-18 (MCP tools + pipeline)           │
│  ├─ Chat 8: Sessions 19-21 (extension: integration + UI)    │
│  ├─ Chat 9: Session 22 (E2E tests)                          │
│  └─ 🎉 Break + demo to yourself                             │
│                                                              │
│  Night (3h): Phase 4 — Scale                                │
│  ├─ Chat 10: Sessions 23-24 (personas + verifiers)          │
│  └─ Chat 11: Sessions 25-26 (analytics + polish)            │
│                                                              │
│  Total: ~19h across 11 chats in one sitting                 │
└─────────────────────────────────────────────────────────────┘
```

### The 11 Mega-Prompts (One Per Chat)

Instead of 26 small prompts, here are 11 **batched mega-prompts** that combine
related sessions. Each mega-prompt is designed to fit within one AI context
window and produce multiple files in one go.

---

#### 🟢 MEGA-PROMPT 1 — Foundation (Sessions 1-3) ~1 hour

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA (Matrix-Orchestrated Tool Agents) for the CodeTrellis project.
> This is the first batch. Create these 3 modules + tests:
>
> **1. `codetrellis/mota/__init__.py`** — Package init with `__all__` exports.
>
> **2. `codetrellis/mota/types.py`** — All core dataclasses:
>
> - `PersonaType` enum: IMPLEMENTOR, REVIEWER, PLANNER (Phase 1); DEBUGGER, TESTER, ARCHITECT (Phase 4)
> - `SessionState` enum: INITIALIZING, EXECUTING, VERIFYING, RETRYING, COMPLETE, FAILED
> - `FailureAction` enum: RETRY, ESCALATE, ABORT
> - `TokenBudgetConfig`: system_prompt=2000, matrix_context=8000, conversation=4000, tool_results=6000
> - `VerificationStrategy`: steps list, required_pass_count (ALL/ANY/N), max_retries=3, on_failure, languages
> - `AgentBlueprint`: name, description, trigger, context_sections, instructions, category, priority, persona, tools_allowed, tools_denied, verification, token_budget, max_iterations=5, slash_command
> - `ToolCall`: tool_name, arguments, result, was_allowed, timestamp
> - `AgentIteration`: iteration_number, tool_calls, llm_response, verification_result, token_usage
> - `AgentSession`: blueprint, state, iterations, total_tokens, started_at, completed_at, audit_events
> - `MOTAAuditEvent`: timestamp, event_type, details, session_id, user_message_hash
> - `MatrixFreshness`: is_fresh, stale_files, matrix_age_seconds, recommendation
> - `AgentPipeline`: stages, handoff_strategy, shared_context
>
> **3. `codetrellis/mota/sanitize.py`** — Input sanitization:
>
> - `sanitize_input(message) -> tuple[str, List[str]]` — detect/filter prompt injection
> - At least 10 suspicious patterns (ignore previous instructions, override persona, system: prefix, etc.)
> - Return cleaned message + list of warnings
>
> **4. `codetrellis/mota/audit.py`** — Structured audit logging:
>
> - `AuditLog` class with `log(event_type, details, session_id)` method
> - `get_trail(session_id)` to retrieve full audit trail
> - SHA-256 hash of user messages for privacy (first 12 chars)
> - JSON serialization support
> - In-memory storage with optional file persistence
>
> **5. Tests for all three:** `tests/test_mota/test_types.py`, `test_sanitize.py`, `test_audit.py`
>
> Follow existing CodeTrellis Python conventions. Full docstrings on all public classes/methods.

**After this chat:** `git add -A && git commit -m "feat(mota): foundation — types, sanitizer, audit"`

---

#### 🟢 MEGA-PROMPT 2 — Decision Engine (Sessions 4-6) ~1.5 hours

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA for CodeTrellis. The foundation is done (`codetrellis/mota/types.py`,
> `sanitize.py`, `audit.py`). Now create the decision engine — 3 modules + tests:
>
> **1. `codetrellis/mota/intent.py`** — Intent Classifier:
>
> - `IntentClassifier` class with `classify(message) -> IntentResult` (intent name + confidence 0-1)
> - Pure regex + keyword matching, NO LLM calls
> - Intents: add-endpoint, add-model, add-store, add-test, add-route, add-hook, update-config, update-infrastructure, fix-issue, refactor-code, add-migration, review, plan, debug, test-gen
> - Slash command override: /implement, /review, /plan, /auto, /debug, /test
> - Fallback to 'implementor' persona for ambiguous messages
> - Trigger patterns: "add","create","implement","fix" → Implementor; "review","check","audit" → Reviewer; "plan","design","estimate" → Planner
>
> **2. `codetrellis/mota/blueprints.py`** — Pre-defined AgentBlueprints:
>
> - Convert the 11 existing CodeTrellis skills into AgentBlueprints
> - `get_blueprint(intent_name) -> AgentBlueprint`
> - `list_blueprints() -> List[AgentBlueprint]`
> - `get_default_blueprint() -> AgentBlueprint` (fallback)
> - Each blueprint defines: persona, tools_allowed/denied, verification strategy, token budget, context_sections
> - Implementor: tools=read,write,terminal(build/test),search; denied=delete_project,git_push,git_force; verify=type_check+lint+test ALL pass
> - Reviewer: tools=read,search,comment; denied=ALL write,terminal; verify=best_practice checklist
> - Planner: tools=read,search; denied=ALL write,terminal; verify=feasibility score
>
> **3. `codetrellis/mota/guard.py`** — ToolGuard:
>
> - `ToolGuard(blueprint, audit_log)` — runtime tool permission enforcement
> - `can_execute(tool_name, session) -> bool` — deny list priority over allow list
> - Every decision (allow/deny) logged to AuditLog
> - `get_denied_attempts(session_id) -> List[ToolCall]`
> - Thread-safe with threading.Lock
>
> **4. Tests:** `test_intent.py` (with 200 labeled messages in `fixtures/test_messages.json`), `test_blueprints.py`, `test_guard.py`
>
> Study the existing types in `codetrellis/mota/types.py` before starting.

**After this chat:** `git add -A && git commit -m "feat(mota): decision engine — intent, blueprints, guard"`

---

#### 🟢 MEGA-PROMPT 3 — Phase 1 Integration (Sessions 7-8) ~1.5 hours

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA for CodeTrellis. Foundation + decision engine are done.
> Now wire everything together — 2 modules + integration tests:
>
> **1. `codetrellis/mota/factory.py`** — Agent Factory (main orchestrator):
>
> - `AgentFactory` class that ties the full Phase 1 pipeline together
> - `create_session(user_message, matrix=None) -> AgentSession`
> - Flow: sanitize input → classify intent → select blueprint → create ToolGuard → log to audit → return configured AgentSession
> - Handle slash command overrides
> - Handle injection attempts (sanitize, log warning, continue)
>
> **2. `codetrellis/mota/session.py`** — Session Manager:
>
> - `SessionManager` class managing AgentSession lifecycle
> - State transitions: INITIALIZING → EXECUTING → VERIFYING → COMPLETE/FAILED
> - `add_iteration()`, `get_current_iteration()`
> - Enforce `max_iterations` from blueprint
> - Track total token usage, timestamps
> - `to_dict()` for JSON serialization
>
> **3. Tests:** `test_factory.py`, `test_session.py`, `test_phase1_integration.py`
>
> - Integration tests: 10+ scenarios covering happy path, slash overrides,
>   injection attempts, ambiguous messages, each persona type
>
> **4. Update `codetrellis/mota/__init__.py`** — export all Phase 1 public APIs
>
> Study ALL existing mota/ modules before starting. This is the integration layer.

**After this chat:** `git add -A && git commit -m "feat(mota): Phase 1 complete — factory + session + integration"`

**☕ BREAK — Review git log, run full test suite, celebrate Phase 1!**

---

#### 🔵 MEGA-PROMPT 4 — Smart Context (Sessions 9-11) ~2 hours

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA Phase 2 for CodeTrellis. Phase 1 is complete (intent, blueprints,
> guard, factory, session). Now add smart context — 3 modules + tests:
>
> **1. `codetrellis/mota/context.py`** — Context Assembler:
>
> - `ContextAssembler` class that builds the right context for each agent
> - Read matrix sections specified in AgentBlueprint.context_sections
> - Integrate with existing `codetrellis/jit_context.py` (study JITContextResult, EXTENSION_TO_SECTIONS)
> - Merge: blueprint context + JIT context + conversation history
> - Respect TokenBudgetConfig limits — truncate intelligently if over budget
> - Return structured `ContextResult` with sections loaded, token counts, truncation info
>
> **2. `codetrellis/mota/logic_filter.py`** — IMPL_LOGIC Filter:
>
> - `LogicFilter` class that reduces 4053 IMPLEMENTATION_LOGIC snippets to ~20 relevant ones
> - Filtering strategies: file path relevance, function/class name matching, import overlap, complexity priority
> - `filter(snippets, intent, file_paths=None, max_snippets=20) -> List[snippet]`
>
> **3. `codetrellis/mota/freshness.py`** — Matrix Freshness:
>
> - `check_freshness(matrix_path, source_paths=None) -> MatrixFreshness`
> - Check matrix file mtime vs source files
> - Thresholds: <5min=ok, 5-30min=incremental, >30min=rescan
> - Study existing `codetrellis/cache.py` and `codetrellis/cache_optimizer.py`
>
> **4. Tests:** `test_context.py`, `test_logic_filter.py`, `test_freshness.py`

**After this chat:** `git add -A && git commit -m "feat(mota): smart context — assembler, logic filter, freshness"`

---

#### 🔵 MEGA-PROMPT 5 — Verification Pipeline (Sessions 12-14) ~2 hours

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA Phase 2 verification for CodeTrellis. Context assembler is done.
> Now add prompt generation + verification + feedback — 4 modules + tests:
>
> **1. `codetrellis/mota/prompt.py`** — Prompt Generator:
>
> - `PromptGenerator` class: persona + context + tools → system prompt for LLM
> - Include persona instructions, context from ContextAssembler, allowed tools list, verification expectations, output format, constraint reminders
> - Respect TokenBudgetConfig.system_prompt limit
>
> **2. `codetrellis/mota/verify.py`** — Verification Engine:
>
> - `VerificationEngine` class running deterministic checks on agent output
> - Python: mypy (type check) + ruff (lint) + pytest (tests)
> - TypeScript: tsc (type check) + eslint (lint) + vitest/jest (tests)
> - Execute as subprocess, capture output
> - Use VerificationStrategy from blueprint (which steps, ALL/ANY/N must pass)
> - Handle tool-not-installed gracefully (skip with warning)
>
> **3. `codetrellis/mota/verify_parser.py`** — Output Parser:
>
> - Parse raw output from mypy, ruff, tsc, eslint, pytest, vitest
> - Into structured results: errors count, warnings count, test pass/fail
>
> **4. `codetrellis/mota/feedback.py`** — Feedback Loop:
>
> - `FeedbackLoop` class: verification failure → focused error context → retry prompt
> - Track retry count, enforce max_retries from VerificationStrategy
> - Support FailureAction: RETRY, ESCALATE (ask user), ABORT
> - Exponential backoff hint for token budgets
>
> **5. Tests:** `test_prompt.py`, `test_verify.py`, `test_verify_parser.py`, `test_feedback.py`

**After this chat:** `git add -A && git commit -m "feat(mota): verification pipeline — prompt, verify, feedback"`

---

#### 🔵 MEGA-PROMPT 6 — Phase 2 Integration (Sessions 15-16) ~1 hour

> **Paste this into a fresh AI chat:**
>
> I'm finalizing MOTA Phase 2 for CodeTrellis. All modules are built. Now:
>
> **1. `tests/test_mota/test_phase2_integration.py`** — Full single-agent flow tests:
>
> - Happy path: message → sanitize → intent → blueprint → context → prompt → (mock LLM) → verify → pass
> - Retry path: first attempt fails lint, second passes
> - Max retry exceeded: escalation triggered
> - Stale matrix: warning logged but proceeds
> - Injection attempt: sanitized then processed normally
> - At least 10 end-to-end scenarios
>
> **2. Update `codetrellis/mota/__init__.py`** — export all Phase 2 public APIs
>
> **3. Manual validation** — Run the pipeline against the real CodeTrellis matrix
> with 10 sample messages and print: intent, persona, context sections, token count.
>
> Study ALL existing mota/ modules. This is the final integration test for Phase 2.

**After this chat:** `git add -A && git commit -m "feat(mota): Phase 2 complete — single-agent flow with verification"`

**🍕 BREAK — Full test suite, review metrics, decide if Phase 3 is needed now.**

---

#### 🟣 MEGA-PROMPT 7 — MCP + Pipeline (Sessions 17-18) ~2 hours

> **Paste this into a fresh AI chat:**
>
> I'm building MOTA Phase 3 for CodeTrellis. Phases 1-2 are complete. Now expose
> MOTA via MCP and add multi-agent pipelines — 2 deliverables + tests:
>
> **1. Add 3 MCP tools to existing `codetrellis/mcp_server.py`:**
>
> - `orchestrate(message)` — full MOTA flow: sanitize → intent → blueprint → context → prompt
> - `get_blueprint(message)` — preview what MOTA would do without executing
> - `verify_output(file_paths, language)` — run verification independently
> - Follow existing MCPTool/MCPToolResult patterns in mcp_server.py
>
> **2. `codetrellis/mota/pipeline.py`** — Multi-agent Pipeline:
>
> - `AgentPipeline` class: sequential list of AgentBlueprint stages
> - Strategies: sequential, parallel, conditional
> - Context handoff: previous agent output → next agent input
> - Example: Planner → Implementor → Reviewer
> - Pipeline-level audit trail
>
> **3. Tests:** `test_mcp.py`, `test_pipeline.py`

**After this chat:** `git add -A && git commit -m "feat(mota): MCP tools + multi-agent pipeline"`

---

#### 🟣 MEGA-PROMPT 8 — Extension Integration (Sessions 19-21) ~2.5 hours

> ⚠️ **Switch to CodeTrellis Chat extension workspace for this chat.**
>
> I'm wiring MOTA into the CodeTrellis Chat VS Code extension. The Python MOTA
> package is complete with MCP tools. Now integrate into the extension:
>
> **1. `src/mota/MOTAService.ts`** — Calls MCP tools (orchestrate, get_blueprint, verify_output)
> **2. `src/mota/MOTAChatHandler.ts`** — Intercepts chat messages, runs MOTA pipeline
> **3. DI registration** — Register MOTAService in the container
> **4. Feature flag** — `codetrellis.mota.enabled` (default: false)
> **5. Chat UI: persona badge** — Show 🔧/🔍/📋 + persona name on agent responses
> **6. Chat UI: verification panel** — Show ✅/❌ after task completion
> **7. Progressive disclosure** — Level 1 (silent), Level 2 (badge+verify), Level 3 (full trace)
> **8. Slash commands** — /implement, /review, /plan, /auto, /debug (disabled), /test (disabled)
>
> Follow existing extension patterns for DI, chat handlers, webview rendering.

**After this chat:** `git add -A && git commit -m "feat(extension): MOTA integration — service, UI, slash commands"`

---

#### 🟣 MEGA-PROMPT 9 — Phase 3 E2E (Session 22) ~1 hour

> **Paste this into a fresh AI chat:**
>
> MOTA Phase 3 is wired up (MCP tools + extension). Create end-to-end tests:
>
> **Python side** (`tests/test_mota/test_e2e.py`):
>
> - MCP tool tests: orchestrate, get_blueprint, verify_output
> - Pipeline test: Planner → Implementor → Reviewer sequence
>
> **Extension side** (in extension workspace):
>
> - Chat message → MOTA → response with persona badge
> - Slash command override test
> - Feature flag disabled = vanilla behavior
>
> Run full test suite across both workspaces.

**After this chat:** `git add -A && git commit -m "feat(mota): Phase 3 complete — E2E tests passing"`

**🎉 BREAK — You now have a working MOTA. Demo it to yourself!**

---

#### 🟠 MEGA-PROMPT 10 — New Personas + Verifiers (Sessions 23-24) ~1.5 hours

> **Paste this into a fresh AI chat:**
>
> MOTA Phases 1-3 are complete. Phase 4 — add 3 new personas and multi-language verifiers:
>
> **1. Update `codetrellis/mota/blueprints.py`** — Add 3 new persona blueprints:
>
> - 🐛 Debugger: triggers on "debug","error", stack traces; sections: ERROR_HANDLING, IMPL_LOGIC, TYPES
> - 🧪 Tester: triggers on "test","coverage","spec"; sections: TYPES, IMPL_LOGIC, RUNBOOK
> - 🏗️ Architect: triggers on "architecture","restructure"; sections: OVERVIEW, TYPES, ROUTES, INFRASTRUCTURE
>
> **2. Update `codetrellis/mota/intent.py`** — Handle new trigger patterns
>
> **3. Extend `codetrellis/mota/verify.py`** — Add language verifiers:
>
> - Go: `go vet` + `golangci-lint` + `go test`
> - Rust: `cargo check` + `cargo clippy` + `cargo test`
> - Java: `javac`/maven/gradle + checkstyle + JUnit
> - C#: `dotnet build` + `dotnet format` + `dotnet test`
>
> **4. Extend `codetrellis/mota/verify_parser.py`** — Parse output from new tools
>
> **5. Enable /debug and /test slash commands** in extension
>
> **6. Tests for everything**

**After this chat:** `git add -A && git commit -m "feat(mota): +3 personas + Go/Rust/Java/C# verifiers"`

---

#### 🟠 MEGA-PROMPT 11 — Analytics + Polish (Sessions 25-26) ~1.5 hours

> **Paste this into a fresh AI chat:**
>
> MOTA is feature-complete. Final session — analytics + performance + polish:
>
> **1. `codetrellis/mota/analytics.py`** — Aggregate audit events into metrics:
>
> - Success rate per persona, avg iterations, token usage trends
> - Most common intents, tool denial frequency, verification rates
> - `get_stats() -> Dict` and `format_report() -> str`
>
> **2. Add `analytics` MCP tool** to mcp_server.py
>
> **3. Add CLI command:** `codetrellis mota stats`
>
> **4. Performance optimization:**
>
> - Cache blueprint selections (same intent → same blueprint)
> - Batch matrix section reads (one disk read, not N)
> - Lazy-load IMPL_LOGIC (only when needed)
> - Add timing decorators to measure pipeline stages
>
> **5. Final polish:**
>
> - Docstrings on all public methods
> - Update **init**.py with complete public API
> - Run full test suite, fix any regressions
>
> **6. Tests:** `test_analytics.py` + full regression suite

**After this chat:** `git add -A && git commit -m "feat(mota): analytics, performance, final polish — MOTA complete 🎉"`

---

### Comparison: 26 Sessions vs 11 Mega-Prompts

| Approach                              | Chats    | Wall Time | Quality                | Recovery                    |
| ------------------------------------- | -------- | --------- | ---------------------- | --------------------------- |
| **26 sessions** (original)            | 26 chats | ~19h      | ⭐⭐⭐⭐⭐ Best        | Easy — per-file rollback    |
| **11 mega-prompts** (recommended)     | 11 chats | ~17h      | ⭐⭐⭐⭐ Great         | Good — per-phase rollback   |
| **1 marathon chat** (not recommended) | 1 chat   | ~19h+     | ⭐⭐ Poor after hour 6 | None — restart from scratch |

### ✅ Final Recommendation

**Go with 11 mega-prompts.** You get:

- ✅ One sitting (one day/weekend marathon)
- ✅ Fresh AI context for each batch (no degradation)
- ✅ 11 clean git commits (rollback per phase)
- ✅ Natural break points for coffee/food
- ✅ ~17 hours total (2h saved from reduced chat setup overhead)
- ✅ Each mega-prompt produces 2-4 tested, working files

**The commit flow:**

```
git log --oneline
abc1234 feat(mota): analytics, performance, final polish — MOTA complete 🎉
def5678 feat(mota): +3 personas + Go/Rust/Java/C# verifiers
ghi9012 feat(mota): Phase 3 complete — E2E tests passing
jkl3456 feat(extension): MOTA integration — service, UI, slash commands
mno7890 feat(mota): MCP tools + multi-agent pipeline
pqr1234 feat(mota): Phase 2 complete — single-agent flow with verification
stu5678 feat(mota): verification pipeline — prompt, verify, feedback
vwx9012 feat(mota): smart context — assembler, logic filter, freshness
yza3456 feat(mota): Phase 1 complete — factory + session + integration
bcd7890 feat(mota): decision engine — intent, blueprints, guard
efg1234 feat(mota): foundation — types, sanitizer, audit
```
