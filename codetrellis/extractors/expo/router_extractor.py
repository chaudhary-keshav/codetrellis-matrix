"""
Expo Router Extractor for CodeTrellis

Extracts Expo Router patterns from JS/TS source code:
- File-based routing (app/ directory convention)
- Layout routes (_layout.tsx)
- Route groups ((group)/)
- API routes (+api.ts)
- Dynamic segments ([param], [...catchAll])
- Navigation patterns (Link, router.push, useRouter)

Supports Expo Router v1-v3 (SDK 49-52+).

Part of CodeTrellis v5.7 - Expo Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExpoRouteInfo:
    """Information about an Expo Router route."""
    route_path: str = ""  # e.g., '/settings', '/user/[id]'
    file_path: str = ""
    is_dynamic: bool = False
    dynamic_params: List[str] = field(default_factory=list)
    is_catch_all: bool = False
    is_index: bool = False
    is_api_route: bool = False
    is_modal: bool = False
    has_error_boundary: bool = False
    exports: List[str] = field(default_factory=list)  # default, ErrorBoundary, etc.
    line_number: int = 0


@dataclass
class ExpoLayoutInfo:
    """Information about an Expo Router layout."""
    layout_type: str = ""  # stack, tabs, drawer, slot
    file_path: str = ""
    route_group: str = ""  # e.g., '(auth)', '(tabs)'
    screens: List[str] = field(default_factory=list)
    has_header_config: bool = False
    has_tab_bar_config: bool = False
    line_number: int = 0


@dataclass
class ExpoRouteGroupInfo:
    """Information about a route group."""
    group_name: str = ""  # e.g., 'auth', 'tabs', 'settings'
    routes: List[str] = field(default_factory=list)
    has_layout: bool = False
    is_shared: bool = False
    file_path: str = ""


@dataclass
class ExpoApiRouteInfo:
    """Information about an Expo Router API route (+api.ts)."""
    route_path: str = ""
    http_methods: List[str] = field(default_factory=list)  # GET, POST, PUT, DELETE
    file_path: str = ""
    line_number: int = 0


class ExpoRouterExtractor:
    """
    Extracts Expo Router patterns from source code.

    Detects Expo Router v1-v3 conventions:
    - Stack, Tab, Drawer navigators via layout files
    - Dynamic routes: [param], [...catchAll], [(...optional)]
    - Route groups: (group)/
    - API routes: +api.ts
    - Navigation hooks: useRouter, useLocalSearchParams, useSegments
    - Link component usage
    - Typed routes (v3+)
    """

    LAYOUT_PATTERNS = {
        'stack': re.compile(
            r"<Stack(?:\.Screen)?[\s>]|"
            r"Stack\s*=\s*createNativeStackNavigator|"
            r"from\s+['\"]expo-router['\"].*\bStack\b",
            re.MULTILINE | re.DOTALL
        ),
        'tabs': re.compile(
            r"<Tabs(?:\.Screen)?[\s>]|"
            r"Tabs\s*=\s*createBottomTabNavigator|"
            r"from\s+['\"]expo-router['\"].*\bTabs\b",
            re.MULTILINE | re.DOTALL
        ),
        'drawer': re.compile(
            r"<Drawer(?:\.Screen)?[\s>]|"
            r"Drawer\s*=\s*createDrawerNavigator|"
            r"from\s+['\"]expo-router['\"].*\bDrawer\b",
            re.MULTILINE | re.DOTALL
        ),
        'slot': re.compile(
            r"<Slot\s*/?>|from\s+['\"]expo-router['\"].*\bSlot\b",
            re.MULTILINE | re.DOTALL
        ),
    }

    NAVIGATION_HOOKS = re.compile(
        r"\b(useRouter|useLocalSearchParams|useGlobalSearchParams|"
        r"useSegments|usePathname|useNavigationContainerRef|"
        r"useRootNavigation|useRootNavigationState)\b",
        re.MULTILINE
    )

    LINK_PATTERN = re.compile(
        r"<Link\s+[^>]*href\s*=\s*[{'\"]([^}'\"]+)",
        re.MULTILINE
    )

    ROUTER_NAVIGATE = re.compile(
        r"router\.(push|replace|back|canGoBack|dismiss|dismissAll|navigate)"
        r"\s*\(",
        re.MULTILINE
    )

    REDIRECT_PATTERN = re.compile(
        r"<Redirect\s+[^>]*href\s*=\s*[{'\"]([^}'\"]+)",
        re.MULTILINE
    )

    ERROR_BOUNDARY_EXPORT = re.compile(
        r"export\s+(?:function|const)\s+ErrorBoundary",
        re.MULTILINE
    )

    SCREEN_OPTIONS = re.compile(
        r"<(?:Stack|Tabs|Drawer)\.Screen\s+[^>]*name\s*=\s*['\"]([^'\"]+)",
        re.MULTILINE
    )

    HTTP_METHOD_EXPORT = re.compile(
        r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)",
        re.MULTILINE
    )

    TYPED_ROUTE_PATTERN = re.compile(
        r"Href|useRouter<|router\.push<|Link<",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Expo Router patterns from source code."""
        result: Dict[str, Any] = {
            'routes': [],
            'layouts': [],
            'route_groups': [],
            'api_routes': [],
            'navigation_hooks': [],
            'router_version': 0,
        }

        # Detect router version from imports
        result['router_version'] = self._detect_router_version(content)

        # Detect if this is a layout file
        if '_layout' in file_path:
            self._extract_layout(content, file_path, result)

        # Detect API routes
        if '+api' in file_path:
            self._extract_api_route(content, file_path, result)

        # Extract route info from file path convention
        self._extract_route_from_path(content, file_path, result)

        # Extract navigation patterns
        self._extract_navigation(content, file_path, result)

        return result

    def _detect_router_version(self, content: str) -> int:
        """Detect Expo Router version from imports and usage."""
        if self.TYPED_ROUTE_PATTERN.search(content):
            return 3
        if re.search(r"from\s+['\"]expo-router['\"]", content):
            return 2
        if re.search(r"from\s+['\"]expo-router/stack['\"]", content):
            return 1
        return 0

    def _extract_layout(self, content: str, file_path: str,
                        result: Dict[str, Any]) -> None:
        """Extract layout information from _layout.tsx files."""
        # Determine layout type
        for layout_type, pattern in self.LAYOUT_PATTERNS.items():
            if pattern.search(content):
                screens: List[str] = []
                for m in self.SCREEN_OPTIONS.finditer(content):
                    screens.append(m.group(1))

                # Extract route group from path
                group = ""
                group_m = re.search(r"\(([^)]+)\)", file_path)
                if group_m:
                    group = group_m.group(1)

                layout = ExpoLayoutInfo(
                    layout_type=layout_type,
                    file_path=file_path,
                    route_group=group,
                    screens=screens[:30],
                    has_header_config='headerShown' in content or 'headerTitle' in content,
                    has_tab_bar_config='tabBarIcon' in content or 'tabBarLabel' in content,
                    line_number=1,
                )
                result['layouts'].append(layout)
                break

    def _extract_api_route(self, content: str, file_path: str,
                           result: Dict[str, Any]) -> None:
        """Extract API route information from +api.ts files."""
        methods: List[str] = []
        for m in self.HTTP_METHOD_EXPORT.finditer(content):
            methods.append(m.group(1))

        if methods:
            # Derive route path from file path
            route_path = self._file_path_to_route(file_path)
            result['api_routes'].append(ExpoApiRouteInfo(
                route_path=route_path,
                http_methods=methods,
                file_path=file_path,
                line_number=1,
            ))

    def _extract_route_from_path(self, content: str, file_path: str,
                                 result: Dict[str, Any]) -> None:
        """Extract route information based on file path convention."""
        # Only process files in app/ directory
        if '/app/' not in file_path and not file_path.startswith('app/'):
            return

        route_path = self._file_path_to_route(file_path)
        if not route_path:
            return

        # Detect dynamic segments
        dynamic_params: List[str] = []
        is_catch_all = False
        for dm in re.finditer(r'\[(?:\.\.\.)?(\w+)\]', route_path):
            dynamic_params.append(dm.group(1))
        if '[...' in route_path:
            is_catch_all = True

        # Detect exports
        exports: List[str] = []
        if re.search(r'export\s+default\b', content):
            exports.append('default')
        if self.ERROR_BOUNDARY_EXPORT.search(content):
            exports.append('ErrorBoundary')
        if re.search(r'export\s+(?:const|function)\s+unstable_settings', content):
            exports.append('unstable_settings')

        route = ExpoRouteInfo(
            route_path=route_path,
            file_path=file_path,
            is_dynamic=bool(dynamic_params),
            dynamic_params=dynamic_params,
            is_catch_all=is_catch_all,
            is_index='index' in file_path.split('/')[-1],
            is_api_route='+api' in file_path,
            is_modal='modal' in file_path.lower(),
            has_error_boundary='ErrorBoundary' in exports,
            exports=exports,
            line_number=1,
        )
        result['routes'].append(route)

        # Extract route groups
        for gm in re.finditer(r'\(([^)]+)\)', file_path):
            group_name = gm.group(1)
            # Check if we already have this group
            existing = [g for g in result['route_groups'] if g.group_name == group_name]
            if existing:
                if route_path not in existing[0].routes:
                    existing[0].routes.append(route_path)
            else:
                result['route_groups'].append(ExpoRouteGroupInfo(
                    group_name=group_name,
                    routes=[route_path],
                    has_layout='_layout' in file_path,
                    file_path=file_path,
                ))

    def _extract_navigation(self, content: str, file_path: str,
                            result: Dict[str, Any]) -> None:
        """Extract navigation hook and pattern usage."""
        for m in self.NAVIGATION_HOOKS.finditer(content):
            hook = m.group(1)
            if hook not in result['navigation_hooks']:
                result['navigation_hooks'].append(hook)

    def _file_path_to_route(self, file_path: str) -> str:
        """Convert file path to Expo Router route path."""
        # Extract app/ relative path
        m = re.search(r'(?:^|/)app/(.+?)(?:\.[jt]sx?)?$', file_path)
        if not m:
            return ""

        route = m.group(1)
        # Remove _layout, +not-found, +html
        if route.endswith('_layout') or route.endswith('+not-found') or route.endswith('+html'):
            return ""
        # Remove +api suffix for route path
        route = re.sub(r'\+api$', '', route)
        # Remove index
        route = re.sub(r'/?index$', '', route)
        # Remove route group markers for route path
        route = re.sub(r'\([^)]+\)/?', '', route)
        # Clean up
        route = '/' + route.strip('/')
        if route == '/':
            return '/'
        return route
