"""
Route Extractor for Angular Routes

Extracts route definitions from Angular route configuration files (*.routes.ts).
Supports:
- Basic routes with path and component
- Redirect routes
- Route parameters (:id, :symbol)
- Child routes (nested)
- Lazy-loaded routes (loadComponent, loadChildren)
- Route guards (canActivate, canDeactivate, etc.)
- Route data and resolve

Part of CodeTrellis v2.0 - Phase 3 Implementation
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class RouteGuardInfo:
    """Information about a route guard"""
    type: str  # canActivate, canDeactivate, canMatch, canLoad, resolve
    guards: List[str]  # List of guard names/functions


@dataclass
class RouteInfo:
    """Information about a single route definition"""
    path: str
    component: Optional[str] = None
    redirect_to: Optional[str] = None
    path_match: Optional[str] = None  # 'full' or 'prefix'
    title: Optional[str] = None
    lazy_load: Optional[str] = None  # loadComponent or loadChildren path
    lazy_load_type: Optional[str] = None  # 'component' or 'children'
    guards: List[RouteGuardInfo] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    children: List['RouteInfo'] = field(default_factory=list)
    params: List[str] = field(default_factory=list)  # Route parameters like :id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {'path': self.path}

        if self.component:
            result['component'] = self.component
        if self.redirect_to:
            result['redirectTo'] = self.redirect_to
        if self.path_match:
            result['pathMatch'] = self.path_match
        if self.title:
            result['title'] = self.title
        if self.lazy_load:
            result['lazyLoad'] = {
                'type': self.lazy_load_type,
                'path': self.lazy_load
            }
        if self.guards:
            result['guards'] = [
                {'type': g.type, 'guards': g.guards}
                for g in self.guards
            ]
        if self.data:
            result['data'] = self.data
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        if self.params:
            result['params'] = self.params

        return result

    def to_codetrellis_format(self) -> str:
        """Convert to CodeTrellis output format"""
        parts = [f"path: '{self.path}'"]

        if self.component:
            parts.append(f"component: {self.component}")
        if self.redirect_to:
            parts.append(f"redirectTo: '{self.redirect_to}'")
        if self.path_match:
            parts.append(f"pathMatch: '{self.path_match}'")
        if self.title:
            parts.append(f"title: '{self.title}'")
        if self.lazy_load:
            parts.append(f"lazy({self.lazy_load_type}): {self.lazy_load}")
        if self.guards:
            for guard in self.guards:
                parts.append(f"{guard.type}: [{', '.join(guard.guards)}]")
        if self.params:
            parts.append(f"params: [{', '.join(self.params)}]")
        if self.children:
            parts.append(f"children: {len(self.children)} routes")

        return ' | '.join(parts)


@dataclass
class RoutesFileInfo:
    """Information about a routes file"""
    file_path: str
    export_name: str  # Usually 'routes'
    routes: List[RouteInfo] = field(default_factory=list)
    total_routes: int = 0
    lazy_routes: int = 0
    guarded_routes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filePath': self.file_path,
            'exportName': self.export_name,
            'routes': [r.to_dict() for r in self.routes],
            'stats': {
                'totalRoutes': self.total_routes,
                'lazyRoutes': self.lazy_routes,
                'guardedRoutes': self.guarded_routes
            }
        }


class RouteExtractor:
    """
    Extracts Angular route definitions from *.routes.ts files.

    Supports Angular 14+ standalone routes and traditional NgModule routes.
    """

    # Pattern to match route array export
    ROUTES_EXPORT_PATTERN = re.compile(
        r'export\s+const\s+(\w+)\s*:\s*Routes\s*=\s*\[',
        re.MULTILINE
    )

    # Pattern to match route parameters in path
    ROUTE_PARAM_PATTERN = re.compile(r':(\w+)')

    # Guard types
    GUARD_TYPES = [
        'canActivate', 'canActivateChild', 'canDeactivate',
        'canMatch', 'canLoad', 'resolve'
    ]

    def __init__(self):
        self.routes_files: List[RoutesFileInfo] = []

    def can_extract(self, file_path: str, content: str) -> bool:
        """Check if this file contains Angular routes"""
        # Check file name pattern
        if not file_path.endswith('.routes.ts'):
            # Also check for route patterns in app-routing.module.ts
            if 'routing.module.ts' not in file_path:
                return False

        # Check for Routes import and export
        has_routes_import = 'Routes' in content and '@angular/router' in content
        has_routes_export = bool(self.ROUTES_EXPORT_PATTERN.search(content))

        return has_routes_import and has_routes_export

    def extract(self, file_path: str, content: str) -> Optional[RoutesFileInfo]:
        """Extract routes from a routes file"""
        if not self.can_extract(file_path, content):
            return None

        # Find the routes export
        export_match = self.ROUTES_EXPORT_PATTERN.search(content)
        if not export_match:
            return None

        export_name = export_match.group(1)
        start_pos = export_match.end() - 1  # Position of opening [

        # Extract the routes array content
        routes_content = self._extract_array_content(content, start_pos)
        if not routes_content:
            return None

        # Parse individual routes
        routes = self._parse_routes_array(routes_content)

        # Calculate stats
        total_routes = self._count_total_routes(routes)
        lazy_routes = self._count_lazy_routes(routes)
        guarded_routes = self._count_guarded_routes(routes)

        routes_file = RoutesFileInfo(
            file_path=file_path,
            export_name=export_name,
            routes=routes,
            total_routes=total_routes,
            lazy_routes=lazy_routes,
            guarded_routes=guarded_routes
        )

        self.routes_files.append(routes_file)
        return routes_file

    def _extract_array_content(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content between matching brackets starting at start_pos"""
        if content[start_pos] != '[':
            return None

        bracket_count = 0
        end_pos = start_pos

        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i
                    break

        if bracket_count != 0:
            return None

        return content[start_pos + 1:end_pos]

    def _parse_routes_array(self, content: str) -> List[RouteInfo]:
        """Parse routes from array content"""
        routes = []

        # Find each route object { ... }
        route_objects = self._extract_route_objects(content)

        for route_obj in route_objects:
            route_info = self._parse_single_route(route_obj)
            if route_info:
                routes.append(route_info)

        return routes

    def _extract_route_objects(self, content: str) -> List[str]:
        """Extract individual route objects from array content"""
        objects = []
        brace_count = 0
        current_object = []
        in_string = False
        string_char = None

        i = 0
        while i < len(content):
            char = content[i]

            # Handle string literals
            if char in '"\'`' and (i == 0 or content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None

            if not in_string:
                if char == '{':
                    brace_count += 1
                    if brace_count == 1:
                        current_object = [char]
                    else:
                        current_object.append(char)
                elif char == '}':
                    brace_count -= 1
                    current_object.append(char)
                    if brace_count == 0:
                        objects.append(''.join(current_object))
                        current_object = []
                elif brace_count > 0:
                    current_object.append(char)
            elif brace_count > 0:
                current_object.append(char)

            i += 1

        return objects

    def _parse_single_route(self, route_obj: str) -> Optional[RouteInfo]:
        """Parse a single route object"""
        # Extract path
        path_match = re.search(r"path\s*:\s*['\"]([^'\"]*)['\"]", route_obj)
        if not path_match:
            return None

        path = path_match.group(1)

        # Extract route parameters from path
        params = self.ROUTE_PARAM_PATTERN.findall(path)

        route = RouteInfo(path=path, params=params)

        # Extract component
        comp_match = re.search(r'component\s*:\s*(\w+)', route_obj)
        if comp_match:
            route.component = comp_match.group(1)

        # Extract redirectTo
        redirect_match = re.search(r"redirectTo\s*:\s*['\"]([^'\"]*)['\"]", route_obj)
        if redirect_match:
            route.redirect_to = redirect_match.group(1)

        # Extract pathMatch
        pathmatch_match = re.search(r"pathMatch\s*:\s*['\"](\w+)['\"]", route_obj)
        if pathmatch_match:
            route.path_match = pathmatch_match.group(1)

        # Extract title
        title_match = re.search(r"title\s*:\s*['\"]([^'\"]*)['\"]", route_obj)
        if title_match:
            route.title = title_match.group(1)

        # Extract lazy loading
        lazy_comp_match = re.search(
            r'loadComponent\s*:\s*\(\)\s*=>\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            route_obj
        )
        if lazy_comp_match:
            route.lazy_load = lazy_comp_match.group(1)
            route.lazy_load_type = 'component'

        lazy_children_match = re.search(
            r'loadChildren\s*:\s*\(\)\s*=>\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            route_obj
        )
        if lazy_children_match:
            route.lazy_load = lazy_children_match.group(1)
            route.lazy_load_type = 'children'

        # Extract guards
        for guard_type in self.GUARD_TYPES:
            guard_match = re.search(
                rf'{guard_type}\s*:\s*\[([^\]]*)\]',
                route_obj
            )
            if guard_match:
                guards_str = guard_match.group(1)
                guard_names = [g.strip() for g in guards_str.split(',') if g.strip()]
                if guard_names:
                    route.guards.append(RouteGuardInfo(
                        type=guard_type,
                        guards=guard_names
                    ))

        # Extract children routes
        children_match = re.search(r'children\s*:\s*\[', route_obj)
        if children_match:
            children_start = children_match.end() - 1
            children_content = self._extract_array_content(route_obj, children_start)
            if children_content:
                route.children = self._parse_routes_array(children_content)

        # Extract data
        data_match = re.search(r'data\s*:\s*\{([^}]*)\}', route_obj)
        if data_match:
            # Simple key-value extraction for data
            data_str = data_match.group(1)
            for item in data_str.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    key = key.strip().strip("'\"")
                    value = value.strip().strip("'\"")
                    route.data[key] = value

        return route

    def _count_total_routes(self, routes: List[RouteInfo]) -> int:
        """Count total routes including children"""
        count = len(routes)
        for route in routes:
            count += self._count_total_routes(route.children)
        return count

    def _count_lazy_routes(self, routes: List[RouteInfo]) -> int:
        """Count lazy-loaded routes"""
        count = sum(1 for r in routes if r.lazy_load)
        for route in routes:
            count += self._count_lazy_routes(route.children)
        return count

    def _count_guarded_routes(self, routes: List[RouteInfo]) -> int:
        """Count routes with guards"""
        count = sum(1 for r in routes if r.guards)
        for route in routes:
            count += self._count_guarded_routes(route.children)
        return count

    def get_all_routes(self) -> List[RoutesFileInfo]:
        """Get all extracted routes files"""
        return self.routes_files

    def get_route_component_mapping(self) -> Dict[str, str]:
        """Get a mapping of paths to components"""
        mapping = {}

        def add_routes(routes: List[RouteInfo], prefix: str = ''):
            for route in routes:
                full_path = f"{prefix}/{route.path}".replace('//', '/')
                if route.component:
                    mapping[full_path] = route.component
                if route.children:
                    add_routes(route.children, full_path)

        for routes_file in self.routes_files:
            add_routes(routes_file.routes)

        return mapping

    def clear(self):
        """Clear all extracted routes"""
        self.routes_files = []
