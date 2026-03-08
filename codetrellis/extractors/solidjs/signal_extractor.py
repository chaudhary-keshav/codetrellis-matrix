"""
Solid.js Signal & Reactivity Extractor for CodeTrellis

Extracts Solid.js reactive primitives:
- createSignal (getter/setter pairs)
- createMemo (derived computations)
- createEffect (side effects)
- createComputed (synchronous computations, deprecated in v2)
- createRenderEffect (render-phase effects)
- createReaction (explicit tracking)
- on() wrapper for explicit dependency tracking
- batch() for batched updates
- untrack() for untracked access
- createRoot() for root scopes
- createDeferred() for deferred signals (v1.1+)
- startTransition / useTransition (v1.1+)
- observable() for interop with RxJS-style observables
- from() for wrapping external reactive sources (v1.4+)
- mapArray / indexArray (reactive list mapping)

Supports:
- Solid.js v1.0-v2.0 full reactivity primitive API
- TypeScript generic annotations on signals
- Accessor<T> / Setter<T> types

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidSignalInfo:
    """Information about a Solid.js signal (createSignal)."""
    name: str  # The getter name
    setter_name: str = ""  # The setter name (setX)
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # TypeScript type T in createSignal<T>()
    initial_value: str = ""  # The initial value expression
    has_options: bool = False  # { equals: false } etc.
    is_exported: bool = False
    signal_type: str = "signal"  # signal, deferred


@dataclass
class SolidMemoInfo:
    """Information about a Solid.js memo (createMemo)."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    dependencies: List[str] = field(default_factory=list)  # Signals accessed
    is_exported: bool = False


@dataclass
class SolidEffectInfo:
    """Information about a Solid.js effect (createEffect, createRenderEffect, createComputed, createReaction)."""
    name: str
    file: str = ""
    line_number: int = 0
    effect_type: str = ""  # createEffect, createRenderEffect, createComputed, createReaction
    has_on_wrapper: bool = False  # Uses on() for explicit deps
    dependencies: List[str] = field(default_factory=list)
    is_deferred: bool = False  # defer: true option


@dataclass
class SolidReactiveUtilInfo:
    """Information about Solid.js reactive utility usage."""
    name: str  # batch, untrack, createRoot, startTransition, observable, from, mapArray, indexArray
    file: str = ""
    line_number: int = 0
    util_type: str = ""


