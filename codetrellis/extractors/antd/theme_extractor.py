"""
Ant Design Theme Extractor for CodeTrellis

Extracts Ant Design theme configuration from React/TypeScript source code.
Covers theming across all Ant Design versions:
- v5.x: ConfigProvider theme prop, Design Tokens (Seed/Map/Alias),
         component-level tokens, algorithms (dark, compact, custom),
         CSS Variables mode, antd-style createStyles
- v4.x: Less variables (@primary-color, @font-size-base, etc.),
         ConfigProvider componentSize, modifyVars in webpack/craco/umi
- v3.x: Less variable overrides, babel-plugin-import
- v2.x/v1.x: Basic theme via less overrides

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AntdThemeInfo:
    """Information about an Ant Design theme configuration."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    method: str = ""              # ConfigProvider, less, modifyVars, createStyles
    antd_version: str = ""        # v1, v2, v3, v4, v5
    has_dark_mode: bool = False
    has_compact: bool = False
    has_css_variables: bool = False
    has_component_tokens: bool = False
    has_algorithm: bool = False
    algorithm_types: List[str] = field(default_factory=list)  # darkAlgorithm, compactAlgorithm
    token_count: int = 0
    custom_tokens: List[str] = field(default_factory=list)


@dataclass
class AntdTokenInfo:
    """Information about Ant Design design tokens (v5+)."""
    token_name: str
    file: str = ""
    line_number: int = 0
    token_type: str = ""          # seed, map, alias, component
    value: str = ""
    is_custom: bool = False


@dataclass
class AntdLessVariableInfo:
    """Information about Ant Design Less variable overrides (v3/v4)."""
    variable_name: str
    file: str = ""
    line_number: int = 0
    value: str = ""
    is_custom: bool = False


@dataclass
class AntdComponentTokenInfo:
    """Information about component-level token customization (v5+)."""
    component_name: str
    file: str = ""
    line_number: int = 0
    tokens: List[str] = field(default_factory=list)
    token_count: int = 0


