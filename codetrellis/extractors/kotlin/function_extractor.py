"""
KotlinFunctionExtractor - Extracts Kotlin function definitions.

Extracts:
- Regular functions (fun)
- Extension functions (Type.fun)
- Suspend functions (coroutines)
- Operator functions
- Infix functions
- Top-level functions
- Lambda expressions (count)
- Higher-order functions

Part of CodeTrellis v4.12 - Kotlin Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KotlinParameterInfo:
    """Information about a Kotlin function parameter."""
    name: str
    type: str
    default_value: Optional[str] = None
    is_vararg: bool = False
    annotations: List[str] = field(default_factory=list)


@dataclass
class KotlinFunctionInfo:
    """Information about a Kotlin function."""
    name: str
    return_type: str = ""
    parameters: List[KotlinParameterInfo] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    receiver_type: Optional[str] = None  # Extension function receiver
    is_suspend: bool = False
    is_inline: bool = False
    is_infix: bool = False
    is_operator: bool = False
    is_tailrec: bool = False
    is_override: bool = False
    is_abstract: bool = False
    is_open: bool = False
    is_private: bool = False
    is_internal: bool = False
    is_extension: bool = False
    generic_params: List[str] = field(default_factory=list)
    class_name: Optional[str] = None
    file: str = ""
    line_number: int = 0
    is_exported: bool = True


class KotlinFunctionExtractor:
    """
    Extracts Kotlin function definitions from source code.

    Handles:
    - Regular functions
    - Extension functions (fun Type.name())
    - Suspend functions (coroutines)
    - Operator, infix, inline, tailrec functions
    - Functions with default parameter values
    - Functions with generic type parameters
    - Vararg parameters
    - Top-level functions and member functions
    """

    # Full function pattern
    FUNCTION_PATTERN = re.compile(
        r'(?:(?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
        r'(?:(public|internal|protected|private)\s+)?'
        r'(?:(override|abstract|open|final)\s+)?'
        r'(?:(suspend|inline|infix|operator|tailrec|external)\s+)*'
        r'fun\s+'
        r'(?:<([^>]+)>\s*)?'  # Generic params
        r'(?:([\w<>,.\s?*]+)\.\s*)?'  # Extension receiver
        r'(\w+)\s*'  # Function name
        r'\(([^)]*)\)\s*'  # Parameters
        r'(?::\s*([\w<>,.\s?*]+?))?'  # Return type
        r'\s*(?:\{|=|$)',
        re.MULTILINE
    )

    # Lambda count pattern
    LAMBDA_PATTERN = re.compile(r'\{[^}]*->')

    def extract(self, content: str, file_path: str = "",
                class_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract all function definitions from Kotlin source code.

        Returns dict with keys: functions, lambda_count
        """
        result = {
            'functions': [],
            'lambda_count': 0,
        }

        if not content or not content.strip():
            return result

        class_names = class_names or []

        for match in self.FUNCTION_PATTERN.finditer(content):
            visibility = match.group(1) or 'public'
            modifier = match.group(2) or ''
            func_modifiers_str = match.group(3) or ''
            generics_str = match.group(4) or ''
            receiver = match.group(5)
            name = match.group(6)
            params_str = match.group(7) or ''
            return_type = match.group(8) or ''

            # Determine modifiers from the matched groups
            func_modifiers = func_modifiers_str.split() if func_modifiers_str else []

            is_suspend = 'suspend' in func_modifiers
            is_inline = 'inline' in func_modifiers
            is_infix = 'infix' in func_modifiers
            is_operator = 'operator' in func_modifiers
            is_tailrec = 'tailrec' in func_modifiers
            is_override = modifier == 'override'
            is_abstract = modifier == 'abstract'
            is_open = modifier == 'open'
            is_extension = receiver is not None

            # Parse parameters
            parameters = self._parse_params(params_str)

            # Generic params
            generic_params = [g.strip() for g in generics_str.split(',')] if generics_str else []

            # Determine class context
            class_name = self._find_enclosing_class(content, match.start(), class_names)

            line_number = content[:match.start()].count('\n') + 1

            result['functions'].append(KotlinFunctionInfo(
                name=name,
                return_type=return_type.strip(),
                parameters=parameters,
                annotations=self._extract_annotations_before(content, match.start()),
                receiver_type=receiver.strip() if receiver else None,
                is_suspend=is_suspend,
                is_inline=is_inline,
                is_infix=is_infix,
                is_operator=is_operator,
                is_tailrec=is_tailrec,
                is_override=is_override,
                is_abstract=is_abstract,
                is_open=is_open,
                is_private=visibility == 'private',
                is_internal=visibility == 'internal',
                is_extension=is_extension,
                generic_params=generic_params,
                class_name=class_name,
                file=file_path,
                line_number=line_number,
                is_exported=visibility in ('public', 'internal'),
            ))

        # Count lambdas
        result['lambda_count'] = len(self.LAMBDA_PATTERN.findall(content))

        return result

    def _parse_params(self, params_str: str) -> List[KotlinParameterInfo]:
        """Parse function parameters."""
        params = []
        if not params_str or not params_str.strip():
            return params

        for param in self._split_params(params_str):
            param = param.strip()
            if not param:
                continue

            # Check for vararg
            is_vararg = False
            if param.startswith('vararg '):
                is_vararg = True
                param = param[7:]

            # Extract annotations
            annotations = []
            while param.startswith('@'):
                ann_match = re.match(r'@(\w+)(?:\([^)]*\))?\s*', param)
                if ann_match:
                    annotations.append(ann_match.group(1))
                    param = param[ann_match.end():]
                else:
                    break

            # Split name: type = default
            default_value = None
            if '=' in param:
                param_part, default_part = param.split('=', 1)
                default_value = default_part.strip()
                param = param_part.strip()

            if ':' in param:
                name, type_str = param.split(':', 1)
                params.append(KotlinParameterInfo(
                    name=name.strip(),
                    type=type_str.strip(),
                    default_value=default_value,
                    is_vararg=is_vararg,
                    annotations=annotations,
                ))

        return params

    def _extract_annotations_before(self, content: str, pos: int) -> List[str]:
        """Extract annotations before a function declaration."""
        annotations = []
        before = content[max(0, pos - 500):pos]
        lines = before.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('@'):
                ann_match = re.match(r'@(\w+)', line)
                if ann_match:
                    annotations.insert(0, ann_match.group(1))
            elif not line:
                continue
            else:
                break
        return annotations

    def _find_enclosing_class(self, content: str, pos: int, class_names: List[str]) -> Optional[str]:
        """Find the enclosing class name for a function at the given position."""
        before = content[:pos]
        # Look for the most recent class/object declaration
        class_pattern = re.compile(
            r'(?:class|object|interface)\s+(\w+)',
        )
        last_class = None
        for match in class_pattern.finditer(before):
            # Check if we're still inside its body (rough heuristic)
            after_class = content[match.end():pos]
            opens = after_class.count('{')
            closes = after_class.count('}')
            if opens > closes:
                last_class = match.group(1)

        return last_class

    def _split_params(self, text: str) -> List[str]:
        """Split parameters respecting nested brackets."""
        parts = []
        depth = 0
        current = []
        for ch in text:
            if ch in ('<', '(', '['):
                depth += 1
                current.append(ch)
            elif ch in ('>', ')', ']'):
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append(''.join(current))
        return parts
