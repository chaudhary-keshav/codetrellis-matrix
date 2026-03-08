"""
XState Guard Extractor for CodeTrellis

Extracts XState guard/condition definitions and usage patterns:
- cond (v4 guard syntax)
- guard (v5 guard syntax)
- Inline guard functions
- Named guard references
- Guard objects with type property
- Combinators: not(), and(), or() (v5)
- stateIn() guards (v5)
- Custom guard functions defined in machine options

Supports:
- XState v3.x (cond property on transitions)
- XState v4.x (cond property, guards in machine options)
- XState v5.x (guard property, not/and/or combinators, stateIn)

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class XstateGuardInfo:
    """Information about an XState guard/condition."""
    name: str
    file: str = ""
    line_number: int = 0
    guard_type: str = ""  # cond, guard, inline, not, and, or, stateIn, custom
    is_named: bool = False  # named reference vs inline function
    is_negated: bool = False  # not() combinator
    combined_guards: List[str] = field(default_factory=list)  # for and/or combinators
    state_value: str = ""  # for stateIn guards
    is_v5: bool = False


class XstateGuardExtractor:
    """
    Extracts XState guard/condition definitions from source code.

    Detects:
    - cond: 'guardName' or cond: (ctx, event) => ... (v4)
    - guard: 'guardName' or guard: (ctx, event) => ... (v5)
    - Guard definitions in machine options guards: { ... }
    - not/and/or combinators (v5)
    - stateIn guards (v5)
    """

    # cond property in transition (v4)
    COND_PATTERN = re.compile(
        r"""cond\s*:\s*(?:['"](\w+)['"]|(\w+)(?:\s*,|\s*\})|(\([^)]*\)\s*=>))""",
        re.MULTILINE
    )

    # guard property in transition (v5)
    GUARD_PATTERN = re.compile(
        r"""guard\s*:\s*(?:['"](\w+)['"]|(\w+)(?:\s*,|\s*\})|(\([^)]*\)\s*=>))""",
        re.MULTILINE
    )

    # Named guard definitions: guards: { guardName: (context, event) => ... }
    GUARD_DEF_PATTERN = re.compile(
        r"""guards\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}""",
        re.MULTILINE | re.DOTALL
    )

    # Guard names inside guards: { ... } block
    GUARD_NAME_IN_BLOCK = re.compile(
        r"""['"]?(\w+)['"]?\s*:\s*(?:\(|function)""",
        re.MULTILINE
    )

    # not() combinator (v5)
    NOT_GUARD_PATTERN = re.compile(
        r"""not\s*\(\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # and() combinator (v5)
    AND_GUARD_PATTERN = re.compile(
        r'and\s*\(\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    # or() combinator (v5)
    OR_GUARD_PATTERN = re.compile(
        r'or\s*\(\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    # stateIn() guard (v5) - matches both string and object forms
    STATE_IN_PATTERN = re.compile(
        r"""stateIn\s*\(\s*(?:['"]([^'"]+)['"]|\{([^}]+)\})""",
        re.MULTILINE
    )

    # Guard object: { type: 'guardName' }
    GUARD_OBJECT_PATTERN = re.compile(
        r"""\{\s*type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract XState guards from source code."""
        guards = []

        # cond guards (v4)
        for match in self.COND_PATTERN.finditer(content):
            name = match.group(1) or match.group(2) or "inline"
            line_number = content[:match.start()].count('\n') + 1
            is_inline = bool(match.group(3))
            guards.append(XstateGuardInfo(
                name=name if not is_inline else "inline",
                file=file_path,
                line_number=line_number,
                guard_type="cond",
                is_named=not is_inline,
            ))

        # guard guards (v5)
        for match in self.GUARD_PATTERN.finditer(content):
            name = match.group(1) or match.group(2) or "inline"
            line_number = content[:match.start()].count('\n') + 1
            is_inline = bool(match.group(3))
            guards.append(XstateGuardInfo(
                name=name if not is_inline else "inline",
                file=file_path,
                line_number=line_number,
                guard_type="guard",
                is_named=not is_inline,
                is_v5=True,
            ))

        # Guard definitions in machine options
        for match in self.GUARD_DEF_PATTERN.finditer(content):
            block = match.group(1)
            base_line = content[:match.start()].count('\n') + 1
            for name_match in self.GUARD_NAME_IN_BLOCK.finditer(block):
                name = name_match.group(1)
                line_number = base_line + block[:name_match.start()].count('\n')
                # Avoid duplicates
                if not any(g.name == name and g.guard_type == "custom" for g in guards):
                    guards.append(XstateGuardInfo(
                        name=name,
                        file=file_path,
                        line_number=line_number,
                        guard_type="custom",
                        is_named=True,
                    ))

        # not() combinator (v5)
        for match in self.NOT_GUARD_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            guards.append(XstateGuardInfo(
                name=f"not({name})",
                file=file_path,
                line_number=line_number,
                guard_type="not",
                is_negated=True,
                combined_guards=[name],
                is_v5=True,
            ))

        # and() combinator (v5)
        for match in self.AND_GUARD_PATTERN.finditer(content):
            combined_str = match.group(1)
            combined = re.findall(r"""['"](\w+)['"]""", combined_str)
            line_number = content[:match.start()].count('\n') + 1
            guards.append(XstateGuardInfo(
                name=f"and({','.join(combined)})",
                file=file_path,
                line_number=line_number,
                guard_type="and",
                combined_guards=combined,
                is_v5=True,
            ))

        # or() combinator (v5)
        for match in self.OR_GUARD_PATTERN.finditer(content):
            combined_str = match.group(1)
            combined = re.findall(r"""['"](\w+)['"]""", combined_str)
            line_number = content[:match.start()].count('\n') + 1
            guards.append(XstateGuardInfo(
                name=f"or({','.join(combined)})",
                file=file_path,
                line_number=line_number,
                guard_type="or",
                combined_guards=combined,
                is_v5=True,
            ))

        # stateIn() guards (v5)
        for match in self.STATE_IN_PATTERN.finditer(content):
            state_value = match.group(1) or match.group(2) or ""
            state_value = state_value.strip()
            line_number = content[:match.start()].count('\n') + 1
            guards.append(XstateGuardInfo(
                name=f"stateIn({state_value})",
                file=file_path,
                line_number=line_number,
                guard_type="stateIn",
                state_value=state_value,
                is_v5=True,
            ))

        return {"guards": guards}
