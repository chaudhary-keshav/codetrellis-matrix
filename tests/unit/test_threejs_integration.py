"""
Tests for Three.js / React Three Fiber integration.

Tests cover:
- All 5 extractors (scene, component, material, animation, api)
- Parser (EnhancedThreeJSParser)
- Scanner integration (ProjectMatrix fields, _parse_threejs)
- Compressor integration ([THREEJS_*] sections)
"""

import pytest
from codetrellis.extractors.threejs import (
    ThreeJSSceneExtractor,
    ThreeJSComponentExtractor,
    ThreeJSMaterialExtractor,
    ThreeJSAnimationExtractor,
    ThreeJSAPIExtractor,
)
from codetrellis.threejs_parser_enhanced import EnhancedThreeJSParser, ThreeJSParseResult


# ═══════════════════════════════════════════════════════════════════════
# Scene Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSSceneExtractor:
    """Tests for ThreeJSSceneExtractor."""

    def setup_method(self):
        self.extractor = ThreeJSSceneExtractor()

    def test_r3f_canvas_detection(self):
        code = '''
import { Canvas } from '@react-three/fiber'

function App() {
  return (
    <Canvas shadows camera={{ position: [0, 5, 10] }} dpr={[1, 2]} frameloop="demand">
      <Scene />
    </Canvas>
  )
}
'''
        result = self.extractor.extract(code, "App.tsx")
        assert len(result['canvases']) >= 1
        canvas = result['canvases'][0]
        assert canvas.has_shadows is True

    def test_perspective_camera_detection(self):
        code = '''
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['cameras']) >= 1
        assert result['cameras'][0].camera_type == 'perspective'

    def test_orthographic_camera_detection(self):
        code = '''
const camera = new THREE.OrthographicCamera(-10, 10, 10, -10, 0.1, 100)
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['cameras']) >= 1
        assert result['cameras'][0].camera_type == 'orthographic'

    def test_webgl_renderer_detection(self):
        code = '''
const renderer = new THREE.WebGLRenderer({ antialias: true })
renderer.shadowMap.enabled = true
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['renderers']) >= 1

    def test_orbit_controls_detection(self):
        code = '''
import { OrbitControls } from '@react-three/drei'

function Scene() {
  return <OrbitControls enableDamping />
}
'''
        result = self.extractor.extract(code, "Scene.tsx")
        assert len(result['controls']) >= 1
        ctrl = result['controls'][0]
        assert ctrl.controls_type == 'orbit'
        assert ctrl.is_drei is True

    def test_light_detection(self):
        code = '''
function Scene() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} castShadow />
      <pointLight position={[0, 5, 0]} />
    </>
  )
}
'''
        result = self.extractor.extract(code, "Scene.tsx")
        assert len(result['lights']) >= 3

    def test_r3f_post_processing_detection(self):
        code = '''
import { EffectComposer, Bloom, SSAO, DepthOfField } from '@react-three/postprocessing'

function Effects() {
  return (
    <EffectComposer>
      <Bloom luminanceThreshold={0.5} />
      <SSAO radius={0.5} />
      <DepthOfField focusDistance={0.01} />
    </EffectComposer>
  )
}
'''
        result = self.extractor.extract(code, "Effects.tsx")
        assert len(result['post_processing']) >= 3

    def test_rapier_physics_detection(self):
        code = '''
import { Physics, RigidBody, CuboidCollider } from '@react-three/rapier'

function Scene() {
  return (
    <Physics debug gravity={[0, -9.81, 0]}>
      <RigidBody type="dynamic">
        <mesh>
          <boxGeometry />
          <meshStandardMaterial />
        </mesh>
      </RigidBody>
    </Physics>
  )
}
'''
        result = self.extractor.extract(code, "Physics.tsx")
        assert len(result['physics']) >= 1
        assert result['physics'][0].engine == 'rapier'

    def test_vanilla_controls_detection(self):
        code = '''
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
const controls = new OrbitControls(camera, renderer.domElement)
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['controls']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSComponentExtractor:
    """Tests for ThreeJSComponentExtractor."""

    def setup_method(self):
        self.extractor = ThreeJSComponentExtractor()

    def test_r3f_mesh_detection(self):
        code = '''
function Box(props) {
  const ref = useRef()
  return (
    <mesh ref={ref} {...props}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="hotpink" />
    </mesh>
  )
}
'''
        result = self.extractor.extract(code, "Box.tsx")
        assert len(result['meshes']) >= 1

    def test_vanilla_mesh_detection(self):
        code = '''
const geometry = new THREE.BoxGeometry(1, 1, 1)
const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 })
const cube = new THREE.Mesh(geometry, material)
scene.add(cube)
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['meshes']) >= 1

    def test_group_detection(self):
        code = '''
