"""
MobX Observable Extractor v1.0

Extracts MobX observable definitions including:
- makeObservable() calls with annotation maps
- makeAutoObservable() calls with overrides/options
- observable() standalone calls
- @observable decorator usage (legacy and modern)
- observable.ref / observable.shallow / observable.deep / observable.struct modifiers
- Observable maps, sets, and arrays
- Class field observable declarations

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MobXObservableInfo:
    """Information about a makeObservable or makeAutoObservable call."""
    name: str = ""
    file: str = ""
    line: int = 0
    observable_type: str = ""  # 'makeObservable', 'makeAutoObservable', 'observable'
    class_name: str = ""
    observable_fields: List[str] = field(default_factory=list)
    action_fields: List[str] = field(default_factory=list)
    computed_fields: List[str] = field(default_factory=list)
    has_overrides: bool = False
    has_options: bool = False
    auto_bind: bool = False
    typescript_type: str = ""
    modifiers: List[str] = field(default_factory=list)  # ref, shallow, deep, struct


@dataclass
class MobXAutoObservableInfo:
    """Information about makeAutoObservable usage."""
    name: str = ""
    file: str = ""
    line: int = 0
    class_name: str = ""
    excluded_fields: List[str] = field(default_factory=list)
    auto_bind: bool = False
    has_overrides: bool = False


@dataclass
class MobXDecoratorObservableInfo:
    """Information about @observable decorator usage."""
    name: str = ""
    file: str = ""
    line: int = 0
    class_name: str = ""
    field_name: str = ""
    modifier: str = ""  # '', 'ref', 'shallow', 'deep', 'struct'
    typescript_type: str = ""


class MobXObservableExtractor:
    """Extracts MobX observable definitions from source code."""

    # makeObservable(this, { field: observable, ... })
    MAKE_OBSERVABLE = re.compile(
        r'makeObservable\s*\(\s*(?:this|(\w+))\s*,\s*\{([^}]*)\}',
        re.DOTALL
    )

    # makeAutoObservable(this, overrides?, options?)
    MAKE_AUTO_OBSERVABLE = re.compile(
        r'makeAutoObservable\s*\(\s*(?:this|(\w+))'
        r'(?:\s*,\s*(\{[^}]*\}))?'
        r'(?:\s*,\s*(\{[^}]*\}))?'
        r'\s*\)',
        re.DOTALL
    )

    # observable(value) / observable.box(value) / observable.map() / observable.set() / observable.array()
    OBSERVABLE_STANDALONE = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*observable(?:\.(box|map|set|array|object|ref|shallow|deep|struct))?\s*\(',
    )

    # @observable / @observable.ref / @observable.shallow / @observable.deep / @observable.struct
    OBSERVABLE_DECORATOR = re.compile(
        r'@observable(?:\.(ref|shallow|deep|struct))?\s*\n?\s*(?:(?:private|protected|public|readonly)\s+)*(\w+)',
    )

    # class ClassName { constructor() { makeObservable/makeAutoObservable ... } }
    CLASS_WITH_OBSERVABLE = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{',
    )

    # observable.ref / observable.shallow / observable.deep / observable.struct in annotation maps
    ANNOTATION_MODIFIER = re.compile(
        r'(\w+)\s*:\s*observable\.(ref|shallow|deep|struct)',
    )

    # Basic field: observable annotation in makeObservable
    ANNOTATION_FIELD = re.compile(
        r'(\w+)\s*:\s*(observable|computed|action|action\.bound|flow|false|true)',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all MobX observable definitions from source content.

        Returns:
            Dict with keys:
            - observables: List[MobXObservableInfo]
            - auto_observables: List[MobXAutoObservableInfo]
            - decorator_observables: List[MobXDecoratorObservableInfo]
        """
        observables: List[MobXObservableInfo] = []
        auto_observables: List[MobXAutoObservableInfo] = []
        decorator_observables: List[MobXDecoratorObservableInfo] = []

        lines = content.split('\n')

        # Find class contexts for associating observables with classes
        class_ranges = self._find_class_ranges(content)

        # Extract makeObservable calls
        for match in self.MAKE_OBSERVABLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            target = match.group(1) or 'this'
            annotations_block = match.group(2)

            # Parse annotations
            obs_fields = []
            action_fields = []
            computed_fields = []
            modifiers = []

            for ann_match in self.ANNOTATION_FIELD.finditer(annotations_block):
                fname = ann_match.group(1)
                ann_type = ann_match.group(2)
                if ann_type == 'observable':
                    obs_fields.append(fname)
                elif ann_type == 'computed':
                    computed_fields.append(fname)
                elif ann_type.startswith('action'):
                    action_fields.append(fname)
                elif ann_type == 'flow':
                    action_fields.append(fname)

            # Check for modifier annotations
            for mod_match in self.ANNOTATION_MODIFIER.finditer(annotations_block):
                modifiers.append(mod_match.group(2))
                obs_fields.append(mod_match.group(1))

            class_name = self._find_enclosing_class(match.start(), class_ranges)

            info = MobXObservableInfo(
                name=class_name or target,
                file=file_path,
                line=line_num,
                observable_type='makeObservable',
                class_name=class_name,
                observable_fields=obs_fields,
                action_fields=action_fields,
                computed_fields=computed_fields,
                modifiers=modifiers,
            )
            observables.append(info)

        # Extract makeAutoObservable calls
        for match in self.MAKE_AUTO_OBSERVABLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            target = match.group(1) or 'this'
            overrides_block = match.group(2) or ''
            options_block = match.group(3) or ''

            excluded = []
            if overrides_block:
                # Parse excluded fields (field: false)
                for excl in re.finditer(r'(\w+)\s*:\s*false', overrides_block):
                    excluded.append(excl.group(1))

            auto_bind = 'autoBind' in options_block and 'true' in options_block
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            auto_info = MobXAutoObservableInfo(
                name=class_name or target,
                file=file_path,
                line=line_num,
                class_name=class_name,
                excluded_fields=excluded,
                auto_bind=auto_bind,
                has_overrides=bool(overrides_block.strip()),
            )
            auto_observables.append(auto_info)

        # Extract standalone observable() calls
        for match in self.OBSERVABLE_STANDALONE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)
            modifier = match.group(2) or ''

            info = MobXObservableInfo(
                name=var_name,
                file=file_path,
                line=line_num,
                observable_type=f'observable.{modifier}' if modifier else 'observable',
                observable_fields=[var_name],
                modifiers=[modifier] if modifier else [],
            )
            observables.append(info)

        # Extract @observable decorators
        for match in self.OBSERVABLE_DECORATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            modifier = match.group(1) or ''
            field_name = match.group(2)
            class_name = self._find_enclosing_class(match.start(), class_ranges)

            dec_info = MobXDecoratorObservableInfo(
                name=f"{class_name}.{field_name}" if class_name else field_name,
                file=file_path,
                line=line_num,
                class_name=class_name,
                field_name=field_name,
                modifier=modifier,
            )
            decorator_observables.append(dec_info)

        return {
            'observables': observables,
            'auto_observables': auto_observables,
            'decorator_observables': decorator_observables,
        }

    def _find_class_ranges(self, content: str) -> List[Dict[str, Any]]:
        """Find class name and character ranges in the content."""
        ranges = []
        for match in self.CLASS_WITH_OBSERVABLE.finditer(content):
            class_name = match.group(1)
            start = match.start()
            # Find matching closing brace (simplified — count braces)
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
