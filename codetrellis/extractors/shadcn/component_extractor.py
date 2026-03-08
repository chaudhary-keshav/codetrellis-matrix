"""
shadcn/ui Component Extractor for CodeTrellis

Extracts shadcn/ui component usage from React/TypeScript source code.
shadcn/ui is unique: components are NOT installed via npm but copied into the
project via CLI (`npx shadcn@latest add`). They live in the user's codebase
(typically `components/ui/` or `src/components/ui/`).

Component categories:
- Layout: Accordion, AspectRatio, Card, Collapsible, Resizable, ScrollArea,
    Separator, Sheet, Sidebar, Tabs
- Forms: Button, Calendar, Checkbox, Combobox, DatePicker, Form, Input,
    InputOTP, Label, RadioGroup, Select, Slider, Switch, Textarea, Toggle,
    ToggleGroup
- Data Display: Avatar, Badge, Carousel, Chart, DataTable, HoverCard,
    Table, Tooltip
- Feedback: Alert, AlertDialog, Progress, Skeleton, Sonner/Toast
- Navigation: Breadcrumb, Command, ContextMenu, Dialog, Drawer,
    DropdownMenu, Menubar, NavigationMenu, Pagination, Popover
- Typography: Typography (prose)

Detection patterns:
- Import from '@/components/ui/*' or relative UI imports
- Import from 'components/ui/*' (alias-free)
- Radix UI primitive imports (@radix-ui/react-*)
- cn() utility from '@/lib/utils' or '@/utils'
- CVA (class-variance-authority) usage
- components.json registry file

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShadcnComponentInfo:
    """Information about a shadcn/ui component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_path: str = ""        # @/components/ui/button, ./ui/button, etc.
    category: str = ""           # layout, forms, data-display, feedback, navigation
    props_used: List[str] = field(default_factory=list)
    variant: str = ""            # variant prop value (default, destructive, outline, etc.)
    size: str = ""               # size prop value (default, sm, lg, icon)
    has_custom_className: bool = False  # Uses className override
    radix_primitive: str = ""    # Underlying Radix UI primitive
    is_composition: bool = False  # Uses sub-components (Card.Header, etc.)
    sub_components: List[str] = field(default_factory=list)


@dataclass
class ShadcnRegistryComponentInfo:
    """Information about a shadcn/ui component installed from registry."""
    name: str
    file: str = ""
    line_number: int = 0
    component_path: str = ""     # components/ui/button.tsx
    has_cva: bool = False        # Uses class-variance-authority
    has_cn: bool = False         # Uses cn() utility
    radix_dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    variant_names: List[str] = field(default_factory=list)
    size_names: List[str] = field(default_factory=list)
    is_customized: bool = False  # Has been modified from original


