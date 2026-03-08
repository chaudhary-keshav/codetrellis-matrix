"""
CSharpModelExtractor - Extracts Entity Framework Core models, DbContext, and data patterns.

Extracts:
- Entity Framework Core DbContext classes
- Entity/Model classes with data annotations ([Table], [Column], [Key], etc.)
- Navigation properties and relationships (HasOne, HasMany, ManyToMany)
- Fluent API configurations (OnModelCreating, IEntityTypeConfiguration<T>)
- DbSet<T> properties (tracked entity types)
- EF Core migrations
- Repository pattern implementations
- Value objects and aggregate roots (DDD patterns)
- DTOs and view models
- AutoMapper profile configurations

Part of CodeTrellis v4.13 - C# Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSharpEntityInfo:
    """Information about a C# entity/model class."""
    name: str
    table_name: str = ""          # From [Table] attribute
    schema: str = ""              # From [Table] schema parameter
    base_class: str = ""
    properties: List[Dict[str, str]] = field(default_factory=list)  # name, type, annotations
    key_properties: List[str] = field(default_factory=list)  # [Key] annotated properties
    navigation_properties: List[Dict[str, str]] = field(default_factory=list)  # name, type, relationship
    indexes: List[str] = field(default_factory=list)  # From [Index] or fluent API
    is_abstract: bool = False
    is_owned: bool = False        # [Owned] attribute
    is_keyless: bool = False      # [Keyless] attribute
    implements: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpDbContextInfo:
    """Information about a C# EF Core DbContext."""
    name: str
    base_class: str = "DbContext"
    db_sets: List[Dict[str, str]] = field(default_factory=list)  # property_name, entity_type
    has_on_model_creating: bool = False
    uses_fluent_api: bool = False
    connection_string_name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpDTOInfo:
    """Information about a C# DTO / View Model."""
    name: str
    properties: List[Dict[str, str]] = field(default_factory=list)
    source_entity: str = ""  # If there's a clear mapping
    is_record: bool = False
    kind: str = "dto"  # dto, viewmodel, request, response, command, query
    file: str = ""
    line_number: int = 0


@dataclass
class CSharpRepositoryInfo:
    """Information about a C# repository implementation."""
    name: str
    interface: str = ""
    entity_type: str = ""
    methods: List[str] = field(default_factory=list)
    uses_dbcontext: bool = False
    file: str = ""
    line_number: int = 0


