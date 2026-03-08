"""
Jotai Middleware Extractor for CodeTrellis

Extracts Jotai middleware and extension patterns:
- atomWithStorage (jotai/utils) — localStorage, sessionStorage, AsyncStorage
- atomWithObservable (jotai/utils) — RxJS Observable integration
- atomWithMachine (jotai-xstate) — XState state machine atoms
- atomEffect (jotai-effect) — side-effect atoms
- atom.onMount — mount/unmount lifecycle
- atomWithProxy (jotai-valtio) — Valtio proxy integration
- atomWithImmer (jotai-immer) — Immer immutable updates
- atomWithLocation (jotai-location) — URL state sync
- atomWithHash (jotai-location) — URL hash sync
- atomWithBroadcast — BroadcastChannel cross-tab sync
- atomWithRefresh (jotai/utils) — refetchable async atoms

Supports:
- Jotai v1.x (atomWithStorage, onMount)
- Jotai v2.x (improved storage API, SyncStringStorage, AsyncStringStorage)

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JotaiStorageAtomInfo:
    """Information about a Jotai storage atom (atomWithStorage)."""
    name: str
    file: str = ""
    line_number: int = 0
    storage_key: str = ""  # localStorage key string
    storage_type: str = ""  # localStorage, sessionStorage, AsyncStorage, custom
    initial_value: str = ""
    has_typescript: bool = False
    type_annotation: str = ""
    has_custom_serializer: bool = False
    has_subscribe: bool = False  # v2 storage subscribe
    is_exported: bool = False


@dataclass
class JotaiEffectInfo:
    """Information about a Jotai effect (atomEffect or onMount)."""
    name: str
    file: str = ""
    line_number: int = 0
    effect_type: str = ""  # onMount, atomEffect, effect
    has_cleanup: bool = False  # returns cleanup function
    source_atom: str = ""  # atom the effect is attached to
    is_exported: bool = False


@dataclass
class JotaiMachineAtomInfo:
    """Information about a Jotai machine atom (jotai-xstate)."""
    name: str
    file: str = ""
    line_number: int = 0
    machine_name: str = ""
    has_typescript: bool = False
    is_exported: bool = False


class JotaiMiddlewareExtractor:
    """
    Extracts Jotai middleware/extension patterns from source code.

    Detects:
    - atomWithStorage calls with key + storage type
    - atomWithObservable for RxJS integration
    - atomWithMachine for XState integration
    - atomEffect for side effects
    - atom.onMount lifecycle
    - atomWithProxy for Valtio integration
    - atomWithImmer for Immer integration
    - atomWithLocation / atomWithHash for URL state
    - atomWithRefresh for refetchable async atoms
    - atomWithBroadcast for cross-tab sync
    """

    # atomWithStorage: const xAtom = atomWithStorage('key', defaultValue)
    ATOM_WITH_STORAGE_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"atomWithStorage\s*(?:<([^>]*)>)?\s*\(\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # atomWithObservable: const xAtom = atomWithObservable((get) => observable$)
    ATOM_WITH_OBSERVABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithObservable\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # atomWithMachine: const xAtom = atomWithMachine(machine)
    ATOM_WITH_MACHINE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithMachine\s*(?:<[^>]*>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # atomEffect: const xEffect = atomEffect((get, set) => { ... })
    ATOM_EFFECT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomEffect\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # atom.onMount: xAtom.onMount = (setAtom) => { ... }
    ON_MOUNT_PATTERN = re.compile(
        r'(\w+)\.onMount\s*=\s*\(',
        re.MULTILINE
    )

    # atomWithProxy: const xAtom = atomWithProxy(proxyState)
    ATOM_WITH_PROXY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithProxy\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # atomWithImmer: const xAtom = atomWithImmer(initialValue)
    ATOM_WITH_IMMER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithImmer\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # atomWithLocation: const locationAtom = atomWithLocation()
    ATOM_WITH_LOCATION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithLocation\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # atomWithHash: const hashAtom = atomWithHash('key', defaultValue)
    ATOM_WITH_HASH_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*"
        r"atomWithHash\s*(?:<[^>]*>)?\s*\(\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # atomWithRefresh: const xAtom = atomWithRefresh((get) => fetch(...))
    ATOM_WITH_REFRESH_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'atomWithRefresh\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Custom storage detection
    CUSTOM_STORAGE_PATTERN = re.compile(
        r'createJSONStorage\s*\(|'
        r'AsyncStorage|sessionStorage|'
        r'getItem|setItem|removeItem',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Jotai middleware patterns from source code."""
        storage_atoms = []
        effects = []
        machine_atoms = []

        # ── atomWithStorage ──────────────────────────────────────
        for m in self.ATOM_WITH_STORAGE_PATTERN.finditer(content):
            name = m.group(1)
            ts_type = m.group(2) or ""
            key = m.group(3)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Detect storage type
            ctx = content[m.start():min(len(content), m.start() + 300)]
            storage_type = "localStorage"
            if 'sessionStorage' in ctx:
                storage_type = "sessionStorage"
            elif 'AsyncStorage' in ctx:
                storage_type = "AsyncStorage"
            elif 'createJSONStorage' in ctx:
                storage_type = "custom"

            has_custom_ser = 'serialize' in ctx or 'deserialize' in ctx
            has_subscribe = 'subscribe' in ctx

            storage_atoms.append(JotaiStorageAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                storage_key=key,
                storage_type=storage_type,
                has_typescript=bool(ts_type),
                type_annotation=ts_type,
                has_custom_serializer=has_custom_ser,
                has_subscribe=has_subscribe,
                is_exported=is_exported,
            ))

        # ── atomEffect ──────────────────────────────────────────
        for m in self.ATOM_EFFECT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            ctx = content[m.start():min(len(content), m.start() + 300)]
            has_cleanup = 'return' in ctx and ('() =>' in ctx[ctx.find('return'):] or 'cleanup' in ctx)

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="atomEffect",
                has_cleanup=has_cleanup,
                is_exported=is_exported,
            ))

        # ── atom.onMount ────────────────────────────────────────
        for m in self.ON_MOUNT_PATTERN.finditer(content):
            atom_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            ctx = content[m.start():min(len(content), m.start() + 200)]
            has_cleanup = 'return' in ctx

            effects.append(JotaiEffectInfo(
                name=f"{atom_name}.onMount",
                file=file_path,
                line_number=line,
                effect_type="onMount",
                has_cleanup=has_cleanup,
                source_atom=atom_name,
            ))

        # ── atomWithMachine ─────────────────────────────────────
        for m in self.ATOM_WITH_MACHINE_PATTERN.finditer(content):
            name = m.group(1)
            machine = m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            machine_atoms.append(JotaiMachineAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                machine_name=machine,
                is_exported=is_exported,
            ))

        # ── atomWithObservable ──────────────────────────────────
        for m in self.ATOM_WITH_OBSERVABLE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="observable",
                is_exported=is_exported,
            ))

        # ── atomWithProxy ──────────────────────────────────────
        for m in self.ATOM_WITH_PROXY_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="proxy",
                is_exported=is_exported,
            ))

        # ── atomWithImmer ──────────────────────────────────────
        for m in self.ATOM_WITH_IMMER_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="immer",
                is_exported=is_exported,
            ))

        # ── atomWithLocation ───────────────────────────────────
        for m in self.ATOM_WITH_LOCATION_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="location",
                is_exported=is_exported,
            ))

        # ── atomWithHash ───────────────────────────────────────
        for m in self.ATOM_WITH_HASH_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            storage_atoms.append(JotaiStorageAtomInfo(
                name=name,
                file=file_path,
                line_number=line,
                storage_key=m.group(2),
                storage_type="hash",
                is_exported=is_exported,
            ))

        # ── atomWithRefresh ────────────────────────────────────
        for m in self.ATOM_WITH_REFRESH_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effects.append(JotaiEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                effect_type="refresh",
                is_exported=is_exported,
            ))

        return {
            'storage_atoms': storage_atoms,
            'effects': effects,
            'machine_atoms': machine_atoms,
        }
