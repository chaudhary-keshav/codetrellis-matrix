"""
Redux Slice Extractor for CodeTrellis

Extracts Redux Toolkit slice definitions and patterns:
- createSlice with name, initialState, reducers, extraReducers
- Prepare callbacks for action payload customization
- createEntityAdapter (CRUD operations, normalized state)
- Auto-generated action creators (slice.actions)
- Selector generation (slice selectors in RTK 2.0+)
- Builder pattern extraReducers (addCase, addMatcher, addDefaultCase)
- Slice reducer export patterns

Supports:
- Redux Toolkit 1.0+ (createSlice, createEntityAdapter)
- Redux Toolkit 1.3+ (builder callback extraReducers)
- Redux Toolkit 1.9+ (slice selectors)
- Redux Toolkit 2.0+ (createSlice with selectors option)

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReduxSliceInfo:
    """Information about a Redux Toolkit slice."""
    name: str  # Variable name
    file: str = ""
    line_number: int = 0
    slice_name: str = ""  # name field value (string key in state)
    initial_state_fields: List[str] = field(default_factory=list)
    initial_state_types: List[str] = field(default_factory=list)  # TypeScript types
    reducers: List[str] = field(default_factory=list)
    prepare_callbacks: List[str] = field(default_factory=list)
    extra_reducers_cases: List[str] = field(default_factory=list)  # addCase thunk names
    extra_reducers_matchers: List[str] = field(default_factory=list)
    has_default_case: bool = False
    entity_adapter: str = ""  # Entity adapter name if used
    exported_actions: List[str] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)  # RTK 2.0 slice selectors
    is_exported: bool = False


@dataclass
class ReduxEntityAdapterInfo:
    """Information about a createEntityAdapter usage."""
    name: str
    file: str = ""
    line_number: int = 0
    entity_type: str = ""  # TypeScript entity type
    sort_comparer: str = ""  # Sort function name
    select_id: str = ""  # Custom ID selector
    crud_operations: List[str] = field(default_factory=list)  # addOne, updateMany, etc.
    selectors_generated: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class ReduxActionCreatorInfo:
    """Information about an exported Redux action creator."""
    name: str
    file: str = ""
    line_number: int = 0
    source_slice: str = ""
    action_type: str = ""  # sync, prepare
    is_exported: bool = False


class ReduxSliceExtractor:
    """
    Extracts Redux Toolkit slice definitions from source code.

    Detects:
    - createSlice with all configuration options
    - Entity adapters with CRUD operations
    - Action creator exports
    - RTK 2.0 slice selectors
    """

    # createSlice
    CREATE_SLICE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createSlice\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # createEntityAdapter
    CREATE_ENTITY_ADAPTER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createEntityAdapter\s*(?:<(\w+)>)?\s*\(',
        re.MULTILINE
    )

    # Action export: export const { action1, action2 } = sliceName.actions
    ACTION_EXPORT_PATTERN = re.compile(
        r'export\s+const\s+\{([^}]+)\}\s*=\s*(\w+)\.actions',
        re.MULTILINE
    )

    # Reducer export: export default sliceName.reducer
    REDUCER_EXPORT_PATTERN = re.compile(
        r'export\s+(?:default\s+)?(?:const\s+\w+\s*=\s*)?(\w+)\.reducer',
        re.MULTILINE
    )

    # createAction (standalone)
    CREATE_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createAction\s*(?:<[^>]*>)?\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # createReducer (standalone, legacy)
    CREATE_REDUCER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createReducer\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Entity adapter CRUD operations
    ENTITY_CRUD_OPS = [
        'addOne', 'addMany', 'setOne', 'setMany', 'setAll',
        'removeOne', 'removeMany', 'removeAll',
        'updateOne', 'updateMany', 'upsertOne', 'upsertMany',
    ]

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Redux slice patterns from source code."""
        slices = []
        entity_adapters = []
        action_creators = []

        # ── createSlice ───────────────────────────────────────────
        for m in self.CREATE_SLICE_PATTERN.finditer(content):
            var_name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            # Extract slice name
            name_match = re.search(r'name\s*:\s*[\'"]([^\'"]+)[\'"]', body)
            slice_name = name_match.group(1) if name_match else ""

            # Extract initialState fields
            state_fields = self._extract_initial_state(body)

            # Extract TS type for initial state
            state_types = self._extract_state_types(body, content[:m.start()])

            # Extract reducers
            reducers = self._extract_reducers(body)

            # Extract prepare callbacks
            prepare_callbacks = self._extract_prepare_callbacks(body)

            # Extract extraReducers cases
            extra_cases, extra_matchers, has_default = self._extract_extra_reducers(body)

            # Extract RTK 2.0 selectors
            selectors = self._extract_slice_selectors(body)

            # Check for entity adapter usage in reducers
            entity_adapter = ""
            for ea in entity_adapters:
                if ea.name in body:
                    entity_adapter = ea.name
                    break

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            slices.append(ReduxSliceInfo(
                name=var_name,
                file=file_path,
                line_number=line,
                slice_name=slice_name,
                initial_state_fields=state_fields[:30],
                initial_state_types=state_types[:10],
                reducers=reducers[:30],
                prepare_callbacks=prepare_callbacks[:15],
                extra_reducers_cases=extra_cases[:20],
                extra_reducers_matchers=extra_matchers[:10],
                has_default_case=has_default,
                entity_adapter=entity_adapter,
                selectors=selectors[:20],
                is_exported=is_exported,
            ))

        # ── createEntityAdapter ───────────────────────────────────
        for m in self.CREATE_ENTITY_ADAPTER_PATTERN.finditer(content):
            name = m.group(1)
            entity_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            after = content[m.end():m.end() + 1000]

            # Extract sort comparer
            sort_match = re.search(r'sortComparer\s*:\s*(?:\(.*?\)\s*=>|(\w+))', after)
            sort_comparer = sort_match.group(1) or "inline" if sort_match else ""

            # Extract selectId
            select_id_match = re.search(r'selectId\s*:\s*(?:\(.*?\)\s*=>|(\w+))', after)
            select_id = select_id_match.group(1) or "inline" if select_id_match else ""

            # Detect CRUD operations used
            crud_ops = [op for op in self.ENTITY_CRUD_OPS if f'{name}.{op}' in content or f'{op}' in content[m.start():m.start() + 3000]]

            # Detect generated selectors (adapter.getSelectors)
            selectors = []
            sel_match = re.search(rf'{re.escape(name)}\.getSelectors\s*\(', content)
            if sel_match:
                selectors = ['selectAll', 'selectById', 'selectIds', 'selectEntities', 'selectTotal']

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            entity_adapters.append(ReduxEntityAdapterInfo(
                name=name,
                file=file_path,
                line_number=line,
                entity_type=entity_type,
                sort_comparer=sort_comparer,
                select_id=select_id,
                crud_operations=crud_ops[:15],
                selectors_generated=selectors,
                is_exported=is_exported,
            ))

        # ── Action exports ────────────────────────────────────────
        for m in self.ACTION_EXPORT_PATTERN.finditer(content):
            actions_str = m.group(1)
            source_slice = m.group(2)
            line = content[:m.start()].count('\n') + 1

            actions = [a.strip() for a in actions_str.split(',') if a.strip()]
            for action in actions:
                action_creators.append(ReduxActionCreatorInfo(
                    name=action,
                    file=file_path,
                    line_number=line,
                    source_slice=source_slice,
                    action_type="sync",
                    is_exported=True,
                ))

        # ── createAction (standalone) ─────────────────────────────
        for m in self.CREATE_ACTION_PATTERN.finditer(content):
            name = m.group(1)
            action_type_str = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            action_creators.append(ReduxActionCreatorInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_slice="",
                action_type=action_type_str,
                is_exported=is_exported,
            ))

        return {
            'slices': slices,
            'entity_adapters': entity_adapters,
            'action_creators': action_creators,
        }

    def _extract_balanced_braces(self, text: str, max_len: int = 8000) -> str:
        """Extract content within balanced braces."""
        depth = 0
        start = None
        for i, ch in enumerate(text[:max_len]):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i + 1]
        return text[:max_len] if start is None else text[start:max_len]

    def _extract_initial_state(self, body: str) -> List[str]:
        """Extract field names from initialState."""
        state_match = re.search(r'initialState\s*(?::\s*\w+)?\s*(?:,|$)', body)
        if state_match:
            # Single variable reference
            ref_match = re.search(r'initialState\s*:\s*(\w+)', body)
            if ref_match:
                return [ref_match.group(1)]

        # Inline object
        state_match = re.search(r'initialState\s*:\s*\{', body)
        if state_match:
            start = state_match.end() - 1
            state_body = self._extract_balanced_braces(body[start:])
            fields = re.findall(r'(\w+)\s*:', state_body)
            return [f for f in fields if f not in ('as', 'const', 'type')]

        # EntityAdapter initialState
        adapter_match = re.search(r'initialState\s*:\s*(\w+)\.getInitialState\s*\(', body)
        if adapter_match:
            # Also get additional fields
            after = body[adapter_match.end():]
            extra_match = re.search(r'\{([^}]+)\}', after)
            extra_fields = re.findall(r'(\w+)\s*:', extra_match.group(1)) if extra_match else []
            return ['ids', 'entities'] + extra_fields

        return []

    def _extract_state_types(self, body: str, prefix: str) -> List[str]:
        """Extract TypeScript types for initial state."""
        types = []
        # interface/type definition near the slice
        type_match = re.search(r'(?:interface|type)\s+(\w+State\w*)\s*(?:=|\{)', prefix[-2000:])
        if type_match:
            types.append(type_match.group(1))
        return types

    def _extract_reducers(self, body: str) -> List[str]:
        """Extract reducer names from createSlice body."""
        reducers_match = re.search(r'reducers\s*:\s*\{', body)
        if reducers_match:
            start = reducers_match.end() - 1
            reducers_body = self._extract_balanced_braces(body[start:])
            # Match reducer names (key: (state, action) => ... or key(state, action) { ... })
            return re.findall(r'(\w+)\s*(?:\(|:\s*(?:\{|state|action|[(]))', reducers_body)
        return []

    def _extract_prepare_callbacks(self, body: str) -> List[str]:
        """Extract reducers with prepare callbacks."""
        return re.findall(r'(\w+)\s*:\s*\{\s*reducer\s*:', body)

    def _extract_extra_reducers(self, body: str):
        """Extract extraReducers cases and matchers."""
        cases = []
        matchers = []
        has_default = False

        # Builder pattern: addCase(thunkName.pending/fulfilled/rejected, ...)
        cases = re.findall(r'\.addCase\s*\(\s*(\w+(?:\.\w+)?)', body)

        # addMatcher
        matchers = re.findall(r'\.addMatcher\s*\(\s*(\w+)', body)

        # addDefaultCase
        has_default = bool(re.search(r'\.addDefaultCase\s*\(', body))

        # Map notation (legacy): [thunkName.pending]: (state) => ...
        legacy_cases = re.findall(r'\[\s*(\w+(?:\.\w+)?)\s*\]\s*:\s*\(', body)
        cases.extend(legacy_cases)

        return cases, matchers, has_default

    def _extract_slice_selectors(self, body: str) -> List[str]:
        """Extract RTK 2.0+ slice selectors."""
        selectors_match = re.search(r'selectors\s*:\s*\{', body)
        if selectors_match:
            start = selectors_match.end() - 1
            sel_body = self._extract_balanced_braces(body[start:])
            return re.findall(r'(\w+)\s*(?:\(|:)', sel_body)
        return []
