"""
Qwik Task & Lifecycle Extractor for CodeTrellis

Extracts Qwik task and lifecycle patterns:
- useTask$(() => { track, cleanup }) — runs on server and client
- useVisibleTask$(() => { ... }) — runs only in browser after visible
- useResource$(() => { track, cleanup }) — async data loading
- <Resource> component for rendering resource states
- track(() => signal.value) explicit dependency tracking
- cleanup(() => teardown) cleanup function

Supports:
- Qwik v0.x (useWatch$, useClientEffect$ — deprecated names)
- Qwik v1.x (useTask$, useVisibleTask$, useResource$)
- Qwik v2.x (@qwik.dev/core, same API)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikTaskInfo:
    """Information about a Qwik task (useTask$, useVisibleTask$)."""
    file: str = ""
    line_number: int = 0
    task_type: str = ""  # useTask$, useVisibleTask$, useWatch$, useClientEffect$
    has_track: bool = False
    has_cleanup: bool = False
    is_eager: bool = False  # { eagerness: 'visible' | 'load' | 'idle' }
    eagerness: str = ""  # visible, load, idle
    strategy: str = ""  # intersection-observer, document-ready, document-idle


@dataclass
class QwikResourceInfo:
    """Information about a Qwik resource (useResource$)."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # TypeScript type for resource value
    has_track: bool = False
    has_cleanup: bool = False
    is_exported: bool = False
    has_resource_component: bool = False  # Uses <Resource> to render


class QwikTaskExtractor:
    """
    Extracts Qwik task and lifecycle patterns from source code.

    Detects:
    - useTask$(() => { ... }) server + client task
    - useVisibleTask$(() => { ... }) browser-only task after element visible
    - useResource$<T>(() => { ... }) async resource loading
    - <Resource value={...} onPending={...} onResolved={...} />
    - track() / cleanup() usage within tasks
    - Eagerness options: { eagerness: 'visible' | 'load' | 'idle' }
    - Legacy: useWatch$, useClientEffect$ (Qwik v0.x)
    """

    # useTask$(() => { ... })
    USE_TASK_PATTERN = re.compile(
        r'useTask\$\s*\(',
        re.MULTILINE
    )

    # useVisibleTask$(() => { ... })
    USE_VISIBLE_TASK_PATTERN = re.compile(
        r'useVisibleTask\$\s*\(',
        re.MULTILINE
    )

    # useWatch$ (legacy v0.x)
    USE_WATCH_PATTERN = re.compile(
        r'useWatch\$\s*\(',
        re.MULTILINE
    )

    # useClientEffect$ (legacy v0.x)
    USE_CLIENT_EFFECT_PATTERN = re.compile(
        r'useClientEffect\$\s*\(',
        re.MULTILINE
    )

    # useResource$<T>(() => { ... })
    USE_RESOURCE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useResource\$\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # <Resource> component usage
    RESOURCE_COMPONENT_PATTERN = re.compile(
        r'<Resource\b([^>]*?)(?:/>|>)',
        re.MULTILINE
    )

    # track() usage
    TRACK_PATTERN = re.compile(
        r'\btrack\s*\(',
        re.MULTILINE
    )

    # cleanup() usage
    CLEANUP_PATTERN = re.compile(
        r'\bcleanup\s*\(',
        re.MULTILINE
    )

    # Eagerness option
    EAGERNESS_PATTERN = re.compile(
        r'eagerness\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Strategy option (useVisibleTask$ strategy)
    STRATEGY_PATTERN = re.compile(
        r'strategy\s*:\s*[\'"]([\w-]+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik task and lifecycle patterns from source code."""
        tasks: List[QwikTaskInfo] = []
        resources: List[QwikResourceInfo] = []

        # ── useTask$ ─────────────────────────────────────────────
        for m in self.USE_TASK_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]

            has_track = bool(self.TRACK_PATTERN.search(body))
            has_cleanup = bool(self.CLEANUP_PATTERN.search(body))

            eagerness = ""
            eager_match = self.EAGERNESS_PATTERN.search(body)
            if eager_match:
                eagerness = eager_match.group(1)

            tasks.append(QwikTaskInfo(
                file=file_path,
                line_number=line,
                task_type="useTask$",
                has_track=has_track,
                has_cleanup=has_cleanup,
                is_eager=bool(eagerness),
                eagerness=eagerness,
            ))

        # ── useVisibleTask$ ──────────────────────────────────────
        for m in self.USE_VISIBLE_TASK_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]

            has_track = bool(self.TRACK_PATTERN.search(body))
            has_cleanup = bool(self.CLEANUP_PATTERN.search(body))

            eagerness = ""
            eager_match = self.EAGERNESS_PATTERN.search(body)
            if eager_match:
                eagerness = eager_match.group(1)

            strategy = ""
            strat_match = self.STRATEGY_PATTERN.search(body)
            if strat_match:
                strategy = strat_match.group(1)

            tasks.append(QwikTaskInfo(
                file=file_path,
                line_number=line,
                task_type="useVisibleTask$",
                has_track=has_track,
                has_cleanup=has_cleanup,
                is_eager=bool(eagerness),
                eagerness=eagerness,
                strategy=strategy,
            ))

        # ── useWatch$ (legacy) ────────────────────────────────────
        for m in self.USE_WATCH_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]

            tasks.append(QwikTaskInfo(
                file=file_path,
                line_number=line,
                task_type="useWatch$",
                has_track=bool(self.TRACK_PATTERN.search(body)),
                has_cleanup=bool(self.CLEANUP_PATTERN.search(body)),
            ))

        # ── useClientEffect$ (legacy) ─────────────────────────────
        for m in self.USE_CLIENT_EFFECT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            body_end = min(len(content), m.end() + 1000)
            body = content[m.end():body_end]

            tasks.append(QwikTaskInfo(
                file=file_path,
                line_number=line,
                task_type="useClientEffect$",
                has_track=bool(self.TRACK_PATTERN.search(body)),
                has_cleanup=bool(self.CLEANUP_PATTERN.search(body)),
            ))

        # ── useResource$ ─────────────────────────────────────────
        for m in self.USE_RESOURCE_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            body_end = min(len(content), m.end() + 1500)
            body = content[m.end():body_end]

            has_track = bool(self.TRACK_PATTERN.search(body))
            has_cleanup = bool(self.CLEANUP_PATTERN.search(body))

            # Check if <Resource value={name}> is used
            has_resource_comp = bool(re.search(
                rf'<Resource\b[^>]*value\s*=\s*\{{\s*{re.escape(name)}\b',
                content
            ))

            resources.append(QwikResourceInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                has_track=has_track,
                has_cleanup=has_cleanup,
                is_exported=is_exported,
                has_resource_component=has_resource_comp,
            ))

        return {
            "tasks": tasks,
            "resources": resources,
        }
