"""
Leaflet/Mapbox layer and geometry extractor.

Extracts:
- L.marker / mapboxgl.Marker / <Marker> instances
- L.polygon, L.polyline, L.circle, L.rectangle shapes
- L.geoJSON / GeoJSON sources
- L.layerGroup / L.featureGroup / LayerGroup
- Mapbox GL sources (geojson, vector, raster, image, video)
- Mapbox GL layers (fill, line, circle, symbol, heatmap, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LeafletMarkerInfo:
    """Represents a detected marker."""
    name: str = ""
    line_number: int = 0
    marker_type: str = ""       # 'default', 'custom', 'div_icon', 'circle_marker'
    has_popup: bool = False
    has_tooltip: bool = False
    has_icon: bool = False
    has_draggable: bool = False
    is_clustered: bool = False


@dataclass
class LeafletShapeInfo:
    """Represents a detected shape/geometry."""
    name: str = ""
    line_number: int = 0
    shape_type: str = ""        # 'polygon', 'polyline', 'circle', 'rectangle', 'circle_marker'
    has_style: bool = False
    has_popup: bool = False
    has_events: bool = False
    is_editable: bool = False


@dataclass
class LeafletGeoJSONInfo:
    """Represents a detected GeoJSON layer or source."""
    name: str = ""
    line_number: int = 0
    source_type: str = ""       # 'inline', 'url', 'variable', 'fetch'
    has_style: bool = False
    has_onEachFeature: bool = False
    has_pointToLayer: bool = False
    has_filter: bool = False
    has_clustering: bool = False


@dataclass
class LeafletLayerGroupInfo:
    """Represents a detected layer group."""
    name: str = ""
    line_number: int = 0
    group_type: str = ""        # 'layer_group', 'feature_group', 'pane'
    is_overlay: bool = False
    has_bounds: bool = False


@dataclass
class LeafletSourceInfo:
    """Represents a Mapbox GL / MapLibre source or layer definition."""
    name: str = ""
    line_number: int = 0
    source_type: str = ""       # 'geojson', 'vector', 'raster', 'image', 'video', 'canvas'
    layer_type: str = ""        # 'fill', 'line', 'circle', 'symbol', 'heatmap', 'fill-extrusion', 'raster', 'hillshade', 'background'
    has_paint: bool = False
    has_layout: bool = False
    has_filter: bool = False
    has_minzoom: bool = False
    has_maxzoom: bool = False


# ── Regex Patterns ────────────────────────────────────────────────────

# Leaflet marker patterns
LEAFLET_MARKER_PATTERN = re.compile(
    r"""L\.marker\s*\(\s*[\[\(]""",
    re.DOTALL
)

LEAFLET_CIRCLE_MARKER_PATTERN = re.compile(
    r"""L\.circleMarker\s*\(""",
    re.DOTALL
)

# Mapbox GL Marker
MAPBOX_MARKER_PATTERN = re.compile(
    r"""new\s+mapboxgl\.Marker\s*\(""",
    re.DOTALL
)

# MapLibre GL Marker
MAPLIBRE_MARKER_PATTERN = re.compile(
    r"""new\s+maplibregl\.Marker\s*\(""",
    re.DOTALL
)

# React-Leaflet Marker JSX
REACT_MARKER_PATTERN = re.compile(
    r'<Marker\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Shape patterns
SHAPE_PATTERNS = {
    'polygon': re.compile(r"""L\.polygon\s*\(""", re.DOTALL),
    'polyline': re.compile(r"""L\.polyline\s*\(""", re.DOTALL),
    'circle': re.compile(r"""L\.circle\s*\(""", re.DOTALL),
    'rectangle': re.compile(r"""L\.rectangle\s*\(""", re.DOTALL),
}

# React-Leaflet shape components
REACT_SHAPE_PATTERNS = {
    'polygon': re.compile(r'<Polygon\b([^>]*?)(?:/>|>)', re.DOTALL),
    'polyline': re.compile(r'<Polyline\b([^>]*?)(?:/>|>)', re.DOTALL),
    'circle': re.compile(r'<Circle\b(?!Marker)([^>]*?)(?:/>|>)', re.DOTALL),
    'rectangle': re.compile(r'<Rectangle\b([^>]*?)(?:/>|>)', re.DOTALL),
    'circle_marker': re.compile(r'<CircleMarker\b([^>]*?)(?:/>|>)', re.DOTALL),
}

# GeoJSON patterns
LEAFLET_GEOJSON_PATTERN = re.compile(
    r"""L\.geoJSON\s*\(""",
    re.DOTALL
)

REACT_GEOJSON_PATTERN = re.compile(
    r'<GeoJSON\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Layer group patterns
LAYER_GROUP_PATTERN = re.compile(r"""L\.layerGroup\s*\(""")
FEATURE_GROUP_PATTERN = re.compile(r"""L\.featureGroup\s*\(""")

# React-Leaflet groups
REACT_LAYER_GROUP_PATTERN = re.compile(r'<LayerGroup\b')
REACT_FEATURE_GROUP_PATTERN = re.compile(r'<FeatureGroup\b')
REACT_PANE_PATTERN = re.compile(r'<Pane\b')

# Mapbox GL addSource pattern
ADD_SOURCE_PATTERN = re.compile(
    r"""\.addSource\s*\(\s*['"]([\w-]+)['"]\s*,\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}""",
    re.DOTALL
)

# Mapbox GL addLayer pattern
ADD_LAYER_PATTERN = re.compile(
    r"""\.addLayer\s*\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}""",
    re.DOTALL
)

# Mapbox GL source type
SOURCE_TYPE_PATTERN = re.compile(r"""type\s*:\s*['"](\w+)['"]""")

# Marker cluster detection
CLUSTER_PATTERN = re.compile(
    r'(?:MarkerCluster|markerClusterGroup|L\.markerClusterGroup|supercluster|'
    r'cluster\s*:\s*true|clusterMaxZoom|clusterRadius)',
    re.IGNORECASE
)

# Popup/tooltip on markers
POPUP_BIND_PATTERN = re.compile(r'\.bindPopup\s*\(')
TOOLTIP_BIND_PATTERN = re.compile(r'\.bindTooltip\s*\(')

# Icon patterns
ICON_PATTERN = re.compile(r'(?:icon\s*[:=]|L\.icon\s*\(|L\.divIcon\s*\(|new\s+L\.Icon)')
DRAGGABLE_PATTERN = re.compile(r'draggable\s*[:=]\s*true')

# Style and interaction patterns
STYLE_PATTERN = re.compile(r'(?:style\s*[:=]|fillColor|strokeColor|weight\s*[:=]|opacity\s*[:=]|color\s*[:=])')
ON_EACH_FEATURE_PATTERN = re.compile(r'onEachFeature\s*[:=]')
POINT_TO_LAYER_PATTERN = re.compile(r'pointToLayer\s*[:=]')
FILTER_PATTERN = re.compile(r'filter\s*[:=]')
EDITABLE_PATTERN = re.compile(r'(?:editable|editing\.enable|pm\.enable|enableEdit)')

# Mapbox layer properties
PAINT_PATTERN = re.compile(r"paint\s*:")
LAYOUT_PATTERN = re.compile(r"layout\s*:")
MINZOOM_PATTERN = re.compile(r"minzoom\s*:")
MAXZOOM_PATTERN = re.compile(r"maxzoom\s*:")


class LeafletLayerExtractor:
    """Extracts markers, shapes, GeoJSON, layers, and sources from Leaflet/Mapbox code."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract layer information.

        Returns:
            Dict with 'markers', 'shapes', 'geojson', 'layer_groups', 'sources'.
        """
        markers = []
        shapes = []
        geojson_layers = []
        layer_groups = []
        sources = []

        has_cluster = bool(CLUSTER_PATTERN.search(content))

        # ── Leaflet Markers ──────────────────────────────────────
        for match in LEAFLET_MARKER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 500]
            markers.append(LeafletMarkerInfo(
                name="L.marker",
                line_number=line,
                marker_type='custom' if ICON_PATTERN.search(context_after) else 'default',
                has_popup=bool(POPUP_BIND_PATTERN.search(context_after)),
                has_tooltip=bool(TOOLTIP_BIND_PATTERN.search(context_after)),
                has_icon=bool(ICON_PATTERN.search(context_after)),
                has_draggable=bool(DRAGGABLE_PATTERN.search(context_after)),
                is_clustered=has_cluster,
            ))

        # ── Circle Markers ───────────────────────────────────────
        for match in LEAFLET_CIRCLE_MARKER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            markers.append(LeafletMarkerInfo(
                name="L.circleMarker",
                line_number=line,
                marker_type='circle_marker',
            ))

        # ── Mapbox GL Markers ────────────────────────────────────
        for match in MAPBOX_MARKER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 300]
            markers.append(LeafletMarkerInfo(
                name="mapboxgl.Marker",
                line_number=line,
                marker_type='mapbox',
                has_popup=bool(re.search(r'\.setPopup\s*\(', context_after)),
                has_draggable=bool(DRAGGABLE_PATTERN.search(context_after)),
            ))

        # ── MapLibre GL Markers ──────────────────────────────────
        for match in MAPLIBRE_MARKER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            markers.append(LeafletMarkerInfo(
                name="maplibregl.Marker",
                line_number=line,
                marker_type='maplibre',
            ))

        # ── React-Leaflet Marker ─────────────────────────────────
        for match in REACT_MARKER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            context_after = content[match.end():match.end() + 300]
            markers.append(LeafletMarkerInfo(
                name="Marker",
                line_number=line,
                marker_type='react-leaflet',
                has_popup=bool(re.search(r'<Popup\b', context_after)),
                has_tooltip=bool(re.search(r'<Tooltip\b', context_after)),
                has_icon=bool(re.search(r'icon\s*=', props)),
                has_draggable=bool(re.search(r'draggable\s*=', props)),
                is_clustered=has_cluster,
            ))

        # ── Leaflet Shapes ───────────────────────────────────────
        for shape_type, pattern in SHAPE_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                context_after = content[match.start():match.start() + 500]
                shapes.append(LeafletShapeInfo(
                    name=f"L.{shape_type}",
                    line_number=line,
                    shape_type=shape_type,
                    has_style=bool(STYLE_PATTERN.search(context_after)),
                    has_popup=bool(POPUP_BIND_PATTERN.search(context_after)),
                    has_events=bool(re.search(r'\.on\s*\(', context_after)),
                    is_editable=bool(EDITABLE_PATTERN.search(context_after)),
                ))

        # ── React-Leaflet Shapes ─────────────────────────────────
        for shape_type, pattern in REACT_SHAPE_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                props = match.group(1) or ""
                shapes.append(LeafletShapeInfo(
                    name=shape_type.replace('_', '').title(),
                    line_number=line,
                    shape_type=shape_type,
                    has_style=bool(re.search(r'(?:pathOptions|fillColor|color|weight)\s*=', props)),
                    has_popup=bool(re.search(r'<Popup\b', content[match.end():match.end() + 300])),
                    has_events=bool(re.search(r'(?:onClick|onMouseOver|eventHandlers)\s*=', props)),
                ))

        # ── Leaflet GeoJSON ──────────────────────────────────────
        for match in LEAFLET_GEOJSON_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 800]
            # Detect source type
            source_type = 'variable'
            if re.search(r'fetch\s*\(', content[max(0, match.start()-200):match.start()]):
                source_type = 'fetch'
            elif re.search(r'\.json\b', content[max(0, match.start()-200):match.start()]):
                source_type = 'url'

            geojson_layers.append(LeafletGeoJSONInfo(
                name="L.geoJSON",
                line_number=line,
                source_type=source_type,
                has_style=bool(STYLE_PATTERN.search(context_after)),
                has_onEachFeature=bool(ON_EACH_FEATURE_PATTERN.search(context_after)),
                has_pointToLayer=bool(POINT_TO_LAYER_PATTERN.search(context_after)),
                has_filter=bool(FILTER_PATTERN.search(context_after)),
                has_clustering=has_cluster,
            ))

        # ── React-Leaflet GeoJSON ────────────────────────────────
        for match in REACT_GEOJSON_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            geojson_layers.append(LeafletGeoJSONInfo(
                name="GeoJSON",
                line_number=line,
                source_type='variable',
                has_style=bool(re.search(r'(?:style|pathOptions)\s*=', props)),
                has_onEachFeature=bool(re.search(r'onEachFeature\s*=', props)),
                has_pointToLayer=bool(re.search(r'pointToLayer\s*=', props)),
                has_filter=bool(re.search(r'filter\s*=', props)),
            ))

        # ── Layer Groups ─────────────────────────────────────────
        for match in LAYER_GROUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            layer_groups.append(LeafletLayerGroupInfo(
                name="L.layerGroup",
                line_number=line,
                group_type='layer_group',
            ))

        for match in FEATURE_GROUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            context_after = content[match.start():match.start() + 300]
            layer_groups.append(LeafletLayerGroupInfo(
                name="L.featureGroup",
                line_number=line,
                group_type='feature_group',
                has_bounds=bool(re.search(r'\.getBounds\s*\(', context_after)),
            ))

        # ── React-Leaflet Groups ─────────────────────────────────
        for match in REACT_LAYER_GROUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            layer_groups.append(LeafletLayerGroupInfo(
                name="LayerGroup",
                line_number=line,
                group_type='layer_group',
            ))

        for match in REACT_FEATURE_GROUP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            layer_groups.append(LeafletLayerGroupInfo(
                name="FeatureGroup",
                line_number=line,
                group_type='feature_group',
            ))

        for match in REACT_PANE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            layer_groups.append(LeafletLayerGroupInfo(
                name="Pane",
                line_number=line,
                group_type='pane',
            ))

        # ── Mapbox GL Sources ────────────────────────────────────
        for match in ADD_SOURCE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            source_name = match.group(1)
            options = match.group(2) or ""
            type_match = SOURCE_TYPE_PATTERN.search(options)
            source_type = type_match.group(1) if type_match else 'unknown'
            sources.append(LeafletSourceInfo(
                name=source_name,
                line_number=line,
                source_type=source_type,
                has_filter=bool(FILTER_PATTERN.search(options)),
            ))

        # ── Mapbox GL Layers ─────────────────────────────────────
        for match in ADD_LAYER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            options = match.group(1) or ""
            type_match = SOURCE_TYPE_PATTERN.search(options)
            layer_type = type_match.group(1) if type_match else 'unknown'
            id_match = re.search(r"""id\s*:\s*['"]([\w-]+)['"]""", options)
            layer_id = id_match.group(1) if id_match else ''
            sources.append(LeafletSourceInfo(
                name=layer_id or f"layer_{line}",
                line_number=line,
                layer_type=layer_type,
                has_paint=bool(PAINT_PATTERN.search(options)),
                has_layout=bool(LAYOUT_PATTERN.search(options)),
                has_filter=bool(FILTER_PATTERN.search(options)),
                has_minzoom=bool(MINZOOM_PATTERN.search(options)),
                has_maxzoom=bool(MAXZOOM_PATTERN.search(options)),
            ))

        return {
            'markers': markers,
            'shapes': shapes,
            'geojson': geojson_layers,
            'layer_groups': layer_groups,
            'sources': sources,
        }
