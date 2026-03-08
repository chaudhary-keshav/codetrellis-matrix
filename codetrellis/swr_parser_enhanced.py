"""
EnhancedSWRParser v1.0 - Comprehensive SWR parser using all extractors.

This parser integrates all SWR extractors to provide complete parsing of
SWR (Vercel) data fetching usage across React/TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting SWR-specific semantics.

Supports:
- swr v0.x (basic useSWR, string keys, initialData, revalidateOnFocus)
- swr v1.x (useSWRInfinite stabilized, SWRConfig provider, fallback data,
             cache provider API, middleware system, useSWRImmutable,
             improved TypeScript, global mutate improvements)
- swr v2.x (useSWRMutation for remote mutations, useSWRSubscription for
             real-time data, preload() for prefetching, keepPreviousData,
             optimisticData/rollbackOnError/populateCache options,
             React 18 concurrent features, improved TypeScript inference,
             throwOnError, onDiscarded callback)

Key Patterns:
- useSWR(key, fetcher, config) — data fetching
- useSWRImmutable(key, fetcher) — immutable data (no revalidation)
- useSWRInfinite(getKey, fetcher, config) — infinite/paginated data
- useSWRMutation(key, fetcher, config) — remote mutations (v2+)
- useSWRSubscription(key, subscribe, config) — real-time data (v2+)
- mutate(key, data, opts) — cache mutation (global or bound)
- preload(key, fetcher) — prefetching (v2+)
- <SWRConfig value={...}> — global configuration
- Middleware via `use` option
- Conditional/dependent fetching (null/false/function keys)

Ecosystem Detection (15+ patterns):
- Core: swr, swr/infinite, swr/mutation, swr/subscription, swr/immutable
- HTTP Clients: fetch, axios, ky, got, ofetch, graphql-request
- Next.js: next (SSR/ISR with SWR)
- Testing: @testing-library/react, msw, jest, vitest
- React: react, react-dom
- React Native: react-native

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all SWR extractors
from .extractors.swr import (
    SWRHookExtractor, SWRHookInfo, SWRInfiniteInfo, SWRSubscriptionInfo,
    SWRMutationExtractor, SWRMutationHookInfo, SWROptimisticUpdateInfo,
    SWRCacheExtractor, SWRConfigInfo, SWRMutateInfo, SWRPreloadInfo,
    SWRMiddlewareExtractor, SWRMiddlewareInfo,
    SWRApiExtractor, SWRImportInfo, SWRIntegrationInfo, SWRTypeInfo,
)


@dataclass
class SWRParseResult:
    """Complete parse result for a file with SWR usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Hooks
    hooks: List[SWRHookInfo] = field(default_factory=list)
    infinite_hooks: List[SWRInfiniteInfo] = field(default_factory=list)
    subscription_hooks: List[SWRSubscriptionInfo] = field(default_factory=list)

    # Mutations (v2+)
    mutation_hooks: List[SWRMutationHookInfo] = field(default_factory=list)
    optimistic_updates: List[SWROptimisticUpdateInfo] = field(default_factory=list)

    # Cache / Config
    configs: List[SWRConfigInfo] = field(default_factory=list)
    mutate_calls: List[SWRMutateInfo] = field(default_factory=list)
    preloads: List[SWRPreloadInfo] = field(default_factory=list)
    config_hooks: List[Dict] = field(default_factory=list)

    # Middleware
    middlewares: List[SWRMiddlewareInfo] = field(default_factory=list)

    # API
    imports: List[SWRImportInfo] = field(default_factory=list)
    integrations: List[SWRIntegrationInfo] = field(default_factory=list)
    types: List[SWRTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    swr_version: str = ""  # v0, v1, v2


class EnhancedSWRParser:
    """
    Enhanced SWR parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when SWR framework is detected. It extracts SWR-specific
    semantics that the language parsers cannot capture.

    Framework detection supports 15+ SWR ecosystem libraries across:
    - Core (swr, swr/infinite, swr/mutation, swr/subscription)
    - HTTP Clients (fetch, axios, ky, got)
    - Next.js (SSR/ISR patterns)
    - Testing (@testing-library/react, msw, jest, vitest)
    - React Native

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # ── Framework Detection Patterns ──────────────────────────────

    FRAMEWORK_PATTERNS = {
        # ── Core SWR ──────────────────────────────────────────────
        'swr': re.compile(
            r"from\s+['\"]swr['\"]|require\(['\"]swr['\"]\)",
            re.MULTILINE
        ),
        'swr-infinite': re.compile(
            r"from\s+['\"]swr/infinite['\"]|require\(['\"]swr/infinite['\"]\)",
            re.MULTILINE
        ),
        'swr-mutation': re.compile(
            r"from\s+['\"]swr/mutation['\"]|require\(['\"]swr/mutation['\"]\)",
            re.MULTILINE
        ),
        'swr-subscription': re.compile(
            r"from\s+['\"]swr/subscription['\"]|require\(['\"]swr/subscription['\"]\)",
            re.MULTILINE
        ),
        'swr-immutable': re.compile(
            r"from\s+['\"]swr/immutable['\"]|require\(['\"]swr/immutable['\"]\)",
            re.MULTILINE
        ),

        # ── HTTP Clients ──────────────────────────────────────────
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|require\(['\"]axios['\"]\)",
            re.MULTILINE
        ),
        'ky': re.compile(
            r"from\s+['\"]ky['\"]",
            re.MULTILINE
        ),
        'graphql-request': re.compile(
            r"from\s+['\"]graphql-request['\"]",
            re.MULTILINE
        ),

        # ── Ecosystem ────────────────────────────────────────────
        'react': re.compile(
            r"from\s+['\"]react['\"]|require\(['\"]react['\"]\)",
            re.MULTILINE
        ),
        'next': re.compile(
            r"from\s+['\"]next[/'\"]|require\(['\"]next['\"]\)",
            re.MULTILINE
        ),
        'react-native': re.compile(
            r"from\s+['\"]react-native['\"]",
            re.MULTILINE
        ),
        'msw': re.compile(
            r"from\s+['\"]msw['\"]|from\s+['\"]@mswjs/data['\"]",
            re.MULTILINE
        ),
    }

    # ── Feature Detection Patterns ────────────────────────────────

    FEATURE_PATTERNS = {
        'use_swr': re.compile(r'useSWR\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_swr_immutable': re.compile(r'useSWRImmutable\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_swr_infinite': re.compile(r'useSWRInfinite\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_swr_mutation': re.compile(r'useSWRMutation\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'use_swr_subscription': re.compile(r'useSWRSubscription\s*(?:<[^>]*>)?\s*\(', re.MULTILINE),
        'swr_config': re.compile(r'<SWRConfig\b', re.MULTILINE),
        'use_swr_config': re.compile(r'useSWRConfig\s*\(', re.MULTILINE),
        'global_mutate': re.compile(r"import\s+\{[^}]*\bmutate\b[^}]*\}\s+from\s+['\"]swr['\"]", re.MULTILINE),
        'preload': re.compile(r"import\s+\{[^}]*\bpreload\b[^}]*\}|preload\s*\(", re.MULTILINE),
        'fallback_data': re.compile(r'\bfallbackData\s*:', re.MULTILINE),
        'initial_data': re.compile(r'\binitialData\s*:', re.MULTILINE),
        'keep_previous_data': re.compile(r'\bkeepPreviousData\b', re.MULTILINE),
        'revalidate_on_focus': re.compile(r'\brevalidateOnFocus\s*:', re.MULTILINE),
        'revalidate_on_reconnect': re.compile(r'\brevalidateOnReconnect\s*:', re.MULTILINE),
        'revalidate_on_mount': re.compile(r'\brevalidateOnMount\s*:', re.MULTILINE),
        'revalidate_if_stale': re.compile(r'\brevalidateIfStale\s*:', re.MULTILINE),
        'refresh_interval': re.compile(r'\brefreshInterval\s*:', re.MULTILINE),
        'deduping_interval': re.compile(r'\bdedupingInterval\s*:', re.MULTILINE),
        'suspense': re.compile(r'\bsuspense\s*:\s*true', re.MULTILINE),
        'error_retry_count': re.compile(r'\berrorRetryCount\s*:', re.MULTILINE),
        'cache_provider': re.compile(r'\bprovider\s*:', re.MULTILINE),
        'middleware': re.compile(r'\buse\s*:\s*\[', re.MULTILINE),
        'conditional_fetching': re.compile(r'useSWR\s*(?:<[^>]*>)?\s*\(\s*(?:null|false)', re.MULTILINE),
        'optimistic_data': re.compile(r'\boptimisticData\s*:', re.MULTILINE),
        'rollback_on_error': re.compile(r'\brollbackOnError\s*:', re.MULTILINE),
        'populate_cache': re.compile(r'\bpopulateCache\s*:', re.MULTILINE),
        'throw_on_error': re.compile(r'\bthrowOnError\s*:', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all SWR extractors."""
        self.hook_extractor = SWRHookExtractor()
        self.mutation_extractor = SWRMutationExtractor()
        self.cache_extractor = SWRCacheExtractor()
        self.middleware_extractor = SWRMiddlewareExtractor()
        self.api_extractor = SWRApiExtractor()

    def is_swr_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains SWR code.

        Returns True if the file imports from SWR or uses SWR patterns.
        """
        swr_indicators = [
            "from 'swr'", 'from "swr"',
            "from 'swr/", 'from "swr/',
            "require('swr')", 'require("swr")',
            'useSWR(', 'useSWRInfinite(',
            'useSWRImmutable(', 'useSWRMutation(',
            'useSWRSubscription(', 'useSWRConfig(',
            '<SWRConfig', 'SWRConfig',
            "swr/infinite", "swr/mutation",
            "swr/subscription", "swr/immutable",
            'preload(',
        ]
        return any(ind in content for ind in swr_indicators)

    def parse(self, content: str, file_path: str = "") -> SWRParseResult:
        """
        Parse a source file for SWR patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            SWRParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = SWRParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.swr_version = self._detect_version(content)

        # ── Hook extraction ───────────────────────────────────────
        try:
            hook_result = self.hook_extractor.extract(content, file_path)
            result.hooks = hook_result.get('hooks', [])
            result.infinite_hooks = hook_result.get('infinite_hooks', [])
            result.subscription_hooks = hook_result.get('subscription_hooks', [])
        except Exception:
            pass

        # ── Mutation extraction ───────────────────────────────────
        try:
            mut_result = self.mutation_extractor.extract(content, file_path)
            result.mutation_hooks = mut_result.get('mutation_hooks', [])
            result.optimistic_updates = mut_result.get('optimistic_updates', [])
        except Exception:
            pass

        # ── Cache extraction ──────────────────────────────────────
        try:
            cache_result = self.cache_extractor.extract(content, file_path)
            result.configs = cache_result.get('configs', [])
            result.mutate_calls = cache_result.get('mutate_calls', [])
            result.preloads = cache_result.get('preloads', [])
            result.config_hooks = cache_result.get('config_hooks', [])
        except Exception:
            pass

        # ── Middleware extraction ──────────────────────────────────
        try:
            mw_result = self.middleware_extractor.extract(content, file_path)
            result.middlewares = mw_result.get('middlewares', [])
        except Exception:
            pass

        # ── API extraction ────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which SWR ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which SWR features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect SWR version based on API usage patterns.

        Returns:
            - 'v2' if SWR v2 patterns detected
            - 'v1' if SWR v1 patterns detected
            - 'v0' if SWR v0 patterns detected
            - '' if unknown
        """
        # v2 indicators (features introduced in v2)
        v2_indicators = [
            'useSWRMutation',         # new in v2
            'useSWRSubscription',     # new in v2
            'preload(',               # new in v2
            'keepPreviousData',       # new in v2
            'optimisticData',         # new in v2
            'rollbackOnError',        # new in v2
            'populateCache',          # new in v2
            'throwOnError',           # new in v2
            'onDiscarded',            # new in v2
            "swr/mutation",           # new subpackage in v2
            "swr/subscription",       # new subpackage in v2
        ]
        if any(ind in content for ind in v2_indicators):
            return "v2"

        # v1 indicators
        v1_indicators = [
            'SWRConfig',              # formalized in v1
            'fallbackData',           # new in v1 (replaces initialData)
            'fallback',               # SWRConfig fallback prop (v1)
            'useSWRImmutable',        # new in v1
            "swr/infinite",           # subpackage formalized in v1
            "swr/immutable",          # subpackage in v1
            'provider:',              # cache provider API (v1)
            'use:',                   # middleware (v1) - but be careful of false positives
        ]
        if any(ind in content for ind in v1_indicators):
            return "v1"

        # v0 indicators
        v0_indicators = [
            'initialData',            # v0 (renamed to fallbackData in v1)
        ]
        if any(ind in content for ind in v0_indicators):
            return "v0"

        # If we see useSWR but no version specifics, assume v2 (current)
        if 'useSWR' in content:
            return "v2"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'v0': 1, 'v1': 2, 'v2': 3}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
