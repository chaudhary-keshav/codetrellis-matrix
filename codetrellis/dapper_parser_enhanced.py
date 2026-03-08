"""
Enhanced Dapper Parser for CodeTrellis.

Extracts Dapper-specific concepts: queries, repositories, type handlers,
multi-mapping, stored procedures, Dapper.Contrib usage.

Supports Dapper 2.x, Dapper.Contrib, Dapper.FluentMap.
Part of CodeTrellis v4.96 (Session 76)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetrellis.extractors.dapper import DapperQueryExtractor


@dataclass
class DapperParseResult:
    """Result of Dapper-enhanced parsing."""
    # Queries
    queries: List[Dict[str, Any]] = field(default_factory=list)

    # Repositories
    repositories: List[Dict[str, Any]] = field(default_factory=list)

    # Type handlers
    type_handlers: List[Dict[str, Any]] = field(default_factory=list)

    # Multi-mapping
    multi_mappings: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregates
    total_queries: int = 0
    total_async_queries: int = 0
    total_stored_procs: int = 0
    total_repositories: int = 0

    # Framework metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_version: str = ""
    file_type: str = ""  # repository, data-access, type-handler, usage


class EnhancedDapperParser:
    """Parser for Dapper concepts in C# files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core
        'dapper': r'using\s+Dapper\b',
        'dapper_contrib': r'using\s+Dapper\.Contrib\b',
        'dapper_fluent_map': r'using\s+Dapper\.FluentMap\b',
        'dapper_simplerCRUD': r'using\s+Dapper\.SimpleCRUD\b',

        # Query patterns
        'query': r'\.\s*Query(?:Async)?\s*<',
        'query_first': r'\.\s*QueryFirst(?:OrDefault)?(?:Async)?\s*<',
        'query_single': r'\.\s*QuerySingle(?:OrDefault)?(?:Async)?\s*<',
        'execute': r'\.\s*Execute(?:Async)?\s*\(',
        'execute_scalar': r'\.\s*ExecuteScalar(?:Async)?\s*(?:<\s*\w+\s*>)?\s*\(',
        'query_multiple': r'\.\s*QueryMultiple(?:Async)?\s*\(',

        # Advanced
        'multi_mapping': r'\.\s*Query(?:Async)?\s*<\s*\w+\s*,\s*\w+',
        'type_handler': r'\bSqlMapper\.TypeHandler\b',
        'dynamic_params': r'\bDynamicParameters\b',
        'stored_procedure': r'\bCommandType\s*\.\s*StoredProcedure\b',

        # Contrib
        'contrib_get': r'\.\s*Get(?:All)?\s*<',
        'contrib_insert': r'\.\s*Insert\s*<',
        'contrib_update': r'\.\s*Update\s*<',
        'contrib_delete': r'\.\s*Delete(?:All)?\s*<',

        # Table attribute (contrib)
        'table_attribute': r'\[Table\s*\(',
    }

    VERSION_FEATURES: Dict[str, List[str]] = {
        '2.0': ['Query', 'Execute', 'QueryMultiple', 'DynamicParameters'],
        '2.0.35': ['QueryAsync', 'ExecuteAsync', 'Buffered'],
        '2.1': ['GetRowParser', 'GetTypeDeserializer'],
    }

    def __init__(self):
        """Initialize extractors."""
        self.query_extractor = DapperQueryExtractor()

    def is_dapper_file(self, content: str, file_path: str = "") -> bool:
        """Check if file contains Dapper code."""
        if not content:
            return False
        indicators = [
            r'using\s+Dapper\b',
            r'\.\s*Query(?:Async)?\s*<',
            r'\.\s*Execute(?:Async)?\s*\(',
            r'\.\s*QueryMultiple(?:Async)?\s*\(',
            r'\bSqlMapper\b',
            r'\bDynamicParameters\b',
            r'using\s+Dapper\.Contrib\b',
        ]
        return any(re.search(p, content) for p in indicators)

    def parse(self, content: str, file_path: str = "") -> DapperParseResult:
        """Parse Dapper concepts from C# file."""
        result = DapperParseResult()

        if not content or not self.is_dapper_file(content, file_path):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_version = self._detect_version(content)
        result.file_type = self._classify_file(content, file_path)

        # Extract
        data = self.query_extractor.extract(content, file_path)

        result.queries = [self._query_to_dict(q) for q in data.get('queries', [])]
        result.repositories = [self._repo_to_dict(r) for r in data.get('repositories', [])]
        result.type_handlers = [self._handler_to_dict(h) for h in data.get('type_handlers', [])]
        result.multi_mappings = [self._mm_to_dict(m) for m in data.get('multi_mappings', [])]

        # Aggregates
        result.total_queries = len(result.queries)
        result.total_async_queries = sum(1 for q in result.queries if q.get('is_async'))
        result.total_stored_procs = sum(1 for q in result.queries if q.get('is_stored_procedure'))
        result.total_repositories = len(result.repositories)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Dapper-related frameworks."""
        found = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if re.search(pattern, content):
                found.append(name)
        return found

    def _detect_version(self, content: str) -> str:
        """Detect Dapper version from usage patterns."""
        if re.search(r'Async\s*[<(]', content):
            return "2.0.35"
        return "2.0"

    def _classify_file(self, content: str, file_path: str) -> str:
        """Classify file type."""
        path_lower = file_path.lower()
        if 'repository' in path_lower or 'repo' in path_lower:
            return "repository"
        if re.search(r'class\s+\w+\s*:\s*SqlMapper\.TypeHandler', content):
            return "type-handler"
        if re.search(r'class\s+\w+(?:Repository|Repo)\b', content):
            return "repository"
        return "data-access"

    def _query_to_dict(self, q) -> Dict[str, Any]:
        return {
            'method_name': q.method_name, 'query_type': q.query_type,
            'return_type': q.return_type, 'is_async': q.is_async,
            'is_stored_procedure': q.is_stored_procedure,
            'has_transaction': q.has_transaction,
            'file': q.file, 'line': q.line_number,
        }

    def _repo_to_dict(self, r) -> Dict[str, Any]:
        return {
            'name': r.name, 'interface_name': r.interface_name,
            'connection_type': r.connection_type, 'query_count': r.query_count,
            'file': r.file, 'line': r.line_number,
        }

    def _handler_to_dict(self, h) -> Dict[str, Any]:
        return {
            'name': h.name, 'handled_type': h.handled_type,
            'file': h.file, 'line': h.line_number,
        }

    def _mm_to_dict(self, m) -> Dict[str, Any]:
        return {
            'types': m.types, 'return_type': m.return_type,
            'split_on': m.split_on,
            'file': m.file, 'line': m.line_number,
        }
