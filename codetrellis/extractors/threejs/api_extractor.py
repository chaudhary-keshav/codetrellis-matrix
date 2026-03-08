"""
Three.js / React Three Fiber API Extractor

Extracts API-level constructs:
- Import detection (three, @react-three/fiber, @react-three/drei, etc.)
- Framework version detection
- TypeScript type usage
- CDN usage (legacy)
- Integration with other libraries (zustand, leva, tunnel-rat)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ThreeJSImportInfo:
    """Import statement for Three.js ecosystem."""
    name: str  # imported name
    file: str
    line_number: int
    source: str  # package name
    is_default: bool = False
    is_namespace: bool = False  # import * as THREE
    is_dynamic: bool = False  # dynamic import()
    is_type_only: bool = False  # import type { ... }
    specifiers: List[str] = field(default_factory=list)


@dataclass
class ThreeJSIntegrationInfo:
    """Integration with other libraries."""
    name: str  # library name
    file: str
    line_number: int
    integration_type: str  # 'state', 'ui', 'physics', 'audio', 'xr', 'a11y'
    version: str = ""


@dataclass
class ThreeJSTypeInfo:
    """TypeScript type usage for Three.js."""
    name: str  # type name
    file: str
    line_number: int
    source: str  # 'three', '@react-three/fiber', etc.
    type_kind: str  # 'interface', 'type', 'generic', 'ref'


class ThreeJSAPIExtractor:
    """Extracts API-level constructs from Three.js/R3F code."""

    # Three.js ecosystem packages
    THREEJS_PACKAGES = [
        'three',
        'three/examples/jsm',
        'three/addons',
        'three-stdlib',
        '@react-three/fiber',
        '@react-three/drei',
        '@react-three/postprocessing',
        '@react-three/rapier',
        '@react-three/cannon',
        '@react-three/xr',
        '@react-three/a11y',
        '@react-three/csg',
        '@react-three/flex',
        '@react-three/test-renderer',
        'postprocessing',
        'lamina',
        'leva',
        'r3f-perf',
        'maath',
        '@pmndrs/vanilla',
        '@pmndrs/assets',
        'suspend-react',
        'its-fine',
        'tunnel-rat',
        'zustand',
        'jotai',
        'valtio',
    ]

    # Pattern to match known packages
    THREEJS_PACKAGE_PATTERN = re.compile(
        r'(?:import|from)\s+["\']('
        + '|'.join(re.escape(pkg) for pkg in THREEJS_PACKAGES)
        + r')(?:/[^"\']*)?["\']'
    )

    # Named imports
    NAMED_IMPORT_PATTERN = re.compile(
        r'import\s*(?:type\s+)?\{\s*([^}]+)\}\s*from\s*["\']([^"\']+)["\']'
    )

    # Default import
    DEFAULT_IMPORT_PATTERN = re.compile(
        r'import\s+(\w+)\s+from\s*["\']([^"\']+)["\']'
    )

    # Namespace import  (import * as THREE from 'three')
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r'import\s*\*\s+as\s+(\w+)\s+from\s*["\']([^"\']+)["\']'
    )

    # Dynamic import
    DYNAMIC_IMPORT_PATTERN = re.compile(
        r'(?:await\s+)?import\s*\(\s*["\']([^"\']+)["\']'
    )

    # Type-only import
    TYPE_IMPORT_PATTERN = re.compile(
        r'import\s+type\s*\{\s*([^}]+)\}\s*from\s*["\']([^"\']+)["\']'
    )

    # require (commonjs)
    REQUIRE_PATTERN = re.compile(
        r'require\s*\(\s*["\']([^"\']+)["\']'
    )

    # CDN script tags (legacy)
    CDN_PATTERN = re.compile(
        r'<script[^>]*src=["\'][^"\']*(?:three\.(?:min\.)?js|three\.module\.js|'
        r'(?:cdn\.jsdelivr\.net|unpkg\.com|cdnjs\.cloudflare\.com)/[^"\']*three)[^"\']*["\']',
        re.IGNORECASE
    )

    # Three.js REVISION/version
    REVISION_PATTERN = re.compile(
        r'THREE\.REVISION|REVISION\s*=\s*["\'](\d+)["\']'
    )

    # TypeScript Three.js types
    TS_TYPE_PATTERNS = {
        'three_type': re.compile(
            r':\s*(THREE\.)?('
            r'Vector2|Vector3|Vector4|Matrix3|Matrix4|Quaternion|Euler|'
            r'Color|Box2|Box3|Sphere|Ray|Plane|Frustum|Triangle|'
            r'Scene|Group|Object3D|Mesh|Camera|'
            r'PerspectiveCamera|OrthographicCamera|'
            r'BufferGeometry|Material|MeshStandardMaterial|'
            r'ShaderMaterial|RawShaderMaterial|'
            r'Texture|DataTexture|CanvasTexture|'
            r'WebGLRenderer|WebGLRenderTarget|'
            r'AnimationMixer|AnimationClip|AnimationAction|'
            r'SkinnedMesh|Bone|Skeleton|'
            r'Light|DirectionalLight|PointLight|SpotLight|'
            r'Raycaster|Clock|Loader'
            r')\b'
        ),
        'r3f_type': re.compile(
            r':\s*(?:import\([^)]+\)\.)?('
            r'ThreeElements|RootState|RenderCallback|'
            r'GroupProps|MeshProps|CanvasProps|'
            r'ThreeEvent|Intersection|Camera|'
            r'Object3DNode|ExtendedColors|'
            r'ReactThreeFiber|Events'
            r')\b'
        ),
        'ref_type': re.compile(
            r'useRef\s*<\s*(THREE\.)?(\w+)\s*>'
        ),
    }

    # Integration libraries with categories
    INTEGRATION_PATTERNS = {
        'zustand': ('state', re.compile(r'(?:from|import)\s*["\']zustand["\']')),
        'jotai': ('state', re.compile(r'(?:from|import)\s*["\']jotai["\']')),
        'valtio': ('state', re.compile(r'(?:from|import)\s*["\']valtio["\']')),
        'leva': ('ui', re.compile(r'(?:from|import)\s*["\']leva["\']')),
        'dat.gui': ('ui', re.compile(r'(?:from|import)\s*["\']dat\.gui["\']')),
        'tweakpane': ('ui', re.compile(r'(?:from|import)\s*["\']tweakpane["\']')),
        'r3f-perf': ('perf', re.compile(r'(?:from|import)\s*["\']r3f-perf["\']')),
        'stats.js': ('perf', re.compile(r'(?:from|import)\s*["\']stats\.js["\']')),
        'tunnel-rat': ('rendering', re.compile(r'(?:from|import)\s*["\']tunnel-rat["\']')),
        'suspend-react': ('suspense', re.compile(r'(?:from|import)\s*["\']suspend-react["\']')),
        'maath': ('math', re.compile(r'(?:from|import)\s*["\']maath["\']')),
        'lamina': ('materials', re.compile(r'(?:from|import)\s*["\']lamina["\']')),
        '@use-gesture/react': ('gesture', re.compile(r'(?:from|import)\s*["\']@use-gesture/react["\']')),
    }

    # R3F Canvas configuration
    CANVAS_CONFIG_PATTERN = re.compile(
        r'<Canvas\s+([^>]+)>',
        re.DOTALL
    )

    # extend() usage (R3F custom elements)
    EXTEND_PATTERN = re.compile(
        r'extend\s*\(\s*\{([^}]+)\}'
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API-level constructs."""
        result = {
            'imports': [],
            'integrations': [],
            'types': [],
            'framework_info': {},
        }

        # Named imports from Three.js ecosystem
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            specifiers_str = match.group(1)
            source = match.group(2)
            if self._is_threejs_package(source):
                line_num = content[:match.start()].count('\n') + 1
                specifiers = [s.strip().split(' as ')[0].strip() for s in specifiers_str.split(',') if s.strip()]
                is_type_only = 'import type' in content[max(0, match.start()-12):match.start()+12]
                result['imports'].append(ThreeJSImportInfo(
                    name=source,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    is_type_only=is_type_only,
                    specifiers=specifiers[:50],  # cap at 50
                ))

        # Default imports
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            imported_name = match.group(1)
            source = match.group(2)
            if self._is_threejs_package(source):
                line_num = content[:match.start()].count('\n') + 1
                result['imports'].append(ThreeJSImportInfo(
                    name=imported_name,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    is_default=True,
                ))

        # Namespace imports
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            alias = match.group(1)
            source = match.group(2)
            if self._is_threejs_package(source):
                line_num = content[:match.start()].count('\n') + 1
                result['imports'].append(ThreeJSImportInfo(
                    name=alias,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    is_namespace=True,
                ))

        # Dynamic imports
        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(content):
            source = match.group(1)
            if self._is_threejs_package(source):
                line_num = content[:match.start()].count('\n') + 1
                result['imports'].append(ThreeJSImportInfo(
                    name=source,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    is_dynamic=True,
                ))

        # Type-only imports
        for match in self.TYPE_IMPORT_PATTERN.finditer(content):
            specifiers_str = match.group(1)
            source = match.group(2)
            if self._is_threejs_package(source):
                line_num = content[:match.start()].count('\n') + 1
                specifiers = [s.strip().split(' as ')[0].strip() for s in specifiers_str.split(',') if s.strip()]
                result['imports'].append(ThreeJSImportInfo(
                    name=source,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    is_type_only=True,
                    specifiers=specifiers[:50],
                ))

        # CDN usage
        for match in self.CDN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['imports'].append(ThreeJSImportInfo(
                name='three-cdn',
                file=file_path,
                line_number=line_num,
                source='cdn',
            ))

        # Integrations
        for lib_name, (category, pattern) in self.INTEGRATION_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                result['integrations'].append(ThreeJSIntegrationInfo(
                    name=lib_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=category,
                ))

        # TypeScript types
        for type_kind, pattern in self.TS_TYPE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Get the actual type name (last capture group)
                type_name = match.group(match.lastindex) if match.lastindex else match.group(0)
                source = 'three' if type_kind == 'three_type' else '@react-three/fiber'
                result['types'].append(ThreeJSTypeInfo(
                    name=type_name,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                    type_kind=type_kind,
                ))

        # Framework info summary
        result['framework_info'] = self._detect_framework_info(content, file_path)

        return result

    def _is_threejs_package(self, source: str) -> bool:
        """Check if import source is a Three.js ecosystem package."""
        for pkg in self.THREEJS_PACKAGES:
            if source == pkg or source.startswith(pkg + '/'):
                return True
        # Also match three/examples/jsm subpaths
        if source.startswith('three/'):
            return True
        return False

    def _detect_framework_info(self, content: str, file_path: str) -> Dict[str, Any]:
        """Detect which Three.js frameworks/versions are used."""
        info: Dict[str, Any] = {
            'has_three': False,
            'has_r3f': False,
            'has_drei': False,
            'has_postprocessing': False,
            'has_rapier': False,
            'has_cannon': False,
            'has_xr': False,
            'has_a11y': False,
            'is_vanilla': False,
            'is_r3f': False,
            'features': [],
        }

        if re.search(r'["\']three["\']', content):
            info['has_three'] = True

        if re.search(r'["\']@react-three/fiber["\']', content):
            info['has_r3f'] = True
            info['is_r3f'] = True

        if re.search(r'["\']@react-three/drei["\']', content):
            info['has_drei'] = True

        if re.search(r'["\']@react-three/postprocessing["\']|["\']postprocessing["\']', content):
            info['has_postprocessing'] = True

        if re.search(r'["\']@react-three/rapier["\']', content):
            info['has_rapier'] = True

        if re.search(r'["\']@react-three/cannon["\']|["\']cannon-es["\']', content):
            info['has_cannon'] = True

        if re.search(r'["\']@react-three/xr["\']', content):
            info['has_xr'] = True

        if re.search(r'["\']@react-three/a11y["\']', content):
            info['has_a11y'] = True

        # Vanilla if THREE is used but no R3F
        if info['has_three'] and not info['has_r3f']:
            info['is_vanilla'] = True

        # Detect features
        features = []
        if re.search(r'<Canvas', content):
            features.append('canvas')
        if re.search(r'useFrame', content):
            features.append('render-loop')
        if re.search(r'useThree', content):
            features.append('state-access')
        if re.search(r'useLoader', content):
            features.append('asset-loading')
        if re.search(r'<mesh|<group|<instancedMesh', content):
            features.append('declarative-3d')
        if re.search(r'extend\s*\(', content):
            features.append('custom-elements')
        if re.search(r'createPortal', content):
            features.append('portals')
        if re.search(r'useGraph', content):
            features.append('scene-graph')
        if re.search(r'events|onClick|onPointerOver|onPointerDown', content):
            features.append('interaction')
        if re.search(r'Suspense|suspend-react|useAsset', content):
            features.append('suspense')
        if re.search(r'Instances|Merged|InstancedBufferAttribute', content):
            features.append('instancing')
        if re.search(r'<EffectComposer|<Bloom|<SSAO|<DepthOfField', content):
            features.append('post-processing')
        if re.search(r'RigidBody|Physics|useRapier', content):
            features.append('physics')
        if re.search(r'XR|VRButton|ARButton|useXR|useController', content):
            features.append('xr')

        info['features'] = features[:20]
        return info
