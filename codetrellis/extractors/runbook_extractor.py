"""
CodeTrellis Runbook Extractor
========================

Phase A (WS-1): Addresses gaps G-01, G-02, G-03 from the CodeTrellis Gap Analysis.

Extracts operational runbook information from a project:
- G-01: Run/build/test commands (package.json scripts, Makefile targets,
         pyproject.toml scripts, Dockerfile CMD/ENTRYPOINT)
- G-02: CI/CD pipeline definitions (.github/workflows, .gitlab-ci.yml,
         Jenkinsfile, bitbucket-pipelines.yml)
- G-03: Environment setup (.env.example, docker-compose.yml, README
         installation sections)

Output format:
    [RUNBOOK]
    # Commands
    dev=npm run start:dev
    build=npm run build
    test=npm run test
    lint=npm run lint
    # CI/CD
    ci:github-actions|triggers:push,pr|jobs:build,test,deploy
    # Environment
    env:NODE_ENV,DATABASE_URL,JWT_SECRET
    docker:node:18-alpine|ports:3000,5000|volumes:./src:/app/src
    compose:services:api,db,redis|networks:backend
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class CommandInfo:
    """A single runnable command"""
    name: str
    command: str
    source: str  # "package.json", "Makefile", "pyproject.toml", "Dockerfile"
    category: str = ""  # "dev", "build", "test", "lint", "deploy", "other"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "source": self.source,
            "category": self.category,
        }


@dataclass
class CICDPipeline:
    """CI/CD pipeline definition"""
    name: str
    platform: str  # "github-actions", "gitlab-ci", "jenkins", "bitbucket"
    file_path: str
    triggers: List[str] = field(default_factory=list)
    jobs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "platform": self.platform,
            "filePath": self.file_path,
            "triggers": self.triggers,
            "jobs": self.jobs,
        }


@dataclass
class EnvVariable:
    """Environment variable from .env.example"""
    name: str
    default_value: str = ""
    comment: str = ""
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "defaultValue": self.default_value,
            "comment": self.comment,
            "required": self.required,
        }


@dataclass
class DockerInfo:
    """Docker configuration info"""
    base_image: str = ""
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    cmd: str = ""
    entrypoint: str = ""
    stages: List[str] = field(default_factory=list)  # Multi-stage build stages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseImage": self.base_image,
            "ports": self.ports,
            "volumes": self.volumes,
            "cmd": self.cmd,
            "entrypoint": self.entrypoint,
            "stages": self.stages,
        }


@dataclass
class ComposeService:
    """Docker Compose service"""
    name: str
    image: str = ""
    build: str = ""
    ports: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    environment: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "image": self.image,
            "build": self.build,
            "ports": self.ports,
            "dependsOn": self.depends_on,
            "environment": self.environment,
        }


@dataclass
class ComposeInfo:
    """Docker Compose configuration"""
    services: List[ComposeService] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "services": [s.to_dict() for s in self.services],
            "networks": self.networks,
            "volumes": self.volumes,
        }


@dataclass
class RunbookContext:
    """Complete runbook information for the project"""
    project_name: str = ""

    # G-01: Commands
    commands: List[CommandInfo] = field(default_factory=list)

    # G-02: CI/CD
    pipelines: List[CICDPipeline] = field(default_factory=list)

    # G-03: Environment
    env_variables: List[EnvVariable] = field(default_factory=list)
    docker: Optional[DockerInfo] = None
    compose: Optional[ComposeInfo] = None
    install_steps: List[str] = field(default_factory=list)

    # v4.9: Developer guide context
    contributing_guide: Optional[Dict[str, Any]] = None  # CONTRIBUTING.md info
    examples: List[Dict[str, str]] = field(default_factory=list)  # examples/ directory
    version_requirements: List[Dict[str, str]] = field(default_factory=list)  # Go 1.22, Python >=3.9
    license_info: Optional[str] = None  # LICENSE file first line

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "projectName": self.project_name,
            "commands": [c.to_dict() for c in self.commands],
            "pipelines": [p.to_dict() for p in self.pipelines],
            "envVariables": [e.to_dict() for e in self.env_variables],
            "installSteps": self.install_steps,
        }
        if self.docker:
            result["docker"] = self.docker.to_dict()
        if self.compose:
            result["compose"] = self.compose.to_dict()
        # v4.9: Developer guide fields
        if self.contributing_guide:
            result["contributingGuide"] = self.contributing_guide
        if self.examples:
            result["examples"] = self.examples
        if self.version_requirements:
            result["versionRequirements"] = self.version_requirements
        if self.license_info:
            result["license"] = self.license_info
        return result

    def has_content(self) -> bool:
        """Check if any runbook data was extracted"""
        return bool(
            self.commands or self.pipelines or self.env_variables or
            self.docker or self.compose or self.install_steps or
            self.contributing_guide or self.examples or self.version_requirements
        )

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format for prompt injection"""
        lines = []

        # Commands section
        if self.commands:
            lines.append("# Commands")
            # Categorize commands
            categorized: Dict[str, List[CommandInfo]] = {}
            for cmd in self.commands:
                cat = cmd.category or "other"
                categorized.setdefault(cat, []).append(cmd)

            # Show most important categories first
            for cat in ["dev", "build", "test", "lint", "deploy", "start", "other"]:
                cmds = categorized.get(cat, [])
                for cmd in cmds[:5]:  # Limit per category
                    lines.append(f"{cmd.name}={cmd.command}")

        # CI/CD section
        if self.pipelines:
            lines.append("# CI/CD")
            for pipeline in self.pipelines:
                triggers = ','.join(pipeline.triggers[:4]) if pipeline.triggers else 'manual'
                jobs = ','.join(pipeline.jobs[:6]) if pipeline.jobs else 'n/a'
                lines.append(f"ci:{pipeline.platform}|triggers:{triggers}|jobs:{jobs}")

        # Environment section
        if self.env_variables:
            lines.append("# Environment")
            var_names = [v.name for v in self.env_variables[:15]]
            lines.append(f"env:{','.join(var_names)}")

        # Docker section
        if self.docker:
            parts = []
            if self.docker.base_image:
                parts.append(self.docker.base_image)
            if self.docker.ports:
                parts.append(f"ports:{','.join(self.docker.ports[:4])}")
            if self.docker.cmd:
                parts.append(f"cmd:{self.docker.cmd[:60]}")
            if self.docker.stages:
                parts.append(f"stages:{','.join(self.docker.stages[:4])}")
            if parts:
                lines.append(f"docker:{'|'.join(parts)}")

        # Compose section
        if self.compose and self.compose.services:
            svc_names = [s.name for s in self.compose.services]
            parts = [f"services:{','.join(svc_names[:8])}"]
            if self.compose.networks:
                parts.append(f"networks:{','.join(self.compose.networks[:4])}")
            lines.append(f"compose:{'|'.join(parts)}")

        # Install steps
        if self.install_steps:
            lines.append("# Setup")
            for step in self.install_steps[:5]:
                lines.append(f"  {step}")

        # v4.9: Contributing guide
        if self.contributing_guide:
            lines.append("# Contributing")
            if self.contributing_guide.get('path'):
                lines.append(f"  guide:{self.contributing_guide['path']}")
            for step in self.contributing_guide.get('setup_steps', [])[:5]:
                lines.append(f"  {step}")
            for prereq in self.contributing_guide.get('prerequisites', [])[:3]:
                lines.append(f"  req:{prereq}")

        # v4.9: Examples
        if self.examples:
            lines.append("# Examples")
            for ex in self.examples[:8]:
                lines.append(f"  {ex.get('path', '')}|{ex.get('description', '')}")

        # v4.9: Version requirements
        if self.version_requirements:
            lines.append("# Version Requirements")
            for vr in self.version_requirements[:5]:
                lines.append(f"  {vr.get('tool', '')}:{vr.get('version', '')}")

        # v4.9: License
        if self.license_info:
            lines.append(f"# License: {self.license_info}")

        return '\n'.join(lines)


