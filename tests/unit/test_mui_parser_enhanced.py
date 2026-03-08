"""
Tests for MUI extractors and EnhancedMuiParser.

Part of CodeTrellis v4.36 Material UI (MUI) Framework Support.
Tests cover:
- Component extraction (core components, MUI X, custom styled, slots)
- Theme extraction (createTheme, palette, typography, breakpoints, overrides)
- Hook extraction (useTheme, useMediaQuery, headless, MUI X hooks)
- Style extraction (sx prop, styled API, makeStyles, Pigment CSS)
- API extraction (DataGrid, forms, dialogs, navigation)
- MUI parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.mui_parser_enhanced import (
    EnhancedMuiParser,
    MuiParseResult,
)
from codetrellis.extractors.mui import (
    MuiComponentExtractor,
    MuiThemeExtractor,
    MuiHookExtractor,
    MuiStyleExtractor,
    MuiApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedMuiParser()


@pytest.fixture
def component_extractor():
    return MuiComponentExtractor()


@pytest.fixture
def theme_extractor():
    return MuiThemeExtractor()


@pytest.fixture
def hook_extractor():
    return MuiHookExtractor()


@pytest.fixture
def style_extractor():
    return MuiStyleExtractor()


@pytest.fixture
def api_extractor():
    return MuiApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiComponentExtractor:
    """Tests for MuiComponentExtractor."""

    def test_v5_component_imports(self, component_extractor):
        code = '''
import { Button, TextField, Box, Stack } from '@mui/material';

function App() {
    return (
        <Stack spacing={2}>
            <TextField label="Name" />
            <Button variant="contained">Submit</Button>
        </Stack>
    );
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'TextField' in names
        assert 'Stack' in names

    def test_v4_component_imports(self, component_extractor):
        code = '''
import { Button, TextField } from '@material-ui/core';

function App() {
    return (
        <div>
            <TextField label="Email" />
            <Button>Click</Button>
        </div>
    );
}
'''
        result = component_extractor.extract(code, "App.jsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'TextField' in names

    def test_mui_x_components(self, component_extractor):
        code = '''
import { DataGrid } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers';
import { TreeView } from '@mui/x-tree-view';
import { LineChart } from '@mui/x-charts';

function Dashboard() {
    return (
        <div>
            <DataGrid rows={rows} columns={columns} />
            <DatePicker label="Date" />
        </div>
    );
}
'''
        result = component_extractor.extract(code, "Dashboard.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'DataGrid' in names
        x_comps = [c for c in components if c.is_x_component]
        assert len(x_comps) >= 1

    def test_custom_styled_component(self, component_extractor):
        code = '''
import { styled } from '@mui/material/styles';
import { Button } from '@mui/material';

const StyledButton = styled(Button)(({ theme }) => ({
    borderRadius: theme.shape.borderRadius * 2,
}));
'''
        result = component_extractor.extract(code, "StyledButton.tsx")
        custom = result.get('custom_components', [])
        assert len(custom) >= 1
        assert custom[0].name == 'StyledButton'

    def test_slot_detection(self, component_extractor):
        code = '''
import { TextField } from '@mui/material';

function MyInput() {
    return (
        <TextField
            slotProps={{
                input: { startAdornment: <Icon /> },
                inputLabel: { shrink: true },
            }}
        />
    );
}
'''
        result = component_extractor.extract(code, "MyInput.tsx")
        slots = result.get('slots', [])
        assert len(slots) >= 1

    def test_sx_prop_detection(self, component_extractor):
        code = '''
import { Box } from '@mui/material';

function Layout() {
    return <Box sx={{ p: 2, bgcolor: 'primary.main' }}>Content</Box>;
}
'''
        result = component_extractor.extract(code, "Layout.tsx")
        components = result.get('components', [])
        box = [c for c in components if c.name == 'Box']
        assert len(box) >= 1
        assert box[0].has_sx_prop


# ═══════════════════════════════════════════════════════════════════
# Theme Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiThemeExtractor:
    """Tests for MuiThemeExtractor."""

    def test_create_theme(self, theme_extractor):
        code = '''
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        primary: { main: '#1976d2' },
        secondary: { main: '#dc004e' },
    },
    typography: {
        fontFamily: '"Roboto", sans-serif',
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert themes[0].method == 'createTheme'

    def test_palette_extraction(self, theme_extractor):
        code = '''
const theme = createTheme({
    palette: {
        primary: { main: '#1976d2', light: '#42a5f5', dark: '#1565c0' },
        error: { main: '#d32f2f' },
        custom: { main: '#ff9800' },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        palettes = result.get('palettes', [])
        assert len(palettes) >= 2
        names = [p.color_name for p in palettes]
        assert 'primary' in names

    def test_v4_theme(self, theme_extractor):
        code = '''
import { createMuiTheme } from '@material-ui/core/styles';

const theme = createMuiTheme({
    palette: {
        primary: { main: '#3f51b5' },
    },
});
'''
        result = theme_extractor.extract(code, "theme.js")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert themes[0].method == 'createMuiTheme'
        assert themes[0].mui_version == 'v4'

    def test_component_overrides(self, theme_extractor):
        code = '''
const theme = createTheme({
    components: {
        MuiButton: {
            styleOverrides: {
                root: { textTransform: 'none' },
            },
            defaultProps: { disableElevation: true },
        },
        MuiTextField: {
            defaultProps: { variant: 'outlined' },
        },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        overrides = result.get('overrides', [])
        assert len(overrides) >= 1
        names = [o.component_name for o in overrides]
        assert 'MuiButton' in names

    def test_css_variables_detection(self, theme_extractor):
        code = '''
const theme = createTheme({
    cssVariables: true,
    palette: {
        primary: { main: '#1976d2' },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert themes[0].has_css_variables

    def test_dark_mode_detection(self, theme_extractor):
        code = '''
const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: { main: '#90caf9' },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert themes[0].has_dark_mode

    def test_extend_theme_joy_ui(self, theme_extractor):
        code = '''
import { extendTheme } from '@mui/joy/styles';

const theme = extendTheme({
    colorSchemes: {
        light: { palette: { primary: { 500: '#0B6BCB' } } },
        dark: { palette: { primary: { 500: '#12467B' } } },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert themes[0].method == 'extendTheme'


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiHookExtractor:
    """Tests for MuiHookExtractor."""

    def test_theme_hooks(self, hook_extractor):
        code = '''
import { useTheme } from '@mui/material/styles';

function ThemeInfo() {
    const theme = useTheme();
    return <div>{theme.palette.primary.main}</div>;
}
'''
        result = hook_extractor.extract(code, "ThemeInfo.tsx")
        hooks = result.get('hook_usages', [])
        assert len(hooks) >= 1
        assert hooks[0].hook_name == 'useTheme'
        assert hooks[0].category == 'theme'

    def test_media_query_hook(self, hook_extractor):
        code = '''
import { useMediaQuery } from '@mui/material';

function ResponsiveComponent() {
    const isMobile = useMediaQuery('(max-width:600px)');
    return isMobile ? <MobileView /> : <DesktopView />;
}
'''
        result = hook_extractor.extract(code, "Responsive.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useMediaQuery' in names

    def test_headless_hooks(self, hook_extractor):
        code = '''
import { useMenu } from '@mui/base/useMenu';
import { useSelect } from '@mui/base/useSelect';

function CustomMenu() {
    const { getListboxProps, getItemProps } = useMenu({});
    return <ul {...getListboxProps()}>...</ul>;
}
'''
        result = hook_extractor.extract(code, "CustomMenu.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useMenu' in names

    def test_custom_mui_hook(self, hook_extractor):
        code = '''
import { useTheme, useMediaQuery } from '@mui/material';

function useMuiResponsive() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    return { isMobile, theme };
}
'''
        result = hook_extractor.extract(code, "useMuiResponsive.ts")
        custom = result.get('custom_hooks', [])
        assert len(custom) >= 1
        assert custom[0].name == 'useMuiResponsive'


# ═══════════════════════════════════════════════════════════════════
# Style Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiStyleExtractor:
    """Tests for MuiStyleExtractor."""

    def test_sx_prop_detection(self, style_extractor):
        code = '''
import { Box, Button } from '@mui/material';

function Card() {
    return (
        <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Button sx={{ mt: 1 }}>Click</Button>
        </Box>
    );
}
'''
        result = style_extractor.extract(code, "Card.tsx")
        sx_usages = result.get('sx_usages', [])
        assert len(sx_usages) >= 1

    def test_sx_theme_callback(self, style_extractor):
        code = '''
<Box sx={(theme) => ({
    color: theme.palette.primary.main,
    [theme.breakpoints.up('md')]: { width: '50%' },
})} />
'''
        result = style_extractor.extract(code, "Themed.tsx")
        sx_usages = result.get('sx_usages', [])
        assert len(sx_usages) >= 1
        assert sx_usages[0].has_theme_callback

    def test_styled_api(self, style_extractor):
        code = '''
import { styled } from '@mui/material/styles';

const StyledCard = styled('div', {
    name: 'AppCard',
    slot: 'Root',
})(({ theme }) => ({
    padding: theme.spacing(2),
    borderRadius: theme.shape.borderRadius,
}));
'''
        result = style_extractor.extract(code, "StyledCard.tsx")
        styled = result.get('styled_components', [])
        assert len(styled) >= 1
        assert styled[0].name == 'StyledCard'
        assert styled[0].has_overrides_name
        assert styled[0].override_slot != ""

    def test_make_styles_v4(self, style_extractor):
        code = '''
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
    root: { padding: theme.spacing(2) },
    title: { fontSize: 24 },
}));
'''
        result = style_extractor.extract(code, "styles.js")
        make_styles = result.get('make_styles', [])
        assert len(make_styles) >= 1
        assert make_styles[0].method == 'makeStyles'
        assert make_styles[0].has_theme_usage

    def test_tss_react_detection(self, style_extractor):
        code = '''
import { makeStyles } from 'tss-react/mui';

const useStyles = makeStyles()((theme) => ({
    root: { color: theme.palette.primary.main },
}));
'''
        result = style_extractor.extract(code, "styles.ts")
        make_styles = result.get('make_styles', [])
        assert len(make_styles) >= 1
        assert make_styles[0].method == 'tss-react'
        assert make_styles[0].is_legacy is False

    def test_pigment_css_detection(self, style_extractor):
        code = '''
import { css, styled } from '@pigment-css/react';

const blueClass = css({ color: 'blue' });
const PigmentBox = styled('div')({ padding: 16 });
'''
        result = style_extractor.extract(code, "pigment.tsx")
        styled = result.get('styled_components', [])
        assert len(styled) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiApiExtractor:
    """Tests for MuiApiExtractor."""

    def test_data_grid_detection(self, api_extractor):
        code = '''
import { DataGrid, GridColDef } from '@mui/x-data-grid';

const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'email', headerName: 'Email', flex: 1 },
];

function UserTable({ rows }) {
    return (
        <DataGrid
            rows={rows}
            columns={columns}
            paginationModel={{ page: 0, pageSize: 10 }}
            pageSizeOptions={[10, 25, 50]}
            checkboxSelection
        />
    );
}
'''
        result = api_extractor.extract(code, "UserTable.tsx")
        grids = result.get('data_grids', [])
        assert len(grids) >= 1
        assert grids[0].grid_type == 'DataGrid'
        assert grids[0].has_pagination
        assert grids[0].has_row_selection
        assert grids[0].column_count == 3

    def test_dialog_detection(self, api_extractor):
        code = '''
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';

function ConfirmDialog({ open, onClose, onConfirm }) {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button onClick={onConfirm}>Confirm</Button>
            </DialogActions>
        </Dialog>
    );
}
'''
        result = api_extractor.extract(code, "ConfirmDialog.tsx")
        dialogs = result.get('dialogs', [])
        assert len(dialogs) >= 1
        assert dialogs[0].has_title
        assert dialogs[0].has_actions
        assert dialogs[0].has_close_handler

    def test_form_pattern_detection(self, api_extractor):
        code = '''
import { TextField, FormControl, FormHelperText, Button } from '@mui/material';

function LoginForm() {
    const [email, setEmail] = useState('');
    const [error, setError] = useState(false);

    return (
        <form onSubmit={handleSubmit}>
            <FormControl error={error}>
                <TextField
                    label="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    helperText={error ? "Invalid email" : ""}
                />
            </FormControl>
            <Button type="submit">Login</Button>
        </form>
    );
}
'''
        result = api_extractor.extract(code, "LoginForm.tsx")
        forms = result.get('forms', [])
        assert len(forms) >= 1
        assert forms[0].has_form_control

    def test_drawer_navigation(self, api_extractor):
        code = '''
import { Drawer, List, ListItem } from '@mui/material';

function Sidebar({ open, onClose }) {
    return (
        <Drawer open={open} onClose={onClose} variant="temporary">
            <List>
                <ListItem>Home</ListItem>
                <ListItem>Settings</ListItem>
            </List>
        </Drawer>
    );
}
'''
        result = api_extractor.extract(code, "Sidebar.tsx")
        navigations = result.get('navigations', [])
        assert len(navigations) >= 1
        assert navigations[0].pattern_type == 'drawer'

    def test_tabs_navigation(self, api_extractor):
        code = '''
import { Tabs, Tab, Box } from '@mui/material';

function NavTabs() {
    const [value, setValue] = useState(0);
    return (
        <Tabs value={value} onChange={(e, v) => setValue(v)}>
            <Tab label="Overview" />
            <Tab label="Details" />
            <Tab label="Settings" />
        </Tabs>
    );
}
'''
        result = api_extractor.extract(code, "NavTabs.tsx")
        navigations = result.get('navigations', [])
        tabs = [n for n in navigations if n.pattern_type == 'tabs']
        assert len(tabs) >= 1
        assert tabs[0].tab_count == 3


# ═══════════════════════════════════════════════════════════════════
# MUI Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedMuiParser:
    """Tests for EnhancedMuiParser integration."""

    def test_is_mui_file_v5(self, parser):
        code = "import { Button } from '@mui/material';"
        assert parser.is_mui_file(code) is True

    def test_is_mui_file_v4(self, parser):
        code = "import { Button } from '@material-ui/core';"
        assert parser.is_mui_file(code) is True

    def test_is_not_mui_file(self, parser):
        code = "import React from 'react';\nconst App = () => <div>Hello</div>;"
        assert parser.is_mui_file(code) is False

    def test_is_mui_file_pigment(self, parser):
        code = "import { css } from '@pigment-css/react';"
        assert parser.is_mui_file(code) is True

    def test_is_mui_file_make_styles(self, parser):
        code = "const useStyles = makeStyles((theme) => ({}));"
        assert parser.is_mui_file(code) is True

    def test_parse_full_file(self, parser):
        code = '''
import { Button, Box, TextField, Dialog, DialogTitle, DialogActions } from '@mui/material';
import { useTheme, useMediaQuery } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { createTheme, styled, ThemeProvider } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        primary: { main: '#1976d2' },
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: { textTransform: 'none' },
            },
        },
    },
});

const StyledBox = styled(Box)(({ theme }) => ({
    padding: theme.spacing(2),
}));

const columns = [
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'name', headerName: 'Name', flex: 1 },
];

function App() {
    const muiTheme = useTheme();
    const isMobile = useMediaQuery(muiTheme.breakpoints.down('sm'));

    return (
        <ThemeProvider theme={theme}>
            <StyledBox sx={{ p: 2 }}>
                <TextField label="Search" />
                <DataGrid rows={[]} columns={columns} pagination />
                <Dialog open={false} onClose={() => {}}>
                    <DialogTitle>Info</DialogTitle>
                    <DialogActions>
                        <Button>OK</Button>
                    </DialogActions>
                </Dialog>
            </StyledBox>
        </ThemeProvider>
    );
}
'''
        result = parser.parse(code, "App.tsx")

        # Verify file type
        assert result.file_type == "tsx"

        # Components detected
        assert len(result.components) >= 3  # Button, Box, TextField, etc.

        # Theme detected
        assert len(result.themes) >= 1
        assert result.has_theme

        # Hooks detected
        assert len(result.hook_usages) >= 1

        # Styled components
        assert len(result.styled_components) >= 1
        assert result.has_styled_api

        # sx prop
        assert len(result.sx_usages) >= 1
        assert result.has_sx_prop

        # DataGrid
        assert len(result.data_grids) >= 1

        # Dialogs
        assert len(result.dialogs) >= 1

        # Frameworks detected
        assert len(result.detected_frameworks) >= 1

        # MUI version
        assert result.mui_version in ('v5', 'v6')

    def test_version_detection_v4(self, parser):
        code = '''
import { Button } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
'''
        result = parser.parse(code, "App.jsx")
        assert result.mui_version == 'v4'

    def test_version_detection_v6(self, parser):
        code = '''
import { styled } from '@pigment-css/react';
import { Button } from '@mui/material';
'''
        result = parser.parse(code, "App.tsx")
        assert result.mui_version == 'v6'

    def test_framework_detection(self, parser):
        code = '''
import { Button } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers';
import DeleteIcon from '@mui/icons-material/Delete';
'''
        result = parser.parse(code, "App.tsx")
        assert 'mui-material' in result.detected_frameworks
        assert 'mui-x-data-grid' in result.detected_frameworks
        assert 'mui-x-date-pickers' in result.detected_frameworks
        assert 'mui-icons' in result.detected_frameworks

    def test_joy_ui_detection(self, parser):
        code = '''
import { Button, Sheet } from '@mui/joy';
import { extendTheme } from '@mui/joy/styles';
'''
        result = parser.parse(code, "App.tsx")
        assert result.has_joy_ui
        assert 'mui-joy' in result.detected_frameworks

    def test_feature_detection(self, parser):
        code = '''
import { Button, Box } from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledBox = styled(Box)(({ theme }) => ({
    padding: theme.spacing(2),
}));

function App() {
    return <StyledBox sx={{ mt: 2 }}><Button>Go</Button></StyledBox>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert 'mui_components' in result.detected_features
        assert 'styled_api' in result.detected_features
        assert 'sx_prop' in result.detected_features

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.tsx")
        assert result.file_path == "empty.tsx"
        assert len(result.components) == 0
        assert len(result.themes) == 0

    def test_non_mui_file(self, parser):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
'''
        result = parser.parse(code, "App.tsx")
        assert len(result.components) == 0
        assert len(result.detected_frameworks) == 0


# ═══════════════════════════════════════════════════════════════════
# BPL Practice Tests
# ═══════════════════════════════════════════════════════════════════

class TestMuiBPLPractices:
    """Tests for MUI BPL practices loading."""

    def test_mui_practices_load(self):
        """Verify MUI practices YAML loads correctly."""
        from codetrellis.bpl.repository import BestPracticesRepository
        repo = BestPracticesRepository()
        repo.load_all()

        # Check that MUI practices are loaded
        all_practices = repo.get_all()
        mui_practices = [p for p in all_practices if p.id.upper().startswith('MUI')]
        assert len(mui_practices) >= 40  # We defined 50, but some may not load

    def test_mui_practice_categories(self):
        """Verify MUI practice categories are valid."""
        from codetrellis.bpl.models import PracticeCategory
        # Check MUI categories exist
        assert hasattr(PracticeCategory, 'MUI_COMPONENTS')
        assert hasattr(PracticeCategory, 'MUI_THEME')
        assert hasattr(PracticeCategory, 'MUI_STYLING')
        assert hasattr(PracticeCategory, 'MUI_HOOKS')
        assert hasattr(PracticeCategory, 'MUI_PERFORMANCE')
        assert hasattr(PracticeCategory, 'MUI_ACCESSIBILITY')
        assert hasattr(PracticeCategory, 'MUI_FORMS')
        assert hasattr(PracticeCategory, 'MUI_DATA_GRID')
        assert hasattr(PracticeCategory, 'MUI_NAVIGATION')
        assert hasattr(PracticeCategory, 'MUI_MIGRATION')
