"""
CodeTrellis CI/CD Extractor
======================

Phase C (WS-6 / G-15): Enhanced standalone CI/CD configuration parser.

Complements RunbookExtractor (Phase A) with deeper analysis of CI/CD configs:
- GitHub Actions workflows (.github/workflows/*.yml)
- GitLab CI (.gitlab-ci.yml)
- Jenkinsfile
- CircleCI (.circleci/config.yml)
- Bitbucket Pipelines (bitbucket-pipelines.yml)

Extracts:
- Pipeline names and triggers
- Job/stage definitions with commands
- Environment variables and secrets
- Matrix build configurations
- Deployment targets
- Test commands

Output feeds into:
- [INFRASTRUCTURE] section in matrix.prompt
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CICDJob:
    """A single job/stage in a CI/CD pipeline"""
    name: str
    runs_on: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    condition: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"name": self.name}
        if self.runs_on:
            result["runs_on"] = self.runs_on
        if self.steps:
            result["steps"] = self.steps
        if self.needs:
            result["needs"] = self.needs
        if self.env_vars:
            result["env"] = self.env_vars
        if self.condition:
            result["condition"] = self.condition
        return result


@dataclass
class CICDPipelineInfo:
    """A complete CI/CD pipeline definition"""
    name: str
    platform: str  # github-actions, gitlab-ci, jenkins, circleci, bitbucket
    file_path: str
    triggers: List[str] = field(default_factory=list)
    jobs: List[CICDJob] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)
    secrets_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "platform": self.platform,
            "file": self.file_path,
            "triggers": self.triggers,
            "jobs": [j.to_dict() for j in self.jobs],
            "env": self.env_vars,
            "secrets": self.secrets_used,
        }


class CICDExtractor:
    """
    Extracts CI/CD pipeline definitions from a project.

    Used by: scanner.py → compressor.py → [INFRASTRUCTURE] section
    """

    def extract(self, root_path: str) -> List[Dict[str, Any]]:
        """
        Extract all CI/CD pipeline information.

        Returns:
            List of pipeline info dicts
        """
        root = Path(root_path)
        pipelines: List[Dict[str, Any]] = []

        # GitHub Actions
        gh_workflows = root / '.github' / 'workflows'
        if gh_workflows.exists():
            for wf_file in sorted(gh_workflows.glob('*.yml')) + sorted(gh_workflows.glob('*.yaml')):
                try:
                    info = self._parse_github_actions(wf_file, root)
                    if info:
                        pipelines.append(info.to_dict())
                except Exception:
                    pass

        # GitLab CI
        gitlab_ci = root / '.gitlab-ci.yml'
        if gitlab_ci.exists():
            try:
                info = self._parse_gitlab_ci(gitlab_ci, root)
                if info:
                    pipelines.append(info.to_dict())
            except Exception:
                pass

        # Jenkinsfile
        jenkinsfile = root / 'Jenkinsfile'
        if jenkinsfile.exists():
            try:
                info = self._parse_jenkinsfile(jenkinsfile, root)
                if info:
                    pipelines.append(info.to_dict())
            except Exception:
                pass

        # CircleCI
        circleci = root / '.circleci' / 'config.yml'
        if circleci.exists():
            try:
                info = self._parse_circleci(circleci, root)
                if info:
                    pipelines.append(info.to_dict())
            except Exception:
                pass

        # Bitbucket Pipelines
        bitbucket = root / 'bitbucket-pipelines.yml'
        if bitbucket.exists():
            try:
                info = self._parse_bitbucket(bitbucket, root)
                if info:
                    pipelines.append(info.to_dict())
            except Exception:
                pass

        return pipelines

    def _parse_github_actions(self, file_path: Path, root: Path) -> Optional[CICDPipelineInfo]:
        """Parse a GitHub Actions workflow YAML."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        # Try YAML parsing
        data = self._safe_yaml_load(content)
        if not data or not isinstance(data, dict):
            return None

        name = data.get('name', file_path.stem)
        info = CICDPipelineInfo(
            name=str(name),
            platform='github-actions',
            file_path=rel_path,
        )

        # Extract triggers
        on_block = data.get('on', data.get(True, {}))  # YAML parses 'on' as True
        if isinstance(on_block, dict):
            info.triggers = list(on_block.keys())
        elif isinstance(on_block, list):
            info.triggers = on_block
        elif isinstance(on_block, str):
            info.triggers = [on_block]

        # Extract environment variables
        env_block = data.get('env', {})
        if isinstance(env_block, dict):
            info.env_vars = list(env_block.keys())

        # Extract jobs
        jobs_block = data.get('jobs', {})
        if isinstance(jobs_block, dict):
            for job_name, job_config in jobs_block.items():
                if not isinstance(job_config, dict):
                    continue

                job = CICDJob(name=job_name)
                job.runs_on = str(job_config.get('runs-on', ''))

                # Extract needs (dependencies)
                needs = job_config.get('needs', [])
                if isinstance(needs, str):
                    job.needs = [needs]
                elif isinstance(needs, list):
                    job.needs = [str(n) for n in needs]

                # Extract condition
                cond = job_config.get('if')
                if cond:
                    job.condition = str(cond)[:80]

                # Extract step names/uses
                steps = job_config.get('steps', [])
                if isinstance(steps, list):
                    for step in steps:
                        if isinstance(step, dict):
                            step_name = step.get('name', '')
                            step_uses = step.get('uses', '')
                            step_run = step.get('run', '')

                            if step_uses:
                                # Action reference: actions/checkout@v4
                                action_short = str(step_uses).split('@')[0].split('/')[-1]
                                job.steps.append(f"use:{action_short}")
                            elif step_run:
                                # Run command: first meaningful line
                                cmd = str(step_run).strip().split('\n')[0][:60]
                                job.steps.append(f"run:{cmd}")
                            elif step_name:
                                job.steps.append(str(step_name)[:60])

                # Extract job environment
                job_env = job_config.get('env', {})
                if isinstance(job_env, dict):
                    job.env_vars = list(job_env.keys())

                # Extract services
                job_services = job_config.get('services', {})
                if isinstance(job_services, dict):
                    job.services = list(job_services.keys())

                info.jobs.append(job)

        # Extract secrets used across the file
        secrets = set(re.findall(r'\$\{\{\s*secrets\.(\w+)\s*\}\}', content))
        info.secrets_used = sorted(secrets)

        return info

    def _parse_gitlab_ci(self, file_path: Path, root: Path) -> Optional[CICDPipelineInfo]:
        """Parse a .gitlab-ci.yml file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        data = self._safe_yaml_load(content)
        if not data or not isinstance(data, dict):
            return None

        info = CICDPipelineInfo(
            name='GitLab CI',
            platform='gitlab-ci',
            file_path=rel_path,
        )

        # Reserved keys that are not stages/jobs
        reserved = {'image', 'stages', 'variables', 'before_script', 'after_script',
                     'cache', 'include', 'default', 'workflow', 'services'}

        # Stages
        stages = data.get('stages', [])
        if isinstance(stages, list):
            info.triggers = [f"stage:{s}" for s in stages]

        # Variables
        variables = data.get('variables', {})
        if isinstance(variables, dict):
            info.env_vars = list(variables.keys())

        # Jobs (everything that's not a reserved key)
        for key, value in data.items():
            if key in reserved or key.startswith('.'):
                continue
            if isinstance(value, dict):
                job = CICDJob(name=key)
                stage = value.get('stage', '')
                if stage:
                    job.needs = [f"stage:{stage}"]
                script = value.get('script', [])
                if isinstance(script, list):
                    job.steps = [str(s)[:60] for s in script[:10]]
                info.jobs.append(job)

        return info if info.jobs else None

    def _parse_jenkinsfile(self, file_path: Path, root: Path) -> Optional[CICDPipelineInfo]:
        """Parse a Jenkinsfile (Groovy-based)."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        info = CICDPipelineInfo(
            name='Jenkins Pipeline',
            platform='jenkins',
            file_path=rel_path,
        )

        # Extract stages
        stage_matches = re.findall(r"stage\s*\(\s*'([^']+)'\s*\)", content)
        if not stage_matches:
            stage_matches = re.findall(r'stage\s*\(\s*"([^"]+)"\s*\)', content)

        for stage_name in stage_matches:
            info.jobs.append(CICDJob(name=stage_name))

        # Extract triggers
        if 'cron' in content:
            info.triggers.append('cron')
        if 'pollSCM' in content:
            info.triggers.append('pollSCM')
        if 'upstream' in content:
            info.triggers.append('upstream')

        # Extract environment variables
        env_matches = re.findall(r'(\w+)\s*=\s*credentials\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        info.secrets_used = [m[1] for m in env_matches]

        return info if info.jobs else None

    def _parse_circleci(self, file_path: Path, root: Path) -> Optional[CICDPipelineInfo]:
        """Parse a CircleCI config.yml."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        data = self._safe_yaml_load(content)
        if not data or not isinstance(data, dict):
            return None

        info = CICDPipelineInfo(
            name='CircleCI',
            platform='circleci',
            file_path=rel_path,
        )

        # Jobs
        jobs = data.get('jobs', {})
        if isinstance(jobs, dict):
            for name, config in jobs.items():
                if isinstance(config, dict):
                    job = CICDJob(name=name)
                    docker = config.get('docker', [])
                    if isinstance(docker, list) and docker:
                        first = docker[0]
                        if isinstance(first, dict):
                            job.runs_on = first.get('image', '')
                    steps = config.get('steps', [])
                    if isinstance(steps, list):
                        for step in steps:
                            if isinstance(step, str):
                                job.steps.append(step)
                            elif isinstance(step, dict):
                                for k in step:
                                    job.steps.append(str(k))
                    info.jobs.append(job)

        # Workflows
        workflows = data.get('workflows', {})
        if isinstance(workflows, dict):
            info.triggers = list(workflows.keys())

        return info if info.jobs else None

    def _parse_bitbucket(self, file_path: Path, root: Path) -> Optional[CICDPipelineInfo]:
        """Parse a bitbucket-pipelines.yml."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        data = self._safe_yaml_load(content)
        if not data or not isinstance(data, dict):
            return None

        info = CICDPipelineInfo(
            name='Bitbucket Pipelines',
            platform='bitbucket',
            file_path=rel_path,
        )

        # Extract pipeline steps
        pipelines = data.get('pipelines', {})
        if isinstance(pipelines, dict):
            for trigger, config in pipelines.items():
                info.triggers.append(str(trigger))
                if isinstance(config, dict):
                    for branch, steps in config.items():
                        if isinstance(steps, list):
                            job = CICDJob(name=f"{trigger}:{branch}")
                            for step in steps:
                                if isinstance(step, dict):
                                    step_info = step.get('step', {})
                                    if isinstance(step_info, dict):
                                        name = step_info.get('name', '')
                                        if name:
                                            job.steps.append(str(name)[:60])
                            if job.steps:
                                info.jobs.append(job)

        return info if info.jobs else None

    def _safe_yaml_load(self, content: str) -> Optional[Dict]:
        """Try to load YAML safely, return None on failure."""
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            return self._basic_yaml_parse(content)
        except Exception:
            return None

    def _basic_yaml_parse(self, content: str) -> Optional[Dict]:
        """Minimal YAML-like parser for when PyYAML is unavailable."""
        result: Dict[str, Any] = {}
        current_key = None

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            indent = len(line) - len(line.lstrip())

            if indent == 0 and ':' in stripped:
                key = stripped.split(':')[0].strip()
                val = stripped.split(':', 1)[1].strip()
                current_key = key
                if val:
                    result[key] = val
                else:
                    result[key] = {}

        return result if result else None
