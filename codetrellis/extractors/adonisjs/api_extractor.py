"""
AdonisJS API extractor - Extract imports, providers, packages, and version detection.

Extracts:
- @adonisjs/* package imports
- AdonisJS providers (AppProvider, RouteProvider, etc.)
- IoC container bindings
- Config providers
- Package version detection (v4, v5, v6)
- Ecosystem packages (lucid, auth, shield, bouncer, drive, mail, etc.)

Supports AdonisJS v4 through v6.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AdonisImportInfo:
    """Information about an AdonisJS-related import."""
    package: str = ""           # '@adonisjs/core', '@adonisjs/lucid'
    alias: str = ""             # import alias
    is_core: bool = False       # @adonisjs/core package
    is_official: bool = False   # @adonisjs/* package
    members: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class AdonisProviderInfo:
    """Information about an AdonisJS provider."""
    name: str = ""              # 'AppProvider', '@adonisjs/lucid'
    path: str = ""              # provider path
    is_core: bool = False
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class AdonisApiSummary:
    """Summary of AdonisJS API usage."""
    adonis_version_hint: str = ""   # 'v4', 'v5', 'v6'
    total_routes: int = 0
    total_controllers: int = 0
    total_models: int = 0
    total_middleware: int = 0
    has_auth: bool = False
    has_lucid: bool = False
    has_validator: bool = False
    has_bouncer: bool = False
    has_mail: bool = False
    has_drive: bool = False
    has_ally: bool = False          # social auth
    has_redis: bool = False
    has_ws: bool = False            # websocket
    orm_type: str = ""              # 'lucid'
    template_engine: str = ""       # 'edge'
    ecosystem_packages: List[str] = field(default_factory=list)


class AdonisApiExtractor:
    """Extract AdonisJS API surface, imports, and ecosystem usage."""

    # Core @adonisjs/* packages
    CORE_PACKAGES: Set[str] = {
        '@adonisjs/core', '@adonisjs/http-server', '@adonisjs/router',
        '@adonisjs/application', '@adonisjs/config', '@adonisjs/env',
        '@adonisjs/logger', '@adonisjs/bodyparser', '@adonisjs/cors',
        '@adonisjs/encryption', '@adonisjs/hash', '@adonisjs/events',
        '@adonisjs/fold',  # IoC container
    }

    # Official @adonisjs/* ecosystem packages
    OFFICIAL_PACKAGES: Set[str] = {
        '@adonisjs/lucid', '@adonisjs/auth', '@adonisjs/shield',
        '@adonisjs/bouncer', '@adonisjs/drive', '@adonisjs/mail',
        '@adonisjs/ally', '@adonisjs/redis', '@adonisjs/session',
        '@adonisjs/view', '@adonisjs/i18n', '@adonisjs/limiter',
        '@adonisjs/transmit', '@adonisjs/static', '@adonisjs/vite',
        '@adonisjs/inertia', '@adonisjs/cache', '@adonisjs/health',
        '@adonisjs/repl', '@adonisjs/assembler', '@adonisjs/ace',
        '@adonisjs/preset-adonis', '@adonisjs/tsconfig',
    }

    # v4 legacy packages
    V4_PACKAGES: Set[str] = {
        '@adonisjs/framework', '@adonisjs/lucid', '@adonisjs/auth',
        '@adonisjs/persona', '@adonisjs/antl', '@adonisjs/websocket',
        '@adonisjs/mail', '@adonisjs/drive', '@adonisjs/validator',
        '@adonisjs/session', '@adonisjs/shield', '@adonisjs/redis',
    }

    # Community packages
    COMMUNITY_PACKAGES: Set[str] = {
        'adonis-ally-discord', 'adonis-ally-github', 'adonis-ally-google',
        'adonis5-scheduler', 'adonis5-swagger', 'adonisjs-swagger',
        'adonis-bull', 'adonis-acl', 'adonis-bumblebee',
        'adonis-notifications', 'adonis-queue-pro',
    }

    # Version detection patterns
    V6_INDICATORS = {
        '@adonisjs/core': re.compile(r"from\s+['\"]@adonisjs/core/", re.MULTILINE),
        'vite': re.compile(r"@adonisjs/vite|defineConfig", re.MULTILINE),
        'esm_import': re.compile(r"import\s+.*from\s+['\"]#", re.MULTILINE),  # subpath imports
        'vine': re.compile(r"@adonisjs/core/.*vine|vine\.compile", re.MULTILINE),
    }

    V5_INDICATORS = {
        'ioc_imports': re.compile(r"from\s+['\"]@ioc:", re.MULTILINE),
        'adonis_env': re.compile(r"Env\.get\s*\(", re.MULTILINE),
        'application': re.compile(r"Application\.start|ApplicationContract", re.MULTILINE),
    }

    V4_INDICATORS = {
        'use_function': re.compile(r"use\s*\(\s*['\"]App/|use\s*\(\s*['\"]Adonis/", re.MULTILINE),
        'module_exports': re.compile(r"module\.exports\s*=\s*class", re.MULTILINE),
        'legacy_route': re.compile(r"Route\.on\s*\(|Route\.render\s*\(", re.MULTILINE),
    }

    # Import patterns
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]|"
        r"(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\(['\"]([^'\"]+)['\"]\))",
        re.MULTILINE,
    )

    # v4 use() pattern: const User = use('App/Models/User')
    USE_PATTERN = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*use\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Provider registration
    PROVIDER_PATTERN = re.compile(
        r"['\"](@adonisjs/[^'\"]+)['\"]|['\"](\./providers/\w+)['\"]|['\"](\w+Provider)['\"]",
        re.MULTILINE,
    )

    # providers array
    PROVIDERS_ARRAY_PATTERN = re.compile(
        r'providers\s*(?:=|:)\s*\[([^\]]*)\]',
        re.DOTALL,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all AdonisJS API/import information from source code.

        Returns:
            Dict with 'imports' (List[AdonisImportInfo]),
                       'providers' (List[AdonisProviderInfo]),
                       'summary' (AdonisApiSummary)
        """
        imports: List[AdonisImportInfo] = []
        providers: List[AdonisProviderInfo] = []
        summary = AdonisApiSummary()

        all_packages = self.CORE_PACKAGES | self.OFFICIAL_PACKAGES | self.V4_PACKAGES | self.COMMUNITY_PACKAGES

        # ── Extract imports ──────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            members_str = match.group(1) or match.group(4) or ''
            alias = match.group(2) or match.group(5) or ''
            package = match.group(3) or match.group(6) or ''

            if not package:
                continue

            # Check if AdonisJS-related
            is_adonis = (
                package in all_packages or
                package.startswith('@adonisjs/') or
                package.startswith('@ioc:Adonis') or  # v5 IoC container imports
                package.startswith('adonis') or
                package.startswith('#')  # v6 subpath imports
            )

            if not is_adonis:
                continue

            line_number = content[:match.start()].count('\n') + 1

            imp = AdonisImportInfo(
                package=package,
                alias=alias,
                is_core=package in self.CORE_PACKAGES,
                is_official=package in self.OFFICIAL_PACKAGES or package.startswith('@adonisjs/'),
                line_number=line_number,
            )

            if members_str:
                imp.members = [m.strip() for m in members_str.split(',') if m.strip()]

            imports.append(imp)

            if package not in summary.ecosystem_packages:
                summary.ecosystem_packages.append(package)

        # ── v4 use() imports ─────────────────────────────────────
        for match in self.USE_PATTERN.finditer(content):
            alias = match.group(1)
            path = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            imports.append(AdonisImportInfo(
                package=path,
                alias=alias,
                is_core=path.startswith('Adonis/'),
                line_number=line_number,
            ))

        # ── Extract providers ────────────────────────────────────
        providers_match = self.PROVIDERS_ARRAY_PATTERN.search(content)
        if providers_match:
            providers_block = providers_match.group(1)
            for prov_match in self.PROVIDER_PATTERN.finditer(providers_block):
                pkg = prov_match.group(1) or prov_match.group(2) or prov_match.group(3) or ''
                if pkg:
                    providers.append(AdonisProviderInfo(
                        name=pkg,
                        path=pkg,
                        is_core=pkg in self.CORE_PACKAGES or pkg.startswith('@adonisjs/'),
                        is_custom=pkg.startswith('./'),
                        file=file_path,
                    ))

        # ── Version detection ────────────────────────────────────
        summary.adonis_version_hint = self._detect_version(content, imports)

        # ── Feature detection ────────────────────────────────────
        pkg_set = {imp.package for imp in imports}

        summary.has_lucid = any(
            '@adonisjs/lucid' in p or 'Lucid' in p or 'BaseModel' in content
            for p in pkg_set
        )
        summary.has_auth = any(
            '@adonisjs/auth' in p or 'auth' in p.lower()
            for p in pkg_set
        ) or 'AuthMiddleware' in content
        summary.has_validator = (
            '@adonisjs/validator' in pkg_set or
            'vine' in content.lower() or
            'request.validate(' in content or
            'request.validateUsing(' in content
        )
        summary.has_bouncer = '@adonisjs/bouncer' in pkg_set or 'bouncer' in content.lower()
        summary.has_mail = '@adonisjs/mail' in pkg_set
        summary.has_drive = '@adonisjs/drive' in pkg_set
        summary.has_ally = '@adonisjs/ally' in pkg_set
        summary.has_redis = '@adonisjs/redis' in pkg_set
        summary.has_ws = (
            '@adonisjs/transmit' in pkg_set or
            '@adonisjs/websocket' in pkg_set
        )

        if summary.has_lucid:
            summary.orm_type = 'lucid'

        if '@adonisjs/view' in pkg_set or 'edge' in content.lower():
            summary.template_engine = 'edge'
        if '@adonisjs/inertia' in pkg_set:
            summary.template_engine = 'inertia'

        return {
            'imports': imports,
            'providers': providers,
            'summary': summary,
        }

    def _detect_version(self, content: str, imports: List[AdonisImportInfo]) -> str:
        """Detect AdonisJS version from code patterns."""
        # Check v6 first (most specific)
        for name, pattern in self.V6_INDICATORS.items():
            if pattern.search(content):
                return 'v6'

        # Check v5
        for name, pattern in self.V5_INDICATORS.items():
            if pattern.search(content):
                return 'v5'

        # Check v4
        for name, pattern in self.V4_INDICATORS.items():
            if pattern.search(content):
                return 'v4'

        # Fallback: if using @adonisjs/core, likely v5+
        if any(imp.package == '@adonisjs/core' for imp in imports):
            return 'v5+'

        return ''
