"""
TanStack Query Mutation Extractor for CodeTrellis

Extracts TanStack Query mutation definitions and patterns:
- useMutation() hook calls with mutation function
- Mutation callbacks: onSuccess, onError, onSettled, onMutate
- Optimistic update patterns (onMutate + setQueryData)
- Automatic cache invalidation (invalidateQueries in onSuccess/onSettled)
- Retry configuration
- TypeScript generics (TData, TError, TVariables, TContext)
- Mutation scope and gcTime (v5)

Supports:
- react-query v1-v3 (useMutation with function + options)
- @tanstack/react-query v4 (useMutation with object config)
- @tanstack/react-query v5 (mutationFn required in object, throwOnError)

Part of CodeTrellis v4.57 - TanStack Query Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TanStackMutationInfo:
    """Information about a TanStack Query useMutation() call."""
    name: str  # Variable name or inferred name
    file: str = ""
    line_number: int = 0
    mutation_fn: str = ""  # Mutation function name or expression
    has_on_success: bool = False
    has_on_error: bool = False
    has_on_settled: bool = False
    has_on_mutate: bool = False  # Optimistic update entry point
    has_invalidation: bool = False  # invalidateQueries in callbacks
    has_set_query_data: bool = False  # setQueryData for optimistic updates
    has_optimistic_update: bool = False  # onMutate + setQueryData pattern
    has_retry: bool = False
    has_gc_time: bool = False
    has_cache_time: bool = False
    has_error_boundary: bool = False  # useErrorBoundary/throwOnError
    has_mutation_key: bool = False  # mutationKey for global handlers
    has_scope: bool = False  # scope option (v5)
    has_typescript: bool = False
    type_params: str = ""  # TypeScript generic parameters
    invalidated_queries: List[str] = field(default_factory=list)  # Query keys invalidated
    is_exported: bool = False


class TanStackMutationExtractor:
    """
    Extracts TanStack Query mutation patterns from source code.

    Detects:
    - useMutation() calls with configuration
    - Mutation callbacks (onSuccess, onError, onSettled, onMutate)
    - Optimistic update patterns
    - Cache invalidation patterns
    - Retry and error handling configuration
    - TypeScript generic annotations
    """

    # useMutation pattern
    USE_MUTATION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'useMutation\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Standalone useMutation without assignment
    STANDALONE_MUTATION_PATTERN = re.compile(
        r'useMutation\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # invalidateQueries pattern
    INVALIDATE_PATTERN = re.compile(
        r'(?:queryClient|client)\s*\.\s*invalidateQueries\s*\(\s*'
        r'(?:\{[^}]*queryKey\s*:\s*(\[[^\]]*\]|\w+)[^}]*\}|(\[[^\]]*\]|\w+))',
        re.MULTILINE
    )

    # setQueryData pattern (optimistic updates)
    SET_QUERY_DATA_PATTERN = re.compile(
        r'(?:queryClient|client)\s*\.\s*setQueryData\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all TanStack Query mutation patterns from source code."""
        result: Dict[str, Any] = {
            'mutations': [],
        }

        # Extract useMutation
        for match in self.USE_MUTATION_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            # Get surrounding context for config detection
            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 1200)
            context = content[ctx_start:ctx_end]

            mutation = TanStackMutationInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Detect mutation function
            mf_match = re.search(r'mutationFn\s*:\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)', context)
            if mf_match:
                mutation.mutation_fn = mf_match.group(1).strip()

            # Detect callbacks
            if re.search(r'\bonSuccess\s*:', context):
                mutation.has_on_success = True
            if re.search(r'\bonError\s*:', context):
                mutation.has_on_error = True
            if re.search(r'\bonSettled\s*:', context):
                mutation.has_on_settled = True
            if re.search(r'\bonMutate\s*:', context):
                mutation.has_on_mutate = True

            # Detect cache invalidation
            if 'invalidateQueries' in context:
                mutation.has_invalidation = True
                # Extract invalidated query keys
                for inv_match in self.INVALIDATE_PATTERN.finditer(context):
                    key = inv_match.group(1) or inv_match.group(2)
                    if key:
                        mutation.invalidated_queries.append(key.strip())

            # Detect optimistic update patterns
            if 'setQueryData' in context:
                mutation.has_set_query_data = True
            if mutation.has_on_mutate and mutation.has_set_query_data:
                mutation.has_optimistic_update = True

            # Detect other options
            if re.search(r'\bretry\s*:', context):
                mutation.has_retry = True
            if re.search(r'\bgcTime\s*:', context):
                mutation.has_gc_time = True
            if re.search(r'\bcacheTime\s*:', context):
                mutation.has_cache_time = True
            if re.search(r'\b(?:useErrorBoundary|throwOnError)\s*:', context):
                mutation.has_error_boundary = True
            if re.search(r'\bmutationKey\s*:', context):
                mutation.has_mutation_key = True
            if re.search(r'\bscope\s*:', context):
                mutation.has_scope = True

            result['mutations'].append(mutation)

        # Track matched positions to avoid duplicates
        matched_positions = {m.line_number for m in result['mutations']}

        # Extract standalone useMutation (e.g. return useMutation(...))
        for match in self.STANDALONE_MUTATION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            if line_num in matched_positions:
                continue
            matched_positions.add(line_num)

            type_params = match.group(1) or ""

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 1200)
            context = content[ctx_start:ctx_end]

            # Try to infer name from enclosing function
            before_context = content[max(0, match.start() - 300):match.start()]
            name_match = re.search(r'(?:function|const|let|var)\s+(\w+)', before_context)
            var_name = name_match.group(1) if name_match else "anonymous"

            mutation = TanStackMutationInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                has_typescript=bool(type_params),
                type_params=type_params,
            )

            # Detect mutation function
            mf_match = re.search(r'mutationFn\s*:\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)', context)
            if mf_match:
                mutation.mutation_fn = mf_match.group(1).strip()

            # Detect callbacks
            if re.search(r'\bonSuccess\s*:', context):
                mutation.has_on_success = True
            if re.search(r'\bonError\s*:', context):
                mutation.has_on_error = True
            if re.search(r'\bonSettled\s*:', context):
                mutation.has_on_settled = True
            if re.search(r'\bonMutate\s*:', context):
                mutation.has_on_mutate = True

            # Detect cache invalidation
            if 'invalidateQueries' in context:
                mutation.has_invalidation = True
                for inv_match in self.INVALIDATE_PATTERN.finditer(context):
                    key = inv_match.group(1) or inv_match.group(2)
                    if key:
                        mutation.invalidated_queries.append(key.strip())

            # Detect optimistic update patterns
            if 'setQueryData' in context:
                mutation.has_set_query_data = True
            if mutation.has_on_mutate and mutation.has_set_query_data:
                mutation.has_optimistic_update = True

            result['mutations'].append(mutation)

        return result
