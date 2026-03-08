"""
PowerShell Attribute Extractor for CodeTrellis

Extracts import, dependency, and metadata patterns from PowerShell source code:
- using statements (PS 5.0+)
- Import-Module / #Requires statements
- Dot-sourcing (. ./file.ps1)
- Comment-based help blocks
- #Requires statements
- Module dependencies
- PowerShell version detection

Supports PowerShell 1.0 through 7.4+ (PowerShell Core / pwsh).
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PSImportInfo:
    """Information about a module import."""
    module: str
    file: str = ""
    line_number: int = 0
    import_type: str = ""  # Import-Module, using, #Requires, dot-source
    version: Optional[str] = None
    alias: Optional[str] = None
    is_conditional: bool = False


@dataclass
class PSUsingInfo:
    """Information about a using statement (PS 5.0+)."""
    namespace: str
    file: str = ""
    line_number: int = 0
    using_type: str = ""  # namespace, module, assembly


@dataclass
class PSRequiresInfo:
    """Information about a #Requires statement."""
    requirement: str
    file: str = ""
    line_number: int = 0
    requires_type: str = ""  # Version, Modules, PSEdition, RunAsAdministrator, Assembly
    version: Optional[str] = None
    modules: List[str] = field(default_factory=list)


@dataclass
class PSCommentHelpInfo:
    """Information about a comment-based help block."""
    target: str  # function name or 'script'
    file: str = ""
    line_number: int = 0
    synopsis: Optional[str] = None
    description: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    examples: int = 0
    notes: Optional[str] = None
    link: Optional[str] = None


@dataclass
class PSDotSourceInfo:
    """Information about a dot-source reference."""
    path: str
    file: str = ""
    line_number: int = 0
    is_relative: bool = True


