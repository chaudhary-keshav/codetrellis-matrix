"""
D3.js Interaction Extractor

Extracts interaction and animation constructs:
- Event listeners (selection.on, d3.dispatch)
- Drag behavior (d3.drag)
- Transitions (selection.transition, d3.transition)
- Tooltips (div.tooltip, d3-tip, mouseover/mouseout patterns)
- Voronoi overlays for hit detection
- Dispatch (custom events)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class D3EventInfo:
    """D3 event listener or dispatch."""
    name: str
    file: str
    line_number: int
    event_type: str  # 'click', 'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave', 'pointerdown', 'pointermove', 'pointerup', 'touchstart', 'touchmove', 'touchend', 'input', 'change', 'custom'
    target: str = ""  # selection target
    is_dispatch: bool = False  # d3.dispatch vs .on()


@dataclass
class D3DragInfo:
    """D3 drag behavior."""
    name: str
    file: str
    line_number: int
    has_subject: bool = False
    has_container: bool = False
    has_filter: bool = False
    has_touch_able: bool = False
    events: List[str] = field(default_factory=list)  # 'start', 'drag', 'end'


@dataclass
class D3TransitionInfo:
    """D3 transition."""
    name: str
    file: str
    line_number: int
    has_duration: bool = False
    has_delay: bool = False
    has_ease: bool = False
    has_on_end: bool = False
    has_on_start: bool = False
    ease_type: str = ""  # 'easeLinear', 'easeCubic', 'easeElastic', etc.
    duration: str = ""
    is_named: bool = False  # .transition("name")
    transition_name: str = ""
    properties: List[str] = field(default_factory=list)  # animated attrs/styles


@dataclass
class D3TooltipInfo:
    """D3 tooltip pattern."""
    name: str
    file: str
    line_number: int
    tooltip_type: str  # 'div', 'd3-tip', 'title', 'custom'
    has_mouseover: bool = False
    has_mouseout: bool = False
    has_mousemove: bool = False
    has_html: bool = False
    has_text: bool = False


class D3InteractionExtractor:
    """Extracts D3.js interaction and animation constructs."""

    # ── Event listener patterns ───────────────────────────────────
    EVENT_ON_PATTERN = re.compile(
        r'\.on\s*\(\s*["\'](\w+)(?:\.(\w+))?["\']',
        re.MULTILINE
    )

    # Standard DOM event types
    STANDARD_EVENTS = {
        'click', 'dblclick', 'contextmenu',
        'mouseover', 'mouseout', 'mousemove', 'mouseenter', 'mouseleave',
        'mousedown', 'mouseup',
        'pointerdown', 'pointermove', 'pointerup', 'pointerover', 'pointerout',
        'pointerenter', 'pointerleave',
        'touchstart', 'touchmove', 'touchend', 'touchcancel',
        'wheel', 'scroll', 'resize',
        'input', 'change', 'submit', 'focus', 'blur',
        'keydown', 'keyup', 'keypress',
    }

    # d3.dispatch pattern
    DISPATCH_PATTERN = re.compile(
        r'd3\.dispatch\s*\(\s*(.+?)\s*\)', re.MULTILINE
    )

    # ── Drag patterns ─────────────────────────────────────────────
    DRAG_PATTERN = re.compile(r'd3\.drag\s*\(', re.MULTILINE)
    DRAG_SUBJECT_PATTERN = re.compile(r'\.subject\s*\(', re.MULTILINE)
    DRAG_CONTAINER_PATTERN = re.compile(r'\.container\s*\(', re.MULTILINE)
    DRAG_FILTER_PATTERN = re.compile(r'\.filter\s*\(', re.MULTILINE)
    DRAG_TOUCHABLE_PATTERN = re.compile(r'\.touchable\s*\(', re.MULTILINE)
    DRAG_ON_PATTERN = re.compile(
        r'\.on\s*\(\s*["\'](start|drag|end)["\']',
        re.MULTILINE
    )

    # ── Transition patterns ───────────────────────────────────────
    TRANSITION_PATTERN = re.compile(
        r'\.transition\s*\(\s*(?:["\'](\w+)["\'])?\s*\)', re.MULTILINE
    )
    D3_TRANSITION_PATTERN = re.compile(
        r'd3\.transition\s*\(\s*(?:["\'](\w+)["\'])?\s*\)', re.MULTILINE
    )
    DURATION_PATTERN = re.compile(r'\.duration\s*\(\s*(\d+)\s*\)', re.MULTILINE)
    DELAY_PATTERN = re.compile(r'\.delay\s*\(', re.MULTILINE)
    EASE_PATTERN = re.compile(
        r'\.ease\s*\(\s*d3\.(\w+)', re.MULTILINE
    )
    TRANSITION_ON_PATTERN = re.compile(
        r'\.on\s*\(\s*["\'](end|start|interrupt)["\']', re.MULTILINE
    )
    TRANSITION_ATTR_PATTERN = re.compile(
        r'\.attr\s*\(\s*["\'](\w+)["\']', re.MULTILINE
    )
    TRANSITION_STYLE_PATTERN = re.compile(
        r'\.style\s*\(\s*["\']([^"\']+)["\']', re.MULTILINE
    )

    # ── Tooltip patterns ──────────────────────────────────────────
    TOOLTIP_DIV_PATTERN = re.compile(
        r'\.(?:append|select(?:All)?)\s*\(\s*["\']div["\']\s*\).*?'
        r'(?:\.(?:attr|classed)\s*\(\s*["\'](?:class|id)["\']\s*,\s*["\'][^"\']*tooltip[^"\']*["\'])',
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    TOOLTIP_CLASS_PATTERN = re.compile(
        r'tooltip|tip',
        re.IGNORECASE
    )
    D3_TIP_PATTERN = re.compile(
        r'd3[.-]tip|d3Tip|d3\.tip\s*\(', re.MULTILINE
    )
    TITLE_TOOLTIP_PATTERN = re.compile(
        r'\.append\s*\(\s*["\']title["\']\s*\)', re.MULTILINE
    )

    # Tooltip event patterns
    TOOLTIP_MOUSEOVER_PATTERN = re.compile(
        r'\.on\s*\(\s*["\']mouseover["\'].*?(?:tooltip|tip)',
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    TOOLTIP_MOUSEOUT_PATTERN = re.compile(
        r'\.on\s*\(\s*["\']mouseout["\'].*?(?:tooltip|tip)',
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )

    # ── Voronoi overlay patterns ──────────────────────────────────
    VORONOI_PATTERN = re.compile(
        r'd3\.(?:voronoi|Delaunay)', re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract interaction constructs from D3.js code."""
        result: Dict[str, Any] = {
            'events': [],
            'drags': [],
            'transitions': [],
            'tooltips': [],
        }

        # ── Event listeners ──────────────────────────────────────
        seen_events: set = set()
        for match in self.EVENT_ON_PATTERN.finditer(content):
            event_type = match.group(1)
            namespace = match.group(2) or ""
            # Skip brush/zoom/drag/transition events (handled separately)
            if event_type in ('start', 'brush', 'end', 'zoom', 'drag', 'interrupt'):
                continue
            key = f"{event_type}:{namespace}:{match.start()}"
            if key in seen_events:
                continue
            seen_events.add(key)
            line_num = content[:match.start()].count('\n') + 1
            is_standard = event_type in self.STANDARD_EVENTS
            result['events'].append(D3EventInfo(
                name=event_type,
                file=file_path,
                line_number=line_num,
                event_type=event_type if is_standard else 'custom',
                target=namespace,
                is_dispatch=False,
            ))

        # d3.dispatch custom events
        for match in self.DISPATCH_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            events_str = match.group(1)
            # Parse event names from dispatch args
            event_names = re.findall(r'["\'](\w+)["\']', events_str)
            for event_name in event_names:
                result['events'].append(D3EventInfo(
                    name=event_name,
                    file=file_path,
                    line_number=line_num,
                    event_type='custom',
                    is_dispatch=True,
                ))

        # ── Drag behaviors ───────────────────────────────────────
        for match in self.DRAG_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.end():match.end() + 500]
            events = [m.group(1) for m in self.DRAG_ON_PATTERN.finditer(after[:400])]

            result['drags'].append(D3DragInfo(
                name='drag',
                file=file_path,
                line_number=line_num,
                has_subject=bool(self.DRAG_SUBJECT_PATTERN.search(after[:400])),
                has_container=bool(self.DRAG_CONTAINER_PATTERN.search(after[:400])),
                has_filter=bool(self.DRAG_FILTER_PATTERN.search(after[:400])),
                has_touch_able=bool(self.DRAG_TOUCHABLE_PATTERN.search(after[:400])),
                events=events,
            ))

        # ── Transitions ──────────────────────────────────────────
        for match in self.TRANSITION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            transition_name = match.group(1) or ""
            after = content[match.end():match.end() + 500]
            duration_match = self.DURATION_PATTERN.search(after[:300])
            ease_match = self.EASE_PATTERN.search(after[:300])
            on_end = bool(self.TRANSITION_ON_PATTERN.search(after[:400]))
            attrs = [m.group(1) for m in self.TRANSITION_ATTR_PATTERN.finditer(after[:300])]
            styles = [m.group(1) for m in self.TRANSITION_STYLE_PATTERN.finditer(after[:300])]

            result['transitions'].append(D3TransitionInfo(
                name='transition',
                file=file_path,
                line_number=line_num,
                has_duration=bool(duration_match),
                has_delay=bool(self.DELAY_PATTERN.search(after[:300])),
                has_ease=bool(ease_match),
                has_on_end=on_end,
                ease_type=ease_match.group(1) if ease_match else "",
                duration=duration_match.group(1) if duration_match else "",
                is_named=bool(transition_name),
                transition_name=transition_name,
                properties=(attrs + styles)[:10],
            ))

        # d3.transition() top-level
        for match in self.D3_TRANSITION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            transition_name = match.group(1) or ""
            after = content[match.end():match.end() + 500]
            duration_match = self.DURATION_PATTERN.search(after[:300])
            ease_match = self.EASE_PATTERN.search(after[:300])

            result['transitions'].append(D3TransitionInfo(
                name='d3_transition',
                file=file_path,
                line_number=line_num,
                has_duration=bool(duration_match),
                has_delay=bool(self.DELAY_PATTERN.search(after[:300])),
                has_ease=bool(ease_match),
                ease_type=ease_match.group(1) if ease_match else "",
                duration=duration_match.group(1) if duration_match else "",
                is_named=bool(transition_name),
                transition_name=transition_name,
            ))

        # ── Tooltips ─────────────────────────────────────────────
        # div-based tooltip
        if self.TOOLTIP_DIV_PATTERN.search(content):
            match = self.TOOLTIP_DIV_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['tooltips'].append(D3TooltipInfo(
                name='div_tooltip',
                file=file_path,
                line_number=line_num,
                tooltip_type='div',
                has_mouseover=bool(self.TOOLTIP_MOUSEOVER_PATTERN.search(content)),
                has_mouseout=bool(self.TOOLTIP_MOUSEOUT_PATTERN.search(content)),
                has_mousemove=bool(re.search(r'\.on\s*\(\s*["\']mousemove["\']', content)),
                has_html=bool(re.search(r'tooltip.*\.html\s*\(', content, re.IGNORECASE | re.DOTALL)),
                has_text=bool(re.search(r'tooltip.*\.text\s*\(', content, re.IGNORECASE | re.DOTALL)),
            ))

        # d3-tip library
        for match in self.D3_TIP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['tooltips'].append(D3TooltipInfo(
                name='d3_tip',
                file=file_path,
                line_number=line_num,
                tooltip_type='d3-tip',
                has_html=bool(re.search(r'\.html\s*\(', content)),
            ))
            break  # Only record d3-tip once per file

        # title element tooltip
        for match in self.TITLE_TOOLTIP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['tooltips'].append(D3TooltipInfo(
                name='title_tooltip',
                file=file_path,
                line_number=line_num,
                tooltip_type='title',
                has_text=True,
            ))
            break  # Only record title tooltip once per file

        return result
