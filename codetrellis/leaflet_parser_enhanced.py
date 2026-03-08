"""
Enhanced Leaflet / Mapbox GL JS mapping framework parser for CodeTrellis.

Parses JavaScript/TypeScript/JSX/TSX files containing Leaflet, Mapbox GL JS,
MapLibre GL JS, React-Leaflet, or Vue-Leaflet code. Delegates to 5 specialized
extractors for comprehensive mapping framework analysis.

Supports:
- Leaflet v0.7.x → v1.9+ (full API surface)
- Mapbox GL JS v0.x → v3+ (full API surface)
- MapLibre GL JS (open-source Mapbox GL fork)
- React-Leaflet v1 → v4 (hooks + components)
- Vue-Leaflet / Angular-Leaflet wrappers
- 30+ Leaflet plugins (Draw, MarkerCluster, Heat, Routing, etc.)
- deck.gl, Turf.js, topojson, proj4 integrations

AST via regex + optional tree-sitter-javascript / tsserver LSP.
v4.75: Full Leaflet/Mapbox support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from codetrellis.extractors.leaflet import (
    LeafletMapExtractor,
    LeafletLayerExtractor,
    LeafletControlExtractor,
    LeafletInteractionExtractor,
    LeafletAPIExtractor,
    LeafletMapInfo,
    LeafletTileLayerInfo,
    LeafletMarkerInfo,
    LeafletShapeInfo,
    LeafletGeoJSONInfo,
    LeafletLayerGroupInfo,
    LeafletSourceInfo,
    LeafletControlInfo,
    LeafletPopupInfo,
    LeafletTooltipInfo,
    LeafletEventInfo,
    LeafletDrawInfo,
    LeafletAnimationInfo,
    LeafletImportInfo,
    LeafletIntegrationInfo,
    LeafletTypeInfo,
    LeafletPluginInfo,
)


@dataclass
class LeafletParseResult:
    """Complete result of parsing a Leaflet/Mapbox file."""
    file_path: str = ""
    file_type: str = ""         # 'js', 'jsx', 'ts', 'tsx', 'vue', 'html'

    # Map instances and tile layers (from map_extractor)
    maps: List[LeafletMapInfo] = field(default_factory=list)
    tile_layers: List[LeafletTileLayerInfo] = field(default_factory=list)

    # Layers and geometries (from layer_extractor)
    markers: List[LeafletMarkerInfo] = field(default_factory=list)
    shapes: List[LeafletShapeInfo] = field(default_factory=list)
    geojson: List[LeafletGeoJSONInfo] = field(default_factory=list)
    layer_groups: List[LeafletLayerGroupInfo] = field(default_factory=list)
    sources: List[LeafletSourceInfo] = field(default_factory=list)

    # Controls, popups, tooltips (from control_extractor)
    controls: List[LeafletControlInfo] = field(default_factory=list)
    popups: List[LeafletPopupInfo] = field(default_factory=list)
    tooltips: List[LeafletTooltipInfo] = field(default_factory=list)

    # Interactions (from interaction_extractor)
    events: List[LeafletEventInfo] = field(default_factory=list)
    drawings: List[LeafletDrawInfo] = field(default_factory=list)
    animations: List[LeafletAnimationInfo] = field(default_factory=list)

    # API (from api_extractor)
    imports: List[LeafletImportInfo] = field(default_factory=list)
    integrations: List[LeafletIntegrationInfo] = field(default_factory=list)
    types: List[LeafletTypeInfo] = field(default_factory=list)
    plugins: List[LeafletPluginInfo] = field(default_factory=list)

    # Detected metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    leaflet_version: str = ""
    mapbox_version: str = ""
    has_typescript: bool = False
    has_react_leaflet: bool = False
    has_mapbox: bool = False
    has_maplibre: bool = False
    has_clustering: bool = False
    has_drawing: bool = False
    has_routing: bool = False
    has_geocoding: bool = False


class EnhancedLeafletParser:
    """
    Full-featured Leaflet/Mapbox mapping framework parser.

    Coordinates 5 specialized extractors to provide comprehensive
    mapping framework analysis. Follows the Recharts parser architecture.
    """

    # Framework/library detection patterns
    FRAMEWORK_PATTERNS = {
        'leaflet': re.compile(r"""(?:from\s+['"]leaflet['"]|require\s*\(\s*['"]leaflet['"]|import\s+L\s+from|L\.map\s*\(|L\.tileLayer|L\.marker|L\.popup|L\.geoJSON)"""),
        'mapbox-gl': re.compile(r"""(?:from\s+['"]mapbox-gl['"]|require\s*\(\s*['"]mapbox-gl['"]|mapboxgl\.Map|mapboxgl\.Marker|mapboxgl\.Popup|mapboxAccessToken)"""),
        'maplibre-gl': re.compile(r"""(?:from\s+['"]maplibre-gl['"]|require\s*\(\s*['"]maplibre-gl['"]|maplibregl\.Map|maplibregl\.Marker)"""),
        'react-leaflet': re.compile(r"""(?:from\s+['"]react-leaflet['"]|<MapContainer|<TileLayer|useMap\s*\(|useMapEvent)"""),
        'vue-leaflet': re.compile(r"""(?:from\s+['"](?:vue2-leaflet|@vue-leaflet)['"]|<l-map|<LMap)"""),
        'react-map-gl': re.compile(r"""(?:from\s+['"]react-map-gl['"]|<Map\s|<Source\s|<Layer\s)"""),
        'deck.gl': re.compile(r"""(?:from\s+['"](?:deck\.gl|@deck\.gl)['"]|new\s+Deck\s*\(|DeckGL)"""),
        'leaflet-draw': re.compile(r"""(?:from\s+['"]leaflet-draw['"]|L\.Draw|L\.Control\.Draw|<EditControl)"""),
        'leaflet-markercluster': re.compile(r"""(?:leaflet\.markercluster|leaflet-markercluster|L\.markerClusterGroup|MarkerClusterGroup)"""),
        'leaflet-heat': re.compile(r"""(?:leaflet\.heat|leaflet-heat|L\.heatLayer|HeatmapLayer)"""),
        'leaflet-routing': re.compile(r"""(?:leaflet-routing-machine|L\.Routing)"""),
        'mapbox-draw': re.compile(r"""(?:@mapbox/mapbox-gl-draw|MapboxDraw|mapbox-gl-draw)"""),
        'mapbox-geocoder': re.compile(r"""(?:@mapbox/mapbox-gl-geocoder|MapboxGeocoder)"""),
        'turf': re.compile(r"""(?:from\s+['"]@turf/|require\s*\(\s*['"]@turf/)"""),
        'topojson': re.compile(r"""(?:from\s+['"]topojson|require\s*\(\s*['"]topojson)"""),
        'proj4': re.compile(r"""(?:from\s+['"]proj4['"]|require\s*\(\s*['"]proj4['"])"""),
        'supercluster': re.compile(r"""(?:from\s+['"]supercluster['"]|require\s*\(\s*['"]supercluster['"])"""),
        'leaflet-geoman': re.compile(r"""(?:@geoman-io|leaflet-geoman|pm\.enable|pm\.addControls)"""),
        'leaflet-geosearch': re.compile(r"""(?:leaflet-geosearch|GeoSearchControl)"""),
    }

    def __init__(self):
        """Initialize all 5 extractors."""
        self.map_extractor = LeafletMapExtractor()
        self.layer_extractor = LeafletLayerExtractor()
        self.control_extractor = LeafletControlExtractor()
        self.interaction_extractor = LeafletInteractionExtractor()
        self.api_extractor = LeafletAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> LeafletParseResult:
        """
        Parse a file for Leaflet/Mapbox mapping constructs.

        Args:
            content: Source code content
            file_path: Path to the source file

        Returns:
            LeafletParseResult with all extracted data
        """
        result = LeafletParseResult()
        result.file_path = file_path

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = 'tsx'
        elif file_path.endswith('.ts'):
            result.file_type = 'ts'
        elif file_path.endswith('.jsx'):
            result.file_type = 'jsx'
        elif file_path.endswith('.vue'):
            result.file_type = 'vue'
        elif file_path.endswith('.html'):
            result.file_type = 'html'
        else:
            result.file_type = 'js'

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract map instances and tile layers ─────────────────
        map_result = self.map_extractor.extract(content, file_path)
        result.maps = map_result.get('maps', [])
        result.tile_layers = map_result.get('tile_layers', [])

        # ── Extract layers and geometries ─────────────────────────
        layer_result = self.layer_extractor.extract(content, file_path)
        result.markers = layer_result.get('markers', [])
        result.shapes = layer_result.get('shapes', [])
        result.geojson = layer_result.get('geojson', [])
        result.layer_groups = layer_result.get('layer_groups', [])
        result.sources = layer_result.get('sources', [])

        # ── Extract controls, popups, tooltips ────────────────────
        control_result = self.control_extractor.extract(content, file_path)
        result.controls = control_result.get('controls', [])
        result.popups = control_result.get('popups', [])
        result.tooltips = control_result.get('tooltips', [])

        # ── Extract interactions ──────────────────────────────────
        interaction_result = self.interaction_extractor.extract(content, file_path)
        result.events = interaction_result.get('events', [])
        result.drawings = interaction_result.get('drawings', [])
        result.animations = interaction_result.get('animations', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])
        result.plugins = api_result.get('plugins', [])

        # Framework info from API extractor
        fw_info = api_result.get('framework_info', {})
        result.has_typescript = fw_info.get('has_typescript', False)
        result.has_react_leaflet = fw_info.get('has_react_leaflet', False)
        result.has_mapbox = fw_info.get('has_mapbox', False)
        result.has_maplibre = fw_info.get('has_maplibre', False)
        result.leaflet_version = fw_info.get('leaflet_version', '')
        result.mapbox_version = fw_info.get('mapbox_version', '')
        result.detected_features = fw_info.get('features', [])

        # Derive boolean features from detected data
        result.has_clustering = bool(result.plugins and any(p.plugin_type == 'clustering' for p in result.plugins))
        result.has_drawing = bool(result.drawings)
        result.has_routing = 'routing' in result.detected_features
        result.has_geocoding = 'geocoding' in result.detected_features

        # Add map-type features to detected_features
        map_types = set(m.map_type for m in result.maps)
        for mt in map_types:
            if mt and f'map_{mt}' not in result.detected_features:
                result.detected_features.append(f'map_{mt}')

        # Add layer-type features
        if result.markers:
            if 'markers' not in result.detected_features:
                result.detected_features.append('markers')
        if result.geojson:
            if 'geojson' not in result.detected_features:
                result.detected_features.append('geojson')
        if result.shapes:
            if 'shapes' not in result.detected_features:
                result.detected_features.append('shapes')
        if result.sources:
            if 'mapbox_sources' not in result.detected_features:
                result.detected_features.append('mapbox_sources')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Leaflet/Mapbox ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_leaflet_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Leaflet/Mapbox code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains mapping framework code
        """
        # Check for Leaflet imports
        if re.search(r"from\s+['\"]leaflet['\"]", content):
            return True
        if re.search(r"from\s+['\"]leaflet(?:/dist)?['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]leaflet(?:/dist)?['\"]\s*\)", content):
            return True

        # Check for Mapbox GL imports
        if re.search(r"from\s+['\"]mapbox-gl['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]mapbox-gl['\"]\s*\)", content):
            return True

        # Check for MapLibre GL imports
        if re.search(r"from\s+['\"]maplibre-gl['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]maplibre-gl['\"]\s*\)", content):
            return True

        # Check for React-Leaflet imports
        if re.search(r"from\s+['\"]react-leaflet['\"]", content):
            return True

        # Check for React-Map-GL imports
        if re.search(r"from\s+['\"]react-map-gl['\"]", content):
            return True

        # Check for Vue-Leaflet imports
        if re.search(r"from\s+['\"](?:vue2-leaflet|@vue-leaflet)['\"/]", content):
            return True

        # Check for L.map() initialization
        if re.search(r"L\.map\s*\(", content):
            return True

        # Check for mapboxgl.Map
        if re.search(r"new\s+mapboxgl\.Map\s*\(", content):
            return True

        # Check for maplibregl.Map
        if re.search(r"new\s+maplibregl\.Map\s*\(", content):
            return True

        # Check for React-Leaflet JSX components
        if re.search(r'<MapContainer\b', content):
            return True

        # Check for Leaflet API usage patterns
        if re.search(r'L\.(?:tileLayer|marker|popup|tooltip|geoJSON|layerGroup|featureGroup|control)\s*\(', content):
            return True

        # Check for mapbox API usage
        if re.search(r'mapboxgl\.(?:Marker|Popup|NavigationControl|GeolocateControl)\s*\(', content):
            return True

        # Check for deck.gl with map
        if re.search(r"from\s+['\"](?:deck\.gl|@deck\.gl)", content):
            if re.search(r'(?:MapView|MapController|DeckGL)', content):
                return True

        # Check for Leaflet CDN in HTML
        if re.search(r'leaflet(?:\.min)?\.(?:js|css)', content):
            if re.search(r'<script|<link', content):
                return True

        # Check for Mapbox CDN in HTML
        if re.search(r'mapbox-gl(?:\.min)?\.(?:js|css)', content):
            if re.search(r'<script|<link', content):
                return True

        # Check for dynamic import
        if re.search(r"import\s*\(\s*['\"](?:leaflet|mapbox-gl|maplibre-gl|react-leaflet)['\"]", content):
            return True

        return False
