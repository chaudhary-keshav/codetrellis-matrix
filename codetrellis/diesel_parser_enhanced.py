"""
EnhancedDieselParser v1.0 - Comprehensive Diesel ORM parser.

Extracts Diesel-specific patterns from Rust source files:
- Schema definitions (diesel::table!, schema.rs)
- Model derivations (Queryable, Insertable, AsChangeset, Identifiable, Associations)
- Query DSL usage (filter, find, insert_into, update, delete)
- Migrations (embed_migrations!, run_pending_migrations)
- Connection types (PgConnection, MysqlConnection, SqliteConnection)
- Custom types (FromSqlRow, AsExpression)
- Join relationships (belongs_to, has_many, inner_join, left_join)
- Pagination patterns
- Connection pooling (r2d2, deadpool)

Supports Diesel 1.x through 2.x.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DieselTableInfo:
    name: str
    columns: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class DieselModelInfo:
    name: str
    table_name: str = ""
    derives: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class DieselQueryInfo:
    kind: str  # select, insert, update, delete, filter, find
    table: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class DieselMigrationInfo:
    kind: str  # embed_migrations, run_pending, sql_file
    name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class DieselConnectionInfo:
    backend: str  # pg, mysql, sqlite
    pool: str = ""  # r2d2, deadpool, bb8, mobc
    file: str = ""
    line_number: int = 0


@dataclass
class DieselAssociationInfo:
    model: str
    kind: str  # belongs_to, has_many, has_one
    target: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class DieselCustomTypeInfo:
    name: str
    kind: str  # FromSqlRow, AsExpression, ToSql, FromSql
    file: str = ""
    line_number: int = 0


@dataclass
class DieselParseResult:
    file_path: str
    file_type: str = "rust"

    tables: List[DieselTableInfo] = field(default_factory=list)
    models: List[DieselModelInfo] = field(default_factory=list)
    queries: List[DieselQueryInfo] = field(default_factory=list)
    migrations: List[DieselMigrationInfo] = field(default_factory=list)
    connections: List[DieselConnectionInfo] = field(default_factory=list)
    associations: List[DieselAssociationInfo] = field(default_factory=list)
    custom_types: List[DieselCustomTypeInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    diesel_version: str = ""


class EnhancedDieselParser:
    """
    Enhanced Diesel ORM parser for comprehensive database layer analysis.

    Supports Diesel 1.x through 2.x:
    - v1.x: Original API with table! macro, PgConnection
    - v2.0: Async support, improved type system, QueryableByName removed
    """

    DIESEL_DETECT = re.compile(
        r'(?:use\s+diesel|diesel::|#\[derive\(.*(?:Queryable|Insertable|AsChangeset).*\)]|diesel::table!)',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'diesel': re.compile(r'\bdiesel\b'),
        'diesel-migrations': re.compile(r'diesel_migrations|embed_migrations'),
        'diesel-r2d2': re.compile(r'diesel::r2d2|r2d2::Pool'),
        'diesel-async': re.compile(r'diesel_async|AsyncPgConnection'),
        'diesel-derives': re.compile(r'diesel_derives|diesel::deserialize'),
    }

    # diesel::table! { users (id) { ... } }
    TABLE_MACRO = re.compile(
        r'(?:diesel::)?table!\s*\{\s*(?P<name>\w+)\s*(?:\(\s*(?P<pk>\w+)\s*\))?\s*\{(?P<body>[^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Column inside table!: name -> Type,
    COLUMN_PATTERN = re.compile(
        r'(\w+)\s*->\s*(\w+)',
    )

    # #[derive(Queryable, Insertable, ...)]
    DERIVE_MODEL = re.compile(
        r'#\[derive\(([^)]*(?:Queryable|Insertable|AsChangeset|Identifiable|Associations|Selectable|QueryableByName)[^)]*)\)\]\s*(?:#\[diesel\(table_name\s*=\s*"?(\w+)"?\s*\)])?\s*(?:pub\s+)?struct\s+(\w+)',
        re.MULTILINE
    )

    # #[diesel(table_name = "users")] or #[table_name = "users"]
    TABLE_NAME_ATTR = re.compile(
        r'#\[(?:diesel\()?\s*table_name\s*=\s*"?(\w+)"?\s*\)?\]',
        re.MULTILINE
    )

    # Query DSL: users::table.filter(...), diesel::insert_into(users)
    QUERY_SELECT = re.compile(
        r'(?P<table>\w+)::table\s*\.(?P<op>filter|find|select|order|limit|offset|first|load|get_result)',
        re.MULTILINE
    )

    QUERY_INSERT = re.compile(
        r'(?:diesel::)?insert_into\s*\(\s*(?P<table>\w+)(?:::\w+)?\s*\)',
        re.MULTILINE
    )

    QUERY_UPDATE = re.compile(
        r'(?:diesel::)?update\s*\(\s*(?P<table>[^)]+)\)',
        re.MULTILINE
    )

    QUERY_DELETE = re.compile(
        r'(?:diesel::)?delete\s*\(\s*(?P<table>[^)]+)\)',
        re.MULTILINE
    )

    # embed_migrations!() / run_pending_migrations
    MIGRATION_EMBED = re.compile(
        r'embed_migrations!\s*\((?P<path>[^)]*)\)',
        re.MULTILINE
    )

    MIGRATION_RUN = re.compile(
        r'run_pending_migrations|run_migrations|MigrationHarness',
    )

    # Connection types
    CONNECTION_TYPE = re.compile(
        r'(?P<type>PgConnection|MysqlConnection|SqliteConnection|AsyncPgConnection|AsyncMysqlConnection)',
    )

    # Pool types
    POOL_TYPE = re.compile(
        r'(?P<pool>r2d2::Pool|deadpool|bb8::Pool|mobc::Pool)',
    )

    # Associations: #[belongs_to(Parent)]
    ASSOCIATION = re.compile(
        r'#\[belongs_to\(\s*(?P<target>\w+)\s*(?:,\s*foreign_key\s*=\s*"?\w+"?)?\s*\)\]',
        re.MULTILINE
    )

    # Custom types: impl FromSqlRow / impl AsExpression / impl ToSql / impl FromSql
    CUSTOM_TYPE = re.compile(
        r'impl\s+(?:diesel::)?(?P<kind>FromSqlRow|AsExpression|ToSql|FromSql)\s*<[^>]*>\s*for\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Joins: .inner_join(...) or .left_join(...)
    JOIN_PATTERN = re.compile(
        r'\.(?P<kind>inner_join|left_join|right_join)\s*\(\s*(?P<table>\w+)',
        re.MULTILINE
    )

    VERSION_FEATURES = {
        '2.x': [r'diesel\s*=\s*"2', r'diesel_async', r'AsyncPgConnection', r'Selectable'],
        '1.x': [r'diesel\s*=\s*"1', r'QueryableByName'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> DieselParseResult:
        result = DieselParseResult(file_path=file_path)
        if not self.DIESEL_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.diesel_version = self._detect_version(content)
        result.tables = self._extract_tables(content, file_path)
        result.models = self._extract_models(content, file_path)
        result.queries = self._extract_queries(content, file_path)
        result.migrations = self._extract_migrations(content, file_path)
        result.connections = self._extract_connections(content, file_path)
        result.associations = self._extract_associations(content, file_path)
        result.custom_types = self._extract_custom_types(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_tables(self, content: str, file_path: str) -> List[DieselTableInfo]:
        tables = []
        for m in self.TABLE_MACRO.finditer(content):
            name = m.group('name')
            body = m.group('body') or ''
            columns = [c.group(1) for c in self.COLUMN_PATTERN.finditer(body)]
            line_num = content[:m.start()].count('\n') + 1
            tables.append(DieselTableInfo(
                name=name, columns=columns,
                file=file_path, line_number=line_num,
            ))
        return tables

    def _extract_models(self, content: str, file_path: str) -> List[DieselModelInfo]:
        models = []
        for m in self.DERIVE_MODEL.finditer(content):
            derives_str = m.group(1)
            derives = [d.strip() for d in derives_str.split(',')]
            table_name = m.group(2) or ''
            name = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            # If table_name not found in derive, check nearby
            if not table_name:
                nearby = content[max(0, m.start() - 200):m.start()]
                tn = self.TABLE_NAME_ATTR.search(nearby)
                if tn:
                    table_name = tn.group(1)

            models.append(DieselModelInfo(
                name=name, table_name=table_name,
                derives=derives, file=file_path, line_number=line_num,
            ))
        return models

    def _extract_queries(self, content: str, file_path: str) -> List[DieselQueryInfo]:
        queries = []

        for m in self.QUERY_SELECT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(DieselQueryInfo(
                kind=m.group('op'), table=m.group('table'),
                file=file_path, line_number=line_num,
            ))

        for m in self.QUERY_INSERT.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(DieselQueryInfo(
                kind='insert', table=m.group('table'),
                file=file_path, line_number=line_num,
            ))

        for m in self.QUERY_UPDATE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(DieselQueryInfo(
                kind='update', table=m.group('table').strip(),
                file=file_path, line_number=line_num,
            ))

        for m in self.QUERY_DELETE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(DieselQueryInfo(
                kind='delete', table=m.group('table').strip(),
                file=file_path, line_number=line_num,
            ))

        for m in self.JOIN_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            queries.append(DieselQueryInfo(
                kind=m.group('kind'), table=m.group('table'),
                file=file_path, line_number=line_num,
            ))

        return queries

    def _extract_migrations(self, content: str, file_path: str) -> List[DieselMigrationInfo]:
        migrations = []
        for m in self.MIGRATION_EMBED.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            migrations.append(DieselMigrationInfo(
                kind='embed_migrations', name=m.group('path').strip() or 'default',
                file=file_path, line_number=line_num,
            ))
        for m in self.MIGRATION_RUN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            migrations.append(DieselMigrationInfo(
                kind='run_pending', file=file_path, line_number=line_num,
            ))
        return migrations

    def _extract_connections(self, content: str, file_path: str) -> List[DieselConnectionInfo]:
        connections = []
        seen_backends = set()

        for m in self.CONNECTION_TYPE.finditer(content):
            ctype = m.group('type')
            backend = 'pg' if 'Pg' in ctype else ('mysql' if 'Mysql' in ctype else 'sqlite')
            if backend not in seen_backends:
                seen_backends.add(backend)
                line_num = content[:m.start()].count('\n') + 1

                pool = ""
                pm = self.POOL_TYPE.search(content)
                if pm:
                    pool = pm.group('pool').split('::')[0]

                connections.append(DieselConnectionInfo(
                    backend=backend, pool=pool,
                    file=file_path, line_number=line_num,
                ))

        return connections

    def _extract_associations(self, content: str, file_path: str) -> List[DieselAssociationInfo]:
        associations = []
        for m in self.ASSOCIATION.finditer(content):
            target = m.group('target')
            line_num = content[:m.start()].count('\n') + 1

            # Find the struct this is applied to
            struct_re = re.compile(r'(?:pub\s+)?struct\s+(\w+)', re.MULTILINE)
            after = content[m.end():m.end() + 200]
            sm = struct_re.search(after)
            model = sm.group(1) if sm else ''

            associations.append(DieselAssociationInfo(
                model=model, kind='belongs_to', target=target,
                file=file_path, line_number=line_num,
            ))
        return associations

    def _extract_custom_types(self, content: str, file_path: str) -> List[DieselCustomTypeInfo]:
        custom_types = []
        for m in self.CUSTOM_TYPE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            custom_types.append(DieselCustomTypeInfo(
                name=m.group('name'), kind=m.group('kind'),
                file=file_path, line_number=line_num,
            ))
        return custom_types
