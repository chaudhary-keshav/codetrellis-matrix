"""
CodeTrellis Architecture Extractor
===========================

Extracts high-level project architecture information for onboarding:
- Entry points (main.ts, index.ts, app.module.ts)
- Directory structure and counts
- Dependencies (package.json, requirements.txt)
- Tech stack detection
- Architectural patterns
- Key configuration files
- API connections

This helps new developers (and AI) quickly understand the project.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ProjectType(Enum):
    """Type of project detected"""
    ANGULAR = "Angular"
    REACT = "React"
    VUE = "Vue"
    NESTJS = "NestJS"
    EXPRESS = "Express"
    FASTAPI = "FastAPI"
    FLASK = "Flask"
    DJANGO = "Django"
    NEXTJS = "Next.js"
    NUXT = "Nuxt"
    PYTHON_LIBRARY = "Python Library"
    NODE_LIBRARY = "Node Library"
    MONOREPO = "Monorepo"
    # v4.5 (G-17): Go project types
    GO_CLI = "Go CLI Application"
    GO_LIBRARY = "Go Library"
    GO_WEB_SERVICE = "Go Web Service"
    GO_FRAMEWORK = "Go Framework"
    # v4.12: Java project types
    JAVA_SPRING_BOOT = "Spring Boot Application"
    JAVA_QUARKUS = "Quarkus Application"
    JAVA_MICRONAUT = "Micronaut Application"
    JAVA_JAKARTA_EE = "Jakarta EE Application"
    JAVA_LIBRARY = "Java Library"
    JAVA_ANDROID = "Android Application"
    # v4.13: C# project types
    CSHARP_ASPNET = "ASP.NET Core Application"
    CSHARP_BLAZOR = "Blazor Application"
    CSHARP_MAUI = "MAUI Application"
    CSHARP_WPF = "WPF Application"
    CSHARP_CONSOLE = "C# Console Application"
    CSHARP_LIBRARY = "C# Library"
    CSHARP_AZURE_FUNCTIONS = "Azure Functions Application"
    # v4.22: Swift project types
    SWIFT_IOS_APP = "iOS Application"
    SWIFT_MACOS_APP = "macOS Application"
    SWIFT_VAPOR_APP = "Vapor Server Application"
    SWIFT_LIBRARY = "Swift Library"
    SWIFT_CLI = "Swift CLI Application"
    UNKNOWN = "Unknown"


class ArchPattern(Enum):
    """Detected architectural patterns"""
    STANDALONE_COMPONENTS = "standalone-components"
    SIGNAL_STORE = "signal-store"
    NGRX_STORE = "ngrx-store"
    REDUX = "redux"
    ONPUSH_CD = "onpush-cd"
    LAZY_LOADING = "lazy-loading"
    MVC = "mvc"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    REPOSITORY_PATTERN = "repository-pattern"
    CQRS = "cqrs"
    EVENT_DRIVEN = "event-driven"
    GRPC = "grpc"
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


@dataclass
class ProjectProfile:
    """
    Multi-dimensional project identity — v5.0.

    Captures ALL languages, frameworks, and facets rather than
    forcing a single ProjectType classification.
    """
    # Primary classification (backward compatible)
    primary_type: str = "Unknown"

    # All languages detected (from discovery)
    languages: list = None  # [{name, percentage, file_count}]

    # All frameworks per language (from discovery + dep analysis)
    frameworks: dict = None  # {"go": ["gin", "gorm"], "typescript": ["react"]}

    # Facets/concerns present
    facets: list = None  # ["rest-api", "websocket", "database", "auth", "docker", "ml"]

    # Sub-projects
    sub_projects: list = None  # From discovery

    # Rich stack summary (human-readable)
    stack_summary: str = ""  # "Go + React/TS + Gin + GORM + WebSocket + Multi-DB"

    # Test framework(s) and strategy
    testing: dict = None  # {"frameworks": ["pytest"], "test_dirs": ["tests/"], "test_file_count": 42}

    # Build system / package manager info
    build_system: dict = None  # {"manager": "yarn", "build_tool": "pdm-backend"}

    def __post_init__(self):
        if self.languages is None:
            self.languages = []
        if self.frameworks is None:
            self.frameworks = {}
        if self.facets is None:
            self.facets = []
        if self.sub_projects is None:
            self.sub_projects = []
        if self.testing is None:
            self.testing = {}
        if self.build_system is None:
            self.build_system = {}

    def to_dict(self):
        d = {
            "primary_type": self.primary_type,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "facets": self.facets,
            "sub_projects": self.sub_projects,
            "stack_summary": self.stack_summary,
        }
        if self.testing:
            d["testing"] = self.testing
        if self.build_system:
            d["build_system"] = self.build_system
        return d

    def to_codetrellis_format(self) -> str:
        parts = []
        if self.languages:
            lang_strs = [
                f"{l['name']}({l['percentage']:.0f}%)"
                for l in self.languages[:5]
            ]
            parts.append(f"languages:{','.join(lang_strs)}")
        if self.facets:
            parts.append(f"facets:{','.join(self.facets[:10])}")
        if self.stack_summary:
            parts.append(f"stack:{self.stack_summary}")
        return '|'.join(parts)


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    version: str = ""
    is_dev: bool = False
    category: str = ""  # core, ui, state, http, testing, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "isDev": self.is_dev,
            "category": self.category,
        }


@dataclass
class DirectoryInfo:
    """Information about a key directory"""
    name: str
    path: str
    file_count: int = 0
    purpose: str = ""  # components, services, models, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "fileCount": self.file_count,
            "purpose": self.purpose,
        }


@dataclass
class EntryPointInfo:
    """Information about a project entry point"""
    file_path: str
    kind: str  # main, bootstrap, routes, config
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass
class ApiConnectionInfo:
    """Information about external API connections"""
    name: str
    base_url: str = ""
    purpose: str = ""
    protocol: str = "http"  # http, grpc, websocket

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "baseUrl": self.base_url,
            "purpose": self.purpose,
            "protocol": self.protocol,
        }


@dataclass
class ProjectOverview:
    """Complete project overview for onboarding"""
    name: str
    project_type: ProjectType = ProjectType.UNKNOWN
    version: str = ""
    description: str = ""
    tech_stack: List[str] = field(default_factory=list)
    patterns: List[ArchPattern] = field(default_factory=list)
    entry_points: List[EntryPointInfo] = field(default_factory=list)
    directories: List[DirectoryInfo] = field(default_factory=list)
    dependencies: List[DependencyInfo] = field(default_factory=list)
    dev_dependencies: List[DependencyInfo] = field(default_factory=list)
    api_connections: List[ApiConnectionInfo] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        return sum(d.file_count for d in self.directories)

    @property
    def core_dependencies(self) -> List[DependencyInfo]:
        return [d for d in self.dependencies if not d.is_dev]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.project_type.value,
            "version": self.version,
            "description": self.description,
            "techStack": self.tech_stack,
            "patterns": [p.value for p in self.patterns],
            "entryPoints": [e.to_dict() for e in self.entry_points],
            "directories": [d.to_dict() for d in self.directories],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "devDependencies": [d.to_dict() for d in self.dev_dependencies],
            "apiConnections": [a.to_dict() for a in self.api_connections],
            "configFiles": self.config_files,
            "scripts": self.scripts,
            "totalFiles": self.total_files,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format for prompt injection"""
        lines = []

        # Line 1: Basic info
        tech = ",".join(self.tech_stack[:5])  # Top 5 tech
        lines.append(f"name:{self.name}|type:{self.project_type.value}|stack:{tech}")

        # Line 2: Entry points
        if self.entry_points:
            entry_str = "→".join(Path(e.file_path).name for e in self.entry_points[:4])
            lines.append(f"entry:{entry_str}")

        # Line 3: Directory summary
        if self.directories:
            dir_parts = []
            for d in sorted(self.directories, key=lambda x: x.file_count, reverse=True)[:6]:
                dir_parts.append(f"{d.name}({d.file_count})")
            lines.append(f"dirs:{','.join(dir_parts)}")

        # Line 4: Patterns
        if self.patterns:
            pattern_str = ",".join(p.value for p in self.patterns[:5])
            lines.append(f"patterns:{pattern_str}")

        # Line 5: Key dependencies
        if self.dependencies:
            key_deps = [d.name for d in self.dependencies if d.category == "core"][:5]
            if key_deps:
                lines.append(f"deps:{','.join(key_deps)}")

        # Line 6: API connections
        if self.api_connections:
            api_parts = [f"{a.name}({a.protocol})" for a in self.api_connections[:3]]
            lines.append(f"apis:{','.join(api_parts)}")

        # Line 7: Available scripts
        if self.scripts:
            script_names = list(self.scripts.keys())[:5]
            lines.append(f"scripts:{','.join(script_names)}")

        return "\n".join(lines)


