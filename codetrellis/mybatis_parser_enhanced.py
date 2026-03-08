"""
EnhancedMyBatisParser v1.0 - Comprehensive MyBatis parser.

Supports:
- MyBatis 2.x (iBATIS legacy)
- MyBatis 3.x (annotation-based, XML mappers, dynamic SQL)
- MyBatis-Plus (enhanced CRUD, code generator, pagination)
- MyBatis-Spring / MyBatis-Spring-Boot

MyBatis-specific extraction:
- Mappers: @Mapper interfaces, @Select/@Insert/@Update/@Delete
- SQL: Providers, SQL builders, inline fragments
- Dynamic SQL: <if>, <choose>, <foreach>, <where>, <set>, <trim>
- Result maps: @Results, type handlers, discriminators
- Cache: @CacheNamespace, L2 cache, custom cache implementations

Framework detection (20+ MyBatis ecosystem patterns):
- Core: mybatis, mybatis-spring, mybatis-spring-boot-starter
- Plus: mybatis-plus, mybatis-plus-boot-starter
- Generator: mybatis-generator
- Cache: mybatis-ehcache, mybatis-redis, mybatis-hazelcast
- Pagehelper: pagehelper, pagehelper-spring-boot-starter

Part of CodeTrellis v4.95 - MyBatis Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .extractors.mybatis import (
    MyBatisMapperExtractor, MyBatisMapperInfo, MyBatisMethodInfo,
    MyBatisSQLExtractor, MyBatisSQLProviderInfo, MyBatisSQLFragmentInfo,
    MyBatisDynamicSQLExtractor, MyBatisDynamicSQLInfo, MyBatisXMLMapperInfo,
    MyBatisResultMapExtractor, MyBatisResultMapInfo, MyBatisTypeHandlerInfo,
    MyBatisCacheExtractor, MyBatisCacheInfo, MyBatisConfigInfo,
)


@dataclass
class MyBatisParseResult:
    """Complete parse result for a MyBatis file."""
    file_path: str
    file_type: str = "mybatis"

    # Mappers
    mappers: List[MyBatisMapperInfo] = field(default_factory=list)
    mapper_scans: List[str] = field(default_factory=list)

    # SQL
    sql_providers: List[MyBatisSQLProviderInfo] = field(default_factory=list)
    sql_fragments: List[MyBatisSQLFragmentInfo] = field(default_factory=list)
    has_script_annotations: bool = False

    # Dynamic SQL
    xml_mappers: List[MyBatisXMLMapperInfo] = field(default_factory=list)
    dynamic_elements: List[MyBatisDynamicSQLInfo] = field(default_factory=list)
    parameter_refs: List[str] = field(default_factory=list)

    # Result Maps
    result_maps: List[MyBatisResultMapInfo] = field(default_factory=list)
    type_handlers: List[MyBatisTypeHandlerInfo] = field(default_factory=list)

    # Cache
    caches: List[MyBatisCacheInfo] = field(default_factory=list)
    configs: List[MyBatisConfigInfo] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    is_mybatis_plus: bool = False

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    mybatis_version: str = ""
    total_mappers: int = 0
    total_statements: int = 0
    total_dynamic_elements: int = 0


class EnhancedMyBatisParser:
    """
    Enhanced MyBatis parser using all extractors for comprehensive parsing.

    Runs AFTER the Java parser when MyBatis framework is detected.
    Also handles XML mapper files.

    Supports MyBatis 2.x through 3.x + MyBatis-Plus.
    """

    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'mybatis_core': re.compile(
            r'import\s+org\.apache\.ibatis\b|'
            r'@Mapper|@Select|@Insert|@Update|@Delete|'
            r'SqlSession|SqlSessionFactory',
            re.MULTILINE
        ),
        'mybatis_annotations': re.compile(
            r'@SelectProvider|@InsertProvider|@UpdateProvider|@DeleteProvider|'
            r'@Results|@Result|@CacheNamespace|@Options',
            re.MULTILINE
        ),
        'mybatis_xml': re.compile(
            r'<mapper\s+namespace|<select\s+id|<insert\s+id|'
            r'<update\s+id|<delete\s+id|<resultMap\s+id',
            re.MULTILINE
        ),

        # ── Spring Integration ────────────────────────────────────
        'mybatis_spring': re.compile(
            r'import\s+org\.mybatis\.spring\b|'
            r'SqlSessionFactoryBean|MapperScannerConfigurer|'
            r'@MapperScan',
            re.MULTILINE
        ),
        'mybatis_spring_boot': re.compile(
            r'mybatis\.mapper-locations|mybatis\.type-aliases-package|'
            r'mybatis\.configuration\.',
            re.MULTILINE
        ),

        # ── MyBatis-Plus ──────────────────────────────────────────
        'mybatis_plus': re.compile(
            r'import\s+com\.baomidou\.mybatisplus\b|'
            r'@TableName|@TableId|@TableField|'
            r'IService|ServiceImpl|BaseMapper',
            re.MULTILINE
        ),
        'mybatis_plus_annotations': re.compile(
            r'@TableLogic|@Version|@EnumValue|@KeySequence|'
            r'@InterceptorIgnore|@OrderBy',
            re.MULTILINE
        ),

        # ── Cache ─────────────────────────────────────────────────
        'mybatis_ehcache': re.compile(
            r'org\.mybatis\.caches\.ehcache\b|EhcacheCache',
            re.MULTILINE
        ),
        'mybatis_redis': re.compile(
            r'org\.mybatis\.caches\.redis\b|RedisCache',
            re.MULTILINE
        ),
        'mybatis_hazelcast': re.compile(
            r'org\.mybatis\.caches\.hazelcast\b|HazelcastCache',
            re.MULTILINE
        ),

        # ── PageHelper ────────────────────────────────────────────
        'pagehelper': re.compile(
            r'import\s+com\.github\.pagehelper\b|'
            r'PageHelper\.startPage|PageInfo<',
            re.MULTILINE
        ),

        # ── Generator ─────────────────────────────────────────────
        'mybatis_generator': re.compile(
            r'import\s+org\.mybatis\.generator\b|'
            r'generatorConfiguration|'
            r'@Generated\s*\(\s*["\']org\.mybatis',
            re.MULTILINE
        ),

        # ── Dynamic SQL ───────────────────────────────────────────
        'mybatis_dynamic_sql': re.compile(
            r'import\s+org\.mybatis\.dynamic\.sql\b|'
            r'SqlBuilder|SelectDSL|InsertDSL',
            re.MULTILINE
        ),

        # ── iBATIS (legacy) ───────────────────────────────────────
        'ibatis_legacy': re.compile(
            r'import\s+com\.ibatis\b|'
            r'SqlMapClient|queryForList|queryForObject',
            re.MULTILINE
        ),
    }

    VERSION_INDICATORS = {
        '3.x': re.compile(
            r'import\s+org\.apache\.ibatis\b|'
            r'SqlSessionFactoryBuilder|'
            r'@Mapper'
        ),
        '2.x': re.compile(
            r'import\s+com\.ibatis\b|'
            r'SqlMapClient|'
            r'sqlMap\.xml'
        ),
    }

    def __init__(self):
        """Initialize the enhanced MyBatis parser with all extractors."""
        self.mapper_extractor = MyBatisMapperExtractor()
        self.sql_extractor = MyBatisSQLExtractor()
        self.dynamic_sql_extractor = MyBatisDynamicSQLExtractor()
        self.result_map_extractor = MyBatisResultMapExtractor()
        self.cache_extractor = MyBatisCacheExtractor()

    def is_mybatis_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains MyBatis code."""
        if not content:
            return False

        # Check XML mapper files
        if file_path.endswith('.xml'):
            if re.search(r'<mapper\s+namespace', content):
                return True
            if re.search(r'mybatis.*\.dtd|mybatis.*config', content):
                return True
            return False

        # Java files
        mybatis_patterns = [
            r'import\s+org\.apache\.ibatis\.',
            r'@Mapper',
            r'@Select\s*\(',
            r'@Insert\s*\(',
            r'@Update\s*\(',
            r'@Delete\s*\(',
            r'@SelectProvider\s*\(',
            r'@CacheNamespace',
            r'SqlSession\s+\w+',
            r'import\s+com\.baomidou\.mybatisplus\.',
            r'@TableName',
            r'BaseMapper\s*<',
        ]
        for pattern in mybatis_patterns:
            if re.search(pattern, content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> MyBatisParseResult:
        """Parse MyBatis source code and extract all mapping information."""
        result = MyBatisParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.mybatis_version = self._detect_version(content)

        # Run all extractors
        # Mappers
        mapper_result = self.mapper_extractor.extract(content, file_path)
        result.mappers = mapper_result.get('mappers', [])
        result.mapper_scans = mapper_result.get('mapper_scans', [])

        # SQL providers
        sql_result = self.sql_extractor.extract(content, file_path)
        result.sql_providers = sql_result.get('providers', [])
        result.sql_fragments = sql_result.get('fragments', [])
        result.has_script_annotations = sql_result.get('has_script_annotations', False)

        # Dynamic SQL
        dynamic_result = self.dynamic_sql_extractor.extract(content, file_path)
        result.xml_mappers = dynamic_result.get('xml_mappers', [])
        result.dynamic_elements = dynamic_result.get('dynamic_elements', [])
        result.parameter_refs = dynamic_result.get('parameter_refs', [])

        # Result maps
        rm_result = self.result_map_extractor.extract(content, file_path)
        result.result_maps = rm_result.get('result_maps', [])
        result.type_handlers = rm_result.get('type_handlers', [])

        # Cache
        cache_result = self.cache_extractor.extract(content, file_path)
        result.caches = cache_result.get('caches', [])
        result.configs = cache_result.get('configs', [])
        result.plugins = cache_result.get('plugins', [])
        result.is_mybatis_plus = cache_result.get('is_mybatis_plus', False)

        # Compute totals
        result.total_mappers = len(result.mappers)
        total_stmts = sum(len(m.methods) for m in result.mappers)
        total_stmts += sum(len(xm.statements) for xm in result.xml_mappers)
        result.total_statements = total_stmts
        result.total_dynamic_elements = len(result.dynamic_elements)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which MyBatis ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect MyBatis version from code patterns."""
        for version, pattern in self.VERSION_INDICATORS.items():
            if pattern.search(content):
                return version
        return ""
