"""
Three.js / React Three Fiber Animation Extractor

Extracts animation constructs:
- useFrame hooks (R3F render loop callbacks)
- AnimationMixer (Three.js animation system)
- Spring animations (@react-spring/three, @react-three/spring)
- Tween animations (gsap, @tweenjs/tween.js)
- Morph target animations
- Keyframe tracks
- useAnimations (drei helper)
- Leva/dat.gui controls for animation parameters
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ThreeJSUseFrameInfo:
    """useFrame hook usage (R3F render loop)."""
    name: str  # containing function/component name, or 'anonymous'
    file: str
    line_number: int
    has_state: bool = False  # uses state parameter
    has_delta: bool = False  # uses delta parameter
    has_clock: bool = False  # uses clock parameter
    has_ref_mutation: bool = False  # mutates a ref (e.g., mesh.rotation.x += ...)
    has_camera_access: bool = False  # accesses camera
    has_gl_access: bool = False  # accesses gl/renderer
    priority: str = ""  # render priority
    updates: List[str] = field(default_factory=list)  # what properties are updated


@dataclass
class ThreeJSAnimationMixerInfo:
    """AnimationMixer usage."""
    name: str
    file: str
    line_number: int
    has_clip_action: bool = False
    has_crossfade: bool = False
    has_time_scale: bool = False
    action_count: int = 0
    is_drei: bool = False  # uses useAnimations from drei


@dataclass
class ThreeJSSpringAnimationInfo:
    """Spring-based animation (react-spring, drei)."""
    name: str
    file: str
    line_number: int
    spring_type: str  # 'useSpring', 'useSprings', 'useTrail', 'useChain', 'animated'
    animated_props: List[str] = field(default_factory=list)
    source: str = ""  # '@react-spring/three', '@react-spring/web'


@dataclass
class ThreeJSTweenInfo:
    """Tween-based animation (gsap, tween.js)."""
    name: str
    file: str
    line_number: int
    tween_type: str  # 'gsap', 'tween', 'anime'
    method: str = ""  # 'to', 'from', 'fromTo', 'timeline', 'Tween'
    target: str = ""  # what's being animated
    has_timeline: bool = False
    has_scroll_trigger: bool = False


@dataclass
class ThreeJSMorphTargetInfo:
    """Morph target animation."""
    name: str
    file: str
    line_number: int
    has_influences: bool = False
    target_count: int = 0


class ThreeJSAnimationExtractor:
    """Extracts animation constructs from Three.js/R3F code."""

    # useFrame pattern
    USE_FRAME_PATTERN = re.compile(
        r'useFrame\s*\(\s*\(\s*(\{[^}]*\}|state|_)?\s*(?:,\s*(delta|\w+))?\s*\)\s*=>\s*\{',
        re.DOTALL
    )

    # Simple useFrame (no destructuring)
    USE_FRAME_SIMPLE = re.compile(
        r'useFrame\s*\('
    )

    # AnimationMixer patterns
    ANIMATION_MIXER_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?AnimationMixer\s*\('
    )

    # useAnimations (drei)
    USE_ANIMATIONS_PATTERN = re.compile(
        r'useAnimations\s*\(\s*(\w+)'
    )

    # AnimationClip/AnimationAction
    CLIP_ACTION_PATTERN = re.compile(
        r'\.clipAction\s*\('
    )

    # react-spring patterns
    SPRING_PATTERNS = {
        'useSpring': re.compile(r'useSpring\s*\('),
        'useSprings': re.compile(r'useSprings\s*\('),
        'useTrail': re.compile(r'useTrail\s*\('),
        'useChain': re.compile(r'useChain\s*\('),
        'useTransition': re.compile(r'useTransition\s*\('),
        'animated': re.compile(r'<animated\.\w+'),
    }

    # GSAP patterns
    GSAP_PATTERNS = re.compile(
        r'gsap\.(to|from|fromTo|timeline|set|registerPlugin)\s*\('
    )
    GSAP_TIMELINE_PATTERN = re.compile(
        r'gsap\.timeline\s*\('
    )
    SCROLL_TRIGGER_PATTERN = re.compile(
        r'(?:ScrollTrigger|scrollTrigger)'
    )

    # Tween.js patterns
    TWEEN_PATTERN = re.compile(
        r'new\s+(?:TWEEN\.)?Tween\s*\('
    )

    # anime.js patterns
    ANIME_PATTERN = re.compile(
        r'anime\s*\(\s*\{'
    )

    # Morph targets
    MORPH_PATTERN = re.compile(
        r'morphTargetInfluences|morphTargetDictionary|morphAttributes'
    )

    # KeyframeTrack
    KEYFRAME_TRACK_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(VectorKeyframeTrack|QuaternionKeyframeTrack|'
        r'NumberKeyframeTrack|ColorKeyframeTrack|BooleanKeyframeTrack|'
        r'StringKeyframeTrack|KeyframeTrack)\s*\('
    )

    # Property update patterns in useFrame
    REF_MUTATION_PATTERN = re.compile(
        r'(?:ref|mesh|group|camera|light)\w*\.current\.\w+\.\w+\s*[+\-*/]?='
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract animation constructs."""
        result = {
            'use_frames': [],
            'animation_mixers': [],
            'spring_animations': [],
            'tweens': [],
            'morph_targets': [],
        }

        # useFrame hooks
        for match in self.USE_FRAME_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            params = match.group(1) or ''
            delta_param = match.group(2) or ''

            # Look at body for analysis
            body_start = match.end()
            body_end = self._find_brace_end(content, body_start - 1)
            body = content[body_start:body_end] if body_end > body_start else ''

            has_state = bool(re.search(r'\bstate\b', params))
            has_delta = bool(delta_param and delta_param != '_')
            has_clock = bool(re.search(r'\bclock\b', params))
            has_camera = bool(re.search(r'\bcamera\b', params) or re.search(r'state\.camera', body))
            has_gl = bool(re.search(r'\bgl\b', params) or re.search(r'state\.gl', body))
            has_ref_mutation = bool(self.REF_MUTATION_PATTERN.search(body))

            # Detect what's being updated
            updates = []
            for prop in ['position', 'rotation', 'scale', 'material', 'opacity', 'color', 'intensity', 'quaternion']:
                if re.search(rf'\.{prop}', body):
                    updates.append(prop)

            # Detect priority
            priority = ''
            prio_match = re.search(r'useFrame\s*\([^,]+,[^,]*,\s*(-?\d+)\s*\)', content[match.start():match.start()+300])
            if prio_match:
                priority = prio_match.group(1)

            result['use_frames'].append(ThreeJSUseFrameInfo(
                name='useFrame',
                file=file_path,
                line_number=line_num,
                has_state=has_state,
                has_delta=has_delta,
                has_clock=has_clock,
                has_ref_mutation=has_ref_mutation,
                has_camera_access=has_camera,
                has_gl_access=has_gl,
                priority=priority,
                updates=updates[:10],
            ))

        # Simple useFrame (catches any we missed)
        simple_count = len(self.USE_FRAME_SIMPLE.findall(content))
        existing_count = len(result['use_frames'])
        if simple_count > existing_count:
            for match in self.USE_FRAME_SIMPLE.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Only add if not already captured
                already = any(uf.line_number == line_num for uf in result['use_frames'])
                if not already:
                    result['use_frames'].append(ThreeJSUseFrameInfo(
                        name='useFrame',
                        file=file_path,
                        line_number=line_num,
                    ))

        # AnimationMixer
        for match in self.ANIMATION_MIXER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['animation_mixers'].append(ThreeJSAnimationMixerInfo(
                name='AnimationMixer',
                file=file_path,
                line_number=line_num,
                has_clip_action=bool(self.CLIP_ACTION_PATTERN.search(content)),
                action_count=len(self.CLIP_ACTION_PATTERN.findall(content)),
            ))

        # useAnimations (drei)
        for match in self.USE_ANIMATIONS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['animation_mixers'].append(ThreeJSAnimationMixerInfo(
                name='useAnimations',
                file=file_path,
                line_number=line_num,
                is_drei=True,
                has_clip_action=True,
            ))

        # Spring animations
        for spring_type, pattern in self.SPRING_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                source = '@react-spring/three' if re.search(r'@react-spring/three', content) else '@react-spring/web'
                result['spring_animations'].append(ThreeJSSpringAnimationInfo(
                    name=spring_type,
                    file=file_path,
                    line_number=line_num,
                    spring_type=spring_type,
                    source=source,
                ))

        # GSAP
        for match in self.GSAP_PATTERNS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            method = match.group(1)
            result['tweens'].append(ThreeJSTweenInfo(
                name='gsap.' + method,
                file=file_path,
                line_number=line_num,
                tween_type='gsap',
                method=method,
                has_timeline=bool(self.GSAP_TIMELINE_PATTERN.search(content)),
                has_scroll_trigger=bool(self.SCROLL_TRIGGER_PATTERN.search(content)),
            ))

        # Tween.js
        for match in self.TWEEN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['tweens'].append(ThreeJSTweenInfo(
                name='Tween',
                file=file_path,
                line_number=line_num,
                tween_type='tween',
                method='Tween',
            ))

        # anime.js
        for match in self.ANIME_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['tweens'].append(ThreeJSTweenInfo(
                name='anime',
                file=file_path,
                line_number=line_num,
                tween_type='anime',
                method='anime',
            ))

        # Morph targets
        for match in self.MORPH_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            already = any(mt.line_number == line_num for mt in result['morph_targets'])
            if not already:
                result['morph_targets'].append(ThreeJSMorphTargetInfo(
                    name='morphTarget',
                    file=file_path,
                    line_number=line_num,
                    has_influences='morphTargetInfluences' in match.group(0),
                ))

        return result

    def _find_brace_end(self, content: str, start: int) -> int:
        """Find matching closing brace."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return min(start + 500, len(content))
