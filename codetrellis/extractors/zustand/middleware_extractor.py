"""
Zustand Middleware Extractor for CodeTrellis

Extracts Zustand middleware patterns and configurations:
- persist middleware (storage, partialize, version, migrate)
- devtools middleware (name, enabled, serialize options)
- subscribeWithSelector middleware
- immer middleware (produce integration)
- combine middleware (merging state slices)
- redux middleware (dispatch/action-based pattern)
- Custom middleware (store enhancer pattern)
- Third-party middleware (lens, temporal, broadcast)

Supports:
- Zustand v3 middleware (zustand/middleware direct)
- Zustand v4 middleware (zustand/middleware package, subscribeWithSelector)
- Zustand v5 middleware (same API, enhanced TypeScript, zustand/middleware)
- Third-party: zundo (temporal/undo-redo), zustand-middleware-*
  zustand-persist (v3 community), zustand-computed, zustand-optics

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ZustandPersistInfo:
    """Information about Zustand persist middleware configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    storage_type: str = ""  # localStorage, sessionStorage, AsyncStorage, custom
    storage_name: str = ""  # persist key name
    has_partialize: bool = False
    partialize_fields: List[str] = field(default_factory=list)
    has_version: bool = False
    version: int = 0
    has_migrate: bool = False
    has_merge: bool = False
    has_skip_hydration: bool = False
    has_on_rehydrate_storage: bool = False
    storage_engine: str = ""  # createJSONStorage, custom


