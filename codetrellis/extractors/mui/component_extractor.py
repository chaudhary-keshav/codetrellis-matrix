"""
MUI Component Extractor for CodeTrellis

Extracts Material UI component usage from React/TypeScript source code.
Covers MUI v0.x legacy through v6.x, including:
- Core component usage (Box, Typography, Button, Grid, Stack, etc.)
- Data display (DataGrid, Table, List, Card, Chip, Avatar, Badge)
- Layout (Container, Grid, Stack, Box)
- Navigation (AppBar, Drawer, Tabs, BottomNavigation, Breadcrumbs)
- Feedback (Dialog, Snackbar, Alert, Backdrop, Skeleton)
- Input (TextField, Select, Autocomplete, DatePicker, Slider, Switch)
- Custom styled components via styled() API
- Component composition and slot patterns (v5+)
- MUI X advanced components (DataGrid, DatePicker, TreeView, Charts)

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MuiComponentInfo:
    """Information about a MUI component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # @mui/material, @material-ui/core, etc.
    category: str = ""            # layout, input, display, feedback, navigation, surface, data, util
    is_x_component: bool = False  # MUI X (DataGrid, DatePicker, TreeView, Charts)
    props_used: List[str] = field(default_factory=list)
    has_sx_prop: bool = False
    has_slots: bool = False
    slot_names: List[str] = field(default_factory=list)


@dataclass
class MuiCustomComponentInfo:
    """Information about a custom MUI-styled component."""
    name: str
    file: str = ""
    line_number: int = 0
    base_component: str = ""     # The MUI component being customized
    method: str = ""             # styled, makeStyles, withStyles, sx
    has_theme_usage: bool = False
    has_responsive: bool = False
    css_properties: List[str] = field(default_factory=list)


@dataclass
class MuiSlotInfo:
    """Information about MUI component slot usage (v5+)."""
    component_name: str
    slot_name: str
    file: str = ""
    line_number: int = 0
    slot_props_type: str = ""


