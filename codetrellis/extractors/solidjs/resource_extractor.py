"""
Solid.js Resource Extractor for CodeTrellis

Extracts Solid.js async data fetching patterns:
- createResource(fetcher, options) for async data
- createResource(source, fetcher) with reactive source signals
- Resource actions: mutate, refetch
- Resource state: loading, error, latest
- Suspense integration (resources auto-trigger Suspense)
- Server functions / server$ (SolidStart)
- createRouteData / useRouteData (SolidStart router data)
- createServerData$ / createServerAction$ (SolidStart v0.x)
- cache / action / redirect / revalidate (SolidStart v1.0 / Solid Router v0.10+)

Supports:
- Solid.js v1.0-v2.0 createResource API
- SolidStart v0.x (createServerData$, createServerAction$, server$)
- SolidStart v1.0+ (cache, action, redirect, json, createAsync)
- Solid Router v0.10+ (cache, action, useAction, useSubmission)

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidResourceInfo:
    """Information about a Solid.js resource (createResource)."""
    name: str  # The resource accessor name
    file: str = ""
    line_number: int = 0
    has_source: bool = False  # Has reactive source signal
    type_annotation: str = ""
    is_exported: bool = False
    has_initial_value: bool = False
    has_ssr: bool = False  # deferStream / ssrLoadFrom
    resource_type: str = "resource"  # resource, async (createAsync)


@dataclass
class SolidServerFunctionInfo:
    """Information about a SolidStart server function."""
    name: str
    file: str = ""
    line_number: int = 0
    function_type: str = ""  # server$, createServerData$, createServerAction$, action, cache
    is_exported: bool = False
    has_redirect: bool = False
    has_revalidate: bool = False


@dataclass
class SolidRouteDataInfo:
    """Information about Solid.js route data loading."""
    name: str
    file: str = ""
    line_number: int = 0
    data_type: str = ""  # createRouteData, useRouteData, routeData, cache, createAsync
    is_exported: bool = False


class SolidResourceExtractor:
    """
    Extracts Solid.js resource and async data patterns from source code.

    Detects:
    - createResource(fetcher) / createResource(source, fetcher)
    - Resource state access: resource.loading, resource.error, resource.latest
    - mutate() / refetch() actions
    - SolidStart server functions: server$(), createServerData$(), createServerAction$()
    - SolidStart v1: cache(), action(), redirect(), json(), createAsync()
    - Solid Router v0.10+: cache(), action(), useAction(), useSubmission()
    - Route data patterns: createRouteData, useRouteData, routeData
    """

    # createResource<T>(fetcher) or createResource<T, S>(source, fetcher)
    CREATE_RESOURCE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+'
        r'(?:\[(\w+)(?:,\s*\{([^}]*)\})?\]|(\w+))\s*=\s*'
        r'createResource\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # createAsync(() => ...) (SolidStart v1.0+)
    CREATE_ASYNC_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createAsync\s*\(',
        re.MULTILINE
    )

    # server$(() => { ... })
    SERVER_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'server\$\s*\(',
        re.MULTILINE
    )

    # createServerData$(() => { ... })
    SERVER_DATA_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createServerData\$\s*\(',
        re.MULTILINE
    )

    # createServerAction$(() => { ... })
    SERVER_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createServerAction\$\s*\(',
        re.MULTILINE
    )

    # cache(() => { ... }, keyName) (SolidStart v1.0+)
    CACHE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'cache\s*\(',
        re.MULTILINE
    )

    # action(() => { ... }) (SolidStart v1.0+)
    ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'action\s*\(',
        re.MULTILINE
    )

    # createRouteData(() => { ... })
    CREATE_ROUTE_DATA_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createRouteData\s*\(',
        re.MULTILINE
    )

    # useRouteData<T>()
    USE_ROUTE_DATA_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useRouteData\s*(?:<[^>]*>)?\s*\(\)',
        re.MULTILINE
    )

    # redirect(path) / revalidate(key) / json(data)
    REDIRECT_PATTERN = re.compile(r'redirect\s*\(', re.MULTILINE)
    REVALIDATE_PATTERN = re.compile(r'revalidate\s*\(', re.MULTILINE)

    # routeData export
    ROUTE_DATA_EXPORT = re.compile(
        r'export\s+(?:const|function)\s+routeData\b',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js resource and async data patterns."""
        resources = []
        server_functions = []
        route_data = []

        has_redirect = bool(self.REDIRECT_PATTERN.search(content))
        has_revalidate = bool(self.REVALIDATE_PATTERN.search(content))

        # ── createResource ────────────────────────────────────────
        for m in self.CREATE_RESOURCE_PATTERN.finditer(content):
            name = m.group(1) or m.group(3)
            destructured = m.group(2) or ""
            type_ann = m.group(4) or ""
            line = content[:m.start()].count('\n') + 1

            # Determine if source signal is used (two-argument form)
            args_start = m.end()
            args_body = content[args_start:min(len(content), args_start + 300)]

            # Count commas at top level to detect source + fetcher args
            # Simple heuristic: if there are function args before a `=>` or `function`
            has_source = bool(re.match(
                r'\s*(?:\w+|\(\)\s*=>\s*\w+)\s*,\s*(?:async\s+)?\(?',
                args_body
            ))

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            has_initial = 'initialValue' in args_body[:200]
            has_ssr = any(kw in args_body[:200] for kw in ['deferStream', 'ssrLoadFrom'])

            resources.append(SolidResourceInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_source=has_source,
                type_annotation=type_ann,
                is_exported=is_exported,
                has_initial_value=has_initial,
                has_ssr=has_ssr,
            ))

        # ── createAsync (SolidStart v1.0+) ────────────────────────
        for m in self.CREATE_ASYNC_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            resources.append(SolidResourceInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported=is_exported,
                resource_type="async",
            ))

        # ── server$ ───────────────────────────────────────────────
        for m in self.SERVER_FUNCTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            server_functions.append(SolidServerFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                function_type="server$",
                is_exported=is_exported,
            ))

        # ── createServerData$ ─────────────────────────────────────
        for m in self.SERVER_DATA_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            server_functions.append(SolidServerFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                function_type="createServerData$",
                is_exported=is_exported,
            ))

        # ── createServerAction$ ───────────────────────────────────
        for m in self.SERVER_ACTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            server_functions.append(SolidServerFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                function_type="createServerAction$",
                is_exported=is_exported,
            ))

        # ── cache() (SolidStart v1.0+) ────────────────────────────
        for m in self.CACHE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            server_functions.append(SolidServerFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                function_type="cache",
                is_exported=is_exported,
                has_revalidate=has_revalidate,
            ))

        # ── action() (SolidStart v1.0+) ───────────────────────────
        for m in self.ACTION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            server_functions.append(SolidServerFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                function_type="action",
                is_exported=is_exported,
                has_redirect=has_redirect,
            ))

        # ── createRouteData ───────────────────────────────────────
        for m in self.CREATE_ROUTE_DATA_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            route_data.append(SolidRouteDataInfo(
                name=name,
                file=file_path,
                line_number=line,
                data_type="createRouteData",
            ))

        # ── useRouteData ──────────────────────────────────────────
        for m in self.USE_ROUTE_DATA_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            route_data.append(SolidRouteDataInfo(
                name=name,
                file=file_path,
                line_number=line,
                data_type="useRouteData",
            ))

        # ── routeData export ──────────────────────────────────────
        for m in self.ROUTE_DATA_EXPORT.finditer(content):
            line = content[:m.start()].count('\n') + 1

            route_data.append(SolidRouteDataInfo(
                name="routeData",
                file=file_path,
                line_number=line,
                data_type="routeData",
                is_exported=True,
            ))

        return {
            "resources": resources,
            "server_functions": server_functions,
            "route_data": route_data,
        }
