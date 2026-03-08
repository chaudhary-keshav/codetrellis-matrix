"""
CSS Animation Extractor for CodeTrellis

Extracts @keyframes definitions, transition declarations,
animation usage, and scroll-driven animations.

Supports:
- CSS3 @keyframes (named animations)
- CSS3 transitions
- CSS3 animation shorthand and individual properties
- CSS Scroll-driven Animations (scroll-timeline, view-timeline)
- Animation composition and iteration
- Will-change optimization hints
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSKeyframeInfo:
    """Information about a @keyframes definition."""
    name: str
    file: str = ""
    line_number: int = 0
    keyframe_stops: List[str] = field(default_factory=list)  # 0%, 50%, 100%, from, to
    properties_animated: List[str] = field(default_factory=list)
    is_vendor_prefixed: bool = False


@dataclass
class CSSTransitionInfo:
    """Information about a CSS transition declaration."""
    property_name: str = "all"
    duration: str = ""
    timing_function: str = ""
    delay: str = ""
    file: str = ""
    line_number: int = 0
    selector: str = ""


@dataclass
class CSSAnimationUsageInfo:
    """Information about CSS animation usage."""
    animation_name: str
    file: str = ""
    line_number: int = 0
    duration: str = ""
    timing_function: str = ""
    delay: str = ""
    iteration_count: str = ""
    direction: str = ""
    fill_mode: str = ""
    play_state: str = ""
    selector: str = ""
    is_scroll_driven: bool = False
    timeline: str = ""


class CSSAnimationExtractor:
    """
    Extracts CSS animations, transitions, and keyframes.

    Detects:
    - @keyframes definitions with all stops
    - Transition declarations
    - Animation usage with full property parsing
    - Scroll-driven animation timelines
    - will-change declarations
    - Vendor-prefixed keyframes
    """

    KEYFRAMES_PATTERN = re.compile(
        r'@(-webkit-|-moz-)?keyframes\s+([\w-]+)\s*\{',
        re.MULTILINE
    )

    TRANSITION_PATTERN = re.compile(
        r'transition\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    ANIMATION_PATTERN = re.compile(
        r'animation(?:-name)?\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    ANIMATION_TIMELINE_PATTERN = re.compile(
        r'animation-timeline\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    SCROLL_TIMELINE_PATTERN = re.compile(
        r'scroll-timeline(?:-name|-axis)?\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    VIEW_TIMELINE_PATTERN = re.compile(
        r'view-timeline(?:-name|-axis|-inset)?\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    WILL_CHANGE_PATTERN = re.compile(
        r'will-change\s*:\s*([^;{}]+?)\s*;',
        re.MULTILINE
    )

    KEYFRAME_STOP_PATTERN = re.compile(
        r'(\d+%|from|to)\s*\{([^}]+)\}',
        re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all animation-related information from CSS source.

        Returns dict with:
          - keyframes: List[CSSKeyframeInfo]
          - transitions: List[CSSTransitionInfo]
          - animations: List[CSSAnimationUsageInfo]
          - will_change: List[Dict]
          - stats: Dict
        """
        keyframes: List[CSSKeyframeInfo] = []
        transitions: List[CSSTransitionInfo] = []
        animations: List[CSSAnimationUsageInfo] = []
        will_change: List[Dict] = []

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        # Extract @keyframes
        for match in self.KEYFRAMES_PATTERN.finditer(clean):
            prefix = match.group(1) or ""
            name = match.group(2)
            line_num = clean[:match.start()].count('\n') + 1

            # Extract the body
            body = self._extract_block_body(clean, match.end())
            stops = []
            props_animated = set()

            for stop_match in self.KEYFRAME_STOP_PATTERN.finditer(body):
                stops.append(stop_match.group(1))
                # Extract property names from stop body
                stop_body = stop_match.group(2)
                for prop_match in re.finditer(r'([\w-]+)\s*:', stop_body):
                    props_animated.add(prop_match.group(1))

            keyframes.append(CSSKeyframeInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                keyframe_stops=stops,
                properties_animated=sorted(props_animated),
                is_vendor_prefixed=bool(prefix),
            ))

        # Extract transitions
        for match in self.TRANSITION_PATTERN.finditer(clean):
            value = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1

            # Parse transition shorthand (property duration timing-function delay)
            parts = [p.strip() for p in value.split(',')]
            for part in parts:
                tokens = part.split()
                prop = tokens[0] if tokens else "all"
                duration = tokens[1] if len(tokens) > 1 else ""
                timing = tokens[2] if len(tokens) > 2 else ""
                delay = tokens[3] if len(tokens) > 3 else ""

                transitions.append(CSSTransitionInfo(
                    property_name=prop,
                    duration=duration,
                    timing_function=timing,
                    delay=delay,
                    file=file_path,
                    line_number=line_num,
                ))

        # Extract animation usage
        for match in self.ANIMATION_PATTERN.finditer(clean):
            value = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1

            # Check for scroll-driven timeline near this animation
            is_scroll_driven = False
            timeline = ""
            nearby = clean[max(0, match.start()-200):match.start()+200]
            tl_match = self.ANIMATION_TIMELINE_PATTERN.search(nearby)
            if tl_match:
                timeline = tl_match.group(1).strip()
                is_scroll_driven = 'scroll' in timeline or 'view' in timeline

            # Parse animation names (could be comma-separated)
            anim_names = [n.strip().split()[0] for n in value.split(',') if n.strip()]
            for anim_name in anim_names:
                if anim_name in ('none', 'initial', 'inherit', 'unset', 'revert'):
                    continue
                animations.append(CSSAnimationUsageInfo(
                    animation_name=anim_name,
                    file=file_path,
                    line_number=line_num,
                    is_scroll_driven=is_scroll_driven,
                    timeline=timeline,
                ))

        # Extract will-change
        for match in self.WILL_CHANGE_PATTERN.finditer(clean):
            value = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1
            will_change.append({
                "properties": [p.strip() for p in value.split(',')],
                "file": file_path,
                "line": line_num,
            })

        # Detect scroll-driven timelines (standalone, without animation shorthand)
        has_scroll_timeline = bool(self.SCROLL_TIMELINE_PATTERN.search(clean))
        has_view_timeline = bool(self.VIEW_TIMELINE_PATTERN.search(clean))
        has_animation_timeline = bool(self.ANIMATION_TIMELINE_PATTERN.search(clean))
        has_any_scroll_driven = (
            has_scroll_timeline or has_view_timeline or has_animation_timeline or
            any(a.is_scroll_driven for a in animations)
        )

        stats = {
            "total_keyframes": len(keyframes),
            "total_transitions": len(transitions),
            "total_animations": len(animations),
            "scroll_driven_animations": sum(1 for a in animations if a.is_scroll_driven),
            "will_change_count": len(will_change),
            "has_scroll_driven": has_any_scroll_driven,
            "has_will_change": len(will_change) > 0,
        }

        return {
            "keyframes": keyframes,
            "transitions": transitions,
            "animations": animations,
            "will_change": will_change,
            "stats": stats,
        }

    def _extract_block_body(self, content: str, start: int) -> str:
        """Extract the body of a brace-delimited block."""
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        return content[start:pos - 1] if pos > start else ""
