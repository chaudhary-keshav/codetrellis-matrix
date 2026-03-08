"""
SWR Hook Extractor for CodeTrellis

Extracts SWR data fetching hook usage patterns:
- useSWR() hook calls with key and fetcher
- useSWRInfinite() for paginated/infinite data (v1+)
- useSWRSubscription() for real-time data (v2+)
- useSWRImmutable() for immutable data
- SWR configuration options: revalidateOnFocus, revalidateOnReconnect,
  refreshInterval, dedupingInterval, suspense, fallbackData,
  keepPreviousData (v2), errorRetryCount, errorRetryInterval
- Conditional fetching (null/false/function key)
- Dependent fetching (key depends on other SWR data)
- TypeScript generics

Supports:
- swr v0.x (basic useSWR with string/array keys)
- swr v1.x (useSWRInfinite stabilized, middleware, fallback, SWRConfig)
- swr v2.x (useSWRMutation, useSWRSubscription, preload, keepPreviousData,
             React 18 concurrent features, improved TypeScript)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SWRHookInfo:
    """Information about a useSWR() call."""
    name: str  # Variable name or inferred name
    file: str = ""
    line_number: int = 0
    key: str = ""  # SWR key expression (string, array, function, null)
    fetcher: str = ""  # Fetcher function name or expression
    hook_name: str = "useSWR"  # useSWR, useSWRImmutable
    has_revalidate_on_focus: bool = False
    has_revalidate_on_reconnect: bool = False
    has_revalidate_on_mount: bool = False
    has_revalidate_if_stale: bool = False
    has_refresh_interval: bool = False
    has_deduping_interval: bool = False
    has_suspense: bool = False
    has_fallback_data: bool = False
    has_initial_data: bool = False  # v0.x (renamed to fallbackData in v1)
    has_keep_previous_data: bool = False  # v2+
    has_error_retry_count: bool = False
    has_error_retry_interval: bool = False
    has_on_success: bool = False
    has_on_error: bool = False
    has_on_error_retry: bool = False
    has_on_loading_slow: bool = False
    has_on_discard: bool = False  # v2+
    has_conditional_fetch: bool = False  # null/false/() => null key
    has_dependent_fetch: bool = False  # key depends on other data
    has_compare: bool = False  # custom compare function
    has_is_online: bool = False
    has_is_visible: bool = False
    has_use: bool = False  # middleware via use option
    has_typescript: bool = False
    type_params: str = ""  # TypeScript generic parameters
    is_exported: bool = False


@dataclass
class SWRInfiniteInfo:
    """Information about a useSWRInfinite() call."""
    name: str
    file: str = ""
    line_number: int = 0
    get_key: str = ""  # getKey function
    fetcher: str = ""
    has_initial_size: bool = False
    has_revalidate_all: bool = False
    has_revalidate_first_page: bool = False  # v2+
    has_persist_size: bool = False
    has_parallel: bool = False  # v2+
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class SWRSubscriptionInfo:
    """Information about a useSWRSubscription() call (v2+)."""
    name: str
    file: str = ""
    line_number: int = 0
    key: str = ""
    subscribe_fn: str = ""
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


class SWRHookExtractor:
    """
    Extracts SWR hook definitions from source code.

    Detects:
    - useSWR() calls with configuration
    - useSWRImmutable() calls
    - useSWRInfinite() for pagination
    - useSWRSubscription() for real-time (v2+)
    - SWR configuration options
    - Conditional and dependent fetching patterns
    - TypeScript generic annotations
    """

    # useSWR / useSWRImmutable patterns
    USE_SWR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'(useSWR|useSWRImmutable)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useSWRInfinite pattern
    USE_SWR_INFINITE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'useSWRInfinite\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useSWRSubscription pattern (v2+)
    USE_SWR_SUBSCRIPTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'useSWRSubscription\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Standalone useSWR in return statement or inside JSX
    STANDALONE_SWR_PATTERN = re.compile(
        r'(useSWR|useSWRImmutable)\s*(?:<([^>]*)>)?\s*\(\s*(?:[\'"`\[]|null|false|\(\s*\)\s*=>|/)',
        re.MULTILINE
    )

    # SWR configuration keys
    SWR_CONFIG_KEYS = {
        'revalidateOnFocus': 'has_revalidate_on_focus',
        'revalidateOnReconnect': 'has_revalidate_on_reconnect',
        'revalidateOnMount': 'has_revalidate_on_mount',
        'revalidateIfStale': 'has_revalidate_if_stale',
        'refreshInterval': 'has_refresh_interval',
        'dedupingInterval': 'has_deduping_interval',
        'suspense': 'has_suspense',
        'fallbackData': 'has_fallback_data',
        'initialData': 'has_initial_data',
        'keepPreviousData': 'has_keep_previous_data',
        'errorRetryCount': 'has_error_retry_count',
        'errorRetryInterval': 'has_error_retry_interval',
        'onSuccess': 'has_on_success',
        'onError': 'has_on_error',
        'onErrorRetry': 'has_on_error_retry',
        'onLoadingSlow': 'has_on_loading_slow',
        'onDiscarded': 'has_on_discard',
        'compare': 'has_compare',
        'isOnline': 'has_is_online',
        'isVisible': 'has_is_visible',
        'use': 'has_use',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all SWR hook patterns from source code."""
        result: Dict[str, Any] = {
            'hooks': [],
            'infinite_hooks': [],
            'subscription_hooks': [],
        }

        lines = content.split('\n')

        # Extract useSWR / useSWRImmutable
        for match in self.USE_SWR_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            hook_name = match.group(2)
            type_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            # Get surrounding context for config detection
            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 800)
            context = content[ctx_start:ctx_end]

            hook = SWRHookInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                hook_name=hook_name,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Extract key
            key_match = re.search(
                r'(?:useSWR|useSWRImmutable)\s*(?:<[^>]*>)?\s*\(\s*'
                r'([\'"`][^\'"`]*[\'"`]|\[[^\]]*\]|null|false|\w+|'
                r'\(\s*\)\s*=>|`[^`]*`)',
                context
            )
            if key_match:
                hook.key = key_match.group(1).strip()

            # Detect conditional fetching (null/false key)
            if hook.key in ('null', 'false') or '? null' in context or '? undefined' in context:
                hook.has_conditional_fetch = True
            elif re.search(r'\(\s*\)\s*=>\s*(?:\w+\s*\?)', context):
                hook.has_conditional_fetch = True

            # Detect dependent fetching
            if re.search(r'\(\s*\)\s*=>\s*\w+\s*&&', context):
                hook.has_dependent_fetch = True
            elif re.search(r'\(\s*\)\s*=>\s*\w+\s*\?', context):
                hook.has_dependent_fetch = True

            # Extract fetcher
            fetcher_match = re.search(
                r'(?:useSWR|useSWRImmutable)\s*(?:<[^>]*>)?\s*\([^,]+,\s*(\w+)',
                context
            )
            if fetcher_match:
                hook.fetcher = fetcher_match.group(1).strip()

            # Detect configuration options
            for config_key, attr_name in self.SWR_CONFIG_KEYS.items():
                if re.search(r'\b' + config_key + r'\s*[:\s]', context):
                    setattr(hook, attr_name, True)

            result['hooks'].append(hook)

        # Extract useSWRInfinite
        for match in self.USE_SWR_INFINITE_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 800)
            context = content[ctx_start:ctx_end]

            infinite = SWRInfiniteInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Detect infinite-specific options
            if re.search(r'\binitialSize\s*:', context):
                infinite.has_initial_size = True
            if re.search(r'\brevalidateAll\s*:', context):
                infinite.has_revalidate_all = True
            if re.search(r'\brevalidateFirstPage\s*:', context):
                infinite.has_revalidate_first_page = True
            if re.search(r'\bpersistSize\s*:', context):
                infinite.has_persist_size = True
            if re.search(r'\bparallel\s*:', context):
                infinite.has_parallel = True

            # Extract getKey function
            gk_match = re.search(
                r'useSWRInfinite\s*(?:<[^>]*>)?\s*\(\s*(\w+|(?:\([^)]*\)|\w+)\s*=>)',
                context
            )
            if gk_match:
                infinite.get_key = gk_match.group(1).strip()

            result['infinite_hooks'].append(infinite)

        # Extract useSWRSubscription (v2+)
        for match in self.USE_SWR_SUBSCRIPTION_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 500)
            context = content[ctx_start:ctx_end]

            sub = SWRSubscriptionInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Extract key
            key_match = re.search(
                r'useSWRSubscription\s*(?:<[^>]*>)?\s*\(\s*'
                r'([\'"`][^\'"`]*[\'"`]|\[[^\]]*\]|\w+)',
                context
            )
            if key_match:
                sub.key = key_match.group(1).strip()

            result['subscription_hooks'].append(sub)

        return result
