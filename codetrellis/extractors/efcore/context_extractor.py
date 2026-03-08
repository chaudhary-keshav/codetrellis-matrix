"""
EF Core DbContext & Migration Extractor.

Extracts DbContext definitions, DbSet declarations, OnModelCreating configuration,
migration history, and database provider settings.

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EFCoreDbSetInfo:
    """Information about a DbSet property."""
    property_name: str = ""
    entity_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EFCoreDbContextInfo:
    """Information about a DbContext class."""
    name: str = ""
    base_class: str = ""  # DbContext, IdentityDbContext, etc.
    db_sets: List[EFCoreDbSetInfo] = field(default_factory=list)
    has_on_model_creating: bool = False
    uses_fluent_api: bool = False
    uses_data_annotations: bool = False
    database_provider: str = ""  # SqlServer, PostgreSQL, MySQL, SQLite, Cosmos, InMemory
    has_seed_data: bool = False
    has_query_filters: bool = False
    has_interceptors: bool = False
    connection_string_name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EFCoreMigrationInfo:
    """Information about an EF Core migration."""
    name: str = ""
    migration_id: str = ""
    has_up: bool = False
    has_down: bool = False
    operations: List[str] = field(default_factory=list)  # CreateTable, AddColumn, etc.
    file: str = ""
    line_number: int = 0


class EFCoreContextExtractor:
    """Extracts EF Core DbContext and migration information."""

    # DbContext class
    DBCONTEXT_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*(DbContext|IdentityDbContext(?:<[^>]+>)?|ApiAuthorizationDbContext(?:<[^>]+>)?)',
        re.MULTILINE
    )

    # DbSet<T> property
    DBSET_PATTERN = re.compile(
        r'(?:public\s+)?(?:virtual\s+)?DbSet\s*<\s*(\w+)\s*>\s+(\w+)\s*\{',
        re.MULTILINE
    )

    # OnModelCreating override
    ON_MODEL_CREATING_PATTERN = re.compile(
        r'protected\s+override\s+void\s+OnModelCreating\s*\(\s*ModelBuilder',
        re.MULTILINE
    )

    # Fluent API patterns inside OnModelCreating
    FLUENT_API_PATTERNS = [
        re.compile(r'modelBuilder\s*\.\s*Entity\s*<', re.MULTILINE),
        re.compile(r'\.HasKey\(', re.MULTILINE),
        re.compile(r'\.HasOne\(', re.MULTILINE),
        re.compile(r'\.HasMany\(', re.MULTILINE),
        re.compile(r'\.HasIndex\(', re.MULTILINE),
        re.compile(r'\.Property\(', re.MULTILINE),
        re.compile(r'\.ToTable\(', re.MULTILINE),
    ]

    # Database provider patterns
    PROVIDER_PATTERNS = {
        'SqlServer': re.compile(r'UseSqlServer|Microsoft\.EntityFrameworkCore\.SqlServer', re.MULTILINE),
        'PostgreSQL': re.compile(r'UseNpgsql|Npgsql\.EntityFrameworkCore\.PostgreSQL', re.MULTILINE),
        'MySQL': re.compile(r'UseMySql|Pomelo\.EntityFrameworkCore\.MySql|MySql\.EntityFrameworkCore', re.MULTILINE),
        'SQLite': re.compile(r'UseSqlite|Microsoft\.EntityFrameworkCore\.Sqlite', re.MULTILINE),
        'Cosmos': re.compile(r'UseCosmos|Microsoft\.EntityFrameworkCore\.Cosmos', re.MULTILINE),
        'InMemory': re.compile(r'UseInMemoryDatabase|Microsoft\.EntityFrameworkCore\.InMemory', re.MULTILINE),
    }

    # HasData seed
    HAS_DATA_PATTERN = re.compile(r'\.HasData\s*\(', re.MULTILINE)

    # HasQueryFilter
    QUERY_FILTER_PATTERN = re.compile(r'\.HasQueryFilter\s*\(', re.MULTILINE)

    # Migration class
    MIGRATION_PATTERN = re.compile(
        r'\[Migration\(["\']([^"\']+)["\']\)\]\s*(?:public\s+)?(?:partial\s+)?class\s+(\w+)\s*:\s*Migration',
        re.MULTILINE
    )

    # Migration operations
    MIGRATION_OP_PATTERNS = {
        'CreateTable': re.compile(r'migrationBuilder\.CreateTable', re.MULTILINE),
        'DropTable': re.compile(r'migrationBuilder\.DropTable', re.MULTILINE),
        'AddColumn': re.compile(r'migrationBuilder\.AddColumn', re.MULTILINE),
        'DropColumn': re.compile(r'migrationBuilder\.DropColumn', re.MULTILINE),
        'AlterColumn': re.compile(r'migrationBuilder\.AlterColumn', re.MULTILINE),
        'CreateIndex': re.compile(r'migrationBuilder\.CreateIndex', re.MULTILINE),
        'DropIndex': re.compile(r'migrationBuilder\.DropIndex', re.MULTILINE),
        'AddForeignKey': re.compile(r'migrationBuilder\.AddForeignKey', re.MULTILINE),
        'AddPrimaryKey': re.compile(r'migrationBuilder\.AddPrimaryKey', re.MULTILINE),
        'RenameTable': re.compile(r'migrationBuilder\.RenameTable', re.MULTILINE),
        'RenameColumn': re.compile(r'migrationBuilder\.RenameColumn', re.MULTILINE),
        'Sql': re.compile(r'migrationBuilder\.Sql\(', re.MULTILINE),
    }

    # Connection string pattern
    CONNECTION_STRING_PATTERN = re.compile(
        r'(?:UseSqlServer|UseNpgsql|UseMySql|UseSqlite|UseCosmos)\s*\(\s*'
        r'(?:(?:\w+\.)?(?:Configuration|GetConnectionString)\s*(?:\[\s*["\']([^"\']+)["\']\]|'
        r'\(\s*["\']([^"\']+)["\']\s*\)))',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract EF Core DbContext and migration information."""
        result = {
            'db_contexts': [],
            'migrations': [],
            'database_provider': '',
        }

        if not content or not content.strip():
            return result

        # Detect database provider
        for provider, pattern in self.PROVIDER_PATTERNS.items():
            if pattern.search(content):
                result['database_provider'] = provider
                break

        # Extract DbContext classes
        for match in self.DBCONTEXT_PATTERN.finditer(content):
            ctx_name = match.group(1)
            base_class = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Extract DbSets
            db_sets = []
            for ds_match in self.DBSET_PATTERN.finditer(content):
                ds_line = content[:ds_match.start()].count('\n') + 1
                db_sets.append(EFCoreDbSetInfo(
                    property_name=ds_match.group(2),
                    entity_type=ds_match.group(1),
                    file=file_path,
                    line_number=ds_line,
                ))

            has_model_creating = bool(self.ON_MODEL_CREATING_PATTERN.search(content))
            uses_fluent = any(p.search(content) for p in self.FLUENT_API_PATTERNS)
            has_seed = bool(self.HAS_DATA_PATTERN.search(content))
            has_filters = bool(self.QUERY_FILTER_PATTERN.search(content))

            # Connection string
            conn_match = self.CONNECTION_STRING_PATTERN.search(content)
            conn_name = (conn_match.group(1) or conn_match.group(2)) if conn_match else ""

            result['db_contexts'].append(EFCoreDbContextInfo(
                name=ctx_name,
                base_class=base_class,
                db_sets=db_sets,
                has_on_model_creating=has_model_creating,
                uses_fluent_api=uses_fluent,
                database_provider=result['database_provider'],
                has_seed_data=has_seed,
                has_query_filters=has_filters,
                connection_string_name=conn_name,
                file=file_path,
                line_number=line,
            ))

        # Extract migrations
        for match in self.MIGRATION_PATTERN.finditer(content):
            migration_id = match.group(1)
            name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            operations = []
            for op_name, op_pattern in self.MIGRATION_OP_PATTERNS.items():
                if op_pattern.search(content):
                    operations.append(op_name)

            has_up = bool(re.search(r'protected\s+override\s+void\s+Up\s*\(', content))
            has_down = bool(re.search(r'protected\s+override\s+void\s+Down\s*\(', content))

            result['migrations'].append(EFCoreMigrationInfo(
                name=name,
                migration_id=migration_id,
                has_up=has_up,
                has_down=has_down,
                operations=operations,
                file=file_path,
                line_number=line,
            ))

        return result
