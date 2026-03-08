"""
ScalaAttributeExtractor - Extracts Scala annotations, implicits, macros, and dependencies.

This extractor parses Scala source code and extracts:
- Annotations (@Inject, @Singleton, @tailrec, custom annotations)
- Implicits and givens (implicit val/def, given instances, context parameters)
- Scala macros (macro def, inline, transparent)
- SBT dependencies (libraryDependencies, plugins)
- Scala compiler plugins and flags
- Build tool configuration (sbt, mill, gradle)
- Import patterns and package structure
- Compiler options

Supports Scala 2.10 through Scala 3.5+ and SBT 1.x, Mill, Scala CLI.

Part of CodeTrellis v4.25 - Scala Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScalaAnnotationInfo:
    """Information about a Scala annotation."""
    name: str
    target: Optional[str] = None  # Name of annotated element
    target_kind: str = "unknown"  # class, method, field, parameter
    arguments: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class ScalaImplicitInfo:
    """Information about a Scala implicit/given."""
    name: str
    type: str = ""
    kind: str = "implicit_val"  # implicit_val, implicit_def, implicit_class, given, using, extension
    scope: str = "local"  # local, companion, package, import
    file: str = ""
    line_number: int = 0
    is_conversion: bool = False  # implicit def that converts between types
    from_type: Optional[str] = None  # For conversions: source type
    to_type: Optional[str] = None  # For conversions: target type


@dataclass
class ScalaMacroInfo:
    """Information about a Scala macro."""
    name: str
    kind: str = "macro"  # macro, inline, transparent_inline, derive
    file: str = ""
    line_number: int = 0
    description: Optional[str] = None


@dataclass
class ScalaDependencyInfo:
    """Information about a Scala/SBT dependency."""
    group_id: str
    artifact_id: str
    version: str = ""
    scope: str = "compile"  # compile, test, provided, runtime, it, optional
    cross_version: str = "%%"  # %% (Scala binary), %%% (Scala.js), % (Java)
    classifier: Optional[str] = None
    excludes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_plugin: bool = False
    is_compiler_plugin: bool = False


@dataclass
class ScalaImportInfo:
    """Information about a Scala import statement."""
    path: str
    members: List[str] = field(default_factory=list)  # specific imports or _/*
    is_wildcard: bool = False
    renames: Dict[str, str] = field(default_factory=dict)  # {OldName -> NewName}
    given_import: bool = False  # import x.given
    file: str = ""
    line_number: int = 0


class ScalaAttributeExtractor:
    """
    Extracts Scala attribute-like constructs from source code.

    Handles:
    - Annotations (@Entity, @Inject, @Singleton, @tailrec, etc.)
    - Implicit values, defs, classes (Scala 2)
    - Given instances and using clauses (Scala 3)
    - Implicit conversions
    - Macro definitions (Scala 2 macros, Scala 3 inline/transparent)
    - SBT build.sbt dependency parsing
    - Mill build.sc dependency parsing
    - Scala CLI directives (//> using dep)
    - Compiler plugins
    - Import patterns and package structure
    - Scala compiler flags (-Ywarn, -Xfatal-warnings, etc.)
    """

    # ── Annotations ─────────────────────────────────────────────
    ANNOTATION_PATTERN = re.compile(
        r'@(?P<name>\w+(?:\.\w+)*)(?:\s*\((?P<args>[^)]*)\))?',
        re.MULTILINE
    )

    # Known framework annotations for context
    KNOWN_ANNOTATIONS = {
        'Inject', 'Singleton', 'Named', 'Provides', 'Module',
        'tailrec', 'throws', 'deprecated', 'inline', 'specialized',
        'transient', 'volatile', 'SerialVersionUID', 'BeanProperty',
        'Entity', 'Table', 'Column', 'Id', 'GeneratedValue',
        'JsonCodec', 'ConfiguredJsonCodec', 'deriving',
        'main', 'static', 'targetName',
    }

    # ── Implicits ───────────────────────────────────────────────
    IMPLICIT_VAL_PATTERN = re.compile(
        r'implicit\s+(?P<lazy>lazy\s+)?val\s+(?P<name>\w+)\s*:\s*(?P<type>[^\s=]+(?:\[[^\]]*\])?)',
        re.MULTILINE
    )

    IMPLICIT_DEF_PATTERN = re.compile(
        r'implicit\s+def\s+(?P<name>\w+)\s*'
        r'(?:\[(?P<generics>[^\]]+)\])?\s*'
        r'(?:\((?P<params>[^)]*)\))?\s*:\s*(?P<return_type>[^\s=]+(?:\[[^\]]*\])?)',
        re.MULTILINE
    )

    IMPLICIT_CLASS_PATTERN = re.compile(
        r'implicit\s+class\s+(?P<name>\w+)\s*'
        r'(?:\[(?P<generics>[^\]]+)\])?\s*'
        r'\((?P<params>[^)]*)\)',
        re.MULTILINE
    )

    # Scala 3 given instances
    GIVEN_PATTERN = re.compile(
        r'given\s+(?:(?P<name>\w+)\s*:\s*)?(?P<type>[^\s=]+(?:\[[^\]]*\])?)\s*(?:with\s+|=)',
        re.MULTILINE
    )

    # ── Macros ──────────────────────────────────────────────────
    MACRO_DEF_PATTERN = re.compile(
        r'def\s+(?P<name>\w+)\s*(?:\[[^\]]*\])?\s*(?:\([^)]*\))*\s*:\s*[^=]*=\s*macro\s+',
        re.MULTILINE
    )

    INLINE_DEF_PATTERN = re.compile(
        r'(?P<transparent>transparent\s+)?inline\s+def\s+(?P<name>\w+)',
        re.MULTILINE
    )

    DERIVE_PATTERN = re.compile(
        r'derives\s+(?P<typeclasses>[\w\s,]+)',
        re.MULTILINE
    )

    # ── SBT Dependencies ───────────────────────────────────────
    SBT_DEP_PATTERN = re.compile(
        r'["\'](?P<group>[^"\']+)["\']\s*'
        r'(?P<cross>%%?%?)\s*'
        r'["\'](?P<artifact>[^"\']+)["\']\s*'
        r'%\s*'
        r'["\'](?P<version>[^"\']+)["\']'
        r'(?:\s*%\s*["\'](?P<scope>[^"\']+)["\'])?',
        re.MULTILINE
    )

    SBT_PLUGIN_PATTERN = re.compile(
        r'addSbtPlugin\s*\(\s*["\'](?P<group>[^"\']+)["\']\s*%\s*'
        r'["\'](?P<artifact>[^"\']+)["\']\s*%\s*'
        r'["\'](?P<version>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    SBT_COMPILER_PLUGIN_PATTERN = re.compile(
        r'addCompilerPlugin\s*\(\s*["\'](?P<group>[^"\']+)["\']\s*'
        r'(?P<cross>%%?)\s*'
        r'["\'](?P<artifact>[^"\']+)["\']\s*%\s*'
        r'["\'](?P<version>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # ── Mill Dependencies ──────────────────────────────────────
    MILL_DEP_PATTERN = re.compile(
        r'ivy"(?P<group>[^:]+)::?(?P<artifact>[^:]+):(?P<version>[^"]+)"',
        re.MULTILINE
    )

    # ── Scala CLI ──────────────────────────────────────────────
    SCALA_CLI_DEP_PATTERN = re.compile(
        r'//>\s*using\s+(?:dep|lib)\s+(?P<dep>[^\n]+)',
        re.MULTILINE
    )

    # ── Imports ────────────────────────────────────────────────
    IMPORT_PATTERN = re.compile(
        r'import\s+(?P<path>[\w.]+)(?:\.\{(?P<members>[^}]+)\}|\.(?P<single>\w+|\*|given))',
        re.MULTILINE
    )

    SIMPLE_IMPORT_PATTERN = re.compile(
        r'import\s+(?P<path>[\w.]+(?:\.\w+))',
        re.MULTILINE
    )

    # ── Package ────────────────────────────────────────────────
    PACKAGE_PATTERN = re.compile(
        r'package\s+(?P<name>[\w.]+)',
        re.MULTILINE
    )

    # ── Compiler Options ───────────────────────────────────────
    SCALAC_OPTIONS_PATTERN = re.compile(
        r'scalacOptions\s*(?:\+\+)?=\s*Seq\s*\((?P<options>[^)]+)\)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Scala attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attribute-like constructs from Scala source code.

        Args:
            content: Scala source code
            file_path: Path to the source file

        Returns:
            Dictionary with keys: annotations, implicits, macros, dependencies, imports, packages
        """
        result = {
            'annotations': [],
            'implicits': [],
            'macros': [],
            'dependencies': [],
            'imports': [],
            'packages': [],
            'compiler_options': [],
        }

        # Detect file type for appropriate extraction
        is_build_file = (
            file_path.endswith('build.sbt') or
            file_path.endswith('plugins.sbt') or
            file_path.endswith('build.sc') or
            file_path.endswith('.scala') and '/project/' in file_path
        )

        if is_build_file:
            result['dependencies'] = self._extract_dependencies(content, file_path)
            result['compiler_options'] = self._extract_compiler_options(content, file_path)
        else:
            result['annotations'] = self._extract_annotations(content, file_path)
            result['implicits'] = self._extract_implicits(content, file_path)
            result['macros'] = self._extract_macros(content, file_path)
            result['imports'] = self._extract_imports(content, file_path)

        # Always extract packages
        result['packages'] = self._extract_packages(content, file_path)

        # Scala CLI deps in .scala files
        if file_path.endswith('.scala') or file_path.endswith('.sc'):
            cli_deps = self._extract_scala_cli_deps(content, file_path)
            result['dependencies'].extend(cli_deps)

        return result

    def _extract_annotations(self, content: str, file_path: str) -> List[ScalaAnnotationInfo]:
        """Extract annotation usages."""
        annotations = []
        lines = content.split('\n')

        for match in self.ANNOTATION_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            args_raw = match.group('args') or ''
            args = [a.strip() for a in args_raw.split(',') if a.strip()] if args_raw else []

            # Determine target: look at what follows the annotation
            target = None
            target_kind = "unknown"
            if line_number < len(lines):
                # Check current and next lines for the annotated element
                for check_line in range(line_number - 1, min(line_number + 3, len(lines))):
                    line_content = lines[check_line].strip()
                    if line_content.startswith('@'):
                        continue

                    target_match = re.match(
                        r'(?:(?:sealed|final|abstract|implicit|case|private|protected|override|lazy|open)\s+)*'
                        r'(?P<kind>class|trait|object|def|val|var|type|enum)\s+(?P<name>\w+)',
                        line_content
                    )
                    if target_match:
                        target = target_match.group('name')
                        kind_map = {
                            'class': 'class', 'trait': 'trait', 'object': 'object',
                            'def': 'method', 'val': 'field', 'var': 'field',
                            'type': 'type', 'enum': 'enum',
                        }
                        target_kind = kind_map.get(target_match.group('kind'), 'unknown')
                        break

            annotation = ScalaAnnotationInfo(
                name=name,
                target=target,
                target_kind=target_kind,
                arguments=args,
                file=file_path,
                line_number=line_number,
            )
            annotations.append(annotation)

        return annotations

    def _extract_implicits(self, content: str, file_path: str) -> List[ScalaImplicitInfo]:
        """Extract implicit values, defs, classes, and Scala 3 givens."""
        implicits = []

        # implicit val
        for match in self.IMPLICIT_VAL_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            impl_type = match.group('type')

            impl = ScalaImplicitInfo(
                name=name,
                type=impl_type,
                kind='implicit_val',
                file=file_path,
                line_number=line_number,
            )
            implicits.append(impl)

        # implicit def (check for conversions)
        for match in self.IMPLICIT_DEF_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            return_type = match.group('return_type')
            params_raw = match.group('params') or ''

            is_conversion = False
            from_type = None
            to_type = None

            # Detect implicit conversion: implicit def foo(x: A): B
            if params_raw and ':' in params_raw:
                param_parts = params_raw.split(':')
                if len(param_parts) == 2:
                    from_type = param_parts[1].strip()
                    to_type = return_type
                    # Simple heuristic: if no extra implicit params, likely a conversion
                    if 'implicit' not in params_raw:
                        is_conversion = True

            impl = ScalaImplicitInfo(
                name=name,
                type=return_type,
                kind='implicit_def',
                is_conversion=is_conversion,
                from_type=from_type,
                to_type=to_type,
                file=file_path,
                line_number=line_number,
            )
            implicits.append(impl)

        # implicit class
        for match in self.IMPLICIT_CLASS_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            params_raw = match.group('params') or ''

            # Extract the wrapped type
            wrapped_type = ""
            if ':' in params_raw:
                parts = params_raw.split(':')
                if len(parts) >= 2:
                    wrapped_type = parts[1].strip()

            impl = ScalaImplicitInfo(
                name=name,
                type=wrapped_type,
                kind='implicit_class',
                is_conversion=True,  # implicit classes are essentially conversions
                from_type=wrapped_type,
                to_type=name,
                file=file_path,
                line_number=line_number,
            )
            implicits.append(impl)

        # Scala 3 given
        for match in self.GIVEN_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name') or f"given_{match.group('type')}"
            given_type = match.group('type')

            impl = ScalaImplicitInfo(
                name=name,
                type=given_type,
                kind='given',
                file=file_path,
                line_number=line_number,
            )
            implicits.append(impl)

        return implicits

    def _extract_macros(self, content: str, file_path: str) -> List[ScalaMacroInfo]:
        """Extract macro definitions."""
        macros = []

        # Scala 2 macro def
        for match in self.MACRO_DEF_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            macros.append(ScalaMacroInfo(
                name=name,
                kind='macro',
                file=file_path,
                line_number=line_number,
            ))

        # Scala 3 inline/transparent inline
        for match in self.INLINE_DEF_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            is_transparent = bool(match.group('transparent'))
            macros.append(ScalaMacroInfo(
                name=name,
                kind='transparent_inline' if is_transparent else 'inline',
                file=file_path,
                line_number=line_number,
            ))

        # derives clause (typeclass derivation)
        for match in self.DERIVE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            typeclasses = [tc.strip() for tc in match.group('typeclasses').split(',') if tc.strip()]
            for tc in typeclasses:
                macros.append(ScalaMacroInfo(
                    name=f"derive_{tc}",
                    kind='derive',
                    description=f"Derives {tc}",
                    file=file_path,
                    line_number=line_number,
                ))

        return macros

    def _extract_dependencies(self, content: str, file_path: str) -> List[ScalaDependencyInfo]:
        """Extract SBT/Mill dependencies."""
        deps = []

        # SBT dependencies
        for match in self.SBT_DEP_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            scope_raw = match.group('scope') or ''
            scope = scope_raw.lower() if scope_raw else 'compile'
            if scope in ('test', 'it'):
                scope = scope
            elif scope == 'provided':
                scope = 'provided'
            else:
                scope = 'compile'

            dep = ScalaDependencyInfo(
                group_id=match.group('group'),
                artifact_id=match.group('artifact'),
                version=match.group('version'),
                scope=scope,
                cross_version=match.group('cross'),
                file=file_path,
                line_number=line_number,
            )
            deps.append(dep)

        # SBT plugins
        for match in self.SBT_PLUGIN_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            dep = ScalaDependencyInfo(
                group_id=match.group('group'),
                artifact_id=match.group('artifact'),
                version=match.group('version'),
                scope='plugin',
                cross_version='%',
                is_plugin=True,
                file=file_path,
                line_number=line_number,
            )
            deps.append(dep)

        # Compiler plugins
        for match in self.SBT_COMPILER_PLUGIN_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            dep = ScalaDependencyInfo(
                group_id=match.group('group'),
                artifact_id=match.group('artifact'),
                version=match.group('version'),
                scope='compile',
                cross_version=match.group('cross'),
                is_compiler_plugin=True,
                file=file_path,
                line_number=line_number,
            )
            deps.append(dep)

        # Mill dependencies
        for match in self.MILL_DEP_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            dep = ScalaDependencyInfo(
                group_id=match.group('group'),
                artifact_id=match.group('artifact'),
                version=match.group('version'),
                cross_version='%%',
                file=file_path,
                line_number=line_number,
            )
            deps.append(dep)

        return deps

    def _extract_scala_cli_deps(self, content: str, file_path: str) -> List[ScalaDependencyInfo]:
        """Extract Scala CLI //> using dep directives."""
        deps = []
        for match in self.SCALA_CLI_DEP_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            dep_str = match.group('dep').strip()

            # Parse group::artifact:version or group:artifact:version
            parts = re.split(r'::?', dep_str)
            if len(parts) >= 3:
                cross = '%%' if '::' in dep_str else '%'
                dep = ScalaDependencyInfo(
                    group_id=parts[0].strip(),
                    artifact_id=parts[1].strip(),
                    version=parts[2].strip(),
                    cross_version=cross,
                    file=file_path,
                    line_number=line_number,
                )
                deps.append(dep)

        return deps

    def _extract_imports(self, content: str, file_path: str) -> List[ScalaImportInfo]:
        """Extract import statements."""
        imports = []

        for match in self.IMPORT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            path = match.group('path')
            members_raw = match.group('members') or ''
            single = match.group('single') or ''

            members = []
            renames = {}
            is_wildcard = False
            given_import = False

            if single:
                if single in ('_', '*'):
                    is_wildcard = True
                elif single == 'given':
                    given_import = True
                else:
                    members = [single]
            elif members_raw:
                for member in members_raw.split(','):
                    member = member.strip()
                    if not member:
                        continue
                    if member in ('_', '*'):
                        is_wildcard = True
                    elif member == 'given':
                        given_import = True
                    elif '=>' in member or 'as' in member:
                        # Rename: OldName => NewName (Scala 2) or OldName as NewName (Scala 3)
                        if '=>' in member:
                            parts = member.split('=>')
                        else:
                            parts = member.split(' as ')
                        if len(parts) == 2:
                            old_name = parts[0].strip()
                            new_name = parts[1].strip()
                            renames[old_name] = new_name
                            if new_name != '_':
                                members.append(new_name)
                    else:
                        members.append(member)

            imp = ScalaImportInfo(
                path=path,
                members=members,
                is_wildcard=is_wildcard,
                renames=renames,
                given_import=given_import,
                file=file_path,
                line_number=line_number,
            )
            imports.append(imp)

        return imports

    def _extract_packages(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract package declarations."""
        packages = []
        for match in self.PACKAGE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            # Skip 'package object' lines
            full_match = content[match.start():match.end() + 10]
            if 'object' in full_match.split('\n')[0]:
                continue

            packages.append({
                'name': match.group('name'),
                'file': file_path,
                'line_number': line_number,
            })
        return packages

    def _extract_compiler_options(self, content: str, file_path: str) -> List[str]:
        """Extract compiler options from build files."""
        options = []
        for match in self.SCALAC_OPTIONS_PATTERN.finditer(content):
            opts_raw = match.group('options')
            for opt in re.findall(r'["\']([^"\']+)["\']', opts_raw):
                options.append(opt)
        return options
