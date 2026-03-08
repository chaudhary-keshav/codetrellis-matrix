"""
Micronaut Data Extractor v1.0 - Repositories, entities, query methods.
Part of CodeTrellis v4.94 - Micronaut Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class MicronautRepositoryInfo:
    """A Micronaut Data repository."""
    name: str
    entity_class: str = ""
    repo_type: str = ""  # crud, jpa, pageable, reactive, async
    custom_methods: List[str] = field(default_factory=list)
    query_methods: List[str] = field(default_factory=list)
    is_reactive: bool = False
    is_async: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautEntityInfo:
    """A Micronaut-mapped entity."""
    name: str
    table_name: str = ""
    id_type: str = ""
    fields: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class MicronautDataExtractor:
    """Extracts Micronaut Data patterns."""

    REPO_PATTERNS = {
        'crud': re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
            r'(?:public\s+)?interface\s+(\w+)\s+extends\s+CrudRepository<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
        'jpa': re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
            r'(?:public\s+)?interface\s+(\w+)\s+extends\s+JpaRepository<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
        'pageable': re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
            r'(?:public\s+)?interface\s+(\w+)\s+extends\s+PageableRepository<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
        'reactive': re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
            r'(?:public\s+)?interface\s+(\w+)\s+extends\s+ReactiveStreamsCrudRepository<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
        'async': re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
            r'(?:public\s+)?interface\s+(\w+)\s+extends\s+AsyncCrudRepository<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
    }

    ENTITY_PATTERN = re.compile(
        r'@(?:MappedEntity|Entity)\s*(?:\(\s*"?([^")\s]*)"?\s*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ID_PATTERN = re.compile(
        r'@(?:Id|GeneratedValue)\s*\n\s*(?:private|protected|public)\s+([\w<>]+)\s+(\w+)',
        re.MULTILINE
    )

    FIELD_PATTERN = re.compile(
        r'(?:@\w+(?:\([^)]*\))?\s*\n\s*)*'
        r'(?:private|protected)\s+([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    QUERY_PATTERN = re.compile(
        r'@Query\(\s*(?:value\s*=\s*)?"([^"]+)"',
        re.MULTILINE
    )

    DERIVED_QUERY_PATTERN = re.compile(
        r'(?:List|Page|Slice|Optional|Publisher|Mono|Flux|CompletableFuture)?<?[\w<>,?\[\]]*>?\s+'
        r'(find|list|count|delete|update|exists|search)(By\w+)\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'repositories': [], 'entities': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract repositories
        for repo_type, pattern in self.REPO_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                entity_class = match.group(2)
                is_reactive = repo_type == 'reactive'
                is_async = repo_type == 'async'

                query_methods = [m.group(1) for m in self.QUERY_PATTERN.finditer(content)]
                derived_methods = [f"{m.group(1)}{m.group(2)}" for m in self.DERIVED_QUERY_PATTERN.finditer(content)]

                result['repositories'].append(MicronautRepositoryInfo(
                    name=name, entity_class=entity_class,
                    repo_type=repo_type,
                    custom_methods=derived_methods,
                    query_methods=query_methods,
                    is_reactive=is_reactive, is_async=is_async,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract entities
        for match in self.ENTITY_PATTERN.finditer(content):
            table_name = match.group(1) or ""
            entity_name = match.group(2)

            # Find ID field
            id_match = self.ID_PATTERN.search(content)
            id_type = id_match.group(1) if id_match else ""

            # Find fields
            fields = [m.group(2) for m in self.FIELD_PATTERN.finditer(content)]

            # Annotations
            pre_class = content[:match.start()]
            last_empty = pre_class.rfind('\n\n')
            annotation_block = pre_class[last_empty:] if last_empty > 0 else ""
            annotations = re.findall(r'@(\w+)', annotation_block)

            result['entities'].append(MicronautEntityInfo(
                name=entity_name, table_name=table_name,
                id_type=id_type, fields=fields,
                annotations=annotations,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
