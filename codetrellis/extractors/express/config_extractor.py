"""
Express.js Config Extractor - Extracts Express application configuration patterns.

Supports:
- express() app creation
- app.set() settings (views, view engine, port, trust proxy, etc.)
- app.enable() / app.disable()
- app.engine() template engine registration
- Environment-based configuration
- Express 3.x/4.x/5.x configuration differences
- Cluster/worker setup
- HTTPS/SSL configuration
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExpressSettingInfo:
    """A single Express app setting."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    setting_type: str = ""  # set, enable, disable, engine
    is_env_based: bool = False


@dataclass
class ExpressAppInfo:
    """Express application instance information."""
    variable_name: str = "app"
    file: str = ""
    line_number: int = 0
    is_exported: bool = False
    creation_style: str = ""  # express(), new Express(), factory


@dataclass
class ExpressServerInfo:
    """Express server listener information."""
    file: str = ""
    line_number: int = 0
    port: str = ""
    host: str = ""
    is_https: bool = False
    uses_cluster: bool = False
    has_callback: bool = False


@dataclass
class ExpressConfigSummary:
    """Summary of Express configuration."""
    total_settings: int = 0
    view_engine: str = ""
    has_trust_proxy: bool = False
    has_static_files: bool = False
    has_template_engine: bool = False
    has_cors_config: bool = False
    has_https: bool = False
    has_cluster: bool = False
    port: str = ""
    env_mode: str = ""  # development, production, etc.


class ExpressConfigExtractor:
    """Extracts Express.js configuration information from source code."""

    # app.set() pattern
    SET_PATTERN = re.compile(
        r'(\w+)\s*\.\s*set\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*([^)]+)\)'
    )

    # app.enable() / app.disable()
    ENABLE_DISABLE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(enable|disable)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)'
    )

    # app.engine()
    ENGINE_PATTERN = re.compile(
        r'(\w+)\s*\.\s*engine\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(\w+)'
    )

    # express() creation
    APP_CREATION_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:express|require\s*\(\s*[\'"`]express[\'"`]\s*\))\s*\(\s*\)'
    )

    # .listen()
    LISTEN_PATTERN = re.compile(
        r'(\w+)\s*\.\s*listen\s*\(\s*([^,)]+)'
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract configuration information from Express.js source code."""
        settings: List[ExpressSettingInfo] = []
        apps: List[ExpressAppInfo] = []
        servers: List[ExpressServerInfo] = []
        lines = content.split('\n')

        uses_cluster = 'cluster' in content and ('fork' in content or 'isMaster' in content or 'isPrimary' in content)
        uses_https = 'https.createServer' in content or 'https.Server' in content

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Express app creation
            app_match = self.APP_CREATION_PATTERN.search(stripped)
            if app_match:
                var_name = app_match.group(1)
                apps.append(ExpressAppInfo(
                    variable_name=var_name,
                    file=file_path,
                    line_number=i,
                    is_exported=self._is_exported(content, var_name),
                    creation_style='express()',
                ))

            # app.set()
            set_match = self.SET_PATTERN.search(stripped)
            if set_match:
                settings.append(ExpressSettingInfo(
                    name=set_match.group(2),
                    value=set_match.group(3).strip().strip("'\"` "),
                    file=file_path,
                    line_number=i,
                    setting_type='set',
                    is_env_based='process.env' in stripped,
                ))

            # app.enable() / app.disable()
            ed_match = self.ENABLE_DISABLE_PATTERN.search(stripped)
            if ed_match:
                settings.append(ExpressSettingInfo(
                    name=ed_match.group(3),
                    value='true' if ed_match.group(2) == 'enable' else 'false',
                    file=file_path,
                    line_number=i,
                    setting_type=ed_match.group(2),
                    is_env_based='process.env' in stripped,
                ))

            # app.engine()
            engine_match = self.ENGINE_PATTERN.search(stripped)
            if engine_match:
                settings.append(ExpressSettingInfo(
                    name=f'engine:{engine_match.group(2)}',
                    value=engine_match.group(3),
                    file=file_path,
                    line_number=i,
                    setting_type='engine',
                ))

            # .listen()
            listen_match = self.LISTEN_PATTERN.search(stripped)
            if listen_match and listen_match.group(1) not in ('socket', 'io', 'ws', 'wss'):
                port_val = listen_match.group(2).strip()
                servers.append(ExpressServerInfo(
                    file=file_path,
                    line_number=i,
                    port=port_val,
                    host=self._extract_host(stripped),
                    is_https=uses_https,
                    uses_cluster=uses_cluster,
                    has_callback='function' in stripped or '=>' in stripped or '),' in stripped,
                ))

        # Build summary
        summary = self._build_summary(settings, servers, uses_https, uses_cluster)

        return {
            "settings": settings,
            "apps": apps,
            "servers": servers,
            "summary": summary,
        }

    def _is_exported(self, content: str, var_name: str) -> bool:
        """Check if a variable is exported."""
        patterns = [
            f'module.exports = {var_name}',
            f'module.exports.{var_name}',
            f'exports.{var_name}',
            f'export default {var_name}',
            f'export {{ {var_name}',
        ]
        return any(p in content for p in patterns)

    def _extract_host(self, line: str) -> str:
        """Extract host from listen call."""
        # .listen(port, 'host', callback)
        match = re.search(r'\.listen\s*\([^,]+,\s*[\'"`]([^\'"`]+)[\'"`]', line)
        return match.group(1) if match else ''

    def _build_summary(
        self,
        settings: List[ExpressSettingInfo],
        servers: List[ExpressServerInfo],
        uses_https: bool,
        uses_cluster: bool,
    ) -> ExpressConfigSummary:
        """Build configuration summary."""
        summary = ExpressConfigSummary()
        summary.total_settings = len(settings)
        summary.has_https = uses_https
        summary.has_cluster = uses_cluster

        for s in settings:
            if s.name == 'view engine':
                summary.view_engine = s.value
                summary.has_template_engine = True
            elif s.name == 'trust proxy':
                summary.has_trust_proxy = True
            elif s.name == 'port':
                summary.port = s.value

        for srv in servers:
            if srv.port and not summary.port:
                summary.port = srv.port

        return summary