class ArchitectureExtractor:
    """
    Extracts project architecture and overview information.

    Analyzes:
    - package.json / requirements.txt for dependencies
    - Project structure for entry points
    - Code patterns for architecture detection
    - Config files for tech stack
    """

    # Known entry points by project type
    ENTRY_POINTS = {
        "angular": ["main.ts", "app.component.ts", "app.routes.ts", "app.module.ts", "app.config.ts"],
        "react": ["index.tsx", "App.tsx", "index.js", "App.js"],
        "nestjs": ["main.ts", "app.module.ts", "app.controller.ts"],
        "python": ["main.py", "app.py", "__main__.py", "wsgi.py", "asgi.py"],
        "node": ["index.js", "index.ts", "server.js", "server.ts", "app.js", "app.ts"],
    }

    # Key directories and their purposes
    DIRECTORY_PURPOSES = {
        "components": "UI Components",
        "services": "Business Logic Services",
        "stores": "State Management",
        "models": "Data Models/Types",
        "utils": "Utility Functions",
        "helpers": "Helper Functions",
        "guards": "Route Guards",
        "interceptors": "HTTP Interceptors",
        "pipes": "Transform Pipes",
        "directives": "Custom Directives",
        "pages": "Page Components",
        "views": "View Components",
        "layouts": "Layout Components",
        "features": "Feature Modules",
        "shared": "Shared Module",
        "core": "Core Module",
        "api": "API Layer",
        "lib": "Library Code",
        "hooks": "React Hooks",
        "context": "React Context",
        "reducers": "Redux Reducers",
        "actions": "Redux Actions",
        "selectors": "Redux Selectors",
        "controllers": "Controllers",
        "repositories": "Data Repositories",
        "entities": "Database Entities",
        "migrations": "DB Migrations",
        "schemas": "Schema Definitions",
        "dtos": "Data Transfer Objects",
        "middleware": "Middleware",
        "config": "Configuration",
        "tests": "Test Files",
        "__tests__": "Test Files",
        "spec": "Test Specifications",
    }

    # Dependency categories
    DEPENDENCY_CATEGORIES = {
        # Angular
        "@angular/core": "core",
        "@angular/common": "core",
        "@angular/router": "core",
        "@angular/forms": "core",
        "@angular/platform-browser": "core",
        "@ngrx/store": "state",
        "@ngrx/effects": "state",
        "@ngrx/signals": "state",
        "rxjs": "reactive",

        # React
        "react": "core",
        "react-dom": "core",
        "react-router": "routing",
        "react-router-dom": "routing",
        "redux": "state",
        "react-redux": "state",
        "@reduxjs/toolkit": "state",
        "zustand": "state",
        "mobx": "state",
        "recoil": "state",

        # NestJS
        "@nestjs/core": "core",
        "@nestjs/common": "core",
        "@nestjs/microservices": "core",
        "@nestjs/mongoose": "database",
        "@nestjs/typeorm": "database",

        # HTTP/API
        "axios": "http",
        "@angular/common/http": "http",
        "socket.io-client": "websocket",
        "@grpc/grpc-js": "grpc",

        # UI
        "tailwindcss": "ui",
        "@angular/material": "ui",
        "@mui/material": "ui",
        "bootstrap": "ui",
        "primeng": "ui",

        # Testing
        "jest": "testing",
        "vitest": "testing",
        "@testing-library/react": "testing",
        "cypress": "testing",
        "playwright": "testing",

        # Python
        "fastapi": "core",
        "flask": "core",
        "django": "core",
        "sqlalchemy": "database",
        "pydantic": "validation",
        "pytest": "testing",
    }

    # Pattern detection keywords
    PATTERN_INDICATORS = {
        ArchPattern.STANDALONE_COMPONENTS: ["standalone: true", "standalone:true"],
        ArchPattern.SIGNAL_STORE: ["signalStore", "withState", "withComputed", "withMethods"],
        ArchPattern.NGRX_STORE: ["@ngrx/store", "createReducer", "createAction", "createSelector"],
        ArchPattern.REDUX: ["createSlice", "configureStore", "useSelector", "useDispatch"],
        ArchPattern.ONPUSH_CD: ["changeDetection: ChangeDetectionStrategy.OnPush"],
        ArchPattern.LAZY_LOADING: ["loadChildren", "loadComponent"],
        ArchPattern.REPOSITORY_PATTERN: ["Repository", "@Repository", "getRepository"],
        ArchPattern.GRPC: [".proto", "GrpcService", "@GrpcMethod"],
        ArchPattern.WEBSOCKET: ["WebSocket", "socket.io", "@SubscribeMessage", "Gateway"],
        ArchPattern.GRAPHQL: ["@Query", "@Mutation", "gql`", "useQuery", "useMutation"],
    }

    def __init__(self):
        self._project_root: Optional[Path] = None

    def extract_from_directory(self, project_path: str) -> ProjectOverview:
        """
        Extract architecture overview from a project directory.

        Args:
            project_path: Path to the project root

        Returns:
            ProjectOverview with all extracted information
        """
        self._project_root = Path(project_path)

        overview = ProjectOverview(name=self._project_root.name)

        # Extract from package.json if exists
        package_json = self._project_root / "package.json"
        if package_json.exists():
            self._extract_from_package_json(package_json, overview)

        # Extract from requirements.txt if exists
        requirements = self._project_root / "requirements.txt"
        if requirements.exists():
            self._extract_from_requirements(requirements, overview)

        # Extract from pyproject.toml if exists
        pyproject = self._project_root / "pyproject.toml"
        if pyproject.exists():
            self._extract_from_pyproject(pyproject, overview)

        # Extract from Package.swift if exists (Swift/SPM)
        package_swift = self._project_root / "Package.swift"
        if package_swift.exists():
            self._extract_from_package_swift(package_swift, overview)

        # Detect project type
        overview.project_type = self._detect_project_type(overview)

        # Find entry points
        overview.entry_points = self._find_entry_points()

        # Analyze directory structure
        overview.directories = self._analyze_directories()

        # Detect patterns from code
        overview.patterns = self._detect_patterns()

        # Find config files
        overview.config_files = self._find_config_files()

        # Extract API connections
        overview.api_connections = self._find_api_connections()

        # Build tech stack
        overview.tech_stack = self._build_tech_stack(overview)

        return overview

    def _extract_from_package_json(self, path: Path, overview: ProjectOverview):
        """Extract info from package.json"""
        try:
            with open(path) as f:
                data = json.load(f)

            overview.name = data.get("name", overview.name)
            overview.version = data.get("version", "")
            overview.description = data.get("description", "")
            overview.scripts = data.get("scripts", {})

            # Process dependencies
            deps = data.get("dependencies", {})
            for name, version in deps.items():
                category = self.DEPENDENCY_CATEGORIES.get(name, "")
                overview.dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    is_dev=False,
                    category=category,
                ))

            # Process dev dependencies
            dev_deps = data.get("devDependencies", {})
            for name, version in dev_deps.items():
                category = self.DEPENDENCY_CATEGORIES.get(name, "testing")
                overview.dev_dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    is_dev=True,
                    category=category,
                ))
        except Exception:
            pass

    def _extract_from_requirements(self, path: Path, overview: ProjectOverview):
        """Extract info from requirements.txt"""
        try:
            content = path.read_text()
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Parse: package==version or package>=version
                match = re.match(r'^([a-zA-Z0-9_-]+)(?:[=<>!]+(.+))?', line)
                if match:
                    name = match.group(1)
                    version = match.group(2) or ""
                    category = self.DEPENDENCY_CATEGORIES.get(name.lower(), "")
                    overview.dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        is_dev=False,
                        category=category,
                    ))
        except Exception:
            pass

    def _extract_from_pyproject(self, path: Path, overview: ProjectOverview):
        """Extract info from pyproject.toml including dependencies."""
        try:
            content = path.read_text(encoding='utf-8')

            # Simple parsing (not full TOML parser)
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                overview.name = name_match.group(1)

            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                overview.version = version_match.group(1)

            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_match:
                overview.description = desc_match.group(1)

            # Parse [project.dependencies] array
            # Format: dependencies = [\n  "starlette>=0.40.0,<0.47.0",\n  "pydantic>=1.0",\n]
            # Note: Use ^\] on its own line as the closing bracket to avoid
            # premature match on extras brackets like django[bcrypt]
            deps_match = re.search(
                r'\[project\].*?dependencies\s*=\s*\[(.*?)^\]',
                content, re.DOTALL | re.MULTILINE
            )
            if deps_match:
                deps_block = deps_match.group(1)
                self._parse_pyproject_dep_list(deps_block, overview, is_dev=False)

            # Parse [project.optional-dependencies] sections
            # Format: [project.optional-dependencies]\n testing = ["pytest", ...]\n all = [...]
            opt_deps_section = re.search(
                r'\[project\.optional-dependencies\](.*?)(?=\n\[|\Z)',
                content, re.DOTALL
            )
            if opt_deps_section:
                section_text = opt_deps_section.group(1)
                # Find each group: group_name = ["dep1", "dep2"]
                # Use ^\] to match closing bracket on its own line (avoids extras like [bcrypt])
                for group_match in re.finditer(
                    r'(\w+)\s*=\s*\[(.*?)^\]', section_text, re.DOTALL | re.MULTILINE
                ):
                    group_name = group_match.group(1).lower()
                    group_deps = group_match.group(2)
                    is_dev = group_name in ('dev', 'test', 'testing', 'docs', 'lint',
                                            'development', 'optional')
                    self._parse_pyproject_dep_list(group_deps, overview, is_dev=is_dev)

            # Parse [tool.poetry.dependencies] if using Poetry
            poetry_deps = re.search(
                r'\[tool\.poetry\.dependencies\](.*?)(?=\n\[|\Z)',
                content, re.DOTALL
            )
            if poetry_deps:
                for dep_match in re.finditer(
                    r'^(\w[\w-]*)\s*=', poetry_deps.group(1), re.MULTILINE
                ):
                    dep_name = dep_match.group(1)
                    if dep_name.lower() != 'python':
                        category = self.DEPENDENCY_CATEGORIES.get(dep_name.lower(), "")
                        overview.dependencies.append(DependencyInfo(
                            name=dep_name, version="", is_dev=False, category=category,
                        ))

        except Exception:
            pass

    def _parse_pyproject_dep_list(self, deps_text: str, overview: ProjectOverview, is_dev: bool):
        """
        Parse a TOML dependency list string like:
          "starlette>=0.40.0,<0.47.0",
          "pydantic>=1.0",
        """
        for dep_str_match in re.finditer(r'"([^"]+)"', deps_text):
            dep_str = dep_str_match.group(1).strip()
            if not dep_str:
                continue
            # Parse: name[extras]>=version,<version; markers
            dep_parse = re.match(r'^([a-zA-Z0-9_][a-zA-Z0-9_.-]*)(?:\[.*?\])?\s*(?:[><=!~]+(.+?))?(?:;.*)?$', dep_str)
            if dep_parse:
                name = dep_parse.group(1)
                version = dep_parse.group(2) or ""
                # Clean up version (remove trailing commas, extra constraints)
                version = version.split(',')[0].strip() if version else ""
                category = self.DEPENDENCY_CATEGORIES.get(name.lower(), "")
                target = overview.dev_dependencies if is_dev else overview.dependencies
                # Avoid duplicates
                if not any(d.name.lower() == name.lower() for d in target):
                    target.append(DependencyInfo(
                        name=name, version=version, is_dev=is_dev, category=category,
                    ))

    def _extract_from_package_swift(self, path: Path, overview: ProjectOverview):
        """Extract info from Package.swift (Swift Package Manager)"""
        try:
            content = path.read_text(encoding='utf-8')

            # Extract package name
            name_match = re.search(r'name:\s*"([^"]+)"', content)
            if name_match:
                overview.name = name_match.group(1)

            # Extract swift-tools-version
            tools_version = re.search(r'//\s*swift-tools-version:\s*([\d.]+)', content)
            if tools_version:
                overview.version = f"swift-tools-version:{tools_version.group(1)}"

            # Extract dependencies from .package(url:..., from:...)
            for dep_match in re.finditer(
                r'\.package\(\s*url:\s*"([^"]+)"[^)]*(?:from:\s*"([^"]*)")?[^)]*\)',
                content
            ):
                url = dep_match.group(1)
                version = dep_match.group(2) or ""
                # Extract package name from URL
                dep_name = url.rstrip('/').split('/')[-1]
                if dep_name.endswith('.git'):
                    dep_name = dep_name[:-4]
                category = self.DEPENDENCY_CATEGORIES.get(dep_name.lower(), "")
                overview.dependencies.append(DependencyInfo(
                    name=dep_name, version=version, is_dev=False, category=category,
                ))

            # Extract platform requirements
            platform_match = re.search(r'platforms:\s*\[(.*?)\]', content, re.DOTALL)
            if platform_match:
                platforms = re.findall(r'\.(iOS|macOS|tvOS|watchOS|visionOS)\("([^"]+)"\)',
                                       platform_match.group(1))
                if platforms and not overview.description:
                    overview.description = "Platforms: " + ", ".join(
                        f"{p[0]} {p[1]}" for p in platforms
                    )

        except Exception:
            pass

    def _detect_project_type(self, overview: ProjectOverview) -> ProjectType:
        """
        Detect project type from dependencies and project structure.
        Phase A (WS-5 / G-11): Enhanced to detect monorepos, Python projects,
        and mixed-stack projects that previously fell through to UNKNOWN.
        """
        dep_names = {d.name.lower() for d in overview.dependencies}

        # --- 1. Check for monorepo indicators FIRST ---
        if self._project_root:
            # Multiple package.json or workspaces config indicates monorepo
            nested_pkg_jsons = list(self._project_root.glob('*/package.json'))
            # Exclude node_modules
            nested_pkg_jsons = [p for p in nested_pkg_jsons
                                if 'node_modules' not in str(p)]

            root_pkg = self._project_root / 'package.json'
            has_workspaces = False
            if root_pkg.exists():
                try:
                    import json
                    with open(root_pkg) as f:
                        data = json.load(f)
                    has_workspaces = 'workspaces' in data
                except Exception:
                    pass

            # Lerna, nx, turborepo, or pnpm workspace indicators
            monorepo_files = [
                'lerna.json', 'nx.json', 'turbo.json',
                'pnpm-workspace.yaml', 'rush.json',
            ]
            has_monorepo_tool = any(
                (self._project_root / f).exists() for f in monorepo_files
            )

            # services/ or packages/ directory with multiple sub-projects
            services_dir = self._project_root / 'services'
            packages_dir = self._project_root / 'packages'
            has_services_dir = (services_dir.is_dir() and
                                len([d for d in services_dir.iterdir() if d.is_dir()]) >= 2)
            has_packages_dir = (packages_dir.is_dir() and
                                len([d for d in packages_dir.iterdir() if d.is_dir()]) >= 2)

            if (has_workspaces or has_monorepo_tool or
                    len(nested_pkg_jsons) >= 2 or
                    has_services_dir or has_packages_dir):
                return ProjectType.MONOREPO

        # --- 2. JavaScript/TypeScript frameworks ---
        if "@angular/core" in dep_names:
            return ProjectType.ANGULAR
        if "react" in dep_names:
            if "next" in dep_names:
                return ProjectType.NEXTJS
            return ProjectType.REACT
        if "vue" in dep_names:
            if "nuxt" in dep_names:
                return ProjectType.NUXT
            return ProjectType.VUE
        if "@nestjs/core" in dep_names:
            return ProjectType.NESTJS
        if "express" in dep_names:
            return ProjectType.EXPRESS

        # --- 3. Python frameworks ---
        if "fastapi" in dep_names:
            return ProjectType.FASTAPI
        if "flask" in dep_names:
            return ProjectType.FLASK
        if "django" in dep_names:
            return ProjectType.DJANGO

        # --- 3b. Django fallback: detect via manage.py + settings.py ---
        if self._project_root:
            has_manage = (self._project_root / 'manage.py').exists()
            # settings.py can be nested (e.g., myproject/settings.py)
            has_settings = any(self._project_root.glob('*/settings.py'))
            if has_manage and has_settings:
                return ProjectType.DJANGO

        # --- 4. Go project detection (go.mod present) ---
        if self._project_root:
            # --- 3b. Java project detection (pom.xml or build.gradle) ---
            pom_xml = self._project_root / 'pom.xml'
            build_gradle = self._project_root / 'build.gradle'
            build_gradle_kts = self._project_root / 'build.gradle.kts'
            if pom_xml.exists() or build_gradle.exists() or build_gradle_kts.exists():
                try:
                    # Read build file to detect framework
                    build_content = ""
                    if pom_xml.exists():
                        build_content = pom_xml.read_text()
                    elif build_gradle.exists():
                        build_content = build_gradle.read_text()
                    elif build_gradle_kts.exists():
                        build_content = build_gradle_kts.read_text()

                    if 'spring-boot' in build_content or 'springframework' in build_content:
                        return ProjectType.JAVA_SPRING_BOOT
                    elif 'quarkus' in build_content.lower():
                        return ProjectType.JAVA_QUARKUS
                    elif 'micronaut' in build_content.lower():
                        return ProjectType.JAVA_MICRONAUT
                    elif 'jakarta' in build_content.lower() or 'javax.servlet' in build_content:
                        return ProjectType.JAVA_JAKARTA_EE
                    elif 'com.android' in build_content:
                        return ProjectType.JAVA_ANDROID
                    else:
                        return ProjectType.JAVA_LIBRARY
                except Exception:
                    return ProjectType.JAVA_LIBRARY

            # --- 4b. C# project detection (.sln or .csproj) ---
            sln_files = list(self._project_root.glob('*.sln'))
            csproj_files = list(self._project_root.glob('**/*.csproj'))
            # Filter out bin/obj directories
            csproj_files = [p for p in csproj_files
                            if 'bin' not in str(p) and 'obj' not in str(p)]
            if sln_files or csproj_files:
                try:
                    # Read csproj/sln to detect framework
                    build_content = ""
                    for csproj in csproj_files[:3]:  # Check first few
                        build_content += csproj.read_text()

                    if 'Microsoft.NET.Sdk.Web' in build_content or 'AspNetCore' in build_content:
                        return ProjectType.CSHARP_ASPNET
                    elif 'Microsoft.NET.Sdk.BlazorWebAssembly' in build_content or \
                         'Microsoft.AspNetCore.Components' in build_content:
                        return ProjectType.CSHARP_BLAZOR
                    elif 'Microsoft.Maui' in build_content:
                        return ProjectType.CSHARP_MAUI
                    elif 'Microsoft.WindowsDesktop.App.WPF' in build_content:
                        return ProjectType.CSHARP_WPF
                    elif 'Microsoft.Azure.Functions' in build_content or \
                         'Microsoft.NET.Sdk.Functions' in build_content:
                        return ProjectType.CSHARP_AZURE_FUNCTIONS
                    elif 'Exe' in build_content:
                        return ProjectType.CSHARP_CONSOLE
                    else:
                        return ProjectType.CSHARP_LIBRARY
                except Exception:
                    return ProjectType.CSHARP_LIBRARY

            go_mod = self._project_root / 'go.mod'
            if go_mod.exists():
                # Read go.mod for module name and dependencies
                try:
                    go_mod_content = go_mod.read_text()
                    has_main_go = (self._project_root / 'main.go').exists()
                    has_cmd_dir = (self._project_root / 'cmd').is_dir()

                    # Detect web frameworks in go.mod
                    web_frameworks = ['gin-gonic', 'labstack/echo', 'go-chi/chi',
                                      'gorilla/mux', 'gofiber/fiber', 'net/http']
                    has_web = any(fw in go_mod_content for fw in web_frameworks)

                    # Detect if it's a framework (has /examples, /plugins, many exported packages)
                    has_examples = (self._project_root / 'examples').is_dir()
                    has_plugins = (self._project_root / 'plugins').is_dir()
                    has_apis_dir = (self._project_root / 'apis').is_dir()

                    # Framework detection: has examples + apis/plugins + exports types for others
                    if has_examples and (has_plugins or has_apis_dir):
                        return ProjectType.GO_FRAMEWORK
                    elif has_web or has_apis_dir:
                        return ProjectType.GO_WEB_SERVICE
                    elif has_main_go or has_cmd_dir:
                        return ProjectType.GO_CLI
                    else:
                        return ProjectType.GO_LIBRARY
                except Exception:
                    return ProjectType.GO_LIBRARY

            # --- 4c. Swift project detection (Package.swift present) ---
            package_swift = self._project_root / 'Package.swift'
            if package_swift.exists():
                try:
                    swift_content = package_swift.read_text()
                    dep_names = {d.name.lower() for d in overview.dependencies}

                    # Detect Vapor server-side
                    if 'vapor' in swift_content.lower() or 'vapor' in dep_names:
                        return ProjectType.SWIFT_VAPOR_APP

                    # Determine target types from Package.swift
                    has_executable = '.executableTarget' in swift_content
                    has_library = '.library(' in swift_content
                    has_xcodeproj = bool(list(self._project_root.glob('*.xcodeproj')))
                    has_xcworkspace = bool(list(self._project_root.glob('*.xcworkspace')))
                    ios_platforms = '.iOS' in swift_content or '.macOS' in swift_content

                    # Library-only packages: if Package.swift declares .library targets
                    # and has NO .executableTarget, it's a library regardless of platform
                    if has_library and not has_executable:
                        return ProjectType.SWIFT_LIBRARY

                    # CLI tool: executable target without iOS/macOS platform markers
                    if has_executable and not ios_platforms:
                        return ProjectType.SWIFT_CLI

                    # Xcode project with platform markers → app
                    if has_xcodeproj or has_xcworkspace:
                        if '.iOS' in swift_content:
                            return ProjectType.SWIFT_IOS_APP
                        elif '.macOS' in swift_content:
                            return ProjectType.SWIFT_MACOS_APP

                    # Executable with platform markers → app
                    if has_executable and ios_platforms:
                        if '.iOS' in swift_content:
                            return ProjectType.SWIFT_IOS_APP
                        else:
                            return ProjectType.SWIFT_MACOS_APP

                    # Fallback: if platforms but no targets info, check for Xcode artifacts
                    if ios_platforms:
                        if '.iOS' in swift_content:
                            return ProjectType.SWIFT_IOS_APP
                        else:
                            return ProjectType.SWIFT_MACOS_APP

                    return ProjectType.SWIFT_LIBRARY
                except Exception:
                    return ProjectType.SWIFT_LIBRARY

        # --- 5. Python library detection (pyproject.toml or setup.py present) ---
        if self._project_root:
            has_pyproject = (self._project_root / 'pyproject.toml').exists()
            has_setup_py = (self._project_root / 'setup.py').exists()
            has_requirements = (self._project_root / 'requirements.txt').exists()
            py_files = list(self._project_root.glob('*.py'))
            if has_pyproject or has_setup_py:
                return ProjectType.PYTHON_LIBRARY
            # If we have Python deps but no framework, still classify as Python Library
            if has_requirements and len(py_files) > 0:
                return ProjectType.PYTHON_LIBRARY

        # --- 6. Node library (has package.json but no framework detected) ---
        if self._project_root and (self._project_root / 'package.json').exists():
            return ProjectType.NODE_LIBRARY

        return ProjectType.UNKNOWN

    def _find_entry_points(self) -> List[EntryPointInfo]:
        """Find project entry points"""
        entry_points = []

        if not self._project_root:
            return entry_points

        # Check src directory first
        src_dir = self._project_root / "src"
        search_dirs = [src_dir, self._project_root] if src_dir.exists() else [self._project_root]

        # Also check src/app for Angular
        app_dir = src_dir / "app" if src_dir.exists() else None
        if app_dir and app_dir.exists():
            search_dirs.insert(0, app_dir)

        for entry_type, filenames in self.ENTRY_POINTS.items():
            for filename in filenames:
                for search_dir in search_dirs:
                    file_path = search_dir / filename
                    if file_path.exists():
                        rel_path = str(file_path.relative_to(self._project_root))
                        entry_points.append(EntryPointInfo(
                            file_path=rel_path,
                            kind=self._get_entry_kind(filename),
                            description=f"{entry_type.title()} entry point",
                        ))
                        break

        return entry_points

    def _get_entry_kind(self, filename: str) -> str:
        """Determine entry point kind from filename"""
        if "main" in filename:
            return "main"
        if "routes" in filename:
            return "routes"
        if "app" in filename:
            return "bootstrap"
        if "config" in filename:
            return "config"
        if "index" in filename:
            return "index"
        return "entry"

    def _analyze_directories(self) -> List[DirectoryInfo]:
        """Analyze key directories in the project"""
        directories = []

        if not self._project_root:
            return directories

        # Phase A (WS-2 / G-21): Comprehensive ignore set for directory analysis
        IGNORE_DIRS = {
            'node_modules', 'dist', 'build', '__pycache__', '.git', 'coverage',
            '.angular', '.next', '.venv', 'venv', 'env', '.pytest_cache',
            '.tox', '.mypy_cache', '.ruff_cache', 'htmlcov', '.nyc_output',
            'tests', 'test', '__tests__', '__mocks__', '__snapshots__',
            'site-packages', '.eggs',
        }

        # Start from src or project root
        src_dir = self._project_root / "src"
        base_dir = src_dir if src_dir.exists() else self._project_root

        # Also check src/app for Angular
        app_dir = base_dir / "app"
        if app_dir.exists():
            base_dir = app_dir

        for item in base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dir_name = item.name.lower()

                # Skip common non-code directories (expanded list)
                if dir_name in IGNORE_DIRS:
                    continue

                # Count relevant source files, but EXCLUDE ignored sub-trees
                # v4.9: Language-agnostic — count ALL known source file types, not just web frontend
                SOURCE_EXTENSIONS = {
                    # Web frontend
                    '.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte',
                    # Backend / systems
                    '.go', '.py', '.java', '.rs', '.rb', '.cs', '.cpp', '.c', '.h',
                    '.swift', '.kt', '.scala', '.ex', '.exs', '.erl', '.hs',
                    '.php', '.pl', '.pm', '.r', '.m', '.mm',
                    # Config/schema (still source)
                    '.proto', '.graphql', '.gql', '.sql',
                }
                file_count = 0
                for f in item.rglob('*'):
                    if not f.is_file():
                        continue
                    if f.suffix not in SOURCE_EXTENSIONS:
                        continue
                    # Phase A (WS-2 / G-21): Skip files inside ignored sub-dirs
                    path_parts = f.relative_to(item).parts
                    if any(part.lower() in IGNORE_DIRS for part in path_parts[:-1]):
                        continue
                    # Skip test files by name pattern (language-agnostic)
                    fname = f.name
                    if any(fname.endswith(p) for p in (
                        '.spec.ts', '.test.ts', '.spec.js', '.test.js',
                        '.spec.py', '.test.py', '_test.go', '_test.rs',
                        'Test.java', 'Tests.java', 'Spec.java',
                        'Test.kt', 'Tests.kt', '_test.exs',
                    )):
                        continue
                    if fname.startswith('test_') and fname.endswith('.py'):
                        continue
                    file_count += 1

                purpose = self.DIRECTORY_PURPOSES.get(dir_name, "")

                directories.append(DirectoryInfo(
                    name=item.name,
                    path=str(item.relative_to(self._project_root)),
                    file_count=file_count,
                    purpose=purpose,
                ))

        return sorted(directories, key=lambda x: x.file_count, reverse=True)

    # Phase E (G-05 fix): Directories to skip during pattern detection
    # These contain test fixtures, mock data, or non-source files that
    # pollute pattern detection (e.g., Angular fixtures in Python projects)
    PATTERN_IGNORE_SEGMENTS = {
        'node_modules', 'dist', 'build', '.git', '.angular', '.codetrellis',
        '__pycache__', '.pytest_cache', '.venv', 'venv', 'env',
        'tests', 'test', '__tests__', 'fixtures', '__fixtures__',
        '__mocks__', '__snapshots__', 'coverage', '.nyc_output',
        'site-packages', '.tox', '.mypy_cache', '.ruff_cache',
        'htmlcov', 'eggs', '.eggs', 'lsp', 'scripts',
    }

    def _is_pattern_scan_ignored(self, file_path: Path) -> bool:
        """Check if a file path should be skipped during pattern detection.

        Phase E: More aggressive filtering than scanner's DEFAULT_IGNORE
        to prevent test fixtures from contaminating pattern detection.
        """
        path_str = str(file_path)
        parts = Path(path_str).parts
        for part in parts:
            if part in self.PATTERN_IGNORE_SEGMENTS:
                return True
            # Also skip test files by name pattern
            if part.startswith('test_') and part.endswith('.py'):
                return True
            if '.spec.' in part or '.test.' in part:
                return True
        return False

    def _detect_patterns(self) -> List[ArchPattern]:
        """Detect architectural patterns from code.

        Phase E fix: Now uses _is_pattern_scan_ignored() to skip test fixtures,
        __tests__, and fixture directories that previously caused false-positive
        Angular pattern detection in Python-only projects like CodeTrellis.
        """
        patterns: Set[ArchPattern] = set()

        if not self._project_root:
            return list(patterns)

        # Sample some files to detect patterns
        src_dir = self._project_root / "src"
        search_dir = src_dir if src_dir.exists() else self._project_root

        # Limit to first 50 files for performance
        files_checked = 0
        max_files = 50

        for ts_file in search_dir.rglob("*.ts"):
            if files_checked >= max_files:
                break

            # Phase E: Use comprehensive ignore check instead of simple string match
            if self._is_pattern_scan_ignored(ts_file):
                continue

            try:
                content = ts_file.read_text()

                for pattern, indicators in self.PATTERN_INDICATORS.items():
                    for indicator in indicators:
                        if indicator in content:
                            patterns.add(pattern)
                            break

                files_checked += 1
            except Exception:
                continue

        # Check for proto files (gRPC)
        if list(self._project_root.rglob("*.proto")):
            patterns.add(ArchPattern.GRPC)

        return list(patterns)

    def _find_config_files(self) -> List[str]:
        """Find configuration files"""
        config_patterns = [
            "package.json",
            "tsconfig.json",
            "tsconfig.*.json",
            "angular.json",
            "nest-cli.json",
            ".eslintrc*",
            ".prettierrc*",
            "vite.config.*",
            "webpack.config.*",
            "tailwind.config.*",
            "docker-compose.yml",
            "Dockerfile",
            ".env.example",
            ".env.sample",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Package.swift",
            ".swiftlint.yml",
            ".swift-format",
            "Makefile",
        ]

        found = []
        if not self._project_root:
            return found

        for pattern in config_patterns:
            for match in self._project_root.glob(pattern):
                found.append(match.name)

        return sorted(set(found))

    def _find_api_connections(self) -> List[ApiConnectionInfo]:
        """Find external API connections from environment files and services"""
        apis = []

        if not self._project_root:
            return apis

        # Check environment files
        env_files = list(self._project_root.glob(".env*")) + list(self._project_root.glob("*environment*.ts"))

        for env_file in env_files:
            try:
                content = env_file.read_text()

                # Look for API URLs
                url_patterns = [
                    r'(?:API_URL|BASE_URL|BACKEND_URL)\s*[=:]\s*["\']?([^"\'\s]+)',
                    r'apiUrl\s*[=:]\s*["\']([^"\']+)',
                    r'baseUrl\s*[=:]\s*["\']([^"\']+)',
                ]

                for pattern in url_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for url in matches:
                        if url and not url.startswith('$'):
                            # Determine protocol
                            protocol = "http"
                            if "grpc" in url.lower():
                                protocol = "grpc"
                            elif "ws://" in url or "wss://" in url:
                                protocol = "websocket"

                            apis.append(ApiConnectionInfo(
                                name=self._extract_api_name(url),
                                base_url=url,
                                protocol=protocol,
                            ))
            except Exception:
                continue

        return apis

    def _extract_api_name(self, url: str) -> str:
        """Extract a friendly name from an API URL"""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Get first part
        parts = url.split('/')
        name = parts[0].split(':')[0]  # Remove port
        return name.replace('.', '-')

    def _build_tech_stack(self, overview: ProjectOverview) -> List[str]:
        """Build a tech stack list from dependencies and patterns"""
        stack = []

        # Add project type
        if overview.project_type != ProjectType.UNKNOWN:
            stack.append(overview.project_type.value)

        # JS/TS key dependencies
        key_deps = {
            "@ngrx/signals": "NgRx Signals",
            "@ngrx/store": "NgRx Store",
            "rxjs": "RxJS",
            "tailwindcss": "TailwindCSS",
            "socket.io-client": "Socket.IO",
            "@grpc/grpc-js": "gRPC",
            "mongoose": "MongoDB",
            "typeorm": "TypeORM",
            "prisma": "Prisma",
            "graphql": "GraphQL",
            "apollo": "Apollo",
        }

        dep_names = {d.name.lower() for d in overview.dependencies}
        for dep, display_name in key_deps.items():
            if dep.lower() in dep_names:
                stack.append(display_name)

        # v5.0: Go framework names from go.mod dependencies
        go_framework_names = {
            'gin-gonic/gin': 'Gin', 'labstack/echo': 'Echo', 'go-chi/chi': 'Chi',
            'gorilla/mux': 'Gorilla Mux', 'gofiber/fiber': 'Fiber',
            'gorm.io/gorm': 'GORM', 'jinzhu/gorm': 'GORM',
            'gorilla/websocket': 'WebSocket', 'go-redis': 'Redis',
            'jinzhu/configor': 'Configor', 'spf13/viper': 'Viper',
            'urfave/cli': 'CLI', 'spf13/cobra': 'Cobra',
            'golang-jwt/jwt': 'JWT', 'dgrijalva/jwt-go': 'JWT',
            'jmoiron/sqlx': 'sqlx', 'jackc/pgx': 'pgx',
            'go-playground/validator': 'Validator',
            'swaggo/swag': 'Swagger',
            'grpc/grpc-go': 'gRPC',
        }
        if self._project_root:
            go_mod = self._project_root / 'go.mod'
            if go_mod.exists():
                try:
                    go_content = go_mod.read_text(encoding='utf-8')
                    for dep_pattern, display_name in go_framework_names.items():
                        if dep_pattern in go_content and display_name not in stack:
                            stack.append(display_name)
                except (OSError, UnicodeDecodeError):
                    pass

        # v5.0: Python framework names from requirements.txt / pyproject.toml
        python_framework_names = {
            'fastapi': 'FastAPI', 'flask': 'Flask', 'django': 'Django',
            'pytorch': 'PyTorch', 'torch': 'PyTorch', 'tensorflow': 'TensorFlow',
            'transformers': 'HuggingFace', 'langchain': 'LangChain',
            'celery': 'Celery', 'sqlalchemy': 'SQLAlchemy',
            'pydantic': 'Pydantic', 'pandas': 'Pandas',
            'numpy': 'NumPy', 'scipy': 'SciPy',
            'scikit-learn': 'scikit-learn', 'keras': 'Keras',
            'scrapy': 'Scrapy', 'dramatiq': 'Dramatiq',
            'uvicorn': 'Uvicorn', 'gunicorn': 'Gunicorn',
        }
        if self._project_root:
            for req_file in ['requirements.txt', 'requirements.in']:
                req_path = self._project_root / req_file
                if req_path.exists():
                    try:
                        req_content = req_path.read_text(encoding='utf-8').lower()
                        for dep_pattern, display_name in python_framework_names.items():
                            if dep_pattern in req_content and display_name not in stack:
                                stack.append(display_name)
                    except (OSError, UnicodeDecodeError):
                        pass

        # v4.22: Swift framework names from Package.swift
        swift_framework_names = {
            'vapor': 'Vapor', 'Hummingbird': 'Hummingbird',
            'Alamofire': 'Alamofire', 'SwiftNIO': 'SwiftNIO',
            'swift-composable-architecture': 'TCA',
            'Kingfisher': 'Kingfisher', 'SnapKit': 'SnapKit',
            'Moya': 'Moya', 'RxSwift': 'RxSwift',
            'swift-argument-parser': 'ArgumentParser',
            'GRDB': 'GRDB', 'Realm': 'Realm',
            'swift-protobuf': 'SwiftProtobuf',
            'grpc-swift': 'gRPC-Swift',
        }
        if self._project_root:
            pkg_swift = self._project_root / 'Package.swift'
            if pkg_swift.exists():
                try:
                    swift_content = pkg_swift.read_text(encoding='utf-8')
                    for dep_pattern, display_name in swift_framework_names.items():
                        if dep_pattern in swift_content and display_name not in stack:
                            stack.append(display_name)
                    # Check for SwiftUI usage in source files
                    sources_dir = self._project_root / 'Sources'
                    if sources_dir.is_dir():
                        for sf in list(sources_dir.rglob('*.swift'))[:20]:
                            try:
                                sc = sf.read_text(encoding='utf-8')
                                if 'import SwiftUI' in sc and 'SwiftUI' not in stack:
                                    stack.append('SwiftUI')
                                if 'import Combine' in sc and 'Combine' not in stack:
                                    stack.append('Combine')
                            except (OSError, UnicodeDecodeError):
                                pass
                except (OSError, UnicodeDecodeError):
                    pass

        # Add patterns
        pattern_display = {
            ArchPattern.STANDALONE_COMPONENTS: "Standalone Components",
            ArchPattern.SIGNAL_STORE: "Signal Store",
            ArchPattern.ONPUSH_CD: "OnPush CD",
            ArchPattern.LAZY_LOADING: "Lazy Loading",
        }

        for pattern in overview.patterns:
            if pattern in pattern_display:
                stack.append(pattern_display[pattern])

        return stack[:15]  # Limit to top 15 (was 10, expanded for multi-lang)

    def build_project_profile(self, overview: ProjectOverview, discovery_result=None) -> 'ProjectProfile':
        """
        Build multi-dimensional project profile from overview + discovery.

        v5.0: Creates a rich profile that captures all languages, frameworks,
        and facets instead of forcing a single ProjectType classification.
        """
        profile = ProjectProfile(primary_type=overview.project_type.value)

        # Languages from discovery
        if discovery_result:
            profile.languages = [
                {"name": lang.get("name", ""), "percentage": lang.get("percentage", 0),
                 "file_count": lang.get("file_count", 0)}
                for lang in (discovery_result.get("languages", [])
                             if isinstance(discovery_result, dict)
                             else [l.to_dict() for l in getattr(discovery_result, 'languages', [])])
            ]

            # Sub-projects from discovery
            profile.sub_projects = (
                discovery_result.get("sub_projects", [])
                if isinstance(discovery_result, dict)
                else [sp.to_dict() for sp in getattr(discovery_result, 'sub_projects', [])]
            )

        # Build frameworks dict from all known deps
        frameworks: dict = {}
        dep_names = {d.name.lower() for d in overview.dependencies}

        # Check JS/TS frameworks
        js_fw_checks = {
            'react': 'react', '@angular/core': 'angular', 'vue': 'vue',
            '@nestjs/core': 'nestjs', 'express': 'express', 'next': 'next',
            'nuxt': 'nuxt', 'svelte': 'svelte',
        }
        js_frameworks = [fw for dep, fw in js_fw_checks.items() if dep in dep_names]
        if js_frameworks:
            frameworks['javascript'] = js_frameworks

        # Check Go frameworks from go.mod
        if self._project_root:
            go_mod = self._project_root / 'go.mod'
            if go_mod.exists():
                try:
                    go_content = go_mod.read_text(encoding='utf-8')
                    go_fw = []
                    go_fw_checks = {
                        'gin-gonic/gin': 'gin', 'labstack/echo': 'echo',
                        'go-chi/chi': 'chi', 'gorilla/mux': 'gorilla',
                        'gofiber/fiber': 'fiber', 'gorm.io/gorm': 'gorm',
                        'urfave/cli': 'cli', 'spf13/cobra': 'cobra',
                    }
                    for dep_pattern, fw in go_fw_checks.items():
                        if dep_pattern in go_content:
                            go_fw.append(fw)
                    if go_fw:
                        frameworks['go'] = go_fw
                except (OSError, UnicodeDecodeError):
                    pass

        # Check Python frameworks from deps
        py_fw_checks = {
            'fastapi': 'fastapi', 'flask': 'flask', 'django': 'django',
            'celery': 'celery', 'sqlalchemy': 'sqlalchemy',
        }
        py_frameworks = [fw for dep, fw in py_fw_checks.items() if dep in dep_names]

        # =====================================================================
        # Phase 2 — Improvement 4: Discovery-Driven Stack Detection
        # =====================================================================
        # Instead of ad-hoc globbing for sub-project requirements files,
        # use the discovery result's sub_projects to read each sub-project's
        # actual manifest and detect per-sub-project frameworks.
        # This gives provenance: "django (apps/api), next.js (apps/web)".
        sub_project_stacks: Dict[str, List[str]] = {}  # sub_path -> [frameworks]

        if discovery_result and self._project_root:
            sub_projects_list = (
                discovery_result.get("sub_projects", [])
                if isinstance(discovery_result, dict)
                else [sp.to_dict() for sp in getattr(discovery_result, 'sub_projects', [])]
            )

            for sp in sub_projects_list:
                sp_path = sp.get("path", "") if isinstance(sp, dict) else getattr(sp, 'path', '')
                sp_manifest = sp.get("manifest_file", "") if isinstance(sp, dict) else getattr(sp, 'manifest_file', '')
                sp_hints = sp.get("framework_hints", []) if isinstance(sp, dict) else getattr(sp, 'framework_hints', [])
                sp_root = self._project_root / sp_path if sp_path else None

                if not sp_root or not sp_root.is_dir():
                    continue

                sp_detected: List[str] = list(sp_hints)  # Start with discovery's framework_hints

                # Read the sub-project's own manifest for additional framework detection
                try:
                    if sp_manifest == 'package.json':
                        pkg_path = sp_root / 'package.json'
                        if pkg_path.exists():
                            import json
                            with open(pkg_path) as f:
                                pkg_data = json.load(f)
                            sp_deps = set(pkg_data.get('dependencies', {}).keys())
                            sp_deps |= set(pkg_data.get('devDependencies', {}).keys())
                            sp_deps = {d.lower() for d in sp_deps}
                            for dep_key, fw_name in js_fw_checks.items():
                                if dep_key in sp_deps and fw_name not in sp_detected:
                                    sp_detected.append(fw_name)
                            # Also check if root deps missed any JS frameworks
                            for dep_key, fw_name in js_fw_checks.items():
                                if dep_key in sp_deps and fw_name not in (frameworks.get('javascript') or []):
                                    frameworks.setdefault('javascript', []).append(fw_name)

                    elif sp_manifest in ('requirements.txt', 'pyproject.toml'):
                        # Read Python manifest for framework detection
                        sp_dep_names: set = set()
                        req_file = sp_root / 'requirements.txt'
                        if req_file.exists():
                            for line in req_file.read_text(encoding='utf-8').splitlines():
                                line = line.strip()
                                if line and not line.startswith(('#', '-')):
                                    m = re.match(r'^([a-zA-Z0-9_-]+)', line)
                                    if m:
                                        sp_dep_names.add(m.group(1).lower())
                        pyproj_file = sp_root / 'pyproject.toml'
                        if pyproj_file.exists():
                            try:
                                pyproj_content = pyproj_file.read_text(encoding='utf-8')
                                # Simple extraction of dependencies from pyproject.toml
                                for line in pyproj_content.splitlines():
                                    m = re.match(r'^\s*"?([a-zA-Z0-9_-]+)', line)
                                    if m:
                                        sp_dep_names.add(m.group(1).lower())
                            except (OSError, UnicodeDecodeError):
                                pass
                        for dep_key, fw_name in py_fw_checks.items():
                            if dep_key in sp_dep_names and fw_name not in sp_detected:
                                sp_detected.append(fw_name)
                            # Aggregate into root-level Python frameworks
                            if dep_key in sp_dep_names and fw_name not in py_frameworks:
                                py_frameworks.append(fw_name)

                    elif sp_manifest == 'go.mod':
                        go_mod_path = sp_root / 'go.mod'
                        if go_mod_path.exists():
                            go_content = go_mod_path.read_text(encoding='utf-8')
                            go_fw_checks_local = {
                                'gin-gonic/gin': 'gin', 'labstack/echo': 'echo',
                                'go-chi/chi': 'chi', 'gorilla/mux': 'gorilla',
                                'gofiber/fiber': 'fiber', 'gorm.io/gorm': 'gorm',
                            }
                            for dep_pattern, fw in go_fw_checks_local.items():
                                if dep_pattern in go_content:
                                    if fw not in sp_detected:
                                        sp_detected.append(fw)
                                    if fw not in (frameworks.get('go') or []):
                                        frameworks.setdefault('go', []).append(fw)
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, Exception):
                    pass

                if sp_detected:
                    sub_project_stacks[sp_path] = sp_detected

        # Check Swift frameworks from Package.swift
        if self._project_root:
            pkg_swift = self._project_root / 'Package.swift'
            if pkg_swift.exists():
                try:
                    swift_content = pkg_swift.read_text(encoding='utf-8')
                    swift_fw_checks = {
                        'vapor': 'vapor', 'Hummingbird': 'hummingbird',
                        'Alamofire': 'alamofire', 'SwiftNIO': 'swiftnio',
                        'swift-composable-architecture': 'tca',
                        'GRDB': 'grdb', 'Realm': 'realm',
                    }
                    swift_fw = []
                    for dep_pattern, fw in swift_fw_checks.items():
                        if dep_pattern in swift_content:
                            swift_fw.append(fw)
                    if swift_fw:
                        frameworks['swift'] = swift_fw
                except (OSError, UnicodeDecodeError):
                    pass

        # Legacy fallback: if no Python frameworks found from root or discovery,
        # try ad-hoc globbing (kept for repos without proper manifests)
        if not py_frameworks and self._project_root:
            sub_req_files = list(self._project_root.glob('*/requirements*.txt'))
            sub_req_files += list(self._project_root.glob('*/*/requirements*.txt'))
            sub_req_files += list(self._project_root.glob('*/requirements/*.txt'))
            sub_req_files += list(self._project_root.glob('*/*/requirements/*.txt'))
            sub_dep_names_legacy: set = set()
            for req_file in sub_req_files:
                try:
                    for line in req_file.read_text(encoding='utf-8').splitlines():
                        line = line.strip()
                        if line and not line.startswith(('#', '-')):
                            m = re.match(r'^([a-zA-Z0-9_-]+)', line)
                            if m:
                                sub_dep_names_legacy.add(m.group(1).lower())
                except (OSError, UnicodeDecodeError):
                    pass
            py_frameworks = [fw for dep, fw in py_fw_checks.items() if dep in sub_dep_names_legacy]

        if py_frameworks:
            frameworks['python'] = py_frameworks

        profile.frameworks = frameworks

        # Enrich sub_projects with per-sub-project detected stacks
        if sub_project_stacks and profile.sub_projects:
            for sp_entry in profile.sub_projects:
                sp_path = sp_entry.get("path", "") if isinstance(sp_entry, dict) else ""
                if sp_path in sub_project_stacks:
                    if isinstance(sp_entry, dict):
                        sp_entry["detected_frameworks"] = sub_project_stacks[sp_path]

        # Detect facets
        facets = []
        # REST API facet
        if any(d.name.lower() in ('express', 'fastapi', 'flask', '@nestjs/core')
               for d in overview.dependencies):
            facets.append('rest-api')
        if self._project_root and (self._project_root / 'go.mod').exists():
            try:
                go_content = (self._project_root / 'go.mod').read_text(encoding='utf-8')
                if any(fw in go_content for fw in ['gin-gonic', 'echo', 'chi', 'gorilla', 'fiber']):
                    facets.append('rest-api')
            except (OSError, UnicodeDecodeError):
                pass

        # WebSocket facet
        if any(d.name.lower() in ('socket.io-client', 'socket.io', 'ws', '@nestjs/websockets')
               for d in overview.dependencies):
            facets.append('websocket')
        if self._project_root and (self._project_root / 'go.mod').exists():
            try:
                go_content = (self._project_root / 'go.mod').read_text(encoding='utf-8')
                if 'gorilla/websocket' in go_content or 'nhooyr.io/websocket' in go_content:
                    if 'websocket' not in facets:
                        facets.append('websocket')
            except (OSError, UnicodeDecodeError):
                pass

        # Database facet
        db_deps = {'mongoose', 'typeorm', 'prisma', 'sequelize', 'sqlalchemy',
                   'psycopg2', 'pymongo', 'redis', 'pg', 'mysql2'}
        if any(d.name.lower() in db_deps for d in overview.dependencies):
            facets.append('database')
        if self._project_root and (self._project_root / 'go.mod').exists():
            try:
                go_content = (self._project_root / 'go.mod').read_text(encoding='utf-8')
                if any(x in go_content for x in ['gorm.io', 'go-sql-driver', 'lib/pq', 'jackc/pgx', 'go-redis']):
                    if 'database' not in facets:
                        facets.append('database')
            except (OSError, UnicodeDecodeError):
                pass

        # Docker facet
        if self._project_root:
            if ((self._project_root / 'Dockerfile').exists() or
                    (self._project_root / 'docker-compose.yml').exists() or
                    (self._project_root / 'docker-compose.yaml').exists()):
                facets.append('docker')

        # CI/CD facet
        if self._project_root:
            if ((self._project_root / '.github' / 'workflows').is_dir() or
                    (self._project_root / '.gitlab-ci.yml').exists() or
                    (self._project_root / 'Jenkinsfile').exists()):
                facets.append('ci-cd')

        # Auth facet (check for JWT/auth deps)
        auth_deps = {'passport', 'jsonwebtoken', '@nestjs/passport', '@nestjs/jwt',
                     'pyjwt', 'python-jose', 'authlib'}
        if any(d.name.lower() in auth_deps for d in overview.dependencies):
            facets.append('auth')
        if self._project_root and (self._project_root / 'go.mod').exists():
            try:
                go_content = (self._project_root / 'go.mod').read_text(encoding='utf-8')
                if 'golang-jwt' in go_content or 'dgrijalva/jwt-go' in go_content:
                    if 'auth' not in facets:
                        facets.append('auth')
            except (OSError, UnicodeDecodeError):
                pass

        # ML facet
        ml_deps = {'tensorflow', 'torch', 'pytorch', 'transformers', 'langchain',
                   'scikit-learn', 'keras', 'onnx', 'huggingface-hub'}
        if any(d.name.lower() in ml_deps for d in overview.dependencies):
            facets.append('ml')

        # gRPC facet
        if any(d.name.lower() in ('@grpc/grpc-js', 'grpcio', 'grpc') for d in overview.dependencies):
            facets.append('grpc')

        profile.facets = list(dict.fromkeys(facets))  # Deduplicate preserving order

        # --- Test framework detection ---
        testing_info = self._detect_testing(overview, dep_names)
        if testing_info:
            profile.testing = testing_info

        # --- Build system / package manager detection ---
        build_info = self._detect_build_system()
        if build_info:
            profile.build_system = build_info

        # Build human-readable stack summary
        lang_parts = []
        if profile.languages:
            for lang in profile.languages[:3]:
                name = lang.get('name', '')
                if name == 'typescript':
                    lang_parts.append('TypeScript')
                elif name == 'javascript':
                    lang_parts.append('JavaScript')
                else:
                    lang_parts.append(name.capitalize())

        fw_parts = []
        for lang_fws in profile.frameworks.values():
            for fw in lang_fws:
                fw_parts.append(fw.capitalize() if len(fw) > 3 else fw.upper())

        all_parts = lang_parts + fw_parts[:5]
        profile.stack_summary = ' + '.join(all_parts) if all_parts else overview.project_type.value

        return profile

    def _detect_testing(self, overview: ProjectOverview, dep_names: set) -> dict:
        """
        Detect test frameworks, test directories, and test file counts.

        Examines:
        - Dependency files (package.json devDependencies, requirements-test.txt)
        - Config files (jest.config.*, pytest.ini, conftest.py, .nycrc)
        - Test file patterns (*_test.go, test_*.py, *.spec.ts, *.test.ts)
        - Test directories (tests/, test/, __tests__/, spec/)
        """
        frameworks = []
        test_dirs = []
        test_file_count = 0
        config_files = []
        root = self._project_root

        if not root:
            return {}

        # --- 1. Framework detection from deps ---
        # JS/TS test frameworks
        js_test_map = {
            'jest': 'jest', '@jest/core': 'jest', 'ts-jest': 'jest',
            'mocha': 'mocha', 'vitest': 'vitest',
            'jasmine': 'jasmine', '@types/jest': 'jest',
            'cypress': 'cypress', 'playwright': 'playwright',
            '@playwright/test': 'playwright',
            'supertest': 'supertest', 'chai': 'chai',
        }
        # Python test frameworks
        py_test_map = {
            'pytest': 'pytest', 'pytest-cov': 'pytest',
            'pytest-asyncio': 'pytest', 'unittest': 'unittest',
            'nose': 'nose', 'nose2': 'nose2', 'tox': 'tox',
            'httpx': 'httpx (test client)',
        }

        all_dep_names = dep_names | {d.name.lower() for d in overview.dev_dependencies}

        for dep, fw in {**js_test_map, **py_test_map}.items():
            if dep in all_dep_names and fw not in frameworks:
                frameworks.append(fw)

        # --- 2. Config file detection ---
        test_config_files = [
            ('jest.config.js', 'jest'), ('jest.config.ts', 'jest'),
            ('jest.preset.js', 'jest'), ('jest.preset.ts', 'jest'),
            ('.jest.config.js', 'jest'),
            ('vitest.config.ts', 'vitest'), ('vitest.config.js', 'vitest'),
            ('pytest.ini', 'pytest'), ('setup.cfg', 'pytest'),  # setup.cfg may have [tool:pytest]
            ('conftest.py', 'pytest'),
            ('.nycrc', 'nyc'), ('.nycrc.json', 'nyc'),
            ('cypress.config.ts', 'cypress'), ('cypress.config.js', 'cypress'),
            ('playwright.config.ts', 'playwright'), ('playwright.config.js', 'playwright'),
            ('karma.conf.js', 'karma'),
        ]
        for cfg_file, fw in test_config_files:
            if (root / cfg_file).exists():
                config_files.append(cfg_file)
                if fw not in frameworks:
                    frameworks.append(fw)

        # Check pyproject.toml for [tool.pytest.ini_options]
        pyproject_path = root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding='utf-8')
                if '[tool.pytest' in content and 'pytest' not in frameworks:
                    frameworks.append('pytest')
                    config_files.append('pyproject.toml [tool.pytest]')
            except (OSError, UnicodeDecodeError):
                pass

        # --- 3. Go testing (built-in, detected by *_test.go files) ---
        has_go_tests = False
        try:
            for f in root.rglob('*_test.go'):
                rel = str(f.relative_to(root))
                if 'vendor/' not in rel:
                    has_go_tests = True
                    break
        except Exception:
            pass
        if has_go_tests and 'go test' not in frameworks:
            frameworks.append('go test')

        # --- 4. Test directories ---
        test_dir_names = ['tests', 'test', '__tests__', 'spec', 'e2e',
                          'test-utils', 'testing', 'integration-tests']
        for dname in test_dir_names:
            dpath = root / dname
            if dpath.is_dir():
                test_dirs.append(dname)

        # Also check for apps/*/test or libs/*/test (monorepo patterns)
        for mono_dir in ['apps', 'libs', 'packages']:
            mono_path = root / mono_dir
            if mono_path.is_dir():
                try:
                    for child in mono_path.iterdir():
                        if child.is_dir():
                            for td in ['test', 'tests', '__tests__', 'spec']:
                                if (child / td).is_dir():
                                    test_dirs.append(f"{mono_dir}/{child.name}/{td}")
                except Exception:
                    pass

        # --- 5. Count test files ---
        test_patterns = ['*_test.go', 'test_*.py', '*_test.py',
                         '*.spec.ts', '*.test.ts', '*.spec.js', '*.test.js',
                         '*.spec.tsx', '*.test.tsx']
        for pattern in test_patterns:
            try:
                count = sum(1 for _ in root.rglob(pattern)
                            if 'node_modules' not in str(_) and 'vendor/' not in str(_))
                test_file_count += count
            except Exception:
                pass

        if not frameworks and not test_dirs and test_file_count == 0:
            return {}

        result = {}
        if frameworks:
            result['frameworks'] = frameworks
        if test_dirs:
            result['test_dirs'] = test_dirs[:10]  # Cap at 10
        if test_file_count > 0:
            result['test_file_count'] = test_file_count
        if config_files:
            result['config_files'] = config_files

        return result

    def _detect_build_system(self) -> dict:
        """
        Detect build system / package manager from lock files and config.
        """
        root = self._project_root
        if not root:
            return {}

        result = {}

        # Package manager detection (from lock files)
        if (root / 'yarn.lock').exists():
            result['package_manager'] = 'yarn'
        elif (root / 'pnpm-lock.yaml').exists():
            result['package_manager'] = 'pnpm'
        elif (root / 'package-lock.json').exists():
            result['package_manager'] = 'npm'
        elif (root / 'bun.lockb').exists():
            result['package_manager'] = 'bun'

        # Python build system from pyproject.toml [build-system]
        pyproject_path = root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding='utf-8')
                # Look for build-backend
                import re
                backend_match = re.search(
                    r'build-backend\s*=\s*["\']([^"\']+)["\']', content
                )
                if backend_match:
                    backend = backend_match.group(1)
                    # Map backend to friendly name
                    backend_names = {
                        'pdm.backend': 'pdm-backend',
                        'pdm.pep517.api': 'pdm-backend',
                        'hatchling.build': 'hatchling',
                        'flit_core.buildapi': 'flit',
                        'setuptools.build_meta': 'setuptools',
                        'poetry.core.masonry.api': 'poetry',
                        'maturin': 'maturin',
                    }
                    result['build_backend'] = backend_names.get(backend, backend)
            except (OSError, UnicodeDecodeError):
                pass

        # Go modules
        if (root / 'go.mod').exists():
            result['build_tool'] = 'go modules'

        # Cargo
        if (root / 'Cargo.toml').exists():
            result['build_tool'] = 'cargo'

        # Swift Package Manager
        if (root / 'Package.swift').exists():
            result['build_tool'] = 'swift package manager'

        # .NET / C#
        sln_files = list(root.glob('*.sln'))
        if sln_files:
            result['build_tool'] = 'dotnet (solution)'
        elif list(root.glob('*.csproj')):
            result['build_tool'] = 'dotnet (csproj)'

        # Makefile
        if (root / 'Makefile').exists():
            result['has_makefile'] = True

        return result

    def can_extract(self, path: str) -> bool:
        """Check if we can extract from this path"""
        p = Path(path)
        return p.is_dir() and (
            (p / "package.json").exists() or
            (p / "requirements.txt").exists() or
            (p / "pyproject.toml").exists() or
            (p / "go.mod").exists() or
            (p / "Cargo.toml").exists() or
            (p / "Package.swift").exists() or
            (p / "pom.xml").exists() or
            (p / "build.gradle").exists() or
            any(p.glob("*.sln")) or
            any(p.glob("*.csproj"))
        )

    def to_dict(self, overview: ProjectOverview) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return overview.to_dict()

    def to_codetrellis_format(self, overview: ProjectOverview) -> str:
        """Convert to CodeTrellis compact format"""
        return overview.to_codetrellis_format()
