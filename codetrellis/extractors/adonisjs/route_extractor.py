"""
AdonisJS route extractor - Extract Route definitions, groups, resources, and params.

Extracts:
- Route.get/post/put/patch/delete/any() calls
- Route.resource() resourceful routes
- Route.group(() => { ... }) with prefix/middleware/namespace
- Route params (:id, :slug) and optional params (:id?)
- Route naming (.as('users.index'))
- Route middleware (.middleware(['auth']))
- Route domain (.domain('api.example.com'))
- Route where constraints (.where('id', /^[0-9]+$/)

Supports AdonisJS v4 (Route.get), v5 (Route.get), v6 (router.get) patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AdonisRouteInfo:
    """Information about a single AdonisJS route."""
    method: str = ""            # GET, POST, PUT, DELETE, PATCH, ANY
    path: str = ""              # /users/:id
    handler: str = ""           # 'UsersController.show' or closure
    name: str = ""              # route name (.as('users.show'))
    middleware: List[str] = field(default_factory=list)
    domain: str = ""
    params: List[str] = field(default_factory=list)         # ['id']
    where_constraints: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0
    is_api: bool = False        # in api group


@dataclass
class AdonisRouteGroupInfo:
    """Information about a route group."""
    prefix: str = ""
    middleware: List[str] = field(default_factory=list)
    namespace: str = ""
    domain: str = ""
    name: str = ""              # group name prefix
    route_count: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class AdonisResourceRouteInfo:
    """Information about a resource route."""
    resource: str = ""          # 'users'
    controller: str = ""        # 'UsersController'
    only: List[str] = field(default_factory=list)       # subset of actions
    except_actions: List[str] = field(default_factory=list)  # excluded actions
    middleware: Dict[str, List[str]] = field(default_factory=dict)
    api_only: bool = False      # .apiOnly() — excludes create/edit
    file: str = ""
    line_number: int = 0


class AdonisRouteExtractor:
    """Extract AdonisJS route definitions."""

    # HTTP method route calls: Route.get('/path', 'Controller.method') or Route.get('/path', handler)
    ROUTE_METHOD_PATTERN = re.compile(
        r'(?:Route|router)\.(?:get|post|put|patch|delete|any|options|head)\s*\(\s*'
        r"['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*(?:['\"]([^'\"]+)['\"]|(\w+)))?",
        re.MULTILINE | re.IGNORECASE,
    )

    # Route method name extraction (get, post, etc.)
    ROUTE_HTTP_METHOD_PATTERN = re.compile(
        r'(?:Route|router)\.(get|post|put|patch|delete|any|options|head)\s*\(',
        re.MULTILINE | re.IGNORECASE,
    )

    # Route.resource('users', 'UsersController')
    RESOURCE_PATTERN = re.compile(
        r"(?:Route|router)\.resource\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*['\"]([^'\"]+)['\"])?",
        re.MULTILINE,
    )

    # Route.group(() => { ... }) or Route.group({ ... })
    GROUP_PATTERN = re.compile(
        r'(?:Route|router)\.group\s*\(',
        re.MULTILINE,
    )

    # Chain methods: .as('name'), .middleware([...]), .prefix('/api'), .namespace('App/Controllers')
    AS_PATTERN = re.compile(
        r"\.as\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    MIDDLEWARE_PATTERN = re.compile(
        r"\.middleware\s*\(\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )

    PREFIX_PATTERN = re.compile(
        r"\.prefix\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    NAMESPACE_PATTERN = re.compile(
        r"\.namespace\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    DOMAIN_PATTERN = re.compile(
        r"\.domain\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    WHERE_PATTERN = re.compile(
        r"\.where\s*\(\s*['\"](\w+)['\"]\s*,\s*(?:\/([^\/]+)\/|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )

    # .apiOnly()
    API_ONLY_PATTERN = re.compile(r'\.apiOnly\s*\(', re.MULTILINE)

    # .only() and .except()
    ONLY_PATTERN = re.compile(
        r"\.only\s*\(\s*\[([^\]]*)\]",
        re.MULTILINE,
    )

    EXCEPT_PATTERN = re.compile(
        r"\.except\s*\(\s*\[([^\]]*)\]",
        re.MULTILINE,
    )

    # Route params: :id, :slug, :id?
    PARAM_PATTERN = re.compile(r':(\w+\??)')

    # v5/v6 controller reference: [UsersController, 'index'] or '#controllers/users'
    CONTROLLER_ARRAY_PATTERN = re.compile(
        r"\[\s*(\w+Controller)\s*,\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    CONTROLLER_HASH_PATTERN = re.compile(
        r"['\"]#controllers/([^'\"]+)['\"]",
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all AdonisJS route information from source code.

        Returns:
            Dict with 'routes' (List[AdonisRouteInfo]),
                       'groups' (List[AdonisRouteGroupInfo]),
                       'resources' (List[AdonisResourceRouteInfo])
        """
        routes: List[AdonisRouteInfo] = []
        groups: List[AdonisRouteGroupInfo] = []
        resources: List[AdonisResourceRouteInfo] = []

        # ── Extract individual routes ────────────────────────────
        for method_match in self.ROUTE_HTTP_METHOD_PATTERN.finditer(content):
            http_method = method_match.group(1).upper()
            line_number = content[:method_match.start()].count('\n') + 1

            # Get the full route call
            route_start = method_match.start()
            # Find the end — look for the next newline or semicolon after possible chain
            route_end = min(route_start + 500, len(content))
            route_block = content[route_start:route_end]

            # Extract path
            path_match = re.search(r"['\"]([^'\"]+)['\"]", route_block)
            if not path_match:
                continue

            path = path_match.group(1)

            route = AdonisRouteInfo(
                method=http_method,
                path=path,
                file=file_path,
                line_number=line_number,
            )

            # Extract params from path
            route.params = [p.rstrip('?') for p in self.PARAM_PATTERN.findall(path)]

            # Handler: string reference or v5 array or v6 hash
            handler_match = self.ROUTE_METHOD_PATTERN.search(route_block)
            if handler_match:
                route.handler = handler_match.group(2) or handler_match.group(3) or ''

            # v5/v6: [Controller, 'method']
            ctrl_match = self.CONTROLLER_ARRAY_PATTERN.search(route_block)
            if ctrl_match:
                route.handler = f"{ctrl_match.group(1)}.{ctrl_match.group(2)}"

            # v6: '#controllers/users.index'
            hash_match = self.CONTROLLER_HASH_PATTERN.search(route_block)
            if hash_match:
                route.handler = hash_match.group(1)

            # Route name
            as_match = self.AS_PATTERN.search(route_block)
            if as_match:
                route.name = as_match.group(1)

            # Middleware
            mw_match = self.MIDDLEWARE_PATTERN.search(route_block)
            if mw_match:
                mw_str = mw_match.group(1) or mw_match.group(2) or ''
                route.middleware = [m.strip().strip("'\"") for m in mw_str.split(',') if m.strip()]

            # Domain
            domain_match = self.DOMAIN_PATTERN.search(route_block)
            if domain_match:
                route.domain = domain_match.group(1)

            # Where constraints
            for where_match in self.WHERE_PATTERN.finditer(route_block):
                param = where_match.group(1)
                constraint = where_match.group(2) or where_match.group(3) or ''
                route.where_constraints[param] = constraint

            routes.append(route)

        # ── Extract route groups ─────────────────────────────────
        for match in self.GROUP_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            block_start = match.start()
            block_end = min(block_start + 2000, len(content))
            block = content[block_start:block_end]

            group = AdonisRouteGroupInfo(
                file=file_path,
                line_number=line_number,
            )

            # Prefix
            prefix_match = self.PREFIX_PATTERN.search(block)
            if prefix_match:
                group.prefix = prefix_match.group(1)

            # Middleware
            mw_match = self.MIDDLEWARE_PATTERN.search(block)
            if mw_match:
                mw_str = mw_match.group(1) or mw_match.group(2) or ''
                group.middleware = [m.strip().strip("'\"") for m in mw_str.split(',') if m.strip()]

            # Namespace
            ns_match = self.NAMESPACE_PATTERN.search(block)
            if ns_match:
                group.namespace = ns_match.group(1)

            # Domain
            domain_match = self.DOMAIN_PATTERN.search(block)
            if domain_match:
                group.domain = domain_match.group(1)

            # Name prefix
            as_match = self.AS_PATTERN.search(block)
            if as_match:
                group.name = as_match.group(1)

            groups.append(group)

        # ── Extract resource routes ──────────────────────────────
        for match in self.RESOURCE_PATTERN.finditer(content):
            resource_name = match.group(1)
            controller = match.group(2) or ''
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]

            resource = AdonisResourceRouteInfo(
                resource=resource_name,
                controller=controller,
                file=file_path,
                line_number=line_number,
            )

            # .apiOnly()
            resource.api_only = bool(self.API_ONLY_PATTERN.search(block))

            # .only([...])
            only_match = self.ONLY_PATTERN.search(block)
            if only_match:
                resource.only = [a.strip().strip("'\"") for a in only_match.group(1).split(',') if a.strip()]

            # .except([...])
            except_match = self.EXCEPT_PATTERN.search(block)
            if except_match:
                resource.except_actions = [a.strip().strip("'\"") for a in except_match.group(1).split(',') if a.strip()]

            resources.append(resource)

        return {
            'routes': routes,
            'groups': groups,
            'resources': resources,
        }
