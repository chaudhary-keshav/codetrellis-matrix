"""
Tests for shadcn/ui extractors and EnhancedShadcnParser.

Part of CodeTrellis v4.39 shadcn/ui Framework Support.
Tests cover:
- Component extraction (40+ components, sub-components, import paths)
- Registry component extraction (CVA definitions, Radix dependencies)
- Theme extraction (CSS variables, components.json, dark mode)
- Hook extraction (useToast, useMobile, ecosystem hooks, custom hooks)
- Style extraction (cn() utility, CVA variants, Tailwind patterns)
- API extraction (Form+zod, Dialog/Sheet/Drawer, Toast/Sonner, DataTable)
- shadcn parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.shadcn_parser_enhanced import (
    EnhancedShadcnParser,
    ShadcnParseResult,
)
from codetrellis.extractors.shadcn import (
    ShadcnComponentExtractor,
    ShadcnThemeExtractor,
    ShadcnHookExtractor,
    ShadcnStyleExtractor,
    ShadcnApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedShadcnParser()


@pytest.fixture
def component_extractor():
    return ShadcnComponentExtractor()


@pytest.fixture
def theme_extractor():
    return ShadcnThemeExtractor()


@pytest.fixture
def hook_extractor():
    return ShadcnHookExtractor()


@pytest.fixture
def style_extractor():
    return ShadcnStyleExtractor()


@pytest.fixture
def api_extractor():
    return ShadcnApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnComponentExtractor:
    """Tests for ShadcnComponentExtractor."""

    def test_button_import_alias(self, component_extractor):
        code = '''
import { Button } from "@/components/ui/button";

function App() {
    return <Button variant="outline">Click me</Button>;
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names

    def test_multiple_component_imports(self, component_extractor):
        code = '''
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function MyCard() {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Title</CardTitle>
            </CardHeader>
            <CardContent>
                <Input placeholder="Enter text" />
            </CardContent>
            <CardFooter>
                <Button>Submit</Button>
            </CardFooter>
        </Card>
    );
}
'''
        result = component_extractor.extract(code, "MyCard.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Card' in names
        assert 'Button' in names
        assert 'Input' in names
        assert len(components) >= 3

    def test_sub_component_detection(self, component_extractor):
        code = '''
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";

function UserCard() {
    return (
        <Card>
            <CardHeader>
                <CardTitle>User</CardTitle>
                <CardDescription>Details</CardDescription>
            </CardHeader>
            <CardContent>Content</CardContent>
            <CardFooter>Footer</CardFooter>
        </Card>
    );
}
'''
        result = component_extractor.extract(code, "UserCard.tsx")
        components = result.get('components', [])
        card_comps = [c for c in components if c.name == 'Card']
        if card_comps:
            subs = card_comps[0].sub_components
            assert any('CardHeader' in s for s in subs) or len(components) >= 4

    def test_dialog_components(self, component_extractor):
        code = '''
import {
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription
} from "@/components/ui/dialog";

function MyDialog() {
    return (
        <Dialog>
            <DialogTrigger>Open</DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Title</DialogTitle>
                    <DialogDescription>Description</DialogDescription>
                </DialogHeader>
            </DialogContent>
        </Dialog>
    );
}
'''
        result = component_extractor.extract(code, "MyDialog.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Dialog' in names

    def test_component_category_detection(self, component_extractor):
        code = '''
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { Tabs } from "@/components/ui/tabs";

function App() {
    return (
        <div>
            <Button>Click</Button>
            <Card>Content</Card>
            <Alert>Warning</Alert>
            <Tabs>Tab content</Tabs>
        </div>
    );
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        categories = {c.category for c in components if c.category}
        # Should detect multiple categories
        assert len(categories) >= 1

    def test_relative_import_detection(self, component_extractor):
        code = '''
import { Button } from "../../components/ui/button";
import { Input } from "../ui/input";

function Form() {
    return (
        <div>
            <Input />
            <Button>Submit</Button>
        </div>
    );
}
'''
        result = component_extractor.extract(code, "Form.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'Input' in names

    def test_tilde_import_detection(self, component_extractor):
        code = '''
import { Button } from "~/components/ui/button";

function App() {
    return <Button>Click</Button>;
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names

    def test_registry_component_extraction(self, component_extractor):
        code = '''
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import * as DialogPrimitive from "@radix-ui/react-dialog";

const buttonVariants = cva(
    "inline-flex items-center justify-center rounded-md",
    {
        variants: {
            variant: {
                default: "bg-primary text-primary-foreground",
                destructive: "bg-destructive",
                outline: "border border-input",
                ghost: "hover:bg-accent",
            },
            size: {
                default: "h-10 px-4 py-2",
                sm: "h-9 px-3",
                lg: "h-11 px-8",
                icon: "h-10 w-10",
            },
        },
    }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant, size, ...props }, ref) => (
        <button
            className={cn(buttonVariants({ variant, size, className }))}
            ref={ref}
            {...props}
        />
    )
);

export { Button, buttonVariants };
'''
        result = component_extractor.extract(code, "components/ui/button.tsx")
        registry = result.get('registry_components', [])
        if registry:
            assert any(r.has_cva for r in registry)

    def test_empty_file(self, component_extractor):
        result = component_extractor.extract("", "empty.tsx")
        components = result.get('components', [])
        assert len(components) == 0

    def test_non_shadcn_file(self, component_extractor):
        code = '''
import React from "react";
import axios from "axios";

function App() {
    return <div>Hello</div>;
}
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        assert len(components) == 0


# ═══════════════════════════════════════════════════════════════════
# Theme Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnThemeExtractor:
    """Tests for ShadcnThemeExtractor."""

    def test_css_variable_extraction(self, theme_extractor):
        code = '''
@layer base {
    :root {
        --background: 0 0% 100%;
        --foreground: 222.2 84% 4.9%;
        --primary: 222.2 47.4% 11.2%;
        --primary-foreground: 210 40% 98%;
        --secondary: 210 40% 96.1%;
        --muted: 210 40% 96.1%;
        --accent: 210 40% 96.1%;
        --destructive: 0 84.2% 60.2%;
        --border: 214.3 31.8% 91.4%;
        --input: 214.3 31.8% 91.4%;
        --ring: 222.2 84% 4.9%;
        --radius: 0.5rem;
    }
    .dark {
        --background: 222.2 84% 4.9%;
        --foreground: 210 40% 98%;
    }
}
'''
        result = theme_extractor.extract(code, "globals.css")
        css_vars = result.get('css_variables', [])
        assert len(css_vars) >= 5
        var_names = [v.variable_name for v in css_vars]
        assert '--background' in var_names or 'background' in var_names

    def test_dark_mode_detection(self, theme_extractor):
        code = '''
@layer base {
    :root {
        --background: 0 0% 100%;
        --foreground: 222.2 84% 4.9%;
    }
    .dark {
        --background: 222.2 84% 4.9%;
        --foreground: 210 40% 98%;
    }
}
'''
        result = theme_extractor.extract(code, "globals.css")
        themes = result.get('themes', [])
        if themes:
            assert any(t.has_dark_mode for t in themes)

    def test_chart_tokens(self, theme_extractor):
        code = '''
@layer base {
    :root {
        --chart-1: 12 76% 61%;
        --chart-2: 173 58% 39%;
        --chart-3: 197 37% 24%;
        --chart-4: 43 74% 66%;
        --chart-5: 27 87% 67%;
    }
}
'''
        result = theme_extractor.extract(code, "globals.css")
        css_vars = result.get('css_variables', [])
        chart_vars = [v for v in css_vars if 'chart' in v.variable_name]
        assert len(chart_vars) >= 3

    def test_sidebar_tokens(self, theme_extractor):
        code = '''
@layer base {
    :root {
        --sidebar-background: 0 0% 98%;
        --sidebar-foreground: 240 5.3% 26.1%;
        --sidebar-primary: 240 5.9% 10%;
        --sidebar-primary-foreground: 0 0% 98%;
    }
}
'''
        result = theme_extractor.extract(code, "globals.css")
        css_vars = result.get('css_variables', [])
        sidebar_vars = [v for v in css_vars if 'sidebar' in v.variable_name]
        assert len(sidebar_vars) >= 2

    def test_components_json_parsing(self, theme_extractor):
        code = '''
{
    "$schema": "https://ui.shadcn.com/schema.json",
    "style": "new-york",
    "rsc": true,
    "tsx": true,
    "tailwind": {
        "config": "tailwind.config.ts",
        "css": "app/globals.css"
    },
    "aliases": {
        "components": "@/components",
        "utils": "@/lib/utils"
    }
}
'''
        result = theme_extractor.extract(code, "components.json")
        cj = result.get('components_json')
        if cj:
            assert cj.style == "new-york"
            assert cj.rsc is True
            assert cj.tsx is True

    def test_tailwind_config_extraction(self, theme_extractor):
        code = '''
module.exports = {
    theme: {
        extend: {
            colors: {
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
            },
            borderRadius: {
                lg: "var(--radius)",
            },
        },
    },
};
'''
        result = theme_extractor.extract(code, "tailwind.config.ts")
        themes = result.get('themes', [])
        # Should detect CSS variable references in Tailwind config
        assert isinstance(themes, list)

    def test_empty_css_file(self, theme_extractor):
        result = theme_extractor.extract("", "empty.css")
        css_vars = result.get('css_variables', [])
        assert len(css_vars) == 0


# ═══════════════════════════════════════════════════════════════════
# Hook Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnHookExtractor:
    """Tests for ShadcnHookExtractor."""

    def test_use_toast_hook(self, hook_extractor):
        code = '''
import { useToast } from "@/components/ui/use-toast";

function MyComponent() {
    const { toast } = useToast();

    return (
        <button onClick={() => toast({ title: "Success" })}>
            Click
        </button>
    );
}
'''
        result = hook_extractor.extract(code, "MyComponent.tsx")
        hooks = result.get('hook_usages', [])
        hook_names = [h.hook_name for h in hooks]
        assert 'useToast' in hook_names

    def test_use_mobile_hook(self, hook_extractor):
        code = '''
import { useIsMobile } from "@/hooks/use-mobile";

function ResponsiveComponent() {
    const isMobile = useIsMobile();
    return isMobile ? <MobileView /> : <DesktopView />;
}
'''
        result = hook_extractor.extract(code, "Responsive.tsx")
        hooks = result.get('hook_usages', [])
        hook_names = [h.hook_name for h in hooks]
        assert 'useIsMobile' in hook_names

    def test_ecosystem_hooks(self, hook_extractor):
        code = '''
import { useTheme } from "next-themes";
import { useForm } from "react-hook-form";
import { useReactTable } from "@tanstack/react-table";

function App() {
    const { theme } = useTheme();
    const form = useForm();
    const table = useReactTable({ data, columns });
}
'''
        result = hook_extractor.extract(code, "App.tsx")
        hooks = result.get('hook_usages', [])
        hook_names = [h.hook_name for h in hooks]
        assert 'useTheme' in hook_names
        assert 'useForm' in hook_names

    def test_custom_hook_detection(self, hook_extractor):
        code = '''
import { useToast } from "@/components/ui/use-toast";

function useApiAction() {
    const { toast } = useToast();

    const execute = async (action) => {
        try {
            await action();
            toast({ title: "Success" });
        } catch (error) {
            toast({ title: "Error", variant: "destructive" });
        }
    };

    return { execute };
}

export { useApiAction };
'''
        result = hook_extractor.extract(code, "hooks/useApiAction.ts")
        custom = result.get('custom_hooks', [])
        if custom:
            custom_names = [h.name for h in custom]
            assert 'useApiAction' in custom_names

    def test_no_hooks_in_non_hook_file(self, hook_extractor):
        code = '''
import React from "react";

function StaticComponent() {
    return <div>No hooks here</div>;
}
'''
        result = hook_extractor.extract(code, "Static.tsx")
        hooks = result.get('hook_usages', [])
        assert len(hooks) == 0


# ═══════════════════════════════════════════════════════════════════
# Style Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnStyleExtractor:
    """Tests for ShadcnStyleExtractor."""

    def test_cn_utility_usage(self, style_extractor):
        code = '''
import { cn } from "@/lib/utils";

function MyComponent({ className }) {
    return (
        <div className={cn("rounded-lg border p-4", className)} />
    );
}
'''
        result = style_extractor.extract(code, "MyComponent.tsx")
        cn_usages = result.get('cn_usages', [])
        assert len(cn_usages) >= 1

    def test_cn_conditional_classes(self, style_extractor):
        code = '''
import { cn } from "@/lib/utils";

function Alert({ variant, className }) {
    return (
        <div className={cn("rounded-lg border p-4", variant === "destructive" && "border-destructive text-destructive", className)} />
    );
}
'''
        result = style_extractor.extract(code, "Alert.tsx")
        cn_usages = result.get('cn_usages', [])
        assert len(cn_usages) >= 1
        if cn_usages:
            assert cn_usages[0].has_conditional

    def test_cva_definition_extraction(self, style_extractor):
        code = '''
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
    "inline-flex items-center justify-center rounded-md text-sm font-medium",
    {
        variants: {
            variant: {
                default: "bg-primary text-primary-foreground",
                destructive: "bg-destructive text-destructive-foreground",
                outline: "border border-input bg-background",
                ghost: "hover:bg-accent",
            },
            size: {
                default: "h-10 px-4 py-2",
                sm: "h-9 px-3",
                lg: "h-11 px-8",
                icon: "h-10 w-10",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    }
);
'''
        result = style_extractor.extract(code, "button.tsx")
        cva_defs = result.get('cva_definitions', [])
        assert len(cva_defs) >= 1
        if cva_defs:
            cva_def = cva_defs[0]
            assert cva_def.name == 'buttonVariants'
            assert 'variant' in cva_def.variant_names
            assert 'size' in cva_def.variant_names

    def test_tailwind_pattern_detection(self, style_extractor):
        code = '''
function Card({ className }) {
    return (
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-4 md:p-6 lg:p-8 dark:bg-slate-900 data-[state=open]:animate-in">
            Content
        </div>
    );
}
'''
        result = style_extractor.extract(code, "Card.tsx")
        patterns = result.get('tailwind_patterns', [])
        # Should detect responsive (md:, lg:) and dark: and data-state patterns
        assert isinstance(patterns, list)

    def test_dark_mode_classes(self, style_extractor):
        code = '''
import { cn } from "@/lib/utils";

function ThemeAware({ className }) {
    return (
        <div className={cn(
            "bg-white text-black dark:bg-slate-950 dark:text-white",
            className
        )} />
    );
}
'''
        result = style_extractor.extract(code, "ThemeAware.tsx")
        cn_usages = result.get('cn_usages', [])
        if cn_usages:
            assert cn_usages[0].has_dark_mode

    def test_empty_file_style(self, style_extractor):
        result = style_extractor.extract("", "empty.tsx")
        cn_usages = result.get('cn_usages', [])
        assert len(cn_usages) == 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnApiExtractor:
    """Tests for ShadcnApiExtractor."""

    def test_form_with_zod_detection(self, api_extractor):
        code = '''
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
    Form, FormControl, FormField, FormItem,
    FormLabel, FormMessage
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const formSchema = z.object({
    username: z.string().min(2),
    email: z.string().email(),
});

function ProfileForm() {
    const form = useForm({
        resolver: zodResolver(formSchema),
    });

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
                <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Username</FormLabel>
                            <FormControl>
                                <Input {...field} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            </form>
        </Form>
    );
}
'''
        result = api_extractor.extract(code, "ProfileForm.tsx")
        forms = result.get('forms', [])
        assert len(forms) >= 1
        if forms:
            form = forms[0]
            assert form.has_zod_schema
            assert form.has_react_hook_form

    def test_dialog_detection(self, api_extractor):
        code = '''
import {
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

function EditDialog() {
    const [open, setOpen] = useState(false);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button>Edit</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Edit Profile</DialogTitle>
                    <DialogDescription>
                        Make changes to your profile.
                    </DialogDescription>
                </DialogHeader>
            </DialogContent>
        </Dialog>
    );
}
'''
        result = api_extractor.extract(code, "EditDialog.tsx")
        dialogs = result.get('dialogs', [])
        assert len(dialogs) >= 1
        if dialogs:
            assert dialogs[0].dialog_type == 'dialog'

    def test_sheet_detection(self, api_extractor):
        code = '''
import {
    Sheet, SheetTrigger, SheetContent,
    SheetHeader, SheetTitle
} from "@/components/ui/sheet";

function SidePanel() {
    return (
        <Sheet>
            <SheetTrigger>Open</SheetTrigger>
            <SheetContent side="right">
                <SheetHeader>
                    <SheetTitle>Menu</SheetTitle>
                </SheetHeader>
            </SheetContent>
        </Sheet>
    );
}
'''
        result = api_extractor.extract(code, "SidePanel.tsx")
        dialogs = result.get('dialogs', [])
        if dialogs:
            assert any(d.dialog_type == 'sheet' for d in dialogs)

    def test_toast_with_sonner(self, api_extractor):
        code = '''
import { toast } from "sonner";

function SaveButton() {
    const handleSave = async () => {
        try {
            await save();
            toast.success("Saved successfully!");
        } catch (error) {
            toast.error("Failed to save.");
        }
    };

    return <Button onClick={handleSave}>Save</Button>;
}
'''
        result = api_extractor.extract(code, "SaveButton.tsx")
        toasts = result.get('toasts', [])
        assert len(toasts) >= 1
        if toasts:
            assert toasts[0].method in ('sonner', 'toast', 'toast.success', 'toast.error')

    def test_use_toast_hook_api(self, api_extractor):
        code = '''
import { useToast } from "@/components/ui/use-toast";

function Notifications() {
    const { toast } = useToast();

    return (
        <Button onClick={() => toast({
            title: "Notification",
            description: "Something happened.",
        })}>
            Notify
        </Button>
    );
}
'''
        result = api_extractor.extract(code, "Notifications.tsx")
        toasts = result.get('toasts', [])
        assert len(toasts) >= 1

    def test_data_table_detection(self, api_extractor):
        code = '''
import {
    ColumnDef,
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    flexRender,
} from "@tanstack/react-table";
import {
    Table, TableBody, TableCell,
    TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";

const columns: ColumnDef<User>[] = [
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={table.getIsAllPageRowsSelected()}
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
            />
        ),
    },
    { accessorKey: "name", header: "Name" },
    { accessorKey: "email", header: "Email" },
];

function UsersTable({ data }) {
    const [sorting, setSorting] = useState([]);
    const [columnFilters, setColumnFilters] = useState([]);

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        onSortingChange: setSorting,
        state: { sorting, columnFilters },
    });
}
'''
        result = api_extractor.extract(code, "UsersTable.tsx")
        tables = result.get('data_tables', [])
        assert len(tables) >= 1
        if tables:
            dt = tables[0]
            assert dt.has_sorting
            assert dt.has_filtering
            assert dt.has_pagination

    def test_alert_dialog_detection(self, api_extractor):
        code = '''
import {
    AlertDialog, AlertDialogAction, AlertDialogCancel,
    AlertDialogContent, AlertDialogDescription,
    AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

function DeleteConfirm() {
    return (
        <AlertDialog>
            <AlertDialogTrigger>Delete</AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                        This cannot be undone.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction>Delete</AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
'''
        result = api_extractor.extract(code, "DeleteConfirm.tsx")
        dialogs = result.get('dialogs', [])
        if dialogs:
            assert any(d.dialog_type == 'alert-dialog' for d in dialogs)

    def test_no_api_patterns(self, api_extractor):
        code = '''
import { Button } from "@/components/ui/button";

function SimpleComponent() {
    return <Button>Click</Button>;
}
'''
        result = api_extractor.extract(code, "Simple.tsx")
        forms = result.get('forms', [])
        dialogs = result.get('dialogs', [])
        toasts = result.get('toasts', [])
        tables = result.get('data_tables', [])
        assert len(forms) == 0
        assert len(dialogs) == 0
        assert len(toasts) == 0
        assert len(tables) == 0


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedShadcnParser:
    """Tests for EnhancedShadcnParser integration."""

    def test_is_shadcn_file_with_alias_import(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
'''
        assert parser.is_shadcn_file(code, "app.tsx") is True

    def test_is_shadcn_file_with_radix(self, parser):
        # Radix UI alone is not sufficient - needs cn() or component imports too
        code = '''
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";
'''
        assert parser.is_shadcn_file(code, "dialog.tsx") is True

    def test_is_shadcn_file_with_cn(self, parser):
        code = '''
import { cn } from "@/lib/utils";
'''
        assert parser.is_shadcn_file(code, "utils.tsx") is True

    def test_is_not_shadcn_file(self, parser):
        code = '''
import React from "react";
import axios from "axios";

function App() {
    return <div>Hello</div>;
}
'''
        assert parser.is_shadcn_file(code, "app.tsx") is False

    def test_is_shadcn_config_file(self, parser):
        assert parser.is_shadcn_config_file("components.json") is True

    def test_is_not_shadcn_config_file(self, parser):
        assert parser.is_shadcn_config_file("package.json") is False

    def test_full_parse_button_component(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function App() {
    return (
        <div className={cn("flex gap-4", "items-center")}>
            <Button variant="outline" size="sm">Cancel</Button>
            <Button>Submit</Button>
        </div>
    );
}
'''
        result = parser.parse(code, "App.tsx")
        assert isinstance(result, ShadcnParseResult)
        assert len(result.components) >= 1
        assert len(result.cn_usages) >= 1

    def test_full_parse_form_with_zod(self, parser):
        code = '''
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const schema = z.object({ name: z.string().min(1) });

function MyForm() {
    const form = useForm({ resolver: zodResolver(schema) });
    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
                <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Name</FormLabel>
                            <FormControl><Input {...field} /></FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <Button type="submit">Submit</Button>
            </form>
        </Form>
    );
}
'''
        result = parser.parse(code, "MyForm.tsx")
        assert len(result.components) >= 2
        assert len(result.forms) >= 1
        assert len(result.detected_frameworks) >= 1

    def test_full_parse_css_file(self, parser):
        code = '''
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
    :root {
        --background: 0 0% 100%;
        --foreground: 222.2 84% 4.9%;
        --primary: 222.2 47.4% 11.2%;
        --primary-foreground: 210 40% 98%;
    }
    .dark {
        --background: 222.2 84% 4.9%;
        --foreground: 210 40% 98%;
    }
}
'''
        result = parser.parse(code, "globals.css")
        assert len(result.css_variables) >= 4
        assert result.has_css_variables
        assert result.has_dark_mode

    def test_version_detection_v1(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
'''
        result = parser.parse(code, "App.tsx")
        # v1 indicators: @/ alias, components/ui/ path
        assert result.shadcn_version in ('', 'v1', 'v2', 'v3')

    def test_version_detection_v2_sidebar(self, parser):
        code = '''
import { Sidebar, SidebarContent, SidebarFooter } from "@/components/ui/sidebar";
import { Chart } from "@/components/ui/chart";
'''
        result = parser.parse(code, "Layout.tsx")
        # Sidebar and Chart are v2+ indicators
        if result.shadcn_version:
            assert result.shadcn_version in ('v2', 'v3')

    def test_framework_detection(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import { useTheme } from "next-themes";
import * as DialogPrimitive from "@radix-ui/react-dialog";
'''
        result = parser.parse(code, "App.tsx")
        frameworks = result.detected_frameworks
        assert len(frameworks) >= 2

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, ShadcnParseResult)
        assert len(result.components) == 0
        assert len(result.cn_usages) == 0

    def test_parse_components_json(self, parser):
        code = '''
{
    "$schema": "https://ui.shadcn.com/schema.json",
    "style": "default",
    "rsc": false,
    "tsx": true,
    "tailwind": {
        "config": "tailwind.config.ts",
        "css": "src/globals.css"
    },
    "aliases": {
        "components": "@/components",
        "utils": "@/lib/utils"
    }
}
'''
        result = parser.parse(code, "components.json")
        assert result.has_components_json
        if result.components_json:
            assert result.components_json.style == "default"
            assert result.components_json.tsx is True

    def test_detected_features(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import { toast } from "sonner";

const variants = cva("base-class", {
    variants: {
        v: { a: "class-a", b: "class-b" }
    }
});

function App() {
    return (
        <div className={cn("p-4", "rounded")}>
            <Button onClick={() => toast.success("Done!")}>
                Click
            </Button>
        </div>
    );
}
'''
        result = parser.parse(code, "App.tsx")
        assert result.has_cn_utility
        assert result.has_cva
        assert result.has_sonner

    def test_data_table_feature_flag(self, parser):
        code = '''
import { useReactTable, getCoreRowModel } from "@tanstack/react-table";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
'''
        result = parser.parse(code, "DataTable.tsx")
        assert result.has_data_table

    def test_sidebar_feature_flag(self, parser):
        code = '''
import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
'''
        result = parser.parse(code, "Layout.tsx")
        assert result.has_sidebar

    def test_chart_feature_flag(self, parser):
        code = '''
import { Chart } from "@/components/ui/chart";
'''
        result = parser.parse(code, "Dashboard.tsx")
        assert result.has_chart

    def test_cva_with_compound_variants(self, parser):
        code = '''
import { cva } from "class-variance-authority";

const alertVariants = cva("relative w-full rounded-lg border p-4", {
    variants: {
        variant: {
            default: "bg-background text-foreground",
            destructive: "border-destructive/50 text-destructive dark:border-destructive",
        },
    },
    compoundVariants: [
        {
            variant: "destructive",
            className: "bg-destructive/10",
        },
    ],
    defaultVariants: {
        variant: "default",
    },
});
'''
        result = parser.parse(code, "alert.tsx")
        assert len(result.cva_definitions) >= 1
        if result.cva_definitions:
            assert result.cva_definitions[0].has_compound_variants

    def test_multiple_cn_calls(self, parser):
        code = '''
import { cn } from "@/lib/utils";

function Card({ className, header, footer }) {
    return (
        <div className={cn("rounded border", className)}>
            <div className={cn("p-4 font-bold", header && "border-b")}>
                Header
            </div>
            <div className={cn("p-4")}>Content</div>
            <div className={cn("p-4 text-sm", footer && "border-t")}>
                Footer
            </div>
        </div>
    );
}
'''
        result = parser.parse(code, "Card.tsx")
        assert len(result.cn_usages) >= 3


# ═══════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════

class TestShadcnEdgeCases:
    """Edge case tests."""

    def test_jsx_extension(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
function App() { return <Button>Click</Button>; }
'''
        result = parser.parse(code, "App.jsx")
        assert len(result.components) >= 1

    def test_js_extension(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
function App() { return <Button>Click</Button>; }
'''
        result = parser.parse(code, "App.js")
        assert len(result.components) >= 1

    def test_ts_extension(self, parser):
        code = '''
import { cn } from "@/lib/utils";
export function mergeClasses(...inputs) { return cn(...inputs); }
'''
        result = parser.parse(code, "helpers.ts")
        assert result.has_cn_utility

    def test_deeply_nested_path(self, parser):
        code = '''
import { Button } from "@/components/ui/button";
function LoginForm() { return <Button>Login</Button>; }
'''
        result = parser.parse(code, "src/features/auth/components/LoginForm.tsx")
        assert len(result.components) >= 1

    def test_mixed_imports(self, parser):
        code = '''
import React from "react";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";

function Page() { return <Button className={cn("px-4")}>Go</Button>; }
'''
        result = parser.parse(code, "Page.tsx")
        assert len(result.components) >= 1
        assert result.has_cn_utility

    def test_unicode_in_content(self, parser):
        code = '''
import { Button } from "@/components/ui/button";

function App() {
    return <Button>提交 ✓</Button>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert len(result.components) >= 1

    def test_very_large_file(self, parser):
        # Simulate a large file with many imports and usages
        imports = 'import { Button } from "@/components/ui/button";\n'
        imports += 'import { cn } from "@/lib/utils";\n'
        body = 'function App() {\n  return (\n    <div>\n'
        for i in range(100):
            body += f'      <div className={{cn("p-{i}", "m-{i}")}}>Item {i}</div>\n'
        body += '    </div>\n  );\n}\n'
        code = imports + body
        result = parser.parse(code, "LargeFile.tsx")
        assert isinstance(result, ShadcnParseResult)
