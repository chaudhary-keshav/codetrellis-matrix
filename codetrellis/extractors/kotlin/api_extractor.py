"""
KotlinAPIExtractor - Extracts Kotlin API endpoint definitions.

Extracts:
- Ktor routing DSL endpoints (get, post, put, delete, patch, head, options)
- Ktor route grouping (route("/path") { ... })
- Spring MVC/WebFlux annotations (@GetMapping, @PostMapping, etc.)
- Ktor WebSocket endpoints
- GraphQL endpoints (DGS, GraphQL Kotlin)
- gRPC service implementations
- Multiplatform API declarations (expect/actual)
- Compose for Web routes (if applicable)

Part of CodeTrellis v4.21 - Kotlin Language Support Upgrade
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KotlinEndpointInfo:
    """Information about a Kotlin API endpoint."""
    method: str = ""  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, WS
    path: str = ""
    handler_name: str = ""
    framework: str = ""  # ktor, spring, quarkus, micronaut
    controller_class: str = ""
    annotations: List[str] = field(default_factory=list)
    parameters: List[Dict[str, str]] = field(default_factory=list)
    consumes: str = ""
    produces: str = ""
    auth_required: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinWebSocketInfo:
    """Information about a Kotlin WebSocket endpoint."""
    path: str = ""
    handler_name: str = ""
    framework: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinGRPCServiceInfo:
    """Information about a Kotlin gRPC service implementation."""
    name: str = ""
    service_name: str = ""
    methods: List[str] = field(default_factory=list)
    is_coroutine: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinGraphQLInfo:
    """Information about a Kotlin GraphQL resolver/type."""
    name: str = ""
    kind: str = ""  # query, mutation, subscription, type, input, scalar
    fields: List[str] = field(default_factory=list)
    framework: str = ""  # dgs, graphql-kotlin, kgraphql
    file: str = ""
    line_number: int = 0


class KotlinAPIExtractor:
    """
    Extracts Kotlin API endpoint definitions from source code.

    Handles:
    - Ktor routing DSL (get/post/put/delete/patch/head/options)
    - Ktor route grouping with prefix resolution
    - Spring MVC/WebFlux annotations
    - Ktor WebSocket endpoints
    - GraphQL resolvers (DGS, GraphQL Kotlin, KGraphQL)
    - gRPC Kotlin service implementations
    - Authentication/Authorization annotations
    """

    # Ktor route patterns
    KTOR_ROUTE_PATTERN = re.compile(
        r'(get|post|put|delete|patch|head|options)\s*\(\s*"([^"]*)"',
        re.MULTILINE
    )

    # Ktor route grouping
    KTOR_ROUTE_GROUP_PATTERN = re.compile(
        r'route\s*\(\s*"([^"]+)"\s*\)\s*\{',
        re.MULTILINE
    )

    # Ktor WebSocket
    KTOR_WEBSOCKET_PATTERN = re.compile(
        r'webSocket\s*\(\s*"([^"]+)"\s*\)',
        re.MULTILINE
    )

    # Spring annotations
    SPRING_MAPPING_PATTERN = re.compile(
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?"([^"]*)"',
        re.MULTILINE
    )

    # Spring @RequestMapping with method=
    SPRING_REQUEST_MAPPING_METHOD = re.compile(
        r'@RequestMapping\s*\([^)]*method\s*=\s*\[?\s*RequestMethod\.(\w+)',
        re.MULTILINE
    )

    # Controller class
    SPRING_CONTROLLER_PATTERN = re.compile(
        r'@(?:RestController|Controller)\s*(?:\([^)]*\))?\s*'
        r'(?:@RequestMapping\s*\(\s*"([^"]*)"\s*\)\s*)?'
        r'class\s+(\w+)',
        re.MULTILINE
    )

    # GraphQL Kotlin patterns
    GRAPHQL_KOTLIN_QUERY = re.compile(
        r'class\s+(\w+)\s*:\s*(?:Query|Mutation|Subscription)\s*(?:\([^)]*\))?\s*\{',
        re.MULTILINE
    )

    # DGS patterns
    DGS_RESOLVER_PATTERN = re.compile(
        r'@Dgs(?:Query|Mutation|Subscription|Data)\s*(?:\([^)]*\))?\s*'
        r'(?:suspend\s+)?fun\s+(\w+)',
        re.MULTILINE
    )

    # gRPC Kotlin service
    GRPC_SERVICE_PATTERN = re.compile(
        r'class\s+(\w+)\s*(?:\([^)]*\))?\s*:\s*(\w+)GrpcKt\.(\w+)CoroutineImplBase\s*\(',
        re.MULTILINE
    )

    # Alternative gRPC pattern
    GRPC_SERVICE_ALT = re.compile(
        r'class\s+(\w+)\s*:\s*(\w+)Grpc\.\w+ImplBase\s*\(',
        re.MULTILINE
    )

    # gRPC method override
    GRPC_METHOD_PATTERN = re.compile(
        r'override\s+(?:suspend\s+)?fun\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Ktor authenticate block
    KTOR_AUTH_PATTERN = re.compile(
        r'authenticate\s*\(\s*(?:"([^"]+)")?\s*\)\s*\{',
        re.MULTILINE
    )

    # Micronaut controller
    MICRONAUT_CONTROLLER_PATTERN = re.compile(
        r'@Controller\s*\(\s*"([^"]*)"\s*\)\s*'
        r'(?:open\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # Micronaut endpoint annotations
    MICRONAUT_ENDPOINT_PATTERN = re.compile(
        r'@(Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*(?:value\s*=\s*)?"([^"]*)"',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all API endpoint definitions from Kotlin source code.

        Returns dict with keys: endpoints, websockets, grpc_services, graphql
        """
        result = {
            'endpoints': [],
            'websockets': [],
            'grpc_services': [],
            'graphql': [],
        }

        if not content or not content.strip():
            return result

        # Extract Ktor routes
        self._extract_ktor_routes(content, file_path, result)

        # Extract Spring endpoints
        self._extract_spring_endpoints(content, file_path, result)

        # Extract Micronaut endpoints
        self._extract_micronaut_endpoints(content, file_path, result)

        # Extract WebSocket endpoints
        self._extract_websockets(content, file_path, result)

        # Extract gRPC services
        self._extract_grpc_services(content, file_path, result)

        # Extract GraphQL resolvers
        self._extract_graphql(content, file_path, result)

        return result

    def _extract_ktor_routes(self, content: str, file_path: str,
                              result: Dict[str, Any]):
        """Extract Ktor routing DSL endpoints with route group prefix resolution."""
        # Build route group prefix map
        group_prefixes = self._build_route_group_map(content)

        for match in self.KTOR_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Resolve prefix from enclosing route groups
            full_path = self._resolve_route_prefix(content, match.start(), group_prefixes)
            if full_path:
                path = full_path + path

            # Check if inside authenticate block
            auth_required = self._is_inside_auth_block(content, match.start())

            # Try to determine handler name
            handler_name = self._extract_handler_name(content, match.end())

            result['endpoints'].append(KotlinEndpointInfo(
                method=method,
                path=path,
                handler_name=handler_name,
                framework='ktor',
                auth_required=auth_required,
                file=file_path,
                line_number=line,
            ))

    def _extract_spring_endpoints(self, content: str, file_path: str,
                                   result: Dict[str, Any]):
        """Extract Spring MVC/WebFlux endpoints."""
        # Find controller base path
        controller_info = {}
        for match in self.SPRING_CONTROLLER_PATTERN.finditer(content):
            base_path = match.group(1) or ""
            class_name = match.group(2)
            controller_info[class_name] = base_path

        base_path = ""
        if controller_info:
            base_path = list(controller_info.values())[0]

        # Method mapping annotations
        method_map = {
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'PatchMapping': 'PATCH',
            'RequestMapping': 'ANY',
        }

        for match in self.SPRING_MAPPING_PATTERN.finditer(content):
            annotation = match.group(1)
            path = match.group(2)
            method = method_map.get(annotation, 'ANY')
            line = content[:match.start()].count('\n') + 1

            full_path = base_path + path if base_path else path

            # Find handler function name after annotation
            handler_name = self._find_next_function(content, match.end())

            # Check for auth annotations
            auth_required = self._has_security_annotation(content, match.start())

            result['endpoints'].append(KotlinEndpointInfo(
                method=method,
                path=full_path,
                handler_name=handler_name,
                framework='spring',
                controller_class=list(controller_info.keys())[0] if controller_info else "",
                auth_required=auth_required,
                file=file_path,
                line_number=line,
            ))

    def _extract_micronaut_endpoints(self, content: str, file_path: str,
                                      result: Dict[str, Any]):
        """Extract Micronaut controller endpoints."""
        # Find controller base path
        controller_base = ""
        controller_name = ""
        ctrl_match = self.MICRONAUT_CONTROLLER_PATTERN.search(content)
        if ctrl_match:
            controller_base = ctrl_match.group(1)
            controller_name = ctrl_match.group(2)

        method_map = {
            'Get': 'GET', 'Post': 'POST', 'Put': 'PUT',
            'Delete': 'DELETE', 'Patch': 'PATCH',
            'Head': 'HEAD', 'Options': 'OPTIONS',
        }

        for match in self.MICRONAUT_ENDPOINT_PATTERN.finditer(content):
            annotation = match.group(1)
            path = match.group(2)
            method = method_map.get(annotation, 'ANY')
            line = content[:match.start()].count('\n') + 1

            full_path = controller_base + path if controller_base else path
            handler_name = self._find_next_function(content, match.end())

            result['endpoints'].append(KotlinEndpointInfo(
                method=method,
                path=full_path,
                handler_name=handler_name,
                framework='micronaut',
                controller_class=controller_name,
                file=file_path,
                line_number=line,
            ))

    def _extract_websockets(self, content: str, file_path: str,
                             result: Dict[str, Any]):
        """Extract WebSocket endpoint definitions."""
        for match in self.KTOR_WEBSOCKET_PATTERN.finditer(content):
            path = match.group(1)
            line = content[:match.start()].count('\n') + 1
            result['websockets'].append(KotlinWebSocketInfo(
                path=path,
                framework='ktor',
                file=file_path,
                line_number=line,
            ))

    def _extract_grpc_services(self, content: str, file_path: str,
                                result: Dict[str, Any]):
        """Extract gRPC service implementations."""
        # Kotlin gRPC coroutine services
        for match in self.GRPC_SERVICE_PATTERN.finditer(content):
            class_name = match.group(1)
            service_name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Find body and extract overridden methods
            body = self._extract_body(content, content.find('{', match.end()))
            methods = [m.group(1) for m in self.GRPC_METHOD_PATTERN.finditer(body)]

            result['grpc_services'].append(KotlinGRPCServiceInfo(
                name=class_name,
                service_name=service_name,
                methods=methods,
                is_coroutine=True,
                file=file_path,
                line_number=line,
            ))

        # Alternative gRPC pattern
        for match in self.GRPC_SERVICE_ALT.finditer(content):
            class_name = match.group(1)
            service_name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            body = self._extract_body(content, content.find('{', match.end()))
            methods = [m.group(1) for m in self.GRPC_METHOD_PATTERN.finditer(body)]

            result['grpc_services'].append(KotlinGRPCServiceInfo(
                name=class_name,
                service_name=service_name,
                methods=methods,
                is_coroutine='suspend' in body[:200],
                file=file_path,
                line_number=line,
            ))

    def _extract_graphql(self, content: str, file_path: str,
                          result: Dict[str, Any]):
        """Extract GraphQL resolvers and types."""
        # GraphQL Kotlin Query/Mutation/Subscription classes
        for match in self.GRAPHQL_KOTLIN_QUERY.finditer(content):
            class_name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            body = self._extract_body(content, match.end() - 1)
            methods = re.findall(r'(?:suspend\s+)?fun\s+(\w+)', body)

            kind = 'query'
            before = content[max(0, match.start() - 20):match.start()]
            if 'Mutation' in content[match.start():match.end()]:
                kind = 'mutation'
            elif 'Subscription' in content[match.start():match.end()]:
                kind = 'subscription'

            result['graphql'].append(KotlinGraphQLInfo(
                name=class_name,
                kind=kind,
                fields=methods,
                framework='graphql-kotlin',
                file=file_path,
                line_number=line,
            ))

        # DGS resolvers
        for match in self.DGS_RESOLVER_PATTERN.finditer(content):
            method_name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            annotation_text = content[match.start():match.end()]

            kind = 'query'
            if 'DgsMutation' in annotation_text:
                kind = 'mutation'
            elif 'DgsSubscription' in annotation_text:
                kind = 'subscription'
            elif 'DgsData' in annotation_text:
                kind = 'data'

            result['graphql'].append(KotlinGraphQLInfo(
                name=method_name,
                kind=kind,
                framework='dgs',
                file=file_path,
                line_number=line,
            ))

    def _build_route_group_map(self, content: str) -> List[Dict]:
        """Build a map of route group positions and their prefixes."""
        groups = []
        for match in self.KTOR_ROUTE_GROUP_PATTERN.finditer(content):
            prefix = match.group(1)
            start = match.start()
            brace_pos = content.find('{', match.end() - 1)
            body_end = self._find_matching_brace(content, brace_pos)
            groups.append({
                'prefix': prefix,
                'start': start,
                'brace_start': brace_pos,
                'brace_end': body_end,
            })
        return groups

    def _resolve_route_prefix(self, content: str, pos: int,
                               groups: List[Dict]) -> str:
        """Resolve the route prefix for a position based on enclosing route groups."""
        prefix_parts = []
        for group in groups:
            if group['brace_start'] < pos < group['brace_end']:
                prefix_parts.append(group['prefix'])

        return ''.join(prefix_parts)

    def _is_inside_auth_block(self, content: str, pos: int) -> bool:
        """Check if position is inside an authenticate { } block."""
        before = content[:pos]
        # Simple heuristic: count authenticate { and } pairs
        auth_matches = list(self.KTOR_AUTH_PATTERN.finditer(before))
        if not auth_matches:
            return False
        last_auth = auth_matches[-1]
        after_auth = content[last_auth.start():pos]
        opens = after_auth.count('{')
        closes = after_auth.count('}')
        return opens > closes

    def _extract_handler_name(self, content: str, pos: int) -> str:
        """Extract handler function name after a route definition."""
        # Look for call { ... } block or function reference
        rest = content[pos:pos + 200]
        # Check for named function reference
        func_ref = re.search(r'\b(\w+)\s*$', rest.split('\n')[0] if '\n' in rest else rest)
        if func_ref and func_ref.group(1) not in ('call', 'null', 'it'):
            return func_ref.group(1)
        return ""

    def _find_next_function(self, content: str, pos: int) -> str:
        """Find the next function name after a position."""
        rest = content[pos:pos + 300]
        match = re.search(r'(?:suspend\s+)?fun\s+(\w+)', rest)
        return match.group(1) if match else ""

    def _has_security_annotation(self, content: str, pos: int) -> bool:
        """Check if there's a security annotation near a position."""
        before = content[max(0, pos - 300):pos]
        security_patterns = [
            '@PreAuthorize', '@Secured', '@RolesAllowed',
            '@Authenticated', '@RequiresPermission',
        ]
        return any(p in before for p in security_patterns)

    def _extract_body(self, content: str, brace_pos: int) -> str:
        """Extract body from opening brace to matching closing brace."""
        if brace_pos < 0 or brace_pos >= len(content) or content[brace_pos] != '{':
            return ""
        depth = 0
        i = brace_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_pos + 1:i]
            elif content[i] == '"':
                i += 1
                while i < len(content) and content[i] != '"':
                    if content[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        return content[brace_pos + 1:]

    def _find_matching_brace(self, content: str, brace_pos: int) -> int:
        """Find the position of the matching closing brace."""
        if brace_pos < 0 or brace_pos >= len(content):
            return len(content)
        depth = 0
        i = brace_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            elif content[i] == '"':
                i += 1
                while i < len(content) and content[i] != '"':
                    if content[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        return len(content)
