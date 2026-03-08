"""
Alpine.js Directive Extractor for CodeTrellis

Extracts Alpine.js directive usage from HTML and JavaScript/TypeScript source code:
- Core directives: x-data, x-bind/:, x-on/@, x-model, x-show, x-if, x-for,
  x-transition, x-effect, x-ref, x-text, x-html, x-init, x-cloak
- Structure directives: x-teleport, x-ignore, x-id
- Plugin directives: x-trap, x-intersect, x-anchor, x-sort, x-collapse, x-mask, x-resize
- Modifier detection: .prevent, .stop, .window, .document, .self, .away, .once,
  .debounce, .throttle, .camel, .dot, .passive, .capture
- Shorthand syntax: :attr (x-bind), @event (x-on)
- Alpine.js v1.x legacy directives (x-spread)

Supports:
- HTML files with Alpine.js attributes
- JavaScript/TypeScript files with Alpine.data() template strings
- Alpine.js v1.x, v2.x, v3.x directive syntax

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class AlpineDirectiveInfo:
    """Information about an Alpine.js directive usage."""
    directive_name: str  # x-data, x-bind, x-on, x-model, etc.
    file: str = ""
    line_number: int = 0
    directive_value: str = ""  # The value/expression of the directive
    modifiers: List[str] = field(default_factory=list)  # .prevent, .stop, .window, etc.
    bound_attribute: str = ""  # For x-bind: the attribute being bound (e.g., class, style)
    event_name: str = ""  # For x-on: the event name (e.g., click, submit)
    is_shorthand: bool = False  # : for x-bind, @ for x-on
    version_hint: str = ""  # v1, v2, v3 (based on directive features)


class AlpineDirectiveExtractor:
    """
    Extracts Alpine.js directive usages from source code.

    Detects all Alpine.js directives in HTML attributes and
    JavaScript template strings, including shorthand syntax
    and modifiers.
    """

    # Core directives pattern in HTML attributes
    # Matches: x-data="..." x-bind:attr="..." :attr="..." x-on:event="..." @event="..."
    DIRECTIVE_PATTERN = re.compile(
        r"""(?:^|\s)"""
        r"""(x-(?:data|bind|on|model|show|if|for|transition|effect|ref|text|html|init|cloak|"""
        r"""teleport|ignore|id|trap|intersect|anchor|sort|collapse|mask|resize|spread|"""
        r"""modelable))"""
        r"""(?::([a-zA-Z0-9\-_.]+))?"""  # :attribute (for x-bind:class, x-on:click)
        r"""(?:\.([a-zA-Z0-9.]+))?"""  # .modifiers
        r"""(?:\s*=\s*"([^"]*)")?""",  # ="value"
        re.MULTILINE
    )

    # Shorthand patterns: :class="..." @click="..."
    SHORTHAND_BIND_PATTERN = re.compile(
        r"""(?:^|\s):([a-zA-Z0-9\-_.]+)"""
        r"""(?:\.([a-zA-Z0-9.]+))?"""
        r"""(?:\s*=\s*"([^"]*)")?""",
        re.MULTILINE
    )

    SHORTHAND_EVENT_PATTERN = re.compile(
        r"""(?:^|\s)@([a-zA-Z0-9\-_.]+)"""
        r"""(?:\.([a-zA-Z0-9.]+))?"""
        r"""(?:\s*=\s*"([^"]*)")?""",
        re.MULTILINE
    )

    # x-for pattern (special: "item in items" or "(item, index) in items")
    X_FOR_PATTERN = re.compile(
        r"""x-for\s*=\s*"([^"]+)"\s*""",
        re.MULTILINE
    )

    # x-transition modifiers
    TRANSITION_MODIFIERS = {
        'enter', 'enter-start', 'enter-end',
        'leave', 'leave-start', 'leave-end',
        'duration', 'delay', 'opacity', 'scale',
    }

    # Version-specific directives
    V1_ONLY_DIRECTIVES = {'x-spread'}
    V3_ONLY_DIRECTIVES = {'x-effect', 'x-teleport', 'x-ignore', 'x-id', 'x-modelable'}
    PLUGIN_DIRECTIVES = {'x-trap', 'x-intersect', 'x-anchor', 'x-sort', 'x-collapse', 'x-mask', 'x-resize'}

    def extract(self, content: str, file_path: str = "") -> List[AlpineDirectiveInfo]:
        """Extract all Alpine.js directive usages from source code.

        Args:
            content: Source code content (HTML or JS/TS).
            file_path: Path to the source file.

        Returns:
            List of AlpineDirectiveInfo objects.
        """
        directives: List[AlpineDirectiveInfo] = []

        lines = content.split('\n')
        for line_idx, line in enumerate(lines, start=1):
            # Full directive syntax: x-directive:arg.mod="value"
            for match in self.DIRECTIVE_PATTERN.finditer(line):
                directive_name = match.group(1)
                bound_attr = match.group(2) or ""
                modifier_str = match.group(3) or ""
                value = match.group(4) or ""

                modifiers = [m for m in modifier_str.split('.') if m] if modifier_str else []
                event_name = ""

                if directive_name == 'x-on':
                    event_name = bound_attr
                    bound_attr = ""
                elif directive_name == 'x-bind':
                    pass  # bound_attr is the attribute

                version_hint = self._detect_version_hint(directive_name)

                directives.append(AlpineDirectiveInfo(
                    directive_name=directive_name,
                    file=file_path,
                    line_number=line_idx,
                    directive_value=value,
                    modifiers=modifiers,
                    bound_attribute=bound_attr,
                    event_name=event_name,
                    is_shorthand=False,
                    version_hint=version_hint,
                ))

            # Shorthand :bind patterns (but not :: or :// or CSS selectors)
            for match in self.SHORTHAND_BIND_PATTERN.finditer(line):
                attr = match.group(1)
                modifier_str = match.group(2) or ""
                value = match.group(3) or ""

                # Skip CSS pseudo-selectors and URLs
                pos = match.start()
                if pos > 0 and line[pos] == ':' and pos > 0 and line[pos - 1] == ':':
                    continue

                modifiers = [m for m in modifier_str.split('.') if m] if modifier_str else []

                directives.append(AlpineDirectiveInfo(
                    directive_name="x-bind",
                    file=file_path,
                    line_number=line_idx,
                    directive_value=value,
                    modifiers=modifiers,
                    bound_attribute=attr,
                    event_name="",
                    is_shorthand=True,
                    version_hint="",
                ))

            # Shorthand @event patterns (but not @ in email addresses)
            for match in self.SHORTHAND_EVENT_PATTERN.finditer(line):
                event = match.group(1)
                modifier_str = match.group(2) or ""
                value = match.group(3) or ""

                modifiers = [m for m in modifier_str.split('.') if m] if modifier_str else []

                directives.append(AlpineDirectiveInfo(
                    directive_name="x-on",
                    file=file_path,
                    line_number=line_idx,
                    directive_value=value,
                    modifiers=modifiers,
                    bound_attribute="",
                    event_name=event,
                    is_shorthand=True,
                    version_hint="",
                ))

        return directives

    def _detect_version_hint(self, directive_name: str) -> str:
        """Detect Alpine.js version hint from directive name.

        Args:
            directive_name: The directive name (e.g., 'x-effect').

        Returns:
            Version hint string (e.g., 'v3').
        """
        if directive_name in self.V1_ONLY_DIRECTIVES:
            return "v1"
        if directive_name in self.V3_ONLY_DIRECTIVES:
            return "v3"
        if directive_name in self.PLUGIN_DIRECTIVES:
            return "v3"
        return ""
