"""
Swift Attribute Extractor for CodeTrellis

Extracts attribute and meta-programming patterns from Swift source code:
- Property wrappers (@propertyWrapper definition & usage)
- Result builders (@resultBuilder)
- Macros (Swift 5.9+: @freestanding, @attached)
- Availability annotations (@available)
- Access control modifiers
- Concurrency annotations (@MainActor, @Sendable, @globalActor, nonisolated)
- Objective-C interop (@objc, @objcMembers, @IBAction, @IBOutlet)
- Testing annotations (@Test, @Suite — Swift Testing framework)
- Compiler attributes (@frozen, @inlinable, @usableFromInline, @_silgen_name)

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SwiftPropertyWrapperInfo:
    """Information about a property wrapper definition."""
    name: str
    file: str = ""
    wrapped_type: str = ""
    projected_type: str = ""  # $ projected value type
    is_generic: bool = False
    line_number: int = 0


@dataclass
class SwiftResultBuilderInfo:
    """Information about a result builder definition."""
    name: str
    file: str = ""
    build_methods: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftMacroInfo:
    """Information about a Swift macro (5.9+)."""
    name: str
    file: str = ""
    kind: str = ""  # freestanding, attached, expression, declaration, accessor, member, memberAttribute, peer, conformance, extension, codeItem
    role: str = ""
    line_number: int = 0


@dataclass
class SwiftAvailabilityInfo:
    """Information about an @available annotation."""
    platforms: List[str] = field(default_factory=list)
    introduced: str = ""
    deprecated: str = ""
    obsoleted: str = ""
    message: str = ""
    renamed: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SwiftConcurrencyInfo:
    """Information about concurrency-related features."""
    name: str = ""
    file: str = ""
    kind: str = ""  # actor, async_func, sendable, main_actor, global_actor, task, task_group, async_sequence, continuation
    is_isolated: bool = True
    line_number: int = 0


class SwiftAttributeExtractor:
    """
    Extracts attribute and meta-programming patterns from Swift source code.

    Covers:
    - Property wrappers (@propertyWrapper)
    - Result builders (@resultBuilder)
    - Macros (@freestanding, @attached)
    - Availability (@available)
    - Concurrency (@MainActor, @Sendable, actor, async/await)
    - ObjC interop (@objc, @IBAction, @IBOutlet)
    - Compiler directives (#if, #available)
    - Testing (@Test, @Suite)
    """

    # Property wrapper definition
    PROPERTY_WRAPPER_DEF_PATTERN = re.compile(
        r'@propertyWrapper\s+'
        r'(?:(?:public|internal|fileprivate|private)\s+)?'
        r'struct\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Result builder definition
    RESULT_BUILDER_DEF_PATTERN = re.compile(
        r'@resultBuilder\s+'
        r'(?:(?:public|internal|fileprivate|private)\s+)?'
        r'(?:struct|enum|class)\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Macro definition (Swift 5.9+)
    MACRO_DEF_PATTERN = re.compile(
        r'(?:@freestanding|@attached)\s*\(\s*(?P<role>\w+)\s*(?:,\s*[^)]+)?\)\s*'
        r'(?:public\s+)?macro\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Macro usage
    MACRO_USAGE_PATTERN = re.compile(
        r'#(?P<name>\w+)(?:\s*\()?',
        re.MULTILINE
    )

    # @available annotation
    AVAILABLE_PATTERN = re.compile(
        r'@available\s*\(\s*(?P<args>[^)]+)\)',
        re.MULTILINE
    )

    # @MainActor usage
    MAIN_ACTOR_PATTERN = re.compile(
        r'@MainActor\s+(?:(?:class|struct|actor|func|var|let|protocol)\s+)?(?P<name>\w+)',
        re.MULTILINE
    )

    # @Sendable annotation
    SENDABLE_PATTERN = re.compile(
        r'@Sendable\b',
        re.MULTILINE
    )

    # Sendable conformance
    SENDABLE_CONFORMANCE_PATTERN = re.compile(
        r'(?:class|struct|enum|actor)\s+(?P<name>\w+)\s*[^{]*\bSendable\b',
        re.MULTILINE
    )

    # @globalActor
    GLOBAL_ACTOR_PATTERN = re.compile(
        r'@globalActor\s+'
        r'(?:(?:public|internal|fileprivate|private)\s+)?'
        r'(?:struct|class|actor|enum)\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Task and TaskGroup usage
    TASK_PATTERN = re.compile(
        r'(?:Task|TaskGroup|ThrowingTaskGroup|withTaskGroup|withThrowingTaskGroup|'
        r'AsyncStream|AsyncThrowingStream|withCheckedContinuation|'
        r'withCheckedThrowingContinuation|withUnsafeContinuation|'
        r'withUnsafeThrowingContinuation)\s*[{(<]',
        re.MULTILINE
    )

    # @objc annotation
    OBJC_PATTERN = re.compile(
        r'@(?:objc|objcMembers|IBAction|IBOutlet|IBDesignable|IBInspectable)\b',
        re.MULTILINE
    )

    # #if compiler directive
    COMPILER_DIRECTIVE_PATTERN = re.compile(
        r'#if\s+(?P<condition>[^\n]+)',
        re.MULTILINE
    )

    # @Test / @Suite (Swift Testing)
    SWIFT_TESTING_PATTERN = re.compile(
        r'@(?:Test|Suite)\s*(?:\([^)]*\))?\s*'
        r'(?:func|struct)\s+(?P<name>\w+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract attribute patterns from Swift source code.

        Args:
            content: Swift source code
            file_path: Path to source file

        Returns:
            Dict with keys: property_wrappers, result_builders, macros,
                           availability, concurrency, objc_annotations,
                           compiler_directives, testing
        """
        return {
            'property_wrappers': self._extract_property_wrappers(content, file_path),
            'result_builders': self._extract_result_builders(content, file_path),
            'macros': self._extract_macros(content, file_path),
            'availability': self._extract_availability(content, file_path),
            'concurrency': self._extract_concurrency(content, file_path),
            'objc_annotations': self._extract_objc(content, file_path),
            'compiler_directives': self._extract_compiler_directives(content, file_path),
            'testing': self._extract_testing(content, file_path),
        }

    def _extract_property_wrappers(self, content: str, file_path: str) -> List[SwiftPropertyWrapperInfo]:
        """Extract property wrapper definitions."""
        wrappers = []
        for match in self.PROPERTY_WRAPPER_DEF_PATTERN.finditer(content):
            name = match.group('name')

            # Look for wrappedValue type in body
            body_start = content.find('{', match.end())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            wrapped_type = ''
            wv_match = re.search(r'var\s+wrappedValue\s*:\s*(\S+)', body)
            if wv_match:
                wrapped_type = wv_match.group(1)

            projected_type = ''
            pv_match = re.search(r'var\s+projectedValue\s*:\s*(\S+)', body)
            if pv_match:
                projected_type = pv_match.group(1)

            is_generic = '<' in name or bool(re.search(r'<\w+>', content[match.start():match.start()+200]))

            line_number = content[:match.start()].count('\n') + 1
            wrappers.append(SwiftPropertyWrapperInfo(
                name=name, file=file_path,
                wrapped_type=wrapped_type,
                projected_type=projected_type,
                is_generic=is_generic,
                line_number=line_number,
            ))
        return wrappers

    def _extract_result_builders(self, content: str, file_path: str) -> List[SwiftResultBuilderInfo]:
        """Extract result builder definitions."""
        builders = []
        for match in self.RESULT_BUILDER_DEF_PATTERN.finditer(content):
            name = match.group('name')

            body_start = content.find('{', match.end())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            build_methods = re.findall(r'static\s+func\s+(build\w+)', body)

            line_number = content[:match.start()].count('\n') + 1
            builders.append(SwiftResultBuilderInfo(
                name=name, file=file_path,
                build_methods=build_methods,
                line_number=line_number,
            ))
        return builders

    def _extract_macros(self, content: str, file_path: str) -> List[SwiftMacroInfo]:
        """Extract macro definitions."""
        macros = []
        for match in self.MACRO_DEF_PATTERN.finditer(content):
            name = match.group('name')
            role = match.group('role')
            kind = 'freestanding' if '@freestanding' in content[match.start():match.start()+20] else 'attached'

            line_number = content[:match.start()].count('\n') + 1
            macros.append(SwiftMacroInfo(
                name=name, file=file_path,
                kind=kind, role=role,
                line_number=line_number,
            ))
        return macros

    def _extract_availability(self, content: str, file_path: str) -> List[SwiftAvailabilityInfo]:
        """Extract @available annotations."""
        avail_list = []
        for match in self.AVAILABLE_PATTERN.finditer(content):
            args = match.group('args')

            platforms = []
            introduced = ''
            deprecated = ''
            message = ''
            renamed = ''

            # Parse platform and version
            for part in args.split(','):
                part = part.strip()
                if part == '*':
                    platforms.append('*')
                elif part.startswith('introduced:'):
                    introduced = part.split(':')[1].strip()
                elif part.startswith('deprecated:'):
                    deprecated = part.split(':')[1].strip()
                elif part.startswith('message:'):
                    message = part.split(':', 1)[1].strip().strip('"')
                elif part.startswith('renamed:'):
                    renamed = part.split(':', 1)[1].strip().strip('"')
                elif re.match(r'(?:iOS|macOS|watchOS|tvOS|visionOS|macCatalyst|swift)\s+[\d.]+', part):
                    platforms.append(part)
                elif part in ('iOS', 'macOS', 'watchOS', 'tvOS', 'visionOS', 'macCatalyst', 'swift'):
                    platforms.append(part)
                elif part == 'unavailable':
                    platforms.append('unavailable')
                elif part == 'deprecated':
                    deprecated = 'yes'

            line_number = content[:match.start()].count('\n') + 1
            avail_list.append(SwiftAvailabilityInfo(
                platforms=platforms,
                introduced=introduced,
                deprecated=deprecated,
                message=message,
                renamed=renamed,
                file=file_path,
                line_number=line_number,
            ))
        return avail_list

    def _extract_concurrency(self, content: str, file_path: str) -> List[SwiftConcurrencyInfo]:
        """Extract concurrency-related annotations and patterns."""
        concurrency = []

        # @MainActor usage
        for match in self.MAIN_ACTOR_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1
            concurrency.append(SwiftConcurrencyInfo(
                name=name, file=file_path,
                kind='main_actor',
                line_number=line_number,
            ))

        # @globalActor definitions
        for match in self.GLOBAL_ACTOR_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1
            concurrency.append(SwiftConcurrencyInfo(
                name=name, file=file_path,
                kind='global_actor',
                line_number=line_number,
            ))

        # Sendable conformance
        for match in self.SENDABLE_CONFORMANCE_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1
            concurrency.append(SwiftConcurrencyInfo(
                name=name, file=file_path,
                kind='sendable',
                line_number=line_number,
            ))

        # Task/TaskGroup usage (unique per kind)
        task_kinds_seen = set()
        for match in self.TASK_PATTERN.finditer(content):
            task_kind = match.group(0).split('{')[0].split('(')[0].split('<')[0].strip()
            if task_kind not in task_kinds_seen:
                task_kinds_seen.add(task_kind)
                line_number = content[:match.start()].count('\n') + 1
                concurrency.append(SwiftConcurrencyInfo(
                    name=task_kind, file=file_path,
                    kind='task',
                    line_number=line_number,
                ))

        return concurrency

    def _extract_objc(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Objective-C interop annotations."""
        annotations = []
        seen = set()
        for match in self.OBJC_PATTERN.finditer(content):
            attr = match.group(0).lstrip('@')
            if attr not in seen:
                seen.add(attr)
                line_number = content[:match.start()].count('\n') + 1
                annotations.append({
                    'attribute': attr,
                    'file': file_path,
                    'line_number': line_number,
                })
        return annotations

    def _extract_compiler_directives(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract compiler directives."""
        directives = []
        for match in self.COMPILER_DIRECTIVE_PATTERN.finditer(content):
            condition = match.group('condition').strip()
            line_number = content[:match.start()].count('\n') + 1
            directives.append({
                'condition': condition,
                'file': file_path,
                'line_number': line_number,
            })
        return directives

    def _extract_testing(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Swift Testing annotations."""
        tests = []
        for match in self.SWIFT_TESTING_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1
            tests.append({
                'name': name,
                'file': file_path,
                'line_number': line_number,
            })
        return tests

    def _extract_brace_body(self, content: str, open_pos: int) -> str:
        """Extract body between matching braces."""
        if open_pos >= len(content) or content[open_pos] != '{':
            return ""
        depth = 0
        i = open_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[open_pos + 1:i]
            i += 1
        return content[open_pos + 1:]
