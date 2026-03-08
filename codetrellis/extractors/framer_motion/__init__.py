"""
Framer Motion animation framework extractors for CodeTrellis.

Provides 5 extractors for comprehensive animation framework analysis:
1. FramerAnimationExtractor   - Variants, keyframes, transitions, AnimatePresence
2. FramerGestureExtractor     - Drag, tap, hover, pan, focus, viewport triggers
3. FramerLayoutExtractor      - Layout animations, shared layout, AnimatePresence exit
4. FramerScrollExtractor      - Scroll-linked animations, useScroll, useInView, parallax
5. FramerAPIExtractor         - Imports, hooks, integrations, TypeScript types, versions

Supports:
- framer-motion v1.x → v11+ (full API)
- motion v11+ (renamed package)
- React Spring interop patterns
- Popmotion / Framer ecosystem
"""

from codetrellis.extractors.framer_motion.animation_extractor import (
    FramerAnimationExtractor,
    FramerVariantInfo,
    FramerKeyframeInfo,
    FramerTransitionInfo,
    FramerAnimatePresenceInfo,
    FramerAnimationControlInfo,
)
from codetrellis.extractors.framer_motion.gesture_extractor import (
    FramerGestureExtractor,
    FramerGestureInfo,
    FramerDragInfo,
    FramerHoverInfo,
    FramerTapInfo,
)
from codetrellis.extractors.framer_motion.layout_extractor import (
    FramerLayoutExtractor,
    FramerLayoutAnimInfo,
    FramerSharedLayoutInfo,
    FramerExitAnimInfo,
)
from codetrellis.extractors.framer_motion.scroll_extractor import (
    FramerScrollExtractor,
    FramerScrollInfo,
    FramerInViewInfo,
    FramerParallaxInfo,
)
from codetrellis.extractors.framer_motion.api_extractor import (
    FramerAPIExtractor,
    FramerImportInfo,
    FramerHookInfo,
    FramerTypeInfo,
    FramerIntegrationInfo,
)

__all__ = [
    "FramerAnimationExtractor",
    "FramerVariantInfo",
    "FramerKeyframeInfo",
    "FramerTransitionInfo",
    "FramerAnimatePresenceInfo",
    "FramerAnimationControlInfo",
    "FramerGestureExtractor",
    "FramerGestureInfo",
    "FramerDragInfo",
    "FramerHoverInfo",
    "FramerTapInfo",
    "FramerLayoutExtractor",
    "FramerLayoutAnimInfo",
    "FramerSharedLayoutInfo",
    "FramerExitAnimInfo",
    "FramerScrollExtractor",
    "FramerScrollInfo",
    "FramerInViewInfo",
    "FramerParallaxInfo",
    "FramerAPIExtractor",
    "FramerImportInfo",
    "FramerHookInfo",
    "FramerTypeInfo",
    "FramerIntegrationInfo",
]
