"""
Chart.js Scale Extractor

Extracts scale and axis configurations:
- Scale types (linear, logarithmic, category, time, timeseries, radialLinear)
- Axis configuration (x, y, r)
- Ticks (stepSize, min, max, precision, callback, autoSkip, maxRotation)
- Grid lines (display, color, drawBorder, drawOnChartArea, drawTicks, tickLength)
- Stacking (stacked: true/false on scales)
- Min/max/suggestedMin/suggestedMax
- Title (display, text, font)
- v2 patterns (xAxes/yAxes) vs v3+ (x/y/r)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChartScaleInfo:
    """Chart.js scale configuration."""
    name: str  # axis id or type
    file: str
    line_number: int
    scale_type: str  # 'linear', 'logarithmic', 'category', 'time', 'timeseries', 'radialLinear'
    axis_id: str = ""  # 'x', 'y', 'r', 'x2', 'y2', etc.
    axis_position: str = ""  # 'top', 'right', 'bottom', 'left'
    has_min: bool = False
    has_max: bool = False
    has_suggested_min: bool = False
    has_suggested_max: bool = False
    has_ticks: bool = False
    has_grid: bool = False
    has_title: bool = False
    has_stacked: bool = False
    has_begin_at_zero: bool = False
    has_reverse: bool = False
    has_time_config: bool = False  # time scale specific
    has_adapter: bool = False  # date adapter
    is_v2_style: bool = False  # xAxes/yAxes (v2) vs x/y (v3+)
    modifiers: List[str] = field(default_factory=list)


@dataclass
class ChartAxisInfo:
    """Chart.js axis-specific feature."""
    name: str
    file: str
    line_number: int
    axis_feature: str  # 'ticks', 'grid', 'title', 'border', 'angleLines', 'pointLabels'
    axis_id: str = ""  # 'x', 'y', 'r'
    has_callback: bool = False
    has_auto_skip: bool = False
    has_rotation: bool = False
    config_keys: List[str] = field(default_factory=list)


class ChartScaleExtractor:
    """Extracts Chart.js scale and axis configurations."""

    # ── v3+ Scale patterns (scales: { x: { ... }, y: { ... } }) ──
    V3_SCALES_PATTERN = re.compile(
        r'scales\s*:\s*\{',
        re.MULTILINE
    )
    # Axis ID patterns within scales block
    V3_AXIS_PATTERN = re.compile(
        r"""(\w+)\s*:\s*\{[^}]*?(?:type\s*:\s*['"](\w+)['"])?""",
        re.MULTILINE
    )

    # ── v2 Scale patterns (scales: { xAxes: [...], yAxes: [...] }) ──
    V2_XAXES_PATTERN = re.compile(
        r'xAxes\s*:\s*\[',
        re.MULTILINE
    )
    V2_YAXES_PATTERN = re.compile(
        r'yAxes\s*:\s*\[',
        re.MULTILINE
    )

    # ── Scale type patterns ───────────────────────────────────────
    SCALE_TYPE_PATTERN = re.compile(
        r"""type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )
    KNOWN_SCALE_TYPES = {
        'linear', 'logarithmic', 'category', 'time', 'timeseries', 'radialLinear',
    }

    # ── Scale modifier patterns ───────────────────────────────────
    MIN_PATTERN = re.compile(r'\bmin\s*:', re.MULTILINE)
    MAX_PATTERN = re.compile(r'\bmax\s*:', re.MULTILINE)
    SUGGESTED_MIN_PATTERN = re.compile(r'suggestedMin\s*:', re.MULTILINE)
    SUGGESTED_MAX_PATTERN = re.compile(r'suggestedMax\s*:', re.MULTILINE)
    STACKED_PATTERN = re.compile(r'stacked\s*:\s*(true|false)', re.MULTILINE)
    BEGIN_AT_ZERO_PATTERN = re.compile(r'beginAtZero\s*:\s*true', re.MULTILINE)
    REVERSE_PATTERN = re.compile(r'reverse\s*:\s*true', re.MULTILINE)

    # ── Ticks patterns ────────────────────────────────────────────
    TICKS_PATTERN = re.compile(r'ticks\s*:\s*\{', re.MULTILINE)
    TICK_CALLBACK_PATTERN = re.compile(r'callback\s*:', re.MULTILINE)
    TICK_STEP_PATTERN = re.compile(r'stepSize\s*:', re.MULTILINE)
    TICK_AUTOSKIP_PATTERN = re.compile(r'autoSkip\s*:', re.MULTILINE)
    TICK_ROTATION_PATTERN = re.compile(r'(?:maxRotation|minRotation)\s*:', re.MULTILINE)
    TICK_PRECISION_PATTERN = re.compile(r'precision\s*:', re.MULTILINE)
    TICK_OPTIONS_PATTERN = re.compile(
        r'(stepSize|min|max|precision|callback|autoSkip|maxRotation|'
        r'minRotation|display|color|font|padding|count|format|'
        r'align|crossAlign|mirror|z|major|backdropColor|'
        r'backdropPadding|showLabelBackdrop|source|includeBounds)\s*:',
        re.MULTILINE
    )

    # ── Grid patterns ─────────────────────────────────────────────
    GRID_PATTERN = re.compile(r'grid\s*:\s*\{', re.MULTILINE)
    # v2 gridLines
    GRIDLINES_PATTERN = re.compile(r'gridLines\s*:\s*\{', re.MULTILINE)
    GRID_OPTIONS_PATTERN = re.compile(
        r'(display|color|drawBorder|drawOnChartArea|drawTicks|tickLength|'
        r'lineWidth|offset|circular|z|borderColor|borderWidth|'
        r'borderDash|borderDashOffset)\s*:',
        re.MULTILINE
    )

    # ── Title patterns ────────────────────────────────────────────
    TITLE_PATTERN = re.compile(r'title\s*:\s*\{', re.MULTILINE)
    TITLE_DISPLAY_PATTERN = re.compile(r'display\s*:\s*true', re.MULTILINE)
    TITLE_TEXT_PATTERN = re.compile(r"""text\s*:\s*['"]([^'"]+)['"]""", re.MULTILINE)

    # ── Time scale patterns ───────────────────────────────────────
    TIME_CONFIG_PATTERN = re.compile(r'time\s*:\s*\{', re.MULTILINE)
    TIME_UNIT_PATTERN = re.compile(
        r"""unit\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )
    ADAPTER_PATTERN = re.compile(r'adapters?\s*:\s*\{', re.MULTILINE)

    # ── Position pattern ──────────────────────────────────────────
    POSITION_PATTERN = re.compile(
        r"""position\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # ── Radial scale patterns ─────────────────────────────────────
    ANGLE_LINES_PATTERN = re.compile(r'angleLines\s*:\s*\{', re.MULTILINE)
    POINT_LABELS_PATTERN = re.compile(r'pointLabels\s*:\s*\{', re.MULTILINE)

    # ── Scale modifier collection ─────────────────────────────────
    SCALE_MODIFIER_PATTERN = re.compile(
        r'(min|max|suggestedMin|suggestedMax|stacked|beginAtZero|reverse|'
        r'position|display|offset|weight|bounds|grace|'
        r'alignToPixels|backgroundColor|afterBuildTicks|'
        r'afterCalculateTickRotation|afterDataLimits|afterFit|'
        r'afterSetDimensions|afterTickToLabelConversion|afterUpdate|'
        r'beforeBuildTicks|beforeCalculateTickRotation|beforeDataLimits|'
        r'beforeFit|beforeSetDimensions|beforeTickToLabelConversion|'
        r'beforeUpdate|ticks|grid|title|border|angleLines|pointLabels)\s*:',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract scale configurations from Chart.js code."""
        result: Dict[str, Any] = {
            'scales': [],
            'axis_features': [],
        }

        # ── v3+ scales ──────────────────────────────────────────
        for match in self.V3_SCALES_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 3000]

            # Find axis definitions within the scales block
            # Look for x: {, y: {, r: {, x2: {, etc.
            for axis_match in re.finditer(
                r"""['"]?(\w+)['"]?\s*:\s*\{""", after
            ):
                axis_id = axis_match.group(1)
                # Filter to likely axis IDs
                if axis_id in ('x', 'y', 'r', 'x2', 'y2', 'xAxis', 'yAxis') or \
                   axis_id.startswith(('x', 'y', 'r')):
                    # Skip if this is a sub-key like 'ticks', 'grid', etc.
                    if axis_id in ('ticks', 'grid', 'title', 'border', 'time',
                                    'angleLines', 'pointLabels', 'adapters',
                                    'type', 'display', 'position', 'offset',
                                    'weight', 'bounds', 'grace', 'min', 'max',
                                    'reverse', 'stacked', 'beginAtZero',
                                    'suggestedMin', 'suggestedMax', 'color',
                                    'font', 'callback', 'backgroundColor',
                                    'padding', 'drawBorder', 'drawOnChartArea'):
                        continue
                    axis_block = after[axis_match.start():axis_match.start() + 1000]

                    scale_type = 'linear'  # default
                    type_match = self.SCALE_TYPE_PATTERN.search(axis_block[:300])
                    if type_match and type_match.group(1) in self.KNOWN_SCALE_TYPES:
                        scale_type = type_match.group(1)

                    position = ''
                    pos_match = self.POSITION_PATTERN.search(axis_block[:300])
                    if pos_match:
                        position = pos_match.group(1)

                    modifiers = [m.group(1) for m in self.SCALE_MODIFIER_PATTERN.finditer(axis_block[:600])]

                    result['scales'].append(ChartScaleInfo(
                        name=f"{axis_id}_{scale_type}",
                        file=file_path,
                        line_number=line_num,
                        scale_type=scale_type,
                        axis_id=axis_id,
                        axis_position=position,
                        has_min=bool(self.MIN_PATTERN.search(axis_block[:400])),
                        has_max=bool(self.MAX_PATTERN.search(axis_block[:400])),
                        has_suggested_min=bool(self.SUGGESTED_MIN_PATTERN.search(axis_block[:400])),
                        has_suggested_max=bool(self.SUGGESTED_MAX_PATTERN.search(axis_block[:400])),
                        has_ticks=bool(self.TICKS_PATTERN.search(axis_block)),
                        has_grid=bool(self.GRID_PATTERN.search(axis_block)),
                        has_title=bool(self.TITLE_PATTERN.search(axis_block)),
                        has_stacked=bool(self.STACKED_PATTERN.search(axis_block[:300])),
                        has_begin_at_zero=bool(self.BEGIN_AT_ZERO_PATTERN.search(axis_block[:300])),
                        has_reverse=bool(self.REVERSE_PATTERN.search(axis_block[:300])),
                        has_time_config=bool(self.TIME_CONFIG_PATTERN.search(axis_block)),
                        has_adapter=bool(self.ADAPTER_PATTERN.search(axis_block)),
                        is_v2_style=False,
                        modifiers=modifiers[:15],
                    ))

                    # Extract axis features
                    if self.TICKS_PATTERN.search(axis_block):
                        ticks_block = axis_block[axis_block.index('ticks'):axis_block.index('ticks') + 500]
                        tick_keys = [m.group(1) for m in self.TICK_OPTIONS_PATTERN.finditer(ticks_block)]
                        result['axis_features'].append(ChartAxisInfo(
                            name=f"{axis_id}_ticks",
                            file=file_path,
                            line_number=line_num,
                            axis_feature='ticks',
                            axis_id=axis_id,
                            has_callback=bool(self.TICK_CALLBACK_PATTERN.search(ticks_block)),
                            has_auto_skip=bool(self.TICK_AUTOSKIP_PATTERN.search(ticks_block)),
                            has_rotation=bool(self.TICK_ROTATION_PATTERN.search(ticks_block)),
                            config_keys=tick_keys[:15],
                        ))

                    if self.GRID_PATTERN.search(axis_block):
                        grid_start = axis_block.index('grid')
                        grid_block = axis_block[grid_start:grid_start + 300]
                        grid_keys = [m.group(1) for m in self.GRID_OPTIONS_PATTERN.finditer(grid_block)]
                        result['axis_features'].append(ChartAxisInfo(
                            name=f"{axis_id}_grid",
                            file=file_path,
                            line_number=line_num,
                            axis_feature='grid',
                            axis_id=axis_id,
                            config_keys=grid_keys[:10],
                        ))

        # ── v2 scales (xAxes/yAxes) ──────────────────────────────
        for pattern, axis_id in [(self.V2_XAXES_PATTERN, 'x'), (self.V2_YAXES_PATTERN, 'y')]:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.start():match.start() + 1500]

                scale_type = 'linear'
                type_match = self.SCALE_TYPE_PATTERN.search(after[:500])
                if type_match and type_match.group(1) in self.KNOWN_SCALE_TYPES:
                    scale_type = type_match.group(1)

                modifiers = [m.group(1) for m in self.SCALE_MODIFIER_PATTERN.finditer(after[:600])]

                result['scales'].append(ChartScaleInfo(
                    name=f"v2_{axis_id}_{scale_type}",
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    axis_id=axis_id,
                    has_min=bool(self.MIN_PATTERN.search(after[:400])),
                    has_max=bool(self.MAX_PATTERN.search(after[:400])),
                    has_ticks=bool(self.TICKS_PATTERN.search(after)),
                    has_grid=bool(self.GRIDLINES_PATTERN.search(after)),
                    has_stacked=bool(self.STACKED_PATTERN.search(after[:400])),
                    has_begin_at_zero=bool(self.BEGIN_AT_ZERO_PATTERN.search(after[:400])),
                    is_v2_style=True,
                    modifiers=modifiers[:15],
                ))

        # ── Radial scale features (radar/polarArea) ──────────────
        if self.ANGLE_LINES_PATTERN.search(content):
            for match in self.ANGLE_LINES_PATTERN.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['axis_features'].append(ChartAxisInfo(
                    name='angleLines',
                    file=file_path,
                    line_number=line_num,
                    axis_feature='angleLines',
                    axis_id='r',
                ))

        if self.POINT_LABELS_PATTERN.search(content):
            for match in self.POINT_LABELS_PATTERN.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['axis_features'].append(ChartAxisInfo(
                    name='pointLabels',
                    file=file_path,
                    line_number=line_num,
                    axis_feature='pointLabels',
                    axis_id='r',
                ))

        return result
