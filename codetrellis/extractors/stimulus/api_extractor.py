"""
Stimulus API / Ecosystem Extractor for CodeTrellis

Extracts Stimulus/Hotwire API usage and ecosystem integrations:
- Import patterns: @hotwired/stimulus, stimulus (legacy), @hotwired/turbo,
                    @hotwired/turbo-rails, @hotwired/strada
- Application.start(), application.register(), application.load()
- Turbo integration: turbo-frame, turbo-stream HTML elements,
                      Turbo.visit(), Turbo.connectStreamSource(),
                      turbo:* events, turbo_frame_tag/turbo_stream_from helpers
- Strada integration: BridgeComponent, BridgeElement, bridge callbacks
- CDN detection: unpkg, jsDelivr, skypack, esm.sh
- Ecosystem integrations: Rails (Importmap, Propshaft, Sprockets),
                           Laravel (Vite, Mix), Django, Phoenix, Spring Boot

Supports:
- Stimulus v1.x (stimulus npm package)
- Stimulus v2.x-v3.x (@hotwired/stimulus)
- Turbo v7.x-v8.x (@hotwired/turbo)
- Turbo Rails (@hotwired/turbo-rails)
- Strada v1.x (@hotwired/strada)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StimulusImportInfo:
    """Information about a Stimulus/Hotwire import."""
    source: str  # Import source (e.g., "@hotwired/stimulus")
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    is_type_import: bool = False
    import_type: str = ""  # esm, cjs, cdn, dynamic
    version_hint: str = ""  # v1, v2, v3


@dataclass
class StimulusIntegrationInfo:
    """Information about a Stimulus/Hotwire ecosystem integration."""
    name: str  # Integration name (e.g., "rails", "turbo")
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # framework, bundler, templating, server


@dataclass
class StimulusConfigInfo:
    """Information about Stimulus/Turbo configuration."""
    config_key: str  # Config key (e.g., "Turbo.session.drive")
    file: str = ""
    line_number: int = 0
    config_value: str = ""


@dataclass
class StimulusCDNInfo:
    """Information about Stimulus/Hotwire CDN usage."""
    url: str
    file: str = ""
    line_number: int = 0
    version: str = ""
    has_defer: bool = False
    has_integrity: bool = False
    package: str = ""  # stimulus, turbo, strada


# ESM import patterns
ESM_IMPORT_PATTERN = re.compile(
    r'import\s+'
    r'(?:'
    r'(?P<default>\w+)\s*,?\s*'
    r')?'
    r'(?:\{(?P<named>[^}]+)\}\s*)?'
    r'from\s+["\'](?P<source>[^"\']+)["\']',
    re.MULTILINE
)

# CJS require patterns
CJS_REQUIRE_PATTERN = re.compile(
    r'(?:const|let|var)\s+'
    r'(?:'
    r'(?:\{(?P<named>[^}]+)\})'
    r'|(?P<default>\w+)'
    r')\s*=\s*require\s*\(\s*["\'](?P<source>[^"\']+)["\']\s*\)',
    re.MULTILINE
)

# Dynamic import
DYNAMIC_IMPORT_PATTERN = re.compile(
    r'import\s*\(\s*["\'](?P<source>[^"\']+)["\']\s*\)',
    re.MULTILINE
)

# Side-effect import: import "module" or import 'module'
SIDE_EFFECT_IMPORT_PATTERN = re.compile(
    r'^import\s+["\'](?P<source>[^"\']+)["\']\s*;?\s*$',
    re.MULTILINE
)

# CDN script tags
CDN_PATTERN = re.compile(
    r'<script[^>]*\bsrc\s*=\s*["\'](?P<url>[^"\']*(?:stimulus|turbo|strada|hotwired)[^"\']*)["\'][^>]*>',
    re.IGNORECASE
)

# Application.start() / Application.load()
APP_START_PATTERN = re.compile(
    r'(?:Application|Stimulus\.Application)\s*\.\s*(?P<method>start|load)\s*\(',
    re.MULTILINE
)

# application.register("name", Controller)
APP_REGISTER_PATTERN = re.compile(
    r'(?:application|app)\s*\.\s*register\s*\(\s*["\'](?P<name>[^"\']+)["\']\s*,\s*(?P<controller>\w+)',
    re.MULTILINE
)

# Turbo elements: <turbo-frame id="...">, <turbo-stream action="..." target="...">
TURBO_FRAME_PATTERN = re.compile(
    r'<turbo-frame\s+[^>]*id\s*=\s*["\'](?P<id>[^"\']+)["\']',
    re.IGNORECASE
)

TURBO_STREAM_PATTERN = re.compile(
    r'<turbo-stream\s+[^>]*action\s*=\s*["\'](?P<action>\w+)["\'][^>]*target\s*=\s*["\'](?P<target>[^"\']+)["\']',
    re.IGNORECASE
)

# Turbo events: turbo:load, turbo:before-visit, turbo:submit-start, turbo:morph-*
TURBO_EVENT_PATTERN = re.compile(
    r'["\'](?P<event>turbo:[\w-]+)["\']',
)

# Turbo JS API: Turbo.visit(), Turbo.connectStreamSource(), Turbo.session.*
TURBO_API_PATTERN = re.compile(
    r'Turbo\s*\.\s*(?P<method>\w+)\s*\(',
    re.MULTILINE
)

# Turbo configuration: Turbo.session.drive = false, etc.
TURBO_CONFIG_PATTERN = re.compile(
    r'Turbo\s*\.\s*session\s*\.\s*(?P<key>\w+)\s*=\s*(?P<value>[^;\n]+)',
)

# Rails helpers: turbo_frame_tag, turbo_stream_from, stimulus_controller
RAILS_HELPER_PATTERN = re.compile(
    r'(?:turbo_frame_tag|turbo_stream_from|turbo_stream\b|stimulus_controller|data_controller)',
    re.MULTILINE
)

# Importmap pin: pin "@hotwired/stimulus", to: "stimulus.min.js"
IMPORTMAP_PIN_PATTERN = re.compile(
    r'pin\s+["\'](?P<package>[^"\']*(?:hotwired|stimulus|turbo|strada)[^"\']*)["\']',
    re.MULTILINE
)

# Hotwire source packages
HOTWIRE_PACKAGES = {
    '@hotwired/stimulus': 'stimulus',
    '@hotwired/turbo': 'turbo',
    '@hotwired/turbo-rails': 'turbo-rails',
    '@hotwired/strada': 'strada',
    'stimulus': 'stimulus-v1',
    'stimulus-webpack-helpers': 'stimulus-v1',
    'stimulus-use': 'stimulus-use',
    'stimulus-vite-helpers': 'stimulus-vite',
    'stimulus-autocomplete': 'stimulus-autocomplete',
    'stimulus-sortable': 'stimulus-sortable',
    'stimulus-components': 'stimulus-components',
    'tailwindcss-stimulus-components': 'tailwind-stimulus',
    'stimulus-dropdown': 'stimulus-dropdown',
    'stimulus-rails-nested-form': 'stimulus-nested-form',
    'stimulus-textarea-autogrow': 'stimulus-autogrow',
    'stimulus-flatpickr': 'stimulus-flatpickr',
    'stimulus-content-loader': 'stimulus-content-loader',
    'stimulus-reveal-controller': 'stimulus-reveal',
    'stimulus-checkbox-select-all': 'stimulus-checkbox',
    'stimulus-character-counter': 'stimulus-counter',
}


class StimulusApiExtractor:
    """Extracts Stimulus/Hotwire API usage and ecosystem integrations."""

    def extract_imports(self, content: str, file_path: str = "") -> List[StimulusImportInfo]:
        """Extract Stimulus/Hotwire import statements.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusImportInfo objects.
        """
        if not content or not content.strip():
            return []

        imports: List[StimulusImportInfo] = []

        # ESM imports
        for match in ESM_IMPORT_PATTERN.finditer(content):
            source = match.group('source')
            if not self._is_hotwire_source(source):
                continue

            named = match.group('named')
            named_imports = [n.strip().split(' as ')[0].strip() for n in named.split(',')] if named else []
            named_imports = [n for n in named_imports if n]

            default_import = match.group('default') or ''
            line = content[:match.start()].count('\n') + 1

            # Detect type imports
            raw = content[max(0, match.start() - 20):match.start()]
            is_type = 'type' in raw

            version_hint = self._detect_version(source)

            imports.append(StimulusImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports[:15],
                default_import=default_import,
                is_type_import=is_type,
                import_type="esm",
                version_hint=version_hint,
            ))

        # CJS require
        for match in CJS_REQUIRE_PATTERN.finditer(content):
            source = match.group('source')
            if not self._is_hotwire_source(source):
                continue

            named = match.group('named')
            named_imports = [n.strip().split(':')[0].strip() for n in named.split(',')] if named else []
            named_imports = [n for n in named_imports if n]

            default_import = match.group('default') or ''
            line = content[:match.start()].count('\n') + 1

            imports.append(StimulusImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports[:15],
                default_import=default_import,
                import_type="cjs",
                version_hint=self._detect_version(source),
            ))

        # Dynamic imports
        for match in DYNAMIC_IMPORT_PATTERN.finditer(content):
            source = match.group('source')
            if not self._is_hotwire_source(source):
                continue

            line = content[:match.start()].count('\n') + 1
            imports.append(StimulusImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                import_type="dynamic",
                version_hint=self._detect_version(source),
            ))

        # Side-effect imports: import "@hotwired/turbo"
        for match in SIDE_EFFECT_IMPORT_PATTERN.finditer(content):
            source = match.group('source')
            if not self._is_hotwire_source(source):
                continue

            # Skip if already captured by ESM pattern (has from keyword)
            already = any(imp.source == source for imp in imports)
            if already:
                continue

            line = content[:match.start()].count('\n') + 1
            imports.append(StimulusImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                import_type="esm",
                version_hint=self._detect_version(source),
            ))

        return imports

    def extract_integrations(self, content: str, file_path: str = "") -> List[StimulusIntegrationInfo]:
        """Extract ecosystem integration patterns.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusIntegrationInfo objects.
        """
        if not content or not content.strip():
            return []

        integrations: List[StimulusIntegrationInfo] = []
        seen = set()

        # Turbo elements (turbo-frame, turbo-stream)
        if re.search(r'<turbo-frame\b', content, re.IGNORECASE):
            if 'turbo-frame' not in seen:
                seen.add('turbo-frame')
                integrations.append(StimulusIntegrationInfo(
                    name="turbo-frame",
                    file=file_path,
                    line_number=self._find_line(content, '<turbo-frame'),
                    integration_type="turbo",
                ))

        if re.search(r'<turbo-stream\b', content, re.IGNORECASE):
            if 'turbo-stream' not in seen:
                seen.add('turbo-stream')
                integrations.append(StimulusIntegrationInfo(
                    name="turbo-stream",
                    file=file_path,
                    line_number=self._find_line(content, '<turbo-stream'),
                    integration_type="turbo",
                ))

        # Rails integration: ERB helpers, Importmap, Propshaft
        if RAILS_HELPER_PATTERN.search(content):
            if 'rails' not in seen:
                seen.add('rails')
                integrations.append(StimulusIntegrationInfo(
                    name="rails",
                    file=file_path,
                    line_number=self._find_line(content, 'turbo_frame_tag'),
                    integration_type="framework",
                ))

        # Importmap
        if IMPORTMAP_PIN_PATTERN.search(content):
            if 'importmap' not in seen:
                seen.add('importmap')
                integrations.append(StimulusIntegrationInfo(
                    name="importmap",
                    file=file_path,
                    line_number=self._find_line(content, 'pin '),
                    integration_type="bundler",
                ))

        # Turbo events
        turbo_events = TURBO_EVENT_PATTERN.findall(content)
        if turbo_events:
            if 'turbo-events' not in seen:
                seen.add('turbo-events')
                integrations.append(StimulusIntegrationInfo(
                    name="turbo-events",
                    file=file_path,
                    line_number=self._find_line(content, 'turbo:'),
                    integration_type="turbo",
                ))

        # Turbo API
        turbo_apis = TURBO_API_PATTERN.findall(content)
        if turbo_apis:
            if 'turbo-api' not in seen:
                seen.add('turbo-api')
                integrations.append(StimulusIntegrationInfo(
                    name="turbo-api",
                    file=file_path,
                    line_number=self._find_line(content, 'Turbo.'),
                    integration_type="turbo",
                ))

        # Strada / native bridge
        if re.search(r'BridgeComponent|BridgeElement|@hotwired/strada', content):
            if 'strada' not in seen:
                seen.add('strada')
                integrations.append(StimulusIntegrationInfo(
                    name="strada",
                    file=file_path,
                    line_number=self._find_line(content, 'Bridge'),
                    integration_type="native",
                ))

        # Laravel integration (Vite + Stimulus)
        if re.search(r'@vite|laravel.*stimulus|stimulus.*laravel', content, re.IGNORECASE):
            if 'laravel' not in seen:
                seen.add('laravel')
                integrations.append(StimulusIntegrationInfo(
                    name="laravel",
                    file=file_path,
                    line_number=self._find_line(content, 'laravel'),
                    integration_type="framework",
                ))

        # Django integration
        if re.search(r'django.*stimulus|stimulus.*django|{%.*stimulus', content, re.IGNORECASE):
            if 'django' not in seen:
                seen.add('django')
                integrations.append(StimulusIntegrationInfo(
                    name="django",
                    file=file_path,
                    line_number=self._find_line(content, 'django'),
                    integration_type="framework",
                ))

        # Phoenix integration
        if re.search(r'phx-|phoenix.*stimulus|stimulus.*phoenix', content, re.IGNORECASE):
            if 'phoenix' not in seen:
                seen.add('phoenix')
                integrations.append(StimulusIntegrationInfo(
                    name="phoenix",
                    file=file_path,
                    line_number=self._find_line(content, 'phx-'),
                    integration_type="framework",
                ))

        # webpack helpers (stimulus-webpack-helpers / @hotwired/stimulus-loading)
        if re.search(r'stimulus-webpack-helpers|definitionsFromContext|eagerControllers|lazyControllers', content):
            if 'webpack' not in seen:
                seen.add('webpack')
                integrations.append(StimulusIntegrationInfo(
                    name="webpack",
                    file=file_path,
                    line_number=self._find_line(content, 'definitionsFromContext'),
                    integration_type="bundler",
                ))

        # Vite helpers (stimulus-vite-helpers)
        if re.search(r'stimulus-vite-helpers|registerControllers|import\.meta\.glob', content):
            if 'vite' not in seen:
                seen.add('vite')
                integrations.append(StimulusIntegrationInfo(
                    name="vite",
                    file=file_path,
                    line_number=self._find_line(content, 'stimulus-vite'),
                    integration_type="bundler",
                ))

        return integrations

    def extract_configs(self, content: str, file_path: str = "") -> List[StimulusConfigInfo]:
        """Extract Turbo/Stimulus configuration settings.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusConfigInfo objects.
        """
        if not content or not content.strip():
            return []

        configs: List[StimulusConfigInfo] = []

        # Turbo.session configuration
        for match in TURBO_CONFIG_PATTERN.finditer(content):
            key = match.group('key')
            value = match.group('value').strip().rstrip(';')
            line = content[:match.start()].count('\n') + 1
            configs.append(StimulusConfigInfo(
                config_key=f"Turbo.session.{key}",
                file=file_path,
                line_number=line,
                config_value=value[:200],
            ))

        # Application.start/load
        for match in APP_START_PATTERN.finditer(content):
            method = match.group('method')
            line = content[:match.start()].count('\n') + 1
            configs.append(StimulusConfigInfo(
                config_key=f"Application.{method}",
                file=file_path,
                line_number=line,
            ))

        return configs

    def extract_cdns(self, content: str, file_path: str = "") -> List[StimulusCDNInfo]:
        """Extract CDN script tag references.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusCDNInfo objects.
        """
        if not content or not content.strip():
            return []

        cdns: List[StimulusCDNInfo] = []

        for match in CDN_PATTERN.finditer(content):
            url = match.group('url')
            line = content[:match.start()].count('\n') + 1
            tag = match.group(0)

            # Detect version from URL
            version = ""
            ver_match = re.search(r'@(\d+\.\d+(?:\.\d+)?)', url)
            if ver_match:
                version = ver_match.group(1)

            # Detect package
            package = "stimulus"
            if 'turbo' in url.lower():
                package = "turbo"
            elif 'strada' in url.lower():
                package = "strada"

            cdns.append(StimulusCDNInfo(
                url=url,
                file=file_path,
                line_number=line,
                version=version,
                has_defer='defer' in tag.lower(),
                has_integrity='integrity' in tag.lower(),
                package=package,
            ))

        return cdns

    def _is_hotwire_source(self, source: str) -> bool:
        """Check if an import source is a Hotwire/Stimulus package."""
        return source in HOTWIRE_PACKAGES or source.startswith('@hotwired/')

    def _detect_version(self, source: str) -> str:
        """Detect Stimulus version from import source."""
        if source == 'stimulus' or source == 'stimulus-webpack-helpers':
            return 'v1'
        elif source.startswith('@hotwired/'):
            return 'v2'  # v2+ uses @hotwired scope
        return ''

    def _find_line(self, content: str, search: str) -> int:
        """Find line number for a search string."""
        idx = content.find(search)
        if idx < 0:
            # Try case-insensitive
            idx = content.lower().find(search.lower())
        if idx >= 0:
            return content[:idx].count('\n') + 1
        return 0
