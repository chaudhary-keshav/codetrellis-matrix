"""
Tailwind CSS Plugin Extractor v1.0

Extracts Tailwind plugin patterns: official plugins, community plugins,
custom utility/variant definitions, and plugin API usage.

Supports:
- Official plugins (@tailwindcss/typography, forms, aspect-ratio, container-queries)
- Community plugins (daisyUI, tailwindcss-animate, etc.)
- Custom plugin API (plugin(), plugin.withOptions())
- Custom utility definitions (addUtilities, matchUtilities)
- Custom variant definitions (addVariant, matchVariant)
- Custom component definitions (addComponents)
- Custom base style definitions (addBase)
- v4: @plugin directive

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TailwindPluginInfo:
    """Information about a Tailwind plugin."""
    name: str = ""
    type: str = ""  # official, community, custom, v4-directive
    package: str = ""
    is_official: bool = False
    has_options: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindCustomUtilityInfo:
    """Information about a custom utility definition."""
    name: str = ""
    method: str = ""  # addUtilities, matchUtilities, addComponents, addBase
    properties: List[str] = field(default_factory=list)
    is_responsive: bool = False
    is_variant_aware: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindCustomVariantInfo:
    """Information about a custom variant definition."""
    name: str = ""
    method: str = ""  # addVariant, matchVariant
    selector: str = ""
    is_dynamic: bool = False
    file: str = ""
    line_number: int = 0


class TailwindPluginExtractor:
    """
    Extracts Tailwind plugin information from JS/TS and CSS files.

    Detects:
    - plugin() function calls
    - plugin.withOptions() calls
    - addUtilities() / matchUtilities()
    - addComponents()
    - addBase()
    - addVariant() / matchVariant()
    - theme() / e() / config() helper usage in plugins
    - Official plugin imports/requires
    - v4 @plugin CSS directive

    Official Plugins:
    - @tailwindcss/typography: Prose classes for rich text
    - @tailwindcss/forms: Form element resets
    - @tailwindcss/aspect-ratio: Aspect ratio utilities
    - @tailwindcss/container-queries: Container query utilities
    - @tailwindcss/line-clamp: Line clamping (deprecated v3.3+)
    """

    OFFICIAL_PLUGINS = {
        '@tailwindcss/typography': 'typography',
        '@tailwindcss/forms': 'forms',
        '@tailwindcss/aspect-ratio': 'aspect-ratio',
        '@tailwindcss/container-queries': 'container-queries',
        '@tailwindcss/line-clamp': 'line-clamp',
        '@tailwindcss/nesting': 'nesting',
        '@tailwindcss/oxide': 'oxide',
    }

    COMMUNITY_PLUGINS = {
        'daisyui': 'daisyUI',
        'tailwindcss-animate': 'animate',
        '@headlessui/tailwindcss': 'headless-ui',
        'tailwind-merge': 'merge',
        'tailwind-variants': 'variants',
        'class-variance-authority': 'cva',
        'clsx': 'clsx',
        'flowbite': 'flowbite',
        'preline': 'preline',
        '@nextui-org/theme': 'nextui',
        'tw-elements': 'tw-elements',
        'tailwindcss-radix': 'radix',
        'tailwindcss-debug-screens': 'debug-screens',
        'tailwindcss-3d': '3d',
    }

    # Plugin function patterns
    PLUGIN_CALL_PATTERN = re.compile(
        r'plugin\s*\(\s*function\s*\(\s*\{?\s*'
        r'(addUtilities|matchUtilities|addComponents|addBase|addVariant|matchVariant|theme|e|config)',
        re.MULTILINE
    )

    PLUGIN_ARROW_PATTERN = re.compile(
        r'plugin\s*\(\s*\(\s*\{?\s*'
        r'(addUtilities|matchUtilities|addComponents|addBase|addVariant|matchVariant|theme|e|config)',
        re.MULTILINE
    )

    PLUGIN_WITH_OPTIONS_PATTERN = re.compile(
        r'plugin\.withOptions\s*\(',
        re.MULTILINE
    )

    # API method patterns
    ADD_UTILITIES_PATTERN = re.compile(
        r'addUtilities\s*\(\s*(?:\{|["\'])',
        re.MULTILINE
    )

    MATCH_UTILITIES_PATTERN = re.compile(
        r'matchUtilities\s*\(\s*\{',
        re.MULTILINE
    )

    ADD_COMPONENTS_PATTERN = re.compile(
        r'addComponents\s*\(\s*(?:\{|["\'])',
        re.MULTILINE
    )

    ADD_BASE_PATTERN = re.compile(
        r'addBase\s*\(\s*(?:\{|["\'])',
        re.MULTILINE
    )

    ADD_VARIANT_PATTERN = re.compile(
        r'addVariant\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    MATCH_VARIANT_PATTERN = re.compile(
        r'matchVariant\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # v4 @plugin directive
    V4_PLUGIN_PATTERN = re.compile(
        r'@plugin\s+["\']([^"\']+)["\']\s*;',
        re.MULTILINE
    )

    # Import/require pattern for plugin detection
    IMPORT_REQUIRE_PATTERN = re.compile(
        r'(?:require\(\s*|import\s+\w+\s+from\s+)["\']([^"\']+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Tailwind plugin patterns from content.

        Args:
            content: JS/TS/CSS source code string.
            file_path: Path to the source file.

        Returns:
            Dict with extracted plugin info.
        """
        result: Dict[str, Any] = {
            'plugins': [],
            'custom_utilities': [],
            'custom_variants': [],
            'stats': {},
        }

        if not content or not content.strip():
            return result

        # Detect imported plugins
        result['plugins'] = self._extract_plugins(content, file_path)

        # Extract custom utility definitions
        result['custom_utilities'] = self._extract_custom_utilities(content, file_path)

        # Extract custom variant definitions
        result['custom_variants'] = self._extract_custom_variants(content, file_path)

        # v4 @plugin directives
        v4_plugins = self._extract_v4_plugins(content, file_path)
        result['plugins'].extend(v4_plugins)

        # Stats
        result['stats'] = {
            'total_plugins': len(result['plugins']),
            'official_plugins': sum(1 for p in result['plugins'] if p.is_official),
            'community_plugins': sum(1 for p in result['plugins'] if p.type == 'community'),
            'custom_plugins': sum(1 for p in result['plugins'] if p.type == 'custom'),
            'custom_utilities': len(result['custom_utilities']),
            'custom_variants': len(result['custom_variants']),
            'has_plugin_api': bool(self.PLUGIN_CALL_PATTERN.search(content) or
                                   self.PLUGIN_ARROW_PATTERN.search(content) or
                                   self.PLUGIN_WITH_OPTIONS_PATTERN.search(content)),
        }

        return result

    def _extract_plugins(self, content: str, file_path: str) -> List[TailwindPluginInfo]:
        """Extract plugin references from imports/requires."""
        results: List[TailwindPluginInfo] = []
        seen: set = set()

        for m in self.IMPORT_REQUIRE_PATTERN.finditer(content):
            pkg = m.group(1)
            if pkg in seen:
                continue

            plugin_info = None

            # Check official
            if pkg in self.OFFICIAL_PLUGINS:
                seen.add(pkg)
                line_num = content[:m.start()].count('\n') + 1
                plugin_info = TailwindPluginInfo(
                    name=self.OFFICIAL_PLUGINS[pkg],
                    type='official',
                    package=pkg,
                    is_official=True,
                    file=file_path,
                    line_number=line_num,
                )

            # Check community
            elif pkg in self.COMMUNITY_PLUGINS:
                seen.add(pkg)
                line_num = content[:m.start()].count('\n') + 1
                plugin_info = TailwindPluginInfo(
                    name=self.COMMUNITY_PLUGINS[pkg],
                    type='community',
                    package=pkg,
                    is_official=False,
                    file=file_path,
                    line_number=line_num,
                )

            if plugin_info:
                results.append(plugin_info)

        # Detect custom plugin definitions
        if self.PLUGIN_CALL_PATTERN.search(content) or self.PLUGIN_ARROW_PATTERN.search(content):
            results.append(TailwindPluginInfo(
                name='custom',
                type='custom',
                has_options=bool(self.PLUGIN_WITH_OPTIONS_PATTERN.search(content)),
                file=file_path,
                line_number=1,
            ))

        return results

    def _extract_custom_utilities(self, content: str, file_path: str) -> List[TailwindCustomUtilityInfo]:
        """Extract custom utility definitions from plugin code."""
        results: List[TailwindCustomUtilityInfo] = []

        # addUtilities
        for m in self.ADD_UTILITIES_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomUtilityInfo(
                name='addUtilities',
                method='addUtilities',
                file=file_path,
                line_number=line_num,
            ))

        # matchUtilities
        for m in self.MATCH_UTILITIES_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomUtilityInfo(
                name='matchUtilities',
                method='matchUtilities',
                is_variant_aware=True,
                file=file_path,
                line_number=line_num,
            ))

        # addComponents
        for m in self.ADD_COMPONENTS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomUtilityInfo(
                name='addComponents',
                method='addComponents',
                file=file_path,
                line_number=line_num,
            ))

        # addBase
        for m in self.ADD_BASE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomUtilityInfo(
                name='addBase',
                method='addBase',
                file=file_path,
                line_number=line_num,
            ))

        return results

    def _extract_custom_variants(self, content: str, file_path: str) -> List[TailwindCustomVariantInfo]:
        """Extract custom variant definitions from plugin code."""
        results: List[TailwindCustomVariantInfo] = []

        # addVariant
        for m in self.ADD_VARIANT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomVariantInfo(
                name=m.group(1),
                method='addVariant',
                is_dynamic=False,
                file=file_path,
                line_number=line_num,
            ))

        # matchVariant
        for m in self.MATCH_VARIANT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append(TailwindCustomVariantInfo(
                name=m.group(1),
                method='matchVariant',
                is_dynamic=True,
                file=file_path,
                line_number=line_num,
            ))

        return results

    def _extract_v4_plugins(self, content: str, file_path: str) -> List[TailwindPluginInfo]:
        """Extract v4 @plugin directive references."""
        results: List[TailwindPluginInfo] = []

        for m in self.V4_PLUGIN_PATTERN.finditer(content):
            path = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Check if it's a known plugin
            is_official = any(p in path for p in self.OFFICIAL_PLUGINS)
            name = path.split('/')[-1].replace('.js', '').replace('.ts', '')

            results.append(TailwindPluginInfo(
                name=name,
                type='v4-directive',
                package=path,
                is_official=is_official,
                file=file_path,
                line_number=line_num,
            ))

        return results
