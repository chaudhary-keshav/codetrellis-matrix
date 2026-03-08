"""
Dart Model Extractor for CodeTrellis

Extracts database/ORM model definitions from Dart source code:
- Drift (formerly Moor) tables and DAOs
- Floor entities and DAOs
- Isar collections
- Hive type adapters
- ObjectBox entities
- Freezed data classes
- JsonSerializable models
- Firebase Firestore models
- Serverpod model definitions

Supports:
- Code generation annotations (@freezed, @JsonSerializable, etc.)
- Null-safe model definitions
- Immutable data classes
- Serialization/deserialization patterns

Part of CodeTrellis v4.27 - Dart Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DartModelInfo:
    """Information about a database/ORM model."""
    name: str
    file: str = ""
    orm: str = ""  # drift, floor, isar, hive, objectbox, firebase, serverpod
    framework: str = ""  # alias for orm (used by scanner)
    table_name: str = ""
    columns: List[Dict[str, str]] = field(default_factory=list)
    fields: List[Dict[str, str]] = field(default_factory=list)
    primary_key: str = ""
    indexes: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartDataClassInfo:
    """Information about a data class (Freezed, JsonSerializable, etc.)."""
    name: str
    file: str = ""
    pattern: str = ""  # freezed, json_serializable, built_value, equatable
    framework: str = ""  # alias for pattern (used by scanner)
    fields: List[Dict[str, str]] = field(default_factory=list)
    has_json: bool = False
    has_copy_with: bool = False
    is_union: bool = False
    union_cases: List[str] = field(default_factory=list)
    doc_comment: str = ""
    line_number: int = 0


@dataclass
class DartMigrationInfo:
    """Information about a database migration."""
    name: str
    file: str = ""
    version: int = 0
    orm: str = ""
    framework: str = ""  # alias for orm (used by scanner)
    line_number: int = 0


class DartModelExtractor:
    """
    Extracts database model and data class definitions from Dart source code.

    Detects:
    - Drift tables (@DataClassName, Table)
    - Floor entities (@Entity, @dao)
    - Isar collections (@collection)
    - Hive type adapters (@HiveType)
    - ObjectBox entities (@Entity)
    - Freezed classes (@freezed, @unfreezed)
    - JsonSerializable models (@JsonSerializable)
    - Firebase models
    - Built Value classes
    - Equatable classes
    """

    # Drift table pattern
    DRIFT_TABLE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+Table\b',
        re.MULTILINE
    )

    # Drift DataClassName annotation
    DRIFT_DATACLASS_PATTERN = re.compile(
        r"@DataClassName\s*\(\s*['\"](?P<name>[^'\"]+)['\"]\s*\)",
        re.MULTILINE
    )

    # Floor entity pattern
    FLOOR_ENTITY_PATTERN = re.compile(
        r'@(?:Entity|entity)\s*(?:\([^)]*\))?\s*\n\s*class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Floor DAO pattern
    FLOOR_DAO_PATTERN = re.compile(
        r'@(?:dao|Dao)\s*\n\s*abstract\s+class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Isar collection pattern
    ISAR_COLLECTION_PATTERN = re.compile(
        r'@(?:collection|Collection)\s*(?:\([^)]*\))?\s*\n\s*class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Hive type adapter pattern
    HIVE_TYPE_PATTERN = re.compile(
        r'@HiveType\s*\(\s*typeId:\s*(?P<type_id>\d+)\s*\)\s*\n\s*class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # ObjectBox entity pattern
    OBJECTBOX_ENTITY_PATTERN = re.compile(
        r'@Entity\s*(?:\([^)]*\))?\s*\n\s*class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Freezed pattern
    FREEZED_PATTERN = re.compile(
        r'@(?:freezed|Freezed|unfreezed)\s*(?:\([^)]*\))?\s*\n\s*'
        r'(?:abstract\s+)?class\s+(?P<name>\w+)\s+with\s+_\$(?P=name)',
        re.MULTILINE
    )

    # Freezed union case pattern
    FREEZED_UNION_CASE_PATTERN = re.compile(
        r'(?:const\s+)?factory\s+\w+\.(?P<case>\w+)\s*\(',
        re.MULTILINE
    )

    # JsonSerializable pattern
    JSON_SERIALIZABLE_PATTERN = re.compile(
        r'@JsonSerializable\s*(?:\([^)]*\))?\s*\n\s*class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Built Value pattern
    BUILT_VALUE_PATTERN = re.compile(
        r'abstract\s+class\s+(?P<name>\w+)\s+implements\s+Built<(?P=name),\s*\w+Builder>',
        re.MULTILINE
    )

    # Equatable pattern
    EQUATABLE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+extends\s+Equatable\b',
        re.MULTILINE
    )

    # Floor migration pattern
    FLOOR_MIGRATION_PATTERN = re.compile(
        r'Migration\s*\(\s*(?P<from>\d+)\s*,\s*(?P<to>\d+)',
        re.MULTILINE
    )

    # Drift migration/schema version pattern
    DRIFT_MIGRATION_PATTERN = re.compile(
        r'@override\s+int\s+get\s+schemaVersion\s*=>\s*(?P<version>\d+)',
        re.MULTILINE
    )

    # Field pattern (for model field extraction)
    MODEL_FIELD_PATTERN = re.compile(
        r'^\s*(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:(?:final|late|static|const)\s+)*'
        r'(?P<type>\w+(?:<[^>]+>)?(?:\?)?)\s+'
        r'(?P<name>\w+)\s*[;=]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all model/data class definitions from Dart source code.

        Returns:
            Dict with 'models', 'data_classes', 'migrations' lists.
        """
        result: Dict[str, Any] = {
            'models': [],
            'data_classes': [],
            'migrations': [],
        }

        result['models'] = self._extract_models(content, file_path)
        result['data_classes'] = self._extract_data_classes(content, file_path)
        result['migrations'] = self._extract_migrations(content, file_path)

        return result

    def _extract_models(self, content: str, file_path: str) -> List[DartModelInfo]:
        """Extract ORM model definitions."""
        models = []

        # Drift tables
        for match in self.DRIFT_TABLE_PATTERN.finditer(content):
            name = match.group('name')
            fields = self._extract_drift_columns(content, match.end())
            models.append(DartModelInfo(
                name=name,
                file=file_path,
                orm="drift",
                fields=fields,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Floor entities
        for match in self.FLOOR_ENTITY_PATTERN.finditer(content):
            name = match.group('name')
            fields = self._extract_model_fields(content, match.end())
            pk = self._find_primary_key(content, match.end())
            models.append(DartModelInfo(
                name=name,
                file=file_path,
                orm="floor",
                fields=fields,
                primary_key=pk,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Isar collections
        for match in self.ISAR_COLLECTION_PATTERN.finditer(content):
            name = match.group('name')
            fields = self._extract_model_fields(content, match.end())
            models.append(DartModelInfo(
                name=name,
                file=file_path,
                orm="isar",
                fields=fields,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Hive types
        for match in self.HIVE_TYPE_PATTERN.finditer(content):
            name = match.group('name')
            fields = self._extract_model_fields(content, match.end())
            models.append(DartModelInfo(
                name=name,
                file=file_path,
                orm="hive",
                fields=fields,
                annotations=[f"typeId:{match.group('type_id')}"],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ObjectBox entities
        for match in self.OBJECTBOX_ENTITY_PATTERN.finditer(content):
            # Avoid duplicate with Floor @Entity (check for 'extends Table' or other Floor markers)
            area_before = content[max(0, match.start() - 100):match.start()]
            if '@dao' in area_before.lower() or '@entity' in area_before.lower():
                # Check if Floor-specific
                area_after = content[match.end():match.end() + 500]
                if 'obx.id' in area_after.lower() or '@Id' in area_after or 'objectbox' in content[:500].lower():
                    name = match.group('name')
                    fields = self._extract_model_fields(content, match.end())
                    models.append(DartModelInfo(
                        name=name,
                        file=file_path,
                        orm="objectbox",
                        fields=fields,
                        line_number=content[:match.start()].count('\n') + 1,
                    ))

        return models

    def _extract_data_classes(self, content: str, file_path: str) -> List[DartDataClassInfo]:
        """Extract data class definitions (Freezed, JsonSerializable, etc.)."""
        data_classes = []

        # Freezed classes
        for match in self.FREEZED_PATTERN.finditer(content):
            name = match.group('name')
            # Find union cases
            union_cases = []
            body_start = match.end()
            body_area = content[body_start:body_start + 2000]
            for case_match in self.FREEZED_UNION_CASE_PATTERN.finditer(body_area):
                union_cases.append(case_match.group('case'))

            is_union = len(union_cases) > 0

            data_classes.append(DartDataClassInfo(
                name=name,
                file=file_path,
                pattern="freezed",
                has_json='fromJson' in body_area or '@JsonSerializable' in body_area,
                has_copy_with=True,  # Freezed always generates copyWith
                is_union=is_union,
                union_cases=union_cases[:10],
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # JsonSerializable classes
        for match in self.JSON_SERIALIZABLE_PATTERN.finditer(content):
            name = match.group('name')
            # Skip if already captured as Freezed
            if any(dc.name == name for dc in data_classes):
                continue

            fields = self._extract_model_fields(content, match.end())
            data_classes.append(DartDataClassInfo(
                name=name,
                file=file_path,
                pattern="json_serializable",
                fields=fields,
                has_json=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Built Value classes
        for match in self.BUILT_VALUE_PATTERN.finditer(content):
            name = match.group('name')
            data_classes.append(DartDataClassInfo(
                name=name,
                file=file_path,
                pattern="built_value",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Equatable classes
        for match in self.EQUATABLE_PATTERN.finditer(content):
            name = match.group('name')
            data_classes.append(DartDataClassInfo(
                name=name,
                file=file_path,
                pattern="equatable",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return data_classes

    def _extract_migrations(self, content: str, file_path: str) -> List[DartMigrationInfo]:
        """Extract database migration definitions."""
        migrations = []

        # Floor migrations
        for match in self.FLOOR_MIGRATION_PATTERN.finditer(content):
            migrations.append(DartMigrationInfo(
                name=f"migration_{match.group('from')}_to_{match.group('to')}",
                file=file_path,
                version=int(match.group('to')),
                orm="floor",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Drift schema version
        for match in self.DRIFT_MIGRATION_PATTERN.finditer(content):
            migrations.append(DartMigrationInfo(
                name=f"schema_v{match.group('version')}",
                file=file_path,
                version=int(match.group('version')),
                orm="drift",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return migrations

    def _extract_drift_columns(self, content: str, start: int) -> List[Dict[str, str]]:
        """Extract Drift table column definitions."""
        fields = []
        area = content[start:start + 1000]

        column_pattern = re.compile(
            r'(?:IntColumn|TextColumn|BoolColumn|DateTimeColumn|RealColumn|BlobColumn)\s+'
            r'get\s+(?P<name>\w+)',
            re.MULTILINE
        )
        for match in column_pattern.finditer(area):
            col_type = content[start + match.start():start + match.end()].split()[0]
            type_map = {
                'IntColumn': 'int', 'TextColumn': 'String', 'BoolColumn': 'bool',
                'DateTimeColumn': 'DateTime', 'RealColumn': 'double', 'BlobColumn': 'Uint8List',
            }
            fields.append({
                'name': match.group('name'),
                'type': type_map.get(col_type, col_type),
            })

        return fields[:30]

    def _extract_model_fields(self, content: str, start: int) -> List[Dict[str, str]]:
        """Extract field definitions from a model class body."""
        fields = []
        area = content[start:start + 1000]

        for match in self.MODEL_FIELD_PATTERN.finditer(area):
            name = match.group('name')
            if name in ('super', 'this', 'return', 'if', 'else', 'for', 'while'):
                continue
            fields.append({
                'name': name,
                'type': match.group('type'),
            })

        return fields[:30]

    def _find_primary_key(self, content: str, start: int) -> str:
        """Find primary key annotation in a model."""
        area = content[start:start + 500]
        pk_match = re.search(r'@(?:PrimaryKey|primaryKey)\s*(?:\([^)]*\))?\s*\n\s*\w+\s+(\w+)', area)
        if pk_match:
            return pk_match.group(1)
        # Check for @Id annotation
        id_match = re.search(r'@Id\s*(?:\([^)]*\))?\s*\n\s*\w+\s+(\w+)', area)
        if id_match:
            return id_match.group(1)
        return ""
