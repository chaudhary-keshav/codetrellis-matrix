"""
CodeTrellis Env Inference Extractor — Phase 4 of v5.0 Universal Scanner
=========================================================================

Infers required environment variables by scanning source code for
config access patterns. Supports:

- Go:       os.Getenv("X"), viper.GetString("x"), envconfig struct tags
- Python:   os.environ["X"], os.getenv("X"), pydantic Settings fields
- Node/TS:  process.env.X, config.get("x")
- Rust:     std::env::var("X")
- Ruby:     ENV["X"], ENV.fetch("X")
- Java:     System.getenv("X"), @Value("${X}")

Merges inferred variables with config templates to highlight
"used but undocumented" and "documented but unused" gaps.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codetrellis.file_classifier import GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class InferredEnvVar:
    """An environment variable inferred from source code."""
    name: str
    source_files: List[str] = field(default_factory=list)
    access_patterns: List[str] = field(default_factory=list)  # e.g. "os.Getenv", "viper.Get"
    default_value: Optional[str] = None
    is_required: bool = False        # No default → required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_files": self.source_files,
            "access_patterns": self.access_patterns,
            "default_value": self.default_value,
            "is_required": self.is_required,
        }


@dataclass
class EnvInferenceResult:
    """Result of environment variable inference."""
    inferred_vars: Dict[str, InferredEnvVar] = field(default_factory=dict)
    documented_only: List[str] = field(default_factory=list)   # In templates but not code
    undocumented: List[str] = field(default_factory=list)       # In code but not templates
    total_files_scanned: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inferred_vars": {k: v.to_dict() for k, v in self.inferred_vars.items()},
            "documented_only": self.documented_only,
            "undocumented": self.undocumented,
            "total_files_scanned": self.total_files_scanned,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# Env Variables ({len(self.inferred_vars)} inferred, "
                      f"{len(self.undocumented)} undocumented)")

        if self.undocumented:
            lines.append(f"## UNDOCUMENTED ({len(self.undocumented)})")
            for name in self.undocumented:
                var = self.inferred_vars.get(name)
                if var:
                    patterns = ','.join(set(var.access_patterns))
                    lines.append(f"  {name} [{patterns}] in {len(var.source_files)} file(s)")

        if self.documented_only:
            lines.append(f"## DOCUMENTED_ONLY ({len(self.documented_only)})")
            for name in self.documented_only[:20]:
                lines.append(f"  {name}")

        # All inferred
        lines.append(f"## ALL INFERRED ({len(self.inferred_vars)})")
        for name, var in sorted(self.inferred_vars.items()):
            req = " [required]" if var.is_required else ""
            default = f"={var.default_value}" if var.default_value else ""
            lines.append(f"  {name}{default}{req}")

        return '\n'.join(lines)


# =============================================================================
# Language-Specific Patterns
# =============================================================================

# Each pattern: (regex, group_index_for_var_name, pattern_label, has_default_group)
# Group 1 = variable name, Group 2 = default value (if present)

GO_PATTERNS = [
    # os.Getenv("VAR")
    (re.compile(r'os\.Getenv\(\s*"([^"]+)"\s*\)'), 1, "os.Getenv", False),
    # os.LookupEnv("VAR")
    (re.compile(r'os\.LookupEnv\(\s*"([^"]+)"\s*\)'), 1, "os.LookupEnv", False),
    # viper.GetString("key"), viper.GetInt("key"), etc.
    (re.compile(r'viper\.Get\w*\(\s*"([^"]+)"\s*\)'), 1, "viper.Get", False),
    # viper.BindEnv("key", "ENV_VAR")
    (re.compile(r'viper\.BindEnv\(\s*"[^"]*"\s*,\s*"([^"]+)"\s*\)'), 1, "viper.BindEnv", False),
    # envconfig struct tag: `envconfig:"VAR"`
    (re.compile(r'`[^`]*envconfig:"([^"]+)"[^`]*`'), 1, "envconfig", False),
    # configor usage: env:"VAR"
    (re.compile(r'`[^`]*env:"([^"]+)"[^`]*`'), 1, "env_tag", False),
    # cli flag EnvVars
    (re.compile(r'EnvVars:\s*\[\]string\{[^}]*"([^"]+)"'), 1, "urfave_cli", False),
]

PYTHON_PATTERNS = [
    # os.environ["VAR"] or os.environ.get("VAR")
    (re.compile(r'os\.environ\[[\'"]([\w]+)[\'"]\]'), 1, "os.environ", False),
    (re.compile(r'os\.environ\.get\(\s*[\'"]([\w]+)[\'"](?:\s*,\s*[\'"]([^"\']*)[\'"])?\s*\)'), 1, "os.environ.get", True),
    # os.getenv("VAR", "default")
    (re.compile(r'os\.getenv\(\s*[\'"]([\w]+)[\'"](?:\s*,\s*[\'"]([^"\']*)[\'"])?\s*\)'), 1, "os.getenv", True),
    # pydantic Field with env
    (re.compile(r'Field\([^)]*env=[\'"]([\w]+)[\'"]'), 1, "pydantic.Field", False),
    # pydantic model_config with env_prefix
    (re.compile(r'env_prefix\s*=\s*[\'"]([\w]+)[\'"]'), 1, "pydantic.env_prefix", False),
    # django settings: env("VAR")
    (re.compile(r'env\(\s*[\'"]([\w]+)[\'"]'), 1, "django_environ", False),
    # decouple config("VAR")
    (re.compile(r'config\(\s*[\'"]([\w]+)[\'"]'), 1, "decouple.config", False),
]

JS_TS_PATTERNS = [
    # process.env.VAR
    (re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)'), 1, "process.env", False),
    # process.env["VAR"]
    (re.compile(r'process\.env\[\s*[\'"]([\w]+)[\'"]\s*\]'), 1, "process.env", False),
    # import.meta.env.VAR (Vite)
    (re.compile(r'import\.meta\.env\.([A-Z_][A-Z0-9_]*)'), 1, "import.meta.env", False),
    # @nestjs/config: configService.get("VAR")
    (re.compile(r'configService\.get(?:<[^>]*>)?\(\s*[\'"]([\w]+)[\'"]'), 1, "configService.get", False),
]

RUST_PATTERNS = [
    # std::env::var("VAR")
    (re.compile(r'env::var\(\s*"([^"]+)"\s*\)'), 1, "env::var", False),
    # std::env::var_os("VAR")
    (re.compile(r'env::var_os\(\s*"([^"]+)"\s*\)'), 1, "env::var_os", False),
]

RUBY_PATTERNS = [
    # ENV["VAR"] or ENV.fetch("VAR")
    (re.compile(r'ENV\[\s*[\'"]([\w]+)[\'"]\s*\]'), 1, "ENV[]", False),
    (re.compile(r'ENV\.fetch\(\s*[\'"]([\w]+)[\'"](?:\s*,\s*[\'"]([^"\']*)[\'"])?\s*\)'), 1, "ENV.fetch", True),
]

JAVA_PATTERNS = [
    # System.getenv("VAR")
    (re.compile(r'System\.getenv\(\s*"([^"]+)"\s*\)'), 1, "System.getenv", False),
    # @Value("${VAR}")
    (re.compile(r'@Value\(\s*"\$\{([^}:]+)(?::([^}]*))?\}"\s*\)'), 1, "@Value", True),
]

# Extension → pattern set
EXTENSION_PATTERNS: Dict[str, list] = {
    '.go': GO_PATTERNS,
    '.py': PYTHON_PATTERNS,
    '.js': JS_TS_PATTERNS,
    '.ts': JS_TS_PATTERNS,
    '.jsx': JS_TS_PATTERNS,
    '.tsx': JS_TS_PATTERNS,
    '.mjs': JS_TS_PATTERNS,
    '.rs': RUST_PATTERNS,
    '.rb': RUBY_PATTERNS,
    '.java': JAVA_PATTERNS,
    '.kt': JAVA_PATTERNS,
}


# =============================================================================
# Env Inference Extractor
# =============================================================================

class EnvInferenceExtractor:
    """
    Infer required environment variables from source code.

    Scans all source files for env-access patterns and builds
    a map of inferred variables. When combined with ConfigTemplateResult,
    highlights undocumented and unused variables.
    """

    # Skip well-known non-user variables
    SKIP_VARS = {
        'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'LC_ALL',
        'PWD', 'OLDPWD', 'HOSTNAME', 'LOGNAME', 'GOPATH', 'GOROOT',
        'NODE_ENV', 'PYTHONPATH', 'VIRTUAL_ENV',
    }

    IGNORE_DIRS = {
        'node_modules', '.git', 'dist', 'build', '__pycache__',
        'vendor', '.next', 'coverage', 'venv', '.venv', '.tox',
        'test', 'tests', '__tests__', 'spec', 'fixtures',
    }

    def extract_from_directory(self, root_dir: Path,
                               gitignore_filter: Optional[GitignoreFilter] = None,
                               ) -> Optional[EnvInferenceResult]:
        """
        Scan all source files for env variable access patterns.

        Args:
            root_dir: Root directory to scan
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            EnvInferenceResult or None if nothing found
        """
        result = EnvInferenceResult()
        file_count = 0

        gi = gitignore_filter

        for root, dirs, files in _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]
            for f in files:
                fp = root / f
                ext = fp.suffix.lower()

                if ext not in EXTENSION_PATTERNS:
                    continue

                file_count += 1
                try:
                    content = fp.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue

                self._scan_file(content, str(fp), ext, result)

        result.total_files_scanned = file_count
        return result if result.inferred_vars else None

    def _scan_file(
        self, content: str, file_path: str, ext: str, result: EnvInferenceResult
    ) -> None:
        """Scan a single file for env patterns."""
        patterns = EXTENSION_PATTERNS.get(ext, [])

        for regex, group_idx, label, has_default in patterns:
            for match in regex.finditer(content):
                var_name = match.group(group_idx)
                if not var_name or var_name in self.SKIP_VARS:
                    continue
                # Skip if it looks like a non-env string (lowercase, too short)
                if len(var_name) < 2:
                    continue

                default_value = None
                if has_default and match.lastindex and match.lastindex >= 2:
                    default_value = match.group(2)

                if var_name in result.inferred_vars:
                    existing = result.inferred_vars[var_name]
                    if file_path not in existing.source_files:
                        existing.source_files.append(file_path)
                    if label not in existing.access_patterns:
                        existing.access_patterns.append(label)
                    if default_value and not existing.default_value:
                        existing.default_value = default_value
                        existing.is_required = False
                else:
                    result.inferred_vars[var_name] = InferredEnvVar(
                        name=var_name,
                        source_files=[file_path],
                        access_patterns=[label],
                        default_value=default_value,
                        is_required=default_value is None,
                    )

    def merge_with_templates(
        self,
        inferred: 'EnvInferenceResult',
        documented_vars: Set[str],
    ) -> None:
        """
        Merge inferred vars with documented template vars.

        Populates inferred.documented_only and inferred.undocumented lists.

        Args:
            inferred: The inference result to update in-place
            documented_vars: Set of variable names from config templates
        """
        inferred_names = set(inferred.inferred_vars.keys())

        inferred.undocumented = sorted(inferred_names - documented_vars)
        inferred.documented_only = sorted(documented_vars - inferred_names)


# =============================================================================
# Compatibility helper
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
