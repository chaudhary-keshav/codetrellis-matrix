"""
Recharts API Extractor

Extracts API-level constructs:
- Import detection (recharts, recharts/es6, recharts/lib, @types/recharts)
- Version detection (v1 patterns, v2+ patterns)
- TypeScript type usage (from recharts types)
- Ecosystem integrations (recharts-scale, recharts-to-png, etc.)
- Custom hook patterns (useChart-related patterns)
- Bare import support (import 'recharts')
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RechartsImportInfo:
    """Recharts import statement."""
    name: str  # package name
    file: str
    line_number: int
    import_type: str  # 'module_default', 'module_named', 'module_namespace', 'require', 'bare'
    package: str = ""  # 'recharts', 'recharts/es6', etc.
    symbols: List[str] = field(default_factory=list)  # imported symbols
    is_tree_shakeable: bool = False  # direct recharts imports (always tree-shakeable)


@dataclass
class RechartsIntegrationInfo:
    """Recharts ecosystem integration."""
    name: str  # library name
    file: str
    line_number: int
    integration_type: str  # 'scale', 'export', 'animation', 'responsive', 'plugin'
    library: str = ""


@dataclass
class RechartsTypeInfo:
    """TypeScript type for Recharts."""
    name: str
    file: str
    line_number: int
    type_source: str  # 'recharts', '@types/recharts', 'custom'
    type_category: str = ""  # 'chart', 'data', 'axis', 'tooltip', 'legend', 'event', 'other'


class RechartsAPIExtractor:
    """Extracts Recharts API-level constructs."""

    # ── Recharts packages ─────────────────────────────────────────
    RECHARTS_PACKAGES = [
        'recharts',
        'recharts/es6',
        'recharts/lib',
        'recharts-scale',
        'recharts-to-png',
        'd3-scale',  # commonly paired
    ]

    # ── Import patterns ───────────────────────────────────────────
    # ES module named: import { LineChart, Line, XAxis } from 'recharts'
    NAMED_IMPORT_PATTERN = re.compile(
        r'import\s*\{([^}]+)\}\s*from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module namespace: import * as Recharts from 'recharts'
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r'import\s*\*\s*as\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # ES module default: import Recharts from 'recharts'
    DEFAULT_IMPORT_PATTERN = re.compile(
        r'import\s+(\w+)\s+from\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    # CommonJS: const { LineChart, Line } = require('recharts')
    REQUIRE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    # Bare import: import 'recharts'
    BARE_IMPORT_PATTERN = re.compile(
        r"""import\s+['"]recharts(?:/[^'"]*)?['"]""",
        re.MULTILINE
    )
    # Dynamic import: const recharts = await import('recharts')
    DYNAMIC_IMPORT_PATTERN = re.compile(
        r"""(?:import|require)\s*\(\s*['"]recharts(?:/[^'"]*)?['"]\s*\)""",
        re.MULTILINE
    )

    # ── Version detection patterns ────────────────────────────────
    # v1 patterns: different API surface, no hooks support
    V1_PATTERNS = re.compile(
        r'(?:ResponsiveContainer\s*(?:width|height)\s*=\s*\d+%?|'
        r'CartesianGrid\s+strokeDasharray)',
        re.MULTILINE
    )
    # v2+ patterns: improved TypeScript support, new components
    V2_PATTERNS = re.compile(
        r'(?:ComposedChart|FunnelChart|Sankey|'
        r'isAnimationActive|animationDuration|'
        r'allowEscapeViewBox|'
        r'from\s*["\']recharts["\'])',
        re.MULTILINE
    )

    # ── Ecosystem integration patterns ────────────────────────────
    ECOSYSTEM_PATTERNS = {
        'recharts-scale': re.compile(
            r"""from\s+['"]recharts-scale['"]|require\s*\(\s*['"]recharts-scale['"]""",
            re.MULTILINE
        ),
        'recharts-to-png': re.compile(
            r"""from\s+['"]recharts-to-png['"]|require\s*\(\s*['"]recharts-to-png['"]""",
            re.MULTILINE
        ),
        'd3-scale': re.compile(
            r"""from\s+['"]d3-scale['"]|require\s*\(\s*['"]d3-scale['"]""",
            re.MULTILINE
        ),
        'd3-shape': re.compile(
            r"""from\s+['"]d3-shape['"]|require\s*\(\s*['"]d3-shape['"]""",
            re.MULTILINE
        ),
        'd3-format': re.compile(
            r"""from\s+['"]d3-format['"]|require\s*\(\s*['"]d3-format['"]""",
            re.MULTILINE
        ),
        'd3-time-format': re.compile(
            r"""from\s+['"]d3-time-format['"]|require\s*\(\s*['"]d3-time-format['"]""",
            re.MULTILINE
        ),
    }

    # ── TypeScript type patterns ──────────────────────────────────
    RECHARTS_TYPE_PATTERN = re.compile(
        r'(?:LineChartProps|BarChartProps|AreaChartProps|PieChartProps|'
        r'RadarChartProps|ScatterChartProps|ComposedChartProps|'
        r'ResponsiveContainerProps|XAxisProps|YAxisProps|ZAxisProps|'
        r'TooltipProps|LegendProps|CartesianGridProps|'
        r'LineProps|BarProps|AreaProps|ScatterProps|PieProps|RadarProps|'
        r'ReferenceLineProps|ReferenceAreaProps|ReferenceDotProps|'
        r'BrushProps|LabelProps|LabelListProps|ErrorBarProps|'
        r'CellProps|CrossProps|SectorProps|CurveProps|'
        r'RadialBarProps|RadialBarChartProps|TreemapProps|'
        r'FunnelChartProps|FunnelProps|SankeyProps|'
        r'PolarGridProps|PolarAngleAxisProps|PolarRadiusAxisProps|'
        r'ActiveShape|Payload|ContentType|'
        r'CategoricalChartState|ChartOffset|TickItem|'
        r'AxisDomain|DataKey|AxisType|ScaleType|StackOffsetType|'
        r'BaseAxisProps|CartesianAxisProps|'
        r'AnimationTiming|LegendType|IconType|'
        r'TooltipPayload|ValueType|NameType)<',
        re.MULTILINE
    )
    TYPES_RECHARTS_IMPORT = re.compile(
        r"import\s+(?:type\s+)?\{[^}]*\}\s*from\s*['\"]recharts",
        re.MULTILINE
    )

    # ── Hook patterns ─────────────────────────────────────────────
    CUSTOM_HOOK_PATTERN = re.compile(
        r'\buse(?:Chart|Recharts|Tooltip|Legend|Animation|Brush)\w*\s*[=(]',
        re.MULTILINE
    )

    # ── Known Recharts component names for detection ──────────────
    ALL_RECHARTS_COMPONENTS = {
        'LineChart', 'BarChart', 'AreaChart', 'PieChart', 'RadarChart',
        'ScatterChart', 'ComposedChart', 'RadialBarChart', 'Treemap',
        'FunnelChart', 'Sankey', 'ResponsiveContainer',
        'Line', 'Bar', 'Area', 'Scatter', 'Pie', 'Radar', 'RadialBar',
        'XAxis', 'YAxis', 'ZAxis', 'CartesianGrid',
        'PolarGrid', 'PolarAngleAxis', 'PolarRadiusAxis',
        'Tooltip', 'Legend', 'Brush',
        'ReferenceLine', 'ReferenceArea', 'ReferenceDot',
        'ErrorBar', 'Label', 'LabelList', 'Cell',
        'Customized', 'Cross', 'Sector', 'Curve',
    }

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API-level constructs from Recharts code."""
        result: Dict[str, Any] = {
            'imports': [],
            'integrations': [],
            'types': [],
            'framework_info': {
                'is_v1': False,
                'is_v2_plus': False,
                'is_tree_shakeable': False,
                'has_animation': False,
                'has_typescript': False,
                'recharts_version': '',
                'features': [],
                'detected_frameworks': [],
            },
        }

        # ── Named imports ────────────────────────────────────────
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            symbols_str = match.group(1)
            package = match.group(2)
            if not self._is_recharts_package(package):
                continue
            symbols = [s.strip().split(' as ')[0].strip() for s in symbols_str.split(',')]
            symbols = [s for s in symbols if s]
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(RechartsImportInfo(
                name=package,
                file=file_path,
                line_number=line_num,
                import_type='module_named',
                package=package,
                symbols=symbols[:30],
                is_tree_shakeable=True,
            ))

        # ── Namespace imports ────────────────────────────────────
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_recharts_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(RechartsImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_namespace',
                package=package,
                symbols=[alias],
            ))

        # ── Default imports ──────────────────────────────────────
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            package = match.group(2)
            if not self._is_recharts_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(RechartsImportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                import_type='module_default',
                package=package,
                symbols=[alias],
            ))

        # ── CommonJS require ─────────────────────────────────────
        for match in self.REQUIRE_PATTERN.finditer(content):
            destructured = match.group(1)
            alias = match.group(2)
            package = match.group(3)
            if not self._is_recharts_package(package):
                continue
            line_num = content[:match.start()].count('\n') + 1
            symbols = []
            if destructured:
                symbols = [s.strip() for s in destructured.split(',') if s.strip()]
            elif alias:
                symbols = [alias]
            result['imports'].append(RechartsImportInfo(
                name=alias or package,
                file=file_path,
                line_number=line_num,
                import_type='require',
                package=package,
                symbols=symbols[:30],
            ))

        # ── Bare imports ─────────────────────────────────────────
        for match in self.BARE_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Only add if not already captured by other patterns
            result['imports'].append(RechartsImportInfo(
                name='recharts_bare',
                file=file_path,
                line_number=line_num,
                import_type='bare',
                package='recharts',
            ))

        # ── Dynamic imports ──────────────────────────────────────
        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(RechartsImportInfo(
                name='recharts_dynamic',
                file=file_path,
                line_number=line_num,
                import_type='dynamic',
                package='recharts',
            ))

        # ── Ecosystem integrations ───────────────────────────────
        for lib_name, pattern in self.ECOSYSTEM_PATTERNS.items():
            if pattern.search(content):
                match = pattern.search(content)
                line_num = content[:match.start()].count('\n') + 1
                integration_type = self._classify_integration(lib_name)
                result['integrations'].append(RechartsIntegrationInfo(
                    name=lib_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=integration_type,
                    library=lib_name,
                ))

        # ── TypeScript types ─────────────────────────────────────
        for match in self.RECHARTS_TYPE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            type_name = match.group(0).rstrip('<')
            category = self._classify_type(type_name)
            result['types'].append(RechartsTypeInfo(
                name=type_name,
                file=file_path,
                line_number=line_num,
                type_source='recharts',
                type_category=category,
            ))

        if self.TYPES_RECHARTS_IMPORT.search(content):
            match = self.TYPES_RECHARTS_IMPORT.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['types'].append(RechartsTypeInfo(
                name='recharts_types',
                file=file_path,
                line_number=line_num,
                type_source='recharts',
                type_category='package',
            ))

        # ── Version detection ────────────────────────────────────
        fw_info = result['framework_info']
        features: List[str] = []
        detected_frameworks: List[str] = []

        if self.V1_PATTERNS.search(content):
            fw_info['is_v1'] = True
            features.append('v1_compat')

        if self.V2_PATTERNS.search(content):
            fw_info['is_v2_plus'] = True
            fw_info['recharts_version'] = 'v2'
            features.append('v2_api')

        # Recharts is always tree-shakeable
        if result['imports']:
            fw_info['is_tree_shakeable'] = True
            features.append('tree_shakeable')

        # TypeScript detection
        fw_info['has_typescript'] = bool(result['types'])
        if result['types']:
            features.append('typescript')

        # Detect hooks
        if self.CUSTOM_HOOK_PATTERN.search(content):
            features.append('hooks')

        # Ecosystem features
        for integration in result['integrations']:
            detected_frameworks.append(integration.library)
            features.append(f"integration_{integration.library.replace('-', '_')}")

        fw_info['features'] = features
        fw_info['detected_frameworks'] = detected_frameworks

        return result

    def _is_recharts_package(self, package: str) -> bool:
        """Check if a package name is Recharts-related."""
        if package in ('recharts', 'recharts/es6', 'recharts/lib'):
            return True
        if package.startswith('recharts/'):
            return True
        if package.startswith('recharts-'):
            return True
        return False

    @staticmethod
    def _classify_integration(lib_name: str) -> str:
        """Classify an ecosystem library."""
        if lib_name in ('recharts-scale',):
            return 'scale'
        elif lib_name in ('recharts-to-png',):
            return 'export'
        elif lib_name.startswith('d3-'):
            return 'd3_utility'
        return 'other'

    @staticmethod
    def _classify_type(type_name: str) -> str:
        """Classify a TypeScript Recharts type."""
        type_map = {
            'LineChartProps': 'chart', 'BarChartProps': 'chart',
            'AreaChartProps': 'chart', 'PieChartProps': 'chart',
            'RadarChartProps': 'chart', 'ScatterChartProps': 'chart',
            'ComposedChartProps': 'chart', 'RadialBarChartProps': 'chart',
            'TreemapProps': 'chart', 'FunnelChartProps': 'chart',
            'FunnelProps': 'chart', 'SankeyProps': 'chart',
            'ResponsiveContainerProps': 'chart',
            'LineProps': 'data', 'BarProps': 'data',
            'AreaProps': 'data', 'ScatterProps': 'data',
            'PieProps': 'data', 'RadarProps': 'data',
            'RadialBarProps': 'data', 'CellProps': 'data',
            'XAxisProps': 'axis', 'YAxisProps': 'axis', 'ZAxisProps': 'axis',
            'CartesianGridProps': 'axis', 'PolarGridProps': 'axis',
            'PolarAngleAxisProps': 'axis', 'PolarRadiusAxisProps': 'axis',
            'BaseAxisProps': 'axis', 'CartesianAxisProps': 'axis',
            'AxisDomain': 'axis', 'AxisType': 'axis',
            'DataKey': 'data', 'ScaleType': 'axis',
            'TooltipProps': 'tooltip', 'TooltipPayload': 'tooltip',
            'ValueType': 'tooltip', 'NameType': 'tooltip',
            'ContentType': 'tooltip', 'Payload': 'tooltip',
            'LegendProps': 'legend', 'LegendType': 'legend', 'IconType': 'legend',
            'BrushProps': 'interaction', 'ErrorBarProps': 'data',
            'LabelProps': 'label', 'LabelListProps': 'label',
            'ReferenceLineProps': 'annotation', 'ReferenceAreaProps': 'annotation',
            'ReferenceDotProps': 'annotation',
            'CrossProps': 'element', 'SectorProps': 'element', 'CurveProps': 'element',
            'ActiveShape': 'element',
            'CategoricalChartState': 'event', 'ChartOffset': 'event',
            'TickItem': 'axis', 'AnimationTiming': 'animation',
            'StackOffsetType': 'data',
        }
        return type_map.get(type_name, 'other')
