"""
Tests for EnhancedPowerShellParser — integration test across all extractors.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.powershell_parser_enhanced import (
    EnhancedPowerShellParser,
    PowerShellParseResult,
)


@pytest.fixture
def parser():
    return EnhancedPowerShellParser()


class TestFrameworkDetection:
    """Tests for PowerShell framework detection."""

    def test_pode_detection(self, parser):
        code = '''
Start-PodeServer {
    Add-PodeEndpoint -Address * -Port 8080 -Protocol Http
    Add-PodeRoute -Method Get -Path '/api/users' -ScriptBlock {
        Write-PodeJsonResponse -Value @{ users = @() }
    }
}
'''
        result = parser.parse(code, "server.ps1")
        assert "pode" in result.detected_frameworks

    def test_pester_detection(self, parser):
        code = '''
Describe "Calculator" {
    It "adds numbers" {
        2 + 2 | Should -Be 4
    }
    It "subtracts numbers" {
        5 - 3 | Should -Be 2
    }
}
'''
        result = parser.parse(code, "calc.Tests.ps1")
        assert "pester" in result.detected_frameworks

    def test_dsc_detection(self, parser):
        code = '''
Configuration WebServerSetup {
    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Node "Server01" {
        WindowsFeature IIS {
            Ensure = "Present"
            Name = "Web-Server"
        }
    }
}
'''
        result = parser.parse(code, "dsc_config.ps1")
        assert "dsc" in result.detected_frameworks

    def test_azure_detection(self, parser):
        code = '''
Connect-AzAccount
$rg = New-AzResourceGroup -Name "TestRG" -Location "East US"
$vm = Get-AzVM -ResourceGroupName "TestRG"
'''
        result = parser.parse(code, "azure.ps1")
        assert "azure" in result.detected_frameworks

    def test_aws_detection(self, parser):
        code = '''
Get-EC2Instance -InstanceId "i-12345"
New-S3Bucket -BucketName "test-bucket"
'''
        result = parser.parse(code, "aws.ps1")
        assert "aws" in result.detected_frameworks

    def test_msgraph_detection(self, parser):
        code = '''
Connect-MgGraph -Scopes "User.Read.All"
$users = Get-MgUser -All
'''
        result = parser.parse(code, "graph.ps1")
        assert "msgraph" in result.detected_frameworks

    def test_psake_detection(self, parser):
        code = '''
Task Build -Depends Clean {
    exec { dotnet build }
}

Task Clean {
    Remove-Item ./bin -Recurse -Force
}

Task Test -Depends Build {
    exec { dotnet test }
}
'''
        result = parser.parse(code, "build.ps1")
        assert "psake" in result.detected_frameworks

    def test_secretmanagement_detection(self, parser):
        code = '''
Import-Module Microsoft.PowerShell.SecretManagement
Register-SecretVault -Name "MyVault" -ModuleName "Az.KeyVault"
$secret = Get-Secret -Name "DbPassword" -AsPlainText
'''
        result = parser.parse(code, "secrets.ps1")
        assert "secretmanagement" in result.detected_frameworks

    def test_remoting_detection(self, parser):
        code = '''
$session = New-PSSession -ComputerName "Server01"
Invoke-Command -Session $session -ScriptBlock {
    Get-Service | Where-Object Status -eq Running
}
Remove-PSSession $session
'''
        result = parser.parse(code, "remoting.ps1")
        assert "remoting" in result.detected_frameworks

    def test_multiple_frameworks(self, parser):
        code = '''
Import-Module Az.Accounts
Import-Module Microsoft.PowerShell.SecretManagement

Connect-AzAccount
$secret = Get-Secret -Name "AzureServicePrincipal"
$vms = Get-AzVM -ResourceGroupName "Production"
'''
        result = parser.parse(code, "multi.ps1")
        assert len(result.detected_frameworks) >= 2


class TestPowerShellCoreDetection:
    """Tests for PowerShell Core detection."""

    def test_shebang_pwsh(self, parser):
        code = '''#!/usr/bin/env pwsh
Write-Host "Hello from pwsh"
'''
        result = parser.parse(code, "script.ps1")
        assert result.is_core is True

    def test_requires_core_edition(self, parser):
        code = '''
#Requires -PSEdition Core
Write-Host "Core only"
'''
        result = parser.parse(code, "core.ps1")
        assert result.is_core is True

    def test_null_coalescing_operator(self, parser):
        code = '''
$value = $null
$result = $value ?? "default"
'''
        result = parser.parse(code, "ps7.ps1")
        assert result.is_core is True

    def test_foreach_parallel(self, parser):
        code = '''
1..10 | ForEach-Object -Parallel {
    Start-Sleep -Seconds 1
    $_
} -ThrottleLimit 5
'''
        result = parser.parse(code, "parallel.ps1")
        assert result.is_core is True


class TestFileTypeDetection:
    """Tests for file type detection."""

    def test_ps1_file(self, parser):
        result = parser.parse("Write-Host 'test'", "script.ps1")
        assert result.file_type == "powershell"

    def test_psm1_file(self, parser):
        result = parser.parse("function Get-Data { }", "MyModule.psm1")
        assert result.file_type == "powershell_module"

    def test_psd1_file(self, parser):
        code = "@{ ModuleVersion = '1.0.0' }"
        result = parser.parse(code, "MyModule.psd1")
        assert result.file_type == "powershell_manifest"


class TestParseManifest:
    """Tests for manifest parsing."""

    def test_parse_manifest(self, parser):
        code = '''
@{
    RootModule = 'MyModule.psm1'
    ModuleVersion = '1.2.3'
    Author = 'Test Author'
    Description = 'A test module'
    FunctionsToExport = @('Get-Data', 'Set-Data')
    RequiredModules = @('PSFramework')
}
'''
        result = parser.parse_manifest(code, "MyModule.psd1")
        assert result.get('module_version') == '1.2.3'
        assert 'Get-Data' in result.get('functions_to_export', [])


class TestIntegration:
    """Integration tests: parse a complex file and verify all extractor outputs."""

    def test_complex_module(self, parser):
        code = '''
#Requires -Version 5.1
#Requires -Modules ActiveDirectory

using namespace System.Collections.Generic

<#
.SYNOPSIS
    Manages user accounts in Active Directory.

.DESCRIPTION
    This module provides cmdlets for managing AD user accounts
    including creation, modification, and removal.
#>

enum UserStatus {
    Active
    Inactive
    Suspended
    Deleted
}

class UserProfile {
    [string]$UserName
    [string]$Email
    [UserStatus]$Status

    UserProfile([string]$userName) {
        $this.UserName = $userName
        $this.Status = [UserStatus]::Active
    }

    [string] GetDisplayName() {
        return "$($this.UserName) ($($this.Status))"
    }
}

function Get-UserProfile {
    [CmdletBinding()]
    [OutputType([UserProfile])]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$UserName,

        [switch]$IncludeGroups
    )

    begin {
        Import-Module ActiveDirectory
    }

    process {
        $adUser = Get-ADUser -Identity $UserName -Properties *
        $profile = [UserProfile]::new($UserName)
        $profile.Email = $adUser.EmailAddress
        Write-Output $profile
    }
}

function Set-UserStatus {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)]
        [string]$UserName,

        [Parameter(Mandatory)]
        [ValidateSet("Active", "Inactive", "Suspended")]
        [UserStatus]$Status
    )

    if ($PSCmdlet.ShouldProcess($UserName, "Set status to $Status")) {
        # Update status
        Write-Verbose "Updated $UserName to $Status"
    }
}
'''
        result = parser.parse(code, "UserManagement.psm1")

        # Verify all sections populated
        assert result.file_type == "powershell_module"
        assert len(result.classes) >= 1
        assert len(result.enums) >= 1
        assert len(result.functions) >= 2
        assert len(result.requires) >= 1
        assert len(result.usings) >= 1
        assert len(result.comment_helps) >= 1

        # Verify class details
        user_class = next((c for c in result.classes if c.name == "UserProfile"), None)
        assert user_class is not None

        # Verify enum
        status_enum = next((e for e in result.enums if e.name == "UserStatus"), None)
        assert status_enum is not None
        assert "Active" in status_enum.values

        # Verify function details
        get_func = next((f for f in result.functions if f.name == "Get-UserProfile"), None)
        assert get_func is not None
        assert get_func.is_advanced is True
        assert get_func.has_begin_process_end is True

        set_func = next((f for f in result.functions if f.name == "Set-UserStatus"), None)
        assert set_func is not None
        assert set_func.supports_should_process is True

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.ps1")
        assert result.file_type == "powershell"
        assert len(result.classes) == 0
        assert len(result.functions) == 0

    def test_comment_only_file(self, parser):
        code = '''
# This is just a comment file
# No actual code here
<#
    Multi-line comment block
    with no code
#>
'''
        result = parser.parse(code, "comments.ps1")
        assert result.file_type == "powershell"
