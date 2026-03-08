"""
CodeTrellis Alpine.js Extractors Module v1.0

Provides comprehensive extractors for Alpine.js framework:

Directive Extractor:
- AlpineDirectiveExtractor: x-data, x-bind/:, x-on/@, x-model, x-show, x-if,
                             x-for, x-transition, x-effect, x-ref, x-text, x-html,
                             x-init, x-cloak, x-teleport, x-ignore, x-id,
                             x-trap, x-intersect, x-anchor, x-sort, x-collapse,
                             x-mask, x-resize, custom x-* directives

Component Extractor:
- AlpineComponentExtractor: x-data component definitions, Alpine.data() registered
                             components, inline x-data objects, component methods,
                             computed getters, init() lifecycle, destroy() lifecycle,
                             nested components, $refs, $el, $root, $data

Store Extractor:
- AlpineStoreExtractor: Alpine.store() definitions, $store access patterns,
                          store state fields, store methods, store getters,
                          cross-store references, persistent stores

Plugin Extractor:
- AlpinePluginExtractor: Alpine.plugin() registrations, @alpinejs/* official plugins
                           (mask/intersect/persist/morph/focus/collapse/anchor/sort/ui),
                           custom plugin definitions, Alpine.directive() custom directives,
                           Alpine.magic() custom magics, third-party plugins

API Extractor:
- AlpineApiExtractor: Import patterns (alpinejs, @alpinejs/*), CDN script tags,
                        Alpine.start(), Alpine.store(), Alpine.data(), Alpine.directive(),
                        Alpine.magic(), Alpine.plugin(), Alpine.bind(), Alpine.evaluate(),
                        TypeScript types, ecosystem integrations (HTMX, Livewire, Turbo)

Supports:
- Alpine.js v1.x (legacy, script tag only, no Alpine.start())
- Alpine.js v2.x (x-spread, x-ref, component object pattern)
- Alpine.js v3.x (Alpine.start(), Alpine.data(), Alpine.store(), modular plugins,
                   x-effect, x-teleport, x-id, x-modelable, x-ignore,
                   ESM imports, CDN with defer)
- Alpine.js v3.14+ (Alpine.bind(), improved reactivity, x-sort plugin)

Part of CodeTrellis v4.66 - Alpine.js Framework Support
"""

from .directive_extractor import (
    AlpineDirectiveExtractor,
    AlpineDirectiveInfo,
)
from .component_extractor import (
    AlpineComponentExtractor,
    AlpineComponentInfo,
    AlpineMethodInfo,
)
from .store_extractor import (
    AlpineStoreExtractor,
    AlpineStoreInfo,
)
from .plugin_extractor import (
    AlpinePluginExtractor,
    AlpinePluginInfo,
    AlpineCustomDirectiveInfo,
    AlpineCustomMagicInfo,
)
from .api_extractor import (
    AlpineApiExtractor,
    AlpineImportInfo,
    AlpineIntegrationInfo,
    AlpineTypeInfo,
    AlpineCDNInfo,
)

__all__ = [
    # Directive
    "AlpineDirectiveExtractor",
    "AlpineDirectiveInfo",
    # Component
    "AlpineComponentExtractor",
    "AlpineComponentInfo",
    "AlpineMethodInfo",
    # Store
    "AlpineStoreExtractor",
    "AlpineStoreInfo",
    # Plugin
    "AlpinePluginExtractor",
    "AlpinePluginInfo",
    "AlpineCustomDirectiveInfo",
    "AlpineCustomMagicInfo",
    # API
    "AlpineApiExtractor",
    "AlpineImportInfo",
    "AlpineIntegrationInfo",
    "AlpineTypeInfo",
    "AlpineCDNInfo",
]
