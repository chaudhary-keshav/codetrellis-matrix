"""
Tests for PowerShellTypeExtractor — class, enum, interface, DSC resource extraction.

Part of CodeTrellis v4.29 PowerShell Language Support.
"""

import pytest
from codetrellis.extractors.powershell.type_extractor import (
    PowerShellTypeExtractor,
    PSClassInfo,
    PSEnumInfo,
    PSInterfaceInfo,
    PSDSCResourceInfo,
    PSPropertyInfo,
)


@pytest.fixture
def extractor():
    return PowerShellTypeExtractor()


class TestClassExtraction:
    """Tests for PowerShell class extraction (PS 5.0+)."""

    def test_simple_class(self, extractor):
        code = '''
class Person {
    [string]$Name
    [int]$Age

    Person([string]$name, [int]$age) {
        $this.Name = $name
        $this.Age = $age
    }

    [string] ToString() {
        return "$($this.Name), age $($this.Age)"
    }
}
'''
        result = extractor.extract(code, "person.ps1")
        classes = result.get('classes', [])
        assert len(classes) >= 1
        cls = classes[0]
        assert cls.name == "Person"

    def test_class_with_inheritance(self, extractor):
        code = '''
class Animal {
    [string]$Name
}

class Dog : Animal {
    [string]$Breed

    [void] Bark() {
        Write-Host "Woof!"
    }
}
'''
        result = extractor.extract(code, "animals.ps1")
        classes = result.get('classes', [])
        dog_classes = [c for c in classes if c.name == "Dog"]
        assert len(dog_classes) >= 1
        assert dog_classes[0].base_class == "Animal"

    def test_class_with_interface(self, extractor):
        code = '''
class Logger : IDisposable {
    [string]$LogPath

    [void] Dispose() {
        # Cleanup
    }
}
'''
        result = extractor.extract(code, "logger.ps1")
        classes = result.get('classes', [])
        assert len(classes) >= 1

    def test_dsc_resource_class(self, extractor):
        code = '''
[DscResource()]
class MyFileResource {
    [DscProperty(Key)]
    [string]$Path

    [DscProperty(Mandatory)]
    [string]$Content

    [MyFileResource] Get() {
        return $this
    }

    [bool] Test() {
        return (Test-Path $this.Path)
    }

    [void] Set() {
        Set-Content -Path $this.Path -Value $this.Content
    }
}
'''
        result = extractor.extract(code, "dsc_resource.ps1")
        classes = result.get('classes', [])
        dsc_classes = [c for c in classes if c.is_dsc_resource]
        assert len(dsc_classes) >= 1
        assert dsc_classes[0].name == "MyFileResource"


class TestEnumExtraction:
    """Tests for PowerShell enum extraction (PS 5.0+)."""

    def test_simple_enum(self, extractor):
        code = '''
enum Color {
    Red
    Green
    Blue
}
'''
        result = extractor.extract(code, "enums.ps1")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        assert enums[0].name == "Color"
        assert "Red" in enums[0].values
        assert "Green" in enums[0].values
        assert "Blue" in enums[0].values

    def test_flags_enum(self, extractor):
        code = '''
[Flags()]
enum FilePermissions {
    None = 0
    Read = 1
    Write = 2
    Execute = 4
}
'''
        result = extractor.extract(code, "perms.ps1")
        enums = result.get('enums', [])
        assert len(enums) >= 1
        assert enums[0].is_flags is True


class TestDSCResourceExtraction:
    """Tests for DSC resource extraction."""

    def test_dsc_resource_properties(self, extractor):
        code = '''
[DscResource()]
class cWebsite {
    [DscProperty(Key)]
    [string]$Name

    [DscProperty(Mandatory)]
    [string]$PhysicalPath

    [DscProperty()]
    [int]$Port = 80

    [cWebsite] Get() { return $this }
    [bool] Test() { return $true }
    [void] Set() { }
}
'''
        result = extractor.extract(code, "website.ps1")
        dsc_resources = result.get('dsc_resources', [])
        # Should be detected either as dsc_resources or classes with is_dsc_resource
        classes = result.get('classes', [])
        all_dsc = dsc_resources + [c for c in classes if c.is_dsc_resource]
        assert len(all_dsc) >= 1


class TestInterfaceExtraction:
    """Tests for .NET interface detection in PowerShell."""

    def test_interface_implementation(self, extractor):
        code = '''
class CustomFormatter : IFormatProvider, ICustomFormatter {
    [object] GetFormat([type]$formatType) {
        return $this
    }

    [string] Format([string]$format, [object]$arg, [IFormatProvider]$formatProvider) {
        return $arg.ToString()
    }
}
'''
        result = extractor.extract(code, "formatter.ps1")
        # Should detect interfaces from class implementations
        classes = result.get('classes', [])
        assert len(classes) >= 1
