# MOTA: Matrix-Orchestrated Tool Agents — VS Code Extension Integration Plan

> **Status:** DRAFT → Multi-Agent Validation
> **Date:** 28 February 2026
> **Context:** This plan integrates the MOTA concept INTO the existing VS Code Extension
> (the Copilot Chat clone), as a **TypeScript-native subsystem (§5.27)** — NOT as a
> separate Python package.
> **Prerequisite:** The extension plan (26 subsystems, 8 phases) is the base.
> **Matrix:** CodeTrellis Matrix (Python) is consumed via MCP protocol, not embedded.

---

# ═══════════════════════════════════════════════════════════════
# SECTION A: THE PLAN (v1.0 — Draft for Review)
# ═══════════════════════════════════════════════════════════════

## 1. Executive Summary

### What's Changing

The existing extension plan (§5.1–§5.26) builds a Copilot Chat clone with 26 subsystems.
**This plan adds §5.27: MOTA — Matrix-Orchestrated Tool Agents**, which makes the
extension **aware of the CodeTrellis Matrix** and uses it to:

1. **Select the right agent persona** for each user request (deterministic, <10ms)
2. **Assemble precise context** from the Matrix (not dump everything)
3. **Choose the right tools** based on project structure (not LLM guessing)
4. **Verify outputs** automatically (type-check, lint, test)
5. **Guard tool permissions** at runtime (not just prompt-level)

### How It Fits

```
EXISTING EXTENSION PLAN (§5.1–§5.26)
┌─────────────────────────────────────────────────────────┐
│  §5.3 Chat Engine ←──── §5.27 MOTA orchestrates ────→ §5.5 Tool System  │
│  §5.4 Prompts    ←──── §5.27 MOTA assembles context                     │
│  §5.23 Agents    ←──── §5.27 MOTA provides personas                     │
│  §5.8 MCP        ←──── §5.27 MOTA consumes Matrix via MCP               │
│  §5.12 Telemetry ←──── §5.27 MOTA logs audit events                     │
└─────────────────────────────────────────────────────────┘
         ▲
         │ MCP Protocol (JSON-RPC)
         │
┌────────┴────────────────────────────────────────────────┐
│  CodeTrellis Matrix (Python CLI/MCP Server)             │
│  33 sections · 4053 IMPL_LOGIC snippets · 11 skills    │
│  Already exists — NO changes needed to Matrix           │
└─────────────────────────────────────────────────────────┘
```

### Key Insight: TypeScript-Native, Matrix via MCP

MOTA is **100% TypeScript** inside the extension. It talks to the Matrix through
the **existing MCP subsystem (§5.8)**. The Matrix stays Python. The extension
stays TypeScript. They communicate via MCP protocol — which BOTH already support.

```
Extension (TypeScript)          Matrix (Python)
┌──────────────┐                ┌──────────────┐
│  MOTA §5.27  │ ──MCP call──→ │  MCP Server   │
│              │ ←─response──  │  (5 tools)    │
│  - Intent    │                │  - search     │
│  - Personas  │                │  - section    │
│  - Guard     │                │  - context    │
│  - Verify    │                │  - skills     │
│  - Audit     │                │  - stats      │
└──────────────┘                └──────────────┘
```

---

## 2. Architecture

### 2.1 MOTA as Subsystem §5.27

MOTA is a new subsystem alongside the existing 26. It follows all existing patterns:
- **DI Container:** All MOTA services registered via `ServiceIdentifier<T>`
- **Event-Driven:** `Event<T>` emitters for state changes
- **Disposable:** `IDisposable` lifecycle on all services
- **Interface-first:** Every service has an `I*` interface + implementation

### 2.2 System Flow (TypeScript)

```
User Message (from §5.3 Chat Engine)
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              §5.27 MOTA Orchestrator (TypeScript)        │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Input    │  │   Intent   │  │   Agent    │        │
│  │ Sanitizer  │→ │ Classifier │→ │  Factory   │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                        │                │
│                  ┌─────────────────────┘                │
│                  ▼                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Context   │  │   Tool     │  │  Tool      │        │
│  │ Assembler  │← │  Selector  │← │  Guard     │        │
│  │            │  └────────────┘  └────────────┘        │
│  │  (calls    │                                         │
│  │   MCP to   │  Powered by: CodeTrellis Matrix         │
│  │   Matrix)  │  via §5.8 MCP Client                    │
│  └────────────┘                                         │
└──────────────────────┬──────────────────────────────────┘
                       │ MOTASession
                       ▼
              ┌──────────────────┐
              │  §5.3 Chat       │
              │  Engine executes │     ┌──────────────┐
              │  with constrained│────→│  §5.12       │
              │  context + tools │     │  Telemetry   │
              └────────┬─────────┘     │  + AuditLog  │
                       │ output        └──────────────┘
                       ▼
              ┌──────────────────┐
              │  Verification    │
              │  Engine          │
              │  (deterministic) │
              └────────┬─────────┘
                       │
                ┌──────┴──────┐
             ✅ Pass       ❌ Fail → Feedback Loop (max 5)
```

### 2.3 Core TypeScript Interfaces

```typescript
// ═══════════════════════════════════════════
// src/extension/mota/types.ts
// ═══════════════════════════════════════════

// ── Enums ──────────────────────────────────

export const enum PersonaType {
  // Phase 1 (3 personas)
  Implementor = 'implementor',
  Reviewer = 'reviewer',
  Planner = 'planner',
  // Phase 2 (3 more)
  Debugger = 'debugger',
  Tester = 'tester',
  Architect = 'architect',
}

export const enum SessionState {
  Initializing = 'initializing',
  Executing = 'executing',
  Verifying = 'verifying',
  Retrying = 'retrying',
  Complete = 'complete',
  Failed = 'failed',
}

export const enum FailureAction {
  Retry = 'retry',
  Escalate = 'escalate',
  Abort = 'abort',
}

// ── Interfaces ─────────────────────────────

export interface ITokenBudgetConfig {
  systemPrompt: number;    // default 2000
  matrixContext: number;    // default 8000
  conversation: number;    // default 4000
  toolResults: number;     // default 6000
}

export interface IVerificationStrategy {
  steps: string[];               // ['typeCheck', 'lint', 'test']
  requiredPassCount: 'ALL' | 'ANY' | number;
  maxRetries: number;
  onFailure: FailureAction;
  languages: string[];           // ['typescript'] for this extension
}

export interface IAgentBlueprint {
  // From existing Matrix Skill
  name: string;
  description: string;
  trigger: string;
  contextSections: string[];     // Matrix sections to load via MCP
  instructions: string;
  category: string;
  priority: number;
  // MOTA additions
  persona: PersonaType;
  toolsAllowed: string[];        // tool names from §5.5
  toolsDenied: string[];
  verification: IVerificationStrategy;
  tokenBudget: ITokenBudgetConfig;
  maxIterations: number;
  slashCommand?: string;         // '/implement', '/review', '/plan'
}

export interface IToolCall {
  toolName: string;
  arguments: Record<string, unknown>;
  result?: string;
  wasAllowed: boolean;
  timestamp: number;
}

export interface IAgentIteration {
  iterationNumber: number;
  toolCalls: IToolCall[];
  llmResponse: string;
  verificationResult?: IVerificationResult;
  tokenUsage: number;
}

export interface IVerificationResult {
  passed: boolean;
  steps: {
    name: string;
    passed: boolean;
    errors: number;
    warnings: number;
    details: string;
  }[];
}

export interface IMOTASession {
  blueprint: IAgentBlueprint;
  state: SessionState;
  iterations: IAgentIteration[];
  totalTokens: number;
  startedAt?: number;
  completedAt?: number;
  auditEvents: IMOTAAuditEvent[];
}

export interface IMOTAAuditEvent {
  timestamp: number;
  eventType: 'intent' | 'blueprint' | 'tool_call' | 'tool_denied' |
             'verification' | 'retry' | 'complete' | 'fail' |
             'context_assembled' | 'matrix_freshness';
  details: Record<string, unknown>;
  sessionId: string;
  userMessageHash: string;    // SHA-256 first 12 chars
}

export interface IMatrixFreshness {
  isFresh: boolean;
  staleFiles: string[];
  matrixAgeSeconds: number;
  recommendation: 'ok' | 'incremental' | 'rescan';
}

export interface IMatrixContext {
  sections: Record<string, string>;   // section name → content
  tokenCount: number;
  truncated: boolean;
  snippets: string[];                 // filtered IMPL_LOGIC
}
```

