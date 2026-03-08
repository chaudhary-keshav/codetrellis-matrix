"""
Tailwind CSS Component Extractor v1.0

Extracts Tailwind component patterns: @layer components definitions,
class composition patterns, and Tailwind directive usage.

Supports:
- @layer base/components/utilities definitions
- @apply-based component composition
- Component class extraction from @layer components blocks
- v4: @utility and @variant custom definitions

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TailwindComponentInfo:
    """Information about a Tailwind component definition."""
    name: str
    selector: str = ""
    utilities_applied: List[str] = field(default_factory=list)
    layer: str = ""  # base, components, utilities
    is_custom: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindLayerInfo:
    """Information about a @layer definition."""
    name: str  # base, components, utilities
    selector_count: int = 0
    selectors: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindDirectiveInfo:
    """Information about a Tailwind-specific directive."""
    directive: str  # @tailwind, @apply, @screen, @config, @layer
    value: str = ""
    file: str = ""
    line_number: int = 0


class TailwindComponentExtractor:
    """
    Extracts Tailwind component patterns from CSS files.

    Detects:
    - @layer components { ... } blocks with selectors and @apply usage
    - @layer base { ... } blocks for base style customizations
    - @layer utilities { ... } blocks for custom utility definitions
    - Component-like class definitions using @apply
    - Tailwind UI component patterns
    - v4 @utility definitions
    """

    # @layer pattern - captures layer name and body
    LAYER_PATTERN = re.compile(
        r'@layer\s+(base|components|utilities)\s*\{',
        re.MULTILINE
    )

    # Selector inside @layer with @apply
    COMPONENT_PATTERN = re.compile(
        r'(\.[\w-]+(?:\s*,\s*\.[\w-]+)*)\s*\{[^}]*?@apply\s+([^;]+);[^}]*\}',
        re.MULTILINE | re.DOTALL
    )

    # General @layer declarations (ordering)
    LAYER_ORDER_PATTERN = re.compile(
        r'@layer\s+([\w,\s]+)\s*;',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Tailwind component patterns.

        Args:
            content: CSS source code string.
            file_path: Path to the source file.

        Returns:
            Dict with extracted component info.
        """
        result: Dict[str, Any] = {
            'components': [],
            'layers': [],
            'directives': [],
            'layer_order': [],
            'stats': {},
        }

        if not content or not content.strip():
            return result

        # Extract layer blocks
        result['layers'] = self._extract_layers(content, file_path)

        # Extract components (selectors with @apply)
        result['components'] = self._extract_components(content, file_path)

        # Extract layer ordering
        result['layer_order'] = self._extract_layer_order(content)

        # Extract all Tailwind directives
        result['directives'] = self._extract_directives(content, file_path)

        # Stats
        result['stats'] = {
            'total_components': len(result['components']),
            'total_layers': len(result['layers']),
            'total_directives': len(result['directives']),
            'has_layer_order': len(result['layer_order']) > 0,
        }

        return result

    def _extract_layers(self, content: str, file_path: str) -> List[TailwindLayerInfo]:
        """Extract @layer block definitions."""
        results: List[TailwindLayerInfo] = []

        for m in self.LAYER_PATTERN.finditer(content):
            layer_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Find the matching closing brace
            start = m.end()
            brace_count = 1
            pos = start
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1

            if brace_count == 0:
                body = content[start:pos - 1]
                # Extract selectors from body
                selectors = re.findall(r'(\.[\w-]+(?:\s*,\s*\.[\w-]+)*)\s*\{', body)
                results.append(TailwindLayerInfo(
                    name=layer_name,
                    selector_count=len(selectors),
                    selectors=[s.strip() for s in selectors[:20]],
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_components(self, content: str, file_path: str) -> List[TailwindComponentInfo]:
        """Extract component-like definitions (selectors with @apply)."""
        results: List[TailwindComponentInfo] = []

        for m in self.COMPONENT_PATTERN.finditer(content):
            selector = m.group(1).strip()
            utilities_str = m.group(2).strip()
            utilities = [u.strip() for u in utilities_str.split() if u.strip()]
            line_num = content[:m.start()].count('\n') + 1

            # Determine which layer this is in
            layer = self._find_enclosing_layer(content, m.start())

            name = selector.lstrip('.').split(',')[0].strip()
            results.append(TailwindComponentInfo(
                name=name,
                selector=selector,
                utilities_applied=utilities,
                layer=layer,
                is_custom=True,
                file=file_path,
                line_number=line_num,
            ))

        return results

    def _find_enclosing_layer(self, content: str, position: int) -> str:
        """Find which @layer block encloses the given position."""
        # Search backwards for @layer
        preceding = content[:position]
        layer_matches = list(self.LAYER_PATTERN.finditer(preceding))
        if not layer_matches:
            return ""

        # Check if the last @layer's brace is still open
        last_match = layer_matches[-1]
        # Count braces between layer start and position
        between = content[last_match.end():position]
        open_count = between.count('{') + 1  # +1 for the layer's own opening brace
        close_count = between.count('}')

        if open_count > close_count:
            return last_match.group(1)
        return ""

    def _extract_layer_order(self, content: str) -> List[str]:
        """Extract @layer ordering declarations."""
        orders = []
        for m in self.LAYER_ORDER_PATTERN.finditer(content):
            layers_str = m.group(1)
            layers = [l.strip() for l in layers_str.split(',') if l.strip()]
            orders.extend(layers)
        return orders

    def _extract_directives(self, content: str, file_path: str) -> List[TailwindDirectiveInfo]:
        """Extract all Tailwind-specific directives."""
        results: List[TailwindDirectiveInfo] = []
        lines = content.split('\n')

        directive_patterns = [
            (r'@tailwind\s+([\w]+)\s*;', '@tailwind'),
            (r'@apply\s+([^;]+)\s*;', '@apply'),
            (r'@screen\s+([\w]+)', '@screen'),
            (r'@config\s+["\']([^"\']+)["\']', '@config'),
            (r'@layer\s+([\w,\s]+)', '@layer'),
            (r'@variants\s+([\w,\s]+)', '@variants'),
            (r'@responsive\b', '@responsive'),
            (r'@utility\s+([\w-]+)', '@utility'),
            (r'@variant\s+([\w-]+)', '@variant'),
            (r'@theme\b', '@theme'),
            (r'@source\s+["\']([^"\']+)["\']', '@source'),
            (r'@plugin\s+["\']([^"\']+)["\']', '@plugin'),
        ]

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            for pattern, directive_name in directive_patterns:
                m = re.match(pattern, stripped)
                if m:
                    value = m.group(1) if m.lastindex else ""
                    results.append(TailwindDirectiveInfo(
                        directive=directive_name,
                        value=value.strip(),
                        file=file_path,
                        line_number=i,
                    ))

        return results
