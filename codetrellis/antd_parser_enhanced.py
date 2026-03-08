"""
EnhancedAntdParser v1.0 - Comprehensive Ant Design parser using all extractors.

This parser integrates all Ant Design extractors to provide complete parsing of
Ant Design usage across React/TypeScript source files (.jsx, .tsx, .js, .ts).
It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting Ant Design-specific semantics.

Supports:
- Ant Design v1.x (legacy antd imports)
- Ant Design v2.x (antd@2, basic component set)
- Ant Design v3.x (antd@3, Less variables, babel-plugin-import,
    Icon component, Form.create HOC, LocaleProvider)
- Ant Design v4.x (antd@4, @ant-design/icons, hooks-based Form,
    Form.useForm, useForm, removed Form.create, ConfigProvider,
    Less variable customization, tree-shaking support,
    Virtual scroll Table, new DatePicker based on dayjs)
- Ant Design v5.x (antd@5, CSS-in-JS with @ant-design/cssinjs,
    Design Tokens (Seed/Map/Alias), ConfigProvider theme prop,
    dark/compact algorithms, component-level token overrides,
    CSS Variables mode (v5.12+), App component with useApp hook,
    removal of Less in favor of CSS-in-JS, antd-style library,
    Flex component, QRCode, Tour, Watermark, FloatButton,
    ColorPicker, improved Form with useWatch/useFormInstance)

Component Detection:
- 80+ Ant Design core components across 6 categories (general, layout,
    navigation, data-entry, data-display, feedback)
- Ant Design Pro components (ProTable, ProForm, ProLayout, ProCard,
    ProDescriptions, ProList, 30+ Pro form fields)
- Sub-component composition (Form.Item, Menu.SubMenu, Table.Column, etc.)
- Custom wrapper components built on antd
- Tree-shaking import patterns (antd/es/*, antd/lib/*)

Theme System:
- ConfigProvider with theme prop (v5+)
- Design Tokens: Seed tokens, Map tokens, Alias tokens
- Algorithms: darkAlgorithm, compactAlgorithm, defaultAlgorithm
- Component-level token customization
- CSS Variables mode (v5.12+)
- Less variable overrides (v3/v4): @primary-color, @font-size-base, etc.
- modifyVars in webpack/craco/umi config
- antd-style createStyles integration

Hook Patterns:
- App hooks: useApp (unified message/notification/modal)
- Form hooks: useForm, useFormInstance, useWatch
- Theme hooks: useToken
- Layout hooks: useBreakpoint (Grid.useBreakpoint)
- Feedback hooks: useMessage, useNotification, useModal
- Pro hooks: useModel, useRequest, useIntl, useAccess

Style System:
- CSS-in-JS via antd-style createStyles (v5+)
- Design token access in styled functions
- Less/CSS module imports for antd overrides
- className / rootClassName / popupClassName overrides
- styled-components wrapping antd components
- CSS Variables mode (v5.12+)

API Patterns:
- Table/ProTable (columns, sorting, filtering, pagination, row selection,
    expandable rows, server-side data, virtual scroll)
- Form (Form.Item rules, layouts, validation, dependencies, dynamic fields)
- Modal (confirm, info, success, error, warning, async close)
- Drawer (form drawers, detail drawers, nested drawers)
- Menu (horizontal, vertical, inline, sidebar, collapsible)

Framework Ecosystem Detection (40+ patterns):
- Core: antd, @ant-design/icons, @ant-design/cssinjs
- Pro: @ant-design/pro-components, @ant-design/pro-table,
       @ant-design/pro-form, @ant-design/pro-layout,
       @ant-design/pro-card, @ant-design/pro-list,
       @ant-design/pro-descriptions, @ant-design/pro-field
- Charts: @ant-design/charts, @ant-design/plots
- Maps: @ant-design/maps
- Mobile: antd-mobile
- Style: antd-style, @ant-design/cssinjs
- Compat: @ant-design/compatible (v3→v4 migration)
- Utils: @ant-design/colors, antd-dayjs-webpack-plugin
- Companion: umi, dumi, @umijs/max, ahooks, @ant-design/icons-svg
- Legacy: babel-plugin-import, less-loader modifyVars

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Ant Design extractors
from .extractors.antd import (
    AntdComponentExtractor, AntdComponentInfo, AntdCustomComponentInfo,
    AntdProComponentInfo,
    AntdThemeExtractor, AntdThemeInfo, AntdTokenInfo,
    AntdLessVariableInfo, AntdComponentTokenInfo,
    AntdHookExtractor, AntdHookUsageInfo, AntdCustomHookInfo,
    AntdStyleExtractor, AntdCSSInJSInfo, AntdLessStyleInfo,
    AntdStyleOverrideInfo,
    AntdApiExtractor, AntdTableInfo, AntdFormPatternInfo,
    AntdModalPatternInfo, AntdMenuPatternInfo,
)


@dataclass
class AntdParseResult:
    """Complete parse result for a file with Ant Design usage."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx

    # Components
    components: List[AntdComponentInfo] = field(default_factory=list)
    custom_components: List[AntdCustomComponentInfo] = field(default_factory=list)
    pro_components: List[AntdProComponentInfo] = field(default_factory=list)

    # Theme
    themes: List[AntdThemeInfo] = field(default_factory=list)
    tokens: List[AntdTokenInfo] = field(default_factory=list)
    less_variables: List[AntdLessVariableInfo] = field(default_factory=list)
    component_tokens: List[AntdComponentTokenInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[AntdHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[AntdCustomHookInfo] = field(default_factory=list)

    # Styles
    css_in_js: List[AntdCSSInJSInfo] = field(default_factory=list)
    less_styles: List[AntdLessStyleInfo] = field(default_factory=list)
    style_overrides: List[AntdStyleOverrideInfo] = field(default_factory=list)

    # API patterns
    tables: List[AntdTableInfo] = field(default_factory=list)
    forms: List[AntdFormPatternInfo] = field(default_factory=list)
    modals: List[AntdModalPatternInfo] = field(default_factory=list)
    menus: List[AntdMenuPatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    antd_version: str = ""  # Detected Ant Design version (v1, v2, v3, v4, v5)
    has_pro_components: bool = False
    has_theme: bool = False
    has_css_in_js: bool = False
    has_less_theming: bool = False
    has_dark_mode: bool = False
    has_css_variables: bool = False
    has_design_tokens: bool = False
    has_antd_mobile: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedAntdParser:
    """
    Enhanced Ant Design parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React parser) when Ant Design framework
    is detected. It extracts antd-specific semantics that the language/React
    parsers cannot capture.

    Framework detection supports 40+ Ant Design ecosystem patterns across:
    - Core (antd, @ant-design/icons, @ant-design/cssinjs)
    - Pro (@ant-design/pro-components, @ant-design/pro-table, etc.)
    - Charts (@ant-design/charts, @ant-design/plots)
    - Mobile (antd-mobile)
    - Style (antd-style, @ant-design/cssinjs)
    - Legacy (@ant-design/compatible, babel-plugin-import)
    - Ecosystem (umi, dumi, ahooks)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Ant Design ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core antd ─────────────────────────────────────────────
        'antd': re.compile(
            r"from\s+['\"]antd['/\"]|"
            r"require\(['\"]antd['/\"]\)",
            re.MULTILINE
        ),
        'antd-icons': re.compile(
            r"from\s+['\"]@ant-design/icons['/\"]|"
            r"require\(['\"]@ant-design/icons['/\"]\)",
            re.MULTILINE
        ),
        'antd-cssinjs': re.compile(
            r"from\s+['\"]@ant-design/cssinjs['/\"]",
            re.MULTILINE
        ),

        # ── Ant Design Pro ────────────────────────────────────────
        'antd-pro-components': re.compile(
            r"from\s+['\"]@ant-design/pro-components['/\"]|"
            r"from\s+['\"]@ant-design/pro-table['/\"]|"
            r"from\s+['\"]@ant-design/pro-form['/\"]|"
            r"from\s+['\"]@ant-design/pro-layout['/\"]|"
            r"from\s+['\"]@ant-design/pro-card['/\"]|"
            r"from\s+['\"]@ant-design/pro-list['/\"]|"
            r"from\s+['\"]@ant-design/pro-descriptions['/\"]|"
            r"from\s+['\"]@ant-design/pro-field['/\"]|"
            r"from\s+['\"]@ant-design/pro-skeleton['/\"]",
            re.MULTILINE
        ),
        'antd-pro-table': re.compile(
            r"from\s+['\"]@ant-design/pro-table['/\"]",
            re.MULTILINE
        ),
        'antd-pro-form': re.compile(
            r"from\s+['\"]@ant-design/pro-form['/\"]",
            re.MULTILINE
        ),
        'antd-pro-layout': re.compile(
            r"from\s+['\"]@ant-design/pro-layout['/\"]",
            re.MULTILINE
        ),

        # ── Charts & Visualization ────────────────────────────────
        'antd-charts': re.compile(
            r"from\s+['\"]@ant-design/charts['/\"]|"
            r"from\s+['\"]@ant-design/plots['/\"]",
            re.MULTILINE
        ),
        'antd-maps': re.compile(
            r"from\s+['\"]@ant-design/maps['/\"]",
            re.MULTILINE
        ),

        # ── Mobile ────────────────────────────────────────────────
        'antd-mobile': re.compile(
            r"from\s+['\"]antd-mobile['/\"]|"
            r"require\(['\"]antd-mobile['/\"]\)",
            re.MULTILINE
        ),

        # ── Styling ──────────────────────────────────────────────
        'antd-style': re.compile(
            r"from\s+['\"]antd-style['/\"]",
            re.MULTILINE
        ),

        # ── Migration / Compat ────────────────────────────────────
        'antd-compatible': re.compile(
            r"from\s+['\"]@ant-design/compatible['/\"]",
            re.MULTILINE
        ),

        # ── Ecosystem (umi) ──────────────────────────────────────
        'umi': re.compile(
            r"from\s+['\"]umi['/\"]|"
            r"from\s+['\"]@umijs/max['/\"]|"
            r"from\s+['\"]@@/",
            re.MULTILINE
        ),
        'dumi': re.compile(
            r"from\s+['\"]dumi['/\"]",
            re.MULTILINE
        ),
        'ahooks': re.compile(
            r"from\s+['\"]ahooks['/\"]",
            re.MULTILINE
        ),

        # ── Utility ──────────────────────────────────────────────
        'antd-colors': re.compile(
            r"from\s+['\"]@ant-design/colors['/\"]",
            re.MULTILINE
        ),
        'antd-icons-svg': re.compile(
            r"from\s+['\"]@ant-design/icons-svg['/\"]",
            re.MULTILINE
        ),
        'antd-dayjs-plugin': re.compile(
            r"antd-dayjs-webpack-plugin|"
            r"from\s+['\"]dayjs['\"]",
            re.MULTILINE
        ),

        # ── Legacy ───────────────────────────────────────────────
        'babel-plugin-import': re.compile(
            r"babel-plugin-import|"
            r"import\s+\w+\s+from\s+['\"]antd/(?:es|lib)/",
            re.MULTILINE
        ),

        # ── Ant Design Vue (sister project) ──────────────────────
        'ant-design-vue': re.compile(
            r"from\s+['\"]ant-design-vue['/\"]",
            re.MULTILINE
        ),

        # ── Ant Design React Native ──────────────────────────────
        'antd-react-native': re.compile(
            r"from\s+['\"]@ant-design/react-native['/\"]",
            re.MULTILINE
        ),

        # ── Ant Design Web3 ──────────────────────────────────────
        'antd-web3': re.compile(
            r"from\s+['\"]@ant-design/web3['/\"]",
            re.MULTILINE
        ),

        # ── Additional ecosystem ─────────────────────────────────
        'antd-img-crop': re.compile(
            r"from\s+['\"]antd-img-crop['\"]",
            re.MULTILINE
        ),
        'antd-moment-webpack-plugin': re.compile(
            r"antd-moment-webpack-plugin",
            re.MULTILINE
        ),
        'antd-token-previewer': re.compile(
            r"from\s+['\"]@ant-design/token-previewer['/\"]",
            re.MULTILINE
        ),
        'antd-happy-work-theme': re.compile(
            r"from\s+['\"]@ant-design/happy-work-theme['/\"]",
            re.MULTILINE
        ),
    }

    # Ant Design version detection from import patterns and APIs
    ANTD_VERSION_INDICATORS = {
        # v5 indicators (CSS-in-JS, Design Tokens, App component)
        '@ant-design/cssinjs': 'v5',
        'antd-style': 'v5',
        'cssVar': 'v5',
        'App.useApp': 'v5',
        'useApp': 'v5',
        'useToken': 'v5',
        'useWatch': 'v5',
        'useFormInstance': 'v5',
        'colorPrimary': 'v5',
        'Flex': 'v5',
        'QRCode': 'v5',
        'Tour': 'v5',
        'Watermark': 'v5',
        'FloatButton': 'v5',
        'ColorPicker': 'v5',
        'Segmented': 'v5',
        'algorithm': 'v5',
        'darkAlgorithm': 'v5',
        'compactAlgorithm': 'v5',
        '@ant-design/happy-work-theme': 'v5',

        # v4 indicators (hooks-based Form, @ant-design/icons)
        '@ant-design/icons': 'v4',
        'Form.useForm': 'v4',
        'useForm': 'v4',
        '@ant-design/compatible': 'v4',

        # v3 indicators (Form.create, LocaleProvider, Icon component)
        'Form.create': 'v3',
        'LocaleProvider': 'v3',
        "from 'antd/lib/icon'": 'v3',
        'babel-plugin-import': 'v3',

        # v2/v1 indicators
        "from 'antd/lib": 'v2',
    }

    # Priority ordering for version comparison
    VERSION_PRIORITY = {'v5': 5, 'v4': 4, 'v3': 3, 'v2': 2, 'v1': 1}

    def __init__(self):
        """Initialize the parser with all Ant Design extractors."""
        self.component_extractor = AntdComponentExtractor()
        self.theme_extractor = AntdThemeExtractor()
        self.hook_extractor = AntdHookExtractor()
        self.style_extractor = AntdStyleExtractor()
        self.api_extractor = AntdApiExtractor()

    def parse(self, content: str, file_path: str = "") -> AntdParseResult:
        """
        Parse source code and extract all Ant Design-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when Ant Design framework is detected. It extracts component usage, theme
        configuration, hook patterns, styling approaches, and API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            AntdParseResult with all extracted Ant Design information
        """
        result = AntdParseResult(file_path=file_path)

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
        result.pro_components = comp_result.get('pro_components', [])

        # ── Extract theme ─────────────────────────────────────────
        theme_result = self.theme_extractor.extract(content, file_path)
        result.themes = theme_result.get('themes', [])
        result.tokens = theme_result.get('tokens', [])
        result.less_variables = theme_result.get('less_variables', [])
        result.component_tokens = theme_result.get('component_tokens', [])

        # ── Extract hooks ─────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hook_usages = hook_result.get('hook_usages', [])
        result.custom_hooks = hook_result.get('custom_hooks', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.css_in_js = style_result.get('css_in_js', [])
        result.less_styles = style_result.get('less_styles', [])
        result.style_overrides = style_result.get('style_overrides', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.tables = api_result.get('tables', [])
        result.forms = api_result.get('forms', [])
        result.modals = api_result.get('modals', [])
        result.menus = api_result.get('menus', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_pro_components = len(result.pro_components) > 0
        result.has_theme = len(result.themes) > 0
        result.has_css_in_js = len(result.css_in_js) > 0
        result.has_less_theming = len(result.less_variables) > 0 or any(
            ls.is_antd_override for ls in result.less_styles
        )
        result.has_dark_mode = any(t.has_dark_mode for t in result.themes)
        result.has_css_variables = any(t.has_css_variables for t in result.themes)
        result.has_design_tokens = len(result.tokens) > 0
        result.has_antd_mobile = 'antd-mobile' in result.detected_frameworks

        # ── Detect antd version ───────────────────────────────────
        result.antd_version = self._detect_antd_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_antd_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Ant Design code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Ant Design code
        """
        if not content:
            return False

        # Check for antd imports (ES module)
        if re.search(r"from\s+['\"]antd['/\"]", content):
            return True

        # Check for antd require() imports (CommonJS)
        if re.search(r"require\(['\"]antd['/\"]\)", content):
            return True

        # Check for @ant-design/* imports
        if re.search(r"from\s+['\"]@ant-design/", content):
            return True

        # Check for @ant-design/* require() imports
        if re.search(r"require\(['\"]@ant-design/", content):
            return True

        # Check for antd tree-shaking imports
        if re.search(r"from\s+['\"]antd/(?:es|lib)/", content):
            return True

        # Check for antd-mobile
        if re.search(r"from\s+['\"]antd-mobile['/\"]", content):
            return True

        # Check for antd-style
        if re.search(r"from\s+['\"]antd-style['/\"]", content):
            return True

        # Check for ConfigProvider with theme (strong antd indicator)
        if re.search(r'<ConfigProvider[^>]*\btheme\s*=', content):
            return True

        # Check for Form.useForm or Form.create (antd-specific patterns)
        if re.search(r'Form\.useForm|Form\.create|Form\.Item', content):
            return True

        # Check for umi (strongly associated with antd)
        if re.search(r"from\s+['\"]umi['\"]|from\s+['\"]@umijs/", content):
            return True

        return False

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Ant Design ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_antd_version(self, content: str, result: AntdParseResult) -> str:
        """
        Detect the Ant Design version from imports and API patterns.

        Returns version string: 'v1', 'v2', 'v3', 'v4', 'v5'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.ANTD_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # Override: CSS-in-JS is definitive v5 indicator
        if result.has_css_in_js:
            return 'v5'

        # Override: design tokens imply v5
        if result.has_design_tokens and any(t.token_type == 'seed' for t in result.tokens):
            return 'v5'

        # Theme-based detection
        for theme in result.themes:
            if theme.antd_version:
                v = theme.antd_version
                v_priority = self.VERSION_PRIORITY.get(v, 0)
                if v_priority > max_priority:
                    max_priority = v_priority
                    detected_version = v

        return detected_version

    def _detect_features(self, content: str, result: AntdParseResult) -> List[str]:
        """Detect Ant Design features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('antd_components')
            categories = set(c.category for c in result.components if c.category)
            for cat in sorted(categories):
                features.append(f'antd_category_{cat}')

        if result.pro_components:
            features.append('pro_components')
            pro_types = set(p.pro_type for p in result.pro_components if p.pro_type)
            for pt in sorted(pro_types):
                features.append(f'pro_{pt}')

        if result.custom_components:
            features.append('custom_wrapped_components')

        # Theme features
        if result.has_theme:
            features.append('theme_configuration')
        if result.has_design_tokens:
            features.append('design_tokens')
        if result.has_dark_mode:
            features.append('dark_mode')
        if result.has_css_variables:
            features.append('css_variables')
        if result.component_tokens:
            features.append('component_tokens')
        if result.less_variables:
            features.append('less_variables')

        # Style features
        if result.has_css_in_js:
            features.append('css_in_js')
        if result.has_less_theming:
            features.append('less_theming')
        if result.style_overrides:
            features.append('class_overrides')

        # Hook features
        if result.hook_usages:
            hook_categories = set(h.category for h in result.hook_usages if h.category)
            for cat in sorted(hook_categories):
                features.append(f'hooks_{cat}')

        # API features
        if result.tables:
            features.append('table_patterns')
            for table in result.tables:
                if table.has_server_side:
                    features.append('server_side_table')
                if table.has_row_selection:
                    features.append('row_selection')
                if table.has_virtual_scroll:
                    features.append('virtual_scroll')

        if result.forms:
            features.append('form_patterns')
            for form in result.forms:
                if form.has_validation:
                    features.append('form_validation')
                if form.has_dynamic_fields:
                    features.append('dynamic_form')

        if result.modals:
            features.append('modal_patterns')

        if result.menus:
            features.append('menu_patterns')

        # Mobile
        if result.has_antd_mobile:
            features.append('antd_mobile')

        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
