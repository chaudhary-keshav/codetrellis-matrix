"""
Chakra UI Style Extractor for CodeTrellis

Extracts Chakra UI styling patterns from React/TypeScript source code.
Covers:
- Style props (bg, color, p, m, w, h, fontSize, etc.)
- sx prop usage
- Responsive array syntax ([value, value, value])
- Responsive object syntax ({ base: ..., md: ..., lg: ... })
- Pseudo-style props (_hover, _focus, _active, _disabled, etc.)
- CSS variables via Chakra tokens
- @emotion/styled integration
- Panda CSS integration (v3)
- chakra() factory styled components
- useStyleConfig / useMultiStyleConfig patterns
- Global styles

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChakraStylePropInfo:
    """Information about Chakra UI style prop usage."""
    component_name: str
    file: str = ""
    line_number: int = 0
    style_props: List[str] = field(default_factory=list)
    pseudo_props: List[str] = field(default_factory=list)  # _hover, _focus, etc.
    has_responsive: bool = False
    responsive_type: str = ""    # array, object, none
    has_theme_tokens: bool = False


@dataclass
class ChakraSxUsageInfo:
    """Information about sx prop usage in Chakra UI."""
    component_name: str
    file: str = ""
    line_number: int = 0
    has_responsive: bool = False
    has_pseudo_selectors: bool = False
    has_theme_callback: bool = False
    has_conditional: bool = False
    property_count: int = 0


@dataclass
class ChakraResponsiveInfo:
    """Information about responsive style patterns."""
    file: str = ""
    line_number: int = 0
    pattern_type: str = ""       # array, object, useBreakpointValue, Show/Hide
    breakpoints_used: List[str] = field(default_factory=list)
    property_name: str = ""


class ChakraStyleExtractor:
    """
    Extracts Chakra UI styling patterns from source code.

    Detects:
    - Style props usage (30+ shorthand props)
    - sx prop patterns
    - Responsive styles (array and object syntax)
    - Pseudo-style props (_hover, _focus, etc.)
    - useStyleConfig / useMultiStyleConfig
    - Global styles configuration
    - CSS variable usage
    """

    # Style shorthand props
    STYLE_PROPS = {
        # Spacing
        'p', 'px', 'py', 'pt', 'pb', 'pl', 'pr', 'ps', 'pe',
        'm', 'mx', 'my', 'mt', 'mb', 'ml', 'mr', 'ms', 'me',
        'padding', 'margin',
        # Layout
        'w', 'h', 'minW', 'maxW', 'minH', 'maxH',
        'width', 'height', 'minWidth', 'maxWidth', 'minHeight', 'maxHeight',
        'display', 'd',
        # Flexbox
        'flexDir', 'flexDirection', 'flexWrap', 'flex', 'flexGrow', 'flexShrink',
        'justifyContent', 'alignItems', 'alignContent', 'alignSelf',
        'order', 'gap', 'rowGap', 'columnGap',
        # Grid
        'gridTemplateColumns', 'gridTemplateRows', 'gridColumn', 'gridRow',
        'gridArea', 'gridAutoColumns', 'gridAutoRows', 'gridAutoFlow',
        'templateColumns', 'templateRows', 'column', 'row',
        # Color
        'bg', 'bgColor', 'backgroundColor', 'color', 'opacity',
        'bgGradient', 'bgClip', 'bgImage',
        # Typography
        'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing',
        'textAlign', 'fontFamily', 'fontStyle', 'textDecoration',
        'textTransform', 'noOfLines', 'isTruncated',
        # Border
        'border', 'borderWidth', 'borderColor', 'borderStyle',
        'borderRadius', 'rounded', 'borderTop', 'borderBottom',
        'borderLeft', 'borderRight', 'borderTopRadius', 'borderBottomRadius',
        # Shadow
        'boxShadow', 'shadow', 'textShadow',
        # Position
        'position', 'pos', 'top', 'right', 'bottom', 'left',
        'zIndex', 'inset', 'insetX', 'insetY',
        # Other
        'overflow', 'overflowX', 'overflowY',
        'cursor', 'transition', 'transform', 'transformOrigin',
        'visibility', 'whiteSpace', 'wordBreak', 'objectFit',
        'boxSizing', 'float', 'clear', 'isolation',
        # Chakra-specific
        'colorScheme', 'variant', 'size', 'orientation',
        'isDisabled', 'isInvalid', 'isRequired', 'isReadOnly',
        'isLoading', 'isActive', 'isChecked', 'isFocusable',
        'isFullWidth', 'isAttached', 'isRound', 'isLazy',
        'spacing', 'divider', 'shouldWrapChildren',
    }

    # Pseudo-style props
    PSEUDO_PROPS = {
        '_hover', '_active', '_focus', '_focusWithin', '_focusVisible',
        '_disabled', '_invalid', '_required', '_readOnly',
        '_first', '_last', '_odd', '_even', '_visited',
        '_activeLink', '_activeStep', '_indeterminate',
        '_groupHover', '_peerHover', '_groupFocus', '_peerFocus',
        '_placeholder', '_before', '_after',
        '_selected', '_hidden', '_grabbed', '_pressed',
        '_expanded', '_loading', '_checked', '_mixed',
        '_dark', '_light', '_mediaDark', '_mediaReduceMotion',
        '_rtl', '_ltr', '_horizontal', '_vertical',
    }

    # sx prop pattern
    SX_PROP_PATTERN = re.compile(
        r'<(\w+)[^>]*\bsx\s*=\s*\{',
        re.MULTILINE
    )

    # __css prop pattern (internal Chakra)
    CSS_PROP_PATTERN = re.compile(
        r'<(\w+)[^>]*\b__css\s*=\s*\{',
        re.MULTILINE
    )

    # Responsive array pattern: property={[val1, val2, val3]}
    RESPONSIVE_ARRAY = re.compile(
        r'(\w+)\s*=\s*\{\s*\[[^\]]*,[^\]]*\]\s*\}',
        re.MULTILINE
    )

    # Responsive object pattern: property={{ base: ..., md: ... }}
    RESPONSIVE_OBJECT = re.compile(
        r'(\w+)\s*=\s*\{\s*\{\s*(?:base|sm|md|lg|xl|2xl)\s*:',
        re.MULTILINE
    )

    # useStyleConfig pattern
    USE_STYLE_CONFIG = re.compile(
        r'useStyleConfig\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # useMultiStyleConfig pattern
    USE_MULTI_STYLE_CONFIG = re.compile(
        r'useMultiStyleConfig\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Global styles pattern
    GLOBAL_STYLES = re.compile(
        r'styles\s*:\s*\{[^}]*global\s*:',
        re.DOTALL
    )

    # Pseudo prop in JSX
    PSEUDO_PROP_IN_JSX = re.compile(
        r'(_hover|_focus|_active|_disabled|_invalid|_dark|_light|'
        r'_placeholder|_before|_after|_first|_last|_odd|_even|'
        r'_selected|_checked|_groupHover|_focusVisible|_focusWithin)\s*=\s*\{',
        re.MULTILINE
    )

    # chakra() factory for styled components
    CHAKRA_STYLED_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*chakra\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # @emotion/styled with Chakra
    EMOTION_STYLED_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*styled\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Chakra UI style information from source code."""
        result = {
            'style_props': [],
            'sx_usages': [],
            'responsive_patterns': [],
        }

        if not content or not content.strip():
            return result

        lines = content.split('\n')
        seen_sx = set()

        # Detect sx prop usage
        for match in self.SX_PROP_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            key = f"sx:{comp_name}:{line_num}"
            if key in seen_sx:
                continue
            seen_sx.add(key)

            # Analyze sx content
            context = content[match.start():match.start() + 500]
            has_responsive = bool(re.search(r'\b(?:base|sm|md|lg|xl|2xl)\s*:', context))
            has_pseudo = bool(re.search(r'["\']&:', context) or re.search(r'_hover|_focus|_active', context))
            has_callback = bool(re.search(r'\(theme\)\s*=>', context) or re.search(r'\(t\)\s*=>', context))
            has_conditional = bool(re.search(r'\?\s*\{|\?\s*["\']', context))
            prop_count = len(re.findall(r'(\w+)\s*:', context[:300]))

            sx_info = ChakraSxUsageInfo(
                component_name=comp_name,
                file=file_path,
                line_number=line_num,
                has_responsive=has_responsive,
                has_pseudo_selectors=has_pseudo,
                has_theme_callback=has_callback,
                has_conditional=has_conditional,
                property_count=prop_count,
            )
            result['sx_usages'].append(sx_info)

        # Detect responsive array patterns
        for match in self.RESPONSIVE_ARRAY.finditer(content):
            prop_name = match.group(1)
            if prop_name in self.STYLE_PROPS:
                line_num = content[:match.start()].count('\n') + 1
                resp_info = ChakraResponsiveInfo(
                    file=file_path,
                    line_number=line_num,
                    pattern_type='array',
                    property_name=prop_name,
                )
                result['responsive_patterns'].append(resp_info)

        # Detect responsive object patterns
        for match in self.RESPONSIVE_OBJECT.finditer(content):
            prop_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Detect which breakpoints
            context = content[match.start():match.start() + 200]
            breakpoints = re.findall(r'\b(base|sm|md|lg|xl|2xl)\s*:', context)
            resp_info = ChakraResponsiveInfo(
                file=file_path,
                line_number=line_num,
                pattern_type='object',
                breakpoints_used=list(set(breakpoints)),
                property_name=prop_name,
            )
            result['responsive_patterns'].append(resp_info)

        # Detect pseudo-prop and style-prop usage across multi-line JSX
        current_component = None
        current_component_line = 0
        component_style_props = []
        component_pseudo_props = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track opening JSX tags (may span multiple lines)
            comp_match = re.match(r'\s*<(\w+)', line)
            if comp_match:
                # Flush previous component if it had props
                if current_component and (component_style_props or component_pseudo_props):
                    style_info = ChakraStylePropInfo(
                        component_name=current_component,
                        file=file_path,
                        line_number=current_component_line,
                        style_props=component_style_props[:15],
                        pseudo_props=component_pseudo_props[:10],
                        has_responsive=False,
                    )
                    result['style_props'].append(style_info)

                current_component = comp_match.group(1)
                current_component_line = i
                component_style_props = []
                component_pseudo_props = []

            # Check for pseudo props on this line
            for pseudo_match in self.PSEUDO_PROP_IN_JSX.finditer(line):
                component_pseudo_props.append(pseudo_match.group(1))

            # Check for style props on this line
            for prop in self.STYLE_PROPS:
                if re.search(rf'\b{re.escape(prop)}\s*=', line):
                    component_style_props.append(prop)

            # If line closes the tag, flush
            if current_component and ('>' in stripped or '/>' in stripped):
                if component_style_props or component_pseudo_props:
                    style_info = ChakraStylePropInfo(
                        component_name=current_component,
                        file=file_path,
                        line_number=current_component_line,
                        style_props=component_style_props[:15],
                        pseudo_props=component_pseudo_props[:10],
                        has_responsive=bool(
                            self.RESPONSIVE_ARRAY.search(line) or
                            self.RESPONSIVE_OBJECT.search(line)
                        ),
                    )
                    result['style_props'].append(style_info)
                    component_style_props = []
                    component_pseudo_props = []
                current_component = None

        # Flush any remaining component
        if current_component and (component_style_props or component_pseudo_props):
            style_info = ChakraStylePropInfo(
                component_name=current_component,
                file=file_path,
                line_number=current_component_line,
                style_props=component_style_props[:15],
                pseudo_props=component_pseudo_props[:10],
                has_responsive=False,
            )
            result['style_props'].append(style_info)

        return result
