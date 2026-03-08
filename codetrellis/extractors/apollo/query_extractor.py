"""
Apollo Client Query Extractor for CodeTrellis

Extracts Apollo Client query usage patterns:
- useQuery() hook calls with variables and options
- useLazyQuery() for imperative query execution
- useSuspenseQuery() for React Suspense (v3.8+)
- useBackgroundQuery() + useReadQuery() (v3.8+)
- client.query() / client.watchQuery() imperative methods
- graphql() HOC (legacy v2 pattern)
- gql tagged template literals (query definitions)
- Query variables, fetchPolicy, pollInterval, skip, error policies
- TypeScript generics and codegen types

Supports:
- Apollo Client v1.x (apollo-client, graphql-tag)
- Apollo Client v2.x (@apollo/react-hooks, apollo-boost, react-apollo)
- Apollo Client v3.x (@apollo/client unified package, v3.8+ Suspense hooks)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ApolloQueryInfo:
    """Information about a useQuery() or useSuspenseQuery() call."""
    name: str  # Variable name or inferred name
    file: str = ""
    line_number: int = 0
    query_name: str = ""  # Name of the gql query document
    hook_name: str = "useQuery"  # useQuery, useSuspenseQuery, useBackgroundQuery, useReadQuery
    has_variables: bool = False
    has_fetch_policy: bool = False
    fetch_policy: str = ""  # cache-first, network-only, cache-and-network, etc.
    has_poll_interval: bool = False
    has_skip: bool = False
    has_error_policy: bool = False
    error_policy: str = ""  # none, ignore, all
    has_on_completed: bool = False
    has_on_error: bool = False
    has_context: bool = False
    has_client: bool = False  # custom client via options
    has_ssr: bool = False  # ssr option
    has_partial_refetch: bool = False
    has_return_partial_data: bool = False
    has_not_if_loaded: bool = False
    has_typescript: bool = False
    type_params: str = ""  # TypeScript generic parameters
    is_exported: bool = False


@dataclass
class ApolloLazyQueryInfo:
    """Information about a useLazyQuery() call."""
    name: str
    file: str = ""
    line_number: int = 0
    query_name: str = ""
    has_variables: bool = False
    has_fetch_policy: bool = False
    fetch_policy: str = ""
    has_on_completed: bool = False
    has_on_error: bool = False
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class ApolloGqlTagInfo:
    """Information about a gql tagged template literal."""
    name: str  # Variable name
    file: str = ""
    line_number: int = 0
    operation_type: str = ""  # query, mutation, subscription, fragment
    operation_name: str = ""  # Name from the GraphQL operation
    has_variables: bool = False
    has_fragments: bool = False
    is_exported: bool = False


class ApolloQueryExtractor:
    """
    Extracts Apollo Client query definitions from source code.

    Detects:
    - useQuery() / useSuspenseQuery() / useBackgroundQuery() / useReadQuery()
    - useLazyQuery() for imperative queries
    - client.query() / client.watchQuery()
    - graphql() HOC (legacy v2)
    - gql tagged template literals
    - Query configuration options
    - TypeScript generic annotations
    """

    # useQuery / useSuspenseQuery / useBackgroundQuery
    USE_QUERY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'(useQuery|useSuspenseQuery|useBackgroundQuery|useReadQuery)\s*'
        r'(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # useLazyQuery
    USE_LAZY_QUERY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\[[^\]]+\]|\w+)\s*=\s*'
        r'useLazyQuery\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # client.query() / client.watchQuery()
    CLIENT_QUERY_PATTERN = re.compile(
        r'(?:client|apolloClient)\s*\.\s*(query|watchQuery)\s*'
        r'(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # graphql() HOC (legacy v2)
    GRAPHQL_HOC_PATTERN = re.compile(
        r'graphql\s*(?:<([^>]*)>)?\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # gql tagged template literal
    GQL_TAG_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*gql\s*`',
        re.MULTILINE
    )

    # Operation type inside gql template
    OPERATION_TYPE_PATTERN = re.compile(
        r'(?:query|mutation|subscription|fragment)\s+(\w+)',
        re.MULTILINE
    )

    # fetchPolicy detection
    FETCH_POLICY_PATTERN = re.compile(
        r'fetchPolicy\s*:\s*[\'"](\w[\w-]*)[\'"]',
        re.MULTILINE
    )

    # errorPolicy detection
    ERROR_POLICY_PATTERN = re.compile(
        r'errorPolicy\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Apollo query patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'queries', 'lazy_queries', 'gql_tags' lists
        """
        queries: List[ApolloQueryInfo] = []
        lazy_queries: List[ApolloLazyQueryInfo] = []
        gql_tags: List[ApolloGqlTagInfo] = []

        lines = content.split('\n')

        # Extract useQuery / useSuspenseQuery / useBackgroundQuery / useReadQuery
        for match in self.USE_QUERY_PATTERN.finditer(content):
            name = match.group(1).strip()
            hook_name = match.group(2)
            type_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Get the query argument and options context
            ctx_start = match.end()
            ctx_end = min(ctx_start + 500, len(content))
            ctx = content[ctx_start:ctx_end]

            # Try to find query name (first argument)
            query_name = ""
            qname_match = re.match(r'\s*(\w+)', ctx)
            if qname_match:
                query_name = qname_match.group(1)

            # Detect fetch policy
            fp_match = self.FETCH_POLICY_PATTERN.search(ctx)
            fetch_policy = fp_match.group(1) if fp_match else ""

            # Detect error policy
            ep_match = self.ERROR_POLICY_PATTERN.search(ctx)
            error_policy = ep_match.group(1) if ep_match else ""

            queries.append(ApolloQueryInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                query_name=query_name,
                hook_name=hook_name,
                has_variables='variables' in ctx[:300],
                has_fetch_policy=bool(fp_match),
                fetch_policy=fetch_policy,
                has_poll_interval='pollInterval' in ctx[:300],
                has_skip='skip' in ctx[:200] and 'skip:' in ctx[:200],
                has_error_policy=bool(ep_match),
                error_policy=error_policy,
                has_on_completed='onCompleted' in ctx[:300],
                has_on_error='onError' in ctx[:300],
                has_context='context' in ctx[:300] and 'context:' in ctx[:300],
                has_client='client:' in ctx[:300] or 'client :' in ctx[:300],
                has_ssr='ssr' in ctx[:200] and ('ssr:' in ctx[:200] or 'ssr :' in ctx[:200]),
                has_partial_refetch='partialRefetch' in ctx[:300],
                has_return_partial_data='returnPartialData' in ctx[:300],
                has_not_if_loaded='notifyOnNetworkStatusChange' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            ))

        # Extract useLazyQuery
        for match in self.USE_LAZY_QUERY_PATTERN.finditer(content):
            name = match.group(1).strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            query_name = ""
            qname_match = re.match(r'\s*(\w+)', ctx)
            if qname_match:
                query_name = qname_match.group(1)

            fp_match = self.FETCH_POLICY_PATTERN.search(ctx)

            lazy_queries.append(ApolloLazyQueryInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                query_name=query_name,
                has_variables='variables' in ctx[:300],
                has_fetch_policy=bool(fp_match),
                fetch_policy=fp_match.group(1) if fp_match else "",
                has_on_completed='onCompleted' in ctx[:300],
                has_on_error='onError' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            ))

        # Extract client.query() / client.watchQuery()
        for match in self.CLIENT_QUERY_PATTERN.finditer(content):
            method = match.group(1)
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            query_name = ""
            qname_match = re.search(r'query\s*:\s*(\w+)', ctx)
            if qname_match:
                query_name = qname_match.group(1)

            fp_match = self.FETCH_POLICY_PATTERN.search(ctx)

            queries.append(ApolloQueryInfo(
                name=f"client.{method}",
                file=file_path,
                line_number=line_num,
                query_name=query_name,
                hook_name=f"client.{method}",
                has_variables='variables' in ctx[:300],
                has_fetch_policy=bool(fp_match),
                fetch_policy=fp_match.group(1) if fp_match else "",
                has_typescript=bool(type_params),
                type_params=type_params,
            ))

        # Extract gql tagged template literals
        for match in self.GQL_TAG_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Find template content
            tpl_start = match.end() - 1  # start at backtick
            tpl_end = content.find('`', tpl_start + 1)
            tpl_content = content[tpl_start + 1:tpl_end] if tpl_end > tpl_start else ""

            operation_type = ""
            operation_name = ""
            op_match = self.OPERATION_TYPE_PATTERN.search(tpl_content)
            if op_match:
                # Check what came before the name
                pre = tpl_content[:op_match.start()].strip()
                if 'mutation' in tpl_content[:op_match.start() + 20]:
                    operation_type = "mutation"
                elif 'subscription' in tpl_content[:op_match.start() + 20]:
                    operation_type = "subscription"
                elif 'fragment' in tpl_content[:op_match.start() + 20]:
                    operation_type = "fragment"
                else:
                    operation_type = "query"
                operation_name = op_match.group(1)

            gql_tags.append(ApolloGqlTagInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                operation_type=operation_type,
                operation_name=operation_name,
                has_variables='$' in tpl_content,
                has_fragments='...' in tpl_content or 'fragment' in tpl_content.lower(),
                is_exported=is_exported,
            ))

        return {
            'queries': queries,
            'lazy_queries': lazy_queries,
            'gql_tags': gql_tags,
        }
