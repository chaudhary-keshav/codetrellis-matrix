"""
JavaScript Model Extractor for CodeTrellis

Extracts data model / ORM definitions from JavaScript source code:
- Mongoose schemas and models
- Sequelize model definitions
- Prisma client usage patterns
- Knex.js migrations and schema builders
- TypeORM entities (when used with JS + decorators via Babel)
- Objection.js models
- Bookshelf.js models
- Generic model patterns (factory functions, class-based)

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSSchemaFieldInfo:
    """Information about a model/schema field."""
    name: str
    type: str = ""
    required: bool = False
    unique: bool = False
    default: Optional[str] = None
    ref: Optional[str] = None  # Mongoose ref / FK
    index: bool = False
    line_number: int = 0


@dataclass
class JSModelInfo:
    """Information about a JavaScript data model."""
    name: str
    file: str = ""
    line_number: int = 0
    orm: str = ""  # mongoose, sequelize, prisma, knex, typeorm, objection
    table_name: str = ""
    fields: List[JSSchemaFieldInfo] = field(default_factory=list)
    relationships: List['JSRelationInfo'] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    is_exported: bool = False
    collection_name: str = ""  # Mongoose collection name


@dataclass
class JSRelationInfo:
    """Information about a model relationship."""
    type: str = ""  # hasOne, hasMany, belongsTo, belongsToMany, ref
    target: str = ""
    foreign_key: str = ""
    through: str = ""
    line_number: int = 0


@dataclass
class JSMigrationInfo:
    """Information about a database migration."""
    name: str
    file: str = ""
    line_number: int = 0
    direction: str = "up"  # up, down
    table_name: str = ""
    operations: List[str] = field(default_factory=list)  # createTable, addColumn, etc.
    orm: str = ""  # knex, sequelize, prisma


class JavaScriptModelExtractor:
    """
    Extracts data model definitions from JavaScript source code.

    Detects:
    - Mongoose Schema/Model definitions
    - Sequelize model definitions (define, init)
    - Knex.js migrations (createTable, alterTable)
    - Prisma client usage
    - Objection.js Model classes
    - Bookshelf.js models
    """

    # Mongoose Schema
    MONGOOSE_SCHEMA_PATTERN = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*new\s+(?:mongoose\.)?Schema\s*\(",
        re.MULTILINE,
    )

    # Mongoose model creation
    MONGOOSE_MODEL_PATTERN = re.compile(
        r"(?:mongoose\.model|model)\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Mongoose model export
    MONGOOSE_EXPORT_PATTERN = re.compile(
        r"(?:module\.)?exports\s*(?:\.\w+)?\s*=\s*(?:mongoose\.)?model\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Sequelize define
    SEQUELIZE_DEFINE_PATTERN = re.compile(
        r"(?:sequelize|db)\.define\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Sequelize Model.init
    SEQUELIZE_INIT_PATTERN = re.compile(
        r"(\w+)\.init\s*\(\s*\{",
        re.MULTILINE,
    )

    # Sequelize class extends Model
    SEQUELIZE_CLASS_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+(?:Sequelize\.)?Model\s*\{",
        re.MULTILINE,
    )

    # Sequelize relationships
    SEQUELIZE_RELATION_PATTERN = re.compile(
        r"(\w+)\.(hasOne|hasMany|belongsTo|belongsToMany)\s*\(\s*(\w+)",
        re.MULTILINE,
    )

    # Knex migration (createTable)
    KNEX_CREATE_TABLE_PATTERN = re.compile(
        r"(?:knex|schema)\.createTable\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Knex migration direction
    KNEX_MIGRATION_PATTERN = re.compile(
        r"exports\.(up|down)\s*=\s*(?:async\s+)?(?:function|\()",
        re.MULTILINE,
    )

    # Objection.js Model
    OBJECTION_MODEL_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+(?:objection\.)?Model\s*\{",
        re.MULTILINE,
    )

    # Objection.js tableName
    OBJECTION_TABLE_PATTERN = re.compile(
        r"static\s+get\s+tableName\s*\(\)\s*\{\s*return\s+['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Mongoose Schema field pattern
    MONGOOSE_FIELD_PATTERN = re.compile(
        r"(\w+)\s*:\s*\{\s*type\s*:\s*([\w.]+)",
        re.MULTILINE,
    )

    # Mongoose hook pattern
    MONGOOSE_HOOK_PATTERN = re.compile(
        r"(?:\w+Schema|\w+)\.(?:pre|post)\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Prisma client usage
    PRISMA_USAGE_PATTERN = re.compile(
        r"(?:prisma|client)\.\s*(\w+)\.\s*"
        r"(findMany|findUnique|findFirst|create|update|delete|upsert|count|aggregate|groupBy)",
        re.MULTILINE,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract model definitions from JavaScript source code.

        Returns dict with keys: models, migrations, relationships
        """
        models = self._extract_models(content, file_path)
        migrations = self._extract_migrations(content, file_path)
        relationships = self._extract_relationships(content, file_path)

        return {
            'models': models,
            'migrations': migrations,
            'relationships': relationships,
        }

    def _extract_models(self, content: str, file_path: str) -> List[JSModelInfo]:
        """Extract data model definitions from various ORMs."""
        models = []
        seen = set()

        # Mongoose models
        for match in self.MONGOOSE_SCHEMA_PATTERN.finditer(content):
            schema_var = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Try to find the model name
            model_name = schema_var.replace('Schema', '').replace('schema', '')
            model_match = self.MONGOOSE_MODEL_PATTERN.search(content)
            if model_match:
                model_name = model_match.group(1)

            if model_name in seen:
                continue
            seen.add(model_name)

            # Extract fields
            fields = self._extract_mongoose_fields(content, match.end())

            # Extract hooks
            hooks = []
            for hook_match in self.MONGOOSE_HOOK_PATTERN.finditer(content):
                hooks.append(hook_match.group(1))

            models.append(JSModelInfo(
                name=model_name,
                file=file_path,
                line_number=line_num,
                orm='mongoose',
                fields=fields,
                hooks=hooks,
                is_exported=True,
            ))

        # Sequelize models (class extends Model)
        for match in self.SEQUELIZE_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            models.append(JSModelInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                orm='sequelize',
                is_exported=True,
            ))

        # Sequelize define
        for match in self.SEQUELIZE_DEFINE_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            models.append(JSModelInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                orm='sequelize',
                table_name=name,
            ))

        # Objection.js models
        for match in self.OBJECTION_MODEL_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            # Try to find tableName
            table_match = self.OBJECTION_TABLE_PATTERN.search(content)
            table_name = table_match.group(1) if table_match else ""

            models.append(JSModelInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                orm='objection',
                table_name=table_name,
            ))

        # Prisma client usage (extract model names from prisma.modelName.method)
        for match in self.PRISMA_USAGE_PATTERN.finditer(content):
            model_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if model_name in seen or model_name in ('$', '_'):
                continue
            seen.add(model_name)

            models.append(JSModelInfo(
                name=model_name.capitalize(),
                file=file_path,
                line_number=line_num,
                orm='prisma',
                table_name=model_name,
            ))

        return models

    def _extract_mongoose_fields(self, content: str, start_pos: int) -> List[JSSchemaFieldInfo]:
        """Extract fields from a Mongoose schema definition."""
        fields = []

        # Search for field definitions after the Schema constructor
        search_area = content[start_pos:start_pos + 2000]

        for match in self.MONGOOSE_FIELD_PATTERN.finditer(search_area):
            name = match.group(1)
            field_type = match.group(2)

            if name in ('type', 'default', 'ref', 'required', 'index', 'unique'):
                continue

            # Check for required/unique/ref in the field definition block
            field_block = search_area[match.start():match.start() + 200]
            required = bool(re.search(r'required\s*:\s*true', field_block))
            unique = bool(re.search(r'unique\s*:\s*true', field_block))
            index = bool(re.search(r'index\s*:\s*true', field_block))
            ref_match = re.search(r"ref\s*:\s*['\"](\w+)['\"]", field_block)
            ref = ref_match.group(1) if ref_match else None

            fields.append(JSSchemaFieldInfo(
                name=name,
                type=field_type,
                required=required,
                unique=unique,
                index=index,
                ref=ref,
            ))

        return fields[:30]  # Cap at 30 fields

    def _extract_migrations(self, content: str, file_path: str) -> List[JSMigrationInfo]:
        """Extract database migration definitions."""
        migrations = []

        # Knex migrations
        for match in self.KNEX_MIGRATION_PATTERN.finditer(content):
            direction = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find table operations
            operations = []
            tables = []
            for table_match in self.KNEX_CREATE_TABLE_PATTERN.finditer(content):
                tables.append(table_match.group(1))
                operations.append('createTable')

            if re.search(r'\.alterTable\s*\(', content):
                operations.append('alterTable')
            if re.search(r'\.dropTable\s*\(', content):
                operations.append('dropTable')

            for table in tables or ['<unknown>']:
                migrations.append(JSMigrationInfo(
                    name=f"{direction}_{table}",
                    file=file_path,
                    line_number=line_num,
                    direction=direction,
                    table_name=table,
                    operations=operations,
                    orm='knex',
                ))

        # Sequelize migration
        if re.search(r'queryInterface\.(createTable|addColumn|removeColumn|changeColumn)', content):
            for match in re.finditer(r'queryInterface\.(createTable|addColumn|removeColumn|changeColumn)\s*\(\s*[\'"](\w+)[\'"]', content):
                operation = match.group(1)
                table = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                migrations.append(JSMigrationInfo(
                    name=f"{operation}_{table}",
                    file=file_path,
                    line_number=line_num,
                    table_name=table,
                    operations=[operation],
                    orm='sequelize',
                ))

        return migrations

    def _extract_relationships(self, content: str, file_path: str) -> List[JSRelationInfo]:
        """Extract model relationship definitions."""
        relationships = []

        # Sequelize relationships
        for match in self.SEQUELIZE_RELATION_PATTERN.finditer(content):
            source = match.group(1)
            rel_type = match.group(2)
            target = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            relationships.append(JSRelationInfo(
                type=rel_type,
                target=target,
                line_number=line_num,
            ))

        # Mongoose refs (already captured in fields, but add explicit relationships)
        for match in re.finditer(r"ref\s*:\s*['\"](\w+)['\"]", content):
            target = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            relationships.append(JSRelationInfo(
                type='ref',
                target=target,
                line_number=line_num,
            ))

        return relationships
