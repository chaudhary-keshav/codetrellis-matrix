"""
Redux Selector Extractor for CodeTrellis

Extracts Redux selector patterns:
- createSelector (reselect) with input/output selector analysis
- createDraftSafeSelector (RTK)
- createStructuredSelector (reselect)
- createEntityAdapter selectors (selectAll, selectById, selectIds, etc.)
- useSelector hook usage with inline/named selectors
- Typed hooks (useAppSelector, useAppDispatch)
- Selector composition and memoization patterns
- RTK 2.0 slice selectors

Supports:
- reselect 1.x-5.x
- Redux Toolkit 1.0-2.x (createDraftSafeSelector)
- Redux Toolkit 2.0+ (createSlice selectors)
- react-redux 7.x-9.x (useSelector, useDispatch)

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReduxSelectorInfo:
    """Information about a Redux selector (createSelector or inline)."""
    name: str
    file: str = ""
    line_number: int = 0
    selector_type: str = ""  # createSelector, createDraftSafeSelector, createStructuredSelector, inline, entityAdapter
    input_selectors: List[str] = field(default_factory=list)
    output_fields: List[str] = field(default_factory=list)
    state_path: str = ""  # e.g., state.users, state.auth
    is_memoized: bool = False
    is_parameterized: bool = False  # Factory selector (selector creator)
    is_exported: bool = False
    source_slice: str = ""  # If derived from a slice


@dataclass
class ReduxTypedHookInfo:
    """Information about typed Redux hook definitions."""
    name: str
    file: str = ""
    line_number: int = 0
    hook_type: str = ""  # useAppSelector, useAppDispatch, useAppStore
    base_type: str = ""  # RootState, AppDispatch
    is_exported: bool = False


class ReduxSelectorExtractor:
    """
    Extracts Redux selector patterns from source code.

    Detects:
    - createSelector with input/output analysis
    - createDraftSafeSelector (RTK-specific)
    - createStructuredSelector (reselect)
    - Entity adapter selectors
    - useSelector with inline/named selectors
    - Typed hooks (useAppSelector, useAppDispatch)
    """

    # createSelector
    CREATE_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(createSelector|createDraftSafeSelector)\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # createStructuredSelector
    CREATE_STRUCTURED_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createStructuredSelector\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # Simple selector: const selectX = (state: RootState) => state.x
    SIMPLE_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(select\w+)\s*=\s*'
        r'\(\s*state\s*(?::\s*\w+)?\s*\)\s*(?::\s*\w+)?\s*=>\s*'
        r'state\.(\w+(?:\.\w+)*)',
        re.MULTILINE
    )

    # useSelector usage
    USE_SELECTOR_PATTERN = re.compile(
        r'(?:const|let)\s+(?:\{([^}]*)\}|(\w+))\s*=\s*'
        r'(?:useSelector|useAppSelector)\s*(?:<[^>]*>)?\s*\(\s*'
        r'(?:\(\s*state\s*(?::\s*\w+)?\s*\)\s*=>\s*'
        r'(?:state\.(\w+(?:\.\w+)*)|(\{[^}]+\}))|'
        r'(\w+))',
        re.MULTILINE
    )

    # useDispatch / useAppDispatch
    USE_DISPATCH_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*'
        r'(?:useDispatch|useAppDispatch)\s*\(\s*\)',
        re.MULTILINE
    )

    # Typed hook definitions: export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
    TYPED_HOOK_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*TypedUseSelectorHook\s*<\s*(\w+)\s*>)?\s*=\s*'
        r'(useSelector|useDispatch)',
        re.MULTILINE
    )

    # Typed hook via useSelector.withTypes<>()
    TYPED_HOOK_WITH_TYPES_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(useApp\w+)\s*=\s*'
        r'(useSelector|useDispatch|useStore)\.withTypes\s*<\s*(\w+)\s*>\s*\(\s*\)',
        re.MULTILINE
    )

    # getSelectors from entity adapter
    GET_SELECTORS_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+\{([^}]+)\}\s*=\s*'
        r'(\w+)\.getSelectors\s*\(\s*'
        r'(?:\(\s*state\s*(?::\s*\w+)?\s*\)\s*=>\s*state\.(\w+))?',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Redux selector patterns from source code."""
        selectors = []
        typed_hooks = []

        # ── createSelector ────────────────────────────────────────
        for m in self.CREATE_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            sel_type = m.group(2)
            line = content[:m.start()].count('\n') + 1
            after = content[m.end():m.end() + 2000]

            # Extract input selectors
            input_selectors = self._extract_input_selectors(after)

            # Detect if parameterized (factory pattern)
            is_parameterized = bool(re.search(r'=>\s*createSelector', content[max(0, m.start() - 100):m.start()]))

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            selectors.append(ReduxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type=sel_type,
                input_selectors=input_selectors[:10],
                is_memoized=True,
                is_parameterized=is_parameterized,
                is_exported=is_exported,
            ))

        # ── createStructuredSelector ──────────────────────────────
        for m in self.CREATE_STRUCTURED_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            # Extract output field names
            output_fields = re.findall(r'(\w+)\s*:', body)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            selectors.append(ReduxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type="createStructuredSelector",
                output_fields=output_fields[:20],
                is_memoized=True,
                is_exported=is_exported,
            ))

        # ── Simple selectors ──────────────────────────────────────
        for m in self.SIMPLE_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            state_path = m.group(2)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            selectors.append(ReduxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                selector_type="inline",
                state_path=f"state.{state_path}",
                is_memoized=False,
                is_exported=is_exported,
            ))

        # ── Entity adapter selectors ──────────────────────────────
        for m in self.GET_SELECTORS_PATTERN.finditer(content):
            destructured = m.group(1)
            adapter_name = m.group(2)
            state_path = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            selector_names = [s.strip() for s in destructured.split(',') if s.strip()]
            for sel_name in selector_names:
                selectors.append(ReduxSelectorInfo(
                    name=sel_name,
                    file=file_path,
                    line_number=line,
                    selector_type="entityAdapter",
                    state_path=f"state.{state_path}" if state_path else "",
                    is_memoized=True,
                    is_exported=True,
                    source_slice=adapter_name,
                ))

        # ── Typed hooks ───────────────────────────────────────────
        for m in self.TYPED_HOOK_PATTERN.finditer(content):
            name = m.group(1)
            base_type = m.group(2) or ""
            base_hook = m.group(3)
            line = content[:m.start()].count('\n') + 1

            if name.startswith('useApp') or base_type:
                is_exported = 'export' in content[max(0, m.start() - 20):m.start()]
                typed_hooks.append(ReduxTypedHookInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    hook_type=f"typed_{base_hook}",
                    base_type=base_type,
                    is_exported=is_exported,
                ))

        # ── Typed hooks with .withTypes<>() (RTK 2.0) ─────────────
        for m in self.TYPED_HOOK_WITH_TYPES_PATTERN.finditer(content):
            name = m.group(1)
            base_hook = m.group(2)
            type_param = m.group(3)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]
            typed_hooks.append(ReduxTypedHookInfo(
                name=name,
                file=file_path,
                line_number=line,
                hook_type=f"typed_{base_hook}",
                base_type=type_param,
                is_exported=is_exported,
            ))

        return {
            'selectors': selectors,
            'typed_hooks': typed_hooks,
        }

    def _extract_balanced_braces(self, text: str, max_len: int = 5000) -> str:
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

    def _extract_input_selectors(self, text: str) -> List[str]:
        """Extract input selector names from createSelector call."""
        # Input selectors are the arguments before the last function argument
        # e.g. createSelector(selectA, selectB, (a, b) => ...)
        # or createSelector([selectA, selectB], (a, b) => ...)

        # Array form
        arr_match = re.search(r'^\s*\[([^\]]+)\]', text)
        if arr_match:
            return [s.strip() for s in arr_match.group(1).split(',') if s.strip() and not s.strip().startswith('(')]

        # Positional form: collect identifiers before the result function
        inputs = []
        depth = 0
        i = 0
        while i < min(len(text), 1000):
            ch = text[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth < 0:
                    break
            elif depth == 0:
                # Match an identifier
                id_match = re.match(r'(\w+)', text[i:])
                if id_match:
                    name = id_match.group(1)
                    # Skip if it's a function body indicator
                    if name in ('state', 'return', 'const', 'let', 'var'):
                        break
                    inputs.append(name)
                    i += len(name)
                    continue
            i += 1
        return inputs