function Scene() {
  return (
    <group position={[0, 0, 0]}>
      <mesh><boxGeometry /><meshBasicMaterial /></mesh>
      <mesh><sphereGeometry /><meshBasicMaterial /></mesh>
    </group>
  )
}
'''
        result = self.extractor.extract(code, "Scene.tsx")
        assert len(result['groups']) >= 1

    def test_instanced_mesh_detection(self):
        code = '''
function Instances() {
  return (
    <instancedMesh args={[null, null, 1000]}>
      <boxGeometry />
      <meshStandardMaterial />
    </instancedMesh>
  )
}
'''
        result = self.extractor.extract(code, "Instances.tsx")
        assert len(result['instanced_meshes']) >= 1

    def test_drei_component_detection(self):
        code = '''
import { Text, Html, Float, OrbitControls, Environment } from '@react-three/drei'

function Scene() {
  return (
    <>
      <Float speed={1.5}>
        <Text fontSize={0.5}>Hello</Text>
      </Float>
      <Html>
        <div>Overlay</div>
      </Html>
      <Environment preset="city" />
    </>
  )
}
'''
        result = self.extractor.extract(code, "Scene.tsx")
        assert len(result['drei_components']) >= 1

    def test_gltf_model_detection(self):
        code = '''
import { useGLTF } from '@react-three/drei'

function Model(props) {
  const { scene } = useGLTF('/model.glb')
  return <primitive object={scene} {...props} />
}

useGLTF.preload('/model.glb')
'''
        result = self.extractor.extract(code, "Model.tsx")
        assert len(result['models']) >= 1
        # First model is from useGLTF usage
        gltf_models = [m for m in result['models'] if m.loader_type == 'gltf']
        assert len(gltf_models) >= 1
        # Preload creates a separate model entry with is_preloaded=True
        preloaded = [m for m in result['models'] if m.is_preloaded]
        assert len(preloaded) >= 1

    def test_extend_detection(self):
        code = '''
import { extend } from '@react-three/fiber'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer'

extend({ EffectComposer })
'''
        result = self.extractor.extract(code, "setup.ts")
        assert len(result['custom_components']) >= 1

    def test_vanilla_group_detection(self):
        code = '''
const group = new THREE.Group()
group.add(mesh1)
group.add(mesh2)
scene.add(group)
'''
        result = self.extractor.extract(code, "scene.js")
        assert len(result['groups']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Material Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSMaterialExtractor:
    """Tests for ThreeJSMaterialExtractor."""

    def setup_method(self):
        self.extractor = ThreeJSMaterialExtractor()

    def test_r3f_material_detection(self):
        code = '''
function Box() {
  return (
    <mesh>
      <boxGeometry />
      <meshStandardMaterial color="hotpink" metalness={0.8} roughness={0.2} />
    </mesh>
  )
}
'''
        result = self.extractor.extract(code, "Box.tsx")
        assert len(result['materials']) >= 1

    def test_vanilla_material_detection(self):
        code = '''
const material = new THREE.MeshPhysicalMaterial({
  color: 0xff0000,
  metalness: 1.0,
  roughness: 0.0,
  clearcoat: 1.0
})
'''
        result = self.extractor.extract(code, "material.js")
        assert len(result['materials']) >= 1

    def test_shader_material_detection(self):
        code = '''
