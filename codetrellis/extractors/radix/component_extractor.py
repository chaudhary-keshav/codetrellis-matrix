"""
Radix UI Component Extractor for CodeTrellis

Extracts Radix UI component usage from React/TypeScript source code.
Covers Radix Primitives v0.x-v1.x and Radix Themes v1.x-v4.x.

Radix Primitives (30+ packages, each @radix-ui/react-*):
- Overlay: Dialog, AlertDialog, Popover, Tooltip, HoverCard,
    ContextMenu, DropdownMenu, Menubar, Toast
- Forms: Checkbox, RadioGroup, Select, Slider, Switch, ToggleGroup,
    Toggle, Form, Label
- Layout: Accordion, Collapsible, NavigationMenu, Tabs, Toolbar
- Content: AspectRatio, Avatar, Progress, ScrollArea, Separator
- Utility: Slot, VisuallyHidden, Portal, Presence, FocusScope,
    DismissableLayer, Direction, Id

Radix Themes (50+ styled components):
- Layout: Box, Flex, Grid, Container, Section
- Typography: Text, Heading, Code, Blockquote, Em, Kbd, Link, Quote, Strong
- Forms: Button, TextField, TextArea, Select, Checkbox, RadioGroup,
    Switch, Slider, SegmentedControl
- Data Display: Badge, Card, Table, DataList, Avatar, Callout, Code
- Feedback: Progress, Skeleton, Spinner
- Overlay: Dialog, AlertDialog, Popover, Tooltip, HoverCard, ContextMenu,
    DropdownMenu
- Navigation: Tabs, TabNav

Detection patterns:
- Import from '@radix-ui/react-*' (primitives)
- Import from '@radix-ui/themes' (styled components)
- Import from '@radix-ui/colors' (color system)
- Import from '@radix-ui/react-icons' (icon set)

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RadixComponentInfo:
    """Information about a Radix UI primitive or Themes component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # @radix-ui/react-dialog, @radix-ui/themes, etc.
    category: str = ""            # overlay, forms, layout, content, utility, typography
    is_primitive: bool = True     # True for @radix-ui/react-*, False for @radix-ui/themes
    props_used: List[str] = field(default_factory=list)
    has_as_child: bool = False    # Uses asChild prop
    sub_components: List[str] = field(default_factory=list)
    data_attributes: List[str] = field(default_factory=list)  # data-state, data-side, etc.
    is_portal: bool = False       # Uses Portal sub-component
    is_controlled: bool = False   # Uses controlled state (open/value + onChange)


