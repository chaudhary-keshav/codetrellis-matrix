"""
CodeTrellis Svelte/SvelteKit Extractors Module v1.0

Provides comprehensive extractors for Svelte/SvelteKit framework constructs:

Component Extractors:
- SvelteComponentExtractor: .svelte component files, props ($props rune, export let),
                            events (createEventDispatcher, on:event), slots (default/named),
                            bindings (bind:), actions (use:), transitions, context API,
                            Svelte 5 runes ($state, $derived, $effect, $props, $bindable, $inspect)

Store Extractors:
- SvelteStoreExtractor: writable/readable/derived stores, custom stores,
                        svelte/store module, store contracts, auto-subscriptions ($store)

Action Extractors:
- SvelteActionExtractor: use: directive actions, action factories,
                         parameter typing, lifecycle (update/destroy)

Routing Extractors:
- SvelteRoutingExtractor: SvelteKit file-based routing (+page.svelte, +layout.svelte,
                          +server.ts, +page.ts, +page.server.ts, +error.svelte,
                          +layout.server.ts), load functions, form actions, hooks,
                          param matchers, route groups, rest params

Lifecycle Extractors:
- SvelteLifecycleExtractor: onMount, onDestroy, beforeUpdate, afterUpdate, tick,
                            Svelte 5 $effect/$effect.pre/$effect.root, context API
                            (setContext/getContext/hasContext/getAllContexts)

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

from .component_extractor import (
    SvelteComponentExtractor,
    SvelteComponentInfo,
    SveltePropInfo,
    SvelteEventInfo,
    SvelteSlotInfo,
    SvelteBindingInfo,
)
from .store_extractor import (
    SvelteStoreExtractor,
    SvelteStoreInfo,
    SvelteStoreSubscriptionInfo,
)
from .action_extractor import (
    SvelteActionExtractor,
    SvelteActionInfo,
)
from .routing_extractor import (
    SvelteRoutingExtractor,
    SvelteRouteInfo,
    SvelteLoadFunctionInfo,
    SvelteFormActionInfo,
    SvelteHookInfo,
    SvelteParamMatcherInfo,
)
from .lifecycle_extractor import (
    SvelteLifecycleExtractor,
    SvelteLifecycleHookInfo,
    SvelteContextInfo,
    SvelteRuneInfo,
)

__all__ = [
    # Component extractor
    'SvelteComponentExtractor',
    'SvelteComponentInfo',
    'SveltePropInfo',
    'SvelteEventInfo',
    'SvelteSlotInfo',
    'SvelteBindingInfo',
    # Store extractor
    'SvelteStoreExtractor',
    'SvelteStoreInfo',
    'SvelteStoreSubscriptionInfo',
    # Action extractor
    'SvelteActionExtractor',
    'SvelteActionInfo',
    # Routing extractor
    'SvelteRoutingExtractor',
    'SvelteRouteInfo',
    'SvelteLoadFunctionInfo',
    'SvelteFormActionInfo',
    'SvelteHookInfo',
    'SvelteParamMatcherInfo',
    # Lifecycle extractor
    'SvelteLifecycleExtractor',
    'SvelteLifecycleHookInfo',
    'SvelteContextInfo',
    'SvelteRuneInfo',
]
