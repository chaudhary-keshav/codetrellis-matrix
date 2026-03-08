"""
Tests for PowerShellAPIExtractor — routes, cmdlet bindings, DSC configs, Pester tests.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.extractors.powershell.api_extractor import (
    PowerShellAPIExtractor,
    PSRouteInfo,
    PSCmdletBindingInfo,
    PSDSCConfigInfo,
    PSPesterTestInfo,
)


@pytest.fixture
def extractor():
    return PowerShellAPIExtractor()


class TestRouteExtraction:
    """Tests for web route extraction (Pode/Polaris/Universal Dashboard)."""

    def test_pode_routes(self, extractor):
        code = '''
Start-PodeServer {
    Add-PodeEndpoint -Address * -Port 8080 -Protocol Http

    Add-PodeRoute -Method Get -Path '/api/users' -ScriptBlock {
        Write-PodeJsonResponse -Value @{ users = @() }
    }

    Add-PodeRoute -Method Post -Path '/api/users' -ScriptBlock {
        $user = $WebEvent.Data
        Write-PodeJsonResponse -Value @{ id = 1 }
    }

    Add-PodeRoute -Method Delete -Path '/api/users/:id' -ScriptBlock {
        Write-PodeJsonResponse -Value @{ deleted = $true }
    }
}
'''
        result = extractor.extract(code, "server.ps1")
        routes = result.get('routes', [])
        assert len(routes) >= 3
        methods = {r.method for r in routes}
        assert "Get" in methods or "GET" in methods
        assert "Post" in methods or "POST" in methods

    def test_polaris_routes(self, extractor):
        code = '''
New-PolarisRoute -Path '/api/health' -Method GET -ScriptBlock {
    [PolarisResponse]$Response.SetStatusCode(200)
    [PolarisResponse]$Response.Send("OK")
}
'''
        result = extractor.extract(code, "polaris_app.ps1")
        routes = result.get('routes', [])
        assert len(routes) >= 1


class TestDSCConfigExtraction:
    """Tests for DSC configuration extraction."""

    def test_dsc_configuration(self, extractor):
        code = '''
Configuration WebServerSetup {
    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Import-DscResource -ModuleName xWebAdministration

    Node "WebServer01" {
        WindowsFeature IIS {
            Name = "Web-Server"
            Ensure = "Present"
        }

        xWebsite DefaultSite {
            Name = "Default Web Site"
            PhysicalPath = "C:\\inetpub\\wwwroot"
            State = "Started"
            DependsOn = "[WindowsFeature]IIS"
        }

        File WebContent {
            DestinationPath = "C:\\inetpub\\wwwroot\\index.html"
            Contents = "<h1>Hello World</h1>"
            Ensure = "Present"
            DependsOn = "[xWebsite]DefaultSite"
        }
    }
}
'''
        result = extractor.extract(code, "webserver.ps1")
        configs = result.get('dsc_configs', [])
        assert len(configs) >= 1
        assert configs[0].name == "WebServerSetup"


class TestPesterTestExtraction:
    """Tests for Pester test extraction."""

    def test_describe_it_blocks(self, extractor):
        code = '''
Describe "Get-UserProfile" {
    BeforeAll {
        Import-Module ./UserProfile.psm1
    }

    Context "When user exists" {
        It "Should return user data" {
            $result = Get-UserProfile -UserName "john"
            $result | Should -Not -BeNullOrEmpty
            $result.UserName | Should -Be "john"
        }

        It "Should include email" -Tag "Integration" {
            $result = Get-UserProfile -UserName "john"
            $result.Email | Should -Match "@"
        }
    }

    Context "When user does not exist" {
        It "Should throw an error" {
            { Get-UserProfile -UserName "nonexistent" } | Should -Throw
        }
    }
}
'''
        result = extractor.extract(code, "Get-UserProfile.Tests.ps1")
        tests = result.get('pester_tests', [])
        assert len(tests) >= 1

    def test_pester_with_mock(self, extractor):
        code = '''
Describe "Send-Email" {
    It "Should call Send-MailMessage" {
        Mock Send-MailMessage { return $true }
        Send-Email -To "user@example.com" -Subject "Test"
        Should -Invoke Send-MailMessage -Times 1
    }
}
'''
        result = extractor.extract(code, "email.Tests.ps1")
        tests = result.get('pester_tests', [])
        assert len(tests) >= 1


class TestCmdletBindingExtraction:
    """Tests for cmdlet binding pattern extraction."""

    def test_azure_cmdlets(self, extractor):
        code = '''
Connect-AzAccount
$vms = Get-AzVM -ResourceGroupName "Production"
foreach ($vm in $vms) {
    Stop-AzVM -ResourceGroupName $vm.ResourceGroupName -Name $vm.Name -Force
}
New-AzResourceGroup -Name "Staging" -Location "East US"
'''
        result = extractor.extract(code, "azure_ops.ps1")
        bindings = result.get('cmdlet_bindings', [])
        assert len(bindings) >= 1

    def test_aws_cmdlets(self, extractor):
        code = '''
Get-EC2Instance -InstanceId "i-1234567890"
New-S3Bucket -BucketName "my-bucket"
Get-IAMUser -UserName "admin"
'''
        result = extractor.extract(code, "aws_ops.ps1")
        bindings = result.get('cmdlet_bindings', [])
        assert len(bindings) >= 1

    def test_graph_cmdlets(self, extractor):
        code = '''
Connect-MgGraph -Scopes "User.Read.All"
$users = Get-MgUser -All
foreach ($user in $users) {
    Update-MgUser -UserId $user.Id -DisplayName $user.DisplayName
}
'''
        result = extractor.extract(code, "graph_ops.ps1")
        bindings = result.get('cmdlet_bindings', [])
        assert len(bindings) >= 1
