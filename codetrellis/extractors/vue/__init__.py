"""
CodeTrellis Vue.js Extractors Module v1.0

Provides comprehensive extractors for Vue.js framework constructs:

Component Extractors:
- VueComponentExtractor: SFC components (Options API, Composition API, <script setup>),
                         defineComponent, defineAsyncComponent, defineCustomElement,
                         props, emits, slots, expose, provide/inject

Composable Extractors:
- VueComposableExtractor: Composition API composables (use* functions),
                          ref/reactive/computed/watch/watchEffect,
                          lifecycle hooks (onMounted, onUpdated, etc.)

Directive Extractors:
- VueDirectiveExtractor: Custom directives (app.directive, vModelModifiers),
                         v-model modifiers, transition hooks

Plugin Extractors:
- VuePluginExtractor: Plugin definitions (app.use, install functions),
                      global components, global directives, provide/inject

Routing Extractors:
- VueRoutingExtractor: Vue Router routes, navigation guards,
                       route meta, lazy-loaded routes, Nuxt pages

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

from .component_extractor import (
    VueComponentExtractor,
    VueComponentInfo,
    VuePropInfo,
    VueEmitInfo,
    VueSlotInfo,
    VueProvideInjectInfo,
)
from .composable_extractor import (
    VueComposableExtractor,
    VueComposableInfo,
    VueRefInfo,
    VueComputedInfo,
    VueWatcherInfo,
    VueLifecycleHookInfo,
)
from .directive_extractor import (
    VueDirectiveExtractor,
    VueDirectiveInfo,
    VueTransitionInfo,
)
from .plugin_extractor import (
    VuePluginExtractor,
    VuePluginInfo,
    VueGlobalRegistrationInfo,
)
from .routing_extractor import (
    VueRoutingExtractor,
    VueRouteInfo,
    VueNavigationGuardInfo,
    VueRouterViewInfo,
)

__all__ = [
    # Component extractor
    'VueComponentExtractor',
    'VueComponentInfo',
    'VuePropInfo',
    'VueEmitInfo',
    'VueSlotInfo',
    'VueProvideInjectInfo',
    # Composable extractor
    'VueComposableExtractor',
    'VueComposableInfo',
    'VueRefInfo',
    'VueComputedInfo',
    'VueWatcherInfo',
    'VueLifecycleHookInfo',
    # Directive extractor
    'VueDirectiveExtractor',
    'VueDirectiveInfo',
    'VueTransitionInfo',
    # Plugin extractor
    'VuePluginExtractor',
    'VuePluginInfo',
    'VueGlobalRegistrationInfo',
    # Routing extractor
    'VueRoutingExtractor',
    'VueRouteInfo',
    'VueNavigationGuardInfo',
    'VueRouterViewInfo',
]
