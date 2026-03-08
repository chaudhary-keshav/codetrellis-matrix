"""
CodeTrellis Valtio Extractors Module v1.0

Provides comprehensive extractors for Valtio proxy-based state management constructs:

Proxy Extractor:
- ValtioProxyExtractor: proxy() definitions, state shape analysis, computed getters,
                         ref() usage, nested proxies, proxyMap(), proxySet(),
                         TypeScript generic types, module-level state

Snapshot Extractor:
- ValtioSnapshotExtractor: useSnapshot() hook calls, snapshot() vanilla calls,
                            useProxy() convenience hook, destructured access,
                            sync option, nested snapshot access, Suspense integration

Subscription Extractor:
- ValtioSubscriptionExtractor: subscribe() state subscriptions, subscribeKey() primitive
                                subscriptions, watch() (deprecated) reactive effects,
                                unsubscribe patterns, notifyInSync option

Action Extractor:
- ValtioActionExtractor: Direct state mutations (state.field = ...), mutation functions,
                          devtools() integration, array mutations (push/splice/pop),
                          async actions, derived/computed patterns

API Extractor:
- ValtioApiExtractor: Import patterns (valtio, valtio/vanilla, valtio/utils,
                       valtio/vanilla/utils), TypeScript types (Snapshot, INTERNAL_Snapshot),
                       integrations (React, React Native, Next.js, derive-valtio,
                       valtio-reactive, use-valtio, eslint-plugin-valtio, proxy-compare),
                       deprecated API detection, version detection (v1, v2)

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

from .proxy_extractor import (
    ValtioProxyExtractor,
    ValtioProxyInfo,
    ValtioRefInfo,
    ValtioProxyCollectionInfo,
)
from .snapshot_extractor import (
    ValtioSnapshotExtractor,
    ValtioSnapshotUsageInfo,
    ValtioUseProxyInfo,
)
from .subscription_extractor import (
    ValtioSubscriptionExtractor,
    ValtioSubscribeInfo,
    ValtioSubscribeKeyInfo,
    ValtioWatchInfo,
)
from .action_extractor import (
    ValtioActionExtractor,
    ValtioActionInfo,
    ValtioDevtoolsInfo,
)
from .api_extractor import (
    ValtioApiExtractor,
    ValtioImportInfo,
    ValtioIntegrationInfo,
    ValtioTypeInfo,
)

__all__ = [
    # Proxy
    "ValtioProxyExtractor",
    "ValtioProxyInfo",
    "ValtioRefInfo",
    "ValtioProxyCollectionInfo",
    # Snapshot
    "ValtioSnapshotExtractor",
    "ValtioSnapshotUsageInfo",
    "ValtioUseProxyInfo",
    # Subscription
    "ValtioSubscriptionExtractor",
    "ValtioSubscribeInfo",
    "ValtioSubscribeKeyInfo",
    "ValtioWatchInfo",
    # Action
    "ValtioActionExtractor",
    "ValtioActionInfo",
    "ValtioDevtoolsInfo",
    # API
    "ValtioApiExtractor",
    "ValtioImportInfo",
    "ValtioIntegrationInfo",
    "ValtioTypeInfo",
]
