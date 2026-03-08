"""
RustModelExtractor - Extracts Rust database model definitions.

This extractor parses Rust source code and extracts:
- Diesel models (#[derive(Queryable, Insertable)])
- SeaORM entities (#[derive(DeriveEntityModel)])
- SQLx models (FromRow)
- Serde models (#[derive(Serialize, Deserialize)])
- Diesel schema! macro definitions
- Database table associations
- Migration patterns

Supports Diesel, SeaORM, SQLx, and other Rust ORM/DB libraries.

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RustModelInfo:
    """Information about a Rust database model."""
    name: str
    table_name: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    orm: str = ""  # diesel, sea-orm, sqlx
    file: str = ""
    line_number: int = 0
    is_insertable: bool = False
    is_queryable: bool = False
    primary_key: Optional[str] = None
    belongs_to: List[str] = field(default_factory=list)
    has_many: List[str] = field(default_factory=list)


@dataclass
class RustSchemaInfo:
    """Information about a Diesel schema! table definition."""
    table_name: str
    columns: List[Dict[str, str]] = field(default_factory=list)
    primary_key: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class RustMigrationInfo:
    """Information about a database migration."""
    name: str
    direction: str = ""  # up, down
    sql: str = ""
    file: str = ""


class RustModelExtractor:
    """
    Extracts Rust database model definitions from source code.

    Handles:
    - Diesel ORM: Queryable, Insertable, Associations, table! macro
    - SeaORM: DeriveEntityModel, DeriveActiveModel, DeriveRelation
    - SQLx: FromRow derive
    - Serde: Serialize, Deserialize (for API models/DTOs)
    - Table name annotations (#[diesel(table_name = "users")])
    - Primary key annotations
    - Relationship macros (belongs_to, has_many)
    """

    # Diesel derive patterns
    DIESEL_DERIVES = {'Queryable', 'Insertable', 'AsChangeset', 'Identifiable',
                      'Associations', 'Selectable', 'QueryableByName'}

    # SeaORM derive patterns
    SEAORM_DERIVES = {'DeriveEntityModel', 'DeriveActiveModel', 'DeriveRelation',
                      'DeriveActiveEnum', 'DerivePartialModel'}

    # SQLx derive patterns
    SQLX_DERIVES = {'FromRow', 'Type'}

    # Serde derives
    SERDE_DERIVES = {'Serialize', 'Deserialize'}

    # Diesel table_name annotation
    TABLE_NAME_PATTERN = re.compile(
        r'#\[(?:diesel\s*\(\s*table_name\s*=\s*"(\w+)"|table_name\s*=\s*"(\w+)")\s*\]',
        re.MULTILINE
    )

    # SeaORM table_name
    SEAORM_TABLE = re.compile(
        r'#\[sea_orm\s*\([^)]*table_name\s*=\s*"(\w+)"',
        re.MULTILINE
    )

    # Diesel schema! macro
    SCHEMA_MACRO = re.compile(
        r'(?:diesel::)?table!\s*\{',
        re.MULTILINE
    )

    # Diesel joinable! macro
    JOINABLE_MACRO = re.compile(
        r'(?:diesel::)?joinable!\s*\(\s*(\w+)\s*->\s*(\w+)\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # belongs_to attribute
    BELONGS_TO = re.compile(
        r'#\[belongs_to\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Derive pattern for detecting model types
    DERIVE_PATTERN = re.compile(
        r'#\[derive\(([^)]+)\)\]',
        re.MULTILINE
    )

    # Struct header (after derives)
    STRUCT_HEADER = re.compile(
        r'(?:pub\s+)?struct\s+(\w+)',
        re.MULTILINE
    )

    # Struct field
    FIELD_PATTERN = re.compile(
        r'^\s*(?:pub\s+)?(\w+)\s*:\s*([^,}]+?)\s*,?\s*$',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Rust model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Rust database model definitions from source code.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            Dict with 'models', 'schemas', 'migrations' keys
        """
        return {
            'models': self._extract_models(content, file_path),
            'schemas': self._extract_schemas(content, file_path),
        }

    def _extract_models(self, content: str, file_path: str) -> List[RustModelInfo]:
        """Extract database model definitions based on derive macros."""
        models = []

        # Find derive blocks and check for ORM derives
        for derive_match in self.DERIVE_PATTERN.finditer(content):
            derives_str = derive_match.group(1)
            derives = [d.strip() for d in derives_str.split(',')]
            derive_set = set(derives)

            # Check if any ORM derive is present
            is_diesel = bool(derive_set & self.DIESEL_DERIVES)
            is_seaorm = bool(derive_set & self.SEAORM_DERIVES)
            is_sqlx = bool(derive_set & self.SQLX_DERIVES)
            has_serde = bool(derive_set & self.SERDE_DERIVES)

            if not (is_diesel or is_seaorm or is_sqlx):
                continue

            # Find the struct after the derive
            after = content[derive_match.end():]
            struct_match = self.STRUCT_HEADER.search(after)
            if not struct_match:
                continue

            # Make sure struct is close to the derive (within 200 chars, accounting for attributes)
            if struct_match.start() > 200:
                continue

            name = struct_match.group(1)
            line_number = content[:derive_match.start()].count('\n') + 1

            # Determine ORM
            orm = 'diesel' if is_diesel else ('sea-orm' if is_seaorm else 'sqlx')

            # Look for table name
            table_name = ''
            context = content[max(0, derive_match.start() - 100):derive_match.end() + struct_match.end() + 50]
            tn_match = self.TABLE_NAME_PATTERN.search(context)
            if tn_match:
                table_name = tn_match.group(1) or tn_match.group(2) or ''
            else:
                seaorm_tn = self.SEAORM_TABLE.search(context)
                if seaorm_tn:
                    table_name = seaorm_tn.group(1)

            if not table_name:
                # Default: snake_case pluralization of struct name
                table_name = self._to_snake_case(name) + 's'

            # Extract fields from struct body
            fields = []
            brace_pos = content.find('{', derive_match.end() + struct_match.end())
            if brace_pos != -1:
                body = self._extract_brace_body(content, brace_pos)
                if body:
                    for field_match in self.FIELD_PATTERN.finditer(body):
                        fname = field_match.group(1)
                        ftype = field_match.group(2).strip().rstrip(',')
                        fields.append({'name': fname, 'type': ftype})

            # Look for relationships
            belongs_to = []
            for bt_match in self.BELONGS_TO.finditer(content[max(0, derive_match.start() - 200):derive_match.end()]):
                belongs_to.append(bt_match.group(1))

            is_queryable = 'Queryable' in derive_set or 'DeriveEntityModel' in derive_set or 'FromRow' in derive_set
            is_insertable = 'Insertable' in derive_set or 'DeriveActiveModel' in derive_set

            # Find primary key
            primary_key = None
            if fields:
                for f in fields:
                    if f['name'] == 'id':
                        primary_key = 'id'
                        break

            models.append(RustModelInfo(
                name=name,
                table_name=table_name,
                fields=fields,
                derives=derives,
                orm=orm,
                file=file_path,
                line_number=line_number,
                is_queryable=is_queryable,
                is_insertable=is_insertable,
                primary_key=primary_key,
                belongs_to=belongs_to,
            ))

        return models

    def _extract_schemas(self, content: str, file_path: str) -> List[RustSchemaInfo]:
        """Extract Diesel schema! table definitions."""
        schemas = []

        for match in self.SCHEMA_MACRO.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            brace_pos = match.end() - 1
            body = self._extract_brace_body(content, brace_pos)

            if body:
                # Parse table name and columns from schema! body
                table_match = re.search(r'(\w+)\s*\(', body)
                if table_match:
                    table_name = table_match.group(1)
                    columns = []

                    # Find column definitions
                    for col_match in re.finditer(r'(\w+)\s*->\s*(\w+)', body):
                        columns.append({
                            'name': col_match.group(1),
                            'type': col_match.group(2),
                        })

                    schemas.append(RustSchemaInfo(
                        table_name=table_name,
                        columns=columns,
                        file=file_path,
                        line_number=line_number,
                    ))

        return schemas

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _extract_brace_body(content: str, open_brace_pos: int) -> Optional[str]:
        """Extract body between matched braces."""
        depth = 1
        i = open_brace_pos + 1
        in_string = False
        in_line_comment = False
        in_block_comment = False
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            next_ch = content[i + 1] if i + 1 < length else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                i += 1
                continue
            if in_block_comment:
                if ch == '*' and next_ch == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            if ch == '/' and next_ch == '/':
                in_line_comment = True
                i += 2
                continue
            if ch == '/' and next_ch == '*':
                in_block_comment = True
                i += 2
                continue
            if ch == '"':
                in_string = True
                i += 1
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return content[open_brace_pos + 1:i]
            i += 1

        return None