@dataclass
class ZustandDevtoolsInfo:
    """Information about Zustand devtools middleware configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    devtools_name: str = ""  # name option for Redux DevTools
    has_enabled: bool = False
    has_serialize: bool = False
    has_anonymousActionType: bool = False


@dataclass
class ZustandCustomMiddlewareInfo:
    """Information about custom or third-party Zustand middleware."""
    name: str
    file: str = ""
    line_number: int = 0
    middleware_type: str = ""  # custom, temporal, broadcast, computed, lens
    is_exported: bool = False


class ZustandMiddlewareExtractor:
    """
    Extracts Zustand middleware patterns from source code.

    Detects:
    - persist() with storage configuration
    - devtools() with naming and options
    - subscribeWithSelector() middleware
    - immer() middleware
    - combine() middleware
    - redux() middleware
    - Custom middleware (StateCreator enhancer pattern)
    - Third-party: zundo/temporal, zustand-computed, zustand-broadcast
    """

    # persist middleware with options
    PERSIST_PATTERN = re.compile(
        r'persist\s*(?:<[^>]*>)?\s*\(\s*'
        r'(?:\([^)]*\)\s*=>\s*(?:\(?\{|create)|'
        r'\w+\s*,\s*\{)',
        re.MULTILINE
    )

    # persist config extraction
    PERSIST_NAME_PATTERN = re.compile(
        r"name\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    PERSIST_STORAGE_PATTERN = re.compile(
        r'storage\s*:\s*(\w+)',
        re.MULTILINE
    )

    PERSIST_PARTIALIZE_PATTERN = re.compile(
        r'partialize\s*:\s*\(\s*state\s*\)\s*=>\s*\(\s*\{([^}]+)\}',
        re.MULTILINE
    )

    PERSIST_VERSION_PATTERN = re.compile(
        r'version\s*:\s*(\d+)',
        re.MULTILINE
    )

    PERSIST_MIGRATE_PATTERN = re.compile(
        r'migrate\s*:\s*(?:\(|async)',
        re.MULTILINE
    )

    PERSIST_MERGE_PATTERN = re.compile(
        r'merge\s*:\s*\(',
        re.MULTILINE
    )

    PERSIST_SKIP_HYDRATION_PATTERN = re.compile(
        r'skipHydration\s*:\s*true',
        re.MULTILINE
    )

    PERSIST_ON_REHYDRATE_PATTERN = re.compile(
        r'onRehydrateStorage\s*:',
        re.MULTILINE
    )

    PERSIST_CREATE_JSON_STORAGE_PATTERN = re.compile(
        r'createJSONStorage\s*\(',
        re.MULTILINE
    )

    # devtools middleware
    DEVTOOLS_PATTERN = re.compile(
        r'devtools\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    DEVTOOLS_NAME_PATTERN = re.compile(
        r"name\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    DEVTOOLS_ENABLED_PATTERN = re.compile(
        r'enabled\s*:\s*',
        re.MULTILINE
    )

    DEVTOOLS_SERIALIZE_PATTERN = re.compile(
        r'serialize\s*:\s*',
        re.MULTILINE
    )

    # subscribeWithSelector middleware
    SUBSCRIBE_WITH_SELECTOR_PATTERN = re.compile(
        r'subscribeWithSelector\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # immer middleware
    IMMER_PATTERN = re.compile(
        r'immer\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # combine middleware
    COMBINE_PATTERN = re.compile(
        r'combine\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # redux middleware
    REDUX_PATTERN = re.compile(
        r'redux\s*(?:<[^>]*>)?\s*\(\s*'
        r'(?:\(\s*state|reducer)',
        re.MULTILINE
    )

    # Custom middleware pattern: const myMiddleware = (config) => (set, get, api) => config(...)
    CUSTOM_MIDDLEWARE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var|function)\s+(\w+)\s*[:=]\s*'
        r'(?:\([^)]*\)\s*=>\s*)?'
        r'\(\s*(?:set|get|api|store|config|f|fn)\s*(?:,\s*(?:set|get|api|store))*\s*\)\s*=>\s*'
        r'(?:config|f|fn)\s*\(',
        re.MULTILINE
    )

    # Third-party middleware patterns
    TEMPORAL_PATTERN = re.compile(
        r"from\s+['\"]zundo['\"]|temporal\s*\(",
        re.MULTILINE
    )

    BROADCAST_PATTERN = re.compile(
        r"from\s+['\"]zustand-broadcast['\"]|broadcast\s*\(",
        re.MULTILINE
    )

    COMPUTED_PATTERN = re.compile(
        r"from\s+['\"]zustand-computed['\"]|computed\s*\(",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Zustand middleware patterns from source code."""
        persist_configs = []
        devtools_configs = []
        custom_middleware = []

        # ── Persist middleware ────────────────────────────────────
        for m in self.PERSIST_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            # Get surrounding context for config extraction
            context_end = min(len(content), m.end() + 800)
            context = content[m.start():context_end]

            name_match = self.PERSIST_NAME_PATTERN.search(context)
            storage_match = self.PERSIST_STORAGE_PATTERN.search(context)
            partialize_match = self.PERSIST_PARTIALIZE_PATTERN.search(context)
            version_match = self.PERSIST_VERSION_PATTERN.search(context)

            partialize_fields = []
            if partialize_match:
                fields_str = partialize_match.group(1)
                partialize_fields = [f.strip().split(':')[0].strip() for f in fields_str.split(',') if f.strip()]

            storage_type = ""
            if storage_match:
                storage_val = storage_match.group(1)
                if 'localStorage' in storage_val:
                    storage_type = "localStorage"
                elif 'sessionStorage' in storage_val:
                    storage_type = "sessionStorage"
                elif 'AsyncStorage' in storage_val:
                    storage_type = "AsyncStorage"
                else:
                    storage_type = storage_val

            persist_configs.append(ZustandPersistInfo(
                name=name_match.group(1) if name_match else "unnamed",
                file=file_path,
                line_number=line,
                storage_type=storage_type,
                storage_name=name_match.group(1) if name_match else "",
                has_partialize=bool(partialize_match),
                partialize_fields=partialize_fields[:15],
                has_version=bool(version_match),
                version=int(version_match.group(1)) if version_match else 0,
                has_migrate=bool(self.PERSIST_MIGRATE_PATTERN.search(context)),
                has_merge=bool(self.PERSIST_MERGE_PATTERN.search(context)),
                has_skip_hydration=bool(self.PERSIST_SKIP_HYDRATION_PATTERN.search(context)),
                has_on_rehydrate_storage=bool(self.PERSIST_ON_REHYDRATE_PATTERN.search(context)),
                storage_engine="createJSONStorage" if self.PERSIST_CREATE_JSON_STORAGE_PATTERN.search(context) else "",
            ))

        # ── Devtools middleware ───────────────────────────────────
        for m in self.DEVTOOLS_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            context_end = min(len(content), m.end() + 400)
            context = content[m.start():context_end]

            name_match = self.DEVTOOLS_NAME_PATTERN.search(context)

            devtools_configs.append(ZustandDevtoolsInfo(
                name=name_match.group(1) if name_match else "unnamed",
                file=file_path,
                line_number=line,
                devtools_name=name_match.group(1) if name_match else "",
                has_enabled=bool(self.DEVTOOLS_ENABLED_PATTERN.search(context)),
                has_serialize=bool(self.DEVTOOLS_SERIALIZE_PATTERN.search(context)),
            ))

        # ── Custom middleware ─────────────────────────────────────
        for m in self.CUSTOM_MIDDLEWARE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            custom_middleware.append(ZustandCustomMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line,
                middleware_type="custom",
                is_exported=is_exported,
            ))

        # ── Third-party middleware ────────────────────────────────
        if self.TEMPORAL_PATTERN.search(content):
            custom_middleware.append(ZustandCustomMiddlewareInfo(
                name="temporal",
                file=file_path,
                line_number=0,
                middleware_type="temporal",
            ))

        if self.BROADCAST_PATTERN.search(content):
            custom_middleware.append(ZustandCustomMiddlewareInfo(
                name="broadcast",
                file=file_path,
                line_number=0,
                middleware_type="broadcast",
            ))

        if self.COMPUTED_PATTERN.search(content):
            custom_middleware.append(ZustandCustomMiddlewareInfo(
                name="computed",
                file=file_path,
                line_number=0,
                middleware_type="computed",
            ))

        return {
            'persist_configs': persist_configs,
            'devtools_configs': devtools_configs,
            'custom_middleware': custom_middleware,
        }
