"""
TypeScript Model Extractor for CodeTrellis

Extracts data model / ORM definitions from TypeScript source code:
- TypeORM entities (@Entity, @Column, @ManyToOne, etc.)
- MikroORM entities (@Entity, @Property, @ManyToOne)
- Prisma generated types (PrismaClient usage)
- Sequelize-typescript models (@Table, @Column)
- Drizzle ORM schema definitions (pgTable, mysqlTable)
- class-validator DTOs (@IsString, @IsEmail, etc.)
- class-transformer decorators (@Expose, @Type, @Transform)
- Mongoose-typescript schemas (prop decorator)
- Objection.js TypeScript models (Model class extension)
- Zod schemas with TypeScript inference

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TSFieldInfo:
    """Information about a model/entity field."""
    name: str
    type: str = ""
    field_type: str = ""  # column type (varchar, int, etc.)
    required: bool = True
    unique: bool = False
    nullable: bool = False
    default: Optional[str] = None
    ref: Optional[str] = None
    index: bool = False
    primary: bool = False
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class TSModelInfo:
    """Information about a TypeScript data model/entity."""
    name: str
    file: str = ""
    line_number: int = 0
    orm: str = ""  # typeorm, mikroorm, prisma, sequelize-typescript, drizzle, mongoose-ts
    table_name: str = ""
    fields: List[TSFieldInfo] = field(default_factory=list)
    relationships: List['TSRelationInfo'] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    is_exported: bool = False
    implements: List[str] = field(default_factory=list)
    extends: str = ""


@dataclass
class TSRelationInfo:
    """Information about a model relationship."""
    name: str = ""
    relationship_type: str = ""  # OneToOne, OneToMany, ManyToOne, ManyToMany
    target: str = ""
    foreign_key: str = ""
    through: str = ""
    inverse: str = ""
    line_number: int = 0


@dataclass
class TSMigrationInfo:
    """Information about a database migration."""
    name: str
    file: str = ""
    line_number: int = 0
    direction: str = "up"
    table_name: str = ""
    operations: List[str] = field(default_factory=list)
    orm: str = ""


@dataclass
class TSDTOInfo:
    """Information about a Data Transfer Object (DTO)."""
    name: str
    file: str = ""
    line_number: int = 0
    fields: List[TSFieldInfo] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)
    is_exported: bool = False
    framework: str = ""  # class-validator, zod, io-ts, runtypes


class TypeScriptModelExtractor:
    """
    Extracts data model definitions from TypeScript source code.

    Detects:
    - TypeORM entities and relations
    - MikroORM entities
    - Sequelize-typescript models
    - Drizzle ORM schemas
    - class-validator DTOs
    - Prisma client patterns
    - Zod schema inference
    """

    # TypeORM entity
    TYPEORM_ENTITY_PATTERN = re.compile(
        r"@Entity\s*\(\s*(?:['\"](\w+)['\"])?\s*\)\s*\n"
        r"(?:.*\n)*?\s*(?:export\s+)?class\s+(\w+)",
        re.MULTILINE,
    )

    # TypeORM column
    TYPEORM_COLUMN_PATTERN = re.compile(
        r"@(Column|PrimaryColumn|PrimaryGeneratedColumn|CreateDateColumn|UpdateDateColumn|DeleteDateColumn|VersionColumn)\s*\(([^)]*)\)\s*\n\s*(\w+)\s*(?:!?\s*:\s*(.+?))?\s*;",
        re.MULTILINE,
    )

    # TypeORM relations
    TYPEORM_RELATION_PATTERN = re.compile(
        r"@(OneToOne|OneToMany|ManyToOne|ManyToMany)\s*\(\s*\(\)\s*=>\s*(\w+)",
        re.MULTILINE,
    )

    # MikroORM entity
    MIKROORM_ENTITY_PATTERN = re.compile(
        r"@Entity\s*\(\s*(?:\{[^}]*\})?\s*\)\s*\n"
        r"(?:.*\n)*?\s*(?:export\s+)?class\s+(\w+)",
        re.MULTILINE,
    )

    # Sequelize-typescript model
    SEQUELIZE_TS_PATTERN = re.compile(
        r"@Table\s*(?:\([^)]*\))?\s*\n"
        r"(?:.*\n)*?\s*(?:export\s+)?class\s+(\w+)\s+extends\s+Model",
        re.MULTILINE,
    )

    # Drizzle ORM table definition
    DRIZZLE_TABLE_PATTERN = re.compile(
        r"(?:export\s+)?(?:const\s+)(\w+)\s*=\s*(pgTable|mysqlTable|sqliteTable)\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # class-validator DTO
    CLASS_VALIDATOR_PATTERN = re.compile(
        r"@(IsString|IsNumber|IsEmail|IsBoolean|IsOptional|IsNotEmpty|IsEnum|IsArray|IsDate|IsUUID|IsInt|Min|Max|MinLength|MaxLength|ValidateNested|IsUrl|IsIP|Matches|ArrayMinSize|ArrayMaxSize)",
        re.MULTILINE,
    )

    # Zod schema with type inference
    ZOD_SCHEMA_PATTERN = re.compile(
        r"(?:export\s+)?(?:const\s+)(\w+)\s*=\s*z\s*\.\s*object\s*\(",
        re.MULTILINE,
    )

    # Prisma client usage
    PRISMA_USAGE_PATTERN = re.compile(
        r"prisma\s*\.\s*(\w+)\s*\.\s*(findMany|findFirst|findUnique|create|update|delete|upsert|count|aggregate|groupBy)\s*\(",
        re.MULTILINE,
    )

    # TypeORM migration
    TYPEORM_MIGRATION_PATTERN = re.compile(
        r"(?:export\s+)?class\s+(\w+)\s+implements\s+MigrationInterface",
        re.MULTILINE,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all model definitions from TypeScript source code.

        Returns dict with keys: models, migrations, relationships, dtos
        """
        models = []
        migrations = []
        relationships = []
        dtos = []

        # TypeORM entities
        for match in self.TYPEORM_ENTITY_PATTERN.finditer(content):
            table_name = match.group(1) or ""
            class_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            fields = self._extract_typeorm_columns(content, class_name)
            rels = self._extract_typeorm_relations(content, class_name)
            relationships.extend(rels)

            models.append(TSModelInfo(
                name=class_name,
                file=file_path,
                line_number=line_num,
                orm="typeorm",
                table_name=table_name or class_name.lower(),
                fields=fields,
                relationships=rels,
                is_exported=True,
            ))

        # Drizzle tables
        for match in self.DRIZZLE_TABLE_PATTERN.finditer(content):
            var_name = match.group(1)
            dialect = match.group(2)
            table_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            models.append(TSModelInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                orm="drizzle",
                table_name=table_name,
                is_exported=bool(re.search(r'\bexport\b', content[max(0, match.start()-20):match.start()])),
            ))

        # Sequelize-typescript models
        for match in self.SEQUELIZE_TS_PATTERN.finditer(content):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            models.append(TSModelInfo(
                name=class_name,
                file=file_path,
                line_number=line_num,
                orm="sequelize-typescript",
                extends="Model",
                is_exported=True,
            ))

        # Zod schemas
        for match in self.ZOD_SCHEMA_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            dtos.append(TSDTOInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                framework="zod",
                is_exported=bool(re.search(r'\bexport\b', content[max(0, match.start()-20):match.start()])),
            ))

        # Prisma usage patterns (track which models are used)
        prisma_models = set()
        for match in self.PRISMA_USAGE_PATTERN.finditer(content):
            model_name = match.group(1)
            if model_name not in prisma_models:
                prisma_models.add(model_name)
                line_num = content[:match.start()].count('\n') + 1
                models.append(TSModelInfo(
                    name=model_name,
                    file=file_path,
                    line_number=line_num,
                    orm="prisma",
                ))

        # TypeORM migrations
        for match in self.TYPEORM_MIGRATION_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Try to extract table operations
            operations = self._extract_migration_ops(content)

            migrations.append(TSMigrationInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                operations=operations,
                orm="typeorm",
            ))

        # class-validator DTOs (classes with validation decorators)
        if self.CLASS_VALIDATOR_PATTERN.search(content):
            dto_classes = re.finditer(
                r'(?:export\s+)?class\s+(\w+(?:Dto|DTO|Input|Params|Args|Payload|Request|Response))\s*(?:extends\s+\w+\s*)?\{',
                content,
                re.MULTILINE,
            )
            for match in dto_classes:
                name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Extract validators used
                validators = list(set(
                    m.group(1) for m in self.CLASS_VALIDATOR_PATTERN.finditer(content)
                ))

                dtos.append(TSDTOInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    validators=validators,
                    framework="class-validator",
                    is_exported=True,
                ))

        return {
            'models': models,
            'migrations': migrations,
            'relationships': relationships,
            'dtos': dtos,
        }

    def _extract_typeorm_columns(self, content: str, class_name: str) -> List[TSFieldInfo]:
        """Extract TypeORM column definitions."""
        fields = []

        for match in self.TYPEORM_COLUMN_PATTERN.finditer(content):
            decorator = match.group(1)
            decorator_args = match.group(2)
            col_name = match.group(3)
            col_type = (match.group(4) or "").strip()
            line_num = content[:match.start()].count('\n') + 1

            is_primary = decorator in ('PrimaryColumn', 'PrimaryGeneratedColumn')
            is_nullable = 'nullable: true' in decorator_args if decorator_args else False
            is_unique = 'unique: true' in decorator_args if decorator_args else False

            fields.append(TSFieldInfo(
                name=col_name,
                type=col_type,
                primary=is_primary,
                nullable=is_nullable,
                unique=is_unique,
                decorators=[decorator],
                line_number=line_num,
            ))

        return fields

    def _extract_typeorm_relations(self, content: str, class_name: str) -> List[TSRelationInfo]:
        """Extract TypeORM relation definitions."""
        relations = []

        for match in self.TYPEORM_RELATION_PATTERN.finditer(content):
            rel_type = match.group(1)
            target = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Look for field name on subsequent line
            name = ""
            after = content[match.end():match.end() + 200]
            field_match = re.search(r'(\w+)\s*[!?]?\s*:', after)
            if field_match:
                name = field_match.group(1)

            relations.append(TSRelationInfo(
                name=name,
                relationship_type=rel_type,
                target=target,
                line_number=line_num,
            ))

        return relations

    def _extract_migration_ops(self, content: str) -> List[str]:
        """Extract migration operations from content."""
        operations = []

        op_patterns = {
            'createTable': r'queryRunner\.createTable|CREATE TABLE',
            'dropTable': r'queryRunner\.dropTable|DROP TABLE',
            'addColumn': r'queryRunner\.addColumn|ADD COLUMN',
            'dropColumn': r'queryRunner\.dropColumn|DROP COLUMN',
            'createIndex': r'queryRunner\.createIndex|CREATE INDEX',
            'addForeignKey': r'queryRunner\.createForeignKey|FOREIGN KEY',
            'alterColumn': r'queryRunner\.changeColumn|ALTER COLUMN',
        }

        for op_name, pattern in op_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                operations.append(op_name)

        return operations
