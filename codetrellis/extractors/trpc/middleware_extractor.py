"""
tRPC Middleware Extractor - Extracts middleware definitions, chains, and usage.

Supports tRPC middleware patterns:
- v9: middleware functions on router
- v10/v11: t.middleware(), procedure.use(), middleware composition
- Protected procedures (authedProcedure, adminProcedure)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TRPCMiddlewareInfo:
    """A tRPC middleware definition or usage."""
    name: str
    file: str = ""
    line_number: int = 0
    middleware_type: str = ""  # auth, logging, rateLimit, input, custom
    is_definition: bool = False
    is_usage: bool = False
    uses_ctx: bool = False
    uses_next: bool = False
    is_async: bool = False


@dataclass
class TRPCMiddlewareStackInfo:
    """Aggregate middleware information for a tRPC app."""
    has_auth: bool = False
    has_rate_limiting: bool = False
    has_logging: bool = False
    has_error_handling: bool = False
    has_input_validation: bool = False
    has_cors: bool = False
    total_middleware: int = 0


class TRPCMiddlewareExtractor:
    """Extracts tRPC middleware definitions and usage."""

    # t.middleware() definition
    MIDDLEWARE_DEF_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:t\.middleware|middleware)\s*\(\s*'
        r'(?:async\s+)?\(?',
        re.MULTILINE,
    )

    # .use(middleware) on procedure chain
    MIDDLEWARE_USE_PATTERN = re.compile(
        r'\.use\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    # Protected/authed procedure definitions
    PROTECTED_PROC_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+Procedure)\s*=\s*'
        r'(?:\w+\.)?procedure\s*(?:\.use\s*\(\s*(\w+)\s*\))+',
        re.MULTILINE,
    )

    # Simpler protected procedure: const authedProcedure = t.procedure.use(isAuthed)
    SIMPLE_PROTECTED_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:\w+\.)?(?:publicProcedure|procedure)\s*\.use\s*\(\s*(\w+)\s*\)',
        re.MULTILINE,
    )

    # Auth-related keywords for categorization
    AUTH_KEYWORDS = {'auth', 'authed', 'authenticated', 'protected', 'admin', 'logged', 'session', 'jwt', 'token'}
    RATE_KEYWORDS = {'rate', 'limit', 'throttle'}
    LOG_KEYWORDS = {'log', 'logger', 'logging', 'trace', 'audit'}
    ERROR_KEYWORDS = {'error', 'catch', 'sentry', 'bugsnag'}
    CORS_KEYWORDS = {'cors'}

    def _categorize_middleware(self, name: str) -> str:
        """Categorize middleware by its name."""
        lower = name.lower()
        if any(k in lower for k in self.AUTH_KEYWORDS):
            return 'auth'
        if any(k in lower for k in self.RATE_KEYWORDS):
            return 'rateLimit'
        if any(k in lower for k in self.LOG_KEYWORDS):
            return 'logging'
        if any(k in lower for k in self.ERROR_KEYWORDS):
            return 'errorHandling'
        if any(k in lower for k in self.CORS_KEYWORDS):
            return 'cors'
        return 'custom'

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all tRPC middleware definitions and usages.

        Returns dict with keys: middleware, stack
        """
        middleware = []
        categories_found = set()

        # ── Middleware definitions ───────────────────────────────
        for match in self.MIDDLEWARE_DEF_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_async = 'async' in content[match.start():match.end()]
            category = self._categorize_middleware(name)
            categories_found.add(category)

            # Check if uses ctx/next
            # Look ahead ~500 chars for ctx and next references
            body_preview = content[match.end():match.end() + 500]
            uses_ctx = 'ctx' in body_preview
            uses_next = 'next' in body_preview

            middleware.append(TRPCMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                middleware_type=category,
                is_definition=True,
                uses_ctx=uses_ctx,
                uses_next=uses_next,
                is_async=is_async,
            ))

        # ── Protected procedure definitions ─────────────────────
        for match in self.SIMPLE_PROTECTED_PATTERN.finditer(content):
            proc_name = match.group(1)
            mw_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            category = self._categorize_middleware(mw_name)
            categories_found.add(category)

            middleware.append(TRPCMiddlewareInfo(
                name=mw_name,
                file=file_path,
                line_number=line_num,
                middleware_type=category,
                is_usage=True,
            ))

        # ── Middleware usage in procedure chains (.use()) ────────
        for match in self.MIDDLEWARE_USE_PATTERN.finditer(content):
            mw_name = match.group(1)
            # Skip if already captured as definition
            if any(m.name == mw_name and m.is_definition for m in middleware):
                continue
            line_num = content[:match.start()].count('\n') + 1
            category = self._categorize_middleware(mw_name)
            categories_found.add(category)

            if not any(m.name == mw_name and m.is_usage for m in middleware):
                middleware.append(TRPCMiddlewareInfo(
                    name=mw_name,
                    file=file_path,
                    line_number=line_num,
                    middleware_type=category,
                    is_usage=True,
                ))

        # ── Build stack summary ─────────────────────────────────
        stack = TRPCMiddlewareStackInfo(
            has_auth='auth' in categories_found,
            has_rate_limiting='rateLimit' in categories_found,
            has_logging='logging' in categories_found,
            has_error_handling='errorHandling' in categories_found,
            has_input_validation=bool(re.search(r'\.input\s*\(', content)),
            has_cors='cors' in categories_found,
            total_middleware=len(middleware),
        )

        return {
            'middleware': middleware,
            'stack': stack,
        }