@dataclass
class RadixThemesComponentInfo:
    """Information about a Radix Themes styled component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    category: str = ""            # layout, typography, forms, data-display, overlay, feedback
    variant: str = ""             # variant prop value
    size: str = ""                # size prop value (1-9)
    color: str = ""               # color prop value
    high_contrast: bool = False   # highContrast prop
    radius: str = ""              # radius prop value
    has_responsive: bool = False  # Uses responsive props {initial, xs, sm, md, lg, xl}


class RadixComponentExtractor:
    """
    Extracts Radix UI component usage from React/TypeScript source code.

    Detects:
    - Radix Primitives (@radix-ui/react-*) imports and usage (30+ primitives)
    - Radix Themes (@radix-ui/themes) imports and usage (50+ styled components)
    - Component composition (Dialog.Root, Dialog.Trigger, Dialog.Content, etc.)
    - asChild prop forwarding pattern
    - Portal usage for overlay components
    - Data attribute state management
    - Controlled vs uncontrolled patterns
    """

    # Radix Primitives: component -> category
    PRIMITIVE_CATEGORIES = {
        # Overlay
        'Dialog': 'overlay', 'DialogRoot': 'overlay', 'DialogTrigger': 'overlay',
        'DialogPortal': 'overlay', 'DialogOverlay': 'overlay',
        'DialogContent': 'overlay', 'DialogTitle': 'overlay',
        'DialogDescription': 'overlay', 'DialogClose': 'overlay',
        'AlertDialog': 'overlay', 'AlertDialogRoot': 'overlay',
        'AlertDialogTrigger': 'overlay', 'AlertDialogPortal': 'overlay',
        'AlertDialogOverlay': 'overlay', 'AlertDialogContent': 'overlay',
        'AlertDialogTitle': 'overlay', 'AlertDialogDescription': 'overlay',
        'AlertDialogAction': 'overlay', 'AlertDialogCancel': 'overlay',
        'Popover': 'overlay', 'PopoverRoot': 'overlay',
        'PopoverTrigger': 'overlay', 'PopoverPortal': 'overlay',
        'PopoverContent': 'overlay', 'PopoverArrow': 'overlay',
        'PopoverClose': 'overlay', 'PopoverAnchor': 'overlay',
        'Tooltip': 'overlay', 'TooltipRoot': 'overlay',
        'TooltipProvider': 'overlay', 'TooltipTrigger': 'overlay',
        'TooltipPortal': 'overlay', 'TooltipContent': 'overlay',
        'TooltipArrow': 'overlay',
        'HoverCard': 'overlay', 'HoverCardRoot': 'overlay',
        'HoverCardTrigger': 'overlay', 'HoverCardPortal': 'overlay',
        'HoverCardContent': 'overlay',
        'ContextMenu': 'overlay', 'ContextMenuRoot': 'overlay',
        'ContextMenuTrigger': 'overlay', 'ContextMenuPortal': 'overlay',
        'ContextMenuContent': 'overlay', 'ContextMenuItem': 'overlay',
        'ContextMenuSub': 'overlay', 'ContextMenuSubTrigger': 'overlay',
        'ContextMenuSubContent': 'overlay',
        'ContextMenuCheckboxItem': 'overlay', 'ContextMenuRadioGroup': 'overlay',
        'ContextMenuRadioItem': 'overlay', 'ContextMenuLabel': 'overlay',
        'ContextMenuSeparator': 'overlay', 'ContextMenuGroup': 'overlay',
        'ContextMenuItemIndicator': 'overlay',
        'DropdownMenu': 'overlay', 'DropdownMenuRoot': 'overlay',
        'DropdownMenuTrigger': 'overlay', 'DropdownMenuPortal': 'overlay',
        'DropdownMenuContent': 'overlay', 'DropdownMenuItem': 'overlay',
        'DropdownMenuSub': 'overlay', 'DropdownMenuSubTrigger': 'overlay',
        'DropdownMenuSubContent': 'overlay',
        'DropdownMenuCheckboxItem': 'overlay', 'DropdownMenuRadioGroup': 'overlay',
        'DropdownMenuRadioItem': 'overlay', 'DropdownMenuLabel': 'overlay',
        'DropdownMenuSeparator': 'overlay', 'DropdownMenuGroup': 'overlay',
        'DropdownMenuItemIndicator': 'overlay',
        'Menubar': 'overlay', 'MenubarRoot': 'overlay',
        'MenubarMenu': 'overlay', 'MenubarTrigger': 'overlay',
        'MenubarPortal': 'overlay', 'MenubarContent': 'overlay',
        'MenubarItem': 'overlay', 'MenubarSub': 'overlay',
        'MenubarSubTrigger': 'overlay', 'MenubarSubContent': 'overlay',
        'MenubarCheckboxItem': 'overlay', 'MenubarRadioGroup': 'overlay',
        'MenubarRadioItem': 'overlay', 'MenubarLabel': 'overlay',
        'MenubarSeparator': 'overlay', 'MenubarGroup': 'overlay',
        'MenubarItemIndicator': 'overlay',
        'Toast': 'overlay', 'ToastProvider': 'overlay',
        'ToastViewport': 'overlay', 'ToastRoot': 'overlay',
        'ToastTitle': 'overlay', 'ToastDescription': 'overlay',
        'ToastAction': 'overlay', 'ToastClose': 'overlay',

        # Forms
        'Checkbox': 'forms', 'CheckboxRoot': 'forms',
        'CheckboxIndicator': 'forms',
        'RadioGroup': 'forms', 'RadioGroupRoot': 'forms',
        'RadioGroupItem': 'forms', 'RadioGroupIndicator': 'forms',
        'Select': 'forms', 'SelectRoot': 'forms',
        'SelectTrigger': 'forms', 'SelectValue': 'forms',
        'SelectIcon': 'forms', 'SelectPortal': 'forms',
        'SelectContent': 'forms', 'SelectViewport': 'forms',
        'SelectItem': 'forms', 'SelectItemText': 'forms',
        'SelectItemIndicator': 'forms', 'SelectGroup': 'forms',
        'SelectLabel': 'forms', 'SelectSeparator': 'forms',
        'SelectScrollUpButton': 'forms', 'SelectScrollDownButton': 'forms',
        'Slider': 'forms', 'SliderRoot': 'forms',
        'SliderTrack': 'forms', 'SliderRange': 'forms',
        'SliderThumb': 'forms',
        'Switch': 'forms', 'SwitchRoot': 'forms',
        'SwitchThumb': 'forms',
        'Toggle': 'forms', 'ToggleRoot': 'forms',
        'ToggleGroup': 'forms', 'ToggleGroupRoot': 'forms',
        'ToggleGroupItem': 'forms',
        'Form': 'forms', 'FormRoot': 'forms',
        'FormField': 'forms', 'FormLabel': 'forms',
        'FormControl': 'forms', 'FormMessage': 'forms',
        'FormValidityState': 'forms', 'FormSubmit': 'forms',
        'Label': 'forms', 'LabelRoot': 'forms',

        # Layout
        'Accordion': 'layout', 'AccordionRoot': 'layout',
        'AccordionItem': 'layout', 'AccordionHeader': 'layout',
        'AccordionTrigger': 'layout', 'AccordionContent': 'layout',
        'Collapsible': 'layout', 'CollapsibleRoot': 'layout',
        'CollapsibleTrigger': 'layout', 'CollapsibleContent': 'layout',
        'NavigationMenu': 'layout', 'NavigationMenuRoot': 'layout',
        'NavigationMenuList': 'layout', 'NavigationMenuItem': 'layout',
        'NavigationMenuTrigger': 'layout', 'NavigationMenuContent': 'layout',
        'NavigationMenuLink': 'layout', 'NavigationMenuSub': 'layout',
        'NavigationMenuViewport': 'layout', 'NavigationMenuIndicator': 'layout',
        'Tabs': 'layout', 'TabsRoot': 'layout',
        'TabsList': 'layout', 'TabsTrigger': 'layout',
        'TabsContent': 'layout',
        'Toolbar': 'layout', 'ToolbarRoot': 'layout',
        'ToolbarButton': 'layout', 'ToolbarLink': 'layout',
        'ToolbarSeparator': 'layout', 'ToolbarToggleGroup': 'layout',
        'ToolbarToggleItem': 'layout',

        # Content
        'AspectRatio': 'content', 'AspectRatioRoot': 'content',
        'Avatar': 'content', 'AvatarRoot': 'content',
        'AvatarImage': 'content', 'AvatarFallback': 'content',
        'Progress': 'content', 'ProgressRoot': 'content',
        'ProgressIndicator': 'content',
        'ScrollArea': 'content', 'ScrollAreaRoot': 'content',
        'ScrollAreaViewport': 'content', 'ScrollAreaScrollbar': 'content',
        'ScrollAreaThumb': 'content', 'ScrollAreaCorner': 'content',
        'Separator': 'content', 'SeparatorRoot': 'content',

        # Utility
        'Slot': 'utility', 'Slottable': 'utility',
        'VisuallyHidden': 'utility',
        'Portal': 'utility',
        'Presence': 'utility',
        'FocusScope': 'utility',
        'DismissableLayer': 'utility',
        'Direction': 'utility', 'DirectionProvider': 'utility',
    }

    # Radix Themes: component -> category
    THEMES_CATEGORIES = {
        # Layout
        'Box': 'layout', 'Flex': 'layout', 'Grid': 'layout',
        'Container': 'layout', 'Section': 'layout',

        # Typography
        'Text': 'typography', 'Heading': 'typography', 'Code': 'typography',
        'Blockquote': 'typography', 'Em': 'typography', 'Kbd': 'typography',
        'Link': 'typography', 'Quote': 'typography', 'Strong': 'typography',

        # Forms
        'Button': 'forms', 'IconButton': 'forms',
        'TextField': 'forms', 'TextFieldRoot': 'forms',
        'TextFieldSlot': 'forms', 'TextFieldInput': 'forms',
        'TextArea': 'forms',
        'Select': 'forms', 'SelectRoot': 'forms', 'SelectTrigger': 'forms',
        'SelectContent': 'forms', 'SelectItem': 'forms',
        'SelectGroup': 'forms', 'SelectLabel': 'forms',
        'SelectSeparator': 'forms',
        'Checkbox': 'forms', 'RadioGroup': 'forms',
        'RadioGroupRoot': 'forms', 'RadioGroupItem': 'forms',
        'Switch': 'forms', 'Slider': 'forms',
        'SegmentedControl': 'forms',

        # Data Display
        'Badge': 'data-display', 'Card': 'data-display',
        'Table': 'data-display', 'TableRoot': 'data-display',
        'TableHeader': 'data-display', 'TableBody': 'data-display',
        'TableRow': 'data-display', 'TableCell': 'data-display',
        'TableColumnHeaderCell': 'data-display', 'TableRowHeaderCell': 'data-display',
        'DataList': 'data-display', 'DataListRoot': 'data-display',
        'DataListItem': 'data-display', 'DataListLabel': 'data-display',
        'DataListValue': 'data-display',
        'Avatar': 'data-display', 'Callout': 'data-display',
        'CalloutRoot': 'data-display', 'CalloutIcon': 'data-display',
        'CalloutText': 'data-display',
        'Inset': 'data-display',

        # Feedback
        'Progress': 'feedback', 'Skeleton': 'feedback', 'Spinner': 'feedback',

        # Overlay
        'Dialog': 'overlay', 'DialogRoot': 'overlay', 'DialogTrigger': 'overlay',
        'DialogContent': 'overlay', 'DialogTitle': 'overlay',
        'DialogDescription': 'overlay', 'DialogClose': 'overlay',
        'AlertDialog': 'overlay', 'AlertDialogRoot': 'overlay',
        'AlertDialogTrigger': 'overlay', 'AlertDialogContent': 'overlay',
        'AlertDialogTitle': 'overlay', 'AlertDialogDescription': 'overlay',
        'AlertDialogAction': 'overlay', 'AlertDialogCancel': 'overlay',
        'Popover': 'overlay', 'PopoverRoot': 'overlay',
        'PopoverTrigger': 'overlay', 'PopoverContent': 'overlay',
        'PopoverClose': 'overlay',
        'Tooltip': 'overlay', 'TooltipContent': 'overlay',
        'HoverCard': 'overlay', 'HoverCardRoot': 'overlay',
        'HoverCardTrigger': 'overlay', 'HoverCardContent': 'overlay',
        'ContextMenu': 'overlay', 'ContextMenuRoot': 'overlay',
        'ContextMenuTrigger': 'overlay', 'ContextMenuContent': 'overlay',
        'ContextMenuItem': 'overlay', 'ContextMenuSub': 'overlay',
        'ContextMenuSubTrigger': 'overlay', 'ContextMenuSubContent': 'overlay',
        'ContextMenuCheckboxItem': 'overlay', 'ContextMenuRadioGroup': 'overlay',
        'ContextMenuRadioItem': 'overlay', 'ContextMenuLabel': 'overlay',
        'ContextMenuSeparator': 'overlay',
        'DropdownMenu': 'overlay', 'DropdownMenuRoot': 'overlay',
        'DropdownMenuTrigger': 'overlay', 'DropdownMenuContent': 'overlay',
        'DropdownMenuItem': 'overlay', 'DropdownMenuSub': 'overlay',
        'DropdownMenuSubTrigger': 'overlay', 'DropdownMenuSubContent': 'overlay',
        'DropdownMenuCheckboxItem': 'overlay', 'DropdownMenuRadioGroup': 'overlay',
        'DropdownMenuRadioItem': 'overlay', 'DropdownMenuLabel': 'overlay',
        'DropdownMenuSeparator': 'overlay',

        # Navigation
        'Tabs': 'navigation', 'TabsRoot': 'navigation', 'TabsList': 'navigation',
        'TabsTrigger': 'navigation', 'TabsContent': 'navigation',
        'TabNav': 'navigation', 'TabNavRoot': 'navigation',
        'TabNavLink': 'navigation',

        # Utility / Provider
        'Theme': 'utility', 'ThemePanel': 'utility',
        'ScrollArea': 'utility',
    }

    # Sub-component patterns for composition detection
    SUB_COMPONENT_PATTERNS = {
        'Dialog': ['Root', 'Trigger', 'Portal', 'Overlay', 'Content', 'Title', 'Description', 'Close'],
        'AlertDialog': ['Root', 'Trigger', 'Portal', 'Overlay', 'Content', 'Title', 'Description', 'Action', 'Cancel'],
        'Popover': ['Root', 'Trigger', 'Portal', 'Content', 'Arrow', 'Close', 'Anchor'],
        'Tooltip': ['Provider', 'Root', 'Trigger', 'Portal', 'Content', 'Arrow'],
        'HoverCard': ['Root', 'Trigger', 'Portal', 'Content'],
        'ContextMenu': ['Root', 'Trigger', 'Portal', 'Content', 'Item', 'Sub', 'SubTrigger', 'SubContent', 'CheckboxItem', 'RadioGroup', 'RadioItem', 'Label', 'Separator', 'Group'],
        'DropdownMenu': ['Root', 'Trigger', 'Portal', 'Content', 'Item', 'Sub', 'SubTrigger', 'SubContent', 'CheckboxItem', 'RadioGroup', 'RadioItem', 'Label', 'Separator', 'Group'],
        'Menubar': ['Root', 'Menu', 'Trigger', 'Portal', 'Content', 'Item', 'Sub', 'SubTrigger', 'SubContent', 'CheckboxItem', 'RadioGroup', 'RadioItem', 'Label', 'Separator', 'Group'],
        'Accordion': ['Root', 'Item', 'Header', 'Trigger', 'Content'],
        'Collapsible': ['Root', 'Trigger', 'Content'],
        'NavigationMenu': ['Root', 'List', 'Item', 'Trigger', 'Content', 'Link', 'Sub', 'Viewport', 'Indicator'],
        'Tabs': ['Root', 'List', 'Trigger', 'Content'],
        'Select': ['Root', 'Trigger', 'Value', 'Icon', 'Portal', 'Content', 'Viewport', 'Item', 'ItemText', 'ItemIndicator', 'Group', 'Label', 'Separator', 'ScrollUpButton', 'ScrollDownButton'],
        'RadioGroup': ['Root', 'Item', 'Indicator'],
        'Slider': ['Root', 'Track', 'Range', 'Thumb'],
        'Switch': ['Root', 'Thumb'],
        'Toast': ['Provider', 'Viewport', 'Root', 'Title', 'Description', 'Action', 'Close'],
        'ScrollArea': ['Root', 'Viewport', 'Scrollbar', 'Thumb', 'Corner'],
        'Avatar': ['Root', 'Image', 'Fallback'],
        'Form': ['Root', 'Field', 'Label', 'Control', 'Message', 'ValidityState', 'Submit'],
        'Toolbar': ['Root', 'Button', 'Link', 'Separator', 'ToggleGroup', 'ToggleItem'],
    }

    # Controlled component props
    CONTROLLED_PROPS = {
        'Dialog': ('open', 'onOpenChange'),
        'AlertDialog': ('open', 'onOpenChange'),
        'Popover': ('open', 'onOpenChange'),
        'Tooltip': ('open', 'onOpenChange'),
        'HoverCard': ('open', 'onOpenChange'),
        'ContextMenu': ('open', 'onOpenChange'),
        'DropdownMenu': ('open', 'onOpenChange'),
        'Collapsible': ('open', 'onOpenChange'),
        'Accordion': ('value', 'onValueChange'),
        'Tabs': ('value', 'onValueChange'),
        'Select': ('value', 'onValueChange'),
        'RadioGroup': ('value', 'onValueChange'),
        'ToggleGroup': ('value', 'onValueChange'),
        'Toggle': ('pressed', 'onPressedChange'),
        'Switch': ('checked', 'onCheckedChange'),
        'Checkbox': ('checked', 'onCheckedChange'),
        'Slider': ('value', 'onValueChange'),
        'NavigationMenu': ('value', 'onValueChange'),
        'Menubar': ('value', 'onValueChange'),
    }

    # Import pattern for @radix-ui/react-*
    PRIMITIVE_IMPORT_PATTERN = re.compile(
        r"""(?:import|from)\s+.*?['"]@radix-ui/react-([a-z-]+)['"]""",
        re.MULTILINE,
    )

    # Import pattern for @radix-ui/themes
    THEMES_IMPORT_PATTERN = re.compile(
        r"""import\s*\{([^}]+)\}\s*from\s*['"]@radix-ui/themes['"]""",
        re.MULTILINE,
    )

    # JSX usage detection (React component usage)
    COMPONENT_USAGE_PATTERN = re.compile(
        r'<(\w+(?:\.\w+)?)\s',
        re.MULTILINE,
    )

    # asChild prop detection
    AS_CHILD_PATTERN = re.compile(
        r'<(\w+(?:\.\w+)?)\s[^>]*\basChild\b',
        re.MULTILINE,
    )

    # Data attribute usage
    DATA_ATTR_PATTERN = re.compile(
        r'\[data-(state|side|align|orientation|disabled|highlighted|placeholder|swipe-direction|swipe|motion)\s*[=~|^$*]?\s*["\']?(\w+)?',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Radix UI component information from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'components' and 'themes_components' lists
        """
        result = {
            'components': [],
            'themes_components': [],
        }

        if not content or not content.strip():
            return result

        # Extract primitive components
        primitives = self._extract_primitive_components(content, file_path)
        result['components'].extend(primitives)

        # Extract Themes components
        themes = self._extract_themes_components(content, file_path)
        result['themes_components'].extend(themes)

        return result

    def _extract_primitive_components(
        self, content: str, file_path: str
    ) -> List[RadixComponentInfo]:
        """Extract Radix Primitives usage from source code."""
        components = []
        seen = set()

        # Find all @radix-ui/react-* imports
        for match in self.PRIMITIVE_IMPORT_PATTERN.finditer(content):
            package_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Parse imported names from import statement
            # Match full import line
            line_start = content.rfind('\n', 0, match.start()) + 1
            # Find end of import (could be multi-line)
            brace_start = content.find('{', line_start, match.start() + 200)
            if brace_start >= 0:
                brace_end = content.find('}', brace_start)
                if brace_end >= 0:
                    import_names_str = content[brace_start + 1:brace_end]
                    import_names = [
                        n.strip().split(' as ')[0].strip()
                        for n in import_names_str.split(',')
                        if n.strip()
                    ]
                else:
                    import_names = [self._package_to_component(package_name)]
            else:
                # Default or namespace import
                import_names = [self._package_to_component(package_name)]

            import_source = f"@radix-ui/react-{package_name}"

            for name in import_names:
                if not name or name.startswith('type '):
                    continue
                key = (name, file_path)
                if key in seen:
                    continue
                seen.add(key)

                category = self.PRIMITIVE_CATEGORIES.get(name, '')
                sub_comps = self._find_sub_components(name, content)
                has_as_child = bool(re.search(
                    rf'<{re.escape(name)}\s[^>]*\basChild\b', content
                ))
                is_portal = f'{name}Portal' in content or '.Portal' in content
                is_controlled = self._is_controlled_usage(name, content)
                data_attrs = self._find_data_attributes(content)

                comp = RadixComponentInfo(
                    name=name,
                    file=file_path,
                    line_number=line_number,
                    import_source=import_source,
                    category=category,
                    is_primitive=True,
                    has_as_child=has_as_child,
                    sub_components=sub_comps,
                    data_attributes=data_attrs[:10],
                    is_portal=is_portal,
                    is_controlled=is_controlled,
                )
                components.append(comp)

        return components

    def _extract_themes_components(
        self, content: str, file_path: str
    ) -> List[RadixThemesComponentInfo]:
        """Extract Radix Themes component usage from source code."""
        components = []
        seen = set()

        for match in self.THEMES_IMPORT_PATTERN.finditer(content):
            names_str = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            names = [
                n.strip().split(' as ')[0].strip()
                for n in names_str.split(',')
                if n.strip() and not n.strip().startswith('type ')
            ]

            for name in names:
                if not name:
                    continue
                key = (name, file_path)
                if key in seen:
                    continue
                seen.add(key)

                category = self.THEMES_CATEGORIES.get(name, '')

                # Detect variant, size, color props in JSX usage
                variant = self._find_prop_value(name, 'variant', content)
                size = self._find_prop_value(name, 'size', content)
                color = self._find_prop_value(name, 'color', content)
                high_contrast = bool(re.search(
                    rf'<{re.escape(name)}\s[^>]*\bhighContrast\b', content
                ))
                radius = self._find_prop_value(name, 'radius', content)
                has_responsive = bool(re.search(
                    rf'<{re.escape(name)}\s[^>]*\b(?:size|variant|color)\s*=\s*\{{', content
                ))

                comp = RadixThemesComponentInfo(
                    name=name,
                    file=file_path,
                    line_number=line_number,
                    category=category,
                    variant=variant,
                    size=size,
                    color=color,
                    high_contrast=high_contrast,
                    radius=radius,
                    has_responsive=has_responsive,
                )
                components.append(comp)

        return components

    def _package_to_component(self, package_name: str) -> str:
        """Convert package name to component name: 'alert-dialog' -> 'AlertDialog'."""
        return ''.join(
            word.capitalize() for word in package_name.split('-')
        )

    def _find_sub_components(self, base_name: str, content: str) -> List[str]:
        """Find sub-components used (e.g., Dialog.Trigger, Dialog.Content)."""
        subs = []
        pattern = re.compile(rf'{re.escape(base_name)}\.(\w+)', re.MULTILINE)
        for match in pattern.finditer(content):
            sub = match.group(1)
            if sub not in subs:
                subs.append(sub)
        return subs[:15]

    def _find_prop_value(self, component: str, prop: str, content: str) -> str:
        """Find the value of a prop on a component in JSX."""
        pattern = re.compile(
            rf'<{re.escape(component)}\s[^>]*\b{prop}\s*=\s*["\']([^"\']+)["\']',
            re.MULTILINE,
        )
        match = pattern.search(content)
        return match.group(1) if match else ""

    def _is_controlled_usage(self, component: str, content: str) -> bool:
        """Check if a component is used in controlled mode."""
        controlled = self.CONTROLLED_PROPS.get(component)
        if not controlled:
            return False
        value_prop, change_handler = controlled
        has_value = bool(re.search(
            rf'<{re.escape(component)}[^>]*\b{value_prop}\s*=', content
        ))
        has_handler = bool(re.search(
            rf'<{re.escape(component)}[^>]*\b{change_handler}\s*=', content
        ))
        return has_value and has_handler

    def _find_data_attributes(self, content: str) -> List[str]:
        """Find Radix data-* attribute selectors used in styling."""
        attrs = []
        for match in self.DATA_ATTR_PATTERN.finditer(content):
            attr = f"data-{match.group(1)}"
            if match.group(2):
                attr += f"={match.group(2)}"
            if attr not in attrs:
                attrs.append(attr)
        return attrs
