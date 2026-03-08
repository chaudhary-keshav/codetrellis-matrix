"""
CSharpTypeExtractor - Extracts C# class, interface, struct, record, and delegate definitions.

This extractor parses C# source code and extracts:
- Class definitions with fields, properties, methods, inheritance, generics
- Interface definitions with method signatures, default interface implementations
- Struct definitions (value types) including ref/readonly struct
- Record/record struct definitions (C# 9/10+) with positional parameters
- Sealed, abstract, partial, static class modifiers
- Delegate definitions
- Generic type parameters and constraints (where T : class, new())
- Nullable reference types

Supports all C# versions from 1.0 through 13 (latest).

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSharpGenericParam:
    """Information about a C# generic type parameter."""
    name: str
    constraints: List[str] = field(default_factory=list)  # where T : class, IDisposable


@dataclass
class CSharpFieldInfo:
    """Information about a C# field."""
    name: str
    type: str
    modifiers: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    default_value: Optional[str] = None
    is_static: bool = False
    is_readonly: bool = False
    is_const: bool = False
    is_required: bool = False  # C# 11


@dataclass
class CSharpPropertyInfo:
    """Information about a C# property."""
    name: str
    type: str
    has_getter: bool = True
    has_setter: bool = False
    has_init: bool = False  # C# 9 init-only setter
    modifiers: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_auto: bool = True
    is_required: bool = False  # C# 11


