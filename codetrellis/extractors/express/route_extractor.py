"""
Express.js Route Extractor - Extracts route definitions, parameters, and routers.

Supports Express.js 3.x through 5.x route patterns:
- app.get/post/put/delete/patch/options/head/all()
- Router() instances with .route() chaining
- app.route('/path').get().post()
- app.param() parameter middleware
- Nested routers with app.use('/prefix', router)
- Path patterns: strings, regex, arrays, parameterized (:id, :id?)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ExpressRouteInfo:
    """A single Express route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, ALL
    path: str
    handler: str  # Handler function name or 'anonymous'
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    has_middleware: bool = False
    middleware_count: int = 0
    middleware_names: List[str] = field(default_factory=list)
    has_params: bool = False
    param_names: List[str] = field(default_factory=list)
    is_dynamic: bool = False
    router_name: str = ""  # Which router this belongs to
    response_type: str = ""  # json, send, render, redirect, etc.


@dataclass
class ExpressRouterInfo:
    """An Express Router() instance."""
    name: str
    file: str = ""
    line_number: int = 0
    mount_path: str = ""
    route_count: int = 0
    has_middleware: bool = False
    middleware_names: List[str] = field(default_factory=list)


@dataclass
class ExpressParamInfo:
    """An app.param() or router.param() declaration."""
    param_name: str
    handler: str
    file: str = ""
    line_number: int = 0
    router_name: str = ""


class ExpressRouteExtractor:
    """Extracts Express.js route definitions from source code."""

    # HTTP methods supported by Express
    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'all'}

    # Route definition patterns
    ROUTE_PATTERNS = [
        # app.get('/path', handler) or app.get('/path', middleware, handler)
        re.compile(
            r'(?:^|\n)\s*(?:(\w+)\s*\.)\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
            r'[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        ),
        # app.route('/path').get(handler).post(handler)
        re.compile(
            r'(?:^|\n)\s*(?:(\w+)\s*\.)route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)'
            r'(?:\s*\.\s*(get|post|put|delete|patch|options|head|all)\s*\()',
            re.IGNORECASE
        ),
    ]

    # Router creation patterns
    ROUTER_PATTERNS = [
        # const router = express.Router()
        re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:express\.Router|Router)\s*\(',
        ),
        # export const router = express.Router()
        re.compile(
            r'export\s+(?:const|let|var)\s+(\w+)\s*=\s*(?:express\.Router|Router)\s*\(',
        ),
    ]

    # Router mount patterns
    ROUTER_MOUNT_PATTERNS = [
        # app.use('/prefix', router)
        re.compile(
            r'(\w+)\s*\.\s*use\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(\w+)',
        ),
    ]

    # Param patterns
    PARAM_PATTERNS = [
        re.compile(
            r'(\w+)\s*\.\s*param\s*\(\s*[\'"`](\w+)[\'"`]',
        ),
    ]

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract route information from Express.js source code."""
        routes: List[ExpressRouteInfo] = []
        routers: List[ExpressRouterInfo] = []
        params: List[ExpressParamInfo] = []

        lines = content.split('\n')

        # Extract routers first
        for pattern in self.ROUTER_PATTERNS:
            for match in pattern.finditer(content):
                router_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                routers.append(ExpressRouterInfo(
                    name=router_name,
                    file=file_path,
                    line_number=line_num,
                ))

        # Extract router mount paths
        for pattern in self.ROUTER_MOUNT_PATTERNS:
            for match in pattern.finditer(content):
                app_name = match.group(1)
                mount_path = match.group(2)
                router_ref = match.group(3)
                for router in routers:
                    if router.name == router_ref:
                        router.mount_path = mount_path

        # Extract routes - line-by-line for accurate line numbers
        router_names = {r.name for r in routers}
        known_receivers = router_names | {'app', 'server', 'api', 'express'}

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            for method in self.HTTP_METHODS:
                # Match: receiver.method('path', ...)
                route_match = re.search(
                    rf'(\w+)\s*\.\s*{method}\s*\(\s*[\'"`/]([^\'"`]*)[\'"`]',
                    stripped, re.IGNORECASE
                )
                if route_match:
                    receiver = route_match.group(1)
                    path = route_match.group(2)
                    if receiver.lower() in known_receivers or receiver in router_names:
                        # Determine handler
                        handler = 'anonymous'
                        # Look for named function reference
                        handler_match = re.search(
                            rf'{method}\s*\([^)]*,\s*(\w+)\s*\)',
                            stripped, re.IGNORECASE
                        )
                        if handler_match:
                            handler = handler_match.group(1)

                        # Check for async handler
                        is_async = 'async' in stripped

                        # Count middleware in args
                        args_match = re.search(
                            rf'{method}\s*\((.+)\)',
                            stripped, re.IGNORECASE | re.DOTALL
                        )
                        middleware_count = 0
                        middleware_names = []
                        if args_match:
                            args_str = args_match.group(1)
                            # Count comma-separated args (minus path and handler)
                            parts = [p.strip() for p in args_str.split(',') if p.strip()]
                            if len(parts) > 2:
                                middleware_count = len(parts) - 2
                                middleware_names = [
                                    p.strip().split('(')[0]
                                    for p in parts[1:-1]
                                    if not p.strip().startswith(('(', '{', 'async', 'function'))
                                ]

                        # Extract params from path
                        param_names = re.findall(r':(\w+)', path)

                        # Determine response type
                        response_type = self._detect_response_type(content, i - 1, lines)

                        routes.append(ExpressRouteInfo(
                            method=method.upper(),
                            path=path if path.startswith('/') else f'/{path}',
                            handler=handler,
                            file=file_path,
                            line_number=i,
                            is_async=is_async,
                            has_middleware=middleware_count > 0,
                            middleware_count=middleware_count,
                            middleware_names=middleware_names,
                            has_params=bool(param_names),
                            param_names=param_names,
                            is_dynamic=bool(param_names) or '*' in path,
                            router_name=receiver if receiver in router_names else '',
                            response_type=response_type,
                        ))

        # Extract params
        for pattern in self.PARAM_PATTERNS:
            for match in pattern.finditer(content):
                receiver = match.group(1)
                param_name = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                params.append(ExpressParamInfo(
                    param_name=param_name,
                    handler='paramHandler',
                    file=file_path,
                    line_number=line_num,
                    router_name=receiver if receiver in router_names else '',
                ))

        # Update router route counts
        for router in routers:
            router.route_count = sum(1 for r in routes if r.router_name == router.name)

        return {
            "routes": routes,
            "routers": routers,
            "params": params,
        }

    def _detect_response_type(self, content: str, line_idx: int, lines: List[str]) -> str:
        """Detect response type by looking at handler body."""
        # Look forward in the next ~20 lines for response patterns
        search_lines = lines[line_idx:min(line_idx + 20, len(lines))]
        body = '\n'.join(search_lines)

        if 'res.json(' in body or '.json(' in body:
            return 'json'
        elif 'res.render(' in body:
            return 'render'
        elif 'res.redirect(' in body:
            return 'redirect'
        elif 'res.sendFile(' in body:
            return 'file'
        elif 'res.download(' in body:
            return 'download'
        elif 'res.send(' in body:
            return 'send'
        elif 'res.status(' in body:
            return 'status'
        return ''
