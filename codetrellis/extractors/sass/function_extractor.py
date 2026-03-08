"""
Sass Function Extractor for CodeTrellis

Extracts SCSS/Sass @function definitions, @return statements,
and built-in/custom function call sites.

Supports:
- @function definitions with parameters
- @return statements
- Built-in Sass functions (color, math, string, list, map, selector, meta)
- Custom function calls
- Dart Sass module-namespaced calls (math.round(), color.mix())
- Function composition patterns

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set


@dataclass
class SassFunctionDefInfo:
    """Information about a @function definition."""
    name: str
    parameters: List[str] = field(default_factory=list)
    has_defaults: bool = False
    has_rest_args: bool = False
    return_count: int = 0          # number of @return statements
    file: str = ""
    line_number: int = 0


@dataclass
class SassFunctionCallInfo:
    """Information about a function call."""
    name: str
    category: str = "custom"       # custom, color, math, string, list, map, selector, meta
    namespace: str = ""            # e.g. "math" for math.round()
    is_builtin: bool = False
    file: str = ""
    line_number: int = 0


class SassFunctionExtractor:
    """
    Extracts Sass/SCSS function definitions and calls.
    """

    # @function definition
    FUNCTION_DEF = re.compile(
        r'@function\s+([\w-]+)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # @return statement
    RETURN_PATTERN = re.compile(r'@return\b', re.MULTILINE)

    # Rest args
    REST_ARGS = re.compile(r'\$[\w-]+\.\.\.')

    # Built-in Sass functions by category
    BUILTIN_FUNCTIONS: Dict[str, Set[str]] = {
        'color': {
            'adjust-color', 'scale-color', 'change-color',
            'ie-hex-str', 'red', 'green', 'blue',
            'mix', 'lighten', 'darken', 'saturate', 'desaturate',
            'adjust-hue', 'opacify', 'fade-in', 'transparentize', 'fade-out',
            'alpha', 'opacity', 'rgba', 'rgb', 'hsl', 'hsla', 'hwb',
            'hue', 'saturation', 'lightness', 'complement', 'invert',
            'grayscale', 'color.adjust', 'color.scale', 'color.change',
            'color.mix', 'color.complement', 'color.invert', 'color.grayscale',
            'color.hwb', 'color.ie-hex-str', 'color.red', 'color.green',
            'color.blue', 'color.hue', 'color.saturation', 'color.lightness',
            'color.alpha', 'color.whiteness', 'color.blackness',
            'color.channel', 'color.space', 'color.is-legacy',
            'color.is-powerless', 'color.is-in-gamut', 'color.to-gamut',
            'color.to-space',
        },
        'math': {
            'abs', 'ceil', 'floor', 'round', 'max', 'min',
            'percentage', 'random', 'unit', 'unitless', 'comparable',
            'clamp', 'hypot', 'log', 'pow', 'sqrt',
            'cos', 'sin', 'tan', 'acos', 'asin', 'atan', 'atan2',
            'math.abs', 'math.ceil', 'math.floor', 'math.round',
            'math.max', 'math.min', 'math.percentage', 'math.random',
            'math.unit', 'math.is-unitless', 'math.compatible',
            'math.clamp', 'math.hypot', 'math.log', 'math.pow', 'math.sqrt',
            'math.cos', 'math.sin', 'math.tan', 'math.acos', 'math.asin',
            'math.atan', 'math.atan2', 'math.div',
        },
        'string': {
            'unquote', 'quote', 'str-length', 'str-insert',
            'str-index', 'str-slice', 'to-upper-case', 'to-lower-case',
            'unique-id',
            'string.unquote', 'string.quote', 'string.length',
            'string.insert', 'string.index', 'string.slice',
            'string.to-upper-case', 'string.to-lower-case',
            'string.unique-id', 'string.split',
        },
        'list': {
            'length', 'nth', 'set-nth', 'join', 'append',
            'zip', 'index', 'list-separator', 'is-bracketed', 'separator',
            'list.length', 'list.nth', 'list.set-nth', 'list.join',
            'list.append', 'list.zip', 'list.index', 'list.separator',
            'list.is-bracketed', 'list.slash',
        },
        'map': {
            'map-get', 'map-merge', 'map-remove', 'map-keys',
            'map-values', 'map-has-key',
            'map.get', 'map.merge', 'map.remove', 'map.keys',
            'map.values', 'map.has-key', 'map.set', 'map.deep-merge',
            'map.deep-remove',
        },
        'selector': {
            'selector-nest', 'selector-append', 'selector-extend',
            'selector-replace', 'selector-unify', 'is-superselector',
            'simple-selectors', 'selector-parse',
            'selector.nest', 'selector.append', 'selector.extend',
            'selector.replace', 'selector.unify', 'selector.is-super',
            'selector.simple', 'selector.parse',
        },
        'meta': {
            'type-of', 'inspect', 'variable-exists', 'global-variable-exists',
            'function-exists', 'mixin-exists', 'content-exists',
            'feature-exists', 'call', 'get-function',
            'meta.type-of', 'meta.inspect', 'meta.variable-exists',
            'meta.global-variable-exists', 'meta.function-exists',
            'meta.mixin-exists', 'meta.content-exists',
            'meta.feature-exists', 'meta.call', 'meta.get-function',
            'meta.calc-args', 'meta.calc-name',
            'meta.module-variables', 'meta.module-functions',
            'meta.module-mixins',
        },
    }

    # Build flat set for quick lookup
    ALL_BUILTINS: Set[str] = set()
    BUILTIN_CATEGORY: Dict[str, str] = {}

    def __init__(self):
        # Initialize flat lookup
        for category, funcs in self.BUILTIN_FUNCTIONS.items():
            for func in funcs:
                self.ALL_BUILTINS.add(func)
                self.BUILTIN_CATEGORY[func] = category

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract function definitions and calls.

        Returns:
            Dict with 'definitions', 'calls', 'stats'
        """
        definitions: List[SassFunctionDefInfo] = []
        calls: List[SassFunctionCallInfo] = []

        # Remove comments
        clean = self._remove_comments(content)

        # Extract @function definitions
        for m in self.FUNCTION_DEF.finditer(clean):
            name = m.group(1)
            params_str = m.group(2)
            line_num = clean[:m.start()].count('\n') + 1
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            has_defaults = any(':' in p for p in params)
            has_rest = bool(self.REST_ARGS.search(params_str))

            # Count @return statements in function body
            return_count = self._count_returns(clean, m.end())

            definitions.append(SassFunctionDefInfo(
                name=name,
                parameters=params[:10],
                has_defaults=has_defaults,
                has_rest_args=has_rest,
                return_count=return_count,
                file=file_path,
                line_number=line_num,
            ))

        # Extract function calls (both built-in and custom)
        call_pattern = re.compile(
            r'(?:^|[^@\w-])((?:[\w-]+\.)?[\w-]+)\s*\(',
            re.MULTILINE
        )
        custom_function_names = {d.name for d in definitions}
        seen_calls: Dict[str, SassFunctionCallInfo] = {}

        for m in call_pattern.finditer(clean):
            full_name = m.group(1).strip()
            line_num = clean[:m.start()].count('\n') + 1

            # Skip CSS functions (url, var, calc handled by CSS parser)
            if full_name in ('url', 'var', 'calc', 'env', 'attr',
                             'counter', 'counters', 'format',
                             'local', 'image-set', 'cross-fade',
                             'element', 'paint', 'path'):
                continue

            # Determine namespace
            namespace = ""
            name = full_name
            if '.' in full_name:
                parts = full_name.split('.', 1)
                namespace = parts[0]
                name = parts[1]

            # Check if built-in
            is_builtin = full_name in self.ALL_BUILTINS or name in self.ALL_BUILTINS
            category = "custom"
            if is_builtin:
                category = self.BUILTIN_CATEGORY.get(
                    full_name, self.BUILTIN_CATEGORY.get(name, 'custom')
                )
            elif name in custom_function_names:
                category = "custom"

            # Deduplicate by name
            if full_name not in seen_calls:
                seen_calls[full_name] = SassFunctionCallInfo(
                    name=full_name,
                    category=category,
                    namespace=namespace,
                    is_builtin=is_builtin,
                    file=file_path,
                    line_number=line_num,
                )

        calls = list(seen_calls.values())

        # Categorize call stats
        builtin_categories_used = set()
        for c in calls:
            if c.is_builtin:
                builtin_categories_used.add(c.category)

        stats = {
            "total_definitions": len(definitions),
            "total_calls": len(calls),
            "builtin_calls": sum(1 for c in calls if c.is_builtin),
            "custom_calls": sum(1 for c in calls if not c.is_builtin),
            "builtin_categories_used": sorted(builtin_categories_used),
            "has_color_functions": 'color' in builtin_categories_used,
            "has_math_functions": 'math' in builtin_categories_used,
            "has_map_functions": 'map' in builtin_categories_used,
            "has_meta_functions": 'meta' in builtin_categories_used,
        }

        return {
            "definitions": definitions,
            "calls": calls,
            "stats": stats,
        }

    def _remove_comments(self, content: str) -> str:
        """Remove CSS/SCSS comments."""
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _count_returns(self, content: str, start_pos: int) -> int:
        """Count @return statements in function body."""
        # Find matching brace
        depth = 0
        pos = start_pos
        # Find opening brace
        while pos < len(content) and content[pos] != '{':
            pos += 1
        if pos >= len(content):
            return 0

        depth = 1
        pos += 1
        body_start = pos
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1

        body = content[body_start:pos - 1] if pos > body_start else ""
        return len(self.RETURN_PATTERN.findall(body))
