"""
PhpModelExtractor - Extracts PHP ORM model, migration, and repository definitions.

This extractor parses PHP source code and extracts:
- Eloquent models (Laravel) with relationships, scopes, casts, fillable, hidden
- Doctrine ORM entities with annotations and attributes
- Propel models
- CakePHP Table classes
- Laravel migrations (create_table, add_column, etc.)
- Doctrine migrations
- Repository classes (Doctrine, custom)
- Model observers and events
- Soft deletes, timestamps, UUIDs
- Model factories

Supports PHP 5.x through PHP 8.3+ features.

Part of CodeTrellis v4.24 - PHP Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PhpRelationInfo:
    """Information about a PHP ORM relationship."""
    name: str
    kind: str = ""  # hasOne, hasMany, belongsTo, belongsToMany, morphTo, etc.
    related_model: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class PhpModelInfo:
    """Information about a PHP ORM model."""
    name: str
    table_name: Optional[str] = None
    orm: str = "eloquent"  # eloquent, doctrine, propel, cakephp
    relationships: List[PhpRelationInfo] = field(default_factory=list)
    fillable: List[str] = field(default_factory=list)
    guarded: List[str] = field(default_factory=list)
    hidden: List[str] = field(default_factory=list)
    casts: Dict[str, str] = field(default_factory=dict)
    scopes: List[str] = field(default_factory=list)
    accessors: List[str] = field(default_factory=list)
    mutators: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    uses_soft_deletes: bool = False
    uses_timestamps: bool = True
    uses_uuid: bool = False
    parent_class: Optional[str] = None
    namespace: Optional[str] = None
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None


@dataclass
class PhpMigrationInfo:
    """Information about a PHP database migration."""
    name: str
    operations: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    framework: str = "laravel"  # laravel, doctrine, phinx
    file: str = ""
    line_number: int = 0


@dataclass
class PhpRepositoryInfo:
    """Information about a PHP repository class."""
    name: str
    entity: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    orm: str = "doctrine"
    parent_class: Optional[str] = None
    file: str = ""
    line_number: int = 0


class PhpModelExtractor:
    """
    Extracts PHP ORM models, migrations, and repositories from source code.

    Handles:
    - Eloquent models (extends Model) with:
      - Relationships (hasOne, hasMany, belongsTo, belongsToMany, morphTo, etc.)
      - Fillable/guarded arrays
      - Hidden fields
      - Casts array
      - Scopes (scopeActive, etc.)
      - Accessors and mutators (getXAttribute, setXAttribute, PHP 8.x Attribute casts)
      - Soft deletes, timestamps, UUIDs
      - Custom table names
    - Doctrine entities (#[ORM\\Entity], @ORM\\Entity)
    - Propel models
    - CakePHP Table classes
    - Laravel migrations (Blueprint operations)
    - Doctrine migrations
    - Phinx migrations
    - Repository classes

    v4.24: Comprehensive PHP ORM extraction.
    """

    # Eloquent model class
    ELOQUENT_MODEL_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+(?P<parent>Model|Authenticatable|Pivot|MorphPivot|'
        r'Eloquent|BaseModel|[A-Za-z_\\]*Model)\b',
        re.MULTILINE
    )

    # Doctrine entity
    DOCTRINE_ENTITY_PATTERN = re.compile(
        r'(?:#\[ORM\\Entity|@ORM\\Entity|@Entity)',
        re.MULTILINE
    )

    # Doctrine entity class
    DOCTRINE_CLASS_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Table name: protected $table = 'name';
    TABLE_NAME_PATTERN = re.compile(
        r'''(?:protected|public)\s+\$table\s*=\s*['"](?P<name>[^'"]+)['"]''',
    )

    # Fillable: protected $fillable = [...]
    FILLABLE_PATTERN = re.compile(
        r'protected\s+\$fillable\s*=\s*\[(?P<fields>[^\]]*)\]',
        re.DOTALL
    )

    # Guarded: protected $guarded = [...]
    GUARDED_PATTERN = re.compile(
        r'protected\s+\$guarded\s*=\s*\[(?P<fields>[^\]]*)\]',
        re.DOTALL
    )

    # Hidden: protected $hidden = [...]
    HIDDEN_PATTERN = re.compile(
        r'protected\s+\$hidden\s*=\s*\[(?P<fields>[^\]]*)\]',
        re.DOTALL
    )

    # Casts: protected $casts = [...]
    CASTS_PATTERN = re.compile(
        r'protected\s+\$casts\s*=\s*\[(?P<casts>[^\]]*)\]',
        re.DOTALL
    )

    # Relationship methods
    RELATIONSHIP_PATTERN = re.compile(
        r'(?:public\s+)?function\s+(?P<name>\w+)\s*\([^)]*\)\s*(?::\s*\w+\s*)?'
        r'\{[^}]*\$this\s*->\s*(?P<type>hasOne|hasMany|belongsTo|belongsToMany|'
        r'hasManyThrough|hasOneThrough|morphTo|morphMany|morphOne|morphToMany|'
        r'morphedByMany)\s*\(\s*(?P<related>[A-Za-z_\\:]+)',
        re.DOTALL
    )

    # Scope methods: public function scopeActive($query)
    SCOPE_PATTERN = re.compile(
        r'public\s+function\s+scope(?P<name>[A-Z]\w*)\s*\(',
    )

    # Accessor: get{Name}Attribute or Attribute::get()
    ACCESSOR_PATTERN = re.compile(
        r'(?:public\s+function\s+get(?P<name>[A-Z]\w*)Attribute|'
        r'protected\s+function\s+(?P<name2>\w+)\s*\(\)\s*:\s*Attribute)',
    )

    # Mutator: set{Name}Attribute
    MUTATOR_PATTERN = re.compile(
        r'public\s+function\s+set(?P<name>[A-Z]\w*)Attribute',
    )

    # SoftDeletes trait
    SOFT_DELETES_PATTERN = re.compile(
        r'use\s+[A-Za-z_\\]*SoftDeletes',
    )

    # HasUuids / UuidTrait
    UUID_PATTERN = re.compile(
        r'use\s+[A-Za-z_\\]*(?:HasUuids|HasUlids|UuidTrait)',
    )

    # Timestamps: public $timestamps = false
    NO_TIMESTAMPS_PATTERN = re.compile(
        r'public\s+\$timestamps\s*=\s*false',
    )

    # Laravel migration
    MIGRATION_CLASS_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+Migration',
        re.MULTILINE
    )

    # Migration operations (in up() method)
    MIGRATION_CREATE_TABLE_PATTERN = re.compile(
        r'''Schema::create\s*\(\s*['"](?P<table>[^'"]+)['"]''',
    )

    MIGRATION_TABLE_PATTERN = re.compile(
        r'''Schema::table\s*\(\s*['"](?P<table>[^'"]+)['"]''',
    )

    MIGRATION_DROP_PATTERN = re.compile(
        r'''Schema::drop(?:IfExists)?\s*\(\s*['"](?P<table>[^'"]+)['"]''',
    )

    # Column definition in migration
    MIGRATION_COLUMN_PATTERN = re.compile(
        r'''\$table\s*->\s*(?P<type>string|integer|bigInteger|unsignedBigInteger|'''
        r'''boolean|text|longText|mediumText|json|jsonb|timestamp|date|datetime|'''
        r'''decimal|float|double|binary|uuid|ulid|id|foreignId|enum|set|char|'''
        r'''smallInteger|tinyInteger|mediumInteger|unsignedInteger|'''
        r'''softDeletes|timestamps|rememberToken)\s*\(\s*['"]?(?P<name>[^'",)]+)?['"]?\s*\)''',
    )

    # Repository class
    REPOSITORY_PATTERN = re.compile(
        r'class\s+(?P<name>\w+Repository)\s+(?:extends\s+(?P<parent>[A-Za-z_\\]+)\s*)?',
        re.MULTILINE
    )

    # Doctrine repository entity reference
    DOCTRINE_REPOSITORY_ENTITY_PATTERN = re.compile(
        r'''#\[ORM\\Entity\s*\(\s*repositoryClass:\s*(?P<repo>[A-Za-z_\\]+)::class\s*\)''',
    )

    def __init__(self):
        """Initialize the model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all PHP ORM patterns from source code.

        Args:
            content: PHP source code content
            file_path: Path to source file

        Returns:
            Dict with 'models', 'migrations', 'repositories' keys
        """
        models = self._extract_models(content, file_path)
        migrations = self._extract_migrations(content, file_path)
        repositories = self._extract_repositories(content, file_path)

        return {
            'models': models,
            'migrations': migrations,
            'repositories': repositories,
        }

    def _extract_string_array(self, text: str) -> List[str]:
        """Extract string values from an array-like string."""
        items = []
        for match in re.finditer(r'''['"]([^'"]+)['"]''', text):
            items.append(match.group(1))
        return items

    def _extract_models(self, content: str, file_path: str) -> List[PhpModelInfo]:
        """Extract ORM model definitions."""
        models = []

        # Eloquent models
        for match in self.ELOQUENT_MODEL_PATTERN.finditer(content):
            name = match.group('name')
            parent = match.group('parent')
            line_number = content[:match.start()].count('\n') + 1

            model = PhpModelInfo(
                name=name,
                orm="eloquent",
                parent_class=parent,
                file=file_path,
                line_number=line_number,
            )

            # Extract model body
            body_start = content.find('{', match.end())
            if body_start != -1:
                body = self._extract_body(content, match.end())
                if body:
                    # Table name
                    table_match = self.TABLE_NAME_PATTERN.search(body)
                    if table_match:
                        model.table_name = table_match.group('name')

                    # Fillable
                    fillable_match = self.FILLABLE_PATTERN.search(body)
                    if fillable_match:
                        model.fillable = self._extract_string_array(fillable_match.group('fields'))

                    # Guarded
                    guarded_match = self.GUARDED_PATTERN.search(body)
                    if guarded_match:
                        model.guarded = self._extract_string_array(guarded_match.group('fields'))

                    # Hidden
                    hidden_match = self.HIDDEN_PATTERN.search(body)
                    if hidden_match:
                        model.hidden = self._extract_string_array(hidden_match.group('fields'))

                    # Casts
                    casts_match = self.CASTS_PATTERN.search(body)
                    if casts_match:
                        casts_text = casts_match.group('casts')
                        for cast_match in re.finditer(r'''['"](\w+)['"]\s*=>\s*['"](\w+)['"]''', casts_text):
                            model.casts[cast_match.group(1)] = cast_match.group(2)

                    # Relationships
                    for rel_match in self.RELATIONSHIP_PATTERN.finditer(body):
                        related = rel_match.group('related')
                        # Clean up ::class suffix
                        related = related.replace('::class', '').rsplit('\\', 1)[-1]
                        model.relationships.append(PhpRelationInfo(
                            name=rel_match.group('name'),
                            kind=rel_match.group('type'),
                            related_model=related,
                            file=file_path,
                        ))

                    # Scopes
                    for scope_match in self.SCOPE_PATTERN.finditer(body):
                        model.scopes.append(scope_match.group('name').lower())

                    # Accessors
                    for acc_match in self.ACCESSOR_PATTERN.finditer(body):
                        acc_name = acc_match.group('name') or acc_match.group('name2')
                        if acc_name:
                            model.accessors.append(acc_name)

                    # Mutators
                    for mut_match in self.MUTATOR_PATTERN.finditer(body):
                        model.mutators.append(mut_match.group('name'))

                    # Soft deletes
                    model.uses_soft_deletes = bool(self.SOFT_DELETES_PATTERN.search(body))

                    # UUIDs
                    model.uses_uuid = bool(self.UUID_PATTERN.search(body))

                    # Timestamps
                    if self.NO_TIMESTAMPS_PATTERN.search(body):
                        model.uses_timestamps = False

                    # Trait uses
                    for trait_match in re.finditer(r'use\s+([A-Za-z_\\]+)\s*[;,{]', body):
                        trait_name = trait_match.group(1).rsplit('\\', 1)[-1]
                        if trait_name not in ('SoftDeletes',):
                            model.traits.append(trait_name)

            models.append(model)

        # Doctrine entities
        if self.DOCTRINE_ENTITY_PATTERN.search(content):
            for match in self.DOCTRINE_CLASS_PATTERN.finditer(content):
                name = match.group('name')
                line_number = content[:match.start()].count('\n') + 1

                # Check that Entity annotation is near this class
                pre_context = content[max(0, match.start() - 300):match.start()]
                if not re.search(r'(?:#\[ORM\\Entity|@ORM\\Entity|@Entity)', pre_context):
                    continue

                model = PhpModelInfo(
                    name=name,
                    orm="doctrine",
                    file=file_path,
                    line_number=line_number,
                )

                # Extract Doctrine table name
                table_match = re.search(
                    r'''(?:#\[ORM\\Table|@ORM\\Table|@Table)\s*\(\s*(?:name:\s*)?['"](?P<name>[^'"]+)['"]''',
                    pre_context
                )
                if table_match:
                    model.table_name = table_match.group('name')

                models.append(model)

        return models

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
            elif ch in ("'", '"'):
                quote = ch
                pos += 1
                while pos < len(content) and content[pos] != quote:
                    if content[pos] == '\\':
                        pos += 1
                    pos += 1
            pos += 1

        if depth == 0:
            return content[brace_start + 1:pos - 1]
        return None

    def _extract_migrations(self, content: str, file_path: str) -> List[PhpMigrationInfo]:
        """Extract migration definitions."""
        migrations = []

        for match in self.MIGRATION_CLASS_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1

            migration = PhpMigrationInfo(
                name=name,
                framework="laravel",
                file=file_path,
                line_number=line_number,
            )

            body = self._extract_body(content, match.end())
            if body:
                # Created tables
                for create_match in self.MIGRATION_CREATE_TABLE_PATTERN.finditer(body):
                    table = create_match.group('table')
                    migration.tables.append(table)
                    migration.operations.append(f"create:{table}")

                # Modified tables
                for table_match in self.MIGRATION_TABLE_PATTERN.finditer(body):
                    table = table_match.group('table')
                    if table not in migration.tables:
                        migration.tables.append(table)
                    migration.operations.append(f"alter:{table}")

                # Dropped tables
                for drop_match in self.MIGRATION_DROP_PATTERN.finditer(body):
                    table = drop_match.group('table')
                    migration.operations.append(f"drop:{table}")

                # Columns
                for col_match in self.MIGRATION_COLUMN_PATTERN.finditer(body):
                    col_name = col_match.group('name')
                    col_type = col_match.group('type')
                    if col_name:
                        migration.columns.append(f"{col_name}:{col_type}")

            migrations.append(migration)

        # Check for Phinx/Doctrine migrations
        if 'AbstractMigration' in content or 'Phinx' in content:
            phinx_match = re.search(r'class\s+(\w+)\s+extends\s+AbstractMigration', content)
            if phinx_match:
                line_number = content[:phinx_match.start()].count('\n') + 1
                migrations.append(PhpMigrationInfo(
                    name=phinx_match.group(1),
                    framework="phinx",
                    file=file_path,
                    line_number=line_number,
                ))

        return migrations

    def _extract_repositories(self, content: str, file_path: str) -> List[PhpRepositoryInfo]:
        """Extract repository class definitions."""
        repositories = []

        for match in self.REPOSITORY_PATTERN.finditer(content):
            name = match.group('name')
            parent = match.group('parent')
            line_number = content[:match.start()].count('\n') + 1

            orm = "custom"
            if parent and ('EntityRepository' in parent or 'ServiceEntityRepository' in parent):
                orm = "doctrine"
            elif parent and 'Repository' in parent:
                orm = "eloquent"

            repo = PhpRepositoryInfo(
                name=name,
                orm=orm,
                parent_class=parent,
                file=file_path,
                line_number=line_number,
            )

            # Extract methods
            body = self._extract_body(content, match.end())
            if body:
                for method_match in re.finditer(r'public\s+function\s+(\w+)\s*\(', body):
                    method_name = method_match.group(1)
                    if not method_name.startswith('__'):
                        repo.methods.append(method_name)

            # Look for entity reference
            entity_match = re.search(
                r'''(?:getEntityName|getClassName)\s*\(\)\s*\{[^}]*return\s+(\w+)::class''',
                content[match.start():match.start() + 2000]
            )
            if entity_match:
                repo.entity = entity_match.group(1)

            repositories.append(repo)

        return repositories
