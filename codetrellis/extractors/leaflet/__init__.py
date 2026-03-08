"""
Leaflet / Mapbox GL JS mapping framework extractors for CodeTrellis.

Provides 5 extractors for comprehensive mapping framework analysis:
1. LeafletMapExtractor        - Map instances, tile layers, views, containers
2. LeafletLayerExtractor      - Markers, polygons, circles, GeoJSON, layer groups
3. LeafletControlExtractor    - Controls, popups, tooltips, legends
4. LeafletInteractionExtractor - Events, drawing, gestures, animations
5. LeafletAPIExtractor        - Imports, integrations, TypeScript types, plugins

Supports:
- Leaflet v0.7.x → v1.9+ (full API)
- Mapbox GL JS v0.x → v3+ (full API)
- React-Leaflet v1 → v4 (hooks + components)
- MapLibre GL JS (open-source Mapbox GL fork)
- Vue-Leaflet, Angular Leaflet wrappers
- Leaflet plugins ecosystem (Draw, MarkerCluster, Heat, Routing, etc.)
"""

from codetrellis.extractors.leaflet.map_extractor import (
    LeafletMapExtractor,
    LeafletMapInfo,
    LeafletTileLayerInfo,
)
from codetrellis.extractors.leaflet.layer_extractor import (
    LeafletLayerExtractor,
    LeafletMarkerInfo,
    LeafletShapeInfo,
    LeafletGeoJSONInfo,
    LeafletLayerGroupInfo,
    LeafletSourceInfo,
)
from codetrellis.extractors.leaflet.control_extractor import (
    LeafletControlExtractor,
    LeafletControlInfo,
    LeafletPopupInfo,
    LeafletTooltipInfo,
)
from codetrellis.extractors.leaflet.interaction_extractor import (
    LeafletInteractionExtractor,
    LeafletEventInfo,
    LeafletDrawInfo,
    LeafletAnimationInfo,
)
from codetrellis.extractors.leaflet.api_extractor import (
    LeafletAPIExtractor,
    LeafletImportInfo,
    LeafletIntegrationInfo,
    LeafletTypeInfo,
    LeafletPluginInfo,
)

__all__ = [
    # Extractors
    "LeafletMapExtractor",
    "LeafletLayerExtractor",
    "LeafletControlExtractor",
    "LeafletInteractionExtractor",
    "LeafletAPIExtractor",
    # Map dataclasses
    "LeafletMapInfo",
    "LeafletTileLayerInfo",
    # Layer dataclasses
    "LeafletMarkerInfo",
    "LeafletShapeInfo",
    "LeafletGeoJSONInfo",
    "LeafletLayerGroupInfo",
    "LeafletSourceInfo",
    # Control dataclasses
    "LeafletControlInfo",
    "LeafletPopupInfo",
    "LeafletTooltipInfo",
    # Interaction dataclasses
    "LeafletEventInfo",
    "LeafletDrawInfo",
    "LeafletAnimationInfo",
    # API dataclasses
    "LeafletImportInfo",
    "LeafletIntegrationInfo",
    "LeafletTypeInfo",
    "LeafletPluginInfo",
]
