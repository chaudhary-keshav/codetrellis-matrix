"""
Next.js Page Extractor for CodeTrellis

Extracts page-level constructs from Next.js applications:
- Pages Router pages (pages/ directory)
- App Router pages (app/ directory - page.tsx, layout.tsx, etc.)
- Data fetching functions (getServerSideProps, getStaticProps, getStaticPaths)
- App Router metadata (generateMetadata, export const metadata)
- Segment config exports (dynamic, revalidate, runtime, fetchCache)
- Parallel routes (@folder), intercepting routes ((..)folder)
- Route groups ((group)), catch-all segments ([...slug])
- Default exports (page components)
- Loading/Error/NotFound/Template special files

Supports:
- Next.js 9.x (pages/ directory, getServerSideProps)
- Next.js 10.x (i18n routing, Image optimization)
- Next.js 12.x (middleware, edge runtime)
- Next.js 13.x (app/ directory, Server Components, Layouts)
- Next.js 14.x (Server Actions, Partial Prerendering)
- Next.js 15.x (Turbopack stable, improved caching, async request APIs)

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NextPageInfo:
    """Information about a Next.js page component."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""  # Inferred URL path from file structure
    router: str = ""  # "pages" or "app"
    is_dynamic: bool = False  # [slug], [...slug], [[...slug]]
    dynamic_params: List[str] = field(default_factory=list)
    has_ssr: bool = False  # getServerSideProps or server component
    has_ssg: bool = False  # getStaticProps or generateStaticParams
    has_isr: bool = False  # revalidate option
    has_metadata: bool = False  # export metadata or generateMetadata
    is_server_component: bool = False
    is_client_component: bool = False
    data_fetching: str = ""  # ssr, ssg, isr, csr, rsc
    is_default_export: bool = True
    parallel_route: str = ""  # @folder name if parallel route
    route_group: str = ""  # (group) name if in route group
    is_intercepting: bool = False
    segment_config: dict = field(default_factory=dict)


@dataclass
class NextLayoutInfo:
    """Information about a Next.js App Router layout."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    is_root_layout: bool = False
    has_metadata: bool = False
    has_viewport: bool = False
    has_children_prop: bool = True
    is_server_component: bool = True
    is_client_component: bool = False
    fonts_used: List[str] = field(default_factory=list)
    providers_wrapped: List[str] = field(default_factory=list)


@dataclass
class NextLoadingInfo:
    """Information about a Next.js App Router loading boundary."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    uses_suspense: bool = False
    skeleton_type: str = ""  # spinner, skeleton, shimmer


@dataclass
class NextErrorInfo:
    """Information about a Next.js App Router error boundary."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    is_global: bool = False  # global-error.tsx
    has_reset: bool = False
    has_error_logging: bool = False
    is_client_component: bool = True  # Error boundaries must be client components


@dataclass
class NextTemplateInfo:
    """Information about a Next.js App Router template."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""


@dataclass
class NextMetadataInfo:
    """Information about Next.js metadata exports."""
    name: str  # metadata, generateMetadata, viewport, generateViewport
    file: str = ""
    line_number: int = 0
    metadata_type: str = ""  # static, dynamic (generateMetadata)
    fields: List[str] = field(default_factory=list)  # title, description, openGraph, etc.


@dataclass
class NextSegmentConfigInfo:
    """Information about Next.js route segment config."""
    name: str  # dynamic, revalidate, runtime, fetchCache, preferredRegion
    file: str = ""
    line_number: int = 0
    value: str = ""  # 'force-dynamic', 0, 'edge', etc.


