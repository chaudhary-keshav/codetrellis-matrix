"""
HTMX API Extractor for CodeTrellis

Extracts HTMX API usage from HTML and JavaScript/TypeScript source code:
- Import patterns: import from 'htmx.org', require('htmx.org'), npm htmx.org
- CDN script tags: unpkg, cdnjs, jsdelivr, htmx.org/dist
- htmx JS API: htmx.ajax(), htmx.process(), htmx.on(), htmx.off(),
  htmx.trigger(), htmx.find(), htmx.findAll(), htmx.closest(),
  htmx.values(), htmx.remove(), htmx.addClass(), htmx.removeClass(),
  htmx.toggleClass(), htmx.takeClass(), htmx.swap()
- htmx configuration: htmx.config.*, htmx.logAll(), htmx.logger
- Ecosystem integrations: Alpine.js, _hyperscript, Django, Flask, Rails,
  Laravel, FastAPI, Go/templ, ASP.NET, Spring Boot, Phoenix LiveView
- TypeScript types: htmx type definitions

Supports:
- HTMX v1.x (htmx.org v1.*, CDN patterns)
- HTMX v2.x (htmx.org v2.*, new API methods, hx-on syntax)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class HtmxImportInfo:
    """Information about an HTMX import."""
    source: str  # htmx.org, htmx.org/dist/htmx.min.js, etc.
    file: str = ""
    line_number: int = 0
    import_type: str = ""  # esm, cjs, script_tag, side_effect
    default_import: str = ""
    named_imports: List[str] = field(default_factory=list)
    is_type_import: bool = False


@dataclass
class HtmxCDNInfo:
    """Information about an HTMX CDN script tag."""
    url: str
    file: str = ""
    line_number: int = 0
    version: str = ""
    has_defer: bool = False
    has_integrity: bool = False
    is_extension: bool = False
    extension_name: str = ""


@dataclass
class HtmxConfigInfo:
    """Information about an HTMX configuration setting."""
    config_key: str  # e.g., historyEnabled, defaultSwapStyle
    file: str = ""
    line_number: int = 0
    config_value: str = ""


@dataclass
class HtmxIntegrationInfo:
    """Information about an HTMX ecosystem integration."""
    name: str  # alpine, hyperscript, django, flask, etc.
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # framework, library, templating
    evidence: str = ""  # What pattern triggered detection


class HtmxApiExtractor:
    """
    Extracts HTMX API usage, imports, CDN tags, config, and integrations.

    Detects how HTMX is loaded (npm/CDN), configured, and what
    ecosystem integrations are present.
    """

    # ESM import pattern
    ESM_IMPORT_PATTERN = re.compile(
        r"""import\s+(?:(?:(\w+)\s*,?\s*)?(?:\{([^}]*)\}\s*)?from\s+)?['"]([^'"]*htmx[^'"]*)['"]\s*;?""",
        re.MULTILINE
    )

    # CJS require pattern
    CJS_REQUIRE_PATTERN = re.compile(
        r"""(?:const|let|var)\s+(\w+)\s*=\s*require\(\s*['"]([^'"]*htmx[^'"]*)['"]\s*\)""",
        re.MULTILINE
    )

    # Side-effect import
    SIDE_EFFECT_IMPORT_PATTERN = re.compile(
        r"""import\s+['"]([^'"]*htmx[^'"]*)['"]\s*;?""",
        re.MULTILINE
    )

    # CDN script tag pattern
    CDN_PATTERN = re.compile(
        r"""<script[^>]*\bsrc\s*=\s*["']([^"']*htmx[^"']*)["'][^>]*>""",
        re.MULTILINE | re.IGNORECASE
    )

    # Version extraction from CDN URLs
    VERSION_PATTERN = re.compile(
        r"""htmx[^/]*?[/@](\d+\.\d+(?:\.\d+)?)""",
        re.IGNORECASE
    )

    # htmx JS API calls
    HTMX_API_PATTERN = re.compile(
        r"""htmx\.(ajax|process|on|off|trigger|find|findAll|closest|values|"""
        r"""remove|addClass|removeClass|toggleClass|takeClass|swap|"""
        r"""logAll|logger|parseInterval|createEventSource|createWebSocket)\s*\(""",
        re.MULTILINE
    )

    # htmx.config.* pattern
    HTMX_CONFIG_PATTERN = re.compile(
        r"""htmx\.config\.(\w+)\s*=\s*(?:['"]([^'"]*)['"]\s*|(\w+|[\d.]+))""",
        re.MULTILINE
    )

    # htmx.defineExtension (also tracked by extension_extractor)
    DEFINE_EXT_PATTERN = re.compile(
        r"""htmx\.defineExtension\(\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # _hyperscript integration
    HYPERSCRIPT_PATTERN = re.compile(
        r"""(?:<script[^>]*hyperscript[^>]*>|from\s+['"]hyperscript[^'"]*['"]|_\s*=\s*['"])""",
        re.MULTILINE | re.IGNORECASE
    )

    # Ecosystem integration detection patterns
    INTEGRATION_PATTERNS = {
        'alpine': (
            re.compile(r"""(?:x-data\s*=|alpinejs|Alpine\.)""", re.MULTILINE),
            'library',
        ),
        'hyperscript': (
            re.compile(r"""(?:hyperscript\.org|_hyperscript|_\s*=\s*['"])""", re.MULTILINE | re.IGNORECASE),
            'library',
        ),
        'django': (
            re.compile(r"""(?:\{%\s*(?:url|csrf_token|load|block|extends)|django)""", re.MULTILINE),
            'framework',
        ),
        'flask': (
            re.compile(r"""(?:\{\{\s*url_for\(|flask|jinja2)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'rails': (
            re.compile(r"""(?:<%=?\s*|\.erb\b|rails|turbo-frame)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'laravel': (
            re.compile(r"""(?:@csrf|@section|blade\.php|livewire)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'fastapi': (
            re.compile(r"""(?:fastapi|from\s+fastapi|jinja2|starlette)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'go_templ': (
            re.compile(r"""(?:templ\s+\w+|\.templ\b|echo\.Context|gin\.Context)""", re.MULTILINE),
            'framework',
        ),
        'aspnet': (
            re.compile(r"""(?:@Html\.|asp-|\.cshtml|\.razor|Blazor)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'spring': (
            re.compile(r"""(?:th:|thymeleaf|spring|\.html\.twig)""", re.MULTILINE | re.IGNORECASE),
            'framework',
        ),
        'phoenix': (
            re.compile(r"""(?:phx-|LiveView|\.heex\b|~H\[|<\.live)""", re.MULTILINE),
            'framework',
        ),
        'tailwind': (
            re.compile(r"""(?:tailwindcss|@tailwind\s|class="[^"]*(?:flex|grid|text-|bg-|p-\d|m-\d))""", re.MULTILINE),
            'library',
        ),
    }

    def extract(
        self, content: str, file_path: str = ""
    ) -> Tuple[List[HtmxImportInfo], List[HtmxIntegrationInfo], List[HtmxConfigInfo], List[HtmxCDNInfo]]:
        """Extract all HTMX API usage from source code.

        Args:
            content: Source code content (HTML or JS/TS).
            file_path: Path to the source file.

        Returns:
            Tuple of (imports, integrations, configs, cdns).
        """
        if not content or not content.strip():
            return [], [], [], []

        imports: List[HtmxImportInfo] = []
        integrations: List[HtmxIntegrationInfo] = []
        configs: List[HtmxConfigInfo] = []
        cdns: List[HtmxCDNInfo] = []

        lines = content.split('\n')

        # Extract ESM imports
        for line_idx, line in enumerate(lines, start=1):
            for match in self.ESM_IMPORT_PATTERN.finditer(line):
                default_import = match.group(1) or ""
                named_str = match.group(2) or ""
                source = match.group(3)

                named_imports = [n.strip().split(' as ')[0].strip()
                                 for n in named_str.split(',')
                                 if n.strip()] if named_str else []

                is_type = 'import type' in line

                imports.append(HtmxImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_idx,
                    import_type='esm',
                    default_import=default_import,
                    named_imports=named_imports,
                    is_type_import=is_type,
                ))

        # Extract CJS requires
        for line_idx, line in enumerate(lines, start=1):
            for match in self.CJS_REQUIRE_PATTERN.finditer(line):
                var_name = match.group(1)
                source = match.group(2)

                imports.append(HtmxImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_idx,
                    import_type='cjs',
                    default_import=var_name,
                ))

        # Extract side-effect imports
        for line_idx, line in enumerate(lines, start=1):
            for match in self.SIDE_EFFECT_IMPORT_PATTERN.finditer(line):
                source = match.group(1)
                # Skip if already captured as ESM import with bindings
                if any(i.source == source and i.line_number == line_idx for i in imports):
                    continue

                imports.append(HtmxImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_idx,
                    import_type='side_effect',
                ))

        # Extract CDN script tags
        for line_idx, line in enumerate(lines, start=1):
            for match in self.CDN_PATTERN.finditer(line):
                url = match.group(1)

                version = ""
                ver_match = self.VERSION_PATTERN.search(url)
                if ver_match:
                    version = ver_match.group(1)

                has_defer = 'defer' in line.lower()
                has_integrity = 'integrity=' in line.lower()

                # Check if this is an extension script
                is_extension = 'ext/' in url.lower() or 'extension' in url.lower()
                extension_name = ""
                if is_extension:
                    ext_match = re.search(r'ext/([a-zA-Z0-9\-]+)', url)
                    if ext_match:
                        extension_name = ext_match.group(1)

                cdns.append(HtmxCDNInfo(
                    url=url,
                    file=file_path,
                    line_number=line_idx,
                    version=version,
                    has_defer=has_defer,
                    has_integrity=has_integrity,
                    is_extension=is_extension,
                    extension_name=extension_name,
                ))

        # Extract htmx.config.* settings
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HTMX_CONFIG_PATTERN.finditer(line):
                config_key = match.group(1)
                config_value = match.group(2) if match.group(2) is not None else (match.group(3) or "")

                configs.append(HtmxConfigInfo(
                    config_key=config_key,
                    file=file_path,
                    line_number=line_idx,
                    config_value=config_value,
                ))

        # Detect ecosystem integrations
        seen_integrations: set = set()
        for name, (pattern, int_type) in self.INTEGRATION_PATTERNS.items():
            for line_idx, line in enumerate(lines, start=1):
                if name in seen_integrations:
                    break
                if pattern.search(line):
                    seen_integrations.add(name)
                    integrations.append(HtmxIntegrationInfo(
                        name=name,
                        file=file_path,
                        line_number=line_idx,
                        integration_type=int_type,
                        evidence=line.strip()[:100],
                    ))

        return imports, integrations, configs, cdns
