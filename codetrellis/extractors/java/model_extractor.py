"""
JavaModelExtractor - Extracts JPA/Hibernate entities, Spring Data repositories.

Extracts:
- JPA @Entity classes with @Table, @Column, @Id
- Relationships: @OneToMany, @ManyToOne, @ManyToMany, @OneToOne
- Spring Data repositories (JpaRepository, CrudRepository, etc.)
- Named queries and JPQL
- MyBatis @Mapper interfaces

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaColumnInfo:
    """Information about a JPA column/field."""
    name: str
    type: str
    column_name: Optional[str] = None
    is_id: bool = False
    is_nullable: bool = True
    is_unique: bool = False
    length: Optional[int] = None
    annotations: List[str] = field(default_factory=list)


@dataclass
class JavaRelationshipInfo:
    """Information about a JPA relationship."""
    type: str  # OneToMany, ManyToOne, ManyToMany, OneToOne
    target_entity: str
    field_name: str
    mapped_by: Optional[str] = None
    cascade: List[str] = field(default_factory=list)
    fetch: Optional[str] = None  # LAZY, EAGER
    join_column: Optional[str] = None


@dataclass
class JavaEntityInfo:
    """Information about a JPA entity."""
    name: str
    table_name: Optional[str] = None
    columns: List[JavaColumnInfo] = field(default_factory=list)
    relationships: List[JavaRelationshipInfo] = field(default_factory=list)
    id_column: Optional[str] = None
    id_strategy: Optional[str] = None  # AUTO, SEQUENCE, IDENTITY, TABLE
    extends: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    named_queries: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_embeddable: bool = False
    is_mapped_superclass: bool = False


@dataclass
class JavaRepositoryInfo:
    """Information about a Spring Data repository."""
    name: str
    entity_type: str
    id_type: str
    base_interface: str  # JpaRepository, CrudRepository, etc.
    custom_methods: List[Dict[str, str]] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class JavaModelExtractor:
    """
    Extracts JPA entities and Spring Data repositories from Java source code.

    Handles:
    - @Entity with @Table
    - @Column with constraints
    - @Id with @GeneratedValue strategy
    - Relationships (@OneToMany, @ManyToOne, etc.)
    - @Embeddable, @MappedSuperclass
    - Spring Data repositories with custom query methods
    - @Query annotations
    - MyBatis @Mapper
    """

    # Entity detection
    ENTITY_PATTERN = re.compile(
        r'@Entity\s*(?:\([^)]*\))?\s*'
        r'(?:@Table\s*\(\s*(?:name\s*=\s*)?["\']([^"\']*)["\'][^)]*\)\s*)?',
        re.MULTILINE
    )

    # Panache entity detection (Quarkus)
    PANACHE_ENTITY_PATTERN = re.compile(
        r'class\s+(\w+)\s+extends\s+'
        r'(PanacheEntity|PanacheEntityBase|PanacheMongoEntity|PanacheMongoEntityBase)'
        r'(?:\s*<[^>]+>)?',
        re.MULTILINE
    )

    # Panache repository detection (Quarkus)
    PANACHE_REPO_PATTERN = re.compile(
        r'(?:@(?:ApplicationScoped|Singleton|Dependent|RequestScoped)\s+)?'
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+'
        r'(PanacheRepository|PanacheRepositoryBase|PanacheMongoRepository|PanacheMongoRepositoryBase)'
        r'\s*<\s*(\w+)(?:\s*,\s*([\w<>]+))?\s*>',
        re.MULTILINE
    )

    # Column patterns
    COLUMN_PATTERN = re.compile(
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:private|protected|public)\s+'
        r'([\w<>\[\].,?\s]+?)\s+(\w+)\s*[;=]',
        re.MULTILINE
    )

    # Relationship patterns
    RELATIONSHIP_PATTERN = re.compile(
        r'@(OneToMany|ManyToOne|ManyToMany|OneToOne)'
        r'\s*(?:\(([^)]*)\))?\s*'
        r'(?:@JoinColumn\s*\(\s*(?:name\s*=\s*)?["\']([^"\']*)["\'][^)]*\)\s*)?'
        r'(?:@JoinTable[^)]*\)\s*)?'
        r'(?:private|protected|public)\s+'
        r'([\w<>\[\].,?\s]+?)\s+(\w+)',
        re.MULTILINE | re.DOTALL
    )

    # Repository detection
    REPOSITORY_PATTERN = re.compile(
        r'(?:@Repository\s*\n\s*)?'
        r'(?:public\s+)?interface\s+(\w+)\s+'
        r'extends\s+((?:Jpa|Crud|PagingAndSorting|Reactive(?:Crud|Sorting))?Repository'
        r'|MongoRepository|ElasticsearchRepository'
        r'|R2dbcRepository)\s*<\s*(\w+)\s*,\s*([\w<>]+)\s*>',
        re.MULTILINE
    )

    # Custom query method detection
    QUERY_METHOD_PATTERN = re.compile(
        r'(?:@Query\s*\(\s*["\']([^"\']+)["\'][^)]*\)\s*)?'
        r'(?:[\w<>\[\].,?\s]+?)\s+(\w+)\s*\([^)]*\)\s*;',
        re.MULTILINE
    )

    # MyBatis mapper
    MAPPER_PATTERN = re.compile(
        r'@Mapper\s*\n\s*'
        r'(?:public\s+)?interface\s+(\w+)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract JPA entities and repositories from Java source code.

        Returns dict with keys: entities, repositories
        """
        result = {
            'entities': [],
            'repositories': [],
        }

        # Check for @Entity
        entity_match = self.ENTITY_PATTERN.search(content)
        if entity_match or '@Embeddable' in content or '@MappedSuperclass' in content:
            table_name = entity_match.group(1) if entity_match else None

            # Get class name
            class_match = re.search(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', content)
            if class_match:
                class_name = class_match.group(1)
                extends = class_match.group(2)

                # Extract columns
                columns = []
                id_column = None
                id_strategy = None
                relationships = []
                annotations_set = set()

                # Get class-level annotations
                for ann in re.findall(r'@(\w+)', content[:content.find('class ')]):
                    annotations_set.add(ann)

                # Extract relationships first (to exclude from regular columns)
                rel_fields = set()
                for rel_match in self.RELATIONSHIP_PATTERN.finditer(content):
                    rel_type = rel_match.group(1)
                    rel_attrs = rel_match.group(2) or ""
                    join_col = rel_match.group(3)
                    target_type = rel_match.group(4).strip()
                    rel_field = rel_match.group(5)
                    rel_fields.add(rel_field)

                    # Parse attributes
                    mapped_by = None
                    cascade = []
                    fetch = None

                    mb_match = re.search(r'mappedBy\s*=\s*["\'](\w+)["\']', rel_attrs)
                    if mb_match:
                        mapped_by = mb_match.group(1)
                    cascade_match = re.search(r'cascade\s*=\s*(?:\{([^}]+)\}|CascadeType\.(\w+))', rel_attrs)
                    if cascade_match:
                        cascade_str = cascade_match.group(1) or cascade_match.group(2)
                        cascade = re.findall(r'CascadeType\.(\w+)', cascade_str) or [cascade_str]
                    fetch_match = re.search(r'fetch\s*=\s*FetchType\.(\w+)', rel_attrs)
                    if fetch_match:
                        fetch = fetch_match.group(1)

                    # Determine target entity
                    target_entity = target_type
                    if '<' in target_type:
                        generic_match = re.search(r'<\s*(\w+)\s*>', target_type)
                        if generic_match:
                            target_entity = generic_match.group(1)

                    relationships.append(JavaRelationshipInfo(
                        type=rel_type,
                        target_entity=target_entity,
                        field_name=rel_field,
                        mapped_by=mapped_by,
                        cascade=cascade,
                        fetch=fetch,
                        join_column=join_col,
                    ))

                # Extract columns
                for col_match in self.COLUMN_PATTERN.finditer(content):
                    ann_block = col_match.group(1) or ""
                    col_type = col_match.group(2).strip()
                    col_name = col_match.group(3)

                    # Skip relationship fields
                    if col_name in rel_fields:
                        continue
                    # Skip static/constant fields
                    if 'static' in ann_block or 'final' in ann_block:
                        continue

                    col_annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', ann_block)

                    is_id = any(a.startswith('Id') for a in col_annotations)
                    is_nullable = True
                    is_unique = False
                    length = None
                    column_name = None

                    for ann in col_annotations:
                        if ann.startswith('Column'):
                            col_attr_match = re.search(r'name\s*=\s*["\']([^"\']*)["\']', ann)
                            if col_attr_match:
                                column_name = col_attr_match.group(1)
                            if 'nullable = false' in ann or 'nullable=false' in ann:
                                is_nullable = False
                            if 'unique = true' in ann or 'unique=true' in ann:
                                is_unique = True
                            length_match = re.search(r'length\s*=\s*(\d+)', ann)
                            if length_match:
                                length = int(length_match.group(1))

                    if is_id:
                        id_column = col_name
                        for ann in col_annotations:
                            if 'GeneratedValue' in ann:
                                strategy_match = re.search(r'GenerationType\.(\w+)', ann)
                                if strategy_match:
                                    id_strategy = strategy_match.group(1)

                    columns.append(JavaColumnInfo(
                        name=col_name,
                        type=col_type,
                        column_name=column_name,
                        is_id=is_id,
                        is_nullable=is_nullable,
                        is_unique=is_unique,
                        length=length,
                        annotations=[a.split('(')[0] for a in col_annotations],
                    ))

                line_number = content[:entity_match.start()].count('\n') + 1 if entity_match else 1

                result['entities'].append(JavaEntityInfo(
                    name=class_name,
                    table_name=table_name,
                    columns=columns,
                    relationships=relationships,
                    id_column=id_column,
                    id_strategy=id_strategy,
                    extends=extends,
                    annotations=list(annotations_set),
                    file=file_path,
                    line_number=line_number,
                    is_embeddable='Embeddable' in annotations_set,
                    is_mapped_superclass='MappedSuperclass' in annotations_set,
                ))

        # Extract repositories
        for repo_match in self.REPOSITORY_PATTERN.finditer(content):
            repo_name = repo_match.group(1)
            base_interface = repo_match.group(2)
            entity_type = repo_match.group(3)
            id_type = repo_match.group(4)

            # Extract custom methods
            custom_methods = []
            brace_start = content.find('{', repo_match.end())
            if brace_start >= 0:
                # Simple extraction of method signatures in the interface
                body_end = content.find('}', brace_start)
                if body_end >= 0:
                    body = content[brace_start + 1:body_end]
                    for m in self.QUERY_METHOD_PATTERN.finditer(body):
                        query = m.group(1)
                        method_name = m.group(2)
                        method_info = {'name': method_name}
                        if query:
                            method_info['query'] = query[:100]
                        custom_methods.append(method_info)

            annotations = re.findall(r'@(\w+)', content[:repo_match.start()])
            line_number = content[:repo_match.start()].count('\n') + 1

            result['repositories'].append(JavaRepositoryInfo(
                name=repo_name,
                entity_type=entity_type,
                id_type=id_type,
                base_interface=base_interface,
                custom_methods=custom_methods,
                annotations=annotations[-5:] if annotations else [],  # Last 5 annotations
                file=file_path,
                line_number=line_number,
            ))

        # --- Quarkus Panache Entity Detection ---
        # Panache entities use `extends PanacheEntity` instead of @Entity annotation
        if not result['entities']:  # Don't duplicate if already found via @Entity
            for panache_match in self.PANACHE_ENTITY_PATTERN.finditer(content):
                class_name = panache_match.group(1)
                panache_base = panache_match.group(2)

                # Check for @Table annotation
                table_match = re.search(r'@Table\s*\(\s*(?:name\s*=\s*)?["\']([^"\']*)["\']', content)
                table_name = table_match.group(1) if table_match else None

                # Extract columns (Panache uses public fields)
                columns = []
                id_column = None
                id_strategy = None
                relationships = []

                # Panache public fields (no getter/setter needed)
                public_field_pattern = re.compile(
                    r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
                    r'public\s+'
                    r'([\w<>\[\].,?\s]+?)\s+(\w+)\s*[;=]',
                    re.MULTILINE
                )
                for field_match in public_field_pattern.finditer(content):
                    ann_block = field_match.group(1) or ""
                    field_type = field_match.group(2).strip()
                    field_name = field_match.group(3)

                    # Skip static/final fields and class declaration
                    if 'static' in ann_block or 'final' in ann_block:
                        continue
                    if field_name in ('serialVersionUID',):
                        continue

                    col_annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', ann_block)
                    is_id = any(a.startswith('Id') for a in col_annotations)

                    if is_id:
                        id_column = field_name

                    columns.append(JavaColumnInfo(
                        name=field_name,
                        type=field_type,
                        is_id=is_id,
                        annotations=[a.split('(')[0] for a in col_annotations],
                    ))

                # Extract relationships
                for rel_match in self.RELATIONSHIP_PATTERN.finditer(content):
                    rel_type = rel_match.group(1)
                    rel_attrs = rel_match.group(2) or ""
                    target_type = rel_match.group(4).strip()
                    rel_field = rel_match.group(5)

                    target_entity = target_type
                    if '<' in target_type:
                        generic_match = re.search(r'<\s*(\w+)\s*>', target_type)
                        if generic_match:
                            target_entity = generic_match.group(1)

                    mapped_by = None
                    mb_match = re.search(r'mappedBy\s*=\s*["\'](\w+)["\']', rel_attrs)
                    if mb_match:
                        mapped_by = mb_match.group(1)

                    fetch = None
                    fetch_match = re.search(r'fetch\s*=\s*FetchType\.(\w+)', rel_attrs)
                    if fetch_match:
                        fetch = fetch_match.group(1)

                    relationships.append(JavaRelationshipInfo(
                        type=rel_type,
                        target_entity=target_entity,
                        field_name=rel_field,
                        mapped_by=mapped_by,
                        fetch=fetch,
                    ))

                # Get class-level annotations
                class_pos = content.find(f'class {class_name}')
                annotations_set = set()
                if class_pos >= 0:
                    for ann in re.findall(r'@(\w+)', content[:class_pos]):
                        annotations_set.add(ann)

                line_number = content[:panache_match.start()].count('\n') + 1

                # Panache entities with PanacheEntity have auto-generated Long id
                is_mongo = 'Mongo' in panache_base
                if not id_column and 'Base' not in panache_base:
                    id_column = 'id'
                    id_strategy = 'AUTO'

                result['entities'].append(JavaEntityInfo(
                    name=class_name,
                    table_name=table_name,
                    columns=columns,
                    relationships=relationships,
                    id_column=id_column,
                    id_strategy=id_strategy,
                    extends=panache_base,
                    annotations=list(annotations_set) + ['PanacheEntity'],
                    file=file_path,
                    line_number=line_number,
                ))

        # --- Quarkus Panache Repository Detection ---
        for panache_repo_match in self.PANACHE_REPO_PATTERN.finditer(content):
            repo_name = panache_repo_match.group(1)
            panache_repo_type = panache_repo_match.group(2)
            entity_type = panache_repo_match.group(3)
            id_type = panache_repo_match.group(4) or 'Long'

            # Extract custom methods from class body
            custom_methods = []
            brace_start = content.find('{', panache_repo_match.end())
            if brace_start >= 0:
                body_end = content.find('}', brace_start)
                if body_end >= 0:
                    body = content[brace_start + 1:body_end]
                    # Find public methods
                    method_pattern = re.compile(
                        r'public\s+[\w<>\[\].,?\s]+?\s+(\w+)\s*\([^)]*\)',
                        re.MULTILINE
                    )
                    for m in method_pattern.finditer(body):
                        custom_methods.append({'name': m.group(1)})

            line_number = content[:panache_repo_match.start()].count('\n') + 1
            result['repositories'].append(JavaRepositoryInfo(
                name=repo_name,
                entity_type=entity_type,
                id_type=id_type,
                base_interface=panache_repo_type,
                custom_methods=custom_methods,
                annotations=['ApplicationScoped'],
                file=file_path,
                line_number=line_number,
            ))

        return result
