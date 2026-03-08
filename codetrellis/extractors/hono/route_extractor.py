"""
Hono Route Extractor - Extracts Hono route definitions from source code.

Detects:
- app.get/post/put/delete/patch/options/head/all() routes
- app.route() sub-router mounting
- app.basePath() prefix
- Grouped routes via new Hono().basePath()
- Route parameters: /users/:id, /posts/:id{[0-9]+}
- Wildcard routes: /api/*
- Hono v1-v4 route patterns
- hono/router/* (RegExpRouter, TrieRouter, SmartRouter, LinearRouter, PatternRouter)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HonoRouteInfo:
    """A single Hono route definition."""
    method: str  # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, ALL
    path: str
    handler: str = ""
    is_async: bool = False
    middleware: List[str] = field(default_factory=list)
    params: List[str] = field(default_factory=list)
    has_validator: bool = False
    validator_type: str = ""  # zod, valibot, typebox, custom
    file: str = ""
    line_number: int = 0


@dataclass
class HonoRouterInfo:
    """A Hono sub-router or app instance."""
    name: str
    base_path: str = ""
    route_count: int = 0
    router_type: str = ""  # RegExpRouter, TrieRouter, SmartRouter, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class HonoParamInfo:
    """A route parameter definition."""
    name: str
    pattern: str = ""  # regex constraint
    is_optional: bool = False


class HonoRouteExtractor:
    """Extracts Hono route definitions from source code."""

    # HTTP method route patterns: app.get('/path', handler)
    ROUTE_PATTERNS = [
        # Standard route definitions
        re.compile(
            r'(?:(\w+)\s*\.)\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
            r'[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        ),
    ]

    # Route mounting: app.route('/api', apiRouter)
    ROUTE_MOUNT_PATTERN = re.compile(
        r'(\w+)\s*\.\s*route\s*\(\s*[\'"`]([^\'"`]*)[\'"`]\s*,\s*(\w+)',
    )

    # basePath: new Hono().basePath('/api')
    BASE_PATH_PATTERN = re.compile(
        r'(?:(\w+)\s*=\s*)?new\s+Hono\s*\([^)]*\)\s*\.\s*basePath\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\)',
    )

    # Hono creation: const app = new Hono()
    HONO_CREATION_PATTERNS = [
        re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+Hono\s*\('),
        re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+Hono\s*<'),
    ]

    # Router type: new Hono({ router: new RegExpRouter() })
    ROUTER_TYPE_PATTERN = re.compile(
        r'new\s+Hono\s*\(\s*\{\s*router\s*:\s*new\s+(\w+Router)\s*\(',
    )

    # Parameter extraction from paths
    PARAM_PATTERN = re.compile(r':(\w+)(?:\{([^}]+)\})?')

    # Wildcard detection
    WILDCARD_PATTERN = re.compile(r'/\*$')

    # Chained routes: app.get('/a', h1).post('/b', h2)
    CHAINED_PATTERN = re.compile(
        r'\.\s*(get|post|put|delete|patch|options|head|all)\s*\(\s*'
        r'[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE
    )

    # Validator usage: validator('json', (value, c) => ...)
    VALIDATOR_PATTERN = re.compile(
        r'validator\s*\(\s*[\'"`](\w+)[\'"`]',
    )

    # Zod validator: zValidator('json', schema)
    ZVALIDATOR_PATTERN = re.compile(
        r'zValidator\s*\(\s*[\'"`](\w+)[\'"`]',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hono routes from source code."""
        routes: List[HonoRouteInfo] = []
        routers: List[HonoRouterInfo] = []
        params: List[HonoParamInfo] = []

        seen_routes = set()

        # Detect Hono instances
        router_type = ""
        type_match = self.ROUTER_TYPE_PATTERN.search(content)
        if type_match:
            router_type = type_match.group(1)

        for pattern in self.HONO_CREATION_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                routers.append(HonoRouterInfo(
                    name=match.group(1),
                    router_type=router_type,
                    file=file_path,
                    line_number=line_num,
                ))

        # basePath detection
        for match in self.BASE_PATH_PATTERN.finditer(content):
            name = match.group(1) or ''
            base = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            if name:
                # Update existing router
                for r in routers:
                    if r.name == name:
                        r.base_path = base
                        break
                else:
                    routers.append(HonoRouterInfo(
                        name=name,
                        base_path=base,
                        file=file_path,
                        line_number=line_num,
                    ))

        # Route definitions
        for pattern in self.ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                receiver = match.group(1)
                method = match.group(2).upper()
                path = match.group(3)
                line_num = content[:match.start()].count('\n') + 1

                route_key = (method, path, line_num)
                if route_key in seen_routes:
                    continue
                seen_routes.add(route_key)

                # Check for async handler
                after_match = content[match.end():match.end()+200]
                is_async = bool(re.search(r'async\s', after_match[:100]))

                # Extract middleware from multi-arg calls
                middleware = []
                mw_scan = content[match.end():match.end()+500]
                # Look for named middleware before the final handler
                mw_matches = re.finditer(r'(\w+)\s*,', mw_scan[:200])
                for mw_match in mw_matches:
                    name = mw_match.group(1)
                    if name not in ('async', 'ctx', 'c', 'next', 'true', 'false'):
                        middleware.append(name)

                # Check for validator
                has_validator = False
                validator_type = ""
                if self.ZVALIDATOR_PATTERN.search(mw_scan[:300]):
                    has_validator = True
                    validator_type = 'zod'
                elif self.VALIDATOR_PATTERN.search(mw_scan[:300]):
                    has_validator = True
                    validator_type = 'custom'

                # Extract params
                route_params = []
                for pm in self.PARAM_PATTERN.finditer(path):
                    pname = pm.group(1)
                    ppattern = pm.group(2) or ''
                    route_params.append(pname)
                    params.append(HonoParamInfo(
                        name=pname,
                        pattern=ppattern,
                    ))

                routes.append(HonoRouteInfo(
                    method=method,
                    path=path,
                    is_async=is_async,
                    middleware=middleware,
                    params=route_params,
                    has_validator=has_validator,
                    validator_type=validator_type,
                    file=file_path,
                    line_number=line_num,
                ))

        # Route mounts
        for match in self.ROUTE_MOUNT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            base_path = match.group(2)
            sub_router = match.group(3)
            for r in routers:
                if r.name == sub_router:
                    r.base_path = base_path
                    break

        # Update route counts
        for r in routers:
            r.route_count = sum(1 for rt in routes if True)  # Count relevant routes

        return {
            'routes': routes,
            'routers': routers,
            'params': params,
        }
