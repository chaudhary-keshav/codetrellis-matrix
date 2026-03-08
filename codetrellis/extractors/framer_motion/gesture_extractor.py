"""
Framer Motion gesture extractor for CodeTrellis.

Extracts gesture-related constructs from framer-motion / motion code:
- Drag configurations (dragConstraints, dragElastic, dragMomentum)
- Hover interactions (whileHover, onHoverStart, onHoverEnd)
- Tap/Press interactions (whileTap, onTap, onTapStart, onTapCancel)
- Pan gestures (onPan, onPanStart, onPanEnd)
- Focus gestures (whileFocus)
- Viewport triggers (whileInView, onViewportEnter, onViewportLeave)
- useDragControls hook

Supports framer-motion v1 → v11+ and motion v11+.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FramerGestureInfo:
    """Generic gesture usage (pan, focus, viewport)."""
    gesture_type: str = ""         # 'pan', 'focus', 'viewport', 'inView'
    event_name: str = ""           # 'onPan', 'whileFocus', 'whileInView'
    line_number: int = 0
    file_path: str = ""
    has_callback: bool = False
    component_type: str = ""


@dataclass
class FramerDragInfo:
    """Drag configuration on a motion component."""
    drag_axis: str = ""            # 'x', 'y', 'true' (both), or ''
    line_number: int = 0
    file_path: str = ""
    has_constraints: bool = False
    has_elastic: bool = False
    has_momentum: bool = False
    has_drag_controls: bool = False
    has_drag_listener: bool = False
    has_drag_snap_to_origin: bool = False
    component_type: str = ""


@dataclass
class FramerHoverInfo:
    """Hover interaction."""
    line_number: int = 0
    file_path: str = ""
    has_while_hover: bool = False
    has_on_hover_start: bool = False
    has_on_hover_end: bool = False
    hover_properties: List[str] = field(default_factory=list)
    component_type: str = ""


@dataclass
class FramerTapInfo:
    """Tap/press interaction."""
    line_number: int = 0
    file_path: str = ""
    has_while_tap: bool = False
    has_on_tap: bool = False
    has_on_tap_start: bool = False
    has_on_tap_cancel: bool = False
    tap_properties: List[str] = field(default_factory=list)
    component_type: str = ""


# ── Regex patterns ──────────────────────────────────────────────

# drag prop: drag, drag="x", drag="y", drag={true}
DRAG_PATTERN = re.compile(
    r"""(?:\s|^)drag(?:\s*=\s*(?:['"](x|y)['"]|\{?\s*(true|false)\s*\}?)|\s|>|/>)""",
    re.MULTILINE
)

# drag-related props
DRAG_CONSTRAINTS_PATTERN = re.compile(r"""dragConstraints""")
DRAG_ELASTIC_PATTERN = re.compile(r"""dragElastic""")
DRAG_MOMENTUM_PATTERN = re.compile(r"""dragMomentum""")
DRAG_CONTROLS_PATTERN = re.compile(r"""dragControls""")
DRAG_LISTENER_PATTERN = re.compile(r"""dragListener""")
DRAG_SNAP_PATTERN = re.compile(r"""dragSnapToOrigin""")

# useDragControls hook
USE_DRAG_CONTROLS_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*useDragControls\s*\(\s*\)""",
    re.MULTILINE
)

# whileHover, onHoverStart, onHoverEnd
HOVER_PATTERN = re.compile(
    r"""(whileHover|onHoverStart|onHoverEnd)\s*=\s*""",
    re.MULTILINE
)

# whileTap, onTap, onTapStart, onTapCancel
TAP_PATTERN = re.compile(
    r"""(whileTap|onTap|onTapStart|onTapCancel)\s*=\s*""",
    re.MULTILINE
)

# Pan events
PAN_PATTERN = re.compile(
    r"""(onPan|onPanStart|onPanEnd|onPanSessionStart)\s*=\s*""",
    re.MULTILINE
)

# Focus
FOCUS_PATTERN = re.compile(
    r"""(whileFocus)\s*=\s*""",
    re.MULTILINE
)

# Viewport / InView
VIEWPORT_PATTERN = re.compile(
    r"""(whileInView|onViewportEnter|onViewportLeave)\s*=\s*""",
    re.MULTILINE
)

# motion.* component tag for context
MOTION_TAG_RE = re.compile(r"""<(motion\.\w+)\b""")


class FramerGestureExtractor:
    """Extract Framer Motion gesture-related constructs."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract all gesture-related constructs.

        Returns dict with keys: drags, hovers, taps, gestures, drag_controls.
        """
        result = {
            'drags': [],
            'hovers': [],
            'taps': [],
            'gestures': [],
            'drag_controls': [],
        }

        if not content.strip():
            return result

        lines = content.split('\n')

        result['drags'] = self._extract_drags(content, file_path, lines)
        result['hovers'] = self._extract_hovers(content, file_path, lines)
        result['taps'] = self._extract_taps(content, file_path, lines)
        result['gestures'] = self._extract_gestures(content, file_path, lines)
        result['drag_controls'] = self._extract_drag_controls(content, file_path, lines)

        return result

    def _extract_drags(self, content: str, file_path: str, lines: list) -> List[FramerDragInfo]:
        """Extract drag configurations."""
        drags = []
        for m in DRAG_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            axis = m.group(1) or m.group(2) or "true"
            if axis == "false":
                continue

            # Search nearby for related drag props
            context_start = max(0, m.start() - 200)
            context_end = min(len(content), m.end() + 500)
            ctx = content[context_start:context_end]

            comp = self._find_motion_component(content, m.start())

            drags.append(FramerDragInfo(
                drag_axis=axis,
                line_number=line_num,
                file_path=file_path,
                has_constraints=bool(DRAG_CONSTRAINTS_PATTERN.search(ctx)),
                has_elastic=bool(DRAG_ELASTIC_PATTERN.search(ctx)),
                has_momentum=bool(DRAG_MOMENTUM_PATTERN.search(ctx)),
                has_drag_controls=bool(DRAG_CONTROLS_PATTERN.search(ctx)),
                has_drag_listener=bool(DRAG_LISTENER_PATTERN.search(ctx)),
                has_drag_snap_to_origin=bool(DRAG_SNAP_PATTERN.search(ctx)),
                component_type=comp,
            ))

        return drags[:30]

    def _extract_hovers(self, content: str, file_path: str, lines: list) -> List[FramerHoverInfo]:
        """Extract hover interactions."""
        # Group hover props by motion component context
        hover_regions = {}
        for m in HOVER_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            prop_name = m.group(1)

            # Use line_num as region key (approximate grouping)
            region = line_num // 5
            if region not in hover_regions:
                hover_regions[region] = {
                    'line': line_num, 'while_hover': False,
                    'on_hover_start': False, 'on_hover_end': False,
                    'props': [],
                }
            if prop_name == 'whileHover':
                hover_regions[region]['while_hover'] = True
                # Extract properties
                val_m = re.search(r"""whileHover\s*=\s*\{\{?\s*([^}]+)\}\}?""", content[m.start():m.start() + 300])
                if val_m:
                    for p in ['opacity', 'scale', 'x', 'y', 'rotate', 'backgroundColor', 'color', 'boxShadow']:
                        if p in val_m.group(1):
                            hover_regions[region]['props'].append(p)
            elif prop_name == 'onHoverStart':
                hover_regions[region]['on_hover_start'] = True
            elif prop_name == 'onHoverEnd':
                hover_regions[region]['on_hover_end'] = True

        hovers = []
        for r in hover_regions.values():
            comp = self._find_motion_component_at_line(content, r['line'])
            hovers.append(FramerHoverInfo(
                line_number=r['line'],
                file_path=file_path,
                has_while_hover=r['while_hover'],
                has_on_hover_start=r['on_hover_start'],
                has_on_hover_end=r['on_hover_end'],
                hover_properties=r['props'],
                component_type=comp,
            ))

        return hovers[:30]

    def _extract_taps(self, content: str, file_path: str, lines: list) -> List[FramerTapInfo]:
        """Extract tap/press interactions."""
        tap_regions = {}
        for m in TAP_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            prop_name = m.group(1)

            region = line_num // 5
            if region not in tap_regions:
                tap_regions[region] = {
                    'line': line_num, 'while_tap': False,
                    'on_tap': False, 'on_tap_start': False,
                    'on_tap_cancel': False, 'props': [],
                }
            if prop_name == 'whileTap':
                tap_regions[region]['while_tap'] = True
                val_m = re.search(r"""whileTap\s*=\s*\{\{?\s*([^}]+)\}\}?""", content[m.start():m.start() + 300])
                if val_m:
                    for p in ['scale', 'opacity', 'x', 'y', 'rotate', 'backgroundColor']:
                        if p in val_m.group(1):
                            tap_regions[region]['props'].append(p)
            elif prop_name == 'onTap':
                tap_regions[region]['on_tap'] = True
            elif prop_name == 'onTapStart':
                tap_regions[region]['on_tap_start'] = True
            elif prop_name == 'onTapCancel':
                tap_regions[region]['on_tap_cancel'] = True

        taps = []
        for r in tap_regions.values():
            comp = self._find_motion_component_at_line(content, r['line'])
            taps.append(FramerTapInfo(
                line_number=r['line'],
                file_path=file_path,
                has_while_tap=r['while_tap'],
                has_on_tap=r['on_tap'],
                has_on_tap_start=r['on_tap_start'],
                has_on_tap_cancel=r['on_tap_cancel'],
                tap_properties=r['props'],
                component_type=comp,
            ))

        return taps[:30]

    def _extract_gestures(self, content: str, file_path: str, lines: list) -> List[FramerGestureInfo]:
        """Extract pan, focus, viewport gestures."""
        gestures = []

        for m in PAN_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            gestures.append(FramerGestureInfo(
                gesture_type='pan',
                event_name=m.group(1),
                line_number=line_num,
                file_path=file_path,
                has_callback=True,
                component_type=self._find_motion_component(content, m.start()),
            ))

        for m in FOCUS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            gestures.append(FramerGestureInfo(
                gesture_type='focus',
                event_name=m.group(1),
                line_number=line_num,
                file_path=file_path,
                has_callback=False,
                component_type=self._find_motion_component(content, m.start()),
            ))

        for m in VIEWPORT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            gestures.append(FramerGestureInfo(
                gesture_type='viewport',
                event_name=m.group(1),
                line_number=line_num,
                file_path=file_path,
                has_callback=m.group(1) != 'whileInView',
                component_type=self._find_motion_component(content, m.start()),
            ))

        return gestures[:40]

    def _extract_drag_controls(self, content: str, file_path: str, lines: list) -> List[Dict]:
        """Extract useDragControls hook usage."""
        controls = []
        for m in USE_DRAG_CONTROLS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            controls.append({
                'variable': m.group(1),
                'line': line_num,
                'file': file_path,
            })
        return controls[:10]

    # ── Helpers ──────────────────────────────────────────────────

    def _find_motion_component(self, content: str, pos: int) -> str:
        """Find nearest motion.* component around the position."""
        search_start = max(0, pos - 300)
        preceding = content[search_start:pos]
        matches = list(MOTION_TAG_RE.finditer(preceding))
        if matches:
            return matches[-1].group(1)
        return ""

    def _find_motion_component_at_line(self, content: str, line_num: int) -> str:
        """Find motion component near a line number."""
        lines = content.split('\n')
        start_line = max(0, line_num - 5)
        end_line = min(len(lines), line_num + 2)
        region = '\n'.join(lines[start_line:end_line])
        m = MOTION_TAG_RE.search(region)
        if m:
            return m.group(1)
        return ""
