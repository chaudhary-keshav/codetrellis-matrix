"""
Ant Design Component Extractor for CodeTrellis

Extracts Ant Design component usage from React/TypeScript source code.
Covers Ant Design v1.x through v5.x, including:
- Core component usage (Button, Input, Table, Form, Layout, etc.)
- Data display (Table, List, Card, Descriptions, Tree, Timeline, Tag)
- Layout (Layout, Grid Row/Col, Space, Flex, Divider)
- Navigation (Menu, Breadcrumb, Pagination, Steps, Tabs, Dropdown)
- Feedback (Modal, Drawer, Notification, Message, Alert, Popconfirm)
- Data Entry (Form, Input, Select, DatePicker, Upload, Transfer, Cascader)
- Pro Components (ProTable, ProForm, ProLayout, ProCard, ProDescriptions)
- Custom wrapped components built on Ant Design
- Component composition patterns

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AntdComponentInfo:
    """Information about an Ant Design component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # antd, @ant-design/pro-components, etc.
    category: str = ""            # layout, input, display, feedback, navigation, data-entry, other
    is_pro_component: bool = False
    props_used: List[str] = field(default_factory=list)
    has_custom_render: bool = False
    sub_components: List[str] = field(default_factory=list)  # e.g., Form.Item, Menu.SubMenu


@dataclass
class AntdCustomComponentInfo:
    """Information about a custom component wrapping Ant Design."""
    name: str
    file: str = ""
    line_number: int = 0
    base_component: str = ""     # The antd component being wrapped
    method: str = ""             # wrapper, hoc, forwardRef
    has_theme_usage: bool = False
    additional_props: List[str] = field(default_factory=list)


