"""
MobX Computed Extractor v1.0

Extracts MobX computed property definitions including:
- computed() function calls
- computed.struct usage
- @computed decorator (legacy)
- @computed.struct decorator
- Computed getters (get property in makeObservable annotations)
- keepAlive and requiresReaction options
- Custom equals comparers
- Computed with setter

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MobXComputedInfo:
    """Information about a MobX computed property."""
    name: str = ""
    file: str = ""
    line: int = 0
    computed_type: str = ""  # 'computed', 'computed.struct', '@computed', 'getter'
    class_name: str = ""
    field_name: str = ""
    has_setter: bool = False
    keep_alive: bool = False
    requires_reaction: bool = False
    has_equals: bool = False
    equals_type: str = ""  # 'structural', 'default', 'shallow', 'custom'
    typescript_type: str = ""


class MobXComputedExtractor:
    """Extracts MobX computed property definitions from source code."""

    # computed(() => expr) / computed(() => expr, { options })
    COMPUTED_CALL = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*computed\s*\(\s*(?:\(\s*\)|function)',
    )

    # computed({ get() {}, set(val) {} })
    COMPUTED_WITH_SETTER = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*computed\s*\(\s*\{[\s\S]*?get\s*\(',
    )

    # @computed / @computed.struct
    COMPUTED_DECORATOR = re.compile(
        r'@computed(?:\.(struct))?\s*\n?\s*(?:get\s+)?(\w+)',
    )

    # In annotation maps: field: computed
    COMPUTED_ANNOTATION = re.compile(
        r'(\w+)\s*:\s*computed(?:\.(struct))?',
    )

    # computed() standalone with options { keepAlive, requiresReaction, equals }
    COMPUTED_OPTIONS = re.compile(
        r'computed\s*\([^,]+,\s*\{([^}]*)\}',
        re.DOTALL
    )

    # Class context for enclosing class detection
    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all MobX computed definitions from source content.

        Returns:
            Dict with keys:
            - computeds: List[MobXComputedInfo]
        """
        computeds: List[MobXComputedInfo] = []

        class_ranges = self._find_class_ranges(content)

        # Extract computed() function calls
        for match in self.COMPUTED_CALL.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)

            # Check for options
            keep_alive, requires_reaction, has_equals, equals_type = self._extract_options(
                content[match.start():match.start() + 500]
            )

            info = MobXComputedInfo(
                name=var_name,
                file=file_path,
                line=line_num,
                computed_type='computed',
                field_name=var_name,
                keep_alive=keep_alive,
                requires_reaction=requires_reaction,
                has_equals=has_equals,
                equals_type=equals_type,
            )
            computeds.append(info)

        # Extract computed with setter
        for match in self.COMPUTED_WITH_SETTER.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)

            # Check if already captured
            if any(c.name == var_name and c.line == line_num for c in computeds):
                continue

            info = MobXComputedInfo(
                name=var_name,
                file=file_path,
                line=line_num,
                computed_type='computed',
                field_name=var_name,
                has_setter='set' in content[match.start():match.start() + 500],
            )
            computeds.append(info)

        # Extract @computed / @computed.struct decorators
        for match in self.COMPUTED_DECORATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            modifier = match.group(1) or ''
            field_name = match.group(2)
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            info = MobXComputedInfo(
                name=f"{class_name}.{field_name}" if class_name else field_name,
                file=file_path,
                line=line_num,
                computed_type=f'@computed.{modifier}' if modifier else '@computed',
                class_name=class_name,
                field_name=field_name,
            )
            computeds.append(info)

        # Extract computed annotations from makeObservable calls
        for match in self.COMPUTED_ANNOTATION.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            field_name = match.group(1)
            modifier = match.group(2) or ''
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            # Avoid duplicates with decorator extractions
            if any(c.field_name == field_name and c.class_name == class_name for c in computeds):
                continue

            info = MobXComputedInfo(
                name=f"{class_name}.{field_name}" if class_name else field_name,
                file=file_path,
                line=line_num,
                computed_type=f'computed.{modifier}' if modifier else 'computed',
                class_name=class_name,
                field_name=field_name,
            )
            computeds.append(info)

        return {
            'computeds': computeds,
        }

    def _extract_options(self, context: str) -> tuple:
        """Extract computed options (keepAlive, requiresReaction, equals)."""
        keep_alive = 'keepAlive' in context and ('true' in context or 'keepAlive:' in context)
        requires_reaction = 'requiresReaction' in context and 'true' in context.split('requiresReaction')[1][:20] if 'requiresReaction' in context else False
        has_equals = 'equals' in context
        equals_type = ''
        if has_equals:
            if 'comparer.structural' in context:
                equals_type = 'structural'
            elif 'comparer.shallow' in context:
                equals_type = 'shallow'
            elif 'comparer.default' in context:
                equals_type = 'default'
            else:
                equals_type = 'custom'
        return keep_alive, requires_reaction, has_equals, equals_type

    def _find_class_ranges(self, content: str) -> List[Dict[str, Any]]:
        """Find class name and character ranges."""
        ranges = []
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            start = match.start()
            depth = 0
            end = start
            for i in range(match.end() - 1, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            ranges.append({'name': class_name, 'start': start, 'end': end})
        return ranges

    def _find_enclosing_class(self, pos: int, class_ranges: List[Dict]) -> str:
        """Find the class name enclosing a given character position."""
        for cr in class_ranges:
            if cr['start'] <= pos <= cr['end']:
                return cr['name']
        return ""
