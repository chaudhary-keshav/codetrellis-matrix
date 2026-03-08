"""
EnhancedChakraParser v1.0 - Comprehensive Chakra UI parser using all extractors.

This parser integrates all Chakra UI extractors to provide complete parsing of
Chakra UI usage across React/TypeScript source files (.jsx, .tsx, .js, .ts).
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Chakra UI-specific semantics.

Supports:
- Chakra UI v1.x (@chakra-ui/react, @chakra-ui/core,
    ChakraProvider, extendTheme, useDisclosure, useColorMode,
    framer-motion integration, CSSReset, theme-tools)
- Chakra UI v2.x (@chakra-ui/react v2, improved theme tokens,
    createMultiStyleConfigHelpers, defineStyle, defineStyleConfig,
    Stepper component, Card component, Show/Hide responsive,
    Portal improvements, system-level style props,
    chakra factory with forwardRef, Ark UI foundation,
    @chakra-ui/anatomy, @chakra-ui/styled-system,
    responsive style arrays and objects)
- Chakra UI v3.x (@chakra-ui/react v3, Ark UI architecture,
    Panda CSS engine, createSystem, defineConfig, defineRecipe,
    defineSlotRecipe, semantic tokens overhaul, conditions API,
    chakra.div factory, slot recipes, zero-runtime CSS,
    @ark-ui/react foundation, Field component replacing FormControl,
    Toaster/toaster API replacing useToast, improved TypeScript,
    token() function, virtual color, colorPalette API)

Component Detection:
- 70+ Chakra UI core components across 10 categories (layout, typography,
    forms, data-display, feedback, overlay, navigation, disclosure,
    media, utility)
- Sub-component composition (Modal.Header, Accordion.Item, Menu.Item, etc.)
- chakra() factory pattern for custom styled components
- chakra.div / chakra.span shorthand elements
- forwardRef integration with Chakra factory
- Custom wrapper components built on Chakra primitives

Theme System:
- extendTheme (v1/v2) with colors, fonts, breakpoints, components
- createSystem + defineConfig (v3) with Panda CSS foundation
- defineRecipe / defineSlotRecipe (v3 component recipes)
- Design tokens (spacing, colors, sizes, radii, shadows, etc.)
- Semantic tokens (colors with light/dark mode values)
- Color mode (light/dark, useColorMode, useColorModeValue)
- Component style overrides (baseStyle, sizes, variants, defaultProps)
- Breakpoints (custom responsive breakpoints array/object)
- Foundation keys (v3 conditions, utilities, globalCss)

Hook Patterns:
- Disclosure hooks: useDisclosure
- Color mode hooks: useColorMode, useColorModeValue
- Theme hooks: useTheme, useToken
- Media hooks: useMediaQuery, useBreakpointValue
- Clipboard hooks: useClipboard
- Form hooks: useCheckbox, useRadio, useCheckboxGroup, useRadioGroup
- Toast hooks: useToast (v1/v2)
- Animation hooks: useAnimation
- Utility hooks: useBoolean, useOutsideClick, useControllable,
    useDimensions, useMergeRefs, usePrevious, useEventListener
- Overlay hooks: usePopover, useMenu

Style System:
- Style props (100+ props: bg, color, p, m, w, h, display, etc.)
- sx prop for escape-hatch styles with theme access
- Responsive style arrays [base, sm, md, lg, xl, 2xl]
- Responsive style objects {base: ..., md: ..., lg: ...}
- Pseudo props (_hover, _active, _focus, _disabled, etc.)
- useStyleConfig / useMultiStyleConfig for component theming
- as prop for element polymorphism
- Condition-based styles (v3 _dark, _hover, _groupHover, etc.)

API Patterns:
- Form (FormControl, FormLabel, FormErrorMessage, FormHelperText,
    isRequired, isInvalid, react-hook-form/formik integration)
- Modal (controlled via useDisclosure, sizes, initialFocusRef,
    close-on-overlay, AlertDialog confirmation)
- Drawer (placement, sizes, form drawers)
- Toast (useToast v1/v2, toaster.create v3, positions, statuses)
- Menu (basic, context, option groups, nested, icons, commands)
- Tabs (controlled, fitted, lazy, variants, orientation)
- Accordion (allowMultiple, allowToggle, controlled)

Framework Ecosystem Detection (30+ patterns):
- Core: @chakra-ui/react, @chakra-ui/core, @chakra-ui/system
- Icons: @chakra-ui/icons, react-icons (common companion)
- Theme: @chakra-ui/theme, @chakra-ui/theme-tools, @chakra-ui/anatomy
- Styled: @chakra-ui/styled-system, @chakra-ui/css-reset
- Pro: @chakra-ui/pro-theme, chakra-templates
- Companion: framer-motion, @emotion/react, @emotion/styled,
    react-hook-form, formik, @saas-ui/react, chakra-react-select,
    chakra-dayzed-datepicker, @fontsource/*
- Ark UI (v3): @ark-ui/react, @ark-ui/anatomy
- Panda CSS (v3): @pandacss/dev, styled-system

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Chakra UI extractors
from .extractors.chakra import (
    ChakraComponentExtractor, ChakraComponentInfo, ChakraCustomComponentInfo,
    ChakraThemeExtractor, ChakraThemeInfo, ChakraTokenInfo,
    ChakraSemanticTokenInfo, ChakraComponentStyleInfo,
    ChakraHookExtractor, ChakraHookUsageInfo, ChakraCustomHookInfo,
    ChakraStyleExtractor, ChakraStylePropInfo, ChakraSxUsageInfo,
    ChakraResponsiveInfo,
    ChakraApiExtractor, ChakraFormPatternInfo, ChakraModalPatternInfo,
    ChakraToastPatternInfo, ChakraMenuPatternInfo,
)


@dataclass
class ChakraParseResult:
    """Complete parse result for a file with Chakra UI usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx

    # Components
    components: List[ChakraComponentInfo] = field(default_factory=list)
    custom_components: List[ChakraCustomComponentInfo] = field(default_factory=list)

    # Theme
    themes: List[ChakraThemeInfo] = field(default_factory=list)
    tokens: List[ChakraTokenInfo] = field(default_factory=list)
    semantic_tokens: List[ChakraSemanticTokenInfo] = field(default_factory=list)
    component_styles: List[ChakraComponentStyleInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[ChakraHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[ChakraCustomHookInfo] = field(default_factory=list)

    # Styles
    style_props: List[ChakraStylePropInfo] = field(default_factory=list)
    sx_usages: List[ChakraSxUsageInfo] = field(default_factory=list)
    responsive_patterns: List[ChakraResponsiveInfo] = field(default_factory=list)

    # API patterns
    forms: List[ChakraFormPatternInfo] = field(default_factory=list)
    modals: List[ChakraModalPatternInfo] = field(default_factory=list)
    toasts: List[ChakraToastPatternInfo] = field(default_factory=list)
    menus: List[ChakraMenuPatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    chakra_version: str = ""  # Detected Chakra UI version (v1, v2, v3)
    has_theme: bool = False
    has_design_tokens: bool = False
    has_semantic_tokens: bool = False
    has_dark_mode: bool = False
    has_recipes: bool = False
    has_panda_css: bool = False
    has_ark_ui: bool = False
    has_style_props: bool = False
    has_responsive: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedChakraParser:
    """
    Enhanced Chakra UI parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React parser) when Chakra UI framework
    is detected. It extracts Chakra UI-specific semantics that the
    language/React parsers cannot capture.

    Framework detection supports 30+ Chakra UI ecosystem patterns across:
    - Core (@chakra-ui/react, @chakra-ui/core, @chakra-ui/system)
    - Icons (@chakra-ui/icons, react-icons)
    - Theme (@chakra-ui/theme, @chakra-ui/theme-tools, @chakra-ui/anatomy)
    - Styled (@chakra-ui/styled-system, @chakra-ui/css-reset)
    - Pro (@chakra-ui/pro-theme, chakra-templates, @saas-ui/react)
    - Ark UI (@ark-ui/react, @ark-ui/anatomy) — v3 foundation
    - Panda CSS (@pandacss/dev, styled-system) — v3 styling

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Chakra UI ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Chakra UI ────────────────────────────────────────
        'chakra-ui': re.compile(
            r"from\s+['\"]@chakra-ui/react['/\"]|"
            r"require\(['\"]@chakra-ui/react['/\"]\)",
            re.MULTILINE
        ),
        'chakra-core': re.compile(
            r"from\s+['\"]@chakra-ui/core['/\"]",
            re.MULTILINE
        ),
        'chakra-system': re.compile(
            r"from\s+['\"]@chakra-ui/system['/\"]",
            re.MULTILINE
        ),

        # ── Icons ─────────────────────────────────────────────────
        'chakra-icons': re.compile(
            r"from\s+['\"]@chakra-ui/icons['/\"]",
            re.MULTILINE
        ),
        'react-icons': re.compile(
            r"from\s+['\"]react-icons['/\"]",
            re.MULTILINE
        ),

        # ── Theme / Styling ──────────────────────────────────────
        'chakra-theme': re.compile(
            r"from\s+['\"]@chakra-ui/theme['/\"]",
            re.MULTILINE
        ),
        'chakra-theme-tools': re.compile(
            r"from\s+['\"]@chakra-ui/theme-tools['/\"]",
            re.MULTILINE
        ),
        'chakra-anatomy': re.compile(
            r"from\s+['\"]@chakra-ui/anatomy['/\"]",
            re.MULTILINE
        ),
        'chakra-styled-system': re.compile(
            r"from\s+['\"]@chakra-ui/styled-system['/\"]",
            re.MULTILINE
        ),
        'chakra-css-reset': re.compile(
            r"from\s+['\"]@chakra-ui/css-reset['/\"]|"
            r"CSSReset",
            re.MULTILINE
        ),

        # ── Individual component packages ─────────────────────────
        'chakra-modal': re.compile(
            r"from\s+['\"]@chakra-ui/modal['/\"]",
            re.MULTILINE
        ),
        'chakra-menu': re.compile(
            r"from\s+['\"]@chakra-ui/menu['/\"]",
            re.MULTILINE
        ),
        'chakra-toast': re.compile(
            r"from\s+['\"]@chakra-ui/toast['/\"]",
            re.MULTILINE
        ),
        'chakra-layout': re.compile(
            r"from\s+['\"]@chakra-ui/layout['/\"]",
            re.MULTILINE
        ),
        'chakra-form-control': re.compile(
            r"from\s+['\"]@chakra-ui/form-control['/\"]",
            re.MULTILINE
        ),
        'chakra-spinner': re.compile(
            r"from\s+['\"]@chakra-ui/spinner['/\"]",
            re.MULTILINE
        ),

        # ── Ark UI (v3 foundation) ───────────────────────────────
        'ark-ui': re.compile(
            r"from\s+['\"]@ark-ui/react['/\"]|"
            r"from\s+['\"]@ark-ui/anatomy['/\"]",
            re.MULTILINE
        ),
        'ark-ui-anatomy': re.compile(
            r"from\s+['\"]@ark-ui/anatomy['/\"]",
            re.MULTILINE
        ),

        # ── Panda CSS (v3 styling) ───────────────────────────────
        'panda-css': re.compile(
            r"from\s+['\"]@pandacss/dev['/\"]|"
            r"from\s+['\"]styled-system/css['\"]|"
            r"from\s+['\"]styled-system/recipes['\"]|"
            r"from\s+['\"]styled-system/patterns['\"]",
            re.MULTILINE
        ),

        # ── Pro / Premium ────────────────────────────────────────
        'chakra-pro-theme': re.compile(
            r"from\s+['\"]@chakra-ui/pro-theme['/\"]",
            re.MULTILINE
        ),
        'saas-ui': re.compile(
            r"from\s+['\"]@saas-ui/react['/\"]|"
            r"from\s+['\"]@saas-ui/",
            re.MULTILINE
        ),
        'chakra-templates': re.compile(
            r"from\s+['\"]chakra-templates['/\"]",
            re.MULTILINE
        ),

        # ── Companion libraries ──────────────────────────────────
        'framer-motion': re.compile(
            r"from\s+['\"]framer-motion['/\"]|"
            r"from\s+['\"]motion/react['/\"]",
            re.MULTILINE
        ),
        'emotion-react': re.compile(
            r"from\s+['\"]@emotion/react['/\"]",
            re.MULTILINE
        ),
        'emotion-styled': re.compile(
            r"from\s+['\"]@emotion/styled['/\"]",
            re.MULTILINE
        ),
        'chakra-react-select': re.compile(
            r"from\s+['\"]chakra-react-select['/\"]",
            re.MULTILINE
        ),
        'chakra-dayzed-datepicker': re.compile(
            r"from\s+['\"]chakra-dayzed-datepicker['/\"]",
            re.MULTILINE
        ),

        # ── Form libraries ───────────────────────────────────────
        'react-hook-form': re.compile(
            r"from\s+['\"]react-hook-form['/\"]",
            re.MULTILINE
        ),
        'formik': re.compile(
            r"from\s+['\"]formik['/\"]",
            re.MULTILINE
        ),

        # ── Font sources ─────────────────────────────────────────
        'fontsource': re.compile(
            r"from\s+['\"]@fontsource/",
            re.MULTILINE
        ),

        # ── Next.js integration ──────────────────────────────────
        'chakra-next-js': re.compile(
            r"from\s+['\"]@chakra-ui/next-js['/\"]",
            re.MULTILINE
        ),
    }

    # Chakra UI version detection from import patterns and APIs
    CHAKRA_VERSION_INDICATORS = {
        # v3 indicators (Ark UI, Panda CSS, createSystem, defineConfig)
        'createSystem': 'v3',
        'defineConfig': 'v3',
        'defineRecipe': 'v3',
        'defineSlotRecipe': 'v3',
        '@ark-ui/react': 'v3',
        '@ark-ui/anatomy': 'v3',
        '@pandacss/dev': 'v3',
        'styled-system/css': 'v3',
        'styled-system/recipes': 'v3',
        'toaster.create': 'v3',
        'toaster.success': 'v3',
        'toaster.error': 'v3',
        'colorPalette': 'v3',
        'Field.Root': 'v3',
        'Field.Label': 'v3',
        'Field.ErrorText': 'v3',
        'chakra.div': 'v3',
        'chakra.span': 'v3',

        # v2 indicators (createMultiStyleConfigHelpers, Card, Show/Hide, Stepper)
        'createMultiStyleConfigHelpers': 'v2',
        'defineStyle': 'v2',
        'defineStyleConfig': 'v2',
        'Card': 'v2',
        'CardHeader': 'v2',
        'CardBody': 'v2',
        'Show': 'v2',
        'Hide': 'v2',
        'Stepper': 'v2',
        'Step': 'v2',

        # v1 indicators (CSSReset, legacy patterns)
        'CSSReset': 'v1',
        '@chakra-ui/core': 'v1',
    }

    # Priority ordering for version comparison
    VERSION_PRIORITY = {'v3': 3, 'v2': 2, 'v1': 1}

    def __init__(self):
        """Initialize the parser with all Chakra UI extractors."""
        self.component_extractor = ChakraComponentExtractor()
        self.theme_extractor = ChakraThemeExtractor()
        self.hook_extractor = ChakraHookExtractor()
        self.style_extractor = ChakraStyleExtractor()
        self.api_extractor = ChakraApiExtractor()

    def parse(self, content: str, file_path: str = "") -> ChakraParseResult:
        """
        Parse source code and extract all Chakra UI-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Chakra UI framework is detected. It extracts component usage, theme
        configuration, hook patterns, styling approaches, and API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ChakraParseResult with all extracted Chakra UI information
        """
        result = ChakraParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "tsx"
        else:
            result.file_type = "jsx"

        # ── Detect frameworks ─────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.custom_components = comp_result.get('custom_components', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.themes = theme_result.get('themes', [])
        result.tokens = theme_result.get('tokens', [])
        result.semantic_tokens = theme_result.get('semantic_tokens', [])
        result.component_styles = theme_result.get('component_styles', [])

        # ── Extract hooks ─────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hook_usages = hook_result.get('hook_usages', [])
        result.custom_hooks = hook_result.get('custom_hooks', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.style_props = style_result.get('style_props', [])
        result.sx_usages = style_result.get('sx_usages', [])
        result.responsive_patterns = style_result.get('responsive_patterns', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.forms = api_result.get('forms', [])
        result.modals = api_result.get('modals', [])
        result.toasts = api_result.get('toasts', [])
        result.menus = api_result.get('menus', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_theme = len(result.themes) > 0
        result.has_design_tokens = len(result.tokens) > 0
        result.has_semantic_tokens = len(result.semantic_tokens) > 0
        result.has_dark_mode = any(t.has_color_mode for t in result.themes)
        result.has_recipes = any(t.has_recipes for t in result.themes)
        result.has_panda_css = 'panda-css' in result.detected_frameworks
        result.has_ark_ui = any(
            fw.startswith('ark-ui') for fw in result.detected_frameworks
        )
        result.has_style_props = len(result.style_props) > 0
        result.has_responsive = len(result.responsive_patterns) > 0

        # ── Detect Chakra version ─────────────────────────────────
        result.chakra_version = self._detect_chakra_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_chakra_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Chakra UI code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Chakra UI code
        """
        if not content:
            return False

        # Check for @chakra-ui/* imports (ES module)
        if re.search(r"from\s+['\"]@chakra-ui/", content):
            return True

        # Check for @chakra-ui/* require() imports (CommonJS)
        if re.search(r"require\(['\"]@chakra-ui/", content):
            return True

        # Check for @ark-ui/react imports (Chakra v3 foundation)
        if re.search(r"from\s+['\"]@ark-ui/react['/\"]", content):
            return True

        # Check for @saas-ui imports (Chakra ecosystem)
        if re.search(r"from\s+['\"]@saas-ui/", content):
            return True

        # Check for chakra-react-select
        if re.search(r"from\s+['\"]chakra-react-select['\"]", content):
            return True

        # Check for ChakraProvider / ChakraBaseProvider
        if re.search(r'<ChakraProvider|<ChakraBaseProvider', content):
            return True

        # Check for extendTheme / createSystem (Chakra theme APIs)
        if re.search(r'extendTheme\s*\(|createSystem\s*\(', content):
            return True

        # Check for Panda CSS styled-system imports (Chakra v3)
        if re.search(r"from\s+['\"]styled-system/", content):
            return True

        # Check for defineRecipe / defineSlotRecipe (Chakra v3)
        if re.search(r'defineRecipe\s*\(|defineSlotRecipe\s*\(', content):
            return True

        # Check for chakra factory usage
        if re.search(r'chakra\.\w+|chakra\(', content):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Chakra UI ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_chakra_version(
        self, content: str, result: ChakraParseResult
    ) -> str:
        """
        Detect the Chakra UI version from imports and API patterns.

        Returns version string: 'v1', 'v2', 'v3'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.CHAKRA_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # Override: Panda CSS / Ark UI is definitive v3 indicator
        if result.has_panda_css or result.has_ark_ui:
            return 'v3'

        # Override: recipes imply v3
        if result.has_recipes:
            return 'v3'

        # Theme-based detection
        for theme in result.themes:
            if theme.chakra_version:
                v = theme.chakra_version
                v_priority = self.VERSION_PRIORITY.get(v, 0)
                if v_priority > max_priority:
                    max_priority = v_priority
                    detected_version = v

        # Default to v2 if we have Chakra usage but can't determine version
        if not detected_version and (
            result.components or result.hook_usages
        ):
            detected_version = 'v2'

        return detected_version

    def _detect_features(
        self, content: str, result: ChakraParseResult
    ) -> List[str]:
        """Detect Chakra UI features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('chakra_components')
            categories = set(
                c.category for c in result.components if c.category
            )
            for cat in sorted(categories):
                features.append(f'chakra_category_{cat}')

        if result.custom_components:
            features.append('custom_wrapped_components')

        # Theme features
        if result.has_theme:
            features.append('theme_configuration')
        if result.has_design_tokens:
            features.append('design_tokens')
        if result.has_semantic_tokens:
            features.append('semantic_tokens')
        if result.has_dark_mode:
            features.append('color_mode')
        if result.has_recipes:
            features.append('recipes')
        if result.component_styles:
            features.append('component_style_overrides')

        # Style features
        if result.has_style_props:
            features.append('style_props')
        if result.sx_usages:
            features.append('sx_prop')
        if result.has_responsive:
            features.append('responsive_patterns')

        # Panda CSS / Ark UI
        if result.has_panda_css:
            features.append('panda_css')
        if result.has_ark_ui:
            features.append('ark_ui')

        # Hook features
        if result.hook_usages:
            hook_categories = set(
                h.category for h in result.hook_usages if h.category
            )
            for cat in sorted(hook_categories):
                features.append(f'hooks_{cat}')

        # API features
        if result.forms:
            features.append('form_patterns')
            for form in result.forms:
                if form.has_validation:
                    features.append('form_validation')
                if form.integration:
                    features.append(f'form_{form.integration}')

        if result.modals:
            features.append('modal_patterns')
            modal_types = set(m.modal_type for m in result.modals)
            for mt in sorted(modal_types):
                features.append(f'{mt}_pattern')

        if result.toasts:
            features.append('toast_patterns')

        if result.menus:
            features.append('menu_patterns')

        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
