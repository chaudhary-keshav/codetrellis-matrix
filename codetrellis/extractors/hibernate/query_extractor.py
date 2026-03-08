"""
Hibernate Query Extractor - Extracts HQL, JPQL, Criteria API, and native SQL.

Extracts:
- HQL queries (Hibernate Query Language)
- JPQL queries (Java Persistence Query Language)
- Criteria API usage (CriteriaBuilder, CriteriaQuery, Predicates)
- Native SQL queries
- Named queries (@NamedQuery, @NamedNativeQuery)
- Repository method queries (Spring Data JPA)
- Query hints and fetch profiles
- Pagination and sorting
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HibernateQueryInfo:
    """Information about an HQL/JPQL/SQL query."""
    query_type: str = ""  # hql, jpql, native_sql
    query_string: str = ""
    method_name: str = ""
    return_type: str = ""
    parameters: List[str] = field(default_factory=list)
    is_update: bool = False
    is_delete: bool = False
    uses_pagination: bool = False
    line_number: int = 0


@dataclass
class HibernateCriteriaInfo:
    """Information about Criteria API usage."""
    root_entity: str = ""
    predicates: List[str] = field(default_factory=list)
    joins: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    projections: List[str] = field(default_factory=list)
    is_multiselect: bool = False
    line_number: int = 0


@dataclass
class HibernateNamedQueryInfo:
    """Information about a named query."""
    name: str = ""
    query: str = ""
    query_type: str = ""  # named_query, named_native_query
    result_class: str = ""
    hints: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


class HibernateQueryExtractor:
    """Extracts query information from Hibernate/JPA source code."""

    # HQL/JPQL query creation
    CREATE_QUERY_PATTERN = re.compile(
        r'(?:session|entityManager|em)\s*\.\s*createQuery\s*\(\s*'
        r'["\']([^"\']+)["\'](?:\s*,\s*(\w+)\.class)?',
        re.MULTILINE
    )

    # Native SQL query creation
    NATIVE_QUERY_PATTERN = re.compile(
        r'(?:session|entityManager|em)\s*\.\s*createNativeQuery\s*\(\s*'
        r'["\']([^"\']+)["\'](?:\s*,\s*(\w+)\.class)?',
        re.MULTILINE
    )

    # Named query reference
    NAMED_QUERY_REF_PATTERN = re.compile(
        r'(?:session|entityManager|em)\s*\.\s*createNamedQuery\s*\(\s*'
        r'["\']([^"\']+)["\'](?:\s*,\s*(\w+)\.class)?',
        re.MULTILINE
    )

    # Named query definition
    NAMED_QUERY_DEF_PATTERN = re.compile(
        r'@NamedQuery\s*\(\s*'
        r'name\s*=\s*["\']([^"\']+)["\']'
        r'(?:\s*,\s*query\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    NAMED_NATIVE_QUERY_DEF_PATTERN = re.compile(
        r'@NamedNativeQuery\s*\(\s*'
        r'name\s*=\s*["\']([^"\']+)["\']'
        r'(?:\s*,\s*query\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s*,\s*resultClass\s*=\s*(\w+)\.class)?',
        re.DOTALL
    )

    # Criteria API
    CRITERIA_BUILDER_PATTERN = re.compile(
        r'CriteriaBuilder\s+(\w+)\s*=\s*'
        r'(?:session|entityManager|em)\s*\.\s*getCriteriaBuilder\s*\(',
        re.MULTILINE
    )

    CRITERIA_QUERY_PATTERN = re.compile(
        r'CriteriaQuery\s*<\s*(\w+)\s*>\s+(\w+)\s*=',
        re.MULTILINE
    )

    CRITERIA_ROOT_PATTERN = re.compile(
        r'Root\s*<\s*(\w+)\s*>\s+(\w+)\s*=\s*\w+\.from\(',
        re.MULTILINE
    )

    CRITERIA_JOIN_PATTERN = re.compile(
        r'(?:Join|SetJoin|ListJoin|MapJoin)\s*<[^>]+>\s+(\w+)\s*=\s*'
        r'\w+\.join\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    CRITERIA_PREDICATE_PATTERN = re.compile(
        r'\w+\.\s*(equal|notEqual|like|greaterThan|lessThan|'
        r'greaterThanOrEqualTo|lessThanOrEqualTo|between|'
        r'isNull|isNotNull|in|isMember|isEmpty|isNotEmpty)\s*\(',
        re.MULTILINE
    )

    # Spring Data JPA @Query
    SPRING_QUERY_PATTERN = re.compile(
        r'@Query\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'
        r'(?:\s*,\s*nativeQuery\s*=\s*(true|false))?'
        r'(?:\s*,\s*countQuery\s*=\s*["\']([^"\']+)["\'])?\s*\)\s*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        re.DOTALL
    )

    # Query parameter patterns
    PARAMETER_PATTERN = re.compile(
        r'\.setParameter\s*\(\s*(?:["\'](\w+)["\']|(\d+))\s*,',
        re.MULTILINE
    )

    # Pagination
    PAGINATION_PATTERN = re.compile(
        r'\.setFirstResult\s*\(|\.setMaxResults\s*\(|'
        r'Pageable\s+\w+|PageRequest\.of\(',
        re.MULTILINE
    )

    # Query hint
    QUERY_HINT_PATTERN = re.compile(
        r'@QueryHint\s*\(\s*name\s*=\s*["\']([^"\']+)["\']'
        r'\s*,\s*value\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Fetch profile
    FETCH_PROFILE_PATTERN = re.compile(
        r'@FetchProfile\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract query information from Hibernate/JPA source code."""
        queries: List[HibernateQueryInfo] = []
        criteria_queries: List[HibernateCriteriaInfo] = []
        named_queries: List[HibernateNamedQueryInfo] = []
        fetch_profiles: List[str] = []

        if not content or not content.strip():
            return {
                'queries': queries,
                'criteria_queries': criteria_queries,
                'named_queries': named_queries,
                'fetch_profiles': fetch_profiles,
            }

        # HQL/JPQL queries
        for match in self.CREATE_QUERY_PATTERN.finditer(content):
            query_str = match.group(1)
            q = HibernateQueryInfo(
                query_type="hql",
                query_string=query_str,
                return_type=match.group(2) or "",
                is_update='UPDATE' in query_str.upper() or 'INSERT' in query_str.upper(),
                is_delete='DELETE' in query_str.upper(),
                line_number=content[:match.start()].count('\n') + 1,
            )
            queries.append(q)

        # Native SQL queries
        for match in self.NATIVE_QUERY_PATTERN.finditer(content):
            query_str = match.group(1)
            q = HibernateQueryInfo(
                query_type="native_sql",
                query_string=query_str,
                return_type=match.group(2) or "",
                is_update='UPDATE' in query_str.upper() or 'INSERT' in query_str.upper(),
                is_delete='DELETE' in query_str.upper(),
                line_number=content[:match.start()].count('\n') + 1,
            )
            queries.append(q)

        # Spring Data @Query
        for match in self.SPRING_QUERY_PATTERN.finditer(content):
            is_native = match.group(2) == 'true'
            query_str = match.group(1)
            q = HibernateQueryInfo(
                query_type="native_sql" if is_native else "jpql",
                query_string=query_str,
                method_name=match.group(4) or "",
                is_update='UPDATE' in query_str.upper() or 'INSERT' in query_str.upper(),
                is_delete='DELETE' in query_str.upper(),
                uses_pagination='countQuery' in (match.group(0) or ""),
                line_number=content[:match.start()].count('\n') + 1,
            )
            queries.append(q)

        # Named query definitions
        for match in self.NAMED_QUERY_DEF_PATTERN.finditer(content):
            nq = HibernateNamedQueryInfo(
                name=match.group(1) or "",
                query=match.group(2) or "",
                query_type="named_query",
                line_number=content[:match.start()].count('\n') + 1,
            )
            named_queries.append(nq)

        for match in self.NAMED_NATIVE_QUERY_DEF_PATTERN.finditer(content):
            nq = HibernateNamedQueryInfo(
                name=match.group(1) or "",
                query=match.group(2) or "",
                query_type="named_native_query",
                result_class=match.group(3) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            named_queries.append(nq)

        # Criteria API
        for match in self.CRITERIA_BUILDER_PATTERN.finditer(content):
            criteria = HibernateCriteriaInfo(
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Find root entity
            root = self.CRITERIA_ROOT_PATTERN.search(content)
            if root:
                criteria.root_entity = root.group(1)

            # Find joins
            for join in self.CRITERIA_JOIN_PATTERN.finditer(content):
                criteria.joins.append(join.group(2))

            # Find predicates
            for pred in self.CRITERIA_PREDICATE_PATTERN.finditer(content):
                criteria.predicates.append(pred.group(1))

            criteria_queries.append(criteria)

        # Fetch profiles
        for match in self.FETCH_PROFILE_PATTERN.finditer(content):
            fetch_profiles.append(match.group(1))

        return {
            'queries': queries,
            'criteria_queries': criteria_queries,
            'named_queries': named_queries,
            'fetch_profiles': fetch_profiles,
        }
