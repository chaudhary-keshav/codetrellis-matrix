"""
Framer Motion animation extractor for CodeTrellis.

Extracts animation constructs from framer-motion / motion code:
- Variant definitions (initial, animate, exit, hover, tap, etc.)
- Keyframe arrays on motion.* components
- Transition configs (spring, tween, inertia, duration, delay)
- AnimatePresence usage and mode
- useAnimation / useAnimationControls hooks
- motion.div, motion.span, etc. component usage

Supports framer-motion v1 → v11+ and motion v11+ (renamed).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FramerVariantInfo:
    """A variant definition (named animation state)."""
    name: str = ""
    variant_key: str = ""          # 'initial', 'animate', 'exit', 'hover', 'tap', etc.
    properties: List[str] = field(default_factory=list)  # e.g. ['opacity', 'x', 'scale']
    line_number: int = 0
    file_path: str = ""
    has_transition: bool = False


@dataclass
class FramerKeyframeInfo:
    """Keyframe animation on a motion component."""
    property_name: str = ""        # 'x', 'opacity', 'rotate', etc.
    values: str = ""               # stringified keyframe array
    line_number: int = 0
    file_path: str = ""
    component_type: str = ""       # 'motion.div', 'motion.span', etc.


@dataclass
class FramerTransitionInfo:
    """Transition configuration."""
    transition_type: str = ""      # 'spring', 'tween', 'inertia', 'keyframes'
    duration: str = ""
    delay: str = ""
    stiffness: str = ""
    damping: str = ""
    line_number: int = 0
    file_path: str = ""
    has_repeat: bool = False
    has_stagger: bool = False


@dataclass
class FramerAnimatePresenceInfo:
    """AnimatePresence wrapper usage."""
    mode: str = ""                 # 'wait', 'sync', 'popLayout', '' (default)
    line_number: int = 0
    file_path: str = ""
    has_initial: bool = False      # initial={false}
    has_exit_before_enter: bool = False  # legacy exitBeforeEnter
    has_on_exit_complete: bool = False
    children_count: int = 0


@dataclass
class FramerAnimationControlInfo:
    """useAnimation / useAnimationControls hook usage."""
    hook_name: str = ""            # 'useAnimation', 'useAnimationControls'
    variable_name: str = ""
    line_number: int = 0
    file_path: str = ""
    methods_called: List[str] = field(default_factory=list)  # 'start', 'stop', 'set'


# ── Regex patterns ──────────────────────────────────────────────

# Variant object definitions: const variants = { ... }
VARIANT_DEF_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*(?::\s*\w+)?\s*=\s*\{""",
    re.MULTILINE
)

# Variant keys inside objects: initial: { ... }, animate: { ... }
VARIANT_KEY_PATTERN = re.compile(
    r"""(?:^|\n)\s*(initial|animate|exit|hover|tap|focus|drag|whileHover|whileTap|whileFocus|whileDrag|whileInView|hidden|visible|show|open|closed|active|inactive|collapsed|expanded|enter|leave)\s*:\s*\{""",
    re.MULTILINE
)

# Animated properties inside variant values
ANIMATED_PROP_PATTERN = re.compile(
    r"""(opacity|x|y|z|scale|scaleX|scaleY|rotate|rotateX|rotateY|rotateZ|skew|skewX|skewY|translateX|translateY|width|height|top|left|right|bottom|color|backgroundColor|borderColor|borderRadius|fontSize|padding|margin|flex|pathLength|pathOffset|strokeDashoffset|strokeDasharray|fill|stroke|d|cx|cy|r|rx|ry)\s*:""",
)

# motion.div, motion.span, etc. usage
MOTION_COMPONENT_PATTERN = re.compile(
    r"""<(motion\.(?:div|span|p|h[1-6]|a|button|img|ul|ol|li|nav|header|footer|main|section|article|aside|form|input|textarea|select|svg|path|circle|rect|g|line|ellipse|polygon|polyline|text|tspan|use|defs|clipPath|mask|filter|foreignObject|pattern|symbol|marker|linearGradient|radialGradient|stop|animate|animateTransform|set|custom))\b""",
    re.MULTILINE
)

