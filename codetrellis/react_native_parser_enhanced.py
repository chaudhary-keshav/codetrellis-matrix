"""
Enhanced React Native Parser for CodeTrellis

Comprehensive React Native framework parser with full extractor support.
Parses React Native components, navigation, native modules, styling, and
platform patterns from JavaScript/TypeScript source code.

This parser runs as a FRAMEWORK-LEVEL overlay on JS/TS files when React Native
imports are detected. It should be called AFTER the base JavaScript/TypeScript
parser and the React parser have run.

Supported React Native versions:
- React Native 0.59+ (Hooks support, first stable hooks release)
- React Native 0.60+ (Autolinking, AndroidX migration)
- React Native 0.63+ (LogBox, Pressable)
- React Native 0.64+ (Hermes on iOS)
- React Native 0.68+ (New Architecture opt-in: Fabric + TurboModules)
- React Native 0.71+ (TypeScript by default, Flexbox Gap)
- React Native 0.72+ (Symlink support, Metro improvements)
- React Native 0.73+ (Debugging improvements, bridgeless mode preview)
- React Native 0.74+ (Yoga 3.0, bridgeless by default for new arch)
- React Native 0.75+ (Auto-linking perf, New Architecture stable)
- React Native 0.76+ (New Architecture default, React 18 concurrent features)

Framework detection supports 40+ React Native ecosystem libraries:
- Core (react-native, react-native-web)
- Navigation (React Navigation v5-v7, Expo Router v1-v3, Wix Navigation)
- Animation (Animated API, Reanimated v2/v3, Moti, Lottie)
- Gestures (react-native-gesture-handler)
- State (Redux, Zustand, Jotai, MMKV, WatermelonDB)
- UI (React Native Paper, NativeBase, Tamagui, Gluestack, UI Kitten)
- Styling (StyleSheet, NativeWind, Restyle, styled-components/native)
- Media (react-native-camera, expo-camera, react-native-video, expo-av)
- Maps (react-native-maps, expo-location)
- Storage (AsyncStorage, MMKV, expo-secure-store, expo-file-system)
- Push (Firebase, expo-notifications, OneSignal)
- Native Modules (NativeModules, TurboModules, Fabric, JSI)
- Platform (Platform API, Dimensions, PermissionsAndroid, expo-* modules)
- Testing (Detox, Maestro, @testing-library/react-native)

Optional AST: tree-sitter-javascript / tree-sitter-typescript
Optional LSP: typescript-language-server (tsserver)

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from codetrellis.extractors.react_native import (
    ReactNativeComponentExtractor,
    RNComponentInfo,
    RNAnimatedComponentInfo,
    RNListComponentInfo,
    ReactNativeNavigationExtractor,
    RNNavigatorInfo,
    RNScreenInfo,
    RNDeepLinkInfo,
    ReactNativeNativeModuleExtractor,
    RNNativeModuleInfo,
    RNTurboModuleInfo,
    RNFabricComponentInfo,
    ReactNativeStylingExtractor,
    RNStyleSheetInfo,
    RNDynamicStyleInfo,
    RNThemeInfo,
    ReactNativePlatformExtractor,
    RNPlatformUsageInfo,
    RNPlatformFileInfo,
    RNPermissionInfo,
)


@dataclass
class ReactNativeParseResult:
    """Result from parsing a React Native source file."""
    file_path: str = ""
    file_type: str = ""  # jsx, tsx, js, ts

    # Components
    components: List[RNComponentInfo] = field(default_factory=list)
    animated_components: List[RNAnimatedComponentInfo] = field(default_factory=list)
    list_components: List[RNListComponentInfo] = field(default_factory=list)

    # Navigation
    navigators: List[RNNavigatorInfo] = field(default_factory=list)
    screens: List[RNScreenInfo] = field(default_factory=list)
    deep_links: List[RNDeepLinkInfo] = field(default_factory=list)

    # Native Modules
    native_modules: List[RNNativeModuleInfo] = field(default_factory=list)
    turbo_modules: List[RNTurboModuleInfo] = field(default_factory=list)
    fabric_components: List[RNFabricComponentInfo] = field(default_factory=list)

    # Styling
    stylesheets: List[RNStyleSheetInfo] = field(default_factory=list)
    dynamic_styles: List[RNDynamicStyleInfo] = field(default_factory=list)
    themes: List[RNThemeInfo] = field(default_factory=list)

    # Platform
    platform_usages: List[RNPlatformUsageInfo] = field(default_factory=list)
    platform_files: List[RNPlatformFileInfo] = field(default_factory=list)
    permissions: List[RNPermissionInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    rn_version: str = ""  # Detected minimum React Native version
    architecture: str = ""  # bridge, new_architecture, bridgeless


class EnhancedReactNativeParser:
    """
    Enhanced React Native parser that uses all extractors for comprehensive parsing.

    Framework detection supports 40+ RN ecosystem libraries across:
    - Navigation (React Navigation, Expo Router, Wix Navigation)
    - Animation (Animated, Reanimated, Moti, Lottie)
    - UI (Paper, NativeBase, Tamagui, Gluestack, UI Kitten)
    - Storage (AsyncStorage, MMKV, WatermelonDB, Realm)
    - Media (Camera, Video, Audio, Image Picker)
    - Maps (react-native-maps, expo-location)
    - Push (Firebase, expo-notifications, OneSignal)
    - Testing (Detox, Maestro, Testing Library)
    - Platform tools (CodePush, Flipper, Sentry)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # React Native ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'react-native': re.compile(
            r"from\s+['\"]react-native['\"]|"
            r"require\(['\"]react-native['\"]\)|"
            r"StyleSheet\.create|View|Text|TouchableOpacity",
            re.MULTILINE
        ),
        'react-native-web': re.compile(
            r"from\s+['\"]react-native-web['\"]|"
            r"from\s+['\"]react-native['\"].*Platform\.OS.*web",
            re.MULTILINE
        ),

        # ── Navigation ────────────────────────────────────────────
        'react-navigation': re.compile(
            r"from\s+['\"]@react-navigation/(?:native|stack|bottom-tabs|drawer|"
            r"material-top-tabs|material-bottom-tabs|native-stack|elements)['\"]|"
            r"NavigationContainer|createStackNavigator|createBottomTabNavigator|"
            r"createNativeStackNavigator|createDrawerNavigator|"
            r"useNavigation|useRoute|useFocusEffect",
            re.MULTILINE
        ),
        'expo-router': re.compile(
            r"from\s+['\"]expo-router['\"]|"
            r"useRouter|useLocalSearchParams|useGlobalSearchParams|useSegments",
            re.MULTILINE
        ),
        'wix-navigation': re.compile(
            r"from\s+['\"]react-native-navigation['\"]|"
            r"Navigation\.registerComponent|Navigation\.setRoot|"
            r"Navigation\.events|Navigation\.push",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'reanimated': re.compile(
            r"from\s+['\"]react-native-reanimated['\"]|"
            r"useSharedValue|useAnimatedStyle|withTiming|withSpring|"
            r"withDecay|useAnimatedGestureHandler|runOnJS|runOnUI",
            re.MULTILINE
        ),
        'gesture-handler': re.compile(
            r"from\s+['\"]react-native-gesture-handler['\"]|"
            r"GestureDetector|Gesture\.\w+|PanGestureHandler|"
            r"TapGestureHandler|FlingGestureHandler|PinchGestureHandler",
            re.MULTILINE
        ),
        'moti': re.compile(
            r"from\s+['\"]moti['\"]|from\s+['\"]moti/|"
            r"MotiView|MotiText|MotiImage|useAnimationState",
            re.MULTILINE
        ),
        'lottie': re.compile(
            r"from\s+['\"]lottie-react-native['\"]|"
            r"LottieView|AnimatedLottieView",
            re.MULTILINE
        ),

        # ── UI Libraries ──────────────────────────────────────────
        'react-native-paper': re.compile(
            r"from\s+['\"]react-native-paper['\"]|"
            r"PaperProvider|MD3DarkTheme|MD3LightTheme|"
            r"Appbar|FAB|Chip|DataTable|SegmentedButtons",
            re.MULTILINE
        ),
        'nativebase': re.compile(
            r"from\s+['\"]native-base['\"]|from\s+['\"]@gluestack-ui/|"
            r"NativeBaseProvider|Box|HStack|VStack|Center|Heading",
            re.MULTILINE
        ),
        'tamagui': re.compile(
            r"from\s+['\"]tamagui['\"]|from\s+['\"]@tamagui/|"
            r"TamaguiProvider|XStack|YStack|Theme|getTokens",
            re.MULTILINE
        ),
        'ui-kitten': re.compile(
            r"from\s+['\"]@ui-kitten/components['\"]|"
            r"ApplicationProvider|Layout|Card|TopNavigation",
            re.MULTILINE
        ),
        'react-native-elements': re.compile(
            r"from\s+['\"]@rneui/|from\s+['\"]react-native-elements['\"]|"
            r"ListItem|ThemeProvider|Header|Overlay",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'nativewind': re.compile(
            r"from\s+['\"]nativewind['\"]|"
            r"className\s*=|styled\(.*nativewind",
            re.MULTILINE
        ),
        'restyle': re.compile(
            r"from\s+['\"]@shopify/restyle['\"]|"
            r"createTheme|createBox|createText|createRestyleComponent",
            re.MULTILINE
        ),
        'styled-native': re.compile(
            r"from\s+['\"]styled-components/native['\"]",
            re.MULTILINE
        ),

        # ── Storage ───────────────────────────────────────────────
        'async-storage': re.compile(
            r"from\s+['\"]@react-native-async-storage/async-storage['\"]|"
            r"AsyncStorage\.(?:getItem|setItem|removeItem|multiGet|multiSet|clear)",
            re.MULTILINE
        ),
        'mmkv': re.compile(
            r"from\s+['\"]react-native-mmkv['\"]|"
            r"MMKV|useMMKVString|useMMKVNumber|useMMKVBoolean|useMMKVObject",
            re.MULTILINE
        ),
        'watermelondb': re.compile(
            r"from\s+['\"]@nozbe/watermelondb['\"]|"
            r"@readonly|@field|@children|@lazy|Model|Database|tableSchema",
            re.MULTILINE
        ),
        'realm': re.compile(
            r"from\s+['\"]realm['\"]|from\s+['\"]@realm/react['\"]|"
            r"Realm\.Object|RealmProvider|useRealm|useQuery",
            re.MULTILINE
        ),
        'expo-secure-store': re.compile(
            r"from\s+['\"]expo-secure-store['\"]|"
            r"SecureStore\.getItemAsync|SecureStore\.setItemAsync",
            re.MULTILINE
        ),

        # ── Media ─────────────────────────────────────────────────
        'react-native-camera': re.compile(
            r"from\s+['\"]react-native-camera['\"]|"
            r"from\s+['\"]react-native-vision-camera['\"]|"
            r"RNCamera|Camera\.\w+|useCameraDevice|useCameraFormat",
            re.MULTILINE
        ),
        'expo-camera': re.compile(
            r"from\s+['\"]expo-camera['\"]|CameraView|useCameraPermissions",
            re.MULTILINE
        ),
        'react-native-video': re.compile(
            r"from\s+['\"]react-native-video['\"]|VideoPlayer|useVideoPlayer",
            re.MULTILINE
        ),
        'expo-av': re.compile(
            r"from\s+['\"]expo-av['\"]|Audio\.Sound|Video\.createAsync",
            re.MULTILINE
        ),
        'expo-image-picker': re.compile(
            r"from\s+['\"]expo-image-picker['\"]|"
            r"launchImageLibraryAsync|launchCameraAsync|MediaTypeOptions",
            re.MULTILINE
        ),

        # ── Maps ──────────────────────────────────────────────────
        'react-native-maps': re.compile(
            r"from\s+['\"]react-native-maps['\"]|"
            r"MapView|Marker|Callout|Polyline|PROVIDER_GOOGLE",
            re.MULTILINE
        ),
        'expo-location': re.compile(
            r"from\s+['\"]expo-location['\"]|"
            r"getCurrentPositionAsync|watchPositionAsync|requestForegroundPermissionsAsync",
            re.MULTILINE
        ),

        # ── Push / Notifications ──────────────────────────────────
        'firebase': re.compile(
            r"from\s+['\"]@react-native-firebase/(?:app|messaging|analytics|crashlytics|"
            r"firestore|auth|storage|remote-config|performance|dynamic-links)['\"]|"
            r"firebase\(\)|messaging\(\)|analytics\(\)",
            re.MULTILINE
        ),
        'expo-notifications': re.compile(
            r"from\s+['\"]expo-notifications['\"]|"
            r"Notifications\.schedule|Notifications\.getPermissionsAsync|"
            r"Notifications\.setNotificationHandler",
            re.MULTILINE
        ),
        'onesignal': re.compile(
            r"from\s+['\"]react-native-onesignal['\"]|"
            r"OneSignal\.initialize|OneSignal\.Notifications",
            re.MULTILINE
        ),

        # ── Lists / Performance ───────────────────────────────────
        'flash-list': re.compile(
            r"from\s+['\"]@shopify/flash-list['\"]|FlashList",
            re.MULTILINE
        ),

        # ── Safe Area / Status Bar ────────────────────────────────
        'safe-area-context': re.compile(
            r"from\s+['\"]react-native-safe-area-context['\"]|"
            r"SafeAreaProvider|SafeAreaView|useSafeAreaInsets",
            re.MULTILINE
        ),

        # ── SVG ───────────────────────────────────────────────────
        'react-native-svg': re.compile(
            r"from\s+['\"]react-native-svg['\"]|"
            r"Svg|Circle|Rect|Path|G|Line|Polygon|Polyline",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'detox': re.compile(
            r"from\s+['\"]detox['\"]|"
            r"device\.launchApp|element\(by\.\w+|expect\(element\(",
            re.MULTILINE
        ),
        'testing-library-rn': re.compile(
            r"from\s+['\"]@testing-library/react-native['\"]|"
            r"render\s*\(|screen\.\w+|fireEvent\.\w+|waitFor\(",
            re.MULTILINE
        ),
        'maestro': re.compile(
            r"maestro|appId:|launchApp:|tapOn:|assertVisible:",
            re.MULTILINE
        ),

        # ── DevTools / Analytics ──────────────────────────────────
        'flipper': re.compile(
            r"from\s+['\"]react-native-flipper['\"]|addPlugin\(|Flipper",
            re.MULTILINE
        ),
        'sentry-rn': re.compile(
            r"from\s+['\"]@sentry/react-native['\"]|"
            r"Sentry\.init|Sentry\.captureException|Sentry\.wrap",
            re.MULTILINE
        ),
        'codepush': re.compile(
            r"from\s+['\"]react-native-code-push['\"]|"
            r"codePush\.\w+|CodePush\.sync",
            re.MULTILINE
        ),

        # ── Expo SDK ──────────────────────────────────────────────
        'expo': re.compile(
            r"from\s+['\"]expo['\"]|from\s+['\"]expo-|"
            r"from\s+['\"]@expo/|expo-constants|expo-updates|expo-splash-screen",
            re.MULTILINE
        ),
    }

    # React Native version detection features
    RN_VERSION_FEATURES = {
        # 0.76: New Architecture default
        'interop': '0.76',
        'Bridgeless': '0.76',

        # 0.74: Yoga 3.0
        'columnGap': '0.74',
        'rowGap': '0.74',

        # 0.73: debuggingOverlay
        'debuggingOverlay': '0.73',

        # 0.71: TypeScript default, gap property
        'gap': '0.71',

        # 0.70: Hermes default
        'Hermes': '0.70',

        # 0.68: New Architecture opt-in
        'TurboModuleRegistry': '0.68',
        'codegenNativeComponent': '0.68',
        'Fabric': '0.68',

        # 0.64: Hermes on iOS
        'HermesInternal': '0.64',

        # 0.63: LogBox, Pressable
        'LogBox': '0.63',
        'Pressable': '0.63',

        # 0.62: Flipper
        'Flipper': '0.62',

        # 0.60: Autolinking
        'autolinking': '0.60',

        # 0.59: Hooks support
        'useState': '0.59',
        'useEffect': '0.59',
    }

    def __init__(self):
        """Initialize the parser with all React Native extractors."""
        self.component_extractor = ReactNativeComponentExtractor()
        self.navigation_extractor = ReactNativeNavigationExtractor()
        self.native_module_extractor = ReactNativeNativeModuleExtractor()
        self.styling_extractor = ReactNativeStylingExtractor()
        self.platform_extractor = ReactNativePlatformExtractor()

    def parse(self, content: str, file_path: str = "") -> ReactNativeParseResult:
        """
        Parse React Native source code and extract all RN-specific information.

        This should be called AFTER the JavaScript/TypeScript parser and React
        parser have run, when React Native imports are detected. It extracts
        RN components, navigation, native modules, styling, and platform patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ReactNativeParseResult with all extracted React Native information
        """
        result = ReactNativeParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.animated_components = comp_result.get('animated_components', [])
        result.list_components = comp_result.get('list_components', [])

        # ── Extract navigation ────────────────────────────────────
        nav_result = self.navigation_extractor.extract(content, file_path)
        result.navigators = nav_result.get('navigators', [])
        result.screens = nav_result.get('screens', [])
        result.deep_links = nav_result.get('deep_links', [])

        # ── Extract native modules ────────────────────────────────
        native_result = self.native_module_extractor.extract(content, file_path)
        result.native_modules = native_result.get('native_modules', [])
        result.turbo_modules = native_result.get('turbo_modules', [])
        result.fabric_components = native_result.get('fabric_components', [])

        # ── Extract styling ───────────────────────────────────────
        style_result = self.styling_extractor.extract(content, file_path)
        result.stylesheets = style_result.get('stylesheets', [])
        result.dynamic_styles = style_result.get('dynamic_styles', [])
        result.themes = style_result.get('themes', [])

        # ── Extract platform patterns ─────────────────────────────
        platform_result = self.platform_extractor.extract(content, file_path)
        result.platform_usages = platform_result.get('platform_usages', [])
        result.platform_files = platform_result.get('platform_files', [])
        result.permissions = platform_result.get('permissions', [])

        # ── Detect RN version ─────────────────────────────────────
        result.rn_version = self._detect_rn_version(content)

        # ── Detect architecture ───────────────────────────────────
        result.architecture = self._detect_architecture(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which React Native ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_rn_version(self, content: str) -> str:
        """
        Detect the minimum React Native version required by the file.

        Returns version string (e.g., '0.76', '0.68', '0.59').
        """
        max_version = '0.0'
        for feature, version in self.RN_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    def _detect_architecture(self, content: str) -> str:
        """Detect which RN architecture the file targets."""
        if re.search(r'TurboModuleRegistry|codegenNativeComponent|Fabric', content):
            if re.search(r'Bridgeless|bridgeless', content):
                return "bridgeless"
            return "new_architecture"
        if re.search(r'\bNativeModules\b|requireNativeComponent', content):
            return "bridge"
        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_react_native_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains React Native code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains React Native code
        """
        # Platform-specific RN files
        if re.search(r'\.(ios|android|native)\.(js|jsx|ts|tsx)$', file_path):
            return True

        # Check for react-native imports
        if re.search(r"from\s+['\"]react-native['\"]", content):
            return True

        # Check for react-native-* imports
        if re.search(r"from\s+['\"]react-native-\w+", content):
            return True

        # Check for @react-navigation imports
        if re.search(r"from\s+['\"]@react-navigation/", content):
            return True

        # Check for expo imports
        if re.search(r"from\s+['\"]expo['\"]|from\s+['\"]expo-", content):
            return True

        # Check for RN-specific API usage
        if re.search(
            r'\bStyleSheet\.create\b|\bNativeModules\b|\bPlatform\.OS\b|'
            r'\bPermissionsAndroid\b|\bAppState\b|\bBackHandler\b',
            content
        ):
            return True

        # Check for core RN components (View, Text, etc.) imported from react-native
        if re.search(r"from\s+['\"]react-native['\"]", content) and re.search(
            r'\b(?:View|Text|Image|ScrollView|FlatList|TouchableOpacity|Pressable)\b',
            content
        ):
            return True

        return False
