# Session-Learned Rules — Derived from 60 Copilot Sessions (March 2026)

> These rules were machine-extracted from analyzing 352 MB of conversation history across 60 sessions.
> Date range: 2026-03-08 through 2026-03-19.
> They encode the recurring friction patterns, wasted cycles, and proven effective strategies
> observed in real usage of this repository with Copilot.
>
> **Purpose:** Improve session quality, reduce retry waste, and stop repeating the same mistakes.
> **Last synced:** 2026-03-19

---

## Rule 1: Do NOT Start a New Session for the Same Task

**Problem observed:** 15 rapid-fire retries (new session within 15 minutes) with the same or near-identical prompt. The worst case: 3 sessions in 8 minutes for "PyPI Launch Plan Implementation Steps" on 2026-03-14. A new cluster appeared on 2026-03-17: 3 sessions in 3 minutes (11:40, 11:42, 11:43) with model-hopping (gpt-5.4 → unknown → unknown).

**What goes wrong:** Every new session loses all accumulated context — file reads, tool calls, partial progress, and error diagnosis. The model starts from zero each time.

**Rule:**

- If the current session is failing, **diagnose why** before abandoning it.
- If the model is stuck, give it a smaller, focused sub-task instead of re-pasting the full prompt.
- If the session truly must be restarted, carry forward a "context summary" of what was already tried and what failed.
- Never open 3+ sessions for the same task within an hour.

---

## Rule 2: Avoid Copy-Pasting Identical Mega-Prompts Across Sessions

**Problem observed:** The same 5,031-character "senior Python release engineer" prompt was pasted identically into 3 consecutive sessions. Each one restarted the entire audit→implement→validate cycle.

**Rule:**

- If reusing a prompt, **prepend a status update**: "Sessions 1-3 were attempted and [X happened]. Continue from [Y]."
- Better: after a failed session, extract what the model DID accomplish and build on it.
- For multi-session tasks, maintain a living status document (e.g., `STATUS.md`) and reference it instead of re-explaining the full plan.

---

## Rule 3: Be Specific, Not Vague

**Problem observed:** Sessions 3 and 4 both used "see attached and fix the issue" — the model had to guess what "the issue" referred to from screenshots, spending most of its context on broad analysis instead of targeted fixes.

**Rule:**

- Always state: **what** is broken, **where** it is, and **what you expected**.
- Bad: "see attached and fix the issue"
- Good: "The error `Unable to handle /path/to/python` appears in VS Code. The venv was deleted. Update `.vscode/settings.json` to point to the correct interpreter."
- If attaching screenshots, describe the key error text in your message.

---

## Rule 4: Don't Model-Hop Without Reason

**Problem observed:** For "Understanding Code Base with CodeTrellis MCP," the user tried claude-opus-4.6, then claude-sonnet-4.6, then gpt-5.4 in quick succession with the same prompt.

**Rule:**

- Pick one model per task and stick with it unless you have a specific reason to switch.
- Model selection guide for this project:
  - **claude-opus-4.6**: Best for complex multi-file implementation, plan execution, deep code analysis. Use for substantial coding tasks.
  - **claude-sonnet-4.6**: Good for moderate tasks, faster responses. Use for targeted fixes, code review, single-file changes.
  - **gpt-5.4**: Good for strategic/planning tasks, documentation, creative writing, multi-agent validation. Use for plan creation, positioning analysis.
- If a model fails, the issue is usually the **prompt clarity** or **task scope**, not the model itself.

---

## Rule 5: Break Large Plans into Bounded Sessions

**Problem observed:** Multiple sessions attempted to implement an entire 12-session plan in one go, resulting in timeouts, partial completions, and abandoned context.

**Rule:**

- Limit each session to **2-3 concrete deliverables** maximum.
- After each session, commit or stash the changes before starting the next.
- Start each new session with: "The following work is already done: [list]. Now implement only: [next 2-3 items]."
- Never ask the model to "implement the entire plan" — it will overcommit and underdeliver.

---

## Rule 6: Validate Before Moving Forward

**Problem observed:** Multiple sessions rushed through implementation without running tests or builds, then discovered failures that required restarting.

**Rule:**

- After every batch of changes, run the quality gates before proceeding:
  ```bash
  pytest tests/ -x -q        # Tests pass
  ruff check codetrellis/     # Lint clean
  python3 -m build            # Build succeeds
  ```
- If validation fails, fix it in the current session — don't start a new one.
- The model should be instructed to "validate after each batch, not at the end."

---

## Rule 7: Always Provide State Context When Resuming

