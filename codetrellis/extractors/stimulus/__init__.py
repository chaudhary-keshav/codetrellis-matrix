"""
CodeTrellis Stimulus / Hotwire Extractors Module v1.0

Provides comprehensive extractors for the Stimulus framework (part of Hotwire):

Controller Extractor:
- StimulusControllerExtractor: Stimulus controller definitions, lifecycle callbacks,
                                class inheritance, connected/disconnected callbacks,
                                initialize, connect, disconnect, controller registration

Target Extractor:
- StimulusTargetExtractor: static targets arrays, target getters (has*Target,
                            *Target, *Targets), target callbacks (targetConnected/
                            targetDisconnected), data-*-target HTML attributes

Action Extractor:
- StimulusActionExtractor: data-action HTML attributes, action descriptors
                            (event->controller#method), action parameters
                            (data-*-param), action options (prevent, stop),
                            keyboard filters, global actions (window/document)

Value Extractor:
- StimulusValueExtractor: static values objects (type definitions), value
                           getters/setters (*Value, *Value=), value change
                           callbacks (*ValueChanged), data-*-value HTML attributes,
                           default values, value type coercion

API Extractor:
- StimulusApiExtractor: Import patterns (@hotwired/stimulus, stimulus),
                          Application.start(), register(), load(),
                          Turbo integration (turbo-frame, turbo-stream,
                          turbo:*, @hotwired/turbo, @hotwired/turbo-rails),
                          Strada integration (@hotwired/strada),
                          CDN detection, ecosystem integrations
                          (Rails, Laravel, Django, Phoenix, Spring)

Supports:
- Stimulus v1.x (legacy, stimulus npm package, data-controller, data-action, data-target)
- Stimulus v2.x (@hotwired/stimulus, values API, classes API, outlets API removed)
- Stimulus v3.x (@hotwired/stimulus, outlets API restored, afterLoad callback)
- Turbo v7.x (@hotwired/turbo, turbo-frame, turbo-stream, turbo-drive)
- Turbo v8.x (@hotwired/turbo, morphing, page refreshes, turbo:morph-*)
- Strada v1.x (@hotwired/strada, native bridge, BridgeComponent)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

from .controller_extractor import (
    StimulusControllerExtractor,
    StimulusControllerInfo,
)

from .target_extractor import (
    StimulusTargetExtractor,
    StimulusTargetInfo,
)

from .action_extractor import (
    StimulusActionExtractor,
    StimulusActionInfo,
)

from .value_extractor import (
    StimulusValueExtractor,
    StimulusValueInfo,
)

from .api_extractor import (
    StimulusApiExtractor,
    StimulusImportInfo,
    StimulusIntegrationInfo,
    StimulusConfigInfo,
    StimulusCDNInfo,
)

__all__ = [
    # Controller
    "StimulusControllerExtractor",
    "StimulusControllerInfo",
    # Target
    "StimulusTargetExtractor",
    "StimulusTargetInfo",
    # Action
    "StimulusActionExtractor",
    "StimulusActionInfo",
    # Value
    "StimulusValueExtractor",
    "StimulusValueInfo",
    # API
    "StimulusApiExtractor",
    "StimulusImportInfo",
    "StimulusIntegrationInfo",
    "StimulusConfigInfo",
    "StimulusCDNInfo",
]
