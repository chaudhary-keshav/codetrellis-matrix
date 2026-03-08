"""
Alpine.js Plugin Extractor for CodeTrellis

Extracts Alpine.js plugin registrations and custom extensions:
- Alpine.plugin() registrations
- @alpinejs/* official plugins (mask, intersect, persist, morph, focus,
  collapse, anchor, sort, ui, resize)
- Alpine.directive() custom directive definitions
- Alpine.magic() custom magic property definitions
- Third-party plugin detection

Supports:
- Alpine.js v3.x (plugin system not available in v1/v2)
- Official @alpinejs/* plugins
- Custom plugins

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class AlpinePluginInfo:
    """Information about an Alpine.js plugin registration."""
    name: str  # Plugin name or package name
    file: str = ""
    line_number: int = 0
    plugin_type: str = ""  # official, custom, third-party
    source_package: str = ""  # @alpinejs/mask, etc.
    is_official: bool = False


@dataclass
class AlpineCustomDirectiveInfo:
    """Information about a custom Alpine.js directive definition."""
    name: str  # Directive name (without x- prefix)
    file: str = ""
    line_number: int = 0
    has_expression: bool = False
    has_modifiers: bool = False
    has_cleanup: bool = False


@dataclass
class AlpineCustomMagicInfo:
    """Information about a custom Alpine.js magic property definition."""
    name: str  # Magic name (without $ prefix)
    file: str = ""
    line_number: int = 0
    has_getter: bool = False


class AlpinePluginExtractor:
    """
    Extracts Alpine.js plugin registrations and custom extensions.

    Detects:
    - Alpine.plugin(pluginFn) calls
    - import statements for @alpinejs/* packages
    - Alpine.directive('name', callback) custom directives
    - Alpine.magic('name', callback) custom magics
    - Third-party Alpine plugins
    """

    # Alpine.plugin() registration
    PLUGIN_PATTERN = re.compile(
        r"""Alpine\.plugin\(\s*(\w+)""",
        re.MULTILINE
    )

    # Alpine.directive() custom directive
    CUSTOM_DIRECTIVE_PATTERN = re.compile(
        r"""Alpine\.directive\(\s*['"](\w+)['"]\s*,""",
        re.MULTILINE
    )

    # Alpine.magic() custom magic
    CUSTOM_MAGIC_PATTERN = re.compile(
        r"""Alpine\.magic\(\s*['"](\w+)['"]\s*,""",
        re.MULTILINE
    )

    # Import pattern for @alpinejs/* packages
    ALPINE_IMPORT_PATTERN = re.compile(
        r"""(?:import\s+(\w+)\s+from|import\s+\{([^}]+)\}\s+from|require\(['"])\s*['"](@alpinejs/[\w-]+)['"]""",
        re.MULTILINE
    )

    # CDN script src patterns for Alpine plugins
    CDN_PLUGIN_PATTERN = re.compile(
        r"""<script[^>]*src\s*=\s*['"][^'"]*alpinejs/([a-z-]+)""",
        re.MULTILINE | re.IGNORECASE
    )

    # Official Alpine.js plugins
    OFFICIAL_PLUGINS = {
        'mask': '@alpinejs/mask',
        'intersect': '@alpinejs/intersect',
        'persist': '@alpinejs/persist',
        'morph': '@alpinejs/morph',
        'focus': '@alpinejs/focus',
        'collapse': '@alpinejs/collapse',
        'anchor': '@alpinejs/anchor',
        'sort': '@alpinejs/sort',
        'ui': '@alpinejs/ui',
        'resize': '@alpinejs/resize',
    }

    # Third-party Alpine.js plugins
    THIRD_PARTY_PLUGINS = {
        'alpine-turbo-drive-adapter': 'Turbo/Hotwire adapter',
        'alpinejs-notify': 'Notifications',
        'alpine-clipboard': 'Clipboard',
        'alpine-tooltip': 'Tooltips',
        'alpine-magic-helpers': 'Magic helpers',
        'alpine-test-utils': 'Testing utilities',
        'alpine-i18n': 'Internationalization',
        'alpinejs-ray': 'Ray debugging',
    }

    def extract(self, content: str, file_path: str = "") -> tuple:
        """Extract Alpine.js plugin information.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            Tuple of (List[AlpinePluginInfo], List[AlpineCustomDirectiveInfo],
                       List[AlpineCustomMagicInfo]).
        """
        plugins: List[AlpinePluginInfo] = []
        custom_directives: List[AlpineCustomDirectiveInfo] = []
        custom_magics: List[AlpineCustomMagicInfo] = []

        # Extract Alpine.plugin() calls
        for match in self.PLUGIN_PATTERN.finditer(content):
            plugin_var = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Try to resolve plugin name from imports
            source_pkg, is_official = self._resolve_plugin_source(content, plugin_var)

            plugins.append(AlpinePluginInfo(
                name=plugin_var,
                file=file_path,
                line_number=line_num,
                plugin_type="official" if is_official else "custom",
                source_package=source_pkg,
                is_official=is_official,
            ))

        # Extract @alpinejs/* imports (even without Alpine.plugin() call)
        for match in self.ALPINE_IMPORT_PATTERN.finditer(content):
            pkg = match.group(3)
            if pkg:
                line_num = content[:match.start()].count('\n') + 1
                plugin_name = pkg.split('/')[-1]
                # Only add if not already found via Alpine.plugin()
                if not any(p.source_package == pkg for p in plugins):
                    plugins.append(AlpinePluginInfo(
                        name=plugin_name,
                        file=file_path,
                        line_number=line_num,
                        plugin_type="official",
                        source_package=pkg,
                        is_official=True,
                    ))

        # Extract CDN plugin references
        for match in self.CDN_PLUGIN_PATTERN.finditer(content):
            plugin_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            if plugin_name in self.OFFICIAL_PLUGINS:
                if not any(p.name == plugin_name for p in plugins):
                    plugins.append(AlpinePluginInfo(
                        name=plugin_name,
                        file=file_path,
                        line_number=line_num,
                        plugin_type="official",
                        source_package=self.OFFICIAL_PLUGINS[plugin_name],
                        is_official=True,
                    ))

        # Extract custom directives
        for match in self.CUSTOM_DIRECTIVE_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check the callback body for expression/modifier/cleanup usage
            body = self._extract_callback_body(content, match.end())
            has_expression = 'expression' in body or 'evaluate' in body
            has_modifiers = 'modifiers' in body
            has_cleanup = 'cleanup' in body

            custom_directives.append(AlpineCustomDirectiveInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                has_expression=has_expression,
                has_modifiers=has_modifiers,
                has_cleanup=has_cleanup,
            ))

        # Extract custom magics
        for match in self.CUSTOM_MAGIC_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            body = self._extract_callback_body(content, match.end())
            has_getter = 'return' in body

            custom_magics.append(AlpineCustomMagicInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                has_getter=has_getter,
            ))

        return plugins, custom_directives, custom_magics

    def _resolve_plugin_source(self, content: str, var_name: str) -> tuple:
        """Resolve a plugin variable name to its import source.

        Args:
            content: Full source code.
            var_name: Variable name used in Alpine.plugin().

        Returns:
            Tuple of (source_package: str, is_official: bool).
        """
        # Check for import of this variable
        import_pat = re.compile(
            rf"""import\s+{re.escape(var_name)}\s+from\s+['"]([^'"]+)['"]""",
            re.MULTILINE
        )
        match = import_pat.search(content)
        if match:
            source = match.group(1)
            is_official = source.startswith('@alpinejs/')
            return source, is_official

        # Check for require
        require_pat = re.compile(
            rf"""{re.escape(var_name)}\s*=\s*require\(['"]([^'"]+)['"]\)""",
            re.MULTILINE
        )
        match = require_pat.search(content)
        if match:
            source = match.group(1)
            is_official = source.startswith('@alpinejs/')
            return source, is_official

        return "", False

    def _extract_callback_body(self, content: str, start: int) -> str:
        """Extract the callback function body.

        Args:
            content: Full source code.
            start: Position after the comma in Alpine.directive('name', ...

        Returns:
            Callback body string.
        """
        depth = 0
        body_start = -1
        for i in range(start, min(start + 3000, len(content))):
            ch = content[i]
            if ch == '{':
                if depth == 0:
                    body_start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and body_start >= 0:
                    return content[body_start:i + 1]
        return ""
