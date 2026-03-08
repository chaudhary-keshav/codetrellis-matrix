"""
PowerShell Model Extractor for CodeTrellis

Extracts data models and configuration patterns from PowerShell source code:
- Module manifests (.psd1)
- DSC node configurations
- Data models (PSCustomObject, hashtables)
- Registry operations
- WMI/CIM queries
- Database operations (SQL Server, etc.)

Supports PowerShell 1.0 through 7.4+ (PowerShell Core / pwsh).
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class PSModuleManifestInfo:
    """Information about a PowerShell module manifest (.psd1)."""
    name: str
    file: str = ""
    line_number: int = 0
    module_version: Optional[str] = None
    guid: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    root_module: Optional[str] = None
    functions_to_export: List[str] = field(default_factory=list)
    cmdlets_to_export: List[str] = field(default_factory=list)
    variables_to_export: List[str] = field(default_factory=list)
    aliases_to_export: List[str] = field(default_factory=list)
    required_modules: List[str] = field(default_factory=list)
    ps_version: Optional[str] = None
    clr_version: Optional[str] = None
    dotnet_version: Optional[str] = None
    compatible_ps_editions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PSDataModelInfo:
    """Information about a data model definition."""
    name: str
    file: str = ""
    line_number: int = 0
    model_type: str = ""  # PSCustomObject, hashtable, ordered, class
    properties: List[str] = field(default_factory=list)
    type_name: Optional[str] = None


@dataclass
class PSRegistryOpInfo:
    """Information about a registry operation."""
    operation: str  # Get, Set, New, Remove, Test
    path: str
    file: str = ""
    line_number: int = 0
    value_name: Optional[str] = None


@dataclass
class PSDSCNodeInfo:
    """Information about a DSC node configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    node_name: str = ""
    resources: List[str] = field(default_factory=list)
    role: Optional[str] = None


