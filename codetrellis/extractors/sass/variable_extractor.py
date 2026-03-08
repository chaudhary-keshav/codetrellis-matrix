"""
Sass Variable Extractor for CodeTrellis

Extracts SCSS/Sass variable declarations, maps, lists, and flags.

Supports:
- $variable declarations with values
- !default, !global, !important flags
- Sass Maps: $map: (key: value, ...)
- Sass Lists: $list: value1, value2, ...  or (value1, value2)
- Nested maps
- Variable interpolation #{$var}
- Variable scoping (global vs local)
- Dart Sass 1.x module namespaces (namespace.$var)

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SassVariableInfo:
    """Information about a Sass $variable declaration."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    is_default: bool = False      # !default flag
    is_global: bool = False       # !global flag
    scope: str = "global"         # global, local, parameter
    data_type: str = "value"      # value, color, number, string, bool, null, list, map
    namespace: str = ""           # e.g. "math" for math.$pi


@dataclass
class SassMapInfo:
    """Information about a Sass map."""
    name: str
    keys: List[str] = field(default_factory=list)
    is_nested: bool = False
    entry_count: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class SassListInfo:
    """Information about a Sass list."""
    name: str
    items: List[str] = field(default_factory=list)
    separator: str = "comma"      # comma, space, slash
    is_bracketed: bool = False    # [list] vs (list)
    file: str = ""
    line_number: int = 0


