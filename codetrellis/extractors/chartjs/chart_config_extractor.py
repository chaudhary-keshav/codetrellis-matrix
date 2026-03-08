"""
Chart.js Chart Config Extractor

Extracts core chart configuration constructs:
- Chart instances (new Chart(ctx, config), Chart constructor)
- Chart types (line, bar, pie, doughnut, radar, polarArea, scatter, bubble, area, mixed)
- Configuration objects (type, data, options)
- Global defaults (Chart.defaults, Chart.defaults.global)
- Responsive settings (responsive, maintainAspectRatio, aspectRatio)
- Canvas context (getContext('2d'), getElementById)
- Chart lifecycle (update, destroy, reset, resize, render)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChartInstanceInfo:
    """Chart.js chart instance creation."""
    name: str  # variable name or 'anonymous'
    file: str
    line_number: int
    chart_type: str  # 'line', 'bar', 'pie', 'doughnut', 'radar', 'polarArea', 'scatter', 'bubble', 'mixed', 'unknown'
    creation_method: str  # 'constructor', 'react_component', 'vue_component', 'angular_component'
    has_options: bool = False
    has_data: bool = False
    has_plugins: bool = False
    is_responsive: bool = False
    canvas_ref: str = ""  # canvas element reference


@dataclass
class ChartTypeInfo:
    """Chart type usage."""
    name: str
    file: str
    line_number: int
    chart_type: str  # 'line', 'bar', 'pie', 'doughnut', 'radar', 'polarArea', 'scatter', 'bubble', 'area', 'mixed', 'horizontalBar'
    is_mixed: bool = False
    is_stacked: bool = False
    sub_types: List[str] = field(default_factory=list)  # for mixed charts


@dataclass
class ChartConfigInfo:
    """Chart configuration object."""
    name: str
    file: str
    line_number: int
    config_type: str  # 'inline', 'variable', 'function_return'
    has_type: bool = False
    has_data: bool = False
    has_options: bool = False
    has_plugins: bool = False
    has_responsive: bool = False
    has_animation: bool = False
    has_interaction: bool = False
    config_keys: List[str] = field(default_factory=list)


@dataclass
class ChartDefaultsInfo:
    """Chart.js global defaults modification."""
    name: str
    file: str
    line_number: int
    defaults_type: str  # 'global', 'scale', 'plugin', 'element', 'chart_type', 'font', 'color'
    property_path: str = ""  # e.g. 'Chart.defaults.font.size'
    is_v2_style: bool = False  # Chart.defaults.global (v2) vs Chart.defaults (v3+)


class ChartConfigExtractor:
    """Extracts Chart.js chart configuration constructs."""

    # ── Chart instance creation patterns ──────────────────────────
    # new Chart(ctx, { type: 'line', ... })
    NEW_CHART_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?new\s+Chart\s*\(\s*'
        r'([\w.\[\]\'\"()\s]+?)\s*,\s*\{',
        re.MULTILINE
    )

    # Chart type in config: type: 'line' or type: "bar"
    CHART_TYPE_IN_CONFIG = re.compile(
        r"""type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # Chart type in config (variable): type: chartType
    CHART_TYPE_VAR_CONFIG = re.compile(
        r'type\s*:\s*(\w+)',
        re.MULTILINE
    )

    # ── Known chart types ─────────────────────────────────────────
    CHART_TYPES = {
        'line', 'bar', 'pie', 'doughnut', 'radar', 'polarArea',
        'scatter', 'bubble', 'area', 'horizontalBar', 'mixed',
    }

    # ── React-chartjs-2 component patterns ────────────────────────
    REACT_CHART_PATTERN = re.compile(
        r'<(Line|Bar|Pie|Doughnut|Radar|PolarArea|Scatter|Bubble|Chart)\b',
        re.MULTILINE
    )

    # ── Vue-chartjs component patterns ────────────────────────────
    VUE_CHART_PATTERN = re.compile(
        r'(?:extends|mixins\s*:\s*\[)\s*(?:Line|Bar|Pie|Doughnut|Radar|PolarArea|Scatter|Bubble|HorizontalBar)',
        re.MULTILINE
    )

    # ── Angular ng2-charts patterns ───────────────────────────────
    ANGULAR_CHART_PATTERN = re.compile(
        r'(?:baseChart|canvas\s+baseChart|ChartType)',
        re.MULTILINE
    )

    # ── Global defaults patterns ──────────────────────────────────
    # v3+: Chart.defaults.font.size, Chart.defaults.color
    DEFAULTS_V3_PATTERN = re.compile(
        r'Chart\.defaults\.(\w+(?:\.\w+)*)\s*=',
        re.MULTILINE
    )
    # v2: Chart.defaults.global.defaultFontSize
    DEFAULTS_V2_PATTERN = re.compile(
        r'Chart\.defaults\.global\.(\w+)\s*=',
        re.MULTILINE
    )
    # Chart.defaults.set / Chart.overrides
    DEFAULTS_SET_PATTERN = re.compile(
        r'Chart\.(?:defaults\.set|overrides)\s*\(',
        re.MULTILINE
    )
    # Chart.defaults for specific chart type
    DEFAULTS_TYPE_PATTERN = re.compile(
        r'Chart\.defaults\.(line|bar|pie|doughnut|radar|polarArea|scatter|bubble)',
        re.MULTILINE
    )

    # ── Canvas context patterns ───────────────────────────────────
    CANVAS_GETCONTEXT = re.compile(
        r"""(?:getElementById|querySelector)\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        re.MULTILINE
    )
    CANVAS_REF_PATTERN = re.compile(
        r'(?:useRef|createRef|ref\s*=|canvasRef|chartRef)\s*[(<]',
        re.MULTILINE
    )

    # ── Chart lifecycle patterns ──────────────────────────────────
    LIFECYCLE_METHODS = re.compile(
        r'\.\s*(update|destroy|reset|resize|render|stop|clear|toBase64Image|'
        r'getDatasetMeta|getElementsAtEventForMode|getElementAtEvent)\s*\(',
        re.MULTILINE
    )

    # ── Config object detection ───────────────────────────────────
    CONFIG_KEYS_PATTERN = re.compile(
        r'(type|data|options|plugins|responsive|maintainAspectRatio|'
        r'aspectRatio|animation|interaction|scales|elements|layout)\s*:',
        re.MULTILINE
    )

    # ── Responsive patterns ───────────────────────────────────────
    RESPONSIVE_PATTERN = re.compile(
        r'responsive\s*:\s*(true|false)',
        re.MULTILINE
    )
    ASPECT_RATIO_PATTERN = re.compile(
        r'(?:maintainAspectRatio|aspectRatio)\s*:',
        re.MULTILINE
    )

    # ── Stacked chart detection ───────────────────────────────────
    STACKED_PATTERN = re.compile(
        r'stacked\s*:\s*true',
        re.MULTILINE
    )

    # ── Mixed chart type detection ────────────────────────────────
    DATASET_TYPE_PATTERN = re.compile(
        r"""datasets\s*:\s*\[[\s\S]*?type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract chart configuration from Chart.js code."""
        result: Dict[str, Any] = {
            'instances': [],
            'chart_types': [],
            'configs': [],
            'defaults': [],
        }

        # ── Chart instances (new Chart) ──────────────────────────
        for match in self.NEW_CHART_PATTERN.finditer(content):
            var_name = match.group(1) or 'anonymous'
            canvas_ref = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 1000]

            # Detect chart type
            chart_type = 'unknown'
            type_match = self.CHART_TYPE_IN_CONFIG.search(after)
            if type_match and type_match.group(1) in self.CHART_TYPES:
                chart_type = type_match.group(1)

            # Check for mixed chart types
            dataset_types = self.DATASET_TYPE_PATTERN.findall(after)
            is_mixed = len(set(dataset_types)) > 1
            if is_mixed:
                chart_type = 'mixed'

            result['instances'].append(ChartInstanceInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
                creation_method='constructor',
                has_options=bool(re.search(r'options\s*:', after)),
                has_data=bool(re.search(r'data\s*:', after)),
                has_plugins=bool(re.search(r'plugins\s*:', after)),
                is_responsive=bool(self.RESPONSIVE_PATTERN.search(after)),
                canvas_ref=canvas_ref,
            ))

            # Also record chart type
            if chart_type != 'unknown':
                result['chart_types'].append(ChartTypeInfo(
                    name=chart_type,
                    file=file_path,
                    line_number=line_num,
                    chart_type=chart_type,
                    is_mixed=is_mixed,
                    is_stacked=bool(self.STACKED_PATTERN.search(after)),
                    sub_types=list(set(dataset_types)) if is_mixed else [],
                ))

        # ── React-chartjs-2 components ───────────────────────────
        for match in self.REACT_CHART_PATTERN.finditer(content):
            component = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            chart_type = component.lower()
            if chart_type == 'polararea':
                chart_type = 'polarArea'
            elif chart_type == 'chart':
                chart_type = 'mixed'
            after = content[match.start():match.start() + 500]

            result['instances'].append(ChartInstanceInfo(
                name=component,
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
                creation_method='react_component',
                has_options=bool(re.search(r'options\s*[=:{]', after)),
                has_data=bool(re.search(r'data\s*[=:{]', after)),
                has_plugins=bool(re.search(r'plugins\s*[=:{]', after)),
            ))

            result['chart_types'].append(ChartTypeInfo(
                name=chart_type,
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
            ))

        # ── Vue-chartjs components ───────────────────────────────
        for match in self.VUE_CHART_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            component_text = match.group(0)
            chart_type = 'unknown'
            for ct in ['Line', 'Bar', 'Pie', 'Doughnut', 'Radar', 'PolarArea',
                        'Scatter', 'Bubble', 'HorizontalBar']:
                if ct in component_text:
                    chart_type = ct[0].lower() + ct[1:]
                    break

            result['instances'].append(ChartInstanceInfo(
                name=chart_type,
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
                creation_method='vue_component',
            ))

        # ── Angular ng2-charts ───────────────────────────────────
        for match in self.ANGULAR_CHART_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 500]
            chart_type = 'unknown'
            type_match = self.CHART_TYPE_IN_CONFIG.search(after)
            if type_match:
                chart_type = type_match.group(1)

            result['instances'].append(ChartInstanceInfo(
                name='ng2_chart',
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
                creation_method='angular_component',
            ))

        # ── Config object detection ──────────────────────────────
        # Look for standalone config objects with type/data/options
        config_regions = list(re.finditer(
            r'(?:const|let|var)\s+(\w*[Cc]onfig\w*|chartOptions|chartData)\s*[:=]\s*\{',
            content, re.MULTILINE
        ))
        for match in config_regions:
            var_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 1000]
            keys = [m.group(1) for m in self.CONFIG_KEYS_PATTERN.finditer(after[:600])]

            result['configs'].append(ChartConfigInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                config_type='variable',
                has_type='type' in keys,
                has_data='data' in keys,
                has_options='options' in keys,
                has_plugins='plugins' in keys,
                has_responsive='responsive' in keys,
                has_animation='animation' in keys,
                has_interaction='interaction' in keys,
                config_keys=keys[:15],
            ))

        # ── Global defaults ──────────────────────────────────────
        # v3+ defaults: Chart.defaults.font.size = 14
        for match in self.DEFAULTS_V3_PATTERN.finditer(content):
            prop_path = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Skip if it's actually a v2 global pattern
            if prop_path.startswith('global'):
                continue
            defaults_type = self._classify_defaults(prop_path)
            result['defaults'].append(ChartDefaultsInfo(
                name=prop_path,
                file=file_path,
                line_number=line_num,
                defaults_type=defaults_type,
                property_path=f"Chart.defaults.{prop_path}",
                is_v2_style=False,
            ))

        # v2 defaults: Chart.defaults.global.defaultFontSize
        for match in self.DEFAULTS_V2_PATTERN.finditer(content):
            prop = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            result['defaults'].append(ChartDefaultsInfo(
                name=prop,
                file=file_path,
                line_number=line_num,
                defaults_type='global',
                property_path=f"Chart.defaults.global.{prop}",
                is_v2_style=True,
            ))

        # Chart type defaults: Chart.defaults.line.spanGaps
        for match in self.DEFAULTS_TYPE_PATTERN.finditer(content):
            chart_type = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Avoid double-counting if already matched by V3 pattern
            result['defaults'].append(ChartDefaultsInfo(
                name=chart_type,
                file=file_path,
                line_number=line_num,
                defaults_type='chart_type',
                property_path=f"Chart.defaults.{chart_type}",
            ))

        return result

    @staticmethod
    def _classify_defaults(prop_path: str) -> str:
        """Classify a defaults property path."""
        first = prop_path.split('.')[0] if '.' in prop_path else prop_path
        if first in ('font', 'color', 'backgroundColor', 'borderColor'):
            return 'font' if first == 'font' else 'color'
        elif first in ('scale', 'scales'):
            return 'scale'
        elif first in ('plugins',):
            return 'plugin'
        elif first in ('elements',):
            return 'element'
        elif first in ('line', 'bar', 'pie', 'doughnut', 'radar', 'polarArea', 'scatter', 'bubble'):
            return 'chart_type'
        elif first in ('animation', 'animations', 'transitions'):
            return 'animation'
        elif first in ('interaction', 'hover'):
            return 'interaction'
        elif first in ('layout',):
            return 'layout'
        return 'global'
