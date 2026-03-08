"""
Remix API Extractor v1.0

Extracts API-level patterns from Remix / React Router v7 files:
- Import detection (@remix-run/*, react-router, @react-router/*)
- Adapter detection (express, cloudflare, vercel, netlify, architect, deno)
- Configuration (remix.config.js, vite.config.ts, react-router.config.ts)
- Entry files (entry.server.tsx, entry.client.tsx)
- Version detection (Remix v1.x, v2.x, React Router v7)
- TypeScript types (LoaderFunctionArgs, Route.LoaderArgs, MetaFunction, etc.)
- Ecosystem detection (Prisma, Drizzle, Supabase, Tailwind, etc.)
- Session/Cookie utilities
- Resource routes

Supports:
- Remix v1.x (@remix-run/react, @remix-run/node, remix.config.js)
- Remix v2.x (@remix-run/react, Vite plugin, flat routes)
- React Router v7 (react-router, @react-router/dev, routes.ts)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RemixImportInfo:
    """Information about a Remix/RR7 import."""
    source: str = ""  # Package name
    named_imports: List[str] = field(default_factory=list)
    has_default_import: bool = False
    default_import_name: str = ""
    file_path: str = ""
    line_number: int = 0
    import_category: str = ""  # core, adapter, routing, data, ui, types


@dataclass
class RemixAdapterInfo:
    """Information about a Remix adapter/runtime."""
    name: str = ""  # express, cloudflare-workers, vercel, netlify, etc.
    package: str = ""
    file_path: str = ""
    line_number: int = 0
    adapter_type: str = ""  # node, edge, serverless


@dataclass
class RemixConfigInfo:
    """Information about Remix/RR7 configuration."""
    file_path: str = ""
    config_type: str = ""  # remix.config.js, vite.config.ts, react-router.config.ts

    # Build config
    has_server_build_target: bool = False
    server_build_target: str = ""
    has_app_directory: bool = False
    app_directory: str = ""

    # Feature flags
    has_v2_route_convention: bool = False
    has_v2_meta: bool = False
    has_v2_error_boundary: bool = False
    has_future_flags: bool = False
    future_flags: List[str] = field(default_factory=list)

    # Vite plugin config
    has_vite_plugin: bool = False
    has_ssr: bool = False
    has_spa_mode: bool = False
    has_basename: bool = False

    # Pre-rendering
    has_prerender: bool = False


@dataclass
class RemixTypeInfo:
    """Information about TypeScript type usage."""
    type_name: str = ""
    file_path: str = ""
    line_number: int = 0
    type_category: str = ""  # loader, action, meta, component, utility


class RemixApiExtractor:
    """Extracts API-level patterns from Remix/RR7 files."""

    # ── Import Detection Patterns ─────────────────────────────────

    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:(\w+)\s*,?\s*)?"
        r"(?:\{\s*([^}]+)\}\s*)?"
        r"from\s+['\"]([^'\"]+)['\"]|"
        r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))",
        re.MULTILINE
    )

    # Remix/RR7 package prefixes
    REMIX_PACKAGES = {
        '@remix-run/react',
        '@remix-run/node',
        '@remix-run/server-runtime',
        '@remix-run/cloudflare',
        '@remix-run/deno',
        '@remix-run/express',
        '@remix-run/architect',
        '@remix-run/netlify',
        '@remix-run/vercel',
        '@remix-run/css-bundle',
        '@remix-run/dev',
        '@remix-run/serve',
        '@remix-run/testing',
        '@remix-run/fs-routes',
        'react-router',
        'react-router-dom',
        '@react-router/dev',
        '@react-router/express',
        '@react-router/architect',
        '@react-router/cloudflare',
        '@react-router/fs-routes',
        '@react-router/node',
        '@react-router/serve',
    }

    # Import categorization
    IMPORT_CATEGORIES = {
        '@remix-run/react': 'core',
        '@remix-run/node': 'adapter',
        '@remix-run/server-runtime': 'core',
        '@remix-run/cloudflare': 'adapter',
        '@remix-run/deno': 'adapter',
        '@remix-run/express': 'adapter',
        '@remix-run/architect': 'adapter',
        '@remix-run/netlify': 'adapter',
        '@remix-run/vercel': 'adapter',
        '@remix-run/css-bundle': 'ui',
        '@remix-run/dev': 'core',
        '@remix-run/serve': 'adapter',
        '@remix-run/testing': 'testing',
        '@remix-run/fs-routes': 'routing',
        'react-router': 'core',
        'react-router-dom': 'core',
        '@react-router/dev': 'core',
        '@react-router/express': 'adapter',
        '@react-router/architect': 'adapter',
        '@react-router/cloudflare': 'adapter',
        '@react-router/fs-routes': 'routing',
        '@react-router/node': 'adapter',
        '@react-router/serve': 'adapter',
    }

    # ── Adapter Detection ─────────────────────────────────────────

    ADAPTER_PATTERNS = {
        'express': re.compile(
            r"from\s+['\"]@remix-run/express['\"]|from\s+['\"]@react-router/express['\"]|"
            r"createRequestHandler.*express",
            re.MULTILINE
        ),
        'cloudflare-workers': re.compile(
            r"from\s+['\"]@remix-run/cloudflare['\"]|from\s+['\"]@react-router/cloudflare['\"]",
            re.MULTILINE
        ),
        'vercel': re.compile(
            r"from\s+['\"]@remix-run/vercel['\"]|@vercel/remix",
            re.MULTILINE
        ),
        'netlify': re.compile(
            r"from\s+['\"]@remix-run/netlify['\"]|@netlify/remix-adapter",
            re.MULTILINE
        ),
        'architect': re.compile(
            r"from\s+['\"]@remix-run/architect['\"]|from\s+['\"]@react-router/architect['\"]",
            re.MULTILINE
        ),
        'deno': re.compile(
            r"from\s+['\"]@remix-run/deno['\"]",
            re.MULTILINE
        ),
        'node': re.compile(
            r"from\s+['\"]@remix-run/node['\"]|from\s+['\"]@react-router/node['\"]",
            re.MULTILINE
        ),
    }

    ADAPTER_TYPES = {
        'express': 'node',
        'node': 'node',
        'cloudflare-workers': 'edge',
        'vercel': 'serverless',
        'netlify': 'serverless',
        'architect': 'serverless',
        'deno': 'edge',
    }

    # ── Config Detection ──────────────────────────────────────────

    CONFIG_FILES = {
        'remix.config.js', 'remix.config.mjs', 'remix.config.ts',
        'vite.config.ts', 'vite.config.js', 'vite.config.mjs',
        'react-router.config.ts', 'react-router.config.js',
    }

    VITE_REMIX_PLUGIN = re.compile(
        r'remix\s*\(|@remix-run/dev.*vitePlugin|unstable_vitePlugin',
        re.MULTILINE
    )

    RR7_VITE_PLUGIN = re.compile(
        r'reactRouter\s*\(|@react-router/dev.*vitePlugin',
        re.MULTILINE
    )

    FUTURE_FLAGS = re.compile(
        r'future\s*:\s*\{([^}]+)\}',
        re.MULTILINE | re.DOTALL
    )

    FLAG_NAMES = re.compile(r'(\w+)\s*:\s*true', re.MULTILINE)

    V2_ROUTE_CONVENTION = re.compile(r'v2_routeConvention\s*:\s*true', re.MULTILINE)
    V2_META = re.compile(r'v2_meta\s*:\s*true', re.MULTILINE)
    V2_ERROR_BOUNDARY = re.compile(r'v2_errorBoundary\s*:\s*true', re.MULTILINE)

    SSR_CONFIG = re.compile(r'ssr\s*:\s*(true|false)', re.MULTILINE)
    SPA_MODE = re.compile(r'ssr\s*:\s*false|spa\s*:\s*true', re.MULTILINE)
    BASENAME_CONFIG = re.compile(r'basename\s*:\s*["\']([^"\']+)["\']', re.MULTILINE)
    PRERENDER_CONFIG = re.compile(r'prerender\s*[=:]', re.MULTILINE)

    APP_DIRECTORY = re.compile(r'appDirectory\s*:\s*["\']([^"\']+)["\']', re.MULTILINE)
    SERVER_BUILD_TARGET = re.compile(r'serverBuildTarget\s*:\s*["\']([^"\']+)["\']', re.MULTILINE)

    # ── Entry Files ───────────────────────────────────────────────

    ENTRY_SERVER = re.compile(
        r'handleRequest|renderToPipeableStream|renderToReadableStream|'
        r'RemixServer|ServerRouter',
        re.MULTILINE
    )

    ENTRY_CLIENT = re.compile(
        r'hydrateRoot|HydratedRouter|RemixBrowser|startTransition',
        re.MULTILINE
    )

    # ── Session / Cookie Utilities ────────────────────────────────

    SESSION_PATTERN = re.compile(
        r'createCookieSessionStorage|createSessionStorage|'
        r'createMemorySessionStorage|createFileSessionStorage|'
        r'createCloudflareKVSessionStorage|createWorkersKVSessionStorage|'
        r'getSession|commitSession|destroySession',
        re.MULTILINE
    )

    COOKIE_PATTERN = re.compile(
        r'createCookie\s*\(|cookie\.\w+',
        re.MULTILINE
    )

    # ── TypeScript Type Detection ─────────────────────────────────

    REMIX_TYPES = {
        'LoaderFunction': ('loader', 'v1'),
        'LoaderFunctionArgs': ('loader', 'v2'),
        'ActionFunction': ('action', 'v1'),
        'ActionFunctionArgs': ('action', 'v2'),
        'MetaFunction': ('meta', 'v2'),
        'V2_MetaFunction': ('meta', 'v2'),
        'LinksFunction': ('meta', 'all'),
        'HeadersFunction': ('meta', 'all'),
        'ShouldRevalidateFunction': ('utility', 'v2'),
        'ErrorBoundaryComponent': ('component', 'v2'),
        'Route.LoaderArgs': ('loader', 'rr7'),
        'Route.ActionArgs': ('action', 'rr7'),
        'Route.MetaArgs': ('meta', 'rr7'),
        'Route.ComponentProps': ('component', 'rr7'),
        'Route.HydrateFallbackProps': ('component', 'rr7'),
        'Route.ErrorBoundaryProps': ('component', 'rr7'),
    }

    TYPE_PATTERN = re.compile(
        r'(?:' + '|'.join(re.escape(t) for t in REMIX_TYPES.keys()) + r')\b',
        re.MULTILINE
    )

    # ── Version Detection Indicators ──────────────────────────────

    V1_INDICATORS = [
        'remix.config.js', '@remix-run/serve', 'CatchBoundary',
        'useCatch', 'V1_Meta',
    ]

    # These must be checked with word boundary to avoid matching v2 variants
    V1_TYPE_INDICATORS = re.compile(
        r'\bLoaderFunction\b(?!Args)|'
        r'\bActionFunction\b(?!Args)',
        re.MULTILINE
    )

    V2_INDICATORS = [
        '@remix-run/dev', 'vitePlugin', 'unstable_vitePlugin',
        'v2_routeConvention', 'v2_meta', 'v2_errorBoundary',
        '@remix-run/fs-routes', 'V2_MetaFunction',
        'useRouteError', 'isRouteErrorResponse',
        'LoaderFunctionArgs', 'ActionFunctionArgs',
    ]

    RR7_INDICATORS = [
        'react-router', '@react-router/dev', '@react-router/express',
        '@react-router/fs-routes', '@react-router/node',
        'Route.LoaderArgs', 'Route.ActionArgs', 'Route.MetaArgs',
        'Route.ComponentProps', 'routes.ts', 'react-router.config',
        'loaderData', 'clientMiddleware', 'middleware',
        'ServerRouter', 'HydratedRouter',
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API-level information from Remix/RR7 source.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with imports, adapters, config, types, version info
        """
        imports: List[RemixImportInfo] = []
        adapters: List[RemixAdapterInfo] = []
        config: Optional[RemixConfigInfo] = None
        types: List[RemixTypeInfo] = []

        # Extract imports
        imports = self._extract_imports(content, file_path)

        # Detect adapters
        adapters = self._detect_adapters(content, file_path)

        # Extract config (if config file)
        config = self._extract_config(content, file_path)

        # Extract TypeScript types
        types = self._extract_types(content, file_path)

        # Detect version
        version = self._detect_version(content, file_path)

        # Detect ecosystem
        detected_frameworks = self._detect_ecosystem(content)

        # Feature detection
        detected_features = self._detect_features(content, file_path)

        return {
            'imports': imports,
            'adapters': adapters,
            'config': config,
            'types': types,
            'remix_version': version,
            'detected_frameworks': detected_frameworks,
            'detected_features': detected_features,
            'has_session': bool(self.SESSION_PATTERN.search(content)),
            'has_cookies': bool(self.COOKIE_PATTERN.search(content)),
            'is_entry_server': bool(self.ENTRY_SERVER.search(content)) and 'entry.server' in (file_path or ''),
            'is_entry_client': bool(self.ENTRY_CLIENT.search(content)) and 'entry.client' in (file_path or ''),
        }

    def _extract_imports(self, content: str, file_path: str) -> List[RemixImportInfo]:
        """Extract Remix/RR7 import statements."""
        imports: List[RemixImportInfo] = []

        for match in self.IMPORT_PATTERN.finditer(content):
            default_name = match.group(1) or ""
            named_str = match.group(2) or ""
            source = match.group(3) or match.group(4) or ""

            # Only track Remix/RR7 packages
            if not any(source.startswith(pkg) or source == pkg for pkg in self.REMIX_PACKAGES):
                continue

            named_imports = [n.strip().split(' as ')[0].strip()
                            for n in named_str.split(',') if n.strip()] if named_str else []

            line_num = content[:match.start()].count('\n') + 1

            # Determine category
            category = "core"
            for pkg, cat in self.IMPORT_CATEGORIES.items():
                if source.startswith(pkg) or source == pkg:
                    category = cat
                    break

            imports.append(RemixImportInfo(
                source=source,
                named_imports=named_imports,
                has_default_import=bool(default_name),
                default_import_name=default_name,
                file_path=file_path,
                line_number=line_num,
                import_category=category,
            ))

        return imports

    def _detect_adapters(self, content: str, file_path: str) -> List[RemixAdapterInfo]:
        """Detect Remix adapters/runtimes."""
        adapters: List[RemixAdapterInfo] = []

        for name, pattern in self.ADAPTER_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                adapters.append(RemixAdapterInfo(
                    name=name,
                    package=f"@remix-run/{name}" if 'remix-run' in match.group(0) else f"@react-router/{name}",
                    file_path=file_path,
                    line_number=line_num,
                    adapter_type=self.ADAPTER_TYPES.get(name, 'node'),
                ))

        return adapters

    def _extract_config(self, content: str, file_path: str) -> Optional[RemixConfigInfo]:
        """Extract configuration from config files."""
        import os
        basename = os.path.basename(file_path) if file_path else ""

        if basename not in self.CONFIG_FILES:
            return None

        config = RemixConfigInfo(file_path=file_path)

        if 'remix.config' in basename:
            config.config_type = "remix.config"
        elif 'react-router.config' in basename:
            config.config_type = "react-router.config"
        elif 'vite.config' in basename:
            # Only if has remix/rr plugin
            if self.VITE_REMIX_PLUGIN.search(content) or self.RR7_VITE_PLUGIN.search(content):
                config.config_type = "vite.config"
            else:
                return None

        # Vite plugin detection
        config.has_vite_plugin = bool(
            self.VITE_REMIX_PLUGIN.search(content) or self.RR7_VITE_PLUGIN.search(content)
        )

        # Future flags
        ff_match = self.FUTURE_FLAGS.search(content)
        if ff_match:
            config.has_future_flags = True
            flags = self.FLAG_NAMES.findall(ff_match.group(1))
            config.future_flags = flags

        config.has_v2_route_convention = bool(self.V2_ROUTE_CONVENTION.search(content))
        config.has_v2_meta = bool(self.V2_META.search(content))
        config.has_v2_error_boundary = bool(self.V2_ERROR_BOUNDARY.search(content))

        # SSR / SPA
        config.has_ssr = bool(self.SSR_CONFIG.search(content))
        config.has_spa_mode = bool(self.SPA_MODE.search(content))

        # Basename
        basename_match = self.BASENAME_CONFIG.search(content)
        if basename_match:
            config.has_basename = True

        # App directory
        app_dir_match = self.APP_DIRECTORY.search(content)
        if app_dir_match:
            config.has_app_directory = True
            config.app_directory = app_dir_match.group(1)

        # Server build target
        target_match = self.SERVER_BUILD_TARGET.search(content)
        if target_match:
            config.has_server_build_target = True
            config.server_build_target = target_match.group(1)

        # Pre-rendering
        config.has_prerender = bool(self.PRERENDER_CONFIG.search(content))

        return config

    def _extract_types(self, content: str, file_path: str) -> List[RemixTypeInfo]:
        """Extract TypeScript type usage."""
        types: List[RemixTypeInfo] = []
        seen = set()

        for match in self.TYPE_PATTERN.finditer(content):
            type_name = match.group(0)
            if type_name in seen:
                continue
            seen.add(type_name)

            line_num = content[:match.start()].count('\n') + 1
            category, _ = self.REMIX_TYPES.get(type_name, ('utility', 'all'))

            types.append(RemixTypeInfo(
                type_name=type_name,
                file_path=file_path,
                line_number=line_num,
                type_category=category,
            ))

        return types

    def _detect_version(self, content: str, file_path: str = "") -> str:
        """
        Detect Remix/RR7 version from content and file path.

        Returns 'v1', 'v2', 'rr7', or '' (unknown).
        """
        # RR7 indicators (check first - most specific)
        if any(ind in content for ind in self.RR7_INDICATORS):
            return "rr7"
        if file_path and any(ind in file_path for ind in ['routes.ts', 'react-router.config']):
            return "rr7"

        # v2 indicators
        if any(ind in content for ind in self.V2_INDICATORS):
            return "v2"

        # v1 indicators
        if any(ind in content for ind in self.V1_INDICATORS):
            return "v1"
        if self.V1_TYPE_INDICATORS.search(content):
            return "v1"

        # Default: check for @remix-run/react (could be v1 or v2)
        if '@remix-run/' in content:
            return "v2"

        return ""

    def _detect_ecosystem(self, content: str) -> List[str]:
        """Detect Remix ecosystem frameworks/libraries."""
        detected: List[str] = []

        ecosystem_patterns = {
            'remix': re.compile(r"@remix-run/|remix\s*\(", re.MULTILINE),
            'react-router': re.compile(r"from\s+['\"]react-router['\"]|@react-router/", re.MULTILINE),
            'prisma': re.compile(r"@prisma/client|PrismaClient|prisma\.", re.MULTILINE),
            'drizzle': re.compile(r"drizzle-orm|drizzle\(|pgTable", re.MULTILINE),
            'supabase': re.compile(r"@supabase/|supabase\.", re.MULTILINE),
            'tailwind': re.compile(r"tailwindcss|tailwind\.config", re.MULTILINE),
            'shadcn': re.compile(r"@/components/ui|shadcn", re.MULTILINE),
            'zod': re.compile(r"from\s+['\"]zod['\"]|z\.\w+", re.MULTILINE),
            'conform': re.compile(r"@conform-to/|useForm\b", re.MULTILINE),
            'remix-auth': re.compile(r"remix-auth|Authenticator", re.MULTILINE),
            'remix-validated-form': re.compile(r"remix-validated-form", re.MULTILINE),
            'remix-toast': re.compile(r"remix-toast", re.MULTILINE),
            'remix-utils': re.compile(r"remix-utils", re.MULTILINE),
            'remix-i18next': re.compile(r"remix-i18next", re.MULTILINE),
            'remix-flat-routes': re.compile(r"remix-flat-routes", re.MULTILINE),
            'epic-stack': re.compile(r"epic-stack|@epic-web/", re.MULTILINE),
            'fly-io': re.compile(r"fly\.toml|fly\.io|@flydotio/", re.MULTILINE),
            'sentry': re.compile(r"@sentry/remix|Sentry", re.MULTILINE),
        }

        for name, pattern in ecosystem_patterns.items():
            if pattern.search(content):
                detected.append(name)

        return detected

    def _detect_features(self, content: str, file_path: str = "") -> List[str]:
        """Detect which Remix/RR7 features are used."""
        features: List[str] = []

        feature_checks = {
            'loader': re.compile(r'export\s+(?:async\s+)?function\s+loader\b', re.MULTILINE),
            'action': re.compile(r'export\s+(?:async\s+)?function\s+action\b', re.MULTILINE),
            'client_loader': re.compile(r'export\s+(?:async\s+)?function\s+clientLoader\b', re.MULTILINE),
            'client_action': re.compile(r'export\s+(?:async\s+)?function\s+clientAction\b', re.MULTILINE),
            'meta': re.compile(r'export\s+(?:const|function)\s+meta\b', re.MULTILINE),
            'links': re.compile(r'export\s+(?:const|function)\s+links\b', re.MULTILINE),
            'headers': re.compile(r'export\s+(?:const|function)\s+headers\b', re.MULTILINE),
            'error_boundary': re.compile(r'export\s+(?:function|const)\s+ErrorBoundary\b', re.MULTILINE),
            'catch_boundary': re.compile(r'export\s+(?:function|const)\s+CatchBoundary\b', re.MULTILINE),
            'handle': re.compile(r'export\s+(?:const|let)\s+handle\b', re.MULTILINE),
            'should_revalidate': re.compile(r'export\s+(?:function|const)\s+shouldRevalidate\b', re.MULTILINE),
            'hydrate_fallback': re.compile(r'export\s+(?:function|const)\s+HydrateFallback\b', re.MULTILINE),
            'middleware': re.compile(r'export\s+(?:const|let)\s+middleware\s*=', re.MULTILINE),
            'client_middleware': re.compile(r'export\s+(?:const|let)\s+clientMiddleware\s*=', re.MULTILINE),
            'defer': re.compile(r'\bdefer\s*\(', re.MULTILINE),
            'streaming': re.compile(r'<Await\b|renderToPipeableStream|renderToReadableStream', re.MULTILINE),
            'session': re.compile(r'createCookieSessionStorage|createSessionStorage|getSession', re.MULTILINE),
            'cookie': re.compile(r'createCookie\s*\(', re.MULTILINE),
            'form': re.compile(r'<Form\b', re.MULTILINE),
            'fetcher': re.compile(r'useFetcher\b', re.MULTILINE),
            'navigation': re.compile(r'useNavigation\s*\(', re.MULTILINE),
            'outlet': re.compile(r'<Outlet\b', re.MULTILINE),
            'link_prefetch': re.compile(r'<Link\b[^>]*prefetch', re.MULTILINE),
            'resource_route': re.compile(r'(?:export\s+(?:async\s+)?function\s+loader\b)(?!.*export\s+default)', re.DOTALL),
            'optimistic_ui': re.compile(r'navigation\.state|isSubmitting|useOptimistic', re.MULTILINE),
            'spa_mode': re.compile(r'ssr\s*:\s*false|spa\s*:\s*true', re.MULTILINE),
            'prerender': re.compile(r'prerender\s*[=:]', re.MULTILINE),
        }

        for name, pattern in feature_checks.items():
            if pattern.search(content):
                features.append(name)

        return features
