"""
GSAP (GreenSock Animation Platform) extractors for CodeTrellis.

Provides 5 extractors for comprehensive GSAP animation analysis:
1. GsapAnimationExtractor   - Tweens (gsap.to/from/fromTo/set), timelines, stagger
2. GsapTimelineExtractor    - Timeline sequences, labels, callbacks, nested timelines
3. GsapPluginExtractor      - ScrollTrigger, MotionPath, Flip, Observer, SplitText, etc.
4. GsapScrollExtractor      - ScrollTrigger configs, pin, scrub, snap, batch
5. GsapAPIExtractor         - Imports, registration, TypeScript types, integrations

Supports:
- GSAP v1.x (TweenMax, TweenLite, TimelineMax, TimelineLite, legacy API)
- GSAP v2.x (transition API, simplified classes)
- GSAP v3.x (gsap.to/from/fromTo/set, gsap.timeline, gsap.registerPlugin,
              ScrollTrigger, MotionPath, Flip, Observer, DrawSVG, MorphSVG,
              SplitText, ScrollSmoother, Draggable, Inertia, TextPlugin,
              PixiPlugin, EaselPlugin, matchMedia, context, effects,
              gsap.utils, gsap.parseEase)

AST via regex + optional tree-sitter-javascript / tsserver LSP.
v4.77: Full GSAP support.
"""

from codetrellis.extractors.gsap.animation_extractor import (
    GsapAnimationExtractor,
    GsapTweenInfo,
    GsapSetInfo,
    GsapStaggerInfo,
    GsapEaseInfo,
)
from codetrellis.extractors.gsap.timeline_extractor import (
    GsapTimelineExtractor,
    GsapTimelineInfo,
    GsapLabelInfo,
    GsapCallbackInfo,
    GsapNestedTimelineInfo,
)
from codetrellis.extractors.gsap.plugin_extractor import (
    GsapPluginExtractor,
    GsapPluginInfo,
    GsapRegistrationInfo,
    GsapEffectInfo,
    GsapUtilityInfo,
)
from codetrellis.extractors.gsap.scroll_extractor import (
    GsapScrollExtractor,
    GsapScrollTriggerInfo,
    GsapScrollSmootherInfo,
    GsapObserverInfo,
    GsapScrollBatchInfo,
)
from codetrellis.extractors.gsap.api_extractor import (
    GsapAPIExtractor,
    GsapImportInfo,
    GsapIntegrationInfo,
    GsapTypeInfo,
    GsapContextInfo,
    GsapMatchMediaInfo,
)

__all__ = [
    # Extractors
    "GsapAnimationExtractor",
    "GsapTimelineExtractor",
    "GsapPluginExtractor",
    "GsapScrollExtractor",
    "GsapAPIExtractor",
    # Animation dataclasses
    "GsapTweenInfo",
    "GsapSetInfo",
    "GsapStaggerInfo",
    "GsapEaseInfo",
    # Timeline dataclasses
    "GsapTimelineInfo",
    "GsapLabelInfo",
    "GsapCallbackInfo",
    "GsapNestedTimelineInfo",
    # Plugin dataclasses
    "GsapPluginInfo",
    "GsapRegistrationInfo",
    "GsapEffectInfo",
    "GsapUtilityInfo",
    # Scroll dataclasses
    "GsapScrollTriggerInfo",
    "GsapScrollSmootherInfo",
    "GsapObserverInfo",
    "GsapScrollBatchInfo",
    # API dataclasses
    "GsapImportInfo",
    "GsapIntegrationInfo",
    "GsapTypeInfo",
    "GsapContextInfo",
    "GsapMatchMediaInfo",
]
