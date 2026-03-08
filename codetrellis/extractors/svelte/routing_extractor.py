"""
Svelte Routing Extractor for CodeTrellis

Extracts routing information from SvelteKit source code:
- File-based routes (+page.svelte, +layout.svelte, +error.svelte)
- Server routes (+server.ts/js with GET/POST/PUT/PATCH/DELETE/OPTIONS)
- Page load functions (+page.ts, +page.server.ts, +layout.ts, +layout.server.ts)
- Form actions (+page.server.ts actions)
- Hooks (hooks.server.ts, hooks.client.ts, hooks.ts)
- Param matchers (params/*.ts)
- Route groups ((group)/route)
- Rest params ([...rest])
- Optional params ([[optional]])
- Layout groups and layout resets (+layout@.svelte)

Supports SvelteKit 1.x through 2.x:
- SvelteKit 1.x: load functions, form actions, hooks, adapter system
- SvelteKit 2.x: shallow routing, enhanced forms, improved hooks,
                  universal/server load distinction, streaming

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SvelteRouteInfo:
    """Information about a SvelteKit route."""
    path: str  # route path pattern
    file: str = ""
    file_type: str = ""  # page, layout, error, server, api
    line_number: int = 0
    has_load: bool = False
    has_server_load: bool = False
    has_actions: bool = False
    is_api_route: bool = False  # +server.ts
    http_methods: List[str] = field(default_factory=list)  # GET, POST, etc.
    params: List[str] = field(default_factory=list)  # route parameters
    is_dynamic: bool = False  # has [param] segments
    is_rest: bool = False  # has [...rest] segments
    is_optional: bool = False  # has [[optional]] segments
    group: str = ""  # route group name (group)
    layout_id: str = ""  # layout inheritance @


@dataclass
class SvelteLoadFunctionInfo:
    """Information about a SvelteKit load function."""
    name: str  # 'load' or custom
    file: str = ""
    line_number: int = 0
    is_server: bool = False  # +page.server.ts vs +page.ts
    is_universal: bool = False  # +page.ts (runs on both client/server)
    returns_type: str = ""  # TypeScript return type
    uses_fetch: bool = False
    uses_depends: bool = False
    uses_parent: bool = False
    uses_cookies: bool = False
    uses_locals: bool = False
    uses_params: bool = False
    uses_url: bool = False
    uses_platform: bool = False
    is_streaming: bool = False  # returns deferred data


@dataclass
class SvelteFormActionInfo:
    """Information about a SvelteKit form action."""
    name: str  # action name or 'default'
    file: str = ""
    line_number: int = 0
    is_default: bool = False
    uses_request: bool = False
    uses_cookies: bool = False
    uses_locals: bool = False
    returns_fail: bool = False  # uses fail()
    returns_redirect: bool = False  # uses redirect()


@dataclass
class SvelteHookInfo:
    """Information about a SvelteKit hook."""
    name: str  # handle, handleFetch, handleError, etc.
    file: str = ""
    line_number: int = 0
    hook_type: str = ""  # server, client, shared
    is_sequence: bool = False  # uses sequence() helper


@dataclass
class SvelteParamMatcherInfo:
    """Information about a SvelteKit param matcher."""
    name: str
    file: str = ""
    line_number: int = 0
    pattern: str = ""  # regex or validation logic description


class SvelteRoutingExtractor:
    """
    Extracts SvelteKit routing information.

    Handles:
    - File-based route detection from file paths
    - Load function extraction from +page.ts/+page.server.ts
    - Form action extraction from +page.server.ts
    - Hook extraction from hooks.server.ts/hooks.client.ts
    - Param matcher extraction from params/*.ts
    """

    # Load function patterns
    LOAD_PATTERN = re.compile(
        r'export\s+(?:const|(?:async\s+)?function)\s+(load)\s*'
        r'(?::\s*\w+\s*)?[=(]',
        re.MULTILINE
    )
    LOAD_ARROW_PATTERN = re.compile(
        r'export\s+const\s+load\s*(?::\s*\w+\s*)?=\s*(?:async\s*)?\(',
        re.MULTILINE
    )

    # Server route HTTP method patterns
    HTTP_METHOD_PATTERN = re.compile(
        r'export\s+(?:const|(?:async\s+)?function)\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|FALLBACK)\b',
        re.MULTILINE
    )

    # Form actions patterns
    ACTIONS_PATTERN = re.compile(
        r'export\s+const\s+actions\s*(?::\s*Actions)?\s*=\s*\{',
        re.MULTILINE
    )
    ACTION_ENTRY_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:async\s*)?\(',
        re.MULTILINE
    )
    ACTION_DEFAULT_PATTERN = re.compile(
        r'default\s*:\s*(?:async\s*)?\(',
        re.MULTILINE
    )

    # Hook patterns
    HOOK_PATTERN = re.compile(
        r'export\s+(?:const|(?:async\s+)?function)\s+'
        r'(handle|handleFetch|handleError|getSession|externalFetch|init)\b',
        re.MULTILINE
    )
    SEQUENCE_PATTERN = re.compile(
        r'sequence\s*\(',
        re.MULTILINE
    )

    # Param matcher pattern
    PARAM_MATCHER_PATTERN = re.compile(
        r'export\s+(?:const\s+)?match\s*[=:]',
        re.MULTILINE
    )

    # Load function helpers
    FETCH_PATTERN = re.compile(r'\bfetch\s*\(', re.MULTILINE)
    DEPENDS_PATTERN = re.compile(r'\bdepends\s*\(', re.MULTILINE)
    PARENT_PATTERN = re.compile(r'\bparent\s*\(', re.MULTILINE)
    COOKIES_PATTERN = re.compile(r'\bcookies\b', re.MULTILINE)
    LOCALS_PATTERN = re.compile(r'\blocals\b', re.MULTILINE)
    PARAMS_PATTERN = re.compile(r'\bparams\b', re.MULTILINE)
    URL_PATTERN = re.compile(r'\burl\b', re.MULTILINE)
    PLATFORM_PATTERN = re.compile(r'\bplatform\b', re.MULTILINE)

    # Fail/redirect patterns
    FAIL_PATTERN = re.compile(r'\bfail\s*\(', re.MULTILINE)
    REDIRECT_PATTERN = re.compile(r'\bredirect\s*\(', re.MULTILINE)

    # Route path extraction from file path
    ROUTE_PATH_PATTERN = re.compile(
        r'src/routes/(.*?)(?:\+page|\+layout|\+error|\+server|\+page\.server|\+layout\.server)',
    )
    PARAM_SEGMENT_PATTERN = re.compile(r'\[([^\]]+)\]')
    REST_SEGMENT_PATTERN = re.compile(r'\[\.\.\.([\w]+)\]')
    OPTIONAL_SEGMENT_PATTERN = re.compile(r'\[\[([\w]+)\]\]')
    GROUP_SEGMENT_PATTERN = re.compile(r'\((\w+)\)')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract routing information from source content.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'routes', 'load_functions', 'form_actions', 'hooks', 'param_matchers'
        """
        routes = []
        load_functions = []
        form_actions = []
        hooks = []
        param_matchers = []

        # Extract route info from file path
        route_info = self._extract_route_from_path(file_path)
        if route_info:
            routes.append(route_info)

        # Extract load functions
        load_funcs = self._extract_load_functions(content, file_path)
        load_functions.extend(load_funcs)

        # Update route with load info
        if routes and load_funcs:
            for lf in load_funcs:
                if lf.is_server:
                    routes[0].has_server_load = True
                else:
                    routes[0].has_load = True

        # Extract server route HTTP methods
        http_methods = self._extract_http_methods(content, file_path)
        if routes and http_methods:
            routes[0].http_methods = http_methods
            routes[0].is_api_route = True

        # Extract form actions
        actions = self._extract_form_actions(content, file_path)
        form_actions.extend(actions)
        if routes and actions:
            routes[0].has_actions = True

        # Extract hooks
        hook_list = self._extract_hooks(content, file_path)
        hooks.extend(hook_list)

        # Extract param matchers
        matchers = self._extract_param_matchers(content, file_path)
        param_matchers.extend(matchers)

        return {
            'routes': routes,
            'load_functions': load_functions,
            'form_actions': form_actions,
            'hooks': hooks,
            'param_matchers': param_matchers,
        }

    def _extract_route_from_path(self, file_path: str) -> Optional[SvelteRouteInfo]:
        """Extract route information from file path."""
        if not file_path:
            return None

        # Normalize path separators
        normalized = file_path.replace('\\', '/')

        match = self.ROUTE_PATH_PATTERN.search(normalized)
        if not match:
            return None

        route_dir = match.group(1)

        # Determine file type
        file_type = 'page'
        if '+server' in normalized:
            file_type = 'server'
        elif '+layout.server' in normalized:
            file_type = 'layout_server'
        elif '+layout' in normalized:
            file_type = 'layout'
        elif '+error' in normalized:
            file_type = 'error'
        elif '+page.server' in normalized:
            file_type = 'page_server'

        # Build route path
        path = '/' + route_dir.rstrip('/')
        # Remove route groups from path
        path = re.sub(r'\([^)]+\)/?', '', path)
        # Convert param segments
        path = re.sub(r'\[\.\.\.([\w]+)\]', r'*\1', path)  # rest params
        path = re.sub(r'\[\[([\w]+)\]\]', r':\1?', path)  # optional params
        path = re.sub(r'\[([\w=]+)\]', r':\1', path)  # dynamic params
        path = path.rstrip('/') or '/'

        # Extract params
        params = self.PARAM_SEGMENT_PATTERN.findall(route_dir)

        # Detect route features
        is_dynamic = bool(self.PARAM_SEGMENT_PATTERN.search(route_dir))
        is_rest = bool(self.REST_SEGMENT_PATTERN.search(route_dir))
        is_optional = bool(self.OPTIONAL_SEGMENT_PATTERN.search(route_dir))

        # Detect groups
        group_match = self.GROUP_SEGMENT_PATTERN.search(route_dir)
        group = group_match.group(1) if group_match else ''

        return SvelteRouteInfo(
            path=path,
            file=file_path,
            file_type=file_type,
            params=params,
            is_dynamic=is_dynamic,
            is_rest=is_rest,
            is_optional=is_optional,
            group=group,
        )

    def _extract_load_functions(self, content: str, file_path: str) -> List[SvelteLoadFunctionInfo]:
        """Extract load function definitions."""
        functions = []

        has_load = bool(self.LOAD_PATTERN.search(content)) or bool(self.LOAD_ARROW_PATTERN.search(content))
        if not has_load:
            return functions

        is_server = '+page.server' in file_path or '+layout.server' in file_path
        is_universal = ('+page.ts' in file_path or '+page.js' in file_path or
                        '+layout.ts' in file_path or '+layout.js' in file_path)

        load_func = SvelteLoadFunctionInfo(
            name='load',
            file=file_path,
            line_number=1,
            is_server=is_server,
            is_universal=is_universal and not is_server,
            uses_fetch=bool(self.FETCH_PATTERN.search(content)),
            uses_depends=bool(self.DEPENDS_PATTERN.search(content)),
            uses_parent=bool(self.PARENT_PATTERN.search(content)),
            uses_cookies=bool(self.COOKIES_PATTERN.search(content)),
            uses_locals=bool(self.LOCALS_PATTERN.search(content)),
            uses_params=bool(self.PARAMS_PATTERN.search(content)),
            uses_url=bool(self.URL_PATTERN.search(content)),
            uses_platform=bool(self.PLATFORM_PATTERN.search(content)),
        )
        functions.append(load_func)

        return functions

    def _extract_http_methods(self, content: str, file_path: str) -> List[str]:
        """Extract HTTP method handlers from +server.ts files."""
        methods = []
        for match in self.HTTP_METHOD_PATTERN.finditer(content):
            methods.append(match.group(1))
        return methods

    def _extract_form_actions(self, content: str, file_path: str) -> List[SvelteFormActionInfo]:
        """Extract form actions from +page.server.ts."""
        actions = []

        if not self.ACTIONS_PATTERN.search(content):
            return actions

        # Find actions block
        actions_match = self.ACTIONS_PATTERN.search(content)
        if not actions_match:
            return actions

        # Extract the actions object body
        start = actions_match.end() - 1  # include the opening brace
        brace_count = 0
        actions_body = ''
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    actions_body = content[start:i+1]
                    break

        # Check for default action
        if self.ACTION_DEFAULT_PATTERN.search(actions_body):
            action = SvelteFormActionInfo(
                name='default',
                file=file_path,
                line_number=content[:actions_match.start()].count('\n') + 1,
                is_default=True,
                uses_request='request' in actions_body,
                uses_cookies=bool(self.COOKIES_PATTERN.search(actions_body)),
                uses_locals=bool(self.LOCALS_PATTERN.search(actions_body)),
                returns_fail=bool(self.FAIL_PATTERN.search(actions_body)),
                returns_redirect=bool(self.REDIRECT_PATTERN.search(actions_body)),
            )
            actions.append(action)

        # Named actions
        for match in self.ACTION_ENTRY_PATTERN.finditer(actions_body):
            name = match.group(1)
            if name == 'default':
                continue

            action = SvelteFormActionInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_default=False,
                uses_request='request' in actions_body,
                uses_cookies=bool(self.COOKIES_PATTERN.search(actions_body)),
            )
            actions.append(action)

        return actions

    def _extract_hooks(self, content: str, file_path: str) -> List[SvelteHookInfo]:
        """Extract SvelteKit hooks."""
        hooks = []

        # Determine hook type from file name
        hook_type = 'server'
        if 'hooks.client' in file_path:
            hook_type = 'client'
        elif 'hooks.ts' in file_path or 'hooks.js' in file_path:
            hook_type = 'shared'

        for match in self.HOOK_PATTERN.finditer(content):
            name = match.group(1)
            hook = SvelteHookInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                hook_type=hook_type,
                is_sequence=bool(self.SEQUENCE_PATTERN.search(content)),
            )
            hooks.append(hook)

        return hooks

    def _extract_param_matchers(self, content: str, file_path: str) -> List[SvelteParamMatcherInfo]:
        """Extract param matcher definitions."""
        matchers = []

        if not self.PARAM_MATCHER_PATTERN.search(content):
            return matchers

        import os
        name = os.path.basename(file_path).rsplit('.', 1)[0] if file_path else 'unknown'

        matcher = SvelteParamMatcherInfo(
            name=name,
            file=file_path,
            line_number=1,
        )
        matchers.append(matcher)

        return matchers
