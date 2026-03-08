"""
React Routing Extractor for CodeTrellis

Extracts routing patterns from React applications:
- React Router v5 (Route, Switch, Redirect)
- React Router v6 (Route, Routes, createBrowserRouter, Outlet, loader/action)
- Next.js Pages Router (pages/ directory, getServerSideProps, getStaticProps)
- Next.js App Router (app/ directory, layout.tsx, page.tsx, loading.tsx, error.tsx)
- TanStack Router (createRouter, createRoute, createFileRoute)
- Remix routing (loader, action, meta, links)
- File-based routing detection

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReactRouteInfo:
    """Information about a React route definition."""
    path: str
    file: str = ""
    line_number: int = 0
    component: str = ""  # Component rendered at this route
    framework: str = ""  # react-router, next-pages, next-app, tanstack, remix
    has_loader: bool = False
    has_action: bool = False
    has_error_boundary: bool = False
    is_lazy: bool = False
    is_protected: bool = False  # Behind auth guard
    is_index: bool = False
    layout: str = ""  # Parent layout component
    children: List[str] = field(default_factory=list)  # Nested route paths
    middleware: List[str] = field(default_factory=list)  # Route guards/middleware


@dataclass
class ReactLayoutInfo:
    """Information about a layout component."""
    name: str
    file: str = ""
    line_number: int = 0
    framework: str = ""  # next-app, remix, react-router
    has_outlet: bool = False  # React Router Outlet
    has_children_prop: bool = False
    nested_layouts: List[str] = field(default_factory=list)


@dataclass
class ReactPageInfo:
    """Information about a Next.js/Remix page or route segment."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""  # Inferred URL path
    framework: str = ""  # next-pages, next-app, remix
    has_ssr: bool = False  # getServerSideProps / server component
    has_ssg: bool = False  # getStaticProps / generateStaticParams
    has_isr: bool = False  # revalidate
    has_api: bool = False  # API route
    has_middleware: bool = False
    has_metadata: bool = False  # Next.js metadata export
    data_fetching: str = ""  # ssr, ssg, isr, csr, rsc


