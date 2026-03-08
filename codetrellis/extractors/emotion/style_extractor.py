"""
Emotion Style Extractor for CodeTrellis

Extracts Emotion CSS-in-JS style patterns from JS/TS source code.
Covers:
- css prop (string and object syntax, the signature Emotion feature)
- css() function from @emotion/css (framework-agnostic)
- css`` tagged template from @emotion/react
- cx() utility for className composition (@emotion/css)
- ClassNames render prop component (@emotion/react)
- CSS property detection (layout, typography, color, spacing, etc.)
- Media query patterns
- Pseudo-selectors
- Dynamic styling patterns
- CSS nesting with & parent selector
- CSS variables

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmotionCssPropInfo:
    """Information about a css prop usage on a JSX element."""
    file: str = ""
    line_number: int = 0
    element: str = ""           # The JSX element with css prop
    syntax: str = ""            # string, object, template, array
    has_theme_usage: bool = False
    has_conditional: bool = False
    css_properties_count: int = 0


@dataclass
class EmotionCssFunctionInfo:
    """Information about a css() or css`` function call."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    syntax: str = ""            # tagged-template, function-call, object
    has_interpolation: bool = False
    has_nesting: bool = False
    css_properties_count: int = 0
    is_composition: bool = False    # Used for composing multiple css rules


@dataclass
class EmotionClassNamesInfo:
    """Information about a ClassNames render prop usage."""
    file: str = ""
    line_number: int = 0
    has_css_call: bool = False
    has_cx_call: bool = False
    has_theme: bool = False


@dataclass
class EmotionStylePatternInfo:
    """Information about CSS patterns within Emotion-styled content."""
    component: str = ""
    file: str = ""
    line_number: int = 0
    categories: List[str] = field(default_factory=list)
    css_properties_count: int = 0
    has_nesting: bool = False
    nesting_depth: int = 0
    has_pseudo_selectors: bool = False
    has_css_variables: bool = False
    has_flexbox: bool = False
    has_grid: bool = False


@dataclass
class EmotionDynamicPropInfo:
    """Information about dynamic prop-based styling."""
    component: str = ""
    file: str = ""
    line_number: int = 0
    prop_name: str = ""
    pattern: str = ""           # ternary, logical, function, theme-function
    has_ternary: bool = False
    has_theme_access: bool = False


@dataclass
class EmotionMediaQueryInfo:
    """Information about a media query in Emotion styles."""
    component: str = ""
    file: str = ""
    line_number: int = 0
    breakpoint: str = ""
    approach: str = ""          # inline, helper, facepaint, theme
    is_mobile_first: bool = False
    has_orientation: bool = False


