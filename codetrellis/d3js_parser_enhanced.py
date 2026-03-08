"""
EnhancedD3JSParser v1.0 - Comprehensive D3.js parser using all extractors.

This parser integrates all D3.js extractors to provide complete parsing of
data visualization applications. It runs as a supplementary layer on top of
the JavaScript and TypeScript parsers, extracting D3.js-specific semantics.

Supports:
- D3.js v3 (monolithic d3 global, d3.scale.linear, d3.svg.axis, d3.layout.force)
- D3.js v4 (modular packages, d3.scaleLinear, d3.axisBottom, d3.forceSimulation)
- D3.js v5 (promises for data loading, selection.join, d3.create)
- D3.js v6 (ES modules, d3.pointer, event parameter changes)
- D3.js v7 (TypeScript types, d3.bin, latest stable)

Visualization constructs:
- Selections (select/selectAll, selection chains)
- Data Joins (enter/update/exit, join, datum)
- Shapes (arc, line, area, pie, stack, symbol, link, contour, ribbon)
- Layouts (force, tree, cluster, treemap, pack, partition, chord, sankey, histogram, voronoi)
- SVG elements (svg, g, rect, circle, path, text, line, polygon, etc.)
- Canvas rendering

Scale constructs:
- Continuous (linear, log, pow, sqrt, time, utc, radial, symlog, identity)
- Ordinal (ordinal, band, point)
- Quantizing (quantize, quantile, threshold)
- Sequential / Diverging
- Color schemes (categorical, sequential, diverging, cyclical)

Axis constructs:
- Axis generators (axisTop/Right/Bottom/Left)
- Tick configuration (ticks, tickFormat, tickValues, tickSize, tickPadding)
- Grid lines
- Brush (2D, X, Y)
- Zoom (scaleExtent, translateExtent, zoomTransform, zoomIdentity)

Interaction constructs:
- Event listeners (on/dispatch)
- Drag behavior
- Transitions (duration, delay, ease, named)
- Tooltips (div, d3-tip, title)

API constructs:
- Import detection (ES module, CommonJS, CDN, Observable)
- Version detection (v3-v7)
- Data loading (csv, json, tsv, dsv)
- Ecosystem integrations (visx, nivo, recharts, vega, topojson, etc.)
- TypeScript type usage
- Geo/map support (projections, geoPath, topojson)

Framework detection (20+ D3 ecosystem patterns):
- Core: d3, d3-selection, d3-scale, d3-axis, d3-shape
- Layout: d3-force, d3-hierarchy, d3-chord, d3-sankey
- Interaction: d3-zoom, d3-brush, d3-drag, d3-transition
- Geo: d3-geo, d3-geo-projection, topojson
- Data: d3-array, d3-fetch, d3-dsv, d3-format, d3-time-format
- Color: d3-scale-chromatic, d3-color, d3-interpolate
- React wrappers: visx, nivo, recharts, victory
- Charting: vega, plotly, chart.js, echarts
- Observable notebooks

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.72 - D3.js Data Visualization Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all D3.js extractors
from .extractors.d3js import (
    D3VisualizationExtractor, D3SelectionInfo, D3DataJoinInfo,
    D3ShapeInfo, D3LayoutInfo, D3SVGElementInfo,
    D3ScaleExtractor, D3ScaleInfo, D3ColorScaleInfo,
    D3AxisExtractor, D3AxisInfo, D3BrushInfo, D3ZoomInfo,
    D3InteractionExtractor, D3EventInfo, D3DragInfo,
    D3TransitionInfo, D3TooltipInfo,
    D3APIExtractor, D3ImportInfo, D3IntegrationInfo, D3TypeInfo,
)


@dataclass
class D3JSParseResult:
    """Complete parse result for a D3.js file."""
    file_path: str
    file_type: str = "js"  # js, jsx, ts, tsx

    # Visualization
    selections: List[D3SelectionInfo] = field(default_factory=list)
    data_joins: List[D3DataJoinInfo] = field(default_factory=list)
    shapes: List[D3ShapeInfo] = field(default_factory=list)
    layouts: List[D3LayoutInfo] = field(default_factory=list)
    svg_elements: List[D3SVGElementInfo] = field(default_factory=list)

    # Scales
    scales: List[D3ScaleInfo] = field(default_factory=list)
    color_scales: List[D3ColorScaleInfo] = field(default_factory=list)

    # Axes
    axes: List[D3AxisInfo] = field(default_factory=list)
    brushes: List[D3BrushInfo] = field(default_factory=list)
    zooms: List[D3ZoomInfo] = field(default_factory=list)

    # Interactions
    events: List[D3EventInfo] = field(default_factory=list)
    drags: List[D3DragInfo] = field(default_factory=list)
    transitions: List[D3TransitionInfo] = field(default_factory=list)
    tooltips: List[D3TooltipInfo] = field(default_factory=list)

    # API
    imports: List[D3ImportInfo] = field(default_factory=list)
    integrations: List[D3IntegrationInfo] = field(default_factory=list)
    types: List[D3TypeInfo] = field(default_factory=list)
    data_loaders: List[Dict] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    d3_version: str = ""  # detected D3.js version ('v3', 'v4', 'v5', 'v6', 'v7')
    is_modular: bool = False  # modular d3-* imports (v4+)
    is_monolithic: bool = False  # monolithic d3 import
    is_observable: bool = False  # Observable notebook
    has_geo: bool = False  # geo/map features


class EnhancedD3JSParser:
    """
    Enhanced D3.js parser using all extractors.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when D3.js is detected. It extracts data-visualization-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 20+ D3 ecosystem libraries across:
    - Core (d3, d3-selection, d3-scale, d3-axis, d3-shape)
    - Layout (d3-force, d3-hierarchy, d3-chord, d3-sankey)
    - Interaction (d3-zoom, d3-brush, d3-drag, d3-transition)
    - Geo (d3-geo, d3-geo-projection, topojson)
    - Color (d3-scale-chromatic, d3-color, d3-interpolate)
    - React wrappers (visx, nivo, recharts, victory)
    - Charting libraries (vega, plotly, chart.js, echarts)
    - Observable notebooks

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # D3 ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'd3': re.compile(
            r"from\s+['\"]d3['\"]|require\(['\"]d3['\"]\)|"
            r"import\s*\*\s+as\s+d3\s+from|"
            r"d3\.\w+|<script[^>]*d3(?:\.min)?\.js",
            re.MULTILINE
        ),
        'd3-selection': re.compile(
            r"from\s+['\"]d3-selection['\"]|"
            r"d3\.select\b|d3\.selectAll\b",
            re.MULTILINE
        ),
        'd3-scale': re.compile(
            r"from\s+['\"]d3-scale['\"]|"
            r"d3\.scaleLinear|d3\.scaleOrdinal|d3\.scaleBand|"
            r"d3\.scaleLog|d3\.scaleTime|d3\.scaleUtc|"
            r"d3\.scaleSequential|d3\.scaleDiverging|d3\.scalePoint",
            re.MULTILINE
        ),
        'd3-axis': re.compile(
            r"from\s+['\"]d3-axis['\"]|"
            r"d3\.axisTop|d3\.axisRight|d3\.axisBottom|d3\.axisLeft",
            re.MULTILINE
        ),
        'd3-shape': re.compile(
            r"from\s+['\"]d3-shape['\"]|"
            r"d3\.line\(|d3\.area\(|d3\.arc\(|d3\.pie\(|d3\.stack\(",
            re.MULTILINE
        ),

        # ── Layout ────────────────────────────────────────────────
        'd3-force': re.compile(
            r"from\s+['\"]d3-force['\"]|"
            r"d3\.forceSimulation|d3\.forceLink|d3\.forceManyBody|d3\.forceCenter",
            re.MULTILINE
        ),
        'd3-hierarchy': re.compile(
            r"from\s+['\"]d3-hierarchy['\"]|"
            r"d3\.hierarchy|d3\.tree\(|d3\.treemap\(|d3\.cluster\(|"
            r"d3\.pack\(|d3\.partition\(",
            re.MULTILINE
        ),
        'd3-chord': re.compile(
            r"from\s+['\"]d3-chord['\"]|d3\.chord\(",
            re.MULTILINE
        ),
        'd3-sankey': re.compile(
            r"from\s+['\"]d3-sankey['\"]|d3Sankey|sankey\(",
            re.MULTILINE
        ),

        # ── Interaction ───────────────────────────────────────────
        'd3-zoom': re.compile(
            r"from\s+['\"]d3-zoom['\"]|d3\.zoom\(|d3\.zoomTransform|d3\.zoomIdentity",
            re.MULTILINE
        ),
        'd3-brush': re.compile(
            r"from\s+['\"]d3-brush['\"]|d3\.brush\(|d3\.brushX\(|d3\.brushY\(",
            re.MULTILINE
        ),
        'd3-drag': re.compile(
            r"from\s+['\"]d3-drag['\"]|d3\.drag\(",
            re.MULTILINE
        ),
        'd3-transition': re.compile(
            r"from\s+['\"]d3-transition['\"]|\.transition\(|d3\.transition\(",
            re.MULTILINE
        ),

        # ── Geo ───────────────────────────────────────────────────
        'd3-geo': re.compile(
            r"from\s+['\"]d3-geo['\"]|d3\.geoPath|d3\.geoMercator|"
            r"d3\.geoAlbers|d3\.geoNaturalEarth|d3\.geoOrthographic|"
            r"d3\.geoEquirectangular|d3\.geoProjection",
            re.MULTILINE
        ),
        'topojson': re.compile(
            r"from\s+['\"]topojson['\"]|topojson\.feature|topojson\.mesh",
            re.MULTILINE
        ),

        # ── Data ──────────────────────────────────────────────────
        'd3-array': re.compile(
            r"from\s+['\"]d3-array['\"]|"
            r"d3\.extent|d3\.min\(|d3\.max\(|d3\.mean|d3\.sum\(|"
            r"d3\.range\(|d3\.group\(|d3\.rollup|d3\.bin\(",
            re.MULTILINE
        ),
        'd3-fetch': re.compile(
            r"from\s+['\"]d3-fetch['\"]|d3\.csv\(|d3\.json\(|d3\.tsv\(",
            re.MULTILINE
        ),
        'd3-format': re.compile(
            r"from\s+['\"]d3-format['\"]|d3\.format\(",
            re.MULTILINE
        ),
        'd3-time-format': re.compile(
            r"from\s+['\"]d3-time-format['\"]|d3\.timeFormat|d3\.timeParse|"
            r"d3\.utcFormat|d3\.utcParse",
            re.MULTILINE
        ),

        # ── Color ─────────────────────────────────────────────────
        'd3-scale-chromatic': re.compile(
            r"from\s+['\"]d3-scale-chromatic['\"]|"
            r"d3\.schemeCategory|d3\.interpolateViridis|d3\.interpolateBlues|"
            r"d3\.interpolateRdYlBu|d3\.schemePaired",
            re.MULTILINE
        ),
        'd3-color': re.compile(
            r"from\s+['\"]d3-color['\"]|d3\.color\(|d3\.rgb\(|d3\.hsl\(",
            re.MULTILINE
        ),
        'd3-interpolate': re.compile(
            r"from\s+['\"]d3-interpolate['\"]|d3\.interpolate\(|"
            r"d3\.interpolateRgb|d3\.interpolateHsl|d3\.interpolateNumber",
            re.MULTILINE
        ),

        # ── React Wrappers ────────────────────────────────────────
        'visx': re.compile(
            r"from\s+['\"]@visx/",
            re.MULTILINE
        ),
        'nivo': re.compile(
            r"from\s+['\"]@nivo/",
            re.MULTILINE
        ),
        'recharts': re.compile(
            r"from\s+['\"]recharts['\"]",
            re.MULTILINE
        ),

        # ── Observable ────────────────────────────────────────────
        'observable': re.compile(
            r"from\s+['\"]@observablehq/|"
            r"import\s*\(\s*['\"]https://cdn\.jsdelivr\.net/npm/@observablehq|"
            r"import\s*\(\s*['\"]https://cdn\.jsdelivr\.net/npm/d3",
            re.MULTILINE
        ),

        # ── Third-party D3 extensions ─────────────────────────────
        'd3-annotation': re.compile(
            r"from\s+['\"]d3-(?:svg-)?annotation['\"]|d3\.annotation\(",
            re.MULTILINE
        ),
        'd3-legend': re.compile(
            r"from\s+['\"]d3-(?:svg-)?legend['\"]|d3\.legend",
            re.MULTILINE
        ),
        'd3-tip': re.compile(
            r"from\s+['\"]d3-tip['\"]|d3[.-]tip",
            re.MULTILINE
        ),
        'd3-cloud': re.compile(
            r"from\s+['\"]d3-cloud['\"]|d3\.layout\.cloud|d3Cloud",
            re.MULTILINE
        ),
    }

    def __init__(self):
        """Initialize the parser with all D3.js extractors."""
        self.visualization_extractor = D3VisualizationExtractor()
        self.scale_extractor = D3ScaleExtractor()
        self.axis_extractor = D3AxisExtractor()
        self.interaction_extractor = D3InteractionExtractor()
        self.api_extractor = D3APIExtractor()

    def parse(self, content: str, file_path: str = "") -> D3JSParseResult:
        """
        Parse D3.js source code and extract all visualization-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when D3.js is detected. It extracts visualization structures, scales,
        axes, interactions, and API usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            D3JSParseResult with all extracted information
        """
        result = D3JSParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract visualization constructs ──────────────────────
        vis_result = self.visualization_extractor.extract(content, file_path)
        result.selections = vis_result.get('selections', [])
        result.data_joins = vis_result.get('data_joins', [])
        result.shapes = vis_result.get('shapes', [])
        result.layouts = vis_result.get('layouts', [])
        result.svg_elements = vis_result.get('svg_elements', [])

        # ── Extract scale constructs ──────────────────────────────
        scale_result = self.scale_extractor.extract(content, file_path)
        result.scales = scale_result.get('scales', [])
        result.color_scales = scale_result.get('color_scales', [])

        # ── Extract axis constructs ───────────────────────────────
        axis_result = self.axis_extractor.extract(content, file_path)
        result.axes = axis_result.get('axes', [])
        result.brushes = axis_result.get('brushes', [])
        result.zooms = axis_result.get('zooms', [])

        # ── Extract interaction constructs ────────────────────────
        int_result = self.interaction_extractor.extract(content, file_path)
        result.events = int_result.get('events', [])
        result.drags = int_result.get('drags', [])
        result.transitions = int_result.get('transitions', [])
        result.tooltips = int_result.get('tooltips', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])
        result.data_loaders = api_result.get('data_loaders', [])

        # Framework info from API extractor
        fw_info = api_result.get('framework_info', {})
        result.is_modular = fw_info.get('is_modular', False)
        result.is_monolithic = fw_info.get('is_monolithic', False)
        result.is_observable = fw_info.get('is_observable', False)
        result.has_geo = fw_info.get('has_geo', False)
        result.detected_features = fw_info.get('features', [])
        result.d3_version = fw_info.get('detected_version', '')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which D3.js ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_d3js_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains D3.js code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains D3.js code
        """
        # Check for D3 imports (ES module or CommonJS)
        if re.search(r"from\s+['\"]d3(?:-\w+)?['\"]", content):
            return True

        # Check for D3 namespace usage
        if re.search(r'd3\.\w+\s*\(', content):
            return True

        # Check for import * as d3
        if re.search(r"import\s*\*\s*as\s+d3\s+from", content):
            return True

        # Check for require('d3')
        if re.search(r"require\s*\(\s*['\"]d3(?:-\w+)?['\"]\s*\)", content):
            return True

        # Check for D3 v3 patterns
        if re.search(r'd3\.(?:scale|svg|layout|geo|behavior)\.\w+', content):
            return True

        # Check for D3 CDN script tags
        if re.search(r'd3(?:\.min)?\.js', content, re.IGNORECASE):
            return True

        # Check for common D3 method chains
        if re.search(r'\.selectAll\s*\(.*?\)\.data\s*\(', content, re.DOTALL):
            return True

        # Check for D3 ecosystem libraries
        if re.search(r"from\s+['\"](?:@visx/|@nivo/|topojson|d3-)", content):
            return True

        return False
