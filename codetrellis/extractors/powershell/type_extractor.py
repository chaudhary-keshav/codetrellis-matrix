"""
PowerShell Type Extractor for CodeTrellis

Extracts type definitions from PowerShell source code:
- Classes (PowerShell 5.0+)
- Enums (PowerShell 5.0+)
- Interfaces (via .NET interop)
- DSC Resources (class-based and MOF-based)
- Custom type definitions (Add-Type)

Supports PowerShell 1.0 through 7.4+ (PowerShell Core / pwsh).
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PSPropertyInfo:
    """Information about a PowerShell class/DSC property."""
    name: str
    type: str = ""
    default_value: Optional[str] = None
    is_mandatory: bool = False
    is_key: bool = False
    validate_set: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PSClassInfo:
    """Information about a PowerShell class definition."""
    name: str
    file: str = ""
    line_number: int = 0
    base_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    properties: List[PSPropertyInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    constructors: List[str] = field(default_factory=list)
    is_dsc_resource: bool = False
    is_abstract: bool = False
    attributes: List[str] = field(default_factory=list)


@dataclass
class PSEnumInfo:
    """Information about a PowerShell enum definition."""
    name: str
    file: str = ""
    line_number: int = 0
    values: List[str] = field(default_factory=list)
    is_flags: bool = False
    underlying_type: Optional[str] = None


@dataclass
class PSInterfaceInfo:
    """Information about a .NET interface used via Add-Type."""
    name: str
    file: str = ""
    line_number: int = 0
    members: List[str] = field(default_factory=list)
    language: str = "CSharp"


@dataclass
class PSDSCResourceInfo:
    """Information about a DSC resource definition."""
    name: str
    file: str = ""
    line_number: int = 0
    resource_type: str = ""  # 'class', 'mof', 'composite'
    properties: List[PSPropertyInfo] = field(default_factory=list)
    key_properties: List[str] = field(default_factory=list)
    module_name: Optional[str] = None


class PowerShellTypeExtractor:
    """
    Extracts type definitions from PowerShell source code.

    Detects:
    - class definitions (PS 5.0+)
    - enum definitions (PS 5.0+)
    - DSC resource classes ([DscResource()])
    - Add-Type inline C#/VB.NET types
    - Custom type accelerators
    """

    # PowerShell class definition
    CLASS_PATTERN = re.compile(
        r'^\s*(?:(?:\[(\w+(?:\([^)]*\))?)\]\s*)*)?'
        r'class\s+(\w+)'
        r'(?:\s*:\s*([\w.,\s\[\]]+))?'
        r'\s*\{',
        re.MULTILINE
    )

    # Enum definition
    ENUM_PATTERN = re.compile(
        r'^\s*(?:\[Flags\(\)\]\s*)?enum\s+(\w+)'
        r'(?:\s*:\s*(\w+))?'
        r'\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Flags attribute for enums
    FLAGS_PATTERN = re.compile(r'\[Flags\(\)\]', re.IGNORECASE)

    # Class property
    PROPERTY_PATTERN = re.compile(
        r'^\s*(?:(\[[\w\(\),\s="\']+\])\s*)*'
        r'(?:(hidden|static)\s+)?'
        r'\[(\w+(?:\[\])?)\]\s*'
        r'\$(\w+)'
        r'(?:\s*=\s*(.+?))?'
        r'\s*$',
        re.MULTILINE
    )

    # Class method
    METHOD_PATTERN = re.compile(
        r'^\s*(?:(hidden|static)\s+)?'
        r'(?:\[(\w+(?:\[\])?)\]\s+)?'
        r'(\w+)\s*\(([^)]*)\)\s*\{',
        re.MULTILINE
    )

    # DSC Resource attribute
    DSC_RESOURCE_ATTR = re.compile(r'\[DscResource\(\)\]', re.IGNORECASE)

    # DSC Key property
    DSC_KEY_ATTR = re.compile(r'\[DscProperty\s*\(\s*Key\s*\)\]', re.IGNORECASE)

    # Add-Type with inline code
    ADD_TYPE_PATTERN = re.compile(
        r"Add-Type\s+(?:-TypeDefinition\s+)?@['\"](.+?)@['\"]",
        re.DOTALL | re.IGNORECASE
    )

    # Add-Type with -MemberDefinition
    ADD_TYPE_MEMBER_PATTERN = re.compile(
        r"Add-Type\s+-Name\s+['\"]?(\w+)['\"]?\s.*?-MemberDefinition\s+@['\"](.+?)@['\"]",
        re.DOTALL | re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all type definitions from PowerShell source code.

        Returns dict with keys: classes, enums, interfaces, dsc_resources
        """
        classes = self._extract_classes(content, file_path)
        enums = self._extract_enums(content, file_path)
        interfaces = self._extract_interfaces(content, file_path)
        dsc_resources = self._extract_dsc_resources(content, file_path, classes)

        return {
            'classes': classes,
            'enums': enums,
            'interfaces': interfaces,
            'dsc_resources': dsc_resources,
        }

    def _extract_classes(self, content: str, file_path: str) -> List[PSClassInfo]:
        """Extract PowerShell class definitions."""
        classes = []
        lines = content.split('\n')

        for match in self.CLASS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            attrs_str = match.group(1) or ""
            name = match.group(2)
            inheritance = match.group(3)

            # Parse base class and interfaces
            base_class = None
            ifaces = []
            if inheritance:
                parts = [p.strip() for p in inheritance.split(',')]
                if parts:
                    base_class = parts[0]
                    ifaces = parts[1:]

            # Check for DSC Resource attribute
            is_dsc = False
            # Check inline attrs captured by the regex
            if attrs_str and re.search(r'DscResource', attrs_str, re.IGNORECASE):
                is_dsc = True
            # Also look above the class definition for attributes on prior lines
            if not is_dsc:
                pre_lines = content[:match.start()].split('\n')
                attr_window = '\n'.join(pre_lines[-5:]) if len(pre_lines) >= 5 else '\n'.join(pre_lines)
                if self.DSC_RESOURCE_ATTR.search(attr_window):
                    is_dsc = True

            # Extract class body
            class_body = self._extract_brace_block(content, match.end() - 1)

            # Parse properties and methods from body
            properties = []
            methods = []
            constructors = []

            if class_body:
                # Extract properties
                for prop_match in self.PROPERTY_PATTERN.finditer(class_body):
                    prop_attrs_str = prop_match.group(1) or ""
                    prop_modifier = prop_match.group(2) or ""
                    prop_type = prop_match.group(3)
                    prop_name = prop_match.group(4)
                    prop_default = prop_match.group(5)

                    prop_attrs = []
                    is_key = False
                    is_mandatory = False
                    validate_set = []

                    if prop_attrs_str:
                        prop_attrs = re.findall(r'\[(\w+(?:\([^)]*\))?)\]', prop_attrs_str)
                        if any('Key' in a for a in prop_attrs):
                            is_key = True
                        if any('Mandatory' in a for a in prop_attrs):
                            is_mandatory = True
                        vs_match = re.search(r'ValidateSet\(([^)]+)\)', prop_attrs_str)
                        if vs_match:
                            validate_set = [v.strip().strip("'\"") for v in vs_match.group(1).split(',')]

                    if prop_modifier:
                        prop_attrs.append(prop_modifier)

                    properties.append(PSPropertyInfo(
                        name=prop_name,
                        type=prop_type,
                        default_value=prop_default.strip() if prop_default else None,
                        is_mandatory=is_mandatory,
                        is_key=is_key,
                        validate_set=validate_set,
                        attributes=prop_attrs,
                        line_number=line_num,
                    ))

                # Extract methods
                for meth_match in self.METHOD_PATTERN.finditer(class_body):
                    modifier = meth_match.group(1) or ""
                    return_type = meth_match.group(2) or "void"
                    meth_name = meth_match.group(3)
                    params = meth_match.group(4).strip()

                    if meth_name == name:
                        # Constructor
                        constructors.append(f"{name}({params})")
                    else:
                        prefix = f"[{modifier}] " if modifier else ""
                        methods.append(f"{prefix}[{return_type}] {meth_name}({params})")

            # Collect class-level attributes
            class_attrs = []
            if attrs_str:
                class_attrs = re.findall(r'\w+(?:\([^)]*\))?', attrs_str)

            classes.append(PSClassInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                base_class=base_class,
                interfaces=ifaces,
                properties=properties,
                methods=methods,
                constructors=constructors,
                is_dsc_resource=is_dsc,
                attributes=class_attrs,
            ))

        return classes

    def _extract_enums(self, content: str, file_path: str) -> List[PSEnumInfo]:
        """Extract PowerShell enum definitions."""
        enums = []

        for match in self.ENUM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1)
            underlying = match.group(2)
            body = match.group(3)

            # Check for [Flags()]
            matched_text = match.group()
            is_flags = bool(self.FLAGS_PATTERN.search(matched_text))
            if not is_flags:
                pre_text = content[:match.start()]
                pre_lines = pre_text.split('\n')
                attr_window = '\n'.join(pre_lines[-3:])
                is_flags = bool(self.FLAGS_PATTERN.search(attr_window))

            # Parse values
            values = []
            for line in body.split('\n'):
                line = line.strip().rstrip(',')
                if line and not line.startswith('#'):
                    # Remove assignment (e.g., Value = 1)
                    val_name = line.split('=')[0].strip()
                    if val_name:
                        values.append(val_name)

            enums.append(PSEnumInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                values=values,
                is_flags=is_flags,
                underlying_type=underlying,
            ))

        return enums

    def _extract_interfaces(self, content: str, file_path: str) -> List[PSInterfaceInfo]:
        """Extract .NET interfaces defined via Add-Type."""
        interfaces = []

        # Look for Add-Type with interface definitions
        for match in self.ADD_TYPE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            type_def = match.group(1)

            # Find interface definitions in C# code
            iface_pattern = re.compile(r'(?:public\s+)?interface\s+(\w+)\s*\{([^}]*)\}', re.DOTALL)
            for iface_match in iface_pattern.finditer(type_def):
                iface_name = iface_match.group(1)
                iface_body = iface_match.group(2)
                members = [m.strip().rstrip(';') for m in iface_body.split('\n') if m.strip() and not m.strip().startswith('//')]

                interfaces.append(PSInterfaceInfo(
                    name=iface_name,
                    file=file_path,
                    line_number=line_num,
                    members=members,
                    language="CSharp",
                ))

        return interfaces

    def _extract_dsc_resources(self, content: str, file_path: str,
                                classes: List[PSClassInfo]) -> List[PSDSCResourceInfo]:
        """Extract DSC resource definitions."""
        dsc_resources = []

        # Class-based DSC resources
        for cls in classes:
            if cls.is_dsc_resource:
                key_props = [p.name for p in cls.properties if p.is_key]
                dsc_resources.append(PSDSCResourceInfo(
                    name=cls.name,
                    file=file_path,
                    line_number=cls.line_number,
                    resource_type='class',
                    properties=cls.properties,
                    key_properties=key_props,
                ))

        # MOF-based DSC resources (Configuration keyword)
        config_pattern = re.compile(
            r'^\s*Configuration\s+(\w+)\s*\{',
            re.MULTILINE | re.IGNORECASE
        )
        for match in config_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1)

            # Look for resource usage within configuration
            config_body = self._extract_brace_block(content, match.end() - 1)
            if config_body:
                resource_usage = re.findall(r'(\w+)\s+["\']?\w+["\']?\s*\{', config_body)
                props = []
                for res in resource_usage:
                    if res not in ('Node', 'if', 'else', 'foreach', 'switch'):
                        props.append(PSPropertyInfo(
                            name=res,
                            type='DSCResource',
                        ))

        return dsc_resources

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within balanced braces starting at start_pos."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        depth = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            i += 1

        return content[start_pos + 1:]  # Unclosed brace — return what we have
