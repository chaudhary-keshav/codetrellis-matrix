"""
Chart.js API Extractor

Extracts API-level constructs:
- Import detection (chart.js, chart.js/auto, react-chartjs-2, vue-chartjs,
  ng2-charts, angular-chart.js, CDN/script tags)
- Version detection (v1 patterns, v2 patterns, v3+ tree-shakeable, v4+ ESM)
- TypeScript type usage (ChartConfiguration, ChartType, ChartData, etc.)
- Ecosystem integrations (react-chartjs-2, vue-chartjs, ng2-charts, Svelte, etc.)
- Animation configuration (duration, easing, delay, loop, onProgress, onComplete)
- Interaction configuration (mode, intersect, axis)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChartImportInfo:
    """Chart.js import statement."""
    name: str  # package name
    file: str
    line_number: int
    import_type: str  # 'module_default', 'module_named', 'module_namespace', 'require', 'cdn', 'auto'
    package: str = ""  # 'chart.js', 'chart.js/auto', 'react-chartjs-2', etc.
    symbols: List[str] = field(default_factory=list)  # imported symbols
    is_tree_shakeable: bool = False  # chart.js (v3+ tree-shakeable)
    is_auto: bool = False  # chart.js/auto (auto-registration)


@dataclass
class ChartIntegrationInfo:
    """Chart.js ecosystem integration."""
    name: str  # library name
    file: str
    line_number: int
    integration_type: str  # 'react', 'vue', 'angular', 'svelte', 'web_component', 'plugin', 'adapter'
    library: str = ""  # 'react-chartjs-2', 'vue-chartjs', 'ng2-charts', etc.


@dataclass
class ChartTypeDefinitionInfo:
    """TypeScript type for Chart.js."""
    name: str  # type name
    file: str
    line_number: int
    type_source: str  # 'chart.js', '@types/chart.js', 'custom'
    type_category: str = ""  # 'config', 'data', 'options', 'scale', 'element', 'plugin', 'animation'


class ChartAPIExtractor:
    """Extracts Chart.js API-level constructs."""

    # ── Chart.js packages ─────────────────────────────────────────
    CHARTJS_PACKAGES = [
        'chart.js', 'chart.js/auto', 'chart.js/helpers',
        'react-chartjs-2', 'vue-chartjs', 'ng2-charts',
        'angular-chart.js', 'svelte-chartjs',
        'chartjs-adapter-date-fns', 'chartjs-adapter-luxon',
        'chartjs-adapter-moment', 'chartjs-adapter-dayjs',
        'chartjs-plugin-datalabels', 'chartjs-plugin-zoom',
        'chartjs-plugin-annotation', 'chartjs-plugin-streaming',
        'chartjs-plugin-gradient', 'chartjs-plugin-crosshair',
        'chartjs-plugin-deferred', 'chartjs-plugin-stacked100',
        'chartjs-plugin-dragdata', 'chartjs-plugin-colorschemes',
    ]

    # ── Import patterns ───────────────────────────────────────────
    # ES module: import { Chart, registerables } from 'chart.js'
    NAMED_IMPORT_PATTERN = re.compile(
        r'import\s*\{([^}]+)\}\s*from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module: import * as Chart from 'chart.js'
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r'import\s*\*\s*as\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module: import Chart from 'chart.js/auto'
    DEFAULT_IMPORT_PATTERN = re.compile(
        r'import\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # CommonJS: const Chart = require('chart.js')
    REQUIRE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    # CDN / script tag patterns
    CDN_PATTERN = re.compile(
        r'<script\b[^>]*src\s*=\s*["\'][^"\']*chart(?:\.min)?\.js[^"\']*["\']',
        re.MULTILINE | re.IGNORECASE
    )
    CDN_URL_PATTERN = re.compile(
        r'(?:cdn\.jsdelivr\.net/npm/chart\.js|'
        r'cdnjs\.cloudflare\.com/ajax/libs/Chart\.js|'
        r'unpkg\.com/chart\.js)',
        re.MULTILINE
    )

    # ── Version detection patterns ────────────────────────────────
    # v1 patterns: Chart.Line, Chart.Bar, Chart.Pie (constructor-based)
    V1_PATTERNS = re.compile(
        r'(?:new\s+Chart\s*\(\s*\w+\s*\)\s*\.\s*(?:Line|Bar|Pie|Doughnut|Radar|PolarArea)\s*\(|'
        r'Chart\.types\.|Chart\.defaults\.colours)',
        re.MULTILINE
    )
    # v2 patterns: Chart.defaults.global, scales.xAxes, scales.yAxes
    V2_PATTERNS = re.compile(
        r'(?:Chart\.defaults\.global|xAxes\s*:|yAxes\s*:|'
        r'Chart\.pluginService|Chart\.plugins\.register|'
        r'animateRotate\s*:|animateScale\s*:)',
        re.MULTILINE
    )
    # v3+ patterns: Chart.register, registerables, tree-shaking imports, scales.x/y
    V3_PATTERNS = re.compile(
        r'(?:Chart\.register\s*\(|registerables\b|'
        r"""from\s*['"]chart\.js['"]|"""
        r'Chart\.overrides|'
        r'interaction\s*:\s*\{|'
        r'parsing\s*:\s*\{)',
        re.MULTILINE
    )
    # v4+ patterns: ES module only, new element types
    V4_PATTERNS = re.compile(
        r"""(?:from\s*['"]chart\.js/auto['"]|"""
        r'Chart\.version\b|'
        r'decimation\s*:\s*\{)',
        re.MULTILINE
    )

    # ── Ecosystem integration patterns ────────────────────────────
    ECOSYSTEM_PATTERNS = {
        # React
        'react-chartjs-2': re.compile(
            r"""from\s+['"]react-chartjs-2['"]""",
            re.MULTILINE
        ),
        # Vue
        'vue-chartjs': re.compile(
            r"""from\s+['"]vue-chartjs['"]""",
            re.MULTILINE
        ),
        # Angular
        'ng2-charts': re.compile(
            r"""from\s+['"]ng2-charts['"]|NgChartsModule""",
            re.MULTILINE
        ),
        'angular-chart.js': re.compile(
            r"""from\s+['"]angular-chart\.js['"]|angular\.module\s*\([^)]*['"]chart\.js['"]""",
            re.MULTILINE
        ),
        # Svelte
        'svelte-chartjs': re.compile(
            r"""from\s+['"]svelte-chartjs['"]""",
            re.MULTILINE
        ),
        # Date adapters (support bare import, from...import, and require)
        'chartjs-adapter-date-fns': re.compile(
            r"""(?:import|from)\s+['"]chartjs-adapter-date-fns['"]|require\s*\(\s*['"]chartjs-adapter-date-fns['"]""",
            re.MULTILINE
        ),
        'chartjs-adapter-luxon': re.compile(
            r"""(?:import|from)\s+['"]chartjs-adapter-luxon['"]|require\s*\(\s*['"]chartjs-adapter-luxon['"]""",
            re.MULTILINE
        ),
        'chartjs-adapter-moment': re.compile(
            r"""(?:import|from)\s+['"]chartjs-adapter-moment['"]|require\s*\(\s*['"]chartjs-adapter-moment['"]""",
            re.MULTILINE
        ),
        'chartjs-adapter-dayjs': re.compile(
            r"""(?:import|from)\s+['"]chartjs-adapter-dayjs['"]|require\s*\(\s*['"]chartjs-adapter-dayjs['"]""",
            re.MULTILINE
        ),
    }

    # ── Animation patterns ────────────────────────────────────────
    ANIMATION_PATTERN = re.compile(
        r'animation\s*:\s*\{',
        re.MULTILINE
    )
    ANIMATION_OPTIONS_PATTERN = re.compile(
        r'(duration|easing|delay|loop|onProgress|onComplete|'
        r'animateRotate|animateScale|numbers|colors)\s*:',
        re.MULTILINE
    )
    ANIMATIONS_PATTERN = re.compile(
        r'animations\s*:\s*\{',
        re.MULTILINE
    )
    TRANSITIONS_PATTERN = re.compile(
        r'transitions\s*:\s*\{',
        re.MULTILINE
    )
    ANIMATION_DISABLED = re.compile(
        r'animation\s*:\s*false',
        re.MULTILINE
    )

    # ── Interaction patterns ──────────────────────────────────────
    INTERACTION_PATTERN = re.compile(
        r'interaction\s*:\s*\{',
        re.MULTILINE
    )
    INTERACTION_MODE_PATTERN = re.compile(
        r"""mode\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )
    HOVER_PATTERN = re.compile(
        r'hover\s*:\s*\{',
        re.MULTILINE
    )
    ONCLICK_PATTERN = re.compile(
        r'onClick\s*:',
        re.MULTILINE
    )
    ONHOVER_PATTERN = re.compile(
        r'onHover\s*:',
        re.MULTILINE
    )

    # ── TypeScript type patterns ──────────────────────────────────
    CHARTJS_TYPE_PATTERN = re.compile(
        r'(?:ChartConfiguration|ChartType|ChartData|ChartOptions|'
        r'ChartDataset|ChartArea|ChartEvent|ChartTypeRegistry|'
        r'ScaleType|Scale|ScaleOptions|ScaleOptionsByType|'
        r'Plugin|PluginOptionsByType|PluginChartOptions|'
        r'TooltipItem|LegendItem|LegendElement|'
        r'Element|PointElement|BarElement|LineElement|ArcElement|'
        r'AnimationSpec|AnimationOptions|'
        r'CartesianScaleOptions|RadialLinearScaleOptions|'
        r'LinearScaleOptions|LogarithmicScaleOptions|'
        r'TimeScaleOptions|CategoryScaleOptions|'
        r'CoreChartOptions|ElementChartOptions|'
        r'DatasetChartOptions|ScaleChartOptions|'
        r'PluginChartOptions|FillerControllerDatasetOptions|'
        r'InteractionOptions|LayoutOptions|'
        r'BubbleDataPoint|ScatterDataPoint)<',
        re.MULTILINE
    )
    TYPES_CHARTJS_IMPORT = re.compile(
        r"import\s+(?:type\s+)?\{[^}]*\}\s*from\s*['\"](?:chart\.js|@types/chart\.js)",
        re.MULTILINE
    )

    # ── Chart.js helper utilities ─────────────────────────────────
    HELPERS_PATTERN = re.compile(
        r"""from\s+['"]chart\.js/helpers['"]|"""
        r'Chart\.helpers\.\w+',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API-level constructs from Chart.js code."""
        result: Dict[str, Any] = {
            'imports': [],
            'integrations': [],
            'types': [],
            'animations': [],
            'interactions': [],
            'framework_info': {
                'is_v1': False,
                'is_v2': False,
                'is_v3_plus': False,
                'is_v4_plus': False,
                'is_tree_shakeable': False,
                'is_auto': False,
                'has_animation': False,
                'has_interaction': False,
                'has_typescript': False,
                'features': [],
                'detected_version': '',
            },
        }

        # ── Imports ──────────────────────────────────────────────
        # Named imports: import { Chart, registerables } from 'chart.js'
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            symbols_str = match.group(1)
            package = match.group(2)
            if not self._is_chartjs_package(package):
                continue
            symbols = [s.strip().split(' as ')[0].strip() for s in symbols_str.split(',')]
            symbols = [s for s in symbols if s]
            line_num = content[:match.start()].count('\n') + 1
            is_auto = package == 'chart.js/auto'
            is_tree_shakeable = package == 'chart.js' and not is_auto
            result['imports'].append(ChartImportInfo(
                name=package,
                file=file_path,
                line_number=line_num,
                import_type='module_named',
                package=package,
                symbols=symbols[:20],
                is_tree_shakeable=is_tree_shakeable,
                is_auto=is_auto,
            ))

        # Namespace imports: import * as Chart from 'chart.js'
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_chartjs_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(ChartImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_namespace',
                package=package,
                symbols=[alias],
                is_tree_shakeable=package == 'chart.js',
                is_auto=package == 'chart.js/auto',
            ))

        # Default imports: import Chart from 'chart.js/auto'
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_chartjs_package(package):
                continue
            # Skip if already matched as named/namespace
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(ChartImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_default',
                package=package,
                symbols=[alias],
                is_tree_shakeable=package == 'chart.js',
                is_auto=package == 'chart.js/auto',
            ))

        # CommonJS require
        for match in self.REQUIRE_PATTERN.finditer(content):
            destructured = match.group(1)
            alias = match.group(2)
            package = match.group(3)
            if not self._is_chartjs_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            symbols = []
            if destructured:
                symbols = [s.strip() for s in destructured.split(',') if s.strip()]
            elif alias:
                symbols = [alias]
            result['imports'].append(ChartImportInfo(
                name=alias or package,
                file=file_path,
                line_number=line_num,
                import_type='require',
                package=package,
                symbols=symbols[:20],
            ))

        # CDN / script tags
        for match in self.CDN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(ChartImportInfo(
                name='chart_js_cdn',
                file=file_path,
                line_number=line_num,
                import_type='cdn',
                package='chart.js',
            ))

        # CDN URLs in code (not script tags)
        for match in self.CDN_URL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Avoid duplicating if already matched as CDN script tag
            result['imports'].append(ChartImportInfo(
                name='chart_js_cdn_url',
                file=file_path,
                line_number=line_num,
                import_type='cdn',
                package='chart.js',
            ))

        # ── Ecosystem integrations ───────────────────────────────
        for lib_name, pattern in self.ECOSYSTEM_PATTERNS.items():
            if pattern.search(content):
                match = pattern.search(content)
                line_num = content[:match.start()].count('\n') + 1
                integration_type = self._classify_integration(lib_name)
                result['integrations'].append(ChartIntegrationInfo(
                    name=lib_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=integration_type,
                    library=lib_name,
                ))

        # ── TypeScript types ─────────────────────────────────────
        for match in self.CHARTJS_TYPE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            type_name = match.group(0).rstrip('<')
            category = self._classify_type(type_name)
            result['types'].append(ChartTypeDefinitionInfo(
                name=type_name,
                file=file_path,
                line_number=line_num,
                type_source='chart.js',
                type_category=category,
            ))

        if self.TYPES_CHARTJS_IMPORT.search(content):
            match = self.TYPES_CHARTJS_IMPORT.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['types'].append(ChartTypeDefinitionInfo(
                name='chart.js_types',
                file=file_path,
                line_number=line_num,
                type_source='chart.js',
                type_category='package',
            ))

        # ── Animation detection ──────────────────────────────────
        if self.ANIMATION_PATTERN.search(content):
            match = self.ANIMATION_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 500]
            options = [m.group(1) for m in self.ANIMATION_OPTIONS_PATTERN.finditer(after)]
            result['animations'].append({
                'type': 'animation',
                'file': file_path,
                'line': line_num,
                'options': options[:10],
            })

        if self.ANIMATIONS_PATTERN.search(content):
            match = self.ANIMATIONS_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append({
                'type': 'animations',
                'file': file_path,
                'line': line_num,
            })

        if self.TRANSITIONS_PATTERN.search(content):
            match = self.TRANSITIONS_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append({
                'type': 'transitions',
                'file': file_path,
                'line': line_num,
            })

        if self.ANIMATION_DISABLED.search(content):
            match = self.ANIMATION_DISABLED.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append({
                'type': 'disabled',
                'file': file_path,
                'line': line_num,
            })

        # ── Interaction detection ────────────────────────────────
        if self.INTERACTION_PATTERN.search(content):
            match = self.INTERACTION_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 300]
            mode = ''
            mode_match = self.INTERACTION_MODE_PATTERN.search(after)
            if mode_match:
                mode = mode_match.group(1)
            result['interactions'].append({
                'type': 'interaction',
                'file': file_path,
                'line': line_num,
                'mode': mode,
            })

        if self.HOVER_PATTERN.search(content):
            match = self.HOVER_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['interactions'].append({
                'type': 'hover',
                'file': file_path,
                'line': line_num,
            })

        if self.ONCLICK_PATTERN.search(content):
            match = self.ONCLICK_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['interactions'].append({
                'type': 'onClick',
                'file': file_path,
                'line': line_num,
            })

        if self.ONHOVER_PATTERN.search(content):
            match = self.ONHOVER_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['interactions'].append({
                'type': 'onHover',
                'file': file_path,
                'line': line_num,
            })

        # ── Version detection ────────────────────────────────────
        fw_info = result['framework_info']
        features: List[str] = []

        if self.V1_PATTERNS.search(content):
            fw_info['is_v1'] = True
            fw_info['detected_version'] = 'v1'
            features.append('v1_api')

        if self.V2_PATTERNS.search(content):
            fw_info['is_v2'] = True
            fw_info['detected_version'] = 'v2'
            features.append('v2_api')

        if self.V3_PATTERNS.search(content):
            fw_info['is_v3_plus'] = True
            fw_info['detected_version'] = 'v3'
            features.append('v3_tree_shakeable')

        if self.V4_PATTERNS.search(content):
            fw_info['is_v4_plus'] = True
            fw_info['detected_version'] = 'v4'
            features.append('v4_esm')

        # Check tree-shakeable vs auto
        any_tree_shakeable = any(i.is_tree_shakeable for i in result['imports'])
        any_auto = any(i.is_auto for i in result['imports'])
        fw_info['is_tree_shakeable'] = any_tree_shakeable
        fw_info['is_auto'] = any_auto

        # Animation detection
        fw_info['has_animation'] = bool(result['animations'])
        if result['animations']:
            features.append('animation')

        # Interaction detection
        fw_info['has_interaction'] = bool(result['interactions'])
        if result['interactions']:
            features.append('interaction')

        # TypeScript detection
        fw_info['has_typescript'] = bool(result['types'])
        if result['types']:
            features.append('typescript')

        # Helpers
        if self.HELPERS_PATTERN.search(content):
            features.append('helpers')

        # Ecosystem features
        for integration in result['integrations']:
            features.append(f"integration_{integration.library.replace('-', '_')}")

        fw_info['features'] = features

        return result

    def _is_chartjs_package(self, package: str) -> bool:
        """Check if a package name is Chart.js-related."""
        if package in ('chart.js', 'chart.js/auto', 'chart.js/helpers'):
            return True
        if package.startswith('chartjs-'):
            return True
        if package in ('react-chartjs-2', 'vue-chartjs', 'ng2-charts',
                        'angular-chart.js', 'svelte-chartjs'):
            return True
        if package in ('@types/chart.js',):
            return True
        return False

    @staticmethod
    def _classify_integration(lib_name: str) -> str:
        """Classify an ecosystem library."""
        if lib_name in ('react-chartjs-2',):
            return 'react'
        elif lib_name in ('vue-chartjs',):
            return 'vue'
        elif lib_name in ('ng2-charts', 'angular-chart.js'):
            return 'angular'
        elif lib_name in ('svelte-chartjs',):
            return 'svelte'
        elif lib_name.startswith('chartjs-adapter-'):
            return 'adapter'
        elif lib_name.startswith('chartjs-plugin-'):
            return 'plugin'
        return 'other'

    @staticmethod
    def _classify_type(type_name: str) -> str:
        """Classify a TypeScript Chart.js type."""
        type_map = {
            'ChartConfiguration': 'config', 'ChartType': 'config',
            'ChartTypeRegistry': 'config',
            'ChartData': 'data', 'ChartDataset': 'data',
            'BubbleDataPoint': 'data', 'ScatterDataPoint': 'data',
            'ChartOptions': 'options', 'CoreChartOptions': 'options',
            'ElementChartOptions': 'options', 'DatasetChartOptions': 'options',
            'ScaleChartOptions': 'options', 'PluginChartOptions': 'options',
            'InteractionOptions': 'options', 'LayoutOptions': 'options',
            'ScaleType': 'scale', 'Scale': 'scale', 'ScaleOptions': 'scale',
            'ScaleOptionsByType': 'scale',
            'CartesianScaleOptions': 'scale', 'RadialLinearScaleOptions': 'scale',
            'LinearScaleOptions': 'scale', 'LogarithmicScaleOptions': 'scale',
            'TimeScaleOptions': 'scale', 'CategoryScaleOptions': 'scale',
            'Element': 'element', 'PointElement': 'element',
            'BarElement': 'element', 'LineElement': 'element', 'ArcElement': 'element',
            'Plugin': 'plugin', 'PluginOptionsByType': 'plugin',
            'TooltipItem': 'plugin', 'LegendItem': 'plugin', 'LegendElement': 'plugin',
            'AnimationSpec': 'animation', 'AnimationOptions': 'animation',
            'FillerControllerDatasetOptions': 'plugin',
            'ChartArea': 'element', 'ChartEvent': 'element',
        }
        return type_map.get(type_name, 'other')
