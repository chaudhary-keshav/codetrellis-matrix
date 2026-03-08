"""
XState Action Extractor for CodeTrellis

Extracts XState action definitions and usage patterns:
- assign (context updates)
- send / sendTo / raise (event dispatching)
- log (logging actions)
- stop / cancel (actor lifecycle)
- pure / choose (conditional actions)
- forwardTo / escalate / respond (v4)
- enqueueActions (v5 - queued actions)
- emit (v5 - event emission)
- Custom named actions
- Inline action functions
- Action creators (action factories)

Supports:
- XState v3.x (actions, onEntry/onExit, assign)
- XState v4.x (send, sendTo, pure, choose, escalate, respond, forwardTo)
- XState v5.x (enqueueActions, emit, sendTo updates, raise updates)

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class XstateActionInfo:
    """Information about an XState action."""
    name: str
    file: str = ""
    line_number: int = 0
    action_type: str = ""  # assign, send, sendTo, raise, log, stop, cancel,
                           # pure, choose, forwardTo, escalate, respond,
                           # enqueueActions, emit, custom, inline
    is_named: bool = False  # named action vs inline
    assigned_properties: List[str] = field(default_factory=list)  # for assign actions
    event_type: str = ""  # for send/raise actions - the event being sent
    target_actor: str = ""  # for sendTo - the target actor
    is_v5: bool = False  # Uses v5 API
    description: str = ""


class XstateActionExtractor:
    """
    Extracts XState action definitions from source code.

    Detects:
    - assign() context update actions
    - send()/sendTo()/raise() event dispatch actions
    - log() logging actions
    - stop()/cancel() actor lifecycle
    - pure()/choose() conditional actions
    - forwardTo/escalate/respond (v4)
    - enqueueActions/emit (v5)
    - Custom named action functions
    - Inline action usage
    """

    # assign() pattern - standalone or imported
    ASSIGN_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?assign\s*(?:<[^>]*>)?\s*\(\s*(?:\{|[\(])',
        re.MULTILINE
    )

    # assign with property names
    ASSIGN_PROPS_PATTERN = re.compile(
        r'assign\s*(?:<[^>]*>)?\s*\(\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # send() / sendTo() pattern
    SEND_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?(?:send|sendTo)\s*\(\s*(?:\{[^}]*type\s*:\s*[\'"](\w+)[\'"]|[\'"](\w+)[\'"])',
        re.MULTILINE
    )

    # raise() pattern
    RAISE_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?raise\s*\(\s*(?:\{[^}]*type\s*:\s*[\'"](\w+)[\'"]|[\'"](\w+)[\'"])',
        re.MULTILINE
    )

    # log() pattern
    LOG_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?log\s*\(',
        re.MULTILINE
    )

    # stop() pattern
    STOP_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?stop\s*\(',
        re.MULTILINE
    )

    # cancel() pattern
    CANCEL_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?cancel\s*\(',
        re.MULTILINE
    )

    # pure() pattern
    PURE_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?pure\s*\(',
        re.MULTILINE
    )

    # choose() pattern
    CHOOSE_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?choose\s*\(\s*\[',
        re.MULTILINE
    )

    # forwardTo() pattern (v4)
    FORWARD_TO_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?forwardTo\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # escalate() pattern (v4)
    ESCALATE_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?escalate\s*\(',
        re.MULTILINE
    )

    # respond() pattern (v4)
    RESPOND_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?respond\s*\(',
        re.MULTILINE
    )

    # enqueueActions() pattern (v5)
    ENQUEUE_ACTIONS_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?enqueueActions\s*\(',
        re.MULTILINE
    )

    # emit() pattern (v5)
    EMIT_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?emit\s*\(',
        re.MULTILINE
    )

    # Named action definitions (actions: { actionName: (context, event) => ... })
    NAMED_ACTION_DEF_PATTERN = re.compile(
        r"""actions\s*:\s*\{[^}]*?['"]?(\w+)['"]?\s*:\s*(?:\(|assign|send|raise|log)""",
        re.MULTILINE | re.DOTALL
    )

    # sendTo with target (v5 pattern)
    SEND_TO_V5_PATTERN = re.compile(
        r"""sendTo\s*\(\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract XState actions from source code."""
        actions = []

        # assign() actions
        for match in self.ASSIGN_PATTERN.finditer(content):
            name = match.group(1) or "assign"
            line_number = content[:match.start()].count('\n') + 1

            # Get assigned properties
            props = []
            props_match = self.ASSIGN_PROPS_PATTERN.search(content[match.start():match.start() + 500])
            if props_match:
                prop_body = props_match.group(1)
                props = re.findall(r'(\w+)\s*:', prop_body)
                # Filter out common non-property keywords
                props = [p for p in props if p not in ('type', 'actions', 'target', 'cond', 'guard')]

            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="assign",
                is_named=bool(match.group(1)),
                assigned_properties=props[:15],
            ))

        # send() / sendTo() actions
        for match in self.SEND_PATTERN.finditer(content):
            name = match.group(1) or "send"
            event_type = match.group(2) or match.group(3) or ""
            line_number = content[:match.start()].count('\n') + 1

            # Check for target actor (sendTo)
            target = ""
            nearby = content[match.start():match.start() + 200]
            target_match = self.SEND_TO_V5_PATTERN.search(nearby)
            if target_match:
                target = target_match.group(1)

            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="sendTo" if "sendTo" in nearby[:15] else "send",
                is_named=bool(match.group(1)),
                event_type=event_type,
                target_actor=target,
            ))

        # raise() actions
        for match in self.RAISE_PATTERN.finditer(content):
            name = match.group(1) or "raise"
            event_type = match.group(2) or match.group(3) or ""
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="raise",
                is_named=bool(match.group(1)),
                event_type=event_type,
            ))

        # log() actions
        for match in self.LOG_PATTERN.finditer(content):
            name = match.group(1) or "log"
            line_number = content[:match.start()].count('\n') + 1
            # Skip console.log
            before = content[max(0, match.start() - 10):match.start()]
            if 'console.' in before:
                continue
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="log",
                is_named=bool(match.group(1)),
            ))

        # stop() actions
        for match in self.STOP_PATTERN.finditer(content):
            name = match.group(1) or "stop"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="stop",
                is_named=bool(match.group(1)),
            ))

        # cancel() actions
        for match in self.CANCEL_PATTERN.finditer(content):
            name = match.group(1) or "cancel"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="cancel",
                is_named=bool(match.group(1)),
            ))

        # pure() actions
        for match in self.PURE_PATTERN.finditer(content):
            name = match.group(1) or "pure"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="pure",
                is_named=bool(match.group(1)),
            ))

        # choose() actions
        for match in self.CHOOSE_PATTERN.finditer(content):
            name = match.group(1) or "choose"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="choose",
                is_named=bool(match.group(1)),
            ))

        # forwardTo() actions (v4)
        for match in self.FORWARD_TO_PATTERN.finditer(content):
            name = match.group(1) or "forwardTo"
            target = match.group(2) or ""
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="forwardTo",
                is_named=bool(match.group(1)),
                target_actor=target,
            ))

        # escalate() actions (v4)
        for match in self.ESCALATE_PATTERN.finditer(content):
            name = match.group(1) or "escalate"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="escalate",
                is_named=bool(match.group(1)),
            ))

        # respond() actions (v4)
        for match in self.RESPOND_PATTERN.finditer(content):
            name = match.group(1) or "respond"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="respond",
                is_named=bool(match.group(1)),
            ))

        # enqueueActions() (v5)
        for match in self.ENQUEUE_ACTIONS_PATTERN.finditer(content):
            name = match.group(1) or "enqueueActions"
            line_number = content[:match.start()].count('\n') + 1
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="enqueueActions",
                is_named=bool(match.group(1)),
                is_v5=True,
            ))

        # emit() (v5)
        for match in self.EMIT_PATTERN.finditer(content):
            name = match.group(1) or "emit"
            line_number = content[:match.start()].count('\n') + 1
            # Skip EventEmitter.emit or similar non-xstate patterns
            before = content[max(0, match.start() - 30):match.start()]
            if '.emit' in before or 'emitter' in before.lower():
                continue
            actions.append(XstateActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type="emit",
                is_named=bool(match.group(1)),
                is_v5=True,
            ))

        return {"actions": actions}
