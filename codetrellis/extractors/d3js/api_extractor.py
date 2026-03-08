"""
D3.js API Extractor

Extracts API-level constructs:
- Import detection (d3 monolithic, d3-* modular packages, CDN/script tags)
- Version detection (v3 patterns, v4+ modular, v5+ join, v6+ ESM, v7+ types)
- Observable / notebook patterns
- TypeScript type usage
- Ecosystem libraries (visx, nivo, recharts, semiotic, victory, vega, plotly)
- Data loading (d3.csv, d3.json, d3.tsv, fetch)
- Utility modules (d3-array, d3-format, d3-time-format, d3-color, d3-interpolate)
- Geo/map modules (d3-geo, d3-geo-projection, topojson)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class D3ImportInfo:
    """D3 import statement."""
    name: str  # package name
    file: str
    line_number: int
    import_type: str  # 'module_default', 'module_named', 'module_namespace', 'require', 'cdn', 'observable'
    package: str = ""  # 'd3', 'd3-selection', 'd3-scale', etc.
    symbols: List[str] = field(default_factory=list)  # imported symbols
    is_modular: bool = False  # d3-* modular import (v4+)
    is_monolithic: bool = False  # import * as d3 / require('d3')


@dataclass
class D3IntegrationInfo:
    """D3 ecosystem integration."""
    name: str  # library name
    file: str
    line_number: int
    integration_type: str  # 'react_wrapper', 'charting_library', 'geo', 'data_utility', 'animation', 'testing'
    library: str = ""  # 'visx', 'nivo', 'recharts', etc.


@dataclass
class D3TypeInfo:
    """TypeScript type for D3."""
    name: str  # type name
    file: str
    line_number: int
    type_source: str  # '@types/d3', 'd3', 'custom'
    type_category: str = ""  # 'selection', 'scale', 'axis', 'shape', 'layout', 'geo', 'transition'


class D3APIExtractor:
    """Extracts D3.js API-level constructs."""

    # ── D3 modular packages ───────────────────────────────────────
    D3_PACKAGES = [
        'd3', 'd3-selection', 'd3-scale', 'd3-axis', 'd3-shape',
        'd3-array', 'd3-color', 'd3-dispatch', 'd3-drag', 'd3-dsv',
        'd3-ease', 'd3-fetch', 'd3-force', 'd3-format', 'd3-geo',
        'd3-hierarchy', 'd3-interpolate', 'd3-path', 'd3-polygon',
        'd3-quadtree', 'd3-random', 'd3-scale-chromatic', 'd3-selection',
        'd3-shape', 'd3-time', 'd3-time-format', 'd3-timer',
        'd3-transition', 'd3-zoom', 'd3-brush', 'd3-chord',
        'd3-contour', 'd3-delaunay', 'd3-sankey', 'd3-cloud',
        'd3-annotation', 'd3-legend', 'd3-tip', 'd3-hexbin',
        'd3-voronoi', 'd3-geo-projection',
    ]

    # ── Import patterns ───────────────────────────────────────────
    # ES module: import { select, selectAll } from 'd3-selection'
    NAMED_IMPORT_PATTERN = re.compile(
        r'import\s*\{([^}]+)\}\s*from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module: import * as d3 from 'd3'
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r'import\s*\*\s*as\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module: import d3 from 'd3'
    DEFAULT_IMPORT_PATTERN = re.compile(
        r'import\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # CommonJS: const d3 = require('d3')
    REQUIRE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    # CDN / script tag
    CDN_PATTERN = re.compile(
        r'<script\b[^>]*src\s*=\s*["\'][^"\']*d3(?:\.min)?\.js[^"\']*["\']',
        re.MULTILINE | re.IGNORECASE
    )
    # Observable notebook patterns
    OBSERVABLE_IMPORT_PATTERN = re.compile(
        r'(?:import\s*\{[^}]*\}\s*from\s*["\']@observablehq/|'
        r'd3\s*=\s*require\s*\(\s*["\']d3|'
        r'import\s*\(\s*["\']https://cdn\.jsdelivr\.net/npm/d3|'
        r'FileAttachment\s*\(|'
        r'viewof\s+\w+\s*=|'
        r'md`)',
        re.MULTILINE
    )

    # ── Version detection patterns ────────────────────────────────
    # v3 patterns: d3.scale.linear, d3.svg.axis, d3.svg.line, d3.layout.force
    V3_PATTERNS = re.compile(
        r'd3\.(?:scale|svg|layout|geo|time|behavior)\.\w+',
        re.MULTILINE
    )
    # v4+ patterns: d3.scaleLinear, d3.axisBottom, d3.forceSimulation
    V4_PATTERNS = re.compile(
        r'd3\.(?:scaleLinear|scaleLog|scaleBand|scaleOrdinal|scalePoint|'
        r'scaleTime|scaleUtc|scaleSequential|scaleDiverging|'
        r'axisTop|axisRight|axisBottom|axisLeft|'
        r'forceSimulation|forceLink|forceManyBody|forceCenter|'
        r'line|area|arc|pie|stack|symbol)',
        re.MULTILINE
    )
    # v5+ patterns: selection.join(), d3.create()
    V5_PATTERNS = re.compile(
        r'\.join\s*\(|d3\.create\s*\(',
        re.MULTILINE
    )
    # v6+ patterns: ES module imports, d3.pointer, d3.groups
    V6_PATTERNS = re.compile(
        r'd3\.pointer\s*\(|d3\.groups?\s*\(|d3\.least\s*\(|d3\.greatest\s*\(|'
        r'd3\.index\s*\(|d3\.union\s*\(|d3\.intersection\s*\(|d3\.difference\s*\(',
        re.MULTILINE
    )
    # v7+ patterns: TypeScript built-in types, d3.bin (renamed from histogram)
    V7_PATTERNS = re.compile(
        r'd3\.bin\s*\(|'
        r'from\s*["\']d3["\'].*?\btype\b|'
        r'import\s+type\s+.*?from\s*["\']d3',
        re.MULTILINE
    )

    # ── Ecosystem integration patterns ────────────────────────────
    ECOSYSTEM_PATTERNS = {
        # React wrappers
        'visx': re.compile(r"from\s+['\"]@visx/", re.MULTILINE),
        'nivo': re.compile(r"from\s+['\"]@nivo/", re.MULTILINE),
        'recharts': re.compile(r"from\s+['\"]recharts['\"]", re.MULTILINE),
        'victory': re.compile(r"from\s+['\"]victory['\"]", re.MULTILINE),
        'semiotic': re.compile(r"from\s+['\"]semiotic['\"]", re.MULTILINE),
        'react-d3-library': re.compile(r"from\s+['\"]react-d3-library['\"]", re.MULTILINE),

        # Charting libraries
        'vega': re.compile(r"from\s+['\"]vega(?:-lite)?['\"]", re.MULTILINE),
        'vega-lite': re.compile(r"from\s+['\"]vega-lite['\"]", re.MULTILINE),
        'plotly': re.compile(r"from\s+['\"]plotly\.js['\"]|Plotly\.newPlot", re.MULTILINE),
        'chart-js': re.compile(r"from\s+['\"]chart\.js['\"]", re.MULTILINE),
        'echarts': re.compile(r"from\s+['\"]echarts['\"]", re.MULTILINE),
        'highcharts': re.compile(r"from\s+['\"]highcharts['\"]", re.MULTILINE),

        # Geo / mapping
        'topojson': re.compile(r"from\s+['\"]topojson['\"]|topojson\.\w+", re.MULTILINE),
        'd3-geo-projection': re.compile(r"from\s+['\"]d3-geo-projection['\"]", re.MULTILINE),
        'leaflet': re.compile(r"from\s+['\"]leaflet['\"]|L\.map", re.MULTILINE),
        'mapbox': re.compile(r"from\s+['\"]mapbox-gl['\"]|mapboxgl\.", re.MULTILINE),
        'deck-gl': re.compile(r"from\s+['\"]@deck\.gl/|from\s+['\"]deck\.gl['\"]", re.MULTILINE),

        # Data utilities
        'crossfilter': re.compile(r"from\s+['\"]crossfilter['\"]|crossfilter\(", re.MULTILINE),
        'lodash': re.compile(r"from\s+['\"]lodash['\"]", re.MULTILINE),
        'moment': re.compile(r"from\s+['\"]moment['\"]", re.MULTILINE),
        'date-fns': re.compile(r"from\s+['\"]date-fns['\"]", re.MULTILINE),

        # Animation
        'gsap': re.compile(r"from\s+['\"]gsap['\"]|gsap\.\w+", re.MULTILINE),
        'anime': re.compile(r"from\s+['\"]animejs['\"]|from\s+['\"]anime['\"]", re.MULTILINE),

        # Observable
        'observable': re.compile(
            r"from\s+['\"]@observablehq/|"
            r"import\s*\(\s*['\"]https://cdn\.jsdelivr\.net/npm/@observablehq|"
            r"Observable\s*\.\s*notebook",
            re.MULTILINE
        ),
    }

    # ── Data loading patterns ─────────────────────────────────────
    DATA_LOAD_PATTERNS = {
        'csv': re.compile(r'd3\.csv\s*\(', re.MULTILINE),
        'tsv': re.compile(r'd3\.tsv\s*\(', re.MULTILINE),
        'json': re.compile(r'd3\.json\s*\(', re.MULTILINE),
        'xml': re.compile(r'd3\.xml\s*\(', re.MULTILINE),
        'html': re.compile(r'd3\.html\s*\(', re.MULTILINE),
        'text': re.compile(r'd3\.text\s*\(', re.MULTILINE),
        'image': re.compile(r'd3\.image\s*\(', re.MULTILINE),
        'svg': re.compile(r'd3\.svg\s*\(\s*["\']', re.MULTILINE),  # d3.svg("url") in v5+
        'dsv': re.compile(r'd3\.dsv\s*\(', re.MULTILINE),
    }

    # ── Geo patterns ──────────────────────────────────────────────
    GEO_PATTERN = re.compile(
        r'd3\.geo(?:Path|Projection|Albers|AlbersUsa|Mercator|NaturalEarth|'
        r'Equirectangular|Orthographic|Stereographic|ConicConformal|'
        r'ConicEqualArea|ConicEquidistant|Gnomonic|TransverseMercator|'
        r'Graticule|Stream|Centroid|Area|Bounds|Contains|Distance)\s*\(',
        re.MULTILINE
    )
    GEOPATH_PATTERN = re.compile(r'd3\.geoPath\s*\(', re.MULTILINE)
    PROJECTION_PATTERN = re.compile(
        r'd3\.geo(Albers|AlbersUsa|Mercator|NaturalEarth1|'
        r'Equirectangular|Orthographic|Stereographic|ConicConformal|'
        r'ConicEqualArea|ConicEquidistant|Gnomonic|TransverseMercator|'
        r'EqualEarth|AzimuthalEqualArea|AzimuthalEquidistant)\s*\(',
        re.MULTILINE
    )

    # ── TypeScript type patterns ──────────────────────────────────
    D3_TYPE_PATTERN = re.compile(
        r'(?:Selection|ScaleLinear|ScaleOrdinal|ScaleBand|ScaleTime|'
        r'Axis|Line|Area|Arc|Pie|Stack|Simulation|GeoPath|GeoProjection|'
        r'Zoom|ZoomBehavior|Drag|DragBehavior|Brush|Transition|'
        r'HierarchyNode|Quadtree|Dispatch|ForceLink|ForceManyBody|'
        r'SimulationNodeDatum|SimulationLinkDatum)<',
        re.MULTILINE
    )
    TYPES_D3_IMPORT = re.compile(
        r'import\s+(?:type\s+)?\{[^}]*\}\s*from\s*["\']@types/d3',
        re.MULTILINE
    )

    # ── D3 utility patterns ───────────────────────────────────────
    D3_ARRAY_UTILS = re.compile(
        r'd3\.(?:min|max|extent|sum|mean|median|deviation|variance|'
        r'ascending|descending|bisect|cross|merge|pairs|permute|'
        r'range|shuffle|ticks|tickIncrement|tickStep|group|groups|'
        r'rollup|rollups|count|sort|reverse|filter|map|reduce|'
        r'flatGroup|flatRollup|index|indexes|least|greatest|'
        r'leastIndex|greatestIndex|quantile|quantileSorted|'
        r'cumsum|rank|bin|histogram|thresholdFreedmanDiaconis|'
        r'thresholdScott|thresholdSturges|every|some|union|'
        r'intersection|difference|superset|subset|disjoint)\s*\(',
        re.MULTILINE
    )
    D3_FORMAT_UTILS = re.compile(
        r'd3\.(?:format|precisionFixed|precisionPrefix|precisionRound|'
        r'formatLocale|formatDefaultLocale|formatSpecifier)\s*\(',
        re.MULTILINE
    )
    D3_TIME_FORMAT_UTILS = re.compile(
        r'd3\.(?:timeFormat|timeParse|utcFormat|utcParse|isoFormat|isoParse|'
        r'timeFormatLocale|timeFormatDefaultLocale)\s*\(',
        re.MULTILINE
    )
    D3_COLOR_UTILS = re.compile(
        r'd3\.(?:color|rgb|hsl|lab|hcl|cubehelix|gray|lch)\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API-level constructs from D3.js code."""
        result: Dict[str, Any] = {
            'imports': [],
            'integrations': [],
            'types': [],
            'data_loaders': [],
            'framework_info': {
                'is_v3': False,
                'is_v4_plus': False,
                'is_v5_plus': False,
                'is_v6_plus': False,
                'is_v7_plus': False,
                'is_modular': False,
                'is_monolithic': False,
                'is_observable': False,
                'has_geo': False,
                'features': [],
                'detected_version': '',
            },
        }

        # ── Imports ──────────────────────────────────────────────
        # Named imports: import { select } from 'd3-selection'
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            symbols_str = match.group(1)
            package = match.group(2)
            if not self._is_d3_package(package):
                continue
            symbols = [s.strip().split(' as ')[0].strip() for s in symbols_str.split(',')]
            symbols = [s for s in symbols if s]
            line_num = content[:match.start()].count('\n') + 1
            is_modular = package.startswith('d3-')
            result['imports'].append(D3ImportInfo(
                name=package,
                file=file_path,
                line_number=line_num,
                import_type='module_named',
                package=package,
                symbols=symbols[:20],
                is_modular=is_modular,
                is_monolithic=package == 'd3',
            ))

        # Namespace imports: import * as d3 from 'd3'
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_d3_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(D3ImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_namespace',
                package=package,
                symbols=[alias],
                is_modular=package.startswith('d3-'),
                is_monolithic=package == 'd3',
            ))

        # Default imports
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_d3_package(package):
                continue
            # Skip if already matched as named/namespace
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(D3ImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_default',
                package=package,
                symbols=[alias],
                is_modular=package.startswith('d3-'),
                is_monolithic=package == 'd3',
            ))

        # CommonJS require
        for match in self.REQUIRE_PATTERN.finditer(content):
            destructured = match.group(1)
            alias = match.group(2)
            package = match.group(3)
            if not self._is_d3_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            symbols = []
            if destructured:
                symbols = [s.strip() for s in destructured.split(',') if s.strip()]
            elif alias:
                symbols = [alias]
            result['imports'].append(D3ImportInfo(
                name=alias or package,
                file=file_path,
                line_number=line_num,
                import_type='require',
                package=package,
                symbols=symbols[:20],
                is_modular=package.startswith('d3-'),
                is_monolithic=package == 'd3',
            ))

        # CDN / script tags
        for match in self.CDN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(D3ImportInfo(
                name='d3_cdn',
                file=file_path,
                line_number=line_num,
                import_type='cdn',
                package='d3',
                is_monolithic=True,
            ))

        # Observable imports
        for match in self.OBSERVABLE_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(D3ImportInfo(
                name='d3_observable',
                file=file_path,
                line_number=line_num,
                import_type='observable',
                package='d3',
                is_monolithic=True,
            ))

        # ── Ecosystem integrations ───────────────────────────────
        for lib_name, pattern in self.ECOSYSTEM_PATTERNS.items():
            if pattern.search(content):
                match = pattern.search(content)
                line_num = content[:match.start()].count('\n') + 1
                integration_type = self._classify_integration(lib_name)
                result['integrations'].append(D3IntegrationInfo(
                    name=lib_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=integration_type,
                    library=lib_name,
                ))

        # ── Data loaders ─────────────────────────────────────────
        for loader_type, pattern in self.DATA_LOAD_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['data_loaders'].append({
                    'type': loader_type,
                    'file': file_path,
                    'line': line_num,
                })

        # ── TypeScript types ─────────────────────────────────────
        for match in self.D3_TYPE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            type_name = match.group(0).rstrip('<')
            category = self._classify_type(type_name)
            result['types'].append(D3TypeInfo(
                name=type_name,
                file=file_path,
                line_number=line_num,
                type_source='d3',
                type_category=category,
            ))

        if self.TYPES_D3_IMPORT.search(content):
            match = self.TYPES_D3_IMPORT.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['types'].append(D3TypeInfo(
                name='@types/d3',
                file=file_path,
                line_number=line_num,
                type_source='@types/d3',
                type_category='package',
            ))

        # ── Version detection ────────────────────────────────────
        fw_info = result['framework_info']
        features: List[str] = []

        if self.V3_PATTERNS.search(content):
            fw_info['is_v3'] = True
            fw_info['detected_version'] = 'v3'
            features.append('v3_api')

        if self.V4_PATTERNS.search(content):
            fw_info['is_v4_plus'] = True
            fw_info['detected_version'] = 'v4'
            features.append('v4_api')

        if self.V5_PATTERNS.search(content):
            fw_info['is_v5_plus'] = True
            fw_info['detected_version'] = 'v5'
            features.append('v5_join')

        if self.V6_PATTERNS.search(content):
            fw_info['is_v6_plus'] = True
            fw_info['detected_version'] = 'v6'
            features.append('v6_esm')

        if self.V7_PATTERNS.search(content):
            fw_info['is_v7_plus'] = True
            fw_info['detected_version'] = 'v7'
            features.append('v7_types')

        # Check modular vs monolithic
        any_modular = any(i.is_modular for i in result['imports'])
        any_monolithic = any(i.is_monolithic for i in result['imports'])
        fw_info['is_modular'] = any_modular
        # V3 API patterns are inherently monolithic (global d3 object)
        fw_info['is_monolithic'] = any_monolithic or fw_info.get('is_v3', False)

        # Observable detection
        if self.OBSERVABLE_IMPORT_PATTERN.search(content):
            fw_info['is_observable'] = True
            features.append('observable')

        # Geo detection
        if self.GEO_PATTERN.search(content) or self.GEOPATH_PATTERN.search(content):
            fw_info['has_geo'] = True
            features.append('geo')

        # Projection detection
        for match in self.PROJECTION_PATTERN.finditer(content):
            proj_name = match.group(1)
            features.append(f"projection_{proj_name}")

        # Data utility features
        if self.D3_ARRAY_UTILS.search(content):
            features.append('d3_array')
        if self.D3_FORMAT_UTILS.search(content):
            features.append('d3_format')
        if self.D3_TIME_FORMAT_UTILS.search(content):
            features.append('d3_time_format')
        if self.D3_COLOR_UTILS.search(content):
            features.append('d3_color')

        # Data loading features
        for loader in result['data_loaders']:
            feat = f"data_{loader['type']}"
            if feat not in features:
                features.append(feat)

        fw_info['features'] = features

        return result

    def _is_d3_package(self, package: str) -> bool:
        """Check if a package name is D3-related."""
        if package == 'd3' or package.startswith('d3-'):
            return True
        if package in ('@types/d3', 'topojson', 'd3-tip', 'd3-annotation',
                       'd3-legend', 'd3-cloud', 'd3-hexbin', 'd3-sankey'):
            return True
        return False

    @staticmethod
    def _classify_integration(lib_name: str) -> str:
        """Classify an ecosystem library."""
        react_wrappers = {'visx', 'nivo', 'recharts', 'victory', 'semiotic', 'react-d3-library'}
        charting = {'vega', 'vega-lite', 'plotly', 'chart-js', 'echarts', 'highcharts'}
        geo = {'topojson', 'd3-geo-projection', 'leaflet', 'mapbox', 'deck-gl'}
        data = {'crossfilter', 'lodash', 'moment', 'date-fns'}
        animation = {'gsap', 'anime'}

        if lib_name in react_wrappers:
            return 'react_wrapper'
        elif lib_name in charting:
            return 'charting_library'
        elif lib_name in geo:
            return 'geo'
        elif lib_name in data:
            return 'data_utility'
        elif lib_name in animation:
            return 'animation'
        elif lib_name == 'observable':
            return 'notebook'
        return 'other'

    @staticmethod
    def _classify_type(type_name: str) -> str:
        """Classify a TypeScript D3 type."""
        type_map = {
            'Selection': 'selection',
            'ScaleLinear': 'scale', 'ScaleOrdinal': 'scale', 'ScaleBand': 'scale',
            'ScaleTime': 'scale',
            'Axis': 'axis',
            'Line': 'shape', 'Area': 'shape', 'Arc': 'shape', 'Pie': 'shape',
            'Stack': 'shape',
            'Simulation': 'layout', 'HierarchyNode': 'layout',
            'GeoPath': 'geo', 'GeoProjection': 'geo',
            'Zoom': 'interaction', 'ZoomBehavior': 'interaction',
            'Drag': 'interaction', 'DragBehavior': 'interaction',
            'Brush': 'interaction',
            'Transition': 'transition',
            'Quadtree': 'spatial', 'Dispatch': 'utility',
            'ForceLink': 'layout', 'ForceManyBody': 'layout',
            'SimulationNodeDatum': 'layout', 'SimulationLinkDatum': 'layout',
        }
        return type_map.get(type_name, 'other')
