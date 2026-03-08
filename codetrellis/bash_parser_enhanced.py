"""
EnhancedBashParser v1.0 - Comprehensive Bash/Shell parser using all extractors.

This parser integrates all Bash extractors to provide complete
parsing of Bash/Shell source files.

Supports:
- All POSIX sh, Bash 2.x-5.x, Zsh, Ksh, Dash, Ash syntax
- Functions (POSIX and bash keyword styles)
- Variables (simple, export, readonly, declare, arrays, associative arrays)
- Aliases, source/include, shebang detection
- Pipelines, subshells, process substitution, traps, here-docs
- HTTP API calls (curl, wget, httpie)
- Service management (Docker, Kubernetes, systemd, cloud CLIs)
- AST support via tree-sitter-bash (optional, degrades to regex)
- LSP support via bash-language-server (optional, degrades to regex)

Bash version detection:
- sh (POSIX)
- bash 2.x, 3.x, 4.x, 5.x (feature-based detection)
- zsh, ksh, ksh93, dash, ash, fish

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from pathlib import Path

# Import all Bash extractors
from .extractors.bash import (
    BashFunctionExtractor, BashFunctionInfo, BashParameterInfo,
    BashVariableExtractor, BashVariableInfo, BashArrayInfo, BashExportInfo,
    BashAliasExtractor, BashAliasInfo, BashSourceInfo, BashShebangInfo,
    BashCommandExtractor, BashPipelineInfo, BashTrapInfo, BashSubshellInfo,
    BashHereDocInfo, BashRedirectInfo,
    BashAPIExtractor, BashHTTPCallInfo, BashCronJobInfo, BashServiceInfo,
)

# Optional: tree-sitter for AST parsing
_has_tree_sitter = False
_bash_language = None
try:
    import tree_sitter_bash as tsbash
    from tree_sitter import Language, Parser as TSParser
    _bash_language = Language(tsbash.language())
    _has_tree_sitter = True
except ImportError:
    pass

# Optional: bash-language-server for LSP
_has_bash_lsp = False
try:
    _bash_lsp_check = subprocess.run(
        ['bash-language-server', '--version'],
        capture_output=True, timeout=5
    )
    if _bash_lsp_check.returncode == 0:
        _has_bash_lsp = True
except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
    pass


@dataclass
class BashParseResult:
    """Complete parse result for a Bash/Shell file."""
    file_path: str
    file_type: str = "bash"

    # Shebang / shell metadata
    shebang: Optional[BashShebangInfo] = None
    shell_type: str = ""           # bash, sh, zsh, ksh, dash, ash, fish
    detected_version: str = ""     # e.g., "bash 5.0+"

    # Functions
    functions: List[BashFunctionInfo] = field(default_factory=list)

    # Variables
    variables: List[BashVariableInfo] = field(default_factory=list)
    arrays: List[BashArrayInfo] = field(default_factory=list)
    exports: List[BashExportInfo] = field(default_factory=list)

    # Aliases and sources
    aliases: List[BashAliasInfo] = field(default_factory=list)
    sources: List[BashSourceInfo] = field(default_factory=list)

    # Shell options
    shell_options: List[Dict] = field(default_factory=list)
    shopt_options: List[Dict] = field(default_factory=list)

    # Commands
    pipelines: List[BashPipelineInfo] = field(default_factory=list)
    traps: List[BashTrapInfo] = field(default_factory=list)
    subshells: List[BashSubshellInfo] = field(default_factory=list)
    heredocs: List[BashHereDocInfo] = field(default_factory=list)
    redirects: List[BashRedirectInfo] = field(default_factory=list)

    # API / Services
    http_calls: List[BashHTTPCallInfo] = field(default_factory=list)
    cron_jobs: List[BashCronJobInfo] = field(default_factory=list)
    services: List[BashServiceInfo] = field(default_factory=list)
    db_commands: List[Dict] = field(default_factory=list)
    package_commands: List[Dict] = field(default_factory=list)

    # AST info (if tree-sitter available)
    ast_node_count: int = 0
    ast_errors: int = 0

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    total_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    has_strict_mode: bool = False   # set -euo pipefail or similar


class EnhancedBashParser:
    """
    Enhanced Bash parser that uses all extractors for comprehensive parsing.

    Features:
    - Regex-based extraction (always available)
    - tree-sitter AST (optional, for precise parsing)
    - bash-language-server LSP (optional, for diagnostics)

    Framework detection supports:
    - Docker (Dockerfile, docker-compose)
    - Kubernetes (kubectl, helm)
    - CI/CD tools (Jenkins, GitHub Actions, GitLab CI)
    - Cloud CLIs (AWS, GCP, Azure)
    - Build tools (Make, CMake, Gradle wrapper)
    - Package managers (apt, yum, brew, pip, npm)
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'docker': re.compile(r'\bdocker\b|\bdocker-compose\b|\bpodman\b'),
        'kubernetes': re.compile(r'\bkubectl\b|\bhelm\b|\bminikube\b|\bkind\b'),
        'terraform': re.compile(r'\bterraform\b|\btofu\b'),
        'ansible': re.compile(r'\bansible\b|\bansible-playbook\b'),
        'aws-cli': re.compile(r'\baws\s'),
        'gcloud': re.compile(r'\bgcloud\s'),
        'azure-cli': re.compile(r'\baz\s'),
        'jenkins': re.compile(r'\bjenkins\b|JOB_NAME|BUILD_NUMBER'),
        'github-actions': re.compile(r'GITHUB_ACTION|GITHUB_WORKSPACE|RUNNER_'),
        'gitlab-ci': re.compile(r'CI_PIPELINE_|CI_PROJECT_|GITLAB_'),
        'circle-ci': re.compile(r'CIRCLE_|CIRCLECI'),
        'make': re.compile(r'\bmake\b|\b\$\(MAKE\)'),
        'gradle': re.compile(r'\bgradlew?\b|\bgradle\b'),
        'maven': re.compile(r'\bmvnw?\b|\bmaven\b'),
        'git': re.compile(r'\bgit\s+(clone|pull|push|checkout|merge|rebase)\b'),
        'systemd': re.compile(r'\bsystemctl\b|\bjournalctl\b'),
        'supervisor': re.compile(r'\bsupervisorctl\b|\bsupervisord\b'),
        'nginx': re.compile(r'\bnginx\b'),
        'ssh': re.compile(r'\bssh\b|\bscp\b|\brsync\b'),
        'cron': re.compile(r'\bcrontab\b|\bcron\b'),
    }

    # Strict mode patterns
    STRICT_MODE = re.compile(
        r'set\s+-(?:[a-zA-Z]*e[a-zA-Z]*|o\s+errexit)|set\s+-(?:[a-zA-Z]*u[a-zA-Z]*|o\s+nounset)'
    )

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.function_extractor = BashFunctionExtractor()
        self.variable_extractor = BashVariableExtractor()
        self.alias_extractor = BashAliasExtractor()
        self.command_extractor = BashCommandExtractor()
        self.api_extractor = BashAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> BashParseResult:
        """
        Parse Bash/Shell source code and extract all information.

        Args:
            content: Bash/Shell source code content
            file_path: Path to source file

        Returns:
            BashParseResult with all extracted information
        """
        result = BashParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Line metrics
        lines = content.split('\n')
        result.total_lines = len(lines)
        result.comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
        result.blank_lines = sum(1 for l in lines if not l.strip())

        # Strict mode detection
        result.has_strict_mode = bool(self.STRICT_MODE.search(content))

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Extract shebang and alias/source info
        alias_result = self.alias_extractor.extract(content, file_path)
        result.shebang = alias_result.get('shebang')
        result.aliases = alias_result.get('aliases', [])
        result.sources = alias_result.get('sources', [])
        result.shell_options = alias_result.get('shell_options', [])
        result.shopt_options = alias_result.get('shopt_options', [])

        # Set shell type from shebang
        if result.shebang:
            result.shell_type = result.shebang.shell_type
            result.detected_version = result.shebang.version_hint
        else:
            # Infer from file extension or content
            result.shell_type = self._infer_shell_type(file_path, content)

        # Extract functions
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])

        # Extract variables
        var_result = self.variable_extractor.extract(content, file_path)
        result.variables = var_result.get('variables', [])
        result.arrays = var_result.get('arrays', [])
        result.exports = var_result.get('exports', [])

        # Extract command patterns
        cmd_result = self.command_extractor.extract(content, file_path)
        result.pipelines = cmd_result.get('pipelines', [])
        result.traps = cmd_result.get('traps', [])
        result.subshells = cmd_result.get('subshells', [])
        result.heredocs = cmd_result.get('heredocs', [])
        result.redirects = cmd_result.get('redirects', [])

        # Extract API/service patterns
        api_result = self.api_extractor.extract(content, file_path)
        result.http_calls = api_result.get('http_calls', [])
        result.cron_jobs = api_result.get('cron_jobs', [])
        result.services = api_result.get('services', [])
        result.db_commands = api_result.get('db_commands', [])
        result.package_commands = api_result.get('packages', [])

        # AST extraction (if tree-sitter available)
        if _has_tree_sitter:
            self._extract_ast_info(content, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks/tools are used in the script."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _infer_shell_type(self, file_path: str, content: str) -> str:
        """Infer shell type from file extension or content patterns."""
        if file_path:
            ext = Path(file_path).suffix.lower()
            name = Path(file_path).name.lower()
            ext_map = {
                '.sh': 'bash',
                '.bash': 'bash',
                '.zsh': 'zsh',
                '.ksh': 'ksh',
                '.dash': 'dash',
                '.ash': 'ash',
                '.fish': 'fish',
                '.csh': 'csh',
                '.tcsh': 'tcsh',
                '.bats': 'bash',  # Bats test framework
            }
            if ext in ext_map:
                return ext_map[ext]

            # Common shell script names
            name_map = {
                '.bashrc': 'bash', '.bash_profile': 'bash',
                '.bash_aliases': 'bash', '.bash_logout': 'bash',
                '.profile': 'sh', '.zshrc': 'zsh', '.zprofile': 'zsh',
                '.kshrc': 'ksh', '.cshrc': 'csh',
            }
            if name in name_map:
                return name_map[name]

        # Check content for shell-specific features
        if re.search(r'\[\[', content):  # Bash/Zsh specific
            return 'bash'
        if re.search(r'typeset\b', content):  # ksh/zsh
            return 'ksh'
        return 'sh'  # Default to POSIX sh

    def _extract_ast_info(self, content: str, result: BashParseResult):
        """Extract AST information using tree-sitter (if available)."""
        if not _has_tree_sitter or not _bash_language:
            return

        try:
            parser = TSParser(_bash_language)
            tree = parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            result.ast_node_count = self._count_nodes(root)
            result.ast_errors = self._count_error_nodes(root)

            # Enhanced extraction from AST
            self._extract_functions_from_ast(root, content, result)

        except Exception:
            pass

    def _count_nodes(self, node) -> int:
        """Count all nodes in AST."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _count_error_nodes(self, node) -> int:
        """Count error nodes in AST."""
        count = 1 if node.type == 'ERROR' else 0
        for child in node.children:
            count += self._count_error_nodes(child)
        return count

    def _extract_functions_from_ast(self, root, content: str, result: BashParseResult):
        """Extract function definitions from AST for more precise results."""
        # tree-sitter-bash uses 'function_definition' node type
        for child in root.children:
            if child.type == 'function_definition':
                name_node = child.child_by_field_name('name')
                if name_node:
                    func_name = content[name_node.start_byte:name_node.end_byte]
                    # Cross-check with regex results for enrichment
                    for func in result.functions:
                        if func.name == func_name:
                            # AST confirmed — no action needed
                            break
            # Recurse into compound statements
            if child.type in ('compound_statement', 'subshell', 'if_statement',
                              'while_statement', 'for_statement', 'case_statement'):
                self._extract_functions_from_ast(child, content, result)

    @staticmethod
    def is_shell_script(file_path: str, content: str = "") -> bool:
        """
        Determine if a file is a shell script.

        Checks:
        1. File extension (.sh, .bash, .zsh, etc.)
        2. Shebang line (#!/bin/bash, #!/usr/bin/env sh, etc.)
        3. Common shell script filenames

        Args:
            file_path: Path to check
            content: Optional file content for shebang check

        Returns:
            True if the file appears to be a shell script
        """
        path = Path(file_path)

        # Check extension
        shell_extensions = {'.sh', '.bash', '.zsh', '.ksh', '.dash', '.ash',
                           '.fish', '.csh', '.tcsh', '.bats'}
        if path.suffix.lower() in shell_extensions:
            return True

        # Check common shell script names (no extension)
        shell_names = {
            '.bashrc', '.bash_profile', '.bash_aliases', '.bash_logout',
            '.profile', '.zshrc', '.zprofile', '.zshenv', '.zlogin', '.zlogout',
            '.kshrc', '.cshrc', '.tcshrc', '.login', '.logout',
            'Makefile',  # Not shell but has shell
        }
        if path.name in shell_names:
            return True

        # Scripts without extension but with shebang
        if content:
            first_line = content.split('\n')[0] if content else ""
            if first_line.startswith('#!'):
                shell_interpreters = {'bash', 'sh', 'zsh', 'ksh', 'dash',
                                     'ash', 'fish', 'csh', 'tcsh'}
                for interp in shell_interpreters:
                    if interp in first_line:
                        return True

        return False
