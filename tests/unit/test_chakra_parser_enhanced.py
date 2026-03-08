"""
Tests for Chakra UI extractors and EnhancedChakraParser.

Part of CodeTrellis v4.38 Chakra UI Framework Support.
Tests cover:
- Component extraction (core components, custom wrappers, sub-components)
- Theme extraction (extendTheme, createSystem, tokens, semantic tokens, recipes)
- Hook extraction (useDisclosure, useColorMode, useToast, custom hooks)
- Style extraction (style props, sx prop, responsive patterns, pseudo props)
- API extraction (Form, Modal, Toast, Menu)
- Chakra parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.chakra_parser_enhanced import (
    EnhancedChakraParser,
    ChakraParseResult,
)
from codetrellis.extractors.chakra import (
    ChakraComponentExtractor,
    ChakraThemeExtractor,
    ChakraHookExtractor,
    ChakraStyleExtractor,
    ChakraApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedChakraParser()


@pytest.fixture
def component_extractor():
    return ChakraComponentExtractor()


@pytest.fixture
def theme_extractor():
    return ChakraThemeExtractor()


@pytest.fixture
def hook_extractor():
    return ChakraHookExtractor()


@pytest.fixture
def style_extractor():
    return ChakraStyleExtractor()


@pytest.fixture
def api_extractor():
    return ChakraApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestChakraComponentExtractor:
    """Tests for ChakraComponentExtractor."""

    def test_core_component_imports(self, component_extractor):
        code = '''
import { Box, Button, Heading, Text, Input } from '@chakra-ui/react';

function App() {
    return (
        <Box p={4}>
            <Heading>Title</Heading>
            <Text>Description</Text>
            <Input placeholder="Enter text" />
            <Button colorScheme="blue">Submit</Button>
        </Box>
    );
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Box' in names
        assert 'Button' in names
        assert 'Heading' in names
        assert 'Text' in names
        assert 'Input' in names
        assert len(components) >= 5

    def test_layout_components(self, component_extractor):
        code = '''
import { VStack, HStack, Flex, Grid, SimpleGrid, Container } from '@chakra-ui/react';

function Layout() {
    return (
        <Container maxW="container.xl">
            <VStack spacing={4}>
                <HStack justify="space-between">
                    <Flex align="center" />
                </HStack>
                <SimpleGrid columns={3} spacing={6} />
                <Grid templateColumns="repeat(3, 1fr)" />
            </VStack>
        </Container>
    );
}
'''
        result = component_extractor.extract(code, "Layout.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'VStack' in names
        assert 'HStack' in names
        assert 'Flex' in names
        assert 'Container' in names

    def test_sub_component_detection(self, component_extractor):
        code = '''
import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody } from '@chakra-ui/react';

function MyModal() {
    return (
        <Modal isOpen={true} onClose={() => {}}>
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Title</ModalHeader>
                <ModalBody>Content</ModalBody>
            </ModalContent>
        </Modal>
    );
}
'''
        result = component_extractor.extract(code, "Modal.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Modal' in names

    def test_chakra_factory_detection(self, component_extractor):
        code = '''
import { chakra } from '@chakra-ui/react';

const StyledVideo = chakra('video');
const StyledSection = chakra('section', {
    baseStyle: { py: 8 },
});

function App() {
    return (
        <chakra.div display="flex" gap={4}>
            <StyledVideo src="/demo.mp4" w="full" />
            <chakra.span color="gray.500">Caption</chakra.span>
        </chakra.div>
    );
}
'''
        result = component_extractor.extract(code, "Styled.tsx")
        custom = result.get('custom_components', [])
        names = [c.name for c in custom]
        assert 'StyledVideo' in names or len(custom) >= 1

    def test_form_components(self, component_extractor):
        code = '''
import { FormControl, FormLabel, FormErrorMessage, Input, Button } from '@chakra-ui/react';

function LoginForm() {
    return (
        <form>
            <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input type="email" />
                <FormErrorMessage>Email is required</FormErrorMessage>
            </FormControl>
            <Button type="submit">Login</Button>
        </form>
    );
}
'''
        result = component_extractor.extract(code, "Login.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'FormControl' in names
        assert 'Input' in names
        assert 'Button' in names

    def test_empty_content(self, component_extractor):
        result = component_extractor.extract("", "empty.tsx")
        assert result.get('components', []) == []
        assert result.get('custom_components', []) == []

    def test_non_chakra_content(self, component_extractor):
        code = '''
function App() {
    return <div>Hello World</div>;
}
'''
        result = component_extractor.extract(code, "plain.tsx")
        assert result.get('components', []) == []


# ═══════════════════════════════════════════════════════════════════
# Theme Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestChakraThemeExtractor:
    """Tests for ChakraThemeExtractor."""

    def test_extend_theme_v1_v2(self, theme_extractor):
        code = '''
import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
    colors: {
        brand: {
            50: '#f0e4ff',
            500: '#7928ca',
            900: '#1a0033',
        },
    },
    fonts: {
        heading: 'Inter, sans-serif',
        body: 'Inter, sans-serif',
    },
});

export default theme;
'''
        result = theme_extractor.extract(code, "theme.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert any(t.method == 'extendTheme' for t in themes)

    def test_create_system_v3(self, theme_extractor):
        code = '''
import { createSystem, defineConfig } from '@chakra-ui/react';

const config = defineConfig({
    theme: {
        tokens: {
            colors: {
                brand: { value: '#7928ca' },
            },
        },
        semanticTokens: {
            colors: {
                primary: { value: '{colors.brand}' },
            },
        },
    },
});

export const system = createSystem(config);
'''
        result = theme_extractor.extract(code, "system.ts")
        themes = result.get('themes', [])
        assert len(themes) >= 1
        assert any(t.method == 'createSystem' for t in themes)

    def test_semantic_tokens_detection(self, theme_extractor):
        code = '''
const theme = extendTheme({
    semanticTokens: {
        colors: {
            'bg.surface': { default: 'white', _dark: 'gray.800' },
            'text.primary': { default: 'gray.900', _dark: 'white' },
        },
    },
});
'''
        result = theme_extractor.extract(code, "theme.ts")
        semantic = result.get('semantic_tokens', [])
        assert len(semantic) >= 1

    def test_recipe_detection_v3(self, theme_extractor):
        code = '''
import { defineRecipe, defineSlotRecipe } from '@chakra-ui/react';

const buttonRecipe = defineRecipe({
    base: { fontWeight: 'bold' },
    variants: {
        visual: {
            solid: { bg: 'brand.500', color: 'white' },
            outline: { border: '2px solid' },
        },
    },
});

const cardSlotRecipe = defineSlotRecipe({
    slots: ['root', 'header', 'body'],
    base: {
        root: { borderRadius: 'lg' },
    },
});
'''
        result = theme_extractor.extract(code, "recipes.ts")
        styles = result.get('component_styles', [])
        assert len(styles) >= 1
        assert any(s.is_recipe for s in styles)

    def test_empty_content(self, theme_extractor):
        result = theme_extractor.extract("", "empty.ts")
        assert result.get('themes', []) == []


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestChakraHookExtractor:
    """Tests for ChakraHookExtractor."""

    def test_disclosure_hook(self, hook_extractor):
        code = '''
import { useDisclosure } from '@chakra-ui/react';

function App() {
    const { isOpen, onOpen, onClose } = useDisclosure();
    return <Button onClick={onOpen}>Open</Button>;
}
'''
        result = hook_extractor.extract(code, "App.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useDisclosure' in names

    def test_color_mode_hook(self, hook_extractor):
        code = '''
import { useColorMode, useColorModeValue } from '@chakra-ui/react';

function ThemeToggle() {
    const { colorMode, toggleColorMode } = useColorMode();
    const bg = useColorModeValue('white', 'gray.800');
    return <Box bg={bg}><Button onClick={toggleColorMode}>Toggle</Button></Box>;
}
'''
        result = hook_extractor.extract(code, "ThemeToggle.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useColorMode' in names
        assert 'useColorModeValue' in names

    def test_media_hooks(self, hook_extractor):
        code = '''
import { useBreakpointValue, useMediaQuery } from '@chakra-ui/react';

function Responsive() {
    const variant = useBreakpointValue({ base: 'sm', md: 'md', lg: 'lg' });
    const [isDesktop] = useMediaQuery('(min-width: 1024px)');
    return <Box>{variant}</Box>;
}
'''
        result = hook_extractor.extract(code, "Responsive.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useBreakpointValue' in names
        assert 'useMediaQuery' in names

    def test_toast_hook(self, hook_extractor):
        code = '''
import { useToast } from '@chakra-ui/react';

function SaveButton() {
    const toast = useToast();
    const handleSave = () => {
        toast({ title: 'Saved!', status: 'success' });
    };
    return <Button onClick={handleSave}>Save</Button>;
}
'''
        result = hook_extractor.extract(code, "Save.tsx")
        hooks = result.get('hook_usages', [])
        names = [h.hook_name for h in hooks]
        assert 'useToast' in names

    def test_custom_hook_detection(self, hook_extractor):
        code = '''
import { useDisclosure, useColorMode } from '@chakra-ui/react';

function useThemeDrawer() {
    const { isOpen, onOpen, onClose } = useDisclosure();
    const { colorMode } = useColorMode();
    return { isOpen, onOpen, onClose, colorMode };
}
'''
        result = hook_extractor.extract(code, "hooks.ts")
        custom = result.get('custom_hooks', [])
        names = [c.name for c in custom]
        assert 'useThemeDrawer' in names

    def test_empty_content(self, hook_extractor):
        result = hook_extractor.extract("", "empty.ts")
        assert result.get('hook_usages', []) == []


# ═══════════════════════════════════════════════════════════════════
# Style Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestChakraStyleExtractor:
    """Tests for ChakraStyleExtractor."""

    def test_style_props_detection(self, style_extractor):
        code = '''
import { Box, Text } from '@chakra-ui/react';

function Card() {
    return (
        <Box bg="gray.100" p={4} borderRadius="lg" shadow="md" w="full">
            <Text color="gray.700" fontSize="md">Content</Text>
        </Box>
    );
}
'''
        result = style_extractor.extract(code, "Card.tsx")
        props = result.get('style_props', [])
        assert len(props) >= 1

    def test_sx_prop_detection(self, style_extractor):
        code = '''
import { Box } from '@chakra-ui/react';

function Styled() {
    return (
        <Box sx={{
            '&::before': { content: '""' },
            scrollbarWidth: 'thin',
        }}>
            Content
        </Box>
    );
}
'''
        result = style_extractor.extract(code, "Styled.tsx")
        sx = result.get('sx_usages', [])
        assert len(sx) >= 1

    def test_responsive_array_detection(self, style_extractor):
        code = '''
import { Box } from '@chakra-ui/react';

function Responsive() {
    return (
        <Box
            fontSize={['sm', 'md', 'lg']}
            p={[2, 4, 6, 8]}
            w={['100%', '50%', '33%']}
        >
            Content
        </Box>
    );
}
'''
        result = style_extractor.extract(code, "Responsive.tsx")
        responsive = result.get('responsive_patterns', [])
        assert len(responsive) >= 1

    def test_responsive_object_detection(self, style_extractor):
        code = '''
import { Box } from '@chakra-ui/react';

function Responsive() {
    return (
        <Box w={{ base: '100%', md: '50%', lg: '33%' }}>
            Content
        </Box>
    );
}
'''
        result = style_extractor.extract(code, "Responsive.tsx")
        responsive = result.get('responsive_patterns', [])
        assert len(responsive) >= 1

    def test_pseudo_prop_detection(self, style_extractor):
        code = '''
import { Button } from '@chakra-ui/react';

function HoverButton() {
    return (
        <Button
            bg="blue.500"
            _hover={{ bg: 'blue.600' }}
            _active={{ bg: 'blue.700' }}
            _disabled={{ opacity: 0.6 }}
        >
            Click
        </Button>
    );
}
'''
        result = style_extractor.extract(code, "Button.tsx")
        props = result.get('style_props', [])
        assert len(props) >= 1

    def test_empty_content(self, style_extractor):
        result = style_extractor.extract("", "empty.tsx")
        assert result.get('style_props', []) == []


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestChakraApiExtractor:
    """Tests for ChakraApiExtractor."""

    def test_form_pattern_detection(self, api_extractor):
        code = '''
import { FormControl, FormLabel, FormErrorMessage, Input, Button } from '@chakra-ui/react';

function LoginForm() {
    return (
        <form>
            <FormControl isRequired isInvalid={!!error}>
                <FormLabel>Email</FormLabel>
                <Input type="email" />
                <FormErrorMessage>Email is required</FormErrorMessage>
            </FormControl>
            <FormControl isRequired>
                <FormLabel>Password</FormLabel>
                <Input type="password" />
            </FormControl>
            <Button type="submit">Login</Button>
        </form>
    );
}
'''
        result = api_extractor.extract(code, "Login.tsx")
        forms = result.get('forms', [])
        assert len(forms) >= 1
        assert forms[0].form_control_count >= 2
        assert forms[0].has_validation
        assert forms[0].has_required_fields

    def test_form_with_rhf_integration(self, api_extractor):
        code = '''
import { FormControl, Input } from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

function Form() {
    const { register, handleSubmit } = useForm();
    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <FormControl>
                <Input {...register('name')} />
            </FormControl>
        </form>
    );
}
'''
        result = api_extractor.extract(code, "Form.tsx")
        forms = result.get('forms', [])
        assert len(forms) >= 1
        assert forms[0].integration == 'react-hook-form'

    def test_modal_detection(self, api_extractor):
        code = '''
import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody } from '@chakra-ui/react';
import { useDisclosure } from '@chakra-ui/react';

function MyModal() {
    const { isOpen, onClose } = useDisclosure();
    return (
        <Modal isOpen={isOpen} onClose={onClose} size="xl">
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Title</ModalHeader>
                <ModalBody>Content</ModalBody>
            </ModalContent>
        </Modal>
    );
}
'''
        result = api_extractor.extract(code, "Modal.tsx")
        modals = result.get('modals', [])
        assert len(modals) >= 1
        assert modals[0].modal_type == 'modal'
        assert modals[0].is_controlled

    def test_drawer_detection(self, api_extractor):
        code = '''
import { Drawer, DrawerContent, DrawerHeader } from '@chakra-ui/react';

function SideDrawer() {
    return (
        <Drawer placement="right" onClose={onClose} isOpen={isOpen} size="md">
            <DrawerContent>
                <DrawerHeader>Details</DrawerHeader>
            </DrawerContent>
        </Drawer>
    );
}
'''
        result = api_extractor.extract(code, "Drawer.tsx")
        modals = result.get('modals', [])
        assert len(modals) >= 1
        assert modals[0].modal_type == 'drawer'
        assert modals[0].placement == 'right'

    def test_alert_dialog_detection(self, api_extractor):
        code = '''
import { AlertDialog, AlertDialogBody, AlertDialogFooter } from '@chakra-ui/react';

function Confirm() {
    return (
        <AlertDialog isOpen={isOpen} onClose={onClose}>
            <AlertDialogBody>Are you sure?</AlertDialogBody>
            <AlertDialogFooter>
                <Button onClick={onClose}>Cancel</Button>
            </AlertDialogFooter>
        </AlertDialog>
    );
}
'''
        result = api_extractor.extract(code, "Confirm.tsx")
        modals = result.get('modals', [])
        assert len(modals) >= 1
        assert modals[0].modal_type == 'alertDialog'

    def test_toast_use_toast(self, api_extractor):
        code = '''
import { useToast } from '@chakra-ui/react';

function App() {
    const toast = useToast();
    toast({
        title: 'Saved!',
        status: 'success',
        position: 'top-right',
    });
}
'''
        result = api_extractor.extract(code, "App.tsx")
        toasts = result.get('toasts', [])
        assert len(toasts) >= 1
        assert toasts[0].method == 'useToast'

    def test_toast_v3_toaster(self, api_extractor):
        code = '''
import { toaster } from '@chakra-ui/react';

function save() {
    toaster.success({ title: 'Saved!' });
    toaster.error({ title: 'Failed!' });
}
'''
        result = api_extractor.extract(code, "save.ts")
        toasts = result.get('toasts', [])
        assert len(toasts) >= 2
        methods = [t.method for t in toasts]
        assert 'toaster.success' in methods
        assert 'toaster.error' in methods

    def test_menu_detection(self, api_extractor):
        code = '''
import { Menu, MenuButton, MenuList, MenuItem, MenuDivider } from '@chakra-ui/react';

function Actions() {
    return (
        <Menu>
            <MenuButton>Actions</MenuButton>
            <MenuList>
                <MenuItem>Edit</MenuItem>
                <MenuItem>Copy</MenuItem>
                <MenuDivider />
                <MenuItem>Delete</MenuItem>
            </MenuList>
        </Menu>
    );
}
'''
        result = api_extractor.extract(code, "Actions.tsx")
        menus = result.get('menus', [])
        assert len(menus) >= 1
        assert menus[0].item_count >= 3
        assert menus[0].has_divider

    def test_empty_content(self, api_extractor):
        result = api_extractor.extract("", "empty.tsx")
        assert result.get('forms', []) == []
        assert result.get('modals', []) == []
        assert result.get('toasts', []) == []
        assert result.get('menus', []) == []


# ═══════════════════════════════════════════════════════════════════
# EnhancedChakraParser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedChakraParser:
    """Tests for the integrated EnhancedChakraParser."""

    def test_parse_empty_content(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, ChakraParseResult)
        assert result.components == []
        assert result.themes == []
        assert result.hook_usages == []

    def test_is_chakra_file_positive(self, parser):
        code = "import { Box, Button } from '@chakra-ui/react';"
        assert parser.is_chakra_file(code)

    def test_is_chakra_file_ark_ui(self, parser):
        code = "import { Dialog } from '@ark-ui/react';"
        assert parser.is_chakra_file(code)

    def test_is_chakra_file_extend_theme(self, parser):
        code = "const theme = extendTheme({ colors: {} });"
        assert parser.is_chakra_file(code)

    def test_is_chakra_file_create_system(self, parser):
        code = "const system = createSystem(config);"
        assert parser.is_chakra_file(code)

    def test_is_chakra_file_chakra_factory(self, parser):
        code = "const Div = chakra.div;"
        assert parser.is_chakra_file(code)

    def test_is_chakra_file_negative(self, parser):
        code = "import React from 'react'; function App() { return <div>Hello</div>; }"
        assert not parser.is_chakra_file(code)

    def test_is_chakra_file_empty(self, parser):
        assert not parser.is_chakra_file("")

    def test_is_chakra_file_none(self, parser):
        assert not parser.is_chakra_file(None)

    def test_detect_frameworks_core(self, parser):
        code = "import { Box } from '@chakra-ui/react'; import { motion } from 'framer-motion';"
        frameworks = parser._detect_frameworks(code)
        assert 'chakra-ui' in frameworks
        assert 'framer-motion' in frameworks

    def test_detect_frameworks_ark_ui(self, parser):
        code = "import { Dialog } from '@ark-ui/react';"
        frameworks = parser._detect_frameworks(code)
        assert 'ark-ui' in frameworks

    def test_detect_frameworks_panda_css(self, parser):
        code = "import { css } from 'styled-system/css';"
        frameworks = parser._detect_frameworks(code)
        assert 'panda-css' in frameworks

    def test_detect_frameworks_saas_ui(self, parser):
        code = "import { AppShell } from '@saas-ui/react';"
        frameworks = parser._detect_frameworks(code)
        assert 'saas-ui' in frameworks

    def test_detect_chakra_version_v1(self, parser):
        code = '''
import { Box, CSSReset } from '@chakra-ui/core';
'''
        result = parser.parse(code, "app.tsx")
        assert result.chakra_version == 'v1'

    def test_detect_chakra_version_v2(self, parser):
        code = '''
import { Card, CardHeader, CardBody, Show, Hide } from '@chakra-ui/react';

function App() {
    return (
        <Card>
            <CardHeader>Title</CardHeader>
            <CardBody>
                <Show above="md"><p>Desktop</p></Show>
                <Hide above="md"><p>Mobile</p></Hide>
            </CardBody>
        </Card>
    );
}
'''
        result = parser.parse(code, "app.tsx")
        assert result.chakra_version == 'v2'

    def test_detect_chakra_version_v3(self, parser):
        code = '''
import { createSystem, defineConfig } from '@chakra-ui/react';
import { Dialog } from '@ark-ui/react';

const config = defineConfig({
    theme: { tokens: { colors: { brand: { value: '#7928ca' } } } }
});
const system = createSystem(config);
'''
        result = parser.parse(code, "system.ts")
        assert result.chakra_version == 'v3'

    def test_full_parse_integration(self, parser):
        code = '''
import { Box, Button, Heading, useDisclosure, useColorModeValue } from '@chakra-ui/react';
import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody } from '@chakra-ui/react';

function Dashboard() {
    const { isOpen, onOpen, onClose } = useDisclosure();
    const bg = useColorModeValue('white', 'gray.800');

    return (
        <Box bg={bg} p={4} borderRadius="lg">
            <Heading size="md">Dashboard</Heading>
            <Button onClick={onOpen} _hover={{ bg: 'blue.600' }}>Open Modal</Button>

            <Modal isOpen={isOpen} onClose={onClose}>
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Details</ModalHeader>
                    <ModalBody>Content</ModalBody>
                </ModalContent>
            </Modal>
        </Box>
    );
}
'''
        result = parser.parse(code, "Dashboard.tsx")
        assert isinstance(result, ChakraParseResult)
        assert result.file_type == "tsx"

        # Components detected
        assert len(result.components) >= 3
        comp_names = [c.name for c in result.components]
        assert 'Box' in comp_names
        assert 'Button' in comp_names

        # Hooks detected
        assert len(result.hook_usages) >= 2
        hook_names = [h.hook_name for h in result.hook_usages]
        assert 'useDisclosure' in hook_names
        assert 'useColorModeValue' in hook_names

        # Modals detected
        assert len(result.modals) >= 1

        # Frameworks detected
        assert 'chakra-ui' in result.detected_frameworks

        # Features detected
        assert len(result.detected_features) > 0

    def test_file_type_detection(self, parser):
        result_tsx = parser.parse("import { Box } from '@chakra-ui/react';", "app.tsx")
        assert result_tsx.file_type == "tsx"

        result_jsx = parser.parse("import { Box } from '@chakra-ui/react';", "app.jsx")
        assert result_jsx.file_type == "jsx"

        result_ts = parser.parse("import { Box } from '@chakra-ui/react';", "app.ts")
        assert result_ts.file_type == "tsx"

    def test_metadata_flags(self, parser):
        code = '''
import { Box } from '@chakra-ui/react';
import { Dialog } from '@ark-ui/react';
import { css } from 'styled-system/css';

const theme = extendTheme({
    semanticTokens: { colors: { bg: { default: 'white', _dark: 'gray.800' } } },
});

function App() {
    return <Box bg="bg" p={4} w={{ base: '100%', md: '50%' }}>Content</Box>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert result.has_ark_ui
        assert result.has_panda_css

    def test_features_detection_form(self, parser):
        code = '''
import { FormControl, FormLabel, FormErrorMessage, Input, useToast } from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

function Form() {
    const { register, handleSubmit } = useForm();
    const toast = useToast();

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <FormControl isRequired isInvalid={!!error}>
                <FormLabel>Name</FormLabel>
                <Input {...register('name')} />
                <FormErrorMessage>Required</FormErrorMessage>
            </FormControl>
        </form>
    );
}
'''
        result = parser.parse(code, "Form.tsx")
        assert 'form_patterns' in result.detected_features
        assert 'form_validation' in result.detected_features
        assert 'form_react-hook-form' in result.detected_features
