"""
Koa Middleware Extractor - Extracts middleware usage from Koa applications.

Supports:
- app.use(middleware) global middleware
- router.use(middleware) router-level middleware
- Common Koa middleware: koa-bodyparser, koa-static, koa-cors, koa-helmet,
  koa-session, koa-passport, koa-jwt, koa-compress, koa-logger, koa-views,
  koa-mount, koa-compose
- Middleware composition: compose([mw1, mw2, mw3])
- Error handling middleware (try/catch, ctx.throw)
- Middleware ordering detection
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KoaMiddlewareInfo:
    """A Koa middleware usage."""
    name: str
    file: str = ""
    line_number: int = 0
    middleware_type: str = ""  # global, router, error, composed
    category: str = ""  # security, auth, logging, parsing, compression, static, session, etc.
    is_global: bool = False
    mount_path: str = ""  # For koa-mount: app.use(mount('/api', middleware))
    source_package: str = ""  # Package name the middleware comes from
    is_error_handler: bool = False


@dataclass
class KoaMiddlewareStackInfo:
    """Summary of middleware stack in a Koa app file."""
    file: str = ""
    total_middleware: int = 0
    global_middleware: int = 0
    has_cors: bool = False
    has_helmet: bool = False
    has_compression: bool = False
    has_session: bool = False
    has_auth: bool = False
    has_rate_limiting: bool = False
    has_body_parser: bool = False
    has_logger: bool = False
    has_static: bool = False
    has_error_handler: bool = False


# Well-known Koa middleware categorization
KNOWN_MIDDLEWARE = {
    # Security
    'koa-helmet': ('security', 'koa-helmet'),
    'helmet': ('security', 'koa-helmet'),
    'koa-cors': ('security', '@koa/cors'),
    'cors': ('security', '@koa/cors'),
    'koa-csrf': ('security', 'koa-csrf'),
    'csrf': ('security', 'koa-csrf'),
    # Auth
    'koa-jwt': ('auth', 'koa-jwt'),
    'jwt': ('auth', 'koa-jwt'),
    'koa-passport': ('auth', 'koa-passport'),
    'passport': ('auth', 'koa-passport'),
    'koa-session': ('session', 'koa-session'),
    'session': ('session', 'koa-session'),
    'koa-generic-session': ('session', 'koa-generic-session'),
    # Logging
    'koa-logger': ('logging', 'koa-logger'),
    'logger': ('logging', 'koa-logger'),
    'koa-morgan': ('logging', 'koa-morgan'),
    # Parsing
    'koa-bodyparser': ('parsing', 'koa-bodyparser'),
    'bodyParser': ('parsing', 'koa-bodyparser'),
    'koa-body': ('parsing', 'koa-body'),
    'koaBody': ('parsing', 'koa-body'),
    'koa-multer': ('upload', 'koa-multer'),
    # Compression
    'koa-compress': ('compression', 'koa-compress'),
    'compress': ('compression', 'koa-compress'),
    # Static files
    'koa-static': ('static', 'koa-static'),
    'serve': ('static', 'koa-static'),
    'koa-send': ('static', 'koa-send'),
    # Views
    'koa-views': ('views', 'koa-views'),
    'views': ('views', 'koa-views'),
    'koa-ejs': ('views', 'koa-ejs'),
    # Mount
    'koa-mount': ('routing', 'koa-mount'),
    'mount': ('routing', 'koa-mount'),
    # Compose
    'koa-compose': ('compose', 'koa-compose'),
    'compose': ('compose', 'koa-compose'),
    # Rate limiting
    'koa-ratelimit': ('rate-limiting', 'koa-ratelimit'),
    'rateLimit': ('rate-limiting', 'koa-ratelimit'),
    # Cache / ETag
    'koa-etag': ('caching', 'koa-etag'),
    'koa-conditional-get': ('caching', 'koa-conditional-get'),
    'koa-cache-control': ('caching', 'koa-cache-control'),
    # Response time
    'koa-response-time': ('monitoring', 'koa-response-time'),
    'responseTime': ('monitoring', 'koa-response-time'),
}


class KoaMiddlewareExtractor:
    """Extracts Koa middleware usage from source code."""

    # Global middleware: app.use(middleware)
    APP_USE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*use\s*\(\s*'
        r'(?:(?:mount\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*)?)?'
        r'(\w+)',
    )

    # Compose pattern: compose([mw1, mw2])
    COMPOSE_PATTERN = re.compile(
        r'compose\s*\(\s*\[\s*([^\]]+)\]',
    )

    # Error handler pattern: app.use(async (ctx, next) => { try { await next() } catch (err) { ... } })
    ERROR_HANDLER_PATTERN = re.compile(
        r'\.use\s*\(\s*(?:async\s+)?\(\s*ctx\s*,\s*next\s*\)\s*=>\s*\{[^}]*try\s*\{[^}]*await\s+next\s*\(',
        re.DOTALL,
    )

    # Error handler pattern v2: function-based
    ERROR_HANDLER_FN_PATTERN = re.compile(
        r'\.use\s*\(\s*(?:async\s+)?function\s*\w*\s*\(\s*ctx\s*,\s*next\s*\)\s*\{[^}]*try\s*\{[^}]*await\s+next',
        re.DOTALL,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Koa middleware information from source code."""
        middleware: List[KoaMiddlewareInfo] = []

        # Extract app.use() calls
        for match in self.APP_USE_PATTERN.finditer(content):
            receiver = match.group(1)
            mount_path = match.group(2) or ""
            mw_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            category, source_pkg = KNOWN_MIDDLEWARE.get(mw_name, ('', ''))
            is_global = receiver in ('app', 'server', 'koa')

            middleware.append(KoaMiddlewareInfo(
                name=mw_name,
                file=file_path,
                line_number=line_num,
                middleware_type='global' if is_global else 'router',
                category=category,
                is_global=is_global,
                mount_path=mount_path,
                source_package=source_pkg,
            ))

        # Extract compose() middleware
        for match in self.COMPOSE_PATTERN.finditer(content):
            mw_list = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            names = [n.strip() for n in mw_list.split(',') if n.strip()]
            for name in names:
                clean = name.strip("'\" ")
                category, source_pkg = KNOWN_MIDDLEWARE.get(clean, ('', ''))
                middleware.append(KoaMiddlewareInfo(
                    name=clean,
                    file=file_path,
                    line_number=line_num,
                    middleware_type='composed',
                    category=category,
                    source_package=source_pkg,
                ))

        # Check for error handling middleware
        has_error_handler = bool(
            self.ERROR_HANDLER_PATTERN.search(content) or
            self.ERROR_HANDLER_FN_PATTERN.search(content)
        )

        # Build stack summary
        stack = KoaMiddlewareStackInfo(
            file=file_path,
            total_middleware=len(middleware),
            global_middleware=sum(1 for m in middleware if m.is_global),
            has_cors=any(m.category == 'security' and 'cors' in m.name.lower() for m in middleware),
            has_helmet=any(m.category == 'security' and 'helmet' in m.name.lower() for m in middleware),
            has_compression=any(m.category == 'compression' for m in middleware),
            has_session=any(m.category == 'session' for m in middleware),
            has_auth=any(m.category == 'auth' for m in middleware),
            has_rate_limiting=any(m.category == 'rate-limiting' for m in middleware),
            has_body_parser=any(m.category == 'parsing' for m in middleware),
            has_logger=any(m.category == 'logging' for m in middleware),
            has_static=any(m.category == 'static' for m in middleware),
            has_error_handler=has_error_handler,
        )

        return {
            'middleware': middleware,
            'stack': stack if middleware or has_error_handler else None,
        }