class EmotionStyleExtractor:
    """
    Extracts Emotion CSS-in-JS style patterns from JS/TS/JSX/TSX source code.

    Detects:
    - css prop on JSX elements (string, object, template, array composition)
    - css() function call from @emotion/css
    - css`` tagged template from @emotion/react
    - cx() utility for className composition
    - ClassNames render prop component
    - CSS property categories
    - Media queries (inline, helper, facepaint)
    - Dynamic styling patterns (ternary, logical, theme functions)
    - CSS nesting and pseudo-selectors
    """

    # Regex: css prop usage on JSX elements
    RE_CSS_PROP = re.compile(
        r"<(\w+)[^>]*\bcss\s*=\s*\{",
        re.MULTILINE
    )

    # Regex: css`` tagged template literal (standalone or assigned)
    RE_CSS_TEMPLATE = re.compile(
        r"(?:(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*)?css\s*`",
        re.MULTILINE
    )

    # Regex: css() function call (object syntax)
    RE_CSS_FUNCTION = re.compile(
        r"(?:(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*)?css\s*\(\s*(?:\{|`)",
        re.MULTILINE
    )

    # Regex: cx() composition utility
    RE_CX = re.compile(
        r"\bcx\s*\(",
        re.MULTILINE
    )

    # Regex: ClassNames render prop component
    RE_CLASSNAMES = re.compile(
        r"<ClassNames\b",
        re.MULTILINE
    )

    # Regex: Media query in styles
    RE_MEDIA_QUERY = re.compile(
        r"@media\s*\(\s*(min-width|max-width|min-height|max-height|orientation)\s*:\s*([^)]+)\)",
        re.MULTILINE
    )

    # Regex: Pseudo-selectors
    RE_PSEUDO = re.compile(
        r"&\s*:(?:hover|focus|active|disabled|first-child|last-child|nth-child|"
        r"before|after|focus-within|focus-visible|placeholder|not|checked|visited)",
        re.MULTILINE
    )

    # Regex: CSS nesting
    RE_NESTING = re.compile(r"&\s*[.:#\[\s{>+~]", re.MULTILINE)

    # Regex: CSS variables
    RE_CSS_VAR = re.compile(r"--[\w-]+\s*:", re.MULTILINE)

    # Regex: Flexbox
    RE_FLEXBOX = re.compile(
        r"display\s*:\s*(?:inline-)?flex|flex-direction|justify-content|align-items|flex-wrap|flex-grow|flex-shrink|gap",
        re.MULTILINE | re.IGNORECASE
    )

    # Regex: Grid
    RE_GRID = re.compile(
        r"display\s*:\s*(?:inline-)?grid|grid-template|grid-column|grid-row|grid-area|grid-gap",
        re.MULTILINE | re.IGNORECASE
    )

    # Regex: Dynamic prop interpolation
    RE_DYNAMIC = re.compile(
        r"\$\{\s*(?:props\s*=>|(?:\(\s*\{[^}]*\}\s*\))\s*=>|\(\s*props\s*\)\s*=>)",
        re.MULTILINE
    )

    # Regex: Ternary in interpolation
    RE_TERNARY = re.compile(r"\?\s*['\"`\w]+\s*:", re.MULTILINE)

    # Regex: Theme access
    RE_THEME_ACCESS = re.compile(
        r"(?:props\.theme|theme\.\w+|\(\s*\{\s*theme\s*\}\s*\)\s*=>)",
        re.MULTILINE
    )

    # Regex: facepaint media queries
    RE_FACEPAINT = re.compile(r"facepaint\s*\(", re.MULTILINE)

    # CSS property categories
    CSS_CATEGORIES = {
        'layout': re.compile(r'(?:display|position|float|clear|overflow|z-index|visibility)\s*:', re.I),
        'flexbox': re.compile(r'(?:flex|justify-content|align-items|align-self|flex-wrap|flex-direction|gap)\s*:', re.I),
        'grid': re.compile(r'(?:grid-template|grid-column|grid-row|grid-area|grid-gap)\s*:', re.I),
        'spacing': re.compile(r'(?:margin|padding|gap)\s*:', re.I),
        'sizing': re.compile(r'(?:width|height|max-width|max-height|min-width|min-height)\s*:', re.I),
        'typography': re.compile(r'(?:font|letter-spacing|line-height|text-align|text-transform|word-break|white-space)\s*:', re.I),
        'color': re.compile(r'(?:color|background|opacity|background-color)\s*:', re.I),
        'border': re.compile(r'(?:border|border-radius|outline|box-shadow)\s*:', re.I),
        'transform': re.compile(r'(?:transform|scale|rotate|translate)\s*:', re.I),
        'transition': re.compile(r'(?:transition|animation)\s*:', re.I),
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Emotion style patterns.

        Returns:
            Dict with 'css_props', 'css_functions', 'classnames', 'style_patterns',
            'dynamic_props', 'media_queries' lists.
        """
        css_props: List[EmotionCssPropInfo] = []
        css_functions: List[EmotionCssFunctionInfo] = []
        classnames: List[EmotionClassNamesInfo] = []
        style_patterns: List[EmotionStylePatternInfo] = []
        dynamic_props: List[EmotionDynamicPropInfo] = []
        media_queries: List[EmotionMediaQueryInfo] = []

        if not content or not content.strip():
            return {
                'css_props': css_props,
                'css_functions': css_functions,
                'classnames': classnames,
                'style_patterns': style_patterns,
                'dynamic_props': dynamic_props,
                'media_queries': media_queries,
            }

        # ── css prop usage ──────────────────────────────────────
        for match in self.RE_CSS_PROP.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            element = match.group(1)

            context = content[match.start():match.start() + 500]
            syntax = "object"
            if re.search(r'css\s*=\s*\{\s*css`', context):
                syntax = "template"
            elif re.search(r'css\s*=\s*\{\s*\[', context):
                syntax = "array"
            elif re.search(r'css\s*=\s*\{\s*`', context):
                syntax = "template"

            css_props.append(EmotionCssPropInfo(
                file=file_path,
                line_number=line_num,
                element=element,
                syntax=syntax,
                has_theme_usage=bool(self.RE_THEME_ACCESS.search(context)),
                has_conditional=bool(self.RE_TERNARY.search(context)),
                css_properties_count=len(re.findall(r'[\w-]+\s*:\s*[^;{}\n]+[;\n,]', context)),
            ))

        # ── css`` tagged template ──────────────────────────────
        for match in self.RE_CSS_TEMPLATE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1) or ""

            body = self._extract_template_body(content, match.end() - 1)

            css_functions.append(EmotionCssFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                syntax="tagged-template",
                has_interpolation=bool(self.RE_DYNAMIC.search(body)) if body else False,
                has_nesting=bool(self.RE_NESTING.search(body)) if body else False,
                css_properties_count=self._count_css_properties(body) if body else 0,
            ))

        # ── css() function call ─────────────────────────────────
        # Only count css() with object argument, not css`` template
        css_fn_matches = re.finditer(
            r"(?:(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*)?css\s*\(\s*\{",
            content, re.MULTILINE
        )
        for match in css_fn_matches:
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1) or ""

            css_functions.append(EmotionCssFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                syntax="function-call",
            ))

        # ── ClassNames ──────────────────────────────────────────
        for match in self.RE_CLASSNAMES.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            classnames.append(EmotionClassNamesInfo(
                file=file_path,
                line_number=line_num,
                has_css_call=bool(re.search(r'\bcss\s*\(', context)),
                has_cx_call=bool(re.search(r'\bcx\s*\(', context)),
                has_theme=bool(self.RE_THEME_ACCESS.search(context)),
            ))

        # ── Media queries ───────────────────────────────────────
        for match in self.RE_MEDIA_QUERY.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            prop = match.group(1)
            value = match.group(2).strip()

            approach = "inline"
            if self.RE_FACEPAINT.search(content):
                approach = "facepaint"

            media_queries.append(EmotionMediaQueryInfo(
                file=file_path,
                line_number=line_num,
                breakpoint=value,
                approach=approach,
                is_mobile_first=prop == "min-width",
                has_orientation=prop == "orientation",
            ))

        # ── Dynamic props ───────────────────────────────────────
        for match in self.RE_DYNAMIC.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 200]

            dynamic_props.append(EmotionDynamicPropInfo(
                file=file_path,
                line_number=line_num,
                pattern="theme-function" if self.RE_THEME_ACCESS.search(context) else "interpolation",
                has_ternary=bool(self.RE_TERNARY.search(context)),
                has_theme_access=bool(self.RE_THEME_ACCESS.search(context)),
            ))

        # ── Build style patterns summary ────────────────────────
        # Analyze the entire file for overall CSS pattern usage
        categories = []
        for cat, pattern in self.CSS_CATEGORIES.items():
            if pattern.search(content):
                categories.append(cat)

        if categories:
            style_patterns.append(EmotionStylePatternInfo(
                file=file_path,
                line_number=1,
                categories=categories,
                css_properties_count=len(re.findall(r'[\w-]+\s*:\s*[^;{}\n]+[;\n]', content)),
                has_nesting=bool(self.RE_NESTING.search(content)),
                nesting_depth=self._max_nesting_depth(content),
                has_pseudo_selectors=bool(self.RE_PSEUDO.search(content)),
                has_css_variables=bool(self.RE_CSS_VAR.search(content)),
                has_flexbox=bool(self.RE_FLEXBOX.search(content)),
                has_grid=bool(self.RE_GRID.search(content)),
            ))

        return {
            'css_props': css_props,
            'css_functions': css_functions,
            'classnames': classnames,
            'style_patterns': style_patterns,
            'dynamic_props': dynamic_props,
            'media_queries': media_queries,
        }

    def _extract_template_body(self, content: str, backtick_pos: int) -> str:
        """Extract content between backticks for a tagged template literal."""
        if backtick_pos >= len(content) or content[backtick_pos] != '`':
            return ""
        depth = 0
        i = backtick_pos + 1
        while i < len(content):
            ch = content[i]
            if ch == '`' and depth == 0:
                return content[backtick_pos + 1:i]
            elif ch == '$' and i + 1 < len(content) and content[i + 1] == '{':
                depth += 1
                i += 1
            elif ch == '}' and depth > 0:
                depth -= 1
            elif ch == '\\':
                i += 1
            i += 1
        return ""

    def _count_css_properties(self, body: str) -> int:
        """Count CSS property declarations."""
        if not body:
            return 0
        return len(re.findall(r'[\w-]+\s*:\s*[^;{}\n]+[;\n]', body))

    def _max_nesting_depth(self, content: str) -> int:
        """Estimate maximum nesting depth from & usage."""
        depth = 0
        max_depth = 0
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('&') or stripped.startswith('.') or stripped.startswith(':'):
                depth += 1
                max_depth = max(max_depth, depth)
            elif stripped == '}':
                depth = max(0, depth - 1)
        return min(max_depth, 10)