const material = new THREE.ShaderMaterial({
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    varying vec2 vUv;
    uniform float uTime;
    void main() {
      gl_FragColor = vec4(vUv, sin(uTime), 1.0);
    }
  `,
  uniforms: {
    uTime: { value: 0.0 }
  }
})
'''
        result = self.extractor.extract(code, "shader.js")
        assert len(result['shaders']) >= 1

    def test_glsl_vertex_shader_detection(self):
        code = '''
const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
'''
        result = self.extractor.extract(code, "shader.ts")
        assert len(result['shaders']) >= 1

    def test_texture_detection(self):
        code = '''
import { useTexture } from '@react-three/drei'

function Ground() {
  const texture = useTexture('/grass.jpg')
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[100, 100]} />
      <meshStandardMaterial map={texture} />
    </mesh>
  )
}
'''
        result = self.extractor.extract(code, "Ground.tsx")
        assert len(result['textures']) >= 1

    def test_uniform_detection(self):
        code = '''
const uniforms = {
  uTime: { value: 0 },
  uResolution: { value: new THREE.Vector2() },
  uColor: { value: new THREE.Color(0xff0000) }
}
'''
        result = self.extractor.extract(code, "shader.js")
        assert len(result['uniforms']) >= 1

    def test_drei_material_detection(self):
        code = '''
import { MeshTransmissionMaterial } from '@react-three/drei'

function Glass() {
  return (
    <mesh>
      <sphereGeometry />
      <MeshTransmissionMaterial thickness={0.5} chromaticAberration={0.5} />
    </mesh>
  )
}
'''
        result = self.extractor.extract(code, "Glass.tsx")
        assert len(result['materials']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Animation Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSAnimationExtractor:
    """Tests for ThreeJSAnimationExtractor."""

    def setup_method(self):
        self.extractor = ThreeJSAnimationExtractor()

    def test_use_frame_detection(self):
        code = '''
function RotatingBox() {
  const ref = useRef()
  useFrame((state, delta) => {
    ref.current.rotation.x += delta
    ref.current.rotation.y += delta * 0.5
  })
  return <mesh ref={ref}><boxGeometry /><meshStandardMaterial /></mesh>
}
'''
        result = self.extractor.extract(code, "RotatingBox.tsx")
        assert len(result['use_frames']) >= 1

    def test_use_frame_with_state(self):
        code = '''
useFrame(({ clock, camera }) => {
  camera.position.y = Math.sin(clock.elapsedTime) * 2
})
'''
        result = self.extractor.extract(code, "scene.tsx")
        assert len(result['use_frames']) >= 1

    def test_animation_mixer_detection(self):
        code = '''
const mixer = new THREE.AnimationMixer(model)
const action = mixer.clipAction(animations[0])
action.play()
'''
        result = self.extractor.extract(code, "animation.js")
        assert len(result['animation_mixers']) >= 1
        assert result['animation_mixers'][0].has_clip_action is True

    def test_use_animations_drei(self):
        code = '''
import { useAnimations, useGLTF } from '@react-three/drei'

function Character() {
  const { scene, animations } = useGLTF('/character.glb')
  const { actions } = useAnimations(animations, scene)
  useEffect(() => { actions.walk?.play() }, [])
  return <primitive object={scene} />
}
'''
        result = self.extractor.extract(code, "Character.tsx")
        assert len(result['animation_mixers']) >= 1
        assert result['animation_mixers'][0].is_drei is True

    def test_spring_animation_detection(self):
        code = '''
import { useSpring, animated } from '@react-spring/three'

function AnimatedBox() {
  const spring = useSpring({ scale: 1.5, config: { mass: 1, tension: 170 } })
  return (
    <animated.mesh scale={spring.scale}>
      <boxGeometry />
      <meshStandardMaterial />
    </animated.mesh>
  )
}
'''
        result = self.extractor.extract(code, "AnimatedBox.tsx")
        assert len(result['spring_animations']) >= 1

    def test_gsap_detection(self):
        code = '''
import gsap from 'gsap'

useEffect(() => {
  gsap.to(meshRef.current.position, { x: 5, duration: 2 })
  gsap.from(meshRef.current.scale, { x: 0, y: 0, z: 0, duration: 1 })
}, [])
'''
        result = self.extractor.extract(code, "animation.tsx")
        assert len(result['tweens']) >= 2

    def test_morph_target_detection(self):
        code = '''
function Face() {
  useFrame(() => {
    mesh.morphTargetInfluences[0] = Math.sin(Date.now() * 0.001)
  })
}
'''
        result = self.extractor.extract(code, "Face.tsx")
        assert len(result['morph_targets']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSAPIExtractor:
    """Tests for ThreeJSAPIExtractor."""

    def setup_method(self):
        self.extractor = ThreeJSAPIExtractor()

    def test_named_import_detection(self):
        code = '''
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
'''
        result = self.extractor.extract(code, "Scene.tsx")
        assert len(result['imports']) >= 2
        # Check specifiers
        fiber_import = [i for i in result['imports'] if i.source == '@react-three/fiber']
        assert len(fiber_import) >= 1
        assert 'Canvas' in fiber_import[0].specifiers

    def test_namespace_import_detection(self):
        code = '''
import * as THREE from 'three'
'''
        result = self.extractor.extract(code, "scene.ts")
        assert len(result['imports']) >= 1
        assert result['imports'][0].is_namespace is True

    def test_dynamic_import_detection(self):
        code = '''
const module = await import('three/examples/jsm/loaders/GLTFLoader')
'''
        result = self.extractor.extract(code, "loader.ts")
        assert len(result['imports']) >= 1
        assert result['imports'][0].is_dynamic is True

    def test_integration_detection(self):
        code = '''
import { useControls } from 'leva'
import create from 'zustand'
'''
        result = self.extractor.extract(code, "store.ts")
        assert len(result['integrations']) >= 2

    def test_framework_info_detection(self):
        code = '''
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
'''
        result = self.extractor.extract(code, "Scene.tsx")
        fw = result['framework_info']
        assert fw['has_three'] is True
        assert fw['has_r3f'] is True
        assert fw['has_drei'] is True
        assert fw['is_r3f'] is True

    def test_vanilla_mode_detection(self):
        code = '''
import * as THREE from 'three'
const scene = new THREE.Scene()
'''
        result = self.extractor.extract(code, "scene.js")
        fw = result['framework_info']
        assert fw['has_three'] is True
        assert fw['is_vanilla'] is True
        assert fw['is_r3f'] is False

    def test_type_import_detection(self):
        code = '''
import type { ThreeElements } from '@react-three/fiber'
'''
        result = self.extractor.extract(code, "types.ts")
        assert len(result['imports']) >= 1
        assert result['imports'][0].is_type_only is True

    def test_feature_detection(self):
        code = '''
import { Canvas, useFrame } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import { Physics, RigidBody } from '@react-three/rapier'

function App() {
  return (
    <Canvas>
      <Physics>
        <RigidBody>
          <mesh onClick={() => {}}>
            <boxGeometry />
          </mesh>
        </RigidBody>
      </Physics>
      <EffectComposer>
        <Bloom />
      </EffectComposer>
    </Canvas>
  )
}
'''
        result = self.extractor.extract(code, "App.tsx")
        fw = result['framework_info']
        features = fw['features']
        assert 'canvas' in features
        assert 'render-loop' in features
        assert 'post-processing' in features
        assert 'physics' in features
        assert 'interaction' in features


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedThreeJSParser:
    """Tests for EnhancedThreeJSParser."""

    def setup_method(self):
        self.parser = EnhancedThreeJSParser()

    def test_is_threejs_file_r3f(self):
        code = '''
import { Canvas, useFrame } from '@react-three/fiber'
'''
        assert self.parser.is_threejs_file(code, "Scene.tsx") is True

    def test_is_threejs_file_vanilla(self):
        code = '''
import * as THREE from 'three'
'''
        assert self.parser.is_threejs_file(code, "scene.js") is True

    def test_is_threejs_file_negative(self):
        code = '''
import React from 'react'
function App() { return <div>Hello</div> }
'''
        assert self.parser.is_threejs_file(code, "App.tsx") is False

    def test_is_threejs_file_jsx_elements(self):
        code = '''
function Scene() {
  return <Canvas><mesh><boxGeometry /></mesh></Canvas>
}
'''
        assert self.parser.is_threejs_file(code, "Scene.jsx") is True

    def test_full_parse_r3f(self):
        code = '''
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, useGLTF } from '@react-three/drei'
import { Physics, RigidBody } from '@react-three/rapier'
import * as THREE from 'three'

function RotatingBox() {
  const ref = useRef()
  useFrame((state, delta) => {
    ref.current.rotation.x += delta
  })
  return (
    <mesh ref={ref} castShadow>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="hotpink" metalness={0.8} />
    </mesh>
  )
}

function Model(props) {
  const { scene } = useGLTF('/robot.glb')
  return <primitive object={scene} />
}

function App() {
  return (
    <Canvas shadows camera={{ position: [0, 5, 10] }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} castShadow />
      <Physics>
        <RigidBody>
          <RotatingBox />
        </RigidBody>
      </Physics>
      <Model />
      <OrbitControls />
      <Environment preset="sunset" />
    </Canvas>
  )
}
'''
        result = self.parser.parse(code, "App.tsx")
        assert isinstance(result, ThreeJSParseResult)
        assert result.file_type == "tsx"

        # Check frameworks detected
        assert 'three' in result.detected_frameworks
        assert 'react-three-fiber' in result.detected_frameworks
        assert 'drei' in result.detected_frameworks
        assert 'rapier' in result.detected_frameworks

        # Check scene constructs
        assert len(result.canvases) >= 1
        assert len(result.lights) >= 2
        assert len(result.controls) >= 1
        assert len(result.physics) >= 1

        # Check components
        assert len(result.meshes) >= 1
        assert len(result.models) >= 1

        # Check materials
        assert len(result.materials) >= 1

        # Check animations
        assert len(result.use_frames) >= 1

        # Check API
        assert len(result.imports) >= 1
        assert result.is_r3f is True

    def test_full_parse_vanilla(self):
        code = '''
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

const scene = new THREE.Scene()
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
const renderer = new THREE.WebGLRenderer({ antialias: true })

const geometry = new THREE.BoxGeometry(1, 1, 1)
const material = new THREE.MeshStandardMaterial({ color: 0xff0000 })
const cube = new THREE.Mesh(geometry, material)
scene.add(cube)

const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
scene.add(ambientLight)

const controls = new OrbitControls(camera, renderer.domElement)

function animate() {
  requestAnimationFrame(animate)
  cube.rotation.x += 0.01
  cube.rotation.y += 0.01
  controls.update()
  renderer.render(scene, camera)
}
animate()
'''
        result = self.parser.parse(code, "scene.js")
        assert isinstance(result, ThreeJSParseResult)
        assert result.file_type == "js"
        assert 'three' in result.detected_frameworks
        assert len(result.cameras) >= 1
        assert len(result.renderers) >= 1
        assert len(result.meshes) >= 1
        assert len(result.materials) >= 1
        assert len(result.lights) >= 1
        assert len(result.controls) >= 1
        assert result.is_vanilla is True

    def test_detect_threejs_version(self):
        code = '''
import { WebGPURenderer } from 'three/examples/jsm/renderers/webgpu/WebGPURenderer'
'''
        result = self.parser.parse(code, "render.ts")
        assert result.threejs_version == 'r160'

    def test_detect_r3f_version(self):
        code = '''
import { Canvas, useFrame, useThree } from '@react-three/fiber'
useFrame(({ camera }) => {})
'''
        result = self.parser.parse(code, "Scene.tsx")
        # useFrame is v1+, useThree is v5+
        assert result.r3f_version in ['v5', 'v7', 'v8', 'v1']

    def test_framework_detection(self):
        code = '''
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Physics } from '@react-three/rapier'
import { EffectComposer } from '@react-three/postprocessing'
import { XR } from '@react-three/xr'
import { useControls } from 'leva'
import create from 'zustand'
'''
        result = self.parser.parse(code, "App.tsx")
        fws = result.detected_frameworks
        assert 'react-three-fiber' in fws
        assert 'drei' in fws
        assert 'rapier' in fws
        assert 'postprocessing' in fws
        assert 'xr' in fws
        assert 'leva' in fws
        assert 'zustand' in fws


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSScannerIntegration:
    """Tests for scanner.py Three.js/R3F integration."""

    def test_project_matrix_has_threejs_fields(self):
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name="test", root_path="/tmp/test")
        # Verify all Three.js fields exist
        assert hasattr(m, 'threejs_canvases')
        assert hasattr(m, 'threejs_cameras')
        assert hasattr(m, 'threejs_renderers')
        assert hasattr(m, 'threejs_controls')
        assert hasattr(m, 'threejs_lights')
        assert hasattr(m, 'threejs_post_processing')
        assert hasattr(m, 'threejs_physics')
        assert hasattr(m, 'threejs_meshes')
        assert hasattr(m, 'threejs_groups')
        assert hasattr(m, 'threejs_instanced_meshes')
        assert hasattr(m, 'threejs_drei_components')
        assert hasattr(m, 'threejs_custom_components')
        assert hasattr(m, 'threejs_models')
        assert hasattr(m, 'threejs_materials')
        assert hasattr(m, 'threejs_shaders')
        assert hasattr(m, 'threejs_textures')
        assert hasattr(m, 'threejs_uniforms')
        assert hasattr(m, 'threejs_use_frames')
        assert hasattr(m, 'threejs_animation_mixers')
        assert hasattr(m, 'threejs_spring_animations')
        assert hasattr(m, 'threejs_tweens')
        assert hasattr(m, 'threejs_morph_targets')
        assert hasattr(m, 'threejs_imports')
        assert hasattr(m, 'threejs_integrations')
        assert hasattr(m, 'threejs_types')
        assert hasattr(m, 'threejs_detected_frameworks')
        assert hasattr(m, 'threejs_detected_features')
        assert hasattr(m, 'threejs_version')
        assert hasattr(m, 'threejs_r3f_version')
        assert hasattr(m, 'threejs_is_vanilla')
        assert hasattr(m, 'threejs_is_r3f')

    def test_project_matrix_default_values(self):
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name="test", root_path="/tmp/test")
        assert m.threejs_canvases == []
        assert m.threejs_meshes == []
        assert m.threejs_materials == []
        assert m.threejs_version == ""
        assert m.threejs_is_vanilla is False
        assert m.threejs_is_r3f is False

    def test_scanner_has_threejs_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, 'threejs_parser')
        assert isinstance(scanner.threejs_parser, EnhancedThreeJSParser)

    def test_scanner_has_parse_threejs_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, '_parse_threejs')
        assert callable(scanner._parse_threejs)


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSCompressorIntegration:
    """Tests for compressor.py Three.js/R3F integration."""

    def test_compressor_has_threejs_methods(self):
        from codetrellis.compressor import MatrixCompressor
        comp = MatrixCompressor()
        assert hasattr(comp, '_compress_threejs_scene')
        assert hasattr(comp, '_compress_threejs_components')
        assert hasattr(comp, '_compress_threejs_materials')
        assert hasattr(comp, '_compress_threejs_animations')
        assert hasattr(comp, '_compress_threejs_api')

    def test_compress_threejs_scene_empty(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        result = comp._compress_threejs_scene(matrix)
        assert result == []

    def test_compress_threejs_scene_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.threejs_canvases = [{"name": "Canvas", "file": "App.tsx", "line": 10, "has_shadows": True, "has_camera": False, "has_gl_config": False, "frameloop": "", "dpr": ""}]
        matrix.threejs_cameras = [{"name": "PerspectiveCamera", "file": "scene.js", "line": 5, "camera_type": "perspective"}]
        matrix.threejs_lights = [{"name": "ambientLight", "file": "Scene.tsx", "line": 3, "light_type": "ambient", "has_shadows": False, "is_helper": False}]
        result = comp._compress_threejs_scene(matrix)
        assert len(result) > 0
        assert any("Canvas" in line for line in result)
        assert any("Cameras" in line for line in result)
        assert any("Lights" in line for line in result)

    def test_compress_threejs_components_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.threejs_meshes = [{"name": "mesh", "file": "Box.tsx", "line": 5, "mesh_type": "mesh", "geometry": "boxGeometry", "material": "meshStandardMaterial", "is_r3f": True}]
        matrix.threejs_models = [{"name": "Model", "file": "Model.tsx", "line": 8, "model_format": "gltf", "loader": "useGLTF", "has_preload": True}]
        result = comp._compress_threejs_components(matrix)
        assert len(result) > 0
        assert any("Meshes" in line for line in result)
        assert any("Models" in line for line in result)

    def test_compress_threejs_api_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.threejs_detected_frameworks = ['three', 'react-three-fiber', 'drei', 'rapier']
        matrix.threejs_version = 'r160'
        matrix.threejs_r3f_version = 'v8'
        matrix.threejs_is_r3f = True
        matrix.threejs_detected_features = ['canvas', 'render-loop', 'physics']
        result = comp._compress_threejs_api(matrix)
        assert len(result) > 0
        assert any("ecosystem" in line for line in result)
        assert any("r160" in line for line in result)
        assert any("R3F" in line for line in result)

    def test_full_compression_includes_threejs_sections(self):
        """Verify that a full compression with Three.js data produces [THREEJS_*] sections."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.threejs_canvases = [{"name": "Canvas", "file": "App.tsx", "line": 10, "has_shadows": True, "has_camera": False, "has_gl_config": False, "frameloop": "", "dpr": ""}]
        matrix.threejs_meshes = [{"name": "mesh", "file": "Box.tsx", "line": 5, "mesh_type": "mesh", "geometry": "boxGeometry", "material": "meshStandardMaterial", "is_r3f": True}]
        matrix.threejs_materials = [{"name": "meshStandardMaterial", "file": "Box.tsx", "line": 7, "material_type": "standard", "is_r3f": True, "is_drei": False}]
        matrix.threejs_use_frames = [{"name": "useFrame", "file": "Anim.tsx", "line": 5, "has_delta": True, "has_ref_mutation": True, "updates": ["rotation"], "priority": ""}]
        matrix.threejs_detected_frameworks = ['three', 'react-three-fiber']
        matrix.threejs_version = 'r150'
        matrix.threejs_is_r3f = True

        # Run full compression
        output = comp.compress(matrix)
        assert "[THREEJS_SCENE]" in output
        assert "[THREEJS_COMPONENTS]" in output
        assert "[THREEJS_MATERIALS]" in output
        assert "[THREEJS_ANIMATIONS]" in output
        assert "[THREEJS_API]" in output


# ═══════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════

class TestThreeJSEdgeCases:
    """Edge case and regression tests."""

    def test_empty_file(self):
        parser = EnhancedThreeJSParser()
        assert parser.is_threejs_file("", "empty.js") is False

    def test_non_threejs_file(self):
        parser = EnhancedThreeJSParser()
        code = "console.log('hello world')"
        assert parser.is_threejs_file(code, "hello.js") is False

    def test_mixed_r3f_and_vanilla(self):
        parser = EnhancedThreeJSParser()
        code = '''
import * as THREE from 'three'
import { Canvas, useFrame } from '@react-three/fiber'

const vec = new THREE.Vector3()

function Scene() {
  useFrame(({ camera }) => {
    camera.position.lerp(vec.set(0, 5, 10), 0.1)
  })
  return <mesh><boxGeometry /><meshStandardMaterial /></mesh>
}
'''
        result = parser.parse(code, "Scene.tsx")
        assert 'three' in result.detected_frameworks
        assert 'react-three-fiber' in result.detected_frameworks
        assert result.is_r3f is True

    def test_large_drei_import(self):
        extractor = ThreeJSAPIExtractor()
        code = '''
import {
  OrbitControls, TransformControls, PivotControls,
  Html, Text, Text3D, Billboard,
  Sphere, Box, Plane, Torus, Cylinder,
  Environment, Sky, Stars, Cloud,
  Float, MeshDistortMaterial, MeshReflectorMaterial,
  useGLTF, useFBX, useTexture, useAnimations,
  Sparkles, Trail, Line, QuadraticBezierLine,
  PerspectiveCamera, OrthographicCamera,
  ContactShadows, AccumulativeShadows, RandomizedLight,
  Loader, useProgress, PerformanceMonitor,
  Preload, BakeShadows, AdaptiveDpr, AdaptiveEvents,
  SoftShadows, Lightformer, KeyboardControls
} from '@react-three/drei'
'''
        result = extractor.extract(code, "imports.tsx")
        assert len(result['imports']) >= 1
        # Should have many specifiers
        drei_import = [i for i in result['imports'] if i.source == '@react-three/drei']
        assert len(drei_import) >= 1
        assert len(drei_import[0].specifiers) > 10

    def test_typescript_three_types(self):
        extractor = ThreeJSAPIExtractor()
        code = '''
import { useRef } from 'react'
import * as THREE from 'three'
import type { ThreeElements } from '@react-three/fiber'

const meshRef = useRef<THREE.Mesh>(null)
const vec: THREE.Vector3 = new THREE.Vector3(1, 2, 3)
'''
        result = extractor.extract(code, "types.tsx")
        assert len(result['types']) >= 1
