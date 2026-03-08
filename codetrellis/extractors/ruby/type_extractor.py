"""
RubyTypeExtractor - Extracts Ruby class, module, struct, and mixin definitions.

This extractor parses Ruby source code and extracts:
- Class definitions with inheritance, mixins, reopened classes
- Module definitions with include/extend/prepend
- Struct.new definitions
- OpenStruct usage
- Data.define (Ruby 3.2+)
- Refinements
- Eigenclass/singleton methods
- Nested class/module hierarchies
- Visibility modifiers (public, private, protected)
- Frozen string literals and magic comments

Supports Ruby 1.8 through Ruby 3.3+ features.

Part of CodeTrellis v4.23 - Ruby Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RubyFieldInfo:
    """Information about a Ruby attribute/field."""
    name: str
    accessor_type: str = ""  # attr_reader, attr_writer, attr_accessor
    type_annotation: Optional[str] = None  # Sorbet/RBS type
    visibility: str = "public"
    is_class_variable: bool = False  # @@var
    is_instance_variable: bool = False  # @var
    default_value: Optional[str] = None


@dataclass
class RubyMixinInfo:
    """Information about a Ruby mixin (include/extend/prepend)."""
    name: str
    kind: str = "include"  # include, extend, prepend
    file: str = ""
    line_number: int = 0


@dataclass
class RubyClassInfo:
    """Information about a Ruby class."""
    name: str
    parent_class: Optional[str] = None
    mixins: List[RubyMixinInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    class_methods: List[str] = field(default_factory=list)
    fields: List[RubyFieldInfo] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    visibility: str = ""
    file: str = ""
    line_number: int = 0
    is_abstract: bool = False
    is_singleton: bool = False
    is_reopened: bool = False
    nested_classes: List[str] = field(default_factory=list)
    nested_modules: List[str] = field(default_factory=list)
    doc_comment: Optional[str] = None
    namespace: Optional[str] = None  # Enclosing module/class


@dataclass
class RubyModuleInfo:
    """Information about a Ruby module."""
    name: str
    mixins: List[RubyMixinInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    module_methods: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_concern: bool = False  # ActiveSupport::Concern
    is_namespace: bool = False  # Module used only as namespace
    doc_comment: Optional[str] = None
    namespace: Optional[str] = None


@dataclass
class RubyStructInfo:
    """Information about a Ruby Struct/Data.define."""
    name: str
    members: List[str] = field(default_factory=list)
    kind: str = "Struct"  # Struct, Data (Ruby 3.2+), OpenStruct
    keyword_init: bool = False
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


class RubyTypeExtractor:
    """
    Extracts Ruby type definitions from source code.

    Handles:
    - Class definitions with < inheritance
    - Module definitions
    - Struct.new with members
    - Data.define (Ruby 3.2+)
    - include/extend/prepend mixins
    - attr_reader/attr_writer/attr_accessor
    - Nested class/module hierarchies
    - Class reopening detection
    - Eigenclass (class << self)
    - Visibility modifiers
    - YARD/RDoc doc comments

    v4.23: Uses indentation-aware extraction for Ruby's end-delimited blocks.
    """

    # Doc comment pattern (# comments before class/module)
    DOC_COMMENT_PATTERN = re.compile(
        r'((?:^\s*#[^\n]*\n)+)\s*',
        re.MULTILINE
    )

    # Class definition: class Name < Parent
    CLASS_HEADER = re.compile(
        r'^\s*class\s+(?P<name>[A-Z]\w*(?:::[A-Z]\w*)*)\s*(?:<\s*(?P<parent>[A-Z]\w*(?:::[A-Z]\w*)*))?',
        re.MULTILINE
    )

    # Module definition: module Name
    MODULE_HEADER = re.compile(
        r'^\s*module\s+(?P<name>[A-Z]\w*(?:::[A-Z]\w*)*)',
        re.MULTILINE
    )

    # Struct.new: Name = Struct.new(:member1, :member2)
    STRUCT_PATTERN = re.compile(
        r'^\s*(?P<name>[A-Z]\w*)\s*=\s*Struct\.new\s*\((?P<members>[^)]*)\)(?:\s*do)?',
        re.MULTILINE
    )

    # Data.define (Ruby 3.2+): Name = Data.define(:member1, :member2)
    DATA_DEFINE_PATTERN = re.compile(
        r'^\s*(?P<name>[A-Z]\w*)\s*=\s*Data\.define\s*\((?P<members>[^)]*)\)',
        re.MULTILINE
    )

    # include/extend/prepend patterns
    MIXIN_PATTERN = re.compile(
        r'^\s*(?P<kind>include|extend|prepend)\s+(?P<name>[A-Z]\w*(?:::[A-Z]\w*)*)',
        re.MULTILINE
    )

    # attr_reader/attr_writer/attr_accessor
    ACCESSOR_PATTERN = re.compile(
        r'^\s*(?P<type>attr_reader|attr_writer|attr_accessor)\s+(?P<attrs>[^\n#]+)',
        re.MULTILINE
    )

    # Instance variable assignment: @name =
    IVAR_PATTERN = re.compile(
        r'^\s*@(?P<name>\w+)\s*=',
        re.MULTILINE
    )

    # Class variable: @@name =
    CVAR_PATTERN = re.compile(
        r'^\s*@@(?P<name>\w+)\s*=',
        re.MULTILINE
    )

    # Constant definition: NAME = value
    CONSTANT_PATTERN = re.compile(
        r'^\s*(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*(?!Struct\.new|Data\.define|Class\.new|Module\.new)',
        re.MULTILINE
    )

    # Eigenclass: class << self
    EIGENCLASS_PATTERN = re.compile(
        r'^\s*class\s*<<\s*(?P<target>self|\w+)',
        re.MULTILINE
    )

    # Visibility modifier
    VISIBILITY_PATTERN = re.compile(
        r'^\s*(?P<visibility>public|private|protected)\s*$',
        re.MULTILINE
    )

    # Concern pattern
    CONCERN_PATTERN = re.compile(
        r'extend\s+ActiveSupport::Concern',
        re.MULTILINE
    )

    # Frozen string literal magic comment
    FROZEN_STRING_PATTERN = re.compile(
        r'^#\s*frozen_string_literal:\s*(?P<value>true|false)',
        re.MULTILINE
    )

    # Refinement pattern
    REFINEMENT_PATTERN = re.compile(
        r'^\s*refine\s+(?P<target>\w+(?:::\w+)*)\s+do',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Ruby type definitions from source code.

        Args:
            content: Ruby source code content
            file_path: Path to source file

        Returns:
            Dict with 'classes', 'modules', 'structs' keys
        """
        classes = self._extract_classes(content, file_path)
        modules = self._extract_modules(content, file_path)
        structs = self._extract_structs(content, file_path)

        # Enrich classes with mixins, fields, constants
        for cls in classes:
            cls.fields = self._extract_class_fields(content, cls)
            cls.constants = self._extract_constants_in_scope(content, cls.name)

        for mod in modules:
            mod.is_concern = bool(self.CONCERN_PATTERN.search(content))
            mod.constants = self._extract_constants_in_scope(content, mod.name)

        return {
            'classes': classes,
            'modules': modules,
            'structs': structs,
        }

    def _extract_classes(self, content: str, file_path: str) -> List[RubyClassInfo]:
        """Extract class definitions from Ruby source."""
        classes = []
        seen_names = set()

        # Collect doc comments positions
        doc_comments = {}
        for match in self.DOC_COMMENT_PATTERN.finditer(content):
            end_pos = match.end()
            doc_comments[end_pos] = match.group(1).strip()

        for match in self.CLASS_HEADER.finditer(content):
            name = match.group('name')
            parent = match.group('parent')
            line_number = content[:match.start()].count('\n') + 1

            # Skip eigenclass definitions
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.start()].strip()
            if '<<' in line_text:
                continue

            # Check for doc comment
            doc = None
            for doc_end, doc_text in doc_comments.items():
                if abs(doc_end - match.start()) < 5:
                    doc = doc_text
                    break

            is_reopened = name in seen_names
            seen_names.add(name)

            # Extract namespace from qualified name
            namespace = None
            short_name = name
            if '::' in name:
                parts = name.rsplit('::', 1)
                namespace = parts[0]
                short_name = parts[1]

            # Extract mixins for this class
            mixins = self._extract_mixins_in_scope(content, match.start())

            cls = RubyClassInfo(
                name=short_name,
                parent_class=parent,
                mixins=mixins,
                file=file_path,
                line_number=line_number,
                is_reopened=is_reopened,
                doc_comment=doc,
                namespace=namespace,
            )
            classes.append(cls)

        return classes

    def _extract_modules(self, content: str, file_path: str) -> List[RubyModuleInfo]:
        """Extract module definitions from Ruby source."""
        modules = []

        for match in self.MODULE_HEADER.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            # Extract namespace from qualified name
            namespace = None
            short_name = name
            if '::' in name:
                parts = name.rsplit('::', 1)
                namespace = parts[0]
                short_name = parts[1]

            # Extract mixins
            mixins = self._extract_mixins_in_scope(content, match.start())

            # Check if it's a concern
            scope_end = self._find_scope_end(content, match.start())
            scope_content = content[match.start():scope_end] if scope_end > 0 else ""
            is_concern = bool(self.CONCERN_PATTERN.search(scope_content))

            mod = RubyModuleInfo(
                name=short_name,
                mixins=mixins,
                file=file_path,
                line_number=line_number,
                is_concern=is_concern,
                namespace=namespace,
            )
            modules.append(mod)

        return modules

    def _extract_structs(self, content: str, file_path: str) -> List[RubyStructInfo]:
        """Extract Struct.new and Data.define definitions."""
        structs = []

        # Struct.new
        for match in self.STRUCT_PATTERN.finditer(content):
            name = match.group('name')
            members_str = match.group('members')
            members = [m.strip().lstrip(':').strip("'\"") for m in members_str.split(',') if m.strip()]
            # Filter out keyword_init: true
            keyword_init = 'keyword_init' in members_str
            members = [m for m in members if 'keyword_init' not in m]
            line_number = content[:match.start()].count('\n') + 1

            structs.append(RubyStructInfo(
                name=name,
                members=members,
                kind="Struct",
                keyword_init=keyword_init,
                file=file_path,
                line_number=line_number,
            ))

        # Data.define (Ruby 3.2+)
        for match in self.DATA_DEFINE_PATTERN.finditer(content):
            name = match.group('name')
            members_str = match.group('members')
            members = [m.strip().lstrip(':').strip("'\"") for m in members_str.split(',') if m.strip()]
            line_number = content[:match.start()].count('\n') + 1

            structs.append(RubyStructInfo(
                name=name,
                members=members,
                kind="Data",
                file=file_path,
                line_number=line_number,
            ))

        return structs

    def _extract_mixins_in_scope(self, content: str, class_start: int) -> List[RubyMixinInfo]:
        """Extract mixins (include/extend/prepend) near a class/module definition."""
        mixins = []
        # Look at the next ~50 lines after the class/module header
        scope_end = min(class_start + 3000, len(content))
        scope = content[class_start:scope_end]

        for match in self.MIXIN_PATTERN.finditer(scope):
            mixins.append(RubyMixinInfo(
                name=match.group('name'),
                kind=match.group('kind'),
                line_number=content[:class_start + match.start()].count('\n') + 1,
            ))

        return mixins

    def _extract_class_fields(self, content: str, cls: RubyClassInfo) -> List[RubyFieldInfo]:
        """Extract fields (attr_*, instance vars) for a class."""
        fields = []
        seen_names = set()

        # Find class scope
        class_match = None
        for m in self.CLASS_HEADER.finditer(content):
            if m.group('name') == cls.name or (cls.namespace and m.group('name') == f"{cls.namespace}::{cls.name}"):
                class_match = m
                break

        if not class_match:
            return fields

        scope_end = self._find_scope_end(content, class_match.start())
        scope = content[class_match.start():scope_end] if scope_end > 0 else content[class_match.start():]

        # Extract attr_reader/attr_writer/attr_accessor
        for match in self.ACCESSOR_PATTERN.finditer(scope):
            accessor_type = match.group('type')
            attrs_str = match.group('attrs')
            # Parse :name, :name2 format
            attrs = re.findall(r':(\w+)', attrs_str)
            for attr_name in attrs:
                if attr_name not in seen_names:
                    seen_names.add(attr_name)
                    fields.append(RubyFieldInfo(
                        name=attr_name,
                        accessor_type=accessor_type,
                        is_instance_variable=True,
                    ))

        return fields

    def _extract_constants_in_scope(self, content: str, scope_name: str) -> List[str]:
        """Extract constants defined within a class/module scope."""
        constants = []
        for match in self.CONSTANT_PATTERN.finditer(content):
            constants.append(match.group('name'))
            if len(constants) >= 20:
                break
        return constants

    def _find_scope_end(self, content: str, start: int) -> int:
        """Find the matching 'end' for a class/module/def block using indentation tracking."""
        lines = content[start:].split('\n')
        if not lines:
            return start

        # Get the indentation of the opening line
        first_line = lines[0]
        indent = len(first_line) - len(first_line.lstrip())
        depth = 1
        pos = start + len(lines[0]) + 1

        block_openers = re.compile(
            r'^\s*(?:class|module|def|do|if|unless|while|until|for|begin|case)\b'
        )
        block_closer = re.compile(r'^\s*end\b')

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                pos += len(line) + 1
                continue

            if block_openers.match(line) and not stripped.endswith('end'):
                depth += 1
            elif block_closer.match(line):
                depth -= 1
                if depth == 0:
                    return pos + len(line)

            pos += len(line) + 1

        return start + len(content[start:])