class PowerShellModelExtractor:
    """
    Extracts data models and configurations from PowerShell source code.

    Detects:
    - Module manifests (.psd1)
    - PSCustomObject definitions
    - Ordered hashtables
    - Registry operations (Get/Set/New-Item, Get/Set-ItemProperty)
    - WMI/CIM queries
    - SQL queries
    - DSC node configurations
    """

    # Module manifest fields
    MANIFEST_FIELD = re.compile(
        r"(\w+)\s*=\s*(?:['\"]([^'\"]*)['\"]|@\(([^)]*)\)|\$(\w+))",
        re.MULTILINE
    )

    # PSCustomObject
    PSCUSTOMOBJECT_PATTERN = re.compile(
        r'\$(\w+)\s*=\s*\[PSCustomObject\]\s*@\{([^}]+)\}',
        re.DOTALL | re.IGNORECASE
    )

    # New-Object PSObject
    PSOBJECT_PATTERN = re.compile(
        r'\$(\w+)\s*=\s*New-Object\s+-TypeName\s+PSObject',
        re.IGNORECASE
    )

    # Ordered hashtable
    ORDERED_HASHTABLE = re.compile(
        r'\$(\w+)\s*=\s*\[ordered\]\s*@\{([^}]+)\}',
        re.DOTALL | re.IGNORECASE
    )

    # Generic hashtable
    HASHTABLE_PATTERN = re.compile(
        r'\$(\w+)\s*=\s*@\{([^}]+)\}',
        re.DOTALL
    )

    # Registry operations
    REGISTRY_PATTERN = re.compile(
        r'\b(Get|Set|New|Remove|Test)-(?:Item(?:Property)?)\s+'
        r"(?:-Path\s+)?['\"]?(HKLM:|HKCU:|HKCR:|HKU:|HKCC:|Registry::)[^'\";\n]+['\"]?",
        re.IGNORECASE
    )

    # WMI/CIM queries
    WMI_PATTERN = re.compile(
        r'\b(Get-(?:WmiObject|CimInstance))\s+'
        r"(?:-ClassName\s+|-Class\s+)?['\"]?(\w+)['\"]?",
        re.IGNORECASE
    )

    # SQL Server queries
    SQL_PATTERN = re.compile(
        r"Invoke-(?:Sqlcmd|DbaQuery)\s+"
        r"(?:-Query\s+)?['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # Module version from manifest
    MODULE_VERSION_PATTERN = re.compile(
        r"ModuleVersion\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # PowerShellVersion from manifest
    PS_VERSION_PATTERN = re.compile(
        r"PowerShellVersion\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # FunctionsToExport
    FUNCTIONS_EXPORT_PATTERN = re.compile(
        r"FunctionsToExport\s*=\s*(?:@\(([^)]*)\)|['\"]([^'\"]+)['\"])",
        re.IGNORECASE | re.DOTALL
    )

    # RequiredModules
    REQUIRED_MODULES_PATTERN = re.compile(
        r"RequiredModules\s*=\s*@\(([^)]*)\)",
        re.IGNORECASE | re.DOTALL
    )

    # CompatiblePSEditions
    PS_EDITIONS_PATTERN = re.compile(
        r"CompatiblePSEditions\s*=\s*@\(([^)]*)\)",
        re.IGNORECASE | re.DOTALL
    )

    # RootModule
    ROOT_MODULE_PATTERN = re.compile(
        r"RootModule\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # GUID
    GUID_PATTERN = re.compile(
        r"GUID\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # Author
    AUTHOR_PATTERN = re.compile(
        r"Author\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # Description
    DESCRIPTION_PATTERN = re.compile(
        r"Description\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE
    )

    # Tags
    TAGS_PATTERN = re.compile(
        r"Tags\s*=\s*@\(([^)]*)\)",
        re.IGNORECASE | re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all data model patterns from PowerShell source code.

        Returns dict with keys: module_manifests, data_models, registry_ops, dsc_nodes
        """
        module_manifests = []
        if file_path.endswith('.psd1'):
            manifest = self._extract_manifest(content, file_path)
            if manifest:
                module_manifests.append(manifest)

        data_models = self._extract_data_models(content, file_path)
        registry_ops = self._extract_registry_ops(content, file_path)
        dsc_nodes = self._extract_dsc_nodes(content, file_path)

        return {
            'module_manifests': module_manifests,
            'data_models': data_models,
            'registry_ops': registry_ops,
            'dsc_nodes': dsc_nodes,
        }

    def _extract_manifest(self, content: str, file_path: str) -> Optional[PSModuleManifestInfo]:
        """Extract module manifest information from .psd1 file."""
        # Get module name from file path
        import os
        name = os.path.splitext(os.path.basename(file_path))[0]

        manifest = PSModuleManifestInfo(
            name=name,
            file=file_path,
            line_number=1,
        )

        # Module version
        mv = self.MODULE_VERSION_PATTERN.search(content)
        if mv:
            manifest.module_version = mv.group(1)

        # PowerShell version
        pv = self.PS_VERSION_PATTERN.search(content)
        if pv:
            manifest.ps_version = pv.group(1)

        # Root module
        rm = self.ROOT_MODULE_PATTERN.search(content)
        if rm:
            manifest.root_module = rm.group(1)

        # GUID
        gm = self.GUID_PATTERN.search(content)
        if gm:
            manifest.guid = gm.group(1)

        # Author
        am = self.AUTHOR_PATTERN.search(content)
        if am:
            manifest.author = am.group(1)

        # Description
        dm = self.DESCRIPTION_PATTERN.search(content)
        if dm:
            manifest.description = dm.group(1)

        # Functions to export
        fe = self.FUNCTIONS_EXPORT_PATTERN.search(content)
        if fe:
            funcs_str = fe.group(1) or fe.group(2) or ""
            if funcs_str and funcs_str != '*':
                manifest.functions_to_export = [
                    f.strip().strip("'\"") for f in funcs_str.split(',')
                    if f.strip() and f.strip().strip("'\"") != '*'
                ]

        # Required modules
        rq = self.REQUIRED_MODULES_PATTERN.search(content)
        if rq:
            mods_str = rq.group(1)
            manifest.required_modules = [
                m.strip().strip("'\"") for m in mods_str.split(',')
                if m.strip()
            ]

        # Compatible PS editions
        pe = self.PS_EDITIONS_PATTERN.search(content)
        if pe:
            manifest.compatible_ps_editions = [
                e.strip().strip("'\"") for e in pe.group(1).split(',')
                if e.strip()
            ]

        # Tags
        tg = self.TAGS_PATTERN.search(content)
        if tg:
            manifest.tags = [
                t.strip().strip("'\"") for t in tg.group(1).split(',')
                if t.strip()
            ]

        return manifest

    def _extract_data_models(self, content: str, file_path: str) -> List[PSDataModelInfo]:
        """Extract data model definitions."""
        models = []
        seen = set()

        # PSCustomObject
        for match in self.PSCUSTOMOBJECT_PATTERN.finditer(content):
            name = match.group(1)
            body = match.group(2)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:match.start()].count('\n') + 1
            props = [p.strip().split('=')[0].strip() for p in body.split('\n')
                     if '=' in p and p.strip() and not p.strip().startswith('#')]

            models.append(PSDataModelInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                model_type='PSCustomObject',
                properties=props,
            ))

        # Ordered hashtables
        for match in self.ORDERED_HASHTABLE.finditer(content):
            name = match.group(1)
            body = match.group(2)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:match.start()].count('\n') + 1
            props = [p.strip().split('=')[0].strip() for p in body.split('\n')
                     if '=' in p and p.strip() and not p.strip().startswith('#')]

            if len(props) >= 2:  # Only track non-trivial hashtables
                models.append(PSDataModelInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    model_type='ordered',
                    properties=props,
                ))

        return models

    def _extract_registry_ops(self, content: str, file_path: str) -> List[PSRegistryOpInfo]:
        """Extract registry operations."""
        ops = []
        seen = set()

        for match in self.REGISTRY_PATTERN.finditer(content):
            verb = match.group(1)
            full_match = match.group(0)
            line_num = content[:match.start()].count('\n') + 1

            # Extract path
            path_match = re.search(r"['\"]?((?:HKLM:|HKCU:|HKCR:|HKU:|HKCC:|Registry::)[^'\";,\n]+)['\"]?", full_match)
            path = path_match.group(1) if path_match else ""

            key = f"{verb}:{path}"
            if key in seen:
                continue
            seen.add(key)

            ops.append(PSRegistryOpInfo(
                operation=verb,
                path=path,
                file=file_path,
                line_number=line_num,
            ))

        return ops

    def _extract_dsc_nodes(self, content: str, file_path: str) -> List[PSDSCNodeInfo]:
        """Extract DSC node configurations."""
        nodes = []

        # Find Node blocks within Configuration blocks
        config_pattern = re.compile(r'Configuration\s+(\w+)\s*\{', re.IGNORECASE)
        for config_match in config_pattern.finditer(content):
            config_name = config_match.group(1)

            # Find Node blocks
            body = self._extract_brace_block(content, config_match.end() - 1)
            if body:
                node_pattern = re.compile(
                    r'Node\s+(?:\$(\w+)|["\']([^"\']+)["\'])\s*\{',
                    re.IGNORECASE
                )
                for node_match in node_pattern.finditer(body):
                    node_name = node_match.group(1) or node_match.group(2)
                    line_num = content[:config_match.start()].count('\n') + body[:node_match.start()].count('\n') + 1

                    # Find resources within node
                    node_body = self._extract_brace_block(body, node_match.end() - 1)
                    resources = []
                    if node_body:
                        res_pattern = re.compile(r'^\s+(\w+)\s+["\']?\w+["\']?\s*\{', re.MULTILINE)
                        for res_match in res_pattern.finditer(node_body):
                            res_type = res_match.group(1)
                            if res_type not in ('if', 'else', 'foreach', 'switch', 'Import'):
                                resources.append(res_type)

                    nodes.append(PSDSCNodeInfo(
                        name=f"{config_name}:{node_name}",
                        file=file_path,
                        line_number=line_num,
                        node_name=node_name,
                        resources=resources,
                    ))

        return nodes

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within balanced braces."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None
        depth = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            i += 1
        return content[start_pos + 1:]
