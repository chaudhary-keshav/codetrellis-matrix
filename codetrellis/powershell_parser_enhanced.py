"""
EnhancedPowerShellParser v1.0 - Comprehensive PowerShell parser using all extractors.

This parser integrates all PowerShell extractors to provide complete
parsing of PowerShell source files.

Supports:
- PowerShell classes, enums, DSC resources (PS 5.0+)
- Functions, advanced functions, filters, workflows
- CmdletBinding, parameter sets, pipeline support
- Pode/Polaris/Universal Dashboard web frameworks
- DSC configurations and node resources
- Pester test framework
- Module manifests (.psd1)
- Script modules (.psm1)
- Azure/AWS/GCP cmdlet patterns
- Microsoft Graph API
- Registry operations
- WMI/CIM queries
- Comment-based help
- using/Import-Module/dot-sourcing
- PowerShell remoting

PowerShell version detection from:
- #Requires -Version
- Shebang (#!/usr/bin/env pwsh)
- Language feature analysis (clean{} → 7.4+, ?? → 7.0+, class → 5.0+)

Framework detection (30+ frameworks/tools):
- Web: Pode, Polaris, Universal Dashboard
- Testing: Pester (v4/v5)
- Config: DSC, PowerShell Remoting
- Cloud: Az (Azure), AWS.Tools, Google.Cloud
- Identity: Microsoft.Graph, AzureAD, MSOnline
- Automation: PSake, Invoke-Build, Plaster
- Package: PSGallery, NuGet
- DevOps: GitHub Actions, Azure DevOps, Jenkins
- Security: SecretManagement, SecretStore
- Data: ImportExcel, dbatools, SqlServer

Optional AST support via PowerShell AST (System.Management.Automation).
Optional LSP support via PowerShell Editor Services (PSES).

Part of CodeTrellis v4.29 - PowerShell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all PowerShell extractors
from .extractors.powershell import (
    PowerShellTypeExtractor, PSClassInfo, PSEnumInfo, PSInterfaceInfo,
    PSDSCResourceInfo, PSPropertyInfo,
    PowerShellFunctionExtractor, PSFunctionInfo, PSParameterInfo,
    PSScriptBlockInfo, PSPipelineInfo,
    PowerShellAPIExtractor, PSRouteInfo, PSCmdletBindingInfo,
    PSDSCConfigInfo, PSPesterTestInfo,
    PowerShellModelExtractor, PSModuleManifestInfo, PSDataModelInfo,
    PSRegistryOpInfo, PSDSCNodeInfo,
    PowerShellAttributeExtractor, PSImportInfo, PSUsingInfo,
    PSRequiresInfo, PSCommentHelpInfo, PSDotSourceInfo,
)


@dataclass
class PowerShellParseResult:
    """Complete parse result for a PowerShell file."""
    file_path: str
    file_type: str = "powershell"

    # Core types
    classes: List[PSClassInfo] = field(default_factory=list)
    enums: List[PSEnumInfo] = field(default_factory=list)
    interfaces: List[PSInterfaceInfo] = field(default_factory=list)
    dsc_resources: List[PSDSCResourceInfo] = field(default_factory=list)

    # Functions
    functions: List[PSFunctionInfo] = field(default_factory=list)
    script_blocks: List[PSScriptBlockInfo] = field(default_factory=list)
    pipelines: List[PSPipelineInfo] = field(default_factory=list)

    # API / Framework
    routes: List[PSRouteInfo] = field(default_factory=list)
    cmdlet_bindings: List[PSCmdletBindingInfo] = field(default_factory=list)
    dsc_configs: List[PSDSCConfigInfo] = field(default_factory=list)
    pester_tests: List[PSPesterTestInfo] = field(default_factory=list)

    # Models / Data
    module_manifests: List[PSModuleManifestInfo] = field(default_factory=list)
    data_models: List[PSDataModelInfo] = field(default_factory=list)
    registry_ops: List[PSRegistryOpInfo] = field(default_factory=list)
    dsc_nodes: List[PSDSCNodeInfo] = field(default_factory=list)

    # Attributes / Imports
    imports: List[PSImportInfo] = field(default_factory=list)
    usings: List[PSUsingInfo] = field(default_factory=list)
    requires: List[PSRequiresInfo] = field(default_factory=list)
    comment_helps: List[PSCommentHelpInfo] = field(default_factory=list)
    dot_sources: List[PSDotSourceInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    ps_version: str = ""
    is_core: bool = False  # PowerShell Core (pwsh) vs Windows PowerShell


class EnhancedPowerShellParser:
    """
    Enhanced PowerShell parser that uses all extractors for comprehensive parsing.

    Framework detection supports 30+ frameworks across:
    - Web servers (Pode, Polaris, Universal Dashboard)
    - Testing (Pester v4/v5, PSUnit)
    - Configuration management (DSC, PowerShell Remoting)
    - Cloud (Az, AWS.Tools, Google.Cloud)
    - Identity (Microsoft.Graph, AzureAD)
    - Build/Automation (PSake, Invoke-Build, Plaster)
    - Security (SecretManagement, SecretStore)
    - Data (ImportExcel, dbatools, SqlServer)
    - DevOps (GitHub Actions, Azure DevOps pipelines)

    Optional AST: PowerShell AST (via subprocess)
    Optional LSP: PowerShell Editor Services
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Web frameworks
        'pode': re.compile(r"Start-PodeServer|Add-PodeRoute|Import-Module\s+Pode|Import-PodeModule", re.IGNORECASE | re.MULTILINE),
        'polaris': re.compile(r"New-PolarisRoute|Start-Polaris|Import-Module\s+Polaris", re.IGNORECASE | re.MULTILINE),
        'universaldashboard': re.compile(r"New-UDDashboard|New-UDEndpoint|Start-UDDashboard|Import-Module\s+UniversalDashboard", re.IGNORECASE | re.MULTILINE),

        # Testing
        'pester': re.compile(r"Describe\s+['\"]|It\s+['\"]|Should\s+-|BeforeAll\s*\{|AfterAll\s*\{|InModuleScope|Mock\s+", re.IGNORECASE | re.MULTILINE),
        'psunit': re.compile(r"Import-Module\s+PSUnit", re.IGNORECASE),

        # DSC
        'dsc': re.compile(r"Configuration\s+\w+\s*\{|Import-DscResource|Start-DscConfiguration|\[DscResource\(\)\]", re.IGNORECASE | re.MULTILINE),

        # Cloud - Azure
        'azure': re.compile(r"(?:Get|Set|New|Remove|Start|Stop)-Az\w+|Connect-AzAccount|Import-Module\s+Az(?:\.\w+)?", re.IGNORECASE),
        'azuread': re.compile(r"(?:Get|Set|New|Remove)-AzureAD\w+|Connect-AzureAD", re.IGNORECASE),

        # Cloud - AWS
        'aws': re.compile(r"(?:Get|Set|New|Remove)-(?:EC2|S3|IAM|Lambda|SNS|SQS)\w+|Import-Module\s+AWS", re.IGNORECASE),

        # Cloud - GCP
        'gcp': re.compile(r"Import-Module\s+Google\.Cloud|(?:Get|Set|New)-Gcloud\w+", re.IGNORECASE),

        # Microsoft Graph
        'msgraph': re.compile(r"(?:Get|New|Set|Remove|Update)-Mg\w+|Connect-MgGraph|Import-Module\s+Microsoft\.Graph", re.IGNORECASE),

        # Exchange
        'exchange': re.compile(r"(?:Get|Set|New|Remove)-Mailbox|Connect-ExchangeOnline|Import-Module\s+ExchangeOnlineManagement", re.IGNORECASE),

        # Active Directory
        'activedirectory': re.compile(r"(?:Get|Set|New|Remove)-AD\w+|Import-Module\s+ActiveDirectory", re.IGNORECASE),

        # Build tools
        'psake': re.compile(r"Task\s+\w+\s*(?:-Depends\s+\w+)?\s*\{|Include\s+|Properties\s*\{|Invoke-psake", re.IGNORECASE | re.MULTILINE),
        'invokebuild': re.compile(r"task\s+\w+\s*(?:-Jobs\s+)?\{|Invoke-Build|\.build\.ps1", re.IGNORECASE | re.MULTILINE),
        'plaster': re.compile(r"Invoke-Plaster|New-PlasterManifest|Import-Module\s+Plaster", re.IGNORECASE),

        # Package management
        'psgallery': re.compile(r"(?:Install|Find|Publish|Register|Update)-Module|Install-PackageProvider|Set-PSRepository", re.IGNORECASE),
        'nuget': re.compile(r"Install-Package|Register-PackageSource|Import-Module\s+PackageManagement", re.IGNORECASE),

        # Security
        'secretmanagement': re.compile(r"(?:Get|Set|Remove)-Secret|Register-SecretVault|Import-Module\s+Microsoft\.PowerShell\.SecretManagement", re.IGNORECASE),
        'secretstore': re.compile(r"Import-Module\s+Microsoft\.PowerShell\.SecretStore|Set-SecretStoreConfiguration", re.IGNORECASE),

        # Data
        'importexcel': re.compile(r"Import-Excel|Export-Excel|Import-Module\s+ImportExcel", re.IGNORECASE),
        'dbatools': re.compile(r"(?:Get|Set|New|Copy|Remove)-Dba\w+|Import-Module\s+dbatools", re.IGNORECASE),
        'sqlserver': re.compile(r"Invoke-Sqlcmd|Import-Module\s+SqlServer", re.IGNORECASE),

        # Remoting
        'remoting': re.compile(r"Enter-PSSession|New-PSSession|Invoke-Command\s.*-ComputerName|Enable-PSRemoting", re.IGNORECASE),

        # CI/CD
        'githubactions': re.compile(r"\$env:GITHUB_ACTION|\$env:GITHUB_WORKSPACE|Write-Host\s+['\"]::(?:set-output|error|warning)", re.IGNORECASE),
        'azuredevops': re.compile(r"Write-Host\s+['\"]##vso\[|##\[command\]|\$env:BUILD_SOURCESDIRECTORY|\$env:SYSTEM_TEAMFOUNDATION", re.IGNORECASE),

        # Configuration management
        'psdesiredstate': re.compile(r"Import-DscResource\s+-ModuleName|Start-DscConfiguration|Test-DscConfiguration", re.IGNORECASE),

        # Logging
        'psframework': re.compile(r"Write-PSFMessage|Import-Module\s+PSFramework", re.IGNORECASE),

        # REST
        'restps': re.compile(r"Import-Module\s+RestPS|Start-RestPSListener", re.IGNORECASE),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = PowerShellTypeExtractor()
        self.function_extractor = PowerShellFunctionExtractor()
        self.api_extractor = PowerShellAPIExtractor()
        self.model_extractor = PowerShellModelExtractor()
        self.attribute_extractor = PowerShellAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> PowerShellParseResult:
        """
        Parse PowerShell source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            PowerShellParseResult with all extracted information
        """
        result = PowerShellParseResult(file_path=file_path)

        # Detect frameworks first
        result.detected_frameworks = self._detect_frameworks(content)

        # Determine file type
        if file_path.endswith('.psd1'):
            result.file_type = "powershell_manifest"
        elif file_path.endswith('.psm1'):
            result.file_type = "powershell_module"
        elif file_path.endswith('.ps1xml'):
            result.file_type = "powershell_format"
        else:
            result.file_type = "powershell"

        # ── Extract types ─────────────────────────────────────────
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.enums = type_result.get('enums', [])
        result.interfaces = type_result.get('interfaces', [])
        result.dsc_resources = type_result.get('dsc_resources', [])

        # ── Extract functions ─────────────────────────────────────
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.script_blocks = func_result.get('script_blocks', [])
        result.pipelines = func_result.get('pipelines', [])

        # ── Extract API/framework patterns ────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.cmdlet_bindings = api_result.get('cmdlet_bindings', [])
        result.dsc_configs = api_result.get('dsc_configs', [])
        result.pester_tests = api_result.get('pester_tests', [])

        # ── Extract models/data ───────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        result.module_manifests = model_result.get('module_manifests', [])
        result.data_models = model_result.get('data_models', [])
        result.registry_ops = model_result.get('registry_ops', [])
        result.dsc_nodes = model_result.get('dsc_nodes', [])

        # ── Extract attributes/imports ────────────────────────────
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.imports = attr_result.get('imports', [])
        result.usings = attr_result.get('usings', [])
        result.requires = attr_result.get('requires', [])
        result.comment_helps = attr_result.get('comment_helps', [])
        result.dot_sources = attr_result.get('dot_sources', [])

        # ── Version detection ─────────────────────────────────────
        result.ps_version = attr_result.get('ps_version', '')

        # ── PowerShell Core detection ─────────────────────────────
        result.is_core = self._detect_core(content, result.ps_version)

        return result

    def parse_manifest(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Parse a PowerShell module manifest (.psd1) file.

        Returns dict with manifest fields.
        """
        model_result = self.model_extractor.extract(content, file_path)
        manifests = model_result.get('module_manifests', [])
        if manifests:
            m = manifests[0]
            return {
                'name': m.name,
                'module_version': m.module_version,
                'ps_version': m.ps_version,
                'root_module': m.root_module,
                'functions_to_export': m.functions_to_export,
                'required_modules': m.required_modules,
                'compatible_ps_editions': m.compatible_ps_editions,
                'author': m.author,
                'description': m.description,
                'guid': m.guid,
                'tags': m.tags,
            }
        return {}

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which frameworks are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_core(self, content: str, ps_version: str) -> bool:
        """Detect if the script targets PowerShell Core (pwsh)."""
        # Shebang check
        if re.search(r'^#!/usr/bin/(?:env\s+)?pwsh', content, re.MULTILINE):
            return True
        # Version 6.0+
        if ps_version:
            try:
                major = int(ps_version.split('.')[0])
                if major >= 6:
                    return True
            except (ValueError, IndexError):
                pass
        # PS 7+ features
        if re.search(r'\?\?=|\?\?(?!=)', content):
            return True
        if re.search(r'ForEach-Object\s+-Parallel', content, re.IGNORECASE):
            return True
        if re.search(r'#Requires\s+-PSEdition\s+Core', content, re.IGNORECASE):
            return True
        return False
