"""
EF Core Model/Entity Extractor.

Extracts entity configurations, relationships, value conversions, and data annotations.

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EFCoreEntityInfo:
    """Information about an EF Core entity."""
    name: str = ""
    table_name: str = ""
    schema: str = ""
    has_composite_key: bool = False
    key_properties: List[str] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    navigation_properties: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    owned_types: List[str] = field(default_factory=list)
    is_keyless: bool = False
    is_owned: bool = False
    is_tph: bool = False  # Table per hierarchy
    is_tpt: bool = False  # Table per type
    discriminator: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class EFCoreRelationshipInfo:
    """Information about an EF Core relationship."""
    principal: str = ""
    dependent: str = ""
    relationship_type: str = ""  # OneToOne, OneToMany, ManyToMany
    foreign_key: str = ""
    navigation_property: str = ""
    inverse_navigation: str = ""
    is_required: bool = False
    on_delete: str = ""  # Cascade, Restrict, SetNull, NoAction
    file: str = ""
    line_number: int = 0


@dataclass
class EFCoreValueConversionInfo:
    """Information about an EF Core value conversion."""
    property_name: str = ""
    entity_name: str = ""
    converter_type: str = ""  # HasConversion, ValueConverter, built-in
    provider_type: str = ""
    model_type: str = ""
    file: str = ""
    line_number: int = 0


class EFCoreModelExtractor:
    """Extracts EF Core entity models, relationships, and value conversions."""

    # IEntityTypeConfiguration<T>
    ENTITY_CONFIG_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IEntityTypeConfiguration\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Entity with data annotations
    TABLE_ATTR_PATTERN = re.compile(r'\[Table\(["\'](\w+)["\']\s*(?:,\s*Schema\s*=\s*["\'](\w+)["\']\s*)?\)\]', re.MULTILINE)
    KEY_ATTR_PATTERN = re.compile(r'\[Key\]', re.MULTILINE)
    REQUIRED_ATTR_PATTERN = re.compile(r'\[Required\]', re.MULTILINE)
    MAX_LENGTH_ATTR_PATTERN = re.compile(r'\[MaxLength\((\d+)\)\]', re.MULTILINE)
    FOREIGN_KEY_ATTR_PATTERN = re.compile(r'\[ForeignKey\(["\'](\w+)["\']\)\]', re.MULTILINE)

    # Fluent API relationship patterns
    HAS_ONE_PATTERN = re.compile(r'\.HasOne\s*(?:<\s*(\w+)\s*>)?\s*\(\s*(?:\w+\s*=>\s*\w+\.(\w+))?\s*\)', re.MULTILINE)
    HAS_MANY_PATTERN = re.compile(r'\.HasMany\s*(?:<\s*(\w+)\s*>)?\s*\(\s*(?:\w+\s*=>\s*\w+\.(\w+))?\s*\)', re.MULTILINE)
    WITH_ONE_PATTERN = re.compile(r'\.WithOne\s*\(\s*(?:\w+\s*=>\s*\w+\.(\w+))?\s*\)', re.MULTILINE)
    WITH_MANY_PATTERN = re.compile(r'\.WithMany\s*\(\s*(?:\w+\s*=>\s*\w+\.(\w+))?\s*\)', re.MULTILINE)
    HAS_FOREIGN_KEY_PATTERN = re.compile(r'\.HasForeignKey\s*(?:<\s*\w+\s*>)?\s*\(\s*\w+\s*=>\s*\w+\.(\w+)\)', re.MULTILINE)
    ON_DELETE_PATTERN = re.compile(r'\.OnDelete\s*\(\s*DeleteBehavior\.(\w+)\s*\)', re.MULTILINE)

    # Value conversions
    HAS_CONVERSION_PATTERN = re.compile(r'\.HasConversion\s*(?:<\s*(\w+)\s*(?:,\s*(\w+)\s*)?>)?\s*\(', re.MULTILINE)
    VALUE_CONVERTER_PATTERN = re.compile(r'new\s+ValueConverter\s*<\s*(\w+)\s*,\s*(\w+)\s*>', re.MULTILINE)

    # ToTable
    TO_TABLE_PATTERN = re.compile(r'\.ToTable\s*\(\s*["\'](\w+)["\']\s*(?:,\s*["\'](\w+)["\']\s*)?\)', re.MULTILINE)

    # HasKey
    HAS_KEY_PATTERN = re.compile(r'\.HasKey\s*\(\s*\w+\s*=>\s*(?:new\s*\{([^}]+)\}|\w+\.(\w+))\s*\)', re.MULTILINE)

    # Owned types
    OWNS_ONE_PATTERN = re.compile(r'\.OwnsOne\s*(?:<\s*(\w+)\s*>)?\s*\(', re.MULTILINE)
    OWNS_MANY_PATTERN = re.compile(r'\.OwnsMany\s*(?:<\s*(\w+)\s*>)?\s*\(', re.MULTILINE)

    # HasIndex
    HAS_INDEX_PATTERN = re.compile(r'\.HasIndex\s*\(\s*\w+\s*=>\s*(?:new\s*\{([^}]+)\}|\w+\.(\w+))\s*\)', re.MULTILINE)

    # Discriminator (TPH)
    DISCRIMINATOR_PATTERN = re.compile(r'\.HasDiscriminator\s*(?:<\s*(\w+)\s*>)?\s*\(', re.MULTILINE)

    # [Keyless]
    KEYLESS_ATTR_PATTERN = re.compile(r'\[Keyless\]', re.MULTILINE)

    # [Owned]
    OWNED_ATTR_PATTERN = re.compile(r'\[Owned\]', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract EF Core entity models and relationships."""
        result = {
            'entities': [],
            'relationships': [],
            'value_conversions': [],
            'entity_configs': [],
        }

        if not content or not content.strip():
            return result

        # IEntityTypeConfiguration implementations
        for match in self.ENTITY_CONFIG_PATTERN.finditer(content):
            config_name = match.group(1)
            entity_name = match.group(2)
            line = content[:match.start()].count('\n') + 1
            result['entity_configs'].append({
                'config_name': config_name,
                'entity_name': entity_name,
                'file': file_path,
                'line': line,
            })

        # Extract relationships from Fluent API
        result['relationships'] = self._extract_relationships(content, file_path)

        # Extract value conversions
        for match in self.HAS_CONVERSION_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['value_conversions'].append(EFCoreValueConversionInfo(
                converter_type=match.group(1) or "inline",
                provider_type=match.group(2) or "",
                file=file_path,
                line_number=line,
            ))

        for match in self.VALUE_CONVERTER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['value_conversions'].append(EFCoreValueConversionInfo(
                model_type=match.group(1),
                provider_type=match.group(2),
                converter_type="ValueConverter",
                file=file_path,
                line_number=line,
            ))

        return result

    def _extract_relationships(self, content: str, file_path: str) -> List[EFCoreRelationshipInfo]:
        """Extract relationship configurations from Fluent API."""
        relationships = []

        # HasOne...WithMany (OneToMany from dependent side)
        for match in self.HAS_ONE_PATTERN.finditer(content):
            principal = match.group(1) or ""
            nav = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1

            # Look for WithMany after HasOne
            after = content[match.end():match.end() + 300]
            with_many = self.WITH_MANY_PATTERN.search(after)
            fk_match = self.HAS_FOREIGN_KEY_PATTERN.search(after)
            delete_match = self.ON_DELETE_PATTERN.search(after)

            relationships.append(EFCoreRelationshipInfo(
                principal=principal,
                relationship_type="OneToMany" if with_many else "OneToOne",
                navigation_property=nav,
                foreign_key=fk_match.group(1) if fk_match else "",
                on_delete=delete_match.group(1) if delete_match else "",
                file=file_path,
                line_number=line,
            ))

        # HasMany...WithOne (OneToMany from principal side)
        for match in self.HAS_MANY_PATTERN.finditer(content):
            dependent = match.group(1) or ""
            nav = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1

            after = content[match.end():match.end() + 300]
            with_one = self.WITH_ONE_PATTERN.search(after)
            with_many = self.WITH_MANY_PATTERN.search(after)
            fk_match = self.HAS_FOREIGN_KEY_PATTERN.search(after)

            rel_type = "ManyToMany" if with_many else "OneToMany"

            relationships.append(EFCoreRelationshipInfo(
                dependent=dependent,
                relationship_type=rel_type,
                navigation_property=nav,
                foreign_key=fk_match.group(1) if fk_match else "",
                file=file_path,
                line_number=line,
            ))

        return relationships
