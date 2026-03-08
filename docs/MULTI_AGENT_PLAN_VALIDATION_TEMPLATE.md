# Multi-Agent Plan Validation Template

# ======================================

# A reusable framework for validating ANY project plan using 6 agent personas.

#

# HOW TO USE:

# 1. Replace [YOUR PLAN NAME] with your project/plan name

# 2. Write your plan in Section A

# 3. Fill in each agent's review in Section B (Round 1)

# 4. Resolve disagreements in Section C (Round 2)

# 5. Write the final validated plan in Section D

#

# The 6 agents represent different perspectives that catch blind spots.

# You can customize the agents for your domain (see "CUSTOMIZATION" below).

#

# CUSTOMIZATION:

# - For a BUSINESS plan: Replace "Matrix Expert" with "Finance Agent"

# - For a PRODUCT plan: Replace "Security Agent" with "QA Agent"

# - For a STARTUP: Add a 7th agent: "Investor/Fundraising Agent"

# - For HARDWARE: Replace "Architect" with "Hardware Engineer"

# - Feel free to add or remove agents based on your domain

#

# Created: [DATE]

# Author: [YOUR NAME]

# Project: [YOUR PROJECT NAME]

---

# ═══════════════════════════════════════════════════════════════

# SECTION A: THE PLAN (v1.0 — Draft for Review)

# ═══════════════════════════════════════════════════════════════

## Plan Name: [YOUR PLAN NAME]

## Executive Summary

<!-- What are you building? Why? What's the core insight? -->

## Problem Statement

<!-- What's broken today? What's missing? -->

## Proposed Solution

<!-- Architecture, components, how it works -->

## Implementation Phases

<!-- Break it into phases. Each phase should deliver standalone value. -->

### Phase 1: [Name] — [Duration]

<!-- Tasks, files, deliverables -->

### Phase 2: [Name] — [Duration]

<!-- Tasks, files, deliverables -->

### Phase 3: [Name] — [Duration]

<!-- Tasks, files, deliverables -->

## Success Metrics

<!-- How do you know it worked? Be specific and measurable. -->

| Metric | Target | How Measured |
| ------ | ------ | ------------ |
|        |        |              |

## Risks

<!-- What could go wrong? -->

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
|      |        |            |

## Timeline

<!-- Total estimated effort -->

## Dependencies

<!-- What do you need that already exists? What's new? -->

---

# ═══════════════════════════════════════════════════════════════

# SECTION B: ROUND 1 — INDEPENDENT AGENT REVIEWS

# ═══════════════════════════════════════════════════════════════

#

# INSTRUCTIONS: For each agent, write their review by adopting

# their perspective. Be HONEST and CRITICAL. The goal is to find

# problems NOW, not after you've built the wrong thing.

#

# Each agent produces:

# ✅ What they agree with (validation)

# ⚠️ What concerns them (risks)

# ❌ What won't work (blockers)

# 💡 What they'd do differently (alternatives)

---

## 🔴 AGENT 1: THE SKEPTIC

<!-- Perspective: Engineering Pragmatism -->
<!-- Core question: "Is this actually buildable in reasonable time?" -->
<!-- Bias: Assumes things take 3x longer and are 2x harder -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

## 🟢 AGENT 2: THE ARCHITECT

<!-- Perspective: System Design & Composability -->
<!-- Core question: "Are the abstractions right? Does this compose?" -->
<!-- Bias: Thinks in interfaces, contracts, and extensibility -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

## 🔵 AGENT 3: THE USER ADVOCATE

<!-- Perspective: User/Developer Experience -->
<!-- Core question: "Will real people actually use this?" -->
<!-- Bias: Users are busy, lazy, and hate configuration -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

## 🟡 AGENT 4: THE BUSINESS STRATEGIST

<!-- Perspective: Market Positioning & Competition -->
<!-- Core question: "Does this create a defensible advantage?" -->
<!-- Bias: Everything must serve differentiation -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

## 🟣 AGENT 5: THE DOMAIN EXPERT

