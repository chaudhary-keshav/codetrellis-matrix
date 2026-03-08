"""
EnhancedSQLParser v1.0 - Comprehensive SQL parser using all extractors.

This parser integrates all SQL extractors to provide complete
parsing of SQL source files across all major dialects.

Supports:
- ANSI SQL (SQL-92, SQL:1999, SQL:2003, SQL:2008, SQL:2011, SQL:2016, SQL:2023)
- PostgreSQL (9.x-17.x)
- MySQL / MariaDB (5.7-9.x / 10.x-11.x)
- SQL Server / T-SQL (2016-2025)
- Oracle / PL/SQL (12c-23ai)
- SQLite (3.x)

Extraction capabilities:
- Tables, views, materialized views, custom types, domains, sequences, schemas
- Stored procedures, functions, triggers, events, CTEs
- Indexes, constraints, partitions, foreign keys
- Roles, grants, RLS policies, default privileges
- Migration metadata and patterns (Flyway, golang-migrate, dbmate, Alembic, etc.)
- Dialect auto-detection from content markers

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all SQL extractors
from .extractors.sql import (
    SQLTypeExtractor, SQLTableInfo, SQLColumnInfo, SQLViewInfo,
    SQLMaterializedViewInfo, SQLCustomTypeInfo, SQLDomainInfo,
    SQLSequenceInfo, SQLSchemaInfo,
    SQLFunctionExtractor, SQLFunctionInfo, SQLStoredProcInfo,
    SQLTriggerInfo, SQLEventInfo, SQLParameterInfo,
    SQLIndexExtractor, SQLIndexInfo, SQLConstraintInfo,
    SQLPartitionInfo, SQLForeignKeyInfo,
    SQLSecurityExtractor, SQLRoleInfo, SQLGrantInfo, SQLRLSPolicyInfo,
    SQLMigrationExtractor, SQLMigrationInfo,
)


@dataclass
class SQLParseResult:
    """Complete parse result for a SQL file."""
    file_path: str
    file_type: str = "sql"

    # Dialect info
    dialect: str = ""                  # postgresql, mysql, sqlserver, oracle, sqlite, ansi
    dialect_version: str = ""

    # Schema objects
    tables: List[SQLTableInfo] = field(default_factory=list)
    views: List[SQLViewInfo] = field(default_factory=list)
    materialized_views: List[SQLMaterializedViewInfo] = field(default_factory=list)
    custom_types: List[SQLCustomTypeInfo] = field(default_factory=list)
    domains: List[SQLDomainInfo] = field(default_factory=list)
    sequences: List[SQLSequenceInfo] = field(default_factory=list)
    schemas: List[SQLSchemaInfo] = field(default_factory=list)

    # Programmability
    functions: List[SQLFunctionInfo] = field(default_factory=list)
    stored_procedures: List[SQLStoredProcInfo] = field(default_factory=list)
    triggers: List[SQLTriggerInfo] = field(default_factory=list)
    events: List[SQLEventInfo] = field(default_factory=list)

    # Structure
    indexes: List[SQLIndexInfo] = field(default_factory=list)
    constraints: List[SQLConstraintInfo] = field(default_factory=list)
    partitions: List[SQLPartitionInfo] = field(default_factory=list)
    foreign_keys: List[SQLForeignKeyInfo] = field(default_factory=list)

    # Security
    roles: List[SQLRoleInfo] = field(default_factory=list)
    grants: List[SQLGrantInfo] = field(default_factory=list)
    rls_policies: List[SQLRLSPolicyInfo] = field(default_factory=list)

    # Migration
    migration: Optional[SQLMigrationInfo] = None

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Referenced tables/objects
    comments: List[str] = field(default_factory=list)
    statement_count: int = 0
    is_migration: bool = False


class EnhancedSQLParser:
    """
    Enhanced SQL parser that uses all extractors for comprehensive parsing.

    Dialect detection supports:
    - PostgreSQL markers (serial, bigserial, jsonb, uuid, text, $$ blocks)
    - MySQL markers (AUTO_INCREMENT, ENGINE=, backtick quoting, TINYINT)
    - SQL Server markers (GO batches, NVARCHAR, sp_ prefixes, [bracket] quoting)
    - Oracle markers (NUMBER, VARCHAR2, PL/SQL blocks, NVL, SYSDATE)
    - SQLite markers (AUTOINCREMENT, PRAGMA, STRICT, WITHOUT ROWID)

    Migration framework detection:
    - Flyway (V1_2__desc.sql, R__repeatable.sql)
    - golang-migrate (000001_name.up.sql)
    - dbmate (-- migrate:up / -- migrate:down)
    - Alembic (-- revision: xxx)
    - Prisma (migration.sql)
    - Liquibase (-- changeset)
    - And more...
    """

    # Comment extraction
    BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
    LINE_COMMENT = re.compile(r'--\s*(.+)$', re.MULTILINE)

    # Dependency detection: references to tables in DML/DQL
    TABLE_REF_PATTERNS = [
        re.compile(r'\bFROM\s+(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE),
        re.compile(r'\bJOIN\s+(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE),
        re.compile(r'\bINTO\s+(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE),
        re.compile(r'\bUPDATE\s+(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE),
        re.compile(r'\bREFERENCES\s+(?:[\w"`.]+\.)?(?P<name>[\w"`.]+)', re.IGNORECASE),
    ]

    # Dialect-specific version markers
    PG_VERSION_MARKERS = {
        'GENERATED ALWAYS AS': '12',
        'JSON_TABLE': '17',
        'MERGE': '15',
        'MULTIRANGE': '14',
        'PUBLICATION': '10',
        'SUBSCRIPTION': '10',
        'STORED GENERATED': '12',
    }

    MYSQL_VERSION_MARKERS = {
        'INVISIBLE': '8.0',
        'JSON_TABLE': '8.0',
        'WINDOW': '8.0',
        'CTE': '8.0',
        'LATERAL': '8.0.14',
        'INTERSECT': '8.0.31',
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = SQLTypeExtractor()
        self.function_extractor = SQLFunctionExtractor()
        self.index_extractor = SQLIndexExtractor()
        self.security_extractor = SQLSecurityExtractor()
        self.migration_extractor = SQLMigrationExtractor()

    def parse(self, content: str, file_path: str = "") -> SQLParseResult:
        """
        Parse SQL source code and extract all information.

        Args:
            content: SQL source code content
            file_path: Path to source file

        Returns:
            SQLParseResult with all extracted information
        """
        result = SQLParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect dialect
        result.dialect = self._detect_dialect(content)
        result.dialect_version = self._detect_dialect_version(content, result.dialect)

        # Extract comments
        result.comments = self._extract_comments(content)

        # Count statements
        result.statement_count = self._count_statements(content)

        # Extract dependencies (referenced tables)
        result.dependencies = self._extract_dependencies(content)

        # Detect frameworks / tools
        result.detected_frameworks = self._detect_frameworks(content, file_path)

        # ── Type extraction (tables, views, types, etc.) ──
        type_result = self.type_extractor.extract(content, file_path)
        result.tables = type_result.get('tables', [])
        result.views = type_result.get('views', [])
        result.materialized_views = type_result.get('materialized_views', [])
        result.custom_types = type_result.get('custom_types', [])
        result.domains = type_result.get('domains', [])
        result.sequences = type_result.get('sequences', [])
        result.schemas = type_result.get('schemas', [])

        # ── Function extraction (functions, procs, triggers, events) ──
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.stored_procedures = func_result.get('procedures', [])
        result.triggers = func_result.get('triggers', [])
        result.events = func_result.get('events', [])

        # ── Index / constraint extraction ──
        index_result = self.index_extractor.extract(content, file_path)
        result.indexes = index_result.get('indexes', [])
        result.constraints = index_result.get('constraints', [])
        result.partitions = index_result.get('partitions', [])
        result.foreign_keys = index_result.get('foreign_keys', [])

        # ── Security extraction ──
        sec_result = self.security_extractor.extract(content, file_path)
        result.roles = sec_result.get('roles', [])
        result.grants = sec_result.get('grants', [])
        result.rls_policies = sec_result.get('rls_policies', [])

        # ── Migration extraction ──
        mig_result = self.migration_extractor.extract(content, file_path)
        result.migration = mig_result.get('migration')
        result.is_migration = result.migration is not None

        return result

    def _detect_dialect(self, content: str) -> str:
        """
        Detect SQL dialect from content markers.

        Uses a scoring system — highest score wins.
        """
        scores: Dict[str, int] = {
            'postgresql': 0,
            'mysql': 0,
            'sqlserver': 0,
            'oracle': 0,
            'sqlite': 0,
        }

        upper = content.upper()

        # ── PostgreSQL markers ──
        pg_markers = [
            'SERIAL', 'BIGSERIAL', 'SMALLSERIAL', 'JSONB', '::',
            'TEXT', 'BYTEA', 'TSQUERY', 'TSVECTOR', 'CIDR', 'INET', 'MACADDR',
            'UUID', 'HSTORE', 'ARRAY[', 'DATERANGE', 'INT4RANGE', 'NUMRANGE',
            'REGCLASS', 'OID', 'RETURNING', '$$', 'RAISE NOTICE', 'RAISE EXCEPTION',
            'PERFORM', 'ILIKE', 'LIMIT ALL', 'COPY ', 'LISTEN ', 'NOTIFY ',
            'CREATE EXTENSION', 'ENABLE ROW LEVEL SECURITY',
        ]
        for marker in pg_markers:
            if marker in upper:
                scores['postgresql'] += 2

        # ── MySQL / MariaDB markers ──
        mysql_markers = [
            'AUTO_INCREMENT', 'ENGINE=', 'CHARSET=', 'COLLATE=',
            'TINYINT', 'MEDIUMINT', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT',
            'TINYBLOB', 'MEDIUMBLOB', 'LONGBLOB', 'UNSIGNED',
            'ENUM(', 'SET(', 'ON DUPLICATE KEY', 'SHOW TABLES',
            'DELIMITER', 'DEFINER=', 'SQL SECURITY',
        ]
        for marker in mysql_markers:
            if marker in upper:
                scores['mysql'] += 2
        # Backtick quoting
        if '`' in content:
            scores['mysql'] += 3

        # ── SQL Server / T-SQL markers ──
        tsql_markers = [
            'NVARCHAR', 'NCHAR', 'NTEXT', 'MONEY', 'SMALLMONEY',
            'DATETIME2', 'DATETIMEOFFSET', 'UNIQUEIDENTIFIER',
            'BIT', 'IMAGE', 'SQL_VARIANT', 'HIERARCHYID', 'GEOGRAPHY',
            'GEOMETRY', 'IDENTITY(', 'CLUSTERED', 'NONCLUSTERED',
            'NOLOCK', 'WITH (NOLOCK)', 'OPTION (RECOMPILE)',
            'TOP ', 'DECLARE @', 'SET @', 'PRINT ', 'RAISERROR',
            'TRY_CAST', 'TRY_CONVERT', 'STRING_AGG', 'OPENJSON',
        ]
        for marker in tsql_markers:
            if marker in upper:
                scores['sqlserver'] += 2
        # GO batch separator
        if re.search(r'^\s*GO\s*$', content, re.MULTILINE | re.IGNORECASE):
            scores['sqlserver'] += 5
        # Bracket quoting
        if re.search(r'\[[\w\s]+\]', content):
            scores['sqlserver'] += 2
        # sp_ prefix
        if 'SP_' in upper or 'XP_' in upper:
            scores['sqlserver'] += 2

        # ── Oracle / PL/SQL markers ──
        oracle_markers = [
            'NUMBER(', 'VARCHAR2', 'RAW(', 'LONG RAW', 'CLOB', 'NCLOB',
            'BFILE', 'ROWID', 'UROWID', 'BINARY_FLOAT', 'BINARY_DOUBLE',
            'NVL(', 'NVL2(', 'DECODE(', 'SYSDATE', 'SYSTIMESTAMP',
            'DBMS_', 'UTL_',
            'CONNECT BY',
            'BULK COLLECT', 'FORALL', 'PIPELINED',
            '%ROWTYPE', 'EXCEPTION WHEN',
        ]
        for marker in oracle_markers:
            if marker in upper:
                scores['oracle'] += 2
        # More specific Oracle patterns (word-boundary)
        if re.search(r'\bDBA_\w+', upper):
            scores['oracle'] += 2
        if re.search(r'\bUSER_TABLES\b|\bUSER_TAB_COLUMNS\b|\bUSER_OBJECTS\b', upper):
            scores['oracle'] += 2
        if re.search(r'\bALL_TABLES\b|\bALL_TAB_COLUMNS\b', upper):
            scores['oracle'] += 2
        if re.search(r'%TYPE\b', upper):
            scores['oracle'] += 2
        # PL/SQL blocks (CREATE ... IS/AS BEGIN — not $$ body)
        if re.search(r'\b(?:IS|AS)\s+BEGIN\b', upper) and '$$' not in content:
            scores['oracle'] += 3

        # ── SQLite markers ──
        sqlite_markers = [
            'AUTOINCREMENT', 'PRAGMA ', 'STRICT', 'WITHOUT ROWID',
            'REPLACE INTO', 'INSERT OR REPLACE', 'INSERT OR IGNORE',
            'INSERT OR ABORT', 'INSERT OR ROLLBACK', 'INSERT OR FAIL',
            'GLOB ', 'TYPEOF(', 'LAST_INSERT_ROWID',
        ]
        for marker in sqlite_markers:
            if marker in upper:
                scores['sqlite'] += 2

        # Get highest scoring dialect
        max_score = max(scores.values())
        if max_score == 0:
            return 'ansi'

        # Return the dialect with highest score
        for dialect, score in scores.items():
            if score == max_score:
                return dialect

        return 'ansi'

    def _detect_dialect_version(self, content: str, dialect: str) -> str:
        """Detect specific dialect version from content markers."""
        upper = content.upper()

        if dialect == 'postgresql':
            max_ver = '9'
            for marker, ver in self.PG_VERSION_MARKERS.items():
                if marker in upper:
                    if ver > max_ver:
                        max_ver = ver
            return f'{max_ver}+'

        if dialect == 'mysql':
            max_ver = '5.7'
            for marker, ver in self.MYSQL_VERSION_MARKERS.items():
                if marker in upper:
                    if ver > max_ver:
                        max_ver = ver
            return f'{max_ver}+'

        return ''

    def _extract_comments(self, content: str) -> List[str]:
        """Extract meaningful comments from SQL file."""
        comments = []

        # Line comments
        for m in self.LINE_COMMENT.finditer(content):
            comment = m.group(1).strip()
            # Skip migration markers and trivial comments
            if comment and not comment.startswith('migrate:') and len(comment) > 3:
                comments.append(comment)

        # Block comments (first one typically has file description)
        for m in self.BLOCK_COMMENT.finditer(content):
            text = m.group(0)[2:-2].strip()
            if text and len(text) > 10:
                comments.append(text)

        return comments[:20]  # Cap at 20 comments

    def _count_statements(self, content: str) -> int:
        """Count SQL statements (semicolons outside of string literals / $$ blocks)."""
        # Simple count — good enough for most cases
        # Remove string literals
        cleaned = re.sub(r"'[^']*'", "''", content)
        # Remove $$ blocks
        cleaned = re.sub(r'\$\$.*?\$\$', '', cleaned, flags=re.DOTALL)
        return cleaned.count(';')

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract referenced table/object names from SQL content."""
        deps: Set[str] = set()
        # Remove string literals
        cleaned = re.sub(r"'[^']*'", "''", content)

        sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'SET', 'VALUES',
            'AND', 'OR', 'NOT', 'NULL', 'DEFAULT', 'INDEX', 'TABLE', 'VIEW',
            'FUNCTION', 'PROCEDURE', 'TRIGGER', 'SCHEMA', 'DATABASE',
            'IF', 'EXISTS', 'CASCADE', 'RESTRICT', 'ON', 'IN', 'AS',
            'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT',
            'CHECK', 'UNIQUE', 'CREATE', 'DROP', 'ALTER', 'ADD', 'COLUMN',
            'BEGIN', 'END', 'COMMIT', 'ROLLBACK', 'GRANT', 'REVOKE',
            'TRUE', 'FALSE', 'DUAL', 'TEMP', 'TEMPORARY',
        }

        for pattern in self.TABLE_REF_PATTERNS:
            for m in pattern.finditer(cleaned):
                name = m.group('name').strip('"').strip('`').strip('[').rstrip(']')
                if name.upper() not in sql_keywords and not name.startswith('@'):
                    deps.add(name)

        return sorted(deps)

    def _detect_frameworks(self, content: str, file_path: str) -> List[str]:
        """Detect SQL-related frameworks/tools from content and file path."""
        frameworks = []
        upper = content.upper()
        path_lower = file_path.lower() if file_path else ""

        # Migration frameworks (from path)
        if 'flyway' in path_lower:
            frameworks.append('flyway')
        if 'alembic' in path_lower:
            frameworks.append('alembic')
        if 'liquibase' in path_lower:
            frameworks.append('liquibase')
        if 'knex' in path_lower:
            frameworks.append('knex')
        if 'prisma' in path_lower:
            frameworks.append('prisma')
        if 'typeorm' in path_lower:
            frameworks.append('typeorm')
        if 'sequelize' in path_lower:
            frameworks.append('sequelize')

        # Extension features
        if 'CREATE EXTENSION' in upper:
            ext_match = re.findall(r'CREATE\s+EXTENSION\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?([\w]+)', content, re.IGNORECASE)
            for ext in ext_match:
                frameworks.append(f'pg-ext:{ext}')

        # PostGIS
        if 'GEOMETRY(' in upper or 'GEOGRAPHY(' in upper or 'ST_' in upper:
            if 'postgis' not in frameworks:
                frameworks.append('postgis')

        # TimescaleDB
        if 'CREATE_HYPERTABLE' in upper or 'HYPERTABLE' in upper:
            frameworks.append('timescaledb')

        # pg_cron
        if 'CRON.SCHEDULE' in upper:
            frameworks.append('pg_cron')

        # pgvector
        if 'VECTOR(' in upper or 'IVFFLAT' in upper or 'HNSW' in upper:
            frameworks.append('pgvector')

        return frameworks

    @staticmethod
    def detect_sql_project_type(files: List[str]) -> Dict[str, Any]:
        """
        Detect SQL project type from a list of file paths.

        Identifies:
        - Migration-heavy projects
        - Schema-definition projects
        - Stored-procedure-heavy projects
        - Mixed projects

        Args:
            files: List of SQL file paths in the project

        Returns:
            Dict with project_type, migration_framework, file_stats
        """
        result: Dict[str, Any] = {
            'project_type': 'mixed',
            'migration_framework': '',
            'migration_count': 0,
            'schema_count': 0,
            'procedure_count': 0,
            'file_count': len(files),
        }

        migration_count = 0
        schema_count = 0
        proc_count = 0

        flyway_count = 0
        golang_migrate_count = 0
        dbmate_count = 0

        for f in files:
            filename = Path(f).name.lower()
            path_lower = f.lower()

            # Migration detection
            if re.match(r'^v\d+', filename, re.IGNORECASE):
                flyway_count += 1
                migration_count += 1
            elif re.match(r'^\d+_.+\.(up|down)\.sql$', filename):
                golang_migrate_count += 1
                migration_count += 1
            elif re.match(r'^\d{14}_', filename):
                dbmate_count += 1
                migration_count += 1
            elif 'migration' in path_lower:
                migration_count += 1

            # Schema files
            if any(kw in filename for kw in ['schema', 'ddl', 'create', 'table', 'init']):
                schema_count += 1

            # Procedure files
            if any(kw in filename for kw in ['procedure', 'function', 'proc', 'trigger', 'plpgsql', 'plsql']):
                proc_count += 1

        result['migration_count'] = migration_count
        result['schema_count'] = schema_count
        result['procedure_count'] = proc_count

        # Determine framework
        fw_counts = {'flyway': flyway_count, 'golang-migrate': golang_migrate_count, 'dbmate': dbmate_count}
        max_fw = max(fw_counts, key=fw_counts.get)
        if fw_counts[max_fw] > 0:
            result['migration_framework'] = max_fw

        # Determine project type
        total = len(files)
        if total > 0:
            migration_ratio = migration_count / total
            proc_ratio = proc_count / total
            if migration_ratio > 0.6:
                result['project_type'] = 'migration-heavy'
            elif proc_ratio > 0.4:
                result['project_type'] = 'procedure-heavy'
            elif schema_count > proc_count and schema_count > migration_count:
                result['project_type'] = 'schema-definition'
            else:
                result['project_type'] = 'mixed'

        return result
