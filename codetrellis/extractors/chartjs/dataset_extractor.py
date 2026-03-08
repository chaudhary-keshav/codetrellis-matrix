"""
Chart.js Dataset Extractor

Extracts dataset definitions and configurations:
- Dataset objects ({ label, data, backgroundColor, borderColor, ... })
- Data arrays and data points (numbers, {x,y}, {x,y,r} for bubble)
- Dataset options (fill, tension, pointRadius, barThickness, etc.)
- Dataset styling (backgroundColor, borderColor, borderWidth, hoverBackgroundColor)
- Multi-dataset detection
- Dataset type overrides (for mixed charts)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChartDatasetInfo:
    """Chart.js dataset definition."""
    name: str  # dataset label or variable name
    file: str
    line_number: int
    dataset_type: str  # 'line', 'bar', 'pie', 'doughnut', 'radar', 'scatter', 'bubble', 'area', 'mixed', 'unknown'
    has_label: bool = False
    has_data: bool = False
    has_background_color: bool = False
    has_border_color: bool = False
    has_fill: bool = False
    has_tension: bool = False
    has_point_style: bool = False
    has_bar_options: bool = False  # barThickness, barPercentage, categoryPercentage
    has_hover_style: bool = False
    has_type_override: bool = False  # type override in dataset (mixed charts)
    overridden_type: str = ""
    options: List[str] = field(default_factory=list)


@dataclass
class ChartDataPointInfo:
    """Chart.js data point format."""
    name: str
    file: str
    line_number: int
    data_format: str  # 'array_numbers', 'array_objects_xy', 'array_objects_xyr', 'array_labels', 'callback'
    has_labels: bool = False
    point_count: int = 0


class ChartDatasetExtractor:
    """Extracts Chart.js dataset definitions and configurations."""

    # ── Dataset block patterns ────────────────────────────────────
    # datasets: [ { ... } ]
    DATASETS_ARRAY_PATTERN = re.compile(
        r'datasets\s*:\s*\[',
        re.MULTILINE
    )

    # Individual dataset object: { label: '...', data: [...], ... }
    DATASET_LABEL_PATTERN = re.compile(
        r"""label\s*:\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # Dataset type override: type: 'bar' inside a dataset
    DATASET_TYPE_OVERRIDE = re.compile(
        r"""type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # ── Data array patterns ───────────────────────────────────────
    DATA_ARRAY_PATTERN = re.compile(
        r'data\s*:\s*\[',
        re.MULTILINE
    )
    # Object data: data: [{ x: 1, y: 2 }, ...]
    DATA_OBJECT_XY_PATTERN = re.compile(
        r'data\s*:\s*\[\s*\{[^}]*x\s*:',
        re.MULTILINE
    )
    # Bubble data: data: [{ x: 1, y: 2, r: 5 }, ...]
    DATA_OBJECT_XYR_PATTERN = re.compile(
        r'data\s*:\s*\[\s*\{[^}]*r\s*:',
        re.MULTILINE
    )

    # ── Labels pattern ────────────────────────────────────────────
    LABELS_PATTERN = re.compile(
        r'labels\s*:\s*\[',
        re.MULTILINE
    )

    # ── Styling patterns ──────────────────────────────────────────
    BACKGROUND_COLOR_PATTERN = re.compile(
        r'backgroundColor\s*:',
        re.MULTILINE
    )
    BORDER_COLOR_PATTERN = re.compile(
        r'borderColor\s*:',
        re.MULTILINE
    )
    BORDER_WIDTH_PATTERN = re.compile(
        r'borderWidth\s*:',
        re.MULTILINE
    )
    FILL_PATTERN = re.compile(
        r'fill\s*:',
        re.MULTILINE
    )
    TENSION_PATTERN = re.compile(
        r'(?:tension|lineTension)\s*:',
        re.MULTILINE
    )
    POINT_STYLE_PATTERN = re.compile(
        r'(?:pointStyle|pointRadius|pointHoverRadius|pointBackgroundColor|'
        r'pointBorderColor|pointBorderWidth|pointHitRadius|pointRotation)\s*:',
        re.MULTILINE
    )
    BAR_OPTIONS_PATTERN = re.compile(
        r'(?:barThickness|barPercentage|categoryPercentage|maxBarThickness|'
        r'minBarLength|borderSkipped|borderRadius)\s*:',
        re.MULTILINE
    )
    HOVER_STYLE_PATTERN = re.compile(
        r'(?:hoverBackgroundColor|hoverBorderColor|hoverBorderWidth|'
        r'hoverOffset|hoverRadius)\s*:',
        re.MULTILINE
    )

    # ── Dataset option patterns ───────────────────────────────────
    DATASET_OPTIONS_PATTERN = re.compile(
        r'(label|data|backgroundColor|borderColor|borderWidth|fill|tension|'
        r'lineTension|pointStyle|pointRadius|pointHoverRadius|pointBackgroundColor|'
        r'pointBorderColor|pointBorderWidth|pointHitRadius|pointRotation|'
        r'barThickness|barPercentage|categoryPercentage|maxBarThickness|'
        r'minBarLength|borderSkipped|borderRadius|borderDash|borderDashOffset|'
        r'hoverBackgroundColor|hoverBorderColor|hoverBorderWidth|hoverOffset|'
        r'hoverRadius|order|stack|yAxisID|xAxisID|hidden|clip|'
        r'showLine|spanGaps|stepped|segment|cubicInterpolationMode|'
        r'rotation|circumference|spacing|weight|offset|cutout|radius|'
        r'animation|parsing|normalized)\s*:',
        re.MULTILINE
    )

    # ── Specific chart type option patterns ───────────────────────
    PIE_DOUGHNUT_PATTERN = re.compile(
        r'(?:cutout|rotation|circumference|spacing|offset|hoverOffset)\s*:',
        re.MULTILINE
    )
    LINE_SPECIFIC_PATTERN = re.compile(
        r'(?:showLine|spanGaps|stepped|segment|cubicInterpolationMode)\s*:',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract dataset definitions from Chart.js code."""
        result: Dict[str, Any] = {
            'datasets': [],
            'data_points': [],
        }

        # ── Find datasets array blocks ───────────────────────────
        for match in self.DATASETS_ARRAY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 3000]

            # Find all labels in this datasets block
            labels = self.DATASET_LABEL_PATTERN.findall(after)
            if not labels:
                labels = ['dataset']

            for label in labels:
                # Find the dataset block for this label
                label_pos = after.find(label)
                if label_pos == -1:
                    continue
                # Get ~500 chars around the label for context
                dataset_block = after[max(0, label_pos - 100):label_pos + 500]

                # Detect type override
                type_override = ''
                has_type_override = False
                type_match = self.DATASET_TYPE_OVERRIDE.search(dataset_block)
                if type_match:
                    type_val = type_match.group(1)
                    if type_val in ('line', 'bar', 'pie', 'doughnut', 'radar',
                                     'polarArea', 'scatter', 'bubble', 'area'):
                        type_override = type_val
                        has_type_override = True

                # Detect data format
                data_format = 'array_numbers'
                if self.DATA_OBJECT_XYR_PATTERN.search(dataset_block):
                    data_format = 'array_objects_xyr'
                elif self.DATA_OBJECT_XY_PATTERN.search(dataset_block):
                    data_format = 'array_objects_xy'

                # Collect options
                options = [m.group(1) for m in self.DATASET_OPTIONS_PATTERN.finditer(dataset_block)]

                dataset_type = type_override if type_override else 'unknown'

                result['datasets'].append(ChartDatasetInfo(
                    name=label,
                    file=file_path,
                    line_number=line_num,
                    dataset_type=dataset_type,
                    has_label=True,
                    has_data=bool(self.DATA_ARRAY_PATTERN.search(dataset_block)),
                    has_background_color=bool(self.BACKGROUND_COLOR_PATTERN.search(dataset_block)),
                    has_border_color=bool(self.BORDER_COLOR_PATTERN.search(dataset_block)),
                    has_fill=bool(self.FILL_PATTERN.search(dataset_block)),
                    has_tension=bool(self.TENSION_PATTERN.search(dataset_block)),
                    has_point_style=bool(self.POINT_STYLE_PATTERN.search(dataset_block)),
                    has_bar_options=bool(self.BAR_OPTIONS_PATTERN.search(dataset_block)),
                    has_hover_style=bool(self.HOVER_STYLE_PATTERN.search(dataset_block)),
                    has_type_override=has_type_override,
                    overridden_type=type_override,
                    options=options[:20],
                ))

        # ── Data point format detection ──────────────────────────
        for match in self.DATA_ARRAY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 500]

            data_format = 'array_numbers'
            if self.DATA_OBJECT_XYR_PATTERN.search(after):
                data_format = 'array_objects_xyr'
            elif self.DATA_OBJECT_XY_PATTERN.search(after):
                data_format = 'array_objects_xy'

            has_labels = bool(self.LABELS_PATTERN.search(
                content[max(0, match.start() - 500):match.start() + 500]
            ))

            result['data_points'].append(ChartDataPointInfo(
                name='data',
                file=file_path,
                line_number=line_num,
                data_format=data_format,
                has_labels=has_labels,
            ))

        return result
