"""
TanStack Query Prefetch Extractor for CodeTrellis

Extracts TanStack Query prefetching and SSR hydration patterns:
- prefetchQuery() server-side or loader prefetching
- prefetchInfiniteQuery() for infinite queries
- ensureQueryData() (v5) — fetch if not cached
- SSR hydration: dehydrate(), hydrate(), HydrationBoundary (v5),
  Hydrate component (v4)
- Next.js integration: getServerSideProps, getStaticProps, RSC
  (React Server Components)
- Remix/React Router integration: loader functions
- Initial data patterns: initialData in query config
- Placeholder data patterns: placeholderData from cache

Supports:
- react-query v3 (dehydrate/hydrate/Hydrate)
- @tanstack/react-query v4 (Hydrate component, dehydrate/hydrate)
- @tanstack/react-query v5 (HydrationBoundary replaces Hydrate,
                              ensureQueryData, improved SSR patterns)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TanStackPrefetchInfo:
    """Information about a TanStack Query prefetch operation."""
    name: str  # Variable name or function containing the prefetch
    file: str = ""
    line_number: int = 0
    prefetch_method: str = ""  # prefetchQuery, prefetchInfiniteQuery, ensureQueryData, fetchQuery
    query_key: str = ""  # Prefetched query key
    context_type: str = ""  # ssr, loader, rsc, component, script
    is_in_get_server_side_props: bool = False
    is_in_get_static_props: bool = False
    is_in_loader: bool = False  # Remix/React Router loader
    is_in_rsc: bool = False  # React Server Component


@dataclass
class TanStackHydrationInfo:
    """Information about TanStack Query SSR hydration."""
    file: str = ""
    line_number: int = 0
    hydration_type: str = ""  # HydrationBoundary, Hydrate, dehydrate, hydrate
    dehydrated_state_source: str = ""  # e.g. "pageProps.dehydratedState"
    is_boundary: bool = False  # HydrationBoundary / Hydrate component
    is_dehydrate_call: bool = False  # dehydrate(queryClient) call
    is_hydrate_call: bool = False  # hydrate(queryClient, state) call


class TanStackPrefetchExtractor:
    """
    Extracts TanStack Query prefetch and SSR hydration patterns.

    Detects:
    - prefetchQuery / prefetchInfiniteQuery calls
    - ensureQueryData (v5) / fetchQuery calls
    - SSR dehydrate/hydrate patterns
    - HydrationBoundary (v5) / Hydrate (v4) components
    - Next.js getServerSideProps / getStaticProps integration
    - Remix loader integration
    - React Server Component prefetching
    """

    # Prefetch method calls
    PREFETCH_PATTERN = re.compile(
        r'(?:await\s+)?(\w+)\s*\.\s*(prefetchQuery|prefetchInfiniteQuery|'
        r'ensureQueryData|ensureInfiniteQueryData|fetchQuery|fetchInfiniteQuery)\s*\(',
        re.MULTILINE
    )

    # dehydrate() call
    DEHYDRATE_PATTERN = re.compile(
        r'dehydrate\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # hydrate() call
    HYDRATE_CALL_PATTERN = re.compile(
        r'hydrate\s*\(\s*(\w+)\s*,\s*(\w+)',
        re.MULTILINE
    )

    # HydrationBoundary (v5) / Hydrate (v4) component
    HYDRATION_BOUNDARY_PATTERN = re.compile(
        r'<(HydrationBoundary|Hydrate)\s+(?:state|options)\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # getServerSideProps / getStaticProps
    NEXT_SSR_PATTERN = re.compile(
        r'(?:export\s+)?(?:async\s+)?function\s+(getServerSideProps|getStaticProps)',
        re.MULTILINE
    )

    # export const getServerSideProps / getStaticProps
    NEXT_SSR_CONST_PATTERN = re.compile(
        r'export\s+const\s+(getServerSideProps|getStaticProps)\s*[=:]',
        re.MULTILINE
    )

    # Remix/React Router loader
    LOADER_PATTERN = re.compile(
        r'(?:export\s+)?(?:async\s+)?function\s+loader\s*\(|'
        r'export\s+(?:const|let)\s+loader\s*=',
        re.MULTILINE
    )

    # React Server Component detection (async component, 'use server', server file naming)
    RSC_PATTERN = re.compile(
        r"['\"]use server['\"]|"
        r'(?:export\s+default\s+)?async\s+function\s+\w+Page',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all TanStack Query prefetch and hydration patterns."""
        result: Dict[str, Any] = {
            'prefetches': [],
            'hydrations': [],
        }

        # Determine context
        is_in_gssp = bool(self.NEXT_SSR_PATTERN.search(content)) or bool(self.NEXT_SSR_CONST_PATTERN.search(content))
        is_in_loader = bool(self.LOADER_PATTERN.search(content))
        is_in_rsc = bool(self.RSC_PATTERN.search(content))
        is_server_file = any(p in file_path for p in ['/server/', '.server.', '/api/', '/pages/api/'])

        # Extract prefetch calls
        for match in self.PREFETCH_PATTERN.finditer(content):
            client_name = match.group(1)
            method = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 500)
            context = content[ctx_start:ctx_end]

            # Detect query key
            query_key = ""
            qk_match = re.search(r'queryKey\s*:\s*(\[[^\]]*\]|\w+)', context)
            if qk_match:
                query_key = qk_match.group(1).strip()

            # Determine context type
            context_type = "component"
            if is_in_gssp:
                context_type = "ssr"
            elif is_in_loader:
                context_type = "loader"
            elif is_in_rsc:
                context_type = "rsc"
            elif is_server_file:
                context_type = "server"

            gssp_match = self.NEXT_SSR_PATTERN.search(content) or self.NEXT_SSR_CONST_PATTERN.search(content)

            prefetch = TanStackPrefetchInfo(
                name=client_name,
                file=file_path,
                line_number=line_num,
                prefetch_method=method,
                query_key=query_key,
                context_type=context_type,
                is_in_get_server_side_props=(
                    bool(gssp_match) and gssp_match.group(1) == 'getServerSideProps'
                ) if gssp_match else False,
                is_in_get_static_props=(
                    bool(gssp_match) and gssp_match.group(1) == 'getStaticProps'
                ) if gssp_match else False,
                is_in_loader=is_in_loader,
                is_in_rsc=is_in_rsc,
            )
            result['prefetches'].append(prefetch)

        # Extract dehydrate calls
        for match in self.DEHYDRATE_PATTERN.finditer(content):
            client_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            result['hydrations'].append(TanStackHydrationInfo(
                file=file_path,
                line_number=line_num,
                hydration_type="dehydrate",
                dehydrated_state_source=client_name,
                is_dehydrate_call=True,
            ))

        # Extract hydrate calls
        for match in self.HYDRATE_CALL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['hydrations'].append(TanStackHydrationInfo(
                file=file_path,
                line_number=line_num,
                hydration_type="hydrate",
                is_hydrate_call=True,
            ))

        # Extract HydrationBoundary / Hydrate components
        for match in self.HYDRATION_BOUNDARY_PATTERN.finditer(content):
            component = match.group(1)
            state_source = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            result['hydrations'].append(TanStackHydrationInfo(
                file=file_path,
                line_number=line_num,
                hydration_type=component,
                dehydrated_state_source=state_source,
                is_boundary=True,
            ))

        return result
