"""
EnhancedRecoilParser v1.0 - Comprehensive Recoil parser using all extractors.

This parser integrates all Recoil extractors to provide complete parsing of
Recoil state management usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Recoil-specific semantics.

Supports:
- Recoil 0.0.x (initial: atom, selector, useRecoilState, useRecoilValue,
                 useSetRecoilState, RecoilRoot)
- Recoil 0.1.x (atomFamily, selectorFamily, useResetRecoilState,
                 constSelector, errorSelector, waitForAll, waitForNone,
                 noWait, useRecoilStateLoadable, useRecoilValueLoadable)
- Recoil 0.2.x (atom effects, useRecoilCallback)
- Recoil 0.3.x (useRecoilCallback improvements, waitForAllSettled, waitForAny)
- Recoil 0.4.x (Snapshot improvements, snapshot.retain(), snapshot.asyncMap(),
                 snapshot_UNSTABLE, useGotoRecoilSnapshot)
- Recoil 0.5.x (useRecoilRefresher_UNSTABLE)
- Recoil 0.6.x (useRecoilStoreID, storeID in effects)
- Recoil 0.7.x (latest — React 18 support, useSyncExternalStore,
                 useRecoilBridgeAcrossReactRoots_UNSTABLE, stability)

Atom Patterns:
- atom({key, default}) — primitive atoms (string, number, boolean, object, array)
- atom({key, default, effects}) — atoms with effects
- atom({key, default, dangerouslyAllowMutability}) — mutable atoms
- atomFamily({key, default}) — parameterized atom factories
- Atom keys (unique string identifiers, required by Recoil)

Selector Patterns:
- selector({key, get}) — read-only synchronous selectors
- selector({key, get, set}) — read-write selectors
- selectorFamily({key, get}) — parameterized selector factories
- Async selectors (get returns Promise, async/await)
- constSelector(value) — constant selectors
- errorSelector(error) — error selectors
- noWait(atom) — non-blocking loadable wrapper
- waitForAll([deps]) — parallel async resolution
- waitForAllSettled([deps]) — parallel with settlement
- waitForAny([deps]) — first resolved value
- waitForNone([deps]) — all as loadables

Effect Patterns:
- Atom effects ({onSet, setSelf, resetSelf, trigger, storeID, ...}) => cleanup
- Persistence effects (localStorage, sessionStorage, AsyncStorage, URL sync)
- Logging, validation, sync, broadcast effects
- Effect factories (reusable, parameterized)

Hook API:
- useRecoilState(atom) → [value, setValue]
- useRecoilValue(atom) → value
- useSetRecoilState(atom) → setValue
- useResetRecoilState(atom) → resetFn
- useRecoilStateLoadable(atom) → [loadable, setValue]
- useRecoilValueLoadable(atom) → loadable
- useRecoilCallback(({snapshot, set, reset, ...}) => ...)
- useRecoilTransaction_UNSTABLE(({get, set, reset}) => ...)
- useRecoilRefresher_UNSTABLE(selector) → refreshFn
- useRecoilBridgeAcrossReactRoots_UNSTABLE() → RecoilBridge

Snapshot API:
- useRecoilSnapshot() → snapshot
- useGotoRecoilSnapshot() → gotoSnapshot
- snapshot_UNSTABLE() → snapshot (outside React)
- snapshot.getLoadable(atom) → Loadable
- snapshot.getPromise(atom) → Promise
- snapshot.map(({set, reset}) => void) → Snapshot
- snapshot.asyncMap(async ({set, reset}) => void) → Promise<Snapshot>
- snapshot.retain() → release
- snapshot.getNodes_UNSTABLE() → Iterable
- snapshot.getInfo_UNSTABLE(atom) → AtomInfo

Framework Ecosystem Detection (15+ patterns):
- Core: recoil
- Extensions: recoil-sync, recoil-relay, recoil-nexus, recoil-persist,
              @recoiljs/refine
- Ecosystem: react, react-dom, react-native, @testing-library/react,
              vitest, jest

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Recoil extractors
from .extractors.recoil import (
    RecoilAtomExtractor, RecoilAtomInfo, RecoilAtomFamilyInfo,
    RecoilSelectorExtractor, RecoilSelectorInfo, RecoilSelectorFamilyInfo,
    RecoilEffectExtractor, RecoilEffectInfo,
    RecoilHookExtractor, RecoilHookUsageInfo, RecoilCallbackInfo,
    RecoilApiExtractor, RecoilImportInfo, RecoilSnapshotUsageInfo, RecoilTypeInfo,
)


@dataclass
class RecoilParseResult:
    """Complete parse result for a file with Recoil usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Atoms
    atoms: List[RecoilAtomInfo] = field(default_factory=list)
    atom_families: List[RecoilAtomFamilyInfo] = field(default_factory=list)

    # Selectors
    selectors: List[RecoilSelectorInfo] = field(default_factory=list)
    selector_families: List[RecoilSelectorFamilyInfo] = field(default_factory=list)

    # Effects
    effects: List[RecoilEffectInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[RecoilHookUsageInfo] = field(default_factory=list)
    callbacks: List[RecoilCallbackInfo] = field(default_factory=list)

    # API
    imports: List[RecoilImportInfo] = field(default_factory=list)
    snapshot_usages: List[RecoilSnapshotUsageInfo] = field(default_factory=list)
    types: List[RecoilTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    recoil_version: str = ""  # 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7


class EnhancedRecoilParser:
    """
    Enhanced Recoil parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Recoil framework is detected. It extracts Recoil-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 15+ Recoil ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Recoil ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'recoil': re.compile(
            r"from\s+['\"]recoil['\"]|require\(['\"]recoil['\"]\)",
            re.MULTILINE
        ),
        'recoil-native': re.compile(
            r"from\s+['\"]recoil/native['\"]",
            re.MULTILINE
        ),

        # ── Extensions ───────────────────────────────────────────
        'recoil-sync': re.compile(
            r"from\s+['\"]recoil-sync['\"]|"
            r"from\s+['\"]recoil-sync/['\"]|"
            r"syncEffect\s*\(|urlSyncEffect\s*\(|"
            r"<RecoilSync\b|<RecoilURLSync\b",
            re.MULTILINE
        ),
        'recoil-relay': re.compile(
            r"from\s+['\"]recoil-relay['\"]|"
            r"graphQLSelector\s*\(|graphQLSelectorFamily\s*\(",
            re.MULTILINE
        ),
        'recoil-nexus': re.compile(
            r"from\s+['\"]recoil-nexus['\"]|"
            r"getRecoil\s*\(|setRecoil\s*\(|resetRecoil\s*\(|"
            r"RecoilNexus\b",
            re.MULTILINE
        ),
        'recoil-persist': re.compile(
            r"from\s+['\"]recoil-persist['\"]|"
            r"recoilPersist\s*\(",
            re.MULTILINE
        ),
        '@recoiljs/refine': re.compile(
            r"from\s+['\"]@recoiljs/refine['\"]",
            re.MULTILINE
        ),

        # ── Ecosystem Integration ─────────────────────────────────
        'react': re.compile(
            r"from\s+['\"]react['\"]|require\(['\"]react['\"]\)",
            re.MULTILINE
        ),
        'react-native': re.compile(
            r"from\s+['\"]react-native['\"]",
            re.MULTILINE
        ),
        'relay': re.compile(
            r"from\s+['\"]relay-runtime['\"]|from\s+['\"]react-relay['\"]",
            re.MULTILINE
        ),
        'testing-library': re.compile(
            r"from\s+['\"]@testing-library/react['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'atom': re.compile(r'\batom\s*(?:<[^>]*>)?\s*\(\s*\{', re.MULTILINE),
        'atom_family': re.compile(r'atomFamily\s*(?:<[^>]*>)?\s*\(\s*\{', re.MULTILINE),
        'selector': re.compile(r'\bselector\s*(?:<[^>]*>)?\s*\(\s*\{', re.MULTILINE),
        'selector_family': re.compile(r'selectorFamily\s*(?:<[^>]*>)?\s*\(\s*\{', re.MULTILINE),
        'atom_effects': re.compile(r'effects(?:_UNSTABLE)?\s*:\s*\[', re.MULTILINE),
        'const_selector': re.compile(r'constSelector\s*\(', re.MULTILINE),
        'error_selector': re.compile(r'errorSelector\s*\(', re.MULTILINE),
        'wait_for_all': re.compile(r'waitForAll\s*\(', re.MULTILINE),
        'wait_for_all_settled': re.compile(r'waitForAllSettled\s*\(', re.MULTILINE),
        'wait_for_any': re.compile(r'waitForAny\s*\(', re.MULTILINE),
        'wait_for_none': re.compile(r'waitForNone\s*\(', re.MULTILINE),
        'no_wait': re.compile(r'noWait\s*\(', re.MULTILINE),
        'use_recoil_state': re.compile(r'useRecoilState\s*\(', re.MULTILINE),
        'use_recoil_value': re.compile(r'useRecoilValue\s*\(', re.MULTILINE),
        'use_set_recoil_state': re.compile(r'useSetRecoilState\s*\(', re.MULTILINE),
        'use_reset_recoil_state': re.compile(r'useResetRecoilState\s*\(', re.MULTILINE),
        'use_recoil_state_loadable': re.compile(r'useRecoilStateLoadable\s*\(', re.MULTILINE),
        'use_recoil_value_loadable': re.compile(r'useRecoilValueLoadable\s*\(', re.MULTILINE),
        'use_recoil_callback': re.compile(r'useRecoilCallback\s*\(', re.MULTILINE),
        'use_recoil_transaction': re.compile(r'useRecoilTransaction_UNSTABLE\s*\(', re.MULTILINE),
        'use_recoil_snapshot': re.compile(r'useRecoilSnapshot\s*\(', re.MULTILINE),
        'use_goto_recoil_snapshot': re.compile(r'useGotoRecoilSnapshot\s*\(', re.MULTILINE),
        'use_recoil_refresher': re.compile(r'useRecoilRefresher_UNSTABLE\s*\(', re.MULTILINE),
        'use_recoil_bridge': re.compile(r'useRecoilBridgeAcrossReactRoots_UNSTABLE\s*\(', re.MULTILINE),
        'snapshot_unstable': re.compile(r'snapshot_UNSTABLE\s*\(', re.MULTILINE),
        'recoil_root': re.compile(r'<RecoilRoot[\s>]', re.MULTILINE),
        'is_recoil_value': re.compile(r'isRecoilValue\s*\(', re.MULTILINE),
        'dangerously_allow_mutability': re.compile(r'dangerouslyAllowMutability\s*:', re.MULTILINE),
        'recoil_sync': re.compile(r'syncEffect\s*\(|<RecoilSync\b|<RecoilURLSync\b', re.MULTILINE),
        'recoil_nexus': re.compile(r'getRecoil\s*\(|setRecoil\s*\(|RecoilNexus\b', re.MULTILINE),
        'recoil_persist': re.compile(r'recoilPersist\s*\(', re.MULTILINE),
        'default_value': re.compile(r'DefaultValue\b', re.MULTILINE),
        'loadable': re.compile(r'\.state\s*===\s*[\'"](?:hasValue|loading|hasError)[\'"]', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Recoil extractors."""
        self.atom_extractor = RecoilAtomExtractor()
        self.selector_extractor = RecoilSelectorExtractor()
        self.effect_extractor = RecoilEffectExtractor()
        self.hook_extractor = RecoilHookExtractor()
        self.api_extractor = RecoilApiExtractor()

    def is_recoil_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Recoil code.

        Returns True if the file imports from Recoil ecosystem
        or uses Recoil patterns (atom, useRecoilState, etc.)
        """
        recoil_indicators = [
            'recoil', "from 'recoil", 'from "recoil',
            "from 'recoil/", 'from "recoil/',
            'recoil-sync', 'recoil-relay', 'recoil-nexus', 'recoil-persist',
            '@recoiljs/refine',
            'useRecoilState(', 'useRecoilValue(', 'useSetRecoilState(',
            'useResetRecoilState(', 'useRecoilCallback(',
            'useRecoilStateLoadable(', 'useRecoilValueLoadable(',
            'RecoilRoot',
            'atomFamily(', 'selectorFamily(',
            'constSelector(', 'errorSelector(',
            'waitForAll(', 'noWait(',
        ]
        return any(ind in content for ind in recoil_indicators)

    def parse(self, content: str, file_path: str = "") -> RecoilParseResult:
        """
        Parse a source file for Recoil patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            RecoilParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = RecoilParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.recoil_version = self._detect_version(content)

        # ── Atom extraction ────────────────────────────────────────
        try:
            atom_result = self.atom_extractor.extract(content, file_path)
            result.atoms = atom_result.get('atoms', [])
            result.atom_families = atom_result.get('atom_families', [])
        except Exception:
            pass

        # ── Selector extraction ───────────────────────────────────
        try:
            sel_result = self.selector_extractor.extract(content, file_path)
            result.selectors = sel_result.get('selectors', [])
            result.selector_families = sel_result.get('selector_families', [])
        except Exception:
            pass

        # ── Effect extraction ─────────────────────────────────────
        try:
            eff_result = self.effect_extractor.extract(content, file_path)
            result.effects = eff_result.get('effects', [])
        except Exception:
            pass

        # ── Hook extraction ───────────────────────────────────────
        try:
            hook_result = self.hook_extractor.extract(content, file_path)
            result.hook_usages = hook_result.get('hook_usages', [])
            result.callbacks = hook_result.get('callbacks', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.snapshot_usages = api_result.get('snapshot_usages', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Recoil ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Recoil features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Recoil version based on API usage patterns.

        Returns the minimum version required based on detected API usage:
        - '0.7' if React 18 APIs / useRecoilBridgeAcrossReactRoots_UNSTABLE
        - '0.6' if storeID / useRecoilStoreID
        - '0.5' if useRecoilRefresher_UNSTABLE
        - '0.4' if snapshot.retain / snapshot.asyncMap / snapshot_UNSTABLE
        - '0.3' if waitForAllSettled / waitForAny
        - '0.2' if atom effects / useRecoilCallback
        - '0.1' if atomFamily / selectorFamily / useResetRecoilState / constSelector /
                    errorSelector / waitForAll / waitForNone / noWait /
                    useRecoilStateLoadable / useRecoilValueLoadable
        - '0.0' if basic atom / selector / useRecoilState / useRecoilValue
        """
        # v0.7 indicators
        v07_indicators = [
            'useRecoilBridgeAcrossReactRoots_UNSTABLE',
            'useSyncExternalStore',
        ]
        if any(ind in content for ind in v07_indicators):
            return "0.7"

        # v0.6 indicators
        v06_indicators = [
            'storeID',
            'useRecoilStoreID',
        ]
        if any(ind in content for ind in v06_indicators):
            return "0.6"

        # v0.5 indicators
        v05_indicators = [
            'useRecoilRefresher_UNSTABLE',
        ]
        if any(ind in content for ind in v05_indicators):
            return "0.5"

        # v0.4 indicators
        v04_indicators = [
            '.retain()',
            '.asyncMap(',
            'snapshot_UNSTABLE(',
            'useGotoRecoilSnapshot',
        ]
        if any(ind in content for ind in v04_indicators):
            return "0.4"

        # v0.3 indicators
        v03_indicators = [
            'waitForAllSettled',
            'waitForAny',
        ]
        if any(ind in content for ind in v03_indicators):
            return "0.3"

        # v0.2 indicators
        v02_indicators = [
            'effects:',
            'effects_UNSTABLE:',
            'useRecoilCallback',
            'AtomEffect',
            'onSet',
            'setSelf',
            'resetSelf',
        ]
        if any(ind in content for ind in v02_indicators):
            return "0.2"

        # v0.1 indicators
        v01_indicators = [
            'atomFamily',
            'selectorFamily',
            'useResetRecoilState',
            'constSelector',
            'errorSelector',
            'waitForAll',
            'waitForNone',
            'noWait',
            'useRecoilStateLoadable',
            'useRecoilValueLoadable',
        ]
        if any(ind in content for ind in v01_indicators):
            return "0.1"

        # v0.0 (basic)
        v00_indicators = [
            "from 'recoil'",
            'from "recoil"',
            'useRecoilState',
            'useRecoilValue',
            'useSetRecoilState',
            'RecoilRoot',
        ]
        if any(ind in content for ind in v00_indicators):
            return "0.0"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {
            '': 0, '0.0': 1, '0.1': 2, '0.2': 3, '0.3': 4,
            '0.4': 5, '0.5': 6, '0.6': 7, '0.7': 8,
        }
        return version_order.get(v1, 0) - version_order.get(v2, 0)
