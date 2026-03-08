"""
EnhancedXstateParser v1.0 - Comprehensive XState parser using all extractors.

This parser integrates all XState extractors to provide complete parsing of
XState state machine usage across TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting XState-specific semantics.

Supports:
- XState v3.x (Machine() factory, interpret, State, assign, send)
- XState v4.x (createMachine, interpret, spawn, predictableActionArguments,
                assign, send, sendTo, raise, log, pure, choose,
                forwardTo, escalate, respond, cond guards,
                invoke services, after/always transitions,
                @xstate/react useMachine/useInterpret/useSelector,
                @xstate/inspect, @xstate/test, @xstate/graph,
                TypeScript typegen with tsTypes/schema)
- XState v5.x (setup().createMachine(), createActor, actor model,
                fromPromise, fromObservable, fromCallback, fromTransition,
                enqueueActions, emit, guard (replaces cond),
                not/and/or guard combinators, stateIn,
                @xstate/react useActor/useActorRef/useSelector,
                @xstate/store, @statelyai/inspect)

State Machine Patterns:
- Machine definitions (createMachine, Machine, setup)
- State nodes (atomic, compound, parallel, final, history)
- Transitions (event-driven, guarded, delayed, eventless)
- Actions (assign, send, raise, log, stop, cancel, pure, choose)
- Guards/conditions (cond v4, guard v5, combinators)
- Services/actors (invoke, spawn, fromPromise, fromCallback)
- Context and event typing

Framework Integration:
- @xstate/react (useMachine, useActor, useSelector, useActorRef)
- @xstate/vue (useMachine)
- @xstate/svelte (useMachine)
- @xstate/solid (useActor)
- @xstate/inspect / @statelyai/inspect
- @xstate/test (createTestModel, createTestMachine)
- @xstate/graph (getSimplePaths, getShortestPaths)
- @xstate/store (createStore)

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all XState extractors
from .extractors.xstate import (
    XstateMachineExtractor, XstateMachineInfo,
    XstateStateExtractor, XstateStateNodeInfo, XstateTransitionInfo, XstateInvokeInfo,
    XstateActionExtractor, XstateActionInfo,
    XstateGuardExtractor, XstateGuardInfo,
    XstateApiExtractor, XstateImportInfo, XstateActorInfo, XstateTypegenInfo,
)


@dataclass
class XstateParseResult:
    """Complete parse result for a file with XState usage."""
    file_path: str
    file_type: str = "ts"  # ts, tsx, js, jsx

    # Machines
    machines: List[XstateMachineInfo] = field(default_factory=list)

    # States
    state_nodes: List[XstateStateNodeInfo] = field(default_factory=list)
    transitions: List[XstateTransitionInfo] = field(default_factory=list)
    invokes: List[XstateInvokeInfo] = field(default_factory=list)

    # Actions
    actions: List[XstateActionInfo] = field(default_factory=list)

    # Guards
    guards: List[XstateGuardInfo] = field(default_factory=list)

    # API
    imports: List[XstateImportInfo] = field(default_factory=list)
    actors: List[XstateActorInfo] = field(default_factory=list)
    typegens: List[XstateTypegenInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    xstate_version: str = ""  # v3, v4, v5


class EnhancedXstateParser:
    """
    Enhanced XState parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when XState
    framework is detected. It extracts XState-specific semantics that
    the language parsers cannot capture.

    Framework detection supports 15+ XState ecosystem libraries across:
    - Core (xstate, createMachine, createActor, setup)
    - React (@xstate/react, useMachine, useActor, useSelector)
    - Vue (@xstate/vue), Svelte (@xstate/svelte), Solid (@xstate/solid)
    - Tools (@xstate/inspect, @xstate/test, @xstate/graph)
    - Store (@xstate/store)
    - Stately (@statelyai/inspect)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # XState ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'xstate': re.compile(
            r"from\s+['\"]xstate['\"]|require\(['\"]xstate['\"]\)|"
            r"from\s+['\"]xstate/lib",
            re.MULTILINE
        ),
        'xstate-v5': re.compile(
            r"from\s+['\"]xstate['\"].*?(?:setup|createActor|fromPromise|fromCallback|fromObservable|fromTransition)",
            re.MULTILINE | re.DOTALL
        ),

        # ── Framework Adapters ────────────────────────────────────
        '@xstate/react': re.compile(
            r"from\s+['\"]@xstate/react['\"]|require\(['\"]@xstate/react['\"]\)",
            re.MULTILINE
        ),
        '@xstate/vue': re.compile(
            r"from\s+['\"]@xstate/vue['\"]",
            re.MULTILINE
        ),
        '@xstate/svelte': re.compile(
            r"from\s+['\"]@xstate/svelte['\"]",
            re.MULTILINE
        ),
        '@xstate/solid': re.compile(
            r"from\s+['\"]@xstate/solid['\"]",
            re.MULTILINE
        ),

        # ── Tools ─────────────────────────────────────────────────
        '@xstate/inspect': re.compile(
            r"from\s+['\"]@xstate/inspect['\"]|"
            r"from\s+['\"]@statelyai/inspect['\"]|"
            r"from\s+['\"]@stately/inspect['\"]",
            re.MULTILINE
        ),
        '@xstate/test': re.compile(
            r"from\s+['\"]@xstate/test['\"]",
            re.MULTILINE
        ),
        '@xstate/graph': re.compile(
            r"from\s+['\"]@xstate/graph['\"]",
            re.MULTILINE
        ),
        '@xstate/store': re.compile(
            r"from\s+['\"]@xstate/store['\"]",
            re.MULTILINE
        ),
        '@xstate/immer': re.compile(
            r"from\s+['\"]@xstate/immer['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'createMachine': re.compile(r'createMachine\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'Machine': re.compile(r'Machine\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'setup': re.compile(r'setup\s*(?:<[^>]*>)?\s*\(\s*\{', re.MULTILINE),
        'createActor': re.compile(r'createActor\s*\(', re.MULTILINE),
        'interpret': re.compile(r'interpret\s*\(', re.MULTILINE),
        'assign': re.compile(r'assign\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'send': re.compile(r'(?:send|sendTo)\s*\(', re.MULTILINE),
        'raise': re.compile(r'(?<!\.)raise\s*\(', re.MULTILINE),
        'invoke': re.compile(r'invoke\s*:\s*(?:\{|\[)', re.MULTILINE),
        'spawn': re.compile(r'spawn\s*\(', re.MULTILINE),
        'after': re.compile(r'after\s*:\s*\{', re.MULTILINE),
        'always': re.compile(r'always\s*:\s*(?:\[|\{)', re.MULTILINE),
        'parallel': re.compile(r"type\s*:\s*['\"]parallel['\"]", re.MULTILINE),
        'history': re.compile(r"type\s*:\s*['\"]history['\"]", re.MULTILINE),
        'final': re.compile(r"type\s*:\s*['\"]final['\"]", re.MULTILINE),
        'guards': re.compile(r'(?:cond|guard)\s*:', re.MULTILINE),
        'useMachine': re.compile(r'useMachine\s*\(', re.MULTILINE),
        'useActor': re.compile(r'useActor\s*\(', re.MULTILINE),
        'useSelector': re.compile(r'useSelector\s*\(', re.MULTILINE),
        'useActorRef': re.compile(r'useActorRef\s*\(', re.MULTILINE),
        'fromPromise': re.compile(r'fromPromise\s*\(', re.MULTILINE),
        'fromCallback': re.compile(r'fromCallback\s*\(', re.MULTILINE),
        'fromObservable': re.compile(r'fromObservable\s*\(', re.MULTILINE),
        'fromTransition': re.compile(r'fromTransition\s*\(', re.MULTILINE),
        'enqueueActions': re.compile(r'enqueueActions\s*\(', re.MULTILINE),
        'emit': re.compile(r'(?<!\.)emit\s*\(', re.MULTILINE),
        'predictableActionArguments': re.compile(r'predictableActionArguments', re.MULTILINE),
        'typegen': re.compile(r'tsTypes|typegen', re.MULTILINE),
        'pure': re.compile(r'pure\s*\(', re.MULTILINE),
        'choose': re.compile(r'choose\s*\(\s*\[', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all XState extractors."""
        self.machine_extractor = XstateMachineExtractor()
        self.state_extractor = XstateStateExtractor()
        self.action_extractor = XstateActionExtractor()
        self.guard_extractor = XstateGuardExtractor()
        self.api_extractor = XstateApiExtractor()

    def is_xstate_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains XState code.

        Returns True if the file imports from XState ecosystem
        or uses XState patterns (createMachine, useMachine, etc.)
        """
        xstate_indicators = [
            'xstate', 'createMachine(', 'Machine(',
            'createActor(', 'interpret(',
            "from 'xstate", 'from "xstate',
            "from '@xstate/", 'from "@xstate/',
            '@xstate/react', '@xstate/vue', '@xstate/svelte',
            '@xstate/solid', '@statelyai/inspect',
            'useMachine(', 'useActor(', 'useActorRef(',
            'setup({', 'fromPromise(', 'fromCallback(',
        ]
        return any(ind in content for ind in xstate_indicators)

    def parse(self, content: str, file_path: str = "") -> XstateParseResult:
        """
        Parse a source file for XState patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            XstateParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = XstateParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.xstate_version = self._detect_version(content)

        # ── Machine extraction ─────────────────────────────────────
        try:
            machine_result = self.machine_extractor.extract(content, file_path)
            result.machines = machine_result.get('machines', [])
        except Exception:
            pass

        # ── State extraction ───────────────────────────────────────
        try:
            state_result = self.state_extractor.extract(content, file_path)
            result.state_nodes = state_result.get('state_nodes', [])
            result.transitions = state_result.get('transitions', [])
            result.invokes = state_result.get('invokes', [])
        except Exception:
            pass

        # ── Action extraction ──────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.actions = action_result.get('actions', [])
        except Exception:
            pass

        # ── Guard extraction ───────────────────────────────────────
        try:
            guard_result = self.guard_extractor.extract(content, file_path)
            result.guards = guard_result.get('guards', [])
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.actors = api_result.get('actors', [])
            result.typegens = api_result.get('typegens', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which XState ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    # Import-based feature detection: features that can be detected from
    # import specifiers alone (e.g. `import { assign } from 'xstate'`)
    _IMPORT_FEATURE_RE = re.compile(
        r"""(?:import|require)\s*\{([^}]+)\}\s*from\s*['"](?:xstate|@xstate/\w+)['"]""",
        re.MULTILINE,
    )
    _IMPORTABLE_FEATURES = {
        'assign', 'send', 'sendTo', 'raise', 'log', 'stop', 'cancel',
        'pure', 'choose', 'forwardTo', 'escalate', 'respond',
        'createMachine', 'Machine', 'setup', 'createActor', 'interpret',
        'spawn', 'fromPromise', 'fromCallback', 'fromObservable',
        'fromTransition', 'enqueueActions', 'emit',
        'useMachine', 'useActor', 'useSelector', 'useActorRef',
    }

    def _detect_features(self, content: str) -> List[str]:
        """Detect which XState features are used (call-sites + imports)."""
        detected: set[str] = set()

        # 1. Call-site patterns (existing)
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.add(name)

        # 2. Import specifiers (covers cases where the symbol is imported
        #    but only used in a way the call-site regex doesn't catch)
        for m in self._IMPORT_FEATURE_RE.finditer(content):
            specifiers = [s.strip().split(' as ')[0].strip() for s in m.group(1).split(',')]
            for spec in specifiers:
                if spec in self._IMPORTABLE_FEATURES:
                    detected.add(spec)

        return sorted(detected)

    def _detect_version(self, content: str) -> str:
        """
        Detect XState version based on API usage patterns.

        Returns:
            - 'v5' if XState v5+ patterns detected
            - 'v4' if XState v4 patterns detected
            - 'v3' if XState v3 patterns detected
            - '' if unknown
        """
        # v5 indicators — call-site patterns
        v5_indicators = [
            'setup(',              # setup() API
            'createActor(',        # createActor (replaces interpret)
            'fromPromise(',        # actor factories
            'fromCallback(',
            'fromObservable(',
            'fromTransition(',
            'enqueueActions(',     # v5 action queuing
            '.emit(',              # v5 event emission
            'useActorRef(',        # @xstate/react v5
        ]
        if any(ind in content for ind in v5_indicators):
            return "v5"

        # v5 indicators — import specifiers
        # (handles import-only files where the API isn't called yet)
        v5_import_symbols = {
            'setup', 'createActor', 'fromPromise', 'fromCallback',
            'fromObservable', 'fromTransition', 'enqueueActions', 'emit',
        }
        for m in self._IMPORT_FEATURE_RE.finditer(content):
            specifiers = {s.strip().split(' as ')[0].strip() for s in m.group(1).split(',')}
            if specifiers & v5_import_symbols:
                return "v5"

        # v4 indicators
        v4_indicators = [
            'createMachine(',              # v4 main API
            'interpret(',                  # v4 interpret
            'predictableActionArguments',  # v4 config
            'tsTypes',                     # v4 typegen
            'spawn(',                      # v4 spawn
        ]
        if any(ind in content for ind in v4_indicators):
            return "v4"

        # v3 indicators
        if 'Machine(' in content:
            return "v3"

        # Basic xstate import = at least v4
        if "'xstate'" in content or '"xstate"' in content:
            return "v4"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v3': 3, 'v4': 4, 'v5': 5}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
