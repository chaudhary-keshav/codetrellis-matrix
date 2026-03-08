"""
Config Extractor for Project Configuration Files

Extracts configuration from various project files:
- package.json (name, version, scripts, dependencies)
- tsconfig.json (compiler options, paths)
- angular.json (project configuration)
- environment.ts files (API URLs, feature flags)
- .env files (environment variables)

Part of CodeTrellis v2.0 - Phase 2 Context Enrichment
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class PackageInfo:
    """Information from package.json"""
    name: str = ""
    version: str = ""
    description: str = ""
    scripts: Dict[str, str] = field(default_factory=dict)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    engines: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'scripts': self.scripts,
            'dependencyCount': len(self.dependencies),
            'devDependencyCount': len(self.dev_dependencies),
            'engines': self.engines,
        }

    def get_key_deps(self) -> List[str]:
        """Get key framework dependencies"""
        key_patterns = [
            '@angular', '@nestjs', 'react', 'vue', 'express',
            'fastapi', 'django', 'socket.io', 'rxjs', '@ngrx',
            'prisma', 'mongoose', 'typeorm', 'graphql'
        ]
        key_deps = []
        for dep in self.dependencies:
            for pattern in key_patterns:
                if pattern in dep.lower():
                    version = self.dependencies[dep]
                    key_deps.append(f"{dep}:{version}")
                    break
        return key_deps


@dataclass
class TSConfigInfo:
    """Information from tsconfig.json"""
    compiler_options: Dict[str, Any] = field(default_factory=dict)
    paths: Dict[str, List[str]] = field(default_factory=dict)
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    strict_mode: bool = False
    target: str = ""
    module: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'target': self.target,
            'module': self.module,
            'strictMode': self.strict_mode,
            'paths': self.paths,
            'include': self.include,
            'exclude': self.exclude,
        }


@dataclass
class EnvironmentConfig:
    """Information from environment files"""
    file_path: str = ""
    api_urls: Dict[str, str] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    config_values: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'filePath': self.file_path,
            'apiUrls': self.api_urls,
            'featureFlags': self.feature_flags,
            'configCount': len(self.config_values),
        }


@dataclass
class AngularConfig:
    """Information from angular.json"""
    project_name: str = ""
    project_type: str = ""
    prefix: str = ""
    styles: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'projectName': self.project_name,
            'projectType': self.project_type,
            'prefix': self.prefix,
            'styles': self.styles,
        }


@dataclass
class ProjectConfigInfo:
    """Complete configuration information for a project"""
    project_path: str
    package_info: Optional[PackageInfo] = None
    tsconfig: Optional[TSConfigInfo] = None
    angular_config: Optional[AngularConfig] = None
    environments: List[EnvironmentConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'projectPath': self.project_path,
            'package': self.package_info.to_dict() if self.package_info else None,
            'tsconfig': self.tsconfig.to_dict() if self.tsconfig else None,
            'angular': self.angular_config.to_dict() if self.angular_config else None,
            'environments': [e.to_dict() for e in self.environments],
        }

    def get_summary(self) -> str:
        """Get a compressed summary for prompt injection"""
        parts = []

        if self.package_info:
            parts.append(f"{self.package_info.name}@{self.package_info.version}")
            key_deps = self.package_info.get_key_deps()
            if key_deps:
                parts.append(f"deps:[{','.join(key_deps[:5])}]")

        if self.tsconfig:
            parts.append(f"ts:{self.tsconfig.target}")
            if self.tsconfig.strict_mode:
                parts.append("strict")

        if self.angular_config:
            parts.append(f"ng:{self.angular_config.prefix}")

        if self.environments:
            env_names = [Path(e.file_path).stem for e in self.environments]
            parts.append(f"envs:[{','.join(env_names)}]")

        return "|".join(parts)


class ConfigExtractor:
    """
    Extracts configuration from project files.

    Example:
        extractor = ConfigExtractor()
        config = extractor.extract_project("/path/to/project")
        print(config.package_info.name)
    """

    # Pattern to match environment variable assignments in TS
    ENV_PATTERN = re.compile(
        r"(\w+)\s*[:=]\s*['\"]?([^'\";\n,}]+)['\"]?",
        re.MULTILINE
    )

    # Pattern to detect API URLs
    API_URL_PATTERN = re.compile(
        r"(api|backend|server|base|endpoint|url|host)['\"]?\s*[:=]\s*['\"]?(https?://[^'\";\n,}]+|/api[^'\";\n,}]*)['\"]?",
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract_package_json(self, file_path: str) -> Optional[PackageInfo]:
        """Extract information from package.json"""
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding='utf-8'))

            return PackageInfo(
                name=data.get('name', ''),
                version=data.get('version', ''),
                description=data.get('description', ''),
                scripts=data.get('scripts', {}),
                dependencies=data.get('dependencies', {}),
                dev_dependencies=data.get('devDependencies', {}),
                engines=data.get('engines', {}),
            )
        except (json.JSONDecodeError, Exception):
            return None

    def extract_tsconfig(self, file_path: str) -> Optional[TSConfigInfo]:
        """Extract information from tsconfig.json"""
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            # Handle comments in tsconfig (strip them)
            content = path.read_text(encoding='utf-8')
            # Remove single-line comments
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            # Remove trailing commas (common in tsconfig)
            content = re.sub(r',(\s*[}\]])', r'\1', content)

            data = json.loads(content)
            compiler_opts = data.get('compilerOptions', {})

            return TSConfigInfo(
                compiler_options=compiler_opts,
                paths=compiler_opts.get('paths', {}),
                include=data.get('include', []),
                exclude=data.get('exclude', []),
                strict_mode=compiler_opts.get('strict', False),
                target=compiler_opts.get('target', ''),
                module=compiler_opts.get('module', ''),
            )
        except (json.JSONDecodeError, Exception):
            return None

    def extract_angular_json(self, file_path: str) -> Optional[AngularConfig]:
        """Extract information from angular.json"""
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            projects = data.get('projects', {})

            if not projects:
                return None

            # Get the first (usually main) project
            project_name = list(projects.keys())[0]
            project = projects[project_name]

            architect = project.get('architect', {})
            build_options = architect.get('build', {}).get('options', {})

            return AngularConfig(
                project_name=project_name,
                project_type=project.get('projectType', ''),
                prefix=project.get('prefix', 'app'),
                styles=build_options.get('styles', []),
                assets=build_options.get('assets', []),
            )
        except (json.JSONDecodeError, Exception):
            return None

    def extract_environment(self, file_path: str) -> Optional[EnvironmentConfig]:
        """Extract information from environment.ts files"""
        path = Path(file_path)
        if not path.exists():
            return None

        content = path.read_text(encoding='utf-8', errors='ignore')
        result = EnvironmentConfig(file_path=file_path)

        # Extract API URLs
        for match in self.API_URL_PATTERN.finditer(content):
            key = match.group(1).lower()
            value = match.group(2)
            result.api_urls[key] = value

        # Extract feature flags (boolean values)
        for match in re.finditer(r"(\w+)\s*[:=]\s*(true|false)", content, re.IGNORECASE):
            key = match.group(1)
            value = match.group(2).lower() == 'true'
            result.feature_flags[key] = value

        # Extract other config values
        for match in self.ENV_PATTERN.finditer(content):
            key = match.group(1)
            value = match.group(2).strip()
            if key not in result.api_urls and key not in result.feature_flags:
                result.config_values[key] = value

        return result

    def extract_project(self, project_path: str) -> ProjectConfigInfo:
        """
        Extract all configuration from a project.

        Args:
            project_path: Root path of the project

        Returns:
            ProjectConfigInfo with all configuration
        """
        project = Path(project_path)
        result = ProjectConfigInfo(project_path=project_path)

        # Extract package.json
        package_path = project / 'package.json'
        if package_path.exists():
            result.package_info = self.extract_package_json(str(package_path))

        # Extract tsconfig.json
        for tsconfig_name in ['tsconfig.json', 'tsconfig.app.json', 'tsconfig.base.json']:
            tsconfig_path = project / tsconfig_name
            if tsconfig_path.exists():
                result.tsconfig = self.extract_tsconfig(str(tsconfig_path))
                break

        # Extract angular.json
        angular_path = project / 'angular.json'
        if angular_path.exists():
            result.angular_config = self.extract_angular_json(str(angular_path))

        # Extract environment files
        env_paths = [
            project / 'src' / 'environments' / 'environment.ts',
            project / 'src' / 'environments' / 'environment.prod.ts',
            project / 'src' / 'environments' / 'environment.development.ts',
            project / 'src' / 'environment.ts',
            project / '.env',
            project / '.env.local',
        ]

        for env_path in env_paths:
            if env_path.exists():
                env_config = self.extract_environment(str(env_path))
                if env_config:
                    result.environments.append(env_config)

        return result


# Convenience functions
def extract_project_config(project_path: str) -> ProjectConfigInfo:
    """
    Extract all configuration from a project.

    Args:
        project_path: Root path of the project

    Returns:
        ProjectConfigInfo with all configuration
    """
    extractor = ConfigExtractor()
    return extractor.extract_project(project_path)


def extract_package_json(file_path: str) -> Optional[PackageInfo]:
    """Extract information from package.json"""
    extractor = ConfigExtractor()
    return extractor.extract_package_json(file_path)