**Problem observed:** Sessions 6-11 (March 14) all asked variations of "read the plan and implement it" without specifying what was already done vs. what remained.

**Rule:**

- When continuing multi-session work, always include:
  1. What sessions/work is already complete
  2. What the current git state is (dirty worktree? uncommitted changes?)
  3. What specific items to work on next
- Reference the tracking document (e.g., `MASTER_IMPLEMENTATION_PROGRAM.md`) by specific session numbers.
- Example: "Sessions 1-5 are complete and committed. Session 6 (trust files) has partial work in the worktree. Complete Session 6 and 7 only."

---

## Rule 8: Use the MCP Tools Before Manual Exploration

**Problem observed:** Several sessions began with broad `find`, `grep`, and multiple `read_file` calls when CodeTrellis MCP tools could have provided the same context in one call.

**Rule:**

- Before any code exploration, call `search_matrix(query)` or `get_context_for_file(path)`.
- Before editing any file, call `get_context_for_file(path)` to understand its dependencies and types.
- These tools are already configured in `.vscode/mcp.json` — they should be the first call in every session.

---

## Rule 9: Don't Cancel Sessions Prematurely

**Problem observed:** 4 sessions were cancelled with "(no response / cancelled)" before the model could produce any output. Several more were cancelled while the model was mid-analysis.

**Rule:**

- Give the model at least 60 seconds to start responding, especially for complex tasks with many file reads.
- If the model is taking tool actions (reading files, running commands), don't interrupt — this is normal processing.
- If a session seems stuck after 2+ minutes with no visible progress, then consider intervention.

---

## Rule 10: Commit Frequently Between Sessions

**Problem observed:** On March 14, there were 12+ sessions in one day with accumulated uncommitted changes. Later sessions couldn't distinguish between "already done" and "in progress" work.

**Rule:**

- After each successful session, commit or stash changes with a descriptive message.
- Use conventional commits: `feat: implement Session 6 trust files`, `fix: resolve version inconsistency`
- This creates clear checkpoints and makes it easy to tell the next session what's already done.
- The `git stash` approach works for work-in-progress, but `git commit` on a branch is better for multi-session plans.

---

## Rule 11: For Multi-Agent Tasks, Specify the Coordination Model

**Problem observed:** Session 5 used a well-structured multi-agent prompt that worked. Other sessions did not specify coordination and got confused results.

**Rule:**

- When using ct-research, ct-implement, and ct-verify agents, always specify:
  1. Which agents to use
  2. What order (parallel or sequential)
  3. What to do with disagreements
  4. What the final deliverable format should be
- Template: "Research first, implement second, verify third. Reconcile disagreements by [priority rule]. Return one unified output."

---

## Rule 12: Version Must Come From One Place

**Problem observed:** Session 18 specifically dealt with "version not pointing to the correct version" — the classic single-source-of-truth violation.

**Rule:**

- `pyproject.toml` is the **only** place to set the version.
- `__init__.py` reads it via `importlib.metadata` — never edit it manually.
- If the CLI shows a wrong version, run `pip install -e .` to sync.
- Never hardcode version strings anywhere else in the codebase.

---

## Effective Patterns (Keep Doing These)

These patterns worked well in the analyzed sessions:

1. **Detailed implementation briefs with constraints** (Sessions 2, 12, 15, 21) — Long prompts with explicit operating rules, scope boundaries, and exit criteria produced the best results.

2. **Phase-based execution** (Session 2) — "Work phase by phase, verify each batch" is the right approach for this project.

3. **Role-based prompting** ("You are a senior Python release engineer") — Giving the model a specific role improved output quality for specialized tasks.

4. **Multi-agent orchestration** (Session 5) — Using ct-research + ct-implement + ct-verify for strategic tasks produced comprehensive results.

5. **Explicit "do not" constraints** — Listing what NOT to do (don't publish, don't force push, don't rewrite wholesale) prevented destructive actions.

6. **Structured PR review prompts** — The 8,334-char "Addressing PR Review Comments" prompt (2026-03-17) worked well by providing explicit review context, enabling focused multi-file changes in a single session.

---

## Model Usage Statistics (60 sessions)

| Model              | Sessions | Best For                          |
| ------------------ | -------- | --------------------------------- |
| Inline/unknown (?) | 38       | Quick completions, small edits    |
| claude-opus-4.6    | 15       | Complex multi-file implementation |
| gpt-5.4            | 5        | Strategic planning, documentation |
| claude-sonnet-4.6  | 2        | Targeted fixes, code review       |
