"""
Preact API Extractor for CodeTrellis

Extracts Preact API patterns from JavaScript/TypeScript source code:
- Import patterns (preact, preact/hooks, preact/compat, @preact/signals,
   @preact/signals-core, preact-router, preact-render-to-string, preact-iso,
   htm, goober, preact-markup)
- SSR patterns (renderToString, renderToStringAsync, hydrate, preact-iso)
- Ecosystem integration detection (Fresh/Deno, WMR, Preact CLI,
   Astro @astrojs/preact, Vite @preact/preset-vite, Next.js preact-compat)
- TypeScript type usage (ComponentChildren, VNode, JSX, FunctionComponent,
   ComponentType, RefObject, RenderableProps, Attributes)
- htm tagged template usage (html`<div>...</div>`)
- preact-router / wouter routing patterns
- preact-render-to-string SSR

Supports:
- Preact 8.x (preact, preact-compat, linked state)
- Preact X (10.x) (preact, preact/hooks, preact/compat, preact/debug)
- @preact/signals v1-v2, @preact/signals-core v1
- preact-router v3-v4, wouter-preact
- preact-render-to-string v5-v6
- Fresh (Deno), WMR, Preact CLI, Astro, Vite integration

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PreactImportInfo:
    """Information about a Preact-related import."""
    source: str  # e.g., 'preact', 'preact/hooks', '@preact/signals'
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    is_type_import: bool = False
    import_category: str = ""  # core, hooks, compat, signals, router, ssr, testing, ecosystem


@dataclass
class PreactIntegrationInfo:
    """Information about a Preact ecosystem integration."""
    name: str
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # framework, ui, routing, ssr, testing, build
    source_package: str = ""


@dataclass
class PreactTypeInfo:
    """Information about Preact TypeScript type usage."""
    type_name: str
    file: str = ""
    line_number: int = 0
    source: str = ""  # e.g., 'preact', 'preact/hooks'


@dataclass
class PreactSSRInfo:
    """Information about Preact SSR patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    ssr_type: str = ""  # render_to_string, hydrate, preact_iso, streaming
    is_async: bool = False


