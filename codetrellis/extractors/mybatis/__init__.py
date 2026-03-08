"""
MyBatis extractors for CodeTrellis.

Provides specialized extractors for MyBatis ORM:
- Mapper: @Mapper interfaces, @Select/@Insert/@Update/@Delete annotations
- SQL: SQL provider classes, @SelectProvider, dynamic SQL builders
- DynamicSQL: <if>, <choose>, <foreach>, <where>, <set>, <trim> in XML
- ResultMap: @Results, @ResultMap, type handlers, discriminators
- Cache: @CacheNamespace, L2 cache, custom cache implementations
"""

from .mapper_extractor import (
    MyBatisMapperExtractor,
    MyBatisMapperInfo,
    MyBatisMethodInfo,
)
from .sql_extractor import (
    MyBatisSQLExtractor,
    MyBatisSQLProviderInfo,
    MyBatisSQLFragmentInfo,
)
from .dynamic_sql_extractor import (
    MyBatisDynamicSQLExtractor,
    MyBatisDynamicSQLInfo,
    MyBatisXMLMapperInfo,
)
from .result_map_extractor import (
    MyBatisResultMapExtractor,
    MyBatisResultMapInfo,
    MyBatisTypeHandlerInfo,
)
from .cache_extractor import (
    MyBatisCacheExtractor,
    MyBatisCacheInfo,
    MyBatisConfigInfo,
)

__all__ = [
    # Mapper
    'MyBatisMapperExtractor', 'MyBatisMapperInfo', 'MyBatisMethodInfo',
    # SQL
    'MyBatisSQLExtractor', 'MyBatisSQLProviderInfo', 'MyBatisSQLFragmentInfo',
    # Dynamic SQL
    'MyBatisDynamicSQLExtractor', 'MyBatisDynamicSQLInfo', 'MyBatisXMLMapperInfo',
    # Result Map
    'MyBatisResultMapExtractor', 'MyBatisResultMapInfo', 'MyBatisTypeHandlerInfo',
    # Cache
    'MyBatisCacheExtractor', 'MyBatisCacheInfo', 'MyBatisConfigInfo',
]
