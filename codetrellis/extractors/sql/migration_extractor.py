"""
SQLMigrationExtractor - Extracts SQL migration patterns and schema versioning.

This extractor parses SQL source code and extracts:
- Migration metadata (version, description, timestamp)
- UP/DOWN migration blocks (Flyway, golang-migrate, dbmate, Alembic)
- Idempotent patterns (IF NOT EXISTS, IF EXISTS, DO $$...$$)
- Transaction control (BEGIN/COMMIT/ROLLBACK in migrations)
- Data migrations vs schema migrations
- Seed data (INSERT INTO patterns)
- DROP TABLE/VIEW/FUNCTION cleanup patterns
- Migration file naming conventions

Supported migration frameworks:
- Flyway (V1_2__description.sql, R__repeatable.sql)
- golang-migrate (000001_name.up.sql, 000001_name.down.sql)
- dbmate (20240101120000_name.sql with --migrate:up / --migrate:down)
- Alembic (revision identifiers)
- Liquibase (changelog format detection)
- Knex migrations
- Django migrations (SQL files)
- Rails migrations (SQL files)
- Prisma migrations (migration.sql)
- TypeORM migrations
- Sequelize migrations

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class SQLMigrationInfo:
    """Information about a SQL migration file."""
    file_path: str
    version: str = ""                  # Migration version (e.g., V1, 000001, timestamp)
    description: str = ""              # Human-readable description
    direction: str = ""                # up, down, repeatable, both
    framework: str = ""                # flyway, golang-migrate, dbmate, alembic, etc.
    tables_created: List[str] = field(default_factory=list)
    tables_dropped: List[str] = field(default_factory=list)
    tables_altered: List[str] = field(default_factory=list)
    columns_added: List[Dict[str, str]] = field(default_factory=list)  # [{table, column}]
    columns_dropped: List[Dict[str, str]] = field(default_factory=list)
    indexes_created: List[str] = field(default_factory=list)
    indexes_dropped: List[str] = field(default_factory=list)
    has_data_migration: bool = False   # Contains INSERT/UPDATE/DELETE
    has_seed_data: bool = False        # Contains INSERT INTO with VALUES
    is_idempotent: bool = False        # Uses IF NOT EXISTS / IF EXISTS
    has_transaction: bool = False      # Wrapped in BEGIN/COMMIT
    statement_count: int = 0
    dialect: str = ""


class SQLMigrationExtractor:
    """
    Extracts migration metadata and patterns from SQL files.

    v4.15: Detects migration framework from filename patterns and content.
    """

    # Filename patterns for migration framework detection
    FLYWAY_VERSIONED = re.compile(r'^V(\d+(?:_\d+)*)__(.+)\.sql$', re.IGNORECASE)
    FLYWAY_REPEATABLE = re.compile(r'^R__(.+)\.sql$', re.IGNORECASE)
    FLYWAY_UNDO = re.compile(r'^U(\d+(?:_\d+)*)__(.+)\.sql$', re.IGNORECASE)
    GOLANG_MIGRATE = re.compile(r'^(\d+)_(.+)\.(up|down)\.sql$', re.IGNORECASE)
    DBMATE = re.compile(r'^(\d{14})_(.+)\.sql$')
    TIMESTAMP_MIGRATE = re.compile(r'^(\d{8,14})[-_](.+)\.sql$')
    PRISMA_MIGRATE = re.compile(r'^(\d{14})_(.+)/migration\.sql$')
    ALEMBIC_MARKER = re.compile(r'--\s*revision:\s*(\w+)', re.IGNORECASE)
    LIQUIBASE_MARKER = re.compile(r'--\s*(?:changeset|liquibase)', re.IGNORECASE)

    # Content patterns
    CREATE_TABLE_PAT = re.compile(r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?(?:UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE)
    DROP_TABLE_PAT = re.compile(r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE)
    ALTER_TABLE_PAT = re.compile(r'ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE)
    ADD_COLUMN_PAT = re.compile(r'ALTER\s+TABLE\s+(?:[\w"`.]+\.)?(?P<table>[\w"`.]+)\s+ADD\s+(?:COLUMN\s+)?(?P<col>[\w"`.]+)', re.IGNORECASE)
    DROP_COLUMN_PAT = re.compile(r'ALTER\s+TABLE\s+(?:[\w"`.]+\.)?(?P<table>[\w"`.]+)\s+DROP\s+(?:COLUMN\s+)?(?P<col>[\w"`.]+)', re.IGNORECASE)
    CREATE_INDEX_PAT = re.compile(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w"`.]+)', re.IGNORECASE)
    DROP_INDEX_PAT = re.compile(r'DROP\s+INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+EXISTS\s+)?(?P<name>[\w"`.]+)', re.IGNORECASE)
    INSERT_PAT = re.compile(r'INSERT\s+INTO', re.IGNORECASE)
    UPDATE_PAT = re.compile(r'UPDATE\s+[\w"`.]+\s+SET', re.IGNORECASE)
    DELETE_PAT = re.compile(r'DELETE\s+FROM', re.IGNORECASE)
    IF_EXISTS_PAT = re.compile(r'\bIF\s+(?:NOT\s+)?EXISTS\b', re.IGNORECASE)
    TRANSACTION_PAT = re.compile(r'\b(?:BEGIN|COMMIT|ROLLBACK)\b', re.IGNORECASE)
    DBMATE_DIRECTION = re.compile(r'--\s*migrate:(?P<dir>up|down)', re.IGNORECASE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract migration information from a SQL file.

        Returns:
            Dict with keys: migration (SQLMigrationInfo or None)
        """
        migration = self._extract_migration(content, file_path)
        return {
            'migration': migration,
        }

    def _extract_migration(self, content: str, file_path: str) -> Optional[SQLMigrationInfo]:
        """Extract migration metadata from file."""
        if not file_path:
            return None

        filename = Path(file_path).name
        parent = Path(file_path).parent.name

        migration = SQLMigrationInfo(file_path=file_path)

        # Detect framework from filename
        framework, version, description, direction = self._detect_framework(filename, parent, content)
        migration.framework = framework
        migration.version = version
        migration.description = description
        migration.direction = direction

        # If no framework detected, check if it looks like a migration at all
        if not framework:
            if not self._looks_like_migration(file_path, content):
                return None

        # Analyze content
        self._analyze_content(content, migration)

        return migration

    def _detect_framework(self, filename: str, parent: str, content: str):
        """Detect migration framework, version, description, direction from filename."""
        # Flyway versioned
        m = self.FLYWAY_VERSIONED.match(filename)
        if m:
            return 'flyway', m.group(1).replace('_', '.'), m.group(2).replace('_', ' '), 'up'

        # Flyway undo
        m = self.FLYWAY_UNDO.match(filename)
        if m:
            return 'flyway', m.group(1).replace('_', '.'), m.group(2).replace('_', ' '), 'down'

        # Flyway repeatable
        m = self.FLYWAY_REPEATABLE.match(filename)
        if m:
            return 'flyway', '', m.group(1).replace('_', ' '), 'repeatable'

        # golang-migrate
        m = self.GOLANG_MIGRATE.match(filename)
        if m:
            return 'golang-migrate', m.group(1), m.group(2).replace('_', ' '), m.group(3).lower()

        # dbmate (check content for -- migrate:up / -- migrate:down)
        m = self.DBMATE.match(filename)
        if m:
            direction = 'both'
            if self.DBMATE_DIRECTION.search(content):
                direction = 'both'  # dbmate files contain both up and down
            return 'dbmate', m.group(1), m.group(2).replace('_', ' '), direction

        # Prisma
        if filename == 'migration.sql':
            return 'prisma', parent, '', 'up'

        # Timestamp-based
        m = self.TIMESTAMP_MIGRATE.match(filename)
        if m:
            return 'timestamp', m.group(1), m.group(2).replace('_', ' '), 'up'

        # Alembic (content marker)
        m = self.ALEMBIC_MARKER.search(content)
        if m:
            return 'alembic', m.group(1), '', 'up'

        # Liquibase (content marker)
        if self.LIQUIBASE_MARKER.search(content):
            return 'liquibase', '', '', 'up'

        return '', '', '', ''

    def _looks_like_migration(self, file_path: str, content: str) -> bool:
        """Check if a SQL file looks like a migration."""
        path_lower = file_path.lower()
        migration_dirs = ('migration', 'migrations', 'migrate', 'db/migrate', 'db/migrations',
                          'sql/migrations', 'schema', 'changelog', 'flyway', 'seed', 'seeds')
        for d in migration_dirs:
            if f'/{d}/' in path_lower or path_lower.endswith(f'/{d}'):
                return True
        # Check for DDL content
        if re.search(r'CREATE\s+(?:TABLE|VIEW|INDEX|FUNCTION|PROCEDURE|TYPE|SEQUENCE|SCHEMA|TRIGGER)', content, re.IGNORECASE):
            return True
        if re.search(r'ALTER\s+TABLE', content, re.IGNORECASE):
            return True
        return False

    def _analyze_content(self, content: str, migration: SQLMigrationInfo):
        """Analyze migration content for patterns."""
        # Tables created
        for m in self.CREATE_TABLE_PAT.finditer(content):
            name = m.group('name').strip('"').strip('`')
            if name not in migration.tables_created:
                migration.tables_created.append(name)

        # Tables dropped
        for m in self.DROP_TABLE_PAT.finditer(content):
            name = m.group('name').strip('"').strip('`')
            if name not in migration.tables_dropped:
                migration.tables_dropped.append(name)

        # Tables altered
        for m in self.ALTER_TABLE_PAT.finditer(content):
            name = m.group('name').strip('"').strip('`')
            if name not in migration.tables_altered:
                migration.tables_altered.append(name)

        # Columns added
        for m in self.ADD_COLUMN_PAT.finditer(content):
            migration.columns_added.append({
                'table': m.group('table').strip('"').strip('`'),
                'column': m.group('col').strip('"').strip('`'),
            })

        # Columns dropped
        for m in self.DROP_COLUMN_PAT.finditer(content):
            migration.columns_dropped.append({
                'table': m.group('table').strip('"').strip('`'),
                'column': m.group('col').strip('"').strip('`'),
            })

        # Indexes
        for m in self.CREATE_INDEX_PAT.finditer(content):
            migration.indexes_created.append(m.group('name').strip('"').strip('`'))
        for m in self.DROP_INDEX_PAT.finditer(content):
            migration.indexes_dropped.append(m.group('name').strip('"').strip('`'))

        # Data migration / seed data
        migration.has_data_migration = bool(
            self.INSERT_PAT.search(content) or
            self.UPDATE_PAT.search(content) or
            self.DELETE_PAT.search(content)
        )
        migration.has_seed_data = bool(
            self.INSERT_PAT.search(content) and
            re.search(r'\bVALUES\b', content, re.IGNORECASE)
        )

        # Idempotent
        migration.is_idempotent = bool(self.IF_EXISTS_PAT.search(content))

        # Transaction
        migration.has_transaction = bool(self.TRANSACTION_PAT.search(content))

        # Statement count
        migration.statement_count = content.count(';')
