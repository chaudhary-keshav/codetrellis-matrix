"""
Astro API Extractor v1.0

Extracts API and ecosystem information from Astro files:
- Imports from astro:* virtual modules (astro:content, astro:assets, astro:transitions,
  astro:middleware, astro:i18n, astro:env, astro:db)
- Official integration detection (@astrojs/react, @astrojs/vue, @astrojs/svelte,
  @astrojs/solid-js, @astrojs/preact, @astrojs/lit, @astrojs/alpinejs,
  @astrojs/tailwind, @astrojs/mdx, @astrojs/image, @astrojs/sitemap,
  @astrojs/partytown, @astrojs/db, @astrojs/node, @astrojs/vercel,
  @astrojs/netlify, @astrojs/cloudflare, @astrojs/deno)
- astro.config.mjs/ts detection and parsing
- TypeScript types (CollectionEntry, InferGetStaticPropsType, etc.)
- Astro version detection (v1, v2, v3, v4, v5)
- Third-party integration detection (Starlight, Keystatic, etc.)

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AstroImportInfo:
    """Information about an import in an Astro file."""
    source: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    is_type_import: bool = False
    is_default_import: bool = False
    is_virtual_module: bool = False  # astro:* imports


@dataclass
class AstroIntegrationInfo:
    """Information about an Astro integration."""
    name: str = ""
    package: str = ""
    category: str = ""  # ui_framework, styling, content, deployment, utility
    line_number: int = 0


@dataclass
class AstroConfigInfo:
    """Information about astro.config.mjs/ts."""
    file_path: str = ""
    line_number: int = 0
    output_mode: str = ""  # static, server, hybrid
    integrations: List[str] = field(default_factory=list)
    adapter: str = ""  # node, vercel, netlify, cloudflare, deno
    has_i18n: bool = False
    has_view_transitions: bool = False
    has_image: bool = False
    has_experimental: bool = False
    has_vite_config: bool = False
    has_markdown_config: bool = False
    has_redirects: bool = False
    has_prefetch: bool = False
    site_url: str = ""
    base_path: str = ""


@dataclass
class AstroTypeInfo:
    """Information about TypeScript types used from Astro."""
    type_name: str = ""
    source: str = ""
    line_number: int = 0


class AstroApiExtractor:
    """Extracts API and ecosystem information from Astro files."""

    # Virtual module imports
    VIRTUAL_MODULE_PATTERN = re.compile(
        r"(?:import|from)\s+['\"]astro:(\w+)['\"]",
        re.MULTILINE
    )

    # Standard import patterns
    IMPORT_PATTERN = re.compile(
        r"import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]|"
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Astro config detection
    CONFIG_DEFINE = re.compile(
        r'defineConfig\s*\(\s*\{',
        re.MULTILINE
    )

    # Output mode
    OUTPUT_MODE = re.compile(
        r"output\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # Site URL
    SITE_URL = re.compile(
        r"site\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Base path
    BASE_PATH = re.compile(
        r"base\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Adapter detection
    ADAPTER_PATTERN = re.compile(
        r"adapter\s*:\s*(?:node|vercel|netlify|cloudflare|deno)\s*\(|"
        r"from\s+['\"]@astrojs/(node|vercel|netlify|cloudflare|deno)['\"]",
        re.MULTILINE
    )

    # Integration patterns
    INTEGRATION_PATTERN = re.compile(
        r"from\s+['\"](@astrojs/\w+)['\"]|"
        r"from\s+['\"](@astrojs/\w[\w-]*)['\"]",
        re.MULTILINE
    )

    # i18n config
    I18N_CONFIG = re.compile(
        r"i18n\s*:\s*\{",
        re.MULTILINE
    )

    # Experimental features
    EXPERIMENTAL = re.compile(
        r"experimental\s*:\s*\{",
        re.MULTILINE
    )

    # Vite config
    VITE_CONFIG = re.compile(
        r"vite\s*:\s*\{",
        re.MULTILINE
    )

    # Markdown config
    MARKDOWN_CONFIG = re.compile(
        r"markdown\s*:\s*\{",
        re.MULTILINE
    )

    # Redirects
    REDIRECTS_CONFIG = re.compile(
        r"redirects\s*:\s*\{",
        re.MULTILINE
    )

    # Prefetch
    PREFETCH_CONFIG = re.compile(
        r"prefetch\s*:\s*(?:true|\{)",
        re.MULTILINE
    )

    # Image config
    IMAGE_CONFIG = re.compile(
        r"image\s*:\s*\{",
        re.MULTILINE
    )

    # Known integrations with categories
    KNOWN_INTEGRATIONS: Dict[str, str] = {
        # UI Frameworks
        "@astrojs/react": "ui_framework",
        "@astrojs/vue": "ui_framework",
        "@astrojs/svelte": "ui_framework",
        "@astrojs/solid-js": "ui_framework",
        "@astrojs/preact": "ui_framework",
        "@astrojs/lit": "ui_framework",
        "@astrojs/alpinejs": "ui_framework",
        # Styling
        "@astrojs/tailwind": "styling",
        # Content
        "@astrojs/mdx": "content",
        "@astrojs/markdoc": "content",
        "@astrojs/db": "content",
        # Deployment
        "@astrojs/node": "deployment",
        "@astrojs/vercel": "deployment",
        "@astrojs/netlify": "deployment",
        "@astrojs/cloudflare": "deployment",
        "@astrojs/deno": "deployment",
        # Utility
        "@astrojs/sitemap": "utility",
        "@astrojs/partytown": "utility",
        "@astrojs/check": "utility",
        "@astrojs/rss": "utility",
        # Third-party
        "@astrojs/starlight": "content",
        "astro-i18next": "utility",
        "astro-icon": "utility",
        "astro-seo": "utility",
        "astro-compress": "utility",
    }

    # Astro TypeScript types
    ASTRO_TYPES = re.compile(
        r"(?:CollectionEntry|InferGetStaticPropsType|InferGetStaticParamsType|"
        r"GetStaticPaths|APIRoute|APIContext|MiddlewareHandler|"
        r"MiddlewareNext|AstroGlobal|AstroUserConfig|AstroIntegration|"
        r"ImageMetadata|GetImageResult|AstroComponentFactory|"
        r"ContentCollectionKey|DataCollectionKey|ValidContentEntrySlug)\b",
        re.MULTILINE
    )

    # Framework detection patterns for version detection
    FRAMEWORK_PATTERNS = {
        'astro': re.compile(
            r"from\s+['\"]astro['/\"]|from\s+['\"]astro:(?:content|assets|transitions|middleware|i18n|env|db)['\"]",
            re.MULTILINE
        ),
        'astro-config': re.compile(
            r"from\s+['\"]astro/config['\"]|defineConfig",
            re.MULTILINE
        ),
        'starlight': re.compile(
            r"from\s+['\"]@astrojs/starlight['/\"]",
            re.MULTILINE
        ),
        'keystatic': re.compile(
            r"from\s+['\"]@keystatic/(?:astro|core)['/\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'content_collections': re.compile(r"from\s+['\"]astro:content['\"]", re.MULTILINE),
        'image_optimization': re.compile(r"from\s+['\"]astro:assets['\"]|<Image\b|<Picture\b", re.MULTILINE),
        'view_transitions': re.compile(r"from\s+['\"]astro:transitions['\"]|<ViewTransitions\b|transition:", re.MULTILINE),
        'middleware': re.compile(r"from\s+['\"]astro:middleware['\"]|defineMiddleware\(", re.MULTILINE),
        'i18n': re.compile(r"from\s+['\"]astro:i18n['\"]|i18n\s*:", re.MULTILINE),
        'env': re.compile(r"from\s+['\"]astro:env['\"]", re.MULTILINE),
        'db': re.compile(r"from\s+['\"]astro:db['\"]|@astrojs/db", re.MULTILINE),
        'server_islands': re.compile(r"server:defer\b", re.MULTILINE),
        'actions': re.compile(r"from\s+['\"]astro:actions['\"]|defineAction\(", re.MULTILINE),
        'client_directives': re.compile(r"client:(?:load|idle|visible|media|only)\b", re.MULTILINE),
        'slots': re.compile(r"<slot\b|Astro\.slots", re.MULTILINE),
        'scoped_styles': re.compile(r"<style\b(?!.*is:global)", re.MULTILINE),
        'global_styles': re.compile(r"<style\s+[^>]*is:global\b", re.MULTILINE),
        'ssr': re.compile(r"output\s*:\s*['\"]server['\"]|export\s+const\s+prerender\s*=\s*false", re.MULTILINE),
        'ssg': re.compile(r"output\s*:\s*['\"]static['\"]|getStaticPaths\b", re.MULTILINE),
        'hybrid': re.compile(r"output\s*:\s*['\"]hybrid['\"]", re.MULTILINE),
        'mdx': re.compile(r"\.mdx['\"]|@astrojs/mdx", re.MULTILINE),
        'rss': re.compile(r"@astrojs/rss|getRssString\(", re.MULTILINE),
        'api_routes': re.compile(r"export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|DELETE|PATCH|ALL)\b", re.MULTILINE),
        'astro_props': re.compile(r"Astro\.props\b", re.MULTILINE),
        'set_html': re.compile(r"set:html\b", re.MULTILINE),
        'class_list': re.compile(r"class:list\b", re.MULTILINE),
        'define_vars': re.compile(r"define:vars\b", re.MULTILINE),
    }

    # Version detection
    VERSION_INDICATORS = {
        'v5': [
            'astro:env',           # v5.0
            'astro:actions',       # v5.0 (stable)
            'server:defer',        # v5.0 server islands
            'astro:db',            # v5.0 (stable)
        ],
        'v4': [
            'astro:i18n',          # v4.0
            'ViewTransitions',     # v3.0 but standard in v4
            'prefetch',            # v4.0
            'devToolbar',          # v4.0
            "output: 'hybrid'",    # v2.0 but stable v4
        ],
        'v3': [
            'astro:assets',        # v3.0
            'astro:transitions',   # v3.0
            '<Image',              # v3.0
            '<Picture',            # v3.0
            'image()',             # v3.0
        ],
        'v2': [
            'astro:content',       # v2.0
            'defineCollection',    # v2.0
            'getCollection',       # v2.0
            "output: 'hybrid'",    # v2.0
        ],
        'v1': [
            'Astro.glob',          # v1.0
            'getStaticPaths',      # v1.0
        ],
    }

    def __init__(self) -> None:
        """Initialize API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API and ecosystem information from an Astro file.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with API information
        """
        imports: List[AstroImportInfo] = []
        integrations: List[AstroIntegrationInfo] = []
        types: List[AstroTypeInfo] = []
        config: Optional[AstroConfigInfo] = None

        # Extract imports
        self._extract_imports(content, imports)

        # Extract integrations
        self._extract_integrations(content, integrations)

        # Extract types
        self._extract_types(content, types)

        # Extract config (for astro.config.* files)
        if self._is_config_file(file_path):
            config = self._extract_config(content, file_path)

        # Detect frameworks and features
        detected_frameworks = self._detect_frameworks(content)
        detected_features = self._detect_features(content)
        version = self._detect_version(content)

        return {
            "imports": imports,
            "integrations": integrations,
            "types": types,
            "config": config,
            "detected_frameworks": detected_frameworks,
            "detected_features": detected_features,
            "astro_version": version,
            "has_provider": False,  # Astro doesn't use providers
        }

    def _extract_imports(self, content: str, imports: List[AstroImportInfo]) -> None:
        """Extract import statements."""
        # Virtual module imports (astro:*)
        for m in self.VIRTUAL_MODULE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            virtual_name = m.group(1)
            imports.append(AstroImportInfo(
                source=f"astro:{virtual_name}",
                line_number=line,
                is_virtual_module=True,
            ))

        # Standard imports
        for m in self.IMPORT_PATTERN.finditer(content):
            named = m.group(1) or ""
            source = m.group(2) or m.group(4) or ""
            default_name = m.group(3) or ""
            is_type = 'import type' in content[max(0, m.start() - 15):m.start() + 15]

            if not source:
                continue

            line = content[:m.start()].count('\n') + 1

            named_list = []
            if named:
                named_list = [n.strip() for n in named.split(',') if n.strip()]
            elif default_name:
                named_list = [default_name]

            imports.append(AstroImportInfo(
                source=source,
                line_number=line,
                named_imports=named_list[:15],
                is_type_import=is_type,
                is_default_import=bool(default_name),
                is_virtual_module=source.startswith('astro:'),
            ))

    def _extract_integrations(self, content: str, integrations: List[AstroIntegrationInfo]) -> None:
        """Extract Astro integration usage."""
        for m in self.INTEGRATION_PATTERN.finditer(content):
            pkg = m.group(1) or m.group(2) or ""
            if not pkg:
                continue

            category = self.KNOWN_INTEGRATIONS.get(pkg, "utility")
            line = content[:m.start()].count('\n') + 1

            # Avoid duplicates
            if any(i.package == pkg for i in integrations):
                continue

            integrations.append(AstroIntegrationInfo(
                name=pkg.split('/')[-1] if '/' in pkg else pkg,
                package=pkg,
                category=category,
                line_number=line,
            ))

        # Also check for third-party integrations
        for pkg, category in self.KNOWN_INTEGRATIONS.items():
            if not pkg.startswith('@astrojs/'):
                if pkg in content:
                    if not any(i.package == pkg for i in integrations):
                        integrations.append(AstroIntegrationInfo(
                            name=pkg,
                            package=pkg,
                            category=category,
                        ))

    def _extract_types(self, content: str, types: List[AstroTypeInfo]) -> None:
        """Extract Astro TypeScript type usage."""
        for m in self.ASTRO_TYPES.finditer(content):
            type_name = m.group(0)
            line = content[:m.start()].count('\n') + 1
            # Avoid duplicates
            if not any(t.type_name == type_name for t in types):
                types.append(AstroTypeInfo(
                    type_name=type_name,
                    source="astro",
                    line_number=line,
                ))

    def _is_config_file(self, file_path: str) -> bool:
        """Check if a file is an Astro config file."""
        if not file_path:
            return False
        import os
        name = os.path.basename(file_path)
        return name.startswith('astro.config.')

    def _extract_config(self, content: str, file_path: str) -> AstroConfigInfo:
        """Extract configuration from astro.config.* file."""
        config = AstroConfigInfo(file_path=file_path, line_number=1)

        # Output mode
        output_match = self.OUTPUT_MODE.search(content)
        if output_match:
            config.output_mode = output_match.group(1)

        # Site URL
        site_match = self.SITE_URL.search(content)
        if site_match:
            config.site_url = site_match.group(1)

        # Base path
        base_match = self.BASE_PATH.search(content)
        if base_match:
            config.base_path = base_match.group(1)

        # Adapter
        adapter_match = self.ADAPTER_PATTERN.search(content)
        if adapter_match:
            config.adapter = adapter_match.group(1) or ""
            # Infer from import
            for adapter_name in ['node', 'vercel', 'netlify', 'cloudflare', 'deno']:
                if f"@astrojs/{adapter_name}" in content:
                    config.adapter = adapter_name
                    break

        # Integrations (list names)
        for m in self.INTEGRATION_PATTERN.finditer(content):
            pkg = m.group(1) or m.group(2) or ""
            if pkg and pkg not in config.integrations:
                config.integrations.append(pkg)

        # Flags
        config.has_i18n = bool(self.I18N_CONFIG.search(content))
        config.has_experimental = bool(self.EXPERIMENTAL.search(content))
        config.has_vite_config = bool(self.VITE_CONFIG.search(content))
        config.has_markdown_config = bool(self.MARKDOWN_CONFIG.search(content))
        config.has_redirects = bool(self.REDIRECTS_CONFIG.search(content))
        config.has_prefetch = bool(self.PREFETCH_CONFIG.search(content))
        config.has_image = bool(self.IMAGE_CONFIG.search(content))

        return config

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Astro ecosystem frameworks are used."""
        detected: List[str] = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Astro features are used."""
        detected: List[str] = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Astro version based on API usage patterns.

        Returns 'v5', 'v4', 'v3', 'v2', 'v1', or '' (unknown).
        """
        for version in ['v5', 'v4', 'v3', 'v2', 'v1']:
            indicators = self.VERSION_INDICATORS[version]
            for indicator in indicators:
                if indicator in content:
                    return version
        return ""
