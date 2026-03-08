"""
TypeScript API Extractor for CodeTrellis

Extracts API/framework patterns from TypeScript source code:
- NestJS controllers, decorators (@Get, @Post, @Controller, @Injectable)
- Express typed routes (Router, RequestHandler)
- Fastify typed routes with schema validation
- tRPC routers and procedures (query, mutation, subscription)
- GraphQL type-graphql resolvers (@Resolver, @Query, @Mutation)
- Angular HttpClient calls and interceptors
- Hono typed routes
- Middleware typed definitions
- WebSocket typed handlers
- gRPC service definitions

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TSRouteInfo:
    """Information about a TypeScript HTTP route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, ALL
    path: str
    handler: str = ""
    file: str = ""
    line_number: int = 0
    framework: str = ""  # nestjs, express, fastify, trpc, hono
    middleware: List[str] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)
    pipes: List[str] = field(default_factory=list)
    interceptors: List[str] = field(default_factory=list)
    is_async: bool = False
    return_type: str = ""
    request_type: str = ""
    response_type: str = ""
    has_validation: bool = False


@dataclass
class TSMiddlewareInfo:
    """Information about middleware definitions."""
    name: str
    file: str = ""
    line_number: int = 0
    type: str = "middleware"  # middleware, guard, interceptor, pipe, filter
    is_global: bool = False
    framework: str = ""
    implements: str = ""  # NestJS interface (CanActivate, NestInterceptor, etc.)


@dataclass
class TSWebSocketInfo:
    """Information about WebSocket event handlers."""
    event: str
    handler: str = ""
    file: str = ""
    line_number: int = 0
    namespace: str = ""
    framework: str = ""  # socket.io, ws, nestjs-gateway


@dataclass
class TSGraphQLResolverInfo:
    """Information about GraphQL resolver definitions."""
    name: str
    resolver_type: str = "Query"  # Query, Mutation, Subscription
    file: str = ""
    line_number: int = 0
    return_type: str = ""
    parent_type: str = ""
    framework: str = ""  # type-graphql, nestjs-graphql, apollo, pothos


@dataclass
class TSTRPCRouterInfo:
    """Information about a tRPC router/procedure."""
    name: str
    procedure_type: str = "query"  # query, mutation, subscription
    file: str = ""
    line_number: int = 0
    input_type: str = ""
    output_type: str = ""
    middleware: List[str] = field(default_factory=list)


