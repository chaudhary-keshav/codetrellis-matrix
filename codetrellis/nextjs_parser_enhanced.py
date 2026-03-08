"""
EnhancedNextJSParser v1.0 - Comprehensive Next.js parser using all extractors.

This parser integrates all Next.js extractors to provide complete parsing of
Next.js application files. It runs as a supplementary layer on top of the
JavaScript, TypeScript, and React parsers, extracting Next.js-specific semantics.

Supports:
- Next.js 9.x (pages/ directory, API routes, getServerSideProps/getStaticProps)
- Next.js 10.x (Image optimization, i18n routing, next/image, next/link improvements)
- Next.js 11.x (Script optimization, next/script, Conformance)
- Next.js 12.x (Middleware, Edge Runtime, React Server Components alpha, SWC compiler)
- Next.js 13.x (App Router, Layouts, Server Components, Route Handlers,
                 Turbopack alpha, next/font, Metadata API)
- Next.js 14.x (Server Actions stable, Partial Prerendering preview,
                 Metadata improvements, Turbopack improvements)
- Next.js 15.x (Turbopack stable, async request APIs, cacheLife/cacheTag,
                 React 19 support, improved form handling, after() API,
                 next.config.ts support)

Next.js-specific extraction:
- Pages Router: pages/, getServerSideProps, getStaticProps, getStaticPaths,
                getInitialProps, _app.tsx, _document.tsx, _error.tsx, custom 404/500
- App Router: app/, page.tsx, layout.tsx, loading.tsx, error.tsx, not-found.tsx,
              template.tsx, route.tsx, default.tsx, global-error.tsx, opengraph-image.tsx
- API Routes: pages/api/*, Route Handlers (app/*/route.ts), Edge API routes
- Server Actions: 'use server' directive, inline actions, form actions,
                   revalidatePath/revalidateTag, redirect()
- Middleware: middleware.ts, request matchers, NextResponse transforms
- Data Fetching: fetch() with cache/revalidate/tags, React cache(),
                  unstable_cache(), generateStaticParams, dynamic rendering
- Configuration: next.config.js/mjs/ts, images, i18n, redirects, rewrites,
                  headers, webpack/turbopack, experimental features
- Metadata: export metadata, generateMetadata, viewport, generateViewport
- Segment Config: dynamic, revalidate, runtime, fetchCache, preferredRegion

Framework detection (40+ Next.js ecosystem patterns):
- Core: next, next/server, next/navigation, next/headers, next/cache
- Routing: next/router (Pages Router), next/navigation (App Router)
- UI: next/image, next/link, next/script, next/font
- Auth: NextAuth.js / Auth.js, Clerk, Supabase Auth, Lucia
- CMS: Contentful, Sanity, Strapi, Payload, Directus
- Database: Prisma, Drizzle, Supabase, PlanetScale, Neon, Vercel Postgres
- Deployment: Vercel, Netlify, AWS Amplify, Cloudflare Pages
- Analytics: Vercel Analytics, Vercel Speed Insights, PostHog, Plausible
- Styling: Tailwind CSS, CSS Modules, styled-components, Emotion, Sass
- Testing: Playwright, Cypress, Jest, Vitest, React Testing Library
- State: Zustand, Jotai, Redux Toolkit, Recoil, TanStack Query
- API: tRPC, GraphQL, REST
- Email: React Email, Resend
- Monitoring: Sentry, DataDog, LogRocket

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Next.js extractors
from .extractors.nextjs import (
    NextPageExtractor, NextPageInfo, NextLayoutInfo, NextLoadingInfo,
    NextErrorInfo, NextTemplateInfo, NextMetadataInfo, NextSegmentConfigInfo,
    NextRouteHandlerExtractor, NextRouteHandlerInfo, NextAPIRouteInfo,
    NextMiddlewareInfo, NextRewriteInfo, NextRedirectInfo,
    NextConfigExtractor, NextConfigInfo, NextImageConfigInfo,
    NextI18nConfigInfo, NextExperimentalInfo,
    NextServerActionExtractor, NextServerActionInfo, NextFormActionInfo,
    NextDataFetchingExtractor, NextFetchCallInfo, NextCacheInfo,
    NextStaticParamsInfo,
)


@dataclass
class NextJSParseResult:
    """Complete parse result for a Next.js file."""
    file_path: str
    file_type: str = "page"  # page, layout, loading, error, template, route, api, middleware, config, action, component

    # Pages
    pages: List[NextPageInfo] = field(default_factory=list)
    layouts: List[NextLayoutInfo] = field(default_factory=list)
    loadings: List[NextLoadingInfo] = field(default_factory=list)
    errors: List[NextErrorInfo] = field(default_factory=list)
    templates: List[NextTemplateInfo] = field(default_factory=list)

    # Metadata
    metadata: List[NextMetadataInfo] = field(default_factory=list)
    segment_configs: List[NextSegmentConfigInfo] = field(default_factory=list)

    # Route Handlers
    route_handlers: List[NextRouteHandlerInfo] = field(default_factory=list)
    api_routes: List[NextAPIRouteInfo] = field(default_factory=list)

    # Middleware
    middleware: List[NextMiddlewareInfo] = field(default_factory=list)

    # Server Actions
    server_actions: List[NextServerActionInfo] = field(default_factory=list)
    form_actions: List[NextFormActionInfo] = field(default_factory=list)

    # Data Fetching
    fetch_calls: List[NextFetchCallInfo] = field(default_factory=list)
    caches: List[NextCacheInfo] = field(default_factory=list)
    static_params: List[NextStaticParamsInfo] = field(default_factory=list)

    # Config
    config: Optional[NextConfigInfo] = None
    image_config: Optional[NextImageConfigInfo] = None
    i18n_config: Optional[NextI18nConfigInfo] = None
    experimental: Optional[NextExperimentalInfo] = None

    # Aggregate signals
    has_dynamic_signals: bool = False
    has_parallel_fetch: bool = False
    suspense_count: int = 0

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    nextjs_version: str = ""  # Detected minimum Next.js version
    router_type: str = ""  # pages, app, hybrid
    is_server_component: bool = False
    is_client_component: bool = False


class EnhancedNextJSParser:
    """
    Enhanced Next.js parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript/React parsers
    when Next.js framework is detected. It extracts Next.js-specific semantics
    that the language/React parsers cannot capture.

    Framework detection supports 40+ Next.js ecosystem libraries across:
    - Core (next, next/server, next/navigation)
    - UI (next/image, next/link, next/script, next/font)
    - Auth (NextAuth, Clerk, Supabase Auth, Lucia)
    - CMS (Contentful, Sanity, Strapi, Payload)
    - Database (Prisma, Drizzle, Supabase, PlanetScale, Neon)
    - Deployment (Vercel, Netlify, AWS Amplify)
    - Analytics (Vercel Analytics, PostHog, Plausible)
    - Testing (Playwright, Cypress, Vitest)

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Next.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Next.js ──────────────────────────────────────────
        'next': re.compile(
            r"from\s+['\"]next['/\"]|require\(['\"]next['/\"]\)|"
            r"NextPage|NextApiRequest|NextApiResponse|NextResponse|NextRequest",
            re.MULTILINE
        ),
        'next-server': re.compile(
            r"from\s+['\"]next/server['\"]|NextResponse|NextRequest|NextMiddleware",
            re.MULTILINE
        ),
        'next-navigation': re.compile(
            r"from\s+['\"]next/navigation['\"]|"
            r"useRouter|usePathname|useSearchParams|useParams|redirect|notFound",
            re.MULTILINE
        ),
        'next-headers': re.compile(
            r"from\s+['\"]next/headers['\"]|cookies\(\)|headers\(\)|draftMode\(\)",
            re.MULTILINE
        ),
        'next-cache': re.compile(
            r"from\s+['\"]next/cache['\"]|revalidatePath|revalidateTag|unstable_cache",
            re.MULTILINE
        ),

        # ── Routing ───────────────────────────────────────────────
        'next-router-pages': re.compile(
            r"from\s+['\"]next/router['\"]|useRouter\(\).*asPath|push\(.*as:",
            re.MULTILINE
        ),
        'next-link': re.compile(
            r"from\s+['\"]next/link['\"]|<Link\s+href",
            re.MULTILINE
        ),

        # ── UI Components ────────────────────────────────────────
        'next-image': re.compile(
            r"from\s+['\"]next/image['\"]|<Image\s+(?:src|alt)",
            re.MULTILINE
        ),
        'next-script': re.compile(
            r"from\s+['\"]next/script['\"]|<Script\s+",
            re.MULTILINE
        ),
        'next-font': re.compile(
            r"from\s+['\"]next/font/(?:google|local)['\"]",
            re.MULTILINE
        ),
        'next-dynamic': re.compile(
            r"from\s+['\"]next/dynamic['\"]|dynamic\s*\(\s*\(\s*\)\s*=>",
            re.MULTILINE
        ),
        'next-og': re.compile(
            r"from\s+['\"]next/og['\"]|ImageResponse",
            re.MULTILINE
        ),

        # ── Auth ─────────────────────────────────────────────────
        'nextauth': re.compile(
            r"from\s+['\"]next-auth['/\"]|from\s+['\"]@auth/|"
            r"NextAuth|getServerSession|signIn|signOut|useSession|"
            r"SessionProvider|authOptions",
            re.MULTILINE
        ),
        'clerk': re.compile(
            r"from\s+['\"]@clerk/nextjs['\"]|"
            r"ClerkProvider|SignIn|SignUp|UserButton|auth\(\)|"
            r"clerkMiddleware|currentUser",
            re.MULTILINE
        ),
        'supabase-auth': re.compile(
            r"from\s+['\"]@supabase/auth-helpers-nextjs['\"]|"
            r"from\s+['\"]@supabase/ssr['\"]|"
            r"createClientComponentClient|createServerComponentClient|"
            r"createMiddlewareClient",
            re.MULTILINE
        ),
        'lucia': re.compile(
            r"from\s+['\"]lucia['\"]|from\s+['\"]@lucia-auth/",
            re.MULTILINE
        ),
        'kinde': re.compile(
            r"from\s+['\"]@kinde-oss/kinde-auth-nextjs['\"]",
            re.MULTILINE
        ),

        # ── CMS ──────────────────────────────────────────────────
        'contentful': re.compile(
            r"from\s+['\"]contentful['\"]|createClient.*contentful|"
            r"CONTENTFUL_SPACE_ID",
            re.MULTILINE
        ),
        'sanity': re.compile(
            r"from\s+['\"]next-sanity['\"]|from\s+['\"]@sanity/|"
            r"createClient.*sanity|groq\s*`",
            re.MULTILINE
        ),
        'strapi': re.compile(
            r"strapi|STRAPI_URL|NEXT_PUBLIC_STRAPI",
            re.MULTILINE
        ),
        'payload': re.compile(
            r"from\s+['\"]payload['\"]|from\s+['\"]@payloadcms/",
            re.MULTILINE
        ),
        'directus': re.compile(
            r"from\s+['\"]@directus/sdk['\"]|createDirectus",
            re.MULTILINE
        ),

        # ── Database ─────────────────────────────────────────────
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|prisma\.\w+",
            re.MULTILINE
        ),
        'drizzle': re.compile(
            r"from\s+['\"]drizzle-orm['\"]|drizzle\(|pgTable|sqliteTable|mysqlTable",
            re.MULTILINE
        ),
        'supabase': re.compile(
            r"from\s+['\"]@supabase/supabase-js['\"]|createClient.*supabase|"
            r"supabase\.from",
            re.MULTILINE
        ),
        'planetscale': re.compile(
            r"from\s+['\"]@planetscale/database['\"]|planetscale",
            re.MULTILINE
        ),
        'neon': re.compile(
            r"from\s+['\"]@neondatabase/serverless['\"]|neon\(",
            re.MULTILINE
        ),
        'vercel-postgres': re.compile(
            r"from\s+['\"]@vercel/postgres['\"]|sql\s*`",
            re.MULTILINE
        ),
        'vercel-kv': re.compile(
            r"from\s+['\"]@vercel/kv['\"]|kv\.\w+",
            re.MULTILINE
        ),
        'vercel-blob': re.compile(
            r"from\s+['\"]@vercel/blob['\"]|put\(.*blob",
            re.MULTILINE
        ),
        'upstash': re.compile(
            r"from\s+['\"]@upstash/redis['\"]|from\s+['\"]@upstash/",
            re.MULTILINE
        ),

        # ── Deployment ───────────────────────────────────────────
        'vercel': re.compile(
            r"vercel\.json|from\s+['\"]@vercel/|VERCEL_URL|vercel deploy",
            re.MULTILINE
        ),

        # ── Analytics ────────────────────────────────────────────
        'vercel-analytics': re.compile(
            r"from\s+['\"]@vercel/analytics['\"]|Analytics\b",
            re.MULTILINE
        ),
        'vercel-speed-insights': re.compile(
            r"from\s+['\"]@vercel/speed-insights['\"]|SpeedInsights",
            re.MULTILINE
        ),
        'posthog': re.compile(
            r"from\s+['\"]posthog-js['\"]|from\s+['\"]posthog-js/react['\"]",
            re.MULTILINE
        ),

        # ── API ──────────────────────────────────────────────────
        'trpc': re.compile(
            r"from\s+['\"]@trpc/(?:server|client|next|react-query)['\"]|"
            r"createTRPCRouter|publicProcedure|protectedProcedure",
            re.MULTILINE
        ),

        # ── Email ────────────────────────────────────────────────
        'react-email': re.compile(
            r"from\s+['\"]@react-email/|from\s+['\"]react-email['\"]",
            re.MULTILINE
        ),
        'resend': re.compile(
            r"from\s+['\"]resend['\"]|Resend\(",
            re.MULTILINE
        ),

        # ── Monitoring ───────────────────────────────────────────
        'sentry': re.compile(
            r"from\s+['\"]@sentry/nextjs['\"]|Sentry\.init|captureException",
            re.MULTILINE
        ),

        # ── MDX ──────────────────────────────────────────────────
        'mdx': re.compile(
            r"from\s+['\"]@next/mdx['\"]|from\s+['\"]next-mdx-remote['\"]|"
            r"from\s+['\"]contentlayer['\"]|MDXRemote|compileMDX",
            re.MULTILINE
        ),

        # ── i18n ─────────────────────────────────────────────────
        'next-intl': re.compile(
            r"from\s+['\"]next-intl['\"]|useTranslations|NextIntlClientProvider",
            re.MULTILINE
        ),
        'next-i18next': re.compile(
            r"from\s+['\"]next-i18next['\"]|serverSideTranslations|useTranslation",
            re.MULTILINE
        ),
    }

    # Next.js version detection from features
    NEXTJS_VERSION_FEATURES = {
        # Next.js 15 features
        'cacheLife': '15.0',
        'cacheTag': '15.0',
        'connection()': '15.0',
        'next.config.ts': '15.0',
        'after(': '15.0',
        'instrumentation.ts': '15.0',
        'forbidden(': '15.0',
        'unauthorized(': '15.0',

        # Next.js 14 features
        'useFormState': '14.0',
        'useFormStatus': '14.0',
        'Partial Prerendering': '14.0',

        # Next.js 13 features
        'generateMetadata': '13.2',
        'generateStaticParams': '13.0',
        'generateViewport': '13.0',
        'next/font': '13.0',
        '/app/': '13.0',
        'page.tsx': '13.0',
        'layout.tsx': '13.0',
        'loading.tsx': '13.0',
        'error.tsx': '13.0',
        "from 'next/navigation'": '13.0',

        # Next.js 12 features
        'middleware.ts': '12.0',
        'NextMiddleware': '12.0',
        'NextResponse': '12.0',
        "runtime: 'edge'": '12.0',

        # Next.js 10 features
        'next/image': '10.0',
        "from 'next/image'": '10.0',

        # Next.js 9 features
        'getServerSideProps': '9.3',
        'getStaticProps': '9.3',
        'getStaticPaths': '9.3',
    }

    def __init__(self):
        """Initialize the parser with all Next.js extractors."""
        self.page_extractor = NextPageExtractor()
        self.route_handler_extractor = NextRouteHandlerExtractor()
        self.config_extractor = NextConfigExtractor()
        self.server_action_extractor = NextServerActionExtractor()
        self.data_fetching_extractor = NextDataFetchingExtractor()

    def parse(self, content: str, file_path: str = "") -> NextJSParseResult:
        """
        Parse Next.js source code and extract all Next.js-specific information.

        This should be called AFTER the JS/TS/React parsers have run, when
        Next.js framework is detected. It extracts Next.js-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            NextJSParseResult with all extracted Next.js information
        """
        result = NextJSParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path)

        # Detect directives
        result.is_client_component = bool(re.search(r"""^['"]use client['"]""", content, re.MULTILINE))
        normalized_fp = file_path.replace('\\', '/')
        if normalized_fp and not normalized_fp.startswith('/'):
            normalized_fp = '/' + normalized_fp
        result.is_server_component = bool(
            re.search(r"""^['"]use server['"]""", content, re.MULTILINE)
        ) or (
            '/app/' in normalized_fp and not result.is_client_component
            and any(s in normalized_fp for s in ('page.', 'layout.', 'route.'))
        )

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Pages & Layouts ──────────────────────────────────────
        page_result = self.page_extractor.extract(content, file_path)
        result.pages = page_result.get('pages', [])
        result.layouts = page_result.get('layouts', [])
        result.loadings = page_result.get('loadings', [])
        result.errors = page_result.get('errors', [])
        result.templates = page_result.get('templates', [])
        result.metadata = page_result.get('metadata', [])
        result.segment_configs = page_result.get('segment_configs', [])

        # ── Route Handlers ───────────────────────────────────────
        route_result = self.route_handler_extractor.extract(content, file_path)
        result.route_handlers = route_result.get('route_handlers', [])
        result.api_routes = route_result.get('api_routes', [])
        result.middleware = route_result.get('middleware', [])

        # ── Server Actions ───────────────────────────────────────
        action_result = self.server_action_extractor.extract(content, file_path)
        result.server_actions = action_result.get('server_actions', [])
        result.form_actions = action_result.get('form_actions', [])

        # ── Data Fetching ────────────────────────────────────────
        fetch_result = self.data_fetching_extractor.extract(content, file_path)
        result.fetch_calls = fetch_result.get('fetch_calls', [])
        result.caches = fetch_result.get('caches', [])
        result.static_params = fetch_result.get('static_params', [])
        result.has_dynamic_signals = fetch_result.get('has_dynamic_signals', False)
        result.has_parallel_fetch = fetch_result.get('has_parallel_fetch', False)
        result.suspense_count = fetch_result.get('suspense_count', 0)

        # ── Config (only for config files) ───────────────────────
        if result.file_type == "config":
            config_result = self.config_extractor.extract(content, file_path)
            result.config = config_result.get('config')
            result.image_config = config_result.get('image_config')
            result.i18n_config = config_result.get('i18n_config')
            result.experimental = config_result.get('experimental')

        # ── Router type detection ────────────────────────────────
        if result.pages or result.api_routes:
            result.router_type = "pages"
        if result.layouts or result.route_handlers:
            result.router_type = "app" if not result.router_type else "hybrid"

        # ── Version detection ────────────────────────────────────
        result.nextjs_version = self._detect_nextjs_version(content, file_path)

        return result

    def _classify_file(self, file_path: str) -> str:
        """Classify a Next.js file by its role."""
        normalized = file_path.replace('\\', '/')
        # Ensure leading slash for consistent substring matching
        if normalized and not normalized.startswith('/'):
            normalized = '/' + normalized
        basename = normalized.split('/')[-1] if normalized else ""

        if basename.startswith('next.config'):
            return "config"
        if basename.startswith('middleware.'):
            return "middleware"
        if basename.startswith('instrumentation.'):
            return "instrumentation"
        if basename.startswith('layout.'):
            return "layout"
        if basename.startswith('page.'):
            return "page"
        if basename.startswith('loading.'):
            return "loading"
        if basename.startswith('error.') or basename.startswith('global-error.'):
            return "error"
        if basename.startswith('not-found.'):
            return "not-found"
        if basename.startswith('template.'):
            return "template"
        if basename.startswith('route.'):
            return "route"
        if '/pages/api/' in normalized:
            return "api"
        if '/pages/' in normalized:
            return "page"
        if 'action' in basename.lower() or 'server' in basename.lower():
            return "action"
        return "component"

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Next.js ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_nextjs_version(self, content: str, file_path: str = "") -> str:
        """
        Detect the minimum Next.js version required by the file.

        Returns version string (e.g., '15.0', '14.0', '13.0').
        Detection is based on features used in the code and file path patterns.
        """
        max_version = '0.0'

        for feature, version in self.NEXTJS_VERSION_FEATURES.items():
            if feature in content or feature in file_path:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1>v2, <0 if v1<v2, 0 if equal."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_nextjs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Next.js-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Next.js-specific patterns
        """
        normalized = file_path.replace('\\', '/')
        # Ensure leading slash for consistent substring matching
        if normalized and not normalized.startswith('/'):
            normalized = '/' + normalized
        basename = normalized.split('/')[-1] if normalized else ""

        # Config files
        if basename.startswith('next.config'):
            return True

        # Middleware
        if basename.startswith('middleware.'):
            return True

        # Instrumentation
        if basename.startswith('instrumentation.'):
            return True

        # App Router special files
        if '/app/' in normalized and basename.split('.')[0] in (
            'page', 'layout', 'loading', 'error', 'global-error',
            'not-found', 'template', 'route', 'default',
            'opengraph-image', 'twitter-image', 'icon', 'apple-icon',
            'sitemap', 'robots', 'manifest',
        ):
            return True

        # Pages Router pages
        if '/pages/' in normalized:
            return True

        # Content-based detection
        if re.search(r"from\s+['\"]next['/\"]", content):
            return True

        if re.search(r'getServerSideProps|getStaticProps|getStaticPaths', content):
            return True

        if re.search(r'NextResponse|NextRequest|NextMiddleware', content):
            return True

        if re.search(r'generateMetadata|generateStaticParams|generateViewport', content):
            return True

        if re.search(r"from\s+['\"]next/(?:server|navigation|headers|cache)['\"]", content):
            return True

        # Server actions with Next.js-specific features
        if re.search(r"revalidatePath|revalidateTag", content):
            return True

        return False
