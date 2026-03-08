"""
Qwik API Extractor for CodeTrellis

Extracts Qwik API usage patterns:
- Import patterns (@builder.io/qwik, @builder.io/qwik-city, @qwik.dev/core, @qwik.dev/router)
- Event handlers (onClick$, onInput$, useOn, useOnWindow, useOnDocument)
- Style hooks (useStyles$, useStylesScoped$)
- SSR patterns (SSRStream, SSRStreamBlock, renderToString, renderToStream)
- TypeScript types (Signal, ReadonlySignal, QRL, NoSerialize, PropsOf, JSXOutput)
- Ecosystem integrations (qwik-ui, modular-forms, qwik-speak, auth.js, etc.)

Supports:
- Qwik v0.x (early import paths)
- Qwik v1.x (@builder.io/qwik, @builder.io/qwik-city)
- Qwik v2.x (@qwik.dev/core, @qwik.dev/router)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikImportInfo:
    """Information about a Qwik ecosystem import."""
    source: str  # e.g. @builder.io/qwik, @builder.io/qwik-city
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    has_default_import: bool = False
    import_category: str = ""  # core, city, router, ui, testing, etc.


@dataclass
class QwikEventHandlerInfo:
    """Information about Qwik event handler usage."""
    handler_name: str  # onClick$, onInput$, etc.
    file: str = ""
    line_number: int = 0
    handler_type: str = ""  # jsx_prop, useOn, useOnWindow, useOnDocument


@dataclass
class QwikStyleInfo:
    """Information about Qwik style hook usage."""
    style_type: str  # useStyles$, useStylesScoped$
    file: str = ""
    line_number: int = 0


@dataclass
class QwikIntegrationInfo:
    """Information about Qwik ecosystem integration."""
    name: str
    file: str = ""
    line_number: int = 0
    integration_type: str = ""  # ui, forms, i18n, auth, testing, build, etc.
    source_package: str = ""


@dataclass
class QwikTypeInfo:
    """Information about Qwik TypeScript type usage."""
    type_name: str  # Signal, ReadonlySignal, QRL, NoSerialize, PropsOf, etc.
    file: str = ""
    line_number: int = 0
    source: str = ""  # import source


class QwikApiExtractor:
    """
    Extracts Qwik API patterns from source code.

    Detects:
    - Import statements from Qwik ecosystem packages
    - Event handler patterns (JSX props, useOn/useOnWindow/useOnDocument)
    - Style hooks (useStyles$, useStylesScoped$)
    - SSR patterns (SSRStream, SSRStreamBlock)
    - TypeScript type annotations (Signal<T>, QRL, etc.)
    - Ecosystem integrations (qwik-ui, modular-forms, qwik-speak, etc.)
    """

    # Import pattern: import { ... } from '...'
    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?(?:(\w+)\s*,?\s*)?(?:\{([^}]*)\})?\s+from\s+['\"]([^'\"]+)['\"])",
        re.MULTILINE
    )

    # Event handler JSX props: onClick$, onInput$, onChange$, onKeyDown$, etc.
    JSX_EVENT_HANDLER_PATTERN = re.compile(
        r'\b(on\w+\$)\s*=\s*\{',
        re.MULTILINE
    )

    # useOn / useOnWindow / useOnDocument
    USE_ON_PATTERN = re.compile(
        r'\b(useOn|useOnWindow|useOnDocument)\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # useStyles$ / useStylesScoped$
    USE_STYLES_PATTERN = re.compile(
        r'\b(useStyles\$|useStylesScoped\$)\s*\(',
        re.MULTILINE
    )

    # Qwik TypeScript types
    QWIK_TYPE_PATTERN = re.compile(
        r'\b(Signal|ReadonlySignal|QRL|NoSerialize|PropsOf|JSXOutput|'
        r'JSXNode|FunctionComponent|Component|QwikIntrinsicElements|'
        r'QwikJSX|QwikChangeEvent|QwikFocusEvent|QwikKeyboardEvent|'
        r'QwikMouseEvent|QwikSubmitEvent|ResourceReturn|TaskCtx|'
        r'VisibleTaskStrategy|EagernessOptions|ResourceCtx|'
        r'RequestHandler|RequestEvent|RequestEventBase|Cookie|'
        r'DeferReturn|DocumentHead|ResolvedDocumentHead|ContentMenu)\b',
        re.MULTILINE
    )

    # SSR patterns
    SSR_PATTERN = re.compile(
        r'\b(SSRStream|SSRStreamBlock|SSRComment|SSRHint|'
        r'renderToString|renderToStream|isServer|isBrowser)\b',
        re.MULTILINE
    )

    # Qwik ecosystem packages
    QWIK_PACKAGES = {
        '@builder.io/qwik': 'core',
        '@builder.io/qwik-city': 'city',
        '@builder.io/qwik/build': 'build',
        '@builder.io/qwik/server': 'server',
        '@builder.io/qwik/optimizer': 'optimizer',
        '@builder.io/qwik/testing': 'testing',
        '@qwik.dev/core': 'core',
        '@qwik.dev/router': 'router',
        'qwik-ui': 'ui',
        '@qwik-ui/headless': 'ui',
        '@qwik-ui/styled': 'ui',
        '@modular-forms/qwik': 'forms',
        'qwik-speak': 'i18n',
        '@auth/qwik': 'auth',
        'qwik-auth': 'auth',
        '@builder.io/qwik-auth': 'auth',
        'qwik-image': 'media',
        '@unpic/qwik': 'media',
        'qwik-lottie': 'animation',
        'qwik-icon': 'icon',
        'qwik-ionicons': 'icon',
        '@fontsource-variable': 'fonts',
        'valibot': 'validation',
        'zod': 'validation',
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik API patterns from source code."""
        imports: List[QwikImportInfo] = []
        event_handlers: List[QwikEventHandlerInfo] = []
        styles: List[QwikStyleInfo] = []
        integrations: List[QwikIntegrationInfo] = []
        types: List[QwikTypeInfo] = []

        # ── Imports ──────────────────────────────────────────────
        for m in self.IMPORT_PATTERN.finditer(content):
            default_import = m.group(1) or ""
            named_str = m.group(2) or ""
            source = m.group(3)
            line = content[:m.start()].count('\n') + 1

            # Only track Qwik-related imports
            is_qwik = any(
                source.startswith(pkg) or source == pkg
                for pkg in self.QWIK_PACKAGES
            )
            if not is_qwik:
                continue

            # Parse named imports
            named_imports = [
                n.strip().split(' as ')[0].strip()
                for n in named_str.split(',')
                if n.strip()
            ]

            category = ""
            for pkg, cat in self.QWIK_PACKAGES.items():
                if source.startswith(pkg) or source == pkg:
                    category = cat
                    break

            imports.append(QwikImportInfo(
                source=source,
                file=file_path,
                line_number=line,
                named_imports=named_imports,
                has_default_import=bool(default_import),
                import_category=category,
            ))

            # Also track as integration if not core
            if category not in ('core', 'city', 'router', 'build', 'server', 'optimizer', 'testing'):
                integrations.append(QwikIntegrationInfo(
                    name=source.split('/')[-1],
                    file=file_path,
                    line_number=line,
                    integration_type=category,
                    source_package=source,
                ))

        # ── Event handlers (JSX) ──────────────────────────────────
        for m in self.JSX_EVENT_HANDLER_PATTERN.finditer(content):
            handler = m.group(1)
            line = content[:m.start()].count('\n') + 1

            event_handlers.append(QwikEventHandlerInfo(
                handler_name=handler,
                file=file_path,
                line_number=line,
                handler_type="jsx_prop",
            ))

        # ── Event handlers (useOn*) ───────────────────────────────
        for m in self.USE_ON_PATTERN.finditer(content):
            hook = m.group(1)
            event = m.group(2)
            line = content[:m.start()].count('\n') + 1

            event_handlers.append(QwikEventHandlerInfo(
                handler_name=f"{hook}:{event}",
                file=file_path,
                line_number=line,
                handler_type=hook,
            ))

        # ── Styles ────────────────────────────────────────────────
        for m in self.USE_STYLES_PATTERN.finditer(content):
            style_type = m.group(1)
            line = content[:m.start()].count('\n') + 1

            styles.append(QwikStyleInfo(
                style_type=style_type,
                file=file_path,
                line_number=line,
            ))

        # ── Types ─────────────────────────────────────────────────
        seen_types: set = set()
        for m in self.QWIK_TYPE_PATTERN.finditer(content):
            type_name = m.group(1)
            if type_name in seen_types:
                continue
            seen_types.add(type_name)

            line = content[:m.start()].count('\n') + 1

            types.append(QwikTypeInfo(
                type_name=type_name,
                file=file_path,
                line_number=line,
            ))

        return {
            "imports": imports,
            "event_handlers": event_handlers,
            "styles": styles,
            "integrations": integrations,
            "types": types,
        }
