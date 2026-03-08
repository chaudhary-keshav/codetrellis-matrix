"""
Ant Design Style Extractor for CodeTrellis

Extracts Ant Design styling patterns from React/TypeScript source code.
Covers styling approaches across all Ant Design versions:
- v5.x: CSS-in-JS via createStyles (antd-style), token usage in styles,
         component class overrides, CSS variables
- v4.x: Less/Sass module imports, CSS modules, class overrides
- v3.x: Less variable overrides, custom less files
- All: styled-components integration, className patterns, inline styles

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AntdCSSInJSInfo:
    """Information about CSS-in-JS usage with Ant Design (v5+)."""
    name: str
    file: str = ""
    line_number: int = 0
    method: str = ""              # createStyles, createGlobalStyle, css
    has_token_usage: bool = False
    has_responsive: bool = False
    style_count: int = 0
    token_names: List[str] = field(default_factory=list)


@dataclass
class AntdLessStyleInfo:
    """Information about Less/CSS style files for Ant Design (v3/v4)."""
    file: str = ""
    line_number: int = 0
    import_path: str = ""
    is_module: bool = False       # CSS Modules (.module.less/.module.css)
    is_antd_override: bool = False
    variable_count: int = 0


@dataclass
class AntdStyleOverrideInfo:
    """Information about Ant Design class name overrides."""
    component_name: str
    file: str = ""
    line_number: int = 0
    override_type: str = ""       # className, style, rootClassName, popupClassName
    has_conditional: bool = False


class AntdStyleExtractor:
    """
    Extracts Ant Design styling patterns from source code.

    Detects:
    - createStyles from antd-style (v5+ CSS-in-JS)
    - Design token usage in style functions
    - Less/CSS module imports for antd overrides
    - className overrides on antd components
    - rootClassName (v5+), popupClassName patterns
    - Inline style objects with theme tokens
    - styled-components wrapping antd components
    """

    # antd-style createStyles pattern
    CREATE_STYLES_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*createStyles\s*\(',
        re.MULTILINE
    )

    # createStyles import
    CREATE_STYLES_IMPORT = re.compile(
        r"from\s+['\"]antd-style['\"].*createStyles|"
        r"import\s+\{[^}]*createStyles[^}]*\}\s+from\s+['\"]antd-style['\"]",
        re.MULTILINE
    )

    # CSS import for antd overrides
    LESS_CSS_IMPORT = re.compile(
        r"import\s+(?:(\w+)\s+from\s+)?['\"]([^'\"]*\.(?:less|css|scss|sass))['\"]",
        re.MULTILINE
    )

    # className override on antd components
    CLASSNAME_OVERRIDE = re.compile(
        r'<(\w+)[^>]*\b(className|rootClassName|popupClassName|dropdownClassName|overlayClassName)\s*=',
        re.MULTILINE
    )

    # styled-components wrapping antd
    STYLED_ANTD_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*styled\((\w+)\)',
        re.MULTILINE
    )

    # css prop or css`` template literal
    CSS_TEMPLATE = re.compile(
        r'css`[^`]+`|css\s*\(\s*\{',
        re.MULTILINE
    )

    # Token usage in styles
    TOKEN_IN_STYLE = re.compile(
        r'token\.(colorPrimary|colorBgContainer|colorText|colorBorder|'
        r'borderRadius|fontSize|fontFamily|padding|margin|'
        r'controlHeight|colorSuccess|colorWarning|colorError|colorInfo)',
        re.MULTILINE
    )

    # Known antd components for className matching
    ANTD_COMPONENTS = {
        'Button', 'Input', 'Select', 'Table', 'Modal', 'Drawer', 'Form',
        'Card', 'Tabs', 'Menu', 'Layout', 'Dropdown', 'Popover', 'Tooltip',
        'DatePicker', 'TimePicker', 'Upload', 'Tree', 'Transfer', 'Cascader',
        'Steps', 'Collapse', 'Pagination', 'Badge', 'Tag', 'Alert',
        'Progress', 'Spin', 'Skeleton', 'Result', 'Descriptions',
        'List', 'Avatar', 'Image', 'Carousel', 'Calendar', 'Breadcrumb',
        'ConfigProvider', 'Space', 'Divider', 'Typography',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Ant Design style information from source code."""
        result = {
            'css_in_js': [],
            'less_styles': [],
            'style_overrides': [],
        }

        if not content or not content.strip():
            return result

        # Detect createStyles usage (antd-style v5+)
        has_create_styles_import = bool(self.CREATE_STYLES_IMPORT.search(content))
        for match in self.CREATE_STYLES_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Check for token usage in body
            body_start = match.start()
            body_end = min(body_start + 3000, len(content))
            body = content[body_start:body_end]

            tokens_found = self.TOKEN_IN_STYLE.findall(body)
            has_responsive = 'responsive' in body.lower() or '@media' in body or 'breakpoint' in body.lower()

            result['css_in_js'].append(AntdCSSInJSInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                method='createStyles',
                has_token_usage=len(tokens_found) > 0,
                has_responsive=has_responsive,
                token_names=list(set(tokens_found))[:15],
            ))

        # Detect Less/CSS imports
        for match in self.LESS_CSS_IMPORT.finditer(content):
            module_name = match.group(1) or ''
            import_path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            is_module = '.module.' in import_path
            is_antd_override = 'antd' in import_path.lower() or 'override' in import_path.lower()

            # Count less variables in context
            var_count = 0
            if import_path.endswith('.less'):
                var_count = content.count('@') // 4  # rough estimate

            result['less_styles'].append(AntdLessStyleInfo(
                file=file_path,
                line_number=line_num,
                import_path=import_path,
                is_module=is_module,
                is_antd_override=is_antd_override,
                variable_count=var_count,
            ))

        # Detect className overrides on antd components
        for match in self.CLASSNAME_OVERRIDE.finditer(content):
            comp_name = match.group(1)
            override_type = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if comp_name in self.ANTD_COMPONENTS:
                # Check if conditional className
                line = content.split('\n')[line_num - 1] if line_num <= content.count('\n') + 1 else ''
                has_conditional = '?' in line or 'classnames' in line.lower() or 'clsx' in line.lower()

                result['style_overrides'].append(AntdStyleOverrideInfo(
                    component_name=comp_name,
                    file=file_path,
                    line_number=line_num,
                    override_type=override_type,
                    has_conditional=has_conditional,
                ))

        # Detect styled-components wrapping antd components
        for match in self.STYLED_ANTD_PATTERN.finditer(content):
            styled_name = match.group(1)
            base_comp = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if base_comp in self.ANTD_COMPONENTS:
                result['css_in_js'].append(AntdCSSInJSInfo(
                    name=styled_name,
                    file=file_path,
                    line_number=line_num,
                    method='styled-components',
                ))

        return result
