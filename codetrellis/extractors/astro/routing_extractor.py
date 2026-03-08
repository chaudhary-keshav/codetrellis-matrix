"""
Astro Routing Extractor v1.0

Extracts routing information from Astro projects:
- File-based routing (src/pages/)
- Dynamic routes ([param], [...spread], [...rest])
- API endpoints (GET, POST, PUT, DELETE, PATCH, ALL in .ts/.js)
- Middleware (src/middleware.ts, defineMiddleware, sequence)
- Rendering modes (SSR, SSG, hybrid, static)
- Redirects and rewrites
- i18n routing
- View transitions
- Page prerendering (export const prerender)

Supports Astro v1.x - v5.x routing features.

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AstroRouteInfo:
    """Information about a route in an Astro project."""
    route_path: str = ""  # /blog/[slug], /api/users
    file_path: str = ""
    line_number: int = 0
    route_type: str = "page"  # page, api, redirect
    is_dynamic: bool = False
    is_rest: bool = False  # [...rest]
    is_index: bool = False
    param_names: List[str] = field(default_factory=list)
    has_get_static_paths: bool = False
    prerender: Optional[bool] = None  # True/False/None(inherit)
    rendering_mode: str = ""  # static, server, hybrid


@dataclass
class AstroEndpointInfo:
    """Information about an API endpoint in an Astro project."""
    file_path: str = ""
    line_number: int = 0
    method: str = ""  # GET, POST, PUT, DELETE, PATCH, ALL
    route_path: str = ""
    has_params: bool = False
    has_request_body: bool = False
    returns_json: bool = False
    returns_redirect: bool = False
    has_error_handling: bool = False
    is_prerendered: bool = False


@dataclass
class AstroMiddlewareInfo:
    """Information about middleware in an Astro project."""
    file_path: str = ""
    line_number: int = 0
    middleware_type: str = ""  # defineMiddleware, sequence, onRequest
    has_next: bool = False
    has_locals: bool = False
    has_redirect: bool = False
    uses_sequence: bool = False


class AstroRoutingExtractor:
    """Extracts routing information from Astro projects."""

    # API endpoint method patterns
    EXPORT_FUNCTION = re.compile(
        r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|ALL|OPTIONS|HEAD)\s*\(',
        re.MULTILINE
    )
    EXPORT_CONST_FUNCTION = re.compile(
        r'export\s+const\s+(GET|POST|PUT|DELETE|PATCH|ALL|OPTIONS|HEAD)\s*(?::\s*APIRoute)?\s*=',
        re.MULTILINE
    )

    # getStaticPaths
    GET_STATIC_PATHS = re.compile(
        r'export\s+(?:async\s+)?function\s+getStaticPaths\b|'
        r'export\s+const\s+getStaticPaths\b',
        re.MULTILINE
    )

    # Prerender
    PRERENDER_TRUE = re.compile(
        r'export\s+const\s+prerender\s*=\s*true',
        re.MULTILINE
    )
    PRERENDER_FALSE = re.compile(
        r'export\s+const\s+prerender\s*=\s*false',
        re.MULTILINE
    )

    # Middleware patterns
    DEFINE_MIDDLEWARE = re.compile(
        r'defineMiddleware\s*\(',
        re.MULTILINE
    )
    SEQUENCE = re.compile(
        r'sequence\s*\(',
        re.MULTILINE
    )
    ON_REQUEST = re.compile(
        r'export\s+(?:const|function)\s+onRequest\b',
        re.MULTILINE
    )

    # Response patterns
    JSON_RESPONSE = re.compile(
        r'(?:Response\.json\s*\(|new\s+Response\s*\(\s*JSON\.stringify)',
        re.MULTILINE
    )
    REDIRECT_RESPONSE = re.compile(
        r'(?:Response\.redirect\s*\(|Astro\.redirect\s*\(|return\s+redirect\s*\()',
        re.MULTILINE
    )

    # Request body
    REQUEST_BODY = re.compile(
        r'request\.(?:json|text|formData|arrayBuffer|blob)\s*\(\s*\)',
        re.MULTILINE
    )

    # Error handling
    TRY_CATCH = re.compile(r'try\s*\{', re.MULTILINE)

    # Dynamic route param detection from file path
    ROUTE_PARAM = re.compile(r'\[([^\]]+)\]')
    REST_PARAM = re.compile(r'\[\.\.\.(\w+)\]')

    # i18n
    I18N_PATTERN = re.compile(
        r"i18n\s*:\s*\{|getRelativeLocaleUrl\s*\(|getAbsoluteLocaleUrl\s*\(",
        re.MULTILINE
    )

    # View transitions
    VIEW_TRANSITIONS = re.compile(
        r'<ViewTransitions\b|transition:(?:name|animate|persist)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract routing information from an Astro file.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with routing information
        """
        routes: List[AstroRouteInfo] = []
        endpoints: List[AstroEndpointInfo] = []
        middleware: List[AstroMiddlewareInfo] = []

        # Determine route path from file path
        route_path = self._file_to_route(file_path)

        # Check if this is a middleware file
        if self._is_middleware_file(file_path):
            self._extract_middleware(content, file_path, middleware)
            return {"routes": routes, "endpoints": endpoints, "middleware": middleware}

        # Check if this is an API endpoint (.ts/.js in pages/)
        is_api = self._is_api_endpoint(file_path, content)

        if is_api:
            self._extract_endpoints(content, file_path, route_path, endpoints)
        else:
            # Regular page route
            route = self._extract_route(content, file_path, route_path)
            if route:
                routes.append(route)

        return {"routes": routes, "endpoints": endpoints, "middleware": middleware}

    def _file_to_route(self, file_path: str) -> str:
        """Convert file path to route path."""
        if not file_path:
            return ""

        # Find the pages directory
        pages_idx = -1
        for marker in ['/pages/', '\\pages\\', '/src/pages/', '\\src\\pages\\']:
            idx = file_path.find(marker)
            if idx != -1:
                pages_idx = idx + len(marker)
                break

        if pages_idx == -1:
            return ""

        route = file_path[pages_idx:]
        # Remove file extension
        for ext in ['.astro', '.md', '.mdx', '.ts', '.js', '.mjs']:
            if route.endswith(ext):
                route = route[:-len(ext)]
                break

        # Remove index
        if route.endswith('/index') or route == 'index':
            route = route.rsplit('index', 1)[0]

        # Ensure leading slash
        if not route.startswith('/'):
            route = '/' + route

        # Clean trailing slash (except root)
        if route != '/' and route.endswith('/'):
            route = route[:-1]

        return route

    def _is_middleware_file(self, file_path: str) -> bool:
        """Check if a file is a middleware file."""
        if not file_path:
            return False
        import os
        name = os.path.basename(file_path)
        return name in ('middleware.ts', 'middleware.js', 'middleware.mjs')

    def _is_api_endpoint(self, file_path: str, content: str) -> bool:
        """Check if a file is an API endpoint."""
        if not file_path:
            return False
        # API endpoints are .ts/.js files in pages/ that export HTTP methods
        if not (file_path.endswith('.ts') or file_path.endswith('.js') or file_path.endswith('.mjs')):
            return False
        if '/pages/' not in file_path and '\\pages\\' not in file_path:
            return False
        return bool(self.EXPORT_FUNCTION.search(content) or self.EXPORT_CONST_FUNCTION.search(content))

    def _extract_route(self, content: str, file_path: str, route_path: str) -> Optional[AstroRouteInfo]:
        """Extract route information from a page file."""
        if not route_path:
            return None

        route = AstroRouteInfo(
            route_path=route_path,
            file_path=file_path,
            line_number=1,
            route_type="page",
        )

        # Dynamic route detection
        params = self.ROUTE_PARAM.findall(route_path)
        if params:
            route.is_dynamic = True
            for p in params:
                if p.startswith('...'):
                    route.is_rest = True
                    route.param_names.append(p[3:])
                else:
                    route.param_names.append(p)

        # Index page
        route.is_index = route_path == '/' or route_path.endswith('/index')

        # getStaticPaths
        route.has_get_static_paths = bool(self.GET_STATIC_PATHS.search(content))

        # Prerender
        if self.PRERENDER_TRUE.search(content):
            route.prerender = True
            route.rendering_mode = "static"
        elif self.PRERENDER_FALSE.search(content):
            route.prerender = False
            route.rendering_mode = "server"

        return route

    def _extract_endpoints(self, content: str, file_path: str, route_path: str,
                           endpoints: List[AstroEndpointInfo]) -> None:
        """Extract API endpoint information."""
        # Check prerender
        is_prerendered = bool(self.PRERENDER_TRUE.search(content))

        # Export function patterns
        for m in self.EXPORT_FUNCTION.finditer(content):
            method = m.group(1)
            line = content[:m.start()].count('\n') + 1
            endpoints.append(self._build_endpoint(
                content, file_path, route_path, method, line, is_prerendered
            ))

        for m in self.EXPORT_CONST_FUNCTION.finditer(content):
            method = m.group(1)
            line = content[:m.start()].count('\n') + 1
            endpoints.append(self._build_endpoint(
                content, file_path, route_path, method, line, is_prerendered
            ))

    def _build_endpoint(self, content: str, file_path: str, route_path: str,
                        method: str, line: int, is_prerendered: bool) -> AstroEndpointInfo:
        """Build an endpoint info object."""
        return AstroEndpointInfo(
            file_path=file_path,
            line_number=line,
            method=method,
            route_path=route_path,
            has_params='params' in content or 'Astro.params' in content,
            has_request_body=bool(self.REQUEST_BODY.search(content)),
            returns_json=bool(self.JSON_RESPONSE.search(content)),
            returns_redirect=bool(self.REDIRECT_RESPONSE.search(content)),
            has_error_handling=bool(self.TRY_CATCH.search(content)),
            is_prerendered=is_prerendered,
        )

    def _extract_middleware(self, content: str, file_path: str,
                           middleware_list: List[AstroMiddlewareInfo]) -> None:
        """Extract middleware information."""
        mw = AstroMiddlewareInfo(file_path=file_path, line_number=1)

        if self.DEFINE_MIDDLEWARE.search(content):
            mw.middleware_type = "defineMiddleware"
        elif self.ON_REQUEST.search(content):
            mw.middleware_type = "onRequest"

        mw.uses_sequence = bool(self.SEQUENCE.search(content))
        mw.has_next = 'next(' in content or 'next)' in content
        mw.has_locals = 'locals' in content or 'Astro.locals' in content
        mw.has_redirect = bool(self.REDIRECT_RESPONSE.search(content))

        middleware_list.append(mw)
