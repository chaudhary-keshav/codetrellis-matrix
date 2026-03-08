"""
Jotai API Extractor for CodeTrellis

Extracts Jotai API patterns, integrations, and ecosystem usage:
- Import patterns (jotai, jotai/utils, jotai/react, jotai-devtools,
                    jotai-immer, jotai-optics, jotai-xstate, jotai-effect,
                    jotai-tanstack-query, jotai-trpc, jotai-molecules,
                    jotai-scope, jotai-location, jotai-valtio)
- TypeScript types (Atom, WritableAtom, PrimitiveAtom, SetStateAction,
                     Getter, Setter, ExtractAtomValue, SetAtom)
- Integration with TanStack Query (atomWithQuery, atomWithMutation,
                                     atomWithSuspenseQuery, atomWithInfiniteQuery)
- DevTools integration (useAtomsDebugValue, useAtomDevtools, DevTools component)
- SSR patterns (useHydrateAtoms, Provider store prop)
- Testing patterns (createStore for testing)
- Migration patterns (v1→v2)

Supports:
- Jotai v1.x (jotai, jotai/utils)
- Jotai v2.x (jotai, jotai/utils, jotai/react, jotai/vanilla)

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JotaiImportInfo:
    """Information about Jotai imports."""
    module: str  # jotai, jotai/utils, jotai-devtools, etc.
    imports: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_type_import: bool = False


@dataclass
class JotaiIntegrationInfo:
    """Information about Jotai integration with other libraries."""
    name: str
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # tanstack-query, xstate, immer, devtools, ssr, testing
    pattern: str = ""


@dataclass
class JotaiTypeInfo:
    """Information about Jotai TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_kind: str = ""  # Atom, WritableAtom, PrimitiveAtom, Getter, Setter, etc.
    generic_params: str = ""


