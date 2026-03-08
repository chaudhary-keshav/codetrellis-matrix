"""
EnhancedShadcnParser v1.0 - Comprehensive shadcn/ui parser using all extractors.

This parser integrates all shadcn/ui extractors to provide complete parsing of
shadcn/ui usage across React/TypeScript source files (.jsx, .tsx, .js, .ts)
and configuration files (components.json, globals.css, tailwind.config.*).

It runs as a supplementary layer on top of the JavaScript/TypeScript/React
parsers, extracting shadcn/ui-specific semantics. shadcn/ui is NOT a
traditional component library — it copies components into the user's project
via CLI, so detection is based on import paths, file structure, and
configuration files rather than package imports.

Supports:
- shadcn/ui v0.x (initial release — manual component setup, no CLI)
    CRA/Vite integration, manual Radix UI wrapping, manual cn() setup,
    manual theme CSS variables, no components.json

- shadcn/ui v1.x (stable — CLI-based installation)
    `npx shadcn-ui@latest init`, components.json config, @/ alias,
    components/ui/ directory, cn() from @/lib/utils, extendTheme via
    CSS variables in globals.css, Radix UI primitives, CVA variants,
    useToast hook, default/new-york styles, dark mode via class

- shadcn/ui v2.x (v2 update — open source restructure)
    `npx shadcn@latest init/add`, new CLI without -ui suffix,
    new components (sidebar, chart, input-otp, breadcrumb, carousel,
    drawer, resizable, sonner, toggle-group, pagination),
    Chart component (recharts integration), Sidebar component,
    Drawer component (vaul), improved TypeScript, monorepo support,
    registry system for custom components, CSS variable v2 tokens
    (chart-1..5, sidebar-*), blocks feature (pre-built layouts),
    icon library selection (lucide default), RSC support flag

- shadcn/ui v3.x / latest (latest updates)
    Tailwind CSS v4 support (@theme directive, CSS-first config),
    React 19 compatibility, improved registry with custom URLs,
    new components (input-otp v3, multi-select concept),
    lift mode (Radix UI native styling), improved dark mode tokens,
    @shadcn/ui package helpers, flat config ESLint support

Component Detection (40+ components):
- Layout: Accordion, AspectRatio, Card, Collapsible, Resizable,
    ScrollArea, Separator, Sheet, Sidebar, Tabs
- Forms: Button, Calendar, Checkbox, DatePicker, Form, Input,
    InputOTP, Label, RadioGroup, Select, Slider, Switch,
    Textarea, Toggle, ToggleGroup
- Data Display: Avatar, Badge, Carousel, Chart, DataTable,
    HoverCard, Table, Tooltip
- Feedback: Alert, AlertDialog, Progress, Skeleton, Toast/Sonner
- Navigation: Breadcrumb, Command, ContextMenu, Dialog, Drawer,
    DropdownMenu, Menubar, NavigationMenu, Pagination, Popover

Theme System:
- CSS variables in :root and .dark (HSL format)
- Core tokens: background, foreground, primary, secondary, destructive,
    muted, accent, popover, card, border, input, ring, radius
- Chart tokens: chart-1 through chart-5
- Sidebar tokens: sidebar-background, sidebar-foreground, sidebar-primary, etc.
- Dark mode via .dark class (next-themes integration)
- Tailwind CSS config with CSS variable references
- components.json registry configuration

Style System:
- cn() utility (clsx + tailwind-merge)
- CVA (class-variance-authority) for type-safe variants
- Tailwind CSS utility classes
- Data attribute selectors (Radix UI state)
- Responsive Tailwind prefixes (sm:, md:, lg:, xl:, 2xl:)
- Dark mode classes (dark:)

API Patterns:
- Form (react-hook-form + zod validation + FormField composition)
- Dialog/Sheet/Drawer/AlertDialog (controlled/uncontrolled, responsive)
- Toast (useToast hook or sonner library)
- DataTable (@tanstack/react-table with sorting/filtering/pagination)
- Command (cmdk-based command palette / combobox)
- Navigation (sidebar, breadcrumb, navigation-menu)

Framework Ecosystem Detection (30+ patterns):
- Core: shadcn/ui components in components/ui/
- Radix UI: @radix-ui/react-* (25+ primitives)
- Styling: tailwind-merge, clsx, class-variance-authority
- Forms: react-hook-form, @hookform/resolvers, zod
- Tables: @tanstack/react-table
- Toast: sonner, @radix-ui/react-toast
- Icons: lucide-react, @radix-ui/react-icons
- Theme: next-themes
- Drawer: vaul
- Command: cmdk
- Calendar: react-day-picker, date-fns
- Carousel: embla-carousel-react
- OTP: input-otp
- Charts: recharts
- Resizable: react-resizable-panels

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all shadcn/ui extractors
from .extractors.shadcn import (
    ShadcnComponentExtractor, ShadcnComponentInfo, ShadcnRegistryComponentInfo,
    ShadcnThemeExtractor, ShadcnThemeInfo, ShadcnCSSVariableInfo,
    ShadcnComponentsJsonInfo,
    ShadcnHookExtractor, ShadcnHookUsageInfo, ShadcnCustomHookInfo,
    ShadcnStyleExtractor, ShadcnCnUsageInfo, ShadcnCvaInfo,
    ShadcnTailwindPatternInfo,
    ShadcnApiExtractor, ShadcnFormPatternInfo, ShadcnDialogPatternInfo,
    ShadcnToastPatternInfo, ShadcnDataTablePatternInfo,
)


@dataclass
class ShadcnParseResult:
    """Complete parse result for a file with shadcn/ui usage."""
    file_path: str
    file_type: str = "tsx"  # tsx, jsx, css, json

    # Components
    components: List[ShadcnComponentInfo] = field(default_factory=list)
    registry_components: List[ShadcnRegistryComponentInfo] = field(default_factory=list)

    # Theme
    themes: List[ShadcnThemeInfo] = field(default_factory=list)
    css_variables: List[ShadcnCSSVariableInfo] = field(default_factory=list)
    components_json: Optional[ShadcnComponentsJsonInfo] = None

    # Hooks
    hook_usages: List[ShadcnHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[ShadcnCustomHookInfo] = field(default_factory=list)

    # Styles
    cn_usages: List[ShadcnCnUsageInfo] = field(default_factory=list)
    cva_definitions: List[ShadcnCvaInfo] = field(default_factory=list)
    tailwind_patterns: List[ShadcnTailwindPatternInfo] = field(default_factory=list)

    # API patterns
    forms: List[ShadcnFormPatternInfo] = field(default_factory=list)
    dialogs: List[ShadcnDialogPatternInfo] = field(default_factory=list)
    toasts: List[ShadcnToastPatternInfo] = field(default_factory=list)
    data_tables: List[ShadcnDataTablePatternInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    shadcn_version: str = ""  # Detected version (v0, v1, v2, v3)
    has_components_json: bool = False
    has_css_variables: bool = False
    has_dark_mode: bool = False
    has_cn_utility: bool = False
    has_cva: bool = False
    has_sonner: bool = False
    has_data_table: bool = False
    has_sidebar: bool = False
    has_chart: bool = False
    detected_features: List[str] = field(default_factory=list)


class EnhancedShadcnParser:
    """
    Enhanced shadcn/ui parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    (and potentially alongside the React/Tailwind parsers) when shadcn/ui
    is detected. It extracts shadcn/ui-specific semantics that the
    language parsers cannot capture.

    Framework detection supports 30+ shadcn/ui ecosystem patterns.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # shadcn/ui ecosystem framework / library detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core shadcn/ui ────────────────────────────────────────
        'shadcn-ui': re.compile(
            r"""from\s+['"]@/components/ui/|"""
            r"""from\s+['"]~/components/ui/|"""
            r"""from\s+['"]components/ui/|"""
            r"""from\s+['"]\.\./ui/|"""
            r"""from\s+['"]\.\/ui/""",
            re.MULTILINE
        ),

        # ── Radix UI Primitives ──────────────────────────────────
        'radix-ui': re.compile(
            r"""from\s+['"]@radix-ui/react-""",
            re.MULTILINE
        ),
        'radix-slot': re.compile(
            r"""from\s+['"]@radix-ui/react-slot['"]""",
            re.MULTILINE
        ),
        'radix-icons': re.compile(
            r"""from\s+['"]@radix-ui/react-icons['"]""",
            re.MULTILINE
        ),

        # ── Styling ──────────────────────────────────────────────
        'tailwind-merge': re.compile(
            r"""from\s+['"]tailwind-merge['"]""",
            re.MULTILINE
        ),
        'clsx': re.compile(
            r"""from\s+['"]clsx['"]""",
            re.MULTILINE
        ),
        'class-variance-authority': re.compile(
            r"""from\s+['"]class-variance-authority['"]""",
            re.MULTILINE
        ),

        # ── Forms ────────────────────────────────────────────────
        'react-hook-form': re.compile(
            r"""from\s+['"]react-hook-form['"]""",
            re.MULTILINE
        ),
        'hookform-resolvers': re.compile(
            r"""from\s+['"]@hookform/resolvers""",
            re.MULTILINE
        ),
        'zod': re.compile(
            r"""from\s+['"]zod['"]""",
            re.MULTILINE
        ),

        # ── Tables ───────────────────────────────────────────────
        'tanstack-table': re.compile(
            r"""from\s+['"]@tanstack/react-table['"]""",
            re.MULTILINE
        ),

        # ── Toast ────────────────────────────────────────────────
        'sonner': re.compile(
            r"""from\s+['"]sonner['"]""",
            re.MULTILINE
        ),

        # ── Icons ────────────────────────────────────────────────
        'lucide-react': re.compile(
            r"""from\s+['"]lucide-react['"]""",
            re.MULTILINE
        ),

        # ── Theme ────────────────────────────────────────────────
        'next-themes': re.compile(
            r"""from\s+['"]next-themes['"]""",
            re.MULTILINE
        ),

        # ── Drawer ───────────────────────────────────────────────
        'vaul': re.compile(
            r"""from\s+['"]vaul['"]""",
            re.MULTILINE
        ),

        # ── Command ──────────────────────────────────────────────
        'cmdk': re.compile(
            r"""from\s+['"]cmdk['"]""",
            re.MULTILINE
        ),

        # ── Calendar / Date ──────────────────────────────────────
        'react-day-picker': re.compile(
            r"""from\s+['"]react-day-picker['"]""",
            re.MULTILINE
        ),
        'date-fns': re.compile(
            r"""from\s+['"]date-fns""",
            re.MULTILINE
        ),

        # ── Carousel ─────────────────────────────────────────────
        'embla-carousel': re.compile(
            r"""from\s+['"]embla-carousel-react['"]""",
            re.MULTILINE
        ),

        # ── OTP ──────────────────────────────────────────────────
        'input-otp': re.compile(
            r"""from\s+['"]input-otp['"]""",
            re.MULTILINE
        ),

        # ── Charts ───────────────────────────────────────────────
        'recharts': re.compile(
            r"""from\s+['"]recharts['"]""",
            re.MULTILINE
        ),

        # ── Resizable ────────────────────────────────────────────
        'react-resizable-panels': re.compile(
            r"""from\s+['"]react-resizable-panels['"]""",
            re.MULTILINE
        ),

        # ── Next.js integration ──────────────────────────────────
        'next-link': re.compile(
            r"""from\s+['"]next/link['"]""",
            re.MULTILINE
        ),
        'next-image': re.compile(
            r"""from\s+['"]next/image['"]""",
            re.MULTILINE
        ),
        'next-navigation': re.compile(
            r"""from\s+['"]next/navigation['"]""",
            re.MULTILINE
        ),

        # ── cn utility ───────────────────────────────────────────
        'cn-utility': re.compile(
            r"""from\s+['"]@/lib/utils['"]|"""
            r"""from\s+['"]~/lib/utils['"]|"""
            r"""from\s+['"]@/utils['"]""",
            re.MULTILINE
        ),
    }

    # shadcn/ui version detection indicators
    SHADCN_VERSION_INDICATORS = {
        # v3/latest indicators
        '@shadcn/ui': 'v3',
        'tailwindcss@4': 'v3',
        '@theme': 'v3',

        # v2 indicators (new components, new CLI)
        'Sidebar': 'v2',
        'SidebarProvider': 'v2',
        'ChartContainer': 'v2',
        'Drawer': 'v2',
        'InputOTP': 'v2',
        'Breadcrumb': 'v2',
        'Carousel': 'v2',
        'Pagination': 'v2',
        'Resizable': 'v2',
        'Sonner': 'v2',
        'ToggleGroup': 'v2',
        'chart-1': 'v2',
        'sidebar-background': 'v2',
        'iconLibrary': 'v2',

        # v1 indicators (basic components, initial CLI)
        'components.json': 'v1',
        '@/components/ui/': 'v1',
        'cn(': 'v1',
        'cva(': 'v1',
    }

    VERSION_PRIORITY = {'v3': 3, 'v2': 2, 'v1': 1, 'v0': 0}

    # Configuration file patterns
    CONFIG_FILE_PATTERNS = {
        'components.json',
    }

    # CSS/theme file patterns
    THEME_FILE_PATTERNS = re.compile(
        r'(?:globals?|app|index|styles?)\.css$',
        re.IGNORECASE,
    )

    def __init__(self):
        """Initialize the parser with all shadcn/ui extractors."""
        self.component_extractor = ShadcnComponentExtractor()
        self.theme_extractor = ShadcnThemeExtractor()
        self.hook_extractor = ShadcnHookExtractor()
        self.style_extractor = ShadcnStyleExtractor()
        self.api_extractor = ShadcnApiExtractor()

    def parse(self, content: str, file_path: str = "") -> ShadcnParseResult:
        """
        Parse source code and extract all shadcn/ui-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when shadcn/ui is detected. It extracts component usage, theme
        configuration, hook patterns, styling approaches, and API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ShadcnParseResult with all extracted shadcn/ui information
        """
        result = ShadcnParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Detect file type
        normalized = file_path.replace('\\', '/')
        if normalized.endswith('.tsx'):
            result.file_type = "tsx"
        elif normalized.endswith('.jsx'):
            result.file_type = "jsx"
        elif normalized.endswith('.ts'):
            result.file_type = "ts"
        elif normalized.endswith('.js') or normalized.endswith('.mjs') or normalized.endswith('.cjs'):
            result.file_type = "js"
        elif normalized.endswith('.css'):
            result.file_type = "css"
        elif normalized.endswith('.json'):
            result.file_type = "json"
        else:
            result.file_type = "tsx"

        # ── Detect frameworks ─────────────────────────────────────
        if result.file_type not in ('css', 'json'):
            result.detected_frameworks = self._detect_frameworks(content)

        # ── Theme extraction (CSS and config files) ───────────────
        if result.file_type in ('css', 'json') or 'tailwind.config' in normalized:
            theme_result = self.theme_extractor.extract(content, file_path)
            result.themes = theme_result.get('themes', [])
            result.css_variables = theme_result.get('css_variables', [])
            result.components_json = theme_result.get('components_json')

            if result.components_json:
                result.has_components_json = True

            if result.themes:
                result.has_css_variables = any(t.has_css_variables for t in result.themes)
                result.has_dark_mode = any(t.has_dark_mode for t in result.themes)

            # For CSS/JSON files, we're done
            if result.file_type in ('css', 'json'):
                result.shadcn_version = self._detect_shadcn_version(content, result)
                result.detected_features = self._detect_features(content, result)
                return result

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.registry_components = comp_result.get('registry_components', [])

        # ── Extract hooks ─────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hook_usages = hook_result.get('hook_usages', [])
        result.custom_hooks = hook_result.get('custom_hooks', [])

        # ── Extract styles ────────────────────────────────────────
        style_result = self.style_extractor.extract(content, file_path)
        result.cn_usages = style_result.get('cn_usages', [])
        result.cva_definitions = style_result.get('cva_definitions', [])
        result.tailwind_patterns = style_result.get('tailwind_patterns', [])

        # ── Extract API patterns ──────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.forms = api_result.get('forms', [])
        result.dialogs = api_result.get('dialogs', [])
        result.toasts = api_result.get('toasts', [])
        result.data_tables = api_result.get('data_tables', [])

        # ── Compute metadata flags ────────────────────────────────
        result.has_cn_utility = len(result.cn_usages) > 0 or 'cn(' in content
        result.has_cva = len(result.cva_definitions) > 0
        result.has_sonner = 'sonner' in result.detected_frameworks
        result.has_data_table = (
            len(result.data_tables) > 0
            or '@tanstack/react-table' in content
        )
        result.has_sidebar = (
            any(c.name.startswith('Sidebar') for c in result.components)
            or bool(re.search(
                r"""from\s+['"]@/components/ui/sidebar['"]""", content
            ))
        )
        result.has_chart = (
            any(c.name.startswith('Chart') for c in result.components)
            or bool(re.search(
                r"""from\s+['"]@/components/ui/chart['"]""", content
            ))
        )

        # ── Detect shadcn/ui version ──────────────────────────────
        result.shadcn_version = self._detect_shadcn_version(content, result)

        # ── Detect features ───────────────────────────────────────
        result.detected_features = self._detect_features(content, result)

        return result

    def is_shadcn_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains shadcn/ui code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains shadcn/ui code
        """
        if not content:
            return False

        normalized = file_path.replace('\\', '/')

        # components.json is always a shadcn file
        if normalized.endswith('components.json'):
            # Verify it's actually shadcn components.json
            return '"$schema"' in content or '"style"' in content or '"aliases"' in content

        # CSS files with shadcn/ui theme variables
        if normalized.endswith('.css'):
            return (
                '--background' in content and '--foreground' in content and
                '--primary' in content
            )

        # Component source files in ui/ directory
        if '/ui/' in normalized and (
            normalized.endswith('.tsx') or normalized.endswith('.jsx')
        ):
            return True

        # Check for shadcn/ui component imports
        if re.search(r"""from\s+['"]@/components/ui/""", content):
            return True
        if re.search(r"""from\s+['"]~/components/ui/""", content):
            return True
        if re.search(r"""from\s+['"]components/ui/""", content):
            return True

        # Check for cn() utility import from lib/utils
        if re.search(r"""from\s+['"]@/lib/utils['"]""", content):
            return True

        # Check for CVA import (strong indicator)
        if re.search(r"""from\s+['"]class-variance-authority['"]""", content):
            return True

        # Check for Radix UI + cn() combination (strong indicator)
        if (re.search(r"""from\s+['"]@radix-ui/react-""", content) and
                'cn(' in content):
            return True

        # Check for tailwind.config with CSS variable references
        if 'tailwind.config' in normalized:
            return 'hsl(var(--' in content

        return False

    def is_shadcn_config_file(self, file_path: str) -> bool:
        """Check if file is a shadcn/ui configuration file."""
        normalized = file_path.replace('\\', '/')
        name = normalized.split('/')[-1]
        return name in self.CONFIG_FILE_PATTERNS

    def is_shadcn_theme_file(self, file_path: str) -> bool:
        """Check if file is a potential shadcn/ui theme CSS file."""
        normalized = file_path.replace('\\', '/')
        name = normalized.split('/')[-1]
        return bool(self.THEME_FILE_PATTERNS.search(name))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which shadcn/ui ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return sorted(frameworks)

    def _detect_shadcn_version(
        self, content: str, result: ShadcnParseResult
    ) -> str:
        """
        Detect the shadcn/ui version from imports and patterns.

        Returns version string: 'v0', 'v1', 'v2', 'v3'
        """
        detected_version = ''
        max_priority = -1

        for indicator, version in self.SHADCN_VERSION_INDICATORS.items():
            if indicator in content:
                priority = self.VERSION_PRIORITY.get(version, 0)
                if priority > max_priority:
                    max_priority = priority
                    detected_version = version

        # v2+ indicators from parsed data
        if result.has_sidebar or result.has_chart:
            if self.VERSION_PRIORITY.get('v2', 0) > max_priority:
                detected_version = 'v2'
                max_priority = 2

        # components.json with iconLibrary is v2+
        if result.components_json and result.components_json.icon_library:
            if self.VERSION_PRIORITY.get('v2', 0) > max_priority:
                detected_version = 'v2'
                max_priority = 2

        # CSS variables for chart/sidebar tokens are v2+
        if any(v.is_chart for v in result.css_variables):
            if self.VERSION_PRIORITY.get('v2', 0) > max_priority:
                detected_version = 'v2'

        # Default to v2 if we have shadcn usage but can't determine version
        if not detected_version and (
            result.components or result.cn_usages or result.has_components_json
        ):
            detected_version = 'v2'

        return detected_version

    def _detect_features(
        self, content: str, result: ShadcnParseResult
    ) -> List[str]:
        """Detect shadcn/ui features used in the file."""
        features: List[str] = []

        # Component-level features
        if result.components:
            features.append('shadcn_components')
            categories = set(
                c.category for c in result.components if c.category
            )
            for cat in sorted(categories):
                features.append(f'shadcn_category_{cat}')

        if result.registry_components:
            features.append('registry_components')

        # Theme features
        if result.has_components_json:
            features.append('components_json')
        if result.has_css_variables:
            features.append('css_variables')
        if result.has_dark_mode:
            features.append('dark_mode')
        if any(t.has_chart_colors for t in result.themes):
            features.append('chart_colors')
        if any(t.has_sidebar_tokens for t in result.themes):
            features.append('sidebar_tokens')

        # Style features
        if result.has_cn_utility:
            features.append('cn_utility')
        if result.has_cva:
            features.append('cva_variants')
        if result.tailwind_patterns:
            tw_types = set(p.pattern_type for p in result.tailwind_patterns)
            for tt in sorted(tw_types):
                features.append(f'tailwind_{tt}')

        # Hook features
        if result.hook_usages:
            hook_categories = set(
                h.category for h in result.hook_usages if h.category
            )
            for cat in sorted(hook_categories):
                features.append(f'hooks_{cat}')

        # API features
        if result.forms:
            features.append('form_patterns')
            if any(f.has_zod_schema for f in result.forms):
                features.append('zod_validation')
            if any(f.has_react_hook_form for f in result.forms):
                features.append('react_hook_form')
        if result.dialogs:
            features.append('dialog_patterns')
            dialog_types = set(d.dialog_type for d in result.dialogs)
            for dt in sorted(dialog_types):
                features.append(f'{dt}_pattern')
        if result.toasts:
            features.append('toast_patterns')
        if result.has_sonner:
            features.append('sonner')
        if result.has_data_table:
            features.append('data_table')
        if result.has_sidebar:
            features.append('sidebar')
        if result.has_chart:
            features.append('chart')

        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for f in features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features
