"""
CSS Media Query Extractor for CodeTrellis

Extracts @media queries, @supports, @layer, @container queries,
and @import at-rules from CSS/SCSS/Less source code.

Supports:
- CSS3 Media Queries (screen, print, min-width, max-width, orientation)
- CSS4 Media Queries Level 4 (range syntax, prefers-*, hover, pointer)
- @supports feature queries
- @layer cascade layers (CSS Cascade Layers)
- @container queries (CSS Container Queries)
- @import rules
- @charset, @namespace declarations
- @property registered custom properties (Houdini)
- @scope rules (CSS Scoping)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSMediaQueryInfo:
    """Information about a CSS @media query."""
    query: str
    file: str = ""
    line_number: int = 0
    media_type: str = ""  # screen, print, all, speech
    features: List[str] = field(default_factory=list)
    is_range_syntax: bool = False  # CSS4 range syntax (width > 768px)
    is_prefers_query: bool = False  # prefers-color-scheme, prefers-reduced-motion
    nested_rule_count: int = 0


@dataclass
class CSSSupportsInfo:
    """Information about a CSS @supports feature query."""
    condition: str
    file: str = ""
    line_number: int = 0
    features_tested: List[str] = field(default_factory=list)
    is_negated: bool = False
    nested_rule_count: int = 0


@dataclass
class CSSLayerInfo:
    """Information about a CSS @layer declaration."""
    name: str
    file: str = ""
    line_number: int = 0
    is_declaration: bool = False  # @layer name; (order declaration)
    is_block: bool = False  # @layer name { ... }
    is_import: bool = False  # @import ... layer(name)
    nested_rule_count: int = 0


@dataclass
class CSSContainerQueryInfo:
    """Information about a CSS @container query."""
    name: str = ""
    query: str = ""
    file: str = ""
    line_number: int = 0
    container_type: str = ""  # inline-size, size, normal
    nested_rule_count: int = 0


class CSSMediaExtractor:
    """
    Extracts @-rule directives from CSS/SCSS/Less source code.

    Detects:
    - @media queries with feature detection
    - @supports feature queries
    - @layer cascade layers
    - @container queries
    - @import rules
    - @property Houdini custom properties
    - @scope rules
    - Responsive breakpoint patterns
    """

    MEDIA_PATTERN = re.compile(
        r'@media\s+([^{]+?)\s*\{',
        re.MULTILINE
    )

    SUPPORTS_PATTERN = re.compile(
        r'@supports\s+([^{]+?)\s*\{',
        re.MULTILINE
    )

    LAYER_BLOCK_PATTERN = re.compile(
        r'@layer\s+([\w-]+(?:\s*,\s*[\w-]+)*)\s*\{',
        re.MULTILINE
    )

    LAYER_DECL_PATTERN = re.compile(
        r'@layer\s+([\w-]+(?:\s*,\s*[\w-]+)*)\s*;',
        re.MULTILINE
    )

    CONTAINER_PATTERN = re.compile(
        r'@container\s+(?:([\w-]+)\s+)?(\([^{]+?\))\s*\{',
        re.MULTILINE
    )

    IMPORT_PATTERN = re.compile(
        r'@import\s+(?:url\(["\']?([^)"\']+)["\']?\)|["\']([^"\']+)["\'])\s*([^;]*);',
        re.MULTILINE
    )

    PROPERTY_PATTERN = re.compile(
        r'@property\s+(--[\w-]+)\s*\{([^}]+)\}',
        re.DOTALL
    )

    SCOPE_PATTERN = re.compile(
        r'@scope\s*(\([^)]*\))?\s*(?:to\s*(\([^)]*\)))?\s*\{',
        re.MULTILINE
    )

    CHARSET_PATTERN = re.compile(r'@charset\s+"([^"]+)"\s*;')
    NAMESPACE_PATTERN = re.compile(r'@namespace\s+(?:(\w+)\s+)?(?:url\()?["\']([^"\']+)["\']')

    # Media features for classification
    PREFERS_FEATURES = {'prefers-color-scheme', 'prefers-reduced-motion',
                        'prefers-contrast', 'prefers-reduced-transparency',
                        'prefers-reduced-data', 'forced-colors'}

    RANGE_SYNTAX = re.compile(r'(?:width|height|aspect-ratio|resolution)\s*[<>=]')

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all @-rule directives from CSS source code.

        Returns dict with:
          - media_queries: List[CSSMediaQueryInfo]
          - supports: List[CSSSupportsInfo]
          - layers: List[CSSLayerInfo]
          - container_queries: List[CSSContainerQueryInfo]
          - imports: List[Dict]
          - properties: List[Dict] (Houdini @property)
          - scopes: List[Dict]
          - breakpoints: List[Dict]
          - stats: Dict
        """
        media_queries: List[CSSMediaQueryInfo] = []
        supports: List[CSSSupportsInfo] = []
        layers: List[CSSLayerInfo] = []
        container_queries: List[CSSContainerQueryInfo] = []
        imports: List[Dict] = []
        registered_properties: List[Dict] = []
        scopes: List[Dict] = []
        breakpoints: List[Dict] = []

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        # Media queries
        for match in self.MEDIA_PATTERN.finditer(clean):
            query = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1
            features = self._extract_features(query)
            is_prefers = any(f in query for f in self.PREFERS_FEATURES)
            is_range = bool(self.RANGE_SYNTAX.search(query))

            media_type = ""
            for mt in ['screen', 'print', 'all', 'speech']:
                if mt in query:
                    media_type = mt
                    break

            # Extract breakpoint value if present
            bp = self._extract_breakpoint(query)
            if bp:
                breakpoints.append(bp)

            nested = self._count_nested_rules(clean, match.end())

            media_queries.append(CSSMediaQueryInfo(
                query=query,
                file=file_path,
                line_number=line_num,
                media_type=media_type,
                features=features,
                is_range_syntax=is_range,
                is_prefers_query=is_prefers,
                nested_rule_count=nested,
            ))

        # @supports
        for match in self.SUPPORTS_PATTERN.finditer(clean):
            condition = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1
            features_tested = re.findall(r'([\w-]+)\s*:', condition)
            is_negated = condition.strip().startswith('not')
            nested = self._count_nested_rules(clean, match.end())

            supports.append(CSSSupportsInfo(
                condition=condition,
                file=file_path,
                line_number=line_num,
                features_tested=features_tested,
                is_negated=is_negated,
                nested_rule_count=nested,
            ))

        # @layer blocks
        for match in self.LAYER_BLOCK_PATTERN.finditer(clean):
            name = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1
            nested = self._count_nested_rules(clean, match.end())

            layers.append(CSSLayerInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_block=True,
                nested_rule_count=nested,
            ))

        # @layer declarations
        for match in self.LAYER_DECL_PATTERN.finditer(clean):
            name = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1
            layers.append(CSSLayerInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_declaration=True,
            ))

        # @container queries
        for match in self.CONTAINER_PATTERN.finditer(clean):
            name = match.group(1) or ""
            query = match.group(2).strip()
            line_num = clean[:match.start()].count('\n') + 1
            nested = self._count_nested_rules(clean, match.end())

            container_queries.append(CSSContainerQueryInfo(
                name=name.strip(),
                query=query,
                file=file_path,
                line_number=line_num,
                nested_rule_count=nested,
            ))

        # @import
        for match in self.IMPORT_PATTERN.finditer(clean):
            url = match.group(1) or match.group(2)
            conditions = match.group(3).strip()
            line_num = clean[:match.start()].count('\n') + 1
            imports.append({
                "url": url,
                "conditions": conditions,
                "file": file_path,
                "line": line_num,
                "has_layer": 'layer' in conditions,
            })

        # @property (Houdini)
        for match in self.PROPERTY_PATTERN.finditer(clean):
            prop_name = match.group(1)
            body = match.group(2)
            line_num = clean[:match.start()].count('\n') + 1

            syntax_match = re.search(r'syntax\s*:\s*["\']([^"\']+)["\']', body)
            inherits_match = re.search(r'inherits\s*:\s*(true|false)', body)
            initial_match = re.search(r'initial-value\s*:\s*([^;]+)', body)

            registered_properties.append({
                "name": prop_name,
                "syntax": syntax_match.group(1) if syntax_match else "",
                "inherits": inherits_match.group(1) == "true" if inherits_match else True,
                "initial_value": initial_match.group(1).strip() if initial_match else "",
                "file": file_path,
                "line": line_num,
            })

        # @scope
        for match in self.SCOPE_PATTERN.finditer(clean):
            scope_start = match.group(1) or ""
            scope_end = match.group(2) or ""
            line_num = clean[:match.start()].count('\n') + 1
            scopes.append({
                "scope_start": scope_start.strip('()'),
                "scope_end": scope_end.strip('()'),
                "file": file_path,
                "line": line_num,
            })

        stats = {
            "total_media_queries": len(media_queries),
            "total_supports": len(supports),
            "total_layers": len(layers),
            "total_container_queries": len(container_queries),
            "total_imports": len(imports),
            "total_registered_properties": len(registered_properties),
            "total_scopes": len(scopes),
            "prefers_queries": sum(1 for m in media_queries if m.is_prefers_query),
            "range_syntax_queries": sum(1 for m in media_queries if m.is_range_syntax),
            "has_range_syntax": any(m.is_range_syntax for m in media_queries),
            "has_houdini": len(registered_properties) > 0,
        }

        return {
            "media_queries": media_queries,
            "supports": supports,
            "layers": layers,
            "container_queries": container_queries,
            "imports": imports,
            "registered_properties": registered_properties,
            "scopes": scopes,
            "breakpoints": breakpoints,
            "stats": stats,
        }

    def _extract_features(self, query: str) -> List[str]:
        """Extract media features from a query."""
        features = re.findall(r'([\w-]+)\s*:', query)
        return features

    def _extract_breakpoint(self, query: str) -> Optional[Dict]:
        """Extract breakpoint value from media query."""
        match = re.search(r'(?:min|max)-width\s*:\s*(\d+(?:\.\d+)?)(px|em|rem)', query)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            direction = "min" if "min-width" in query else "max"
            return {"value": value, "unit": unit, "direction": direction, "query": query}

        # CSS4 range syntax
        match = re.search(r'width\s*([<>=]+)\s*(\d+(?:\.\d+)?)(px|em|rem)', query)
        if match:
            return {"value": float(match.group(2)), "unit": match.group(3),
                    "direction": "range", "query": query}
        return None

    def _count_nested_rules(self, content: str, start: int) -> int:
        """Count nested rule blocks inside an @-rule."""
        depth = 1
        pos = start
        count = 0
        while pos < len(content) and depth > 0:
            ch = content[pos]
            if ch == '{':
                depth += 1
                if depth == 2:
                    count += 1
            elif ch == '}':
                depth -= 1
            pos += 1
        return count
