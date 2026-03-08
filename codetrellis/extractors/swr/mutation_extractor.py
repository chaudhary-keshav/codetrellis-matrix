"""
SWR Mutation Extractor for CodeTrellis

Extracts SWR mutation patterns (v2+):
- useSWRMutation() hook calls (v2+ remote mutations)
- Optimistic UI patterns with mutate() + optimisticData
- Bound mutate with rollback patterns
- Manual cache updates via mutate(key, data)
- Error rollback (rollbackOnError)
- populateCache for selective cache updates

Supports:
- swr v0.x-v1.x (manual mutate() for mutations)
- swr v2.x (useSWRMutation dedicated hook, optimisticData, rollbackOnError,
             populateCache, revalidate option)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SWRMutationHookInfo:
    """Information about a useSWRMutation() call (v2+)."""
    name: str  # Variable name or inferred name
    file: str = ""
    line_number: int = 0
    key: str = ""  # SWR key
    mutation_fn: str = ""  # Mutation fetcher function
    has_optimistic_data: bool = False
    has_rollback_on_error: bool = False
    has_populate_cache: bool = False
    has_revalidate: bool = False
    has_on_success: bool = False
    has_on_error: bool = False
    has_throw_on_error: bool = False  # throwOnError option
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class SWROptimisticUpdateInfo:
    """Information about an optimistic update pattern."""
    file: str = ""
    line_number: int = 0
    key: str = ""  # Key being updated
    has_rollback: bool = False
    pattern_type: str = ""  # 'bound_mutate', 'global_mutate', 'useSWRMutation'


class SWRMutationExtractor:
    """
    Extracts SWR mutation patterns from source code.

    Detects:
    - useSWRMutation() calls with configuration (v2+)
    - Optimistic update patterns (mutate with optimisticData)
    - Manual cache mutation via mutate(key, data)
    - Rollback patterns (rollbackOnError)
    - Cache population (populateCache)
    """

    # useSWRMutation pattern (v2+)
    USE_SWR_MUTATION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'useSWRMutation\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Optimistic update pattern: mutate(..., { optimisticData: ... })
    OPTIMISTIC_PATTERN = re.compile(
        r'mutate\s*\([^)]*optimisticData\s*:',
        re.MULTILINE | re.DOTALL
    )

    # Bound mutate with data: mutate(newData, false) or mutate(data, { revalidate: false })
    BOUND_MUTATE_WITH_DATA_PATTERN = re.compile(
        r'mutate\s*\(\s*(?![\'\"`/\[])(\w+|(?:async\s*)?\([^)]*\)\s*=>|[^,{)]+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all SWR mutation patterns from source code."""
        result: Dict[str, Any] = {
            'mutation_hooks': [],
            'optimistic_updates': [],
        }

        # Extract useSWRMutation (v2+)
        for match in self.USE_SWR_MUTATION_PATTERN.finditer(content):
            var_name = match.group(1).strip('{}').strip().split(',')[0].strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()]

            ctx_start = match.start()
            ctx_end = min(len(content), ctx_start + 1000)
            context = content[ctx_start:ctx_end]

            mutation = SWRMutationHookInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            )

            # Extract key
            key_match = re.search(
                r'useSWRMutation\s*(?:<[^>]*>)?\s*\(\s*'
                r'([\'"`][^\'"`]*[\'"`]|\[[^\]]*\]|\w+)',
                context
            )
            if key_match:
                mutation.key = key_match.group(1).strip()

            # Extract mutation function
            mf_match = re.search(
                r'useSWRMutation\s*(?:<[^>]*>)?\s*\([^,]+,\s*(\w+|(?:async\s*)?\([^)]*\)\s*=>)',
                context
            )
            if mf_match:
                mutation.mutation_fn = mf_match.group(1).strip()

            # Detect options
            if re.search(r'\boptimisticData\s*:', context):
                mutation.has_optimistic_data = True
            if re.search(r'\brollbackOnError\s*:', context):
                mutation.has_rollback_on_error = True
            if re.search(r'\bpopulateCache\s*:', context):
                mutation.has_populate_cache = True
            if re.search(r'\brevalidate\s*:', context):
                mutation.has_revalidate = True
            if re.search(r'\bonSuccess\s*:', context):
                mutation.has_on_success = True
            if re.search(r'\bonError\s*:', context):
                mutation.has_on_error = True
            if re.search(r'\bthrowOnError\s*:', context):
                mutation.has_throw_on_error = True

            result['mutation_hooks'].append(mutation)

        # Detect optimistic update patterns
        for match in self.OPTIMISTIC_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = max(0, match.start() - 200)
            ctx_end = min(len(content), match.end() + 300)
            context = content[ctx_start:ctx_end]

            has_rollback = bool(re.search(r'rollbackOnError', context))

            # Determine pattern type
            pattern_type = 'global_mutate'
            if re.search(r'useSWRMutation', context):
                pattern_type = 'useSWRMutation'
            elif re.search(r'\}\s*=\s*useSWR', content[max(0, match.start() - 500):match.start()]):
                pattern_type = 'bound_mutate'

            result['optimistic_updates'].append(SWROptimisticUpdateInfo(
                file=file_path,
                line_number=line_num,
                has_rollback=has_rollback,
                pattern_type=pattern_type,
            ))

        return result
