"""
Enhanced Expo Parser for CodeTrellis

Comprehensive Expo framework parser with full extractor support.
Parses Expo configuration, SDK modules, Expo Router, config plugins,
and EAS integration from JavaScript/TypeScript source code and config files.

This parser runs as a FRAMEWORK-LEVEL overlay on JS/TS files when Expo
imports are detected. It should be called AFTER the base JavaScript/TypeScript
parser, React parser, and React Native parser have run.

Supported Expo SDK versions:
- SDK 44+ (EAS Build GA, expo-dev-client)
- SDK 45+ (Expo Modules API, hermes default)
- SDK 46+ (EAS Update GA)
- SDK 47+ (Expo Router beta)
- SDK 48+ (Expo Router v1 stable)
- SDK 49+ (Expo Router v2, expo-image, local Expo Modules)
- SDK 50+ (Expo Router v3, new architecture preview)
- SDK 51+ (New Architecture support, expo-camera v15, expo-video, expo-sqlite next)
- SDK 52+ (React 19, new architecture default, React Compiler)

Framework detection supports 60+ Expo ecosystem patterns:
- Core (expo, expo-constants, expo-updates, expo-dev-client)
- Router (expo-router v1-v3, file-based routing, API routes, typed routes)
- Media (expo-camera, expo-av, expo-image-picker, expo-image, expo-video)
- Location (expo-location, expo-task-manager, background location)
- Storage (expo-file-system, expo-secure-store, expo-sqlite)
- Notifications (expo-notifications, push tokens, scheduling)
- Auth (expo-auth-session, expo-apple-authentication, expo-local-authentication)
- UI (expo-splash-screen, expo-font, expo-linear-gradient, expo-blur, expo-haptics)
- Device (expo-device, expo-application, expo-battery, expo-sensors, expo-constants)
- Config Plugins (@expo/config-plugins, withAndroidManifest, withInfoPlist)
- Expo Modules API (expo-modules-core, native module definitions)
- EAS (eas-cli, EAS Build, EAS Update, EAS Submit, EAS Metadata)
- Icons (@expo/vector-icons)
- Linking (expo-linking, deep links, universal links)
- OTA Updates (expo-updates, runtime versioning, update channels)

Optional AST: tree-sitter-javascript / tree-sitter-typescript
Optional LSP: typescript-language-server (tsserver)

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from codetrellis.extractors.expo import (
    ExpoConfigExtractor,
    ExpoConfigInfo,
    ExpoEASConfigInfo,
    ExpoPluginConfigInfo,
    ExpoModuleExtractor,
    ExpoModuleUsageInfo,
    ExpoPermissionInfo,
    ExpoAssetInfo,
    ExpoRouterExtractor,
    ExpoRouteInfo,
    ExpoLayoutInfo,
    ExpoRouteGroupInfo,
    ExpoApiRouteInfo,
    ExpoPluginExtractor,
    ExpoConfigPluginInfo,
    ExpoModulesAPIInfo,
    ExpoApiExtractor,
    ExpoImportInfo,
    ExpoIntegrationInfo,
    ExpoEASInfo,
)


@dataclass
class ExpoParseResult:
    """Result from parsing an Expo source file or config."""
    file_path: str = ""
    file_type: str = ""  # jsx, tsx, js, ts, json

    # Config (app.json, app.config.js, eas.json)
    config: ExpoConfigInfo = field(default_factory=ExpoConfigInfo)
    eas_config: ExpoEASConfigInfo = field(default_factory=ExpoEASConfigInfo)
    config_plugins_declared: List[ExpoPluginConfigInfo] = field(default_factory=list)

    # SDK Modules
    modules: List[ExpoModuleUsageInfo] = field(default_factory=list)
    permissions: List[ExpoPermissionInfo] = field(default_factory=list)
    assets: List[ExpoAssetInfo] = field(default_factory=list)

    # Expo Router
    routes: List[ExpoRouteInfo] = field(default_factory=list)
    layouts: List[ExpoLayoutInfo] = field(default_factory=list)
    route_groups: List[ExpoRouteGroupInfo] = field(default_factory=list)
    api_routes: List[ExpoApiRouteInfo] = field(default_factory=list)
    navigation_hooks: List[str] = field(default_factory=list)
    router_version: int = 0

    # Config Plugins & Modules API
    config_plugins: List[ExpoConfigPluginInfo] = field(default_factory=list)
    modules_api: List[ExpoModulesAPIInfo] = field(default_factory=list)
    has_custom_plugins: bool = False

    # API / Ecosystem
    imports: ExpoImportInfo = field(default_factory=ExpoImportInfo)
    integrations: List[ExpoIntegrationInfo] = field(default_factory=list)
    eas: ExpoEASInfo = field(default_factory=ExpoEASInfo)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    sdk_version: int = 0  # Detected SDK version (44-52+)
    workflow: str = ""  # 'managed' or 'bare'


class EnhancedExpoParser:
    """
    Enhanced Expo parser that uses all extractors for comprehensive parsing.

    Framework detection supports 60+ Expo ecosystem patterns across:
    - Core SDK (expo-constants, expo-updates, expo-dev-client, expo-modules-core)
    - Expo Router (v1-v3, file-based routing, layouts, groups, API routes, typed routes)
    - Media (expo-camera, expo-av, expo-image-picker, expo-image, expo-video)
    - Location (expo-location, geofencing, background location)
    - Storage (expo-file-system, expo-secure-store, expo-sqlite)
    - Notifications (expo-notifications, push tokens, scheduling, categories)
    - Auth (expo-auth-session, expo-apple-authentication, expo-local-authentication)
    - UI (expo-splash-screen, expo-font, expo-linear-gradient, expo-blur, expo-haptics)
    - Device (expo-device, expo-application, expo-battery, expo-sensors)
    - Config Plugins (@expo/config-plugins custom native modifications)
    - Expo Modules API (Swift/Kotlin native module definitions)
    - EAS (Build, Update, Submit, Metadata)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Expo ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'expo': re.compile(
            r"from\s+['\"]expo['\"]|"
            r"from\s+['\"]expo/|"
            r"require\(['\"]expo['\"]\)",
            re.MULTILINE
        ),
        'expo-constants': re.compile(
            r"from\s+['\"]expo-constants['\"]|"
            r"Constants\.expoConfig|Constants\.manifest|"
            r"Constants\.appOwnership",
            re.MULTILINE
        ),
        'expo-updates': re.compile(
            r"from\s+['\"]expo-updates['\"]|"
            r"Updates\.checkForUpdateAsync|Updates\.fetchUpdateAsync|"
            r"useUpdates\b",
            re.MULTILINE
        ),
        'expo-dev-client': re.compile(
            r"from\s+['\"]expo-dev-client['\"]|"
            r"expo-dev-launcher|expo-dev-menu",
            re.MULTILINE
        ),
        'expo-modules-core': re.compile(
            r"from\s+['\"]expo-modules-core['\"]|"
            r"from\s+['\"]expo['\"].*NativeModulesProxy|"
            r"requireNativeModule|requireOptionalNativeModule",
            re.MULTILINE
        ),

        # ── Router ────────────────────────────────────────────────
        'expo-router': re.compile(
            r"from\s+['\"]expo-router['\"]|"
            r"useRouter|useLocalSearchParams|useGlobalSearchParams|"
            r"useSegments|usePathname|<Link\s|<Redirect\s|"
            r"\bStack\b.*expo-router|\bTabs\b.*expo-router|"
            r"\bDrawer\b.*expo-router|\bSlot\b.*expo-router",
            re.MULTILINE
        ),

        # ── Media ─────────────────────────────────────────────────
        'expo-camera': re.compile(
            r"from\s+['\"]expo-camera['\"]|"
            r"CameraView|useCameraPermissions|CameraType",
            re.MULTILINE
        ),
        'expo-av': re.compile(
            r"from\s+['\"]expo-av['\"]|"
            r"Audio\.Sound|Audio\.Recording|Video\b.*expo|"
            r"useAudioPlayer\b",
            re.MULTILINE
        ),
        'expo-image-picker': re.compile(
            r"from\s+['\"]expo-image-picker['\"]|"
            r"launchImageLibraryAsync|launchCameraAsync|MediaTypeOptions",
            re.MULTILINE
        ),
        'expo-image': re.compile(
            r"from\s+['\"]expo-image['\"]|"
            r"Image\b.*expo-image|ImageContentFit",
            re.MULTILINE
        ),
        'expo-video': re.compile(
            r"from\s+['\"]expo-video['\"]|"
            r"useVideoPlayer|VideoView",
            re.MULTILINE
        ),
        'expo-media-library': re.compile(
            r"from\s+['\"]expo-media-library['\"]|"
            r"MediaLibrary\.\w+",
            re.MULTILINE
        ),

        # ── Location ─────────────────────────────────────────────
        'expo-location': re.compile(
            r"from\s+['\"]expo-location['\"]|"
            r"requestForegroundPermissionsAsync|"
            r"getCurrentPositionAsync|watchPositionAsync|"
            r"startGeofencingAsync|LocationAccuracy",
            re.MULTILINE
        ),
        'expo-task-manager': re.compile(
            r"from\s+['\"]expo-task-manager['\"]|"
            r"TaskManager\.defineTask|isTaskRegisteredAsync",
            re.MULTILINE
        ),

        # ── Storage ───────────────────────────────────────────────
        'expo-file-system': re.compile(
            r"from\s+['\"]expo-file-system['\"]|"
            r"FileSystem\.documentDirectory|FileSystem\.readAsStringAsync|"
            r"FileSystem\.writeAsStringAsync|FileSystem\.downloadAsync",
            re.MULTILINE
        ),
        'expo-secure-store': re.compile(
            r"from\s+['\"]expo-secure-store['\"]|"
            r"SecureStore\.getItemAsync|SecureStore\.setItemAsync",
            re.MULTILINE
        ),
        'expo-sqlite': re.compile(
            r"from\s+['\"]expo-sqlite['\"]|"
            r"openDatabaseSync|openDatabaseAsync|useSQLiteContext",
            re.MULTILINE
        ),
        'expo-document-picker': re.compile(
            r"from\s+['\"]expo-document-picker['\"]|"
            r"getDocumentAsync",
            re.MULTILINE
        ),

        # ── Notifications ─────────────────────────────────────────
        'expo-notifications': re.compile(
            r"from\s+['\"]expo-notifications['\"]|"
            r"getExpoPushTokenAsync|scheduleNotificationAsync|"
            r"setNotificationHandler|addNotificationReceivedListener|"
            r"addNotificationResponseReceivedListener",
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'expo-auth-session': re.compile(
            r"from\s+['\"]expo-auth-session['\"]|"
            r"useAuthRequest|makeRedirectUri|AuthSession\.\w+|"
            r"TokenResponse|exchangeCodeAsync",
            re.MULTILINE
        ),
        'expo-apple-authentication': re.compile(
            r"from\s+['\"]expo-apple-authentication['\"]|"
            r"AppleAuthentication\.\w+|AppleAuthenticationButton",
            re.MULTILINE
        ),
        'expo-local-authentication': re.compile(
            r"from\s+['\"]expo-local-authentication['\"]|"
            r"authenticateAsync|hasHardwareAsync|isEnrolledAsync|"
            r"LocalAuthentication\.\w+",
            re.MULTILINE
        ),
        'expo-web-browser': re.compile(
            r"from\s+['\"]expo-web-browser['\"]|"
            r"WebBrowser\.openBrowserAsync|WebBrowser\.warmUpAsync|"
            r"maybeCompleteAuthSession",
            re.MULTILINE
        ),

        # ── UI / UX ──────────────────────────────────────────────
        'expo-splash-screen': re.compile(
            r"from\s+['\"]expo-splash-screen['\"]|"
            r"SplashScreen\.preventAutoHideAsync|SplashScreen\.hideAsync",
            re.MULTILINE
        ),
        'expo-font': re.compile(
            r"from\s+['\"]expo-font['\"]|"
            r"useFonts|Font\.loadAsync",
            re.MULTILINE
        ),
        'expo-linear-gradient': re.compile(
            r"from\s+['\"]expo-linear-gradient['\"]|"
            r"LinearGradient\b",
            re.MULTILINE
        ),
        'expo-blur': re.compile(
            r"from\s+['\"]expo-blur['\"]|"
            r"BlurView\b|BlurTint",
            re.MULTILINE
        ),
        'expo-haptics': re.compile(
            r"from\s+['\"]expo-haptics['\"]|"
            r"Haptics\.impactAsync|Haptics\.notificationAsync|"
            r"Haptics\.selectionAsync|ImpactFeedbackStyle",
            re.MULTILINE
        ),
        'expo-status-bar': re.compile(
            r"from\s+['\"]expo-status-bar['\"]|"
            r"StatusBar\b.*expo|setStatusBarStyle",
            re.MULTILINE
        ),
        'expo-navigation-bar': re.compile(
            r"from\s+['\"]expo-navigation-bar['\"]|"
            r"NavigationBar\.setBackgroundColorAsync",
            re.MULTILINE
        ),
        'expo-system-ui': re.compile(
            r"from\s+['\"]expo-system-ui['\"]|"
            r"setBackgroundColorAsync",
            re.MULTILINE
        ),

        # ── Device ────────────────────────────────────────────────
        'expo-device': re.compile(
            r"from\s+['\"]expo-device['\"]|"
            r"Device\.isDevice|Device\.modelName|Device\.brand",
            re.MULTILINE
        ),
        'expo-application': re.compile(
            r"from\s+['\"]expo-application['\"]|"
            r"Application\.applicationId|Application\.nativeBuildVersion",
            re.MULTILINE
        ),
        'expo-battery': re.compile(
            r"from\s+['\"]expo-battery['\"]|"
            r"Battery\.getBatteryLevelAsync|useBatteryLevel",
            re.MULTILINE
        ),
        'expo-sensors': re.compile(
            r"from\s+['\"]expo-sensors['\"]|"
            r"Accelerometer|Gyroscope|Magnetometer|Barometer|"
            r"Pedometer|DeviceMotion|LightSensor",
            re.MULTILINE
        ),
        'expo-network': re.compile(
            r"from\s+['\"]expo-network['\"]|"
            r"getNetworkStateAsync|getIpAddressAsync",
            re.MULTILINE
        ),
        'expo-brightness': re.compile(
            r"from\s+['\"]expo-brightness['\"]|"
            r"Brightness\.getBrightnessAsync|setBrightnessAsync",
            re.MULTILINE
        ),

        # ── Sharing / Communication ───────────────────────────────
        'expo-sharing': re.compile(
            r"from\s+['\"]expo-sharing['\"]|"
            r"Sharing\.shareAsync|isAvailableAsync.*Sharing",
            re.MULTILINE
        ),
        'expo-clipboard': re.compile(
            r"from\s+['\"]expo-clipboard['\"]|"
            r"Clipboard\.setStringAsync|Clipboard\.getStringAsync",
            re.MULTILINE
        ),
        'expo-linking': re.compile(
            r"from\s+['\"]expo-linking['\"]|"
            r"Linking\.createURL|Linking\.openURL|useURL\b",
            re.MULTILINE
        ),
        'expo-mail-composer': re.compile(
            r"from\s+['\"]expo-mail-composer['\"]|"
            r"MailComposer\.composeAsync",
            re.MULTILINE
        ),
        'expo-contacts': re.compile(
            r"from\s+['\"]expo-contacts['\"]|"
            r"Contacts\.getContactsAsync|Contacts\.requestPermissionsAsync",
            re.MULTILINE
        ),
        'expo-calendar': re.compile(
            r"from\s+['\"]expo-calendar['\"]|"
            r"Calendar\.getCalendarsAsync|Calendar\.createEventAsync",
            re.MULTILINE
        ),

        # ── Updates / OTA ─────────────────────────────────────────
        'eas-update': re.compile(
            r"eas\s+update|EAS\s+Update|Updates\.checkForUpdateAsync|"
            r"runtimeVersion|useUpdates",
            re.MULTILINE
        ),

        # ── Crypto ────────────────────────────────────────────────
        'expo-crypto': re.compile(
            r"from\s+['\"]expo-crypto['\"]|"
            r"Crypto\.digestStringAsync|Crypto\.getRandomBytesAsync",
            re.MULTILINE
        ),

        # ── Config Plugins ────────────────────────────────────────
        'expo-config-plugins': re.compile(
            r"from\s+['\"]@expo/config-plugins['\"]|"
            r"from\s+['\"]expo/config-plugins['\"]|"
            r"withAndroidManifest|withInfoPlist|withAppDelegate|"
            r"withDangerousMod|withPlugins",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'expo-vector-icons': re.compile(
            r"from\s+['\"]@expo/vector-icons['\"]|"
            r"from\s+['\"]@expo/vector-icons/|"
            r"Ionicons|MaterialIcons|FontAwesome|"
            r"MaterialCommunityIcons|Feather|AntDesign",
            re.MULTILINE
        ),

        # ── Misc ──────────────────────────────────────────────────
        'expo-keep-awake': re.compile(
            r"from\s+['\"]expo-keep-awake['\"]|"
            r"useKeepAwake|activateKeepAwake",
            re.MULTILINE
        ),
        'expo-screen-orientation': re.compile(
            r"from\s+['\"]expo-screen-orientation['\"]|"
            r"ScreenOrientation\.\w+|OrientationLock",
            re.MULTILINE
        ),
        'expo-localization': re.compile(
            r"from\s+['\"]expo-localization['\"]|"
            r"getLocales|useCalendars|getCalendars",
            re.MULTILINE
        ),
        'expo-print': re.compile(
            r"from\s+['\"]expo-print['\"]|"
            r"Print\.printAsync|Print\.printToFileAsync",
            re.MULTILINE
        ),
        'expo-store-review': re.compile(
            r"from\s+['\"]expo-store-review['\"]|"
            r"StoreReview\.requestReview|isAvailableAsync.*StoreReview",
            re.MULTILINE
        ),
    }

    # SDK version detection: feature → minimum SDK version
    SDK_VERSION_FEATURES = {
        # SDK 52: React 19, new architecture default, React Compiler
        'React Compiler': 52,
        'react-compiler': 52,
        'useFormStatus': 52,
        'useOptimistic': 52,

        # SDK 51: New Architecture support, new APIs
        'expo-video': 51,
        'VideoView': 51,
        'useSQLiteContext': 51,
        'CameraView': 51,
        'useVideoPlayer': 51,

        # SDK 50: Expo Router v3, typed routes
        'Href': 50,
        'useRouter<': 50,
        'router.push<': 50,
        'Link<': 50,
        'expo-router/typed-routes': 50,

        # SDK 49: Expo Router v2, expo-image
        'expo-image': 49,
        'ImageContentFit': 49,
        'useSegments': 49,

        # SDK 48: Expo Router v1 stable
        'useLocalSearchParams': 48,

        # SDK 47: Expo Router beta
        'expo-router': 47,

        # SDK 46: EAS Update GA
        'Updates.checkForUpdateAsync': 46,

        # SDK 45: Expo Modules API, Hermes default
        'requireNativeModule': 45,
        'expo-modules-core': 45,

        # SDK 44: EAS Build GA, dev client
        'expo-dev-client': 44,
    }

    def __init__(self) -> None:
        """Initialize the parser with all Expo extractors."""
        self.config_extractor = ExpoConfigExtractor()
        self.module_extractor = ExpoModuleExtractor()
        self.router_extractor = ExpoRouterExtractor()
        self.plugin_extractor = ExpoPluginExtractor()
        self.api_extractor = ExpoApiExtractor()

    def parse(self, content: str, file_path: str = "") -> ExpoParseResult:
        """
        Parse Expo source code and extract all Expo-specific information.

        This should be called AFTER the JavaScript/TypeScript parser, React
        parser, and React Native parser have run, when Expo imports are detected.
        It extracts Expo config, SDK modules, router patterns, config plugins,
        and EAS integration information.

        Args:
            content: Source code or config file content
            file_path: Path to source file

        Returns:
            ExpoParseResult with all extracted Expo information
        """
        result = ExpoParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        elif file_path.endswith('.json'):
            result.file_type = "json"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract config (app.json, eas.json, etc.) ────────────
        config_result = self.config_extractor.extract(content, file_path)
        configs = config_result.get('configs', [])
        if configs:
            result.config = configs[0]
        eas_configs = config_result.get('eas_configs', [])
        if eas_configs:
            result.eas_config = eas_configs[0]
        result.config_plugins_declared = config_result.get('plugin_configs', [])

        # ── Extract SDK modules ───────────────────────────────────
        module_result = self.module_extractor.extract(content, file_path)
        result.modules = module_result.get('modules', [])
        result.permissions = module_result.get('permissions', [])
        result.assets = module_result.get('assets', [])

        # ── Extract router patterns ──────────────────────────────
        router_result = self.router_extractor.extract(content, file_path)
        result.routes = router_result.get('routes', [])
        result.layouts = router_result.get('layouts', [])
        result.route_groups = router_result.get('route_groups', [])
        result.api_routes = router_result.get('api_routes', [])
        result.navigation_hooks = router_result.get('navigation_hooks', [])
        result.router_version = router_result.get('router_version', 0)

        # ── Extract config plugins ────────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.config_plugins = plugin_result.get('config_plugins', [])
        result.modules_api = plugin_result.get('modules_api', [])
        result.has_custom_plugins = plugin_result.get('has_custom_plugins', False)

        # ── Extract API / ecosystem ──────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        if api_result.get('imports'):
            result.imports = api_result['imports']
        result.integrations = api_result.get('integrations', [])
        if api_result.get('eas'):
            result.eas = api_result['eas']
        result.workflow = api_result.get('workflow', '')

        # ── Detect SDK version ───────────────────────────────────
        result.sdk_version = self._detect_sdk_version(content)
        # Also incorporate version from config
        if result.config.sdk_version:
            try:
                config_sdk = int(result.config.sdk_version.split('.')[0])
                result.sdk_version = max(result.sdk_version, config_sdk)
            except (ValueError, IndexError):
                pass
        # Also from api_result
        if api_result.get('sdk_version', 0) > result.sdk_version:
            result.sdk_version = api_result['sdk_version']

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Expo ecosystem frameworks/libraries are used."""
        frameworks: List[str] = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_sdk_version(self, content: str) -> int:
        """
        Detect the minimum Expo SDK version required by the file.

        Returns SDK version number (e.g., 52, 51, 50, etc.).
        """
        max_version = 0
        for feature, version in self.SDK_VERSION_FEATURES.items():
            if feature in content:
                if version > max_version:
                    max_version = version
        return max_version

    def is_expo_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Expo code worth parsing with this parser.

        This checks for Expo-specific patterns beyond what the React Native
        parser already detects. Files that are purely React Native (without
        Expo SDK usage) will return False.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Expo-specific code
        """
        # Config files
        basename = file_path.split('/')[-1] if file_path else ''
        if basename in ('app.json', 'app.config.js', 'app.config.ts', 'eas.json'):
            return True

        # Expo Router app/ directory files
        if '/app/' in file_path or file_path.startswith('app/'):
            if re.search(r'\.(jsx?|tsx?)$', file_path):
                return True

        # Config plugin files
        if 'plugin' in file_path.lower() and file_path.endswith(('.js', '.ts')):
            if re.search(r'@expo/config-plugins|withAndroid|withIos|withInfo', content):
                return True

        # Expo Modules API (native modules)
        if file_path.endswith(('.swift', '.kt')) and 'expo' in content.lower():
            return True

        # Check for expo-* imports (beyond the basic 'expo' import)
        if re.search(r"from\s+['\"]expo-\w+['\"]", content):
            return True

        # Check for @expo/* imports
        if re.search(r"from\s+['\"]@expo/", content):
            return True

        # Check for Expo-specific APIs
        if re.search(
            r'Constants\.expoConfig|SplashScreen\.preventAutoHideAsync|'
            r'Updates\.checkForUpdateAsync|registerRootComponent|'
            r'getExpoPushTokenAsync',
            content
        ):
            return True

        return False

    def is_config_file(self, file_path: str) -> bool:
        """Check if a file is an Expo config file."""
        basename = file_path.split('/')[-1] if file_path else ''
        return basename in ('app.json', 'app.config.js', 'app.config.ts', 'eas.json')
