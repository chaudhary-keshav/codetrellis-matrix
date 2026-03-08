"""
Leaflet/Mapbox interaction, event, and animation extractor.

Extracts:
- Map events (.on(), onClick, etc.)
- Drawing interactions (Leaflet.Draw, Mapbox Draw)
- Animations (flyTo, panTo, setView transitions)
- Gestures (drag, scroll zoom, touch zoom, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LeafletEventInfo:
    """Represents a detected map event handler."""
    name: str = ""
    line_number: int = 0
    event_type: str = ""        # 'click', 'move', 'zoom', 'load', 'layer', 'draw', 'popup', 'custom'
    component: str = ""         # 'map', 'marker', 'layer', 'control', etc.
    is_delegated: bool = False  # onEachFeature delegation


@dataclass
class LeafletDrawInfo:
    """Represents a detected drawing interaction."""
    name: str = ""
    line_number: int = 0
    draw_type: str = ""         # 'polygon', 'polyline', 'rectangle', 'circle', 'marker', 'full'
    library: str = ""           # 'leaflet-draw', 'mapbox-draw', 'geoman', 'leaflet-editable'
    has_edit: bool = False
    has_delete: bool = False


@dataclass
class LeafletAnimationInfo:
    """Represents a detected map animation/transition."""
    name: str = ""
    line_number: int = 0
    animation_type: str = ""    # 'fly_to', 'pan_to', 'set_view', 'fit_bounds', 'ease_to', 'zoom_to'
    has_duration: bool = False
    has_easing: bool = False
    value: str = ""


# ── Regex Patterns ────────────────────────────────────────────────────

# Leaflet .on() event pattern
LEAFLET_ON_EVENT_PATTERN = re.compile(
    r"""\.on\s*\(\s*['"](\w+)['"]\s*,""",
    re.DOTALL
)

# Mapbox GL .on() event pattern (same syntax)
MAPBOX_ON_EVENT_PATTERN = re.compile(
    r"""map\.on\s*\(\s*['"](\w+)['"]\s*,""",
    re.DOTALL
)

# React-Leaflet event props
REACT_EVENT_PROP_PATTERN = re.compile(
    r"""(?:eventHandlers\s*=\s*\{?\s*\{([^}]*)\}|(?:on(?:Click|DblClick|MouseDown|MouseUp|MouseOver|MouseOut|ContextMenu|Add|Remove|PopupOpen|PopupClose|TooltipOpen|TooltipClose|DragStart|Drag|DragEnd|MoveStart|Move|MoveEnd|ZoomStart|Zoom|ZoomEnd|Load))\s*=)""",
    re.DOTALL
)

# Mapbox GL event handler methods
MAPBOX_EVENT_METHODS = re.compile(
    r"""\.on\s*\(\s*['"](?:click|dblclick|mousedown|mouseup|mousemove|mouseenter|mouseleave|contextmenu|wheel|touchstart|touchend|touchcancel|movestart|move|moveend|dragstart|drag|dragend|zoomstart|zoom|zoomend|pitchstart|pitch|pitchend|rotatestart|rotate|rotateend|load|idle|remove|render|resize|data|styledata|sourcedata|error)['"]\s*,""",
    re.DOTALL
)

# Event type categorization
EVENT_CATEGORIES = {
    'click': 'click',
    'dblclick': 'click',
    'contextmenu': 'click',
    'mousedown': 'click',
    'mouseup': 'click',
    'mousemove': 'move',
    'mouseover': 'move',
    'mouseout': 'move',
    'mouseenter': 'move',
    'mouseleave': 'move',
    'move': 'move',
    'movestart': 'move',
    'moveend': 'move',
    'zoom': 'zoom',
    'zoomstart': 'zoom',
    'zoomend': 'zoom',
    'zoomlevelschange': 'zoom',
    'drag': 'move',
    'dragstart': 'move',
    'dragend': 'move',
    'load': 'load',
    'unload': 'load',
    'idle': 'load',
    'resize': 'load',
    'add': 'layer',
    'remove': 'layer',
    'layeradd': 'layer',
    'layerremove': 'layer',
    'popupopen': 'popup',
    'popupclose': 'popup',
    'tooltipopen': 'popup',
    'tooltipclose': 'popup',
    'draw:created': 'draw',
    'draw:edited': 'draw',
    'draw:deleted': 'draw',
    'draw:drawstart': 'draw',
    'pm:create': 'draw',
    'pm:edit': 'draw',
    'pm:remove': 'draw',
    'pitch': 'zoom',
    'pitchstart': 'zoom',
    'pitchend': 'zoom',
    'rotate': 'zoom',
    'rotatestart': 'zoom',
    'rotateend': 'zoom',
    'data': 'load',
    'styledata': 'load',
    'sourcedata': 'load',
    'render': 'load',
    'error': 'load',
}

# Drawing library patterns
LEAFLET_DRAW_PATTERN = re.compile(
    r"""(?:L\.Draw|leaflet-draw|new\s+L\.Control\.Draw|'leaflet-draw')""",
    re.IGNORECASE
)

MAPBOX_DRAW_PATTERN = re.compile(
    r"""(?:MapboxDraw|@mapbox/mapbox-gl-draw|mapbox-gl-draw)""",
    re.IGNORECASE
)

GEOMAN_PATTERN = re.compile(
    r"""(?:@geoman-io|leaflet-geoman|pm\.enable|pm\.addControls)""",
    re.IGNORECASE
)

LEAFLET_EDITABLE_PATTERN = re.compile(
    r"""(?:leaflet-editable|editable\s*:\s*true|\.enableEdit|\.disableEdit)""",
    re.IGNORECASE
)

# Draw type detection
DRAW_TYPE_PATTERNS = {
    'polygon': re.compile(r'(?:polygon|Polygon)\s*[:=]\s*(?:true|\{)', re.IGNORECASE),
    'polyline': re.compile(r'(?:polyline|Polyline)\s*[:=]\s*(?:true|\{)', re.IGNORECASE),
    'rectangle': re.compile(r'(?:rectangle|Rectangle)\s*[:=]\s*(?:true|\{)', re.IGNORECASE),
    'circle': re.compile(r'(?:circle|Circle)\s*[:=]\s*(?:true|\{)', re.IGNORECASE),
    'marker': re.compile(r'(?:marker|Marker)\s*[:=]\s*(?:true|\{)', re.IGNORECASE),
}

# Animation patterns
ANIMATION_PATTERNS = {
    'fly_to': re.compile(r"""\.flyTo\s*\("""),
    'pan_to': re.compile(r"""\.panTo\s*\("""),
    'set_view': re.compile(r"""\.setView\s*\("""),
    'fit_bounds': re.compile(r"""\.fitBounds\s*\("""),
    'fly_to_bounds': re.compile(r"""\.flyToBounds\s*\("""),
    'ease_to': re.compile(r"""\.easeTo\s*\("""),
    'jump_to': re.compile(r"""\.jumpTo\s*\("""),
    'zoom_to': re.compile(r"""\.zoomTo\s*\("""),
    'rotate_to': re.compile(r"""\.rotateTo\s*\("""),
}

DURATION_PATTERN = re.compile(r'(?:duration|animate)\s*[:=]')
EASING_PATTERN = re.compile(r'(?:easing|easeLinearity)\s*[:=]')


class LeafletInteractionExtractor:
    """Extracts events, drawing, and animations from Leaflet/Mapbox code."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract interaction information.

        Returns:
            Dict with 'events', 'drawings', 'animations'.
        """
        events = []
        drawings = []
        animations = []

        # ── Leaflet .on() Events ─────────────────────────────────
        for match in LEAFLET_ON_EVENT_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            event_name = match.group(1).lower()
            category = EVENT_CATEGORIES.get(event_name, 'custom')
            # Try to determine which component
            before = content[max(0, match.start()-100):match.start()]
            component = 'map'
            if re.search(r'marker', before, re.IGNORECASE):
                component = 'marker'
            elif re.search(r'layer|polygon|polyline|circle|geojson', before, re.IGNORECASE):
                component = 'layer'
            events.append(LeafletEventInfo(
                name=event_name,
                line_number=line,
                event_type=category,
                component=component,
            ))

        # ── React-Leaflet Event Props ────────────────────────────
        for match in REACT_EVENT_PROP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            event_handlers = match.group(1) if match.group(1) else match.group(0)
            # Extract handler names
            handler_names = re.findall(r'(\w+)\s*:', event_handlers) if match.group(1) else []
            if handler_names:
                for handler in handler_names:
                    category = EVENT_CATEGORIES.get(handler.lower(), 'custom')
                    events.append(LeafletEventInfo(
                        name=handler,
                        line_number=line,
                        event_type=category,
                        component='react-leaflet',
                    ))
            else:
                # Single event prop like onClick=
                prop_match = re.search(r'on(\w+)\s*=', match.group(0))
                if prop_match:
                    event_name = prop_match.group(1).lower()
                    category = EVENT_CATEGORIES.get(event_name, 'custom')
                    events.append(LeafletEventInfo(
                        name=event_name,
                        line_number=line,
                        event_type=category,
                        component='react-leaflet',
                    ))

        # ── Drawing: Leaflet Draw ────────────────────────────────
        for match in LEAFLET_DRAW_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 800]
            draw_types = []
            for dt, dp in DRAW_TYPE_PATTERNS.items():
                if dp.search(context_after):
                    draw_types.append(dt)
            drawings.append(LeafletDrawInfo(
                name="LeafletDraw",
                line_number=line,
                draw_type=','.join(draw_types) if draw_types else 'full',
                library='leaflet-draw',
                has_edit=bool(re.search(r'edit\s*[:=]\s*(?:true|\{)', context_after, re.IGNORECASE)),
                has_delete=bool(re.search(r'(?:delete|remove)\s*[:=]\s*(?:true|\{)', context_after, re.IGNORECASE)),
            ))

        # ── Drawing: Mapbox Draw ─────────────────────────────────
        for match in MAPBOX_DRAW_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 500]
            drawings.append(LeafletDrawInfo(
                name="MapboxDraw",
                line_number=line,
                draw_type='full',
                library='mapbox-draw',
                has_edit=True,
                has_delete=bool(re.search(r'trash', context_after, re.IGNORECASE)),
            ))

        # ── Drawing: Geoman ──────────────────────────────────────
        for match in GEOMAN_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            drawings.append(LeafletDrawInfo(
                name="Geoman",
                line_number=line,
                draw_type='full',
                library='geoman',
                has_edit=True,
                has_delete=True,
            ))

        # ── Drawing: Leaflet Editable ────────────────────────────
        for match in LEAFLET_EDITABLE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            drawings.append(LeafletDrawInfo(
                name="LeafletEditable",
                line_number=line,
                draw_type='full',
                library='leaflet-editable',
                has_edit=True,
            ))

        # ── Animations ───────────────────────────────────────────
        for anim_type, pattern in ANIMATION_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                context_after = content[match.start():match.start() + 300]
                animations.append(LeafletAnimationInfo(
                    name=anim_type,
                    line_number=line,
                    animation_type=anim_type,
                    has_duration=bool(DURATION_PATTERN.search(context_after)),
                    has_easing=bool(EASING_PATTERN.search(context_after)),
                ))

        return {
            'events': events,
            'drawings': drawings,
            'animations': animations,
        }
