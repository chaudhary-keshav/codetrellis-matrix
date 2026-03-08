"""
CSS Preprocessor Extractor for CodeTrellis

Extracts preprocessor-specific patterns from SCSS, Less, and Stylus files.

Supports:
- SCSS: $variables, @mixin/@include, @extend, @use/@forward, %placeholders,
         @function/@return, @each/@for/@while, nesting, interpolation
- Less: @variables, .mixin(), :extend(), @import, guards, loops
- Stylus: Variables, mixins, @extend, conditionals, hash objects
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSMixinInfo:
    """Information about a CSS preprocessor mixin."""
    name: str
    file: str = ""
    line_number: int = 0
    preprocessor: str = ""  # scss, less, stylus
    parameters: List[str] = field(default_factory=list)
    has_content_block: bool = False  # @content in SCSS
    is_usage: bool = False  # True if @include, False if @mixin


@dataclass
class CSSPreprocessorVariableInfo:
    """Information about a preprocessor variable."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    preprocessor: str = ""  # scss, less, stylus
    scope: str = "global"  # global, local, parameter


@dataclass
class CSSPreprocessorFunctionInfo:
    """Information about a preprocessor function."""
    name: str
    file: str = ""
    line_number: int = 0
    preprocessor: str = ""
    parameters: List[str] = field(default_factory=list)
    is_usage: bool = False


@dataclass
class CSSExtendInfo:
    """Information about @extend usage."""
    target: str
    file: str = ""
    line_number: int = 0
    preprocessor: str = ""
    is_placeholder: bool = False  # SCSS %placeholder


@dataclass
class CSSPreprocessorImportInfo:
    """Information about preprocessor import/use/forward."""
    path: str
    file: str = ""
    line_number: int = 0
    preprocessor: str = ""
    import_type: str = "import"  # import, use, forward