class TypeScriptAPIExtractor:
    """
    Extracts API and framework patterns from TypeScript source code.

    Detects:
    - NestJS controllers and route decorators
    - Express typed routes
    - Fastify typed routes
    - tRPC router procedures
    - GraphQL resolvers (type-graphql, NestJS GraphQL)
    - Hono typed routes
    - WebSocket gateways
    """

    # NestJS controller decorator
    NESTJS_CONTROLLER_PATTERN = re.compile(
        r"@Controller\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)",
        re.MULTILINE,
    )

    # NestJS route decorators (@Get, @Post, etc.)
    NESTJS_ROUTE_PATTERN = re.compile(
        r"@(Get|Post|Put|Delete|Patch|All|Head|Options)\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)",
        re.MULTILINE,
    )

    # NestJS injectable
    NESTJS_INJECTABLE_PATTERN = re.compile(
        r"@Injectable\s*\(\s*\)",
        re.MULTILINE,
    )

    # NestJS guards/pipes/interceptors decorators
    NESTJS_GUARD_PATTERN = re.compile(
        r"@UseGuards?\s*\(\s*(\w+)",
        re.MULTILINE,
    )
    NESTJS_PIPE_PATTERN = re.compile(
        r"@UsePipes?\s*\(\s*(\w+)",
        re.MULTILINE,
    )
    NESTJS_INTERCEPTOR_PATTERN = re.compile(
        r"@UseInterceptors?\s*\(\s*(\w+)",
        re.MULTILINE,
    )

    # Express typed route
    EXPRESS_ROUTE_PATTERN = re.compile(
        r"(?:app|router|server)\s*\.\s*(get|post|put|delete|patch|all|use)\s*[<(]\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE,
    )

    # Fastify typed route
    FASTIFY_ROUTE_PATTERN = re.compile(
        r"(?:fastify|app|server)\s*\.\s*(get|post|put|delete|patch|all)\s*(?:<[^>]+>)?\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE,
    )

    # tRPC router / procedure
    # Simple pattern to find procedure declarations — paren balancing done programmatically
    TRPC_PROCEDURE_PATTERN = re.compile(
        r"(\w+)\s*:\s*(?:\w+\.)*\w*[Pp]rocedure\b",
        re.MULTILINE,
    )
    # After finding a procedure, look for the operation type
    TRPC_OPERATION_PATTERN = re.compile(
        r"\.\s*(query|mutation|subscription)\s*\(",
    )

    # GraphQL type-graphql resolvers
    TYPEGRAPHQL_RESOLVER_PATTERN = re.compile(
        r"@(Query|Mutation|Subscription)\s*\(",
        re.MULTILINE,
    )

    # NestJS GraphQL resolver
    NESTJS_GQL_RESOLVER_PATTERN = re.compile(
        r"@(Query|Mutation|Subscription)\s*\([^)]*\)\s*\n\s*(?:async\s+)?(\w+)",
        re.MULTILINE,
    )

    # Hono route
    HONO_ROUTE_PATTERN = re.compile(
        r"(?:app|hono)\s*\.\s*(get|post|put|delete|patch|all)\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE,
    )

    # WebSocket gateway (NestJS)
    WEBSOCKET_GATEWAY_PATTERN = re.compile(
        r"@WebSocketGateway\s*\(",
        re.MULTILINE,
    )
    WEBSOCKET_EVENT_PATTERN = re.compile(
        r"@SubscribeMessage\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Middleware class pattern (implements NestMiddleware, CanActivate, etc.)
    MIDDLEWARE_IMPL_PATTERN = re.compile(
        r"class\s+(\w+)\s+implements\s+(NestMiddleware|CanActivate|NestInterceptor|PipeTransform|ExceptionFilter)",
        re.MULTILINE,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all API patterns from TypeScript source code.

        Returns dict with keys: routes, middleware, websockets, graphql_resolvers, trpc_routers
        """
        routes = []
        middleware = []
        websockets = []
        graphql_resolvers = []
        trpc_routers = []

        # NestJS controller routes
        controller_prefix = ""
        ctrl_match = self.NESTJS_CONTROLLER_PATTERN.search(content)
        if ctrl_match:
            controller_prefix = ctrl_match.group(1)

        for match in self.NESTJS_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            full_path = f"/{controller_prefix}/{path}".replace('//', '/') if controller_prefix else f"/{path}"
            line_num = content[:match.start()].count('\n') + 1

            # Look for handler name on next line
            handler = ""
            next_lines = content[match.end():match.end() + 200]
            handler_match = re.search(r'(?:async\s+)?(\w+)\s*\(', next_lines)
            if handler_match:
                handler = handler_match.group(1)

            # Look for guards/pipes/interceptors nearby
            guards = [m.group(1) for m in self.NESTJS_GUARD_PATTERN.finditer(content[max(0, match.start()-200):match.end()])]
            pipes = [m.group(1) for m in self.NESTJS_PIPE_PATTERN.finditer(content[max(0, match.start()-200):match.end()])]
            interceptors = [m.group(1) for m in self.NESTJS_INTERCEPTOR_PATTERN.finditer(content[max(0, match.start()-200):match.end()])]

            routes.append(TSRouteInfo(
                method=method,
                path=full_path.rstrip('/') or '/',
                handler=handler,
                file=file_path,
                line_number=line_num,
                framework="nestjs",
                guards=guards,
                pipes=pipes,
                interceptors=interceptors,
                has_validation=bool(pipes),
            ))

        # Express typed routes
        for match in self.EXPRESS_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            if method == 'USE':
                method = 'ALL'
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            routes.append(TSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework="express",
            ))

        # Fastify routes
        for match in self.FASTIFY_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            routes.append(TSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework="fastify",
            ))

        # Hono routes
        for match in self.HONO_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            routes.append(TSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework="hono",
            ))

        # tRPC routers — use programmatic paren-balancing to avoid ReDoS
        for match in self.TRPC_PROCEDURE_PATTERN.finditer(content):
            name = match.group(1)
            # Skip common false-positive words
            if name in ('const', 'let', 'var', 'type', 'interface', 'export', 'import', 'return', 'async', 'function'):
                continue
            # Scan forward from the end of the procedure match to find .query/.mutation/.subscription
            # We need to skip over any chained .input(...) calls with arbitrarily nested parens
            search_start = match.end()
            search_region = content[search_start:search_start + 2000]  # limit search window
            pos = 0
            found_op = None
            while pos < len(search_region):
                ch = search_region[pos]
                if ch == '(':
                    # Skip balanced parens
                    depth = 1
                    pos += 1
                    while pos < len(search_region) and depth > 0:
                        if search_region[pos] == '(':
                            depth += 1
                        elif search_region[pos] == ')':
                            depth -= 1
                        pos += 1
                    continue
                # Check for .query( / .mutation( / .subscription(
                if ch == '.':
                    op_match = self.TRPC_OPERATION_PATTERN.match(search_region, pos)
                    if op_match:
                        found_op = op_match.group(1)
                        break
                # Stop at boundaries that indicate we've left the procedure chain
                if ch in (';', '}') and search_region[max(0, pos-1):pos+1] != '};':
                    break
                pos += 1

            if found_op:
                line_num = content[:match.start()].count('\n') + 1
                trpc_routers.append(TSTRPCRouterInfo(
                    name=name,
                    procedure_type=found_op,
                    file=file_path,
                    line_number=line_num,
                ))

        # GraphQL resolvers (type-graphql / NestJS GraphQL)
        for match in self.NESTJS_GQL_RESOLVER_PATTERN.finditer(content):
            resolver_type = match.group(1)
            name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            graphql_resolvers.append(TSGraphQLResolverInfo(
                name=name,
                resolver_type=resolver_type,
                file=file_path,
                line_number=line_num,
                framework="nestjs-graphql" if '@Resolver' in content else "type-graphql",
            ))

        # For type-graphql without method name on next line
        if not graphql_resolvers:
            for match in self.TYPEGRAPHQL_RESOLVER_PATTERN.finditer(content):
                resolver_type = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                next_lines = content[match.end():match.end() + 200]
                name_match = re.search(r'(?:async\s+)?(\w+)\s*\(', next_lines)
                name = name_match.group(1) if name_match else "unknown"

                graphql_resolvers.append(TSGraphQLResolverInfo(
                    name=name,
                    resolver_type=resolver_type,
                    file=file_path,
                    line_number=line_num,
                    framework="type-graphql",
                ))

        # WebSocket events (NestJS gateway)
        for match in self.WEBSOCKET_EVENT_PATTERN.finditer(content):
            event = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find handler name
            handler = ""
            next_lines = content[match.end():match.end() + 200]
            handler_match = re.search(r'(?:async\s+)?(\w+)\s*\(', next_lines)
            if handler_match:
                handler = handler_match.group(1)

            websockets.append(TSWebSocketInfo(
                event=event,
                handler=handler,
                file=file_path,
                line_number=line_num,
                framework="nestjs-gateway",
            ))

        # Middleware implementations
        for match in self.MIDDLEWARE_IMPL_PATTERN.finditer(content):
            name = match.group(1)
            implements = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            type_map = {
                'NestMiddleware': 'middleware',
                'CanActivate': 'guard',
                'NestInterceptor': 'interceptor',
                'PipeTransform': 'pipe',
                'ExceptionFilter': 'filter',
            }

            middleware.append(TSMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                type=type_map.get(implements, 'middleware'),
                framework="nestjs",
                implements=implements,
            ))

        return {
            'routes': routes,
            'middleware': middleware,
            'websockets': websockets,
            'graphql_resolvers': graphql_resolvers,
            'trpc_routers': trpc_routers,
        }
