"""
Vue.js Routing Extractor for CodeTrellis

Extracts routing patterns from Vue.js source code:
- Vue Router route definitions (createRouter, routes array)
- Route components, lazy-loaded routes, route meta
- Navigation guards (beforeEach, beforeResolve, afterEach, per-route guards)
- Route names, paths, aliases, redirects
- Nested routes (children)
- Router views (RouterView, router-view)
- Nuxt.js page conventions (pages/ directory, definePageMeta)

Supports Vue Router 3.x (Vue 2) through Vue Router 4.x (Vue 3).
Supports Nuxt 2.x through Nuxt 3.x pages directory convention.

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VueRouteInfo:
    """Information about a Vue Router route definition."""
    path: str
    name: str = ""
    file: str = ""
    line_number: int = 0
    component: str = ""
    is_lazy: bool = False
    has_children: bool = False
    children_count: int = 0
    has_meta: bool = False
    meta_keys: List[str] = field(default_factory=list)
    has_redirect: bool = False
    redirect_to: str = ""
    has_alias: bool = False
    has_props: bool = False
    has_guard: bool = False
    guard_type: str = ""  # beforeEnter


@dataclass
class VueNavigationGuardInfo:
    """Information about a Vue Router navigation guard."""
    guard_type: str  # beforeEach, beforeResolve, afterEach, beforeEnter
    file: str = ""
    line_number: int = 0
    is_global: bool = False
    has_next: bool = False  # Vue Router 3 style with next()


@dataclass
class VueRouterViewInfo:
    """Information about a RouterView usage."""
    name: str = ""  # named view
    file: str = ""
    line_number: int = 0


class VueRoutingExtractor:
    """
    Extracts Vue Router route definitions from source code.

    Detects:
    - Route arrays with path/component/name/meta
    - Lazy-loaded routes (() => import(...))
    - Navigation guards (global and per-route)
    - Nested routes (children arrays)
    - RouterView/router-view usage
    - Nuxt pages directory convention
    - definePageMeta (Nuxt 3)
    """

    # createRouter
    CREATE_ROUTER_PATTERN = re.compile(
        r'createRouter\s*\(\s*\{',
        re.MULTILINE
    )

    # new VueRouter (Vue 2)
    NEW_ROUTER_PATTERN = re.compile(
        r'new\s+VueRouter\s*\(\s*\{',
        re.MULTILINE
    )

    # Route definition: { path: '...', component: ... }
    ROUTE_PATTERN = re.compile(
        r'\{\s*path\s*:\s*[\'"]([^\'"]+)[\'"]\s*,',
        re.MULTILINE
    )

    # Route name
    ROUTE_NAME_PATTERN = re.compile(
        r'name\s*:\s*[\'"]([^\'"]+)[\'"]',
    )

    # Route component (eager)
    ROUTE_COMPONENT_PATTERN = re.compile(
        r'component\s*:\s*(\w+)',
    )

    # Lazy route component (supports /* comments */ between import( and path)
    LAZY_COMPONENT_PATTERN = re.compile(
        r'component\s*:\s*\(\)\s*=>\s*import\s*\(\s*(?:/\*.*?\*/\s*)?[\'"]([^\'"]+)[\'"]\s*\)',
    )

    # defineAsyncComponent lazy route
    ASYNC_COMPONENT_ROUTE_PATTERN = re.compile(
        r'component\s*:\s*defineAsyncComponent\s*\(\s*\(\)\s*=>\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
    )

    # Route meta
    ROUTE_META_PATTERN = re.compile(
        r'meta\s*:\s*\{([^}]+)\}',
        re.DOTALL
    )

    # Route redirect
    ROUTE_REDIRECT_PATTERN = re.compile(
        r'redirect\s*:\s*(?:[\'"]([^\'"]+)[\'"]|(\{[^}]+\}))',
    )

    # Route alias
    ROUTE_ALIAS_PATTERN = re.compile(
        r'alias\s*:\s*[\'"]([^\'"]+)[\'"]',
    )

    # Route props
    ROUTE_PROPS_PATTERN = re.compile(
        r'props\s*:\s*(?:true|(\{[^}]+\})|\w+)',
    )

    # beforeEnter guard
    BEFORE_ENTER_PATTERN = re.compile(
        r'beforeEnter\s*:\s*(?:\(|function|async)',
    )

    # Global navigation guards
    GLOBAL_GUARD_PATTERN = re.compile(
        r'router\s*\.\s*(beforeEach|beforeResolve|afterEach)\s*\(',
        re.MULTILINE
    )

    # RouterView / router-view
    ROUTER_VIEW_PATTERN = re.compile(
        r'<(?:RouterView|router-view)(?:\s+name=[\'"]([^\'"]+)[\'"])?\s*/?>',
        re.MULTILINE
    )

    # Children routes
    CHILDREN_PATTERN = re.compile(
        r'children\s*:\s*\[',
    )

    # Nuxt definePageMeta
    DEFINE_PAGE_META_PATTERN = re.compile(
        r'definePageMeta\s*\(\s*\{([^}]+)\}\s*\)',
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Vue Router route definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'guards', 'router_views', 'page_meta'
        """
        result: Dict[str, Any] = {
            'routes': [],
            'guards': [],
            'router_views': [],
            'page_meta': [],
        }

        # Extract routes
        for m in self.ROUTE_PATTERN.finditer(content):
            path = m.group(1)
            route_context = content[m.start():m.start() + 500]

            name_match = self.ROUTE_NAME_PATTERN.search(route_context)
            name = name_match.group(1) if name_match else ""

            # Determine component (lazy or eager)
            lazy_match = self.LAZY_COMPONENT_PATTERN.search(route_context)
            async_match = self.ASYNC_COMPONENT_ROUTE_PATTERN.search(route_context)
            eager_match = self.ROUTE_COMPONENT_PATTERN.search(route_context)

            is_lazy = bool(lazy_match or async_match)
            if lazy_match:
                component = lazy_match.group(1)
            elif async_match:
                component = async_match.group(1)
            elif eager_match:
                component = eager_match.group(1)
            else:
                component = ""

            # Meta
            meta_match = self.ROUTE_META_PATTERN.search(route_context)
            has_meta = bool(meta_match)
            meta_keys = []
            if meta_match:
                meta_keys = re.findall(r'(\w+)\s*:', meta_match.group(1))

            # Redirect
            redirect_match = self.ROUTE_REDIRECT_PATTERN.search(route_context)
            has_redirect = bool(redirect_match)
            redirect_to = ""
            if redirect_match:
                redirect_to = redirect_match.group(1) or redirect_match.group(2) or ""

            # Alias
            has_alias = bool(self.ROUTE_ALIAS_PATTERN.search(route_context))

            # Props
            has_props = bool(self.ROUTE_PROPS_PATTERN.search(route_context))

            # Guard
            has_guard = bool(self.BEFORE_ENTER_PATTERN.search(route_context))

            # Children
            has_children = bool(self.CHILDREN_PATTERN.search(route_context))

            route = VueRouteInfo(
                path=path,
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                component=component,
                is_lazy=is_lazy,
                has_children=has_children,
                has_meta=has_meta,
                meta_keys=meta_keys,
                has_redirect=has_redirect,
                redirect_to=redirect_to,
                has_alias=has_alias,
                has_props=has_props,
                has_guard=has_guard,
                guard_type="beforeEnter" if has_guard else "",
            )
            result['routes'].append(route)

        # Extract global navigation guards
        for m in self.GLOBAL_GUARD_PATTERN.finditer(content):
            after = content[m.end():m.end() + 200]
            has_next = bool(re.search(r'\bnext\b', after))
            result['guards'].append(VueNavigationGuardInfo(
                guard_type=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_global=True,
                has_next=has_next,
            ))

        # Extract RouterView usage
        for m in self.ROUTER_VIEW_PATTERN.finditer(content):
            result['router_views'].append(VueRouterViewInfo(
                name=m.group(1) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract Nuxt definePageMeta
        for m in self.DEFINE_PAGE_META_PATTERN.finditer(content):
            body = m.group(1)
            meta_keys = re.findall(r'(\w+)\s*:', body)
            result['page_meta'].append({
                'file': file_path,
                'line': content[:m.start()].count('\n') + 1,
                'meta_keys': meta_keys,
            })

        return result