### 2.4 Service Interfaces (DI-Ready)

```typescript
// ═══════════════════════════════════════════
// src/extension/mota/services.ts
// ═══════════════════════════════════════════

import { createDecorator } from '../../platform/instantiation/instantiation';

// ── Service Identifiers ────────────────────

export const IMOTAService = createDecorator<IMOTAService>('motaService');
export const IMOTAIntentClassifier = createDecorator<IMOTAIntentClassifier>('motaIntentClassifier');
export const IMOTABlueprintRegistry = createDecorator<IMOTABlueprintRegistry>('motaBlueprintRegistry');
export const IMOTAToolGuard = createDecorator<IMOTAToolGuard>('motaToolGuard');
export const IMOTAContextAssembler = createDecorator<IMOTAContextAssembler>('motaContextAssembler');
export const IMOTAVerificationEngine = createDecorator<IMOTAVerificationEngine>('motaVerificationEngine');
export const IMOTAAuditLog = createDecorator<IMOTAAuditLog>('motaAuditLog');
export const IMOTASessionManager = createDecorator<IMOTASessionManager>('motaSessionManager');

// ── Service Interfaces ─────────────────────

export interface IMOTAService {
  _serviceBrand: undefined;

  /** Main entry: user message → orchestrated agent session */
  orchestrate(message: string): Promise<IMOTASession>;

  /** Preview what MOTA would do without executing */
  getBlueprint(message: string): Promise<IAgentBlueprint>;

  /** Check if MOTA is available (Matrix MCP server connected) */
  readonly isAvailable: boolean;

  /** Feature flag */
  readonly isEnabled: boolean;

  /** Events */
  readonly onDidSessionStart: Event<IMOTASession>;
  readonly onDidSessionComplete: Event<IMOTASession>;
  readonly onDidSessionFail: Event<IMOTASession>;
}

export interface IMOTAIntentClassifier {
  _serviceBrand: undefined;

  /** Classify user message → intent + confidence */
  classify(message: string): IIntentResult;

  /** Support slash command override */
  classifyWithOverride(message: string, slashCommand?: string): IIntentResult;
}

export interface IIntentResult {
  intent: string;
  confidence: number;
  persona: PersonaType;
  slashCommandUsed?: string;
}

export interface IMOTABlueprintRegistry {
  _serviceBrand: undefined;

  /** Get blueprint for intent */
  getBlueprint(intent: string): IAgentBlueprint;

  /** List all registered blueprints */
  listBlueprints(): IAgentBlueprint[];

  /** Default fallback blueprint */
  getDefaultBlueprint(): IAgentBlueprint;

  /** Register blueprints from Matrix skills (via MCP) */
  loadFromMatrix(): Promise<void>;
}

export interface IMOTAToolGuard {
  _serviceBrand: undefined;

  /** Check if tool can be executed by current persona */
  canExecute(toolName: string, session: IMOTASession): boolean;

  /** Get all denied tool attempts for a session */
  getDeniedAttempts(sessionId: string): IToolCall[];
}

export interface IMOTAContextAssembler {
  _serviceBrand: undefined;

  /** Assemble context from Matrix via MCP */
  assemble(blueprint: IAgentBlueprint, userMessage: string): Promise<IMatrixContext>;

  /** Check matrix freshness */
  checkFreshness(): Promise<IMatrixFreshness>;
}

export interface IMOTAVerificationEngine {
  _serviceBrand: undefined;

  /** Run verification on agent output */
  verify(filePaths: string[], strategy: IVerificationStrategy): Promise<IVerificationResult>;
}

export interface IMOTAAuditLog {
  _serviceBrand: undefined;

  /** Log an audit event */
  log(event: IMOTAAuditEvent): void;

  /** Get audit trail for session */
  getTrail(sessionId: string): IMOTAAuditEvent[];

  /** Export all events */
  export(): IMOTAAuditEvent[];
}

export interface IMOTASessionManager {
  _serviceBrand: undefined;

  /** Create a new session from blueprint */
  createSession(blueprint: IAgentBlueprint): IMOTASession;

  /** Transition session state */
  transition(sessionId: string, newState: SessionState): void;

  /** Add iteration to session */
  addIteration(sessionId: string, iteration: IAgentIteration): void;

  /** Get active session */
  getActiveSession(): IMOTASession | undefined;
}
```

### 2.5 Integration Points with Existing Subsystems

| Existing Subsystem | Integration | How MOTA Uses It |
|---|---|---|
| **§5.3 Chat Engine** | `IChatSessionService` | MOTA hooks into the chat request handler. Before the chat engine processes a message, MOTA classifies intent and assembles context. |
| **§5.4 Prompts** | `PromptRenderer` | MOTA generates persona-specific system prompts using the existing JSX prompt system. Token budgets from IAgentBlueprint feed into the existing token allocator. |
| **§5.5 Tool System** | `IToolDefinition`, tool hooks | MOTA's ToolGuard registers as a **pre-tool-use hook** (`IPreToolUseHookResult`). When the LLM tries to call a tool, ToolGuard checks permissions before execution. |
| **§5.8 MCP** | `IMcpService` | MOTA calls the CodeTrellis Matrix MCP server's 5 tools: `search_matrix`, `get_section`, `get_context_for_file`, `get_skills`, `get_cache_stats`. This is how context flows from Python → TypeScript. |
| **§5.12 Telemetry** | `ITelemetryReporter` | MOTA audit events are reported as telemetry events. Intent accuracy, persona selection, tool denials, verification results — all tracked. |
| **§5.23 Agents** | `IChatAgentService` | MOTA personas register as custom agent providers. 🔧 Implementor, 🔍 Reviewer, 📋 Planner are agent providers with constrained capabilities. |
| **§5.25 Slash Commands** | `IClaudeSlashCommandService` | MOTA registers `/implement`, `/review`, `/plan`, `/auto` as slash commands. Each forces a specific persona. |

### 2.6 Agent Personas

**Phase 1 (3 personas):**

| Persona | Trigger Patterns | Matrix Sections (via MCP) | Extension Tools Allowed (§5.5) | Tools Denied | Verification |
|---------|-----------------|---------------------------|-------------------------------|-------------|-------------|
| 🔧 **Implementor** | "add", "create", "implement", "fix", "update" | TYPES, ROUTES, IMPL_LOGIC, BEST_PRACTICES, RUNBOOK | readFile, editFile, replaceString, createFile, findTextInFiles, runTerminalCommand, listDir | deleteFile (project-level), gitPush, gitForce | tsc + eslint + vitest (ALL pass) |
| 🔍 **Reviewer** | "review", "check", "audit" | BEST_PRACTICES, SECURITY, TYPES, IMPL_LOGIC | readFile, findTextInFiles, semanticSearch, listDir | ALL write/edit tools, runTerminalCommand | best-practice checklist score |
| 📋 **Planner** | "plan", "design", "estimate", "how should" | OVERVIEW, PROGRESS, ACTIONABLE, BUSINESS_DOMAIN, TYPES | readFile, findTextInFiles, semanticSearch, listDir | ALL write/edit tools, runTerminalCommand | feasibility score |

**Phase 2 (3 more):**

| Persona | Trigger Patterns | Matrix Sections |
|---------|-----------------|-----------------|
| 🐛 **Debugger** | "debug", "error", stack traces | ERROR_HANDLING, IMPL_LOGIC, TYPES |
| 🧪 **Tester** | "test", "coverage", "spec" | TYPES, IMPL_LOGIC, RUNBOOK |
| 🏗️ **Architect** | "architecture", "restructure" | OVERVIEW, TYPES, ROUTES, INFRASTRUCTURE |

