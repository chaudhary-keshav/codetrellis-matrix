"""
EnhancedThreeJSParser v1.0 - Comprehensive Three.js / React Three Fiber parser using all extractors.

This parser integrates all Three.js/R3F extractors to provide complete parsing of
3D web applications. It runs as a supplementary layer on top of the JavaScript and
TypeScript parsers, extracting Three.js-specific semantics.

Supports:
- Three.js r73+ (ES modules, BufferGeometry migration)
- Three.js r118+ (WebGL2, examples/jsm migration)
- Three.js r133+ (Color management, sRGB default)
- Three.js r150+ (WebGPU renderer, WebGPURenderer)
- Three.js r160+ (Updated material system, BatchedMesh)
- Three.js r162+ (Latest stable, TSL shading language)
- React Three Fiber v1–v8+ (declarative Three.js for React)
- @react-three/drei v1–v9+ (useful helpers for R3F)
- @react-three/postprocessing v2+ (post-processing effects)
- @react-three/rapier v1+ (Rapier physics integration)
- @react-three/cannon v6+ (cannon-es physics integration)
- @react-three/xr v5+ (WebXR support)
- @react-three/a11y v3+ (accessibility for 3D scenes)

Scene constructs:
- Canvas (R3F root), Camera, Renderer, Controls, Lights
- Post-processing (EffectComposer, individual effects)
- Physics engines (Rapier, Cannon, Ammo, Oimo, Havok)

Component constructs:
- Mesh, Group, InstancedMesh, SkinnedMesh, Line, Points, Sprite, LOD
- Drei components (100+ across 10 categories)
- Custom R3F elements (extend())
- GLTF/FBX/OBJ model loading (useGLTF, useFBX, GLTFLoader)
- Geometry and material detection

Material constructs:
- Standard/Physical/Lambert/Phong/Toon/Matcap + more materials
- ShaderMaterial, RawShaderMaterial, NodeMaterial
- Drei special materials (MeshTransmission, MeshReflector, etc.)
- GLSL vertex/fragment shaders, uniforms, textures
- glslify, tagged template literals

Animation constructs:
- useFrame (R3F render loop callbacks)
- AnimationMixer / useAnimations (skeletal animation)
- Spring animations (@react-spring/three)
- Tween animations (GSAP, Tween.js, anime.js)
- Morph target animations

API constructs:
- Import detection (three, @react-three/*, etc.)
- Framework version detection
- TypeScript type usage for Three.js/R3F
- Integration libraries (zustand, leva, r3f-perf, etc.)
- CDN usage (legacy script tag patterns)

Framework detection (30+ Three.js ecosystem patterns):
- Core: three, @react-three/fiber, @react-three/drei
- Physics: @react-three/rapier, @react-three/cannon, cannon-es, ammo.js, oimo.js
- Post-processing: @react-three/postprocessing, postprocessing
- XR: @react-three/xr, WebXR API
- State: zustand, jotai, valtio (pmndrs ecosystem)
- UI: leva, dat.gui, tweakpane
- Performance: r3f-perf, stats.js
- Animation: @react-spring/three, gsap, @tweenjs/tween.js, anime.js
- Utilities: maath, three-stdlib, lamina, tunnel-rat, suspend-react
- Assets: @pmndrs/assets, draco, basis, ktx2
- Accessibility: @react-three/a11y
- Testing: @react-three/test-renderer

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.71 - Three.js / React Three Fiber Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Three.js/R3F extractors
from .extractors.threejs import (
    ThreeJSSceneExtractor, ThreeJSCanvasInfo, ThreeJSCameraInfo,
    ThreeJSRendererInfo, ThreeJSControlsInfo, ThreeJSLightInfo,
    ThreeJSPostProcessingInfo, ThreeJSPhysicsInfo,
    ThreeJSComponentExtractor, ThreeJSMeshInfo, ThreeJSGroupInfo,
    ThreeJSInstancedMeshInfo, ThreeJSDreiComponentInfo,
    ThreeJSCustomComponentInfo, ThreeJSModelInfo,
    ThreeJSMaterialExtractor, ThreeJSMaterialInfo, ThreeJSShaderInfo,
    ThreeJSTextureInfo, ThreeJSUniformInfo,
    ThreeJSAnimationExtractor, ThreeJSUseFrameInfo,
    ThreeJSAnimationMixerInfo, ThreeJSSpringAnimationInfo,
    ThreeJSTweenInfo, ThreeJSMorphTargetInfo,
    ThreeJSAPIExtractor, ThreeJSImportInfo, ThreeJSIntegrationInfo,
    ThreeJSTypeInfo,
)


@dataclass
class ThreeJSParseResult:
    """Complete parse result for a Three.js/R3F file."""
    file_path: str
    file_type: str = "jsx"  # js, jsx, ts, tsx

    # Scene-level
    canvases: List[ThreeJSCanvasInfo] = field(default_factory=list)
    cameras: List[ThreeJSCameraInfo] = field(default_factory=list)
    renderers: List[ThreeJSRendererInfo] = field(default_factory=list)
    controls: List[ThreeJSControlsInfo] = field(default_factory=list)
    lights: List[ThreeJSLightInfo] = field(default_factory=list)
    post_processing: List[ThreeJSPostProcessingInfo] = field(default_factory=list)
    physics: List[ThreeJSPhysicsInfo] = field(default_factory=list)

    # Components
    meshes: List[ThreeJSMeshInfo] = field(default_factory=list)
    groups: List[ThreeJSGroupInfo] = field(default_factory=list)
    instanced_meshes: List[ThreeJSInstancedMeshInfo] = field(default_factory=list)
    drei_components: List[ThreeJSDreiComponentInfo] = field(default_factory=list)
    custom_components: List[ThreeJSCustomComponentInfo] = field(default_factory=list)
    models: List[ThreeJSModelInfo] = field(default_factory=list)

    # Materials
    materials: List[ThreeJSMaterialInfo] = field(default_factory=list)
    shaders: List[ThreeJSShaderInfo] = field(default_factory=list)
    textures: List[ThreeJSTextureInfo] = field(default_factory=list)
    uniforms: List[ThreeJSUniformInfo] = field(default_factory=list)

    # Animations
    use_frames: List[ThreeJSUseFrameInfo] = field(default_factory=list)
    animation_mixers: List[ThreeJSAnimationMixerInfo] = field(default_factory=list)
    spring_animations: List[ThreeJSSpringAnimationInfo] = field(default_factory=list)
    tweens: List[ThreeJSTweenInfo] = field(default_factory=list)
    morph_targets: List[ThreeJSMorphTargetInfo] = field(default_factory=list)

    # API
    imports: List[ThreeJSImportInfo] = field(default_factory=list)
    integrations: List[ThreeJSIntegrationInfo] = field(default_factory=list)
    types: List[ThreeJSTypeInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    threejs_version: str = ""  # detected minimum Three.js revision
    r3f_version: str = ""  # detected minimum R3F version
    is_vanilla: bool = False  # pure Three.js (no R3F)
    is_r3f: bool = False  # React Three Fiber


class EnhancedThreeJSParser:
    """
    Enhanced Three.js / React Three Fiber parser using all extractors.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when Three.js/R3F is detected. It extracts 3D-specific semantics that
    the language parsers cannot capture.

    Framework detection supports 30+ Three.js ecosystem libraries across:
    - Core (three, @react-three/fiber, @react-three/drei)
    - Physics (@react-three/rapier, @react-three/cannon, cannon-es, ammo.js)
    - Post-processing (@react-three/postprocessing, postprocessing)
    - XR (@react-three/xr, WebXR)
    - State (zustand, jotai, valtio — pmndrs ecosystem)
    - UI (leva, dat.gui, tweakpane)
    - Performance (r3f-perf, stats.js)
    - Animation (@react-spring/three, gsap, tween.js, anime.js)
    - Utilities (maath, three-stdlib, lamina, tunnel-rat, suspend-react)
    - Accessibility (@react-three/a11y)
    - Testing (@react-three/test-renderer)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Three.js ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'three': re.compile(
            r"from\s+['\"]three['\"]|require\(['\"]three['\"]\)|"
            r"import\s*\*\s+as\s+THREE\s+from|"
            r"THREE\.\w+|new\s+THREE\.\w+",
            re.MULTILINE
        ),
        'react-three-fiber': re.compile(
            r"from\s+['\"]@react-three/fiber['\"]|"
            r"<Canvas|useFrame|useThree|useLoader|useGraph|extend\s*\(",
            re.MULTILINE
        ),
        'drei': re.compile(
            r"from\s+['\"]@react-three/drei['\"]|"
            r"useGLTF|useFBX|useTexture|useAnimations|"
            r"<OrbitControls|<Environment|<Html|<Text|<Float|<Sky|<Stars|"
            r"<MeshReflectorMaterial|<MeshTransmissionMaterial",
            re.MULTILINE
        ),

        # ── Physics ───────────────────────────────────────────────
        'rapier': re.compile(
            r"from\s+['\"]@react-three/rapier['\"]|"
            r"<Physics|<RigidBody|<CuboidCollider|<BallCollider|useRapier",
            re.MULTILINE
        ),
        'cannon': re.compile(
            r"from\s+['\"]@react-three/cannon['\"]|from\s+['\"]cannon-es['\"]|"
            r"usePlane|useBox|useSphere|useCylinder|useConvexPolyhedron",
            re.MULTILINE
        ),
        'ammo': re.compile(
            r"from\s+['\"]ammo\.js['\"]|AmmoPhysics|Ammo\(\)",
            re.MULTILINE
        ),
        'oimo': re.compile(
            r"from\s+['\"]oimo['\"]|OIMO\.\w+",
            re.MULTILINE
        ),

        # ── Post-processing ──────────────────────────────────────
        'postprocessing': re.compile(
            r"from\s+['\"]@react-three/postprocessing['\"]|"
            r"from\s+['\"]postprocessing['\"]|"
            r"<EffectComposer|<Bloom|<SSAO|<DepthOfField|<ChromaticAberration",
            re.MULTILINE
        ),

        # ── XR / WebXR ───────────────────────────────────────────
        'xr': re.compile(
            r"from\s+['\"]@react-three/xr['\"]|"
            r"<XR|<VRButton|<ARButton|useXR|useController|useHitTest|"
            r"VRButton\.createButton|ARButton\.createButton|"
            r"navigator\.xr|XRSession",
            re.MULTILINE
        ),

        # ── Accessibility ─────────────────────────────────────────
        'a11y': re.compile(
            r"from\s+['\"]@react-three/a11y['\"]|<A11y|useA11y",
            re.MULTILINE
        ),

        # ── State Management (pmndrs ecosystem) ──────────────────
        'zustand': re.compile(
            r"from\s+['\"]zustand['\"]",
            re.MULTILINE
        ),
        'jotai': re.compile(
            r"from\s+['\"]jotai['\"]",
            re.MULTILINE
        ),
        'valtio': re.compile(
            r"from\s+['\"]valtio['\"]",
            re.MULTILINE
        ),

        # ── UI Controls ───────────────────────────────────────────
        'leva': re.compile(
            r"from\s+['\"]leva['\"]|useControls|<Leva",
            re.MULTILINE
        ),
        'dat-gui': re.compile(
            r"from\s+['\"]dat\.gui['\"]|new\s+dat\.GUI|new\s+GUI",
            re.MULTILINE
        ),
        'tweakpane': re.compile(
            r"from\s+['\"]tweakpane['\"]|new\s+Pane",
            re.MULTILINE
        ),

        # ── Performance ───────────────────────────────────────────
        'r3f-perf': re.compile(
            r"from\s+['\"]r3f-perf['\"]|<Perf|usePerf",
            re.MULTILINE
        ),
        'stats-js': re.compile(
            r"from\s+['\"]stats\.js['\"]|new\s+Stats\(\)",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'react-spring-three': re.compile(
            r"from\s+['\"]@react-spring/three['\"]|"
            r"animated\.\w+|useSpring.*three",
            re.MULTILINE
        ),
        'gsap': re.compile(
            r"from\s+['\"]gsap['\"]|gsap\.\w+",
            re.MULTILINE
        ),
        'tween-js': re.compile(
            r"from\s+['\"]@tweenjs/tween\.js['\"]|from\s+['\"]tween\.js['\"]|"
            r"new\s+TWEEN\.Tween|TWEEN\.update",
            re.MULTILINE
        ),
        'anime-js': re.compile(
            r"from\s+['\"]animejs['\"]|from\s+['\"]anime['\"]",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'three-stdlib': re.compile(
            r"from\s+['\"]three-stdlib['\"]",
            re.MULTILINE
        ),
        'maath': re.compile(
            r"from\s+['\"]maath['\"]",
            re.MULTILINE
        ),
        'lamina': re.compile(
            r"from\s+['\"]lamina['\"]|<LayerMaterial|<Depth|<Noise|<Fresnel",
            re.MULTILINE
        ),
        'tunnel-rat': re.compile(
            r"from\s+['\"]tunnel-rat['\"]",
            re.MULTILINE
        ),
        'suspend-react': re.compile(
            r"from\s+['\"]suspend-react['\"]",
            re.MULTILINE
        ),
        'use-gesture': re.compile(
            r"from\s+['\"]@use-gesture/react['\"]|useDrag|usePinch|useWheel",
            re.MULTILINE
        ),

        # ── CSG / Constructive Solid Geometry ─────────────────────
        'csg': re.compile(
            r"from\s+['\"]@react-three/csg['\"]|"
            r"<Geometry|<Base|<Addition|<Subtraction|<Intersection",
            re.MULTILINE
        ),

        # ── Flex Layout ───────────────────────────────────────────
        'flex': re.compile(
            r"from\s+['\"]@react-three/flex['\"]|<Flex|<Box.*flex",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'test-renderer': re.compile(
            r"from\s+['\"]@react-three/test-renderer['\"]|"
            r"ReactThreeTestRenderer|create\(\s*<Canvas",
            re.MULTILINE
        ),

        # ── Assets ────────────────────────────────────────────────
        'pmndrs-assets': re.compile(
            r"from\s+['\"]@pmndrs/assets['\"]",
            re.MULTILINE
        ),
    }

    # Three.js version detection from features
    THREEJS_VERSION_FEATURES = {
        # r162+ (2024) features
        'WebGPURenderer': 'r160',
        'BatchedMesh': 'r160',
        'TSL': 'r162',
        'NodeMaterial': 'r155',

        # r150+ features
        'ColorManagement': 'r150',
        'SRGBColorSpace': 'r152',
        'LinearSRGBColorSpace': 'r152',

        # r133+ features
        'texture.colorSpace': 'r133',

        # r118+ features
        'three/examples/jsm': 'r118',
        'three/addons': 'r118',

        # r125+ features
        'WebGL1Renderer': 'r118',

        # r73+ features (ES modules era)
        'from \'three\'': 'r73',
        'from "three"': 'r73',
    }

    # R3F version detection
    R3F_VERSION_FEATURES = {
        # v8+ features
        'frameloop': 'v8',
        'createRoot': 'v8',
        'events.compute': 'v8',

        # v7+ features
        'useFrame.*state': 'v7',
        'invalidate': 'v7',
        'advance': 'v7',

        # v6+ features
        'useGraph': 'v6',
        'Canvas.*flat': 'v6',

        # v5+ features
        'useThree': 'v5',

        # v1+ features
        'useFrame': 'v1',
        'Canvas': 'v1',
    }

    def __init__(self):
        """Initialize the parser with all Three.js/R3F extractors."""
        self.scene_extractor = ThreeJSSceneExtractor()
        self.component_extractor = ThreeJSComponentExtractor()
        self.material_extractor = ThreeJSMaterialExtractor()
        self.animation_extractor = ThreeJSAnimationExtractor()
        self.api_extractor = ThreeJSAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> ThreeJSParseResult:
        """
        Parse Three.js/R3F source code and extract all 3D-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Three.js/R3F is detected. It extracts scene structures, 3D
        components, materials/shaders, animations, and API usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ThreeJSParseResult with all extracted information
        """
        result = ThreeJSParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract scene-level constructs ────────────────────────
        scene_result = self.scene_extractor.extract(content, file_path)
        result.canvases = scene_result.get('canvases', [])
        result.cameras = scene_result.get('cameras', [])
        result.renderers = scene_result.get('renderers', [])
        result.controls = scene_result.get('controls', [])
        result.lights = scene_result.get('lights', [])
        result.post_processing = scene_result.get('post_processing', [])
        result.physics = scene_result.get('physics', [])

        # ── Extract component constructs ──────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.meshes = comp_result.get('meshes', [])
        result.groups = comp_result.get('groups', [])
        result.instanced_meshes = comp_result.get('instanced_meshes', [])
        result.drei_components = comp_result.get('drei_components', [])
        result.custom_components = comp_result.get('custom_components', [])
        result.models = comp_result.get('models', [])

        # ── Extract material constructs ───────────────────────────
        mat_result = self.material_extractor.extract(content, file_path)
        result.materials = mat_result.get('materials', [])
        result.shaders = mat_result.get('shaders', [])
        result.textures = mat_result.get('textures', [])
        result.uniforms = mat_result.get('uniforms', [])

        # ── Extract animation constructs ──────────────────────────
        anim_result = self.animation_extractor.extract(content, file_path)
        result.use_frames = anim_result.get('use_frames', [])
        result.animation_mixers = anim_result.get('animation_mixers', [])
        result.spring_animations = anim_result.get('spring_animations', [])
        result.tweens = anim_result.get('tweens', [])
        result.morph_targets = anim_result.get('morph_targets', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])

        # Framework info from API extractor
        fw_info = api_result.get('framework_info', {})
        result.is_vanilla = fw_info.get('is_vanilla', False)
        result.is_r3f = fw_info.get('is_r3f', False)
        result.detected_features = fw_info.get('features', [])

        # ── Detect versions ───────────────────────────────────────
        result.threejs_version = self._detect_threejs_version(content)
        result.r3f_version = self._detect_r3f_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Three.js ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_threejs_version(self, content: str) -> str:
        """Detect minimum Three.js revision from features used."""
        max_rev = ''
        for feature, rev in self.THREEJS_VERSION_FEATURES.items():
            if feature in content:
                if not max_rev or self._rev_compare(rev, max_rev) > 0:
                    max_rev = rev
        return max_rev

    def _detect_r3f_version(self, content: str) -> str:
        """Detect minimum R3F version from features used."""
        max_ver = ''
        for feature, ver in self.R3F_VERSION_FEATURES.items():
            if re.search(feature, content):
                if not max_ver or self._ver_compare(ver, max_ver) > 0:
                    max_ver = ver
        return max_ver

    @staticmethod
    def _rev_compare(r1: str, r2: str) -> int:
        """Compare Three.js revision strings (e.g., 'r150' vs 'r133')."""
        try:
            n1 = int(r1.lstrip('r'))
            n2 = int(r2.lstrip('r'))
            return n1 - n2
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def _ver_compare(v1: str, v2: str) -> int:
        """Compare R3F version strings (e.g., 'v8' vs 'v6')."""
        try:
            n1 = int(v1.lstrip('v'))
            n2 = int(v2.lstrip('v'))
            return n1 - n2
        except (ValueError, AttributeError):
            return 0

    def is_threejs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Three.js/R3F code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Three.js/R3F code
        """
        # Check for Three.js imports
        if re.search(r"from\s+['\"]three['\"]", content):
            return True

        # Check for R3F imports
        if re.search(r"from\s+['\"]@react-three/", content):
            return True

        # Check for THREE namespace usage
        if re.search(r'THREE\.\w+', content):
            return True

        # Check for R3F JSX elements
        if re.search(r'<Canvas[\s/>]|<mesh[\s/>]|<group[\s/>]', content):
            return True

        # Check for R3F hooks
        if re.search(r'\buseFrame\s*\(|\buseThree\s*\(|\buseLoader\s*\(', content):
            return True

        # Check for drei usage
        if re.search(r'\buseGLTF\s*\(|\buseTexture\s*\(|\buseFBX\s*\(', content):
            return True

        # Check for Three.js CDN
        if re.search(r'three\.(?:min\.)?js|three\.module\.js', content, re.IGNORECASE):
            return True

        # Check for three-stdlib
        if re.search(r"from\s+['\"]three-stdlib['\"]", content):
            return True

        return False
