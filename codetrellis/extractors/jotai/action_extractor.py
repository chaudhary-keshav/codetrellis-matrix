"""
Jotai Action Extractor for CodeTrellis

Extracts Jotai hook usages and action patterns:
- useAtom() — read + write hook
- useAtomValue() — read-only hook
- useSetAtom() — write-only hook
- useStore() — access to Jotai store instance
- useHydrateAtoms() — SSR hydration hook
- atom write functions (get, set, reset)
- Provider component usage
- Store API (createStore, getDefaultStore, store.get/set/sub)
- useAtomCallback (jotai/utils) — callback with atom access

Supports:
- Jotai v1.x (useAtom, Provider)
- Jotai v2.x (useAtomValue, useSetAtom, createStore, getDefaultStore, useStore)

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JotaiHookUsageInfo:
    """Information about a Jotai hook usage."""
    hook_name: str  # useAtom, useAtomValue, useSetAtom, useStore
    file: str = ""
    line_number: int = 0
    atom_name: str = ""  # atom being used
    destructured_names: List[str] = field(default_factory=list)  # [value, setValue]
    is_in_component: bool = False  # used inside React component


@dataclass
class JotaiWriteFnInfo:
    """Information about a Jotai atom write function."""
    name: str
    file: str = ""
    line_number: int = 0
    write_type: str = ""  # set, reset, dispatch
    target_atoms: List[str] = field(default_factory=list)  # atoms written to
    is_async: bool = False


@dataclass
class JotaiStoreUsageInfo:
    """Information about Jotai store API usage."""
    name: str
    file: str = ""
    line_number: int = 0
    usage_type: str = ""  # createStore, getDefaultStore, store.get, store.set, store.sub
    store_name: str = ""
    is_exported: bool = False


class JotaiActionExtractor:
    """
    Extracts Jotai hook usages and action patterns from source code.

    Detects:
    - useAtom / useAtomValue / useSetAtom hook calls
    - useStore hook calls
    - useHydrateAtoms hook calls
    - Provider component declarations
    - createStore / getDefaultStore calls
    - store.get / store.set / store.sub imperative API
    - useAtomCallback from jotai/utils
    - Atom write functions within atom() definitions
    """

    # useAtom: const [value, setValue] = useAtom(xAtom)
    USE_ATOM_PATTERN = re.compile(
        r'(?:const|let|var)\s+\[([^\]]*)\]\s*=\s*useAtom\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useAtomValue: const value = useAtomValue(xAtom)
    USE_ATOM_VALUE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useAtomValue\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useSetAtom: const setValue = useSetAtom(xAtom)
    USE_SET_ATOM_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useSetAtom\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useStore: const store = useStore()
    USE_STORE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useStore\s*\(',
        re.MULTILINE
    )

    # useHydrateAtoms: useHydrateAtoms([[atomA, valueA], [atomB, valueB]])
    USE_HYDRATE_ATOMS_PATTERN = re.compile(
        r'useHydrateAtoms\s*\(',
        re.MULTILINE
    )

    # useAtomCallback: const callback = useAtomCallback((get, set) => ...)
    USE_ATOM_CALLBACK_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useAtomCallback\s*\(',
        re.MULTILINE
    )

    # Provider: <Provider store={myStore}>
    PROVIDER_PATTERN = re.compile(
        r'<Provider\s+(?:store\s*=\s*\{(\w+)\})?',
        re.MULTILINE
    )

    # createStore: const store = createStore()
    CREATE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*createStore\s*\(',
        re.MULTILINE
    )

    # getDefaultStore: const store = getDefaultStore()
    GET_DEFAULT_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*getDefaultStore\s*\(',
        re.MULTILINE
    )

    # store.get(atom): store.get(countAtom)
    STORE_GET_PATTERN = re.compile(
        r'(\w+)\.get\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # store.set(atom, value): store.set(countAtom, 5)
    STORE_SET_PATTERN = re.compile(
        r'(\w+)\.set\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # store.sub(atom, callback): store.sub(countAtom, () => {})
    STORE_SUB_PATTERN = re.compile(
        r'(\w+)\.sub\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Write function within atom: set(targetAtom, newValue)
    SET_ATOM_PATTERN = re.compile(
        r'set\s*\(\s*(\w+)\s*,',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Jotai hook and action patterns from source code."""
        hook_usages = []
        write_fns = []
        store_usages = []

        # ── useAtom ──────────────────────────────────────────
        for m in self.USE_ATOM_PATTERN.finditer(content):
            destructured = [n.strip() for n in m.group(1).split(',') if n.strip()]
            atom_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useAtom",
                file=file_path,
                line_number=line,
                atom_name=atom_name,
                destructured_names=destructured[:5],
            ))

        # ── useAtomValue ─────────────────────────────────────
        for m in self.USE_ATOM_VALUE_PATTERN.finditer(content):
            var_name = m.group(1)
            atom_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useAtomValue",
                file=file_path,
                line_number=line,
                atom_name=atom_name,
                destructured_names=[var_name],
            ))

        # ── useSetAtom ───────────────────────────────────────
        for m in self.USE_SET_ATOM_PATTERN.finditer(content):
            var_name = m.group(1)
            atom_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useSetAtom",
                file=file_path,
                line_number=line,
                atom_name=atom_name,
                destructured_names=[var_name],
            ))

        # ── useStore ─────────────────────────────────────────
        for m in self.USE_STORE_PATTERN.finditer(content):
            var_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useStore",
                file=file_path,
                line_number=line,
                destructured_names=[var_name],
            ))

        # ── useHydrateAtoms ──────────────────────────────────
        for m in self.USE_HYDRATE_ATOMS_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useHydrateAtoms",
                file=file_path,
                line_number=line,
            ))

        # ── useAtomCallback ──────────────────────────────────
        for m in self.USE_ATOM_CALLBACK_PATTERN.finditer(content):
            var_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(JotaiHookUsageInfo(
                hook_name="useAtomCallback",
                file=file_path,
                line_number=line,
                destructured_names=[var_name],
            ))

        # ── createStore ──────────────────────────────────────
        for m in self.CREATE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            store_usages.append(JotaiStoreUsageInfo(
                name=name,
                file=file_path,
                line_number=line,
                usage_type="createStore",
                store_name=name,
                is_exported=is_exported,
            ))

        # ── getDefaultStore ──────────────────────────────────
        for m in self.GET_DEFAULT_STORE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            store_usages.append(JotaiStoreUsageInfo(
                name=name,
                file=file_path,
                line_number=line,
                usage_type="getDefaultStore",
                store_name=name,
                is_exported=is_exported,
            ))

        # ── Provider ─────────────────────────────────────────
        for m in self.PROVIDER_PATTERN.finditer(content):
            store_name = m.group(1) or ""
            line = content[:m.start()].count('\n') + 1

            store_usages.append(JotaiStoreUsageInfo(
                name="Provider",
                file=file_path,
                line_number=line,
                usage_type="Provider",
                store_name=store_name,
            ))

        # ── store.get / store.set / store.sub ────────────────
        # Only detect if we know about store variables
        known_stores = {su.store_name for su in store_usages if su.store_name}

        for m in self.STORE_GET_PATTERN.finditer(content):
            store_var = m.group(1)
            atom_name = m.group(2)
            # Basic heuristic: check if variable name contains 'store' or is a known store
            if 'store' in store_var.lower() or store_var in known_stores:
                line = content[:m.start()].count('\n') + 1
                store_usages.append(JotaiStoreUsageInfo(
                    name=f"{store_var}.get",
                    file=file_path,
                    line_number=line,
                    usage_type="store.get",
                    store_name=store_var,
                ))

        for m in self.STORE_SET_PATTERN.finditer(content):
            store_var = m.group(1)
            atom_name = m.group(2)
            if 'store' in store_var.lower() or store_var in known_stores:
                line = content[:m.start()].count('\n') + 1
                store_usages.append(JotaiStoreUsageInfo(
                    name=f"{store_var}.set",
                    file=file_path,
                    line_number=line,
                    usage_type="store.set",
                    store_name=store_var,
                ))

        for m in self.STORE_SUB_PATTERN.finditer(content):
            store_var = m.group(1)
            atom_name = m.group(2)
            if 'store' in store_var.lower() or store_var in known_stores:
                line = content[:m.start()].count('\n') + 1
                store_usages.append(JotaiStoreUsageInfo(
                    name=f"{store_var}.sub",
                    file=file_path,
                    line_number=line,
                    usage_type="store.sub",
                    store_name=store_var,
                ))

        # ── Write functions (set(atom, value) within atom bodies) ─
        for m in self.SET_ATOM_PATTERN.finditer(content):
            target = m.group(1)
            # Skip if it's a simple set() (Zustand-style) without atom arg
            if target in ('state', 'prev', 'draft', 'produce'):
                continue
            line = content[:m.start()].count('\n') + 1

            write_fns.append(JotaiWriteFnInfo(
                name=f"set({target})",
                file=file_path,
                line_number=line,
                write_type="set",
                target_atoms=[target],
            ))

        return {
            'hook_usages': hook_usages,
            'write_fns': write_fns,
            'store_usages': store_usages,
        }
