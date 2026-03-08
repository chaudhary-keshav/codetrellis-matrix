"""
Recoil Selector Extractor for CodeTrellis

Extracts Recoil selector definitions and patterns:
- selector({key, get}) read-only selectors (synchronous/async)
- selector({key, get, set}) read-write selectors
- selectorFamily({key, get}) parameterized selector factories
- selectorFamily({key, get, set}) read-write selector families
- constSelector(value) — constant selectors
- errorSelector(error) — error selectors
- noWait(loadable) — non-blocking selectors
- waitForAll([atoms]) — parallel async
- waitForAllSettled([atoms]) — parallel with settlement
- waitForAny([atoms]) — first to resolve
- waitForNone([atoms]) — all loadable without blocking

Supports:
- Recoil 0.0.x through 0.7.x+
- Async selectors with Promise / async get
- Selector caching and memoization
- TypeScript generics

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecoilSelectorInfo:
    """Information about a Recoil selector definition."""
    name: str
    file: str = ""
    line_number: int = 0
    key: str = ""
    is_async: bool = False
    is_writable: bool = False  # has set() function
    has_typescript: bool = False
    type_annotation: str = ""
    dependencies: List[str] = field(default_factory=list)  # atoms/selectors read via get()
    is_exported: bool = False
    selector_type: str = ""  # selector, constSelector, errorSelector


@dataclass
class RecoilSelectorFamilyInfo:
    """Information about a Recoil selectorFamily definition."""
    name: str
    file: str = ""
    line_number: int = 0
    key: str = ""
    param_type: str = ""
    is_async: bool = False
    is_writable: bool = False
    has_typescript: bool = False
    type_annotation: str = ""
    is_exported: bool = False


class RecoilSelectorExtractor:
    """
    Extracts Recoil selector definitions from source code.

    Detects:
    - selector({key, get}) — read-only selectors
    - selector({key, get, set}) — read-write selectors
    - selectorFamily({key, get}) — parameterized selector factories
    - constSelector(value) — constant selectors
    - errorSelector(error) — error selectors
    - noWait(loadable) — non-blocking
    - waitForAll/waitForAllSettled/waitForAny/waitForNone — concurrency helpers
    - Async selectors (async get, get returns Promise)
    - get() dependency tracking
    """

    # selector({key: 'name', get: ...})
    SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'selector\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # selectorFamily({key: 'name', get: ...})
    SELECTOR_FAMILY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'selectorFamily\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # constSelector(value)
    CONST_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'constSelector\s*\(\s*(.+?)\s*\)',
        re.MULTILINE
    )

    # errorSelector(error)
    ERROR_SELECTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'errorSelector\s*\(\s*(.+?)\s*\)',
        re.MULTILINE
    )

    # Concurrency helpers
    WAIT_FOR_ALL_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'waitForAll\s*\(',
        re.MULTILINE
    )

    WAIT_FOR_ALL_SETTLED_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'waitForAllSettled\s*\(',
        re.MULTILINE
    )

    WAIT_FOR_ANY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'waitForAny\s*\(',
        re.MULTILINE
    )

    WAIT_FOR_NONE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'waitForNone\s*\(',
        re.MULTILINE
    )

    # noWait(atom)
    NO_WAIT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'noWait\s*\(',
        re.MULTILINE
    )

    # Key extraction
    KEY_PATTERN = re.compile(
        r"key\s*:\s*['\"`]([^'\"`]+)['\"`]",
        re.MULTILINE
    )

    # Dependency extraction: get(someAtom)
    GET_DEPENDENCY_PATTERN = re.compile(
        r'get\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Async indicator: async ({get}) =>  or  get: async ({get}) =>
    ASYNC_GET_PATTERN = re.compile(
        r'get\s*:\s*async\b|get\s*:\s*\(?\s*\{?\s*get\s*\}?\s*\)?\s*=>\s*\{?\s*await\b',
        re.MULTILINE
    )

    # Writable selector: set: ({set, get, reset}, newValue) =>
    SET_FN_PATTERN = re.compile(
        r'\bset\s*:\s*(?:\(|async\s*\()',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Recoil selector patterns from source code."""
        selectors = []
        selector_families = []

        seen_names = set()

        # ── selectorFamily ──────────────────────────────────────
        for m in self.SELECTOR_FAMILY_PATTERN.finditer(content):
            name = m.group(1)
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            block = self._extract_block(content, m.end() - 1, 600)

            key_match = self.KEY_PATTERN.search(block)
            key = key_match.group(1) if key_match else ""

            is_async = bool(self.ASYNC_GET_PATTERN.search(block)) or 'await ' in block
            is_writable = bool(self.SET_FN_PATTERN.search(block))

            param_type = ""
            if ts_type and ',' in ts_type:
                parts = ts_type.split(',')
                param_type = parts[-1].strip() if len(parts) >= 2 else ""

            selector_families.append(RecoilSelectorFamilyInfo(
                name=name,
                file=file_path,
                line_number=line,
                key=key,
                param_type=param_type,
                is_async=is_async,
                is_writable=is_writable,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── selector ────────────────────────────────────────────
        for m in self.SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            block = self._extract_block(content, m.end() - 1, 600)

            key_match = self.KEY_PATTERN.search(block)
            key = key_match.group(1) if key_match else ""

            is_async = bool(self.ASYNC_GET_PATTERN.search(block)) or 'await ' in block
            is_writable = bool(self.SET_FN_PATTERN.search(block))

            # Extract dependencies
            dependencies = []
            for dep_match in self.GET_DEPENDENCY_PATTERN.finditer(block):
                dep_name = dep_match.group(1)
                if dep_name not in ('get', 'set', 'reset') and dep_name not in dependencies:
                    dependencies.append(dep_name)

            selectors.append(RecoilSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                key=key,
                is_async=is_async,
                is_writable=is_writable,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                dependencies=dependencies[:15],
                is_exported=is_exported,
                selector_type="selector",
            ))
            seen_names.add(name)

        # ── constSelector ───────────────────────────────────────
        for m in self.CONST_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            selectors.append(RecoilSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported=is_exported,
                selector_type="constSelector",
            ))
            seen_names.add(name)

        # ── errorSelector ───────────────────────────────────────
        for m in self.ERROR_SELECTOR_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            selectors.append(RecoilSelectorInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported=is_exported,
                selector_type="errorSelector",
            ))
            seen_names.add(name)

        # ── waitForAll / waitForAllSettled / waitForAny / waitForNone / noWait ──
        for pattern, sel_type in [
            (self.WAIT_FOR_ALL_PATTERN, "waitForAll"),
            (self.WAIT_FOR_ALL_SETTLED_PATTERN, "waitForAllSettled"),
            (self.WAIT_FOR_ANY_PATTERN, "waitForAny"),
            (self.WAIT_FOR_NONE_PATTERN, "waitForNone"),
            (self.NO_WAIT_PATTERN, "noWait"),
        ]:
            for m in pattern.finditer(content):
                name = m.group(1)
                if name in seen_names:
                    continue
                line = content[:m.start()].count('\n') + 1
                is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

                selectors.append(RecoilSelectorInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    is_exported=is_exported,
                    selector_type=sel_type,
                ))
                seen_names.add(name)

        return {
            'selectors': selectors,
            'selector_families': selector_families,
        }

    def _extract_block(self, content: str, brace_start: int, max_chars: int = 600) -> str:
        """Extract a brace-balanced block starting at the given { position."""
        if brace_start >= len(content) or content[brace_start] != '{':
            return content[brace_start:brace_start + max_chars]

        depth = 0
        end = brace_start
        while end < min(len(content), brace_start + max_chars):
            ch = content[end]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_start:end + 1]
            end += 1
        return content[brace_start:end]
