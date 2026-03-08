"""
MobX Action Extractor v1.0

Extracts MobX action definitions including:
- action() function wrapping
- action.bound wrapping
- @action decorator
- @action.bound decorator
- runInAction() calls
- flow() generator function wrapping
- flow.bound
- @flow decorator
- flowResult() calls
- Async action patterns
- Action annotations in makeObservable

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MobXActionInfo:
    """Information about a MobX action."""
    name: str = ""
    file: str = ""
    line: int = 0
    action_type: str = ""  # 'action', 'action.bound', '@action', '@action.bound', 'runInAction', 'annotation'
    class_name: str = ""
    is_async: bool = False
    is_bound: bool = False
    modified_fields: List[str] = field(default_factory=list)
    has_error_handling: bool = False


@dataclass
class MobXFlowInfo:
    """Information about a MobX flow (generator-based async action)."""
    name: str = ""
    file: str = ""
    line: int = 0
    flow_type: str = ""  # 'flow', 'flow.bound', '@flow', 'annotation'
    class_name: str = ""
    is_bound: bool = False
    uses_flow_result: bool = False
    has_error_handling: bool = False


class MobXActionExtractor:
    """Extracts MobX action definitions from source code."""

    # action(() => { ... }) / action("name", () => { ... })
    ACTION_WRAP = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*action(?:\.(bound))?\s*\(',
    )

    # @action / @action.bound
    ACTION_DECORATOR = re.compile(
        r'@action(?:\.(bound))?\s*\n?\s*(?:(?:private|protected|public|readonly|async)\s+)*(\w+)',
    )

    # runInAction(() => { ... })
    RUN_IN_ACTION = re.compile(
        r'runInAction\s*\(',
    )

    # flow(function* () { ... }) / flow(function*name() { ... })
    # Matches both: const x = flow(...) and class field x = flow(...)
    FLOW_WRAP = re.compile(
        r'(?:(?:const|let|var)\s+)?(\w+)\s*=\s*flow(?:\.(bound))?\s*\(\s*function\s*\*',
    )

    # @flow / @flow.bound
    FLOW_DECORATOR = re.compile(
        r'@flow(?:\.(bound))?\s*\n?\s*(?:(?:private|protected|public|readonly)\s+)*\*?\s*(\w+)',
    )

    # flowResult()
    FLOW_RESULT = re.compile(
        r'flowResult\s*\(\s*(\w+)',
    )

    # action/action.bound annotations in makeObservable
    ACTION_ANNOTATION = re.compile(
        r'(\w+)\s*:\s*(action(?:\.bound)?|flow(?:\.bound)?)',
    )

    # Class context
    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all MobX action definitions from source content.

        Returns:
            Dict with keys:
            - actions: List[MobXActionInfo]
            - flows: List[MobXFlowInfo]
        """
        actions: List[MobXActionInfo] = []
        flows: List[MobXFlowInfo] = []

        class_ranges = self._find_class_ranges(content)

        # Extract action() wrapping
        for match in self.ACTION_WRAP.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            action_name = match.group(1)
            is_bound = bool(match.group(2))

            info = MobXActionInfo(
                name=action_name,
                file=file_path,
                line=line_num,
                action_type='action.bound' if is_bound else 'action',
                is_bound=is_bound,
            )
            actions.append(info)

        # Extract @action / @action.bound decorators
        for match in self.ACTION_DECORATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            is_bound = bool(match.group(1))
            method_name = match.group(2)
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            # Check if the method is async
            context_after = content[match.start():match.start() + 200]
            is_async = 'async ' in context_after.split(method_name)[0] if method_name in context_after else False

            info = MobXActionInfo(
                name=f"{class_name}.{method_name}" if class_name else method_name,
                file=file_path,
                line=line_num,
                action_type='@action.bound' if is_bound else '@action',
                class_name=class_name,
                is_async=is_async,
                is_bound=is_bound,
            )
            actions.append(info)

        # Extract runInAction calls
        for match in self.RUN_IN_ACTION.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            # Check for error handling in context
            context = content[max(0, match.start() - 100):match.start() + 300]
            has_error = 'try' in context or 'catch' in context

            info = MobXActionInfo(
                name='runInAction',
                file=file_path,
                line=line_num,
                action_type='runInAction',
                class_name=class_name,
                has_error_handling=has_error,
            )
            actions.append(info)

        # Extract flow() wrapping
        for match in self.FLOW_WRAP.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            flow_name = match.group(1)
            is_bound = bool(match.group(2))

            info = MobXFlowInfo(
                name=flow_name,
                file=file_path,
                line=line_num,
                flow_type='flow.bound' if is_bound else 'flow',
                is_bound=is_bound,
            )
            flows.append(info)

        # Extract @flow decorators
        for match in self.FLOW_DECORATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            is_bound = bool(match.group(1))
            method_name = match.group(2)
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            info = MobXFlowInfo(
                name=f"{class_name}.{method_name}" if class_name else method_name,
                file=file_path,
                line=line_num,
                flow_type='@flow.bound' if is_bound else '@flow',
                class_name=class_name,
                is_bound=is_bound,
            )
            flows.append(info)

        # Extract flowResult() calls
        flow_result_names = set()
        for match in self.FLOW_RESULT.finditer(content):
            flow_result_names.add(match.group(1))

        # Mark flows that use flowResult
        for fl in flows:
            base_name = fl.name.split('.')[-1]
            if base_name in flow_result_names:
                fl.uses_flow_result = True

        # Extract action/flow annotations from makeObservable
        for match in self.ACTION_ANNOTATION.finditer(content):
            field_name = match.group(1)
            ann_type = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            if ann_type.startswith('flow'):
                # Check not already captured
                if not any(f.name.endswith(f".{field_name}") or f.name == field_name for f in flows):
                    is_bound = 'bound' in ann_type
                    info = MobXFlowInfo(
                        name=f"{class_name}.{field_name}" if class_name else field_name,
                        file=file_path,
                        line=line_num,
                        flow_type='annotation',
                        class_name=class_name,
                        is_bound=is_bound,
                    )
                    flows.append(info)
            elif ann_type.startswith('action'):
                # Check not already captured
                if not any(a.name.endswith(f".{field_name}") or a.name == field_name for a in actions):
                    is_bound = 'bound' in ann_type
                    info = MobXActionInfo(
                        name=f"{class_name}.{field_name}" if class_name else field_name,
                        file=file_path,
                        line=line_num,
                        action_type='annotation',
                        class_name=class_name,
                        is_bound=is_bound,
                    )
                    actions.append(info)

        return {
            'actions': actions,
            'flows': flows,
        }

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
