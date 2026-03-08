"""
Recharts Axis Extractor

Extracts axis and grid constructs:
- XAxis, YAxis, ZAxis components and configuration
- CartesianGrid configuration (strokeDasharray, horizontal, vertical)
- PolarGrid, PolarAngleAxis, PolarRadiusAxis for radar/radialBar charts
- Tick customization (tick, tickFormatter, tickLine, tickSize, tickCount)
- Axis labels and orientation
- Axis domain and range
- Multi-axis support (multiple yAxisId, xAxisId)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RechartsAxisInfo:
    """Recharts axis component configuration."""
    name: str  # 'XAxis', 'YAxis', 'ZAxis'
    file: str
    line_number: int
    axis_type: str  # 'x', 'y', 'z'
    axis_id: str = ""  # yAxisId/xAxisId value for multi-axis
    data_key: str = ""
    axis_data_type: str = ""  # type='number'|'category'
    has_tick_formatter: bool = False
    has_custom_tick: bool = False  # tick={<CustomTick />}
    has_tick_line: bool = False
    has_axis_line: bool = False
    has_label: bool = False
    has_domain: bool = False
    has_scale: bool = False  # scale='log'|'time'|'band'|'point'
    has_orientation: bool = False  # orientation='top'|'right'
    has_reversed: bool = False
    has_allow_decimals: bool = False
    has_allow_data_overflow: bool = False
    has_tick_count: bool = False
    has_interval: bool = False
    has_angle: bool = False  # angle={-45} for rotated labels
    has_padding: bool = False
    has_hide: bool = False
    config_props: List[str] = field(default_factory=list)


@dataclass
class RechartsGridInfo:
    """CartesianGrid or PolarGrid configuration."""
    name: str  # 'CartesianGrid', 'PolarGrid'
    file: str
    line_number: int
    grid_type: str  # 'cartesian', 'polar'
    has_stroke_dasharray: bool = False
    has_horizontal: bool = False
    has_vertical: bool = False
    has_fill: bool = False
    has_fill_opacity: bool = False
    has_stroke: bool = False


@dataclass
class RechartsPolarAxisInfo:
    """PolarAngleAxis or PolarRadiusAxis configuration."""
    name: str  # 'PolarAngleAxis', 'PolarRadiusAxis'
    file: str
    line_number: int
    polar_type: str  # 'angle', 'radius'
    data_key: str = ""
    has_tick: bool = False
    has_tick_formatter: bool = False
    has_domain: bool = False
    has_label: bool = False
    has_orientation: bool = False
    has_cx: bool = False
    has_cy: bool = False


class RechartsAxisExtractor:
    """Extracts Recharts axis and grid constructs."""

    # ── Cartesian Axis patterns ───────────────────────────────────
    XAXIS_PATTERN = re.compile(
        r'<XAxis\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    YAXIS_PATTERN = re.compile(
        r'<YAxis\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    ZAXIS_PATTERN = re.compile(
        r'<ZAxis\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── Grid patterns ─────────────────────────────────────────────
    CARTESIAN_GRID_PATTERN = re.compile(
        r'<CartesianGrid\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    POLAR_GRID_PATTERN = re.compile(
        r'<PolarGrid\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── Polar Axis patterns ───────────────────────────────────────
    POLAR_ANGLE_AXIS_PATTERN = re.compile(
        r'<PolarAngleAxis\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    POLAR_RADIUS_AXIS_PATTERN = re.compile(
        r'<PolarRadiusAxis\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # ── Prop patterns ─────────────────────────────────────────────
    DATAKEY_PATTERN = re.compile(r"""dataKey\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
    AXIS_TYPE_PATTERN = re.compile(r"""\btype\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    TICK_FORMATTER_PATTERN = re.compile(r'\btickFormatter\s*=', re.MULTILINE)
    CUSTOM_TICK_PATTERN = re.compile(r'\btick\s*=\s*\{', re.MULTILINE)
    TICK_LINE_PATTERN = re.compile(r'\btickLine\s*=', re.MULTILINE)
    AXIS_LINE_PATTERN = re.compile(r'\baxisLine\s*=', re.MULTILINE)
    LABEL_PATTERN = re.compile(r'\blabel\s*=', re.MULTILINE)
    DOMAIN_PATTERN = re.compile(r'\bdomain\s*=', re.MULTILINE)
    SCALE_PATTERN = re.compile(r"""\bscale\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    ORIENTATION_PATTERN = re.compile(r"""\borientation\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    REVERSED_PATTERN = re.compile(r'\breversed\b', re.MULTILINE)
    ALLOW_DECIMALS_PATTERN = re.compile(r'\ballowDecimals\s*=', re.MULTILINE)
    ALLOW_DATA_OVERFLOW_PATTERN = re.compile(r'\ballowDataOverflow\s*=', re.MULTILINE)
    TICK_COUNT_PATTERN = re.compile(r'\btickCount\s*=', re.MULTILINE)
    INTERVAL_PATTERN = re.compile(r'\binterval\s*=', re.MULTILINE)
    ANGLE_PATTERN = re.compile(r'\bangle\s*=', re.MULTILINE)
    PADDING_PATTERN = re.compile(r'\bpadding\s*=', re.MULTILINE)
    HIDE_PATTERN = re.compile(r'\bhide\s*[={]?\s*(?:true|\{true\})?', re.MULTILINE)
    AXIS_ID_PATTERN = re.compile(r"""(?:yAxisId|xAxisId)\s*=\s*['"]?([^'">\s]+)['"]?""", re.MULTILINE)

    # Grid-specific props
    STROKE_DASHARRAY_PATTERN = re.compile(r'\bstrokeDasharray\s*=', re.MULTILINE)
    HORIZONTAL_PATTERN = re.compile(r'\bhorizontal\s*=', re.MULTILINE)
    VERTICAL_PATTERN = re.compile(r'\bvertical\s*=', re.MULTILINE)
    FILL_PATTERN = re.compile(r'\bfill\s*=', re.MULTILINE)
    FILL_OPACITY_PATTERN = re.compile(r'\bfillOpacity\s*=', re.MULTILINE)
    STROKE_PATTERN = re.compile(r'\bstroke\s*=', re.MULTILINE)

    # Polar-specific props
    CX_PATTERN = re.compile(r'\bcx\s*=', re.MULTILINE)
    CY_PATTERN = re.compile(r'\bcy\s*=', re.MULTILINE)

    # ── Axis config prop collection ───────────────────────────────
    AXIS_CONFIG_PATTERN = re.compile(
        r'(dataKey|type|tickFormatter|tick|tickLine|axisLine|label|'
        r'domain|scale|orientation|reversed|allowDecimals|allowDataOverflow|'
        r'tickCount|interval|angle|padding|hide|height|width|'
        r'dx|dy|mirror|minTickGap|tickSize|tickMargin|'
        r'unit|name|stroke|strokeWidth)\s*=',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract axis and grid configuration from Recharts code."""
        result: Dict[str, Any] = {
            'axes': [],
            'grids': [],
            'polar_axes': [],
        }

        # ── XAxis ────────────────────────────────────────────────
        for match in self.XAXIS_PATTERN.finditer(content):
            result['axes'].append(self._extract_axis(
                match, content, file_path, 'XAxis', 'x'
            ))

        # ── YAxis ────────────────────────────────────────────────
        for match in self.YAXIS_PATTERN.finditer(content):
            result['axes'].append(self._extract_axis(
                match, content, file_path, 'YAxis', 'y'
            ))

        # ── ZAxis ────────────────────────────────────────────────
        for match in self.ZAXIS_PATTERN.finditer(content):
            result['axes'].append(self._extract_axis(
                match, content, file_path, 'ZAxis', 'z'
            ))

        # ── CartesianGrid ────────────────────────────────────────
        for match in self.CARTESIAN_GRID_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            result['grids'].append(RechartsGridInfo(
                name='CartesianGrid',
                file=file_path,
                line_number=line_num,
                grid_type='cartesian',
                has_stroke_dasharray=bool(self.STROKE_DASHARRAY_PATTERN.search(props)),
                has_horizontal=bool(self.HORIZONTAL_PATTERN.search(props)),
                has_vertical=bool(self.VERTICAL_PATTERN.search(props)),
                has_fill=bool(self.FILL_PATTERN.search(props)),
                has_fill_opacity=bool(self.FILL_OPACITY_PATTERN.search(props)),
                has_stroke=bool(self.STROKE_PATTERN.search(props)),
            ))

        # ── PolarGrid ───────────────────────────────────────────
        for match in self.POLAR_GRID_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            result['grids'].append(RechartsGridInfo(
                name='PolarGrid',
                file=file_path,
                line_number=line_num,
                grid_type='polar',
                has_stroke_dasharray=bool(self.STROKE_DASHARRAY_PATTERN.search(props)),
                has_fill=bool(self.FILL_PATTERN.search(props)),
                has_stroke=bool(self.STROKE_PATTERN.search(props)),
            ))

        # ── PolarAngleAxis ───────────────────────────────────────
        for match in self.POLAR_ANGLE_AXIS_PATTERN.finditer(content):
            result['polar_axes'].append(self._extract_polar_axis(
                match, content, file_path, 'PolarAngleAxis', 'angle'
            ))

        # ── PolarRadiusAxis ──────────────────────────────────────
        for match in self.POLAR_RADIUS_AXIS_PATTERN.finditer(content):
            result['polar_axes'].append(self._extract_polar_axis(
                match, content, file_path, 'PolarRadiusAxis', 'radius'
            ))

        return result

    def _extract_axis(self, match, content: str, file_path: str,
                      name: str, axis_type: str) -> RechartsAxisInfo:
        """Extract axis information from a matched component."""
        props = match.group(1) or ''
        line_num = content[:match.start()].count('\n') + 1

        data_key = ''
        dk_match = self.DATAKEY_PATTERN.search(props)
        if dk_match:
            data_key = dk_match.group(1)

        axis_data_type = ''
        type_match = self.AXIS_TYPE_PATTERN.search(props)
        if type_match:
            axis_data_type = type_match.group(1)

        axis_id = ''
        id_match = self.AXIS_ID_PATTERN.search(props)
        if id_match:
            axis_id = id_match.group(1)

        config_props = list(dict.fromkeys(
            m.group(1) for m in self.AXIS_CONFIG_PATTERN.finditer(props)
        ))

        return RechartsAxisInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            axis_type=axis_type,
            axis_id=axis_id,
            data_key=data_key,
            axis_data_type=axis_data_type,
            has_tick_formatter=bool(self.TICK_FORMATTER_PATTERN.search(props)),
            has_custom_tick=bool(self.CUSTOM_TICK_PATTERN.search(props)),
            has_tick_line=bool(self.TICK_LINE_PATTERN.search(props)),
            has_axis_line=bool(self.AXIS_LINE_PATTERN.search(props)),
            has_label=bool(self.LABEL_PATTERN.search(props)),
            has_domain=bool(self.DOMAIN_PATTERN.search(props)),
            has_scale=bool(self.SCALE_PATTERN.search(props)),
            has_orientation=bool(self.ORIENTATION_PATTERN.search(props)),
            has_reversed=bool(self.REVERSED_PATTERN.search(props)),
            has_allow_decimals=bool(self.ALLOW_DECIMALS_PATTERN.search(props)),
            has_allow_data_overflow=bool(self.ALLOW_DATA_OVERFLOW_PATTERN.search(props)),
            has_tick_count=bool(self.TICK_COUNT_PATTERN.search(props)),
            has_interval=bool(self.INTERVAL_PATTERN.search(props)),
            has_angle=bool(self.ANGLE_PATTERN.search(props)),
            has_padding=bool(self.PADDING_PATTERN.search(props)),
            has_hide=bool(self.HIDE_PATTERN.search(props)),
            config_props=config_props[:15],
        )

    def _extract_polar_axis(self, match, content: str, file_path: str,
                            name: str, polar_type: str) -> RechartsPolarAxisInfo:
        """Extract polar axis information from a matched component."""
        props = match.group(1) or ''
        line_num = content[:match.start()].count('\n') + 1

        data_key = ''
        dk_match = self.DATAKEY_PATTERN.search(props)
        if dk_match:
            data_key = dk_match.group(1)

        return RechartsPolarAxisInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            polar_type=polar_type,
            data_key=data_key,
            has_tick=bool(self.CUSTOM_TICK_PATTERN.search(props)),
            has_tick_formatter=bool(self.TICK_FORMATTER_PATTERN.search(props)),
            has_domain=bool(self.DOMAIN_PATTERN.search(props)),
            has_label=bool(self.LABEL_PATTERN.search(props)),
            has_orientation=bool(self.ORIENTATION_PATTERN.search(props)),
            has_cx=bool(self.CX_PATTERN.search(props)),
            has_cy=bool(self.CY_PATTERN.search(props)),
        )
