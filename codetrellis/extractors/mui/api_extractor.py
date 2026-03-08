"""
MUI API Extractor for CodeTrellis

Extracts Material UI advanced API patterns from React/TypeScript source code.
Covers MUI v4.x through v6.x advanced component patterns:
- DataGrid column definitions and features (sorting, filtering, pagination)
- Form patterns (controlled forms, validation, multi-step)
- Dialog patterns (confirmation, form dialogs, full-screen)
- Navigation patterns (Drawer + AppBar, Tabs, Breadcrumbs, Stepper)
- MUI X advanced features (tree views, date pickers, charts)
- System utility patterns (responsive values, breakpoint helpers)
- Snackbar/notification patterns
- Table patterns (sorting, pagination, selection)

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MuiDataGridInfo:
    """Information about MUI DataGrid usage."""
    name: str = ""               # Variable name or component reference
    file: str = ""
    line_number: int = 0
    grid_type: str = ""          # DataGrid, DataGridPro, DataGridPremium
    column_count: int = 0
    column_names: List[str] = field(default_factory=list)
    has_sorting: bool = False
    has_filtering: bool = False
    has_pagination: bool = False
    has_row_selection: bool = False
    has_cell_editing: bool = False
    has_row_grouping: bool = False   # Pro/Premium
    has_tree_data: bool = False      # Pro/Premium
    has_aggregation: bool = False    # Premium
    has_custom_toolbar: bool = False
    has_custom_footer: bool = False
    has_server_side: bool = False    # Server-side data loading
    api_ref_used: bool = False       # useGridApiRef


@dataclass
class MuiFormPatternInfo:
    """Information about MUI form patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    pattern_type: str = ""       # controlled, uncontrolled, validation, multi-step
    input_components: List[str] = field(default_factory=list)
    has_validation: bool = False
    has_form_control: bool = False
    has_helper_text: bool = False
    has_error_state: bool = False
    integration: str = ""        # react-hook-form, formik, native


@dataclass
class MuiDialogPatternInfo:
    """Information about MUI dialog patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    dialog_type: str = ""        # confirmation, form, full-screen, responsive
    has_title: bool = False
    has_actions: bool = False
    has_content_text: bool = False
    has_transition: bool = False
    has_close_handler: bool = False
    is_responsive: bool = False


@dataclass
class MuiNavigationInfo:
    """Information about MUI navigation patterns."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    pattern_type: str = ""       # drawer, appbar, tabs, breadcrumbs, stepper, bottom-nav
    is_responsive: bool = False
    has_mini_variant: bool = False   # Drawer mini variant
    has_permanent: bool = False      # Drawer permanent
    has_swipeable: bool = False      # SwipeableDrawer
    tab_count: int = 0
    step_count: int = 0


