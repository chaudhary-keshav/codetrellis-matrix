"""
SQLAlchemyExtractor - Extracts SQLAlchemy model definitions from Python source code.

This extractor parses SQLAlchemy ORM models and extracts:
- Model class definitions (declarative base)
- Column definitions with types, constraints
- Relationships (one-to-many, many-to-one, many-to-many)
- Primary keys, foreign keys
- Indexes and unique constraints
- Table names

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class RelationshipType(Enum):
    """Types of SQLAlchemy relationships."""
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    ONE_TO_ONE = "one_to_one"


@dataclass
class SQLAlchemyColumnInfo:
    """Information about a SQLAlchemy column."""
    name: str
    type: str
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True
    unique: bool = False
    default: Optional[str] = None
    server_default: Optional[str] = None
    index: bool = False
    autoincrement: bool = False


@dataclass
class SQLAlchemyRelationshipInfo:
    """Information about a SQLAlchemy relationship."""
    name: str
    target_model: str
    relationship_type: RelationshipType = RelationshipType.MANY_TO_ONE
    back_populates: Optional[str] = None
    backref: Optional[str] = None
    cascade: Optional[str] = None
    lazy: str = "select"
    secondary: Optional[str] = None  # For many-to-many


@dataclass
class SQLAlchemyModelInfo:
    """Complete information about a SQLAlchemy model."""
    name: str
    table_name: str
    columns: List[SQLAlchemyColumnInfo] = field(default_factory=list)
    relationships: List[SQLAlchemyRelationshipInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    unique_constraints: List[str] = field(default_factory=list)
    line_number: int = 0


class SQLAlchemyExtractor:
    """
    Extracts SQLAlchemy ORM model definitions from source code.

    Handles:
    - Declarative base models (class User(Base):)
    - SQLAlchemy 2.0 style (class User(DeclarativeBase):)
    - Column() definitions with all options
    - Mapped[] type annotations (SQLAlchemy 2.0)
    - relationship() definitions
    - ForeignKey constraints
    - __tablename__ attribute
    """

    # Pattern for model class definition
    MODEL_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    # Pattern for __tablename__
    TABLENAME_PATTERN = re.compile(
        r'__tablename__\s*=\s*[\'"](\w+)[\'"]'
    )

    # Pattern for Column definitions
    COLUMN_PATTERN = re.compile(
        r'(\w+)\s*(?::\s*Mapped\[([^\]]+)\])?\s*=\s*(?:mapped_column|Column)\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE
    )

    # Pattern for relationship definitions
    RELATIONSHIP_PATTERN = re.compile(
        r'(\w+)\s*(?::\s*Mapped\[([^\]]+)\])?\s*=\s*relationship\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE
    )

    # SQL types to match
    SQL_TYPES = [
        'Integer', 'String', 'Text', 'Boolean', 'Float', 'Numeric',
        'DateTime', 'Date', 'Time', 'LargeBinary', 'PickleType',
        'Unicode', 'UnicodeText', 'BigInteger', 'SmallInteger', 'Enum',
        'JSON', 'ARRAY', 'UUID', 'Interval'
    ]

    # Base classes that indicate SQLAlchemy model
    BASE_CLASSES = ['Base', 'DeclarativeBase', 'Model', 'db.Model']

    def __init__(self):
        """Initialize the SQLAlchemy extractor."""
        pass

    def extract(self, content: str) -> List[SQLAlchemyModelInfo]:
        """
        Extract all SQLAlchemy model definitions from Python content.

        Args:
            content: Python source code

        Returns:
            List of SQLAlchemyModelInfo objects
        """
        models = []

        # Find all class definitions
        for class_match in self.MODEL_PATTERN.finditer(content):
            class_name = class_match.group(1)
            bases_str = class_match.group(2)
            bases = [b.strip() for b in bases_str.split(',')]

            # Check if this is a SQLAlchemy model
            if not self._is_sqlalchemy_model(bases):
                continue

            # Find the class body
            class_start = class_match.end()
            class_body = self._extract_class_body(content, class_start)

            # Extract table name
            table_name = self._extract_table_name(class_body) or class_name.lower()

            # Extract columns
            columns = self._extract_columns(class_body)

            # Extract relationships
            relationships = self._extract_relationships(class_body)

            # Calculate line number
            line_number = content[:class_match.start()].count('\n') + 1

            model = SQLAlchemyModelInfo(
                name=class_name,
                table_name=table_name,
                columns=columns,
                relationships=relationships,
                bases=bases,
                line_number=line_number
            )

            models.append(model)

        return models

    def _is_sqlalchemy_model(self, bases: List[str]) -> bool:
        """Check if class bases indicate a SQLAlchemy model."""
        for base in bases:
            for model_base in self.BASE_CLASSES:
                if model_base in base:
                    return True
        return False

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract the class body starting from the given position."""
        lines = content[start:].split('\n')
        body_lines = []
        indent = None

        for line in lines:
            if not line.strip():
                body_lines.append(line)
                continue

            # Determine base indent from first non-empty line
            if indent is None:
                spaces = len(line) - len(line.lstrip())
                if spaces > 0:
                    indent = spaces
                else:
                    break

            # Check if we've exited the class
            current_spaces = len(line) - len(line.lstrip())
            if line.strip() and current_spaces < indent:
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _extract_table_name(self, class_body: str) -> Optional[str]:
        """Extract __tablename__ from class body."""
        match = self.TABLENAME_PATTERN.search(class_body)
        if match:
            return match.group(1)
        return None

    def _extract_columns(self, class_body: str) -> List[SQLAlchemyColumnInfo]:
        """Extract column definitions from class body."""
        columns = []

        for match in self.COLUMN_PATTERN.finditer(class_body):
            col_name = match.group(1)
            mapped_type = match.group(2)
            col_args = match.group(3)

            # Parse column type
            col_type = self._extract_column_type(col_args, mapped_type)

            # Parse column options
            primary_key = 'primary_key=True' in col_args or 'primary_key = True' in col_args
            nullable = 'nullable=False' not in col_args and 'nullable = False' not in col_args
            unique = 'unique=True' in col_args or 'unique = True' in col_args
            index = 'index=True' in col_args or 'index = True' in col_args
            autoincrement = 'autoincrement=True' in col_args or 'autoincrement = True' in col_args

            # Extract foreign key
            foreign_key = self._extract_foreign_key(col_args)

            # Extract default
            default = self._extract_default(col_args)

            column = SQLAlchemyColumnInfo(
                name=col_name,
                type=col_type,
                primary_key=primary_key,
                foreign_key=foreign_key,
                nullable=nullable,
                unique=unique,
                default=default,
                index=index,
                autoincrement=autoincrement
            )

            columns.append(column)

        return columns

    def _extract_column_type(self, col_args: str, mapped_type: Optional[str]) -> str:
        """Extract the column type from arguments or Mapped annotation."""
        # Try to get from Mapped type annotation first
        if mapped_type:
            # Clean up Optional, etc.
            clean_type = mapped_type.replace('Optional[', '').replace(']', '')
            return clean_type

        # Look for SQL type in arguments
        for sql_type in self.SQL_TYPES:
            pattern = rf'{sql_type}(?:\([^)]*\))?'
            match = re.search(pattern, col_args)
            if match:
                return match.group(0)

        return "Unknown"

    def _extract_foreign_key(self, col_args: str) -> Optional[str]:
        """Extract ForeignKey reference from column arguments."""
        match = re.search(r'ForeignKey\s*\(\s*[\'"]([^"\']+)[\'"]', col_args)
        if match:
            return match.group(1)
        return None

    def _extract_default(self, col_args: str) -> Optional[str]:
        """Extract default value from column arguments."""
        match = re.search(r'default\s*=\s*([^,\)]+)', col_args)
        if match:
            return match.group(1).strip()
        return None

    def _extract_relationships(self, class_body: str) -> List[SQLAlchemyRelationshipInfo]:
        """Extract relationship definitions from class body."""
        relationships = []

        for match in self.RELATIONSHIP_PATTERN.finditer(class_body):
            rel_name = match.group(1)
            mapped_type = match.group(2)
            rel_args = match.group(3)

            # Extract target model
            target_model = self._extract_target_model(rel_args)

            # Extract relationship options
            back_populates = self._extract_option(rel_args, 'back_populates')
            backref = self._extract_option(rel_args, 'backref')
            cascade = self._extract_option(rel_args, 'cascade')
            lazy = self._extract_option(rel_args, 'lazy') or 'select'
            secondary = self._extract_option(rel_args, 'secondary')

            # Determine relationship type
            rel_type = self._determine_relationship_type(mapped_type, rel_args, secondary)

            relationship = SQLAlchemyRelationshipInfo(
                name=rel_name,
                target_model=target_model,
                relationship_type=rel_type,
                back_populates=back_populates,
                backref=backref,
                cascade=cascade,
                lazy=lazy,
                secondary=secondary
            )

            relationships.append(relationship)

        return relationships

    def _extract_target_model(self, rel_args: str) -> str:
        """Extract the target model from relationship arguments."""
        # First positional argument is the model
        match = re.search(r'^[\'"]?(\w+)[\'"]?', rel_args.strip())
        if match:
            return match.group(1)
        return "Unknown"

    def _extract_option(self, rel_args: str, option: str) -> Optional[str]:
        """Extract an option value from relationship arguments."""
        match = re.search(rf'{option}\s*=\s*[\'"]?([^\'"`,\)]+)[\'"]?', rel_args)
        if match:
            return match.group(1).strip()
        return None

    def _determine_relationship_type(
        self,
        mapped_type: Optional[str],
        rel_args: str,
        secondary: Optional[str]
    ) -> RelationshipType:
        """Determine the type of relationship."""
        if secondary:
            return RelationshipType.MANY_TO_MANY

        # Check Mapped type for List
        if mapped_type:
            if 'List[' in mapped_type or 'list[' in mapped_type:
                return RelationshipType.ONE_TO_MANY

        # Check uselist
        if 'uselist=False' in rel_args or 'uselist = False' in rel_args:
            return RelationshipType.ONE_TO_ONE

        return RelationshipType.MANY_TO_ONE

    def to_codetrellis_format(self, models: List[SQLAlchemyModelInfo]) -> str:
        """
        Convert extracted SQLAlchemy models to CodeTrellis format.

        Args:
            models: List of SQLAlchemyModelInfo objects

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        if models:
            lines.append("[SQLALCHEMY_MODELS]")

            for model in models:
                # Model header
                lines.append(f"Model:{model.name}|table:{model.table_name}")

                # Columns
                col_parts = []
                for col in model.columns:
                    flags = []
                    if col.primary_key:
                        flags.append("PK")
                    if col.foreign_key:
                        flags.append(f"FK:{col.foreign_key}")
                    if col.unique:
                        flags.append("UQ")
                    if col.index:
                        flags.append("IX")
                    if not col.nullable:
                        flags.append("!")

                    flag_str = f"[{','.join(flags)}]" if flags else ""
                    default_str = f"={col.default}" if col.default else ""
                    col_parts.append(f"{col.name}:{col.type}{flag_str}{default_str}")

                if col_parts:
                    lines.append(f"  cols:[{','.join(col_parts)}]")

                # Relationships
                rel_parts = []
                for rel in model.relationships:
                    rel_type_short = {
                        RelationshipType.ONE_TO_MANY: "1:N",
                        RelationshipType.MANY_TO_ONE: "N:1",
                        RelationshipType.MANY_TO_MANY: "N:N",
                        RelationshipType.ONE_TO_ONE: "1:1"
                    }.get(rel.relationship_type, "N:1")

                    back = f"↔{rel.back_populates}" if rel.back_populates else ""
                    rel_parts.append(f"{rel.name}->{rel.target_model}({rel_type_short}){back}")

                if rel_parts:
                    lines.append(f"  rels:[{','.join(rel_parts)}]")

                lines.append("")

        return "\n".join(lines)


# Convenience function
def extract_sqlalchemy_models(content: str) -> List[SQLAlchemyModelInfo]:
    """Extract SQLAlchemy model definitions from Python content."""
    extractor = SQLAlchemyExtractor()
    return extractor.extract(content)
