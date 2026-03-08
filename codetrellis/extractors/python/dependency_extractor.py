"""
DependencyExtractor - Extracts Python dependencies from Python source code and project files.

This extractor parses:
- Import statements (import x, from x import y)
- requirements.txt files
- pyproject.toml dependencies
- setup.py dependencies
- Pipfile dependencies

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum


class DependencyType(Enum):
    """Types of dependencies."""
    STANDARD_LIBRARY = "stdlib"
    THIRD_PARTY = "third_party"
    LOCAL = "local"
    DEV = "dev"


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str] = field(default_factory=list)  # from x import a, b
    alias: Optional[str] = None  # import x as alias
    is_relative: bool = False
    level: int = 0  # Number of dots for relative imports
    line_number: int = 0


@dataclass
class DependencyInfo:
    """Information about a project dependency."""
    name: str
    version_spec: Optional[str] = None  # e.g., ">=1.0,<2.0"
    extras: List[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.THIRD_PARTY
    source: str = "unknown"  # requirements.txt, pyproject.toml, etc.


class DependencyExtractor:
    """
    Extracts import statements and project dependencies from Python files.

    Handles:
    - import module
    - import module as alias
    - from module import name
    - from module import name as alias
    - from . import module (relative imports)
    - from ..module import name
    - requirements.txt parsing
    - pyproject.toml [project.dependencies]
    - setup.py install_requires
    """

    # Standard library modules (subset of commonly used)
    STDLIB_MODULES = {
        'os', 'sys', 're', 'json', 'datetime', 'time', 'math', 'random',
        'typing', 'collections', 'itertools', 'functools', 'pathlib',
        'abc', 'dataclasses', 'enum', 'io', 'copy', 'pickle', 'sqlite3',
        'threading', 'multiprocessing', 'asyncio', 'concurrent', 'queue',
        'socket', 'http', 'urllib', 'email', 'html', 'xml', 'logging',
        'unittest', 'doctest', 'pdb', 'profile', 'timeit', 'contextlib',
        'warnings', 'traceback', 'inspect', 'dis', 'gc', 'weakref',
        'array', 'struct', 'codecs', 'locale', 'gettext', 'argparse',
        'shutil', 'glob', 'tempfile', 'csv', 'configparser', 'hashlib',
        'hmac', 'secrets', 'uuid', 'decimal', 'fractions', 'statistics',
        'textwrap', 'string', 'difflib', 'heapq', 'bisect', 'operator',
        'types', 'copy', 'pprint', 'reprlib', 'graphlib', 'zlib', 'gzip',
        'bz2', 'lzma', 'zipfile', 'tarfile', 'platform', 'errno', 'signal',
        'select', 'selectors', 'mmap', 'fcntl', 'pty', 'tty', 'subprocess',
        'sched', 'contextvars', 'ast', 'token', 'tokenize', 'keyword',
        '__future__', 'builtins', 'importlib', 'pkgutil', 'modulefinder',
    }

    # Import pattern: import x [as alias]
    IMPORT_PATTERN = re.compile(
        r'^import\s+(\S+)(?:\s+as\s+(\w+))?',
        re.MULTILINE
    )

    # From import pattern: from x import y [as alias]
    FROM_IMPORT_PATTERN = re.compile(
        r'^from\s+(\.*)(\S*)\s+import\s+(.+?)(?:#|$)',
        re.MULTILINE
    )

    # Requirements.txt pattern
    REQUIREMENT_PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+)(?:\[([^\]]+)\])?\s*((?:[<>=!~]+\s*[\d.a-zA-Z*]+,?\s*)*)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the dependency extractor."""
        pass

    def extract_imports(self, content: str) -> List[ImportInfo]:
        """
        Extract import statements from Python content.

        Args:
            content: Python source code

        Returns:
            List of ImportInfo objects
        """
        imports = []

        # Extract 'import x' statements
        for match in self.IMPORT_PATTERN.finditer(content):
            module = match.group(1)
            alias = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            imports.append(ImportInfo(
                module=module,
                alias=alias,
                line_number=line_number
            ))

        # Extract 'from x import y' statements
        for match in self.FROM_IMPORT_PATTERN.finditer(content):
            dots = match.group(1)
            module = match.group(2)
            names_str = match.group(3).strip()
            line_number = content[:match.start()].count('\n') + 1

            is_relative = len(dots) > 0
            level = len(dots)

            # Parse imported names
            names = self._parse_import_names(names_str)

            imports.append(ImportInfo(
                module=module if module else '',
                names=names,
                is_relative=is_relative,
                level=level,
                line_number=line_number
            ))

        return imports

    def _parse_import_names(self, names_str: str) -> List[str]:
        """Parse imported names handling parentheses and multiple lines."""
        # Handle parenthesized imports
        names_str = names_str.strip()
        if names_str.startswith('('):
            names_str = names_str[1:]
        if names_str.endswith(')'):
            names_str = names_str[:-1]

        # Split by comma
        names = []
        for part in names_str.split(','):
            part = part.strip()
            if not part or part.startswith('#'):
                continue

            # Handle 'name as alias'
            if ' as ' in part:
                name = part.split(' as ')[0].strip()
            else:
                name = part

            if name:
                names.append(name)

        return names

    def extract_requirements(self, content: str) -> List[DependencyInfo]:
        """
        Extract dependencies from requirements.txt content.

        Args:
            content: requirements.txt content

        Returns:
            List of DependencyInfo objects
        """
        dependencies = []

        for line in content.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('-'):
                continue

            # Handle -r and -e flags
            if line.startswith('-r ') or line.startswith('-e '):
                continue

            # Parse the requirement
            match = self.REQUIREMENT_PATTERN.match(line)
            if match:
                name = match.group(1)
                extras_str = match.group(2)
                version_spec = match.group(3).strip() if match.group(3) else None

                extras = [e.strip() for e in extras_str.split(',')] if extras_str else []

                dependencies.append(DependencyInfo(
                    name=name,
                    version_spec=version_spec if version_spec else None,
                    extras=extras,
                    source="requirements.txt"
                ))

        return dependencies

    def extract_pyproject_dependencies(self, content: str) -> List[DependencyInfo]:
        """
        Extract dependencies from pyproject.toml content.

        Args:
            content: pyproject.toml content

        Returns:
            List of DependencyInfo objects
        """
        dependencies = []

        # Find [project.dependencies] section
        deps_match = re.search(
            r'\[project\]\s*(?:[^\[]*?)dependencies\s*=\s*\[([^\]]+)\]',
            content,
            re.MULTILINE | re.DOTALL
        )

        if deps_match:
            deps_content = deps_match.group(1)
            dependencies.extend(self._parse_toml_deps(deps_content, "dependencies", DependencyType.THIRD_PARTY))

        # Find [project.optional-dependencies] sections
        optional_match = re.search(
            r'\[project\.optional-dependencies\]\s*([^\[]+)',
            content,
            re.MULTILINE | re.DOTALL
        )

        if optional_match:
            optional_content = optional_match.group(1)
            for group_match in re.finditer(r'(\w+)\s*=\s*\[([^\]]+)\]', optional_content):
                group_name = group_match.group(1)
                group_deps = group_match.group(2)
                dep_type = DependencyType.DEV if group_name in ('dev', 'test', 'testing') else DependencyType.THIRD_PARTY
                dependencies.extend(self._parse_toml_deps(group_deps, f"optional-dependencies.{group_name}", dep_type))

        return dependencies

    def _parse_toml_deps(self, content: str, source: str, dep_type: DependencyType) -> List[DependencyInfo]:
        """Parse dependencies from TOML array format."""
        dependencies = []

        for dep_str in re.findall(r'[\'"]([^"\']+)[\'"]', content):
            match = self.REQUIREMENT_PATTERN.match(dep_str)
            if match:
                name = match.group(1)
                extras_str = match.group(2)
                version_spec = match.group(3).strip() if match.group(3) else None

                extras = [e.strip() for e in extras_str.split(',')] if extras_str else []

                dependencies.append(DependencyInfo(
                    name=name,
                    version_spec=version_spec if version_spec else None,
                    extras=extras,
                    dependency_type=dep_type,
                    source=f"pyproject.toml:{source}"
                ))

        return dependencies

    def classify_imports(self, imports: List[ImportInfo]) -> Dict[str, List[ImportInfo]]:
        """
        Classify imports by type (stdlib, third-party, local).

        Args:
            imports: List of ImportInfo objects

        Returns:
            Dict mapping type to list of imports
        """
        classified = {
            'stdlib': [],
            'third_party': [],
            'local': []
        }

        for imp in imports:
            if imp.is_relative:
                classified['local'].append(imp)
            elif self._is_stdlib(imp.module):
                classified['stdlib'].append(imp)
            else:
                classified['third_party'].append(imp)

        return classified

    def _is_stdlib(self, module: str) -> bool:
        """Check if module is a standard library module."""
        # Get top-level module name
        top_level = module.split('.')[0]
        return top_level in self.STDLIB_MODULES

    def get_unique_modules(self, imports: List[ImportInfo]) -> Set[str]:
        """
        Get unique top-level module names from imports.

        Args:
            imports: List of ImportInfo objects

        Returns:
            Set of unique module names
        """
        modules = set()
        for imp in imports:
            if imp.module:
                top_level = imp.module.split('.')[0]
                modules.add(top_level)
        return modules

    def to_codetrellis_format(self, imports: List[ImportInfo], dependencies: List[DependencyInfo] = None) -> str:
        """
        Convert extracted dependency data to CodeTrellis format.

        Args:
            imports: List of ImportInfo objects
            dependencies: Optional list of DependencyInfo objects

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # Classify imports
        classified = self.classify_imports(imports)

        # Add imports by category
        if classified['stdlib']:
            lines.append("[IMPORTS:STDLIB]")
            modules = sorted(set(imp.module.split('.')[0] for imp in classified['stdlib']))
            lines.append(','.join(modules))
            lines.append("")

        if classified['third_party']:
            lines.append("[IMPORTS:THIRD_PARTY]")
            modules = sorted(set(imp.module.split('.')[0] for imp in classified['third_party']))
            lines.append(','.join(modules))
            lines.append("")

        if classified['local']:
            lines.append("[IMPORTS:LOCAL]")
            for imp in classified['local']:
                dots = '.' * imp.level
                names = ','.join(imp.names) if imp.names else '*'
                lines.append(f"{dots}{imp.module}→{names}")
            lines.append("")

        # Add dependencies if provided
        if dependencies:
            lines.append("[DEPENDENCIES]")
            for dep in dependencies:
                parts = [dep.name]
                if dep.version_spec:
                    parts.append(dep.version_spec)
                if dep.extras:
                    parts.append(f"[{','.join(dep.extras)}]")
                if dep.dependency_type == DependencyType.DEV:
                    parts.append("(dev)")
                lines.append('|'.join(parts))

        return "\n".join(lines)


# Convenience functions
def extract_imports(content: str) -> List[ImportInfo]:
    """Extract import statements from Python content."""
    extractor = DependencyExtractor()
    return extractor.extract_imports(content)


def extract_requirements(content: str) -> List[DependencyInfo]:
    """Extract dependencies from requirements.txt content."""
    extractor = DependencyExtractor()
    return extractor.extract_requirements(content)


def extract_pyproject_dependencies(content: str) -> List[DependencyInfo]:
    """Extract dependencies from pyproject.toml content."""
    extractor = DependencyExtractor()
    return extractor.extract_pyproject_dependencies(content)
