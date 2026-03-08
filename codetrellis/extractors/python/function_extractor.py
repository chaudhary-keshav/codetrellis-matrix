"""
PythonFunctionExtractor - Extracts function and class definitions from Python source code.

This extractor parses Python code and extracts:
- Function definitions (def, async def)
- Class definitions with methods
- Decorators
- Type annotations
- Docstrings
- Default parameters

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    type_annotation: Optional[str] = None
    default: Optional[str] = None
    is_args: bool = False  # *args
    is_kwargs: bool = False  # **kwargs
    is_keyword_only: bool = False
    is_positional_only: bool = False


@dataclass
class FunctionInfo:
    """Information about a Python function."""
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    docstring: Optional[str] = None
    line_number: int = 0


@dataclass
class ClassInfo:
    """Information about a Python class."""
    name: str
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    class_variables: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    line_number: int = 0


class PythonFunctionExtractor:
    """
    Extracts function and class definitions from Python source code.

    Handles:
    - Regular and async functions
    - Class definitions with inheritance
    - Instance methods, class methods, static methods
    - Properties
    - Type annotations
    - *args and **kwargs
    - Decorators
    - Docstrings
    """

    # Decorator pattern
    DECORATOR_PATTERN = re.compile(
        r'^(\s*)@(\w+(?:\.\w+)*(?:\([^)]*\))?)',
        re.MULTILINE
    )

    # Function definition pattern
    FUNCTION_PATTERN = re.compile(
        r'^(\s*)(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    # Class definition pattern
    CLASS_PATTERN = re.compile(
        r'^(\s*)class\s+(\w+)(?:\s*\(\s*([^)]*)\s*\))?\s*:',
        re.MULTILINE
    )

    # Docstring pattern
    DOCSTRING_PATTERN = re.compile(
        r'^\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        """Initialize the function extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all functions and classes from Python content.

        Args:
            content: Python source code

        Returns:
            Dict containing 'functions' and 'classes'
        """
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)

        return {
            'functions': functions,
            'classes': classes
        }

    def _extract_functions(self, content: str) -> List[FunctionInfo]:
        """Extract top-level function definitions."""
        functions = []
        lines = content.split('\n')

        # Find decorators before each function
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for decorators
            decorators = []
            while line.strip().startswith('@'):
                decorator_match = re.match(r'\s*@(\w+(?:\.\w+)*(?:\([^)]*\))?)', line)
                if decorator_match:
                    decorators.append(decorator_match.group(1))
                i += 1
                if i >= len(lines):
                    break
                line = lines[i]

            # Check for function definition
            func_match = re.match(
                r'^(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
                line
            )

            if func_match:
                is_async = func_match.group(1) is not None
                func_name = func_match.group(2)
                params_str = func_match.group(3)
                return_type = func_match.group(4)

                # Parse parameters
                parameters = self._parse_parameters(params_str)

                # Look for docstring
                docstring = None
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        docstring = self._extract_docstring_from_lines(lines, i + 1)

                # Determine function type from decorators
                is_staticmethod = any('staticmethod' in d for d in decorators)
                is_classmethod = any('classmethod' in d for d in decorators)
                is_property = any('property' in d for d in decorators)

                func = FunctionInfo(
                    name=func_name,
                    parameters=parameters,
                    return_type=return_type.strip() if return_type else None,
                    decorators=decorators,
                    is_async=is_async,
                    is_method=False,
                    is_classmethod=is_classmethod,
                    is_staticmethod=is_staticmethod,
                    is_property=is_property,
                    docstring=docstring,
                    line_number=i + 1
                )

                functions.append(func)

            i += 1

        return functions

    def _extract_classes(self, content: str) -> List[ClassInfo]:
        """Extract class definitions with methods."""
        classes = []

        for class_match in self.CLASS_PATTERN.finditer(content):
            indent = len(class_match.group(1))
            class_name = class_match.group(2)
            bases_str = class_match.group(3) or ""

            # Parse base classes
            bases = [b.strip() for b in bases_str.split(',') if b.strip()]

            # Find decorators before class
            decorators = self._find_decorators_before(content, class_match.start())

            # Extract class body
            class_body_start = class_match.end()
            class_body = self._extract_class_body(content, class_body_start, indent)

            # Extract methods from class body
            methods = self._extract_methods(class_body)

            # Extract class variables
            class_variables = self._extract_class_variables(class_body)

            # Look for docstring
            docstring = None
            remaining = content[class_match.end():]
            docstring_match = self.DOCSTRING_PATTERN.search(remaining[:500])
            if docstring_match:
                docstring = (docstring_match.group(1) or docstring_match.group(2)).strip()

            # Calculate line number
            line_number = content[:class_match.start()].count('\n') + 1

            cls = ClassInfo(
                name=class_name,
                bases=bases,
                decorators=decorators,
                methods=methods,
                class_variables=class_variables,
                docstring=docstring,
                line_number=line_number
            )

            classes.append(cls)

        return classes

    def _extract_methods(self, class_body: str) -> List[FunctionInfo]:
        """Extract methods from a class body."""
        methods = []
        lines = class_body.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for decorators
            decorators = []
            while line.strip().startswith('@'):
                decorator_match = re.match(r'\s*@(\w+(?:\.\w+)*(?:\([^)]*\))?)', line)
                if decorator_match:
                    decorators.append(decorator_match.group(1))
                i += 1
                if i >= len(lines):
                    break
                line = lines[i]

            # Check for method definition
            func_match = re.match(
                r'\s*(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
                line
            )

            if func_match:
                is_async = func_match.group(1) is not None
                func_name = func_match.group(2)
                params_str = func_match.group(3)
                return_type = func_match.group(4)

                # Parse parameters
                parameters = self._parse_parameters(params_str)

                # Look for docstring
                docstring = None
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        docstring = self._extract_docstring_from_lines(lines, i + 1)

                # Determine method type from decorators
                is_staticmethod = any('staticmethod' in d for d in decorators)
                is_classmethod = any('classmethod' in d for d in decorators)
                is_property = any('property' in d for d in decorators)

                method = FunctionInfo(
                    name=func_name,
                    parameters=parameters,
                    return_type=return_type.strip() if return_type else None,
                    decorators=decorators,
                    is_async=is_async,
                    is_method=True,
                    is_classmethod=is_classmethod,
                    is_staticmethod=is_staticmethod,
                    is_property=is_property,
                    docstring=docstring,
                    line_number=i + 1
                )

                methods.append(method)

            i += 1

        return methods

    def _parse_parameters(self, params_str: str) -> List[ParameterInfo]:
        """Parse function parameters."""
        parameters = []

        if not params_str.strip():
            return parameters

        # Handle multiline parameters by removing newlines
        params_str = re.sub(r'\s+', ' ', params_str)

        # Track keyword-only and positional-only markers
        saw_star = False
        saw_slash = False

        for part in self._split_params(params_str):
            part = part.strip()
            if not part:
                continue

            # Handle * and / markers
            if part == '*':
                saw_star = True
                continue
            if part == '/':
                saw_slash = True
                continue

            param = self._parse_single_parameter(part, saw_star, saw_slash)
            if param:
                parameters.append(param)

        return parameters

    def _parse_single_parameter(self, part: str, is_keyword_only: bool, is_positional_only: bool) -> Optional[ParameterInfo]:
        """Parse a single parameter string."""
        # Check for *args
        if part.startswith('*') and not part.startswith('**'):
            name = part[1:].split(':')[0].strip()
            type_annotation = None
            if ':' in part:
                type_annotation = part.split(':', 1)[1].strip()
                if '=' in type_annotation:
                    type_annotation = type_annotation.split('=')[0].strip()
            return ParameterInfo(
                name=name,
                type_annotation=type_annotation,
                is_args=True
            )

        # Check for **kwargs
        if part.startswith('**'):
            name = part[2:].split(':')[0].strip()
            type_annotation = None
            if ':' in part:
                type_annotation = part.split(':', 1)[1].strip()
                if '=' in type_annotation:
                    type_annotation = type_annotation.split('=')[0].strip()
            return ParameterInfo(
                name=name,
                type_annotation=type_annotation,
                is_kwargs=True
            )

        # Regular parameter
        name = part
        type_annotation = None
        default = None

        if ':' in part:
            name_part, rest = part.split(':', 1)
            name = name_part.strip()

            if '=' in rest:
                type_annotation, default = rest.rsplit('=', 1)
                type_annotation = type_annotation.strip()
                default = default.strip()
            else:
                type_annotation = rest.strip()
        elif '=' in part:
            name, default = part.split('=', 1)
            name = name.strip()
            default = default.strip()

        return ParameterInfo(
            name=name,
            type_annotation=type_annotation,
            default=default,
            is_keyword_only=is_keyword_only,
            is_positional_only=is_positional_only
        )

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameters handling nested brackets."""
        params = []
        current = ""
        depth = 0

        for char in params_str:
            if char in '([{':
                depth += 1
            elif char in ')]}':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current)
                current = ""
                continue
            current += char

        if current.strip():
            params.append(current)

        return params

    def _extract_class_body(self, content: str, start: int, base_indent: int) -> str:
        """Extract class body starting from position."""
        lines = content[start:].split('\n')
        body_lines = []
        indent = None

        for line in lines:
            if not line.strip():
                body_lines.append(line)
                continue

            current_spaces = len(line) - len(line.lstrip())

            # First non-empty line sets the indent
            if indent is None:
                if current_spaces > base_indent:
                    indent = current_spaces
                else:
                    break

            # Check if we've exited the class
            if line.strip() and current_spaces <= base_indent:
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _extract_class_variables(self, class_body: str) -> List[str]:
        """Extract class-level variable definitions."""
        variables = []

        # Pattern for class variable with type annotation
        var_pattern = re.compile(r'^\s+(\w+)\s*:\s*([^=]+)(?:\s*=\s*(.+))?$', re.MULTILINE)

        for match in var_pattern.finditer(class_body):
            name = match.group(1)
            type_annotation = match.group(2).strip()
            variables.append(f"{name}:{type_annotation}")

        return variables

    def _find_decorators_before(self, content: str, position: int) -> List[str]:
        """Find decorators immediately before a position."""
        decorators = []
        lines_before = content[:position].rstrip().split('\n')

        for i in range(len(lines_before) - 1, -1, -1):
            line = lines_before[i].strip()
            if line.startswith('@'):
                decorator_match = re.match(r'@(\w+(?:\.\w+)*(?:\([^)]*\))?)', line)
                if decorator_match:
                    decorators.insert(0, decorator_match.group(1))
            elif line:
                break

        return decorators

    def _extract_docstring_from_lines(self, lines: List[str], start_index: int) -> Optional[str]:
        """Extract docstring starting at given line index."""
        if start_index >= len(lines):
            return None

        first_line = lines[start_index].strip()
        quote = '"""' if '"""' in first_line else "'''"

        # Single line docstring
        if first_line.count(quote) >= 2:
            return first_line.strip(quote).strip()

        # Multi-line docstring
        docstring_lines = [first_line.replace(quote, '')]
        for i in range(start_index + 1, min(start_index + 50, len(lines))):
            line = lines[i]
            if quote in line:
                docstring_lines.append(line.replace(quote, ''))
                break
            docstring_lines.append(line)

        return '\n'.join(docstring_lines).strip()

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """
        Convert extracted data to CodeTrellis format.

        Args:
            result: Dict with 'functions' and 'classes'

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # Add functions
        functions = result.get('functions', [])
        if functions:
            lines.append("[FUNCTIONS]")
            for func in functions:
                func_str = self._format_function(func)
                lines.append(func_str)
            lines.append("")

        # Add classes
        classes = result.get('classes', [])
        if classes:
            lines.append("[CLASSES]")
            for cls in classes:
                cls_str = self._format_class(cls)
                lines.append(cls_str)
            lines.append("")

        return "\n".join(lines)

    def _format_function(self, func: FunctionInfo) -> str:
        """Format a function for CodeTrellis output."""
        parts = []

        # Decorators
        if func.decorators:
            dec_str = '@' + ','.join(func.decorators)
            parts.append(f"[{dec_str}]")

        # Async marker
        if func.is_async:
            parts.append("async")

        # Function name and parameters
        params = []
        for p in func.parameters:
            if p.name == 'self' or p.name == 'cls':
                continue
            param_str = p.name
            if p.type_annotation:
                param_str += f":{p.type_annotation}"
            if p.default:
                param_str += f"={p.default}"
            if p.is_args:
                param_str = f"*{param_str}"
            if p.is_kwargs:
                param_str = f"**{param_str}"
            params.append(param_str)

        func_str = f"{func.name}({','.join(params)})"
        parts.append(func_str)

        # Return type
        if func.return_type:
            parts.append(f"→{func.return_type}")

        return " ".join(parts)

    def _format_class(self, cls: ClassInfo) -> str:
        """Format a class for CodeTrellis output."""
        parts = []

        # Decorators
        if cls.decorators:
            dec_str = '@' + ','.join(cls.decorators)
            parts.append(f"[{dec_str}]")

        # Class name and bases
        if cls.bases:
            class_str = f"class {cls.name}({','.join(cls.bases)})"
        else:
            class_str = f"class {cls.name}"
        parts.append(class_str)

        # Methods
        method_strs = []
        for method in cls.methods:
            flags = []
            if method.is_classmethod:
                flags.append("@cm")
            if method.is_staticmethod:
                flags.append("@sm")
            if method.is_property:
                flags.append("@prop")
            if method.is_async:
                flags.append("async")

            flag_str = f"[{','.join(flags)}]" if flags else ""

            # Format parameters
            params = []
            for p in method.parameters:
                if p.name in ('self', 'cls'):
                    continue
                param_str = p.name
                if p.type_annotation:
                    param_str += f":{p.type_annotation}"
                params.append(param_str)

            return_str = f"→{method.return_type}" if method.return_type else ""
            method_strs.append(f"{flag_str}{method.name}({','.join(params)}){return_str}")

        if method_strs:
            parts.append(f"methods:[{';'.join(method_strs)}]")

        return "|".join(parts)


# Convenience function
def extract_functions_and_classes(content: str) -> Dict[str, Any]:
    """Extract functions and classes from Python content."""
    extractor = PythonFunctionExtractor()
    return extractor.extract(content)
