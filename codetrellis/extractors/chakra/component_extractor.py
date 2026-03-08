"""
Chakra UI Component Extractor for CodeTrellis

Extracts Chakra UI component usage from React/TypeScript source code.
Covers Chakra UI v1.x through v3.x (Ark UI), including:
- Layout (Box, Flex, Grid, Stack, Container, Center, Wrap, AspectRatio, SimpleGrid)
- Typography (Heading, Text, Code, Kbd, Mark, Highlight)
- Forms (Input, Select, Checkbox, Radio, Switch, Slider, Textarea,
    NumberInput, PinInput, FormControl, FormLabel, FormHelperText, FormErrorMessage)
- Data Display (Badge, Tag, Stat, Table, Card, List, Accordion, Tabs)
- Feedback (Alert, Toast, Progress, Skeleton, Spinner, CircularProgress)
- Overlay (Modal, Drawer, Popover, Tooltip, AlertDialog, Menu)
- Navigation (Breadcrumb, Link, LinkBox, LinkOverlay, Stepper, Tabs)
- Media (Image, Avatar, Icon, IconButton)
- Disclosure (Accordion, Tabs, Editable, Collapse)
- Custom wrapper components built on Chakra

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChakraComponentInfo:
    """Information about a Chakra UI component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # @chakra-ui/react, @chakra-ui/icons, etc.
    category: str = ""            # layout, forms, data-display, feedback, overlay, navigation, media, typography
    props_used: List[str] = field(default_factory=list)
    has_style_props: bool = False
    has_responsive_props: bool = False
    sub_components: List[str] = field(default_factory=list)  # e.g., Modal.Header, Accordion.Item


@dataclass
class ChakraCustomComponentInfo:
    """Information about a custom component wrapping Chakra UI."""
    name: str
    file: str = ""
    line_number: int = 0
    base_component: str = ""     # The Chakra component being wrapped
    method: str = ""             # wrapper, forwardRef, chakra factory
    has_theme_usage: bool = False
    additional_props: List[str] = field(default_factory=list)


