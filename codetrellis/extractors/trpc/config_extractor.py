"""
tRPC Config Extractor - Extracts adapter, link, and configuration patterns.

Supports:
- Adapters: @trpc/server/adapters/* (express, fastify, next, standalone, ws, fetch, lambda)
- Links: httpBatchLink, httpLink, wsLink, splitLink, loggerLink, etc.
- initTRPC / createTRPCProxyClient configuration
- Error formatters, transformers (superjson)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TRPCAdapterInfo:
    """A tRPC server adapter."""
    adapter_type: str  # express, fastify, next, standalone, ws, fetch, lambda, h3
    file: str = ""
    line_number: int = 0
    import_path: str = ""
    handler_name: str = ""


@dataclass
class TRPCLinkInfo:
    """A tRPC client link."""
    link_type: str  # httpBatchLink, httpLink, wsLink, splitLink, loggerLink, etc.
    file: str = ""
    line_number: int = 0
    url: str = ""
    is_batch: bool = False


@dataclass
class TRPCConfigSummary:
    """Aggregate tRPC configuration summary."""
    has_superjson: bool = False
    has_error_formatter: bool = False
    has_ssr: bool = False
    has_websockets: bool = False
    has_subscriptions: bool = False
    adapter_type: str = ""
    trpc_version: str = ""


class TRPCConfigExtractor:
    """Extracts tRPC configuration, adapters, and links."""

    # Adapter import patterns
    ADAPTER_PATTERNS = {
        'express': re.compile(
            r"from\s+['\"]@trpc/server/adapters/express['\"]|"
            r"createExpressMiddleware",
            re.MULTILINE,
        ),
        'fastify': re.compile(
            r"from\s+['\"]@trpc/server/adapters/fastify['\"]|"
            r"fastifyTRPCPlugin",
            re.MULTILINE,
        ),
        'next': re.compile(
            r"from\s+['\"]@trpc/server/adapters/next['\"]|"
            r"createNextApiHandler|fetchRequestHandler",
            re.MULTILINE,
        ),
        'standalone': re.compile(
            r"from\s+['\"]@trpc/server/adapters/standalone['\"]|"
            r"createHTTPServer",
            re.MULTILINE,
        ),
        'ws': re.compile(
            r"from\s+['\"]@trpc/server/adapters/ws['\"]|"
            r"applyWSSHandler",
            re.MULTILINE,
        ),
        'fetch': re.compile(
            r"from\s+['\"]@trpc/server/adapters/fetch['\"]|"
            r"fetchRequestHandler",
            re.MULTILINE,
        ),
        'lambda': re.compile(
            r"from\s+['\"]@trpc/server/adapters/aws-lambda['\"]|"
            r"awsLambdaRequestHandler",
            re.MULTILINE,
        ),
        'h3': re.compile(
            r"from\s+['\"]trpc-nuxt['\"]|"
            r"createNuxtApiHandler",
            re.MULTILINE,
        ),
    }

    # Link patterns
    LINK_PATTERNS = {
        'httpBatchLink': re.compile(
            r'httpBatchLink\s*\(', re.MULTILINE,
        ),
        'httpLink': re.compile(
            r'httpLink\s*\(', re.MULTILINE,
        ),
        'wsLink': re.compile(
            r'wsLink\s*\(', re.MULTILINE,
        ),
        'splitLink': re.compile(
            r'splitLink\s*\(', re.MULTILINE,
        ),
        'loggerLink': re.compile(
            r'loggerLink\s*\(', re.MULTILINE,
        ),
        'httpBatchStreamLink': re.compile(
            r'httpBatchStreamLink\s*\(', re.MULTILINE,
        ),
        'unstable_httpBatchStreamLink': re.compile(
            r'unstable_httpBatchStreamLink\s*\(', re.MULTILINE,
        ),
    }

    # initTRPC pattern
    INIT_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*initTRPC\s*(?:\.\s*context\s*<[^>]*>\s*\(\s*\))?\s*\.create\s*\(',
        re.MULTILINE,
    )

    # Superjson transformer
    SUPERJSON_PATTERN = re.compile(
        r'superjson|transformer\s*:\s*superjson',
        re.MULTILINE,
    )

    # Error formatter
    ERROR_FORMATTER_PATTERN = re.compile(
        r'errorFormatter|\.errorFormatter\s*\(',
        re.MULTILINE,
    )

    # URL in link config
    URL_PATTERN = re.compile(
        r"url\s*:\s*['\"`]([^'\"`]+)['\"`]",
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract tRPC configuration, adapters, and links.

        Returns dict with keys: adapters, links, summary
        """
        adapters = []
        links = []

        # ── Adapters ────────────────────────────────────────────
        adapter_type = ""
        for adapter, pattern in self.ADAPTER_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                adapters.append(TRPCAdapterInfo(
                    adapter_type=adapter,
                    file=file_path,
                    line_number=line_num,
                    import_path=f"@trpc/server/adapters/{adapter}",
                ))
                adapter_type = adapter

        # ── Links ───────────────────────────────────────────────
        for link_type, pattern in self.LINK_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                # Try to find URL in nearby config
                nearby = content[match.start():match.start() + 300]
                url_match = self.URL_PATTERN.search(nearby)
                url = url_match.group(1) if url_match else ""

                links.append(TRPCLinkInfo(
                    link_type=link_type,
                    file=file_path,
                    line_number=line_num,
                    url=url,
                    is_batch='batch' in link_type.lower(),
                ))

        # ── Summary ─────────────────────────────────────────────
        has_ws = any(l.link_type in ('wsLink',) for l in links)
        has_subs = bool(re.search(r'\.subscription\s*\(', content))

        summary = TRPCConfigSummary(
            has_superjson=bool(self.SUPERJSON_PATTERN.search(content)),
            has_error_formatter=bool(self.ERROR_FORMATTER_PATTERN.search(content)),
            has_ssr=bool(re.search(r'ssr\s*:\s*true', content)),
            has_websockets=has_ws,
            has_subscriptions=has_subs,
            adapter_type=adapter_type,
        )

        return {
            'adapters': adapters,
            'links': links,
            'summary': summary,
        }
