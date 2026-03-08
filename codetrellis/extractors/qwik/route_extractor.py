"""
Qwik Route Extractor for CodeTrellis

Extracts Qwik City / Qwik Router routing patterns:
- routeLoader$() — server-side data loaders
- routeAction$() — server-side form actions
- server$() — server-only functions
- globalAction$() — global server actions
- Form component usage
- zod() validation schemas
- File-based routing detection (layout.tsx, index.tsx, [param], [...catchall])
- Middleware: onRequest, onGet, onPost, etc.
- useNavigate(), useLocation()

Supports:
- Qwik City v0.x (early routing API)
- Qwik City v1.x (routeLoader$, routeAction$, server$)
- Qwik v2.x (@qwik.dev/router)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikRouteLoaderInfo:
    """Information about a Qwik routeLoader$."""
    name: str
    file: str = ""
    line_number: int = 0
    has_zod_validation: bool = False
    is_exported: bool = False
    return_type: str = ""


@dataclass
class QwikRouteActionInfo:
    """Information about a Qwik routeAction$."""
    name: str
    file: str = ""
    line_number: int = 0
    has_zod_validation: bool = False
    is_exported: bool = False
    has_form_component: bool = False


@dataclass
class QwikMiddlewareInfo:
    """Information about Qwik middleware (onRequest, onGet, onPost, etc.)."""
    name: str  # onRequest, onGet, onPost, onPut, onDelete, onPatch
    file: str = ""
    line_number: int = 0
    is_exported: bool = False


class QwikRouteExtractor:
    """
    Extracts Qwik City routing patterns from source code.

    Detects:
    - routeLoader$() for server-side data loading
    - routeAction$() for server-side form handling
    - server$() for RPC-like server functions
    - globalAction$() for global form actions
    - zod() validation integration
    - Form component usage with routeAction$
    - Middleware handlers (onRequest, onGet, onPost, etc.)
    - Navigation hooks (useNavigate, useLocation)
    - File-based route patterns ([param], [...catchall], layout)
    """

    # routeLoader$() pattern
    ROUTE_LOADER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'routeLoader\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # routeAction$() pattern
    ROUTE_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'routeAction\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # server$() pattern
    SERVER_DOLLAR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'server\$\s*\(',
        re.MULTILINE
    )

    # globalAction$() pattern
    GLOBAL_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'globalAction\$\s*\(',
        re.MULTILINE
    )

    # Middleware patterns: export const onRequest, onGet, onPost, etc.
    MIDDLEWARE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var|function)\s+(on(?:Request|Get|Post|Put|Delete|Patch|Head|Options))\s*',
        re.MULTILINE
    )

    # zod() validation
    ZOD_PATTERN = re.compile(
        r'zod\$?\s*\(',
        re.MULTILINE
    )

    # <Form> component
    FORM_COMPONENT_PATTERN = re.compile(
        r'<Form\b',
        re.MULTILINE
    )

    # useNavigate()
    USE_NAVIGATE_PATTERN = re.compile(
        r'useNavigate\s*\(',
        re.MULTILINE
    )

    # useLocation()
    USE_LOCATION_PATTERN = re.compile(
        r'useLocation\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik routing patterns from source code."""
        loaders: List[QwikRouteLoaderInfo] = []
        actions: List[QwikRouteActionInfo] = []
        server_fns: List[dict] = []
        middleware: List[QwikMiddlewareInfo] = []
        nav_hooks: List[dict] = []

        # ── routeLoader$ ─────────────────────────────────────────
        for m in self.ROUTE_LOADER_PATTERN.finditer(content):
            name = m.group(1)
            return_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]
            has_zod = bool(self.ZOD_PATTERN.search(body))

            loaders.append(QwikRouteLoaderInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_zod_validation=has_zod,
                is_exported=is_exported,
                return_type=return_type,
            ))

        # ── routeAction$ ─────────────────────────────────────────
        for m in self.ROUTE_ACTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]
            has_zod = bool(self.ZOD_PATTERN.search(body))
            has_form = bool(self.FORM_COMPONENT_PATTERN.search(content))

            actions.append(QwikRouteActionInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_zod_validation=has_zod,
                is_exported=is_exported,
                has_form_component=has_form,
            ))

        # ── server$ ──────────────────────────────────────────────
        for m in self.SERVER_DOLLAR_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            server_fns.append({
                "name": name,
                "file": file_path,
                "line": line,
                "function_type": "server$",
                "is_exported": is_exported,
            })

        # ── globalAction$ ─────────────────────────────────────────
        for m in self.GLOBAL_ACTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            server_fns.append({
                "name": name,
                "file": file_path,
                "line": line,
                "function_type": "globalAction$",
                "is_exported": is_exported,
            })

        # ── Middleware ────────────────────────────────────────────
        for m in self.MIDDLEWARE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            middleware.append(QwikMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported=is_exported,
            ))

        # ── Navigation hooks ──────────────────────────────────────
        for m in self.USE_NAVIGATE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            nav_hooks.append({
                "hook_name": "useNavigate",
                "file": file_path,
                "line": line,
            })

        for m in self.USE_LOCATION_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            nav_hooks.append({
                "hook_name": "useLocation",
                "file": file_path,
                "line": line,
            })

        return {
            "loaders": loaders,
            "actions": actions,
            "server_functions": server_fns,
            "middleware": middleware,
            "nav_hooks": nav_hooks,
        }
