"""
MyBatis Result Map Extractor - Extracts @Results, result maps, type handlers.

Extracts:
- @Results annotation with @Result mappings
- @ResultMap references
- @TypeDiscriminator annotations
- TypeHandler implementations
- @MappedTypes and @MappedJdbcTypes
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MyBatisResultMapInfo:
    """Information about a result mapping."""
    id: str = ""
    result_type: str = ""
    columns: List[Dict[str, str]] = field(default_factory=list)
    associations: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)
    discriminator_column: str = ""
    has_auto_mapping: bool = False
    extends_map: str = ""
    line_number: int = 0


@dataclass
class MyBatisTypeHandlerInfo:
    """Information about a custom type handler."""
    class_name: str = ""
    java_type: str = ""
    jdbc_type: str = ""
    mapped_types: List[str] = field(default_factory=list)
    mapped_jdbc_types: List[str] = field(default_factory=list)
    line_number: int = 0


class MyBatisResultMapExtractor:
    """Extracts result mapping and type handler information."""

    # @Results annotation
    RESULTS_PATTERN = re.compile(
        r'@Results\s*\(\s*(?:id\s*=\s*["\'](\w+)["\'])?\s*(?:,\s*)?'
        r'(?:value\s*=\s*)?\{(.*?)\}\s*\)',
        re.DOTALL
    )

    # Individual @Result
    RESULT_PATTERN = re.compile(
        r'@Result\s*\(\s*'
        r'(?:.*?column\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?property\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?javaType\s*=\s*(\w+)\.class)?'
        r'(?:.*?jdbcType\s*=\s*JdbcType\.(\w+))?'
        r'(?:.*?id\s*=\s*(true|false))?'
        r'(?:.*?typeHandler\s*=\s*(\w+)\.class)?',
        re.DOTALL
    )

    # @ConstructorArgs
    CONSTRUCTOR_ARGS_PATTERN = re.compile(
        r'@ConstructorArgs\s*\(\s*\{(.*?)\}\s*\)',
        re.DOTALL
    )

    # @TypeDiscriminator
    TYPE_DISCRIMINATOR_PATTERN = re.compile(
        r'@TypeDiscriminator\s*\(\s*'
        r'column\s*=\s*["\'](\w+)["\']'
        r'(?:.*?javaType\s*=\s*(\w+)\.class)?',
        re.DOTALL
    )

    # TypeHandler class
    TYPE_HANDLER_PATTERN = re.compile(
        r'(?:@MappedTypes\s*\(\s*\{?\s*([\w.,\s]+)\s*\.class\s*\}?\s*\)\s*)?'
        r'(?:@MappedJdbcTypes\s*\(\s*\{?\s*([\w.,\s]+)\s*\}?\s*\)\s*)?'
        r'(?:public\s+)?class\s+(\w+)\s+'
        r'(?:extends\s+(?:BaseTypeHandler|TypeReference)\s*<\s*(\w+)\s*>|'
        r'implements\s+TypeHandler\s*<\s*(\w+)\s*>)',
        re.DOTALL
    )

    # XML result map association/collection
    ASSOCIATION_PATTERN = re.compile(
        r'<association\s+property\s*=\s*["\'](\w+)["\']'
        r'(?:\s+javaType\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+select\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    COLLECTION_PATTERN = re.compile(
        r'<collection\s+property\s*=\s*["\'](\w+)["\']'
        r'(?:\s+ofType\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+select\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    # Auto-mapping hint
    AUTO_MAPPING_PATTERN = re.compile(
        r'autoMapping\s*=\s*["\']?(true|false)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract result mapping and type handler information."""
        result_maps: List[MyBatisResultMapInfo] = []
        type_handlers: List[MyBatisTypeHandlerInfo] = []

        if not content or not content.strip():
            return {'result_maps': result_maps, 'type_handlers': type_handlers}

        # @Results annotations
        for match in self.RESULTS_PATTERN.finditer(content):
            rm = MyBatisResultMapInfo(
                id=match.group(1) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Parse individual @Result entries
            results_body = match.group(2) or ""
            for r in self.RESULT_PATTERN.finditer(results_body):
                col_info = {
                    'column': r.group(1) or "",
                    'property': r.group(2) or "",
                    'java_type': r.group(3) or "",
                    'jdbc_type': r.group(4) or "",
                    'is_id': r.group(5) == 'true' if r.group(5) else False,
                }
                rm.columns.append(col_info)

            result_maps.append(rm)

        # XML associations
        for match in self.ASSOCIATION_PATTERN.finditer(content):
            # Find parent result map
            if result_maps:
                result_maps[-1].associations.append(match.group(1))

        # XML collections
        for match in self.COLLECTION_PATTERN.finditer(content):
            if result_maps:
                result_maps[-1].collections.append(match.group(1))

        # Type handlers
        for match in self.TYPE_HANDLER_PATTERN.finditer(content):
            handler = MyBatisTypeHandlerInfo(
                class_name=match.group(3) or "",
                java_type=match.group(4) or match.group(5) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Mapped types
            if match.group(1):
                handler.mapped_types = [
                    t.strip() for t in match.group(1).split(',') if t.strip()
                ]
            # Mapped JDBC types
            if match.group(2):
                handler.mapped_jdbc_types = [
                    t.strip() for t in match.group(2).split(',') if t.strip()
                ]

            type_handlers.append(handler)

        return {'result_maps': result_maps, 'type_handlers': type_handlers}
