"""
HTMX Event Extractor for CodeTrellis

Extracts HTMX event patterns from HTML and JavaScript source code:
- hx-trigger specifications: click, submit, load, revealed, intersect,
  every Ns, custom events, multiple triggers
- hx-trigger modifiers: changed, delay:Ns, throttle:Ns, from:selector,
  target:selector, consume, queue:first/last/all/none, once
- hx-on:event="handler" (v2 inline event syntax)
- hx-on::htmx-event="handler" (htmx: namespaced events)
- htmx lifecycle events in JavaScript: htmx:afterOnLoad, htmx:beforeRequest,
  htmx:afterRequest, htmx:beforeSwap, htmx:afterSwap, htmx:afterSettle,
  htmx:configRequest, htmx:load, htmx:responseError, htmx:sendError,
  htmx:sseMessage, htmx:wsConnecting, htmx:wsOpen, htmx:wsClose,
  htmx:wsError, htmx:historyCacheMiss, etc.
- document.addEventListener / htmx.on() event registrations

Supports:
- HTMX v1.x (htmx.on, document.addEventListener patterns)
- HTMX v2.x (hx-on:event, hx-on::htmx-event, improved event model)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HtmxEventInfo:
    """Information about an HTMX event pattern."""
    event_name: str  # click, submit, htmx:afterSwap, etc.
    file: str = ""
    line_number: int = 0
    event_type: str = ""  # trigger, lifecycle, inline, js_listener
    handler: str = ""  # The handler expression
    modifiers: List[str] = field(default_factory=list)  # changed, delay:1s, throttle:500ms, etc.
    source_element: str = ""  # from:selector
    is_htmx_event: bool = False  # htmx: namespaced event
    is_sse: bool = False  # SSE event
    is_ws: bool = False  # WebSocket event
    version_hint: str = ""  # v1, v2


class HtmxEventExtractor:
    """
    Extracts HTMX event patterns from source code.

    Detects hx-trigger specifications, hx-on inline event handlers,
    and JavaScript htmx event listeners.
    """

    # hx-trigger attribute pattern
    HX_TRIGGER_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?hx-trigger\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # hx-on:event="handler" pattern (v2)
    HX_ON_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?hx-on:([a-zA-Z][a-zA-Z0-9:.\-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # hx-on::htmx-event="handler" pattern (v2, htmx: namespaced)
    HX_ON_HTMX_PATTERN = re.compile(
        r"""(?:^|\s)(?:data-)?hx-on::([a-zA-Z][a-zA-Z0-9:.\-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""",
        re.MULTILINE
    )

    # JavaScript htmx.on() pattern
    HTMX_ON_JS_PATTERN = re.compile(
        r"""htmx\.on\(\s*(?:['"]([^'"]+)['"]\s*,\s*)?['"]([^'"]+)['"]\s*,""",
        re.MULTILINE
    )

    # document.addEventListener for htmx events
    DOC_LISTENER_PATTERN = re.compile(
        r"""(?:document|body|window)\.addEventListener\(\s*['"]([^'"]*htmx[^'"]*)['"]\s*,""",
        re.MULTILINE | re.IGNORECASE
    )

    # document.body.addEventListener for htmx events
    BODY_LISTENER_PATTERN = re.compile(
        r"""document\.body\.addEventListener\(\s*['"]([^'"]+)['"]\s*,""",
        re.MULTILINE
    )

    # Known htmx lifecycle events
    HTMX_LIFECYCLE_EVENTS = {
        'htmx:abort', 'htmx:afterOnLoad', 'htmx:afterProcessNode',
        'htmx:afterRequest', 'htmx:afterSettle', 'htmx:afterSwap',
        'htmx:beforeCleanupElement', 'htmx:beforeOnLoad',
        'htmx:beforeProcessNode', 'htmx:beforeRequest', 'htmx:beforeSend',
        'htmx:beforeSwap', 'htmx:beforeTransition', 'htmx:configRequest',
        'htmx:confirm', 'htmx:historyCacheMiss', 'htmx:historyCacheMissError',
        'htmx:historyCacheMissLoad', 'htmx:historyRestore',
        'htmx:beforeHistorySave', 'htmx:load', 'htmx:noSSESourceError',
        'htmx:onLoadError', 'htmx:oobAfterSwap', 'htmx:oobBeforeSwap',
        'htmx:oobErrorNoTarget', 'htmx:prompt', 'htmx:pushedIntoHistory',
        'htmx:replacedInHistory', 'htmx:responseError', 'htmx:sendError',
        'htmx:sseError', 'htmx:sseOpen', 'htmx:swapError',
        'htmx:targetError', 'htmx:timeout', 'htmx:trigger',
        'htmx:validateUrl', 'htmx:validation:failed',
        'htmx:validation:halted', 'htmx:validation:validate',
        'htmx:xhr:abort', 'htmx:xhr:loadend', 'htmx:xhr:loadstart',
        'htmx:xhr:progress',
    }

    # SSE-related events
    SSE_EVENTS = {
        'htmx:sseError', 'htmx:sseOpen', 'htmx:noSSESourceError',
        'sse-connect', 'sse-swap',
    }

    # WebSocket-related events
    WS_EVENTS = {
        'htmx:wsConnecting', 'htmx:wsOpen', 'htmx:wsClose',
        'htmx:wsError', 'htmx:wsBeforeMessage', 'htmx:wsAfterMessage',
        'htmx:wsConfigSend', 'htmx:wsBeforeSend', 'htmx:wsAfterSend',
        'ws-connect', 'ws-send',
    }

    # Trigger modifiers
    TRIGGER_MODIFIER_PATTERN = re.compile(
        r"""(changed|once|delay:\d+[ms]*|throttle:\d+[ms]*|from:[^\s,]+|target:[^\s,]+|consume|queue:(?:first|last|all|none))""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> List[HtmxEventInfo]:
        """Extract all HTMX event patterns from source code.

        Args:
            content: Source code content (HTML or JS/TS).
            file_path: Path to the source file.

        Returns:
            List of HtmxEventInfo objects.
        """
        if not content or not content.strip():
            return []

        results: List[HtmxEventInfo] = []
        lines = content.split('\n')

        # Extract hx-trigger specifications
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HX_TRIGGER_PATTERN.finditer(line):
                trigger_value = match.group(1) if match.group(1) is not None else (match.group(2) or "")
                self._parse_trigger_spec(trigger_value, file_path, line_idx, results)

        # Extract hx-on:event handlers (v2)
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HX_ON_PATTERN.finditer(line):
                event_name = match.group(1)
                handler = match.group(2) if match.group(2) is not None else (match.group(3) or "")

                # Skip double-colon patterns (handled next)
                if event_name.startswith(':'):
                    continue

                results.append(HtmxEventInfo(
                    event_name=event_name,
                    file=file_path,
                    line_number=line_idx,
                    event_type='inline',
                    handler=handler[:200],
                    is_htmx_event=event_name.startswith('htmx:') or event_name.startswith('htmx-'),
                    version_hint='v2',
                ))

        # Extract hx-on::htmx-event handlers (v2, htmx: namespaced)
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HX_ON_HTMX_PATTERN.finditer(line):
                event_name = match.group(1)
                handler = match.group(2) if match.group(2) is not None else (match.group(3) or "")

                full_event = f"htmx:{event_name}"

                results.append(HtmxEventInfo(
                    event_name=full_event,
                    file=file_path,
                    line_number=line_idx,
                    event_type='inline',
                    handler=handler[:200],
                    is_htmx_event=True,
                    version_hint='v2',
                ))

        # Extract JavaScript htmx.on() listeners
        for line_idx, line in enumerate(lines, start=1):
            for match in self.HTMX_ON_JS_PATTERN.finditer(line):
                event_name = match.group(2) if match.group(2) else match.group(1)
                if not event_name:
                    continue

                results.append(HtmxEventInfo(
                    event_name=event_name,
                    file=file_path,
                    line_number=line_idx,
                    event_type='js_listener',
                    is_htmx_event=event_name.startswith('htmx:'),
                    is_sse=event_name in self.SSE_EVENTS,
                    is_ws=event_name in self.WS_EVENTS,
                ))

        # Extract document.addEventListener for htmx events
        for line_idx, line in enumerate(lines, start=1):
            for match in self.DOC_LISTENER_PATTERN.finditer(line):
                event_name = match.group(1)
                results.append(HtmxEventInfo(
                    event_name=event_name,
                    file=file_path,
                    line_number=line_idx,
                    event_type='js_listener',
                    is_htmx_event=True,
                    is_sse=event_name in self.SSE_EVENTS,
                    is_ws=event_name in self.WS_EVENTS,
                ))

        # Extract document.body.addEventListener patterns
        for line_idx, line in enumerate(lines, start=1):
            for match in self.BODY_LISTENER_PATTERN.finditer(line):
                event_name = match.group(1)
                if 'htmx' not in event_name.lower():
                    continue
                results.append(HtmxEventInfo(
                    event_name=event_name,
                    file=file_path,
                    line_number=line_idx,
                    event_type='js_listener',
                    is_htmx_event=True,
                ))

        return results

    def _parse_trigger_spec(
        self, trigger_value: str, file_path: str, line_number: int,
        results: List[HtmxEventInfo]
    ) -> None:
        """Parse an hx-trigger value into individual event specs.

        hx-trigger can contain comma-separated triggers, each with modifiers.
        Examples:
          "click"
          "click, keyup delay:500ms changed"
          "every 2s"
          "load"
          "revealed"
          "intersect threshold:0.5"
          "click from:body"
          "click target:.child"
          "sse:message"

        Args:
            trigger_value: The hx-trigger attribute value.
            file_path: Path to the source file.
            line_number: Line number.
            results: List to append results to.
        """
        if not trigger_value:
            return

        # Split by comma for multiple triggers
        triggers = [t.strip() for t in trigger_value.split(',')]

        for trigger in triggers:
            if not trigger:
                continue

            parts = trigger.split()
            event_name = parts[0] if parts else trigger

            # Extract modifiers
            modifiers: List[str] = []
            for mod_match in self.TRIGGER_MODIFIER_PATTERN.finditer(trigger):
                modifiers.append(mod_match.group(1))

            # Detect SSE/WS
            is_sse = event_name.startswith('sse:') or event_name in self.SSE_EVENTS
            is_ws = event_name.startswith('ws:') or event_name in self.WS_EVENTS

            # Detect source element
            source_element = ""
            from_match = re.search(r'from:([^\s,]+)', trigger)
            if from_match:
                source_element = from_match.group(1)

            results.append(HtmxEventInfo(
                event_name=event_name,
                file=file_path,
                line_number=line_number,
                event_type='trigger',
                modifiers=modifiers,
                source_element=source_element,
                is_htmx_event=False,
                is_sse=is_sse,
                is_ws=is_ws,
            ))
