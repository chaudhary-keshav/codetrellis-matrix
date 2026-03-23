"""
Expo Plugin Extractor for CodeTrellis

Extracts Expo config plugin and Expo Modules API patterns:
- Config plugins in app.json/app.config.js
- Custom config plugins (withAndroidManifest, withInfoPlist, etc.)
- Expo Modules API (native module definitions)
- Plugin composition patterns

Supports Expo SDK 44-52+.

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ExpoConfigPluginInfo:
    """Information about an Expo config plugin."""
    name: str = ""  # e.g., 'expo-camera', './my-plugin'
    options: Dict[str, Any] = field(default_factory=dict)
    is_custom: bool = False
    is_inline: bool = False  # Defined inline vs separate file
    modifies_android: bool = False
    modifies_ios: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoModulesAPIInfo:
    """Information about Expo Modules API usage (native modules)."""
    module_name: str = ""
    language: str = ""  # swift, kotlin, cpp
    has_view: bool = False
    has_events: bool = False
    has_async_function: bool = False
    exported_methods: List[str] = field(default_factory=list)
    exported_properties: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


# Well-known Expo config plugins
KNOWN_PLUGINS = {
    'expo-camera', 'expo-location', 'expo-notifications',
    'expo-media-library', 'expo-contacts', 'expo-calendar',
    'expo-sensors', 'expo-av', 'expo-image-picker',
    'expo-file-system', 'expo-local-authentication',
    'expo-barcode-scanner', 'expo-screen-orientation',
    'expo-screen-capture', 'expo-brightness', 'expo-build-properties',
    'expo-splash-screen', 'expo-font', 'expo-updates',
    'expo-apple-authentication', 'expo-dev-client',
    'expo-router', 'expo-localization', 'expo-secure-store',
    'expo-navigation-bar', 'expo-system-ui',
    'expo-document-picker', 'expo-sqlite',
    '@react-native-firebase/app', 'react-native-maps',
    'sentry-expo', '@sentry/react-native',
}


class ExpoPluginExtractor:
    """
    Extracts Expo config plugin and Modules API patterns.

    Detects:
    - Plugin declarations in app.json/app.config.js
    - Custom config plugins (withAndroidManifest, withInfoPlist, etc.)
    - Expo Modules API definitions (Swift/Kotlin/C++ native modules)
    - Plugin modifier patterns (withDangerousMod, withPlugins, etc.)
    """

    # Config plugin patterns in app.json/app.config.js
    PLUGIN_ARRAY_PATTERN = re.compile(
        r'"plugins"\s*:\s*\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]',
        re.MULTILINE | re.DOTALL
    )

    PLUGIN_ENTRY_PATTERN = re.compile(
        r'["\']([^"\']+)["\']',
    )

    # Custom config plugin patterns
    WITH_ANDROID_MANIFEST = re.compile(
        r"withAndroidManifest\s*\(", re.MULTILINE
    )
    WITH_INFO_PLIST = re.compile(
        r"withInfoPlist\s*\(", re.MULTILINE
    )
    WITH_APP_DELEGATE = re.compile(
        r"withAppDelegate\s*\(", re.MULTILINE
    )
    WITH_DANGEROUS_MOD = re.compile(
        r"withDangerousMod\s*\(", re.MULTILINE
    )
    WITH_PLUGINS = re.compile(
        r"withPlugins\s*\(", re.MULTILINE
    )
    WITH_GRADLE_PROPERTIES = re.compile(
        r"withGradleProperties\s*\(", re.MULTILINE
    )
    WITH_ANDROID_COLORS = re.compile(
        r"withAndroidColors\s*\(|withAndroidStyles\s*\(", re.MULTILINE
    )
    WITH_ENTITLEMENTS = re.compile(
        r"withEntitlementsPlist\s*\(", re.MULTILINE
    )

    # Config plugin imports
    CONFIG_PLUGIN_IMPORT = re.compile(
        r"from\s+['\"]@expo/config-plugins['\"]|"
        r"from\s+['\"]expo/config-plugins['\"]|"
        r"require\(['\"]@expo/config-plugins['\"]\)",
        re.MULTILINE
    )

    # Expo Modules API patterns
    EXPO_MODULE_DEF = re.compile(
        r"(?:Module|Name)\s*\(\s*['\"](\w+)['\"]", re.MULTILINE
    )
    EXPO_MODULE_FUNCTION = re.compile(
        r"(?:AsyncFunction|Function)\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE
    )
    EXPO_MODULE_PROPERTY = re.compile(
        r"Property\s*\(\s*['\"](\w+)['\"]", re.MULTILINE
    )
    EXPO_MODULE_EVENT = re.compile(
        r"Events\s*\(|sendEvent\s*\(", re.MULTILINE
    )
    EXPO_MODULE_VIEW = re.compile(
        r"ViewDefinition\s*\(|View\s*\(\s*\w+\.self", re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Expo plugin patterns from source code."""
        result: Dict[str, Any] = {
            'config_plugins': [],
            'modules_api': [],
            'has_custom_plugins': False,
            'plugin_count': 0,
        }

        self._extract_config_plugins(content, file_path, result)
        self._extract_custom_plugins(content, file_path, result)
        self._extract_modules_api(content, file_path, result)

        result['plugin_count'] = len(result['config_plugins'])

        return result

    def _extract_config_plugins(self, content: str, file_path: str,
                                result: Dict[str, Any]) -> None:
        """Extract plugins from app.json/app.config.js plugins array."""
        m = self.PLUGIN_ARRAY_PATTERN.search(content)
        if not m:
            return

        plugins_str = m.group(1)
        for pm in self.PLUGIN_ENTRY_PATTERN.finditer(plugins_str):
            name = pm.group(1)
            # Skip if it looks like a config value rather than plugin name
            if '/' not in name and '-' not in name and '.' not in name and not name.startswith('@'):
                if name not in KNOWN_PLUGINS and not name.startswith('expo'):
                    continue

            is_custom = name.startswith('./') or name.startswith('../')
            plugin = ExpoConfigPluginInfo(
                name=name,
                is_custom=is_custom,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            result['config_plugins'].append(plugin)

    def _extract_custom_plugins(self, content: str, file_path: str,
                                result: Dict[str, Any]) -> None:
        """Extract custom config plugin definitions."""
        # Check if this file imports config-plugins
        if not self.CONFIG_PLUGIN_IMPORT.search(content):
            return

        result['has_custom_plugins'] = True

        plugin_patterns = [
            (self.WITH_ANDROID_MANIFEST, 'withAndroidManifest', True, False),
            (self.WITH_INFO_PLIST, 'withInfoPlist', False, True),
            (self.WITH_APP_DELEGATE, 'withAppDelegate', False, True),
            (self.WITH_DANGEROUS_MOD, 'withDangerousMod', True, True),
            (self.WITH_PLUGINS, 'withPlugins', True, True),
            (self.WITH_GRADLE_PROPERTIES, 'withGradleProperties', True, False),
            (self.WITH_ANDROID_COLORS, 'withAndroidColors/Styles', True, False),
            (self.WITH_ENTITLEMENTS, 'withEntitlementsPlist', False, True),
        ]

        for pattern, name, android, ios in plugin_patterns:
            for pm in pattern.finditer(content):
                line_num = content[:pm.start()].count('\n') + 1
                result['config_plugins'].append(ExpoConfigPluginInfo(
                    name=name,
                    is_custom=True,
                    is_inline=True,
                    modifies_android=android,
                    modifies_ios=ios,
                    file=file_path,
                    line_number=line_num,
                ))

    def _extract_modules_api(self, content: str, file_path: str,
                             result: Dict[str, Any]) -> None:
        """Extract Expo Modules API definitions (native modules)."""
        # Detect language from file extension
        lang = ""
        if file_path.endswith('.swift'):
            lang = 'swift'
        elif file_path.endswith(('.kt', '.java')):
            lang = 'kotlin'
        elif file_path.endswith(('.cpp', '.h', '.mm')):
            lang = 'cpp'
        elif file_path.endswith(('.ts', '.js')):
            lang = 'typescript'

        for m in self.EXPO_MODULE_DEF.finditer(content):
            module_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Extract methods
            methods: List[str] = []
            for fm in self.EXPO_MODULE_FUNCTION.finditer(content):
                methods.append(fm.group(1))

            # Extract properties
            properties: List[str] = []
            for pm in self.EXPO_MODULE_PROPERTY.finditer(content):
                properties.append(pm.group(1))

            module_info = ExpoModulesAPIInfo(
                module_name=module_name,
                language=lang,
                has_view=bool(self.EXPO_MODULE_VIEW.search(content)),
                has_events=bool(self.EXPO_MODULE_EVENT.search(content)),
                has_async_function='AsyncFunction' in content,
                exported_methods=methods[:30],
                exported_properties=properties[:20],
                file=file_path,
                line_number=line_num,
            )
            result['modules_api'].append(module_info)
