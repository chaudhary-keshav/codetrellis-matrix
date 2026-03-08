"""
AutoMapper Mapping Extractor.

Extracts profiles, CreateMap configurations, value resolvers, type converters, projections.

Supports AutoMapper 8.x through 13.x.
Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AutoMapperMappingInfo:
    """Information about an AutoMapper mapping."""
    source_type: str = ""
    destination_type: str = ""
    is_reverse_map: bool = False
    member_configs: List[str] = field(default_factory=list)  # ForMember, Ignore, MapFrom, etc.
    has_condition: bool = False
    has_null_substitute: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class AutoMapperProfileInfo:
    """Information about an AutoMapper profile."""
    name: str = ""
    mappings: List[AutoMapperMappingInfo] = field(default_factory=list)
    total_mappings: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class AutoMapperValueResolverInfo:
    """Information about a custom value resolver."""
    name: str = ""
    source_type: str = ""
    destination_type: str = ""
    dest_member_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AutoMapperTypeConverterInfo:
    """Information about a custom type converter."""
    name: str = ""
    source_type: str = ""
    destination_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AutoMapperProjectionInfo:
    """Information about a queryable projection."""
    source_type: str = ""
    destination_type: str = ""
    method: str = ""  # ProjectTo, MapFrom with query
    file: str = ""
    line_number: int = 0


class AutoMapperMappingExtractor:
    """Extracts AutoMapper profiles, mappings, resolvers, and converters."""

    # Profile class
    PROFILE_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*Profile\b',
        re.MULTILINE
    )

    # CreateMap<TSource, TDest>()
    CREATE_MAP_PATTERN = re.compile(
        r'CreateMap\s*<\s*(\w+)\s*,\s*(\w+)\s*>\s*\(\s*\)',
        re.MULTILINE
    )

    # .ReverseMap()
    REVERSE_MAP_PATTERN = re.compile(r'\.ReverseMap\s*\(\s*\)', re.MULTILINE)

    # .ForMember(dest => dest.X, opt => opt.MapFrom(src => src.Y))
    FOR_MEMBER_PATTERN = re.compile(
        r'\.ForMember\s*\(\s*\w+\s*=>\s*\w+\.(\w+)\s*,',
        re.MULTILINE
    )

    # .ForMember(..., opt => opt.Ignore())
    IGNORE_PATTERN = re.compile(r'\.Ignore\s*\(\s*\)', re.MULTILINE)

    # .ForMember(..., opt => opt.MapFrom(...))
    MAP_FROM_PATTERN = re.compile(r'\.MapFrom\s*\(', re.MULTILINE)

    # .ForMember(..., opt => opt.Condition(...))
    CONDITION_PATTERN = re.compile(r'\.Condition\s*\(', re.MULTILINE)

    # .ForMember(..., opt => opt.NullSubstitute(...))
    NULL_SUBSTITUTE_PATTERN = re.compile(r'\.NullSubstitute\s*\(', re.MULTILINE)

    # IValueResolver<TSource, TDest, TDestMember>
    VALUE_RESOLVER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IValueResolver\s*<\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # ITypeConverter<TSource, TDest>
    TYPE_CONVERTER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*ITypeConverter\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # IMemberValueResolver<TSource, TDest, TSourceMember, TDestMember>
    MEMBER_VALUE_RESOLVER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IMemberValueResolver\s*<',
        re.MULTILINE
    )

    # ProjectTo<T>()
    PROJECT_TO_PATTERN = re.compile(
        r'\.ProjectTo\s*<\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    # .Map<TDest>(source)
    MAP_CALL_PATTERN = re.compile(
        r'\.Map\s*<\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract AutoMapper profiles, mappings, and resolvers."""
        result = {
            'profiles': [],
            'mappings': [],
            'value_resolvers': [],
            'type_converters': [],
            'projections': [],
        }

        if not content or not content.strip():
            return result

        # Profiles
        for match in self.PROFILE_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Extract mappings within this profile
            mappings = self._extract_mappings(content, file_path)

            result['profiles'].append(AutoMapperProfileInfo(
                name=name,
                mappings=mappings,
                total_mappings=len(mappings),
                file=file_path,
                line_number=line,
            ))

        # Standalone mappings (not in profile context)
        if not result['profiles']:
            result['mappings'] = self._extract_mappings(content, file_path)

        # Value resolvers
        for match in self.VALUE_RESOLVER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['value_resolvers'].append(AutoMapperValueResolverInfo(
                name=match.group(1),
                source_type=match.group(2),
                destination_type=match.group(3),
                dest_member_type=match.group(4),
                file=file_path,
                line_number=line,
            ))

        # Type converters
        for match in self.TYPE_CONVERTER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['type_converters'].append(AutoMapperTypeConverterInfo(
                name=match.group(1),
                source_type=match.group(2),
                destination_type=match.group(3),
                file=file_path,
                line_number=line,
            ))

        # Projections
        for match in self.PROJECT_TO_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['projections'].append(AutoMapperProjectionInfo(
                destination_type=match.group(1),
                method="ProjectTo",
                file=file_path,
                line_number=line,
            ))

        return result

    def _extract_mappings(self, content: str, file_path: str) -> List[AutoMapperMappingInfo]:
        """Extract CreateMap configurations."""
        mappings = []
        for match in self.CREATE_MAP_PATTERN.finditer(content):
            source = match.group(1)
            dest = match.group(2)
            line = content[:match.start()].count('\n') + 1

            # Look after CreateMap for chained config
            after = content[match.end():match.end() + 1000]

            # Check for ReverseMap
            is_reverse = bool(self.REVERSE_MAP_PATTERN.search(after[:300]))

            # Collect ForMember configs
            members = [m.group(1) for m in self.FOR_MEMBER_PATTERN.finditer(after[:500])]

            has_condition = bool(self.CONDITION_PATTERN.search(after[:500]))
            has_null_sub = bool(self.NULL_SUBSTITUTE_PATTERN.search(after[:500]))

            mappings.append(AutoMapperMappingInfo(
                source_type=source,
                destination_type=dest,
                is_reverse_map=is_reverse,
                member_configs=members[:10],
                has_condition=has_condition,
                has_null_substitute=has_null_sub,
                file=file_path,
                line_number=line,
            ))

        return mappings