class JotaiApiExtractor:
    """
    Extracts Jotai API patterns, integrations, and TypeScript types.

    Detects:
    - Import patterns across all versions and ecosystem packages
    - TanStack Query integration (atomWithQuery, atomWithMutation)
    - DevTools integration (useAtomsDebugValue, DevTools component)
    - SSR patterns (useHydrateAtoms, Provider with store)
    - Testing patterns (createStore for isolated tests)
    - TypeScript utility types
    - Migration patterns (v1→v2 deprecated API detection)
    """

    # Import patterns for Jotai ecosystem
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]"
        r"(jotai(?:[/-][\w-]+)?(?:/[\w-]+)?)['\"]|"
        r"require\(['\"]"
        r"(jotai(?:[/-][\w-]+)?(?:/[\w-]+)?)['\"]"
        r"\))",
        re.MULTILINE
    )

    # TypeScript type imports
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]jotai(?:/\w+)?['\"]",
        re.MULTILINE
    )

    # TypeScript types: Atom, WritableAtom, PrimitiveAtom, etc.
    TS_TYPE_USAGE_PATTERN = re.compile(
        r'(?:type|interface)\s+(\w+)\s*=?\s*'
        r'(Atom|WritableAtom|PrimitiveAtom|SetStateAction|'
        r'Getter|Setter|ExtractAtomValue|SetAtom|'
        r'AtomFamily|WritableAtomFamily)\s*<([^>]*?)>',
        re.MULTILINE
    )

    # TypeScript: Atom<T> usage in type annotations
    ATOM_TYPE_ANNOTATION = re.compile(
        r':\s*(Atom|WritableAtom|PrimitiveAtom)\s*<\s*(\w+)',
        re.MULTILINE
    )

    # TanStack Query + Jotai integration
    TANSTACK_QUERY_PATTERN = re.compile(
        r'(?:atomWithQuery|atomWithMutation|atomWithSuspenseQuery|'
        r'atomWithInfiniteQuery|atomWithSuspenseInfiniteQuery)\s*\(',
        re.MULTILINE
    )

    # tRPC + Jotai integration
    TRPC_PATTERN = re.compile(
        r"from\s+['\"]jotai-trpc['\"]|"
        r'httpBatchLink|createTRPCJotai',
        re.MULTILINE
    )

    # DevTools integration
    DEVTOOLS_PATTERN = re.compile(
        r'useAtomsDebugValue|useAtomDevtools|'
        r'<DevTools\b|jotai-devtools',
        re.MULTILINE
    )

    # SSR hydration patterns
    SSR_PATTERN = re.compile(
        r'useHydrateAtoms\s*\(|'
        r'<Provider\s+store\s*=',
        re.MULTILINE
    )

    # Testing patterns
    TESTING_PATTERN = re.compile(
        r'createStore\s*\(\s*\)|'
        r'renderHook.*useAtom|'
        r"(?:it|test|describe)\s*\(['\"].*(?:atom|jotai)",
        re.MULTILINE
    )

    # Deprecated v1 API detection
    DEPRECATED_V1_PATTERN = re.compile(
        r"from\s+['\"]jotai/devtools['\"]|"
        r'useUpdateAtom\s*\(|'
        r'useAtomValue\s*\(\s*\w+\s*,\s*scope',
        re.MULTILINE
    )

    # Molecules integration
    MOLECULES_PATTERN = re.compile(
        r"from\s+['\"]jotai-molecules['\"]|"
        r'molecule\s*\(|useMolecule\s*\(',
        re.MULTILINE
    )

    # Scope integration
    SCOPE_PATTERN = re.compile(
        r"from\s+['\"]jotai-scope['\"]|"
        r'ScopeProvider\b|createScope\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Jotai API patterns from source code."""
        imports = []
        integrations = []
        types = []

        # ── Import patterns ───────────────────────────────────────
        for m in self.IMPORT_PATTERN.finditer(content):
            named_imports_str = m.group(1)
            default_import = m.group(2)
            module_esm = m.group(3)
            module_cjs = m.group(4)
            module = module_esm or module_cjs or ""
            line = content[:m.start()].count('\n') + 1

            import_names = []
            if named_imports_str:
                import_names = [n.strip().split(' as ')[0].strip()
                               for n in named_imports_str.split(',') if n.strip()]
            elif default_import:
                import_names = [default_import]

            is_type = 'import type' in content[max(0, m.start() - 15):m.start() + 20]

            imports.append(JotaiImportInfo(
                module=module,
                imports=import_names[:20],
                file=file_path,
                line_number=line,
                is_type_import=is_type,
            ))

        # ── Type imports ──────────────────────────────────────────
        for m in self.TYPE_IMPORT_PATTERN.finditer(content):
            type_names_str = m.group(1)
            line = content[:m.start()].count('\n') + 1
            type_names = [n.strip().split(' as ')[0].strip()
                         for n in type_names_str.split(',') if n.strip()]

            for tname in type_names:
                types.append(JotaiTypeInfo(
                    name=tname,
                    file=file_path,
                    line_number=line,
                    type_kind="import",
                ))

        # ── TypeScript type usage ─────────────────────────────────
        for m in self.TS_TYPE_USAGE_PATTERN.finditer(content):
            name = m.group(1)
            type_kind = m.group(2)
            generic = m.group(3)
            line = content[:m.start()].count('\n') + 1

            types.append(JotaiTypeInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_kind=type_kind,
                generic_params=generic[:60],
            ))

        # ── Atom type annotations ─────────────────────────────────
        for m in self.ATOM_TYPE_ANNOTATION.finditer(content):
            type_kind = m.group(1)
            type_param = m.group(2)
            line = content[:m.start()].count('\n') + 1

            types.append(JotaiTypeInfo(
                name=f"{type_kind}<{type_param}>",
                file=file_path,
                line_number=line,
                type_kind=type_kind,
                generic_params=type_param,
            ))

        # ── TanStack Query integration ────────────────────────────
        for m in self.TANSTACK_QUERY_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            pattern_text = m.group(0).rstrip('(').strip()
            integrations.append(JotaiIntegrationInfo(
                name="tanstack-query",
                file=file_path,
                line_number=line,
                integration_type="tanstack-query",
                pattern=pattern_text,
            ))

        # ── tRPC integration ──────────────────────────────────────
        if self.TRPC_PATTERN.search(content):
            line = 1
            m = self.TRPC_PATTERN.search(content)
            if m:
                line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="trpc",
                file=file_path,
                line_number=line,
                integration_type="trpc",
            ))

        # ── DevTools integration ──────────────────────────────────
        if self.DEVTOOLS_PATTERN.search(content):
            m = self.DEVTOOLS_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="devtools",
                file=file_path,
                line_number=line,
                integration_type="devtools",
                pattern=m.group(0)[:30],
            ))

        # ── SSR patterns ──────────────────────────────────────────
        if self.SSR_PATTERN.search(content):
            m = self.SSR_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="ssr",
                file=file_path,
                line_number=line,
                integration_type="ssr",
                pattern=m.group(0)[:30],
            ))

        # ── Testing patterns ──────────────────────────────────────
        if self.TESTING_PATTERN.search(content):
            m = self.TESTING_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="testing",
                file=file_path,
                line_number=line,
                integration_type="testing",
            ))

        # ── Molecules integration ─────────────────────────────────
        if self.MOLECULES_PATTERN.search(content):
            m = self.MOLECULES_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="molecules",
                file=file_path,
                line_number=line,
                integration_type="molecules",
            ))

        # ── Scope integration ─────────────────────────────────────
        if self.SCOPE_PATTERN.search(content):
            m = self.SCOPE_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="scope",
                file=file_path,
                line_number=line,
                integration_type="scope",
            ))

        # ── Deprecated v1 API ─────────────────────────────────────
        if self.DEPRECATED_V1_PATTERN.search(content):
            m = self.DEPRECATED_V1_PATTERN.search(content)
            line = content[:m.start()].count('\n') + 1
            integrations.append(JotaiIntegrationInfo(
                name="deprecated-v1",
                file=file_path,
                line_number=line,
                integration_type="deprecated",
                pattern=m.group(0)[:30],
            ))

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
        }
