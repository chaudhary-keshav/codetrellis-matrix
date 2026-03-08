"""
Leaflet/Mapbox API, import, integration, TypeScript type, and plugin extractor.

Extracts:
- Import statements (leaflet, mapbox-gl, react-leaflet, maplibre-gl, etc.)
- Ecosystem integrations (D3, Turf.js, plugins, etc.)
- TypeScript types (LatLng, Map, Marker, etc.)
- Leaflet plugins and extensions
- Framework info (version, features, modes)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LeafletImportInfo:
    """Represents a detected import statement."""
    name: str = ""
    line_number: int = 0
    import_type: str = ""       # 'module_default', 'module_named', 'module_namespace', 'require', 'dynamic', 'css'
    package: str = ""           # 'leaflet', 'mapbox-gl', 'react-leaflet', 'maplibre-gl', etc.
    symbols: List[str] = field(default_factory=list)
    is_plugin: bool = False


@dataclass
class LeafletIntegrationInfo:
    """Represents a detected ecosystem integration."""
    name: str = ""
    line_number: int = 0
    integration_type: str = ""  # 'geospatial', 'ui', 'data', 'routing', 'geocoding', 'visualization'
    library: str = ""


@dataclass
class LeafletTypeInfo:
    """Represents a detected TypeScript type usage."""
    name: str = ""
    line_number: int = 0
    type_source: str = ""       # 'leaflet', 'mapbox-gl', 'react-leaflet', 'maplibre-gl', 'geojson'
    type_category: str = ""     # 'map', 'layer', 'geometry', 'event', 'control', 'options'


@dataclass
class LeafletPluginInfo:
    """Represents a detected Leaflet plugin."""
    name: str = ""
    line_number: int = 0
    plugin_type: str = ""       # 'marker', 'layer', 'control', 'draw', 'routing', 'geocoding', 'heatmap', 'clustering', 'tile'
    package: str = ""


# ── Regex Patterns ────────────────────────────────────────────────────

# Import patterns for all mapping libraries
IMPORT_PATTERNS = [
    # ES module default import
    re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]\s*;?"""),
    # ES module named import
    re.compile(r"""import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]\s*;?"""),
    # ES module namespace import
    re.compile(r"""import\s+\*\s+as\s+(\w+)\s+from\s+['"]([^'"]+)['"]\s*;?"""),
    # ES module default + named import (import X, { Y, Z } from '...')
    re.compile(r"""import\s+\w+\s*,\s*\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]\s*;?"""),
    # CommonJS require
    re.compile(r"""(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    # Dynamic import
    re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    # Bare/side-effect import (import 'package')
    re.compile(r"""import\s+['"]([^'"]+)['"]\s*;?"""),
    # CSS import (leaflet/dist/leaflet.css)
    re.compile(r"""import\s+['"]([^'"]*leaflet[^'"]*\.css)['"]\s*;?"""),
    re.compile(r"""import\s+['"]([^'"]*mapbox[^'"]*\.css)['"]\s*;?"""),
    re.compile(r"""import\s+['"]([^'"]*maplibre[^'"]*\.css)['"]\s*;?"""),
]

