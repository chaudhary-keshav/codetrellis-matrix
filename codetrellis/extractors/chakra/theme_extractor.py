"""
Chakra UI Theme Extractor for CodeTrellis

Extracts Chakra UI theme configuration from React/TypeScript source code.
Covers:
- extendTheme (v1/v2) and createSystem/defineConfig (v3)
- Color mode configuration (light/dark/system)
- Color tokens, spacing tokens, typography tokens
- Semantic tokens (v2+)
- Component style overrides (baseStyle, variants, sizes, defaultProps)
- Responsive breakpoints
- Custom theme foundations (colors, fonts, fontSizes, space, sizes)
- Recipes and slot recipes (v3)
- Layer styles and text styles

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChakraThemeInfo:
    """Information about a Chakra UI theme configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    method: str = ""             # extendTheme, createSystem, defineConfig, defineTheme
    chakra_version: str = ""     # v1, v2, v3
    has_color_mode: bool = False
    has_semantic_tokens: bool = False
    has_component_styles: bool = False
    has_custom_breakpoints: bool = False
    has_custom_colors: bool = False
    has_custom_fonts: bool = False
    has_recipes: bool = False    # v3 recipes
    foundation_keys: List[str] = field(default_factory=list)  # colors, fonts, sizes, etc.
    component_overrides: List[str] = field(default_factory=list)  # Button, Input, etc.
    token_count: int = 0


@dataclass
class ChakraTokenInfo:
    """Information about a Chakra UI design token."""
    token_name: str
    file: str = ""
    line_number: int = 0
    token_type: str = ""         # color, spacing, typography, size, border, shadow, semantic
    value: str = ""
    is_semantic: bool = False
    category: str = ""           # foundation, semantic, custom


@dataclass
class ChakraSemanticTokenInfo:
    """Information about a Chakra UI semantic token."""
    token_name: str
    file: str = ""
    line_number: int = 0
    light_value: str = ""
    dark_value: str = ""
    token_type: str = ""         # colors, shadows, borders, etc.


@dataclass
class ChakraComponentStyleInfo:
    """Information about a Chakra UI component style override."""
    component_name: str
    file: str = ""
    line_number: int = 0
    has_base_style: bool = False
    has_variants: bool = False
    has_sizes: bool = False
    has_default_props: bool = False
    is_recipe: bool = False      # v3 recipe / slot recipe
    variants: List[str] = field(default_factory=list)
    sizes: List[str] = field(default_factory=list)