---

## 3. File Structure (Extension-Side Only)

```
src/extension/mota/                    # §5.27 — MOTA Subsystem
├── motaService.ts                     # IMOTAService — main orchestrator
├── intentClassifier.ts                # IMOTAIntentClassifier — regex + keyword
├── blueprintRegistry.ts               # IMOTABlueprintRegistry — skill → blueprint
├── toolGuard.ts                       # IMOTAToolGuard — runtime permission hook
├── contextAssembler.ts                # IMOTAContextAssembler — MCP → context
├── verificationEngine.ts              # IMOTAVerificationEngine — tsc/eslint/vitest
├── auditLog.ts                        # IMOTAAuditLog — structured event logging
├── sessionManager.ts                  # IMOTASessionManager — session lifecycle
├── inputSanitizer.ts                  # Prompt injection detection
├── promptElements/                    # JSX prompt elements for personas
│   ├── implementorPrompt.tsx          # 🔧 Implementor system prompt
│   ├── reviewerPrompt.tsx             # 🔍 Reviewer system prompt
│   ├── plannerPrompt.tsx              # 📋 Planner system prompt
│   └── matrixContextPrompt.tsx        # Matrix context injection prompt element
├── participants/                      # Chat participant providers
│   ├── motaParticipant.ts             # Main MOTA chat participant
│   └── personaBadge.ts               # UI badge rendering
├── slashCommands/                     # Slash command handlers
│   ├── implementCommand.ts            # /implement
│   ├── reviewCommand.ts               # /review
│   ├── planCommand.ts                 # /plan
│   └── autoCommand.ts                 # /auto (default)
├── types.ts                           # All interfaces & enums
└── services.ts                        # Service identifiers & DI registration

test/unit/mota/                        # Tests
├── intentClassifier.test.ts
├── blueprintRegistry.test.ts
├── toolGuard.test.ts
├── contextAssembler.test.ts
├── verificationEngine.test.ts
├── auditLog.test.ts
├── sessionManager.test.ts
├── inputSanitizer.test.ts
├── motaService.test.ts                # Integration tests
└── fixtures/
    ├── testMessages.json              # 200 labeled messages
    └── mockMatrixResponses.json       # Mock MCP responses
```

---

## 4. DI Registration

```typescript
// In src/extension/services.ts — add to existing registration

// Layer 5: MOTA (depends on Layer 2 MCP, Layer 3 Chat, Layer 4 Tools)
builder.register(IMOTAAuditLog, MOTAAuditLog);
builder.register(IMOTAIntentClassifier, MOTAIntentClassifier);
builder.register(IMOTABlueprintRegistry, MOTABlueprintRegistry);
builder.register(IMOTAToolGuard, MOTAToolGuard);
builder.register(IMOTAContextAssembler, MOTAContextAssembler);
builder.register(IMOTAVerificationEngine, MOTAVerificationEngine);
builder.register(IMOTASessionManager, MOTASessionManager);
builder.register(IMOTAService, MOTAService);  // Last — depends on all above
```

---

## 5. How MOTA Consumes Matrix (MCP Flow)

```typescript
// Inside MOTAContextAssembler — calling Matrix via existing MCP subsystem

class MOTAContextAssembler implements IMOTAContextAssembler {
  constructor(
    @IMcpService private readonly mcpService: IMcpService,
    @IMOTAAuditLog private readonly auditLog: IMOTAAuditLog,
  ) {}

  async assemble(blueprint: IAgentBlueprint, userMessage: string): Promise<IMatrixContext> {
    const sections: Record<string, string> = {};
    let totalTokens = 0;

    // 1. Call Matrix MCP server for each required section
    for (const sectionName of blueprint.contextSections) {
      const result = await this.mcpService.callTool(
        'codetrellis',              // MCP server name
        'get_section',              // MCP tool
        { name: sectionName }       // arguments
      );
      sections[sectionName] = result.content;
      totalTokens += this.estimateTokens(result.content);
    }

    // 2. Get file-specific context if user mentions files
    const mentionedFiles = this.extractFilePaths(userMessage);
    if (mentionedFiles.length > 0) {
      for (const filePath of mentionedFiles) {
        const result = await this.mcpService.callTool(
          'codetrellis',
          'get_context_for_file',
          { file_path: filePath }
        );
        sections[`file:${filePath}`] = result.content;
        totalTokens += this.estimateTokens(result.content);
      }
    }

    // 3. Truncate if over budget
    const truncated = totalTokens > blueprint.tokenBudget.matrixContext;
    if (truncated) {
      // Priority-based truncation: keep high-priority sections
      this.truncateToFit(sections, blueprint.tokenBudget.matrixContext);
    }

    this.auditLog.log({
      timestamp: Date.now(),
      eventType: 'context_assembled',
      details: {
        sections: Object.keys(sections).length,
        tokens: totalTokens,
        truncated,
      },
      sessionId: '', // filled by caller
      userMessageHash: this.hashMessage(userMessage),
    });

    return { sections, tokenCount: totalTokens, truncated, snippets: [] };
  }
}
```

---

## 6. Where MOTA Fits in the Extension Phase Plan

MOTA doesn't replace any existing phase. It's an **addition** that can be built
**after Phase 3 (Tool System)** because it depends on:
- §5.3 Chat Engine (Phase 2) ✅
- §5.4 Prompts (Phase 2) ✅
- §5.5 Tool System (Phase 3) ✅
- §5.8 MCP (Phase 6) ⚠️ — needs basic MCP client first

**Option A: Build MOTA as Phase 6.5 (after MCP)**
- Clean dependency order
- Full MCP client available
- Delay: starts at week 26

**Option B: Build MOTA in parallel with Phase 4-6, stub MCP calls**
- Faster integration
- Mock MCP responses during development
- Wire to real MCP when §5.8 is ready
- Can start at week 11 (after Phase 3)

**Recommended: Option B** — Build MOTA with mock MCP, wire later.

### Updated Phase Timeline

| Phase | Duration | Subsystems | MOTA Work |
|-------|----------|-----------|-----------|
| 0: Foundation | 3 weeks | §5.15 Observable, DI | — |
| 1: Auth & LLM | 3 weeks | §5.1, §5.2 | — |
| 2: Basic Chat | 4 weeks | §5.3, §5.4 | — |
| 3: Tool System | 5 weeks | §5.5 | — |
| **3.5: MOTA Core** | **3 weeks** | **§5.27 (partial)** | **Intent + Blueprint + Guard + Audit (mock MCP)** |
| 4: Completions | 4 weeks | §5.6 | — |
| 5: Search | 4 weeks | §5.7 | — |
| 6: MCP | 3 weeks | §5.8 | **Wire MOTA to real MCP** |
| **6.5: MOTA Full** | **3 weeks** | **§5.27 (complete)** | **Context + Verify + Personas + Slash commands** |
| 7: Advanced | 10 weeks | §5.9–§5.26 | — |
| 8: Polish | 4 weeks | — | MOTA analytics + optimization |
| **Total** | **~46 weeks** | | **6 weeks MOTA** |

---

## 7. Security & Trust (Same as MOTA v2, but TypeScript)

### 7.1 ToolGuard as Pre-Tool Hook

```typescript
// Registers into the existing §5.5 tool hook system

class MOTAToolGuard implements IMOTAToolGuard, IPreToolUseHook {
  canExecute(toolName: string, session: IMOTASession): boolean {
    const { toolsAllowed, toolsDenied } = session.blueprint;

    // Deny list takes priority
    if (toolsDenied.includes(toolName)) {
      this.auditLog.log({
        eventType: 'tool_denied',
        details: { tool: toolName, reason: 'in_deny_list', persona: session.blueprint.persona },
        // ...
      });
      return false;
    }

    // Allow list enforcement
    if (toolsAllowed.length > 0 && !toolsAllowed.includes(toolName)) {
      this.auditLog.log({
        eventType: 'tool_denied',
        details: { tool: toolName, reason: 'not_in_allow_list', persona: session.blueprint.persona },
        // ...
      });
      return false;
    }

    return true;
  }
}
```

