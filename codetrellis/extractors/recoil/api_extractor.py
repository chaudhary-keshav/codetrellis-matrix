"""
Recoil API Extractor for CodeTrellis

Extracts Recoil API usage patterns:
- Import patterns (recoil, recoil/native, recoil-sync, recoil-relay)
- RecoilRoot configuration (initializeState, override, unstable_extraRoots)
- Snapshot API (snapshot_UNSTABLE, useRecoilSnapshot, useGotoRecoilSnapshot,
                Snapshot methods: getLoadable, getPromise, getInfo_UNSTABLE,
                getNodes_UNSTABLE, map, asyncMap, retain)
- TypeScript types (RecoilState, RecoilValueReadOnly, RecoilLoadable,
                    AtomEffect, SerializableParam, Loadable, DefaultValue,
                    GetRecoilValue, SetRecoilState, ResetRecoilState,
                    CallbackInterface, TransactionInterface_UNSTABLE)
- Ecosystem detection (recoil, recoil-sync, recoil-relay, recoil-nexus,
                        recoil-persist, @recoiljs/refine)

Supports:
- Recoil 0.0.x through 0.7.x+

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecoilImportInfo:
    """Information about a Recoil import statement."""
    module: str
    file: str = ""
    line_number: int = 0
    imports: List[str] = field(default_factory=list)
    is_type_import: bool = False


@dataclass
class RecoilSnapshotUsageInfo:
    """Information about a Recoil Snapshot API usage."""
    name: str
    file: str = ""
    line_number: int = 0
    usage_type: str = ""  # useRecoilSnapshot, useGotoRecoilSnapshot, snapshot_UNSTABLE
    methods_used: List[str] = field(default_factory=list)  # getLoadable, getPromise, map, etc.


@dataclass
class RecoilTypeInfo:
    """Information about a Recoil TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_kind: str = ""  # state_type, loadable_type, effect_type, callback_type, utility_type
    generic_params: str = ""


