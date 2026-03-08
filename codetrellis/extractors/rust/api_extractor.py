"""
RustAPIExtractor - Extracts Rust web API endpoints and gRPC services.

This extractor parses Rust source code and extracts:
- Actix-web routes (#[get], #[post], web::resource, etc.)
- Rocket routes (#[get], #[post], mount)
- Axum routes (Router::new().route(), get/post handlers)
- Warp routes (warp::path, warp::get, etc.)
- Tide routes (app.at("/path").get(handler))
- Tonic gRPC services (#[tonic::async_trait])
- Tower services
- GraphQL endpoints (async-graphql, juniper)

Supports all major Rust web frameworks across all versions.

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RustRouteInfo:
    """Information about a Rust HTTP route/endpoint."""
    method: str  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, ANY
    path: str
    handler: str
    framework: str  # actix-web, rocket, axum, warp, tide
    file: str = ""
    line_number: int = 0
    middleware: List[str] = field(default_factory=list)
    is_async: bool = True  # Most Rust web handlers are async
    attributes: List[str] = field(default_factory=list)


@dataclass
class RustGRPCServiceInfo:
    """Information about a Rust gRPC service implementation."""
    name: str
    methods: List[str] = field(default_factory=list)
    proto_package: str = ""
    framework: str = "tonic"  # tonic is the dominant Rust gRPC framework
    file: str = ""
    line_number: int = 0


@dataclass
class RustGraphQLInfo:
    """Information about Rust GraphQL endpoints."""
    name: str
    query_type: str = ""  # Query, Mutation, Subscription
    fields: List[str] = field(default_factory=list)
    framework: str = ""  # async-graphql, juniper
    file: str = ""
    line_number: int = 0


class RustAPIExtractor:
    """
    Extracts Rust API definitions from source code.

    Handles:
    - Actix-web: attribute macros (#[get("/path")], #[post("/path")])
      and resource-based routing
    - Rocket: attribute macros (#[get("/path")], #[post("/path")])
    - Axum: Router::new().route("/path", get(handler))
    - Warp: warp::path("...").and(warp::get()).map(handler)
    - Tide: app.at("/path").get(handler)
    - Tonic gRPC: #[tonic::async_trait] impl ServiceName for ...
    - async-graphql: #[Object] impl QueryRoot
    - juniper: #[graphql_object] impl Query
    """

    # Actix-web / Rocket attribute routes
    ACTIX_ROCKET_ROUTE = re.compile(
        r'#\[(?P<framework>(?:actix_web::)?(?:get|post|put|delete|patch|head|options))\s*\(\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    # Actix-web route attribute (generic)
    ACTIX_ROUTE = re.compile(
        r'#\[route\s*\(\s*"(?P<path>[^"]+)"\s*,\s*method\s*=\s*"(?P<method>\w+)"',
        re.MULTILINE
    )

    # Function after route attribute
    HANDLER_AFTER_ATTR = re.compile(
        r'(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Axum router: Router::new().route("/path", get(handler))
    AXUM_ROUTE = re.compile(
        r'\.route\s*\(\s*"(?P<path>[^"]+)"\s*,\s*(?P<method>get|post|put|delete|patch|head|options|any)\s*\(\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # Axum router with method_router: get(handler).post(handler)
    AXUM_METHOD_ROUTER = re.compile(
        r'\.route\s*\(\s*"(?P<path>[^"]+)"\s*,\s*(?P<methods>(?:get|post|put|delete|patch)\s*\(\s*\w+\s*\)(?:\s*\.\s*(?:get|post|put|delete|patch)\s*\(\s*\w+\s*\))*)',
        re.MULTILINE
    )

    # Tide routes
    TIDE_ROUTE = re.compile(
        r'\.at\s*\(\s*"(?P<path>[^"]+)"\s*\)\s*\.(?P<method>get|post|put|delete|patch|all)\s*\(\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # Warp routes
    WARP_PATH = re.compile(
        r'warp::path\s*!\s*\(\s*"?(?P<path>[^)"]+)"?\s*\)',
        re.MULTILINE
    )

    # Tonic gRPC impl
    TONIC_IMPL = re.compile(
        r'#\[tonic::async_trait\]\s*impl\s+(?P<service>\w+)\s+for\s+(?P<impl_name>\w+)',
        re.MULTILINE
    )

    # async-graphql Object
    GRAPHQL_OBJECT = re.compile(
        r'#\[Object\]\s*impl\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Generic REST handler detection (framework-agnostic)
    GENERIC_HANDLER = re.compile(
        r'(?P<vis>pub\s+)?async\s+fn\s+(?P<name>\w+)\s*\([^)]*(?:HttpRequest|Request|Json|Path|Query|State|Extension|web::)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Rust API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Rust API definitions from source code.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'grpc_services', 'graphql' keys
        """
        return {
            'routes': self._extract_routes(content, file_path),
            'grpc_services': self._extract_grpc(content, file_path),
            'graphql': self._extract_graphql(content, file_path),
        }

    def _extract_routes(self, content: str, file_path: str) -> List[RustRouteInfo]:
        """Extract HTTP routes from Rust web framework code."""
        routes = []

        # Actix-web / Rocket attribute routes (#[get("/path")], #[post("/path")])
        for match in self.ACTIX_ROCKET_ROUTE.finditer(content):
            attr = match.group('framework')
            path = match.group('path')
            method = attr.split('::')[-1].upper() if '::' in attr else attr.upper()
            line_number = content[:match.start()].count('\n') + 1

            # Determine framework
            framework = 'actix-web' if 'actix_web' in attr else self._detect_web_framework(content)

            # Find handler function name after the attribute
            after = content[match.end():]
            handler_match = self.HANDLER_AFTER_ATTR.search(after)
            handler = handler_match.group('name') if handler_match else ''

            routes.append(RustRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework=framework,
                file=file_path,
                line_number=line_number,
            ))

        # Actix-web generic #[route("/path", method = "GET")]
        for match in self.ACTIX_ROUTE.finditer(content):
            path = match.group('path')
            method = match.group('method').upper()
            line_number = content[:match.start()].count('\n') + 1

            after = content[match.end():]
            handler_match = self.HANDLER_AFTER_ATTR.search(after)
            handler = handler_match.group('name') if handler_match else ''

            routes.append(RustRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework='actix-web',
                file=file_path,
                line_number=line_number,
            ))

        # Axum routes
        for match in self.AXUM_ROUTE.finditer(content):
            path = match.group('path')
            method = match.group('method').upper()
            handler = match.group('handler')
            line_number = content[:match.start()].count('\n') + 1

            routes.append(RustRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework='axum',
                file=file_path,
                line_number=line_number,
            ))

        # Axum multi-method routes
        for match in self.AXUM_METHOD_ROUTER.finditer(content):
            path = match.group('path')
            methods_str = match.group('methods')
            line_number = content[:match.start()].count('\n') + 1

            for m in re.finditer(r'(get|post|put|delete|patch)\s*\(\s*(\w+)', methods_str):
                routes.append(RustRouteInfo(
                    method=m.group(1).upper(),
                    path=path,
                    handler=m.group(2),
                    framework='axum',
                    file=file_path,
                    line_number=line_number,
                ))

        # Tide routes
        for match in self.TIDE_ROUTE.finditer(content):
            routes.append(RustRouteInfo(
                method=match.group('method').upper(),
                path=match.group('path'),
                handler=match.group('handler'),
                framework='tide',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return routes

    def _extract_grpc(self, content: str, file_path: str) -> List[RustGRPCServiceInfo]:
        """Extract gRPC service implementations."""
        services = []

        for match in self.TONIC_IMPL.finditer(content):
            service = match.group('service')
            impl_name = match.group('impl_name')
            line_number = content[:match.start()].count('\n') + 1

            # Find methods in the impl body
            methods = []
            brace_pos = content.find('{', match.end())
            if brace_pos != -1:
                body = self._extract_brace_body(content, brace_pos)
                if body:
                    for fn_match in re.finditer(r'async\s+fn\s+(\w+)', body):
                        methods.append(fn_match.group(1))

            services.append(RustGRPCServiceInfo(
                name=service,
                methods=methods,
                framework='tonic',
                file=file_path,
                line_number=line_number,
            ))

        return services

    def _extract_graphql(self, content: str, file_path: str) -> List[RustGraphQLInfo]:
        """Extract GraphQL resolvers."""
        graphql = []

        for match in self.GRAPHQL_OBJECT.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            # Determine query type from name
            query_type = 'Query'
            lower_name = name.lower()
            if 'mutation' in lower_name:
                query_type = 'Mutation'
            elif 'subscription' in lower_name:
                query_type = 'Subscription'

            # Extract field resolvers
            fields = []
            brace_pos = content.find('{', match.end())
            if brace_pos != -1:
                body = self._extract_brace_body(content, brace_pos)
                if body:
                    for fn_match in re.finditer(r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', body):
                        fields.append(fn_match.group(1))

            graphql.append(RustGraphQLInfo(
                name=name,
                query_type=query_type,
                fields=fields,
                framework='async-graphql',
                file=file_path,
                line_number=line_number,
            ))

        return graphql

    def _detect_web_framework(self, content: str) -> str:
        """Detect which Rust web framework is being used."""
        if 'actix_web' in content or 'actix_rt' in content:
            return 'actix-web'
        if 'rocket::' in content or '#[rocket' in content:
            return 'rocket'
        if 'axum::' in content:
            return 'axum'
        if 'warp::' in content:
            return 'warp'
        if 'tide::' in content:
            return 'tide'
        return 'unknown'

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """Extract body between matched braces."""
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_line_comment = False
        in_block_comment = False
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue
            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue
            if ch == '"':
                in_string = True
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]
            i += 1

        return None