class ChakraThemeExtractor:
    """
    Extracts Chakra UI theme configuration from source code.

    Detects:
    - extendTheme / createSystem / defineConfig / defineTheme calls
    - Color mode configuration
    - Token definitions (colors, spacing, typography, etc.)
    - Semantic tokens
    - Component style overrides
    - Custom breakpoints
    - Recipes (v3)
    """

    # Theme creation patterns
    EXTEND_THEME_PATTERN = re.compile(
        r'(?:const|let|var|export\s+(?:const|default))\s+(\w+)\s*=\s*extendTheme\s*\(',
        re.MULTILINE
    )

    CREATE_SYSTEM_PATTERN = re.compile(
        r'(?:const|let|var|export\s+(?:const|default))\s+(\w+)\s*=\s*createSystem\s*\(',
        re.MULTILINE
    )

    DEFINE_CONFIG_PATTERN = re.compile(
        r'(?:const|let|var|export\s+(?:const|default))\s+(\w+)\s*=\s*defineConfig\s*\(',
        re.MULTILINE
    )

    DEFINE_THEME_PATTERN = re.compile(
        r'(?:const|let|var|export\s+(?:const|default))\s+(\w+)\s*=\s*defineTheme\s*\(',
        re.MULTILINE
    )

    # Color mode pattern
    COLOR_MODE_PATTERN = re.compile(
        r'(?:initialColorMode|colorMode|useColorMode|ColorModeProvider|'
        r'useColorModeValue|toggleColorMode|setColorMode)',
        re.MULTILINE
    )

    # Semantic tokens pattern
    SEMANTIC_TOKENS_PATTERN = re.compile(
        r'semanticTokens\s*:\s*\{',
        re.MULTILINE
    )

    # Component styles pattern
    COMPONENT_STYLES_PATTERN = re.compile(
        r'components\s*:\s*\{',
        re.MULTILINE
    )

    # Foundation keys detection
    FOUNDATION_KEYS_PATTERN = re.compile(
        r'\b(colors|fonts|fontSizes|fontWeights|lineHeights|letterSpacings|'
        r'space|sizes|radii|shadows|borders|breakpoints|zIndices|'
        r'transition|blur|config|styles|layerStyles|textStyles)\s*:',
        re.MULTILINE
    )

    # Component name in overrides
    COMPONENT_OVERRIDE_PATTERN = re.compile(
        r'(\w+)\s*:\s*\{[^}]*(?:baseStyle|variants|sizes|defaultProps)',
        re.MULTILINE
    )

    # Recipe pattern (v3)
    RECIPE_PATTERN = re.compile(
        r'(?:defineRecipe|defineSlotRecipe)\s*\(',
        re.MULTILINE
    )

    # Breakpoint override
    BREAKPOINT_PATTERN = re.compile(
        r'breakpoints\s*:\s*\{',
        re.MULTILINE
    )

    # Custom color definition
    CUSTOM_COLOR_PATTERN = re.compile(
        r'colors\s*:\s*\{',
        re.MULTILINE
    )

    # Font definition
    FONT_PATTERN = re.compile(
        r'fonts\s*:\s*\{',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Chakra UI theme configuration from source code."""
        result = {
            'themes': [],
            'tokens': [],
            'semantic_tokens': [],
            'component_styles': [],
        }

        if not content or not content.strip():
            return result

        # Detect theme creation
        theme_patterns = [
            (self.EXTEND_THEME_PATTERN, 'extendTheme', 'v2'),
            (self.CREATE_SYSTEM_PATTERN, 'createSystem', 'v3'),
            (self.DEFINE_CONFIG_PATTERN, 'defineConfig', 'v3'),
            (self.DEFINE_THEME_PATTERN, 'defineTheme', 'v2'),
        ]

        for pattern, method, version in theme_patterns:
            for match in pattern.finditer(content):
                name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Extract theme context (up to 3000 chars after theme start)
                theme_context = content[match.start():match.start() + 3000]

                # Detect features
                foundation_keys = [
                    m.group(1) for m in self.FOUNDATION_KEYS_PATTERN.finditer(theme_context)
                ]
                has_color_mode = bool(self.COLOR_MODE_PATTERN.search(theme_context))
                has_semantic = bool(self.SEMANTIC_TOKENS_PATTERN.search(theme_context))
                has_comp_styles = bool(self.COMPONENT_STYLES_PATTERN.search(theme_context))
                has_breakpoints = bool(self.BREAKPOINT_PATTERN.search(theme_context))
                has_colors = bool(self.CUSTOM_COLOR_PATTERN.search(theme_context))
                has_fonts = bool(self.FONT_PATTERN.search(theme_context))
                has_recipes = bool(self.RECIPE_PATTERN.search(theme_context))

                # Extract component override names
                comp_overrides = list(set(
                    m.group(1) for m in self.COMPONENT_OVERRIDE_PATTERN.finditer(theme_context)
                ))

                theme_info = ChakraThemeInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    method=method,
                    chakra_version=version,
                    has_color_mode=has_color_mode,
                    has_semantic_tokens=has_semantic,
                    has_component_styles=has_comp_styles,
                    has_custom_breakpoints=has_breakpoints,
                    has_custom_colors=has_colors,
                    has_custom_fonts=has_fonts,
                    has_recipes=has_recipes,
                    foundation_keys=list(set(foundation_keys)),
                    component_overrides=comp_overrides[:20],
                    token_count=len(foundation_keys),
                )
                result['themes'].append(theme_info)

        # Detect standalone color mode
        if self.COLOR_MODE_PATTERN.search(content) and not result['themes']:
            for match in self.COLOR_MODE_PATTERN.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                token_info = ChakraTokenInfo(
                    token_name=match.group(0),
                    file=file_path,
                    line_number=line_num,
                    token_type='color-mode',
                    category='utility',
                )
                result['tokens'].append(token_info)
                break  # Only log one instance

        # Detect semantic tokens
        for match in self.SEMANTIC_TOKENS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Find token names after semanticTokens: {
            context = content[match.end():match.end() + 1500]
            # Match both simple word keys and quoted dotted keys like 'bg.surface'
            token_names = re.findall(r"""(?:['"]([^'"]+)['"]|(\w+))\s*:\s*\{""", context)
            for groups in token_names[:20]:
                tname = groups[0] or groups[1]
                # Skip structural keys but allow category keys like 'colors'
                if tname in ('default', '_dark', '_light'):
                    continue
                sem_info = ChakraSemanticTokenInfo(
                    token_name=tname,
                    file=file_path,
                    line_number=line_num,
                    token_type='semantic',
                )
                result['semantic_tokens'].append(sem_info)

        # Detect component style overrides
        for match in self.COMPONENT_OVERRIDE_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            comp_style = ChakraComponentStyleInfo(
                component_name=comp_name,
                file=file_path,
                line_number=line_num,
                has_base_style='baseStyle' in context,
                has_variants='variants' in context,
                has_sizes='sizes' in context,
                has_default_props='defaultProps' in context,
            )

            # Extract variant names
            variant_matches = re.findall(r'variants\s*:\s*\{([^}]+)', context)
            if variant_matches:
                comp_style.variants = re.findall(r'(\w+)\s*:', variant_matches[0])[:10]

            # Extract size names
            size_matches = re.findall(r'sizes\s*:\s*\{([^}]+)', context)
            if size_matches:
                comp_style.sizes = re.findall(r'(\w+)\s*:', size_matches[0])[:10]

            result['component_styles'].append(comp_style)

        # Detect standalone recipe definitions (v3: defineRecipe / defineSlotRecipe)
        STANDALONE_RECIPE = re.compile(
            r'(?:const|let|var|export\s+(?:const|default))\s+(\w+)\s*=\s*'
            r'(defineRecipe|defineSlotRecipe)\s*\(',
            re.MULTILINE
        )
        for match in STANDALONE_RECIPE.finditer(content):
            recipe_name = match.group(1)
            recipe_method = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 1000]

            comp_style = ChakraComponentStyleInfo(
                component_name=recipe_name,
                file=file_path,
                line_number=line_num,
                has_base_style='base' in context or 'baseStyle' in context,
                has_variants='variants' in context,
                has_sizes='sizes' in context,
                has_default_props='defaultProps' in context,
                is_recipe=True,
            )

            # Extract variant names
            variant_matches = re.findall(r'variants\s*:\s*\{([^}]+)', context)
            if variant_matches:
                comp_style.variants = re.findall(r'(\w+)\s*:', variant_matches[0])[:10]

            result['component_styles'].append(comp_style)

        return result
