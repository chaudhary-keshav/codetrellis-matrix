"""
CodeTrellis Lit / Web Components Extractors Module v1.0

Provides comprehensive extractors for Lit framework and Web Components:

Component Extractor:
- LitComponentExtractor: LitElement class components, @customElement decorator,
                          static styles, render(), connectedCallback, disconnectedCallback,
                          firstUpdated, updated, willUpdate, createRenderRoot,
                          shadow DOM / light DOM, custom element registration

Property Extractor:
- LitPropertyExtractor: @property decorator, @state decorator, reactive properties,
                         static properties block, attribute reflection, converters,
                         hasChanged, type coercion, PropertyDeclaration

Event Extractor:
- LitEventExtractor: @event decorators, CustomEvent dispatching, EventTarget,
                      dispatchEvent, addEventListener, event options,
                      composed/bubbles/cancelable, @eventOptions

Template Extractor:
- LitTemplateExtractor: html`` tagged templates, svg`` tagged templates,
                         css`` tagged templates, nothing/noChange sentinels,
                         repeat/map/join/range/when/choose/guard/cache/keyed/live
                         template directives, ref() directive, classMap/styleMap,
                         ifDefined/until/asyncAppend/asyncReplace, unsafeHTML/unsafeSVG,
                         template expressions, event bindings (.listener @event ?attr .prop)

API Extractor:
- LitApiExtractor: Import patterns (lit, lit-element, lit-html, lit/decorators,
                    @lit/reactive-element, @lit-labs/*, @lit/localize, @lit/task,
                    @lit/context), ecosystem integrations, TypeScript types,
                    SSR patterns (@lit-labs/ssr), controllers, mixins, tasks

Supports:
- Polymer 1.x-3.x (legacy Polymer element, iron-*, paper-*)
- lit-element 2.x (LitElement, customElement, property, css, html)
- lit-html 1.x (html, svg, render, directives)
- lit 2.x (unified package, decorators, reactive-element)
- lit 3.x (Preact signals integration, @lit-labs/preact-signals)
- @lit/reactive-element (ReactiveElement, ReactiveController)
- @lit-labs/* experimental packages (ssr, router, task, context, motion, observers, virtualizer)
- @lit/localize (localization framework)
- @lit/task (async data loading)
- @lit/context (context protocol)
- Web Components standards (Custom Elements v1, Shadow DOM, HTML Templates, CSS Custom Properties)

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

from .component_extractor import (
    LitComponentExtractor,
    LitComponentInfo,
    LitMixinInfo,
    LitControllerInfo,
)
from .property_extractor import (
    LitPropertyExtractor,
    LitPropertyInfo,
    LitStateInfo,
)
from .event_extractor import (
    LitEventExtractor,
    LitEventInfo,
    LitEventListenerInfo,
)
from .template_extractor import (
    LitTemplateExtractor,
    LitTemplateInfo,
    LitDirectiveUsageInfo,
    LitCSSInfo,
)
from .api_extractor import (
    LitApiExtractor,
    LitImportInfo,
    LitIntegrationInfo,
    LitTypeInfo,
    LitSSRInfo,
)

__all__ = [
    # Component
    "LitComponentExtractor",
    "LitComponentInfo",
    "LitMixinInfo",
    "LitControllerInfo",
    # Property
    "LitPropertyExtractor",
    "LitPropertyInfo",
    "LitStateInfo",
    # Event
    "LitEventExtractor",
    "LitEventInfo",
    "LitEventListenerInfo",
    # Template
    "LitTemplateExtractor",
    "LitTemplateInfo",
    "LitDirectiveUsageInfo",
    "LitCSSInfo",
    # API
    "LitApiExtractor",
    "LitImportInfo",
    "LitIntegrationInfo",
    "LitTypeInfo",
    "LitSSRInfo",
]
