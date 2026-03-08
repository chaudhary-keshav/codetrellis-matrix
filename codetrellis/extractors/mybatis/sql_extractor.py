"""
MyBatis SQL Extractor - Extracts SQL providers and SQL builder usage.

Extracts:
- @SelectProvider, @InsertProvider, @UpdateProvider, @DeleteProvider
- SQL builder class usage (SQL class)
- SqlBuilder patterns
- Inline SQL fragments
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MyBatisSQLProviderInfo:
    """Information about a SQL provider method."""
    provider_type: str = ""  # SelectProvider, InsertProvider, UpdateProvider, DeleteProvider
    type_class: str = ""
    method_name: str = ""
    mapper_method: str = ""
    line_number: int = 0


@dataclass
class MyBatisSQLFragmentInfo:
    """Information about an SQL builder/fragment usage."""
    builder_type: str = ""  # SQL, SQLBuilder, StringBuffer
    operations: List[str] = field(default_factory=list)  # SELECT, FROM, WHERE, JOIN, etc.
    tables: List[str] = field(default_factory=list)
    method_name: str = ""
    line_number: int = 0


class MyBatisSQLExtractor:
    """Extracts SQL provider and builder information."""

    # SQL Provider annotations
    SELECT_PROVIDER_PATTERN = re.compile(
        r'@SelectProvider\s*\(\s*'
        r'(?:type|value)\s*=\s*(\w+)\.class'
        r'(?:\s*,\s*method\s*=\s*["\'](\w+)["\'])?\s*\)\s*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        re.DOTALL
    )

    INSERT_PROVIDER_PATTERN = re.compile(
        r'@InsertProvider\s*\(\s*'
        r'(?:type|value)\s*=\s*(\w+)\.class'
        r'(?:\s*,\s*method\s*=\s*["\'](\w+)["\'])?\s*\)\s*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        re.DOTALL
    )

    UPDATE_PROVIDER_PATTERN = re.compile(
        r'@UpdateProvider\s*\(\s*'
        r'(?:type|value)\s*=\s*(\w+)\.class'
        r'(?:\s*,\s*method\s*=\s*["\'](\w+)["\'])?\s*\)\s*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        re.DOTALL
    )

    DELETE_PROVIDER_PATTERN = re.compile(
        r'@DeleteProvider\s*\(\s*'
        r'(?:type|value)\s*=\s*(\w+)\.class'
        r'(?:\s*,\s*method\s*=\s*["\'](\w+)["\'])?\s*\)\s*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
        re.DOTALL
    )

    # SQL builder class usage
    SQL_BUILDER_PATTERN = re.compile(
        r'new\s+SQL\s*\(\s*\)\s*(?:\{\{|\.)|\bSQL\s+\w+\s*=\s*new\s+SQL\b',
        re.MULTILINE
    )

    SQL_BUILDER_METHOD_PATTERN = re.compile(
        r'\.(?:SELECT|INSERT_INTO|UPDATE|DELETE_FROM|FROM|WHERE|AND|OR|'
        r'JOIN|INNER_JOIN|LEFT_OUTER_JOIN|RIGHT_OUTER_JOIN|'
        r'GROUP_BY|HAVING|ORDER_BY|LIMIT|OFFSET|'
        r'SET|VALUES|INTO_COLUMNS|INTO_VALUES)\s*\(\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    # Script annotation
    SCRIPT_PATTERN = re.compile(
        r'@(?:Select|Insert|Update|Delete)\s*\(\s*"<script>(.*?)</script>"\s*\)',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract SQL provider and builder information."""
        providers: List[MyBatisSQLProviderInfo] = []
        fragments: List[MyBatisSQLFragmentInfo] = []
        has_script_annotations = False

        if not content or not content.strip():
            return {
                'providers': providers,
                'fragments': fragments,
                'has_script_annotations': has_script_annotations,
            }

        # SQL Providers
        provider_patterns = [
            ('SelectProvider', self.SELECT_PROVIDER_PATTERN),
            ('InsertProvider', self.INSERT_PROVIDER_PATTERN),
            ('UpdateProvider', self.UPDATE_PROVIDER_PATTERN),
            ('DeleteProvider', self.DELETE_PROVIDER_PATTERN),
        ]

        for provider_type, pattern in provider_patterns:
            for match in pattern.finditer(content):
                provider = MyBatisSQLProviderInfo(
                    provider_type=provider_type,
                    type_class=match.group(1),
                    method_name=match.group(2) or "",
                    mapper_method=match.group(3) or "",
                    line_number=content[:match.start()].count('\n') + 1,
                )
                providers.append(provider)

        # SQL builder usage
        for match in self.SQL_BUILDER_PATTERN.finditer(content):
            frag = MyBatisSQLFragmentInfo(
                builder_type="SQL",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Find operations in the builder chain
            # Look at the surrounding context (next ~500 chars)
            context = content[match.start():match.start() + 500]
            for op in self.SQL_BUILDER_METHOD_PATTERN.finditer(context):
                frag.operations.append(op.group(0).split('(')[0].strip().lstrip('.'))
                table_ref = op.group(1)
                if table_ref and any(
                    op.group(0).startswith(f'.{kw}')
                    for kw in ['FROM', 'JOIN', 'INNER_JOIN', 'LEFT_OUTER_JOIN',
                               'RIGHT_OUTER_JOIN', 'INSERT_INTO', 'UPDATE', 'DELETE_FROM']
                ):
                    frag.tables.append(table_ref)

            fragments.append(frag)

        # Script annotations
        has_script_annotations = bool(self.SCRIPT_PATTERN.search(content))

        return {
            'providers': providers,
            'fragments': fragments,
            'has_script_annotations': has_script_annotations,
        }
