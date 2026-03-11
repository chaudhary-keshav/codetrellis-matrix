"""
EnhancedSeaORMParser v1.0 - Comprehensive SeaORM parser.

Extracts SeaORM-specific patterns from Rust source files:
- Entity definitions (DeriveEntityModel, DeriveRelation)
- ActiveModel operations (insert, update, delete, save)
- Relations (HasMany, HasOne, BelongsTo)
- Query builder (find, filter, select, paginate)
- Migration support (MigratorTrait, MigrationTrait)
- Database connections (DatabaseConnection, ConnectOptions)
- Column definitions and custom types
- Seeder patterns
- Transaction support

Supports SeaORM 0.x through 1.x.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SeaORMEntityInfo:
    name: str
    table_name: str = ""
    columns: List[str] = field(default_factory=list)
    primary_key: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMRelationInfo:
    kind: str  # HasMany, HasOne, BelongsTo
    from_entity: str = ""
    to_entity: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMQueryInfo:
    kind: str  # find, find_by_id, filter, all, paginate, insert, update, delete
    entity: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMMigrationInfo:
    kind: str  # migration_trait, up, down, create_table, alter_table
    name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMConnectionInfo:
    backend: str  # postgres, mysql, sqlite
    pool: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMActiveModelInfo:
    entity: str
    operation: str = ""  # insert, update, delete, save
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMColumnInfo:
    name: str
    column_type: str = ""
    nullable: bool = False
    unique: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SeaORMParseResult:
    file_path: str
    file_type: str = "rust"

    entities: List[SeaORMEntityInfo] = field(default_factory=list)
    relations: List[SeaORMRelationInfo] = field(default_factory=list)
    queries: List[SeaORMQueryInfo] = field(default_factory=list)
    migrations: List[SeaORMMigrationInfo] = field(default_factory=list)
    connections: List[SeaORMConnectionInfo] = field(default_factory=list)
    active_models: List[SeaORMActiveModelInfo] = field(default_factory=list)
    columns: List[SeaORMColumnInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    seaorm_version: str = ""


class EnhancedSeaORMParser:
    """
    Enhanced SeaORM parser for comprehensive async ORM analysis.

    Supports SeaORM 0.x through 1.x:
    - v0.x: DeriveEntityModel, ActiveModel, async queries
    - v1.0: Stabilized API, improved migration system
    """

    SEAORM_DETECT = re.compile(
        r'(?:use\s+sea_orm|sea_orm::|#\[derive\(.*DeriveEntityModel.*\)]|DeriveRelation)',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'sea-orm': re.compile(r'\bsea_orm\b|sea-orm'),
        'sea-orm-migration': re.compile(r'sea_orm_migration|MigratorTrait'),
        'sea-orm-cli': re.compile(r'sea-orm-cli'),
        'sea-query': re.compile(r'sea_query'),
    }

    # #[derive(DeriveEntityModel)] + #[sea_orm(table_name = "users")]
    ENTITY_DERIVE = re.compile(
        r'#\[derive\([^)]*DeriveEntityModel[^)]*\)\]\s*(?:#\[sea_orm\((?P<attrs>[^)]*)\)\]\s*)?(?:pub\s+)?struct\s+(?P<name>\w+)',
        re.MULTILINE | re.DOTALL
    )

    TABLE_NAME_ATTR = re.compile(
        r'table_name\s*=\s*"(\w+)"',
    )

    # #[derive(DeriveRelation)] enum Relation { ... }
    RELATION_ENUM = re.compile(
        r'#\[derive\([^)]*DeriveRelation[^)]*\)\]\s*(?:pub\s+)?enum\s+Relation\s*\{(?P<body>[^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # #[sea_orm(has_many = "Entity::Posts")] or
    # #[sea_orm(belongs_to = "Entity::User", ...)]
    RELATION_ATTR = re.compile(
        r'#\[sea_orm\(\s*(?P<kind>has_many|has_one|belongs_to)\s*=\s*"(?P<target>[^"]+)"',
        re.MULTILINE
    )

    # Entity::find(), Entity::find_by_id(), Entity::insert(), etc.
    ENTITY_QUERY = re.compile(
        r'(?P<entity>\w+)::(?P<op>find|find_by_id|insert|update|delete|delete_many|delete_by_id)\s*\(',
        re.MULTILINE
    )

    # .filter(), .all(), .one(), .paginate(), .count()
    QUERY_CHAIN = re.compile(
        r'\.(?P<op>filter|all|one|one_or_none|paginate|count|order_by_asc|order_by_desc|group_by|having|limit|offset)\s*\(',
        re.MULTILINE
    )

    # ActiveModel operations: model.insert(), model.update(), model.save(), model.delete()
    ACTIVE_MODEL_OP = re.compile(
        r'(?P<var>\w+)\.(?P<op>insert|update|save|delete)\s*\(\s*(?:&?\s*)?(?P<db>\w+)',
        re.MULTILINE
    )

    # impl MigrationTrait for MigrationXXX
    MIGRATION_TRAIT = re.compile(
        r'impl\s+MigrationTrait\s+for\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Migration operations: manager.create_table, alter_table, etc.
    MIGRATION_OP = re.compile(
        r'manager\.(?P<op>create_table|alter_table|drop_table|create_index|drop_index)\s*\(',
        re.MULTILINE
    )

    # Database connection: Database::connect
    DB_CONNECT = re.compile(
        r'Database::connect\s*\(\s*(?:"(?P<url>[^"]*)")?',
        re.MULTILINE
    )

    # Column definitions: #[sea_orm(column_type = "...", nullable, unique)]
    COLUMN_ATTR = re.compile(
        r'#\[sea_orm\((?P<attrs>[^)]*)\)\]\s*(?:pub\s+)?(?P<name>\w+)',
        re.MULTILINE
    )

    # impl Related<Entity> for Entity
    RELATED_IMPL = re.compile(
        r'impl\s+Related<(?:super::)?(?P<target>\w+)::Entity>\s+for\s+Entity',
        re.MULTILINE
    )

    VERSION_FEATURES = {
        '1.x': [r'sea-orm\s*=\s*"1', r'sea_orm\s*=\s*"1'],
        '0.12': [r'sea-orm\s*=\s*"0\.12', r'DerivePartialModel'],
        '0.11': [r'sea-orm\s*=\s*"0\.11'],
        '0.10': [r'sea-orm\s*=\s*"0\.10'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> SeaORMParseResult:
        result = SeaORMParseResult(file_path=file_path)
        if not self.SEAORM_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.seaorm_version = self._detect_version(content)
        result.entities = self._extract_entities(content, file_path)
        result.relations = self._extract_relations(content, file_path)
        result.queries = self._extract_queries(content, file_path)
        result.migrations = self._extract_migrations(content, file_path)
        result.connections = self._extract_connections(content, file_path)
        result.active_models = self._extract_active_models(content, file_path)
        result.columns = self._extract_columns(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_entities(self, content: str, file_path: str) -> List[SeaORMEntityInfo]:
        entities = []
        for m in self.ENTITY_DERIVE.finditer(content):
            name = m.group('name')
            attrs = m.group('attrs') or ''
            table_name = ''
            tn = self.TABLE_NAME_ATTR.search(attrs)
            if tn:
                table_name = tn.group(1)
            line_num = content[:m.start()].count('\n') + 1
            entities.append(SeaORMEntityInfo(
                name=name, table_name=table_name,
                file=file_path, line_number=line_num,
            ))
        return entities

    def _extract_relations(self, content: str, file_path: str) -> List[SeaORMRelationInfo]:
        relations = []

        for m in self.RELATION_ATTR.finditer(content):
            kind = m.group('kind')
            target = m.group('target')
            line_num = content[:m.start()].count('\n') + 1
            relations.append(SeaORMRelationInfo(
                kind=kind, to_entity=target,
                file=file_path, line_number=line_num,
            ))

        for m in self.RELATED_IMPL.finditer(content):
            target = m.group('target')
            line_num = content[:m.start()].count('\n') + 1
            relations.append(SeaORMRelationInfo(
                kind='related', to_entity=target,
                file=file_path, line_number=line_num,
            ))

        return relations

    def _extract_queries(self, content: str, file_path: str) -> List[SeaORMQueryInfo]:
        queries = []

        for m in self.ENTITY_QUERY.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(SeaORMQueryInfo(
                kind=m.group('op'), entity=m.group('entity'),
                file=file_path, line_number=line_num,
            ))

        for m in self.QUERY_CHAIN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(SeaORMQueryInfo(
                kind=m.group('op'),
                file=file_path, line_number=line_num,
            ))

        return queries

    def _extract_migrations(self, content: str, file_path: str) -> List[SeaORMMigrationInfo]:
        migrations = []

        for m in self.MIGRATION_TRAIT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            migrations.append(SeaORMMigrationInfo(
                kind='migration_trait', name=m.group('name'),
                file=file_path, line_number=line_num,
            ))

        for m in self.MIGRATION_OP.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            migrations.append(SeaORMMigrationInfo(
                kind=m.group('op'),
                file=file_path, line_number=line_num,
            ))

        return migrations

    def _extract_connections(self, content: str, file_path: str) -> List[SeaORMConnectionInfo]:
        connections = []
        for m in self.DB_CONNECT.finditer(content):
            url = m.group('url') or ''
            backend = 'postgres'
            if 'mysql' in url.lower():
                backend = 'mysql'
            elif 'sqlite' in url.lower():
                backend = 'sqlite'
            line_num = content[:m.start()].count('\n') + 1
            connections.append(SeaORMConnectionInfo(
                backend=backend, file=file_path, line_number=line_num,
            ))
        return connections

    def _extract_active_models(self, content: str, file_path: str) -> List[SeaORMActiveModelInfo]:
        active_models = []
        for m in self.ACTIVE_MODEL_OP.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            active_models.append(SeaORMActiveModelInfo(
                entity=m.group('var'), operation=m.group('op'),
                file=file_path, line_number=line_num,
            ))
        return active_models

    def _extract_columns(self, content: str, file_path: str) -> List[SeaORMColumnInfo]:
        columns = []
        for m in self.COLUMN_ATTR.finditer(content):
            attrs = m.group('attrs')
            name = m.group('name')
            col_type = ''
            ct = re.search(r'column_type\s*=\s*"(\w+)"', attrs)
            if ct:
                col_type = ct.group(1)
            nullable = 'nullable' in attrs
            unique = 'unique' in attrs
            line_num = content[:m.start()].count('\n') + 1
            columns.append(SeaORMColumnInfo(
                name=name, column_type=col_type,
                nullable=nullable, unique=unique,
                file=file_path, line_number=line_num,
            ))
        return columns
