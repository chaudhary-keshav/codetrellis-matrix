"""
NgRx Store Extractor for CodeTrellis

Extracts NgRx store configuration and setup patterns:
- StoreModule.forRoot() / forFeature() (class-based, NgRx v1-v15)
- provideStore() / provideState() (standalone, NgRx v15+)
- Store injection and usage (store.dispatch(), store.select(), store.pipe())
- StoreDevtoolsModule / provideStoreDevtools()
- ComponentStore (NgRx v12+): setState, patchState, updater, select, effect
- SignalStore (NgRx v16+): signalStore, withState, withComputed, withMethods,
  withHooks, patchState, signalStoreFeature

Supports:
- NgRx 1.x-4.x (legacy patterns: StoreModule.provideStore)
- NgRx 4.x-7.x (StoreModule.forRoot/forFeature)
- NgRx 8.x-11.x (createReducer, createAction)
- NgRx 12.x-15.x (ComponentStore, standalone APIs)
- NgRx 16.x-19.x (SignalStore, functional APIs)

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NgrxStoreInfo:
    """Information about an NgRx store module configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    setup_method: str = ""  # forRoot, forFeature, provideStore, provideState
    feature_name: str = ""  # feature key for forFeature/provideState
    reducer_names: List[str] = field(default_factory=list)
    has_devtools: bool = False
    has_router_store: bool = False
    has_effects: bool = False
    has_entity: bool = False
    meta_reducers: List[str] = field(default_factory=list)
    runtime_checks: List[str] = field(default_factory=list)
    is_standalone: bool = False  # provideStore vs StoreModule
    is_exported: bool = False


@dataclass
class NgrxComponentStoreInfo:
    """Information about an NgRx ComponentStore usage."""
    name: str
    file: str = ""
    line_number: int = 0
    state_type: str = ""  # TypeScript state interface name
    updaters: List[str] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    has_patch_state: bool = False
    has_set_state: bool = False
    patch_state_calls: List[Dict] = field(default_factory=list)  # v4.54: {name, fields, line}
    updater_details: List[Dict] = field(default_factory=list)  # v4.54: {name, param_type, line}
    is_exported: bool = False


@dataclass
class NgrxSignalStoreInfo:
    """Information about an NgRx SignalStore usage."""
    name: str
    file: str = ""
    line_number: int = 0
    state_fields: List[str] = field(default_factory=list)
    computed_fields: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    with_hooks: bool = False
    features: List[str] = field(default_factory=list)  # signalStoreFeature names
    has_entities: bool = False  # withEntities()
    has_devtools: bool = False  # withDevtools()
    computed_details: List[Dict] = field(default_factory=list)  # v4.54: {name, deps, line}
    method_details: List[Dict] = field(default_factory=list)  # v4.54: {name, return_type, is_async, line}
    is_exported: bool = False


@dataclass
class NgrxDevToolsConfig:
    """Information about NgRx DevTools configuration (v4.54)."""
    name: str  # StoreDevtoolsModule or provideStoreDevtools
    file: str = ""
    line_number: int = 0
    max_age: Optional[int] = None
    log_only: Optional[str] = None  # expression e.g. 'environment.production'
    action_sanitizer: bool = False
    state_sanitizer: bool = False
    serialize: bool = False
    features: List[str] = field(default_factory=list)  # pause, lock, persist, etc.
    is_standalone: bool = False


