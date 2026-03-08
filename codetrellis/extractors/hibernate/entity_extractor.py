"""
Hibernate Entity Extractor - Extracts JPA/Hibernate entity mappings.

Extracts:
- @Entity classes with @Table annotations
- Column mappings (@Column, @Id, @GeneratedValue)
- Relationships (@OneToMany, @ManyToOne, @ManyToMany, @OneToOne)
- Embeddable types (@Embeddable, @Embedded)
- Inheritance strategies (@Inheritance, @DiscriminatorColumn)
- Converters (@Converter, @Convert)
- Enums (@Enumerated)
- LOB fields (@Lob, @Basic)
- Temporal annotations (@Temporal)
- Natural IDs (@NaturalId)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HibernateRelationshipInfo:
    """Information about an entity relationship."""
    field_name: str = ""
    relationship_type: str = ""  # OneToMany, ManyToOne, ManyToMany, OneToOne
    target_entity: str = ""
    mapped_by: str = ""
    fetch_type: str = ""  # LAZY, EAGER
    cascade: List[str] = field(default_factory=list)
    join_column: str = ""
    join_table: str = ""
    orphan_removal: bool = False
    optional: bool = True
    line_number: int = 0


@dataclass
class HibernateEmbeddableInfo:
    """Information about an embeddable type."""
    class_name: str = ""
    fields: List[str] = field(default_factory=list)
    attribute_overrides: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class HibernateEntityInfo:
    """Information about a Hibernate entity."""
    class_name: str = ""
    table_name: str = ""
    schema: str = ""
    catalog: str = ""
    id_field: str = ""
    id_type: str = ""
    id_strategy: str = ""  # AUTO, IDENTITY, SEQUENCE, TABLE, UUID
    columns: List[str] = field(default_factory=list)
    relationships: List[HibernateRelationshipInfo] = field(default_factory=list)
    embeddables: List[str] = field(default_factory=list)
    inheritance_strategy: str = ""  # SINGLE_TABLE, JOINED, TABLE_PER_CLASS
    discriminator_column: str = ""
    discriminator_value: str = ""
    is_mapped_superclass: bool = False
    is_audited: bool = False
    indexes: List[str] = field(default_factory=list)
    unique_constraints: List[str] = field(default_factory=list)
    natural_id_fields: List[str] = field(default_factory=list)
    converters: List[str] = field(default_factory=list)
    line_number: int = 0


class HibernateEntityExtractor:
    """Extracts Hibernate/JPA entity information from Java source code."""

    # Entity class detection
    ENTITY_PATTERN = re.compile(
        r'@Entity(?:\s*\(.*?\))?\s*(?:@Table\s*\(\s*'
        r'(?:name\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?schema\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?catalog\s*=\s*["\'](\w+)["\'])?'
        r'\s*\))?\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.DOTALL
    )

    MAPPED_SUPERCLASS_PATTERN = re.compile(
        r'@MappedSuperclass\s*(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.DOTALL
    )

    EMBEDDABLE_PATTERN = re.compile(
        r'@Embeddable\s*(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.DOTALL
    )

    # ID field patterns
    ID_PATTERN = re.compile(
        r'@Id\s*(?:@GeneratedValue\s*\(\s*'
        r'(?:strategy\s*=\s*GenerationType\.(\w+))?'
        r'(?:.*?generator\s*=\s*["\'](\w+)["\'])?'
        r'\s*\))?\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:private|protected)\s+(\w+(?:<[^>]+>)?)\s+(\w+)',
        re.DOTALL
    )

    # Column annotation
    COLUMN_PATTERN = re.compile(
        r'@Column\s*\(\s*(?:name\s*=\s*["\'](\w+)["\'])?.*?\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:private|protected)\s+\w+(?:<[^>]+>)?\s+(\w+)',
        re.DOTALL
    )

    BASIC_FIELD_PATTERN = re.compile(
        r'(?:private|protected)\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*[;=]',
        re.MULTILINE
    )

    # Relationship patterns
    RELATIONSHIP_PATTERN = re.compile(
        r'@(OneToMany|ManyToOne|ManyToMany|OneToOne)\s*'
        r'(?:\(\s*(.*?)\))?\s*'
        r'(?:@JoinColumn\s*\(\s*(?:name\s*=\s*["\'](\w+)["\'])?.*?\)\s*)?'
        r'(?:@JoinTable\s*\(\s*(?:name\s*=\s*["\'](\w+)["\'])?.*?\)\s*)?'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:private|protected)\s+(?:Set|List|Collection|Map)?(?:<(\w+)>)?\s*(\w+)',
        re.DOTALL
    )

    # Inheritance
    INHERITANCE_PATTERN = re.compile(
        r'@Inheritance\s*\(\s*strategy\s*=\s*InheritanceType\.(\w+)\s*\)',
        re.MULTILINE
    )

    DISCRIMINATOR_COLUMN_PATTERN = re.compile(
        r'@DiscriminatorColumn\s*\(\s*name\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    DISCRIMINATOR_VALUE_PATTERN = re.compile(
        r'@DiscriminatorValue\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Index / Unique constraints
    INDEX_PATTERN = re.compile(
        r'@Index\s*\(\s*(?:name\s*=\s*["\'](\w+)["\'])?\s*(?:,\s*columnList\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE
    )

    UNIQUE_CONSTRAINT_PATTERN = re.compile(
        r'@UniqueConstraint\s*\(\s*(?:name\s*=\s*["\'](\w+)["\'])?\s*(?:,\s*)?columnNames\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # Natural ID
    NATURAL_ID_PATTERN = re.compile(
        r'@NaturalId\s*(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:private|protected)\s+\w+(?:<[^>]+>)?\s+(\w+)',
        re.DOTALL
    )

    # Converter
    CONVERTER_PATTERN = re.compile(
        r'@Converter(?:\s*\(\s*autoApply\s*=\s*(true|false)\s*\))?\s*'
        r'(?:public\s+)?class\s+(\w+)',
        re.DOTALL
    )

    # Auditing (Envers)
    AUDITED_PATTERN = re.compile(r'@Audited', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract entity information from Hibernate/JPA source code."""
        entities: List[HibernateEntityInfo] = []
        embeddables: List[HibernateEmbeddableInfo] = []
        relationships: List[HibernateRelationshipInfo] = []

        if not content or not content.strip():
            return {
                'entities': entities,
                'embeddables': embeddables,
                'relationships': relationships,
            }

        lines = content.split('\n')

        # Extract entities
        for match in self.ENTITY_PATTERN.finditer(content):
            entity = HibernateEntityInfo(
                table_name=match.group(1) or "",
                schema=match.group(2) or "",
                catalog=match.group(3) or "",
                class_name=match.group(4) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Check if audited
            entity.is_audited = bool(self.AUDITED_PATTERN.search(content))

            # Get inheritance
            inh = self.INHERITANCE_PATTERN.search(content)
            if inh:
                entity.inheritance_strategy = inh.group(1)

            disc_col = self.DISCRIMINATOR_COLUMN_PATTERN.search(content)
            if disc_col:
                entity.discriminator_column = disc_col.group(1)

            disc_val = self.DISCRIMINATOR_VALUE_PATTERN.search(content)
            if disc_val:
                entity.discriminator_value = disc_val.group(1)

            # Get ID field
            id_match = self.ID_PATTERN.search(content)
            if id_match:
                entity.id_strategy = id_match.group(1) or "AUTO"
                entity.id_type = id_match.group(3) or ""
                entity.id_field = id_match.group(4) or ""

            # Get columns
            for col_match in self.COLUMN_PATTERN.finditer(content):
                col_name = col_match.group(2) or col_match.group(1)
                if col_name:
                    entity.columns.append(col_name)

            # Get natural IDs
            for nat_match in self.NATURAL_ID_PATTERN.finditer(content):
                entity.natural_id_fields.append(nat_match.group(1))

            # Get indexes
            for idx_match in self.INDEX_PATTERN.finditer(content):
                idx_name = idx_match.group(1) or idx_match.group(2) or ""
                if idx_name:
                    entity.indexes.append(idx_name)

            # Get unique constraints
            for uc_match in self.UNIQUE_CONSTRAINT_PATTERN.finditer(content):
                uc_name = uc_match.group(1) or uc_match.group(2) or ""
                if uc_name:
                    entity.unique_constraints.append(uc_name)

            entities.append(entity)

        # Extract mapped superclasses
        for match in self.MAPPED_SUPERCLASS_PATTERN.finditer(content):
            entity = HibernateEntityInfo(
                class_name=match.group(1),
                is_mapped_superclass=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            entities.append(entity)

        # Extract embeddables
        for match in self.EMBEDDABLE_PATTERN.finditer(content):
            emb = HibernateEmbeddableInfo(
                class_name=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            )
            embeddables.append(emb)

        # Extract relationships
        for match in self.RELATIONSHIP_PATTERN.finditer(content):
            rel = HibernateRelationshipInfo(
                relationship_type=match.group(1),
                join_column=match.group(3) or "",
                join_table=match.group(4) or "",
                target_entity=match.group(5) or "",
                field_name=match.group(6) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Parse relationship attributes
            attrs_str = match.group(2) or ""
            if 'mappedBy' in attrs_str:
                mb = re.search(r'mappedBy\s*=\s*["\'](\w+)["\']', attrs_str)
                if mb:
                    rel.mapped_by = mb.group(1)
            if 'fetch' in attrs_str:
                ft = re.search(r'fetch\s*=\s*FetchType\.(\w+)', attrs_str)
                if ft:
                    rel.fetch_type = ft.group(1)
            if 'cascade' in attrs_str:
                cas = re.findall(r'CascadeType\.(\w+)', attrs_str)
                rel.cascade = cas
            if 'orphanRemoval' in attrs_str:
                rel.orphan_removal = 'true' in attrs_str

            relationships.append(rel)

        return {
            'entities': entities,
            'embeddables': embeddables,
            'relationships': relationships,
        }
