"""
Next.js Route Handler Extractor for CodeTrellis

Extracts route handler patterns from Next.js applications:
- App Router route handlers (app/**/route.ts - GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Pages Router API routes (pages/api/**)
- Edge API routes (runtime: 'edge')
- Next.js middleware (middleware.ts at project root)
- Streaming responses (ReadableStream, NextResponse)
- Rewrite and redirect configurations
- CORS handling
- Rate limiting patterns
- Auth middleware patterns

Supports:
- Next.js 9.x+ (API routes in pages/api)
- Next.js 12.x+ (middleware, edge runtime)
- Next.js 13.x+ (route handlers in app/)
- Next.js 14.x+ (improved middleware patterns)
- Next.js 15.x+ (async request APIs)

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NextRouteHandlerInfo:
    """Information about a Next.js App Router route handler."""
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    http_methods: List[str] = field(default_factory=list)  # GET, POST, etc.
    is_edge: bool = False  # runtime: 'edge'
    is_streaming: bool = False
    has_auth: bool = False
    has_cors: bool = False
    has_rate_limiting: bool = False
    response_type: str = ""  # json, stream, redirect, rewrite
    dynamic_params: List[str] = field(default_factory=list)
    uses_cookies: bool = False
    uses_headers: bool = False
    uses_next_request: bool = False
    segment_config: dict = field(default_factory=dict)


@dataclass
class NextAPIRouteInfo:
    """Information about a Next.js Pages Router API route."""
    name: str
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    http_methods: List[str] = field(default_factory=list)
    is_dynamic: bool = False
    dynamic_params: List[str] = field(default_factory=list)
    has_auth: bool = False
    has_validation: bool = False
    has_cors: bool = False
    response_type: str = ""  # json, stream, redirect


@dataclass
class NextMiddlewareInfo:
    """Information about Next.js middleware."""
    file: str = ""
    line_number: int = 0
    matcher_paths: List[str] = field(default_factory=list)
    has_auth_check: bool = False
    has_redirect: bool = False
    has_rewrite: bool = False
    has_headers: bool = False
    has_cookies: bool = False
    is_edge: bool = True  # Middleware always runs on Edge
    uses_next_response: bool = False
    conditional_paths: List[str] = field(default_factory=list)


@dataclass
class NextRewriteInfo:
    """Information about a Next.js rewrite rule."""
    source: str
    destination: str
    file: str = ""
    line_number: int = 0
    is_permanent: bool = False
    has_locale: bool = False


@dataclass
class NextRedirectInfo:
    """Information about a Next.js redirect rule."""
    source: str
    destination: str
    file: str = ""
    line_number: int = 0
    permanent: bool = False
    status_code: int = 0


class NextRouteHandlerExtractor:
    """
    Extracts route handler patterns from Next.js source code.

    Detects:
    - App Router route handlers (GET, POST, PUT, DELETE, etc.)
    - Pages Router API routes
    - Middleware configuration
    - Edge runtime usage
    - Streaming responses
    - Auth/CORS patterns
    """

    # App Router route handler exports
    ROUTE_HANDLER_PATTERN = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(',
        re.MULTILINE
    )

    # Arrow function route handlers
    ROUTE_HANDLER_ARROW = re.compile(
        r'^[ \t]*export\s+(?:const|let|var)\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*=\s*(?:async\s*)?\(',
        re.MULTILINE
    )

    # Pages Router API handler
    PAGES_API_HANDLER = re.compile(
        r'^[ \t]*export\s+default\s+(?:async\s+)?function\s*(?:\w+)?\s*\(\s*'
        r'(?:req|request)\s*(?::\s*Next\w*Request)?\s*,\s*'
        r'(?:res|response)\s*(?::\s*Next\w*Response)?\s*\)',
        re.MULTILINE
    )

    # Method checking in Pages API
    PAGES_METHOD_CHECK = re.compile(
        r"req\.method\s*===?\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # Middleware matcher config
    MIDDLEWARE_MATCHER = re.compile(
        r"export\s+const\s+config\s*=\s*\{[^}]*matcher\s*:\s*(\[[^\]]+\]|['\"][^'\"]+['\"])",
        re.MULTILINE | re.DOTALL
    )

    # Middleware file detection
    MIDDLEWARE_EXPORT = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+middleware\s*\(',
        re.MULTILINE
    )

    # Edge runtime
    EDGE_RUNTIME = re.compile(
        r"export\s+const\s+runtime\s*=\s*['\"]edge['\"]",
        re.MULTILINE
    )

    # NextResponse usage
    NEXT_RESPONSE = re.compile(
        r'NextResponse\.\w+',
        re.MULTILINE
    )

    # NextRequest usage
    NEXT_REQUEST = re.compile(
        r'NextRequest|request\s*:\s*NextRequest|req\s*:\s*NextRequest',
        re.MULTILINE
    )

    # Streaming
    STREAMING_PATTERN = re.compile(
        r'ReadableStream|TransformStream|new\s+Response\s*\(\s*stream|'
        r'StreamingTextResponse|NextResponse\.json.*stream',
        re.MULTILINE
    )

    # Auth patterns
    AUTH_PATTERN = re.compile(
        r'getServerSession|getSession|auth\(\)|getToken|'
        r'NextAuth|authOptions|createMiddlewareClient|'
        r'withAuth|isAuthenticated|requireAuth|clerkMiddleware|'
        r'currentUser\(\)|session\b',
        re.MULTILINE
    )

    # CORS pattern
    CORS_PATTERN = re.compile(
        r'Access-Control-Allow-Origin|allowedOrigins|cors\(|'
        r"headers\.set\(['\"]Access-Control",
        re.MULTILINE
    )

    # Rate limiting
    RATE_LIMIT_PATTERN = re.compile(
        r'rateLimit|rateLimiter|upstash.*ratelimit|@upstash/ratelimit|'
        r'Ratelimit|RateLimiter',
        re.MULTILINE
    )

    # Cookies usage
    COOKIES_PATTERN = re.compile(
        r'cookies\(\)|request\.cookies|response\.cookies|'
        r"NextResponse\..*cookie|req\.cookies",
        re.MULTILINE
    )

    # Headers usage
    HEADERS_PATTERN = re.compile(
        r'headers\(\)|request\.headers|response\.headers|'
        r'NextResponse\..*header',
        re.MULTILINE
    )

    # Dynamic segment in file path
    DYNAMIC_SEGMENT = re.compile(r'\[([^\]]+)\]')

    # Redirect/rewrite in config
    REDIRECT_PATTERN = re.compile(
        r"source\s*:\s*['\"]([^'\"]+)['\"].*?destination\s*:\s*['\"]([^'\"]+)['\"].*?(?:permanent\s*:\s*(true|false))?",
        re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract route handler patterns from Next.js source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'route_handlers', 'api_routes', 'middleware',
                      'rewrites', 'redirects'
        """
        route_handlers = []
        api_routes = []
        middleware_list = []
        rewrites = []
        redirects = []

        normalized = file_path.replace('\\', '/')
        # Ensure leading slash for consistent substring matching
        if normalized and not normalized.startswith('/'):
            normalized = '/' + normalized

        # ── App Router route handlers (app/**/route.ts) ──────────
        basename = normalized.split('/')[-1] if normalized else ""
        if basename.startswith('route.') and '/app/' in normalized:
            methods = []
            for m in self.ROUTE_HANDLER_PATTERN.finditer(content):
                methods.append(m.group(1))
            for m in self.ROUTE_HANDLER_ARROW.finditer(content):
                methods.append(m.group(1))

            if methods:
                route_path = self._infer_route_path(normalized, is_api=True)
                dynamic_params = self.DYNAMIC_SEGMENT.findall(normalized)

                handler = NextRouteHandlerInfo(
                    file=file_path,
                    line_number=1,
                    route_path=route_path,
                    http_methods=list(set(methods)),
                    is_edge=bool(self.EDGE_RUNTIME.search(content)),
                    is_streaming=bool(self.STREAMING_PATTERN.search(content)),
                    has_auth=bool(self.AUTH_PATTERN.search(content)),
                    has_cors=bool(self.CORS_PATTERN.search(content)),
                    has_rate_limiting=bool(self.RATE_LIMIT_PATTERN.search(content)),
                    dynamic_params=dynamic_params,
                    uses_cookies=bool(self.COOKIES_PATTERN.search(content)),
                    uses_headers=bool(self.HEADERS_PATTERN.search(content)),
                    uses_next_request=bool(self.NEXT_REQUEST.search(content)),
                )
                route_handlers.append(handler)

        # ── Pages Router API routes (pages/api/**) ───────────────
        elif '/pages/api/' in normalized:
            methods = []
            for m in self.PAGES_METHOD_CHECK.finditer(content):
                methods.append(m.group(1))

            if not methods:
                # Default handler usually handles all methods
                if self.PAGES_API_HANDLER.search(content):
                    methods = ["ALL"]

            route_path = self._infer_api_route_path(normalized)
            dynamic_params = self.DYNAMIC_SEGMENT.findall(normalized)

            api_route = NextAPIRouteInfo(
                name=basename.split('.')[0],
                file=file_path,
                line_number=1,
                route_path=route_path,
                http_methods=methods,
                is_dynamic=len(dynamic_params) > 0,
                dynamic_params=dynamic_params,
                has_auth=bool(self.AUTH_PATTERN.search(content)),
                has_validation=bool(re.search(r'zod|yup|joi|validate', content, re.IGNORECASE)),
                has_cors=bool(self.CORS_PATTERN.search(content)),
            )
            api_routes.append(api_route)

        # ── Middleware detection ──────────────────────────────────
        if basename.startswith('middleware.') or self.MIDDLEWARE_EXPORT.search(content):
            matcher_paths = []
            matcher_match = self.MIDDLEWARE_MATCHER.search(content)
            if matcher_match:
                raw = matcher_match.group(1)
                # Extract path strings
                matcher_paths = re.findall(r"['\"]([^'\"]+)['\"]", raw)

            mw = NextMiddlewareInfo(
                file=file_path,
                line_number=1,
                matcher_paths=matcher_paths,
                has_auth_check=bool(self.AUTH_PATTERN.search(content)),
                has_redirect=bool(re.search(r'NextResponse\.redirect|redirect\(', content)),
                has_rewrite=bool(re.search(r'NextResponse\.rewrite|rewrite\(', content)),
                has_headers=bool(self.HEADERS_PATTERN.search(content)),
                has_cookies=bool(self.COOKIES_PATTERN.search(content)),
                uses_next_response=bool(self.NEXT_RESPONSE.search(content)),
            )
            middleware_list.append(mw)

        return {
            "route_handlers": route_handlers,
            "api_routes": api_routes,
            "middleware": middleware_list,
            "rewrites": rewrites,
            "redirects": redirects,
        }

    def _infer_route_path(self, file_path: str, is_api: bool = False) -> str:
        """Infer API route path from file system path."""
        path = file_path
        if '/app/' in path:
            path = path.split('/app/', 1)[1]
        else:
            return "/api"

        # Remove route.ext
        path = re.sub(r'/?route\.\w+$', '', path)

        # Remove route groups
        path = re.sub(r'\([^)]+\)/?', '', path)

        # Clean up
        path = re.sub(r'/+', '/', path)
        if not path.startswith('/'):
            path = '/' + path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Convert dynamic segments
        path = re.sub(r'\[\.\.\.(\w+)\]', r'*\1', path)
        path = re.sub(r'\[\[\.\.\.(\w+)\]\]', r'*\1?', path)
        path = re.sub(r'\[(\w+)\]', r':\1', path)

        return path if path else "/"

    def _infer_api_route_path(self, file_path: str) -> str:
        """Infer Pages Router API route path."""
        path = file_path
        if '/pages/' in path:
            path = path.split('/pages/', 1)[1]
        else:
            return "/api"

        # Remove extension
        path = re.sub(r'\.\w+$', '', path)

        # Remove index
        path = re.sub(r'/index$', '', path)

        if not path.startswith('/'):
            path = '/' + path

        # Convert dynamic segments
        path = re.sub(r'\[\.\.\.(\w+)\]', r'*\1', path)
        path = re.sub(r'\[(\w+)\]', r':\1', path)

        return path if path else "/"
