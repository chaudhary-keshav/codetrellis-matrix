"""
GSAP Timeline Extractor — Timelines, labels, callbacks, nesting.

Extracts:
- gsap.timeline() (v3+)
- TimelineMax / TimelineLite (v1-v2)
- Timeline methods: .to() / .from() / .fromTo() / .set() / .add() / .addLabel()
- Labels and position parameters
- Callbacks (onComplete, onUpdate, onStart, onRepeat)
- Nested timelines
- Timeline defaults
- Paused timelines and play/pause/reverse controls

v4.77: Full GSAP timeline support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GsapTimelineInfo:
    """A GSAP timeline definition."""
    name: str = ""                   # Variable name
    file: str = ""
    line_number: int = 0
    api_style: str = ""              # 'v3', 'v1', 'v2'
    tween_count: int = 0             # Number of chained tweens
    label_count: int = 0
    has_defaults: bool = False
    has_repeat: bool = False
    has_yoyo: bool = False
    has_paused: bool = False
    has_callbacks: bool = False
    has_nested: bool = False
    has_scrollTrigger: bool = False
    is_exported: bool = False


@dataclass
class GsapLabelInfo:
    """A timeline label."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    timeline_name: str = ""


@dataclass
class GsapCallbackInfo:
    """A GSAP callback (onComplete, onUpdate, etc.)."""
    callback_type: str = ""          # 'onComplete', 'onUpdate', 'onStart', 'onRepeat', 'onReverseComplete'
    file: str = ""
    line_number: int = 0
    handler_name: str = ""
    context: str = ""                # 'tween' or 'timeline'


@dataclass
class GsapNestedTimelineInfo:
    """A nested timeline reference."""
    parent_name: str = ""
    child_name: str = ""
    file: str = ""
    line_number: int = 0
    position: str = ""               # Position parameter


class GsapTimelineExtractor:
    """
    Extracts GSAP timeline constructs from JavaScript/TypeScript.

    Supports gsap.timeline() (v3+) and TimelineMax/TimelineLite (v1-v2).
    """

    # v3 gsap.timeline()
    GSAP_V3_TIMELINE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?gsap\.timeline\s*\(',
        re.MULTILINE
    )

    # v1/v2 TimelineMax / TimelineLite
    GSAP_LEGACY_TIMELINE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?new\s+(TimelineMax|TimelineLite)\s*\(',
        re.MULTILINE
    )

    # Timeline chained methods
    TIMELINE_METHOD = re.compile(
        r'\.(to|from|fromTo|set|add|addLabel|addPause|call)\s*\('
    )

    # Label pattern
    LABEL_PATTERN = re.compile(
        r'\.addLabel\s*\(\s*["\'](\w+)["\']'
    )

    # Timeline defaults
    DEFAULTS_PATTERN = re.compile(
        r'defaults\s*:\s*\{'
    )

    # Nested timeline: .add(otherTimeline)
    NESTED_PATTERN = re.compile(
        r'\.add\s*\(\s*(\w+)(?:\s*,\s*["\']?([^)"\']*)["\']?)?\s*\)'
    )

    # Callback pattern
    CALLBACK_PATTERN = re.compile(
        r'(onComplete|onUpdate|onStart|onRepeat|onReverseComplete)\s*:\s*(?:(\w+)|function|\()'
    )

    # Paused
    PAUSED_PATTERN = re.compile(r'paused\s*:\s*true')
    REPEAT_PATTERN = re.compile(r'repeat\s*:\s*(-?\d+)')
    YOYO_PATTERN = re.compile(r'yoyo\s*:\s*true')
    SCROLL_TRIGGER_PATTERN = re.compile(r'scrollTrigger\s*:')

    # Export detection
    EXPORT_PATTERN = re.compile(r'export\s+(?:const|let|var|function|default)')

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all GSAP timeline constructs from source code."""
        timelines = []
        labels = []
        callbacks = []
        nested = []

        # ── v3 gsap.timeline() ──────────────────────────────────
        for match in self.GSAP_V3_TIMELINE.finditer(content):
            var_name = match.group(1) or 'anonymous'
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 2000]

            tl = self._build_timeline(var_name, 'v3', ctx, file_path, line_num, content, match.start())
            timelines.append(tl)

            # Extract labels
            for lm in self.LABEL_PATTERN.finditer(ctx):
                labels.append(GsapLabelInfo(
                    name=lm.group(1),
                    file=file_path,
                    line_number=line_num + ctx[:lm.start()].count('\n'),
                    timeline_name=var_name,
                ))

            # Extract nested
            for nm in self.NESTED_PATTERN.finditer(ctx):
                child = nm.group(1)
                if child not in ('function', 'true', 'false', 'null', 'undefined') and not child.startswith('"') and not child.startswith("'"):
                    nested.append(GsapNestedTimelineInfo(
                        parent_name=var_name,
                        child_name=child,
                        file=file_path,
                        line_number=line_num + ctx[:nm.start()].count('\n'),
                        position=nm.group(2) or '',
                    ))

        # ── v1/v2 TimelineMax / TimelineLite ────────────────────
        for match in self.GSAP_LEGACY_TIMELINE.finditer(content):
            var_name = match.group(1) or 'anonymous'
            class_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 2000]

            api_style = 'v1' if class_name == 'TimelineMax' else 'v2'
            tl = self._build_timeline(var_name, api_style, ctx, file_path, line_num, content, match.start())
            timelines.append(tl)

            for lm in self.LABEL_PATTERN.finditer(ctx):
                labels.append(GsapLabelInfo(
                    name=lm.group(1),
                    file=file_path,
                    line_number=line_num + ctx[:lm.start()].count('\n'),
                    timeline_name=var_name,
                ))

        # ── Callbacks (standalone) ──────────────────────────────
        for match in self.CALLBACK_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            callbacks.append(GsapCallbackInfo(
                callback_type=match.group(1),
                file=file_path,
                line_number=line_num,
                handler_name=match.group(2) or 'inline',
                context='tween',
            ))

        return {
            'timelines': timelines[:50],
            'labels': labels[:100],
            'callbacks': callbacks[:100],
            'nested': nested[:50],
        }

    def _build_timeline(self, name: str, api_style: str, ctx: str,
                        file_path: str, line_num: int, full_content: str, offset: int) -> GsapTimelineInfo:
        """Build a GsapTimelineInfo from context."""
        # Count chained methods
        tween_count = len(self.TIMELINE_METHOD.findall(ctx))
        label_count = len(self.LABEL_PATTERN.findall(ctx))

        # Check if exported
        line_start = full_content.rfind('\n', 0, offset) + 1
        line_text = full_content[line_start:offset + 100]
        is_exported = bool(self.EXPORT_PATTERN.search(line_text[:100]))

        return GsapTimelineInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            api_style=api_style,
            tween_count=tween_count,
            label_count=label_count,
            has_defaults=bool(self.DEFAULTS_PATTERN.search(ctx)),
            has_repeat=bool(self.REPEAT_PATTERN.search(ctx)),
            has_yoyo=bool(self.YOYO_PATTERN.search(ctx)),
            has_paused=bool(self.PAUSED_PATTERN.search(ctx)),
            has_callbacks=bool(self.CALLBACK_PATTERN.search(ctx)),
            has_nested=bool(self.NESTED_PATTERN.search(ctx)),
            has_scrollTrigger=bool(self.SCROLL_TRIGGER_PATTERN.search(ctx)),
            is_exported=is_exported,
        )
