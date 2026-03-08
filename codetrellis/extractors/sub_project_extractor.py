"""
CodeTrellis Sub-Project Extractor — Phase 6 of v5.0 Universal Scanner
=======================================================================

Handles multi-project / monorepo layouts:
- Identifies sub-projects from discovery results
- Runs targeted extraction per sub-project
- Resolves cross-references between sub-projects
- Builds dependency graph across sub-projects

Works with DiscoveryExtractor's SubProjectInfo to provide
deep per-project analysis without re-walking the entire tree.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SubProjectDependency:
    """A dependency relationship between sub-projects."""
    from_project: str
    to_project: str
    dep_type: str            # "import", "api_call", "shared_module", "docker_network"
    evidence: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_project": self.from_project,
            "to_project": self.to_project,
            "dep_type": self.dep_type,
            "evidence": self.evidence,
        }


@dataclass
class SubProjectAnalysis:
    """Analysis of a single sub-project."""
    name: str
    root_path: str
    project_type: str        # "go_module", "python_package", "node_package", "rust_crate"
    language: str
    description: Optional[str] = None
    entry_points: List[str] = field(default_factory=list)
    exported_packages: List[str] = field(default_factory=list)
    internal_deps: List[str] = field(default_factory=list)  # deps within monorepo
    external_deps: List[str] = field(default_factory=list)  # external dependencies
    # Gap #9 Fix: Add completion tracking fields
    completion_percentage: Optional[int] = None
    status: Optional[str] = None  # "complete", "in-progress", "pending"
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "root_path": self.root_path,
            "project_type": self.project_type,
            "language": self.language,
            "description": self.description,
            "entry_points": self.entry_points,
            "exported_packages": self.exported_packages[:10],
            "internal_deps": self.internal_deps,
            "external_deps": self.external_deps[:15],
        }
        # Gap #9 Fix: Include completion fields if available
        if self.completion_percentage is not None:
            result["completion_percentage"] = self.completion_percentage
        if self.status:
            result["status"] = self.status
        if self.summary:
            result["summary"] = self.summary
        return result


@dataclass
class SubProjectResult:
    """Complete sub-project analysis."""
    projects: List[SubProjectAnalysis] = field(default_factory=list)
    cross_deps: List[SubProjectDependency] = field(default_factory=list)
    is_monorepo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projects": [p.to_dict() for p in self.projects],
            "cross_deps": [d.to_dict() for d in self.cross_deps],
            "is_monorepo": self.is_monorepo,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# Sub-Projects ({len(self.projects)})")
        if self.is_monorepo:
            lines.append("# Monorepo detected")

        for proj in self.projects:
            desc = f" # {proj.description}" if proj.description else ""
            # Gap #9 Fix: Include completion status in header
            status_str = ""
            if proj.status:
                status_str = f"|{proj.status}"
            if proj.completion_percentage is not None:
                status_str += f":{proj.completion_percentage}%"
            
            lines.append(f"## {proj.name} [{proj.language}/{proj.project_type}]{status_str}{desc}")
            lines.append(f"  path: {proj.root_path}")
            
            # Gap #9 Fix: Show summary if available
            if proj.summary:
                lines.append(f"  status: {proj.summary}")
            
            if proj.entry_points:
                lines.append(f"  entry: {', '.join(proj.entry_points[:3])}")
            if proj.internal_deps:
                lines.append(f"  internal_deps: {', '.join(proj.internal_deps)}")
            if proj.external_deps:
                top_deps = proj.external_deps[:10]
                more = f",+{len(proj.external_deps)-10}" if len(proj.external_deps) > 10 else ""
                lines.append(f"  deps: {', '.join(top_deps)}{more}")

        if self.cross_deps:
            lines.append(f"## Cross-Dependencies ({len(self.cross_deps)})")
            for dep in self.cross_deps:
                lines.append(f"  {dep.from_project} -> {dep.to_project} [{dep.dep_type}]")

        return '\n'.join(lines)


# =============================================================================
# Sub-Project Extractor
# =============================================================================

class SubProjectExtractor:
    """
    Analyze sub-projects / monorepo structure.

    Uses DiscoveryExtractor's SubProjectInfo list as input
    and performs deeper per-project analysis.
    """

    def extract(
        self,
        root_dir: Path,
        sub_projects: List[Any],  # List[SubProjectInfo] from discovery
    ) -> Optional[SubProjectResult]:
        """
        Analyze each sub-project and detect cross-dependencies.

        Args:
            root_dir: Top-level project directory
            sub_projects: List of SubProjectInfo from DiscoveryExtractor

        Returns:
            SubProjectResult or None if no sub-projects
        """
        if not sub_projects:
            return None

        result = SubProjectResult()
        result.is_monorepo = len(sub_projects) > 1

        project_names: Set[str] = set()
        project_paths: Dict[str, str] = {}  # name → relative path

        for sp in sub_projects:
            name = getattr(sp, 'name', '') or ''
            path = getattr(sp, 'path', '') or ''
            project_type = getattr(sp, 'project_type', '') or ''
            language = getattr(sp, 'language', '') or ''

            if not name or not path:
                continue

            full_path = root_dir / path if not Path(path).is_absolute() else Path(path)
            if not full_path.exists():
                continue

            analysis = self._analyze_sub_project(full_path, name, project_type, language)
            result.projects.append(analysis)
            project_names.add(name)
            project_paths[name] = path

        # Detect cross-dependencies
        if result.is_monorepo:
            self._detect_cross_deps(root_dir, result, project_names, project_paths)

        return result if result.projects else None

    def _analyze_sub_project(
        self,
        project_path: Path,
        name: str,
        project_type: str,
        language: str,
    ) -> SubProjectAnalysis:
        """Analyze a single sub-project."""
        analysis = SubProjectAnalysis(
            name=name,
            root_path=str(project_path),
            project_type=project_type,
            language=language,
        )

        if language == 'Go' or project_type == 'go_module':
            self._analyze_go_project(project_path, analysis)
        elif language == 'Python' or project_type in ('python_package', 'python_project'):
            self._analyze_python_project(project_path, analysis)
        elif language in ('JavaScript', 'TypeScript') or project_type == 'node_package':
            self._analyze_node_project(project_path, analysis)
        elif language == 'Rust' or project_type == 'rust_crate':
            self._analyze_rust_project(project_path, analysis)
        elif language == 'Swift' or project_type == 'swift_package':
            self._analyze_swift_project(project_path, analysis)
        
        # Gap #9 Fix: Calculate completion percentage and generate summary
        self._calculate_completion(project_path, analysis)

        return analysis
    
    def _calculate_completion(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Calculate completion percentage based on TODO/FIXME markers and file count."""
        total_files = 0
        total_lines = 0
        todo_count = 0
        fixme_count = 0
        placeholder_count = 0
        
        # Scan source files
        for ext in ['*.py', '*.ts', '*.js', '*.go', '*.rs', '*.java', '*.swift']:
            for file_path in path.rglob(ext):
                # Skip ignored directories
                if any(part in str(file_path) for part in ['node_modules', '.git', '__pycache__', 'vendor', 'dist', 'build']):
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    total_files += 1
                    total_lines += content.count('\n')
                    
                    # Count markers
                    todo_count += len(re.findall(r'\bTODO\b', content, re.IGNORECASE))
                    fixme_count += len(re.findall(r'\bFIXME\b', content, re.IGNORECASE))
                    placeholder_count += len(re.findall(r'\bPLACEHOLDER\b', content, re.IGNORECASE))
                except (OSError, UnicodeDecodeError):
                    continue
        
        # Calculate completion percentage
        if total_files > 0:
            # Heuristic: each FIXME counts as 2% incomplete, TODO as 1%, PLACEHOLDER as 0.5%
            incompleteness = min(100, (fixme_count * 2 + todo_count * 1 + placeholder_count * 0.5))
            completion = max(0, 100 - incompleteness)
            
            # Generate summary
            status = "complete" if completion >= 95 else "in-progress" if completion >= 50 else "pending"
            summary_parts = []
            
            if fixme_count > 0:
                summary_parts.append(f"{fixme_count} FIXMEs")
            if todo_count > 0:
                summary_parts.append(f"{todo_count} TODOs")
            if placeholder_count > 0:
                summary_parts.append(f"{placeholder_count} placeholders")
            
            summary = f"{status}: {int(completion)}% complete ({total_files} files, {total_lines} lines)"
            if summary_parts:
                summary += f" - {', '.join(summary_parts)}"
            
            # Store in analysis (add these fields to SubProjectAnalysis if needed)
            if not hasattr(analysis, 'completion_percentage'):
                analysis.completion_percentage = int(completion)
            if not hasattr(analysis, 'summary'):
                analysis.summary = summary
            if not hasattr(analysis, 'status'):
                analysis.status = status

    def _analyze_go_project(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Analyze a Go module sub-project."""
        go_mod = path / 'go.mod'
        if go_mod.exists():
            try:
                content = go_mod.read_text(encoding='utf-8')
                # Module name
                mod_match = re.search(r'^module\s+(\S+)', content, re.M)
                if mod_match:
                    analysis.exported_packages.append(mod_match.group(1))

                # Dependencies
                for m in re.finditer(r'^\s+(\S+)\s+v[\d.]+', content, re.M):
                    dep = m.group(1)
                    analysis.external_deps.append(dep)
            except (OSError, UnicodeDecodeError):
                pass

        # Entry points: main.go files
        for main_go in path.rglob('main.go'):
            rel = str(main_go.relative_to(path))
            analysis.entry_points.append(rel)

        # Description from README
        analysis.description = self._read_description(path)

    def _analyze_python_project(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Analyze a Python sub-project."""
        # pyproject.toml
        pyproject = path / 'pyproject.toml'
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding='utf-8')
                name_match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.M)
                if name_match:
                    analysis.exported_packages.append(name_match.group(1))
                desc_match = re.search(r'^description\s*=\s*"([^"]+)"', content, re.M)
                if desc_match:
                    analysis.description = desc_match.group(1)
            except (OSError, UnicodeDecodeError):
                pass

        # setup.py
        setup = path / 'setup.py'
        if setup.exists():
            try:
                content = setup.read_text(encoding='utf-8')
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if name_match:
                    analysis.exported_packages.append(name_match.group(1))
            except (OSError, UnicodeDecodeError):
                pass

        # requirements.txt
        req_file = path / 'requirements.txt'
        if req_file.exists():
            try:
                for line in req_file.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        pkg = re.split(r'[>=<!\[]', line)[0].strip()
                        if pkg:
                            analysis.external_deps.append(pkg)
            except (OSError, UnicodeDecodeError):
                pass

        # Entry points: __main__.py, manage.py, app.py
        for entry in ('__main__.py', 'manage.py', 'app.py', 'main.py', 'wsgi.py'):
            if (path / entry).exists():
                analysis.entry_points.append(entry)

        if not analysis.description:
            analysis.description = self._read_description(path)

    def _analyze_node_project(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Analyze a Node/TypeScript sub-project."""
        pkg_json = path / 'package.json'
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding='utf-8'))
                name = data.get('name', '')
                if name:
                    analysis.exported_packages.append(name)
                analysis.description = data.get('description')

                # Entry points
                main = data.get('main', '')
                if main:
                    analysis.entry_points.append(main)

                # Dependencies
                for dep_key in ('dependencies', 'devDependencies'):
                    for dep in data.get(dep_key, {}).keys():
                        if not dep.startswith('@types/'):
                            analysis.external_deps.append(dep)
            except (OSError, json.JSONDecodeError):
                pass

        if not analysis.description:
            analysis.description = self._read_description(path)

    def _analyze_rust_project(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Analyze a Rust crate."""
        cargo_toml = path / 'Cargo.toml'
        if cargo_toml.exists():
            try:
                content = cargo_toml.read_text(encoding='utf-8')
                name_match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.M)
                if name_match:
                    analysis.exported_packages.append(name_match.group(1))
                desc_match = re.search(r'^description\s*=\s*"([^"]+)"', content, re.M)
                if desc_match:
                    analysis.description = desc_match.group(1)

                # Dependencies
                in_deps = False
                for line in content.splitlines():
                    if line.strip().startswith('[dependencies'):
                        in_deps = True
                        continue
                    if line.strip().startswith('[') and in_deps:
                        in_deps = False
                        continue
                    if in_deps:
                        dep_match = re.match(r'^(\w[\w-]*)\s*=', line.strip())
                        if dep_match:
                            analysis.external_deps.append(dep_match.group(1))
            except (OSError, UnicodeDecodeError):
                pass

        # Entry point
        if (path / 'src' / 'main.rs').exists():
            analysis.entry_points.append('src/main.rs')
        if (path / 'src' / 'lib.rs').exists():
            analysis.entry_points.append('src/lib.rs')

        if not analysis.description:
            analysis.description = self._read_description(path)

    def _analyze_swift_project(self, path: Path, analysis: SubProjectAnalysis) -> None:
        """Analyze a Swift package sub-project."""
        package_swift = path / 'Package.swift'
        if package_swift.exists():
            try:
                content = package_swift.read_text(encoding='utf-8')
                # Package name
                name_match = re.search(r'name:\s*"([^"]+)"', content)
                if name_match:
                    analysis.exported_packages.append(name_match.group(1))
                # Dependencies
                for dep_match in re.finditer(
                    r'\.package\(\s*url:\s*"([^"]+)"', content
                ):
                    url = dep_match.group(1)
                    dep_name = url.rstrip('/').split('/')[-1]
                    if dep_name.endswith('.git'):
                        dep_name = dep_name[:-4]
                    analysis.external_deps.append(dep_name)
            except (OSError, UnicodeDecodeError):
                pass

        # Entry points
        sources_dir = path / 'Sources'
        if sources_dir.is_dir():
            for target_dir in sources_dir.iterdir():
                if target_dir.is_dir():
                    main_swift = target_dir / 'main.swift'
                    if main_swift.exists():
                        analysis.entry_points.append(
                            f'Sources/{target_dir.name}/main.swift'
                        )

        if not analysis.description:
            analysis.description = self._read_description(path)

    def _read_description(self, path: Path) -> Optional[str]:
        """Read first meaningful line from README."""
        for readme_name in ('README.md', 'README.rst', 'README.txt', 'README'):
            readme = path / readme_name
            if readme.exists():
                try:
                    content = readme.read_text(encoding='utf-8')
                    for line in content.splitlines():
                        stripped = line.strip()
                        if stripped and not stripped.startswith('#') and not stripped.startswith('='):
                            return stripped[:120]
                except (OSError, UnicodeDecodeError):
                    pass
        return None

    def _detect_cross_deps(
        self,
        root_dir: Path,
        result: SubProjectResult,
        project_names: Set[str],
        project_paths: Dict[str, str],
    ) -> None:
        """Detect dependencies between sub-projects."""
        # Build import path → project name map
        import_to_project: Dict[str, str] = {}
        for proj in result.projects:
            for pkg in proj.exported_packages:
                import_to_project[pkg] = proj.name

        # Check each project's deps against the map
        for proj in result.projects:
            for dep in proj.external_deps:
                for import_path, dep_project in import_to_project.items():
                    if dep_project != proj.name and (dep == import_path or dep.startswith(import_path + '/')):
                        result.cross_deps.append(SubProjectDependency(
                            from_project=proj.name,
                            to_project=dep_project,
                            dep_type='import',
                            evidence=dep,
                        ))

            # Move internal deps from external to internal
            for dep in result.cross_deps:
                if dep.from_project == proj.name:
                    if dep.to_project not in proj.internal_deps:
                        proj.internal_deps.append(dep.to_project)

        # Check docker-compose for network links
        compose_file = root_dir / 'docker-compose.yml'
        if not compose_file.exists():
            compose_file = root_dir / 'docker-compose.yaml'

        if compose_file.exists():
            try:
                content = compose_file.read_text(encoding='utf-8')
                # Detect service names that match project names
                service_pattern = re.compile(r'^\s+(\w[\w-]*):\s*$', re.M)
                services = set(m.group(1) for m in service_pattern.finditer(content))

                # Check depends_on
                depends_pattern = re.compile(r'depends_on:.*?(?=\w+:|\Z)', re.DOTALL)
                for section in depends_pattern.finditer(content):
                    section_text = section.group(0)
                    deps_in_section = re.findall(r'-\s*(\w[\w-]*)', section_text)
                    for dep_name in deps_in_section:
                        if dep_name in project_names:
                            result.cross_deps.append(SubProjectDependency(
                                from_project='docker-compose',
                                to_project=dep_name,
                                dep_type='docker_network',
                            ))
            except (OSError, UnicodeDecodeError):
                pass
