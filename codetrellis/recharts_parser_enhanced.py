"""
EnhancedRechartsParser v1.0 - Comprehensive Recharts parser using all extractors.

This parser integrates all Recharts extractors to provide complete parsing of
React-based charting applications. It runs as a supplementary layer on top of
the JavaScript and TypeScript parsers, extracting Recharts-specific semantics.

Supports:
- Recharts v1 (original API)
- Recharts v2+ (improved TypeScript, new components: Funnel, Sankey)

Chart components:
- Container charts (LineChart, BarChart, AreaChart, PieChart, RadarChart,
  ScatterChart, ComposedChart, RadialBarChart, Treemap, FunnelChart, Sankey)
- ResponsiveContainer (width, height, aspect, debounce)

Data series:
- Line, Bar, Area, Scatter, Pie, Radar, RadialBar
- dataKey, stackId, name, type (monotone, natural, basis, etc.)
- Cell for individual segment styling

Axes and grids:
- XAxis, YAxis, ZAxis with dataKey, domain, scale, tickFormatter
- CartesianGrid (strokeDasharray, horizontal, vertical)
- PolarGrid, PolarAngleAxis, PolarRadiusAxis for radar/radialBar

Customization:
- Tooltip (content, formatter, labelFormatter, custom renderers)
- Legend (content, formatter, iconType, layout, align)
- ReferenceLine, ReferenceArea, ReferenceDot annotations
- Brush for data zoom/pan
- Label, LabelList for data labels
- Event handlers (onClick, onMouseEnter, onMouseLeave, onMouseMove)
- Animation props (isAnimationActive, animationDuration, animationEasing)

API:
- Import detection (recharts, recharts/es6, recharts/lib)
- Version detection (v1 vs v2+)
- TypeScript type usage (LineChartProps, TooltipPayload, etc.)
- Ecosystem integrations (recharts-scale, recharts-to-png, d3-*)

Framework detection (Recharts ecosystem patterns):
- Core: recharts, recharts/es6, recharts/lib
- Scale: recharts-scale
- Export: recharts-to-png
- D3 utilities: d3-scale, d3-shape, d3-format, d3-time-format

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.74 - Recharts Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Recharts extractors
from .extractors.recharts import (
    RechartsComponentExtractor, RechartsComponentInfo, RechartsResponsiveInfo,
    RechartsDataExtractor, RechartsSeriesInfo, RechartsDataKeyInfo, RechartsCellInfo,
    RechartsAxisExtractor, RechartsAxisInfo, RechartsGridInfo, RechartsPolarAxisInfo,
    RechartsCustomizationExtractor, RechartsTooltipInfo, RechartsLegendInfo,
    RechartsReferenceInfo, RechartsBrushInfo, RechartsEventInfo, RechartsAnimationInfo,
    RechartsAPIExtractor, RechartsImportInfo, RechartsIntegrationInfo, RechartsTypeInfo,
)


@dataclass
class RechartsParseResult:
    """Complete parse result for a Recharts file."""
    file_path: str
    file_type: str = "jsx"  # js, jsx, ts, tsx

    # Chart components
    components: List[RechartsComponentInfo] = field(default_factory=list)
    responsive_containers: List[RechartsResponsiveInfo] = field(default_factory=list)

    # Data series
    series: List[RechartsSeriesInfo] = field(default_factory=list)
    data_keys: List[RechartsDataKeyInfo] = field(default_factory=list)
    cells: List[RechartsCellInfo] = field(default_factory=list)

    # Axes and grids
    axes: List[RechartsAxisInfo] = field(default_factory=list)
    grids: List[RechartsGridInfo] = field(default_factory=list)
    polar_axes: List[RechartsPolarAxisInfo] = field(default_factory=list)

    # Customization
    tooltips: List[RechartsTooltipInfo] = field(default_factory=list)
    legends: List[RechartsLegendInfo] = field(default_factory=list)
    references: List[RechartsReferenceInfo] = field(default_factory=list)
    brushes: List[RechartsBrushInfo] = field(default_factory=list)
    events: List[RechartsEventInfo] = field(default_factory=list)
    animations: List[RechartsAnimationInfo] = field(default_factory=list)
    labels: List[Dict] = field(default_factory=list)

    # API
    imports: List[RechartsImportInfo] = field(default_factory=list)
    integrations: List[RechartsIntegrationInfo] = field(default_factory=list)
    types: List[RechartsTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    recharts_version: str = ""  # detected Recharts version ('v1', 'v2')
    is_tree_shakeable: bool = False  # always true for recharts
    has_animation: bool = False  # animation configuration present
    has_typescript: bool = False  # TypeScript types present
    has_responsive: bool = False  # ResponsiveContainer detected


class EnhancedRechartsParser:
    """
    Enhanced Recharts parser using all extractors.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when Recharts is detected. It extracts charting-specific semantics
    that the language parsers cannot capture.

    Recharts is a React-based charting library built on D3.js.
    Unlike Chart.js (imperative canvas API), Recharts uses a
    declarative JSX component model (<LineChart>, <Bar>, <Tooltip>, etc.).

    Framework detection supports Recharts ecosystem libraries:
    - Core: recharts, recharts/es6, recharts/lib
    - Scale: recharts-scale
    - Export: recharts-to-png
    - D3 utilities: d3-scale, d3-shape, d3-format, d3-time-format

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Recharts ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'recharts': re.compile(
            r"from\s+['\"]recharts['\"]|require\(['\"]recharts['\"]\)|"
            r"import\s+['\"]recharts['\"]|"
            r"<(?:LineChart|BarChart|AreaChart|PieChart|RadarChart|"
            r"ScatterChart|ComposedChart|RadialBarChart|Treemap|"
            r"FunnelChart|Sankey|ResponsiveContainer)\b",
            re.MULTILINE
        ),
        'recharts/es6': re.compile(
            r"from\s+['\"]recharts/es6",
            re.MULTILINE
        ),
        'recharts/lib': re.compile(
            r"from\s+['\"]recharts/lib",
            re.MULTILINE
        ),

        # ── Ecosystem ─────────────────────────────────────────────
        'recharts-scale': re.compile(
            r"from\s+['\"]recharts-scale['\"]|"
            r"require\(['\"]recharts-scale['\"]\)",
            re.MULTILINE
        ),
        'recharts-to-png': re.compile(
            r"from\s+['\"]recharts-to-png['\"]|"
            r"require\(['\"]recharts-to-png['\"]\)",
            re.MULTILINE
        ),

        # ── D3 utilities commonly paired with Recharts ────────────
        'd3-scale': re.compile(
            r"from\s+['\"]d3-scale['\"]|require\(['\"]d3-scale['\"]\)",
            re.MULTILINE
        ),
        'd3-shape': re.compile(
            r"from\s+['\"]d3-shape['\"]|require\(['\"]d3-shape['\"]\)",
            re.MULTILINE
        ),
        'd3-format': re.compile(
            r"from\s+['\"]d3-format['\"]|require\(['\"]d3-format['\"]\)",
            re.MULTILINE
        ),
        'd3-time-format': re.compile(
            r"from\s+['\"]d3-time-format['\"]|require\(['\"]d3-time-format['\"]\)",
            re.MULTILINE
        ),
    }

    def __init__(self):
        """Initialize the parser with all Recharts extractors."""
        self.component_extractor = RechartsComponentExtractor()
        self.data_extractor = RechartsDataExtractor()
        self.axis_extractor = RechartsAxisExtractor()
        self.customization_extractor = RechartsCustomizationExtractor()
        self.api_extractor = RechartsAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> RechartsParseResult:
        """
        Parse Recharts source code and extract all charting-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Recharts is detected. It extracts chart components, data series,
        axes, customization, and API usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            RechartsParseResult with all extracted information
        """
        result = RechartsParseResult(file_path=file_path)

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

        # ── Extract chart component constructs ────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.responsive_containers = comp_result.get('responsive_containers', [])

        # ── Extract data series constructs ────────────────────────
        data_result = self.data_extractor.extract(content, file_path)
        result.series = data_result.get('series', [])
        result.data_keys = data_result.get('data_keys', [])
        result.cells = data_result.get('cells', [])

        # ── Extract axis constructs ───────────────────────────────
        axis_result = self.axis_extractor.extract(content, file_path)
        result.axes = axis_result.get('axes', [])
        result.grids = axis_result.get('grids', [])
        result.polar_axes = axis_result.get('polar_axes', [])

        # ── Extract customization constructs ──────────────────────
        cust_result = self.customization_extractor.extract(content, file_path)
        result.tooltips = cust_result.get('tooltips', [])
        result.legends = cust_result.get('legends', [])
        result.references = cust_result.get('references', [])
        result.brushes = cust_result.get('brushes', [])
        result.events = cust_result.get('events', [])
        result.animations = cust_result.get('animations', [])
        result.labels = cust_result.get('labels', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])

        # Framework info from API extractor
        fw_info = api_result.get('framework_info', {})
        result.is_tree_shakeable = fw_info.get('is_tree_shakeable', False)
        result.has_animation = bool(result.animations)
        result.has_typescript = fw_info.get('has_typescript', False)
        result.has_responsive = bool(result.responsive_containers)
        result.detected_features = fw_info.get('features', [])
        result.recharts_version = fw_info.get('recharts_version', '')

        # Add component-level features
        if result.has_responsive:
            if 'responsive' not in result.detected_features:
                result.detected_features.append('responsive')
        if result.has_animation:
            if 'animation' not in result.detected_features:
                result.detected_features.append('animation')

        # Detect chart types as features
        chart_types = set(c.chart_type for c in result.components)
        for ct in chart_types:
            if ct != 'unknown' and f'chart_{ct}' not in result.detected_features:
                result.detected_features.append(f'chart_{ct}')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Recharts ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_recharts_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Recharts code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Recharts code
        """
        # Check for recharts imports (ES module named - most common)
        if re.search(r"from\s+['\"]recharts['\"]", content):
            return True

        # Check for recharts named imports with specific components
        if re.search(r"from\s+['\"]recharts(?:/es6|/lib)?['\"]", content):
            return True

        # Check for require('recharts')
        if re.search(r"require\s*\(\s*['\"]recharts(?:/es6|/lib)?['\"]\s*\)", content):
            return True

        # Check for bare import
        if re.search(r"import\s+['\"]recharts['\"]", content):
            return True

        # Check for Recharts chart container JSX components
        if re.search(
            r'<(?:LineChart|BarChart|AreaChart|PieChart|RadarChart|'
            r'ScatterChart|ComposedChart|RadialBarChart|Treemap|'
            r'FunnelChart|Sankey)\b',
            content
        ):
            return True

        # Check for ResponsiveContainer wrapping a chart
        if re.search(r'<ResponsiveContainer\b', content):
            # Make sure it's Recharts and not a different library
            if re.search(r"from\s+['\"]recharts", content):
                return True
            # Also check for Recharts chart components nearby
            if re.search(
                r'<(?:LineChart|BarChart|AreaChart|PieChart|RadarChart|'
                r'ScatterChart|ComposedChart|RadialBarChart)\b',
                content
            ):
                return True

        # Check for recharts-scale or recharts-to-png
        if re.search(r"from\s+['\"]recharts-", content):
            return True

        # Check for dynamic import
        if re.search(r"import\s*\(\s*['\"]recharts['\"]", content):
            return True

        return False
