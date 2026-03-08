"""
Bash/Shell Variable Extractor for CodeTrellis

Extracts variable definitions from Bash/Shell source files.

Supports:
- Simple variable assignments: VAR=value
- Export declarations: export VAR=value
- Readonly variables: readonly VAR=value
- Indexed arrays: arr=(val1 val2 val3)
- Associative arrays: declare -A map=([key]=val)
- Declare/typeset with flags: declare -i, -r, -x, -a, -A
- Environment variable references: $VAR, ${VAR}, ${VAR:-default}
- Parameter expansion: ${VAR:=default}, ${VAR:+alt}, ${VAR:?error}
- Here-string variable capture
- Read command variable assignments

Bash versions: sh, bash (2.x-5.x), zsh, ksh, dash

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BashVariableInfo:
    """Information about a Bash variable."""
    name: str = ""
    value: str = ""
    line_number: int = 0
    is_readonly: bool = False
    is_integer: bool = False
    is_local: bool = False
    is_exported: bool = False
    scope: str = "global"          # "global", "local", "function"
    var_type: str = "string"       # "string", "integer", "array", "assoc_array", "nameref"
    has_default: bool = False
    default_value: str = ""
    source: str = ""               # "assignment", "export", "declare", "read", "env"


@dataclass
class BashArrayInfo:
    """Information about a Bash array."""
    name: str = ""
    line_number: int = 0
    array_type: str = "indexed"    # "indexed", "associative"
    elements: List[str] = field(default_factory=list)
    is_readonly: bool = False
    is_exported: bool = False


@dataclass
class BashExportInfo:
    """Information about an exported variable."""
    name: str = ""
    value: str = ""
    line_number: int = 0
    source_file: str = ""


class BashVariableExtractor:
    """
    Extracts variable definitions from Bash/Shell scripts.

    Handles all major variable declaration styles.
    """

    # Simple assignment: VAR=value (not inside if/for/etc.)
    SIMPLE_ASSIGN = re.compile(
        r'^[ \t]*([A-Za-z_]\w*)=(.*)$',
        re.MULTILINE
    )

    # Export: export VAR=value or export VAR
    EXPORT_PATTERN = re.compile(
        r'^[ \t]*export\s+([A-Za-z_]\w*)(?:=(.*))?$',
        re.MULTILINE
    )

    # Readonly: readonly VAR=value or readonly VAR
    READONLY_PATTERN = re.compile(
        r'^[ \t]*readonly\s+([A-Za-z_]\w*)(?:=(.*))?$',
        re.MULTILINE
    )

    # Declare/typeset: declare [-flags] VAR[=value]
    DECLARE_PATTERN = re.compile(
        r'^[ \t]*(?:declare|typeset)\s+(-[a-zA-Z]+)?\s*([A-Za-z_]\w*)(?:=(.*))?$',
        re.MULTILINE
    )

    # Array assignment: arr=(val1 val2 val3)
    ARRAY_ASSIGN = re.compile(
        r'^[ \t]*([A-Za-z_]\w*)=\(\s*([^)]*)\)',
        re.MULTILINE
    )

    # Associative array: declare -A map=([key]=val ...)
    ASSOC_ARRAY = re.compile(
        r'^[ \t]*declare\s+-A\s+([A-Za-z_]\w*)(?:=\(\s*([^)]*)\))?',
        re.MULTILINE
    )

    # Read command: read [-flags] VAR1 VAR2 ...
    READ_PATTERN = re.compile(
        r'^[ \t]*read\s+(?:-[a-zA-Z]+\s+)*(.+)$',
        re.MULTILINE
    )

    # Local variable: local VAR=value
    LOCAL_PATTERN = re.compile(
        r'^[ \t]*local\s+([A-Za-z_]\w*)(?:=(.*))?$',
        re.MULTILINE
    )

    # Parameter expansion with default: ${VAR:-default} or ${VAR:=default}
    PARAM_EXPANSION = re.compile(
        r'\$\{([A-Za-z_]\w*)(?::-|:=|:\+|:\?)([^}]*)\}'
    )

    # Environment variable reference: $VAR or ${VAR}
    ENV_REF = re.compile(r'\$\{?([A-Za-z_]\w*)\}?')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all variable definitions from Bash/Shell source.

        Args:
            content: Shell script content
            file_path: Path to source file

        Returns:
            Dict with 'variables', 'arrays', 'exports' keys
        """
        variables = []
        arrays = []
        exports = []
        seen_names = set()

        # Extract associative arrays first (higher priority than simple assigns)
        for match in self.ASSOC_ARRAY.finditer(content):
            name = match.group(1)
            elements_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            elements = []
            if elements_str:
                # Parse [key]=value pairs
                for pair in re.finditer(r'\[([^\]]+)\]=(\S+)', elements_str):
                    elements.append(f"{pair.group(1)}={pair.group(2)}")

            arrays.append(BashArrayInfo(
                name=name,
                line_number=line_num,
                array_type="associative",
                elements=elements,
            ))
            seen_names.add(name)

        # Extract indexed arrays
        for match in self.ARRAY_ASSIGN.finditer(content):
            name = match.group(1)
            if name in seen_names:
                continue
            elements_str = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            elements = [e.strip().strip('"').strip("'") for e in elements_str.split() if e.strip()]

            arrays.append(BashArrayInfo(
                name=name,
                line_number=line_num,
                array_type="indexed",
                elements=elements,
            ))
            seen_names.add(name)

        # Extract declare/typeset variables
        for match in self.DECLARE_PATTERN.finditer(content):
            flags = match.group(1) or ""
            name = match.group(2)
            value = match.group(3) or ""
            if name in seen_names:
                continue
            line_num = content[:match.start()].count('\n') + 1

            var_type = "string"
            is_readonly = '-r' in flags
            is_exported = '-x' in flags
            is_integer = '-i' in flags
            if '-a' in flags:
                var_type = "array"
            elif '-A' in flags:
                var_type = "assoc_array"
            elif '-n' in flags:
                var_type = "nameref"
            elif is_integer:
                var_type = "integer"

            variables.append(BashVariableInfo(
                name=name,
                value=value.strip(),
                line_number=line_num,
                is_readonly=is_readonly,
                is_exported=is_exported,
                is_integer=is_integer,
                var_type=var_type,
                source="declare",
            ))
            seen_names.add(name)

        # Extract exports
        for match in self.EXPORT_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            exports.append(BashExportInfo(
                name=name,
                value=value.strip(),
                line_number=line_num,
                source_file=file_path,
            ))

            if name not in seen_names:
                variables.append(BashVariableInfo(
                    name=name,
                    value=value.strip(),
                    line_number=line_num,
                    is_exported=True,
                    source="export",
                ))
                seen_names.add(name)

        # Extract readonly variables
        for match in self.READONLY_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2) or ""
            if name in seen_names:
                continue
            line_num = content[:match.start()].count('\n') + 1

            variables.append(BashVariableInfo(
                name=name,
                value=value.strip(),
                line_number=line_num,
                is_readonly=True,
                source="assignment",
            ))
            seen_names.add(name)

        # Extract local variables
        for match in self.LOCAL_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2) or ""
            if name in seen_names:
                continue
            line_num = content[:match.start()].count('\n') + 1

            variables.append(BashVariableInfo(
                name=name,
                value=value.strip(),
                line_number=line_num,
                is_local=True,
                scope="local",
                source="assignment",
            ))
            seen_names.add(name)

        # Extract simple assignments (excluding already found)
        for match in self.SIMPLE_ASSIGN.finditer(content):
            name = match.group(1)
            value = match.group(2)
            if name in seen_names:
                continue
            # Filter out common non-variable patterns
            if name in ('if', 'then', 'else', 'fi', 'for', 'while', 'do', 'done',
                        'case', 'esac', 'function', 'select', 'until', 'in'):
                continue
            line_num = content[:match.start()].count('\n') + 1

            variables.append(BashVariableInfo(
                name=name,
                value=value.strip(),
                line_number=line_num,
                source="assignment",
            ))
            seen_names.add(name)

        # Extract read variables
        for match in self.READ_PATTERN.finditer(content):
            var_list = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            for var_name in var_list.split():
                var_name = var_name.strip()
                if var_name.startswith('-'):
                    continue
                if var_name and var_name not in seen_names:
                    variables.append(BashVariableInfo(
                        name=var_name,
                        line_number=line_num,
                        source="read",
                    ))
                    seen_names.add(var_name)

        return {
            'variables': variables,
            'arrays': arrays,
            'exports': exports,
        }
