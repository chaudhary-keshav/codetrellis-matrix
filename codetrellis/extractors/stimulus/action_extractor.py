"""
Stimulus Action Extractor for CodeTrellis

Extracts Stimulus action definitions from HTML and JavaScript/TypeScript:
- data-action HTML attributes with action descriptors
- Action descriptor parsing: event->controller#method
- Action parameters: data-*-param attributes
- Action options: :prevent, :stop, :self, :once (v3.x)
- Keyboard filters: keydown.enter, keydown.esc, etc.
- Global actions: @window, @document

Supports:
- Stimulus v1.x (basic data-action)
- Stimulus v2.x (action parameters via data-*-*-param)
- Stimulus v3.x (action options :prevent/:stop/:self/:once, outlets)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StimulusActionInfo:
    """Information about a Stimulus action definition."""
    descriptor: str  # Full action descriptor (e.g., "click->search#perform")
    file: str = ""
    line_number: int = 0
    event_name: str = ""  # click, submit, input, change, etc.
    controller_name: str = ""  # Controller identifier (e.g., "search")
    method_name: str = ""  # Method name (e.g., "perform")
    action_type: str = ""  # html_attribute, inline
    has_prevent: bool = False  # :prevent option (v3.x)
    has_stop: bool = False  # :stop option (v3.x)
    has_self: bool = False  # :self option (v3.x)
    has_once: bool = False  # :once option (v3.x)
    has_passive: bool = False  # :passive option
    has_capture: bool = False  # :capture option
    is_global: bool = False  # @window or @document target
    global_target: str = ""  # "window" or "document"
    keyboard_filter: str = ""  # e.g., "enter", "esc", "space"
    params: List[str] = field(default_factory=list)  # Action parameters
    version_hint: str = ""  # v1, v2, v3


# HTML: data-action="event->controller#method"
# Can be multi-action: "click->ctrl#a keydown.enter->ctrl#b"
HTML_ACTION_PATTERN = re.compile(
    r'data-action\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)

# Individual action descriptor: event->controller#method:option
ACTION_DESCRIPTOR_PATTERN = re.compile(
    r'(?:(?P<event>[\w.]+)'  # Event name (with optional keyboard filter)
    r'(?:@(?P<global>\w+))?'  # Optional @window/@document
    r'->)?'  # Arrow separator
    r'(?P<controller>[\w-]+)'  # Controller identifier
    r'#(?P<method>\w+)'  # Method name
    r'(?::(?P<options>[\w:]+))?'  # Options like :prevent:stop
)

# Action parameters: data-controller-name-param="value"
ACTION_PARAM_PATTERN = re.compile(
    r'data-(?P<controller>[\w-]+)-(?P<param>[\w-]+)-param\s*=\s*["\'](?P<value>[^"\']*)["\']',
    re.IGNORECASE
)


class StimulusActionExtractor:
    """Extracts Stimulus action definitions from HTML and JavaScript/TypeScript code."""

    def extract(self, content: str, file_path: str = "") -> List[StimulusActionInfo]:
        """Extract Stimulus action definitions from source code or HTML.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusActionInfo objects.
        """
        if not content or not content.strip():
            return []

        actions: List[StimulusActionInfo] = []

        # Extract data-action attributes
        for attr_match in HTML_ACTION_PATTERN.finditer(content):
            attr_value = attr_match.group(1)
            line = content[:attr_match.start()].count('\n') + 1

            # Parse individual action descriptors (space-separated)
            descriptors = attr_value.strip().split()
            for desc_str in descriptors:
                desc_match = ACTION_DESCRIPTOR_PATTERN.match(desc_str.strip())
                if desc_match:
                    event = desc_match.group('event') or ''
                    global_target = desc_match.group('global') or ''
                    controller = desc_match.group('controller') or ''
                    method = desc_match.group('method') or ''
                    options_str = desc_match.group('options') or ''

                    # Parse keyboard filters (e.g., keydown.enter -> filter=enter)
                    keyboard_filter = ""
                    if '.' in event:
                        parts = event.split('.')
                        event = parts[0]
                        keyboard_filter = '.'.join(parts[1:])

                    # Parse options
                    options = options_str.split(':') if options_str else []
                    has_prevent = 'prevent' in options
                    has_stop = 'stop' in options
                    has_self = 'self' in options
                    has_once = 'once' in options
                    has_passive = 'passive' in options
                    has_capture = 'capture' in options

                    # Version hints from features
                    version_hint = ""
                    if any([has_prevent, has_stop, has_self, has_once]):
                        version_hint = "v3"
                    elif keyboard_filter:
                        version_hint = "v2"

                    actions.append(StimulusActionInfo(
                        descriptor=desc_str.strip(),
                        file=file_path,
                        line_number=line,
                        event_name=event,
                        controller_name=controller,
                        method_name=method,
                        action_type="html_attribute",
                        has_prevent=has_prevent,
                        has_stop=has_stop,
                        has_self=has_self,
                        has_once=has_once,
                        has_passive=has_passive,
                        has_capture=has_capture,
                        is_global=bool(global_target),
                        global_target=global_target,
                        keyboard_filter=keyboard_filter,
                        version_hint=version_hint,
                    ))

        # Extract action parameters
        params_by_controller: dict = {}
        for param_match in ACTION_PARAM_PATTERN.finditer(content):
            controller = param_match.group('controller')
            param = param_match.group('param')
            params_by_controller.setdefault(controller, []).append(param)

        # Associate params with actions
        for action in actions:
            ctrl_params = params_by_controller.get(action.controller_name, [])
            if ctrl_params:
                action.params = ctrl_params[:15]

        return actions