<!-- Perspective: Deep knowledge of the specific domain/technology -->
<!-- Core question: "Can the existing infrastructure support this?" -->
<!-- Bias: Knows every limitation and capability of current system -->
<!-- CUSTOMIZE: Rename to match your domain (e.g., "The Data Engineer") -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

## 🟠 AGENT 6: THE SECURITY & RELIABILITY AGENT

<!-- Perspective: Production Readiness & Trust -->
<!-- Core question: "What happens when it fails?" -->
<!-- Bias: Assumes everything will fail and plans for it -->
<!-- CUSTOMIZE: For non-tech projects, rename to "Risk Manager" -->

### Verdict: [PASS / CONDITIONAL PASS / FAIL]

### ✅ Agreements

### ⚠️ Concerns

### ❌ Won't Work

### 💡 Alternatives

---

# ═══════════════════════════════════════════════════════════════

# ROUND 1 SUMMARY TABLE

# ═══════════════════════════════════════════════════════════════

| Agent            | Verdict | Key Demand |
| ---------------- | ------- | ---------- |
| 🔴 Skeptic       |         |            |
| 🟢 Architect     |         |            |
| 🔵 User Advocate |         |            |
| 🟡 Strategist    |         |            |
| 🟣 Domain Expert |         |            |
| 🟠 Security      |         |            |

### Unanimous Agreements (LOCKED ✅)

<!-- Things ALL agents agree on — these are confirmed decisions -->

1.
2.
3.

### Majority Agreements (4+ agents)

<!-- Things MOST agents agree on — high confidence -->

1.
2.
3.

### Disagreements (FLAGGED for Round 2)

<!-- Things agents disagree on — need debate -->

1.
2.
3.

---

# ═══════════════════════════════════════════════════════════════

# SECTION C: ROUND 2 — CROSS-AGENT DEBATE

# ═══════════════════════════════════════════════════════════════

#

# INSTRUCTIONS: For each disagreement from Round 1, let the

# opposing agents debate. Other agents can weigh in.

# Find a RESOLUTION that all agents can accept.

---

## DEBATE 1: [Topic]

<!-- Which agents disagree? What are their positions? -->

### Agent A's Position:

### Agent B's Rebuttal:

### Other Agents Weigh In:

### 🤝 RESOLUTION:

<!-- The compromise that all agents accept -->

---

## DEBATE 2: [Topic]

### Agent A's Position:

### Agent B's Rebuttal:

### Other Agents Weigh In:

### 🤝 RESOLUTION:

---

## DEBATE 3: [Topic]

### Agent A's Position:

### Agent B's Rebuttal:

### Other Agents Weigh In:

### 🤝 RESOLUTION:

---

# ═══════════════════════════════════════════════════════════════

# ROUND 2 CONSENSUS

# ═══════════════════════════════════════════════════════════════

## Architecture Decisions (LOCKED)

| Decision | Resolution | Agreed By |
| -------- | ---------- | --------- |
|          |            |           |

## Must-Have Additions (from Agent Reviews)

1.
2.
3.
4.
5.

---

# ═══════════════════════════════════════════════════════════════

# SECTION D: THE PLAN (v2.0 — FINAL VALIDATED)

# ═══════════════════════════════════════════════════════════════

#

# INSTRUCTIONS: Rewrite the plan from Section A, incorporating

# ALL the feedback from the agents. This is the plan you BUILD.

## Plan Name: [YOUR PLAN NAME] v2.0 (VALIDATED)

## Executive Summary (Updated)

## Architecture (Updated)

## Implementation Phases (Updated)

## Success Metrics (Outcome-Based)

| Metric | Target | How Measured |
| ------ | ------ | ------------ |
|        |        |              |

## Risks & Mitigations (Updated)

| Risk | Impact | Mitigation | Owner |
| ---- | ------ | ---------- | ----- |
|      |        |            |       |

## Timeline (Realistic)

## Validation Summary

| Agent            | Final Verdict |
| ---------------- | ------------- |
| 🔴 Skeptic       |               |
| 🟢 Architect     |               |
| 🔵 User Advocate |               |
| 🟡 Strategist    |               |
| 🟣 Domain Expert |               |
| 🟠 Security      |               |

**Consensus: \_/6 agents approve.**

---

