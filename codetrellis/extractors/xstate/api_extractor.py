"""
XState API Extractor for CodeTrellis

Extracts XState API patterns, imports, actor usage, and TypeScript integration:
- xstate core imports (createMachine, createActor, assign, etc.)
- @xstate/react (useMachine, useActor, useSelector, useActorRef)
- @xstate/vue (useMachine), @xstate/svelte (useMachine)
- @xstate/solid (createService, useActor)
- @xstate/inspect, @statelyai/inspect
- @xstate/test, @xstate/graph
- @xstate/store (createStore, useSelector)
- interpret (v4) / createActor (v5)
- spawn (v4) / fromPromise/fromObservable/fromCallback/fromTransition (v5)
- TypeScript typegen integration

Supports:
- XState v3.x (Machine, interpret, State)
- XState v4.x (createMachine, interpret, spawn, @xstate/react useMachine)
- XState v5.x (createActor, setup, fromPromise/fromObservable/fromCallback,
               @xstate/react useActor/useActorRef/useSelector)

Part of CodeTrellis v4.55 - XState Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class XstateImportInfo:
    """Information about an XState import."""
    source: str
    file: str = ""
    line_number: int = 0
    imported_names: List[str] = field(default_factory=list)
    is_default: bool = False
    subpath: str = ""  # e.g., xstate/lib, @xstate/react, @xstate/inspect


@dataclass
class XstateActorInfo:
    """Information about an XState actor/interpreter usage."""
    name: str
    file: str = ""
    line_number: int = 0
    creation_method: str = ""  # createActor, interpret, spawn, useMachine, useActor
    machine_name: str = ""  # the machine being interpreted
    has_subscribe: bool = False
    has_start: bool = False
    has_stop: bool = False
    actor_type: str = ""  # promise, callback, observable, transition, machine


@dataclass
class XstateTypegenInfo:
    """Information about XState TypeScript typegen."""
    file: str = ""
    line_number: int = 0
    typegen_type: str = ""  # tsTypes, schema, types, setup generic
    has_context_type: bool = False
    has_event_type: bool = False
    context_type: str = ""
    event_type: str = ""


class XstateApiExtractor:
    """
    Extracts XState API patterns from source code.

    Detects:
    - Import patterns from xstate and @xstate/* packages
    - Actor/interpreter creation patterns
    - React/Vue/Svelte/Solid hook usages
    - TypeScript typegen references
    - Spawn and actor factory patterns
    """

    # Import from 'xstate' or '@xstate/*'
    IMPORT_PATTERN = re.compile(
        r"""(?:import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['"]([^'"]+)['"]|"""
        r"""(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\(['"]([^'"]+)['"]\))""",
        re.MULTILINE
    )

    # createActor() (v5)
    CREATE_ACTOR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createActor\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # interpret() (v4)
    INTERPRET_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'interpret\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useMachine() hook (@xstate/react, @xstate/vue, @xstate/svelte)
    USE_MACHINE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\[([^\]]+)\]|(\w+))\s*=\s*'
        r'useMachine\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useActor() hook (@xstate/react v5)
    USE_ACTOR_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\[([^\]]+)\]|(\w+))\s*=\s*'
        r'useActor\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useSelector() hook
    USE_SELECTOR_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useSelector\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useActorRef() hook (@xstate/react v5)
    USE_ACTOR_REF_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useActorRef\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # spawn() (v4 - spawn child actors)
    SPAWN_PATTERN = re.compile(
        r'spawn\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # fromPromise() (v5 actor factories)
    FROM_PROMISE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*fromPromise\s*\(',
        re.MULTILINE
    )

    # fromObservable() (v5)
    FROM_OBSERVABLE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*fromObservable\s*\(',
        re.MULTILINE
    )

    # fromCallback() (v5)
    FROM_CALLBACK_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*fromCallback\s*\(',
        re.MULTILINE
    )

    # fromTransition() (v5)
    FROM_TRANSITION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*fromTransition\s*\(',
        re.MULTILINE
    )

    # TypeScript typegen reference
    TYPEGEN_PATTERN = re.compile(
        r"""tsTypes\s*:\s*\{\}\s*as\s*import\s*\(['"]([^'"]+)['"]\)""",
        re.MULTILINE
    )

    # Schema types
    SCHEMA_TYPES_PATTERN = re.compile(
        r'schema\s*:\s*\{[^}]*?'
        r'(?:context\s*:\s*\{\}\s*as\s*(\w+)|events\s*:\s*\{\}\s*as\s*(\w+))',
        re.MULTILINE | re.DOTALL
    )

    # .subscribe() call
    SUBSCRIBE_PATTERN = re.compile(
        r'(\w+)\.subscribe\s*\(',
        re.MULTILINE
    )

    # .start() call
    START_PATTERN = re.compile(
        r'(\w+)\.start\s*\(',
        re.MULTILINE
    )

    # .stop() call
    STOP_CALL_PATTERN = re.compile(
        r'(\w+)\.stop\s*\(',
        re.MULTILINE
    )

    # XState ecosystem packages
    XSTATE_PACKAGES = {
        'xstate', '@xstate/react', '@xstate/vue', '@xstate/svelte',
        '@xstate/solid', '@xstate/inspect', '@statelyai/inspect',
        '@xstate/test', '@xstate/graph', '@xstate/store',
        '@xstate/immer', '@xstate/analytics',
        'xstate/lib', 'xstate/lib/actions',
    }

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract XState API patterns from source code."""
        imports = []
        actors = []
        typegens = []

        # ── Imports ──────────────────────────────────────────────
        for match in self.IMPORT_PATTERN.finditer(content):
            named_imports = match.group(1) or match.group(4) or ""
            default_import = match.group(2) or match.group(5) or ""
            source = match.group(3) or match.group(6) or ""

            # Only capture XState-related imports
            if not self._is_xstate_import(source):
                continue

            imported_names = []
            if named_imports:
                imported_names = [n.strip().split(' as ')[0].strip()
                                  for n in named_imports.split(',') if n.strip()]
            elif default_import:
                imported_names = [default_import]

            line_number = content[:match.start()].count('\n') + 1

            # Determine subpath
            subpath = ""
            if '/' in source:
                subpath = source.split('/', 1)[1] if not source.startswith('@') else source

            imports.append(XstateImportInfo(
                source=source,
                file=file_path,
                line_number=line_number,
                imported_names=imported_names[:20],
                is_default=bool(default_import),
                subpath=subpath,
            ))

        # ── Actors (createActor, interpret) ──────────────────────
        # Collect actor names for subscribe/start/stop detection
        actor_names = set()

        for match in self.CREATE_ACTOR_PATTERN.finditer(content):
            name = match.group(1)
            machine = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            actor_names.add(name)
            actors.append(XstateActorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="createActor",
                machine_name=machine,
                actor_type="machine",
            ))

        for match in self.INTERPRET_PATTERN.finditer(content):
            name = match.group(1)
            machine = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            actor_names.add(name)
            actors.append(XstateActorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="interpret",
                machine_name=machine,
                actor_type="machine",
            ))

        # useMachine()
        for match in self.USE_MACHINE_PATTERN.finditer(content):
            destructured = match.group(1) or match.group(2) or ""
            machine = match.group(3)
            line_number = content[:match.start()].count('\n') + 1
            actors.append(XstateActorInfo(
                name=destructured.split(',')[0].strip() if ',' in destructured else destructured,
                file=file_path,
                line_number=line_number,
                creation_method="useMachine",
                machine_name=machine,
                actor_type="machine",
            ))

        # useActor()
        for match in self.USE_ACTOR_PATTERN.finditer(content):
            destructured = match.group(1) or match.group(2) or ""
            machine = match.group(3)
            line_number = content[:match.start()].count('\n') + 1
            actors.append(XstateActorInfo(
                name=destructured.split(',')[0].strip() if ',' in destructured else destructured,
                file=file_path,
                line_number=line_number,
                creation_method="useActor",
                machine_name=machine,
                actor_type="machine",
            ))

        # useActorRef()
        for match in self.USE_ACTOR_REF_PATTERN.finditer(content):
            name = match.group(1)
            machine = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            actors.append(XstateActorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="useActorRef",
                machine_name=machine,
                actor_type="machine",
            ))

        # useSelector()
        for match in self.USE_SELECTOR_PATTERN.finditer(content):
            name = match.group(1)
            actor = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            actors.append(XstateActorInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                creation_method="useSelector",
                machine_name=actor,
            ))

        # fromPromise/fromObservable/fromCallback/fromTransition (v5)
        for pattern, actor_type in [
            (self.FROM_PROMISE_PATTERN, "promise"),
            (self.FROM_OBSERVABLE_PATTERN, "observable"),
            (self.FROM_CALLBACK_PATTERN, "callback"),
            (self.FROM_TRANSITION_PATTERN, "transition"),
        ]:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                actors.append(XstateActorInfo(
                    name=name,
                    file=file_path,
                    line_number=line_number,
                    creation_method=f"from{actor_type.capitalize()}",
                    actor_type=actor_type,
                ))

        # spawn() (v4)
        for match in self.SPAWN_PATTERN.finditer(content):
            spawned = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            actors.append(XstateActorInfo(
                name=f"spawned_{spawned}",
                file=file_path,
                line_number=line_number,
                creation_method="spawn",
                machine_name=spawned,
            ))

        # Update actors with subscribe/start/stop
        for actor in actors:
            if actor.name in actor_names or actor.creation_method in ("createActor", "interpret"):
                for sub_match in self.SUBSCRIBE_PATTERN.finditer(content):
                    if sub_match.group(1) == actor.name:
                        actor.has_subscribe = True
                for start_match in self.START_PATTERN.finditer(content):
                    if start_match.group(1) == actor.name:
                        actor.has_start = True
                for stop_match in self.STOP_CALL_PATTERN.finditer(content):
                    if stop_match.group(1) == actor.name:
                        actor.has_stop = True

        # ── TypeScript typegen ──────────────────────────────────
        for match in self.TYPEGEN_PATTERN.finditer(content):
            typegen_file = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            typegens.append(XstateTypegenInfo(
                file=file_path,
                line_number=line_number,
                typegen_type="tsTypes",
            ))

        for match in self.SCHEMA_TYPES_PATTERN.finditer(content):
            context_type = match.group(1) or ""
            event_type = match.group(2) or ""
            line_number = content[:match.start()].count('\n') + 1
            typegens.append(XstateTypegenInfo(
                file=file_path,
                line_number=line_number,
                typegen_type="schema",
                has_context_type=bool(context_type),
                has_event_type=bool(event_type),
                context_type=context_type,
                event_type=event_type,
            ))

        return {
            "imports": imports,
            "actors": actors,
            "typegens": typegens,
        }

    def _is_xstate_import(self, source: str) -> bool:
        """Check if an import source is XState-related."""
        if source in self.XSTATE_PACKAGES:
            return True
        if source.startswith('xstate') or source.startswith('@xstate/'):
            return True
        if source.startswith('@statelyai/'):
            return True
        return False
