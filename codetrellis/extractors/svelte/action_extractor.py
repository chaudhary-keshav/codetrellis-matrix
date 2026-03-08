"""
Svelte Action Extractor for CodeTrellis

Extracts action definitions from Svelte source code:
- use: directive action functions
- Action factories (functions returning action objects)
- Action lifecycle methods (update, destroy)
- Parameter types for actions
- Typed actions with Action<> generic

Supports Svelte 3.x through 5.x:
- Svelte 3/4: function-based actions with node, params
- Svelte 5: improved TypeScript action typing

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SvelteActionInfo:
    """Information about a Svelte action definition."""
    name: str
    file: str = ""
    line_number: int = 0
    is_exported: bool = False
    has_parameter: bool = False
    parameter_type: str = ""  # TypeScript type for parameters
    has_update: bool = False  # implements update lifecycle
    has_destroy: bool = False  # implements destroy lifecycle
    return_type: str = ""  # Action return type
    description: str = ""  # JSDoc description


class SvelteActionExtractor:
    """
    Extracts Svelte action definitions.

    An action is a function that receives an HTML element node and
    optionally parameters, and returns an object with update/destroy methods.

    Pattern: export function actionName(node: HTMLElement, params?) { ... }
    """

    # Action function patterns
    # function name(node: HTMLElement, ...) { ... return { update?, destroy? } }
    ACTION_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?function\s+(\w+)\s*\(\s*'
        r'(\w+)\s*:\s*(?:HTMLElement|Element|Node|SVGElement|HTMLInputElement'
        r'|HTML\w+Element)\b'
        r'(?:\s*,\s*(\w+)\s*(?::\s*([^)]+?))?)?'
        r'\s*\)',
        re.MULTILINE
    )

    # Untyped action function pattern - detected by return { destroy/update }
    ACTION_UNTYPED_PATTERN = re.compile(
        r'(?:export\s+)?function\s+(\w+)\s*\(\s*(\w+)'
        r'(?:\s*,\s*(\w+))?\s*\)',
        re.MULTILINE
    )

    # Arrow function action pattern
    ACTION_ARROW_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*(?::\s*Action\s*(?:<([^>]+)>)?)?'
        r'\s*=\s*\(\s*'
        r'(\w+)\s*:\s*(?:HTMLElement|Element|Node|HTML\w+Element)\b'
        r'(?:\s*,\s*(\w+)\s*(?::\s*([^)]+?))?)?'
        r'\s*\)',
        re.MULTILINE
    )

    # Typed Action<> pattern
    TYPED_ACTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*:\s*Action\s*<([^>]+)>'
        r'\s*=',
        re.MULTILINE
    )

    # Return object with update/destroy
    ACTION_RETURN_PATTERN = re.compile(
        r'return\s*\{[^}]*(?:update|destroy)[^}]*\}',
        re.MULTILINE | re.DOTALL
    )

    # Export detection
    EXPORT_PATTERN = re.compile(
        r'export\s+(?:const|let|function)\s+(\w+)',
        re.MULTILINE
    )

    # JSDoc pattern
    JSDOC_PATTERN = re.compile(
        r'/\*\*\s*(.*?)\s*\*/',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract action definitions from source content.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'actions' list
        """
        actions = []
        exported_names = set(self.EXPORT_PATTERN.findall(content))

        # Function-based actions
        for match in self.ACTION_FUNCTION_PATTERN.finditer(content):
            name = match.group(1)
            has_param = match.group(3) is not None
            param_type = (match.group(4) or '').strip()

            # Check for update/destroy in function body
            func_start = match.end()
            brace_count = 0
            func_body = ''
            for i in range(func_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        func_body = content[func_start:i+1]
                        break

            has_update = 'update' in func_body
            has_destroy = 'destroy' in func_body

            action = SvelteActionInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names or 'export' in content[max(0, match.start()-10):match.start()],
                has_parameter=has_param,
                parameter_type=param_type,
                has_update=has_update,
                has_destroy=has_destroy,
            )
            actions.append(action)

        # Untyped function-based actions (detected by return { update/destroy })
        for match in self.ACTION_UNTYPED_PATTERN.finditer(content):
            name = match.group(1)
            has_param = match.group(3) is not None

            # Avoid duplicates with typed actions
            if any(a.name == name for a in actions):
                continue

            # Extract function body
            func_start = match.end()
            brace_count = 0
            func_body = ''
            for i in range(func_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        func_body = content[func_start:i+1]
                        break

            # Only consider it an action if it returns update or destroy
            has_update = bool(re.search(r'\bupdate\b', func_body))
            has_destroy = bool(re.search(r'\bdestroy\b', func_body))
            if not has_update and not has_destroy:
                continue

            action = SvelteActionInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names or 'export' in content[max(0, match.start()-10):match.start()],
                has_parameter=has_param,
                has_update=has_update,
                has_destroy=has_destroy,
            )
            actions.append(action)

        # Arrow function actions
        for match in self.ACTION_ARROW_PATTERN.finditer(content):
            name = match.group(1)
            type_param = match.group(2) or ''
            has_param = match.group(4) is not None
            param_type = (match.group(5) or type_param).strip()

            # Avoid duplicates
            if any(a.name == name for a in actions):
                continue

            action = SvelteActionInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names,
                has_parameter=has_param,
                parameter_type=param_type,
            )
            actions.append(action)

        # Typed Action<> pattern
        for match in self.TYPED_ACTION_PATTERN.finditer(content):
            name = match.group(1)
            type_params = match.group(2)

            # Avoid duplicates
            if any(a.name == name for a in actions):
                continue

            action = SvelteActionInfo(
                name=name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                is_exported=name in exported_names,
                has_parameter=',' in type_params,
                parameter_type=type_params.split(',')[1].strip() if ',' in type_params else '',
                return_type=f'Action<{type_params}>',
            )
            actions.append(action)

        return {'actions': actions}
