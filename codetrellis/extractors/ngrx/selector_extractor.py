"""
NgRx Selector Extractor for CodeTrellis

Extracts NgRx selector patterns:
- createSelector() with input selectors and projector functions
- createFeatureSelector<State>() for feature state slicing
- Selector composition (selectors using other selectors)
- Props selectors (deprecated in v13+, but still detected for legacy)
- selectSignal() / store.selectSignal() (NgRx v16+)
- Feature creator selectors (createFeature v12.1+)
- Memoization and selector reset patterns

Supports:
- NgRx 4.x-7.x (createSelector, createFeatureSelector)
- NgRx 8.x-11.x (improved memoization, props deprecation)
- NgRx 12.x-15.x (createFeature auto-selectors)
- NgRx 16.x-19.x (selectSignal, Signal integration)

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NgrxSelectorInfo:
    """Information about an NgRx selector."""
    name: str
    file: str = ""
    line_number: int = 0
    selector_type: str = ""  # createSelector, createFeatureSelector, inline
    input_selectors: List[str] = field(default_factory=list)
    feature_name: str = ""  # For createFeatureSelector
    state_path: str = ""  # Derived path if detectable
    is_composed: bool = False  # Uses other selectors as input
    is_parameterized: bool = False  # Uses factory pattern for props
    is_exported: bool = False
    has_memoization_reset: bool = False


@dataclass
class NgrxFeatureSelectorInfo:
    """Information about an NgRx feature selector from createFeature."""
    name: str
    file: str = ""
    line_number: int = 0
    feature_name: str = ""
    state_type: str = ""
    generated_selectors: List[str] = field(default_factory=list)
    reducer_name: str = ""
    is_exported: bool = False


class NgrxSelectorExtractor:
    """
    Extracts NgRx selector patterns from source code.

    Detects:
    - createSelector() with input selectors
    - createFeatureSelector<State>()
    - createFeature (v12.1+ auto-generated selectors)
    - Selector composition chains
    - selectSignal / store.selectSignal (v16+)
    - Factory selectors (parameterized)
    - Inline store.select() calls
    """

    # createSelector
    CREATE_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*createSelector\s*\(',
        re.MULTILINE
    )

    # createFeatureSelector
    CREATE_FEATURE_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*'
        r'createFeatureSelector\s*<\s*(\w+)\s*>\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # createFeature (v12.1+ - auto-generates selectors)
    CREATE_FEATURE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*createFeature\s*\(\s*\{',
        re.MULTILINE
    )

    # Factory selector (returns a function)
    FACTORY_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*createSelector\s*\(',
        re.MULTILINE
    )

    # store.select() inline usage
    STORE_SELECT_PATTERN = re.compile(
        r'(?:this\.)?store\.(?:select|selectSignal)\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # selectSignal usage (v16+)
    SELECT_SIGNAL_PATTERN = re.compile(
        r'(?:this\.)?store\.selectSignal\s*\(',
        re.MULTILINE
    )

    # Input selectors in createSelector - look for identifiers before the last arg
    INPUT_SELECTOR_PATTERN = re.compile(
        r'createSelector\s*\(\s*([^)]+)\)',
        re.MULTILINE | re.DOTALL
    )

    # Memoization reset
    MEMOIZATION_RESET_PATTERN = re.compile(
        r'\.release\s*\(\s*\)|resetMemoization|clearMemoization',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract all NgRx selector information from source code."""
        result: Dict = {
            'selectors': [],
            'feature_selectors': [],
            'select_signal_count': 0,
        }

        has_memo_reset = bool(self.MEMOIZATION_RESET_PATTERN.search(content))

        # ── createSelector ────────────────────────────────────
        for match in self.CREATE_SELECTOR_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Try to extract input selectors
            block_start = match.start()
            block_end = min(block_start + 600, len(content))
            block = content[block_start:block_end]

            input_selectors = self._extract_input_selectors(block)
            is_composed = len(input_selectors) > 0

            sel = NgrxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                selector_type='createSelector',
                input_selectors=input_selectors,
                is_composed=is_composed,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
                has_memoization_reset=has_memo_reset,
            )
            result['selectors'].append(sel)

        # ── createFeatureSelector ─────────────────────────────
        for match in self.CREATE_FEATURE_SELECTOR_PATTERN.finditer(content):
            name = match.group(1)
            state_type = match.group(2)
            feature_name = match.group(3)
            line_number = content[:match.start()].count('\n') + 1

            sel = NgrxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                selector_type='createFeatureSelector',
                feature_name=feature_name,
                state_path=feature_name,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['selectors'].append(sel)

        # ── Factory selectors ─────────────────────────────────
        for match in self.FACTORY_SELECTOR_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            sel = NgrxSelectorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                selector_type='factory',
                is_parameterized=True,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['selectors'].append(sel)

        # ── createFeature (auto-generated selectors) ──────────
        for match in self.CREATE_FEATURE_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 1000, len(content))
            block = content[block_start:block_end]

            # Extract feature name
            feat_name_match = re.search(r'name\s*:\s*[\'"](\w+)[\'"]', block)
            feature_name = feat_name_match.group(1) if feat_name_match else ""

            # Extract reducer name
            reducer_match = re.search(r'reducer\s*:\s*(\w+)', block)
            reducer_name = reducer_match.group(1) if reducer_match else ""

            # State type
            state_match = re.search(r'createFeature\s*<\s*(\w+)', block)
            state_type = state_match.group(1) if state_match else ""

            # Generated selectors (from state fields)
            state_fields = re.findall(r'(\w+)\s*:', block[:300])
            generated = [f"select{f[0].upper()}{f[1:]}" for f in state_fields if f not in ('name', 'reducer', 'extraSelectors')]

            fs = NgrxFeatureSelectorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                feature_name=feature_name,
                state_type=state_type,
                generated_selectors=generated,
                reducer_name=reducer_name,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['feature_selectors'].append(fs)

        # ── selectSignal count ────────────────────────────────
        result['select_signal_count'] = len(self.SELECT_SIGNAL_PATTERN.findall(content))

        return result

    def _extract_input_selectors(self, block: str) -> List[str]:
        """Extract input selector names from createSelector() call."""
        # Look for createSelector(sel1, sel2, ..., (a, b) => ...)
        selectors = []
        match = re.search(
            r'createSelector\s*\(\s*'
            r'((?:\w+\s*,\s*)*\w+)\s*,\s*'
            r'(?:\([^)]*\)\s*=>|\bfunction\b)',
            block, re.DOTALL
        )
        if match:
            sel_text = match.group(1)
            selectors = [s.strip() for s in sel_text.split(',') if s.strip()]
        return selectors