class NgrxStoreExtractor:
    """
    Extracts NgRx store configuration patterns from source code.

    Detects:
    - StoreModule.forRoot() / forFeature() (class-based modules)
    - provideStore() / provideState() (standalone)
    - Store injection and select/dispatch usage
    - StoreDevtoolsModule / provideStoreDevtools
    - ComponentStore (v12+)
    - SignalStore (v16+)
    - Meta-reducers and runtime checks
    """

    # StoreModule.forRoot / forFeature
    STORE_MODULE_PATTERN = re.compile(
        r'StoreModule\s*\.\s*(forRoot|forFeature)\s*\(\s*'
        r'(?:[\'"](\w+)[\'"],?\s*)?',
        re.MULTILINE
    )

    # provideStore / provideState (standalone)
    PROVIDE_STORE_PATTERN = re.compile(
        r'(provideStore|provideState)\s*\(\s*'
        r'(?:[\'"](\w+)[\'"],?\s*)?',
        re.MULTILINE
    )

    # ComponentStore class
    COMPONENT_STORE_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w+)\s+extends\s+ComponentStore\s*<\s*(\w+)',
        re.MULTILINE
    )

    # signalStore
    SIGNAL_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*signalStore\s*\(',
        re.MULTILINE
    )

    # StoreDevtoolsModule / provideStoreDevtools
    DEVTOOLS_PATTERN = re.compile(
        r'StoreDevtoolsModule|provideStoreDevtools',
        re.MULTILINE
    )

    # ComponentStore updater
    UPDATER_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\s*=\s*this\.updater\s*[<(]',
        re.MULTILINE
    )

    # ComponentStore select
    CS_SELECT_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\$?\s*=\s*this\.select\s*[<(]',
        re.MULTILINE
    )

    # ComponentStore effect
    CS_EFFECT_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\s*=\s*this\.effect\s*[<(]',
        re.MULTILINE
    )

    # signalStore with* features
    WITH_STATE_PATTERN = re.compile(
        r'withState\s*(?:<[^>]*>)?\s*\(\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )
    WITH_COMPUTED_PATTERN = re.compile(
        r'withComputed\s*\(\s*(?:\([^)]*\)\s*=>\s*\(\s*\{|[^)]*=>)',
        re.MULTILINE
    )
    WITH_METHODS_PATTERN = re.compile(
        r'withMethods\s*\(\s*(?:\([^)]*\)\s*=>\s*\(\s*\{|[^)]*=>)',
        re.MULTILINE
    )
    WITH_HOOKS_PATTERN = re.compile(
        r'withHooks\s*\(',
        re.MULTILINE
    )
    WITH_ENTITIES_PATTERN = re.compile(
        r'withEntities\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # EffectsModule / provideEffects
    EFFECTS_PATTERN = re.compile(
        r'EffectsModule\s*\.\s*forRoot|EffectsModule\s*\.\s*forFeature|provideEffects',
        re.MULTILINE
    )

    # EntityModule / provideEntity
    ENTITY_PATTERN = re.compile(
        r'EntityDataModule|provideEntityData|@ngrx/entity',
        re.MULTILINE
    )

    # RouterStoreModule
    ROUTER_STORE_PATTERN = re.compile(
        r'StoreRouterConnectingModule|provideRouterStore|routerReducer',
        re.MULTILINE
    )

    # Meta-reducers
    META_REDUCER_PATTERN = re.compile(
        r'metaReducers\s*[=:]\s*\[([^\]]*)\]',
        re.MULTILINE | re.DOTALL
    )

    # Runtime checks
    RUNTIME_CHECKS_PATTERN = re.compile(
        r'runtimeChecks\s*:\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Reducer map keys
    REDUCER_MAP_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:\w+Reducer|\w+\.reducer)',
        re.MULTILINE
    )

    # v4.54: DevTools configuration extraction
    DEVTOOLS_CONFIG_PATTERN = re.compile(
        r'(?:StoreDevtoolsModule\s*\.\s*instrument|provideStoreDevtools)\s*\(\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # v4.54: DevTools maxAge
    DEVTOOLS_MAX_AGE_PATTERN = re.compile(
        r'maxAge\s*:\s*(\d+)',
        re.MULTILINE
    )

    # v4.54: DevTools logOnly
    DEVTOOLS_LOG_ONLY_PATTERN = re.compile(
        r'logOnly\s*:\s*([^\s,}]+)',
        re.MULTILINE
    )

    # v4.54: DevTools actionSanitizer/stateSanitizer
    DEVTOOLS_SANITIZER_PATTERN = re.compile(
        r'(actionSanitizer|stateSanitizer)\s*:',
        re.MULTILINE
    )

    # v4.54: DevTools serialize option
    DEVTOOLS_SERIALIZE_PATTERN = re.compile(
        r'serialize\s*:',
        re.MULTILINE
    )

    # v4.54: DevTools features (pause, lock, persist, etc.)
    DEVTOOLS_FEATURES_PATTERN = re.compile(
        r'features\s*:\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # v4.54: ComponentStore patchState calls with field names
    CS_PATCH_STATE_PATTERN = re.compile(
        r'(?:this\.)?patchState\s*\(\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # v4.54: ComponentStore updater with param type
    CS_UPDATER_DETAIL_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\s*=\s*this\.updater\s*(?:<([^>]*)>)?\s*\(\s*'
        r'\(\s*state\s*(?::\s*\w+)?\s*,\s*(\w+)\s*(?::\s*([^)]+))?\s*\)',
        re.MULTILINE
    )

    # v4.54: Cross-file Store.select() references
    STORE_SELECT_REF_PATTERN = re.compile(
        r'(?:this\.)?store\.select\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # v4.54: Cross-file Store.dispatch() references
    STORE_DISPATCH_REF_PATTERN = re.compile(
        r'(?:this\.)?store\.dispatch\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # v4.54: withComputed signal details (name: computed(() => ...))
    WITH_COMPUTED_DETAIL_PATTERN = re.compile(
        r'(\w+)\s*:\s*computed\s*\(\s*\(\s*\)\s*=>\s*',
        re.MULTILINE
    )

    # v4.54: withMethods detail extraction (name: (args) => { } or async name())
    WITH_METHODS_DETAIL_PATTERN = re.compile(
        r'(?:async\s+)?(\w+)\s*(?:\([^)]*\)\s*(?::\s*([^{,]+))?\s*\{|:\s*(?:rxMethod|function))',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract all NgRx store information from source code."""
        result: Dict = {
            'stores': [],
            'component_stores': [],
            'signal_stores': [],
            'devtools_configs': [],  # v4.54
            'store_select_refs': [],  # v4.54: cross-file Store.select()
            'store_dispatch_refs': [],  # v4.54: cross-file Store.dispatch()
        }

        has_devtools = bool(self.DEVTOOLS_PATTERN.search(content))
        has_effects = bool(self.EFFECTS_PATTERN.search(content))
        has_entity = bool(self.ENTITY_PATTERN.search(content))
        has_router_store = bool(self.ROUTER_STORE_PATTERN.search(content))

        # ── StoreModule.forRoot / forFeature ──────────────────
        for match in self.STORE_MODULE_PATTERN.finditer(content):
            method = match.group(1)
            feature_name = match.group(2) or ""

            # Try to find reducer names nearby
            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]
            reducer_names = [m.group(1) for m in self.REDUCER_MAP_PATTERN.finditer(block)]

            # Meta-reducers
            meta_match = self.META_REDUCER_PATTERN.search(block)
            meta_reducers = []
            if meta_match:
                meta_text = meta_match.group(1)
                meta_reducers = [m.strip() for m in meta_text.split(',') if m.strip()]

            # Runtime checks
            rt_match = self.RUNTIME_CHECKS_PATTERN.search(block)
            runtime_checks = []
            if rt_match:
                rt_text = rt_match.group(1)
                runtime_checks = re.findall(r'(\w+)\s*:\s*true', rt_text)

            store = NgrxStoreInfo(
                name=f"StoreModule.{method}",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                setup_method=method,
                feature_name=feature_name,
                reducer_names=reducer_names,
                has_devtools=has_devtools,
                has_effects=has_effects,
                has_entity=has_entity,
                has_router_store=has_router_store,
                meta_reducers=meta_reducers,
                runtime_checks=runtime_checks,
                is_standalone=False,
            )
            result['stores'].append(store)

        # ── provideStore / provideState ──────────────────────
        for match in self.PROVIDE_STORE_PATTERN.finditer(content):
            method = match.group(1)
            feature_name = match.group(2) or ""

            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]
            reducer_names = [m.group(1) for m in self.REDUCER_MAP_PATTERN.finditer(block)]

            # Meta-reducers
            meta_match = self.META_REDUCER_PATTERN.search(block)
            meta_reducers = []
            if meta_match:
                meta_text = meta_match.group(1)
                meta_reducers = [m.strip() for m in meta_text.split(',') if m.strip()]

            # Runtime checks
            rt_match = self.RUNTIME_CHECKS_PATTERN.search(block)
            runtime_checks = []
            if rt_match:
                rt_text = rt_match.group(1)
                runtime_checks = re.findall(r'(\w+)\s*:\s*true', rt_text)

            store = NgrxStoreInfo(
                name=method,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                setup_method=method,
                feature_name=feature_name,
                reducer_names=reducer_names,
                has_devtools=has_devtools,
                has_effects=has_effects,
                has_entity=has_entity,
                has_router_store=has_router_store,
                meta_reducers=meta_reducers,
                runtime_checks=runtime_checks,
                is_standalone=True,
            )
            result['stores'].append(store)

        # ── ComponentStore ────────────────────────────────────
        for match in self.COMPONENT_STORE_PATTERN.finditer(content):
            cs_name = match.group(1)
            state_type = match.group(2)

            # Scan class body for updaters, selectors, effects
            class_start = match.start()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]

            updaters = [m.group(1) for m in self.UPDATER_PATTERN.finditer(class_body)]
            selectors = [m.group(1) for m in self.CS_SELECT_PATTERN.finditer(class_body)]
            effects = [m.group(1) for m in self.CS_EFFECT_PATTERN.finditer(class_body)]

            # v4.54: Extract patchState call details
            patch_state_calls = []
            for ps_match in self.CS_PATCH_STATE_PATTERN.finditer(class_body):
                fields_text = ps_match.group(1)
                fields = re.findall(r'(\w+)\s*[,:=]', fields_text)
                line = class_body[:ps_match.start()].count('\n') + content[:class_start].count('\n') + 1
                patch_state_calls.append({
                    'fields': fields[:10],
                    'line': line,
                })

            # v4.54: Extract updater details (param type)
            updater_details = []
            for ud_match in self.CS_UPDATER_DETAIL_PATTERN.finditer(class_body):
                ud_name = ud_match.group(1)
                generic_type = ud_match.group(2) or ""
                param_name = ud_match.group(3) or ""
                param_type = ud_match.group(4) or generic_type or ""
                line = class_body[:ud_match.start()].count('\n') + content[:class_start].count('\n') + 1
                updater_details.append({
                    'name': ud_name,
                    'param_type': param_type.strip(),
                    'line': line,
                })

            cs = NgrxComponentStoreInfo(
                name=cs_name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                state_type=state_type,
                updaters=updaters,
                selectors=selectors,
                effects=effects,
                has_patch_state='patchState' in class_body,
                has_set_state='setState' in class_body,
                patch_state_calls=patch_state_calls,
                updater_details=updater_details,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['component_stores'].append(cs)

        # ── SignalStore ───────────────────────────────────────
        for match in self.SIGNAL_STORE_PATTERN.finditer(content):
            ss_name = match.group(1)
            block_start = match.start()
            block_end = min(block_start + 3000, len(content))
            block = content[block_start:block_end]

            # Extract state fields from withState({ key: value })
            state_fields = []
            ws_match = self.WITH_STATE_PATTERN.search(block)
            if ws_match:
                state_text = ws_match.group(1)
                state_fields = re.findall(r'(\w+)\s*:', state_text)

            has_computed = bool(self.WITH_COMPUTED_PATTERN.search(block))
            has_methods = bool(self.WITH_METHODS_PATTERN.search(block))
            has_hooks = bool(self.WITH_HOOKS_PATTERN.search(block))
            has_entities = bool(self.WITH_ENTITIES_PATTERN.search(block))

            # v4.54: Deep extraction of computed field names and dependencies
            computed_fields = []
            computed_details = []
            if has_computed:
                comp_matches = re.findall(r'(\w+)\s*:\s*computed\(', block)
                computed_fields = comp_matches

                # Extract dependencies from computed signals (what store signals they read)
                # Pattern: withComputed(({ dep1, dep2 }) => ({
                comp_deps_match = re.search(
                    r'withComputed\s*\(\s*\(\s*\{([^}]*)\}\s*\)\s*=>',
                    block, re.DOTALL
                )
                comp_deps = []
                if comp_deps_match:
                    deps_text = comp_deps_match.group(1)
                    comp_deps = [d.strip() for d in deps_text.split(',') if d.strip()]

                for cf in computed_fields:
                    # Try to find the computed body to extract signal reads
                    cf_pattern = re.compile(
                        rf'{re.escape(cf)}\s*:\s*computed\s*\(\s*\(\s*\)\s*=>\s*([^\n,}}]+)',
                        re.DOTALL
                    )
                    cf_match = cf_pattern.search(block)
                    signal_reads = []
                    if cf_match:
                        cf_body = cf_match.group(1)
                        # Find signal reads like `dep()` within the computed body
                        signal_reads = re.findall(r'(\w+)\s*\(\s*\)', cf_body)
                        signal_reads = [sr for sr in signal_reads if sr not in ('computed', 'effect', 'inject')]

                    computed_details.append({
                        'name': cf,
                        'deps': comp_deps if comp_deps else signal_reads[:10],
                    })

            # v4.54: Deep extraction of method names and return types
            methods = []
            method_details = []
            if has_methods:
                meth_matches = re.findall(r'(\w+)\s*(?::\s*\(|:\s*rxMethod)', block)
                methods = [m for m in meth_matches if m not in ('withMethods', 'withComputed', 'withState')]

                # Extract method details with async detection and return type hints
                methods_section = ""
                meth_section_match = re.search(
                    r'withMethods\s*\(\s*(?:\([^)]*\)\s*=>\s*\(\s*\{|[^)]*=>\s*\(\s*\{)(.*?)(?:\}\s*\)\s*\))',
                    block, re.DOTALL
                )
                if meth_section_match:
                    methods_section = meth_section_match.group(1)

                for meth_name in methods:
                    is_async = bool(re.search(
                        rf'async\s+{re.escape(meth_name)}\s*\(', methods_section
                    ))
                    # Try to detect return type
                    ret_match = re.search(
                        rf'{re.escape(meth_name)}\s*\([^)]*\)\s*:\s*(\w+)',
                        methods_section
                    )
                    return_type = ret_match.group(1) if ret_match else ""
                    is_rxmethod = bool(re.search(
                        rf'{re.escape(meth_name)}\s*:\s*rxMethod', block
                    ))

                    method_details.append({
                        'name': meth_name,
                        'return_type': return_type,
                        'is_async': is_async,
                        'is_rxmethod': is_rxmethod,
                    })

            # Signal store features
            features = re.findall(r'(signalStoreFeature|withDevtools|withEntities|withCallState|withRequestStatus)\s*\(', block)

            ss = NgrxSignalStoreInfo(
                name=ss_name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                state_fields=state_fields,
                computed_fields=computed_fields,
                methods=methods,
                with_hooks=has_hooks,
                features=features,
                has_entities=has_entities,
                has_devtools='withDevtools' in block,
                computed_details=computed_details,
                method_details=method_details,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['signal_stores'].append(ss)

        # ── v4.54: DevTools Configuration ────────────────────
        for dt_match in self.DEVTOOLS_CONFIG_PATTERN.finditer(content):
            config_text = dt_match.group(1)
            line_number = content[:dt_match.start()].count('\n') + 1

            # Determine if standalone (provideStoreDevtools vs StoreDevtoolsModule)
            is_standalone = 'provideStoreDevtools' in content[max(0, dt_match.start() - 30):dt_match.start() + 30]
            name = 'provideStoreDevtools' if is_standalone else 'StoreDevtoolsModule'

            # maxAge
            max_age_match = self.DEVTOOLS_MAX_AGE_PATTERN.search(config_text)
            max_age = int(max_age_match.group(1)) if max_age_match else None

            # logOnly
            log_only_match = self.DEVTOOLS_LOG_ONLY_PATTERN.search(config_text)
            log_only = log_only_match.group(1).strip() if log_only_match else None

            # Sanitizers
            sanitizers = [m.group(1) for m in self.DEVTOOLS_SANITIZER_PATTERN.finditer(config_text)]
            has_action_sanitizer = 'actionSanitizer' in sanitizers
            has_state_sanitizer = 'stateSanitizer' in sanitizers

            # serialize
            has_serialize = bool(self.DEVTOOLS_SERIALIZE_PATTERN.search(config_text))

            # features
            features_list = []
            feat_match = self.DEVTOOLS_FEATURES_PATTERN.search(config_text)
            if feat_match:
                feat_text = feat_match.group(1)
                features_list = re.findall(r'(\w+)\s*:', feat_text)

            dt_config = NgrxDevToolsConfig(
                name=name,
                file=file_path,
                line_number=line_number,
                max_age=max_age,
                log_only=log_only,
                action_sanitizer=has_action_sanitizer,
                state_sanitizer=has_state_sanitizer,
                serialize=has_serialize,
                features=features_list,
                is_standalone=is_standalone,
            )
            result['devtools_configs'].append(dt_config)

        # ── v4.54: Cross-file Store.select() refs ────────────
        for sel_match in self.STORE_SELECT_REF_PATTERN.finditer(content):
            selector_name = sel_match.group(1)
            line_number = content[:sel_match.start()].count('\n') + 1
            result['store_select_refs'].append({
                'selector': selector_name,
                'file': file_path,
                'line': line_number,
            })

        # ── v4.54: Cross-file Store.dispatch() refs ──────────
        for disp_match in self.STORE_DISPATCH_REF_PATTERN.finditer(content):
            action_name = disp_match.group(1)
            line_number = content[:disp_match.start()].count('\n') + 1
            result['store_dispatch_refs'].append({
                'action': action_name,
                'file': file_path,
                'line': line_number,
            })

        return result

    def _find_class_end(self, content: str, start: int) -> int:
        """Find the end of a class body by brace counting."""
        brace_count = 0
        in_class = False
        i = start
        while i < len(content):
            ch = content[i]
            if ch == '{':
                brace_count += 1
                in_class = True
            elif ch == '}':
                brace_count -= 1
                if in_class and brace_count == 0:
                    return i + 1
            i += 1
        return min(start + 3000, len(content))
