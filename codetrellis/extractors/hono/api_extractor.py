"""
Hono API Extractor - Extracts API patterns and ecosystem information.

Detects:
- RESTful resource patterns from route definitions
- API versioning (v1, v2, etc.)
- Import analysis for Hono ecosystem packages
- Multi-runtime detection (Cloudflare Workers, Deno, Bun, Node.js, AWS Lambda, etc.)
- Hono adapter usage
- RPC mode (hc client)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set


@dataclass
class HonoResourceInfo:
    """A RESTful resource detected from route patterns."""
    name: str
    routes: int = 0
    methods: List[str] = field(default_factory=list)
    has_crud: bool = False
    base_path: str = ""


@dataclass
class HonoImportInfo:
    """An import from a Hono ecosystem package."""
    name: str
    source: str
    is_type_import: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HonoRuntimeInfo:
    """Detected runtime/deployment target."""
    runtime: str  # cloudflare-workers, deno, bun, node, aws-lambda, vercel, netlify, fastly
    adapter: str = ""  # @hono/node-server, etc.
    entry_point: str = ""


@dataclass
class HonoApiSummary:
    """Summary of Hono API patterns."""
    total_resources: int = 0
    total_imports: int = 0
    runtime: str = ""
    has_rpc: bool = False
    has_openapi: bool = False
    has_graphql: bool = False
    has_websocket: bool = False
    has_streaming: bool = False
    api_style: str = ""  # rest, rpc, graphql, mixed


class HonoApiExtractor:
    """Extracts API patterns and ecosystem information from Hono source code."""

    # Import patterns
    IMPORT_PATTERNS = [
        # ESM: import { Hono } from 'hono'
        re.compile(
            r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"
        ),
        # CJS: const { Hono } = require('hono')
        re.compile(
            r"(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)"
        ),
    ]

    # Type import: import type { ... } from 'hono'
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]"
    )

    # Hono packages set
    HONO_PACKAGES: Set[str] = {
        # Core
        'hono', 'hono/hono-base',
        # Routing
        'hono/router/reg-exp-router', 'hono/router/trie-router',
        'hono/router/smart-router', 'hono/router/linear-router',
        'hono/router/pattern-router',
        # Middleware
        'hono/cors', 'hono/jwt', 'hono/basic-auth', 'hono/bearer-auth',
        'hono/logger', 'hono/pretty-json', 'hono/secure-headers',
        'hono/cache', 'hono/compress', 'hono/etag', 'hono/timing',
        'hono/body-limit', 'hono/csrf', 'hono/powered-by',
        'hono/trailing-slash', 'hono/request-id', 'hono/method-override',
        'hono/ip-restriction', 'hono/context-storage', 'hono/timeout',
        # Helpers
        'hono/html', 'hono/css', 'hono/jsx', 'hono/jsx/dom',
        'hono/streaming', 'hono/cookie', 'hono/adapter',
        'hono/factory', 'hono/validator', 'hono/testing',
        'hono/utils/body', 'hono/utils/buffer', 'hono/utils/cookie',
        # RPC
        'hono/client',
        # Third-party
        '@hono/zod-validator', '@hono/valibot-validator',
        '@hono/typebox-validator', '@hono/arktype-validator',
        '@hono/graphql-server', '@hono/swagger-ui', '@hono/node-server',
        '@hono/sentry', '@hono/prometheus', '@hono/trpc-server',
        '@hono/clerk-auth', '@hono/auth-js', '@hono/oidc-auth',
        '@hono/firebase-auth', '@hono/qwik-city', '@hono/node-ws',
    }

    # Runtime detection patterns
    RUNTIME_PATTERNS = {
        'cloudflare-workers': re.compile(
            r"export\s+default\s+app|"
            r"addEventListener\s*\(\s*['\"]fetch['\"]|"
            r"from\s+['\"]hono/cloudflare-workers['\"]|"
            r"c\.env\.\w+|c\.executionCtx",
            re.MULTILINE
        ),
        'deno': re.compile(
            r"Deno\.serve|from\s+['\"]https://deno\.land|"
            r"from\s+['\"]hono/deno['\"]|"
            r"import.*from\s+['\"]npm:hono",
            re.MULTILINE
        ),
        'bun': re.compile(
            r"export\s+default\s+\{?\s*(?:port|fetch)|"
            r"Bun\.serve|from\s+['\"]hono/bun['\"]",
            re.MULTILINE
        ),
        'node': re.compile(
            r"from\s+['\"]@hono/node-server['\"]|"
            r"require\(['\"]@hono/node-server['\"]\)|"
            r"serve\s*\(\s*(?:app|\{.*fetch.*\})",
            re.MULTILINE
        ),
        'aws-lambda': re.compile(
            r"from\s+['\"]hono/aws-lambda['\"]|"
            r"handle\s*\(\s*event\s*,\s*context|"
            r"APIGatewayProxyEvent",
            re.MULTILINE
        ),
        'vercel': re.compile(
            r"from\s+['\"]hono/vercel['\"]|"
            r"export\s+(?:const|default)\s+(?:GET|POST|PUT|DELETE|PATCH)",
            re.MULTILINE
        ),
        'netlify': re.compile(
            r"from\s+['\"]hono/netlify['\"]|"
            r"netlify.*edge",
            re.MULTILINE
        ),
        'fastly': re.compile(
            r"from\s+['\"]hono/fastly['\"]|"
            r"addEventListener\s*\(\s*['\"]fetch['\"].*Fastly",
            re.MULTILINE
        ),
    }

    # RPC mode: hc<AppType>('...')
    RPC_PATTERN = re.compile(
        r"from\s+['\"]hono/client['\"]|hc\s*<|hc\s*\(",
    )

    # OpenAPI
    OPENAPI_PATTERN = re.compile(
        r"from\s+['\"]@hono/zod-openapi['\"]|createRoute|openapi",
    )

    # GraphQL
    GRAPHQL_PATTERN = re.compile(
        r"from\s+['\"]@hono/graphql-server['\"]|graphqlServer",
    )

    # WebSocket
    WEBSOCKET_PATTERN = re.compile(
        r"from\s+['\"]@hono/node-ws['\"]|"
        r"upgradeWebSocket|c\.upgrade",
    )

    # Streaming
    STREAMING_PATTERN = re.compile(
        r"from\s+['\"]hono/streaming['\"]|"
        r"c\.stream\(|c\.streamText\(|c\.streamSSE\(|"
        r"stream\.write|stream\.pipe",
    )

    # Resource extraction from routes
    RESOURCE_PATTERN = re.compile(
        r'(?:get|post|put|delete|patch)\s*\(\s*[\'"`]/(?:api/)?(?:v\d+/)?(\w+)',
        re.IGNORECASE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hono API patterns from source code."""
        imports: List[HonoImportInfo] = []
        resources_map: Dict[str, HonoResourceInfo] = {}

        # Extract imports
        for pattern in self.IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                names_str = match.group(1) or match.group(2) or ''
                source = match.group(3)
                line_num = content[:match.start()].count('\n') + 1

                if not any(source.startswith(p) for p in ('hono', '@hono/')):
                    continue

                for name in names_str.split(','):
                    name = name.strip().split(' as ')[-1].strip()
                    if name:
                        imports.append(HonoImportInfo(
                            name=name,
                            source=source,
                            file=file_path,
                            line_number=line_num,
                        ))

        # Type imports
        for match in self.TYPE_IMPORT_PATTERN.finditer(content):
            names_str = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            if any(source.startswith(p) for p in ('hono', '@hono/')):
                for name in names_str.split(','):
                    name = name.strip().split(' as ')[-1].strip()
                    if name:
                        imports.append(HonoImportInfo(
                            name=name,
                            source=source,
                            is_type_import=True,
                            file=file_path,
                            line_number=line_num,
                        ))

        # Detect resources from route patterns
        for match in self.RESOURCE_PATTERN.finditer(content):
            resource_name = match.group(1).lower()
            # Skip common non-resource paths
            if resource_name in ('api', 'v1', 'v2', 'v3', 'auth', 'health', 'status'):
                continue

            method_match = re.match(r'(get|post|put|delete|patch)', match.group(0), re.IGNORECASE)
            method = method_match.group(1).upper() if method_match else 'GET'

            if resource_name not in resources_map:
                resources_map[resource_name] = HonoResourceInfo(
                    name=resource_name,
                    base_path=f'/{resource_name}',
                )
            res = resources_map[resource_name]
            res.routes += 1
            if method not in res.methods:
                res.methods.append(method)

        # Mark CRUD resources
        for res in resources_map.values():
            crud_methods = {'GET', 'POST', 'PUT', 'DELETE'}
            if crud_methods.issubset(set(res.methods)):
                res.has_crud = True

        resources = list(resources_map.values())

        # Detect runtime
        runtime = ''
        adapter = ''
        for rt, pattern in self.RUNTIME_PATTERNS.items():
            if pattern.search(content):
                runtime = rt
                break
        if '@hono/node-server' in content:
            adapter = '@hono/node-server'

        runtime_info = HonoRuntimeInfo(
            runtime=runtime,
            adapter=adapter,
        ) if runtime else None

        # Feature detection
        has_rpc = bool(self.RPC_PATTERN.search(content))
        has_openapi = bool(self.OPENAPI_PATTERN.search(content))
        has_graphql = bool(self.GRAPHQL_PATTERN.search(content))
        has_websocket = bool(self.WEBSOCKET_PATTERN.search(content))
        has_streaming = bool(self.STREAMING_PATTERN.search(content))

        # Determine API style
        api_style = 'rest'
        if has_rpc and has_graphql:
            api_style = 'mixed'
        elif has_rpc:
            api_style = 'rpc'
        elif has_graphql:
            api_style = 'graphql'

        summary = HonoApiSummary(
            total_resources=len(resources),
            total_imports=len(imports),
            runtime=runtime,
            has_rpc=has_rpc,
            has_openapi=has_openapi,
            has_graphql=has_graphql,
            has_websocket=has_websocket,
            has_streaming=has_streaming,
            api_style=api_style,
        )

        return {
            'imports': imports,
            'resources': resources,
            'runtime': runtime_info,
            'summary': summary,
        }
