"""
Sass Nesting Extractor for CodeTrellis

Extracts SCSS/Sass nesting patterns, @extend, %placeholders,
@at-root, and selector structure analysis.

Supports:
- Nesting depth analysis per rule
- @extend usage (class and placeholder)
- %placeholder selectors (definitions and usages)
- @at-root directive (with/without queries)
- Parent selector & usage
- BEM-style nesting patterns (&__element, &--modifier)
- Selector nesting quality metrics

Part of CodeTrellis v4.44 — Sass/SCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class SassNestingInfo:
    """Information about nesting depth at a selector."""
    selector: str
    depth: int = 0
    has_parent_selector: bool = False  # Uses &
    is_bem_pattern: bool = False       # &__element or &--modifier
    file: str = ""
    line_number: int = 0


@dataclass
class SassExtendInfo:
    """Information about @extend usage."""
    target: str
    is_placeholder: bool = False       # @extend %placeholder
    is_optional: bool = False          # @extend .class !optional
    file: str = ""
    line_number: int = 0


@dataclass
class SassPlaceholderInfo:
    """Information about a %placeholder selector definition."""
    name: str
    extend_count: int = 0              # How many times it's @extended
    file: str = ""
    line_number: int = 0


@dataclass
class SassAtRootInfo:
    """Information about @at-root directive."""
    query: str = ""                    # e.g. "(without: media)"
    has_query: bool = False
    file: str = ""
    line_number: int = 0


class SassNestingExtractor:
    """
    Extracts Sass/SCSS nesting patterns and selector structure.
    """

    # @extend pattern
    EXTEND_PATTERN = re.compile(
        r'@extend\s+([^;!]+?)(\s*!optional)?\s*;',
        re.MULTILINE
    )

    # %placeholder definition
    PLACEHOLDER_DEF = re.compile(
        r'^(%[\w-]+)\s*\{',
        re.MULTILINE
    )

    # %placeholder in indented syntax
    SASS_PLACEHOLDER_DEF = re.compile(
        r'^(%[\w-]+)\s*$',
        re.MULTILINE
    )

    # @at-root directive
    AT_ROOT_PATTERN = re.compile(
        r'@at-root\s*(?:\(([^)]+)\)\s*)?(?:\{|$)',
        re.MULTILINE
    )

    # Parent selector &
    PARENT_SELECTOR = re.compile(r'&')

    # BEM patterns: &__element, &--modifier
    BEM_PATTERN = re.compile(r'&(?:__|--)([\w-]+)')

    # Selector rule (simplified — opening brace after selector)
    SELECTOR_RULE = re.compile(
        r'^([^{@/][^{]*?)\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract nesting patterns, @extend, placeholders, @at-root.

        Returns:
            Dict with 'nesting', 'extends', 'placeholders', 'at_roots', 'stats'
        """
        nesting_info: List[SassNestingInfo] = []
        extends: List[SassExtendInfo] = []
        placeholders: List[SassPlaceholderInfo] = []
        at_roots: List[SassAtRootInfo] = []

        # Remove comments
        clean = self._remove_comments(content)

        is_sass = file_path.lower().endswith('.sass')

        # Analyze nesting depths
        nesting_info = self._analyze_nesting(clean, file_path, is_sass)

        # Extract @extend usages
        for m in self.EXTEND_PATTERN.finditer(clean):
            target = m.group(1).strip()
            is_optional = bool(m.group(2))
            line_num = clean[:m.start()].count('\n') + 1

            extends.append(SassExtendInfo(
                target=target,
                is_placeholder=target.startswith('%'),
                is_optional=is_optional,
                file=file_path,
                line_number=line_num,
            ))

        # Extract %placeholder definitions
        ph_pattern = self.SASS_PLACEHOLDER_DEF if is_sass else self.PLACEHOLDER_DEF
        for m in ph_pattern.finditer(clean):
            name = m.group(1)
            line_num = clean[:m.start()].count('\n') + 1
            # Count extends of this placeholder
            extend_count = sum(
                1 for e in extends if e.target == name
            )
            placeholders.append(SassPlaceholderInfo(
                name=name,
                extend_count=extend_count,
                file=file_path,
                line_number=line_num,
            ))

        # Extract @at-root
        for m in self.AT_ROOT_PATTERN.finditer(clean):
            query = m.group(1) or ""
            line_num = clean[:m.start()].count('\n') + 1
            at_roots.append(SassAtRootInfo(
                query=query,
                has_query=bool(query),
                file=file_path,
                line_number=line_num,
            ))

        # Compute stats
        max_depth = max((n.depth for n in nesting_info), default=0)
        avg_depth = (
            sum(n.depth for n in nesting_info) / len(nesting_info)
            if nesting_info else 0
        )
        parent_selector_count = sum(1 for n in nesting_info if n.has_parent_selector)
        bem_count = sum(1 for n in nesting_info if n.is_bem_pattern)

        # Detect deep nesting warnings (depth > 4 is usually problematic)
        deep_nesting_selectors = [n for n in nesting_info if n.depth > 4]

        # Count unused placeholders
        extended_targets = {e.target for e in extends}
        unused_placeholders = [
            p for p in placeholders if p.name not in extended_targets
        ]

        stats = {
            "max_nesting_depth": max_depth,
            "avg_nesting_depth": round(avg_depth, 1),
            "total_rules": len(nesting_info),
            "parent_selector_count": parent_selector_count,
            "bem_pattern_count": bem_count,
            "total_extends": len(extends),
            "placeholder_extends": sum(1 for e in extends if e.is_placeholder),
            "class_extends": sum(1 for e in extends if not e.is_placeholder),
            "optional_extends": sum(1 for e in extends if e.is_optional),
            "total_placeholders": len(placeholders),
            "unused_placeholders": len(unused_placeholders),
            "at_root_count": len(at_roots),
            "deep_nesting_count": len(deep_nesting_selectors),
            "has_bem_patterns": bem_count > 0,
            "has_at_root": len(at_roots) > 0,
        }

        return {
            "nesting": nesting_info,
            "extends": extends,
            "placeholders": placeholders,
            "at_roots": at_roots,
            "stats": stats,
        }

    def _remove_comments(self, content: str) -> str:
        """Remove CSS/SCSS comments."""
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _analyze_nesting(self, content: str, file_path: str,
                         is_sass: bool) -> List[SassNestingInfo]:
        """Analyze nesting depths in the content."""
        results: List[SassNestingInfo] = []

        if is_sass:
            return self._analyze_indented_nesting(content, file_path)

        # Track brace depth
        depth = 0
        current_selector = ""
        i = 0
        line_num = 1

        while i < len(content):
            char = content[i]

            if char == '\n':
                line_num += 1
            elif char == '{':
                selector = current_selector.strip()
                if selector and not selector.startswith('@'):
                    has_parent = bool(self.PARENT_SELECTOR.search(selector))
                    is_bem = bool(self.BEM_PATTERN.search(selector))
                    results.append(SassNestingInfo(
                        selector=selector[:80],
                        depth=depth,
                        has_parent_selector=has_parent,
                        is_bem_pattern=is_bem,
                        file=file_path,
                        line_number=line_num,
                    ))
                depth += 1
                current_selector = ""
            elif char == '}':
                depth = max(0, depth - 1)
                current_selector = ""
            elif char == ';':
                current_selector = ""
            else:
                current_selector += char

            i += 1

        return results

    def _analyze_indented_nesting(self, content: str,
                                  file_path: str) -> List[SassNestingInfo]:
        """Analyze nesting in indented Sass syntax."""
        results: List[SassNestingInfo] = []

        for line_num, line in enumerate(content.split('\n'), 1):
            stripped = line.rstrip()
            if not stripped or stripped.startswith('//'):
                continue

            # Calculate indentation depth
            indent = len(line) - len(line.lstrip())
            depth = indent // 2  # Assume 2-space indent

            # Check if it looks like a selector
            clean_line = stripped.lstrip()
            if (clean_line and
                not clean_line.startswith('$') and
                not clean_line.startswith('@') and
                not clean_line.startswith('+') and
                not clean_line.startswith('=') and
                ':' not in clean_line and
                depth >= 0):

                has_parent = bool(self.PARENT_SELECTOR.search(clean_line))
                is_bem = bool(self.BEM_PATTERN.search(clean_line))

                if has_parent or (not clean_line.startswith('-') and
                                  not clean_line.startswith('//')):
                    results.append(SassNestingInfo(
                        selector=clean_line[:80],
                        depth=depth,
                        has_parent_selector=has_parent,
                        is_bem_pattern=is_bem,
                        file=file_path,
                        line_number=line_num,
                    ))

        return results
