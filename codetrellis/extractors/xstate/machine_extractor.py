"""
XState Machine Extractor for CodeTrellis

Extracts XState machine definitions and configuration patterns:
- createMachine() (v4+), Machine() (v3), setup().createMachine() (v5)
- Machine IDs, initial states, context types
- Machine options (actions, guards, services/actors, delays)
- predictableActionArguments (v4.x)
- Machine version, description, tags
- TypeScript generics and typegen references
- Nested/hierarchical machine detection

Supports:
- XState v3.x (Machine() factory)
- XState v4.x (createMachine, interpret, predictableActionArguments)
- XState v5.x (setup().createMachine(), createActor, actor model)

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class XstateMachineInfo:
    """Information about an XState machine definition."""
    name: str
    file: str = ""
    line_number: int = 0
    machine_id: str = ""
    initial_state: str = ""
    creation_method: str = ""  # createMachine, Machine, setup
    context_type: str = ""  # TypeScript context type
    has_context: bool = False
    has_types: bool = False  # TypeScript typegen
    has_tsTypes: bool = False  # tsTypes (v4 typegen)
    has_schema: bool = False  # schema property
    state_count: int = 0
    top_level_states: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    has_parallel: bool = False
    has_history: bool = False
    has_final: bool = False
    has_invoke: bool = False
    has_after: bool = False  # delayed transitions
    has_always: bool = False  # eventless transitions
    is_exported: bool = False
    version: str = ""  # machine version field
    description: str = ""
    predictable_action_args: bool = False
    xstate_version: str = ""  # v3, v4, v5
    has_setup: bool = False  # v5 setup() pattern
    setup_actions: List[str] = field(default_factory=list)
    setup_guards: List[str] = field(default_factory=list)
    setup_actors: List[str] = field(default_factory=list)
    setup_delays: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class XstateMachineExtractor:
    """
    Extracts XState machine definitions from source code.

    Detects:
    - createMachine() with config + options (v4+)
    - Machine() factory (v3)
    - setup().createMachine() pattern (v5)
    - Machine IDs, initial states, context
    - TypeScript generic types and typegen
    - Machine-level config (predictableActionArguments, version, etc.)
    """

    # createMachine() pattern (v4+)
    CREATE_MACHINE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createMachine\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Machine() pattern (v3)
    MACHINE_V3_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'Machine\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # setup().createMachine() pattern (v5)
    SETUP_MACHINE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'setup\s*(?:<[^>]*>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # Machine ID pattern
    MACHINE_ID_PATTERN = re.compile(
        r"""id\s*:\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # Initial state pattern
    INITIAL_STATE_PATTERN = re.compile(
        r"""initial\s*:\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # Context pattern
    CONTEXT_PATTERN = re.compile(
        r'context\s*:\s*(?:\{|[({])',
        re.MULTILINE
    )

    # States block pattern - extract top-level state names
    STATE_NAME_PATTERN = re.compile(
        r"""(?:^|\n)\s{2,6}(\w+)\s*:\s*\{""",
        re.MULTILINE
    )

    # Parallel type detection
    PARALLEL_TYPE_PATTERN = re.compile(
        r"""type\s*:\s*['"]parallel['"]""",
        re.MULTILINE
    )

    # History type detection
    HISTORY_TYPE_PATTERN = re.compile(
        r"""type\s*:\s*['"]history['"]""",
        re.MULTILINE
    )

    # Final type detection
    FINAL_TYPE_PATTERN = re.compile(
        r"""type\s*:\s*['"]final['"]""",
        re.MULTILINE
    )

    # Invoke detection
    INVOKE_PATTERN = re.compile(
        r'invoke\s*:\s*(?:\{|\[)',
        re.MULTILINE
    )

    # After (delayed transitions) detection
    AFTER_PATTERN = re.compile(
        r'after\s*:\s*\{',
        re.MULTILINE
    )

    # Always (eventless transitions) detection
    ALWAYS_PATTERN = re.compile(
        r'always\s*:\s*(?:\[|\{)',
        re.MULTILINE
    )

    # predictableActionArguments (v4)
    PREDICTABLE_ACTIONS_PATTERN = re.compile(
        r'predictableActionArguments\s*:\s*true',
        re.MULTILINE
    )

    # Version field
    VERSION_PATTERN = re.compile(
        r"""version\s*:\s*['"]([^'"]+)['"]""",
        re.MULTILINE
    )

    # tsTypes (v4 typegen)
    TS_TYPES_PATTERN = re.compile(
        r'tsTypes\s*:\s*\{',
        re.MULTILINE
    )

    # schema (v4 typegen)
    SCHEMA_PATTERN = re.compile(
        r'schema\s*:\s*\{',
        re.MULTILINE
    )

    # TypeScript context type
    CONTEXT_TYPE_PATTERN = re.compile(
        r'createMachine\s*<\s*\{?\s*context\s*:\s*(\w+)',
        re.MULTILINE
    )

    # Generic type parameter
    GENERIC_TYPE_PATTERN = re.compile(
        r'createMachine\s*<([^>]+)>',
        re.MULTILINE
    )

    # setup() actions/guards/actors/delays
    SETUP_ACTIONS_PATTERN = re.compile(
        r"""actions\s*:\s*\{[^}]*?(\w+)\s*:""",
        re.MULTILINE
    )

    SETUP_GUARDS_PATTERN = re.compile(
        r"""guards\s*:\s*\{[^}]*?(\w+)\s*:""",
        re.MULTILINE
    )

    SETUP_ACTORS_PATTERN = re.compile(
        r"""actors\s*:\s*\{[^}]*?(\w+)\s*:""",
        re.MULTILINE
    )

    # Event type patterns - look for on: { EVENT_NAME: ... }
    EVENT_TYPE_PATTERN = re.compile(
        r"""on\s*:\s*\{[^}]*?['"]?(\w[\w.]*?)['"]?\s*:""",
        re.MULTILINE
    )

    # Tags pattern
    TAGS_PATTERN = re.compile(
        r"""tags\s*:\s*\[([^\]]+)\]""",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract XState machine definitions from source code."""
        machines = []

        # createMachine() (v4+)
        for match in self.CREATE_MACHINE_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            matched_text = match.group(0)
            is_exported = matched_text.lstrip().startswith('export')

            # Get machine body (approximate - find matching brace context)
            body_start = match.end()
            body = self._extract_body(content, body_start)

            machine = XstateMachineInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="createMachine",
                is_exported=is_exported,
            )
            self._analyze_machine_body(machine, body, content)
            machines.append(machine)

        # Machine() (v3)
        for match in self.MACHINE_V3_PATTERN.finditer(content):
            name = match.group(1)
            # Skip if already matched by createMachine
            if any(m.name == name for m in machines):
                continue
            line_number = content[:match.start()].count('\n') + 1
            matched_text = match.group(0)
            is_exported = matched_text.lstrip().startswith('export')

            body_start = match.end()
            body = self._extract_body(content, body_start)

            machine = XstateMachineInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="Machine",
                is_exported=is_exported,
                xstate_version="v3",
            )
            self._analyze_machine_body(machine, body, content)
            machines.append(machine)

        # setup().createMachine() (v5)
        for match in self.SETUP_MACHINE_PATTERN.finditer(content):
            name = match.group(1)
            if any(m.name == name for m in machines):
                continue
            line_number = content[:match.start()].count('\n') + 1
            matched_text = match.group(0)
            is_exported = matched_text.lstrip().startswith('export')

            # Get the full setup + createMachine body
            body_start = match.end()
            body = self._extract_body(content, body_start - 1)  # include opening brace

            machine = XstateMachineInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="setup",
                is_exported=is_exported,
                has_setup=True,
                xstate_version="v5",
            )
            self._analyze_setup_body(machine, body)
            self._analyze_machine_body(machine, body, content)
            machines.append(machine)

        return {"machines": machines}

    def _extract_body(self, content: str, start: int, max_len: int = 5000) -> str:
        """Extract a balanced brace body from content starting at position."""
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

    def _analyze_machine_body(self, machine: XstateMachineInfo, body: str, full_content: str):
        """Analyze a machine config body to extract metadata."""
        # Machine ID
        id_match = self.MACHINE_ID_PATTERN.search(body)
        if id_match:
            machine.machine_id = id_match.group(1)

        # Initial state
        initial_match = self.INITIAL_STATE_PATTERN.search(body)
        if initial_match:
            machine.initial_state = initial_match.group(1)

        # Context
        if self.CONTEXT_PATTERN.search(body):
            machine.has_context = True

        # States
        states_match = re.search(r'states\s*:\s*\{', body)
        if states_match:
            states_body = self._extract_body(body, states_match.end() - 1)
            state_names = self._extract_top_level_keys(states_body)
            machine.top_level_states = state_names[:30]
            machine.state_count = len(state_names)

        # Feature detection
        machine.has_parallel = bool(self.PARALLEL_TYPE_PATTERN.search(body))
        machine.has_history = bool(self.HISTORY_TYPE_PATTERN.search(body))
        machine.has_final = bool(self.FINAL_TYPE_PATTERN.search(body))
        machine.has_invoke = bool(self.INVOKE_PATTERN.search(body))
        machine.has_after = bool(self.AFTER_PATTERN.search(body))
        machine.has_always = bool(self.ALWAYS_PATTERN.search(body))
        machine.predictable_action_args = bool(self.PREDICTABLE_ACTIONS_PATTERN.search(body))

        # Version
        ver_match = self.VERSION_PATTERN.search(body)
        if ver_match:
            machine.version = ver_match.group(1)

        # TypeScript typegen
        machine.has_tsTypes = bool(self.TS_TYPES_PATTERN.search(body))
        machine.has_schema = bool(self.SCHEMA_PATTERN.search(body))
        machine.has_types = machine.has_tsTypes or machine.has_schema

        # Context type
        ctx_type_match = self.CONTEXT_TYPE_PATTERN.search(full_content)
        if ctx_type_match:
            machine.context_type = ctx_type_match.group(1)
        else:
            generic_match = self.GENERIC_TYPE_PATTERN.search(full_content)
            if generic_match:
                machine.context_type = generic_match.group(1).strip()[:60]

        # Event types
        event_matches = self.EVENT_TYPE_PATTERN.findall(body)
        machine.event_types = list(dict.fromkeys(event_matches))[:30]

        # Tags
        tags_match = self.TAGS_PATTERN.search(body)
        if tags_match:
            raw = tags_match.group(1)
            machine.tags = re.findall(r"""['"]([^'"]+)['"]""", raw)

        # XState version detection (if not already set)
        if not machine.xstate_version:
            machine.xstate_version = self._detect_version(full_content, body)

    def _analyze_setup_body(self, machine: XstateMachineInfo, body: str):
        """Analyze setup() block for v5 defined actions/guards/actors."""
        # Extract action names from setup({ actions: { ... } })
        actions_block = re.search(r'actions\s*:\s*\{([^}]*)\}', body)
        if actions_block:
            names = re.findall(r'(\w+)\s*:', actions_block.group(1))
            machine.setup_actions = names[:20]

        # Extract guard names
        guards_block = re.search(r'guards\s*:\s*\{([^}]*)\}', body)
        if guards_block:
            names = re.findall(r'(\w+)\s*:', guards_block.group(1))
            machine.setup_guards = names[:20]

        # Extract actor names
        actors_block = re.search(r'actors\s*:\s*\{([^}]*)\}', body)
        if actors_block:
            names = re.findall(r'(\w+)\s*:', actors_block.group(1))
            machine.setup_actors = names[:20]

        # Extract delay names
        delays_block = re.search(r'delays\s*:\s*\{([^}]*)\}', body)
        if delays_block:
            names = re.findall(r'(\w+)\s*:', delays_block.group(1))
            machine.setup_delays = names[:20]

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
                if state == "seek_key" and depth == 1:
                    # quoted key
                    end_quote = body.find(ch, i + 1)
                    if end_quote > i:
                        keys.append(body[i + 1:end_quote])
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
                elif ch.isalnum() or ch == '_' or ch == '$':
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

    def _detect_version(self, full_content: str, body: str) -> str:
        """Detect XState version from usage patterns."""
        # v5 indicators
        if 'setup(' in full_content or 'createActor(' in full_content:
            return "v5"
        if 'fromPromise(' in full_content or 'fromObservable(' in full_content:
            return "v5"
        if 'fromCallback(' in full_content or 'fromTransition(' in full_content:
            return "v5"
        if 'enqueueActions(' in full_content or '.emit(' in full_content:
            return "v5"

        # v4 indicators
        if 'createMachine(' in full_content:
            if 'predictableActionArguments' in body:
                return "v4"
            if 'interpret(' in full_content:
                return "v4"
            return "v4"

        # v3 indicators
        if 'Machine(' in full_content:
            return "v3"

        return ""
