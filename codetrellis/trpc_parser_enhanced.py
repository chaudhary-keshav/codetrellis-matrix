"""
EnhancedTRPCParser v1.0 - Comprehensive tRPC parser using all extractors.

This parser integrates all tRPC extractors to provide complete parsing of
tRPC application files. It runs as a supplementary layer on top of the
JavaScript/TypeScript parsers, extracting tRPC-specific semantics.

Supports:
- tRPC v9.x (createRouter, query/mutation on router, context, middleware)
- tRPC v10.x (initTRPC, t.router/t.procedure/t.middleware, publicProcedure,
              .input()/.output()/.query()/.mutation()/.subscription(),
              createTRPCProxyClient, links, superjson transformer)
- tRPC v11.x (httpBatchStreamLink, server functions, improved streaming,
              createTRPCClient, enhanced adapters)

tRPC-specific extraction:
- Routers: t.router({ ... }), createTRPCRouter(), createRouter() (v9)
- Procedures: .query(), .mutation(), .subscription() with input/output schemas
- Middleware: t.middleware(), .use(), protected procedures (authedProcedure)
- Context: createContext, createTRPCContext, ctx typing
- Links: httpBatchLink, httpLink, wsLink, splitLink, loggerLink
- Adapters: express, fastify, next, standalone, ws, fetch, lambda
- Clients: createTRPCProxyClient, createTRPCReact, createTRPCNext
- Type Inference: inferRouterInputs, inferRouterOutputs

Framework detection (20+ tRPC ecosystem patterns):
- Core: @trpc/server, @trpc/client, @trpc/react-query, @trpc/next
- Adapters: @trpc/server/adapters/express, /fastify, /next, /standalone, /ws, /fetch
- Validation: zod, yup, superstruct, io-ts, @sinclair/typebox
- Transformer: superjson
- Ecosystem: trpc-openapi, trpc-shield, trpc-panel, trpc-nuxt
- Database: @prisma/client, drizzle-orm

Optional AST support via tree-sitter-typescript / tree-sitter-javascript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.85 - tRPC Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all tRPC extractors
from .extractors.trpc import (
    TRPCRouterExtractor, TRPCRouterInfo, TRPCProcedureInfo, TRPCMergedRouterInfo,
    TRPCMiddlewareExtractor, TRPCMiddlewareInfo, TRPCMiddlewareStackInfo,
    TRPCContextExtractor, TRPCContextInfo, TRPCInputInfo, TRPCOutputInfo,
    TRPCConfigExtractor, TRPCAdapterInfo, TRPCLinkInfo, TRPCConfigSummary,
    TRPCApiExtractor, TRPCImportInfo, TRPCClientInfo, TRPCApiSummary,
)


@dataclass
class TRPCParseResult:
    """Complete parse result for a tRPC file."""
    file_path: str
    file_type: str = "router"  # router, middleware, context, config, client, adapter, test

    # Routers
    routers: List[TRPCRouterInfo] = field(default_factory=list)
    procedures: List[TRPCProcedureInfo] = field(default_factory=list)
    merged_routers: List[TRPCMergedRouterInfo] = field(default_factory=list)

    # Middleware
    middleware: List[TRPCMiddlewareInfo] = field(default_factory=list)
    middleware_stack: Optional[TRPCMiddlewareStackInfo] = None

    # Context
    contexts: List[TRPCContextInfo] = field(default_factory=list)
    inputs: List[TRPCInputInfo] = field(default_factory=list)
    outputs: List[TRPCOutputInfo] = field(default_factory=list)

    # Configuration
    adapters: List[TRPCAdapterInfo] = field(default_factory=list)
    links: List[TRPCLinkInfo] = field(default_factory=list)
    config_summary: Optional[TRPCConfigSummary] = None

    # API Patterns
    imports: List[TRPCImportInfo] = field(default_factory=list)
    clients: List[TRPCClientInfo] = field(default_factory=list)
    api_summary: Optional[TRPCApiSummary] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    trpc_version: str = ""
    is_typescript: bool = False
    total_procedures: int = 0
    total_routers: int = 0
    total_middleware: int = 0


class EnhancedTRPCParser:
    """
    Enhanced tRPC parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript/TypeScript parsers
    when tRPC framework is detected. It extracts tRPC-specific semantics
    that the language parsers cannot capture.

    Optional AST: tree-sitter-typescript / tree-sitter-javascript
    Optional LSP: typescript-language-server (tsserver)
    """

    # tRPC ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core tRPC ────────────────────────────────────────────
        '@trpc/server': re.compile(
            r"from\s+['\"]@trpc/server['\"]|require\(['\"]@trpc/server['\"]\)|"
            r"initTRPC",
            re.MULTILINE,
        ),
        '@trpc/client': re.compile(
            r"from\s+['\"]@trpc/client['\"]|require\(['\"]@trpc/client['\"]\)|"
            r"createTRPCProxyClient|createTRPCClient",
            re.MULTILINE,
        ),
        '@trpc/react-query': re.compile(
            r"from\s+['\"]@trpc/react-query['\"]|createTRPCReact",
            re.MULTILINE,
        ),
        '@trpc/next': re.compile(
            r"from\s+['\"]@trpc/next['\"]|createTRPCNext",
            re.MULTILINE,
        ),
        'trpc-v9': re.compile(
            r"from\s+['\"]trpc['\"]|require\(['\"]trpc['\"]\)|"
            r"from\s+['\"]@trpc/server['\"].*createRouter",
            re.MULTILINE,
        ),

        # ── Adapters ────────────────────────────────────────────
        'trpc-express': re.compile(
            r"from\s+['\"]@trpc/server/adapters/express['\"]|createExpressMiddleware",
            re.MULTILINE,
        ),
        'trpc-fastify': re.compile(
            r"from\s+['\"]@trpc/server/adapters/fastify['\"]|fastifyTRPCPlugin",
            re.MULTILINE,
        ),
        'trpc-next-adapter': re.compile(
            r"from\s+['\"]@trpc/server/adapters/next['\"]|createNextApiHandler",
            re.MULTILINE,
        ),
        'trpc-standalone': re.compile(
            r"from\s+['\"]@trpc/server/adapters/standalone['\"]|createHTTPServer",
            re.MULTILINE,
        ),
        'trpc-ws': re.compile(
            r"from\s+['\"]@trpc/server/adapters/ws['\"]|applyWSSHandler",
            re.MULTILINE,
        ),
        'trpc-fetch': re.compile(
            r"from\s+['\"]@trpc/server/adapters/fetch['\"]|fetchRequestHandler",
            re.MULTILINE,
        ),
        'trpc-lambda': re.compile(
            r"from\s+['\"]@trpc/server/adapters/aws-lambda['\"]|awsLambdaRequestHandler",
            re.MULTILINE,
        ),

        # ── Validation ──────────────────────────────────────────
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|require\(['\"]zod['\"]\)|z\.\w+\(",
            re.MULTILINE,
        ),
        'superjson': re.compile(
            r"from\s+['\"]superjson['\"]|require\(['\"]superjson['\"]\)",
            re.MULTILINE,
        ),
        'yup': re.compile(
            r"from\s+['\"]yup['\"]",
            re.MULTILINE,
        ),
        '@sinclair/typebox': re.compile(
            r"from\s+['\"]@sinclair/typebox['\"]",
            re.MULTILINE,
        ),

        # ── Ecosystem ───────────────────────────────────────────
        'trpc-openapi': re.compile(
            r"from\s+['\"]trpc-openapi['\"]|generateOpenApiDocument|"
            r"createOpenApiExpressMiddleware|createOpenApiNextHandler",
            re.MULTILINE,
        ),
        'trpc-shield': re.compile(
            r"from\s+['\"]trpc-shield['\"]|shield\s*\(",
            re.MULTILINE,
        ),
        'trpc-panel': re.compile(
            r"from\s+['\"]trpc-panel['\"]|renderTrpcPanel",
            re.MULTILINE,
        ),
        'trpc-nuxt': re.compile(
            r"from\s+['\"]trpc-nuxt['\"]|createNuxtApiHandler",
            re.MULTILINE,
        ),

        # ── Database ────────────────────────────────────────────
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient",
            re.MULTILINE,
        ),
        'drizzle': re.compile(
            r"from\s+['\"]drizzle-orm['\"]|drizzle\(",
            re.MULTILINE,
        ),

        # ── React Query / TanStack ──────────────────────────────
        '@tanstack/react-query': re.compile(
            r"from\s+['\"]@tanstack/react-query['\"]|QueryClient",
            re.MULTILINE,
        ),
    }

    # tRPC version detection from features/patterns
    TRPC_VERSION_FEATURES = {
        # v9 features
        'createRouter': '9.0',
        'trpc/server': '9.0',
        # v10 features
        'initTRPC': '10.0',
        't.router': '10.0',
        't.procedure': '10.0',
        't.middleware': '10.0',
        'publicProcedure': '10.0',
        'createTRPCRouter': '10.0',
        'createTRPCProxyClient': '10.0',
        'createTRPCReact': '10.0',
        'createTRPCNext': '10.0',
        'httpBatchLink': '10.0',
        'createCallerFactory': '10.0',
        # v11 features
        'httpBatchStreamLink': '11.0',
        'createTRPCClient': '11.0',
        'experimental_formDataLink': '11.0',
        'experimental_nextHttpLink': '11.0',
    }

    def __init__(self):
        """Initialize the parser with all tRPC extractors."""
        self.router_extractor = TRPCRouterExtractor()
        self.middleware_extractor = TRPCMiddlewareExtractor()
        self.context_extractor = TRPCContextExtractor()
        self.config_extractor = TRPCConfigExtractor()
        self.api_extractor = TRPCApiExtractor()

    def parse(self, content: str, file_path: str = "") -> TRPCParseResult:
        """
        Parse tRPC source code and extract all tRPC-specific information.

        This should be called AFTER the JS/TS parsers have run, when
        tRPC framework is detected. It extracts tRPC-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            TRPCParseResult with all extracted tRPC information
        """
        result = TRPCParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # TypeScript detection
        result.is_typescript = file_path.endswith(('.ts', '.tsx'))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Routers & Procedures ─────────────────────────────────
        router_result = self.router_extractor.extract(content, file_path)
        result.routers = router_result.get('routers', [])
        result.procedures = router_result.get('procedures', [])
        result.merged_routers = router_result.get('merged_routers', [])
        result.total_routers = len(result.routers)
        result.total_procedures = len(result.procedures)

        # ── Middleware ───────────────────────────────────────────
        mw_result = self.middleware_extractor.extract(content, file_path)
        result.middleware = mw_result.get('middleware', [])
        result.middleware_stack = mw_result.get('stack')
        result.total_middleware = len(result.middleware)

        # ── Context & Schemas ────────────────────────────────────
        ctx_result = self.context_extractor.extract(content, file_path)
        result.contexts = ctx_result.get('contexts', [])
        result.inputs = ctx_result.get('inputs', [])
        result.outputs = ctx_result.get('outputs', [])

        # ── Configuration ────────────────────────────────────────
        config_result = self.config_extractor.extract(content, file_path)
        result.adapters = config_result.get('adapters', [])
        result.links = config_result.get('links', [])
        result.config_summary = config_result.get('summary')

        # ── API Patterns ─────────────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.clients = api_result.get('clients', [])
        result.api_summary = api_result.get('summary')

        # ── Version detection ────────────────────────────────────
        result.trpc_version = self._detect_trpc_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a tRPC file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if 'trpc' in basename and ('router' in basename or 'route' in basename):
            return 'router'
        if 'trpc' in basename and 'context' in basename:
            return 'context'
        if 'trpc' in basename and 'client' in basename:
            return 'client'
        if 'trpc' in basename and ('middleware' in basename or 'mw' in basename):
            return 'middleware'
        if 'trpc' in basename:
            return 'config'
        if 'router' in basename:
            return 'router'
        if 'middleware' in basename:
            return 'middleware'
        if 'context' in basename:
            return 'context'
        if 'client' in basename:
            return 'client'
        if 'test' in basename or 'spec' in basename:
            return 'test'

        # By directory conventions
        if '/routers/' in normalized or '/router/' in normalized:
            return 'router'
        if '/server/trpc' in normalized or '/trpc/' in normalized:
            if 'createTRPCRouter' in content or 't.router' in content:
                return 'router'
            if 'createContext' in content or 'createTRPCContext' in content:
                return 'context'
            return 'config'
        if '/api/trpc' in normalized:
            return 'adapter'

        # By content
        if 't.router(' in content or 'createTRPCRouter(' in content or 'createRouter(' in content:
            return 'router'
        if 'createTRPCProxyClient' in content or 'createTRPCReact' in content or 'createTRPCClient' in content:
            return 'client'
        if 'createContext' in content or 'createTRPCContext' in content:
            return 'context'
        if 'createExpressMiddleware' in content or 'createNextApiHandler' in content:
            return 'adapter'
        if 't.middleware(' in content:
            return 'middleware'

        return 'router'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which tRPC ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_trpc_version(self, content: str) -> str:
        """
        Detect the minimum tRPC version required by the file.

        Returns version string (e.g., '11.0', '10.0', '9.0').
        Detection is based on features used in the code.
        """
        max_version = '0.0'

        for feature, version in self.TRPC_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_trpc_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a tRPC-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains tRPC-specific patterns
        """
        # Direct @trpc/* imports
        if re.search(r"from\s+['\"]@trpc/", content):
            return True

        # v9 trpc import
        if re.search(r"from\s+['\"]trpc['\"]|require\(['\"]trpc['\"]\)", content):
            return True

        # initTRPC
        if re.search(r'initTRPC\b', content):
            return True

        # tRPC router/procedure patterns
        if re.search(r'createTRPCRouter|createTRPCProxyClient|createTRPCReact|createTRPCNext|createTRPCClient', content):
            return True

        # t.router / t.procedure / t.middleware
        if re.search(r'\bt\.\s*(?:router|procedure|middleware)\s*\(', content):
            return True

        # publicProcedure / protectedProcedure (common pattern)
        if re.search(r'(?:public|protected|authed|admin)Procedure\s*\.', content):
            return True

        # tRPC adapter patterns
        if re.search(r'createExpressMiddleware|fastifyTRPCPlugin|createNextApiHandler|'
                      r'createHTTPServer|applyWSSHandler|fetchRequestHandler|awsLambdaRequestHandler', content):
            return True

        # httpBatchLink / httpLink / wsLink (client links)
        if re.search(r'httpBatchLink|httpBatchStreamLink|wsLink|splitLink', content):
            return True

        # trpc-openapi
        if re.search(r'trpc-openapi|generateOpenApiDocument', content):
            return True

        # Check file path for tRPC conventions
        if file_path:
            lower_path = file_path.lower()
            if '/trpc/' in lower_path or 'trpc.' in lower_path.split('/')[-1]:
                return True

        return False
