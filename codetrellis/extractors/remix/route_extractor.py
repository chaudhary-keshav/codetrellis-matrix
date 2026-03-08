"""
Remix Route Extractor v1.0

Extracts routing information from Remix / React Router v7 files:
- Route configuration (routes.ts, route(), index(), layout(), prefix())
- File-based routing (@remix-run/fs-routes, @react-router/fs-routes, flatRoutes)
- Nested routes and Outlet usage
- Dynamic segments (:param), optional segments (:param?), splats (*)
- Layout routes (pathless layouts)
- Index routes
- Root route (root.tsx)
- Route module file type detection (page, layout, route handler, etc.)

Supports:
- Remix v1.x (routes in remix.config.js, convention-based)
- Remix v2.x (Vite, flat file routing, v2_routeConvention)
- React Router v7 (routes.ts config file, @react-router/dev/routes)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RemixRouteInfo:
    """Information about a route in a Remix application."""
    name: str = ""
    path: str = ""
    file_path: str = ""
    line_number: int = 0

    # Route type
    route_type: str = ""  # page, layout, index, error, catch, root, api

    # Dynamic segments
    has_dynamic_params: bool = False
    dynamic_params: List[str] = field(default_factory=list)
    has_splat: bool = False
    has_optional_params: bool = False

    # Nesting
    is_nested: bool = False
    parent_route: str = ""
    child_count: int = 0

    # Module exports
    has_loader: bool = False
    has_action: bool = False
    has_meta: bool = False
    has_links: bool = False
    has_headers: bool = False
    has_error_boundary: bool = False
    has_catch_boundary: bool = False  # v1
    has_handle: bool = False
    has_should_revalidate: bool = False
    has_hydrate_fallback: bool = False

    # Config style
    config_style: str = ""  # file-based, config-based, flat-routes

    # Export type
    is_default_export: bool = False
    component_name: str = ""


@dataclass
class RemixLayoutInfo:
    """Information about a layout route."""
    name: str = ""
    file_path: str = ""
    line_number: int = 0
    has_outlet: bool = False
    child_routes: List[str] = field(default_factory=list)
    is_root: bool = False
    is_pathless: bool = False


@dataclass
class RemixOutletInfo:
    """Information about an Outlet usage."""
    file_path: str = ""
    line_number: int = 0
    has_context: bool = False
    context_type: str = ""


class RemixRouteExtractor:
    """Extracts route information from Remix / React Router v7 files."""

    # Route config patterns (routes.ts / route config files)
    ROUTE_CONFIG_PATTERN = re.compile(
        r'route\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*(?:,\s*\[)?',
        re.MULTILINE
    )

    INDEX_CONFIG_PATTERN = re.compile(
        r'index\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    LAYOUT_CONFIG_PATTERN = re.compile(
        r'layout\(\s*["\']([^"\']+)["\']\s*,\s*\[',
        re.MULTILINE
    )

    PREFIX_CONFIG_PATTERN = re.compile(
        r'prefix\(\s*["\']([^"\']+)["\']\s*,\s*\[',
        re.MULTILINE
    )

    # Route module export patterns
    LOADER_EXPORT = re.compile(
        r'export\s+(?:async\s+)?function\s+loader\b|'
        r'export\s+(?:const|let)\s+loader\s*[=:]',
        re.MULTILINE
    )

    CLIENT_LOADER_EXPORT = re.compile(
        r'export\s+(?:async\s+)?function\s+clientLoader\b|'
        r'export\s+(?:const|let)\s+clientLoader\s*[=:]',
        re.MULTILINE
    )

    ACTION_EXPORT = re.compile(
        r'export\s+(?:async\s+)?function\s+action\b|'
        r'export\s+(?:const|let)\s+action\s*[=:]',
        re.MULTILINE
    )

    META_EXPORT = re.compile(
        r'export\s+(?:const|function)\s+meta\b',
        re.MULTILINE
    )

    LINKS_EXPORT = re.compile(
        r'export\s+(?:const|function)\s+links\b',
        re.MULTILINE
    )

    HEADERS_EXPORT = re.compile(
        r'export\s+(?:const|function)\s+headers\b',
        re.MULTILINE
    )

    ERROR_BOUNDARY_EXPORT = re.compile(
        r'export\s+(?:function|const)\s+ErrorBoundary\b',
        re.MULTILINE
    )

    CATCH_BOUNDARY_EXPORT = re.compile(
        r'export\s+(?:function|const)\s+CatchBoundary\b',
        re.MULTILINE
    )

    HANDLE_EXPORT = re.compile(
        r'export\s+(?:const|let)\s+handle\s*[=:]',
        re.MULTILINE
    )

    SHOULD_REVALIDATE_EXPORT = re.compile(
        r'export\s+(?:function|const)\s+shouldRevalidate\b',
        re.MULTILINE
    )

    HYDRATE_FALLBACK_EXPORT = re.compile(
        r'export\s+(?:function|const)\s+HydrateFallback\b',
        re.MULTILINE
    )

    DEFAULT_EXPORT = re.compile(
        r'export\s+default\s+(?:function\s+(\w+)|(\w+))',
        re.MULTILINE
    )

    # Outlet usage
    OUTLET_PATTERN = re.compile(
        r'<Outlet\b([^/>]*)/?>',
        re.MULTILINE
    )

    OUTLET_CONTEXT_PATTERN = re.compile(
        r'context\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # Dynamic param extraction from paths
    DYNAMIC_PARAM_PATTERN = re.compile(r':(\w+)\??')
    SPLAT_PATTERN = re.compile(r'\*$|/\*$')
    OPTIONAL_PARAM_PATTERN = re.compile(r':(\w+)\?')

    # File-based routing patterns (filename-based)
    # Remix v2 flat routes: routes/posts.$postId.tsx -> /posts/:postId
    FLAT_ROUTE_DYNAMIC = re.compile(r'\$(\w+)')
    # Remix v1 nested routes: routes/posts/$postId.tsx -> /posts/:postId
    V1_DYNAMIC_SEGMENT = re.compile(r'/\$(\w+)')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract route information from a Remix/RR7 source file.

        Args:
            content: Source code content
            file_path: Path to the source file

        Returns:
            Dict with routes, layouts, outlets
        """
        routes: List[RemixRouteInfo] = []
        layouts: List[RemixLayoutInfo] = []
        outlets: List[RemixOutletInfo] = []

        # Extract route configs (from routes.ts)
        routes.extend(self._extract_route_configs(content, file_path))

        # Extract route module info (from individual route files)
        route_info = self._extract_route_module(content, file_path)
        if route_info:
            routes.append(route_info)

        # Extract layouts
        layouts.extend(self._extract_layouts(content, file_path))

        # Extract outlets
        outlets.extend(self._extract_outlets(content, file_path))

        return {
            'routes': routes,
            'layouts': layouts,
            'outlets': outlets,
        }

    def _extract_route_configs(self, content: str, file_path: str) -> List[RemixRouteInfo]:
        """Extract route() / index() / layout() / prefix() configs."""
        routes: List[RemixRouteInfo] = []

        # route("path", "./file.tsx")
        for match in self.ROUTE_CONFIG_PATTERN.finditer(content):
            path = match.group(1)
            module_file = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            route = RemixRouteInfo(
                name=self._path_to_name(path),
                path=path,
                file_path=module_file,
                line_number=line_num,
                route_type="page",
                config_style="config-based",
            )

            # Parse dynamic segments
            self._parse_dynamic_segments(route, path)

            # Check for children (nested routes)
            if match.group(0).rstrip().endswith('['):
                route.is_nested = True

            routes.append(route)

        # index("./file.tsx")
        for match in self.INDEX_CONFIG_PATTERN.finditer(content):
            module_file = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            routes.append(RemixRouteInfo(
                name="index",
                path="/",
                file_path=module_file,
                line_number=line_num,
                route_type="index",
                config_style="config-based",
                is_default_export=True,
            ))

        # layout("./layout.tsx", [...])
        for match in self.LAYOUT_CONFIG_PATTERN.finditer(content):
            module_file = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            routes.append(RemixRouteInfo(
                name=self._path_to_name(module_file),
                path="",
                file_path=module_file,
                line_number=line_num,
                route_type="layout",
                config_style="config-based",
                is_nested=True,
            ))

        return routes

    def _extract_route_module(self, content: str, file_path: str) -> Optional[RemixRouteInfo]:
        """Extract route module information from a route file."""
        # Only process if file has route module exports
        has_any_export = any([
            self.LOADER_EXPORT.search(content),
            self.ACTION_EXPORT.search(content),
            self.META_EXPORT.search(content),
            self.DEFAULT_EXPORT.search(content),
            self.ERROR_BOUNDARY_EXPORT.search(content),
        ])

        if not has_any_export:
            return None

        route = RemixRouteInfo(file_path=file_path)

        # Determine route type from file path
        route.route_type = self._detect_route_type(file_path)

        # Detect exports
        route.has_loader = bool(self.LOADER_EXPORT.search(content))
        route.has_action = bool(self.ACTION_EXPORT.search(content))
        route.has_meta = bool(self.META_EXPORT.search(content))
        route.has_links = bool(self.LINKS_EXPORT.search(content))
        route.has_headers = bool(self.HEADERS_EXPORT.search(content))
        route.has_error_boundary = bool(self.ERROR_BOUNDARY_EXPORT.search(content))
        route.has_catch_boundary = bool(self.CATCH_BOUNDARY_EXPORT.search(content))
        route.has_handle = bool(self.HANDLE_EXPORT.search(content))
        route.has_should_revalidate = bool(self.SHOULD_REVALIDATE_EXPORT.search(content))
        route.has_hydrate_fallback = bool(self.HYDRATE_FALLBACK_EXPORT.search(content))

        # Default export (component)
        default_match = self.DEFAULT_EXPORT.search(content)
        if default_match:
            route.is_default_export = True
            route.component_name = default_match.group(1) or default_match.group(2) or ""

        # Detect dynamic params from file path
        if file_path:
            self._parse_file_based_params(route, file_path)

        return route

    def _extract_layouts(self, content: str, file_path: str) -> List[RemixLayoutInfo]:
        """Extract layout information."""
        layouts: List[RemixLayoutInfo] = []

        has_outlet = bool(self.OUTLET_PATTERN.search(content))
        default_match = self.DEFAULT_EXPORT.search(content)

        if has_outlet and default_match:
            import os
            name = os.path.basename(file_path).rsplit('.', 1)[0] if file_path else ""
            layouts.append(RemixLayoutInfo(
                name=default_match.group(1) or default_match.group(2) or name,
                file_path=file_path,
                has_outlet=True,
                is_root='root' in file_path.lower() if file_path else False,
            ))

        return layouts

    def _extract_outlets(self, content: str, file_path: str) -> List[RemixOutletInfo]:
        """Extract Outlet usage."""
        outlets: List[RemixOutletInfo] = []

        for match in self.OUTLET_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            attrs = match.group(1) or ""

            outlet = RemixOutletInfo(
                file_path=file_path,
                line_number=line_num,
            )

            # Check for context prop
            ctx_match = self.OUTLET_CONTEXT_PATTERN.search(attrs)
            if ctx_match:
                outlet.has_context = True
                outlet.context_type = ctx_match.group(1).strip()

            outlets.append(outlet)

        return outlets

    def _parse_dynamic_segments(self, route: RemixRouteInfo, path: str) -> None:
        """Parse dynamic segments from route path."""
        params = self.DYNAMIC_PARAM_PATTERN.findall(path)
        if params:
            route.has_dynamic_params = True
            route.dynamic_params = params

        if self.SPLAT_PATTERN.search(path):
            route.has_splat = True

        if self.OPTIONAL_PARAM_PATTERN.search(path):
            route.has_optional_params = True

    def _parse_file_based_params(self, route: RemixRouteInfo, file_path: str) -> None:
        """Parse dynamic params from file-based routing conventions."""
        # Remix v2 flat routes: $param
        flat_params = self.FLAT_ROUTE_DYNAMIC.findall(file_path)
        if flat_params:
            route.has_dynamic_params = True
            route.dynamic_params = flat_params

        # Remix v1: /$param
        v1_params = self.V1_DYNAMIC_SEGMENT.findall(file_path)
        if v1_params:
            route.has_dynamic_params = True
            route.dynamic_params = list(set(route.dynamic_params + v1_params))

        # Splat route: $.tsx or [...].tsx
        import os
        basename = os.path.basename(file_path)
        if basename.startswith('$.') or basename == '$.tsx' or '[...' in basename:
            route.has_splat = True

    def _detect_route_type(self, file_path: str) -> str:
        """Detect route type from file path."""
        if not file_path:
            return "page"

        import os
        basename = os.path.basename(file_path).lower()
        dir_name = os.path.dirname(file_path).lower()

        if 'root' in basename:
            return "root"
        if '_layout' in basename or basename.startswith('__'):
            return "layout"
        if '_index' in basename or basename == 'index.tsx' or basename == 'index.ts':
            return "index"
        if '_error' in basename or 'error' in basename:
            return "error"
        if 'routes.ts' in basename or 'routes.js' in basename:
            return "config"
        if basename.startswith('resource.') or '.resource.' in basename:
            return "resource"

        return "page"

    @staticmethod
    def _path_to_name(path: str) -> str:
        """Convert a route path to a name."""
        return path.strip('/').replace('/', '_').replace(':', '').replace('*', 'splat') or "root"
