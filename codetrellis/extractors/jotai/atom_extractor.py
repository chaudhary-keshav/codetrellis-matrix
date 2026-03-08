"""
Jotai Atom Extractor for CodeTrellis

Extracts Jotai atom definitions and configuration patterns:
- atom() primitive atoms (string, number, boolean, object, array)
- atom() writable atoms with read/write functions
- atom() read-only (derived) atoms
- atom() async atoms (read returns Promise)
- atomWithDefault() atoms with lazy default
- atomFamily() parameterized atom factories (jotai/utils)
- atomWithReset() resettable atoms + RESET sentinel (jotai/utils)
- atomWithReducer() reducer-based atoms (jotai/utils)
- Atom creators (factory functions returning atoms)
- TypeScript generic annotations (Atom<T>, PrimitiveAtom<T>, WritableAtom<V,A,R>)

Supports:
- Jotai v1.x (atom, Provider, useAtom)
- Jotai v2.x (store API, createStore, getDefaultStore, atom scoping)

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JotaiAtomInfo:
    """Information about a Jotai atom definition."""
    name: str
    file: str = ""
    line_number: int = 0
    atom_type: str = ""  # primitive, writable, readonly, async, derived
    creation_method: str = ""  # atom, atomWithDefault, atomWithReducer
    initial_value: str = ""
    value_type: str = ""  # string, number, boolean, object, array, unknown
    has_typescript: bool = False
    type_annotation: str = ""  # TypeScript generic e.g. Atom<number>
    has_read_fn: bool = False
    has_write_fn: bool = False
    is_async: bool = False
    is_exported: bool = False
    dependencies: List[str] = field(default_factory=list)  # atoms read in read fn
    description: str = ""


@dataclass
class JotaiAtomFamilyInfo:
    """Information about a Jotai atomFamily definition."""
    name: str
    file: str = ""
    line_number: int = 0
    param_type: str = ""  # parameter type for the factory
    atom_type: str = ""  # type of atom created
    has_typescript: bool = False
    type_annotation: str = ""
    has_equality_fn: bool = False
    is_exported: bool = False


@dataclass
class JotaiResettableAtomInfo:
    """Information about a Jotai resettable atom (atomWithReset)."""
    name: str
    file: str = ""
    line_number: int = 0
    initial_value: str = ""
    has_typescript: bool = False
    type_annotation: str = ""
    is_exported: bool = False


class JotaiAtomExtractor:
    """
    Extracts Jotai atom definitions from source code.

    Detects:
    - atom() calls with primitive, object, or function initializers
    - Writable atoms (atom with read + write functions)
    - Read-only derived atoms (atom with only read function)
    - Async atoms (read function returns Promise)
    - atomWithDefault() for lazy defaults
    - atomFamily() parameterized atom factories
    - atomWithReset() resettable atoms
    - atomWithReducer() reducer-based atoms
    - TypeScript generic annotations
    - Export declarations
    """

    # atom() primitive: const xAtom = atom(initialValue)
    ATOM_PRIMITIVE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(\s*'
        r'(?!(?:\s*\(?\s*(?:get|set)\b))'  # NOT a function arg (read/write)
        r'([^)]*?)\s*\)',
        re.MULTILINE
    )

    # atom() with read function (derived or async): const xAtom = atom((get) => ...)
    ATOM_READ_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(\s*'
        r'(?:async\s+)?\(?\s*get\s*\)?\s*=>\s*',
        re.MULTILINE
    )

    # atom() with read + write functions: const xAtom = atom(readFn, writeFn)
    ATOM_WRITABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(\s*'
        r'(?:async\s+)?\(?\s*get\s*\)?\s*=>[^,]+,\s*'
        r'(?:async\s+)?\(?\s*get\s*,\s*set',
        re.MULTILINE
    )

    # atomWithDefault(): const xAtom = atomWithDefault((get) => ...)
    ATOM_WITH_DEFAULT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithDefault\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # atomFamily(): const xAtomFamily = atomFamily((param) => atom(...))
    ATOM_FAMILY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomFamily\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # atomWithReset(): const xAtom = atomWithReset(initialValue)
    ATOM_WITH_RESET_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithReset\s*(?:<([^>]*)>)?\s*\(\s*([^)]*?)\s*\)',
        re.MULTILINE
    )

    # atomWithReducer(): const xAtom = atomWithReducer(initialValue, reducer)
    ATOM_WITH_REDUCER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithReducer\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Generic atom() call (fallback): const xAtom = atom(...)
    ATOM_GENERIC_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Async indicator within atom
    ASYNC_PATTERN = re.compile(r'async\s+\(', re.MULTILINE)

    # Dependency extraction: get(someAtom)
    GET_DEPENDENCY_PATTERN = re.compile(
        r'get\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Jotai atom patterns from source code."""
        atoms = []
        atom_families = []
        resettable_atoms = []

        seen_names = set()

        # ── atomFamily ──────────────────────────────────────────
        for m in self.ATOM_FAMILY_PATTERN.finditer(content):
            name = m.group(1)
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            atom_families.append(JotaiAtomFamilyInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                is_exported=is_exported,
                has_equality_fn='areEqual' in content[m.start():m.start() + 300] or
                                'deepEqual' in content[m.start():m.start() + 300],
            ))
            seen_names.add(name)

        # ── atomWithReset ───────────────────────────────────────
        for m in self.ATOM_WITH_RESET_PATTERN.finditer(content):
            name = m.group(1)
            ts_type = m.group(2) or ""
            initial = m.group(3).strip() if m.group(3) else ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            resettable_atoms.append(JotaiResettableAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                initial_value=initial[:50],
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── atomWithDefault ─────────────────────────────────────
        for m in self.ATOM_WITH_DEFAULT_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            atoms.append(JotaiAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                atom_type="writable",
                creation_method="atomWithDefault",
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_read_fn=True,
                has_write_fn=True,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── atomWithReducer ─────────────────────────────────────
        for m in self.ATOM_WITH_REDUCER_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            atoms.append(JotaiAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                atom_type="writable",
                creation_method="atomWithReducer",
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_read_fn=True,
                has_write_fn=True,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── atom() with read+write (writable derived) ──────────
        for m in self.ATOM_WRITABLE_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Check if async
            context_start = m.start()
            context_end = min(len(content), m.start() + 200)
            context_text = content[context_start:context_end]
            is_async = bool(self.ASYNC_PATTERN.search(context_text))

            # Extract dependencies
            deps = [d.group(1) for d in self.GET_DEPENDENCY_PATTERN.finditer(context_text)]

            atoms.append(JotaiAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                atom_type="writable",
                creation_method="atom",
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_read_fn=True,
                has_write_fn=True,
                is_async=is_async,
                is_exported=is_exported,
                dependencies=deps[:15],
            ))
            seen_names.add(name)

        # ── atom() with read function (derived/async) ──────────
        for m in self.ATOM_READ_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Check if async
            context_start = m.start()
            context_end = min(len(content), m.start() + 300)
            context_text = content[context_start:context_end]
            is_async = 'async' in context_text[:50]

            # Extract dependencies
            deps = [d.group(1) for d in self.GET_DEPENDENCY_PATTERN.finditer(context_text)]

            # Check if it also has a write fn (look for comma after read fn)
            has_write = bool(re.search(r',\s*(?:async\s+)?\(?\s*(?:get|_)\s*,\s*set', context_text))

            atoms.append(JotaiAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                atom_type="async" if is_async else ("writable" if has_write else "derived"),
                creation_method="atom",
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_read_fn=True,
                has_write_fn=has_write,
                is_async=is_async,
                is_exported=is_exported,
                dependencies=deps[:15],
            ))
            seen_names.add(name)

        # ── atom() primitive (fallback) ─────────────────────────
        for m in self.ATOM_GENERIC_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Try to determine initial value and type
            context_start = m.end() - 1  # position of (
            context_end = min(len(content), context_start + 100)
            context_text = content[context_start:context_end]

            # Extract initial value (inside atom(...))
            initial_value = ""
            value_type = "unknown"
            inner = context_text[1:]  # skip opening (
            paren_depth = 1
            i = 0
            while i < len(inner) and paren_depth > 0:
                if inner[i] == '(':
                    paren_depth += 1
                elif inner[i] == ')':
                    paren_depth -= 1
                i += 1
            if paren_depth == 0:
                initial_value = inner[:i - 1].strip()

            # Determine value type from initial value
            if initial_value:
                iv = initial_value.strip()
                if iv in ('true', 'false'):
                    value_type = "boolean"
                elif iv == 'null' or iv == 'undefined':
                    value_type = "null"
                elif iv.startswith(("'", '"', '`')):
                    value_type = "string"
                elif iv.startswith('{'):
                    value_type = "object"
                elif iv.startswith('['):
                    value_type = "array"
                elif iv.replace('.', '', 1).replace('-', '', 1).isdigit():
                    value_type = "number"
                elif '(' in iv or '=>' in iv:
                    # This is likely a function — skip as it's a derived atom
                    continue

            # Check if it has read/write by examining content after atom(
            has_read = 'get' in context_text[:60] and '=>' in context_text[:60]
            if has_read:
                continue  # Already handled above

            atoms.append(JotaiAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                atom_type="primitive",
                creation_method="atom",
                initial_value=initial_value[:50],
                value_type=value_type,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        return {
            'atoms': atoms,
            'atom_families': atom_families,
            'resettable_atoms': resettable_atoms,
        }
