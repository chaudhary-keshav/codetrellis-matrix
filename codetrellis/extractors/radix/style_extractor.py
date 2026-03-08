"""
Radix UI Style Extractor for CodeTrellis

Extracts styling patterns used with Radix UI components — CSS modules,
styled-components, Stitches, Tailwind CSS, vanilla-extract,
data-attribute selectors, CSS variable usage.

Radix Primitives are unstyled by default, so detecting how they
are styled is important for understanding the project architecture.

Styling approaches:
- CSS Modules (.module.css / .module.scss)
- Stitches (styled() / css() — co-created by Radix team)
- Tailwind CSS (className=)
- styled-components / Emotion (styled())
- vanilla-extract (style.css.ts / recipe())
- Inline styles (style={})
- CSS-in-JS (sx prop)
- Data attribute selectors for Radix state (&[data-state="open"])

Data Attributes (Radix state management):
- data-state: open, closed, active, inactive, checked, unchecked, indeterminate
- data-side: top, right, bottom, left
- data-align: start, center, end
- data-orientation: horizontal, vertical
- data-disabled: (presence)
- data-highlighted: (presence)
- data-placeholder: (presence)
- data-swipe: start, move, end, cancel
- data-swipe-direction: up, down, left, right
- data-motion: from-start, from-end, to-start, to-end

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RadixStylePatternInfo:
    """Information about a styling approach used with Radix UI."""
    file: str = ""
    line_number: int = 0
    approach: str = ""            # css-modules, stitches, tailwind, styled-components, vanilla-extract, inline, emotion
    framework_import: str = ""    # Import source for styling framework
    component: str = ""           # Which Radix component is being styled
    has_animation: bool = False   # Includes animation/transition styles
    has_responsive: bool = False  # Includes responsive/media query styles
    has_dark_mode: bool = False   # Includes dark mode styles
    class_count: int = 0          # Number of class names / utility classes


@dataclass
class RadixDataAttributeInfo:
    """Information about Radix data-* attribute usage in CSS/styling."""
    attribute: str               # data-state, data-side, etc.
    file: str = ""
    line_number: int = 0
    value: str = ""              # open, closed, etc.
    selector: str = ""           # Full CSS selector string
    context: str = ""            # animation, visibility, positioning, interaction


class RadixStyleExtractor:
    """
    Extracts styling patterns used with Radix UI components.

    Detects:
    - CSS Modules with data-attribute selectors
    - Stitches styled() / css() usage
    - Tailwind CSS class composition
    - styled-components / Emotion wrapping Radix components
    - vanilla-extract recipe() for Radix
    - Data attribute selectors for state management
    - Animation/transition patterns
    """

    # Stitches detection (co-created with Radix UI team)
    STITCHES_IMPORT_PATTERN = re.compile(
        r"""from\s+['"]@stitches/react['"]|"""
        r"""from\s+['"]@stitches/core['"]|"""
        r"""from\s+['"]stitches\.config['"]""",
        re.MULTILINE,
    )

    STITCHES_STYLED_PATTERN = re.compile(
        r'(?:const|let|var)\s+\w+\s*=\s*styled\(\s*["\']?\w+',
        re.MULTILINE,
    )

    STITCHES_CSS_PATTERN = re.compile(
        r'(?:const|let|var)\s+\w+\s*=\s*css\(\s*\{',
        re.MULTILINE,
    )

    # CSS Modules detection
    CSS_MODULE_IMPORT = re.compile(
        r"""import\s+(\w+)\s+from\s+['"][^'"]+\.module\.(?:css|scss|sass)['"]""",
        re.MULTILINE,
    )

    # Tailwind className detection (in JSX)
    TAILWIND_CLASS_PATTERN = re.compile(
        r'className\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )

    # styled-components / Emotion
    STYLED_COMPONENTS_PATTERN = re.compile(
        r"""from\s+['"]styled-components['"]|"""
        r"""from\s+['"]@emotion/styled['"]|"""
        r"""from\s+['"]@emotion/react['"]""",
        re.MULTILINE,
    )

    # vanilla-extract
    VANILLA_EXTRACT_PATTERN = re.compile(
        r"""from\s+['"]@vanilla-extract/(?:css|recipes|sprinkles)['"]""",
        re.MULTILINE,
    )

    # Data attribute selector in CSS
    DATA_ATTR_CSS_PATTERN = re.compile(
        r"""\[data-(state|side|align|orientation|disabled|highlighted|placeholder|swipe-direction|swipe|motion)\s*(?:=\s*['"]?(\w+)['"]?)?\]""",
        re.MULTILINE,
    )

    # Data attribute selector in Stitches/Emotion/styled-components
    DATA_ATTR_JS_PATTERN = re.compile(
        r"""'&\[data-(state|side|align|orientation|disabled|highlighted|placeholder)\s*(?:=\s*"(\w+)")?\]'""",
        re.MULTILINE,
    )

    # Animation patterns for Radix
    ANIMATION_PATTERN = re.compile(
        r'(?:animation|transition|@keyframes|transform|opacity)\s*:',
        re.MULTILINE,
    )

    # Responsive patterns
    RESPONSIVE_PATTERN = re.compile(
        r'@media|@container|\bresponsive\b|breakpoint',
        re.MULTILINE | re.IGNORECASE,
    )

    # Dark mode patterns
    DARK_MODE_PATTERN = re.compile(
        r"""\.dark\s|dark:|prefers-color-scheme:\s*dark|data-theme\s*=\s*['"]dark""",
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract styling patterns from source code with Radix UI.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'style_patterns' and 'data_attributes' lists
        """
        result = {
            'style_patterns': [],
            'data_attributes': [],
        }

        if not content or not content.strip():
            return result

        # Detect styling approaches
        patterns = self._detect_style_approaches(content, file_path)
        result['style_patterns'].extend(patterns)

        # Extract data attribute usage
        attrs = self._extract_data_attributes(content, file_path)
        result['data_attributes'].extend(attrs)

        return result

    def _detect_style_approaches(
        self, content: str, file_path: str
    ) -> List[RadixStylePatternInfo]:
        """Detect which styling approaches are used with Radix UI."""
        patterns = []
        has_animation = bool(self.ANIMATION_PATTERN.search(content))
        has_responsive = bool(self.RESPONSIVE_PATTERN.search(content))
        has_dark_mode = bool(self.DARK_MODE_PATTERN.search(content))

        # Stitches
        if self.STITCHES_IMPORT_PATTERN.search(content):
            match = self.STITCHES_IMPORT_PATTERN.search(content)
            styled_count = len(self.STITCHES_STYLED_PATTERN.findall(content))
            css_count = len(self.STITCHES_CSS_PATTERN.findall(content))
            patterns.append(RadixStylePatternInfo(
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                approach='stitches',
                framework_import='@stitches/react',
                has_animation=has_animation,
                has_responsive=has_responsive,
                has_dark_mode=has_dark_mode,
                class_count=styled_count + css_count,
            ))

        # CSS Modules
        if self.CSS_MODULE_IMPORT.search(content):
            match = self.CSS_MODULE_IMPORT.search(content)
            patterns.append(RadixStylePatternInfo(
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                approach='css-modules',
                has_animation=has_animation,
                has_responsive=has_responsive,
                has_dark_mode=has_dark_mode,
            ))

        # Tailwind CSS
        tw_classes = self.TAILWIND_CLASS_PATTERN.findall(content)
        if tw_classes and any(
            any(c.startswith(p) for p in ('flex', 'grid', 'p-', 'm-', 'text-', 'bg-', 'w-', 'h-', 'rounded', 'border'))
            for cls in tw_classes
            for c in cls.split()
        ):
            patterns.append(RadixStylePatternInfo(
                file=file_path,
                line_number=1,
                approach='tailwind',
                has_animation=has_animation,
                has_responsive=has_responsive,
                has_dark_mode=has_dark_mode,
                class_count=sum(len(c.split()) for c in tw_classes),
            ))

        # styled-components / Emotion
        if self.STYLED_COMPONENTS_PATTERN.search(content):
            match = self.STYLED_COMPONENTS_PATTERN.search(content)
            approach = 'emotion' if '@emotion' in match.group(0) else 'styled-components'
            patterns.append(RadixStylePatternInfo(
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                approach=approach,
                framework_import=match.group(0).split("'")[-2] if "'" in match.group(0) else '',
                has_animation=has_animation,
                has_responsive=has_responsive,
                has_dark_mode=has_dark_mode,
            ))

        # vanilla-extract
        if self.VANILLA_EXTRACT_PATTERN.search(content):
            match = self.VANILLA_EXTRACT_PATTERN.search(content)
            patterns.append(RadixStylePatternInfo(
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                approach='vanilla-extract',
                framework_import='@vanilla-extract/css',
                has_animation=has_animation,
                has_responsive=has_responsive,
                has_dark_mode=has_dark_mode,
            ))

        return patterns

    def _extract_data_attributes(
        self, content: str, file_path: str
    ) -> List[RadixDataAttributeInfo]:
        """Extract Radix data-* attribute usage in styling."""
        attrs = []
        seen = set()

        # CSS selectors
        for match in self.DATA_ATTR_CSS_PATTERN.finditer(content):
            attr_name = f"data-{match.group(1)}"
            value = match.group(2) or ""
            key = (attr_name, value, file_path)
            if key in seen:
                continue
            seen.add(key)

            context = self._attribute_context(match.group(1), value)
            line_number = content[:match.start()].count('\n') + 1

            attrs.append(RadixDataAttributeInfo(
                attribute=attr_name,
                file=file_path,
                line_number=line_number,
                value=value,
                selector=match.group(0),
                context=context,
            ))

        # JS/CSS-in-JS selectors
        for match in self.DATA_ATTR_JS_PATTERN.finditer(content):
            attr_name = f"data-{match.group(1)}"
            value = match.group(2) or ""
            key = (attr_name, value, file_path)
            if key in seen:
                continue
            seen.add(key)

            context = self._attribute_context(match.group(1), value)
            line_number = content[:match.start()].count('\n') + 1

            attrs.append(RadixDataAttributeInfo(
                attribute=attr_name,
                file=file_path,
                line_number=line_number,
                value=value,
                selector=match.group(0),
                context=context,
            ))

        return attrs

    def _attribute_context(self, attr_type: str, value: str) -> str:
        """Determine the context of a data attribute."""
        context_map = {
            'state': 'animation' if value in ('open', 'closed') else 'interaction',
            'side': 'positioning',
            'align': 'positioning',
            'orientation': 'layout',
            'disabled': 'interaction',
            'highlighted': 'interaction',
            'placeholder': 'visibility',
            'swipe-direction': 'interaction',
            'swipe': 'interaction',
            'motion': 'animation',
        }
        return context_map.get(attr_type, 'other')
