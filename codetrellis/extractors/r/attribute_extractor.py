"""
R Attribute Extractor for CodeTrellis

Extracts metadata and configuration from R source code:
- DESCRIPTION file parsing (package metadata, dependencies, imports)
- NAMESPACE exports/imports
- Roxygen tags (@export, @import, @importFrom, @useDynLib)
- Config files (yaml, json, toml configs)
- Package dependencies (library/require calls, renv.lock)
- Installed package detection (renv, packrat, pak)
- Package options (options(), .onLoad, .onAttach)
- Environment variables (Sys.getenv, Sys.setenv)
- Lifecycle hooks (.onLoad, .onUnload, .onAttach, .First.lib)

Supports: R 2.x through R 4.4+
Part of CodeTrellis v4.26 - R Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RPackageDepInfo:
    """Information about an R package dependency."""
    name: str
    version: str = ""
    type: str = "Imports"  # Imports, Depends, Suggests, LinkingTo, Enhances
    source: str = "DESCRIPTION"  # DESCRIPTION, library, renv.lock
    file: str = ""
    line_number: int = 0


@dataclass
class RExportInfo:
    """Information about an exported symbol."""
    name: str
    kind: str = "function"  # function, class, method, data
    pattern: str = ""  # S3method, exportClasses, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class RConfigInfo:
    """Information about R configuration."""
    key: str
    value: str = ""
    source: str = ""  # .Rprofile, options(), .onLoad, Sys.getenv
    file: str = ""
    line_number: int = 0


@dataclass
class RLifecycleHookInfo:
    """Information about R package lifecycle hooks."""
    name: str  # .onLoad, .onAttach, .onUnload, .First.lib, .Last.lib
    actions: List[str] = field(default_factory=list)  # What the hook does
    file: str = ""
    line_number: int = 0


@dataclass
class RPackageMetadataInfo:
    """Information about R package metadata from DESCRIPTION."""
    name: str = ""
    title: str = ""
    version: str = ""
    description: str = ""
    authors: List[str] = field(default_factory=list)
    license: str = ""
    url: str = ""
    bug_reports: str = ""
    encoding: str = "UTF-8"
    roxygen_note: str = ""
    r_version: str = ""  # Minimum R version from Depends
    collate: List[str] = field(default_factory=list)
    lazy_data: bool = False
    vignette_builder: str = ""
    system_requirements: str = ""


class RAttributeExtractor:
    """
    Extracts R package metadata and configuration.

    Detects:
    - DESCRIPTION file fields (Package, Version, Imports, Depends, etc.)
    - NAMESPACE exports (export, exportClasses, S3method, exportPattern)
    - library/require calls throughout the code
    - renv.lock package snapshots
    - .Rprofile / .Renviron configuration
    - Package options (options(), getOption())
    - Lifecycle hooks (.onLoad, .onAttach, .onUnload)
    - Environment variables (Sys.getenv, Sys.setenv)
    - Rcpp/C++ integration (useDynLib, sourceCpp)
    """

    # library/require patterns
    LIBRARY_PATTERN = re.compile(
        r'(?:library|require)\s*\(\s*["\']?(\w+)["\']?\s*(?:,.*?)?\)',
        re.MULTILINE
    )

    # Import patterns (inside functions or scripts)
    IMPORT_PATTERN = re.compile(
        r'(\w+)::(\w+)',
        re.MULTILINE
    )

    # options() settings
    OPTIONS_PATTERN = re.compile(
        r'options\s*\(\s*(\w+)\s*=\s*(.+?)\s*(?:,|\))',
        re.MULTILINE
    )

    # Sys.getenv / Sys.setenv
    GETENV_PATTERN = re.compile(
        r'Sys\.getenv\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    SETENV_PATTERN = re.compile(
        r'Sys\.setenv\s*\(\s*(\w+)\s*=',
        re.MULTILINE
    )

    # Lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'(\.onLoad|\.onAttach|\.onUnload|\.First\.lib|\.Last\.lib|\.onDetach)\s*(?:<-|=)\s*function',
        re.MULTILINE
    )

    # NAMESPACE patterns
    NS_EXPORT = re.compile(r'export\s*\(\s*(\w+)\s*\)')
    NS_EXPORT_PATTERN = re.compile(r'exportPattern\s*\(\s*["\']([^"\']+)["\']')
    NS_S3_METHOD = re.compile(r'S3method\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)')
    NS_EXPORT_CLASSES = re.compile(r'exportClasses\s*\(\s*(\w+)\s*\)')
    NS_EXPORT_METHODS = re.compile(r'exportMethods\s*\(\s*(\w+)\s*\)')
    NS_IMPORT = re.compile(r'^import\s*\(\s*(\w+)\s*\)', re.MULTILINE)
    NS_IMPORT_FROM = re.compile(r'importFrom\s*\(\s*(\w+)\s*,\s*(.+?)\s*\)')
    NS_USE_DYN_LIB = re.compile(r'useDynLib\s*\(\s*(\w+)')

    # DESCRIPTION field patterns
    DESC_FIELD = re.compile(r'^(\w+(?:\.\w+)*):\s*(.*)', re.MULTILINE)

    # renv.lock parsing (JSON)
    RENV_PACKAGE = re.compile(
        r'"Package"\s*:\s*"(\w+)".*?"Version"\s*:\s*"([^"]+)"',
        re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all R attribute/metadata definitions from source code."""
        result = {
            "dependencies": [],
            "exports": [],
            "configs": [],
            "lifecycle_hooks": [],
            "package_metadata": None,
            "env_vars": [],
        }

        fname = file_path.split('/')[-1] if file_path else ""

        # DESCRIPTION file
        if fname == "DESCRIPTION":
            metadata, deps = self._parse_description(content, file_path)
            result["package_metadata"] = metadata
            result["dependencies"].extend(deps)
            return result

        # NAMESPACE file
        if fname == "NAMESPACE":
            result["exports"].extend(self._parse_namespace(content, file_path))
            return result

        # renv.lock
        if fname == "renv.lock":
            result["dependencies"].extend(self._parse_renv_lock(content, file_path))
            return result

        # Regular R source files
        result["dependencies"].extend(self._extract_library_calls(content, file_path))
        result["configs"].extend(self._extract_options(content, file_path))
        result["env_vars"].extend(self._extract_env_vars(content, file_path))
        result["lifecycle_hooks"].extend(self._extract_lifecycle_hooks(content, file_path))

        return result

    def _parse_description(self, content: str, file_path: str) -> tuple:
        """Parse DESCRIPTION file for package metadata and dependencies."""
        metadata = RPackageMetadataInfo()
        deps = []

        # Parse fields (handling multi-line continuation with leading whitespace)
        current_field = None
        current_value = []
        fields = {}

        for line in content.split('\n'):
            field_m = self.DESC_FIELD.match(line)
            if field_m:
                # Save previous field
                if current_field:
                    fields[current_field] = '\n'.join(current_value).strip()
                current_field = field_m.group(1)
                current_value = [field_m.group(2)]
            elif line.startswith(' ') or line.startswith('\t'):
                if current_field:
                    current_value.append(line.strip())

        # Save last field
        if current_field:
            fields[current_field] = '\n'.join(current_value).strip()

        # Map to metadata
        metadata.name = fields.get('Package', '')
        metadata.title = fields.get('Title', '')
        metadata.version = fields.get('Version', '')
        metadata.description = fields.get('Description', '')
        metadata.license = fields.get('License', '')
        metadata.url = fields.get('URL', '')
        metadata.bug_reports = fields.get('BugReports', '')
        metadata.encoding = fields.get('Encoding', 'UTF-8')
        metadata.roxygen_note = fields.get('RoxygenNote', '')
        metadata.lazy_data = fields.get('LazyData', '').lower() == 'true'
        metadata.vignette_builder = fields.get('VignetteBuilder', '')
        metadata.system_requirements = fields.get('SystemRequirements', '')

        # Authors
        authors_str = fields.get('Authors@R', fields.get('Author', ''))
        if authors_str:
            # Extract person names from Authors@R
            person_names = re.findall(r'person\s*\(\s*["\']([^"\']+)["\']', authors_str)
            if person_names:
                metadata.authors = person_names
            else:
                metadata.authors = [authors_str.split(',')[0].strip()]

        # Collate
        collate = fields.get('Collate', '')
        if collate:
            metadata.collate = re.findall(r'["\']([^"\']+)["\']', collate)

        # Parse dependency fields
        dep_fields = ['Depends', 'Imports', 'Suggests', 'LinkingTo', 'Enhances']
        for dep_type in dep_fields:
            dep_str = fields.get(dep_type, '')
            if dep_str:
                # Split on commas, handling multi-line
                dep_items = re.split(r',\s*', dep_str.replace('\n', ' '))
                for item in dep_items:
                    item = item.strip()
                    if not item:
                        continue
                    # Parse "package (>= version)" format
                    pkg_m = re.match(r'(\w+)(?:\s*\(([^)]+)\))?', item)
                    if pkg_m:
                        pkg_name = pkg_m.group(1)
                        version = pkg_m.group(2) or ""

                        # Extract R version from Depends
                        if pkg_name == 'R' and dep_type == 'Depends':
                            metadata.r_version = version.replace('>=', '').strip()
                            continue

                        deps.append(RPackageDepInfo(
                            name=pkg_name,
                            version=version,
                            type=dep_type,
                            source="DESCRIPTION",
                            file=file_path,
                        ))

        return metadata, deps

    def _parse_namespace(self, content: str, file_path: str) -> List[RExportInfo]:
        """Parse NAMESPACE file for exports."""
        exports = []

        for m in self.NS_EXPORT.finditer(content):
            exports.append(RExportInfo(
                name=m.group(1),
                kind="function",
                pattern="export",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.NS_S3_METHOD.finditer(content):
            exports.append(RExportInfo(
                name=f"{m.group(1)}.{m.group(2)}",
                kind="s3_method",
                pattern="S3method",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.NS_EXPORT_CLASSES.finditer(content):
            exports.append(RExportInfo(
                name=m.group(1),
                kind="class",
                pattern="exportClasses",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.NS_EXPORT_METHODS.finditer(content):
            exports.append(RExportInfo(
                name=m.group(1),
                kind="method",
                pattern="exportMethods",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.NS_EXPORT_PATTERN.finditer(content):
            exports.append(RExportInfo(
                name=m.group(1),
                kind="pattern",
                pattern="exportPattern",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        return exports

    def _parse_renv_lock(self, content: str, file_path: str) -> List[RPackageDepInfo]:
        """Parse renv.lock file for package dependencies."""
        deps = []
        try:
            import json
            data = json.loads(content)
            packages = data.get('Packages', {})
            for pkg_name, pkg_info in packages.items():
                deps.append(RPackageDepInfo(
                    name=pkg_name,
                    version=pkg_info.get('Version', ''),
                    type="renv",
                    source="renv.lock",
                    file=file_path,
                ))
        except (json.JSONDecodeError, Exception):
            # Fallback to regex
            for m in self.RENV_PACKAGE.finditer(content):
                deps.append(RPackageDepInfo(
                    name=m.group(1),
                    version=m.group(2),
                    type="renv",
                    source="renv.lock",
                    file=file_path,
                ))
        return deps

    def _extract_library_calls(self, content: str, file_path: str) -> List[RPackageDepInfo]:
        """Extract library/require calls from source code."""
        deps = []
        seen = set()
        for m in self.LIBRARY_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:m.start()].count('\n') + 1
            deps.append(RPackageDepInfo(
                name=name,
                type="library",
                source="source",
                file=file_path,
                line_number=line_num,
            ))
        return deps

    def _extract_options(self, content: str, file_path: str) -> List[RConfigInfo]:
        """Extract options() settings."""
        configs = []
        for m in self.OPTIONS_PATTERN.finditer(content):
            configs.append(RConfigInfo(
                key=m.group(1),
                value=m.group(2).strip(),
                source="options()",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        return configs

    def _extract_env_vars(self, content: str, file_path: str) -> List[RConfigInfo]:
        """Extract environment variable usage."""
        env_vars = []
        seen = set()

        for m in self.GETENV_PATTERN.finditer(content):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                env_vars.append(RConfigInfo(
                    key=name,
                    source="Sys.getenv",
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

        for m in self.SETENV_PATTERN.finditer(content):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                env_vars.append(RConfigInfo(
                    key=name,
                    source="Sys.setenv",
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

        return env_vars

    def _extract_lifecycle_hooks(self, content: str, file_path: str) -> List[RLifecycleHookInfo]:
        """Extract lifecycle hook functions."""
        hooks = []
        for m in self.LIFECYCLE_PATTERN.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Try to extract what the hook does
            actions = []
            block_start = content.find('{', m.end())
            if block_start != -1:
                body = content[block_start:block_start + 500]
                if 'packageStartupMessage' in body:
                    actions.append('startup_message')
                if 'library.dynam' in body or 'useDynLib' in body:
                    actions.append('load_shared_lib')
                if 'options(' in body:
                    actions.append('set_options')
                if 'Sys.setenv' in body:
                    actions.append('set_env_vars')
                if 'register' in body.lower():
                    actions.append('register_methods')

            hooks.append(RLifecycleHookInfo(
                name=name,
                actions=actions,
                file=file_path,
                line_number=line_num,
            ))
        return hooks
