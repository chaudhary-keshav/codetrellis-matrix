"""
JavaScript Attribute Extractor for CodeTrellis

Extracts import/export and metadata from JavaScript source code:
- ES6 imports (named, default, namespace, side-effect)
- CommonJS require() calls
- Dynamic imports (import())
- ES6 exports (named, default, re-exports)
- CommonJS module.exports / exports
- JSDoc comments (@param, @returns, @type, @typedef)
- Decorator patterns (Stage 3 decorators, legacy/experimental)
- Package.json dependency inference

Part of CodeTrellis v4.30 - JavaScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JSImportInfo:
    """Information about a JavaScript import statement."""
    source: str  # module specifier
    file: str = ""
    line_number: int = 0
    import_type: str = "es6"  # es6, commonjs, dynamic
    default_import: str = ""
    named_imports: List[str] = field(default_factory=list)
    namespace_import: str = ""
    is_side_effect: bool = False
    is_type_only: bool = False


@dataclass
class JSExportInfo:
    """Information about a JavaScript export statement."""
    name: str
    file: str = ""
    line_number: int = 0
    export_type: str = "named"  # named, default, re-export, cjs
    source: str = ""  # re-export source
    is_type_only: bool = False


@dataclass
class JSJSDocInfo:
    """Information about a JSDoc comment block."""
    name: str  # function/class name it documents
    file: str = ""
    line_number: int = 0
    description: str = ""
    params: List[str] = field(default_factory=list)  # @param entries
    returns: str = ""  # @returns type
    tags: List[str] = field(default_factory=list)  # @deprecated, @abstract, etc.
    typedef: str = ""  # @typedef name
    type: str = ""  # @type annotation


@dataclass
class JSDecoratorInfo:
    """Information about a decorator (Stage 3 / legacy)."""
    name: str
    file: str = ""
    line_number: int = 0
    arguments: List[str] = field(default_factory=list)
    target: str = ""  # class or method it decorates


@dataclass
class JSDynamicImportInfo:
    """Information about a dynamic import() call."""
    source: str
    file: str = ""
    line_number: int = 0
    is_conditional: bool = False
    is_lazy: bool = False


class JavaScriptAttributeExtractor:
    """
    Extracts import/export and metadata from JavaScript source code.

    Detects:
    - ES6 import/export (all forms)
    - CommonJS require/module.exports
    - Dynamic import() calls
    - JSDoc comment blocks
    - Decorators (@)
    """

    # ES6 named import
    NAMED_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # ES6 default import
    DEFAULT_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # ES6 combined default + named import
    COMBINED_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+(\w+)\s*,\s*\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # ES6 namespace import
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # ES6 side-effect import
    SIDE_EFFECT_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # CommonJS require
    REQUIRE_PATTERN = re.compile(
        r"(?:const|let|var)\s+(?:(\w+)|\{([^}]+)\})\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Dynamic import
    DYNAMIC_IMPORT_PATTERN = re.compile(
        r"import\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # ES6 named export
    NAMED_EXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+(?:const|let|var|function\s*\*?|class|async\s+function)\s+(\w+)",
        re.MULTILINE,
    )

    # ES6 default export
    DEFAULT_EXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+default\s+(?:class\s+(\w+)|function\s*\*?\s*(\w+)|(\w+))",
        re.MULTILINE,
    )

    # Re-export
    REEXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Export all re-export
    REEXPORT_ALL_PATTERN = re.compile(
        r"^[ \t]*export\s+\*\s+(?:as\s+(\w+)\s+)?from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # CommonJS exports
    CJS_EXPORT_PATTERN = re.compile(
        r"^[ \t]*module\.exports\s*=",
        re.MULTILINE,
    )
    CJS_NAMED_EXPORT_PATTERN = re.compile(
        r"^[ \t]*(?:module\.)?exports\.(\w+)\s*=",
        re.MULTILINE,
    )

    # JSDoc block
    JSDOC_PATTERN = re.compile(
        r"/\*\*\s*\n([\s\S]*?)\*/",
        re.MULTILINE,
    )

    # Decorator pattern
    DECORATOR_PATTERN = re.compile(
        r"^[ \t]*@(\w+)(?:\(([^)]*)\))?",
        re.MULTILINE,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract imports, exports, JSDoc, and decorators.

        Returns dict with keys: imports, exports, jsdoc, decorators, dynamic_imports
        """
        imports = self._extract_imports(content, file_path)
        exports = self._extract_exports(content, file_path)
        jsdoc = self._extract_jsdoc(content, file_path)
        decorators = self._extract_decorators(content, file_path)
        dynamic_imports = self._extract_dynamic_imports(content, file_path)

        return {
            'imports': imports,
            'exports': exports,
            'jsdoc': jsdoc,
            'decorators': decorators,
            'dynamic_imports': dynamic_imports,
        }

    def _extract_imports(self, content: str, file_path: str) -> List[JSImportInfo]:
        """Extract all import statements (ES6 + CommonJS)."""
        imports = []
        seen_sources = set()

        # Combined default + named import (must be before default import)
        for match in self.COMBINED_IMPORT_PATTERN.finditer(content):
            default_name = match.group(1)
            named_raw = match.group(2)
            source = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            named = [n.strip().split(' as ')[0].strip() for n in named_raw.split(',') if n.strip()]

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='es6',
                default_import=default_name,
                named_imports=named,
            ))
            seen_sources.add((source, line_num))

        # Namespace import
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            ns = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if (source, line_num) in seen_sources:
                continue
            seen_sources.add((source, line_num))

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='es6',
                namespace_import=ns,
            ))

        # Named import
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            named_raw = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if (source, line_num) in seen_sources:
                continue
            seen_sources.add((source, line_num))

            named = [n.strip().split(' as ')[0].strip() for n in named_raw.split(',') if n.strip()]

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='es6',
                named_imports=named,
            ))

        # Default import
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            default_name = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if (source, line_num) in seen_sources:
                continue
            seen_sources.add((source, line_num))

            # Skip if it's actually a 'from' clause we already processed
            if default_name in ('type', 'typeof'):
                continue

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='es6',
                default_import=default_name,
            ))

        # Side-effect import
        for match in self.SIDE_EFFECT_IMPORT_PATTERN.finditer(content):
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if (source, line_num) in seen_sources:
                continue
            seen_sources.add((source, line_num))

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='es6',
                is_side_effect=True,
            ))

        # CommonJS require
        for match in self.REQUIRE_PATTERN.finditer(content):
            default_name = match.group(1) or ""
            named_raw = match.group(2) or ""
            source = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            named = [n.strip().split(':')[0].strip() for n in named_raw.split(',') if n.strip()] if named_raw else []

            imports.append(JSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type='commonjs',
                default_import=default_name,
                named_imports=named,
            ))

        return imports

    def _extract_exports(self, content: str, file_path: str) -> List[JSExportInfo]:
        """Extract all export statements (ES6 + CommonJS)."""
        exports = []
        seen = set()

        # Named exports
        for match in self.NAMED_EXPORT_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            exports.append(JSExportInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                export_type='named',
            ))

        # Default exports
        for match in self.DEFAULT_EXPORT_PATTERN.finditer(content):
            name = match.group(1) or match.group(2) or match.group(3) or '<default>'
            line_num = content[:match.start()].count('\n') + 1

            exports.append(JSExportInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                export_type='default',
            ))

        # Re-exports
        for match in self.REEXPORT_PATTERN.finditer(content):
            named_raw = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            names = [n.strip().split(' as ')[-1].strip() for n in named_raw.split(',') if n.strip()]
            for name in names:
                exports.append(JSExportInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    export_type='re-export',
                    source=source,
                ))

        # Re-export all
        for match in self.REEXPORT_ALL_PATTERN.finditer(content):
            alias = match.group(1) or '*'
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            exports.append(JSExportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                export_type='re-export',
                source=source,
            ))

        # CommonJS named exports
        for match in self.CJS_NAMED_EXPORT_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if name in seen:
                continue
            seen.add(name)

            exports.append(JSExportInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                export_type='cjs',
            ))

        # CommonJS module.exports
        if self.CJS_EXPORT_PATTERN.search(content):
            line_num = content[:self.CJS_EXPORT_PATTERN.search(content).start()].count('\n') + 1
            exports.append(JSExportInfo(
                name='<module.exports>',
                file=file_path,
                line_number=line_num,
                export_type='cjs',
            ))

        return exports

    def _extract_jsdoc(self, content: str, file_path: str) -> List[JSJSDocInfo]:
        """Extract JSDoc comment blocks."""
        jsdocs = []

        for match in self.JSDOC_PATTERN.finditer(content):
            body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find what this JSDoc documents (next non-empty line after */)
            end_pos = match.end()
            rest = content[end_pos:end_pos + 200].strip()

            # Extract the documented name
            name_match = re.match(
                r'(?:export\s+(?:default\s+)?)?(?:async\s+)?'
                r'(?:function\s*\*?\s*(\w+)|class\s+(\w+)|'
                r'(?:const|let|var)\s+(\w+))',
                rest
            )
            name = ""
            if name_match:
                name = name_match.group(1) or name_match.group(2) or name_match.group(3) or ""

            # Parse JSDoc tags
            description_lines = []
            params = []
            returns = ""
            tags = []
            typedef = ""
            type_ann = ""

            for line in body.split('\n'):
                stripped = re.sub(r'^\s*\*\s?', '', line).strip()
                if not stripped:
                    continue

                if stripped.startswith('@param'):
                    params.append(stripped)
                elif stripped.startswith('@returns') or stripped.startswith('@return'):
                    returns = stripped
                elif stripped.startswith('@typedef'):
                    m = re.match(r'@typedef\s+\{([^}]+)\}\s+(\w+)', stripped)
                    if m:
                        typedef = m.group(2)
                        type_ann = m.group(1)
                elif stripped.startswith('@type'):
                    m = re.match(r'@type\s+\{([^}]+)\}', stripped)
                    if m:
                        type_ann = m.group(1)
                elif stripped.startswith('@'):
                    tag = stripped.split()[0]
                    tags.append(tag)
                else:
                    description_lines.append(stripped)

            if not name and typedef:
                name = typedef

            if name or typedef or params:
                jsdocs.append(JSJSDocInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    description=' '.join(description_lines)[:200],
                    params=params[:20],
                    returns=returns,
                    tags=tags,
                    typedef=typedef,
                    type=type_ann,
                ))

        return jsdocs

    def _extract_decorators(self, content: str, file_path: str) -> List[JSDecoratorInfo]:
        """Extract decorator patterns."""
        decorators = []

        for match in self.DECORATOR_PATTERN.finditer(content):
            name = match.group(1)
            args_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            # Find what the decorator is applied to
            end_pos = match.end()
            rest = content[end_pos:end_pos + 200].strip()
            target_match = re.match(r'(?:@\w+(?:\([^)]*\))?\s*)*(?:export\s+)?(?:class\s+(\w+)|(\w+)\s*\()', rest)
            target = ""
            if target_match:
                target = target_match.group(1) or target_match.group(2) or ""

            decorators.append(JSDecoratorInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                arguments=[a.strip() for a in args_str.split(',') if a.strip()] if args_str else [],
                target=target,
            ))

        return decorators

    def _extract_dynamic_imports(self, content: str, file_path: str) -> List[JSDynamicImportInfo]:
        """Extract dynamic import() calls."""
        dynamic_imports = []

        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(content):
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check if it's conditional (inside if/ternary/try)
            pre = content[max(0, match.start() - 100):match.start()]
            is_conditional = bool(re.search(r'if\s*\(|case\s|catch\s*\(|\?\s*$', pre))
            is_lazy = bool(re.search(r'lazy\s*\(|React\.lazy|Suspense', pre))

            dynamic_imports.append(JSDynamicImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                is_conditional=is_conditional,
                is_lazy=is_lazy,
            ))

        return dynamic_imports
