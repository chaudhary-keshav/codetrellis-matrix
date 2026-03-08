"""
Recharts Data Extractor

Extracts data-related constructs:
- Data series components (Line, Bar, Area, Scatter, Pie, Radar, RadialBar)
- Data key usage (dataKey prop across components)
- Data formatting (formatter, tickFormatter, labelFormatter)
- Data domains (domain prop on axes)
- Cell components (individual styling for pie/bar segments)
- Data stacking (stackId prop for stacked charts)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RechartsSeriesInfo:
    """Recharts data series component (Line, Bar, Area, etc.)."""
    name: str  # component type, e.g. 'Line'
    file: str
    line_number: int
    series_type: str  # 'line', 'bar', 'area', 'scatter', 'pie', 'radar', 'radialBar'
    data_key: str = ""  # dataKey prop value
    has_name: bool = False  # name prop (legend label)
    has_type: bool = False  # type prop (e.g. 'monotone')
    has_stroke: bool = False
    has_fill: bool = False
    has_dot: bool = False
    has_active_dot: bool = False
    has_stack_id: bool = False
    stack_id: str = ""
    has_animation: bool = False
    has_label: bool = False
    has_custom_shape: bool = False  # shape prop
    has_error_bar: bool = False
    styling_props: List[str] = field(default_factory=list)


@dataclass
class RechartsDataKeyInfo:
    """dataKey prop usage across Recharts components."""
    name: str  # the dataKey value
    file: str
    line_number: int
    component: str  # which component uses it (Line, XAxis, etc.)
    key_type: str  # 'series', 'axis', 'tooltip', 'label', 'other'


@dataclass
class RechartsCellInfo:
    """Cell component usage for individual segment styling."""
    name: str
    file: str
    line_number: int
    has_fill: bool = False
    has_stroke: bool = False
    is_dynamic: bool = False  # uses map/index pattern


class RechartsDataExtractor:
    """Extracts Recharts data series and data key constructs."""

    # ── Data series component patterns ────────────────────────────
    SERIES_COMPONENTS = {
        'Line': 'line',
        'Bar': 'bar',
        'Area': 'area',
        'Scatter': 'scatter',
        'Pie': 'pie',
        'Radar': 'radar',
        'RadialBar': 'radialBar',
    }

    SERIES_PATTERN = re.compile(
        r'<(Line|Bar|Area|Scatter|Pie|Radar|RadialBar)\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── DataKey patterns ──────────────────────────────────────────
    DATAKEY_STRING_PATTERN = re.compile(
        r"""dataKey\s*=\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )
    DATAKEY_EXPR_PATTERN = re.compile(
        r'dataKey\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # ── Series prop patterns ──────────────────────────────────────
    NAME_PROP_PATTERN = re.compile(r"""\bname\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
    TYPE_PROP_PATTERN = re.compile(r"""\btype\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    STROKE_PROP_PATTERN = re.compile(r'\bstroke\s*=', re.MULTILINE)
    FILL_PROP_PATTERN = re.compile(r'\bfill\s*=', re.MULTILINE)
    DOT_PROP_PATTERN = re.compile(r'\bdot\s*=', re.MULTILINE)
    ACTIVE_DOT_PATTERN = re.compile(r'\bactiveDot\s*=', re.MULTILINE)
    STACK_ID_PATTERN = re.compile(r"""\bstackId\s*=\s*['"]?([^'">\s]+)['"]?""", re.MULTILINE)
    ANIMATION_PROP_PATTERN = re.compile(
        r'\b(?:isAnimationActive|animationDuration|animationBegin|'
        r'animationEasing|animateNewValues)\s*=',
        re.MULTILINE
    )
    LABEL_PROP_PATTERN = re.compile(r'\blabel\s*=', re.MULTILINE)
    SHAPE_PROP_PATTERN = re.compile(r'\bshape\s*=', re.MULTILINE)
    ERROR_BAR_PATTERN = re.compile(r'<ErrorBar\b', re.MULTILINE)

    # ── Styling prop names for series ─────────────────────────────
    STYLING_PROPS_PATTERN = re.compile(
        r'(stroke|fill|strokeWidth|strokeDasharray|strokeOpacity|'
        r'fillOpacity|opacity|legendType|hide|connectNulls|'
        r'unit|yAxisId|xAxisId|barSize|maxBarSize|minPointSize|'
        r'innerRadius|outerRadius|startAngle|endAngle|'
        r'cx|cy|paddingAngle)\s*=',
        re.MULTILINE
    )

    # ── Cell component pattern ────────────────────────────────────
    CELL_PATTERN = re.compile(
        r'<Cell\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    CELL_MAP_PATTERN = re.compile(
        r'\.map\s*\([^)]*\)\s*(?:=>)?\s*(?:\(?\s*)?<Cell\b',
        re.MULTILINE | re.DOTALL
    )

    # ── Formatter patterns ────────────────────────────────────────
    FORMATTER_PATTERN = re.compile(
        r'\b(?:formatter|tickFormatter|labelFormatter)\s*=',
        re.MULTILINE
    )
    DOMAIN_PATTERN = re.compile(
        r"""\bdomain\s*=\s*\{?\[""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract data series and data key constructs from Recharts code."""
        result: Dict[str, Any] = {
            'series': [],
            'data_keys': [],
            'cells': [],
        }

        # ── Data series components ───────────────────────────────
        for match in self.SERIES_PATTERN.finditer(content):
            comp_name = match.group(1)
            props = match.group(2) or ''
            series_type = self.SERIES_COMPONENTS.get(comp_name, 'unknown')
            line_num = content[:match.start()].count('\n') + 1

            # Extract dataKey
            data_key = ''
            dk_match = self.DATAKEY_STRING_PATTERN.search(props)
            if dk_match:
                data_key = dk_match.group(1)
            else:
                dk_expr = self.DATAKEY_EXPR_PATTERN.search(props)
                if dk_expr:
                    data_key = dk_expr.group(1).strip()

            # Extract stackId
            stack_id = ''
            has_stack_id = False
            sid_match = self.STACK_ID_PATTERN.search(props)
            if sid_match:
                stack_id = sid_match.group(1)
                has_stack_id = True

            # Check for ErrorBar as child
            has_error_bar = False
            if comp_name in ('Line', 'Bar', 'Area', 'Scatter'):
                close_tag = f'</{comp_name}>'
                close_pos = content.find(close_tag, match.end())
                if close_pos != -1:
                    inner = content[match.end():close_pos]
                    has_error_bar = bool(self.ERROR_BAR_PATTERN.search(inner))

            # Collect styling props
            styling_props = list(dict.fromkeys(
                m.group(1) for m in self.STYLING_PROPS_PATTERN.finditer(props)
            ))

            result['series'].append(RechartsSeriesInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                series_type=series_type,
                data_key=data_key,
                has_name=bool(self.NAME_PROP_PATTERN.search(props)),
                has_type=bool(self.TYPE_PROP_PATTERN.search(props)),
                has_stroke=bool(self.STROKE_PROP_PATTERN.search(props)),
                has_fill=bool(self.FILL_PROP_PATTERN.search(props)),
                has_dot=bool(self.DOT_PROP_PATTERN.search(props)),
                has_active_dot=bool(self.ACTIVE_DOT_PATTERN.search(props)),
                has_stack_id=has_stack_id,
                stack_id=stack_id,
                has_animation=bool(self.ANIMATION_PROP_PATTERN.search(props)),
                has_label=bool(self.LABEL_PROP_PATTERN.search(props)),
                has_custom_shape=bool(self.SHAPE_PROP_PATTERN.search(props)),
                has_error_bar=has_error_bar,
                styling_props=styling_props[:15],
            ))

            # Record dataKey usage
            if data_key:
                result['data_keys'].append(RechartsDataKeyInfo(
                    name=data_key,
                    file=file_path,
                    line_number=line_num,
                    component=comp_name,
                    key_type='series',
                ))

        # ── DataKey usage on non-series components (axes, tooltips) ──
        for dk_match in self.DATAKEY_STRING_PATTERN.finditer(content):
            dk_val = dk_match.group(1)
            line_num = content[:dk_match.start()].count('\n') + 1
            # Determine which component this belongs to
            before = content[max(0, dk_match.start() - 200):dk_match.start()]
            component = 'unknown'
            key_type = 'other'
            if '<XAxis' in before or '<YAxis' in before or '<ZAxis' in before:
                component = 'Axis'
                key_type = 'axis'
            elif '<Tooltip' in before:
                component = 'Tooltip'
                key_type = 'tooltip'
            elif '<Label' in before:
                component = 'Label'
                key_type = 'label'
            # Skip if already captured as series dataKey
            already_captured = any(
                d.name == dk_val and d.line_number == line_num
                for d in result['data_keys']
            )
            if not already_captured and key_type != 'other':
                result['data_keys'].append(RechartsDataKeyInfo(
                    name=dk_val,
                    file=file_path,
                    line_number=line_num,
                    component=component,
                    key_type=key_type,
                ))

        # ── Cell components ──────────────────────────────────────
        for match in self.CELL_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            is_dynamic = bool(self.CELL_MAP_PATTERN.search(
                content[max(0, match.start() - 200):match.end()]
            ))
            result['cells'].append(RechartsCellInfo(
                name='Cell',
                file=file_path,
                line_number=line_num,
                has_fill=bool(self.FILL_PROP_PATTERN.search(props)),
                has_stroke=bool(self.STROKE_PROP_PATTERN.search(props)),
                is_dynamic=is_dynamic,
            ))

        return result
