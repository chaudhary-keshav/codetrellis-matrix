"""
Three.js / React Three Fiber Component Extractor

Extracts 3D component constructs:
- R3F primitive components (mesh, group, instancedMesh, line, points, sprite)
- Three.js class-based objects (Mesh, Group, InstancedMesh, etc.)
- Drei helper components (Text, Html, Image, Billboard, Float, etc.)
- Geometry types (box, sphere, plane, torus, custom buffer geometry)
- GLTF/GLB model loading (useGLTF, GLTFLoader, useLoader)
- Custom R3F components (extend(), forwardRef with Three.js objects)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ThreeJSMeshInfo:
    """Mesh or primitive 3D object."""
    name: str
    file: str
    line_number: int
    mesh_type: str  # 'mesh', 'instanced_mesh', 'skinned_mesh', 'line', 'points', 'sprite', 'lod'
    geometry: str  # 'box', 'sphere', 'plane', 'torus', 'buffer', 'custom', etc.
    material: str  # material type used, if detectable
    has_ref: bool = False
    has_cast_shadow: bool = False
    has_receive_shadow: bool = False
    has_onClick: bool = False
    has_onPointer: bool = False
    has_position: bool = False
    has_rotation: bool = False
    has_scale: bool = False
    is_r3f: bool = True


@dataclass
class ThreeJSGroupInfo:
    """Group or scene node."""
    name: str
    file: str
    line_number: int
    group_type: str  # 'group', 'scene', 'object3d'
    children_count: int = 0
    has_ref: bool = False
    is_r3f: bool = True


@dataclass
class ThreeJSInstancedMeshInfo:
    """Instanced mesh for rendering many copies efficiently."""
    name: str
    file: str
    line_number: int
    count: str  # instance count expression
    geometry: str = ""
    material: str = ""
    has_instance_color: bool = False
    has_instance_matrix: bool = False
    is_r3f: bool = True
    is_drei_instances: bool = False


@dataclass
class ThreeJSDreiComponentInfo:
    """Drei helper component usage."""
    name: str  # component name (Text, Html, Image, etc.)
    file: str
    line_number: int
    category: str  # 'text', 'html', 'gizmo', 'loader', 'shape', 'staging', 'misc', 'abstractions', 'controls', 'performance'
    props: List[str] = field(default_factory=list)


@dataclass
class ThreeJSCustomComponentInfo:
    """Custom R3F component or extended Three.js class."""
    name: str
    file: str
    line_number: int
    component_type: str  # 'r3f_component', 'extend', 'use_gltf', 'use_loader', 'use_fbx'
    base_class: str = ""  # for extend()
    model_path: str = ""  # for useGLTF/useLoader
    is_exported: bool = False
    hooks_used: List[str] = field(default_factory=list)


@dataclass
class ThreeJSModelInfo:
    """3D model loading."""
    name: str
    file: str
    line_number: int
    loader_type: str  # 'gltf', 'fbx', 'obj', 'draco', 'ktx2', 'exr', 'hdr'
    model_path: str = ""
    is_preloaded: bool = False
    has_animations: bool = False
    has_draco: bool = False


class ThreeJSComponentExtractor:
    """Extracts Three.js/R3F component constructs."""

    # R3F mesh patterns (JSX lowercase for Three.js primitives)
    R3F_MESH_PATTERN = re.compile(
        r'<(mesh|skinnedMesh|instancedMesh|line|lineSegments|lineLoop|points|sprite|lod)\b([^>]*?)(?:/>|>)',
        re.DOTALL
    )

    # Vanilla Three.js mesh patterns
    VANILLA_MESH_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(Mesh|SkinnedMesh|InstancedMesh|Line|LineSegments|LineLoop|Points|Sprite|LOD)\s*\(',
    )

    # R3F geometry patterns (JSX lowercase)
    R3F_GEOMETRY_PATTERNS = re.compile(
        r'<(boxGeometry|sphereGeometry|planeGeometry|cylinderGeometry|coneGeometry|'
        r'torusGeometry|torusKnotGeometry|ringGeometry|circleGeometry|'
        r'dodecahedronGeometry|icosahedronGeometry|octahedronGeometry|'
        r'tetrahedronGeometry|capsuleGeometry|latheGeometry|extrudeGeometry|'
        r'shapeGeometry|tubeGeometry|bufferGeometry|edgesGeometry)\b'
    )

    # Vanilla geometry patterns
    VANILLA_GEOMETRY_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(BoxGeometry|SphereGeometry|PlaneGeometry|'
        r'CylinderGeometry|ConeGeometry|TorusGeometry|TorusKnotGeometry|'
        r'BufferGeometry|ExtrudeGeometry|LatheGeometry|ShapeGeometry|'
        r'TubeGeometry|RingGeometry|CircleGeometry|CapsuleGeometry|'
        r'DodecahedronGeometry|IcosahedronGeometry|OctahedronGeometry|'
        r'TetrahedronGeometry|EdgesGeometry|WireframeGeometry)\s*\('
    )

    # Group/scene patterns
    R3F_GROUP_PATTERN = re.compile(
        r'<(group|scene|object3D)\b', re.IGNORECASE
    )

    VANILLA_GROUP_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(Group|Scene|Object3D)\s*\('
    )

    # Drei components by category
    DREI_COMPONENTS = {
        'text': ['Text', 'Text3D', 'Billboard'],
        'html': ['Html', 'Hud'],
        'gizmo': ['GizmoHelper', 'GizmoViewcube', 'GizmoViewport', 'PivotControls', 'Grid', 'Helper'],
        'loader': ['useGLTF', 'useFBX', 'useOBJ', 'useTexture', 'useKTX2', 'useCubeTexture', 'Loader', 'useProgress'],
        'shape': ['RoundedBox', 'Torus', 'Box', 'Sphere', 'Plane', 'Cone', 'Cylinder', 'Ring', 'Dodecahedron', 'Icosahedron', 'Octahedron', 'Tetrahedron', 'Extrude', 'Lathe', 'Shape', 'Tube', 'TorusKnot', 'Circle', 'Capsule', 'Line', 'QuadraticBezierLine', 'CubicBezierLine', 'CatmullRomLine', 'Edges', 'Wireframe', 'Decal'],
        'staging': ['Center', 'Float', 'Stage', 'Backdrop', 'Environment', 'Lightformer', 'ContactShadows', 'AccumulativeShadows', 'RandomizedLight', 'BakeShadows', 'SoftShadows', 'Sky', 'Stars', 'Cloud', 'Sparkles', 'MeshReflectorMaterial', 'MeshRefractionMaterial', 'MeshTransmissionMaterial', 'MeshDiscardMaterial', 'MeshDistortMaterial', 'MeshWobbleMaterial', 'PointMaterial', 'SpotLight', 'SpotLightShadow'],
        'abstractions': ['Image', 'Reflector', 'CubeCamera', 'MeshPortalMaterial', 'Caustics', 'Decal', 'AsciiRenderer', 'ScreenSpace', 'ScreenSizer', 'Mask', 'useMask', 'Clone', 'Float', 'Detailed', 'Preload'],
        'performance': ['Instances', 'Instance', 'Merged', 'Points', 'Segments', 'PerformanceMonitor', 'AdaptiveDpr', 'AdaptiveEvents', 'Bvh', 'useDetectGPU'],
        'controls': ['OrbitControls', 'MapControls', 'TrackballControls', 'FlyControls', 'DeviceOrientationControls', 'PointerLockControls', 'FirstPersonControls', 'CameraControls', 'FaceControls', 'ScrollControls', 'PresentationControls', 'KeyboardControls'],
        'misc': ['useHelper', 'useContextBridge', 'useBVH', 'useCursor', 'useIntersect', 'useBoxProjectedEnv', 'View', 'Resize', 'CameraShake'],
    }

    DREI_PATTERN = re.compile(
        r'<(' + '|'.join(
            comp for cat_comps in DREI_COMPONENTS.values() for comp in cat_comps
            if not comp.startswith('use')
        ) + r')\b'
    )

    DREI_HOOK_PATTERN = re.compile(
        r'\b(' + '|'.join(
            comp for cat_comps in DREI_COMPONENTS.values() for comp in cat_comps
            if comp.startswith('use')
        ) + r')\s*\('
    )

    # Model loading patterns
    USE_GLTF_PATTERN = re.compile(
        r'(?:useGLTF|useLoader\s*\(\s*GLTFLoader)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    )
    USE_FBX_PATTERN = re.compile(
        r'(?:useFBX|useLoader\s*\(\s*FBXLoader)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    )
    USE_OBJ_PATTERN = re.compile(
        r'(?:useOBJ|useLoader\s*\(\s*OBJLoader)\s*\(\s*[\'"]([^\'"]+)[\'"]'
    )

    GLTF_LOADER_PATTERN = re.compile(
        r'new\s+GLTFLoader\s*\(\s*\)\.load\s*\(\s*[\'"]([^\'"]+)[\'"]'
    )

    PRELOAD_PATTERN = re.compile(
        r'useGLTF\.preload\s*\(\s*[\'"]([^\'"]+)[\'"]'
    )

    # extend() pattern
    EXTEND_PATTERN = re.compile(
        r'extend\s*\(\s*\{([^}]+)\}'
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract component constructs."""
        result = {
            'meshes': [],
            'groups': [],
            'instanced_meshes': [],
            'drei_components': [],
            'custom_components': [],
            'models': [],
        }

        # R3F mesh components
        for match in self.R3F_MESH_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            tag = match.group(1)
            attrs = match.group(2)
            mesh_type = self._normalize_mesh_type(tag)
            geometry = self._detect_geometry_in_children(content, match.end())

            if mesh_type == 'instanced_mesh':
                count_match = re.search(r'(?:args|count)\s*=\s*\{?\s*\[?\s*([^\]}\s,]+)', attrs or '')
                result['instanced_meshes'].append(ThreeJSInstancedMeshInfo(
                    name=tag,
                    file=file_path,
                    line_number=line_num,
                    count=count_match.group(1) if count_match else "",
                    geometry=geometry,
                ))
            else:
                result['meshes'].append(ThreeJSMeshInfo(
                    name=tag,
                    file=file_path,
                    line_number=line_num,
                    mesh_type=mesh_type,
                    geometry=geometry,
                    material=self._detect_material_in_children(content, match.end()),
                    has_ref=bool(re.search(r'\bref\s*=', attrs or '')),
                    has_cast_shadow=bool(re.search(r'\bcastShadow\b', attrs or '')),
                    has_receive_shadow=bool(re.search(r'\breceiveShadow\b', attrs or '')),
                    has_onClick=bool(re.search(r'\bonClick\b', attrs or '')),
                    has_onPointer=bool(re.search(r'\bonPointer\w+', attrs or '')),
                    has_position=bool(re.search(r'\bposition\b', attrs or '')),
                    has_rotation=bool(re.search(r'\brotation\b', attrs or '')),
                    has_scale=bool(re.search(r'\bscale\b', attrs or '')),
                    is_r3f=True,
                ))

        # Vanilla Three.js mesh objects
        for match in self.VANILLA_MESH_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            cls_name = match.group(1)
            result['meshes'].append(ThreeJSMeshInfo(
                name=cls_name,
                file=file_path,
                line_number=line_num,
                mesh_type=self._normalize_mesh_type(cls_name),
                geometry='',
                material='',
                is_r3f=False,
            ))

        # Groups
        for match in self.R3F_GROUP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['groups'].append(ThreeJSGroupInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                group_type=match.group(1).lower(),
                is_r3f=True,
            ))

        for match in self.VANILLA_GROUP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['groups'].append(ThreeJSGroupInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                group_type=match.group(1).lower(),
                is_r3f=False,
            ))

        # Drei components (JSX tags)
        for match in self.DREI_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            comp_name = match.group(1)
            category = self._categorize_drei(comp_name)
            result['drei_components'].append(ThreeJSDreiComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                category=category,
            ))

        # Drei hooks
        for match in self.DREI_HOOK_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            hook_name = match.group(1)
            category = self._categorize_drei(hook_name)
            result['drei_components'].append(ThreeJSDreiComponentInfo(
                name=hook_name,
                file=file_path,
                line_number=line_num,
                category=category,
            ))

        # Model loading
        for pattern, loader_type in [
            (self.USE_GLTF_PATTERN, 'gltf'),
            (self.USE_FBX_PATTERN, 'fbx'),
            (self.USE_OBJ_PATTERN, 'obj'),
            (self.GLTF_LOADER_PATTERN, 'gltf'),
        ]:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                model_path = match.group(1)
                result['models'].append(ThreeJSModelInfo(
                    name=model_path.split('/')[-1],
                    file=file_path,
                    line_number=line_num,
                    loader_type=loader_type,
                    model_path=model_path,
                    has_draco=bool(re.search(r'[Dd]raco', content)),
                ))

        # Preloaded models
        for match in self.PRELOAD_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            model_path = match.group(1)
            result['models'].append(ThreeJSModelInfo(
                name=model_path.split('/')[-1] + ' (preload)',
                file=file_path,
                line_number=line_num,
                loader_type='gltf',
                model_path=model_path,
                is_preloaded=True,
            ))

        # extend() for custom R3F elements
        for match in self.EXTEND_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            classes = re.findall(r'(\w+)', match.group(1))
            for cls in classes:
                result['custom_components'].append(ThreeJSCustomComponentInfo(
                    name=cls,
                    file=file_path,
                    line_number=line_num,
                    component_type='extend',
                    base_class=cls,
                ))

        return result

    def _normalize_mesh_type(self, name: str) -> str:
        """Normalize mesh type from tag/class name."""
        name_lower = name.lower()
        mapping = {
            'mesh': 'mesh', 'skinnedmesh': 'skinned_mesh',
            'instancedmesh': 'instanced_mesh',
            'line': 'line', 'linesegments': 'line', 'lineloop': 'line',
            'points': 'points', 'sprite': 'sprite', 'lod': 'lod',
        }
        return mapping.get(name_lower, 'mesh')

    def _categorize_drei(self, name: str) -> str:
        """Categorize a drei component/hook."""
        for category, components in self.DREI_COMPONENTS.items():
            if name in components:
                return category
        return 'misc'

    def _detect_geometry_in_children(self, content: str, start_pos: int) -> str:
        """Detect geometry type in mesh children (limited lookahead)."""
        lookahead = content[start_pos:start_pos + 300]
        match = self.R3F_GEOMETRY_PATTERNS.search(lookahead)
        if match:
            name = match.group(1)
            return name.replace('Geometry', '').lower()
        match = self.VANILLA_GEOMETRY_PATTERN.search(lookahead)
        if match:
            return match.group(1).replace('Geometry', '').lower()
        return ''

    def _detect_material_in_children(self, content: str, start_pos: int) -> str:
        """Detect material type in mesh children (limited lookahead)."""
        lookahead = content[start_pos:start_pos + 300]
        mat_pattern = re.compile(
            r'<(meshStandardMaterial|meshBasicMaterial|meshPhongMaterial|'
            r'meshLambertMaterial|meshPhysicalMaterial|meshToonMaterial|'
            r'meshNormalMaterial|meshMatcapMaterial|meshDepthMaterial|'
            r'shaderMaterial|rawShaderMaterial|pointsMaterial|'
            r'lineBasicMaterial|lineDashedMaterial|spriteMaterial)\b'
        )
        match = mat_pattern.search(lookahead)
        if match:
            return match.group(1).replace('Material', '').replace('mesh', '').lower()
        return ''
