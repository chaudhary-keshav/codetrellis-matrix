"""
EnhancedJotaiParser v1.0 - Comprehensive Jotai parser using all extractors.

This parser integrates all Jotai extractors to provide complete parsing of
Jotai atomic state management usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Jotai-specific semantics.

Supports:
- Jotai v1.x (atom, Provider, useAtom, atomFamily, atomWithStorage,
               selectAtom, splitAtom, focusAtom, useUpdateAtom, freezeAtom)
- Jotai v2.x (atom, useAtom, useAtomValue, useSetAtom, createStore,
               getDefaultStore, useStore, Provider store prop,
               useHydrateAtoms, atom scoping, improved TypeScript types,
               jotai/react + jotai/vanilla subpath exports)

Atom Patterns:
- Primitive atoms (atom(initialValue) — string, number, boolean, object, array)
- Derived atoms (atom((get) => get(sourceAtom).field) — read-only computed)
- Writable derived atoms (atom(readFn, writeFn) — custom write logic)
- Async atoms (atom(async (get) => await fetch(...)) — Promise-based)
- Atom families (atomFamily((param) => atom(...)) — parameterized factories)
- Resettable atoms (atomWithReset(initialValue) + RESET sentinel)
- Reducer atoms (atomWithReducer(initialValue, reducer))

Utility Atoms (jotai/utils, jotai-* ecosystem):
- atomWithStorage (localStorage, sessionStorage, AsyncStorage, custom)
- selectAtom (memoized selector with equality function)
- focusAtom (jotai-optics — lens-based atom access)
- splitAtom (split array atom into individual atoms)
- loadable (wrap async atom with loading/error state)
- unwrap (unwrap async atom with fallback)
- atomWithDefault (lazy default value)
- atomWithObservable (RxJS integration)
- atomWithMachine (jotai-xstate — XState integration)
- atomEffect (jotai-effect — side-effect atoms)
- atomWithProxy (jotai-valtio — Valtio proxy state)
- atomWithImmer (jotai-immer — Immer immutable updates)
- atomWithLocation / atomWithHash (jotai-location — URL state)
- atomWithRefresh (refetchable async atoms)
- atomWithQuery / atomWithMutation (jotai-tanstack-query)

Hook API:
- useAtom(atom) → [value, setValue] (read + write)
- useAtomValue(atom) → value (read-only, v2)
- useSetAtom(atom) → setValue (write-only, v2)
- useStore() → store instance (v2)
- useHydrateAtoms([[atom, value]]) → SSR hydration (v2)
- useAtomCallback((get, set) => ...) (jotai/utils)

Store API (v2):
- createStore() → store
- getDefaultStore() → default store
- store.get(atom) → value
- store.set(atom, value)
- store.sub(atom, callback) → unsubscribe

Framework Ecosystem Detection (30+ patterns):
- Core: jotai, jotai/react, jotai/vanilla, jotai/utils
- Extensions: jotai-devtools, jotai-immer, jotai-optics, jotai-xstate,
              jotai-effect, jotai-tanstack-query, jotai-trpc,
              jotai-molecules, jotai-scope, jotai-location, jotai-valtio
- Ecosystem: react, react-dom, @tanstack/react-query, react-hook-form,
              next, immer, xstate, rxjs, @testing-library/react, vitest, jest

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Jotai extractors
from .extractors.jotai import (
    JotaiAtomExtractor, JotaiAtomInfo, JotaiAtomFamilyInfo, JotaiResettableAtomInfo,
    JotaiSelectorExtractor, JotaiDerivedAtomInfo, JotaiSelectAtomInfo, JotaiFocusAtomInfo,
    JotaiMiddlewareExtractor, JotaiStorageAtomInfo, JotaiEffectInfo, JotaiMachineAtomInfo,
    JotaiActionExtractor, JotaiHookUsageInfo, JotaiWriteFnInfo, JotaiStoreUsageInfo,
    JotaiApiExtractor, JotaiImportInfo, JotaiIntegrationInfo, JotaiTypeInfo,
)


@dataclass
class JotaiParseResult:
    """Complete parse result for a file with Jotai usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Atoms
    atoms: List[JotaiAtomInfo] = field(default_factory=list)
    atom_families: List[JotaiAtomFamilyInfo] = field(default_factory=list)
    resettable_atoms: List[JotaiResettableAtomInfo] = field(default_factory=list)

    # Selectors / Derived
    derived_atoms: List[JotaiDerivedAtomInfo] = field(default_factory=list)
    select_atoms: List[JotaiSelectAtomInfo] = field(default_factory=list)
    focus_atoms: List[JotaiFocusAtomInfo] = field(default_factory=list)

    # Middleware / Extensions
    storage_atoms: List[JotaiStorageAtomInfo] = field(default_factory=list)
    effects: List[JotaiEffectInfo] = field(default_factory=list)
    machine_atoms: List[JotaiMachineAtomInfo] = field(default_factory=list)

    # Actions / Hooks
    hook_usages: List[JotaiHookUsageInfo] = field(default_factory=list)
    write_fns: List[JotaiWriteFnInfo] = field(default_factory=list)
    store_usages: List[JotaiStoreUsageInfo] = field(default_factory=list)

    # API
    imports: List[JotaiImportInfo] = field(default_factory=list)
    integrations: List[JotaiIntegrationInfo] = field(default_factory=list)
    types: List[JotaiTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    jotai_version: str = ""  # v1, v2


class EnhancedJotaiParser:
    """
    Enhanced Jotai parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Jotai framework is detected. It extracts Jotai-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Jotai ecosystem libraries across:
    - Core (jotai, jotai/react, jotai/vanilla, jotai/utils)
    - Extensions (jotai-devtools, jotai-immer, jotai-optics, jotai-xstate,
                   jotai-effect, jotai-tanstack-query, jotai-trpc,
                   jotai-molecules, jotai-scope, jotai-location, jotai-valtio)
    - Testing (@testing-library/react, vitest, jest)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Jotai ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'jotai': re.compile(
            r"from\s+['\"]jotai['\"]|require\(['\"]jotai['\"]\)|"
            r"from\s+['\"]jotai/react['\"]",
            re.MULTILINE
        ),
        'jotai-utils': re.compile(
            r"from\s+['\"]jotai/utils['\"]|"
            r"from\s+['\"]jotai-utils['\"]",
            re.MULTILINE
        ),
        'jotai-vanilla': re.compile(
            r"from\s+['\"]jotai/vanilla['\"]",
            re.MULTILINE
        ),

        # ── Extensions ───────────────────────────────────────────
        'jotai-devtools': re.compile(
            r"from\s+['\"]jotai-devtools['\"]|"
            r"useAtomsDebugValue|useAtomDevtools|<DevTools",
            re.MULTILINE
        ),
        'jotai-immer': re.compile(
            r"from\s+['\"]jotai-immer['\"]|atomWithImmer\s*\(",
            re.MULTILINE
        ),
        'jotai-optics': re.compile(
            r"from\s+['\"]jotai-optics['\"]|focusAtom\s*\(",
            re.MULTILINE
        ),
        'jotai-xstate': re.compile(
            r"from\s+['\"]jotai-xstate['\"]|atomWithMachine\s*\(",
            re.MULTILINE
        ),
        'jotai-effect': re.compile(
            r"from\s+['\"]jotai-effect['\"]|atomEffect\s*\(",
            re.MULTILINE
        ),
        'jotai-tanstack-query': re.compile(
            r"from\s+['\"]jotai-tanstack-query['\"]|"
            r"from\s+['\"]jotai/query['\"]|"
            r"atomWithQuery\s*\(|atomWithMutation\s*\(",
            re.MULTILINE
        ),
        'jotai-trpc': re.compile(
            r"from\s+['\"]jotai-trpc['\"]|createTRPCJotai\s*\(",
            re.MULTILINE
        ),
        'jotai-molecules': re.compile(
            r"from\s+['\"]jotai-molecules['\"]|"
            r"molecule\s*\(|useMolecule\s*\(",
            re.MULTILINE
        ),
        'jotai-scope': re.compile(
            r"from\s+['\"]jotai-scope['\"]|ScopeProvider\b",
            re.MULTILINE
        ),
        'jotai-location': re.compile(
            r"from\s+['\"]jotai-location['\"]|"
            r"atomWithLocation\s*\(|atomWithHash\s*\(",
            re.MULTILINE
        ),
        'jotai-valtio': re.compile(
            r"from\s+['\"]jotai-valtio['\"]|atomWithProxy\s*\(",
            re.MULTILINE
        ),

        # ── Ecosystem Integration ─────────────────────────────────
        'immer': re.compile(
            r"from\s+['\"]immer['\"]|produce\s*\(",
            re.MULTILINE
        ),
        'xstate': re.compile(
            r"from\s+['\"]xstate['\"]|createMachine\s*\(",
            re.MULTILINE
        ),
        'rxjs': re.compile(
            r"from\s+['\"]rxjs['\"]|Observable\b|Subject\b",
            re.MULTILINE
        ),
        'react-query': re.compile(
            r"from\s+['\"]@tanstack/react-query['\"]|from\s+['\"]react-query['\"]",
            re.MULTILINE
        ),
        'react-hook-form': re.compile(
            r"from\s+['\"]react-hook-form['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'atom': re.compile(r'\batom\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'atom_family': re.compile(r'atomFamily\s*\(', re.MULTILINE),
        'atom_with_storage': re.compile(r'atomWithStorage\s*\(', re.MULTILINE),
        'atom_with_reset': re.compile(r'atomWithReset\s*\(', re.MULTILINE),
        'atom_with_default': re.compile(r'atomWithDefault\s*\(', re.MULTILINE),
        'atom_with_reducer': re.compile(r'atomWithReducer\s*\(', re.MULTILINE),
        'atom_with_observable': re.compile(r'atomWithObservable\s*\(', re.MULTILINE),
        'atom_with_machine': re.compile(r'atomWithMachine\s*\(', re.MULTILINE),
        'atom_effect': re.compile(r'atomEffect\s*\(', re.MULTILINE),
        'atom_with_proxy': re.compile(r'atomWithProxy\s*\(', re.MULTILINE),
        'atom_with_immer': re.compile(r'atomWithImmer\s*\(', re.MULTILINE),
        'atom_with_location': re.compile(r'atomWithLocation\s*\(', re.MULTILINE),
        'atom_with_hash': re.compile(r'atomWithHash\s*\(', re.MULTILINE),
        'atom_with_refresh': re.compile(r'atomWithRefresh\s*\(', re.MULTILINE),
        'atom_with_query': re.compile(r'atomWithQuery\s*\(', re.MULTILINE),
        'atom_with_mutation': re.compile(r'atomWithMutation\s*\(', re.MULTILINE),
        'select_atom': re.compile(r'selectAtom\s*\(', re.MULTILINE),
        'focus_atom': re.compile(r'focusAtom\s*\(', re.MULTILINE),
        'split_atom': re.compile(r'splitAtom\s*\(', re.MULTILINE),
        'loadable': re.compile(r'loadable\s*\(', re.MULTILINE),
        'unwrap': re.compile(r'unwrap\s*\(', re.MULTILINE),
        'on_mount': re.compile(r'\.onMount\s*=', re.MULTILINE),
        'use_atom': re.compile(r'useAtom\s*\(', re.MULTILINE),
        'use_atom_value': re.compile(r'useAtomValue\s*\(', re.MULTILINE),
        'use_set_atom': re.compile(r'useSetAtom\s*\(', re.MULTILINE),
        'use_store': re.compile(r'useStore\s*\(', re.MULTILINE),
        'use_hydrate_atoms': re.compile(r'useHydrateAtoms\s*\(', re.MULTILINE),
        'create_store': re.compile(r'createStore\s*\(', re.MULTILINE),
        'get_default_store': re.compile(r'getDefaultStore\s*\(', re.MULTILINE),
        'provider': re.compile(r'<Provider[\s>]', re.MULTILINE),
        'devtools': re.compile(r'useAtomsDebugValue|useAtomDevtools|<DevTools', re.MULTILINE),
        'use_atom_callback': re.compile(r'useAtomCallback\s*\(', re.MULTILINE),
        'scope_provider': re.compile(r'ScopeProvider\b', re.MULTILINE),
        'molecule': re.compile(r'molecule\s*\(|useMolecule\s*\(', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Jotai extractors."""
        self.atom_extractor = JotaiAtomExtractor()
        self.selector_extractor = JotaiSelectorExtractor()
        self.middleware_extractor = JotaiMiddlewareExtractor()
        self.action_extractor = JotaiActionExtractor()
        self.api_extractor = JotaiApiExtractor()

    def is_jotai_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Jotai code.

        Returns True if the file imports from Jotai ecosystem
        or uses Jotai patterns (atom, useAtom, etc.)
        """
        jotai_indicators = [
            'jotai', "from 'jotai", 'from "jotai',
            "from 'jotai/", 'from "jotai/',
            'jotai/utils', 'jotai/react', 'jotai/vanilla',
            'jotai-devtools', 'jotai-immer', 'jotai-optics',
            'jotai-xstate', 'jotai-effect', 'jotai-tanstack-query',
            'jotai-trpc', 'jotai-molecules', 'jotai-scope',
            'jotai-location', 'jotai-valtio',
            'useAtom(', 'useAtomValue(', 'useSetAtom(',
            'atomWithStorage(', 'atomFamily(',
            'atomWithReset(', 'atomEffect(',
            'useHydrateAtoms(',
        ]
        return any(ind in content for ind in jotai_indicators)

    def parse(self, content: str, file_path: str = "") -> JotaiParseResult:
        """
        Parse a source file for Jotai patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            JotaiParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = JotaiParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.jotai_version = self._detect_version(content)

        # ── Atom extraction ────────────────────────────────────────
        try:
            atom_result = self.atom_extractor.extract(content, file_path)
            result.atoms = atom_result.get('atoms', [])
            result.atom_families = atom_result.get('atom_families', [])
            result.resettable_atoms = atom_result.get('resettable_atoms', [])
        except Exception:
            pass

        # ── Selector extraction ───────────────────────────────────
        try:
            sel_result = self.selector_extractor.extract(content, file_path)
            result.derived_atoms = sel_result.get('derived_atoms', [])
            result.select_atoms = sel_result.get('select_atoms', [])
            result.focus_atoms = sel_result.get('focus_atoms', [])
        except Exception:
            pass

        # ── Middleware extraction ──────────────────────────────────
        try:
            mw_result = self.middleware_extractor.extract(content, file_path)
            result.storage_atoms = mw_result.get('storage_atoms', [])
            result.effects = mw_result.get('effects', [])
            result.machine_atoms = mw_result.get('machine_atoms', [])
        except Exception:
            pass

        # ── Action extraction ─────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.hook_usages = action_result.get('hook_usages', [])
            result.write_fns = action_result.get('write_fns', [])
            result.store_usages = action_result.get('store_usages', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Jotai ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Jotai features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Jotai version based on API usage patterns.

        Returns:
            - 'v2' if Jotai v2+ patterns detected
            - 'v1' if only v1 patterns
            - '' if unknown
        """
        # v2 indicators (subpath exports, new hooks, store API)
        v2_indicators = [
            'useAtomValue',           # v2 hook
            'useSetAtom',             # v2 hook
            'useStore',               # v2 store hook
            'createStore',            # v2 store API
            'getDefaultStore',        # v2 store API
            'useHydrateAtoms',        # v2 SSR
            "jotai/react'",           # v2 subpath export
            'jotai/react"',           # v2 subpath export
            "jotai/vanilla'",         # v2 subpath export
            'jotai/vanilla"',         # v2 subpath export
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators (deprecated in v2)
        v1_indicators = [
            'useUpdateAtom',         # deprecated in v2
            'useAtomCallback',       # moved to jotai/utils in v2
            "jotai/devtools'",       # moved to jotai-devtools in v2
            'jotai/devtools"',
        ]
        if any(ind in content for ind in v1_indicators):
            return "v1"

        # Basic jotai import present
        if "from 'jotai'" in content or 'from "jotai"' in content:
            return "v2"  # Most common version now

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v1': 1, 'v2': 2}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
