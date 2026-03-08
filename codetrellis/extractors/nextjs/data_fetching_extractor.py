"""
Next.js Data Fetching Extractor for CodeTrellis

Extracts data fetching patterns from Next.js applications:
- fetch() with Next.js cache options (cache, next.revalidate, next.tags)
- React cache() wrapper
- unstable_cache() / cacheLife() / cacheTag()
- generateStaticParams for static generation
- Dynamic rendering signals (cookies(), headers(), searchParams)
- Parallel data fetching (Promise.all, Promise.allSettled)
- Streaming with Suspense boundaries
- ISR configuration (revalidate)
- On-demand revalidation (revalidatePath, revalidateTag)
- Data fetching in Server Components vs Client Components

Supports:
- Next.js 9.x (getServerSideProps, getStaticProps)
- Next.js 13.x (fetch extensions, Server Components)
- Next.js 14.x (caching improvements, Partial Prerendering)
- Next.js 15.x (async request APIs, cacheLife, cacheTag)

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NextFetchCallInfo:
    """Information about a fetch() call with Next.js options."""
    file: str = ""
    line_number: int = 0
    url: str = ""
    method: str = "GET"
    cache_option: str = ""  # force-cache, no-store, no-cache
    revalidate: int = 0  # next.revalidate seconds
    tags: List[str] = field(default_factory=list)  # next.tags
    is_in_server_component: bool = False
    is_in_route_handler: bool = False
    is_in_server_action: bool = False
    error_handling: str = ""  # try-catch, .catch, none


@dataclass
class NextCacheInfo:
    """Information about Next.js caching usage."""
    file: str = ""
    line_number: int = 0
    cache_type: str = ""  # react_cache, unstable_cache, cache_life, cache_tag
    name: str = ""
    tags: List[str] = field(default_factory=list)
    revalidate: int = 0
    key_parts: List[str] = field(default_factory=list)


@dataclass
class NextStaticParamsInfo:
    """Information about generateStaticParams."""
    file: str = ""
    line_number: int = 0
    route_path: str = ""
    param_names: List[str] = field(default_factory=list)
    is_async: bool = True
    data_source: str = ""  # database, api, filesystem, static


class NextDataFetchingExtractor:
    """
    Extracts data fetching patterns from Next.js source code.

    Detects:
    - fetch() with Next.js cache/revalidate options
    - React cache() and unstable_cache()
    - generateStaticParams
    - Dynamic rendering signals
    - Parallel data fetching
    - Streaming patterns
    """

    # fetch() with next options
    FETCH_CALL = re.compile(
        r"(?:await\s+)?fetch\s*\(\s*(?:['\"`]([^'\"`]+)['\"`]|(\w+))\s*"
        r"(?:,\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\})?\s*\)",
        re.MULTILINE | re.DOTALL
    )

    # Next.js fetch cache option
    FETCH_CACHE = re.compile(
        r"cache\s*:\s*['\"](\w[\w-]*)['\"]",
        re.MULTILINE
    )

    # Next.js revalidate option
    FETCH_REVALIDATE = re.compile(
        r"(?:next\s*:\s*\{[^}]*)?revalidate\s*:\s*(\d+)",
        re.MULTILINE
    )

    # Next.js tags
    FETCH_TAGS = re.compile(
        r"tags\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )

    # React cache()
    REACT_CACHE = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*cache\s*\(",
        re.MULTILINE
    )

    # unstable_cache
    UNSTABLE_CACHE = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*unstable_cache\s*\(",
        re.MULTILINE
    )

    # cacheLife (Next.js 15+)
    CACHE_LIFE = re.compile(
        r"cacheLife\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # cacheTag (Next.js 15+)
    CACHE_TAG = re.compile(
        r"cacheTag\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # generateStaticParams
    GENERATE_STATIC_PARAMS = re.compile(
        r'^[ \t]*export\s+(async\s+)?function\s+generateStaticParams\s*\(',
        re.MULTILINE
    )

    # Dynamic rendering signals
    DYNAMIC_SIGNALS = re.compile(
        r'(?:await\s+)?(?:cookies|headers)\s*\(\)|'
        r'searchParams\b|useSearchParams|'
        r'connection\s*\(\)',
        re.MULTILINE
    )

    # Parallel data fetching
    PARALLEL_FETCH = re.compile(
        r'Promise\.(?:all|allSettled|race)\s*\(\s*\[',
        re.MULTILINE
    )

    # Suspense streaming
    SUSPENSE_BOUNDARY = re.compile(
        r'<Suspense\b',
        re.MULTILINE
    )

    # Directives
    USE_CLIENT = re.compile(r'''^['"]use client['"]''', re.MULTILINE)
    USE_SERVER = re.compile(r'''^['"]use server['"]''', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract data fetching patterns from Next.js source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'fetch_calls', 'caches', 'static_params',
                      'has_dynamic_signals', 'has_parallel_fetch',
                      'suspense_count'
        """
        fetch_calls = []
        caches = []
        static_params = []

        normalized = file_path.replace('\\', '/')
        is_client = bool(self.USE_CLIENT.search(content))
        is_server_action = bool(self.USE_SERVER.search(content))
        is_route_handler = normalized.endswith(('route.ts', 'route.tsx', 'route.js', 'route.jsx'))
        is_server_component = not is_client and '/app/' in normalized

        # ── fetch() calls ────────────────────────────────────────
        for m in self.FETCH_CALL.finditer(content):
            url = m.group(1) or m.group(2) or ""
            options = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            cache_option = ""
            cm = self.FETCH_CACHE.search(options)
            if cm:
                cache_option = cm.group(1)

            revalidate = 0
            rm = self.FETCH_REVALIDATE.search(options)
            if rm:
                try:
                    revalidate = int(rm.group(1))
                except ValueError:
                    pass

            tags = []
            tm = self.FETCH_TAGS.search(options)
            if tm:
                tags = re.findall(r"['\"]([^'\"]+)['\"]", tm.group(1))

            method = "GET"
            mm = re.search(r"method\s*:\s*['\"](\w+)['\"]", options)
            if mm:
                method = mm.group(1).upper()

            # Error handling detection
            # Look at surrounding context
            before = content[max(0, m.start() - 200):m.start()]
            after = content[m.end():min(m.end() + 200, len(content))]
            error_handling = "none"
            if 'try' in before and 'catch' in after:
                error_handling = "try-catch"
            elif '.catch(' in after:
                error_handling = ".catch"

            fetch_info = NextFetchCallInfo(
                file=file_path,
                line_number=line,
                url=url,
                method=method,
                cache_option=cache_option,
                revalidate=revalidate,
                tags=tags,
                is_in_server_component=is_server_component,
                is_in_route_handler=is_route_handler,
                is_in_server_action=is_server_action,
                error_handling=error_handling,
            )
            fetch_calls.append(fetch_info)

        # ── React cache() ────────────────────────────────────────
        for m in self.REACT_CACHE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            caches.append(NextCacheInfo(
                file=file_path,
                line_number=line,
                cache_type="react_cache",
                name=m.group(1),
            ))

        # ── unstable_cache ───────────────────────────────────────
        for m in self.UNSTABLE_CACHE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            # Try to extract tags/revalidate from options
            after = content[m.end():min(m.end() + 500, len(content))]
            tags = []
            tm = self.FETCH_TAGS.search(after)
            if tm:
                tags = re.findall(r"['\"]([^'\"]+)['\"]", tm.group(1))

            revalidate = 0
            rm = self.FETCH_REVALIDATE.search(after)
            if rm:
                try:
                    revalidate = int(rm.group(1))
                except ValueError:
                    pass

            caches.append(NextCacheInfo(
                file=file_path,
                line_number=line,
                cache_type="unstable_cache",
                name=m.group(1),
                tags=tags,
                revalidate=revalidate,
            ))

        # ── cacheLife (Next.js 15+) ──────────────────────────────
        for m in self.CACHE_LIFE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            caches.append(NextCacheInfo(
                file=file_path,
                line_number=line,
                cache_type="cache_life",
                name=m.group(1),
            ))

        # ── cacheTag (Next.js 15+) ──────────────────────────────
        for m in self.CACHE_TAG.finditer(content):
            line = content[:m.start()].count('\n') + 1
            caches.append(NextCacheInfo(
                file=file_path,
                line_number=line,
                cache_type="cache_tag",
                name=m.group(1),
            ))

        # ── generateStaticParams ─────────────────────────────────
        for m in self.GENERATE_STATIC_PARAMS.finditer(content):
            line = content[:m.start()].count('\n') + 1
            # Infer param names from file path dynamic segments
            param_names = re.findall(r'\[(\w+)\]', normalized)
            is_async = bool(m.group(1))

            # Try to detect data source
            body_start = m.end()
            body_end = min(body_start + 1000, len(content))
            body = content[body_start:body_end]
            data_source = "static"
            if re.search(r'prisma|supabase|db\.|mongoose', body, re.IGNORECASE):
                data_source = "database"
            elif re.search(r'fetch\(|axios|got\(', body):
                data_source = "api"
            elif re.search(r'readdir|readFile|glob|fs\.', body):
                data_source = "filesystem"

            static_params.append(NextStaticParamsInfo(
                file=file_path,
                line_number=line,
                route_path=self._infer_route_path(normalized),
                param_names=param_names,
                is_async=is_async,
                data_source=data_source,
            ))

        # ── Aggregate signals ────────────────────────────────────
        has_dynamic_signals = bool(self.DYNAMIC_SIGNALS.search(content))
        has_parallel_fetch = bool(self.PARALLEL_FETCH.search(content))
        suspense_count = len(self.SUSPENSE_BOUNDARY.findall(content))

        return {
            "fetch_calls": fetch_calls,
            "caches": caches,
            "static_params": static_params,
            "has_dynamic_signals": has_dynamic_signals,
            "has_parallel_fetch": has_parallel_fetch,
            "suspense_count": suspense_count,
        }

    def _infer_route_path(self, file_path: str) -> str:
        """Infer route path from file system path."""
        path = file_path
        if '/app/' in path:
            path = path.split('/app/', 1)[1]
        elif '/pages/' in path:
            path = path.split('/pages/', 1)[1]
        else:
            return "/"

        path = re.sub(r'/?(page|layout|route)\.\w+$', '', path)
        path = re.sub(r'\([^)]+\)/?', '', path)
        path = re.sub(r'@\w+/?', '', path)
        path = re.sub(r'/+', '/', path)
        if not path.startswith('/'):
            path = '/' + path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        return path if path else "/"
