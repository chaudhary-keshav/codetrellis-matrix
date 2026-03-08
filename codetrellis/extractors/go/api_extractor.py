"""
GoAPIExtractor - Extracts Go API patterns (HTTP handlers, Gin, Echo, gRPC).

This extractor parses Go source code and extracts:
- net/http handler functions (http.HandleFunc)
- Gin router registrations (r.GET, r.POST, etc.)
- Echo router registrations (e.GET, e.POST, etc.)
- Chi router registrations (r.Get, r.Post, etc.)
- Gorilla Mux router registrations (r.HandleFunc)
- gRPC service implementations

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GoRouteInfo:
    """Information about an HTTP route/endpoint."""
    method: str
    path: str
    handler: str
    framework: str = "net/http"  # net/http, gin, echo, chi, gorilla
    file: str = ""
    line_number: int = 0
    middleware: List[str] = field(default_factory=list)


@dataclass
class GoHandlerInfo:
    """Information about an HTTP handler function."""
    name: str
    pattern: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GoGRPCServiceInfo:
    """Information about a gRPC service implementation."""
    name: str
    server_interface: str = ""
    methods: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class GoAPIExtractor:
    """
    Extracts Go API patterns from source code.

    Handles:
    - Standard library net/http handlers
    - Gin framework routes (router.GET, router.POST, etc.)
    - Echo framework routes (e.GET, e.POST, etc.)
    - Chi framework routes (r.Get, r.Post, etc.)
    - Gorilla Mux routes (r.HandleFunc)
    - gRPC service registrations
    """

    HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}

    # net/http patterns
    HANDLE_FUNC_PATTERN = re.compile(
        r'http\.HandleFunc\(\s*"([^"]+)"\s*,\s*(\w+)\s*\)',
    )

    HANDLE_PATTERN = re.compile(
        r'(?:\w+\.)*(?:mux|router|http|serveMux|ServeMux)\.Handle(?:Func)?\(\s*"([^"]+)"\s*,\s*(\w+)',
    )

    # GAP-19: Custom route registration wrappers commonly found in stdlib-based servers
    # Catches: addRoute("/path", label, handler), addRouteWithMetrics("/path", ...)
    ADD_ROUTE_FUNC_PATTERN = re.compile(
        r'(?:addRoute|addRouteWithMetrics|registerRoute|registerHandler)\s*\(\s*"([^"]+)"',
    )

    # Gin patterns: router.GET("/path", handler)
    # v4.9.1: Added Match for broader coverage
    GIN_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Any|Match|Group)\(\s*"([^"]+)"\s*(?:,\s*(\w+(?:\.\w+)?))?',
    )

    # Echo patterns: e.GET("/path", handler)
    ECHO_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Any|Group)\(\s*"([^"]+)"\s*(?:,\s*(\w+(?:\.\w+)?))?',
    )

    # Chi patterns: r.Get("/path", handler)
    CHI_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(Get|Post|Put|Delete|Patch|Head|Options|Route|Group|Mount)\(\s*"([^"]+)"\s*(?:,\s*(\w+(?:\.\w+)?))?',
    )

    # gRPC: RegisterXServiceServer(s, &server{})
    GRPC_REGISTER_PATTERN = re.compile(
        r'Register(\w+)Server\(\s*\w+\s*,\s*[&]?(\w+)',
    )

    # gRPC service interface implementation
    GRPC_IMPL_PATTERN = re.compile(
        r'type\s+(\w+)\s+struct\s*\{[^}]*Unimplemented(\w+)Server',
        re.DOTALL
    )

    # Generic route pattern: any receiver calling method-like HTTP verbs with a path string
    # Catches: router.GET("/path", handler), api.Post("/path", handler), group.Delete("/path", handler)
    # v4.9: Changed [^"]+ to [^"]* to also match empty-path routes like .GET("", handler)
    # v4.9.1: Added Any, Match, Static, StaticFS, StaticFile for broader Gin/Echo coverage (GAP-10, GAP-2)
    GENERIC_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(GET|Get|POST|Post|PUT|Put|DELETE|Delete|PATCH|Patch|HEAD|Head|OPTIONS|Options|Any|ANY|Match|MATCH)\s*\(\s*"([^"]*)"\s*(?:,\s*([^,\n)]+))?',
    )

    # Static file serving patterns: router.Static("/assets", "./public")
    # Catches: StaticFS, Static, StaticFile (Gin-specific)
    STATIC_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(Static|StaticFS|StaticFile|STATIC|STATICFS|STATICFILE)\s*\(\s*"([^"]*)"\s*,\s*([^)]+)\)',
    )

    # Go stdlib handler signature: func name(w http.ResponseWriter, r *http.Request)
    HTTP_HANDLER_SIGNATURE = re.compile(
        r'func\s+(?:\(\s*\w+\s+\*?\w+\s*\)\s+)?(\w+)\s*\([^)]*http\.ResponseWriter[^)]*\*?http\.Request[^)]*\)',
    )

    # PocketBase-style route binding: e.Router.GET/POST/etc or se.Router.AddRoute
    # v4.9: Changed [^"]+ to [^"]* to match empty-path routes
    POCKETBASE_ROUTE_PATTERN = re.compile(
        r'(\w+)\.(?:Router|Group)\s*\(\s*"?([^")\s]*)"?\s*\)\s*\.\s*(GET|Get|POST|Post|PUT|Put|DELETE|Delete|PATCH|Patch)\s*\(\s*"([^"]*)"',
    )

    # AddRoute pattern (various frameworks)
    ADD_ROUTE_PATTERN = re.compile(
        r'\.(?:AddRoute|Route|Add)\s*\(\s*(?:"(GET|POST|PUT|DELETE|PATCH)"\s*,\s*)?"([^"]+)"\s*,\s*(\w+(?:\.\w+)?)',
    )

    # Route group assignment: sub := rg.Group("/prefix")
    GROUP_ASSIGN_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*\w+\.Group\s*\(\s*"([^"]*)"',
    )

    def __init__(self):
        """Initialize the Go API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API patterns from Go source code.

        Args:
            content: Go source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'handlers', 'grpc_services' keys
        """
        # Detect which framework is in use
        framework = self._detect_framework(content)

        # Build route group prefix map: variable_name -> prefix_path
        group_prefixes = self._build_group_prefix_map(content)

        routes = []
        handlers = []
        grpc_services = []

        # Extract net/http handlers
        routes.extend(self._extract_http_routes(content, file_path))

        # Extract framework-specific routes
        if framework == 'gin':
            routes.extend(self._extract_gin_routes(content, file_path, group_prefixes))
        elif framework == 'echo':
            routes.extend(self._extract_echo_routes(content, file_path, group_prefixes))
        elif framework == 'chi':
            routes.extend(self._extract_chi_routes(content, file_path, group_prefixes))

        # Extract generic routes (catches custom routers like PocketBase)
        routes.extend(self._extract_generic_routes(content, file_path, framework, group_prefixes))

        # Extract HTTP handler functions by signature
        handlers.extend(self._extract_handler_signatures(content, file_path))

        # Extract gRPC services
        grpc_services.extend(self._extract_grpc_services(content, file_path))

        # Deduplicate routes by method+path
        seen = set()
        deduped_routes = []
        for route in routes:
            key = f"{route.method}:{route.path}"
            if key not in seen:
                seen.add(key)
                deduped_routes.append(route)

        return {
            'routes': deduped_routes,
            'handlers': handlers,
            'grpc_services': grpc_services,
            'framework': framework,
        }

    def _build_group_prefix_map(self, content: str) -> Dict[str, str]:
        """
        Build a map of variable names to their route group prefixes.

        Parses patterns like:
            sub := rg.Group("/backups")
            apiGroup := pbRouter.Group("/api")

        Also resolves chained groups:
            apiGroup := pbRouter.Group("/api")
            sub := apiGroup.Group("/backups")  -> sub = "/api/backups"
        """
        group_map: Dict[str, str] = {}

        for match in self.GROUP_ASSIGN_PATTERN.finditer(content):
            var_name = match.group(1)
            prefix = match.group(2)

            # Check if the parent (right side of :=) is also a known group
            # Extract the parent variable name from the full match context
            full_match = match.group(0)
            parent_match = re.search(r'(\w+)\.Group', full_match)
            if parent_match:
                parent_var = parent_match.group(1)
                if parent_var in group_map:
                    prefix = group_map[parent_var] + prefix

            group_map[var_name] = prefix

        return group_map

    def _detect_framework(self, content: str) -> str:
        """Detect which Go web framework is in use."""
        if '"github.com/gin-gonic/gin"' in content:
            return 'gin'
        elif '"github.com/labstack/echo' in content:
            return 'echo'
        elif '"github.com/go-chi/chi' in content:
            return 'chi'
        elif '"github.com/gorilla/mux"' in content:
            return 'gorilla'
        elif '"google.golang.org/grpc"' in content:
            return 'grpc'
        elif '"net/http"' in content:
            return 'net/http'
        return 'unknown'

    def _extract_http_routes(self, content: str, file_path: str) -> List[GoRouteInfo]:
        """Extract standard library net/http routes."""
        routes = []

        for match in self.HANDLE_FUNC_PATTERN.finditer(content):
            path = match.group(1)
            handler = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            routes.append(GoRouteInfo(
                method='ANY',
                path=path,
                handler=handler,
                framework='net/http',
                file=file_path,
                line_number=line_number,
            ))

        for match in self.HANDLE_PATTERN.finditer(content):
            path = match.group(1)
            handler = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            routes.append(GoRouteInfo(
                method='ANY',
                path=path,
                handler=handler,
                framework='net/http',
                file=file_path,
                line_number=line_number,
            ))

        # GAP-19: Custom route registration wrappers (e.g. Caddy's addRoute)
        seen_paths = {r.path for r in routes}
        for match in self.ADD_ROUTE_FUNC_PATTERN.finditer(content):
            path = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            if path in seen_paths:
                continue
            seen_paths.add(path)

            routes.append(GoRouteInfo(
                method='ANY',
                path=path,
                handler='wrapper',
                framework='net/http',
                file=file_path,
                line_number=line_number,
            ))

        return routes

    def _extract_gin_routes(self, content: str, file_path: str, group_prefixes: Dict[str, str] = None) -> List[GoRouteInfo]:
        """Extract Gin framework routes."""
        routes = []
        if group_prefixes is None:
            group_prefixes = {}

        for match in self.GIN_ROUTE_PATTERN.finditer(content):
            receiver = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            handler = match.group(4) or ''
            line_number = content[:match.start()].count('\n') + 1

            if method in self.HTTP_METHODS or method in ('ANY', 'MATCH'):
                # Apply group prefix if the receiver is a known group variable
                full_path = path
                if receiver in group_prefixes:
                    prefix = group_prefixes[receiver]
                    if prefix and not path.startswith(prefix):
                        full_path = prefix + path

                routes.append(GoRouteInfo(
                    method=method if method != 'MATCH' else 'ANY',
                    path=full_path,
                    handler=handler,
                    framework='gin',
                    file=file_path,
                    line_number=line_number,
                ))

        return routes

    def _extract_echo_routes(self, content: str, file_path: str, group_prefixes: Dict[str, str] = None) -> List[GoRouteInfo]:
        """Extract Echo framework routes."""
        routes = []
        if group_prefixes is None:
            group_prefixes = {}

        for match in self.ECHO_ROUTE_PATTERN.finditer(content):
            receiver = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            handler = match.group(4) or ''
            line_number = content[:match.start()].count('\n') + 1

            if method in self.HTTP_METHODS or method == 'ANY':
                full_path = path
                if receiver in group_prefixes:
                    prefix = group_prefixes[receiver]
                    if prefix and not path.startswith(prefix):
                        full_path = prefix + path

                routes.append(GoRouteInfo(
                    method=method,
                    path=full_path,
                    handler=handler,
                    framework='echo',
                    file=file_path,
                    line_number=line_number,
                ))

        return routes

    def _extract_chi_routes(self, content: str, file_path: str, group_prefixes: Dict[str, str] = None) -> List[GoRouteInfo]:
        """Extract Chi framework routes."""
        routes = []
        if group_prefixes is None:
            group_prefixes = {}

        for match in self.CHI_ROUTE_PATTERN.finditer(content):
            receiver = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            handler = match.group(4) or ''
            line_number = content[:match.start()].count('\n') + 1

            # Chi uses CamelCase methods
            method_upper = method.upper()
            if method_upper in self.HTTP_METHODS:
                full_path = path
                if receiver in group_prefixes:
                    prefix = group_prefixes[receiver]
                    if prefix and not path.startswith(prefix):
                        full_path = prefix + path

                routes.append(GoRouteInfo(
                    method=method_upper,
                    path=full_path,
                    handler=handler,
                    framework='chi',
                    file=file_path,
                    line_number=line_number,
                ))

        return routes

    def _extract_grpc_services(self, content: str, file_path: str) -> List[GoGRPCServiceInfo]:
        """Extract gRPC service implementations."""
        results = []

        # Find gRPC service implementations (embedding UnimplementedXServer)
        for match in self.GRPC_IMPL_PATTERN.finditer(content):
            impl_name = match.group(1)
            service_name = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            results.append(GoGRPCServiceInfo(
                name=impl_name,
                server_interface=f'{service_name}Server',
                file=file_path,
                line_number=line_number,
            ))

        return results

    def _extract_generic_routes(self, content: str, file_path: str, known_framework: str,
                               group_prefixes: Dict[str, str] = None) -> List[GoRouteInfo]:
        """
        Extract routes from any router using generic pattern matching.
        This catches custom routers (PocketBase, custom frameworks) that
        use standard HTTP method naming conventions.

        Args:
            group_prefixes: Map of variable names to their route group prefixes.
                           Used to reconstruct full paths like /api/backups/{key}.
        """
        routes = []
        seen = set()
        if group_prefixes is None:
            group_prefixes = {}

        # Generic route pattern: receiver.Method("/path", handler)
        for match in self.GENERIC_ROUTE_PATTERN.finditer(content):
            receiver = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            handler = match.group(4) or 'anonymous'
            handler = handler.strip().rstrip(',').rstrip(')')
            line_number = content[:match.start()].count('\n') + 1

            # Skip if this looks like a known framework call we already captured
            if known_framework in ('gin', 'echo', 'chi'):
                continue

            # Filter: path must look like a URL path (starts with / or : or {)
            # OR be empty (meaning the route is the group root itself)
            # This avoids matching r.Get("Content-Type", ...) as a route
            # v4.9: Allow empty paths — common in Go routers (group.GET("", handler))
            if path == '':
                # Empty path is valid only if receiver is a known group or looks like a router variable
                # The full_path will be the group prefix itself
                pass
            elif not (path.startswith('/') or path.startswith(':') or path.startswith('{')):
                continue

            # Apply group prefix if the receiver is a known group variable
            full_path = path
            if receiver in group_prefixes:
                prefix = group_prefixes[receiver]
                if prefix and not path.startswith(prefix):
                    full_path = prefix + path
            elif path == '':
                # Empty path with unknown receiver — use receiver name as hint
                full_path = f'/{receiver}'

            key = f"{method}:{full_path}"
            if key in seen:
                continue
            seen.add(key)

            if method in self.HTTP_METHODS:
                routes.append(GoRouteInfo(
                    method=method,
                    path=full_path,
                    handler=handler[:50],
                    framework='generic',
                    file=file_path,
                    line_number=line_number,
                ))
            elif method in ('ANY', 'MATCH'):
                # GAP-10: router.Any() matches all HTTP methods
                # GAP-2: router.Match() matches specified methods
                routes.append(GoRouteInfo(
                    method='ANY',
                    path=full_path,
                    handler=handler[:50],
                    framework='generic',
                    file=file_path,
                    line_number=line_number,
                ))

        # GAP-2: Static file serving routes (StaticFS, Static, StaticFile)
        for match in self.STATIC_ROUTE_PATTERN.finditer(content):
            receiver = match.group(1)
            static_method = match.group(2).upper()
            path = match.group(3)
            target = match.group(4).strip().rstrip(')')
            line_number = content[:match.start()].count('\n') + 1

            # Apply group prefix if available
            full_path = path
            if receiver in group_prefixes:
                prefix = group_prefixes[receiver]
                if prefix and not path.startswith(prefix):
                    full_path = prefix + path

            key = f"GET:{full_path}"
            if key in seen:
                continue
            seen.add(key)

            routes.append(GoRouteInfo(
                method='GET',
                path=full_path,
                handler=f'static:{target[:40]}',
                framework='generic',
                file=file_path,
                line_number=line_number,
            ))

        # PocketBase-style nested route patterns
        for match in self.POCKETBASE_ROUTE_PATTERN.finditer(content):
            group_receiver = match.group(1)
            group_path = match.group(2)
            method = match.group(3).upper()
            path = match.group(4)
            line_number = content[:match.start()].count('\n') + 1

            full_path = f"{group_path}{path}" if group_path else path
            key = f"{method}:{full_path}"
            if key in seen:
                continue
            seen.add(key)

            routes.append(GoRouteInfo(
                method=method,
                path=full_path,
                handler=f"{group_receiver}.handler",
                framework='pocketbase',
                file=file_path,
                line_number=line_number,
            ))

        # AddRoute pattern
        for match in self.ADD_ROUTE_PATTERN.finditer(content):
            method = (match.group(1) or 'ANY').upper()
            path = match.group(2)
            handler = match.group(3)
            line_number = content[:match.start()].count('\n') + 1

            # Filter: path must look like a URL path
            if not (path.startswith('/') or path.startswith(':') or path.startswith('{')):
                continue

            key = f"{method}:{path}"
            if key in seen:
                continue
            seen.add(key)

            routes.append(GoRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework='generic',
                file=file_path,
                line_number=line_number,
            ))

        return routes

    def _extract_handler_signatures(self, content: str, file_path: str) -> List[GoHandlerInfo]:
        """Extract functions with HTTP handler signatures."""
        handlers = []

        for match in self.HTTP_HANDLER_SIGNATURE.finditer(content):
            func_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            handlers.append(GoHandlerInfo(
                name=func_name,
                pattern='http.HandlerFunc',
                file=file_path,
                line_number=line_number,
            ))

        return handlers
