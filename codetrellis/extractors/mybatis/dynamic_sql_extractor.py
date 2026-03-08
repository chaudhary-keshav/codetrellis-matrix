"""
MyBatis Dynamic SQL Extractor - Extracts dynamic SQL elements from XML mappers.

Extracts:
- XML mapper files: <mapper>, <select>, <insert>, <update>, <delete>
- Dynamic SQL tags: <if>, <choose>, <when>, <otherwise>, <foreach>
- SQL building tags: <where>, <set>, <trim>
- SQL fragments: <sql>, <include>
- Parameter mapping: #{param}, ${param}
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MyBatisDynamicSQLInfo:
    """Information about dynamic SQL usage."""
    element_type: str = ""  # if, choose, foreach, where, set, trim, bind
    test_expression: str = ""  # for <if test="...">
    collection: str = ""  # for <foreach collection="...">
    item: str = ""
    separator: str = ""
    parent_statement: str = ""
    line_number: int = 0


@dataclass
class MyBatisXMLMapperInfo:
    """Information about an XML mapper file."""
    namespace: str = ""
    statements: List[Dict[str, str]] = field(default_factory=list)
    sql_fragments: List[Dict[str, str]] = field(default_factory=list)
    result_maps: List[str] = field(default_factory=list)
    dynamic_elements: List[MyBatisDynamicSQLInfo] = field(default_factory=list)
    parameter_maps: List[str] = field(default_factory=list)
    line_number: int = 0


class MyBatisDynamicSQLExtractor:
    """Extracts dynamic SQL elements from MyBatis XML and annotation-based mappers."""

    # XML mapper namespace
    MAPPER_NAMESPACE_PATTERN = re.compile(
        r'<mapper\s+namespace\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # SQL statements in XML
    SELECT_STATEMENT_PATTERN = re.compile(
        r'<select\s+id\s*=\s*["\'](\w+)["\']'
        r'(?:\s+resultType\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+resultMap\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+parameterType\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    INSERT_STATEMENT_PATTERN = re.compile(
        r'<insert\s+id\s*=\s*["\'](\w+)["\']'
        r'(?:\s+parameterType\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+useGeneratedKeys\s*=\s*["\'](\w+)["\'])?'
        r'(?:\s+keyProperty\s*=\s*["\'](\w+)["\'])?',
        re.DOTALL
    )

    UPDATE_STATEMENT_PATTERN = re.compile(
        r'<update\s+id\s*=\s*["\'](\w+)["\']'
        r'(?:\s+parameterType\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    DELETE_STATEMENT_PATTERN = re.compile(
        r'<delete\s+id\s*=\s*["\'](\w+)["\']'
        r'(?:\s+parameterType\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    # Dynamic SQL elements
    IF_PATTERN = re.compile(
        r'<if\s+test\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    CHOOSE_PATTERN = re.compile(
        r'<choose\s*>',
        re.MULTILINE
    )

    WHEN_PATTERN = re.compile(
        r'<when\s+test\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    FOREACH_PATTERN = re.compile(
        r'<foreach\s+'
        r'(?:.*?collection\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?item\s*=\s*["\'](\w+)["\'])?'
        r'(?:.*?separator\s*=\s*["\']([^"\']*)["\'])?',
        re.DOTALL
    )

    WHERE_PATTERN = re.compile(r'<where\s*>', re.MULTILINE)
    SET_PATTERN = re.compile(r'<set\s*>', re.MULTILINE)

    TRIM_PATTERN = re.compile(
        r'<trim\s+'
        r'(?:prefix\s*=\s*["\']([^"\']*)["\'])?'
        r'(?:\s+prefixOverrides\s*=\s*["\']([^"\']*)["\'])?'
        r'(?:\s+suffix\s*=\s*["\']([^"\']*)["\'])?'
        r'(?:\s+suffixOverrides\s*=\s*["\']([^"\']*)["\'])?',
        re.DOTALL
    )

    BIND_PATTERN = re.compile(
        r'<bind\s+name\s*=\s*["\'](\w+)["\']'
        r'\s+value\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # SQL fragments
    SQL_FRAGMENT_PATTERN = re.compile(
        r'<sql\s+id\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    INCLUDE_PATTERN = re.compile(
        r'<include\s+refid\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Parameter references
    PARAM_HASH_PATTERN = re.compile(r'#\{(\w+(?:\.\w+)?)\}')
    PARAM_DOLLAR_PATTERN = re.compile(r'\$\{(\w+(?:\.\w+)?)\}')

    # Result map in XML
    RESULT_MAP_XML_PATTERN = re.compile(
        r'<resultMap\s+id\s*=\s*["\'](\w+)["\']'
        r'\s+type\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract dynamic SQL elements."""
        xml_mappers: List[MyBatisXMLMapperInfo] = []
        dynamic_elements: List[MyBatisDynamicSQLInfo] = []
        parameter_refs: List[str] = []
        dollar_refs: List[str] = []

        if not content or not content.strip():
            return {
                'xml_mappers': xml_mappers,
                'dynamic_elements': dynamic_elements,
                'parameter_refs': parameter_refs,
                'dollar_refs': dollar_refs,
            }

        # Detect XML mapper
        ns_match = self.MAPPER_NAMESPACE_PATTERN.search(content)
        if ns_match:
            mapper_info = MyBatisXMLMapperInfo(
                namespace=ns_match.group(1),
                line_number=content[:ns_match.start()].count('\n') + 1,
            )

            # Extract statements
            for match in self.SELECT_STATEMENT_PATTERN.finditer(content):
                stmt = {
                    'id': match.group(1),
                    'type': 'select',
                    'result_type': match.group(2) or "",
                    'result_map': match.group(3) or "",
                    'parameter_type': match.group(4) or "",
                }
                mapper_info.statements.append(stmt)

            for match in self.INSERT_STATEMENT_PATTERN.finditer(content):
                stmt = {
                    'id': match.group(1),
                    'type': 'insert',
                    'parameter_type': match.group(2) or "",
                    'use_generated_keys': match.group(3) or "",
                    'key_property': match.group(4) or "",
                }
                mapper_info.statements.append(stmt)

            for match in self.UPDATE_STATEMENT_PATTERN.finditer(content):
                stmt = {
                    'id': match.group(1),
                    'type': 'update',
                    'parameter_type': match.group(2) or "",
                }
                mapper_info.statements.append(stmt)

            for match in self.DELETE_STATEMENT_PATTERN.finditer(content):
                stmt = {
                    'id': match.group(1),
                    'type': 'delete',
                    'parameter_type': match.group(2) or "",
                }
                mapper_info.statements.append(stmt)

            # SQL fragments
            for match in self.SQL_FRAGMENT_PATTERN.finditer(content):
                mapper_info.sql_fragments.append({'id': match.group(1)})

            # Result maps
            for match in self.RESULT_MAP_XML_PATTERN.finditer(content):
                mapper_info.result_maps.append(match.group(1))

            xml_mappers.append(mapper_info)

        # Dynamic SQL elements
        for match in self.IF_PATTERN.finditer(content):
            dynamic_elements.append(MyBatisDynamicSQLInfo(
                element_type='if',
                test_expression=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.FOREACH_PATTERN.finditer(content):
            dynamic_elements.append(MyBatisDynamicSQLInfo(
                element_type='foreach',
                collection=match.group(1) or "",
                item=match.group(2) or "",
                separator=match.group(3) or "",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.WHEN_PATTERN.finditer(content):
            dynamic_elements.append(MyBatisDynamicSQLInfo(
                element_type='when',
                test_expression=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for _ in self.WHERE_PATTERN.finditer(content):
            dynamic_elements.append(MyBatisDynamicSQLInfo(element_type='where'))

        for _ in self.SET_PATTERN.finditer(content):
            dynamic_elements.append(MyBatisDynamicSQLInfo(element_type='set'))

        # Parameter refs
        for match in self.PARAM_HASH_PATTERN.finditer(content):
            parameter_refs.append(match.group(1))

        for match in self.PARAM_DOLLAR_PATTERN.finditer(content):
            dollar_refs.append(match.group(1))

        return {
            'xml_mappers': xml_mappers,
            'dynamic_elements': dynamic_elements,
            'parameter_refs': parameter_refs,
            'dollar_refs': dollar_refs,
        }
