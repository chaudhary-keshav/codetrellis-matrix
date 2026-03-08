"""
Apollo Client Cache Extractor for CodeTrellis

Extracts Apollo Client cache configuration and usage patterns:
- InMemoryCache instantiation with typePolicies
- typePolicies with keyFields, merge, read functions
- Field policies (read/merge functions, keyArgs)
- cache.readQuery / cache.writeQuery / cache.readFragment / cache.writeFragment
- cache.modify with field modifiers
- cache.evict / cache.gc() for garbage collection
- makeVar() reactive variables
- possibleTypes for unions/interfaces (fragment matching)
- fetchPolicy options across queries/mutations
- Local state management with @client directive

Supports:
- Apollo Client v1.x (basic cache, InMemoryCache)
- Apollo Client v2.x (InMemoryCache, dataIdFromObject, fragmentMatcher)
- Apollo Client v3.x (typePolicies, field policies, reactive variables, cache.modify)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ApolloCacheConfigInfo:
    """Information about InMemoryCache configuration."""
    file: str = ""
    line_number: int = 0
    has_type_policies: bool = False
    has_possible_types: bool = False
    has_data_id_from_object: bool = False  # v2 legacy
    has_fragment_matcher: bool = False  # v2 legacy
    has_add_typename: bool = False
    has_result_caching: bool = False
    has_cache_redirect: bool = False  # v2 legacy
    policy_count: int = 0  # Number of type policies
    version_hint: str = ""  # v2 or v3 based on patterns


@dataclass
class ApolloTypePolicyInfo:
    """Information about a type policy definition."""
    type_name: str  # The GraphQL type name (e.g., "Query", "User")
    file: str = ""
    line_number: int = 0
    has_key_fields: bool = False
    key_fields: str = ""  # Key fields expression
    has_merge: bool = False  # Type-level merge function
    field_count: int = 0  # Number of field policies
    field_names: List[str] = field(default_factory=list)
    has_read: bool = False  # Any field has read function
    has_field_merge: bool = False  # Any field has merge function
    has_key_args: bool = False  # Any field has keyArgs


@dataclass
class ApolloReactiveVarInfo:
    """Information about a makeVar() reactive variable."""
    name: str
    file: str = ""
    line_number: int = 0
    initial_value: str = ""
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class ApolloCacheOperationInfo:
    """Information about a cache operation (read/write/modify/evict)."""
    operation: str  # readQuery, writeQuery, readFragment, writeFragment, modify, evict, gc
    file: str = ""
    line_number: int = 0
    query_name: str = ""
    has_variables: bool = False
    has_fragment: bool = False
    has_broadcast: bool = False
    has_optimistic: bool = False


class ApolloCacheExtractor:
    """
    Extracts Apollo Client cache configuration and operations from source code.

    Detects:
    - InMemoryCache instantiation and configuration
    - typePolicies with field policies (v3)
    - cache.readQuery/writeQuery/readFragment/writeFragment
    - cache.modify / cache.evict / cache.gc()
    - makeVar() reactive variables
    - possibleTypes for unions/interfaces
    - fetchPolicy patterns
    - @client directive for local state
    """

    # InMemoryCache instantiation
    IN_MEMORY_CACHE_PATTERN = re.compile(
        r'new\s+InMemoryCache\s*\(',
        re.MULTILINE
    )

    # typePolicies
    TYPE_POLICIES_PATTERN = re.compile(
        r'typePolicies\s*:\s*\{',
        re.MULTILINE
    )

    # Individual type policy: TypeName: { ... }
    TYPE_POLICY_ENTRY_PATTERN = re.compile(
        r"(\w+)\s*:\s*\{\s*(?:keyFields|fields|merge)",
        re.MULTILINE
    )

    # makeVar() reactive variable
    MAKE_VAR_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*makeVar\s*'
        r'(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Cache operations
    CACHE_OPERATION_PATTERN = re.compile(
        r'(?:cache|client\.cache)\s*\.\s*(readQuery|writeQuery|readFragment|writeFragment|modify|evict|gc)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # possibleTypes
    POSSIBLE_TYPES_PATTERN = re.compile(
        r'possibleTypes\s*:',
        re.MULTILINE
    )

    # @client directive
    CLIENT_DIRECTIVE_PATTERN = re.compile(
        r'@client\b',
        re.MULTILINE
    )

    # fetchPolicy values
    FETCH_POLICY_PATTERN = re.compile(
        r"fetchPolicy\s*:\s*['\"](\w[\w-]*)['\"]",
        re.MULTILINE
    )

    # dataIdFromObject (v2 legacy)
    DATA_ID_FROM_OBJECT_PATTERN = re.compile(
        r'dataIdFromObject\s*[:\(]',
        re.MULTILINE
    )

    # fragmentMatcher / IntrospectionFragmentMatcher (v2 legacy)
    FRAGMENT_MATCHER_PATTERN = re.compile(
        r'(?:IntrospectionFragmentMatcher|fragmentMatcher)\s*[:\(]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Apollo cache patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'cache_configs', 'type_policies', 'reactive_vars',
                       'cache_operations' lists
        """
        cache_configs: List[ApolloCacheConfigInfo] = []
        type_policies: List[ApolloTypePolicyInfo] = []
        reactive_vars: List[ApolloReactiveVarInfo] = []
        cache_operations: List[ApolloCacheOperationInfo] = []

        # Extract InMemoryCache
        for match in self.IN_MEMORY_CACHE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 1500, len(content))
            ctx = content[ctx_start:ctx_end]

            has_type_policies = bool(self.TYPE_POLICIES_PATTERN.search(ctx))
            has_possible_types = bool(self.POSSIBLE_TYPES_PATTERN.search(ctx))
            has_data_id = bool(self.DATA_ID_FROM_OBJECT_PATTERN.search(ctx))
            has_fragment_matcher = bool(self.FRAGMENT_MATCHER_PATTERN.search(ctx))

            # Determine version hint
            version_hint = ""
            if has_type_policies or 'makeVar' in content:
                version_hint = "v3"
            elif has_data_id or has_fragment_matcher:
                version_hint = "v2"

            # Count policies
            policy_count = len(self.TYPE_POLICY_ENTRY_PATTERN.findall(ctx))

            cache_configs.append(ApolloCacheConfigInfo(
                file=file_path,
                line_number=line_num,
                has_type_policies=has_type_policies,
                has_possible_types=has_possible_types,
                has_data_id_from_object=has_data_id,
                has_fragment_matcher=has_fragment_matcher,
                has_add_typename='addTypename' in ctx[:500],
                has_result_caching='resultCaching' in ctx[:500],
                has_cache_redirect='cacheRedirects' in ctx[:500],
                policy_count=policy_count,
                version_hint=version_hint,
            ))

        # Extract individual type policies
        for match in self.TYPE_POLICY_ENTRY_PATTERN.finditer(content):
            type_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.start()
            ctx_end = min(ctx_start + 800, len(content))
            ctx = content[ctx_start:ctx_end]

            # Find field names in fields: { ... }
            field_names: List[str] = []
            fields_match = re.search(r'fields\s*:\s*\{', ctx)
            if fields_match:
                fields_ctx = ctx[fields_match.end():]
                # Extract field names (simple word followed by : or {)
                for fm in re.finditer(r'(\w+)\s*[:\{]', fields_ctx[:500]):
                    fn = fm.group(1)
                    if fn not in ('read', 'merge', 'keyArgs', 'function', 'return', 'const', 'let', 'var', 'if', 'else'):
                        field_names.append(fn)

            type_policies.append(ApolloTypePolicyInfo(
                type_name=type_name,
                file=file_path,
                line_number=line_num,
                has_key_fields='keyFields' in ctx[:300],
                key_fields=self._extract_key_fields(ctx),
                has_merge='merge:' in ctx[:200] or 'merge(' in ctx[:200],
                field_count=len(field_names),
                field_names=field_names[:10],  # Limit
                has_read='read:' in ctx[:500] or 'read(' in ctx[:500],
                has_field_merge=bool(re.search(r'fields.*merge', ctx[:500], re.DOTALL)),
                has_key_args='keyArgs' in ctx[:500],
            ))

        # Extract makeVar() reactive variables
        for match in self.MAKE_VAR_PATTERN.finditer(content):
            name = match.group(1)
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Try to get initial value
            ctx_start = match.end()
            ctx_end = min(ctx_start + 200, len(content))
            ctx = content[ctx_start:ctx_end]
            initial_value = ""
            iv_match = re.match(r'\s*([^)]+)', ctx)
            if iv_match:
                initial_value = iv_match.group(1).strip()[:80]

            reactive_vars.append(ApolloReactiveVarInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                initial_value=initial_value,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            ))

        # Extract cache operations
        for match in self.CACHE_OPERATION_PATTERN.finditer(content):
            operation = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            query_name = ""
            qname_match = re.search(r'query\s*:\s*(\w+)', ctx)
            if qname_match:
                query_name = qname_match.group(1)

            cache_operations.append(ApolloCacheOperationInfo(
                operation=operation,
                file=file_path,
                line_number=line_num,
                query_name=query_name,
                has_variables='variables' in ctx[:200],
                has_fragment='fragment' in ctx[:200].lower(),
                has_broadcast='broadcast' in ctx[:200],
                has_optimistic='optimistic' in ctx[:200],
            ))

        return {
            'cache_configs': cache_configs,
            'type_policies': type_policies,
            'reactive_vars': reactive_vars,
            'cache_operations': cache_operations,
        }

    @staticmethod
    def _extract_key_fields(ctx: str) -> str:
        """Extract keyFields value from context."""
        kf_match = re.search(r'keyFields\s*:\s*(\[[^\]]*\]|false|"[^"]*")', ctx)
        if kf_match:
            return kf_match.group(1)[:60]
        return ""
