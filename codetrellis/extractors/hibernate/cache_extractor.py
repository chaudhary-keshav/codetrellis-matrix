"""
Hibernate Cache Extractor - Extracts L1/L2 cache and query cache configuration.

Extracts:
- L2 cache annotations (@Cacheable, @Cache)
- Cache concurrency strategies (READ_ONLY, READ_WRITE, NONSTRICT_READ_WRITE, TRANSACTIONAL)
- Cache regions and configuration
- Query cache usage
- Cache provider detection (EhCache, Infinispan, Hazelcast, Caffeine)
- Collection cache
- Natural ID cache
- Cache eviction strategies
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HibernateCacheRegionInfo:
    """Information about a cache region."""
    region_name: str = ""
    entity_class: str = ""
    concurrency_strategy: str = ""  # READ_ONLY, READ_WRITE, NONSTRICT_READ_WRITE, TRANSACTIONAL
    is_collection_cache: bool = False
    is_query_cache: bool = False
    is_natural_id_cache: bool = False
    line_number: int = 0


@dataclass
class HibernateCacheConfigInfo:
    """Information about cache configuration."""
    cache_provider: str = ""  # ehcache, infinispan, hazelcast, caffeine, redis
    l2_cache_enabled: bool = False
    query_cache_enabled: bool = False
    cache_mode: str = ""  # NORMAL, GET, PUT, REFRESH, IGNORE
    regions: List[HibernateCacheRegionInfo] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


class HibernateCacheExtractor:
    """Extracts Hibernate cache configuration and usage."""

    # L2 cache annotation
    CACHEABLE_PATTERN = re.compile(
        r'@(?:javax\.persistence\.)?Cacheable\s*(?:\(\s*(true|false)\s*\))?\s*'
        r'(?:@org\.hibernate\.annotations\.Cache\s*\(\s*'
        r'(?:usage\s*=\s*CacheConcurrencyStrategy\.(\w+))?'
        r'(?:.*?region\s*=\s*["\']([^"\']+)["\'])?'
        r'\s*\))?\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.DOTALL
    )

    # @Cache annotation standalone
    CACHE_ANNOTATION_PATTERN = re.compile(
        r'@Cache\s*\(\s*'
        r'(?:usage\s*=\s*CacheConcurrencyStrategy\.(\w+))?'
        r'(?:.*?region\s*=\s*["\']([^"\']+)["\'])?',
        re.DOTALL
    )

    # Collection cache
    COLLECTION_CACHE_PATTERN = re.compile(
        r'@Cache\s*\(\s*usage\s*=\s*CacheConcurrencyStrategy\.(\w+)\s*\)\s*'
        r'(?:@\w+(?:\(.*?\))?\s*)*'
        r'(?:private|protected)\s+(?:Set|List|Collection|Map)<',
        re.DOTALL
    )

    # Natural ID cache
    NATURAL_ID_CACHE_PATTERN = re.compile(
        r'@NaturalIdCache\s*(?:\(\s*region\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE
    )

    # Cache provider detection
    EHCACHE_PATTERN = re.compile(
        r'org\.hibernate\.cache\.ehcache|EhCacheRegionFactory|'
        r'net\.sf\.ehcache|org\.ehcache',
        re.MULTILINE
    )

    INFINISPAN_CACHE_PATTERN = re.compile(
        r'org\.hibernate\.cache\.infinispan|InfinispanRegionFactory',
        re.MULTILINE
    )

    HAZELCAST_CACHE_PATTERN = re.compile(
        r'com\.hazelcast\.hibernate|HazelcastCacheRegionFactory',
        re.MULTILINE
    )

    CAFFEINE_CACHE_PATTERN = re.compile(
        r'com\.github\.benmanes\.caffeine|CaffeineRegionFactory',
        re.MULTILINE
    )

    REDIS_CACHE_PATTERN = re.compile(
        r'org\.redisson\.hibernate|RedissonRegionFactory',
        re.MULTILINE
    )

    # Cache config properties
    L2_CACHE_ENABLED_PATTERN = re.compile(
        r'hibernate\.cache\.use_second_level_cache\s*[=:]\s*(true|false)|'
        r'setProperty\s*\(\s*["\']hibernate\.cache\.use_second_level_cache["\']'
        r'\s*,\s*["\']?(true|false)',
        re.MULTILINE
    )

    QUERY_CACHE_ENABLED_PATTERN = re.compile(
        r'hibernate\.cache\.use_query_cache\s*[=:]\s*(true|false)|'
        r'setProperty\s*\(\s*["\']hibernate\.cache\.use_query_cache["\']'
        r'\s*,\s*["\']?(true|false)',
        re.MULTILINE
    )

    # Query cache hint
    QUERY_CACHE_HINT_PATTERN = re.compile(
        r'\.setCacheable\s*\(\s*true\s*\)|'
        r'\.setHint\s*\(\s*["\']org\.hibernate\.cacheable["\']'
        r'\s*,\s*["\']?true',
        re.MULTILINE
    )

    # Query cache region
    QUERY_CACHE_REGION_PATTERN = re.compile(
        r'\.setCacheRegion\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Cache mode
    CACHE_MODE_PATTERN = re.compile(
        r'setCacheMode\s*\(\s*CacheMode\.(\w+)\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract cache configuration and usage."""
        cache_regions: List[HibernateCacheRegionInfo] = []
        cache_config = HibernateCacheConfigInfo()
        query_cache_regions: List[str] = []

        if not content or not content.strip():
            return {
                'cache_regions': cache_regions,
                'cache_config': cache_config,
                'query_cache_regions': query_cache_regions,
            }

        # L2 cache annotations
        for match in self.CACHEABLE_PATTERN.finditer(content):
            region = HibernateCacheRegionInfo(
                entity_class=match.group(4) or "",
                concurrency_strategy=match.group(2) or "",
                region_name=match.group(3) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            cache_regions.append(region)

        # Collection caches
        for match in self.COLLECTION_CACHE_PATTERN.finditer(content):
            region = HibernateCacheRegionInfo(
                concurrency_strategy=match.group(1) or "",
                is_collection_cache=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            cache_regions.append(region)

        # Natural ID caches
        for match in self.NATURAL_ID_CACHE_PATTERN.finditer(content):
            region = HibernateCacheRegionInfo(
                region_name=match.group(1) or "",
                is_natural_id_cache=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            cache_regions.append(region)

        # Detect cache provider
        if self.EHCACHE_PATTERN.search(content):
            cache_config.cache_provider = "ehcache"
        elif self.INFINISPAN_CACHE_PATTERN.search(content):
            cache_config.cache_provider = "infinispan"
        elif self.HAZELCAST_CACHE_PATTERN.search(content):
            cache_config.cache_provider = "hazelcast"
        elif self.CAFFEINE_CACHE_PATTERN.search(content):
            cache_config.cache_provider = "caffeine"
        elif self.REDIS_CACHE_PATTERN.search(content):
            cache_config.cache_provider = "redis"

        # L2 cache enabled
        l2 = self.L2_CACHE_ENABLED_PATTERN.search(content)
        if l2:
            val = l2.group(1) or l2.group(2)
            cache_config.l2_cache_enabled = val == 'true'

        # Query cache enabled
        qc = self.QUERY_CACHE_ENABLED_PATTERN.search(content)
        if qc:
            val = qc.group(1) or qc.group(2)
            cache_config.query_cache_enabled = val == 'true'

        # Cache mode
        cm = self.CACHE_MODE_PATTERN.search(content)
        if cm:
            cache_config.cache_mode = cm.group(1)

        cache_config.regions = cache_regions

        # Query cache regions
        for match in self.QUERY_CACHE_REGION_PATTERN.finditer(content):
            query_cache_regions.append(match.group(1))

        return {
            'cache_regions': cache_regions,
            'cache_config': cache_config,
            'query_cache_regions': query_cache_regions,
        }
