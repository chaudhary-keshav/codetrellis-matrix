"""
CodeTrellis React Native Extractors Module v1.0

Provides comprehensive extractors for React Native framework constructs:

Component Extractors:
- ReactNativeComponentExtractor: Core RN components (View, Text, ScrollView,
                                  FlatList, SectionList, Image, Pressable,
                                  TouchableOpacity, Modal, ActivityIndicator),
                                  Animated components, custom native views

Navigation Extractors:
- ReactNativeNavigationExtractor: React Navigation stacks, tabs, drawers,
                                    screen definitions, deep link configs,
                                    navigation actions, Expo Router routes

Native Module Extractors:
- ReactNativeNativeModuleExtractor: NativeModules, TurboModules (New Architecture),
                                      Fabric components, native event emitters,
                                      bridge calls, codegen specs

Styling Extractors:
- ReactNativeStylingExtractor: StyleSheet.create, inline styles, dynamic styles,
                                 styled-components/native, NativeWind/Tailwind,
                                 responsive styles, theme patterns

Platform Extractors:
- ReactNativePlatformExtractor: Platform.OS, Platform.select, Platform.Version,
                                  platform-specific files (.ios./.android.),
                                  Dimensions/useWindowDimensions, permissions

Part of CodeTrellis v5.6 - React Native Language Support
"""

from .component_extractor import (
    ReactNativeComponentExtractor,
    RNComponentInfo,
    RNAnimatedComponentInfo,
    RNListComponentInfo,
)
from .navigation_extractor import (
    ReactNativeNavigationExtractor,
    RNNavigatorInfo,
    RNScreenInfo,
    RNDeepLinkInfo,
)
from .native_module_extractor import (
    ReactNativeNativeModuleExtractor,
    RNNativeModuleInfo,
    RNTurboModuleInfo,
    RNFabricComponentInfo,
)
from .styling_extractor import (
    ReactNativeStylingExtractor,
    RNStyleSheetInfo,
    RNDynamicStyleInfo,
    RNThemeInfo,
)
from .platform_extractor import (
    ReactNativePlatformExtractor,
    RNPlatformUsageInfo,
    RNPlatformFileInfo,
    RNPermissionInfo,
)

__all__ = [
    # Component extractor
    "ReactNativeComponentExtractor",
    "RNComponentInfo",
    "RNAnimatedComponentInfo",
    "RNListComponentInfo",
    # Navigation extractor
    "ReactNativeNavigationExtractor",
    "RNNavigatorInfo",
    "RNScreenInfo",
    "RNDeepLinkInfo",
    # Native module extractor
    "ReactNativeNativeModuleExtractor",
    "RNNativeModuleInfo",
    "RNTurboModuleInfo",
    "RNFabricComponentInfo",
    # Styling extractor
    "ReactNativeStylingExtractor",
    "RNStyleSheetInfo",
    "RNDynamicStyleInfo",
    "RNThemeInfo",
    # Platform extractor
    "ReactNativePlatformExtractor",
    "RNPlatformUsageInfo",
    "RNPlatformFileInfo",
    "RNPermissionInfo",
]
