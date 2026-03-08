"""
RxJS extractors package — 4 specialized extractors for reactive programming.

Extractors:
1. operator_extractor  — Pipeable, creation, transformation, filtering, combination, error, utility operators
2. observable_extractor — Observable creation, subscriptions, lifecycle, conversion
3. subject_extractor   — Subject, BehaviorSubject, ReplaySubject, AsyncSubject, emissions
4. scheduler_extractor — Schedulers, TestScheduler, marble testing
5. api_extractor       — Imports, framework integrations, TypeScript types, version, deprecations

v4.77: Full RxJS support (v5, v6, v7).
"""

from codetrellis.extractors.rxjs.operator_extractor import (
    RxjsOperatorExtractor,
    RxjsOperatorInfo,
    RxjsCustomOperatorInfo,
    RxjsPipeInfo,
)

from codetrellis.extractors.rxjs.observable_extractor import (
    RxjsObservableExtractor,
    RxjsObservableInfo,
    RxjsSubscriptionInfo,
    RxjsConversionInfo,
    RxjsSubscriptionMgmtInfo,
)

from codetrellis.extractors.rxjs.subject_extractor import (
    RxjsSubjectExtractor,
    RxjsSubjectInfo,
    RxjsSubjectEmissionInfo,
)

from codetrellis.extractors.rxjs.scheduler_extractor import (
    RxjsSchedulerExtractor,
    RxjsSchedulerInfo,
    RxjsTestingInfo,
    RxjsMarbleInfo,
)

from codetrellis.extractors.rxjs.api_extractor import (
    RxjsAPIExtractor,
    RxjsImportInfo,
    RxjsIntegrationInfo,
    RxjsTypeInfo,
    RxjsDeprecationInfo,
)

__all__ = [
    # Extractors
    'RxjsOperatorExtractor',
    'RxjsObservableExtractor',
    'RxjsSubjectExtractor',
    'RxjsSchedulerExtractor',
    'RxjsAPIExtractor',
    # Operator dataclasses
    'RxjsOperatorInfo',
    'RxjsCustomOperatorInfo',
    'RxjsPipeInfo',
    # Observable dataclasses
    'RxjsObservableInfo',
    'RxjsSubscriptionInfo',
    'RxjsConversionInfo',
    'RxjsSubscriptionMgmtInfo',
    # Subject dataclasses
    'RxjsSubjectInfo',
    'RxjsSubjectEmissionInfo',
    # Scheduler dataclasses
    'RxjsSchedulerInfo',
    'RxjsTestingInfo',
    'RxjsMarbleInfo',
    # API dataclasses
    'RxjsImportInfo',
    'RxjsIntegrationInfo',
    'RxjsTypeInfo',
    'RxjsDeprecationInfo',
]
