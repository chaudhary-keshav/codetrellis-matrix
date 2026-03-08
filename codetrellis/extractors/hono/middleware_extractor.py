"""
Hono Middleware Extractor - Extracts Hono middleware usage from source code.

Detects:
- app.use() global middleware
- app.use('/path', middleware) path-scoped middleware
- Built-in Hono middleware from hono/... imports
- Third-party middleware
- Middleware composition patterns
- Custom middleware functions
- Hono v1-v4 middleware patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HonoMiddlewareInfo:
    """A single middleware usage."""
    name: str
    middleware_type: str = "custom"  # builtin, third-party, custom, error
    category: str = ""  # security, auth, validation, logging, cors, cache, compress, etc.
    is_global: bool = True
    mount_path: str = ""
    source_package: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HonoMiddlewareStackInfo:
    """Summary of the middleware stack in a Hono application."""
    has_cors: bool = False
    has_jwt: bool = False
    has_basic_auth: bool = False
    has_bearer_auth: bool = False
    has_logger: bool = False
    has_pretty_json: bool = False
    has_secure_headers: bool = False
    has_cache: bool = False
    has_compress: bool = False
    has_etag: bool = False
    has_timing: bool = False
    has_body_limit: bool = False
    has_csrf: bool = False
    has_powered_by: bool = False
    has_trailing_slash: bool = False


# Known Hono built-in middleware from hono/* packages
KNOWN_MIDDLEWARE: Dict[str, tuple] = {
    # (category, source_package)
    'cors': ('security', 'hono/cors'),
    'jwt': ('auth', 'hono/jwt'),
    'basicAuth': ('auth', 'hono/basic-auth'),
    'bearerAuth': ('auth', 'hono/bearer-auth'),
    'logger': ('logging', 'hono/logger'),
    'prettyJSON': ('response', 'hono/pretty-json'),
    'secureHeaders': ('security', 'hono/secure-headers'),
    'cache': ('performance', 'hono/cache'),
    'compress': ('performance', 'hono/compress'),
    'etag': ('performance', 'hono/etag'),
    'timing': ('monitoring', 'hono/timing'),
    'bodyLimit': ('validation', 'hono/body-limit'),
    'csrf': ('security', 'hono/csrf'),
    'poweredBy': ('metadata', 'hono/powered-by'),
    'trailingSlash': ('routing', 'hono/trailing-slash'),
    'requestId': ('monitoring', 'hono/request-id'),
    'methodOverride': ('routing', 'hono/method-override'),
    'ipRestriction': ('security', 'hono/ip-restriction'),
    'contextStorage': ('utility', 'hono/context-storage'),
    'timeout': ('performance', 'hono/timeout'),
    # Third-party
    'sentry': ('monitoring', '@hono/sentry'),
    'zValidator': ('validation', '@hono/zod-validator'),
    'vValidator': ('validation', '@hono/valibot-validator'),
    'tbValidator': ('validation', '@hono/typebox-validator'),
    'arktypeValidator': ('validation', '@hono/arktype-validator'),
    'graphqlServer': ('api', '@hono/graphql-server'),
    'swaggerUI': ('documentation', '@hono/swagger-ui'),
    'prometheus': ('monitoring', '@hono/prometheus'),
    'trpcServer': ('api', '@hono/trpc-server'),
    'clerkAuth': ('auth', '@hono/clerk-auth'),
    'authJs': ('auth', '@hono/auth-js'),
    'oidcAuth': ('auth', '@hono/oidc-auth'),
    'firebase': ('auth', '@hono/firebase-auth'),
    'qwik': ('framework', '@hono/qwik-city'),
    'node-ws': ('websocket', '@hono/node-ws'),
}


class HonoMiddlewareExtractor:
    """Extracts Hono middleware usage from source code."""

    # app.use() patterns
    APP_USE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*use\s*\(\s*'
        r'(?:[\'"`]([^\'"`]*)[\'"`]\s*,\s*)?'
        r'(\w+)',
    )

    # Hono middleware import: import { cors } from 'hono/cors'
    HONO_IMPORT_PATTERN = re.compile(
        r"(?:import\s*\{([^}]+)\}\s*from|"
        r"const\s*\{([^}]+)\}\s*=\s*require\(['\"])"
        r"['\"]?(hono/[\w-]+|@hono/[\w-]+)['\"]?\)?",
    )

    # Custom middleware: const myMiddleware = createMiddleware(...)
    CREATE_MIDDLEWARE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*createMiddleware\s*[<(]',
    )

    # Factory middleware: const myMiddleware = (options) => async (c, next) => { ... }
    FACTORY_PATTERN = re.compile(
        r'(?:const|let|var|function)\s+(\w+)\s*=?\s*(?:\([^)]*\))?\s*(?:=>|{)\s*'
        r'(?:return\s+)?async\s*\(\s*c\s*,\s*next\s*\)',
    )

    # Error handler: app.onError((err, c) => ...)
    ERROR_HANDLER_PATTERN = re.compile(
        r'(\w+)\s*\.\s*onError\s*\(',
    )

    # Not found handler: app.notFound((c) => ...)
    NOT_FOUND_PATTERN = re.compile(
        r'(\w+)\s*\.\s*notFound\s*\(',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hono middleware from source code."""
        middleware: List[HonoMiddlewareInfo] = []
        seen_names = set()

        # Detect Hono middleware imports
        imported_middleware: Dict[str, str] = {}  # name -> source
        for match in self.HONO_IMPORT_PATTERN.finditer(content):
            names_str = match.group(1) or match.group(2) or ''
            source = match.group(3) or ''
            for name in names_str.split(','):
                name = name.strip().split(' as ')[-1].strip()
                if name:
                    imported_middleware[name] = source

        # app.use() calls
        for match in self.APP_USE_PATTERN.finditer(content):
            mount_path = match.group(2) or ''
            mw_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            if mw_name in seen_names and mount_path == '':
                continue
            seen_names.add(mw_name)

            # Determine type and category
            mw_type = 'custom'
            category = ''
            source_package = ''

            if mw_name in KNOWN_MIDDLEWARE:
                cat, src = KNOWN_MIDDLEWARE[mw_name]
                mw_type = 'builtin'
                category = cat
                source_package = src
            elif mw_name in imported_middleware:
                source_package = imported_middleware[mw_name]
                if source_package.startswith('hono/'):
                    mw_type = 'builtin'
                elif source_package.startswith('@hono/'):
                    mw_type = 'third-party'
                else:
                    mw_type = 'third-party'

            middleware.append(HonoMiddlewareInfo(
                name=mw_name,
                middleware_type=mw_type,
                category=category,
                is_global=not bool(mount_path),
                mount_path=mount_path,
                source_package=source_package,
                file=file_path,
                line_number=line_num,
            ))

        # Error handler
        for match in self.ERROR_HANDLER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            middleware.append(HonoMiddlewareInfo(
                name='onError',
                middleware_type='builtin',
                category='error',
                is_global=True,
                file=file_path,
                line_number=line_num,
            ))

        # Not found handler
        for match in self.NOT_FOUND_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            middleware.append(HonoMiddlewareInfo(
                name='notFound',
                middleware_type='builtin',
                category='error',
                is_global=True,
                file=file_path,
                line_number=line_num,
            ))

        # createMiddleware usage
        for match in self.CREATE_MIDDLEWARE_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            if name not in seen_names:
                middleware.append(HonoMiddlewareInfo(
                    name=name,
                    middleware_type='custom',
                    file=file_path,
                    line_number=line_num,
                ))

        # Build stack summary
        mw_names = {m.name for m in middleware}
        stack = HonoMiddlewareStackInfo(
            has_cors='cors' in mw_names,
            has_jwt='jwt' in mw_names,
            has_basic_auth='basicAuth' in mw_names,
            has_bearer_auth='bearerAuth' in mw_names,
            has_logger='logger' in mw_names,
            has_pretty_json='prettyJSON' in mw_names,
            has_secure_headers='secureHeaders' in mw_names,
            has_cache='cache' in mw_names,
            has_compress='compress' in mw_names,
            has_etag='etag' in mw_names,
            has_timing='timing' in mw_names,
            has_body_limit='bodyLimit' in mw_names,
            has_csrf='csrf' in mw_names,
            has_powered_by='poweredBy' in mw_names,
            has_trailing_slash='trailingSlash' in mw_names,
        )

        return {
            'middleware': middleware,
            'stack': stack,
        }