@dataclass
class AntdProComponentInfo:
    """Information about Ant Design Pro component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""      # @ant-design/pro-components, @ant-design/pro-table, etc.
    pro_type: str = ""           # table, form, layout, card, list, descriptions, field
    columns_count: int = 0
    has_request: bool = False    # Pro components with request prop for data fetching
    has_search: bool = False     # ProTable search feature


class AntdComponentExtractor:
    """
    Extracts Ant Design component usage from React/TypeScript source code.

    Detects:
    - Ant Design core component imports and usage (80+ components)
    - Ant Design Pro component imports (ProTable, ProForm, ProLayout, etc.)
    - Custom components wrapping Ant Design
    - Component composition (Form.Item, Menu.SubMenu, etc.)
    """

    # Ant Design component categories
    COMPONENT_CATEGORIES = {
        # General
        'Button': 'general', 'Icon': 'general', 'Typography': 'general',
        'Text': 'general', 'Title': 'general', 'Paragraph': 'general',
        'Link': 'general',
        # Layout
        'Layout': 'layout', 'Header': 'layout', 'Footer': 'layout',
        'Content': 'layout', 'Sider': 'layout',
        'Row': 'layout', 'Col': 'layout',
        'Space': 'layout', 'Flex': 'layout', 'Divider': 'layout',
        'Grid': 'layout',
        # Navigation
        'Menu': 'navigation', 'Breadcrumb': 'navigation',
        'Pagination': 'navigation', 'Steps': 'navigation',
        'Tabs': 'navigation', 'Dropdown': 'navigation',
        'Affix': 'navigation', 'Anchor': 'navigation',
        'BackTop': 'navigation',
        # Data Entry
        'Form': 'data-entry', 'Input': 'data-entry', 'InputNumber': 'data-entry',
        'Select': 'data-entry', 'TreeSelect': 'data-entry',
        'Cascader': 'data-entry', 'Checkbox': 'data-entry',
        'Radio': 'data-entry', 'Switch': 'data-entry',
        'Slider': 'data-entry', 'DatePicker': 'data-entry',
        'TimePicker': 'data-entry', 'Transfer': 'data-entry',
        'Upload': 'data-entry', 'AutoComplete': 'data-entry',
        'ColorPicker': 'data-entry', 'Mentions': 'data-entry',
        'Rate': 'data-entry', 'RangePicker': 'data-entry',
        # Data Display
        'Table': 'data-display', 'Collapse': 'data-display',
        'Card': 'data-display', 'Descriptions': 'data-display',
        'List': 'data-display', 'Tree': 'data-display',
        'Timeline': 'data-display', 'Tag': 'data-display',
        'Tooltip': 'data-display', 'Popover': 'data-display',
        'Badge': 'data-display', 'Avatar': 'data-display',
        'Calendar': 'data-display', 'Carousel': 'data-display',
        'Empty': 'data-display', 'Image': 'data-display',
        'Statistic': 'data-display', 'Segmented': 'data-display',
        'QRCode': 'data-display', 'Tour': 'data-display',
        'Watermark': 'data-display',
        # Feedback
        'Modal': 'feedback', 'Drawer': 'feedback',
        'Alert': 'feedback', 'Notification': 'feedback',
        'Message': 'feedback', 'Popconfirm': 'feedback',
        'Progress': 'feedback', 'Spin': 'feedback',
        'Skeleton': 'feedback', 'Result': 'feedback',
        # Other
        'ConfigProvider': 'other',
        'App': 'other', 'FloatButton': 'other',
        'WaterMark': 'other',
    }

    # Sub-component patterns (Form.Item, Menu.SubMenu, etc.)
    SUB_COMPONENT_PATTERNS = {
        'Form': ['Item', 'List', 'Provider', 'ErrorList', 'useForm', 'useWatch', 'useFormInstance'],
        'Menu': ['Item', 'SubMenu', 'ItemGroup', 'Divider'],
        'Table': ['Column', 'ColumnGroup', 'Summary'],
        'Layout': ['Header', 'Footer', 'Content', 'Sider'],
        'Typography': ['Text', 'Title', 'Paragraph', 'Link'],
        'Input': ['TextArea', 'Password', 'Search', 'Group', 'OTP'],
        'Select': ['Option', 'OptGroup'],
        'Checkbox': ['Group'],
        'Radio': ['Group', 'Button'],
        'List': ['Item'],
        'Card': ['Meta', 'Grid'],
        'Collapse': ['Panel'],
        'Tabs': ['TabPane'],
        'Steps': ['Step'],
        'Breadcrumb': ['Item', 'Separator'],
        'Timeline': ['Item'],
        'Tree': ['TreeNode', 'DirectoryTree'],
        'Upload': ['Dragger'],
        'Dropdown': ['Button'],
        'Avatar': ['Group'],
        'Badge': ['Ribbon'],
        'Image': ['PreviewGroup'],
        'Descriptions': ['Item'],
    }

    # Pro component names
    PRO_COMPONENTS = {
        'ProTable', 'EditableProTable', 'DragSortTable',
        'ProForm', 'ProFormText', 'ProFormSelect', 'ProFormDatePicker',
        'ProFormDigit', 'ProFormTextArea', 'ProFormRadio',
        'ProFormCheckbox', 'ProFormSwitch', 'ProFormUploadButton',
        'ProFormUploadDragger', 'ProFormList', 'ProFormGroup',
        'ProFormDependency', 'ProFormFieldSet', 'ProFormSet',
        'StepsForm', 'ModalForm', 'DrawerForm', 'QueryFilter',
        'LightFilter', 'LoginForm', 'LoginFormPage',
        'ProLayout', 'PageContainer', 'FooterToolbar',
        'ProCard', 'StatisticCard', 'CheckCard',
        'ProList', 'ProDescriptions',
        'ProFormDateTimePicker', 'ProFormDateRangePicker',
        'ProFormTimePicker', 'ProFormMoney', 'ProFormColorPicker',
        'ProFormSlider', 'ProFormRate', 'ProFormCascader',
        'ProFormTreeSelect', 'ProFormSegmented',
        'ProSkeleton', 'WaterMark',
        'ProField', 'ProFormItem',
    }

    # Import pattern for antd components
    ANTD_IMPORT_PATTERN = re.compile(
        r"import\s*\{([^}]+)\}\s*from\s*['\"]antd['\"]",
        re.MULTILINE
    )

    # Import pattern for @ant-design/ scope
    ANT_DESIGN_IMPORT_PATTERN = re.compile(
        r"import\s*\{([^}]+)\}\s*from\s*['\"]@ant-design/([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Import pattern for antd/es or antd/lib (tree-shaking imports)
    ANTD_SUBPATH_IMPORT = re.compile(
        r"import\s+(\w+)\s+from\s*['\"]antd/(?:es|lib)/(\w+)['\"]",
        re.MULTILINE
    )

    # JSX usage pattern
    JSX_USAGE_PATTERN = re.compile(
        r'<(\w+)(?:\.\w+)?\s',
        re.MULTILINE
    )

    # Sub-component usage (Form.Item, Menu.SubMenu)
    SUB_COMPONENT_USAGE = re.compile(
        r'<(\w+)\.(\w+)\s',
        re.MULTILINE
    )

    # Custom component wrapper patterns
    CUSTOM_WRAPPER_PATTERN = re.compile(
        r'(?:const|function)\s+(\w+)\s*[=:]\s*(?:\([^)]*\)\s*(?:=>|:)|\s*\{)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Ant Design component information from source code."""
        result = {
            'components': [],
            'custom_components': [],
            'pro_components': [],
        }

        if not content or not content.strip():
            return result

        # Extract imports
        imported_components = set()
        import_sources = {}

        # antd imports
        for match in self.ANTD_IMPORT_PATTERN.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in match.group(1).split(',')]
            for name in names:
                if name:
                    imported_components.add(name)
                    import_sources[name] = 'antd'

        # @ant-design/* imports
        for match in self.ANT_DESIGN_IMPORT_PATTERN.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in match.group(1).split(',')]
            scope = match.group(2)
            for name in names:
                if name:
                    imported_components.add(name)
                    import_sources[name] = f'@ant-design/{scope}'

        # antd/es/* or antd/lib/* imports (tree-shaking)
        for match in self.ANTD_SUBPATH_IMPORT.finditer(content):
            name = match.group(1)
            if name:
                imported_components.add(name)
                import_sources[name] = f'antd/{match.group(2)}'

        # Find component usages in JSX
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Direct component usage
            for jsx_match in self.JSX_USAGE_PATTERN.finditer(line):
                comp_name = jsx_match.group(1)
                if comp_name in imported_components or comp_name in self.COMPONENT_CATEGORIES:
                    category = self.COMPONENT_CATEGORIES.get(comp_name, 'other')
                    is_pro = comp_name in self.PRO_COMPONENTS
                    source = import_sources.get(comp_name, '')

                    # Check for props
                    props_used = self._extract_props(line, comp_name)
                    has_custom_render = 'render' in line.lower() and comp_name in line

                    comp_info = AntdComponentInfo(
                        name=comp_name,
                        file=file_path,
                        line_number=i,
                        import_source=source,
                        category=category,
                        is_pro_component=is_pro,
                        props_used=props_used,
                        has_custom_render=has_custom_render,
                    )
                    result['components'].append(comp_info)

                    if is_pro:
                        pro_type = self._classify_pro_type(comp_name)
                        pro_info = AntdProComponentInfo(
                            name=comp_name,
                            file=file_path,
                            line_number=i,
                            import_source=source,
                            pro_type=pro_type,
                            has_request='request' in line or 'request=' in line,
                            has_search='search' in line,
                        )
                        result['pro_components'].append(pro_info)

            # Sub-component usage
            for sub_match in self.SUB_COMPONENT_USAGE.finditer(line):
                parent = sub_match.group(1)
                child = sub_match.group(2)
                if parent in imported_components or parent in self.COMPONENT_CATEGORIES:
                    comp_info = AntdComponentInfo(
                        name=f"{parent}.{child}",
                        file=file_path,
                        line_number=i,
                        import_source=import_sources.get(parent, ''),
                        category=self.COMPONENT_CATEGORIES.get(parent, 'other'),
                        sub_components=[child],
                    )
                    result['components'].append(comp_info)

        # Detect custom wrappers
        for match in self.CUSTOM_WRAPPER_PATTERN.finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            # Check if function body references antd components
            body_start = match.start()
            body_end = min(body_start + 2000, len(content))
            body = content[body_start:body_end]

            for antd_comp in imported_components:
                if antd_comp in self.COMPONENT_CATEGORIES and f'<{antd_comp}' in body:
                    result['custom_components'].append(AntdCustomComponentInfo(
                        name=func_name,
                        file=file_path,
                        line_number=line_num,
                        base_component=antd_comp,
                        method='wrapper',
                    ))
                    break

        return result

    def _extract_props(self, line: str, comp_name: str) -> List[str]:
        """Extract prop names from a JSX component usage line."""
        props = []
        prop_pattern = re.compile(r'(\w+)=')
        for m in prop_pattern.finditer(line):
            prop = m.group(1)
            if prop != comp_name and prop not in ('import', 'from', 'const', 'let', 'var'):
                props.append(prop)
        return props[:20]

    def _classify_pro_type(self, name: str) -> str:
        """Classify pro component type."""
        name_lower = name.lower()
        if 'table' in name_lower:
            return 'table'
        elif 'form' in name_lower or 'filter' in name_lower or 'login' in name_lower:
            return 'form'
        elif 'layout' in name_lower or 'pagecontainer' in name_lower or 'footer' in name_lower:
            return 'layout'
        elif 'card' in name_lower or 'statistic' in name_lower or 'check' in name_lower:
            return 'card'
        elif 'list' in name_lower:
            return 'list'
        elif 'description' in name_lower:
            return 'descriptions'
        elif 'field' in name_lower:
            return 'field'
        elif 'skeleton' in name_lower:
            return 'skeleton'
        return 'other'
