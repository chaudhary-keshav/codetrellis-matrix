"""
Hono Config Extractor - Extracts Hono application configuration.

Detects:
- new Hono() creation with options
- new Hono({ router: new RegExpRouter() }) router selection
- app.basePath() configuration
- Hono generics: new Hono<{ Bindings: Env }>()
- Export patterns: export default app
- Serve/listen configuration
- Wrangler.toml / wrangler.json bindings
- Multi-runtime entry points
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HonoAppInfo:
    """A Hono application instance."""
    variable_name: str
    base_path: str = ""
    router_type: str = ""  # RegExpRouter, TrieRouter, SmartRouter, etc.
    has_generics: bool = False
    generic_types: str = ""  # e.g. "{ Bindings: Env, Variables: { user: User } }"
    file: str = ""
    line_number: int = 0
    is_exported: bool = False


@dataclass
class HonoServerInfo:
    """A Hono server configuration."""
    file: str = ""
    line_number: int = 0
    port: str = ""
    hostname: str = ""
    runtime: str = ""  # node, bun, deno, cloudflare, etc.
    entry_export: str = ""  # 'default', 'named', 'fetch'


@dataclass
class HonoConfigSummary:
    """Summary of Hono app configuration."""
    total_apps: int = 0
    total_servers: int = 0
    router_type: str = ""
    runtime: str = ""
    has_basepath: bool = False
    has_generics: bool = False


class HonoConfigExtractor:
    """Extracts Hono application configuration from source code."""

    # Hono creation: const app = new Hono()
    APP_CREATION_PATTERNS = [
        # new Hono() or new Hono({ ... })
        re.compile(
            r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+Hono\s*(?:<([^>]+)>)?\s*\(',
        ),
        # export const app = new Hono()
        re.compile(
            r'export\s+(?:const|let|var)\s+(\w+)\s*=\s*new\s+Hono\s*(?:<([^>]+)>)?\s*\(',
        ),
    ]

    # Router type: new Hono({ router: new RegExpRouter() })
    ROUTER_TYPE_PATTERN = re.compile(
        r'new\s+Hono\s*(?:<[^>]+>)?\s*\(\s*\{[^}]*router\s*:\s*new\s+(\w+Router)\s*\(',
    )

    # basePath: app.basePath('/api') or new Hono().basePath('/api')
    BASEPATH_PATTERN = re.compile(
        r'\.basePath\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\)',
    )

    # Export default: export default app
    EXPORT_DEFAULT_PATTERN = re.compile(
        r'export\s+default\s+(\w+)',
    )

    # Node.js serve: serve({ fetch: app.fetch, port: 3000 })
    NODE_SERVE_PATTERN = re.compile(
        r'serve\s*\(\s*(?:\{[^}]*port\s*:\s*(\d+)|app)',
    )

    # Bun.serve: export default { port: 3000, fetch: app.fetch }
    BUN_SERVE_PATTERN = re.compile(
        r'export\s+default\s+\{[^}]*port\s*:\s*(\d+)',
    )

    # Deno.serve: Deno.serve(app.fetch) or Deno.serve({ port: 3000 }, app.fetch)
    DENO_SERVE_PATTERN = re.compile(
        r'Deno\.serve\s*\(',
    )

    # Listen pattern: app.listen(3000)
    LISTEN_PATTERN = re.compile(
        r'(\w+)\s*\.\s*listen\s*\(\s*(?:(\d+)|(\w+))',
    )

    # Wrangler config detection
    WRANGLER_PATTERN = re.compile(
        r'wrangler\.toml|wrangler\.json|wrangler\.jsonc',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hono configuration from source code."""
        apps: List[HonoAppInfo] = []
        servers: List[HonoServerInfo] = []

        # Detect router type globally
        router_type = ""
        rt_match = self.ROUTER_TYPE_PATTERN.search(content)
        if rt_match:
            router_type = rt_match.group(1)

        # basePath detection
        base_path = ""
        bp_match = self.BASEPATH_PATTERN.search(content)
        if bp_match:
            base_path = bp_match.group(1)

        # Export default
        exported_name = ""
        export_match = self.EXPORT_DEFAULT_PATTERN.search(content)
        if export_match:
            exported_name = export_match.group(1)

        # App creation
        for pattern in self.APP_CREATION_PATTERNS:
            for match in pattern.finditer(content):
                var_name = match.group(1)
                generic_types = match.group(2) or ''
                line_num = content[:match.start()].count('\n') + 1
                is_exported = 'export' in content[max(0, match.start()-20):match.start()] \
                    or var_name == exported_name

                apps.append(HonoAppInfo(
                    variable_name=var_name,
                    base_path=base_path,
                    router_type=router_type,
                    has_generics=bool(generic_types),
                    generic_types=generic_types,
                    file=file_path,
                    line_number=line_num,
                    is_exported=is_exported,
                ))

        # Server/serve detection
        runtime = ''

        # Node.js @hono/node-server
        node_match = self.NODE_SERVE_PATTERN.search(content)
        if node_match:
            runtime = 'node'
            port = node_match.group(1) or ''
            line_num = content[:node_match.start()].count('\n') + 1
            servers.append(HonoServerInfo(
                file=file_path,
                line_number=line_num,
                port=port,
                runtime='node',
                entry_export='named',
            ))

        # Bun
        bun_match = self.BUN_SERVE_PATTERN.search(content)
        if bun_match:
            runtime = 'bun'
            port = bun_match.group(1) or ''
            line_num = content[:bun_match.start()].count('\n') + 1
            servers.append(HonoServerInfo(
                file=file_path,
                line_number=line_num,
                port=port,
                runtime='bun',
                entry_export='default',
            ))

        # Deno
        if self.DENO_SERVE_PATTERN.search(content):
            runtime = 'deno'
            servers.append(HonoServerInfo(
                file=file_path,
                runtime='deno',
                entry_export='named',
            ))

        # Cloudflare Workers: export default app
        if not runtime and exported_name:
            # If there's an export default and no other runtime detected,
            # it's likely Cloudflare Workers or a generic export
            if 'c.env' in content or 'executionCtx' in content:
                runtime = 'cloudflare-workers'
                servers.append(HonoServerInfo(
                    file=file_path,
                    runtime='cloudflare-workers',
                    entry_export='default',
                ))

        # Generic listen
        for match in self.LISTEN_PATTERN.finditer(content):
            port = match.group(2) or match.group(3) or ''
            line_num = content[:match.start()].count('\n') + 1
            if not any(s.line_number == line_num for s in servers):
                servers.append(HonoServerInfo(
                    file=file_path,
                    line_number=line_num,
                    port=port,
                    runtime=runtime or 'node',
                ))

        summary = HonoConfigSummary(
            total_apps=len(apps),
            total_servers=len(servers),
            router_type=router_type,
            runtime=runtime,
            has_basepath=bool(base_path),
            has_generics=any(a.has_generics for a in apps),
        )

        return {
            'apps': apps,
            'servers': servers,
            'summary': summary,
        }
