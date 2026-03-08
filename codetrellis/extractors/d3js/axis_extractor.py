"""
D3.js Axis Extractor

Extracts axis, brush, and zoom constructs:
- Axes (axisTop, axisRight, axisBottom, axisLeft)
- Tick configuration (ticks, tickFormat, tickSize, tickValues, tickPadding)
- Grid lines (inner/outer tick sizes)
- Brush (brush, brushX, brushY)
- Zoom (zoom behavior, zoomTransform, zoomIdentity)
- D3 v3 axis patterns (d3.svg.axis)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class D3AxisInfo:
    """D3 axis generator."""
    name: str
    file: str
    line_number: int
    axis_type: str  # 'top', 'right', 'bottom', 'left'
    has_scale: bool = False
    has_ticks: bool = False
    has_tick_format: bool = False
    has_tick_values: bool = False
    has_tick_size: bool = False
    has_tick_padding: bool = False
    has_grid: bool = False  # tickSizeInner/Outer used for grid lines
    is_v3: bool = False  # d3.svg.axis() pattern
    modifiers: List[str] = field(default_factory=list)


@dataclass
class D3BrushInfo:
    """D3 brush behavior."""
    name: str
    file: str
    line_number: int
    brush_type: str  # 'brush' (2D), 'brushX', 'brushY'
    has_extent: bool = False
    has_on: bool = False
    has_filter: bool = False
    has_handle_size: bool = False
    events: List[str] = field(default_factory=list)  # 'start', 'brush', 'end'


@dataclass
class D3ZoomInfo:
    """D3 zoom behavior."""
    name: str
    file: str
    line_number: int
    has_scale_extent: bool = False
    has_translate_extent: bool = False
    has_on: bool = False
    has_filter: bool = False
    has_transform: bool = False
    has_transform_identity: bool = False
    events: List[str] = field(default_factory=list)  # 'start', 'zoom', 'end'


class D3AxisExtractor:
    """Extracts D3.js axis, brush, and zoom constructs."""

    # ── Axis patterns (D3 v4+) ────────────────────────────────────
    AXIS_PATTERNS = {
        'top': re.compile(r'd3\.axisTop\s*\(', re.MULTILINE),
        'right': re.compile(r'd3\.axisRight\s*\(', re.MULTILINE),
        'bottom': re.compile(r'd3\.axisBottom\s*\(', re.MULTILINE),
        'left': re.compile(r'd3\.axisLeft\s*\(', re.MULTILINE),
    }

    # ── Axis patterns (D3 v3) ─────────────────────────────────────
    V3_AXIS_PATTERN = re.compile(
        r'd3\.svg\.axis\s*\(\s*\)', re.MULTILINE
    )
    V3_ORIENT_PATTERN = re.compile(
        r'\.orient\s*\(\s*["\'](\w+)["\']\s*\)', re.MULTILINE
    )

    # ── Axis modifiers ────────────────────────────────────────────
    TICKS_PATTERN = re.compile(r'\.ticks\s*\(', re.MULTILINE)
    TICK_FORMAT_PATTERN = re.compile(r'\.tickFormat\s*\(', re.MULTILINE)
    TICK_VALUES_PATTERN = re.compile(r'\.tickValues\s*\(', re.MULTILINE)
    TICK_SIZE_PATTERN = re.compile(r'\.tickSize(?:Inner|Outer)?\s*\(', re.MULTILINE)
    TICK_PADDING_PATTERN = re.compile(r'\.tickPadding\s*\(', re.MULTILINE)
    TICK_ARGUMENTS_PATTERN = re.compile(r'\.tickArguments\s*\(', re.MULTILINE)
    AXIS_MODIFIER_PATTERN = re.compile(
        r'\.(ticks|tickFormat|tickValues|tickSize|tickSizeInner|tickSizeOuter|'
        r'tickPadding|tickArguments|scale|offset)\s*\(',
        re.MULTILINE
    )

    # Grid detection: tickSizeInner(-height) or tickSizeInner(-width)
    GRID_PATTERN = re.compile(
        r'\.tickSizeInner\s*\(\s*-\s*\w+|\.tickSize\s*\(\s*-\s*\w+',
        re.MULTILINE
    )

    # ── Brush patterns ────────────────────────────────────────────
    BRUSH_PATTERNS = {
        'brush': re.compile(r'd3\.brush\s*\(', re.MULTILINE),
        'brushX': re.compile(r'd3\.brushX\s*\(', re.MULTILINE),
        'brushY': re.compile(r'd3\.brushY\s*\(', re.MULTILINE),
    }

    BRUSH_EXTENT_PATTERN = re.compile(r'\.extent\s*\(', re.MULTILINE)
    BRUSH_HANDLE_SIZE_PATTERN = re.compile(r'\.handleSize\s*\(', re.MULTILINE)
    BRUSH_FILTER_PATTERN = re.compile(r'\.filter\s*\(', re.MULTILINE)
    BRUSH_ON_PATTERN = re.compile(
        r'\.on\s*\(\s*["\'](start|brush|end)["\']', re.MULTILINE
    )

    # ── Zoom patterns ─────────────────────────────────────────────
    ZOOM_PATTERN = re.compile(r'd3\.zoom\s*\(', re.MULTILINE)
    ZOOM_SCALE_EXTENT_PATTERN = re.compile(r'\.scaleExtent\s*\(', re.MULTILINE)
    ZOOM_TRANSLATE_EXTENT_PATTERN = re.compile(r'\.translateExtent\s*\(', re.MULTILINE)
    ZOOM_ON_PATTERN = re.compile(
        r'\.on\s*\(\s*["\'](start|zoom|end)["\']', re.MULTILINE
    )
    ZOOM_TRANSFORM_PATTERN = re.compile(
        r'd3\.zoomTransform\s*\(', re.MULTILINE
    )
    ZOOM_IDENTITY_PATTERN = re.compile(
        r'd3\.zoomIdentity', re.MULTILINE
    )
    ZOOM_FILTER_PATTERN = re.compile(
        r'\.filter\s*\(', re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract axis, brush, and zoom constructs from D3.js code."""
        result: Dict[str, Any] = {
            'axes': [],
            'brushes': [],
            'zooms': [],
        }

        # ── D3 v4+ Axes ─────────────────────────────────────────
        for axis_type, pattern in self.AXIS_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                modifiers = [m.group(1) for m in self.AXIS_MODIFIER_PATTERN.finditer(after[:400])]
                has_grid = bool(self.GRID_PATTERN.search(after[:400]))

                result['axes'].append(D3AxisInfo(
                    name=f"axis{axis_type.title()}",
                    file=file_path,
                    line_number=line_num,
                    axis_type=axis_type,
                    has_scale=True,  # v4+ axes always take a scale
                    has_ticks=bool(self.TICKS_PATTERN.search(after[:400])),
                    has_tick_format=bool(self.TICK_FORMAT_PATTERN.search(after[:400])),
                    has_tick_values=bool(self.TICK_VALUES_PATTERN.search(after[:400])),
                    has_tick_size=bool(self.TICK_SIZE_PATTERN.search(after[:400])),
                    has_tick_padding=bool(self.TICK_PADDING_PATTERN.search(after[:400])),
                    has_grid=has_grid,
                    is_v3=False,
                    modifiers=modifiers[:10],
                ))

        # ── D3 v3 Axes ──────────────────────────────────────────
        for match in self.V3_AXIS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.end():match.end() + 500]
            orient_match = self.V3_ORIENT_PATTERN.search(after[:300])
            axis_type = orient_match.group(1).lower() if orient_match else 'bottom'
            modifiers = [m.group(1) for m in self.AXIS_MODIFIER_PATTERN.finditer(after[:400])]
            has_grid = bool(self.GRID_PATTERN.search(after[:400]))

            result['axes'].append(D3AxisInfo(
                name='v3_axis',
                file=file_path,
                line_number=line_num,
                axis_type=axis_type,
                has_scale=bool(re.search(r'\.scale\s*\(', after[:300])),
                has_ticks=bool(self.TICKS_PATTERN.search(after[:400])),
                has_tick_format=bool(self.TICK_FORMAT_PATTERN.search(after[:400])),
                has_tick_values=bool(self.TICK_VALUES_PATTERN.search(after[:400])),
                has_tick_size=bool(self.TICK_SIZE_PATTERN.search(after[:400])),
                has_tick_padding=bool(self.TICK_PADDING_PATTERN.search(after[:400])),
                has_grid=has_grid,
                is_v3=True,
                modifiers=modifiers[:10],
            ))

        # ── Brushes ──────────────────────────────────────────────
        for brush_type, pattern in self.BRUSH_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                events = [m.group(1) for m in self.BRUSH_ON_PATTERN.finditer(after[:400])]

                result['brushes'].append(D3BrushInfo(
                    name=brush_type,
                    file=file_path,
                    line_number=line_num,
                    brush_type=brush_type,
                    has_extent=bool(self.BRUSH_EXTENT_PATTERN.search(after[:400])),
                    has_on=bool(events),
                    has_filter=bool(self.BRUSH_FILTER_PATTERN.search(after[:400])),
                    has_handle_size=bool(self.BRUSH_HANDLE_SIZE_PATTERN.search(after[:400])),
                    events=events,
                ))

        # ── Zooms ────────────────────────────────────────────────
        for match in self.ZOOM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.end():match.end() + 500]
            events = [m.group(1) for m in self.ZOOM_ON_PATTERN.finditer(after[:400])]

            result['zooms'].append(D3ZoomInfo(
                name='zoom',
                file=file_path,
                line_number=line_num,
                has_scale_extent=bool(self.ZOOM_SCALE_EXTENT_PATTERN.search(after[:400])),
                has_translate_extent=bool(self.ZOOM_TRANSLATE_EXTENT_PATTERN.search(after[:400])),
                has_on=bool(events),
                has_filter=bool(self.ZOOM_FILTER_PATTERN.search(after[:400])),
                has_transform=bool(self.ZOOM_TRANSFORM_PATTERN.search(content)),
                has_transform_identity=bool(self.ZOOM_IDENTITY_PATTERN.search(content)),
                events=events,
            ))

        return result
