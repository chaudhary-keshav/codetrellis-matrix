"""
Recharts Extractors Package

Provides 5 specialized extractors for Recharts data visualization framework:
- RechartsComponentExtractor: Chart components (LineChart, BarChart, PieChart, etc.)
- RechartsDataExtractor: Data series (Line, Bar, Area), dataKey usage, Cell
- RechartsAxisExtractor: Axes (XAxis, YAxis, ZAxis), grids, polar axes
- RechartsCustomizationExtractor: Tooltip, Legend, references, Brush, events, animations
- RechartsAPIExtractor: Imports, ecosystem integrations, TypeScript types, version

Part of CodeTrellis v4.74 - Recharts Framework Support
"""

from .component_extractor import (
    RechartsComponentExtractor,
    RechartsComponentInfo,
    RechartsResponsiveInfo,
)
from .data_extractor import (
    RechartsDataExtractor,
    RechartsSeriesInfo,
    RechartsDataKeyInfo,
    RechartsCellInfo,
)
from .axis_extractor import (
    RechartsAxisExtractor,
    RechartsAxisInfo,
    RechartsGridInfo,
    RechartsPolarAxisInfo,
)
from .customization_extractor import (
    RechartsCustomizationExtractor,
    RechartsTooltipInfo,
    RechartsLegendInfo,
    RechartsReferenceInfo,
    RechartsBrushInfo,
    RechartsEventInfo,
    RechartsAnimationInfo,
)
from .api_extractor import (
    RechartsAPIExtractor,
    RechartsImportInfo,
    RechartsIntegrationInfo,
    RechartsTypeInfo,
)

__all__ = [
    # Extractors
    "RechartsComponentExtractor",
    "RechartsDataExtractor",
    "RechartsAxisExtractor",
    "RechartsCustomizationExtractor",
    "RechartsAPIExtractor",
    # Component dataclasses
    "RechartsComponentInfo",
    "RechartsResponsiveInfo",
    # Data dataclasses
    "RechartsSeriesInfo",
    "RechartsDataKeyInfo",
    "RechartsCellInfo",
    # Axis dataclasses
    "RechartsAxisInfo",
    "RechartsGridInfo",
    "RechartsPolarAxisInfo",
    # Customization dataclasses
    "RechartsTooltipInfo",
    "RechartsLegendInfo",
    "RechartsReferenceInfo",
    "RechartsBrushInfo",
    "RechartsEventInfo",
    "RechartsAnimationInfo",
    # API dataclasses
    "RechartsImportInfo",
    "RechartsIntegrationInfo",
    "RechartsTypeInfo",
]
