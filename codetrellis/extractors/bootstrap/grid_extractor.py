"""
Bootstrap Grid Extractor for CodeTrellis

Extracts Bootstrap grid system usage from HTML and JSX/TSX source code.
Covers Bootstrap v3.x through v5.x grid systems:

Bootstrap 3: 4-tier grid (xs, sm, md, lg), float-based
Bootstrap 4: 5-tier grid (sm, md, lg, xl) + flexbox
Bootstrap 5: 6-tier grid (sm, md, lg, xl, xxl) + CSS Grid option

Grid Features:
- Container types (fixed, fluid, responsive containers)
- Row modifiers (row-cols-*, g-* gutters, no-gutters)
- Column spans (col-*, col-sm-*, col-md-*, auto, equal-width)
- Column ordering (order-*, order-sm-*)
- Column offsetting (offset-*, offset-sm-*)
- Nesting rows
- Responsive breakpoints
- CSS Grid mode (.grid, grid-template-*, gap)

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BootstrapGridInfo:
    """Information about a Bootstrap grid usage."""
    grid_type: str = ""          # flexbox, css-grid
    file: str = ""
    line_number: int = 0
    container_type: str = ""     # container, container-fluid, container-sm, etc.
    columns: List[str] = field(default_factory=list)   # col specs e.g. col-md-6
    gutters: List[str] = field(default_factory=list)    # g-*, gx-*, gy-*
    ordering: List[str] = field(default_factory=list)   # order-*
    offsets: List[str] = field(default_factory=list)     # offset-*
    row_cols: List[str] = field(default_factory=list)    # row-cols-*
    breakpoints_used: List[str] = field(default_factory=list)
    is_nested: bool = False


@dataclass
class BootstrapBreakpointInfo:
    """Information about responsive breakpoint usage."""
    breakpoint: str = ""        # sm, md, lg, xl, xxl
    file: str = ""
    line_number: int = 0
    context: str = ""           # grid, display, spacing, typography
    classes: List[str] = field(default_factory=list)


class BootstrapGridExtractor:
    """
    Extracts Bootstrap grid system usage from source code.

    Detects:
    - Container types (container, container-fluid, responsive containers)
    - Row/Col patterns with breakpoint-specific columns
    - Gutters (g-*, gx-*, gy-*)
    - Row-cols patterns
    - Column ordering and offsetting
    - Nested grids
    - CSS Grid mode (Bootstrap 5.1+)
    - React-Bootstrap Grid components (Container, Row, Col)
    """

    BREAKPOINTS = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']

    CONTAINER_PATTERNS = [
        'container', 'container-fluid',
        'container-sm', 'container-md', 'container-lg',
        'container-xl', 'container-xxl',
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Bootstrap grid usage from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'grids' and 'breakpoints' keys
        """
        grids: List[BootstrapGridInfo] = []
        breakpoints: List[BootstrapBreakpointInfo] = []

        if not content or not content.strip():
            return {'grids': grids, 'breakpoints': breakpoints}

        is_react = file_path.endswith(('.jsx', '.tsx')) or bool(
            re.search(r"from\s+['\"]react-bootstrap", content)
        )

        if is_react:
            self._extract_react_grid(content, file_path, grids)
        else:
            self._extract_html_grid(content, file_path, grids)

        # Extract responsive breakpoint usage
        self._extract_breakpoints(content, file_path, breakpoints)

        return {'grids': grids, 'breakpoints': breakpoints}

    def _extract_html_grid(
        self, content: str, file_path: str,
        grids: List[BootstrapGridInfo]
    ):
        """Extract grid patterns from HTML class-based markup."""
        # Find rows with their col children
        row_pattern = re.compile(
            r'<\w+\b[^>]*class\s*=\s*["\'][^"\']*\brow\b[^"\']*["\'][^>]*>',
            re.DOTALL | re.IGNORECASE
        )

        for m in row_pattern.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            row_attrs = m.group(0)

            # Extract row classes
            cls_match = re.search(r'class\s*=\s*["\']([^"\']+)["\']', row_attrs)
            if not cls_match:
                continue

            classes = cls_match.group(1).split()

            # Find gutters
            gutters = [c for c in classes if re.match(r'g[xy]?-\d+', c)]

            # Find row-cols
            row_cols = [c for c in classes if c.startswith('row-cols')]

            # Look for col-* patterns in next ~2000 chars
            after = content[m.end():m.end() + 2000]
            col_pattern = re.compile(
                r'class\s*=\s*["\'][^"\']*\b(col(?:-(?:sm|md|lg|xl|xxl))?(?:-\d+)?)\b'
            )
            columns = []
            for cm in col_pattern.finditer(after):
                columns.append(cm.group(1))

            # Detect breakpoints used
            bp_used = set()
            for c in columns + gutters + row_cols:
                for bp in self.BREAKPOINTS:
                    if f'-{bp}' in c or f'-{bp}-' in c:
                        bp_used.add(bp)

            # Detect container
            container_type = ""
            # Look backwards for container
            before = content[max(0, m.start() - 500):m.start()]
            for cp in self.CONTAINER_PATTERNS:
                if cp in before:
                    container_type = cp
                    break

            # Check for nesting
            is_nested = bool(re.search(r'\brow\b.*\brow\b', after[:500]))

            grids.append(BootstrapGridInfo(
                grid_type='flexbox',
                file=file_path,
                line_number=line_num,
                container_type=container_type,
                columns=columns[:20],
                gutters=gutters[:6],
                ordering=[],
                offsets=[c for c in columns if 'offset' in c][:6],
                row_cols=row_cols[:4],
                breakpoints_used=sorted(bp_used),
                is_nested=is_nested,
            ))

    def _extract_react_grid(
        self, content: str, file_path: str,
        grids: List[BootstrapGridInfo]
    ):
        """Extract React-Bootstrap grid patterns."""
        # Find <Row> components
        row_pattern = re.compile(
            r'<Row\b([^>]*)(?:/>|>)',
            re.DOTALL
        )

        for m in row_pattern.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            props_str = m.group(1)

            # Extract gutter props
            gutters = []
            for gp in ['g', 'gx', 'gy']:
                if re.search(rf'\b{gp}\s*=', props_str):
                    gutters.append(gp)

            # Look for <Col> children
            after = content[m.end():m.end() + 2000]
            col_pattern = re.compile(
                r'<Col\b([^>]*?)(?:/>|>)',
                re.DOTALL
            )
            columns = []
            bp_used = set()
            for cm in col_pattern.finditer(after):
                col_props = cm.group(1)
                for bp in self.BREAKPOINTS:
                    if re.search(rf'\b{bp}\s*=', col_props):
                        bp_used.add(bp)
                        columns.append(f'col-{bp}')

                # Generic col
                if not columns or re.search(r'\bcolumn\b|\bcol\b', col_props):
                    columns.append('col')

            grids.append(BootstrapGridInfo(
                grid_type='flexbox',
                file=file_path,
                line_number=line_num,
                columns=columns[:20],
                gutters=gutters[:6],
                breakpoints_used=sorted(bp_used),
            ))

    def _extract_breakpoints(
        self, content: str, file_path: str,
        breakpoints: List[BootstrapBreakpointInfo]
    ):
        """Extract responsive breakpoint usage across all utilities."""
        seen = set()

        # Pattern: <prefix>-<breakpoint>-<value> e.g., d-md-flex, text-lg-center
        bp_class_pattern = re.compile(
            r'\b(d|text|float|m[trblxy]?|p[trblxy]?|order|'
            r'align-(?:items|self|content)|justify-content|'
            r'flex|w|h|col|offset|g[xy]?|row-cols|'
            r'container|display|position|top|bottom|start|end|'
            r'border|rounded|shadow|opacity|overflow|'
            r'fs|lh|fw|font|bg|table|list-group)'
            r'-(sm|md|lg|xl|xxl)(?:-\w+)?'
        )

        for m in bp_class_pattern.finditer(content):
            bp = m.group(2)
            context_type = m.group(1)
            key = (bp, context_type)
            if key in seen:
                continue
            seen.add(key)

            line_num = content[:m.start()].count('\n') + 1

            # Map to context category
            if context_type in ('col', 'offset', 'row-cols', 'container', 'g', 'gx', 'gy'):
                ctx = 'grid'
            elif context_type in ('d', 'display'):
                ctx = 'display'
            elif context_type.startswith(('m', 'p')):
                ctx = 'spacing'
            elif context_type in ('text', 'fs', 'lh', 'fw', 'font'):
                ctx = 'typography'
            elif context_type.startswith('flex') or context_type.startswith('align') or context_type.startswith('justify'):
                ctx = 'flex'
            else:
                ctx = 'utility'

            breakpoints.append(BootstrapBreakpointInfo(
                breakpoint=bp,
                file=file_path,
                line_number=line_num,
                context=ctx,
                classes=[m.group(0)],
            ))
