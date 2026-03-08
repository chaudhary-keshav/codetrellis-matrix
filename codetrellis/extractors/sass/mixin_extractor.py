"""
Sass Mixin Extractor for CodeTrellis

Extracts SCSS/Sass mixin definitions and @include usages.

Supports:
- @mixin definitions with parameters (defaults, rest args, keyword args)
- @include usages with arguments
- @content blocks (slot-like mixin content injection)
- Mixin nesting
- Conditional @content
- Mixin libraries detection (Bourbon, Compass, etc.)

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SassMixinDefInfo:
    """Information about a @mixin definition."""
    name: str
    parameters: List[str] = field(default_factory=list)
    has_defaults: bool = False
    has_rest_args: bool = False       # $args...
    has_content_block: bool = False   # @content inside body
    file: str = ""
    line_number: int = 0
    body_lines: int = 0


@dataclass
class SassMixinUsageInfo:
    """Information about an @include usage."""
    name: str
    arguments: List[str] = field(default_factory=list)
    has_content_block: bool = False  # @include name { ... }
    namespace: str = ""              # e.g. "mixins" for @include mixins.name
    file: str = ""
    line_number: int = 0


class SassMixinExtractor:
    """
    Extracts Sass/SCSS mixin definitions and @include usages.
    """

    # @mixin definition
    MIXIN_DEF = re.compile(
        r'@mixin\s+([\w-]+)\s*(?:\(([^)]*)\))?\s*\{',
        re.MULTILINE
    )

    # Indented sass mixin: =mixin-name(params)
    SASS_MIXIN_DEF = re.compile(
        r'^=([\w-]+)\s*(?:\(([^)]*)\))?',
        re.MULTILINE
    )

    # @include usage
    INCLUDE_PATTERN = re.compile(
        r'@include\s+(?:([\w-]+)\.)?([\w-]+)\s*(?:\(([^)]*)\))?\s*(;|\{)',
        re.MULTILINE
    )

    # Indented sass include: +mixin-name(args)
    SASS_INCLUDE_PATTERN = re.compile(
        r'^\s*\+([\w-]+)\s*(?:\(([^)]*)\))?',
        re.MULTILINE
    )

    # @content directive inside mixin body
    CONTENT_PATTERN = re.compile(r'@content\b', re.MULTILINE)

    # Rest args pattern
    REST_ARGS_PATTERN = re.compile(r'\$[\w-]+\.\.\.')

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract mixin definitions and usages.

        Returns:
            Dict with 'definitions', 'usages', 'stats'
        """
        definitions: List[SassMixinDefInfo] = []
        usages: List[SassMixinUsageInfo] = []

        # Remove comments
        clean = self._remove_comments(content)

        is_sass = file_path.lower().endswith('.sass')

        # Extract mixin definitions
        def_pattern = self.SASS_MIXIN_DEF if is_sass else self.MIXIN_DEF
        for m in def_pattern.finditer(clean):
            name = m.group(1)
            params_str = m.group(2) or ""
            line_num = clean[:m.start()].count('\n') + 1
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            has_defaults = any(':' in p for p in params)
            has_rest = bool(self.REST_ARGS_PATTERN.search(params_str))

            # Check for @content in body
            has_content = False
            body_lines = 0
            if not is_sass:
                body_lines, has_content = self._analyze_mixin_body(
                    clean, m.end() - 1
                )
            else:
                # For indented syntax, look at subsequent indented lines
                has_content = self._check_indented_content(clean, m.end())

            definitions.append(SassMixinDefInfo(
                name=name,
                parameters=params[:10],
                has_defaults=has_defaults,
                has_rest_args=has_rest,
                has_content_block=has_content,
                file=file_path,
                line_number=line_num,
                body_lines=body_lines,
            ))

        # Extract @include usages
        inc_pattern = self.SASS_INCLUDE_PATTERN if is_sass else self.INCLUDE_PATTERN
        for m in inc_pattern.finditer(clean):
            if is_sass:
                name = m.group(1)
                args_str = m.group(2) or ""
                namespace = ""
                has_block = False
            else:
                namespace = m.group(1) or ""
                name = m.group(2)
                args_str = m.group(3) or ""
                has_block = m.group(4) == '{'

            line_num = clean[:m.start()].count('\n') + 1
            args = [a.strip() for a in args_str.split(',') if a.strip()]

            usages.append(SassMixinUsageInfo(
                name=name,
                arguments=args[:10],
                has_content_block=has_block,
                namespace=namespace,
                file=file_path,
                line_number=line_num,
            ))

        # Detect mixin libraries
        libraries = self._detect_mixin_libraries(clean)

        stats = {
            "total_definitions": len(definitions),
            "total_usages": len(usages),
            "with_content_block": sum(1 for d in definitions if d.has_content_block),
            "with_defaults": sum(1 for d in definitions if d.has_defaults),
            "with_rest_args": sum(1 for d in definitions if d.has_rest_args),
            "content_block_usages": sum(1 for u in usages if u.has_content_block),
            "namespaced_usages": sum(1 for u in usages if u.namespace),
            "mixin_libraries": libraries,
        }

        return {
            "definitions": definitions,
            "usages": usages,
            "stats": stats,
        }

    def _remove_comments(self, content: str) -> str:
        """Remove CSS/SCSS comments."""
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _analyze_mixin_body(self, content: str, brace_pos: int) -> tuple:
        """Analyze mixin body: count lines and check for @content."""
        depth = 1
        pos = brace_pos + 1
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1

        body = content[brace_pos + 1:pos - 1] if pos > brace_pos + 1 else ""
        body_lines = body.count('\n') + 1
        has_content = bool(self.CONTENT_PATTERN.search(body))
        return body_lines, has_content

    def _check_indented_content(self, content: str, pos: int) -> bool:
        """Check for @content in indented sass block."""
        lines = content[pos:pos + 500].split('\n')
        for line in lines[1:]:
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                break
            if '@content' in line:
                return True
        return False

    def _detect_mixin_libraries(self, content: str) -> List[str]:
        """Detect known mixin libraries."""
        libraries = []
        library_patterns = {
            'bourbon': r'@(?:import|use)\s+["\'].*bourbon',
            'compass': r'@(?:import|use)\s+["\'].*compass',
            'susy': r'@(?:import|use)\s+["\'].*susy',
            'breakpoint': r'@(?:import|use)\s+["\'].*breakpoint',
            'animate.scss': r'@(?:import|use)\s+["\'].*animate',
            'include-media': r'@(?:import|use)\s+["\'].*include-media',
            'sass-mq': r'@(?:import|use)\s+["\'].*mq',
            'rfs': r'@(?:import|use)\s+["\'].*rfs',
            'mathsass': r'@(?:import|use)\s+["\'].*mathsass',
        }
        for lib, pattern in library_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                libraries.append(lib)
        return libraries
