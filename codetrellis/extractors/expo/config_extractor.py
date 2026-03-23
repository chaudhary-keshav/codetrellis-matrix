"""
Expo Config Extractor for CodeTrellis

Extracts Expo configuration from source files:
- app.json / app.config.js / app.config.ts configuration
- EAS Build configuration (eas.json)
- Expo SDK version detection
- Managed vs bare workflow identification
- Config plugin declarations
- Splash screen, icon, and asset configuration

Supports Expo SDK 44-52+ (all modern versions).

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ExpoConfigInfo:
    """Information about Expo app configuration."""
    name: str = ""
    slug: str = ""
    sdk_version: str = ""
    version: str = ""
    platforms: List[str] = field(default_factory=list)
    scheme: str = ""  # Deep linking scheme
    plugins: List[str] = field(default_factory=list)
    has_splash: bool = False
    has_icon: bool = False
    has_adaptive_icon: bool = False
    orientation: str = ""
    user_interface_style: str = ""  # light, dark, automatic
    updates_url: str = ""
    runtime_version: str = ""
    config_type: str = ""  # app.json, app.config.js, app.config.ts
    workflow: str = ""  # managed, bare
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoEASConfigInfo:
    """Information about EAS Build configuration."""
    build_profiles: List[str] = field(default_factory=list)
    submit_profiles: List[str] = field(default_factory=list)
    update_channels: List[str] = field(default_factory=list)
    has_eas_update: bool = False
    has_eas_submit: bool = False
    cli_version: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ExpoPluginConfigInfo:
    """Information about an Expo config plugin declaration."""
    name: str = ""
    options: Dict[str, Any] = field(default_factory=dict)
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


class ExpoConfigExtractor:
    """
    Extracts Expo configuration information from config files and source code.

    Detects:
    - app.json expo configuration (name, slug, SDK version, platforms)
    - app.config.js/ts dynamic configuration
    - eas.json build/submit/update profiles
    - Config plugin declarations
    - Managed vs bare workflow detection
    - Asset configuration (splash, icons)
    """

    # Patterns for detecting Expo config in JS/TS files
    EXPO_CONFIG_EXPORT = re.compile(
        r"(?:export\s+default|module\.exports\s*=)\s*"
        r"(?:\{|(?:defineConfig|withExpo)\s*\()",
        re.MULTILINE
    )

    SDK_VERSION_PATTERN = re.compile(
        r"['\"]sdkVersion['\"]\s*:\s*['\"](\d+\.\d+\.\d+)['\"]",
        re.MULTILINE
    )

    EXPO_PACKAGE_VERSION = re.compile(
        r"['\"]expo['\"]\s*:\s*['\"](?:~|\^)?(\d+)\.",
        re.MULTILINE
    )

    PLUGIN_PATTERN = re.compile(
        r"['\"]plugins['\"]\s*:\s*\[([^\]]*)\]",
        re.DOTALL
    )

    PLUGIN_ENTRY = re.compile(
        r"""['\"]([a-zA-Z@][\w/.-]+)['\"]""",
    )

    EAS_BUILD_PROFILE = re.compile(
        r"['\"](\w+)['\"]\s*:\s*\{[^}]*['\"]distribution['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Expo configuration from content."""
        result: Dict[str, Any] = {
            'configs': [],
            'eas_configs': [],
            'plugin_configs': [],
        }

        if file_path.endswith('app.json'):
            self._extract_app_json(content, file_path, result)
        elif re.search(r'app\.config\.(js|ts|mjs)$', file_path):
            self._extract_app_config_js(content, file_path, result)
        elif file_path.endswith('eas.json'):
            self._extract_eas_json(content, file_path, result)
        else:
            # Check for inline expo config patterns in regular source files
            self._extract_inline_config(content, file_path, result)

        return result

    def _extract_app_json(self, content: str, file_path: str,
                          result: Dict[str, Any]) -> None:
        """Extract configuration from app.json."""
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return

        expo = data.get('expo', data)  # Sometimes expo key wraps everything
        if not isinstance(expo, dict):
            return

        config = ExpoConfigInfo(
            name=expo.get('name', ''),
            slug=expo.get('slug', ''),
            sdk_version=expo.get('sdkVersion', ''),
            version=expo.get('version', ''),
            platforms=expo.get('platforms', ['ios', 'android']),
            scheme=expo.get('scheme', ''),
            has_splash='splash' in expo,
            has_icon='icon' in expo,
            has_adaptive_icon='android' in expo and 'adaptiveIcon' in expo.get('android', {}),
            orientation=expo.get('orientation', ''),
            user_interface_style=expo.get('userInterfaceStyle', ''),
            config_type='app.json',
            workflow='managed',
            file=file_path,
            line_number=1,
        )

        # Extract updates config
        updates = expo.get('updates', {})
        if isinstance(updates, dict):
            config.updates_url = updates.get('url', '')

        # Extract runtime version
        rv = expo.get('runtimeVersion', '')
        if isinstance(rv, dict):
            config.runtime_version = rv.get('policy', '')
        elif isinstance(rv, str):
            config.runtime_version = rv

        # Extract plugins
        plugins = expo.get('plugins', [])
        if isinstance(plugins, list):
            for plugin in plugins:
                if isinstance(plugin, str):
                    config.plugins.append(plugin)
                    result['plugin_configs'].append(ExpoPluginConfigInfo(
                        name=plugin, file=file_path, line_number=1
                    ))
                elif isinstance(plugin, list) and len(plugin) >= 1:
                    name = plugin[0] if isinstance(plugin[0], str) else ''
                    opts = plugin[1] if len(plugin) > 1 and isinstance(plugin[1], dict) else {}
                    config.plugins.append(name)
                    result['plugin_configs'].append(ExpoPluginConfigInfo(
                        name=name, options=opts, file=file_path, line_number=1
                    ))

        result['configs'].append(config)

    def _extract_app_config_js(self, content: str, file_path: str,
                               result: Dict[str, Any]) -> None:
        """Extract configuration from app.config.js/ts."""
        config = ExpoConfigInfo(
            config_type='app.config.js' if file_path.endswith('.js') else 'app.config.ts',
            file=file_path,
            line_number=1,
        )

        # Detect name
        name_m = re.search(r"name\s*:\s*['\"]([^'\"]+)['\"]", content)
        if name_m:
            config.name = name_m.group(1)

        # Detect slug
        slug_m = re.search(r"slug\s*:\s*['\"]([^'\"]+)['\"]", content)
        if slug_m:
            config.slug = slug_m.group(1)

        # Detect SDK version
        sdk_m = self.SDK_VERSION_PATTERN.search(content)
        if sdk_m:
            config.sdk_version = sdk_m.group(1)

        # Detect scheme
        scheme_m = re.search(r"scheme\s*:\s*['\"]([^'\"]+)['\"]", content)
        if scheme_m:
            config.scheme = scheme_m.group(1)

        # Detect platforms
        platforms_m = re.search(r"platforms\s*:\s*\[([^\]]*)\]", content)
        if platforms_m:
            config.platforms = re.findall(r"['\"](\w+)['\"]", platforms_m.group(1))

        # Detect splash/icon
        config.has_splash = 'splash' in content
        config.has_icon = bool(re.search(r"\bicon\s*:", content))

        # Detect plugins
        plugins_m = self.PLUGIN_PATTERN.search(content)
        if plugins_m:
            for pm in self.PLUGIN_ENTRY.finditer(plugins_m.group(1)):
                name = pm.group(1)
                config.plugins.append(name)
                result['plugin_configs'].append(ExpoPluginConfigInfo(
                    name=name, file=file_path, line_number=1
                ))

        # Detect runtime version
        rv_m = re.search(r"runtimeVersion\s*:\s*['\"]([^'\"]+)['\"]", content)
        if rv_m:
            config.runtime_version = rv_m.group(1)

        # Detect workflow from native dirs reference
        if re.search(r"ios/|android/|expo\s*eject|bare\s*workflow", content):
            config.workflow = 'bare'
        else:
            config.workflow = 'managed'

        result['configs'].append(config)

    def _extract_eas_json(self, content: str, file_path: str,
                          result: Dict[str, Any]) -> None:
        """Extract EAS configuration from eas.json."""
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return

        if not isinstance(data, dict):
            return

        eas = ExpoEASConfigInfo(file=file_path, line_number=1)

        # Build profiles
        build = data.get('build', {})
        if isinstance(build, dict):
            eas.build_profiles = list(build.keys())

        # Submit profiles
        submit = data.get('submit', {})
        if isinstance(submit, dict):
            eas.submit_profiles = list(submit.keys())
            eas.has_eas_submit = len(eas.submit_profiles) > 0

        # CLI version
        cli = data.get('cli', {})
        if isinstance(cli, dict):
            eas.cli_version = cli.get('version', '')

        # Check for EAS Update channels
        for profile_name, profile_data in build.items():
            if isinstance(profile_data, dict) and 'channel' in profile_data:
                eas.update_channels.append(profile_data['channel'])
                eas.has_eas_update = True

        result['eas_configs'].append(eas)

    def _extract_inline_config(self, content: str, file_path: str,
                               result: Dict[str, Any]) -> None:
        """Extract Expo config patterns from regular source files."""
        # Detect Constants.expoConfig usage
        if re.search(r"Constants\.expoConfig|Constants\.manifest", content):
            config = ExpoConfigInfo(
                config_type='inline',
                file=file_path,
                line_number=1,
            )
            result['configs'].append(config)
