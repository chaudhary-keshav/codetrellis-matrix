"""
Vert.x Route Extractor v1.0

Extracts Vert.x HTTP routing patterns including Router, routes, sub-routers, handlers.
Covers Vert.x Web 2.x through 4.x.

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VertxRouteInfo:
    """A Vert.x HTTP route."""
    method: str = ""  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str = ""
    handler: str = ""
    produces: str = ""
    consumes: str = ""
    is_blocking: bool = False
    order: int = -1
    file: str = ""
    line_number: int = 0


@dataclass
class VertxHandlerInfo:
    """A Vert.x route handler or middleware."""
    name: str = ""
    handler_type: str = ""  # body_handler, cors_handler, session_handler, auth_handler, static_handler, custom
    file: str = ""
    line_number: int = 0


@dataclass
class VertxSubRouterInfo:
    """A Vert.x sub-router mount."""
    mount_path: str = ""
    router_var: str = ""
    file: str = ""
    line_number: int = 0


class VertxRouteExtractor:
    """Extracts Vert.x HTTP routes and handler chain patterns."""

    # Router creation
    ROUTER_CREATE_PATTERN = re.compile(
        r'Router\s*\.\s*router\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Route with HTTP method: router.get("/path").handler(...)
    ROUTE_METHOD_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(get|post|put|delete|patch|head|options|route)\s*\(\s*"([^"]*)"',
        re.MULTILINE
    )

    # Route with method() then handler: router.route("/path").method(HttpMethod.GET)
    ROUTE_HTTPMETHOD_PATTERN = re.compile(
        r'(\w+)\s*\.\s*route\s*\(\s*"([^"]*)"(?:\s*\))?\s*\.\s*method\s*\(\s*HttpMethod\s*\.\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Handler attachment: .handler(ctx -> ...) or .handler(this::methodName) or .handler(new SomeHandler())
    HANDLER_PATTERN = re.compile(
        r'\.\s*handler\s*\(\s*(?:this\s*::\s*(\w+)|new\s+(\w+)|(\w+)\s*::\s*(\w+)|(\w+)\s*\.\s*create)',
        re.MULTILINE
    )

    # Sub-router mounting: router.mountSubRouter("/api", subRouter)
    SUBROUTER_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(?:mountSubRouter|route)\s*\(\s*"([^"]*)"(?:\s*,\s*|\s*\)\s*\.\s*subRouter\s*\(\s*)(\w+)',
        re.MULTILINE
    )

    # Built-in handlers
    BODY_HANDLER_PATTERN = re.compile(r'BodyHandler\s*\.\s*create\s*\(', re.MULTILINE)
    CORS_HANDLER_PATTERN = re.compile(r'CorsHandler\s*\.\s*create\s*\(', re.MULTILINE)
    SESSION_HANDLER_PATTERN = re.compile(r'SessionHandler\s*\.\s*create\s*\(', re.MULTILINE)
    STATIC_HANDLER_PATTERN = re.compile(r'StaticHandler\s*\.\s*create\s*\(', re.MULTILINE)
    AUTH_HANDLER_PATTERN = re.compile(r'(?:BasicAuthHandler|JWTAuthHandler|OAuth2AuthHandler|RedirectAuthHandler)\s*\.\s*create\s*\(', re.MULTILINE)
    FAVICON_HANDLER_PATTERN = re.compile(r'FaviconHandler\s*\.\s*create\s*\(', re.MULTILINE)
    TIMEOUT_HANDLER_PATTERN = re.compile(r'TimeoutHandler\s*\.\s*create\s*\(', re.MULTILINE)
    ERROR_HANDLER_PATTERN = re.compile(r'ErrorHandler\s*\.\s*create\s*\(', re.MULTILINE)
    LOGGER_HANDLER_PATTERN = re.compile(r'LoggerHandler\s*\.\s*create\s*\(', re.MULTILINE)
    RESPONSE_TIME_PATTERN = re.compile(r'ResponseTimeHandler\s*\.\s*create\s*\(', re.MULTILINE)

    # produces/consumes
    PRODUCES_PATTERN = re.compile(r'\.produces\s*\(\s*"([^"]+)"', re.MULTILINE)
    CONSUMES_PATTERN = re.compile(r'\.consumes\s*\(\s*"([^"]+)"', re.MULTILINE)
    BLOCKING_HANDLER_PATTERN = re.compile(r'\.blockingHandler\s*\(', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Vert.x routes, handlers, and sub-routers."""
        result = {
            'routes': [],
            'handlers': [],
            'sub_routers': [],
        }

        if not content:
            return result

        # Extract routes with HTTP methods
        for m in self.ROUTE_METHOD_PATTERN.finditer(content):
            method = m.group(2).upper()
            path = m.group(3)
            line = content[:m.start()].count('\n') + 1

            # Check for handler name nearby
            handler = ""
            context = content[m.end():m.end() + 500]
            h_match = self.HANDLER_PATTERN.search(context)
            if h_match:
                handler = h_match.group(1) or h_match.group(2) or \
                          (f"{h_match.group(3)}::{h_match.group(4)}" if h_match.group(3) else "") or \
                          h_match.group(5) or ""

            # Check produces/consumes
            produces = ""
            consumes = ""
            is_blocking = False
            p_match = self.PRODUCES_PATTERN.search(context)
            if p_match:
                produces = p_match.group(1)
            c_match = self.CONSUMES_PATTERN.search(context)
            if c_match:
                consumes = c_match.group(1)
            if self.BLOCKING_HANDLER_PATTERN.search(context):
                is_blocking = True

            if method == "ROUTE":
                method = "*"  # All methods

            result['routes'].append(VertxRouteInfo(
                method=method,
                path=path,
                handler=handler,
                produces=produces,
                consumes=consumes,
                is_blocking=is_blocking,
                file=file_path,
                line_number=line,
            ))

        # Routes with explicit HttpMethod
        for m in self.ROUTE_HTTPMETHOD_PATTERN.finditer(content):
            path = m.group(2)
            method = m.group(3).upper()
            line = content[:m.start()].count('\n') + 1
            result['routes'].append(VertxRouteInfo(
                method=method, path=path, file=file_path, line_number=line,
            ))

        # Extract sub-routers
        for m in self.SUBROUTER_PATTERN.finditer(content):
            mount_path = m.group(2)
            router_var = m.group(3)
            line = content[:m.start()].count('\n') + 1
            result['sub_routers'].append(VertxSubRouterInfo(
                mount_path=mount_path, router_var=router_var,
                file=file_path, line_number=line,
            ))

        # Extract built-in handlers
        handler_patterns = [
            (self.BODY_HANDLER_PATTERN, 'BodyHandler', 'body_handler'),
            (self.CORS_HANDLER_PATTERN, 'CorsHandler', 'cors_handler'),
            (self.SESSION_HANDLER_PATTERN, 'SessionHandler', 'session_handler'),
            (self.STATIC_HANDLER_PATTERN, 'StaticHandler', 'static_handler'),
            (self.AUTH_HANDLER_PATTERN, 'AuthHandler', 'auth_handler'),
            (self.FAVICON_HANDLER_PATTERN, 'FaviconHandler', 'favicon_handler'),
            (self.TIMEOUT_HANDLER_PATTERN, 'TimeoutHandler', 'timeout_handler'),
            (self.ERROR_HANDLER_PATTERN, 'ErrorHandler', 'error_handler'),
            (self.LOGGER_HANDLER_PATTERN, 'LoggerHandler', 'logger_handler'),
            (self.RESPONSE_TIME_PATTERN, 'ResponseTimeHandler', 'response_time_handler'),
        ]
        for pattern, name, handler_type in handler_patterns:
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                result['handlers'].append(VertxHandlerInfo(
                    name=name, handler_type=handler_type,
                    file=file_path, line_number=line,
                ))

        return result
