"""
Hapi API extractor - Extract imports, ecosystem packages, and API surface.

Extracts:
- @hapi/* package imports (inert, vision, boom, joi, etc.)
- Community plugin imports (hapi-swagger, hapi-auth-jwt2, etc.)
- Hapi utility usage (Boom errors, Joi validation, wreck HTTP client)
- Ecosystem integration (swagger, documentation, monitoring)
- Version detection from package patterns

Supports @hapi/hapi v17-v21+ ecosystem.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class HapiImportInfo:
    """Information about a Hapi-related import."""
    package: str = ""           # '@hapi/hapi', '@hapi/boom', 'joi'
    alias: str = ""             # import alias
    is_official: bool = False   # @hapi/* package
    is_community: bool = False  # community plugin
    members: List[str] = field(default_factory=list)  # named imports
    line_number: int = 0


@dataclass
class HapiApiSummary:
    """Summary of Hapi API usage in a file or project."""
    hapi_version_hint: str = ""     # detected version hint
    total_routes: int = 0
    total_plugins: int = 0
    total_strategies: int = 0
    total_methods: int = 0
    total_ext_points: int = 0
    has_swagger: bool = False
    has_monitoring: bool = False
    validation_library: str = ""     # joi, zod, yup
    cache_provider: str = ""         # catbox-redis, catbox-memcached
    frameworks_detected: List[str] = field(default_factory=list)
    ecosystem_packages: List[str] = field(default_factory=list)


class HapiApiExtractor:
    """Extract Hapi API surface, imports, and ecosystem usage."""

    # @hapi/* official packages
    HAPI_OFFICIAL_PACKAGES: Set[str] = {
        '@hapi/hapi', '@hapi/boom', '@hapi/joi', '@hapi/hoek',
        '@hapi/inert', '@hapi/vision', '@hapi/cookie', '@hapi/bell',
        '@hapi/basic', '@hapi/jwt', '@hapi/crumb', '@hapi/yar',
        '@hapi/good', '@hapi/nes', '@hapi/scooter', '@hapi/blankie',
        '@hapi/h2o2', '@hapi/wreck', '@hapi/lab', '@hapi/code',
        '@hapi/catbox', '@hapi/catbox-memory', '@hapi/catbox-redis',
        '@hapi/catbox-memcached', '@hapi/glue', '@hapi/confidence',
        '@hapi/accept', '@hapi/heavy', '@hapi/podium', '@hapi/somever',
    }

    # Community/ecosystem packages
    COMMUNITY_PACKAGES: Set[str] = {
        'hapi-swagger', 'hapi-auth-jwt2', 'hapi-auth-bearer-token',
        'hapi-rate-limit', 'hapi-pino', 'hapi-boom-decorators',
        'hapi-auth-cookie', 'laabr', 'blipp', 'hapi-dev-errors',
        'hapi-alive', 'hapi-pagination', 'schmervice', 'schwifty',
        'hapi-hemera', 'hapi-graceful-pm2', 'haute-couture',
        'hapi-auth-keycloak', 'hapi-pal',
    }

    # Legacy hapi packages (pre-v17 / pre-scope)
    LEGACY_PACKAGES: Set[str] = {
        'hapi', 'joi', 'boom', 'hoek', 'inert', 'vision',
        'hapi-auth-cookie', 'good', 'good-console', 'good-squeeze',
        'catbox', 'catbox-redis', 'catbox-memcached', 'wreck',
        'lab', 'code',
    }

    # Swagger/documentation packages
    SWAGGER_PACKAGES: Set[str] = {
        'hapi-swagger', '@hapi/vision', '@hapi/inert',
    }

    # Monitoring packages
    MONITORING_PACKAGES: Set[str] = {
        '@hapi/good', 'hapi-pino', 'laabr', 'hapi-alive',
    }

    # Import patterns
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]|"
        r"(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\(['\"]([^'\"]+)['\"]\))",
        re.MULTILINE,
    )

    # Boom usage: Boom.badRequest(), Boom.unauthorized(), etc.
    BOOM_PATTERN = re.compile(
        r'Boom\.(\w+)\s*\(',
        re.MULTILINE,
    )

    # Joi usage: Joi.object(), Joi.string(), etc.
    JOI_PATTERN = re.compile(
        r'Joi\.(\w+)\s*\(',
        re.MULTILINE,
    )

    # Wreck usage: Wreck.get(), Wreck.post(), etc.
    WRECK_PATTERN = re.compile(
        r'Wreck\.(\w+)\s*\(',
        re.MULTILINE,
    )

    # Version detection patterns
    # @hapi/hapi → v17+; hapi → pre-v17
    VERSION_PATTERNS = {
        '@hapi/hapi': '17+',
        'hapi': 'pre-17',
        '@hapi/joi': '17+',
        'joi': 'pre-17',
        '@hapi/boom': '17+',
        'boom': 'pre-17',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Hapi API/import information from source code.

        Returns:
            Dict with 'imports' (List[HapiImportInfo]),
                       'summary' (HapiApiSummary)
        """
        imports: List[HapiImportInfo] = []
        summary = HapiApiSummary()

        all_packages = self.HAPI_OFFICIAL_PACKAGES | self.COMMUNITY_PACKAGES | self.LEGACY_PACKAGES

        # ── Extract imports ──────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            # ES Module: import { X } from 'pkg' or import X from 'pkg'
            members_str = match.group(1) or match.group(4) or ''
            alias = match.group(2) or match.group(5) or ''
            package = match.group(3) or match.group(6) or ''

            if not package:
                continue

            # Check if it's a Hapi-related package
            if package not in all_packages and not package.startswith('@hapi/'):
                # Also check for partial matches (e.g., 'hapi-' prefix)
                if not any(package.startswith(prefix) for prefix in ('hapi-', '@hapi/')):
                    continue

            line_number = content[:match.start()].count('\n') + 1

            imp = HapiImportInfo(
                package=package,
                alias=alias,
                is_official=package in self.HAPI_OFFICIAL_PACKAGES or package.startswith('@hapi/'),
                is_community=package in self.COMMUNITY_PACKAGES,
                line_number=line_number,
            )

            if members_str:
                imp.members = [m.strip() for m in members_str.split(',') if m.strip()]

            imports.append(imp)

            # Track ecosystem packages
            if package not in summary.ecosystem_packages:
                summary.ecosystem_packages.append(package)

        # ── Version hint ─────────────────────────────────────────
        for pkg, version in self.VERSION_PATTERNS.items():
            if any(imp.package == pkg for imp in imports):
                summary.hapi_version_hint = version
                break

        # ── Swagger detection ────────────────────────────────────
        summary.has_swagger = any(
            imp.package in self.SWAGGER_PACKAGES for imp in imports
        )

        # ── Monitoring detection ─────────────────────────────────
        summary.has_monitoring = any(
            imp.package in self.MONITORING_PACKAGES for imp in imports
        )

        # ── Validation library ───────────────────────────────────
        if any(imp.package in ('@hapi/joi', 'joi') for imp in imports):
            summary.validation_library = 'joi'
        elif self.JOI_PATTERN.search(content):
            summary.validation_library = 'joi'
        elif re.search(r"from\s+['\"]zod['\"]", content):
            summary.validation_library = 'zod'
        elif re.search(r"from\s+['\"]yup['\"]", content):
            summary.validation_library = 'yup'

        # ── Cache provider ───────────────────────────────────────
        for imp in imports:
            if 'catbox' in imp.package:
                summary.cache_provider = imp.package
                break

        return {
            'imports': imports,
            'summary': summary,
        }
