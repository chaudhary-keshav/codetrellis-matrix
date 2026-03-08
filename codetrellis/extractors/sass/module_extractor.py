"""
Sass Module Extractor for CodeTrellis

Extracts SCSS/Sass module system constructs:
@use, @forward, @import, partials, and namespaces.

Supports:
- @use with as (namespace aliases), show/hide (member visibility)
- @forward with show/hide, prefix, and configuration ($var: value)
- @import (legacy, deprecated in Dart Sass)
- Partial detection (_partial.scss)
- Index files (_index.scss)
- Dart Sass module system (1.23.0+)
- Namespace analysis
- Circular dependency detection hints

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class SassUseInfo:
    """Information about a @use statement."""
    path: str
    namespace: str = ""            # alias or auto-derived
    as_clause: str = ""            # explicit 'as' value (* for no namespace)
    show_members: List[str] = field(default_factory=list)
    hide_members: List[str] = field(default_factory=list)
    with_config: Dict[str, str] = field(default_factory=dict)  # $var: value
    is_builtin: bool = False       # sass:math, sass:color, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class SassForwardInfo:
    """Information about a @forward statement."""
    path: str
    prefix: str = ""               # prefix for forwarded members
    show_members: List[str] = field(default_factory=list)
    hide_members: List[str] = field(default_factory=list)
    with_config: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class SassImportInfo:
    """Information about a legacy @import statement."""
    path: str
    is_partial: bool = False        # _ prefix
    is_css_import: bool = False     # ends in .css, url(), etc.
    file: str = ""
    line_number: int = 0


@dataclass
class SassPartialInfo:
    """Information about a Sass partial file."""
    name: str                       # without _prefix
    path: str
    is_index: bool = False          # _index.scss
    exported_members: List[str] = field(default_factory=list)


class SassModuleExtractor:
    """
    Extracts Sass/SCSS module system constructs.

    Detects @use/@forward (Dart Sass module system) and legacy @import,
    along with partial files and namespace patterns.
    """

    # @use pattern with optional as/show/hide/with
    USE_PATTERN = re.compile(
        r'@use\s+["\']([^"\']+)["\']'
        r'(?:\s+as\s+([\w*]+))?'
        r'(?:\s+with\s*\(([^)]+)\))?'
        r'(?:\s+show\s+([\w$,\s-]+))?'
        r'(?:\s+hide\s+([\w$,\s-]+))?',
        re.MULTILINE
    )

    # Alternative: @use with show/hide before with
    USE_SHOW_HIDE = re.compile(
        r'@use\s+["\']([^"\']+)["\']'
        r'(?:\s+as\s+([\w*]+))?'
        r'(?:\s+show\s+([\w$,\s-]+))?'
        r'(?:\s+hide\s+([\w$,\s-]+))?',
        re.MULTILINE
    )

    # @forward pattern
    FORWARD_PATTERN = re.compile(
        r'@forward\s+["\']([^"\']+)["\']'
        r'(?:\s+as\s+([\w-]+-\*))?'
        r'(?:\s+show\s+([\w$,\s-]+))?'
        r'(?:\s+hide\s+([\w$,\s-]+))?'
        r'(?:\s+with\s*\(([^)]+)\))?',
        re.MULTILINE
    )

    # @import pattern (legacy)
    IMPORT_PATTERN = re.compile(
        r'@import\s+["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Built-in Sass modules
    BUILTIN_MODULES: Set[str] = {
        'sass:math', 'sass:color', 'sass:string', 'sass:list',
        'sass:map', 'sass:selector', 'sass:meta',
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract module system constructs.

        Returns:
            Dict with 'uses', 'forwards', 'imports', 'partials', 'stats'
        """
        uses: List[SassUseInfo] = []
        forwards: List[SassForwardInfo] = []
        imports: List[SassImportInfo] = []

        # Remove comments
        clean = self._remove_comments(content)

        # Extract @use statements
        for m in self.USE_PATTERN.finditer(clean):
            path = m.group(1)
            as_clause = m.group(2) or ""
            with_config_str = m.group(3) or ""
            show_str = m.group(4) or ""
            hide_str = m.group(5) or ""
            line_num = clean[:m.start()].count('\n') + 1

            namespace = as_clause
            if not namespace:
                # Auto-derive namespace from path
                namespace = self._derive_namespace(path)

            is_builtin = path in self.BUILTIN_MODULES

            with_config = {}
            if with_config_str:
                with_config = self._parse_config(with_config_str)

            show_members = [s.strip() for s in show_str.split(',') if s.strip()] if show_str else []
            hide_members = [s.strip() for s in hide_str.split(',') if s.strip()] if hide_str else []

            uses.append(SassUseInfo(
                path=path,
                namespace=namespace,
                as_clause=as_clause,
                show_members=show_members,
                hide_members=hide_members,
                with_config=with_config,
                is_builtin=is_builtin,
                file=file_path,
                line_number=line_num,
            ))

        # Also try the alternative pattern for show/hide without with
        if not uses:
            for m in self.USE_SHOW_HIDE.finditer(clean):
                path = m.group(1)
                as_clause = m.group(2) or ""
                show_str = m.group(3) or ""
                hide_str = m.group(4) or ""
                line_num = clean[:m.start()].count('\n') + 1

                namespace = as_clause or self._derive_namespace(path)
                is_builtin = path in self.BUILTIN_MODULES

                show_members = [s.strip() for s in show_str.split(',') if s.strip()] if show_str else []
                hide_members = [s.strip() for s in hide_str.split(',') if s.strip()] if hide_str else []

                uses.append(SassUseInfo(
                    path=path,
                    namespace=namespace,
                    as_clause=as_clause,
                    show_members=show_members,
                    hide_members=hide_members,
                    is_builtin=is_builtin,
                    file=file_path,
                    line_number=line_num,
                ))

        # Extract @forward statements
        for m in self.FORWARD_PATTERN.finditer(clean):
            path = m.group(1)
            prefix = m.group(2) or ""
            show_str = m.group(3) or ""
            hide_str = m.group(4) or ""
            with_config_str = m.group(5) or ""
            line_num = clean[:m.start()].count('\n') + 1

            with_config = {}
            if with_config_str:
                with_config = self._parse_config(with_config_str)

            show_members = [s.strip() for s in show_str.split(',') if s.strip()] if show_str else []
            hide_members = [s.strip() for s in hide_str.split(',') if s.strip()] if hide_str else []

            forwards.append(SassForwardInfo(
                path=path,
                prefix=prefix,
                show_members=show_members,
                hide_members=hide_members,
                with_config=with_config,
                file=file_path,
                line_number=line_num,
            ))

        # Extract @import statements (legacy)
        for m in self.IMPORT_PATTERN.finditer(clean):
            path = m.group(1)
            line_num = clean[:m.start()].count('\n') + 1

            is_css = (
                path.endswith('.css') or
                path.startswith('http://') or
                path.startswith('https://') or
                path.startswith('url(')
            )

            is_partial = '/' in path and path.rsplit('/', 1)[-1].startswith('_')

            imports.append(SassImportInfo(
                path=path,
                is_partial=is_partial,
                is_css_import=is_css,
                file=file_path,
                line_number=line_num,
            ))

        # Detect partial file
        partial_info = self._detect_partial(file_path, content)

        # Determine module system used
        module_system = "none"
        if uses or forwards:
            module_system = "dart_sass"  # Modern @use/@forward
        elif imports:
            module_system = "legacy"     # Legacy @import

        # Count built-in module usage
        builtin_modules_used = [u.path for u in uses if u.is_builtin]

        stats = {
            "total_uses": len(uses),
            "total_forwards": len(forwards),
            "total_imports": len(imports),
            "module_system": module_system,
            "builtin_modules_used": builtin_modules_used,
            "has_namespaces": any(u.as_clause for u in uses),
            "has_show_hide": any(u.show_members or u.hide_members for u in uses),
            "has_configuration": any(u.with_config for u in uses) or any(f.with_config for f in forwards),
            "has_prefixes": any(f.prefix for f in forwards),
            "is_partial": partial_info is not None,
            "css_imports": sum(1 for i in imports if i.is_css_import),
        }

        result: Dict[str, Any] = {
            "uses": uses,
            "forwards": forwards,
            "imports": imports,
            "stats": stats,
        }

        if partial_info:
            result["partial"] = partial_info

        return result

    def _remove_comments(self, content: str) -> str:
        """Remove CSS/SCSS comments."""
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _derive_namespace(self, path: str) -> str:
        """Derive namespace from module path."""
        # sass:math -> math
        if path.startswith('sass:'):
            return path.split(':')[1]
        # Remove directory path and extension
        name = path.rsplit('/', 1)[-1]
        # Remove _ prefix (partial)
        if name.startswith('_'):
            name = name[1:]
        # Remove extension
        for ext in ('.scss', '.sass', '.css'):
            if name.endswith(ext):
                name = name[:-len(ext)]
        return name

    def _parse_config(self, config_str: str) -> Dict[str, str]:
        """Parse @use/@forward with ($var: value) configuration."""
        config: Dict[str, str] = {}
        pairs = config_str.split(',')
        for pair in pairs:
            pair = pair.strip()
            if ':' in pair:
                key, value = pair.split(':', 1)
                config[key.strip()] = value.strip()
        return config

    def _detect_partial(self, file_path: str, content: str) -> Optional[SassPartialInfo]:
        """Detect if current file is a partial."""
        if not file_path:
            return None

        import os
        basename = os.path.basename(file_path)
        if not basename.startswith('_'):
            return None

        name = basename.lstrip('_')
        for ext in ('.scss', '.sass'):
            if name.endswith(ext):
                name = name[:-len(ext)]

        is_index = name == 'index'

        # Extract exported members (rough heuristic)
        exported = []
        var_pattern = re.compile(r'(\$[\w-]+)\s*:', re.MULTILINE)
        for m in var_pattern.finditer(content):
            exported.append(m.group(1))
        mixin_pattern = re.compile(r'@mixin\s+([\w-]+)', re.MULTILINE)
        for m in mixin_pattern.finditer(content):
            exported.append(m.group(1))
        func_pattern = re.compile(r'@function\s+([\w-]+)', re.MULTILINE)
        for m in func_pattern.finditer(content):
            exported.append(m.group(1))

        return SassPartialInfo(
            name=name,
            path=file_path,
            is_index=is_index,
            exported_members=exported[:20],
        )