class CSSPreprocessorExtractor:
    """
    Extracts preprocessor-specific patterns from CSS preprocessor files.

    Supports SCSS, Less, and Stylus with comprehensive pattern detection.
    """

    # SCSS patterns
    SCSS_VARIABLE = re.compile(r'(\$[\w-]+)\s*:\s*([^;]+);', re.MULTILINE)
    SCSS_MIXIN_DEF = re.compile(
        r'@mixin\s+([\w-]+)\s*(?:\(([^)]*)\))?\s*\{', re.MULTILINE)
    SCSS_MIXIN_USE = re.compile(
        r'@include\s+([\w-]+)\s*(?:\(([^)]*)\))?', re.MULTILINE)
    SCSS_FUNCTION_DEF = re.compile(
        r'@function\s+([\w-]+)\s*\(([^)]*)\)', re.MULTILINE)
    SCSS_FUNCTION_CALL = re.compile(
        r'(?<![:\w-])([\w-]+)\s*\(', re.MULTILINE)
    SCSS_EXTEND = re.compile(
        r'@extend\s+([^;]+);', re.MULTILINE)
    SCSS_USE = re.compile(
        r'@use\s+["\']([^"\']+)["\'](?:\s+as\s+([\w*]+))?', re.MULTILINE)
    SCSS_FORWARD = re.compile(
        r'@forward\s+["\']([^"\']+)["\']', re.MULTILINE)
    SCSS_PLACEHOLDER = re.compile(r'(%[\w-]+)\s*\{', re.MULTILINE)
    SCSS_EACH = re.compile(r'@each\s+', re.MULTILINE)
    SCSS_FOR = re.compile(r'@for\s+', re.MULTILINE)
    SCSS_WHILE = re.compile(r'@while\s+', re.MULTILINE)
    SCSS_IF = re.compile(r'@if\s+', re.MULTILINE)
    SCSS_INTERPOLATION = re.compile(r'#\{[^}]+\}')
    SCSS_CONTENT = re.compile(r'@content\b')

    # Less patterns
    LESS_VARIABLE = re.compile(r'(@[\w-]+)\s*:\s*([^;]+);', re.MULTILINE)
    LESS_MIXIN_DEF = re.compile(
        r'\.([\w-]+)\s*\(([^)]*)\)\s*(?:when\s*\([^)]+\)\s*)?\{', re.MULTILINE)
    LESS_MIXIN_CALL = re.compile(
        r'\.([\w-]+)\s*\(([^)]*)\)\s*;', re.MULTILINE)
    LESS_EXTEND = re.compile(
        r':extend\(([^)]+)\)', re.MULTILINE)
    LESS_GUARD = re.compile(
        r'when\s*\(([^)]+)\)', re.MULTILINE)

    # Common import
    IMPORT_PATTERN = re.compile(
        r'@import\s+["\']([^"\']+)["\']', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract preprocessor patterns from source code.

        Returns dict with:
          - mixins: List[CSSMixinInfo]
          - variables: List[CSSPreprocessorVariableInfo]
          - functions: List[CSSPreprocessorFunctionInfo]
          - extends: List[CSSExtendInfo]
          - imports: List[CSSPreprocessorImportInfo]
          - stats: Dict with counts and feature flags
        """
        preprocessor = self._detect_preprocessor(file_path, content)

        mixins: List[CSSMixinInfo] = []
        variables: List[CSSPreprocessorVariableInfo] = []
        functions: List[CSSPreprocessorFunctionInfo] = []
        extends: List[CSSExtendInfo] = []
        imports: List[CSSPreprocessorImportInfo] = []

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        if preprocessor in ('scss', 'sass'):
            self._extract_scss(clean, file_path, preprocessor,
                               mixins, variables, functions, extends, imports)
        elif preprocessor == 'less':
            self._extract_less(clean, file_path, preprocessor,
                               mixins, variables, functions, extends, imports)
        elif preprocessor == 'stylus':
            self._extract_stylus(clean, file_path, preprocessor,
                                 mixins, variables, functions, extends, imports)

        # Common imports
        for m in self.IMPORT_PATTERN.finditer(clean):
            line_num = clean[:m.start()].count('\n') + 1
            imports.append(CSSPreprocessorImportInfo(
                path=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                import_type="import",
            ))

        stats = {
            "preprocessor": preprocessor,
            "total_mixins": len([m for m in mixins if not m.is_usage]),
            "total_mixin_usages": len([m for m in mixins if m.is_usage]),
            "total_variables": len(variables),
            "total_functions": len([f for f in functions if not f.is_usage]),
            "total_extends": len(extends),
            "total_imports": len(imports),
            "has_placeholders": any(e.is_placeholder for e in extends),
            "has_loops": bool(self.SCSS_EACH.search(clean) or
                              self.SCSS_FOR.search(clean) or
                              self.SCSS_WHILE.search(clean)),
            "has_conditionals": bool(self.SCSS_IF.search(clean)),
            "has_interpolation": bool(self.SCSS_INTERPOLATION.search(clean)),
            "has_module_system": any(i.import_type in ('use', 'forward')
                                     for i in imports),
        }

        return {
            "mixins": mixins,
            "variables": variables,
            "functions": functions,
            "extends": extends,
            "imports": imports,
            "stats": stats,
        }

    def _detect_preprocessor(self, file_path: str, content: str) -> str:
        """Detect which preprocessor based on file extension and content."""
        path_lower = file_path.lower()
        if path_lower.endswith('.scss'):
            return 'scss'
        elif path_lower.endswith('.sass'):
            return 'sass'
        elif path_lower.endswith('.less'):
            return 'less'
        elif path_lower.endswith('.styl') or path_lower.endswith('.stylus'):
            return 'stylus'

        # Content-based detection
        if '$' in content and '@mixin' in content:
            return 'scss'
        if '@' in content and ':extend(' in content:
            return 'less'
        return 'css'

    def _extract_scss(
        self, content: str, file_path: str, preprocessor: str,
        mixins: List[CSSMixinInfo],
        variables: List[CSSPreprocessorVariableInfo],
        functions: List[CSSPreprocessorFunctionInfo],
        extends: List[CSSExtendInfo],
        imports: List[CSSPreprocessorImportInfo],
    ) -> None:
        """Extract SCSS-specific patterns."""
        # Variables
        for m in self.SCSS_VARIABLE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            variables.append(CSSPreprocessorVariableInfo(
                name=m.group(1),
                value=m.group(2).strip(),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
            ))

        # Mixin definitions
        for m in self.SCSS_MIXIN_DEF.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in (m.group(2) or '').split(',')
                      if p.strip()]
            # Check if mixin uses @content
            brace_pos = m.end()
            has_content = self._has_content_block(content, brace_pos)
            mixins.append(CSSMixinInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                has_content_block=has_content,
                is_usage=False,
            ))

        # Mixin usages
        for m in self.SCSS_MIXIN_USE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in (m.group(2) or '').split(',')
                      if p.strip()]
            mixins.append(CSSMixinInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                is_usage=True,
            ))

        # Function definitions
        for m in self.SCSS_FUNCTION_DEF.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in m.group(2).split(',')
                      if p.strip()]
            functions.append(CSSPreprocessorFunctionInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                is_usage=False,
            ))

        # Extends
        for m in self.SCSS_EXTEND.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            target = m.group(1).strip()
            extends.append(CSSExtendInfo(
                target=target,
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                is_placeholder=target.startswith('%'),
            ))

        # Placeholders (as definitions)
        for m in self.SCSS_PLACEHOLDER.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            extends.append(CSSExtendInfo(
                target=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                is_placeholder=True,
            ))

        # @use and @forward (SCSS module system)
        for m in self.SCSS_USE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            imports.append(CSSPreprocessorImportInfo(
                path=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                import_type="use",
            ))

        for m in self.SCSS_FORWARD.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            imports.append(CSSPreprocessorImportInfo(
                path=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                import_type="forward",
            ))

    def _extract_less(
        self, content: str, file_path: str, preprocessor: str,
        mixins: List[CSSMixinInfo],
        variables: List[CSSPreprocessorVariableInfo],
        functions: List[CSSPreprocessorFunctionInfo],
        extends: List[CSSExtendInfo],
        imports: List[CSSPreprocessorImportInfo],
    ) -> None:
        """Extract Less-specific patterns."""
        # Variables (Less uses @ prefix, avoid @media, @import, etc.)
        for m in self.LESS_VARIABLE.finditer(content):
            var_name = m.group(1)
            if var_name in ('@media', '@import', '@keyframes', '@font-face',
                            '@supports', '@layer', '@container', '@charset',
                            '@namespace', '@page', '@counter-style'):
                continue
            line_num = content[:m.start()].count('\n') + 1
            variables.append(CSSPreprocessorVariableInfo(
                name=var_name,
                value=m.group(2).strip(),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
            ))

        # Mixin definitions
        for m in self.LESS_MIXIN_DEF.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in m.group(2).split(',')
                      if p.strip()]
            mixins.append(CSSMixinInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                is_usage=False,
            ))

        # Mixin calls
        for m in self.LESS_MIXIN_CALL.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in m.group(2).split(',')
                      if p.strip()]
            mixins.append(CSSMixinInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                is_usage=True,
            ))

        # Extends
        for m in self.LESS_EXTEND.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            extends.append(CSSExtendInfo(
                target=m.group(1).strip(),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                is_placeholder=False,
            ))

    def _extract_stylus(
        self, content: str, file_path: str, preprocessor: str,
        mixins: List[CSSMixinInfo],
        variables: List[CSSPreprocessorVariableInfo],
        functions: List[CSSPreprocessorFunctionInfo],
        extends: List[CSSExtendInfo],
        imports: List[CSSPreprocessorImportInfo],
    ) -> None:
        """Extract Stylus-specific patterns."""
        # Stylus variables (name = value)
        var_pattern = re.compile(r'^([\w-]+)\s*=\s*(.+)$', re.MULTILINE)
        for m in var_pattern.finditer(content):
            name = m.group(1)
            # Skip CSS property-like assignments
            if name in ('display', 'color', 'margin', 'padding', 'width',
                        'height', 'position', 'background', 'border', 'font'):
                continue
            line_num = content[:m.start()].count('\n') + 1
            variables.append(CSSPreprocessorVariableInfo(
                name=name,
                value=m.group(2).strip(),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
            ))

        # Stylus mixin-like definitions (name(params))
        mixin_def = re.compile(
            r'^([\w-]+)\s*\(([^)]*)\)\s*$', re.MULTILINE)
        for m in mixin_def.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in m.group(2).split(',')
                      if p.strip()]
            mixins.append(CSSMixinInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                parameters=params,
                is_usage=False,
            ))

        # Stylus @extend
        extend_pattern = re.compile(r'@extend\s+(\S+)', re.MULTILINE)
        for m in extend_pattern.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            extends.append(CSSExtendInfo(
                target=m.group(1).strip(),
                file=file_path,
                line_number=line_num,
                preprocessor=preprocessor,
                is_placeholder=False,
            ))

    def _has_content_block(self, content: str, brace_pos: int) -> bool:
        """Check if a mixin body contains @content."""
        depth = 1
        pos = brace_pos
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        body = content[brace_pos:pos]
        return bool(self.SCSS_CONTENT.search(body))
