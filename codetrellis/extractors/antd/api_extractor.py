"""
Ant Design API Pattern Extractor for CodeTrellis

Extracts Ant Design API patterns from React/TypeScript source code.
Covers patterns across all Ant Design versions:
- Table/ProTable: column definitions, sorting, filtering, pagination,
                   row selection, expandable rows, server-side data
- Form patterns: Form.Item rules, form layouts, validation, dependencies,
                  dynamic fields, form submission, initialValues
- Modal patterns: confirmation, form modals, full-screen, async close
- Drawer patterns: form drawers, detail drawers, nested drawers
- Menu/Navigation: menu items, submenu, sidebar, top navigation,
                    breadcrumb, steps

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AntdTableInfo:
    """Information about Ant Design Table/ProTable usage."""
    name: str
    file: str = ""
    line_number: int = 0
    table_type: str = ""          # Table, ProTable, EditableProTable
    column_count: int = 0
    has_sorting: bool = False
    has_filtering: bool = False
    has_pagination: bool = False
    has_row_selection: bool = False
    has_expandable: bool = False
    has_server_side: bool = False
    has_virtual_scroll: bool = False
    has_custom_render: bool = False


@dataclass
class AntdFormPatternInfo:
    """Information about Ant Design Form patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    form_layout: str = ""         # horizontal, vertical, inline
    has_validation: bool = False
    has_dependencies: bool = False
    has_dynamic_fields: bool = False
    has_initial_values: bool = False
    field_count: int = 0
    integration: str = ""         # react-hook-form, formik, custom


