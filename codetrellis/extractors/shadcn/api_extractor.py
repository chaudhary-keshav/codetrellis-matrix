"""
shadcn/ui API Extractor for CodeTrellis

Extracts API-level patterns specific to shadcn/ui:
- Form patterns (react-hook-form + zod schema validation)
- Dialog/Sheet/Drawer overlay patterns
- Toast/Sonner notification patterns
- Command palette / Combobox patterns
- DataTable patterns (@tanstack/react-table)
- Navigation patterns (sidebar, breadcrumb, navigation-menu)

shadcn/ui has strong opinions about certain patterns:
- Forms: Uses react-hook-form with zod validation (FormField + Controller)
- Toast: Two options - custom useToast hook OR sonner library
- DataTable: @tanstack/react-table with shadcn/ui Table component
- Command: Built on cmdk for command palette / combobox
- Dialog: Radix Dialog with preset compositions

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShadcnFormPatternInfo:
    """Information about a shadcn/ui Form pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    has_zod_schema: bool = False       # Uses zod for validation
    has_react_hook_form: bool = False   # Uses react-hook-form
    field_count: int = 0               # Number of FormField instances
    input_types: List[str] = field(default_factory=list)  # Input, Select, Checkbox, etc.
    has_form_message: bool = False     # Uses FormMessage for errors
    has_form_description: bool = False  # Uses FormDescription
    schema_name: str = ""              # Zod schema variable name
    has_server_action: bool = False    # Uses server action for submission


@dataclass
class ShadcnDialogPatternInfo:
    """Information about a shadcn/ui Dialog/Sheet/Drawer pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    dialog_type: str = ""             # dialog, sheet, drawer, alert-dialog
    has_form: bool = False            # Contains a form inside
    has_close_button: bool = False    # Has explicit close button
    is_controlled: bool = False       # Uses open/onOpenChange
    is_responsive: bool = False       # Uses different component on mobile
    trigger_type: str = ""            # button, link, context-menu, etc.
    size: str = ""                    # For Sheet: side (left, right, top, bottom)


@dataclass
class ShadcnToastPatternInfo:
    """Information about a shadcn/ui Toast pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    method: str = ""                  # useToast, sonner, toast()
    has_action: bool = False          # Has action button
    has_description: bool = False     # Has description
    variant: str = ""                 # default, destructive
    position: str = ""               # For sonner: position config


