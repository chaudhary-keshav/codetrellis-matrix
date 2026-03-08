"""
Jakarta EE JPA Extractor v1.0 - Entities, relationships, named queries.
Part of CodeTrellis v4.94 - Jakarta EE Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class JakartaEntityInfo:
    """A JPA entity."""
    name: str
    table_name: str = ""
    id_type: str = ""
    id_strategy: str = ""  # auto, sequence, identity, table, uuid
    fields: List[str] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    inheritance_strategy: str = ""  # single_table, joined, table_per_class
    is_embeddable: bool = False
    is_mapped_superclass: bool = False
    annotations: List[str] = field(default_factory=list)
    namespace: str = ""  # jakarta or javax
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaNamedQueryInfo:
    """A named JPQL or SQL query."""
    name: str
    query: str = ""
    query_type: str = ""  # jpql, native
    entity: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaRelationshipInfo:
    """A JPA relationship."""
    field_name: str
    relationship_type: str = ""  # one_to_one, one_to_many, many_to_one, many_to_many
    target_entity: str = ""
    fetch_type: str = ""  # lazy, eager
    cascade_types: List[str] = field(default_factory=list)
    mapped_by: str = ""
    file: str = ""
    line_number: int = 0


class JakartaJPAExtractor:
    """Extracts Jakarta Persistence (JPA) patterns."""

    ENTITY_PATTERN = re.compile(
        r'@Entity\s*(?:\(\s*name\s*=\s*"([^"]*)")?\s*\)?\s*\n'
        r'(?:@Table\(\s*name\s*=\s*"([^"]*)"[^)]*\)\s*\n)?'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    EMBEDDABLE_PATTERN = re.compile(
        r'@Embeddable\s*\n(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    MAPPED_SUPERCLASS_PATTERN = re.compile(
        r'@MappedSuperclass\s*\n(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ID_PATTERN = re.compile(
        r'@Id\s*\n(?:@GeneratedValue\(\s*strategy\s*=\s*GenerationType\.(\w+)\s*\)\s*\n)?'
        r'\s*(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'\s*(?:private|protected)\s+([\w<>]+)\s+(\w+)',
        re.MULTILINE
    )

    RELATIONSHIP_PATTERN = re.compile(
        r'@(OneToOne|OneToMany|ManyToOne|ManyToMany)'
        r'(?:\(\s*'
        r'(?:[^)]*(?:targetEntity\s*=\s*(\w+)\.class)?'
        r'(?:[^)]*fetch\s*=\s*FetchType\.(\w+))?'
        r'(?:[^)]*cascade\s*=\s*\{?([^})]+)\}?)?'
        r'(?:[^)]*mappedBy\s*=\s*"([^"]*)")?[^)]*)\))?'
        r'[\s\S]*?'
        r'(?:private|protected|public)\s+(?:[\w<>,?]+)\s+(\w+)',
        re.MULTILINE
    )

    NAMED_QUERY_PATTERN = re.compile(
        r'@NamedQuery\(\s*name\s*=\s*"([^"]+)"\s*,\s*query\s*=\s*"([^"]+)"',
        re.MULTILINE
    )

    NAMED_NATIVE_QUERY_PATTERN = re.compile(
        r'@NamedNativeQuery\(\s*name\s*=\s*"([^"]+)"\s*,\s*query\s*=\s*"([^"]+)"',
        re.MULTILINE
    )

    INHERITANCE_PATTERN = re.compile(
        r'@Inheritance\(\s*strategy\s*=\s*InheritanceType\.(\w+)\s*\)',
        re.MULTILINE
    )

    COLUMN_PATTERN = re.compile(
        r'(?:@Column\([^)]*\)\s*\n\s*)?'
        r'(?:private|protected)\s+([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(r'import\s+(jakarta|javax)\.persistence\.')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'entities': [], 'named_queries': [], 'relationships': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        ns_match = self.NAMESPACE_PATTERN.search(content)
        namespace = ns_match.group(1) if ns_match else ""

        # Extract entities
        for match in self.ENTITY_PATTERN.finditer(content):
            entity_name_attr = match.group(1) or ""
            table_name = match.group(2) or ""
            class_name = match.group(3)

            # Find ID
            id_match = self.ID_PATTERN.search(content)
            id_strategy = id_match.group(1).lower() if id_match and id_match.group(1) else ""
            id_type = id_match.group(2) if id_match else ""

            # Inheritance
            inh_match = self.INHERITANCE_PATTERN.search(content)
            inheritance = inh_match.group(1).lower() if inh_match else ""

            # Fields
            fields = [m.group(2) for m in self.COLUMN_PATTERN.finditer(content)]

            # Relationships
            relationships = []
            for rm in self.RELATIONSHIP_PATTERN.finditer(content):
                rel_type = rm.group(1)
                rel_type_normalized = rel_type.lower().replace('to', '_to_')
                if rel_type_normalized.startswith('_'):
                    rel_type_normalized = rel_type_normalized[1:]
                target = rm.group(2) or ""
                fetch = (rm.group(3) or "").lower()
                cascade_raw = rm.group(4) or ""
                cascades = [c.strip().replace('CascadeType.', '') for c in cascade_raw.split(',') if c.strip()]
                mapped_by = rm.group(5) or ""
                field_name = rm.group(6)

                rel_info = JakartaRelationshipInfo(
                    field_name=field_name,
                    relationship_type=rel_type_normalized,
                    target_entity=target, fetch_type=fetch,
                    cascade_types=cascades, mapped_by=mapped_by,
                    file=file_path, line_number=content[:rm.start()].count('\n') + 1,
                )
                relationships.append(vars(rel_info))
                result['relationships'].append(vars(rel_info))

            # Annotations
            pre_class = content[:match.start()]
            last_empty = pre_class.rfind('\n\n')
            ann_block = pre_class[last_empty:] if last_empty > 0 else ""
            annotations = re.findall(r'@(\w+)', ann_block)

            result['entities'].append(JakartaEntityInfo(
                name=class_name, table_name=table_name,
                id_type=id_type, id_strategy=id_strategy,
                fields=fields, relationships=relationships,
                inheritance_strategy=inheritance,
                annotations=annotations, namespace=namespace,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Embeddables
        for match in self.EMBEDDABLE_PATTERN.finditer(content):
            result['entities'].append(JakartaEntityInfo(
                name=match.group(1), is_embeddable=True,
                namespace=namespace,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # MappedSuperclass
        for match in self.MAPPED_SUPERCLASS_PATTERN.finditer(content):
            result['entities'].append(JakartaEntityInfo(
                name=match.group(1), is_mapped_superclass=True,
                namespace=namespace,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Named queries
        for match in self.NAMED_QUERY_PATTERN.finditer(content):
            result['named_queries'].append(JakartaNamedQueryInfo(
                name=match.group(1), query=match.group(2),
                query_type='jpql',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.NAMED_NATIVE_QUERY_PATTERN.finditer(content):
            result['named_queries'].append(JakartaNamedQueryInfo(
                name=match.group(1), query=match.group(2),
                query_type='native',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
