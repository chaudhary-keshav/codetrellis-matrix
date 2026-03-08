"""
EnhancedEFCoreParser v1.0 - Comprehensive per-file Entity Framework Core parser.

Supports EF Core 2.x through 9.x features including:
- DbContext, DbSet, OnModelCreating
- Migrations (Up/Down, operations)
- Fluent API relationships (HasOne/HasMany/WithOne/WithMany)
- Value conversions, query filters
- Interceptors (command, save changes, connection, transaction)
- Compiled queries, raw SQL
- Database providers (SQL Server, PostgreSQL, MySQL, SQLite, Cosmos, InMemory)
- TPH/TPT/TPC inheritance mapping
- Owned types, keyless entities
- Seed data (HasData)

Part of CodeTrellis v4.96 - .NET Framework Enhanced Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .extractors.efcore import (
    EFCoreContextExtractor,
    EFCoreDbContextInfo,
    EFCoreDbSetInfo,
    EFCoreMigrationInfo,
    EFCoreModelExtractor,
    EFCoreEntityInfo,
    EFCoreRelationshipInfo,
    EFCoreValueConversionInfo,
    EFCoreQueryExtractor,
    EFCoreQueryFilterInfo,
    EFCoreInterceptorInfo,
)


@dataclass
class EFCoreParseResult:
    """Complete parse result for an EF Core file."""
    file_path: str
    file_type: str = "unknown"  # context, migration, entity_config, model, repository

    # DbContext
    db_contexts: List[EFCoreDbContextInfo] = field(default_factory=list)
    migrations: List[EFCoreMigrationInfo] = field(default_factory=list)

    # Models
    relationships: List[EFCoreRelationshipInfo] = field(default_factory=list)
    value_conversions: List[EFCoreValueConversionInfo] = field(default_factory=list)
    entity_configs: List[Dict] = field(default_factory=list)

    # Queries
    query_filters: List[EFCoreQueryFilterInfo] = field(default_factory=list)
    interceptors: List[EFCoreInterceptorInfo] = field(default_factory=list)
    compiled_queries: int = 0
    raw_sql_count: int = 0
    uses_no_tracking: bool = False
    uses_split_query: bool = False

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    efcore_version: str = ""
    database_provider: str = ""
    total_db_sets: int = 0
    total_migrations: int = 0


class EnhancedEFCoreParser:
    """Enhanced per-file EF Core parser."""

    FRAMEWORK_PATTERNS = {
        'efcore': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\b', re.MULTILINE),
        'efcore-design': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\.Design\b', re.MULTILINE),
        'efcore-migrations': re.compile(r'using\s+Microsoft\.EntityFrameworkCore\.Migrations\b', re.MULTILINE),
        'efcore-sqlserver': re.compile(r'UseSqlServer|Microsoft\.EntityFrameworkCore\.SqlServer', re.MULTILINE),
        'efcore-npgsql': re.compile(r'UseNpgsql|Npgsql\.EntityFrameworkCore', re.MULTILINE),
        'efcore-mysql': re.compile(r'UseMySql|Pomelo\.EntityFrameworkCore\.MySql', re.MULTILINE),
        'efcore-sqlite': re.compile(r'UseSqlite|Microsoft\.EntityFrameworkCore\.Sqlite', re.MULTILINE),
        'efcore-cosmos': re.compile(r'UseCosmos|Microsoft\.EntityFrameworkCore\.Cosmos', re.MULTILINE),
        'efcore-inmemory': re.compile(r'UseInMemoryDatabase', re.MULTILINE),
        'efcore-proxies': re.compile(r'UseLazyLoadingProxies', re.MULTILINE),
        'efcore-temporal': re.compile(r'IsTemporal|TemporalAsOf|TemporalAll', re.MULTILINE),
    }

    VERSION_FEATURES = {
        'IsTemporal': '6.0',
        'TemporalAsOf': '6.0',
        'ExecuteUpdate': '7.0',
        'ExecuteDelete': '7.0',
        'UseSeeding': '9.0',
        'UseAsyncSeeding': '9.0',
        'HierarchyId': '8.0',
        'ComplexProperty': '8.0',
        'ToJson': '7.0',
        'TPC': '7.0',
        'HasTrigger': '7.0',
        'HasConversion': '2.1',
        'HasQueryFilter': '2.0',
        'AsSplitQuery': '5.0',
        'AsNoTrackingWithIdentityResolution': '5.0',
        'FromSqlInterpolated': '3.0',
        'IDbContextFactory': '5.0',
        'compiled query': '2.0',
    }

    def __init__(self):
        self.context_extractor = EFCoreContextExtractor()
        self.model_extractor = EFCoreModelExtractor()
        self.query_extractor = EFCoreQueryExtractor()

    def parse(self, content: str, file_path: str = "") -> EFCoreParseResult:
        result = EFCoreParseResult(file_path=file_path)
        if not content or not content.strip():
            return result

        result.file_type = self._classify_file(file_path, content)
        result.detected_frameworks = self._detect_frameworks(content)

        ctx_result = self.context_extractor.extract(content, file_path)
        result.db_contexts = ctx_result.get('db_contexts', [])
        result.migrations = ctx_result.get('migrations', [])
        result.database_provider = ctx_result.get('database_provider', '')
        result.total_db_sets = sum(len(c.db_sets) for c in result.db_contexts)
        result.total_migrations = len(result.migrations)

        model_result = self.model_extractor.extract(content, file_path)
        result.relationships = model_result.get('relationships', [])
        result.value_conversions = model_result.get('value_conversions', [])
        result.entity_configs = model_result.get('entity_configs', [])

        query_result = self.query_extractor.extract(content, file_path)
        result.query_filters = query_result.get('query_filters', [])
        result.interceptors = query_result.get('interceptors', [])
        result.compiled_queries = query_result.get('compiled_queries', 0)
        result.raw_sql_count = query_result.get('raw_sql_count', 0)
        result.uses_no_tracking = query_result.get('uses_no_tracking', False)
        result.uses_split_query = query_result.get('uses_split_query', False)

        result.efcore_version = self._detect_version(content)
        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""
        if 'dbcontext' in basename or 'context' in basename:
            return 'context'
        if '/migrations/' in normalized or 'migration' in basename:
            return 'migration'
        if 'configuration' in basename and 'IEntityTypeConfiguration' in content:
            return 'entity_config'
        if 'repository' in basename:
            return 'repository'
        if 'DbContext' in content:
            return 'context'
        if ': Migration' in content:
            return 'migration'
        return 'model'

    def _detect_frameworks(self, content: str) -> List[str]:
        return [fw for fw, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        max_v = '0.0'
        for feat, ver in self.VERSION_FEATURES.items():
            if feat in content:
                parts_f = [int(x) for x in ver.split('.')]
                parts_m = [int(x) for x in max_v.split('.')]
                if parts_f > parts_m:
                    max_v = ver
        return max_v if max_v != '0.0' else ''

    def is_efcore_file(self, content: str, file_path: str = "") -> bool:
        if re.search(r'using\s+Microsoft\.EntityFrameworkCore\b', content):
            return True
        if 'DbContext' in content or 'DbSet<' in content:
            return True
        if ': Migration' in content:
            return True
        if 'IEntityTypeConfiguration' in content:
            return True
        return False
