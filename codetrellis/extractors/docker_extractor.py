"""
CodeTrellis Docker Extractor
=======================

Phase C (WS-6 / G-13): Extracts infrastructure context from Dockerfiles
and docker-compose.yml files.

Extracts:
- Dockerfile: FROM (base image/runtime), EXPOSE (ports), CMD/ENTRYPOINT,
  multi-stage builds, HEALTHCHECK, environment defaults, WORKDIR
- docker-compose.yml: Services, ports, depends_on, volumes, networks,
  environment variables, health checks

Output feeds into:
- [INFRASTRUCTURE] section in matrix.prompt
- [SERVICE_MAP] section (depends_on relationships)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from codetrellis.file_classifier import GitignoreFilter


@dataclass
class DockerStage:
    """A single stage in a multi-stage Dockerfile build"""
    name: Optional[str]
    base_image: str
    commands: List[str] = field(default_factory=list)
    expose_ports: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    workdir: Optional[str] = None
    cmd: Optional[str] = None
    entrypoint: Optional[str] = None
    healthcheck: Optional[str] = None
    copy_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "base_image": self.base_image,
        }
        if self.name:
            result["name"] = self.name
        if self.expose_ports:
            result["ports"] = self.expose_ports
        if self.env_vars:
            result["env"] = self.env_vars
        if self.workdir:
            result["workdir"] = self.workdir
        if self.cmd:
            result["cmd"] = self.cmd
        if self.entrypoint:
            result["entrypoint"] = self.entrypoint
        if self.healthcheck:
            result["healthcheck"] = self.healthcheck
        return result


@dataclass
class DockerfileInfo:
    """Parsed Dockerfile information"""
    file_path: str
    stages: List[DockerStage] = field(default_factory=list)
    is_multistage: bool = False
    final_image: Optional[str] = None
    final_ports: List[str] = field(default_factory=list)
    final_cmd: Optional[str] = None
    final_entrypoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "file": self.file_path,
            "multistage": self.is_multistage,
            "stages": [s.to_dict() for s in self.stages],
        }
        if self.final_image:
            result["final_image"] = self.final_image
        if self.final_ports:
            result["ports"] = self.final_ports
        if self.final_cmd:
            result["cmd"] = self.final_cmd
        if self.final_entrypoint:
            result["entrypoint"] = self.final_entrypoint
        return result


@dataclass
class ComposeServiceInfo:
    """A single service in docker-compose.yml"""
    name: str
    image: Optional[str] = None
    build: Optional[str] = None
    ports: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    environment: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    healthcheck: Optional[str] = None
    command: Optional[str] = None
    restart: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"name": self.name}
        if self.image:
            result["image"] = self.image
        if self.build:
            result["build"] = self.build
        if self.ports:
            result["ports"] = self.ports
        if self.depends_on:
            result["depends_on"] = self.depends_on
        if self.environment:
            result["environment"] = self.environment
        if self.volumes:
            result["volumes"] = self.volumes
        if self.healthcheck:
            result["healthcheck"] = self.healthcheck
        return result


@dataclass
class ComposeFileInfo:
    """Parsed docker-compose.yml information"""
    file_path: str
    services: List[ComposeServiceInfo] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "services": [s.to_dict() for s in self.services],
            "networks": self.networks,
            "volumes": self.volumes,
        }


class DockerExtractor:
    """
    Extracts Docker infrastructure context from a project.

    Parses:
    - Dockerfile / Dockerfile.* files
    - docker-compose.yml / docker-compose.*.yml files

    Used by: scanner.py → compressor.py → [INFRASTRUCTURE] section
    """

    def extract(self, root_path: str) -> Dict[str, Any]:
        """
        Extract all Docker-related information from a project.

        Args:
            root_path: Path to project root

        Returns:
            Dict with 'dockerfiles' and 'compose_files' keys
        """
        root = Path(root_path)
        result: Dict[str, Any] = {
            "dockerfiles": [],
            "compose_files": [],
        }

        # Find and parse Dockerfiles
        for dockerfile in self._find_dockerfiles(root):
            try:
                info = self._parse_dockerfile(dockerfile, root)
                if info:
                    result["dockerfiles"].append(info.to_dict())
            except Exception:
                pass

        # Find and parse docker-compose files
        for compose_file in self._find_compose_files(root):
            try:
                info = self._parse_compose_file(compose_file, root)
                if info:
                    result["compose_files"].append(info.to_dict())
            except Exception:
                pass

        return result

    def _find_dockerfiles(self, root: Path) -> List[Path]:
        """Find all Dockerfiles in the project (excluding _archive, node_modules, and .gitignored paths)."""
        dockerfiles = []
        ignore_dirs = {'node_modules', '.git', '_archive', 'dist', 'build', '__pycache__', '.venv', 'venv'}
        
        # Load gitignore filter to respect .gitignore rules
        gitignore_filter = GitignoreFilter.from_root(root)

        for dirpath, dirnames, filenames in __import__('os').walk(root):
            # Skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            # Check if current directory is gitignored
            rel_dir = str(Path(dirpath).relative_to(root))
            if gitignore_filter.should_ignore(rel_dir):
                dirnames[:] = []  # Stop recursion into this directory
                continue
            
            for f in filenames:
                if f == 'Dockerfile' or f.startswith('Dockerfile.'):
                    file_path = Path(dirpath) / f
                    rel_path = str(file_path.relative_to(root))
                    # Skip if gitignored
                    if not gitignore_filter.should_ignore(rel_path):
                        dockerfiles.append(file_path)
        return dockerfiles

    def _find_compose_files(self, root: Path) -> List[Path]:
        """Find all docker-compose files (excluding _archive, node_modules, and .gitignored paths)."""
        compose_files = []
        ignore_dirs = {'node_modules', '.git', '_archive', 'dist', 'build', '__pycache__', '.venv', 'venv'}
        
        # Load gitignore filter to respect .gitignore rules
        gitignore_filter = GitignoreFilter.from_root(root)

        for dirpath, dirnames, filenames in __import__('os').walk(root):
            # Skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            # Check if current directory is gitignored
            rel_dir = str(Path(dirpath).relative_to(root))
            if gitignore_filter.should_ignore(rel_dir):
                dirnames[:] = []  # Stop recursion into this directory
                continue
            
            for f in filenames:
                if f.startswith('docker-compose') and (f.endswith('.yml') or f.endswith('.yaml')):
                    file_path = Path(dirpath) / f
                    rel_path = str(file_path.relative_to(root))
                    # Skip if gitignored
                    if not gitignore_filter.should_ignore(rel_path):
                        compose_files.append(file_path)
        return compose_files

    def _parse_dockerfile(self, file_path: Path, root: Path) -> Optional[DockerfileInfo]:
        """Parse a single Dockerfile."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        stages: List[DockerStage] = []
        current_stage: Optional[DockerStage] = None

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # FROM instruction → new stage
            from_match = re.match(r'^FROM\s+(\S+)(?:\s+AS\s+(\S+))?', stripped, re.IGNORECASE)
            if from_match:
                if current_stage:
                    stages.append(current_stage)
                current_stage = DockerStage(
                    base_image=from_match.group(1),
                    name=from_match.group(2),
                )
                continue

            if not current_stage:
                continue

            # EXPOSE
            expose_match = re.match(r'^EXPOSE\s+(.+)', stripped, re.IGNORECASE)
            if expose_match:
                ports = re.findall(r'(\d+(?:/\w+)?)', expose_match.group(1))
                current_stage.expose_ports.extend(ports)
                continue

            # ENV
            env_match = re.match(r'^ENV\s+(\w+)[=\s]+(.+)', stripped, re.IGNORECASE)
            if env_match:
                current_stage.env_vars[env_match.group(1)] = env_match.group(2).strip()
                continue

            # WORKDIR
            workdir_match = re.match(r'^WORKDIR\s+(.+)', stripped, re.IGNORECASE)
            if workdir_match:
                current_stage.workdir = workdir_match.group(1).strip()
                continue

            # CMD
            cmd_match = re.match(r'^CMD\s+(.+)', stripped, re.IGNORECASE)
            if cmd_match:
                current_stage.cmd = cmd_match.group(1).strip()
                continue

            # ENTRYPOINT
            entry_match = re.match(r'^ENTRYPOINT\s+(.+)', stripped, re.IGNORECASE)
            if entry_match:
                current_stage.entrypoint = entry_match.group(1).strip()
                continue

            # HEALTHCHECK
            health_match = re.match(r'^HEALTHCHECK\s+(.+)', stripped, re.IGNORECASE)
            if health_match:
                current_stage.healthcheck = health_match.group(1).strip()
                continue

            # COPY (track sources)
            copy_match = re.match(r'^COPY\s+(?:--from=\S+\s+)?(\S+)\s+', stripped, re.IGNORECASE)
            if copy_match:
                current_stage.copy_sources.append(copy_match.group(1))
                continue

            # RUN (track install commands)
            run_match = re.match(r'^RUN\s+(.+)', stripped, re.IGNORECASE)
            if run_match:
                cmd_text = run_match.group(1).strip()
                # Only capture meaningful commands, not continuation lines
                if any(kw in cmd_text for kw in ['install', 'pip', 'npm', 'yarn', 'apk', 'apt']):
                    current_stage.commands.append(cmd_text[:120])

        # Append last stage
        if current_stage:
            stages.append(current_stage)

        if not stages:
            return None

        # Build the info
        info = DockerfileInfo(
            file_path=rel_path,
            stages=stages,
            is_multistage=len(stages) > 1,
        )

        # Final stage info (last stage = the one that runs in production)
        final = stages[-1]
        info.final_image = final.base_image
        info.final_ports = final.expose_ports
        info.final_cmd = final.cmd
        info.final_entrypoint = final.entrypoint

        return info

    def _parse_compose_file(self, file_path: Path, root: Path) -> Optional[ComposeFileInfo]:
        """Parse a docker-compose.yml file using simple YAML-like parsing."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        # Try YAML import
        try:
            import yaml
            data = yaml.safe_load(content)
        except ImportError:
            # Fallback: basic parsing without PyYAML
            data = self._basic_compose_parse(content)
        except Exception:
            data = self._basic_compose_parse(content)

        if not data or not isinstance(data, dict):
            return None

        info = ComposeFileInfo(file_path=rel_path)

        # Parse services
        services_data = data.get('services', {})
        if isinstance(services_data, dict):
            for svc_name, svc_config in services_data.items():
                if not isinstance(svc_config, dict):
                    continue
                svc = ComposeServiceInfo(name=svc_name)
                svc.image = svc_config.get('image')

                build_val = svc_config.get('build')
                if isinstance(build_val, str):
                    svc.build = build_val
                elif isinstance(build_val, dict):
                    svc.build = build_val.get('context', build_val.get('dockerfile', ''))

                ports = svc_config.get('ports', [])
                if isinstance(ports, list):
                    svc.ports = [str(p) for p in ports]

                depends = svc_config.get('depends_on', [])
                if isinstance(depends, list):
                    svc.depends_on = depends
                elif isinstance(depends, dict):
                    svc.depends_on = list(depends.keys())

                env_val = svc_config.get('environment', [])
                if isinstance(env_val, list):
                    svc.environment = [str(e) for e in env_val[:20]]  # Limit
                elif isinstance(env_val, dict):
                    svc.environment = [f"{k}={v}" for k, v in list(env_val.items())[:20]]

                volumes = svc_config.get('volumes', [])
                if isinstance(volumes, list):
                    svc.volumes = [str(v) for v in volumes]

                networks = svc_config.get('networks', [])
                if isinstance(networks, list):
                    svc.networks = [str(n) for n in networks]
                elif isinstance(networks, dict):
                    svc.networks = list(networks.keys())

                command = svc_config.get('command')
                if command:
                    svc.command = str(command)[:100]

                restart = svc_config.get('restart')
                if restart:
                    svc.restart = str(restart)

                healthcheck = svc_config.get('healthcheck')
                if isinstance(healthcheck, dict):
                    test = healthcheck.get('test', '')
                    if isinstance(test, list):
                        test = ' '.join(str(t) for t in test)
                    svc.healthcheck = str(test)[:100]

                info.services.append(svc)

        # Parse top-level networks
        networks_data = data.get('networks', {})
        if isinstance(networks_data, dict):
            info.networks = list(networks_data.keys())

        # Parse top-level volumes
        volumes_data = data.get('volumes', {})
        if isinstance(volumes_data, dict):
            info.volumes = list(volumes_data.keys())

        return info if info.services else None

    def _basic_compose_parse(self, content: str) -> Optional[Dict]:
        """
        Basic YAML-like parser for docker-compose when PyYAML is unavailable.
        Handles simple key: value structures.
        """
        result: Dict[str, Any] = {"services": {}}
        current_service = None
        current_key = None
        indent_level = 0

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Calculate indent
            indent = len(line) - len(line.lstrip())

            # Top-level: services, networks, volumes
            if indent == 0 and ':' in stripped:
                key = stripped.split(':')[0].strip()
                if key == 'services':
                    indent_level = 1
                    current_key = 'services'
                elif key in ('networks', 'volumes'):
                    indent_level = 1
                    current_key = key
                    result[key] = {}
                continue

            # Service name level
            if indent_level == 1 and current_key == 'services' and indent == 2:
                svc_name = stripped.rstrip(':').strip()
                current_service = svc_name
                result['services'][svc_name] = {}
                continue

            # Service properties
            if current_service and indent >= 4:
                if ':' in stripped:
                    prop_key = stripped.split(':')[0].strip()
                    prop_val = stripped.split(':', 1)[1].strip() if ':' in stripped else ''
                    if prop_key in ('image', 'build', 'command', 'restart'):
                        result['services'][current_service][prop_key] = prop_val
                elif stripped.startswith('- '):
                    val = stripped[2:].strip()
                    # Determine which list this belongs to
                    # (simple heuristic based on content)
                    if ':' in val and any(c.isdigit() for c in val):
                        result['services'][current_service].setdefault('ports', []).append(val)

        return result if result.get('services') else None
