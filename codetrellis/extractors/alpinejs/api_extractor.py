"""
Alpine.js API Extractor for CodeTrellis

Extracts Alpine.js API usage patterns from JavaScript/TypeScript/HTML source code:
- Import patterns (alpinejs, @alpinejs/*)
- CDN script tag references
- Alpine.start() initialization
- Alpine.store() API calls
- Alpine.data() API calls
- Alpine.directive() API calls
- Alpine.magic() API calls
- Alpine.plugin() API calls
- Alpine.bind() API calls (v3.10+)
- Alpine.evaluate() API calls
- TypeScript type imports
- Ecosystem integrations (HTMX, Livewire, Turbo/Hotwire, Tailwind)

Supports:
- Alpine.js v1.x (CDN only, no Alpine.start())
- Alpine.js v2.x (CDN, Alpine global)
- Alpine.js v3.x (npm/CDN, Alpine.start(), modular API)

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class AlpineImportInfo:
    """Information about an Alpine.js import statement."""
    source: str  # Package name (e.g., 'alpinejs', '@alpinejs/mask')
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    import_category: str = ""  # core, plugin, type
    is_type_import: bool = False
    is_cdn: bool = False


@dataclass
class AlpineIntegrationInfo:
    """Information about an Alpine.js ecosystem integration."""
    name: str  # Integration name (e.g., 'htmx', 'livewire')
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # frontend, backend, tooling
    source_package: str = ""


@dataclass
class AlpineTypeInfo:
    """Information about an Alpine.js TypeScript type usage."""
    type_name: str  # Alpine, AlpineComponent, etc.
    file: str = ""
    line_number: int = 0
    source: str = ""  # Import source


@dataclass
class AlpineCDNInfo:
    """Information about an Alpine.js CDN script inclusion."""
    url: str
    file: str = ""
    line_number: int = 0
    has_defer: bool = False
    version: str = ""  # Version from URL if detectable
    is_plugin: bool = False
    plugin_name: str = ""


class AlpineApiExtractor:
    """
    Extracts Alpine.js API usage and ecosystem integration patterns.

    Detects:
    - ESM/CJS imports of alpinejs and @alpinejs/* packages
    - CDN script tags for Alpine.js and plugins
    - Alpine.start() / window.Alpine / document.addEventListener('alpine:init')
    - Alpine.store(), Alpine.data(), Alpine.directive(), Alpine.magic(), Alpine.plugin()
    - Alpine.bind() (v3.10+), Alpine.evaluate()
    - TypeScript type imports
    - Ecosystem: HTMX, Laravel Livewire, Hotwire/Turbo, Tailwind CSS
    """

    # ESM import patterns
    IMPORT_PATTERN = re.compile(
        r"""(?:import\s+(?:type\s+)?\{([^}]+)\}\s+from|"""
        r"""import\s+(\w+)\s+from|"""
        r"""import\s+)\s*['\"]([^'\"]+)['\"]""",
        re.MULTILINE
    )

    # CommonJS require pattern
    REQUIRE_PATTERN = re.compile(
        r"""(?:const|let|var)\s+(\w+)\s*=\s*require\(\s*['\"]([^'\"]+)['"]\s*\)""",
        re.MULTILINE
    )

    # CDN script tag pattern
    CDN_PATTERN = re.compile(
        r"""<script[^>]*src\s*=\s*['"]([^'"]*alpinejs?[^'"]*)['"]\s*[^>]*>""",
        re.MULTILINE | re.IGNORECASE
    )

    # Alpine API calls
    ALPINE_API_PATTERN = re.compile(
        r"""Alpine\.(start|store|data|directive|magic|plugin|bind|evaluate|effect|raw|reactive|release|disableEffectScheduling|setReactivity|setEvaluator|closestDataStack|skipDuringClone|onlyDuringClone|addRootSelector|addInitSelector|addScopeToNode|dontAutoEvaluateFunctions|interceptor|transition|closestRoot|destroyTree|findClosest|interceptInit|version)\s*\(""",
        re.MULTILINE
    )

    # window.Alpine assignment
    WINDOW_ALPINE_PATTERN = re.compile(
        r"""window\.Alpine\s*=""",
        re.MULTILINE
    )

    # document.addEventListener('alpine:init', ...)
    ALPINE_INIT_EVENT_PATTERN = re.compile(
        r"""(?:document|window)\.addEventListener\(\s*['"]alpine:(?:init|initialized?)['"]\s*,""",
        re.MULTILINE
    )

    # CDN version extraction (e.g., alpinejs@3.14.1)
    VERSION_FROM_CDN = re.compile(
        r"""alpinejs?@(\d+\.\d+(?:\.\d+)?)""",
    )

    # Alpine.js package detection prefixes
    ALPINE_PACKAGES = [
        'alpinejs',
        '@alpinejs/',
    ]

    # Ecosystem integration detection patterns
    ECOSYSTEM_PATTERNS = {
        'htmx': re.compile(r"""(?:from\s+['"]htmx\.org['"]|<script[^>]*htmx|hx-(?:get|post|put|delete|patch|trigger|swap|target))""", re.MULTILINE | re.IGNORECASE),
        'livewire': re.compile(r"""(?:@livewire|wire:|Livewire\.|livewire/)""", re.MULTILINE | re.IGNORECASE),
        'turbo': re.compile(r"""(?:@hotwired/turbo|turbo-frame|turbo-stream|data-turbo)""", re.MULTILINE | re.IGNORECASE),
        'tailwind': re.compile(r"""(?:tailwindcss|@tailwind|class="[^"]*(?:flex|grid|text-|bg-|p-|m-|w-|h-))""", re.MULTILINE),
        'laravel': re.compile(r"""(?:@csrf|@auth|@yield|@extends|@section|blade\.php)""", re.MULTILINE | re.IGNORECASE),
        'django': re.compile(r"""(?:\{%\s*load|{%\s*block|{%\s*extends|{%\s*static)""", re.MULTILINE),
        'rails': re.compile(r"""(?:<%=|<%-|content_for|render\s+partial|turbo_stream)""", re.MULTILINE),
        'phoenix_liveview': re.compile(r"""(?:phx-click|phx-change|phx-submit|live_component)""", re.MULTILINE),
    }

    # Known Alpine.js TypeScript types
    ALPINE_TYPES = {
        'Alpine', 'AlpineComponent', 'DirectiveCallback', 'DirectiveData',
        'DirectiveUtilities', 'ElementWithXAttributes', 'InferInterceptors',
        'Interceptor', 'InterceptorObject', 'Magics', 'MagicUtilities',
        'PluginCallback', 'Stores', 'XAttributes',
    }

    def extract(self, content: str, file_path: str = "") -> tuple:
        """Extract Alpine.js API usage patterns.

        Args:
            content: Source code content.
            file_path: Path to the source file.

        Returns:
            Tuple of (List[AlpineImportInfo], List[AlpineIntegrationInfo],
                       List[AlpineTypeInfo], List[AlpineCDNInfo]).
        """
        imports: List[AlpineImportInfo] = []
        integrations: List[AlpineIntegrationInfo] = []
        types: List[AlpineTypeInfo] = []
        cdns: List[AlpineCDNInfo] = []

        # Extract ESM imports
        for match in self.IMPORT_PATTERN.finditer(content):
            named = match.group(1)
            default = match.group(2) or ""
            source = match.group(3)

            if not self._is_alpine_import(source):
                continue

            line_num = content[:match.start()].count('\n') + 1
            named_imports = [n.strip() for n in named.split(',')] if named else []
            is_type = 'import type' in content[max(0, match.start() - 15):match.start() + 15]
            category = self._categorize_import(source)

            imports.append(AlpineImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_imports,
                default_import=default,
                import_category=category,
                is_type_import=is_type,
                is_cdn=False,
            ))

            # Extract TypeScript types
            if is_type:
                for ni in named_imports:
                    if ni in self.ALPINE_TYPES:
                        types.append(AlpineTypeInfo(
                            type_name=ni,
                            file=file_path,
                            line_number=line_num,
                            source=source,
                        ))

        # Extract require imports
        for match in self.REQUIRE_PATTERN.finditer(content):
            var_name = match.group(1)
            source = match.group(2)

            if not self._is_alpine_import(source):
                continue

            line_num = content[:match.start()].count('\n') + 1
            category = self._categorize_import(source)

            imports.append(AlpineImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=[],
                default_import=var_name,
                import_category=category,
                is_type_import=False,
                is_cdn=False,
            ))

        # Extract CDN script tags
        for match in self.CDN_PATTERN.finditer(content):
            url = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            tag = content[match.start():match.end()]
            has_defer = 'defer' in tag.lower()

            version = ""
            ver_match = self.VERSION_FROM_CDN.search(url)
            if ver_match:
                version = ver_match.group(1)

            is_plugin = any(p in url for p in ['intersect', 'persist', 'mask', 'morph',
                                                'focus', 'collapse', 'anchor', 'sort', 'ui', 'resize'])
            plugin_name = ""
            if is_plugin:
                for p in ['intersect', 'persist', 'mask', 'morph', 'focus',
                          'collapse', 'anchor', 'sort', 'ui', 'resize']:
                    if p in url:
                        plugin_name = p
                        break

            cdns.append(AlpineCDNInfo(
                url=url,
                file=file_path,
                line_number=line_num,
                has_defer=has_defer,
                version=version,
                is_plugin=is_plugin,
                plugin_name=plugin_name,
            ))

        # Detect ecosystem integrations
        for eco_name, pattern in self.ECOSYSTEM_PATTERNS.items():
            if pattern.search(content):
                integrations.append(AlpineIntegrationInfo(
                    name=eco_name,
                    file=file_path,
                    line_number=0,
                    integration_type=self._categorize_integration(eco_name),
                    source_package=eco_name,
                ))

        return imports, integrations, types, cdns

    def _is_alpine_import(self, source: str) -> bool:
        """Check if an import source is an Alpine.js package.

        Args:
            source: Import source string.

        Returns:
            True if this is an Alpine.js import.
        """
        return any(source == pkg or source.startswith(pkg) for pkg in self.ALPINE_PACKAGES)

    def _categorize_import(self, source: str) -> str:
        """Categorize an Alpine.js import.

        Args:
            source: Import source string.

        Returns:
            Category string.
        """
        if source == 'alpinejs':
            return 'core'
        if source.startswith('@alpinejs/'):
            return 'plugin'
        return 'core'

    def _categorize_integration(self, name: str) -> str:
        """Categorize an ecosystem integration.

        Args:
            name: Integration name.

        Returns:
            Integration type string.
        """
        frontend = {'htmx', 'turbo', 'tailwind'}
        backend = {'livewire', 'laravel', 'django', 'rails', 'phoenix_liveview'}
        if name in frontend:
            return 'frontend'
        if name in backend:
            return 'backend'
        return 'tooling'
