"""
Pinia API Extractor for CodeTrellis

Extracts Pinia API usage patterns:
- Import patterns (pinia, @pinia/nuxt, @pinia/testing)
- TypeScript types (StoreDefinition, StateTree, PiniaPluginContext, etc.)
- Integration patterns (Nuxt modules, Vue DevTools, testing utilities)
- Migration patterns (Vuex → Pinia)
- Deprecated API detection

Supports:
- Pinia v0.x-v2.x import patterns
- @pinia/nuxt module integration
- @pinia/testing (createTestingPinia)
- TypeScript StoreDefinition, Store, StateTree, etc.

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PiniaImportInfo:
    """Information about a Pinia-related import."""
    source: str
    file: str = ""
    line_number: int = 0
    imported_names: List[str] = field(default_factory=list)
    is_default: bool = False
    is_type_only: bool = False


@dataclass
class PiniaIntegrationInfo:
    """Information about a Pinia ecosystem integration."""
    integration_type: str  # nuxt, testing, devtools, orm, persistedstate, router
    file: str = ""
    line_number: int = 0
    library: str = ""
    pattern: str = ""


@dataclass
class PiniaTypeInfo:
    """Information about a Pinia TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_category: str = ""  # store_definition, state_tree, plugin_context, getter_tree, action_tree
    type_expression: str = ""


