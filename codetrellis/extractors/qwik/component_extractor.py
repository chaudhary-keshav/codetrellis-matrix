"""
Qwik Component Extractor for CodeTrellis

Extracts Qwik component definitions and patterns:
- component$() wrapper (the core Qwik component pattern)
- Inline components (plain arrow functions without component$)
- <Slot /> content projection
- Polymorphic components (as prop pattern)
- TypeScript PropsOf<> / Component generics
- Event handler props (onClick$, onInput$, etc.)
- Ref forwarding (useSignal<Element>)
- Exported vs non-exported components
- Default export detection

Supports:
- Qwik v0.x (component$, useClientEffect$)
- Qwik v1.x (component$, useSignal, useVisibleTask$)
- Qwik v2.x (@qwik.dev/core, improved component$ types)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikComponentInfo:
    """Information about a Qwik component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    component_type: str = ""  # component$, inline, polymorphic
    props_type: str = ""  # TypeScript props interface/type
    has_slot: bool = False
    has_ref: bool = False
    is_exported: bool = False
    is_default_export: bool = False
    event_handlers: List[str] = field(default_factory=list)  # onClick$, onInput$, etc.
    signals_used: List[str] = field(default_factory=list)
    tasks_used: List[str] = field(default_factory=list)
    has_jsx: bool = True


@dataclass
class QwikSlotInfo:
    """Information about Qwik <Slot> usage."""
    file: str = ""
    line_number: int = 0
    parent_component: str = ""
    slot_name: str = ""  # named slot or default
    has_fallback: bool = False


class QwikComponentExtractor:
    """
    Extracts Qwik component definitions from source code.

    Detects:
    - component$() wrapper declarations
    - Inline components (without component$)
    - TypeScript Component<Props> annotations
    - PropsOf<> type utility
    - <Slot> content projection
    - Event handlers (onClick$, onInput$, etc.)
    - Ref usage (useSignal<Element>)
    - Export patterns (export default, export const)
    """

    # component$() pattern: export const Name = component$(() => { ... })
    COMPONENT_DOLLAR_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)\s*'
        r'=\s*component\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # export default component$(() => { ... }) without named variable
    DEFAULT_COMPONENT_DOLLAR_PATTERN = re.compile(
        r'export\s+default\s+component\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Inline component (plain function, not wrapped in component$)
    INLINE_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*\w+\s*)?=\s*\(([^)]*)\)\s*(?::\s*\w+)?\s*=>\s*(?:\{|<)',
        re.MULTILINE
    )

    # <Slot> usage
    SLOT_PATTERN = re.compile(
        r'<Slot\b([^>]*?)(?:/>|>)',
        re.MULTILINE
    )

    # Event handler patterns: onClick$, onInput$, onChange$, etc.
    EVENT_HANDLER_PATTERN = re.compile(
        r'\bon(\w+)\$\s*=\s*\{',
        re.MULTILINE
    )

    # useSignal<Element> ref pattern
    REF_PATTERN = re.compile(
        r'useSignal\s*<\s*(?:HTML\w*Element|Element)\s*>',
        re.MULTILINE
    )

    # PropsOf<> type usage
    PROPSOF_PATTERN = re.compile(
        r'PropsOf\s*<\s*[\'"]?(\w+)[\'"]?\s*>',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik component definitions from source code."""
        components: List[QwikComponentInfo] = []
        slots: List[QwikSlotInfo] = []

        # ── component$() declarations ────────────────────────────
        for m in self.COMPONENT_DOLLAR_PATTERN.finditer(content):
            name = m.group(1)
            props_type = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            # Determine export status
            prefix = content[max(0, m.start() - 40):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            # Check component body for patterns
            body_end = min(len(content), m.end() + 3000)
            body = content[m.end():body_end]

            # Detect <Slot>
            has_slot = bool(self.SLOT_PATTERN.search(body))

            # Detect ref
            has_ref = bool(self.REF_PATTERN.search(body))

            # Detect event handlers
            event_handlers = list(set(
                f"on{eh.group(1)}$" for eh in self.EVENT_HANDLER_PATTERN.finditer(body)
            ))

            # Detect signals and tasks used
            signals = re.findall(r'\b(useSignal|useStore|useComputed\$)\b', body)
            unique_signals = list(dict.fromkeys(signals))

            tasks = re.findall(r'\b(useTask\$|useVisibleTask\$|useResource\$)\b', body)
            unique_tasks = list(dict.fromkeys(tasks))

            components.append(QwikComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="component$",
                props_type=props_type,
                has_slot=has_slot,
                has_ref=has_ref,
                is_exported=is_exported,
                is_default_export=is_default,
                event_handlers=event_handlers,
                signals_used=unique_signals,
                tasks_used=unique_tasks,
            ))

        # ── export default component$() without name ──────────────
        for m in self.DEFAULT_COMPONENT_DOLLAR_PATTERN.finditer(content):
            # Skip if already captured as named component
            already_captured = any(
                c.line_number == content[:m.start()].count('\n') + 1
                for c in components
            )
            if already_captured:
                continue

            props_type = m.group(1) or ""
            line = content[:m.start()].count('\n') + 1

            body_end = min(len(content), m.end() + 3000)
            body = content[m.end():body_end]

            has_slot = bool(self.SLOT_PATTERN.search(body))
            has_ref = bool(self.REF_PATTERN.search(body))
            event_handlers = list(set(
                f"on{eh.group(1)}$" for eh in self.EVENT_HANDLER_PATTERN.finditer(body)
            ))

            components.append(QwikComponentInfo(
                name="default",
                file=file_path,
                line_number=line,
                component_type="component$",
                props_type=props_type,
                has_slot=has_slot,
                has_ref=has_ref,
                is_exported=True,
                is_default_export=True,
                event_handlers=event_handlers,
            ))

        # ── Inline components ─────────────────────────────────────
        for m in self.INLINE_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)

            # Skip lowercase names (not components) and already found
            if name[0].islower():
                continue

            # Skip if already captured as component$
            if any(c.name == name for c in components):
                continue

            line = content[:m.start()].count('\n') + 1
            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            components.append(QwikComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="inline",
                is_exported=is_exported,
                is_default_export=False,
            ))

        # ── <Slot> extraction ─────────────────────────────────────
        for m in self.SLOT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            attrs = m.group(1)

            slot_name = ""
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attrs)
            if name_match:
                slot_name = name_match.group(1)

            # Find parent component
            parent = ""
            for comp in components:
                if comp.line_number < line:
                    parent = comp.name

            slots.append(QwikSlotInfo(
                file=file_path,
                line_number=line,
                parent_component=parent,
                slot_name=slot_name,
            ))

        return {
            "components": components,
            "slots": slots,
        }