class PreactApiExtractor:
    """
    Extracts Preact API usage patterns from source code.

    Detects:
    - All Preact import sources and named imports
    - SSR/hydration patterns
    - Ecosystem integrations (Fresh, WMR, Astro, Vite, etc.)
    - TypeScript type usage
    - htm tagged templates
    """

    # Import categories by source pattern
    IMPORT_CATEGORIES = {
        'preact': 'core',
        'preact/hooks': 'hooks',
        'preact/compat': 'compat',
        'preact/debug': 'debug',
        'preact/devtools': 'debug',
        'preact/jsx-runtime': 'core',
        'preact/jsx-dev-runtime': 'core',
        'preact/test-utils': 'testing',
        '@preact/signals': 'signals',
        '@preact/signals-core': 'signals',
        '@preact/signals-react': 'signals',
        '@preact/preset-vite': 'build',
        '@preact/async-loader': 'ssr',
        'preact-router': 'router',
        'preact-router/match': 'router',
        'wouter-preact': 'router',
        'preact-render-to-string': 'ssr',
        'preact-render-to-string/stream': 'ssr',
        'preact-iso': 'ssr',
        'preact-compat': 'compat',
        '@testing-library/preact': 'testing',
        'preact-markup': 'utility',
        'preact-portal': 'utility',
        'htm': 'htm',
        'htm/preact': 'htm',
        'goober': 'styling',
        'goober/global': 'styling',
    }

    # Import pattern (named + default)
    IMPORT_PATTERN = re.compile(
        r'^[ \t]*import\s+'
        r'(?:(type)\s+)?'
        r'(?:'
        r'(?:(\w+)\s*,?\s*)?'  # default import
        r'(?:\{([^}]+)\}\s*)?'  # named imports
        r')'
        r'from\s+[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # Require pattern
    REQUIRE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )

    # Preact-relevant import sources (for filtering)
    PREACT_SOURCES = {
        'preact', 'preact/hooks', 'preact/compat', 'preact/debug',
        'preact/devtools', 'preact/jsx-runtime', 'preact/jsx-dev-runtime',
        'preact/test-utils', 'preact-compat',
        '@preact/signals', '@preact/signals-core', '@preact/signals-react',
        '@preact/preset-vite', '@preact/async-loader',
        'preact-router', 'preact-router/match', 'wouter-preact',
        'preact-render-to-string', 'preact-render-to-string/stream',
        'preact-iso', 'preact-markup', 'preact-portal',
        'htm', 'htm/preact', 'goober', 'goober/global',
    }

    # SSR patterns
    RENDER_TO_STRING_PATTERN = re.compile(
        r'renderToString\s*\(',
        re.MULTILINE
    )
    RENDER_TO_STRING_ASYNC_PATTERN = re.compile(
        r'renderToStringAsync\s*\(',
        re.MULTILINE
    )
    HYDRATE_PATTERN = re.compile(
        r'\bhydrate\s*\(',
        re.MULTILINE
    )
    PREACT_ISO_PATTERN = re.compile(
        r'\b(?:lazy|ErrorBoundary|LocationProvider|Router|prerender)\b.*preact-iso',
        re.MULTILINE
    )
    RENDER_TO_STREAM_PATTERN = re.compile(
        r'renderToReadableStream\s*\(',
        re.MULTILINE
    )

    # TypeScript Preact types
    PREACT_TYPES = [
        'ComponentChildren', 'VNode', 'JSX', 'FunctionComponent', 'FC',
        'ComponentType', 'ComponentClass', 'RefObject', 'Ref', 'RefCallback',
        'RenderableProps', 'Attributes', 'ClassAttributes',
        'Component', 'AnyComponent', 'PreactDOMAttributes',
        'Signal', 'ReadonlySignal', 'Computed',
    ]

    TYPE_USAGE_PATTERN = re.compile(
        r'\b(' + '|'.join(PREACT_TYPES) + r')\b\s*(?:<|[,)\];\s])',
        re.MULTILINE
    )

    # htm tagged template: html`<div>...</div>`
    HTM_PATTERN = re.compile(
        r'\bhtml\s*`',
        re.MULTILINE
    )

    # Ecosystem framework detection
    ECOSYSTEM_PATTERNS = {
        'fresh': (re.compile(r'from\s+[\'"](\$fresh|\$fresh/|fresh/)', re.MULTILINE), 'framework'),
        'wmr': (re.compile(r'from\s+[\'"]wmr[\'"]', re.MULTILINE), 'build'),
        'preact-cli': (re.compile(r'preact\.config|preact-cli', re.MULTILINE), 'build'),
        'astro-preact': (re.compile(r'@astrojs/preact', re.MULTILINE), 'framework'),
        'vite-preact': (re.compile(r'@preact/preset-vite', re.MULTILINE), 'build'),
        'preact-testing-library': (re.compile(r'@testing-library/preact', re.MULTILINE), 'testing'),
        'enzyme-preact': (re.compile(r'enzyme-adapter-preact', re.MULTILINE), 'testing'),
        'goober': (re.compile(r"from\s+['\"]goober['\"]", re.MULTILINE), 'styling'),
        'preact-i18n': (re.compile(r"from\s+['\"]preact-i18n['\"]", re.MULTILINE), 'i18n'),
        'preact-helmet': (re.compile(r"from\s+['\"]preact-helmet['\"]", re.MULTILINE), 'utility'),
        'preact-custom-element': (re.compile(r"from\s+['\"]preact-custom-element['\"]", re.MULTILINE), 'webcomponent'),
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Preact API patterns from source code."""
        imports: List[PreactImportInfo] = []
        integrations: List[PreactIntegrationInfo] = []
        types: List[PreactTypeInfo] = []
        ssr_patterns: List[PreactSSRInfo] = []

        # ── Import extraction ─────────────────────────────────────
        for m in self.IMPORT_PATTERN.finditer(content):
            is_type = bool(m.group(1))
            default_import = m.group(2) or ""
            named_str = m.group(3) or ""
            source = m.group(4)
            line = content[:m.start()].count('\n') + 1

            # Filter to Preact-relevant imports
            if not self._is_preact_source(source):
                continue

            named_imports = []
            if named_str:
                named_imports = [n.strip().split(' as ')[0].strip().replace('type ', '')
                                 for n in named_str.split(',')
                                 if n.strip()]

            category = self._categorize_import(source)

            imports.append(PreactImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports[:15],
                default_import=default_import,
                is_type_import=is_type,
                import_category=category,
            ))

        # ── Require extraction ────────────────────────────────────
        for m in self.REQUIRE_PATTERN.finditer(content):
            named_str = m.group(1) or ""
            default_import = m.group(2) or ""
            source = m.group(3)
            line = content[:m.start()].count('\n') + 1

            if not self._is_preact_source(source):
                continue

            named_imports = []
            if named_str:
                named_imports = [n.strip().split(':')[0].strip()
                                 for n in named_str.split(',')
                                 if n.strip()]

            category = self._categorize_import(source)

            imports.append(PreactImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports[:15],
                default_import=default_import,
                import_category=category,
            ))

        # ── SSR patterns ──────────────────────────────────────────
        for m in self.RENDER_TO_STRING_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            ssr_patterns.append(PreactSSRInfo(
                name="renderToString",
                file=file_path,
                line_number=line,
                ssr_type="render_to_string",
                is_async=False,
            ))

        for m in self.RENDER_TO_STRING_ASYNC_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            ssr_patterns.append(PreactSSRInfo(
                name="renderToStringAsync",
                file=file_path,
                line_number=line,
                ssr_type="render_to_string",
                is_async=True,
            ))

        for m in self.HYDRATE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            ssr_patterns.append(PreactSSRInfo(
                name="hydrate",
                file=file_path,
                line_number=line,
                ssr_type="hydrate",
            ))

        for m in self.RENDER_TO_STREAM_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            ssr_patterns.append(PreactSSRInfo(
                name="renderToReadableStream",
                file=file_path,
                line_number=line,
                ssr_type="streaming",
                is_async=True,
            ))

        # ── Ecosystem integrations ────────────────────────────────
        for eco_name, (pattern, eco_type) in self.ECOSYSTEM_PATTERNS.items():
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                integrations.append(PreactIntegrationInfo(
                    name=eco_name,
                    file=file_path,
                    line_number=line,
                    integration_type=eco_type,
                    source_package=eco_name,
                ))
                break  # One per ecosystem per file

        # ── TypeScript type usage ─────────────────────────────────
        seen_types = set()
        for m in self.TYPE_USAGE_PATTERN.finditer(content):
            type_name = m.group(1)
            if type_name in seen_types:
                continue
            seen_types.add(type_name)
            line = content[:m.start()].count('\n') + 1
            types.append(PreactTypeInfo(
                type_name=type_name,
                file=file_path,
                line_number=line,
                source=self._infer_type_source(type_name),
            ))

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
            'ssr_patterns': ssr_patterns,
        }

    def _is_preact_source(self, source: str) -> bool:
        """Check if an import source is Preact-related."""
        if source in self.PREACT_SOURCES:
            return True
        if source.startswith('preact') or source.startswith('@preact/'):
            return True
        if source in ('htm', 'htm/preact', 'goober', 'goober/global'):
            return True
        if 'preact' in source.lower():
            return True
        return False

    def _categorize_import(self, source: str) -> str:
        """Categorize an import by its source."""
        if source in self.IMPORT_CATEGORIES:
            return self.IMPORT_CATEGORIES[source]
        if source.startswith('@preact/signals'):
            return 'signals'
        if source.startswith('preact-router'):
            return 'router'
        if source.startswith('preact'):
            return 'core'
        if 'htm' in source:
            return 'htm'
        return 'ecosystem'

    def _infer_type_source(self, type_name: str) -> str:
        """Infer the package source for a Preact type."""
        signal_types = {'Signal', 'ReadonlySignal', 'Computed'}
        if type_name in signal_types:
            return '@preact/signals'
        return 'preact'
