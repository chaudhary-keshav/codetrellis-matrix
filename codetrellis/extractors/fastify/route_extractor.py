"""
Fastify Route Extractor - Extracts route definitions and route options.

Supports:
- fastify.get/post/put/delete/patch/options/head/all()
- fastify.route() with options object
- Route shorthand methods
- Route prefixing
- Parameterized routes (:id, :param)
- Wildcard routes
- Async handlers
- Schema-based validation (inline)
- Fastify 3.x through 5.x route patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FastifyRouteInfo:
    """A single Fastify route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
    path: str
    handler: str = "anonymous"
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    has_schema: bool = False
    has_prehandler: bool = False
    has_prevalidation: bool = False
    has_preserialization: bool = False
    prehandler_names: List[str] = field(default_factory=list)
    has_params: bool = False
    param_names: List[str] = field(default_factory=list)
    response_status: int = 0
    constraint: str = ""  # version, host constraints


@dataclass
class FastifyRouteOptionsInfo:
    """Route options from fastify.route({...}) style."""
    method: str = ""
    path: str = ""
    file: str = ""
    line_number: int = 0
    has_schema: bool = False
    has_handler: bool = False
    has_prehandler: bool = False
    has_on_request: bool = False
    has_pre_parsing: bool = False
    has_pre_validation: bool = False
    has_pre_serialization: bool = False
    has_on_send: bool = False
    has_on_response: bool = False
    has_on_timeout: bool = False
    has_on_error: bool = False
    constraint_version: str = ""
    constraint_host: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


class FastifyRouteExtractor:
    """Extracts Fastify route information from source code."""

    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'all'}

    # Shorthand route: fastify.get('/path', opts, handler) or fastify.get('/path', handler)
    SHORTHAND_ROUTE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
        r'[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE
    )

    # fastify.route({...})
    FULL_ROUTE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*route\s*\(\s*\{',
    )

    # Method inside route options: method: 'GET'
    ROUTE_METHOD_PATTERN = re.compile(
        r"method\s*:\s*['\"`](\w+)['\"`]"
    )

    # URL inside route options: url: '/path'
    ROUTE_URL_PATTERN = re.compile(
        r"url\s*:\s*['\"`]([^'\"`]+)['\"`]"
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract route information from Fastify source code."""
        routes: List[FastifyRouteInfo] = []
        route_options: List[FastifyRouteOptionsInfo] = []
        lines = content.split('\n')

        known_receivers = {'fastify', 'app', 'server', 'instance', 'f', 'this'}

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Shorthand routes
            for method in self.HTTP_METHODS:
                match = re.search(
                    rf'(\w+)\s*\.\s*{method}\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                    stripped, re.IGNORECASE
                )
                if match:
                    receiver = match.group(1)
                    path = match.group(2)

                    if receiver.lower() not in known_receivers:
                        continue

                    param_names = re.findall(r':(\w+)', path)
                    is_async = 'async' in stripped

                    # Check for schema/preHandler in the rest of the line or next lines
                    context = '\n'.join(lines[i-1:min(i+10, len(lines))])
                    has_schema = 'schema' in context
                    has_prehandler = 'preHandler' in context or 'onRequest' in context

                    routes.append(FastifyRouteInfo(
                        method=method.upper(),
                        path=path if path.startswith('/') else f'/{path}',
                        handler='anonymous',
                        file=file_path,
                        line_number=i,
                        is_async=is_async,
                        has_schema=has_schema,
                        has_prehandler=has_prehandler,
                        has_params=bool(param_names),
                        param_names=param_names,
                    ))

            # fastify.route({...})
            route_match = self.FULL_ROUTE_PATTERN.search(stripped)
            if route_match:
                receiver = route_match.group(1)
                if receiver.lower() in known_receivers:
                    # Extract route options from the block
                    block = self._extract_block(lines, i - 1)
                    method_match = self.ROUTE_METHOD_PATTERN.search(block)
                    url_match = self.ROUTE_URL_PATTERN.search(block)

                    ro = FastifyRouteOptionsInfo(
                        method=method_match.group(1).upper() if method_match else '',
                        path=url_match.group(1) if url_match else '',
                        file=file_path,
                        line_number=i,
                        has_schema='schema' in block,
                        has_handler='handler' in block,
                        has_prehandler='preHandler' in block,
                        has_on_request='onRequest' in block,
                        has_pre_parsing='preParsing' in block,
                        has_pre_validation='preValidation' in block,
                        has_pre_serialization='preSerialization' in block,
                        has_on_send='onSend' in block,
                        has_on_response='onResponse' in block,
                        has_on_timeout='onTimeout' in block,
                        has_on_error='onError' in block,
                    )

                    # Version constraint
                    ver_match = re.search(r"constraints\s*:.*version\s*:\s*['\"`]([^'\"`]+)['\"`]", block)
                    if ver_match:
                        ro.constraint_version = ver_match.group(1)

                    route_options.append(ro)

                    # Also add as a regular route
                    if ro.method and ro.path:
                        param_names = re.findall(r':(\w+)', ro.path)
                        routes.append(FastifyRouteInfo(
                            method=ro.method,
                            path=ro.path,
                            file=file_path,
                            line_number=i,
                            has_schema=ro.has_schema,
                            has_prehandler=ro.has_prehandler,
                            has_params=bool(param_names),
                            param_names=param_names,
                            constraint=ro.constraint_version,
                        ))

        return {
            "routes": routes,
            "route_options": route_options,
        }

    def _extract_block(self, lines: List[str], start_idx: int, max_lines: int = 40) -> str:
        """Extract a code block starting from a line."""
        body_lines = []
        depth = 0
        started = False
        for j in range(start_idx, min(start_idx + max_lines, len(lines))):
            line = lines[j]
            body_lines.append(line)
            depth += line.count('{') - line.count('}')
            if '{' in line:
                started = True
            if started and depth <= 0:
                break
        return '\n'.join(body_lines)
