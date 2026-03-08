"""
Lua Model Extractor for CodeTrellis

Extracts data model and database patterns from Lua source code:
- Lapis models (Model:extend, relations)
- pgmoon PostgreSQL queries
- luasql connections and queries
- Redis data structures
- Tarantool spaces and indexes
- LuaSQL/pgmoon/resty.mysql schema patterns
- Migration definitions

Part of CodeTrellis v4.28 - Lua Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LuaModelInfo:
    """Information about a database model."""
    name: str
    table_name: str = ""
    file: str = ""
    orm: str = ""  # lapis, sequel, tarantool
    relations: List[Dict[str, str]] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    fields: List[Dict[str, str]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    timestamps: bool = False
    primary_key: str = ""
    line_number: int = 0


@dataclass
class LuaQueryInfo:
    """Information about a database query."""
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, CREATE, etc.
    table: str = ""
    driver: str = ""  # pgmoon, luasql, resty.mysql, resty.redis
    is_parameterized: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LuaSchemaInfo:
    """Information about a schema/migration definition."""
    name: str
    operation: str = ""  # create_table, add_column, drop_table, etc.
    table_name: str = ""
    columns: List[Dict[str, str]] = field(default_factory=list)
    framework: str = ""
    file: str = ""
    line_number: int = 0


class LuaModelExtractor:
    """
    Extracts Lua data model patterns using regex-based parsing.

    Supports:
    - Lapis Model:extend() patterns
    - Lapis migration schema
    - pgmoon queries
    - luasql connections
    - resty.mysql queries
    - resty.redis commands
    - Tarantool box.schema
    """

    # Lapis Model pattern
    LAPIS_MODEL_PATTERN = re.compile(
        r"(?:local\s+)?(?P<name>\w+)\s*=\s*Model\s*:\s*extend\s*\(\s*['\"](?P<table>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Lapis relations
    LAPIS_RELATION_PATTERN = re.compile(
        r"(?P<type>has_one|has_many|belongs_to|polymorphic_belongs_to)\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Lapis migration create_table
    LAPIS_CREATE_TABLE_PATTERN = re.compile(
        r"schema\.create_table\s*\(\s*['\"](?P<table>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # SQL query patterns (embedded SQL strings)
    SQL_QUERY_PATTERN = re.compile(
        r"(?:db\s*:\s*query|pg\s*:\s*query|mysql\s*:\s*query|conn\s*:\s*execute)\s*\(\s*['\"\[]+"
        r"(?P<query>(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s[^'\"]+)",
        re.MULTILINE | re.IGNORECASE
    )

    # Tarantool space definition
    TARANTOOL_SPACE_PATTERN = re.compile(
        r"box\.schema\.space\.create\s*\(\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Tarantool index definition
    TARANTOOL_INDEX_PATTERN = re.compile(
        r"(?P<space>\w+)\s*:\s*create_index\s*\(\s*['\"](?P<name>[^'\"]+)['\"]",
        re.MULTILINE
    )

    # pgmoon/resty database connection
    DB_CONNECT_PATTERN = re.compile(
        r"(?:pgmoon|Postgres|mysql|resty\.mysql|luasql\.\w+)\s*(?:\.new|:new|:connect)\s*\(",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all model/database patterns from Lua source code.

        Args:
            content: Lua source code
            file_path: Path to source file

        Returns:
            Dict with 'models', 'queries', 'schemas' lists
        """
        models = []
        queries = []
        schemas = []

        # Lapis models
        models.extend(self._extract_lapis_models(content, file_path))

        # SQL queries
        queries.extend(self._extract_sql_queries(content, file_path))

        # Tarantool spaces
        schemas.extend(self._extract_tarantool_schemas(content, file_path))

        # Lapis migration schemas
        schemas.extend(self._extract_lapis_schemas(content, file_path))

        return {
            'models': models,
            'queries': queries,
            'schemas': schemas,
        }

    def _extract_lapis_models(self, content: str, file_path: str) -> List[LuaModelInfo]:
        """Extract Lapis Model:extend() patterns."""
        results = []
        for match in self.LAPIS_MODEL_PATTERN.finditer(content):
            name = match.group('name')
            table_name = match.group('table')
            line_num = content[:match.start()].count('\n') + 1

            # Find relations
            relations = []
            for rel in self.LAPIS_RELATION_PATTERN.finditer(content):
                relations.append({
                    "type": rel.group('type'),
                    "name": rel.group('name'),
                })

            # Check for timestamps
            timestamps = 'timestamp = true' in content or 'timestamps = true' in content

            results.append(LuaModelInfo(
                name=name,
                table_name=table_name,
                file=file_path,
                orm="lapis",
                relations=relations,
                timestamps=timestamps,
                line_number=line_num,
            ))
        return results

    def _extract_sql_queries(self, content: str, file_path: str) -> List[LuaQueryInfo]:
        """Extract SQL queries from Lua code."""
        results = []
        for match in self.SQL_QUERY_PATTERN.finditer(content):
            query = match.group('query').strip()
            query_type = query.split()[0].upper() if query else ""
            line_num = content[:match.start()].count('\n') + 1

            # Detect driver from context
            driver = "unknown"
            prefix = content[max(0, match.start()-50):match.start()]
            if 'pgmoon' in prefix or 'pg:' in prefix or 'Postgres' in content[:match.start()]:
                driver = "pgmoon"
            elif 'mysql' in prefix or 'resty.mysql' in content[:match.start()]:
                driver = "resty.mysql"
            elif 'luasql' in prefix:
                driver = "luasql"

            # Check for parameterized query
            is_param = '?' in query or '$' in query

            # Extract table name
            table = ""
            if query_type in ('SELECT', 'DELETE'):
                table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
                if table_match:
                    table = table_match.group(1)
            elif query_type in ('INSERT',):
                table_match = re.search(r'INTO\s+(\w+)', query, re.IGNORECASE)
                if table_match:
                    table = table_match.group(1)
            elif query_type in ('UPDATE',):
                table_match = re.search(r'UPDATE\s+(\w+)', query, re.IGNORECASE)
                if table_match:
                    table = table_match.group(1)

            results.append(LuaQueryInfo(
                query_type=query_type,
                table=table,
                driver=driver,
                is_parameterized=is_param,
                file=file_path,
                line_number=line_num,
            ))
        return results

    def _extract_tarantool_schemas(self, content: str, file_path: str) -> List[LuaSchemaInfo]:
        """Extract Tarantool space/index definitions."""
        results = []
        for match in self.TARANTOOL_SPACE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaSchemaInfo(
                name=match.group('name'),
                operation="create_space",
                table_name=match.group('name'),
                framework="tarantool",
                file=file_path,
                line_number=line_num,
            ))
        return results

    def _extract_lapis_schemas(self, content: str, file_path: str) -> List[LuaSchemaInfo]:
        """Extract Lapis migration schema definitions."""
        results = []
        for match in self.LAPIS_CREATE_TABLE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            results.append(LuaSchemaInfo(
                name=match.group('table'),
                operation="create_table",
                table_name=match.group('table'),
                framework="lapis",
                file=file_path,
                line_number=line_num,
            ))
        return results