class SassVariableExtractor:
    """
    Extracts Sass/SCSS variable declarations, maps, and lists.

    Handles both SCSS (.scss) and indented Sass (.sass) syntax.
    """

    # SCSS $variable declarations
    VARIABLE_PATTERN = re.compile(
        r'(\$[\w-]+)\s*:\s*([^;{]+?)(\s*!default)?(\s*!global)?\s*;',
        re.MULTILINE
    )

    # Sass (indented) variable: $var: value (no semicolon)
    SASS_VARIABLE_PATTERN = re.compile(
        r'^(\$[\w-]+)\s*:\s*(.+?)(\s*!default)?(\s*!global)?\s*$',
        re.MULTILINE
    )

    # Map pattern: $map: (key: value, ...)
    MAP_PATTERN = re.compile(
        r'(\$[\w-]+)\s*:\s*\(([^)]*(?:\([^)]*\)[^)]*)*)\)\s*(?:!default\s*)?;',
        re.DOTALL | re.MULTILINE
    )

    # Namespaced variable usage: namespace.$var
    NAMESPACE_VAR_PATTERN = re.compile(
        r'([\w-]+)\.\$([\w-]+)',
        re.MULTILINE
    )

    # Variable interpolation: #{$var}
    INTERPOLATION_PATTERN = re.compile(r'#\{\$[\w-]+\}')

    # Color patterns for type detection
    COLOR_PATTERN = re.compile(
        r'^(?:#[0-9a-fA-F]{3,8}|'
        r'(?:rgb|rgba|hsl|hsla|hwb|lab|lch|oklch|oklab|color)\s*\(|'
        r'(?:red|blue|green|yellow|black|white|gray|grey|orange|purple|'
        r'pink|cyan|magenta|lime|olive|navy|teal|aqua|fuchsia|silver|'
        r'maroon|transparent|currentColor|inherit)$)',
        re.IGNORECASE
    )

    # Number pattern
    NUMBER_PATTERN = re.compile(
        r'^-?\d+(?:\.\d+)?(?:px|em|rem|%|vh|vw|vmin|vmax|ch|ex|'
        r'cm|mm|in|pt|pc|deg|rad|grad|turn|s|ms|Hz|kHz|dpi|dpcm|dppx|fr)?$'
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Sass variables, maps, and lists.

        Returns:
            Dict with 'variables', 'maps', 'lists', 'stats'
        """
        variables: List[SassVariableInfo] = []
        maps: List[SassMapInfo] = []
        lists: List[SassListInfo] = []

        # Remove comments
        clean = self._remove_comments(content)

        is_sass = file_path.lower().endswith('.sass')

        # Extract maps first (they are also variables but with structure)
        map_names = set()
        for m in self.MAP_PATTERN.finditer(clean):
            name = m.group(1)
            body = m.group(2).strip()
            line_num = clean[:m.start()].count('\n') + 1
            keys = self._extract_map_keys(body)
            is_nested = '(' in body[1:] if len(body) > 1 else False
            map_names.add(name)
            maps.append(SassMapInfo(
                name=name,
                keys=keys,
                is_nested=is_nested,
                entry_count=len(keys),
                file=file_path,
                line_number=line_num,
            ))

        # Extract variables
        pattern = self.SASS_VARIABLE_PATTERN if is_sass else self.VARIABLE_PATTERN
        for m in pattern.finditer(clean):
            name = m.group(1)
            value = m.group(2).strip()
            is_default = bool(m.group(3))
            is_global = bool(m.group(4))
            line_num = clean[:m.start()].count('\n') + 1

            # Detect data type
            data_type = self._detect_type(value)

            # Check if it's a list
            if name not in map_names and data_type == 'value':
                list_info = self._detect_list(name, value, file_path, line_num)
                if list_info:
                    lists.append(list_info)
                    data_type = 'list'

            if name in map_names:
                data_type = 'map'

            variables.append(SassVariableInfo(
                name=name,
                value=value[:120],
                file=file_path,
                line_number=line_num,
                is_default=is_default,
                is_global=is_global,
                data_type=data_type,
            ))

        # Count interpolations
        interpolation_count = len(self.INTERPOLATION_PATTERN.findall(clean))

        # Count namespace usages
        namespace_usages = self.NAMESPACE_VAR_PATTERN.findall(clean)
        namespaces_used = list(set(ns for ns, _ in namespace_usages))

        stats = {
            "total_variables": len(variables),
            "total_maps": len(maps),
            "total_lists": len(lists),
            "default_count": sum(1 for v in variables if v.is_default),
            "global_count": sum(1 for v in variables if v.is_global),
            "interpolation_count": interpolation_count,
            "namespaces_used": namespaces_used,
            "has_maps": len(maps) > 0,
            "has_lists": len(lists) > 0,
            "has_defaults": any(v.is_default for v in variables),
            "has_namespaces": len(namespaces_used) > 0,
        }

        return {
            "variables": variables,
            "maps": maps,
            "lists": lists,
            "stats": stats,
        }

    def _remove_comments(self, content: str) -> str:
        """Remove CSS/SCSS comments."""
        # Block comments
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Line comments
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_map_keys(self, body: str) -> List[str]:
        """Extract keys from a map body string."""
        keys = []
        depth = 0
        current_key = ""
        for char in body:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ':' and depth == 0 and current_key.strip():
                keys.append(current_key.strip())
                current_key = ""
                # Skip the value
                continue
            elif char == ',' and depth == 0:
                current_key = ""
                continue

            if depth == 0 and char != ',':
                current_key += char

        return keys

    def _detect_type(self, value: str) -> str:
        """Detect the data type of a Sass variable value."""
        value = value.strip().rstrip('!default').rstrip('!global').strip()

        if value.startswith('(') and ')' in value:
            # Could be a map or list
            if ':' in value:
                return 'map'
            return 'list'

        if self.COLOR_PATTERN.match(value):
            return 'color'

        if self.NUMBER_PATTERN.match(value):
            return 'number'

        if value.startswith('"') or value.startswith("'"):
            return 'string'

        if value in ('true', 'false'):
            return 'bool'

        if value == 'null':
            return 'null'

        return 'value'

    def _detect_list(self, name: str, value: str, file_path: str,
                     line_num: int) -> Optional[SassListInfo]:
        """Detect if a variable value is a list."""
        # Comma-separated values (more than 1 comma)
        if ',' in value and value.count(',') >= 1:
            items = [item.strip() for item in value.split(',') if item.strip()]
            if len(items) >= 2:
                return SassListInfo(
                    name=name,
                    items=items[:10],
                    separator="comma",
                    is_bracketed=value.startswith('['),
                    file=file_path,
                    line_number=line_num,
                )

        # Space-separated (at least 3 tokens, avoiding property shorthand)
        tokens = value.split()
        if len(tokens) >= 3 and not any(
            t.endswith(':') for t in tokens
        ):
            # Likely a list if name suggests collection
            if any(kw in name.lower() for kw in
                   ('list', 'items', 'sizes', 'colors', 'breakpoints',
                    'fonts', 'weights', 'spacers', 'values')):
                return SassListInfo(
                    name=name,
                    items=tokens[:10],
                    separator="space",
                    file=file_path,
                    line_number=line_num,
                )

        return None