class PowerShellAttributeExtractor:
    """
    Extracts import, dependency, and metadata from PowerShell source code.

    Detects:
    - using namespace/module/assembly (PS 5.0+)
    - Import-Module statements
    - #Requires -Module/-Version/-PSEdition/-RunAsAdministrator
    - Dot-sourcing (. ./file.ps1, . $PSScriptRoot/file.ps1)
    - Comment-based help (.SYNOPSIS, .DESCRIPTION, .PARAMETER, .EXAMPLE)
    - PowerShell version from #Requires
    """

    # using statement (PS 5.0+)
    USING_PATTERN = re.compile(
        r'^\s*using\s+(namespace|module|assembly)\s+(.+?)\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    # Import-Module
    IMPORT_MODULE_PATTERN = re.compile(
        r'Import-Module\s+'
        r"(?:-Name\s+)?['\"]?(\w[\w.-]*)['\"]?"
        r"(?:\s+-(?:RequiredVersion|MinimumVersion)\s+['\"]?([^'\"\s]+)['\"]?)?",
        re.IGNORECASE
    )

    # #Requires statement
    REQUIRES_PATTERN = re.compile(
        r'^#Requires\s+(.+?)\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    # #Requires -Version
    REQUIRES_VERSION = re.compile(
        r'-Version\s+(\d+(?:\.\d+)*)',
        re.IGNORECASE
    )

    # #Requires -Modules
    REQUIRES_MODULES = re.compile(
        r'-Modules?\s+(.+?)(?:\s+-|$)',
        re.IGNORECASE
    )

    # #Requires -PSEdition
    REQUIRES_EDITION = re.compile(
        r'-PSEdition\s+(\w+)',
        re.IGNORECASE
    )

    # #Requires -RunAsAdministrator
    REQUIRES_ADMIN = re.compile(
        r'-RunAsAdministrator',
        re.IGNORECASE
    )

    # Dot-sourcing
    DOT_SOURCE_PATTERN = re.compile(
        r'^\s*\.\s+(?:[\$\w]+(?:\\\w+)*[\\/])?["\']?([^"\';\n]+\.ps[m1d]*)["\']?',
        re.MULTILINE
    )

    # Comment-based help block
    COMMENT_HELP_PATTERN = re.compile(
        r'<#(.*?)#>',
        re.DOTALL
    )

    # Individual help keywords
    HELP_SYNOPSIS = re.compile(r'\.SYNOPSIS\s*\n(.*?)(?=\.\w+|\n\s*#>)', re.DOTALL | re.IGNORECASE)
    HELP_DESCRIPTION = re.compile(r'\.DESCRIPTION\s*\n(.*?)(?=\.\w+|\n\s*#>)', re.DOTALL | re.IGNORECASE)
    HELP_PARAMETER = re.compile(r'\.PARAMETER\s+(\w+)', re.IGNORECASE)
    HELP_EXAMPLE = re.compile(r'\.EXAMPLE', re.IGNORECASE)
    HELP_NOTES = re.compile(r'\.NOTES\s*\n(.*?)(?=\.\w+|\n\s*#>)', re.DOTALL | re.IGNORECASE)
    HELP_LINK = re.compile(r'\.LINK\s*\n\s*(.+)', re.IGNORECASE)

    # PowerShell version detection from shebang
    SHEBANG_PATTERN = re.compile(r'^#!/usr/bin/env\s+pwsh|^#!/usr/bin/pwsh', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all attribute/import patterns from PowerShell source code.

        Returns dict with keys: imports, usings, requires, comment_helps, dot_sources, ps_version
        """
        imports = self._extract_imports(content, file_path)
        usings = self._extract_usings(content, file_path)
        requires = self._extract_requires(content, file_path)
        comment_helps = self._extract_comment_help(content, file_path)
        dot_sources = self._extract_dot_sources(content, file_path)
        ps_version = self._detect_ps_version(content, requires)

        return {
            'imports': imports,
            'usings': usings,
            'requires': requires,
            'comment_helps': comment_helps,
            'dot_sources': dot_sources,
            'ps_version': ps_version,
        }

    def _extract_imports(self, content: str, file_path: str) -> List[PSImportInfo]:
        """Extract Import-Module statements."""
        imports = []
        seen = set()

        for match in self.IMPORT_MODULE_PATTERN.finditer(content):
            module = match.group(1)
            version = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            if module in seen:
                continue
            seen.add(module)

            # Check if conditional (inside if/try block)
            pre_lines = content[:match.start()].split('\n')
            is_conditional = False
            for line in reversed(pre_lines[-5:]):
                if re.match(r'\s*(if|try|switch)\s', line):
                    is_conditional = True
                    break

            imports.append(PSImportInfo(
                module=module,
                file=file_path,
                line_number=line_num,
                import_type='Import-Module',
                version=version,
                is_conditional=is_conditional,
            ))

        return imports

    def _extract_usings(self, content: str, file_path: str) -> List[PSUsingInfo]:
        """Extract using statements (PS 5.0+)."""
        usings = []

        for match in self.USING_PATTERN.finditer(content):
            using_type = match.group(1).lower()
            namespace = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            usings.append(PSUsingInfo(
                namespace=namespace,
                file=file_path,
                line_number=line_num,
                using_type=using_type,
            ))

        return usings

    def _extract_requires(self, content: str, file_path: str) -> List[PSRequiresInfo]:
        """Extract #Requires statements."""
        requires = []

        for match in self.REQUIRES_PATTERN.finditer(content):
            req_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            req_type = ""
            version = None
            modules = []

            # Check type
            ver_match = self.REQUIRES_VERSION.search(req_text)
            if ver_match:
                req_type = "Version"
                version = ver_match.group(1)

            mod_match = self.REQUIRES_MODULES.search(req_text)
            if mod_match:
                req_type = "Modules" if not req_type else req_type + ",Modules"
                mods_str = mod_match.group(1)
                modules = [m.strip().strip("'\"") for m in mods_str.split(',') if m.strip()]

            ed_match = self.REQUIRES_EDITION.search(req_text)
            if ed_match:
                req_type = "PSEdition" if not req_type else req_type + ",PSEdition"
                version = ed_match.group(1) if not version else version

            if self.REQUIRES_ADMIN.search(req_text):
                req_type = "RunAsAdministrator" if not req_type else req_type + ",RunAsAdministrator"

            requires.append(PSRequiresInfo(
                requirement=req_text.strip(),
                file=file_path,
                line_number=line_num,
                requires_type=req_type,
                version=version,
                modules=modules,
            ))

        return requires

    def _extract_comment_help(self, content: str, file_path: str) -> List[PSCommentHelpInfo]:
        """Extract comment-based help blocks."""
        helps = []

        for match in self.COMMENT_HELP_PATTERN.finditer(content):
            help_text = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check if there's a .SYNOPSIS tag
            if '.SYNOPSIS' not in help_text.upper() and '.DESCRIPTION' not in help_text.upper():
                continue

            # Determine target (function following this block)
            post_text = content[match.end():match.end() + 200]
            func_match = re.search(r'function\s+([\w-]+)', post_text, re.IGNORECASE)
            target = func_match.group(1) if func_match else 'script'

            synopsis = None
            syn_match = self.HELP_SYNOPSIS.search(help_text)
            if syn_match:
                synopsis = syn_match.group(1).strip()

            description = None
            desc_match = self.HELP_DESCRIPTION.search(help_text)
            if desc_match:
                description = desc_match.group(1).strip()

            parameters = [m.group(1) for m in self.HELP_PARAMETER.finditer(help_text)]
            examples = len(self.HELP_EXAMPLE.findall(help_text))

            notes = None
            notes_match = self.HELP_NOTES.search(help_text)
            if notes_match:
                notes = notes_match.group(1).strip()

            link = None
            link_match = self.HELP_LINK.search(help_text)
            if link_match:
                link = link_match.group(1).strip()

            helps.append(PSCommentHelpInfo(
                target=target,
                file=file_path,
                line_number=line_num,
                synopsis=synopsis,
                description=description,
                parameters=parameters,
                examples=examples,
                notes=notes,
                link=link,
            ))

        return helps

    def _extract_dot_sources(self, content: str, file_path: str) -> List[PSDotSourceInfo]:
        """Extract dot-source references."""
        sources = []

        for match in self.DOT_SOURCE_PATTERN.finditer(content):
            path = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1

            is_relative = not (path.startswith('/') or path.startswith('\\') or
                               ':' in path[:3])

            sources.append(PSDotSourceInfo(
                path=path,
                file=file_path,
                line_number=line_num,
                is_relative=is_relative,
            ))

        return sources

    def _detect_ps_version(self, content: str, requires: List[PSRequiresInfo]) -> str:
        """Detect PowerShell version from #Requires and content analysis."""
        # First check #Requires -Version
        for req in requires:
            if req.version and 'Version' in req.requires_type:
                return req.version

        # Check for PS 7.x / pwsh features
        if self.SHEBANG_PATTERN.search(content):
            return "7.0+"

        # Check for PS 7+ features
        if re.search(r'\?\?=|\?\?(?!=)', content):
            return "7.0+"
        if re.search(r'\?\.\w+', content):
            return "7.0+"
        if re.search(r'ForEach-Object\s+-Parallel', content, re.IGNORECASE):
            return "7.0+"
        if re.search(r'clean\s*\{', content, re.IGNORECASE):
            return "7.4+"

        # Check for PS 5.0+ features
        if re.search(r'^\s*using\s+(?:namespace|module|assembly)', content, re.MULTILINE | re.IGNORECASE):
            return "5.0+"
        if re.search(r'^\s*class\s+\w+', content, re.MULTILINE):
            return "5.0+"
        if re.search(r'^\s*enum\s+\w+', content, re.MULTILINE):
            return "5.0+"

        # Check for PS 3.0+ features
        if re.search(r'\[ordered\]', content, re.IGNORECASE):
            return "3.0+"
        if re.search(r'workflow\s+\w+', content, re.IGNORECASE):
            return "3.0+"

        return ""
