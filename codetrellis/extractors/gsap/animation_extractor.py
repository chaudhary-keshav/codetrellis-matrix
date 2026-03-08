"""
GSAP Animation Extractor — Tweens, sets, stagger, easing.

Extracts:
- gsap.to() / gsap.from() / gsap.fromTo() tweens (v3+)
- gsap.set() instant property sets
- TweenMax.to() / TweenLite.to() (v1-v2 legacy)
- Stagger animations (stagger property, gsap.utils.toArray + stagger)
- Ease configurations (power, elastic, bounce, back, custom)
- Duration / delay / repeat / yoyo / overwrite

v4.77: Full GSAP tween support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GsapTweenInfo:
    """A GSAP tween animation (gsap.to/from/fromTo, TweenMax/Lite)."""
    name: str = ""                   # Variable name or 'anonymous'
    file: str = ""
    line_number: int = 0
    tween_type: str = ""             # 'to', 'from', 'fromTo', 'set'
    api_style: str = ""              # 'v3' (gsap.*), 'v1' (TweenMax.*), 'v2' (TweenLite.*)
    target: str = ""                 # CSS selector or ref
    has_duration: bool = False
    has_delay: bool = False
    has_ease: str = ""               # Ease name (e.g., 'power2.out', 'elastic')
    has_stagger: bool = False
    has_repeat: bool = False
    has_yoyo: bool = False
    has_overwrite: bool = False
    has_onComplete: bool = False
    has_onUpdate: bool = False
    has_scrollTrigger: bool = False
    properties_animated: List[str] = field(default_factory=list)
    is_exported: bool = False


@dataclass
class GsapSetInfo:
    """A GSAP instant set (gsap.set / TweenMax.set)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    api_style: str = ""
    target: str = ""
    properties_set: List[str] = field(default_factory=list)


