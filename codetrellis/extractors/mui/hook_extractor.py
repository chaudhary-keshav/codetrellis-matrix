"""
MUI Hook Extractor for CodeTrellis

Extracts Material UI hook usage from React/TypeScript source code.
Covers MUI v4.x through v6.x hooks:
- useTheme: Access the theme object
- useMediaQuery: CSS media query hook
- useScrollTrigger: Scroll-based triggers
- useAutocomplete: Autocomplete headless logic
- useColorScheme: v6 color scheme switcher
- usePagination: Pagination headless logic
- useFormControl: Form control context
- useInput: Input headless logic
- useSlider: Slider headless logic
- useSwitch: Switch headless logic
- useBadge: Badge headless logic
- useMenu: Menu headless logic
- useSelect: Select headless logic
- useTab: Tab headless logic
- useTabsList: Tabs list headless logic
- useOption: Option headless logic
- Joy UI hooks (useColorInversion, useThemeWithoutDefault)
- Custom MUI-related hooks (useMui* patterns)
- MUI X hooks (useGridApiRef, useGridApiContext)

Part of CodeTrellis v4.36 - Material UI (MUI) Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MuiHookUsageInfo:
    """Information about a MUI hook usage."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""    # @mui/material, @mui/base, @mui/joy, etc.
    category: str = ""         # theme, media, form, headless, x-grid, color
    arguments: List[str] = field(default_factory=list)
    parent_component: str = ""


@dataclass
class MuiCustomHookInfo:
    """Information about a custom MUI-related hook."""
    name: str
    file: str = ""
    line_number: int = 0
    hooks_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    parameters: List[str] = field(default_factory=list)


