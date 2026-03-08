"""
PhpTypeExtractor - Extracts PHP class, interface, trait, and enum definitions.

This extractor parses PHP source code and extracts:
- Class definitions with inheritance, interfaces, traits
- Interface definitions with extends
- Trait definitions with use declarations
- Enum definitions (PHP 8.1+) with backed types
- Abstract classes
- Final classes
- Anonymous classes (PHP 7+)
- Readonly classes (PHP 8.2+)
- Class constants (including typed constants PHP 8.3+)
- Property declarations with types (PHP 7.4+ typed properties)
- Readonly properties (PHP 8.1+)
- Constructor property promotion (PHP 8.0+)
- Namespace and use import tracking
- PHPDoc comment extraction
- Visibility modifiers

Supports PHP 5.x through PHP 8.3+ features.

Part of CodeTrellis v4.24 - PHP Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PhpFieldInfo:
    """Information about a PHP property/field."""
    name: str
    type_hint: Optional[str] = None
    visibility: str = "public"
    is_static: bool = False
    is_readonly: bool = False
    is_nullable: bool = False
    default_value: Optional[str] = None
    is_promoted: bool = False  # Constructor promotion (PHP 8.0+)
    doc_comment: Optional[str] = None


@dataclass
class PhpConstantInfo:
    """Information about a PHP class constant."""
    name: str
    value: Optional[str] = None
    visibility: str = "public"
    type_hint: Optional[str] = None  # PHP 8.3+ typed constants
    is_final: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class PhpClassInfo:
    """Information about a PHP class."""
    name: str
    parent_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    properties: List[PhpFieldInfo] = field(default_factory=list)
    constants: List[PhpConstantInfo] = field(default_factory=list)
    namespace: Optional[str] = None
    visibility: str = ""
    file: str = ""
    line_number: int = 0
    is_abstract: bool = False
    is_final: bool = False
    is_readonly: bool = False  # PHP 8.2+
    is_anonymous: bool = False  # PHP 7+
    doc_comment: Optional[str] = None


@dataclass
class PhpInterfaceInfo:
    """Information about a PHP interface."""
    name: str
    extends: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    constants: List[PhpConstantInfo] = field(default_factory=list)
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class PhpTraitInfo:
    """Information about a PHP trait."""
    name: str
    methods: List[str] = field(default_factory=list)
    properties: List[PhpFieldInfo] = field(default_factory=list)
    uses_traits: List[str] = field(default_factory=list)
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class PhpEnumInfo:
    """Information about a PHP enum (PHP 8.1+)."""
    name: str
    backed_type: Optional[str] = None  # string, int, or None (pure enum)
    cases: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


class PhpTypeExtractor:
    """
    Extracts PHP type definitions from source code.

    Handles:
    - Class definitions with extends/implements
    - Interface definitions with extends
    - Trait definitions and use declarations
    - Enum definitions (PHP 8.1+) with backed types
    - Abstract and final classes
    - Readonly classes (PHP 8.2+)
    - Anonymous classes (PHP 7+)
    - Namespace tracking
    - Property declarations with typed properties (PHP 7.4+)
    - Readonly properties (PHP 8.1+)
    - Constructor property promotion (PHP 8.0+)
    - Class constants (typed PHP 8.3+)
    - PHPDoc comment extraction

    v4.24: Comprehensive PHP type extraction with all modern PHP features.
    """

    # Namespace declaration
    NAMESPACE_PATTERN = re.compile(
        r'^\s*namespace\s+(?P<name>[A-Za-z_\\][A-Za-z0-9_\\]*)\s*[;{]',
        re.MULTILINE
    )

    # Use import declarations
    USE_IMPORT_PATTERN = re.compile(
        r'^\s*use\s+(?P<name>[A-Za-z_\\][A-Za-z0-9_\\]*(?:\s*,\s*[A-Za-z_\\][A-Za-z0-9_\\]*)*)\s*(?:as\s+(?P<alias>\w+))?\s*;',
        re.MULTILINE
    )

    # Class definition
    CLASS_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*(?P<abstract>abstract\s+)?(?P<final>final\s+)?(?P<readonly>readonly\s+)?'
        r'class\s+(?P<name>\w+)'
        r'(?:\s+extends\s+(?P<parent>[A-Za-z_\\][A-Za-z0-9_\\]*))?'
        r'(?:\s+implements\s+(?P<interfaces>[A-Za-z_\\][A-Za-z0-9_\\,\s]*))?',
        re.MULTILINE
    )

    # Interface definition
    INTERFACE_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*interface\s+(?P<name>\w+)'
        r'(?:\s+extends\s+(?P<extends>[A-Za-z_\\][A-Za-z0-9_\\,\s]*))?',
        re.MULTILINE
    )

    # Trait definition
    TRAIT_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*trait\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Enum definition (PHP 8.1+)
    ENUM_PATTERN = re.compile(
        r'(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)'
        r'^\s*enum\s+(?P<name>\w+)'
        r'(?:\s*:\s*(?P<backed_type>string|int))?'
        r'(?:\s+implements\s+(?P<interfaces>[A-Za-z_\\][A-Za-z0-9_\\,\s]*))?',
        re.MULTILINE
    )

    # Property declaration (PHP 7.4+ typed properties)
    PROPERTY_PATTERN = re.compile(
        r'^\s*(?P<visibility>public|protected|private)\s+'
        r'(?P<static>static\s+)?'
        r'(?P<readonly>readonly\s+)?'
        r'(?P<nullable>\?)?(?P<type>[A-Za-z_\\][A-Za-z0-9_\\|&]*\s+)?'
        r'\$(?P<name>\w+)'
        r'(?:\s*=\s*(?P<default>[^;]+))?;',
        re.MULTILINE
    )

    # Class constant
    CONSTANT_PATTERN = re.compile(
        r'^\s*(?P<visibility>public|protected|private)?\s*'
        r'(?P<final>final\s+)?'
        r'const\s+'
        r'(?P<type>[A-Za-z_\\][A-Za-z0-9_\\|]*\s+)?'
        r'(?P<name>[A-Z_][A-Z0-9_]*)\s*=\s*(?P<value>[^;]+);',
        re.MULTILINE
    )

    # Trait use declaration inside a class
    TRAIT_USE_PATTERN = re.compile(
        r'^\s*use\s+(?P<traits>[A-Za-z_\\][A-Za-z0-9_\\,\s]*)\s*[;{]',
        re.MULTILINE
    )

    # Enum case
    ENUM_CASE_PATTERN = re.compile(
        r'^\s*case\s+(?P<name>\w+)(?:\s*=\s*(?P<value>[^;]+))?;',
        re.MULTILINE
    )

    # Anonymous class (PHP 7+)
    ANONYMOUS_CLASS_PATTERN = re.compile(
        r'new\s+class\s*(?:\([^)]*\))?\s*'
        r'(?:extends\s+(?P<parent>[A-Za-z_\\]\w*))?'
        r'(?:\s+implements\s+(?P<interfaces>[A-Za-z_\\][\w\\,\s]*))?',
        re.MULTILINE
    )

    # Constructor property promotion (PHP 8.0+)
    CONSTRUCTOR_PROMOTION_PATTERN = re.compile(
        r'(?P<visibility>public|protected|private)\s+'
        r'(?P<readonly>readonly\s+)?'
        r'(?P<nullable>\?)?(?P<type>[A-Za-z_\\][A-Za-z0-9_\\|&]*)\s+'
        r'\$(?P<name>\w+)',
    )

    # PHPDoc comment
    DOC_COMMENT_PATTERN = re.compile(
        r'/\*\*\s*([\s\S]*?)\*/',
    )

    def __init__(self):
        """Initialize the type extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all PHP type definitions from source code.

        Args:
            content: PHP source code content
            file_path: Path to source file

        Returns:
            Dict with 'classes', 'interfaces', 'traits', 'enums' keys
        """
        namespace = self._extract_namespace(content)
        classes = self._extract_classes(content, file_path, namespace)
        interfaces = self._extract_interfaces(content, file_path, namespace)
        traits = self._extract_traits(content, file_path, namespace)
        enums = self._extract_enums(content, file_path, namespace)

        return {
            'classes': classes,
            'interfaces': interfaces,
            'traits': traits,
            'enums': enums,
            'namespace': namespace,
        }

    def _extract_namespace(self, content: str) -> Optional[str]:
        """Extract the namespace declaration."""
        match = self.NAMESPACE_PATTERN.search(content)
        if match:
            return match.group('name')
        return None

    def _extract_doc_comment(self, text: str) -> Optional[str]:
        """Extract the last PHPDoc comment before a declaration."""
        if not text:
            return None
        text = text.strip()
        match = self.DOC_COMMENT_PATTERN.search(text)
        if match:
            comment = match.group(1).strip()
            # Clean up * prefixes
            lines = []
            for line in comment.split('\n'):
                line = re.sub(r'^\s*\*\s?', '', line).strip()
                if line:
                    lines.append(line)
            return ' '.join(lines)[:200]
        return None

    def _extract_classes(self, content: str, file_path: str, namespace: Optional[str]) -> List[PhpClassInfo]:
        """Extract class definitions from PHP source."""
        classes = []
        lines = content.split('\n')

        for match in self.CLASS_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            doc = self._extract_doc_comment(match.group('doc'))

            interfaces_str = match.group('interfaces')
            interfaces = []
            if interfaces_str:
                interfaces = [i.strip() for i in interfaces_str.split(',') if i.strip()]

            cls = PhpClassInfo(
                name=match.group('name'),
                parent_class=match.group('parent'),
                interfaces=interfaces,
                namespace=namespace,
                file=file_path,
                line_number=line_number,
                is_abstract=bool(match.group('abstract')),
                is_final=bool(match.group('final')),
                is_readonly=bool(match.group('readonly')),
                doc_comment=doc,
            )

            # Extract class body for traits, properties, constants
            body = self._extract_body(content, match.end())
            if body:
                cls.traits = self._extract_trait_uses(body)
                cls.properties = self._extract_properties(body)
                cls.constants = self._extract_constants(body, file_path, line_number)

                # Extract constructor promoted properties
                promoted = self._extract_promoted_properties(body)
                cls.properties.extend(promoted)

            classes.append(cls)

        return classes

    def _extract_interfaces(self, content: str, file_path: str, namespace: Optional[str]) -> List[PhpInterfaceInfo]:
        """Extract interface definitions."""
        interfaces = []

        for match in self.INTERFACE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            doc = self._extract_doc_comment(match.group('doc'))

            extends_str = match.group('extends')
            extends = []
            if extends_str:
                extends = [e.strip() for e in extends_str.split(',') if e.strip()]

            iface = PhpInterfaceInfo(
                name=match.group('name'),
                extends=extends,
                namespace=namespace,
                file=file_path,
                line_number=line_number,
                doc_comment=doc,
            )

            # Extract interface body for method signatures and constants
            body = self._extract_body(content, match.end())
            if body:
                iface.constants = self._extract_constants(body, file_path, line_number)

            interfaces.append(iface)

        return interfaces

    def _extract_traits(self, content: str, file_path: str, namespace: Optional[str]) -> List[PhpTraitInfo]:
        """Extract trait definitions."""
        traits = []

        for match in self.TRAIT_PATTERN.finditer(content):
            # Avoid matching 'use Trait;' inside classes
            line_text = content[content.rfind('\n', 0, match.start()) + 1:match.start()].strip()
            if line_text and not line_text.startswith(('trait', '//', '/*', '*', '#')):
                continue

            line_number = content[:match.start()].count('\n') + 1
            doc = self._extract_doc_comment(match.group('doc'))

            trait = PhpTraitInfo(
                name=match.group('name'),
                namespace=namespace,
                file=file_path,
                line_number=line_number,
                doc_comment=doc,
            )

            body = self._extract_body(content, match.end())
            if body:
                trait.uses_traits = self._extract_trait_uses(body)
                trait.properties = self._extract_properties(body)

            traits.append(trait)

        return traits

    def _extract_enums(self, content: str, file_path: str, namespace: Optional[str]) -> List[PhpEnumInfo]:
        """Extract enum definitions (PHP 8.1+)."""
        enums = []

        for match in self.ENUM_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            doc = self._extract_doc_comment(match.group('doc'))

            interfaces_str = match.group('interfaces')
            implements = []
            if interfaces_str:
                implements = [i.strip() for i in interfaces_str.split(',') if i.strip()]

            enum = PhpEnumInfo(
                name=match.group('name'),
                backed_type=match.group('backed_type'),
                implements=implements,
                namespace=namespace,
                file=file_path,
                line_number=line_number,
                doc_comment=doc,
            )

            # Extract enum body for cases, methods, traits
            body = self._extract_body(content, match.end())
            if body:
                enum.cases = self._extract_enum_cases(body)
                enum.traits = self._extract_trait_uses(body)

            enums.append(enum)

        return enums

    def _extract_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract body between matching braces."""
        brace_start = content.find('{', start_pos)
        if brace_start == -1:
            return None

        depth = 1
        pos = brace_start + 1
        while pos < len(content) and depth > 0:
            ch = content[pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch == "'" or ch == '"':
                # Skip strings
                quote = ch
                pos += 1
                while pos < len(content) and content[pos] != quote:
                    if content[pos] == '\\':
                        pos += 1
                    pos += 1
            elif ch == '/' and pos + 1 < len(content):
                if content[pos + 1] == '/':
                    # Skip line comment
                    pos = content.find('\n', pos)
                    if pos == -1:
                        break
                elif content[pos + 1] == '*':
                    # Skip block comment
                    pos = content.find('*/', pos + 2)
                    if pos == -1:
                        break
                    pos += 1
            pos += 1

        if depth == 0:
            return content[brace_start + 1:pos - 1]
        return None

    def _extract_trait_uses(self, body: str) -> List[str]:
        """Extract trait use declarations from class/trait body."""
        traits = []
        for match in self.TRAIT_USE_PATTERN.finditer(body):
            traits_str = match.group('traits')
            for t in traits_str.split(','):
                t = t.strip()
                if t:
                    # Get short name from fully qualified
                    short = t.rsplit('\\', 1)[-1]
                    traits.append(short)
        return traits

    def _extract_properties(self, body: str) -> List[PhpFieldInfo]:
        """Extract property declarations."""
        properties = []
        for match in self.PROPERTY_PATTERN.finditer(body):
            type_hint = match.group('type')
            if type_hint:
                type_hint = type_hint.strip()
            nullable = bool(match.group('nullable'))
            if nullable and type_hint:
                type_hint = f"?{type_hint}"

            prop = PhpFieldInfo(
                name=match.group('name'),
                type_hint=type_hint,
                visibility=match.group('visibility'),
                is_static=bool(match.group('static')),
                is_readonly=bool(match.group('readonly')),
                is_nullable=nullable,
                default_value=match.group('default').strip() if match.group('default') else None,
            )
            properties.append(prop)
        return properties

    def _extract_promoted_properties(self, body: str) -> List[PhpFieldInfo]:
        """Extract constructor-promoted properties (PHP 8.0+)."""
        promoted = []
        # Find constructor
        ctor_match = re.search(
            r'function\s+__construct\s*\((?P<params>[^)]*)\)',
            body, re.DOTALL
        )
        if not ctor_match:
            return promoted

        params_str = ctor_match.group('params')
        for match in self.CONSTRUCTOR_PROMOTION_PATTERN.finditer(params_str):
            nullable = bool(match.group('nullable'))
            type_hint = match.group('type')
            if nullable:
                type_hint = f"?{type_hint}"

            promoted.append(PhpFieldInfo(
                name=match.group('name'),
                type_hint=type_hint,
                visibility=match.group('visibility'),
                is_readonly=bool(match.group('readonly')),
                is_nullable=nullable,
                is_promoted=True,
            ))

        return promoted

    def _extract_constants(self, body: str, file_path: str, base_line: int) -> List[PhpConstantInfo]:
        """Extract class constants."""
        constants = []
        for match in self.CONSTANT_PATTERN.finditer(body):
            visibility = match.group('visibility') or 'public'
            type_hint = match.group('type')
            if type_hint:
                type_hint = type_hint.strip()

            constants.append(PhpConstantInfo(
                name=match.group('name'),
                value=match.group('value').strip() if match.group('value') else None,
                visibility=visibility,
                type_hint=type_hint,
                is_final=bool(match.group('final')),
                file=file_path,
                line_number=base_line + body[:match.start()].count('\n'),
            ))
        return constants

    def _extract_enum_cases(self, body: str) -> List[str]:
        """Extract enum case names."""
        cases = []
        for match in self.ENUM_CASE_PATTERN.finditer(body):
            cases.append(match.group('name'))
        return cases
