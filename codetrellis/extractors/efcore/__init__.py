"""
Entity Framework Core extractors for CodeTrellis.

Part of CodeTrellis v4.96 - .NET Framework Enhanced Support
"""

from .context_extractor import (
    EFCoreContextExtractor,
    EFCoreDbContextInfo,
    EFCoreDbSetInfo,
    EFCoreMigrationInfo,
)
from .model_extractor import (
    EFCoreModelExtractor,
    EFCoreEntityInfo,
    EFCoreRelationshipInfo,
    EFCoreValueConversionInfo,
)
from .query_extractor import (
    EFCoreQueryExtractor,
    EFCoreQueryFilterInfo,
    EFCoreInterceptorInfo,
)

__all__ = [
    'EFCoreContextExtractor', 'EFCoreDbContextInfo', 'EFCoreDbSetInfo', 'EFCoreMigrationInfo',
    'EFCoreModelExtractor', 'EFCoreEntityInfo', 'EFCoreRelationshipInfo', 'EFCoreValueConversionInfo',
    'EFCoreQueryExtractor', 'EFCoreQueryFilterInfo', 'EFCoreInterceptorInfo',
]
