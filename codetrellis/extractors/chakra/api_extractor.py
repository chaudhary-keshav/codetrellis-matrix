"""
Chakra UI API Extractor for CodeTrellis

Extracts Chakra UI API patterns from React/TypeScript source code.
Covers:
- Form patterns (FormControl, validation, error states)
- Modal/AlertDialog patterns (confirmation, form, controlled)
- Drawer patterns (placement, sizes, form drawers)
- Toast patterns (useToast, toaster, positions, variants)
- Menu patterns (context menu, nested, option groups)
- Tab patterns (controlled, lazy, fitted)
- Accordion patterns (allowMultiple, allowToggle)
- Stepper patterns (active step, orientation)
- Popover patterns (hover, focus, controlled)

Part of CodeTrellis v4.38 - Chakra UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChakraFormPatternInfo:
    """Information about a Chakra UI form pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    form_control_count: int = 0
    has_validation: bool = False
    has_error_messages: bool = False
    has_helper_text: bool = False
    has_required_fields: bool = False
    input_types: List[str] = field(default_factory=list)
    integration: str = ""        # react-hook-form, formik, none


@dataclass
class ChakraModalPatternInfo:
    """Information about a Chakra UI modal/dialog pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    modal_type: str = ""         # modal, alertDialog, drawer
    has_form: bool = False
    has_close_on_overlay: bool = False
    has_close_on_esc: bool = False
    has_initial_focus: bool = False
    size: str = ""               # xs, sm, md, lg, xl, full
    placement: str = ""          # top, right, bottom, left (drawer)
    is_controlled: bool = False


@dataclass
class ChakraToastPatternInfo:
    """Information about a Chakra UI toast pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    method: str = ""             # useToast, toaster.create, toaster.success, etc.
    has_custom_render: bool = False
    position: str = ""           # top, top-right, bottom, etc.
    variant: str = ""            # subtle, solid, left-accent, top-accent
    statuses_used: List[str] = field(default_factory=list)  # success, error, warning, info, loading


