"""
Leaflet/Mapbox map instance and tile layer extractor.

Extracts:
- L.map() / mapboxgl.Map / MapContainer (React-Leaflet) instances
- L.tileLayer() / mapboxgl tile sources / provider tiles
- Map view configuration (center, zoom, bounds)
- Map container elements and sizing
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LeafletMapInfo:
    """Represents a detected map instance."""
    name: str = ""
    line_number: int = 0
    map_type: str = ""          # 'leaflet', 'mapbox', 'maplibre', 'react-leaflet', 'vue-leaflet'
    has_center: bool = False
    has_zoom: bool = False
    has_bounds: bool = False
    has_max_bounds: bool = False
    has_crs: bool = False       # Custom CRS / projection
    container_id: str = ""
    children: List[str] = field(default_factory=list)


@dataclass
class LeafletTileLayerInfo:
    """Represents a detected tile layer."""
    name: str = ""
    line_number: int = 0
    provider: str = ""          # 'osm', 'mapbox', 'stamen', 'carto', 'custom'
    tile_type: str = ""         # 'raster', 'vector', 'wms', 'wmts'
    has_attribution: bool = False
    has_access_token: bool = False
    has_subdomains: bool = False
    url_template: str = ""


# ── Regex Patterns ────────────────────────────────────────────────────

# Leaflet L.map() pattern
LEAFLET_MAP_PATTERN = re.compile(
    r"""L\.map\s*\(\s*['"]([^'"]+)['"]\s*(?:,\s*\{([^}]*)\})?\s*\)""",
    re.DOTALL
)

# Mapbox GL Map pattern
MAPBOX_MAP_PATTERN = re.compile(
    r"""new\s+mapboxgl\.Map\s*\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*\)""",
    re.DOTALL
)

# MapLibre GL Map pattern
MAPLIBRE_MAP_PATTERN = re.compile(
    r"""new\s+maplibregl\.Map\s*\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*\)""",
    re.DOTALL
)

# React-Leaflet MapContainer JSX pattern
REACT_LEAFLET_MAP_PATTERN = re.compile(
    r'<MapContainer\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Vue-Leaflet LMap pattern
VUE_LEAFLET_MAP_PATTERN = re.compile(
    r'<(?:l-map|LMap)\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# Leaflet tile layer pattern
TILE_LAYER_PATTERN = re.compile(
    r"""L\.tileLayer\s*\(\s*['"]([^'"]+)['"]""",
    re.DOTALL
)

# Mapbox style URL pattern
MAPBOX_STYLE_PATTERN = re.compile(
    r"""style\s*:\s*['"]mapbox://styles/([^'"]+)['"]"""
)

# React-Leaflet TileLayer JSX
REACT_TILE_LAYER_PATTERN = re.compile(
    r'<TileLayer\b([^>]*?)(?:/>|>)',
    re.DOTALL
)

# WMS tile layer
WMS_TILE_LAYER_PATTERN = re.compile(
    r"""L\.tileLayer\.wms\s*\(\s*['"]([^'"]+)['"]""",
    re.DOTALL
)

# Map options patterns
CENTER_PATTERN = re.compile(r'center\s*[:=]\s*[\[{(]')
ZOOM_PATTERN = re.compile(r'zoom\s*[:=]\s*\d')
BOUNDS_PATTERN = re.compile(r'(?:bounds|fitBounds|maxBounds)\s*[:=(]')
MAX_BOUNDS_PATTERN = re.compile(r'maxBounds\s*[:=]')
CRS_PATTERN = re.compile(r'(?:crs|CRS)\s*[:=]')

# Provider detection from URL
PROVIDER_PATTERNS = {
    'osm': re.compile(r'tile\.openstreetmap\.org|osm\.org'),
    'mapbox': re.compile(r'api\.mapbox\.com|mapbox://'),
    'stamen': re.compile(r'stamen-tiles|stadia.*stamen'),
    'carto': re.compile(r'basemaps\.cartocdn\.com|cartodb'),
    'thunderforest': re.compile(r'thunderforest\.com'),
    'esri': re.compile(r'arcgisonline\.com|arcgis'),
    'here': re.compile(r'maps\.hereapi\.com|here\.com'),
    'maptiler': re.compile(r'maptiler\.com'),
    'google': re.compile(r'mt[0-9]\.google\.com|googleapis.*maps'),
}

# Child component detection in React-Leaflet
CHILD_PATTERN = re.compile(
    r'<(TileLayer|Marker|Popup|Tooltip|Circle|CircleMarker|Polygon|'
    r'Polyline|Rectangle|GeoJSON|LayerGroup|FeatureGroup|'
    r'LayersControl|ZoomControl|ScaleControl|AttributionControl|'
    r'ImageOverlay|VideoOverlay|SVGOverlay|Pane|WMSTileLayer)\b'
)


class LeafletMapExtractor:
    """Extracts map instances and tile layers from Leaflet/Mapbox code."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract map instances and tile layers.

        Returns:
            Dict with 'maps' and 'tile_layers' lists.
        """
        maps = []
        tile_layers = []

        # ── Leaflet L.map() ──────────────────────────────────────
        for match in LEAFLET_MAP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            container_id = match.group(1)
            options = match.group(2) or ""
            maps.append(LeafletMapInfo(
                name=f"L.map('{container_id}')",
                line_number=line,
                map_type='leaflet',
                has_center=bool(CENTER_PATTERN.search(options)),
                has_zoom=bool(ZOOM_PATTERN.search(options)),
                has_bounds=bool(BOUNDS_PATTERN.search(options)),
                has_max_bounds=bool(MAX_BOUNDS_PATTERN.search(options)),
                has_crs=bool(CRS_PATTERN.search(options)),
                container_id=container_id,
            ))

        # ── Mapbox GL Map ────────────────────────────────────────
        for match in MAPBOX_MAP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            options = match.group(1) or ""
            container_match = re.search(r"container\s*:\s*['\"]([^'\"]+)['\"]", options)
            container_id = container_match.group(1) if container_match else ""
            maps.append(LeafletMapInfo(
                name=f"mapboxgl.Map",
                line_number=line,
                map_type='mapbox',
                has_center=bool(CENTER_PATTERN.search(options)),
                has_zoom=bool(ZOOM_PATTERN.search(options)),
                has_bounds=bool(BOUNDS_PATTERN.search(options)),
                has_max_bounds=bool(MAX_BOUNDS_PATTERN.search(options)),
                container_id=container_id,
            ))

        # ── MapLibre GL Map ──────────────────────────────────────
        for match in MAPLIBRE_MAP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            options = match.group(1) or ""
            container_match = re.search(r"container\s*:\s*['\"]([^'\"]+)['\"]", options)
            container_id = container_match.group(1) if container_match else ""
            maps.append(LeafletMapInfo(
                name=f"maplibregl.Map",
                line_number=line,
                map_type='maplibre',
                has_center=bool(CENTER_PATTERN.search(options)),
                has_zoom=bool(ZOOM_PATTERN.search(options)),
                has_bounds=bool(BOUNDS_PATTERN.search(options)),
                has_max_bounds=bool(MAX_BOUNDS_PATTERN.search(options)),
                container_id=container_id,
            ))

        # ── React-Leaflet MapContainer ───────────────────────────
        for match in REACT_LEAFLET_MAP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            # Detect children
            children = []
            region_after = content[match.end():match.end() + 2000]
            for child_match in CHILD_PATTERN.finditer(region_after):
                child_name = child_match.group(1)
                if child_name not in children:
                    children.append(child_name)
            maps.append(LeafletMapInfo(
                name="MapContainer",
                line_number=line,
                map_type='react-leaflet',
                has_center=bool(re.search(r'center\s*[={]', props)),
                has_zoom=bool(re.search(r'zoom\s*[={]', props)),
                has_bounds=bool(re.search(r'bounds\s*[={]', props)),
                has_max_bounds=bool(re.search(r'maxBounds\s*[={]', props)),
                has_crs=bool(re.search(r'crs\s*[={]', props)),
                children=children[:15],
            ))

        # ── Vue-Leaflet LMap ─────────────────────────────────────
        for match in VUE_LEAFLET_MAP_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            maps.append(LeafletMapInfo(
                name="LMap",
                line_number=line,
                map_type='vue-leaflet',
                has_center=bool(re.search(r':?center\s*=', props)),
                has_zoom=bool(re.search(r':?zoom\s*=', props)),
            ))

        # ── Tile Layers: L.tileLayer() ───────────────────────────
        for match in TILE_LAYER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            url = match.group(1)
            provider = self._detect_provider(url)
            context_after = content[match.start():match.start() + 500]
            tile_layers.append(LeafletTileLayerInfo(
                name="L.tileLayer",
                line_number=line,
                provider=provider,
                tile_type='raster',
                has_attribution=bool(re.search(r'attribution\s*:', context_after)),
                has_access_token=bool(re.search(r'(?:accessToken|access_token|apiKey|api_key)\s*:', context_after)),
                has_subdomains=bool(re.search(r'subdomains\s*:', context_after)),
                url_template=url[:100],
            ))

        # ── WMS Tile Layers ──────────────────────────────────────
        for match in WMS_TILE_LAYER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            url = match.group(1)
            tile_layers.append(LeafletTileLayerInfo(
                name="L.tileLayer.wms",
                line_number=line,
                provider='wms',
                tile_type='wms',
                url_template=url[:100],
            ))

        # ── React-Leaflet TileLayer JSX ──────────────────────────
        for match in REACT_TILE_LAYER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            props = match.group(1) or ""
            url_match = re.search(r'url\s*=\s*[{"\']([^"\'{}]+)', props)
            url = url_match.group(1) if url_match else ""
            provider = self._detect_provider(url) if url else 'unknown'
            tile_layers.append(LeafletTileLayerInfo(
                name="TileLayer",
                line_number=line,
                provider=provider,
                tile_type='raster',
                has_attribution=bool(re.search(r'attribution\s*=', props)),
                url_template=url[:100],
            ))

        # ── Mapbox style sources ─────────────────────────────────
        for match in MAPBOX_STYLE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            style = match.group(1)
            tile_layers.append(LeafletTileLayerInfo(
                name="mapbox.style",
                line_number=line,
                provider='mapbox',
                tile_type='vector',
                has_access_token=True,
                url_template=f"mapbox://styles/{style}",
            ))

        return {
            'maps': maps,
            'tile_layers': tile_layers,
        }

    def _detect_provider(self, url: str) -> str:
        """Detect tile provider from URL template."""
        for provider, pattern in PROVIDER_PATTERNS.items():
            if pattern.search(url):
                return provider
        return 'custom'
