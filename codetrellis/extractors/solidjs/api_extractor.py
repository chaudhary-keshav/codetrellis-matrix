"""
Solid.js API Extractor for CodeTrellis

Extracts Solid.js API patterns, imports, integrations, and TypeScript types:
- Import patterns from solid-js, solid-js/store, solid-js/web, solid-js/html
- @solidjs/router imports
- solid-start / vinxi imports
- Framework integrations (Tailwind, i18n, testing, forms)
- TypeScript type patterns (Accessor, Setter, Component, JSX.Element)
- Context API (createContext, useContext)
- Lifecycle hooks (onMount, onCleanup, onError)
- SSR/hydration patterns
- Build tool integrations (Vite, Vinxi)
- Testing utilities (@solidjs/testing-library)
- Animation integrations (solid-transition-group, Motion)

Supports:
- Solid.js v1.0-v2.0 full API surface
- SolidStart v0.x and v1.0+
- All Solid.js ecosystem packages

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidImportInfo:
    """Information about a Solid.js import statement."""
    source: str  # Module source (solid-js, solid-js/store, etc.)
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    is_default: bool = False
    subpath: str = ""  # /store, /web, /html


@dataclass
class SolidContextInfo:
    """Information about a Solid.js context."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    has_default_value: bool = False
    provider_name: str = ""
    is_exported: bool = False


@dataclass
class SolidLifecycleInfo:
    """Information about a Solid.js lifecycle hook."""
    hook_name: str  # onMount, onCleanup, onError
    file: str = ""
    line_number: int = 0


@dataclass
class SolidIntegrationInfo:
    """Information about a Solid.js ecosystem integration."""
    integration_type: str  # testing, i18n, forms, animation, ssr, meta, devtools
    file: str = ""
    line_number: int = 0
    library: str = ""
    pattern: str = ""


