"""
Preact Signal Extractor for CodeTrellis

Extracts Preact Signals usage patterns from JavaScript/TypeScript source code:
- signal(initialValue) / signal<T>(initialValue) — reactive state primitives
- computed(() => derivedValue) — derived computed values
- effect(() => sideEffect) — reactive side effects
- batch(() => { ... }) — batched updates for performance
- untracked(() => value) — read without tracking (v2)
- Signal<T> / ReadonlySignal<T> TypeScript types
- .value access patterns
- useSignal(initial) / useComputed(fn) — Preact-specific hook wrappers
- useSignalEffect(fn) — effect bound to component lifecycle

@preact/signals versions:
- v1.0: signal, computed, effect, batch
- v1.1+: improved TypeScript types, peek()
- v2.0: untracked, improved internals

@preact/signals-core:
- Low-level signal primitives (signal, computed, effect, batch)
- Framework-agnostic, usable without Preact

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PreactSignalInfo:
    """Information about a Preact signal() declaration."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # Signal<T> type parameter
    initial_value: str = ""
    is_exported: bool = False
    is_module_level: bool = False  # Declared at module level (global state)
    uses_peek: bool = False  # .peek() for untracked reads
    package: str = ""  # @preact/signals or @preact/signals-core


@dataclass
class PreactComputedInfo:
    """Information about a Preact computed() declaration."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    is_exported: bool = False
    dependencies: List[str] = field(default_factory=list)  # signals read inside


@dataclass
class PreactEffectInfo:
    """Information about a Preact effect() declaration."""
    name: str
    file: str = ""
    line_number: int = 0
    has_cleanup: bool = False
    signals_read: List[str] = field(default_factory=list)
    is_component_bound: bool = False  # useSignalEffect vs standalone effect


@dataclass
class PreactBatchInfo:
    """Information about a Preact batch() call."""
    file: str = ""
    line_number: int = 0
    enclosing_function: str = ""


class PreactSignalExtractor:
    """
    Extracts Preact Signals patterns from source code.

    Detects:
    - signal() / signal<T>() declarations
    - computed() derived state
    - effect() side effects
    - batch() grouped updates
    - useSignal / useComputed / useSignalEffect hook wrappers
    - .value access patterns
    - Module-level vs component-level signals
    - @preact/signals vs @preact/signals-core usage
    """

    # signal() declaration: const count = signal(0)
    SIGNAL_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*[^=]+?)?\s*=\s*'
        r'signal\s*(?:<\s*([^>]*)\s*>)?\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # useSignal() hook: const count = useSignal(0)
    USE_SIGNAL_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useSignal\s*(?:<\s*([^>]*)\s*>)?\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # computed() declaration: const doubled = computed(() => count.value * 2)
    COMPUTED_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'computed\s*(?:<\s*([^>]*)\s*>)?\s*\(',
        re.MULTILINE
    )

    # useComputed() hook
    USE_COMPUTED_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useComputed\s*(?:<\s*([^>]*)\s*>)?\s*\(',
        re.MULTILINE
    )

    # effect() declaration: effect(() => { ... })
    EFFECT_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'effect\s*\(\s*(?:async\s+)?(?:\(\)\s*=>|function)',
        re.MULTILINE
    )

    # useSignalEffect() hook
    USE_SIGNAL_EFFECT_PATTERN = re.compile(
        r'useSignalEffect\s*\(\s*(?:async\s+)?(?:\(\)\s*=>|function)',
        re.MULTILINE
    )

    # batch() call: batch(() => { ... })
    BATCH_PATTERN = re.compile(
        r'batch\s*\(\s*(?:async\s+)?(?:\(\)\s*=>|function)',
        re.MULTILINE
    )

    # .peek() usage for untracked reads
    PEEK_PATTERN = re.compile(
        r'(\w+)\.peek\s*\(\s*\)',
        re.MULTILINE
    )

    # .value access
    VALUE_ACCESS_PATTERN = re.compile(
        r'(\w+)\.value\b',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Preact Signals patterns from source code."""
        signals: List[PreactSignalInfo] = []
        computeds: List[PreactComputedInfo] = []
        effects: List[PreactEffectInfo] = []
        batches: List[PreactBatchInfo] = []

        # Determine package source
        package = ""
        if '@preact/signals-core' in content:
            package = "@preact/signals-core"
        elif '@preact/signals' in content:
            package = "@preact/signals"

        # Collect .peek() usages
        peek_vars = set(m.group(1) for m in self.PEEK_PATTERN.finditer(content))

        # ── signal() declarations ─────────────────────────────────
        for m in self.SIGNAL_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            initial = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            # Check if module-level (not indented, or before any function)
            line_start = content.rfind('\n', 0, m.start()) + 1
            indent = len(content[line_start:m.start()]) - len(content[line_start:m.start()].lstrip())
            is_module_level = indent == 0

            signals.append(PreactSignalInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                initial_value=initial.strip()[:50],
                is_exported=is_exported,
                is_module_level=is_module_level,
                uses_peek=name in peek_vars,
                package=package,
            ))

        # ── useSignal() hook calls ────────────────────────────────
        for m in self.USE_SIGNAL_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            initial = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            signals.append(PreactSignalInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                initial_value=initial.strip()[:50],
                is_exported=False,
                is_module_level=False,
                uses_peek=name in peek_vars,
                package=package,
            ))

        # ── computed() declarations ───────────────────────────────
        for m in self.COMPUTED_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            # Try to find .value accesses in the computed body
            body_end = min(len(content), m.end() + 500)
            body = content[m.end():body_end]
            deps = list(set(re.findall(r'(\w+)\.value\b', body)))

            computeds.append(PreactComputedInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_exported=is_exported,
                dependencies=deps[:10],
            ))

        # ── useComputed() hook calls ──────────────────────────────
        for m in self.USE_COMPUTED_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            body_end = min(len(content), m.end() + 500)
            body = content[m.end():body_end]
            deps = list(set(re.findall(r'(\w+)\.value\b', body)))

            computeds.append(PreactComputedInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_exported=False,
                dependencies=deps[:10],
            ))

        # ── effect() declarations ─────────────────────────────────
        for m in self.EFFECT_PATTERN.finditer(content):
            name = m.group(1) or "anonymous"
            line = content[:m.start()].count('\n') + 1

            body_end = min(len(content), m.end() + 500)
            body = content[m.end():body_end]
            has_cleanup = bool(re.search(r'return\s+(?:function|\(?\s*\)?\s*=>)', body))
            signals_read = list(set(re.findall(r'(\w+)\.value\b', body)))

            effects.append(PreactEffectInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_cleanup=has_cleanup,
                signals_read=signals_read[:10],
                is_component_bound=False,
            ))

        # ── useSignalEffect() hook calls ──────────────────────────
        for m in self.USE_SIGNAL_EFFECT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1

            body_end = min(len(content), m.end() + 500)
            body = content[m.end():body_end]
            has_cleanup = bool(re.search(r'return\s+(?:function|\(?\s*\)?\s*=>)', body))
            signals_read = list(set(re.findall(r'(\w+)\.value\b', body)))

            effects.append(PreactEffectInfo(
                name="useSignalEffect",
                file=file_path,
                line_number=line,
                has_cleanup=has_cleanup,
                signals_read=signals_read[:10],
                is_component_bound=True,
            ))

        # ── batch() calls ─────────────────────────────────────────
        for m in self.BATCH_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1

            # Find enclosing function
            before = content[max(0, m.start() - 1000):m.start()]
            func_match = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)', before)
            enclosing = ""
            if func_match:
                last = func_match[-1]
                enclosing = last[0] or last[1]

            batches.append(PreactBatchInfo(
                file=file_path,
                line_number=line,
                enclosing_function=enclosing,
            ))

        return {
            'signals': signals,
            'computeds': computeds,
            'effects': effects,
            'batches': batches,
        }