class SolidSignalExtractor:
    """
    Extracts Solid.js reactive primitive usage from source code.

    Detects:
    - createSignal(initialValue) -> [getter, setter]
    - createMemo(() => computation)
    - createEffect(() => sideEffect)
    - createComputed(() => syncComputation)
    - createRenderEffect(() => renderEffect)
    - createReaction(tracking, effect)
    - on(deps, effect) explicit dependency tracking
    - batch(() => { ... }) batched updates
    - untrack(() => value) untracked access
    - createRoot(dispose => { ... }) manual root scopes
    - createDeferred(source, options) deferred signals (v1.1+)
    - startTransition / useTransition concurrent features (v1.1+)
    - observable(signal) RxJS interop
    - from(producer) external source wrapping (v1.4+)
    - mapArray / indexArray reactive list utilities
    """

    # createSignal<T>(initialValue, options?)
    CREATE_SIGNAL_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+\[(\w+),\s*(\w+)\]\s*=\s*'
        r'createSignal\s*(?:<([^>]*)>)?\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # createMemo<T>(() => ...)
    CREATE_MEMO_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createMemo\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # createEffect(() => ...)
    CREATE_EFFECT_PATTERN = re.compile(
        r'createEffect\s*\(',
        re.MULTILINE
    )

    # createRenderEffect(() => ...)
    CREATE_RENDER_EFFECT_PATTERN = re.compile(
        r'createRenderEffect\s*\(',
        re.MULTILINE
    )

    # createComputed(() => ...)
    CREATE_COMPUTED_PATTERN = re.compile(
        r'createComputed\s*\(',
        re.MULTILINE
    )

    # createReaction(tracking, effect)
    CREATE_REACTION_PATTERN = re.compile(
        r'createReaction\s*\(',
        re.MULTILINE
    )

    # on(deps, fn) wrapper
    ON_WRAPPER_PATTERN = re.compile(
        r'\bon\s*\(\s*(?:\[([^\]]*)\]|(\w+))\s*,',
        re.MULTILINE
    )

    # batch(() => { ... })
    BATCH_PATTERN = re.compile(
        r'batch\s*\(\s*\(\)\s*=>',
        re.MULTILINE
    )

    # untrack(() => ...)
    UNTRACK_PATTERN = re.compile(
        r'untrack\s*\(\s*\(\)\s*=>',
        re.MULTILINE
    )

    # createRoot(dispose => { ... })
    CREATE_ROOT_PATTERN = re.compile(
        r'createRoot\s*\(',
        re.MULTILINE
    )

    # createDeferred(source, options)
    CREATE_DEFERRED_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*createDeferred\s*\(',
        re.MULTILINE
    )

    # startTransition / useTransition
    TRANSITION_PATTERN = re.compile(
        r'(?:startTransition|useTransition)\s*\(',
        re.MULTILINE
    )

    # observable(accessor)
    OBSERVABLE_PATTERN = re.compile(
        r'observable\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # from(producer)
    FROM_PATTERN = re.compile(
        r'from\s*\(\s*(?:(?:\w+)|(?:\([^)]*\)\s*=>))',
        re.MULTILINE
    )

    # mapArray / indexArray
    MAP_ARRAY_PATTERN = re.compile(
        r'(mapArray|indexArray)\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js reactive primitives from source code."""
        signals = []
        memos = []
        effects = []
        reactive_utils = []

        # ── Signals ───────────────────────────────────────────────
        for m in self.CREATE_SIGNAL_PATTERN.finditer(content):
            getter = m.group(1)
            setter = m.group(2)
            type_ann = m.group(3) or ""
            initial = m.group(4).strip() if m.group(4) else ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            # Check for options object (equals, name)
            has_options = ',' in initial and '{' in initial

            signals.append(SolidSignalInfo(
                name=getter,
                setter_name=setter,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                initial_value=initial.split(',')[0].strip() if ',' in initial and '{' in initial else initial,
                has_options=has_options,
                is_exported=is_exported,
            ))

        # ── Deferred signals ──────────────────────────────────────
        for m in self.CREATE_DEFERRED_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            signals.append(SolidSignalInfo(
                name=name,
                file=file_path,
                line_number=line,
                signal_type="deferred",
            ))

        # ── Memos ─────────────────────────────────────────────────
        for m in self.CREATE_MEMO_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            memos.append(SolidMemoInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                is_exported=is_exported,
            ))

        # ── Effects ───────────────────────────────────────────────
        effect_patterns = [
            (self.CREATE_EFFECT_PATTERN, "createEffect"),
            (self.CREATE_RENDER_EFFECT_PATTERN, "createRenderEffect"),
            (self.CREATE_COMPUTED_PATTERN, "createComputed"),
            (self.CREATE_REACTION_PATTERN, "createReaction"),
        ]

        for pattern, effect_type in effect_patterns:
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1

                # Check for on() wrapper in nearby code
                body = content[m.end():min(len(content), m.end() + 200)]
                has_on = bool(re.match(r'\s*on\s*\(', body))

                # Check for defer option
                is_deferred = 'defer' in body[:100] if body else False

                effects.append(SolidEffectInfo(
                    name=effect_type,
                    file=file_path,
                    line_number=line,
                    effect_type=effect_type,
                    has_on_wrapper=has_on,
                    is_deferred=is_deferred,
                ))

        # ── Reactive utilities ────────────────────────────────────
        util_patterns = [
            (self.BATCH_PATTERN, "batch"),
            (self.UNTRACK_PATTERN, "untrack"),
            (self.CREATE_ROOT_PATTERN, "createRoot"),
            (self.TRANSITION_PATTERN, "transition"),
        ]

        for pattern, util_type in util_patterns:
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                reactive_utils.append(SolidReactiveUtilInfo(
                    name=util_type,
                    file=file_path,
                    line_number=line,
                    util_type=util_type,
                ))

        # observable()
        for m in self.OBSERVABLE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            reactive_utils.append(SolidReactiveUtilInfo(
                name="observable",
                file=file_path,
                line_number=line,
                util_type="observable",
            ))

        # from()
        for m in self.FROM_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            reactive_utils.append(SolidReactiveUtilInfo(
                name="from",
                file=file_path,
                line_number=line,
                util_type="from",
            ))

        # mapArray / indexArray
        for m in self.MAP_ARRAY_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            reactive_utils.append(SolidReactiveUtilInfo(
                name=m.group(1),
                file=file_path,
                line_number=line,
                util_type=m.group(1),
            ))

        return {
            "signals": signals,
            "memos": memos,
            "effects": effects,
            "reactive_utils": reactive_utils,
        }
