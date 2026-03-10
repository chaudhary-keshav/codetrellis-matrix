"""
EnhancedCobraParser v1.0 - Comprehensive Cobra CLI framework parser.

Supports:
- Cobra v1.x (spf13/cobra)
- Viper integration (spf13/viper)

Cobra-specific extraction:
- Command definitions (cobra.Command{})
- Sub-command registration (AddCommand)
- Flag definitions (StringVar, BoolVar, IntVar, PersistentFlags, Flags)
- Flag types (String, Bool, Int, Float64, StringSlice, StringArray, Duration, Count, IP, etc.)
- Run/RunE handlers
- PreRun/PostRun/PersistentPreRun/PersistentPostRun
- Completion (ValidArgsFunction, RegisterFlagCompletionFunc)
- Command groups (AddGroup)
- Root command detection
- Viper binding (viper.BindPFlag, viper.BindPFlags)

Part of CodeTrellis v5.2.0 - Go Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CobraCommandInfo:
    """Cobra CLI command."""
    name: str
    use: str = ""
    short: str = ""
    long: str = ""
    variable_name: str = ""
    has_run: bool = False
    has_run_e: bool = False
    has_pre_run: bool = False
    has_post_run: bool = False
    has_persistent_pre_run: bool = False
    has_persistent_post_run: bool = False
    has_valid_args: bool = False
    is_root: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CobraFlagInfo:
    """Cobra flag definition."""
    name: str
    flag_type: str = ""  # String, Bool, Int, Float64, Duration, StringSlice, etc.
    short_hand: str = ""
    default_value: str = ""
    description: str = ""
    is_persistent: bool = False
    is_required: bool = False
    command: str = ""  # Which command this flag belongs to
    file: str = ""
    line_number: int = 0


@dataclass
class CobraSubCommandInfo:
    """Cobra sub-command registration."""
    parent: str
    child: str
    file: str = ""
    line_number: int = 0


@dataclass
class CobraGroupInfo:
    """Cobra command group."""
    id: str
    title: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class CobraViperBindInfo:
    """Cobra-Viper flag binding."""
    flag_name: str
    config_key: str = ""
    bind_type: str = ""  # BindPFlag, BindPFlags, BindEnv
    file: str = ""
    line_number: int = 0


@dataclass
class CobraParseResult:
    file_path: str
    file_type: str = "go"

    commands: List[CobraCommandInfo] = field(default_factory=list)
    flags: List[CobraFlagInfo] = field(default_factory=list)
    sub_commands: List[CobraSubCommandInfo] = field(default_factory=list)
    groups: List[CobraGroupInfo] = field(default_factory=list)
    viper_bindings: List[CobraViperBindInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    has_viper: bool = False
    has_completion: bool = False
    total_commands: int = 0
    total_flags: int = 0


class EnhancedCobraParser:
    """Enhanced Cobra parser for comprehensive CLI extraction."""

    COBRA_IMPORT = re.compile(r'"github\.com/spf13/cobra"')
    VIPER_IMPORT = re.compile(r'"github\.com/spf13/viper"')

    # Command definition: &cobra.Command{ Use: "name", ... }
    COMMAND_PATTERN = re.compile(
        r'(\w+)\s*(?::?=|=)\s*&cobra\.Command\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL,
    )

    # Command fields
    USE_PATTERN = re.compile(r'Use:\s*"([^"]+)"')
    SHORT_PATTERN = re.compile(r'Short:\s*"([^"]*)"')
    LONG_PATTERN = re.compile(r'Long:\s*(?:`([^`]*)`|"([^"]*)")')
    RUN_PATTERN = re.compile(r'\bRun\s*:')
    RUN_E_PATTERN = re.compile(r'\bRunE\s*:')
    PRE_RUN_PATTERN = re.compile(r'\bPreRun(?:E)?\s*:')
    POST_RUN_PATTERN = re.compile(r'\bPostRun(?:E)?\s*:')
    PERSISTENT_PRE_RUN_PATTERN = re.compile(r'\bPersistentPreRun(?:E)?\s*:')
    PERSISTENT_POST_RUN_PATTERN = re.compile(r'\bPersistentPostRun(?:E)?\s*:')
    VALID_ARGS_PATTERN = re.compile(r'\bValidArgs(?:Function)?\s*:')

    # AddCommand: rootCmd.AddCommand(subCmd, sub2Cmd)
    ADD_COMMAND_PATTERN = re.compile(
        r'(\w+)\.AddCommand\s*\(\s*([^)]+)\)',
    )

    # AddGroup: rootCmd.AddGroup(&cobra.Group{ID: "id", Title: "title"})
    ADD_GROUP_PATTERN = re.compile(
        r'\.AddGroup\s*\(\s*&cobra\.Group\s*\{\s*ID:\s*"([^"]+)"\s*,\s*Title:\s*"([^"]+)"',
    )

    # Persistent flags: cmd.PersistentFlags().StringVarP(&var, "name", "n", "default", "description")
    # Also handles non-Var: cmd.PersistentFlags().String("name", "default", "description")
    PERSISTENT_FLAG_PATTERN = re.compile(
        r'(\w+)\.PersistentFlags\(\)\.(String|Bool|Int|Float64|Duration|StringSlice|'
        r'StringArray|IntSlice|Float64Slice|Count|IP|IPSlice|IPNet|BytesHex|BytesBase64)(?:Var)?(?:P)?\s*\('
        r'\s*(?:&\w+\s*,\s*)?"([^"]*)"(?:\s*,\s*"([^"]*)")?(?:\s*,\s*(?:"([^"]*)"|[^,)]+))?(?:\s*,\s*"([^"]*)")?',
    )

    # Local flags: cmd.Flags().StringVarP(...)
    # Also handles non-Var: cmd.Flags().String("name", "default", "description")
    LOCAL_FLAG_PATTERN = re.compile(
        r'(\w+)\.Flags\(\)\.(String|Bool|Int|Float64|Duration|StringSlice|'
        r'StringArray|IntSlice|Float64Slice|Count|IP|IPSlice|IPNet|BytesHex|BytesBase64)(?:Var)?(?:P)?\s*\('
        r'\s*(?:&\w+\s*,\s*)?"([^"]*)"(?:\s*,\s*"([^"]*)")?(?:\s*,\s*(?:"([^"]*)"|[^,)]+))?(?:\s*,\s*"([^"]*)")?',
    )

    # Mark required: cmd.MarkFlagRequired("name")
    REQUIRED_FLAG_PATTERN = re.compile(
        r'\.MarkFlagRequired\s*\(\s*"([^"]+)"',
    )
    REQUIRED_PERSISTENT_PATTERN = re.compile(
        r'\.MarkPersistentFlagRequired\s*\(\s*"([^"]+)"',
    )

    # Viper binding: viper.BindPFlag("key", cmd.Flags().Lookup("flag"))
    VIPER_BIND_PFLAG = re.compile(
        r'viper\.BindPFlag\s*\(\s*"([^"]+)"\s*,\s*\w+\.(?:Persistent)?Flags\(\)\.Lookup\s*\(\s*"([^"]+)"\s*\)',
    )
    VIPER_BIND_PFLAGS = re.compile(r'viper\.BindPFlags\s*\(')
    VIPER_BIND_ENV = re.compile(r'viper\.BindEnv\s*\(\s*"([^"]+)"')

    # Completion
    COMPLETION_PATTERN = re.compile(
        r'\.RegisterFlagCompletionFunc\s*\(\s*"([^"]+)"',
    )
    VALID_ARGS_FUNC = re.compile(
        r'ValidArgsFunction\s*:\s*func\s*\(',
    )

    # Root command detection
    ROOT_CMD_PATTERN = re.compile(
        r'rootCmd|RootCmd|root[Cc]ommand',
    )

    FRAMEWORK_PATTERNS = {
        'cobra': re.compile(r'"github\.com/spf13/cobra"'),
        'viper': re.compile(r'"github\.com/spf13/viper"'),
        'pflag': re.compile(r'"github\.com/spf13/pflag"'),
        'cobra-cli': re.compile(r'"github\.com/spf13/cobra-cli"'),
        'survey': re.compile(r'"github\.com/AlecAivazis/survey"'),
        'promptui': re.compile(r'"github\.com/manifoldco/promptui"'),
        'color': re.compile(r'"github\.com/fatih/color"'),
        'tablewriter': re.compile(r'"github\.com/olekukonko/tablewriter"'),
        'lipgloss': re.compile(r'"github\.com/charmbracelet/lipgloss"'),
        'bubbletea': re.compile(r'"github\.com/charmbracelet/bubbletea"'),
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> CobraParseResult:
        result = CobraParseResult(file_path=file_path)

        if not self.COBRA_IMPORT.search(content):
            # Check for cobra.Command usage without import
            if 'cobra.Command' not in content:
                return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.has_viper = bool(self.VIPER_IMPORT.search(content))
        result.has_completion = bool(self.COMPLETION_PATTERN.search(content) or self.VALID_ARGS_FUNC.search(content))

        required_flags = set()
        for m in self.REQUIRED_FLAG_PATTERN.finditer(content):
            required_flags.add(m.group(1))
        for m in self.REQUIRED_PERSISTENT_PATTERN.finditer(content):
            required_flags.add(m.group(1))

        # Commands
        for m in self.COMMAND_PATTERN.finditer(content):
            var_name = m.group(1)
            body = m.group(2)

            use_m = self.USE_PATTERN.search(body)
            short_m = self.SHORT_PATTERN.search(body)
            long_m = self.LONG_PATTERN.search(body)

            use_str = use_m.group(1) if use_m else ""
            cmd_name = use_str.split()[0] if use_str else var_name

            is_root = bool(self.ROOT_CMD_PATTERN.match(var_name))

            result.commands.append(CobraCommandInfo(
                name=cmd_name,
                use=use_str,
                short=short_m.group(1) if short_m else "",
                long=(long_m.group(1) or long_m.group(2)) if long_m else "",
                variable_name=var_name,
                has_run=bool(self.RUN_PATTERN.search(body)),
                has_run_e=bool(self.RUN_E_PATTERN.search(body)),
                has_pre_run=bool(self.PRE_RUN_PATTERN.search(body)),
                has_post_run=bool(self.POST_RUN_PATTERN.search(body)),
                has_persistent_pre_run=bool(self.PERSISTENT_PRE_RUN_PATTERN.search(body)),
                has_persistent_post_run=bool(self.PERSISTENT_POST_RUN_PATTERN.search(body)),
                has_valid_args=bool(self.VALID_ARGS_PATTERN.search(body)),
                is_root=is_root,
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Sub-command registration
        for m in self.ADD_COMMAND_PATTERN.finditer(content):
            parent = m.group(1)
            children_str = m.group(2)
            for child in children_str.split(','):
                child = child.strip()
                if child:
                    result.sub_commands.append(CobraSubCommandInfo(
                        parent=parent, child=child,
                        file=file_path, line_number=content[:m.start()].count('\n') + 1,
                    ))

        # Command groups
        for m in self.ADD_GROUP_PATTERN.finditer(content):
            result.groups.append(CobraGroupInfo(
                id=m.group(1), title=m.group(2),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Persistent flags
        for m in self.PERSISTENT_FLAG_PATTERN.finditer(content):
            flag_name = m.group(3)
            result.flags.append(CobraFlagInfo(
                name=flag_name, flag_type=m.group(2),
                short_hand=m.group(4) or "",
                default_value=m.group(5) or "",
                description=m.group(6) or "",
                is_persistent=True,
                is_required=flag_name in required_flags,
                command=m.group(1),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Local flags
        for m in self.LOCAL_FLAG_PATTERN.finditer(content):
            flag_name = m.group(3)
            result.flags.append(CobraFlagInfo(
                name=flag_name, flag_type=m.group(2),
                short_hand=m.group(4) or "",
                default_value=m.group(5) or "",
                description=m.group(6) or "",
                is_persistent=False,
                is_required=flag_name in required_flags,
                command=m.group(1),
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        # Viper bindings
        for m in self.VIPER_BIND_PFLAG.finditer(content):
            result.viper_bindings.append(CobraViperBindInfo(
                config_key=m.group(1), flag_name=m.group(2),
                bind_type="BindPFlag",
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.VIPER_BIND_ENV.finditer(content):
            result.viper_bindings.append(CobraViperBindInfo(
                config_key=m.group(1), flag_name="",
                bind_type="BindEnv",
                file=file_path, line_number=content[:m.start()].count('\n') + 1,
            ))

        result.total_commands = len(result.commands)
        result.total_flags = len(result.flags)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks
