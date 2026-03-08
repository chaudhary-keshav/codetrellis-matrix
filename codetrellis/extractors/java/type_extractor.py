"""
JavaTypeExtractor - Extracts Java class, interface, record, and annotation definitions.

This extractor parses Java source code and extracts:
- Class definitions with fields, methods, inheritance, generics
- Interface definitions with method signatures, default methods
- Record definitions (Java 14+) with components
- Sealed classes/interfaces (Java 17+) with permitted subtypes
- Abstract classes with abstract methods
- Annotation type definitions
- Generic type parameters and bounds

Supports all Java versions from 8 through 21+.

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaGenericParam:
    """Information about a Java generic type parameter."""
    name: str
    bounds: List[str] = field(default_factory=list)  # extends/super bounds


@dataclass
class JavaFieldInfo:
    """Information about a Java class field."""
    name: str
    type: str
    modifiers: List[str] = field(default_factory=list)  # public, private, static, final, etc.
    annotations: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    comment: Optional[str] = None
    is_static: bool = False
    is_final: bool = False


@dataclass
class JavaClassInfo:
    """Information about a Java class."""
    name: str
    kind: str = "class"  # class, abstract_class, sealed_class
    fields: List[JavaFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)  # method signatures
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    permits: List[str] = field(default_factory=list)  # sealed class permits
    annotations: List[str] = field(default_factory=list)
    generic_params: List[JavaGenericParam] = field(default_factory=list)
    inner_classes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True  # public
    is_abstract: bool = False
    is_sealed: bool = False
    is_static: bool = False
    modifiers: List[str] = field(default_factory=list)
    javadoc: Optional[str] = None


@dataclass
class JavaInterfaceInfo:
    """Information about a Java interface."""
    name: str
    methods: List[Dict[str, Any]] = field(default_factory=list)
    default_methods: List[Dict[str, Any]] = field(default_factory=list)
    static_methods: List[Dict[str, Any]] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    permits: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    generic_params: List[JavaGenericParam] = field(default_factory=list)
    constants: List[Dict[str, str]] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_sealed: bool = False
    is_functional: bool = False  # @FunctionalInterface
    javadoc: Optional[str] = None


@dataclass
class JavaRecordInfo:
    """Information about a Java record (Java 14+)."""
    name: str
    components: List[Dict[str, str]] = field(default_factory=list)  # name, type pairs
    implements: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    generic_params: List[JavaGenericParam] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)  # custom methods beyond auto-generated
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    javadoc: Optional[str] = None


@dataclass
class JavaAnnotationDef:
    """Information about a Java annotation type definition."""
    name: str
    elements: List[Dict[str, Any]] = field(default_factory=list)  # annotation elements
    retention: Optional[str] = None  # RUNTIME, CLASS, SOURCE
    target: List[str] = field(default_factory=list)  # TYPE, METHOD, FIELD, etc.
    annotations: List[str] = field(default_factory=list)  # meta-annotations
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    javadoc: Optional[str] = None


class JavaTypeExtractor:
    """
    Extracts Java type definitions from source code.

    Handles:
    - Classes (concrete, abstract, sealed, inner, static)
    - Interfaces (regular, sealed, functional)
    - Records (Java 14+)
    - Annotation type definitions
    - Generic type parameters with bounds
    - Inheritance (extends/implements/permits)
    - Field declarations with annotations
    - Access modifiers (public, private, protected, package-private)

    Uses brace-balanced extraction for nested type bodies.
    """

    # Package declaration
    PACKAGE_PATTERN = re.compile(r'^package\s+([\w.]+)\s*;', re.MULTILINE)

    # Import statements
    IMPORT_PATTERN = re.compile(r'^import\s+(?:static\s+)?([\w.*]+)\s*;', re.MULTILINE)

    # Javadoc comment extraction
    JAVADOC_PATTERN = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)

    # Class header pattern (handles abstract, sealed, final, static, inner classes)
    CLASS_HEADER = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'               # Optional Javadoc
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'    # Annotations
        r'((?:public|protected|private|abstract|final|sealed|static|strictfp)\s+)*'  # Modifiers
        r'class\s+(\w+)'                         # class Name
        r'(?:\s*<([^>]+)>)?'                     # Generic params
        r'(?:\s+extends\s+([\w.<>,\s?]+?))?'     # extends
        r'(?:\s+implements\s+([\w.<>,\s?]+?))?'  # implements
        r'(?:\s+permits\s+([\w,\s]+?))?'         # permits (sealed)
        r'\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Interface header
    INTERFACE_HEADER = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'((?:public|protected|private|sealed|static|strictfp)\s+)*'
        r'interface\s+(\w+)'
        r'(?:\s*<([^>]+)>)?'
        r'(?:\s+extends\s+([\w.<>,\s?]+?))?'
        r'(?:\s+permits\s+([\w,\s]+?))?'
        r'\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Record header (Java 14+)
    RECORD_HEADER = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'((?:public|protected|private|sealed|static|strictfp)\s+)*'
        r'record\s+(\w+)'
        r'(?:\s*<([^>]+)>)?'
        r'\s*\(([^)]*)\)'                       # record components
        r'(?:\s+implements\s+([\w.<>,\s?]+?))?'
        r'\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Enum header (handled by EnumExtractor, but we detect for completeness)
    ENUM_HEADER = re.compile(
        r'((?:public|protected|private|static|strictfp)\s+)*'
        r'enum\s+(\w+)'
        r'(?:\s+implements\s+([\w.<>,\s?]+?))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Annotation type definition
    ANNOTATION_DEF_HEADER = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'((?:public|protected|private)\s+)?'
        r'@interface\s+(\w+)\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Field pattern
    FIELD_PATTERN = re.compile(
        r'^\s*((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'              # annotations
        r'((?:public|protected|private|static|final|volatile|transient|synchronized)\s+)*'  # modifiers
        r'([\w<>\[\].,?\s]+?)\s+'                              # type
        r'(\w+)'                                                # name
        r'(?:\s*=\s*([^;]+))?'                                 # optional initializer
        r'\s*;',
        re.MULTILINE
    )

    # Method signature in interface
    INTERFACE_METHOD_PATTERN = re.compile(
        r'^\s*((?:default|static)\s+)?'        # optional default/static
        r'(?:(?:public|protected)\s+)?'        # optional access modifier
        r'(?:<([^>]+)>\s+)?'                   # optional generic params
        r'([\w<>\[\].,?\s]+?)\s+'              # return type
        r'(\w+)\s*'                            # method name
        r'\(([^)]*)\)',                        # parameters
        re.MULTILINE
    )

    # Annotation element pattern
    ANNOTATION_ELEMENT_PATTERN = re.compile(
        r'^\s*([\w<>\[\].,?\s]+?)\s+(\w+)\s*\(\s*\)'  # type name()
        r'(?:\s+default\s+([^;]+))?'                    # optional default value
        r'\s*;',
        re.MULTILINE
    )

    def __init__(self):
        pass

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """
        Extract body between matched braces using brace-counting.
        Handles nested braces, comments, strings correctly.
        """
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_char = False
        in_line_comment = False
        in_block_comment = False
        string_char = '"'
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue

            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == string_char:
                    in_string = False
                i += 1
                continue

            if in_char:
                if ch == '\\':
                    i += 2
                    continue
                if ch == "'":
                    in_char = False
                i += 1
                continue

            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue

            if ch == '"':
                in_string = True
                string_char = '"'
                i += 1
                continue
            if ch == "'":
                in_char = True
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]

            i += 1

        return None

    def _parse_generic_params(self, generic_str: str) -> List[JavaGenericParam]:
        """Parse generic type parameters like <T extends Comparable<T>, U>."""
        if not generic_str:
            return []
        params = []
        # Simple split - handles basic cases
        depth = 0
        current = ""
        for ch in generic_str:
            if ch == '<':
                depth += 1
                current += ch
            elif ch == '>':
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            params.append(current.strip())

        result = []
        for p in params:
            parts = re.split(r'\s+extends\s+|\s+super\s+', p, maxsplit=1)
            name = parts[0].strip()
            bounds = [parts[1].strip()] if len(parts) > 1 else []
            result.append(JavaGenericParam(name=name, bounds=bounds))
        return result

    def _parse_annotations(self, annotation_str: str) -> List[str]:
        """Parse annotation block into list of annotation names."""
        if not annotation_str:
            return []
        annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotation_str)
        return annotations

    def _extract_fields(self, body: str) -> List[JavaFieldInfo]:
        """Extract field declarations from a class body."""
        fields = []
        for match in self.FIELD_PATTERN.finditer(body):
            annotations_str = match.group(1) or ""
            modifiers_str = match.group(2) or ""
            field_type = match.group(3).strip()
            field_name = match.group(4)
            default_value = match.group(5)

            # Skip if it looks like a method (has parentheses in what we think is the type)
            if '(' in field_type or field_name[0].isupper():
                continue
            # Skip common false positives
            if field_type in ('return', 'throw', 'new', 'if', 'for', 'while', 'switch', 'try', 'catch'):
                continue

            modifiers = modifiers_str.split() if modifiers_str else []
            annotations = self._parse_annotations(annotations_str)

            fields.append(JavaFieldInfo(
                name=field_name,
                type=field_type,
                modifiers=modifiers,
                annotations=annotations,
                default_value=default_value.strip() if default_value else None,
                is_static='static' in modifiers,
                is_final='final' in modifiers,
            ))
        return fields

    def _extract_methods_from_body(self, body: str) -> List[str]:
        """Extract method signatures from a class body (names only for compact representation)."""
        methods = []
        # Match method declarations: modifiers returnType methodName(params)
        method_pattern = re.compile(
            r'(?:(?:public|protected|private|static|final|abstract|synchronized|native|default)\s+)*'
            r'(?:<[^>]+>\s+)?'
            r'(?:[\w<>\[\].,?\s]+?)\s+'
            r'(\w+)\s*\([^)]*\)',
            re.MULTILINE
        )
        for match in method_pattern.finditer(body):
            name = match.group(1)
            # Filter out control flow keywords
            if name not in ('if', 'for', 'while', 'switch', 'try', 'catch', 'return', 'throw', 'new', 'super', 'this'):
                if name not in methods:
                    methods.append(name)
        return methods

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Java type definitions from source code.

        Returns dict with keys: classes, interfaces, records, annotation_defs
        """
        result = {
            'classes': [],
            'interfaces': [],
            'records': [],
            'annotation_defs': [],
            'package': '',
            'imports': [],
        }

        # Extract package
        pkg_match = self.PACKAGE_PATTERN.search(content)
        if pkg_match:
            result['package'] = pkg_match.group(1)

        # Extract imports
        result['imports'] = [m.group(1) for m in self.IMPORT_PATTERN.finditer(content)]

        # Extract classes
        for match in self.CLASS_HEADER.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            class_name = match.group(4)
            generic_str = match.group(5)
            extends_str = match.group(6)
            implements_str = match.group(7)
            permits_str = match.group(8)

            # Find the opening brace position
            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            modifiers = modifiers_str.split() if modifiers_str else []
            annotations = self._parse_annotations(annotations_str)
            is_abstract = 'abstract' in modifiers
            is_sealed = 'sealed' in modifiers

            kind = "class"
            if is_abstract:
                kind = "abstract_class"
            elif is_sealed:
                kind = "sealed_class"

            fields = self._extract_fields(body) if body else []
            method_names = self._extract_methods_from_body(body) if body else []
            generic_params = self._parse_generic_params(generic_str)

            implements = [s.strip() for s in implements_str.split(',')] if implements_str else []
            permits = [s.strip() for s in permits_str.split(',')] if permits_str else []

            # Detect inner classes
            inner_classes = []
            if body:
                for inner_match in re.finditer(r'(?:static\s+)?class\s+(\w+)', body):
                    inner_classes.append(inner_match.group(1))

            # Extract first line of javadoc
            javadoc_text = None
            if javadoc:
                # Clean up javadoc
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            is_public = 'public' in modifiers
            line_number = content[:match.start()].count('\n') + 1

            result['classes'].append(JavaClassInfo(
                name=class_name,
                kind=kind,
                fields=fields,
                methods=method_names,
                extends=extends_str.strip() if extends_str else None,
                implements=implements,
                permits=permits,
                annotations=annotations,
                generic_params=generic_params,
                inner_classes=inner_classes,
                file=file_path,
                line_number=line_number,
                is_exported=is_public,
                is_abstract=is_abstract,
                is_sealed=is_sealed,
                is_static='static' in modifiers,
                modifiers=modifiers,
                javadoc=javadoc_text,
            ))

        # Extract interfaces
        for match in self.INTERFACE_HEADER.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            iface_name = match.group(4)
            generic_str = match.group(5)
            extends_str = match.group(6)
            permits_str = match.group(7)

            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            modifiers = modifiers_str.split() if modifiers_str else []
            annotations = self._parse_annotations(annotations_str)
            is_sealed = 'sealed' in modifiers
            is_functional = '@FunctionalInterface' in annotations_str

            # Extract interface methods
            methods = []
            default_methods = []
            static_methods = []
            constants = []

            if body:
                for m_match in self.INTERFACE_METHOD_PATTERN.finditer(body):
                    modifier = (m_match.group(1) or "").strip()
                    return_type = m_match.group(3).strip()
                    method_name = m_match.group(4)
                    params_str = m_match.group(5)

                    if method_name in ('if', 'for', 'while', 'switch', 'try', 'catch', 'return'):
                        continue

                    method_info = {
                        'name': method_name,
                        'return_type': return_type,
                        'params': params_str.strip(),
                    }

                    if modifier == 'default':
                        default_methods.append(method_info)
                    elif modifier == 'static':
                        static_methods.append(method_info)
                    else:
                        methods.append(method_info)

                # Extract constants (static final fields in interfaces)
                for f in self._extract_fields(body):
                    if f.is_static or f.is_final:
                        constants.append({'name': f.name, 'type': f.type})

            extends_list = [s.strip() for s in extends_str.split(',')] if extends_str else []
            permits = [s.strip() for s in permits_str.split(',')] if permits_str else []
            generic_params = self._parse_generic_params(generic_str)

            javadoc_text = None
            if javadoc:
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            line_number = content[:match.start()].count('\n') + 1

            result['interfaces'].append(JavaInterfaceInfo(
                name=iface_name,
                methods=methods,
                default_methods=default_methods,
                static_methods=static_methods,
                extends=extends_list,
                permits=permits,
                annotations=annotations,
                generic_params=generic_params,
                constants=constants,
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers,
                is_sealed=is_sealed,
                is_functional=is_functional,
                javadoc=javadoc_text,
            ))

        # Extract records (Java 14+)
        for match in self.RECORD_HEADER.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            record_name = match.group(4)
            generic_str = match.group(5)
            components_str = match.group(6)
            implements_str = match.group(7)

            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            annotations = self._parse_annotations(annotations_str)
            modifiers = modifiers_str.split() if modifiers_str else []
            generic_params = self._parse_generic_params(generic_str)
            implements = [s.strip() for s in implements_str.split(',')] if implements_str else []

            # Parse components
            components = []
            if components_str:
                for comp in self._split_params(components_str):
                    comp = comp.strip()
                    if comp:
                        parts = comp.rsplit(None, 1)
                        if len(parts) == 2:
                            components.append({'type': parts[0], 'name': parts[1]})

            method_names = self._extract_methods_from_body(body) if body else []

            javadoc_text = None
            if javadoc:
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            line_number = content[:match.start()].count('\n') + 1

            result['records'].append(JavaRecordInfo(
                name=record_name,
                components=components,
                implements=implements,
                annotations=annotations,
                generic_params=generic_params,
                methods=method_names,
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers,
                javadoc=javadoc_text,
            ))

        # Extract annotation definitions
        for match in self.ANNOTATION_DEF_HEADER.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            annotation_name = match.group(4)

            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            annotations = self._parse_annotations(annotations_str)

            # Parse elements
            elements = []
            retention = None
            target = []

            if body:
                for elem_match in self.ANNOTATION_ELEMENT_PATTERN.finditer(body):
                    elements.append({
                        'type': elem_match.group(1).strip(),
                        'name': elem_match.group(2),
                        'default': elem_match.group(3).strip() if elem_match.group(3) else None,
                    })

            # Check meta-annotations
            for ann in annotations:
                if ann.startswith('Retention'):
                    ret_match = re.search(r'RetentionPolicy\.(\w+)', ann)
                    if ret_match:
                        retention = ret_match.group(1)
                elif ann.startswith('Target'):
                    targets = re.findall(r'ElementType\.(\w+)', ann)
                    target = targets

            javadoc_text = None
            if javadoc:
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            line_number = content[:match.start()].count('\n') + 1

            result['annotation_defs'].append(JavaAnnotationDef(
                name=annotation_name,
                elements=elements,
                retention=retention,
                target=target,
                annotations=annotations,
                file=file_path,
                line_number=line_number,
                is_exported='public' in (modifiers_str or ''),
                javadoc=javadoc_text,
            ))

        return result

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameter list respecting generic brackets."""
        params = []
        depth = 0
        current = ""
        for ch in params_str:
            if ch in ('<', '(', '['):
                depth += 1
                current += ch
            elif ch in ('>', ')', ']'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            params.append(current.strip())
        return params