class MuiHookExtractor:
    """
    Extracts MUI hook usage from source code.

    Detects:
    - Built-in MUI hooks from @mui/material, @mui/system, @mui/base
    - Joy UI hooks from @mui/joy
    - MUI X hooks from @mui/x-data-grid, @mui/x-date-pickers
    - Custom hooks that wrap MUI hooks
    """

    # Known MUI hooks and their categories
    MUI_HOOKS = {
        # Theme hooks
        'useTheme': 'theme',
        'useThemeProps': 'theme',
        'useColorScheme': 'theme',
        'useColorInversion': 'theme',
        'useThemeWithoutDefault': 'theme',

        # Media/Responsive hooks
        'useMediaQuery': 'media',
        'useScrollTrigger': 'media',

        # Form hooks
        'useFormControl': 'form',
        'useFormControlContext': 'form',
        'useInput': 'form',

        # Headless/unstyled hooks (Base UI / MUI Base)
        'useAutocomplete': 'headless',
        'usePagination': 'headless',
        'useSlider': 'headless',
        'useSwitch': 'headless',
        'useBadge': 'headless',
        'useMenu': 'headless',
        'useMenuItem': 'headless',
        'useSelect': 'headless',
        'useOption': 'headless',
        'useOptionGroup': 'headless',
        'useTab': 'headless',
        'useTabsList': 'headless',
        'useTabPanel': 'headless',
        'useButton': 'headless',
        'useDropdown': 'headless',
        'useMenuButton': 'headless',
        'useSnackbar': 'headless',
        'useNumberInput': 'headless',
        'usePopup': 'headless',
        'useTransition': 'headless',

        # MUI X Data Grid hooks
        'useGridApiRef': 'x-grid',
        'useGridApiContext': 'x-grid',
        'useGridRootProps': 'x-grid',
        'useGridSelector': 'x-grid',
        'useGridApiEventHandler': 'x-grid',

        # MUI X Date Picker hooks
        'useDateField': 'x-date',
        'useTimeField': 'x-date',
        'useDateTimeField': 'x-date',
        'useClearableField': 'x-date',

        # MUI X Tree View hooks
        'useTreeViewApiRef': 'x-tree',
        'useTreeItem2': 'x-tree',

        # Utility hooks
        'useForkRef': 'utility',
        'useEventCallback': 'utility',
        'useControlled': 'utility',
        'useId': 'utility',
        'useEnhancedEffect': 'utility',
        'usePreviousProps': 'utility',
        'useIsFocusVisible': 'utility',
    }

    # MUI hook import sources
    HOOK_IMPORT_PATTERN = re.compile(
        r"import\s+\{[^}]*\b(use\w+)\b[^}]*\}\s+from\s+['\"](@mui/[\w/\-]+)['\"]",
        re.MULTILINE
    )

    # General MUI hook usage pattern
    HOOK_USAGE_PATTERN = re.compile(
        r"\b(use(?:Theme|MediaQuery|ScrollTrigger|Autocomplete|ColorScheme|"
        r"Pagination|FormControl|Input|Slider|Switch|Badge|Menu|MenuItem|"
        r"Select|Option|Tab|TabsList|TabPanel|Button|Dropdown|MenuButton|"
        r"Snackbar|NumberInput|Popup|Transition|GridApiRef|GridApiContext|"
        r"GridRootProps|GridSelector|GridApiEventHandler|DateField|TimeField|"
        r"DateTimeField|ClearableField|TreeViewApiRef|TreeItem2|"
        r"ForkRef|EventCallback|Controlled|Id|EnhancedEffect|"
        r"ColorInversion|ThemeWithoutDefault|ThemeProps|FormControlContext|"
        r"OptionGroup|PreviousProps|IsFocusVisible))\s*\(",
        re.MULTILINE
    )

    # Custom MUI-related hook definition
    CUSTOM_HOOK_PATTERN = re.compile(
        r"(?:export\s+)?(?:function|const|let|var)\s+(useMui\w+|use\w*Theme\w*|use\w*Style\w*)\s*"
        r"(?:=\s*(?:\([^)]*\)|)\s*(?:=>|{)|\([^)]*\)\s*(?::\s*\w+\s*)?{)",
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the MUI hook extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all MUI hook usage from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'hook_usages', 'custom_hooks' lists
        """
        hook_usages: List[MuiHookUsageInfo] = []
        custom_hooks: List[MuiCustomHookInfo] = []

        # Track imported hooks
        imported_hooks: Dict[str, str] = {}
        for match in self.HOOK_IMPORT_PATTERN.finditer(content):
            hook_name = match.group(1)
            source = match.group(2)
            imported_hooks[hook_name] = source

        # Extract MUI hook usages
        for match in self.HOOK_USAGE_PATTERN.finditer(content):
            hook_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Get category
            category = self.MUI_HOOKS.get(hook_name, 'custom')

            # Extract arguments (simple)
            args_start = match.end()
            args_str = self._extract_args(content, args_start - 1)
            args = [a.strip()[:40] for a in args_str.split(',') if a.strip()] if args_str else []

            hook_usages.append(MuiHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line_number,
                import_source=imported_hooks.get(hook_name, ''),
                category=category,
                arguments=args[:5],
            ))

        # Extract custom MUI-related hooks
        for match in self.CUSTOM_HOOK_PATTERN.finditer(content):
            hook_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Check if exported
            prefix = content[max(0, match.start() - 10):match.start()]
            is_exported = 'export' in prefix or 'export' in content[match.start():match.end()]

            # Find MUI hooks used inside this custom hook
            body_start = content.find('{', match.end())
            if body_start != -1:
                body = self._extract_brace_body(content, body_start)
                hooks_used = [
                    h for h in self.MUI_HOOKS.keys()
                    if h in body
                ]
            else:
                hooks_used = []

            custom_hooks.append(MuiCustomHookInfo(
                name=hook_name,
                file=file_path,
                line_number=line_number,
                hooks_used=hooks_used[:15],
                is_exported=is_exported,
            ))

        return {
            'hook_usages': hook_usages,
            'custom_hooks': custom_hooks,
        }

    def _extract_args(self, content: str, paren_start: int) -> str:
        """Extract arguments from a parenthesized expression."""
        if paren_start >= len(content) or content[paren_start] != '(':
            return ""
        depth = 0
        result = []
        for ch in content[paren_start:paren_start + 500]:
            if ch == '(':
                depth += 1
                if depth > 1:
                    result.append(ch)
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
                result.append(ch)
            else:
                result.append(ch)
        return ''.join(result)

    def _extract_brace_body(self, content: str, start: int, max_chars: int = 2000) -> str:
        """Extract a brace-balanced body."""
        depth = 0
        result = []
        for ch in content[start:start + max_chars]:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
            result.append(ch)
        return ''.join(result)
