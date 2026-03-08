"""
EnhancedNgrxParser v1.0 - Comprehensive NgRx state management parser using all extractors.

This parser integrates all NgRx extractors to provide complete parsing of
NgRx state management usage across Angular/TypeScript source files.
It runs as a supplementary layer on top of the TypeScript parser,
extracting NgRx-specific semantics.

Supports:
- NgRx 1.x-3.x (legacy: class-based actions, ngrx-store-freeze)
- NgRx 4.x-7.x (StoreModule.forRoot/forFeature, @Effect() decorator,
                  createFeatureSelector, combineReducers, class actions)
- NgRx 8.x-11.x (createAction, createReducer, on(), createEffect,
                   createSelector, props<T>(), emptyProps())
- NgRx 12.x-15.x (ComponentStore: setState/patchState/updater/select/effect,
                    createFeature auto-selectors, standalone APIs: provideStore/
                    provideState/provideEffects/provideStoreDevtools,
                    createActionGroup v13.2+, concatLatestFrom)
- NgRx 16.x-19.x (SignalStore: signalStore/withState/withComputed/withMethods/
                    withHooks/signalStoreFeature/withEntities/withDevtools,
                    selectSignal, functional effects, rxMethod,
                    Angular Signals integration, inject-based)

Store Patterns:
- StoreModule.forRoot() / .forFeature() (class-based module setup)
- provideStore() / provideState() (standalone setup, v15+)
- Store<State> injection, store.select(), store.dispatch()
- Meta-reducers, runtime checks (strictStateImmutability, etc.)
- StoreDevtoolsModule / provideStoreDevtools()
- ComponentStore (v12+): updater, select, effect, patchState, setState
- SignalStore (v16+): withState, withComputed, withMethods, withHooks,
  signalStoreFeature, withEntities, patchState

Action Patterns:
- createAction('[Source] Event', props<T>()) (v8+)
- createActionGroup({ source, events }) (v13.2+)
- Legacy class-based actions (implements Action, type + payload)
- [Source] Event naming convention

Effect Patterns:
- createEffect() with Actions + ofType + RxJS pipe (v8+)
- Legacy @Effect() decorator (v4-v7, deprecated v12+)
- Functional effects with inject (v16+)
- dispatch: false (non-dispatching effects)
- concatLatestFrom / withLatestFrom for store access in effects
- ComponentStore effects (this.effect())

Selector Patterns:
- createSelector() with input selectors and projector
- createFeatureSelector<State>('key')
- createFeature() auto-generated selectors (v12.1+)
- Factory selectors (parameterized)
- selectSignal() / store.selectSignal() (v16+)
- Memoization and selector composition

Entity Patterns:
- @ngrx/entity: createEntityAdapter, EntityState, CRUD operations
- sortComparer, selectId customization
- Entity selectors (selectAll, selectEntities, selectIds, selectTotal)

Router Store:
- @ngrx/router-store: routerReducer, RouterState, MinimalRouterStateSerializer
- Router selectors (selectRouteParams, selectQueryParams, etc.)

Framework Ecosystem Detection (25+ patterns):
- Core: @ngrx/store, @ngrx/effects, @ngrx/entity
- DevTools: @ngrx/store-devtools
- Router: @ngrx/router-store
- ComponentStore: @ngrx/component-store
- Signals: @ngrx/signals
- Operators: @ngrx/operators
- Schematics: @ngrx/schematics
- ESLint: @ngrx/eslint-plugin
- Community: ngrx-store-freeze, ngrx-forms, ngrx-entity-relationship

Optional AST support via tree-sitter-typescript.
Optional LSP support via angular-language-server.

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all NgRx extractors
from .extractors.ngrx import (
    NgrxStoreExtractor, NgrxStoreInfo, NgrxComponentStoreInfo, NgrxSignalStoreInfo,
    NgrxDevToolsConfig,
    NgrxEffectExtractor, NgrxEffectInfo, NgrxComponentStoreEffectInfo,
    NgrxSelectorExtractor, NgrxSelectorInfo, NgrxFeatureSelectorInfo,
    NgrxActionExtractor, NgrxActionInfo, NgrxActionGroupInfo,
    NgrxApiExtractor, NgrxEntityInfo, NgrxRouterStoreInfo,
)


@dataclass
class NgrxParseResult:
    """Complete parse result for a file with NgRx usage."""
    file_path: str
    file_type: str = "ts"  # ts, spec.ts

    # Store
    stores: List[NgrxStoreInfo] = field(default_factory=list)
    component_stores: List[NgrxComponentStoreInfo] = field(default_factory=list)
    signal_stores: List[NgrxSignalStoreInfo] = field(default_factory=list)

    # Actions
    actions: List[NgrxActionInfo] = field(default_factory=list)
    action_groups: List[NgrxActionGroupInfo] = field(default_factory=list)

    # Effects
    effects: List[NgrxEffectInfo] = field(default_factory=list)
    component_store_effects: List[NgrxComponentStoreEffectInfo] = field(default_factory=list)
    registered_effects: List[str] = field(default_factory=list)

    # Selectors
    selectors: List[NgrxSelectorInfo] = field(default_factory=list)
    feature_selectors: List[NgrxFeatureSelectorInfo] = field(default_factory=list)
    select_signal_count: int = 0

    # Entity
    entities: List[NgrxEntityInfo] = field(default_factory=list)

    # Router Store
    router_stores: List[NgrxRouterStoreInfo] = field(default_factory=list)

    # v4.54: DevTools configuration
    devtools_configs: List[NgrxDevToolsConfig] = field(default_factory=list)

    # v4.54: Cross-file store references (dependency graph)
    store_select_refs: List[Dict[str, Any]] = field(default_factory=list)
    store_dispatch_refs: List[Dict[str, Any]] = field(default_factory=list)

    # v4.54: ESLint NgRx rules
    eslint_ngrx_rules: List[Dict[str, Any]] = field(default_factory=list)

    # API / Metadata
    packages: List[str] = field(default_factory=list)
    community_packages: List[str] = field(default_factory=list)
    reducer_count: int = 0
    on_handlers: List[str] = field(default_factory=list)
    has_create_feature: bool = False

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    ngrx_version: str = ""  # legacy, v4-v7, v8-v11, v12-v15, v16+


class EnhancedNgrxParser:
    """
    Enhanced NgRx parser that uses all extractors.

    This parser runs AFTER the TypeScript parser when NgRx framework is detected.
    It extracts NgRx-specific semantics that the language parser cannot capture.

    Framework detection supports 25+ NgRx ecosystem libraries across:
    - Core (@ngrx/store, @ngrx/effects, @ngrx/entity)
    - DevTools (@ngrx/store-devtools)
    - Router (@ngrx/router-store)
    - ComponentStore (@ngrx/component-store)
    - Signals (@ngrx/signals)
    - Operators (@ngrx/operators)
    - Schematics (@ngrx/schematics)
    - ESLint (@ngrx/eslint-plugin)
    - Community (ngrx-store-freeze, ngrx-forms, etc.)

    Optional AST: tree-sitter-typescript
    Optional LSP: angular-language-server
    """

    # NgRx ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────
        'ngrx-store': re.compile(
            r"from\s+['\"]@ngrx/store['\"]|"
            r"StoreModule|provideStore|Store\s*<|createReducer|createAction|"
            r"ActionReducerMap|MetaReducer",
            re.MULTILINE
        ),
        'ngrx-effects': re.compile(
            r"from\s+['\"]@ngrx/effects['\"]|"
            r"EffectsModule|provideEffects|createEffect|"
            r"Actions\s*,|ofType\s*\(",
            re.MULTILINE
        ),
        'ngrx-entity': re.compile(
            r"from\s+['\"]@ngrx/entity['\"]|"
            r"createEntityAdapter|EntityState|EntityAdapter",
            re.MULTILINE
        ),

        # ── DevTools ─────────────────────────────────────────
        'ngrx-store-devtools': re.compile(
            r"from\s+['\"]@ngrx/store-devtools['\"]|"
            r"StoreDevtoolsModule|provideStoreDevtools",
            re.MULTILINE
        ),

        # ── Router ───────────────────────────────────────────
        'ngrx-router-store': re.compile(
            r"from\s+['\"]@ngrx/router-store['\"]|"
            r"StoreRouterConnectingModule|provideRouterStore|routerReducer|"
            r"RouterState|selectRouteParams",
            re.MULTILINE
        ),

        # ── ComponentStore ───────────────────────────────────
        'ngrx-component-store': re.compile(
            r"from\s+['\"]@ngrx/component-store['\"]|"
            r"ComponentStore\s*<|extends\s+ComponentStore",
            re.MULTILINE
        ),

        # ── Signals ──────────────────────────────────────────
        'ngrx-signals': re.compile(
            r"from\s+['\"]@ngrx/signals['\"]|"
            r"signalStore\s*\(|withState\s*\(|withComputed\s*\(|"
            r"withMethods\s*\(|signalStoreFeature|patchState\s*\(",
            re.MULTILINE
        ),

        # ── Operators ────────────────────────────────────────
        'ngrx-operators': re.compile(
            r"from\s+['\"]@ngrx/operators['\"]|"
            r"concatLatestFrom",
            re.MULTILINE
        ),

        # ── Schematics ──────────────────────────────────────
        'ngrx-schematics': re.compile(
            r"@ngrx/schematics",
            re.MULTILINE
        ),

        # ── ESLint ───────────────────────────────────────────
        'ngrx-eslint-plugin': re.compile(
            r"@ngrx/eslint-plugin|ngrx/",
            re.MULTILINE
        ),

        # ── Community ────────────────────────────────────────
        'ngrx-store-freeze': re.compile(
            r"ngrx-store-freeze|storeFreeze",
            re.MULTILINE
        ),
        'ngrx-forms': re.compile(
            r"from\s+['\"]ngrx-forms['\"]|NgrxFormsModule",
            re.MULTILINE
        ),
        'ngrx-entity-relationship': re.compile(
            r"from\s+['\"]ngrx-entity-relationship['\"]|"
            r"rootEntity|relatedEntity|childEntity",
            re.MULTILINE
        ),
        'ngrx-store-localstorage': re.compile(
            r"from\s+['\"]ngrx-store-localstorage['\"]|localStorageSync",
            re.MULTILINE
        ),
        'ngrx-translate': re.compile(
            r"from\s+['\"]ngrx-translate['\"]",
            re.MULTILINE
        ),
        'ngrx-store-logger': re.compile(
            r"from\s+['\"]ngrx-store-logger['\"]|storeLogger",
            re.MULTILINE
        ),

        # ── Angular Core (for context) ──────────────────────
        'angular': re.compile(
            r"from\s+['\"]@angular/core['\"]|@Component|@Injectable|@NgModule",
            re.MULTILINE
        ),
        'angular-router': re.compile(
            r"from\s+['\"]@angular/router['\"]|RouterModule|Routes",
            re.MULTILINE
        ),
        'rxjs': re.compile(
            r"from\s+['\"]rxjs['\"/]|Observable|Subject|BehaviorSubject",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'store_module': re.compile(r'StoreModule\s*\.\s*(?:forRoot|forFeature)', re.MULTILINE),
        'standalone_store': re.compile(r'provideStore\s*\(|provideState\s*\(', re.MULTILINE),
        'create_action': re.compile(r'createAction\s*\(', re.MULTILINE),
        'create_action_group': re.compile(r'createActionGroup\s*\(', re.MULTILINE),
        'create_reducer': re.compile(r'createReducer\s*\(', re.MULTILINE),
        'create_effect': re.compile(r'createEffect\s*\(', re.MULTILINE),
        'create_selector': re.compile(r'createSelector\s*\(', re.MULTILINE),
        'create_feature_selector': re.compile(r'createFeatureSelector\s*<', re.MULTILINE),
        'create_feature': re.compile(r'createFeature\s*\(', re.MULTILINE),
        'entity_adapter': re.compile(r'createEntityAdapter\s*<', re.MULTILINE),
        'component_store': re.compile(r'extends\s+ComponentStore\s*<', re.MULTILINE),
        'signal_store': re.compile(r'signalStore\s*\(', re.MULTILINE),
        'select_signal': re.compile(r'selectSignal\s*\(', re.MULTILINE),
        'functional_effects': re.compile(r'createEffect\s*\(\s*\(\s*\)', re.MULTILINE),
        'legacy_effects': re.compile(r'@Effect\s*\(', re.MULTILINE),
        'runtime_checks': re.compile(r'runtimeChecks\s*:', re.MULTILINE),
        'meta_reducers': re.compile(r'metaReducers\s*:', re.MULTILINE),
        'router_store': re.compile(r'routerReducer|StoreRouterConnectingModule|provideRouterStore', re.MULTILINE),
        'devtools': re.compile(r'StoreDevtoolsModule|provideStoreDevtools', re.MULTILINE),
        'with_entities': re.compile(r'withEntities\s*[<(]', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all NgRx extractors."""
        self.store_extractor = NgrxStoreExtractor()
        self.effect_extractor = NgrxEffectExtractor()
        self.selector_extractor = NgrxSelectorExtractor()
        self.action_extractor = NgrxActionExtractor()
        self.api_extractor = NgrxApiExtractor()

    def is_ngrx_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains NgRx code.

        Returns True if the file imports from NgRx ecosystem
        or uses NgRx patterns (createAction, createEffect, etc.)
        or is an ESLint config with @ngrx rules.
        """
        # Check ESLint config files for @ngrx rules
        eslint_files = [
            '.eslintrc', '.eslintrc.json', '.eslintrc.js', '.eslintrc.cjs',
            'eslint.config.js', 'eslint.config.mjs', 'eslint.config.ts',
        ]
        if any(file_path.endswith(ef) for ef in eslint_files):
            if '@ngrx' in content:
                return True

        ngrx_indicators = [
            '@ngrx/', 'createAction', 'createReducer', 'createEffect',
            'createSelector', 'createFeatureSelector', 'createFeature',
            'StoreModule', 'EffectsModule', 'provideStore', 'provideEffects',
            'provideState', 'ComponentStore', 'signalStore',
            'createActionGroup', 'createEntityAdapter', 'ofType',
            'ActionReducerMap', 'MetaReducer',
        ]
        return any(ind in content for ind in ngrx_indicators)

    def parse(self, content: str, file_path: str = "") -> NgrxParseResult:
        """
        Parse a source file for NgRx patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            NgrxParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.spec.ts'):
            file_type = "spec.ts"

        result = NgrxParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.ngrx_version = self._detect_version(content)

        # ── Store extraction ───────────────────────────────────
        try:
            store_result = self.store_extractor.extract(content, file_path)
            result.stores = store_result.get('stores', [])
            result.component_stores = store_result.get('component_stores', [])
            result.signal_stores = store_result.get('signal_stores', [])
            result.devtools_configs = store_result.get('devtools_configs', [])
            result.store_select_refs = store_result.get('store_select_refs', [])
            result.store_dispatch_refs = store_result.get('store_dispatch_refs', [])
        except Exception:
            pass

        # ── Action extraction ──────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.actions = action_result.get('actions', [])
            result.action_groups = action_result.get('action_groups', [])
        except Exception:
            pass

        # ── Effect extraction ──────────────────────────────────
        try:
            effect_result = self.effect_extractor.extract(content, file_path)
            result.effects = effect_result.get('effects', [])
            result.component_store_effects = effect_result.get('component_store_effects', [])
            result.registered_effects = effect_result.get('registered_effects', [])
        except Exception:
            pass

        # ── Selector extraction ────────────────────────────────
        try:
            sel_result = self.selector_extractor.extract(content, file_path)
            result.selectors = sel_result.get('selectors', [])
            result.feature_selectors = sel_result.get('feature_selectors', [])
            result.select_signal_count = sel_result.get('select_signal_count', 0)
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.packages = api_result.get('packages', [])
            result.entities = api_result.get('entities', [])
            result.router_stores = api_result.get('router_stores', [])
            result.community_packages = api_result.get('community_packages', [])
            result.reducer_count = api_result.get('reducer_count', 0)
            result.on_handlers = api_result.get('on_handlers', [])
            result.has_create_feature = api_result.get('has_create_feature', False)
        except Exception:
            pass

        # ── v4.54: ESLint NgRx rules detection ────────────────
        try:
            result.eslint_ngrx_rules = self._extract_eslint_ngrx_rules(content, file_path)
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which NgRx ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which NgRx features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect NgRx version based on API usage patterns.

        Returns:
            - 'v16+' if NgRx Signals/functional effects detected
            - 'v12-v15' if ComponentStore/createFeature/standalone detected
            - 'v8-v11' if createAction/createReducer/createEffect detected
            - 'v4-v7' if StoreModule but no createAction detected
            - 'legacy' if only legacy patterns
        """
        # v16+ indicators (SignalStore, selectSignal, functional effects)
        v16_indicators = [
            'signalStore', 'withState(', 'withComputed(', 'withMethods(',
            'selectSignal', '@ngrx/signals', 'signalStoreFeature',
            'rxMethod', 'withEntities(',
        ]
        if any(ind in content for ind in v16_indicators):
            return "v16+"

        # v12-v15 indicators (ComponentStore, createFeature, standalone)
        v12_indicators = [
            'ComponentStore', 'createFeature(', 'provideStore(', 'provideState(',
            'provideEffects(', 'provideStoreDevtools(', 'createActionGroup(',
            'concatLatestFrom',
        ]
        if any(ind in content for ind in v12_indicators):
            return "v12-v15"

        # v8-v11 indicators (createAction, createReducer, createEffect)
        v8_indicators = [
            'createAction(', 'createReducer(', 'createEffect(',
            'props<', 'emptyProps(', 'on(',
        ]
        if any(ind in content for ind in v8_indicators):
            return "v8-v11"

        # v4-v7 indicators (class-based patterns)
        v4_indicators = [
            'StoreModule', 'EffectsModule', '@Effect(',
            'implements Action', 'createFeatureSelector',
        ]
        if any(ind in content for ind in v4_indicators):
            return "v4-v7"

        # Legacy
        legacy_indicators = ['ngrx-store-freeze', '@ngrx/store']
        if any(ind in content for ind in legacy_indicators):
            return "legacy"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'legacy': 1, 'v4-v7': 2, 'v8-v11': 3, 'v12-v15': 4, 'v16+': 5}
        return version_order.get(v1, 0) - version_order.get(v2, 0)

    # v4.54: NgRx ESLint rule patterns
    ESLINT_NGRX_RULE_PATTERN = re.compile(
        r'["\'](@ngrx/[\w-]+)["\']'
        r'\s*:\s*["\']?(error|warn|off|\d+)["\']?',
        re.MULTILINE
    )

    # v4.54: ESLint extends @ngrx patterns
    ESLINT_NGRX_EXTENDS_PATTERN = re.compile(
        r'["\'](?:plugin:)?@ngrx/?([\w-]*)["\']',
        re.MULTILINE
    )

    # v4.54: Flat config @ngrx plugin detection
    ESLINT_NGRX_FLAT_CONFIG_PATTERN = re.compile(
        r'(?:from|require)\s*\(\s*["\']@ngrx/eslint-plugin["\']\s*\)|'
        r'ngrx\s*\.\s*configs\s*\.\s*(\w+)',
        re.MULTILINE
    )

    def _extract_eslint_ngrx_rules(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract NgRx ESLint rules from ESLint config files.

        Parses .eslintrc, .eslintrc.json, .eslintrc.js, eslint.config.js/ts/mjs
        for @ngrx/ rules and plugin configuration to detect team conventions.

        Returns:
            List of dicts with keys: rule, severity, file
        """
        # Only parse ESLint config files
        eslint_files = [
            '.eslintrc', '.eslintrc.json', '.eslintrc.js', '.eslintrc.cjs',
            '.eslintrc.yaml', '.eslintrc.yml',
            'eslint.config.js', 'eslint.config.mjs', 'eslint.config.cjs',
            'eslint.config.ts', 'eslint.config.mts',
        ]
        is_eslint_file = any(file_path.endswith(ef) for ef in eslint_files)
        if not is_eslint_file:
            return []

        rules: List[Dict[str, Any]] = []

        # Extract individual @ngrx/* rules
        for rule_match in self.ESLINT_NGRX_RULE_PATTERN.finditer(content):
            rule_name = rule_match.group(1)
            severity = rule_match.group(2)
            rules.append({
                'rule': rule_name,
                'severity': severity,
                'file': file_path,
            })

        # Extract extends presets
        for ext_match in self.ESLINT_NGRX_EXTENDS_PATTERN.finditer(content):
            preset_name = ext_match.group(1) or "recommended"
            rules.append({
                'rule': f'@ngrx/preset:{preset_name}',
                'severity': 'preset',
                'file': file_path,
            })

        # Extract flat config usage
        for flat_match in self.ESLINT_NGRX_FLAT_CONFIG_PATTERN.finditer(content):
            config_name = flat_match.group(1) or "all"
            rules.append({
                'rule': f'@ngrx/flat-config:{config_name}',
                'severity': 'config',
                'file': file_path,
            })

        return rules
