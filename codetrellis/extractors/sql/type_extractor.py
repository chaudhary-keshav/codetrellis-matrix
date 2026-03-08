"""
SQLTypeExtractor - Extracts SQL DDL definitions across all major dialects.

This extractor parses SQL source code and extracts:
- CREATE TABLE with columns, data types, defaults, constraints
- CREATE VIEW / CREATE OR REPLACE VIEW
- CREATE MATERIALIZED VIEW (PostgreSQL, Oracle, SQL Server)
- CREATE TYPE / CREATE DOMAIN (PostgreSQL, Oracle, SQL Server UDTs)
- CREATE SEQUENCE (PostgreSQL, Oracle, SQL Server)
- CREATE SCHEMA declarations
- ALTER TABLE statements (add/modify/drop columns, rename)
- COMMENT ON statements (PostgreSQL, Oracle)
- Partitioned tables (PARTITION BY range/list/hash)
- Temporary tables (TEMPORARY, GLOBAL TEMPORARY, LOCAL TEMPORARY)
- Column-level and table-level constraints inline

Supported SQL dialects:
- ANSI SQL (SQL:2023, SQL:2016, SQL:2011, SQL:2008, SQL:2003, SQL:1999, SQL-92)
- PostgreSQL (9.x - 17.x) with JSONB, ARRAY, GENERATED, IDENTITY, EXCLUDE
- MySQL / MariaDB (5.7 - 9.x / 10.x - 11.x) with ENGINE, CHARSET, AUTO_INCREMENT
- SQL Server / T-SQL (2016 - 2025) with IDENTITY, NVARCHAR, FILESTREAM
- Oracle / PL/SQL (12c - 23ai) with NUMBER, VARCHAR2, CLOB, BLOB
- SQLite (3.x) with AUTOINCREMENT, WITHOUT ROWID, STRICT

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class SQLColumnInfo:
    """Information about a SQL table column."""
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_unique: bool = False
    default_value: Optional[str] = None
    check_constraint: Optional[str] = None
    comment: Optional[str] = None
    is_identity: bool = False       # IDENTITY / GENERATED ALWAYS
    is_auto_increment: bool = False  # AUTO_INCREMENT (MySQL)
    is_serial: bool = False          # SERIAL / BIGSERIAL (PostgreSQL)
    references: Optional[str] = None  # FK table.column
    collation: Optional[str] = None
    is_generated: bool = False       # GENERATED ALWAYS AS (expr) STORED/VIRTUAL
    generation_expr: Optional[str] = None


@dataclass
class SQLTableInfo:
    """Information about a SQL table."""
    name: str
    schema_name: str = ""
    columns: List[SQLColumnInfo] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    unique_constraints: List[Dict[str, Any]] = field(default_factory=list)
    check_constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)  # Named inline indexes
    dialect: str = ""               # postgresql, mysql, sqlserver, oracle, sqlite
    engine: str = ""                # MySQL engine (InnoDB, MyISAM, etc.)
    charset: str = ""               # MySQL charset
    collation: str = ""             # MySQL/PostgreSQL collation
    tablespace: str = ""            # Oracle/PostgreSQL tablespace
    is_temporary: bool = False
    is_unlogged: bool = False       # PostgreSQL UNLOGGED
    is_partitioned: bool = False
    partition_by: str = ""          # RANGE, LIST, HASH
    partition_columns: List[str] = field(default_factory=list)
    inherits: List[str] = field(default_factory=list)  # PostgreSQL INHERITS
    like_table: str = ""            # CREATE TABLE ... LIKE other_table
    comment: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class SQLViewInfo:
    """Information about a SQL view."""
    name: str
    schema_name: str = ""
    query: str = ""                  # Truncated SELECT body
    columns: List[str] = field(default_factory=list)  # Explicit column list
    is_replace: bool = False         # CREATE OR REPLACE
    is_recursive: bool = False       # WITH RECURSIVE
    with_check_option: bool = False
    security_definer: bool = False   # PostgreSQL SECURITY DEFINER
    dependencies: List[str] = field(default_factory=list)  # Referenced tables
    dialect: str = ""
    comment: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class SQLMaterializedViewInfo:
    """Information about a materialized view."""
    name: str
    schema_name: str = ""
    query: str = ""
    columns: List[str] = field(default_factory=list)
    storage_params: Dict[str, str] = field(default_factory=dict)
    refresh_mode: str = ""           # ON DEMAND, ON COMMIT, FAST, COMPLETE
    is_populated: bool = True        # WITH DATA / WITH NO DATA
    dependencies: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLCustomTypeInfo:
    """Information about a custom type (PostgreSQL CREATE TYPE, Oracle OBJECT TYPE, etc.)."""
    name: str
    schema_name: str = ""
    kind: str = ""                   # enum, composite, range, base, object
    values: List[str] = field(default_factory=list)        # Enum values
    attributes: List[Dict[str, str]] = field(default_factory=list)  # Composite fields
    base_type: str = ""              # For range/base types
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLDomainInfo:
    """Information about a SQL domain (PostgreSQL, SQL Server)."""
    name: str
    schema_name: str = ""
    base_type: str = ""
    default_value: Optional[str] = None
    check_constraint: Optional[str] = None
    is_nullable: bool = True
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLSequenceInfo:
    """Information about a SQL sequence."""
    name: str
    schema_name: str = ""
    start_value: Optional[int] = None
    increment: int = 1
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    cache_size: int = 1
    cycle: bool = False
    owned_by: Optional[str] = None   # PostgreSQL OWNED BY table.column
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLSchemaInfo:
    """Information about a SQL schema declaration."""
    name: str
    owner: str = ""
    authorization: str = ""
    dialect: str = ""
    file: str = ""
    line_number: int = 0


class SQLTypeExtractor:
    """
    Extracts SQL DDL type definitions from source code.

    Handles all major SQL dialects:
    - ANSI SQL standard CREATE TABLE/VIEW/SEQUENCE/DOMAIN/TYPE
    - PostgreSQL extensions: UNLOGGED, INHERITS, PARTITION BY, GENERATED, JSONB, arrays
    - MySQL extensions: ENGINE, AUTO_INCREMENT, CHARSET, COLLATE
    - SQL Server extensions: IDENTITY, NVARCHAR(MAX), FILESTREAM, computed columns
    - Oracle extensions: NUMBER, VARCHAR2, CLOB, BLOB, OBJECT TYPE, nested tables
    - SQLite extensions: AUTOINCREMENT, WITHOUT ROWID, STRICT

    v4.15: Uses regex-based extraction with dialect auto-detection.
    """

    # Dialect detection patterns
    PG_MARKERS = re.compile(
        r'\b(?:SERIAL|BIGSERIAL|SMALLSERIAL|JSONB|JSONPATH|TEXT\b|BYTEA|CIDR|INET|MACADDR|'
        r'UUID|TSRANGE|DATERANGE|INT4RANGE|INT8RANGE|NUMRANGE|HSTORE|'
        r'REGCLASS|OID|UNLOGGED|INHERITS|WITH\s+OIDS|EXCLUDE\s+USING|'
        r'GENERATED\s+ALWAYS|IDENTITY|STORED|CREATE\s+EXTENSION|'
        r'pg_catalog|information_schema|pg_|'
        r'RAISE\s+(?:NOTICE|EXCEPTION|WARNING)|RETURNS?\s+(?:SETOF|TABLE)|'
        r'\$\$|LANGUAGE\s+plpgsql)\b',
        re.IGNORECASE
    )
    MYSQL_MARKERS = re.compile(
        r'\b(?:AUTO_INCREMENT|ENGINE\s*=|DEFAULT\s+CHARSET|COLLATE\s*=|'
        r'UNSIGNED|TINYINT|MEDIUMINT|TINYBLOB|MEDIUMBLOB|LONGBLOB|'
        r'TINYTEXT|MEDIUMTEXT|LONGTEXT|ENUM\s*\(|SET\s*\(|'
        r'ON\s+UPDATE\s+CURRENT_TIMESTAMP|IF\s+NOT\s+EXISTS|'
        r'DELIMITER|DEFINER\s*=|ALGORITHM\s*=|SQL_MODE)\b',
        re.IGNORECASE
    )
    SQLSERVER_MARKERS = re.compile(
        r'\b(?:NVARCHAR|NCHAR|NTEXT|UNIQUEIDENTIFIER|DATETIME2|DATETIMEOFFSET|'
        r'HIERARCHYID|GEOGRAPHY|GEOMETRY|SQL_VARIANT|MONEY|SMALLMONEY|'
        r'IDENTITY\s*\(\s*\d|GO\s*$|EXEC(?:UTE)?\s|sp_|xp_|sys\.|'
        r'FILESTREAM|ROWGUIDCOL|INCLUDE\s*\(|CLUSTERED|NONCLUSTERED|'
        r'WITH\s*\(\s*PAD_INDEX|FILLFACTOR|'
        r'BEGIN\s+TRY|END\s+TRY|BEGIN\s+CATCH|END\s+CATCH|'
        r'@@\w+|PRINT\s|RAISERROR|THROW\b)\b',
        re.IGNORECASE | re.MULTILINE
    )
    ORACLE_MARKERS = re.compile(
        r'\b(?:VARCHAR2|NUMBER\s*\(|CLOB|BLOB|NCLOB|BFILE|RAW\s*\(|'
        r'LONG\s+RAW|ROWID|UROWID|BINARY_FLOAT|BINARY_DOUBLE|'
        r'TABLESPACE|PCTFREE|INITRANS|STORAGE\s*\(|'
        r'DBMS_|UTL_|SYS\.|DBA_|ALL_|USER_|V\$|'
        r'PLS_INTEGER|BINARY_INTEGER|EXCEPTION\s+WHEN|'
        r'PRAGMA\s+AUTONOMOUS_TRANSACTION|BULK\s+COLLECT|FORALL\b)\b',
        re.IGNORECASE
    )
    SQLITE_MARKERS = re.compile(
        r'\b(?:AUTOINCREMENT|WITHOUT\s+ROWID|STRICT|'
        r'sqlite_master|sqlite_sequence|'
        r'ATTACH\s+DATABASE|PRAGMA\s+\w+)\b',
        re.IGNORECASE
    )

    # CREATE TABLE pattern — matches header only; body is extracted via balanced-paren scan
    CREATE_TABLE_HEADER = re.compile(
        r'CREATE\s+'
        r'(?P<temporary>(?:GLOBAL\s+|LOCAL\s+)?TEMP(?:ORARY)?\s+)?'
        r'(?P<unlogged>UNLOGGED\s+)?'
        r'TABLE\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"``\[\].]+\.)?'
        r'(?P<name>[\w"``\[\].]+)\s*'
        r'(?=\()',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE VIEW pattern
    CREATE_VIEW = re.compile(
        r'CREATE\s+'
        r'(?P<replace>OR\s+REPLACE\s+)?'
        r'(?P<recursive>RECURSIVE\s+)?'
        r'(?P<mat>MATERIALIZED\s+)?'
        r'VIEW\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s*'
        r'(?:\((?P<cols>[^)]+)\)\s*)?'
        r'(?:WITH\s*\([^)]*\)\s*)?'
        r'AS\s+(?P<query>.+?)(?:WITH\s+(?:CASCADED\s+|LOCAL\s+)?CHECK\s+OPTION)?'
        r'\s*;',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE MATERIALIZED VIEW (separate pattern for PostgreSQL/Oracle specifics)
    CREATE_MATVIEW = re.compile(
        r'CREATE\s+MATERIALIZED\s+VIEW\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s*'
        r'(?:\((?P<cols>[^)]+)\)\s*)?'
        r'(?:(?:TABLESPACE|USING|WITH)\s+[^AS]+)?\s*'
        r'AS\s+(?P<query>.+?)'
        r'(?:\s+WITH\s+(?P<data>NO\s+)?DATA)?'
        r'\s*;',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE TYPE (PostgreSQL enum/composite/range, Oracle OBJECT)
    CREATE_TYPE = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?TYPE\s+'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'(?:AS\s+(?P<kind>ENUM|OBJECT|RANGE|TABLE)\s*)?'
        r'(?:AS\s+)?'
        r'(?:\(\s*(?P<body>[^;]+?)\s*\))?\s*;',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE DOMAIN (PostgreSQL / SQL standard)
    CREATE_DOMAIN = re.compile(
        r'CREATE\s+DOMAIN\s+'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'(?:AS\s+)?(?P<type>\w[\w()\s,]*?)'
        r'(?:\s+DEFAULT\s+(?P<default>[^;]+?))?'
        r'(?:\s+(?:NOT\s+NULL|NULL))?'
        r'(?:\s+(?:CONSTRAINT\s+\w+\s+)?CHECK\s*\((?P<check>[^;]+?)\))?'
        r'\s*;',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE SEQUENCE
    CREATE_SEQUENCE = re.compile(
        r'CREATE\s+SEQUENCE\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)'
        r'(?P<opts>[^;]*);',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE SCHEMA
    CREATE_SCHEMA = re.compile(
        r'CREATE\s+SCHEMA\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<name>[\w"`.]+)'
        r'(?:\s+AUTHORIZATION\s+(?P<auth>[\w"`.]+))?',
        re.IGNORECASE
    )

    # ALTER TABLE ... ADD COLUMN / MODIFY / DROP COLUMN
    ALTER_TABLE = re.compile(
        r'ALTER\s+TABLE\s+'
        r'(?:IF\s+EXISTS\s+)?'
        r'(?:ONLY\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'(?P<action>ADD(?:\s+COLUMN)?|DROP(?:\s+COLUMN)?|ALTER(?:\s+COLUMN)?|'
        r'MODIFY(?:\s+COLUMN)?|RENAME(?:\s+COLUMN)?|'
        r'ADD\s+CONSTRAINT|DROP\s+CONSTRAINT|'
        r'ADD\s+(?:PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK|INDEX))\s+'
        r'(?P<detail>[^;]+);',
        re.IGNORECASE | re.DOTALL
    )

    # COMMENT ON (PostgreSQL, Oracle)
    COMMENT_ON = re.compile(
        r"COMMENT\s+ON\s+(?P<obj_type>TABLE|COLUMN|VIEW|FUNCTION|SCHEMA|TYPE|INDEX|SEQUENCE)\s+"
        r"(?P<obj_name>[\w\"`.]+(?:\.[\w\"`.]+)*)\s+"
        r"IS\s+'(?P<comment>[^']+)'",
        re.IGNORECASE
    )

    # Column parser — handles inline constraints
    COLUMN_PATTERN = re.compile(
        r'^\s*(?P<name>[\w"`]+)\s+'
        r'(?P<type>[\w()\s,]+?)'
        r'(?:\s+(?P<constraints>.+))?\s*$',
        re.IGNORECASE
    )

    # Table-level constraint patterns
    PK_CONSTRAINT = re.compile(
        r'(?:CONSTRAINT\s+[\w"`.]+\s+)?PRIMARY\s+KEY\s*\(\s*(?P<cols>[^)]+)\)',
        re.IGNORECASE
    )
    FK_CONSTRAINT = re.compile(
        r'(?:CONSTRAINT\s+(?P<name>[\w"`.]+)\s+)?FOREIGN\s+KEY\s*\(\s*(?P<cols>[^)]+)\s*\)\s*'
        r'REFERENCES\s+(?P<ref_table>[\w"`.]+(?:\.[\w"`.]+)?)\s*\(\s*(?P<ref_cols>[^)]+)\s*\)'
        r'(?:\s+ON\s+DELETE\s+(?P<on_delete>\w+(?:\s+\w+)?))?'
        r'(?:\s+ON\s+UPDATE\s+(?P<on_update>\w+(?:\s+\w+)?))?',
        re.IGNORECASE
    )
    UNIQUE_CONSTRAINT = re.compile(
        r'(?:CONSTRAINT\s+(?P<name>[\w"`.]+)\s+)?UNIQUE\s*\(\s*(?P<cols>[^)]+)\)',
        re.IGNORECASE
    )
    CHECK_CONSTRAINT = re.compile(
        r'(?:CONSTRAINT\s+(?P<name>[\w"`.]+)\s+)?CHECK\s*\(\s*(?P<expr>[^)]+)\)',
        re.IGNORECASE
    )

    # Partition pattern (PostgreSQL, MySQL, Oracle)
    PARTITION_BY = re.compile(
        r'PARTITION\s+BY\s+(?P<strategy>RANGE|LIST|HASH|KEY)\s*\(\s*(?P<cols>[^)]+)\)',
        re.IGNORECASE
    )

    # MySQL table options
    MYSQL_OPTIONS = re.compile(
        r'(?:ENGINE\s*=\s*(?P<engine>\w+))|'
        r'(?:DEFAULT\s+CHARSET\s*=\s*(?P<charset>\w+))|'
        r'(?:COLLATE\s*=\s*(?P<collation>\w+))|'
        r'(?:AUTO_INCREMENT\s*=\s*(?P<auto_inc>\d+))|'
        r'(?:COMMENT\s*=\s*\'(?P<comment>[^\']+)\')',
        re.IGNORECASE
    )

    def __init__(self):
        self._comments: Dict[str, str] = {}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all DDL type definitions from SQL source code.

        Args:
            content: SQL source code
            file_path: Path to source file

        Returns:
            Dict with keys: tables, views, materialized_views, custom_types,
                           domains, sequences, schemas, alter_statements
        """
        dialect = self._detect_dialect(content)

        # Extract COMMENT ON statements first for annotation
        self._comments = {}
        for m in self.COMMENT_ON.finditer(content):
            key = f"{m.group('obj_type').lower()}:{m.group('obj_name')}"
            self._comments[key] = m.group('comment')

        tables = self._extract_tables(content, file_path, dialect)
        views = self._extract_views(content, file_path, dialect)
        mat_views = self._extract_materialized_views(content, file_path, dialect)
        custom_types = self._extract_custom_types(content, file_path, dialect)
        domains = self._extract_domains(content, file_path, dialect)
        sequences = self._extract_sequences(content, file_path, dialect)
        schemas = self._extract_schemas(content, file_path, dialect)
        alter_stmts = self._extract_alter_statements(content, file_path, dialect)

        return {
            'tables': tables,
            'views': views,
            'materialized_views': mat_views,
            'custom_types': custom_types,
            'domains': domains,
            'sequences': sequences,
            'schemas': schemas,
            'alter_statements': alter_stmts,
            'dialect': dialect,
        }

    def _detect_dialect(self, content: str) -> str:
        """Auto-detect SQL dialect from content markers."""
        scores = {
            'postgresql': len(self.PG_MARKERS.findall(content)),
            'mysql': len(self.MYSQL_MARKERS.findall(content)),
            'sqlserver': len(self.SQLSERVER_MARKERS.findall(content)),
            'oracle': len(self.ORACLE_MARKERS.findall(content)),
            'sqlite': len(self.SQLITE_MARKERS.findall(content)),
        }
        if max(scores.values()) == 0:
            return 'ansi'
        return max(scores, key=scores.get)

    def _clean_name(self, name: str) -> str:
        """Remove quoting characters from identifiers."""
        if not name:
            return name
        return name.strip().strip('"').strip('`').strip('[').strip(']').strip('.')

    def _extract_balanced_parens(self, content: str, start: int) -> str:
        """Extract content between balanced parentheses starting at position start.
        
        Args:
            content: Full SQL source
            start: Position of opening '('
            
        Returns:
            String between outermost parentheses (excluding them), or '' if unbalanced.
        """
        if start >= len(content) or content[start] != '(':
            return ''
        depth = 0
        i = start
        while i < len(content):
            ch = content[i]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    return content[start + 1:i].strip()
            elif ch == "'" or ch == '"':
                # Skip quoted strings to avoid counting parens inside them
                quote = ch
                i += 1
                while i < len(content) and content[i] != quote:
                    if content[i] == '\\':
                        i += 1  # skip escaped char
                    i += 1
            i += 1
        return ''

    def _extract_tables(self, content: str, file_path: str, dialect: str) -> List[SQLTableInfo]:
        """Extract CREATE TABLE statements."""
        tables = []
        for m in self.CREATE_TABLE_HEADER.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))

            if not name or name.upper() in ('AS', 'SELECT', 'IF'):
                continue

            # Find the opening paren after the header match and extract body
            paren_pos = content.find('(', m.end() - 1)
            body = self._extract_balanced_parens(content, paren_pos) if paren_pos >= 0 else ''
            # end_pos is after the closing paren
            end_pos = m.end()
            if paren_pos >= 0 and body:
                end_pos = paren_pos + len(body) + 2  # +2 for the parens

            table = SQLTableInfo(
                name=name,
                schema_name=schema,
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_temporary=bool(m.group('temporary')),
                is_unlogged=bool(m.group('unlogged')),
            )

            # Look up COMMENT ON TABLE
            comment_key = f"table:{schema + '.' if schema else ''}{name}"
            if comment_key in self._comments:
                table.comment = self._comments[comment_key]

            # Parse columns and constraints from body
            if body:
                self._parse_table_body(body, table, dialect)

            # Check for MySQL table options after the closing paren
            full_stmt = content[m.start():content.find(';', end_pos) + 1] if ';' in content[end_pos:end_pos+500] else content[m.start():end_pos+500]
            self._parse_mysql_options(full_stmt, table)

            # Check for PARTITION BY
            part_match = self.PARTITION_BY.search(full_stmt)
            if part_match:
                table.is_partitioned = True
                table.partition_by = part_match.group('strategy').upper()
                table.partition_columns = [c.strip() for c in part_match.group('cols').split(',')]

            # Check for INHERITS (PostgreSQL)
            inherits_match = re.search(r'INHERITS\s*\(\s*([^)]+)\)', full_stmt, re.IGNORECASE)
            if inherits_match:
                table.inherits = [t.strip() for t in inherits_match.group(1).split(',')]

            tables.append(table)
        return tables

    def _parse_table_body(self, body: str, table: SQLTableInfo, dialect: str):
        """Parse column definitions and table constraints from CREATE TABLE body."""
        # Split by commas, respecting parenthetical groups
        parts = self._split_definitions(body)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Table-level PRIMARY KEY
            pk_match = self.PK_CONSTRAINT.match(part)
            if pk_match:
                table.primary_key = [c.strip().strip('"').strip('`') for c in pk_match.group('cols').split(',')]
                continue

            # Table-level FOREIGN KEY
            fk_match = self.FK_CONSTRAINT.match(part)
            if fk_match:
                table.foreign_keys.append({
                    'name': self._clean_name(fk_match.group('name') or ''),
                    'columns': [c.strip() for c in fk_match.group('cols').split(',')],
                    'ref_table': self._clean_name(fk_match.group('ref_table')),
                    'ref_columns': [c.strip() for c in fk_match.group('ref_cols').split(',')],
                    'on_delete': (fk_match.group('on_delete') or '').upper(),
                    'on_update': (fk_match.group('on_update') or '').upper(),
                })
                continue

            # Table-level UNIQUE
            uq_match = self.UNIQUE_CONSTRAINT.match(part)
            if uq_match:
                table.unique_constraints.append({
                    'name': self._clean_name(uq_match.group('name') or ''),
                    'columns': [c.strip() for c in uq_match.group('cols').split(',')],
                })
                continue

            # Table-level CHECK
            ck_match = self.CHECK_CONSTRAINT.match(part)
            if ck_match:
                table.check_constraints.append(ck_match.group('expr').strip())
                continue

            # Skip CONSTRAINT keyword-only lines
            if re.match(r'^\s*CONSTRAINT\s', part, re.IGNORECASE):
                continue

            # Column definition
            col = self._parse_column(part, table, dialect)
            if col:
                table.columns.append(col)

    def _parse_column(self, defn: str, table: SQLTableInfo, dialect: str) -> Optional[SQLColumnInfo]:
        """Parse a single column definition."""
        # Remove leading/trailing whitespace
        defn = defn.strip()
        if not defn:
            return None

        # Skip keywords that aren't columns
        skip_keywords = {'CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'INDEX', 'KEY', 'EXCLUDE'}
        first_word = defn.split()[0].upper().strip('"').strip('`').strip('[').strip(']')
        if first_word in skip_keywords:
            return None

        # Try to parse name and type
        parts = defn.split(None, 1)
        if len(parts) < 2:
            return None

        col_name = self._clean_name(parts[0])
        rest = parts[1]

        # Extract data type (everything before constraint keywords)
        type_match = re.match(
            r'(?P<type>[\w]+(?:\s*\([^)]*\))?(?:\s+(?:VARYING|PRECISION|UNSIGNED|ZEROFILL|WITH(?:OUT)?\s+TIME\s+ZONE|CHARACTER\s+SET\s+\w+))*)',
            rest, re.IGNORECASE
        )
        if not type_match:
            return None

        data_type = type_match.group('type').strip()
        constraints_str = rest[type_match.end():].strip()

        col = SQLColumnInfo(name=col_name, data_type=data_type)

        # Parse inline constraints
        if constraints_str:
            upper = constraints_str.upper()
            col.is_nullable = 'NOT NULL' not in upper
            col.is_primary_key = 'PRIMARY KEY' in upper or 'PRIMARY' in upper
            col.is_unique = 'UNIQUE' in upper
            col.is_identity = 'IDENTITY' in upper or 'GENERATED' in upper
            col.is_auto_increment = 'AUTO_INCREMENT' in upper
            col.is_serial = data_type.upper() in ('SERIAL', 'BIGSERIAL', 'SMALLSERIAL')

            # GENERATED ALWAYS AS
            gen_match = re.search(r'GENERATED\s+ALWAYS\s+AS\s*\(([^)]+)\)', constraints_str, re.IGNORECASE)
            if gen_match:
                col.is_generated = True
                col.generation_expr = gen_match.group(1).strip()

            # DEFAULT value
            default_match = re.search(r"DEFAULT\s+([^,\s]+(?:\([^)]*\))?)", constraints_str, re.IGNORECASE)
            if default_match:
                col.default_value = default_match.group(1).strip()

            # REFERENCES
            ref_match = re.search(r'REFERENCES\s+([\w"`.]+(?:\.[\w"`.]+)?)\s*\(\s*([\w"`.]+)\s*\)', constraints_str, re.IGNORECASE)
            if ref_match:
                col.references = f"{self._clean_name(ref_match.group(1))}.{self._clean_name(ref_match.group(2))}"

            # COLLATE
            collate_match = re.search(r'COLLATE\s+(\w+)', constraints_str, re.IGNORECASE)
            if collate_match:
                col.collation = collate_match.group(1)

            # If primary key, also set in table
            if col.is_primary_key and col_name not in table.primary_key:
                table.primary_key.append(col_name)

        # Look up column comment
        comment_key = f"column:{table.schema_name + '.' if table.schema_name else ''}{table.name}.{col_name}"
        if comment_key in self._comments:
            col.comment = self._comments[comment_key]

        return col

    def _parse_mysql_options(self, stmt: str, table: SQLTableInfo):
        """Parse MySQL-specific table options."""
        for m in self.MYSQL_OPTIONS.finditer(stmt):
            if m.group('engine'):
                table.engine = m.group('engine')
            if m.group('charset'):
                table.charset = m.group('charset')
            if m.group('collation'):
                table.collation = m.group('collation')
            if m.group('comment'):
                table.comment = m.group('comment')

    def _extract_views(self, content: str, file_path: str, dialect: str) -> List[SQLViewInfo]:
        """Extract CREATE VIEW statements."""
        views = []
        for m in self.CREATE_VIEW.finditer(content):
            if m.group('mat'):
                continue  # Skip materialized views — handled separately
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            query = (m.group('query') or '').strip()

            view = SQLViewInfo(
                name=name,
                schema_name=schema,
                query=query[:200] + ('...' if len(query) > 200 else ''),
                is_replace=bool(m.group('replace')),
                is_recursive=bool(m.group('recursive')),
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            if m.group('cols'):
                view.columns = [c.strip() for c in m.group('cols').split(',')]

            # Extract table dependencies from query
            view.dependencies = self._extract_table_refs(query)

            # WITH CHECK OPTION
            if re.search(r'WITH\s+(?:CASCADED\s+|LOCAL\s+)?CHECK\s+OPTION', m.group(0), re.IGNORECASE):
                view.with_check_option = True

            views.append(view)
        return views

    def _extract_materialized_views(self, content: str, file_path: str, dialect: str) -> List[SQLMaterializedViewInfo]:
        """Extract CREATE MATERIALIZED VIEW statements."""
        mat_views = []
        for m in self.CREATE_MATVIEW.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            query = (m.group('query') or '').strip()

            mv = SQLMaterializedViewInfo(
                name=name,
                schema_name=schema,
                query=query[:200] + ('...' if len(query) > 200 else ''),
                is_populated=not bool(m.group('data')),
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            if m.group('cols'):
                mv.columns = [c.strip() for c in m.group('cols').split(',')]
            mv.dependencies = self._extract_table_refs(query)
            mat_views.append(mv)
        return mat_views

    def _extract_custom_types(self, content: str, file_path: str, dialect: str) -> List[SQLCustomTypeInfo]:
        """Extract CREATE TYPE statements (PostgreSQL, Oracle, SQL Server)."""
        types = []
        for m in self.CREATE_TYPE.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            kind = (m.group('kind') or '').lower()
            body = (m.group('body') or '').strip()

            ct = SQLCustomTypeInfo(
                name=name,
                schema_name=schema,
                kind=kind or 'composite',
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            if kind == 'enum' and body:
                ct.values = [v.strip().strip("'") for v in body.split(',')]
            elif body:
                # Composite type — parse as attributes
                for attr in body.split(','):
                    attr = attr.strip()
                    parts = attr.split(None, 1)
                    if len(parts) == 2:
                        ct.attributes.append({'name': self._clean_name(parts[0]), 'type': parts[1].strip()})

            types.append(ct)
        return types

    def _extract_domains(self, content: str, file_path: str, dialect: str) -> List[SQLDomainInfo]:
        """Extract CREATE DOMAIN statements."""
        domains = []
        for m in self.CREATE_DOMAIN.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            base_type = (m.group('type') or '').strip()

            domain = SQLDomainInfo(
                name=name,
                schema_name=schema,
                base_type=base_type,
                default_value=m.group('default'),
                check_constraint=m.group('check'),
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            # NOT NULL in the statement
            if re.search(r'\bNOT\s+NULL\b', m.group(0), re.IGNORECASE):
                domain.is_nullable = False
            domains.append(domain)
        return domains

    def _extract_sequences(self, content: str, file_path: str, dialect: str) -> List[SQLSequenceInfo]:
        """Extract CREATE SEQUENCE statements."""
        sequences = []
        for m in self.CREATE_SEQUENCE.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            opts = m.group('opts') or ''

            seq = SQLSequenceInfo(
                name=name,
                schema_name=schema,
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            # Parse options
            start_match = re.search(r'START\s+(?:WITH\s+)?(\d+)', opts, re.IGNORECASE)
            if start_match:
                seq.start_value = int(start_match.group(1))
            inc_match = re.search(r'INCREMENT\s+(?:BY\s+)?(\d+)', opts, re.IGNORECASE)
            if inc_match:
                seq.increment = int(inc_match.group(1))
            min_match = re.search(r'MINVALUE\s+(\d+)', opts, re.IGNORECASE)
            if min_match:
                seq.min_value = int(min_match.group(1))
            max_match = re.search(r'MAXVALUE\s+(\d+)', opts, re.IGNORECASE)
            if max_match:
                seq.max_value = int(max_match.group(1))
            cache_match = re.search(r'CACHE\s+(\d+)', opts, re.IGNORECASE)
            if cache_match:
                seq.cache_size = int(cache_match.group(1))
            if re.search(r'\bCYCLE\b', opts, re.IGNORECASE) and not re.search(r'\bNO\s+CYCLE\b', opts, re.IGNORECASE):
                seq.cycle = True
            owned_match = re.search(r'OWNED\s+BY\s+([\w"`.]+)', opts, re.IGNORECASE)
            if owned_match:
                seq.owned_by = self._clean_name(owned_match.group(1))

            sequences.append(seq)
        return sequences

    def _extract_schemas(self, content: str, file_path: str, dialect: str) -> List[SQLSchemaInfo]:
        """Extract CREATE SCHEMA statements."""
        schemas = []
        for m in self.CREATE_SCHEMA.finditer(content):
            name = self._clean_name(m.group('name'))
            auth = self._clean_name(m.group('auth') or '')
            schemas.append(SQLSchemaInfo(
                name=name,
                authorization=auth,
                dialect=dialect,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        return schemas

    def _extract_alter_statements(self, content: str, file_path: str, dialect: str) -> List[Dict[str, Any]]:
        """Extract ALTER TABLE statements for schema evolution tracking."""
        alters = []
        for m in self.ALTER_TABLE.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            action = m.group('action').strip().upper()
            detail = m.group('detail').strip()

            alters.append({
                'table': f"{schema + '.' if schema else ''}{name}",
                'action': action,
                'detail': detail[:150],
                'file': file_path,
                'line': content[:m.start()].count('\n') + 1,
            })
        return alters

    def _extract_table_refs(self, query: str) -> List[str]:
        """Extract table references from a SQL query (FROM/JOIN clauses)."""
        tables = set()
        # FROM and JOIN patterns
        pattern = re.compile(
            r'(?:FROM|JOIN)\s+([\w"`.]+(?:\.[\w"`.]+)?)',
            re.IGNORECASE
        )
        for m in pattern.finditer(query):
            name = self._clean_name(m.group(1))
            if name.upper() not in ('SELECT', 'WHERE', 'SET', 'VALUES', 'AS', 'ON', 'AND', 'OR'):
                tables.add(name)
        return sorted(tables)

    def _split_definitions(self, body: str) -> List[str]:
        """Split column/constraint definitions respecting parenthetical groups."""
        parts = []
        depth = 0
        current = []
        for char in body:
            if char == '(':
                depth += 1
                current.append(char)
            elif char == ')':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)
        if current:
            parts.append(''.join(current))
        return parts
