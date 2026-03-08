"""
MUI Style Extractor for CodeTrellis

Extracts Material UI styling patterns from React/TypeScript source code.
Covers MUI v4.x through v6.x styling approaches:
- sx prop usage (v5+, system props)
- styled() API (v5+ Emotion-based, v4 @material-ui/styles)
- makeStyles() (v4 legacy, tss-react migration)
- withStyles() (v4 legacy HOC approach)
- CSS theme variables (v5 experimental, v6 default)
- Pigment CSS (v6 zero-runtime styling)
- Theme-aware responsive styling
- Global style overrides
- CSS-in-JS patterns (Emotion, styled-components integration)

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MuiSxUsageInfo:
    """Information about sx prop usage."""
    component_name: str = ""
    file: str = ""
    line_number: int = 0
    has_theme_callback: bool = False   # sx={(theme) => ...}
    has_responsive: bool = False       # sx={{ xs: ..., md: ... }}
    has_conditional: bool = False      # sx={[condition && {...}]}
    has_nested_selectors: bool = False  # sx={{ '& .child': {...} }}
    system_props_used: List[str] = field(default_factory=list)  # m, p, display, etc.


@dataclass
class MuiStyledComponentInfo:
    """Information about styled() API usage."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    base_component: str = ""       # Component or HTML element being styled
    has_theme_usage: bool = False
    has_props_usage: bool = False   # styled(Comp, { shouldForwardProp })
    has_responsive: bool = False
    has_overrides_name: bool = False  # { name: 'MuiCustom', slot: 'Root' }
    override_name: str = ""
    override_slot: str = ""
    css_properties_count: int = 0
    is_pigment_css: bool = False    # v6 Pigment CSS


