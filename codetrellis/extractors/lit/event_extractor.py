"""
Lit Event Extractor for CodeTrellis

Extracts Lit event handling patterns from JavaScript/TypeScript source code:
- CustomEvent dispatching (this.dispatchEvent(new CustomEvent(...)))
- @eventOptions decorator for passive/capture options
- Event listener bindings in templates (@click, @input, @change, etc.)
- addEventListener calls in lifecycle methods
- Event type declarations (declare events: EventMap)
- Fire event patterns (this.fire() in Polymer)

Supports:
- Polymer 1.x-3.x (fire(), on-event, listeners block)
- lit-element 2.x (dispatchEvent, @event bindings)
- lit 2.x-3.x (event bindings, @eventOptions)
- Vanilla Web Components (addEventListener, dispatchEvent)

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class LitEventInfo:
    """Information about a dispatched custom event."""
    name: str  # Event name (e.g., 'value-changed')
    file: str = ""
    line_number: int = 0
    event_class: str = "CustomEvent"  # CustomEvent, Event, etc.
    has_detail: bool = False
    has_bubbles: bool = False
    has_composed: bool = False
    has_cancelable: bool = False
    detail_type: str = ""  # TypeScript type for detail
    component_name: str = ""
    is_typed: bool = False  # Has TypeScript EventMap declaration


@dataclass
class LitEventListenerInfo:
    """Information about an event listener binding."""
    event_name: str  # click, input, custom-event, etc.
    file: str = ""
    line_number: int = 0
    handler_name: str = ""  # Method name handling the event
    binding_type: str = "template"  # template (@event), addEventListener, Polymer (on-event)
    has_options: bool = False  # @eventOptions or options param
    is_passive: bool = False
    is_capture: bool = False
    is_once: bool = False
    component_name: str = ""


class LitEventExtractor:
    """
    Extracts event handling patterns from Lit / Web Components source code.

    Detects:
    - this.dispatchEvent(new CustomEvent('name', { detail, bubbles, composed }))
    - @eventOptions({ passive: true }) handler()
    - Template event bindings: @click=${this.handler}
    - addEventListener('event', handler, options)
    - Polymer fire() and listeners block
    - TypeScript EventMap declarations
    """

    # Custom event dispatch
    DISPATCH_CUSTOM_EVENT = re.compile(
        r'(?:this\.)?dispatchEvent\s*\(\s*new\s+(\w*Event)\s*\(\s*'
        r'[\'"]([a-zA-Z][a-zA-Z0-9-]*)[\'"]'
        r'(?:\s*,\s*(\{[^}]*\}))?',
        re.MULTILINE
    )

    # @eventOptions decorator
    EVENT_OPTIONS_DECORATOR = re.compile(
        r'@eventOptions\s*\(\s*(\{[^}]*\})\s*\)\s*'
        r'(?:(?:private|protected|public)\s+)?'
        r'(\w+)',
        re.MULTILINE
    )

    # Template event bindings: @click=${this._onClick}
    TEMPLATE_EVENT_BINDING = re.compile(
        r'@([a-z][a-z0-9-]*)\s*=\s*\$\{(?:this\.)?(\w+)',
        re.MULTILINE
    )

    # addEventListener
    ADD_EVENT_LISTENER = re.compile(
        r'(?:this\.)?addEventListener\s*\(\s*'
        r'[\'"]([a-zA-Z][a-zA-Z0-9-]*)[\'"]'
        r'\s*,\s*(?:this\.)?(\w+)',
        re.MULTILINE
    )

    # Polymer fire()
    POLYMER_FIRE = re.compile(
        r'this\.fire\s*\(\s*[\'"]([a-zA-Z][a-zA-Z0-9-]*)[\'"]',
        re.MULTILINE
    )

    # Polymer listeners block
    POLYMER_LISTENERS = re.compile(
        r'listeners\s*:\s*\{([^}]*)\}',
        re.MULTILINE
    )

    # TypeScript event declaration
    TS_EVENT_MAP = re.compile(
        r'(?:declare\s+)?(?:interface|type)\s+(\w*Events?\w*)\s*(?:extends\s+\w+\s*)?\{([^}]*)\}',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract event information from source code.

        Returns dict with keys: events, listeners
        """
        events: List[LitEventInfo] = []
        listeners: List[LitEventListenerInfo] = []

        # ── Custom event dispatches ───────────────────────────────
        for m in self.DISPATCH_CUSTOM_EVENT.finditer(content):
            event_class = m.group(1) or "Event"
            event_name = m.group(2)
            options_str = m.group(3) or ""
            line_num = content[:m.start()].count('\n') + 1

            evt = LitEventInfo(
                name=event_name,
                file=file_path,
                line_number=line_num,
                event_class=event_class,
                has_detail='detail' in options_str,
                has_bubbles='bubbles' in options_str,
                has_composed='composed' in options_str,
                has_cancelable='cancelable' in options_str,
            )
            events.append(evt)

        # ── Polymer fire() calls ──────────────────────────────────
        for m in self.POLYMER_FIRE.finditer(content):
            event_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            evt = LitEventInfo(
                name=event_name,
                file=file_path,
                line_number=line_num,
                event_class="CustomEvent",
                has_bubbles=True,  # Polymer fire() bubbles by default
                has_composed=True,
            )
            events.append(evt)

        # ── Template event bindings ───────────────────────────────
        for m in self.TEMPLATE_EVENT_BINDING.finditer(content):
            event_name = m.group(1)
            handler_name = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            listener = LitEventListenerInfo(
                event_name=event_name,
                file=file_path,
                line_number=line_num,
                handler_name=handler_name,
                binding_type="template",
            )
            listeners.append(listener)

        # ── @eventOptions decorators ──────────────────────────────
        for m in self.EVENT_OPTIONS_DECORATOR.finditer(content):
            options_str = m.group(1)
            handler_name = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            # Update any matching listener
            for l in listeners:
                if l.handler_name == handler_name:
                    l.has_options = True
                    l.is_passive = 'passive' in options_str and 'true' in options_str
                    l.is_capture = 'capture' in options_str and 'true' in options_str

        # ── addEventListener calls ────────────────────────────────
        for m in self.ADD_EVENT_LISTENER.finditer(content):
            event_name = m.group(1)
            handler_name = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            listener = LitEventListenerInfo(
                event_name=event_name,
                file=file_path,
                line_number=line_num,
                handler_name=handler_name,
                binding_type="addEventListener",
            )
            listeners.append(listener)

        # ── Polymer listeners block ───────────────────────────────
        for m in self.POLYMER_LISTENERS.finditer(content):
            block = m.group(1)
            base_line = content[:m.start()].count('\n') + 1
            for entry in re.finditer(r"['\"]([^'\"]+)['\"]\s*:\s*['\"](\w+)['\"]", block):
                event_name = entry.group(1)
                handler_name = entry.group(2)
                listener = LitEventListenerInfo(
                    event_name=event_name,
                    file=file_path,
                    line_number=base_line,
                    handler_name=handler_name,
                    binding_type="polymer-listeners",
                )
                listeners.append(listener)

        return {
            'events': events,
            'listeners': listeners,
        }
