"""
ASP.NET Core Configuration Extractor.

Extracts configuration binding, Options pattern, and IConfiguration usage.

Supports:
- IConfiguration / IOptions<T> / IOptionsSnapshot<T> / IOptionsMonitor<T>
- Configuration binding (builder.Configuration.Bind, Configure<T>)
- appsettings sections
- Environment-specific configuration
- User secrets
- Azure Key Vault integration
- Custom configuration providers

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AspNetConfigBindingInfo:
    """Information about a configuration binding."""
    section: str = ""              # Configuration section name
    bound_type: str = ""           # Type being bound to
    method: str = ""               # Bind, Configure, Get<T>, GetSection
    is_required: bool = False      # GetRequiredSection
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetOptionsPatternInfo:
    """Information about Options pattern usage."""
    options_type: str = ""         # The TOptions type
    pattern: str = ""              # IOptions, IOptionsSnapshot, IOptionsMonitor
    section: str = ""              # Config section
    has_validation: bool = False   # .ValidateDataAnnotations() / .Validate()
    has_post_configure: bool = False  # PostConfigure<T>
    file: str = ""
    line_number: int = 0


class AspNetCoreConfigExtractor:
    """Extracts ASP.NET Core configuration patterns."""

    # Configure<T> with section binding
    CONFIGURE_OPTIONS_PATTERN = re.compile(
        r'\.Configure\s*<\s*(\w+)\s*>\s*\(\s*'
        r'(?:(?:\w+\.)?(?:Configuration|GetSection)\s*(?:\[\s*["\']([^"\']+)["\']\s*\]|'
        r'\(\s*["\']([^"\']+)["\']\s*\)))',
        re.MULTILINE
    )

    # services.AddOptions<T>().Bind(Configuration.GetSection("..."))
    ADD_OPTIONS_PATTERN = re.compile(
        r'\.AddOptions\s*<\s*(\w+)\s*>\s*\(\s*\)'
        r'(?:\s*\.\s*Bind\s*\(\s*(?:\w+\.)?(?:Configuration\.)?GetSection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\))?',
        re.MULTILINE
    )

    # Configuration.GetSection / Configuration.Bind
    GET_SECTION_PATTERN = re.compile(
        r'Configuration\s*(?:\[\s*["\']([^"\']+)["\']\s*\]|\.\s*GetSection\s*\(\s*["\']([^"\']+)["\']\s*\))',
        re.MULTILINE
    )

    # GetRequiredSection
    GET_REQUIRED_SECTION_PATTERN = re.compile(
        r'\.GetRequiredSection\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # Configuration.Get<T>()
    CONFIG_GET_PATTERN = re.compile(
        r'Configuration\s*\.Get\s*<\s*(\w+)\s*>\s*\(\s*\)',
        re.MULTILINE
    )

    # IOptions<T> / IOptionsSnapshot<T> / IOptionsMonitor<T> injection
    OPTIONS_INJECTION_PATTERN = re.compile(
        r'(IOptions(?:Snapshot|Monitor)?)\s*<\s*(\w+)\s*>\s+(\w+)',
        re.MULTILINE
    )

    # ValidateDataAnnotations
    VALIDATE_ANNOTATIONS_PATTERN = re.compile(
        r'\.ValidateDataAnnotations\s*\(\s*\)',
        re.MULTILINE
    )

    # PostConfigure
    POST_CONFIGURE_PATTERN = re.compile(
        r'\.PostConfigure\s*<\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    # Environment variable patterns
    ENV_PATTERN = re.compile(
        r'Environment\.GetEnvironmentVariable\s*\(\s*["\'](\w+)["\']\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract configuration patterns."""
        result = {
            'config_bindings': [],
            'options_patterns': [],
            'env_vars': [],
        }

        if not content or not content.strip():
            return result

        # Configure<T> bindings
        for match in self.CONFIGURE_OPTIONS_PATTERN.finditer(content):
            bound_type = match.group(1)
            section = match.group(2) or match.group(3) or ""
            line = content[:match.start()].count('\n') + 1
            result['config_bindings'].append(AspNetConfigBindingInfo(
                section=section,
                bound_type=bound_type,
                method="Configure",
                file=file_path,
                line_number=line,
            ))

        # AddOptions<T>().Bind()
        for match in self.ADD_OPTIONS_PATTERN.finditer(content):
            bound_type = match.group(1)
            section = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1
            result['config_bindings'].append(AspNetConfigBindingInfo(
                section=section,
                bound_type=bound_type,
                method="AddOptions",
                file=file_path,
                line_number=line,
            ))

        # GetSection usage
        for match in self.GET_SECTION_PATTERN.finditer(content):
            section = match.group(1) or match.group(2)
            line = content[:match.start()].count('\n') + 1
            result['config_bindings'].append(AspNetConfigBindingInfo(
                section=section,
                method="GetSection",
                file=file_path,
                line_number=line,
            ))

        # GetRequiredSection
        for match in self.GET_REQUIRED_SECTION_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['config_bindings'].append(AspNetConfigBindingInfo(
                section=match.group(1),
                method="GetRequiredSection",
                is_required=True,
                file=file_path,
                line_number=line,
            ))

        # Configuration.Get<T>()
        for match in self.CONFIG_GET_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['config_bindings'].append(AspNetConfigBindingInfo(
                bound_type=match.group(1),
                method="Get",
                file=file_path,
                line_number=line,
            ))

        # IOptions<T> injections
        for match in self.OPTIONS_INJECTION_PATTERN.finditer(content):
            pattern_type = match.group(1)
            options_type = match.group(2)
            line = content[:match.start()].count('\n') + 1
            result['options_patterns'].append(AspNetOptionsPatternInfo(
                options_type=options_type,
                pattern=pattern_type,
                file=file_path,
                line_number=line,
            ))

        # Environment variables
        for match in self.ENV_PATTERN.finditer(content):
            result['env_vars'].append(match.group(1))

        return result
