"""
Remix Loader Extractor v1.0

Extracts data loading patterns from Remix / React Router v7 files:
- loader function (server-side data loading)
- clientLoader function (client-side data loading)
- useLoaderData hook usage
- json() / defer() / redirect() utilities
- Typed loader data (typeof loader, Route.LoaderArgs)
- Streaming with defer() + Await + Suspense
- Cache headers and revalidation
- Server timing

Supports:
- Remix v1.x (json, redirect, useLoaderData, LoaderFunction)
- Remix v2.x (defer, Await, streaming, typed loader data)
- React Router v7 (Route.LoaderArgs, Route.ComponentProps, loaderData prop)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RemixLoaderInfo:
    """Information about a loader function."""
    file_path: str = ""
    line_number: int = 0
    is_async: bool = False

    # Parameters
    has_request: bool = False
    has_params: bool = False
    has_context: bool = False

    # Return patterns
    returns_json: bool = False
    returns_defer: bool = False
    returns_redirect: bool = False
    returns_response: bool = False
    returns_throw: bool = False
    returns_plain: bool = False

    # Data fetching
    fetches_data: bool = False
    fetch_sources: List[str] = field(default_factory=list)  # db, api, fetch, prisma, etc.

    # Type safety
    has_typed_args: bool = False
    args_type: str = ""  # LoaderFunctionArgs, Route.LoaderArgs, etc.
    return_type: str = ""

    # Cache / Headers
    has_cache_control: bool = False
    cache_max_age: int = 0

    # Streaming
    has_defer: bool = False
    deferred_keys: List[str] = field(default_factory=list)


@dataclass
class RemixClientLoaderInfo:
    """Information about a clientLoader function."""
    file_path: str = ""
    line_number: int = 0
    is_async: bool = False
    calls_server_loader: bool = False
    has_hydrate: bool = False
    has_typed_args: bool = False
    args_type: str = ""


@dataclass
class RemixFetcherInfo:
    """Information about useFetcher usage."""
    file_path: str = ""
    line_number: int = 0
    fetcher_key: str = ""
    has_load: bool = False
    has_submit: bool = False
    has_form: bool = False


class RemixLoaderExtractor:
    """Extracts loader/data-loading patterns from Remix/RR7 files."""

    # Loader function patterns
    LOADER_PATTERN = re.compile(
        r'export\s+(async\s+)?function\s+loader\s*\(\s*'
        r'(?:\{\s*([^}]*)\}\s*(?::\s*(\w[\w.]*))?)?\s*\)',
        re.MULTILINE
    )

    LOADER_ARROW_PATTERN = re.compile(
        r'export\s+(?:const|let)\s+loader\s*(?::\s*(\w[\w.]*))?\s*=\s*(async\s+)?',
        re.MULTILINE
    )

    # Client loader patterns
    CLIENT_LOADER_PATTERN = re.compile(
        r'export\s+(async\s+)?function\s+clientLoader\s*\(\s*'
        r'(?:\{\s*([^}]*)\}\s*(?::\s*(\w[\w.]*))?)?\s*\)',
        re.MULTILINE
    )

    CLIENT_LOADER_HYDRATE = re.compile(
        r'clientLoader\.hydrate\s*=\s*true',
        re.MULTILINE
    )

    # useLoaderData patterns
    USE_LOADER_DATA = re.compile(
        r'useLoaderData\s*(?:<\s*typeof\s+loader\s*>)?\s*\(\s*\)',
        re.MULTILINE
    )

    # Data return patterns
    JSON_RETURN = re.compile(r'\bjson\s*\(', re.MULTILINE)
    DEFER_RETURN = re.compile(r'\bdefer\s*\(', re.MULTILINE)
    REDIRECT_RETURN = re.compile(r'\bredirect\s*\(', re.MULTILINE)
    RESPONSE_RETURN = re.compile(r'new\s+Response\s*\(', re.MULTILINE)
    THROW_RESPONSE = re.compile(r'throw\s+(?:new\s+Response|json|redirect)\s*\(', re.MULTILINE)

    # Defer/streaming patterns
    DEFER_KEY_PATTERN = re.compile(
        r'defer\s*\(\s*\{([^}]+)\}',
        re.MULTILINE | re.DOTALL
    )

    AWAIT_COMPONENT = re.compile(
        r'<Await\b',
        re.MULTILINE
    )

    # Data sources detection
    PRISMA_USAGE = re.compile(r'prisma\.\w+', re.MULTILINE)
    DRIZZLE_USAGE = re.compile(r'db\.\w+|drizzle\(', re.MULTILINE)
    FETCH_USAGE = re.compile(r'\bfetch\s*\(', re.MULTILINE)
    SUPABASE_USAGE = re.compile(r'supabase\.\w+', re.MULTILINE)

    # Cache headers
    CACHE_CONTROL = re.compile(
        r'["\']Cache-Control["\']\s*[,:]\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    MAX_AGE_PATTERN = re.compile(r'max-age=(\d+)')

    # useFetcher patterns
    USE_FETCHER = re.compile(
        r'useFetcher\s*(?:<\s*\w+\s*>)?\s*\(\s*(?:\{\s*key:\s*["\']([^"\']+)["\']\s*\})?\s*\)',
        re.MULTILINE
    )

    FETCHER_LOAD = re.compile(r'fetcher\.load\s*\(', re.MULTILINE)
    FETCHER_SUBMIT = re.compile(r'fetcher\.submit\s*\(', re.MULTILINE)
    FETCHER_FORM = re.compile(r'<fetcher\.Form\b', re.MULTILINE)

    # Typed loader args
    TYPED_LOADER_ARGS = re.compile(
        r'(?:LoaderFunctionArgs|LoaderArgs|Route\.LoaderArgs)',
        re.MULTILINE
    )

    # Server loader call from clientLoader
    SERVER_LOADER_CALL = re.compile(
        r'(?:await\s+)?serverLoader\s*\(\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract loader / data-loading information from source.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with loaders, client_loaders, fetchers
        """
        loaders: List[RemixLoaderInfo] = []
        client_loaders: List[RemixClientLoaderInfo] = []
        fetchers: List[RemixFetcherInfo] = []

        # Extract loader functions
        loader = self._extract_loader(content, file_path)
        if loader:
            loaders.append(loader)

        # Extract clientLoader
        client_loader = self._extract_client_loader(content, file_path)
        if client_loader:
            client_loaders.append(client_loader)

        # Extract fetcher usage
        fetchers.extend(self._extract_fetchers(content, file_path))

        return {
            'loaders': loaders,
            'client_loaders': client_loaders,
            'fetchers': fetchers,
            'has_use_loader_data': bool(self.USE_LOADER_DATA.search(content)),
            'has_await_component': bool(self.AWAIT_COMPONENT.search(content)),
        }

    def _extract_loader(self, content: str, file_path: str) -> Optional[RemixLoaderInfo]:
        """Extract loader function information."""
        match = self.LOADER_PATTERN.search(content)
        arrow_match = self.LOADER_ARROW_PATTERN.search(content)

        if not match and not arrow_match:
            return None

        loader = RemixLoaderInfo(file_path=file_path)

        if match:
            loader.line_number = content[:match.start()].count('\n') + 1
            loader.is_async = bool(match.group(1))
            params = match.group(2) or ""
            type_name = match.group(3) or ""

            loader.has_request = 'request' in params
            loader.has_params = 'params' in params
            loader.has_context = 'context' in params

            if type_name:
                loader.has_typed_args = True
                loader.args_type = type_name
        elif arrow_match:
            loader.line_number = content[:arrow_match.start()].count('\n') + 1
            loader.is_async = bool(arrow_match.group(2))
            if arrow_match.group(1):
                loader.has_typed_args = True
                loader.args_type = arrow_match.group(1)

        # Detect return patterns
        loader.returns_json = bool(self.JSON_RETURN.search(content))
        loader.returns_defer = bool(self.DEFER_RETURN.search(content))
        loader.returns_redirect = bool(self.REDIRECT_RETURN.search(content))
        loader.returns_response = bool(self.RESPONSE_RETURN.search(content))
        loader.returns_throw = bool(self.THROW_RESPONSE.search(content))
        loader.returns_plain = not any([
            loader.returns_json, loader.returns_defer,
            loader.returns_redirect, loader.returns_response,
        ])

        # Detect typed args
        if self.TYPED_LOADER_ARGS.search(content):
            loader.has_typed_args = True

        # Detect data sources
        loader.fetches_data = True
        if self.PRISMA_USAGE.search(content):
            loader.fetch_sources.append('prisma')
        if self.DRIZZLE_USAGE.search(content):
            loader.fetch_sources.append('drizzle')
        if self.FETCH_USAGE.search(content):
            loader.fetch_sources.append('fetch')
        if self.SUPABASE_USAGE.search(content):
            loader.fetch_sources.append('supabase')

        # Detect defer/streaming
        if loader.returns_defer:
            loader.has_defer = True
            defer_match = self.DEFER_KEY_PATTERN.search(content)
            if defer_match:
                keys_str = defer_match.group(1)
                key_pattern = re.compile(r'(\w+)\s*:', re.MULTILINE)
                loader.deferred_keys = key_pattern.findall(keys_str)

        # Detect cache headers
        cache_match = self.CACHE_CONTROL.search(content)
        if cache_match:
            loader.has_cache_control = True
            max_age_match = self.MAX_AGE_PATTERN.search(cache_match.group(1))
            if max_age_match:
                loader.cache_max_age = int(max_age_match.group(1))

        return loader

    def _extract_client_loader(self, content: str, file_path: str) -> Optional[RemixClientLoaderInfo]:
        """Extract clientLoader function."""
        match = self.CLIENT_LOADER_PATTERN.search(content)
        if not match:
            return None

        cl = RemixClientLoaderInfo(file_path=file_path)
        cl.line_number = content[:match.start()].count('\n') + 1
        cl.is_async = bool(match.group(1))
        params = match.group(2) or ""
        type_name = match.group(3) or ""

        cl.calls_server_loader = bool(self.SERVER_LOADER_CALL.search(content))
        cl.has_hydrate = bool(self.CLIENT_LOADER_HYDRATE.search(content))

        if type_name:
            cl.has_typed_args = True
            cl.args_type = type_name

        return cl

    def _extract_fetchers(self, content: str, file_path: str) -> List[RemixFetcherInfo]:
        """Extract useFetcher usage."""
        fetchers: List[RemixFetcherInfo] = []

        for match in self.USE_FETCHER.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            fetcher = RemixFetcherInfo(
                file_path=file_path,
                line_number=line_num,
                fetcher_key=match.group(1) or "",
                has_load=bool(self.FETCHER_LOAD.search(content)),
                has_submit=bool(self.FETCHER_SUBMIT.search(content)),
                has_form=bool(self.FETCHER_FORM.search(content)),
            )
            fetchers.append(fetcher)

        return fetchers
