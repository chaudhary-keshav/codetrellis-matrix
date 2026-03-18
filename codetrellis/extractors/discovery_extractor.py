"""
CodeTrellis Discovery Extractor — Phase 1 of v5.0 Universal Scanner
====================================================================

Lightweight pre-pass that runs BEFORE all other extractors.
Discovers:
- Language breakdown (which languages exist and in what proportion)
- Sub-projects (embedded ui/, frontend/, etc.)
- Spec files (OpenAPI, GraphQL schemas, protobuf)
- Config templates (.env.example, config.example.yml)
- README summary for domain classification
- Package descriptions from manifests

All operations are cheap (glob/stat, no AST parsing).
Target: <1 second for repositories up to 100k files.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codetrellis.file_classifier import FileClassifier, GitignoreFilter
from codetrellis.language_config import EXT_TO_LANG, MANIFEST_TO_LANG


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SubProjectInfo:
    """An embedded sub-project discovered inside the main project."""
    path: str                       # Relative path (e.g., "ui/", "frontend/")
    manifest_file: str              # e.g., "package.json", "go.mod", "Cargo.toml"
    languages: List[str] = field(default_factory=list)  # Detected languages
    name: Optional[str] = None     # From manifest (e.g., package.json "name")
    description: Optional[str] = None  # From manifest
    framework_hints: List[str] = field(default_factory=list)  # e.g., ["react", "mobx"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "manifest_file": self.manifest_file,
            "languages": self.languages,
            "name": self.name,
            "description": self.description,
            "framework_hints": self.framework_hints,
        }


@dataclass
class SpecFileInfo:
    """A structured specification file found in the project."""
    path: str                       # Relative path
    spec_type: str                  # "openapi-2.0", "openapi-3.0", "graphql-schema",
                                    # "protobuf", "avro", "thrift", "json-schema"
    format: str                     # "json", "yaml", "proto", "graphql"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "spec_type": self.spec_type,
            "format": self.format,
        }


@dataclass
class ConfigTemplateInfo:
    """A configuration template file found in the project."""
    path: str                       # Relative path
    template_type: str              # "env-example", "yaml-example", "toml-example"
    format: str                     # "env", "yaml", "toml", "ini", "json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "template_type": self.template_type,
            "format": self.format,
        }


@dataclass
class LanguageBreakdown:
    """Language presence detected in the project."""
    name: str                       # "go", "python", "typescript", "java", "rust"
    file_count: int = 0             # Number of files with this language's extensions
    percentage: float = 0.0         # % of total code files
    root_dirs: List[str] = field(default_factory=list)  # Which directories contain this
    manifest: Optional[str] = None  # "go.mod", "pyproject.toml", "Cargo.toml"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "file_count": self.file_count,
            "percentage": round(self.percentage, 1),
            "root_dirs": self.root_dirs,
            "manifest": self.manifest,
        }


@dataclass
class ProjectDiscoveryResult:
    """Result of the discovery pre-pass."""
    # Language breakdown (plural — NOT one ProjectType)
    languages: List[LanguageBreakdown] = field(default_factory=list)
    primary_language: str = "unknown"

    # Sub-projects found
    sub_projects: List[SubProjectInfo] = field(default_factory=list)

    # Spec files found (gold mines)
    spec_files: List[SpecFileInfo] = field(default_factory=list)

    # Config templates found
    config_templates: List[ConfigTemplateInfo] = field(default_factory=list)

    # Manifest files found
    manifest_files: List[str] = field(default_factory=list)

    # README info for domain classification
    readme_summary: Optional[str] = None
    readme_description: Optional[str] = None

    # Package description from manifest
    package_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "languages": [lang.to_dict() for lang in self.languages],
            "primary_language": self.primary_language,
            "sub_projects": [sp.to_dict() for sp in self.sub_projects],
            "spec_files": [sf.to_dict() for sf in self.spec_files],
            "config_templates": [ct.to_dict() for ct in self.config_templates],
            "manifest_files": self.manifest_files,
            "readme_summary": self.readme_summary,
            "readme_description": self.readme_description,
            "package_description": self.package_description,
        }


# =============================================================================
# Discovery Extractor
# =============================================================================

class DiscoveryExtractor:
    """
    Lightweight pre-pass discovery — runs BEFORE all other extractors.

    Only uses glob/stat operations and reads first few hundred bytes
    of manifest files. No AST parsing, no regex on source code.
    """

    # Extension → language mapping (from centralized language_config)
    LANGUAGE_MAP: Dict[str, str] = EXT_TO_LANG

    # Manifest files that indicate a sub-project boundary
    MANIFEST_FILES: List[str] = [
        'package.json', 'go.mod', 'Cargo.toml', 'pyproject.toml',
        'setup.py', 'pom.xml', 'build.gradle', 'build.gradle.kts',
        'Gemfile', 'mix.exs', 'Package.swift', 'pubspec.yaml',
        'composer.json',
    ]

    # Manifest → language (from centralized language_config)
    MANIFEST_LANGUAGE: Dict[str, str] = MANIFEST_TO_LANG

    # JS/TS framework detection from package.json dependencies
    JS_FRAMEWORK_HINTS: Dict[str, str] = {
        'react': 'react',
        'react-dom': 'react',
        'next': 'next',
        'vue': 'vue',
        'nuxt': 'nuxt',
        '@angular/core': 'angular',
        'svelte': 'svelte',
        '@sveltejs/kit': 'sveltekit',
        'solid-js': 'solid',
        'preact': 'preact',
        'ember-source': 'ember',
        '@nestjs/core': 'nestjs',
        'express': 'express',
        'fastify': 'fastify',
        'koa': 'koa',
        'hapi': 'hapi',
        'gatsby': 'gatsby',
        'remix': 'remix',
        'astro': 'astro',
        'mobx': 'mobx',
        'redux': 'redux',
        '@reduxjs/toolkit': 'redux',
        'zustand': 'zustand',
        'recoil': 'recoil',
        'tailwindcss': 'tailwind',
        '@mui/material': 'material-ui',
        'socket.io-client': 'socket.io',
    }

    # Directories to skip
    IGNORE_DIRS: Set[str] = {
        'node_modules', 'dist', 'build', '.git', '.angular',
        '.codetrellis', '__pycache__', '.pytest_cache', '.venv',
        'venv', 'env', 'site-packages', 'coverage', '.nyc_output',
        '.tox', '.mypy_cache', '.ruff_cache', 'htmlcov', 'eggs',
        '.eggs', 'vendor', '.next', '.nuxt', '.svelte-kit',
        'target',  # Rust/Java build output
        '.gradle', '.idea', '.vscode',
    }

    def discover(self, root_path: Path,
                 gitignore_filter: Optional[GitignoreFilter] = None,
                 ) -> ProjectDiscoveryResult:
        """
        Run discovery pre-pass. Must be fast (<1 second for most repos).

        Args:
            root_path: Absolute path to project root
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            ProjectDiscoveryResult with all discovery findings
        """
        root = Path(root_path).resolve()
        result = ProjectDiscoveryResult()
        gi = gitignore_filter

        # 1. Count languages by file extension
        result.languages = self._count_languages(root, gi)
        if result.languages:
            result.primary_language = result.languages[0].name

        # 2. Find sub-projects (embedded package.json, go.mod, etc.)
        result.sub_projects = self._find_sub_projects(root, gi)

        # 3. Find spec files (OpenAPI, GraphQL, protobuf)
        result.spec_files = self._find_spec_files(root, gi)

        # 4. Find config templates (.env.example, config.example.yml)
        result.config_templates = self._find_config_templates(root, gi)

        # 5. Collect manifest files at root
        result.manifest_files = self._find_root_manifests(root)

        # 6. Extract README summary
        result.readme_summary, result.readme_description = self._extract_readme_summary(root)

        # 7. Extract package description from manifest(s)
        result.package_description = self._extract_package_description(
            root, result.sub_projects
        )

        return result

    def _count_languages(self, root: Path,
                         gi: Optional[GitignoreFilter] = None,
                         ) -> List[LanguageBreakdown]:
        """Count files per language by walking the directory tree."""
        counts: Dict[str, int] = {}
        dirs_per_lang: Dict[str, Set[str]] = {}
        total_code_files = 0

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter ignored directories in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in self.IGNORE_DIRS and not d.startswith('.')
                and not (gi and not gi.is_empty and gi.should_ignore(
                    os.path.relpath(os.path.join(dirpath, d), str(root)),
                    is_dir=True))
            ]

            rel_dir = os.path.relpath(dirpath, root)
            top_dir = rel_dir.split(os.sep)[0] if rel_dir != '.' else '.'

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                lang = self.LANGUAGE_MAP.get(ext)
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
                    if lang not in dirs_per_lang:
                        dirs_per_lang[lang] = set()
                    dirs_per_lang[lang].add(top_dir)
                    total_code_files += 1

        if total_code_files == 0:
            return []

        # Find manifests at root level for each language
        manifest_for_lang: Dict[str, str] = {}
        for manifest, lang in self.MANIFEST_LANGUAGE.items():
            if (root / manifest).exists():
                manifest_for_lang[lang] = manifest

        # Build sorted result
        breakdowns = []
        for lang, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            breakdowns.append(LanguageBreakdown(
                name=lang,
                file_count=count,
                percentage=(count / total_code_files) * 100,
                root_dirs=sorted(dirs_per_lang.get(lang, set()))[:10],
                manifest=manifest_for_lang.get(lang),
            ))

        return breakdowns

    # Directories that contain example/sample/demo projects — sub-projects
    # found under these paths are tagged as examples and excluded from the
    # main project profile to avoid false-positive framework/DB detections.
    # Now delegates to unified FileClassifier (Phase 1 systemic improvement).
    EXAMPLE_PARENT_DIRS: Set[str] = FileClassifier.EXAMPLE_DIRS

    def _find_sub_projects(self, root: Path,
                           gi: Optional[GitignoreFilter] = None,
                           ) -> List[SubProjectInfo]:
        """
        Find embedded sub-projects by looking for manifest files in subdirectories.
        Only looks at immediate and one-level-deep subdirectories (not root).
        Sub-projects whose path is under an example/sample directory are excluded.
        """
        sub_projects: List[SubProjectInfo] = []
        seen_paths: Set[str] = set()

        for dirpath, dirnames, filenames in os.walk(root):
            # Don't go too deep — 3 levels max
            rel = os.path.relpath(dirpath, root)
            depth = len(rel.split(os.sep)) if rel != '.' else 0
            if depth > 3:
                dirnames.clear()
                continue

            # Skip root level (that's the main project, not a sub-project)
            if rel == '.':
                # Filter ignored dirs
                dirnames[:] = [
                    d for d in dirnames
                    if d not in self.IGNORE_DIRS and not d.startswith('.')
                    and not (gi and not gi.is_empty and gi.should_ignore(d, is_dir=True))
                ]
                continue

            # Filter ignored dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in self.IGNORE_DIRS and not d.startswith('.')
                and not (gi and not gi.is_empty and gi.should_ignore(
                    os.path.relpath(os.path.join(dirpath, d), str(root)),
                    is_dir=True))
            ]

            # Skip sub-projects inside example/sample directories
            rel_parts = Path(rel).parts
            if any(p.lower() in self.EXAMPLE_PARENT_DIRS for p in rel_parts):
                continue

            for manifest in self.MANIFEST_FILES:
                manifest_path = os.path.join(dirpath, manifest)
                if os.path.isfile(manifest_path):
                    rel_path = os.path.relpath(dirpath, root)
                    if rel_path in seen_paths:
                        continue
                    seen_paths.add(rel_path)

                    info = self._analyze_sub_project(
                        root, Path(dirpath), manifest, Path(manifest_path)
                    )
                    if info:
                        sub_projects.append(info)
                    break  # Only process first manifest per directory

        return sub_projects

    def _analyze_sub_project(
        self, root: Path, project_dir: Path, manifest: str, manifest_path: Path
    ) -> Optional[SubProjectInfo]:
        """Analyze a single sub-project from its manifest file."""
        rel_path = str(project_dir.relative_to(root))
        info = SubProjectInfo(path=rel_path, manifest_file=manifest)

        # Determine languages in this sub-directory (quick scan)
        lang_set: Set[str] = set()
        try:
            for f in project_dir.rglob('*'):
                if f.is_file():
                    ext = f.suffix.lower()
                    lang = self.LANGUAGE_MAP.get(ext)
                    if lang:
                        lang_set.add(lang)
                    if len(lang_set) >= 5:
                        break  # Enough — don't scan entire tree
        except (PermissionError, OSError):
            pass
        info.languages = sorted(lang_set)

        # Parse manifest for name, description, framework hints
        if manifest == 'package.json':
            try:
                data = json.loads(manifest_path.read_text(encoding='utf-8'))
                info.name = data.get('name')
                info.description = data.get('description')
                all_deps = {}
                all_deps.update(data.get('dependencies', {}))
                all_deps.update(data.get('devDependencies', {}))
                for dep_name, hint in self.JS_FRAMEWORK_HINTS.items():
                    if dep_name in all_deps:
                        info.framework_hints.append(hint)
                # Deduplicate
                info.framework_hints = list(dict.fromkeys(info.framework_hints))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass
        elif manifest == 'go.mod':
            try:
                content = manifest_path.read_text(encoding='utf-8')
                module_match = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
                if module_match:
                    info.name = module_match.group(1).split('/')[-1]
            except (OSError, UnicodeDecodeError):
                pass
        elif manifest in ('pyproject.toml', 'setup.py'):
            try:
                content = manifest_path.read_text(encoding='utf-8')
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)', content)
                if name_match:
                    info.name = name_match.group(1)
                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)', content)
                if desc_match:
                    info.description = desc_match.group(1)
            except (OSError, UnicodeDecodeError):
                pass
        elif manifest == 'Cargo.toml':
            try:
                content = manifest_path.read_text(encoding='utf-8')
                name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
                if name_match:
                    info.name = name_match.group(1)
                desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
                if desc_match:
                    info.description = desc_match.group(1)
            except (OSError, UnicodeDecodeError):
                pass
        elif manifest == 'Package.swift':
            try:
                content = manifest_path.read_text(encoding='utf-8')
                name_match = re.search(r'name:\s*"([^"]+)"', content)
                if name_match:
                    info.name = name_match.group(1)
                # Detect Swift frameworks
                swift_framework_hints = {
                    'vapor': 'vapor', 'Vapor': 'vapor',
                    'SwiftUI': 'swiftui',
                    'Hummingbird': 'hummingbird',
                    'Alamofire': 'alamofire',
                    'swift-composable-architecture': 'tca',
                    'Kitura': 'kitura',
                }
                for dep_key, hint in swift_framework_hints.items():
                    if dep_key in content:
                        info.framework_hints.append(hint)
                info.framework_hints = list(dict.fromkeys(info.framework_hints))
            except (OSError, UnicodeDecodeError):
                pass

        return info

    def _find_spec_files(self, root: Path,
                         gi: Optional[GitignoreFilter] = None,
                         ) -> List[SpecFileInfo]:
        """Find OpenAPI, GraphQL, protobuf, and other spec files."""
        specs: List[SpecFileInfo] = []
        seen_paths: Set[str] = set()

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter ignored dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in self.IGNORE_DIRS and not d.startswith('.')
                and not (gi and not gi.is_empty and gi.should_ignore(
                    os.path.relpath(os.path.join(dirpath, d), str(root)),
                    is_dir=True))
            ]

            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root)
                lower_name = filename.lower()

                if rel_path in seen_paths:
                    continue

                # OpenAPI/Swagger files by name convention
                if lower_name in (
                    'swagger.json', 'swagger.yaml', 'swagger.yml',
                    'openapi.json', 'openapi.yaml', 'openapi.yml',
                    'spec.json', 'spec.yaml', 'spec.yml',
                    'api-spec.json', 'api-spec.yaml', 'api-spec.yml',
                ):
                    spec_type = self._detect_openapi_version(full_path, lower_name)
                    if spec_type:
                        fmt = 'json' if lower_name.endswith('.json') else 'yaml'
                        specs.append(SpecFileInfo(
                            path=rel_path,
                            spec_type=spec_type,
                            format=fmt,
                        ))
                        seen_paths.add(rel_path)

                # GraphQL schema files
                elif lower_name.endswith(('.graphql', '.gql', '.graphqls')):
                    specs.append(SpecFileInfo(
                        path=rel_path,
                        spec_type='graphql-schema',
                        format='graphql',
                    ))
                    seen_paths.add(rel_path)

                # Protobuf files (already handled by proto parser, but record for discovery)
                elif lower_name.endswith('.proto'):
                    specs.append(SpecFileInfo(
                        path=rel_path,
                        spec_type='protobuf',
                        format='proto',
                    ))
                    seen_paths.add(rel_path)

                # Avro schema files
                elif lower_name.endswith('.avsc'):
                    specs.append(SpecFileInfo(
                        path=rel_path,
                        spec_type='avro',
                        format='json',
                    ))
                    seen_paths.add(rel_path)

                # Thrift files
                elif lower_name.endswith('.thrift'):
                    specs.append(SpecFileInfo(
                        path=rel_path,
                        spec_type='thrift',
                        format='thrift',
                    ))
                    seen_paths.add(rel_path)

        return specs

    def _detect_openapi_version(self, file_path: str, filename: str) -> Optional[str]:
        """
        Peek at first 500 bytes to detect OpenAPI/Swagger version.
        Returns 'openapi-2.0', 'openapi-3.0', or None if not a valid spec.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                header = f.read(500)

            if '"swagger"' in header or "'swagger'" in header or 'swagger:' in header:
                return 'openapi-2.0'
            elif '"openapi"' in header or "'openapi'" in header or 'openapi:' in header:
                return 'openapi-3.0'
            # spec.json might just be an OpenAPI file without clear version in first 500 bytes
            elif filename in ('spec.json', 'spec.yaml', 'spec.yml'):
                if '"paths"' in header or 'paths:' in header:
                    return 'openapi-2.0'  # Conservative guess
            return None
        except (OSError, UnicodeDecodeError):
            return None

    def _find_config_templates(self, root: Path,
                               gi: Optional[GitignoreFilter] = None,
                               ) -> List[ConfigTemplateInfo]:
        """Find configuration template files."""
        templates: List[ConfigTemplateInfo] = []

        # Patterns to match
        template_patterns = [
            ('.env.example', 'env-example', 'env'),
            ('.env.sample', 'env-example', 'env'),
            ('.env.template', 'env-example', 'env'),
            ('.env.dist', 'env-example', 'env'),
            ('.env.development', 'env-example', 'env'),
            ('.env.production', 'env-example', 'env'),
            ('.env.local.example', 'env-example', 'env'),
        ]

        # Check root level for direct matches
        for pattern, ttype, fmt in template_patterns:
            path = root / pattern
            if path.is_file():
                templates.append(ConfigTemplateInfo(
                    path=pattern,
                    template_type=ttype,
                    format=fmt,
                ))

        # Walk for *.example.yml, *.example.yaml, *.example.toml, etc.
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in self.IGNORE_DIRS and not d.startswith('.')
                and not (gi and not gi.is_empty and gi.should_ignore(
                    os.path.relpath(os.path.join(dirpath, d), str(root)),
                    is_dir=True))
            ]

            # Limit depth to 3
            rel = os.path.relpath(dirpath, root)
            depth = len(rel.split(os.sep)) if rel != '.' else 0
            if depth > 3:
                dirnames.clear()
                continue

            for filename in filenames:
                lower = filename.lower()
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root)

                # Skip if already found at root
                if rel_path in [t.path for t in templates]:
                    continue

                if '.example.' in lower or '.sample.' in lower or '.template.' in lower:
                    if lower.endswith(('.yml', '.yaml')):
                        templates.append(ConfigTemplateInfo(
                            path=rel_path,
                            template_type='yaml-example',
                            format='yaml',
                        ))
                    elif lower.endswith('.toml'):
                        templates.append(ConfigTemplateInfo(
                            path=rel_path,
                            template_type='toml-example',
                            format='toml',
                        ))
                    elif lower.endswith('.json'):
                        templates.append(ConfigTemplateInfo(
                            path=rel_path,
                            template_type='json-example',
                            format='json',
                        ))
                    elif lower.endswith('.ini'):
                        templates.append(ConfigTemplateInfo(
                            path=rel_path,
                            template_type='ini-example',
                            format='ini',
                        ))

        return templates

    def _find_root_manifests(self, root: Path) -> List[str]:
        """Find all manifest files at the project root."""
        found = []
        all_manifests = self.MANIFEST_FILES + [
            'requirements.txt', 'go.sum', 'Cargo.lock',
            'Makefile', 'CMakeLists.txt', 'Dockerfile',
        ]
        for m in all_manifests:
            if (root / m).is_file():
                found.append(m)
        return found

    def _extract_readme_summary(self, root: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Read README.md and extract:
        - summary: first 500 chars
        - description: first paragraph after the title

        Returns:
            (summary, description) tuple
        """
        readme_names = ['README.md', 'readme.md', 'README.rst', 'README.txt', 'README']
        for name in readme_names:
            readme_path = root / name
            if readme_path.is_file():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    summary = content[:500]

                    # Extract description: first non-empty paragraph after # Title
                    description = None
                    lines = content.split('\n')
                    found_title = False
                    desc_lines: List[str] = []

                    for line in lines:
                        stripped = line.strip()
                        if not found_title:
                            if stripped.startswith('#'):
                                found_title = True
                            continue

                        # Skip badges, empty lines, and sub-headers right after title
                        if stripped.startswith('![') or stripped.startswith('[!['):
                            continue
                        if stripped.startswith('>'):
                            # Blockquote could be a description
                            desc_lines.append(stripped.lstrip('> '))
                            continue
                        if stripped.startswith('#'):
                            # Hit next section — stop
                            break
                        if stripped == '' and desc_lines:
                            break  # End of description paragraph
                        if stripped == '':
                            continue
                        desc_lines.append(stripped)

                    if desc_lines:
                        description = ' '.join(desc_lines)[:300]

                    return summary, description
                except (OSError, UnicodeDecodeError):
                    pass

        return None, None

    def _extract_package_description(
        self, root: Path, sub_projects: List[SubProjectInfo]
    ) -> Optional[str]:
        """
        Extract the best project description from manifest files.
        Checks root package.json, pyproject.toml, go.mod, and sub-project descriptions.
        """
        descriptions: List[str] = []

        # Root package.json
        pkg_json = root / 'package.json'
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text(encoding='utf-8'))
                desc = data.get('description', '')
                if desc:
                    descriptions.append(desc)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass

        # Root pyproject.toml
        pyproject = root / 'pyproject.toml'
        if pyproject.is_file():
            try:
                content = pyproject.read_text(encoding='utf-8')
                match = re.search(r'description\s*=\s*["\']([^"\']+)', content)
                if match:
                    descriptions.append(match.group(1))
            except (OSError, UnicodeDecodeError):
                pass

        # Sub-project descriptions
        for sp in sub_projects:
            if sp.description:
                descriptions.append(sp.description)

        # Return the longest description as the most informative
        if descriptions:
            return max(descriptions, key=len)
        return None
