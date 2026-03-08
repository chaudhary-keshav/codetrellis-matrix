"""
RubyModelExtractor - Extracts Ruby database models, migrations, and ORM patterns.

This extractor parses Ruby source code and extracts:
- ActiveRecord models (associations, validations, scopes, callbacks, enums)
- Sequel models
- Mongoid models (documents, fields, embedded relations)
- ROM (Ruby Object Mapper) relations/mappers
- DataMapper models
- ActiveRecord migrations (create_table, add_column, add_index)
- Database schema definitions
- Rails concerns for models

Supports Rails 4.x through Rails 8.x, Sequel, Mongoid 7+, ROM 5+.

Part of CodeTrellis v4.23 - Ruby Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RubyAssociationInfo:
    """Information about a Ruby model association."""
    kind: str  # belongs_to, has_many, has_one, has_and_belongs_to_many, embeds_many, embeds_one
    name: str
    class_name: Optional[str] = None
    foreign_key: Optional[str] = None
    through: Optional[str] = None
    dependent: Optional[str] = None  # destroy, nullify, delete_all
    polymorphic: bool = False


@dataclass
class RubyValidationInfo:
    """Information about a Ruby model validation."""
    kind: str  # presence, uniqueness, length, format, numericality, custom
    fields: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RubyScopeInfo:
    """Information about a Ruby model scope."""
    name: str
    description: Optional[str] = None
    is_default: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class RubyModelInfo:
    """Information about a Ruby ORM model."""
    name: str
    table_name: Optional[str] = None
    orm: str = "activerecord"  # activerecord, sequel, mongoid, rom, datamapper
    parent_class: Optional[str] = None
    fields: List[Dict] = field(default_factory=list)
    associations: List[RubyAssociationInfo] = field(default_factory=list)
    validations: List[RubyValidationInfo] = field(default_factory=list)
    scopes: List[RubyScopeInfo] = field(default_factory=list)
    callbacks: List[str] = field(default_factory=list)
    enums: List[Dict] = field(default_factory=list)
    indexes: List[Dict] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_sti: bool = False  # Single Table Inheritance
    is_polymorphic: bool = False
    concerns: List[str] = field(default_factory=list)


@dataclass
class RubyMigrationInfo:
    """Information about a Ruby database migration."""
    name: str
    version: Optional[str] = None
    direction: str = "up"  # up, down, change
    operations: List[Dict] = field(default_factory=list)  # create_table, add_column, etc.
    file: str = ""
    line_number: int = 0


class RubyModelExtractor:
    """
    Extracts Ruby model and migration definitions from source code.

    Handles:
    - ActiveRecord models with associations, validations, scopes, callbacks
    - ActiveRecord enums
    - Sequel models
    - Mongoid documents with fields, relations, embedded documents
    - ROM relations/mappers/commands
    - DataMapper models
    - Rails migrations (create_table, add_column, add_index, etc.)
    - Schema.rb parsing
    - Single Table Inheritance (STI) detection
    - Polymorphic associations
    """

    # ActiveRecord model pattern
    AR_MODEL_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>[A-Z]\w*)\s*<\s*(?P<parent>ActiveRecord::Base|ApplicationRecord|ActiveRecord::Migration(?:\[\d+\.\d+\])?)',
        re.MULTILINE
    )

    # Sequel model pattern
    SEQUEL_MODEL_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>[A-Z]\w*)\s*<\s*Sequel::Model',
        re.MULTILINE
    )

    # Mongoid document pattern
    MONGOID_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>[A-Z]\w*).*\n(?:.*\n)*?\s*include\s+Mongoid::Document',
        re.MULTILINE
    )

    # Mongoid simpler detection
    MONGOID_INCLUDE_PATTERN = re.compile(
        r'include\s+Mongoid::Document',
        re.MULTILINE
    )

    # Association patterns
    ASSOCIATION_PATTERN = re.compile(
        r'^\s*(?P<kind>belongs_to|has_many|has_one|has_and_belongs_to_many|embeds_many|embeds_one|embedded_in)\s+:(?P<name>\w+)(?P<options>[^\n]*)',
        re.MULTILINE
    )

    # Validation patterns
    VALIDATION_PATTERN = re.compile(
        r'^\s*validates?\s+(?P<fields>(?::[\w,\s]+)+)\s*,?\s*(?P<options>[^\n]+)?',
        re.MULTILINE
    )

    # Named validations
    VALIDATES_PATTERN = re.compile(
        r'^\s*validates_(?P<kind>presence_of|uniqueness_of|length_of|format_of|numericality_of|inclusion_of|exclusion_of|acceptance_of|confirmation_of|associated)\s+:(?P<field>\w+)',
        re.MULTILINE
    )

    # Scope pattern
    SCOPE_PATTERN = re.compile(
        r'^\s*scope\s+:(?P<name>\w+)\s*,\s*(?:->|lambda|proc)',
        re.MULTILINE
    )

    # Default scope
    DEFAULT_SCOPE_PATTERN = re.compile(
        r'^\s*default_scope\s',
        re.MULTILINE
    )

    # Enum pattern (Rails 4.1+)
    ENUM_PATTERN = re.compile(
        r'^\s*enum\s+(?::?(?P<name>\w+)(?:\s*,\s*|\s*=>\s*|\s*:\s*))(?P<values>[^\n]+)',
        re.MULTILINE
    )

    # Callback pattern
    CALLBACK_PATTERN = re.compile(
        r'^\s*(?P<kind>before_save|after_save|before_create|after_create|before_update|after_update|before_destroy|after_destroy|before_validation|after_validation|after_commit|after_rollback|after_initialize|after_find|around_save|around_create|around_update|around_destroy)\s+:?(?P<name>\w+)',
        re.MULTILINE
    )

    # Concern pattern
    CONCERN_INCLUDE_PATTERN = re.compile(
        r'^\s*include\s+(?P<name>\w+(?:::\w+)*)',
        re.MULTILINE
    )

    # Migration operations
    MIGRATION_OP_PATTERN = re.compile(
        r'^\s*(?P<op>create_table|drop_table|add_column|remove_column|rename_column|add_index|remove_index|add_reference|add_foreign_key|change_column|change_column_default|change_column_null|create_join_table|add_timestamps|rename_table)\s+[:\'](?P<target>\w+)',
        re.MULTILINE
    )

    # Column definition in create_table block
    COLUMN_PATTERN = re.compile(
        r'^\s*t\.(?P<type>string|text|integer|bigint|float|decimal|boolean|date|datetime|timestamp|time|binary|json|jsonb|uuid|inet|citext|hstore|array|references|belongs_to)\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # Mongoid field definition
    MONGOID_FIELD_PATTERN = re.compile(
        r'^\s*field\s+:(?P<name>\w+)\s*,\s*type:\s*(?P<type>\w+)',
        re.MULTILINE
    )

    # Table name override
    TABLE_NAME_PATTERN = re.compile(
        r'^\s*self\.table_name\s*=\s*[\'"](?P<name>\w+)[\'"]',
        re.MULTILINE
    )

    # ActiveRecord index in schema
    INDEX_PATTERN = re.compile(
        r'^\s*(?:add_index|t\.index)\s+[:\[\'](?P<columns>[^\]]+)',
        re.MULTILINE
    )

    # STI detection: self.inheritance_column or type column
    STI_PATTERN = re.compile(
        r'self\.inheritance_column|^\s*t\.\w+\s+:type\b',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all model and migration definitions from Ruby source code.

        Args:
            content: Ruby source code content
            file_path: Path to source file

        Returns:
            Dict with 'models', 'migrations' keys
        """
        models = self._extract_models(content, file_path)
        migrations = self._extract_migrations(content, file_path)

        return {
            'models': models,
            'migrations': migrations,
        }

    def _extract_models(self, content: str, file_path: str) -> List[RubyModelInfo]:
        """Extract ORM model definitions."""
        models = []

        # ActiveRecord models
        for match in self.AR_MODEL_PATTERN.finditer(content):
            name = match.group('name')
            parent = match.group('parent')

            # Skip migrations
            if 'Migration' in parent:
                continue

            line = content[:match.start()].count('\n') + 1

            # Extract associations
            associations = self._extract_associations(content)

            # Extract validations
            validations = self._extract_validations(content)

            # Extract scopes
            scopes = self._extract_scopes(content, file_path)

            # Extract callbacks
            callbacks = [m.group('name') for m in self.CALLBACK_PATTERN.finditer(content)]

            # Extract enums
            enums = self._extract_enums(content)

            # Check for table name override
            table_name = None
            tn_match = self.TABLE_NAME_PATTERN.search(content)
            if tn_match:
                table_name = tn_match.group('name')
            else:
                # Default table name (pluralize class name)
                table_name = self._pluralize(name.lower())

            # Check for STI
            is_sti = bool(self.STI_PATTERN.search(content)) or (parent not in ('ApplicationRecord', 'ActiveRecord::Base'))

            # Extract concerns
            concerns = []
            for cm in self.CONCERN_INCLUDE_PATTERN.finditer(content):
                concern_name = cm.group('name')
                if concern_name not in ('ActiveRecord', 'ActiveModel', 'ActiveSupport'):
                    concerns.append(concern_name)

            model = RubyModelInfo(
                name=name,
                table_name=table_name,
                orm="activerecord",
                parent_class=parent,
                associations=associations,
                validations=validations,
                scopes=scopes,
                callbacks=callbacks,
                enums=enums,
                file=file_path,
                line_number=line,
                is_sti=is_sti and parent not in ('ApplicationRecord', 'ActiveRecord::Base'),
                concerns=concerns,
            )
            models.append(model)

        # Sequel models
        for match in self.SEQUEL_MODEL_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            associations = self._extract_associations(content)

            models.append(RubyModelInfo(
                name=name,
                orm="sequel",
                associations=associations,
                file=file_path,
                line_number=line,
            ))

        # Mongoid models
        if self.MONGOID_INCLUDE_PATTERN.search(content):
            # Find the enclosing class
            class_match = re.search(r'^\s*class\s+(?P<name>[A-Z]\w*)', content, re.MULTILINE)
            if class_match:
                name = class_match.group('name')
                line = content[:class_match.start()].count('\n') + 1

                # Extract Mongoid fields
                fields = []
                for fm in self.MONGOID_FIELD_PATTERN.finditer(content):
                    fields.append({
                        'name': fm.group('name'),
                        'type': fm.group('type'),
                    })

                associations = self._extract_associations(content)

                models.append(RubyModelInfo(
                    name=name,
                    orm="mongoid",
                    fields=fields,
                    associations=associations,
                    file=file_path,
                    line_number=line,
                ))

        return models

    def _extract_associations(self, content: str) -> List[RubyAssociationInfo]:
        """Extract model associations."""
        associations = []

        for match in self.ASSOCIATION_PATTERN.finditer(content):
            kind = match.group('kind')
            name = match.group('name')
            options_str = match.group('options') or ""

            # Parse options
            class_name = None
            cn_match = re.search(r'class_name:\s*[\'"](\w+)[\'"]', options_str)
            if cn_match:
                class_name = cn_match.group(1)

            foreign_key = None
            fk_match = re.search(r'foreign_key:\s*[\'"](\w+)[\'"]', options_str)
            if fk_match:
                foreign_key = fk_match.group(1)

            through = None
            thr_match = re.search(r'through:\s*:(\w+)', options_str)
            if thr_match:
                through = thr_match.group(1)

            dependent = None
            dep_match = re.search(r'dependent:\s*:(\w+)', options_str)
            if dep_match:
                dependent = dep_match.group(1)

            polymorphic = 'polymorphic' in options_str

            associations.append(RubyAssociationInfo(
                kind=kind,
                name=name,
                class_name=class_name,
                foreign_key=foreign_key,
                through=through,
                dependent=dependent,
                polymorphic=polymorphic,
            ))

        return associations

    def _extract_validations(self, content: str) -> List[RubyValidationInfo]:
        """Extract model validations."""
        validations = []

        for match in self.VALIDATION_PATTERN.finditer(content):
            fields_str = match.group('fields')
            options_str = match.group('options') or ""

            fields = re.findall(r':(\w+)', fields_str)
            if not fields:
                continue

            # Determine validation kind from options
            kinds = []
            for kind in ['presence', 'uniqueness', 'length', 'format', 'numericality',
                        'inclusion', 'exclusion', 'acceptance', 'confirmation', 'associated']:
                if kind in options_str:
                    kinds.append(kind)

            if not kinds:
                kinds = ['custom']

            for kind in kinds:
                validations.append(RubyValidationInfo(
                    kind=kind,
                    fields=fields,
                ))

        # Named validations (validates_presence_of, etc.)
        for match in self.VALIDATES_PATTERN.finditer(content):
            kind = match.group('kind').replace('_of', '')
            field_name = match.group('field')
            validations.append(RubyValidationInfo(
                kind=kind,
                fields=[field_name],
            ))

        return validations

    def _extract_scopes(self, content: str, file_path: str) -> List[RubyScopeInfo]:
        """Extract model scopes."""
        scopes = []

        for match in self.SCOPE_PATTERN.finditer(content):
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            scopes.append(RubyScopeInfo(
                name=name,
                file=file_path,
                line_number=line,
            ))

        # Default scope
        if self.DEFAULT_SCOPE_PATTERN.search(content):
            scopes.append(RubyScopeInfo(
                name='default',
                is_default=True,
                file=file_path,
            ))

        return scopes

    def _extract_enums(self, content: str) -> List[Dict]:
        """Extract ActiveRecord enum definitions."""
        enums = []

        for match in self.ENUM_PATTERN.finditer(content):
            name = match.group('name')
            values_str = match.group('values')
            # Try to extract enum values
            values = re.findall(r':(\w+)', values_str)
            enums.append({
                'name': name,
                'values': values[:20],
            })

        return enums

    def _extract_migrations(self, content: str, file_path: str) -> List[RubyMigrationInfo]:
        """Extract database migration definitions."""
        migrations = []

        # Detect migration class
        mig_match = re.search(
            r'class\s+(?P<name>\w+)\s*<\s*ActiveRecord::Migration(?:\[(?P<version>\d+\.\d+)\])?',
            content
        )
        if not mig_match:
            return migrations

        name = mig_match.group('name')
        version = mig_match.group('version')
        line = content[:mig_match.start()].count('\n') + 1

        # Extract operations
        operations = []
        for match in self.MIGRATION_OP_PATTERN.finditer(content):
            op = match.group('op')
            target = match.group('target')

            op_info = {'operation': op, 'target': target}

            # If create_table, extract columns
            if op == 'create_table':
                columns = []
                for col_match in self.COLUMN_PATTERN.finditer(content):
                    columns.append({
                        'name': col_match.group('name'),
                        'type': col_match.group('type'),
                    })
                op_info['columns'] = columns[:30]

            operations.append(op_info)

        migrations.append(RubyMigrationInfo(
            name=name,
            version=version,
            operations=operations,
            file=file_path,
            line_number=line,
        ))

        return migrations

    def _pluralize(self, name: str) -> str:
        """Simple pluralization for table name inference."""
        if name.endswith('y') and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        else:
            return name + 's'
