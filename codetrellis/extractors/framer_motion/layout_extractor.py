"""
Framer Motion layout animation extractor for CodeTrellis.

Extracts layout-related animation constructs:
- layout prop on motion components (layout, layout="position", layout="size")
- LayoutGroup usage
- Shared layout animations (layoutId, layoutScroll, layoutDependency)
- AnimatePresence exit animations
- layoutTransition configurations
- useMotionValueEvent for layout events

Supports framer-motion v2+ layout animations and motion v11+.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FramerLayoutAnimInfo:
    """Layout animation configuration on a motion component."""
    layout_type: str = ""          # 'true', 'position', 'size', 'preserve-aspect'
    line_number: int = 0
    file_path: str = ""
    component_type: str = ""       # 'motion.div', etc.
    has_layout_id: bool = False
    has_layout_scroll: bool = False
    has_layout_dependency: bool = False
    layout_id_value: str = ""


@dataclass
class FramerSharedLayoutInfo:
    """Shared layout / LayoutGroup usage."""
    layout_group_type: str = ""    # 'LayoutGroup', 'AnimateSharedLayout' (legacy)
    line_number: int = 0
    file_path: str = ""
    layout_id: str = ""
    has_crossfade: bool = False
    is_legacy: bool = False        # AnimateSharedLayout (deprecated in v5+)


@dataclass
class FramerExitAnimInfo:
    """Exit animation (AnimatePresence + exit prop)."""
    exit_properties: List[str] = field(default_factory=list)
    line_number: int = 0
    file_path: str = ""
    component_type: str = ""
    has_custom: bool = False       # custom prop for dynamic exit


# ── Regex patterns ──────────────────────────────────────────────

# layout prop: layout, layout="position", layout="size", layout={true}
LAYOUT_PROP_PATTERN = re.compile(
    r"""(?:\s|^)layout(?:\s*=\s*(?:['"](position|size|preserve-aspect)['"]|\{?\s*(true)\s*\}?)|\s|/>|>)""",
    re.MULTILINE
)

# layoutId prop: layoutId="id"
LAYOUT_ID_PATTERN = re.compile(
    r"""layoutId\s*=\s*(?:['"]([\w\-]+)['"]|\{([^}]+)\})""",
    re.MULTILINE
)

# layoutScroll
LAYOUT_SCROLL_PATTERN = re.compile(r"""layoutScroll""")

# layoutDependency
LAYOUT_DEPENDENCY_PATTERN = re.compile(r"""layoutDependency""")

# LayoutGroup
LAYOUT_GROUP_PATTERN = re.compile(
    r"""<LayoutGroup\b([^>]*)>""",
    re.MULTILINE
)

# AnimateSharedLayout (legacy, deprecated in v5)
ANIMATE_SHARED_LAYOUT_PATTERN = re.compile(
    r"""<AnimateSharedLayout\b([^>]*)>""",
    re.MULTILINE
)

# exit prop: exit={{ ... }} or exit="variantName"
EXIT_PROP_PATTERN = re.compile(
    r"""exit\s*=\s*(?:\{\{?\s*([^}]+)\}\}?|['"]([\w]+)['"])""",
    re.MULTILINE
)

# custom exit prop
CUSTOM_PROP_PATTERN = re.compile(r"""custom\s*=\s*""")

# motion.* tag
MOTION_TAG_RE = re.compile(r"""<(motion\.\w+)\b""")

# Animated properties for exit detection
EXIT_PROP_NAMES = {
    'opacity', 'x', 'y', 'z', 'scale', 'scaleX', 'scaleY',
    'rotate', 'rotateX', 'rotateY', 'rotateZ',
    'width', 'height', 'translateX', 'translateY',
}


class FramerLayoutExtractor:
    """Extract Framer Motion layout animation constructs."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract all layout-related animation constructs.

        Returns dict with keys: layout_anims, shared_layouts, exit_anims.
        """
        result = {
            'layout_anims': [],
            'shared_layouts': [],
            'exit_anims': [],
        }

        if not content.strip():
            return result

        result['layout_anims'] = self._extract_layout_anims(content, file_path)
        result['shared_layouts'] = self._extract_shared_layouts(content, file_path)
        result['exit_anims'] = self._extract_exit_anims(content, file_path)

        return result

    def _extract_layout_anims(self, content: str, file_path: str) -> List[FramerLayoutAnimInfo]:
        """Extract layout prop usage on motion components."""
        anims = []
        for m in LAYOUT_PROP_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            layout_type = m.group(1) or m.group(2) or "true"

            # Look for layoutId nearby
            context_start = max(0, m.start() - 100)
            context_end = min(len(content), m.end() + 300)
            ctx = content[context_start:context_end]

            layout_id = ""
            lid_m = LAYOUT_ID_PATTERN.search(ctx)
            if lid_m:
                layout_id = lid_m.group(1) or lid_m.group(2) or ""

            comp = self._find_motion_component(content, m.start())

            anims.append(FramerLayoutAnimInfo(
                layout_type=layout_type,
                line_number=line_num,
                file_path=file_path,
                component_type=comp,
                has_layout_id=bool(layout_id),
                has_layout_scroll=bool(LAYOUT_SCROLL_PATTERN.search(ctx)),
                has_layout_dependency=bool(LAYOUT_DEPENDENCY_PATTERN.search(ctx)),
                layout_id_value=layout_id,
            ))

        return anims[:40]

    def _extract_shared_layouts(self, content: str, file_path: str) -> List[FramerSharedLayoutInfo]:
        """Extract LayoutGroup, AnimateSharedLayout, and standalone layoutId usage."""
        results = []
        seen_layout_ids = set()

        # Modern LayoutGroup
        for m in LAYOUT_GROUP_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            attrs = m.group(1)

            # Extract layoutId from children context
            layout_id = ""
            lid_m = LAYOUT_ID_PATTERN.search(content[m.end():m.end() + 1000])
            if lid_m:
                layout_id = lid_m.group(1) or lid_m.group(2) or ""

            results.append(FramerSharedLayoutInfo(
                layout_group_type='LayoutGroup',
                line_number=line_num,
                file_path=file_path,
                layout_id=layout_id,
                has_crossfade='crossfade' in attrs.lower() if attrs else False,
                is_legacy=False,
            ))

        # Legacy AnimateSharedLayout
        for m in ANIMATE_SHARED_LAYOUT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            attrs = m.group(1)

            results.append(FramerSharedLayoutInfo(
                layout_group_type='AnimateSharedLayout',
                line_number=line_num,
                file_path=file_path,
                layout_id="",
                has_crossfade='crossfade' in attrs.lower() if attrs else False,
                is_legacy=True,
            ))

        # Standalone layoutId props (shared layout animation without explicit group)
        for m in LAYOUT_ID_PATTERN.finditer(content):
            layout_id = m.group(1) or m.group(2) or ""
            if layout_id in seen_layout_ids:
                continue
            seen_layout_ids.add(layout_id)
            line_num = content[:m.start()].count('\n') + 1
            comp = self._find_motion_component(content, m.start())

            results.append(FramerSharedLayoutInfo(
                layout_group_type=comp or 'motion.div',
                line_number=line_num,
                file_path=file_path,
                layout_id=layout_id,
                has_crossfade=False,
                is_legacy=False,
            ))

        return results[:20]

    def _extract_exit_anims(self, content: str, file_path: str) -> List[FramerExitAnimInfo]:
        """Extract exit animations."""
        exits = []
        for m in EXIT_PROP_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            value = m.group(1) or m.group(2) or ""

            # Extract properties from inline exit value
            props = []
            if m.group(1):  # Inline object
                for p in EXIT_PROP_NAMES:
                    if p in value:
                        props.append(p)

            # Check for custom prop nearby
            context_start = max(0, m.start() - 200)
            context_end = min(len(content), m.end() + 200)
            ctx = content[context_start:context_end]

            comp = self._find_motion_component(content, m.start())

            exits.append(FramerExitAnimInfo(
                exit_properties=props,
                line_number=line_num,
                file_path=file_path,
                component_type=comp,
                has_custom=bool(CUSTOM_PROP_PATTERN.search(ctx)),
            ))

        return exits[:30]

    # ── Helpers ──────────────────────────────────────────────────

    def _find_motion_component(self, content: str, pos: int) -> str:
        """Find nearest motion.* component around the position."""
        search_start = max(0, pos - 300)
        preceding = content[search_start:pos]
        matches = list(MOTION_TAG_RE.finditer(preceding))
        if matches:
            return matches[-1].group(1)
        return ""
