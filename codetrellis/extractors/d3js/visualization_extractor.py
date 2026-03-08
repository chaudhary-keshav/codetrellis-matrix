"""
D3.js Visualization Extractor

Extracts core visualization constructs:
- Selections (d3.select, d3.selectAll, selection chains)
- Data Joins (data binding, enter/update/exit, join pattern)
- Shapes / Generators (arc, line, area, pie, stack, symbol, link)
- Layouts (force, tree, cluster, treemap, pack, partition, chord, sankey, histogram)
- SVG Elements (svg, g, rect, circle, path, text, line, polygon)
- Canvas rendering (d3 + canvas 2D context)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class D3SelectionInfo:
    """D3 selection (select / selectAll)."""
    name: str  # selector string or variable
    file: str
    line_number: int
    selection_type: str  # 'select', 'selectAll', 'select_child', 'select_children'
    selector: str = ""  # CSS selector or element
    is_chained: bool = False
    has_data_binding: bool = False
    chain_methods: List[str] = field(default_factory=list)


@dataclass
class D3DataJoinInfo:
    """D3 data join (enter/update/exit or join)."""
    name: str
    file: str
    line_number: int
    join_type: str  # 'classic' (enter/update/exit), 'join' (v5+), 'datum'
    has_enter: bool = False
    has_exit: bool = False
    has_update: bool = False
    has_key_function: bool = False
    element: str = ""  # element being created (rect, circle, path, etc.)


@dataclass
class D3ShapeInfo:
    """D3 shape generator (arc, line, area, pie, etc.)."""
    name: str
    file: str
    line_number: int
    shape_type: str  # 'arc', 'line', 'area', 'pie', 'stack', 'symbol', 'link_horizontal', 'link_vertical', 'link_radial', 'curve', 'contour'
    has_accessor: bool = False  # x(), y(), innerRadius(), etc.
    has_curve: bool = False  # .curve(d3.curveCardinal)
    curve_type: str = ""
    accessors: List[str] = field(default_factory=list)


@dataclass
class D3LayoutInfo:
    """D3 layout algorithm."""
    name: str
    file: str
    line_number: int
    layout_type: str  # 'force', 'tree', 'cluster', 'treemap', 'pack', 'partition', 'chord', 'sankey', 'histogram', 'voronoi', 'delaunay'
    has_simulation: bool = False  # force layout simulation
    forces: List[str] = field(default_factory=list)  # forceCenter, forceCollide, forceLink, forceManyBody, forceX, forceY
    tiling: str = ""  # treemap tiling strategy
    has_size: bool = False


@dataclass
class D3SVGElementInfo:
    """SVG element creation via D3."""
    name: str
    file: str
    line_number: int
    element_type: str  # 'svg', 'g', 'rect', 'circle', 'path', 'text', 'line', 'polygon', 'ellipse', 'image', 'foreignObject'
    is_appended: bool = False  # .append('element')
    has_attributes: bool = False
    has_style: bool = False
    attributes: List[str] = field(default_factory=list)


class D3VisualizationExtractor:
    """Extracts D3.js core visualization constructs."""

    # Selection patterns
    SELECT_PATTERN = re.compile(
        r'd3\.select\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE
    )
    SELECTALL_PATTERN = re.compile(
        r'd3\.selectAll\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE
    )
    SELECT_VAR_PATTERN = re.compile(
        r'd3\.select\(\s*([\w.]+)\s*\)', re.MULTILINE
    )
    SELECT_CHILD_PATTERN = re.compile(
        r'\.selectChild(?:ren)?\s*\(', re.MULTILINE
    )
    # Generic selection chain
    SELECTION_CHAIN_PATTERN = re.compile(
        r'(?:d3\.select(?:All)?|\.select(?:All)?)\s*\([^)]*\)\s*(?:\.\w+\s*\([^)]*\)\s*)+',
        re.MULTILINE | re.DOTALL
    )
    CHAIN_METHOD_PATTERN = re.compile(r'\.(\w+)\s*\(')

    # Data join patterns
    DATA_BIND_PATTERN = re.compile(
        r'\.data\s*\(\s*(\w+)', re.MULTILINE
    )
    JOIN_PATTERN = re.compile(
        r'\.join\s*\(\s*["\'](\w+)["\']', re.MULTILINE
    )
    ENTER_PATTERN = re.compile(
        r'\.enter\s*\(\s*\)', re.MULTILINE
    )
    EXIT_PATTERN = re.compile(
        r'\.exit\s*\(\s*\)', re.MULTILINE
    )
    DATUM_PATTERN = re.compile(
        r'\.datum\s*\(', re.MULTILINE
    )
    KEY_FUNCTION_PATTERN = re.compile(
        r'\.data\s*\(\s*\w+\s*,\s*(?:function|d\s*=>|\(\s*d\s*\)\s*=>)',
        re.MULTILINE
    )

    # Shape generator patterns
    SHAPE_PATTERNS = {
        'arc': re.compile(r'd3\.arc\s*\(', re.MULTILINE),
        'line': re.compile(r'd3\.line\s*\(', re.MULTILINE),
        'area': re.compile(r'd3\.area\s*\(', re.MULTILINE),
        'pie': re.compile(r'd3\.pie\s*\(', re.MULTILINE),
        'stack': re.compile(r'd3\.stack\s*\(', re.MULTILINE),
        'symbol': re.compile(r'd3\.symbol\s*\(', re.MULTILINE),
        'link_horizontal': re.compile(r'd3\.linkHorizontal\s*\(', re.MULTILINE),
        'link_vertical': re.compile(r'd3\.linkVertical\s*\(', re.MULTILINE),
        'link_radial': re.compile(r'd3\.linkRadial\s*\(', re.MULTILINE),
        'contour': re.compile(r'd3\.contour(?:s|Density)?\s*\(', re.MULTILINE),
        'ribbon': re.compile(r'd3\.ribbon\s*\(', re.MULTILINE),
    }

    # Curve patterns
    CURVE_PATTERN = re.compile(
        r'\.curve\s*\(\s*d3\.(curve\w+)', re.MULTILINE
    )

    # Shape accessor patterns
    ACCESSOR_PATTERN = re.compile(
        r'\.(x|y|x0|x1|y0|y1|innerRadius|outerRadius|startAngle|endAngle|'
        r'padAngle|cornerRadius|value|sort|sortValues|keys|order|offset|'
        r'source|target|angle|radius|defined|size|type)\s*\(',
        re.MULTILINE
    )

    # Layout patterns
    LAYOUT_PATTERNS = {
        'force': re.compile(r'd3\.forceSimulation\s*\(', re.MULTILINE),
        'tree': re.compile(r'd3\.tree\s*\(', re.MULTILINE),
        'cluster': re.compile(r'd3\.cluster\s*\(', re.MULTILINE),
        'treemap': re.compile(r'd3\.treemap\s*\(', re.MULTILINE),
        'pack': re.compile(r'd3\.pack\s*\(', re.MULTILINE),
        'partition': re.compile(r'd3\.partition\s*\(', re.MULTILINE),
        'chord': re.compile(r'd3\.chord(?:Directed|Transpose)?\s*\(', re.MULTILINE),
        'sankey': re.compile(r'(?:d3\.sankey|d3Sankey|sankey)\s*\(', re.MULTILINE),
        'histogram': re.compile(r'd3\.(?:histogram|bin)\s*\(', re.MULTILINE),
        'voronoi': re.compile(r'd3\.(?:voronoi|Voronoi|Delaunay)\s*\(', re.MULTILINE),
        'delaunay': re.compile(r'(?:d3\.Delaunay|Delaunay)\.from\s*\(', re.MULTILINE),
    }

    # Force patterns (sub-types of force layout)
    FORCE_PATTERNS = {
        'forceCenter': re.compile(r'd3\.forceCenter\s*\('),
        'forceCollide': re.compile(r'd3\.forceCollide\s*\('),
        'forceLink': re.compile(r'd3\.forceLink\s*\('),
        'forceManyBody': re.compile(r'd3\.forceManyBody\s*\('),
        'forceX': re.compile(r'd3\.forceX\s*\('),
        'forceY': re.compile(r'd3\.forceY\s*\('),
        'forceRadial': re.compile(r'd3\.forceRadial\s*\('),
    }

    # Treemap tiling strategies
    TREEMAP_TILING_PATTERN = re.compile(
        r'd3\.treemap(Binary|Dice|Slice|SliceDice|Squarify|Resquarify)',
        re.MULTILINE
    )

    # SVG element append patterns
    APPEND_PATTERN = re.compile(
        r'\.append\s*\(\s*["\'](\w+)["\']\s*\)', re.MULTILINE
    )

    # Attribute patterns
    ATTR_PATTERN = re.compile(
        r'\.attr\s*\(\s*["\']([^"\']+)["\']\s*,', re.MULTILINE
    )
    STYLE_PATTERN = re.compile(
        r'\.style\s*\(\s*["\']([^"\']+)["\']\s*,', re.MULTILINE
    )

    # Canvas rendering
    CANVAS_CONTEXT_PATTERN = re.compile(
        r'\.getContext\s*\(\s*["\']2d["\']\s*\)', re.MULTILINE
    )
    CANVAS_D3_PATTERN = re.compile(
        r'd3\.(?:select|create)\s*\(\s*["\']canvas["\']\s*\)', re.MULTILINE
    )

    # Hierarchy pattern (d3.hierarchy)
    HIERARCHY_PATTERN = re.compile(
        r'd3\.hierarchy\s*\(', re.MULTILINE
    )

    # Stratify pattern (d3.stratify)
    STRATIFY_PATTERN = re.compile(
        r'd3\.stratify\s*\(', re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract visualization constructs from D3.js code."""
        result: Dict[str, Any] = {
            'selections': [],
            'data_joins': [],
            'shapes': [],
            'layouts': [],
            'svg_elements': [],
        }

        # ── Selections ───────────────────────────────────────────
        for match in self.SELECT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Check if this is a chained selection
            after = content[match.end():match.end() + 500]
            chain_methods = [m.group(1) for m in self.CHAIN_METHOD_PATTERN.finditer(after[:200])]
            result['selections'].append(D3SelectionInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                selection_type='select',
                selector=match.group(1),
                is_chained=bool(chain_methods),
                has_data_binding='.data(' in after[:200],
                chain_methods=chain_methods[:10],
            ))

        for match in self.SELECTALL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.end():match.end() + 500]
            chain_methods = [m.group(1) for m in self.CHAIN_METHOD_PATTERN.finditer(after[:200])]
            result['selections'].append(D3SelectionInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                selection_type='selectAll',
                selector=match.group(1),
                is_chained=bool(chain_methods),
                has_data_binding='.data(' in after[:200],
                chain_methods=chain_methods[:10],
            ))

        # Variable-based select (e.g., d3.select(container))
        for match in self.SELECT_VAR_PATTERN.finditer(content):
            # Skip string-based ones already matched above
            var_name = match.group(1)
            if var_name.startswith('"') or var_name.startswith("'"):
                continue
            line_num = content[:match.start()].count('\n') + 1
            result['selections'].append(D3SelectionInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                selection_type='select',
                selector=var_name,
                is_chained=False,
                has_data_binding=False,
            ))

        # ── Data Joins ───────────────────────────────────────────
        # join() pattern (D3 v5+)
        for match in self.JOIN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['data_joins'].append(D3DataJoinInfo(
                name='join',
                file=file_path,
                line_number=line_num,
                join_type='join',
                has_enter=True,
                has_exit=True,
                has_update=True,
                element=match.group(1),
            ))

        # Classic enter/exit pattern
        for match in self.ENTER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Look for append after enter
            after = content[match.end():match.end() + 200]
            element = ''
            append_match = self.APPEND_PATTERN.search(after)
            if append_match:
                element = append_match.group(1)
            # Check for key function in surrounding context
            before = content[max(0, match.start() - 200):match.start()]
            has_key = bool(self.KEY_FUNCTION_PATTERN.search(before))
            result['data_joins'].append(D3DataJoinInfo(
                name='enter',
                file=file_path,
                line_number=line_num,
                join_type='classic',
                has_enter=True,
                has_exit=bool(self.EXIT_PATTERN.search(
                    content[max(0, match.start() - 500):match.end() + 500]
                )),
                has_key_function=has_key,
                element=element,
            ))

        # datum() pattern
        for match in self.DATUM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['data_joins'].append(D3DataJoinInfo(
                name='datum',
                file=file_path,
                line_number=line_num,
                join_type='datum',
            ))

        # ── Shape Generators ─────────────────────────────────────
        for shape_type, pattern in self.SHAPE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Look for accessors and curve in subsequent code
                after = content[match.end():match.end() + 500]
                accessors = [m.group(1) for m in self.ACCESSOR_PATTERN.finditer(after[:300])]
                curve_match = self.CURVE_PATTERN.search(after[:300])
                result['shapes'].append(D3ShapeInfo(
                    name=shape_type,
                    file=file_path,
                    line_number=line_num,
                    shape_type=shape_type,
                    has_accessor=bool(accessors),
                    has_curve=bool(curve_match),
                    curve_type=curve_match.group(1) if curve_match else "",
                    accessors=accessors[:10],
                ))

        # ── Layouts ──────────────────────────────────────────────
        for layout_type, pattern in self.LAYOUT_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                forces: List[str] = []
                tiling = ""
                has_simulation = False

                if layout_type == 'force':
                    has_simulation = True
                    for force_name, force_pat in self.FORCE_PATTERNS.items():
                        if force_pat.search(content):
                            forces.append(force_name)

                if layout_type == 'treemap':
                    tm_match = self.TREEMAP_TILING_PATTERN.search(content)
                    if tm_match:
                        tiling = tm_match.group(1)

                after = content[match.end():match.end() + 300]
                has_size = bool(re.search(r'\.size\s*\(', after))

                result['layouts'].append(D3LayoutInfo(
                    name=layout_type,
                    file=file_path,
                    line_number=line_num,
                    layout_type=layout_type,
                    has_simulation=has_simulation,
                    forces=forces,
                    tiling=tiling,
                    has_size=has_size,
                ))

        # ── SVG Elements ─────────────────────────────────────────
        seen_elements: Dict[str, int] = {}
        for match in self.APPEND_PATTERN.finditer(content):
            element_type = match.group(1)
            if element_type in ('svg', 'g', 'rect', 'circle', 'path', 'text',
                                'line', 'polygon', 'ellipse', 'image',
                                'foreignObject', 'defs', 'clipPath',
                                'linearGradient', 'radialGradient', 'pattern',
                                'marker', 'use', 'tspan', 'polyline'):
                line_num = content[:match.start()].count('\n') + 1
                # Check for attr/style chaining
                after = content[match.end():match.end() + 500]
                attrs = [m.group(1) for m in self.ATTR_PATTERN.finditer(after[:300])]
                has_style = bool(self.STYLE_PATTERN.search(after[:300]))

                key = f"{element_type}:{file_path}"
                if key not in seen_elements or seen_elements[key] < 5:
                    seen_elements[key] = seen_elements.get(key, 0) + 1
                    result['svg_elements'].append(D3SVGElementInfo(
                        name=element_type,
                        file=file_path,
                        line_number=line_num,
                        element_type=element_type,
                        is_appended=True,
                        has_attributes=bool(attrs),
                        has_style=has_style,
                        attributes=attrs[:10],
                    ))

        return result
