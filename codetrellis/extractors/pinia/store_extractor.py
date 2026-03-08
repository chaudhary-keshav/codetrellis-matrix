"""
Pinia Store Extractor for CodeTrellis

Extracts Pinia store definitions and configuration patterns:
- defineStore() with Options API (state, getters, actions)
- defineStore() with Setup API (Composition API: ref, computed, function)
- Store IDs (string identifiers)
- State shape extraction (fields + types)
- HMR (Hot Module Replacement) acceptHMR pattern
- Store composition (using other stores)
- TypeScript generic stores defineStore<Id, S, G, A>()

Supports:
- Pinia v0.x (early API, @pinia/composition, vuex-like)
- Pinia v1.x (first stable, Options + Setup stores, SSR)
- Pinia v2.x (Vue 3 official, defineStore with auto-id, storeToRefs,
              $patch/$reset/$subscribe/$onAction, plugin API, DevTools)
- Pinia v3.x (planned: improved TypeScript, tree-shaking,
              modular architecture)

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PiniaStoreInfo:
    """Information about a Pinia store definition."""
    name: str
    store_id: str = ""
    file: str = ""
    line_number: int = 0
    api_style: str = ""  # options, setup
    state_fields: List[str] = field(default_factory=list)
    getters: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    has_typescript: bool = False
    type_name: str = ""  # TypeScript interface/type for state
    is_exported: bool = False
    uses_other_stores: List[str] = field(default_factory=list)
    has_hmr: bool = False
    has_persist: bool = False
    has_reset: bool = False
    has_subscribe: bool = False
    has_on_action: bool = False
    pinia_version: str = ""


class PiniaStoreExtractor:
    """
    Extracts Pinia store definitions from source code.

    Detects:
    - defineStore('id', { state, getters, actions }) — Options API
    - defineStore('id', () => { ... }) — Setup API (Composition)
    - TypeScript generic defineStore<Id, S, G, A>()
    - Store composition (using other stores inside)
    - HMR patterns (import.meta.hot?.accept, acceptHMR)
    - $patch, $reset, $subscribe, $onAction usage
    - Persist plugin integration
    """

    # defineStore('id', { ... }) or defineStore('id', () => { ... })
    DEFINE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'defineStore\s*(?:<[^>]*>)?\s*\(\s*'
        r"['\"](\w[\w-]*)['\"]",
        re.MULTILINE
    )

    # defineStore with only callback (auto-id in Pinia v2+)
    DEFINE_STORE_AUTO_ID_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'defineStore\s*(?:<[^>]*>)?\s*\(\s*\(',
        re.MULTILINE
    )

    # Options API: { state: () => ({...}), getters: {...}, actions: {...} }
    OPTIONS_API_PATTERN = re.compile(
        r'defineStore\s*(?:<[^>]*>)?\s*\(\s*'
        r"['\"][\w-]+['\"]\s*,\s*\{",
        re.MULTILINE
    )

    # Setup API: defineStore('id', () => { ... })
    SETUP_API_PATTERN = re.compile(
        r'defineStore\s*(?:<[^>]*>)?\s*\(\s*'
        r"['\"][\w-]+['\"]\s*,\s*\(\s*\)\s*=>",
        re.MULTILINE
    )

    # State fields in Options API: state: () => ({ field1: ..., field2: ... })
    STATE_FIELD_PATTERN = re.compile(
        r'state\s*:\s*\(\s*\)\s*=>\s*\(\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Getters in Options API
    GETTER_PATTERN = re.compile(
        r'getters\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Actions in Options API
    ACTION_PATTERN = re.compile(
        r'actions\s*:\s*\{([^}]*(?:\{[^}]*(?:\{[^}]*\}[^}]*)*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Setup API: ref/reactive for state
    SETUP_REF_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*(?:ref|reactive|shallowRef|shallowReactive)\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Setup API: computed for getters
    SETUP_COMPUTED_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*computed\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Setup API: function/const for actions
    SETUP_FUNCTION_PATTERN = re.compile(
        r'(?:function\s+(\w+)|(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>)',
        re.MULTILINE
    )

    # HMR pattern
    HMR_PATTERN = re.compile(
        r'import\.meta\.hot|acceptHMR\s*\(',
        re.MULTILINE
    )

    # Store composition (using another store)
    USE_STORE_PATTERN = re.compile(
        r'(?:const|let)\s+\w+\s*=\s*(use\w+Store)\s*\(\)',
        re.MULTILINE
    )

    # Export pattern
    EXPORT_PATTERN = re.compile(
        r'export\s+(?:const|let|var|function)\s+(\w+)',
        re.MULTILINE
    )

    # Persist integration
    PERSIST_PATTERN = re.compile(
        r'persist\s*:\s*(?:true|\{)',
        re.MULTILINE
    )

    # TypeScript generic store
    TS_GENERIC_PATTERN = re.compile(
        r'defineStore\s*<([^>]+)>',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Pinia store definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'stores' list
        """
        stores: List[PiniaStoreInfo] = []

        # Find all defineStore calls
        for match in self.DEFINE_STORE_PATTERN.finditer(content):
            var_name = match.group(1)
            store_id = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            store = PiniaStoreInfo(
                name=var_name,
                store_id=store_id,
                file=file_path,
                line_number=line_number,
            )

            # Determine API style
            # Check if this specific store uses Setup API
            store_region = content[match.start():]
            if self.SETUP_API_PATTERN.search(store_region[:200]):
                store.api_style = "setup"
                self._extract_setup_members(store_region, store)
            elif self.OPTIONS_API_PATTERN.search(store_region[:200]):
                store.api_style = "options"
                self._extract_options_members(store_region, store)

            # Check for TypeScript
            ts_match = self.TS_GENERIC_PATTERN.search(store_region[:200])
            if ts_match:
                store.has_typescript = True
                store.type_name = ts_match.group(1).strip()

            # Check for export
            export_line = content[max(0, match.start() - 50):match.start()]
            store.is_exported = 'export' in export_line

            # Check for HMR
            store.has_hmr = bool(self.HMR_PATTERN.search(content))

            # Check for persist
            store.has_persist = bool(self.PERSIST_PATTERN.search(store_region[:1000]))

            # Check for $reset, $subscribe, $onAction usage
            store.has_reset = '$reset' in content
            store.has_subscribe = '$subscribe' in content
            store.has_on_action = '$onAction' in content

            # Check for store composition
            for use_match in self.USE_STORE_PATTERN.finditer(store_region[:2000]):
                used_store = use_match.group(1)
                if used_store != var_name and used_store not in store.uses_other_stores:
                    store.uses_other_stores.append(used_store)

            stores.append(store)

        return {'stores': stores}

    def _extract_options_members(self, region: str, store: PiniaStoreInfo) -> None:
        """Extract state fields, getters, and actions from Options API store."""
        # State fields
        state_match = self.STATE_FIELD_PATTERN.search(region[:3000])
        if state_match:
            state_body = state_match.group(1)
            for field_match in re.finditer(r'(\w+)\s*:', state_body):
                field_name = field_match.group(1)
                if field_name not in store.state_fields:
                    store.state_fields.append(field_name)

        # Getters
        getter_match = self.GETTER_PATTERN.search(region[:5000])
        if getter_match:
            getter_body = getter_match.group(1)
            for g_match in re.finditer(r'(\w+)\s*\(', getter_body):
                getter_name = g_match.group(1)
                if getter_name not in store.getters:
                    store.getters.append(getter_name)

        # Actions
        action_match = self.ACTION_PATTERN.search(region[:8000])
        if action_match:
            action_body = action_match.group(1)
            for a_match in re.finditer(r'(?:async\s+)?(\w+)\s*\(', action_body):
                action_name = a_match.group(1)
                if action_name not in ('async', 'await', 'if', 'else', 'try', 'catch', 'this', 'return', 'const', 'let', 'var', 'function', 'new', 'throw', 'Error', 'Promise', 'console', 'set', 'get'):
                    if action_name not in store.actions:
                        store.actions.append(action_name)

    def _extract_setup_members(self, region: str, store: PiniaStoreInfo) -> None:
        """Extract ref/reactive (state), computed (getters), functions (actions) from Setup API."""
        # Limit search region (up to closing of defineStore)
        search_region = region[:5000]

        # State: ref(), reactive()
        for ref_match in self.SETUP_REF_PATTERN.finditer(search_region):
            field_name = ref_match.group(1)
            if field_name not in store.state_fields:
                store.state_fields.append(field_name)

        # Getters: computed()
        for comp_match in self.SETUP_COMPUTED_PATTERN.finditer(search_region):
            getter_name = comp_match.group(1)
            if getter_name not in store.getters:
                store.getters.append(getter_name)

        # Actions: functions
        for fn_match in self.SETUP_FUNCTION_PATTERN.finditer(search_region):
            fn_name = fn_match.group(1) or fn_match.group(2)
            if fn_name and fn_name not in ('async', 'await', 'if', 'else', 'try', 'catch', 'return', 'const', 'let', 'var'):
                if fn_name not in store.actions and fn_name not in store.state_fields and fn_name not in store.getters:
                    store.actions.append(fn_name)