# motion() factory usage: motion("div"), motion.create("div")
MOTION_FACTORY_PATTERN = re.compile(
    r"""motion\s*\(\s*['"]([\w.]+)['"]\s*\)""",
)

# Keyframe arrays in props: x={[0, 100, 0]} OR x: [0, 100, 0] (inside animate={{ }})
KEYFRAME_PROP_PATTERN = re.compile(
    r"""(opacity|x|y|z|scale|scaleX|scaleY|rotate|rotateX|rotateY|rotateZ|width|height|pathLength|d|fill|stroke)\s*[=:]\s*\{?\s*\[([\d\s,.\-'"]+)\]""",
    re.MULTILINE
)

# transition={{ ... }}
TRANSITION_PROP_PATTERN = re.compile(
    r"""transition\s*=?\s*\{\{?\s*([^}]+)\}\}?""",
    re.MULTILINE
)

# Transition type detection
TRANSITION_TYPE_PATTERN = re.compile(
    r"""type\s*:\s*['"]?(spring|tween|inertia|keyframes|just)['"]?""",
)

# AnimatePresence
ANIMATE_PRESENCE_PATTERN = re.compile(
    r"""<AnimatePresence\b([^>]*)>""",
    re.MULTILINE
)

# useAnimation / useAnimationControls
ANIMATION_CONTROLS_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*(useAnimation|useAnimationControls)\s*\(\s*\)""",
    re.MULTILINE
)

# useAnimate (v10+) — destructured: const [scope, animate] = useAnimate()
USE_ANIMATE_PATTERN = re.compile(
    r"""(?:const|let|var)\s+\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*(useAnimate)\s*\(\s*\)""",
    re.MULTILINE
)

# Controls method calls: controls.start(), controls.stop()
CONTROLS_METHOD_PATTERN = re.compile(
    r"""(\w+)\.(start|stop|set|mount|getState)\s*\(""",
)

# animate prop values: animate={{ opacity: 1 }}
ANIMATE_PROP_PATTERN = re.compile(
    r"""(initial|animate|exit|whileHover|whileTap|whileFocus|whileDrag|whileInView)\s*=\s*\{\{?\s*([^}]+)\}\}?""",
    re.MULTILINE
)

# Variant reference: animate="visible" or variants={variants}
VARIANT_REF_PATTERN = re.compile(
    r"""(?:initial|animate|exit|whileHover|whileTap|whileFocus|whileDrag|whileInView)\s*=\s*['"]([\w]+)['"]""",
)


