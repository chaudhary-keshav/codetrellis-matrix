"""
CSS Layout Extractor for CodeTrellis

Extracts Flexbox, Grid, Multi-column, and other CSS layout patterns.

Supports:
- CSS Flexbox (all properties)
- CSS Grid (including subgrid, masonry)
- CSS Multi-column layout
- CSS Container Queries (container-type)
- CSS Logical Properties (inline/block dimensions)
- Display modes (flex, grid, inline-flex, inline-grid, contents)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSFlexboxInfo:
    """Information about a Flexbox layout."""
    selector: str = ""
    file: str = ""
    line_number: int = 0
    direction: str = ""  # row, column, row-reverse, column-reverse
    wrap: str = ""  # nowrap, wrap, wrap-reverse
    justify_content: str = ""
    align_items: str = ""
    align_content: str = ""
    gap: str = ""
    is_inline: bool = False
    child_count: int = 0


@dataclass
class CSSGridInfo:
    """Information about a CSS Grid layout."""
    selector: str = ""
    file: str = ""
    line_number: int = 0
    template_columns: str = ""
    template_rows: str = ""
    template_areas: List[str] = field(default_factory=list)
    gap: str = ""
    auto_flow: str = ""
    is_subgrid: bool = False
    is_masonry: bool = False
    is_inline: bool = False
    named_lines: List[str] = field(default_factory=list)
    uses_repeat: bool = False
    uses_auto_fill: bool = False
    uses_auto_fit: bool = False
    uses_minmax: bool = False
    uses_fr: bool = False


@dataclass
class CSSMultiColumnInfo:
    """Information about CSS Multi-column layout."""
    selector: str = ""
    file: str = ""
    line_number: int = 0
    column_count: str = ""
    column_width: str = ""
    column_gap: str = ""
    column_rule: str = ""
    column_span: str = ""


class CSSLayoutExtractor:
    """
    Extracts CSS layout patterns from source code.

    Detects:
    - Flexbox containers and child properties
    - Grid containers with template definitions
    - Subgrid and masonry layout usage
    - Multi-column layouts
    - Container query container definitions
    - Layout summary statistics
    """

    # Flexbox detection
    FLEX_DISPLAY = re.compile(r'display\s*:\s*(inline-)?flex\b', re.MULTILINE)
    FLEX_DIRECTION = re.compile(r'flex-direction\s*:\s*([\w-]+)', re.MULTILINE)
    FLEX_WRAP = re.compile(r'flex-wrap\s*:\s*([\w-]+)', re.MULTILINE)
    JUSTIFY_CONTENT = re.compile(r'justify-content\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    ALIGN_ITEMS = re.compile(r'align-items\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)

    # Grid detection
    GRID_DISPLAY = re.compile(r'display\s*:\s*(inline-)?grid\b', re.MULTILINE)
    GRID_TEMPLATE_COLS = re.compile(r'grid-template-columns\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    GRID_TEMPLATE_ROWS = re.compile(r'grid-template-rows\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    GRID_TEMPLATE_AREAS = re.compile(r'grid-template-areas\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    GRID_GAP = re.compile(r'(?:grid-)?gap\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    GRID_AUTO_FLOW = re.compile(r'grid-auto-flow\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    SUBGRID_PATTERN = re.compile(r'subgrid\b', re.MULTILINE)
    MASONRY_PATTERN = re.compile(r'masonry\b', re.MULTILINE)

    # Multi-column detection
    COLUMN_COUNT = re.compile(r'column-count\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    COLUMN_WIDTH = re.compile(r'column-width\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    COLUMNS_SHORTHAND = re.compile(r'columns\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    COLUMN_GAP = re.compile(r'column-gap\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    COLUMN_RULE = re.compile(r'column-rule\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)

    # Container type
    CONTAINER_TYPE = re.compile(r'container-type\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)
    CONTAINER_NAME = re.compile(r'container-name\s*:\s*([^;{}]+?)\s*;', re.MULTILINE)

    # Rule block pattern
    RULE_BLOCK = re.compile(r'([^{@/][^{]*?)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all layout patterns from CSS source.

        Returns dict with:
          - flexbox: List[CSSFlexboxInfo]
          - grid: List[CSSGridInfo]
          - multi_column: List[CSSMultiColumnInfo]
          - containers: List[Dict]
          - stats: Dict
        """
        flexbox: List[CSSFlexboxInfo] = []
        grid: List[CSSGridInfo] = []
        multi_column: List[CSSMultiColumnInfo] = []
        containers: List[Dict] = []

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        # Process rule blocks
        for match in self.RULE_BLOCK.finditer(clean):
            selector = match.group(1).strip()
            body = match.group(2)
            line_num = clean[:match.start()].count('\n') + 1

            # Skip @-rules
            if selector.startswith('@'):
                continue

            # Check for Flexbox
            flex_match = self.FLEX_DISPLAY.search(body)
            if flex_match:
                is_inline = flex_match.group(1) is not None
                direction_match = self.FLEX_DIRECTION.search(body)
                wrap_match = self.FLEX_WRAP.search(body)
                justify_match = self.JUSTIFY_CONTENT.search(body)
                align_match = self.ALIGN_ITEMS.search(body)
                gap_match = self.GRID_GAP.search(body)

                flexbox.append(CSSFlexboxInfo(
                    selector=selector[:80],
                    file=file_path,
                    line_number=line_num,
                    direction=direction_match.group(1) if direction_match else "",
                    wrap=wrap_match.group(1) if wrap_match else "",
                    justify_content=justify_match.group(1).strip() if justify_match else "",
                    align_items=align_match.group(1).strip() if align_match else "",
                    gap=gap_match.group(1).strip() if gap_match else "",
                    is_inline=is_inline,
                ))

            # Check for Grid
            grid_match = self.GRID_DISPLAY.search(body)
            if grid_match:
                is_inline = grid_match.group(1) is not None
                cols_match = self.GRID_TEMPLATE_COLS.search(body)
                rows_match = self.GRID_TEMPLATE_ROWS.search(body)
                areas_match = self.GRID_TEMPLATE_AREAS.search(body)
                gap_match = self.GRID_GAP.search(body)
                flow_match = self.GRID_AUTO_FLOW.search(body)

                cols_val = cols_match.group(1).strip() if cols_match else ""
                rows_val = rows_match.group(1).strip() if rows_match else ""

                template_areas = []
                if areas_match:
                    area_val = areas_match.group(1)
                    template_areas = re.findall(r'"([^"]+)"', area_val)

                is_subgrid = bool(self.SUBGRID_PATTERN.search(body))
                is_masonry = bool(self.MASONRY_PATTERN.search(body))

                grid.append(CSSGridInfo(
                    selector=selector[:80],
                    file=file_path,
                    line_number=line_num,
                    template_columns=cols_val[:100],
                    template_rows=rows_val[:100],
                    template_areas=template_areas,
                    gap=gap_match.group(1).strip() if gap_match else "",
                    auto_flow=flow_match.group(1).strip() if flow_match else "",
                    is_subgrid=is_subgrid,
                    is_masonry=is_masonry,
                    is_inline=is_inline,
                    uses_repeat='repeat(' in cols_val or 'repeat(' in rows_val,
                    uses_auto_fill='auto-fill' in cols_val,
                    uses_auto_fit='auto-fit' in cols_val,
                    uses_minmax='minmax(' in cols_val or 'minmax(' in rows_val,
                    uses_fr='fr' in cols_val or 'fr' in rows_val,
                ))

            # Check for Multi-column
            col_count_match = self.COLUMN_COUNT.search(body)
            col_width_match = self.COLUMN_WIDTH.search(body)
            columns_match = self.COLUMNS_SHORTHAND.search(body)
            if col_count_match or col_width_match or columns_match:
                col_gap_match = self.COLUMN_GAP.search(body)
                col_rule_match = self.COLUMN_RULE.search(body)

                multi_column.append(CSSMultiColumnInfo(
                    selector=selector[:80],
                    file=file_path,
                    line_number=line_num,
                    column_count=col_count_match.group(1).strip() if col_count_match else "",
                    column_width=col_width_match.group(1).strip() if col_width_match else "",
                    column_gap=col_gap_match.group(1).strip() if col_gap_match else "",
                    column_rule=col_rule_match.group(1).strip() if col_rule_match else "",
                ))

            # Check for container definitions
            ctype_match = self.CONTAINER_TYPE.search(body)
            cname_match = self.CONTAINER_NAME.search(body)
            if ctype_match or cname_match:
                containers.append({
                    "selector": selector[:80],
                    "container_type": ctype_match.group(1).strip() if ctype_match else "",
                    "container_name": cname_match.group(1).strip() if cname_match else "",
                    "file": file_path,
                    "line": line_num,
                })

        stats = {
            "flexbox_count": len(flexbox),
            "grid_count": len(grid),
            "multi_column_count": len(multi_column),
            "container_count": len(containers),
            "subgrid_count": sum(1 for g in grid if g.is_subgrid),
            "masonry_count": sum(1 for g in grid if g.is_masonry),
            "auto_fill_count": sum(1 for g in grid if g.uses_auto_fill),
            "auto_fit_count": sum(1 for g in grid if g.uses_auto_fit),
        }

        return {
            "flexbox": flexbox,
            "grid": grid,
            "multi_column": multi_column,
            "containers": containers,
            "stats": stats,
        }
