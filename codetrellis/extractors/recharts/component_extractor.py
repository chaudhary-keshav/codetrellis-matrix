"""
Recharts Component Extractor

Extracts React component-based chart constructs:
- Chart components (LineChart, BarChart, AreaChart, PieChart, RadarChart,
  ScatterChart, ComposedChart, RadialBarChart, Treemap, Funnel, Sankey)
- ResponsiveContainer usage (width, height, aspect, debounce)
- Chart composition patterns (composed charts with multiple series types)
- Chart dimensions (width, height, margin props)
- Nested children structure (data components inside charts)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RechartsComponentInfo:
    """Recharts chart component usage."""
    name: str  # component name, e.g. 'LineChart'
    file: str
    line_number: int
    chart_type: str  # 'line', 'bar', 'area', 'pie', 'radar', 'scatter', 'composed', 'radialBar', 'treemap', 'funnel', 'sankey'
    has_data_prop: bool = False
    has_width: bool = False
    has_height: bool = False
    has_margin: bool = False
    has_layout: bool = False  # layout='vertical'
    has_sync_id: bool = False  # syncId prop for synchronized charts
    is_responsive: bool = False  # wrapped in ResponsiveContainer
    children: List[str] = field(default_factory=list)  # nested child component names


@dataclass
class RechartsResponsiveInfo:
    """ResponsiveContainer usage."""
    name: str
    file: str
    line_number: int
    has_width: bool = False
    has_height: bool = False
    has_aspect: bool = False
    has_debounce: bool = False
    has_min_width: bool = False
    has_min_height: bool = False


class RechartsComponentExtractor:
    """Extracts Recharts chart component constructs."""

    # ── Chart component patterns ──────────────────────────────────
    CHART_COMPONENTS = {
        'LineChart': 'line',
        'BarChart': 'bar',
        'AreaChart': 'area',
        'PieChart': 'pie',
        'RadarChart': 'radar',
        'ScatterChart': 'scatter',
        'ComposedChart': 'composed',
        'RadialBarChart': 'radialBar',
        'Treemap': 'treemap',
        'FunnelChart': 'funnel',
        'Sankey': 'sankey',
    }

    # Match opening JSX tag for chart components
    CHART_COMPONENT_PATTERN = re.compile(
        r'<(LineChart|BarChart|AreaChart|PieChart|RadarChart|ScatterChart|'
        r'ComposedChart|RadialBarChart|Treemap|FunnelChart|Sankey)\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── ResponsiveContainer patterns ──────────────────────────────
    RESPONSIVE_CONTAINER_PATTERN = re.compile(
        r'<ResponsiveContainer\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── Prop patterns ─────────────────────────────────────────────
    DATA_PROP_PATTERN = re.compile(r'\bdata\s*[={]', re.MULTILINE)
    WIDTH_PROP_PATTERN = re.compile(r'\bwidth\s*[={]', re.MULTILINE)
    HEIGHT_PROP_PATTERN = re.compile(r'\bheight\s*[={]', re.MULTILINE)
    MARGIN_PROP_PATTERN = re.compile(r'\bmargin\s*[={]', re.MULTILINE)
    LAYOUT_PROP_PATTERN = re.compile(r"""\blayout\s*=\s*['"]?vertical['"]?""", re.MULTILINE)
    SYNC_ID_PROP_PATTERN = re.compile(r'\bsyncId\s*[={]', re.MULTILINE)
    ASPECT_PROP_PATTERN = re.compile(r'\baspect\s*[={]', re.MULTILINE)
    DEBOUNCE_PROP_PATTERN = re.compile(r'\bdebounce\s*[={]', re.MULTILINE)
    MIN_WIDTH_PATTERN = re.compile(r'\bminWidth\s*[={]', re.MULTILINE)
    MIN_HEIGHT_PATTERN = re.compile(r'\bminHeight\s*[={]', re.MULTILINE)

    # ── Child component detection patterns ────────────────────────
    # All possible child components that appear inside chart containers
    CHILD_COMPONENTS = [
        'Line', 'Bar', 'Area', 'Scatter', 'Pie', 'Radar', 'RadialBar',
        'XAxis', 'YAxis', 'ZAxis', 'CartesianGrid', 'PolarGrid',
        'PolarAngleAxis', 'PolarRadiusAxis',
        'Tooltip', 'Legend', 'Brush',
        'ReferenceLine', 'ReferenceArea', 'ReferenceDot',
        'ErrorBar', 'Label', 'LabelList', 'Cell',
        'Customized', 'Cross', 'Sector',
    ]
    CHILD_COMPONENT_PATTERN = re.compile(
        r'<(' + '|'.join(CHILD_COMPONENTS) + r')\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract Recharts component usage from code."""
        result: Dict[str, Any] = {
            'components': [],
            'responsive_containers': [],
        }

        # Track ResponsiveContainer positions for is_responsive detection
        responsive_ranges: List[tuple] = []
        for match in self.RESPONSIVE_CONTAINER_PATTERN.finditer(content):
            rc_start = match.start()
            # Find corresponding closing tag or estimate range
            close_tag = content.find('</ResponsiveContainer>', rc_start)
            if close_tag == -1:
                close_tag = rc_start + 2000  # estimate
            responsive_ranges.append((rc_start, close_tag))

            line_num = content[:rc_start].count('\n') + 1
            props = match.group(1) or ''
            result['responsive_containers'].append(RechartsResponsiveInfo(
                name='ResponsiveContainer',
                file=file_path,
                line_number=line_num,
                has_width=bool(self.WIDTH_PROP_PATTERN.search(props)),
                has_height=bool(self.HEIGHT_PROP_PATTERN.search(props)),
                has_aspect=bool(self.ASPECT_PROP_PATTERN.search(props)),
                has_debounce=bool(self.DEBOUNCE_PROP_PATTERN.search(props)),
                has_min_width=bool(self.MIN_WIDTH_PATTERN.search(props)),
                has_min_height=bool(self.MIN_HEIGHT_PATTERN.search(props)),
            ))

        # ── Chart components ─────────────────────────────────────
        for match in self.CHART_COMPONENT_PATTERN.finditer(content):
            comp_name = match.group(1)
            props = match.group(2) or ''
            chart_type = self.CHART_COMPONENTS.get(comp_name, 'unknown')
            line_num = content[:match.start()].count('\n') + 1

            # Find closing tag to extract children
            closing_tag = f'</{comp_name}>'
            close_pos = content.find(closing_tag, match.end())
            children = []
            if close_pos != -1:
                inner = content[match.end():close_pos]
                children = list(dict.fromkeys(
                    m.group(1) for m in self.CHILD_COMPONENT_PATTERN.finditer(inner)
                ))

            # Check if inside a ResponsiveContainer
            comp_pos = match.start()
            is_responsive = any(
                start <= comp_pos <= end for start, end in responsive_ranges
            )

            result['components'].append(RechartsComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                chart_type=chart_type,
                has_data_prop=bool(self.DATA_PROP_PATTERN.search(props)),
                has_width=bool(self.WIDTH_PROP_PATTERN.search(props)),
                has_height=bool(self.HEIGHT_PROP_PATTERN.search(props)),
                has_margin=bool(self.MARGIN_PROP_PATTERN.search(props)),
                has_layout=bool(self.LAYOUT_PROP_PATTERN.search(props)),
                has_sync_id=bool(self.SYNC_ID_PROP_PATTERN.search(props)),
                is_responsive=is_responsive,
                children=children[:20],
            ))

        return result
