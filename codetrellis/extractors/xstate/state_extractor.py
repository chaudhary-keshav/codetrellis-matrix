"""
XState State Extractor for CodeTrellis

Extracts XState state node definitions and transitions:
- State nodes (atomic, compound, parallel, final, history)
- Transitions (event → target, with guards, actions)
- Entry / exit actions on states
- Invoke configurations (services, actors, promises, callbacks)
- After (delayed transitions)
- Always (eventless / transient transitions)
- Tags and meta on state nodes
- On done / on error transitions for invoked services

Supports:
- XState v3.x (Machine, onEntry/onExit, services)
- XState v4.x (createMachine, invoke, predictableActionArguments)
- XState v5.x (setup, actors, enqueueActions, emit)

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class XstateStateNodeInfo:
    """Information about a state node in an XState machine."""
    name: str
    file: str = ""
    line_number: int = 0
    machine_name: str = ""
    state_type: str = "atomic"  # atomic, compound, parallel, final, history
    parent_state: str = ""
    initial_child: str = ""
    has_entry: bool = False
    has_exit: bool = False
    entry_actions: List[str] = field(default_factory=list)
    exit_actions: List[str] = field(default_factory=list)
    event_names: List[str] = field(default_factory=list)
    has_invoke: bool = False
    has_after: bool = False
    has_always: bool = False
    tags: List[str] = field(default_factory=list)
    description: str = ""
    history_type: str = ""  # shallow, deep (for history states)


@dataclass
class XstateTransitionInfo:
    """Information about a transition in an XState machine."""
    event: str
    file: str = ""
    line_number: int = 0
    machine_name: str = ""
    source_state: str = ""
    target_state: str = ""
    has_guard: bool = False
    guard_name: str = ""
    has_actions: bool = False
    action_names: List[str] = field(default_factory=list)
    is_internal: bool = False
    description: str = ""


@dataclass
class XstateInvokeInfo:
    """Information about an invoke/service configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    machine_name: str = ""
    state_name: str = ""
    invoke_type: str = ""  # promise, callback, observable, machine, actor
    source_name: str = ""  # service/actor source ID
    has_on_done: bool = False
    has_on_error: bool = False
    on_done_target: str = ""
    on_error_target: str = ""


