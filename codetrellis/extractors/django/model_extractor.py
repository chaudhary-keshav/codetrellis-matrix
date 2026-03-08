"""
Django Model Extractor for CodeTrellis.

Extracts Django model definitions including fields, relationships,
Meta options, managers, querysets, abstract models, proxy models.

Supports Django 1.x - 5.x.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoFieldInfo:
    """Information about a Django model field."""
    name: str
    field_type: str  # CharField, IntegerField, ForeignKey, etc.
    max_length: Optional[int] = None
    null: bool = False
    blank: bool = False
    unique: bool = False
    primary_key: bool = False
    default: Optional[str] = None
    choices: Optional[str] = None
    db_index: bool = False
    help_text: Optional[str] = None
    validators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class DjangoRelationshipInfo:
    """Information about a Django model relationship."""
    name: str
    relationship_type: str  # ForeignKey, OneToOneField, ManyToManyField, GenericForeignKey
    related_model: str
    on_delete: str = ""
    related_name: Optional[str] = None
    through: Optional[str] = None
    line_number: int = 0


@dataclass
class DjangoMetaInfo:
    """Information about Django model Meta class."""
    ordering: List[str] = field(default_factory=list)
    verbose_name: Optional[str] = None
    verbose_name_plural: Optional[str] = None
    db_table: Optional[str] = None
    unique_together: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    abstract: bool = False
    proxy: bool = False
    managed: bool = True
    permissions: List[str] = field(default_factory=list)
    default_related_name: Optional[str] = None
    app_label: Optional[str] = None


@dataclass
class DjangoManagerInfo:
    """Information about a Django model manager."""
    name: str
    manager_class: str
    is_custom: bool = False
    methods: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class DjangoModelInfo:
    """Complete information about a Django model."""
    name: str
    file: str = ""
    bases: List[str] = field(default_factory=list)
    fields: List[DjangoFieldInfo] = field(default_factory=list)
    relationships: List[DjangoRelationshipInfo] = field(default_factory=list)
    meta: Optional[DjangoMetaInfo] = None
    managers: List[DjangoManagerInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_proxy: bool = False
    has_str: bool = False
    has_save: bool = False
    has_clean: bool = False
    docstring: Optional[str] = None
    line_number: int = 0


# Django field types
DJANGO_FIELD_TYPES = {
    # Basic fields
    'AutoField', 'BigAutoField', 'SmallAutoField',
    'BooleanField', 'NullBooleanField',
    'CharField', 'TextField', 'SlugField', 'EmailField', 'URLField',
    'IntegerField', 'SmallIntegerField', 'BigIntegerField', 'PositiveIntegerField',
    'PositiveSmallIntegerField', 'PositiveBigIntegerField',
    'FloatField', 'DecimalField',
    'DateField', 'DateTimeField', 'TimeField', 'DurationField',
    'BinaryField', 'FileField', 'ImageField', 'FilePathField',
    'UUIDField', 'IPAddressField', 'GenericIPAddressField',
    'JSONField',
    # Relationship fields
    'ForeignKey', 'OneToOneField', 'ManyToManyField',
    'GenericForeignKey', 'GenericRelation',
}

RELATIONSHIP_FIELDS = {'ForeignKey', 'OneToOneField', 'ManyToManyField', 'GenericForeignKey', 'GenericRelation'}


class DjangoModelExtractor:
    """
    Extracts Django model definitions from Python source code.
    
    Handles:
    - Model class definitions (models.Model, AbstractUser, etc.)
    - Field definitions (CharField, IntegerField, ForeignKey, etc.)
    - Relationships (ForeignKey, OneToOneField, ManyToManyField)
    - Meta inner class (ordering, db_table, constraints, indexes)
    - Custom managers
    - Model methods (__str__, save, clean, get_absolute_url)
    - Abstract and proxy models
    - Django 1.x - 5.x field types
    """

    # Model class pattern: class Name(models.Model) or class Name(BaseModel)
    MODEL_CLASS_PATTERN = re.compile(
        r'^class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    # Field definition pattern
    FIELD_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(?:models\.)?(\w+(?:Field|Key|Relation))\s*\(([^)]*(?:\([^)]*\)[^)]*)*)\)',
        re.MULTILINE
    )

    # Manager pattern
    MANAGER_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(?:models\.)?(\w*Manager)\s*\(',
        re.MULTILINE
    )

    # Meta class pattern
    META_PATTERN = re.compile(
        r'^\s{4}class\s+Meta\s*(?:\([^)]*\))?\s*:\s*\n((?:\s{8}[^\n]+\n)*)',
        re.MULTILINE
    )

    # Method definition pattern inside class
    METHOD_PATTERN = re.compile(
        r'^\s{4}def\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Property pattern
    PROPERTY_PATTERN = re.compile(
        r'^\s{4}@property\s*\n\s{4}def\s+(\w+)',
        re.MULTILINE
    )

    # Django model base classes
    DJANGO_MODEL_BASES = {
        'models.Model', 'Model',
        'AbstractUser', 'AbstractBaseUser', 'PermissionsMixin',
        'TimeStampedModel', 'SoftDeletableModel',
        'MPTTModel', 'PolymorphicModel',
    }

    def __init__(self):
        """Initialize the Django model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> List[DjangoModelInfo]:
        """
        Extract all Django models from Python content.

        Args:
            content: Python source code
            file_path: Path to the source file

        Returns:
            List of DjangoModelInfo objects
        """
        models = []
        lines = content.split('\n')

        for match in self.MODEL_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip() for b in bases_str.split(',')]

            # Check if this is a Django model
            if not self._is_django_model(bases, content):
                continue

            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body = self._extract_class_body(content, match.end(), lines)

            # Extract fields
            fields = self._extract_fields(class_body)

            # Extract relationships
            relationships = self._extract_relationships(class_body)

            # Extract Meta
            meta = self._extract_meta(class_body)

            # Extract managers
            managers = self._extract_managers(class_body)

            # Extract methods
            methods = [m.group(1) for m in self.METHOD_PATTERN.finditer(class_body)]

            # Extract properties
            properties = [m.group(1) for m in self.PROPERTY_PATTERN.finditer(class_body)]

            # Determine model type
            is_abstract = meta.abstract if meta else any('Abstract' in b for b in bases)
            is_proxy = meta.proxy if meta else False

            # Extract docstring
            docstring = self._extract_docstring(class_body)

            model = DjangoModelInfo(
                name=class_name,
                file=file_path,
                bases=bases,
                fields=fields,
                relationships=relationships,
                meta=meta,
                managers=managers,
                methods=methods,
                properties=properties,
                is_abstract=is_abstract,
                is_proxy=is_proxy,
                has_str='__str__' in methods,
                has_save='save' in methods,
                has_clean='clean' in methods,
                docstring=docstring,
                line_number=line_number,
            )
            models.append(model)

        return models

    def _is_django_model(self, bases: List[str], content: str) -> bool:
        """Check if class bases indicate a Django model."""
        for base in bases:
            base = base.strip()
            if base in self.DJANGO_MODEL_BASES:
                return True
            if 'models.Model' in base or 'Model' in base:
                return True
            # Check if any base class ends with 'Model' and content imports django
            if base.endswith('Model') and ('from django' in content or 'import django' in content):
                return True
        # Check for django.db.models import
        if 'from django.db import models' in content or 'from django.db.models import' in content:
            for base in bases:
                if 'Model' in base:
                    return True
        return False

    def _extract_class_body(self, content: str, class_end: int, lines: List[str]) -> str:
        """Extract the body of a class definition using indentation."""
        start_line = content[:class_end].count('\n')
        body_lines = []
        base_indent = None

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                body_lines.append(line)
                continue

            indent = len(line) - len(line.lstrip())
            if base_indent is None:
                base_indent = indent

            if indent < base_indent and line.strip():
                # Check if this is a new top-level definition
                if line.strip().startswith(('class ', 'def ', '@')):
                    break
                # Or if it's at module level
                if indent == 0:
                    break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _extract_fields(self, class_body: str) -> List[DjangoFieldInfo]:
        """Extract field definitions from class body."""
        fields = []

        for match in self.FIELD_PATTERN.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2)
            field_args = match.group(3)

            if field_type in RELATIONSHIP_FIELDS:
                continue  # Handle separately in _extract_relationships

            if field_type not in DJANGO_FIELD_TYPES and not field_type.endswith('Field'):
                continue

            fi = DjangoFieldInfo(
                name=field_name,
                field_type=field_type,
                max_length=self._extract_int_arg(field_args, 'max_length'),
                null='null=True' in field_args or 'null = True' in field_args,
                blank='blank=True' in field_args or 'blank = True' in field_args,
                unique='unique=True' in field_args or 'unique = True' in field_args,
                primary_key='primary_key=True' in field_args or 'primary_key = True' in field_args,
                default=self._extract_str_arg(field_args, 'default'),
                choices=self._extract_str_arg(field_args, 'choices'),
                db_index='db_index=True' in field_args or 'db_index = True' in field_args,
                help_text=self._extract_str_arg(field_args, 'help_text'),
                line_number=class_body[:match.start()].count('\n') + 1,
            )
            fields.append(fi)

        return fields

    def _extract_relationships(self, class_body: str) -> List[DjangoRelationshipInfo]:
        """Extract relationship fields from class body."""
        relationships = []

        for match in self.FIELD_PATTERN.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2)
            field_args = match.group(3)

            if field_type not in RELATIONSHIP_FIELDS:
                continue

            # Extract related model (first positional arg)
            related_model = self._extract_first_arg(field_args)

            # Extract on_delete
            on_delete_match = re.search(r'on_delete\s*=\s*(?:models\.)?(\w+)', field_args)
            on_delete = on_delete_match.group(1) if on_delete_match else ""

            # Extract related_name
            related_name = self._extract_str_arg(field_args, 'related_name')

            # Extract through
            through = self._extract_str_arg(field_args, 'through')

            rel = DjangoRelationshipInfo(
                name=field_name,
                relationship_type=field_type,
                related_model=related_model,
                on_delete=on_delete,
                related_name=related_name,
                through=through,
                line_number=class_body[:match.start()].count('\n') + 1,
            )
            relationships.append(rel)

        return relationships

    def _extract_meta(self, class_body: str) -> Optional[DjangoMetaInfo]:
        """Extract Meta inner class options."""
        meta_match = self.META_PATTERN.search(class_body)
        if not meta_match:
            return None

        meta_body = meta_match.group(1)
        meta = DjangoMetaInfo()

        # ordering
        ordering_match = re.search(r"ordering\s*=\s*\[([^\]]*)\]", meta_body)
        if ordering_match:
            meta.ordering = re.findall(r"['\"]([^'\"]+)['\"]", ordering_match.group(1))

        # verbose_name
        vn_match = re.search(r"verbose_name\s*=\s*['\"]([^'\"]+)['\"]", meta_body)
        if vn_match:
            meta.verbose_name = vn_match.group(1)

        # db_table
        db_match = re.search(r"db_table\s*=\s*['\"]([^'\"]+)['\"]", meta_body)
        if db_match:
            meta.db_table = db_match.group(1)

        # abstract
        if 'abstract = True' in meta_body or 'abstract=True' in meta_body:
            meta.abstract = True

        # proxy
        if 'proxy = True' in meta_body or 'proxy=True' in meta_body:
            meta.proxy = True

        # unique_together
        ut_match = re.search(r"unique_together\s*=\s*[\[\(]([^\]\)]+)", meta_body)
        if ut_match:
            meta.unique_together = re.findall(r"['\"](\w+)['\"]", ut_match.group(1))

        return meta

    def _extract_managers(self, class_body: str) -> List[DjangoManagerInfo]:
        """Extract manager definitions."""
        managers = []
        for match in self.MANAGER_PATTERN.finditer(class_body):
            managers.append(DjangoManagerInfo(
                name=match.group(1),
                manager_class=match.group(2),
                is_custom=match.group(2) != 'Manager',
                line_number=class_body[:match.start()].count('\n') + 1,
            ))
        return managers

    def _extract_docstring(self, class_body: str) -> Optional[str]:
        """Extract docstring from class body."""
        match = re.match(r'\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')', class_body, re.DOTALL)
        if match:
            return (match.group(1) or match.group(2)).strip()
        return None

    def _extract_int_arg(self, args: str, name: str) -> Optional[int]:
        """Extract an integer keyword argument."""
        match = re.search(rf'{name}\s*=\s*(\d+)', args)
        return int(match.group(1)) if match else None

    def _extract_str_arg(self, args: str, name: str) -> Optional[str]:
        """Extract a string keyword argument."""
        match = re.search(rf"{name}\s*=\s*['\"]([^'\"]*)['\"]", args)
        return match.group(1) if match else None

    def _extract_first_arg(self, args: str) -> str:
        """Extract the first positional argument."""
        args = args.strip()
        # Handle quoted string
        match = re.match(r"['\"]([^'\"]+)['\"]", args)
        if match:
            return match.group(1)
        # Handle bare name (e.g., User, 'self')
        match = re.match(r'(\w+(?:\.\w+)*)', args)
        if match:
            return match.group(1)
        return ""
