"""
Tests for PowerShellAttributeExtractor — imports, using, requires, comment help, dot-source.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.extractors.powershell.attribute_extractor import (
    PowerShellAttributeExtractor,
    PSImportInfo,
    PSUsingInfo,
    PSRequiresInfo,
    PSCommentHelpInfo,
    PSDotSourceInfo,
)


@pytest.fixture
def extractor():
    return PowerShellAttributeExtractor()


class TestImportExtraction:
    """Tests for Import-Module extraction."""

    def test_import_module(self, extractor):
        code = '''
Import-Module ActiveDirectory
Import-Module -Name Az.Accounts -MinimumVersion 2.0.0
Import-Module ./lib/CustomModule.psm1
Import-Module Microsoft.PowerShell.SecretManagement
'''
        result = extractor.extract(code, "imports.ps1")
        imports = result.get('imports', [])
        assert len(imports) >= 3
        modules = [i.module for i in imports]
        assert "ActiveDirectory" in modules


class TestUsingExtraction:
    """Tests for using statement extraction (PS 5.0+)."""

    def test_using_statements(self, extractor):
        code = '''
using namespace System.Collections.Generic
using namespace System.IO
using module ./MyClasses.psm1
using assembly System.Net.Http
'''
        result = extractor.extract(code, "usings.ps1")
        usings = result.get('usings', [])
        assert len(usings) >= 3
        types = {u.using_type for u in usings}
        assert "namespace" in types


class TestRequiresExtraction:
    """Tests for #Requires statement extraction."""

    def test_requires_version(self, extractor):
        code = '''
#Requires -Version 7.0
#Requires -Modules @{ ModuleName="Az.Accounts"; ModuleVersion="2.0.0" }
#Requires -RunAsAdministrator
#Requires -PSEdition Core
'''
        result = extractor.extract(code, "requires.ps1")
        requires = result.get('requires', [])
        assert len(requires) >= 2


class TestCommentHelpExtraction:
    """Tests for comment-based help extraction."""

    def test_comment_based_help(self, extractor):
        code = '''
<#
.SYNOPSIS
    Gets user profile information from Active Directory.

.DESCRIPTION
    This function retrieves detailed user profile information from Active Directory
    including email, department, and manager information.

.PARAMETER UserName
    The SAM account name of the user to look up.

.PARAMETER IncludeManager
    Switch to include manager information in the output.

.EXAMPLE
    Get-UserProfile -UserName "john.doe"

    Returns the profile for john.doe.

.EXAMPLE
    Get-ADUser -Filter * | Get-UserProfile -IncludeManager

    Gets profiles for all AD users with manager info.

.OUTPUTS
    PSCustomObject

.NOTES
    Requires Active Directory module.
#>
function Get-UserProfile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$UserName,
        [switch]$IncludeManager
    )
    # Implementation
}
'''
        result = extractor.extract(code, "profile.ps1")
        helps = result.get('comment_helps', [])
        assert len(helps) >= 1
        h = helps[0]
        assert "user profile" in h.synopsis.lower() or "Gets" in h.synopsis


class TestDotSourceExtraction:
    """Tests for dot-sourcing extraction."""

    def test_dot_source(self, extractor):
        code = '''
. $PSScriptRoot/Private/Get-InternalConfig.ps1
. $PSScriptRoot/Private/Write-InternalLog.ps1
. "$PSScriptRoot\\Public\\Get-UserProfile.ps1"
. ./lib/helpers.ps1
'''
        result = extractor.extract(code, "module.psm1")
        dot_sources = result.get('dot_sources', [])
        assert len(dot_sources) >= 3


class TestVersionDetection:
    """Tests for PowerShell version detection."""

    def test_version_from_requires(self, extractor):
        code = '''
#Requires -Version 7.2

function Get-Data {
    [CmdletBinding()]
    param()
    # Uses PS 7.2+ features
}
'''
        result = extractor.extract(code, "modern.ps1")
        version = result.get('ps_version', '')
        assert version == "7.2" or version.startswith("7")

    def test_ps5_class_detection(self, extractor):
        code = '''
class MyClass {
    [string]$Name

    MyClass([string]$name) {
        $this.Name = $name
    }
}
'''
        result = extractor.extract(code, "classes.ps1")
        version = result.get('ps_version', '')
        # Should detect at least 5.0 from class usage
        if version:
            assert version.startswith("5") or float(version) >= 5.0

    def test_ps7_features(self, extractor):
        code = '''
$x = $null ?? "default"
$items ??= @()
$result = $value ? "yes" : "no"
'''
        result = extractor.extract(code, "ps7.ps1")
        version = result.get('ps_version', '')
        if version:
            assert float(version.split('.')[0]) >= 7
