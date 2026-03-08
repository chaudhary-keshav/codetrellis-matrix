"""
Three.js / React Three Fiber Material Extractor

Extracts material and shader constructs:
- Built-in materials (Standard, Physical, Basic, Phong, Lambert, Toon, etc.)
- Shader materials (ShaderMaterial, RawShaderMaterial)
- Custom shaders (vertex, fragment GLSL)
- Uniforms and varying declarations
- Textures (maps, normal maps, environment maps, displacement, etc.)
- Drei materials (MeshReflectorMaterial, MeshTransmissionMaterial, etc.)
- Node materials (Three.js r149+ NodeMaterial system)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ThreeJSMaterialInfo:
    """Material usage."""
    name: str
    file: str
    line_number: int
    material_type: str  # 'standard', 'physical', 'basic', 'phong', 'lambert', 'toon', 'normal', 'matcap', 'depth', 'shader', 'raw_shader', 'points', 'line_basic', 'line_dashed', 'sprite'
    is_r3f: bool = True
    has_map: bool = False
    has_normal_map: bool = False
    has_env_map: bool = False
    has_displacement: bool = False
    has_emissive: bool = False
    has_roughness_map: bool = False
    has_metalness_map: bool = False
    has_ao_map: bool = False
    has_alpha_map: bool = False
    is_transparent: bool = False
    is_wireframe: bool = False
    side: str = ""  # 'front', 'back', 'double'
    props: List[str] = field(default_factory=list)


@dataclass
class ThreeJSShaderInfo:
    """Shader material or GLSL code."""
    name: str
    file: str
    line_number: int
    shader_type: str  # 'vertex', 'fragment', 'shader_material', 'raw_shader_material', 'compute'
    has_uniforms: bool = False
    has_varyings: bool = False
    has_defines: bool = False
    glsl_version: str = ""  # '100', '300 es'
    uniform_count: int = 0
    is_r3f: bool = True
    uses_glslify: bool = False
    uses_drei_shaderMaterial: bool = False


@dataclass
class ThreeJSTextureInfo:
    """Texture loading and usage."""
    name: str
    file: str
    line_number: int
    texture_type: str  # 'map', 'normal', 'roughness', 'metalness', 'env', 'displacement', 'ao', 'emissive', 'alpha', 'cube', 'hdr', 'exr', 'ktx2', 'video'
    loader: str  # 'useTexture', 'TextureLoader', 'CubeTextureLoader', 'RGBELoader', 'EXRLoader', 'KTX2Loader', 'VideoTexture'
    path: str = ""
    is_preloaded: bool = False


@dataclass
class ThreeJSUniformInfo:
    """Shader uniform declaration."""
    name: str
    file: str
    line_number: int
    uniform_type: str  # 'float', 'vec2', 'vec3', 'vec4', 'mat3', 'mat4', 'sampler2D', 'int', 'bool'
    initial_value: str = ""
    is_animated: bool = False  # updated in useFrame


class ThreeJSMaterialExtractor:
    """Extracts material and shader constructs."""

    # R3F material JSX patterns
    R3F_MATERIAL_PATTERN = re.compile(
        r'<(meshStandardMaterial|meshBasicMaterial|meshPhongMaterial|'
        r'meshLambertMaterial|meshPhysicalMaterial|meshToonMaterial|'
        r'meshNormalMaterial|meshMatcapMaterial|meshDepthMaterial|'
        r'shaderMaterial|rawShaderMaterial|pointsMaterial|'
        r'lineBasicMaterial|lineDashedMaterial|spriteMaterial|'
        r'shadowMaterial)\b([^>]*?)(?:/>|>)',
        re.DOTALL
    )

    # Vanilla Three.js material patterns
    VANILLA_MATERIAL_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(MeshStandardMaterial|MeshBasicMaterial|'
        r'MeshPhongMaterial|MeshLambertMaterial|MeshPhysicalMaterial|'
        r'MeshToonMaterial|MeshNormalMaterial|MeshMatcapMaterial|'
        r'MeshDepthMaterial|ShaderMaterial|RawShaderMaterial|'
        r'PointsMaterial|LineBasicMaterial|LineDashedMaterial|'
        r'SpriteMaterial|ShadowMaterial|NodeMaterial)\s*\(',
    )

    # Drei special materials
    DREI_MATERIAL_PATTERN = re.compile(
        r'<(MeshReflectorMaterial|MeshRefractionMaterial|'
        r'MeshTransmissionMaterial|MeshDiscardMaterial|'
        r'MeshDistortMaterial|MeshWobbleMaterial|'
        r'PointMaterial|MeshPortalMaterial|'
        r'shaderMaterial)\b'
    )

    # Shader string patterns (template literals or multiline strings)
    # Handles: vertexShader = `...`, vertexShader = /* glsl */ `...`, vertex: glsl`...`
    VERTEX_SHADER_PATTERN = re.compile(
        r'(?:vertexShader|vertex)\s*[:=]\s*(?:/\*\s*glsl\s*\*/\s*)?(?:`([^`]+)`|[\'"]([^\'"]+)[\'"]|glsl`([^`]+)`)',
        re.DOTALL
    )
    FRAGMENT_SHADER_PATTERN = re.compile(
        r'(?:fragmentShader|fragment)\s*[:=]\s*(?:/\*\s*glsl\s*\*/\s*)?(?:`([^`]+)`|[\'"]([^\'"]+)[\'"]|glsl`([^`]+)`)',
        re.DOTALL
    )

    # GLSL uniform declaration patterns
    GLSL_UNIFORM_PATTERN = re.compile(
        r'uniform\s+(float|int|bool|vec[234]|mat[234]|sampler2D|samplerCube|sampler3D)\s+(\w+)'
    )

    # JS uniforms object pattern
    JS_UNIFORM_PATTERN = re.compile(
        r'uniforms\s*[:=]\s*\{([^}]+)\}',
        re.DOTALL
    )

    # Texture loading patterns
    USE_TEXTURE_PATTERN = re.compile(
        r'useTexture\s*\(\s*(?:[\'"]([^\'"]+)[\'"]|\{[^}]*\}|\[)',
    )
    TEXTURE_LOADER_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?(TextureLoader|CubeTextureLoader|'
        r'RGBELoader|EXRLoader|KTX2Loader|CompressedTextureLoader)\s*\('
    )
    VIDEO_TEXTURE_PATTERN = re.compile(
        r'new\s+(?:THREE\.)?VideoTexture\s*\('
    )

    # glslify pattern
    GLSLIFY_PATTERN = re.compile(r'glslify|glsl`|#pragma glslify')

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract material and shader constructs."""
        result = {
            'materials': [],
            'shaders': [],
            'textures': [],
            'uniforms': [],
        }

        # R3F materials
        for match in self.R3F_MATERIAL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            mat_name = match.group(1)
            attrs = match.group(2) or ''
            mat_type = self._normalize_material_type(mat_name)
            result['materials'].append(ThreeJSMaterialInfo(
                name=mat_name,
                file=file_path,
                line_number=line_num,
                material_type=mat_type,
                is_r3f=True,
                has_map=bool(re.search(r'\bmap\b', attrs)),
                has_normal_map=bool(re.search(r'\bnormalMap\b', attrs)),
                has_env_map=bool(re.search(r'\benvMap\b', attrs)),
                has_displacement=bool(re.search(r'\bdisplacementMap\b', attrs)),
                has_emissive=bool(re.search(r'\bemissive\b', attrs)),
                has_roughness_map=bool(re.search(r'\broughnessMap\b', attrs)),
                has_metalness_map=bool(re.search(r'\bmetalnessMap\b', attrs)),
                has_ao_map=bool(re.search(r'\baoMap\b', attrs)),
                has_alpha_map=bool(re.search(r'\balphaMap\b', attrs)),
                is_transparent=bool(re.search(r'\btransparent\b', attrs)),
                is_wireframe=bool(re.search(r'\bwireframe\b', attrs)),
                side=self._extract_side(attrs),
            ))

        # Vanilla materials
        for match in self.VANILLA_MATERIAL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            cls = match.group(1)
            mat_type = self._normalize_material_type(cls)
            # Look at constructor args
            context_end = min(match.end() + 500, len(content))
            context = content[match.start():context_end]
            result['materials'].append(ThreeJSMaterialInfo(
                name=cls,
                file=file_path,
                line_number=line_num,
                material_type=mat_type,
                is_r3f=False,
                has_map=bool(re.search(r'\bmap\s*:', context)),
                has_normal_map=bool(re.search(r'\bnormalMap\s*:', context)),
                has_env_map=bool(re.search(r'\benvMap\s*:', context)),
                is_transparent=bool(re.search(r'\btransparent\s*:\s*true', context)),
                is_wireframe=bool(re.search(r'\bwireframe\s*:\s*true', context)),
            ))

        # Drei materials
        for match in self.DREI_MATERIAL_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            mat_name = match.group(1)
            result['materials'].append(ThreeJSMaterialInfo(
                name=mat_name,
                file=file_path,
                line_number=line_num,
                material_type='drei_' + mat_name.replace('Mesh', '').replace('Material', '').lower(),
                is_r3f=True,
            ))

        # Shader detection
        for pattern, shader_type in [
            (self.VERTEX_SHADER_PATTERN, 'vertex'),
            (self.FRAGMENT_SHADER_PATTERN, 'fragment'),
        ]:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                shader_code = match.group(1) or match.group(2) or match.group(3) or ''
                uniform_matches = self.GLSL_UNIFORM_PATTERN.findall(shader_code)
                result['shaders'].append(ThreeJSShaderInfo(
                    name=f'{shader_type}_shader',
                    file=file_path,
                    line_number=line_num,
                    shader_type=shader_type,
                    has_uniforms=bool(uniform_matches),
                    has_varyings=bool(re.search(r'\bvarying\b', shader_code)),
                    has_defines=bool(re.search(r'#define\b', shader_code)),
                    glsl_version='300 es' if '#version 300 es' in shader_code else '100',
                    uniform_count=len(uniform_matches),
                    uses_glslify=bool(self.GLSLIFY_PATTERN.search(shader_code)),
                ))

                # Extract uniforms from GLSL
                for u_type, u_name in uniform_matches:
                    result['uniforms'].append(ThreeJSUniformInfo(
                        name=u_name,
                        file=file_path,
                        line_number=line_num,
                        uniform_type=u_type,
                    ))

        # JS uniform objects
        for match in self.JS_UNIFORM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            uniforms_str = match.group(1)
            uniform_names = re.findall(r'(\w+)\s*:\s*\{', uniforms_str)
            for u_name in uniform_names:
                value_match = re.search(rf'{u_name}\s*:\s*\{{\s*value\s*:\s*([^,}}]+)', uniforms_str)
                result['uniforms'].append(ThreeJSUniformInfo(
                    name=u_name,
                    file=file_path,
                    line_number=line_num,
                    uniform_type='unknown',
                    initial_value=value_match.group(1).strip() if value_match else '',
                ))

        # Texture loading
        for match in self.USE_TEXTURE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            path = match.group(1) or ''
            result['textures'].append(ThreeJSTextureInfo(
                name=path.split('/')[-1] if path else 'useTexture',
                file=file_path,
                line_number=line_num,
                texture_type='map',
                loader='useTexture',
                path=path,
            ))

        for match in self.TEXTURE_LOADER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            loader_name = match.group(1)
            tex_type = 'hdr' if 'RGBE' in loader_name else 'exr' if 'EXR' in loader_name else 'ktx2' if 'KTX2' in loader_name else 'cube' if 'Cube' in loader_name else 'map'
            result['textures'].append(ThreeJSTextureInfo(
                name=loader_name,
                file=file_path,
                line_number=line_num,
                texture_type=tex_type,
                loader=loader_name,
            ))

        for match in self.VIDEO_TEXTURE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['textures'].append(ThreeJSTextureInfo(
                name='VideoTexture',
                file=file_path,
                line_number=line_num,
                texture_type='video',
                loader='VideoTexture',
            ))

        return result

    def _normalize_material_type(self, name: str) -> str:
        """Normalize material type from class/tag name."""
        name = name.replace('mesh', '').replace('Mesh', '')
        name = name.replace('Material', '').replace('material', '')
        mapping = {
            'Standard': 'standard', 'standard': 'standard',
            'Basic': 'basic', 'basic': 'basic',
            'Phong': 'phong', 'phong': 'phong',
            'Lambert': 'lambert', 'lambert': 'lambert',
            'Physical': 'physical', 'physical': 'physical',
            'Toon': 'toon', 'toon': 'toon',
            'Normal': 'normal', 'normal': 'normal',
            'Matcap': 'matcap', 'matcap': 'matcap',
            'Depth': 'depth', 'depth': 'depth',
            'Shader': 'shader', 'shader': 'shader',
            'RawShader': 'raw_shader', 'rawShader': 'raw_shader',
            'Points': 'points', 'points': 'points',
            'LineBasic': 'line_basic', 'lineBasic': 'line_basic',
            'LineDashed': 'line_dashed', 'lineDashed': 'line_dashed',
            'Sprite': 'sprite', 'sprite': 'sprite',
            'Shadow': 'shadow', 'shadow': 'shadow',
            'Node': 'node', 'node': 'node',
        }
        return mapping.get(name, 'standard')

    def _extract_side(self, attrs: str) -> str:
        """Extract material side property."""
        match = re.search(r'side\s*=\s*\{?\s*(?:THREE\.)?(\w+Side)', attrs)
        if match:
            side = match.group(1)
            if 'Double' in side:
                return 'double'
            elif 'Back' in side:
                return 'back'
            return 'front'
        return ''
