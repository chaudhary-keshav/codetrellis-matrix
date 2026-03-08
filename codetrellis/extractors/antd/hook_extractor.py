"""
Ant Design Hook Extractor for CodeTrellis

Extracts Ant Design hook usage from React/TypeScript source code.
Covers hooks across all Ant Design versions:
- v5.x: useApp (message/notification/modal), useToken, useBreakpoint,
         useWatch, useForm, useFormInstance, useMessage, useNotification,
         useModal
- v4.x: Form.useForm, useBreakpoint
- Pro Components: useModel, useRequest, useIntl

Part of CodeTrellis v4.37 - Ant Design Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AntdHookUsageInfo:
    """Information about an Ant Design hook usage."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""       # antd, @ant-design/pro-components, etc.
    category: str = ""            # form, app, theme, layout, data, pro
    arguments: List[str] = field(default_factory=list)


@dataclass
class AntdCustomHookInfo:
    """Information about a custom hook using Ant Design hooks."""
    name: str
    file: str = ""
    line_number: int = 0
    hooks_used: List[str] = field(default_factory=list)


class AntdHookExtractor:
    """
    Extracts Ant Design hook usage from source code.

    Detects:
    - useApp (v5+ unified message/notification/modal)
    - useToken (v5+ design token access)
    - useMessage, useNotification, useModal (v5+ static methods)
    - Form.useForm / useForm
    - useFormInstance (v5+)
    - useWatch (v5+)
    - useBreakpoint (Grid.useBreakpoint)
    - Pro hooks: useModel, useRequest, useIntl, useAccess
    - Custom hooks that wrap antd hooks
    """

    # Known Ant Design hooks with categories
    KNOWN_HOOKS = {
        # App hooks (v5+)
        'useApp': 'app',
        # Form hooks
        'useForm': 'form',
        'useFormInstance': 'form',
        'useWatch': 'form',
        # Theme hooks (v5+)
        'useToken': 'theme',
        # Layout hooks
        'useBreakpoint': 'layout',
        # Feedback hooks (v5+ static method hooks)
        'useMessage': 'feedback',
        'useNotification': 'feedback',
        'useModal': 'feedback',
        # Navigation hooks
        'useTabBar': 'navigation',
        # Pro hooks
        'useModel': 'pro',
        'useRequest': 'pro',
        'useIntl': 'pro',
        'useAccess': 'pro',
        'useReactTable': 'pro',
    }

    # Hook import patterns
    HOOK_IMPORT_PATTERN = re.compile(
        r"import\s*\{([^}]*(?:use\w+)[^}]*)\}\s*from\s*['\"](?:antd|@ant-design/[^'\"]+)['\"]",
        re.MULTILINE
    )

    # Form.useForm pattern
    FORM_USE_FORM_PATTERN = re.compile(
        r'(?:const|let|var)\s*\[(\w+)\]\s*=\s*Form\.useForm\(\)',
        re.MULTILINE
    )

    # Grid.useBreakpoint
    GRID_USE_BREAKPOINT = re.compile(
        r'(?:const|let|var)\s*(\w+)\s*=\s*Grid\.useBreakpoint\(\)',
        re.MULTILINE
    )

    # Generic hook usage
    HOOK_USAGE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:\[?[\w\s,]*\]?|{[\w\s,]*}|\w+)\s*=\s*(use\w+)\s*\(',
        re.MULTILINE
    )

    # App.useApp pattern
    APP_USE_APP_PATTERN = re.compile(
        r'(?:const|let|var)\s*\{([^}]+)\}\s*=\s*App\.useApp\(\)',
        re.MULTILINE
    )

    # Custom hook definition
    CUSTOM_HOOK_DEF = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(use\w+)\s*[=(]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Ant Design hook information from source code."""
        result = {
            'hook_usages': [],
            'custom_hooks': [],
        }

        if not content or not content.strip():
            return result

        # Track imported hooks
        imported_hooks = set()

        # Extract hook imports
        for match in self.HOOK_IMPORT_PATTERN.finditer(content):
            imports = match.group(1)
            for name in re.findall(r'(use\w+)', imports):
                imported_hooks.add(name)

        # Detect Form.useForm
        for match in self.FORM_USE_FORM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['hook_usages'].append(AntdHookUsageInfo(
                hook_name='useForm',
                file=file_path,
                line_number=line_num,
                import_source='antd',
                category='form',
                arguments=[match.group(1)],
            ))

        # Detect Grid.useBreakpoint
        for match in self.GRID_USE_BREAKPOINT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['hook_usages'].append(AntdHookUsageInfo(
                hook_name='useBreakpoint',
                file=file_path,
                line_number=line_num,
                import_source='antd',
                category='layout',
            ))

        # Detect App.useApp
        for match in self.APP_USE_APP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            destructured = [n.strip() for n in match.group(1).split(',')]
            result['hook_usages'].append(AntdHookUsageInfo(
                hook_name='useApp',
                file=file_path,
                line_number=line_num,
                import_source='antd',
                category='app',
                arguments=destructured,
            ))

        # Detect generic hook usages
        for match in self.HOOK_USAGE_PATTERN.finditer(content):
            hook_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if hook_name in self.KNOWN_HOOKS:
                category = self.KNOWN_HOOKS[hook_name]
                result['hook_usages'].append(AntdHookUsageInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    import_source='antd' if hook_name in imported_hooks else '',
                    category=category,
                ))
            elif hook_name in imported_hooks:
                result['hook_usages'].append(AntdHookUsageInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    import_source='antd',
                    category='other',
                ))

        # Detect custom hooks that use antd hooks
        for match in self.CUSTOM_HOOK_DEF.finditer(content):
            hook_name = match.group(1)
            if hook_name not in self.KNOWN_HOOKS:
                line_num = content[:match.start()].count('\n') + 1
                # Check body for antd hook usage
                body_start = match.start()
                body_end = min(body_start + 3000, len(content))
                body = content[body_start:body_end]

                antd_hooks_used = []
                for known_hook in self.KNOWN_HOOKS:
                    if known_hook in body:
                        antd_hooks_used.append(known_hook)

                # Also check for Form.useForm and similar
                if 'Form.useForm' in body:
                    antd_hooks_used.append('Form.useForm')
                if 'App.useApp' in body:
                    antd_hooks_used.append('App.useApp')

                if antd_hooks_used:
                    result['custom_hooks'].append(AntdCustomHookInfo(
                        name=hook_name,
                        file=file_path,
                        line_number=line_num,
                        hooks_used=antd_hooks_used,
                    ))

        return result
