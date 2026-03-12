"""
Enhanced Ecto Parser for CodeTrellis

Self-contained framework parser for Ecto (Elixir database wrapper/query generator).
Detects and extracts:
- Schema definitions (fields, associations, embeds, timestamps)
- Changeset pipelines (cast, validate, constraints)
- Migration operations (create_table, alter, add_column, create_index)
- Query patterns (from, join, where, select, preload)
- Repo operations (get, all, insert, update, delete)
- Multi/transaction patterns
- Custom Ecto types

Ecto versions: 1.0–3.11+ (detects based on features)

Reference pattern: Rails parser (self-contained framework file)

Part of CodeTrellis - Ecto Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class EctoSchemaFieldInfo:
    """Information about an Ecto schema field."""
    name: str
    type: str = ""
    field_type: str = "field"  # field, belongs_to, has_one, has_many, many_to_many, embeds_one, embeds_many
    options: str = ""
    line_number: int = 0


@dataclass
class EctoSchemaInfo:
    """Information about an Ecto schema."""
    name: str
    table: str = ""
    fields: List[EctoSchemaFieldInfo] = field(default_factory=list)
    primary_key: str = ""
    has_timestamps: bool = False
    schema_type: str = "schema"  # schema, embedded_schema
    derives: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class EctoChangesetInfo:
    """Information about an Ecto changeset function."""
    name: str
    cast_fields: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class EctoMigrationInfo:
    """Information about an Ecto migration."""
    name: str
    version: str = ""
    operations: List[str] = field(default_factory=list)
    tables_created: List[str] = field(default_factory=list)
    tables_altered: List[str] = field(default_factory=list)
    indexes_created: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class EctoQueryInfo:
    """Information about an Ecto query pattern."""
    name: str
    query_type: str = ""  # from, join, where, select, preload, subquery
    source: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EctoRepoCallInfo:
    """Information about a Repo operation call."""
    operation: str  # get, get!, all, one, insert, update, delete, aggregate, preload
    schema: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EctoMultiInfo:
    """Information about an Ecto.Multi transaction."""
    name: str
    steps: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class EctoCustomTypeInfo:
    """Information about a custom Ecto type."""
    name: str
    base_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EctoParseResult:
    """Complete parse result for an Ecto file."""
    file_path: str
    file_type: str = "elixir"

    # Schemas
    schemas: List[EctoSchemaInfo] = field(default_factory=list)

    # Changesets
    changesets: List[EctoChangesetInfo] = field(default_factory=list)

    # Migrations
    migrations: List[EctoMigrationInfo] = field(default_factory=list)

    # Queries
    queries: List[EctoQueryInfo] = field(default_factory=list)

    # Repo operations
    repo_calls: List[EctoRepoCallInfo] = field(default_factory=list)

    # Multi / transactions
    multis: List[EctoMultiInfo] = field(default_factory=list)

    # Custom types
    custom_types: List[EctoCustomTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    ecto_version: str = ""
    has_soft_delete: bool = False
    has_multi: bool = False
    total_schemas: int = 0
    total_migrations: int = 0


# ── Parser ───────────────────────────────────────────────────────────────────

class EnhancedEctoParser:
    """
    Enhanced Ecto framework parser for CodeTrellis.

    Self-contained parser that extracts Ecto-specific patterns from Elixir files.
    Only populates results if Ecto framework is detected in the file content.
    """

    # Ecto framework detection
    ECTO_REQUIRE = re.compile(
        r'use\s+Ecto\.\w+|'
        r'Ecto\.Schema|Ecto\.Changeset|Ecto\.Query|'
        r'Ecto\.Repo|Ecto\.Migration|Ecto\.Multi|Ecto\.Type|'
        r'@behaviour\s+Ecto\.\w+|'
        r'schema\s+"[^"]+"\s+do|embedded_schema\s+do|'
        r'import\s+Ecto\.(?:Query|Changeset)|'
        r'Repo\.(?:get|all|one|insert|update|delete|aggregate|preload)',
        re.MULTILINE,
    )

    # ── Schema patterns ──────────────────────────────────────────────────

    SCHEMA_RE = re.compile(
        r'^\s*schema\s+"([^"]+)"\s+do\b',
        re.MULTILINE,
    )

    EMBEDDED_SCHEMA_RE = re.compile(
        r'^\s*embedded_schema\s+do\b',
        re.MULTILINE,
    )

    SCHEMA_FIELD_RE = re.compile(
        r'^\s*(field|belongs_to|has_one|has_many|many_to_many|embeds_one|embeds_many)\s+:(\w+)(?:\s*,\s*:?(\w[\w.]*))?(?:\s*,\s*(.+))?$',
        re.MULTILINE,
    )

    TIMESTAMPS_RE = re.compile(r'^\s*timestamps\b', re.MULTILINE)

    PRIMARY_KEY_RE = re.compile(
        r'@primary_key\s+\{:(\w+)\s*,\s*:?(\w+)',
        re.MULTILINE,
    )

    DERIVE_RE = re.compile(
        r'@derive\s+(?:\{?([\w.]+)|(\[.+?\]))',
        re.MULTILINE,
    )

    # ── Changeset patterns ───────────────────────────────────────────────

    CHANGESET_RE = re.compile(
        r'^\s*def\s+(\w*changeset\w*)\s*\(',
        re.MULTILINE,
    )

    CAST_RE = re.compile(
        r'\|>\s*cast\(\s*(?:\w+\s*,\s*)?\[([^\]]*)\]',
    )

    VALIDATE_REQUIRED_RE = re.compile(
        r'\|>\s*validate_required\(\s*\[([^\]]*)\]',
    )

    VALIDATION_RE = re.compile(
        r'\|>\s*(validate_\w+|check_constraint|unique_constraint|'
        r'foreign_key_constraint|no_assoc_constraint|exclusion_constraint|'
        r'assoc_constraint|unsafe_validate_unique)\(',
    )

    CONSTRAINT_RE = re.compile(
        r'\|>\s*(unique_constraint|foreign_key_constraint|'
        r'check_constraint|exclusion_constraint|no_assoc_constraint)\(\s*:?(\w+)',
    )

    # ── Migration patterns ───────────────────────────────────────────────

    MIGRATION_RE = re.compile(
        r'defmodule\s+([\w.]+)\s+do\s*\n\s*use\s+Ecto\.Migration',
        re.MULTILINE,
    )

    CREATE_TABLE_RE = re.compile(
        r'create\s+table\(\s*:(\w+)',
        re.MULTILINE,
    )

    ALTER_TABLE_RE = re.compile(
        r'alter\s+table\(\s*:(\w+)',
        re.MULTILINE,
    )

    CREATE_INDEX_RE = re.compile(
        r'create\s+(?:unique\s+)?index\(\s*:(\w+)\s*,\s*\[([^\]]*)\]',
        re.MULTILINE,
    )

    MIGRATION_OP_RE = re.compile(
        r'^\s*(add|remove|modify|rename|timestamps|execute|flush)\b',
        re.MULTILINE,
    )

    # ── Query patterns ───────────────────────────────────────────────────

    QUERY_FROM_RE = re.compile(
        r'from\(?\s*(\w+)\s+in\s+"?(\w[\w.]*)"?',
        re.MULTILINE,
    )

    QUERY_JOIN_RE = re.compile(
        r'(join|left_join|right_join|cross_join|inner_join|full_join)\s*:',
        re.MULTILINE,
    )

    QUERY_PRELOAD_RE = re.compile(
        r'preload\(\s*(?:\w+\s*,\s*)?\[?:?(\w+)',
        re.MULTILINE,
    )

    # ── Repo patterns ────────────────────────────────────────────────────

    REPO_CALL_RE = re.compile(
        r'Repo\.(get!?|get_by!?|all|one!?|insert!?|update!?|delete!?|'
        r'insert_or_update!?|insert_all|update_all|delete_all|'
        r'aggregate|preload|exists\?|reload!?)\(',
        re.MULTILINE,
    )

    # ── Multi patterns ───────────────────────────────────────────────────

    MULTI_NEW_RE = re.compile(
        r'(?:Ecto\.Multi\.new|Multi\.new)\(\)',
        re.MULTILINE,
    )

    MULTI_STEP_RE = re.compile(
        r'\|>\s*(?:Ecto\.)?Multi\.(insert|update|delete|run|one|all|'
        r'insert_or_update|update_all|delete_all|put|merge|append)\(\s*:(\w+)',
        re.MULTILINE,
    )

    # ── Custom type patterns ─────────────────────────────────────────────

    CUSTOM_TYPE_RE = re.compile(
        r'use\s+Ecto\.Type|@behaviour\s+Ecto\.Type',
        re.MULTILINE,
    )

    # ── Version detection ────────────────────────────────────────────────

    VERSION_FEATURES = [
        ('3.12', re.compile(r'Ecto\.Query\.with_named_binding|Ecto\.Query\.has_named_binding\?', re.MULTILINE)),
        ('3.11', re.compile(r'Ecto\.Enum|parameterized_type|dump_embed', re.MULTILINE)),
        ('3.10', re.compile(r'Ecto\.Query\.dynamic|exists\?', re.MULTILINE)),
        ('3.9', re.compile(r'Ecto\.Multi\.put|Ecto\.Changeset\.traverse_errors', re.MULTILINE)),
        ('3.0', re.compile(r'Ecto\.Schema\.__schema__|Ecto\.Query\.API', re.MULTILINE)),
        ('2.0', re.compile(r'Ecto\.Multi|Ecto\.Changeset\.change', re.MULTILINE)),
        ('1.0', re.compile(r'Ecto\.Schema|Ecto\.Changeset', re.MULTILINE)),
    ]

    def parse(self, content: str, file_path: str = "") -> EctoParseResult:
        """Parse Elixir source code for Ecto-specific patterns."""
        result = EctoParseResult(file_path=file_path)

        # Check if this file uses Ecto
        if not self.ECTO_REQUIRE.search(content):
            return result

        # Detect version
        result.ecto_version = self._detect_version(content)

        # Feature flags
        result.has_soft_delete = bool(re.search(r'soft_delete|deleted_at|paranoid', content))
        result.has_multi = bool(self.MULTI_NEW_RE.search(content))

        # Extract all patterns
        self._extract_schemas(content, file_path, result)
        self._extract_changesets(content, file_path, result)
        self._extract_migrations(content, file_path, result)
        self._extract_queries(content, file_path, result)
        self._extract_repo_calls(content, file_path, result)
        self._extract_multis(content, file_path, result)
        self._extract_custom_types(content, file_path, result)

        # Update totals
        result.total_schemas = len(result.schemas)
        result.total_migrations = len(result.migrations)

        return result

    def _detect_version(self, content: str) -> str:
        """Detect Ecto version based on features used."""
        for version, pattern in self.VERSION_FEATURES:
            if pattern.search(content):
                return version
        return ""

    def _find_enclosing_module(self, content: str, pos: int) -> str:
        """Find the nearest enclosing defmodule name."""
        prefix = content[:pos]
        modules = re.findall(r'defmodule\s+([\w.]+)\s+do', prefix)
        return modules[-1] if modules else "Unknown"

    def _extract_block(self, content: str, start: int) -> str:
        """Extract content up to matching end keyword."""
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            rest = content[pos:]
            if re.match(r'\b(do|fn)\b', rest):
                depth += 1
                pos += 2
            elif re.match(r'\bend\b', rest):
                depth -= 1
                if depth == 0:
                    return content[start:pos]
                pos += 3
            else:
                pos += 1
        return content[start:min(start + 1000, len(content))]

    def _extract_schemas(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Ecto schema definitions."""
        for m in self.SCHEMA_RE.finditer(content):
            table = m.group(1)
            line = content[:m.start()].count('\n') + 1
            module = self._find_enclosing_module(content, m.start())

            block = self._extract_block(content, m.end())
            fields = self._extract_schema_fields(block, line)
            has_timestamps = bool(self.TIMESTAMPS_RE.search(block))

            # Primary key
            pk_match = self.PRIMARY_KEY_RE.search(content[:m.start()])
            primary_key = pk_match.group(1) if pk_match else "id"

            # Derives
            derives = [d.group(1) or d.group(2) for d in self.DERIVE_RE.finditer(content[:m.start()])]

            result.schemas.append(EctoSchemaInfo(
                name=module,
                table=table,
                fields=fields[:50],
                primary_key=primary_key,
                has_timestamps=has_timestamps,
                schema_type="schema",
                derives=derives[:10],
                file=file_path,
                line_number=line,
            ))

        for m in self.EMBEDDED_SCHEMA_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            module = self._find_enclosing_module(content, m.start())
            block = self._extract_block(content, m.end())
            fields = self._extract_schema_fields(block, line)

            result.schemas.append(EctoSchemaInfo(
                name=module,
                table="",
                fields=fields[:50],
                schema_type="embedded_schema",
                file=file_path,
                line_number=line,
            ))

    def _extract_schema_fields(self, block: str, base_line: int) -> List[EctoSchemaFieldInfo]:
        """Extract fields from a schema block."""
        fields = []
        for m in self.SCHEMA_FIELD_RE.finditer(block):
            field_type = m.group(1)
            name = m.group(2)
            data_type = m.group(3) or ""
            options = (m.group(4) or "").strip()
            line = base_line + block[:m.start()].count('\n')

            fields.append(EctoSchemaFieldInfo(
                name=name,
                type=data_type,
                field_type=field_type,
                options=options[:80],
                line_number=line,
            ))

        # Timestamps
        if self.TIMESTAMPS_RE.search(block):
            fields.append(EctoSchemaFieldInfo(name="inserted_at", type="naive_datetime", field_type="timestamps"))
            fields.append(EctoSchemaFieldInfo(name="updated_at", type="naive_datetime", field_type="timestamps"))

        return fields

    def _extract_changesets(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Ecto changeset functions."""
        for m in self.CHANGESET_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            func_block = self._extract_block(content, m.end())

            cast_fields = []
            cast_m = self.CAST_RE.search(func_block)
            if cast_m:
                cast_fields = [f.strip().lstrip(':') for f in cast_m.group(1).split(',') if f.strip()]

            required_fields = []
            req_m = self.VALIDATE_REQUIRED_RE.search(func_block)
            if req_m:
                required_fields = [f.strip().lstrip(':') for f in req_m.group(1).split(',') if f.strip()]

            validations = [v.group(1) for v in self.VALIDATION_RE.finditer(func_block)]
            constraints = [c.group(1) for c in self.CONSTRAINT_RE.finditer(func_block)]

            result.changesets.append(EctoChangesetInfo(
                name=name,
                cast_fields=cast_fields[:30],
                required_fields=required_fields[:30],
                validations=validations[:20],
                constraints=constraints[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_migrations(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Ecto migration definitions."""
        for m in self.MIGRATION_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Extract version from module name (e.g., V20230101120000)
            version_match = re.search(r'(\d{14})', name)
            version = version_match.group(1) if version_match else ""

            tables_created = [t.group(1) for t in self.CREATE_TABLE_RE.finditer(content)]
            tables_altered = [t.group(1) for t in self.ALTER_TABLE_RE.finditer(content)]
            indexes = [f"{i.group(1)}({i.group(2)})" for i in self.CREATE_INDEX_RE.finditer(content)]
            operations = [o.group(1) for o in self.MIGRATION_OP_RE.finditer(content)]

            result.migrations.append(EctoMigrationInfo(
                name=name,
                version=version,
                operations=list(set(operations))[:20],
                tables_created=tables_created[:20],
                tables_altered=tables_altered[:20],
                indexes_created=indexes[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_queries(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Ecto query patterns."""
        for m in self.QUERY_FROM_RE.finditer(content):
            var = m.group(1)
            source = m.group(2)
            line = content[:m.start()].count('\n') + 1

            result.queries.append(EctoQueryInfo(
                name=f"from {var} in {source}",
                query_type="from",
                source=source,
                file=file_path,
                line_number=line,
            ))

        for m in self.QUERY_JOIN_RE.finditer(content):
            join_type = m.group(1)
            line = content[:m.start()].count('\n') + 1
            result.queries.append(EctoQueryInfo(
                name=join_type,
                query_type="join",
                file=file_path,
                line_number=line,
            ))

    def _extract_repo_calls(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Repo operation calls."""
        for m in self.REPO_CALL_RE.finditer(content):
            operation = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Try to detect schema being operated on
            after = content[m.end():m.end() + 60]
            schema_match = re.match(r'\s*([\w.]+)', after)
            schema = schema_match.group(1) if schema_match else ""

            result.repo_calls.append(EctoRepoCallInfo(
                operation=operation,
                schema=schema,
                file=file_path,
                line_number=line,
            ))

    def _extract_multis(self, content: str, file_path: str, result: EctoParseResult):
        """Extract Ecto.Multi transaction patterns."""
        if not self.MULTI_NEW_RE.search(content):
            return

        for m in self.MULTI_NEW_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            func_name = self._find_enclosing_function(content, m.start())

            # Find Multi steps after this point
            steps = []
            search_area = content[m.start():m.start() + 1000]
            for step in self.MULTI_STEP_RE.finditer(search_area):
                steps.append(f"{step.group(1)}:{step.group(2)}")

            result.multis.append(EctoMultiInfo(
                name=func_name,
                steps=steps[:20],
                file=file_path,
                line_number=line,
            ))

    def _extract_custom_types(self, content: str, file_path: str, result: EctoParseResult):
        """Extract custom Ecto type definitions."""
        if not self.CUSTOM_TYPE_RE.search(content):
            return

        module = self._find_enclosing_module(content, 0)
        line_match = self.CUSTOM_TYPE_RE.search(content)
        line = content[:line_match.start()].count('\n') + 1 if line_match else 1

        # Try to detect base type from type/0 callback
        base_type_match = re.search(r'def\s+type\b.*?:(\w+)', content)
        base_type = base_type_match.group(1) if base_type_match else ""

        result.custom_types.append(EctoCustomTypeInfo(
            name=module,
            base_type=base_type,
            file=file_path,
            line_number=line,
        ))

    def _find_enclosing_function(self, content: str, pos: int) -> str:
        """Find the nearest enclosing def name."""
        prefix = content[:pos]
        funcs = re.findall(r'def\s+(\w+)\s*\(', prefix)
        return funcs[-1] if funcs else "unknown"
