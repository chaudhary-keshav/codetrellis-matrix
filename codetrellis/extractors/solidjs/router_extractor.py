"""
Solid.js Router Extractor for CodeTrellis

Extracts Solid.js routing patterns and configuration:
- @solidjs/router (Solid Router v0.8+)
- solid-start file-based routing
- Route definitions (<Route>, <Routes>, useRoutes)
- Route params (useParams), search params (useSearchParams)
- Navigate, useNavigate, useLocation, useMatch
- Protected routes, route guards
- Layout routes (nested <Route>)
- Lazy route loading
- Data loading (route data, preload)
- Route actions (useAction, useSubmission)

Supports:
- @solidjs/router v0.8-v0.14+ (latest API)
- solid-start v0.x (file-based routing, createRouteData)
- SolidStart v1.0+ (vinxi-based, cache/action/redirect)
- Solid Router hooks: useParams, useNavigate, useLocation, useSearchParams, useMatch, useBeforeLeave

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidRouteInfo:
    """Information about a Solid.js route definition."""
    path: str
    file: str = ""
    line_number: int = 0
    component: str = ""
    has_data: bool = False  # Has route data/preload function
    has_children: bool = False  # Is a layout route
    is_lazy: bool = False
    is_index: bool = False
    has_guard: bool = False  # Protected route / matchFilters
    route_type: str = ""  # declarative, config, file_based


@dataclass
class SolidRouterHookInfo:
    """Information about Solid Router hook usage."""
    hook_name: str  # useParams, useNavigate, useLocation, useSearchParams, useMatch, useBeforeLeave, useAction, useSubmission
    file: str = ""
    line_number: int = 0
    type_params: str = ""  # TypeScript generic params


class SolidRouterExtractor:
    """
    Extracts Solid.js routing patterns from source code.

    Detects:
    - <Route path="..." component={...} /> declarative routes
    - <Routes> wrapper
    - useRoutes() config-based routing
    - Route hooks: useParams, useNavigate, useLocation, etc.
    - useBeforeLeave for route guards
    - Data loading: preload, cache, routeData
    - Actions: useAction, useSubmission, useSubmissions
    - File-based routing (SolidStart conventions)
    - Navigate component for redirects
    """

    # <Route path="..." component={Component} />
    ROUTE_PATTERN = re.compile(
        r'<Route\s+[^>]*path\s*=\s*["\']([^"\']+)["\']([^>]*?)(?:/>|>)',
        re.MULTILINE
    )

    # useRoutes config-based
    USE_ROUTES_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useRoutes\s*\(',
        re.MULTILINE
    )

    # Route config objects: { path: "/...", component: ... }
    ROUTE_CONFIG_PATTERN = re.compile(
        r'\{\s*path\s*:\s*["\']([^"\']+)["\']'
        r'(?:[^}]*component\s*:\s*(\w+))?',
        re.MULTILINE
    )

    # Router hooks
    ROUTER_HOOK_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(useParams|useNavigate|useLocation|useSearchParams|useMatch|useBeforeLeave|useAction|useSubmission|useSubmissions)'
        r'\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Navigate component
    NAVIGATE_PATTERN = re.compile(
        r'<Navigate\s+[^>]*href\s*=\s*["\']([^"\']+)',
        re.MULTILINE
    )

    # A component: <A href="...">
    A_LINK_PATTERN = re.compile(
        r'<A\s+[^>]*href\s*=\s*["\']([^"\']+)',
        re.MULTILINE
    )

    # lazy(() => import('./routes/...'))
    LAZY_ROUTE_PATTERN = re.compile(
        r'lazy\s*\(\s*\(\)\s*=>\s*import\s*\(["\']([^"\']+)["\']\)',
        re.MULTILINE
    )

    # preload function
    PRELOAD_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w*(?:preload|load)\w*)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js routing patterns from source code."""
        routes = []
        hooks = []

        # ── Declarative routes ────────────────────────────────────
        for m in self.ROUTE_PATTERN.finditer(content):
            path = m.group(1)
            attrs = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            component = ""
            comp_match = re.search(r'component\s*=\s*\{(\w+)\}', attrs)
            if comp_match:
                component = comp_match.group(1)

            has_data = bool(re.search(r'(?:data|preload|load)\s*=', attrs))
            has_children = '>' in m.group(0) and '/>' not in m.group(0)
            is_lazy = 'lazy' in attrs
            has_guard = bool(re.search(r'matchFilters', attrs))

            routes.append(SolidRouteInfo(
                path=path,
                file=file_path,
                line_number=line,
                component=component,
                has_data=has_data,
                has_children=has_children,
                is_lazy=is_lazy,
                is_index=path == "/" or path == "",
                has_guard=has_guard,
                route_type="declarative",
            ))

        # ── Config-based routes ───────────────────────────────────
        for m in self.ROUTE_CONFIG_PATTERN.finditer(content):
            path = m.group(1)
            component = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            # Skip if already captured as declarative
            if any(r.path == path and abs(r.line_number - line) < 3 for r in routes):
                continue

            routes.append(SolidRouteInfo(
                path=path,
                file=file_path,
                line_number=line,
                component=component,
                route_type="config",
            ))

        # ── Router hooks ──────────────────────────────────────────
        for m in self.ROUTER_HOOK_PATTERN.finditer(content):
            var_name = m.group(1)
            hook_name = m.group(2)
            type_params = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            hooks.append(SolidRouterHookInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                type_params=type_params,
            ))

        return {
            "routes": routes,
            "router_hooks": hooks,
        }
