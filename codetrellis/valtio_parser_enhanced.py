"""
EnhancedValtioParser v1.0 - Comprehensive Valtio parser using all extractors.

This parser integrates all Valtio extractors to provide complete parsing of
Valtio proxy-based state management usage across React/TypeScript/JavaScript
source files. It runs as a supplementary layer on top of the JavaScript/
TypeScript/React parsers, extracting Valtio-specific semantics.

Supports:
- Valtio v1.x (proxy, useSnapshot, subscribe from 'valtio', utils from 'valtio/utils',
                derive, underive, addComputed, proxyWithComputed — now deprecated)
- Valtio v2.x (React 18+ useSyncExternalStore, valtio/vanilla subpath,
                valtio/react subpath, valtio/vanilla/utils,
                unstable_enableOp, unstable_deepProxy,
                isProxyMap, isProxySet, getVersion,
                watch deprecated in v2.3.0)

Core Patterns:
- proxy() state definitions with mutable state model
- useSnapshot() for React component subscriptions (auto-tracking)
- subscribe() for listening to state changes (vanilla + React)
- snapshot() for immutable state access (vanilla)
- ref() to hold non-proxy values (DOM refs, class instances)
- Direct mutations (state.field = value) — the Valtio way

Utility Patterns:
- subscribeKey() for primitive key subscription
- watch() reactive effects (deprecated v2.3.0+)
- devtools() Redux DevTools integration
- deepClone() for deep state cloning
- proxyMap() and proxySet() for Map/Set-like proxy collections
- useProxy() convenience hook (experimental)

Ecosystem Integration Detection:
- Core: valtio, valtio/vanilla, valtio/utils, valtio/vanilla/utils, valtio/react
- Ecosystem: derive-valtio, valtio-reactive, use-valtio, eslint-plugin-valtio
- Integration: proxy-compare, React, Next.js
- Deprecated: derive/underive → derive-valtio, watch → valtio-reactive,
              proxyWithComputed → native getters

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Valtio extractors
from .extractors.valtio import (
    ValtioProxyExtractor, ValtioProxyInfo, ValtioRefInfo, ValtioProxyCollectionInfo,
    ValtioSnapshotExtractor, ValtioSnapshotUsageInfo, ValtioUseProxyInfo,
    ValtioSubscriptionExtractor, ValtioSubscribeInfo, ValtioSubscribeKeyInfo, ValtioWatchInfo,
    ValtioActionExtractor, ValtioActionInfo, ValtioDevtoolsInfo,
    ValtioApiExtractor, ValtioImportInfo, ValtioIntegrationInfo, ValtioTypeInfo,
)


@dataclass
class ValtioParseResult:
    """Complete parse result for a file with Valtio usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js

    # Proxy
    proxies: List[ValtioProxyInfo] = field(default_factory=list)
    refs: List[ValtioRefInfo] = field(default_factory=list)
    collections: List[ValtioProxyCollectionInfo] = field(default_factory=list)

    # Snapshot
    snapshots: List[ValtioSnapshotUsageInfo] = field(default_factory=list)
    use_proxies: List[ValtioUseProxyInfo] = field(default_factory=list)

    # Subscription
    subscribes: List[ValtioSubscribeInfo] = field(default_factory=list)
    subscribe_keys: List[ValtioSubscribeKeyInfo] = field(default_factory=list)
    watches: List[ValtioWatchInfo] = field(default_factory=list)

    # Action
    actions: List[ValtioActionInfo] = field(default_factory=list)
    devtools_configs: List[ValtioDevtoolsInfo] = field(default_factory=list)

    # API
    imports: List[ValtioImportInfo] = field(default_factory=list)
    integrations: List[ValtioIntegrationInfo] = field(default_factory=list)
    types: List[ValtioTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    valtio_version: str = ""  # v1, v2, unknown
    deprecated_apis: List[str] = field(default_factory=list)


class EnhancedValtioParser:
    """
    Enhanced Valtio parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript/React parser
    when Valtio framework is detected. It extracts Valtio-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 10+ Valtio ecosystem libraries across:
    - Core (valtio, valtio/vanilla, valtio/react)
    - Utilities (valtio/utils, valtio/vanilla/utils)
    - Ecosystem (derive-valtio, valtio-reactive, use-valtio)
    - Tools (eslint-plugin-valtio, proxy-compare)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Valtio ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'valtio': re.compile(
            r"from\s+['\"]valtio['\"]|require\(['\"]valtio['\"]\)",
            re.MULTILINE
        ),
        'valtio-vanilla': re.compile(
            r"from\s+['\"]valtio/vanilla['\"]|"
            r"from\s+['\"]valtio/vanilla/utils['\"]",
            re.MULTILINE
        ),
        'valtio-react': re.compile(
            r"from\s+['\"]valtio/react['\"]|"
            r"from\s+['\"]valtio/react/utils['\"]",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'valtio-utils': re.compile(
            r"from\s+['\"]valtio/utils['\"]|"
            r"from\s+['\"]valtio/vanilla/utils['\"]",
            re.MULTILINE
        ),

        # ── Ecosystem ────────────────────────────────────────────
        'derive-valtio': re.compile(
            r"from\s+['\"]derive-valtio['\"]|require\(['\"]derive-valtio['\"]\)",
            re.MULTILINE
        ),
        'valtio-reactive': re.compile(
            r"from\s+['\"]valtio-reactive['\"]|require\(['\"]valtio-reactive['\"]\)",
            re.MULTILINE
        ),
        'use-valtio': re.compile(
            r"from\s+['\"]use-valtio['\"]|require\(['\"]use-valtio['\"]\)",
            re.MULTILINE
        ),
        'eslint-plugin-valtio': re.compile(
            r"eslint-plugin-valtio|valtio/recommended",
            re.MULTILINE
        ),
        'proxy-compare': re.compile(
            r"from\s+['\"]proxy-compare['\"]|require\(['\"]proxy-compare['\"]\)",
            re.MULTILINE
        ),

        # ── Integration ──────────────────────────────────────────
        'react': re.compile(
            r"from\s+['\"]react['\"]|useSnapshot\s*\(",
            re.MULTILINE
        ),
        'next': re.compile(
            r"from\s+['\"]next|'use client'|\"use client\"",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'proxy': re.compile(r'proxy\s*\(', re.MULTILINE),
        'useSnapshot': re.compile(r'useSnapshot\s*\(', re.MULTILINE),
        'subscribe': re.compile(r'(?<!\w)subscribe\s*\(', re.MULTILINE),
        'snapshot': re.compile(r'(?<!\w)snapshot\s*\(', re.MULTILINE),
        'ref': re.compile(r'ref\s*\(', re.MULTILINE),
        'subscribeKey': re.compile(r'subscribeKey\s*\(', re.MULTILINE),
        'watch': re.compile(r'watch\s*\(\s*\(', re.MULTILINE),
        'devtools': re.compile(r'devtools\s*\(', re.MULTILINE),
        'proxyMap': re.compile(r'proxyMap\s*\(', re.MULTILINE),
        'proxySet': re.compile(r'proxySet\s*\(', re.MULTILINE),
        'useProxy': re.compile(r'useProxy\s*\(', re.MULTILINE),
        'deepClone': re.compile(r'deepClone\s*\(', re.MULTILINE),
        'getVersion': re.compile(r'getVersion\s*\(', re.MULTILINE),
        'deepProxy': re.compile(r'unstable_deepProxy\s*\(', re.MULTILINE),
        'enableOp': re.compile(r'unstable_enableOp\s*\(', re.MULTILINE),
        'derive': re.compile(r'derive\s*\(', re.MULTILINE),
        'underive': re.compile(r'underive\s*\(', re.MULTILINE),
        'proxyWithComputed': re.compile(r'proxyWithComputed\s*\(', re.MULTILINE),
        'computed_getters': re.compile(r'get\s+\w+\s*\(\s*\)\s*\{', re.MULTILINE),
        'direct_mutation': re.compile(r'\w+\.\w+\s*=\s*', re.MULTILINE),
    }

    def __init__(self) -> None:
        """Initialize all Valtio extractors."""
        self.proxy_extractor = ValtioProxyExtractor()
        self.snapshot_extractor = ValtioSnapshotExtractor()
        self.subscription_extractor = ValtioSubscriptionExtractor()
        self.action_extractor = ValtioActionExtractor()
        self.api_extractor = ValtioApiExtractor()

    def is_valtio_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Valtio code.

        Returns True if the file imports from Valtio ecosystem
        or uses Valtio patterns (proxy, useSnapshot, etc.)
        """
        valtio_indicators = [
            'valtio', 'proxy(', 'useSnapshot(',
            "from 'valtio", 'from "valtio',
            "from 'valtio/", 'from "valtio/',
            'valtio/vanilla', 'valtio/utils',
            'valtio/react', 'derive-valtio',
            'valtio-reactive', 'use-valtio',
            'proxy-compare',
        ]
        return any(ind in content for ind in valtio_indicators)

    def parse(self, content: str, file_path: str = "") -> ValtioParseResult:
        """
        Parse a source file for Valtio patterns.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            ValtioParseResult with all extracted information.
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith(('.js', '.mjs', '.cjs')):
            file_type = "js"

        result = ValtioParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)

        # ── API extraction (run first for version + known proxies) ─
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
            result.valtio_version = api_result.get('detected_version', '')
            result.deprecated_apis = api_result.get('deprecated_apis', [])
        except Exception:
            pass

        # ── Proxy extraction ───────────────────────────────────────
        try:
            proxy_result = self.proxy_extractor.extract(content, file_path)
            result.proxies = proxy_result.get('proxies', [])
            result.refs = proxy_result.get('refs', [])
            result.collections = proxy_result.get('collections', [])
        except Exception:
            pass

        # Build known proxy names for action extractor context
        known_proxies = [p.name for p in result.proxies if p.name]

        # ── Snapshot extraction ────────────────────────────────────
        try:
            snap_result = self.snapshot_extractor.extract(content, file_path)
            result.snapshots = snap_result.get('snapshots', [])
            result.use_proxies = snap_result.get('use_proxies', [])
        except Exception:
            pass

        # ── Subscription extraction ────────────────────────────────
        try:
            sub_result = self.subscription_extractor.extract(content, file_path)
            result.subscribes = sub_result.get('subscribes', [])
            result.subscribe_keys = sub_result.get('subscribe_keys', [])
            result.watches = sub_result.get('watches', [])
        except Exception:
            pass

        # ── Action extraction ─────────────────────────────────────
        try:
            action_result = self.action_extractor.extract(
                content, file_path, known_proxies=known_proxies,
            )
            result.actions = action_result.get('actions', [])
            result.devtools_configs = action_result.get('devtools', [])
        except Exception:
            pass

        # ── Version detection (merge with API extractor) ──────────
        if not result.valtio_version:
            result.valtio_version = self._detect_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Valtio ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Valtio features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Valtio version based on API usage patterns.

        Returns:
            - 'v2' if Valtio v2+ patterns detected (vanilla/react subpaths, unstable_ APIs)
            - 'v1' if Valtio v1 patterns detected (derive from valtio/utils, proxyWithComputed)
            - 'unknown' if insufficient signals
        """
        v2_signals = 0
        v1_signals = 0

        # v2 indicators: subpath exports, unstable APIs, isProxy* helpers
        v2_checks = [
            (r"from\s+['\"]valtio/vanilla", 2),
            (r"from\s+['\"]valtio/react", 2),
            (r"unstable_(?:enableOp|deepProxy|getInternalStates)", 1),
            (r"isProxy(?:Map|Set)\s*\(", 1),
        ]
        for pattern, weight in v2_checks:
            if re.search(pattern, content):
                v2_signals += weight

        # v1 indicators: deprecated APIs from valtio/utils
        v1_checks = [
            (r"from\s+['\"]valtio/utils['\"].*(?:derive|underive|proxyWithComputed)", 2),
            (r"proxyWithComputed\s*\(", 1),
            (r"addComputed\s*\(", 1),
        ]
        for pattern, weight in v1_checks:
            if re.search(pattern, content):
                v1_signals += weight

        if v2_signals > 0 and v2_signals > v1_signals:
            return 'v2'
        if v1_signals > 0:
            return 'v1'
        return 'unknown'

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {'': 0, 'unknown': 0, 'v1': 1, 'v2': 2}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
