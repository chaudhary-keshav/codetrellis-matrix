"""
CodeTrellis Expo Extractors Module v1.0

Provides comprehensive extractors for Expo framework constructs:

Config Extractors:
- ExpoConfigExtractor: app.json, app.config.js/ts, eas.json parsing,
                        Expo SDK version, managed vs bare workflow detection

Module Extractors:
- ExpoModuleExtractor: expo-* SDK module usage detection (50+ packages),
                         module imports, API usage patterns, permissions

Router Extractors:
- ExpoRouterExtractor: Expo Router v1-v3 file-based routing, layouts,
                         route groups, API routes, typed routes, middleware

Plugin Extractors:
- ExpoPluginExtractor: Config plugins (withAndroidManifest, withInfoPlist,
                         custom plugins), mod plugins, Expo Modules API

API Extractors:
- ExpoApiExtractor: Import analysis, SDK version detection, EAS detection,
                      dev-client, ecosystem integration, TypeScript types

Part of CodeTrellis v5.7 - Expo Framework Support
"""

from .config_extractor import (
    ExpoConfigExtractor,
    ExpoConfigInfo,
    ExpoEASConfigInfo,
    ExpoPluginConfigInfo,
)
from .module_extractor import (
    ExpoModuleExtractor,
    ExpoModuleUsageInfo,
    ExpoPermissionInfo,
    ExpoAssetInfo,
)
from .router_extractor import (
    ExpoRouterExtractor,
    ExpoRouteInfo,
    ExpoLayoutInfo,
    ExpoRouteGroupInfo,
    ExpoApiRouteInfo,
)
from .plugin_extractor import (
    ExpoPluginExtractor,
    ExpoConfigPluginInfo,
    ExpoModulesAPIInfo,
)
from .api_extractor import (
    ExpoApiExtractor,
    ExpoImportInfo,
    ExpoIntegrationInfo,
    ExpoEASInfo,
)

__all__ = [
    # Config extractor
    "ExpoConfigExtractor",
    "ExpoConfigInfo",
    "ExpoEASConfigInfo",
    "ExpoPluginConfigInfo",
    # Module extractor
    "ExpoModuleExtractor",
    "ExpoModuleUsageInfo",
    "ExpoPermissionInfo",
    "ExpoAssetInfo",
    # Router extractor
    "ExpoRouterExtractor",
    "ExpoRouteInfo",
    "ExpoLayoutInfo",
    "ExpoRouteGroupInfo",
    "ExpoApiRouteInfo",
    # Plugin extractor
    "ExpoPluginExtractor",
    "ExpoConfigPluginInfo",
    "ExpoModulesAPIInfo",
    # API extractor
    "ExpoApiExtractor",
    "ExpoImportInfo",
    "ExpoIntegrationInfo",
    "ExpoEASInfo",
]
