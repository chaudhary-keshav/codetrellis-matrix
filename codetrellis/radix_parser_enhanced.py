"""
EnhancedRadixParser v1.0 - Comprehensive Radix UI parser using all extractors.

This parser integrates all Radix UI extractors to provide complete parsing of
Radix UI usage across React/TypeScript source files (.jsx, .tsx, .js, .ts)
and CSS/styling files.

It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Radix UI-specific semantics. Radix UI components are
installed as separate npm packages (@radix-ui/react-*), unlike shadcn/ui
which copies components into the project.

Supports:
- Radix Primitives v0.x (initial release — individual @radix-ui/react-* packages)
    Pre-1.0 API with breaking changes between minor versions,
    compound component pattern (Root/Trigger/Content/etc.),
    initial accessibility implementation, basic data attributes

- Radix Primitives v1.x (stable — current major version)
    Stable API surface, 30+ primitives, asChild prop composition,
    data-state/data-side/data-align attributes, forceMount for animations,
    Portal rendering, FocusScope/DismissableLayer,
    keyboard navigation (arrow keys, Home/End, typeahead),
    ARIA compliance, RTL support (DirectionProvider)

- Radix Themes v1.x (initial styled component library)
    @radix-ui/themes package, <Theme> provider, 28 color scales (12 steps),
    appearance (light/dark/inherit), accentColor, grayColor,
    panelBackground (solid/translucent), radius, scaling

- Radix Themes v2.x (improved component API)
    New components (SegmentedControl, Inset, Spinner, DataList),
    improved responsive props, better TypeScript types

- Radix Themes v3.x-v4.x (latest — layout primitives + new components)
    Layout primitives (Box, Flex, Grid, Container, Section),
    ThemePanel for interactive theme configuration,
    improved SSR support, React Server Components compatibility,
    CSS Layers, improved dark mode

Component Detection (30+ primitives + 50+ themes):
Primitives:
- Overlay: Dialog, AlertDialog, Popover, Tooltip, HoverCard,
    ContextMenu, DropdownMenu, Menubar, Toast
- Forms: Checkbox, RadioGroup, Select, Slider, Switch, ToggleGroup,
    Toggle, Form, Label
- Layout: Accordion, Collapsible, NavigationMenu, Tabs, Toolbar
- Content: AspectRatio, Avatar, Progress, ScrollArea, Separator
- Utility: Slot, VisuallyHidden, Portal, Presence, FocusScope

Themes:
- Layout: Box, Flex, Grid, Container, Section
- Typography: Text, Heading, Code, Blockquote, Em, Kbd, Link, Quote, Strong
- Forms: Button, IconButton, TextField, TextArea, Select, Checkbox,
    RadioGroup, Switch, Slider, SegmentedControl
- Data Display: Badge, Card, Table, DataList, Avatar, Callout, Inset
- Feedback: Progress, Skeleton, Spinner
- Overlay: Dialog, AlertDialog, Popover, Tooltip, HoverCard,
    ContextMenu, DropdownMenu
- Navigation: Tabs, TabNav

Data Attributes (state management):
- data-state: open, closed, active, inactive, checked, unchecked, indeterminate
- data-side: top, right, bottom, left
- data-align: start, center, end
- data-orientation: horizontal, vertical
- data-disabled, data-highlighted, data-placeholder
- data-swipe, data-swipe-direction, data-motion

Framework Ecosystem Detection (30+ patterns):
- Core: @radix-ui/react-* (all 30+ primitives)
- Themes: @radix-ui/themes, @radix-ui/themes/styles.css
- Colors: @radix-ui/colors (28 scales)
- Icons: @radix-ui/react-icons (500+ icons)
- Styling: @stitches/react (co-created with Radix team), tailwind-merge,
    styled-components, @emotion/styled, @vanilla-extract/css
- Animation: framer-motion, react-spring, motion
- Utilities: @radix-ui/react-slot, @radix-ui/react-presence,
    @radix-ui/react-compose-refs, @radix-ui/react-use-controllable-state

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Radix UI extractors
from .extractors.radix import (
    RadixComponentExtractor, RadixComponentInfo, RadixThemesComponentInfo,
    RadixPrimitiveExtractor, RadixPrimitiveInfo, RadixSlotInfo,
    RadixThemeExtractor, RadixThemeConfigInfo, RadixColorScaleInfo,
    RadixStyleExtractor, RadixStylePatternInfo, RadixDataAttributeInfo,
    RadixApiExtractor, RadixCompositionPatternInfo,
    RadixControlledPatternInfo, RadixPortalPatternInfo,
)


@dataclass
class RadixParseResult:
    """Complete parse result for a file with Radix UI usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, ts, js, css

    # Components (primitives)
    components: List[RadixComponentInfo] = field(default_factory=list)

    # Themes components
    themes_components: List[RadixThemesComponentInfo] = field(default_factory=list)

    # Primitives (low-level)
    primitives: List[RadixPrimitiveInfo] = field(default_factory=list)
    slots: List[RadixSlotInfo] = field(default_factory=list)

    # Theme configuration
    theme_configs: List[RadixThemeConfigInfo] = field(default_factory=list)
    color_scales: List[RadixColorScaleInfo] = field(default_factory=list)

    # Styling
    style_patterns: List[RadixStylePatternInfo] = field(default_factory=list)
    data_attributes: List[RadixDataAttributeInfo] = field(default_factory=list)

    # API / Composition
    compositions: List[RadixCompositionPatternInfo] = field(default_factory=list)
    controlled_patterns: List[RadixControlledPatternInfo] = field(default_factory=list)
    portal_patterns: List[RadixPortalPatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    radix_version: str = ""  # Detected version (v0, v1 for primitives; themes-v1..v4)
    has_primitives: bool = False
    has_themes: bool = False
    has_colors: bool = False
    has_icons: bool = False
    has_slot: bool = False
    has_portal: bool = False
    has_dark_mode: bool = False
    has_animation: bool = False
    has_stitches: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedRadixParser:
    """
    Enhanced Radix UI parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React/shadcn parsers) when Radix UI
    is detected. It extracts Radix UI-specific semantics that the
    language parsers cannot capture.

    Framework detection supports 30+ Radix UI ecosystem patterns.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Radix UI ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Radix Primitives ─────────────────────────────────────
        'radix-primitives': re.compile(
            r"""from\s+['"]@radix-ui/react-(?!icons|themes)""",
            re.MULTILINE,
        ),

        # ── Radix Themes ─────────────────────────────────────────
        'radix-themes': re.compile(
            r"""from\s+['"]@radix-ui/themes['"]""",
            re.MULTILINE,
        ),
        'radix-themes-css': re.compile(
            r"""(?:import|@import)\s+['"]@radix-ui/themes/styles\.css['"]""",
            re.MULTILINE,
        ),

        # ── Radix Colors ─────────────────────────────────────────
        'radix-colors': re.compile(
            r"""from\s+['"]@radix-ui/colors/""",
            re.MULTILINE,
        ),

        # ── Radix Icons ──────────────────────────────────────────
        'radix-icons': re.compile(
            r"""from\s+['"]@radix-ui/react-icons['"]""",
            re.MULTILINE,
        ),

        # ── Individual primitives (top 20 most-used) ─────────────
        'radix-dialog': re.compile(
            r"""from\s+['"]@radix-ui/react-dialog['"]""",
            re.MULTILINE,
        ),
        'radix-alert-dialog': re.compile(
            r"""from\s+['"]@radix-ui/react-alert-dialog['"]""",
            re.MULTILINE,
        ),
        'radix-popover': re.compile(
            r"""from\s+['"]@radix-ui/react-popover['"]""",
            re.MULTILINE,
        ),
        'radix-tooltip': re.compile(
            r"""from\s+['"]@radix-ui/react-tooltip['"]""",
            re.MULTILINE,
        ),
        'radix-dropdown-menu': re.compile(
            r"""from\s+['"]@radix-ui/react-dropdown-menu['"]""",
            re.MULTILINE,
        ),
        'radix-context-menu': re.compile(
            r"""from\s+['"]@radix-ui/react-context-menu['"]""",
            re.MULTILINE,
        ),
        'radix-menubar': re.compile(
            r"""from\s+['"]@radix-ui/react-menubar['"]""",
            re.MULTILINE,
        ),
        'radix-select': re.compile(
            r"""from\s+['"]@radix-ui/react-select['"]""",
            re.MULTILINE,
        ),
        'radix-accordion': re.compile(
            r"""from\s+['"]@radix-ui/react-accordion['"]""",
            re.MULTILINE,
        ),
        'radix-tabs': re.compile(
            r"""from\s+['"]@radix-ui/react-tabs['"]""",
            re.MULTILINE,
        ),
        'radix-checkbox': re.compile(
            r"""from\s+['"]@radix-ui/react-checkbox['"]""",
            re.MULTILINE,
        ),
        'radix-radio-group': re.compile(
            r"""from\s+['"]@radix-ui/react-radio-group['"]""",
            re.MULTILINE,
        ),
        'radix-switch': re.compile(
            r"""from\s+['"]@radix-ui/react-switch['"]""",
            re.MULTILINE,
        ),
        'radix-slider': re.compile(
            r"""from\s+['"]@radix-ui/react-slider['"]""",
            re.MULTILINE,
        ),
        'radix-toggle': re.compile(
            r"""from\s+['"]@radix-ui/react-toggle['"]""",
            re.MULTILINE,
        ),
        'radix-toggle-group': re.compile(
            r"""from\s+['"]@radix-ui/react-toggle-group['"]""",
            re.MULTILINE,
        ),
        'radix-avatar': re.compile(
            r"""from\s+['"]@radix-ui/react-avatar['"]""",
            re.MULTILINE,
        ),
        'radix-hover-card': re.compile(
            r"""from\s+['"]@radix-ui/react-hover-card['"]""",
            re.MULTILINE,
        ),
        'radix-navigation-menu': re.compile(
            r"""from\s+['"]@radix-ui/react-navigation-menu['"]""",
            re.MULTILINE,
        ),
        'radix-toast': re.compile(
            r"""from\s+['"]@radix-ui/react-toast['"]""",
            re.MULTILINE,
        ),

        # ── Utility primitives ───────────────────────────────────
        'radix-slot': re.compile(
            r"""from\s+['"]@radix-ui/react-slot['"]""",
            re.MULTILINE,
        ),
        'radix-visually-hidden': re.compile(
            r"""from\s+['"]@radix-ui/react-visually-hidden['"]""",
            re.MULTILINE,
        ),
        'radix-portal': re.compile(
            r"""from\s+['"]@radix-ui/react-portal['"]""",
            re.MULTILINE,
        ),
        'radix-presence': re.compile(
            r"""from\s+['"]@radix-ui/react-presence['"]""",
            re.MULTILINE,
        ),
        'radix-focus-scope': re.compile(
            r"""from\s+['"]@radix-ui/react-focus-scope['"]""",
            re.MULTILINE,
        ),

        # ── Styling frameworks commonly used with Radix ──────────
        'stitches': re.compile(
            r"""from\s+['"]@stitches/react['"]|from\s+['"]@stitches/core['"]""",
            re.MULTILINE,
        ),
        'tailwind-merge': re.compile(
            r"""from\s+['"]tailwind-merge['"]""",
            re.MULTILINE,
        ),
        'clsx': re.compile(
            r"""from\s+['"]clsx['"]""",
            re.MULTILINE,
        ),
        'class-variance-authority': re.compile(
            r"""from\s+['"]class-variance-authority['"]""",
            re.MULTILINE,
        ),
        'vanilla-extract': re.compile(
            r"""from\s+['"]@vanilla-extract/css['"]|from\s+['"]@vanilla-extract/recipes['"]""",
            re.MULTILINE,
        ),

        # ── Animation ────────────────────────────────────────────
        'framer-motion': re.compile(
            r"""from\s+['"]framer-motion['"]""",
            re.MULTILINE,
        ),
        'react-spring': re.compile(
            r"""from\s+['"]@react-spring/web['"]|from\s+['"]react-spring['"]""",
            re.MULTILINE,
        ),
    }

    # Radix version detection indicators
    RADIX_VERSION_INDICATORS = {
        # Radix Themes v4 indicators
        'ThemePanel': 'themes-v4',
        'DataList': 'themes-v3',
        'SegmentedControl': 'themes-v2',
        'Spinner': 'themes-v2',
        'Inset': 'themes-v3',

        # Radix Themes v1 indicators
        '@radix-ui/themes': 'themes-v1',

        # Radix Primitives v1 (stable)
        'asChild': 'v1',
        'forceMount': 'v1',
        'data-state': 'v1',
        '.Root': 'v1',

        # Radix Primitives v0 (pre-stable)
        'as={': 'v0',  # Old polymorphic prop (replaced by asChild)
    }

    VERSION_PRIORITY = {
        'themes-v4': 8, 'themes-v3': 7, 'themes-v2': 6, 'themes-v1': 5,
        'v1': 2, 'v0': 1,
    }

    def __init__(self):
        """Initialize the parser with all Radix UI extractors."""
        self.component_extractor = RadixComponentExtractor()
        self.primitive_extractor = RadixPrimitiveExtractor()
        self.theme_extractor = RadixThemeExtractor()
        self.style_extractor = RadixStyleExtractor()
        self.api_extractor = RadixApiExtractor()

    def parse(self, content: str, file_path: str = "") -> RadixParseResult:
        """
        Parse source code and extract all Radix UI-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            RadixParseResult with all extracted Radix UI information
        """
        result = RadixParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        normalized = file_path.replace('\\', '/')
        if normalized.endswith('.tsx'):
            result.file_type = "tsx"
        elif normalized.endswith('.jsx'):
            result.file_type = "jsx"
        elif normalized.endswith('.ts'):
            result.file_type = "ts"
        elif normalized.endswith('.js') or normalized.endswith('.mjs') or normalized.endswith('.cjs'):
            result.file_type = "js"
        elif normalized.endswith('.css'):
            result.file_type = "css"
        else:
            result.file_type = "tsx"

        # ── Detect frameworks ─────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        if result.file_type not in ('css',):
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])
            result.themes_components = comp_result.get('themes_components', [])

        # ── Extract primitives ────────────────────────────────────
        if result.file_type not in ('css',):
            prim_result = self.primitive_extractor.extract(content, file_path)
            result.primitives = prim_result.get('primitives', [])
            result.slots = prim_result.get('slots', [])

        # ── Extract theme configuration ──────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.theme_configs = theme_result.get('theme_configs', [])
        result.color_scales = theme_result.get('color_scales', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.style_patterns = style_result.get('style_patterns', [])
        result.data_attributes = style_result.get('data_attributes', [])

        # ── Extract API patterns ──────────────────────────────────
        if result.file_type not in ('css',):
            api_result = self.api_extractor.extract(content, file_path)
            result.compositions = api_result.get('compositions', [])
            result.controlled_patterns = api_result.get('controlled_patterns', [])
            result.portal_patterns = api_result.get('portal_patterns', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_primitives = len(result.components) > 0
        result.has_themes = len(result.themes_components) > 0
        result.has_colors = len(result.color_scales) > 0
        result.has_icons = 'radix-icons' in result.detected_frameworks
        result.has_slot = any(s.name == 'Slot' for s in result.slots) or \
            any(p.primitive_type == 'slot' for p in result.primitives)
        result.has_portal = any(c.is_portal for c in result.components) or \
            len(result.portal_patterns) > 0
        result.has_dark_mode = any(
            tc.appearance in ('dark', 'inherit') for tc in result.theme_configs
        ) or any(sp.has_dark_mode for sp in result.style_patterns)
        result.has_animation = any(sp.has_animation for sp in result.style_patterns) or \
            any(pp.animation_library for pp in result.portal_patterns)
        result.has_stitches = 'stitches' in result.detected_frameworks

        # ── Detect Radix version ──────────────────────────────────
        result.radix_version = self._detect_radix_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_radix_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Radix UI code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Radix UI code
        """
        if not content:
            return False

        # Check for any @radix-ui import
        if re.search(r"""from\s+['"]@radix-ui/""", content):
            return True

        # Check for Radix Themes CSS import
        if re.search(r"""@import\s+['"]@radix-ui/themes""", content):
            return True

        # Check for Radix data attributes in CSS
        if re.search(r'\[data-(?:state|side|align|orientation)\s*=', content):
            # Only if also has Radix-like selectors
            if re.search(r'(?:Dialog|Popover|Tooltip|Accordion|Select)\w*', content):
                return True

        # Check for Stitches + Radix patterns
        if (re.search(r"""from\s+['"]@stitches/""", content) and
                re.search(r'data-state|asChild|\.Root|\.Trigger|\.Content', content)):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Radix UI ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_radix_version(
        self, content: str, result: RadixParseResult
    ) -> str:
        """
        Detect the Radix UI version from imports and patterns.

        Returns version string: 'v0', 'v1', 'themes-v1', 'themes-v2', 'themes-v3', 'themes-v4'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.RADIX_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # Default to v1 if we have primitives but can't determine version
        if not detected_version and result.has_primitives:
            detected_version = 'v1'

        # If Themes detected, ensure themes version
        if result.has_themes and not detected_version.startswith('themes-'):
            detected_version = 'themes-v1'

        return detected_version

    def _detect_features(
        self, content: str, result: RadixParseResult
    ) -> List[str]:
        """Detect Radix UI features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('radix_primitives')
            categories = set(
                c.category for c in result.components if c.category
            )
            for cat in sorted(categories):
                features.append(f'radix_category_{cat}')

        if result.themes_components:
            features.append('radix_themes')
            categories = set(
                c.category for c in result.themes_components if c.category
            )
            for cat in sorted(categories):
                features.append(f'themes_category_{cat}')

        # Primitive features
        if result.primitives:
            for prim in result.primitives:
                features.append(f'primitive_{prim.primitive_type}')

        # Theme features
        if result.theme_configs:
            features.append('theme_provider')
            if any(tc.is_nested for tc in result.theme_configs):
                features.append('nested_theme')
            if any(tc.has_theme_panel for tc in result.theme_configs):
                features.append('theme_panel')

        if result.has_colors:
            features.append('radix_colors')

        # Style features
        if result.style_patterns:
            for sp in result.style_patterns:
                features.append(f'styling_{sp.approach}')

        if result.data_attributes:
            features.append('data_attributes')

        # API features
        if result.has_slot:
            features.append('slot_composition')
        if result.has_portal:
            features.append('portal_rendering')
        if result.has_dark_mode:
            features.append('dark_mode')
        if result.has_animation:
            features.append('animation_integration')
        if result.has_stitches:
            features.append('stitches_styling')
        if result.has_icons:
            features.append('radix_icons')

        if result.controlled_patterns:
            has_controlled = any(cp.is_controlled for cp in result.controlled_patterns)
            has_uncontrolled = any(not cp.is_controlled for cp in result.controlled_patterns)
            if has_controlled:
                features.append('controlled_state')
            if has_uncontrolled:
                features.append('uncontrolled_state')

        if result.compositions:
            features.append('compound_components')

        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