# ============================================================
# Command categories for common script names
# ============================================================

COMMAND_CATEGORIES = {
    "dev": {"dev", "start:dev", "serve", "watch", "develop"},
    "start": {"start", "start:prod", "start:debug", "run", "up"},
    "build": {"build", "compile", "bundle", "pack", "dist"},
    "test": {"test", "test:unit", "test:e2e", "test:cov", "test:watch",
             "spec", "check", "verify", "coverage"},
    "lint": {"lint", "lint:fix", "format", "prettier", "eslint",
             "stylelint", "typecheck", "type-check"},
    "deploy": {"deploy", "release", "publish", "push", "ship",
               "ci", "cd"},
    "db": {"db:migrate", "db:seed", "migration:run", "migration:generate",
           "prisma:generate", "prisma:push"},
    "docker": {"docker:build", "docker:run", "docker:push",
               "compose:up", "compose:down"},
}


def _categorize_command(name: str) -> str:
    """Determine command category from its name"""
    name_lower = name.lower()
    for category, keywords in COMMAND_CATEGORIES.items():
        if name_lower in keywords:
            return category
        # Also check if name starts with a category prefix
        for kw in keywords:
            if name_lower.startswith(kw.split(':')[0] + ':'):
                return category
    return "other"


class RunbookExtractor:
    """
    Extracts runbook / operational context from a project.

    Scans for:
    - package.json scripts
    - pyproject.toml scripts
    - Makefile targets
    - Dockerfile CMD/ENTRYPOINT
    - docker-compose.yml services
    - .env.example variables
    - CI/CD configs (GitHub Actions, GitLab CI, etc.)
    - README installation/setup sections
    """

    def __init__(self):
        self._project_root: Optional[Path] = None

    def extract(self, project_path: str) -> RunbookContext:
        """
        Extract runbook context from a project directory.

        Args:
            project_path: Path to the project root

        Returns:
            RunbookContext with all extracted operational information
        """
        self._project_root = Path(project_path)
        ctx = RunbookContext(project_name=self._project_root.name)

        # G-01: Extract commands
        self._extract_package_json_scripts(ctx)
        self._extract_pyproject_scripts(ctx)
        self._extract_makefile_targets(ctx)
        self._extract_shell_scripts(ctx)
        self._extract_dockerfile(ctx)

        # G-02: Extract CI/CD
        self._extract_github_actions(ctx)
        self._extract_gitlab_ci(ctx)
        self._extract_other_ci(ctx)

        # G-03: Extract environment
        self._extract_env_example(ctx)
        self._extract_source_env_vars(ctx)  # v4.9: scan source code for env var usage
        self._extract_docker_compose(ctx)
        self._extract_readme_setup(ctx)

        # v4.9: Extract developer guide context
        self._extract_contributing(ctx)
        self._extract_examples(ctx)
        self._extract_version_requirements(ctx)
        self._extract_license(ctx)

        return ctx

    def can_extract(self, project_path: str) -> bool:
        """Check if project has any runbook-related files"""
        root = Path(project_path)
        indicators = [
            'package.json', 'pyproject.toml', 'Makefile',
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            '.env.example', '.env.sample',
            '.github/workflows', '.gitlab-ci.yml',
        ]
        for ind in indicators:
            target = root / ind
            if target.exists():
                return True
        return False

    # ========================================================
    # G-01: Command extraction
    # ========================================================

    def _extract_package_json_scripts(self, ctx: RunbookContext):
        """Extract scripts from package.json (root and service-level)"""
        if not self._project_root:
            return

        # Find all package.json files (root + services/)
        pkg_files = [self._project_root / 'package.json']

        for sub_dir in ['services', 'packages', 'apps']:
            services_dir = self._project_root / sub_dir
            if services_dir.is_dir():
                for child in services_dir.iterdir():
                    if child.is_dir():
                        pkg = child / 'package.json'
                        if pkg.exists():
                            pkg_files.append(pkg)

        for pkg_path in pkg_files:
            if not pkg_path.exists():
                continue
            try:
                import json
                with open(pkg_path, encoding='utf-8') as f:
                    data = json.load(f)

                scripts = data.get('scripts', {})
                source = str(pkg_path.relative_to(self._project_root))

                for name, command in scripts.items():
                    ctx.commands.append(CommandInfo(
                        name=name,
                        command=command,
                        source=source,
                        category=_categorize_command(name),
                    ))
            except Exception:
                pass

    def _extract_pyproject_scripts(self, ctx: RunbookContext):
        """Extract scripts from pyproject.toml"""
        if not self._project_root:
            return

        pyproject = self._project_root / 'pyproject.toml'
        if not pyproject.exists():
            return

        try:
            content = pyproject.read_text(encoding='utf-8')

            # Parse [tool.poetry.scripts] or [project.scripts]
            in_scripts = False
            section_pattern = re.compile(r'^\[(.*)\]')
            entry_pattern = re.compile(r'^(\w[\w-]*)\s*=\s*["\'](.+?)["\']')

            for line in content.split('\n'):
                line = line.strip()
                section_match = section_pattern.match(line)
                if section_match:
                    section = section_match.group(1).lower()
                    in_scripts = section in (
                        'tool.poetry.scripts', 'project.scripts',
                        'tool.poetry.plugins', 'project.entry-points',
                    )
                    continue

                if in_scripts:
                    entry_match = entry_pattern.match(line)
                    if entry_match:
                        ctx.commands.append(CommandInfo(
                            name=entry_match.group(1),
                            command=entry_match.group(2),
                            source='pyproject.toml',
                            category=_categorize_command(entry_match.group(1)),
                        ))
        except Exception:
            pass

    def _extract_makefile_targets(self, ctx: RunbookContext):
        """Extract targets, variables, and metadata from Makefile.

        Phase E (G-16): Enhanced Makefile parsing beyond basic targets.
        Now extracts:
        - Target names with prerequisite chains
        - .PHONY declarations (marks targets that aren't files)
        - Variable assignments (=, :=, ?=, +=)
        - include directives
        - First command lines for each target
        """
        if not self._project_root:
            return

        makefile = self._project_root / 'Makefile'
        if not makefile.exists():
            return

        try:
            content = makefile.read_text(encoding='utf-8')

            # --- Phase E: Extract .PHONY declarations ---
            phony_targets: set = set()
            phony_pattern = re.compile(r'^\.PHONY\s*:\s*(.+)', re.MULTILINE)
            for match in phony_pattern.finditer(content):
                targets = match.group(1).strip().split()
                phony_targets.update(targets)

            # --- Phase E: Extract include directives ---
            include_pattern = re.compile(r'^-?include\s+(.+)', re.MULTILINE)
            for match in include_pattern.finditer(content):
                include_file = match.group(1).strip()
                ctx.commands.append(CommandInfo(
                    name=f"include {include_file}",
                    command=f"include {include_file}",
                    source='Makefile',
                    category='config',
                ))

            # --- Phase E: Extract variable assignments ---
            var_pattern = re.compile(
                r'^([A-Z_][A-Z0-9_]*)\s*(?::=|\?=|\+=|=)\s*(.+?)$',
                re.MULTILINE,
            )
            makefile_vars: dict = {}
            for match in var_pattern.finditer(content):
                var_name = match.group(1)
                var_value = match.group(2).strip()
                makefile_vars[var_name] = var_value

            # Store significant vars as metadata in a synthetic command entry
            if makefile_vars:
                sig_vars = {k: v for k, v in makefile_vars.items()
                            if k not in ('SHELL', 'MAKEFLAGS') and len(v) < 120}
                if sig_vars:
                    var_summary = ', '.join(
                        f"{k}={v[:40]}" for k, v in list(sig_vars.items())[:8]
                    )
                    ctx.commands.append(CommandInfo(
                        name="Makefile vars",
                        command=var_summary,
                        source='Makefile',
                        category='config',
                    ))

            # --- Extract targets with prerequisites ---
            target_pattern = re.compile(
                r'^([a-zA-Z][\w.-]*)\s*:\s*([^=\n]*)',
                re.MULTILINE,
            )

            for match in target_pattern.finditer(content):
                target = match.group(1)
                prerequisites = match.group(2).strip()

                if target.upper() == target and '_' not in target:
                    continue  # Skip all-caps single-word (likely variables)

                # Try to get the first command line(s) after the target
                rest = content[match.end():]
                cmd_lines = []
                for cmd_line in rest.split('\n')[1:5]:
                    if cmd_line.startswith('\t') or cmd_line.startswith('    '):
                        cmd_lines.append(cmd_line.strip())
                    elif cmd_line.strip() == '':
                        continue
                    else:
                        break

                command = ' && '.join(cmd_lines[:2]) if cmd_lines else target

                # Phase E: Annotate with prerequisites and phony status
                name_parts = [f"make {target}"]
                if target in phony_targets:
                    name_parts.append("[phony]")
                if prerequisites:
                    deps = prerequisites.split()[:4]  # Limit to 4 deps
                    if deps:
                        name_parts.append(f"← {' '.join(deps)}")

                ctx.commands.append(CommandInfo(
                    name=' '.join(name_parts),
                    command=command,
                    source='Makefile',
                    category=_categorize_command(target),
                ))
        except Exception:
            pass

    def _extract_shell_scripts(self, ctx: RunbookContext):
        """Extract shell script (.sh) files as run commands.

        Many Python projects and services use shell scripts for startup,
        install, and deployment instead of package.json or Makefile.
        """
        if not self._project_root:
            return

        # Only look for .sh files at the project root level (not recursively)
        sh_files = list(self._project_root.glob('*.sh'))
        if not sh_files:
            return

        for sh_file in sorted(sh_files):
            name = sh_file.stem  # e.g., 'start', 'install_ml_deps'
            try:
                content = sh_file.read_text(encoding='utf-8')
                # Extract the first meaningful line (skip shebang, comments, blank lines)
                first_cmd = ''
                for line in content.split('\n'):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and not stripped.startswith('set '):
                        first_cmd = stripped[:120]
                        break

                ctx.commands.append(CommandInfo(
                    name=name,
                    command=f"./{sh_file.name}" + (f"  # {first_cmd}" if first_cmd else ''),
                    source='shell-script',
                    category=_categorize_command(name),
                ))
            except Exception:
                ctx.commands.append(CommandInfo(
                    name=name,
                    command=f"./{sh_file.name}",
                    source='shell-script',
                    category=_categorize_command(name),
                ))

    def _extract_dockerfile(self, ctx: RunbookContext):
        """Extract Docker info from Dockerfile"""
        if not self._project_root:
            return

        dockerfile = self._project_root / 'Dockerfile'
        if not dockerfile.exists():
            return

        try:
            content = dockerfile.read_text(encoding='utf-8')
            docker = DockerInfo()

            # Extract FROM (base image + stages)
            from_pattern = re.compile(r'^FROM\s+(\S+)(?:\s+[Aa][Ss]\s+(\S+))?', re.MULTILINE)
            for match in from_pattern.finditer(content):
                image = match.group(1)
                stage = match.group(2)
                if not docker.base_image:
                    docker.base_image = image
                if stage:
                    docker.stages.append(stage)

            # Extract EXPOSE
            expose_pattern = re.compile(r'^EXPOSE\s+(.+)', re.MULTILINE)
            for match in expose_pattern.finditer(content):
                ports = match.group(1).strip().split()
                docker.ports.extend(ports)

            # Extract CMD
            cmd_pattern = re.compile(r'^CMD\s+(.+)', re.MULTILINE)
            cmd_match = cmd_pattern.search(content)
            if cmd_match:
                docker.cmd = cmd_match.group(1).strip()

            # Extract ENTRYPOINT
            ep_pattern = re.compile(r'^ENTRYPOINT\s+(.+)', re.MULTILINE)
            ep_match = ep_pattern.search(content)
            if ep_match:
                docker.entrypoint = ep_match.group(1).strip()

            # Extract VOLUME
            vol_pattern = re.compile(r'^VOLUME\s+(.+)', re.MULTILINE)
            for match in vol_pattern.finditer(content):
                docker.volumes.append(match.group(1).strip())

            if docker.base_image:
                ctx.docker = docker
        except Exception:
            pass

    # ========================================================
    # G-02: CI/CD extraction
    # ========================================================

    def _extract_github_actions(self, ctx: RunbookContext):
        """Extract GitHub Actions workflow files"""
        if not self._project_root:
            return

        workflows_dir = self._project_root / '.github' / 'workflows'
        if not workflows_dir.is_dir():
            return

        for yml_file in workflows_dir.glob('*.yml'):
            self._parse_github_workflow(yml_file, ctx)
        for yaml_file in workflows_dir.glob('*.yaml'):
            self._parse_github_workflow(yaml_file, ctx)

    def _parse_github_workflow(self, path: Path, ctx: RunbookContext):
        """Parse a single GitHub Actions workflow file"""
        try:
            content = path.read_text(encoding='utf-8')

            # Extract workflow name
            name_match = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
            name = name_match.group(1) if name_match else path.stem

            # Extract triggers
            triggers: List[str] = []
            # Look for "on:" section
            on_match = re.search(r'^on:\s*(.+)?$', content, re.MULTILINE)
            if on_match:
                rest = on_match.group(1)
                if rest and rest.strip():
                    # Inline: on: push  or  on: [push, pull_request]
                    triggers.extend(re.findall(r'[a-z_]+', rest))
                else:
                    # Multi-line on: section
                    on_start = on_match.end()
                    remaining = content[on_start:]
                    for line in remaining.split('\n'):
                        if line and not line[0].isspace() and line.strip():
                            break  # Next top-level key
                        trigger = line.strip().rstrip(':')
                        if trigger and not trigger.startswith('#') and not trigger.startswith('-'):
                            triggers.append(trigger)

            # Extract job names
            jobs: List[str] = []
            jobs_section = re.search(r'^jobs:\s*$', content, re.MULTILINE)
            if jobs_section:
                remaining = content[jobs_section.end():]
                # Jobs are defined at 2-space indent
                for line in remaining.split('\n'):
                    match = re.match(r'^  ([a-zA-Z][\w-]*):\s*$', line)
                    if match:
                        jobs.append(match.group(1))

            rel_path = str(path.relative_to(self._project_root))
            ctx.pipelines.append(CICDPipeline(
                name=name,
                platform='github-actions',
                file_path=rel_path,
                triggers=triggers[:5],
                jobs=jobs[:10],
            ))
        except Exception:
            pass

    def _extract_gitlab_ci(self, ctx: RunbookContext):
        """Extract GitLab CI config"""
        if not self._project_root:
            return

        gitlab_ci = self._project_root / '.gitlab-ci.yml'
        if not gitlab_ci.exists():
            return

        try:
            content = gitlab_ci.read_text(encoding='utf-8')

            # Extract stages
            stages: List[str] = []
            stages_match = re.search(r'^stages:\s*$', content, re.MULTILINE)
            if stages_match:
                remaining = content[stages_match.end():]
                for line in remaining.split('\n'):
                    m = re.match(r'^\s+-\s+(\S+)', line)
                    if m:
                        stages.append(m.group(1))
                    elif line.strip() and not line.startswith(' '):
                        break

            # Extract job names (top-level keys that aren't reserved)
            reserved = {'stages', 'variables', 'image', 'services', 'before_script',
                        'after_script', 'cache', 'include', 'default', 'workflow'}
            jobs: List[str] = []
            for match in re.finditer(r'^([a-zA-Z][\w:-]*):\s*$', content, re.MULTILINE):
                job_name = match.group(1)
                if job_name.lower() not in reserved:
                    jobs.append(job_name)

            ctx.pipelines.append(CICDPipeline(
                name='GitLab CI',
                platform='gitlab-ci',
                file_path='.gitlab-ci.yml',
                triggers=stages,
                jobs=jobs[:10],
            ))
        except Exception:
            pass

    def _extract_other_ci(self, ctx: RunbookContext):
        """Extract Jenkins, Bitbucket, CircleCI configs"""
        if not self._project_root:
            return

        # Jenkinsfile
        jenkinsfile = self._project_root / 'Jenkinsfile'
        if jenkinsfile.exists():
            try:
                content = jenkinsfile.read_text(encoding='utf-8')
                stages = re.findall(r"stage\s*\(\s*['\"](.+?)['\"]\s*\)", content)
                ctx.pipelines.append(CICDPipeline(
                    name='Jenkinsfile',
                    platform='jenkins',
                    file_path='Jenkinsfile',
                    triggers=['scm'],
                    jobs=stages[:10],
                ))
            except Exception:
                pass

        # Bitbucket
        bitbucket = self._project_root / 'bitbucket-pipelines.yml'
        if bitbucket.exists():
            ctx.pipelines.append(CICDPipeline(
                name='Bitbucket Pipelines',
                platform='bitbucket',
                file_path='bitbucket-pipelines.yml',
                triggers=['push'],
                jobs=[],
            ))

        # CircleCI
        circleci = self._project_root / '.circleci' / 'config.yml'
        if circleci.exists():
            try:
                content = circleci.read_text(encoding='utf-8')
                jobs = re.findall(r'^  ([a-zA-Z][\w-]*):\s*$', content, re.MULTILINE)
                ctx.pipelines.append(CICDPipeline(
                    name='CircleCI',
                    platform='circleci',
                    file_path='.circleci/config.yml',
                    triggers=['push'],
                    jobs=jobs[:10],
                ))
            except Exception:
                pass

    # ========================================================
    # G-03: Environment extraction
    # ========================================================

    def _extract_env_example(self, ctx: RunbookContext):
        """Extract environment variables from .env.example or .env.sample"""
        if not self._project_root:
            return

        env_files = ['.env.example', '.env.sample', '.env.template']
        for env_name in env_files:
            env_path = self._project_root / env_name
            if not env_path.exists():
                continue

            try:
                content = env_path.read_text(encoding='utf-8')
                last_comment = ''

                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        last_comment = ''
                        continue
                    if line.startswith('#'):
                        last_comment = line.lstrip('# ').strip()
                        continue

                    # Parse KEY=VALUE
                    match = re.match(r'^([A-Z][A-Z0-9_]*)\s*=\s*(.*)', line)
                    if match:
                        ctx.env_variables.append(EnvVariable(
                            name=match.group(1),
                            default_value=match.group(2).strip().strip('"').strip("'"),
                            comment=last_comment,
                        ))
                        last_comment = ''
            except Exception:
                pass
            break  # Only process first found

    def _extract_source_env_vars(self, ctx: RunbookContext):
        """
        v4.9: Extract environment variables from source code patterns.
        Generic — works for ANY language:
          - Go:     os.Getenv("VAR"), os.LookupEnv("VAR")
          - Python: os.environ["VAR"], os.environ.get("VAR"), os.getenv("VAR")
          - Node:   process.env.VAR, process.env["VAR"]
          - Rust:   env::var("VAR"), std::env::var("VAR")
          - Java:   System.getenv("VAR")
          - Ruby:   ENV["VAR"], ENV.fetch("VAR")
          - PHP:    getenv("VAR"), $_ENV["VAR"]
          - C#:     Environment.GetEnvironmentVariable("VAR")
        Only extracts vars not already found in .env.example.
        """
        if not self._project_root:
            return

        # Language-specific env var patterns (compiled once)
        ENV_PATTERNS = [
            # Go: os.Getenv("VAR"), os.LookupEnv("VAR")
            re.compile(r'os\.(?:Getenv|LookupEnv)\s*\(\s*"([A-Z][A-Z0-9_]{2,})"'),
            # Python: os.environ["VAR"], os.environ.get("VAR", ...), os.getenv("VAR", ...)
            re.compile(r'os\.environ(?:\.get)?\s*[\[\(]\s*["\']([A-Z][A-Z0-9_]{2,})["\']'),
            re.compile(r'os\.getenv\s*\(\s*["\']([A-Z][A-Z0-9_]{2,})["\']'),
            # Node/TypeScript: process.env.VAR, process.env["VAR"]
            re.compile(r'process\.env\.([A-Z][A-Z0-9_]{2,})'),
            re.compile(r'process\.env\[\s*["\']([A-Z][A-Z0-9_]{2,})["\']'),
            # Rust: env::var("VAR"), std::env::var("VAR")
            re.compile(r'env::var(?:_os)?\s*\(\s*"([A-Z][A-Z0-9_]{2,})"'),
            # Java: System.getenv("VAR")
            re.compile(r'System\.getenv\s*\(\s*"([A-Z][A-Z0-9_]{2,})"'),
            # Ruby: ENV["VAR"], ENV.fetch("VAR")
            re.compile(r'ENV\s*[\[\.](?:fetch\s*\(\s*)?["\']([A-Z][A-Z0-9_]{2,})["\']'),
            # PHP: getenv("VAR"), $_ENV["VAR"]
            re.compile(r'(?:getenv|\$_ENV)\s*[\[\(]\s*["\']([A-Z][A-Z0-9_]{2,})["\']'),
            # C#: Environment.GetEnvironmentVariable("VAR")
            re.compile(r'Environment\.GetEnvironmentVariable\s*\(\s*"([A-Z][A-Z0-9_]{2,})"'),
        ]

        SOURCE_EXTENSIONS = {
            '.go', '.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.java',
            '.rb', '.cs', '.php', '.kt', '.scala', '.ex', '.exs', '.swift',
        }

        # Collect names already known from .env.example
        known_names = {v.name for v in ctx.env_variables}
        found_vars: Dict[str, str] = {}  # name -> file_path (first occurrence)

        # Common placeholder names used in docs/comments — not real env vars
        PLACEHOLDER_NAMES = {
            'VAR', 'YOUR_VAR', 'MY_VAR', 'ENV_VAR', 'SOME_VAR',
            'VARIABLE', 'KEY', 'VALUE', 'YOUR_KEY', 'YOUR_VALUE',
            'API_KEY', 'SECRET', 'TOKEN',  # too generic without context
            'XXX', 'TODO', 'FIXME', 'PLACEHOLDER',
        }

        # Walk source files (limit depth and file count to avoid slowness)
        files_checked = 0
        max_files = 500

        try:
            for f in self._project_root.rglob('*'):
                if files_checked >= max_files:
                    break
                if not f.is_file() or f.suffix not in SOURCE_EXTENSIONS:
                    continue
                # Skip vendor/node_modules/build dirs
                rel = str(f.relative_to(self._project_root))
                if any(skip in rel for skip in (
                    'node_modules', 'vendor', '.git', '__pycache__',
                    'dist/', 'build/', '.venv/', 'venv/',
                )):
                    continue

                files_checked += 1
                try:
                    content = f.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 200_000:  # Skip very large files
                        continue
                    for pattern in ENV_PATTERNS:
                        for match in pattern.finditer(content):
                            var_name = match.group(1)
                            if (var_name not in known_names
                                    and var_name not in found_vars
                                    and var_name not in PLACEHOLDER_NAMES):
                                found_vars[var_name] = rel
                except Exception:
                    continue
        except Exception:
            pass

        # Add discovered env vars (sorted by name, limit to 30)
        for var_name in sorted(found_vars)[:30]:
            ctx.env_variables.append(EnvVariable(
                name=var_name,
                default_value='',
                comment=f'Used in {found_vars[var_name]}',
                required=False,  # Can't determine from source scan
            ))

    def _extract_docker_compose(self, ctx: RunbookContext):
        """Extract services from docker-compose.yml"""
        if not self._project_root:
            return

        compose_names = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
        compose_path = None
        for name in compose_names:
            candidate = self._project_root / name
            if candidate.exists():
                compose_path = candidate
                break

        if not compose_path:
            return

        try:
            content = compose_path.read_text(encoding='utf-8')
            compose = ComposeInfo()

            # Find services section
            services_match = re.search(r'^services:\s*$', content, re.MULTILINE)
            if not services_match:
                return

            remaining = content[services_match.end():]

            # Parse services at 2-space indent
            current_service: Optional[ComposeService] = None

            for line in remaining.split('\n'):
                # New top-level section ends services
                if line and not line[0].isspace() and line.strip().endswith(':'):
                    break

                # Service name (2-space indent)
                svc_match = re.match(r'^  ([a-zA-Z][\w-]*):\s*$', line)
                if svc_match:
                    if current_service:
                        compose.services.append(current_service)
                    current_service = ComposeService(name=svc_match.group(1))
                    continue

                if not current_service:
                    continue

                stripped = line.strip()

                # Image
                img_match = re.match(r'image:\s*(.+)', stripped)
                if img_match:
                    current_service.image = img_match.group(1).strip()

                # Build
                build_match = re.match(r'build:\s*(.+)', stripped)
                if build_match:
                    current_service.build = build_match.group(1).strip()

                # Ports
                port_match = re.match(r'-\s*["\']?(\d+:\d+)["\']?', stripped)
                if port_match and 'ports:' in content[:content.find(line)]:
                    current_service.ports.append(port_match.group(1))

                # Depends on
                dep_match = re.match(r'-\s*(\w[\w-]*)', stripped)
                if dep_match:
                    # This is a list item, could be depends_on or ports
                    pass

            if current_service:
                compose.services.append(current_service)

            # Extract top-level networks
            networks_match = re.search(r'^networks:\s*$', content, re.MULTILINE)
            if networks_match:
                net_remaining = content[networks_match.end():]
                for line in net_remaining.split('\n'):
                    if line and not line[0].isspace() and line.strip():
                        break
                    net_match = re.match(r'^  ([a-zA-Z][\w-]*):', line)
                    if net_match:
                        compose.networks.append(net_match.group(1))

            # Extract top-level volumes
            volumes_match = re.search(r'^volumes:\s*$', content, re.MULTILINE)
            if volumes_match:
                vol_remaining = content[volumes_match.end():]
                for line in vol_remaining.split('\n'):
                    if line and not line[0].isspace() and line.strip():
                        break
                    vol_match = re.match(r'^  ([a-zA-Z][\w-]*):', line)
                    if vol_match:
                        compose.volumes.append(vol_match.group(1))

            if compose.services:
                ctx.compose = compose
        except Exception:
            pass

    def _extract_readme_setup(self, ctx: RunbookContext):
        """Extract installation/setup steps from README"""
        if not self._project_root:
            return

        for readme_name in ['README.md', 'readme.md', 'README.rst']:
            readme_path = self._project_root / readme_name
            if not readme_path.exists():
                continue

            try:
                content = readme_path.read_text(encoding='utf-8')

                # Look for installation/setup/getting started sections
                section_patterns = [
                    r'#+\s*(?:Installation|Setup|Getting\s+Started|Quick\s+Start|Prerequisites)',
                    r'#+\s*(?:How\s+to\s+[Rr]un|Running|Development)',
                ]

                for pattern in section_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        # Extract content until next heading of same or higher level
                        heading_level = content[match.start():match.end()].count('#')
                        rest = content[match.end():]

                        # Find next heading of same or higher level
                        next_heading = re.search(
                            r'^#{1,' + str(heading_level) + r'}\s',
                            rest, re.MULTILINE
                        )
                        section = rest[:next_heading.start()] if next_heading else rest[:1000]

                        # Extract code blocks as install steps
                        code_blocks = re.findall(r'```(?:bash|sh|shell)?\n(.+?)```',
                                                 section, re.DOTALL)
                        for block in code_blocks[:5]:
                            for line in block.strip().split('\n'):
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    ctx.install_steps.append(line)

                        # If no code blocks, extract lines that look like commands
                        if not code_blocks:
                            for line in section.split('\n'):
                                line = line.strip()
                                if line.startswith('$ ') or line.startswith('> '):
                                    ctx.install_steps.append(line.lstrip('$ > '))

            except Exception:
                pass
            break  # Only process first README

    # ========================================================
    # v4.9: Developer Guide Context
    # ========================================================

    def _extract_contributing(self, ctx: RunbookContext):
        """Extract CONTRIBUTING.md for developer onboarding context."""
        if not self._project_root:
            return

        for name in ['CONTRIBUTING.md', '.github/CONTRIBUTING.md', 'docs/CONTRIBUTING.md',
                      'contributing.md', 'CONTRIBUTE.md']:
            p = self._project_root / name
            if not p.exists():
                continue

            try:
                content = p.read_text(encoding='utf-8', errors='ignore')
                prereqs = []
                setup_steps = []

                for line in content.splitlines():
                    stripped = line.strip()
                    # Extract prerequisites
                    if re.search(r'prerequisit|require|install|need|depend', stripped, re.I) and len(stripped) < 200:
                        prereqs.append(stripped[:120])
                    # Extract numbered/bulleted setup steps
                    if re.match(r'^\d+\.?\s+|^-\s+|^\*\s+', stripped) and len(stripped) > 10:
                        setup_steps.append(stripped[:120])

                ctx.contributing_guide = {
                    'path': name,
                    'prerequisites': prereqs[:10],
                    'setup_steps': setup_steps[:15],
                }
            except Exception:
                ctx.contributing_guide = {'path': name}
            break

    def _extract_examples(self, ctx: RunbookContext):
        """Extract examples/ directory listing for developer reference."""
        if not self._project_root:
            return

        for examples_dir in ['examples', 'example', 'docs/examples', 'samples', '_examples']:
            p = self._project_root / examples_dir
            if not p.is_dir():
                continue

            for f in sorted(p.rglob('*'))[:15]:
                if f.is_file() and not f.name.startswith('.'):
                    # Infer description from filename
                    desc = f.stem.replace('_', ' ').replace('-', ' ')
                    ctx.examples.append({
                        'path': str(f.relative_to(self._project_root)),
                        'description': desc,
                    })
            break

    def _extract_version_requirements(self, ctx: RunbookContext):
        """Extract version requirements from go.mod, package.json engines, pyproject.toml."""
        if not self._project_root:
            return

        # Go version from go.mod
        go_mod = self._project_root / 'go.mod'
        if go_mod.exists():
            try:
                content = go_mod.read_text(encoding='utf-8')
                m = re.search(r'^go\s+(\S+)', content, re.M)
                if m:
                    ctx.version_requirements.append({'tool': 'Go', 'version': m.group(1)})
            except Exception:
                pass

        # Node version from package.json engines
        for pkg_json_path in [self._project_root / 'package.json']:
            if not pkg_json_path.exists():
                continue
            try:
                import json
                with open(pkg_json_path, encoding='utf-8') as f:
                    data = json.load(f)
                for engine, ver in data.get('engines', {}).items():
                    ctx.version_requirements.append({'tool': engine, 'version': str(ver)})
            except Exception:
                pass

        # Python version from pyproject.toml
        pyproject = self._project_root / 'pyproject.toml'
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding='utf-8')
                m = re.search(r'requires-python\s*=\s*["\'](.+?)["\']', content)
                if m:
                    ctx.version_requirements.append({'tool': 'Python', 'version': m.group(1)})
            except Exception:
                pass

        # Rust version from rust-toolchain.toml
        rust_toolchain = self._project_root / 'rust-toolchain.toml'
        if rust_toolchain.exists():
            try:
                content = rust_toolchain.read_text(encoding='utf-8')
                m = re.search(r'channel\s*=\s*["\'](.+?)["\']', content)
                if m:
                    ctx.version_requirements.append({'tool': 'Rust', 'version': m.group(1)})
            except Exception:
                pass

    def _extract_license(self, ctx: RunbookContext):
        """Extract license type from LICENSE file."""
        if not self._project_root:
            return

        for name in ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'license']:
            p = self._project_root / name
            if not p.exists():
                continue
            try:
                first_line = p.read_text(encoding='utf-8', errors='ignore').split('\n')[0].strip()
                ctx.license_info = first_line[:80] if first_line else name
            except Exception:
                ctx.license_info = name
            break
