"""
Leaflet/Mapbox control, popup, and tooltip extractor.

Extracts:
- L.control.* / mapboxgl NavigationControl, etc.
- L.popup / mapboxgl.Popup / <Popup>
- L.tooltip / <Tooltip>
- Custom controls and legends
- LayersControl for base/overlay switching
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LeafletControlInfo:
    """Represents a detected map control."""
    name: str = ""
    line_number: int = 0
    control_type: str = ""      # 'zoom', 'layers', 'scale', 'attribution', 'fullscreen', 'draw', 'geocoder', 'custom'
    has_position: bool = False
    is_custom: bool = False
    has_options: bool = False


@dataclass
class LeafletPopupInfo:
    """Represents a detected popup."""
    name: str = ""
    line_number: int = 0
    popup_type: str = ""        # 'bind', 'standalone', 'jsx'
    has_content: bool = False
    is_custom: bool = False
    has_close_button: bool = False
    has_max_width: bool = False


@dataclass
class LeafletTooltipInfo:
    """Represents a detected tooltip."""
    name: str = ""
    line_number: int = 0
    tooltip_type: str = ""      # 'bind', 'standalone', 'jsx'
    has_content: bool = False
    is_permanent: bool = False
    is_custom: bool = False


# ── Regex Patterns ────────────────────────────────────────────────────

# Leaflet built-in controls
LEAFLET_CONTROL_PATTERNS = {
    'zoom': re.compile(r"""L\.control\.zoom\s*\("""),
    'layers': re.compile(r"""L\.control\.layers\s*\("""),
    'scale': re.compile(r"""L\.control\.scale\s*\("""),
    'attribution': re.compile(r"""L\.control\.attribution\s*\("""),
}

# Mapbox GL controls
MAPBOX_CONTROL_PATTERNS = {
    'zoom': re.compile(r"""new\s+mapboxgl\.NavigationControl\s*\("""),
    'scale': re.compile(r"""new\s+mapboxgl\.ScaleControl\s*\("""),
    'fullscreen': re.compile(r"""new\s+mapboxgl\.FullscreenControl\s*\("""),
    'geolocate': re.compile(r"""new\s+mapboxgl\.GeolocateControl\s*\("""),
    'attribution': re.compile(r"""new\s+mapboxgl\.AttributionControl\s*\("""),
}

# MapLibre GL controls
MAPLIBRE_CONTROL_PATTERNS = {
    'zoom': re.compile(r"""new\s+maplibregl\.NavigationControl\s*\("""),
    'scale': re.compile(r"""new\s+maplibregl\.ScaleControl\s*\("""),
    'fullscreen': re.compile(r"""new\s+maplibregl\.FullscreenControl\s*\("""),
    'geolocate': re.compile(r"""new\s+maplibregl\.GeolocateControl\s*\("""),
    'terrain': re.compile(r"""new\s+maplibregl\.TerrainControl\s*\("""),
}

# React-Leaflet control components
REACT_CONTROL_PATTERNS = {
    'zoom': re.compile(r'<ZoomControl\b'),
    'layers': re.compile(r'<LayersControl\b'),
    'scale': re.compile(r'<ScaleControl\b'),
    'attribution': re.compile(r'<AttributionControl\b'),
}

# Custom control pattern
CUSTOM_CONTROL_PATTERN = re.compile(
    r"""L\.Control\.extend\s*\(|L\.control\(\s*\{|extends\s+L\.Control""",
    re.DOTALL
)

# Leaflet Draw control
DRAW_CONTROL_PATTERN = re.compile(
    r"""(?:L\.Control\.Draw|new\s+L\.Draw\.Control|leaflet-draw|<EditControl)\s*[\(\{]?""",
    re.IGNORECASE
)

# Geocoder control
GEOCODER_PATTERN = re.compile(
    r"""(?:L\.Control\.Geocoder|MapboxGeocoder|mapbox-gl-geocoder|leaflet-geosearch)\s*[\(\{]?""",
    re.IGNORECASE
)

# Popup patterns
BIND_POPUP_PATTERN = re.compile(
    r"""\.bindPopup\s*\(\s*(['"`]|function|<|`|\()""",
    re.DOTALL
)

STANDALONE_POPUP_PATTERN = re.compile(
    r"""(?:L\.popup|new\s+mapboxgl\.Popup|new\s+maplibregl\.Popup)\s*\(""",
    re.DOTALL
)

REACT_POPUP_PATTERN = re.compile(
    r'<Popup\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Tooltip patterns
BIND_TOOLTIP_PATTERN = re.compile(
    r"""\.bindTooltip\s*\(""",
    re.DOTALL
)

REACT_TOOLTIP_PATTERN = re.compile(
    r'<Tooltip\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Control options
POSITION_PATTERN = re.compile(r'position\s*[:=]\s*[\'"]')
CLOSE_BUTTON_PATTERN = re.compile(r'closeButton\s*[:=]')
MAX_WIDTH_PATTERN = re.compile(r'maxWidth\s*[:=]')
PERMANENT_PATTERN = re.compile(r'permanent\s*[:=]\s*true')


class LeafletControlExtractor:
    """Extracts controls, popups, and tooltips from Leaflet/Mapbox code."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract controls, popups, and tooltips.

        Returns:
            Dict with 'controls', 'popups', 'tooltips'.
        """
        controls = []
        popups = []
        tooltips = []

        # ── Leaflet Controls ─────────────────────────────────────
        for ctrl_type, pattern in LEAFLET_CONTROL_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                context_after = content[match.start():match.start() + 300]
                controls.append(LeafletControlInfo(
                    name=f"L.control.{ctrl_type}",
                    line_number=line,
                    control_type=ctrl_type,
                    has_position=bool(POSITION_PATTERN.search(context_after)),
                    has_options=True,
                ))

        # ── Mapbox GL Controls ───────────────────────────────────
        for ctrl_type, pattern in MAPBOX_CONTROL_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                controls.append(LeafletControlInfo(
                    name=f"mapboxgl.{ctrl_type.title()}Control",
                    line_number=line,
                    control_type=ctrl_type,
                    has_position=bool(re.search(r'position\s*[:=]', content[match.start():match.start() + 200])),
                ))

        # ── MapLibre GL Controls ─────────────────────────────────
        for ctrl_type, pattern in MAPLIBRE_CONTROL_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                controls.append(LeafletControlInfo(
                    name=f"maplibregl.{ctrl_type.title()}Control",
                    line_number=line,
                    control_type=ctrl_type,
                ))

        # ── React-Leaflet Controls ───────────────────────────────
        for ctrl_type, pattern in REACT_CONTROL_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                controls.append(LeafletControlInfo(
                    name=f"{ctrl_type.title()}Control",
                    line_number=line,
                    control_type=ctrl_type,
                ))

        # ── Custom Controls ──────────────────────────────────────
        for match in CUSTOM_CONTROL_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            controls.append(LeafletControlInfo(
                name="CustomControl",
                line_number=line,
                control_type='custom',
                is_custom=True,
            ))

        # ── Draw Controls ────────────────────────────────────────
        for match in DRAW_CONTROL_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            controls.append(LeafletControlInfo(
                name="DrawControl",
                line_number=line,
                control_type='draw',
            ))

        # ── Geocoder Controls ────────────────────────────────────
        for match in GEOCODER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            controls.append(LeafletControlInfo(
                name="GeocoderControl",
                line_number=line,
                control_type='geocoder',
            ))

        # ── Bound Popups ─────────────────────────────────────────
        for match in BIND_POPUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 500]
            popups.append(LeafletPopupInfo(
                name="bindPopup",
                line_number=line,
                popup_type='bind',
                has_content=True,
                is_custom=bool(re.search(r'(?:function|=>|`)', context_after[:100])),
                has_close_button=bool(CLOSE_BUTTON_PATTERN.search(context_after)),
                has_max_width=bool(MAX_WIDTH_PATTERN.search(context_after)),
            ))

        # ── Standalone Popups ────────────────────────────────────
        for match in STANDALONE_POPUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 300]
            popups.append(LeafletPopupInfo(
                name="Popup",
                line_number=line,
                popup_type='standalone',
                has_content=bool(re.search(r'\.setContent\s*\(', context_after)),
                has_close_button=bool(CLOSE_BUTTON_PATTERN.search(context_after)),
                has_max_width=bool(MAX_WIDTH_PATTERN.search(context_after)),
            ))

        # ── React-Leaflet Popups ─────────────────────────────────
        for match in REACT_POPUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            # Check for content between tags
            close_tag = content.find('</Popup>', match.end())
            has_children = close_tag > match.end() + 1 if close_tag > 0 else False
            popups.append(LeafletPopupInfo(
                name="Popup",
                line_number=line,
                popup_type='jsx',
                has_content=has_children or bool(props.strip()),
                is_custom=has_children,
                has_close_button=bool(re.search(r'closeButton\s*=', props)),
                has_max_width=bool(re.search(r'maxWidth\s*=', props)),
            ))

        # ── Bound Tooltips ───────────────────────────────────────
        for match in BIND_TOOLTIP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 300]
            tooltips.append(LeafletTooltipInfo(
                name="bindTooltip",
                line_number=line,
                tooltip_type='bind',
                has_content=True,
                is_permanent=bool(PERMANENT_PATTERN.search(context_after)),
            ))

        # ── React-Leaflet Tooltips ───────────────────────────────
        for match in REACT_TOOLTIP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            close_tag = content.find('</Tooltip>', match.end())
            has_children = close_tag > match.end() + 1 if close_tag > 0 else False
            tooltips.append(LeafletTooltipInfo(
                name="Tooltip",
                line_number=line,
                tooltip_type='jsx',
                has_content=has_children or bool(props.strip()),
                is_permanent=bool(re.search(r'permanent\s*=', props)),
                is_custom=has_children,
            ))

        return {
            'controls': controls,
            'popups': popups,
            'tooltips': tooltips,
        }
