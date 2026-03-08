"""
Koa Config Extractor - Extracts Koa application configuration.

Detects:
- new Koa() creation
- app.keys = [] (for signed cookies)
- app.proxy = true (trust proxy)
- app.subdomainOffset
- app.env
- app.silent
- app.listen() calls with port/host
- app.on('error', handler) error event listeners
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KoaAppInfo:
    """A Koa application instance."""
    variable_name: str
    file: str = ""
    line_number: int = 0
    is_exported: bool = False


@dataclass
class KoaServerInfo:
    """A Koa server listen() call."""
    file: str = ""
    line_number: int = 0
    port: str = ""
    host: str = ""
    is_https: bool = False
    uses_cluster: bool = False


@dataclass
class KoaSettingInfo:
    """A Koa app configuration setting."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    setting_type: str = ""  # 'keys', 'proxy', 'subdomainOffset', 'env', 'silent'
    is_env_based: bool = False


@dataclass
class KoaConfigSummary:
    """Summary of Koa app configuration."""
    total_apps: int = 0
    total_servers: int = 0
    has_proxy: bool = False
    has_keys: bool = False
    has_error_listener: bool = False


class KoaConfigExtractor:
    """Extracts Koa application configuration from source code."""

    # Koa app creation: const app = new Koa()
    APP_CREATION_PATTERNS = [
        re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*new\s+Koa\s*\('),
        re.compile(r'export\s+(?:const|let|var)\s+(\w+)\s*=\s*new\s+Koa\s*\('),
    ]

    # Settings: app.keys = [...], app.proxy = true, etc.
    SETTING_PATTERNS = [
        (re.compile(r'(\w+)\s*\.\s*keys\s*=\s*(\[.{1,200}\])'), 'keys'),
        (re.compile(r'(\w+)\s*\.\s*proxy\s*=\s*(true|false)'), 'proxy'),
        (re.compile(r'(\w+)\s*\.\s*subdomainOffset\s*=\s*(\d+)'), 'subdomainOffset'),
        (re.compile(r'(\w+)\s*\.\s*env\s*=\s*[\'"`](\w+)[\'"`]'), 'env'),
        (re.compile(r'(\w+)\s*\.\s*silent\s*=\s*(true|false)'), 'silent'),
    ]

    # Listen pattern: app.listen(port, host?)
    LISTEN_PATTERN = re.compile(
        r'(\w+)\s*\.\s*listen\s*\(\s*'
        r'(?:(\d+)|(\w+(?:\.\w+)*)|process\.env\.(\w+))',
    )

    # Error listener: app.on('error', handler)
    ERROR_LISTENER_PATTERN = re.compile(
        r'(\w+)\s*\.\s*on\s*\(\s*[\'"`]error[\'"`]',
    )

    # HTTPS detection
    HTTPS_PATTERN = re.compile(
        r'https\.createServer|http2\.createServer|http2\.createSecureServer',
    )

    # Cluster detection
    CLUSTER_PATTERN = re.compile(
        r'cluster\.fork|cluster\.isMaster|cluster\.isPrimary',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Koa configuration from source code."""
        apps: List[KoaAppInfo] = []
        servers: List[KoaServerInfo] = []
        settings: List[KoaSettingInfo] = []
        has_error_listener = False

        # App creation
        for pattern in self.APP_CREATION_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                is_exported = 'export' in content[max(0, match.start()-20):match.start()]
                apps.append(KoaAppInfo(
                    variable_name=match.group(1),
                    file=file_path,
                    line_number=line_num,
                    is_exported=is_exported,
                ))

        # Settings
        for pattern, setting_type in self.SETTING_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                value = match.group(2)
                is_env = 'process.env' in value if value else False
                settings.append(KoaSettingInfo(
                    name=setting_type,
                    value=value,
                    file=file_path,
                    line_number=line_num,
                    setting_type=setting_type,
                    is_env_based=is_env,
                ))

        # Listen calls
        is_https = bool(self.HTTPS_PATTERN.search(content))
        uses_cluster = bool(self.CLUSTER_PATTERN.search(content))
        for match in self.LISTEN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            port = match.group(2) or match.group(3) or match.group(4) or ''
            is_env = bool(match.group(4)) or 'process.env' in (match.group(3) or '')
            servers.append(KoaServerInfo(
                file=file_path,
                line_number=line_num,
                port=port,
                is_https=is_https,
                uses_cluster=uses_cluster,
            ))

        # Error listeners
        if self.ERROR_LISTENER_PATTERN.search(content):
            has_error_listener = True

        summary = KoaConfigSummary(
            total_apps=len(apps),
            total_servers=len(servers),
            has_proxy=any(s.setting_type == 'proxy' for s in settings),
            has_keys=any(s.setting_type == 'keys' for s in settings),
            has_error_listener=has_error_listener,
        )

        return {
            'apps': apps,
            'servers': servers,
            'settings': settings,
            'summary': summary,
            'has_error_listener': has_error_listener,
        }