# ═══════════════════════════════════════════════════════════════

# TIPS FOR USING THIS TEMPLATE

# ═══════════════════════════════════════════════════════════════

#

# 1. BE BRUTALLY HONEST in agent reviews. The Skeptic should be

# genuinely skeptical. The Security Agent should assume the worst.

# If you're too nice, the template is useless.

#

# 2. DISAGREE ON PURPOSE. Force at least 2-3 disagreements into

# Round 2. If everyone agrees on everything, you haven't pushed

# hard enough.

#

# 3. CUSTOMIZE THE AGENTS for your domain:

# - Mobile app? Add "Platform Agent" (iOS vs Android concerns)

# - Data pipeline? Replace Architect with "Data Engineer"

# - Startup? Add "Investor Agent" (will VCs fund this?)

# - Regulated industry? Add "Compliance Agent"

#

# 4. TIME BOX IT. Don't spend more than 2-3 hours on the full process:

# - 30 min: Write Plan v1.0

# - 60 min: All 6 agent reviews

# - 30 min: Round 2 debates

# - 30 min: Final plan v2.0

#

# 5. USE WITH AI. Give this template to an AI assistant and say:

# "Here's my plan. Run each of these 6 agent personas against it

# and give me their honest reviews." The AI will role-play each

# persona and find real issues.

#

# 6. REVISIT AFTER BUILDING. Once you've built Phase 1, run the

# agents again on your Phase 2 plan. The Domain Expert will have

# new knowledge from Phase 1 implementation.

---

# ═══════════════════════════════════════════════════════════════

# SECTION E: SESSION-BASED IMPLEMENTATION APPROACH

# ═══════════════════════════════════════════════════════════════

#

# After your plan is validated (Section D), break it into AI-assisted

# sessions. Each session = one AI chat conversation that produces a

# committed, tested deliverable.

#

# WHY SESSIONS?

# - AI assistants work best with focused, bounded tasks

# - One commit per session = clean rollback points

# - Each session fits within a single AI context window

# - You can parallelize independent sessions

# - Clear progress tracking: "I'm on session 12/26"

#

# HOW TO DESIGN SESSIONS:

# 1. Each session should produce 1-3 files max

# 2. Each session must have a clear exit check (test command)

# 3. Mark dependencies — which sessions must complete first

# 4. Classify by effort: ⚡ Quick (<30m), 🔨 Build (30-60m), 🏗️ Deep (60-90m)

# 5. Classify by AI involvement: 🤖 AI-heavy, 🤝 Collaborative, 👤 Human-heavy

# 6. Include "What to Ask" — the exact prompt for the AI

## Session Plan

### PHASE 1: [Name] (Sessions 1-N)

#### Session 1 [⚡/🔨/🏗️] [🤖/🤝/👤] — [Title]

**Duration:** ~Xm | **Depends on:** [Nothing / Session N]

**What you build:**

<!-- List specific files -->

**What to ask the AI:**

> "[Paste this exact prompt into your AI chat session]"

**Exit check:**

```bash
# Command(s) to verify the session's work
```

**Commit:** `type(scope): description`

---

#### Session 2 ...

<!-- Repeat for each session -->

---

### PHASE 2: [Name] (Sessions N+1 to M)

<!-- Continue same pattern -->

---

### Session Summary Dashboard

| Session   | Phase | Duration | Type | Key Deliverable | Files         |
| --------- | ----- | -------- | ---- | --------------- | ------------- |
| 1         | P1    | Xm       | ⚡🤖 | [What]          | [file.py]     |
| 2         | P1    | Xm       | 🔨🤝 | [What]          | [file.py]     |
| ...       |       |          |      |                 |               |
| **TOTAL** |       | **Xh**   |      | **Complete**    | **N modules** |

---

### Tips for AI-Assisted Sessions

<!-- Customize these for your project -->

1. **Start each session fresh.** Open a new AI chat. Paste the "What to Ask"
   prompt. The AI reads the codebase and has all the context it needs.

2. **One commit per session.** Clean rollback points. If a session goes
   sideways, `git reset --hard` and retry.

3. **Run tests before AND after.** Before: confirm nothing is broken.
   After: confirm the session's work is solid.

