"""
CSS Function Extractor for CodeTrellis

Extracts CSS function usage patterns from source code.

Supports:
- Math functions: calc(), min(), max(), clamp(), abs(), sign(), round(), mod(), rem()
- Color functions: rgb(), hsl(), oklch(), oklab(), color-mix(), color(), light-dark()
- Transform functions: translate(), rotate(), scale(), skew(), matrix(), perspective()
- Filter functions: blur(), brightness(), contrast(), grayscale(), etc.
- Shape functions: circle(), ellipse(), polygon(), inset(), path()
- Gradient functions: linear-gradient(), radial-gradient(), conic-gradient()
- var() custom property references
- env() environment variables
- url() resource references
- attr() attribute references
- CSS Houdini: paint(), CSSStyleValue
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSFunctionUsageInfo:
    """Information about CSS function usage."""
    function_name: str
    file: str = ""
    line_number: int = 0
    category: str = ""  # math, color, transform, filter, shape, gradient, resource
    arguments: str = ""
    is_nested: bool = False  # Function inside another function
    property_context: str = ""  # Which property uses this function


class CSSFunctionExtractor:
    """
    Extracts CSS function usage from source code.

    Detects all modern CSS functions across categories:
    math, color, transform, filter, shape, gradient, resource, and Houdini.
    """

    FUNCTION_CATEGORIES = {
        'math': {'calc', 'min', 'max', 'clamp', 'abs', 'sign', 'round',
                 'mod', 'rem', 'sin', 'cos', 'tan', 'asin', 'acos',
                 'atan', 'atan2', 'pow', 'sqrt', 'hypot', 'log', 'exp'},
        'color': {'rgb', 'rgba', 'hsl', 'hsla', 'hwb', 'lch', 'oklch',
                  'lab', 'oklab', 'color', 'color-mix', 'color-contrast',
                  'light-dark'},
        'transform': {'translate', 'translateX', 'translateY', 'translateZ',
                      'translate3d', 'rotate', 'rotateX', 'rotateY', 'rotateZ',
                      'rotate3d', 'scale', 'scaleX', 'scaleY', 'scaleZ',
                      'scale3d', 'skew', 'skewX', 'skewY', 'matrix',
                      'matrix3d', 'perspective'},
        'filter': {'blur', 'brightness', 'contrast', 'drop-shadow',
                   'grayscale', 'hue-rotate', 'invert', 'opacity',
                   'saturate', 'sepia'},
        'shape': {'circle', 'ellipse', 'polygon', 'inset', 'path',
                  'rect', 'xywh'},
        'gradient': {'linear-gradient', 'radial-gradient', 'conic-gradient',
                     'repeating-linear-gradient', 'repeating-radial-gradient',
                     'repeating-conic-gradient'},
        'resource': {'url', 'image', 'image-set', 'cross-fade',
                     'element', 'paint'},
        'reference': {'var', 'env', 'attr', 'counter', 'counters',
                      'symbols', 'format', 'local'},
        'timing': {'cubic-bezier', 'steps', 'linear'},
        'grid': {'repeat', 'minmax', 'fit-content'},
    }

    # Build reverse lookup
    _FUNCTION_TO_CATEGORY: Dict[str, str] = {}
    for cat, funcs in FUNCTION_CATEGORIES.items():
        for f in funcs:
            _FUNCTION_TO_CATEGORY[f] = cat

    # Pattern to match CSS functions
    FUNCTION_PATTERN = re.compile(
        r'([\w-]+)\s*\(',
        re.MULTILINE
    )

    # Property context pattern - find property name before function
    PROPERTY_CONTEXT = re.compile(
        r'([\w-]+)\s*:\s*[^;]*$'
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract CSS function usage from source code.

        Returns dict with:
          - functions: List[CSSFunctionUsageInfo]
          - stats: Dict with counts by category
        """
        functions: List[CSSFunctionUsageInfo] = []
        category_counts: Dict[str, int] = {}
        seen_functions: set = set()

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        for match in self.FUNCTION_PATTERN.finditer(clean):
            func_name = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1

            # Skip non-CSS functions (selectors, etc.)
            category = self._FUNCTION_TO_CATEGORY.get(func_name, "")
            if not category:
                # Check for vendor-prefixed versions
                unprefixed = re.sub(r'^-(webkit|moz|ms|o)-', '', func_name)
                category = self._FUNCTION_TO_CATEGORY.get(unprefixed, "")
                if not category:
                    continue

            # Get property context
            before = clean[:match.start()]
            lines_before = before.split('\n')
            last_line = lines_before[-1] if lines_before else ""
            prop_match = self.PROPERTY_CONTEXT.search(last_line)
            prop_context = prop_match.group(1) if prop_match else ""

            # Check for nesting
            is_nested = self._is_nested_function(clean, match.start())

            # Deduplicate by (function, line)
            key = (func_name, line_num)
            if key in seen_functions:
                continue
            seen_functions.add(key)

            functions.append(CSSFunctionUsageInfo(
                function_name=func_name,
                file=file_path,
                line_number=line_num,
                category=category,
                is_nested=is_nested,
                property_context=prop_context,
            ))

            category_counts[category] = category_counts.get(category, 0) + 1

        stats = {
            "total_function_calls": len(functions),
            "categories": category_counts,
            "unique_functions": len(set(f.function_name for f in functions)),
            "has_modern_color": any(f.function_name in {'oklch', 'oklab', 'color-mix', 'light-dark'}
                                   for f in functions),
            "has_container_queries": any(f.function_name == 'cqi' for f in functions),
            "has_math_functions": 'math' in category_counts,
            "has_gradients": 'gradient' in category_counts,
        }

        return {
            "functions": functions,
            "stats": stats,
        }

    def _is_nested_function(self, content: str, pos: int) -> bool:
        """Check if a function call is nested inside another function."""
        # Count open parens before this position on the same declaration
        before = content[:pos]
        last_semicolon = before.rfind(';')
        last_brace = before.rfind('{')
        start = max(last_semicolon, last_brace, 0)
        segment = before[start:pos]

        open_parens = segment.count('(')
        close_parens = segment.count(')')
        return open_parens > close_parens
