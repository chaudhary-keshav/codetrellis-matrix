"""
CodeTrellis D3.js Extractors Module v1.0

Provides comprehensive extractors for D3.js data visualization:

Visualization Extractor:
- D3VisualizationExtractor: Selections, data joins (enter/update/exit),
                             shapes (arc, line, area, pie, stack),
                             layouts (force, tree, treemap, cluster, chord, sankey, pack),
                             SVG elements, canvas rendering, groups

Scale Extractor:
- D3ScaleExtractor: Scale types (linear, log, pow, sqrt, time, utc, ordinal,
                     band, point, quantize, quantile, threshold, sequential,
                     diverging), color scales, domain/range detection

Axis Extractor:
- D3AxisExtractor: Axis generators (axisTop/Right/Bottom/Left),
                    tick configuration, grid lines, labels,
                    brush, zoom, formatting

Interaction Extractor:
- D3InteractionExtractor: Event listeners (on/dispatch), drag behavior,
                           zoom/pan, brush selections, tooltips,
                           transitions/animations, voronoi overlays

API Extractor:
- D3APIExtractor: Import detection (d3 monolithic, d3-* modular packages),
                   version detection (v3–v7), Observable/notebook patterns,
                   TypeScript type usage, ecosystem (visx, nivo, recharts)

Part of CodeTrellis — D3.js Data Visualization Support
"""

from .visualization_extractor import (
    D3VisualizationExtractor,
    D3SelectionInfo,
    D3DataJoinInfo,
    D3ShapeInfo,
    D3LayoutInfo,
    D3SVGElementInfo,
)
from .scale_extractor import (
    D3ScaleExtractor,
    D3ScaleInfo,
    D3ColorScaleInfo,
)
from .axis_extractor import (
    D3AxisExtractor,
    D3AxisInfo,
    D3BrushInfo,
    D3ZoomInfo,
)
from .interaction_extractor import (
    D3InteractionExtractor,
    D3EventInfo,
    D3DragInfo,
    D3TransitionInfo,
    D3TooltipInfo,
)
from .api_extractor import (
    D3APIExtractor,
    D3ImportInfo,
    D3IntegrationInfo,
    D3TypeInfo,
)

__all__ = [
    # Visualization extractor
    "D3VisualizationExtractor",
    "D3SelectionInfo",
    "D3DataJoinInfo",
    "D3ShapeInfo",
    "D3LayoutInfo",
    "D3SVGElementInfo",
    # Scale extractor
    "D3ScaleExtractor",
    "D3ScaleInfo",
    "D3ColorScaleInfo",
    # Axis extractor
    "D3AxisExtractor",
    "D3AxisInfo",
    "D3BrushInfo",
    "D3ZoomInfo",
    # Interaction extractor
    "D3InteractionExtractor",
    "D3EventInfo",
    "D3DragInfo",
    "D3TransitionInfo",
    "D3TooltipInfo",
    # API extractor
    "D3APIExtractor",
    "D3ImportInfo",
    "D3IntegrationInfo",
    "D3TypeInfo",
]