class MuiComponentExtractor:
    """
    Extracts MUI component usage from React/TypeScript source code.

    Detects:
    - MUI core component imports and usage
    - MUI X advanced component imports (DataGrid, DatePicker, TreeView, Charts)
    - Custom styled components built on MUI
    - Component slot/slotProps patterns (v5+)
    - Component composition patterns
    """

    # MUI component categories
    COMPONENT_CATEGORIES = {
        # Layout
        'Box': 'layout', 'Container': 'layout', 'Grid': 'layout', 'Grid2': 'layout',
        'Stack': 'layout', 'ImageList': 'layout', 'ImageListItem': 'layout',
        'Masonry': 'layout',
        # Input
        'TextField': 'input', 'Select': 'input', 'Autocomplete': 'input',
        'Checkbox': 'input', 'Radio': 'input', 'RadioGroup': 'input',
        'Switch': 'input', 'Slider': 'input', 'Rating': 'input',
        'ToggleButton': 'input', 'ToggleButtonGroup': 'input',
        'Button': 'input', 'IconButton': 'input', 'ButtonGroup': 'input',
        'Fab': 'input', 'LoadingButton': 'input',
        'FormControl': 'input', 'FormLabel': 'input', 'FormHelperText': 'input',
        'FormGroup': 'input', 'FormControlLabel': 'input',
        'InputBase': 'input', 'Input': 'input', 'OutlinedInput': 'input',
        'FilledInput': 'input', 'InputAdornment': 'input', 'InputLabel': 'input',
        # Display
        'Typography': 'display', 'Divider': 'display',
        'Avatar': 'display', 'AvatarGroup': 'display',
        'Badge': 'display', 'Chip': 'display',
        'Icon': 'display', 'SvgIcon': 'display',
        'List': 'display', 'ListItem': 'display', 'ListItemText': 'display',
        'ListItemButton': 'display', 'ListItemIcon': 'display',
        'ListItemAvatar': 'display', 'ListSubheader': 'display',
        'Table': 'display', 'TableBody': 'display', 'TableCell': 'display',
        'TableContainer': 'display', 'TableHead': 'display',
        'TableRow': 'display', 'TablePagination': 'display',
        'TableSortLabel': 'display', 'TableFooter': 'display',
        'Tooltip': 'display', 'Collapse': 'display',
        # Feedback
        'Alert': 'feedback', 'AlertTitle': 'feedback',
        'Dialog': 'feedback', 'DialogTitle': 'feedback',
        'DialogContent': 'feedback', 'DialogActions': 'feedback',
        'DialogContentText': 'feedback',
        'Snackbar': 'feedback', 'SnackbarContent': 'feedback',
        'Backdrop': 'feedback', 'CircularProgress': 'feedback',
        'LinearProgress': 'feedback', 'Skeleton': 'feedback',
        'Modal': 'feedback',
        # Navigation
        'AppBar': 'navigation', 'Toolbar': 'navigation',
        'Drawer': 'navigation', 'SwipeableDrawer': 'navigation',
        'Tabs': 'navigation', 'Tab': 'navigation', 'TabContext': 'navigation',
        'TabList': 'navigation', 'TabPanel': 'navigation',
        'BottomNavigation': 'navigation', 'BottomNavigationAction': 'navigation',
        'Breadcrumbs': 'navigation', 'Link': 'navigation',
        'Menu': 'navigation', 'MenuItem': 'navigation',
        'MenuList': 'navigation',
        'Pagination': 'navigation', 'PaginationItem': 'navigation',
        'SpeedDial': 'navigation', 'SpeedDialAction': 'navigation',
        'SpeedDialIcon': 'navigation',
        'Stepper': 'navigation', 'Step': 'navigation',
        'StepLabel': 'navigation', 'StepButton': 'navigation',
        'StepContent': 'navigation', 'StepConnector': 'navigation',
        'StepIcon': 'navigation', 'MobileStepper': 'navigation',
        # Surface
        'Paper': 'surface', 'Card': 'surface', 'CardContent': 'surface',
        'CardActions': 'surface', 'CardMedia': 'surface',
        'CardHeader': 'surface', 'CardActionArea': 'surface',
        'Accordion': 'surface', 'AccordionSummary': 'surface',
        'AccordionDetails': 'surface', 'AccordionActions': 'surface',
        # Utility
        'CssBaseline': 'utility', 'ScopedCssBaseline': 'utility',
        'GlobalStyles': 'utility', 'NoSsr': 'utility',
        'Portal': 'utility', 'Popover': 'utility', 'Popper': 'utility',
        'ClickAwayListener': 'utility', 'Grow': 'utility',
        'Fade': 'utility', 'Slide': 'utility', 'Zoom': 'utility',
        'Transition': 'utility', 'TransitionGroup': 'utility',
        'ThemeProvider': 'utility', 'StyledEngineProvider': 'utility',
        'CacheProvider': 'utility',
    }

    # MUI X component mapping
    MUI_X_COMPONENTS = {
        'DataGrid': 'data-grid', 'DataGridPro': 'data-grid',
        'DataGridPremium': 'data-grid',
        'GridColDef': 'data-grid', 'GridRenderCellParams': 'data-grid',
        'GridToolbar': 'data-grid', 'GridActionsCellItem': 'data-grid',
        'DatePicker': 'date-picker', 'DateTimePicker': 'date-picker',
        'TimePicker': 'date-picker', 'DateRangePicker': 'date-picker',
        'DateCalendar': 'date-picker', 'StaticDatePicker': 'date-picker',
        'DesktopDatePicker': 'date-picker', 'MobileDatePicker': 'date-picker',
        'LocalizationProvider': 'date-picker',
        'TreeView': 'tree-view', 'SimpleTreeView': 'tree-view',
        'RichTreeView': 'tree-view', 'TreeItem': 'tree-view',
        'TreeItem2': 'tree-view',
        'BarChart': 'charts', 'LineChart': 'charts', 'PieChart': 'charts',
        'ScatterChart': 'charts', 'SparkLineChart': 'charts',
        'Gauge': 'charts', 'ChartsLegend': 'charts',
    }

    # Import source detection patterns
    IMPORT_PATTERNS = [
        # v5+ @mui/* named imports: import { A, B } from '@mui/...'
        re.compile(
            r"import\s+\{\s*([\w\s,]+)\s*\}\s+from\s+['\"](@mui/[\w/\-]+)['\"]",
            re.MULTILINE
        ),
        # v4 @material-ui/* named imports
        re.compile(
            r"import\s+\{\s*([\w\s,]+)\s*\}\s+from\s+['\"](@material-ui/[\w/\-]+)['\"]",
            re.MULTILINE
        ),
        # Default imports: import Button from '@mui/material/Button'
        re.compile(
            r"import\s+(\w+)\s+from\s+['\"](@mui/[\w/\-]+)['\"]",
            re.MULTILINE
        ),
        # Default imports v4
        re.compile(
            r"import\s+(\w+)\s+from\s+['\"](@material-ui/[\w/\-]+)['\"]",
            re.MULTILINE
        ),
        # v0.x legacy imports
        re.compile(
            r"import\s+\{\s*([\w\s,]+)\s*\}\s+from\s+['\"](material-ui[\w/\-]*)['\"]",
            re.MULTILINE
        ),
    ]

    # Styled component patterns
    STYLED_PATTERNS = [
        # styled(Component)(...) or styled('div')(...)
        re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*styled\(\s*['\"]?(\w+)['\"]?\s*\)",
            re.MULTILINE
        ),
    ]

    # Slot/SlotProps patterns (v5+)
    SLOT_PATTERN = re.compile(
        r"<(\w+)\s+[^>]*(?:slots|slotProps|components|componentsProps)\s*=\s*\{",
        re.MULTILINE
    )

    # sx prop pattern
    SX_PATTERN = re.compile(
        r"<(\w+)\s+[^>]*sx\s*=\s*\{",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the MUI component extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all MUI component usage from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components', 'custom_components', 'slots' lists
        """
        components: List[MuiComponentInfo] = []
        custom_components: List[MuiCustomComponentInfo] = []
        slots: List[MuiSlotInfo] = []

        # Track imported MUI components
        imported_components: Dict[str, str] = {}  # name -> import_source

        # Extract imports
        for pattern in self.IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                names_str = match.group(1)
                source = match.group(2)
                names = [n.strip() for n in names_str.split(',') if n.strip()]
                for name in names:
                    # Clean up: remove 'type' keyword if present
                    clean_name = re.sub(r'^\s*type\s+', '', name).strip()
                    if clean_name and clean_name[0].isupper():
                        imported_components[clean_name] = source

        # Extract component usages from JSX
        jsx_pattern = re.compile(r'<(\w+)(\s+[^>]*)?/?>', re.MULTILINE)
        for match in jsx_pattern.finditer(content):
            comp_name = match.group(1)
            props_str = match.group(2) or ""

            # Only track known MUI components
            if comp_name not in imported_components and comp_name not in self.COMPONENT_CATEGORIES and comp_name not in self.MUI_X_COMPONENTS:
                continue

            # Skip if it looks like an HTML element (lowercase)
            if comp_name[0].islower():
                continue

            is_x = comp_name in self.MUI_X_COMPONENTS
            category = self.MUI_X_COMPONENTS.get(comp_name, '') if is_x else self.COMPONENT_CATEGORIES.get(comp_name, '')

            # Extract props
            props = re.findall(r'(\w+)\s*=', props_str)
            has_sx = 'sx' in props

            # Check for slots
            has_slots = bool(re.search(r'(?:slots|slotProps|components|componentsProps)\s*=', props_str))
            slot_names = []
            if has_slots:
                slot_match = re.search(r'slots\s*=\s*\{\s*\{([^}]+)\}\s*\}', props_str)
                if slot_match:
                    slot_names = re.findall(r'(\w+)\s*:', slot_match.group(1))

            line_number = content[:match.start()].count('\n') + 1

            comp_info = MuiComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_number,
                import_source=imported_components.get(comp_name, ''),
                category=category,
                is_x_component=is_x,
                props_used=props[:30],
                has_sx_prop=has_sx,
                has_slots=has_slots,
                slot_names=slot_names[:10],
            )
            components.append(comp_info)

        # Extract custom styled components
        for pattern in self.STYLED_PATTERNS:
            for match in pattern.finditer(content):
                comp_name = match.group(1)
                base_comp = match.group(2)
                line_number = content[:match.start()].count('\n') + 1

                # Check for theme usage in the styled block
                # Look ahead for the function body
                rest = content[match.end():]
                theme_used = bool(re.search(r'theme\s*[.)\[]|theme\s*=>', rest[:500]))
                responsive = bool(re.search(
                    r'theme\.breakpoints|@media|\[theme\.breakpoints',
                    rest[:500]
                ))

                custom_components.append(MuiCustomComponentInfo(
                    name=comp_name,
                    file=file_path,
                    line_number=line_number,
                    base_component=base_comp,
                    method='styled',
                    has_theme_usage=theme_used,
                    has_responsive=responsive,
                ))

        # Extract slot usages
        for match in self.SLOT_PATTERN.finditer(content):
            comp_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            # Try to find slot names
            rest = content[match.end():match.end() + 300]
            slot_name_matches = re.findall(r'(\w+)\s*:', rest[:200])
            for slot_name in slot_name_matches[:5]:
                if slot_name not in ('sx', 'style', 'className', 'ref', 'key', 'id'):
                    slots.append(MuiSlotInfo(
                        component_name=comp_name,
                        slot_name=slot_name,
                        file=file_path,
                        line_number=line_number,
                    ))

        # Deduplicate components by (name, line_number)
        seen = set()
        deduped_components = []
        for c in components:
            key = (c.name, c.line_number)
            if key not in seen:
                seen.add(key)
                deduped_components.append(c)

        return {
            'components': deduped_components,
            'custom_components': custom_components,
            'slots': slots,
        }