# Mapping-related packages
MAPPING_PACKAGES = {
    'leaflet': 'leaflet',
    'mapbox-gl': 'mapbox-gl',
    'maplibre-gl': 'maplibre-gl',
    'react-leaflet': 'react-leaflet',
    '@react-leaflet/core': 'react-leaflet',
    'vue2-leaflet': 'vue-leaflet',
    '@vue-leaflet/vue-leaflet': 'vue-leaflet',
    'ngx-leaflet': 'angular-leaflet',
    'react-map-gl': 'react-map-gl',
    'svelte-maplibre': 'svelte-maplibre',
    'deck.gl': 'deck.gl',
    '@deck.gl/core': 'deck.gl',
    '@deck.gl/react': 'deck.gl',
    '@deck.gl/layers': 'deck.gl',
    '@deck.gl/geo-layers': 'deck.gl',
    'leaflet-draw': 'leaflet-draw',
    'leaflet.markercluster': 'leaflet-markercluster',
    'leaflet-markercluster': 'leaflet-markercluster',
    'leaflet.heat': 'leaflet-heat',
    'leaflet-routing-machine': 'leaflet-routing',
    'leaflet-control-geocoder': 'leaflet-geocoder',
    'leaflet-geosearch': 'leaflet-geosearch',
    '@geoman-io/leaflet-geoman-free': 'leaflet-geoman',
    'leaflet-realtime': 'leaflet-realtime',
    'leaflet-image': 'leaflet-image',
    'leaflet-fullscreen': 'leaflet-fullscreen',
    'leaflet-minimap': 'leaflet-minimap',
    'leaflet-sidebar': 'leaflet-sidebar',
    'leaflet-easybutton': 'leaflet-easybutton',
    'leaflet-omnivore': 'leaflet-omnivore',
    '@mapbox/mapbox-gl-draw': 'mapbox-draw',
    '@mapbox/mapbox-gl-geocoder': 'mapbox-geocoder',
    '@mapbox/mapbox-gl-directions': 'mapbox-directions',
    '@mapbox/mapbox-sdk': 'mapbox-sdk',
    'mapbox-gl-draw': 'mapbox-draw',
    '@turf/turf': 'turf',
    '@turf/helpers': 'turf',
    '@turf/boolean-point-in-polygon': 'turf',
    '@turf/distance': 'turf',
    '@turf/buffer': 'turf',
    '@turf/area': 'turf',
    '@turf/centroid': 'turf',
    '@turf/bbox': 'turf',
    'topojson-client': 'topojson',
    'proj4': 'proj4',
    'proj4leaflet': 'proj4leaflet',
    'geojson': 'geojson',
    'wellknown': 'wellknown',
    'pbf': 'pbf',
    '@mapbox/vector-tile': 'vector-tile',
    'supercluster': 'supercluster',
}

# Plugin categories
PLUGIN_CATEGORIES = {
    'leaflet-draw': 'draw',
    'leaflet-geoman': 'draw',
    'leaflet-markercluster': 'clustering',
    'supercluster': 'clustering',
    'leaflet-heat': 'heatmap',
    'leaflet-routing': 'routing',
    'mapbox-directions': 'routing',
    'leaflet-geocoder': 'geocoding',
    'leaflet-geosearch': 'geocoding',
    'mapbox-geocoder': 'geocoding',
    'leaflet-fullscreen': 'control',
    'leaflet-minimap': 'control',
    'leaflet-sidebar': 'control',
    'leaflet-easybutton': 'control',
    'leaflet-omnivore': 'data',
    'leaflet-realtime': 'data',
    'leaflet-image': 'export',
    'mapbox-draw': 'draw',
    'mapbox-sdk': 'api',
    'deck.gl': 'visualization',
    'turf': 'geospatial',
    'topojson': 'data',
    'proj4': 'projection',
    'proj4leaflet': 'projection',
    'geojson': 'data',
    'wellknown': 'data',
    'pbf': 'data',
    'vector-tile': 'data',
}

# Integration type mapping
INTEGRATION_TYPES = {
    'turf': 'geospatial',
    'topojson': 'data',
    'proj4': 'geospatial',
    'proj4leaflet': 'geospatial',
    'geojson': 'data',
    'supercluster': 'data',
    'deck.gl': 'visualization',
    'react-map-gl': 'ui',
    'svelte-maplibre': 'ui',
    'vue-leaflet': 'ui',
    'angular-leaflet': 'ui',
    'react-leaflet': 'ui',
    'leaflet-routing': 'routing',
    'mapbox-directions': 'routing',
    'leaflet-geocoder': 'geocoding',
    'leaflet-geosearch': 'geocoding',
    'mapbox-geocoder': 'geocoding',
    'mapbox-sdk': 'api',
    'wellknown': 'data',
    'pbf': 'data',
    'vector-tile': 'data',
}

