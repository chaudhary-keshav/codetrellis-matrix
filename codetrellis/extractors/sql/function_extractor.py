"""
SQLFunctionExtractor - Extracts SQL stored procedures, functions, triggers, and events.

This extractor parses SQL source code and extracts:
- CREATE FUNCTION (PostgreSQL, MySQL, SQL Server, Oracle, SQLite)
- CREATE PROCEDURE / CREATE OR REPLACE PROCEDURE
- CREATE TRIGGER (all timing/event combinations)
- CREATE EVENT (MySQL scheduled events)
- Parameter lists with IN/OUT/INOUT modes
- Function/procedure bodies (truncated for token efficiency)
- Return types and volatility markers (IMMUTABLE, STABLE, VOLATILE)
- Language declarations (plpgsql, sql, plv8, plpython3u, etc.)
- Security context (DEFINER, INVOKER)
- CTE (Common Table Expression) detection
- Cursor declarations

Supported SQL dialects:
- PostgreSQL: $$ body, RETURNS, LANGUAGE, IMMUTABLE/STABLE/VOLATILE, OUT params
- MySQL: DELIMITER, DETERMINISTIC, READS/MODIFIES SQL DATA, BEGIN...END
- SQL Server / T-SQL: AS BEGIN...END, OUTPUT params, @@ROWCOUNT, TRY/CATCH
- Oracle / PL/SQL: IS/AS BEGIN...END, PRAGMA, EXCEPTION WHEN, BULK COLLECT
- SQLite: limited function support (mostly UDFs via extensions)

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SQLParameterInfo:
    """Information about a function/procedure parameter."""
    name: str
    data_type: str
    mode: str = "IN"          # IN, OUT, INOUT, VARIADIC
    default_value: Optional[str] = None
    is_output: bool = False   # SQL Server OUTPUT keyword


@dataclass
class SQLFunctionInfo:
    """Information about a SQL function."""
    name: str
    schema_name: str = ""
    parameters: List[SQLParameterInfo] = field(default_factory=list)
    return_type: str = ""
    returns_table: bool = False       # RETURNS TABLE(...)
    returns_setof: bool = False       # RETURNS SETOF
    language: str = ""                # plpgsql, sql, tsql, plsql
    volatility: str = ""              # IMMUTABLE, STABLE, VOLATILE
    is_deterministic: bool = False    # MySQL DETERMINISTIC
    is_aggregate: bool = False        # CREATE AGGREGATE
    is_window: bool = False           # Window function
    security_definer: bool = False    # SECURITY DEFINER
    parallel_safe: str = ""           # PARALLEL SAFE/UNSAFE/RESTRICTED
    body_preview: str = ""            # First ~200 chars of body
    body_statements: int = 0          # Approximate statement count
    calls: List[str] = field(default_factory=list)  # Functions/procedures called
    tables_referenced: List[str] = field(default_factory=list)
    has_exception_handler: bool = False
    has_transaction: bool = False     # BEGIN TRANSACTION / COMMIT
    has_cursor: bool = False          # DECLARE CURSOR / OPEN / FETCH
    has_dynamic_sql: bool = False     # EXECUTE / EXEC / EXECUTE IMMEDIATE
    dialect: str = ""
    comment: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class SQLStoredProcInfo:
    """Information about a SQL stored procedure."""
    name: str
    schema_name: str = ""
    parameters: List[SQLParameterInfo] = field(default_factory=list)
    language: str = ""
    security_definer: bool = False
    body_preview: str = ""
    body_statements: int = 0
    calls: List[str] = field(default_factory=list)
    tables_referenced: List[str] = field(default_factory=list)
    has_exception_handler: bool = False
    has_transaction: bool = False
    has_cursor: bool = False
    has_dynamic_sql: bool = False
    dialect: str = ""
    comment: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class SQLTriggerInfo:
    """Information about a SQL trigger."""
    name: str
    schema_name: str = ""
    table_name: str = ""
    timing: str = ""                  # BEFORE, AFTER, INSTEAD OF
    events: List[str] = field(default_factory=list)  # INSERT, UPDATE, DELETE, TRUNCATE
    for_each: str = "STATEMENT"       # ROW or STATEMENT
    when_condition: Optional[str] = None
    function_name: str = ""           # PostgreSQL: EXECUTE FUNCTION
    body_preview: str = ""            # MySQL/SQL Server inline body
    is_constraint: bool = False       # PostgreSQL constraint trigger
    is_deferred: bool = False         # DEFERRABLE INITIALLY DEFERRED
    referencing: Dict[str, str] = field(default_factory=dict)  # OLD AS x, NEW AS y (SQL Server)
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLEventInfo:
    """Information about a MySQL scheduled event."""
    name: str
    schedule: str = ""                # AT datetime / EVERY interval
    is_recurring: bool = False
    starts: Optional[str] = None
    ends: Optional[str] = None
    body_preview: str = ""
    is_enabled: bool = True
    dialect: str = "mysql"
    file: str = ""
    line_number: int = 0


class SQLFunctionExtractor:
    """
    Extracts SQL functions, procedures, triggers, and events from source code.

    Handles:
    - CREATE FUNCTION with various body delimiters ($$ for PG, BEGIN...END, AS)
    - CREATE PROCEDURE / CREATE OR REPLACE PROCEDURE
    - CREATE TRIGGER (BEFORE/AFTER/INSTEAD OF for INSERT/UPDATE/DELETE/TRUNCATE)
    - CREATE EVENT (MySQL only)
    - Parameter parsing (IN, OUT, INOUT, VARIADIC, DEFAULT, OUTPUT)
    - Body analysis (statement count, function calls, table references)
    - Cross-dialect compatibility

    v4.15: Uses brace-balanced extraction for PL/pgSQL $$ bodies.
    """

    # CREATE FUNCTION pattern (multi-dialect)
    CREATE_FUNCTION = re.compile(
        r'CREATE\s+'
        r'(?:OR\s+REPLACE\s+)?'
        r'(?:AGGREGATE\s+)?'
        r'FUNCTION\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s*'
        r'\(\s*(?P<params>[^)]*)\s*\)',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE PROCEDURE
    CREATE_PROCEDURE = re.compile(
        r'CREATE\s+'
        r'(?:OR\s+REPLACE\s+)?'
        r'PROC(?:EDURE)?\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s*'
        r'(?:\(\s*(?P<params>[^)]*)\s*\))?',
        re.IGNORECASE | re.DOTALL
    )

    # CREATE TRIGGER
    CREATE_TRIGGER = re.compile(
        r'CREATE\s+'
        r'(?:OR\s+REPLACE\s+)?'
        r'(?:CONSTRAINT\s+)?'
        r'TRIGGER\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<schema>[\w"`.]+\.)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'(?P<timing>BEFORE|AFTER|INSTEAD\s+OF)\s+'
        r'(?P<events>(?:INSERT|UPDATE|DELETE|TRUNCATE)(?:\s+OR\s+(?:INSERT|UPDATE|DELETE|TRUNCATE))*)\s+'
        r'ON\s+(?P<table>[\w"`.]+(?:\.[\w"`.]+)?)',
        re.IGNORECASE
    )

    # CREATE EVENT (MySQL)
    CREATE_EVENT = re.compile(
        r'CREATE\s+'
        r'(?:DEFINER\s*=\s*\S+\s+)?'
        r'EVENT\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'ON\s+SCHEDULE\s+'
        r'(?P<schedule>.+?)\s+'
        r'(?:ON\s+COMPLETION\s+(?:NOT\s+)?PRESERVE\s+)?'
        r'(?:(?P<enabled>ENABLE|DISABLE(?:\s+ON\s+SLAVE)?)\s+)?'
        r'(?:COMMENT\s+\'[^\']*\'\s+)?'
        r'DO\s+',
        re.IGNORECASE | re.DOTALL
    )

    # RETURNS clause (PostgreSQL/MySQL)
    RETURNS_PATTERN = re.compile(
        r'RETURNS\s+(?P<setof>SETOF\s+)?(?P<table>TABLE\s*\()?(?P<type>[^;$]+?)(?:\s+(?:AS|LANGUAGE|IMMUTABLE|STABLE|VOLATILE|DETERMINISTIC|SECURITY|PARALLEL|BEGIN|DECLARE|\$\$|RETURN))',
        re.IGNORECASE
    )

    # LANGUAGE declaration
    LANGUAGE_PATTERN = re.compile(
        r'LANGUAGE\s+(?P<lang>\w+)',
        re.IGNORECASE
    )

    # Volatility markers (PostgreSQL)
    VOLATILITY_PATTERN = re.compile(
        r'\b(?P<vol>IMMUTABLE|STABLE|VOLATILE)\b',
        re.IGNORECASE
    )

    # PARALLEL safety (PostgreSQL)
    PARALLEL_PATTERN = re.compile(
        r'PARALLEL\s+(?P<mode>SAFE|UNSAFE|RESTRICTED)',
        re.IGNORECASE
    )

    # CTE pattern — matches both "WITH name AS (" and ", name AS ("
    CTE_PATTERN = re.compile(
        r'(?:\bWITH\s+(?:RECURSIVE\s+)?|,\s*)(\w+)\s+AS\s*\(',
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all SQL functions, procedures, triggers, and events.

        Returns:
            Dict with keys: functions, procedures, triggers, events, ctes
        """
        functions = self._extract_functions(content, file_path)
        procedures = self._extract_procedures(content, file_path)
        triggers = self._extract_triggers(content, file_path)
        events = self._extract_events(content, file_path)
        ctes = self._extract_ctes(content, file_path)

        return {
            'functions': functions,
            'procedures': procedures,
            'triggers': triggers,
            'events': events,
            'ctes': ctes,
        }

    def _extract_functions(self, content: str, file_path: str) -> List[SQLFunctionInfo]:
        """Extract CREATE FUNCTION statements."""
        functions = []
        for m in self.CREATE_FUNCTION.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            raw_params = m.group('params') or ''

            func = SQLFunctionInfo(
                name=name,
                schema_name=schema,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Parse parameters
            func.parameters = self._parse_parameters(raw_params)

            # Get the rest of the statement after the closing paren
            after = content[m.end():]

            # RETURNS
            ret_match = self.RETURNS_PATTERN.search(after[:500])
            if ret_match:
                func.return_type = ret_match.group('type').strip()
                func.returns_setof = bool(ret_match.group('setof'))
                func.returns_table = bool(ret_match.group('table'))

            # LANGUAGE
            lang_match = self.LANGUAGE_PATTERN.search(after[:500])
            if lang_match:
                func.language = lang_match.group('lang').lower()

            # Volatility
            vol_match = self.VOLATILITY_PATTERN.search(after[:500])
            if vol_match:
                func.volatility = vol_match.group('vol').upper()

            # PARALLEL
            par_match = self.PARALLEL_PATTERN.search(after[:500])
            if par_match:
                func.parallel_safe = par_match.group('mode').upper()

            # SECURITY
            if re.search(r'SECURITY\s+DEFINER', after[:500], re.IGNORECASE):
                func.security_definer = True

            # DETERMINISTIC (MySQL)
            if re.search(r'\bDETERMINISTIC\b', after[:500], re.IGNORECASE):
                func.is_deterministic = True

            # AGGREGATE
            if re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?AGGREGATE', content[m.start():m.start()+100], re.IGNORECASE):
                func.is_aggregate = True

            # Extract body preview
            body = self._extract_body(after)
            func.body_preview = body[:200] + ('...' if len(body) > 200 else '')
            func.body_statements = self._count_statements(body)

            # Analyze body
            self._analyze_body(body, func)

            # Detect dialect
            func.dialect = self._detect_func_dialect(content[m.start():m.start()+len(after[:1000])])

            functions.append(func)
        return functions

    def _extract_procedures(self, content: str, file_path: str) -> List[SQLStoredProcInfo]:
        """Extract CREATE PROCEDURE statements."""
        procedures = []
        for m in self.CREATE_PROCEDURE.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            raw_params = m.group('params') or ''

            proc = SQLStoredProcInfo(
                name=name,
                schema_name=schema,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            proc.parameters = self._parse_parameters(raw_params)

            after = content[m.end():]
            lang_match = self.LANGUAGE_PATTERN.search(after[:300])
            if lang_match:
                proc.language = lang_match.group('lang').lower()

            if re.search(r'SECURITY\s+DEFINER', after[:300], re.IGNORECASE):
                proc.security_definer = True

            body = self._extract_body(after)
            proc.body_preview = body[:200] + ('...' if len(body) > 200 else '')
            proc.body_statements = self._count_statements(body)
            self._analyze_body_proc(body, proc)
            proc.dialect = self._detect_func_dialect(content[m.start():m.start()+len(after[:1000])])

            procedures.append(proc)
        return procedures

    def _extract_triggers(self, content: str, file_path: str) -> List[SQLTriggerInfo]:
        """Extract CREATE TRIGGER statements."""
        triggers = []
        for m in self.CREATE_TRIGGER.finditer(content):
            schema = self._clean_name(m.group('schema') or '')
            name = self._clean_name(m.group('name'))
            timing = m.group('timing').strip().upper()
            events_str = m.group('events').upper()
            table = self._clean_name(m.group('table'))

            events = re.split(r'\s+OR\s+', events_str)

            trigger = SQLTriggerInfo(
                name=name,
                schema_name=schema,
                table_name=table,
                timing=timing,
                events=events,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            after = content[m.end():]

            # FOR EACH ROW / FOR EACH STATEMENT
            row_match = re.search(r'FOR\s+EACH\s+(?P<each>ROW|STATEMENT)', after[:300], re.IGNORECASE)
            if row_match:
                trigger.for_each = row_match.group('each').upper()

            # WHEN condition
            when_match = re.search(r'WHEN\s*\(\s*(.+?)\s*\)', after[:500], re.IGNORECASE)
            if when_match:
                trigger.when_condition = when_match.group(1).strip()

            # EXECUTE FUNCTION/PROCEDURE (PostgreSQL)
            exec_match = re.search(r'EXECUTE\s+(?:FUNCTION|PROCEDURE)\s+([\w"`.]+)', after[:300], re.IGNORECASE)
            if exec_match:
                trigger.function_name = self._clean_name(exec_match.group(1))

            # CONSTRAINT trigger
            if re.search(r'CONSTRAINT', content[m.start():m.end()], re.IGNORECASE):
                trigger.is_constraint = True

            # REFERENCING (SQL Server: REFERENCING OLD AS o NEW AS n)
            ref_match = re.search(
                r'REFERENCING\s+(?:OLD\s+(?:ROW\s+)?AS\s+(\w+)\s+)?(?:NEW\s+(?:ROW\s+)?AS\s+(\w+))?',
                after[:300], re.IGNORECASE
            )
            if ref_match:
                if ref_match.group(1):
                    trigger.referencing['old'] = ref_match.group(1)
                if ref_match.group(2):
                    trigger.referencing['new'] = ref_match.group(2)

            triggers.append(trigger)
        return triggers

    def _extract_events(self, content: str, file_path: str) -> List[SQLEventInfo]:
        """Extract CREATE EVENT statements (MySQL)."""
        events = []
        for m in self.CREATE_EVENT.finditer(content):
            name = self._clean_name(m.group('name'))
            schedule = m.group('schedule').strip()

            event = SQLEventInfo(
                name=name,
                schedule=schedule,
                is_recurring='EVERY' in schedule.upper(),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            if m.group('enabled'):
                event.is_enabled = m.group('enabled').upper() == 'ENABLE'

            events.append(event)
        return events

    def _extract_ctes(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Common Table Expression (WITH ... AS) declarations."""
        ctes = []
        for m in self.CTE_PATTERN.finditer(content):
            ctes.append({
                'name': m.group(1),
                'is_recursive': 'RECURSIVE' in content[m.start():m.end()].upper(),
                'file': file_path,
                'line': content[:m.start()].count('\n') + 1,
            })
        return ctes

    def _parse_parameters(self, raw_params: str) -> List[SQLParameterInfo]:
        """Parse function/procedure parameter list."""
        params = []
        if not raw_params.strip():
            return params

        for part in self._split_params(raw_params):
            part = part.strip()
            if not part:
                continue

            param = SQLParameterInfo(name='', data_type='')

            # Check for mode prefix
            mode_match = re.match(r'^(IN\s+OUT|INOUT|OUT|IN|VARIADIC)\s+', part, re.IGNORECASE)
            if mode_match:
                mode = mode_match.group(1).upper().replace('IN OUT', 'INOUT')
                param.mode = mode
                param.is_output = mode in ('OUT', 'INOUT')
                part = part[mode_match.end():]

            # SQL Server OUTPUT at end
            if re.search(r'\bOUTPUT\s*$', part, re.IGNORECASE):
                param.is_output = True
                param.mode = 'OUT'
                part = re.sub(r'\bOUTPUT\s*$', '', part, flags=re.IGNORECASE).strip()

            # Split name and type
            tokens = part.split(None, 1)
            if len(tokens) == 2:
                # Check if first token looks like a type (no name given — PostgreSQL allows this)
                if tokens[0].upper() in ('INT', 'INTEGER', 'TEXT', 'VARCHAR', 'BOOLEAN', 'FLOAT', 'DOUBLE',
                                          'NUMERIC', 'BIGINT', 'SMALLINT', 'REAL', 'DATE', 'TIMESTAMP',
                                          'UUID', 'JSON', 'JSONB', 'BYTEA', 'VOID'):
                    param.data_type = part
                else:
                    param.name = tokens[0].strip('"').strip('`').strip('@')
                    remaining = tokens[1]
                    # Check for DEFAULT
                    default_match = re.search(r'\s+DEFAULT\s+(.+)$', remaining, re.IGNORECASE)
                    if default_match:
                        param.default_value = default_match.group(1).strip()
                        remaining = remaining[:default_match.start()]
                    param.data_type = remaining.strip()
            elif len(tokens) == 1:
                param.data_type = tokens[0]

            if param.data_type:
                params.append(param)

        return params

    def _split_params(self, raw: str) -> List[str]:
        """Split parameter list respecting parenthetical groups."""
        parts = []
        depth = 0
        current = []
        for char in raw:
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

    def _extract_body(self, after_header: str) -> str:
        """Extract function/procedure body from the text after the header."""
        # PostgreSQL $$ body
        dollar_match = re.search(r'\$(\w*)\$\s*(.*?)\$\1\$', after_header, re.DOTALL)
        if dollar_match:
            return dollar_match.group(2).strip()

        # BEGIN ... END body (T-SQL, PL/SQL, MySQL)
        begin_match = re.search(r'\bBEGIN\b(.*?)\bEND\b', after_header, re.DOTALL | re.IGNORECASE)
        if begin_match:
            return begin_match.group(1).strip()

        # AS single statement (simple functions)
        as_match = re.search(r'\bAS\b\s+(.*?)(?:;|\Z)', after_header[:500], re.DOTALL | re.IGNORECASE)
        if as_match:
            return as_match.group(1).strip()

        # RETURN single expression
        ret_match = re.search(r'\bRETURN\b\s+(.*?)(?:;|\Z)', after_header[:500], re.DOTALL | re.IGNORECASE)
        if ret_match:
            return ret_match.group(1).strip()

        return ''

    def _count_statements(self, body: str) -> int:
        """Approximate statement count in function body."""
        if not body:
            return 0
        # Count semicolons as proxy for statement count
        return body.count(';') + 1

    def _analyze_body(self, body: str, func: SQLFunctionInfo):
        """Analyze function body for patterns."""
        if not body:
            return
        upper = body.upper()
        func.has_exception_handler = 'EXCEPTION' in upper or 'CATCH' in upper
        func.has_transaction = any(kw in upper for kw in ('BEGIN TRANSACTION', 'COMMIT', 'ROLLBACK', 'SAVEPOINT'))
        func.has_cursor = any(kw in upper for kw in ('DECLARE CURSOR', 'OPEN ', 'FETCH ', 'CLOSE '))
        func.has_dynamic_sql = any(kw in upper for kw in ('EXECUTE ', 'EXEC ', 'EXECUTE IMMEDIATE'))

        # Extract function calls
        call_pattern = re.compile(r'\b([\w]+)\s*\(', re.IGNORECASE)
        sql_keywords = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                        'IF', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'NOT', 'IN', 'EXISTS',
                        'COALESCE', 'NULLIF', 'CAST', 'CONVERT', 'COUNT', 'SUM', 'AVG',
                        'MIN', 'MAX', 'ARRAY', 'ROW', 'VALUES', 'SET', 'RAISE', 'RETURN'}
        calls = set()
        for cm in call_pattern.finditer(body):
            fname = cm.group(1)
            if fname.upper() not in sql_keywords:
                calls.add(fname)
        func.calls = sorted(calls)[:15]

        # Extract table references
        table_pattern = re.compile(r'(?:FROM|JOIN|INTO|UPDATE)\s+([\w"`.]+)', re.IGNORECASE)
        tables = set()
        for tm in table_pattern.finditer(body):
            tname = tm.group(1).strip('"').strip('`')
            if tname.upper() not in sql_keywords:
                tables.add(tname)
        func.tables_referenced = sorted(tables)[:15]

    def _analyze_body_proc(self, body: str, proc: SQLStoredProcInfo):
        """Analyze procedure body for patterns (reuses function analysis)."""
        if not body:
            return
        upper = body.upper()
        proc.has_exception_handler = 'EXCEPTION' in upper or 'CATCH' in upper
        proc.has_transaction = any(kw in upper for kw in ('BEGIN TRANSACTION', 'COMMIT', 'ROLLBACK', 'SAVEPOINT'))
        proc.has_cursor = any(kw in upper for kw in ('DECLARE CURSOR', 'OPEN ', 'FETCH ', 'CLOSE '))
        proc.has_dynamic_sql = any(kw in upper for kw in ('EXECUTE ', 'EXEC ', 'EXECUTE IMMEDIATE'))

        call_pattern = re.compile(r'\b([\w]+)\s*\(', re.IGNORECASE)
        sql_keywords = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                        'IF', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'NOT', 'IN', 'EXISTS',
                        'COALESCE', 'NULLIF', 'CAST', 'CONVERT', 'COUNT', 'SUM', 'AVG',
                        'MIN', 'MAX', 'ARRAY', 'ROW', 'VALUES', 'SET', 'RAISE', 'RETURN'}
        calls = set()
        for cm in call_pattern.finditer(body):
            fname = cm.group(1)
            if fname.upper() not in sql_keywords:
                calls.add(fname)
        proc.calls = sorted(calls)[:15]

        table_pattern = re.compile(r'(?:FROM|JOIN|INTO|UPDATE)\s+([\w"`.]+)', re.IGNORECASE)
        tables = set()
        for tm in table_pattern.finditer(body):
            tname = tm.group(1).strip('"').strip('`')
            if tname.upper() not in sql_keywords:
                tables.add(tname)
        proc.tables_referenced = sorted(tables)[:15]

    def _detect_func_dialect(self, text: str) -> str:
        """Detect dialect from function/procedure text."""
        upper = text.upper()
        if '$$' in text or 'LANGUAGE PLPGSQL' in upper or 'RETURNS SETOF' in upper:
            return 'postgresql'
        if 'DELIMITER' in upper or 'DETERMINISTIC' in upper or 'DEFINER' in upper:
            return 'mysql'
        if 'AS BEGIN' in upper and ('@@' in text or 'EXEC' in upper):
            return 'sqlserver'
        if 'IS BEGIN' in upper or 'PRAGMA' in upper or 'PLS_INTEGER' in upper:
            return 'oracle'
        return ''

    def _clean_name(self, name: str) -> str:
        """Remove quoting characters from identifiers."""
        if not name:
            return name
        return name.strip().strip('"').strip('`').strip('[').strip(']').strip('.')
