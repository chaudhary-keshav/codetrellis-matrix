"""
Bash/Shell Command Extractor for CodeTrellis

Extracts command-level constructs from Bash/Shell source files.

Supports:
- Pipelines: cmd1 | cmd2 | cmd3
- Subshells: $(...) and `...`
- Process substitution: <(cmd), >(cmd)
- Here documents: <<EOF ... EOF, <<-EOF, <<<
- Redirections: >, >>, 2>&1, &>, /dev/null
- Traps: trap 'handler' SIGNAL
- Background jobs: cmd &
- Coprocesses: coproc NAME { ... }
- Conditional execution: cmd1 && cmd2, cmd1 || cmd2
- Command substitution nesting

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BashPipelineInfo:
    """Information about a pipeline."""
    commands: List[str] = field(default_factory=list)
    line_number: int = 0
    pipe_count: int = 0
    has_error_pipe: bool = False    # |&  (pipefail)
    is_backgrounded: bool = False   # ends with &


@dataclass
class BashTrapInfo:
    """Information about a signal trap."""
    signal: str = ""               # EXIT, INT, TERM, ERR, DEBUG, RETURN
    handler: str = ""              # Handler command/function
    line_number: int = 0
    is_cleanup: bool = False       # Trap handler performs cleanup


@dataclass
class BashSubshellInfo:
    """Information about a subshell usage."""
    command: str = ""
    line_number: int = 0
    syntax: str = "dollar_paren"   # "dollar_paren" $(), "backtick" ``, "paren_group" ()
    is_nested: bool = False


@dataclass
class BashHereDocInfo:
    """Information about a here document."""
    delimiter: str = ""
    line_number: int = 0
    is_indented: bool = False      # <<- allows tab indentation
    is_heredoc: bool = True        # True = heredoc, False = herestring
    target_command: str = ""       # command receiving the heredoc


@dataclass
class BashRedirectInfo:
    """Information about a redirection."""
    fd_from: str = ""              # 1, 2, &
    operator: str = ""             # >, >>, 2>, 2>&1, &>
    target: str = ""               # file, /dev/null, &1
    line_number: int = 0


class BashCommandExtractor:
    """
    Extracts command-level patterns from Bash/Shell scripts.
    """

    # Pipeline pattern (multi-command pipes)
    PIPELINE_PATTERN = re.compile(
        r'^[ \t]*(.+?\|.+?)(?:\s*(?:#.*)?)?$',
        re.MULTILINE
    )

    # Trap: trap 'handler' SIGNAL [SIGNAL...]
    TRAP_PATTERN = re.compile(
        r'''trap\s+(?:'([^']*)'|"([^"]*)"|(\w+))\s+([\w\s]+)''',
        re.MULTILINE
    )

    # Here document: <<[-]DELIM
    HEREDOC_PATTERN = re.compile(
        r'^[ \t]*(\w+).*?<<(-?)[ \t]*[\'\"]?(\w+)[\'\"]?',
        re.MULTILINE
    )

    # Here string: <<<
    HERESTRING_PATTERN = re.compile(
        r'<<<\s*(.+)$',
        re.MULTILINE
    )

    # Subshell: $(command) — non-greedy
    DOLLAR_SUBSHELL = re.compile(r'\$\(([^)]+)\)')

    # Backtick subshell: `command`
    BACKTICK_SUBSHELL = re.compile(r'`([^`]+)`')

    # Process substitution: <(cmd) or >(cmd)
    PROCESS_SUB = re.compile(r'[<>]\(([^)]+)\)')

    # Redirection patterns
    REDIRECT_PATTERN = re.compile(
        r'(\d*)?(>>|>&|&>>|&>|2>&1|2>|>)\s*([^\s;|&]+)'
    )

    # Background: cmd &
    BACKGROUND_PATTERN = re.compile(
        r'^[ \t]*(.+?)\s*&\s*(?:#.*)?$',
        re.MULTILINE
    )

    # Coproc: coproc NAME { ... } or coproc cmd
    COPROC_PATTERN = re.compile(
        r'^[ \t]*coproc\s+(\w+)',
        re.MULTILINE
    )

    # Wait: wait $PID or wait
    WAIT_PATTERN = re.compile(
        r'^[ \t]*wait\b(.*)$',
        re.MULTILINE
    )

    # Cleanup signals
    CLEANUP_SIGNALS = {'EXIT', 'TERM', 'INT', 'QUIT', 'HUP'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract command-level constructs from Bash/Shell source.

        Args:
            content: Shell script content
            file_path: Path to source file

        Returns:
            Dict with pipelines, traps, subshells, heredocs, redirects
        """
        pipelines = []
        traps = []
        subshells = []
        heredocs = []
        redirects = []

        # Extract pipelines
        for match in self.PIPELINE_PATTERN.finditer(content):
            line = match.group(1).strip()
            # Skip comments and empty pipes
            if line.startswith('#'):
                continue
            pipe_parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(pipe_parts) >= 2:
                line_num = content[:match.start()].count('\n') + 1
                pipelines.append(BashPipelineInfo(
                    commands=pipe_parts,
                    line_number=line_num,
                    pipe_count=len(pipe_parts) - 1,
                    has_error_pipe='|&' in line,
                    is_backgrounded=line.rstrip().endswith('&'),
                ))

        # Extract traps
        for match in self.TRAP_PATTERN.finditer(content):
            handler = match.group(1) or match.group(2) or match.group(3) or ""
            signals_str = match.group(4).strip()
            line_num = content[:match.start()].count('\n') + 1

            for sig in signals_str.split():
                sig_upper = sig.upper().lstrip('SIG')
                traps.append(BashTrapInfo(
                    signal=sig_upper,
                    handler=handler,
                    line_number=line_num,
                    is_cleanup=sig_upper in self.CLEANUP_SIGNALS,
                ))

        # Extract subshells
        for match in self.DOLLAR_SUBSHELL.finditer(content):
            cmd = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            subshells.append(BashSubshellInfo(
                command=cmd[:100],
                line_number=line_num,
                syntax="dollar_paren",
                is_nested='$(' in cmd,
            ))

        for match in self.BACKTICK_SUBSHELL.finditer(content):
            cmd = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            subshells.append(BashSubshellInfo(
                command=cmd[:100],
                line_number=line_num,
                syntax="backtick",
            ))

        # Extract here documents
        for match in self.HEREDOC_PATTERN.finditer(content):
            target_cmd = match.group(1)
            is_indented = bool(match.group(2))
            delimiter = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            heredocs.append(BashHereDocInfo(
                delimiter=delimiter,
                line_number=line_num,
                is_indented=is_indented,
                target_command=target_cmd,
            ))

        # Extract here strings
        for match in self.HERESTRING_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            heredocs.append(BashHereDocInfo(
                delimiter="<<<",
                line_number=line_num,
                is_heredoc=False,
                target_command=match.group(1).strip()[:50],
            ))

        # Extract redirections
        for match in self.REDIRECT_PATTERN.finditer(content):
            fd = match.group(1) or ""
            op = match.group(2)
            target = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            redirects.append(BashRedirectInfo(
                fd_from=fd,
                operator=op,
                target=target,
                line_number=line_num,
            ))

        return {
            'pipelines': pipelines,
            'traps': traps,
            'subshells': subshells,
            'heredocs': heredocs,
            'redirects': redirects,
        }
