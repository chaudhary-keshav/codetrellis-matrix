"""
Emotion Animation Extractor for CodeTrellis

Extracts Emotion keyframes and animation patterns from JS/TS source code.
Covers:
- keyframes`` tagged template from @emotion/react or @emotion/css
- keyframes({}) object syntax
- Animation composition and usage in styled components or css prop
- CSS transition patterns
- Reusable animation definitions

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmotionKeyframesInfo:
    """Information about a keyframes definition."""
    name: str
    file: str = ""
    line_number: int = 0
    syntax: str = ""            # tagged-template, object
    steps: List[str] = field(default_factory=list)  # from/to, 0%/50%/100%, etc.
    properties_animated: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class EmotionAnimationUsageInfo:
    """Information about animation usage in styles."""
    file: str = ""
    line_number: int = 0
    keyframes_name: str = ""
    property: str = ""          # animation, animation-name
    has_duration: bool = False
    has_timing_function: bool = False
    has_iteration: bool = False
    is_composed: bool = False   # Using ${keyframeName} in css


class EmotionAnimationExtractor:
    """
    Extracts Emotion keyframes and animation patterns.

    Detects:
    - keyframes`` tagged template definitions
    - keyframes({}) object syntax definitions
    - Animation usage in styled or css prop
    - Animation composition with ${keyframeName}
    - CSS transition patterns
    """

    # Regex: keyframes`` tagged template
    RE_KEYFRAMES_TEMPLATE = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*keyframes\s*`",
        re.MULTILINE
    )

    # Regex: keyframes({}) object syntax
    RE_KEYFRAMES_OBJECT = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*keyframes\s*\(\s*\{",
        re.MULTILINE
    )

    # Regex: Animation steps (from/to or percentage)
    RE_ANIMATION_STEPS = re.compile(
        r"(?:from|to|\d+%)\s*\{",
        re.MULTILINE
    )

    # Regex: Animated CSS properties
    RE_ANIMATED_PROPERTIES = re.compile(
        r"(transform|opacity|background(?:-color)?|color|width|height|"
        r"top|left|right|bottom|scale|rotate|translateX|translateY|"
        r"margin|padding|border|box-shadow|filter|clip-path)\s*:",
        re.MULTILINE | re.IGNORECASE
    )

    # Regex: Animation usage (animation: or animation-name:)
    RE_ANIMATION_USAGE = re.compile(
        r"animation(?:-name)?\s*:\s*(?:\$\{\s*(\w+)\s*\}|(\w+))",
        re.MULTILINE
    )

    # Regex: ${keyframeName} interpolation in animation
    RE_KEYFRAME_INTERPOLATION = re.compile(
        r"\$\{\s*(\w+)\s*\}",
        re.MULTILINE
    )

    # Regex: CSS transition
    RE_TRANSITION = re.compile(
        r"transition\s*:\s*([^;}\n]+)",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Emotion animation patterns.

        Returns:
            Dict with 'keyframes' and 'animation_usages' lists.
        """
        keyframes: List[EmotionKeyframesInfo] = []
        animation_usages: List[EmotionAnimationUsageInfo] = []

        if not content or not content.strip():
            return {
                'keyframes': keyframes,
                'animation_usages': animation_usages,
            }

        # ── keyframes`` tagged template ─────────────────────────
        for match in self.RE_KEYFRAMES_TEMPLATE.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 10):match.start() + 10]

            body = self._extract_template_body(content, match.end() - 1)
            steps = self._extract_steps(body) if body else []
            props_animated = self._extract_animated_properties(body) if body else []

            keyframes.append(EmotionKeyframesInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                syntax="tagged-template",
                steps=steps,
                properties_animated=props_animated,
                is_exported=is_exported,
            ))

        # ── keyframes({}) object syntax ─────────────────────────
        for match in self.RE_KEYFRAMES_OBJECT.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 10):match.start() + 10]

            keyframes.append(EmotionKeyframesInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                syntax="object",
                is_exported=is_exported,
            ))

        # ── Animation usage ─────────────────────────────────────
        for match in self.RE_ANIMATION_USAGE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            kf_name = match.group(1) or match.group(2) or ""

            context = content[match.start():match.start() + 200]
            has_duration = bool(re.search(r'\d+(?:\.\d+)?(?:ms|s)\b', context))
            has_timing = bool(re.search(r'(?:ease|linear|ease-in|ease-out|ease-in-out|cubic-bezier)', context))
            has_iteration = bool(re.search(r'(?:infinite|\d+)\s*(?:;|$|})', context))

            animation_usages.append(EmotionAnimationUsageInfo(
                file=file_path,
                line_number=line_num,
                keyframes_name=kf_name,
                property="animation",
                has_duration=has_duration,
                has_timing_function=has_timing,
                has_iteration=has_iteration,
                is_composed=bool(match.group(1)),  # Uses ${} interpolation
            ))

        return {
            'keyframes': keyframes,
            'animation_usages': animation_usages,
        }

    def _extract_template_body(self, content: str, backtick_pos: int) -> str:
        """Extract content between backticks."""
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

    def _extract_steps(self, body: str) -> List[str]:
        """Extract animation step names (from, to, percentages)."""
        steps = []
        for match in re.finditer(r'(from|to|\d+%)\s*\{', body):
            steps.append(match.group(1))
        return sorted(set(steps))

    def _extract_animated_properties(self, body: str) -> List[str]:
        """Extract CSS properties being animated."""
        props = set()
        for match in self.RE_ANIMATED_PROPERTIES.finditer(body):
            props.add(match.group(1).lower())
        return sorted(props)
