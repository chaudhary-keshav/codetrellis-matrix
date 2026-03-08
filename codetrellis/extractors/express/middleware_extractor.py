"""
Express.js Middleware Extractor - Extracts middleware usage, definitions, and stacks.

Supports:
- app.use() global middleware
- Router-level middleware  
- Route-level middleware
- Built-in middleware: express.json(), express.urlencoded(), express.static()
- Third-party middleware: cors, helmet, morgan, compression, cookie-parser, etc.
- Custom middleware function definitions
- Middleware ordering/stacking
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ExpressMiddlewareInfo:
    """A single middleware usage or definition."""
    name: str
    file: str = ""
    line_number: int = 0
    middleware_type: str = ""  # builtin, third-party, custom, error-handler
    category: str = ""  # security, parsing, logging, cors, static, session, auth, compression, etc.
    is_global: bool = False  # app.use() vs route-specific
    mount_path: str = ""  # Optional mount path
    has_options: bool = False
    is_conditional: bool = False
    source_package: str = ""  # e.g., 'cors', 'helmet', 'morgan'


@dataclass
class ExpressMiddlewareStackInfo:
    """Summary of middleware stack configuration."""
    total_middleware: int = 0
    global_middleware: int = 0
    route_middleware: int = 0
    builtin_count: int = 0
    third_party_count: int = 0
    custom_count: int = 0
    has_cors: bool = False
    has_helmet: bool = False
    has_compression: bool = False
    has_session: bool = False
    has_auth: bool = False
    has_rate_limiting: bool = False
    has_body_parser: bool = False
    has_cookie_parser: bool = False
    has_morgan: bool = False
    has_static: bool = False


class ExpressMiddlewareExtractor:
    """Extracts Express.js middleware information from source code."""

    # Built-in middleware
    BUILTIN_MIDDLEWARE = {
        'express.json': ('builtin', 'parsing'),
        'express.urlencoded': ('builtin', 'parsing'),
        'express.static': ('builtin', 'static'),
        'express.raw': ('builtin', 'parsing'),
        'express.text': ('builtin', 'parsing'),
        'express.Router': ('builtin', 'routing'),
    }

    # Third-party middleware detection
    THIRD_PARTY_MIDDLEWARE = {
        'cors': ('third-party', 'cors'),
        'helmet': ('third-party', 'security'),
        'morgan': ('third-party', 'logging'),
        'compression': ('third-party', 'compression'),
        'cookie-parser': ('third-party', 'cookies'),
        'cookieParser': ('third-party', 'cookies'),
        'express-session': ('third-party', 'session'),
        'session': ('third-party', 'session'),
        'passport': ('third-party', 'auth'),
        'express-rate-limit': ('third-party', 'rate-limiting'),
        'rateLimit': ('third-party', 'rate-limiting'),
        'multer': ('third-party', 'file-upload'),
        'body-parser': ('third-party', 'parsing'),
        'bodyParser': ('third-party', 'parsing'),
        'express-validator': ('third-party', 'validation'),
        'hpp': ('third-party', 'security'),
        'csurf': ('third-party', 'security'),
        'express-mongo-sanitize': ('third-party', 'security'),
        'xss-clean': ('third-party', 'security'),
        'serve-favicon': ('third-party', 'static'),
        'connect-flash': ('third-party', 'flash'),
        'method-override': ('third-party', 'http'),
        'response-time': ('third-party', 'monitoring'),
        'express-prometheus-middleware': ('third-party', 'monitoring'),
        'swagger-ui-express': ('third-party', 'docs'),
        'express-openapi-validator': ('third-party', 'validation'),
    }

    # app.use() pattern
    USE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*use\s*\(\s*'
        r'(?:[\'"`]([^\'"`]*)[\'"`]\s*,\s*)?'  # Optional mount path
        r'(\w[\w.]*(?:\([^)]*\))?)',  # Middleware reference
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract middleware information from Express.js source code."""
        middleware_list: List[ExpressMiddlewareInfo] = []
        lines = content.split('\n')

        # Detect imports to map variable names to packages
        import_map = self._build_import_map(content)

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # app.use() or router.use()
            use_match = self.USE_PATTERN.search(stripped)
            if use_match:
                receiver = use_match.group(1)
                mount_path = use_match.group(2) or ''
                mw_ref = use_match.group(3)

                mw_name = mw_ref.split('(')[0].strip()
                mw_type, category, source = self._classify_middleware(mw_name, import_map)

                middleware_list.append(ExpressMiddlewareInfo(
                    name=mw_name,
                    file=file_path,
                    line_number=i,
                    middleware_type=mw_type,
                    category=category,
                    is_global=receiver in ('app', 'server', 'express'),
                    mount_path=mount_path,
                    has_options='(' in mw_ref and mw_ref.endswith(')'),
                    is_conditional='if ' in line or 'process.env' in line,
                    source_package=source,
                ))

            # Detect custom middleware definitions: function(req, res, next)
            custom_mw_match = re.search(
                r'(?:const|let|var|function)\s+(\w+)\s*=?\s*(?:async\s+)?(?:function\s*)?\('
                r'\s*(?:req|request)\s*,\s*(?:res|response)\s*,\s*next\s*\)',
                stripped
            )
            if custom_mw_match:
                mw_name = custom_mw_match.group(1)
                middleware_list.append(ExpressMiddlewareInfo(
                    name=mw_name,
                    file=file_path,
                    line_number=i,
                    middleware_type='custom',
                    category='custom',
                    source_package='custom',
                ))

        # Build stack summary
        stack = self._build_stack_summary(middleware_list)

        return {
            "middleware": middleware_list,
            "stack": stack,
        }

    def _build_import_map(self, content: str) -> Dict[str, str]:
        """Map variable names to imported package names."""
        import_map: Dict[str, str] = {}

        # ESM: import xyz from 'package'
        for match in re.finditer(r'import\s+(\w+)\s+from\s+[\'"`]([^\'"`]+)[\'"`]', content):
            import_map[match.group(1)] = match.group(2)

        # ESM: import { xyz } from 'package'
        for match in re.finditer(r'import\s+\{([^}]+)\}\s+from\s+[\'"`]([^\'"`]+)[\'"`]', content):
            names = [n.strip().split(' as ')[-1].strip() for n in match.group(1).split(',')]
            pkg = match.group(2)
            for name in names:
                import_map[name] = pkg

        # CJS: const xyz = require('package')
        for match in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)', content):
            import_map[match.group(1)] = match.group(2)

        return import_map

    def _classify_middleware(self, name: str, import_map: Dict[str, str]) -> tuple:
        """Classify a middleware by type, category, and source package."""
        # Check built-in
        if name in self.BUILTIN_MIDDLEWARE or f'express.{name}' in self.BUILTIN_MIDDLEWARE:
            key = name if name in self.BUILTIN_MIDDLEWARE else f'express.{name}'
            mw_type, category = self.BUILTIN_MIDDLEWARE[key]
            return mw_type, category, 'express'

        # Check if name maps to a known package
        source_pkg = import_map.get(name, '')
        for pkg_name, (mw_type, category) in self.THIRD_PARTY_MIDDLEWARE.items():
            if name == pkg_name or source_pkg == pkg_name or pkg_name in source_pkg:
                return mw_type, category, pkg_name

        # Check name-based heuristics
        name_lower = name.lower()
        for pkg_name, (mw_type, category) in self.THIRD_PARTY_MIDDLEWARE.items():
            if pkg_name.replace('-', '') in name_lower:
                return mw_type, category, pkg_name

        return 'custom', 'custom', source_pkg or 'custom'

    def _build_stack_summary(self, middleware_list: List[ExpressMiddlewareInfo]) -> ExpressMiddlewareStackInfo:
        """Build a summary of the middleware stack."""
        stack = ExpressMiddlewareStackInfo()
        stack.total_middleware = len(middleware_list)

        for mw in middleware_list:
            if mw.is_global:
                stack.global_middleware += 1
            else:
                stack.route_middleware += 1

            if mw.middleware_type == 'builtin':
                stack.builtin_count += 1
            elif mw.middleware_type == 'third-party':
                stack.third_party_count += 1
            else:
                stack.custom_count += 1

            cat = mw.category
            if cat == 'cors':
                stack.has_cors = True
            elif cat == 'security':
                stack.has_helmet = True
            elif cat == 'compression':
                stack.has_compression = True
            elif cat == 'session':
                stack.has_session = True
            elif cat == 'auth':
                stack.has_auth = True
            elif cat == 'rate-limiting':
                stack.has_rate_limiting = True
            elif cat == 'parsing':
                stack.has_body_parser = True
            elif cat == 'cookies':
                stack.has_cookie_parser = True
            elif cat == 'logging':
                stack.has_morgan = True
            elif cat == 'static':
                stack.has_static = True

        return stack