### 7.2 Input Sanitization

Same suspicious patterns as MOTA v2, implemented in TypeScript:
- Prompt injection detection
- Persona override attempts
- System prefix injection

---

## 8. UX (Leveraging Existing Extension UI)

### 8.1 Progressive Disclosure (3 Levels)

- **Level 1 (Default):** MOTA works silently. Better results, no UI change.
- **Level 2 (Setting: `codetrellis.mota.showPersona`):** Persona badge (🔧/🔍/📋) + verification results in chat.
- **Level 3 (Setting: `codetrellis.mota.showTrace`):** Full orchestration trace: intent, sections loaded, tokens, audit log.

### 8.2 Slash Commands (Using §5.25)

| Command | PersonaType | Registration |
|---------|------------|-------------|
| `/implement` | Implementor | Via §5.25 slash command system |
| `/review` | Reviewer | Via §5.25 slash command system |
| `/plan` | Planner | Via §5.25 slash command system |
| `/auto` | Auto-detect | Default behavior |

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Intent accuracy | >90% | 200 labeled test messages |
| Context precision | >80% | Human evaluation: relevant sections selected |
| Token savings | 40% less | vs no-MOTA baseline (dump everything) |
| Verification catch rate | >70% | Bugs caught by auto-verify |
| Tool denial accuracy | 100% | ToolGuard blocks ALL denied tools |
| First-attempt success | >60% | Tasks completed without retry |

---

## 10. Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| MCP server not running | No matrix context | Graceful fallback: MOTA disabled, vanilla chat behavior |
| Matrix stale | Wrong context | Freshness check via MCP `get_cache_stats` |
| Intent misclassification | Wrong persona | Fallback to Implementor; slash command override |
| Prompt injection | Malicious tool use | Input sanitizer + ToolGuard (runtime, not just prompt) |
| Extension bundle size | Slower load | MOTA is lazy-loaded only when Matrix MCP server detected |
| Circular dependency | DI failure | MOTA depends on MCP/Chat/Tools, never the reverse |

---

# ═══════════════════════════════════════════════════════════════
# SECTION B: ROUND 1 — INDEPENDENT AGENT REVIEWS
# ═══════════════════════════════════════════════════════════════

---

## 🔴 AGENT 1: THE SKEPTIC

**Core question:** "Is building MOTA as §5.27 inside the extension realistic?"

### Verdict: CONDITIONAL PASS

### ✅ Agreements
1. **TypeScript-native is correct.** Building MOTA in Python and bridging to TS would be a maintenance nightmare. Two codebases, two test suites, two deployment flows. TS-native inside the extension is the only sane choice.
2. **MCP as the bridge is smart.** The Matrix stays Python, the extension stays TS, and MCP is the protocol both already support. No new protocol needed.
3. **DI integration follows existing patterns.** Using `ServiceIdentifier<T>`, `_serviceBrand`, `IDisposable` — this will feel native to the codebase.

### ⚠️ Concerns
1. **Phase 3.5 timing is aggressive.** After Phase 3 (Tool System), the team will want to move to completions (Phase 4), not detour to MOTA. MOTA should be parallel work, not blocking.
2. **200 labeled test messages is a lot of manual work.** Who creates these? If the AI creates them, they'll be biased toward patterns the AI already understands.
3. **6 weeks total for MOTA seems right,** but only if the person building it is the same person who built the extension (context familiarity).

### ❌ Won't Work
1. **"Wire to real MCP when §5.8 is ready" is risky.** Mock MCP and real MCP always diverge. Build a thin MCP adapter from day 1, even if the backend is mock data. When real MCP arrives, just swap the backend.

### 💡 Alternatives
1. **Start with JUST ToolGuard + Intent.** Don't build the full MOTA pipeline first. Get ToolGuard into the tool hooks immediately — it has standalone value even without Matrix context.
2. **Hardcode 3 blueprints first,** load from Matrix skills later. Don't block on MCP integration.

---

## 🟢 AGENT 2: THE ARCHITECT

**Core question:** "Are the TypeScript abstractions right? Does this compose with §5.1–§5.26?"

### Verdict: PASS WITH REVISIONS

### ✅ Agreements
1. **Interface-first design is excellent.** Every MOTA service has an `I*` interface. This means any service can be swapped (mock in tests, null when disabled).
2. **ToolGuard as `IPreToolUseHook` is the perfect integration.** It plugs into the existing §5.5 hook system. Zero change to the tool system itself.
3. **DI registration order is correct.** MOTA is Layer 5, depends on Layers 2-4. No circular dependencies.

### ⚠️ Concerns
1. **`IMOTAService.orchestrate()` does too much.** It should be broken into: `classifyIntent()`, `selectBlueprint()`, `assembleContext()`, `execute()`, `verify()`. The caller (chat handler) should be able to call these individually.
2. **Missing: `NullMOTAService`.** When MOTA is disabled (feature flag off, or no Matrix MCP server), every consumer needs a null implementation. This pattern exists throughout the codebase (see `NullMcpService`, `NullExperimentationService`).
3. **Missing: `IMOTAFeedbackLoop`.** The verification → retry flow needs its own service interface, not embedded in `MOTAService`.

### ❌ Won't Work
1. **`IMatrixContext.sections` as `Record<string, string>` is too loose.** Define specific section types. The Matrix has 33 named sections — create a union type for section names.

### 💡 Alternatives
1. Add `type MatrixSectionName = 'PYTHON_TYPES' | 'ROUTES_SEMANTIC' | 'IMPLEMENTATION_LOGIC' | ... ;`
2. Add `NullMOTAService` that returns no-op for all methods when MOTA is disabled.
3. Extract `IMOTAFeedbackLoop` as a separate service.

---

## 🔵 AGENT 3: THE USER ADVOCATE

**Core question:** "Will this make the extension noticeably better for users?"

### Verdict: PASS

### ✅ Agreements
1. **Progressive disclosure is exactly right.** Level 1 = invisible improvement. Users who don't care about MOTA never see it. Users who want control get Level 2/3.
2. **Slash commands are intuitive.** `/implement`, `/review`, `/plan` — clear, memorable, discoverable.
3. **Verification results in chat** are a killer feature. Seeing "✅ Type check: 0 errors, ✅ Lint: 0 warnings, ✅ Tests: 5/5" after every task builds trust.

### ⚠️ Concerns
1. **What happens when Matrix MCP server isn't running?** 90% of users won't have the Matrix installed. MOTA must degrade gracefully — not show errors, just work like vanilla chat.
2. **"Persona badge" might confuse casual users.** Why is there a 🔧 next to the AI's name? Add a tooltip and a "What's this?" link.

### ❌ Won't Work
Nothing — the UX design is solid.

### 💡 Alternatives
1. **Auto-detect Matrix MCP server** on extension activation. If found, enable MOTA silently. If not, never show MOTA UI elements.
2. Add onboarding: first time MOTA activates, show a notification: "CodeTrellis Matrix detected! AI now uses your project's patterns for better results. [Learn More]"

---

## 🟡 AGENT 4: THE BUSINESS STRATEGIST

**Core question:** "Does MOTA integration create competitive advantage?"

### Verdict: STRONG PASS

### ✅ Agreements
1. **This is THE differentiator.** No other AI coding extension has a pre-computed project matrix feeding context deterministically. Cursor, Continue, Cline — all dump context or let the LLM guess. MOTA + Matrix = unique.
2. **MCP as the protocol is a platform play.** Any MCP client (Claude Desktop, Cursor, etc.) can use the Matrix. But ONLY CodeTrellis Chat gets the MOTA orchestration layer.
3. **The 10x moment demo still works** — and now it's even cleaner because it's one integrated extension, not Python + TS glued together.

