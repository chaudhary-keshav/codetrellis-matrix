"""
Tests for PowerShellFunctionExtractor — function, filter, workflow, script block extraction.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.extractors.powershell.function_extractor import (
    PowerShellFunctionExtractor,
    PSFunctionInfo,
    PSParameterInfo,
    PSScriptBlockInfo,
    PSPipelineInfo,
)


@pytest.fixture
def extractor():
    return PowerShellFunctionExtractor()


class TestFunctionExtraction:
    """Tests for PowerShell function extraction."""

    def test_simple_function(self, extractor):
        code = '''
function Get-Greeting {
    param(
        [string]$Name = "World"
    )
    return "Hello, $Name!"
}
'''
        result = extractor.extract(code, "greeting.ps1")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "Get-Greeting"

    def test_advanced_function_with_cmdletbinding(self, extractor):
        code = '''
function Set-UserProfile {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string]$UserName,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Active", "Inactive", "Suspended")]
        [string]$Status,

        [switch]$Force
    )

    begin {
        Write-Verbose "Starting user profile update"
    }

    process {
        if ($PSCmdlet.ShouldProcess($UserName, "Set status to $Status")) {
            # Update profile
        }
    }

    end {
        Write-Verbose "Completed"
    }
}
'''
        result = extractor.extract(code, "profile.ps1")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        func = functions[0]
        assert func.name == "Set-UserProfile"
        assert func.is_advanced is True
        assert func.cmdlet_binding is True
        assert func.supports_should_process is True
        assert func.verb == "Set"
        assert func.noun == "UserProfile"
        assert func.has_begin_process_end is True

    def test_filter_extraction(self, extractor):
        code = '''
filter ConvertTo-Upper {
    $_.ToUpper()
}
'''
        result = extractor.extract(code, "filters.ps1")
        functions = result.get('functions', [])
        filters = [f for f in functions if f.function_type == 'filter']
        assert len(filters) >= 1
        assert filters[0].name == "ConvertTo-Upper"

    def test_verb_noun_parsing(self, extractor):
        code = '''
function Get-ProcessInfo {
    Get-Process
}

function New-DatabaseConnection {
    param([string]$ConnectionString)
}

function Remove-TempFiles {
    param([string]$Path)
}
'''
        result = extractor.extract(code, "cmdlets.ps1")
        functions = result.get('functions', [])
        verbs = {f.verb for f in functions if f.verb}
        assert "Get" in verbs
        assert "New" in verbs
        assert "Remove" in verbs

    def test_parameter_extraction(self, extractor):
        code = '''
function Test-Connection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ComputerName,

        [int]$Port = 443,

        [switch]$UseSsl,

        [ValidateSet("TCP", "UDP")]
        [string]$Protocol = "TCP"
    )
    # Implementation
}
'''
        result = extractor.extract(code, "connection.ps1")
        functions = result.get('functions', [])
        assert len(functions) >= 1
        params = functions[0].parameters
        assert len(params) >= 3


class TestScriptBlockExtraction:
    """Tests for script block extraction."""

    def test_scriptblock_variable(self, extractor):
        code = '''
$action = {
    param($message)
    Write-Host $message
}

$filter = { $_.Status -eq "Running" }
'''
        result = extractor.extract(code, "blocks.ps1")
        blocks = result.get('script_blocks', [])
        assert len(blocks) >= 1


class TestPipelineExtraction:
    """Tests for pipeline pattern extraction."""

    def test_pipeline_detection(self, extractor):
        code = '''
Get-Process | Where-Object { $_.CPU -gt 100 } | Sort-Object CPU -Descending | Select-Object -First 10

Get-ChildItem -Recurse | Where-Object { $_.Extension -eq ".log" } | Remove-Item -Force
'''
        result = extractor.extract(code, "pipes.ps1")
        pipelines = result.get('pipelines', [])
        assert len(pipelines) >= 1
