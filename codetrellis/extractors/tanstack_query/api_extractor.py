"""
TanStack Query API Extractor for CodeTrellis

Extracts TanStack Query API patterns, imports, integrations, and ecosystem usage:
- Import patterns (@tanstack/react-query, @tanstack/vue-query,
  @tanstack/svelte-query, @tanstack/solid-query, @tanstack/angular-query-experimental,
  react-query legacy)
- DevTools: @tanstack/react-query-devtools, ReactQueryDevtools
- TypeScript types: UseQueryResult, UseMutationResult, QueryKey, QueryFunction,
  QueryOptions, InfiniteData, QueryClient, etc.
- HTTP client integrations: axios, ky, fetch, got, superagent, ofetch
- tRPC integration (@trpc/client, @trpc/react-query)
- GraphQL integrations (graphql-request, @graphql-codegen, urql, Apollo)
- Testing: @testing-library/react, renderHook, MSW (@mswjs/data)
- Version detection: react-query v1-v3, @tanstack/react-query v4, v5

Supports:
- react-query v1-v2 (legacy single package, QueryCache API)
- react-query v3 (QueryClient, query keys as arrays, Hydrate)
- @tanstack/react-query v4 (scoped package, cacheTime, keepPreviousData,
  onSuccess/onError/onSettled on useQuery deprecated at v5)
- @tanstack/react-query v5 (gcTime, placeholderData, throwOnError,
  queryOptions, useSuspenseQuery, HydrationBoundary, initialPageParam required)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TanStackImportInfo:
    """Information about TanStack Query imports."""
    source: str  # @tanstack/react-query, react-query, etc.
    file: str = ""
    line_number: int = 0
    imported_names: List[str] = field(default_factory=list)
    is_default: bool = False
    is_type_import: bool = False
    subpath: str = ""  # e.g., /devtools, /persistQueryClient


@dataclass
class TanStackIntegrationInfo:
    """Information about TanStack Query integration with other libraries."""
    integration_type: str  # http-client, trpc, graphql, testing, devtools, persistence
    file: str = ""
    line_number: int = 0
    library: str = ""  # axios, ky, graphql-request, etc.
    pattern: str = ""  # Description of integration pattern


@dataclass
class TanStackTypeInfo:
    """Information about TanStack Query TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_category: str = ""  # query-result, mutation-result, key, options, client, data
    type_expression: str = ""


