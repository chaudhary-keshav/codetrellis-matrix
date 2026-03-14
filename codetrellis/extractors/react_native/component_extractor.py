"""
React Native Component Extractor for CodeTrellis

Extracts React Native component usage and definitions from JS/TS source code:
- Core RN components (View, Text, ScrollView, Image, TextInput, etc.)
- List components (FlatList, SectionList, VirtualizedList)
- Animated components (Animated.View, LayoutAnimation, Reanimated)
- Touch/Pressable components (TouchableOpacity, Pressable)
- Modal, Alert, ActionSheet patterns
- Custom native view components (requireNativeComponent)
- Platform-specific component imports

Supports React Native 0.59+ through 0.76+ (New Architecture).

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RNComponentInfo:
    """Information about a React Native component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    component_type: str = "core"  # core, custom, animated, third_party
    source_module: str = ""  # e.g., 'react-native', 'react-native-safe-area-context'
    props_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    wraps_native: bool = False  # Uses requireNativeComponent


@dataclass
class RNAnimatedComponentInfo:
    """Information about an Animated component or animation pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    animation_type: str = ""  # animated_api, layout_animation, reanimated, moti
    animated_values: List[str] = field(default_factory=list)
    interpolations: List[str] = field(default_factory=list)
    uses_native_driver: bool = False
    is_gesture_based: bool = False


@dataclass
class RNListComponentInfo:
    """Information about a list/virtualized component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    list_type: str = ""  # FlatList, SectionList, VirtualizedList, FlashList
    has_key_extractor: bool = False
    has_render_item: bool = False
    has_pagination: bool = False
    has_pull_to_refresh: bool = False
    estimated_item_size: bool = False


# Core React Native component names for detection
CORE_RN_COMPONENTS = {
    'View', 'Text', 'Image', 'ScrollView', 'TextInput',
    'TouchableOpacity', 'TouchableHighlight', 'TouchableWithoutFeedback',
    'Pressable', 'Button', 'Switch', 'ActivityIndicator',
    'Modal', 'Alert', 'StatusBar', 'SafeAreaView',
    'KeyboardAvoidingView', 'ImageBackground', 'RefreshControl',
}

LIST_COMPONENTS = {
    'FlatList', 'SectionList', 'VirtualizedList',
}

ANIMATED_PATTERNS = {
    'Animated.View', 'Animated.Text', 'Animated.Image', 'Animated.ScrollView',
    'Animated.FlatList', 'Animated.createAnimatedComponent',
}


