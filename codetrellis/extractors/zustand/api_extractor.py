"""
Zustand API Extractor for CodeTrellis

Extracts Zustand API patterns, integrations, and ecosystem usage:
- Import patterns (zustand, zustand/middleware, zustand/shallow, zustand/react)
- Integration with React Query / TanStack Query
- Integration with React Hook Form
- Zustand/vanilla usage outside React
- SSR hydration patterns
- Testing patterns (act, renderHook)
- Devtools integration
- TypeScript utility types
- Migration patterns (v3→v4, v4→v5)

Supports:
- Zustand v1-v3 (single import from 'zustand')
- Zustand v4 (subpath exports: zustand/middleware, zustand/shallow, zustand/vanilla)
- Zustand v5 (zustand/react, useShallow, getInitialState, improved TS types)

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ZustandImportInfo:
    """Information about Zustand imports."""
    module: str  # zustand, zustand/middleware, zustand/shallow, etc.
    imports: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_type_import: bool = False


@dataclass
class ZustandIntegrationInfo:
    """Information about Zustand integration with other libraries."""
    name: str
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # react-query, react-hook-form, next, ssr, testing
    pattern: str = ""


@dataclass
class ZustandTypeInfo:
    """Information about Zustand TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_kind: str = ""  # StateCreator, StoreApi, UseBoundStore, ExtractState, etc.
    generic_params: str = ""


class ZustandApiExtractor:
    """
    Extracts Zustand API patterns, integrations, and TypeScript types.

    Detects:
    - Import patterns across all versions
    - React Query integration (hydration, dehydration)
    - SSR patterns (getServerSideProps, getInitialState)
    - Testing patterns (renderHook, act)
    - TypeScript utility types (StateCreator, StoreApi, etc.)
    - Migration patterns (deprecated API usage)
    """

    # Import patterns
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]"
        r"(zustand(?:/\w+)?)['\"]|"
        r"require\(['\"]"
        r"(zustand(?:/\w+)?)['\"]"
        r"\))",
        re.MULTILINE
    )

    # TypeScript type imports
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]zustand(?:/\w+)?['\"]",
        re.MULTILINE
    )

    # TypeScript types: StateCreator, StoreApi, UseBoundStore, etc.
    TS_TYPE_USAGE_PATTERN = re.compile(
        r'(?:type|interface)\s+(\w+)\s*=\s*'
        r'(StateCreator|StoreApi|UseBoundStore|ExtractState|StoreMutatorIdentifier|'
        r'Mutate|SetState|GetState)\s*<([^>]*)>',
        re.MULTILINE
    )

    # TypeScript: StateCreator<State, Mutations, Actions>
    STATE_CREATOR_PATTERN = re.compile(
        r'StateCreator\s*<\s*(\w+)',
        re.MULTILINE
    )

    # React Query + Zustand integration
    REACT_QUERY_INTEGRATION = re.compile(
        r"from\s+['\"](?:@tanstack/react-query|react-query)['\"].*?"
        r"(?:queryKey|useQuery|useMutation|QueryClient)",
        re.MULTILINE | re.DOTALL
    )

    # React Hook Form integration
    REACT_HOOK_FORM_INTEGRATION = re.compile(
        r"from\s+['\"]react-hook-form['\"].*?"
        r"(?:useForm|useFormContext|useWatch)",
        re.MULTILINE | re.DOTALL
    )

    # SSR hydration: store.getState() in getServerSideProps
    SSR_PATTERN = re.compile(
        r'(?:getServerSideProps|getStaticProps|getInitialProps)\s*'
        r'(?::\s*\w+\s*)?=?\s*async\s*\(',
        re.MULTILINE
    )

    # Testing patterns
    TESTING_PATTERN = re.compile(
        r'(?:renderHook|act|waitFor)\s*\(',
        re.MULTILINE
    )

    # Zustand test helper: reset store
    TEST_RESET_PATTERN = re.compile(
        r'(?:beforeEach|afterEach)\s*\(\s*\(\s*\)\s*=>\s*\{[^}]*'
        r'(?:setState|destroy|getInitialState)',
        re.MULTILINE | re.DOTALL
    )

    # Deprecated API detection (v3 → v4 migration)
    DEPRECATED_V3_PATTERN = re.compile(
        r"from\s+['\"]zustand/context['\"]",
        re.MULTILINE
    )

    # Next.js integration
    NEXTJS_INTEGRATION = re.compile(
        r"from\s+['\"]next(?:/\w+)?['\"]",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Zustand API patterns from source code."""
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

            imports.append(ZustandImportInfo(
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
                types.append(ZustandTypeInfo(
                    name=tname,
                    file=file_path,
                    line_number=line,
                    type_kind="import",
                ))

        # ── TypeScript type usage ─────────────────────────────────
        for m in self.TS_TYPE_USAGE_PATTERN.finditer(content):
            name = m.group(1)
            type_kind = m.group(2)
            generic_params = m.group(3)
            line = content[:m.start()].count('\n') + 1

            types.append(ZustandTypeInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_kind=type_kind,
                generic_params=generic_params[:100],
            ))

        # ── StateCreator usage ────────────────────────────────────
        for m in self.STATE_CREATOR_PATTERN.finditer(content):
            state_type = m.group(1)
            line = content[:m.start()].count('\n') + 1

            types.append(ZustandTypeInfo(
                name=f"StateCreator<{state_type}>",
                file=file_path,
                line_number=line,
                type_kind="StateCreator",
                generic_params=state_type,
            ))

        # ── Integrations ──────────────────────────────────────────
        # React Query
        if self.REACT_QUERY_INTEGRATION.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="react-query",
                file=file_path,
                integration_type="react-query",
                pattern="useQuery/useMutation with Zustand store",
            ))

        # React Hook Form
        if self.REACT_HOOK_FORM_INTEGRATION.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="react-hook-form",
                file=file_path,
                integration_type="react-hook-form",
                pattern="useForm with Zustand store",
            ))

        # SSR
        if self.SSR_PATTERN.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="ssr",
                file=file_path,
                integration_type="ssr",
                pattern="Server-side state hydration",
            ))

        # Next.js
        if self.NEXTJS_INTEGRATION.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="nextjs",
                file=file_path,
                integration_type="next",
                pattern="Next.js integration",
            ))

        # Testing
        if self.TESTING_PATTERN.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="testing",
                file=file_path,
                integration_type="testing",
                pattern="renderHook/act testing patterns",
            ))

        # Deprecated API
        if self.DEPRECATED_V3_PATTERN.search(content):
            integrations.append(ZustandIntegrationInfo(
                name="deprecated-context",
                file=file_path,
                integration_type="deprecated",
                pattern="zustand/context (deprecated in v4+)",
            ))

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
        }