@dataclass
class CSharpClassInfo:
    """Information about a C# class."""
    name: str
    kind: str = "class"  # class, abstract_class, sealed_class, static_class
    fields: List[CSharpFieldInfo] = field(default_factory=list)
    properties: List[CSharpPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    base_class: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    generic_params: List[CSharpGenericParam] = field(default_factory=list)
    nested_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True  # public
    is_abstract: bool = False
    is_sealed: bool = False
    is_static: bool = False
    is_partial: bool = False
    namespace: str = ""
    modifiers: List[str] = field(default_factory=list)
    xml_doc: Optional[str] = None


@dataclass
class CSharpInterfaceInfo:
    """Information about a C# interface."""
    name: str
    methods: List[Dict[str, Any]] = field(default_factory=list)
    properties: List[CSharpPropertyInfo] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    generic_params: List[CSharpGenericParam] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    namespace: str = ""
    xml_doc: Optional[str] = None


@dataclass
class CSharpStructInfo:
    """Information about a C# struct (value type)."""
    name: str
    fields: List[CSharpFieldInfo] = field(default_factory=list)
    properties: List[CSharpPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    generic_params: List[CSharpGenericParam] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_readonly: bool = False
    is_ref: bool = False  # ref struct (C# 7.2)
    is_record: bool = False  # record struct (C# 10)
    namespace: str = ""
    modifiers: List[str] = field(default_factory=list)


@dataclass
class CSharpRecordInfo:
    """Information about a C# record (C# 9+) or record struct (C# 10+)."""
    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)  # positional params
    base_record: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    generic_params: List[CSharpGenericParam] = field(default_factory=list)
    additional_members: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_struct: bool = False  # record struct vs record class
    namespace: str = ""


@dataclass
class CSharpDelegateInfo:
    """Information about a C# delegate type."""
    name: str
    return_type: str = "void"
    parameters: List[Dict[str, str]] = field(default_factory=list)
    generic_params: List[CSharpGenericParam] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    namespace: str = ""


class CSharpTypeExtractor:
    """
    Extracts C# type definitions from source code.

    Handles:
    - Classes (abstract, sealed, static, partial)
    - Interfaces (including default implementations C# 8+)
    - Structs (readonly, ref, record struct)
    - Records (record class C# 9+, record struct C# 10+)
    - Delegates
    - Generic type parameters with constraints
    - Attribute decorations
    - Properties (auto, init-only, required)
    - Nullable reference type annotations (T?)
    - Primary constructors (C# 12)
    """

    # Namespace pattern
    NAMESPACE_PATTERN = re.compile(
        r'(?:^|\n)\s*namespace\s+([\w.]+)\s*[{;]',
        re.MULTILINE
    )

    # File-scoped namespace (C# 10)
    FILE_SCOPED_NAMESPACE = re.compile(
        r'^\s*namespace\s+([\w.]+)\s*;',
        re.MULTILINE
    )

    # Using directives
    USING_PATTERN = re.compile(r'^\s*using\s+(?:static\s+)?([\w.=\s]+);', re.MULTILINE)

    # Class pattern (handles all modifiers)
    CLASS_PATTERN = re.compile(
        r'(?:(?:///.*\n)*)?'                              # Optional XML docs
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'                # Attributes
        r'((?:public|private|protected|internal|static|abstract|sealed|partial|new|unsafe)\s+)*'  # Modifiers
        r'class\s+'                                        # class keyword
        r'(\w+)'                                           # Class name
        r'(?:<([^>]+)>)?'                                  # Optional generic params
        r'(?:\s*\([^)]*\))?'                               # Optional primary constructor (C# 12)
        r'(?:\s*:\s*([^\n{]+))?'                           # Optional base/interfaces
        r'(?:\s*(?:where\s+\w+\s*:[^{]+))*'               # Optional generic constraints
        r'\s*\{',
        re.MULTILINE
    )

    # Interface pattern
    INTERFACE_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|partial|new)\s+)*'
        r'interface\s+'
        r'(\w+)'
        r'(?:<([^>]+)>)?'
        r'(?:\s*:\s*([^\n{]+))?'
        r'(?:\s*(?:where\s+\w+\s*:[^{]+))*'
        r'\s*\{',
        re.MULTILINE
    )

    # Struct pattern (includes ref struct, readonly struct, record struct)
    STRUCT_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|partial|readonly|ref|unsafe|new)\s+)*'
        r'struct\s+'
        r'(\w+)'
        r'(?:<([^>]+)>)?'
        r'(?:\s*:\s*([^\n{]+))?'
        r'(?:\s*(?:where\s+\w+\s*:[^{]+))*'
        r'\s*\{',
        re.MULTILINE
    )

    # Record pattern (C# 9+)
    RECORD_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|partial|abstract|sealed)\s+)*'
        r'record\s+(?:(struct|class)\s+)?'                # record [struct|class]
        r'(\w+)'                                           # Record name
        r'(?:<([^>]+)>)?'                                  # Optional generics
        r'(?:\s*\(([^)]*)\))?'                             # Optional positional params
        r'(?:\s*:\s*([^\n{;]+))?'                          # Optional base/interfaces
        r'\s*[{;]',
        re.MULTILINE
    )

    # Delegate pattern
    DELEGATE_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|unsafe)\s+)*'
        r'delegate\s+'
        r'([\w<>\[\]?,\s]+?)\s+'                          # Return type
        r'(\w+)'                                           # Delegate name
        r'(?:<([^>]+)>)?'                                  # Optional generics
        r'\s*\(([^)]*)\)\s*;',                             # Parameters
        re.MULTILINE
    )

    # Property pattern
    PROPERTY_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'                # Attributes
        r'((?:public|private|protected|internal|static|virtual|override|abstract|sealed|new|required|readonly)\s+)*'
        r'([\w<>\[\]?,.\s]+?)\s+'                          # Type
        r'(\w+)\s*'                                        # Property name
        r'\{([^}]*)\}',                                    # Accessors
        re.MULTILINE | re.DOTALL
    )

    # Field pattern
    FIELD_PATTERN = re.compile(
        r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
        r'((?:public|private|protected|internal|static|readonly|const|volatile|required|new|unsafe)\s+)*'
        r'([\w<>\[\]?,.\s]+?)\s+'
        r'(\w+)\s*'
        r'(?:=\s*([^;]+))?\s*;',
        re.MULTILINE
    )

    # Generic constraint pattern
    CONSTRAINT_PATTERN = re.compile(
        r'where\s+(\w+)\s*:\s*([^{;]+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all type definitions from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: classes, interfaces, structs, records, delegates
        """
        result = {
            "classes": [],
            "interfaces": [],
            "structs": [],
            "records": [],
            "delegates": [],
        }

        # Detect namespace
        namespace = self._detect_namespace(content)

        # Extract generic constraints for later use
        constraints = self._extract_constraints(content)

        # Extract classes
        for match in self.CLASS_PATTERN.finditer(content):
            cls = self._parse_class(match, content, file_path, namespace, constraints)
            if cls:
                result["classes"].append(cls)

        # Extract interfaces
        for match in self.INTERFACE_PATTERN.finditer(content):
            iface = self._parse_interface(match, content, file_path, namespace, constraints)
            if iface:
                result["interfaces"].append(iface)

        # Extract structs
        for match in self.STRUCT_PATTERN.finditer(content):
            struct = self._parse_struct(match, content, file_path, namespace, constraints)
            if struct:
                result["structs"].append(struct)

        # Extract records
        for match in self.RECORD_PATTERN.finditer(content):
            rec = self._parse_record(match, content, file_path, namespace, constraints)
            if rec:
                result["records"].append(rec)

        # Extract delegates
        for match in self.DELEGATE_PATTERN.finditer(content):
            dlg = self._parse_delegate(match, file_path, namespace, constraints)
            if dlg:
                result["delegates"].append(dlg)

        return result

    def _detect_namespace(self, content: str) -> str:
        """Detect the namespace of the file."""
        # File-scoped namespace first (C# 10+)
        m = self.FILE_SCOPED_NAMESPACE.search(content)
        if m:
            return m.group(1)
        # Traditional namespace
        m = self.NAMESPACE_PATTERN.search(content)
        if m:
            return m.group(1)
        return ""

    def _extract_constraints(self, content: str) -> Dict[str, List[str]]:
        """Extract generic constraints (where T : class, new())."""
        constraints = {}
        for m in self.CONSTRAINT_PATTERN.finditer(content):
            param_name = m.group(1)
            constraint_text = m.group(2).strip().rstrip('{').rstrip(';').strip()
            parts = [c.strip() for c in constraint_text.split(',')]
            constraints[param_name] = parts
        return constraints

    def _parse_attributes(self, attr_str: str) -> List[str]:
        """Parse attribute decorations from string."""
        attrs = []
        if not attr_str:
            return attrs
        # Extract [Attribute] and [Attribute(params)]
        for m in re.finditer(r'\[(\w[\w.,\s()="]*?)\]', attr_str):
            attr_text = m.group(1).strip()
            # Get just the attribute name (before parens)
            attr_name = re.match(r'(\w+)', attr_text)
            if attr_name:
                attrs.append(attr_name.group(1))
        return attrs

    def _parse_modifiers(self, mod_str: str) -> List[str]:
        """Parse access and other modifiers."""
        if not mod_str:
            return []
        return [m.strip() for m in mod_str.split() if m.strip()]

    def _is_exported(self, modifiers: List[str]) -> bool:
        """Check if type is public/internal (exported)."""
        return 'public' in modifiers or 'internal' in modifiers or not any(
            m in modifiers for m in ('private', 'protected')
        )

    def _extract_brace_body(self, content: str, start_pos: int) -> str:
        """Extract body between matched braces starting at start_pos."""
        brace_count = 0
        i = start_pos
        body_start = None
        while i < len(content):
            if content[i] == '{':
                if body_start is None:
                    body_start = i + 1
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[body_start:i] if body_start else ""
            i += 1
        return content[body_start:] if body_start else ""

    def _parse_generic_params(self, gen_str: str, constraints: Dict[str, List[str]]) -> List[CSharpGenericParam]:
        """Parse generic type parameters with constraints."""
        if not gen_str:
            return []
        params = []
        for p in gen_str.split(','):
            p = p.strip()
            if p:
                cons = constraints.get(p, [])
                params.append(CSharpGenericParam(name=p, constraints=cons))
        return params

    def _parse_base_types(self, base_str: str) -> tuple:
        """Parse base class and implemented interfaces from inheritance clause."""
        if not base_str:
            return None, []
        parts = [p.strip() for p in base_str.split(',')]
        base_class = None
        interfaces = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            # Remove generic constraints that may appear
            part = re.sub(r'\s+where\s+.*', '', part).strip()
            if i == 0:
                # First could be base class or interface
                if part.startswith('I') and len(part) > 1 and part[1].isupper():
                    interfaces.append(part)
                else:
                    base_class = part
            else:
                interfaces.append(part)
        return base_class, interfaces

    def _parse_class(self, match, content: str, file_path: str, namespace: str,
                     constraints: Dict[str, List[str]]) -> Optional[CSharpClassInfo]:
        """Parse a class definition from regex match."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            name = match.group(3)
            gen_str = match.group(4) or ""
            base_str = match.group(5) or ""

            modifiers = self._parse_modifiers(mod_str)
            is_abstract = 'abstract' in modifiers
            is_sealed = 'sealed' in modifiers
            is_static = 'static' in modifiers
            is_partial = 'partial' in modifiers

            kind = "class"
            if is_abstract:
                kind = "abstract_class"
            elif is_sealed:
                kind = "sealed_class"
            elif is_static:
                kind = "static_class"

            base_class, implements = self._parse_base_types(base_str)

            # Extract body for fields, properties, methods
            body = self._extract_brace_body(content, match.start())
            fields = self._extract_fields(body)
            properties = self._extract_properties(body)
            methods = self._extract_method_names(body)

            line_number = content[:match.start()].count('\n') + 1

            return CSharpClassInfo(
                name=name,
                kind=kind,
                fields=fields,
                properties=properties,
                methods=methods,
                base_class=base_class,
                implements=implements,
                attributes=self._parse_attributes(attr_str),
                generic_params=self._parse_generic_params(gen_str, constraints),
                file=file_path,
                line_number=line_number,
                is_exported=self._is_exported(modifiers),
                is_abstract=is_abstract,
                is_sealed=is_sealed,
                is_static=is_static,
                is_partial=is_partial,
                namespace=namespace,
                modifiers=modifiers,
            )
        except Exception:
            return None

    def _parse_interface(self, match, content: str, file_path: str, namespace: str,
                         constraints: Dict[str, List[str]]) -> Optional[CSharpInterfaceInfo]:
        """Parse an interface definition."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            name = match.group(3)
            gen_str = match.group(4) or ""
            extends_str = match.group(5) or ""

            modifiers = self._parse_modifiers(mod_str)
            extends = [e.strip() for e in extends_str.split(',') if e.strip()] if extends_str else []
            # Clean generic constraints from extends
            extends = [re.sub(r'\s+where\s+.*', '', e).strip() for e in extends]
            extends = [e for e in extends if e]

            body = self._extract_brace_body(content, match.start())
            methods = self._extract_interface_methods(body)
            properties = self._extract_properties(body)
            events = self._extract_event_names(body)

            line_number = content[:match.start()].count('\n') + 1

            return CSharpInterfaceInfo(
                name=name,
                methods=methods,
                properties=properties,
                events=events,
                extends=extends,
                attributes=self._parse_attributes(attr_str),
                generic_params=self._parse_generic_params(gen_str, constraints),
                file=file_path,
                line_number=line_number,
                is_exported=self._is_exported(modifiers),
                namespace=namespace,
            )
        except Exception:
            return None

    def _parse_struct(self, match, content: str, file_path: str, namespace: str,
                      constraints: Dict[str, List[str]]) -> Optional[CSharpStructInfo]:
        """Parse a struct definition."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            name = match.group(3)
            gen_str = match.group(4) or ""
            impl_str = match.group(5) or ""

            modifiers = self._parse_modifiers(mod_str)
            is_readonly = 'readonly' in modifiers
            is_ref = 'ref' in modifiers

            implements = [i.strip() for i in impl_str.split(',') if i.strip()] if impl_str else []
            implements = [re.sub(r'\s+where\s+.*', '', i).strip() for i in implements]
            implements = [i for i in implements if i]

            body = self._extract_brace_body(content, match.start())
            fields = self._extract_fields(body)
            properties = self._extract_properties(body)
            methods = self._extract_method_names(body)

            line_number = content[:match.start()].count('\n') + 1

            return CSharpStructInfo(
                name=name,
                fields=fields,
                properties=properties,
                methods=methods,
                implements=implements,
                attributes=self._parse_attributes(attr_str),
                generic_params=self._parse_generic_params(gen_str, constraints),
                file=file_path,
                line_number=line_number,
                is_exported=self._is_exported(modifiers),
                is_readonly=is_readonly,
                is_ref=is_ref,
                namespace=namespace,
                modifiers=modifiers,
            )
        except Exception:
            return None

    def _parse_record(self, match, content: str, file_path: str, namespace: str,
                      constraints: Dict[str, List[str]]) -> Optional[CSharpRecordInfo]:
        """Parse a record definition (C# 9+)."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            struct_or_class = match.group(3) or ""
            name = match.group(4)
            gen_str = match.group(5) or ""
            params_str = match.group(6) or ""
            base_str = match.group(7) or ""

            modifiers = self._parse_modifiers(mod_str)
            is_struct = struct_or_class == "struct"

            # Parse positional parameters
            parameters = []
            if params_str:
                for p in params_str.split(','):
                    p = p.strip()
                    if p:
                        parts = p.rsplit(' ', 1)
                        if len(parts) == 2:
                            parameters.append({"type": parts[0].strip(), "name": parts[1].strip()})

            # Parse base/implements
            base_record = None
            implements = []
            if base_str:
                parts = [p.strip() for p in base_str.split(',')]
                for i, part in enumerate(parts):
                    part = re.sub(r'\s+where\s+.*', '', part).strip()
                    if not part:
                        continue
                    if i == 0 and not part.startswith('I'):
                        base_record = part
                    else:
                        implements.append(part)

            line_number = content[:match.start()].count('\n') + 1

            return CSharpRecordInfo(
                name=name,
                parameters=parameters,
                base_record=base_record,
                implements=implements,
                attributes=self._parse_attributes(attr_str),
                generic_params=self._parse_generic_params(gen_str, constraints),
                file=file_path,
                line_number=line_number,
                is_exported=self._is_exported(modifiers),
                is_struct=is_struct,
                namespace=namespace,
            )
        except Exception:
            return None

    def _parse_delegate(self, match, file_path: str, namespace: str,
                        constraints: Dict[str, List[str]]) -> Optional[CSharpDelegateInfo]:
        """Parse a delegate definition."""
        try:
            attr_str = match.group(1) or ""
            mod_str = match.group(2) or ""
            return_type = match.group(3).strip()
            name = match.group(4)
            gen_str = match.group(5) or ""
            params_str = match.group(6) or ""

            modifiers = self._parse_modifiers(mod_str)
            parameters = []
            if params_str.strip():
                for p in params_str.split(','):
                    p = p.strip()
                    if p:
                        parts = p.rsplit(' ', 1)
                        if len(parts) == 2:
                            parameters.append({"type": parts[0].strip(), "name": parts[1].strip()})

            return CSharpDelegateInfo(
                name=name,
                return_type=return_type,
                parameters=parameters,
                generic_params=self._parse_generic_params(gen_str, constraints),
                attributes=self._parse_attributes(attr_str),
                file=file_path,
                is_exported=self._is_exported(modifiers),
                namespace=namespace,
            )
        except Exception:
            return None

    def _extract_fields(self, body: str) -> List[CSharpFieldInfo]:
        """Extract field declarations from type body."""
        fields = []
        for m in self.FIELD_PATTERN.finditer(body):
            attr_str = m.group(1) or ""
            mod_str = m.group(2) or ""
            type_str = m.group(3).strip()
            name = m.group(4)
            default = m.group(5)

            # Skip if it looks like a method or property
            if '(' in type_str or '{' in type_str:
                continue
            # Skip if type is a keyword that's not actually a type
            if type_str in ('return', 'throw', 'if', 'else', 'for', 'while', 'switch',
                           'case', 'break', 'continue', 'yield', 'class', 'struct', 'interface',
                           'namespace', 'using', 'var', 'get', 'set', 'add', 'remove'):
                continue

            modifiers = self._parse_modifiers(mod_str)
            fields.append(CSharpFieldInfo(
                name=name,
                type=type_str,
                modifiers=modifiers,
                attributes=self._parse_attributes(attr_str),
                default_value=default.strip() if default else None,
                is_static='static' in modifiers,
                is_readonly='readonly' in modifiers,
                is_const='const' in modifiers,
                is_required='required' in modifiers,
            ))
        return fields[:20]  # Limit to prevent noise

    def _extract_properties(self, body: str) -> List[CSharpPropertyInfo]:
        """Extract property declarations from type body."""
        properties = []
        prop_re = re.compile(
            r'((?:\[[\w.,\s()="\[\]]+\]\s*)*)'
            r'((?:public|private|protected|internal|static|virtual|override|abstract|sealed|new|required)\s+)*'
            r'([\w<>\[\]?,.\s]+?)\s+'
            r'(\w+)\s*\{',
            re.MULTILINE
        )
        for m in prop_re.finditer(body):
            attr_str = m.group(1) or ""
            mod_str = m.group(2) or ""
            type_str = m.group(3).strip()
            name = m.group(4)

            if type_str in ('return', 'class', 'struct', 'namespace', 'if', 'else',
                           'for', 'while', 'switch', 'using', 'var'):
                continue
            if name in ('get', 'set', 'add', 'remove', 'init'):
                continue

            # Look ahead for accessor keywords
            after = body[m.end():]
            accessor_body = ""
            brace_count = 1
            i = 0
            while i < len(after) and brace_count > 0:
                if after[i] == '{':
                    brace_count += 1
                elif after[i] == '}':
                    brace_count -= 1
                i += 1
            if i > 0:
                accessor_body = after[:i]

            has_getter = 'get' in accessor_body
            has_setter = 'set' in accessor_body
            has_init = 'init' in accessor_body
            modifiers = self._parse_modifiers(mod_str)

            properties.append(CSharpPropertyInfo(
                name=name,
                type=type_str,
                has_getter=has_getter,
                has_setter=has_setter,
                has_init=has_init,
                modifiers=modifiers,
                attributes=self._parse_attributes(attr_str),
                is_required='required' in modifiers,
            ))
        return properties[:20]

    def _extract_method_names(self, body: str) -> List[str]:
        """Extract method names from type body."""
        method_re = re.compile(
            r'(?:public|private|protected|internal|static|virtual|override|abstract|sealed|async|new|unsafe|extern)\s+'
            r'(?:(?:public|private|protected|internal|static|virtual|override|abstract|sealed|async|new|unsafe|extern)\s+)*'
            r'[\w<>\[\]?,.\s]+?\s+'
            r'(\w+)\s*\(',
            re.MULTILINE
        )
        names = []
        for m in method_re.finditer(body):
            name = m.group(1)
            if name not in ('if', 'while', 'for', 'switch', 'catch', 'using',
                           'lock', 'fixed', 'foreach', 'class', 'struct',
                           'interface', 'return', 'throw', 'new', 'get', 'set'):
                if name not in names:
                    names.append(name)
        return names

    def _extract_interface_methods(self, body: str) -> List[Dict[str, Any]]:
        """Extract method signatures from interface body."""
        methods = []
        method_re = re.compile(
            r'(?:([\w<>\[\]?,.\s]+?)\s+)?'   # Return type (optional for some patterns)
            r'(\w+)\s*'                        # Method name
            r'(?:<([^>]+)>)?\s*'               # Optional generics
            r'\(([^)]*)\)\s*'                  # Parameters
            r'(?:;|\{)',                        # End with ; or {
            re.MULTILINE
        )
        for m in method_re.finditer(body):
            return_type = m.group(1) or "void"
            name = m.group(2)
            if name in ('get', 'set', 'add', 'remove', 'init', 'if', 'while',
                        'for', 'switch', 'using', 'return', 'throw', 'new'):
                continue
            methods.append({
                "name": name,
                "return_type": return_type.strip(),
            })
        return methods

    def _extract_event_names(self, body: str) -> List[str]:
        """Extract event declarations from body."""
        event_re = re.compile(r'event\s+[\w<>\[\]?,.\s]+?\s+(\w+)\s*;', re.MULTILINE)
        return [m.group(1) for m in event_re.finditer(body)]
