"""
Styled Components Style Extractor for CodeTrellis

Extracts CSS style patterns from styled-components template literals:
- CSS property detection (layout, typography, color, spacing, etc.)
- Media query patterns (mobile-first, desktop-first, breakpoints)
- Pseudo-selector usage (:hover, :focus, :active, ::before, ::after)
- CSS nesting with & parent selector
- Dynamic prop-based conditional styles
- Responsive design patterns
- CSS custom properties (variables) usage
- CSS Grid and Flexbox patterns

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyledStylePatternInfo:
    """Information about CSS patterns in styled-components."""
    file: str = ""
    line_number: int = 0
    component_name: str = ""
    has_flexbox: bool = False
    has_grid: bool = False
    has_animations: bool = False
    has_transitions: bool = False
    has_transforms: bool = False
    has_pseudo_selectors: bool = False
    pseudo_selectors: List[str] = field(default_factory=list)
    has_nesting: bool = False
    nesting_depth: int = 0
    has_css_variables: bool = False
    css_variables: List[str] = field(default_factory=list)
    property_categories: List[str] = field(default_factory=list)


@dataclass
class StyledDynamicPropInfo:
    """Information about dynamic prop-based styling."""
    file: str = ""
    line_number: int = 0
    component_name: str = ""
    prop_name: str = ""
    style_property: str = ""
    pattern: str = ""    # ternary, logical-and, switch, map, function
    is_transient: bool = False   # $-prefixed


@dataclass
class StyledMediaQueryInfo:
    """Information about media query usage."""
    file: str = ""
    line_number: int = 0
    component_name: str = ""
    query_type: str = ""          # min-width, max-width, prefers-color-scheme, etc.
    breakpoint_value: str = ""    # 768px, 1024px, etc.
    is_mobile_first: bool = False
    property_count: int = 0


class StyledStyleExtractor:
    """
    Extracts CSS style patterns from styled-components.

    Detects:
    - Layout patterns (Flexbox, Grid)
    - Media queries and responsive design
    - Pseudo-selectors and pseudo-elements
    - CSS nesting depth
    - Dynamic prop-based styles
    - CSS custom properties
    - Animation and transition patterns
    """

    # CSS property categories
    PROPERTY_CATEGORIES = {
        'layout': {'display', 'position', 'float', 'clear', 'overflow',
                   'z-index', 'top', 'right', 'bottom', 'left', 'visibility'},
        'flexbox': {'flex', 'flex-direction', 'flex-wrap', 'flex-flow',
                    'justify-content', 'align-items', 'align-content',
                    'align-self', 'flex-grow', 'flex-shrink', 'flex-basis',
                    'gap', 'row-gap', 'column-gap', 'order'},
        'grid': {'grid', 'grid-template-columns', 'grid-template-rows',
                 'grid-template-areas', 'grid-area', 'grid-column',
                 'grid-row', 'grid-gap', 'grid-auto-flow', 'grid-auto-columns',
                 'grid-auto-rows', 'place-items', 'place-content', 'place-self'},
        'spacing': {'margin', 'margin-top', 'margin-right', 'margin-bottom',
                    'margin-left', 'padding', 'padding-top', 'padding-right',
                    'padding-bottom', 'padding-left'},
        'sizing': {'width', 'height', 'max-width', 'max-height',
                   'min-width', 'min-height', 'aspect-ratio'},
        'typography': {'font', 'font-family', 'font-size', 'font-weight',
                       'font-style', 'line-height', 'letter-spacing',
                       'text-align', 'text-decoration', 'text-transform',
                       'word-spacing', 'white-space', 'word-break',
                       'overflow-wrap', 'text-overflow'},
        'color': {'color', 'background', 'background-color', 'opacity',
                  'background-image', 'background-size', 'background-position'},
        'border': {'border', 'border-width', 'border-style', 'border-color',
                   'border-radius', 'border-top', 'border-right',
                   'border-bottom', 'border-left', 'outline', 'box-shadow'},
        'animation': {'animation', 'animation-name', 'animation-duration',
                      'animation-timing-function', 'animation-delay',
                      'animation-iteration-count', 'animation-direction',
                      'animation-fill-mode', 'animation-play-state'},
        'transition': {'transition', 'transition-property', 'transition-duration',
                       'transition-timing-function', 'transition-delay'},
        'transform': {'transform', 'transform-origin', 'perspective',
                      'backface-visibility'},
    }

    # Pseudo-selectors
    PSEUDO_SELECTORS = {
        ':hover', ':focus', ':active', ':visited', ':disabled', ':enabled',
        ':checked', ':first-child', ':last-child', ':nth-child', ':not',
        ':focus-visible', ':focus-within', ':placeholder', ':placeholder-shown',
        '::before', '::after', '::placeholder', '::selection',
        '::first-line', '::first-letter',
    }

    # Media query patterns
    RE_MEDIA_QUERY = re.compile(
        r"@media\s*\(([^)]+)\)\s*\{",
        re.MULTILINE
    )

    # Dynamic prop pattern: ${props => ...} or ${({ prop }) => ...}
    RE_DYNAMIC_STYLE = re.compile(
        r"\$\{\s*(?:\(\s*\{?\s*(\w+)\s*\}?\s*\)|(\w+))\s*=>",
        re.MULTILINE
    )

    # CSS variable usage
    RE_CSS_VAR = re.compile(
        r"var\(\s*--([\w-]+)\s*\)|"
        r"--([\w-]+)\s*:",
        re.MULTILINE
    )

    # Nesting with &
    RE_NESTING = re.compile(
        r"&\s*[\.\[:\w>~+]|&\s*\{|&\s*,",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract CSS style patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'style_patterns', 'dynamic_props', 'media_queries' lists
        """
        style_patterns: List[StyledStylePatternInfo] = []
        dynamic_props: List[StyledDynamicPropInfo] = []
        media_queries: List[StyledMediaQueryInfo] = []

        if not content or not content.strip():
            return {
                'style_patterns': style_patterns,
                'dynamic_props': dynamic_props,
                'media_queries': media_queries,
            }

        # Find all styled-component template literal blocks
        styled_blocks = self._find_styled_blocks(content)

        for comp_name, block, line_num in styled_blocks:
            # ── Style pattern analysis ────────────────────────────
            categories = set()
            for cat, props in self.PROPERTY_CATEGORIES.items():
                for prop in props:
                    # Check camelCase and kebab-case
                    camel = prop.replace('-', '')
                    if re.search(rf'\b{re.escape(prop)}\s*:', block) or \
                       re.search(rf'\b{camel}\s*:', block):
                        categories.add(cat)
                        break

            # Pseudo selectors
            pseudo_found = []
            for ps in self.PSEUDO_SELECTORS:
                if ps in block:
                    pseudo_found.append(ps)

            # CSS variables
            css_vars = []
            for vm in self.RE_CSS_VAR.finditer(block):
                var_name = vm.group(1) or vm.group(2)
                if var_name:
                    css_vars.append(f"--{var_name}")

            # Nesting depth
            nesting = 0
            depth = 0
            for ch in block:
                if ch == '{':
                    depth += 1
                    nesting = max(nesting, depth)
                elif ch == '}':
                    depth -= 1

            pattern = StyledStylePatternInfo(
                file=file_path,
                line_number=line_num,
                component_name=comp_name,
                has_flexbox='flexbox' in categories,
                has_grid='grid' in categories,
                has_animations='animation' in categories,
                has_transitions='transition' in categories,
                has_transforms='transform' in categories,
                has_pseudo_selectors=len(pseudo_found) > 0,
                pseudo_selectors=pseudo_found[:10],
                has_nesting=bool(self.RE_NESTING.search(block)),
                nesting_depth=nesting,
                has_css_variables=len(css_vars) > 0,
                css_variables=css_vars[:10],
                property_categories=sorted(categories),
            )
            style_patterns.append(pattern)

            # ── Dynamic prop patterns ─────────────────────────────
            for dm in self.RE_DYNAMIC_STYLE.finditer(block):
                prop_name = dm.group(1) or dm.group(2) or ""
                dp_line = line_num + block[:dm.start()].count('\n')

                # Determine the pattern type
                after = block[dm.end():dm.end() + 100]
                if '?' in after and ':' in after:
                    dp_pattern = "ternary"
                elif '&&' in after:
                    dp_pattern = "logical-and"
                elif 'switch' in after:
                    dp_pattern = "switch"
                else:
                    dp_pattern = "function"

                # Try to find the CSS property being set
                before = block[:dm.start()]
                lines = before.split('\n')
                style_prop = ""
                if lines:
                    last_line = lines[-1].strip()
                    if ':' in last_line:
                        style_prop = last_line.split(':')[0].strip()

                is_transient = prop_name.startswith('$') if prop_name else False

                dynamic_props.append(StyledDynamicPropInfo(
                    file=file_path,
                    line_number=dp_line,
                    component_name=comp_name,
                    prop_name=prop_name,
                    style_property=style_prop,
                    pattern=dp_pattern,
                    is_transient=is_transient,
                ))

            # ── Media queries ─────────────────────────────────────
            for mq in self.RE_MEDIA_QUERY.finditer(block):
                query = mq.group(1).strip()
                mq_line = line_num + block[:mq.start()].count('\n')

                # Determine query type
                query_type = "custom"
                breakpoint_value = ""
                is_mobile_first = False

                if 'min-width' in query:
                    query_type = "min-width"
                    is_mobile_first = True
                    bv = re.search(r'min-width:\s*([\d.]+(?:px|em|rem))', query)
                    if bv:
                        breakpoint_value = bv.group(1)
                elif 'max-width' in query:
                    query_type = "max-width"
                    bv = re.search(r'max-width:\s*([\d.]+(?:px|em|rem))', query)
                    if bv:
                        breakpoint_value = bv.group(1)
                elif 'prefers-color-scheme' in query:
                    query_type = "prefers-color-scheme"
                elif 'prefers-reduced-motion' in query:
                    query_type = "prefers-reduced-motion"

                # Count properties in the media query block
                mq_block_start = mq.end()
                depth = 1
                pos = mq_block_start
                while pos < len(block) and depth > 0:
                    if block[pos] == '{':
                        depth += 1
                    elif block[pos] == '}':
                        depth -= 1
                    pos += 1
                mq_block = block[mq_block_start:pos - 1] if pos > mq_block_start else ""
                mq_prop_count = sum(1 for line in mq_block.split('\n')
                                   if line.strip() and ':' in line.strip()
                                   and not line.strip().startswith('//'))

                media_queries.append(StyledMediaQueryInfo(
                    file=file_path,
                    line_number=mq_line,
                    component_name=comp_name,
                    query_type=query_type,
                    breakpoint_value=breakpoint_value,
                    is_mobile_first=is_mobile_first,
                    property_count=mq_prop_count,
                ))

        return {
            'style_patterns': style_patterns,
            'dynamic_props': dynamic_props,
            'media_queries': media_queries,
        }

    def _find_styled_blocks(self, content: str):
        """Find all styled-component template literal blocks with component names."""
        blocks = []

        # Pattern: const Xxx = styled.yyy`...` or const Xxx = styled(Yyy)`...`
        pattern = re.compile(
            r"(?:const|let|var)\s+(\w+)\s*=\s*styled"
            r"(?:\.\s*\w+|\(\s*\w+\s*\))"
            r"(?:\.attrs\s*\([^)]*\))?"
            r"(?:\.withConfig\s*\([^)]*\))?"
            r"\s*`",
            re.MULTILINE
        )

        for m in pattern.finditer(content):
            comp_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Find the closing backtick (handling nested ${})
            start = m.end()
            depth = 0
            pos = start
            while pos < len(content):
                ch = content[pos]
                if ch == '`' and depth == 0:
                    break
                elif ch == '$' and pos + 1 < len(content) and content[pos + 1] == '{':
                    depth += 1
                    pos += 1
                elif ch == '}' and depth > 0:
                    depth -= 1
                pos += 1

            block = content[start:pos]
            blocks.append((comp_name, block, line_num))

        return blocks
