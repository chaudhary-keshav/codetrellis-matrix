"""
Enhanced GSAP animation platform parser for CodeTrellis.

Parses JavaScript/TypeScript/JSX/TSX files containing GSAP
animation code. Delegates to 5 specialized extractors for comprehensive
animation platform analysis.

Supports:
- GreenSock v1 (TweenMax/TweenLite, TimelineMax/TimelineLite)
- GSAP v2 (transition package)
- GSAP v3 (gsap.to/from/fromTo/set, gsap.timeline(), gsap.registerPlugin())
- ScrollTrigger, ScrollSmoother, Observer, ScrollToPlugin
- Club/Premium plugins (Flip, SplitText, DrawSVG, MorphSVG, MotionPath, etc.)
- Free plugins (TextPlugin, CSSRulePlugin, AttrPlugin, etc.)
- gsap.context() / gsap.matchMedia() (v3.11+)
- @gsap/react (useGSAP hook)
- TypeScript types
- Framework integrations (React, Vue, Angular, Svelte, Next.js)

AST via regex + optional tree-sitter-javascript / tsserver LSP.
v4.77: Full GSAP support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from codetrellis.extractors.gsap import (
    GsapAnimationExtractor,
    GsapTimelineExtractor,
    GsapPluginExtractor,
    GsapScrollExtractor,
    GsapAPIExtractor,
    GsapTweenInfo,
    GsapSetInfo,
    GsapStaggerInfo,
    GsapEaseInfo,
    GsapTimelineInfo,
    GsapLabelInfo,
    GsapCallbackInfo,
    GsapNestedTimelineInfo,
    GsapPluginInfo,
    GsapRegistrationInfo,
    GsapEffectInfo,
    GsapUtilityInfo,
    GsapScrollTriggerInfo,
    GsapScrollSmootherInfo,
    GsapObserverInfo,
    GsapScrollBatchInfo,
    GsapImportInfo,
    GsapIntegrationInfo,
    GsapTypeInfo,
    GsapContextInfo,
    GsapMatchMediaInfo,
)


@dataclass
class GsapParseResult:
    """Complete result of parsing a GSAP file."""
    file_path: str = ""
    file_type: str = ""          # 'js', 'jsx', 'ts', 'tsx'

    # Animation constructs (from animation_extractor)
    tweens: List[GsapTweenInfo] = field(default_factory=list)
    sets: List[GsapSetInfo] = field(default_factory=list)
    staggers: List[GsapStaggerInfo] = field(default_factory=list)
    eases: List[GsapEaseInfo] = field(default_factory=list)

    # Timeline constructs (from timeline_extractor)
    timelines: List[GsapTimelineInfo] = field(default_factory=list)
    labels: List[GsapLabelInfo] = field(default_factory=list)
    callbacks: List[GsapCallbackInfo] = field(default_factory=list)
    nested_timelines: List[GsapNestedTimelineInfo] = field(default_factory=list)

    # Plugin constructs (from plugin_extractor)
    plugins: List[GsapPluginInfo] = field(default_factory=list)
    registrations: List[GsapRegistrationInfo] = field(default_factory=list)
    effects: List[GsapEffectInfo] = field(default_factory=list)
    utilities: List[GsapUtilityInfo] = field(default_factory=list)

    # Scroll constructs (from scroll_extractor)
    scroll_triggers: List[GsapScrollTriggerInfo] = field(default_factory=list)
    scroll_smoothers: List[GsapScrollSmootherInfo] = field(default_factory=list)
    observers: List[GsapObserverInfo] = field(default_factory=list)
    scroll_batches: List[GsapScrollBatchInfo] = field(default_factory=list)

    # API constructs (from api_extractor)
    imports: List[GsapImportInfo] = field(default_factory=list)
    integrations: List[GsapIntegrationInfo] = field(default_factory=list)
    types: List[GsapTypeInfo] = field(default_factory=list)
    contexts: List[GsapContextInfo] = field(default_factory=list)
    match_medias: List[GsapMatchMediaInfo] = field(default_factory=list)
    version_info: Dict = field(default_factory=dict)

    # Detected metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    gsap_version: str = ""
    has_typescript: bool = False
    has_tweens: bool = False
    has_timelines: bool = False
    has_scroll_trigger: bool = False
    has_scroll_smoother: bool = False
    has_plugins: bool = False
    has_staggers: bool = False
    has_context: bool = False
    has_match_media: bool = False
    has_club_plugins: bool = False


class EnhancedGsapParser:
    """
    Full-featured GSAP animation platform parser.

    Coordinates 5 specialized extractors to provide comprehensive
    animation platform analysis. Follows the Framer Motion parser architecture.
    """

    # Framework/library detection patterns
    FRAMEWORK_PATTERNS = {
        'gsap': re.compile(r"""(?:from\s+['"]gsap['"]|require\s*\(\s*['"]gsap['"])"""),
        'gsap-subpath': re.compile(r"""(?:from\s+['"]gsap/[^'"]+['"])"""),
        'gsap-trial': re.compile(r"""(?:from\s+['"]gsap-trial['"])"""),
        '@gsap/react': re.compile(r"""(?:from\s+['"]@gsap/react['"]|useGSAP\s*\()"""),
        '@gsap/vue': re.compile(r"""(?:from\s+['"]@gsap/vue['"])"""),
        '@gsap/angular': re.compile(r"""(?:from\s+['"]@gsap/angular['"])"""),
        '@gsap/svelte': re.compile(r"""(?:from\s+['"]@gsap/svelte['"])"""),
        'scrolltrigger': re.compile(r"""(?:ScrollTrigger|from\s+['"]gsap/ScrollTrigger['"])"""),
        'scrollsmoother': re.compile(r"""(?:ScrollSmoother|from\s+['"]gsap/ScrollSmoother['"])"""),
        'draggable': re.compile(r"""(?:Draggable\.create|from\s+['"]gsap/Draggable['"])"""),
        'flip': re.compile(r"""(?:Flip\.from|Flip\.fit|from\s+['"]gsap/Flip['"])"""),
        'observer': re.compile(r"""(?:Observer\.create|from\s+['"]gsap/Observer['"])"""),
        'split-text': re.compile(r"""(?:new\s+SplitText|from\s+['"]gsap/SplitText['"])"""),
        'motion-path': re.compile(r"""(?:MotionPathPlugin|from\s+['"]gsap/MotionPathPlugin['"])"""),
        'draw-svg': re.compile(r"""(?:DrawSVGPlugin|from\s+['"]gsap/DrawSVGPlugin['"])"""),
        'morph-svg': re.compile(r"""(?:MorphSVGPlugin|from\s+['"]gsap/MorphSVGPlugin['"])"""),
        'pixi': re.compile(r"""(?:PixiPlugin|from\s+['"]gsap/PixiPlugin['"])"""),
        'text-plugin': re.compile(r"""(?:TextPlugin|from\s+['"]gsap/TextPlugin['"])"""),
        'css-rule-plugin': re.compile(r"""(?:CSSRulePlugin|from\s+['"]gsap/CSSRulePlugin['"])"""),
        'greensock-v1': re.compile(r"""(?:TweenMax|TweenLite|TimelineMax|TimelineLite)\b"""),
        'cdn-gsap': re.compile(r"""cdnjs\.cloudflare\.com/ajax/libs/gsap"""),
        'unpkg-gsap': re.compile(r"""unpkg\.com/gsap"""),
        'cdn-greensock': re.compile(r"""cdn\.jsdelivr\.net/npm/gsap"""),
    }

    def __init__(self):
        """Initialize all 5 extractors."""
        self.animation_extractor = GsapAnimationExtractor()
        self.timeline_extractor = GsapTimelineExtractor()
        self.plugin_extractor = GsapPluginExtractor()
        self.scroll_extractor = GsapScrollExtractor()
        self.api_extractor = GsapAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> GsapParseResult:
        """
        Parse a file for GSAP animation constructs.

        Args:
            content: Source code content
            file_path: Path to the source file

        Returns:
            GsapParseResult with all extracted data
        """
        result = GsapParseResult()
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
        result.tweens = anim_result.get('tweens', [])
        result.sets = anim_result.get('sets', [])
        result.staggers = anim_result.get('staggers', [])
        result.eases = anim_result.get('eases', [])

        # ── Extract timeline constructs ───────────────────────────
        tl_result = self.timeline_extractor.extract(content, file_path)
        result.timelines = tl_result.get('timelines', [])
        result.labels = tl_result.get('labels', [])
        result.callbacks = tl_result.get('callbacks', [])
        result.nested_timelines = tl_result.get('nested', [])

        # ── Extract plugin constructs ─────────────────────────────
        plugin_result = self.plugin_extractor.extract(content, file_path)
        result.plugins = plugin_result.get('plugins', [])
        result.registrations = plugin_result.get('registrations', [])
        result.effects = plugin_result.get('effects', [])
        result.utilities = plugin_result.get('utilities', [])

        # ── Extract scroll constructs ─────────────────────────────
        scroll_result = self.scroll_extractor.extract(content, file_path)
        result.scroll_triggers = scroll_result.get('scroll_triggers', [])
        result.scroll_smoothers = scroll_result.get('smoothers', [])
        result.observers = scroll_result.get('observers', [])
        result.scroll_batches = scroll_result.get('batches', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])
        result.contexts = api_result.get('contexts', [])
        result.match_medias = api_result.get('match_medias', [])
        result.version_info = api_result.get('version_info', {})

        # Derive version hint
        pkg = result.version_info.get('package', 'unknown')
        if pkg == 'gsap-v3':
            result.gsap_version = 'v3'
        elif pkg == 'gsap-v1':
            result.gsap_version = 'v1'
        elif 'greensock-v1' in result.detected_frameworks:
            result.gsap_version = 'v1'
        elif 'gsap' in result.detected_frameworks:
            result.gsap_version = 'v3'

        min_ver = result.version_info.get('min_version', '')
        if min_ver:
            result.gsap_version = min_ver

        # Derive boolean features
        result.has_tweens = bool(result.tweens or result.sets)
        result.has_timelines = bool(result.timelines)
        result.has_scroll_trigger = bool(result.scroll_triggers)
        result.has_scroll_smoother = bool(result.scroll_smoothers)
        result.has_plugins = bool(result.plugins or result.registrations)
        result.has_staggers = bool(result.staggers)
        result.has_context = bool(result.contexts)
        result.has_match_media = bool(result.match_medias)
        result.has_club_plugins = any(
            p.is_premium for p in result.plugins if hasattr(p, 'is_premium') and p.is_premium
        )

        # Build detected_features list
        if result.has_tweens:
            result.detected_features.append('tweens')
        if result.has_timelines:
            result.detected_features.append('timelines')
        if result.has_scroll_trigger:
            result.detected_features.append('scroll_trigger')
        if result.has_scroll_smoother:
            result.detected_features.append('scroll_smoother')
        if result.has_plugins:
            result.detected_features.append('plugins')
        if result.has_staggers:
            result.detected_features.append('staggers')
        if result.has_context:
            result.detected_features.append('context')
        if result.has_match_media:
            result.detected_features.append('match_media')
        if result.has_club_plugins:
            result.detected_features.append('club_plugins')
        if result.eases:
            result.detected_features.append('custom_eases')
        if result.callbacks:
            result.detected_features.append('callbacks')
        if result.effects:
            result.detected_features.append('effects')
        if result.utilities:
            result.detected_features.append('utilities')
        if result.observers:
            result.detected_features.append('observer')
        if result.nested_timelines:
            result.detected_features.append('nested_timelines')
        if result.integrations:
            result.detected_features.append('integrations')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which GSAP ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_gsap_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains GSAP code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains GSAP animation code
        """
        # Check for gsap v3 imports
        if re.search(r"from\s+['\"]gsap['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]gsap['\"]\s*\)", content):
            return True

        # Check for gsap subpath imports
        if re.search(r"from\s+['\"]gsap/[^'\"]+['\"]", content):
            return True

        # Check for @gsap/* packages
        if re.search(r"from\s+['\"]@gsap/[^'\"]+['\"]", content):
            return True

        # Check for gsap-trial (Club GreenSock)
        if re.search(r"from\s+['\"]gsap-trial['\"]", content):
            return True

        # Check for gsap v3 API calls
        if re.search(r'\bgsap\s*\.\s*(?:to|from|fromTo|set|timeline|registerPlugin|registerEffect|registerEase|context|matchMedia|defaults|config)\s*\(', content):
            return True

        # Check for v1/v2 legacy classes
        if re.search(r'\b(?:TweenMax|TweenLite|TimelineMax|TimelineLite)\s*\.', content):
            return True
        if re.search(r'\bnew\s+(?:TweenMax|TweenLite|TimelineMax|TimelineLite)\s*\(', content):
            return True

        # Check for ScrollTrigger
        if re.search(r'\bScrollTrigger\s*\.(?:create|defaults|batch|scrollerProxy|addEventListener)\s*\(', content):
            return True

        # Check for ScrollSmoother
        if re.search(r'\bScrollSmoother\s*\.(?:create|get)\s*\(', content):
            return True

        # Check for Draggable
        if re.search(r'\bDraggable\s*\.(?:create|get)\s*\(', content):
            return True

        # Check for Flip
        if re.search(r'\bFlip\s*\.(?:from|fit|to|getState)\s*\(', content):
            return True

        # Check for Observer
        if re.search(r'\bObserver\s*\.create\s*\(', content):
            return True

        # Check for SplitText
        if re.search(r'\bnew\s+SplitText\s*\(', content):
            return True

        # Check for CDN includes
        if re.search(r'(?:cdnjs\.cloudflare\.com|unpkg\.com|cdn\.jsdelivr\.net)/[^"\']*gsap', content, re.IGNORECASE):
            return True

        # Check for GreenSock CDN
        if re.search(r'(?:cdnjs\.cloudflare\.com|unpkg\.com|cdn\.jsdelivr\.net)/[^"\']*(?:greensock|TweenMax)', content, re.IGNORECASE):
            return True

        # Check for scrollTrigger inline config
        if re.search(r'scrollTrigger\s*:\s*\{', content):
            return True

        # Check for gsap.utils
        if re.search(r'\bgsap\s*\.\s*utils\s*\.', content):
            return True

        # Check for dynamic import
        if re.search(r"import\s*\(\s*['\"]gsap", content):
            return True

        # Check for useGSAP hook
        if re.search(r'\buseGSAP\s*\(', content):
            return True

        return False
