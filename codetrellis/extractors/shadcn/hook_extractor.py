"""
shadcn/ui Hook Extractor for CodeTrellis

Extracts hook usage patterns related to shadcn/ui components.
shadcn/ui ships a few hooks as installable primitives via CLI:
- useToast (toast notification state management)
- useMobile / useIsMobile (responsive detection)
- useMediaQuery (custom media query hook)

Additionally detects hooks from the shadcn/ui ecosystem:
- next-themes: useTheme (dark mode toggling)
- @radix-ui/react-*: various Radix hooks
- react-hook-form: useForm (form integration)
- @tanstack/react-table: useReactTable (data table)
- cmdk: useCommandState (command palette)
- vaul: useDrawer (drawer component)
- input-otp: useOTP
- embla-carousel-react: useEmblaCarousel
- recharts: useChart hooks

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShadcnHookUsageInfo:
    """Information about a hook usage related to shadcn/ui."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""      # @/hooks/use-toast, next-themes, etc.
    category: str = ""           # toast, theme, form, table, responsive, carousel
    arguments: List[str] = field(default_factory=list)
    is_shadcn_hook: bool = False  # True if from shadcn/ui hooks dir


@dataclass
class ShadcnCustomHookInfo:
    """Information about a custom hook wrapping shadcn/ui functionality."""
    name: str
    file: str = ""
    line_number: int = 0
    hooks_used: List[str] = field(default_factory=list)
    shadcn_components_used: List[str] = field(default_factory=list)