@dataclass
class AntdModalPatternInfo:
    """Information about Ant Design Modal/Drawer patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    modal_type: str = ""          # modal, drawer, confirm, info, success, error, warning
    has_form: bool = False
    has_async_close: bool = False
    has_footer: bool = False
    is_responsive: bool = False


@dataclass
class AntdMenuPatternInfo:
    """Information about Ant Design Menu/Navigation patterns."""
    name: str
    file: str = ""
    line_number: int = 0
    menu_type: str = ""           # horizontal, vertical, inline, sidebar
    item_count: int = 0
    has_submenu: bool = False
    has_icons: bool = False
    has_groups: bool = False
    is_collapsible: bool = False


class AntdApiExtractor:
    """
    Extracts Ant Design API patterns from source code.

    Detects:
    - Table/ProTable column definitions and features
    - Form.Item validation rules and patterns
    - Modal.confirm / Modal.info static methods
    - Drawer with form patterns
    - Menu item structures and navigation patterns
    - Upload patterns
    """

    # Table/ProTable usage
    TABLE_PATTERN = re.compile(
        r'<(Table|ProTable|EditableProTable|DragSortTable)\b',
        re.MULTILINE
    )

    # Column definition
    COLUMNS_DEF = re.compile(
        r'(?:const|let|var)\s+(\w*[Cc]olumns?\w*)\s*(?::\s*[\w<>\[\]]+\s*)?=\s*\[',
        re.MULTILINE
    )

    # Individual column features
    COLUMN_FEATURES = {
        'sorter': 'sorting',
        'filters': 'filtering',
        'filterDropdown': 'filtering',
        'onFilter': 'filtering',
        'render': 'custom_render',
        'fixed': 'fixed_columns',
        'ellipsis': 'ellipsis',
        'editable': 'editable',
        'valueType': 'pro_value_type',
    }

    # Form pattern
    FORM_PATTERN = re.compile(
        r'<Form\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # Form.Item pattern
    FORM_ITEM_PATTERN = re.compile(
        r'<Form\.Item\b',
        re.MULTILINE
    )

    # Form layout detection
    FORM_LAYOUT = re.compile(
        r'layout\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Modal/Drawer pattern
    MODAL_PATTERN = re.compile(
        r'<(Modal|Drawer)\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # Modal static methods
    MODAL_STATIC = re.compile(
        r'Modal\.(confirm|info|success|error|warning|destroyAll)\s*\(',
        re.MULTILINE
    )

    # Menu pattern
    MENU_PATTERN = re.compile(
        r'<Menu\b([^>]*?)(?:>|/>)',
        re.MULTILINE | re.DOTALL
    )

    # Menu items definition
    MENU_ITEMS_DEF = re.compile(
        r'(?:const|let|var)\s+(\w*[Ii]tems?\w*|menuItems?)\s*(?::\s*[\w<>\[\]]+\s*)?=\s*\[',
        re.MULTILINE
    )

    # Upload pattern
    UPLOAD_PATTERN = re.compile(
        r'<(Upload|Dragger)\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Ant Design API pattern information from source code."""
        result = {
            'tables': [],
            'forms': [],
            'modals': [],
            'menus': [],
        }

        if not content or not content.strip():
            return result

        # ── Table patterns ────────────────────────────────────────
        for match in self.TABLE_PATTERN.finditer(content):
            table_type = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            context_end = min(match.start() + 3000, len(content))
            context = content[match.start():context_end]

            # Count columns from columns prop or nearby columns definition
            col_count = 0
            for col_match in self.COLUMNS_DEF.finditer(content):
                col_start = col_match.start()
                col_end = min(col_start + 5000, len(content))
                col_block = content[col_start:col_end]
                col_count = col_block.count("title:") + col_block.count("'title'") + col_block.count('"title"')
                break

            result['tables'].append(AntdTableInfo(
                name=table_type,
                file=file_path,
                line_number=line_num,
                table_type=table_type,
                column_count=col_count,
                has_sorting='sorter' in context or 'sortOrder' in context,
                has_filtering='filters' in context or 'onFilter' in context or 'filterDropdown' in context,
                has_pagination='pagination' in context,
                has_row_selection='rowSelection' in context,
                has_expandable='expandable' in context or 'expandedRowRender' in context,
                has_server_side='request' in context or 'onTableChange' in context,
                has_virtual_scroll='virtual' in context or 'scroll' in context,
                has_custom_render='render' in context,
            ))

        # ── Form patterns ─────────────────────────────────────────
        for match in self.FORM_PATTERN.finditer(content):
            props = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Detect layout
            layout_match = self.FORM_LAYOUT.search(props)
            layout = layout_match.group(1) if layout_match else 'horizontal'

            # Count Form.Item
            context_end = min(match.start() + 5000, len(content))
            context = content[match.start():context_end]
            field_count = len(self.FORM_ITEM_PATTERN.findall(context))

            result['forms'].append(AntdFormPatternInfo(
                name='Form',
                file=file_path,
                line_number=line_num,
                form_layout=layout,
                has_validation='rules' in context or 'required' in context,
                has_dependencies='dependencies' in context or 'shouldUpdate' in context,
                has_dynamic_fields='Form.List' in context or 'add(' in context,
                has_initial_values='initialValues' in context,
                field_count=field_count,
            ))

        # ── Modal/Drawer patterns ──────────────────────────────────
        for match in self.MODAL_PATTERN.finditer(content):
            modal_type = match.group(1).lower()
            props = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            context_end = min(match.start() + 2000, len(content))
            context = content[match.start():context_end]

            result['modals'].append(AntdModalPatternInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                modal_type=modal_type,
                has_form='<Form' in context or 'Form.Item' in context,
                has_async_close='confirmLoading' in props or 'onOk' in props,
                has_footer='footer' in props,
                is_responsive='width' in props and '%' in props,
            ))

        # Modal static methods
        for match in self.MODAL_STATIC.finditer(content):
            method = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            result['modals'].append(AntdModalPatternInfo(
                name=f'Modal.{method}',
                file=file_path,
                line_number=line_num,
                modal_type=method,
            ))

        # ── Menu patterns ──────────────────────────────────────────
        for match in self.MENU_PATTERN.finditer(content):
            props = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            context_end = min(match.start() + 3000, len(content))
            context = content[match.start():context_end]

            # Detect menu mode
            mode_match = re.search(r'mode\s*=\s*["\'](\w+)["\']', props)
            menu_type = mode_match.group(1) if mode_match else 'vertical'

            # Count items
            item_count = context.count('<Menu.Item') + context.count("label:")
            has_submenu = 'SubMenu' in context or 'children:' in context
            has_icons = 'icon' in context.lower()
            has_groups = 'ItemGroup' in context or 'group' in context.lower()
            is_collapsible = 'collapsed' in context.lower() or 'collapsible' in context.lower()

            result['menus'].append(AntdMenuPatternInfo(
                name='Menu',
                file=file_path,
                line_number=line_num,
                menu_type=menu_type,
                item_count=item_count,
                has_submenu=has_submenu,
                has_icons=has_icons,
                has_groups=has_groups,
                is_collapsible=is_collapsible,
            ))

        return result
