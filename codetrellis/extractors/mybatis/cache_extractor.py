"""
MyBatis Cache Extractor - Extracts cache configuration and MyBatis config.

Extracts:
- @CacheNamespace annotations
- @CacheNamespaceRef references
- XML <cache> configuration
- Custom cache implementations
- MyBatis global configuration (mybatis-config.xml, application.yml)
- Plugin/interceptor registration
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MyBatisCacheInfo:
    """Information about MyBatis cache configuration."""
    cache_type: str = ""  # namespace, ref, xml
    implementation: str = ""  # default, ehcache, redis, hazelcast
    eviction: str = ""  # LRU, FIFO, SOFT, WEAK
    flush_interval: int = 0
    size: int = 0
    read_write: bool = True
    blocking: bool = False
    namespace: str = ""
    properties: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class MyBatisConfigInfo:
    """Information about MyBatis global configuration."""
    config_type: str = ""  # xml, spring_boot, spring
    mapper_locations: List[str] = field(default_factory=list)
    type_aliases_package: str = ""
    type_handlers_package: str = ""
    plugins: List[str] = field(default_factory=list)
    settings: Dict[str, str] = field(default_factory=dict)
    environments: List[str] = field(default_factory=list)
    line_number: int = 0


class MyBatisCacheExtractor:
    """Extracts MyBatis cache and configuration information."""

    # @CacheNamespace
    CACHE_NAMESPACE_PATTERN = re.compile(
        r'@CacheNamespace\s*\(\s*'
        r'(?:implementation\s*=\s*(\w+)\.class)?'
        r'(?:.*?eviction\s*=\s*(\w+)\.class)?'
        r'(?:.*?flushInterval\s*=\s*(\d+))?'
        r'(?:.*?size\s*=\s*(\d+))?'
        r'(?:.*?readWrite\s*=\s*(true|false))?'
        r'(?:.*?blocking\s*=\s*(true|false))?',
        re.DOTALL
    )

    # @CacheNamespaceRef
    CACHE_NAMESPACE_REF_PATTERN = re.compile(
        r'@CacheNamespaceRef\s*\(\s*(?:value\s*=\s*)?(\w+)\.class\s*\)',
        re.MULTILINE
    )

    # XML <cache> element
    XML_CACHE_PATTERN = re.compile(
        r'<cache\s*'
        r'(?:type\s*=\s*["\']([^"\']+)["\'])?'
        r'(?:\s+eviction\s*=\s*["\'](\w+)["\'])?'
        r'(?:\s+flushInterval\s*=\s*["\'](\d+)["\'])?'
        r'(?:\s+size\s*=\s*["\'](\d+)["\'])?'
        r'(?:\s+readOnly\s*=\s*["\'](\w+)["\'])?',
        re.DOTALL
    )

    # XML <cache-ref>
    XML_CACHE_REF_PATTERN = re.compile(
        r'<cache-ref\s+namespace\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # MyBatis configuration (XML)
    MYBATIS_CONFIG_PATTERN = re.compile(
        r'<configuration\s*>',
        re.MULTILINE
    )

    # Settings
    SETTING_PATTERN = re.compile(
        r'<setting\s+name\s*=\s*["\'](\w+)["\']'
        r'\s+value\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Type alias package
    TYPE_ALIAS_PACKAGE_PATTERN = re.compile(
        r'<typeAliases>\s*<package\s+name\s*=\s*["\']([^"\']+)["\']',
        re.DOTALL
    )

    # Plugin/interceptor
    PLUGIN_PATTERN = re.compile(
        r'<plugin\s+interceptor\s*=\s*["\']([^"\']+)["\']|'
        r'@Intercepts\s*\(\s*\{?\s*@Signature',
        re.DOTALL
    )

    INTERCEPTOR_CLASS_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+Interceptor',
        re.DOTALL
    )

    # Spring Boot config (in Java)
    SPRING_MYBATIS_CONFIG_PATTERN = re.compile(
        r'@MapperScan|SqlSessionFactoryBean|'
        r'mybatis\.mapper-locations|'
        r'mybatis\.type-aliases-package|'
        r'mybatis\.configuration\.',
        re.MULTILINE
    )

    # MapperScannerConfigurer
    MAPPER_SCANNER_PATTERN = re.compile(
        r'MapperScannerConfigurer\s+\w+|'
        r'setBasePackage\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # MyBatis-Plus configuration
    MYBATIS_PLUS_PATTERN = re.compile(
        r'import\s+com\.baomidou\.mybatisplus\b|'
        r'@TableName|@TableId|@TableField|'
        r'IService|ServiceImpl|BaseMapper',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract cache and configuration information."""
        caches: List[MyBatisCacheInfo] = []
        configs: List[MyBatisConfigInfo] = []
        plugins: List[str] = []
        is_mybatis_plus = False

        if not content or not content.strip():
            return {
                'caches': caches,
                'configs': configs,
                'plugins': plugins,
                'is_mybatis_plus': is_mybatis_plus,
            }

        # @CacheNamespace
        for match in self.CACHE_NAMESPACE_PATTERN.finditer(content):
            cache = MyBatisCacheInfo(
                cache_type="namespace",
                implementation=match.group(1) or "default",
                eviction=match.group(2) or "LRU",
                flush_interval=int(match.group(3)) if match.group(3) else 0,
                size=int(match.group(4)) if match.group(4) else 0,
                read_write=match.group(5) != 'false' if match.group(5) else True,
                blocking=match.group(6) == 'true' if match.group(6) else False,
                line_number=content[:match.start()].count('\n') + 1,
            )
            caches.append(cache)

        # @CacheNamespaceRef
        for match in self.CACHE_NAMESPACE_REF_PATTERN.finditer(content):
            cache = MyBatisCacheInfo(
                cache_type="ref",
                namespace=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            )
            caches.append(cache)

        # XML <cache>
        for match in self.XML_CACHE_PATTERN.finditer(content):
            cache = MyBatisCacheInfo(
                cache_type="xml",
                implementation=match.group(1) or "default",
                eviction=match.group(2) or "LRU",
                flush_interval=int(match.group(3)) if match.group(3) else 0,
                size=int(match.group(4)) if match.group(4) else 0,
                line_number=content[:match.start()].count('\n') + 1,
            )
            caches.append(cache)

        # XML <cache-ref>
        for match in self.XML_CACHE_REF_PATTERN.finditer(content):
            cache = MyBatisCacheInfo(
                cache_type="xml_ref",
                namespace=match.group(1),
                line_number=content[:match.start()].count('\n') + 1,
            )
            caches.append(cache)

        # MyBatis configuration
        if self.MYBATIS_CONFIG_PATTERN.search(content):
            config = MyBatisConfigInfo(
                config_type="xml",
                line_number=1,
            )

            # Settings
            for match in self.SETTING_PATTERN.finditer(content):
                config.settings[match.group(1)] = match.group(2)

            # Type alias package
            ta = self.TYPE_ALIAS_PACKAGE_PATTERN.search(content)
            if ta:
                config.type_aliases_package = ta.group(1)

            configs.append(config)

        # Spring Boot / Spring config
        if self.SPRING_MYBATIS_CONFIG_PATTERN.search(content):
            config = MyBatisConfigInfo(
                config_type="spring_boot",
                line_number=1,
            )
            configs.append(config)

        # Plugins/interceptors
        for match in self.PLUGIN_PATTERN.finditer(content):
            if match.group(1):
                plugins.append(match.group(1))

        for match in self.INTERCEPTOR_CLASS_PATTERN.finditer(content):
            plugins.append(match.group(1))

        # MyBatis-Plus detection
        is_mybatis_plus = bool(self.MYBATIS_PLUS_PATTERN.search(content))

        return {
            'caches': caches,
            'configs': configs,
            'plugins': plugins,
            'is_mybatis_plus': is_mybatis_plus,
        }
