"""
CodeTrellis Config Template Extractor — Phase 4 of v5.0 Universal Scanner
==========================================================================

Extracts configuration templates and their variables from:
- .env.example / .env.sample / .env.template
- docker-compose.yml environment sections
- Kubernetes ConfigMap / Secret templates
- Helm values.yaml
- Terraform variable definitions
- config/*.example.* files

Maps every expected configuration variable with its default value,
description, and source file.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from codetrellis.file_classifier import GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConfigVariable:
    """A single configuration variable."""
    name: str
    default_value: Optional[str] = None
    description: Optional[str] = None
    source_file: str = ""
    required: bool = False
    category: str = "general"       # database, auth, api, storage, cache, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "default_value": self.default_value,
            "description": self.description,
            "source_file": self.source_file,
            "required": self.required,
            "category": self.category,
        }


@dataclass
class ConfigTemplate:
    """A single config template file parsed."""
    file_path: str
    template_type: str            # "env", "docker-compose", "k8s", "helm", "terraform"
    variables: List[ConfigVariable] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "template_type": self.template_type,
            "variables": [v.to_dict() for v in self.variables],
        }


@dataclass
class ConfigTemplateResult:
    """Aggregate result from all config templates."""
    templates: List[ConfigTemplate] = field(default_factory=list)
    all_variables: Dict[str, ConfigVariable] = field(default_factory=dict)  # name → var

    def to_dict(self) -> Dict[str, Any]:
        return {
            "templates": [t.to_dict() for t in self.templates],
            "all_variables": {k: v.to_dict() for k, v in self.all_variables.items()},
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# Config Templates ({len(self.templates)} file(s), {len(self.all_variables)} variable(s))")

        # Group variables by category
        by_category: Dict[str, List[ConfigVariable]] = {}
        for var in self.all_variables.values():
            cat = var.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(var)

        for category, vars_list in sorted(by_category.items()):
            lines.append(f"## {category.upper()} ({len(vars_list)})")
            for var in vars_list:
                default_str = f"={var.default_value}" if var.default_value else ""
                req = " [required]" if var.required else ""
                desc = f" # {var.description}" if var.description else ""
                lines.append(f"  {var.name}{default_str}{req}{desc}")

        return '\n'.join(lines)


# =============================================================================
# Category Detection
# =============================================================================

CATEGORY_PATTERNS: Dict[str, re.Pattern] = {
    "database": re.compile(r'DB_|DATABASE_|MONGO|POSTGRES|MYSQL|REDIS|SQL|SQLITE', re.I),
    "auth": re.compile(r'AUTH|JWT|TOKEN|SECRET|SESSION|OAUTH|API_KEY|PASSWORD', re.I),
    "api": re.compile(r'API_|BASE_URL|ENDPOINT|HOST|PORT|URL|CORS', re.I),
    "storage": re.compile(r'S3_|STORAGE|BUCKET|MINIO|UPLOAD|ASSET', re.I),
    "cache": re.compile(r'CACHE|REDIS|MEMCACHE', re.I),
    "email": re.compile(r'SMTP|MAIL|EMAIL|SENDGRID', re.I),
    "logging": re.compile(r'LOG_|SENTRY|LOGGING|DATADOG|NEWRELIC', re.I),
    "feature": re.compile(r'FEATURE_|ENABLE_|DISABLE_|FLAG_', re.I),
    "ci_cd": re.compile(r'CI_|CD_|DEPLOY|BUILD|DOCKER|REGISTRY', re.I),
}


def _categorize(name: str) -> str:
    """Determine category for a config variable name."""
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(name):
            return category
    return "general"


# =============================================================================
# Config Template Extractor
# =============================================================================

class ConfigTemplateExtractor:
    """
    Extract config templates and their variables from a project.
    """

    # Files that are config templates
    ENV_TEMPLATE_NAMES = {
        '.env.example', '.env.sample', '.env.template',
        '.env.development', '.env.production', '.env.staging',
        '.env.local.example', '.env.test',
        'env.example', 'env.sample',
    }

    HELM_FILES = {'values.yaml', 'values.yml'}

    def can_extract_file(self, file_path: Path) -> bool:
        """Check if this file is a config template."""
        name = file_path.name.lower()
        if name in self.ENV_TEMPLATE_NAMES:
            return True
        if name in self.HELM_FILES and 'chart' in str(file_path).lower():
            return True
        if name.endswith(('.example', '.sample', '.template')) and 'config' in str(file_path).lower():
            return True
        if name in ('docker-compose.yml', 'docker-compose.yaml') and file_path.exists():
            return True
        return False

    def extract_from_directory(self, root_dir: Path,
                               gitignore_filter: Optional[GitignoreFilter] = None,
                               ) -> Optional[ConfigTemplateResult]:
        """
        Scan directory for all config templates and extract variables.

        Args:
            root_dir: Root directory to scan
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            ConfigTemplateResult or None if nothing found
        """
        result = ConfigTemplateResult()

        ignore_dirs = {
            'node_modules', '.git', 'dist', 'build', '__pycache__',
            'vendor', '.next', 'coverage', 'venv', '.venv',
        }

        gi = gitignore_filter

        for root, dirs, files in _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]
            for f in files:
                fp = root / f
                if self.can_extract_file(fp):
                    template = self._extract_file(fp)
                    if template and template.variables:
                        result.templates.append(template)
                        for var in template.variables:
                            if var.name not in result.all_variables:
                                result.all_variables[var.name] = var

        return result if result.templates else None

    def _extract_file(self, file_path: Path) -> Optional[ConfigTemplate]:
        """Parse a single config template file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None

        name = file_path.name.lower()

        if any(name.startswith('.env') or name.startswith('env.')):
            return self._parse_env_file(content, str(file_path))
        elif name in ('docker-compose.yml', 'docker-compose.yaml'):
            return self._parse_docker_compose(content, str(file_path))
        elif name in self.HELM_FILES:
            return self._parse_helm_values(content, str(file_path))
        elif name.endswith(('.example', '.sample', '.template')):
            return self._parse_env_file(content, str(file_path))

        return None

    def _parse_env_file(self, content: str, file_path: str) -> ConfigTemplate:
        """Parse a .env-style file."""
        template = ConfigTemplate(
            file_path=file_path,
            template_type="env",
        )

        last_comment = None

        for line in content.splitlines():
            stripped = line.strip()

            # Comment line
            if stripped.startswith('#'):
                comment = stripped.lstrip('#').strip()
                if comment:
                    last_comment = comment
                continue

            # Empty line resets comment
            if not stripped:
                last_comment = None
                continue

            # Parse KEY=VALUE
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.*))?$', stripped)
            if match:
                key = match.group(1)
                value = match.group(2)

                # Clean value
                if value:
                    value = value.strip()
                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    # Remove inline comments
                    inline_comment = re.search(r'\s+#\s+(.+)$', value)
                    if inline_comment:
                        value = value[:inline_comment.start()].strip()

                template.variables.append(ConfigVariable(
                    name=key,
                    default_value=value if value else None,
                    description=last_comment,
                    source_file=file_path,
                    required=not value,
                    category=_categorize(key),
                ))
                last_comment = None

        return template

    def _parse_docker_compose(self, content: str, file_path: str) -> ConfigTemplate:
        """Extract environment variables from docker-compose.yml."""
        template = ConfigTemplate(
            file_path=file_path,
            template_type="docker-compose",
        )

        seen: Set[str] = set()

        # Match environment: sections with KEY=VALUE or ${VAR} patterns
        # Simple regex approach - handles common patterns
        for match in re.finditer(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::?-([^}]*))?\}', content):
            name = match.group(1)
            default = match.group(2)
            if name not in seen:
                seen.add(name)
                template.variables.append(ConfigVariable(
                    name=name,
                    default_value=default if default else None,
                    source_file=file_path,
                    required=not default,
                    category=_categorize(name),
                ))

        # Also match inline KEY=VALUE in environment sections
        in_env = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith('environment:'):
                in_env = True
                continue
            if in_env:
                if stripped.startswith('- ') or stripped.startswith('-'):
                    env_val = stripped.lstrip('- ').strip()
                    eq_match = re.match(r'^([A-Za-z_]\w*)=(.*)$', env_val)
                    if eq_match and eq_match.group(1) not in seen:
                        name = eq_match.group(1)
                        seen.add(name)
                        template.variables.append(ConfigVariable(
                            name=name,
                            default_value=eq_match.group(2) or None,
                            source_file=file_path,
                            category=_categorize(name),
                        ))
                elif stripped and not stripped.startswith('#') and not stripped.startswith('-'):
                    # Indented KEY: VALUE
                    kv_match = re.match(r'^([A-Za-z_]\w*):\s*(.*)$', stripped)
                    if kv_match and kv_match.group(1) not in seen:
                        name = kv_match.group(1)
                        val = kv_match.group(2).strip().strip('"').strip("'")
                        seen.add(name)
                        template.variables.append(ConfigVariable(
                            name=name,
                            default_value=val if val else None,
                            source_file=file_path,
                            category=_categorize(name),
                        ))
                    elif not re.match(r'^\s', line):
                        in_env = False

        return template

    def _parse_helm_values(self, content: str, file_path: str) -> ConfigTemplate:
        """Extract keys from a Helm values.yaml."""
        template = ConfigTemplate(
            file_path=file_path,
            template_type="helm",
        )

        # Parse top-level and one-level-deep YAML keys
        current_section = ""
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Top-level key
            if not line.startswith(' ') and not line.startswith('\t'):
                match = re.match(r'^(\w+):\s*(.*)', stripped)
                if match:
                    current_section = match.group(1)
                    value = match.group(2).strip()
                    if value and value != '{}' and value != '[]':
                        template.variables.append(ConfigVariable(
                            name=current_section,
                            default_value=value.strip('"').strip("'"),
                            source_file=file_path,
                            category=_categorize(current_section),
                        ))
            else:
                # Nested key
                match = re.match(r'^(\w+):\s*(.*)', stripped)
                if match and current_section:
                    key = f"{current_section}.{match.group(1)}"
                    value = match.group(2).strip()
                    if value and value != '{}' and value != '[]':
                        template.variables.append(ConfigVariable(
                            name=key,
                            default_value=value.strip('"').strip("'"),
                            source_file=file_path,
                            category=_categorize(match.group(1)),
                        ))

        return template


# =============================================================================
# Compatibility helper
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