class AntdThemeExtractor:
    """
    Extracts Ant Design theme configuration from source code.

    Detects:
    - ConfigProvider with theme prop (v5+)
    - Design token customization (seed, map, alias tokens)
    - Algorithm usage (dark, compact, custom)
    - Component-level token overrides (v5+)
    - CSS Variables mode (v5.12+)
    - Less variable overrides (v3/v4)
    - modifyVars in build configs
    """

    # ConfigProvider theme pattern
    CONFIG_PROVIDER_THEME = re.compile(
        r'<ConfigProvider[^>]*\btheme\s*=\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # createTheme or theme object creation
    THEME_OBJECT = re.compile(
        r'(?:const|let|var)\s+(\w*[Tt]heme\w*)\s*(?::\s*\w+\s*)?=\s*\{',
        re.MULTILINE
    )

    # Algorithm patterns
    ALGORITHM_PATTERN = re.compile(
        r'(?:theme\.)?(\w*[Aa]lgorithm\w*)|'
        r'(darkAlgorithm|compactAlgorithm|defaultAlgorithm)',
        re.MULTILINE
    )

    # Token patterns
    TOKEN_PATTERN = re.compile(
        r'\b(colorPrimary|colorSuccess|colorWarning|colorError|colorInfo|'
        r'colorBgContainer|colorBgElevated|colorBgLayout|colorBorder|'
        r'colorText|colorTextSecondary|colorTextTertiary|colorTextQuaternary|'
        r'fontSize|fontSizeHeading\d|fontFamily|fontWeightStrong|'
        r'lineHeight|lineWidth|lineType|'
        r'borderRadius|borderRadiusLG|borderRadiusSM|borderRadiusXS|'
        r'controlHeight|controlHeightSM|controlHeightLG|'
        r'padding|paddingXS|paddingSM|paddingMD|paddingLG|paddingXL|'
        r'margin|marginXS|marginSM|marginMD|marginLG|marginXL|'
        r'motion|motionDurationFast|motionDurationMid|motionDurationSlow|'
        r'sizeStep|sizeUnit|wireframe|'
        r'colorPrimaryBg|colorPrimaryBgHover|colorPrimaryBorder|'
        r'colorPrimaryBorderHover|colorPrimaryHover|colorPrimaryActive|'
        r'colorPrimaryTextHover|colorPrimaryText|colorPrimaryTextActive|'
        r'boxShadow|boxShadowSecondary|screenXS|screenSM|screenMD|screenLG|screenXL|screenXXL)\b',
        re.MULTILINE
    )

    # Less variable pattern (v3/v4)
    LESS_VARIABLE_PATTERN = re.compile(
        r'@(primary-color|link-color|success-color|warning-color|error-color|'
        r'font-size-base|heading-color|text-color|text-color-secondary|'
        r'disabled-color|border-radius-base|border-color-base|'
        r'box-shadow-base|btn-primary-bg|input-height-base|'
        r'layout-body-background|layout-header-background|'
        r'layout-sider-background|menu-dark-bg|'
        r'component-background|body-background)\s*:\s*([^;]+)',
        re.MULTILINE
    )

    # modifyVars pattern
    MODIFY_VARS_PATTERN = re.compile(
        r'modifyVars\s*:\s*\{([^}]+)\}',
        re.MULTILINE | re.DOTALL
    )

    # CSS Variables mode (v5.12+)
    CSS_VARIABLES_PATTERN = re.compile(
        r'cssVar\s*:\s*(?:true|\{)|'
        r"cssVar\s*:\s*\{\s*key\s*:",
        re.MULTILINE
    )

    # Component token pattern
    COMPONENT_TOKEN_PATTERN = re.compile(
        r'components\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Individual component token
    INDIVIDUAL_COMPONENT_TOKEN = re.compile(
        r'(\w+)\s*:\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # Import algorithm from antd
    ALGORITHM_IMPORT = re.compile(
        r"from\s+['\"]antd['\"].*\btheme\b|"
        r"import\s+\{[^}]*\btheme\b[^}]*\}\s+from\s+['\"]antd['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Ant Design theme information from source code."""
        result = {
            'themes': [],
            'tokens': [],
            'less_variables': [],
            'component_tokens': [],
        }

        if not content or not content.strip():
            return result

        # Detect v5+ ConfigProvider theme
        for match in self.CONFIG_PROVIDER_THEME.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Check for theme features in surrounding context
            context_end = min(match.start() + 3000, len(content))
            context = content[match.start():context_end]

            algorithms = []
            if 'darkAlgorithm' in context:
                algorithms.append('darkAlgorithm')
            if 'compactAlgorithm' in context:
                algorithms.append('compactAlgorithm')
            if 'defaultAlgorithm' in context:
                algorithms.append('defaultAlgorithm')

            theme_info = AntdThemeInfo(
                name='ConfigProvider',
                file=file_path,
                line_number=line_num,
                method='ConfigProvider',
                antd_version='v5',
                has_dark_mode='darkAlgorithm' in context or 'dark' in context.lower(),
                has_compact='compactAlgorithm' in context or 'compact' in context.lower(),
                has_css_variables=bool(self.CSS_VARIABLES_PATTERN.search(context)),
                has_component_tokens='components:' in context or 'components :' in context,
                has_algorithm=len(algorithms) > 0,
                algorithm_types=algorithms,
            )
            result['themes'].append(theme_info)

        # Detect theme objects
        for match in self.THEME_OBJECT.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            context_end = min(match.start() + 2000, len(content))
            context = content[match.start():context_end]

            # Only count if it looks like an antd theme
            if any(tok in context for tok in ['colorPrimary', 'token', 'algorithm', 'components']):
                tokens_found = self.TOKEN_PATTERN.findall(context)
                theme_info = AntdThemeInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    method='object',
                    antd_version='v5',
                    has_dark_mode='dark' in context.lower(),
                    token_count=len(tokens_found),
                    custom_tokens=list(set(tokens_found))[:20],
                )
                result['themes'].append(theme_info)

        # Extract design tokens (v5+)
        for match in self.TOKEN_PATTERN.finditer(content):
            token = match.group(1) if match.group(1) else match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            token_type = self._classify_token(token)
            result['tokens'].append(AntdTokenInfo(
                token_name=token,
                file=file_path,
                line_number=line_num,
                token_type=token_type,
            ))

        # Extract Less variables (v3/v4)
        for match in self.LESS_VARIABLE_PATTERN.finditer(content):
            var_name = match.group(1)
            value = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            result['less_variables'].append(AntdLessVariableInfo(
                variable_name=var_name,
                file=file_path,
                line_number=line_num,
                value=value,
            ))

        # Extract modifyVars
        for match in self.MODIFY_VARS_PATTERN.finditer(content):
            vars_content = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Parse individual vars
            var_pattern = re.compile(r"'@([\w-]+)'\s*:\s*['\"]?([^,'\"}]+)")
            for vm in var_pattern.finditer(vars_content):
                result['less_variables'].append(AntdLessVariableInfo(
                    variable_name=vm.group(1),
                    file=file_path,
                    line_number=line_num,
                    value=vm.group(2).strip(),
                    is_custom=True,
                ))

        # Extract component-level tokens (v5+)
        for match in self.COMPONENT_TOKEN_PATTERN.finditer(content):
            components_block = match.group(1)
            for comp_match in self.INDIVIDUAL_COMPONENT_TOKEN.finditer(components_block):
                comp_name = comp_match.group(1)
                tokens_block = comp_match.group(2)
                token_names = re.findall(r'(\w+)\s*:', tokens_block)
                if comp_name[0].isupper():  # Only component names (capitalized)
                    result['component_tokens'].append(AntdComponentTokenInfo(
                        component_name=comp_name,
                        file=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        tokens=token_names[:20],
                        token_count=len(token_names),
                    ))

        return result

    def _classify_token(self, token: str) -> str:
        """Classify a token as seed, map, or alias."""
        seed_tokens = {
            'colorPrimary', 'colorSuccess', 'colorWarning', 'colorError', 'colorInfo',
            'fontSize', 'fontFamily', 'borderRadius', 'lineWidth', 'lineType',
            'controlHeight', 'sizeStep', 'sizeUnit', 'wireframe', 'motion',
        }
        if token in seed_tokens:
            return 'seed'
        elif token.startswith('color') and ('Bg' in token or 'Text' in token or 'Border' in token):
            return 'map'
        elif token.startswith('screen'):
            return 'alias'
        elif token.startswith('padding') or token.startswith('margin'):
            return 'map'
        return 'alias'
