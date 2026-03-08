"""
Tests for PowerShellModelExtractor — manifests, data models, registry ops, DSC nodes.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.extractors.powershell.model_extractor import (
    PowerShellModelExtractor,
    PSModuleManifestInfo,
    PSDataModelInfo,
    PSRegistryOpInfo,
    PSDSCNodeInfo,
)


@pytest.fixture
def extractor():
    return PowerShellModelExtractor()


class TestManifestExtraction:
    """Tests for module manifest (.psd1) extraction."""

    def test_module_manifest(self, extractor):
        code = '''
@{
    RootModule = 'MyModule.psm1'
    ModuleVersion = '2.1.0'
    GUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    Author = 'John Doe'
    CompanyName = 'Contoso'
    Description = 'A sample PowerShell module for user management'
    PowerShellVersion = '5.1'
    CompatiblePSEditions = @('Desktop', 'Core')
    FunctionsToExport = @('Get-User', 'Set-User', 'New-User', 'Remove-User')
    CmdletsToExport = @()
    AliasesToExport = @()
    RequiredModules = @('ActiveDirectory', 'Microsoft.PowerShell.SecretManagement')
    PrivateData = @{
        PSData = @{
            Tags = @('UserManagement', 'ActiveDirectory', 'Identity')
            LicenseUri = 'https://github.com/contoso/MyModule/blob/main/LICENSE'
            ProjectUri = 'https://github.com/contoso/MyModule'
        }
    }
}
'''
        result = extractor.extract(code, "MyModule.psd1")
        manifests = result.get('module_manifests', [])
        assert len(manifests) >= 1
        m = manifests[0]
        assert m.module_version == "2.1.0"
        assert "Get-User" in m.functions_to_export
        assert "ActiveDirectory" in m.required_modules


class TestDataModelExtraction:
    """Tests for PSCustomObject and data model extraction."""

    def test_pscustomobject(self, extractor):
        code = '''
$user = [PSCustomObject]@{
    UserName = "john.doe"
    Email = "john@example.com"
    Department = "Engineering"
    IsActive = $true
}

$report = [PSCustomObject]@{
    Date = Get-Date
    TotalUsers = 150
    ActiveUsers = 120
}
'''
        result = extractor.extract(code, "models.ps1")
        models = result.get('data_models', [])
        assert len(models) >= 1

    def test_ordered_hashtable(self, extractor):
        code = '''
$config = [ordered]@{
    ServerName = "web01"
    Port = 443
    SSLEnabled = $true
    MaxConnections = 1000
}
'''
        result = extractor.extract(code, "config.ps1")
        models = result.get('data_models', [])
        assert len(models) >= 1


class TestRegistryOpExtraction:
    """Tests for registry operation extraction."""

    def test_registry_operations(self, extractor):
        code = '''
# Read registry
$value = Get-ItemProperty -Path "HKLM:\\SOFTWARE\\MyApp" -Name "Version"

# Write registry
Set-ItemProperty -Path "HKLM:\\SOFTWARE\\MyApp" -Name "LastRun" -Value (Get-Date)

# Create key
New-Item -Path "HKLM:\\SOFTWARE\\MyApp\\Settings" -Force

# Remove key
Remove-ItemProperty -Path "HKLM:\\SOFTWARE\\MyApp" -Name "OldSetting"
'''
        result = extractor.extract(code, "registry.ps1")
        reg_ops = result.get('registry_ops', [])
        assert len(reg_ops) >= 1


class TestDSCNodeExtraction:
    """Tests for DSC node extraction."""

    def test_dsc_nodes(self, extractor):
        code = '''
Configuration ServerConfig {
    Node "WebServer01" {
        WindowsFeature IIS {
            Ensure = "Present"
            Name = "Web-Server"
        }
    }

    Node "DBServer01" {
        SqlServerSetup InstallSQL {
            InstanceName = "MSSQLSERVER"
            Features = "SQLENGINE"
        }
    }

    Node $AllNodes.NodeName {
        File ConfigFile {
            DestinationPath = "C:\\Config\\app.json"
            Ensure = "Present"
        }
    }
}
'''
        result = extractor.extract(code, "servers.ps1")
        nodes = result.get('dsc_nodes', [])
        assert len(nodes) >= 1
