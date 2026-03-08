"""
Chakra UI Hook Extractor for CodeTrellis

Extracts Chakra UI hook usage from React/TypeScript source code.
Covers all Chakra UI hooks across versions:
- Disclosure: useDisclosure
- Color Mode: useColorMode, useColorModeValue
- Theme: useTheme, useToken, useChakra
- Media: useBreakpoint, useBreakpointValue, useMediaQuery
- Clipboard: useClipboard
- Form: useBoolean, useControllable, useControllableState, useFormControl
- Animation: useAnimationState, usePrefersReducedMotion
- Responsive: useBreakpoint, useBreakpointValue
- Toast: useToast (v2), toaster (v3)
- Utility: useOutsideClick, useMergeRefs, useCallbackRef
- Custom hooks wrapping Chakra hooks

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChakraHookUsageInfo:
    """Information about a Chakra UI hook usage."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""      # @chakra-ui/react, @chakra-ui/hooks, etc.
    category: str = ""           # disclosure, color-mode, theme, media, clipboard, form, animation, toast, utility
    arguments: List[str] = field(default_factory=list)
    destructured_values: List[str] = field(default_factory=list)


@dataclass
class ChakraCustomHookInfo:
    """Information about a custom hook wrapping Chakra UI hooks."""
    name: str
    file: str = ""
    line_number: int = 0
    hooks_used: List[str] = field(default_factory=list)  # Chakra hooks used inside
    description: str = ""


