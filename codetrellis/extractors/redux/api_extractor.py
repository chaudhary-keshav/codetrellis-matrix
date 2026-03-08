"""
Redux RTK Query API Extractor for CodeTrellis

Extracts RTK Query API patterns:
- createApi with fetchBaseQuery / graphqlRequestBaseQuery / fetchBaseQuery wrapper
- Query and mutation endpoint definitions with tags
- Cache tag management (providesTags, invalidatesTags)
- Cache lifecycle callbacks (onCacheEntryAdded, onQueryStarted)
- Optimistic updates (via onQueryStarted + dispatch(api.util.updateQueryData))
- Streaming/WebSocket updates (via onCacheEntryAdded + cacheDataLoaded)
- transformResponse / transformErrorResponse
- Code splitting (injectEndpoints, enhanceEndpoints)
- Generated hook names (useXQuery, useXMutation)
- Polling (pollingInterval)
- Prefetching (usePrefetch)
- Tag types / tag IDs
- API base URL / headers

Supports:
- RTK Query 1.0+ (createApi, fetchBaseQuery)
- RTK Query with GraphQL (graphqlRequestBaseQuery)
- RTK Query code splitting (injectEndpoints)
- RTK Query streaming (onCacheEntryAdded)
- RTK Query 2.0 (enhanced type safety, selectFromResult)

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReduxRTKQueryApiInfo:
    """Information about a createApi definition."""
    name: str
    file: str = ""
    line_number: int = 0
    reducer_path: str = ""
    base_url: str = ""
    base_query_type: str = ""  # fetchBaseQuery, graphqlRequestBaseQuery, custom
    tag_types: List[str] = field(default_factory=list)
    endpoint_count: int = 0
    query_count: int = 0
    mutation_count: int = 0
    has_auth_header: bool = False
    has_error_handling: bool = False
    has_code_splitting: bool = False  # injectEndpoints used
    generated_hooks: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class ReduxRTKQueryEndpointInfo:
    """Information about an RTK Query endpoint."""
    name: str
    file: str = ""
    line_number: int = 0
    api_name: str = ""  # Parent API name
    endpoint_type: str = ""  # query, mutation
    url_pattern: str = ""  # URL or query string
    method: str = ""  # GET, POST, PUT, DELETE, PATCH
    provides_tags: List[str] = field(default_factory=list)
    invalidates_tags: List[str] = field(default_factory=list)
    has_transform_response: bool = False
    has_transform_error: bool = False
    has_on_query_started: bool = False
    has_on_cache_entry_added: bool = False
    has_polling: bool = False
    has_select_from_result: bool = False
    is_exported: bool = False


@dataclass
class ReduxCacheTagInfo:
    """Information about cache tag usage."""
    tag_type: str
    file: str = ""
    line_number: int = 0
    usage: str = ""  # provides, invalidates
    endpoint: str = ""
    is_list_tag: bool = False  # Uses 'LIST' id pattern


class ReduxApiExtractor:
    """
    Extracts RTK Query API patterns from source code.

    Detects:
    - createApi definitions with full configuration
    - Query and mutation endpoints
    - Cache tag management
    - Cache lifecycle callbacks
    - Code splitting patterns
    - Generated hook exports
    """

    # createApi
    CREATE_API_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createApi\s*\(\s*\{',
        re.MULTILINE
    )

    # injectEndpoints
    INJECT_ENDPOINTS_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(\w+)\.injectEndpoints\s*\(\s*\{',
        re.MULTILINE
    )

    # enhanceEndpoints
    ENHANCE_ENDPOINTS_PATTERN = re.compile(
        r'(\w+)\.enhanceEndpoints\s*\(\s*\{',
        re.MULTILINE
    )

    # Generated hook export: export const { useGetXQuery, useUpdateXMutation } = apiName
    HOOK_EXPORT_PATTERN = re.compile(
        r'export\s+const\s+\{([^}]+)\}\s*=\s*(\w+)',
        re.MULTILINE
    )

    # fetchBaseQuery
    FETCH_BASE_QUERY_PATTERN = re.compile(
        r'fetchBaseQuery\s*\(\s*\{',
        re.MULTILINE
    )

    # graphqlRequestBaseQuery
    GRAPHQL_BASE_QUERY_PATTERN = re.compile(
        r'graphqlRequestBaseQuery\s*\(\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract RTK Query API patterns from source code."""
        apis = []
        endpoints = []
        cache_tags = []

        # ── createApi ─────────────────────────────────────────────
        for m in self.CREATE_API_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:], max_len=15000)

            # Extract reducerPath
            rp_match = re.search(r'reducerPath\s*:\s*[\'"]([^\'"]+)[\'"]', body)
            reducer_path = rp_match.group(1) if rp_match else ""

            # Detect base query type
            base_query_type = "custom"
            if 'fetchBaseQuery' in body:
                base_query_type = "fetchBaseQuery"
            elif 'graphqlRequestBaseQuery' in body:
                base_query_type = "graphqlRequestBaseQuery"

            # Extract base URL
            base_url = ""
            url_match = re.search(r'baseUrl\s*:\s*[\'"`]([^\'"` ]+)[\'"`]', body)
            if url_match:
                base_url = url_match.group(1)
            else:
                # Environment variable pattern
                env_match = re.search(r'baseUrl\s*:\s*(?:process\.env\.(\w+)|import\.meta\.env\.(\w+))', body)
                if env_match:
                    base_url = f"${{{env_match.group(1) or env_match.group(2)}}}"

            # Extract tagTypes
            tag_match = re.search(r'tagTypes\s*:\s*\[([^\]]+)\]', body)
            tag_types = []
            if tag_match:
                tag_types = [t.strip().strip("'\"") for t in tag_match.group(1).split(',') if t.strip()]

            # Detect auth header
            has_auth = bool(re.search(r'[Aa]uthori[zs]ation|[Bb]earer|token|prepareHeaders', body))

            # Detect error handling
            has_error = bool(re.search(r'fetchBaseQuery.*responseHandler|baseQueryWithReauth|queryFn', body))

            # Extract endpoints
            ep_result = self._extract_endpoints(body, name, file_path)
            query_count = sum(1 for ep in ep_result if ep.endpoint_type == 'query')
            mutation_count = sum(1 for ep in ep_result if ep.endpoint_type == 'mutation')
            endpoints.extend(ep_result)

            # Extract cache tags from endpoints
            for ep in ep_result:
                for tag in ep.provides_tags:
                    cache_tags.append(ReduxCacheTagInfo(
                        tag_type=tag,
                        file=file_path,
                        line_number=ep.line_number,
                        usage="provides",
                        endpoint=ep.name,
                        is_list_tag='LIST' in str(tag),
                    ))
                for tag in ep.invalidates_tags:
                    cache_tags.append(ReduxCacheTagInfo(
                        tag_type=tag,
                        file=file_path,
                        line_number=ep.line_number,
                        usage="invalidates",
                        endpoint=ep.name,
                    ))

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            # Extract generated hooks
            generated_hooks = self._extract_generated_hooks(content, name)

            apis.append(ReduxRTKQueryApiInfo(
                name=name,
                file=file_path,
                line_number=line,
                reducer_path=reducer_path,
                base_url=base_url,
                base_query_type=base_query_type,
                tag_types=tag_types[:20],
                endpoint_count=len(ep_result),
                query_count=query_count,
                mutation_count=mutation_count,
                has_auth_header=has_auth,
                has_error_handling=has_error,
                generated_hooks=generated_hooks[:30],
                is_exported=is_exported,
            ))

        # ── injectEndpoints ───────────────────────────────────────
        for m in self.INJECT_ENDPOINTS_PATTERN.finditer(content):
            name = m.group(1)
            base_api = m.group(2)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:], max_len=10000)

            ep_result = self._extract_endpoints(body, base_api, file_path)
            endpoints.extend(ep_result)

            # Mark code splitting on the parent API
            for api in apis:
                if api.name == base_api:
                    api.has_code_splitting = True

            # Extract hooks from injected
            hooks = self._extract_generated_hooks(content, name)
            for api in apis:
                if api.name == base_api:
                    api.generated_hooks.extend(hooks)

        return {
            'apis': apis,
            'endpoints': endpoints,
            'cache_tags': cache_tags,
        }

    def _extract_endpoints(self, body: str, api_name: str, file_path: str) -> List[ReduxRTKQueryEndpointInfo]:
        """Extract query and mutation endpoint definitions."""
        endpoints_list = []

        # Find endpoints builder section
        ep_match = re.search(r'endpoints\s*:\s*\(\s*(\w+)\s*\)\s*=>\s*\(\s*\{', body)
        if not ep_match:
            ep_match = re.search(r'endpoints\s*:\s*\(\s*(\w+)\s*\)\s*=>\s*\{', body)
        if not ep_match:
            return endpoints_list

        builder_name = ep_match.group(1)
        ep_body_start = ep_match.end() - 1
        ep_body = self._extract_balanced_braces(body[ep_body_start:], max_len=10000)

        # Match both query and mutation endpoints
        ep_pattern = re.compile(
            rf'(\w+)\s*:\s*{re.escape(builder_name)}\.(query|mutation)\s*(?:<[^>]*>)?\s*\(\s*\{{',
            re.MULTILINE
        )

        for em in ep_pattern.finditer(ep_body):
            ep_name = em.group(1)
            ep_type = em.group(2)
            ep_line = body[:body.find(ep_body) + em.start()].count('\n') + 1

            ep_def_start = em.end() - 1
            ep_def = self._extract_balanced_braces(ep_body[ep_def_start:])

            # Extract URL
            url_pattern = ""
            url_match = re.search(r'url\s*:\s*[\'"`]([^\'"` ]+)[\'"`]', ep_def)
            if url_match:
                url_pattern = url_match.group(1)
            else:
                url_template = re.search(r'url\s*:\s*`([^`]+)`', ep_def)
                if url_template:
                    url_pattern = url_template.group(1)

            # Extract method
            method = "GET" if ep_type == "query" else "POST"
            method_match = re.search(r'method\s*:\s*[\'"](\w+)[\'"]', ep_def)
            if method_match:
                method = method_match.group(1).upper()

            # Extract providesTags
            provides = self._extract_tags(ep_def, 'providesTags')

            # Extract invalidatesTags
            invalidates = self._extract_tags(ep_def, 'invalidatesTags')

            # Detect features
            has_transform = bool(re.search(r'transformResponse\s*:', ep_def))
            has_transform_err = bool(re.search(r'transformErrorResponse\s*:', ep_def))
            has_on_query = bool(re.search(r'onQueryStarted\s*:', ep_def))
            has_on_cache = bool(re.search(r'onCacheEntryAdded\s*:', ep_def))
            has_polling = bool(re.search(r'pollingInterval\s*:', ep_def))
            has_select_from = bool(re.search(r'selectFromResult\s*:', ep_def))

            endpoints_list.append(ReduxRTKQueryEndpointInfo(
                name=ep_name,
                file=file_path,
                line_number=ep_line,
                api_name=api_name,
                endpoint_type=ep_type,
                url_pattern=url_pattern[:200],
                method=method,
                provides_tags=provides[:10],
                invalidates_tags=invalidates[:10],
                has_transform_response=has_transform,
                has_transform_error=has_transform_err,
                has_on_query_started=has_on_query,
                has_on_cache_entry_added=has_on_cache,
                has_polling=has_polling,
                has_select_from_result=has_select_from,
            ))

        return endpoints_list

    def _extract_tags(self, body: str, tag_field: str) -> List[str]:
        """Extract tag type names from providesTags/invalidatesTags."""
        tag_match = re.search(rf'{tag_field}\s*:\s*\[([^\]]+)\]', body)
        if tag_match:
            tags_str = tag_match.group(1)
            return [t.strip().strip("'\"") for t in re.findall(r"['\"](\w+)['\"]", tags_str)]

        # Function form
        fn_match = re.search(rf'{tag_field}\s*:\s*(?:\(.*?\)\s*=>|\w+\s*\()', body)
        if fn_match:
            after = body[fn_match.end():fn_match.end() + 500]
            return re.findall(r"['\"](\w+)['\"]", after[:200])

        return []

    def _extract_generated_hooks(self, content: str, api_name: str) -> List[str]:
        """Extract auto-generated hook exports from an API."""
        hooks = []
        for m in self.HOOK_EXPORT_PATTERN.finditer(content):
            exports_str = m.group(1)
            source = m.group(2)
            if source == api_name:
                for name in exports_str.split(','):
                    name = name.strip()
                    if name.startswith('use') and ('Query' in name or 'Mutation' in name or 'Lazy' in name or 'Prefetch' in name):
                        hooks.append(name)
        return hooks

    def _extract_balanced_braces(self, text: str, max_len: int = 10000) -> str:
        """Extract content within balanced braces."""
        depth = 0
        start = None
        for i, ch in enumerate(text[:max_len]):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i + 1]
        return text[:max_len] if start is None else text[start:max_len]