class ShadcnComponentExtractor:
    """
    Extracts shadcn/ui component usage from React/TypeScript source code.

    Detects:
    - shadcn/ui component imports from ui/ directory
    - Radix UI primitive imports that underpin shadcn/ui
    - Component registry files (components.json)
    - Component variant usage
    - Custom component wrappers
    - Sub-component composition patterns
    """

    # shadcn/ui component categories — 40+ components
    COMPONENT_CATEGORIES = {
        # Layout
        'Accordion': 'layout', 'AccordionItem': 'layout',
        'AccordionTrigger': 'layout', 'AccordionContent': 'layout',
        'AspectRatio': 'layout',
        'Card': 'layout', 'CardHeader': 'layout', 'CardTitle': 'layout',
        'CardDescription': 'layout', 'CardContent': 'layout',
        'CardFooter': 'layout',
        'Collapsible': 'layout', 'CollapsibleTrigger': 'layout',
        'CollapsibleContent': 'layout',
        'ResizablePanel': 'layout', 'ResizablePanelGroup': 'layout',
        'ResizableHandle': 'layout',
        'ScrollArea': 'layout', 'ScrollBar': 'layout',
        'Separator': 'layout',
        'Sheet': 'layout', 'SheetTrigger': 'layout', 'SheetContent': 'layout',
        'SheetHeader': 'layout', 'SheetTitle': 'layout',
        'SheetDescription': 'layout', 'SheetFooter': 'layout',
        'SheetClose': 'layout',
        'Sidebar': 'layout', 'SidebarContent': 'layout',
        'SidebarGroup': 'layout', 'SidebarGroupLabel': 'layout',
        'SidebarGroupContent': 'layout', 'SidebarMenu': 'layout',
        'SidebarMenuItem': 'layout', 'SidebarMenuButton': 'layout',
        'SidebarProvider': 'layout', 'SidebarTrigger': 'layout',
        'SidebarInset': 'layout', 'SidebarFooter': 'layout',
        'SidebarHeader': 'layout', 'SidebarRail': 'layout',
        'Tabs': 'layout', 'TabsList': 'layout', 'TabsTrigger': 'layout',
        'TabsContent': 'layout',

        # Forms
        'Button': 'forms', 'buttonVariants': 'forms',
        'Calendar': 'forms',
        'Checkbox': 'forms',
        'Form': 'forms', 'FormField': 'forms', 'FormItem': 'forms',
        'FormLabel': 'forms', 'FormControl': 'forms',
        'FormDescription': 'forms', 'FormMessage': 'forms',
        'Input': 'forms',
        'InputOTP': 'forms', 'InputOTPGroup': 'forms',
        'InputOTPSlot': 'forms', 'InputOTPSeparator': 'forms',
        'Label': 'forms',
        'RadioGroup': 'forms', 'RadioGroupItem': 'forms',
        'Select': 'forms', 'SelectTrigger': 'forms', 'SelectValue': 'forms',
        'SelectContent': 'forms', 'SelectItem': 'forms',
        'SelectGroup': 'forms', 'SelectLabel': 'forms',
        'SelectSeparator': 'forms', 'SelectScrollUpButton': 'forms',
        'SelectScrollDownButton': 'forms',
        'Slider': 'forms',
        'Switch': 'forms',
        'Textarea': 'forms',
        'Toggle': 'forms', 'toggleVariants': 'forms',
        'ToggleGroup': 'forms', 'ToggleGroupItem': 'forms',
        'DatePicker': 'forms',

        # Data Display
        'Avatar': 'data-display', 'AvatarImage': 'data-display',
        'AvatarFallback': 'data-display',
        'Badge': 'data-display', 'badgeVariants': 'data-display',
        'Carousel': 'data-display', 'CarouselContent': 'data-display',
        'CarouselItem': 'data-display', 'CarouselPrevious': 'data-display',
        'CarouselNext': 'data-display',
        'ChartContainer': 'data-display', 'ChartTooltip': 'data-display',
        'ChartTooltipContent': 'data-display', 'ChartLegend': 'data-display',
        'ChartLegendContent': 'data-display',
        'HoverCard': 'data-display', 'HoverCardTrigger': 'data-display',
        'HoverCardContent': 'data-display',
        'Table': 'data-display', 'TableBody': 'data-display',
        'TableCaption': 'data-display', 'TableCell': 'data-display',
        'TableFooter': 'data-display', 'TableHead': 'data-display',
        'TableHeader': 'data-display', 'TableRow': 'data-display',
        'Tooltip': 'data-display', 'TooltipTrigger': 'data-display',
        'TooltipContent': 'data-display', 'TooltipProvider': 'data-display',

        # Feedback
        'Alert': 'feedback', 'AlertTitle': 'feedback',
        'AlertDescription': 'feedback',
        'AlertDialog': 'feedback', 'AlertDialogTrigger': 'feedback',
        'AlertDialogContent': 'feedback', 'AlertDialogHeader': 'feedback',
        'AlertDialogTitle': 'feedback', 'AlertDialogDescription': 'feedback',
        'AlertDialogFooter': 'feedback', 'AlertDialogAction': 'feedback',
        'AlertDialogCancel': 'feedback',
        'Progress': 'feedback',
        'Skeleton': 'feedback',
        'Toaster': 'feedback',

        # Navigation
        'Breadcrumb': 'navigation', 'BreadcrumbList': 'navigation',
        'BreadcrumbItem': 'navigation', 'BreadcrumbLink': 'navigation',
        'BreadcrumbPage': 'navigation', 'BreadcrumbSeparator': 'navigation',
        'BreadcrumbEllipsis': 'navigation',
        'Command': 'navigation', 'CommandDialog': 'navigation',
        'CommandInput': 'navigation', 'CommandList': 'navigation',
        'CommandEmpty': 'navigation', 'CommandGroup': 'navigation',
        'CommandItem': 'navigation', 'CommandSeparator': 'navigation',
        'CommandShortcut': 'navigation',
        'ContextMenu': 'navigation', 'ContextMenuTrigger': 'navigation',
        'ContextMenuContent': 'navigation', 'ContextMenuItem': 'navigation',
        'ContextMenuSub': 'navigation', 'ContextMenuSubTrigger': 'navigation',
        'ContextMenuSubContent': 'navigation',
        'ContextMenuCheckboxItem': 'navigation',
        'ContextMenuRadioGroup': 'navigation',
        'ContextMenuRadioItem': 'navigation',
        'ContextMenuLabel': 'navigation', 'ContextMenuSeparator': 'navigation',
        'Dialog': 'navigation', 'DialogTrigger': 'navigation',
        'DialogContent': 'navigation', 'DialogHeader': 'navigation',
        'DialogTitle': 'navigation', 'DialogDescription': 'navigation',
        'DialogFooter': 'navigation', 'DialogClose': 'navigation',
        'Drawer': 'navigation', 'DrawerTrigger': 'navigation',
        'DrawerContent': 'navigation', 'DrawerHeader': 'navigation',
        'DrawerTitle': 'navigation', 'DrawerDescription': 'navigation',
        'DrawerFooter': 'navigation', 'DrawerClose': 'navigation',
        'DropdownMenu': 'navigation', 'DropdownMenuTrigger': 'navigation',
        'DropdownMenuContent': 'navigation', 'DropdownMenuItem': 'navigation',
        'DropdownMenuSub': 'navigation', 'DropdownMenuSubTrigger': 'navigation',
        'DropdownMenuSubContent': 'navigation',
        'DropdownMenuCheckboxItem': 'navigation',
        'DropdownMenuRadioGroup': 'navigation',
        'DropdownMenuRadioItem': 'navigation',
        'DropdownMenuLabel': 'navigation', 'DropdownMenuSeparator': 'navigation',
        'DropdownMenuGroup': 'navigation', 'DropdownMenuPortal': 'navigation',
        'DropdownMenuShortcut': 'navigation',
        'Menubar': 'navigation', 'MenubarMenu': 'navigation',
        'MenubarTrigger': 'navigation', 'MenubarContent': 'navigation',
        'MenubarItem': 'navigation', 'MenubarSub': 'navigation',
        'MenubarSubTrigger': 'navigation', 'MenubarSubContent': 'navigation',
        'MenubarCheckboxItem': 'navigation',
        'MenubarRadioGroup': 'navigation', 'MenubarRadioItem': 'navigation',
        'MenubarSeparator': 'navigation', 'MenubarLabel': 'navigation',
        'MenubarShortcut': 'navigation', 'MenubarGroup': 'navigation',
        'NavigationMenu': 'navigation', 'NavigationMenuList': 'navigation',
        'NavigationMenuItem': 'navigation', 'NavigationMenuLink': 'navigation',
        'NavigationMenuTrigger': 'navigation',
        'NavigationMenuContent': 'navigation',
        'NavigationMenuIndicator': 'navigation',
        'NavigationMenuViewport': 'navigation',
        'Pagination': 'navigation', 'PaginationContent': 'navigation',
        'PaginationItem': 'navigation', 'PaginationLink': 'navigation',
        'PaginationPrevious': 'navigation', 'PaginationNext': 'navigation',
        'PaginationEllipsis': 'navigation',
        'Popover': 'navigation', 'PopoverTrigger': 'navigation',
        'PopoverContent': 'navigation', 'PopoverAnchor': 'navigation',
    }

    # Radix UI primitives that shadcn/ui wraps
    RADIX_PRIMITIVES = {
        'accordion': '@radix-ui/react-accordion',
        'alert-dialog': '@radix-ui/react-alert-dialog',
        'aspect-ratio': '@radix-ui/react-aspect-ratio',
        'avatar': '@radix-ui/react-avatar',
        'checkbox': '@radix-ui/react-checkbox',
        'collapsible': '@radix-ui/react-collapsible',
        'context-menu': '@radix-ui/react-context-menu',
        'dialog': '@radix-ui/react-dialog',
        'dropdown-menu': '@radix-ui/react-dropdown-menu',
        'hover-card': '@radix-ui/react-hover-card',
        'label': '@radix-ui/react-label',
        'menubar': '@radix-ui/react-menubar',
        'navigation-menu': '@radix-ui/react-navigation-menu',
        'popover': '@radix-ui/react-popover',
        'progress': '@radix-ui/react-progress',
        'radio-group': '@radix-ui/react-radio-group',
        'scroll-area': '@radix-ui/react-scroll-area',
        'select': '@radix-ui/react-select',
        'separator': '@radix-ui/react-separator',
        'slider': '@radix-ui/react-slider',
        'slot': '@radix-ui/react-slot',
        'switch': '@radix-ui/react-switch',
        'tabs': '@radix-ui/react-tabs',
        'toast': '@radix-ui/react-toast',
        'toggle': '@radix-ui/react-toggle',
        'toggle-group': '@radix-ui/react-toggle-group',
        'tooltip': '@radix-ui/react-tooltip',
    }

    # Import path patterns for shadcn/ui components
    SHADCN_IMPORT_PATTERNS = [
        # Standard shadcn/ui import paths
        re.compile(r"""from\s+['"]@/components/ui/([^'"]+)['"]"""),
        re.compile(r"""from\s+['"]~/components/ui/([^'"]+)['"]"""),
        re.compile(r"""from\s+['"]@/components/([^'"]+)['"]"""),
        re.compile(r"""from\s+['"]components/ui/([^'"]+)['"]"""),
        re.compile(r"""from\s+['"]\.\.?/(?:components/)?ui/([^'"]+)['"]"""),
        # src prefix variants
        re.compile(r"""from\s+['"]@/src/components/ui/([^'"]+)['"]"""),
        re.compile(r"""from\s+['"]src/components/ui/([^'"]+)['"]"""),
    ]

    # Radix UI import detection
    RADIX_IMPORT_RE = re.compile(
        r"""from\s+['"](@radix-ui/react-[\w-]+)['"]""",
        re.MULTILINE,
    )

    # JSX component usage (self-closing and paired)
    COMPONENT_USAGE_RE = re.compile(
        r'<(\w+)(?:\s|\.|/|>)',
        re.MULTILINE,
    )

    # Component props extraction
    PROPS_RE = re.compile(
        r'<(\w+)\s+([^>]+?)(?:/>|>)',
        re.MULTILINE | re.DOTALL,
    )

    # Variant/size prop extraction
    VARIANT_PROP_RE = re.compile(
        r"""variant\s*=\s*['"](\w+)['"]""",
    )
    SIZE_PROP_RE = re.compile(
        r"""size\s*=\s*['"](\w+)['"]""",
    )

    # className prop (for customization detection)
    CLASSNAME_RE = re.compile(
        r'className\s*=',
    )

    # CVA definition detection (in component source files)
    CVA_RE = re.compile(
        r"""(?:const|let)\s+(\w+)\s*=\s*cva\s*\(""",
        re.MULTILINE,
    )

    # CVA variants extraction
    CVA_VARIANTS_RE = re.compile(
        r"""variants\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}""",
        re.DOTALL,
    )

    # Export detection for registry components
    EXPORT_RE = re.compile(
        r"""export\s+(?:const|function|default)\s+(\w+)""",
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract shadcn/ui component information from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components' and 'registry_components' lists
        """
        result: Dict[str, Any] = {
            'components': [],
            'registry_components': [],
        }

        if not content or not content.strip():
            return result

        # Detect if this is a component source file (in ui/ directory)
        is_registry = self._is_registry_component(file_path)

        if is_registry:
            reg_comp = self._extract_registry_component(content, file_path)
            if reg_comp:
                result['registry_components'].append(reg_comp)

        # Extract component usage from imports and JSX
        components = self._extract_component_usage(content, file_path)
        result['components'] = components

        return result

    def _is_registry_component(self, file_path: str) -> bool:
        """Check if the file is a shadcn/ui registry component (in ui/ dir)."""
        if not file_path:
            return False
        normalized = file_path.replace('\\', '/')
        return '/ui/' in normalized and (
            normalized.endswith('.tsx') or normalized.endswith('.jsx')
        )

    def _extract_registry_component(
        self, content: str, file_path: str
    ) -> Optional[ShadcnRegistryComponentInfo]:
        """Extract info about a shadcn/ui registry component definition."""
        # Get component name from file path
        name = file_path.replace('\\', '/').split('/')[-1]
        name = re.sub(r'\.\w+$', '', name)  # remove extension

        info = ShadcnRegistryComponentInfo(
            name=name,
            file=file_path,
            line_number=1,
            component_path=file_path,
        )

        # CVA detection
        cva_matches = self.CVA_RE.findall(content)
        info.has_cva = len(cva_matches) > 0

        # cn() detection
        info.has_cn = 'cn(' in content

        # Radix UI dependency detection
        radix_matches = self.RADIX_IMPORT_RE.findall(content)
        info.radix_dependencies = list(set(radix_matches))

        # Export detection
        info.exports = self.EXPORT_RE.findall(content)

        # CVA variant/size extraction
        for cva_match in self.CVA_VARIANTS_RE.finditer(content):
            variants_block = cva_match.group(1)
            # Extract variant names
            variant_keys = re.findall(
                r'(\w+)\s*:', variants_block
            )
            for key in variant_keys:
                if key == 'variant':
                    # Extract variant values
                    variant_section = re.search(
                        r'variant\s*:\s*\{([^}]+)\}', variants_block
                    )
                    if variant_section:
                        vals = re.findall(
                            r'(\w+)\s*:', variant_section.group(1)
                        )
                        info.variant_names.extend(vals)
                elif key == 'size':
                    size_section = re.search(
                        r'size\s*:\s*\{([^}]+)\}', variants_block
                    )
                    if size_section:
                        vals = re.findall(
                            r'(\w+)\s*:', size_section.group(1)
                        )
                        info.size_names.extend(vals)

        return info

    def _extract_component_usage(
        self, content: str, file_path: str
    ) -> List[ShadcnComponentInfo]:
        """Extract shadcn/ui component usage from imports and JSX."""
        components: List[ShadcnComponentInfo] = []
        seen: set = set()

        # Step 1: Find shadcn/ui imports
        imported_components: Dict[str, str] = {}  # name -> import_path
        for pattern in self.SHADCN_IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                import_source = match.group(0)
                ui_module = match.group(1)
                # Extract named imports
                full_line = self._get_import_line(content, match.start())
                names = self._extract_import_names(full_line)
                for name in names:
                    imported_components[name] = ui_module

        # Step 2: Scan for JSX usage of known shadcn/ui components
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for comp_match in self.COMPONENT_USAGE_RE.finditer(line):
                comp_name = comp_match.group(1)
                if comp_name in self.COMPONENT_CATEGORIES or comp_name in imported_components:
                    key = f"{comp_name}:{line_num}"
                    if key in seen:
                        continue
                    seen.add(key)

                    # Extract props from JSX
                    props_used = self._extract_props(line, comp_name)
                    variant = ""
                    size = ""
                    has_custom_class = False

                    variant_match = self.VARIANT_PROP_RE.search(line)
                    if variant_match:
                        variant = variant_match.group(1)

                    size_match = self.SIZE_PROP_RE.search(line)
                    if size_match:
                        size = size_match.group(1)

                    if self.CLASSNAME_RE.search(line):
                        has_custom_class = True

                    # Determine category
                    category = self.COMPONENT_CATEGORIES.get(comp_name, "")

                    # Determine import path
                    import_path = imported_components.get(comp_name, "")

                    # Detect sub-components
                    sub_components = self._detect_sub_components(
                        comp_name, content
                    )

                    components.append(ShadcnComponentInfo(
                        name=comp_name,
                        file=file_path,
                        line_number=line_num,
                        import_path=import_path,
                        category=category,
                        props_used=props_used,
                        variant=variant,
                        size=size,
                        has_custom_className=has_custom_class,
                        is_composition=len(sub_components) > 0,
                        sub_components=sub_components,
                    ))

        return components

    def _get_import_line(self, content: str, start: int) -> str:
        """Get the full import statement containing the position."""
        # Find the start of the import
        line_start = content.rfind('\n', 0, start) + 1
        # Find the end (could be multi-line)
        idx = start
        brace_depth = 0
        while idx < len(content):
            ch = content[idx]
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
            elif ch in ("'", '"'):
                # Skip to end of string
                quote = ch
                idx += 1
                while idx < len(content) and content[idx] != quote:
                    idx += 1
            elif ch == '\n' and brace_depth <= 0:
                break
            idx += 1
        return content[line_start:idx]

    def _extract_import_names(self, import_line: str) -> List[str]:
        """Extract named imports from an import statement."""
        match = re.search(r'\{([^}]+)\}', import_line)
        if not match:
            # Default import
            default_match = re.search(
                r'import\s+(\w+)\s+from', import_line
            )
            if default_match:
                return [default_match.group(1)]
            return []
        names_str = match.group(1)
        names = []
        for part in names_str.split(','):
            part = part.strip()
            if ' as ' in part:
                # import { X as Y } — use alias Y
                alias = part.split(' as ')[-1].strip()
                names.append(alias)
            elif part:
                names.append(part)
        return names

    def _extract_props(self, line: str, comp_name: str) -> List[str]:
        """Extract prop names from a JSX component usage line."""
        # Find the component tag and its props
        pattern = re.compile(
            rf'<{re.escape(comp_name)}\s+([^>]+?)(?:/>|>)',
            re.DOTALL,
        )
        match = pattern.search(line)
        if not match:
            return []
        props_str = match.group(1)
        # Extract prop names (key= or key without =)
        props = re.findall(r'(\w+)\s*=', props_str)
        return props[:15]

    def _detect_sub_components(
        self, base_name: str, content: str
    ) -> List[str]:
        """Detect sub-component usage (e.g., Card with CardHeader, CardContent)."""
        sub_components = []
        # Common sub-component patterns for shadcn/ui
        sub_prefixes = {
            'Card': ['CardHeader', 'CardTitle', 'CardDescription',
                     'CardContent', 'CardFooter'],
            'Dialog': ['DialogTrigger', 'DialogContent', 'DialogHeader',
                       'DialogTitle', 'DialogDescription', 'DialogFooter',
                       'DialogClose'],
            'Sheet': ['SheetTrigger', 'SheetContent', 'SheetHeader',
                      'SheetTitle', 'SheetDescription', 'SheetFooter',
                      'SheetClose'],
            'Drawer': ['DrawerTrigger', 'DrawerContent', 'DrawerHeader',
                       'DrawerTitle', 'DrawerDescription', 'DrawerFooter',
                       'DrawerClose'],
            'AlertDialog': ['AlertDialogTrigger', 'AlertDialogContent',
                           'AlertDialogHeader', 'AlertDialogTitle',
                           'AlertDialogDescription', 'AlertDialogFooter',
                           'AlertDialogAction', 'AlertDialogCancel'],
            'DropdownMenu': ['DropdownMenuTrigger', 'DropdownMenuContent',
                            'DropdownMenuItem', 'DropdownMenuSeparator',
                            'DropdownMenuLabel', 'DropdownMenuGroup'],
            'Select': ['SelectTrigger', 'SelectValue', 'SelectContent',
                       'SelectItem', 'SelectGroup', 'SelectLabel'],
            'Accordion': ['AccordionItem', 'AccordionTrigger',
                         'AccordionContent'],
            'Tabs': ['TabsList', 'TabsTrigger', 'TabsContent'],
            'Table': ['TableHeader', 'TableBody', 'TableRow',
                      'TableHead', 'TableCell', 'TableCaption',
                      'TableFooter'],
            'Tooltip': ['TooltipTrigger', 'TooltipContent',
                        'TooltipProvider'],
            'NavigationMenu': ['NavigationMenuList', 'NavigationMenuItem',
                               'NavigationMenuLink',
                               'NavigationMenuTrigger',
                               'NavigationMenuContent'],
            'Command': ['CommandInput', 'CommandList', 'CommandEmpty',
                        'CommandGroup', 'CommandItem',
                        'CommandSeparator', 'CommandShortcut'],
            'Breadcrumb': ['BreadcrumbList', 'BreadcrumbItem',
                           'BreadcrumbLink', 'BreadcrumbPage',
                           'BreadcrumbSeparator'],
            'Sidebar': ['SidebarContent', 'SidebarGroup',
                        'SidebarGroupLabel', 'SidebarGroupContent',
                        'SidebarMenu', 'SidebarMenuItem',
                        'SidebarMenuButton', 'SidebarProvider',
                        'SidebarTrigger'],
            'Form': ['FormField', 'FormItem', 'FormLabel',
                     'FormControl', 'FormDescription', 'FormMessage'],
            'Avatar': ['AvatarImage', 'AvatarFallback'],
            'HoverCard': ['HoverCardTrigger', 'HoverCardContent'],
            'Popover': ['PopoverTrigger', 'PopoverContent'],
            'ContextMenu': ['ContextMenuTrigger', 'ContextMenuContent',
                           'ContextMenuItem', 'ContextMenuSeparator'],
            'Menubar': ['MenubarMenu', 'MenubarTrigger',
                        'MenubarContent', 'MenubarItem',
                        'MenubarSeparator'],
            'Carousel': ['CarouselContent', 'CarouselItem',
                         'CarouselPrevious', 'CarouselNext'],
            'Pagination': ['PaginationContent', 'PaginationItem',
                           'PaginationLink', 'PaginationPrevious',
                           'PaginationNext', 'PaginationEllipsis'],
            'InputOTP': ['InputOTPGroup', 'InputOTPSlot',
                         'InputOTPSeparator'],
            'Alert': ['AlertTitle', 'AlertDescription'],
            'Collapsible': ['CollapsibleTrigger', 'CollapsibleContent'],
        }

        if base_name in sub_prefixes:
            for sub in sub_prefixes[base_name]:
                if re.search(rf'<{sub}[\s/>]', content):
                    sub_components.append(sub)

        return sub_components