class XstateStateExtractor:
    """
    Extracts XState state node definitions and transitions from source code.

    Detects:
    - State nodes with their types (atomic, compound, parallel, final, history)
    - Transitions with events, targets, guards, and actions
    - Entry/exit actions
    - Invoke (services/actors) configurations
    - Delayed transitions (after)
    - Eventless transitions (always)
    """

    # State node patterns within states: { ... }
    STATE_NODE_PATTERN = re.compile(
        r"""(\w+)\s*:\s*\{""",
        re.MULTILINE
    )

    # Entry actions
    ENTRY_PATTERN = re.compile(
        r'(?:entry|onEntry)\s*:\s*(?:\[([^\]]*)\]|(\w+)|{)',
        re.MULTILINE
    )

    # Exit actions
    EXIT_PATTERN = re.compile(
        r'(?:exit|onExit)\s*:\s*(?:\[([^\]]*)\]|(\w+)|{)',
        re.MULTILINE
    )

    # Transition pattern: EVENT_NAME: 'target' or EVENT_NAME: { target: '...' }
    TRANSITION_SIMPLE_PATTERN = re.compile(
        r"""['"]?(\w[\w.]*?)['"]?\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    TRANSITION_OBJECT_PATTERN = re.compile(
        r"""['"]?(\w[\w.]*?)['"]?\s*:\s*\{[^}]*?target\s*:\s*['"]([^'"]+)['"]""",
        re.MULTILINE | re.DOTALL
    )

    # Guard in transition
    TRANSITION_GUARD_PATTERN = re.compile(
        r"""(?:cond|guard)\s*:\s*['"]?(\w+)['"]?""",
        re.MULTILINE
    )

    # Actions in transition
    TRANSITION_ACTIONS_PATTERN = re.compile(
        r"""actions\s*:\s*(?:\[([^\]]*)\]|['"](\w+)['"]|(\w+))""",
        re.MULTILINE
    )

    # Invoke pattern
    INVOKE_PATTERN = re.compile(
        r"""invoke\s*:\s*\{[^}]*?(?:src|id)\s*:\s*['"]?(\w+)['"]?""",
        re.MULTILINE | re.DOTALL
    )

    # onDone transition
    ON_DONE_PATTERN = re.compile(
        r"""onDone\s*:\s*(?:['"](\w+)['"]|\{[^}]*?target\s*:\s*['"]([^'"]+)['"])""",
        re.MULTILINE | re.DOTALL
    )

    # onError transition
    ON_ERROR_PATTERN = re.compile(
        r"""onError\s*:\s*(?:['"](\w+)['"]|\{[^}]*?target\s*:\s*['"]([^'"]+)['"])""",
        re.MULTILINE | re.DOTALL
    )

    # Type of state
    STATE_TYPE_PATTERN = re.compile(
        r"""type\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # History type
    HISTORY_PATTERN = re.compile(
        r"""history\s*:\s*['"]?(shallow|deep)['"]?""",
        re.MULTILINE
    )

    # Tags
    TAGS_PATTERN = re.compile(
        r"""tags\s*:\s*\[([^\]]+)\]""",
        re.MULTILINE
    )

    # After (delayed) transitions
    AFTER_PATTERN = re.compile(
        r'after\s*:\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Always (eventless) transitions
    ALWAYS_PATTERN = re.compile(
        r'always\s*:\s*(?:\[([^\]]*)\]|\{([^}]*)\})',
        re.MULTILINE | re.DOTALL
    )

    # Description
    DESCRIPTION_PATTERN = re.compile(
        r"""description\s*:\s*['"`]([^'"`]+)['"`]""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract state nodes, transitions, and invokes from source code."""
        state_nodes = []
        transitions = []
        invokes = []

        # Find all machine definitions to scope state extraction
        machine_blocks = self._find_machine_blocks(content)

        for machine_name, states_body, machine_start_line in machine_blocks:
            # Extract state nodes from the states block
            self._extract_states(
                states_body, machine_name, file_path,
                machine_start_line, state_nodes, transitions, invokes
            )

        return {
            "state_nodes": state_nodes,
            "transitions": transitions,
            "invokes": invokes,
        }

    def _find_machine_blocks(self, content: str) -> List[tuple]:
        """Find machine blocks and extract their states bodies."""
        blocks = []

        # Pattern to find states: { ... } within createMachine/Machine/setup
        machine_pattern = re.compile(
            r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
            r'(?:createMachine|Machine|setup)\s*(?:<[^>]*>)?\s*\(',
            re.MULTILINE
        )

        for match in machine_pattern.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Find states: { ... } block within this machine
            machine_body_start = match.end()
            remaining = content[machine_body_start:]

            states_match = re.search(r'states\s*:\s*\{', remaining)
            if states_match:
                states_start = machine_body_start + states_match.end() - 1
                states_body = self._extract_brace_block(content, states_start)
                blocks.append((name, states_body, line_number))

        return blocks

    def _extract_brace_block(self, content: str, start: int, max_len: int = 5000) -> str:
        """Extract balanced brace block from content."""
        end = min(start + max_len, len(content))
        depth = 0
        in_string = False
        string_char = None

        for i in range(start, end):
            ch = content[i]
            if in_string:
                if ch == string_char and (i == 0 or content[i - 1] != '\\'):
                    in_string = False
                continue
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth <= 0:
                    return content[start:i + 1]

        return content[start:end]

    def _extract_states(self, states_body: str, machine_name: str, file_path: str,
                        base_line: int, state_nodes: List, transitions: List, invokes: List):
        """Extract state nodes from a states block."""
        # Parse top-level keys of the states block
        keys = self._extract_top_level_keys(states_body)

        for key_name in keys:
            # Find this key's body
            key_pattern = re.compile(
                rf"""['"]?{re.escape(key_name)}['"]?\s*:\s*\{{""",
                re.MULTILINE
            )
            key_match = key_pattern.search(states_body)
            if not key_match:
                continue

            state_body = self._extract_brace_block(states_body, key_match.end() - 1)
            line_number = base_line + states_body[:key_match.start()].count('\n')

            # Determine state type
            state_type = "atomic"
            type_match = self.STATE_TYPE_PATTERN.search(state_body)
            if type_match:
                state_type = type_match.group(1)
            elif re.search(r'states\s*:\s*\{', state_body):
                state_type = "compound"

            # Entry/exit
            has_entry = bool(self.ENTRY_PATTERN.search(state_body))
            has_exit = bool(self.EXIT_PATTERN.search(state_body))

            entry_actions = []
            entry_match = self.ENTRY_PATTERN.search(state_body)
            if entry_match:
                actions_str = entry_match.group(1) or entry_match.group(2) or ""
                entry_actions = re.findall(r"""['"](\w+)['"]""", actions_str)
                if entry_match.group(2):
                    entry_actions = [entry_match.group(2)]

            exit_actions = []
            exit_match = self.EXIT_PATTERN.search(state_body)
            if exit_match:
                actions_str = exit_match.group(1) or exit_match.group(2) or ""
                exit_actions = re.findall(r"""['"](\w+)['"]""", actions_str)
                if exit_match.group(2):
                    exit_actions = [exit_match.group(2)]

            # Events
            event_names = []
            on_match = re.search(r'on\s*:\s*\{', state_body, re.DOTALL)
            on_body = ""
            if on_match:
                brace_start = state_body.index('{', on_match.start())
                on_body = self._extract_brace_block(state_body, brace_start)
                # Strip outer braces
                if on_body.startswith('{') and on_body.endswith('}'):
                    on_body = on_body[1:-1]
                event_names = re.findall(r"""['"]?(\w[\w.]*?)['"]?\s*:""", on_body)

            # Invoke
            has_invoke = bool(self.INVOKE_PATTERN.search(state_body))

            # After / Always
            has_after = bool(self.AFTER_PATTERN.search(state_body))
            has_always = bool(self.ALWAYS_PATTERN.search(state_body))

            # Tags
            tags = []
            tags_match = self.TAGS_PATTERN.search(state_body)
            if tags_match:
                tags = re.findall(r"""['"]([^'"]+)['"]""", tags_match.group(1))

            # Description
            description = ""
            desc_match = self.DESCRIPTION_PATTERN.search(state_body)
            if desc_match:
                description = desc_match.group(1)

            # Initial child
            initial_child = ""
            initial_match = re.search(r"""initial\s*:\s*['"](\w+)['"]""", state_body)
            if initial_match:
                initial_child = initial_match.group(1)

            # History type
            history_type = ""
            hist_match = self.HISTORY_PATTERN.search(state_body)
            if hist_match:
                history_type = hist_match.group(1)

            node = XstateStateNodeInfo(
                name=key_name,
                file=file_path,
                line_number=line_number,
                machine_name=machine_name,
                state_type=state_type,
                initial_child=initial_child,
                has_entry=has_entry,
                has_exit=has_exit,
                entry_actions=entry_actions[:10],
                exit_actions=exit_actions[:10],
                event_names=event_names[:20],
                has_invoke=has_invoke,
                has_after=has_after,
                has_always=has_always,
                tags=tags,
                description=description,
                history_type=history_type,
            )
            state_nodes.append(node)

            # Extract transitions
            if on_match and on_body:
                self._extract_transitions(
                    on_body, key_name, machine_name,
                    file_path, line_number, transitions
                )

            # Extract invokes
            if has_invoke:
                self._extract_invokes(
                    state_body, key_name, machine_name,
                    file_path, line_number, invokes
                )

    def _extract_transitions(self, on_body: str, source_state: str,
                             machine_name: str, file_path: str,
                             base_line: int, transitions: List):
        """Extract transitions from an on: { ... } block."""
        # Simple transitions: EVENT: 'target'
        for match in self.TRANSITION_SIMPLE_PATTERN.finditer(on_body):
            event = match.group(1)
            target = match.group(2)
            # Skip if it's a property like 'target:', 'actions:', etc.
            if event in ('target', 'actions', 'cond', 'guard', 'internal', 'description', 'in'):
                continue

            transitions.append(XstateTransitionInfo(
                event=event,
                file=file_path,
                line_number=base_line + on_body[:match.start()].count('\n'),
                machine_name=machine_name,
                source_state=source_state,
                target_state=target,
            ))

        # Object transitions: EVENT: { target: 'target', cond: '...', actions: [...] }
        for match in self.TRANSITION_OBJECT_PATTERN.finditer(on_body):
            event = match.group(1)
            target = match.group(2)
            if event in ('target', 'actions', 'cond', 'guard', 'internal', 'description', 'in'):
                continue

            # Check for guard
            transition_body = on_body[match.start():match.end() + 200]
            guard_match = self.TRANSITION_GUARD_PATTERN.search(transition_body)
            guard_name = guard_match.group(1) if guard_match else ""

            # Check for actions
            actions_match = self.TRANSITION_ACTIONS_PATTERN.search(transition_body)
            action_names = []
            if actions_match:
                actions_str = actions_match.group(1) or actions_match.group(2) or actions_match.group(3) or ""
                action_names = re.findall(r"""['"](\w+)['"]""", actions_str)
                if actions_match.group(2):
                    action_names = [actions_match.group(2)]
                elif actions_match.group(3) and not actions_match.group(1):
                    action_names = [actions_match.group(3)]

            # Avoid duplicates (simple + object match same transition)
            existing = [t for t in transitions if t.event == event
                        and t.source_state == source_state
                        and t.machine_name == machine_name]
            if existing:
                # Update existing with additional info
                existing[0].has_guard = bool(guard_name)
                existing[0].guard_name = guard_name
                existing[0].has_actions = bool(action_names)
                existing[0].action_names = action_names[:10]
                continue

            transitions.append(XstateTransitionInfo(
                event=event,
                file=file_path,
                line_number=base_line + on_body[:match.start()].count('\n'),
                machine_name=machine_name,
                source_state=source_state,
                target_state=target,
                has_guard=bool(guard_name),
                guard_name=guard_name,
                has_actions=bool(action_names),
                action_names=action_names[:10],
            ))

        # Array transitions: EVENT: [ { guard: '...', target: '...' }, { target: '...' } ]
        array_pattern = re.compile(
            r"""['"]?(\w[\w.]*?)['"]?\s*:\s*\[""",
            re.MULTILINE
        )
        for match in array_pattern.finditer(on_body):
            event = match.group(1)
            if event in ('target', 'actions', 'cond', 'guard', 'internal', 'description', 'in', 'entry', 'exit', 'tags', 'always', 'after'):
                continue
            # Already have this event as simple/object transition?
            if any(t.event == event and t.source_state == source_state and t.machine_name == machine_name for t in transitions):
                continue
            # Extract the array body
            array_start = match.end() - 1
            array_body = self._extract_brace_block_bracket(on_body, array_start)
            # Find each { target: '...' } object in the array
            obj_pattern = re.compile(
                r"""\{[^}]*?target\s*:\s*['"]([^'"]+)['"][^}]*\}""",
                re.DOTALL
            )
            for obj_match in obj_pattern.finditer(array_body):
                target = obj_match.group(1)
                obj_text = obj_match.group(0)
                guard_m = self.TRANSITION_GUARD_PATTERN.search(obj_text)
                guard_name = guard_m.group(1) if guard_m else ""
                actions_m = self.TRANSITION_ACTIONS_PATTERN.search(obj_text)
                action_names = []
                if actions_m:
                    actions_str = actions_m.group(1) or actions_m.group(2) or actions_m.group(3) or ""
                    action_names = re.findall(r"""['"](\w+)['"]""", actions_str)
                    if actions_m.group(2):
                        action_names = [actions_m.group(2)]
                transitions.append(XstateTransitionInfo(
                    event=event,
                    file=file_path,
                    line_number=base_line + on_body[:match.start()].count('\n'),
                    machine_name=machine_name,
                    source_state=source_state,
                    target_state=target,
                    has_guard=bool(guard_name),
                    guard_name=guard_name,
                    has_actions=bool(action_names),
                    action_names=action_names[:10],
                ))

    def _extract_brace_block_bracket(self, content: str, start: int, max_len: int = 3000) -> str:
        """Extract balanced bracket [...] block from content."""
        end = min(start + max_len, len(content))
        depth = 0
        in_string = False
        string_char = None
        for i in range(start, end):
            ch = content[i]
            if in_string:
                if ch == string_char and (i == 0 or content[i - 1] != '\\'):
                    in_string = False
                continue
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                continue
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth <= 0:
                    return content[start:i + 1]
        return content[start:end]

    def _extract_invokes(self, state_body: str, state_name: str,
                         machine_name: str, file_path: str,
                         base_line: int, invokes: List):
        """Extract invoke configurations from a state body."""
        for match in self.INVOKE_PATTERN.finditer(state_body):
            source_name = match.group(1)

            # Find the invoke block for onDone/onError
            invoke_body = state_body[match.start():match.start() + 500]

            # Determine invoke type
            invoke_type = "unknown"
            if 'fromPromise' in invoke_body:
                invoke_type = "promise"
            elif 'fromCallback' in invoke_body:
                invoke_type = "callback"
            elif 'fromObservable' in invoke_body:
                invoke_type = "observable"
            elif 'Machine' in invoke_body or 'machine' in invoke_body.lower():
                invoke_type = "machine"
            else:
                invoke_type = "actor"

            # onDone
            on_done_target = ""
            done_match = self.ON_DONE_PATTERN.search(invoke_body)
            if done_match:
                on_done_target = done_match.group(1) or done_match.group(2) or ""

            # onError
            on_error_target = ""
            error_match = self.ON_ERROR_PATTERN.search(invoke_body)
            if error_match:
                on_error_target = error_match.group(1) or error_match.group(2) or ""

            invokes.append(XstateInvokeInfo(
                name=source_name,
                file=file_path,
                line_number=base_line + state_body[:match.start()].count('\n'),
                machine_name=machine_name,
                state_name=state_name,
                invoke_type=invoke_type,
                source_name=source_name,
                has_on_done=bool(on_done_target),
                has_on_error=bool(on_error_target),
                on_done_target=on_done_target,
                on_error_target=on_error_target,
            ))

    def _extract_top_level_keys(self, body: str) -> List[str]:
        """Extract top-level keys from a { key: ... } block."""
        keys = []
        depth = 0
        in_string = False
        string_char = None
        current_key = ""
        state = "seek_key"

        for i, ch in enumerate(body):
            if in_string:
                if ch == string_char and body[i - 1:i] != '\\':
                    in_string = False
                continue
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                continue
            if ch == '{':
                depth += 1
                if depth == 1:
                    state = "seek_key"
                    current_key = ""
                elif state == "in_key":
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    state = "seek_key"
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
            elif depth == 1:
                if ch == ':' and state == "in_key":
                    if current_key.strip():
                        keys.append(current_key.strip())
                    current_key = ""
                    state = "seek_key"
                elif ch == ',' or ch == '\n':
                    current_key = ""
                    state = "seek_key"
                elif ch.isalnum() or ch == '_':
                    if state == "seek_key":
                        state = "in_key"
                        current_key = ch
                    else:
                        current_key += ch
                elif ch in (' ', '\t', '\r'):
                    pass
                else:
                    current_key = ""
                    state = "seek_key"

        return keys