### ⚠️ Concerns
1. **"Requires CodeTrellis Matrix installed" is a friction point.** Consider bundling a lightweight Matrix scanner IN the extension (TypeScript port of the core scanner) for zero-config experience.
2. **The naming needs work.** Users see "CodeTrellis Chat" extension. They install "CodeTrellis Matrix" CLI. They use "MOTA" internally. Too many names. Simplify to ONE brand.

### ❌ Won't Work
Nothing blocking.

### 💡 Alternatives
1. **Phase 1: Matrix via MCP (external).** Phase 2: Bundled lightweight TypeScript scanner (built-in). This way MOTA works even without the Python Matrix installed.
2. Unified brand: "CodeTrellis" = everything. The extension IS CodeTrellis. The Matrix IS CodeTrellis. MOTA is invisible.

---

## 🟣 AGENT 5: THE MATRIX EXPERT

**Core question:** "Can the existing Matrix infrastructure support this TypeScript integration?"

### Verdict: PASS WITH CHANGES

### ✅ Agreements
1. **MCP server already has the 5 tools MOTA needs.** `search_matrix`, `get_section`, `get_context_for_file`, `get_skills`, `get_cache_stats` — these map 1:1 to MOTA's needs.
2. **11 auto-generated skills map directly to AgentBlueprints.** The skill → blueprint conversion is straightforward.
3. **JIT context system already does file → section mapping.** MOTA's ContextAssembler just needs to call `get_context_for_file` — the logic exists.

### ⚠️ Concerns
1. **MCP call latency.** Each `get_section` call is a JSON-RPC round-trip. If MOTA needs 5 sections, that's 5 round-trips. Need a **batch API**: `get_sections(names: string[]) → Record<string, string>`.
2. **IMPL_LOGIC filtering happens server-side in Python, but MOTA needs it client-side in TS.** Either: (a) add a `get_filtered_logic(query, max)` MCP tool, or (b) port the filter to TS.
3. **Matrix freshness check** needs the `get_cache_stats` tool to return file modification times, not just cache stats.

### ❌ Won't Work
1. **Calling MCP 5 times per user message** is too slow for <10ms intent classification. Solution: cache Matrix sections locally in the extension after first load. Only refresh when `get_cache_stats` says stale.

### 💡 Alternatives
1. **Add `get_sections` (batch) MCP tool** to the Python MCP server — one call returns multiple sections.
2. **Add `get_filtered_logic(query, max_snippets)` MCP tool** — filter IMPL_LOGIC server-side.
3. **Cache Matrix sections in extension memory** with TTL. Only re-fetch when stale.

---

## 🟠 AGENT 6: THE SECURITY & RELIABILITY AGENT

**Core question:** "Is the TypeScript ToolGuard implementation bulletproof?"

### Verdict: CONDITIONAL PASS

### ✅ Agreements
1. **ToolGuard as `IPreToolUseHook` is the right integration.** It's at the middleware level, before tool execution. Cannot be bypassed by prompt injection.
2. **Audit logging with message hashing** protects user privacy while maintaining debuggability.
3. **Input sanitization** catches the obvious prompt injection patterns.

### ⚠️ Concerns
1. **ToolGuard must be synchronous.** If `canExecute()` is async (awaiting MCP), a race condition could allow a tool call before guard responds. Ensure ToolGuard uses locally cached permissions, never MCP calls.
2. **The deny list is static per blueprint.** What about dynamic denials? E.g., deny `deleteFile` for files outside the workspace. Need path-based guards too.
3. **Audit log persistence.** In-memory only = lost on extension reload. Should persist to extension global storage or a local file.

### ❌ Won't Work
1. **No rate limiting on MOTA sessions.** If an agent loops (retry → fail → retry), it burns tokens. Add: max tokens per session, circuit breaker after N failures.

### 💡 Alternatives
1. Add `IToolGuardRule` interface for composable rules (deny-list rule, path-scope rule, rate-limit rule).
2. Persist audit log to `context.globalState` or a local SQLite (you already have SQLite for embeddings in §5.7).
3. Add circuit breaker: after 3 consecutive failed verifications, ESCALATE to user instead of retrying.

---

# ═══════════════════════════════════════════════════════════════
# ROUND 1 SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════

| Agent | Verdict | Key Demand |
|-------|---------|-----------|
| 🔴 Skeptic | CONDITIONAL PASS | Start with ToolGuard + Intent only. Hardcode blueprints. |
| 🟢 Architect | PASS w/REVISIONS | Add NullMOTAService. Extract FeedbackLoop. Type section names. |
| 🔵 User Advocate | PASS | Auto-detect Matrix. Graceful degradation. Onboarding notification. |
| 🟡 Strategist | STRONG PASS | Consider bundled TS scanner for zero-config. Unify brand. |
| 🟣 Matrix Expert | PASS w/CHANGES | Batch MCP API. Cache sections locally. Server-side IMPL_LOGIC filter. |
| 🟠 Security | CONDITIONAL PASS | Sync ToolGuard. Path-based guards. Persist audit. Circuit breaker. |

### Unanimous Agreements (LOCKED ✅)
1. **MOTA must be 100% TypeScript** inside the extension. No Python in the extension.
2. **Matrix communication via MCP** (existing protocol, existing tools).
3. **ToolGuard as `IPreToolUseHook`** — middleware integration with §5.5.
4. **Progressive disclosure** (3 levels) for UX.
5. **DI pattern** (`ServiceIdentifier<T>`, `_serviceBrand`, `NullService`) for all MOTA services.

### Majority Agreements (4+ agents)
1. **Cache Matrix sections locally** in the extension (5/6 — all except User Advocate who doesn't care about implementation).
2. **Start with hardcoded blueprints,** load from Matrix skills later (4/6 — Skeptic, Architect, Matrix Expert, Security).
3. **Batch MCP API needed** for performance (4/6 — Skeptic, Architect, Matrix Expert, Security).
4. **Audit log should persist** beyond memory (4/6 — Architect, Strategist, Matrix Expert, Security).

### Disagreements (FLAGGED for Round 2)
1. **When to build MOTA:** Skeptic says "after Phase 3, just ToolGuard." Strategist says "ASAP for differentiation." Architect says "after Phase 6 (MCP ready)."
2. **Bundled TS scanner:** Strategist wants it for zero-config. Matrix Expert says "over-engineering, MCP is enough." Skeptic says "scope creep."
3. **ToolGuard complexity:** Security wants composable rules (path-scope, rate-limit). Skeptic says "just allow/deny lists, don't over-engineer Phase 1."

---

# ═══════════════════════════════════════════════════════════════
# SECTION C: ROUND 2 — CROSS-AGENT DEBATE
# ═══════════════════════════════════════════════════════════════

---

## DEBATE 1: When to Build MOTA

### 🔴 Skeptic's Position:
"Build MOTA core (ToolGuard + Intent) as Phase 3.5 after Tools are done. Mock MCP.
Don't block on Phase 6 MCP. But ONLY ToolGuard + Intent — not the full pipeline."

### 🟡 Strategist's Rebuttal:
"If we wait, competitors ship first. The demo needs to work by Phase 3.5. But I agree
we can start with mocked Matrix data."

### 🟢 Architect's Counter:
"I agree with Phase 3.5 timing, but we need proper interfaces from day 1. Even with
mock MCP, the `IMOTAContextAssembler` interface should exist so the real MCP swaps in
cleanly at Phase 6."

### Other Agents:
- 🟣 Matrix Expert: "Phase 3.5 is fine. I'll prepare a `mock-matrix.json` fixture with
  representative section data. The TS code won't know it's mock vs real."
- 🟠 Security: "ToolGuard MUST be Phase 3.5. Intent classifier can wait. Guard has
  standalone value."

### 🤝 RESOLUTION:
**Phase 3.5 (after Tool System, week 16-18):** Build ToolGuard + Intent + Blueprints + Audit.
Use mock Matrix data (static JSON). All interfaces defined properly.

**Phase 6.5 (after MCP, week 27-29):** Wire to real MCP. Add ContextAssembler + Verification +
FeedbackLoop + Personas + Slash commands.

**Total: 6 weeks MOTA across two chunks.** All 6 agents approve.

---

## DEBATE 2: Bundled TypeScript Scanner

### 🟡 Strategist's Position:
"Users shouldn't need to install a separate Python CLI. Bundle a lightweight TS scanner
inside the extension for zero-config experience."

### 🟣 Matrix Expert's Rebuttal:
"The Matrix scanner is 80+ files, 40+ language parsers, 774 files scanned. You cannot
port that to TypeScript. The value of the Matrix IS the Python analysis depth."

### 🔴 Skeptic's Support for Matrix Expert:
"This is textbook scope creep. We'd be building a second Matrix in TypeScript. That's
a 6-month project, not a feature toggle. Kill this idea."

### 🔵 User Advocate Compromise:
"What if we bundle just a TINY scanner that produces 3 sections (TYPES, ROUTES, OVERVIEW)
from TypeScript files only? Good enough for 'zero-config' demo. Full Matrix for depth."

### 🟢 Architect:
"I like the compromise, but not for Phase 1. Phase 4+ at best. For now, auto-detect
Matrix MCP server and show onboarding instructions if not found."

### 🤝 RESOLUTION:
**Phase 1 (now):** NO bundled scanner. Matrix via MCP only. Auto-detect + onboarding
notification if Matrix not found.

**Future (post-launch):** MAYBE a lightweight TS-only scanner as a fallback. Not in this plan.

All 6 agents approve.

---

## DEBATE 3: ToolGuard Complexity

### 🟠 Security's Position:
"ToolGuard needs composable rules: deny-list, allow-list, path-scope (only files in
workspace), rate-limit (max N tool calls per minute), circuit breaker."

