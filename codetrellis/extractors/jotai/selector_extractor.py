"""
Jotai Selector Extractor for CodeTrellis

Extracts Jotai derived atom and selector patterns:
- Derived atoms (read-only atom with get function)
- selectAtom (jotai/utils) — memoized selector with equality fn
- focusAtom (jotai-optics) — lens-based atom access
- splitAtom (jotai/utils) — splits array atom into individual atoms
- loadable (jotai/utils) — wraps async atoms with loading state
- unwrap (jotai/utils) — unwraps async atoms with fallback
- atomWithReducer (jotai/utils) — reducer-based state updates

Supports:
- Jotai v1.x (atom read-only, atomFamily derived)
- Jotai v2.x (improved derived atom types, selectAtom stability)

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JotaiDerivedAtomInfo:
    """Information about a Jotai derived (read-only) atom."""
    name: str
    file: str = ""
    line_number: int = 0
    source_atoms: List[str] = field(default_factory=list)  # atoms read via get()
    is_async: bool = False
    has_typescript: bool = False
    type_annotation: str = ""
    is_exported: bool = False


@dataclass
class JotaiSelectAtomInfo:
    """Information about a selectAtom usage."""
    name: str
    file: str = ""
    line_number: int = 0
    source_atom: str = ""  # atom being selected from
    selector_fn: str = ""  # brief description of selector
    has_equality_fn: bool = False
    is_exported: bool = False


@dataclass
class JotaiFocusAtomInfo:
    """Information about a focusAtom (jotai-optics) usage."""
    name: str
    file: str = ""
    line_number: int = 0
    source_atom: str = ""
    optic_path: str = ""  # lens path
    is_exported: bool = False


class JotaiSelectorExtractor:
    """
    Extracts Jotai selector/derived patterns from source code.

    Detects:
    - Derived atoms (atom((get) => get(sourceAtom).field))
    - selectAtom from jotai/utils
    - focusAtom from jotai-optics
    - splitAtom from jotai/utils
    - loadable from jotai/utils
    - unwrap from jotai/utils
    """

    # selectAtom: const xAtom = selectAtom(sourceAtom, (v) => v.field)
    SELECT_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'selectAtom\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # focusAtom: const xAtom = focusAtom(sourceAtom, (optic) => optic.prop('field'))
    FOCUS_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'focusAtom\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # splitAtom: const xAtomsAtom = splitAtom(listAtom)
    SPLIT_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'splitAtom\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # loadable: const xAtom = loadable(asyncAtom)
    LOADABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'loadable\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # unwrap: const xAtom = unwrap(asyncAtom, (prev) => prev ?? fallback)
    UNWRAP_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'unwrap\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Derived atom: const xAtom = atom((get) => get(sourceAtom))
    DERIVED_ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(\s*'
        r'(?:async\s+)?\(?\s*get\s*\)?\s*=>',
        re.MULTILINE
    )

    # get(atomName) dependency extraction
    GET_DEPENDENCY_PATTERN = re.compile(
        r'get\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Jotai selector/derived patterns from source code."""
        derived_atoms = []
        select_atoms = []
        focus_atoms = []

        seen_names = set()

        # ── selectAtom ──────────────────────────────────────────
        for m in self.SELECT_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Check for equality function
            ctx = content[m.start():min(len(content), m.start() + 200)]
            has_eq = ctx.count(',') >= 2  # selectAtom(source, selector, equalityFn)

            select_atoms.append(JotaiSelectAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atom=source,
                has_equality_fn=has_eq,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── focusAtom ──────────────────────────────────────────
        for m in self.FOCUS_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Try to extract optic path
            ctx = content[m.start():min(len(content), m.start() + 200)]
            optic_match = re.search(r"\.prop\(['\"](\w+)['\"]\)", ctx)
            optic_path = optic_match.group(1) if optic_match else ""

            focus_atoms.append(JotaiFocusAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atom=source,
                optic_path=optic_path,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── splitAtom ──────────────────────────────────────────
        for m in self.SPLIT_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            derived_atoms.append(JotaiDerivedAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atoms=[source],
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── loadable ───────────────────────────────────────────
        for m in self.LOADABLE_PATTERN.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            derived_atoms.append(JotaiDerivedAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atoms=[source],
                is_async=True,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── unwrap ─────────────────────────────────────────────
        for m in self.UNWRAP_PATTERN.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            derived_atoms.append(JotaiDerivedAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atoms=[source],
                is_async=True,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── Derived atoms (atom((get) => ...)) ────────────────
        for m in self.DERIVED_ATOM_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Extract dependencies
            ctx = content[m.start():min(len(content), m.start() + 500)]
            deps = [d.group(1) for d in self.GET_DEPENDENCY_PATTERN.finditer(ctx)]
            is_async = 'async' in content[m.start():m.start() + 50]

            # Check if also has write fn -> skip (handled by atom extractor)
            has_write = bool(re.search(r',\s*(?:async\s+)?\(?\s*(?:get|_)\s*,\s*set', ctx[:300]))
            if has_write:
                continue

            derived_atoms.append(JotaiDerivedAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                source_atoms=list(dict.fromkeys(deps))[:15],
                is_async=is_async,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        return {
            'derived_atoms': derived_atoms,
            'select_atoms': select_atoms,
            'focus_atoms': focus_atoms,
        }
