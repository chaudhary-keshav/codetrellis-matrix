"""
Qwik Signal & State Extractor for CodeTrellis

Extracts Qwik reactive state primitives:
- useSignal(initialValue) -> Signal<T> with .value access
- useStore(initialObject, options?) -> deep/shallow reactive store
- useComputed$(() => derived) -> ReadonlySignal<T>
- Signal<T>, ReadonlySignal<T> type annotations

Supports:
- Qwik v0.x (useStore, useWatch$)
- Qwik v1.x (useSignal, useComputed$, deep: false option)
- Qwik v2.x (@qwik.dev/core, improved signal types)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikSignalInfo:
    """Information about a Qwik signal (useSignal)."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # TypeScript type T in useSignal<T>()
    initial_value: str = ""  # The initial value expression
    is_exported: bool = False
    is_element_ref: bool = False  # useSignal<HTMLElement>()


@dataclass
class QwikStoreInfo:
    """Information about a Qwik store (useStore)."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    is_deep: bool = True  # default is deep reactivity
    is_exported: bool = False
    initial_fields: List[str] = field(default_factory=list)
    has_methods: bool = False  # QRL methods on store


@dataclass
class QwikComputedInfo:
    """Information about a Qwik computed value (useComputed$)."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    is_exported: bool = False


class QwikSignalExtractor:
    """
    Extracts Qwik reactive state from source code.

    Detects:
    - useSignal<T>(initialValue) -> Signal<T>
    - useStore<T>(initialObject, { deep: false })
    - useComputed$(() => derivedValue) -> ReadonlySignal<T>
    - Element refs via useSignal<HTMLElement>()
    """

    # useSignal<T>(initialValue)
    USE_SIGNAL_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useSignal\s*(?:<([^>]*)>)?\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # useStore<T>(initialObject, options?)
    USE_STORE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useStore\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useComputed$(() => ...)
    USE_COMPUTED_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useComputed\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Deep option detection: { deep: false }
    DEEP_FALSE_PATTERN = re.compile(
        r'\{\s*deep\s*:\s*false\s*\}',
        re.MULTILINE
    )

    # Element ref detection
    ELEMENT_REF_PATTERN = re.compile(
        r'useSignal\s*<\s*(?:HTML\w*Element|Element|SVG\w*Element)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik reactive state from source code."""
        signals: List[QwikSignalInfo] = []
        stores: List[QwikStoreInfo] = []
        computeds: List[QwikComputedInfo] = []

        # ── useSignal ─────────────────────────────────────────────
        for m in self.USE_SIGNAL_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            initial = m.group(3).strip()
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            # Check if element ref
            is_ref = bool(re.search(
                r'HTML\w*Element|^Element$|SVG\w*Element',
                type_ann
            ))

            signals.append(QwikSignalInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                initial_value=initial,
                is_exported=is_exported,
                is_element_ref=is_ref,
            ))

        # ── useStore ──────────────────────────────────────────────
        for m in self.USE_STORE_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            # Check for deep: false in the subsequent text
            body_end = min(len(content), m.end() + 500)
            body = content[m.end():body_end]
            is_deep = not bool(self.DEEP_FALSE_PATTERN.search(body))

            # Extract initial fields from object literal
            initial_fields: List[str] = []
            field_matches = re.findall(r'(\w+)\s*:', body[:200])
            initial_fields = field_matches[:10]

            # Check for QRL methods
            has_methods = bool(re.search(r'\$\s*\(', body[:500]))

            stores.append(QwikStoreInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_deep=is_deep,
                is_exported=is_exported,
                initial_fields=initial_fields,
                has_methods=has_methods,
            ))

        # ── useComputed$ ──────────────────────────────────────────
        for m in self.USE_COMPUTED_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            computeds.append(QwikComputedInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_exported=is_exported,
            ))

        return {
            "signals": signals,
            "stores": stores,
            "computeds": computeds,
        }
