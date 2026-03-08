"""
Enhanced Framer Motion animation framework parser for CodeTrellis.

Parses JavaScript/TypeScript/JSX/TSX files containing Framer Motion
animation code. Delegates to 5 specialized extractors for comprehensive
animation framework analysis.

Supports:
- framer-motion v1 → v10 (full API surface)
- motion v11+ (renamed package, same API)
- React-based motion components (motion.div, motion.span, etc.)
- Gesture animations (drag, hover, tap, pan, focus, viewport)
- Layout animations (layout prop, shared layout, AnimatePresence)
- Scroll-linked animations (useScroll, useInView, parallax)
- Animation hooks (useMotionValue, useTransform, useSpring, useAnimate, etc.)
- TypeScript types (Variants, Transition, MotionProps, etc.)
- Ecosystem integrations (Popmotion, React Spring bridge)

AST via regex + optional tree-sitter-javascript / tsserver LSP.
v4.76: Full Framer Motion support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from codetrellis.extractors.framer_motion import (
    FramerAnimationExtractor,
    FramerGestureExtractor,
    FramerLayoutExtractor,
    FramerScrollExtractor,
    FramerAPIExtractor,
    FramerVariantInfo,
    FramerKeyframeInfo,
    FramerTransitionInfo,
    FramerAnimatePresenceInfo,
    FramerAnimationControlInfo,
    FramerGestureInfo,
    FramerDragInfo,
    FramerHoverInfo,
    FramerTapInfo,
    FramerLayoutAnimInfo,
    FramerSharedLayoutInfo,
    FramerExitAnimInfo,
    FramerScrollInfo,
    FramerInViewInfo,
    FramerParallaxInfo,
    FramerImportInfo,
    FramerHookInfo,
    FramerTypeInfo,
    FramerIntegrationInfo,
)


@dataclass
class FramerMotionParseResult:
    """Complete result of parsing a Framer Motion file."""
    file_path: str = ""
    file_type: str = ""         # 'js', 'jsx', 'ts', 'tsx'

    # Animation constructs (from animation_extractor)
    variants: List[FramerVariantInfo] = field(default_factory=list)
    keyframes: List[FramerKeyframeInfo] = field(default_factory=list)
    transitions: List[FramerTransitionInfo] = field(default_factory=list)
    animate_presences: List[FramerAnimatePresenceInfo] = field(default_factory=list)
    animation_controls: List[FramerAnimationControlInfo] = field(default_factory=list)
    motion_components: List[Dict] = field(default_factory=list)

    # Gesture constructs (from gesture_extractor)
    drags: List[FramerDragInfo] = field(default_factory=list)
    hovers: List[FramerHoverInfo] = field(default_factory=list)
    taps: List[FramerTapInfo] = field(default_factory=list)
    gestures: List[FramerGestureInfo] = field(default_factory=list)
    drag_controls: List[Dict] = field(default_factory=list)

    # Layout constructs (from layout_extractor)
    layout_anims: List[FramerLayoutAnimInfo] = field(default_factory=list)
    shared_layouts: List[FramerSharedLayoutInfo] = field(default_factory=list)
    exit_anims: List[FramerExitAnimInfo] = field(default_factory=list)

    # Scroll constructs (from scroll_extractor)
    scrolls: List[FramerScrollInfo] = field(default_factory=list)
    in_views: List[FramerInViewInfo] = field(default_factory=list)
    parallaxes: List[FramerParallaxInfo] = field(default_factory=list)
    scroll_events: List[Dict] = field(default_factory=list)

    # API constructs (from api_extractor)
    imports: List[FramerImportInfo] = field(default_factory=list)
    hooks: List[FramerHookInfo] = field(default_factory=list)
    types: List[FramerTypeInfo] = field(default_factory=list)
    integrations: List[FramerIntegrationInfo] = field(default_factory=list)
    motion_elements: List[Dict] = field(default_factory=list)
    version_info: Dict = field(default_factory=dict)

    # Detected metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    framer_motion_version: str = ""
    has_typescript: bool = False
    has_variants: bool = False
    has_gestures: bool = False
    has_layout_animations: bool = False
    has_scroll_animations: bool = False
    has_animate_presence: bool = False
    has_drag: bool = False


class EnhancedFramerMotionParser:
    """
    Full-featured Framer Motion animation framework parser.

    Coordinates 5 specialized extractors to provide comprehensive
    animation framework analysis. Follows the Leaflet parser architecture.
    """

    # Framework/library detection patterns
    FRAMEWORK_PATTERNS = {
        'framer-motion': re.compile(r"""(?:from\s+['"]framer-motion['"]|require\s*\(\s*['"]framer-motion['"])"""),
        'motion': re.compile(r"""(?:from\s+['"]motion['"]|require\s*\(\s*['"]motion['"])"""),
        'motion-subpath': re.compile(r"""(?:from\s+['"](?:framer-motion|motion)/[^'"]+['"])"""),
        'animate-presence': re.compile(r"""(?:<AnimatePresence|AnimatePresence\s)"""),
        'lazy-motion': re.compile(r"""(?:<LazyMotion|LazyMotion\s)"""),
        'motion-config': re.compile(r"""(?:<MotionConfig|MotionConfig\s)"""),
        'layout-group': re.compile(r"""(?:<LayoutGroup|LayoutGroup\s)"""),
        'reorder': re.compile(r"""(?:<Reorder\.Group|<Reorder\.Item|Reorder\.)"""),
        'popmotion': re.compile(r"""(?:from\s+['"]popmotion['"]|require\s*\(\s*['"]popmotion['"])"""),
        'react-spring-bridge': re.compile(r"""(?:from\s+['"]@react-spring/framer-motion['"])"""),
        'framer': re.compile(r"""(?:from\s+['"]framer['"]|require\s*\(\s*['"]framer['"])"""),
        'motion-dom': re.compile(r"""(?:from\s+['"](?:framer-motion|motion)/dom['"])"""),
        'motion-three': re.compile(r"""(?:from\s+['"]framer-motion-3d['"]|motion-three)"""),
    }

    def __init__(self):
        """Initialize all 5 extractors."""
        self.animation_extractor = FramerAnimationExtractor()
        self.gesture_extractor = FramerGestureExtractor()
        self.layout_extractor = FramerLayoutExtractor()
        self.scroll_extractor = FramerScrollExtractor()
        self.api_extractor = FramerAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> FramerMotionParseResult:
        """
        Parse a file for Framer Motion animation constructs.

        Args:
            content: Source code content
            file_path: Path to the source file

        Returns:
            FramerMotionParseResult with all extracted data
        """
        result = FramerMotionParseResult()
        result.file_path = file_path

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = 'tsx'
            result.has_typescript = True
        elif file_path.endswith('.ts'):
            result.file_type = 'ts'
            result.has_typescript = True
        elif file_path.endswith('.jsx'):
            result.file_type = 'jsx'
        else:
            result.file_type = 'js'

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract animation constructs ──────────────────────────
        anim_result = self.animation_extractor.extract(content, file_path)
        result.variants = anim_result.get('variants', [])
        result.keyframes = anim_result.get('keyframes', [])
        result.transitions = anim_result.get('transitions', [])
        result.animate_presences = anim_result.get('animate_presences', [])
        result.animation_controls = anim_result.get('animation_controls', [])
        result.motion_components = anim_result.get('motion_components', [])

        # ── Extract gesture constructs ────────────────────────────
        gesture_result = self.gesture_extractor.extract(content, file_path)
        result.drags = gesture_result.get('drags', [])
        result.hovers = gesture_result.get('hovers', [])
        result.taps = gesture_result.get('taps', [])
        result.gestures = gesture_result.get('gestures', [])
        result.drag_controls = gesture_result.get('drag_controls', [])

        # ── Extract layout constructs ─────────────────────────────
        layout_result = self.layout_extractor.extract(content, file_path)
        result.layout_anims = layout_result.get('layout_anims', [])
        result.shared_layouts = layout_result.get('shared_layouts', [])
        result.exit_anims = layout_result.get('exit_anims', [])

        # ── Extract scroll constructs ─────────────────────────────
        scroll_result = self.scroll_extractor.extract(content, file_path)
        result.scrolls = scroll_result.get('scrolls', [])
        result.in_views = scroll_result.get('in_views', [])
        result.parallaxes = scroll_result.get('parallaxes', [])
        result.scroll_events = scroll_result.get('scroll_events', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.hooks = api_result.get('hooks', [])
        result.types = api_result.get('types', [])
        result.integrations = api_result.get('integrations', [])
        result.motion_elements = api_result.get('motion_elements', [])
        result.version_info = api_result.get('version_info', {})

        # Derive version hint
        pkg = result.version_info.get('package', 'unknown')
        if pkg == 'motion':
            result.framer_motion_version = 'v11+'
        elif pkg == 'framer-motion':
            result.framer_motion_version = 'v1-v10'

        # Derive boolean features
        result.has_variants = bool(result.variants)
        result.has_gestures = bool(result.drags or result.hovers or result.taps or result.gestures)
        result.has_layout_animations = bool(result.layout_anims or result.shared_layouts)
        result.has_scroll_animations = bool(result.scrolls or result.in_views or result.parallaxes)
        result.has_animate_presence = bool(result.animate_presences)
        result.has_drag = bool(result.drags or result.drag_controls)

        # Build detected_features list
        if result.has_variants:
            result.detected_features.append('variants')
        if result.has_gestures:
            result.detected_features.append('gestures')
        if result.has_layout_animations:
            result.detected_features.append('layout_animations')
        if result.has_scroll_animations:
            result.detected_features.append('scroll_animations')
        if result.has_animate_presence:
            result.detected_features.append('animate_presence')
        if result.has_drag:
            result.detected_features.append('drag')
        if result.keyframes:
            result.detected_features.append('keyframes')
        if result.transitions:
            result.detected_features.append('transitions')
        if result.exit_anims:
            result.detected_features.append('exit_animations')
        if result.hooks:
            result.detected_features.append('hooks')
        if result.motion_elements:
            result.detected_features.append('motion_components')
        if result.parallaxes:
            result.detected_features.append('parallax')
        if result.integrations:
            result.detected_features.append('integrations')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Framer Motion ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_framer_motion_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Framer Motion code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Framer Motion animation code
        """
        # Check for framer-motion imports
        if re.search(r"from\s+['\"]framer-motion['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]framer-motion['\"]\s*\)", content):
            return True

        # Check for motion package (v11+)
        if re.search(r"from\s+['\"]motion['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]motion['\"]\s*\)", content):
            return True

        # Check for framer-motion subpath imports
        if re.search(r"from\s+['\"](?:framer-motion|motion)/[^'\"]+['\"]", content):
            return True

        # Check for motion.div, motion.span JSX components
        if re.search(r'<motion\.\w+', content):
            return True

        # Check for motion() factory
        if re.search(r'motion\(\s*\w+', content):
            # Avoid false positive with CSS `motion` property
            if re.search(r"from\s+['\"](?:framer-motion|motion)", content):
                return True

        # Check for AnimatePresence component
        if re.search(r'<AnimatePresence', content):
            return True

        # Check for LazyMotion / MotionConfig / LayoutGroup
        if re.search(r'<(?:LazyMotion|MotionConfig|LayoutGroup)\b', content):
            return True

        # Check for Reorder components
        if re.search(r'<Reorder\.(?:Group|Item)\b', content):
            return True

        # Check for common framer-motion hooks
        if re.search(r'\b(?:useMotionValue|useTransform|useSpring|useAnimate|useScroll|useInView)\s*\(', content):
            return True

        # Check for animation props (whileHover, whileTap, etc.) on motion components
        if re.search(r'(?:whileHover|whileTap|whileDrag|whileFocus|whileInView)\s*=', content):
            return True

        # Check for animate/initial/exit props on motion components
        if re.search(r'<motion\.\w+[^>]*(?:animate|initial|exit|variants)\s*=', content):
            return True

        # Check for dynamic import
        if re.search(r"import\s*\(\s*['\"](?:framer-motion|motion)['\"]", content):
            return True

        # Check for framer-motion-3d
        if re.search(r"from\s+['\"]framer-motion-3d['\"]", content):
            return True

        # Check for framer SDK
        if re.search(r"from\s+['\"]framer['\"]", content):
            return True

        return False
