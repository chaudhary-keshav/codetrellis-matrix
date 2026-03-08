"""
Tailwind CSS Utility Extractor v1.0

Extracts Tailwind utility class usage patterns, @apply directives,
arbitrary values, and responsive/state variants.

Supports:
- Tailwind v1.x: Basic utility classes
- Tailwind v2.x: Dark mode, JIT mode, ring utilities
- Tailwind v3.x: Arbitrary values, arbitrary properties, important modifier
- Tailwind v4.x: CSS-first configuration, @theme directive, @utility directive

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple


@dataclass
class TailwindUtilityInfo:
    """Information about a Tailwind utility class usage."""
    class_name: str
    category: str = ""  # layout, spacing, typography, color, etc.
    variant: str = ""  # hover, focus, sm, md, lg, dark, etc.
    is_arbitrary: bool = False
    arbitrary_value: str = ""
    is_negative: bool = False
    is_important: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindApplyInfo:
    """Information about an @apply directive usage."""
    selector: str = ""
    utilities: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindArbitraryInfo:
    """Information about arbitrary value usage."""
    property_name: str = ""
    value: str = ""
    is_arbitrary_property: bool = False  # [property:value] syntax
    file: str = ""
    line_number: int = 0


class TailwindUtilityExtractor:
    """
    Extracts Tailwind utility class usage patterns from CSS and template files.

    Detects:
    - @apply directive usage with utility class lists
    - @tailwind directives (base, components, utilities)
    - Utility class categorization (layout, spacing, typography, colors, etc.)
    - Responsive variants (sm:, md:, lg:, xl:, 2xl:)
    - State variants (hover:, focus:, active:, dark:, etc.)
    - Arbitrary values (w-[100px], text-[#1da1f2])
    - Arbitrary properties ([mask-type:luminance])
    - Important modifier (!text-red-500)
    - Negative values (-mt-4, -translate-x-1/2)
    """

    # Tailwind utility class categories
    UTILITY_CATEGORIES = {
        # Layout
        'container': 'layout', 'columns': 'layout',
        'break-after': 'layout', 'break-before': 'layout', 'break-inside': 'layout',
        'box-decoration': 'layout', 'box': 'layout',
        'block': 'layout', 'inline': 'layout', 'flex': 'layout', 'grid': 'layout',
        'table': 'layout', 'hidden': 'layout', 'contents': 'layout',
        'list-item': 'layout', 'flow-root': 'layout',
        'float': 'layout', 'clear': 'layout', 'isolate': 'layout',
        'isolation': 'layout', 'object': 'layout', 'overflow': 'layout',
        'overscroll': 'layout', 'static': 'layout', 'fixed': 'layout',
        'absolute': 'layout', 'relative': 'layout', 'sticky': 'layout',
        'inset': 'layout', 'top': 'layout', 'right': 'layout',
        'bottom': 'layout', 'left': 'layout', 'visible': 'layout',
        'invisible': 'layout', 'z': 'layout',
        # Flexbox & Grid
        'basis': 'flexbox_grid', 'flex-row': 'flexbox_grid', 'flex-col': 'flexbox_grid',
        'flex-wrap': 'flexbox_grid', 'flex-nowrap': 'flexbox_grid',
        'flex-1': 'flexbox_grid', 'flex-auto': 'flexbox_grid', 'flex-initial': 'flexbox_grid',
        'flex-none': 'flexbox_grid', 'grow': 'flexbox_grid', 'shrink': 'flexbox_grid',
        'order': 'flexbox_grid',
        'grid-cols': 'flexbox_grid', 'col-span': 'flexbox_grid',
        'col-start': 'flexbox_grid', 'col-end': 'flexbox_grid',
        'grid-rows': 'flexbox_grid', 'row-span': 'flexbox_grid',
        'row-start': 'flexbox_grid', 'row-end': 'flexbox_grid',
        'grid-flow': 'flexbox_grid', 'auto-cols': 'flexbox_grid',
        'auto-rows': 'flexbox_grid', 'gap': 'flexbox_grid',
        'justify': 'flexbox_grid', 'items': 'flexbox_grid',
        'content': 'flexbox_grid', 'self': 'flexbox_grid',
        'place': 'flexbox_grid',
        # Spacing
        'p': 'spacing', 'px': 'spacing', 'py': 'spacing',
        'pt': 'spacing', 'pr': 'spacing', 'pb': 'spacing', 'pl': 'spacing',
        'ps': 'spacing', 'pe': 'spacing',
        'm': 'spacing', 'mx': 'spacing', 'my': 'spacing',
        'mt': 'spacing', 'mr': 'spacing', 'mb': 'spacing', 'ml': 'spacing',
        'ms': 'spacing', 'me': 'spacing',
        'space-x': 'spacing', 'space-y': 'spacing',
        # Sizing
        'w': 'sizing', 'min-w': 'sizing', 'max-w': 'sizing',
        'h': 'sizing', 'min-h': 'sizing', 'max-h': 'sizing',
        'size': 'sizing',
        # Typography
        'font': 'typography', 'text': 'typography', 'antialiased': 'typography',
        'subpixel-antialiased': 'typography', 'italic': 'typography',
        'not-italic': 'typography', 'tracking': 'typography',
        'leading': 'typography', 'list': 'typography', 'placeholder': 'typography',
        'decoration': 'typography', 'underline': 'typography',
        'overline': 'typography', 'line-through': 'typography',
        'no-underline': 'typography', 'uppercase': 'typography',
        'lowercase': 'typography', 'capitalize': 'typography',
        'normal-case': 'typography', 'truncate': 'typography',
        'indent': 'typography', 'align': 'typography',
        'whitespace': 'typography', 'break': 'typography', 'hyphens': 'typography',
        'content-none': 'typography',
        # Colors / Backgrounds
        'bg': 'colors', 'from': 'colors', 'via': 'colors', 'to': 'colors',
        'gradient': 'colors', 'text-opacity': 'colors',
        'bg-opacity': 'colors',
        # Borders
        'border': 'borders', 'rounded': 'borders', 'divide': 'borders',
        'outline': 'borders', 'ring': 'borders', 'ring-offset': 'borders',
        # Effects
        'shadow': 'effects', 'opacity': 'effects', 'mix-blend': 'effects',
        'bg-blend': 'effects',
        # Filters
        'blur': 'filters', 'brightness': 'filters', 'contrast': 'filters',
        'drop-shadow': 'filters', 'grayscale': 'filters', 'hue-rotate': 'filters',
        'invert': 'filters', 'saturate': 'filters', 'sepia': 'filters',
        'backdrop-blur': 'filters', 'backdrop-brightness': 'filters',
        'backdrop-contrast': 'filters', 'backdrop-grayscale': 'filters',
        'backdrop-hue-rotate': 'filters', 'backdrop-invert': 'filters',
        'backdrop-opacity': 'filters', 'backdrop-saturate': 'filters',
        'backdrop-sepia': 'filters',
        # Transforms
        'scale': 'transforms', 'rotate': 'transforms', 'translate': 'transforms',
        'skew': 'transforms', 'origin': 'transforms',
        # Transitions & Animation
        'transition': 'transitions', 'duration': 'transitions',
        'ease': 'transitions', 'delay': 'transitions', 'animate': 'transitions',
        # Interactivity
        'accent': 'interactivity', 'appearance': 'interactivity',
        'cursor': 'interactivity', 'caret': 'interactivity',
        'pointer-events': 'interactivity', 'resize': 'interactivity',
        'scroll': 'interactivity', 'snap': 'interactivity',
        'touch': 'interactivity', 'select': 'interactivity',
        'will-change': 'interactivity',
        # Accessibility
        'sr-only': 'accessibility', 'not-sr-only': 'accessibility',
        'forced-color-adjust': 'accessibility',
    }

    # Responsive variants
    RESPONSIVE_VARIANTS = {'sm', 'md', 'lg', 'xl', '2xl'}

    # State variants
    STATE_VARIANTS = {
        'hover', 'focus', 'focus-within', 'focus-visible', 'active',
        'visited', 'target', 'first', 'last', 'only', 'odd', 'even',
        'first-of-type', 'last-of-type', 'only-of-type', 'empty',
        'disabled', 'enabled', 'checked', 'indeterminate', 'default',
        'required', 'valid', 'invalid', 'in-range', 'out-of-range',
        'placeholder-shown', 'autofill', 'read-only',
        'before', 'after', 'first-letter', 'first-line', 'marker',
        'selection', 'file', 'backdrop', 'placeholder',
        'dark', 'motion-safe', 'motion-reduce', 'contrast-more',
        'contrast-less', 'portrait', 'landscape', 'print',
        'rtl', 'ltr', 'open', 'closed',
        'group-hover', 'group-focus', 'peer-hover', 'peer-focus',
        'aria-checked', 'aria-disabled', 'aria-expanded',
        'aria-hidden', 'aria-pressed', 'aria-readonly',
        'aria-required', 'aria-selected',
        'data', 'supports', 'has',
    }

    # @apply pattern
    APPLY_PATTERN = re.compile(
        r'(?P<selector>[^{]+?)\s*\{\s*(?:[^}]*?)?@apply\s+(?P<utilities>[^;]+);',
        re.MULTILINE | re.DOTALL
    )

    # Arbitrary value pattern: class-[value]
    ARBITRARY_VALUE_PATTERN = re.compile(
        r'(?:^|\s|["\'])(?P<prefix>[\w-]+)-\[(?P<value>[^\]]+)\]',
        re.MULTILINE
    )

    # Arbitrary property pattern: [property:value]
    ARBITRARY_PROPERTY_PATTERN = re.compile(
        r'(?:^|\s|["\'])\[(?P<property>[\w-]+):(?P<value>[^\]]+)\]',
        re.MULTILINE
    )

    # @tailwind directive
    TAILWIND_DIRECTIVE_PATTERN = re.compile(
        r'@tailwind\s+(base|components|utilities|variants)\s*;',
        re.MULTILINE
    )

    # @screen directive (v1/v2)
    SCREEN_DIRECTIVE_PATTERN = re.compile(
        r'@screen\s+([\w]+)\s*\{',
        re.MULTILINE
    )

    # @variants directive (v1/v2)
    VARIANTS_DIRECTIVE_PATTERN = re.compile(
        r'@variants\s+([\w,\s]+)\s*\{',
        re.MULTILINE
    )

    # @responsive directive (v1/v2)
    RESPONSIVE_DIRECTIVE_PATTERN = re.compile(
        r'@responsive\s*\{',
        re.MULTILINE
    )

    # theme() function usage
    THEME_FUNCTION_PATTERN = re.compile(
        r'theme\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # v4: @utility directive
    UTILITY_DIRECTIVE_PATTERN = re.compile(
        r'@utility\s+([\w-]+)\s*\{',
        re.MULTILINE
    )

    # v4: @variant directive
    VARIANT_DIRECTIVE_PATTERN = re.compile(
        r'@variant\s+([\w-]+)\s*(?:\([^)]*\)\s*)?(?:\{|;)',
        re.MULTILINE
    )

    # v4: @theme directive
    THEME_DIRECTIVE_PATTERN = re.compile(
        r'@theme\s*(?:inline\s*)?\{',
        re.MULTILINE
    )

    # v4: @source directive
    SOURCE_DIRECTIVE_PATTERN = re.compile(
        r'@source\s+["\']([^"\']+)["\']\s*;',
        re.MULTILINE
    )

    # v4: @plugin directive
    PLUGIN_DIRECTIVE_PATTERN = re.compile(
        r'@plugin\s+["\']([^"\']+)["\']\s*;',
        re.MULTILINE
    )

    # v4: @config directive
    CONFIG_DIRECTIVE_PATTERN = re.compile(
        r'@config\s+["\']([^"\']+)["\']\s*;',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Tailwind utility patterns from content.

        Args:
            content: CSS/HTML/JSX source code string.
            file_path: Path to the source file.

        Returns:
            Dict with extracted utility info.
        """
        result: Dict[str, Any] = {
            'utilities': [],
            'apply_directives': [],
            'arbitrary_values': [],
            'tailwind_directives': [],
            'screen_directives': [],
            'theme_functions': [],
            'v4_utilities': [],
            'v4_variants': [],
            'v4_themes': [],
            'v4_sources': [],
            'v4_plugins': [],
            'v4_configs': [],
            'stats': {},
        }

        if not content or not content.strip():
            return result

        lines = content.split('\n')

        # Extract @apply directives
        result['apply_directives'] = self._extract_apply_directives(content, file_path)

        # Extract @tailwind directives
        result['tailwind_directives'] = self._extract_tailwind_directives(content, file_path)

        # Extract @screen directives (v1/v2)
        result['screen_directives'] = self._extract_screen_directives(content, file_path)

        # Extract arbitrary values
        result['arbitrary_values'] = self._extract_arbitrary_values(content, file_path)

        # Extract theme() function calls
        result['theme_functions'] = self._extract_theme_functions(content, file_path)

        # Extract v4-specific directives
        result['v4_utilities'] = self._extract_v4_utilities(content, file_path)
        result['v4_variants'] = self._extract_v4_variants(content, file_path)
        result['v4_themes'] = self._extract_v4_themes(content, file_path)
        result['v4_sources'] = self._extract_v4_sources(content, file_path)
        result['v4_plugins'] = self._extract_v4_plugins(content, file_path)
        result['v4_configs'] = self._extract_v4_configs(content, file_path)

        # Compute stats
        result['stats'] = {
            'total_apply': len(result['apply_directives']),
            'total_arbitrary': len(result['arbitrary_values']),
            'total_tailwind_directives': len(result['tailwind_directives']),
            'total_theme_functions': len(result['theme_functions']),
            'has_v4_features': bool(
                result['v4_utilities'] or result['v4_variants'] or
                result['v4_themes'] or result['v4_sources'] or
                result['v4_plugins'] or result['v4_configs']
            ),
        }

        return result

    def _extract_apply_directives(self, content: str, file_path: str) -> List[TailwindApplyInfo]:
        """Extract @apply directive usages."""
        results: List[TailwindApplyInfo] = []
        lines = content.split('\n')

        # Find @apply directives with their enclosing selector
        current_selector = ""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track selector context
            if '{' in stripped and '@' not in stripped:
                # Simple selector detection
                sel_match = re.match(r'^([^{]+)\s*\{', stripped)
                if sel_match:
                    current_selector = sel_match.group(1).strip()

            # Detect @apply
            apply_match = re.match(r'@apply\s+(.+?)\s*;', stripped)
            if apply_match:
                utilities_str = apply_match.group(1)
                utilities = [u.strip() for u in utilities_str.split() if u.strip()]
                results.append(TailwindApplyInfo(
                    selector=current_selector,
                    utilities=utilities,
                    file=file_path,
                    line_number=i,
                ))

            # Reset selector on closing brace
            if '}' in stripped:
                current_selector = ""

        return results

    def _extract_tailwind_directives(self, content: str, file_path: str) -> List[str]:
        """Extract @tailwind directive declarations."""
        directives = []
        for m in self.TAILWIND_DIRECTIVE_PATTERN.finditer(content):
            directives.append(m.group(1))
        return directives

    def _extract_screen_directives(self, content: str, file_path: str) -> List[str]:
        """Extract @screen directive usages (v1/v2)."""
        screens = []
        for m in self.SCREEN_DIRECTIVE_PATTERN.finditer(content):
            screens.append(m.group(1))
        return screens

    def _extract_arbitrary_values(self, content: str, file_path: str) -> List[TailwindArbitraryInfo]:
        """Extract arbitrary value and property usages."""
        results: List[TailwindArbitraryInfo] = []

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Arbitrary values: class-[value]
            for m in self.ARBITRARY_VALUE_PATTERN.finditer(line):
                results.append(TailwindArbitraryInfo(
                    property_name=m.group('prefix'),
                    value=m.group('value'),
                    is_arbitrary_property=False,
                    file=file_path,
                    line_number=i,
                ))

            # Arbitrary properties: [property:value]
            for m in self.ARBITRARY_PROPERTY_PATTERN.finditer(line):
                results.append(TailwindArbitraryInfo(
                    property_name=m.group('property'),
                    value=m.group('value'),
                    is_arbitrary_property=True,
                    file=file_path,
                    line_number=i,
                ))

        return results

    def _extract_theme_functions(self, content: str, file_path: str) -> List[str]:
        """Extract theme() function usages."""
        return [m.group(1) for m in self.THEME_FUNCTION_PATTERN.finditer(content)]

    def _extract_v4_utilities(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @utility directives (Tailwind v4)."""
        results = []
        for m in self.UTILITY_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'name': m.group(1),
                'file': file_path,
                'line': line_num,
            })
        return results

    def _extract_v4_variants(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @variant directives (Tailwind v4)."""
        results = []
        for m in self.VARIANT_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'name': m.group(1),
                'file': file_path,
                'line': line_num,
            })
        return results

    def _extract_v4_themes(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @theme directives (Tailwind v4)."""
        results = []
        for m in self.THEME_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'file': file_path,
                'line': line_num,
            })
        return results

    def _extract_v4_sources(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @source directives (Tailwind v4)."""
        results = []
        for m in self.SOURCE_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'path': m.group(1),
                'file': file_path,
                'line': line_num,
            })
        return results

    def _extract_v4_plugins(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @plugin directives (Tailwind v4)."""
        results = []
        for m in self.PLUGIN_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'path': m.group(1),
                'file': file_path,
                'line': line_num,
            })
        return results

    def _extract_v4_configs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract @config directives (Tailwind v4)."""
        results = []
        for m in self.CONFIG_DIRECTIVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            results.append({
                'path': m.group(1),
                'file': file_path,
                'line': line_num,
            })
        return results

    def categorize_utility(self, class_name: str) -> str:
        """Categorize a Tailwind utility class into a category."""
        # Remove variant prefixes (hover:, sm:, etc.)
        base = class_name
        while ':' in base:
            base = base.split(':', 1)[1]

        # Remove negative prefix
        if base.startswith('-'):
            base = base[1:]

        # Remove important modifier
        if base.startswith('!'):
            base = base[1:]

        # Check exact matches first
        if base in self.UTILITY_CATEGORIES:
            return self.UTILITY_CATEGORIES[base]

        # Check prefix matches
        for prefix, category in self.UTILITY_CATEGORIES.items():
            if base.startswith(prefix + '-') or base == prefix:
                return category

        # Color classes (text-*, bg-*)
        if base.startswith('text-') and not base.startswith('text-opacity'):
            return 'typography'

        return 'other'
