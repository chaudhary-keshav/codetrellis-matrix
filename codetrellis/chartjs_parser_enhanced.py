"""
EnhancedChartJSParser v1.0 - Comprehensive Chart.js parser using all extractors.

This parser integrates all Chart.js extractors to provide complete parsing of
charting applications. It runs as a supplementary layer on top of the JavaScript
and TypeScript parsers, extracting Chart.js-specific semantics.

Supports:
- Chart.js v1 (Chart.Line, Chart.Bar, Chart.Pie — constructor-based)
- Chart.js v2 (new Chart(ctx, config), scales.xAxes/yAxes, Chart.defaults.global)
- Chart.js v3 (tree-shakeable, Chart.register, scales.x/y, Chart.defaults)
- Chart.js v4 (ESM-only, chart.js/auto, improved TypeScript types)

Chart configuration constructs:
- Chart instances (new Chart, React/Vue/Angular components)
- Chart types (line, bar, pie, doughnut, radar, polarArea, scatter, bubble, area, mixed)
- Configuration objects (type, data, options, plugins)
- Global defaults (Chart.defaults, Chart.defaults.global v2)
- Responsive settings (responsive, maintainAspectRatio, aspectRatio)

Dataset constructs:
- Dataset definitions (label, data, styling)
- Data formats (number arrays, {x,y} objects, {x,y,r} bubble)
- Dataset styling (backgroundColor, borderColor, fill, tension, pointStyle)
- Bar/line/pie-specific options

Scale constructs:
- Scale types (linear, logarithmic, category, time, timeseries, radialLinear)
- Axis configuration (x, y, r, positions)
- Ticks (stepSize, callback, autoSkip, rotation)
- Grid lines (display, color, drawBorder)
- v2 patterns (xAxes/yAxes) vs v3+ (x/y/r)

Plugin constructs:
- Plugin registration (Chart.register, Chart.plugins.register)
- Built-in plugins (tooltip, legend, title, subtitle, filler, decimation)
- Ecosystem plugins (chartjs-plugin-datalabels, zoom, annotation, streaming)
- Custom inline plugins (id + lifecycle hooks)

API constructs:
- Import detection (chart.js, chart.js/auto, react-chartjs-2, vue-chartjs, ng2-charts)
- Version detection (v1–v4+)
- CDN patterns (cdnjs, unpkg, jsdelivr)
- TypeScript types (ChartConfiguration, ChartType, ChartData, etc.)
- Animation configuration
- Interaction configuration
- Ecosystem integrations

Framework detection (15+ Chart.js ecosystem patterns):
- Core: chart.js, chart.js/auto, chart.js/helpers
- React: react-chartjs-2
- Vue: vue-chartjs
- Angular: ng2-charts, angular-chart.js
- Svelte: svelte-chartjs
- Adapters: chartjs-adapter-date-fns, luxon, moment, dayjs
- Plugins: datalabels, zoom, annotation, streaming, gradient, crosshair
- CDN: cdnjs, unpkg, jsdelivr

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.73 - Chart.js Charting Library Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Chart.js extractors
from .extractors.chartjs import (
    ChartConfigExtractor, ChartInstanceInfo, ChartTypeInfo,
    ChartConfigInfo, ChartDefaultsInfo,
    ChartDatasetExtractor, ChartDatasetInfo, ChartDataPointInfo,
    ChartScaleExtractor, ChartScaleInfo, ChartAxisInfo,
    ChartPluginExtractor, ChartPluginInfo, ChartPluginRegistrationInfo,
    ChartAPIExtractor, ChartImportInfo, ChartIntegrationInfo,
    ChartTypeDefinitionInfo,
)


@dataclass
class ChartJSParseResult:
    """Complete parse result for a Chart.js file."""
    file_path: str
    file_type: str = "js"  # js, jsx, ts, tsx, html

    # Chart configuration
    instances: List[ChartInstanceInfo] = field(default_factory=list)
    chart_types: List[ChartTypeInfo] = field(default_factory=list)
    configs: List[ChartConfigInfo] = field(default_factory=list)
    defaults: List[ChartDefaultsInfo] = field(default_factory=list)

    # Datasets
    datasets: List[ChartDatasetInfo] = field(default_factory=list)
    data_points: List[ChartDataPointInfo] = field(default_factory=list)

    # Scales
    scales: List[ChartScaleInfo] = field(default_factory=list)
    axis_features: List[ChartAxisInfo] = field(default_factory=list)

    # Plugins
    plugins: List[ChartPluginInfo] = field(default_factory=list)
    registrations: List[ChartPluginRegistrationInfo] = field(default_factory=list)

    # API
    imports: List[ChartImportInfo] = field(default_factory=list)
    integrations: List[ChartIntegrationInfo] = field(default_factory=list)
    types: List[ChartTypeDefinitionInfo] = field(default_factory=list)
    animations: List[Dict] = field(default_factory=list)
    interactions: List[Dict] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    chartjs_version: str = ""  # detected Chart.js version ('v1', 'v2', 'v3', 'v4')
    is_tree_shakeable: bool = False  # chart.js tree-shakeable imports (v3+)
    is_auto: bool = False  # chart.js/auto (auto-registration)
    has_animation: bool = False  # animation configuration
    has_interaction: bool = False  # interaction configuration
    has_typescript: bool = False  # TypeScript types


class EnhancedChartJSParser:
    """
    Enhanced Chart.js parser using all extractors.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when Chart.js is detected. It extracts charting-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 15+ Chart.js ecosystem libraries across:
    - Core (chart.js, chart.js/auto, chart.js/helpers)
    - React (react-chartjs-2)
    - Vue (vue-chartjs)
    - Angular (ng2-charts, angular-chart.js)
    - Svelte (svelte-chartjs)
    - Adapters (chartjs-adapter-date-fns, chartjs-adapter-luxon, etc.)
    - Plugins (chartjs-plugin-datalabels, chartjs-plugin-zoom, etc.)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Chart.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'chart.js': re.compile(
            r"from\s+['\"]chart\.js['\"]|require\(['\"]chart\.js['\"]\)|"
            r"import\s+Chart\s+from|new\s+Chart\s*\(|"
            r"<script[^>]*chart(?:\.min)?\.js",
            re.MULTILINE
        ),
        'chart.js/auto': re.compile(
            r"from\s+['\"]chart\.js/auto['\"]|"
            r"require\(['\"]chart\.js/auto['\"]\)",
            re.MULTILINE
        ),
        'chart.js/helpers': re.compile(
            r"from\s+['\"]chart\.js/helpers['\"]|"
            r"Chart\.helpers\.\w+",
            re.MULTILINE
        ),

        # ── React ─────────────────────────────────────────────────
        'react-chartjs-2': re.compile(
            r"from\s+['\"]react-chartjs-2['\"]|"
            r"<(?:Line|Bar|Pie|Doughnut|Radar|PolarArea|Scatter|Bubble|Chart)\b",
            re.MULTILINE
        ),

        # ── Vue ───────────────────────────────────────────────────
        'vue-chartjs': re.compile(
            r"from\s+['\"]vue-chartjs['\"]|"
            r"extends\s+(?:Line|Bar|Pie|Doughnut|Radar|PolarArea|Scatter|Bubble|HorizontalBar)",
            re.MULTILINE
        ),

        # ── Angular ───────────────────────────────────────────────
        'ng2-charts': re.compile(
            r"from\s+['\"]ng2-charts['\"]|NgChartsModule|baseChart",
            re.MULTILINE
        ),
        'angular-chart.js': re.compile(
            r"from\s+['\"]angular-chart\.js['\"]|"
            r"angular\.module\s*\([^)]*['\"]chart\.js['\"]",
            re.MULTILINE
        ),

        # ── Svelte ────────────────────────────────────────────────
        'svelte-chartjs': re.compile(
            r"from\s+['\"]svelte-chartjs['\"]",
            re.MULTILINE
        ),

        # ── Date Adapters (support bare import, from, require) ────
        'chartjs-adapter-date-fns': re.compile(
            r"(?:import|from)\s+['\"]chartjs-adapter-date-fns['\"]|"
            r"require\(['\"]chartjs-adapter-date-fns['\"]\)",
            re.MULTILINE
        ),
        'chartjs-adapter-luxon': re.compile(
            r"(?:import|from)\s+['\"]chartjs-adapter-luxon['\"]|"
            r"require\(['\"]chartjs-adapter-luxon['\"]\)",
            re.MULTILINE
        ),
        'chartjs-adapter-moment': re.compile(
            r"(?:import|from)\s+['\"]chartjs-adapter-moment['\"]|"
            r"require\(['\"]chartjs-adapter-moment['\"]\)",
            re.MULTILINE
        ),
        'chartjs-adapter-dayjs': re.compile(
            r"(?:import|from)\s+['\"]chartjs-adapter-dayjs['\"]|"
            r"require\(['\"]chartjs-adapter-dayjs['\"]\)",
            re.MULTILINE
        ),

        # ── Plugins ───────────────────────────────────────────────
        'chartjs-plugin-datalabels': re.compile(
            r"from\s+['\"]chartjs-plugin-datalabels['\"]|"
            r"require\(['\"]chartjs-plugin-datalabels['\"]\)|"
            r"ChartDataLabels",
            re.MULTILINE
        ),
        'chartjs-plugin-zoom': re.compile(
            r"from\s+['\"]chartjs-plugin-zoom['\"]|"
            r"require\(['\"]chartjs-plugin-zoom['\"]\)",
            re.MULTILINE
        ),
        'chartjs-plugin-annotation': re.compile(
            r"from\s+['\"]chartjs-plugin-annotation['\"]|"
            r"require\(['\"]chartjs-plugin-annotation['\"]\)",
            re.MULTILINE
        ),
        'chartjs-plugin-streaming': re.compile(
            r"from\s+['\"]chartjs-plugin-streaming['\"]|"
            r"require\(['\"]chartjs-plugin-streaming['\"]\)",
            re.MULTILINE
        ),
    }

    def __init__(self):
        """Initialize the parser with all Chart.js extractors."""
        self.config_extractor = ChartConfigExtractor()
        self.dataset_extractor = ChartDatasetExtractor()
        self.scale_extractor = ChartScaleExtractor()
        self.plugin_extractor = ChartPluginExtractor()
        self.api_extractor = ChartAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> ChartJSParseResult:
        """
        Parse Chart.js source code and extract all charting-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Chart.js is detected. It extracts chart configurations, datasets,
        scales, plugins, and API usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ChartJSParseResult with all extracted information
        """
        result = ChartJSParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        elif file_path.endswith('.html'):
            result.file_type = "html"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract chart config constructs ───────────────────────
        config_result = self.config_extractor.extract(content, file_path)
        result.instances = config_result.get('instances', [])
        result.chart_types = config_result.get('chart_types', [])
        result.configs = config_result.get('configs', [])
        result.defaults = config_result.get('defaults', [])

        # ── Extract dataset constructs ────────────────────────────
        dataset_result = self.dataset_extractor.extract(content, file_path)
        result.datasets = dataset_result.get('datasets', [])
        result.data_points = dataset_result.get('data_points', [])

        # ── Extract scale constructs ──────────────────────────────
        scale_result = self.scale_extractor.extract(content, file_path)
        result.scales = scale_result.get('scales', [])
        result.axis_features = scale_result.get('axis_features', [])

        # ── Extract plugin constructs ─────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.registrations = plugin_result.get('registrations', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])
        result.animations = api_result.get('animations', [])
        result.interactions = api_result.get('interactions', [])

        # Framework info from API extractor
        fw_info = api_result.get('framework_info', {})
        result.is_tree_shakeable = fw_info.get('is_tree_shakeable', False)
        result.is_auto = fw_info.get('is_auto', False)
        result.has_animation = fw_info.get('has_animation', False)
        result.has_interaction = fw_info.get('has_interaction', False)
        result.has_typescript = fw_info.get('has_typescript', False)
        result.detected_features = fw_info.get('features', [])
        result.chartjs_version = fw_info.get('detected_version', '')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Chart.js ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_chartjs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Chart.js code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Chart.js code
        """
        # Check for Chart.js imports (ES module)
        if re.search(r"from\s+['\"]chart\.js(?:/auto)?['\"]", content):
            return True

        # Check for Chart constructor
        if re.search(r'new\s+Chart\s*\(', content):
            return True

        # Check for import Chart from 'chart.js'
        if re.search(r"import\s+Chart\s+from\s+['\"]chart\.js", content):
            return True

        # Check for require('chart.js')
        if re.search(r"require\s*\(\s*['\"]chart\.js(?:/auto)?['\"]\s*\)", content):
            return True

        # Check for react-chartjs-2 imports
        if re.search(r"from\s+['\"]react-chartjs-2['\"]", content):
            return True

        # Check for vue-chartjs imports
        if re.search(r"from\s+['\"]vue-chartjs['\"]", content):
            return True

        # Check for ng2-charts
        if re.search(r"from\s+['\"]ng2-charts['\"]|NgChartsModule|baseChart", content):
            return True

        # Check for Chart.js CDN script tags
        if re.search(r'chart(?:\.min)?\.js', content, re.IGNORECASE):
            # More specific: check for known CDN patterns
            if re.search(
                r'cdn\.jsdelivr\.net/npm/chart\.js|'
                r'cdnjs\.cloudflare\.com/ajax/libs/Chart\.js|'
                r'unpkg\.com/chart\.js',
                content
            ):
                return True

        # Check for Chart.register (v3+)
        if re.search(r'Chart\.register\s*\(', content):
            return True

        # Check for Chart.defaults
        if re.search(r'Chart\.defaults\.', content):
            return True

        # Check for chartjs-plugin-* imports
        if re.search(r"(?:import|from)\s+['\"]chartjs-plugin-|require\(['\"]chartjs-plugin-", content):
            return True

        # Check for chartjs-adapter-* imports (bare import, from, or require)
        if re.search(r"(?:import|from)\s+['\"]chartjs-adapter-|require\(['\"]chartjs-adapter-", content):
            return True

        # Check for svelte-chartjs
        if re.search(r"(?:import|from)\s+['\"]svelte-chartjs['\"]", content):
            return True

        # Check for angular-chart.js
        if re.search(r"(?:import|from)\s+['\"]angular-chart\.js['\"]", content):
            return True

        return False
