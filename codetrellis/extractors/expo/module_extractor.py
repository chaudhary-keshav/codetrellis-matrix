"""
Expo Module Extractor for CodeTrellis

Extracts Expo SDK module usage from JS/TS source code:
- 50+ expo-* package imports and API usage
- Permission requests and declarations
- Asset usage (fonts, images, icons)
- Module categories (media, storage, location, auth, etc.)

Supports Expo SDK 44-52+ (all modern versions).

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ExpoModuleUsageInfo:
    """Information about an Expo SDK module usage."""
    module: str = ""  # e.g., 'expo-camera', 'expo-location'
    apis_used: List[str] = field(default_factory=list)
    category: str = ""  # media, storage, location, auth, ui, device, etc.
    is_async: bool = False
    requires_permission: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoPermissionInfo:
    """Information about an Expo permission request."""
    permission_type: str = ""  # camera, location, notifications, etc.
    hook_used: str = ""  # useCameraPermissions, requestForegroundPermissionsAsync, etc.
    is_foreground: bool = True
    is_background: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoAssetInfo:
    """Information about Expo asset usage (fonts, images, icons)."""
    asset_type: str = ""  # font, image, icon, audio, video
    source: str = ""  # e.g., 'expo-font', '@expo/vector-icons'
    names: List[str] = field(default_factory=list)
    is_preloaded: bool = False
    file: str = ""
    line_number: int = 0


# Expo SDK modules with their categories and permission requirements
EXPO_MODULES = {
    # Media
    'expo-camera': {'category': 'media', 'requires_permission': True},
    'expo-av': {'category': 'media', 'requires_permission': True},
    'expo-image-picker': {'category': 'media', 'requires_permission': True},
    'expo-media-library': {'category': 'media', 'requires_permission': True},
    'expo-video': {'category': 'media', 'requires_permission': False},
    'expo-image': {'category': 'media', 'requires_permission': False},
    'expo-image-manipulator': {'category': 'media', 'requires_permission': False},
    # Location
    'expo-location': {'category': 'location', 'requires_permission': True},
    'expo-task-manager': {'category': 'location', 'requires_permission': False},
    # Storage
    'expo-file-system': {'category': 'storage', 'requires_permission': False},
    'expo-secure-store': {'category': 'storage', 'requires_permission': False},
    'expo-sqlite': {'category': 'storage', 'requires_permission': False},
    'expo-document-picker': {'category': 'storage', 'requires_permission': False},
    # Notifications
    'expo-notifications': {'category': 'notifications', 'requires_permission': True},
    # Auth
    'expo-auth-session': {'category': 'auth', 'requires_permission': False},
    'expo-apple-authentication': {'category': 'auth', 'requires_permission': False},
    'expo-local-authentication': {'category': 'auth', 'requires_permission': True},
    'expo-web-browser': {'category': 'auth', 'requires_permission': False},
    # UI / UX
    'expo-splash-screen': {'category': 'ui', 'requires_permission': False},
    'expo-status-bar': {'category': 'ui', 'requires_permission': False},
    'expo-font': {'category': 'ui', 'requires_permission': False},
    'expo-linear-gradient': {'category': 'ui', 'requires_permission': False},
    'expo-blur': {'category': 'ui', 'requires_permission': False},
    'expo-haptics': {'category': 'ui', 'requires_permission': False},
    'expo-navigation-bar': {'category': 'ui', 'requires_permission': False},
    'expo-system-ui': {'category': 'ui', 'requires_permission': False},
    # Device
    'expo-constants': {'category': 'device', 'requires_permission': False},
    'expo-device': {'category': 'device', 'requires_permission': False},
    'expo-application': {'category': 'device', 'requires_permission': False},
    'expo-battery': {'category': 'device', 'requires_permission': False},
    'expo-brightness': {'category': 'device', 'requires_permission': False},
    'expo-cellular': {'category': 'device', 'requires_permission': False},
    'expo-network': {'category': 'device', 'requires_permission': False},
    'expo-sensors': {'category': 'device', 'requires_permission': False},
    'expo-barcode-scanner': {'category': 'device', 'requires_permission': True},
    # Sharing / Communication
    'expo-sharing': {'category': 'sharing', 'requires_permission': False},
    'expo-clipboard': {'category': 'sharing', 'requires_permission': False},
    'expo-linking': {'category': 'sharing', 'requires_permission': False},
    'expo-mail-composer': {'category': 'sharing', 'requires_permission': False},
    'expo-sms': {'category': 'sharing', 'requires_permission': False},
    'expo-contacts': {'category': 'sharing', 'requires_permission': True},
    'expo-calendar': {'category': 'sharing', 'requires_permission': True},
    # Updates / OTA
    'expo-updates': {'category': 'updates', 'requires_permission': False},
    # Maps / Geo
    'expo-map-view': {'category': 'maps', 'requires_permission': True},
    # Crypto
    'expo-crypto': {'category': 'crypto', 'requires_permission': False},
    'expo-random': {'category': 'crypto', 'requires_permission': False},
    # Misc
    'expo-keep-awake': {'category': 'misc', 'requires_permission': False},
    'expo-screen-capture': {'category': 'misc', 'requires_permission': False},
    'expo-screen-orientation': {'category': 'misc', 'requires_permission': False},
    'expo-print': {'category': 'misc', 'requires_permission': False},
    'expo-store-review': {'category': 'misc', 'requires_permission': False},
    'expo-localization': {'category': 'misc', 'requires_permission': False},
    'expo-intent-launcher': {'category': 'misc', 'requires_permission': False},
}


class ExpoModuleExtractor:
    """
    Extracts Expo SDK module usage from source code.

    Detects:
    - expo-* package imports (50+ modules)
    - API method calls for each module
    - Permission request patterns
    - Font loading and asset preloading
    - @expo/vector-icons usage
    """

    EXPO_IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:\*\s+as\s+\w+|\{[^}]*\}|\w+(?:\s*,\s*\{[^}]*\})?)\s+from\s+['\"]"
        r"(expo[\w/-]*)['\"]|"
        r"require\(['\"]"
        r"(expo[\w/-]*)['\"]"
        r"\))",
        re.MULTILINE
    )

    EXPO_ICON_IMPORT = re.compile(
        r"from\s+['\"]@expo/vector-icons(?:/(\w+))?['\"]",
        re.MULTILINE
    )

    PERMISSION_PATTERNS = {
        'camera': re.compile(
            r"useCameraPermissions|requestCameraPermissionsAsync|"
            r"Camera\.requestCameraPermissionsAsync",
            re.MULTILINE
        ),
        'location_foreground': re.compile(
            r"requestForegroundPermissionsAsync|"
            r"useForegroundPermissions",
            re.MULTILINE
        ),
        'location_background': re.compile(
            r"requestBackgroundPermissionsAsync|"
            r"useBackgroundPermissions",
            re.MULTILINE
        ),
        'media_library': re.compile(
            r"requestPermissionsAsync.*MediaLibrary|"
            r"MediaLibrary\.requestPermissionsAsync",
            re.MULTILINE
        ),
        'notifications': re.compile(
            r"requestPermissionsAsync.*Notifications|"
            r"Notifications\.requestPermissionsAsync|"
            r"getPermissionsAsync.*Notifications",
            re.MULTILINE
        ),
        'contacts': re.compile(
            r"requestPermissionsAsync.*Contacts|"
            r"Contacts\.requestPermissionsAsync",
            re.MULTILINE
        ),
        'calendar': re.compile(
            r"requestCalendarPermissionsAsync|"
            r"Calendar\.requestCalendarPermissionsAsync",
            re.MULTILINE
        ),
        'audio': re.compile(
            r"requestPermissionsAsync.*Audio|"
            r"Audio\.requestPermissionsAsync|"
            r"setAudioModeAsync",
            re.MULTILINE
        ),
    }

    FONT_LOAD_PATTERN = re.compile(
        r"useFonts\s*\(|Font\.loadAsync\s*\(|loadAsync\s*\(",
        re.MULTILINE
    )

    ASSET_PRELOAD_PATTERN = re.compile(
        r"Asset\.loadAsync|Asset\.fromModule|useAssets\s*\(",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Expo module usage from source code."""
        result: Dict[str, Any] = {
            'modules': [],
            'permissions': [],
            'assets': [],
        }

        self._extract_module_imports(content, file_path, result)
        self._extract_permissions(content, file_path, result)
        self._extract_assets(content, file_path, result)

        return result

    def _extract_module_imports(self, content: str, file_path: str,
                                result: Dict[str, Any]) -> None:
        """Extract expo-* module imports and API usage."""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for m in self.EXPO_IMPORT_PATTERN.finditer(line):
                module = m.group(1) or m.group(2)
                if not module:
                    continue

                # Normalize module name (strip subpath)
                base_module = module.split('/')[0]
                if base_module.startswith('expo-') or base_module == 'expo':
                    module_info = EXPO_MODULES.get(base_module, {})

                    # Extract named imports as APIs used
                    apis: List[str] = []
                    named_m = re.search(r"\{([^}]+)\}", line)
                    if named_m:
                        apis = [a.strip().split(' as ')[0].strip()
                                for a in named_m.group(1).split(',')
                                if a.strip()]

                    usage = ExpoModuleUsageInfo(
                        module=base_module,
                        apis_used=apis[:20],  # Cap
                        category=module_info.get('category', 'misc'),
                        requires_permission=module_info.get('requires_permission', False),
                        file=file_path,
                        line_number=i,
                    )

                    # Check if any API call is async
                    if re.search(r'await\s+\w+', line) or 'Async' in line:
                        usage.is_async = True

                    result['modules'].append(usage)

    def _extract_permissions(self, content: str, file_path: str,
                             result: Dict[str, Any]) -> None:
        """Extract Expo permission request patterns."""
        for perm_type, pattern in self.PERMISSION_PATTERNS.items():
            for m in pattern.finditer(content):
                # Find line number
                line_num = content[:m.start()].count('\n') + 1
                hook = m.group(0).strip()

                perm = ExpoPermissionInfo(
                    permission_type=perm_type.replace('_foreground', '').replace('_background', ''),
                    hook_used=hook[:100],
                    is_foreground='foreground' in perm_type.lower() or 'background' not in perm_type.lower(),
                    is_background='background' in perm_type.lower(),
                    file=file_path,
                    line_number=line_num,
                )
                result['permissions'].append(perm)

    def _extract_assets(self, content: str, file_path: str,
                        result: Dict[str, Any]) -> None:
        """Extract font loading and asset preloading patterns."""
        # Font loading
        for m in self.FONT_LOAD_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1

            # Try to extract font names from the surrounding code
            font_names: List[str] = []
            context = content[m.start():min(m.start() + 500, len(content))]
            for fm in re.finditer(r"['\"]([^'\"]+)['\"]", context):
                name = fm.group(1)
                if not name.startswith(('expo', '@', './', '../', 'http')):
                    font_names.append(name)
                if len(font_names) >= 10:
                    break

            result['assets'].append(ExpoAssetInfo(
                asset_type='font',
                source='expo-font',
                names=font_names,
                is_preloaded=True,
                file=file_path,
                line_number=line_num,
            ))

        # Vector icons
        for m in self.EXPO_ICON_IMPORT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            icon_family = m.group(1) or 'multiple'
            result['assets'].append(ExpoAssetInfo(
                asset_type='icon',
                source='@expo/vector-icons',
                names=[icon_family],
                file=file_path,
                line_number=line_num,
            ))

        # Asset preloading
        for m in self.ASSET_PRELOAD_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            result['assets'].append(ExpoAssetInfo(
                asset_type='image',
                source='expo-asset',
                is_preloaded=True,
                file=file_path,
                line_number=line_num,
            ))