### 🔴 Skeptic's Rebuttal:
"Phase 3.5 ToolGuard should be JUST allow/deny lists. Simple, testable, shippable.
Add composable rules in Phase 6.5 when we have real usage data."

### 🟢 Architect's Compromise:
"Design the `IToolGuardRule` interface now. Implement only `AllowDenyRule` for Phase 3.5.
Add `PathScopeRule`, `RateLimitRule` in Phase 6.5. The interface is cheap; the
implementations are what cost time."

### 🟠 Security's Response:
"Accepted. But the circuit breaker (max 3 consecutive failures → escalate) MUST be in
Phase 3.5. It's 10 lines of code and prevents token burn."

### 🤝 RESOLUTION:
**Phase 3.5:** `IToolGuardRule` interface + `AllowDenyRule` implementation + circuit breaker
(3 failures → escalate).

**Phase 6.5:** Add `PathScopeRule`, `RateLimitRule`, audit log persistence.

All 6 agents approve.

---

# ═══════════════════════════════════════════════════════════════
# ROUND 2 CONSENSUS
# ═══════════════════════════════════════════════════════════════

## Architecture Decisions (LOCKED)

| Decision | Resolution | Agreed By |
|----------|-----------|-----------|
| MOTA timing | Phase 3.5 (core) + Phase 6.5 (full) | 6/6 |
| Bundled TS scanner | NO — MCP only. Auto-detect + onboarding. | 6/6 |
| ToolGuard complexity | Interface now, AllowDeny + CircuitBreaker in 3.5, more in 6.5 | 6/6 |
| Section caching | Cache in extension memory, TTL-based refresh | 5/6 |
| Batch MCP API | Add `get_sections` to Python MCP server | 5/6 |
| Audit persistence | globalState for now, SQLite later | 4/6 |
| NullMOTAService | Required for feature-flag-off path | 6/6 |
| Section name types | Union type for 33 section names | 5/6 |

## Must-Have Additions (from Agent Reviews)

1. `NullMOTAService` — null implementation when disabled
2. `IToolGuardRule` — composable rule interface
3. Circuit breaker — 3 failures → escalate
4. Matrix section caching with TTL
5. `MatrixSectionName` union type
6. `IMOTAFeedbackLoop` — separate service
7. Auto-detect Matrix MCP server on activation
8. Onboarding notification when Matrix first detected
9. Batch `get_sections` MCP tool (Python-side change)
10. Graceful degradation when Matrix not available

---

# ═══════════════════════════════════════════════════════════════
# SECTION D: THE PLAN (v2.0 — FINAL VALIDATED)
# ═══════════════════════════════════════════════════════════════

## MOTA Extension Integration — v2.0 (VALIDATED)

### Timing: Two Chunks

**Phase 3.5 — MOTA Core (3 weeks, after Tool System)**
| # | Task | File | Notes |
|---|------|------|-------|
| 3.5.1 | Types & enums | `src/extension/mota/types.ts` | All interfaces from Section 2.3 + MatrixSectionName union |
| 3.5.2 | Service interfaces | `src/extension/mota/services.ts` | All `I*` interfaces + service identifiers + NullMOTAService |
| 3.5.3 | Input sanitizer | `src/extension/mota/inputSanitizer.ts` | Prompt injection detection |
| 3.5.4 | Audit log | `src/extension/mota/auditLog.ts` | In-memory + globalState persistence |
| 3.5.5 | Intent classifier | `src/extension/mota/intentClassifier.ts` | Regex + keyword, slash command override |
| 3.5.6 | Blueprint registry | `src/extension/mota/blueprintRegistry.ts` | 3 hardcoded personas, `IToolGuardRule` interface |
| 3.5.7 | ToolGuard | `src/extension/mota/toolGuard.ts` | `AllowDenyRule` + circuit breaker, `IPreToolUseHook` |
| 3.5.8 | Session manager | `src/extension/mota/sessionManager.ts` | Session lifecycle, max iterations |
| 3.5.9 | MOTAService | `src/extension/mota/motaService.ts` | Orchestrator (mock MCP), NullMOTAService |
| 3.5.10 | DI registration | `src/extension/services.ts` | Register all MOTA services as Layer 5 |
| 3.5.11 | Unit tests | `test/unit/mota/*.test.ts` | 200 labeled messages, guard tests, audit tests |

**Exit Criteria Phase 3.5:**
- [ ] Intent accuracy >90% on 200 labeled messages
- [ ] ToolGuard blocks 100% of denied tools
- [ ] Circuit breaker triggers after 3 failures
- [ ] NullMOTAService returns no-op for everything
- [ ] All tests pass (`vitest --run --pool=forks`)

---

**Phase 6.5 — MOTA Full (3 weeks, after MCP)**
| # | Task | File | Notes |
|---|------|------|-------|
| 6.5.1 | Context assembler | `src/extension/mota/contextAssembler.ts` | Real MCP calls, section caching, TTL |
| 6.5.2 | Matrix cache | `src/extension/mota/matrixCache.ts` | In-memory cache with freshness check |
| 6.5.3 | Verification engine | `src/extension/mota/verificationEngine.ts` | tsc + eslint + vitest (TS-only for now) |
| 6.5.4 | Feedback loop | `src/extension/mota/feedbackLoop.ts` | Verify → error context → retry |
| 6.5.5 | Persona prompts | `src/extension/mota/promptElements/*.tsx` | JSX prompts for 3 personas |
| 6.5.6 | Chat participant | `src/extension/mota/participants/motaParticipant.ts` | MOTA-aware chat participant |
| 6.5.7 | Persona badge | `src/extension/mota/participants/personaBadge.ts` | UI rendering |
| 6.5.8 | Slash commands | `src/extension/mota/slashCommands/*.ts` | /implement, /review, /plan, /auto |
| 6.5.9 | Blueprint from Matrix | Update `blueprintRegistry.ts` | Load skills via `get_skills` MCP tool |
| 6.5.10 | Path scope rule | `src/extension/mota/toolGuard.ts` | Add `PathScopeRule`, `RateLimitRule` |
| 6.5.11 | Auto-detect + onboarding | `src/extension/mota/motaService.ts` | Detect Matrix MCP server, show notification |
| 6.5.12 | Integration tests | `test/unit/mota/*.test.ts` | Full pipeline with mock MCP |

**Exit Criteria Phase 6.5:**
- [ ] Context assembly from real Matrix MCP server works
- [ ] Verification catches >70% of introduced bugs
- [ ] Slash commands functional
- [ ] Graceful degradation when Matrix not running
- [ ] E2E: message → persona → context → response → verification ✅

