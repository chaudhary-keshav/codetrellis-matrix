"""
AdonisJS model extractor - Extract Lucid ORM models, relationships, hooks, scopes.

Extracts:
- Model class definitions (extends BaseModel)
- Column declarations (@column, @column.date, @column.dateTime)
- Relationships (@hasMany, @belongsTo, @manyToMany, @hasOne, @hasManyThrough)
- Model hooks (@beforeSave, @afterFind, @beforeCreate, @afterCreate, etc.)
- Computed properties (@computed)
- Query scopes
- Soft deletes (@column.dateTime({ autoCreate: false }) for deletedAt)
- Table name overrides (static table = 'users')
- Primary key customization
- v4: class User extends Model { ... }
- v5/v6: class User extends BaseModel { ... } with decorators

Supports AdonisJS v4 (class-based) through v6 (decorators + ESM).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AdonisRelationshipInfo:
    """Information about a Lucid ORM relationship."""
    type: str = ""              # hasMany, belongsTo, manyToMany, hasOne, hasManyThrough
    name: str = ""              # property name (e.g., 'posts')
    related_model: str = ""     # related model class (e.g., 'Post')
    foreign_key: str = ""
    local_key: str = ""
    pivot_table: str = ""       # for manyToMany
    through_model: str = ""     # for hasManyThrough
    options: Dict[str, Any] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class AdonisModelHookInfo:
    """Information about a Lucid model hook."""
    event: str = ""             # beforeSave, afterFind, beforeCreate, afterCreate, etc.
    method: str = ""            # method name
    is_static: bool = False
    line_number: int = 0


@dataclass
class AdonisModelInfo:
    """Information about an AdonisJS Lucid model."""
    name: str = ""              # User
    table: str = ""             # table name (defaults to pluralized snake_case)
    primary_key: str = "id"     # primary key column
    file: str = ""
    columns: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[AdonisRelationshipInfo] = field(default_factory=list)
    hooks: List[AdonisModelHookInfo] = field(default_factory=list)
    computed_properties: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    has_soft_deletes: bool = False
    has_timestamps: bool = False
    traits: List[str] = field(default_factory=list)  # v4 traits
    line_number: int = 0


class AdonisModelExtractor:
    """Extract AdonisJS Lucid ORM model definitions."""

    # Model class: class User extends BaseModel { or class User extends Model {
    # Also: class Post extends compose(BaseModel, SoftDeletes) {
    MODEL_CLASS_PATTERN = re.compile(
        r'(?:export\s+default\s+)?class\s+(\w+)\s+extends\s+'
        r'(?:(BaseModel|Model)|compose\s*\(\s*(BaseModel|Model)(?:\s*,\s*\w+)*\s*\))\s*\{',
        re.MULTILINE,
    )

    # v4: module.exports = class User extends Model {
    V4_MODEL_PATTERN = re.compile(
        r'module\.exports\s*=\s*class\s+(\w+)\s+extends\s+Model\s*\{',
        re.MULTILINE,
    )

    # Table name: public static table = 'users' or static get table() { return 'users' }
    TABLE_PATTERN = re.compile(
        r"(?:public\s+)?static\s+(?:table\s*=\s*['\"](\w+)['\"]|"
        r"get\s+table\s*\(\s*\)\s*\{[^}]*return\s+['\"](\w+)['\"])",
        re.MULTILINE,
    )

    # Primary key: public static primaryKey = 'uuid'
    PRIMARY_KEY_PATTERN = re.compile(
        r"(?:public\s+)?static\s+primaryKey\s*=\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )

    # Column decorator: @column() or @column({ isPrimary: true }) or @column.date() or @column.dateTime()
    COLUMN_PATTERN = re.compile(
        r'@column(?:\.(\w+))?\s*\(([^)]*)\)\s*(?:public\s+)?(?:declare\s+)?(\w+)',
        re.MULTILINE,
    )

    # Relationship decorators
    RELATIONSHIP_PATTERN = re.compile(
        r'@(hasMany|belongsTo|manyToMany|hasOne|hasManyThrough)\s*\(\s*\(\)\s*=>\s*(\w+)',
        re.MULTILINE,
    )

    # Relationship with options: @hasMany(() => Post, { foreignKey: 'authorId' })
    RELATIONSHIP_OPTIONS_PATTERN = re.compile(
        r'@(hasMany|belongsTo|manyToMany|hasOne|hasManyThrough)\s*\(\s*\(\)\s*=>\s*(\w+)\s*,?\s*(?:\{([^}]*)\})?\)',
        re.MULTILINE,
    )

    # Property name after relationship decorator
    RELATIONSHIP_PROP_PATTERN = re.compile(
        r'(?:public\s+)?(?:declare\s+)?(\w+)\s*:',
        re.MULTILINE,
    )

    # Hook decorators: @beforeSave(), @afterFind(), @beforeCreate(), etc.
    HOOK_PATTERN = re.compile(
        r'@(before(?:Save|Create|Update|Delete|Find|Fetch|Paginate)|'
        r'after(?:Save|Create|Update|Delete|Find|Fetch|Paginate))\s*\(\s*\)',
        re.MULTILINE,
    )

    # Hook method following the decorator
    HOOK_METHOD_PATTERN = re.compile(
        r'(?:public\s+)?static\s+(?:async\s+)?(\w+)',
        re.MULTILINE,
    )

    # Computed property: @computed()
    COMPUTED_PATTERN = re.compile(
        r'@computed\s*\(\s*\)\s*(?:public\s+)?get\s+(\w+)',
        re.MULTILINE,
    )

    # Query scope: public static scopeActive(query)  (v4)
    SCOPE_PATTERN = re.compile(
        r'(?:public\s+)?static\s+scope(\w+)\s*\(',
        re.MULTILINE,
    )

    # v5/v6 scope: public static published = scope((query) => { ... })
    V5_SCOPE_PATTERN = re.compile(
        r'(?:public\s+)?static\s+(\w+)\s*=\s*scope\s*\(',
        re.MULTILINE,
    )

    # v4 traits: static get traits() { return ['@provider:SoftDeletes', ...] }
    TRAITS_PATTERN = re.compile(
        r"static\s+get\s+traits\s*\(\s*\)\s*\{[^}]*return\s*\[([^\]]*)\]",
        re.DOTALL,
    )

    # Soft deletes indicator
    SOFT_DELETE_PATTERN = re.compile(
        r'SoftDeletes|deletedAt|@column\.dateTime.*deletedAt',
        re.MULTILINE,
    )

    # Timestamps
    TIMESTAMPS_PATTERN = re.compile(
        r'createdAt|updatedAt|@column\.dateTime\s*\(\s*\{\s*autoCreate\s*:\s*true',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all AdonisJS model information from source code.

        Returns:
            Dict with 'models' (List[AdonisModelInfo])
        """
        models: List[AdonisModelInfo] = []

        # Find model classes
        for match in list(self.MODEL_CLASS_PATTERN.finditer(content)) + \
                      list(self.V4_MODEL_PATTERN.finditer(content)):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            model = AdonisModelInfo(
                name=name,
                file=file_path,
                line_number=line_number,
            )

            # Get class body
            class_start = match.end()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]

            # Table name
            table_match = self.TABLE_PATTERN.search(class_body)
            if table_match:
                model.table = table_match.group(1) or table_match.group(2) or ''

            # Primary key
            pk_match = self.PRIMARY_KEY_PATTERN.search(class_body)
            if pk_match:
                model.primary_key = pk_match.group(1)

            # Columns
            model.columns = self._extract_columns(class_body)

            # Relationships
            model.relationships = self._extract_relationships(class_body, line_number)

            # Hooks
            model.hooks = self._extract_hooks(class_body, line_number)

            # Computed properties
            for comp_match in self.COMPUTED_PATTERN.finditer(class_body):
                model.computed_properties.append(comp_match.group(1))

            # Scopes (v4 pattern: scopeActive)
            for scope_match in self.SCOPE_PATTERN.finditer(class_body):
                scope_name = scope_match.group(1)
                # Convert PascalCase to camelCase
                model.scopes.append(scope_name[0].lower() + scope_name[1:])

            # Scopes (v5/v6 pattern: published = scope(...))
            for scope_match in self.V5_SCOPE_PATTERN.finditer(class_body):
                scope_name = scope_match.group(1)
                if scope_name not in model.scopes:
                    model.scopes.append(scope_name)

            # Soft deletes
            model.has_soft_deletes = bool(self.SOFT_DELETE_PATTERN.search(class_body))

            # Timestamps
            model.has_timestamps = bool(self.TIMESTAMPS_PATTERN.search(class_body))

            # v4 traits
            traits_match = self.TRAITS_PATTERN.search(class_body)
            if traits_match:
                traits_str = traits_match.group(1)
                model.traits = [t.strip().strip("'\"") for t in traits_str.split(',') if t.strip()]

            models.append(model)

        return {'models': models}

    def _extract_columns(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract column declarations."""
        columns = []
        for match in self.COLUMN_PATTERN.finditer(class_body):
            col_type = match.group(1) or 'default'  # date, dateTime, or default
            options_str = match.group(2).strip()
            name = match.group(3)

            col = {
                'name': name,
                'type': col_type,
            }

            # Parse options
            if options_str:
                if 'isPrimary' in options_str and 'true' in options_str:
                    col['isPrimary'] = True
                if 'autoCreate' in options_str and 'true' in options_str:
                    col['autoCreate'] = True
                if 'autoUpdate' in options_str and 'true' in options_str:
                    col['autoUpdate'] = True
                if 'serializeAs' in options_str:
                    serialize_match = re.search(r"serializeAs\s*:\s*['\"](\w+)['\"]", options_str)
                    if serialize_match:
                        col['serializeAs'] = serialize_match.group(1)

            columns.append(col)

        return columns

    def _extract_relationships(self, class_body: str, base_line: int) -> List[AdonisRelationshipInfo]:
        """Extract relationship declarations."""
        relationships = []

        for match in self.RELATIONSHIP_OPTIONS_PATTERN.finditer(class_body):
            rel_type = match.group(1)
            related_model = match.group(2)
            options_str = match.group(3) or ''
            line_number = base_line + class_body[:match.start()].count('\n')

            rel = AdonisRelationshipInfo(
                type=rel_type,
                related_model=related_model,
                line_number=line_number,
            )

            # Try to get the property name
            rest = class_body[match.end():]
            prop_match = self.RELATIONSHIP_PROP_PATTERN.search(rest[:100])
            if prop_match:
                rel.name = prop_match.group(1)

            # Parse options
            if options_str:
                fk_match = re.search(r"foreignKey\s*:\s*['\"](\w+)['\"]", options_str)
                if fk_match:
                    rel.foreign_key = fk_match.group(1)

                lk_match = re.search(r"localKey\s*:\s*['\"](\w+)['\"]", options_str)
                if lk_match:
                    rel.local_key = lk_match.group(1)

                pivot_match = re.search(r"pivotTable\s*:\s*['\"](\w+)['\"]", options_str)
                if pivot_match:
                    rel.pivot_table = pivot_match.group(1)

            relationships.append(rel)

        return relationships

    def _extract_hooks(self, class_body: str, base_line: int) -> List[AdonisModelHookInfo]:
        """Extract model hook declarations."""
        hooks = []

        for match in self.HOOK_PATTERN.finditer(class_body):
            event = match.group(1)
            line_number = base_line + class_body[:match.start()].count('\n')

            hook = AdonisModelHookInfo(
                event=event,
                line_number=line_number,
                is_static=True,
            )

            # Find the method name following the decorator
            rest = class_body[match.end():]
            method_match = self.HOOK_METHOD_PATTERN.search(rest[:200])
            if method_match:
                hook.method = method_match.group(1)

            hooks.append(hook)

        return hooks

    @staticmethod
    def _find_class_end(content: str, start: int) -> int:
        """Find the end of a class body by counting braces."""
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
            i += 1
        return i
