"""
Expo API Extractor for CodeTrellis

Extracts high-level Expo ecosystem integration patterns:
- Expo SDK version detection
- Import analysis and dependency mapping
- EAS (Expo Application Services) usage
- Dev client detection
- Managed vs bare workflow indicators
- Cross-module integration patterns

Supports Expo SDK 44-52+.

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExpoImportInfo:
    """Information about Expo-related imports in a file."""
    file_path: str = ""
    expo_imports: List[str] = field(default_factory=list)
    third_party_rn_imports: List[str] = field(default_factory=list)
    has_expo_core: bool = False
    has_expo_router: bool = False
    has_expo_dev_client: bool = False
    import_count: int = 0


@dataclass
class ExpoIntegrationInfo:
    """Information about cross-module Expo patterns."""
    pattern_name: str = ""  # e.g., 'deep-linking', 'push-notifications', 'social-auth'
    modules_involved: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoEASInfo:
    """Information about Expo Application Services usage."""
    has_eas_build: bool = False
    has_eas_update: bool = False
    has_eas_submit: bool = False
    has_eas_metadata: bool = False
    build_profiles: List[str] = field(default_factory=list)
    update_channels: List[str] = field(default_factory=list)
    runtime_version_policy: str = ""  # appVersion, nativeVersion, fingerprint, custom


# SDK version mapping: feature -> minimum SDK version
SDK_FEATURES = {
    'expo-router': 49,
    'expo-router-v3': 50,
    'expo-dev-client': 44,
    'eas-update': 46,
    'new-architecture': 51,
    'react-19': 52,
    'expo-image': 49,
    'expo-sqlite-next': 51,
    'expo-camera-next': 51,
    'expo-video': 51,
}


class ExpoApiExtractor:
    """
    Extracts high-level Expo ecosystem integration patterns.

    Detects:
    - SDK version from package.json/app.json
    - All expo-* imports across a file
    - EAS Build/Update/Submit configuration
    - Dev client vs Expo Go usage
    - Managed/bare workflow detection
    - Cross-module integration patterns (deep linking, push + navigation, etc.)
    """

    EXPO_IMPORT = re.compile(
        r"(?:import\s+(?:\*\s+as\s+\w+|\{[^}]*\}|\w+(?:\s*,\s*\{[^}]*\})?)\s+from\s+['\"]"
        r"(expo(?:[\w/-]*))['\"]|"
        r"require\(['\"]"
        r"(expo(?:[\w/-]*))['\"]"
        r"\))",
        re.MULTILINE
    )

    RN_THIRD_PARTY_IMPORT = re.compile(
        r"from\s+['\"](@?react-native[\w/-]*)['\"]|"
        r"require\(['\"](@?react-native[\w/-]*)['\"]",
        re.MULTILINE
    )

    SDK_VERSION_JSON = re.compile(
        r'"sdkVersion"\s*:\s*"(\d+\.\d+\.\d+)"',
    )

    EXPO_PKG_VERSION = re.compile(
        r'"expo"\s*:\s*["\'](?:~|\^)?(\d+)',
    )

    RUNTIME_VERSION = re.compile(
        r'"runtimeVersion"\s*:\s*(?:"([^"]+)"|\{[^}]*"policy"\s*:\s*"([^"]+)")',
        re.MULTILINE | re.DOTALL
    )

    DEV_CLIENT_PATTERN = re.compile(
        r"expo-dev-client|expo-dev-launcher|expo-dev-menu",
        re.MULTILINE
    )

    MANAGED_WORKFLOW_INDICATORS = re.compile(
        r"expo\s+start|npx\s+expo\s+start|"
        r'"start"\s*:\s*"expo\s+start"|'
        r"expo-updates|Constants\.expoConfig",
        re.MULTILINE
    )

    BARE_WORKFLOW_INDICATORS = re.compile(
        r"react-native\s+run-android|react-native\s+run-ios|"
        r"android/app/build\.gradle|ios/Podfile|"
        r"\"react-native\"\s*:\s*\"",
        re.MULTILINE
    )

    # Integration patterns: common combinations of expo modules
    DEEP_LINKING_PATTERN = re.compile(
        r"expo-linking|Linking\.createURL|useURL\s*\(",
        re.MULTILINE
    )

    PUSH_NOTIFICATION_PATTERN = re.compile(
        r"expo-notifications.*(?:expo-device|expo-constants)|"
        r"getExpoPushTokenAsync|schedulePushNotificationAsync",
        re.MULTILINE | re.DOTALL
    )

    SOCIAL_AUTH_PATTERN = re.compile(
        r"expo-auth-session.*(?:expo-web-browser|expo-crypto)|"
        r"useAuthRequest|AuthSession\.makeRedirectUri",
        re.MULTILINE | re.DOTALL
    )

    IMAGE_PIPELINE_PATTERN = re.compile(
        r"expo-image-picker.*expo-image-manipulator|"
        r"expo-image-manipulator.*expo-file-system",
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Expo ecosystem integration patterns from source code."""
        result: Dict[str, Any] = {
            'imports': None,
            'integrations': [],
            'eas': None,
            'sdk_version': 0,
            'workflow': '',
        }

        self._extract_imports(content, file_path, result)
        self._extract_sdk_version(content, result)
        self._extract_eas(content, file_path, result)
        self._extract_workflow(content, result)
        self._extract_integrations(content, file_path, result)

        return result

    def _extract_imports(self, content: str, file_path: str,
                         result: Dict[str, Any]) -> None:
        """Extract all Expo-related imports from a file."""
        expo_imports: List[str] = []
        rn_imports: List[str] = []

        for m in self.EXPO_IMPORT.finditer(content):
            module = m.group(1) or m.group(2)
            if module and module not in expo_imports:
                expo_imports.append(module)

        for m in self.RN_THIRD_PARTY_IMPORT.finditer(content):
            module = m.group(1) or m.group(2)
            if module and module not in rn_imports:
                rn_imports.append(module)

        if expo_imports or rn_imports:
            result['imports'] = ExpoImportInfo(
                file_path=file_path,
                expo_imports=expo_imports[:50],
                third_party_rn_imports=rn_imports[:30],
                has_expo_core='expo' in expo_imports or any(
                    i.startswith('expo/') for i in expo_imports
                ),
                has_expo_router='expo-router' in expo_imports,
                has_expo_dev_client='expo-dev-client' in expo_imports,
                import_count=len(expo_imports) + len(rn_imports),
            )

    def _extract_sdk_version(self, content: str,
                             result: Dict[str, Any]) -> None:
        """Extract Expo SDK version from config or package files."""
        m = self.SDK_VERSION_JSON.search(content)
        if m:
            try:
                result['sdk_version'] = int(m.group(1).split('.')[0])
                return
            except (ValueError, IndexError):
                pass

        m = self.EXPO_PKG_VERSION.search(content)
        if m:
            try:
                result['sdk_version'] = int(m.group(1))
            except ValueError:
                pass

    def _extract_eas(self, content: str, file_path: str,
                     result: Dict[str, Any]) -> None:
        """Extract EAS configuration."""
        is_eas_file = file_path.endswith('eas.json')
        has_eas_refs = 'eas-cli' in content or 'eas build' in content or is_eas_file

        if not has_eas_refs and '"build"' not in content:
            return

        eas = ExpoEASInfo()

        if is_eas_file or '"build"' in content:
            eas.has_eas_build = True
            # Extract build profiles
            for m in re.finditer(r'"build"\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
                                 content, re.DOTALL):
                for pm in re.finditer(r'"(\w+)"\s*:', m.group(1)):
                    profile = pm.group(1)
                    if profile not in ('extends', 'env', 'cache'):
                        eas.build_profiles.append(profile)

        if '"submit"' in content:
            eas.has_eas_submit = True

        if '"channel"' in content or 'eas update' in content:
            eas.has_eas_update = True
            for m in re.finditer(r'"channel"\s*:\s*"([^"]+)"', content):
                if m.group(1) not in eas.update_channels:
                    eas.update_channels.append(m.group(1))

        if '"store"' in content and is_eas_file:
            eas.has_eas_metadata = True

        # Runtime version policy
        m = self.RUNTIME_VERSION.search(content)
        if m:
            eas.runtime_version_policy = m.group(2) or 'fixed'

        # Cap lists
        eas.build_profiles = eas.build_profiles[:10]
        eas.update_channels = eas.update_channels[:10]

        result['eas'] = eas

    def _extract_workflow(self, content: str,
                          result: Dict[str, Any]) -> None:
        """Detect managed vs bare workflow."""
        managed_score = len(self.MANAGED_WORKFLOW_INDICATORS.findall(content))
        bare_score = len(self.BARE_WORKFLOW_INDICATORS.findall(content))

        if managed_score > bare_score:
            result['workflow'] = 'managed'
        elif bare_score > managed_score:
            result['workflow'] = 'bare'
        elif managed_score > 0:
            result['workflow'] = 'managed'

    def _extract_integrations(self, content: str, file_path: str,
                              result: Dict[str, Any]) -> None:
        """Detect known cross-module integration patterns."""
        patterns = [
            ('deep-linking', self.DEEP_LINKING_PATTERN, ['expo-linking', 'expo-router']),
            ('push-notifications', self.PUSH_NOTIFICATION_PATTERN,
             ['expo-notifications', 'expo-device', 'expo-constants']),
            ('social-auth', self.SOCIAL_AUTH_PATTERN,
             ['expo-auth-session', 'expo-web-browser', 'expo-crypto']),
            ('image-pipeline', self.IMAGE_PIPELINE_PATTERN,
             ['expo-image-picker', 'expo-image-manipulator', 'expo-file-system']),
        ]

        for name, pattern, modules in patterns:
            m = pattern.search(content)
            if m:
                line_num = content[:m.start()].count('\n') + 1
                result['integrations'].append(ExpoIntegrationInfo(
                    pattern_name=name,
                    modules_involved=modules,
                    file=file_path,
                    line_number=line_num,
                ))