class MuiApiExtractor:
    """
    Extracts MUI advanced API patterns from source code.

    Detects:
    - DataGrid configurations with column defs, features, and API refs
    - Form patterns with validation and state management
    - Dialog patterns (confirmation, form, responsive)
    - Navigation patterns (Drawer, AppBar, Tabs, Stepper, Breadcrumbs)
    - Advanced MUI X usage patterns
    """

    # DataGrid column definition pattern
    DATAGRID_COLUMNS = re.compile(
        r"(?:const|let|var)\s+(\w*[Cc]olumns?\w*)\s*(?::\s*GridColDef\[\]\s*)?=\s*\[",
        re.MULTILINE
    )

    # DataGrid component usage
    DATAGRID_USAGE = re.compile(
        r"<(DataGrid|DataGridPro|DataGridPremium)\s",
        re.MULTILINE
    )

    # Dialog patterns
    DIALOG_PATTERN = re.compile(
        r"<Dialog\s+[^>]*>",
        re.MULTILINE
    )

    # Drawer patterns
    DRAWER_PATTERN = re.compile(
        r"<(Drawer|SwipeableDrawer)\s+[^>]*>",
        re.MULTILINE
    )

    # Tabs patterns
    TABS_PATTERN = re.compile(
        r"<Tabs\s+[^>]*>",
        re.MULTILINE
    )

    # Stepper patterns
    STEPPER_PATTERN = re.compile(
        r"<(Stepper|MobileStepper)\s+[^>]*>",
        re.MULTILINE
    )

    # AppBar patterns
    APPBAR_PATTERN = re.compile(
        r"<AppBar\s+[^>]*>",
        re.MULTILINE
    )

    # Form pattern detection
    FORM_CONTROL_PATTERN = re.compile(
        r"<FormControl\s+[^>]*>",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the MUI API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all MUI API patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'data_grids', 'forms', 'dialogs', 'navigations'
        """
        data_grids: List[MuiDataGridInfo] = []
        forms: List[MuiFormPatternInfo] = []
        dialogs: List[MuiDialogPatternInfo] = []
        navigations: List[MuiNavigationInfo] = []

        # ── DataGrid ─────────────────────────────────────────────
        for match in self.DATAGRID_USAGE.finditer(content):
            grid_type = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Look for features in surrounding context
            context = content[max(0, match.start() - 200):match.start() + 1000]

            grid_info = MuiDataGridInfo(
                name=grid_type,
                file=file_path,
                line_number=line_number,
                grid_type=grid_type,
                has_sorting=bool(re.search(r'sortModel|onSortModelChange|sortable', context)),
                has_filtering=bool(re.search(r'filterModel|onFilterModelChange|filterable', context)),
                has_pagination=bool(re.search(r'paginationModel|pageSizeOptions|pagination', context)),
                has_row_selection=bool(re.search(r'rowSelectionModel|checkboxSelection|onRowSelectionModelChange', context)),
                has_cell_editing=bool(re.search(r'processRowUpdate|onCellEditStart|editMode', context)),
                has_row_grouping=bool(re.search(r'rowGrouping|groupingColDef', context)),
                has_tree_data=bool(re.search(r'treeData|getTreeDataPath', context)),
                has_aggregation=bool(re.search(r'aggregation|aggregationModel', context)),
                has_custom_toolbar=bool(re.search(r'Toolbar|GridToolbar|slots.*toolbar', context, re.IGNORECASE)),
                has_custom_footer=bool(re.search(r'Footer|GridFooter|slots.*footer', context, re.IGNORECASE)),
                has_server_side=bool(re.search(r'rowCount|onPaginationModelChange|loading|serverSide', context)),
                api_ref_used=bool(re.search(r'apiRef|useGridApiRef', context)),
            )

            # Try to find column definitions
            col_match = self.DATAGRID_COLUMNS.search(content)
            if col_match:
                col_body = self._extract_array_body(content, col_match.end() - 1)
                if col_body:
                    field_names = re.findall(r"field\s*:\s*['\"](\w+)['\"]", col_body)
                    grid_info.column_count = len(field_names)
                    grid_info.column_names = field_names[:30]

            data_grids.append(grid_info)

        # ── Forms ────────────────────────────────────────────────
        form_controls = list(self.FORM_CONTROL_PATTERN.finditer(content))
        if form_controls:
            # Aggregate form info
            line_number = content[:form_controls[0].start()].count('\n') + 1
            input_comps = []
            for comp_name in ['TextField', 'Select', 'Autocomplete', 'Checkbox',
                               'Radio', 'Switch', 'Slider', 'Rating', 'DatePicker']:
                if f'<{comp_name}' in content:
                    input_comps.append(comp_name)

            has_validation = bool(re.search(r'\berror\s*[=:]|\bhelperText\s*[=:].*error', content))
            has_helper = bool(re.search(r'<FormHelperText|helperText\s*=', content))

            # Detect form integration
            integration = ''
            if 'useForm' in content or 'Controller' in content:
                integration = 'react-hook-form'
            elif 'Formik' in content or 'useFormik' in content:
                integration = 'formik'
            elif 'handleSubmit' in content or 'onChange' in content:
                integration = 'native'

            forms.append(MuiFormPatternInfo(
                name='form',
                file=file_path,
                line_number=line_number,
                pattern_type='controlled' if 'value=' in content or 'value =' in content else 'uncontrolled',
                input_components=input_comps[:20],
                has_validation=has_validation,
                has_form_control=True,
                has_helper_text=has_helper,
                has_error_state=bool(re.search(r'\berror\b', content)),
                integration=integration,
            ))

        # ── Dialogs ──────────────────────────────────────────────
        for match in self.DIALOG_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 800]

            dialog_type = 'standard'
            if 'fullScreen' in context:
                dialog_type = 'full-screen'
            elif 'maxWidth' in context and ('sm' in context or 'xs' in context):
                dialog_type = 'responsive'
            elif 'onConfirm' in context or 'handleConfirm' in context:
                dialog_type = 'confirmation'
            elif '<TextField' in context or '<FormControl' in context:
                dialog_type = 'form'

            dialogs.append(MuiDialogPatternInfo(
                name='Dialog',
                file=file_path,
                line_number=line_number,
                dialog_type=dialog_type,
                has_title='<DialogTitle' in context or 'DialogTitle' in context,
                has_actions='<DialogActions' in context,
                has_content_text='<DialogContentText' in context,
                has_transition=bool(re.search(r'Transition|Slide|Fade|Grow|Zoom', context)),
                has_close_handler=bool(re.search(r'onClose|handleClose', context)),
                is_responsive='fullWidth' in context or 'fullScreen' in context,
            ))

        # ── Navigation ───────────────────────────────────────────
        # Drawer
        for match in self.DRAWER_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            navigations.append(MuiNavigationInfo(
                name=comp_name,
                file=file_path,
                line_number=line_number,
                pattern_type='drawer',
                is_responsive=bool(re.search(r'useMediaQuery|variant.*temporary.*permanent', context)),
                has_mini_variant='variant="permanent"' in context and 'width' in context,
                has_permanent='permanent' in context,
                has_swipeable=comp_name == 'SwipeableDrawer',
            ))

        # Tabs
        for match in self.TABS_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            # Count Tab children
            tab_count = content.count('<Tab ')

            navigations.append(MuiNavigationInfo(
                name='Tabs',
                file=file_path,
                line_number=line_number,
                pattern_type='tabs',
                tab_count=tab_count,
            ))

        # Stepper
        for match in self.STEPPER_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            step_count = content.count('<Step ')

            navigations.append(MuiNavigationInfo(
                name=comp_name,
                file=file_path,
                line_number=line_number,
                pattern_type='stepper',
                step_count=step_count,
            ))

        # AppBar
        for match in self.APPBAR_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            navigations.append(MuiNavigationInfo(
                name='AppBar',
                file=file_path,
                line_number=line_number,
                pattern_type='appbar',
                is_responsive=bool(re.search(r'useMediaQuery|useScrollTrigger', context)),
            ))

        return {
            'data_grids': data_grids,
            'forms': forms,
            'dialogs': dialogs,
            'navigations': navigations,
        }

    def _extract_array_body(self, content: str, start: int, max_chars: int = 5000) -> str:
        """Extract array body from [ to matching ]."""
        if start >= len(content) or content[start] != '[':
            return ""
        depth = 0
        result = []
        for ch in content[start:start + max_chars]:
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    break
            result.append(ch)
        return ''.join(result)
