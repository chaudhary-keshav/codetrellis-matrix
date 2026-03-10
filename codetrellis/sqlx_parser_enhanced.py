"""
EnhancedSqlxParser v1.0 - Comprehensive sqlx (Go SQL extensions) parser.

Supports:
- sqlx v1.x (jmoiron/sqlx)
- Standard database/sql patterns used alongside sqlx

sqlx-specific extraction:
- Connection patterns (sqlx.Connect, sqlx.Open, sqlx.MustConnect)
- Query methods (Get, Select, NamedQuery, NamedExec, QueryRow, Queryx)
- Named parameters (:name syntax)
- Struct scanning (StructScan, SliceScan, MapScan)
- Transaction patterns (Beginx, MustBegin, Tx)
- Prepared statements (Preparex, PrepareNamed, Stmtx)
- Rebind for cross-driver portability
- In() clause expansion
- DB tags (`db:"column_name"`)
- Driver detection (pgx, mysql, sqlite3, mssql)

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SqlxQueryInfo:
    """sqlx query operation."""
    method: str  # Get, Select, NamedQuery, NamedExec, Exec, QueryRowx, Queryx, etc.
    query: str = ""  # The SQL query if extractable
    has_named_params: bool = False
    result_type: str = ""  # The struct being scanned into
    file: str = ""
    line_number: int = 0


@dataclass
class SqlxModelInfo:
    """Struct with db tags (used for sqlx scanning)."""
    name: str
    fields: List[Dict[str, str]] = field(default_factory=list)  # [{name, type, db_tag}]
    file: str = ""
    line_number: int = 0


@dataclass
class SqlxConnectionInfo:
    """sqlx database connection."""
    method: str  # Connect, Open, MustConnect
    driver: str = ""
    dsn_var: str = ""
    variable_name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SqlxPreparedStmtInfo:
    """sqlx prepared statement."""
    name: str
    method: str  # Preparex, PrepareNamed, Stmtx
    query: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SqlxTxInfo:
    """sqlx transaction usage."""
    method: str  # Beginx, MustBegin, BeginTxx
    variable_name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SqlxParseResult:
    file_path: str
    file_type: str = "go"

    queries: List[SqlxQueryInfo] = field(default_factory=list)
    models: List[SqlxModelInfo] = field(default_factory=list)
    connections: List[SqlxConnectionInfo] = field(default_factory=list)
    prepared_stmts: List[SqlxPreparedStmtInfo] = field(default_factory=list)
    transactions: List[SqlxTxInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    detected_driver: str = ""
    has_named_params: bool = False
    has_rebind: bool = False
    has_in_clause: bool = False
    total_queries: int = 0
    total_models: int = 0


class EnhancedSqlxParser:
    """Enhanced sqlx parser for comprehensive SQL extension extraction."""

    SQLX_IMPORT = re.compile(r'"github\.com/jmoiron/sqlx"')

    # Connection: db := sqlx.Connect("postgres", dsn) / sqlx.Open / sqlx.MustConnect
    CONNECT_PATTERN = re.compile(
        r'(\w+)\s*(?:,\s*\w+\s*)?:?=\s*sqlx\.(Connect|Open|MustConnect|MustOpen)\s*\(\s*"?(\w+)"?\s*,\s*([^)]+)\)',
    )

    # Query methods: db.Get(&user, "SELECT ...", args...) — also matches *Context variants
    GET_PATTERN = re.compile(
        r'\.(Get|Select|NamedQuery|NamedExec|QueryRowx|Queryx|MustExec|Exec|QueryRow)(?:Context)?\s*\(\s*([^)]{0,500})',
        re.DOTALL,
    )

    # Named query: db.NamedExec("INSERT INTO users (:name, :email)", user)
    NAMED_PARAM = re.compile(r':\w+')

    # Struct scan: row.StructScan(&user)
    STRUCT_SCAN_PATTERN = re.compile(
        r'\.(StructScan|SliceScan|MapScan|Scan)\s*\(\s*&?(\w+)',
    )

    # Prepared statement: stmt, err := db.Preparex("SELECT ...") or r.db.Preparex(...)
    PREPARE_PATTERN = re.compile(
        r'(\w+)\s*,?\s*\w*\s*:?=\s*(?:\w+\.)+?(Preparex|PrepareNamed|Stmtx|MustPreparex)\s*\(\s*(?:`|")((?:[^`"\\]|\\.)*)(?:`|")',
    )

    # Transaction: tx := db.MustBegin() or r.db.Beginx()
    TX_PATTERN = re.compile(
        r'(\w+)\s*(?:,\s*\w+\s*)?:?=\s*(?:\w+\.)+?(Beginx|MustBegin|BeginTxx)\s*\(',
    )

    # Rebind: sqlx.Rebind(sqlx.DOLLAR, query)
    REBIND_PATTERN = re.compile(r'sqlx\.Rebind|\.Rebind\s*\(')

    # In clause: sqlx.In("SELECT ... WHERE id IN (?)", ids)
    IN_CLAUSE_PATTERN = re.compile(r'sqlx\.In\s*\(')

    # db struct tag: `db:"column_name"`
    DB_TAG_PATTERN = re.compile(r'db:"([^"]*)"')

    # Model with db tags
    MODEL_PATTERN = re.compile(
        r'type\s+(\w+)\s+struct\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # SQL query string extraction (inline)
    SQL_QUERY_PATTERN = re.compile(r'(?:`|")((?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\s[^`"]{0,500})(?:`|")', re.IGNORECASE)

    # Driver imports
    DRIVER_PATTERNS = {
        'postgres': re.compile(r'"github\.com/lib/pq"|"github\.com/jackc/pgx'),
        'mysql': re.compile(r'"github\.com/go-sql-driver/mysql"'),
        'sqlite3': re.compile(r'"github\.com/mattn/go-sqlite3"|"modernc\.org/sqlite"'),
        'mssql': re.compile(r'"github\.com/denisenkom/go-mssqldb"'),
    }

    FRAMEWORK_PATTERNS = {
        'sqlx': re.compile(r'"github\.com/jmoiron/sqlx"'),
        'squirrel': re.compile(r'"github\.com/Masterminds/squirrel"'),
        'goqu': re.compile(r'"github\.com/doug-martin/goqu"'),
        'dbr': re.compile(r'"github\.com/gocraft/dbr"'),
        'sqlboiler': re.compile(r'"github\.com/volatiletech/sqlboiler"'),
        'pgx': re.compile(r'"github\.com/jackc/pgx'),
        'database-sql': re.compile(r'"database/sql"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> SqlxParseResult:
        result = SqlxParseResult(file_path=file_path)

        if not self.SQLX_IMPORT.search(content):
            # Also check for db tags without explicit sqlx import
            if not self.DB_TAG_PATTERN.search(content):
                return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_driver = self._detect_driver(content)
        result.has_rebind = bool(self.REBIND_PATTERN.search(content))
        result.has_in_clause = bool(self.IN_CLAUSE_PATTERN.search(content))

        # Connections
        for m in self.CONNECT_PATTERN.finditer(content):
            result.connections.append(SqlxConnectionInfo(
                variable_name=m.group(1), method=m.group(2),
                driver=m.group(3), dsn_var=m.group(4).strip(),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Models with db tags
        for m in self.MODEL_PATTERN.finditer(content):
            model_name = m.group(1)
            body = m.group(2)

            if not self.DB_TAG_PATTERN.search(body):
                continue

            fields = []
            for line in body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue

                field_match = re.match(r'(\w+)\s+([\[\]*\w.]+)', line)
                db_match = self.DB_TAG_PATTERN.search(line)
                if field_match and db_match:
                    fields.append({
                        'name': field_match.group(1),
                        'type': field_match.group(2),
                        'db_tag': db_match.group(1),
                    })

            if fields:
                result.models.append(SqlxModelInfo(
                    name=model_name, fields=fields, file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

        # Queries
        for m in self.GET_PATTERN.finditer(content):
            method = m.group(1)
            args = m.group(2)

            has_named = bool(self.NAMED_PARAM.search(args))
            if has_named:
                result.has_named_params = True

            # Try to extract the SQL query
            sql_match = self.SQL_QUERY_PATTERN.search(args)
            query = sql_match.group(1).strip() if sql_match else ""

            result.queries.append(SqlxQueryInfo(
                method=method, query=query[:200],  # Truncate long queries
                has_named_params=has_named,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Prepared statements
        for m in self.PREPARE_PATTERN.finditer(content):
            result.prepared_stmts.append(SqlxPreparedStmtInfo(
                name=m.group(1), method=m.group(2),
                query=m.group(3)[:200],
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Transactions
        for m in self.TX_PATTERN.finditer(content):
            result.transactions.append(SqlxTxInfo(
                variable_name=m.group(1), method=m.group(2),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        result.total_queries = len(result.queries)
        result.total_models = len(result.models)

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
