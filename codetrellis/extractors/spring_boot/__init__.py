"""
CodeTrellis Spring Boot Extractors Module v1.0

Provides comprehensive extractors for Spring Boot framework constructs:

- SpringBootBeanExtractor: @Component, @Service, @Repository, @Controller beans,
  @Configuration classes, @Bean factory methods, profiles, conditions
- SpringBootAutoConfigExtractor: @EnableAutoConfiguration, auto-config classes,
  @ConditionalOn*, starter detection, customizers
- SpringBootEndpointExtractor: REST controllers, @RequestMapping, WebFlux handlers,
  actuator endpoints, health indicators, metrics
- SpringBootPropertyExtractor: application.properties/yml, @ConfigurationProperties,
  @Value, profiles, property sources, environment
- SpringBootSecurityExtractor: SecurityFilterChain, WebSecurityConfigurerAdapter (legacy),
  @EnableWebSecurity, OAuth2, JWT, method security
- SpringBootDataExtractor: Spring Data repositories, @Query, projections, auditing,
  transaction management, cache abstraction

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

from .bean_extractor import (
    SpringBootBeanExtractor,
    SpringBootBeanInfo,
    SpringBootConfigurationInfo,
    SpringBootBeanMethodInfo,
    SpringBootProfileInfo,
    SpringBootConditionInfo,
)
from .autoconfig_extractor import (
    SpringBootAutoConfigExtractor,
    SpringBootAutoConfigInfo,
    SpringBootStarterInfo,
    SpringBootCustomizerInfo,
)
from .endpoint_extractor import (
    SpringBootEndpointExtractor,
    SpringBootControllerInfo,
    SpringBootEndpointInfo,
    SpringBootActuatorInfo,
    SpringBootWebFluxHandlerInfo,
)
from .property_extractor import (
    SpringBootPropertyExtractor,
    SpringBootPropertyInfo,
    SpringBootConfigPropsInfo,
    SpringBootProfileConfigInfo,
)
from .security_extractor import (
    SpringBootSecurityExtractor,
    SpringBootSecurityConfigInfo,
    SpringBootAuthInfo,
    SpringBootMethodSecurityInfo,
)
from .data_extractor import (
    SpringBootDataExtractor,
    SpringBootRepoInfo,
    SpringBootQueryMethodInfo,
    SpringBootCacheInfo,
    SpringBootTransactionInfo,
)

__all__ = [
    # Bean extractors
    'SpringBootBeanExtractor', 'SpringBootBeanInfo', 'SpringBootConfigurationInfo',
    'SpringBootBeanMethodInfo', 'SpringBootProfileInfo', 'SpringBootConditionInfo',
    # AutoConfig extractors
    'SpringBootAutoConfigExtractor', 'SpringBootAutoConfigInfo',
    'SpringBootStarterInfo', 'SpringBootCustomizerInfo',
    # Endpoint extractors
    'SpringBootEndpointExtractor', 'SpringBootControllerInfo',
    'SpringBootEndpointInfo', 'SpringBootActuatorInfo', 'SpringBootWebFluxHandlerInfo',
    # Property extractors
    'SpringBootPropertyExtractor', 'SpringBootPropertyInfo',
    'SpringBootConfigPropsInfo', 'SpringBootProfileConfigInfo',
    # Security extractors
    'SpringBootSecurityExtractor', 'SpringBootSecurityConfigInfo',
    'SpringBootAuthInfo', 'SpringBootMethodSecurityInfo',
    # Data extractors
    'SpringBootDataExtractor', 'SpringBootRepoInfo',
    'SpringBootQueryMethodInfo', 'SpringBootCacheInfo', 'SpringBootTransactionInfo',
]
