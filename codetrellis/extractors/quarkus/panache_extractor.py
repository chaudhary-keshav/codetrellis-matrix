"""
Quarkus Panache Extractor v1.0 - Panache entities, repositories, active record.
Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class QuarkusPanacheEntityInfo:
    """A Panache entity (active record pattern)."""
    name: str
    entity_type: str = ""  # panache_entity, panache_entity_base, panache_mongo_entity, reactive_panache_entity
    id_type: str = "Long"
    custom_finders: List[str] = field(default_factory=list)
    named_queries: List[str] = field(default_factory=list)
    is_reactive: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusPanacheRepoInfo:
    """A Panache repository."""
    name: str
    entity_class: str = ""
    repo_type: str = ""  # panache_repository, panache_repository_base, reactive_panache_repository
    custom_methods: List[str] = field(default_factory=list)
    is_reactive: bool = False
    file: str = ""
    line_number: int = 0


class QuarkusPanacheExtractor:
    """Extracts Quarkus Panache patterns."""

    ENTITY_PATTERNS = {
        'panache_entity': re.compile(
            r'(?:@Entity\s*\n)?(?:public\s+)?class\s+(\w+)\s+extends\s+PanacheEntity\b',
            re.MULTILINE
        ),
        'panache_entity_base': re.compile(
            r'(?:@Entity\s*\n)?(?:public\s+)?class\s+(\w+)\s+extends\s+PanacheEntityBase<([\w<>,?]+)>',
            re.MULTILINE
        ),
        'panache_mongo_entity': re.compile(
            r'(?:public\s+)?class\s+(\w+)\s+extends\s+(?:Reactive)?PanacheMongoEntity(?:Base)?',
            re.MULTILINE
        ),
        'reactive_panache_entity': re.compile(
            r'(?:@Entity\s*\n)?(?:public\s+)?class\s+(\w+)\s+extends\s+ReactivePanacheEntity(?:Base)?',
            re.MULTILINE
        ),
    }

    REPO_PATTERNS = {
        'panache_repository': re.compile(
            r'(?:@ApplicationScoped\s*\n)?(?:public\s+)?class\s+(\w+)\s+implements\s+PanacheRepository<(\w+)>',
            re.MULTILINE
        ),
        'panache_repository_base': re.compile(
            r'(?:@ApplicationScoped\s*\n)?(?:public\s+)?class\s+(\w+)\s+implements\s+PanacheRepositoryBase<(\w+)\s*,\s*([\w<>]+)>',
            re.MULTILINE
        ),
        'reactive_panache_repository': re.compile(
            r'(?:@ApplicationScoped\s*\n)?(?:public\s+)?class\s+(\w+)\s+implements\s+ReactivePanacheRepository<(\w+)>',
            re.MULTILINE
        ),
    }

    CUSTOM_FINDER_PATTERN = re.compile(
        r'(?:public\s+static\s+)?([\w<>,?\[\]]+)\s+(find\w+|list\w+|count\w+|delete\w+|update\w+)\s*\(',
        re.MULTILINE
    )

    NAMED_QUERY_PATTERN = re.compile(
        r'@NamedQuery\(\s*name\s*=\s*"([^"]+)"',
        re.MULTILINE
    )

    PUBLIC_METHOD_PATTERN = re.compile(
        r'public\s+([\w<>,?\[\]]+)\s+(\w+)\s*\([^)]*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'entities': [], 'repositories': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract entities
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                id_type = "Long"
                if entity_type == 'panache_entity_base' and match.lastindex and match.lastindex >= 2:
                    id_type = match.group(2)

                is_reactive = 'reactive' in entity_type.lower() or 'Reactive' in match.group(0)
                finders = [m.group(2) for m in self.CUSTOM_FINDER_PATTERN.finditer(content)]
                named_queries = [m.group(1) for m in self.NAMED_QUERY_PATTERN.finditer(content)]

                annotations = []
                pre_class = content[:match.start()]
                last_newlines = pre_class.rfind('\n\n')
                if last_newlines > 0:
                    annotation_block = pre_class[last_newlines:]
                    annotations = re.findall(r'@(\w+)', annotation_block)

                result['entities'].append(QuarkusPanacheEntityInfo(
                    name=name, entity_type=entity_type, id_type=id_type,
                    custom_finders=finders, named_queries=named_queries,
                    is_reactive=is_reactive, annotations=annotations,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract repositories
        for repo_type, pattern in self.REPO_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                entity_class = match.group(2)
                is_reactive = 'reactive' in repo_type.lower()

                custom_methods = [m.group(2) for m in self.PUBLIC_METHOD_PATTERN.finditer(content)
                                  if m.group(2) not in ('toString', 'hashCode', 'equals')]

                result['repositories'].append(QuarkusPanacheRepoInfo(
                    name=name, entity_class=entity_class,
                    repo_type=repo_type, custom_methods=custom_methods,
                    is_reactive=is_reactive,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        return result
