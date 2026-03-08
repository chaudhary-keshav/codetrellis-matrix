"""
Three.js / React Three Fiber Scene Extractor

Extracts scene-level constructs:
- Canvas setup (R3F <Canvas> component configuration)
- Cameras (PerspectiveCamera, OrthographicCamera, custom cameras)
- Renderers (WebGLRenderer config, toneMapping, shadows, encoding)
- Controls (OrbitControls, FlyControls, PointerLockControls, etc.)
- Lights (ambient, directional, point, spot, hemisphere, area, rect)
- Post-processing (EffectComposer, Bloom, SSAO, DOF, etc.)
- Physics (rapier, cannon-es, ammo.js)
- Environment (fog, background, environment maps, HDR, skybox)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ThreeJSCanvasInfo:
    """R3F Canvas component or Three.js renderer setup."""
    name: str  # 'Canvas' or custom name
    file: str
    line_number: int
    canvas_type: str  # 'r3f', 'vanilla'
    has_shadows: bool = False
    has_camera: bool = False
    has_gl_config: bool = False
    has_raycaster: bool = False
    has_frameloop: bool = False
    frameloop: str = ""  # 'always', 'demand', 'never'
    dpr: str = ""
    has_flat: bool = False
    has_linear: bool = False
    has_orthographic: bool = False
    has_events: bool = False
    props: List[str] = field(default_factory=list)


@dataclass
class ThreeJSCameraInfo:
    """Camera configuration."""
    name: str
    file: str
    line_number: int
    camera_type: str  # 'perspective', 'orthographic', 'cube', 'stereo', 'array'
    is_drei: bool = False
    has_controls: bool = False
    fov: str = ""
    near: str = ""
    far: str = ""
    position: str = ""
    make_default: bool = False


@dataclass
class ThreeJSRendererInfo:
    """Renderer configuration (vanilla Three.js)."""
    name: str
    file: str
    line_number: int
    renderer_type: str  # 'webgl', 'webgl2', 'webgpu', 'css2d', 'css3d', 'svg'
    tone_mapping: str = ""
    output_encoding: str = ""
    has_shadows: bool = False
    shadow_type: str = ""
    pixel_ratio: str = ""
    antialias: bool = False


@dataclass
class ThreeJSControlsInfo:
    """Camera/interaction controls."""
    name: str
    file: str
    line_number: int
    controls_type: str  # 'orbit', 'fly', 'pointer_lock', 'trackball', 'map', 'drag', 'transform', 'first_person'
    is_drei: bool = False
    has_limits: bool = False
    has_damping: bool = False
    has_auto_rotate: bool = False
    props: List[str] = field(default_factory=list)


@dataclass
class ThreeJSLightInfo:
    """Light source."""
    name: str
    file: str
    line_number: int
    light_type: str  # 'ambient', 'directional', 'point', 'spot', 'hemisphere', 'rect_area'
    intensity: str = ""
    color: str = ""
    has_shadow: bool = False
    has_helper: bool = False
    is_drei: bool = False


@dataclass
class ThreeJSPostProcessingInfo:
    """Post-processing effect."""
    name: str
    file: str
    line_number: int
    effect_type: str  # 'bloom', 'ssao', 'dof', 'vignette', 'chromatic_aberration', 'tone_mapping', 'smaa', 'fxaa', 'custom'
    source: str  # '@react-three/postprocessing', 'three/examples/jsm/postprocessing'
    has_custom_shader: bool = False
    props: List[str] = field(default_factory=list)


@dataclass
class ThreeJSPhysicsInfo:
    """Physics engine configuration."""
    name: str
    file: str
    line_number: int
    engine: str  # 'rapier', 'cannon', 'ammo', 'oimo', 'havok'
    has_gravity: bool = False
    has_debug: bool = False
    body_types: List[str] = field(default_factory=list)  # 'rigid', 'collider', 'joint'
    props: List[str] = field(default_factory=list)


class ThreeJSSceneExtractor:
    """Extracts Three.js/R3F scene-level constructs."""

    # R3F Canvas patterns
    CANVAS_PATTERN = re.compile(
        r'<Canvas\b([^>]*?)(?:/>|>)', re.DOTALL
    )
    CANVAS_PROP_PATTERN = re.compile(
        r'(\w+)(?:=\{([^}]*)\}|="([^"]*)")?'
    )

    # Camera patterns
    CAMERA_PATTERNS = {
        'perspective': re.compile(
            r'(?:new\s+(?:THREE\.)?PerspectiveCamera|<(?:perspectiveCamera|PerspectiveCamera)\b)', re.IGNORECASE
        ),
        'orthographic': re.compile(
            r'(?:new\s+(?:THREE\.)?OrthographicCamera|<(?:orthographicCamera|OrthographicCamera)\b)', re.IGNORECASE
        ),
        'cube': re.compile(r'new\s+(?:THREE\.)?CubeCamera'),
        'stereo': re.compile(r'new\s+(?:THREE\.)?StereoCamera'),
    }

    # Drei camera patterns
    DREI_CAMERA_PATTERN = re.compile(
        r'<(PerspectiveCamera|OrthographicCamera|CubeCamera)\b'
    )

    # Renderer patterns
    RENDERER_PATTERNS = {
        'webgl': re.compile(r'new\s+(?:THREE\.)?WebGLRenderer'),
        'webgpu': re.compile(r'new\s+(?:THREE\.)?WebGPURenderer'),
        'css2d': re.compile(r'new\s+CSS2DRenderer'),
        'css3d': re.compile(r'new\s+CSS3DRenderer'),
        'svg': re.compile(r'new\s+SVGRenderer'),
    }

    # Controls patterns
    CONTROLS_PATTERNS = {
        'orbit': re.compile(r'(?:<OrbitControls|new\s+OrbitControls|OrbitControls\s*\()'),
        'fly': re.compile(r'(?:<FlyControls|new\s+FlyControls)'),
        'pointer_lock': re.compile(r'(?:<PointerLockControls|new\s+PointerLockControls)'),
        'trackball': re.compile(r'(?:<TrackballControls|new\s+TrackballControls)'),
        'map': re.compile(r'(?:<MapControls|new\s+MapControls)'),
        'drag': re.compile(r'(?:<DragControls|new\s+DragControls)'),
        'transform': re.compile(r'(?:<TransformControls|new\s+TransformControls)'),
        'first_person': re.compile(r'(?:<FirstPersonControls|new\s+FirstPersonControls)'),
        'arcball': re.compile(r'(?:<ArcballControls|new\s+ArcballControls)'),
        'scroll': re.compile(r'(?:<ScrollControls|new\s+ScrollControls)'),
    }

    # Light patterns
    LIGHT_PATTERNS = {
        'ambient': re.compile(r'(?:<ambientLight|new\s+(?:THREE\.)?AmbientLight)'),
        'directional': re.compile(r'(?:<directionalLight|new\s+(?:THREE\.)?DirectionalLight)'),
        'point': re.compile(r'(?:<pointLight|new\s+(?:THREE\.)?PointLight)'),
        'spot': re.compile(r'(?:<spotLight|new\s+(?:THREE\.)?SpotLight)'),
        'hemisphere': re.compile(r'(?:<hemisphereLight|new\s+(?:THREE\.)?HemisphereLight)'),
        'rect_area': re.compile(r'(?:<rectAreaLight|new\s+(?:THREE\.)?RectAreaLight)'),
    }

    # Drei light helpers
    DREI_LIGHT_HELPERS = re.compile(
        r'<(Environment|Stage|ContactShadows|AccumulativeShadows|SoftShadows|Sky|Stars|Cloud|Lightformer)\b'
    )

    # Post-processing patterns (R3F)
    R3F_POSTPROCESSING = re.compile(
        r'<(EffectComposer|Bloom|DepthOfField|SSAO|SSR|ToneMapping|Vignette|'
        r'ChromaticAberration|Noise|Glitch|Scanline|Pixelation|SMAA|FXAA|'
        r'BrightnessContrast|HueSaturation|ColorAverage|Sepia|LUT|N8AO|'
        r'TiltShift|GodRays|Outline|SelectiveBloom)\b'
    )

    # Vanilla Three.js post-processing
    VANILLA_POSTPROCESSING = re.compile(
        r'new\s+(?:THREE\.)?(?:EffectComposer|RenderPass|ShaderPass|'
        r'UnrealBloomPass|SSAOPass|BokehPass|FilmPass|GlitchPass|'
        r'OutlinePass|SAOPass|SMAAPass|FXAAShader|TAARenderPass)\b'
    )

    # Physics patterns
    PHYSICS_PATTERNS = {
        'rapier': re.compile(r'(?:<Physics|useRapier|RigidBody|from\s+[\'"]@react-three/rapier)'),
        'cannon': re.compile(r'(?:useCannon|useBox|useSphere|usePlane|useCylinder|from\s+[\'"]@react-three/cannon)'),
        'ammo': re.compile(r'(?:Ammo\.btDiscreteDynamicsWorld|from\s+[\'"]ammo\.js)'),
        'oimo': re.compile(r'(?:from\s+[\'"]oimo|OIMO\.World)'),
        'havok': re.compile(r'(?:from\s+[\'"]@babylonjs/havok|HavokPlugin)'),
    }

    # Fog patterns
    FOG_PATTERN = re.compile(r'(?:<fog\b|new\s+(?:THREE\.)?(?:Fog|FogExp2)\b)')

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract scene-level constructs from Three.js/R3F code."""
        result = {
            'canvases': [],
            'cameras': [],
            'renderers': [],
            'controls': [],
            'lights': [],
            'post_processing': [],
            'physics': [],
        }

        lines = content.split('\n')

        # Extract Canvas components
        for match in self.CANVAS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            props_str = match.group(1)
            props = []
            has_shadows = bool(re.search(r'\bshadows\b', props_str))
            has_camera = bool(re.search(r'\bcamera\b', props_str))
            has_gl = bool(re.search(r'\bgl\b', props_str))
            has_raycaster = bool(re.search(r'\braycaster\b', props_str))
            has_frameloop = bool(re.search(r'\bframeloop\b', props_str))
            frameloop = ""
            fl_match = re.search(r'frameloop\s*=\s*["\'](\w+)["\']', props_str)
            if fl_match:
                frameloop = fl_match.group(1)
            dpr_match = re.search(r'dpr\s*=', props_str)
            has_flat = bool(re.search(r'\bflat\b', props_str))
            has_linear = bool(re.search(r'\blinear\b', props_str))
            has_orthographic = bool(re.search(r'\borthographic\b', props_str))

            for pm in self.CANVAS_PROP_PATTERN.finditer(props_str):
                props.append(pm.group(1))

            result['canvases'].append(ThreeJSCanvasInfo(
                name='Canvas',
                file=file_path,
                line_number=line_num,
                canvas_type='r3f',
                has_shadows=has_shadows,
                has_camera=has_camera,
                has_gl_config=has_gl,
                has_raycaster=has_raycaster,
                has_frameloop=has_frameloop,
                frameloop=frameloop,
                dpr=dpr_match.group(0) if dpr_match else "",
                has_flat=has_flat,
                has_linear=has_linear,
                has_orthographic=has_orthographic,
                props=props[:20],
            ))

        # Extract cameras
        for cam_type, pattern in self.CAMERA_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['cameras'].append(ThreeJSCameraInfo(
                    name=cam_type.title() + 'Camera',
                    file=file_path,
                    line_number=line_num,
                    camera_type=cam_type,
                    is_drei=False,
                ))

        for match in self.DREI_CAMERA_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            cam_name = match.group(1)
            cam_type = 'perspective' if 'Perspective' in cam_name else 'orthographic' if 'Orthographic' in cam_name else 'cube'
            result['cameras'].append(ThreeJSCameraInfo(
                name=cam_name,
                file=file_path,
                line_number=line_num,
                camera_type=cam_type,
                is_drei=True,
                make_default=bool(re.search(r'makeDefault', content[match.start():match.start()+200])),
            ))

        # Extract renderers (vanilla Three.js)
        for rend_type, pattern in self.RENDERER_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Check nearby config
                context_end = min(match.end() + 500, len(content))
                context = content[match.start():context_end]
                result['renderers'].append(ThreeJSRendererInfo(
                    name=rend_type.upper() + 'Renderer',
                    file=file_path,
                    line_number=line_num,
                    renderer_type=rend_type,
                    tone_mapping=self._extract_tone_mapping(context),
                    has_shadows=bool(re.search(r'shadowMap\.enabled\s*=\s*true', context)),
                    shadow_type=self._extract_shadow_type(context),
                    antialias=bool(re.search(r'antialias\s*:\s*true', context)),
                ))

        # Extract controls
        for ctrl_type, pattern in self.CONTROLS_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                context_end = min(match.end() + 300, len(content))
                context = content[match.start():context_end]
                is_drei = match.group(0).startswith('<')
                result['controls'].append(ThreeJSControlsInfo(
                    name=ctrl_type.title().replace('_', '') + 'Controls',
                    file=file_path,
                    line_number=line_num,
                    controls_type=ctrl_type,
                    is_drei=is_drei,
                    has_damping=bool(re.search(r'(?:enableDamping|damping)', context)),
                    has_auto_rotate=bool(re.search(r'autoRotate', context)),
                    has_limits=bool(re.search(r'(?:minDistance|maxDistance|minPolarAngle|maxPolarAngle)', context)),
                ))

        # Extract lights
        for light_type, pattern in self.LIGHT_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                context_end = min(match.end() + 200, len(content))
                context = content[match.start():context_end]
                result['lights'].append(ThreeJSLightInfo(
                    name=light_type.title().replace('_', '') + 'Light',
                    file=file_path,
                    line_number=line_num,
                    light_type=light_type,
                    has_shadow=bool(re.search(r'(?:castShadow|shadow)', context)),
                    is_drei=match.group(0).startswith('<'),
                    intensity=self._extract_numeric_prop(context, 'intensity'),
                ))

        # Drei environment/lighting helpers
        for match in self.DREI_LIGHT_HELPERS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['lights'].append(ThreeJSLightInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                light_type='environment',
                is_drei=True,
            ))

        # Post-processing (R3F)
        for match in self.R3F_POSTPROCESSING.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            effect_name = match.group(1)
            result['post_processing'].append(ThreeJSPostProcessingInfo(
                name=effect_name,
                file=file_path,
                line_number=line_num,
                effect_type=self._classify_effect(effect_name),
                source='@react-three/postprocessing',
            ))

        # Post-processing (vanilla)
        for match in self.VANILLA_POSTPROCESSING.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['post_processing'].append(ThreeJSPostProcessingInfo(
                name=match.group(0).split('(')[0].split()[-1],
                file=file_path,
                line_number=line_num,
                effect_type='custom',
                source='three/examples/jsm/postprocessing',
            ))

        # Physics
        for engine, pattern in self.PHYSICS_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['physics'].append(ThreeJSPhysicsInfo(
                    name=engine.title() + 'Physics',
                    file=file_path,
                    line_number=line_num,
                    engine=engine,
                    has_gravity=bool(re.search(r'gravity', content)),
                    has_debug=bool(re.search(r'debug', content)),
                ))
                break  # one per engine

        return result

    def _extract_tone_mapping(self, context: str) -> str:
        """Extract tone mapping type."""
        match = re.search(r'toneMapping\s*[:=]\s*(?:THREE\.)?(\w+ToneMapping)', context)
        return match.group(1) if match else ""

    def _extract_shadow_type(self, context: str) -> str:
        """Extract shadow map type."""
        match = re.search(r'shadowMap\.type\s*=\s*(?:THREE\.)?(\w+)', context)
        return match.group(1) if match else ""

    def _extract_numeric_prop(self, context: str, prop: str) -> str:
        """Extract numeric property value."""
        match = re.search(rf'{prop}\s*[:=]\s*\{{?\s*([0-9.]+)', context)
        return match.group(1) if match else ""

    def _classify_effect(self, name: str) -> str:
        """Classify post-processing effect type."""
        effect_map = {
            'Bloom': 'bloom', 'SelectiveBloom': 'bloom',
            'DepthOfField': 'dof', 'SSAO': 'ssao', 'N8AO': 'ssao',
            'SSR': 'ssr', 'Vignette': 'vignette',
            'ChromaticAberration': 'chromatic_aberration',
            'Noise': 'noise', 'Glitch': 'glitch',
            'ToneMapping': 'tone_mapping', 'SMAA': 'smaa', 'FXAA': 'fxaa',
            'BrightnessContrast': 'color', 'HueSaturation': 'color',
            'Sepia': 'color', 'ColorAverage': 'color', 'LUT': 'color',
            'TiltShift': 'blur', 'GodRays': 'volumetric',
            'Outline': 'outline', 'Scanline': 'retro',
            'Pixelation': 'retro',
        }
        return effect_map.get(name, 'custom')
