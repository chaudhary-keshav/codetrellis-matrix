"""
AdonisJS middleware extractor - Extract middleware definitions, kernel, and usage.

Extracts:
- Middleware class definitions (handle method, guard)
- Named middleware registration (kernel.ts / start/kernel.ts)
- Global middleware stack
- Route middleware application
- Middleware groups
- v4: Http/Kernel.ts with global/named arrays
- v5: start/kernel.ts with Server.middleware.register()
- v6: start/kernel.ts with router.use(), server.use()

Supports AdonisJS v4 through v6 middleware patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AdonisMiddlewareInfo:
    """Information about a middleware definition."""
    name: str = ""              # class name or alias
    class_name: str = ""        # AuthMiddleware
    alias: str = ""             # 'auth', 'guest', 'throttle'
    is_global: bool = False     # registered as global middleware
    is_named: bool = False      # registered as named middleware
    has_handle: bool = False    # has handle() method
    is_async: bool = False
    guard: str = ""             # auth guard type
    file: str = ""
    line_number: int = 0


@dataclass
class AdonisMiddlewareKernelInfo:
    """Middleware kernel configuration (start/kernel.ts)."""
    global_middleware: List[str] = field(default_factory=list)
    named_middleware: Dict[str, str] = field(default_factory=dict)  # alias -> import path
    server_middleware: List[str] = field(default_factory=list)      # v6 server.use()
    router_middleware: List[str] = field(default_factory=list)      # v6 router.use()
    file: str = ""
    line_number: int = 0


class AdonisMiddlewareExtractor:
    """Extract AdonisJS middleware definitions and kernel configuration."""

    # Middleware class: export default class AuthMiddleware {
    MIDDLEWARE_CLASS_PATTERN = re.compile(
        r'(?:export\s+default\s+)?class\s+(\w+Middleware)\s*(?:extends\s+(\w+))?\s*\{',
        re.MULTILINE,
    )

    # v4: module.exports = class AuthMiddleware {
    V4_MIDDLEWARE_CLASS_PATTERN = re.compile(
        r'module\.exports\s*=\s*class\s+(\w+Middleware)\s*\{',
        re.MULTILINE,
    )

    # handle method: async handle({ request, auth, response }, next)
    HANDLE_PATTERN = re.compile(
        r'(?:async\s+)?handle\s*\(\s*(?:\{[^}]*\}|\w+)',
        re.MULTILINE,
    )

    # Guard: auth.use('web') or auth.authenticate()
    GUARD_PATTERN = re.compile(
        r"auth\.(?:use\s*\(\s*['\"](\w+)['\"]|authenticate\s*\()",
        re.MULTILINE,
    )

    # ── Kernel patterns ──────────────────────────────────────

    # v5: Server.middleware.register([...])
    V5_GLOBAL_PATTERN = re.compile(
        r'Server\.middleware\.register\s*\(\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    # v5: Server.middleware.registerNamed({ auth: ... })
    V5_NAMED_PATTERN = re.compile(
        r'Server\.middleware\.registerNamed\s*\(\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # v6: server.use([...])
    V6_SERVER_USE_PATTERN = re.compile(
        r'server\.use\s*\(\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    # v6: router.use([...])
    V6_ROUTER_USE_PATTERN = re.compile(
        r'router\.use\s*\(\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    # v6: router.named({ auth: ... }) or export const middleware = router.named({})
    V6_NAMED_PATTERN = re.compile(
        r'(?:router\.named|middleware)\s*(?:=\s*router\.named)?\s*\(\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # v4 kernel global: const globalMiddleware = [...]
    V4_GLOBAL_PATTERN = re.compile(
        r'(?:global|globalMiddleware|serverMiddleware)\s*(?:=|:)\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    # v4 kernel named: const namedMiddleware = { auth: '...', guest: '...' }
    V4_NAMED_PATTERN = re.compile(
        r'(?:named|namedMiddleware)\s*(?:=|:)\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # Import paths in middleware arrays: () => import('...') or require('...')
    IMPORT_REF_PATTERN = re.compile(
        r"(?:import\(['\"]([^'\"]+)['\"]\)|require\(['\"]([^'\"]+)['\"]\)|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )

    # Named middleware key-value: auth: () => import('...')
    NAMED_KV_PATTERN = re.compile(
        r"(\w+)\s*:\s*(?:\(\)\s*=>\s*import\(['\"]([^'\"]+)['\"]\)|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all AdonisJS middleware information from source code.

        Returns:
            Dict with 'middleware' (List[AdonisMiddlewareInfo]),
                       'kernel' (AdonisMiddlewareKernelInfo or None)
        """
        middleware: List[AdonisMiddlewareInfo] = []
        kernel: Optional[AdonisMiddlewareKernelInfo] = None

        # ── Extract middleware class definitions ─────────────────
        for match in list(self.MIDDLEWARE_CLASS_PATTERN.finditer(content)) + \
                      list(self.V4_MIDDLEWARE_CLASS_PATTERN.finditer(content)):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            mw = AdonisMiddlewareInfo(
                name=name,
                class_name=name,
                file=file_path,
                line_number=line_number,
            )

            # Check for handle method
            class_start = match.end()
            class_end = min(class_start + 3000, len(content))
            class_body = content[class_start:class_end]

            handle_match = self.HANDLE_PATTERN.search(class_body)
            if handle_match:
                mw.has_handle = True
                mw.is_async = 'async' in class_body[:handle_match.end()]

            # Check for auth guard
            guard_match = self.GUARD_PATTERN.search(class_body)
            if guard_match:
                mw.guard = guard_match.group(1) or 'default'

            middleware.append(mw)

        # ── Extract kernel configuration ─────────────────────────
        is_kernel_file = self._is_kernel_file(file_path, content)
        if is_kernel_file:
            kernel = self._extract_kernel(content, file_path)

        return {
            'middleware': middleware,
            'kernel': kernel,
        }

    def _is_kernel_file(self, file_path: str, content: str) -> bool:
        """Check if this is a middleware kernel file."""
        normalized = file_path.lower().replace('\\', '/')
        if 'kernel' in normalized:
            return True
        if 'Server.middleware' in content:
            return True
        if 'server.use(' in content and 'router.use(' in content:
            return True
        if 'globalMiddleware' in content or 'namedMiddleware' in content:
            return True
        return False

    def _extract_kernel(self, content: str, file_path: str) -> AdonisMiddlewareKernelInfo:
        """Extract middleware kernel configuration."""
        kernel = AdonisMiddlewareKernelInfo(file=file_path)

        # ── v6 patterns ──────────────────────────────────────────
        # server.use([...])
        server_match = self.V6_SERVER_USE_PATTERN.search(content)
        if server_match:
            kernel.server_middleware = self._extract_import_refs(server_match.group(1))

        # router.use([...])
        router_match = self.V6_ROUTER_USE_PATTERN.search(content)
        if router_match:
            kernel.router_middleware = self._extract_import_refs(router_match.group(1))

        # router.named({...})
        named_match = self.V6_NAMED_PATTERN.search(content)
        if named_match:
            kernel.named_middleware = self._extract_named_middleware(named_match.group(1))

        # ── v5 patterns ──────────────────────────────────────────
        # Server.middleware.register([...])
        v5_global = self.V5_GLOBAL_PATTERN.search(content)
        if v5_global:
            kernel.global_middleware = self._extract_import_refs(v5_global.group(1))

        # Server.middleware.registerNamed({...})
        v5_named = self.V5_NAMED_PATTERN.search(content)
        if v5_named:
            kernel.named_middleware.update(self._extract_named_middleware(v5_named.group(1)))

        # ── v4 patterns ──────────────────────────────────────────
        v4_global = self.V4_GLOBAL_PATTERN.search(content)
        if v4_global:
            kernel.global_middleware = self._extract_import_refs(v4_global.group(1))

        v4_named = self.V4_NAMED_PATTERN.search(content)
        if v4_named:
            kernel.named_middleware.update(self._extract_named_middleware(v4_named.group(1)))

        return kernel

    def _extract_import_refs(self, block: str) -> List[str]:
        """Extract import references from an array block."""
        refs = []
        for match in self.IMPORT_REF_PATTERN.finditer(block):
            ref = match.group(1) or match.group(2) or match.group(3) or ''
            if ref:
                refs.append(ref)
        return refs

    def _extract_named_middleware(self, block: str) -> Dict[str, str]:
        """Extract named middleware from an object block."""
        named = {}
        for match in self.NAMED_KV_PATTERN.finditer(block):
            alias = match.group(1)
            path = match.group(2) or match.group(3) or ''
            named[alias] = path
        return named
