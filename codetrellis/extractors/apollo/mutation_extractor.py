"""
Apollo Client Mutation Extractor for CodeTrellis

Extracts Apollo Client mutation usage patterns:
- useMutation() hook calls with options
- client.mutate() imperative calls
- optimisticResponse for optimistic UI updates
- update function for manual cache updates
- refetchQueries / awaitRefetchQueries
- onCompleted / onError callbacks
- errorPolicy, context, ignoreResults
- TypeScript generics

Supports:
- Apollo Client v1.x (apollo-client)
- Apollo Client v2.x (@apollo/react-hooks, react-apollo)
- Apollo Client v3.x (@apollo/client unified package)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ApolloMutationInfo:
    """Information about a useMutation() or client.mutate() call."""
    name: str  # Variable name or 'client.mutate'
    file: str = ""
    line_number: int = 0
    mutation_name: str = ""  # Name of the gql mutation document
    hook_name: str = "useMutation"  # useMutation, client.mutate
    has_variables: bool = False
    has_optimistic_response: bool = False
    has_update: bool = False  # update cache function
    has_refetch_queries: bool = False
    has_await_refetch_queries: bool = False
    has_on_completed: bool = False
    has_on_error: bool = False
    has_on_query_updated: bool = False  # v3.8+
    has_error_policy: bool = False
    has_context: bool = False
    has_ignore_results: bool = False
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class ApolloOptimisticResponseInfo:
    """Information about an optimisticResponse in a mutation."""
    file: str = ""
    line_number: int = 0
    mutation_name: str = ""
    has_typename: bool = False  # includes __typename
    has_id: bool = False  # includes id field
    pattern: str = ""  # optimistic_response, update_cache, refetch


class ApolloMutationExtractor:
    """
    Extracts Apollo Client mutation definitions from source code.

    Detects:
    - useMutation() hook calls with configuration
    - client.mutate() imperative mutations
    - optimisticResponse patterns
    - Cache update functions (readQuery/writeQuery in update)
    - refetchQueries patterns
    - TypeScript generic annotations
    """

    # useMutation() pattern
    USE_MUTATION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\[[^\]]+\]|\w+)\s*=\s*'
        r'useMutation\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # client.mutate() pattern
    CLIENT_MUTATE_PATTERN = re.compile(
        r'(?:client|apolloClient)\s*\.\s*mutate\s*'
        r'(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # optimisticResponse detection
    OPTIMISTIC_RESPONSE_PATTERN = re.compile(
        r'optimisticResponse\s*[:\(]',
        re.MULTILINE
    )

    # refetchQueries detection
    REFETCH_QUERIES_PATTERN = re.compile(
        r'refetchQueries\s*:',
        re.MULTILINE
    )

    # update function detection (cache update)
    # Matches: update: (cache, ...) | update: function | update(cache, ...)
    UPDATE_PATTERN = re.compile(
        r'update\s*(?::\s*(?:\(|function)|(?=\s*\(\s*(?:cache|store)\b))',
        re.MULTILINE
    )

    # Cache read/write in update functions
    CACHE_UPDATE_PATTERN = re.compile(
        r'(?:cache|store)\s*\.\s*(readQuery|writeQuery|readFragment|writeFragment|modify|evict)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Apollo mutation patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'mutations', 'optimistic_responses' lists
        """
        mutations: List[ApolloMutationInfo] = []
        optimistic_responses: List[ApolloOptimisticResponseInfo] = []

        # Extract useMutation()
        for match in self.USE_MUTATION_PATTERN.finditer(content):
            name = match.group(1).strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            ctx_start = match.end()
            ctx_end = min(ctx_start + 600, len(content))
            ctx = content[ctx_start:ctx_end]

            # Try to find mutation name (first argument)
            mutation_name = ""
            mname_match = re.match(r'\s*(\w+)', ctx)
            if mname_match:
                mutation_name = mname_match.group(1)

            has_optimistic = bool(self.OPTIMISTIC_RESPONSE_PATTERN.search(ctx))
            has_update = bool(self.UPDATE_PATTERN.search(ctx))
            has_refetch = bool(self.REFETCH_QUERIES_PATTERN.search(ctx))

            mutations.append(ApolloMutationInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                mutation_name=mutation_name,
                hook_name="useMutation",
                has_variables='variables' in ctx[:300],
                has_optimistic_response=has_optimistic,
                has_update=has_update,
                has_refetch_queries=has_refetch,
                has_await_refetch_queries='awaitRefetchQueries' in ctx[:400],
                has_on_completed='onCompleted' in ctx[:400],
                has_on_error='onError' in ctx[:400],
                has_on_query_updated='onQueryUpdated' in ctx[:400],
                has_error_policy='errorPolicy' in ctx[:300],
                has_context='context:' in ctx[:300] or 'context :' in ctx[:300],
                has_ignore_results='ignoreResults' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            ))

            # Track optimistic response patterns
            if has_optimistic:
                optimistic_responses.append(ApolloOptimisticResponseInfo(
                    file=file_path,
                    line_number=line_num,
                    mutation_name=mutation_name,
                    has_typename='__typename' in ctx,
                    has_id=bool(re.search(r'\bid\s*:', ctx[:400])),
                    pattern="optimistic_response",
                ))

        # Extract client.mutate()
        for match in self.CLIENT_MUTATE_PATTERN.finditer(content):
            type_params = match.group(1) or ""
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 500, len(content))
            ctx = content[ctx_start:ctx_end]

            mutation_name = ""
            mname_match = re.search(r'mutation\s*:\s*(\w+)', ctx)
            if mname_match:
                mutation_name = mname_match.group(1)

            has_optimistic = bool(self.OPTIMISTIC_RESPONSE_PATTERN.search(ctx))
            has_update = bool(self.UPDATE_PATTERN.search(ctx))
            has_refetch = bool(self.REFETCH_QUERIES_PATTERN.search(ctx))

            mutations.append(ApolloMutationInfo(
                name="client.mutate",
                file=file_path,
                line_number=line_num,
                mutation_name=mutation_name,
                hook_name="client.mutate",
                has_variables='variables' in ctx[:300],
                has_optimistic_response=has_optimistic,
                has_update=has_update,
                has_refetch_queries=has_refetch,
                has_await_refetch_queries='awaitRefetchQueries' in ctx[:400],
                has_on_completed='onCompleted' in ctx[:400] if 'then(' not in ctx[:400] else False,
                has_on_error='onError' in ctx[:400] if 'catch(' not in ctx[:400] else False,
                has_error_policy='errorPolicy' in ctx[:300],
                has_context='context:' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
            ))

            if has_optimistic:
                optimistic_responses.append(ApolloOptimisticResponseInfo(
                    file=file_path,
                    line_number=line_num,
                    mutation_name=mutation_name,
                    has_typename='__typename' in ctx,
                    has_id=bool(re.search(r'\bid\s*:', ctx[:400])),
                    pattern="optimistic_response",
                ))

        return {
            'mutations': mutations,
            'optimistic_responses': optimistic_responses,
        }