---

**Python-Side Changes (1 day, before Phase 6.5):**
| # | Change | File |
|---|--------|------|
| P.1 | Add `get_sections(names)` batch tool | `codetrellis/mcp_server.py` |
| P.2 | Add `get_filtered_logic(query, max)` tool | `codetrellis/mcp_server.py` |
| P.3 | Enhance `get_cache_stats` with file mtimes | `codetrellis/mcp_server.py` |

---

### Validation Summary

| Agent | Final Verdict |
|-------|--------------|
| 🔴 Skeptic | ✅ PASS — "Phase 3.5 + 6.5 split is realistic. Hardcoded blueprints first." |
| 🟢 Architect | ✅ PASS — "Proper interfaces, NullService, composable ToolGuard." |
| 🔵 User Advocate | ✅ PASS — "Progressive disclosure. Auto-detect. Graceful degradation." |
| 🟡 Strategist | ✅ PASS — "Differentiator delivered. MCP platform play. Unified brand later." |
| 🟣 Matrix Expert | ✅ PASS — "MCP bridge works. Batch API. Section caching." |
| 🟠 Security | ✅ PASS — "ToolGuard Phase 3.5. Circuit breaker. Audit persistence." |

**Consensus: 6/6 agents approve.**

---

# ═══════════════════════════════════════════════════════════════
# SECTION E: SESSION-BASED IMPLEMENTATION (MEGA-PROMPTS)
# ═══════════════════════════════════════════════════════════════

> All work is in the **VS Code Extension workspace** (TypeScript).
> The only Python change is 3 small additions to `mcp_server.py` (1 day).

## Marathon Plan: 7 Mega-Prompts (~14 hours)

```
Phase 3.5 — MOTA Core (after Tool System is built)
├─ Mega-Prompt 1: Types + Sanitizer + Audit (~1.5h)
├─ Mega-Prompt 2: Intent + Blueprints + Guard (~2h)
├─ Mega-Prompt 3: Session + MOTAService + DI + Tests (~2h)
└─ ☕ Break — run full test suite

Phase 6.5 — MOTA Full (after MCP is built)
├─ Mega-Prompt 4: Context + Cache + Verification (~2h)
├─ Mega-Prompt 5: Prompts + Participant + Badge + Slash (~2h)
├─ Mega-Prompt 6: Wire to Real MCP + Auto-detect (~1.5h)
├─ Mega-Prompt 7: Integration Tests + Polish (~1.5h)
└─ 🎉 MOTA Complete

Python-Side (anytime before Phase 6.5)
├─ Mega-Prompt P: Add 2 MCP tools + enhance 1 (~1h)
```

---

### 🟢 MEGA-PROMPT 1 — Foundation (Phase 3.5, ~1.5h)

> **Paste into a fresh AI chat in the extension workspace:**
>
> I'm adding MOTA (Matrix-Orchestrated Tool Agents) as subsystem §5.27 to this
> VS Code extension. This is the first batch. Create these files:
>
> **1. `src/extension/mota/types.ts`** — All core types:
> - `PersonaType` const enum: Implementor, Reviewer, Planner, Debugger, Tester, Architect
> - `SessionState` const enum: Initializing, Executing, Verifying, Retrying, Complete, Failed
> - `FailureAction` const enum: Retry, Escalate, Abort
> - `MatrixSectionName` type: union of all 33 Matrix section names
> - `ITokenBudgetConfig`, `IVerificationStrategy`, `IAgentBlueprint`, `IToolCall`,
>   `IAgentIteration`, `IVerificationResult`, `IMOTASession`, `IMOTAAuditEvent`,
>   `IMatrixFreshness`, `IMatrixContext`, `IIntentResult`
> - Follow existing extension patterns: use `const enum`, `interface`, proper JSDoc
>
> **2. `src/extension/mota/services.ts`** — Service interfaces + identifiers:
> - `IMOTAService`, `IMOTAIntentClassifier`, `IMOTABlueprintRegistry`, `IMOTAToolGuard`,
>   `IMOTAContextAssembler`, `IMOTAVerificationEngine`, `IMOTAAuditLog`, `IMOTASessionManager`,
>   `IMOTAFeedbackLoop`
> - Each with `_serviceBrand: undefined` pattern
> - Use `createDecorator<T>()` for service identifiers
> - Include `NullMOTAService` class (no-op implementation)
>
> **3. `src/extension/mota/inputSanitizer.ts`** — Prompt injection detection:
> - `sanitizeInput(message: string): { cleaned: string; warnings: string[] }`
> - 10+ suspicious patterns (ignore previous instructions, override persona, etc.)
>
> **4. `src/extension/mota/auditLog.ts`** — Structured audit logging:
> - Implements `IMOTAAuditLog`
> - In-memory storage + VS Code `context.globalState` persistence
> - `log()`, `getTrail()`, `export()` methods
> - SHA-256 hash of user messages (first 12 chars)
>
> **5. Tests:** `test/unit/mota/types.test.ts`, `inputSanitizer.test.ts`, `auditLog.test.ts`
>
> Follow DI patterns from this codebase. Study `src/platform/instantiation/` for patterns.

**Commit:** `feat(mota): foundation — types, services, sanitizer, audit`

---

### 🟢 MEGA-PROMPT 2 — Decision Engine (Phase 3.5, ~2h)

> I'm building MOTA §5.27 for this extension. Foundation is done (types, services,
> sanitizer, audit). Now create the decision engine:
>
> **1. `src/extension/mota/intentClassifier.ts`** — Implements `IMOTAIntentClassifier`:
> - Pure regex + keyword matching (NO LLM)
> - Intents: add-endpoint, add-model, fix-issue, refactor-code, review, plan, debug, test-gen, etc.
> - Slash command override: /implement → Implementor, /review → Reviewer, /plan → Planner
> - Fallback: Implementor persona
> - Returns `IIntentResult` with confidence 0-1
>
> **2. `src/extension/mota/blueprintRegistry.ts`** — Implements `IMOTABlueprintRegistry`:
> - 3 hardcoded blueprints: Implementor, Reviewer, Planner (from plan Section 2.6)
> - `getBlueprint(intent)`, `listBlueprints()`, `getDefaultBlueprint()`
> - `loadFromMatrix()` — stubbed for Phase 6.5 (will call MCP `get_skills`)
>
> **3. `src/extension/mota/toolGuard.ts`** — Implements `IMOTAToolGuard`:
> - `IToolGuardRule` interface with `evaluate(toolName, session): {allowed, reason}`
> - `AllowDenyRule` implementation
> - `CircuitBreakerRule`: 3 consecutive failures → escalate
> - Registers as `IPreToolUseHook` in the existing §5.5 tool hook system
> - All decisions logged to `IMOTAAuditLog`
>
> **4. Tests:** `intentClassifier.test.ts` (with 200 labeled messages in `fixtures/testMessages.json`),
> `blueprintRegistry.test.ts`, `toolGuard.test.ts`

**Commit:** `feat(mota): decision engine — intent, blueprints, guard`

---

### 🟢 MEGA-PROMPT 3 — Integration (Phase 3.5, ~2h)

> MOTA §5.27 foundation + decision engine are done. Now wire everything together:
>
> **1. `src/extension/mota/sessionManager.ts`** — Implements `IMOTASessionManager`:
> - State machine: Initializing → Executing → Verifying → Complete/Failed
> - Track iterations, token usage, timestamps
> - Enforce `maxIterations` from blueprint
>
> **2. `src/extension/mota/motaService.ts`** — Implements `IMOTAService`:
> - Main orchestrator: sanitize → classify → blueprint → guard → session
> - Feature flag: `codetrellis.mota.enabled`
> - `isAvailable` checks if Matrix MCP server is detected
> - Events: onDidSessionStart, onDidSessionComplete, onDidSessionFail
> - For now: mock Matrix context (static JSON fixture)
>
> **3. Update `src/extension/services.ts`** — Register MOTA services:
> - Layer 5: all MOTA services, conditional on feature flag
> - When disabled: register NullMOTAService
>
> **4. Tests:** `sessionManager.test.ts`, `motaService.test.ts` (integration: 10+ scenarios
> including happy path, slash overrides, injection attempts, circuit breaker, disabled flag)