class TanStackApiExtractor:
    """
    Extracts TanStack Query API patterns, imports, integrations, and TypeScript types.

    Detects:
    - Import patterns across all framework adapters and versions
    - DevTools usage
    - HTTP client and data fetching integrations
    - tRPC integration patterns
    - GraphQL integration
    - Testing patterns
    - TypeScript utility type usage
    - Deprecated API patterns (for migration guidance)
    """

    # ─── Import Patterns ──────────────────────────────────────────

    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]"
        r"(@tanstack/[\w-]+(?:/[\w-]+)?|react-query(?:/[\w-]+)?)['\"]|"
        r"require\(['\"]"
        r"(@tanstack/[\w-]+(?:/[\w-]+)?|react-query(?:/[\w-]+)?)['\"]"
        r"\))",
        re.MULTILINE
    )

    # Type-only imports
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]"
        r"(@tanstack/[\w-]+|react-query)['\"]",
        re.MULTILINE
    )

    # ─── TypeScript Type Usage ────────────────────────────────────

    # Query result types
    QUERY_RESULT_TYPE_PATTERN = re.compile(
        r'(?:type|interface)\s+(\w+)\s*=?\s*'
        r'(UseQueryResult|UseSuspenseQueryResult|UseInfiniteQueryResult|'
        r'UseMutationResult|UseQueryOptions|UseMutationOptions|'
        r'QueryObserverResult|InfiniteData|QueryKey|QueryFunction|'
        r'QueryClient|QueryOptions|MutationOptions|'
        r'UseBaseQueryResult|DefinedUseQueryResult)\s*(?:<([^>]*)>)?',
        re.MULTILINE
    )

    # Standalone type references in annotations
    TS_TYPE_ANNOTATION_PATTERN = re.compile(
        r':\s*(UseQueryResult|UseSuspenseQueryResult|UseInfiniteQueryResult|'
        r'UseMutationResult|QueryKey|QueryFunction|InfiniteData|'
        r'QueryClient|Updater|MutationFunction)\s*(?:<([^>]*)>)?',
        re.MULTILINE
    )

    # ─── Integration Patterns ─────────────────────────────────────

    # HTTP clients
    HTTP_CLIENT_PATTERNS = {
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|require\(['\"]axios['\"]\)|"
            r"axios\s*\.\s*(?:get|post|put|patch|delete|request)\s*\(",
            re.MULTILINE
        ),
        'ky': re.compile(
            r"from\s+['\"]ky['\"]|ky\s*\.\s*(?:get|post|put|patch|delete)\s*\(",
            re.MULTILINE
        ),
        'fetch': re.compile(
            r'\bfetch\s*\(\s*[\'"`]|window\.fetch|globalThis\.fetch',
            re.MULTILINE
        ),
        'got': re.compile(
            r"from\s+['\"]got['\"]",
            re.MULTILINE
        ),
        'ofetch': re.compile(
            r"from\s+['\"]ofetch['\"]|\$fetch\s*\(",
            re.MULTILINE
        ),
        'superagent': re.compile(
            r"from\s+['\"]superagent['\"]",
            re.MULTILINE
        ),
    }

    # tRPC
    TRPC_PATTERNS = {
        'trpc-client': re.compile(
            r"from\s+['\"]@trpc/client['\"]|createTRPCProxyClient\s*\(",
            re.MULTILINE
        ),
        'trpc-react': re.compile(
            r"from\s+['\"]@trpc/react-query['\"]|"
            r"from\s+['\"]@trpc/react['\"]|"
            r"createTRPCReact\s*\(",
            re.MULTILINE
        ),
        'trpc-next': re.compile(
            r"from\s+['\"]@trpc/next['\"]|createTRPCNext\s*\(",
            re.MULTILINE
        ),
    }

    # GraphQL
    GRAPHQL_PATTERNS = {
        'graphql-request': re.compile(
            r"from\s+['\"]graphql-request['\"]|new\s+GraphQLClient\s*\(",
            re.MULTILINE
        ),
        'graphql-codegen': re.compile(
            r"from\s+['\"]@graphql-codegen/|from\s+['\"].*/generated/graphql['\"]",
            re.MULTILINE
        ),
        'urql': re.compile(
            r"from\s+['\"]urql['\"]|from\s+['\"]@urql/",
            re.MULTILINE
        ),
    }

    # DevTools
    DEVTOOLS_PATTERN = re.compile(
        r"from\s+['\"]@tanstack/react-query-devtools['\"]|"
        r"<ReactQueryDevtools\b|"
        r"from\s+['\"]react-query/devtools['\"]",
        re.MULTILINE
    )

    # Testing
    TESTING_PATTERNS = {
        'testing-library': re.compile(
            r"from\s+['\"]@testing-library/react['\"]|renderHook\s*\(",
            re.MULTILINE
        ),
        'msw': re.compile(
            r"from\s+['\"]msw['\"]|from\s+['\"]@mswjs/data['\"]|"
            r"setupServer\s*\(|setupWorker\s*\(",
            re.MULTILINE
        ),
        'vitest': re.compile(
            r"from\s+['\"]vitest['\"]|import.*vitest",
            re.MULTILINE
        ),
        'jest': re.compile(
            r"jest\.mock\s*\(|describe\s*\(|it\s*\(|test\s*\(",
            re.MULTILINE
        ),
    }

    # Persistence
    PERSISTENCE_PATTERNS = {
        'persist-client': re.compile(
            r"from\s+['\"]@tanstack/query-persist-client-core['\"]|"
            r"from\s+['\"]@tanstack/react-query-persist-client['\"]|"
            r"persistQueryClient\s*\(",
            re.MULTILINE
        ),
        'sync-storage': re.compile(
            r"from\s+['\"]@tanstack/query-sync-storage-persister['\"]|"
            r"createSyncStoragePersister\s*\(",
            re.MULTILINE
        ),
        'async-storage': re.compile(
            r"from\s+['\"]@tanstack/query-async-storage-persister['\"]|"
            r"createAsyncStoragePersister\s*\(",
            re.MULTILINE
        ),
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all TanStack Query API patterns from source code."""
        result: Dict[str, Any] = {
            'imports': [],
            'integrations': [],
            'types': [],
        }

        # ── Imports ────────────────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            named_imports = match.group(1) or ""
            default_import = match.group(2) or ""
            source = match.group(3) or match.group(4) or ""
            line_num = content[:match.start()].count('\n') + 1

            imported_names = []
            if named_imports:
                imported_names = [n.strip().split(' as ')[0].strip()
                                  for n in named_imports.split(',') if n.strip()]
            elif default_import:
                imported_names = [default_import]

            # Determine subpath
            subpath = ""
            if '/' in source:
                parts = source.split('/')
                if source.startswith('@tanstack/'):
                    subpath = '/'.join(parts[2:]) if len(parts) > 2 else ""
                else:
                    subpath = '/'.join(parts[1:]) if len(parts) > 1 else ""

            is_type = bool(re.search(
                r'import\s+type\s+', content[max(0, match.start() - 20):match.start() + 20]
            ))

            result['imports'].append(TanStackImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                imported_names=imported_names,
                is_default=bool(default_import),
                is_type_import=is_type,
                subpath=subpath,
            ))

        # ── TypeScript Types ───────────────────────────────────────
        for match in self.QUERY_RESULT_TYPE_PATTERN.finditer(content):
            type_name = match.group(1)
            base_type = match.group(2)
            generic = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            category = "query-result"
            if "Mutation" in base_type:
                category = "mutation-result"
            elif base_type in ("QueryKey", "QueryFunction"):
                category = "key"
            elif "Options" in base_type:
                category = "options"
            elif base_type == "QueryClient":
                category = "client"
            elif base_type == "InfiniteData":
                category = "data"

            result['types'].append(TanStackTypeInfo(
                name=type_name,
                file=file_path,
                line_number=line_num,
                type_category=category,
                type_expression=f"{base_type}<{generic}>" if generic else base_type,
            ))

        # ── Integrations ───────────────────────────────────────────
        # Only detect integrations if this file has TanStack Query imports
        # or tRPC imports (which use TanStack Query under the hood)
        has_tq = any('tanstack' in imp.source or 'react-query' in imp.source
                      for imp in result['imports'])
        has_trpc = any(pattern.search(content) for pattern in self.TRPC_PATTERNS.values())

        if has_tq or has_trpc:
            # HTTP clients
            for name, pattern in self.HTTP_CLIENT_PATTERNS.items():
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    result['integrations'].append(TanStackIntegrationInfo(
                        integration_type="http-client",
                        file=file_path,
                        line_number=line_num,
                        library=name,
                        pattern=f"{name} used as query/mutation fetch function",
                    ))

            # tRPC
            for name, pattern in self.TRPC_PATTERNS.items():
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    result['integrations'].append(TanStackIntegrationInfo(
                        integration_type="trpc",
                        file=file_path,
                        line_number=line_num,
                        library=name,
                        pattern="tRPC integration with TanStack Query",
                    ))

            # GraphQL
            for name, pattern in self.GRAPHQL_PATTERNS.items():
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    result['integrations'].append(TanStackIntegrationInfo(
                        integration_type="graphql",
                        file=file_path,
                        line_number=line_num,
                        library=name,
                        pattern="GraphQL integration with TanStack Query",
                    ))

        # DevTools (always detect)
        devtools_match = self.DEVTOOLS_PATTERN.search(content)
        if devtools_match:
            line_num = content[:devtools_match.start()].count('\n') + 1
            result['integrations'].append(TanStackIntegrationInfo(
                integration_type="devtools",
                file=file_path,
                line_number=line_num,
                library="@tanstack/react-query-devtools",
                pattern="React Query DevTools for debugging",
            ))

        # Testing
        if has_tq:
            for name, pattern in self.TESTING_PATTERNS.items():
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    result['integrations'].append(TanStackIntegrationInfo(
                        integration_type="testing",
                        file=file_path,
                        line_number=line_num,
                        library=name,
                        pattern=f"{name} used for testing TanStack Query code",
                    ))

        # Persistence
        for name, pattern in self.PERSISTENCE_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                result['integrations'].append(TanStackIntegrationInfo(
                    integration_type="persistence",
                    file=file_path,
                    line_number=line_num,
                    library=name,
                    pattern="Query client persistence for offline support",
                ))

        return result