@dataclass
class MuiMakeStylesInfo:
    """Information about makeStyles() usage (v4 legacy / tss-react)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    method: str = ""             # makeStyles, withStyles, tss-react
    class_names: List[str] = field(default_factory=list)
    has_theme_usage: bool = False
    has_props_usage: bool = False
    is_legacy: bool = True        # v4 legacy pattern


class MuiStyleExtractor:
    """
    Extracts MUI styling patterns from source code.

    Detects:
    - sx prop usage on MUI components
    - styled() API (v5+ and Emotion)
    - makeStyles() / withStyles() (v4 legacy)
    - tss-react makeStyles (v5 migration helper)
    - Theme callbacks in styles
    - Responsive styling patterns
    - CSS theme variables
    - Pigment CSS patterns (v6)
    - Global styles (GlobalStyles component)
    """

    # sx prop pattern (comprehensive)
    SX_PATTERN = re.compile(
        r"<(\w+)\s+[^>]*\bsx\s*=\s*\{",
        re.MULTILINE
    )

    # sx with theme callback: sx={(theme) => ...}
    SX_THEME_CALLBACK = re.compile(
        r"\bsx\s*=\s*\{\s*\(\s*theme\s*\)\s*=>",
        re.MULTILINE
    )

    # sx with responsive object: sx={{ xs: ..., md: ... }}
    SX_RESPONSIVE = re.compile(
        r"\bsx\s*=\s*\{\s*\{[^}]*\b(?:xs|sm|md|lg|xl)\s*:",
        re.MULTILINE
    )

    # sx with nested selectors: sx={{ '& .child': {...} }}
    SX_NESTED = re.compile(
        r"\bsx\s*=\s*\{[^}]*['\"]&",
        re.MULTILINE
    )

    # styled() API pattern
    STYLED_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*styled\(\s*"
        r"(?:['\"](\w+)['\"]|(\w+))\s*"
        r"(?:,\s*\{([^}]*)\})?"
        r"\s*\)",
        re.MULTILINE
    )

    # makeStyles() pattern (v4 legacy)
    MAKE_STYLES_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*makeStyles\s*\(",
        re.MULTILINE
    )

    # withStyles() pattern (v4 legacy HOC)
    WITH_STYLES_PATTERN = re.compile(
        r"withStyles\s*\(\s*(?:\([^)]*\)\s*=>|{)",
        re.MULTILINE
    )

    # tss-react makeStyles (v5 migration)
    TSS_MAKE_STYLES = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:tss\.)?makeStyles\s*\(",
        re.MULTILINE
    )

    # Pigment CSS patterns (v6)
    PIGMENT_CSS = re.compile(
        r"from\s+['\"]@pigment-css/|pigment-css-vite-plugin|pigmentCss",
        re.MULTILINE
    )

    # System prop patterns (shorthand props used on Box, Stack, etc.)
    SYSTEM_PROP_NAMES = {
        'm', 'mt', 'mr', 'mb', 'ml', 'mx', 'my', 'margin',
        'p', 'pt', 'pr', 'pb', 'pl', 'px', 'py', 'padding',
        'display', 'overflow', 'textOverflow', 'visibility', 'whiteSpace',
        'flexDirection', 'flexWrap', 'justifyContent', 'alignItems', 'alignContent',
        'order', 'flex', 'flexGrow', 'flexShrink', 'alignSelf',
        'gap', 'columnGap', 'rowGap',
        'gridColumn', 'gridRow', 'gridAutoFlow', 'gridAutoColumns', 'gridAutoRows',
        'gridTemplateColumns', 'gridTemplateRows', 'gridTemplateAreas',
        'bgcolor', 'color', 'border', 'borderTop', 'borderRight', 'borderBottom',
        'borderLeft', 'borderColor', 'borderRadius',
        'width', 'maxWidth', 'minWidth', 'height', 'maxHeight', 'minHeight',
        'boxSizing', 'position', 'zIndex', 'top', 'right', 'bottom', 'left',
        'boxShadow', 'fontFamily', 'fontSize', 'fontStyle', 'fontWeight',
        'letterSpacing', 'lineHeight', 'textAlign', 'textTransform',
    }

    def __init__(self):
        """Initialize the MUI style extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all MUI styling patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'sx_usages', 'styled_components', 'make_styles' lists
        """
        sx_usages: List[MuiSxUsageInfo] = []
        styled_components: List[MuiStyledComponentInfo] = []
        make_styles: List[MuiMakeStylesInfo] = []

        # ── sx prop usages ───────────────────────────────────────
        for match in self.SX_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Check features in surrounding context
            context = content[match.start():match.start() + 500]

            sx_info = MuiSxUsageInfo(
                component_name=comp_name,
                file=file_path,
                line_number=line_number,
                has_theme_callback=bool(re.search(r'\(\s*theme\s*\)\s*=>', context)),
                has_responsive=bool(re.search(r'\b(?:xs|sm|md|lg|xl)\s*:', context)),
                has_conditional=bool(re.search(r'sx\s*=\s*\{\s*\[', context)),
                has_nested_selectors=bool(re.search(r"['\"]&", context)),
            )

            # Detect system props used
            props_in_sx = re.findall(r'(\w+)\s*:', context)
            sx_info.system_props_used = [
                p for p in props_in_sx
                if p in self.SYSTEM_PROP_NAMES
            ][:20]

            sx_usages.append(sx_info)

        # ── styled() components ──────────────────────────────────
        for match in self.STYLED_PATTERN.finditer(content):
            comp_name = match.group(1)
            base_str = match.group(2) or match.group(3) or ""
            options_str = match.group(4) or ""
            line_number = content[:match.start()].count('\n') + 1

            # Look ahead for the style function body
            rest = content[match.end():]
            theme_used = bool(re.search(r'\(\s*\{\s*theme|theme\s*[.)=>]|theme\.', rest[:800]))
            props_used = bool(re.search(r'\(\s*\{\s*(?:theme\s*,\s*)?\w+|ownerState|props', rest[:800]))
            responsive = bool(re.search(r'theme\.breakpoints|\[theme\.breakpoints|@media', rest[:800]))

            # Extract name/slot from options
            override_name = ""
            override_slot = ""
            if options_str:
                name_match = re.search(r"name\s*:\s*['\"](\w+)['\"]", options_str)
                if name_match:
                    override_name = name_match.group(1)
                slot_match = re.search(r"slot\s*:\s*['\"](\w+)['\"]", options_str)
                if slot_match:
                    override_slot = slot_match.group(1)

            styled_components.append(MuiStyledComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_number,
                base_component=base_str,
                has_theme_usage=theme_used,
                has_props_usage=props_used,
                has_responsive=responsive,
                has_overrides_name=bool(override_name),
                override_name=override_name,
                override_slot=override_slot,
            ))

        # ── Detect tss-react import to mark tss-react usages ────
        has_tss_import = bool(re.search(r"from\s+['\"]tss-react", content))

        # ── tss-react makeStyles (v5 migration) — process FIRST ──
        tss_lines: set = set()
        if has_tss_import:
            for match in self.TSS_MAKE_STYLES.finditer(content):
                var_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                tss_lines.add(line_number)

                make_styles.append(MuiMakeStylesInfo(
                    name=var_name,
                    file=file_path,
                    line_number=line_number,
                    method='tss-react',
                    is_legacy=False,
                ))

        # ── makeStyles() (v4 legacy) ────────────────────────────
        for match in self.MAKE_STYLES_PATTERN.finditer(content):
            var_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Skip if already captured by tss-react
            if line_number in tss_lines:
                continue

            # Extract class names from the makeStyles body
            body = self._extract_paren_body(content, match.end() - 1)
            class_names = re.findall(r'(\w+)\s*:\s*\{', body) if body else []
            theme_used = 'theme' in body if body else False

            make_styles.append(MuiMakeStylesInfo(
                name=var_name,
                file=file_path,
                line_number=line_number,
                method='makeStyles',
                class_names=class_names[:30],
                has_theme_usage=theme_used,
                is_legacy=True,
            ))

        # ── withStyles() (v4 legacy HOC) ─────────────────────────
        for match in self.WITH_STYLES_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            make_styles.append(MuiMakeStylesInfo(
                name='withStyles',
                file=file_path,
                line_number=line_number,
                method='withStyles',
                is_legacy=True,
            ))

        return {
            'sx_usages': sx_usages,
            'styled_components': styled_components,
            'make_styles': make_styles,
        }

    def _extract_paren_body(self, content: str, start: int, max_chars: int = 3000) -> str:
        """Extract a parenthesis-balanced body."""
        if start >= len(content) or content[start] != '(':
            return ""
        depth = 0
        result = []
        for ch in content[start:start + max_chars]:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
            result.append(ch)
        return ''.join(result)