class PiniaApiExtractor:
    """
    Extracts Pinia API patterns including imports, types, and integrations.

    Detects:
    - Imports from 'pinia' (defineStore, storeToRefs, createPinia, mapState, etc.)
    - Imports from '@pinia/nuxt' (Nuxt integration)
    - Imports from '@pinia/testing' (createTestingPinia, TestingOptions)
    - Imports from 'pinia-plugin-persistedstate'
    - Imports from 'pinia-orm'
    - TypeScript types (StoreDefinition, Store, StateTree, PiniaPluginContext,
                        DefineStoreOptions, _GettersTree, _ActionsTree, StoreGeneric,
                        PiniaCustomProperties, PiniaCustomStateProperties)
    - Vuex migration patterns (mapState, mapGetters → storeToRefs)
    - Vue DevTools integration detection
    """

    # ES6 import pattern
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]|"
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]|"
        r"const\s+\{([^}]+)\}\s*=\s*require\(['\"]([^'\"]+)['\"]\))",
        re.MULTILINE
    )

    # Pinia-related import sources
    PINIA_SOURCES = {
        'pinia', '@pinia/nuxt', '@pinia/testing',
        'pinia-plugin-persistedstate', 'pinia-plugin-persist',
        'pinia-plugin-debounce', '@pinia/plugin-debounce',
        'pinia-orm', '@pinia/orm',
        'pinia/dist/pinia',
    }

    # TypeScript Pinia types
    TS_TYPE_PATTERN = re.compile(
        r'(?::\s*|extends\s+|implements\s+|<\s*)'
        r'(StoreDefinition|Store(?:Generic)?|StateTree|'
        r'PiniaPluginContext|PiniaPlugin|PiniaCustomProperties|'
        r'PiniaCustomStateProperties|DefineStoreOptions(?:InPlugin)?|'
        r'_GettersTree|_ActionsTree|StoreActions|StoreGetters|StoreState|'
        r'_StoreWithState|_StoreWithGetters|_ExtractStateFromSetupStore|'
        r'_ExtractGettersFromSetupStore|_ExtractActionsFromSetupStore)',
        re.MULTILINE
    )

    # Nuxt module integration
    NUXT_MODULE_PATTERN = re.compile(
        r"modules\s*:\s*\[[^\]]*['\"]@pinia/nuxt['\"][^\]]*\]|"
        r"from\s+['\"]@pinia/nuxt['\"]|"
        r"defineNuxtConfig.*pinia",
        re.MULTILINE | re.DOTALL
    )

    # Testing integration
    TESTING_PATTERN = re.compile(
        r"createTestingPinia|@pinia/testing|setActivePinia|"
        r"createPinia\s*\(\s*\).*test",
        re.MULTILINE | re.IGNORECASE
    )

    # Vuex migration indicators
    VUEX_MIGRATION_PATTERN = re.compile(
        r"from\s+['\"]vuex['\"]|"
        r"mapState\s*\(|mapGetters\s*\(|mapActions\s*\(|mapMutations\s*\(",
        re.MULTILINE
    )

    # mapState/mapStores/mapGetters/mapActions/mapWritableState from pinia
    PINIA_MAP_HELPERS = re.compile(
        r'\b(mapStores|mapState|mapGetters|mapActions|mapWritableState)\s*\(',
        re.MULTILINE
    )

    # Vue DevTools
    DEVTOOLS_PATTERN = re.compile(
        r"__VUE_DEVTOOLS__|@vue/devtools|customInspector|addTimeline|"
        r"devtools\s*:\s*true",
        re.MULTILINE
    )

    # Type category mapping
    TYPE_CATEGORIES = {
        'StoreDefinition': 'store_definition',
        'Store': 'store_definition',
        'StoreGeneric': 'store_definition',
        'StateTree': 'state_tree',
        'PiniaPluginContext': 'plugin_context',
        'PiniaPlugin': 'plugin_context',
        'PiniaCustomProperties': 'plugin_context',
        'PiniaCustomStateProperties': 'plugin_context',
        'DefineStoreOptions': 'store_definition',
        'DefineStoreOptionsInPlugin': 'store_definition',
        '_GettersTree': 'getter_tree',
        '_ActionsTree': 'action_tree',
        'StoreActions': 'action_tree',
        'StoreGetters': 'getter_tree',
        'StoreState': 'state_tree',
        '_StoreWithState': 'store_definition',
        '_StoreWithGetters': 'store_definition',
        '_ExtractStateFromSetupStore': 'state_tree',
        '_ExtractGettersFromSetupStore': 'getter_tree',
        '_ExtractActionsFromSetupStore': 'action_tree',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Pinia API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'imports', 'integrations', 'types' lists
        """
        imports: List[PiniaImportInfo] = []
        integrations: List[PiniaIntegrationInfo] = []
        types: List[PiniaTypeInfo] = []

        # Imports
        for match in self.IMPORT_PATTERN.finditer(content):
            # Named imports
            named = match.group(1) or match.group(5)
            source = match.group(2) or match.group(4) or match.group(6)
            default_name = match.group(3)

            if not source:
                continue

            # Check if source is Pinia-related
            is_pinia = any(source.startswith(s) for s in self.PINIA_SOURCES)
            if not is_pinia and 'pinia' not in source.lower():
                continue

            line = content[:match.start()].count('\n') + 1
            is_type_only = 'import type' in content[max(0, match.start() - 20):match.start() + 20]

            if named:
                names = [n.strip().split(' as ')[0].strip() for n in named.split(',') if n.strip()]
            elif default_name:
                names = [default_name]
            else:
                names = []

            imports.append(PiniaImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                imported_names=names,
                is_default=bool(default_name),
                is_type_only=is_type_only,
            ))

        # Integrations
        if self.NUXT_MODULE_PATTERN.search(content):
            integrations.append(PiniaIntegrationInfo(
                integration_type="nuxt",
                file=file_path,
                library="@pinia/nuxt",
                pattern="nuxt_module",
            ))

        if self.TESTING_PATTERN.search(content):
            integrations.append(PiniaIntegrationInfo(
                integration_type="testing",
                file=file_path,
                library="@pinia/testing",
                pattern="createTestingPinia",
            ))

        if self.DEVTOOLS_PATTERN.search(content):
            integrations.append(PiniaIntegrationInfo(
                integration_type="devtools",
                file=file_path,
                library="vue-devtools",
                pattern="devtools",
            ))

        if self.VUEX_MIGRATION_PATTERN.search(content):
            integrations.append(PiniaIntegrationInfo(
                integration_type="vuex_migration",
                file=file_path,
                library="vuex",
                pattern="vuex_coexistence",
            ))

        # Pinia map helpers
        for map_match in self.PINIA_MAP_HELPERS.finditer(content):
            helper_name = map_match.group(1)
            line = content[:map_match.start()].count('\n') + 1
            integrations.append(PiniaIntegrationInfo(
                integration_type="map_helper",
                file=file_path,
                library="pinia",
                pattern=helper_name,
            ))

        # TypeScript types
        for type_match in self.TS_TYPE_PATTERN.finditer(content):
            type_name = type_match.group(1)
            line = content[:type_match.start()].count('\n') + 1
            category = self.TYPE_CATEGORIES.get(type_name, 'unknown')
            types.append(PiniaTypeInfo(
                name=type_name,
                file=file_path,
                line_number=line,
                type_category=category,
                type_expression=content[type_match.start():type_match.end()],
            ))

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
        }
