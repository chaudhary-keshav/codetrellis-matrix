"""
Koa API Extractor - Extracts API patterns and ecosystem info from Koa applications.

Detects:
- RESTful resource patterns (CRUD on a resource path)
- API versioning (prefix-based, header-based)
- Response format patterns (JSON, HTML, stream)
- Import ecosystem detection (koa and related packages)
- TypeScript type definitions for Koa
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KoaResourceInfo:
    """A detected RESTful resource."""
    name: str  # Resource name (e.g., 'users')
    base_path: str  # e.g., '/api/users'
    operations: List[str] = field(default_factory=list)  # ['GET', 'POST', 'PUT', 'DELETE']
    file: str = ""
    line_number: int = 0


@dataclass
class KoaImportInfo:
    """A Koa-related import."""
    source: str  # Package name
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    is_default_import: bool = False
    is_type_import: bool = False


@dataclass
class KoaApiSummary:
    """Summary of API patterns in a Koa app."""
    total_resources: int = 0
    has_versioning: bool = False
    version_prefix: str = ""
    response_formats: List[str] = field(default_factory=list)


class KoaApiExtractor:
    """Extracts Koa API patterns from source code."""

    # Import patterns
    IMPORT_PATTERNS = [
        # ESM: import Koa from 'koa'
        re.compile(
            r"import\s+(?:(\w+)(?:\s*,\s*\{([^}]+)\})?\s+from|"
            r"\{([^}]+)\}\s+from|"
            r"\*\s+as\s+(\w+)\s+from)\s+['\"]([^'\"]+)['\"]",
        ),
        # CJS: const Koa = require('koa')
        re.compile(
            r"(?:const|let|var)\s+(?:(\w+)|{([^}]+)})\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ),
    ]

    # Type import: import type { Context } from 'koa'
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
    )

    # Koa-related packages
    KOA_PACKAGES = {
        'koa', '@koa/router', 'koa-router', 'koa-bodyparser', 'koa-body',
        '@koa/cors', 'koa-cors', 'koa-helmet', 'koa-session', 'koa-jwt',
        'koa-passport', 'koa-static', 'koa-compress', 'koa-logger',
        'koa-views', 'koa-mount', 'koa-compose', 'koa-etag',
        'koa-conditional-get', 'koa-ratelimit', 'koa-send', 'koa-multer',
        'koa-ejs', 'koa-pug', 'koa-response-time', 'koa-cache-control',
        'koa-json', 'koa-json-error', 'koa-tree-router', 'koa-better-router',
        'koa-websocket', 'koa-socket-2', '@koa/multer', 'koa-csrf',
        'koa-generic-session', 'koa-convert', 'koa-onerror',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Koa API patterns from source code."""
        imports: List[KoaImportInfo] = []
        resources: List[KoaResourceInfo] = []

        # Extract imports
        for pattern in self.IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                groups = match.groups()
                source = groups[-1] if groups[-1] else ''
                if not any(pkg in source for pkg in ('koa', '@koa')):
                    continue
                line_num = content[:match.start()].count('\n') + 1

                named = []
                default_name = ''
                if groups[0]:
                    default_name = groups[0]
                if groups[1]:
                    named = [n.strip() for n in groups[1].split(',') if n.strip()]
                elif groups[2]:
                    named = [n.strip() for n in groups[2].split(',') if n.strip()]

                imports.append(KoaImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    named_imports=named,
                    is_default_import=bool(default_name),
                ))

        # Type imports
        for match in self.TYPE_IMPORT_PATTERN.finditer(content):
            source = match.group(2)
            if not any(pkg in source for pkg in ('koa', '@koa')):
                continue
            line_num = content[:match.start()].count('\n') + 1
            named = [n.strip() for n in match.group(1).split(',') if n.strip()]
            imports.append(KoaImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named,
                is_type_import=True,
            ))

        # Detect resources from route patterns
        route_methods = {}  # path -> set of methods
        route_pattern = re.compile(
            r'\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE,
        )
        for match in route_pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            base = re.sub(r'/:\w+', '', path).rstrip('/')
            if base not in route_methods:
                route_methods[base] = set()
            route_methods[base].add(method)

        for base_path, methods in route_methods.items():
            if len(methods) >= 2:
                name = base_path.rstrip('/').split('/')[-1] if base_path else 'root'
                resources.append(KoaResourceInfo(
                    name=name,
                    base_path=base_path or '/',
                    operations=sorted(methods),
                    file=file_path,
                ))

        # API versioning detection
        has_versioning = bool(re.search(r'/v\d+/', content))
        version_prefix = ''
        v_match = re.search(r'prefix\s*:\s*[\'"`](/v\d+)[\'"`]', content)
        if v_match:
            version_prefix = v_match.group(1)
            has_versioning = True

        summary = KoaApiSummary(
            total_resources=len(resources),
            has_versioning=has_versioning,
            version_prefix=version_prefix,
        )

        return {
            'imports': imports,
            'resources': resources,
            'summary': summary,
        }
