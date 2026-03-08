"""
CodeTrellis Three.js / React Three Fiber Extractors Module v1.0

Provides comprehensive extractors for Three.js and React Three Fiber (R3F):

Scene Extractor:
- ThreeJSSceneExtractor: Canvas/scene setup, camera, renderer, controls,
                          postprocessing, physics, shadows, fog, background

Component Extractor:
- ThreeJSComponentExtractor: R3F components (mesh, group, instancedMesh),
                              drei components, custom 3D components,
                              Three.js class-based objects

Material Extractor:
- ThreeJSMaterialExtractor: Built-in materials, ShaderMaterial, custom shaders,
                              textures, uniforms, GLSL code patterns

Animation Extractor:
- ThreeJSAnimationExtractor: useFrame hooks, gsap/tween animations,
                              spring animations, keyframe animations,
                              AnimationMixer, morph targets

API Extractor:
- ThreeJSAPIExtractor: Import detection (three, @react-three/fiber,
                        @react-three/drei, @react-three/postprocessing,
                        @react-three/rapier, @react-three/xr, etc.),
                        framework/version detection, TypeScript types

Part of CodeTrellis — Three.js / React Three Fiber Language Support
"""

from .scene_extractor import (
    ThreeJSSceneExtractor,
    ThreeJSCanvasInfo,
    ThreeJSCameraInfo,
    ThreeJSRendererInfo,
    ThreeJSControlsInfo,
    ThreeJSLightInfo,
    ThreeJSPostProcessingInfo,
    ThreeJSPhysicsInfo,
)
from .component_extractor import (
    ThreeJSComponentExtractor,
    ThreeJSMeshInfo,
    ThreeJSGroupInfo,
    ThreeJSInstancedMeshInfo,
    ThreeJSDreiComponentInfo,
    ThreeJSCustomComponentInfo,
    ThreeJSModelInfo,
)
from .material_extractor import (
    ThreeJSMaterialExtractor,
    ThreeJSMaterialInfo,
    ThreeJSShaderInfo,
    ThreeJSTextureInfo,
    ThreeJSUniformInfo,
)
from .animation_extractor import (
    ThreeJSAnimationExtractor,
    ThreeJSUseFrameInfo,
    ThreeJSAnimationMixerInfo,
    ThreeJSSpringAnimationInfo,
    ThreeJSTweenInfo,
    ThreeJSMorphTargetInfo,
)
from .api_extractor import (
    ThreeJSAPIExtractor,
    ThreeJSImportInfo,
    ThreeJSIntegrationInfo,
    ThreeJSTypeInfo,
)

__all__ = [
    # Scene extractor
    "ThreeJSSceneExtractor",
    "ThreeJSCanvasInfo",
    "ThreeJSCameraInfo",
    "ThreeJSRendererInfo",
    "ThreeJSControlsInfo",
    "ThreeJSLightInfo",
    "ThreeJSPostProcessingInfo",
    "ThreeJSPhysicsInfo",
    # Component extractor
    "ThreeJSComponentExtractor",
    "ThreeJSMeshInfo",
    "ThreeJSGroupInfo",
    "ThreeJSInstancedMeshInfo",
    "ThreeJSDreiComponentInfo",
    "ThreeJSCustomComponentInfo",
    "ThreeJSModelInfo",
    # Material extractor
    "ThreeJSMaterialExtractor",
    "ThreeJSMaterialInfo",
    "ThreeJSShaderInfo",
    "ThreeJSTextureInfo",
    "ThreeJSUniformInfo",
    # Animation extractor
    "ThreeJSAnimationExtractor",
    "ThreeJSUseFrameInfo",
    "ThreeJSAnimationMixerInfo",
    "ThreeJSSpringAnimationInfo",
    "ThreeJSTweenInfo",
    "ThreeJSMorphTargetInfo",
    # API extractor
    "ThreeJSAPIExtractor",
    "ThreeJSImportInfo",
    "ThreeJSIntegrationInfo",
    "ThreeJSTypeInfo",
]
