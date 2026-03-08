"""
tRPC API Extractor - Extracts imports, client patterns, and ecosystem integration.

Supports:
- @trpc/server, @trpc/client, @trpc/react-query, @trpc/next imports
- createTRPCProxyClient / createTRPCReact / createTRPCNext
- Type inference: RouterInput, RouterOutput, inferRouterInputs, inferRouterOutputs
- Ecosystem integrations: Next.js, React Query, Prisma, Drizzle, Zod
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TRPCImportInfo:
    """A tRPC-related import statement."""
    module: str
    named_imports: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    import_type: str = ""  # core, client, react, next, adapter, ecosystem


@dataclass
class TRPCClientInfo:
    """A tRPC client creation."""
    name: str
    client_type: str = ""  # proxy, react, next, vanilla
    file: str = ""
    line_number: int = 0
    has_links: bool = False
    has_transformer: bool = False


@dataclass
class TRPCApiSummary:
    """Aggregate API pattern summary."""
    total_imports: int = 0
    has_react_query: bool = False
    has_next_integration: bool = False
    has_type_inference: bool = False
    has_proxy_client: bool = False
    has_vanilla_client: bool = False
    validation_library: str = ""  # zod, yup, superstruct, typebox
    integrations: List[str] = field(default_factory=list)


class TRPCApiExtractor:
    """Extracts tRPC API patterns and ecosystem integration."""

    # tRPC package imports
    TRPC_PACKAGES = {
        '@trpc/server': 'core',
        '@trpc/client': 'client',
        '@trpc/react-query': 'react',
        '@trpc/next': 'next',
        'trpc': 'core',  # v9
        '@trpc/server/adapters/express': 'adapter',
        '@trpc/server/adapters/fastify': 'adapter',
        '@trpc/server/adapters/next': 'adapter',
        '@trpc/server/adapters/standalone': 'adapter',
        '@trpc/server/adapters/ws': 'adapter',
        '@trpc/server/adapters/fetch': 'adapter',
        '@trpc/server/adapters/aws-lambda': 'adapter',
    }

    # Ecosystem packages
    ECOSYSTEM_PACKAGES = {
        'superjson': 'superjson',
        'zod': 'zod',
        'yup': 'yup',
        '@sinclair/typebox': 'typebox',
        'superstruct': 'superstruct',
        'io-ts': 'io-ts',
        '@prisma/client': 'prisma',
        'drizzle-orm': 'drizzle',
        'trpc-openapi': 'openapi',
        'trpc-nuxt': 'nuxt',
        'trpc-shield': 'shield',
        'trpc-panel': 'panel',
        '@tanstack/react-query': 'react-query',
    }

    # Import pattern
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]|"
        r"require\(['\"]([^'\"]+)['\"]\))",
        re.MULTILINE,
    )

    # Client creation patterns
    CLIENT_PATTERNS = {
        'proxy': re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*createTRPCProxyClient\s*<',
            re.MULTILINE,
        ),
        'react': re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*createTRPCReact\s*<',
            re.MULTILINE,
        ),
        'next': re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*createTRPCNext\s*<',
            re.MULTILINE,
        ),
        'vanilla': re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*createTRPCClient\s*<',
            re.MULTILINE,
        ),
    }

    # Type inference patterns
    TYPE_INFERENCE_PATTERN = re.compile(
        r'inferRouterInputs|inferRouterOutputs|RouterInput|RouterOutput|'
        r'inferProcedureInput|inferProcedureOutput',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract tRPC API patterns, imports, and integrations.

        Returns dict with keys: imports, clients, summary
        """
        imports = []
        clients = []
        integrations = set()
        validation_lib = ""

        # ── Imports ─────────────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            named = match.group(1)
            default = match.group(2)
            module = match.group(3) or match.group(4)
            if not module:
                continue

            # Check if it's a tRPC or ecosystem package
            import_type = ""
            for pkg, itype in self.TRPC_PACKAGES.items():
                if module.startswith(pkg) or module == pkg:
                    import_type = itype
                    break

            if not import_type:
                for pkg, eco_name in self.ECOSYSTEM_PACKAGES.items():
                    if module.startswith(pkg) or module == pkg:
                        import_type = 'ecosystem'
                        integrations.add(eco_name)
                        if eco_name in ('zod', 'yup', 'typebox', 'superstruct', 'io-ts'):
                            validation_lib = eco_name
                        break

            if import_type:
                named_imports = []
                if named:
                    named_imports = [n.strip().split(' as ')[0].strip()
                                     for n in named.split(',') if n.strip()]
                elif default:
                    named_imports = [default]

                imports.append(TRPCImportInfo(
                    module=module,
                    named_imports=named_imports[:20],
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    import_type=import_type,
                ))

        # ── Client creations ────────────────────────────────────
        for client_type, pattern in self.CLIENT_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                nearby = content[match.start():match.start() + 500]

                clients.append(TRPCClientInfo(
                    name=name,
                    client_type=client_type,
                    file=file_path,
                    line_number=line_num,
                    has_links='links' in nearby or 'link' in nearby,
                    has_transformer='transformer' in nearby or 'superjson' in nearby,
                ))

        # ── Summary ─────────────────────────────────────────────
        has_react = any(i.import_type == 'react' for i in imports)
        has_next = any(i.import_type == 'next' for i in imports)
        has_type_inf = bool(self.TYPE_INFERENCE_PATTERN.search(content))

        summary = TRPCApiSummary(
            total_imports=len(imports),
            has_react_query=has_react,
            has_next_integration=has_next,
            has_type_inference=has_type_inf,
            has_proxy_client=any(c.client_type == 'proxy' for c in clients),
            has_vanilla_client=any(c.client_type == 'vanilla' for c in clients),
            validation_library=validation_lib,
            integrations=sorted(integrations),
        )

        return {
            'imports': imports,
            'clients': clients,
            'summary': summary,
        }
