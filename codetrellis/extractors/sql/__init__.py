"""
CodeTrellis SQL Extractors Module v1.0

Provides comprehensive extractors for SQL language constructs across
all major SQL dialects: PostgreSQL, MySQL, SQL Server (T-SQL), Oracle (PL/SQL),
SQLite, MariaDB, and ANSI SQL.

Core Extractors:
- SQLTypeExtractor: tables, views, materialized views, custom types, domains, sequences
- SQLFunctionExtractor: stored procedures, functions, triggers, events
- SQLIndexExtractor: indexes, constraints, partitions, tablespaces
- SQLSecurityExtractor: roles, grants, RLS policies, audit trails
- SQLMigrationExtractor: migration patterns, schema versioning, changelog

Part of CodeTrellis v4.15 - SQL Language Support
"""

from .type_extractor import (
    SQLTypeExtractor,
    SQLTableInfo,
    SQLColumnInfo,
    SQLViewInfo,
    SQLMaterializedViewInfo,
    SQLCustomTypeInfo,
    SQLDomainInfo,
    SQLSequenceInfo,
    SQLSchemaInfo,
)
from .function_extractor import (
    SQLFunctionExtractor,
    SQLStoredProcInfo,
    SQLFunctionInfo,
    SQLTriggerInfo,
    SQLEventInfo,
    SQLParameterInfo,
)
from .index_extractor import (
    SQLIndexExtractor,
    SQLIndexInfo,
    SQLConstraintInfo,
    SQLPartitionInfo,
    SQLForeignKeyInfo,
)
from .security_extractor import (
    SQLSecurityExtractor,
    SQLRoleInfo,
    SQLGrantInfo,
    SQLRLSPolicyInfo,
)
from .migration_extractor import (
    SQLMigrationExtractor,
    SQLMigrationInfo,
)

__all__ = [
    # Type extractors
    'SQLTypeExtractor', 'SQLTableInfo', 'SQLColumnInfo', 'SQLViewInfo',
    'SQLMaterializedViewInfo', 'SQLCustomTypeInfo', 'SQLDomainInfo',
    'SQLSequenceInfo', 'SQLSchemaInfo',
    # Function extractors
    'SQLFunctionExtractor', 'SQLStoredProcInfo', 'SQLFunctionInfo',
    'SQLTriggerInfo', 'SQLEventInfo', 'SQLParameterInfo',
    # Index extractors
    'SQLIndexExtractor', 'SQLIndexInfo', 'SQLConstraintInfo',
    'SQLPartitionInfo', 'SQLForeignKeyInfo',
    # Security extractors
    'SQLSecurityExtractor', 'SQLRoleInfo', 'SQLGrantInfo', 'SQLRLSPolicyInfo',
    # Migration extractors
    'SQLMigrationExtractor', 'SQLMigrationInfo',
]
