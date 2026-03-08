"""
NgRx API Extractor for CodeTrellis

Extracts NgRx ecosystem API usage and configuration:
- @ngrx/store imports and usage
- @ngrx/effects imports and registration
- @ngrx/entity (EntityAdapter, EntityState, sorted/unsorted)
- @ngrx/store-devtools configuration
- @ngrx/router-store (routerReducer, RouterState, selectRouteParams)
- @ngrx/component-store imports
- @ngrx/signals (signalStore, withState, withComputed, withMethods)
- @ngrx/operators (concatLatestFrom)
- @ngrx/eslint-plugin
- @ngrx/schematics
- ngrx-store-freeze (legacy)
- TypeScript types (Action, ActionReducerMap, createReducer, on)

Supports:
- NgRx 4.x-19.x package structure (@ngrx/* scoped packages)
- Legacy ngrx packages (ngrx-store-freeze, @ngrx/store-devtools)
- Community packages (ngrx-entity-relationship, ngrx-forms, ngrx-translate)

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NgrxEntityInfo:
    """Information about @ngrx/entity usage."""
    name: str
    file: str = ""
    line_number: int = 0
    entity_type: str = ""  # TypeScript entity type
    sort_comparer: bool = False
    select_id: bool = False
    adapter_methods: List[str] = field(default_factory=list)
    has_entity_state: bool = False
    is_exported: bool = False


@dataclass
class NgrxRouterStoreInfo:
    """Information about @ngrx/router-store usage."""
    name: str
    file: str = ""
    line_number: int = 0
    serializer_type: str = ""  # DefaultRouterStateSerializer, MinimalRouterStateSerializer, custom
    selectors: List[str] = field(default_factory=list)
    has_custom_serializer: bool = False
    is_standalone: bool = False  # provideRouterStore vs StoreRouterConnectingModule


class NgrxApiExtractor:
    """
    Extracts NgRx ecosystem API usage and configuration.

    Detects:
    - @ngrx/* package imports
    - Entity adapter usage and operations
    - Router store configuration
    - TypeScript type usage
    - Community package integration
    """

    # @ngrx/* package imports
    NGRX_IMPORT_PATTERN = re.compile(
        r"(?:import|from)\s+['\"](@ngrx/[\w-]+)['\"]",
        re.MULTILINE
    )

    # EntityAdapter creation (handles optional TS type annotation e.g. adapter: EntityAdapter<X> = ...)
    ENTITY_ADAPTER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*(?::\s*\w+(?:<[^>]*>)?\s*)?=\s*'
        r'createEntityAdapter\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # EntityAdapter method usage
    ENTITY_METHOD_PATTERN = re.compile(
        r'(?:adapter|entityAdapter|\w+Adapter)\s*\.\s*(addOne|addMany|addAll|setOne|setMany|setAll|'
        r'removeOne|removeMany|removeAll|updateOne|updateMany|upsertOne|upsertMany|mapOne|map)\s*\(',
        re.MULTILINE
    )

    # EntityState usage
    ENTITY_STATE_PATTERN = re.compile(
        r'EntityState\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # sortComparer in entity adapter
    SORT_COMPARER_PATTERN = re.compile(
        r'sortComparer\s*:',
        re.MULTILINE
    )

    # selectId in entity adapter
    SELECT_ID_PATTERN = re.compile(
        r'selectId\s*:',
        re.MULTILINE
    )

    # StoreRouterConnectingModule / provideRouterStore
    ROUTER_STORE_PATTERN = re.compile(
        r'(StoreRouterConnectingModule|provideRouterStore)\s*',
        re.MULTILINE
    )

    # Router serializer
    ROUTER_SERIALIZER_PATTERN = re.compile(
        r'(MinimalRouterStateSerializer|DefaultRouterStateSerializer|CustomRouterStateSerializer)\s*',
        re.MULTILINE
    )

    # Router store selectors
    ROUTER_SELECTOR_PATTERN = re.compile(
        r'(selectRouteParams|selectRouteParam|selectRouteData|'
        r'selectQueryParams|selectQueryParam|selectFragment|'
        r'selectUrl|selectTitle|getRouterSelectors|getSelectors)',
        re.MULTILINE
    )

    # Community packages
    COMMUNITY_PACKAGE_PATTERN = re.compile(
        r"from\s+['\"]("
        r"ngrx-store-freeze|"
        r"ngrx-entity-relationship|"
        r"ngrx-forms|"
        r"ngrx-translate|"
        r"ngrx-store-logger|"
        r"@ngrx-traits/common|"
        r"ngrx-store-localstorage"
        r")['\"]",
        re.MULTILINE
    )

    # createReducer / on()
    CREATE_REDUCER_PATTERN = re.compile(
        r'createReducer\s*\(',
        re.MULTILINE
    )

    ON_PATTERN = re.compile(
        r'\bon\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # ActionReducerMap
    ACTION_REDUCER_MAP_PATTERN = re.compile(
        r'ActionReducerMap\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # createFeature (v12.1+)
    CREATE_FEATURE_USAGE_PATTERN = re.compile(
        r'createFeature\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract all NgRx API usage from source code."""
        result: Dict = {
            'packages': [],
            'entities': [],
            'router_stores': [],
            'community_packages': [],
            'reducer_count': 0,
            'on_handlers': [],
            'action_reducer_maps': [],
            'has_create_feature': False,
        }

        # ── Package imports ───────────────────────────────────
        packages = list(set(m.group(1) for m in self.NGRX_IMPORT_PATTERN.finditer(content)))
        result['packages'] = packages

        # ── Entity adapters ───────────────────────────────────
        for match in self.ENTITY_ADAPTER_PATTERN.finditer(content):
            name = match.group(1)
            entity_type = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]

            # Find adapter methods used anywhere in file
            adapter_methods = list(set(m.group(1) for m in self.ENTITY_METHOD_PATTERN.finditer(content)))

            entity = NgrxEntityInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                entity_type=entity_type,
                sort_comparer=bool(self.SORT_COMPARER_PATTERN.search(block)),
                select_id=bool(self.SELECT_ID_PATTERN.search(block)),
                adapter_methods=adapter_methods,
                has_entity_state=bool(self.ENTITY_STATE_PATTERN.search(content)),
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['entities'].append(entity)

        # ── Router store ──────────────────────────────────────
        for match in self.ROUTER_STORE_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            serializer_match = self.ROUTER_SERIALIZER_PATTERN.search(content)
            serializer = serializer_match.group(1) if serializer_match else ""

            router_selectors = list(set(
                m.group(1) for m in self.ROUTER_SELECTOR_PATTERN.finditer(content)
            ))

            rs = NgrxRouterStoreInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                serializer_type=serializer,
                selectors=router_selectors,
                has_custom_serializer='CustomRouterStateSerializer' in content,
                is_standalone=name == 'provideRouterStore',
            )
            result['router_stores'].append(rs)

        # ── Community packages ────────────────────────────────
        for match in self.COMMUNITY_PACKAGE_PATTERN.finditer(content):
            pkg = match.group(1)
            if pkg not in result['community_packages']:
                result['community_packages'].append(pkg)

        # ── Reducer information ───────────────────────────────
        result['reducer_count'] = len(self.CREATE_REDUCER_PATTERN.findall(content))
        result['on_handlers'] = [m.group(1) for m in self.ON_PATTERN.finditer(content)]
        result['action_reducer_maps'] = [m.group(1) for m in self.ACTION_REDUCER_MAP_PATTERN.finditer(content)]
        result['has_create_feature'] = bool(self.CREATE_FEATURE_USAGE_PATTERN.search(content))

        return result
