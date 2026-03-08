"""
TypeScript Attribute Extractor for CodeTrellis

Extracts import/export and metadata from TypeScript source code:
- ES module imports with type-only (import type { Foo })
- Dynamic imports with type inference
- Named, default, and namespace exports
- Type re-exports (export type { Foo } from './bar')
- Decorator definitions and applications
- Namespace declarations (namespace Foo { })
- Module augmentation (declare module 'foo' { })
- Triple-slash directives (/// <reference types="..." />)
- TSDoc/JSDoc comments (@param, @returns, @template, @deprecated)
- Global augmentation (declare global { })
- Ambient declarations (declare const, declare function)

Part of CodeTrellis v4.31 - TypeScript Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TSImportInfo:
    """Information about a TypeScript import statement."""
    source: str
    file: str = ""
    line_number: int = 0
    import_type: str = "es6"  # es6, dynamic, type_only, require
    default_import: str = ""
    named_imports: List[str] = field(default_factory=list)
    namespace_import: str = ""
    is_side_effect: bool = False
    is_type_only: bool = False


@dataclass
class TSExportInfo:
    """Information about a TypeScript export statement."""
    name: str
    file: str = ""
    line_number: int = 0
    export_type: str = "named"  # named, default, re_export, type_only, namespace
    source: str = ""
    is_type_only: bool = False
    kind: str = ""  # class, interface, type, enum, function, const, var


@dataclass
class TSDecoratorInfo:
    """Information about a decorator application."""
    name: str
    file: str = ""
    line_number: int = 0
    arguments: List[str] = field(default_factory=list)
    target: str = ""  # class, method, property, parameter
    target_name: str = ""


@dataclass
class TSNamespaceInfo:
    """Information about a namespace/module declaration."""
    name: str
    file: str = ""
    line_number: int = 0
    is_ambient: bool = False  # declare namespace
    is_module_augmentation: bool = False  # declare module 'foo'
    is_global: bool = False  # declare global
    exports: List[str] = field(default_factory=list)


@dataclass
class TSTripleSlashDirective:
    """Information about a triple-slash reference directive."""
    directive_type: str = ""  # types, path, lib, no-default-lib
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class TSTSDocInfo:
    """Information about a TSDoc/JSDoc comment block."""
    target: str = ""
    file: str = ""
    line_number: int = 0
    description: str = ""
    params: List[dict] = field(default_factory=list)
    returns: str = ""
    template_params: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    since: str = ""
    example: str = ""


class TypeScriptAttributeExtractor:
    """
    Extracts import/export and metadata from TypeScript source code.

    Detects:
    - Type-only imports/exports
    - Decorator patterns
    - Namespace/module declarations
    - Triple-slash directives
    - TSDoc comments
    - Ambient declarations
    """

    # Type-only import
    TYPE_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+type\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Named import
    NAMED_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Default import
    DEFAULT_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Combined default + named import
    COMBINED_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+(\w+)\s*,\s*\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Namespace import
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Side-effect import
    SIDE_EFFECT_IMPORT_PATTERN = re.compile(
        r"^[ \t]*import\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Dynamic import
    DYNAMIC_IMPORT_PATTERN = re.compile(
        r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    )

    # Type-only export
    TYPE_EXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+type\s+\{([^}]+)\}(?:\s+from\s+['\"]([^'\"]+)['\"])?",
        re.MULTILINE,
    )

    # Named export with kind
    NAMED_EXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+(?:declare\s+)?(class|interface|type|enum|function|const|let|var|abstract\s+class|async\s+function)\s+(\w+)",
        re.MULTILINE,
    )

    # Default export
    DEFAULT_EXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+default\s+(?:(class|function|abstract\s+class)\s+)?(\w+)?",
        re.MULTILINE,
    )

    # Re-export
    REEXPORT_PATTERN = re.compile(
        r"^[ \t]*export\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Export all
    EXPORT_ALL_PATTERN = re.compile(
        r"^[ \t]*export\s+\*\s+(?:as\s+(\w+)\s+)?from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Decorator
    DECORATOR_PATTERN = re.compile(
        r"^[ \t]*@(\w+(?:\.\w+)*)\s*(?:\(([^)]*)\))?",
        re.MULTILINE,
    )

    # Namespace declaration
    NAMESPACE_PATTERN = re.compile(
        r"^[ \t]*(?:export\s+)?(?:declare\s+)?namespace\s+(\w+(?:\.\w+)*)\s*\{",
        re.MULTILINE,
    )

    # Module augmentation
    MODULE_AUGMENTATION_PATTERN = re.compile(
        r"^[ \t]*declare\s+module\s+['\"]([^'\"]+)['\"]\s*\{",
        re.MULTILINE,
    )

    # Global augmentation
    GLOBAL_AUGMENTATION_PATTERN = re.compile(
        r"^[ \t]*declare\s+global\s*\{",
        re.MULTILINE,
    )

    # Triple-slash directive
    TRIPLE_SLASH_PATTERN = re.compile(
        r'^///\s*<reference\s+(types|path|lib|no-default-lib)\s*=\s*["\']([^"\']+)["\']\s*/?>',
        re.MULTILINE,
    )

    # TSDoc / JSDoc block
    TSDOC_PATTERN = re.compile(
        r'/\*\*\s*(.*?)\s*\*/',
        re.DOTALL,
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all attributes from TypeScript source code.

        Returns dict with keys: imports, exports, decorators, namespaces,
                                 triple_slash_directives, tsdoc
        """
        imports = self._extract_imports(content, file_path)
        exports = self._extract_exports(content, file_path)
        decorators = self._extract_decorators(content, file_path)
        namespaces = self._extract_namespaces(content, file_path)
        directives = self._extract_triple_slash(content, file_path)
        tsdoc = self._extract_tsdoc(content, file_path)

        return {
            'imports': imports,
            'exports': exports,
            'decorators': decorators,
            'namespaces': namespaces,
            'triple_slash_directives': directives,
            'tsdoc': tsdoc,
        }

    def _extract_imports(self, content: str, file_path: str) -> List[TSImportInfo]:
        """Extract all import statements."""
        imports = []
        seen = set()

        # Type-only imports
        for match in self.TYPE_IMPORT_PATTERN.finditer(content):
            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="type_only",
                    named_imports=names,
                    is_type_only=True,
                ))

        # Combined imports (default + named)
        for match in self.COMBINED_IMPORT_PATTERN.finditer(content):
            default_name = match.group(1)
            named = [n.strip() for n in match.group(2).split(',') if n.strip()]
            source = match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="es6",
                    default_import=default_name,
                    named_imports=named,
                ))

        # Namespace imports
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            ns_name = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="es6",
                    namespace_import=ns_name,
                ))

        # Named imports (must check after type-only and combined to avoid duplicates)
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Check if this was a type import
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            if 'import type' in line_text:
                continue

            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2)
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="es6",
                    named_imports=names,
                ))

        # Default imports (must check after combined to avoid duplicates)
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            source = match.group(2)
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                default_name = match.group(1)
                # Skip 'type' keyword false positive
                if default_name == 'type':
                    continue
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="es6",
                    default_import=default_name,
                ))

        # Side-effect imports
        for match in self.SIDE_EFFECT_IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            source = match.group(1)
            key = (source, line_num)
            if key not in seen:
                seen.add(key)
                imports.append(TSImportInfo(
                    source=source,
                    file=file_path,
                    line_number=line_num,
                    import_type="es6",
                    is_side_effect=True,
                ))

        # Dynamic imports
        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(content):
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            imports.append(TSImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                import_type="dynamic",
            ))

        return imports

    def _extract_exports(self, content: str, file_path: str) -> List[TSExportInfo]:
        """Extract all export statements."""
        exports = []

        # Named exports with kind
        for match in self.NAMED_EXPORT_PATTERN.finditer(content):
            kind = match.group(1).strip()
            name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Normalize kind
            if kind.startswith('abstract'):
                kind = 'abstract class'
            elif kind.startswith('async'):
                kind = 'function'

            exports.append(TSExportInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                export_type="named",
                kind=kind,
            ))

        # Default exports
        for match in self.DEFAULT_EXPORT_PATTERN.finditer(content):
            kind = (match.group(1) or "").strip()
            name = match.group(2) or "default"
            line_num = content[:match.start()].count('\n') + 1

            exports.append(TSExportInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                export_type="default",
                kind=kind,
            ))

        # Type-only exports
        for match in self.TYPE_EXPORT_PATTERN.finditer(content):
            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            for name in names:
                exports.append(TSExportInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    export_type="type_only" if not source else "re_export",
                    source=source,
                    is_type_only=True,
                    kind="type",
                ))

        # Re-exports
        for match in self.REEXPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Skip if this was a type export
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            if 'export type' in line_text:
                continue

            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2)

            for name in names:
                exports.append(TSExportInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    export_type="re_export",
                    source=source,
                ))

        # Export all
        for match in self.EXPORT_ALL_PATTERN.finditer(content):
            alias = match.group(1) or "*"
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            exports.append(TSExportInfo(
                name=alias,
                file=file_path,
                line_number=line_num,
                export_type="namespace" if alias != "*" else "re_export",
                source=source,
            ))

        return exports

    def _extract_decorators(self, content: str, file_path: str) -> List[TSDecoratorInfo]:
        """Extract decorator applications."""
        decorators = []

        for match in self.DECORATOR_PATTERN.finditer(content):
            name = match.group(1)
            args_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            # Determine target from next non-decorator line
            target = ""
            target_name = ""
            after = content[match.end():]
            for after_line in after.split('\n')[:5]:
                stripped = after_line.strip()
                if stripped.startswith('@'):
                    continue
                if re.match(r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', stripped):
                    target = "class"
                    m = re.match(r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', stripped)
                    if m:
                        target_name = m.group(1)
                    break
                elif re.match(r'(?:public|private|protected|static|async|abstract|readonly|override)\s', stripped) or re.match(r'\w+\s*[\(:?!]', stripped):
                    target = "method"
                    m = re.match(r'(?:(?:public|private|protected|static|async|abstract|readonly|override)\s+)*(\w+)', stripped)
                    if m:
                        target_name = m.group(1)
                    break

            arguments = [a.strip() for a in args_str.split(',') if a.strip()] if args_str else []

            decorators.append(TSDecoratorInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                arguments=arguments[:10],
                target=target,
                target_name=target_name,
            ))

        return decorators

    def _extract_namespaces(self, content: str, file_path: str) -> List[TSNamespaceInfo]:
        """Extract namespace and module declarations."""
        namespaces = []

        # Regular namespaces
        for match in self.NAMESPACE_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_text = content[line_start:match.end()]
            is_ambient = 'declare' in line_text

            namespaces.append(TSNamespaceInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_ambient=is_ambient,
            ))

        # Module augmentations
        for match in self.MODULE_AUGMENTATION_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            namespaces.append(TSNamespaceInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_ambient=True,
                is_module_augmentation=True,
            ))

        # Global augmentations
        for match in self.GLOBAL_AUGMENTATION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            namespaces.append(TSNamespaceInfo(
                name="global",
                file=file_path,
                line_number=line_num,
                is_global=True,
            ))

        return namespaces

    def _extract_triple_slash(self, content: str, file_path: str) -> List[TSTripleSlashDirective]:
        """Extract triple-slash reference directives."""
        directives = []

        for match in self.TRIPLE_SLASH_PATTERN.finditer(content):
            directive_type = match.group(1)
            value = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            directives.append(TSTripleSlashDirective(
                directive_type=directive_type,
                value=value,
                file=file_path,
                line_number=line_num,
            ))

        return directives

    def _extract_tsdoc(self, content: str, file_path: str) -> List[TSTSDocInfo]:
        """Extract TSDoc/JSDoc comment blocks."""
        tsdoc_entries = []

        for match in self.TSDOC_PATTERN.finditer(content):
            doc_body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find what it documents (next non-empty line after the comment)
            target = ""
            after = content[match.end():match.end() + 500]
            for after_line in after.split('\n'):
                stripped = after_line.strip()
                if not stripped:
                    continue
                # Get the name of what's documented
                m = re.match(
                    r'(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?'
                    r'(?:class|interface|type|enum|function|const|let|var)\s+(\w+)',
                    stripped
                )
                if m:
                    target = m.group(1)
                else:
                    # Method or property
                    m = re.match(r'(?:(?:public|private|protected|static|abstract|readonly|override|async)\s+)*(\w+)', stripped)
                    if m:
                        target = m.group(1)
                break

            # Parse doc body
            description = ""
            params = []
            returns = ""
            template_params = []
            tags = []
            deprecated = False
            since = ""
            example = ""

            lines = doc_body.split('\n')
            desc_lines = []
            for doc_line in lines:
                cleaned = re.sub(r'^\s*\*\s?', '', doc_line).strip()
                if not cleaned:
                    continue

                if cleaned.startswith('@param'):
                    m = re.match(r'@param\s+(?:\{([^}]+)\}\s+)?(\w+)\s*[-–]?\s*(.*)', cleaned)
                    if m:
                        params.append({
                            "type": m.group(1) or "",
                            "name": m.group(2),
                            "description": m.group(3),
                        })
                elif cleaned.startswith('@returns') or cleaned.startswith('@return'):
                    returns = re.sub(r'^@returns?\s*', '', cleaned)
                elif cleaned.startswith('@template'):
                    template_params.append(re.sub(r'^@template\s*', '', cleaned))
                elif cleaned.startswith('@deprecated'):
                    deprecated = True
                    tags.append('deprecated')
                elif cleaned.startswith('@since'):
                    since = re.sub(r'^@since\s*', '', cleaned)
                elif cleaned.startswith('@example'):
                    example = re.sub(r'^@example\s*', '', cleaned)
                elif cleaned.startswith('@'):
                    tag_m = re.match(r'@(\w+)', cleaned)
                    if tag_m:
                        tags.append(tag_m.group(1))
                else:
                    desc_lines.append(cleaned)

            description = ' '.join(desc_lines)[:300]

            if target or description:
                tsdoc_entries.append(TSTSDocInfo(
                    target=target,
                    file=file_path,
                    line_number=line_num,
                    description=description,
                    params=params,
                    returns=returns,
                    template_params=template_params,
                    tags=tags,
                    deprecated=deprecated,
                    since=since,
                    example=example,
                ))

        return tsdoc_entries
