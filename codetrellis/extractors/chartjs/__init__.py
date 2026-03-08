"""
CodeTrellis Chart.js Extractors Module v1.0

Provides comprehensive extractors for Chart.js charting library:

Chart Config Extractor:
- ChartConfigExtractor: Chart instances (new Chart), chart types (line, bar,
                         pie, doughnut, radar, polarArea, scatter, bubble,
                         area, mixed), configuration objects, global defaults,
                         responsive settings, canvas context

Dataset Extractor:
- ChartDatasetExtractor: Dataset definitions, data arrays, dataset options,
                          backgroundColor/borderColor, fill, tension, point styles,
                          bar/line/pie/doughnut-specific options

Scale Extractor:
- ChartScaleExtractor: Scale types (linear, logarithmic, category, time,
                        timeseries, radialLinear), axis configuration (x, y, r),
                        ticks, grid lines, stacking, min/max/suggestedMin/suggestedMax

Plugin Extractor:
- ChartPluginExtractor: Plugin registration (Chart.register), built-in plugins
                         (tooltip, legend, title, filler, decimation),
                         ecosystem plugins (chartjs-plugin-datalabels, zoom,
                         annotation, streaming), custom inline plugins

API Extractor:
- ChartAPIExtractor: Import detection (chart.js, chart.js/auto, react-chartjs-2,
                      vue-chartjs, ng2-charts, angular-chart.js),
                      version detection (v1–v4+), CDN patterns (cdnjs, unpkg,
                      jsdelivr), TypeScript types, ecosystem integrations

Part of CodeTrellis — Chart.js Charting Library Support
"""

from .chart_config_extractor import (
    ChartConfigExtractor,
    ChartInstanceInfo,
    ChartTypeInfo,
    ChartConfigInfo,
    ChartDefaultsInfo,
)
from .dataset_extractor import (
    ChartDatasetExtractor,
    ChartDatasetInfo,
    ChartDataPointInfo,
)
from .scale_extractor import (
    ChartScaleExtractor,
    ChartScaleInfo,
    ChartAxisInfo,
)
from .plugin_extractor import (
    ChartPluginExtractor,
    ChartPluginInfo,
    ChartPluginRegistrationInfo,
)
from .api_extractor import (
    ChartAPIExtractor,
    ChartImportInfo,
    ChartIntegrationInfo,
    ChartTypeDefinitionInfo,
)

__all__ = [
    # Chart config extractor
    "ChartConfigExtractor",
    "ChartInstanceInfo",
    "ChartTypeInfo",
    "ChartConfigInfo",
    "ChartDefaultsInfo",
    # Dataset extractor
    "ChartDatasetExtractor",
    "ChartDatasetInfo",
    "ChartDataPointInfo",
    # Scale extractor
    "ChartScaleExtractor",
    "ChartScaleInfo",
    "ChartAxisInfo",
    # Plugin extractor
    "ChartPluginExtractor",
    "ChartPluginInfo",
    "ChartPluginRegistrationInfo",
    # API extractor
    "ChartAPIExtractor",
    "ChartImportInfo",
    "ChartIntegrationInfo",
    "ChartTypeDefinitionInfo",
]
