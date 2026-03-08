"""
Koa Route Extractor - Extracts route definitions from Koa applications.

Supports:
- koa-router v5.x-v12.x (router.get/post/put/delete/patch, router.routes())
- @koa/router v8.x-v13.x (modern scoped package)
- koa-route (simple routing)
- koa-tree-router, koa-better-router
- Nested routers with router.use('/prefix', nestedRouter.routes())
- Named routes: router.url('name', params)
- Router middleware chaining: router.get('/path', mw1, mw2, handler)
- Route parameters: /users/:id, /users/:id(\\d+)
- Allowed methods: router.allowedMethods()
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KoaRouteInfo:
    """A single Koa route definition."""
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
    route_name: str = ""  # Named route (router.get('name', '/path', handler))


@dataclass
class KoaRouterInfo:
    """A Koa Router() instance."""
    name: str
    file: str = ""
    line_number: int = 0
    prefix: str = ""  # router({ prefix: '/api' })
    route_count: int = 0
    has_middleware: bool = False
    middleware_names: List[str] = field(default_factory=list)
    has_allowed_methods: bool = False
    router_package: str = ""  # 'koa-router', '@koa/router', 'koa-tree-router'


@dataclass
class KoaParamInfo:
    """A router.param() declaration."""
    param_name: str
    handler: str
    file: str = ""
    line_number: int = 0
    router_name: str = ""


class KoaRouteExtractor:
    """Extracts Koa route definitions from source code."""

    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'all'}

    # Route definition patterns
    ROUTE_PATTERNS = [
        # router.get('/path', handler) or router.get('name', '/path', handler)
        re.compile(
            r'(?:^|\n)\s*(?:(\w+)\s*\.)\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
            r'(?:([\'"`]\w+[\'"`])\s*,\s*)?'
            r'[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        ),
    ]

    # koa-route module style: route.get('/path', handler) — used inside app.use()
    KOA_ROUTE_MODULE_PATTERN = re.compile(
        r'route\s*\.\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
        r'[\'"`]([^\'"`]+)[\'"`]\s*,\s*(\w+)',
        re.IGNORECASE
    )

    # Router creation patterns
    ROUTER_PATTERNS = [
        # const router = new Router() / new Router({ prefix: '/api' })
        re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+Router\s*\(',
        ),
        # export const router = new Router()
        re.compile(
            r'export\s+(?:const|let|var)\s+(\w+)\s*=\s*new\s+Router\s*\(',
        ),
        # const router = Router()  (some koa-router versions)
        re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*Router\s*\(\s*(?:\{[^}]*\})?\s*\)',
        ),
    ]

    # Router mount patterns
    ROUTER_MOUNT_PATTERNS = [
        # app.use(router.routes())
        re.compile(
            r'(\w+)\s*\.\s*use\s*\(\s*(\w+)\.routes\s*\(\s*\)',
        ),
        # app.use('/prefix', router.routes())
        re.compile(
            r'(\w+)\s*\.\s*use\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(\w+)\.routes\s*\(',
        ),
    ]

    # Router prefix pattern
    ROUTER_PREFIX_PATTERN = re.compile(
        r'new\s+Router\s*\(\s*\{\s*prefix\s*:\s*[\'"`]([^\'"`]+)[\'"`]',
    )

    # Param middleware
    PARAM_PATTERN = re.compile(
        r'(\w+)\s*\.\s*param\s*\(\s*[\'"`](\w+)[\'"`]\s*,\s*(\w+)',
    )

    # AllowedMethods pattern
    ALLOWED_METHODS_PATTERN = re.compile(
        r'(\w+)\s*\.allowedMethods\s*\(',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Koa route information from source code."""
        routes: List[KoaRouteInfo] = []
        routers: List[KoaRouterInfo] = []
        params: List[KoaParamInfo] = []

        lines = content.split('\n')

        # Extract routers
        router_names = set()
        for pattern in self.ROUTER_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                prefix = ''
                prefix_m = self.ROUTER_PREFIX_PATTERN.search(content[match.start():match.start() + 200])
                if prefix_m:
                    prefix = prefix_m.group(1)

                # Detect router package
                pkg = self._detect_router_package(content)

                routers.append(KoaRouterInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    prefix=prefix,
                    router_package=pkg,
                ))
                router_names.add(name)

        # Extract routes
        for pattern in self.ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                receiver = match.group(1) or ''
                method = match.group(2).upper()
                named = match.group(3)
                path = match.group(4)

                line_num = content[:match.start()].count('\n') + 1
                line_text = lines[line_num - 1] if line_num <= len(lines) else ""

                # Count middleware arguments
                rest_of_call = content[match.end():]
                mw_count, mw_names, handler = self._parse_handler_args(rest_of_call, line_text)

                # Extract param names from path
                param_names = re.findall(r':(\w+)', path)
                is_dynamic = bool(param_names) or '*' in path

                is_async = 'async' in line_text or 'async' in rest_of_call[:100]

                route_name = named.strip("'\"` ") if named else ""

                routes.append(KoaRouteInfo(
                    method=method,
                    path=path,
                    handler=handler,
                    file=file_path,
                    line_number=line_num,
                    is_async=is_async,
                    has_middleware=mw_count > 0,
                    middleware_count=mw_count,
                    middleware_names=mw_names,
                    has_params=bool(param_names),
                    param_names=param_names,
                    is_dynamic=is_dynamic,
                    router_name=receiver if receiver in router_names else "",
                    route_name=route_name,
                ))

        # Extract koa-route module style: route.get('/path', handler)
        for match in self.KOA_ROUTE_MODULE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            handler = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""

            param_names = re.findall(r':(\w+)', path)
            is_dynamic = bool(param_names) or '*' in path
            is_async = 'async' in line_text

            routes.append(KoaRouteInfo(
                method=method,
                path=path,
                handler=handler,
                file=file_path,
                line_number=line_num,
                is_async=is_async,
                has_params=bool(param_names),
                param_names=param_names,
                is_dynamic=is_dynamic,
            ))

        # Update router route counts
        for router in routers:
            router.route_count = sum(1 for r in routes if r.router_name == router.name)

        # Check allowedMethods
        for match in self.ALLOWED_METHODS_PATTERN.finditer(content):
            rname = match.group(1)
            for router in routers:
                if router.name == rname:
                    router.has_allowed_methods = True

        # Extract params
        for match in self.PARAM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            params.append(KoaParamInfo(
                param_name=match.group(2),
                handler=match.group(3),
                file=file_path,
                line_number=line_num,
                router_name=match.group(1) if match.group(1) in router_names else "",
            ))

        return {
            'routes': routes,
            'routers': routers,
            'params': params,
        }

    def _parse_handler_args(self, rest: str, line_text: str):
        """Parse middleware and handler from route arguments."""
        # Simple heuristic: count comma-separated function refs before closing paren
        mw_names = []
        handler = 'anonymous'
        # Find function names or arrow functions in the arg list
        func_refs = re.findall(r'(\w+)(?:\s*,|\s*\))', rest[:300])
        if func_refs:
            handler = func_refs[-1] if func_refs else 'anonymous'
            mw_names = func_refs[:-1] if len(func_refs) > 1 else []
        elif 'async' in rest[:100] or '=>' in rest[:100]:
            handler = 'anonymous'
        return len(mw_names), mw_names[:10], handler

    def _detect_router_package(self, content: str) -> str:
        """Detect which Koa router package is being used."""
        if re.search(r"from\s+['\"]@koa/router['\"]|require\(['\"]@koa/router['\"]\)", content):
            return '@koa/router'
        if re.search(r"from\s+['\"]koa-router['\"]|require\(['\"]koa-router['\"]\)", content):
            return 'koa-router'
        if re.search(r"from\s+['\"]koa-tree-router['\"]|require\(['\"]koa-tree-router['\"]\)", content):
            return 'koa-tree-router'
        if re.search(r"from\s+['\"]koa-route['\"]|require\(['\"]koa-route['\"]\)", content):
            return 'koa-route'
        if re.search(r"from\s+['\"]koa-better-router['\"]|require\(['\"]koa-better-router['\"]\)", content):
            return 'koa-better-router'
        return ''
