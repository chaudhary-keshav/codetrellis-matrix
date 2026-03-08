"""
CodeTrellis HTMX Extractors Module v1.0

Provides comprehensive extractors for the HTMX framework:

Attribute Extractor:
- HtmxAttributeExtractor: hx-get, hx-post, hx-put, hx-patch, hx-delete,
                            hx-swap, hx-target, hx-trigger, hx-select,
                            hx-boost, hx-push-url, hx-indicator, hx-vals,
                            hx-headers, hx-confirm, hx-disable, hx-encoding,
                            hx-include, hx-params, hx-preserve, hx-prompt,
                            hx-replace-url, hx-select-oob, hx-swap-oob,
                            hx-sync, hx-validate, hx-on, hx-disinherit,
                            hx-history, hx-history-elt

Request Extractor:
- HtmxRequestExtractor: HTTP method endpoints (GET/POST/PUT/PATCH/DELETE),
                          hx-vals data, hx-headers, hx-include selectors,
                          hx-params filtering, hx-encoding (multipart),
                          request patterns, endpoint analysis

Event Extractor:
- HtmxEventExtractor: hx-trigger patterns (click, submit, load, revealed,
                        intersect, every Ns, custom events), htmx lifecycle
                        events (htmx:afterOnLoad, htmx:beforeRequest, etc.),
                        hx-on:* inline event handlers, modifier detection
                        (changed, delay, throttle, from, target, consume, queue)

Extension Extractor:
- HtmxExtensionExtractor: hx-ext attribute registrations, official extensions
                            (sse, ws, json-enc, class-tools, debug,
                             loading-states, head-support, preload,
                             response-targets, multi-swap, path-deps,
                             remove-me, restored, alpine-morph, client-side-templates,
                             event-header, include-vals, method-override, morphdom-swap),
                            custom extensions, extension dependencies

API Extractor:
- HtmxApiExtractor: Import patterns (htmx.org, htmx.org/dist), CDN script
                      tags, htmx.ajax(), htmx.process(), htmx.on(), htmx.off(),
                      htmx.trigger(), htmx.find(), htmx.findAll(), htmx.config,
                      htmx.logAll(), htmx.logger, htmx.defineExtension(),
                      _hyperscript integration, ecosystem integrations
                      (Alpine.js, Django, Flask, Rails, Laravel, FastAPI, Go/templ)

Supports:
- HTMX v1.x (legacy, htmx.org v1, data-hx-* prefix)
- HTMX v2.x (htmx.org v2, head-support default, improved WebSocket/SSE,
              response-targets, hx-on:* syntax, hx-disabled-elt,
              htmx:historyCacheMiss, hx-inherit)

Part of CodeTrellis v4.67 - HTMX Framework Support
"""

from .attribute_extractor import (
    HtmxAttributeExtractor,
    HtmxAttributeInfo,
)

from .request_extractor import (
    HtmxRequestExtractor,
    HtmxRequestInfo,
)

from .event_extractor import (
    HtmxEventExtractor,
    HtmxEventInfo,
)

from .extension_extractor import (
    HtmxExtensionExtractor,
    HtmxExtensionInfo,
)

from .api_extractor import (
    HtmxApiExtractor,
    HtmxImportInfo,
    HtmxIntegrationInfo,
    HtmxConfigInfo,
    HtmxCDNInfo,
)

__all__ = [
    # Attribute
    "HtmxAttributeExtractor",
    "HtmxAttributeInfo",
    # Request
    "HtmxRequestExtractor",
    "HtmxRequestInfo",
    # Event
    "HtmxEventExtractor",
    "HtmxEventInfo",
    # Extension
    "HtmxExtensionExtractor",
    "HtmxExtensionInfo",
    # API
    "HtmxApiExtractor",
    "HtmxImportInfo",
    "HtmxIntegrationInfo",
    "HtmxConfigInfo",
    "HtmxCDNInfo",
]