class ChakraComponentExtractor:
    """
    Extracts Chakra UI component usage from React/TypeScript source code.

    Detects:
    - Chakra UI core component imports and usage (70+ components)
    - Custom components wrapping Chakra
    - Component composition (Modal.Header, Accordion.Item, etc.)
    - chakra() factory function usage
    """

    # Chakra UI component categories
    COMPONENT_CATEGORIES = {
        # Layout
        'Box': 'layout', 'Flex': 'layout', 'Grid': 'layout',
        'GridItem': 'layout', 'SimpleGrid': 'layout',
        'Stack': 'layout', 'HStack': 'layout', 'VStack': 'layout',
        'Container': 'layout', 'Center': 'layout', 'Square': 'layout',
        'Circle': 'layout', 'Wrap': 'layout', 'WrapItem': 'layout',
        'AspectRatio': 'layout', 'Spacer': 'layout', 'Divider': 'layout',
        'AbsoluteCenter': 'layout', 'Float': 'layout', 'Bleed': 'layout',

        # Typography
        'Heading': 'typography', 'Text': 'typography', 'Code': 'typography',
        'Kbd': 'typography', 'Mark': 'typography', 'Highlight': 'typography',
        'Em': 'typography', 'Strong': 'typography', 'Blockquote': 'typography',

        # Forms
        'Input': 'forms', 'InputGroup': 'forms', 'InputLeftElement': 'forms',
        'InputRightElement': 'forms', 'InputLeftAddon': 'forms',
        'InputRightAddon': 'forms',
        'Select': 'forms', 'NativeSelect': 'forms',
        'Checkbox': 'forms', 'CheckboxGroup': 'forms',
        'Radio': 'forms', 'RadioGroup': 'forms',
        'Switch': 'forms', 'Slider': 'forms',
        'Textarea': 'forms', 'NumberInput': 'forms',
        'NumberInputField': 'forms', 'NumberInputStepper': 'forms',
        'NumberIncrementStepper': 'forms', 'NumberDecrementStepper': 'forms',
        'PinInput': 'forms', 'PinInputField': 'forms',
        'FormControl': 'forms', 'FormLabel': 'forms',
        'FormHelperText': 'forms', 'FormErrorMessage': 'forms',
        'Editable': 'forms', 'EditablePreview': 'forms',
        'EditableInput': 'forms', 'EditableTextarea': 'forms',
        'Button': 'forms', 'ButtonGroup': 'forms', 'IconButton': 'forms',
        'Field': 'forms', 'Fieldset': 'forms', 'SegmentGroup': 'forms',
        'RatingGroup': 'forms', 'FileUpload': 'forms',
        'ColorPicker': 'forms',

        # Data Display
        'Badge': 'data-display', 'Tag': 'data-display',
        'Stat': 'data-display', 'StatLabel': 'data-display',
        'StatNumber': 'data-display', 'StatHelpText': 'data-display',
        'StatArrow': 'data-display', 'StatGroup': 'data-display',
        'Table': 'data-display', 'Thead': 'data-display',
        'Tbody': 'data-display', 'Tfoot': 'data-display',
        'Tr': 'data-display', 'Th': 'data-display', 'Td': 'data-display',
        'TableCaption': 'data-display', 'TableContainer': 'data-display',
        'Card': 'data-display', 'CardHeader': 'data-display',
        'CardBody': 'data-display', 'CardFooter': 'data-display',
        'List': 'data-display', 'ListItem': 'data-display',
        'ListIcon': 'data-display', 'OrderedList': 'data-display',
        'UnorderedList': 'data-display',
        'DataList': 'data-display', 'Timeline': 'data-display',
        'EmptyState': 'data-display', 'Status': 'data-display',

        # Feedback
        'Alert': 'feedback', 'AlertIcon': 'feedback',
        'AlertTitle': 'feedback', 'AlertDescription': 'feedback',
        'Progress': 'feedback', 'ProgressLabel': 'feedback',
        'CircularProgress': 'feedback', 'CircularProgressLabel': 'feedback',
        'Skeleton': 'feedback', 'SkeletonCircle': 'feedback',
        'SkeletonText': 'feedback',
        'Spinner': 'feedback', 'Toast': 'feedback',
        'Toaster': 'feedback',

        # Overlay
        'Modal': 'overlay', 'ModalOverlay': 'overlay',
        'ModalContent': 'overlay', 'ModalHeader': 'overlay',
        'ModalBody': 'overlay', 'ModalFooter': 'overlay',
        'ModalCloseButton': 'overlay',
        'Drawer': 'overlay', 'DrawerOverlay': 'overlay',
        'DrawerContent': 'overlay', 'DrawerHeader': 'overlay',
        'DrawerBody': 'overlay', 'DrawerFooter': 'overlay',
        'DrawerCloseButton': 'overlay',
        'Popover': 'overlay', 'PopoverTrigger': 'overlay',
        'PopoverContent': 'overlay', 'PopoverHeader': 'overlay',
        'PopoverBody': 'overlay', 'PopoverFooter': 'overlay',
        'PopoverArrow': 'overlay', 'PopoverCloseButton': 'overlay',
        'Tooltip': 'overlay',
        'AlertDialog': 'overlay', 'AlertDialogOverlay': 'overlay',
        'AlertDialogContent': 'overlay', 'AlertDialogHeader': 'overlay',
        'AlertDialogBody': 'overlay', 'AlertDialogFooter': 'overlay',
        'AlertDialogCloseButton': 'overlay',
        'Menu': 'overlay', 'MenuButton': 'overlay',
        'MenuList': 'overlay', 'MenuItem': 'overlay',
        'MenuItemOption': 'overlay', 'MenuGroup': 'overlay',
        'MenuOptionGroup': 'overlay', 'MenuDivider': 'overlay',
        'Dialog': 'overlay', 'HoverCard': 'overlay',

        # Navigation
        'Breadcrumb': 'navigation', 'BreadcrumbItem': 'navigation',
        'BreadcrumbLink': 'navigation', 'BreadcrumbSeparator': 'navigation',
        'Link': 'navigation', 'LinkBox': 'navigation',
        'LinkOverlay': 'navigation',
        'Stepper': 'navigation', 'Step': 'navigation',
        'StepIndicator': 'navigation', 'StepStatus': 'navigation',
        'StepTitle': 'navigation', 'StepDescription': 'navigation',
        'StepSeparator': 'navigation',
        'Steps': 'navigation',
        'Pagination': 'navigation',

        # Disclosure
        'Tabs': 'disclosure', 'TabList': 'disclosure', 'Tab': 'disclosure',
        'TabPanels': 'disclosure', 'TabPanel': 'disclosure',
        'TabIndicator': 'disclosure',
        'Accordion': 'disclosure', 'AccordionItem': 'disclosure',
        'AccordionButton': 'disclosure', 'AccordionPanel': 'disclosure',
        'AccordionIcon': 'disclosure',
        'Collapse': 'disclosure', 'Fade': 'disclosure',
        'ScaleFade': 'disclosure', 'Slide': 'disclosure',
        'SlideFade': 'disclosure',
        'Collapsible': 'disclosure',

        # Media & Icons
        'Image': 'media', 'Avatar': 'media', 'AvatarBadge': 'media',
        'AvatarGroup': 'media', 'Icon': 'media',
        'CloseButton': 'media', 'VisuallyHidden': 'media',

        # Providers & Utility
        'ChakraProvider': 'utility', 'ChakraBaseProvider': 'utility',
        'Provider': 'utility', 'ColorModeProvider': 'utility',
        'CSSReset': 'utility', 'GlobalStyle': 'utility',
        'Portal': 'utility', 'Show': 'utility', 'Hide': 'utility',
        'EnvironmentProvider': 'utility', 'ClientOnly': 'utility',
        'FormatNumber': 'utility', 'FormatByte': 'utility',
        'Separator': 'utility',
    }

    # Sub-component patterns
    SUB_COMPONENT_PATTERNS = {
        'Modal': ['Overlay', 'Content', 'Header', 'Body', 'Footer', 'CloseButton'],
        'Drawer': ['Overlay', 'Content', 'Header', 'Body', 'Footer', 'CloseButton'],
        'Popover': ['Trigger', 'Content', 'Header', 'Body', 'Footer', 'Arrow', 'CloseButton'],
        'AlertDialog': ['Overlay', 'Content', 'Header', 'Body', 'Footer', 'CloseButton'],
        'Menu': ['Button', 'List', 'Item', 'ItemOption', 'Group', 'OptionGroup', 'Divider'],
        'Accordion': ['Item', 'Button', 'Panel', 'Icon'],
        'Tabs': ['List', 'Tab', 'Panels', 'Panel', 'Indicator'],
        'Stat': ['Label', 'Number', 'HelpText', 'Arrow', 'Group'],
        'Card': ['Header', 'Body', 'Footer'],
        'Table': ['Head', 'Body', 'Foot', 'Row', 'Header', 'Cell', 'Caption', 'Container'],
        'NumberInput': ['Field', 'Stepper', 'IncrementStepper', 'DecrementStepper'],
        'Input': ['Group', 'LeftElement', 'RightElement', 'LeftAddon', 'RightAddon'],
        'Breadcrumb': ['Item', 'Link', 'Separator'],
        'Stepper': ['Step', 'Indicator', 'Status', 'Title', 'Description', 'Separator'],
        'Form': ['Control', 'Label', 'HelperText', 'ErrorMessage'],
        'List': ['Item', 'Icon'],
        'Alert': ['Icon', 'Title', 'Description'],
        'Editable': ['Preview', 'Input', 'Textarea'],
        'Pin': ['Input', 'InputField'],
        'Avatar': ['Badge', 'Group'],
    }

    # Import pattern for @chakra-ui/* imports
    CHAKRA_IMPORT_PATTERN = re.compile(
        r"import\s*\{([^}]+)\}\s*from\s*['\"]@chakra-ui/([^'\"]+)['\"]",
        re.MULTILINE
    )

    # v3: Import from chakra-ui (non-scoped)
    CHAKRA_V3_IMPORT_PATTERN = re.compile(
        r"import\s*\{([^}]+)\}\s*from\s*['\"]chakra-ui['\"]",
        re.MULTILINE
    )

    # JSX usage pattern — match <Component followed by space, >, />, or newline
    JSX_USAGE_PATTERN = re.compile(
        r'<(\w+)(?:\.\w+)?[\s/>]',
        re.MULTILINE
    )

    # Sub-component usage (Modal.Header, Accordion.Item)
    SUB_COMPONENT_USAGE = re.compile(
        r'<(\w+)\.(\w+)[\s/>]',
        re.MULTILINE
    )

    # chakra() factory pattern: const StyledDiv = chakra('div', { ... })
    CHAKRA_FACTORY_PATTERN = re.compile(
        r"(?:const|let|var)\s+(\w+)\s*=\s*chakra\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # chakra.div, chakra.span (v2 factory shorthand)
    CHAKRA_FACTORY_SHORTHAND = re.compile(
        r"<chakra\.(\w+)\s",
        re.MULTILINE
    )

    # forwardRef from Chakra
    FORWARD_REF_PATTERN = re.compile(
        r"(?:const|function)\s+(\w+)\s*=\s*forwardRef\s*[<(]",
        re.MULTILINE
    )

    # Style props that indicate Chakra usage
    STYLE_PROP_INDICATORS = {
        'bg', 'bgColor', 'color', 'p', 'px', 'py', 'pt', 'pb', 'pl', 'pr',
        'm', 'mx', 'my', 'mt', 'mb', 'ml', 'mr', 'w', 'h', 'minW', 'maxW',
        'minH', 'maxH', 'display', 'flexDir', 'flexDirection', 'justifyContent',
        'alignItems', 'textAlign', 'fontSize', 'fontWeight', 'lineHeight',
        'letterSpacing', 'borderRadius', 'borderWidth', 'borderColor',
        'boxShadow', 'opacity', 'zIndex', 'position', 'top', 'right',
        'bottom', 'left', 'overflow', 'cursor', 'transition',
        'colorScheme', 'variant', 'size', 'isDisabled', 'isInvalid',
        'isRequired', 'isReadOnly', 'isLoading',
    }

    # Responsive props patterns: { base: ..., md: ..., lg: ... } or [..., ..., ...]
    RESPONSIVE_OBJECT_PATTERN = re.compile(
        r'=\{\s*\{\s*base\s*:.*?(?:sm|md|lg|xl|2xl)\s*:',
        re.DOTALL
    )
    RESPONSIVE_ARRAY_PATTERN = re.compile(
        r'=\{\s*\[.+?,\s*.+?\]\s*\}',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Chakra UI component information from source code."""
        result = {
            'components': [],
            'custom_components': [],
        }

        if not content or not content.strip():
            return result

        # Extract imports
        imported_components = set()
        import_sources = {}

        # @chakra-ui/* imports (v1, v2)
        for match in self.CHAKRA_IMPORT_PATTERN.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in match.group(1).split(',')]
            scope = match.group(2)
            for name in names:
                if name:
                    imported_components.add(name)
                    import_sources[name] = f'@chakra-ui/{scope}'

        # chakra-ui imports (v3)
        for match in self.CHAKRA_V3_IMPORT_PATTERN.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in match.group(1).split(',')]
            for name in names:
                if name:
                    imported_components.add(name)
                    import_sources[name] = 'chakra-ui'

        # Detect chakra factory usage
        for match in self.CHAKRA_FACTORY_PATTERN.finditer(content):
            comp_name = match.group(1)
            base_element = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            custom_info = ChakraCustomComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                base_component=base_element,
                method='chakra-factory',
            )
            result['custom_components'].append(custom_info)

        # Detect chakra.div shorthand
        for match in self.CHAKRA_FACTORY_SHORTHAND.finditer(content):
            element = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            comp_info = ChakraComponentInfo(
                name=f'chakra.{element}',
                file=file_path,
                line_number=line_num,
                import_source='@chakra-ui/react',
                category='layout',
                has_style_props=True,
            )
            result['components'].append(comp_info)

        # Find component usages in JSX
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Direct component usage
            for jsx_match in self.JSX_USAGE_PATTERN.finditer(line):
                comp_name = jsx_match.group(1)
                if comp_name in imported_components or comp_name in self.COMPONENT_CATEGORIES:
                    category = self.COMPONENT_CATEGORIES.get(comp_name, 'other')
                    source = import_sources.get(comp_name, '')

                    # Check for style props
                    has_style_props = any(
                        re.search(rf'\b{prop}\s*=', line)
                        for prop in list(self.STYLE_PROP_INDICATORS)[:15]
                    )

                    # Check for responsive props
                    has_responsive = bool(
                        self.RESPONSIVE_OBJECT_PATTERN.search(line) or
                        self.RESPONSIVE_ARRAY_PATTERN.search(line)
                    )

                    # Extract props
                    props_used = self._extract_props(line, comp_name)

                    comp_info = ChakraComponentInfo(
                        name=comp_name,
                        file=file_path,
                        line_number=i,
                        import_source=source,
                        category=category,
                        props_used=props_used,
                        has_style_props=has_style_props,
                        has_responsive_props=has_responsive,
                    )
                    result['components'].append(comp_info)

            # Sub-component usage
            for sub_match in self.SUB_COMPONENT_USAGE.finditer(line):
                parent = sub_match.group(1)
                child = sub_match.group(2)
                if parent in imported_components or parent in self.COMPONENT_CATEGORIES:
                    comp_info = ChakraComponentInfo(
                        name=f"{parent}.{child}",
                        file=file_path,
                        line_number=i,
                        import_source=import_sources.get(parent, ''),
                        category=self.COMPONENT_CATEGORIES.get(parent, 'other'),
                        sub_components=[child],
                    )
                    result['components'].append(comp_info)

        # Detect forwardRef custom components
        for match in self.FORWARD_REF_PATTERN.finditer(content):
            comp_name = match.group(1)
            # Only count if it uses Chakra components inside
            if comp_name not in self.COMPONENT_CATEGORIES and comp_name not in imported_components:
                line_num = content[:match.start()].count('\n') + 1
                # Check if any Chakra component is used nearby (within 50 lines)
                context_start = max(0, match.start() - 50)
                context_end = min(len(content), match.end() + 2000)
                context = content[context_start:context_end]
                chakra_used = any(
                    c in context for c in list(self.COMPONENT_CATEGORIES.keys())[:30]
                )
                if chakra_used:
                    custom_info = ChakraCustomComponentInfo(
                        name=comp_name,
                        file=file_path,
                        line_number=line_num,
                        method='forwardRef',
                        has_theme_usage='useTheme' in context or 'useColorMode' in context,
                    )
                    result['custom_components'].append(custom_info)

        return result

    def _extract_props(self, line: str, component: str) -> List[str]:
        """Extract prop names from a JSX line."""
        props = []
        # Simple prop extraction: propName= or propName={
        prop_pattern = re.compile(r'\b(\w+)\s*=\s*[{"\']')
        for m in prop_pattern.finditer(line):
            prop = m.group(1)
            if prop != component and prop not in ('className', 'key', 'ref', 'id', 'style'):
                props.append(prop)
        return props[:20]
