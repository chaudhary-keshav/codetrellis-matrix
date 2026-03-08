"""
CSharpAttributeExtractor - Extracts and categorizes C# attribute usage.

Extracts:
- Dependency Injection attributes ([Inject], [FromServices], service registrations)
- Validation attributes ([Required], [Range], [RegularExpression], custom validators)
- Authorization attributes ([Authorize], [AllowAnonymous], policy-based)
- Serialization attributes ([JsonProperty], [JsonIgnore], [XmlElement])
- Entity Framework attributes ([Table], [Column], [Key], [ForeignKey], etc.)
- Testing attributes ([Fact], [Theory], [Test], [TestMethod])
- Middleware / Filter attributes ([ServiceFilter], [TypeFilter], [ActionFilter])
- Custom attributes (user-defined attribute classes)
- Obsolete / Deprecated markers
- Assembly-level attributes

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set


@dataclass
class CSharpAttributeInfo:
    """Information about a C# attribute usage."""
    name: str
    target: str = ""       # Class, method, property, parameter name it decorates
    target_kind: str = ""  # class, method, property, parameter, assembly
    category: str = ""     # di, validation, auth, serialization, ef, testing, filter, custom
    arguments: str = ""    # Raw argument text
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpCustomAttributeInfo:
    """Information about a user-defined attribute class."""
    name: str
    base_class: str = "Attribute"
    attribute_usage: str = ""    # [AttributeUsage(AttributeTargets.Class)]
    properties: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class CSharpAttributeExtractor:
    """
    Extracts and categorizes C# attribute usage from source code.

    Categories:
    - di: Dependency injection ([Inject], [FromServices], [Service], etc.)
    - validation: Data validation ([Required], [Range], [StringLength], etc.)
    - auth: Authorization ([Authorize], [AllowAnonymous], [Roles], etc.)
    - serialization: JSON/XML serialization ([JsonProperty], [XmlElement], etc.)
    - ef: Entity Framework ([Table], [Column], [Key], [Index], etc.)
    - testing: Test framework ([Fact], [Theory], [Test], [TestMethod], etc.)
    - filter: MVC filters ([ServiceFilter], [TypeFilter], etc.)
    - routing: Routing ([Route], [HttpGet], [ApiController], etc.)
    - swagger: API documentation ([SwaggerOperation], [ProducesResponseType], etc.)
    - custom: User-defined attributes
    - other: Unrecognized/uncategorized
    """

    # ─── Category Definitions ──────────────────────────────────────

    CATEGORY_MAP: Dict[str, Set[str]] = {
        "di": {
            "Inject", "FromServices", "FromKeyedServices", "Service",
            "Singleton", "Scoped", "Transient", "ActivatorUtilitiesConstructor",
        },
        "validation": {
            "Required", "Range", "StringLength", "MaxLength", "MinLength",
            "RegularExpression", "Compare", "EmailAddress", "Phone", "Url",
            "CreditCard", "DataType", "CustomValidation", "FileExtensions",
        },
        "auth": {
            "Authorize", "AllowAnonymous", "Roles", "RequiresClaim",
        },
        "serialization": {
            "JsonProperty", "JsonPropertyName", "JsonIgnore", "JsonConverter",
            "JsonInclude", "JsonRequired", "JsonExtensionData", "JsonDerivedType",
            "JsonPolymorphic", "JsonConstructor", "JsonSerializable",
            "XmlRoot", "XmlElement", "XmlAttribute", "XmlIgnore", "XmlArray",
            "DataContract", "DataMember", "IgnoreDataMember",
            "ProtoContract", "ProtoMember",  # Protobuf
            "MessagePackObject", "Key",  # MessagePack
        },
        "ef": {
            "Table", "Column", "Key", "ForeignKey", "InverseProperty",
            "NotMapped", "DatabaseGenerated", "ConcurrencyCheck", "Timestamp",
            "MaxLength", "Index", "Owned", "Keyless", "Comment",
            "Precision", "Unicode", "DeleteBehavior", "BackingField",
        },
        "testing": {
            "Fact", "Theory", "InlineData", "ClassData", "MemberData",
            "Test", "TestMethod", "TestClass", "TestInitialize", "TestCleanup",
            "SetUp", "TearDown", "TestFixture", "TestCase",
            "Category", "Ignore", "Explicit", "Trait",
        },
        "filter": {
            "ServiceFilter", "TypeFilter", "ActionFilter",
            "ExceptionFilter", "ResultFilter", "ResourceFilter",
            "Middleware",
        },
        "routing": {
            "Route", "HttpGet", "HttpPost", "HttpPut", "HttpDelete", "HttpPatch",
            "HttpHead", "HttpOptions", "ApiController", "NonAction", "Area",
            "ApiVersion", "MapToApiVersion",
            "Consumes", "Produces", "ProducesResponseType",
            "ApiExplorerSettings",
        },
        "swagger": {
            "SwaggerOperation", "SwaggerResponse", "SwaggerSchema",
            "OpenApiOperation", "OpenApiResponse",
        },
        "lifecycle": {
            "Obsolete", "Deprecated",
            "SuppressMessage", "ExcludeFromCodeCoverage",
            "DebuggerDisplay", "DebuggerStepThrough", "DebuggerHidden",
            "Conditional",
        },
        "configuration": {
            "Options", "Configure", "ConfigurationSection",
        },
    }

    # Build reverse lookup
    _ATTR_TO_CATEGORY: Dict[str, str] = {}
    for cat, attrs in CATEGORY_MAP.items():
        for attr in attrs:
            _ATTR_TO_CATEGORY[attr] = cat

    # ─── Patterns ──────────────────────────────────────────────────

    # General attribute pattern: [AttributeName] or [AttributeName(args)]
    ATTRIBUTE_PATTERN = re.compile(
        r'\[(?:assembly:\s*)?'
        r'(\w+(?:\.\w+)?)'                    # Attribute name (possibly with namespace)
        r'(?:Attribute)?'                      # Optional "Attribute" suffix
        r'(?:\s*\(([^)\]]*(?:\([^)]*\))*[^)\]]*)\))?'  # Optional arguments (handles nested parens)
        r'\s*\]',
        re.MULTILINE
    )

    # What follows an attribute - to determine the target
    TARGET_AFTER_ATTR = re.compile(
        r'\s*(?:\[.*?\]\s*)*'                  # Possibly more attributes
        r'(?:'
        r'(?:public|private|protected|internal|static|abstract|sealed|virtual|override|async|readonly|partial|required|new)\s+)*'
        r'(?:'
        r'(?:class|struct|record|interface|enum|delegate)\s+(\w+)'  # Type declaration
        r'|'
        r'([\w<>\[\]?,.\s]+?)\s+(\w+)\s*[\({;=]'  # Member/property/field
        r')',
        re.MULTILINE | re.DOTALL
    )

    # Custom attribute class definition
    CUSTOM_ATTR_PATTERN = re.compile(
        r'(?:\[AttributeUsage\s*\(([^)]+)\)\]\s*)?'
        r'(?:public|internal)\s+(?:sealed\s+)?class\s+(\w+Attribute)\s*:\s*'
        r'((?:\w+\.)*Attribute)\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Assembly-level attribute
    ASSEMBLY_ATTR_PATTERN = re.compile(
        r'\[assembly:\s*(\w+)(?:\s*\(([^)]*)\))?\s*\]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attribute usage from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: attributes, custom_attributes, attribute_summary
        """
        result = {
            "attributes": [],
            "custom_attributes": [],
            "attribute_summary": {},
        }

        result["attributes"] = self._extract_attributes(content, file_path)
        result["custom_attributes"] = self._extract_custom_attributes(content, file_path)
        result["attribute_summary"] = self._build_summary(result["attributes"])

        return result

    def _extract_attributes(self, content: str, file_path: str) -> List[CSharpAttributeInfo]:
        """Extract all attribute usages."""
        attributes = []

        for match in self.ATTRIBUTE_PATTERN.finditer(content):
            raw_name = match.group(1)
            arguments = match.group(2) or ""

            # Strip namespace prefix
            name = raw_name.split('.')[-1]
            # Strip "Attribute" suffix if present
            if name.endswith("Attribute") and name != "Attribute":
                name = name[:-len("Attribute")]

            # Categorize
            category = self._ATTR_TO_CATEGORY.get(name, "custom")

            # Determine target
            target = ""
            target_kind = ""

            # Check if assembly-level
            before = content[max(0, match.start()-15):match.start()]
            if "assembly:" in content[match.start():match.end()]:
                target_kind = "assembly"
            else:
                # Look at what follows
                after = content[match.end():]
                target_match = self.TARGET_AFTER_ATTR.match(after)
                if target_match:
                    type_name = target_match.group(1)
                    member_type = target_match.group(2)
                    member_name = target_match.group(3)

                    if type_name:
                        target = type_name
                        # Determine kind from keyword before name
                        type_section = after[:target_match.end()]
                        if 'class ' in type_section:
                            target_kind = "class"
                        elif 'struct ' in type_section:
                            target_kind = "struct"
                        elif 'record ' in type_section:
                            target_kind = "record"
                        elif 'interface ' in type_section:
                            target_kind = "interface"
                        elif 'enum ' in type_section:
                            target_kind = "enum"
                        elif 'delegate ' in type_section:
                            target_kind = "delegate"
                        else:
                            target_kind = "type"
                    elif member_name:
                        target = member_name
                        if member_type and '(' in after[:target_match.end()]:
                            target_kind = "method"
                        else:
                            target_kind = "property"

            line_number = content[:match.start()].count('\n') + 1

            attributes.append(CSharpAttributeInfo(
                name=name,
                target=target,
                target_kind=target_kind,
                category=category,
                arguments=arguments.strip()[:200],  # Truncate long args
                file=file_path,
                line_number=line_number,
            ))

        return attributes

    def _extract_custom_attributes(self, content: str, file_path: str) -> List[CSharpCustomAttributeInfo]:
        """Extract custom attribute class definitions."""
        custom_attrs = []
        for match in self.CUSTOM_ATTR_PATTERN.finditer(content):
            usage = match.group(1) or ""
            name = match.group(2)
            base = match.group(3)

            # Extract properties
            body_start = match.end()
            body_end = self._find_brace_end(content, body_start - 1)
            if body_end < 0:
                body_end = min(body_start + 1000, len(content))
            body = content[body_start:body_end]

            props = []
            prop_re = re.compile(r'public\s+([\w<>?]+)\s+(\w+)\s*\{', re.MULTILINE)
            for p in prop_re.finditer(body):
                props.append(f"{p.group(1)} {p.group(2)}")

            line_number = content[:match.start()].count('\n') + 1
            custom_attrs.append(CSharpCustomAttributeInfo(
                name=name,
                base_class=base,
                attribute_usage=usage.strip(),
                properties=props[:10],
                file=file_path,
                line_number=line_number,
            ))

        return custom_attrs

    def _build_summary(self, attributes: List[CSharpAttributeInfo]) -> Dict[str, int]:
        """Build a summary count of attributes by category."""
        summary: Dict[str, int] = {}
        for attr in attributes:
            cat = attr.category
            summary[cat] = summary.get(cat, 0) + 1
        return summary

    def _find_brace_end(self, content: str, start: int) -> int:
        """Find matching closing brace from start position."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1
