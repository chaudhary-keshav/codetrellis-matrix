"""
Framer Motion scroll animation extractor for CodeTrellis.

Extracts scroll-related animation constructs:
- useScroll hook usage (scrollY, scrollX, scrollYProgress, scrollXProgress)
- useInView hook for intersection-based animations
- Scroll-linked motion values (useTransform chained with scroll)
- Parallax effects (useTransform with scroll progress)
- useMotionValueEvent for scroll events
- whileInView prop on components
- Scroll containers (scrollable motion components)

Supports framer-motion v5+ scroll APIs and motion v11+.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FramerScrollInfo:
    """useScroll hook usage."""
    variable_name: str = ""        # destructured var name
    scroll_values: List[str] = field(default_factory=list)  # 'scrollY', 'scrollX', 'scrollYProgress', etc.
    line_number: int = 0
    file_path: str = ""
    has_target: bool = False       # target: ref
    has_offset: bool = False       # offset: ["start end", "end start"]
    has_container: bool = False    # container: ref
    has_axis: bool = False


@dataclass
class FramerInViewInfo:
    """useInView hook usage."""
    variable_name: str = ""
    ref_name: str = ""
    line_number: int = 0
    file_path: str = ""
    has_once: bool = False         # once: true
    has_amount: bool = False       # amount: 0.5
    has_margin: bool = False       # margin: "-100px"


@dataclass
class FramerParallaxInfo:
    """Parallax effect using useTransform with scroll."""
    variable_name: str = ""
    input_source: str = ""         # e.g. 'scrollYProgress'
    output_property: str = ""      # e.g. 'y', 'opacity', 'scale'
    line_number: int = 0
    file_path: str = ""
    input_range: str = ""          # e.g. '[0, 1]'
    output_range: str = ""         # e.g. '[0, -100]'


# ── Regex patterns ──────────────────────────────────────────────

# useScroll() hook
USE_SCROLL_PATTERN = re.compile(
    r"""(?:const|let|var)\s+\{\s*([\w\s,]+)\s*\}\s*=\s*useScroll\s*\(([^)]*)\)""",
    re.MULTILINE
)

# useInView() hook
USE_IN_VIEW_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*useInView\s*\(\s*(\w+)?\s*(?:,\s*\{([^}]*)\})?\s*\)""",
    re.MULTILINE
)

# useTransform() with scroll values
USE_TRANSFORM_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*useTransform\s*\(\s*(\w+)\s*,\s*(\[[^\]]+\])\s*,\s*(\[[^\]]+\])""",
    re.MULTILINE
)

# useMotionValueEvent with scroll
MOTION_VALUE_EVENT_PATTERN = re.compile(
    r"""useMotionValueEvent\s*\(\s*(\w+)\s*,\s*['"](change|animationStart|animationComplete|animationCancel)['"]""",
    re.MULTILINE
)

# Scroll-related motion values
SCROLL_VALUE_NAMES = {
    'scrollY', 'scrollX', 'scrollYProgress', 'scrollXProgress',
}

# whileInView prop detection (also in gesture extractor, but relevant here)
WHILE_IN_VIEW_PATTERN = re.compile(
    r"""whileInView\s*=\s*(?:\{\{?\s*([^}]+)\}\}?|['"]([\w]+)['"])""",
    re.MULTILINE
)

# useSpring chained with scroll
USE_SPRING_SCROLL_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*useSpring\s*\(\s*(\w+)""",
    re.MULTILINE
)


class FramerScrollExtractor:
    """Extract Framer Motion scroll-related constructs."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract all scroll-related animation constructs.

        Returns dict with keys: scrolls, in_views, parallaxes, scroll_events.
        """
        result = {
            'scrolls': [],
            'in_views': [],
            'parallaxes': [],
            'scroll_events': [],
        }

        if not content.strip():
            return result

        result['scrolls'] = self._extract_scrolls(content, file_path)
        result['in_views'] = self._extract_in_views(content, file_path)
        result['parallaxes'] = self._extract_parallaxes(content, file_path)
        result['scroll_events'] = self._extract_scroll_events(content, file_path)

        return result

    def _extract_scrolls(self, content: str, file_path: str) -> List[FramerScrollInfo]:
        """Extract useScroll hook usage."""
        scrolls = []
        for m in USE_SCROLL_PATTERN.finditer(content):
            destructured = m.group(1)
            config = m.group(2) or ""
            line_num = content[:m.start()].count('\n') + 1

            # Parse destructured values
            values = [v.strip() for v in destructured.split(',') if v.strip()]

            scrolls.append(FramerScrollInfo(
                variable_name=destructured.strip(),
                scroll_values=values,
                line_number=line_num,
                file_path=file_path,
                has_target='target' in config,
                has_offset='offset' in config,
                has_container='container' in config,
                has_axis='axis' in config,
            ))

        return scrolls[:20]

    def _extract_in_views(self, content: str, file_path: str) -> List[FramerInViewInfo]:
        """Extract useInView hook usage."""
        in_views = []
        for m in USE_IN_VIEW_PATTERN.finditer(content):
            var_name = m.group(1)
            ref_name = m.group(2) or ""
            config = m.group(3) or ""
            line_num = content[:m.start()].count('\n') + 1

            in_views.append(FramerInViewInfo(
                variable_name=var_name,
                ref_name=ref_name,
                line_number=line_num,
                file_path=file_path,
                has_once='once' in config,
                has_amount='amount' in config,
                has_margin='margin' in config,
            ))

        return in_views[:20]

    def _extract_parallaxes(self, content: str, file_path: str) -> List[FramerParallaxInfo]:
        """Extract parallax effects (useTransform chained with scroll values)."""
        parallaxes = []
        for m in USE_TRANSFORM_PATTERN.finditer(content):
            var_name = m.group(1)
            input_source = m.group(2)
            input_range = m.group(3)
            output_range = m.group(4)
            line_num = content[:m.start()].count('\n') + 1

            # Determine output property from variable name
            output_prop = self._infer_property_from_name(var_name)

            parallaxes.append(FramerParallaxInfo(
                variable_name=var_name,
                input_source=input_source,
                output_property=output_prop,
                line_number=line_num,
                file_path=file_path,
                input_range=input_range,
                output_range=output_range,
            ))

        return parallaxes[:20]

    def _extract_scroll_events(self, content: str, file_path: str) -> List[Dict]:
        """Extract useMotionValueEvent for scroll-related events."""
        events = []
        for m in MOTION_VALUE_EVENT_PATTERN.finditer(content):
            value_name = m.group(1)
            event_type = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            events.append({
                'value_name': value_name,
                'event_type': event_type,
                'line': line_num,
                'file': file_path,
            })

        return events[:20]

    # ── Helpers ──────────────────────────────────────────────────

    def _infer_property_from_name(self, var_name: str) -> str:
        """Infer the animated property from a variable name."""
        lower = var_name.lower()
        if 'opacity' in lower:
            return 'opacity'
        if 'scale' in lower:
            return 'scale'
        if 'rotate' in lower or 'rotation' in lower:
            return 'rotate'
        if 'y' in lower and ('scroll' in lower or 'parallax' in lower or 'offset' in lower):
            return 'y'
        if 'x' in lower:
            return 'x'
        if 'y' in lower:
            return 'y'
        if 'width' in lower:
            return 'width'
        if 'height' in lower:
            return 'height'
        if 'background' in lower or 'bg' in lower:
            return 'backgroundColor'
        return var_name