class ChakraHookExtractor:
    """
    Extracts Chakra UI hook usage from source code.

    Detects:
    - All built-in Chakra UI hooks (20+ hooks)
    - Custom hooks that wrap Chakra hooks
    - Hook destructuring patterns
    - Hook arguments
    """

    # Chakra hook categories
    HOOK_CATEGORIES = {
        # Disclosure hooks
        'useDisclosure': 'disclosure',

        # Color mode hooks
        'useColorMode': 'color-mode',
        'useColorModeValue': 'color-mode',
        'useColorModePreference': 'color-mode',

        # Theme hooks
        'useTheme': 'theme',
        'useToken': 'theme',
        'useChakra': 'theme',
        'useStyleConfig': 'theme',
        'useMultiStyleConfig': 'theme',

        # Media / responsive hooks
        'useBreakpoint': 'media',
        'useBreakpointValue': 'media',
        'useMediaQuery': 'media',

        # Clipboard
        'useClipboard': 'clipboard',

        # Form hooks
        'useBoolean': 'form',
        'useControllable': 'form',
        'useControllableState': 'form',
        'useFormControl': 'form',
        'useFormControlContext': 'form',
        'useCheckbox': 'form',
        'useCheckboxGroup': 'form',
        'useRadio': 'form',
        'useRadioGroup': 'form',
        'useRangeSlider': 'form',
        'useSlider': 'form',
        'useNumberInput': 'form',
        'useEditable': 'form',
        'usePinInput': 'form',

        # Toast hooks
        'useToast': 'toast',
        'createToastFn': 'toast',

        # Animation hooks
        'useAnimationState': 'animation',
        'usePrefersReducedMotion': 'animation',

        # Utility hooks
        'useOutsideClick': 'utility',
        'useMergeRefs': 'utility',
        'useCallbackRef': 'utility',
        'useConst': 'utility',
        'useDimensions': 'utility',
        'useEventListener': 'utility',
        'useFocusOnPointerDown': 'utility',
        'useInterval': 'utility',
        'useLatestRef': 'utility',
        'usePanGesture': 'utility',
        'usePrevious': 'utility',
        'useSafeLayoutEffect': 'utility',
        'useTimeout': 'utility',
        'useUnmountEffect': 'utility',
        'useUpdateEffect': 'utility',
        'useWhyDidYouUpdate': 'utility',
        'useFocusEffect': 'utility',

        # Accordion/Tabs/Menu disclosure hooks
        'useAccordion': 'disclosure',
        'useAccordionItem': 'disclosure',
        'useTabs': 'disclosure',
        'useTab': 'disclosure',
        'useTabPanel': 'disclosure',
        'useMenu': 'disclosure',
        'useMenuItem': 'disclosure',

        # Modal/Dialog hooks
        'useModal': 'overlay',
        'useModalContext': 'overlay',
        'useDrawer': 'overlay',
        'usePopover': 'overlay',
        'useTooltip': 'overlay',

        # Image hooks
        'useImage': 'media',

        # v3/Ark UI hooks
        'useRecipe': 'theme',
        'useSlotRecipe': 'theme',
    }

    # Hook usage pattern: const {...} = useHookName(...)
    HOOK_USAGE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]*)\}|(\w+))\s*=\s*(use\w+)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # Standalone hook call: useHookName(...)
    STANDALONE_HOOK_PATTERN = re.compile(
        r'\b(use(?:Disclosure|ColorMode|ColorModeValue|Theme|Token|Chakra|'
        r'Breakpoint|BreakpointValue|MediaQuery|Clipboard|Boolean|'
        r'Controllable|ControllableState|FormControl|Toast|'
        r'OutsideClick|MergeRefs|StyleConfig|MultiStyleConfig|'
        r'AnimationState|PrefersReducedMotion|Accordion|Tabs|Menu|'
        r'Modal|Drawer|Popover|Tooltip|Image|Recipe|SlotRecipe|'
        r'Checkbox|CheckboxGroup|Radio|RadioGroup|Slider|RangeSlider|'
        r'NumberInput|Editable|PinInput|Interval|Timeout|Previous|'
        r'Const|Dimensions|EventListener|UpdateEffect))\s*\(',
        re.MULTILINE
    )

    # Custom hook definition
    CUSTOM_HOOK_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(use[A-Z]\w+)\s*[=(:]\s*',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Chakra UI hook usage from source code."""
        result = {
            'hook_usages': [],
            'custom_hooks': [],
        }

        if not content or not content.strip():
            return result

        seen_hooks = set()

        # Detect hook usages with destructuring
        for match in self.HOOK_USAGE_PATTERN.finditer(content):
            destructured = match.group(1)
            variable = match.group(2)
            hook_name = match.group(3)
            args = match.group(4)

            if hook_name in self.HOOK_CATEGORIES:
                line_num = content[:match.start()].count('\n') + 1
                deduplication_key = f"{hook_name}:{line_num}"
                if deduplication_key in seen_hooks:
                    continue
                seen_hooks.add(deduplication_key)

                hook_info = ChakraHookUsageInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    category=self.HOOK_CATEGORIES[hook_name],
                    arguments=[a.strip() for a in args.split(',') if a.strip()][:5],
                    destructured_values=[
                        v.strip() for v in (destructured or '').split(',') if v.strip()
                    ][:10],
                )
                result['hook_usages'].append(hook_info)

        # Detect standalone hook calls
        for match in self.STANDALONE_HOOK_PATTERN.finditer(content):
            hook_name = match.group(1)
            if hook_name in self.HOOK_CATEGORIES:
                line_num = content[:match.start()].count('\n') + 1
                deduplication_key = f"{hook_name}:{line_num}"
                if deduplication_key in seen_hooks:
                    continue
                seen_hooks.add(deduplication_key)

                hook_info = ChakraHookUsageInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    category=self.HOOK_CATEGORIES[hook_name],
                )
                result['hook_usages'].append(hook_info)

        # Detect custom hooks wrapping Chakra hooks
        for match in self.CUSTOM_HOOK_PATTERN.finditer(content):
            hook_name = match.group(1)
            if hook_name not in self.HOOK_CATEGORIES:
                line_num = content[:match.start()].count('\n') + 1
                # Look at function body (up to 1500 chars)
                body_start = match.end()
                body = content[body_start:body_start + 1500]

                # Check if any Chakra hooks are used inside
                chakra_hooks_used = []
                for known_hook in self.HOOK_CATEGORIES:
                    if known_hook in body:
                        chakra_hooks_used.append(known_hook)

                if chakra_hooks_used:
                    custom_info = ChakraCustomHookInfo(
                        name=hook_name,
                        file=file_path,
                        line_number=line_num,
                        hooks_used=chakra_hooks_used[:10],
                    )
                    result['custom_hooks'].append(custom_info)

        return result
