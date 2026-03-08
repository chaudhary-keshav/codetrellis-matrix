"""
Dart Attribute Extractor for CodeTrellis

Extracts annotations, metadata, and language-specific attributes from Dart source code:
- Code generation annotations (@freezed, @JsonSerializable, @riverpod, etc.)
- Deprecation annotations (@deprecated, @Deprecated)
- Override annotations (@override)
- Access control (part/part of, show/hide, deferred)
- Null safety markers (required, late, ?)
- Dart analysis annotations (@immutable, @sealed, @protected, @visibleForTesting, etc.)
- Build runner configurations
- Flutter-specific annotations (@WidgetbindingsObserver, etc.)
- Isolate patterns (compute, Isolate.spawn)
- Platform channel interop (MethodChannel, EventChannel)

Supports Dart 2.0 through Dart 3.x+ features including:
- Records (Dart 3.0+)
- Sealed class hierarchies (Dart 3.0+)
- Pattern matching (Dart 3.0+)
- Macros (experimental)

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DartAnnotationInfo:
    """Information about a Dart annotation."""
    name: str
    file: str = ""
    target: str = ""  # class/method/field the annotation is on
    category: str = ""  # annotation category
    arguments: str = ""
    line_number: int = 0


@dataclass
class DartImportInfo:
    """Information about import/export directives."""
    uri: str
    file: str = ""
    is_export: bool = False
    is_deferred: bool = False
    deferred_as: str = ""
    show: List[str] = field(default_factory=list)
    hide: List[str] = field(default_factory=list)
    prefix: str = ""
    line_number: int = 0


@dataclass
class DartPartInfo:
    """Information about part/part of directives."""
    uri: str
    file: str = ""
    is_part_of: bool = False
    line_number: int = 0


@dataclass
class DartIsolateInfo:
    """Information about isolate/concurrency patterns."""
    name: str
    file: str = ""
    kind: str = ""  # compute, isolate_spawn, isolate_run (scanner alias)
    pattern: str = ""  # compute, isolate_spawn, isolate_run
    function_name: str = ""  # function being run in isolate
    line_number: int = 0


@dataclass
class DartPlatformChannelInfo:
    """Information about platform channel interop."""
    name: str
    file: str = ""
    channel_type: str = ""  # method_channel, event_channel, basic_message
    kind: str = ""  # alias for channel_type (used by scanner)
    channel_name: str = ""
    methods: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class DartNullSafetyInfo:
    """Information about null safety patterns."""
    late_fields: int = 0
    nullable_types: int = 0
    required_params: int = 0
    null_assertions: int = 0
    null_aware_ops: int = 0


class DartAttributeExtractor:
    """
    Extracts annotations, metadata, and Dart-specific attributes.

    Detects:
    - Code generation annotations (freezed, json_serializable, riverpod, etc.)
    - Analysis annotations (@immutable, @protected, @visibleForTesting)
    - Import/export directives with show/hide/deferred
    - Part/part of directives
    - Isolate/compute patterns
    - Platform channel interop
    - Null safety patterns
    - Records and pattern matching
    """

    # General annotation pattern
    ANNOTATION_PATTERN = re.compile(
        r'^\s*@(?P<name>\w+)(?:\((?P<args>[^)]*)\))?\s*$',
        re.MULTILINE
    )

    # Import directive pattern
    IMPORT_PATTERN = re.compile(
        r"^\s*import\s+['\"](?P<uri>[^'\"]+)['\"]\s*"
        r"(?:deferred\s+as\s+(?P<deferred_as>\w+)\s*)?"
        r"(?:as\s+(?P<prefix>\w+)\s*)?"
        r"(?:show\s+(?P<show>[^;]+?)\s*)?"
        r"(?:hide\s+(?P<hide>[^;]+?)\s*)?;",
        re.MULTILINE
    )

    # Export directive pattern
    EXPORT_PATTERN = re.compile(
        r"^\s*export\s+['\"](?P<uri>[^'\"]+)['\"]\s*"
        r"(?:show\s+(?P<show>[^;]+?)\s*)?"
        r"(?:hide\s+(?P<hide>[^;]+?)\s*)?;",
        re.MULTILINE
    )

    # Part directive pattern
    PART_PATTERN = re.compile(
        r"^\s*part\s+['\"](?P<uri>[^'\"]+)['\"]\s*;",
        re.MULTILINE
    )

    # Part of directive pattern
    PART_OF_PATTERN = re.compile(
        r"^\s*part\s+of\s+(?:['\"](?P<uri>[^'\"]+)['\"]|(?P<library>\w+(?:\.\w+)*))\s*;",
        re.MULTILINE
    )

    # Library directive
    LIBRARY_PATTERN = re.compile(
        r'^\s*library\s+(?P<name>\w+(?:\.\w+)*)\s*;',
        re.MULTILINE
    )

    # Compute function pattern
    COMPUTE_PATTERN = re.compile(
        r'compute\s*(?:<[^>]+>)?\s*\(\s*(?P<func>\w+)',
        re.MULTILINE
    )

    # Isolate.spawn / Isolate.run pattern
    ISOLATE_PATTERN = re.compile(
        r'Isolate\.(?P<method>spawn|run)\s*\(\s*(?P<func>\w+)',
        re.MULTILINE
    )

    # MethodChannel pattern
    METHOD_CHANNEL_PATTERN = re.compile(
        r"(?:const\s+)?MethodChannel\s*\(\s*['\"](?P<name>[^'\"]+)['\"]\s*\)",
        re.MULTILINE
    )

    # EventChannel pattern
    EVENT_CHANNEL_PATTERN = re.compile(
        r"(?:const\s+)?EventChannel\s*\(\s*['\"](?P<name>[^'\"]+)['\"]\s*\)",
        re.MULTILINE
    )

    # invokeMethod pattern
    INVOKE_METHOD_PATTERN = re.compile(
        r"invokeMethod\s*(?:<[^>]+>)?\s*\(\s*['\"](?P<method>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Record type pattern (Dart 3.0+)
    RECORD_PATTERN = re.compile(
        r'\(\s*(?:\w+\s+\w+\s*,\s*)*\w+\s+\w+\s*\)',
    )

    # Pattern matching: switch expression (Dart 3.0+)
    SWITCH_EXPRESSION_PATTERN = re.compile(
        r'=\s*switch\s*\(',
        re.MULTILINE
    )

    # Sealed class pattern (Dart 3.0+)
    SEALED_CLASS_PATTERN = re.compile(
        r'sealed\s+class\s+\w+',
        re.MULTILINE
    )

    # Key code-gen annotations to track
    CODEGEN_ANNOTATIONS = {
        'freezed', 'Freezed', 'unfreezed',
        'JsonSerializable', 'JsonKey',
        'riverpod', 'Riverpod',
        'injectable', 'Injectable', 'lazySingleton', 'LazySingleton',
        'singleton', 'Singleton',
        'HiveType', 'HiveField',
        'collection',  # Isar
        'Entity',  # Floor/ObjectBox
        'GenerateMocks', 'GenerateNiceMocks',  # Mockito
        'RoutePage',  # AutoRoute
        'TypeConverter',  # Floor
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attributes, annotations, and metadata from Dart source code.

        Returns:
            Dict with 'annotations', 'imports', 'exports', 'parts',
            'isolates', 'platform_channels', 'null_safety',
            'dart3_features' lists/dicts.
        """
        result: Dict[str, Any] = {
            'annotations': [],
            'imports': [],
            'exports': [],
            'parts': [],
            'isolates': [],
            'platform_channels': [],
            'null_safety': {},
            'dart3_features': {},
            'library': '',
        }

        result['annotations'] = self._extract_annotations(content, file_path)
        result['imports'] = self._extract_imports(content, file_path)
        result['exports'] = self._extract_exports(content, file_path)
        result['parts'] = self._extract_parts(content, file_path)
        result['isolates'] = self._extract_isolates(content, file_path)
        result['platform_channels'] = self._extract_platform_channels(content, file_path)
        result['null_safety'] = self._analyze_null_safety(content)
        result['dart3_features'] = self._detect_dart3_features(content)

        # Library directive
        lib_match = self.LIBRARY_PATTERN.search(content)
        if lib_match:
            result['library'] = lib_match.group('name')

        return result

    def _extract_annotations(self, content: str, file_path: str) -> List[DartAnnotationInfo]:
        """Extract code-gen and analysis annotations."""
        annotations = []

        for match in self.ANNOTATION_PATTERN.finditer(content):
            name = match.group('name')
            if name in self.CODEGEN_ANNOTATIONS or name in (
                'override', 'deprecated', 'Deprecated',
                'immutable', 'protected', 'visibleForTesting',
                'visibleForOverriding', 'nonVirtual', 'sealed',
                'experimental', 'mustCallSuper', 'optionalTypeArgs',
                'pragma',
            ):
                # Find what the annotation is attached to
                next_line_start = match.end() + 1
                next_line_end = content.find('\n', next_line_start)
                target = ""
                if next_line_end > next_line_start:
                    target_line = content[next_line_start:next_line_end].strip()
                    # Extract target name
                    target_match = re.search(r'(?:class|mixin|enum|extension|void|Future|String|int|double|bool)\s+(\w+)', target_line)
                    if target_match:
                        target = target_match.group(1)

                annotations.append(DartAnnotationInfo(
                    name=name,
                    file=file_path,
                    target=target,
                    arguments=match.group('args') or "",
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        return annotations

    def _extract_imports(self, content: str, file_path: str) -> List[DartImportInfo]:
        """Extract import directives."""
        imports = []

        for match in self.IMPORT_PATTERN.finditer(content):
            uri = match.group('uri')

            show = []
            if match.group('show'):
                show = [s.strip() for s in match.group('show').split(',')]

            hide = []
            if match.group('hide'):
                hide = [h.strip() for h in match.group('hide').split(',')]

            imports.append(DartImportInfo(
                uri=uri,
                file=file_path,
                is_deferred=bool(match.group('deferred_as')),
                deferred_as=match.group('deferred_as') or "",
                show=show,
                hide=hide,
                prefix=match.group('prefix') or match.group('deferred_as') or "",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return imports

    def _extract_exports(self, content: str, file_path: str) -> List[DartImportInfo]:
        """Extract export directives."""
        exports = []

        for match in self.EXPORT_PATTERN.finditer(content):
            uri = match.group('uri')

            show = []
            if match.group('show'):
                show = [s.strip() for s in match.group('show').split(',')]

            hide = []
            if match.group('hide'):
                hide = [h.strip() for h in match.group('hide').split(',')]

            exports.append(DartImportInfo(
                uri=uri,
                file=file_path,
                is_export=True,
                show=show,
                hide=hide,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return exports

    def _extract_parts(self, content: str, file_path: str) -> List[DartPartInfo]:
        """Extract part/part of directives."""
        parts = []

        for match in self.PART_PATTERN.finditer(content):
            parts.append(DartPartInfo(
                uri=match.group('uri'),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.PART_OF_PATTERN.finditer(content):
            uri = match.group('uri') or match.group('library') or ""
            parts.append(DartPartInfo(
                uri=uri,
                file=file_path,
                is_part_of=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return parts

    def _extract_isolates(self, content: str, file_path: str) -> List[DartIsolateInfo]:
        """Extract isolate/compute concurrency patterns."""
        isolates = []

        for match in self.COMPUTE_PATTERN.finditer(content):
            isolates.append(DartIsolateInfo(
                name=match.group('func'),
                file=file_path,
                pattern="compute",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.ISOLATE_PATTERN.finditer(content):
            isolates.append(DartIsolateInfo(
                name=match.group('func'),
                file=file_path,
                pattern=f"isolate_{match.group('method')}",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return isolates

    def _extract_platform_channels(self, content: str, file_path: str) -> List[DartPlatformChannelInfo]:
        """Extract platform channel interop patterns."""
        channels = []

        # Method channels
        for match in self.METHOD_CHANNEL_PATTERN.finditer(content):
            channel_name = match.group('name')
            # Find invoked methods
            methods = []
            for inv_match in self.INVOKE_METHOD_PATTERN.finditer(content):
                methods.append(inv_match.group('method'))

            channels.append(DartPlatformChannelInfo(
                name=channel_name,
                file=file_path,
                channel_type="method_channel",
                channel_name=channel_name,
                methods=methods[:10],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Event channels
        for match in self.EVENT_CHANNEL_PATTERN.finditer(content):
            channels.append(DartPlatformChannelInfo(
                name=match.group('name'),
                file=file_path,
                channel_type="event_channel",
                channel_name=match.group('name'),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return channels

    def _analyze_null_safety(self, content: str) -> Dict[str, int]:
        """Analyze null safety usage patterns."""
        return {
            'late_fields': len(re.findall(r'\blate\s+', content)),
            'nullable_types': len(re.findall(r'\w\?\s', content)),
            'required_params': len(re.findall(r'\brequired\s+', content)),
            'null_assertions': content.count('!.') + content.count('!\n'),
            'null_aware_ops': content.count('?.') + content.count('??'),
        }

    def _detect_dart3_features(self, content: str) -> Dict[str, Any]:
        """Detect Dart 3.0+ feature usage."""
        return {
            'has_records': bool(self.RECORD_PATTERN.search(content)),
            'has_switch_expressions': bool(self.SWITCH_EXPRESSION_PATTERN.search(content)),
            'has_sealed_classes': bool(self.SEALED_CLASS_PATTERN.search(content)),
            'has_patterns': bool(re.search(r'\bcase\s+\w+\s*\(', content)),
            'has_class_modifiers': bool(re.search(r'\b(?:sealed|base|interface|final)\s+class\b', content)),
        }
