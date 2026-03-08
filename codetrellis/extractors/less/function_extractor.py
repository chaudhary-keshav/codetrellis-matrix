"""
Less Function Extractor for CodeTrellis

Extracts Less built-in function calls, custom plugins, and function usage patterns.

Supports 70+ built-in functions across categories:
- **Color**: color(), rgb(), rgba(), hsl(), hsla(), hsv(), hsva(),
  darken(), lighten(), saturate(), desaturate(), fadein(), fadeout(),
  fade(), spin(), mix(), tint(), shade(), greyscale(), contrast(),
  multiply(), screen(), overlay(), softlight(), hardlight(),
  difference(), exclusion(), average(), negation()
- **Math**: ceil(), floor(), round(), sqrt(), abs(), pow(), mod(),
  min(), max(), percentage(), pi(), e(), acos(), asin(), atan(),
  sin(), cos(), tan()
- **String**: escape(), e(), %(format), replace()
- **List**: length(), extract(), range(), each()
- **Type**: isnumber(), isstring(), iscolor(), iskeyword(), isurl(),
  ispixel(), isem(), ispercentage(), isunit(), isruleset(), isdefined()
- **Misc**: unit(), convert(), data-uri(), image-size(),
  image-width(), image-height(), svg-gradient(), get-unit(),
  if(), boolean()
- **Color Channels**: hue(), saturation(), lightness(), hsvhue(),
  hsvsaturation(), hsvvalue(), red(), green(), blue(), alpha(),
  luma(), luminance()

Less 3.5+: @plugin support for custom functions

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set


@dataclass
class LessFunctionCallInfo:
    """Information about a Less function call."""
    name: str
    category: str = "custom"       # color, math, string, list, type, misc, channel, custom
    is_builtin: bool = False
    argument_count: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class LessPluginInfo:
    """Information about a Less @plugin directive."""
    name: str
    path: str = ""
    options: str = ""
    file: str = ""
    line_number: int = 0


class LessFunctionExtractor:
    """
    Extracts Less built-in and custom function calls, and @plugin directives.
    """

    # Built-in functions by category
    BUILTIN_FUNCTIONS: Dict[str, Set[str]] = {
        'color': {
            'color', 'rgb', 'rgba', 'hsl', 'hsla', 'hsv', 'hsva',
            'argb', 'darken', 'lighten', 'saturate', 'desaturate',
            'fadein', 'fadeout', 'fade', 'spin', 'mix', 'tint', 'shade',
            'greyscale', 'contrast',
        },
        'color_blending': {
            'multiply', 'screen', 'overlay', 'softlight', 'hardlight',
            'difference', 'exclusion', 'average', 'negation',
        },
        'color_channel': {
            'hue', 'saturation', 'lightness', 'hsvhue', 'hsvsaturation',
            'hsvvalue', 'red', 'green', 'blue', 'alpha', 'luma', 'luminance',
        },
        'math': {
            'ceil', 'floor', 'round', 'sqrt', 'abs', 'pow', 'mod',
            'min', 'max', 'percentage', 'pi', 'e',
            'acos', 'asin', 'atan', 'sin', 'cos', 'tan',
        },
        'string': {
            'escape', 'replace',
        },
        'list': {
            'length', 'extract', 'range', 'each',
        },
        'type': {
            'isnumber', 'isstring', 'iscolor', 'iskeyword', 'isurl',
            'ispixel', 'isem', 'ispercentage', 'isunit', 'isruleset',
            'isdefined',
        },
        'misc': {
            'unit', 'convert', 'data-uri', 'image-size',
            'image-width', 'image-height', 'svg-gradient',
            'get-unit', 'if', 'boolean', 'default',
        },
    }

    # Build flat lookup: function_name -> category
    _FUNC_CATEGORY: Dict[str, str] = {}
    for _cat, _funcs in BUILTIN_FUNCTIONS.items():
        for _fn in _funcs:
            _FUNC_CATEGORY[_fn.lower()] = _cat

    # All built-in function names
    ALL_BUILTINS: Set[str] = set()
    for _funcs in BUILTIN_FUNCTIONS.values():
        ALL_BUILTINS |= _funcs

    # Function call pattern: name(
    FUNCTION_CALL_PATTERN = re.compile(
        r'(?<![.\w@$#-])([\w-]+)\s*\(',
        re.MULTILINE
    )

    # Less e() / ~"..." escaping
    ESCAPE_PATTERN = re.compile(r'~\s*["\']|e\s*\(', re.MULTILINE)

    # @plugin directive (Less 3.5+)
    PLUGIN_PATTERN = re.compile(
        r'@plugin\s+(?:\(([^)]*)\)\s+)?["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Format string: %(format, args)
    FORMAT_PATTERN = re.compile(r'%\s*\(', re.MULTILINE)

    # CSS functions to exclude from Less function tracking
    CSS_FUNCTIONS = {
        'url', 'calc', 'var', 'env', 'attr', 'counter', 'counters',
        'linear-gradient', 'radial-gradient', 'conic-gradient',
        'repeating-linear-gradient', 'repeating-radial-gradient',
        'clamp', 'cubic-bezier', 'steps', 'format', 'local',
        'rotate', 'scale', 'translate', 'skew', 'matrix',
        'rotate3d', 'scale3d', 'translate3d', 'perspective',
        'translateX', 'translateY', 'translateZ',
        'scaleX', 'scaleY', 'rotateX', 'rotateY', 'rotateZ',
        'polygon', 'circle', 'ellipse', 'inset', 'path',
        'drop-shadow', 'blur', 'brightness', 'contrast', 'grayscale',
        'hue-rotate', 'invert', 'opacity', 'saturate', 'sepia',
        'minmax', 'fit-content', 'repeat',
        'color-mix', 'oklch', 'oklab', 'light-dark',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Less function calls and @plugin directives.

        Returns dict with 'calls', 'plugins', 'stats' keys.
        """
        if not content or not content.strip():
            return {'calls': [], 'plugins': [], 'stats': {}}

        clean = self._strip_comments(content)

        calls = self._extract_function_calls(clean, file_path)
        plugins = self._extract_plugins(clean, file_path)

        # Aggregate by category
        by_category: Dict[str, int] = {}
        for c in calls:
            by_category[c.category] = by_category.get(c.category, 0) + 1

        stats = {
            'total_calls': len(calls),
            'total_plugins': len(plugins),
            'builtin_calls': sum(1 for c in calls if c.is_builtin),
            'custom_calls': sum(1 for c in calls if not c.is_builtin),
            'by_category': by_category,
            'has_color_functions': by_category.get('color', 0) > 0 or by_category.get('color_blending', 0) > 0,
            'has_math_functions': by_category.get('math', 0) > 0,
            'has_type_functions': by_category.get('type', 0) > 0,
            'has_string_functions': by_category.get('string', 0) > 0,
            'has_list_functions': by_category.get('list', 0) > 0,
            'has_plugins': len(plugins) > 0,
            'has_escape': bool(self.ESCAPE_PATTERN.search(clean)),
            'has_format_string': bool(self.FORMAT_PATTERN.search(clean)),
        }

        return {'calls': calls, 'plugins': plugins, 'stats': stats}

    def _strip_comments(self, content: str) -> str:
        """Strip Less comments preserving line structure."""
        result = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_function_calls(self, content: str, file_path: str) -> List[LessFunctionCallInfo]:
        """Extract function calls from Less content."""
        calls: List[LessFunctionCallInfo] = []
        seen: Dict[str, LessFunctionCallInfo] = {}

        for match in self.FUNCTION_CALL_PATTERN.finditer(content):
            name = match.group(1).lower()

            # Skip CSS-native functions
            if name in self.CSS_FUNCTIONS:
                continue

            # Skip @keyframes names
            before = content[max(0, match.start() - 20):match.start()].strip()
            if before.endswith('@keyframes') or before.endswith('@-webkit-keyframes'):
                continue

            line_num = content[:match.start()].count('\n') + 1

            # Determine category
            is_builtin = name in self.ALL_BUILTINS
            category = self._FUNC_CATEGORY.get(name, 'custom')

            # Count arguments
            arg_start = match.end()
            arg_end = self._find_matching_paren(content, arg_start - 1)
            args_str = content[arg_start:arg_end] if arg_end > arg_start else ""
            arg_count = len([a for a in args_str.split(',') if a.strip()]) if args_str.strip() else 0

            if name not in seen:
                info = LessFunctionCallInfo(
                    name=name,
                    category=category,
                    is_builtin=is_builtin,
                    argument_count=arg_count,
                    file=file_path,
                    line_number=line_num,
                )
                seen[name] = info
                calls.append(info)

        return calls

    def _extract_plugins(self, content: str, file_path: str) -> List[LessPluginInfo]:
        """Extract @plugin directives."""
        plugins: List[LessPluginInfo] = []

        for match in self.PLUGIN_PATTERN.finditer(content):
            options = match.group(1) or ""
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Extract plugin name from path
            name = path.split('/')[-1].replace('.js', '').replace('.less', '')

            plugins.append(LessPluginInfo(
                name=name,
                path=path,
                options=options,
                file=file_path,
                line_number=line_num,
            ))

        return plugins

    def _find_matching_paren(self, content: str, start: int) -> int:
        """Find matching closing parenthesis."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(content)
