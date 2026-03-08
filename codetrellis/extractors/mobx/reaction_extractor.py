"""
MobX Reaction Extractor v1.0

Extracts MobX reaction definitions including:
- autorun() calls with options
- reaction() calls with data/effect functions and options
- when() calls with predicate/effect functions and options
- observe() calls for deep observation
- intercept() calls
- onBecomeObserved() / onBecomeUnobserved() callbacks
- Disposer patterns (stored disposers, cleanup in useEffect)
- Reaction options (delay, fireImmediately, scheduler, onError, signal)

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MobXReactionInfo:
    """Information about a MobX reaction."""
    name: str = ""
    file: str = ""
    line: int = 0
    reaction_type: str = ""  # 'autorun', 'reaction', 'when', 'observe', 'intercept',
                              # 'onBecomeObserved', 'onBecomeUnobserved'
    has_disposer: bool = False
    disposer_name: str = ""
    has_delay: bool = False
    has_fire_immediately: bool = False
    has_scheduler: bool = False
    has_on_error: bool = False
    has_signal: bool = False
    class_name: str = ""
    is_in_use_effect: bool = False


class MobXReactionExtractor:
    """Extracts MobX reaction definitions from source code."""

    # autorun(() => { ... }) / autorun(() => { ... }, { options })
    AUTORUN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?autorun\s*\(',
    )

    # reaction(() => data, (data, prev) => effect) / reaction(() => data, effect, options)
    REACTION = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?reaction\s*\(',
    )

    # when(() => predicate, () => effect) / when(() => predicate)
    WHEN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?when\s*\(',
    )

    # observe(observable, listener) / observe(observable, property, listener)
    OBSERVE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?observe\s*\(',
    )

    # intercept(observable, handler)
    INTERCEPT = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?intercept\s*\(',
    )

    # onBecomeObserved(observable, property?, handler)
    ON_BECOME_OBSERVED = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?onBecomeObserved\s*\(',
    )

    # onBecomeUnobserved(observable, property?, handler)
    ON_BECOME_UNOBSERVED = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?onBecomeUnobserved\s*\(',
    )

    # Detect useEffect context
    USE_EFFECT_CONTEXT = re.compile(
        r'useEffect\s*\(\s*\(\)\s*=>\s*\{',
    )

    # Class context
    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all MobX reaction definitions from source content.

        Returns:
            Dict with keys:
            - reactions: List[MobXReactionInfo]
        """
        reactions: List[MobXReactionInfo] = []

        class_ranges = self._find_class_ranges(content)
        use_effect_ranges = self._find_use_effect_ranges(content)

        # Extract each reaction type
        reaction_patterns = [
            (self.AUTORUN, 'autorun'),
            (self.REACTION, 'reaction'),
            (self.WHEN, 'when'),
            (self.OBSERVE, 'observe'),
            (self.INTERCEPT, 'intercept'),
            (self.ON_BECOME_OBSERVED, 'onBecomeObserved'),
            (self.ON_BECOME_UNOBSERVED, 'onBecomeUnobserved'),
        ]

        for pattern, reaction_type in reaction_patterns:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                disposer_name = match.group(1) or ''
                class_name = self._find_enclosing_class(match.start(), class_ranges)
                is_in_effect = self._is_in_use_effect(match.start(), use_effect_ranges)

                # Check for options in context after the match
                context_after = content[match.start():min(match.start() + 600, len(content))]
                has_delay = 'delay' in context_after
                has_fire_immediately = 'fireImmediately' in context_after
                has_scheduler = 'scheduler' in context_after
                has_on_error = 'onError' in context_after
                has_signal = 'signal' in context_after

                info = MobXReactionInfo(
                    name=disposer_name or f'{reaction_type}',
                    file=file_path,
                    line=line_num,
                    reaction_type=reaction_type,
                    has_disposer=bool(disposer_name),
                    disposer_name=disposer_name,
                    has_delay=has_delay,
                    has_fire_immediately=has_fire_immediately,
                    has_scheduler=has_scheduler,
                    has_on_error=has_on_error,
                    has_signal=has_signal,
                    class_name=class_name,
                    is_in_use_effect=is_in_effect,
                )
                reactions.append(info)

        return {
            'reactions': reactions,
        }

    def _find_use_effect_ranges(self, content: str) -> List[Dict[str, int]]:
        """Find useEffect callback ranges."""
        ranges = []
        for match in self.USE_EFFECT_CONTEXT.finditer(content):
            start = match.start()
            # Find matching closing brace
            depth = 0
            end = start
            for i in range(match.end() - 1, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            ranges.append({'start': start, 'end': end})
        return ranges

    def _is_in_use_effect(self, pos: int, use_effect_ranges: List[Dict]) -> bool:
        """Check if a position is inside a useEffect callback."""
        for r in use_effect_ranges:
            if r['start'] <= pos <= r['end']:
                return True
        return False

    def _find_class_ranges(self, content: str) -> List[Dict[str, Any]]:
        """Find class name and character ranges."""
        ranges = []
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            start = match.start()
            depth = 0
            end = start
            for i in range(match.end() - 1, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            ranges.append({'name': class_name, 'start': start, 'end': end})
        return ranges

    def _find_enclosing_class(self, pos: int, class_ranges: List[Dict]) -> str:
        """Find the class name enclosing a given character position."""
        for cr in class_ranges:
            if cr['start'] <= pos <= cr['end']:
                return cr['name']
        return ""
