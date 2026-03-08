"""
Enhanced AutoMapper Parser for CodeTrellis.

Extracts AutoMapper-specific concepts: profiles, CreateMap configurations,
value resolvers, type converters, queryable projections.

Supports AutoMapper 8.x through 13.x.
Part of CodeTrellis v4.96 (Session 76)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetrellis.extractors.automapper import (
    AutoMapperMappingExtractor,
)


@dataclass
class AutoMapperParseResult:
    """Result of AutoMapper-enhanced parsing."""
    # Profiles
    profiles: List[Dict[str, Any]] = field(default_factory=list)

    # Standalone mappings (outside profiles)
    mappings: List[Dict[str, Any]] = field(default_factory=list)

    # Custom resolvers
    value_resolvers: List[Dict[str, Any]] = field(default_factory=list)
    type_converters: List[Dict[str, Any]] = field(default_factory=list)

    # Projections
    projections: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregates
    total_profiles: int = 0
    total_mappings: int = 0
    total_resolvers: int = 0

    # Framework metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_version: str = ""
    file_type: str = ""  # profile, resolver, converter, usage


class EnhancedAutoMapperParser:
    """Parser for AutoMapper concepts in C# files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core AutoMapper
        'automapper': r'using\s+AutoMapper\b',
        'automapper_extensions': r'using\s+AutoMapper\.Extensions\b',
        'automapper_queryable': r'using\s+AutoMapper\.QueryableExtensions\b',
        'automapper_collection': r'using\s+AutoMapper\.Collection\b',
        'automapper_ef': r'using\s+AutoMapper\.EntityFrameworkCore\b',

        # Core types
        'profile': r'\bclass\s+\w+\s*:\s*Profile\b',
        'create_map': r'\bCreateMap\s*<',
        'reverse_map': r'\.ReverseMap\s*\(',
        'for_member': r'\.ForMember\s*\(',
        'for_all_members': r'\.ForAllMembers\s*\(',

        # Resolvers / Converters
        'value_resolver': r'\bIValueResolver\s*<',
        'member_value_resolver': r'\bIMemberValueResolver\s*<',
        'type_converter': r'\bITypeConverter\s*<',

        # DI integration
        'add_automapper': r'\.AddAutoMapper\s*\(',
        'add_profiles': r'\.AddMaps\s*\(',

        # Projections
        'project_to': r'\.ProjectTo\s*<',
        'map_call': r'\.Map\s*<\s*\w+\s*>\s*\(',

        # Configuration
        'mapper_config': r'\bMapperConfiguration\b',
        'assertion_config': r'\.AssertConfigurationIsValid\s*\(',

        # v12+ attributes
        'auto_map_attribute': r'\[AutoMap\s*\(',
    }

    VERSION_FEATURES: Dict[str, List[str]] = {
        '8.0': ['CreateMap', 'Profile', 'ForMember', 'ReverseMap'],
        '9.0': ['CreateMap', 'Profile', 'RecordSupport'],
        '10.0': ['CreateMap', 'Profile', 'IValueResolver'],
        '11.0': ['AddAutoMapper', 'ProjectTo', 'Collection'],
        '12.0': ['AutoMapAttribute', 'AttributeMapping'],
        '13.0': ['AutoMapAttribute', 'ImprovedPerformance'],
    }

    def __init__(self):
        """Initialize extractors."""
        self.mapping_extractor = AutoMapperMappingExtractor()

    def is_automapper_file(self, content: str, file_path: str = "") -> bool:
        """Check if file contains AutoMapper code."""
        if not content:
            return False
        indicators = [
            r'using\s+AutoMapper\b',
            r'\bclass\s+\w+\s*:\s*Profile\b',
            r'\bCreateMap\s*<',
            r'\bIValueResolver\s*<',
            r'\bITypeConverter\s*<',
            r'\.AddAutoMapper\s*\(',
            r'\[AutoMap\s*\(',
        ]
        return any(re.search(p, content) for p in indicators)

    def parse(self, content: str, file_path: str = "") -> AutoMapperParseResult:
        """Parse AutoMapper concepts from C# file."""
        result = AutoMapperParseResult()

        if not content or not self.is_automapper_file(content, file_path):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_version = self._detect_version(content)
        result.file_type = self._classify_file(content, file_path)

        # Extract with mapping extractor
        mapping_data = self.mapping_extractor.extract(content, file_path)

        result.profiles = [self._profile_to_dict(p) for p in mapping_data.get('profiles', [])]
        result.mappings = [self._mapping_to_dict(m) for m in mapping_data.get('mappings', [])]
        result.value_resolvers = [self._resolver_to_dict(r) for r in mapping_data.get('value_resolvers', [])]
        result.type_converters = [self._converter_to_dict(c) for c in mapping_data.get('type_converters', [])]
        result.projections = [self._projection_to_dict(p) for p in mapping_data.get('projections', [])]

        # Aggregates
        result.total_profiles = len(result.profiles)
        profile_mappings = sum(p.get('total_mappings', 0) for p in result.profiles)
        result.total_mappings = profile_mappings + len(result.mappings)
        result.total_resolvers = len(result.value_resolvers) + len(result.type_converters)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect AutoMapper-related frameworks."""
        found = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if re.search(pattern, content):
                found.append(name)
        return found

    def _detect_version(self, content: str) -> str:
        """Detect AutoMapper version from usage patterns."""
        detected = "8.0"
        if re.search(r'\[AutoMap\s*\(', content):
            detected = "12.0"
        elif re.search(r'\.AddAutoMapper\s*\(', content):
            detected = "11.0"
        elif re.search(r'\bIValueResolver\s*<', content):
            detected = "10.0"
        return detected

    def _classify_file(self, content: str, file_path: str) -> str:
        """Classify file type."""
        path_lower = file_path.lower()
        if re.search(r'\bclass\s+\w+\s*:\s*Profile\b', content):
            return "profile"
        if re.search(r'\bIValueResolver\s*<', content) or re.search(r'\bIMemberValueResolver\s*<', content):
            return "resolver"
        if re.search(r'\bITypeConverter\s*<', content):
            return "converter"
        if 'profile' in path_lower or 'mapping' in path_lower:
            return "profile"
        return "usage"

    def _profile_to_dict(self, p) -> Dict[str, Any]:
        return {
            'name': p.name,
            'total_mappings': p.total_mappings,
            'file': p.file,
            'line': p.line_number,
        }

    def _mapping_to_dict(self, m) -> Dict[str, Any]:
        return {
            'source_type': m.source_type,
            'destination_type': m.destination_type,
            'is_reverse_map': m.is_reverse_map,
            'member_configs': m.member_configs,
            'has_condition': m.has_condition,
            'file': m.file,
            'line': m.line_number,
        }

    def _resolver_to_dict(self, r) -> Dict[str, Any]:
        return {
            'name': r.name,
            'source_type': r.source_type,
            'destination_type': r.destination_type,
            'dest_member_type': r.dest_member_type,
            'file': r.file,
            'line': r.line_number,
        }

    def _converter_to_dict(self, c) -> Dict[str, Any]:
        return {
            'name': c.name,
            'source_type': c.source_type,
            'destination_type': c.destination_type,
            'file': c.file,
            'line': c.line_number,
        }

    def _projection_to_dict(self, p) -> Dict[str, Any]:
        return {
            'destination_type': p.destination_type,
            'method': p.method,
            'file': p.file,
            'line': p.line_number,
        }