class NextPageExtractor:
    """
    Extracts page-level patterns from Next.js source code.

    Detects:
    - Pages Router pages with data fetching
    - App Router pages with segment config
    - Layout, Loading, Error, Template special files
    - Metadata exports (static and dynamic)
    - Dynamic route segments
    - Parallel/intercepting routes
    """

    # Pages Router data fetching
    PAGES_GSSP = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+getServerSideProps\s*\(',
        re.MULTILINE
    )
    PAGES_GSP = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+getStaticProps\s*\(',
        re.MULTILINE
    )
    PAGES_GSPATHS = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+getStaticPaths\s*\(',
        re.MULTILINE
    )
    PAGES_GIP = re.compile(
        r'(?:getInitialProps|\.getInitialProps)\s*=',
        re.MULTILINE
    )

    # App Router metadata
    STATIC_METADATA = re.compile(
        r'^[ \t]*export\s+const\s+(metadata|viewport)\s*(?::\s*\w+\s*)?=\s*\{',
        re.MULTILINE
    )
    DYNAMIC_METADATA = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+(generateMetadata|generateViewport)\s*\(',
        re.MULTILINE
    )

    # Segment config
    SEGMENT_CONFIG = re.compile(
        r'^[ \t]*export\s+const\s+(dynamic|revalidate|runtime|fetchCache|preferredRegion|dynamicParams|maxDuration)\s*=\s*[\'"]?([^\s;\n\'"]+)',
        re.MULTILINE
    )

    # Default export detection
    DEFAULT_EXPORT = re.compile(
        r'^[ \t]*export\s+default\s+(?:async\s+)?(?:function\s+)?(\w+)',
        re.MULTILINE
    )

    # Directive detection
    USE_CLIENT = re.compile(r'''^['"]use client['"]''', re.MULTILINE)
    USE_SERVER = re.compile(r'''^['"]use server['"]''', re.MULTILINE)

    # generateStaticParams
    GENERATE_STATIC_PARAMS = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+generateStaticParams\s*\(',
        re.MULTILINE
    )

    # Error boundary reset
    ERROR_RESET = re.compile(r'reset\s*\(\s*\)|reset\s*:', re.MULTILINE)

    # Dynamic route segment pattern in file path
    DYNAMIC_SEGMENT = re.compile(r'\[([^\]]+)\]')

    # Parallel route pattern
    PARALLEL_ROUTE = re.compile(r'@(\w+)')

    # Route group pattern
    ROUTE_GROUP = re.compile(r'\((\w+)\)')

    # Intercepting route pattern
    INTERCEPTING_ROUTE = re.compile(r'\(\.\.\??\.?\)')

    # Metadata fields
    METADATA_FIELD = re.compile(
        r'(?:title|description|openGraph|twitter|icons|manifest|robots|'
        r'alternates|authors|creator|publisher|keywords|metadataBase)\s*:',
        re.MULTILINE
    )

    # Font imports
    FONT_IMPORT = re.compile(
        r"from\s+['\"]next/font/(?:google|local)['\"]",
        re.MULTILINE
    )
    FONT_USAGE = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*(\w+)\s*\(",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract page-level patterns from Next.js source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'pages', 'layouts', 'loadings', 'errors', 'templates',
                      'metadata', 'segment_configs'
        """
        pages = []
        layouts = []
        loadings = []
        errors = []
        templates = []
        metadata_items = []
        segment_configs = []

        normalized = file_path.replace('\\', '/')
        # Ensure leading slash for consistent substring matching
        if normalized and not normalized.startswith('/'):
            normalized = '/' + normalized

        # Determine router type
        is_pages_router = '/pages/' in normalized
        is_app_router = '/app/' in normalized

        # Detect directives
        is_client = bool(self.USE_CLIENT.search(content))
        is_server = bool(self.USE_SERVER.search(content))

        # ── Route path inference ─────────────────────────────────
        route_path = self._infer_route_path(normalized)

        # ── Dynamic segments ─────────────────────────────────────
        dynamic_params = self.DYNAMIC_SEGMENT.findall(normalized)
        is_dynamic = len(dynamic_params) > 0

        # ── Parallel route ───────────────────────────────────────
        parallel_match = self.PARALLEL_ROUTE.search(normalized)
        parallel_route = parallel_match.group(1) if parallel_match else ""

        # ── Route group ──────────────────────────────────────────
        group_match = self.ROUTE_GROUP.search(normalized)
        route_group = group_match.group(1) if group_match else ""

        # ── Intercepting route ───────────────────────────────────
        is_intercepting = bool(self.INTERCEPTING_ROUTE.search(normalized))

        # ── Default export (page component name) ─────────────────
        default_match = self.DEFAULT_EXPORT.search(content)
        component_name = default_match.group(1) if default_match else ""

        # ── App Router special files ─────────────────────────────
        basename = normalized.split('/')[-1] if normalized else ""

        if is_app_router and basename.startswith('page.'):
            page = NextPageInfo(
                name=component_name or "Page",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
                router="app",
                is_dynamic=is_dynamic,
                dynamic_params=dynamic_params,
                has_metadata=bool(self.STATIC_METADATA.search(content) or self.DYNAMIC_METADATA.search(content)),
                is_server_component=not is_client,
                is_client_component=is_client,
                has_ssg=bool(self.GENERATE_STATIC_PARAMS.search(content)),
                has_ssr=not is_client,  # Server components are SSR by default
                data_fetching="rsc" if not is_client else "csr",
                parallel_route=parallel_route,
                route_group=route_group,
                is_intercepting=is_intercepting,
            )
            # Check ISR
            seg_match = self.SEGMENT_CONFIG.search(content)
            if seg_match and seg_match.group(1) == 'revalidate':
                page.has_isr = True
                page.data_fetching = "isr"
            pages.append(page)

        elif is_app_router and basename.startswith('layout.'):
            layout = NextLayoutInfo(
                name=component_name or "Layout",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
                is_root_layout=(route_path == "/" or 'app/layout.' in normalized),
                has_metadata=bool(self.STATIC_METADATA.search(content) or self.DYNAMIC_METADATA.search(content)),
                has_viewport=bool(re.search(r'export\s+const\s+viewport\b', content)),
                is_server_component=not is_client,
                is_client_component=is_client,
                fonts_used=self._detect_fonts(content),
                providers_wrapped=self._detect_providers(content),
            )
            layouts.append(layout)

        elif is_app_router and basename.startswith('loading.'):
            loading = NextLoadingInfo(
                name=component_name or "Loading",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
                uses_suspense=bool(re.search(r'<Suspense', content)),
            )
            loadings.append(loading)

        elif is_app_router and (basename.startswith('error.') or basename.startswith('global-error.')):
            error = NextErrorInfo(
                name=component_name or "Error",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
                is_global=basename.startswith('global-error.'),
                has_reset=bool(self.ERROR_RESET.search(content)),
                has_error_logging=bool(re.search(r'console\.error|reportError|captureException', content)),
                is_client_component=is_client or True,  # Error boundaries require 'use client'
            )
            errors.append(error)

        elif is_app_router and basename.startswith('template.'):
            template = NextTemplateInfo(
                name=component_name or "Template",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
            )
            templates.append(template)

        elif is_app_router and basename.startswith('not-found.'):
            # not-found.tsx treated like a special page
            page = NextPageInfo(
                name=component_name or "NotFound",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path + "/not-found",
                router="app",
                data_fetching="rsc" if not is_client else "csr",
                is_server_component=not is_client,
                is_client_component=is_client,
            )
            pages.append(page)

        # ── Pages Router pages ───────────────────────────────────
        elif is_pages_router and not basename.startswith('_') and basename.startswith(('index.', 'page.')) or (
            is_pages_router and '/api/' not in normalized and not basename.startswith('_')
        ):
            has_gssp = bool(self.PAGES_GSSP.search(content))
            has_gsp = bool(self.PAGES_GSP.search(content))
            has_gspaths = bool(self.PAGES_GSPATHS.search(content))
            has_gip = bool(self.PAGES_GIP.search(content))

            data_fetching = "csr"
            if has_gssp:
                data_fetching = "ssr"
            elif has_gsp and has_gspaths:
                data_fetching = "ssg"
            elif has_gsp:
                data_fetching = "ssg"

            page = NextPageInfo(
                name=component_name or "Page",
                file=file_path,
                line_number=default_match.start() if default_match else 1,
                route_path=route_path,
                router="pages",
                is_dynamic=is_dynamic,
                dynamic_params=dynamic_params,
                has_ssr=has_gssp or has_gip,
                has_ssg=has_gsp,
                has_isr=bool(re.search(r'revalidate\s*:\s*\d+', content)),
                data_fetching=data_fetching,
            )
            pages.append(page)

        # ── Metadata extraction ──────────────────────────────────
        for m in self.STATIC_METADATA.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            # Extract metadata fields
            fields = self.METADATA_FIELD.findall(content[m.start():m.start() + 500])
            metadata_items.append(NextMetadataInfo(
                name=name,
                file=file_path,
                line_number=line,
                metadata_type="static",
                fields=[f.strip().rstrip(':') for f in fields],
            ))

        for m in self.DYNAMIC_METADATA.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            metadata_items.append(NextMetadataInfo(
                name=name,
                file=file_path,
                line_number=line,
                metadata_type="dynamic",
                fields=[],
            ))

        # ── Segment config extraction ────────────────────────────
        for m in self.SEGMENT_CONFIG.finditer(content):
            name = m.group(1)
            value = m.group(2).strip("'\"")
            line = content[:m.start()].count('\n') + 1
            segment_configs.append(NextSegmentConfigInfo(
                name=name,
                file=file_path,
                line_number=line,
                value=value,
            ))

        return {
            "pages": pages,
            "layouts": layouts,
            "loadings": loadings,
            "errors": errors,
            "templates": templates,
            "metadata": metadata_items,
            "segment_configs": segment_configs,
        }

    def _infer_route_path(self, file_path: str) -> str:
        """Infer URL route path from file system path."""
        path = file_path

        # App Router: strip everything before /app/
        if '/app/' in path:
            path = path.split('/app/', 1)[1]
        elif '/pages/' in path:
            path = path.split('/pages/', 1)[1]
        else:
            return "/"

        # Remove file extension and index/page
        path = re.sub(r'/?(index|page|layout|loading|error|template|not-found|global-error)\.\w+$', '', path)

        # Remove route groups: (group)
        path = re.sub(r'\([^)]+\)/?', '', path)

        # Remove parallel routes: @folder
        path = re.sub(r'@\w+/?', '', path)

        # Clean up double slashes
        path = re.sub(r'/+', '/', path)

        # Ensure leading slash
        if not path.startswith('/'):
            path = '/' + path

        # Remove trailing slash (except root)
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Convert dynamic segments: [slug] -> :slug
        path = re.sub(r'\[\.\.\.(\w+)\]', r'*\1', path)  # catch-all
        path = re.sub(r'\[\[\.\.\.(\w+)\]\]', r'*\1?', path)  # optional catch-all
        path = re.sub(r'\[(\w+)\]', r':\1', path)  # dynamic segment

        return path if path else "/"

    def _detect_fonts(self, content: str) -> List[str]:
        """Detect Next.js font usage."""
        fonts = []
        if self.FONT_IMPORT.search(content):
            # Find font function calls
            font_funcs = re.findall(
                r"(?:const|let|var)\s+\w+\s*=\s*(\w+)\s*\(",
                content
            )
            fonts.extend(font_funcs)
        return fonts

    def _detect_providers(self, content: str) -> List[str]:
        """Detect provider components wrapped in layout."""
        providers = []
        provider_pattern = re.compile(r'<(\w*Provider)\b', re.MULTILINE)
        for m in provider_pattern.finditer(content):
            providers.append(m.group(1))
        return providers