class ReactRoutingExtractor:
    """
    Extracts routing patterns from React source code.

    Detects:
    - React Router v5/v6 route definitions
    - Next.js pages/app router patterns
    - TanStack Router definitions
    - Remix route patterns
    - File-based routing inference
    """

    # React Router v6 - createBrowserRouter
    CREATE_ROUTER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:createBrowserRouter|createHashRouter|createMemoryRouter)\s*\(\s*\[',
        re.MULTILINE
    )

    # React Router - Route component (JSX)
    ROUTE_JSX_PATTERN = re.compile(
        r'<Route\s+'
        r'(?:[^>]*?)'
        r'path\s*=\s*[{\'"]([^\'"}>]+)[\'"}]'
        r'(?:[^>]*?)'
        r'(?:element\s*=\s*\{?\s*<?([A-Z]\w*)|component\s*=\s*\{?\s*([A-Z]\w*))?',
        re.MULTILINE | re.DOTALL
    )

    # React Router - Route object (createBrowserRouter)
    ROUTE_OBJECT_PATTERN = re.compile(
        r'\{\s*'
        r'path\s*:\s*[\'"]([^\'"]+)[\'"]'
        r'(?:[^}]*?)'
        r'(?:element\s*:\s*<?([A-Z]\w*)|Component\s*:\s*([A-Z]\w*)|lazy\s*:\s*)',
        re.MULTILINE | re.DOTALL
    )

    # Next.js Pages Router - getServerSideProps / getStaticProps
    NEXT_PAGES_SSR_PATTERN = re.compile(
        r'export\s+(?:async\s+)?function\s+(getServerSideProps|getStaticProps|getStaticPaths)\s*\(',
        re.MULTILINE
    )

    # Next.js App Router - metadata
    NEXT_APP_METADATA_PATTERN = re.compile(
        r'export\s+(?:const|async\s+function)\s+(metadata|generateMetadata|generateStaticParams)\b',
        re.MULTILINE
    )

    # Next.js App Router - route segment config
    NEXT_SEGMENT_CONFIG = re.compile(
        r'export\s+const\s+(dynamic|revalidate|runtime|fetchCache|preferredRegion)\s*=',
        re.MULTILINE
    )

    # React Router - Outlet
    OUTLET_PATTERN = re.compile(r'<Outlet\s*/?>', re.MULTILINE)

    # Route loader/action
    LOADER_PATTERN = re.compile(
        r'(?:export\s+)?(?:async\s+)?(?:function|const)\s+(loader|action)\s*[\(=]',
        re.MULTILINE
    )

    # Protected route patterns
    PROTECTED_ROUTE_PATTERN = re.compile(
        r'(?:ProtectedRoute|PrivateRoute|AuthGuard|RequireAuth|withAuth)\b',
        re.MULTILINE
    )

    # TanStack Router
    TANSTACK_ROUTE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:createRoute|createFileRoute|createRootRoute|new\s+Route)\s*\(',
        re.MULTILINE
    )

    # Remix patterns
    REMIX_EXPORTS_PATTERN = re.compile(
        r'export\s+(?:async\s+)?(?:function|const)\s+'
        r'(loader|action|meta|links|headers|handle|shouldRevalidate)\b',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract routing patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'layouts', 'pages'
        """
        routes = []
        layouts = []
        pages = []

        # Infer framework from file path and content
        # Normalize: check for /pages/ or pages/ at start
        normalized_path = '/' + file_path.lstrip('/') if file_path and not file_path.startswith('/') else file_path
        is_next_pages = '/pages/' in normalized_path and (
            file_path.endswith('.tsx') or file_path.endswith('.jsx') or
            file_path.endswith('.ts') or file_path.endswith('.js')
        )
        is_next_app = '/app/' in normalized_path and (
            'page.' in file_path or 'layout.' in file_path or
            'loading.' in file_path or 'error.' in file_path or
            'route.' in file_path or 'template.' in file_path
        )
        has_remix = bool(self.REMIX_EXPORTS_PATTERN.search(content))
        has_rr = bool(re.search(r'from\s+[\'"]react-router', content))

        # ── React Router v6 Routes (JSX) ─────────────────────────
        for m in self.ROUTE_JSX_PATTERN.finditer(content):
            path = m.group(1)
            component = m.group(2) or m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            is_protected = bool(self.PROTECTED_ROUTE_PATTERN.search(
                content[max(0, m.start() - 200):m.end() + 200]))

            route = ReactRouteInfo(
                path=path,
                file=file_path,
                line_number=line,
                component=component,
                framework="react-router",
                is_protected=is_protected,
                is_index=path == '/' or path == '',
            )
            routes.append(route)

        # ── React Router v6 Routes (createBrowserRouter objects) ──
        for m in self.ROUTE_OBJECT_PATTERN.finditer(content):
            path = m.group(1)
            component = m.group(2) or m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            is_lazy = bool(re.search(r'lazy\s*:', content[m.start():m.end() + 100]))

            route = ReactRouteInfo(
                path=path,
                file=file_path,
                line_number=line,
                component=component,
                framework="react-router",
                is_lazy=is_lazy,
                is_index=path == '/' or path == '',
            )
            routes.append(route)

        # ── Next.js Pages Router ──────────────────────────────────
        if is_next_pages:
            # Infer route from file path
            route_path = self._infer_next_pages_route(file_path)
            is_api = '/api/' in file_path

            has_ssr = bool(re.search(r'getServerSideProps', content))
            has_ssg = bool(re.search(r'getStaticProps', content))
            has_isr = bool(re.search(r'revalidate', content))

            data_fetching = "csr"
            if has_ssr:
                data_fetching = "ssr"
            elif has_ssg:
                data_fetching = "isr" if has_isr else "ssg"

            page = ReactPageInfo(
                name=self._name_from_path(file_path),
                file=file_path,
                route_path=route_path,
                framework="next-pages",
                has_ssr=has_ssr,
                has_ssg=has_ssg,
                has_isr=has_isr,
                has_api=is_api,
                data_fetching=data_fetching,
            )
            pages.append(page)

        # ── Next.js App Router ────────────────────────────────────
        if is_next_app:
            route_path = self._infer_next_app_route(file_path)
            is_layout = 'layout.' in file_path
            is_page = 'page.' in file_path
            is_route = 'route.' in file_path  # API route

            has_metadata = bool(self.NEXT_APP_METADATA_PATTERN.search(content))
            has_generate_static = bool(re.search(r'generateStaticParams', content))
            is_server = not bool(re.search(r"['\"]use client['\"]", content))

            data_fetching = "rsc" if is_server else "csr"
            if has_generate_static:
                data_fetching = "ssg"

            if is_layout:
                layout = ReactLayoutInfo(
                    name=self._name_from_path(file_path),
                    file=file_path,
                    framework="next-app",
                    has_children_prop=bool(re.search(r'children', content)),
                )
                layouts.append(layout)

            if is_page or is_route:
                page = ReactPageInfo(
                    name=self._name_from_path(file_path),
                    file=file_path,
                    route_path=route_path,
                    framework="next-app",
                    has_ssr=is_server,
                    has_ssg=has_generate_static,
                    has_api=is_route,
                    has_metadata=has_metadata,
                    data_fetching=data_fetching,
                )
                pages.append(page)

        # ── Remix Routes ──────────────────────────────────────────
        if has_remix:
            remix_exports = [m.group(1) for m in self.REMIX_EXPORTS_PATTERN.finditer(content)]

            route = ReactRouteInfo(
                path=self._infer_remix_route(file_path),
                file=file_path,
                framework="remix",
                has_loader='loader' in remix_exports,
                has_action='action' in remix_exports,
            )
            routes.append(route)

        # ── TanStack Router ───────────────────────────────────────
        for m in self.TANSTACK_ROUTE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Try to extract path
            after = content[m.end():m.end() + 300]
            path_match = re.search(r'path\s*:\s*[\'"]([^\'"]+)[\'"]', after)
            path = path_match.group(1) if path_match else ""

            route = ReactRouteInfo(
                path=path,
                file=file_path,
                line_number=line,
                component=name,
                framework="tanstack-router",
            )
            routes.append(route)

        # ── Layout detection (React Router / generic) ─────────────
        if self.OUTLET_PATTERN.search(content):
            # File contains <Outlet />, it's a layout
            layout_name = self._name_from_path(file_path)
            layout = ReactLayoutInfo(
                name=layout_name,
                file=file_path,
                framework="react-router" if has_rr else "unknown",
                has_outlet=True,
            )
            layouts.append(layout)

        # ── Route loader/action detection ─────────────────────────
        for m in self.LOADER_PATTERN.finditer(content):
            export_name = m.group(1)
            # Attach to routes in this file
            for rt in routes:
                if rt.file == file_path:
                    if export_name == 'loader':
                        rt.has_loader = True
                    elif export_name == 'action':
                        rt.has_action = True

        return {
            'routes': routes,
            'layouts': layouts,
            'pages': pages,
        }

    def _infer_next_pages_route(self, file_path: str) -> str:
        """Infer URL route from Next.js pages directory file path."""
        # /pages/api/users/[id].ts -> /api/users/[id]
        match = re.search(r'/pages/(.+?)(?:\.\w+)$', file_path)
        if match:
            route = '/' + match.group(1)
            route = route.replace('/index', '').replace('\\', '/')
            if not route:
                route = '/'
            return route
        return ""

    def _infer_next_app_route(self, file_path: str) -> str:
        """Infer URL route from Next.js app directory file path."""
        # /app/dashboard/settings/page.tsx -> /dashboard/settings
        match = re.search(r'/app/(.+?)(?:/(?:page|layout|loading|error|route|template)\.\w+)$', file_path)
        if match:
            route = '/' + match.group(1)
            route = route.replace('\\', '/')
            # Convert (group) to optional group markers
            route = re.sub(r'/\(([^)]+)\)', '', route)
            return route if route else '/'
        # Root page/layout
        if re.search(r'/app/(?:page|layout)\.\w+$', file_path):
            return '/'
        return ""

    def _infer_remix_route(self, file_path: str) -> str:
        """Infer URL route from Remix file path."""
        match = re.search(r'/routes/(.+?)(?:\.\w+)$', file_path)
        if match:
            route = match.group(1)
            # Remix conventions: $ = dynamic, _ = pathless
            route = route.replace('.', '/').replace('$', ':')
            return '/' + route
        return ""

    def _name_from_path(self, file_path: str) -> str:
        """Extract a meaningful name from file path."""
        import os
        name = os.path.basename(file_path)
        name = re.sub(r'\.\w+$', '', name)  # Remove extension
        return name
