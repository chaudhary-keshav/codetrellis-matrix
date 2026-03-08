"""
EF Core Query/Interceptor Extractor.

Extracts query filters, interceptors, compiled queries, and raw SQL usage.

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EFCoreQueryFilterInfo:
    """Information about an EF Core global query filter."""
    entity_name: str = ""
    filter_expression: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EFCoreInterceptorInfo:
    """Information about an EF Core interceptor."""
    name: str = ""
    kind: str = ""  # DbCommandInterceptor, SaveChangesInterceptor, ConnectionInterceptor
    base_class: str = ""
    methods_overridden: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class EFCoreQueryExtractor:
    """Extracts EF Core query patterns and interceptors."""

    # Query filter
    QUERY_FILTER_PATTERN = re.compile(
        r'\.HasQueryFilter\s*\(\s*(\w+)\s*=>\s*([^)]+)\)',
        re.MULTILINE
    )

    # Compiled queries
    COMPILED_QUERY_PATTERN = re.compile(
        r'EF\.CompileQuery\s*<\s*([^>]+)\s*>\s*\(',
        re.MULTILINE
    )
    COMPILED_ASYNC_QUERY_PATTERN = re.compile(
        r'EF\.CompileAsyncQuery\s*<\s*([^>]+)\s*>\s*\(',
        re.MULTILINE
    )

    # Raw SQL usage
    RAW_SQL_PATTERN = re.compile(
        r'\.(?:FromSqlRaw|FromSqlInterpolated|ExecuteSqlRaw|ExecuteSqlInterpolated)\s*\(',
        re.MULTILINE
    )

    # Interceptor classes
    INTERCEPTOR_PATTERNS = {
        'DbCommandInterceptor': re.compile(
            r'class\s+(\w+)\s*:\s*(?:DbCommandInterceptor|IDbCommandInterceptor)',
            re.MULTILINE
        ),
        'SaveChangesInterceptor': re.compile(
            r'class\s+(\w+)\s*:\s*(?:SaveChangesInterceptor|ISaveChangesInterceptor)',
            re.MULTILINE
        ),
        'ConnectionInterceptor': re.compile(
            r'class\s+(\w+)\s*:\s*(?:DbConnectionInterceptor|IDbConnectionInterceptor)',
            re.MULTILINE
        ),
        'TransactionInterceptor': re.compile(
            r'class\s+(\w+)\s*:\s*(?:DbTransactionInterceptor|IDbTransactionInterceptor)',
            re.MULTILINE
        ),
    }

    # Interceptor method overrides
    INTERCEPTOR_METHOD_PATTERN = re.compile(
        r'public\s+override\s+\w+\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # No-tracking queries
    NO_TRACKING_PATTERN = re.compile(r'\.AsNoTracking\s*\(\s*\)', re.MULTILINE)
    NO_TRACKING_IDENTITY_PATTERN = re.compile(r'\.AsNoTrackingWithIdentityResolution\s*\(\s*\)', re.MULTILINE)

    # Split query
    SPLIT_QUERY_PATTERN = re.compile(r'\.AsSplitQuery\s*\(\s*\)', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract query patterns and interceptors."""
        result = {
            'query_filters': [],
            'interceptors': [],
            'compiled_queries': 0,
            'raw_sql_count': 0,
            'uses_no_tracking': False,
            'uses_split_query': False,
        }

        if not content or not content.strip():
            return result

        # Query filters
        for match in self.QUERY_FILTER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['query_filters'].append(EFCoreQueryFilterInfo(
                entity_name=match.group(1),
                filter_expression=match.group(2).strip()[:100],
                file=file_path,
                line_number=line,
            ))

        # Interceptors
        for kind, pattern in self.INTERCEPTOR_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1

                # Find overridden methods
                methods = [m.group(1) for m in self.INTERCEPTOR_METHOD_PATTERN.finditer(content)]

                result['interceptors'].append(EFCoreInterceptorInfo(
                    name=name,
                    kind=kind,
                    base_class=kind,
                    methods_overridden=methods[:10],
                    file=file_path,
                    line_number=line,
                ))

        # Compiled queries
        result['compiled_queries'] = (
            len(self.COMPILED_QUERY_PATTERN.findall(content)) +
            len(self.COMPILED_ASYNC_QUERY_PATTERN.findall(content))
        )

        # Raw SQL
        result['raw_sql_count'] = len(self.RAW_SQL_PATTERN.findall(content))

        # Query hints
        result['uses_no_tracking'] = bool(
            self.NO_TRACKING_PATTERN.search(content) or
            self.NO_TRACKING_IDENTITY_PATTERN.search(content)
        )
        result['uses_split_query'] = bool(self.SPLIT_QUERY_PATTERN.search(content))

        return result
