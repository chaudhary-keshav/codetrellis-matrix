"""
Hibernate extractors for CodeTrellis.

Provides specialized extractors for Hibernate ORM:
- Entity: JPA entity mapping, table/column annotations, relationships
- Session: SessionFactory, Session, EntityManager, transaction management
- Query: HQL, JPQL, Criteria API, native SQL, named queries
- Cache: L1/L2 cache, query cache, cache regions, eviction strategies
- Listener: Entity lifecycle callbacks, Hibernate event listeners, interceptors
"""

from .entity_extractor import (
    HibernateEntityExtractor,
    HibernateEntityInfo,
    HibernateRelationshipInfo,
    HibernateEmbeddableInfo,
)
from .session_extractor import (
    HibernateSessionExtractor,
    HibernateSessionFactoryInfo,
    HibernateTransactionInfo,
)
from .query_extractor import (
    HibernateQueryExtractor,
    HibernateQueryInfo,
    HibernateCriteriaInfo,
    HibernateNamedQueryInfo,
)
from .cache_extractor import (
    HibernateCacheExtractor,
    HibernateCacheRegionInfo,
    HibernateCacheConfigInfo,
)
from .listener_extractor import (
    HibernateListenerExtractor,
    HibernateListenerInfo,
    HibernateCallbackInfo,
    HibernateInterceptorInfo,
)

__all__ = [
    # Entity
    'HibernateEntityExtractor', 'HibernateEntityInfo',
    'HibernateRelationshipInfo', 'HibernateEmbeddableInfo',
    # Session
    'HibernateSessionExtractor', 'HibernateSessionFactoryInfo',
    'HibernateTransactionInfo',
    # Query
    'HibernateQueryExtractor', 'HibernateQueryInfo',
    'HibernateCriteriaInfo', 'HibernateNamedQueryInfo',
    # Cache
    'HibernateCacheExtractor', 'HibernateCacheRegionInfo',
    'HibernateCacheConfigInfo',
    # Listener
    'HibernateListenerExtractor', 'HibernateListenerInfo',
    'HibernateCallbackInfo', 'HibernateInterceptorInfo',
]