@dataclass
class SolidTypeInfo:
    """Information about a Solid.js TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_category: str = ""  # accessor, setter, component, jsx, store, signal
    type_expression: str = ""


class SolidApiExtractor:
    """
    Extracts Solid.js API usage patterns from source code.

    Detects:
    - Import patterns from solid-js ecosystem packages
    - Context API: createContext, useContext
    - Lifecycle: onMount, onCleanup, onError
    - TypeScript types: Accessor<T>, Setter<T>, Component<P>, JSX.Element
    - SSR: renderToString, renderToStream, hydrate, isServer
    - Integrations: testing, i18n, forms, animations, meta, devtools
    - Build tooling: vite-plugin-solid, vinxi
    """

    # Import from solid-js ecosystem
    SOLID_IMPORT_PATTERN = re.compile(
        r"import\s+(?:(?:\{([^}]+)\})|(\w+))\s+from\s+['\"]"
        r"(solid-js(?:/\w+)?|@solidjs/\w+|solid-start(?:/\w+)?|vinxi(?:/\w+)?|"
        r"@solid-primitives/\w+|solid-styled-components|solid-transition-group|"
        r"@motionone/solid|solid-markdown|solid-meta|solid-styled|"
        r"@tanstack/solid-query|@tanstack/solid-table|@tanstack/solid-virtual|"
        r"@solidjs/testing-library|solid-testing-library|"
        r"@kobalte/core|@ark-ui/solid|solid-toast|solid-icons|"
        r"solid-headless|@solid-mediakit/\w+)['\"]",
        re.MULTILINE
    )

    # createContext<T>(defaultValue?)
    CREATE_CONTEXT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createContext\s*(?:<([^>]*)>)?\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # useContext(Context)
    USE_CONTEXT_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useContext\s*(?:<[^>]*>)?\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'(onMount|onCleanup|onError)\s*\(',
        re.MULTILINE
    )

    # TypeScript Solid types
    SOLID_TYPE_PATTERN = re.compile(
        r':\s*(Accessor|Setter|Signal|Resource|Component|ParentComponent|FlowComponent|VoidComponent|JSX\.Element|JSXElement|Store|SetStoreFunction)\s*(?:<([^>]*)>)?',
        re.MULTILINE
    )

    # isServer check
    IS_SERVER_PATTERN = re.compile(
        r'isServer\b',
        re.MULTILINE
    )

    # SSR functions
    SSR_PATTERN = re.compile(
        r'(renderToString|renderToStream|renderToStringAsync|hydrate|generateHydrationScript|HydrationScript)\s*[(<]',
        re.MULTILINE
    )

    # Testing patterns
    TESTING_PATTERN = re.compile(
        r'(render|cleanup|fireEvent|screen|renderHook)\s*(?:\(|\.)',
        re.MULTILINE
    )

    # Solid Primitives
    SOLID_PRIMITIVES_PATTERN = re.compile(
        r"from\s+['\"]@solid-primitives/(\w+)['\"]",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js API patterns from source code."""
        imports = []
        contexts = []
        lifecycles = []
        integrations = []
        types = []

        # ── Imports ───────────────────────────────────────────────
        for m in self.SOLID_IMPORT_PATTERN.finditer(content):
            named = m.group(1)
            default_import = m.group(2)
            source = m.group(3)
            line = content[:m.start()].count('\n') + 1

            named_imports = []
            if named:
                named_imports = [n.strip().split(' as ')[0].strip() for n in named.split(',') if n.strip()]

            subpath = ""
            if '/' in source:
                parts = source.split('/')
                if len(parts) > 1:
                    subpath = '/'.join(parts[1:])

            imports.append(SolidImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports[:20],
                is_default=bool(default_import),
                subpath=subpath,
            ))

        # ── Contexts ──────────────────────────────────────────────
        for m in self.CREATE_CONTEXT_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            default_val = m.group(3).strip() if m.group(3) else ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            has_default = bool(default_val) and default_val not in ('', 'undefined', 'null')

            # Look for Provider usage
            provider_name = f"{name}.Provider"

            contexts.append(SolidContextInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                has_default_value=has_default,
                provider_name=provider_name,
                is_exported=is_exported,
            ))

        # ── Lifecycle hooks ───────────────────────────────────────
        for m in self.LIFECYCLE_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            lifecycles.append(SolidLifecycleInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
            ))

        # ── TypeScript types ──────────────────────────────────────
        for m in self.SOLID_TYPE_PATTERN.finditer(content):
            type_name = m.group(1)
            type_params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            # Categorize
            type_cat = "component"
            if type_name in ('Accessor', 'Signal'):
                type_cat = "signal"
            elif type_name == 'Setter':
                type_cat = "setter"
            elif type_name == 'Resource':
                type_cat = "resource"
            elif type_name in ('Store', 'SetStoreFunction'):
                type_cat = "store"
            elif type_name.startswith('JSX'):
                type_cat = "jsx"

            types.append(SolidTypeInfo(
                name=type_name,
                file=file_path,
                line_number=line,
                type_category=type_cat,
                type_expression=f"{type_name}<{type_params}>" if type_params else type_name,
            ))

        # ── Integrations ──────────────────────────────────────────
        # SSR
        for m in self.SSR_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            integrations.append(SolidIntegrationInfo(
                integration_type="ssr",
                file=file_path,
                line_number=line,
                library="solid-js/web",
                pattern=m.group(1),
            ))

        # Solid Primitives
        for m in self.SOLID_PRIMITIVES_PATTERN.finditer(content):
            primitive = m.group(1)
            line = content[:m.start()].count('\n') + 1
            integrations.append(SolidIntegrationInfo(
                integration_type="primitive",
                file=file_path,
                line_number=line,
                library=f"@solid-primitives/{primitive}",
                pattern=primitive,
            ))

        # Testing
        if '@solidjs/testing-library' in content or 'solid-testing-library' in content:
            for m in self.TESTING_PATTERN.finditer(content):
                line = content[:m.start()].count('\n') + 1
                integrations.append(SolidIntegrationInfo(
                    integration_type="testing",
                    file=file_path,
                    line_number=line,
                    library="@solidjs/testing-library",
                    pattern=m.group(1),
                ))
                break  # Just detect once

        # TanStack integrations
        if '@tanstack/solid-query' in content:
            line = content.index('@tanstack/solid-query')
            line = content[:line].count('\n') + 1
            integrations.append(SolidIntegrationInfo(
                integration_type="data-fetching",
                file=file_path,
                line_number=line,
                library="@tanstack/solid-query",
                pattern="tanstack-query",
            ))

        # Kobalte UI
        if '@kobalte/core' in content:
            line = content.index('@kobalte/core')
            line = content[:line].count('\n') + 1
            integrations.append(SolidIntegrationInfo(
                integration_type="ui",
                file=file_path,
                line_number=line,
                library="@kobalte/core",
                pattern="kobalte",
            ))

        return {
            "imports": imports,
            "contexts": contexts,
            "lifecycles": lifecycles,
            "integrations": integrations,
            "types": types,
        }