class ShadcnHookExtractor:
    """
    Extracts shadcn/ui hook usage patterns from React/TypeScript code.

    Detects:
    - shadcn/ui built-in hooks (useToast, useMobile, useIsMobile)
    - next-themes hooks (useTheme)
    - react-hook-form hooks (useForm, useFormField)
    - @tanstack/react-table hooks (useReactTable)
    - Radix UI hooks
    - Custom hooks that wrap shadcn/ui components
    """

    # Known shadcn/ui hooks (installable via CLI)
    SHADCN_HOOKS = {
        'useToast': 'toast',
        'useMobile': 'responsive',
        'useIsMobile': 'responsive',
        'useMediaQuery': 'responsive',
    }

    # Ecosystem hooks commonly used with shadcn/ui
    ECOSYSTEM_HOOKS = {
        # next-themes
        'useTheme': ('theme', 'next-themes'),

        # react-hook-form
        'useForm': ('form', 'react-hook-form'),
        'useFormContext': ('form', 'react-hook-form'),
        'useFormState': ('form', 'react-hook-form'),
        'useFieldArray': ('form', 'react-hook-form'),
        'useWatch': ('form', 'react-hook-form'),
        'useController': ('form', 'react-hook-form'),

        # @tanstack/react-table
        'useReactTable': ('table', '@tanstack/react-table'),
        'useSortBy': ('table', '@tanstack/react-table'),
        'useFilters': ('table', '@tanstack/react-table'),
        'usePagination': ('table', '@tanstack/react-table'),

        # embla-carousel
        'useEmblaCarousel': ('carousel', 'embla-carousel-react'),

        # cmdk
        'useCommandState': ('command', 'cmdk'),

        # vaul (drawer)
        'useDrawer': ('drawer', 'vaul'),

        # sonner (toast)
        'useSonner': ('toast', 'sonner'),

        # react-day-picker
        'useDayPicker': ('calendar', 'react-day-picker'),

        # react-resizable-panels
        'usePanel': ('layout', 'react-resizable-panels'),
        'usePanelGroup': ('layout', 'react-resizable-panels'),
    }

    # Hook detection regex
    HOOK_USAGE_RE = re.compile(
        r"""(?:const|let)\s+(?:\{[^}]*\}|\w+)\s*=\s*(use\w+)\s*\(""",
        re.MULTILINE,
    )

    # Hook import detection
    HOOK_IMPORT_RE = re.compile(
        r"""import\s+\{([^}]*)\}\s+from\s+['"]([^'"]+)['"]""",
        re.MULTILINE,
    )

    # Custom hook definition
    CUSTOM_HOOK_RE = re.compile(
        r"""(?:export\s+)?(?:function|const)\s+(use\w+)\s*(?:\(|=\s*\()""",
        re.MULTILINE,
    )

    # shadcn/ui hook import path patterns
    SHADCN_HOOK_PATHS = [
        re.compile(r"""['"]@/hooks/([^'"]+)['"]"""),
        re.compile(r"""['"]~/hooks/([^'"]+)['"]"""),
        re.compile(r"""['"]@/components/ui/([^'"]+)['"]"""),
        re.compile(r"""['"]\.\.?/hooks/([^'"]+)['"]"""),
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract shadcn/ui hook information from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'hook_usages' and 'custom_hooks' lists
        """
        result: Dict[str, Any] = {
            'hook_usages': [],
            'custom_hooks': [],
        }

        if not content or not content.strip():
            return result

        # Build import map: hook_name -> import_source
        import_map: Dict[str, str] = {}
        for match in self.HOOK_IMPORT_RE.finditer(content):
            names = match.group(1)
            source = match.group(2)
            for name in names.split(','):
                name = name.strip()
                if ' as ' in name:
                    name = name.split(' as ')[0].strip()
                if name.startswith('use'):
                    import_map[name] = source

        # Extract hook usages
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for match in self.HOOK_USAGE_RE.finditer(line):
                hook_name = match.group(1)
                import_source = import_map.get(hook_name, '')

                # Determine category and source
                category = ''
                is_shadcn = False

                if hook_name in self.SHADCN_HOOKS:
                    category = self.SHADCN_HOOKS[hook_name]
                    is_shadcn = True
                elif hook_name in self.ECOSYSTEM_HOOKS:
                    category, _ = self.ECOSYSTEM_HOOKS[hook_name]
                else:
                    # Check if imported from shadcn/ui paths
                    for pattern in self.SHADCN_HOOK_PATHS:
                        if pattern.search(import_source or ''):
                            is_shadcn = True
                            category = 'custom'
                            break

                if category or is_shadcn:
                    result['hook_usages'].append(ShadcnHookUsageInfo(
                        hook_name=hook_name,
                        file=file_path,
                        line_number=line_num,
                        import_source=import_source,
                        category=category,
                        is_shadcn_hook=is_shadcn,
                    ))

        # Detect custom hooks that use shadcn/ui components
        for match in self.CUSTOM_HOOK_RE.finditer(content):
            hook_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check if this custom hook uses shadcn/ui hooks or components
            # Find the function body
            start = match.end()
            hooks_used = []
            shadcn_components = []

            # Simple scan: look for shadcn hooks in nearby content
            body_end = min(start + 2000, len(content))
            body = content[start:body_end]

            for known_hook in list(self.SHADCN_HOOKS.keys()) + [
                'useForm', 'useTheme', 'useReactTable'
            ]:
                if known_hook in body:
                    hooks_used.append(known_hook)

            # Check for shadcn/ui component imports used in the hook
            shadcn_comp_re = re.compile(
                r"""from\s+['"]@/components/ui/""", re.MULTILINE
            )
            if shadcn_comp_re.search(content):
                # Check if any imported shadcn components are used in hook body
                comp_imports = re.findall(
                    r"""import\s+\{([^}]*)\}\s+from\s+['"]@/components/ui/""",
                    content
                )
                for imp_group in comp_imports:
                    for comp in imp_group.split(','):
                        comp = comp.strip()
                        if comp and comp in body:
                            shadcn_components.append(comp)

            if hooks_used or shadcn_components:
                result['custom_hooks'].append(ShadcnCustomHookInfo(
                    name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    hooks_used=hooks_used,
                    shadcn_components_used=shadcn_components,
                ))

        return result