@dataclass
class GsapStaggerInfo:
    """Stagger animation configuration."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    stagger_type: str = ""           # 'simple', 'object', 'function', 'grid'
    amount: str = ""                 # Stagger amount
    from_direction: str = ""         # 'start', 'center', 'end', 'edges', 'random'
    has_grid: bool = False
    has_ease: bool = False
    has_repeat: bool = False


@dataclass
class GsapEaseInfo:
    """Ease/easing configuration."""
    name: str = ""                   # Ease name
    file: str = ""
    line_number: int = 0
    ease_type: str = ""              # 'power', 'elastic', 'bounce', 'back', 'expo', 'circ', 'sine', 'custom', 'steps', 'rough', 'slow', 'expoScale'
    is_custom: bool = False
    is_plugin: bool = False


class GsapAnimationExtractor:
    """
    Extracts GSAP tween/animation constructs from JavaScript/TypeScript.

    Supports GSAP v1 (TweenMax/TweenLite), v2, and v3+ (gsap.*) APIs.
    """

    # v3 gsap.to/from/fromTo/set patterns
    GSAP_V3_TWEEN = re.compile(
        r'(?:(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'gsap\.(to|from|fromTo|set)\s*\()',
        re.MULTILINE
    )

    # v1/v2 TweenMax/TweenLite.to/from/fromTo/set
    GSAP_LEGACY_TWEEN = re.compile(
        r'(?:(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'(TweenMax|TweenLite|TweenNano)\.(to|from|fromTo|set|staggerTo|staggerFrom|staggerFromTo)\s*\()',
        re.MULTILINE
    )

    # Stagger detection in tween vars
    STAGGER_PATTERN = re.compile(
        r'stagger\s*:\s*(?:(\{[^}]*\})|([^\s,}]+))',
        re.DOTALL
    )

    # Ease pattern
    EASE_PATTERN = re.compile(
        r'ease\s*:\s*["\']?([a-zA-Z0-9_.]+(?:\([^)]*\))?)["\']?'
    )

    # Callback patterns
    CALLBACK_PATTERN = re.compile(
        r'(onComplete|onUpdate|onStart|onRepeat|onReverseComplete)\s*:'
    )

    # ScrollTrigger in vars
    SCROLL_TRIGGER_IN_VARS = re.compile(
        r'scrollTrigger\s*:'
    )

    # Property animation detection (common GSAP properties)
    ANIMATED_PROPS = re.compile(
        r'(?:^|\s)(x|y|z|rotation|rotationX|rotationY|rotationZ|scale|scaleX|scaleY|'
        r'skewX|skewY|opacity|autoAlpha|transformOrigin|width|height|left|top|right|bottom|'
        r'backgroundColor|color|borderRadius|fontSize|letterSpacing|lineHeight|padding|margin|'
        r'clipPath|attr|innerHTML|textContent|morphSVG|drawSVG|motionPath)\s*:'
    )

    # Duration
    DURATION_PATTERN = re.compile(r'duration\s*:\s*[\d.]+')
    DELAY_PATTERN = re.compile(r'delay\s*:\s*[\d.]+')
    REPEAT_PATTERN = re.compile(r'repeat\s*:\s*(-?\d+)')
    YOYO_PATTERN = re.compile(r'yoyo\s*:\s*true')
    OVERWRITE_PATTERN = re.compile(r'overwrite\s*:')

    # Export detection
    EXPORT_PATTERN = re.compile(r'export\s+(?:const|let|var|function|default)')

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all GSAP animation constructs from source code."""
        tweens = []
        sets = []
        staggers = []
        eases = []

        lines = content.split('\n')

        # ── v3 gsap.to/from/fromTo/set ──────────────────────────
        for match in self.GSAP_V3_TWEEN.finditer(content):
            var_name = match.group(1) or 'anonymous'
            method = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Get surrounding context (next ~300 chars for property inspection)
            ctx = content[match.start():match.start() + 500]

            if method == 'set':
                props = [p.group(1) for p in self.ANIMATED_PROPS.finditer(ctx)]
                sets.append(GsapSetInfo(
                    name=var_name,
                    file=file_path,
                    line_number=line_num,
                    api_style='v3',
                    target=self._extract_target(ctx),
                    properties_set=props[:10],
                ))
            else:
                tween = self._build_tween(var_name, method, 'v3', ctx, file_path, line_num, content, match.start())
                tweens.append(tween)

        # ── v1/v2 TweenMax/TweenLite ────────────────────────────
        for match in self.GSAP_LEGACY_TWEEN.finditer(content):
            var_name = match.group(1) or 'anonymous'
            class_name = match.group(2)
            method = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]

            api_style = 'v1' if class_name in ('TweenMax', 'TweenNano') else 'v2'

            if method == 'set':
                props = [p.group(1) for p in self.ANIMATED_PROPS.finditer(ctx)]
                sets.append(GsapSetInfo(
                    name=var_name,
                    file=file_path,
                    line_number=line_num,
                    api_style=api_style,
                    target=self._extract_target(ctx),
                    properties_set=props[:10],
                ))
            elif 'stagger' in method.lower():
                stag = GsapStaggerInfo(
                    name=var_name,
                    file=file_path,
                    line_number=line_num,
                    stagger_type='legacy',
                )
                staggers.append(stag)
                tween = self._build_tween(var_name, method.replace('stagger', '').lower() or 'to', api_style, ctx, file_path, line_num, content, match.start())
                tween.has_stagger = True
                tweens.append(tween)
            else:
                tween = self._build_tween(var_name, method, api_style, ctx, file_path, line_num, content, match.start())
                tweens.append(tween)

        # ── Stagger configs ─────────────────────────────────────
        for match in self.STAGGER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            obj_val = match.group(1)
            simple_val = match.group(2)
            stag = GsapStaggerInfo(
                name='stagger',
                file=file_path,
                line_number=line_num,
                stagger_type='object' if obj_val else 'simple',
                amount=simple_val or '',
                has_grid='grid' in (obj_val or ''),
                from_direction=self._extract_stagger_from(obj_val) if obj_val else '',
                has_ease='ease' in (obj_val or ''),
                has_repeat='repeat' in (obj_val or ''),
            )
            staggers.append(stag)

        # ── Ease patterns ───────────────────────────────────────
        seen_eases = set()
        for match in self.EASE_PATTERN.finditer(content):
            ease_name = match.group(1).strip("'\"")
            if ease_name in seen_eases:
                continue
            seen_eases.add(ease_name)
            line_num = content[:match.start()].count('\n') + 1
            ease_type = self._classify_ease(ease_name)
            eases.append(GsapEaseInfo(
                name=ease_name,
                file=file_path,
                line_number=line_num,
                ease_type=ease_type,
                is_custom='Custom' in ease_name or '(' in ease_name,
                is_plugin=ease_type in ('rough', 'slow', 'expoScale', 'custom'),
            ))

        return {
            'tweens': tweens[:100],
            'sets': sets[:50],
            'staggers': staggers[:50],
            'eases': eases[:30],
        }

    def _build_tween(self, name: str, method: str, api_style: str, ctx: str,
                     file_path: str, line_num: int, full_content: str, offset: int) -> GsapTweenInfo:
        """Build a GsapTweenInfo from context."""
        props = [p.group(1) for p in self.ANIMATED_PROPS.finditer(ctx)]
        callbacks = [c.group(1) for c in self.CALLBACK_PATTERN.finditer(ctx)]

        # Check if line is exported
        line_start = full_content.rfind('\n', 0, offset) + 1
        line_text = full_content[line_start:offset + 200]
        is_exported = bool(self.EXPORT_PATTERN.search(line_text[:100]))

        ease_match = self.EASE_PATTERN.search(ctx)

        return GsapTweenInfo(
            name=name,
            file=file_path,
            line_number=line_num,
            tween_type=method,
            api_style=api_style,
            target=self._extract_target(ctx),
            has_duration=bool(self.DURATION_PATTERN.search(ctx)),
            has_delay=bool(self.DELAY_PATTERN.search(ctx)),
            has_ease=ease_match.group(1) if ease_match else '',
            has_stagger=bool(self.STAGGER_PATTERN.search(ctx)),
            has_repeat=bool(self.REPEAT_PATTERN.search(ctx)),
            has_yoyo=bool(self.YOYO_PATTERN.search(ctx)),
            has_overwrite=bool(self.OVERWRITE_PATTERN.search(ctx)),
            has_onComplete='onComplete' in callbacks,
            has_onUpdate='onUpdate' in callbacks,
            has_scrollTrigger=bool(self.SCROLL_TRIGGER_IN_VARS.search(ctx)),
            properties_animated=props[:10],
            is_exported=is_exported,
        )

    def _extract_target(self, ctx: str) -> str:
        """Extract the target selector from the first argument."""
        # Match first string argument: gsap.to(".class", {...})
        m = re.search(r'\(\s*["\']([^"\']+)["\']', ctx)
        if m:
            return m.group(1)
        # Match ref: gsap.to(ref.current, {...})
        m = re.search(r'\(\s*(\w+(?:\.\w+)*)', ctx)
        if m:
            return m.group(1)
        return ''

    def _extract_stagger_from(self, obj_str: str) -> str:
        """Extract the 'from' direction from stagger config."""
        m = re.search(r'from\s*:\s*["\']?(\w+)', obj_str)
        return m.group(1) if m else ''

    def _classify_ease(self, ease_name: str) -> str:
        """Classify an ease name into its type."""
        lower = ease_name.lower()
        for kind in ('power', 'elastic', 'bounce', 'back', 'expo', 'circ', 'sine',
                     'steps', 'rough', 'slow', 'expoScale', 'custom'):
            if kind.lower() in lower:
                return kind
        if 'linear' in lower:
            return 'linear'
        if 'ease' in lower:
            return 'ease'
        return 'custom'