# TypeScript type patterns for mapping libs
LEAFLET_TYPE_PATTERN = re.compile(
    r"""(?:L\.|Leaflet\.)(Map|Marker|LatLng|LatLngBounds|TileLayer|GeoJSON|LayerGroup|FeatureGroup|Control|Icon|DivIcon|Popup|Tooltip|Circle|CircleMarker|Polygon|Polyline|Rectangle|ImageOverlay|VideoOverlay|SVGOverlay|Pane|Layer|LayerEvent|LeafletEvent|LeafletMouseEvent|LeafletKeyboardEvent|Path|PathOptions|MapOptions|MarkerOptions|PopupOptions|TooltipOptions|TileLayerOptions|GeoJSONOptions|IconOptions|DivIconOptions|FitBoundsOptions|ZoomPanOptions|LocateOptions|Renderer|Canvas|SVG|CRS|Projection|Transformation|Bounds|Point)\b"""
)

MAPBOX_TYPE_PATTERN = re.compile(
    r"""(?:mapboxgl|maplibregl)\.(Map|Marker|Popup|NavigationControl|GeolocateControl|AttributionControl|ScaleControl|FullscreenControl|LngLat|LngLatBounds|LngLatLike|Style|Layer|Source|AnyLayer|AnySourceData|MapboxEvent|MapLayerMouseEvent|MapMouseEvent|MapTouchEvent|MapWheelEvent|MapboxGeoJSONFeature|Expression|StyleFunction|MapOptions|MarkerOptions|PopupOptions)\b"""
)

REACT_LEAFLET_TYPE_PATTERN = re.compile(
    r"""(?:import\s+type\s+\{[^}]*|:\s*)(MapContainer|TileLayer|Marker|Popup|Tooltip|Circle|CircleMarker|Polygon|Polyline|Rectangle|GeoJSON|LayerGroup|FeatureGroup|LayersControl|ZoomControl|ScaleControl|AttributionControl|ImageOverlay|VideoOverlay|SVGOverlay|Pane|useMap|useMapEvent|useMapEvents)\b"""
)

# Leaflet version detection from package.json or comments
VERSION_PATTERN = re.compile(
    r"""(?:['"]leaflet['"]\s*:\s*['"]\^?~?(\d+\.\d+(?:\.\d+)?)|Leaflet\s+v?(\d+\.\d+(?:\.\d+)?)|leaflet@(\d+\.\d+(?:\.\d+)?))""",
    re.IGNORECASE
)

MAPBOX_VERSION_PATTERN = re.compile(
    r"""(?:['"]mapbox-gl['"]\s*:\s*['"]\^?~?(\d+\.\d+(?:\.\d+)?)|mapbox-gl@(\d+\.\d+(?:\.\d+)?))""",
    re.IGNORECASE
)