4. **Parallelize where possible.** Look at the dependency graph. Sessions
   with no dependencies on each other can run in parallel AI windows.

5. **Integration sessions need more attention.** Sessions that combine
   multiple modules (like wiring everything together) need more human
   guidance. Mark these as 🤝 Collaborative.

6. **Checkpoint after each phase.** Before starting Phase N+1, review
   Phase N output. Run the agents from Section B again on the updated
   plan if needed.

7. **Track actual vs estimated time.** Fill in actual duration after each
   session. This helps calibrate future project estimates.

| Session | Estimated | Actual | Notes |
| ------- | --------- | ------ | ----- |
| 1       | Xm        |        |       |
| 2       | Xm        |        |       |
| ...     |           |        |       |

---

# ═══════════════════════════════════════════════════════════════

# SECTION F: MEGA-PROMPT MARATHON APPROACH (ALTERNATIVE)

# ═══════════════════════════════════════════════════════════════

#

# If you want to do the entire implementation in ONE SITTING (marathon),

# batch multiple sessions into "mega-prompts" — one AI chat per phase.

#

# WHY MEGA-PROMPTS?

# - Fewer chat sessions (11 instead of 26)

# - Same total time, less overhead from setup/context switching

# - Still get fresh AI context per batch (no quality degradation)

# - Clean git commits per batch

#

# HOW TO DESIGN MEGA-PROMPTS:

# 1. Group 2-4 related sessions into one mega-prompt

# 2. Each mega-prompt should produce files that belong together logically

# 3. Keep each mega-prompt under ~2 hours of AI work

# 4. Insert breaks between phases for human review

#

# DO NOT try a single continuous AI chat for 19+ hours. The AI loses

# context and quality degrades dramatically after hour 3-4.

## Marathon Schedule

<!-- Plan your day/weekend -->

```
Morning (Xh):   Phase 1 — [Name]
├─ Mega-Prompt 1: Sessions [1-3] — [Title] (~Xh)
├─ Mega-Prompt 2: Sessions [4-6] — [Title] (~Xh)
├─ Mega-Prompt 3: Sessions [7-8] — [Title] (~Xh)
└─ ☕ Break + review

Afternoon (Xh): Phase 2 — [Name]
├─ Mega-Prompt 4: Sessions [9-11] — [Title] (~Xh)
├─ Mega-Prompt 5: Sessions [12-14] — [Title] (~Xh)
├─ Mega-Prompt 6: Sessions [15-16] — [Title] (~Xh)
└─ 🍕 Break + review

Evening (Xh):   Phase 3 — [Name]
├─ ...
└─ 🎉 Break + demo
```

## Mega-Prompts

### Mega-Prompt 1 — [Title] (Sessions 1-N) ~Xh

> **Paste into a fresh AI chat:**
>
> I'm building [PROJECT]. This is batch 1. Create these modules + tests:
>
> **1. `path/to/file.py`** — [Description]:
>
> - [Requirement 1]
> - [Requirement 2]
>
> **2. `path/to/file2.py`** — [Description]:
>
> - [Requirement 1]
>
> **3. Tests for everything.**
>
> Follow existing project conventions.

**After this chat:** `git add -A && git commit -m "type(scope): description"`

---

### Mega-Prompt 2 — [Title] (Sessions N+1-M)

<!-- Repeat pattern -->

---

## Comparison: Sessions vs Mega-Prompts vs Marathon

| Approach                              | Chats | Wall Time | Quality         | Recovery                    |
| ------------------------------------- | ----- | --------- | --------------- | --------------------------- |
| **Sessions** (granular)               | Many  | Xh        | ⭐⭐⭐⭐⭐ Best | Easy — per-file rollback    |
| **Mega-prompts** (recommended)        | ~10   | Xh        | ⭐⭐⭐⭐ Great  | Good — per-batch rollback   |
| **1 marathon chat** (not recommended) | 1     | Xh+       | ⭐⭐ Poor       | None — restart from scratch |

**✅ Recommendation:** Use mega-prompts. Same total time, fewer chats,
fresh context each batch, clean git history.
