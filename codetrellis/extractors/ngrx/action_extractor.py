"""
NgRx Action Extractor for CodeTrellis

Extracts NgRx action patterns:
- createAction() with type strings and props
- createActionGroup() (NgRx v13.2+)
- Legacy action classes (implements Action)
- Action type naming conventions ([Source] Event)
- props<T>() type parameters
- emptyProps()
- Action unions and exported action types

Supports:
- NgRx 1.x-3.x (manual action classes with type enum)
- NgRx 4.x-7.x (action classes implementing Action interface)
- NgRx 8.x-12.x (createAction, props)
- NgRx 13.x-19.x (createActionGroup, source/events pattern)

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NgrxActionInfo:
    """Information about an NgRx action."""
    name: str
    file: str = ""
    line_number: int = 0
    action_type: str = ""  # '[Books] Load Books'
    source: str = ""  # 'Books' (extracted from type)
    event: str = ""  # 'Load Books' (extracted from type)
    has_props: bool = False
    props_type: str = ""  # TypeScript type of props
    creation_method: str = ""  # createAction, createActionGroup, class
    is_exported: bool = False


@dataclass
class NgrxActionGroupInfo:
    """Information about an NgRx action group (v13.2+)."""
    name: str
    file: str = ""
    line_number: int = 0
    source: str = ""  # source string
    events: List[str] = field(default_factory=list)  # event names
    event_count: int = 0
    is_exported: bool = False


class NgrxActionExtractor:
    """
    Extracts NgRx action patterns from source code.

    Detects:
    - createAction('[Source] Event', props<T>())
    - createActionGroup({ source: 'Source', events: {...} })
    - Legacy action classes (class LoadBooks implements Action)
    - Action type patterns ([Source] Event)
    - props<T>() and emptyProps()
    """

    # createAction
    CREATE_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*createAction\s*\(\s*'
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # createActionGroup (v13.2+)
    CREATE_ACTION_GROUP_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*createActionGroup\s*\(\s*\{',
        re.MULTILINE
    )

    # Legacy action class
    LEGACY_ACTION_CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w+)\s+implements\s+Action\s*\{',
        re.MULTILINE
    )

    # Action type constant
    ACTION_TYPE_CONST_PATTERN = re.compile(
        r'(?:readonly\s+)?type\s*=\s*[\'"](\[[\w\s]+\]\s+[\w\s]+)[\'"]',
        re.MULTILINE
    )

    # props<T>()
    PROPS_PATTERN = re.compile(
        r'props\s*<\s*\{?\s*([^}>)]+)\s*\}?\s*>\s*\(\s*\)',
        re.MULTILINE
    )

    # emptyProps()
    EMPTY_PROPS_PATTERN = re.compile(
        r'emptyProps\s*\(\s*\)',
        re.MULTILINE
    )

    # Source and event from action type string [Source] Event
    SOURCE_EVENT_PATTERN = re.compile(
        r'\[([^\]]+)\]\s*(.*)',
    )

    # Action group source
    GROUP_SOURCE_PATTERN = re.compile(
        r"source\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Action group events
    GROUP_EVENTS_PATTERN = re.compile(
        r"['\"]([^'\"]+)['\"](?:\s*:\s*(?:props|emptyProps))",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract all NgRx action information from source code."""
        result: Dict = {
            'actions': [],
            'action_groups': [],
        }

        # ── createAction ──────────────────────────────────────
        for match in self.CREATE_ACTION_PATTERN.finditer(content):
            name = match.group(1)
            action_type = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            # Extract source and event from type string
            source = ""
            event = ""
            se_match = self.SOURCE_EVENT_PATTERN.match(action_type)
            if se_match:
                source = se_match.group(1).strip()
                event = se_match.group(2).strip()

            # Check for props
            block_start = match.start()
            block_end = min(block_start + 300, len(content))
            block = content[block_start:block_end]

            has_props = bool(self.PROPS_PATTERN.search(block))
            has_empty_props = bool(self.EMPTY_PROPS_PATTERN.search(block))

            props_type = ""
            if has_props:
                p_match = self.PROPS_PATTERN.search(block)
                if p_match:
                    props_type = p_match.group(1).strip()

            action = NgrxActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type=action_type,
                source=source,
                event=event,
                has_props=has_props and not has_empty_props,
                props_type=props_type,
                creation_method='createAction',
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['actions'].append(action)

        # ── createActionGroup ─────────────────────────────────
        for match in self.CREATE_ACTION_GROUP_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 1500, len(content))
            block = content[block_start:block_end]

            # Extract source
            source_match = self.GROUP_SOURCE_PATTERN.search(block)
            source = source_match.group(1) if source_match else ""

            # Extract events
            events = [m.group(1) for m in self.GROUP_EVENTS_PATTERN.finditer(block)]

            group = NgrxActionGroupInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                source=source,
                events=events,
                event_count=len(events),
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['action_groups'].append(group)

        # ── Legacy action classes ─────────────────────────────
        for match in self.LEGACY_ACTION_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Find type constant inside class
            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]

            type_match = self.ACTION_TYPE_CONST_PATTERN.search(block)
            action_type = type_match.group(1) if type_match else ""

            source = ""
            event = ""
            if action_type:
                se_match = self.SOURCE_EVENT_PATTERN.match(action_type)
                if se_match:
                    source = se_match.group(1).strip()
                    event = se_match.group(2).strip()

            # Check for constructor payload
            has_props = 'constructor' in block and 'payload' in block

            action = NgrxActionInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_type=action_type,
                source=source,
                event=event,
                has_props=has_props,
                creation_method='class',
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['actions'].append(action)

        return result
