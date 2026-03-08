"""
JavaScript API Extractor for CodeTrellis

Extracts API/framework patterns from JavaScript source code:
- Express.js routes (app.get/post/put/delete/patch, Router)
- Fastify routes (fastify.route, fastify.get/post, schema validation)
- Koa routes (koa-router)
- Hapi.js routes (server.route)
- Nest.js-like decorators (if used in JS via Babel/SWC)
- Middleware definitions (app.use, router.use)
- WebSocket handlers (ws, socket.io)
- GraphQL resolvers (Query, Mutation, Subscription)
- REST client calls (fetch, axios)

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSRouteInfo:
    """Information about a JavaScript HTTP route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, ALL
    path: str
    handler: str = ""
    file: str = ""
    line_number: int = 0
    framework: str = "express"  # express, fastify, koa, hapi
    middleware: List[str] = field(default_factory=list)
    is_async: bool = False
    controller: str = ""
    has_validation: bool = False


@dataclass
class JSMiddlewareInfo:
    """Information about middleware definitions."""
    name: str
    file: str = ""
    line_number: int = 0
    type: str = "middleware"  # middleware, error_handler, guard, interceptor
    is_global: bool = False
    framework: str = "express"
    path: str = ""


@dataclass
class JSWebSocketInfo:
    """Information about WebSocket event handlers."""
    event: str
    handler: str = ""
    file: str = ""
    line_number: int = 0
    namespace: str = ""
    framework: str = "ws"  # ws, socket.io, uws


@dataclass
class JSGraphQLResolverInfo:
    """Information about GraphQL resolver definitions."""
    name: str
    resolver_type: str = "Query"  # Query, Mutation, Subscription
    file: str = ""
    line_number: int = 0
    return_type: str = ""
    arguments: List[str] = field(default_factory=list)


