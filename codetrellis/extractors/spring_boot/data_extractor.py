"""
Spring Boot Data Extractor v1.0

Extracts Spring Data, caching, and transaction management patterns.

Extracts:
- Spring Data repositories (JpaRepository, CrudRepository, ReactiveCrud, etc.)
- @Query custom queries (JPQL, native SQL)
- Query method derivation (findBy*, countBy*, deleteBy*)
- Projections and DTOs
- @Cacheable, @CacheEvict, @CachePut
- @Transactional with propagation and isolation levels
- Auditing (@CreatedDate, @LastModifiedDate, @CreatedBy)
- Specification/Criteria API usage

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootRepoInfo:
    """Spring Data repository interface."""
    name: str
    entity_type: str = ""
    id_type: str = ""
    repo_type: str = ""  # JpaRepository, CrudRepository, ReactiveCrud, etc.
    custom_queries: List[str] = field(default_factory=list)  # @Query methods
    derived_methods: List[str] = field(default_factory=list)  # findBy*, countBy*, etc.
    custom_methods: List[str] = field(default_factory=list)  # other methods
    has_specification: bool = False  # extends JpaSpecificationExecutor
    has_querydsl: bool = False  # extends QuerydslPredicateExecutor
    has_paging: bool = False  # extends PagingAndSortingRepository
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootQueryMethodInfo:
    """A @Query method in a repository."""
    method_name: str
    query: str = ""
    is_native: bool = False
    return_type: str = ""
    parameters: List[str] = field(default_factory=list)
    is_modifying: bool = False  # @Modifying
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootCacheInfo:
    """Cache annotation usage."""
    annotation: str = ""  # Cacheable, CacheEvict, CachePut, Caching
    cache_names: List[str] = field(default_factory=list)
    key: str = ""  # SpEL key expression
    condition: str = ""
    target_method: str = ""
    target_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootTransactionInfo:
    """@Transactional annotation usage."""
    target_method: str = ""
    target_class: str = ""
    propagation: str = ""  # REQUIRED, REQUIRES_NEW, etc.
    isolation: str = ""  # DEFAULT, READ_COMMITTED, etc.
    read_only: bool = False
    timeout: int = -1
    rollback_for: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class SpringBootDataExtractor:
    """Extracts Spring Data, cache, and transaction patterns."""

    # Repository interface declaration
    REPO_PATTERN = re.compile(
        r'(?:public\s+)?interface\s+(\w+)\s+extends\s+'
        r'((?:JpaRepository|CrudRepository|PagingAndSortingRepository|'
        r'ReactiveCrudRepository|ReactiveMongoRepository|'
        r'ReactiveSortingRepository|MongoRepository|'
        r'ElasticsearchRepository|CassandraRepository|'
        r'R2dbcRepository|ListCrudRepository|ListPagingAndSortingRepository|'
        r'(?:JpaSpecificationExecutor|QuerydslPredicateExecutor)\s*,?\s*)*'
        r'(?:[\w<>,\s?]*))'
        r'\s*\{',
        re.MULTILINE
    )

    # Extract generic types from repository
    GENERIC_TYPE_PATTERN = re.compile(
        r'(?:Jpa|Crud|PagingAndSorting|ReactiveCrud|ReactiveMongo|'
        r'Mongo|Elasticsearch|Cassandra|R2dbc|ListCrud|ListPagingAndSorting)'
        r'Repository\s*<\s*(\w+)\s*,\s*([\w<>]+)\s*>'
    )

    # @Query annotation
    QUERY_PATTERN = re.compile(
        r'@Query\(\s*(?:value\s*=\s*)?'
        r'"([^"]+)"'
        r'(?:\s*,\s*nativeQuery\s*=\s*(true|false))?'
        r'\s*\)\s*\n'
        r'(?:@Modifying\s*\n)?'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:\w[\w<>,\s?]*)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # @Modifying
    MODIFYING_PATTERN = re.compile(r'@Modifying\b')

    # Derived query methods
    DERIVED_METHOD_PATTERN = re.compile(
        r'(?:List|Optional|Stream|Page|Slice|Flux|Mono|Long|Integer|Boolean|int|long|boolean)?\s*'
        r'<?[\w,\s]*>?\s+'
        r'((?:find|count|delete|exists|remove|read|get|query|search|stream)By\w+)'
        r'\s*\(',
        re.MULTILINE
    )

    # @Cacheable, @CacheEvict, @CachePut
    CACHE_PATTERN = re.compile(
        r'@(Cacheable|CacheEvict|CachePut|Caching)'
        r'(?:\(\s*'
        r'(?:value\s*=\s*)?(?:"([^"]*)"|\{([^}]*)\})?'
        r'(?:\s*,\s*key\s*=\s*"([^"]*)")?'
        r'(?:\s*,\s*condition\s*=\s*"([^"]*)")?'
        r'[^)]*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:(?:public|protected|private)\s+)?'
        r'(?:static\s+)?(?:final\s+)?'
        r'(\w[\w<>,\s]*?)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # @Transactional
    TRANSACTIONAL_PATTERN = re.compile(
        r'@Transactional'
        r'(?:\(\s*'
        r'(?:propagation\s*=\s*Propagation\.(\w+))?'
        r'(?:\s*,?\s*isolation\s*=\s*Isolation\.(\w+))?'
        r'(?:\s*,?\s*readOnly\s*=\s*(true|false))?'
        r'(?:\s*,?\s*timeout\s*=\s*(\d+))?'
        r'(?:\s*,?\s*rollbackFor\s*=\s*(?:\{([^}]*)\}|(\w+\.class)))?'
        r'[^)]*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?(?:\w[\w<>,\s?]*)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Class-level @Transactional
    CLASS_TRANSACTIONAL_PATTERN = re.compile(
        r'@Transactional'
        r'(?:\([^)]*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # JpaSpecificationExecutor
    SPEC_EXECUTOR_PATTERN = re.compile(r'JpaSpecificationExecutor')
    QUERYDSL_PATTERN = re.compile(r'QuerydslPredicateExecutor')
    PAGING_PATTERN = re.compile(r'PagingAndSortingRepository|ListPagingAndSortingRepository')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring Data, cache, and transaction patterns."""
        result: Dict[str, Any] = {
            'repositories': [],
            'query_methods': [],
            'caches': [],
            'transactions': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Repositories
        for match in self.REPO_PATTERN.finditer(content):
            repo_name = match.group(1)
            extends_clause = match.group(2)

            # Extract entity type and ID type
            gen_match = self.GENERIC_TYPE_PATTERN.search(extends_clause)
            entity_type = gen_match.group(1) if gen_match else ""
            id_type = gen_match.group(2) if gen_match else ""

            # Determine base repo type
            repo_type = "JpaRepository"
            for rt in ['JpaRepository', 'CrudRepository', 'PagingAndSortingRepository',
                       'ReactiveCrudRepository', 'ReactiveMongoRepository', 'MongoRepository',
                       'ElasticsearchRepository', 'CassandraRepository', 'R2dbcRepository',
                       'ListCrudRepository', 'ListPagingAndSortingRepository']:
                if rt in extends_clause:
                    repo_type = rt
                    break

            has_spec = bool(self.SPEC_EXECUTOR_PATTERN.search(extends_clause))
            has_querydsl = bool(self.QUERYDSL_PATTERN.search(extends_clause))
            has_paging = bool(self.PAGING_PATTERN.search(extends_clause))

            # Find interface body
            iface_start = match.end()
            brace_count = 1
            iface_end = iface_start
            for i, ch in enumerate(content[iface_start:], iface_start):
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        iface_end = i
                        break

            body = content[iface_start:iface_end]

            # Extract query methods
            custom_queries = []
            for qm in self.QUERY_PATTERN.finditer(body):
                custom_queries.append(qm.group(3))

            # Extract derived methods
            derived_methods = [m.group(1) for m in self.DERIVED_METHOD_PATTERN.finditer(body)]

            result['repositories'].append(SpringBootRepoInfo(
                name=repo_name,
                entity_type=entity_type,
                id_type=id_type,
                repo_type=repo_type,
                custom_queries=custom_queries,
                derived_methods=derived_methods,
                has_specification=has_spec,
                has_querydsl=has_querydsl,
                has_paging=has_paging,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Query methods
        for match in self.QUERY_PATTERN.finditer(content):
            query_text = match.group(1)
            is_native = match.group(2) == 'true' if match.group(2) else False
            method_name = match.group(3)

            # Check for @Modifying
            context_start = max(0, match.start() - 100)
            context = content[context_start:match.start()]
            is_modifying = bool(self.MODIFYING_PATTERN.search(context))

            result['query_methods'].append(SpringBootQueryMethodInfo(
                method_name=method_name,
                query=query_text[:200],
                is_native=is_native,
                is_modifying=is_modifying,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Cache annotations
        for match in self.CACHE_PATTERN.finditer(content):
            annotation = match.group(1)
            cache_name = match.group(2) or ""
            cache_names_str = match.group(3) or ""
            key = match.group(4) or ""
            condition = match.group(5) or ""
            return_type = match.group(6) or ""
            method_name = match.group(7)

            names = []
            if cache_name:
                names.append(cache_name)
            elif cache_names_str:
                names = [n.strip().strip('"') for n in cache_names_str.split(',') if n.strip()]

            result['caches'].append(SpringBootCacheInfo(
                annotation=annotation,
                cache_names=names,
                key=key,
                condition=condition,
                target_method=method_name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @Transactional (method level)
        for match in self.TRANSACTIONAL_PATTERN.finditer(content):
            propagation = match.group(1) or ""
            isolation = match.group(2) or ""
            read_only = match.group(3) == 'true' if match.group(3) else False
            timeout = int(match.group(4)) if match.group(4) else -1
            rollback_str = match.group(5) or match.group(6) or ""
            method_name = match.group(7)

            rollback_for = []
            if rollback_str:
                rollback_for = [r.strip().replace('.class', '') for r in rollback_str.split(',') if r.strip()]

            result['transactions'].append(SpringBootTransactionInfo(
                target_method=method_name,
                propagation=propagation,
                isolation=isolation,
                read_only=read_only,
                timeout=timeout,
                rollback_for=rollback_for,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
