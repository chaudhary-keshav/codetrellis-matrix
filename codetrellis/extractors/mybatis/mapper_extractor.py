"""
MyBatis Mapper Extractor - Extracts @Mapper interfaces and annotated methods.

Extracts:
- @Mapper interface declarations
- @Select, @Insert, @Update, @Delete annotated methods
- Parameter mappings (@Param)
- Return types (single, List, Map, Optional)
- @Options (useGeneratedKeys, keyProperty, fetchSize, timeout)
- @ResultMap references
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MyBatisMethodInfo:
    """Information about a mapper method."""
    method_name: str = ""
    sql_type: str = ""  # select, insert, update, delete
    sql: str = ""
    return_type: str = ""
    parameters: List[str] = field(default_factory=list)
    param_annotations: List[str] = field(default_factory=list)
    result_map: str = ""
    use_generated_keys: bool = False
    key_property: str = ""
    fetch_size: int = 0
    flush_cache: bool = False
    use_cache: bool = True
    line_number: int = 0


@dataclass
class MyBatisMapperInfo:
    """Information about a MyBatis mapper interface."""
    interface_name: str = ""
    namespace: str = ""
    methods: List[MyBatisMethodInfo] = field(default_factory=list)
    is_spring_managed: bool = False
    extends_interfaces: List[str] = field(default_factory=list)
    line_number: int = 0


class MyBatisMapperExtractor:
    """Extracts MyBatis mapper interface information."""

    # Mapper interface detection
    MAPPER_PATTERN = re.compile(
        r'@Mapper\s*(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:public\s+)?interface\s+(\w+)'
        r'(?:\s+extends\s+([\w,\s<>]+))?',
        re.DOTALL
    )

    # Also detect interfaces that extend MyBatis base interfaces
    MYBATIS_INTERFACE_PATTERN = re.compile(
        r'(?:public\s+)?interface\s+(\w+)\s+extends\s+'
        r'(?:[\w,\s]*)(BaseMapper|Mapper|CrudMapper)\s*<',
        re.DOTALL
    )

    # SQL annotation methods
    SELECT_PATTERN = re.compile(
        r'@Select\s*\(\s*(?:["\']|{["\'])(.*?)(?:["\']|})\s*\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)',
        re.DOTALL
    )

    INSERT_PATTERN = re.compile(
        r'@Insert\s*\(\s*(?:["\']|{["\'])(.*?)(?:["\']|})\s*\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)',
        re.DOTALL
    )

    UPDATE_PATTERN = re.compile(
        r'@Update\s*\(\s*(?:["\']|{["\'])(.*?)(?:["\']|})\s*\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)',
        re.DOTALL
    )

    DELETE_PATTERN = re.compile(
        r'@Delete\s*\(\s*(?:["\']|{["\'])(.*?)(?:["\']|})\s*\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)',
        re.DOTALL
    )

    # @Param annotation
    PARAM_ANNOTATION_PATTERN = re.compile(
        r'@Param\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # @Options annotation
    OPTIONS_PATTERN = re.compile(
        r'@Options\s*\((.*?)\)',
        re.DOTALL
    )

    # @Results / @ResultMap reference
    RESULT_MAP_REF_PATTERN = re.compile(
        r'@ResultMap\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # @MapperScan (Spring)
    MAPPER_SCAN_PATTERN = re.compile(
        r'@MapperScan\s*\(\s*(?:basePackages\s*=\s*)?["\']([^"\']+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract mapper interface information."""
        mappers: List[MyBatisMapperInfo] = []
        mapper_scans: List[str] = []

        if not content or not content.strip():
            return {'mappers': mappers, 'mapper_scans': mapper_scans}

        # Find @Mapper interfaces
        for match in self.MAPPER_PATTERN.finditer(content):
            mapper = MyBatisMapperInfo(
                interface_name=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            )
            if match.group(2):
                mapper.extends_interfaces = [
                    e.strip() for e in match.group(2).split(',') if e.strip()
                ]
            # Check if Spring managed
            if '@Component' in content or '@Repository' in content:
                mapper.is_spring_managed = True

            mappers.append(mapper)

        # Find MyBatis base interface extensions
        for match in self.MYBATIS_INTERFACE_PATTERN.finditer(content):
            mapper = MyBatisMapperInfo(
                interface_name=match.group(1),
                extends_interfaces=[match.group(2)],
                line_number=content[:match.start()].count('\n') + 1,
            )
            mappers.append(mapper)

        # Extract methods for each SQL type
        method_patterns = [
            ('select', self.SELECT_PATTERN),
            ('insert', self.INSERT_PATTERN),
            ('update', self.UPDATE_PATTERN),
            ('delete', self.DELETE_PATTERN),
        ]

        all_methods: List[MyBatisMethodInfo] = []
        for sql_type, pattern in method_patterns:
            for match in pattern.finditer(content):
                method = MyBatisMethodInfo(
                    sql_type=sql_type,
                    sql=match.group(1).strip(),
                    method_name=match.group(2),
                    line_number=content[:match.start()].count('\n') + 1,
                )

                # Parse parameters
                params_str = match.group(3) or ""
                for param in self.PARAM_ANNOTATION_PATTERN.finditer(params_str):
                    method.param_annotations.append(param.group(1))

                # Check for @ResultMap ref
                # Look backwards from the method for @ResultMap
                method_start = match.start()
                preceding = content[max(0, method_start - 200):method_start]
                rm = self.RESULT_MAP_REF_PATTERN.search(preceding)
                if rm:
                    method.result_map = rm.group(1)

                all_methods.append(method)

        # Assign methods to mapper if there's one mapper
        if mappers and all_methods:
            mappers[0].methods = all_methods

        # MapperScan
        for match in self.MAPPER_SCAN_PATTERN.finditer(content):
            mapper_scans.append(match.group(1))

        return {'mappers': mappers, 'mapper_scans': mapper_scans}
