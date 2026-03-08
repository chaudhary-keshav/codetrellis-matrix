"""
Django REST Framework Serializer Extractor for CodeTrellis.

Extracts DRF serializers including Serializer, ModelSerializer,
HyperlinkedModelSerializer, field definitions, and validators.
Supports DRF 3.x.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoSerializerFieldInfo:
    """Information about a DRF serializer field."""
    name: str
    field_type: str
    required: bool = True
    read_only: bool = False
    write_only: bool = False
    source: Optional[str] = None
    many: bool = False


@dataclass
class DjangoSerializerInfo:
    """Information about a DRF serializer."""
    name: str
    serializer_type: str  # serializer, model_serializer, hyperlinked, list_serializer
    file: str = ""
    base_classes: List[str] = field(default_factory=list)
    fields: List[DjangoSerializerFieldInfo] = field(default_factory=list)
    model: Optional[str] = None
    meta_fields: Optional[List[str]] = None
    meta_exclude: Optional[List[str]] = None
    meta_extra_kwargs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    meta_read_only_fields: List[str] = field(default_factory=list)
    meta_depth: Optional[int] = None
    validators: List[str] = field(default_factory=list)
    validate_methods: List[str] = field(default_factory=list)
    nested_serializers: List[str] = field(default_factory=list)
    line_number: int = 0


# Serializer field types
DRF_SERIALIZER_FIELD_TYPES = {
    'BooleanField', 'NullBooleanField', 'CharField', 'EmailField',
    'RegexField', 'SlugField', 'URLField', 'UUIDField',
    'FilePathField', 'IPAddressField',
    'IntegerField', 'FloatField', 'DecimalField',
    'DateTimeField', 'DateField', 'TimeField', 'DurationField',
    'ChoiceField', 'MultipleChoiceField',
    'FileField', 'ImageField',
    'ListField', 'DictField', 'HStoreField', 'JSONField',
    'ReadOnlyField', 'HiddenField', 'ModelField',
    'SerializerMethodField',
    # Relational fields
    'StringRelatedField', 'PrimaryKeyRelatedField',
    'HyperlinkedRelatedField', 'SlugRelatedField',
    'HyperlinkedIdentityField', 'ManyRelatedField',
}

DRF_SERIALIZER_BASES = {
    'Serializer', 'ModelSerializer', 'HyperlinkedModelSerializer',
    'ListSerializer', 'BaseSerializer',
    'serializers.Serializer', 'serializers.ModelSerializer',
    'serializers.HyperlinkedModelSerializer',
}


class DjangoSerializerExtractor:
    """
    Extracts DRF serializer definitions.

    Handles:
    - Serializer and ModelSerializer classes
    - Field declarations with all options
    - Meta class (model, fields, exclude, extra_kwargs, depth)
    - validate_* methods
    - Nested serializer detection
    - SerializerMethodField handlers
    """

    SERIALIZER_CLASS_PATTERN = re.compile(
        r'^class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    FIELD_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(?:serializers\.)?(\w+)\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    NESTED_SERIALIZER_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(\w+Serializer)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    VALIDATE_METHOD_PATTERN = re.compile(
        r'^\s{4}def\s+(validate(?:_\w+)?)\s*\(',
        re.MULTILINE
    )

    META_PATTERN = re.compile(
        r'^\s{4}class\s+Meta\s*.*?:\s*\n((?:\s{8}.*\n)*)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the DRF serializer extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract DRF serializer definitions.

        Returns:
            Dict with 'serializers'
        """
        serializers = []

        for match in self.SERIALIZER_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip() for b in bases_str.split(',')]

            # Check if this is a serializer
            serializer_type = self._classify_serializer(bases)
            if not serializer_type:
                continue

            class_body = self._extract_class_body(content, match.end())

            # Extract fields
            fields = self._extract_fields(class_body)

            # Extract nested serializers
            nested = []
            for nm in self.NESTED_SERIALIZER_PATTERN.finditer(class_body):
                nested.append(nm.group(2))

            # Extract validate methods
            validate_methods = self.VALIDATE_METHOD_PATTERN.findall(class_body)

            # Extract Meta class
            model = None
            meta_fields = None
            meta_exclude = None
            meta_read_only_fields = []
            meta_depth = None
            meta_extra_kwargs = {}

            meta_match = self.META_PATTERN.search(class_body)
            if meta_match:
                meta_body = meta_match.group(1)
                model = self._extract_meta_attr(meta_body, 'model')
                meta_fields = self._extract_meta_list(meta_body, 'fields')
                meta_exclude = self._extract_meta_list(meta_body, 'exclude')
                meta_read_only_fields = self._extract_meta_list(meta_body, 'read_only_fields') or []

                depth_match = re.search(r'depth\s*=\s*(\d+)', meta_body)
                if depth_match:
                    meta_depth = int(depth_match.group(1))

            # Extract class-level validators
            validators = []
            validator_match = re.search(r'^\s{4}validators\s*=\s*\[([^\]]+)\]', class_body, re.MULTILINE)
            if validator_match:
                validators = [v.strip() for v in validator_match.group(1).split(',') if v.strip()]

            serializer = DjangoSerializerInfo(
                name=class_name,
                serializer_type=serializer_type,
                file=file_path,
                base_classes=bases,
                fields=fields,
                model=model,
                meta_fields=meta_fields,
                meta_exclude=meta_exclude,
                meta_extra_kwargs=meta_extra_kwargs,
                meta_read_only_fields=meta_read_only_fields,
                meta_depth=meta_depth,
                validators=validators,
                validate_methods=validate_methods,
                nested_serializers=nested,
                line_number=content[:match.start()].count('\n') + 1,
            )
            serializers.append(serializer)

        return {'serializers': serializers}

    def _classify_serializer(self, bases: List[str]) -> Optional[str]:
        """Classify serializer type."""
        for base in bases:
            clean = base.strip().split('.')[-1]
            if 'HyperlinkedModelSerializer' in clean:
                return 'hyperlinked'
            if 'ModelSerializer' in clean:
                return 'model_serializer'
            if 'ListSerializer' in clean:
                return 'list_serializer'
            if 'Serializer' in clean:
                return 'serializer'
        return None

    def _extract_fields(self, class_body: str) -> List[DjangoSerializerFieldInfo]:
        """Extract serializer field declarations."""
        fields = []
        for match in self.FIELD_PATTERN.finditer(class_body):
            name = match.group(1)
            field_type = match.group(2)
            kwargs_str = match.group(3)

            # Skip if not a recognized field type
            if field_type not in DRF_SERIALIZER_FIELD_TYPES and not field_type.endswith('Field'):
                continue

            required = 'required=False' not in kwargs_str
            read_only = 'read_only=True' in kwargs_str
            write_only = 'write_only=True' in kwargs_str
            many = 'many=True' in kwargs_str

            source = None
            source_match = re.search(r"source\s*=\s*['\"]([^'\"]+)['\"]", kwargs_str)
            if source_match:
                source = source_match.group(1)

            fields.append(DjangoSerializerFieldInfo(
                name=name,
                field_type=field_type,
                required=required,
                read_only=read_only,
                write_only=write_only,
                source=source,
                many=many,
            ))

        return fields

    def _extract_meta_attr(self, meta_body: str, attr: str) -> Optional[str]:
        """Extract a simple attribute from Meta class."""
        match = re.search(rf'{attr}\s*=\s*(\w+)', meta_body)
        return match.group(1) if match else None

    def _extract_meta_list(self, meta_body: str, attr: str) -> Optional[List[str]]:
        """Extract a list attribute from Meta class."""
        if re.search(rf"{attr}\s*=\s*['\"]__all__['\"]", meta_body):
            return ['__all__']

        match = re.search(rf'{attr}\s*=\s*[\[\(]([^\]\)]+)[\]\)]', meta_body)
        if not match:
            return None

        items = re.findall(r"['\"](\w+)['\"]", match.group(1))
        return items if items else None

    def _extract_class_body(self, content: str, class_end: int) -> str:
        """Extract class body using indentation."""
        lines = content.split('\n')
        start_line = content[:class_end].count('\n')
        body_lines = []

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent < 4 and line.strip():
                break
            body_lines.append(line)

        return '\n'.join(body_lines)
