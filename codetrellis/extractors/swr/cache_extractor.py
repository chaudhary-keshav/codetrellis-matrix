"""
SWR Cache Extractor for CodeTrellis

Extracts SWR cache management and global configuration patterns:
- SWRConfig provider usage and configuration
- Global fetcher configuration
- Cache provider (Map-based, localStorage, custom)
- Global mutate() function (bound and unbound)
- Cache operations: mutate(), useSWRConfig(), cache.get/set/delete
- Prefetching via preload() (v2+) and mutate with data
- Fallback data (SWRConfig fallback prop)
- Deduplication and auto-revalidation configuration

Supports:
- swr v0.x (SWRConfig as SWRConfigInterface, global mutate)
- swr v1.x (SWRConfig provider, cache provider, fallback)
- swr v2.x (preload, improved cache, serialization)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SWRConfigInfo:
    """Information about an SWRConfig provider."""
    name: str = "SWRConfig"
    file: str = ""
    line_number: int = 0
    has_global_fetcher: bool = False
    has_fallback: bool = False
    has_cache_provider: bool = False
    cache_provider_type: str = ""  # map, localStorage, custom
    has_suspense: bool = False
    has_revalidate_on_focus: bool = False
    has_revalidate_on_reconnect: bool = False
    has_deduping_interval: bool = False
    has_error_retry_count: bool = False
    has_on_success: bool = False
    has_on_error: bool = False
    has_on_error_retry: bool = False
    has_use: bool = False  # middleware
    is_exported: bool = False


@dataclass
class SWRMutateInfo:
    """Information about a global or bound mutate() call."""
    operation: str = "mutate"  # mutate, revalidate
    file: str = ""
    line_number: int = 0
    target_key: str = ""  # SWR key being targeted
    is_global: bool = False  # Global mutate() vs bound mutate
    has_data: bool = False  # mutate(key, data)
    has_revalidation: bool = False  # mutate(key, data, { revalidate: true })
    has_optimistic_data: bool = False  # optimisticData option (v2+)
    has_rollback_on_error: bool = False  # rollbackOnError option (v2+)
    has_populate_cache: bool = False  # populateCache option (v2+)


@dataclass
class SWRPreloadInfo:
    """Information about a preload() call (v2+)."""
    key: str = ""
    file: str = ""
    line_number: int = 0
    fetcher: str = ""


class SWRCacheExtractor:
    """
    Extracts SWR cache management patterns.

    Detects:
    - SWRConfig provider usage and configuration
    - Global fetcher configuration
    - Cache provider patterns (Map, localStorage, custom)
    - Global and bound mutate() calls
    - preload() for prefetching (v2+)
    - fallback data patterns
    - useSWRConfig() hook
    """

    # SWRConfig provider
    SWR_CONFIG_PATTERN = re.compile(
        r'<SWRConfig\s+(?:value\s*=\s*\{([^}]*)\}|[^>]*)',
        re.MULTILINE | re.DOTALL
    )

    # Global mutate import and usage
    GLOBAL_MUTATE_PATTERN = re.compile(
        r'(?:import\s+\{[^}]*\bmutate\b[^}]*\}\s+from\s+[\'"]swr[\'"]|'
        r'(?:const|let|var)\s+\{[^}]*\bmutate\b[^}]*\}\s*=\s*useSWRConfig\s*\(\s*\))',
        re.MULTILINE
    )

    # mutate() call patterns
    MUTATE_CALL_PATTERN = re.compile(
        r'(?:(?:global)?[Mm]utate|(?:const|let|var)\s+\{[^}]*\bmutate\b[^}]*\})\s*'
        r'|mutate\s*\(\s*([\'"`/][^,)]*|[\w.]+|\[[^\]]*\])',
        re.MULTILINE
    )

    # Bound mutate from useSWR destructuring
    BOUND_MUTATE_PATTERN = re.compile(
        r'(?:const|let|var)\s+\{[^}]*\bmutate\b[^}]*\}\s*=\s*useSWR',
        re.MULTILINE
    )

    # preload() (v2+)
    PRELOAD_PATTERN = re.compile(
        r'preload\s*\(\s*([\'"`][^\'"`]*[\'"`]|\[[^\]]*\]|\w+)\s*,\s*(\w+)',
        re.MULTILINE
    )

    # useSWRConfig hook
    USE_SWR_CONFIG_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\{[^}]*\}|\w+)\s*=\s*useSWRConfig\s*\(\s*\)',
        re.MULTILINE
    )

    # Cache provider pattern
    CACHE_PROVIDER_PATTERN = re.compile(
        r'(?:provider\s*:\s*|cache\s*:\s*new\s+)(\w+)',
        re.MULTILINE
    )

    # Fallback data
    FALLBACK_PATTERN = re.compile(
        r'fallback\s*:\s*\{',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all SWR cache patterns from source code."""
        result: Dict[str, Any] = {
            'configs': [],
            'mutate_calls': [],
            'preloads': [],
            'config_hooks': [],
        }

        # Extract SWRConfig providers
        for match in self.SWR_CONFIG_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 1000)
            context = content[ctx_start:ctx_end]

            config = SWRConfigInfo(
                file=file_path,
                line_number=line_num,
            )

            # Detect configuration options
            if re.search(r'\bfetcher\s*[:\s]', context):
                config.has_global_fetcher = True
            if self.FALLBACK_PATTERN.search(context):
                config.has_fallback = True
            if re.search(r'\bprovider\s*:', context) or re.search(r'\bcache\s*:', context):
                config.has_cache_provider = True
                if 'Map' in context:
                    config.cache_provider_type = "map"
                elif 'localStorage' in context:
                    config.cache_provider_type = "localStorage"
                else:
                    config.cache_provider_type = "custom"
            if re.search(r'\bsuspense\s*:\s*true', context):
                config.has_suspense = True
            if re.search(r'\brevalidateOnFocus\s*:', context):
                config.has_revalidate_on_focus = True
            if re.search(r'\brevalidateOnReconnect\s*:', context):
                config.has_revalidate_on_reconnect = True
            if re.search(r'\bdedupingInterval\s*:', context):
                config.has_deduping_interval = True
            if re.search(r'\berrorRetryCount\s*:', context):
                config.has_error_retry_count = True
            if re.search(r'\bonSuccess\s*:', context):
                config.has_on_success = True
            if re.search(r'\bonError\s*:', context):
                config.has_on_error = True
            if re.search(r'\bonErrorRetry\s*:', context):
                config.has_on_error_retry = True
            if re.search(r'\buse\s*:\s*\[', context):
                config.has_use = True

            result['configs'].append(config)

        # Extract global mutate calls
        for match in re.finditer(r'(?<!\w)mutate\s*\(\s*([\'"`][^\'"`]*[\'"`]|\[[^\]]*\]|\w+)', content):
            line_num = content[:match.start()].count('\n') + 1
            target_key = match.group(1).strip()

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 500)
            context = content[ctx_start:ctx_end]

            # Check if this is a bound or global mutate
            before = content[max(0, match.start() - 200):match.start()]
            is_global = bool(re.search(r'import\s+\{[^}]*\bmutate\b', content[:match.start()]))

            mutate_info = SWRMutateInfo(
                file=file_path,
                line_number=line_num,
                target_key=target_key,
                is_global=is_global,
            )

            # Detect options
            if re.search(r'mutate\s*\([^,]+,\s*(?!\{)\S', context):
                mutate_info.has_data = True
            if re.search(r'\brevalidate\s*:', context):
                mutate_info.has_revalidation = True
            if re.search(r'\boptimisticData\s*:', context):
                mutate_info.has_optimistic_data = True
            if re.search(r'\brollbackOnError\s*:', context):
                mutate_info.has_rollback_on_error = True
            if re.search(r'\bpopulateCache\s*:', context):
                mutate_info.has_populate_cache = True

            result['mutate_calls'].append(mutate_info)

        # Extract preload() calls (v2+)
        for match in self.PRELOAD_PATTERN.finditer(content):
            key = match.group(1).strip()
            fetcher = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            result['preloads'].append(SWRPreloadInfo(
                key=key,
                file=file_path,
                line_number=line_num,
                fetcher=fetcher,
            ))

        # Extract useSWRConfig hooks
        for match in self.USE_SWR_CONFIG_PATTERN.finditer(content):
            var_name = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            result['config_hooks'].append({
                'name': var_name,
                'file': file_path,
                'line_number': line_num,
            })

        return result