class ReactNativeComponentExtractor:
    """
    Extracts React Native component definitions and usages from source code.

    Detects:
    - Core RN component imports and usages
    - FlatList/SectionList with render patterns
    - Animated API usage (Animated.Value, Animated.timing, etc.)
    - Reanimated v2/v3 shared values and worklets
    - Custom native view wrappers (requireNativeComponent)
    - Third-party RN component libraries
    """

    # Import patterns for core RN components
    RN_IMPORT_PATTERN = re.compile(
        r"import\s+\{([^}]+)\}\s+from\s+['\"]react-native['\"]",
        re.MULTILINE
    )

    # requireNativeComponent pattern
    REQUIRE_NATIVE = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*requireNativeComponent\s*[<(]",
        re.MULTILINE
    )

    # Animated.Value / Animated.ValueXY creation
    ANIMATED_VALUE = re.compile(
        r"new\s+Animated\.(?:Value|ValueXY)\s*\(",
        re.MULTILINE
    )

    # Animated API calls
    ANIMATED_CALL = re.compile(
        r"Animated\.(?:timing|spring|decay|sequence|parallel|stagger|loop|event)\s*\(",
        re.MULTILINE
    )

    # LayoutAnimation usage
    LAYOUT_ANIMATION = re.compile(
        r"LayoutAnimation\.(?:configureNext|create|easeInEaseOut|linear|spring)\s*\(",
        re.MULTILINE
    )

    # Reanimated v2/v3 patterns
    REANIMATED_IMPORT = re.compile(
        r"from\s+['\"]react-native-reanimated['\"]",
        re.MULTILINE
    )
    SHARED_VALUE = re.compile(
        r"useSharedValue\s*\(|useAnimatedStyle\s*\(|withTiming\s*\(|withSpring\s*\(",
        re.MULTILINE
    )

    # FlatList/SectionList patterns
    FLATLIST_PATTERN = re.compile(
        r"<(?:FlatList|SectionList|VirtualizedList|FlashList)\b([^>]*(?:>|/>))",
        re.DOTALL
    )

    # Moti animation library
    MOTI_IMPORT = re.compile(
        r"from\s+['\"]moti['\"]|from\s+['\"]moti/",
        re.MULTILINE
    )

    # Component definition pattern (functional)
    COMPONENT_DEF = re.compile(
        r"(?:export\s+(?:default\s+)?)?(?:const|function)\s+(\w+)\s*"
        r"(?::\s*(?:React\.)?FC\b|=\s*\(|[=(]\s*\{|\()",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract React Native component information from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: components, animated_components, list_components
        """
        components = []
        animated_components = []
        list_components = []

        # Extract imported RN components
        imported_rn = set()
        for match in self.RN_IMPORT_PATTERN.finditer(content):
            imports_str = match.group(1)
            for imp in imports_str.split(','):
                name = imp.strip().split(' as ')[0].strip()
                if name:
                    imported_rn.add(name)

        # Core components from imports
        for name in imported_rn:
            if name in CORE_RN_COMPONENTS:
                line_num = self._find_usage_line(content, name)
                components.append(RNComponentInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    component_type="core",
                    source_module="react-native",
                ))

        # List components
        for name in imported_rn:
            if name in LIST_COMPONENTS:
                line_num = self._find_usage_line(content, name)
                info = RNListComponentInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    list_type=name,
                )
                # Check for common props
                list_section = self._find_component_jsx(content, name)
                if list_section:
                    info.has_key_extractor = 'keyExtractor' in list_section
                    info.has_render_item = 'renderItem' in list_section
                    info.has_pagination = 'onEndReached' in list_section or 'onEndReachedThreshold' in list_section
                    info.has_pull_to_refresh = 'onRefresh' in list_section or 'refreshing' in list_section
                    info.estimated_item_size = 'getItemLayout' in list_section or 'estimatedItemSize' in list_section
                list_components.append(info)

        # FlashList (third-party high perf list)
        if re.search(r"from\s+['\"]@shopify/flash-list['\"]", content):
            for match in re.finditer(r'<FlashList\b', content):
                line_num = content[:match.start()].count('\n') + 1
                info = RNListComponentInfo(
                    name="FlashList",
                    file=file_path,
                    line_number=line_num,
                    list_type="FlashList",
                )
                list_section = self._find_component_jsx(content, "FlashList")
                if list_section:
                    info.has_render_item = 'renderItem' in list_section
                    info.estimated_item_size = 'estimatedItemSize' in list_section
                list_components.append(info)

        # requireNativeComponent wrappers
        for match in self.REQUIRE_NATIVE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            components.append(RNComponentInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                component_type="custom",
                source_module="native",
                wraps_native=True,
            ))

        # Animated API components
        if self.ANIMATED_VALUE.search(content) or self.ANIMATED_CALL.search(content):
            anim_values = []
            for m in re.finditer(r'(?:const|let)\s+(\w+)\s*=\s*(?:new\s+Animated\.(?:Value|ValueXY)|useRef\(new\s+Animated\.Value)', content):
                anim_values.append(m.group(1))
            uses_native = 'useNativeDriver: true' in content or 'useNativeDriver:true' in content
            first_line = 0
            m = self.ANIMATED_VALUE.search(content) or self.ANIMATED_CALL.search(content)
            if m:
                first_line = content[:m.start()].count('\n') + 1
            animated_components.append(RNAnimatedComponentInfo(
                name="Animated",
                file=file_path,
                line_number=first_line,
                animation_type="animated_api",
                animated_values=anim_values[:10],
                uses_native_driver=uses_native,
            ))

        # LayoutAnimation
        if self.LAYOUT_ANIMATION.search(content):
            m = self.LAYOUT_ANIMATION.search(content)
            animated_components.append(RNAnimatedComponentInfo(
                name="LayoutAnimation",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                animation_type="layout_animation",
            ))

        # Reanimated v2/v3
        if self.REANIMATED_IMPORT.search(content):
            shared_vals = []
            for m in re.finditer(r'(?:const|let)\s+(\w+)\s*=\s*useSharedValue\s*\(', content):
                shared_vals.append(m.group(1))
            is_gesture = bool(re.search(r"from\s+['\"]react-native-gesture-handler['\"]", content))
            first = self.REANIMATED_IMPORT.search(content)
            animated_components.append(RNAnimatedComponentInfo(
                name="Reanimated",
                file=file_path,
                line_number=content[:first.start()].count('\n') + 1,
                animation_type="reanimated",
                animated_values=shared_vals[:10],
                is_gesture_based=is_gesture,
            ))

        # Moti
        if self.MOTI_IMPORT.search(content):
            m = self.MOTI_IMPORT.search(content)
            animated_components.append(RNAnimatedComponentInfo(
                name="Moti",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                animation_type="moti",
            ))

        # Third-party component libraries
        third_party_libs = {
            'react-native-safe-area-context': ['SafeAreaView', 'SafeAreaProvider', 'useSafeAreaInsets'],
            'react-native-svg': ['Svg', 'Circle', 'Rect', 'Path', 'G', 'Line'],
            'react-native-maps': ['MapView', 'Marker', 'Callout', 'Polyline'],
            'react-native-webview': ['WebView'],
            'react-native-video': ['Video'],
            'react-native-camera': ['Camera', 'RNCamera'],
            'react-native-linear-gradient': ['LinearGradient'],
            'react-native-blur': ['BlurView'],
            'expo-camera': ['Camera', 'CameraView'],
            'expo-image': ['Image'],
            'expo-av': ['Audio', 'Video'],
            'expo-linear-gradient': ['LinearGradient'],
        }
        for module, comp_names in third_party_libs.items():
            pattern = re.compile(rf"from\s+['\"](?:@\w+/)?{re.escape(module)}['\"]")
            if pattern.search(content):
                for cname in comp_names:
                    if re.search(rf'\b{re.escape(cname)}\b', content):
                        components.append(RNComponentInfo(
                            name=cname,
                            file=file_path,
                            line_number=self._find_usage_line(content, cname),
                            component_type="third_party",
                            source_module=module,
                        ))

        return {
            'components': components,
            'animated_components': animated_components,
            'list_components': list_components,
        }

    def _find_usage_line(self, content: str, name: str) -> int:
        """Find the first line where a component name appears."""
        match = re.search(rf'\b{re.escape(name)}\b', content)
        if match:
            return content[:match.start()].count('\n') + 1
        return 0

    def _find_component_jsx(self, content: str, name: str) -> str:
        """Find JSX usage of a component and return the props area."""
        tag_start = re.search(rf'<{re.escape(name)}\b', content)
        if not tag_start:
            return ""
        rest = content[tag_start.end():]
        # Find the matching /> or closing > by tracking angle bracket depth.
        # Skip > that is part of => (arrow functions) or >= (comparison).
        depth = 1
        i = 0
        while i < len(rest) and depth > 0:
            ch = rest[i]
            if ch == '<':
                depth += 1
            elif ch == '>':
                # Skip => and >=
                if i > 0 and rest[i - 1] in ('=', '!'):
                    i += 1
                    continue
                depth -= 1
            i += 1
        return rest[:i]
