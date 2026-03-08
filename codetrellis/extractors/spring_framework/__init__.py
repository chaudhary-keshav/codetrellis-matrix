"""
CodeTrellis Spring Framework Extractors Module v1.0

Provides extractors for Spring Framework core constructs (non-Boot specific):

- SpringDIExtractor: @Autowired, @Inject, @Resource, constructor injection,
  setter injection, field injection, @Qualifier, @Primary, @Lazy
- SpringAOPExtractor: @Aspect, @Before, @After, @Around, @AfterReturning,
  @AfterThrowing, pointcut expressions, introductions
- SpringEventExtractor: ApplicationEvent, @EventListener, ApplicationEventPublisher,
  @TransactionalEventListener, async events
- SpringMVCExtractor: HandlerInterceptor, ViewResolver, MessageConverter,
  MultipartResolver, WebMvcConfigurer, argument resolvers

Part of CodeTrellis v4.94 - Spring Framework Support
"""

from .di_extractor import (
    SpringDIExtractor,
    SpringDIInfo,
    SpringBeanDefinitionInfo,
    SpringQualifierInfo,
)
from .aop_extractor import (
    SpringAOPExtractor,
    SpringAspectInfo,
    SpringAdviceInfo,
    SpringPointcutInfo,
)
from .event_extractor import (
    SpringEventExtractor,
    SpringEventInfo,
    SpringEventListenerInfo,
    SpringEventPublisherInfo,
)
from .mvc_extractor import (
    SpringMVCExtractor,
    SpringInterceptorInfo,
    SpringConverterInfo,
    SpringResolverInfo,
)

__all__ = [
    # DI extractors
    'SpringDIExtractor', 'SpringDIInfo', 'SpringBeanDefinitionInfo', 'SpringQualifierInfo',
    # AOP extractors
    'SpringAOPExtractor', 'SpringAspectInfo', 'SpringAdviceInfo', 'SpringPointcutInfo',
    # Event extractors
    'SpringEventExtractor', 'SpringEventInfo', 'SpringEventListenerInfo', 'SpringEventPublisherInfo',
    # MVC extractors
    'SpringMVCExtractor', 'SpringInterceptorInfo', 'SpringConverterInfo', 'SpringResolverInfo',
]