class FramerAnimationExtractor:
    """Extract Framer Motion animation constructs."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract all animation-related constructs from source code.

        Returns dict with keys: variants, keyframes, transitions,
        animate_presences, animation_controls, motion_components.
        """
        result = {
            'variants': [],
            'keyframes': [],
            'transitions': [],
            'animate_presences': [],
            'animation_controls': [],
            'motion_components': [],
        }

        if not content.strip():
            return result

        lines = content.split('\n')

        # ── Extract variant definitions ─────────────────────────
        result['variants'] = self._extract_variants(content, file_path, lines)

        # ── Extract keyframes ───────────────────────────────────
        result['keyframes'] = self._extract_keyframes(content, file_path, lines)

        # ── Extract transitions ──────────────────────────────────
        result['transitions'] = self._extract_transitions(content, file_path, lines)

        # ── Extract AnimatePresence ──────────────────────────────
        result['animate_presences'] = self._extract_animate_presences(content, file_path, lines)

        # ── Extract animation controls ───────────────────────────
        result['animation_controls'] = self._extract_animation_controls(content, file_path, lines)

        # ── Extract motion component usage ───────────────────────
        result['motion_components'] = self._extract_motion_components(content, file_path, lines)

        return result

    def _extract_variants(self, content: str, file_path: str, lines: list) -> List[FramerVariantInfo]:
        """Extract variant definitions from source."""
        variants = []

        # Find variant objects with variant keys
        for m in VARIANT_KEY_PATTERN.finditer(content):
            variant_key = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Extract animated properties within this variant
            brace_start = m.end() - 1
            props = self._extract_variant_props(content, brace_start)

            # Find the enclosing variable name
            var_name = self._find_enclosing_var(content, m.start())

            variants.append(FramerVariantInfo(
                name=var_name,
                variant_key=variant_key,
                properties=props,
                line_number=line_num,
                file_path=file_path,
                has_transition='transition' in content[brace_start:brace_start + 500],
            ))

        # Also extract inline animate={{ ... }}
        for m in ANIMATE_PROP_PATTERN.finditer(content):
            prop_name = m.group(1)
            value = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            props = [p.strip().split(':')[0].strip()
                     for p in value.split(',')
                     if ':' in p and p.strip().split(':')[0].strip() in {
                         'opacity', 'x', 'y', 'z', 'scale', 'rotate',
                         'scaleX', 'scaleY', 'width', 'height',
                         'backgroundColor', 'color', 'borderRadius',
                         'pathLength', 'translateX', 'translateY',
                     }]

            if props:
                variants.append(FramerVariantInfo(
                    name="inline",
                    variant_key=prop_name,
                    properties=props,
                    line_number=line_num,
                    file_path=file_path,
                    has_transition=False,
                ))

        return variants[:50]

    def _extract_keyframes(self, content: str, file_path: str, lines: list) -> List[FramerKeyframeInfo]:
        """Extract keyframe arrays from motion components."""
        keyframes = []
        for m in KEYFRAME_PROP_PATTERN.finditer(content):
            prop = m.group(1)
            values = m.group(2).strip()
            line_num = content[:m.start()].count('\n') + 1

            # Try to find the enclosing component type
            comp_type = self._find_motion_component_above(content, m.start())

            keyframes.append(FramerKeyframeInfo(
                property_name=prop,
                values=values,
                line_number=line_num,
                file_path=file_path,
                component_type=comp_type,
            ))

        return keyframes[:50]

    def _extract_transitions(self, content: str, file_path: str, lines: list) -> List[FramerTransitionInfo]:
        """Extract transition configurations."""
        transitions = []
        for m in TRANSITION_PROP_PATTERN.finditer(content):
            body = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Detect transition type
            t_type = ""
            type_m = TRANSITION_TYPE_PATTERN.search(body)
            if type_m:
                t_type = type_m.group(1)
            elif 'stiffness' in body or 'damping' in body:
                t_type = "spring"
            elif 'duration' in body:
                t_type = "tween"

            # Extract numeric values
            duration = self._extract_value(body, 'duration')
            delay = self._extract_value(body, 'delay')
            stiffness = self._extract_value(body, 'stiffness')
            damping = self._extract_value(body, 'damping')

            transitions.append(FramerTransitionInfo(
                transition_type=t_type,
                duration=duration,
                delay=delay,
                stiffness=stiffness,
                damping=damping,
                line_number=line_num,
                file_path=file_path,
                has_repeat='repeat' in body.lower(),
                has_stagger='stagger' in body.lower() or 'delayChildren' in body or 'staggerChildren' in body,
            ))

        return transitions[:50]

    def _extract_animate_presences(self, content: str, file_path: str, lines: list) -> List[FramerAnimatePresenceInfo]:
        """Extract AnimatePresence usage."""
        results = []
        for m in ANIMATE_PRESENCE_PATTERN.finditer(content):
            attrs = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            mode = ""
            mode_m = re.search(r"""mode\s*=\s*['"](wait|sync|popLayout)['"]""", attrs)
            if mode_m:
                mode = mode_m.group(1)

            results.append(FramerAnimatePresenceInfo(
                mode=mode,
                line_number=line_num,
                file_path=file_path,
                has_initial='initial={false}' in attrs or 'initial={ false }' in attrs,
                has_exit_before_enter='exitBeforeEnter' in attrs,
                has_on_exit_complete='onExitComplete' in attrs,
            ))

        return results[:20]

    def _extract_animation_controls(self, content: str, file_path: str, lines: list) -> List[FramerAnimationControlInfo]:
        """Extract useAnimation / useAnimationControls / useAnimate hook usage."""
        controls = []
        for m in ANIMATION_CONTROLS_PATTERN.finditer(content):
            var_name = m.group(1)
            hook_name = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            # Find method calls on this variable
            methods = []
            for cm in CONTROLS_METHOD_PATTERN.finditer(content):
                if cm.group(1) == var_name:
                    methods.append(cm.group(2))

            controls.append(FramerAnimationControlInfo(
                hook_name=hook_name,
                variable_name=var_name,
                line_number=line_num,
                file_path=file_path,
                methods_called=list(set(methods)),
            ))

        # useAnimate (v10+): const [scope, animate] = useAnimate()
        for m in USE_ANIMATE_PATTERN.finditer(content):
            scope_var = m.group(1)
            animate_var = m.group(2)
            hook_name = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            # Find method calls: animate(scope.current, ...)
            methods = []
            for cm in CONTROLS_METHOD_PATTERN.finditer(content):
                if cm.group(1) == animate_var:
                    methods.append(cm.group(2))
            # Also check for direct animate() calls
            if re.search(rf"""\b{re.escape(animate_var)}\s*\(""", content):
                methods.append('animate')

            controls.append(FramerAnimationControlInfo(
                hook_name=hook_name,
                variable_name=scope_var,
                line_number=line_num,
                file_path=file_path,
                methods_called=list(set(methods)),
            ))

        return controls[:20]

    def _extract_motion_components(self, content: str, file_path: str, lines: list) -> List[Dict]:
        """Extract unique motion.* component types used with counts."""
        from collections import Counter
        counter = Counter()
        for m in MOTION_COMPONENT_PATTERN.finditer(content):
            counter[m.group(1)] += 1
        for m in MOTION_FACTORY_PATTERN.finditer(content):
            counter[f"motion({m.group(1)})"] += 1
        result = [{'component': comp, 'count': cnt} for comp, cnt in counter.most_common(30)]
        return result

    # ── Helpers ──────────────────────────────────────────────────

    def _extract_variant_props(self, content: str, brace_start: int) -> List[str]:
        """Extract animated CSS/transform properties from a variant body."""
        # Find the matching closing brace
        depth = 0
        end = min(brace_start + 2000, len(content))
        body_end = brace_start
        for i in range(brace_start, end):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    body_end = i
                    break

        body = content[brace_start:body_end]
        props = []
        for pm in ANIMATED_PROP_PATTERN.finditer(body):
            props.append(pm.group(1))
        return list(set(props))[:20]

    def _find_enclosing_var(self, content: str, pos: int) -> str:
        """Find the variable name of the object containing pos."""
        # Look backwards for const/let/var declaration
        search_start = max(0, pos - 500)
        preceding = content[search_start:pos]
        m = re.search(r"""(?:const|let|var)\s+(\w+)\s*(?::\s*\w+)?\s*=\s*\{""", preceding)
        if m:
            return m.group(1)
        return ""

    def _find_motion_component_above(self, content: str, pos: int) -> str:
        """Find the nearest motion.* component above the given position."""
        search_start = max(0, pos - 300)
        preceding = content[search_start:pos]
        for m in MOTION_COMPONENT_PATTERN.finditer(preceding):
            pass  # Get last match
        # Find last match
        matches = list(MOTION_COMPONENT_PATTERN.finditer(preceding))
        if matches:
            return matches[-1].group(1)
        return ""

    def _extract_value(self, body: str, key: str) -> str:
        """Extract a numeric or string value for a key from a body string."""
        m = re.search(rf"""{key}\s*:\s*([\d.]+|'[^']*'|"[^"]*")""", body)
        if m:
            return m.group(1).strip("'\"")
        return ""
