"""
GoFunctionExtractor - Extracts Go function and method definitions.

This extractor parses Go source code and extracts:
- Top-level function definitions
- Methods with receivers (value and pointer)
- Parameters and return types
- Exported vs unexported detection
- init() and main() functions

Part of CodeTrellis v4.5 - Go Language Support (G-17)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GoParameterInfo:
    """Information about a Go function parameter."""
    name: str
    type: str
    is_variadic: bool = False


@dataclass
class GoFunctionInfo:
    """Information about a Go function."""
    name: str
    parameters: List[GoParameterInfo] = field(default_factory=list)
    return_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = False
    is_init: bool = False
    is_main: bool = False
    comment: Optional[str] = None


@dataclass
class GoMethodInfo:
    """Information about a Go method (function with receiver)."""
    name: str
    receiver_name: str = ""
    receiver_type: str = ""
    is_pointer_receiver: bool = False
    parameters: List[GoParameterInfo] = field(default_factory=list)
    return_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = False
    comment: Optional[str] = None


class GoFunctionExtractor:
    """
    Extracts Go function and method definitions from source code.

    Handles:
    - Top-level func declarations
    - Methods with value and pointer receivers
    - Multiple return values
    - Named return values
    - Variadic parameters
    - init() and main() special functions
    - Comment extraction
    """

    # Function pattern: func Name(params) (returns) {
    FUNC_PATTERN = re.compile(
        r'(?:(//.+)\n\s*)?^func\s+(\w+)\s*\(([^)]*)\)\s*(\([^)]*\)|[\w\[\]\*\.]+)?\s*\{',
        re.MULTILINE
    )

    # Method pattern: func (r *ReceiverType) Name(params) (returns) {
    METHOD_PATTERN = re.compile(
        r'(?:(//.+)\n\s*)?^func\s+\((\w+)\s+(\*?\w+(?:\.\w+)?)\)\s+(\w+)\s*\(([^)]*)\)\s*(\([^)]*\)|[\w\[\]\*\.]+)?\s*\{',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Go function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Go functions and methods from source code.

        Args:
            content: Go source code content
            file_path: Path to source file

        Returns:
            Dict with 'functions' and 'methods' keys
        """
        return {
            'functions': self._extract_functions(content, file_path),
            'methods': self._extract_methods(content, file_path),
        }

    def _parse_params(self, params_str: str) -> List[GoParameterInfo]:
        """Parse a Go parameter list string into GoParameterInfo objects."""
        if not params_str or not params_str.strip():
            return []

        params = []
        # Split by comma, but handle complex types with commas inside brackets
        parts = self._smart_split(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            is_variadic = '...' in part
            part = part.replace('...', '')

            tokens = part.split()
            if len(tokens) >= 2:
                # name type pattern
                name = tokens[0]
                param_type = ' '.join(tokens[1:])
                params.append(GoParameterInfo(
                    name=name,
                    type=param_type.strip(),
                    is_variadic=is_variadic,
                ))
            elif len(tokens) == 1:
                # Just a type (unnamed), or continuation of previous
                params.append(GoParameterInfo(
                    name="",
                    type=tokens[0].strip(),
                    is_variadic=is_variadic,
                ))

        return params

    def _parse_returns(self, returns_str: Optional[str]) -> List[str]:
        """Parse return type string into a list of return types."""
        if not returns_str or not returns_str.strip():
            return []

        returns_str = returns_str.strip()

        # Remove outer parens if present
        if returns_str.startswith('(') and returns_str.endswith(')'):
            returns_str = returns_str[1:-1]

        # Split by comma
        parts = self._smart_split(returns_str)
        result = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Remove named return variable (e.g., "err error" -> "error")
            tokens = part.split()
            if len(tokens) >= 2 and not tokens[0].startswith('*') and not tokens[0].startswith('['):
                result.append(tokens[-1])
            else:
                result.append(part)

        return result

    def _smart_split(self, s: str) -> List[str]:
        """Split by comma, respecting brackets and parentheses."""
        parts = []
        depth = 0
        current = []
        for ch in s:
            if ch in ('(', '[', '{'):
                depth += 1
                current.append(ch)
            elif ch in (')', ']', '}'):
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

    def _extract_functions(self, content: str, file_path: str) -> List[GoFunctionInfo]:
        """Extract top-level function definitions (not methods)."""
        results = []

        # First find methods to exclude them from function matches
        method_positions = set()
        for m in self.METHOD_PATTERN.finditer(content):
            method_positions.add(m.start())

        for match in self.FUNC_PATTERN.finditer(content):
            if match.start() in method_positions:
                continue

            comment = match.group(1)
            name = match.group(2)
            params_str = match.group(3)
            returns_str = match.group(4)
            line_number = content[:match.start()].count('\n') + 1

            info = GoFunctionInfo(
                name=name,
                parameters=self._parse_params(params_str),
                return_types=self._parse_returns(returns_str),
                file=file_path,
                line_number=line_number,
                is_exported=name[0].isupper() if name else False,
                is_init=name == 'init',
                is_main=name == 'main',
                comment=comment.strip().lstrip('/ ') if comment else None,
            )
            results.append(info)

        return results

    def _extract_methods(self, content: str, file_path: str) -> List[GoMethodInfo]:
        """Extract method definitions (functions with receivers)."""
        results = []

        for match in self.METHOD_PATTERN.finditer(content):
            comment = match.group(1)
            receiver_name = match.group(2)
            receiver_type = match.group(3)
            name = match.group(4)
            params_str = match.group(5)
            returns_str = match.group(6)
            line_number = content[:match.start()].count('\n') + 1

            is_pointer = receiver_type.startswith('*')
            clean_receiver = receiver_type.lstrip('*')

            info = GoMethodInfo(
                name=name,
                receiver_name=receiver_name,
                receiver_type=clean_receiver,
                is_pointer_receiver=is_pointer,
                parameters=self._parse_params(params_str),
                return_types=self._parse_returns(returns_str),
                file=file_path,
                line_number=line_number,
                is_exported=name[0].isupper() if name else False,
                comment=comment.strip().lstrip('/ ') if comment else None,
            )
            results.append(info)

        return results
