"""
Styled Components Mixin Extractor for CodeTrellis

Extracts CSS helper/mixin patterns from styled-components usage:
- css`` tagged template helper for reusable style fragments
- keyframes`` for animation definitions
- Shared mixin functions returning css``
- Polished helper usage (lighten, darken, transparentize, etc.)
- Interpolation functions for conditional/dynamic styles
- Tagged template composition patterns

Part of CodeTrellis v4.42 - Styled Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StyledCssHelperInfo:
    """Information about a css`` helper usage."""
    name: str
    file: str = ""
    line_number: int = 0
    property_count: int = 0
    has_dynamic_props: bool = False
    has_theme_usage: bool = False
    has_media_query: bool = False
    is_conditional: bool = False     # Used in ternary/conditional
    used_in_components: List[str] = field(default_factory=list)


@dataclass
class StyledKeyframesInfo:
    """Information about a keyframes`` definition."""
    name: str
    file: str = ""
    line_number: int = 0
    steps: List[str] = field(default_factory=list)   # from, to, 0%, 50%, 100%
    properties_animated: List[str] = field(default_factory=list)
    has_dynamic_values: bool = False


@dataclass
class StyledMixinInfo:
    """Information about a mixin/helper function returning CSS."""
    name: str
    file: str = ""
    line_number: int = 0
    parameters: List[str] = field(default_factory=list)
    returns_css: bool = False
    has_theme_usage: bool = False
    is_arrow_function: bool = False
    mixin_type: str = ""   # css-helper, interpolation, polished, utility


class StyledMixinExtractor:
    """
    Extracts CSS helpers, keyframes, and mixin patterns.

    Detects:
    - css`` tagged template helper definitions
    - keyframes`` animation definitions
    - Mixin functions that return css`` fragments
    - Polished utility usage (lighten, darken, etc.)
    - Conditional style interpolation patterns
    """

    # css`` helper definition
    RE_CSS_HELPER = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*css\s*`",
        re.MULTILINE
    )

    # keyframes`` definition
    RE_KEYFRAMES = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*keyframes\s*`",
        re.MULTILINE
    )

    # Function returning css``
    RE_CSS_FUNCTION = re.compile(
        r"(?:export\s+)?(?:const|let|var|function)\s+(\w+)\s*"
        r"(?:=\s*\(([^)]*)\)\s*=>|=\s*function\s*\(([^)]*)\)\s*\{|\(([^)]*)\)\s*\{)"
        r"[\s\S]*?css\s*`",
        re.MULTILINE
    )

    # Arrow function mixin returning css``
    RE_ARROW_MIXIN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*css\s*`",
        re.MULTILINE
    )

    # Polished helpers
    POLISHED_HELPERS = {
        'lighten', 'darken', 'transparentize', 'opacify', 'rgba', 'rgb',
        'hsl', 'hsla', 'adjustHue', 'complement', 'desaturate', 'saturate',
        'shade', 'tint', 'mix', 'invert', 'grayscale', 'parseToRgb',
        'parseToHsl', 'rem', 'em', 'modularScale', 'stripUnit',
        'clearFix', 'ellipsis', 'hideText', 'hideVisually', 'normalize',
        'placeholder', 'selection', 'triangle', 'wordWrap', 'position',
        'size', 'margin', 'padding', 'borderColor', 'borderWidth',
        'borderStyle', 'borderRadius', 'animation', 'transitions',
        'between', 'cover', 'fluidRange', 'timingFunctions',
    }

    # Polished import detection
    RE_POLISHED = re.compile(
        r"from\s+['\"]polished['/\"]|require\(['\"]polished['\"]\)",
        re.MULTILINE
    )

    # Keyframe steps
    RE_KEYFRAME_STEPS = re.compile(
        r"(from|to|\d+%)\s*\{",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract CSS helpers, keyframes, and mixins from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'css_helpers', 'keyframes', 'mixins' lists
        """
        css_helpers: List[StyledCssHelperInfo] = []
        keyframes_list: List[StyledKeyframesInfo] = []
        mixins: List[StyledMixinInfo] = []

        if not content or not content.strip():
            return {
                'css_helpers': css_helpers,
                'keyframes': keyframes_list,
                'mixins': mixins,
            }

        has_polished = bool(self.RE_POLISHED.search(content))

        # ── css`` helpers ─────────────────────────────────────────
        for m in self.RE_CSS_HELPER.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Get template literal block
            block_start = m.end()
            block_end = content.find('`', block_start)
            block = content[block_start:block_end] if block_end != -1 else ""

            prop_count = sum(1 for line in block.split('\n')
                           if line.strip() and ':' in line.strip()
                           and not line.strip().startswith('//'))

            has_dynamic = bool(re.search(r'\$\{', block))
            has_theme = bool(re.search(r'theme\.|useTheme', block))
            has_media = bool(re.search(r'@media', block))

            # Find which components use this helper
            used_in = []
            for usage in re.finditer(rf'\$\{{\s*{re.escape(name)}\s*\}}', content):
                # Look backwards for the component name
                before = content[:usage.start()]
                comp_match = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*styled', before)
                if comp_match:
                    used_in.append(comp_match[-1])

            # Check if used conditionally
            is_conditional = bool(re.search(
                rf'{re.escape(name)}\s*\?|'
                rf'\?\s*{re.escape(name)}|'
                rf'&&\s*{re.escape(name)}|'
                rf'{re.escape(name)}\s*&&',
                content
            ))

            css_helpers.append(StyledCssHelperInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                property_count=prop_count,
                has_dynamic_props=has_dynamic,
                has_theme_usage=has_theme,
                has_media_query=has_media,
                is_conditional=is_conditional,
                used_in_components=used_in[:10],
            ))

        # ── keyframes`` ──────────────────────────────────────────
        for m in self.RE_KEYFRAMES.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            block_start = m.end()
            block_end = content.find('`', block_start)
            block = content[block_start:block_end] if block_end != -1 else ""

            # Extract keyframe steps
            steps = [s.group(1) for s in self.RE_KEYFRAME_STEPS.finditer(block)]

            # Extract animated properties
            props_animated = set()
            for line in block.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('//'):
                    prop = line.split(':')[0].strip()
                    if prop and prop not in ('from', 'to') and not prop.endswith('%'):
                        props_animated.add(prop)

            has_dynamic = bool(re.search(r'\$\{', block))

            keyframes_list.append(StyledKeyframesInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                steps=steps[:10],
                properties_animated=sorted(props_animated)[:15],
                has_dynamic_values=has_dynamic,
            ))

        # ── Arrow function mixins returning css`` ─────────────────
        for m in self.RE_ARROW_MIXIN.finditer(content):
            name = m.group(1)
            params_str = m.group(2) or ""
            line_num = content[:m.start()].count('\n') + 1

            # Skip if already captured as css helper
            if any(h.name == name for h in css_helpers):
                continue

            params = [p.strip().split(':')[0].strip()
                     for p in params_str.split(',') if p.strip()]

            block_start = m.end()
            block_end = content.find('`', block_start)
            block = content[block_start:block_end] if block_end != -1 else ""
            has_theme = bool(re.search(r'theme\.|useTheme', block))

            mixins.append(StyledMixinInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                parameters=params[:10],
                returns_css=True,
                has_theme_usage=has_theme,
                is_arrow_function=True,
                mixin_type="css-helper",
            ))

        # ── Polished helpers ──────────────────────────────────────
        if has_polished:
            for helper in self.POLISHED_HELPERS:
                if re.search(rf'\b{helper}\s*\(', content):
                    line_num = 0
                    for i, line in enumerate(content.split('\n'), 1):
                        if helper in line:
                            line_num = i
                            break

                    mixins.append(StyledMixinInfo(
                        name=helper,
                        file=file_path,
                        line_number=line_num,
                        parameters=[],
                        returns_css=False,
                        has_theme_usage=False,
                        is_arrow_function=False,
                        mixin_type="polished",
                    ))

        return {
            'css_helpers': css_helpers,
            'keyframes': keyframes_list,
            'mixins': mixins,
        }