class RecoilApiExtractor:
    """
    Extracts Recoil API patterns from source code.

    Detects:
    - Import statements from recoil and ecosystem packages
    - RecoilRoot usage and configuration
    - Snapshot API usage
    - TypeScript type imports and usages
    - Ecosystem library integration
    """

    # Import pattern: import { ... } from 'recoil'
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?\{([^}]+)\}\s+from|"
        r"import\s+(\w+)\s+from|"
        r"const\s+\{([^}]+)\}\s*=\s*require\s*\()\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Recoil-related packages
    RECOIL_PACKAGES = {
        'recoil', 'recoil/native', 'recoil-sync', 'recoil-relay',
        'recoil-nexus', 'recoil-persist', '@recoiljs/refine',
        'recoil-sync/url', 'recoil-sync/refine',
    }

    # RecoilRoot: <RecoilRoot initializeState={...} override={...}>
    RECOIL_ROOT_PATTERN = re.compile(
        r'<RecoilRoot\b([^>]*?)(?:/?>)',
        re.DOTALL
    )

    # Snapshot: useRecoilSnapshot(), useGotoRecoilSnapshot(), snapshot_UNSTABLE()
    USE_SNAPSHOT_PATTERN = re.compile(
        r'(?:const\s+)?(\w+)\s*=\s*useRecoilSnapshot\s*\(',
        re.MULTILINE
    )

    GOTO_SNAPSHOT_PATTERN = re.compile(
        r'(?:const\s+)?(\w+)\s*=\s*useGotoRecoilSnapshot\s*\(',
        re.MULTILINE
    )

    SNAPSHOT_UNSTABLE_PATTERN = re.compile(
        r'snapshot_UNSTABLE\s*\(',
        re.MULTILINE
    )

    # Snapshot methods: snapshot.getLoadable(), snapshot.getPromise(), etc.
    SNAPSHOT_METHOD_PATTERN = re.compile(
        r'(\w+)\.(getLoadable|getPromise|getInfo_UNSTABLE|getNodes_UNSTABLE|map|asyncMap|retain)\s*\(',
        re.MULTILINE
    )

    # TypeScript types
    RECOIL_TYPES = {
        'RecoilState': 'state_type',
        'RecoilValueReadOnly': 'state_type',
        'RecoilLoadable': 'loadable_type',
        'Loadable': 'loadable_type',
        'DefaultValue': 'utility_type',
        'AtomEffect': 'effect_type',
        'SerializableParam': 'utility_type',
        'GetRecoilValue': 'callback_type',
        'SetRecoilState': 'callback_type',
        'ResetRecoilState': 'callback_type',
        'CallbackInterface': 'callback_type',
        'TransactionInterface_UNSTABLE': 'callback_type',
        'ReadOnlySelectorOptions': 'utility_type',
        'ReadWriteSelectorOptions': 'utility_type',
        'AtomOptions': 'utility_type',
        'AtomFamilyOptions': 'utility_type',
        'SelectorFamilyOptions': 'utility_type',
    }

    # Recoil-sync API
    RECOIL_SYNC_PATTERNS = {
        'syncEffect': re.compile(r'syncEffect\s*\(', re.MULTILINE),
        'urlSyncEffect': re.compile(r'urlSyncEffect\s*\(', re.MULTILINE),
        'RecoilSync': re.compile(r'<RecoilSync\b', re.MULTILINE),
        'RecoilURLSync': re.compile(r'<RecoilURLSync\b', re.MULTILINE),
        'RecoilURLSyncJSON': re.compile(r'<RecoilURLSyncJSON\b', re.MULTILINE),
        'RecoilURLSyncTransit': re.compile(r'<RecoilURLSyncTransit\b', re.MULTILINE),
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Recoil API patterns from source code."""
        imports = []
        snapshot_usages = []
        types = []

        # ── Imports ────────────────────────────────────────────
        for m in self.IMPORT_PATTERN.finditer(content):
            named_imports = m.group(1) or m.group(3) or ""
            default_import = m.group(2) or ""
            module = m.group(4)

            # Only process recoil-related imports
            if not any(module.startswith(pkg) for pkg in self.RECOIL_PACKAGES):
                if module != 'recoil':
                    continue

            line = content[:m.start()].count('\n') + 1
            is_type_import = 'import type' in content[max(0, m.start() - 15):m.start() + 15]

            imported_names = []
            if named_imports:
                imported_names = [n.strip().split(' as ')[0].strip()
                                  for n in named_imports.split(',')
                                  if n.strip() and n.strip() != 'type']
            if default_import:
                imported_names.append(default_import)

            imports.append(RecoilImportInfo(
                module=module,
                file=file_path,
                line_number=line,
                imports=imported_names[:15],
                is_type_import=is_type_import,
            ))

            # ── Type detection from imports ────────────────────
            for imp_name in imported_names:
                clean_name = imp_name.strip()
                if clean_name in self.RECOIL_TYPES:
                    types.append(RecoilTypeInfo(
                        name=clean_name,
                        file=file_path,
                        line_number=line,
                        type_kind=self.RECOIL_TYPES[clean_name],
                    ))

        # ── Snapshot API ───────────────────────────────────────
        for m in self.USE_SNAPSHOT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Find methods used on this snapshot
            methods = self._find_snapshot_methods(content, name)

            snapshot_usages.append(RecoilSnapshotUsageInfo(
                name=name,
                file=file_path,
                line_number=line,
                usage_type="useRecoilSnapshot",
                methods_used=methods,
            ))

        for m in self.GOTO_SNAPSHOT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            snapshot_usages.append(RecoilSnapshotUsageInfo(
                name=name,
                file=file_path,
                line_number=line,
                usage_type="useGotoRecoilSnapshot",
            ))

        for m in self.SNAPSHOT_UNSTABLE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1

            snapshot_usages.append(RecoilSnapshotUsageInfo(
                name="snapshot_UNSTABLE",
                file=file_path,
                line_number=line,
                usage_type="snapshot_UNSTABLE",
            ))

        # ── RecoilRoot detection ───────────────────────────────
        for m in self.RECOIL_ROOT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            props = m.group(1) or ""

            snapshot_usages.append(RecoilSnapshotUsageInfo(
                name="RecoilRoot",
                file=file_path,
                line_number=line,
                usage_type="RecoilRoot",
                methods_used=[p.strip().split('=')[0].strip()
                              for p in props.split() if '=' in p or p in ('override',)][:5],
            ))

        return {
            'imports': imports,
            'snapshot_usages': snapshot_usages,
            'types': types,
        }

    def _find_snapshot_methods(self, content: str, snapshot_name: str) -> List[str]:
        """Find methods called on a snapshot variable."""
        methods = []
        pattern = re.compile(
            rf'{re.escape(snapshot_name)}\.(getLoadable|getPromise|getInfo_UNSTABLE|getNodes_UNSTABLE|map|asyncMap|retain)\s*\(',
            re.MULTILINE,
        )
        for m in pattern.finditer(content):
            method = m.group(1)
            if method not in methods:
                methods.append(method)
        return methods[:10]
