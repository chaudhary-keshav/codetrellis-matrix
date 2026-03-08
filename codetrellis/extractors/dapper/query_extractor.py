"""
Dapper Query Extractor.

Extracts Dapper SQL queries, repository patterns, type handlers,
multi-mapping, stored procedures, and contrib extensions.

Supports Dapper 2.x + Dapper.Contrib, Dapper.FluentMap.
Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DapperQueryInfo:
    """Information about a Dapper query."""
    method_name: str = ""
    query_type: str = ""  # query, query-first, query-single, execute, execute-scalar, query-multiple
    sql_snippet: str = ""
    return_type: str = ""
    is_async: bool = False
    is_stored_procedure: bool = False
    has_parameters: bool = False
    has_transaction: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class DapperRepositoryInfo:
    """Information about a repository using Dapper."""
    name: str = ""
    interface_name: str = ""
    connection_type: str = ""  # SqlConnection, NpgsqlConnection, etc.
    query_count: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class DapperTypeHandlerInfo:
    """Information about a custom Dapper type handler."""
    name: str = ""
    handled_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class DapperMultiMappingInfo:
    """Information about a multi-mapping query."""
    types: List[str] = field(default_factory=list)
    return_type: str = ""
    split_on: str = ""
    file: str = ""
    line_number: int = 0


class DapperQueryExtractor:
    """Extracts Dapper queries and repository patterns."""

    # Query methods: connection.Query<T>(sql)
    QUERY_PATTERN = re.compile(
        r'\.\s*(Query|QueryFirst|QueryFirstOrDefault|QuerySingle|QuerySingleOrDefault'
        r'|QueryAsync|QueryFirstAsync|QueryFirstOrDefaultAsync|QuerySingleAsync|QuerySingleOrDefaultAsync)'
        r'\s*<\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    # Execute methods
    EXECUTE_PATTERN = re.compile(
        r'\.\s*(Execute|ExecuteAsync|ExecuteScalar|ExecuteScalarAsync'
        r'|ExecuteReader|ExecuteReaderAsync)'
        r'\s*(?:<\s*(\w+)\s*>)?\s*\(',
        re.MULTILINE
    )

    # QueryMultiple
    QUERY_MULTIPLE_PATTERN = re.compile(
        r'\.\s*(QueryMultiple|QueryMultipleAsync)\s*\(',
        re.MULTILINE
    )

    # Multi-mapping: Query<T1, T2, TReturn>(...)
    MULTI_MAP_PATTERN = re.compile(
        r'\.Query(?:Async)?\s*<\s*(\w+(?:\s*,\s*\w+){1,6})\s*>\s*\(',
        re.MULTILINE
    )

    # splitOn parameter
    SPLIT_ON_PATTERN = re.compile(
        r'splitOn\s*:\s*"([^"]*)"',
        re.MULTILINE
    )

    # Stored procedure
    STORED_PROC_PATTERN = re.compile(
        r'CommandType\s*\.\s*StoredProcedure',
        re.MULTILINE
    )

    # SQL string detection
    SQL_STRING_PATTERN = re.compile(
        r'(?:@"|"""|")\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|EXEC|CALL|WITH|MERGE)\b',
        re.MULTILINE | re.IGNORECASE
    )

    # TypeHandler
    TYPE_HANDLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*(?:<[^>]+>)?\s*:\s*SqlMapper\.TypeHandler\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Repository pattern
    REPOSITORY_PATTERN = re.compile(
        r'class\s+(\w+(?:Repository|Repo))\s*(?::\s*(\w+))?\b',
        re.MULTILINE
    )

    # Connection usage
    CONNECTION_PATTERNS = {
        'SqlConnection': re.compile(r'\bSqlConnection\b'),
        'NpgsqlConnection': re.compile(r'\bNpgsqlConnection\b'),
        'MySqlConnection': re.compile(r'\bMySqlConnection\b'),
        'SqliteConnection': re.compile(r'\bSqliteConnection\b'),
        'IDbConnection': re.compile(r'\bIDbConnection\b'),
    }

    # Dapper.Contrib - Get, Insert, Update, Delete
    CONTRIB_PATTERN = re.compile(
        r'\.\s*(Get|GetAll|Insert|Update|Delete|DeleteAll)\s*<\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    # Transaction
    TRANSACTION_PATTERN = re.compile(
        r'\bBeginTransaction\s*\(|IDbTransaction\b|\btransaction\s*:',
        re.MULTILINE
    )

    # DynamicParameters
    DYNAMIC_PARAMS_PATTERN = re.compile(
        r'\bDynamicParameters\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Dapper queries and patterns."""
        result: Dict[str, Any] = {
            'queries': [],
            'repositories': [],
            'type_handlers': [],
            'multi_mappings': [],
        }

        if not content or not content.strip():
            return result

        has_transaction = bool(self.TRANSACTION_PATTERN.search(content))

        # Query<T> calls
        for match in self.QUERY_PATTERN.finditer(content):
            method = match.group(1)
            return_type = match.group(2)
            line = content[:match.start()].count('\n') + 1

            query_type = "query"
            if "First" in method:
                query_type = "query-first"
            elif "Single" in method:
                query_type = "query-single"

            is_async = "Async" in method

            # Check for stored proc nearby
            after = content[match.end():match.end() + 300]
            is_sp = bool(self.STORED_PROC_PATTERN.search(after))

            result['queries'].append(DapperQueryInfo(
                method_name=method,
                query_type=query_type,
                return_type=return_type,
                is_async=is_async,
                is_stored_procedure=is_sp,
                has_parameters=bool(self.DYNAMIC_PARAMS_PATTERN.search(content)),
                has_transaction=has_transaction,
                file=file_path,
                line_number=line,
            ))

        # Execute calls
        for match in self.EXECUTE_PATTERN.finditer(content):
            method = match.group(1)
            return_type = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1

            query_type = "execute"
            if "Scalar" in method:
                query_type = "execute-scalar"
            elif "Reader" in method:
                query_type = "execute-reader"

            after = content[match.end():match.end() + 300]
            is_sp = bool(self.STORED_PROC_PATTERN.search(after))

            result['queries'].append(DapperQueryInfo(
                method_name=method,
                query_type=query_type,
                return_type=return_type,
                is_async="Async" in method,
                is_stored_procedure=is_sp,
                has_transaction=has_transaction,
                file=file_path,
                line_number=line,
            ))

        # QueryMultiple
        for match in self.QUERY_MULTIPLE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['queries'].append(DapperQueryInfo(
                method_name=match.group(1),
                query_type="query-multiple",
                is_async="Async" in match.group(1),
                has_transaction=has_transaction,
                file=file_path,
                line_number=line,
            ))

        # Contrib methods
        for match in self.CONTRIB_PATTERN.finditer(content):
            method = match.group(1)
            return_type = match.group(2)
            line = content[:match.start()].count('\n') + 1

            query_type = "execute" if method in ("Insert", "Update", "Delete", "DeleteAll") else "query"

            result['queries'].append(DapperQueryInfo(
                method_name=f"Contrib.{method}",
                query_type=query_type,
                return_type=return_type,
                file=file_path,
                line_number=line,
            ))

        # Multi-mapping
        for match in self.MULTI_MAP_PATTERN.finditer(content):
            types_str = match.group(1)
            types = [t.strip() for t in types_str.split(',')]
            if len(types) >= 2:
                line = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                split_match = self.SPLIT_ON_PATTERN.search(after)
                split_on = split_match.group(1) if split_match else ""

                result['multi_mappings'].append(DapperMultiMappingInfo(
                    types=types[:-1],  # last is return type
                    return_type=types[-1],
                    split_on=split_on,
                    file=file_path,
                    line_number=line,
                ))

        # Type handlers
        for match in self.TYPE_HANDLER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['type_handlers'].append(DapperTypeHandlerInfo(
                name=match.group(1),
                handled_type=match.group(2),
                file=file_path,
                line_number=line,
            ))

        # Repositories
        for match in self.REPOSITORY_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            interface_name = match.group(2) or ""
            conn_type = ""
            for ctype, cpat in self.CONNECTION_PATTERNS.items():
                if cpat.search(content):
                    conn_type = ctype
                    break
            result['repositories'].append(DapperRepositoryInfo(
                name=match.group(1),
                interface_name=interface_name,
                connection_type=conn_type,
                query_count=len(result['queries']),
                file=file_path,
                line_number=line,
            ))

        return result