class JavaScriptAPIExtractor:
    """
    Extracts API and framework patterns from JavaScript source code.

    Detects:
    - Express.js routes (app.METHOD, Router.METHOD)
    - Fastify routes (fastify.METHOD, fastify.route({...}))
    - Koa routes via koa-router
    - Hapi.js server.route({...})
    - Middleware patterns (app.use, error middleware)
    - WebSocket handlers (ws, socket.io)
    - GraphQL resolvers
    """

    # Express/Koa/Fastify route patterns
    ROUTE_PATTERN = re.compile(
        r"(?:app|router|server|fastify|route(?:r)?)\s*\.\s*"
        r"(get|post|put|delete|patch|all|options|head)\s*\(\s*"
        r"['\"`]([^'\"`]+)['\"`]",
        re.IGNORECASE | re.MULTILINE,
    )

    # Express Router creation
    ROUTER_PATTERN = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*"
        r"(?:express\.Router\(\)|require\(['\"]express['\"]\)\.Router\(\)|"
        r"new\s+(?:express\.)?Router\(\))",
        re.MULTILINE,
    )

    # Hapi.js route registration
    HAPI_ROUTE_PATTERN = re.compile(
        r"server\.route\s*\(\s*\{\s*"
        r"method\s*:\s*['\"](\w+)['\"].*?"
        r"path\s*:\s*['\"]([^'\"]+)['\"]",
        re.DOTALL | re.IGNORECASE,
    )

    # Fastify route with schema
    FASTIFY_ROUTE_PATTERN = re.compile(
        r"fastify\.route\s*\(\s*\{\s*"
        r"method\s*:\s*['\"](\w+)['\"].*?"
        r"url\s*:\s*['\"]([^'\"]+)['\"]",
        re.DOTALL | re.IGNORECASE,
    )

    # Middleware patterns
    MIDDLEWARE_PATTERN = re.compile(
        r"(?:app|router|server)\s*\.\s*use\s*\(\s*"
        r"(?:['\"]([^'\"]+)['\"],\s*)?"
        r"(\w+)",
        re.MULTILINE,
    )

    # Error middleware (Express 4-arg)
    ERROR_MIDDLEWARE_PATTERN = re.compile(
        r"(?:app|router)\s*\.\s*use\s*\(\s*"
        r"(?:async\s+)?\(\s*(?:err|error),\s*req,\s*res,\s*next\s*\)",
        re.MULTILINE,
    )

    # WebSocket event handlers
    WS_EVENT_PATTERN = re.compile(
        r"(?:ws|socket|io|wss|connection)\s*\.\s*on\s*\(\s*"
        r"['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Socket.IO namespace
    SOCKETIO_NS_PATTERN = re.compile(
        r"(?:io|server)\s*\.\s*of\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # GraphQL resolver patterns
    GRAPHQL_RESOLVER_PATTERN = re.compile(
        r"(?:Query|Mutation|Subscription)\s*:\s*\{\s*"
        r"(?:[\s\S]*?)(\w+)\s*(?::\s*(?:async\s+)?\(|\([^)]*\)\s*\{)",
        re.MULTILINE,
    )

    # GraphQL type resolver (individual)
    GRAPHQL_FIELD_PATTERN = re.compile(
        r"(\w+)\s*:\s*\{\s*(?:type|resolve|args)",
        re.MULTILINE,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract API patterns from JavaScript source code.

        Returns dict with keys: routes, middleware, websockets, graphql_resolvers
        """
        routes = self._extract_routes(content, file_path)
        middleware = self._extract_middleware(content, file_path)
        websockets = self._extract_websockets(content, file_path)
        graphql = self._extract_graphql(content, file_path)

        return {
            'routes': routes,
            'middleware': middleware,
            'websockets': websockets,
            'graphql_resolvers': graphql,
        }

    def _extract_routes(self, content: str, file_path: str) -> List[JSRouteInfo]:
        """Extract HTTP route definitions."""
        routes = []
        seen = set()

        # Detect framework
        framework = self._detect_framework(content)

        # Standard Express/Fastify/Koa routes
        for match in self.ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            key = f"{method}:{path}"
            if key in seen:
                continue
            seen.add(key)

            # Check for async handler
            rest = content[match.end():match.end() + 100]
            is_async = bool(re.search(r'async\s', rest))

            routes.append(JSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework=framework,
                is_async=is_async,
            ))

        # Hapi.js routes
        for match in self.HAPI_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            key = f"{method}:{path}"
            if key in seen:
                continue
            seen.add(key)

            routes.append(JSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework='hapi',
            ))

        # Fastify route() objects
        for match in self.FASTIFY_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            key = f"{method}:{path}"
            if key in seen:
                continue
            seen.add(key)

            routes.append(JSRouteInfo(
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
                framework='fastify',
                has_validation=True,
            ))

        return routes

    def _extract_middleware(self, content: str, file_path: str) -> List[JSMiddlewareInfo]:
        """Extract middleware definitions."""
        middleware = []
        seen = set()
        framework = self._detect_framework(content)

        # Standard middleware
        for match in self.MIDDLEWARE_PATTERN.finditer(content):
            path = match.group(1) or ""
            name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            # Skip common non-middleware identifiers
            if name in ('function', 'async', '(', '{'):
                continue

            is_global = not path

            middleware.append(JSMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_global=is_global,
                framework=framework,
                path=path,
            ))

        # Error middleware (4-arg)
        for match in self.ERROR_MIDDLEWARE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            middleware.append(JSMiddlewareInfo(
                name='<error_handler>',
                file=file_path,
                line_number=line_num,
                type='error_handler',
                is_global=True,
                framework=framework,
            ))

        return middleware

    def _extract_websockets(self, content: str, file_path: str) -> List[JSWebSocketInfo]:
        """Extract WebSocket event handlers."""
        websockets = []
        seen = set()

        # Detect WS framework
        ws_framework = 'ws'
        if re.search(r'socket\.io|require\([\'"]socket\.io[\'"]\)|from\s+[\'"]socket\.io[\'"]', content):
            ws_framework = 'socket.io'
        elif re.search(r'uws|uWebSockets', content):
            ws_framework = 'uws'

        for match in self.WS_EVENT_PATTERN.finditer(content):
            event = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            key = f"{event}"
            if key in seen:
                continue
            seen.add(key)

            websockets.append(JSWebSocketInfo(
                event=event,
                file=file_path,
                line_number=line_num,
                framework=ws_framework,
            ))

        # Socket.IO namespaces
        for match in self.SOCKETIO_NS_PATTERN.finditer(content):
            ns = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            websockets.append(JSWebSocketInfo(
                event='<namespace>',
                namespace=ns,
                file=file_path,
                line_number=line_num,
                framework='socket.io',
            ))

        return websockets

    def _extract_graphql(self, content: str, file_path: str) -> List[JSGraphQLResolverInfo]:
        """Extract GraphQL resolver definitions."""
        resolvers = []

        # Detect resolver type blocks
        for resolver_type in ('Query', 'Mutation', 'Subscription'):
            pattern = re.compile(
                rf'{resolver_type}\s*:\s*\{{([^}}]+)\}}',
                re.DOTALL,
            )
            for block_match in pattern.finditer(content):
                body = block_match.group(1)
                line_base = content[:block_match.start()].count('\n') + 1

                # Extract individual resolver fields
                field_pattern = re.compile(r'(\w+)\s*(?::\s*(?:async\s+)?\(|\([^)]*\)\s*(?:=>|\{))', re.MULTILINE)
                for field_match in field_pattern.finditer(body):
                    name = field_match.group(1)
                    if name in ('async', 'function', 'const', 'let', 'var'):
                        continue

                    resolvers.append(JSGraphQLResolverInfo(
                        name=name,
                        resolver_type=resolver_type,
                        file=file_path,
                        line_number=line_base + body[:field_match.start()].count('\n'),
                    ))

        return resolvers

    def _detect_framework(self, content: str) -> str:
        """Detect which HTTP framework is being used."""
        if re.search(r"require\(['\"]fastify['\"]\)|from\s+['\"]fastify['\"]", content):
            return 'fastify'
        if re.search(r"require\(['\"]@hapi/hapi['\"]\)|require\(['\"]hapi['\"]\)|from\s+['\"]@hapi", content):
            return 'hapi'
        if re.search(r"require\(['\"]koa['\"]\)|from\s+['\"]koa['\"]", content):
            return 'koa'
        if re.search(r"require\(['\"]express['\"]\)|from\s+['\"]express['\"]", content):
            return 'express'
        return 'express'  # default