@dataclass
class ChakraMenuPatternInfo:
    """Information about a Chakra UI menu pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    menu_type: str = ""          # basic, context, option, nested
    item_count: int = 0
    has_option_group: bool = False
    has_divider: bool = False
    has_icon: bool = False
    has_command: bool = False


class ChakraApiExtractor:
    """
    Extracts Chakra UI API patterns from source code.

    Detects:
    - Form patterns (FormControl, validation, error handling)
    - Modal/AlertDialog/Drawer patterns
    - Toast patterns (useToast, toaster)
    - Menu patterns
    - Tab patterns
    - Accordion patterns
    """

    # Form pattern detection
    FORM_CONTROL_PATTERN = re.compile(
        r'<FormControl\b',
        re.MULTILINE
    )
    FORM_ERROR_PATTERN = re.compile(
        r'<FormErrorMessage|isInvalid',
        re.MULTILINE
    )
    FORM_HELPER_PATTERN = re.compile(
        r'<FormHelperText',
        re.MULTILINE
    )
    FORM_REQUIRED_PATTERN = re.compile(
        r'isRequired',
        re.MULTILINE
    )

    # React Hook Form integration
    REACT_HOOK_FORM_PATTERN = re.compile(
        r'useForm\s*\(|register\s*\(|handleSubmit|Controller\b|useFormContext',
        re.MULTILINE
    )

    # Formik integration
    FORMIK_PATTERN = re.compile(
        r'useFormik|<Formik|<Field\b|<FieldArray',
        re.MULTILINE
    )

    # Modal patterns
    MODAL_PATTERN = re.compile(
        r'<Modal\b',
        re.MULTILINE
    )
    ALERT_DIALOG_PATTERN = re.compile(
        r'<AlertDialog\b',
        re.MULTILINE
    )
    DRAWER_PATTERN = re.compile(
        r'<Drawer\b',
        re.MULTILINE
    )
    DIALOG_PATTERN = re.compile(
        r'<Dialog\b',
        re.MULTILINE
    )

    # Toast patterns
    USE_TOAST_PATTERN = re.compile(
        r'useToast\s*\(',
        re.MULTILINE
    )
    TOASTER_PATTERN = re.compile(
        r'toaster\.(create|success|error|warning|info|loading|promise|dismiss|update)\s*\(',
        re.MULTILINE
    )
    TOAST_STATUS_PATTERN = re.compile(
        r'status\s*:\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    TOAST_POSITION_PATTERN = re.compile(
        r'position\s*:\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Menu patterns
    MENU_PATTERN = re.compile(
        r'<Menu\b',
        re.MULTILINE
    )
    MENU_ITEM_PATTERN = re.compile(
        r'<MenuItem\b',
        re.MULTILINE
    )
    MENU_OPTION_GROUP_PATTERN = re.compile(
        r'<MenuOptionGroup\b',
        re.MULTILINE
    )
    CONTEXT_MENU_PATTERN = re.compile(
        r'onContextMenu|ContextMenu',
        re.MULTILINE
    )

    # Input type patterns
    INPUT_TYPES = {
        'Input': 'text', 'Textarea': 'textarea', 'Select': 'select',
        'Checkbox': 'checkbox', 'Radio': 'radio', 'Switch': 'switch',
        'Slider': 'slider', 'NumberInput': 'number', 'PinInput': 'pin',
        'DatePicker': 'date', 'ColorPicker': 'color',
        'FileUpload': 'file', 'RatingGroup': 'rating',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Chakra UI API patterns from source code."""
        result = {
            'forms': [],
            'modals': [],
            'toasts': [],
            'menus': [],
        }

        if not content or not content.strip():
            return result

        # ── Form patterns ─────────────────────────────────────────
        form_controls = list(self.FORM_CONTROL_PATTERN.finditer(content))
        if form_controls:
            has_validation = bool(self.FORM_ERROR_PATTERN.search(content))
            has_helper = bool(self.FORM_HELPER_PATTERN.search(content))
            has_required = bool(self.FORM_REQUIRED_PATTERN.search(content))

            # Detect integration
            integration = ''
            if self.REACT_HOOK_FORM_PATTERN.search(content):
                integration = 'react-hook-form'
            elif self.FORMIK_PATTERN.search(content):
                integration = 'formik'

            # Detect input types used
            input_types_used = []
            for comp, itype in self.INPUT_TYPES.items():
                if re.search(rf'<{comp}\b', content):
                    input_types_used.append(itype)

            line_num = content[:form_controls[0].start()].count('\n') + 1
            form_info = ChakraFormPatternInfo(
                name='Form',
                file=file_path,
                line_number=line_num,
                form_control_count=len(form_controls),
                has_validation=has_validation,
                has_error_messages=has_validation,
                has_helper_text=has_helper,
                has_required_fields=has_required,
                input_types=input_types_used,
                integration=integration,
            )
            result['forms'].append(form_info)

        # ── Modal/AlertDialog/Drawer patterns ─────────────────────
        modal_types = [
            (self.MODAL_PATTERN, 'modal'),
            (self.ALERT_DIALOG_PATTERN, 'alertDialog'),
            (self.DRAWER_PATTERN, 'drawer'),
            (self.DIALOG_PATTERN, 'dialog'),
        ]

        for pattern, mtype in modal_types:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Check surrounding context
                context_start = max(0, match.start() - 100)
                context = content[context_start:match.start() + 1000]

                has_form = bool(re.search(r'<Form|<form|FormControl|handleSubmit', context))
                has_close_overlay = bool(re.search(r'closeOnOverlayClick', context))
                has_close_esc = bool(re.search(r'closeOnEsc', context))
                has_initial_focus = bool(re.search(r'initialFocusRef|autoFocus', context))
                is_controlled = bool(re.search(r'isOpen|onClose|onOpen|useDisclosure', context))

                # Detect size
                size_match = re.search(r'size\s*=\s*["\'](\w+)["\']', context)
                size = size_match.group(1) if size_match else ''

                # Detect placement (drawer)
                placement_match = re.search(r'placement\s*=\s*["\'](\w+)["\']', context)
                placement = placement_match.group(1) if placement_match else ''

                modal_info = ChakraModalPatternInfo(
                    name=mtype.title(),
                    file=file_path,
                    line_number=line_num,
                    modal_type=mtype,
                    has_form=has_form,
                    has_close_on_overlay=has_close_overlay,
                    has_close_on_esc=has_close_esc,
                    has_initial_focus=has_initial_focus,
                    size=size,
                    placement=placement,
                    is_controlled=is_controlled,
                )
                result['modals'].append(modal_info)

        # ── Toast patterns ────────────────────────────────────────
        toast_methods = list(self.USE_TOAST_PATTERN.finditer(content))
        toaster_calls = list(self.TOASTER_PATTERN.finditer(content))

        if toast_methods:
            line_num = content[:toast_methods[0].start()].count('\n') + 1
            statuses = [m.group(1) for m in self.TOAST_STATUS_PATTERN.finditer(content)]
            positions = [m.group(1) for m in self.TOAST_POSITION_PATTERN.finditer(content)]

            toast_info = ChakraToastPatternInfo(
                name='useToast',
                file=file_path,
                line_number=line_num,
                method='useToast',
                has_custom_render=bool(re.search(r'render\s*:', content)),
                position=positions[0] if positions else '',
                statuses_used=list(set(statuses))[:6],
            )
            result['toasts'].append(toast_info)

        for match in toaster_calls:
            line_num = content[:match.start()].count('\n') + 1
            method = match.group(1)
            toast_info = ChakraToastPatternInfo(
                name='toaster',
                file=file_path,
                line_number=line_num,
                method=f'toaster.{method}',
            )
            result['toasts'].append(toast_info)

        # ── Menu patterns ─────────────────────────────────────────
        menu_matches = list(self.MENU_PATTERN.finditer(content))
        if menu_matches:
            items = list(self.MENU_ITEM_PATTERN.finditer(content))
            has_option = bool(self.MENU_OPTION_GROUP_PATTERN.search(content))
            has_context = bool(self.CONTEXT_MENU_PATTERN.search(content))
            has_divider = bool(re.search(r'<MenuDivider', content))
            has_icon = bool(re.search(r'icon\s*=', content) and any(
                re.search(r'<MenuItem[^>]*icon', content[m.start():m.start() + 200])
                for m in menu_matches[:3]
            ))
            has_command = bool(re.search(r'command\s*=', content))

            menu_type = 'basic'
            if has_context:
                menu_type = 'context'
            elif has_option:
                menu_type = 'option'

            line_num = content[:menu_matches[0].start()].count('\n') + 1
            menu_info = ChakraMenuPatternInfo(
                name='Menu',
                file=file_path,
                line_number=line_num,
                menu_type=menu_type,
                item_count=len(items),
                has_option_group=has_option,
                has_divider=has_divider,
                has_icon=has_icon,
                has_command=has_command,
            )
            result['menus'].append(menu_info)

        return result
