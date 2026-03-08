"""
KotlinModelExtractor - Extracts Kotlin data model definitions.

Extracts:
- JPA/Hibernate entities (@Entity, @Table)
- Spring Data repositories (CrudRepository, JpaRepository, etc.)
- Exposed table objects (org.jetbrains.exposed)
- Room entities (Android persistence)
- kotlinx.serialization models (@Serializable)
- Data transfer objects (DTOs)
- Panache entities (Quarkus)
- Ktor ContentNegotiation data classes
- Realm model classes
- Arrow optics lenses

Part of CodeTrellis v4.21 - Kotlin Language Support Upgrade
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KotlinEntityInfo:
    """Information about a Kotlin JPA entity or data model."""
    name: str
    table_name: str = ""
    orm: str = ""  # jpa, exposed, room, realm, panache
    columns: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    primary_key: Optional[str] = None
    indices: List[str] = field(default_factory=list)
    is_data_class: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinRepositoryInfo:
    """Information about a Kotlin repository."""
    name: str
    entity_type: str = ""
    id_type: str = ""
    extends: str = ""  # CrudRepository, JpaRepository, etc.
    custom_methods: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    framework: str = ""  # spring-data, quarkus-panache, micronaut-data
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinExposedTableInfo:
    """Information about a Kotlin Exposed table object."""
    name: str
    table_name: str = ""
    columns: List[Dict[str, str]] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    primary_key: Optional[str] = None
    is_id_table: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinSerializableInfo:
    """Information about a kotlinx.serializable data class."""
    name: str
    serial_name: str = ""
    properties: List[Dict[str, str]] = field(default_factory=list)
    is_sealed: bool = False
    discriminator: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class KotlinDTOInfo:
    """Information about a Kotlin DTO."""
    name: str
    properties: List[Dict[str, str]] = field(default_factory=list)
    mapper_pattern: str = ""  # mapstruct, manual, extension-function
    file: str = ""
    line_number: int = 0


class KotlinModelExtractor:
    """
    Extracts Kotlin data model definitions from source code.

    Handles:
    - JPA/Hibernate entities with relationships
    - Spring Data / Micronaut Data repositories
    - Exposed table objects and DSL
    - Room entities (Android)
    - kotlinx.serialization models
    - Panache entities (Quarkus)
    - DTO detection
    """

    # JPA Entity pattern
    ENTITY_PATTERN = re.compile(
        r'@Entity\s*(?:\([^)]*\))?\s*'
        r'(?:@Table\s*\(\s*(?:name\s*=\s*)?"(\w+)"[^)]*\)\s*)?'
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:data\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # JPA Column annotations
    COLUMN_PATTERN = re.compile(
        r'@Column\s*\(([^)]*)\)\s*'
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)?'
        r'(?:var|val)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)',
        re.MULTILINE
    )

    # JPA Relationship annotations
    RELATIONSHIP_PATTERN = re.compile(
        r'@(OneToMany|ManyToOne|OneToOne|ManyToMany)\s*(?:\(([^)]*)\))?\s*'
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)?'
        r'(?:var|val)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)',
        re.MULTILINE
    )

    # JPA Id annotation
    ID_PATTERN = re.compile(
        r'@Id\s*(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)?'
        r'(?:var|val)\s+(\w+)',
        re.MULTILINE
    )

    # Repository pattern
    REPOSITORY_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'interface\s+(\w+)\s*:\s*'
        r'((?:Crud|Jpa|Paging|PagingAndSorting|Reactive|R2dbc|CoroutineCrud|CoroutineSorting|'
        r'ListCrud|ListPaging|MongoRepository|QueryByExample|QueryDsl|'
        r'Panache|PanacheRepository|PanacheEntityBase|'
        r'CrudRepository|PageableRepository)Repository)\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Exposed Table object
    EXPOSED_TABLE_PATTERN = re.compile(
        r'object\s+(\w+)\s*:\s*(Table|IntIdTable|LongIdTable|UUIDTable|CompositeIdTable)\s*\(\s*(?:"(\w+)")?\s*\)',
        re.MULTILINE
    )

    # Exposed column definition
    EXPOSED_COLUMN_PATTERN = re.compile(
        r'val\s+(\w+)\s*=\s*(integer|long|varchar|text|bool|blob|date|datetime|timestamp|float|double|decimal|uuid|binary|reference)\s*\(',
        re.MULTILINE
    )

    # Exposed reference
    EXPOSED_REFERENCE_PATTERN = re.compile(
        r'val\s+\w+\s*=\s*reference\s*\(\s*"[^"]*"\s*,\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # kotlinx.serialization
    SERIALIZABLE_PATTERN = re.compile(
        r'@Serializable\s*(?:\([^)]*\))?\s*'
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:data\s+)?(?:sealed\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # SerialName annotation
    SERIAL_NAME_PATTERN = re.compile(
        r'@SerialName\s*\(\s*"([^"]+)"\s*\)',
    )

    # Room entity (Android)
    ROOM_ENTITY_PATTERN = re.compile(
        r'@Entity\s*\(\s*tableName\s*=\s*"(\w+)"[^)]*\)\s*'
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'data\s+class\s+(\w+)',
        re.MULTILINE
    )

    # Room DAO
    ROOM_DAO_PATTERN = re.compile(
        r'@Dao\s*\s*interface\s+(\w+)',
        re.MULTILINE
    )

    # Panache entity (Quarkus)
    PANACHE_ENTITY_PATTERN = re.compile(
        r'class\s+(\w+)\s*(?:\([^)]*\))?\s*:\s*PanacheEntity(?:Base)?\s*\(',
        re.MULTILINE
    )

    # DTO heuristic: classes ending in Dto/DTO/Response/Request
    DTO_PATTERN = re.compile(
        r'(?:data\s+)?class\s+(\w+(?:Dto|DTO|Response|Request|Command|Event|Message))\s*\(',
        re.MULTILINE
    )

    # Property for DTO extraction
    DTO_PROPERTY_PATTERN = re.compile(
        r'(?:val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all data model definitions from Kotlin source code.

        Returns dict with keys: entities, repositories, exposed_tables,
                                serializables, dtos
        """
        result = {
            'entities': [],
            'repositories': [],
            'exposed_tables': [],
            'serializables': [],
            'dtos': [],
        }

        if not content or not content.strip():
            return result

        # Extract JPA entities
        self._extract_jpa_entities(content, file_path, result)

        # Extract repositories
        self._extract_repositories(content, file_path, result)

        # Extract Exposed tables
        self._extract_exposed_tables(content, file_path, result)

        # Extract kotlinx.serialization models
        self._extract_serializables(content, file_path, result)

        # Extract Panache entities
        self._extract_panache_entities(content, file_path, result)

        # Extract Room entities (Android)
        self._extract_room_entities(content, file_path, result)

        # Extract DTOs
        self._extract_dtos(content, file_path, result)

        return result

    def _extract_jpa_entities(self, content: str, file_path: str,
                               result: Dict[str, Any]):
        """Extract JPA/Hibernate entity definitions."""
        for match in self.ENTITY_PATTERN.finditer(content):
            table_name = match.group(1) or ""
            class_name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Extract body
            brace_pos = content.find('{', match.end())
            body = self._extract_body(content, brace_pos) if brace_pos >= 0 else ""

            # Extract columns
            columns = []
            for col_match in self.COLUMN_PATTERN.finditer(body):
                col_attrs = col_match.group(1)
                col_name = col_match.group(2)
                col_type = col_match.group(3).strip()
                nullable = 'nullable' in col_attrs and 'false' not in col_attrs.split('nullable')[1][:10]
                unique = 'unique' in col_attrs and 'true' in col_attrs.split('unique')[1][:10]
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': nullable,
                    'unique': unique,
                })

            # Also extract properties without @Column
            for prop_match in re.finditer(r'(?:var|val)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', body):
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2).strip()
                if not any(c['name'] == prop_name for c in columns):
                    columns.append({
                        'name': prop_name,
                        'type': prop_type,
                        'nullable': '?' in prop_type,
                        'unique': False,
                    })

            # Extract relationships
            relationships = []
            for rel_match in self.RELATIONSHIP_PATTERN.finditer(body):
                rel_type = rel_match.group(1)
                rel_attrs = rel_match.group(2) or ""
                field_name = rel_match.group(3)
                target_type = rel_match.group(4).strip()

                # Extract mapped by
                mapped_by = ""
                mb_match = re.search(r'mappedBy\s*=\s*"(\w+)"', rel_attrs)
                if mb_match:
                    mapped_by = mb_match.group(1)

                # Clean up target type (extract from List<Type>, Set<Type>, etc.)
                type_match = re.search(r'(?:List|Set|MutableList|MutableSet|Collection)<\s*(\w+)', target_type)
                if type_match:
                    target_type = type_match.group(1)

                relationships.append({
                    'type': rel_type,
                    'target': target_type,
                    'mapped_by': mapped_by,
                    'field': field_name,
                })

            # Extract primary key
            primary_key = None
            id_match = self.ID_PATTERN.search(body)
            if id_match:
                primary_key = id_match.group(1)

            # Detect annotations
            annotations = []
            ann_before = content[max(0, match.start() - 500):match.end()]
            for ann_match in re.finditer(r'@(\w+)', ann_before):
                ann_name = ann_match.group(1)
                if ann_name not in annotations:
                    annotations.append(ann_name)

            is_data = 'data class' in content[match.start():match.end() + 20]

            result['entities'].append(KotlinEntityInfo(
                name=class_name,
                table_name=table_name,
                orm='jpa',
                columns=columns,
                relationships=relationships,
                annotations=annotations,
                primary_key=primary_key,
                is_data_class=is_data,
                file=file_path,
                line_number=line,
            ))

    def _extract_repositories(self, content: str, file_path: str,
                               result: Dict[str, Any]):
        """Extract repository interface definitions."""
        for match in self.REPOSITORY_PATTERN.finditer(content):
            name = match.group(1)
            repo_type = match.group(2)
            entity_type = match.group(3)
            id_type = match.group(4)
            line = content[:match.start()].count('\n') + 1

            # Determine framework
            framework = 'spring-data'
            if 'Panache' in repo_type:
                framework = 'quarkus-panache'
            elif 'Coroutine' in repo_type:
                framework = 'spring-data-coroutines'

            # Extract custom methods
            brace_pos = content.find('{', match.end())
            body = ""
            if brace_pos >= 0:
                body = self._extract_body(content, brace_pos)

            custom_methods = []
            if body:
                for method_match in re.finditer(r'(?:suspend\s+)?fun\s+(\w+)', body):
                    custom_methods.append(method_match.group(1))

            # Extract annotations
            annotations = []
            ann_before = content[max(0, match.start() - 200):match.start()]
            for ann_match in re.finditer(r'@(\w+)', ann_before):
                annotations.append(ann_match.group(1))

            result['repositories'].append(KotlinRepositoryInfo(
                name=name,
                entity_type=entity_type,
                id_type=id_type,
                extends=repo_type,
                custom_methods=custom_methods,
                annotations=annotations,
                framework=framework,
                file=file_path,
                line_number=line,
            ))

    def _extract_exposed_tables(self, content: str, file_path: str,
                                 result: Dict[str, Any]):
        """Extract Exposed table object definitions."""
        for match in self.EXPOSED_TABLE_PATTERN.finditer(content):
            name = match.group(1)
            table_type = match.group(2)
            table_name = match.group(3) or name.lower()
            line = content[:match.start()].count('\n') + 1

            # Extract body
            brace_pos = content.find('{', match.end())
            body = self._extract_body(content, brace_pos) if brace_pos >= 0 else ""

            # Extract columns
            columns = []
            for col_match in self.EXPOSED_COLUMN_PATTERN.finditer(body):
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                columns.append({'name': col_name, 'type': col_type})

            # Extract references
            references = []
            for ref_match in self.EXPOSED_REFERENCE_PATTERN.finditer(body):
                references.append(ref_match.group(1))

            is_id_table = table_type in ('IntIdTable', 'LongIdTable', 'UUIDTable')

            result['exposed_tables'].append(KotlinExposedTableInfo(
                name=name,
                table_name=table_name,
                columns=columns,
                references=references,
                is_id_table=is_id_table,
                file=file_path,
                line_number=line,
            ))

    def _extract_serializables(self, content: str, file_path: str,
                                result: Dict[str, Any]):
        """Extract kotlinx.serialization model classes."""
        for match in self.SERIALIZABLE_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Check for @SerialName
            serial_name = ""
            sn_match = self.SERIAL_NAME_PATTERN.search(content[max(0, match.start() - 100):match.end()])
            if sn_match:
                serial_name = sn_match.group(1)

            # Extract properties
            brace_pos = content.find('{', match.end())
            # Also check constructor
            paren_pos = content.find('(', match.end())
            props_str = ""
            if paren_pos >= 0 and (brace_pos < 0 or paren_pos < brace_pos):
                close = self._find_matching_paren(content, paren_pos)
                props_str = content[paren_pos + 1:close]

            properties = []
            for prop_match in re.finditer(r'(?:val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', props_str):
                properties.append({
                    'name': prop_match.group(1),
                    'type': prop_match.group(2).strip(),
                })

            is_sealed = 'sealed' in content[max(0, match.start() - 30):match.start()]

            result['serializables'].append(KotlinSerializableInfo(
                name=name,
                serial_name=serial_name,
                properties=properties,
                is_sealed=is_sealed,
                file=file_path,
                line_number=line,
            ))

    def _extract_panache_entities(self, content: str, file_path: str,
                                   result: Dict[str, Any]):
        """Extract Quarkus Panache entity definitions."""
        for match in self.PANACHE_ENTITY_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            brace_pos = content.find('{', match.end())
            body = self._extract_body(content, brace_pos) if brace_pos >= 0 else ""

            # Extract columns from companion object find methods
            columns = []
            for prop_match in re.finditer(r'(?:var|val)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', body):
                columns.append({
                    'name': prop_match.group(1),
                    'type': prop_match.group(2).strip(),
                    'nullable': '?' in prop_match.group(2),
                    'unique': False,
                })

            result['entities'].append(KotlinEntityInfo(
                name=name,
                orm='panache',
                columns=columns,
                file=file_path,
                line_number=line,
            ))

    def _extract_room_entities(self, content: str, file_path: str,
                                result: Dict[str, Any]):
        """Extract Android Room entity definitions."""
        for match in self.ROOM_ENTITY_PATTERN.finditer(content):
            table_name = match.group(1)
            name = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Extract constructor properties
            paren_pos = content.find('(', match.end())
            columns = []
            if paren_pos >= 0:
                close = self._find_matching_paren(content, paren_pos)
                params = content[paren_pos + 1:close]
                for prop_match in re.finditer(r'(?:val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', params):
                    columns.append({
                        'name': prop_match.group(1),
                        'type': prop_match.group(2).strip(),
                        'nullable': '?' in prop_match.group(2),
                        'unique': False,
                    })

            result['entities'].append(KotlinEntityInfo(
                name=name,
                table_name=table_name,
                orm='room',
                columns=columns,
                is_data_class=True,
                file=file_path,
                line_number=line,
            ))

    def _extract_dtos(self, content: str, file_path: str,
                       result: Dict[str, Any]):
        """Extract DTO classes based on naming convention."""
        for match in self.DTO_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Skip if already matched as entity or serializable
            existing_names = {e.name for e in result['entities']}
            existing_names.update(s.name for s in result['serializables'])
            if name in existing_names:
                continue

            # Extract properties
            paren_pos = content.find('(', match.end())
            properties = []
            if paren_pos >= 0:
                close = self._find_matching_paren(content, paren_pos)
                params = content[paren_pos + 1:close]
                for prop_match in re.finditer(r'(?:val|var)\s+(\w+)\s*:\s*([\w<>,.\s?*]+)', params):
                    properties.append({
                        'name': prop_match.group(1),
                        'type': prop_match.group(2).strip(),
                    })

            result['dtos'].append(KotlinDTOInfo(
                name=name,
                properties=properties,
                file=file_path,
                line_number=line,
            ))

    def _extract_body(self, content: str, brace_pos: int) -> str:
        """Extract body from opening brace to matching closing brace."""
        if brace_pos < 0 or brace_pos >= len(content) or content[brace_pos] != '{':
            return ""
        depth = 0
        i = brace_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[brace_pos + 1:i]
            elif content[i] == '"':
                i += 1
                while i < len(content) and content[i] != '"':
                    if content[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        return content[brace_pos + 1:]

    def _find_matching_paren(self, content: str, pos: int) -> int:
        """Find matching closing parenthesis."""
        depth = 0
        i = pos
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(content)
