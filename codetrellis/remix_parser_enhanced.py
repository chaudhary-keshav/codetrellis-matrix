"""
EnhancedRemixParser v1.0 - Comprehensive Remix / React Router v7 parser using all extractors.

This parser integrates all Remix extractors to provide complete parsing of
Remix and React Router v7 (framework mode) application files. It runs as a
supplementary layer on top of the JavaScript, TypeScript, and React parsers,
extracting Remix-specific semantics.

Supports:
- Remix v1.x (remix.config.js, @remix-run/react, @remix-run/node, CatchBoundary,
               nested routes, loader, action, meta object, links, useLoaderData,
               useActionData, useCatch, LoaderFunction, ActionFunction,
               createCookieSessionStorage, json, redirect)
- Remix v2.x (Vite plugin, flat routes, v2_routeConvention, v2_meta, v2_errorBoundary,
               @remix-run/fs-routes, ErrorBoundary with useRouteError/isRouteErrorResponse,
               V2_MetaFunction, defer + Await/Suspense streaming, unstable_compileAssets,
               future flags, serverBuildTarget removal)
- React Router v7 (react-router, @react-router/dev/routes, routes.ts config,
                    Route.LoaderArgs/ActionArgs/MetaArgs/ComponentProps typegen,
                    loaderData/actionData as component props, middleware/clientMiddleware,
                    ServerRouter/HydratedRouter, SPA mode, pre-rendering,
                    @react-router/express|cloudflare|architect|node|serve adapters)

Remix-specific extraction:
- Routes: routes.ts config (route/index/layout/prefix), file-based routing
          (flat routes, nested directories), dynamic segments (:param, *splat),
          optional segments (:param?), root.tsx, nested Outlets
- Loaders: loader (server), clientLoader (browser), useLoaderData, json(),
           defer() + Await + Suspense streaming, redirect(), typed loader data,
           cache headers, data sources (Prisma, Drizzle, Supabase, fetch)
- Actions: action (server), clientAction (browser), <Form>, useFetcher,
           useSubmit, useNavigation, request.formData(), intent pattern,
           optimistic UI, validation (Zod, Yup, Valibot)
- Meta: meta function (v1 object/v2 array), links function, headers function,
        handle export, ErrorBoundary, CatchBoundary (v1), HydrateFallback,
        shouldRevalidate, middleware, clientMiddleware
- API: @remix-run/* and @react-router/* imports, adapter detection
       (Express, Cloudflare, Vercel, Netlify, Architect, Deno, Node),
       configuration (remix.config/vite.config/react-router.config),
       entry.server/entry.client files, session/cookie management,
       TypeScript types, version detection, ecosystem detection

Framework detection (30+ Remix ecosystem patterns):
- Core: @remix-run/react, @remix-run/node, @remix-run/dev, react-router
- Adapters: @remix-run/express, @remix-run/cloudflare, @react-router/express
- Data: Prisma, Drizzle, Supabase, Turso, Convex
- Auth: remix-auth, Clerk, Auth.js, Lucia
- Forms: Conform, remix-validated-form, Zod, Valibot
- Styling: Tailwind CSS, shadcn/ui, CSS Modules, Vanilla Extract
- Testing: Playwright, Cypress, Vitest, React Testing Library
- Deployment: Fly.io, Vercel, Netlify, Cloudflare Pages, Railway
- Community: remix-utils, remix-i18next, remix-flat-routes, Epic Stack

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Remix extractors
from .extractors.remix import (
    RemixRouteExtractor, RemixRouteInfo, RemixLayoutInfo, RemixOutletInfo,
    RemixLoaderExtractor, RemixLoaderInfo, RemixClientLoaderInfo, RemixFetcherInfo,
    RemixActionExtractor, RemixActionInfo, RemixClientActionInfo, RemixFormInfo,
    RemixMetaExtractor, RemixMetaInfo, RemixLinksInfo, RemixHeadersInfo, RemixErrorBoundaryInfo,
    RemixApiExtractor, RemixImportInfo, RemixAdapterInfo, RemixConfigInfo, RemixTypeInfo,
)


@dataclass
class RemixParseResult:
    """Complete parse result for a file with Remix/RR7 usage."""
    file_path: str
    file_type: str = "route"  # route, layout, index, root, config, entry, resource

    # Routes
    routes: List[RemixRouteInfo] = field(default_factory=list)
    layouts: List[RemixLayoutInfo] = field(default_factory=list)
    outlets: List[RemixOutletInfo] = field(default_factory=list)

    # Loaders
    loaders: List[RemixLoaderInfo] = field(default_factory=list)
    client_loaders: List[RemixClientLoaderInfo] = field(default_factory=list)
    fetchers: List[RemixFetcherInfo] = field(default_factory=list)

    # Actions
    actions: List[RemixActionInfo] = field(default_factory=list)
    client_actions: List[RemixClientActionInfo] = field(default_factory=list)
    forms: List[RemixFormInfo] = field(default_factory=list)

    # Meta/Head
    meta: Optional[RemixMetaInfo] = None
    links: Optional[RemixLinksInfo] = None
    headers: Optional[RemixHeadersInfo] = None
    error_boundaries: List[RemixErrorBoundaryInfo] = field(default_factory=list)

    # API
    imports: List[RemixImportInfo] = field(default_factory=list)
    adapters: List[RemixAdapterInfo] = field(default_factory=list)
    config: Optional[RemixConfigInfo] = None
    types: List[RemixTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    remix_version: str = ""  # v1, v2, rr7

    # Flags
    has_typescript: bool = False
    has_streaming: bool = False
    has_session: bool = False
    has_cookies: bool = False
    has_optimistic_ui: bool = False
    is_entry_server: bool = False
    is_entry_client: bool = False
    is_resource_route: bool = False


class EnhancedRemixParser:
    """
    Enhanced Remix parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript/React parsers
    when Remix or React Router v7 framework is detected. It extracts Remix-specific
    semantics that the language/React parsers cannot capture.

    Framework detection supports 30+ Remix ecosystem libraries across:
    - Core (Remix, React Router)
    - Adapters (Express, Cloudflare, Vercel, Netlify, Architect, Deno)
    - Data (Prisma, Drizzle, Supabase)
    - Auth (remix-auth, Clerk)
    - Forms (Conform, remix-validated-form)
    - Styling (Tailwind, shadcn/ui)
    - Deployment (Fly.io, Vercel, Netlify, Cloudflare)

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # ── Framework Detection Patterns ──────────────────────────────

    FRAMEWORK_PATTERNS = {
        # ── Core Remix ────────────────────────────────────────────
        'remix': re.compile(
            r"from\s+['\"]@remix-run/|remix\.config\.|"
            r"createRequestHandler|RemixServer|RemixBrowser",
            re.MULTILINE
        ),
        'react-router': re.compile(
            r"from\s+['\"]react-router['\"]|from\s+['\"]react-router-dom['\"]|"
            r"from\s+['\"]@react-router/",
            re.MULTILINE
        ),
        'remix-react': re.compile(
            r"from\s+['\"]@remix-run/react['\"]|"
            r"useLoaderData|useActionData|useFetcher|useNavigation|useMatches",
            re.MULTILINE
        ),
        'remix-node': re.compile(
            r"from\s+['\"]@remix-run/node['\"]|from\s+['\"]@react-router/node['\"]",
            re.MULTILINE
        ),

        # ── Adapters ─────────────────────────────────────────────
        'remix-express': re.compile(
            r"from\s+['\"]@remix-run/express['\"]|from\s+['\"]@react-router/express['\"]",
            re.MULTILINE
        ),
        'remix-cloudflare': re.compile(
            r"from\s+['\"]@remix-run/cloudflare['\"]|from\s+['\"]@react-router/cloudflare['\"]",
            re.MULTILINE
        ),
        'remix-vercel': re.compile(
            r"from\s+['\"]@remix-run/vercel['\"]|@vercel/remix",
            re.MULTILINE
        ),
        'remix-netlify': re.compile(
            r"from\s+['\"]@remix-run/netlify['\"]|@netlify/remix-adapter",
            re.MULTILINE
        ),
        'remix-architect': re.compile(
            r"from\s+['\"]@remix-run/architect['\"]|from\s+['\"]@react-router/architect['\"]",
            re.MULTILINE
        ),
        'remix-deno': re.compile(
            r"from\s+['\"]@remix-run/deno['\"]",
            re.MULTILINE
        ),

        # ── Data ──────────────────────────────────────────────────
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|prisma\.\w+",
            re.MULTILINE
        ),
        'drizzle': re.compile(
            r"from\s+['\"]drizzle-orm['\"]|drizzle\(|pgTable|sqliteTable",
            re.MULTILINE
        ),
        'supabase': re.compile(
            r"from\s+['\"]@supabase/|supabase\.",
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'remix-auth': re.compile(
            r"from\s+['\"]remix-auth['\"]|Authenticator",
            re.MULTILINE
        ),
        'clerk': re.compile(
            r"from\s+['\"]@clerk/remix['\"]|from\s+['\"]@clerk/react-router['\"]",
            re.MULTILINE
        ),

        # ── Forms / Validation ────────────────────────────────────
        'conform': re.compile(
            r"from\s+['\"]@conform-to/|useForm\(",
            re.MULTILINE
        ),
        'remix-validated-form': re.compile(
            r"from\s+['\"]remix-validated-form['\"]",
            re.MULTILINE
        ),
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|z\.\w+",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'tailwind': re.compile(
            r"tailwindcss|tailwind\.config",
            re.MULTILINE
        ),
        'shadcn': re.compile(
            r"@/components/ui|shadcn",
            re.MULTILINE
        ),

        # ── Community ─────────────────────────────────────────────
        'remix-utils': re.compile(
            r"from\s+['\"]remix-utils['/\"]",
            re.MULTILINE
        ),
        'remix-i18next': re.compile(
            r"from\s+['\"]remix-i18next['\"]",
            re.MULTILINE
        ),
        'remix-flat-routes': re.compile(
            r"from\s+['\"]remix-flat-routes['\"]",
            re.MULTILINE
        ),
        'epic-stack': re.compile(
            r"@epic-web/|epic-stack",
            re.MULTILINE
        ),

        # ── Monitoring ────────────────────────────────────────────
        'sentry': re.compile(
            r"from\s+['\"]@sentry/remix['\"]|Sentry\.init",
            re.MULTILINE
        ),

        # ── Deployment ────────────────────────────────────────────
        'fly-io': re.compile(
            r"fly\.toml|fly\.io|@flydotio/",
            re.MULTILINE
        ),
    }

    # ── Feature Detection Patterns ────────────────────────────────

    FEATURE_PATTERNS = {
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
        'json': re.compile(r'\bjson\s*\(', re.MULTILINE),
        'redirect': re.compile(r'\bredirect\s*\(', re.MULTILINE),
        'form': re.compile(r'<Form\b', re.MULTILINE),
        'fetcher': re.compile(r'useFetcher\b', re.MULTILINE),
        'navigation': re.compile(r'useNavigation\s*\(', re.MULTILINE),
        'outlet': re.compile(r'<Outlet\b', re.MULTILINE),
        'streaming': re.compile(r'<Await\b|renderToPipeableStream', re.MULTILINE),
        'session': re.compile(r'createCookieSessionStorage|getSession', re.MULTILINE),
        'cookie': re.compile(r'createCookie\s*\(', re.MULTILINE),
        'use_loader_data': re.compile(r'useLoaderData\b', re.MULTILINE),
        'use_action_data': re.compile(r'useActionData\b', re.MULTILINE),
        'use_submit': re.compile(r'useSubmit\b', re.MULTILINE),
        'use_matches': re.compile(r'useMatches\b', re.MULTILINE),
        'use_route_error': re.compile(r'useRouteError\b', re.MULTILINE),
        'link_prefetch': re.compile(r'<Link[^>]*prefetch', re.MULTILINE),
        'scroll_restoration': re.compile(r'<ScrollRestoration', re.MULTILINE),
        'live_reload': re.compile(r'<LiveReload|<Scripts', re.MULTILINE),
    }

    # ── Config File Patterns ──────────────────────────────────────

    CONFIG_FILE_PATTERNS = {
        'remix.config.js', 'remix.config.mjs', 'remix.config.ts',
        'react-router.config.ts', 'react-router.config.js',
    }

    def __init__(self) -> None:
        """Initialize all Remix extractors."""
        self.route_extractor = RemixRouteExtractor()
        self.loader_extractor = RemixLoaderExtractor()
        self.action_extractor = RemixActionExtractor()
        self.meta_extractor = RemixMetaExtractor()
        self.api_extractor = RemixApiExtractor()

    def is_remix_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Remix / React Router v7 framework code.

        Returns True if the file imports from @remix-run/* or react-router/*,
        or is a Remix config file, or contains Remix-specific patterns.
        """
        if file_path:
            import os
            name = os.path.basename(file_path)
            # Config files
            if name in self.CONFIG_FILE_PATTERNS:
                return True
            # Entry files
            if 'entry.server' in name or 'entry.client' in name:
                return True
            # routes.ts
            if name == 'routes.ts' or name == 'routes.js':
                if '@react-router/' in content or '@remix-run/' in content:
                    return True
            # Vite config with remix plugin
            if 'vite.config' in name:
                if '@remix-run/dev' in content or '@react-router/dev' in content or 'remix(' in content or 'reactRouter(' in content:
                    return True

        # Check for Remix/RR7-specific imports or patterns
        remix_indicators = [
            '@remix-run/', '@react-router/',
            'useLoaderData', 'useActionData',
            'useFetcher', 'useNavigation',
            'RemixServer', 'RemixBrowser',
            'ServerRouter', 'HydratedRouter',
            'createRequestHandler',
            'Route.LoaderArgs', 'Route.ActionArgs',
            'LoaderFunctionArgs', 'ActionFunctionArgs',
        ]
        return any(ind in content for ind in remix_indicators)

    def parse(self, content: str, file_path: str = "") -> RemixParseResult:
        """
        Parse a source file for Remix / React Router v7 patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            RemixParseResult with all extracted information
        """
        # Determine file type
        file_type = self._detect_file_type(content, file_path)
        result = RemixParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.remix_version = self._detect_version(content, file_path)

        # ── Route extraction ──────────────────────────────────────
        try:
            route_result = self.route_extractor.extract(content, file_path)
            result.routes = route_result.get('routes', [])
            result.layouts = route_result.get('layouts', [])
            result.outlets = route_result.get('outlets', [])
        except Exception:
            pass

        # ── Loader extraction ─────────────────────────────────────
        try:
            loader_result = self.loader_extractor.extract(content, file_path)
            result.loaders = loader_result.get('loaders', [])
            result.client_loaders = loader_result.get('client_loaders', [])
            result.fetchers = loader_result.get('fetchers', [])
            result.has_streaming = loader_result.get('has_await_component', False)
        except Exception:
            pass

        # ── Action extraction ─────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(content, file_path)
            result.actions = action_result.get('actions', [])
            result.client_actions = action_result.get('client_actions', [])
            result.forms = action_result.get('forms', [])
            result.has_optimistic_ui = action_result.get('has_optimistic_ui', False)
        except Exception:
            pass

        # ── Meta extraction ───────────────────────────────────────
        try:
            meta_result = self.meta_extractor.extract(content, file_path)
            result.meta = meta_result.get('meta')
            result.links = meta_result.get('links')
            result.headers = meta_result.get('headers')
            result.error_boundaries = meta_result.get('error_boundaries', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.adapters = api_result.get('adapters', [])
            result.config = api_result.get('config')
            result.types = api_result.get('types', [])
            result.has_session = api_result.get('has_session', False)
            result.has_cookies = api_result.get('has_cookies', False)
            result.is_entry_server = api_result.get('is_entry_server', False)
            result.is_entry_client = api_result.get('is_entry_client', False)

            # Merge frameworks/features from API extractor
            for fw in api_result.get('detected_frameworks', []):
                if fw not in result.detected_frameworks:
                    result.detected_frameworks.append(fw)
            for feat in api_result.get('detected_features', []):
                if feat not in result.detected_features:
                    result.detected_features.append(feat)

            # Version: take most specific
            api_version = api_result.get('remix_version', '')
            if api_version:
                result.remix_version = self._highest_version(result.remix_version, api_version)
        except Exception:
            pass

        # ── Flags ─────────────────────────────────────────────────
        result.has_typescript = file_path.endswith('.tsx') or file_path.endswith('.ts') if file_path else False
        result.has_streaming = result.has_streaming or 'streaming' in result.detected_features
        result.is_resource_route = self._is_resource_route(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Remix ecosystem frameworks are used."""
        detected: List[str] = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Remix features are used."""
        detected: List[str] = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str, file_path: str = "") -> str:
        """
        Detect Remix / React Router v7 version from content.

        Returns 'v1', 'v2', 'rr7', or '' (unknown).
        """
        # RR7 indicators (check first)
        rr7_indicators = [
            '@react-router/', 'react-router.config',
            'Route.LoaderArgs', 'Route.ActionArgs', 'Route.MetaArgs',
            'Route.ComponentProps', 'ServerRouter', 'HydratedRouter',
            'clientMiddleware', './+types/',
        ]
        if any(ind in content for ind in rr7_indicators):
            return "rr7"
        if file_path and ('routes.ts' in file_path and '@react-router/' in content):
            return "rr7"

        # v2 indicators
        v2_indicators = [
            'unstable_vitePlugin', 'vitePlugin',
            'v2_routeConvention', 'v2_meta', 'v2_errorBoundary',
            'V2_MetaFunction', '@remix-run/fs-routes',
            'useRouteError', 'isRouteErrorResponse',
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators
        v1_indicators = [
            'CatchBoundary', 'useCatch',
            'LoaderFunction', 'ActionFunction',
            'V1_Meta',
        ]
        if any(ind in content for ind in v1_indicators):
            return "v1"

        # Default for @remix-run packages
        if '@remix-run/' in content:
            return "v2"

        return ""

    def _detect_file_type(self, content: str, file_path: str) -> str:
        """Detect the type of Remix file."""
        if not file_path:
            return "route"

        import os
        basename = os.path.basename(file_path).lower()

        if 'root' in basename and 'config' not in basename:
            return "root"
        if 'entry.server' in basename:
            return "entry"
        if 'entry.client' in basename:
            return "entry"
        if 'routes.ts' in basename or 'routes.js' in basename:
            return "config"
        if 'remix.config' in basename or 'react-router.config' in basename:
            return "config"
        if 'vite.config' in basename:
            return "config"
        if '_layout' in basename or basename.startswith('__'):
            return "layout"
        if '_index' in basename:
            return "index"

        # Resource route: has loader but no default export
        if self._is_resource_route(content):
            return "resource"

        return "route"

    @staticmethod
    def _is_resource_route(content: str) -> bool:
        """Check if this is a resource route (loader/action without component)."""
        has_loader = bool(re.search(r'export\s+(?:async\s+)?function\s+loader\b', content))
        has_default = bool(re.search(r'export\s+default\s+', content))
        return has_loader and not has_default

    @staticmethod
    def _highest_version(v1: str, v2: str) -> str:
        """Return the highest/most specific version."""
        order = {'': 0, 'v1': 1, 'v2': 2, 'rr7': 3}
        if order.get(v1, 0) >= order.get(v2, 0):
            return v1
        return v2
