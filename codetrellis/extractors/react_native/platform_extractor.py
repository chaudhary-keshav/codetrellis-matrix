"""
React Native Platform Extractor for CodeTrellis

Extracts platform-specific patterns from React Native source code:
- Platform.OS / Platform.select / Platform.Version usage
- Platform-specific file extensions (.ios.js, .android.js, .native.js, .web.js)
- Dimensions and responsive layout patterns
- Permission patterns (PermissionsAndroid, expo-permissions)
- App lifecycle (AppState, BackHandler, Linking)
- Device info (react-native-device-info, expo-device)
- StatusBar, SafeAreaView, KeyboardAvoidingView platform handling

Supports React Native 0.59+ cross-platform patterns.

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RNPlatformUsageInfo:
    """Information about platform-specific code usage."""
    name: str
    file: str = ""
    line_number: int = 0
    usage_type: str = ""  # os_check, select, version_check, conditional_import
    platforms: List[str] = field(default_factory=list)  # ios, android, web, windows, macos


@dataclass
class RNPlatformFileInfo:
    """Information about platform-specific file extensions."""
    name: str
    file: str = ""
    line_number: int = 0
    platform: str = ""  # ios, android, native, web
    base_name: str = ""  # File name without platform extension


@dataclass
class RNPermissionInfo:
    """Information about permission requests."""
    name: str
    file: str = ""
    line_number: int = 0
    permission_type: str = ""  # camera, location, notifications, storage, etc.
    library: str = ""  # PermissionsAndroid, expo-permissions, react-native-permissions
    is_request: bool = False  # True if requesting, False if just checking


class ReactNativePlatformExtractor:
    """
    Extracts platform-awareness and device-related patterns from source code.

    Detects:
    - Platform.OS / Platform.select / Platform.Version usage
    - Platform-specific file suffixes (.ios./.android./.native./.web.)
    - PermissionsAndroid and third-party permission libs
    - AppState lifecycle listeners
    - BackHandler (Android back button)
    - Linking (deep links, URL handling)
    - StatusBar / SafeAreaView platform handling
    - Keyboard / KeyboardAvoidingView patterns
    """

    # Platform.OS checks
    PLATFORM_OS = re.compile(
        r"Platform\.OS\s*(?:===?|!==?)\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # Platform.select
    PLATFORM_SELECT = re.compile(
        r"Platform\.select\s*\(\s*\{([^}]*)\}",
        re.DOTALL
    )

    # Platform.Version
    PLATFORM_VERSION = re.compile(
        r"Platform\.Version\s*(?:[><=!]+)\s*(\d+)",
        re.MULTILINE
    )

    # Platform-specific file extension detection
    PLATFORM_FILE_EXT = re.compile(
        r"\.(ios|android|native|web|windows|macos)\.\w+$"
    )

    # PermissionsAndroid
    PERMISSIONS_ANDROID = re.compile(
        r"PermissionsAndroid\.(?:request|check|requestMultiple)\s*\(\s*"
        r"(?:PermissionsAndroid\.PERMISSIONS\.)?(\w+)",
        re.MULTILINE
    )

    # expo-permissions / expo-* permission modules
    EXPO_PERMISSIONS = re.compile(
        r"from\s+['\"]expo-(camera|location|notifications|media-library|"
        r"contacts|calendar|sensors|audio|image-picker|file-system|"
        r"local-authentication|haptics|brightness|battery)['\"]",
        re.MULTILINE
    )

    # react-native-permissions
    RN_PERMISSIONS = re.compile(
        r"from\s+['\"]react-native-permissions['\"]|"
        r"PERMISSIONS\.(?:IOS|ANDROID)\.(\w+)|"
        r"(?:check|request|requestMultiple|checkMultiple)\s*\(",
        re.MULTILINE
    )

    # AppState
    APP_STATE = re.compile(
        r"AppState\.addEventListener\s*\(\s*['\"]change['\"]|"
        r"AppState\.currentState|"
        r"useAppState",
        re.MULTILINE
    )

    # BackHandler (Android)
    BACK_HANDLER = re.compile(
        r"BackHandler\.addEventListener\s*\(\s*['\"]hardwareBackPress['\"]|"
        r"useBackHandler",
        re.MULTILINE
    )

    # Linking (URL handling)
    LINKING_API = re.compile(
        r"Linking\.(?:openURL|getInitialURL|addEventListener|canOpenURL|openSettings)\s*\(",
        re.MULTILINE
    )

    # Keyboard handling
    KEYBOARD_API = re.compile(
        r"Keyboard\.(?:addListener|dismiss|removeAllListeners)\s*\(|"
        r"KeyboardAvoidingView|"
        r"useKeyboard",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract platform-specific information from source code.

        Returns:
            Dict with keys: platform_usages, platform_files, permissions
        """
        platform_usages = []
        platform_files = []
        permissions = []

        # Platform.OS checks
        for match in self.PLATFORM_OS.finditer(content):
            platform = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            platform_usages.append(RNPlatformUsageInfo(
                name=f"Platform.OS=={platform}",
                file=file_path,
                line_number=line_num,
                usage_type="os_check",
                platforms=[platform],
            ))

        # Platform.select
        for match in self.PLATFORM_SELECT.finditer(content):
            platforms_block = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            platforms = re.findall(r"(ios|android|web|windows|macos|native|default)\s*:", platforms_block)
            platform_usages.append(RNPlatformUsageInfo(
                name="Platform.select",
                file=file_path,
                line_number=line_num,
                usage_type="select",
                platforms=platforms,
            ))

        # Platform.Version
        for match in self.PLATFORM_VERSION.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            platform_usages.append(RNPlatformUsageInfo(
                name=f"Platform.Version>={match.group(1)}",
                file=file_path,
                line_number=line_num,
                usage_type="version_check",
            ))

        # Platform-specific file detection
        ext_match = self.PLATFORM_FILE_EXT.search(file_path)
        if ext_match:
            platform = ext_match.group(1)
            base = re.sub(r'\.(ios|android|native|web|windows|macos)\.', '.', file_path)
            platform_files.append(RNPlatformFileInfo(
                name=file_path.split('/')[-1],
                file=file_path,
                platform=platform,
                base_name=base.split('/')[-1],
            ))

        # AppState listener
        if self.APP_STATE.search(content):
            m = self.APP_STATE.search(content)
            platform_usages.append(RNPlatformUsageInfo(
                name="AppState",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                usage_type="lifecycle",
            ))

        # BackHandler (Android)
        if self.BACK_HANDLER.search(content):
            m = self.BACK_HANDLER.search(content)
            platform_usages.append(RNPlatformUsageInfo(
                name="BackHandler",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                usage_type="os_check",
                platforms=["android"],
            ))

        # Linking API
        if self.LINKING_API.search(content):
            m = self.LINKING_API.search(content)
            platform_usages.append(RNPlatformUsageInfo(
                name="Linking",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                usage_type="deep_link",
            ))

        # Keyboard handling
        if self.KEYBOARD_API.search(content):
            m = self.KEYBOARD_API.search(content)
            platform_usages.append(RNPlatformUsageInfo(
                name="Keyboard",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                usage_type="keyboard",
            ))

        # PermissionsAndroid
        for match in self.PERMISSIONS_ANDROID.finditer(content):
            perm_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            permissions.append(RNPermissionInfo(
                name=perm_name,
                file=file_path,
                line_number=line_num,
                permission_type=perm_name.lower(),
                library="PermissionsAndroid",
                is_request='request' in content[max(0, match.start()-20):match.start()].lower(),
            ))

        # expo module permissions
        for match in self.EXPO_PERMISSIONS.finditer(content):
            module_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            has_request = bool(re.search(
                rf'requestPermissions|requestForeground|requestBackground|requestMediaLibrary',
                content
            ))
            permissions.append(RNPermissionInfo(
                name=module_name,
                file=file_path,
                line_number=line_num,
                permission_type=module_name,
                library=f"expo-{module_name}",
                is_request=has_request,
            ))

        # react-native-permissions
        for match in self.RN_PERMISSIONS.finditer(content):
            if match.group(1):
                perm_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                permissions.append(RNPermissionInfo(
                    name=perm_name,
                    file=file_path,
                    line_number=line_num,
                    permission_type=perm_name.lower(),
                    library="react-native-permissions",
                ))

        return {
            'platform_usages': platform_usages,
            'platform_files': platform_files,
            'permissions': permissions,
        }
