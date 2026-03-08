"""
Lit API Extractor for CodeTrellis

Extracts Lit ecosystem API usage patterns from JavaScript/TypeScript source code:
- Import patterns (lit, lit-element, lit-html, lit/decorators, @lit/reactive-element)
- @lit-labs/* experimental packages
- @lit/localize localization
- @lit/task async task controller
- @lit/context context protocol
- SSR patterns (@lit-labs/ssr, @lit-labs/ssr-client)
- TypeScript types (PropertyValues, ReactiveController, etc.)
- Ecosystem integrations (Vaadin, Shoelace, Spectrum, Open WC)
- Build tool integrations (Vite, Rollup, esbuild, @web/dev-server)

Supports:
- Polymer 1.x-3.x imports
- lit-element 2.x imports
- lit-html 1.x-2.x imports
- lit 2.x-3.x unified imports
- @lit-labs/* experimental packages
- @open-wc/* tooling
- @web/* tooling

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class LitImportInfo:
    """Information about a Lit ecosystem import."""
    source: str  # Package name (e.g., 'lit', 'lit/decorators.js')
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    import_category: str = ""  # core, decorators, directives, labs, tools, polymer
    is_type_import: bool = False
    is_side_effect: bool = False  # import 'lit/polyfill-support.js'


@dataclass
class LitIntegrationInfo:
    """Information about a Lit ecosystem integration."""
    name: str  # Integration name (e.g., 'vaadin', 'shoelace')
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # ui-library, tooling, testing, framework
    source_package: str = ""


@dataclass
class LitTypeInfo:
    """Information about a Lit TypeScript type usage."""
    type_name: str  # PropertyValues, ReactiveController, etc.
    file: str = ""
    line_number: int = 0
    source: str = ""  # Import source


@dataclass
class LitSSRInfo:
    """Information about a Lit SSR pattern."""
    name: str  # render, LitElementRenderer, etc.
    file: str = ""
    line_number: int = 0
    ssr_type: str = ""  # server-render, client-hydrate, declarative-shadow-dom
    is_async: bool = False


class LitApiExtractor:
    """
    Extracts Lit API usage and ecosystem integration patterns.

    Detects:
    - Core lit imports (lit, lit-element, lit-html)
    - Decorator imports (lit/decorators.js)
    - Directive imports (lit/directives/*.js)
    - Lab imports (@lit-labs/ssr, @lit-labs/router, @lit-labs/task, etc.)
    - Stable lab promotions (@lit/task, @lit/context, @lit/localize)
    - Tooling (@open-wc/testing, @web/dev-server, @web/test-runner)
    - UI libraries (Vaadin, Shoelace, Spectrum Web Components, Lion)
    - SSR patterns
    - TypeScript types
    """

    # Import pattern: from 'source' / import 'source'
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?\{([^}]+)\}\s+from|"
        r"import\s+(\w+)\s+from|"
        r"import\s+)\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Side-effect imports: import 'lit/polyfill-support.js'
    SIDE_EFFECT_IMPORT = re.compile(
        r"import\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Import categories by source
    IMPORT_CATEGORIES = {
        'lit': 'core',
        'lit-element': 'core',
        'lit-html': 'core',
        'lit/decorators.js': 'decorators',
        'lit/decorators': 'decorators',
        'lit/directive.js': 'directives',
        'lit/directive': 'directives',
        'lit/async-directive.js': 'directives',
        'lit/static-html.js': 'core',
        'lit/static-html': 'core',
        '@lit/reactive-element': 'core',
        '@lit/reactive-element/decorators.js': 'decorators',
        '@lit/reactive-element/decorators': 'decorators',
        '@lit/localize': 'localization',
        '@lit/task': 'controller',
        '@lit/context': 'context',
    }

    # Integration patterns
    INTEGRATION_PATTERNS = {
        # UI Libraries
        'vaadin': re.compile(r"(?:from|import)\s+['\"]@vaadin/", re.MULTILINE),
        'shoelace': re.compile(r"from\s+['\"]@shoelace-style/shoelace", re.MULTILINE),
        'spectrum-web-components': re.compile(r"from\s+['\"]@spectrum-web-components/", re.MULTILINE),
        'lion': re.compile(r"from\s+['\"]@lion/", re.MULTILINE),
        'material-web': re.compile(r"from\s+['\"]@material/web", re.MULTILINE),
        'carbon-web-components': re.compile(r"from\s+['\"]@carbon/web-components", re.MULTILINE),
        'patternfly-elements': re.compile(r"from\s+['\"]@patternfly/elements", re.MULTILINE),
        'fast-element': re.compile(r"from\s+['\"]@microsoft/fast-element", re.MULTILINE),

        # Tooling
        'open-wc-testing': re.compile(r"from\s+['\"]@open-wc/testing", re.MULTILINE),
        'open-wc-scoped-elements': re.compile(r"from\s+['\"]@open-wc/scoped-elements", re.MULTILINE),
        'web-dev-server': re.compile(r"from\s+['\"]@web/dev-server", re.MULTILINE),
        'web-test-runner': re.compile(r"from\s+['\"]@web/test-runner", re.MULTILINE),
        'web-component-analyzer': re.compile(r"web-component-analyzer|wca\b", re.MULTILINE),
        'custom-elements-manifest': re.compile(r"custom-elements-manifest|@custom-elements-manifest", re.MULTILINE),
        'storybook-wc': re.compile(r"@storybook/web-components", re.MULTILINE),

        # Build tools
        'rollup-plugin-lit-css': re.compile(r"rollup-plugin-lit-css", re.MULTILINE),
        'vite-plugin-lit-css': re.compile(r"vite-plugin-lit-css", re.MULTILINE),

        # State management
        'lit-state': re.compile(r"from\s+['\"]lit-element-state|from\s+['\"]@lit-app/state", re.MULTILINE),

        # Routing
        'lit-router': re.compile(r"@lit-labs/router|from\s+['\"]lit-element-router", re.MULTILINE),

        # Polymer
        'polymer': re.compile(r"from\s+['\"]@polymer/", re.MULTILINE),
    }

    # SSR patterns
    SSR_PATTERNS = {
        'lit-labs-ssr': re.compile(r"from\s+['\"]@lit-labs/ssr", re.MULTILINE),
        'lit-labs-ssr-client': re.compile(r"from\s+['\"]@lit-labs/ssr-client", re.MULTILINE),
        'declarative-shadow-dom': re.compile(r'<template\s+shadowroot', re.MULTILINE),
        'lit-hydrate': re.compile(r"from\s+['\"]@lit-labs/ssr-client/lit-element-hydrate-support", re.MULTILINE),
    }

    # TypeScript types from lit
    LIT_TYPES = [
        'PropertyValues', 'PropertyDeclaration', 'PropertyValueMap',
        'ReactiveController', 'ReactiveControllerHost', 'ReactiveElement',
        'LitElement', 'CSSResult', 'CSSResultGroup', 'CSSResultOrNative',
        'TemplateResult', 'SVGTemplateResult', 'RenderOptions',
        'Directive', 'AsyncDirective', 'DirectiveResult',
        'ComplexAttributeConverter', 'AttributeConverter',
        'PropertyDeclarations', 'UpdatedProperties',
    ]

    TS_TYPE_USAGE = re.compile(
        r'\b(' + '|'.join(LIT_TYPES) + r')\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract API usage information from source code.

        Returns dict with keys: imports, integrations, types, ssr_patterns
        """
        imports: List[LitImportInfo] = []
        integrations: List[LitIntegrationInfo] = []
        types: List[LitTypeInfo] = []
        ssr_patterns: List[LitSSRInfo] = []

        # ── Imports ───────────────────────────────────────────────
        for m in self.IMPORT_PATTERN.finditer(content):
            named = m.group(1)
            default = m.group(2)
            source = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            # Skip non-lit imports
            if not self._is_lit_import(source):
                continue

            named_imports = []
            if named:
                named_imports = [n.strip() for n in named.split(',') if n.strip()]
            elif default:
                named_imports = [default]

            is_type = 'import type' in content[max(0, m.start() - 20):m.start() + 20]

            category = self._categorize_import(source)

            imp = LitImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_imports,
                import_category=category,
                is_type_import=is_type,
            )
            imports.append(imp)

        # ── Side-effect imports ───────────────────────────────────
        for m in self.SIDE_EFFECT_IMPORT.finditer(content):
            source = m.group(1)
            # Only capture lit-related side-effect imports
            if self._is_lit_import(source) and '{' not in content[m.start():m.end()]:
                line_num = content[:m.start()].count('\n') + 1
                # Check if already captured as named import
                if not any(i.source == source for i in imports):
                    imports.append(LitImportInfo(
                        source=source,
                        file=file_path,
                        line_number=line_num,
                        import_category=self._categorize_import(source),
                        is_side_effect=True,
                    ))

        # ── Integrations ──────────────────────────────────────────
        for name, pattern in self.INTEGRATION_PATTERNS.items():
            if pattern.search(content):
                line_num = 0
                m = pattern.search(content)
                if m:
                    line_num = content[:m.start()].count('\n') + 1
                integrations.append(LitIntegrationInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=self._categorize_integration(name),
                    source_package=name,
                ))

        # ── TypeScript types ──────────────────────────────────────
        if file_path.endswith('.ts'):
            seen_types = set()
            for m in self.TS_TYPE_USAGE.finditer(content):
                type_name = m.group(1)
                if type_name not in seen_types:
                    seen_types.add(type_name)
                    line_num = content[:m.start()].count('\n') + 1
                    types.append(LitTypeInfo(
                        type_name=type_name,
                        file=file_path,
                        line_number=line_num,
                    ))

        # ── SSR patterns ──────────────────────────────────────────
        for name, pattern in self.SSR_PATTERNS.items():
            if pattern.search(content):
                m = pattern.search(content)
                line_num = content[:m.start()].count('\n') + 1 if m else 0
                ssr_patterns.append(LitSSRInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    ssr_type=self._categorize_ssr(name),
                ))

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
            'ssr_patterns': ssr_patterns,
        }

    def _is_lit_import(self, source: str) -> bool:
        """Check if an import source is from the Lit ecosystem."""
        lit_prefixes = [
            'lit', 'lit-element', 'lit-html',
            '@lit', '@lit-labs',
            '@polymer', '@vaadin',
            '@open-wc', '@web',
            '@shoelace-style',
            '@spectrum-web-components',
            '@lion',
            '@material/web',
            '@carbon/web-components',
            '@patternfly',
            '@microsoft/fast-element',
            '@storybook/web-components',
        ]
        return any(source == prefix or source.startswith(prefix + '/') or source.startswith(prefix + '-')
                    for prefix in lit_prefixes)

    def _categorize_import(self, source: str) -> str:
        """Categorize an import source."""
        # Check exact matches first
        if source in self.IMPORT_CATEGORIES:
            return self.IMPORT_CATEGORIES[source]

        # Check prefix matches
        if source.startswith('lit/directives/'):
            return 'directives'
        if source.startswith('@lit-labs/'):
            return 'labs'
        if source.startswith('@lit/'):
            return 'core'
        if source.startswith('@polymer/'):
            return 'polymer'
        if source.startswith('@open-wc/') or source.startswith('@web/'):
            return 'tooling'
        if source.startswith('@vaadin/') or source.startswith('@shoelace'):
            return 'ui-library'
        if source.startswith('lit-element') or source.startswith('lit-html'):
            return 'core'
        if source.startswith('lit'):
            return 'core'

        return 'other'

    def _categorize_integration(self, name: str) -> str:
        """Categorize an integration."""
        ui_libs = {'vaadin', 'shoelace', 'spectrum-web-components', 'lion',
                    'material-web', 'carbon-web-components', 'patternfly-elements', 'fast-element'}
        tooling = {'open-wc-testing', 'open-wc-scoped-elements', 'web-dev-server',
                    'web-test-runner', 'web-component-analyzer', 'custom-elements-manifest',
                    'storybook-wc', 'rollup-plugin-lit-css', 'vite-plugin-lit-css'}
        if name in ui_libs:
            return 'ui-library'
        if name in tooling:
            return 'tooling'
        if name == 'polymer':
            return 'legacy'
        return 'other'

    def _categorize_ssr(self, name: str) -> str:
        """Categorize an SSR pattern."""
        if 'hydrate' in name:
            return 'client-hydrate'
        if 'shadow-dom' in name:
            return 'declarative-shadow-dom'
        return 'server-render'
