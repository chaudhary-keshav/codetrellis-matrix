"""
Bash/Shell Alias & Source Extractor for CodeTrellis

Extracts alias definitions, source/include directives, and shebang info
from Bash/Shell source files.

Supports:
- Alias definitions: alias name='command'
- Source/include: source file.sh, . file.sh
- Shebang detection: #!/bin/bash, #!/usr/bin/env bash
- Shell option detection: set -e, set -o pipefail, shopt -s
- Bash version features: BASH_VERSION, BASH_VERSINFO

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BashAliasInfo:
    """Information about a Bash alias."""
    name: str = ""
    command: str = ""
    line_number: int = 0
    is_global: bool = False        # defined in .bashrc/.profile


@dataclass
class BashSourceInfo:
    """Information about a sourced/included file."""
    file_path: str = ""
    line_number: int = 0
    syntax: str = "source"         # "source" or "dot"
    is_conditional: bool = False   # inside if [ -f ... ]


@dataclass
class BashShebangInfo:
    """Information about the script's shebang line."""
    interpreter: str = ""          # bash, sh, zsh, ksh, dash, fish, env
    path: str = ""                 # /bin/bash, /usr/bin/env bash
    flags: List[str] = field(default_factory=list)  # -e, -x, etc.
    shell_type: str = ""           # "bash", "sh", "zsh", "ksh", "dash", "fish"
    version_hint: str = ""         # e.g., "bash4+" from feature usage


class BashAliasExtractor:
    """
    Extracts alias definitions, source directives, and shebang info.
    """

    # Alias: alias name='command' or alias name="command"
    ALIAS_PATTERN = re.compile(
        r'^[ \t]*alias\s+([\w.-]+)=[\'"](.+?)[\'"]',
        re.MULTILINE
    )

    # Unalias
    UNALIAS_PATTERN = re.compile(
        r'^[ \t]*unalias\s+([\w.-]+)',
        re.MULTILINE
    )

    # Source: source file or . file
    SOURCE_PATTERN = re.compile(
        r'^[ \t]*(?:source|\.)[ \t]+([^\s;#]+)',
        re.MULTILINE
    )

    # Shebang
    SHEBANG_PATTERN = re.compile(
        r'^#!\s*(/\S+)(?:\s+(.+))?$'
    )

    # Shell options: set -e, set -o pipefail, set -euo pipefail
    SET_OPTION = re.compile(
        r'^[ \t]*set\s+([+-][a-zA-Z]+(?:\s+[+-][a-zA-Z]+)*|[+-]o\s+\w+)',
        re.MULTILINE
    )

    # shopt: shopt -s extglob, shopt -s nullglob
    SHOPT_PATTERN = re.compile(
        r'^[ \t]*shopt\s+(-[su])\s+(\w+)',
        re.MULTILINE
    )

    # Bash version check patterns
    BASH_VERSION_CHECK = re.compile(
        r'BASH_VERSINFO\[0\]|BASH_VERSION'
    )

    # Common shells
    SHELL_MAP = {
        'bash': 'bash',
        'sh': 'sh',
        'zsh': 'zsh',
        'ksh': 'ksh',
        'ksh93': 'ksh',
        'dash': 'dash',
        'ash': 'ash',
        'fish': 'fish',
        'tcsh': 'tcsh',
        'csh': 'csh',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract aliases, sources, and shebang info.

        Args:
            content: Shell script content
            file_path: Path to source file

        Returns:
            Dict with 'aliases', 'sources', 'shebang', 'shell_options', 'shopt_options' keys
        """
        aliases = []
        sources = []
        shebang = None
        shell_options = []
        shopt_options = []

        # Extract shebang (first line only)
        first_line = content.split('\n')[0] if content else ""
        shebang_match = self.SHEBANG_PATTERN.match(first_line)
        if shebang_match:
            path = shebang_match.group(1)
            args = shebang_match.group(2) or ""

            # Determine shell type
            interpreter = path.split('/')[-1]
            flags = []

            if interpreter == 'env':
                # #!/usr/bin/env bash -e
                parts = args.split()
                if parts:
                    interpreter = parts[0]
                    flags = parts[1:] if len(parts) > 1 else []
            else:
                flags = args.split() if args else []

            shell_type = self.SHELL_MAP.get(interpreter, interpreter)

            shebang = BashShebangInfo(
                interpreter=interpreter,
                path=path + (' ' + args if args else ''),
                flags=flags,
                shell_type=shell_type,
            )

            # Detect bash version hints from features used
            if shell_type == 'bash':
                shebang.version_hint = self._detect_bash_version(content)

        # Extract aliases
        for match in self.ALIAS_PATTERN.finditer(content):
            name = match.group(1)
            command = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            aliases.append(BashAliasInfo(
                name=name,
                command=command,
                line_number=line_num,
            ))

        # Extract source/include
        for match in self.SOURCE_PATTERN.finditer(content):
            sourced_file = match.group(1).strip('"').strip("'")
            line_num = content[:match.start()].count('\n') + 1

            syntax = "dot" if content[match.start():].lstrip().startswith('.') else "source"

            # Check if conditional (within if block checking file existence)
            is_conditional = self._is_conditional_source(content, match.start())

            sources.append(BashSourceInfo(
                file_path=sourced_file,
                line_number=line_num,
                syntax=syntax,
                is_conditional=is_conditional,
            ))

        # Extract set options
        for match in self.SET_OPTION.finditer(content):
            option = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            shell_options.append({
                'option': option,
                'line': line_num,
            })

        # Extract shopt options
        for match in self.SHOPT_PATTERN.finditer(content):
            flag = match.group(1)
            option = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            shopt_options.append({
                'flag': flag,
                'option': option,
                'line': line_num,
                'enabled': flag == '-s',
            })

        return {
            'aliases': aliases,
            'sources': sources,
            'shebang': shebang,
            'shell_options': shell_options,
            'shopt_options': shopt_options,
        }

    def _is_conditional_source(self, content: str, pos: int) -> bool:
        """Check if a source statement is inside a conditional block."""
        # Look backwards for if [ -f or if [[ -f
        preceding = content[max(0, pos - 200):pos]
        return bool(re.search(r'if\s+\[{1,2}\s+-[ferd]\s+', preceding))

    def _detect_bash_version(self, content: str) -> str:
        """Detect minimum Bash version from feature usage."""
        features = {
            '4.0+': [
                r'\bmapfile\b', r'\breadarray\b', r'&>>',
                r'declare\s+-A',  # associative arrays
            ],
            '4.2+': [
                r'\bprintf\s+-v\b',
                r'declare\s+-g',  # global scope in function
            ],
            '4.3+': [
                r'declare\s+-n',  # namerefs
            ],
            '4.4+': [
                r'\$\{!',  # indirect expansion improvements
            ],
            '5.0+': [
                r'EPOCHSECONDS', r'EPOCHREALTIME',
                r'\$\{[^}]*@[aEPK]\}',  # parameter transformation
            ],
            '5.1+': [
                r'BASH_ARGV0',
                r'\$\{[^}]*@L\}',  # lowercase transformation
            ],
            '5.2+': [
                r'READLINE_MARK',
            ],
        }

        detected_version = ""
        for version, patterns in features.items():
            for pat in patterns:
                if re.search(pat, content):
                    detected_version = version
                    # Don't break - keep looking for higher versions

        return detected_version
