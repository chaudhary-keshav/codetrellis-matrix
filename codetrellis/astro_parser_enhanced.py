"""
EnhancedAstroParser v1.0 - Comprehensive Astro framework parser using all extractors.

This parser integrates all Astro extractors to provide complete parsing of
Astro source files (.astro, astro.config.*, content collection configs,
API endpoints, middleware).

Supports:
- Astro v1.x (Astro.glob, getStaticPaths, file-based routing, components)
- Astro v2.x (Content Collections with defineCollection/getCollection/getEntry,
               hybrid rendering, Zod schemas, type-safe markdown)
- Astro v3.x (Image optimization astro:assets, View Transitions astro:transitions,
               faster builds, HTML minification)
- Astro v4.x (i18n routing astro:i18n, Dev Toolbar, Audit, prefetch,
               incremental content caching)
- Astro v5.x (Content Layer, astro:env, stable Server Islands server:defer,
               stable Astro Actions astro:actions, simplified prerendering,
               astro:db stable, CSRF protection)

Key Patterns:
- .astro component files (frontmatter + template)
- --- fenced frontmatter with TypeScript
- Astro.props, Astro.slots, Astro.redirect, Astro.url, Astro.cookies
- client:load/idle/visible/media/only island hydration directives
- Content Collections (defineCollection, z schema, getCollection, getEntry)
- File-based routing (src/pages/, dynamic [param], [...rest])
- API endpoints (export function GET/POST/PUT/DELETE)
- Middleware (defineMiddleware, sequence)
- Integrations (@astrojs/react, @astrojs/vue, @astrojs/svelte, @astrojs/tailwind, etc.)

Ecosystem Detection (30+ patterns):
- Core: astro, astro:content, astro:assets, astro:transitions, astro:middleware
- UI Frameworks: @astrojs/react, @astrojs/vue, @astrojs/svelte, @astrojs/solid-js,
                 @astrojs/preact, @astrojs/lit, @astrojs/alpinejs
- Styling: @astrojs/tailwind, Tailwind CSS
- Content: @astrojs/mdx, @astrojs/markdoc, @astrojs/db, @astrojs/starlight
- Deployment: @astrojs/node, @astrojs/vercel, @astrojs/netlify, @astrojs/cloudflare
- Utility: @astrojs/sitemap, @astrojs/partytown, @astrojs/rss, @astrojs/check

Optional AST support via tree-sitter-html (for template parsing).
Optional LSP support via Astro Language Server (@astrojs/language-server).

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Astro extractors
from .extractors.astro import (
    AstroComponentExtractor, AstroComponentInfo, AstroSlotInfo, AstroExpressionInfo,
    AstroFrontmatterExtractor, AstroFrontmatterInfo, AstroDataFetchInfo, AstroCollectionInfo,
    AstroIslandExtractor, AstroIslandInfo,
    AstroRoutingExtractor, AstroRouteInfo, AstroEndpointInfo, AstroMiddlewareInfo,
    AstroApiExtractor, AstroImportInfo, AstroIntegrationInfo, AstroConfigInfo, AstroTypeInfo,
)


@dataclass
class AstroParseResult:
    """Complete parse result for a file with Astro usage."""
    file_path: str
    file_type: str = "astro"  # astro, ts, js, mjs, mdx

    # Components
    components: List[AstroComponentInfo] = field(default_factory=list)

    # Frontmatter
    frontmatter: Optional[AstroFrontmatterInfo] = None

    # Islands
    islands: List[AstroIslandInfo] = field(default_factory=list)

    # Routing
    routes: List[AstroRouteInfo] = field(default_factory=list)
    endpoints: List[AstroEndpointInfo] = field(default_factory=list)
    middleware: List[AstroMiddlewareInfo] = field(default_factory=list)

    # API
    imports: List[AstroImportInfo] = field(default_factory=list)
    integrations: List[AstroIntegrationInfo] = field(default_factory=list)
    config: Optional[AstroConfigInfo] = None
    types: List[AstroTypeInfo] = field(default_factory=list)

    # Collections
    collections: List[AstroCollectionInfo] = field(default_factory=list)
    data_fetches: List[AstroDataFetchInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    astro_version: str = ""  # v1, v2, v3, v4, v5

    # Flags
    has_typescript: bool = False
    has_content_collections: bool = False
    has_view_transitions: bool = False
    has_ssr: bool = False
    has_islands: bool = False


class EnhancedAstroParser:
    """
    Enhanced Astro parser that uses all extractors.

    This parser handles .astro component files, astro.config.* configuration,
    content collection configs, API endpoints, and middleware.

    Framework detection supports 30+ Astro ecosystem libraries across:
    - Core (Astro v1-v5)
    - UI Frameworks (React, Vue, Svelte, Solid, Preact, Lit, Alpine)
    - Styling (Tailwind, PostCSS)
    - Content (MDX, Markdoc, Starlight, Content Collections)
    - Deployment (Node, Vercel, Netlify, Cloudflare)
    - Utility (Sitemap, Partytown, RSS, Check)

    Optional AST: tree-sitter-html
    Optional LSP: Astro Language Server (@astrojs/language-server)
    """

    # ── Framework Detection Patterns ──────────────────────────────

    FRAMEWORK_PATTERNS = {
        # ── Core Astro ────────────────────────────────────────────
        'astro': re.compile(
            r"from\s+['\"]astro['/\"]|\.astro['\"]|---\s*\n.*?\n---|defineConfig",
            re.MULTILINE | re.DOTALL
        ),
        'astro-content': re.compile(
            r"from\s+['\"]astro:content['\"]",
            re.MULTILINE
        ),
        'astro-assets': re.compile(
            r"from\s+['\"]astro:assets['\"]",
            re.MULTILINE
        ),
        'astro-transitions': re.compile(
            r"from\s+['\"]astro:transitions['\"]|<ViewTransitions\b",
            re.MULTILINE
        ),
        'astro-middleware': re.compile(
            r"from\s+['\"]astro:middleware['\"]|defineMiddleware\(",
            re.MULTILINE
        ),
        'astro-i18n': re.compile(
            r"from\s+['\"]astro:i18n['\"]",
            re.MULTILINE
        ),
        'astro-env': re.compile(
            r"from\s+['\"]astro:env['\"]",
            re.MULTILINE
        ),
        'astro-db': re.compile(
            r"from\s+['\"]astro:db['\"]|@astrojs/db",
            re.MULTILINE
        ),
        'astro-actions': re.compile(
            r"from\s+['\"]astro:actions['\"]|defineAction\(",
            re.MULTILINE
        ),

        # ── UI Frameworks ─────────────────────────────────────────
        'astro-react': re.compile(
            r"from\s+['\"]@astrojs/react['\"]|"
            r"client:(?:load|idle|visible|media|only).*\.(?:jsx|tsx)['\"]",
            re.MULTILINE
        ),
        'astro-vue': re.compile(
            r"from\s+['\"]@astrojs/vue['\"]|"
            r"\.vue['\"].*client:|client:.*\.vue['\"]",
            re.MULTILINE
        ),
        'astro-svelte': re.compile(
            r"from\s+['\"]@astrojs/svelte['\"]|"
            r"\.svelte['\"].*client:|client:.*\.svelte['\"]",
            re.MULTILINE
        ),
        'astro-solid': re.compile(
            r"from\s+['\"]@astrojs/solid-js['\"]",
            re.MULTILINE
        ),
        'astro-preact': re.compile(
            r"from\s+['\"]@astrojs/preact['\"]",
            re.MULTILINE
        ),
        'astro-lit': re.compile(
            r"from\s+['\"]@astrojs/lit['\"]",
            re.MULTILINE
        ),
        'astro-alpinejs': re.compile(
            r"from\s+['\"]@astrojs/alpinejs['\"]",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'astro-tailwind': re.compile(
            r"from\s+['\"]@astrojs/tailwind['\"]|tailwindcss",
            re.MULTILINE
        ),

        # ── Content ───────────────────────────────────────────────
        'astro-mdx': re.compile(
            r"from\s+['\"]@astrojs/mdx['\"]|\.mdx['\"]",
            re.MULTILINE
        ),
        'astro-markdoc': re.compile(
            r"from\s+['\"]@astrojs/markdoc['\"]",
            re.MULTILINE
        ),
        'starlight': re.compile(
            r"from\s+['\"]@astrojs/starlight['/\"]",
            re.MULTILINE
        ),

        # ── Deployment ────────────────────────────────────────────
        'astro-node': re.compile(
            r"from\s+['\"]@astrojs/node['\"]",
            re.MULTILINE
        ),
        'astro-vercel': re.compile(
            r"from\s+['\"]@astrojs/vercel['/\"]",
            re.MULTILINE
        ),
        'astro-netlify': re.compile(
            r"from\s+['\"]@astrojs/netlify['/\"]",
            re.MULTILINE
        ),
        'astro-cloudflare': re.compile(
            r"from\s+['\"]@astrojs/cloudflare['/\"]",
            re.MULTILINE
        ),

        # ── Utility ───────────────────────────────────────────────
        'astro-sitemap': re.compile(
            r"from\s+['\"]@astrojs/sitemap['\"]",
            re.MULTILINE
        ),
        'astro-rss': re.compile(
            r"from\s+['\"]@astrojs/rss['\"]",
            re.MULTILINE
        ),
        'astro-partytown': re.compile(
            r"from\s+['\"]@astrojs/partytown['\"]",
            re.MULTILINE
        ),
    }

    # ── Feature Detection Patterns ────────────────────────────────

    FEATURE_PATTERNS = {
        'frontmatter': re.compile(r'^---\s*\n', re.MULTILINE),
        'astro_props': re.compile(r'Astro\.props\b', re.MULTILINE),
        'astro_slots': re.compile(r'Astro\.slots\b|<slot\b', re.MULTILINE),
        'astro_redirect': re.compile(r'Astro\.redirect\s*\(', re.MULTILINE),
        'astro_url': re.compile(r'Astro\.url\b', re.MULTILINE),
        'astro_cookies': re.compile(r'Astro\.cookies\b', re.MULTILINE),
        'astro_request': re.compile(r'Astro\.request\b', re.MULTILINE),
        'astro_params': re.compile(r'Astro\.params\b', re.MULTILINE),
        'astro_locals': re.compile(r'Astro\.locals\b', re.MULTILINE),
        'astro_glob': re.compile(r'Astro\.glob\s*\(', re.MULTILINE),
        'client_load': re.compile(r'client:load\b', re.MULTILINE),
        'client_idle': re.compile(r'client:idle\b', re.MULTILINE),
        'client_visible': re.compile(r'client:visible\b', re.MULTILINE),
        'client_media': re.compile(r'client:media\b', re.MULTILINE),
        'client_only': re.compile(r'client:only\b', re.MULTILINE),
        'server_defer': re.compile(r'server:defer\b', re.MULTILINE),
        'content_collections': re.compile(r'getCollection\s*\(|defineCollection\s*\(', re.MULTILINE),
        'view_transitions': re.compile(r'<ViewTransitions\b|transition:', re.MULTILINE),
        'image_component': re.compile(r'<Image\b|<Picture\b', re.MULTILINE),
        'get_static_paths': re.compile(r'getStaticPaths\b', re.MULTILINE),
        'api_endpoint': re.compile(r'export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|DELETE)\b', re.MULTILINE),
        'middleware': re.compile(r'defineMiddleware\(|export\s+const\s+onRequest\b', re.MULTILINE),
        'scoped_style': re.compile(r'<style\b', re.MULTILINE),
        'global_style': re.compile(r'<style\s+[^>]*is:global\b', re.MULTILINE),
        'set_html': re.compile(r'set:html\b', re.MULTILINE),
        'set_text': re.compile(r'set:text\b', re.MULTILINE),
        'class_list': re.compile(r'class:list\b', re.MULTILINE),
        'define_vars': re.compile(r'define:vars\b', re.MULTILINE),
        'is_inline': re.compile(r'is:inline\b', re.MULTILINE),
    }

    def __init__(self) -> None:
        """Initialize all Astro extractors."""
        self.component_extractor = AstroComponentExtractor()
        self.frontmatter_extractor = AstroFrontmatterExtractor()
        self.island_extractor = AstroIslandExtractor()
        self.routing_extractor = AstroRoutingExtractor()
        self.api_extractor = AstroApiExtractor()

    # File extension patterns for Astro-related files
    CONFIG_FILE_PATTERNS = {
        'astro.config.mjs', 'astro.config.ts', 'astro.config.js',
        'astro.config.cjs', 'astro.config.mts',
    }

    def is_astro_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Astro framework code.

        Returns True if the file is an .astro file, an Astro config file,
        or imports from Astro packages.
        """
        if file_path:
            import os
            name = os.path.basename(file_path)
            if file_path.endswith('.astro'):
                return True
            if name in self.CONFIG_FILE_PATTERNS:
                return True
            # Content collection config
            if 'content/config' in file_path:
                if 'defineCollection' in content or 'astro:content' in content:
                    return True

        # Check for Astro-specific imports or patterns
        astro_indicators = [
            'astro:content', 'astro:assets', 'astro:transitions',
            'astro:middleware', 'astro:i18n', 'astro:env', 'astro:db',
            'astro:actions',
            '@astrojs/', 'Astro.props', 'Astro.redirect', 'Astro.glob',
            'Astro.slots', 'Astro.url', 'Astro.cookies', 'Astro.params',
            'defineConfig', 'client:load', 'client:idle', 'client:visible',
            'client:only', 'client:media', 'server:defer',
        ]
        return any(ind in content for ind in astro_indicators)

    def parse(self, content: str, file_path: str = "") -> AstroParseResult:
        """
        Parse a source file for Astro patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            AstroParseResult with all extracted information
        """
        # Determine file type
        file_type = "astro"
        if file_path.endswith('.astro'):
            file_type = "astro"
        elif file_path.endswith('.ts') or file_path.endswith('.mts'):
            file_type = "ts"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"
        elif file_path.endswith('.mdx'):
            file_type = "mdx"

        result = AstroParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.astro_version = self._detect_version(content)

        # ── Component extraction ──────────────────────────────────
        if file_type == "astro":
            try:
                comp_result = self.component_extractor.extract(content, file_path)
                result.components = comp_result.get('components', [])
            except Exception:
                pass

        # ── Frontmatter extraction ────────────────────────────────
        try:
            fm_result = self.frontmatter_extractor.extract(content, file_path)
            result.frontmatter = fm_result.get('frontmatter')
            if result.frontmatter:
                result.has_typescript = result.frontmatter.has_typescript
                result.collections = result.frontmatter.collections
                result.data_fetches = result.frontmatter.data_fetches
                result.has_content_collections = result.frontmatter.is_collection_config or bool(result.frontmatter.collections)
        except Exception:
            pass

        # ── Island extraction ─────────────────────────────────────
        if file_type == "astro":
            try:
                island_result = self.island_extractor.extract(content, file_path)
                result.islands = island_result.get('islands', [])
                result.has_islands = bool(result.islands)
            except Exception:
                pass

        # ── Routing extraction ────────────────────────────────────
        try:
            route_result = self.routing_extractor.extract(content, file_path)
            result.routes = route_result.get('routes', [])
            result.endpoints = route_result.get('endpoints', [])
            result.middleware = route_result.get('middleware', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.config = api_result.get('config')
            result.types = api_result.get('types', [])

            # Merge detected frameworks/features from API extractor
            for fw in api_result.get('detected_frameworks', []):
                if fw not in result.detected_frameworks:
                    result.detected_frameworks.append(fw)
            for feat in api_result.get('detected_features', []):
                if feat not in result.detected_features:
                    result.detected_features.append(feat)

            # Version: take the highest
            api_version = api_result.get('astro_version', '')
            if api_version and self._version_compare(api_version, result.astro_version) > 0:
                result.astro_version = api_version
        except Exception:
            pass

        # ── Flags ─────────────────────────────────────────────────
        result.has_view_transitions = 'view_transitions' in result.detected_features
        result.has_ssr = 'ssr' in result.detected_features or any(
            e.rendering_mode == 'server' for r in result.routes for e in [r]
        )

        return result

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
        # v5 indicators
        v5_indicators = [
            'astro:env', 'astro:actions', 'server:defer',
            'defineAction(', 'astro:db',
        ]
        if any(ind in content for ind in v5_indicators):
            return "v5"

        # v4 indicators
        v4_indicators = [
            'astro:i18n', 'devToolbar', 'prefetch:',
            'getRelativeLocaleUrl', 'getAbsoluteLocaleUrl',
        ]
        if any(ind in content for ind in v4_indicators):
            return "v4"

        # v3 indicators
        v3_indicators = [
            'astro:assets', 'astro:transitions',
            '<ViewTransitions', '<Image', '<Picture',
        ]
        if any(ind in content for ind in v3_indicators):
            return "v3"

        # v2 indicators
        v2_indicators = [
            'astro:content', 'defineCollection', 'getCollection',
            'getEntry', "output: 'hybrid'", 'output: "hybrid"',
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators
        v1_indicators = [
            'Astro.glob', 'getStaticPaths', 'Astro.props',
        ]
        if any(ind in content for ind in v1_indicators):
            return "v1"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v1': 1, 'v2': 2, 'v3': 3, 'v4': 4, 'v5': 5}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
