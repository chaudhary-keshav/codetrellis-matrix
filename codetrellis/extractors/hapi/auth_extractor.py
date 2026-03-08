"""
Hapi auth extractor - Extract authentication strategies, schemes, and scope.

Extracts:
- server.auth.strategy() calls (strategy name, scheme, options)
- server.auth.scheme() calls (custom auth scheme definitions)
- server.auth.default() calls (default auth strategy)
- Auth strategies: jwt, cookie, bearer, basic, bell (OAuth)
- Scope-based authorization (scope: ['admin', 'user:write'])
- Auth mode (required, try, optional)
- Auth artifacts and credentials patterns

Supports @hapi/hapi v17-v21+ auth system.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class HapiAuthScopeInfo:
    """Authorization scope configuration."""
    scopes: List[str] = field(default_factory=list)
    entity: str = ""            # user, app, any
    access_type: str = ""       # required, forbidden
    line_number: int = 0


@dataclass
class HapiAuthSchemeInfo:
    """Custom auth scheme definition."""
    name: str = ""
    handler_type: str = ""      # authenticate, payload, response
    has_authenticate: bool = False
    has_payload: bool = False
    has_response: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HapiAuthStrategyInfo:
    """Auth strategy registration."""
    name: str = ""              # 'jwt', 'session', etc.
    scheme: str = ""            # 'jwt', 'cookie', 'bearer-access-token', 'basic', 'bell'
    package: str = ""           # '@hapi/jwt', 'hapi-auth-jwt2', etc.
    mode: str = ""              # 'required', 'try', 'optional'
    is_default: bool = False
    options: Dict[str, Any] = field(default_factory=dict)
    scopes: List[HapiAuthScopeInfo] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class HapiAuthExtractor:
    """Extract Hapi authentication strategies, schemes, and scope."""

    # server.auth.strategy(name, scheme, options)
    STRATEGY_PATTERN = re.compile(
        r'server\.auth\.strategy\s*\(\s*[\'"](\w+)[\'"]\s*,\s*[\'"](\w[\w-]*)[\'"]',
        re.MULTILINE,
    )

    # server.auth.scheme(name, implementation)
    SCHEME_PATTERN = re.compile(
        r'server\.auth\.scheme\s*\(\s*[\'"](\w[\w-]*)[\'"]\s*,',
        re.MULTILINE,
    )

    # server.auth.default(strategy) or server.auth.default({ strategy, mode })
    DEFAULT_PATTERN = re.compile(
        r'server\.auth\.default\s*\(\s*(?:[\'"](\w+)[\'"]|\{([^}]+)\})',
        re.MULTILINE,
    )

    # Auth mode: mode: 'required' | 'try' | 'optional'
    MODE_PATTERN = re.compile(
        r'mode\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    # Scope patterns: scope: ['admin', 'user:write']
    SCOPE_PATTERN = re.compile(
        r'scope\s*:\s*\[([^\]]+)\]',
        re.MULTILINE,
    )

    # Entity pattern: entity: 'user' | 'app' | 'any'
    ENTITY_PATTERN = re.compile(
        r'entity\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    # Common auth packages → scheme mapping
    AUTH_PACKAGE_MAP: Dict[str, str] = {
        '@hapi/jwt': 'jwt',
        '@hapi/cookie': 'cookie',
        '@hapi/basic': 'basic',
        '@hapi/bell': 'bell',
        'hapi-auth-jwt2': 'jwt',
        'hapi-auth-bearer-token': 'bearer-access-token',
        'hapi-auth-cookie': 'cookie',
        '@hapi/crumb': 'crumb',
    }

    # Scheme → authenticate/payload/response
    SCHEME_HANDLER_PATTERN = re.compile(
        r'(authenticate|payload|response)\s*:\s*(?:async\s+)?(?:function|\()',
        re.MULTILINE,
    )

    # validate function in strategy options
    VALIDATE_FUNC_PATTERN = re.compile(
        r'validate\s*:\s*(?:async\s+)?(?:function\s+)?(\w+)',
        re.MULTILINE,
    )

    # Cookie-specific: cookie name, password, isSecure, etc.
    COOKIE_PATTERN = re.compile(
        r'cookie\s*:\s*[\'"](\w+)[\'"]|'
        r'password\s*:\s*[\'"]|'
        r'isSecure\s*:\s*(true|false)',
        re.MULTILINE,
    )

    # JWT-specific: keys, algorithms, verify
    JWT_PATTERN = re.compile(
        r'keys\s*:\s*[\'"]|'
        r'algorithms\s*:\s*\[|'
        r'verify\s*:\s*\{',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Hapi auth information from source code.

        Returns:
            Dict with 'strategies' (List[HapiAuthStrategyInfo]),
                       'schemes' (List[HapiAuthSchemeInfo]),
                       'default_strategy' (str)
        """
        strategies: List[HapiAuthStrategyInfo] = []
        schemes: List[HapiAuthSchemeInfo] = []
        default_strategy = ""

        # ── Extract auth strategies ──────────────────────────────
        for match in self.STRATEGY_PATTERN.finditer(content):
            name = match.group(1)
            scheme = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            strategy = HapiAuthStrategyInfo(
                name=name,
                scheme=scheme,
                file=file_path,
                line_number=line_number,
            )

            # Extract options block
            block_start = match.start()
            block_end = min(block_start + 2000, len(content))
            block = content[block_start:block_end]

            # Mode
            mode_match = self.MODE_PATTERN.search(block)
            if mode_match:
                strategy.mode = mode_match.group(1)

            # Validate function
            validate_match = self.VALIDATE_FUNC_PATTERN.search(block)
            if validate_match:
                strategy.options['validate'] = validate_match.group(1)

            # Detect auth package from imports
            for pkg, pkg_scheme in self.AUTH_PACKAGE_MAP.items():
                if pkg_scheme == scheme:
                    if re.search(re.escape(pkg), content):
                        strategy.package = pkg
                        break

            # Scopes
            strategy.scopes = self._extract_scopes(block, line_number)

            strategies.append(strategy)

        # ── Extract auth schemes ─────────────────────────────────
        for match in self.SCHEME_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            scheme = HapiAuthSchemeInfo(
                name=name,
                file=file_path,
                line_number=line_number,
            )

            # Look for handler types in the scheme implementation
            block_start = match.start()
            block_end = min(block_start + 3000, len(content))
            block = content[block_start:block_end]

            for handler_match in self.SCHEME_HANDLER_PATTERN.finditer(block):
                handler_type = handler_match.group(1)
                if handler_type == 'authenticate':
                    scheme.has_authenticate = True
                elif handler_type == 'payload':
                    scheme.has_payload = True
                elif handler_type == 'response':
                    scheme.has_response = True

            schemes.append(scheme)

        # ── Extract default strategy ─────────────────────────────
        default_match = self.DEFAULT_PATTERN.search(content)
        if default_match:
            default_strategy = default_match.group(1) or ''
            if not default_strategy and default_match.group(2):
                # Parse { strategy: 'name' }
                strat_match = re.search(r'strategy\s*:\s*[\'"](\w+)[\'"]', default_match.group(2))
                if strat_match:
                    default_strategy = strat_match.group(1)

            # Mark the default strategy
            for strategy in strategies:
                if strategy.name == default_strategy:
                    strategy.is_default = True

        return {
            'strategies': strategies,
            'schemes': schemes,
            'default_strategy': default_strategy,
        }

    def _extract_scopes(self, block: str, base_line: int) -> List[HapiAuthScopeInfo]:
        """Extract scope configurations from a block."""
        scopes: List[HapiAuthScopeInfo] = []

        for match in self.SCOPE_PATTERN.finditer(block):
            scope_str = match.group(1)
            scope_list = [s.strip().strip("'\"") for s in scope_str.split(',') if s.strip()]

            scope_info = HapiAuthScopeInfo(
                scopes=scope_list,
                line_number=base_line,
            )

            # Entity
            entity_match = self.ENTITY_PATTERN.search(block)
            if entity_match:
                scope_info.entity = entity_match.group(1)

            scopes.append(scope_info)

        return scopes
