"""
Recoil Atom Extractor for CodeTrellis

Extracts Recoil atom definitions and configuration patterns:
- atom({key, default}) primitive atoms (string, number, boolean, object, array)
- atom({key, default, effects}) atoms with effects
- atom({key, default, dangerouslyAllowMutability}) mutable atoms
- atomFamily({key, default}) parameterized atom factories
- TypeScript generic annotations (RecoilState<T>, atom<T>)
- Export declarations

Supports:
- Recoil 0.0.x (initial public release, atom/selector)
- Recoil 0.1.x (atomFamily, selectorFamily)
- Recoil 0.2.x (atom effects)
- Recoil 0.3.x (useRecoilCallback improvements)
- Recoil 0.4.x (snapshot improvements)
- Recoil 0.5.x (useRecoilRefresher_UNSTABLE)
- Recoil 0.6.x (useRecoilStoreID)
- Recoil 0.7.x (latest, stability improvements, React 18 support)

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecoilAtomInfo:
    """Information about a Recoil atom definition."""
    name: str
    file: str = ""
    line_number: int = 0
    key: str = ""  # Recoil requires unique string keys
    default_value: str = ""
    value_type: str = ""  # string, number, boolean, object, array, selector, null, unknown
    has_typescript: bool = False
    type_annotation: str = ""  # TypeScript generic e.g. atom<number>
    has_effects: bool = False
    effect_count: int = 0
    has_dangerously_allow_mutability: bool = False
    is_exported: bool = False
    description: str = ""


@dataclass
class RecoilAtomFamilyInfo:
    """Information about a Recoil atomFamily definition."""
    name: str
    file: str = ""
    line_number: int = 0
    key: str = ""  # key can be a string or function returning string
    param_type: str = ""  # parameter type for the factory
    default_value: str = ""
    has_typescript: bool = False
    type_annotation: str = ""
    has_effects: bool = False
    is_exported: bool = False


class RecoilAtomExtractor:
    """
    Extracts Recoil atom definitions from source code.

    Detects:
    - atom({key, default}) calls with primitive, object, or selector defaults
    - atom({key, default, effects}) atoms with atom effects
    - atom({key, default, dangerouslyAllowMutability}) mutable atoms
    - atomFamily({key, default}) parameterized atom factories
    - TypeScript generic annotations
    - Export declarations
    """

    # atom({key: 'myAtom', default: value})
    ATOM_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atom\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # atomFamily({key: 'myAtomFamily', default: (param) => value})
    ATOM_FAMILY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomFamily\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # Key extraction: key: 'name' or key: "name" or key: `name`
    KEY_PATTERN = re.compile(
        r"key\s*:\s*['\"`]([^'\"`]+)['\"`]",
        re.MULTILINE
    )

    # Default value extraction: default: value
    DEFAULT_PATTERN = re.compile(
        r'default\s*:\s*(.+?)(?:,\s*(?:effects|dangerouslyAllowMutability|key)\b|\s*\})',
        re.DOTALL
    )

    # Effects presence: effects: [...]  or effects_UNSTABLE: [...]
    EFFECTS_PATTERN = re.compile(
        r'effects(?:_UNSTABLE)?\s*:\s*\[',
        re.MULTILINE
    )

    # dangerouslyAllowMutability: true
    MUTABLE_PATTERN = re.compile(
        r'dangerouslyAllowMutability\s*:\s*true',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Recoil atom patterns from source code."""
        atoms = []
        atom_families = []

        seen_names = set()

        # ── atomFamily ──────────────────────────────────────────
        for m in self.ATOM_FAMILY_PATTERN.finditer(content):
            name = m.group(1)
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Extract block (simple brace counting up to ~500 chars)
            block = self._extract_block(content, m.end() - 1, 500)

            key_match = self.KEY_PATTERN.search(block)
            key = key_match.group(1) if key_match else ""

            has_effects = bool(self.EFFECTS_PATTERN.search(block))

            # Infer param type from TypeScript generics
            param_type = ""
            if ts_type and ',' in ts_type:
                parts = ts_type.split(',')
                param_type = parts[-1].strip() if len(parts) >= 2 else ""

            atom_families.append(RecoilAtomFamilyInfo(
                name=name,
                file=file_path,
                line_number=line,
                key=key,
                param_type=param_type,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_effects=has_effects,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        # ── atom ────────────────────────────────────────────────
        for m in self.ATOM_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            ts_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Extract block
            block = self._extract_block(content, m.end() - 1, 500)

            key_match = self.KEY_PATTERN.search(block)
            key = key_match.group(1) if key_match else ""

            # Default value
            default_value = ""
            value_type = "unknown"
            default_match = self.DEFAULT_PATTERN.search(block)
            if default_match:
                raw_default = default_match.group(1).strip()
                default_value = raw_default[:60]
                value_type = self._infer_value_type(raw_default)

            has_effects = bool(self.EFFECTS_PATTERN.search(block))
            effect_count = 0
            if has_effects:
                # Count effects in the effects array
                effects_start = block.find('effects')
                if effects_start >= 0:
                    effects_block = block[effects_start:]
                    effect_count = effects_block.count(',') + 1
                    if effect_count > 20:
                        effect_count = 1  # fallback

            has_mutable = bool(self.MUTABLE_PATTERN.search(block))

            atoms.append(RecoilAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                key=key,
                default_value=default_value,
                value_type=value_type,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_effects=has_effects,
                effect_count=effect_count,
                has_dangerously_allow_mutability=has_mutable,
                is_exported=is_exported,
            ))
            seen_names.add(name)

        return {
            'atoms': atoms,
            'atom_families': atom_families,
        }

    def _extract_block(self, content: str, brace_start: int, max_chars: int = 500) -> str:
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

    def _infer_value_type(self, value: str) -> str:
        """Infer the type of a default value."""
        value = value.strip().rstrip(',').strip()
        if value in ('null', 'undefined'):
            return 'null'
        if value in ('true', 'false'):
            return 'boolean'
        if value.startswith(("'", '"', '`')):
            return 'string'
        if value.startswith('['):
            return 'array'
        if value.startswith('{'):
            return 'object'
        if re.match(r'^-?\d+(\.\d+)?$', value):
            return 'number'
        if 'selector' in value or 'Selector' in value:
            return 'selector'
        if value.startswith('new '):
            return 'object'
        return 'unknown'
