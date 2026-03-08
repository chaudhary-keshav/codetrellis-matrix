"""
Django extractors for CodeTrellis.

Extracts Django-specific constructs: models, views, URLs, middleware,
forms, admin, signals, management commands, template tags, serializers (DRF).
"""

from .model_extractor import DjangoModelExtractor, DjangoModelInfo, DjangoFieldInfo, DjangoRelationshipInfo
from .view_extractor import DjangoViewExtractor, DjangoViewInfo, DjangoURLPatternInfo
from .middleware_extractor import DjangoMiddlewareExtractor, DjangoMiddlewareInfo
from .form_extractor import DjangoFormExtractor, DjangoFormInfo
from .admin_extractor import DjangoAdminExtractor, DjangoAdminInfo
from .signal_extractor import DjangoSignalExtractor, DjangoSignalInfo
from .serializer_extractor import DjangoSerializerExtractor, DjangoSerializerInfo
from .api_extractor import DjangoAPIExtractor, DjangoProjectInfo

__all__ = [
    'DjangoModelExtractor', 'DjangoModelInfo', 'DjangoFieldInfo', 'DjangoRelationshipInfo',
    'DjangoViewExtractor', 'DjangoViewInfo', 'DjangoURLPatternInfo',
    'DjangoMiddlewareExtractor', 'DjangoMiddlewareInfo',
    'DjangoFormExtractor', 'DjangoFormInfo',
    'DjangoAdminExtractor', 'DjangoAdminInfo',
    'DjangoSignalExtractor', 'DjangoSignalInfo',
    'DjangoSerializerExtractor', 'DjangoSerializerInfo',
    'DjangoAPIExtractor', 'DjangoProjectInfo',
]