@dataclass
class ShadcnDataTablePatternInfo:
    """Information about a shadcn/ui DataTable pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    has_sorting: bool = False
    has_filtering: bool = False
    has_pagination: bool = False
    has_row_selection: bool = False
    has_column_visibility: bool = False
    has_column_pinning: bool = False
    column_count: int = 0
    has_server_side: bool = False     # Server-side data fetching
    has_toolbar: bool = False         # DataTableToolbar component


class ShadcnApiExtractor:
    """
    Extracts shadcn/ui API-level patterns from React/TypeScript code.

    Detects:
    - Form patterns with react-hook-form + zod
    - Dialog/Sheet/Drawer overlay patterns
    - Toast/Sonner notification patterns
    - Command/Combobox patterns
    - DataTable patterns
    - Navigation patterns
    """

    # Form detection patterns
    FORM_COMPONENT_RE = re.compile(
        r'<Form[\s>]|<FormField[\s>]',
        re.MULTILINE,
    )
    ZOD_SCHEMA_RE = re.compile(
        r"""(?:const|let)\s+(\w+)\s*=\s*z\.object\s*\(""",
        re.MULTILINE,
    )
    REACT_HOOK_FORM_RE = re.compile(
        r"""useForm\s*<""",
        re.MULTILINE,
    )
    FORM_FIELD_RE = re.compile(
        r'<FormField',
        re.MULTILINE,
    )
    FORM_MESSAGE_RE = re.compile(
        r'<FormMessage',
    )
    FORM_DESCRIPTION_RE = re.compile(
        r'<FormDescription',
    )
    SERVER_ACTION_RE = re.compile(
        r"""action\s*=\s*\{[^}]*\}|'use server'""",
        re.MULTILINE,
    )

    # Dialog/Sheet/Drawer patterns
    DIALOG_TYPES = {
        'Dialog': 'dialog',
        'Sheet': 'sheet',
        'Drawer': 'drawer',
        'AlertDialog': 'alert-dialog',
    }
    DIALOG_RE = re.compile(
        r'<(Dialog|Sheet|Drawer|AlertDialog)[\s>]',
        re.MULTILINE,
    )
    CONTROLLED_RE = re.compile(
        r'(?:open|isOpen)\s*=\s*\{',
    )
    SIDE_RE = re.compile(
        r"""side\s*=\s*['"](\w+)['"]""",
    )

    # Toast patterns
    TOAST_HOOK_RE = re.compile(
        r'useToast\s*\(\s*\)',
    )
    TOAST_CALL_RE = re.compile(
        r'toast\s*\(\s*\{',
    )
    SONNER_IMPORT_RE = re.compile(
        r"""from\s+['"]sonner['"]""",
    )
    SONNER_TOAST_RE = re.compile(
        r'(?:toast|sonner)\s*\.\s*(success|error|warning|info|promise|custom|message|loading|dismiss)\s*\(',
        re.MULTILINE,
    )
    SONNER_SIMPLE_RE = re.compile(
        r"""(?<![\w.])toast\s*\(\s*['"]""",
    )

    # DataTable patterns
    DATA_TABLE_RE = re.compile(
        r'useReactTable\s*\(',
        re.MULTILINE,
    )
    COLUMN_DEF_RE = re.compile(
        r"""(?:const|let)\s+(\w*[cC]olumns?\w*)\s*(?::\s*ColumnDef[^=]*)?=\s*\[""",
        re.MULTILINE,
    )
    SORTING_RE = re.compile(
        r'getSortedRowModel|onSortingChange|SortingState',
    )
    FILTERING_RE = re.compile(
        r'getFilteredRowModel|onColumnFiltersChange|ColumnFiltersState',
    )
    PAGINATION_RE = re.compile(
        r'getPaginationRowModel|onPaginationChange|PaginationState',
    )
    ROW_SELECTION_RE = re.compile(
        r'onRowSelectionChange|RowSelectionState|enableRowSelection',
    )
    COLUMN_VISIBILITY_RE = re.compile(
        r'onColumnVisibilityChange|VisibilityState|columnVisibility',
    )

    # Command/Combobox patterns
    COMMAND_RE = re.compile(
        r'<Command[\s>]|<CommandDialog',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract shadcn/ui API patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'forms', 'dialogs', 'toasts', 'data_tables'
        """
        result: Dict[str, Any] = {
            'forms': [],
            'dialogs': [],
            'toasts': [],
            'data_tables': [],
        }

        if not content or not content.strip():
            return result

        # Extract form patterns
        result['forms'] = self._extract_forms(content, file_path)

        # Extract dialog/sheet/drawer patterns
        result['dialogs'] = self._extract_dialogs(content, file_path)

        # Extract toast patterns
        result['toasts'] = self._extract_toasts(content, file_path)

        # Extract data table patterns
        result['data_tables'] = self._extract_data_tables(content, file_path)

        return result

    def _extract_forms(
        self, content: str, file_path: str
    ) -> List[ShadcnFormPatternInfo]:
        """Extract shadcn/ui Form patterns."""
        forms: List[ShadcnFormPatternInfo] = []

        if not self.FORM_COMPONENT_RE.search(content):
            return forms

        # Get component name
        comp_match = re.search(
            r"""(?:function|const)\s+([A-Z]\w*)\s*(?:\(|=)""",
            content,
        )
        name = comp_match.group(1) if comp_match else "UnnamedForm"

        form_info = ShadcnFormPatternInfo(
            name=name,
            file=file_path,
            line_number=1,
        )

        # Zod schema
        zod_match = self.ZOD_SCHEMA_RE.search(content)
        if zod_match:
            form_info.has_zod_schema = True
            form_info.schema_name = zod_match.group(1)

        # React Hook Form
        form_info.has_react_hook_form = bool(
            self.REACT_HOOK_FORM_RE.search(content) or
            'useForm(' in content
        )

        # Count FormFields
        form_info.field_count = len(self.FORM_FIELD_RE.findall(content))

        # Input types used
        input_types = set()
        for comp in ['Input', 'Textarea', 'Select', 'Checkbox', 'Switch',
                      'RadioGroup', 'Slider', 'Calendar', 'DatePicker',
                      'InputOTP', 'Combobox', 'Toggle']:
            if re.search(rf'<{comp}[\s/>]', content):
                input_types.add(comp)
        form_info.input_types = sorted(input_types)

        # FormMessage / FormDescription
        form_info.has_form_message = bool(
            self.FORM_MESSAGE_RE.search(content)
        )
        form_info.has_form_description = bool(
            self.FORM_DESCRIPTION_RE.search(content)
        )

        # Server action
        form_info.has_server_action = bool(
            self.SERVER_ACTION_RE.search(content)
        )

        # Line number from first Form component
        form_match = self.FORM_COMPONENT_RE.search(content)
        if form_match:
            form_info.line_number = content[:form_match.start()].count('\n') + 1

        forms.append(form_info)
        return forms

    def _extract_dialogs(
        self, content: str, file_path: str
    ) -> List[ShadcnDialogPatternInfo]:
        """Extract Dialog/Sheet/Drawer/AlertDialog patterns."""
        dialogs: List[ShadcnDialogPatternInfo] = []

        for match in self.DIALOG_RE.finditer(content):
            comp_name = match.group(1)
            dialog_type = self.DIALOG_TYPES.get(comp_name, 'dialog')
            line_num = content[:match.start()].count('\n') + 1

            # Get component context name
            comp_context = re.search(
                r"""(?:function|const)\s+([A-Z]\w*)""",
                content[:match.start()],
            )
            name = comp_context.group(1) if comp_context else comp_name

            # Check for form inside
            end_tag = f'</{comp_name}>'
            end_idx = content.find(end_tag, match.end())
            body = content[match.start():end_idx] if end_idx > 0 else content[match.start():]

            info = ShadcnDialogPatternInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                dialog_type=dialog_type,
                has_form='<Form' in body or '<form' in body,
                has_close_button=f'{comp_name}Close' in body or 'DialogClose' in body,
                is_controlled=bool(self.CONTROLLED_RE.search(body)),
            )

            # Sheet side
            side_match = self.SIDE_RE.search(body)
            if side_match:
                info.size = side_match.group(1)

            # Responsive dialog (uses both Dialog and Drawer)
            if 'useMediaQuery' in content or 'useMobile' in content or 'useIsMobile' in content:
                if 'Dialog' in content and 'Drawer' in content:
                    info.is_responsive = True

            dialogs.append(info)

        return dialogs

    def _extract_toasts(
        self, content: str, file_path: str
    ) -> List[ShadcnToastPatternInfo]:
        """Extract Toast/Sonner notification patterns."""
        toasts: List[ShadcnToastPatternInfo] = []

        # useToast hook
        if self.TOAST_HOOK_RE.search(content):
            for match in re.finditer(r'toast\s*\(\s*\{', content):
                line_num = content[:match.start()].count('\n') + 1
                # Check for properties
                end = content.find('})', match.start())
                body = content[match.start():end] if end > 0 else ""

                toasts.append(ShadcnToastPatternInfo(
                    name="toast",
                    file=file_path,
                    line_number=line_num,
                    method="useToast",
                    has_action='action' in body,
                    has_description='description' in body,
                    variant='destructive' if 'destructive' in body else 'default',
                ))

        # Sonner toast
        if self.SONNER_IMPORT_RE.search(content):
            for match in self.SONNER_TOAST_RE.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                method_type = match.group(1)
                toasts.append(ShadcnToastPatternInfo(
                    name=f"sonner.{method_type}",
                    file=file_path,
                    line_number=line_num,
                    method="sonner",
                    variant=method_type,
                ))

            # Simple sonner toast calls
            for match in self.SONNER_SIMPLE_RE.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                toasts.append(ShadcnToastPatternInfo(
                    name="sonner.toast",
                    file=file_path,
                    line_number=line_num,
                    method="sonner",
                ))

        return toasts

    def _extract_data_tables(
        self, content: str, file_path: str
    ) -> List[ShadcnDataTablePatternInfo]:
        """Extract DataTable patterns (@tanstack/react-table)."""
        tables: List[ShadcnDataTablePatternInfo] = []

        if not self.DATA_TABLE_RE.search(content) and not self.COLUMN_DEF_RE.search(content):
            return tables

        # Get component name
        comp_match = re.search(
            r"""(?:function|const)\s+([A-Z]\w*Table\w*|[A-Z]\w*)\s*(?:\(|=)""",
            content,
        )
        name = comp_match.group(1) if comp_match else "DataTable"

        info = ShadcnDataTablePatternInfo(
            name=name,
            file=file_path,
            line_number=1,
        )

        # Features
        info.has_sorting = bool(self.SORTING_RE.search(content))
        info.has_filtering = bool(self.FILTERING_RE.search(content))
        info.has_pagination = bool(self.PAGINATION_RE.search(content))
        info.has_row_selection = bool(self.ROW_SELECTION_RE.search(content))
        info.has_column_visibility = bool(
            self.COLUMN_VISIBILITY_RE.search(content)
        )

        # Column count (from columnDef array)
        for col_match in self.COLUMN_DEF_RE.finditer(content):
            # Count accessorKey or id entries
            col_start = col_match.end()
            # Find matching ]
            depth = 1
            idx = col_start
            while idx < len(content) and depth > 0:
                if content[idx] == '[':
                    depth += 1
                elif content[idx] == ']':
                    depth -= 1
                idx += 1
            col_body = content[col_start:idx]
            info.column_count = len(re.findall(
                r'accessorKey|accessorFn|id\s*:', col_body
            ))

        # Toolbar
        info.has_toolbar = bool(
            re.search(r'DataTableToolbar|TableToolbar', content)
        )

        # Server-side
        info.has_server_side = bool(
            re.search(r'manualPagination|manualSorting|manualFiltering', content)
        )

        # Line number
        table_match = self.DATA_TABLE_RE.search(content)
        if table_match:
            info.line_number = content[:table_match.start()].count('\n') + 1

        tables.append(info)
        return tables
