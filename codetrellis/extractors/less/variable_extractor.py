"""
Less Variable Extractor for CodeTrellis

Extracts Less @variable declarations, lazy evaluation, scope, and property merging.

Supports:
- @variable declarations with values
- Variable interpolation @{var}
- Lazy evaluation (variables can be defined after use)
- Variable scoping (global vs local)
- Property as variable: $prop (Less 3.0+)
- Variable overriding (last definition wins)
- CSS Custom Properties passthrough (--var)
- Variable type detection (color, number, string, dimension, etc.)

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class LessVariableInfo:
    """Information about a Less @variable declaration."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    scope: str = "global"         # global, local
    data_type: str = "value"      # value, color, number, string, dimension, url, list, bool
    is_overridden: bool = False   # Variable redefined later
    is_lazy: bool = False         # Used before definition (lazy evaluation)


@dataclass
class LessVariableUsageInfo:
    """Information about a Less variable usage."""
    name: str
    context: str = ""             # property-value, selector, import, mixin-arg, guard
    is_interpolated: bool = False  # @{var} interpolation syntax
    file: str = ""
    line_number: int = 0


class LessVariableExtractor:
    """
    Extracts Less @variable declarations and usages.

    Less variables use @ prefix: @variable: value;
    Less supports lazy evaluation — variables can be referenced before definition.
    Less uses last-definition-wins for variable scoping.
    """

    # Less @variable declarations: @name: value;
    VARIABLE_PATTERN = re.compile(
        r'^[ \t]*(@[\w-]+)\s*:\s*([^;]+?)\s*;',
        re.MULTILINE
    )

    # Variable interpolation: @{var}
    INTERPOLATION_PATTERN = re.compile(r'@\{([\w-]+)\}')

    # Variable usage: @var (not followed by :, indicating usage not declaration)
    USAGE_PATTERN = re.compile(
        r'(?<!["\'])(@[\w-]+)(?!\s*:)(?!\{)',
        re.MULTILINE
    )

    # Property as variable: $prop (Less 3.0+)
    PROPERTY_VAR_PATTERN = re.compile(r'\$[\w-]+')

    # Color patterns for type detection
    COLOR_PATTERN = re.compile(
        r'^(?:#[0-9a-fA-F]{3,8}|'
        r'(?:rgb|rgba|hsl|hsla|hwb|lab|lch|oklch|oklab|color)\s*\(|'
        r'(?:red|blue|green|yellow|black|white|gray|grey|orange|purple|'
        r'pink|cyan|magenta|lime|olive|navy|teal|aqua|fuchsia|silver|'
        r'maroon|transparent|currentColor|inherit)$)',
        re.IGNORECASE
    )

    # Dimension patterns
    DIMENSION_PATTERN = re.compile(
        r'^-?[\d.]+(?:px|em|rem|%|vh|vw|vmin|vmax|ch|ex|cm|mm|in|pt|pc|'
        r'deg|rad|grad|turn|s|ms|Hz|kHz|dpi|dpcm|dppx|fr)$',
        re.IGNORECASE
    )

    # Number pattern
    NUMBER_PATTERN = re.compile(r'^-?[\d.]+$')

    # String pattern
    STRING_PATTERN = re.compile(r'^["\'].*["\']$')

    # URL pattern
    URL_PATTERN = re.compile(r'^url\s*\(', re.IGNORECASE)

    # Boolean pattern
    BOOLEAN_PATTERN = re.compile(r'^(?:true|false)$', re.IGNORECASE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Less variable declarations and usages.

        Returns dict with 'variables', 'usages', 'stats' keys.
        """
        if not content or not content.strip():
            return {'variables': [], 'usages': [], 'stats': {}}

        # Strip comments for accurate parsing
        clean_content = self._strip_comments(content)

        variables = self._extract_variables(clean_content, file_path)
        usages = self._extract_usages(clean_content, file_path)
        interpolations = self._extract_interpolations(clean_content, file_path)
        usages.extend(interpolations)

        # Detect lazy evaluation
        var_names = {v.name for v in variables}
        var_lines = {v.name: v.line_number for v in variables}
        for usage in usages:
            if usage.name in var_names:
                var_line = var_lines.get(usage.name, 0)
                if var_line > usage.line_number:
                    usage.is_lazy = True
                    for v in variables:
                        if v.name == usage.name:
                            v.is_lazy = True

        # Detect overrides
        name_counts: Dict[str, int] = {}
        for v in variables:
            name_counts[v.name] = name_counts.get(v.name, 0) + 1
        for v in variables:
            if name_counts.get(v.name, 0) > 1:
                v.is_overridden = True

        stats = {
            'total_variables': len(variables),
            'total_usages': len(usages),
            'total_interpolations': len([u for u in usages if u.is_interpolated]),
            'has_lazy_evaluation': any(v.is_lazy for v in variables),
            'has_overrides': any(v.is_overridden for v in variables),
            'has_property_vars': bool(self.PROPERTY_VAR_PATTERN.search(clean_content)),
            'data_types': list(set(v.data_type for v in variables)),
        }

        return {'variables': variables, 'usages': usages, 'stats': stats}

    def _strip_comments(self, content: str) -> str:
        """Strip Less comments (// and /* */) preserving line structure."""
        # Remove block comments
        result = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), content, flags=re.DOTALL)
        # Remove line comments
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_variables(self, content: str, file_path: str) -> List[LessVariableInfo]:
        """Extract @variable declarations."""
        variables: List[LessVariableInfo] = []
        lines = content.split('\n')

        for match in self.VARIABLE_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2).strip()

            # Skip CSS at-rules that look like variables
            if name.lower() in ('@import', '@media', '@keyframes', '@font-face',
                                 '@charset', '@namespace', '@supports', '@page',
                                 '@layer', '@container', '@scope', '@property',
                                 '@plugin'):
                continue

            # Determine line number
            line_num = content[:match.start()].count('\n') + 1

            # Detect scope
            scope = self._detect_scope(content, match.start())

            # Detect data type
            data_type = self._detect_type(value)

            variables.append(LessVariableInfo(
                name=name,
                value=value[:200],  # truncate long values
                file=file_path,
                line_number=line_num,
                scope=scope,
                data_type=data_type,
            ))

        return variables

    def _extract_usages(self, content: str, file_path: str) -> List[LessVariableUsageInfo]:
        """Extract variable usages (non-declaration references)."""
        usages: List[LessVariableUsageInfo] = []

        # Find all @var usages that are NOT declarations
        for match in self.USAGE_PATTERN.finditer(content):
            name = match.group(1)

            # Skip CSS at-rules
            if name.lower() in ('@import', '@media', '@keyframes', '@font-face',
                                 '@charset', '@namespace', '@supports', '@page',
                                 '@layer', '@container', '@scope', '@property',
                                 '@plugin', '@arguments', '@rest'):
                continue

            # Check it's not a declaration
            after = content[match.end():match.end() + 5]
            if after.lstrip().startswith(':'):
                continue

            line_num = content[:match.start()].count('\n') + 1
            context = self._detect_usage_context(content, match.start())

            usages.append(LessVariableUsageInfo(
                name=name,
                context=context,
                is_interpolated=False,
                file=file_path,
                line_number=line_num,
            ))

        return usages

    def _extract_interpolations(self, content: str, file_path: str) -> List[LessVariableUsageInfo]:
        """Extract @{variable} interpolations."""
        interpolations: List[LessVariableUsageInfo] = []

        for match in self.INTERPOLATION_PATTERN.finditer(content):
            name = f"@{match.group(1)}"
            line_num = content[:match.start()].count('\n') + 1
            context = self._detect_usage_context(content, match.start())

            interpolations.append(LessVariableUsageInfo(
                name=name,
                context=context,
                is_interpolated=True,
                file=file_path,
                line_number=line_num,
            ))

        return interpolations

    def _detect_scope(self, content: str, pos: int) -> str:
        """Detect if variable is global or local (inside a ruleset)."""
        before = content[:pos]
        open_braces = before.count('{') - before.count('}')
        if open_braces > 0:
            return 'local'
        return 'global'

    def _detect_type(self, value: str) -> str:
        """Detect the data type of a variable value."""
        value = value.strip()

        if self.COLOR_PATTERN.match(value):
            return 'color'
        if self.URL_PATTERN.match(value):
            return 'url'
        if self.STRING_PATTERN.match(value):
            return 'string'
        if self.BOOLEAN_PATTERN.match(value):
            return 'bool'
        if self.DIMENSION_PATTERN.match(value):
            return 'dimension'
        if self.NUMBER_PATTERN.match(value):
            return 'number'
        if ',' in value and not value.startswith('('):
            return 'list'

        return 'value'

    def _detect_usage_context(self, content: str, pos: int) -> str:
        """Detect where a variable is used: property-value, selector, etc."""
        # Get line containing the usage
        line_start = content.rfind('\n', 0, pos) + 1
        line_end = content.find('\n', pos)
        if line_end == -1:
            line_end = len(content)
        line = content[line_start:line_end].strip()

        if ':' in line[:line.find('@') if '@' in line else len(line)]:
            return 'property-value'
        if line.startswith('.') or line.startswith('#') or line.startswith('&'):
            return 'selector'
        if '@import' in line:
            return 'import'
        if 'when' in line:
            return 'guard'

        return 'property-value'