class LeafletAPIExtractor:
    """Extracts imports, integrations, types, plugins, and framework info."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract API information.

        Returns:
            Dict with 'imports', 'integrations', 'types', 'plugins', 'framework_info'.
        """
        imports = []
        integrations = []
        types = []
        plugins = []
        framework_info = {
            'leaflet_version': '',
            'mapbox_version': '',
            'has_typescript': False,
            'has_react_leaflet': False,
            'has_mapbox': False,
            'has_maplibre': False,
            'features': [],
        }

        detected_packages = set()

        # ── Import Detection ─────────────────────────────────────
        for line_idx, line_text in enumerate(content.split('\n'), 1):
            stripped = line_text.strip()

            # Skip comments
            if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
                continue

            for pattern in IMPORT_PATTERNS:
                for match in pattern.finditer(line_text):
                    groups = match.groups()
                    package = ''
                    symbols = []
                    import_type = 'module_default'

                    if len(groups) == 2:
                        # Default or named import
                        if '{' in match.group(0) or ',' in (groups[0] or ''):
                            symbols = [s.strip().split(' as ')[0].strip() for s in groups[0].split(',') if s.strip()]
                            import_type = 'module_named'
                        elif '* as' in match.group(0):
                            import_type = 'module_namespace'
                        package = groups[1]
                    elif len(groups) == 3:
                        # require with destructuring or default
                        if groups[0]:
                            symbols = [s.strip() for s in groups[0].split(',') if s.strip()]
                            import_type = 'require'
                        else:
                            import_type = 'require'
                        package = groups[2]
                    elif len(groups) == 1:
                        # Dynamic import or CSS
                        package = groups[0]
                        if 'import(' in match.group(0):
                            import_type = 'dynamic'
                        elif '.css' in package:
                            import_type = 'css'

                    if not package:
                        continue

                    # Check if it's a mapping-related package
                    mapped_pkg = None
                    # Try exact match first
                    if package in MAPPING_PACKAGES:
                        mapped_pkg = MAPPING_PACKAGES[package]
                    else:
                        # Fallback to substring match (longer keys first to avoid false matches)
                        for pkg_key, pkg_name in sorted(MAPPING_PACKAGES.items(), key=lambda x: -len(x[0])):
                            if pkg_key in package:
                                mapped_pkg = pkg_name
                                break

                    if mapped_pkg or any(kw in package for kw in ['leaflet', 'mapbox', 'maplibre', 'map-gl']):
                        is_plugin = mapped_pkg in PLUGIN_CATEGORIES if mapped_pkg else False
                        imports.append(LeafletImportInfo(
                            name=symbols[0] if symbols else package.split('/')[-1],
                            line_number=line_idx,
                            import_type=import_type,
                            package=mapped_pkg or package,
                            symbols=symbols[:10],
                            is_plugin=is_plugin,
                        ))
                        if mapped_pkg:
                            detected_packages.add(mapped_pkg)

                        # Track plugins
                        if is_plugin and mapped_pkg:
                            plugin_type = PLUGIN_CATEGORIES.get(mapped_pkg, 'other')
                            plugins.append(LeafletPluginInfo(
                                name=mapped_pkg,
                                line_number=line_idx,
                                plugin_type=plugin_type,
                                package=package,
                            ))

        # ── Integrations ─────────────────────────────────────────
        for pkg in detected_packages:
            if pkg in INTEGRATION_TYPES:
                integrations.append(LeafletIntegrationInfo(
                    name=pkg,
                    line_number=0,
                    integration_type=INTEGRATION_TYPES[pkg],
                    library=pkg,
                ))

        # ── TypeScript Types ─────────────────────────────────────
        is_ts = file_path.endswith(('.ts', '.tsx'))
        has_type_annotations = bool(re.search(r':\s*(?:L\.|mapboxgl\.|maplibregl\.)\w+', content))

        if is_ts or has_type_annotations:
            framework_info['has_typescript'] = True

            for match in LEAFLET_TYPE_PATTERN.finditer(content):
                line = content[:match.start()].count('\n') + 1
                type_name = match.group(1)
                types.append(LeafletTypeInfo(
                    name=type_name,
                    line_number=line,
                    type_source='leaflet',
                    type_category=self._categorize_type(type_name),
                ))

            for match in MAPBOX_TYPE_PATTERN.finditer(content):
                line = content[:match.start()].count('\n') + 1
                type_name = match.group(1)
                source = 'mapbox-gl' if 'mapboxgl' in match.group(0) else 'maplibre-gl'
                types.append(LeafletTypeInfo(
                    name=type_name,
                    line_number=line,
                    type_source=source,
                    type_category=self._categorize_type(type_name),
                ))

        # ── Framework Info ───────────────────────────────────────
        # Version detection
        version_match = VERSION_PATTERN.search(content)
        if version_match:
            framework_info['leaflet_version'] = next(
                (g for g in version_match.groups() if g), ''
            )

        mapbox_version_match = MAPBOX_VERSION_PATTERN.search(content)
        if mapbox_version_match:
            framework_info['mapbox_version'] = next(
                (g for g in mapbox_version_match.groups() if g), ''
            )

        # Framework detection
        if 'react-leaflet' in detected_packages:
            framework_info['has_react_leaflet'] = True
            if 'react-leaflet' not in framework_info['features']:
                framework_info['features'].append('react-leaflet')

        if 'mapbox-gl' in detected_packages:
            framework_info['has_mapbox'] = True
            if 'mapbox-gl' not in framework_info['features']:
                framework_info['features'].append('mapbox-gl')

        if 'maplibre-gl' in detected_packages:
            framework_info['has_maplibre'] = True
            if 'maplibre-gl' not in framework_info['features']:
                framework_info['features'].append('maplibre-gl')

        # Feature detection
        if any(p in detected_packages for p in ['leaflet-draw', 'mapbox-draw', 'leaflet-geoman']):
            if 'drawing' not in framework_info['features']:
                framework_info['features'].append('drawing')

        if any(p in detected_packages for p in ['leaflet-markercluster', 'supercluster']):
            if 'clustering' not in framework_info['features']:
                framework_info['features'].append('clustering')

        if 'leaflet-heat' in detected_packages:
            if 'heatmap' not in framework_info['features']:
                framework_info['features'].append('heatmap')

        if any(p in detected_packages for p in ['leaflet-routing', 'mapbox-directions']):
            if 'routing' not in framework_info['features']:
                framework_info['features'].append('routing')

        if any(p in detected_packages for p in ['leaflet-geocoder', 'leaflet-geosearch', 'mapbox-geocoder']):
            if 'geocoding' not in framework_info['features']:
                framework_info['features'].append('geocoding')

        if any(p in detected_packages for p in ['turf', 'proj4', 'proj4leaflet']):
            if 'geospatial' not in framework_info['features']:
                framework_info['features'].append('geospatial')

        if 'deck.gl' in detected_packages:
            if 'deck.gl' not in framework_info['features']:
                framework_info['features'].append('deck.gl')

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
            'plugins': plugins,
            'framework_info': framework_info,
        }

    def _categorize_type(self, type_name: str) -> str:
        """Categorize a TypeScript type name."""
        map_types = {'Map', 'MapOptions', 'MapboxEvent'}
        layer_types = {'Layer', 'TileLayer', 'TileLayerOptions', 'ImageOverlay', 'VideoOverlay', 'SVGOverlay', 'Source', 'AnyLayer', 'AnySourceData'}
        geometry_types = {'LatLng', 'LatLngBounds', 'LngLat', 'LngLatBounds', 'LngLatLike', 'Point', 'Bounds', 'GeoJSON', 'MapboxGeoJSONFeature'}
        event_types = {'LeafletEvent', 'LeafletMouseEvent', 'LeafletKeyboardEvent', 'LayerEvent', 'MapLayerMouseEvent', 'MapMouseEvent', 'MapTouchEvent', 'MapWheelEvent'}
        control_types = {'Control', 'NavigationControl', 'GeolocateControl', 'AttributionControl', 'ScaleControl', 'FullscreenControl'}
        marker_types = {'Marker', 'MarkerOptions', 'Icon', 'DivIcon', 'IconOptions', 'DivIconOptions', 'CircleMarker'}

        if type_name in map_types:
            return 'map'
        elif type_name in layer_types:
            return 'layer'
        elif type_name in geometry_types:
            return 'geometry'
        elif type_name in event_types:
            return 'event'
        elif type_name in control_types:
            return 'control'
        elif type_name in marker_types:
            return 'marker'
        else:
            return 'options'
