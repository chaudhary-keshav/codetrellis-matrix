"""
Recharts Customization Extractor

Extracts customization and interaction constructs:
- Tooltip component (content, formatter, wrapperStyle, custom content)
- Legend component (content, iconType, formatter, custom renderer)
- ReferenceLine, ReferenceArea, ReferenceDot annotations
- Brush component for data zoom/pan
- Label and LabelList components
- Custom shapes and renderers (activeShape, shape, content props)
- Event handlers (onClick, onMouseEnter, onMouseLeave, onMouseMove)
- Animation configuration (isAnimationActive, animationDuration, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RechartsTooltipInfo:
    """Tooltip component configuration."""
    name: str
    file: str
    line_number: int
    has_content: bool = False  # custom content renderer
    has_formatter: bool = False
    has_label_formatter: bool = False
    has_wrapper_style: bool = False
    has_cursor: bool = False
    has_active: bool = False
    has_offset: bool = False
    has_filter_null: bool = False
    has_item_sorter: bool = False
    has_shared: bool = False  # shared tooltip in ComposedChart
    is_custom: bool = False  # uses content={CustomTooltip}
    config_props: List[str] = field(default_factory=list)


@dataclass
class RechartsLegendInfo:
    """Legend component configuration."""
    name: str
    file: str
    line_number: int
    has_content: bool = False  # custom content renderer
    has_formatter: bool = False
    has_icon_type: bool = False
    has_icon_size: bool = False
    has_layout: bool = False
    has_align: bool = False
    has_vertical_align: bool = False
    has_wrapper_style: bool = False
    has_on_click: bool = False
    has_payload: bool = False
    is_custom: bool = False  # uses content={CustomLegend}
    config_props: List[str] = field(default_factory=list)


@dataclass
class RechartsReferenceInfo:
    """ReferenceLine, ReferenceArea, ReferenceDot annotations."""
    name: str  # 'ReferenceLine', 'ReferenceArea', 'ReferenceDot'
    file: str
    line_number: int
    reference_type: str  # 'line', 'area', 'dot'
    has_x: bool = False
    has_y: bool = False
    has_label: bool = False
    has_stroke: bool = False
    has_fill: bool = False
    has_stroke_dasharray: bool = False
    has_if_overflow: bool = False  # ifOverflow='extendDomain'
    axis_ref: str = ""  # x1, x2, y1, y2 for area


@dataclass
class RechartsBrushInfo:
    """Brush component for data zoom/pan."""
    name: str
    file: str
    line_number: int
    has_data_key: bool = False
    has_height: bool = False
    has_start_index: bool = False
    has_end_index: bool = False
    has_stroke: bool = False
    has_fill: bool = False
    has_on_change: bool = False
    has_traveller_width: bool = False


@dataclass
class RechartsEventInfo:
    """Event handler on chart or chart components."""
    name: str  # event type: 'onClick', 'onMouseEnter', etc.
    file: str
    line_number: int
    event_type: str  # 'click', 'mouseenter', 'mouseleave', 'mousemove'
    component: str = ""  # which component has the handler


@dataclass
class RechartsAnimationInfo:
    """Animation configuration on Recharts components."""
    name: str
    file: str
    line_number: int
    animation_type: str  # 'active', 'duration', 'easing', 'begin', 'disabled'
    value: str = ""


class RechartsCustomizationExtractor:
    """Extracts Recharts customization and interaction constructs."""

    # ── Tooltip patterns ──────────────────────────────────────────
    TOOLTIP_PATTERN = re.compile(
        r'<Tooltip\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    TOOLTIP_CONTENT_PATTERN = re.compile(r'\bcontent\s*=\s*\{', re.MULTILINE)
    TOOLTIP_FORMATTER_PATTERN = re.compile(r'\bformatter\s*=', re.MULTILINE)
    TOOLTIP_LABEL_FORMATTER_PATTERN = re.compile(r'\blabelFormatter\s*=', re.MULTILINE)
    TOOLTIP_WRAPPER_STYLE_PATTERN = re.compile(r'\bwrapperStyle\s*=', re.MULTILINE)
    TOOLTIP_CURSOR_PATTERN = re.compile(r'\bcursor\s*=', re.MULTILINE)
    TOOLTIP_ACTIVE_PATTERN = re.compile(r'\bactive\s*=', re.MULTILINE)
    TOOLTIP_OFFSET_PATTERN = re.compile(r'\boffset\s*=', re.MULTILINE)
    TOOLTIP_FILTER_NULL_PATTERN = re.compile(r'\bfilterNull\s*=', re.MULTILINE)
    TOOLTIP_ITEM_SORTER_PATTERN = re.compile(r'\bitemSorter\s*=', re.MULTILINE)
    TOOLTIP_SHARED_PATTERN = re.compile(r'\bshared\s*=', re.MULTILINE)
    TOOLTIP_CONFIG_PATTERN = re.compile(
        r'(content|formatter|labelFormatter|wrapperStyle|cursor|active|'
        r'offset|filterNull|itemSorter|shared|separator|'
        r'contentStyle|itemStyle|labelStyle|allowEscapeViewBox|'
        r'animationDuration|animationEasing|isAnimationActive|'
        r'coordinate|viewBox|position)\s*=',
        re.MULTILINE
    )

    # ── Legend patterns ───────────────────────────────────────────
    LEGEND_PATTERN = re.compile(
        r'<Legend\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    LEGEND_CONTENT_PATTERN = re.compile(r'\bcontent\s*=\s*\{', re.MULTILINE)
    LEGEND_FORMATTER_PATTERN = re.compile(r'\bformatter\s*=', re.MULTILINE)
    LEGEND_ICON_TYPE_PATTERN = re.compile(r'\biconType\s*=', re.MULTILINE)
    LEGEND_ICON_SIZE_PATTERN = re.compile(r'\biconSize\s*=', re.MULTILINE)
    LEGEND_LAYOUT_PATTERN = re.compile(r"""\blayout\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    LEGEND_ALIGN_PATTERN = re.compile(r"""\balign\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    LEGEND_VERTICAL_ALIGN_PATTERN = re.compile(r"""\bverticalAlign\s*=\s*['"](\w+)['"]""", re.MULTILINE)
    LEGEND_WRAPPER_STYLE_PATTERN = re.compile(r'\bwrapperStyle\s*=', re.MULTILINE)
    LEGEND_ONCLICK_PATTERN = re.compile(r'\bonClick\s*=', re.MULTILINE)
    LEGEND_PAYLOAD_PATTERN = re.compile(r'\bpayload\s*=', re.MULTILINE)
    LEGEND_CONFIG_PATTERN = re.compile(
        r'(content|formatter|iconType|iconSize|layout|align|verticalAlign|'
        r'wrapperStyle|onClick|onMouseEnter|onMouseLeave|payload|'
        r'chartWidth|chartHeight|margin|width|height)\s*=',
        re.MULTILINE
    )

    # ── Reference patterns ────────────────────────────────────────
    REFERENCE_LINE_PATTERN = re.compile(
        r'<ReferenceLine\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    REFERENCE_AREA_PATTERN = re.compile(
        r'<ReferenceArea\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    REFERENCE_DOT_PATTERN = re.compile(
        r'<ReferenceDot\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # Reference props
    REF_X_PATTERN = re.compile(r'\b(?:x|x1|x2)\s*=', re.MULTILINE)
    REF_Y_PATTERN = re.compile(r'\b(?:y|y1|y2)\s*=', re.MULTILINE)
    REF_LABEL_PATTERN = re.compile(r'\blabel\s*=', re.MULTILINE)
    REF_STROKE_PATTERN = re.compile(r'\bstroke\s*=', re.MULTILINE)
    REF_FILL_PATTERN = re.compile(r'\bfill\s*=', re.MULTILINE)
    REF_STROKE_DASHARRAY_PATTERN = re.compile(r'\bstrokeDasharray\s*=', re.MULTILINE)
    REF_IF_OVERFLOW_PATTERN = re.compile(r"""\bifOverflow\s*=\s*['"](\w+)['"]""", re.MULTILINE)

    # ── Brush patterns ────────────────────────────────────────────
    BRUSH_PATTERN = re.compile(
        r'<Brush\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    BRUSH_DATAKEY_PATTERN = re.compile(r"""dataKey\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
    BRUSH_HEIGHT_PATTERN = re.compile(r'\bheight\s*=', re.MULTILINE)
    BRUSH_START_INDEX_PATTERN = re.compile(r'\bstartIndex\s*=', re.MULTILINE)
    BRUSH_END_INDEX_PATTERN = re.compile(r'\bendIndex\s*=', re.MULTILINE)
    BRUSH_STROKE_PATTERN = re.compile(r'\bstroke\s*=', re.MULTILINE)
    BRUSH_FILL_PATTERN = re.compile(r'\bfill\s*=', re.MULTILINE)
    BRUSH_ON_CHANGE_PATTERN = re.compile(r'\bonChange\s*=', re.MULTILINE)
    BRUSH_TRAVELLER_WIDTH_PATTERN = re.compile(r'\btravellerWidth\s*=', re.MULTILINE)

    # ── Event handler patterns ────────────────────────────────────
    EVENT_PATTERNS = {
        'onClick': ('click', re.compile(r'\bonClick\s*=', re.MULTILINE)),
        'onMouseEnter': ('mouseenter', re.compile(r'\bonMouseEnter\s*=', re.MULTILINE)),
        'onMouseLeave': ('mouseleave', re.compile(r'\bonMouseLeave\s*=', re.MULTILINE)),
        'onMouseMove': ('mousemove', re.compile(r'\bonMouseMove\s*=', re.MULTILINE)),
        'onMouseDown': ('mousedown', re.compile(r'\bonMouseDown\s*=', re.MULTILINE)),
        'onMouseUp': ('mouseup', re.compile(r'\bonMouseUp\s*=', re.MULTILINE)),
    }

    # ── Chart-level event patterns (on chart container components) ─
    CHART_COMPONENTS_RE = re.compile(
        r'<(LineChart|BarChart|AreaChart|PieChart|RadarChart|ScatterChart|'
        r'ComposedChart|RadialBarChart|Treemap|FunnelChart|Sankey)\b([^>]*?)(?:>)',
        re.MULTILINE | re.DOTALL
    )

    # ── Animation patterns ────────────────────────────────────────
    IS_ANIMATION_ACTIVE_PATTERN = re.compile(
        r'isAnimationActive\s*=\s*\{?\s*(true|false)\s*\}?',
        re.MULTILINE
    )
    ANIMATION_DURATION_PATTERN = re.compile(
        r'animationDuration\s*=\s*\{?\s*(\d+)\s*\}?',
        re.MULTILINE
    )
    ANIMATION_EASING_PATTERN = re.compile(
        r"""animationEasing\s*=\s*['"](\w+)['"]""",
        re.MULTILINE
    )
    ANIMATION_BEGIN_PATTERN = re.compile(
        r'animationBegin\s*=\s*\{?\s*(\d+)\s*\}?',
        re.MULTILINE
    )

    # ── Label / LabelList patterns ────────────────────────────────
    LABEL_PATTERN = re.compile(
        r'<Label\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )
    LABEL_LIST_PATTERN = re.compile(
        r'<LabelList\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract customization and interaction from Recharts code."""
        result: Dict[str, Any] = {
            'tooltips': [],
            'legends': [],
            'references': [],
            'brushes': [],
            'events': [],
            'animations': [],
            'labels': [],
        }

        # ── Tooltips ─────────────────────────────────────────────
        for match in self.TOOLTIP_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            has_content = bool(self.TOOLTIP_CONTENT_PATTERN.search(props))
            config_props = list(dict.fromkeys(
                m.group(1) for m in self.TOOLTIP_CONFIG_PATTERN.finditer(props)
            ))
            result['tooltips'].append(RechartsTooltipInfo(
                name='Tooltip',
                file=file_path,
                line_number=line_num,
                has_content=has_content,
                has_formatter=bool(self.TOOLTIP_FORMATTER_PATTERN.search(props)),
                has_label_formatter=bool(self.TOOLTIP_LABEL_FORMATTER_PATTERN.search(props)),
                has_wrapper_style=bool(self.TOOLTIP_WRAPPER_STYLE_PATTERN.search(props)),
                has_cursor=bool(self.TOOLTIP_CURSOR_PATTERN.search(props)),
                has_active=bool(self.TOOLTIP_ACTIVE_PATTERN.search(props)),
                has_offset=bool(self.TOOLTIP_OFFSET_PATTERN.search(props)),
                has_filter_null=bool(self.TOOLTIP_FILTER_NULL_PATTERN.search(props)),
                has_item_sorter=bool(self.TOOLTIP_ITEM_SORTER_PATTERN.search(props)),
                has_shared=bool(self.TOOLTIP_SHARED_PATTERN.search(props)),
                is_custom=has_content,
                config_props=config_props[:15],
            ))

        # ── Legends ──────────────────────────────────────────────
        for match in self.LEGEND_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            has_content = bool(self.LEGEND_CONTENT_PATTERN.search(props))
            config_props = list(dict.fromkeys(
                m.group(1) for m in self.LEGEND_CONFIG_PATTERN.finditer(props)
            ))
            result['legends'].append(RechartsLegendInfo(
                name='Legend',
                file=file_path,
                line_number=line_num,
                has_content=has_content,
                has_formatter=bool(self.LEGEND_FORMATTER_PATTERN.search(props)),
                has_icon_type=bool(self.LEGEND_ICON_TYPE_PATTERN.search(props)),
                has_icon_size=bool(self.LEGEND_ICON_SIZE_PATTERN.search(props)),
                has_layout=bool(self.LEGEND_LAYOUT_PATTERN.search(props)),
                has_align=bool(self.LEGEND_ALIGN_PATTERN.search(props)),
                has_vertical_align=bool(self.LEGEND_VERTICAL_ALIGN_PATTERN.search(props)),
                has_wrapper_style=bool(self.LEGEND_WRAPPER_STYLE_PATTERN.search(props)),
                has_on_click=bool(self.LEGEND_ONCLICK_PATTERN.search(props)),
                has_payload=bool(self.LEGEND_PAYLOAD_PATTERN.search(props)),
                is_custom=has_content,
                config_props=config_props[:15],
            ))

        # ── Reference Lines ──────────────────────────────────────
        for match in self.REFERENCE_LINE_PATTERN.finditer(content):
            result['references'].append(self._extract_reference(
                match, content, file_path, 'ReferenceLine', 'line'
            ))

        # ── Reference Areas ──────────────────────────────────────
        for match in self.REFERENCE_AREA_PATTERN.finditer(content):
            result['references'].append(self._extract_reference(
                match, content, file_path, 'ReferenceArea', 'area'
            ))

        # ── Reference Dots ───────────────────────────────────────
        for match in self.REFERENCE_DOT_PATTERN.finditer(content):
            result['references'].append(self._extract_reference(
                match, content, file_path, 'ReferenceDot', 'dot'
            ))

        # ── Brush ────────────────────────────────────────────────
        for match in self.BRUSH_PATTERN.finditer(content):
            props = match.group(1) or ''
            line_num = content[:match.start()].count('\n') + 1
            result['brushes'].append(RechartsBrushInfo(
                name='Brush',
                file=file_path,
                line_number=line_num,
                has_data_key=bool(self.BRUSH_DATAKEY_PATTERN.search(props)),
                has_height=bool(self.BRUSH_HEIGHT_PATTERN.search(props)),
                has_start_index=bool(self.BRUSH_START_INDEX_PATTERN.search(props)),
                has_end_index=bool(self.BRUSH_END_INDEX_PATTERN.search(props)),
                has_stroke=bool(self.BRUSH_STROKE_PATTERN.search(props)),
                has_fill=bool(self.BRUSH_FILL_PATTERN.search(props)),
                has_on_change=bool(self.BRUSH_ON_CHANGE_PATTERN.search(props)),
                has_traveller_width=bool(self.BRUSH_TRAVELLER_WIDTH_PATTERN.search(props)),
            ))

        # ── Events on chart components ───────────────────────────
        for match in self.CHART_COMPONENTS_RE.finditer(content):
            comp_name = match.group(1)
            props = match.group(2) or ''
            for event_name, (event_type, pattern) in self.EVENT_PATTERNS.items():
                if pattern.search(props):
                    line_num = content[:match.start()].count('\n') + 1
                    result['events'].append(RechartsEventInfo(
                        name=event_name,
                        file=file_path,
                        line_number=line_num,
                        event_type=event_type,
                        component=comp_name,
                    ))

        # ── Animations ───────────────────────────────────────────
        for match in self.IS_ANIMATION_ACTIVE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            value = match.group(1)
            anim_type = 'disabled' if value == 'false' else 'active'
            result['animations'].append(RechartsAnimationInfo(
                name='isAnimationActive',
                file=file_path,
                line_number=line_num,
                animation_type=anim_type,
                value=value,
            ))

        for match in self.ANIMATION_DURATION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append(RechartsAnimationInfo(
                name='animationDuration',
                file=file_path,
                line_number=line_num,
                animation_type='duration',
                value=match.group(1),
            ))

        for match in self.ANIMATION_EASING_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append(RechartsAnimationInfo(
                name='animationEasing',
                file=file_path,
                line_number=line_num,
                animation_type='easing',
                value=match.group(1),
            ))

        for match in self.ANIMATION_BEGIN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['animations'].append(RechartsAnimationInfo(
                name='animationBegin',
                file=file_path,
                line_number=line_num,
                animation_type='begin',
                value=match.group(1),
            ))

        # ── Labels ───────────────────────────────────────────────
        for match in self.LABEL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['labels'].append({
                'type': 'Label',
                'file': file_path,
                'line': line_num,
            })

        for match in self.LABEL_LIST_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['labels'].append({
                'type': 'LabelList',
                'file': file_path,
                'line': line_num,
            })

        return result

    def _extract_reference(self, match, content: str, file_path: str,
                           name: str, ref_type: str) -> RechartsReferenceInfo:
        """Extract reference component information."""
        props = match.group(1) or ''
        line_num = content[:match.start()].count('\n') + 1
        return RechartsReferenceInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            reference_type=ref_type,
            has_x=bool(self.REF_X_PATTERN.search(props)),
            has_y=bool(self.REF_Y_PATTERN.search(props)),
            has_label=bool(self.REF_LABEL_PATTERN.search(props)),
            has_stroke=bool(self.REF_STROKE_PATTERN.search(props)),
            has_fill=bool(self.REF_FILL_PATTERN.search(props)),
            has_stroke_dasharray=bool(self.REF_STROKE_DASHARRAY_PATTERN.search(props)),
            has_if_overflow=bool(self.REF_IF_OVERFLOW_PATTERN.search(props)),
        )