class CSharpModelExtractor:
    """
    Extracts C# data model / Entity Framework Core constructs.

    Handles:
    - DbContext detection (inherits DbContext/IdentityDbContext)
    - DbSet<T> property extraction
    - Entity classes with data annotations
    - Navigation properties and relationships
    - Fluent API configuration (IEntityTypeConfiguration<T>)
    - Repository pattern detection
    - DTO/ViewModel/Request/Response/Command/Query patterns
    - Value Objects and DDD patterns
    - AutoMapper profiles
    """

    # DbContext detection
    DBCONTEXT_PATTERN = re.compile(
        r'(?:public|internal)\s+class\s+(\w+)\s*:\s*'
        r'((?:Identity)?DbContext(?:<\w+>)?)\s*',
        re.MULTILINE
    )

    # DbSet<T> properties
    DBSET_PATTERN = re.compile(
        r'public\s+(?:virtual\s+)?DbSet<(\w+)>\s+(\w+)\s*\{',
        re.MULTILINE
    )

    # Table attribute
    TABLE_ATTR_PATTERN = re.compile(
        r'\[Table\s*\(\s*["\'](\w+)["\'](?:\s*,\s*Schema\s*=\s*["\'](\w+)["\'])?\s*\)\]'
    )

    # Key attribute
    KEY_ATTR_PATTERN = re.compile(r'\[Key\]')

    # Column attribute
    COLUMN_ATTR_PATTERN = re.compile(
        r'\[Column\s*\(\s*["\'](\w+)["\']\s*(?:,\s*TypeName\s*=\s*["\']([^"\']+)["\'])?\s*\)\]'
    )

    # Required attribute
    REQUIRED_ATTR_PATTERN = re.compile(r'\[Required\]')

    # MaxLength / StringLength
    LENGTH_ATTR_PATTERN = re.compile(
        r'\[(?:MaxLength|StringLength)\s*\(\s*(\d+)\s*\)\]'
    )

    # Entity class detection via data annotations or base class
    ENTITY_CLASS_PATTERN = re.compile(
        r'(?:\[Table\s*\([^\)]+\)\]\s*)?'
        r'(?:public|internal)\s+(?:abstract\s+)?class\s+(\w+)'
        r'(?:\s*:\s*([^\{]+))?\s*\{',
        re.MULTILINE
    )

    # Navigation property (virtual reference/collection)
    NAV_PROP_PATTERN = re.compile(
        r'public\s+virtual\s+'
        r'((?:ICollection|IList|List|HashSet|IEnumerable)<(\w+)>|(\w+))\s+'
        r'(\w+)\s*\{',
        re.MULTILINE
    )

    # IEntityTypeConfiguration<T>
    ENTITY_CONFIG_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IEntityTypeConfiguration<(\w+)>',
        re.MULTILINE
    )

    # Repository interface/class
    REPOSITORY_PATTERN = re.compile(
        r'(?:public|internal)\s+(?:class|interface)\s+(\w*Repository\w*)'
        r'(?:<(\w+)>)?'
        r'(?:\s*:\s*([^\{]+))?\s*\{',
        re.MULTILINE
    )

    # OnModelCreating
    ON_MODEL_CREATING = re.compile(
        r'(?:protected\s+)?override\s+void\s+OnModelCreating\s*\(',
        re.MULTILINE
    )

    # Owned attribute
    OWNED_PATTERN = re.compile(r'\[Owned\]')

    # Keyless attribute
    KEYLESS_PATTERN = re.compile(r'\[Keyless\]')

    # DTO / ViewModel naming patterns
    DTO_PATTERN = re.compile(
        r'(?:public|internal)\s+(?:sealed\s+)?(?:class|record(?:\s+struct)?)\s+'
        r'(\w+(?:Dto|DTO|ViewModel|Request|Response|Command|Query))\s*'
        r'(?:\([^)]*\))?\s*'  # record primary constructor
        r'(?:\{|;)',
        re.MULTILINE
    )

    # AutoMapper Profile
    AUTOMAPPER_PROFILE_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*Profile\s*\{',
        re.MULTILINE
    )
    AUTOMAPPER_MAP_PATTERN = re.compile(
        r'CreateMap<(\w+),\s*(\w+)>\s*\(',
    )

    # Fluent API: HasOne, HasMany, etc.
    FLUENT_RELATIONSHIP = re.compile(
        r'\.\s*(HasOne|HasMany|HasKey|HasIndex|HasAlternateKey|OwnsOne|OwnsMany)'
        r'(?:<(\w+)>)?',
    )

    # Property (for entity scanning)
    PROPERTY_PATTERN = re.compile(
        r'public\s+(?:required\s+)?(?:virtual\s+)?'
        r'([\w<>\[\]?,.\s]+?)\s+'
        r'(\w+)\s*\{\s*get',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all data model constructs from C# source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with keys: entities, db_contexts, dtos, repositories, entity_configs
        """
        result = {
            "entities": [],
            "db_contexts": [],
            "dtos": [],
            "repositories": [],
            "entity_configs": [],
        }

        result["db_contexts"] = self._extract_dbcontexts(content, file_path)
        result["entities"] = self._extract_entities(content, file_path)
        result["dtos"] = self._extract_dtos(content, file_path)
        result["repositories"] = self._extract_repositories(content, file_path)
        result["entity_configs"] = self._extract_entity_configs(content, file_path)

        return result

    def _extract_dbcontexts(self, content: str, file_path: str) -> List[CSharpDbContextInfo]:
        """Extract DbContext classes."""
        contexts = []
        for match in self.DBCONTEXT_PATTERN.finditer(content):
            name = match.group(1)
            base_class = match.group(2)

            # Extract DbSet properties
            db_sets = []
            for ds in self.DBSET_PATTERN.finditer(content):
                db_sets.append({
                    "entity_type": ds.group(1),
                    "property_name": ds.group(2),
                })

            has_on_model_creating = bool(self.ON_MODEL_CREATING.search(content))
            uses_fluent_api = bool(self.FLUENT_RELATIONSHIP.search(content))

            line_number = content[:match.start()].count('\n') + 1
            contexts.append(CSharpDbContextInfo(
                name=name,
                base_class=base_class,
                db_sets=db_sets,
                has_on_model_creating=has_on_model_creating,
                uses_fluent_api=uses_fluent_api,
                file=file_path,
                line_number=line_number,
            ))

        return contexts

    def _extract_entities(self, content: str, file_path: str) -> List[CSharpEntityInfo]:
        """Extract entity/model classes with data annotations."""
        entities = []
        lines = content.split('\n')

        # Look for classes that appear to be entities
        for match in self.ENTITY_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            base_clause = match.group(2) or ""

            # Check for Table attribute preceding the class
            preceding = content[:match.start()]
            table_name = ""
            schema = ""
            table_match = self.TABLE_ATTR_PATTERN.search(preceding[-300:] if len(preceding) > 300 else preceding)
            if table_match:
                table_name = table_match.group(1)
                schema = table_match.group(2) or ""

            is_owned = bool(self.OWNED_PATTERN.search(preceding[-200:] if len(preceding) > 200 else preceding))
            is_keyless = bool(self.KEYLESS_PATTERN.search(preceding[-200:] if len(preceding) > 200 else preceding))

            # Check if it's likely an entity (has Table attr, or has navigation properties, etc.)
            body_start = match.end()
            body_end = self._find_brace_end(content, body_start - 1)
            if body_end < 0:
                body_end = min(body_start + 3000, len(content))
            body = content[body_start:body_end]

            # Extract properties
            properties = []
            key_properties = []
            nav_properties = []

            for prop in self.PROPERTY_PATTERN.finditer(body):
                prop_type = prop.group(1).strip()
                prop_name = prop.group(2)

                # Check for [Key] before property
                prop_preceding = body[:prop.start()]
                prop_preceding_short = prop_preceding[-200:] if len(prop_preceding) > 200 else prop_preceding
                is_key = bool(self.KEY_ATTR_PATTERN.search(prop_preceding_short))
                is_required = bool(self.REQUIRED_ATTR_PATTERN.search(prop_preceding_short))

                annotations = []
                if is_key:
                    key_properties.append(prop_name)
                    annotations.append("[Key]")
                if is_required:
                    annotations.append("[Required]")

                length_m = self.LENGTH_ATTR_PATTERN.search(prop_preceding_short)
                if length_m:
                    annotations.append(f"[MaxLength({length_m.group(1)})]")

                properties.append({
                    "name": prop_name,
                    "type": prop_type,
                    "annotations": ", ".join(annotations),
                })

            for nav in self.NAV_PROP_PATTERN.finditer(body):
                full_type = nav.group(1)
                collection_inner = nav.group(2)
                single_ref = nav.group(3)
                nav_name = nav.group(4)

                if collection_inner:
                    nav_properties.append({
                        "name": nav_name,
                        "type": full_type,
                        "relationship": "collection",
                    })
                elif single_ref:
                    nav_properties.append({
                        "name": nav_name,
                        "type": single_ref,
                        "relationship": "reference",
                    })

            # Only include if it looks like an entity
            is_entity = (
                table_name
                or is_owned
                or is_keyless
                or key_properties
                or nav_properties
                or any(a.get("annotations") for a in properties)
            )
            if not is_entity:
                continue

            base_parts = [b.strip() for b in base_clause.split(',') if b.strip()]
            base_class = base_parts[0] if base_parts else ""
            implements = base_parts[1:] if len(base_parts) > 1 else []

            line_number = content[:match.start()].count('\n') + 1
            entities.append(CSharpEntityInfo(
                name=name,
                table_name=table_name,
                schema=schema,
                base_class=base_class,
                properties=properties[:50],
                key_properties=key_properties,
                navigation_properties=nav_properties,
                is_abstract='abstract' in content[max(0, match.start()-30):match.start()],
                is_owned=is_owned,
                is_keyless=is_keyless,
                implements=implements,
                file=file_path,
                line_number=line_number,
            ))

        return entities

    def _extract_dtos(self, content: str, file_path: str) -> List[CSharpDTOInfo]:
        """Extract DTOs, ViewModels, Request/Response types."""
        dtos = []
        for match in self.DTO_PATTERN.finditer(content):
            name = match.group(1)

            # Determine kind from suffix
            kind = "dto"
            name_lower = name.lower()
            if name_lower.endswith("viewmodel"):
                kind = "viewmodel"
            elif name_lower.endswith("request"):
                kind = "request"
            elif name_lower.endswith("response"):
                kind = "response"
            elif name_lower.endswith("command"):
                kind = "command"
            elif name_lower.endswith("query"):
                kind = "query"

            is_record = "record" in content[max(0, match.start()-20):match.start()+len(name)+20]

            # Extract properties
            body_start = match.end()
            body_end = self._find_brace_end(content, body_start - 1)
            if body_end < 0:
                body_end = min(body_start + 2000, len(content))
            body = content[body_start:body_end]

            properties = []
            for prop in self.PROPERTY_PATTERN.finditer(body):
                properties.append({
                    "name": prop.group(2),
                    "type": prop.group(1).strip(),
                })

            line_number = content[:match.start()].count('\n') + 1
            dtos.append(CSharpDTOInfo(
                name=name,
                properties=properties[:30],
                is_record=is_record,
                kind=kind,
                file=file_path,
                line_number=line_number,
            ))

        return dtos

    def _extract_repositories(self, content: str, file_path: str) -> List[CSharpRepositoryInfo]:
        """Extract repository pattern implementations."""
        repos = []
        for match in self.REPOSITORY_PATTERN.finditer(content):
            name = match.group(1)
            generic_type = match.group(2) or ""
            base_clause = match.group(3) or ""

            # Check if it's a class (not interface) and uses DbContext
            is_class = "class" in content[max(0, match.start()-20):match.start()+5]
            uses_db = bool(re.search(r'_(?:context|db|dbContext)\b', content))

            # Extract methods
            methods = []
            method_re = re.compile(
                r'public\s+(?:async\s+)?(?:virtual\s+)?[\w<>\[\]?,.\s]+\s+(\w+)\s*\(',
                re.MULTILINE
            )
            body_start = match.end()
            body_end = self._find_brace_end(content, body_start - 1)
            if body_end < 0:
                body_end = min(body_start + 3000, len(content))
            body = content[body_start:body_end]
            for m in method_re.finditer(body):
                mname = m.group(1)
                if mname not in ('Dispose', 'ToString', name):
                    methods.append(mname)

            interface = ""
            if base_clause:
                parts = [p.strip() for p in base_clause.split(',')]
                for p in parts:
                    if p.startswith('I') and 'Repository' in p:
                        interface = p
                        break

            line_number = content[:match.start()].count('\n') + 1
            repos.append(CSharpRepositoryInfo(
                name=name,
                interface=interface,
                entity_type=generic_type,
                methods=methods[:20],
                uses_dbcontext=uses_db and is_class,
                file=file_path,
                line_number=line_number,
            ))

        return repos

    def _extract_entity_configs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract IEntityTypeConfiguration<T> implementations."""
        configs = []
        for match in self.ENTITY_CONFIG_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            configs.append({
                "config_class": match.group(1),
                "entity_type": match.group(2),
                "file": file_path,
                "line_number": line_number,
            })
        return configs

    def _find_brace_end(self, content: str, start: int) -> int:
        """Find matching closing brace from start position."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1
