"""
Django Admin Extractor for CodeTrellis.

Extracts Django admin site configurations including ModelAdmin,
InlineAdmin, admin.site.register, list_display, filters, etc.
Supports Django 1.x - 5.x admin patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoInlineAdminInfo:
    """Information about a Django inline admin."""
    name: str
    model: Optional[str] = None
    inline_type: str = "TabularInline"  # TabularInline, StackedInline
    extra: int = 3
    max_num: Optional[int] = None
    fields: List[str] = field(default_factory=list)


@dataclass
class DjangoAdminInfo:
    """Information about a Django ModelAdmin."""
    name: str
    file: str = ""
    model: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    list_display: List[str] = field(default_factory=list)
    list_filter: List[str] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)
    ordering: List[str] = field(default_factory=list)
    readonly_fields: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    fieldsets: List[str] = field(default_factory=list)
    inlines: List[DjangoInlineAdminInfo] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    raw_id_fields: List[str] = field(default_factory=list)
    prepopulated_fields: Dict[str, List[str]] = field(default_factory=dict)
    autocomplete_fields: List[str] = field(default_factory=list)
    is_registered: bool = False
    decorator_register: bool = False  # @admin.register()
    line_number: int = 0


ADMIN_BASE_CLASSES = {
    'ModelAdmin', 'TabularInline', 'StackedInline',
    'InlineModelAdmin', 'SimpleListFilter',
    'admin.ModelAdmin', 'admin.TabularInline', 'admin.StackedInline',
}


class DjangoAdminExtractor:
    """
    Extracts Django admin configurations.

    Handles:
    - ModelAdmin classes with all attributes
    - @admin.register() decorator pattern
    - admin.site.register() function call pattern
    - Inline admins (TabularInline, StackedInline)
    - Custom admin actions
    - list_display, list_filter, search_fields, etc.
    """

    ADMIN_CLASS_PATTERN = re.compile(
        r'^(?:@admin\.register\(([^)]+)\)\s*\n)?class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    REGISTER_PATTERN = re.compile(
        r'admin\.site\.register\s*\(\s*(\w+)\s*(?:,\s*(\w+))?\s*\)',
        re.MULTILINE
    )

    LIST_ATTR_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*[\[\(]([^\]\)]*?)[\]\)]',
        re.MULTILINE | re.DOTALL
    )

    INLINE_PATTERN = re.compile(
        r'^\s{4}inlines\s*=\s*[\[\(]([^\]\)]+)[\]\)]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Django admin extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django admin configurations.

        Returns:
            Dict with 'admin_classes' and 'registrations'
        """
        admin_classes = []
        registrations = []

        # Extract admin classes (with optional @admin.register decorator)
        for match in self.ADMIN_CLASS_PATTERN.finditer(content):
            register_models = match.group(1)
            class_name = match.group(2)
            bases_str = match.group(3)
            bases = [b.strip() for b in bases_str.split(',')]

            # Check if this is an admin class
            is_admin = any(
                b.strip().split('.')[-1] in ('ModelAdmin', 'TabularInline',
                                              'StackedInline', 'InlineModelAdmin',
                                              'SimpleListFilter')
                for b in bases
            )
            if not is_admin:
                continue

            class_body = self._extract_class_body(content, match.end())

            # Extract attributes
            attrs = self._extract_list_attrs(class_body)

            # Determine model from @admin.register or from class body
            model = None
            decorator_register = False
            if register_models:
                model = register_models.strip().split(',')[0].strip()
                decorator_register = True

            admin_info = DjangoAdminInfo(
                name=class_name,
                file=file_path,
                model=model,
                base_classes=bases,
                list_display=attrs.get('list_display', []),
                list_filter=attrs.get('list_filter', []),
                search_fields=attrs.get('search_fields', []),
                ordering=attrs.get('ordering', []),
                readonly_fields=attrs.get('readonly_fields', []),
                fields=attrs.get('fields', []),
                actions=attrs.get('actions', []),
                raw_id_fields=attrs.get('raw_id_fields', []),
                autocomplete_fields=attrs.get('autocomplete_fields', []),
                is_registered=decorator_register,
                decorator_register=decorator_register,
                line_number=content[:match.start()].count('\n') + 1,
            )
            admin_classes.append(admin_info)

        # Extract admin.site.register() calls
        for match in self.REGISTER_PATTERN.finditer(content):
            model_name = match.group(1)
            admin_class = match.group(2)
            registrations.append({
                'model': model_name,
                'admin_class': admin_class,
                'line_number': content[:match.start()].count('\n') + 1,
            })

            # Link to admin class if found
            for ac in admin_classes:
                if admin_class and ac.name == admin_class:
                    ac.model = model_name
                    ac.is_registered = True

        return {
            'admin_classes': admin_classes,
            'registrations': registrations,
        }

    def _extract_list_attrs(self, class_body: str) -> Dict[str, List[str]]:
        """Extract list attributes from admin class body."""
        result = {}
        for match in self.LIST_ATTR_PATTERN.finditer(class_body):
            attr_name = match.group(1)
            value_str = match.group(2)
            items = re.findall(r"['\"]([^'\"]+)['\"]", value_str)
            if not items:
                # Try identifiers (for inlines, actions)
                items = [i.strip() for i in value_str.split(',') if i.strip()]
            result[attr_name] = items
        return result

    def _extract_class_body(self, content: str, class_end: int) -> str:
        """Extract class body using indentation."""
        lines = content.split('\n')
        start_line = content[:class_end].count('\n')
        body_lines = []

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent < 4 and line.strip():
                break
            body_lines.append(line)

        return '\n'.join(body_lines)
