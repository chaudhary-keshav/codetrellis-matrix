"""
Swift Model Extractor for CodeTrellis

Extracts data model patterns from Swift source code:
- Core Data entities (@NSManaged, NSManagedObject)
- SwiftData models (@Model, @Attribute, @Relationship, @Query)
- GRDB records (Record, PersistableRecord, FetchableRecord)
- Realm objects (Object, EmbeddedObject)
- Codable types (Codable, Encodable, Decodable, CodingKeys)
- Firebase models (DocumentSnapshot mapping)
- Migration patterns (NSPersistentContainer, Schema versioning)

Part of CodeTrellis v4.22 - Swift Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SwiftModelInfo:
    """Information about a data model."""
    name: str
    file: str = ""
    framework: str = ""  # core_data, swift_data, grdb, realm, codable
    fields: List[Dict[str, str]] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    unique_constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    is_codable: bool = False
    coding_keys: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftMigrationInfo:
    """Information about a database migration."""
    name: str
    file: str = ""
    framework: str = ""
    version: str = ""
    operations: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SwiftCodableInfo:
    """Information about a Codable conformance."""
    name: str
    file: str = ""
    coding_keys: List[Dict[str, str]] = field(default_factory=list)
    custom_decode: bool = False
    custom_encode: bool = False
    nested_containers: List[str] = field(default_factory=list)
    line_number: int = 0


class SwiftModelExtractor:
    """
    Extracts data model patterns from Swift source code.

    Supports:
    - Core Data (NSManagedObject, @NSManaged)
    - SwiftData (@Model, @Attribute, @Relationship, @Query)
    - GRDB (Record, PersistableRecord, FetchableRecord)
    - Realm (Object, EmbeddedObject, @Persisted)
    - Codable (CodingKeys, custom encode/decode)
    """

    # Core Data entity pattern
    CORE_DATA_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s*:\s*[^{]*NSManagedObject[^{]*\{',
        re.MULTILINE
    )

    # @NSManaged property
    NSMANAGED_PATTERN = re.compile(
        r'@NSManaged\s+(?:public\s+)?var\s+(?P<name>\w+)\s*:\s*(?P<type>[^\n{]+)',
        re.MULTILINE
    )

    # SwiftData @Model pattern
    SWIFT_DATA_PATTERN = re.compile(
        r'@Model\s*(?:\([^)]*\))?\s*'
        r'(?:(?:public|internal|fileprivate|private)\s+)?'
        r'(?:final\s+)?class\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # SwiftData @Attribute
    SWIFT_DATA_ATTRIBUTE_PATTERN = re.compile(
        r'@Attribute\s*(?:\((?P<options>[^)]*)\))?\s*'
        r'var\s+(?P<name>\w+)\s*:\s*(?P<type>[^\n{=]+)',
        re.MULTILINE
    )

    # SwiftData @Relationship
    SWIFT_DATA_RELATIONSHIP_PATTERN = re.compile(
        r'@Relationship\s*(?:\((?P<options>[^)]*)\))?\s*'
        r'var\s+(?P<name>\w+)\s*:\s*(?P<type>[^\n{=]+)',
        re.MULTILINE
    )

    # GRDB Record pattern
    GRDB_PATTERN = re.compile(
        r'(?:class|struct)\s+(?P<name>\w+)\s*:\s*[^{]*'
        r'(?:Record|PersistableRecord|FetchableRecord|TableRecord)\b[^{]*\{',
        re.MULTILINE
    )

    # Realm Object pattern
    REALM_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s*:\s*[^{]*'
        r'(?:Object|EmbeddedObject)\b[^{]*\{',
        re.MULTILINE
    )

    # @Persisted property (Realm)
    PERSISTED_PATTERN = re.compile(
        r'@Persisted\s*(?:\((?P<options>[^)]*)\))?\s*'
        r'var\s+(?P<name>\w+)\s*:\s*(?P<type>[^\n{=]+)',
        re.MULTILINE
    )

    # Codable conformance pattern
    CODABLE_PATTERN = re.compile(
        r'(?:class|struct|enum)\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*:\s*[^{]*'
        r'(?:Codable|Encodable|Decodable)\b[^{]*\{',
        re.MULTILINE
    )

    # CodingKeys enum
    CODING_KEYS_PATTERN = re.compile(
        r'enum\s+CodingKeys\s*:\s*[^{]*\{(?P<body>[^}]+)\}',
        re.MULTILINE
    )

    # Migration pattern
    MIGRATION_PATTERN = re.compile(
        r'(?:class|struct)\s+(?P<name>\w+)\s*:\s*[^{]*Migration\b[^{]*\{',
        re.MULTILINE
    )

    # Schema version pattern (SwiftData)
    SCHEMA_VERSION_PATTERN = re.compile(
        r'Schema\s*\(\s*(?P<version>[^,)]+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract data model patterns from Swift source code.

        Args:
            content: Swift source code
            file_path: Path to source file

        Returns:
            Dict with keys: models, migrations, codables
        """
        return {
            'models': self._extract_models(content, file_path),
            'migrations': self._extract_migrations(content, file_path),
            'codables': self._extract_codables(content, file_path),
        }

    def _extract_models(self, content: str, file_path: str) -> List[SwiftModelInfo]:
        """Extract data model definitions."""
        models = []

        # Core Data entities
        for match in self.CORE_DATA_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            fields = []
            relationships = []
            for prop in self.NSMANAGED_PATTERN.finditer(body):
                prop_name = prop.group('name')
                prop_type = prop.group('type').strip()
                if 'Set<' in prop_type or 'NSSet' in prop_type or 'NSOrderedSet' in prop_type:
                    relationships.append({'name': prop_name, 'type': prop_type})
                else:
                    fields.append({'name': prop_name, 'type': prop_type})

            line_number = content[:match.start()].count('\n') + 1
            models.append(SwiftModelInfo(
                name=name, file=file_path, framework='core_data',
                fields=fields, relationships=relationships,
                line_number=line_number,
            ))

        # SwiftData models
        for match in self.SWIFT_DATA_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            fields = []
            relationships = []
            unique = []
            indexes = []

            for attr in self.SWIFT_DATA_ATTRIBUTE_PATTERN.finditer(body):
                options = attr.group('options') or ''
                fields.append({
                    'name': attr.group('name'),
                    'type': attr.group('type').strip(),
                    'options': options,
                })
                if '.unique' in options:
                    unique.append(attr.group('name'))

            for rel in self.SWIFT_DATA_RELATIONSHIP_PATTERN.finditer(body):
                relationships.append({
                    'name': rel.group('name'),
                    'type': rel.group('type').strip(),
                    'options': (rel.group('options') or ''),
                })

            # Also extract plain var/let properties
            for prop in re.finditer(r'(?<!@\w{1,20}\s)(?:var|let)\s+(\w+)\s*:\s*([^\n{=]+)', body):
                prop_name = prop.group(1)
                prop_type = prop.group(2).strip()
                # Skip if already found via @Attribute
                if not any(f['name'] == prop_name for f in fields):
                    fields.append({'name': prop_name, 'type': prop_type})

            line_number = content[:match.start()].count('\n') + 1
            models.append(SwiftModelInfo(
                name=name, file=file_path, framework='swift_data',
                fields=fields, relationships=relationships,
                unique_constraints=unique,
                line_number=line_number,
            ))

        # GRDB Records
        for match in self.GRDB_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            fields = []
            for prop in re.finditer(r'(?:var|let)\s+(\w+)\s*:\s*([^\n{=]+)', body):
                fields.append({'name': prop.group(1), 'type': prop.group(2).strip()})

            line_number = content[:match.start()].count('\n') + 1
            models.append(SwiftModelInfo(
                name=name, file=file_path, framework='grdb',
                fields=fields,
                line_number=line_number,
            ))

        # Realm Objects
        for match in self.REALM_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            fields = []
            relationships = []
            for prop in self.PERSISTED_PATTERN.finditer(body):
                prop_name = prop.group('name')
                prop_type = prop.group('type').strip()
                options = prop.group('options') or ''
                if 'List<' in prop_type or 'LinkingObjects' in prop_type or 'MutableSet<' in prop_type:
                    relationships.append({'name': prop_name, 'type': prop_type})
                else:
                    fields.append({'name': prop_name, 'type': prop_type, 'options': options})

            line_number = content[:match.start()].count('\n') + 1
            models.append(SwiftModelInfo(
                name=name, file=file_path, framework='realm',
                fields=fields, relationships=relationships,
                line_number=line_number,
            ))

        return models

    def _extract_migrations(self, content: str, file_path: str) -> List[SwiftMigrationInfo]:
        """Extract migration definitions."""
        migrations = []
        for match in self.MIGRATION_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            operations = []
            if 'addColumn' in body or 'add(column' in body:
                operations.append('add_column')
            if 'createTable' in body or 'create(table' in body:
                operations.append('create_table')
            if 'dropTable' in body or 'drop(table' in body:
                operations.append('drop_table')
            if 'renameColumn' in body or 'rename(column' in body:
                operations.append('rename_column')
            if 'createIndex' in body or 'addIndex' in body:
                operations.append('create_index')

            line_number = content[:match.start()].count('\n') + 1
            migrations.append(SwiftMigrationInfo(
                name=name, file=file_path,
                operations=operations,
                line_number=line_number,
            ))

        # SwiftData schema versions
        for match in self.SCHEMA_VERSION_PATTERN.finditer(content):
            version = match.group('version').strip().strip('"')
            line_number = content[:match.start()].count('\n') + 1
            migrations.append(SwiftMigrationInfo(
                name=f'Schema_v{version}', file=file_path,
                framework='swift_data', version=version,
                line_number=line_number,
            ))

        return migrations

    def _extract_codables(self, content: str, file_path: str) -> List[SwiftCodableInfo]:
        """Extract Codable conformance details."""
        codables = []
        for match in self.CODABLE_PATTERN.finditer(content):
            name = match.group('name')
            body_start = content.find('{', match.start())
            body = self._extract_brace_body(content, body_start) if body_start >= 0 else ''

            coding_keys = []
            ck_match = self.CODING_KEYS_PATTERN.search(body)
            if ck_match:
                ck_body = ck_match.group('body')
                for case_match in re.finditer(r'case\s+(\w+)\s*(?:=\s*"([^"]*)")?', ck_body):
                    key_name = case_match.group(1)
                    raw_val = case_match.group(2) or key_name
                    coding_keys.append({'swift_name': key_name, 'json_key': raw_val})

            custom_decode = 'init(from decoder:' in body or 'init(from decoder :' in body
            custom_encode = 'func encode(to encoder:' in body or 'func encode(to encoder :' in body

            nested_containers = re.findall(r'nestedContainer\s*\(\s*keyedBy:\s*(\w+)', body)

            line_number = content[:match.start()].count('\n') + 1
            codables.append(SwiftCodableInfo(
                name=name, file=file_path,
                coding_keys=coding_keys,
                custom_decode=custom_decode,
                custom_encode=custom_encode,
                nested_containers=nested_containers,
                line_number=line_number,
            ))

        return codables

    def _extract_brace_body(self, content: str, open_pos: int) -> str:
        """Extract body between matching braces."""
        if open_pos >= len(content) or content[open_pos] != '{':
            return ""
        depth = 0
        i = open_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[open_pos + 1:i]
            i += 1
        return content[open_pos + 1:]
