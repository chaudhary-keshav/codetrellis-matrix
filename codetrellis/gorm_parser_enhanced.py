"""
EnhancedGormParser v1.0 - Comprehensive GORM (Go ORM) parser.

Supports:
- GORM v1.x (jinzhu/gorm)
- GORM v2.x (gorm.io/gorm, new API, driver separation)

GORM-specific extraction:
- Model definitions (gorm.Model embedding, custom primary keys)
- Tag parsing (gorm:"column:name;type:varchar(100);primaryKey;autoIncrement;index;unique;not null;default:...")
- Associations (HasOne, HasMany, BelongsTo, Many2Many) via struct tags and preloads
- Hooks (BeforeCreate, AfterCreate, BeforeUpdate, AfterUpdate, BeforeSave, AfterSave, BeforeDelete, AfterDelete, AfterFind)
- Scopes (func(db *gorm.DB) *gorm.DB)
- Migrations (AutoMigrate, CreateTable, Migrator)
- Soft deletes (gorm.DeletedAt, soft_delete.DeletedAt)
- Transactions (Begin/Commit/Rollback, Transaction())
- Plugin detection (sharding, dbresolver, prometheus, opentelemetry)
- Driver detection (mysql, postgres, sqlite, sqlserver, clickhouse)

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class GormModelInfo:
    """GORM model/entity."""
    name: str
    table_name: str = ""
    embeds_gorm_model: bool = False
    has_soft_delete: bool = False
    fields: List[Dict[str, Any]] = field(default_factory=list)  # [{name, type, tags}]
    associations: List[Dict[str, str]] = field(default_factory=list)  # [{type, field, related_model}]
    file: str = ""
    line_number: int = 0


@dataclass
class GormHookInfo:
    """GORM lifecycle hook."""
    hook_type: str  # BeforeCreate, AfterCreate, etc.
    model: str  # Receiver type
    file: str = ""
    line_number: int = 0


@dataclass
class GormScopeInfo:
    """GORM scope function."""
    name: str
    file: str = ""
    line_number: int = 0


@dataclass
class GormMigrationInfo:
    """GORM migration call."""
    migration_type: str  # AutoMigrate, CreateTable, DropTable, etc.
    models: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class GormQueryInfo:
    """Notable GORM query pattern."""
    query_type: str  # Create, Find, First, Where, Joins, Preload, Raw, Exec, etc.
    model: str = ""
    conditions: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class GormParseResult:
    file_path: str
    file_type: str = "go"

    models: List[GormModelInfo] = field(default_factory=list)
    hooks: List[GormHookInfo] = field(default_factory=list)
    scopes: List[GormScopeInfo] = field(default_factory=list)
    migrations: List[GormMigrationInfo] = field(default_factory=list)
    queries: List[GormQueryInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    detected_driver: str = ""
    gorm_version: str = ""
    has_soft_delete: bool = False
    has_transactions: bool = False
    total_models: int = 0
    total_hooks: int = 0


class EnhancedGormParser:
    """Enhanced GORM parser for comprehensive ORM extraction."""

    GORM_V2_IMPORT = re.compile(r'"gorm\.io/gorm"')
    GORM_V1_IMPORT = re.compile(r'"github\.com/jinzhu/gorm"')

    # Model definition: type User struct { gorm.Model ... }
    MODEL_PATTERN = re.compile(
        r'type\s+(\w+)\s+struct\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # gorm struct tag: `gorm:"column:name;type:varchar(100);..."`
    GORM_TAG_PATTERN = re.compile(r'gorm:"([^"]*)"')

    # Table name override: func (User) TableName() string { return "users" }
    TABLE_NAME_PATTERN = re.compile(
        r'func\s+\(\s*\w*\s*\*?(\w+)\s*\)\s+TableName\s*\(\s*\)\s+string\s*\{[^}]*return\s+"([^"]+)"',
    )

    # Hooks
    HOOK_PATTERN = re.compile(
        r'func\s+\(\s*\w+\s+\*?(\w+)\s*\)\s+(Before(?:Create|Update|Save|Delete)|'
        r'After(?:Create|Update|Save|Delete|Find))\s*\(',
    )

    # Scope: func ScopeName(db *gorm.DB) *gorm.DB
    SCOPE_PATTERN = re.compile(
        r'func\s+(\w+)\s*\(\s*\w+\s+\*gorm\.DB\s*\)\s+\*gorm\.DB\s*\{',
    )

    # Migration: db.AutoMigrate(&User{}, &Product{})
    AUTO_MIGRATE_PATTERN = re.compile(
        r'\.AutoMigrate\s*\(\s*([^)]+)\)',
    )

    # CreateTable, DropTable, etc.
    MIGRATOR_PATTERN = re.compile(
        r'\.Migrator\(\)\.(\w+)\s*\(\s*([^)]*)\)',
    )

    # Transaction: db.Transaction(func(tx *gorm.DB) error { ... })
    TRANSACTION_PATTERN = re.compile(
        r'\.Transaction\s*\(\s*func\s*\(\s*\w+\s+\*gorm\.DB\s*\)',
    )

    # Begin/Commit/Rollback
    TX_PATTERN = re.compile(
        r'\.(Begin|Commit|Rollback|SavePoint|RollbackTo)\s*\(',
    )

    # Query methods
    QUERY_PATTERN = re.compile(
        r'\.(Create|Save|Delete|Find|First|Last|Take|Where|Or|Not|'
        r'Joins|Preload|Association|Related|'
        r'Raw|Exec|Scan|Row|Rows|Pluck|Count|'
        r'Group|Having|Order|Limit|Offset|Distinct|'
        r'Select|Omit|Assign|Attrs|FirstOrCreate|FirstOrInit|'
        r'Updates|Update|UpdateColumn|UpdateColumns)\s*\(',
    )

    # Association types in struct fields
    ASSOC_PATTERNS = {
        'has_one': re.compile(r'(\w+)\s+(\w+)\s+.*?`.*?gorm:.*?"`'),
        'has_many': re.compile(r'(\w+)\s+\[\](\w+)'),
        'belongs_to': re.compile(r'(\w+)ID\s+uint'),
        'many2many': re.compile(r'gorm:"many2many:(\w+)"'),
    }

    # Driver detection
    DRIVER_PATTERNS = {
        'mysql': re.compile(r'"gorm\.io/driver/mysql"'),
        'postgres': re.compile(r'"gorm\.io/driver/postgres"'),
        'sqlite': re.compile(r'"gorm\.io/driver/sqlite"'),
        'sqlserver': re.compile(r'"gorm\.io/driver/sqlserver"'),
        'clickhouse': re.compile(r'"gorm\.io/driver/clickhouse"'),
    }

    FRAMEWORK_PATTERNS = {
        'gorm': re.compile(r'"gorm\.io/gorm"|"github\.com/jinzhu/gorm"'),
        'gorm-dbresolver': re.compile(r'"gorm\.io/plugin/dbresolver"'),
        'gorm-sharding': re.compile(r'"gorm\.io/sharding"'),
        'gorm-prometheus': re.compile(r'"gorm\.io/plugin/prometheus"'),
        'gorm-opentelemetry': re.compile(r'"gorm\.io/plugin/opentelemetry"'),
        'gorm-soft-delete': re.compile(r'"gorm\.io/plugin/soft_delete"'),
        'gorm-optimisticlock': re.compile(r'"gorm\.io/plugin/optimisticlock"'),
        'gorm-datatypes': re.compile(r'"gorm\.io/datatypes"'),
        'gorm-gen': re.compile(r'"gorm\.io/gen"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> GormParseResult:
        result = GormParseResult(file_path=file_path)

        has_v2 = self.GORM_V2_IMPORT.search(content)
        has_v1 = self.GORM_V1_IMPORT.search(content)

        if not has_v2 and not has_v1:
            # Check for gorm tags or gorm.Model embedding without explicit import
            if not re.search(r'gorm\.Model|gorm:"', content):
                return result

        result.gorm_version = "v2" if has_v2 else "v1"
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_driver = self._detect_driver(content)

        # Table name overrides
        table_names: Dict[str, str] = {}
        for m in self.TABLE_NAME_PATTERN.finditer(content):
            table_names[m.group(1)] = m.group(2)

        # Models
        for m in self.MODEL_PATTERN.finditer(content):
            model_name = m.group(1)
            body = m.group(2)

            # Only include structs that look like GORM models
            is_gorm_model = (
                'gorm.Model' in body
                or 'gorm.DeletedAt' in body
                or 'gorm:"' in body
                or model_name in table_names
            )
            if not is_gorm_model:
                continue

            embeds_gorm_model = 'gorm.Model' in body
            has_soft_delete = 'DeletedAt' in body

            # Parse fields
            fields = []
            associations = []
            for line in body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('gorm.'):
                    continue

                field_match = re.match(r'(\w+)\s+([\[\]*\w.]+)', line)
                if field_match:
                    fname = field_match.group(1)
                    ftype = field_match.group(2)
                    tag_match = self.GORM_TAG_PATTERN.search(line)
                    tag = tag_match.group(1) if tag_match else ""

                    fields.append({'name': fname, 'type': ftype, 'tags': tag})

                    # Detect associations
                    if ftype.startswith('[]'):
                        related = ftype.lstrip('[]').lstrip('*')
                        m2m = re.search(r'gorm:"many2many:(\w+)"', line)
                        if m2m:
                            associations.append({'type': 'many2many', 'field': fname, 'related_model': related, 'join_table': m2m.group(1)})
                        else:
                            associations.append({'type': 'has_many', 'field': fname, 'related_model': related})
                    elif ftype.startswith('*') and not ftype.startswith('*gorm'):
                        associations.append({'type': 'has_one', 'field': fname, 'related_model': ftype.lstrip('*')})

            result.models.append(GormModelInfo(
                name=model_name,
                table_name=table_names.get(model_name, ""),
                embeds_gorm_model=embeds_gorm_model,
                has_soft_delete=has_soft_delete,
                fields=fields,
                associations=associations,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

            if has_soft_delete:
                result.has_soft_delete = True

        # Hooks
        for m in self.HOOK_PATTERN.finditer(content):
            result.hooks.append(GormHookInfo(
                model=m.group(1), hook_type=m.group(2),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Scopes
        for m in self.SCOPE_PATTERN.finditer(content):
            result.scopes.append(GormScopeInfo(
                name=m.group(1), file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Migrations
        for m in self.AUTO_MIGRATE_PATTERN.finditer(content):
            models_str = m.group(1)
            model_names = re.findall(r'&(\w+)\{', models_str)
            result.migrations.append(GormMigrationInfo(
                migration_type="AutoMigrate", models=model_names,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.MIGRATOR_PATTERN.finditer(content):
            models_str = m.group(2)
            model_names = re.findall(r'&(\w+)\{', models_str)
            result.migrations.append(GormMigrationInfo(
                migration_type=m.group(1), models=model_names,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Transactions
        if self.TRANSACTION_PATTERN.search(content) or self.TX_PATTERN.search(content):
            result.has_transactions = True

        # Query patterns
        for m in self.QUERY_PATTERN.finditer(content):
            result.queries.append(GormQueryInfo(
                query_type=m.group(1), file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        result.total_models = len(result.models)
        result.total_hooks = len(result.hooks)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_driver(self, content: str) -> str:
        for driver, pattern in self.DRIVER_PATTERNS.items():
            if pattern.search(content):
                return driver
        return ""