**Commit:** `feat(mota): Phase 3.5 complete — MOTA core with mock Matrix`

---

### 🔵 MEGA-PROMPT 4 — Smart Context (Phase 6.5, ~2h)

> MOTA core is built (Phase 3.5). MCP subsystem (§5.8) is now available.
> Wire MOTA to the real CodeTrellis Matrix via MCP:
>
> **1. `src/extension/mota/matrixCache.ts`** — Section cache:
> - In-memory cache with TTL (default 5 minutes)
> - Stores Matrix sections after MCP fetch
> - Freshness check via `get_cache_stats` MCP tool
>
> **2. `src/extension/mota/contextAssembler.ts`** — Implements `IMOTAContextAssembler`:
> - Calls Matrix MCP server via §5.8 `IMcpService`
> - Uses `get_sections` (batch) for blueprint.contextSections
> - Uses `get_context_for_file` for mentioned files
> - Uses `get_filtered_logic` for IMPL_LOGIC subsetting
> - Respects TokenBudgetConfig, truncates by priority
> - Uses matrixCache for repeated requests
>
> **3. `src/extension/mota/verificationEngine.ts`** — Implements `IMOTAVerificationEngine`:
> - Runs `tsc --noEmit` (type check), `eslint` (lint), `vitest --run` (test)
> - Executes via existing terminal tools from §5.5
> - Parses output into `IVerificationResult`
> - Handles tool-not-installed gracefully
>
> **4. `src/extension/mota/feedbackLoop.ts`** — Implements `IMOTAFeedbackLoop`:
> - Verification failure → parse errors → generate retry context
> - Track retry count, enforce maxRetries
> - FailureAction: Retry, Escalate, Abort
>
> **5. Tests** for all four modules

**Commit:** `feat(mota): smart context + verification via real MCP`

---

### 🔵 MEGA-PROMPT 5 — UX Layer (Phase 6.5, ~2h)

> MOTA is connected to real Matrix. Now add the UX layer:
>
> **1. `src/extension/mota/promptElements/`** — JSX prompt elements:
> - `implementorPrompt.tsx` — system prompt for 🔧 Implementor
> - `reviewerPrompt.tsx` — system prompt for 🔍 Reviewer
> - `plannerPrompt.tsx` — system prompt for 📋 Planner
> - `matrixContextPrompt.tsx` — injects Matrix context with priority-based token allocation
> - Follow existing §5.4 prompt element patterns (priority, flexGrow)
>
> **2. `src/extension/mota/participants/motaParticipant.ts`** — Chat participant:
> - Registers as a chat participant provider
> - Intercepts messages, runs through MOTA pipeline
> - Renders persona badge and verification results
>
> **3. `src/extension/mota/participants/personaBadge.ts`** — UI rendering:
> - Shows 🔧/🔍/📋 emoji + persona name
> - Progressive disclosure based on settings
>
> **4. `src/extension/mota/slashCommands/`** — Slash commands:
> - `implementCommand.ts`, `reviewCommand.ts`, `planCommand.ts`, `autoCommand.ts`
> - Register via §5.25 slash command system
>
> **5. Tests** for participant and slash commands

**Commit:** `feat(mota): UX — persona prompts, badges, slash commands`

---

### 🔵 MEGA-PROMPT 6 — Wire + Auto-detect (Phase 6.5, ~1.5h)

> MOTA UX is ready. Now wire end-to-end and add auto-detection:
>
> **1. Update `motaService.ts`** — Replace mock Matrix with real MCP calls:
> - On activation: check if CodeTrellis Matrix MCP server is in the MCP server list
> - If found: enable MOTA, load blueprints from Matrix skills
> - If not found: stay disabled, use NullMOTAService
>
> **2. Onboarding notification:**
> - First time Matrix detected: show "CodeTrellis Matrix detected! AI now uses your
>   project's patterns. [Learn More] [Settings]"
> - Store in globalState so notification shows only once
>
> **3. Graceful degradation:**
> - If MCP server disconnects mid-session: fall back to vanilla chat
> - If Matrix is stale: show warning but continue
>
> **4. Update `blueprintRegistry.ts`** — Load real skills from `get_skills` MCP tool:
> - Map Matrix skills to AgentBlueprints dynamically
> - Fall back to hardcoded blueprints if MCP call fails

**Commit:** `feat(mota): wire to real Matrix MCP + auto-detect + onboarding`

---

### 🔵 MEGA-PROMPT 7 — Integration Tests + Polish (Phase 6.5, ~1.5h)

> MOTA is fully wired. Final session — integration tests and polish:
>
> **1. `test/unit/mota/motaIntegration.test.ts`** — Full pipeline tests:
> - Message → sanitize → intent → blueprint → context (mock MCP) → prompt → verify
> - 10+ scenarios: happy path, retry, escalation, disabled, slash override, injection
>
> **2. Performance:** Lazy-load MOTA module, cache blueprints, batch MCP calls
>
> **3. Update package.json:** Add `codetrellis.mota.enabled` and `codetrellis.mota.showPersona`
> and `codetrellis.mota.showTrace` settings with descriptions
>
> **4. All tests pass:** `npm run test:unit` + `npm run typecheck`

**Commit:** `feat(mota): Phase 6.5 complete — MOTA fully integrated 🎉`

---

### 🟡 MEGA-PROMPT P — Python MCP Changes (1h, anytime before Phase 6.5)

> **This one goes in the CodeTrellis Matrix workspace (Python):**
>
> Add 2 new MCP tools and enhance 1 in `codetrellis/mcp_server.py`:
>
> **1. `get_sections(names: List[str])` tool** — Batch fetch multiple sections in one call.
> Returns `Dict[str, str]` mapping section name to content.
>
> **2. `get_filtered_logic(query: str, max_snippets: int = 20)` tool** — Filter IMPL_LOGIC
> snippets by relevance to query. Return top N snippets.
>
> **3. Enhance `get_cache_stats`** — Add `matrix_mtime` (file modification time) and
> `source_files_newer_count` (number of source files modified since last scan).
>
> Add tests in `tests/test_mcp_server.py`.

**Commit:** `feat(mcp): add batch sections + filtered logic tools for MOTA`

---

### Session Summary

| Mega-Prompt | Phase | Duration | Deliverables | Language |
|-------------|-------|----------|-------------|----------|
| 1 | 3.5 | ~1.5h | Types, services, sanitizer, audit | TypeScript |
| 2 | 3.5 | ~2h | Intent, blueprints, ToolGuard | TypeScript |
| 3 | 3.5 | ~2h | Session, MOTAService, DI, integration tests | TypeScript |
| P | pre-6.5 | ~1h | Batch MCP tools (Python) | Python |
| 4 | 6.5 | ~2h | Context, cache, verify, feedback | TypeScript |
| 5 | 6.5 | ~2h | Prompts, participant, badge, slash | TypeScript |
| 6 | 6.5 | ~1.5h | Wire MCP, auto-detect, onboarding | TypeScript |
| 7 | 6.5 | ~1.5h | Integration tests, polish | TypeScript |
| **Total** | | **~14h** | **17 TS files + 3 Python changes** | **TS + tiny Python** |

---

### Tips

1. **Phase 3.5 can be done in one sitting** (~5.5h across 3 mega-prompts).
2. **Phase 6.5 can be done in one sitting** (~7h across 4 mega-prompts).
3. **Mega-Prompt P (Python)** can be done anytime — even in 30 minutes before Phase 6.5.
4. **Always commit between mega-prompts** — fresh AI context each time.
5. **Mock MCP responses** for Phase 3.5 using static JSON in `test/unit/mota/fixtures/`.
6. **The only Python code change** is 3 small additions to `mcp_server.py`.
