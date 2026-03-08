"""
Django View & URL Extractor for CodeTrellis.

Extracts Django views (CBVs and FBVs), URL patterns, viewsets (DRF).
Supports Django 1.x - 5.x URL configurations and view patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoViewInfo:
    """Information about a Django view."""
    name: str
    view_type: str  # function, class, viewset, apiview, generic
    file: str = ""
    methods: List[str] = field(default_factory=list)  # GET, POST, etc.
    mixins: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    template_name: Optional[str] = None
    model: Optional[str] = None
    queryset: Optional[str] = None
    serializer_class: Optional[str] = None
    permission_classes: List[str] = field(default_factory=list)
    authentication_classes: List[str] = field(default_factory=list)
    is_async: bool = False
    actions: List[str] = field(default_factory=list)  # For ViewSets
    line_number: int = 0


@dataclass
class DjangoURLPatternInfo:
    """Information about a Django URL pattern."""
    path: str
    view: str
    name: Optional[str] = None
    pattern_type: str = "path"  # path, re_path, url (legacy)
    methods: List[str] = field(default_factory=list)
    namespace: Optional[str] = None
    app_name: Optional[str] = None
    is_include: bool = False
    include_module: Optional[str] = None
    line_number: int = 0


# Django CBV base classes
DJANGO_VIEW_BASES = {
    # Core views
    'View', 'TemplateView', 'RedirectView',
    # Detail views
    'DetailView', 'ListView',
    # Edit views
    'CreateView', 'UpdateView', 'DeleteView', 'FormView',
    # Date views
    'ArchiveIndexView', 'YearArchiveView', 'MonthArchiveView',
    'DayArchiveView', 'TodayArchiveView', 'DateDetailView',
    # DRF views
    'APIView', 'GenericAPIView',
    'ViewSet', 'ModelViewSet', 'ReadOnlyModelViewSet',
    'GenericViewSet', 'ViewSetMixin',
    # DRF generic views
    'CreateAPIView', 'ListAPIView', 'RetrieveAPIView',
    'DestroyAPIView', 'UpdateAPIView',
    'ListCreateAPIView', 'RetrieveUpdateAPIView',
    'RetrieveDestroyAPIView', 'RetrieveUpdateDestroyAPIView',
}

DJANGO_VIEW_MIXINS = {
    'LoginRequiredMixin', 'PermissionRequiredMixin', 'UserPassesTestMixin',
    'AccessMixin', 'MultipleObjectMixin', 'SingleObjectMixin',
    'FormMixin', 'ModelFormMixin', 'ProcessFormView',
    'ContextMixin', 'TemplateResponseMixin',
    # DRF mixins
    'CreateModelMixin', 'ListModelMixin', 'RetrieveModelMixin',
    'UpdateModelMixin', 'DestroyModelMixin',
}


class DjangoViewExtractor:
    """
    Extracts Django view definitions and URL patterns.

    Handles:
    - Function-based views (FBVs)
    - Class-based views (CBVs) — all generic views
    - Django REST Framework ViewSets and APIViews
    - URL patterns (path, re_path, url)
    - URL includes and namespaces
    - Decorators (@login_required, @api_view, etc.)
    - Async views (Django 4.1+)
    """

    # View class pattern
    VIEW_CLASS_PATTERN = re.compile(
        r'^class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    # Function-based view patterns (decorated with @)
    FBV_DECORATOR_PATTERN = re.compile(
        r'@(api_view|require_http_methods|require_GET|require_POST|require_safe|csrf_exempt|login_required|permission_required)\s*(?:\(\s*([^)]*)\s*\))?\s*\n(?:@\w+[^\n]*\n)*\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # URL pattern: path('route/', view, name='name')
    PATH_PATTERN = re.compile(
        r"(?:path|re_path|url)\s*\(\s*[r]?['\"]([^'\"]*)['\"]"
        r"\s*,\s*([^,\)]+)"
        r"(?:\s*,\s*name\s*=\s*['\"]([^'\"]+)['\"])?"
        r"[^)]*\)",
        re.MULTILINE
    )

    # URL include pattern
    INCLUDE_PATTERN = re.compile(
        r"path\s*\(\s*['\"]([^'\"]*)['\"]"
        r"\s*,\s*include\s*\(\s*['\"]?([^'\",\)]+)['\"]?"
        r"(?:\s*,\s*namespace\s*=\s*['\"]([^'\"]+)['\"])?"
        r"[^)]*\)",
        re.MULTILINE
    )

    # Attribute pattern inside class
    ATTR_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(.+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Django view extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django views and URL patterns.

        Returns:
            Dict with 'views' and 'url_patterns'
        """
        views = []

        # Extract class-based views
        views.extend(self._extract_class_views(content, file_path))

        # Extract function-based views
        views.extend(self._extract_function_views(content, file_path))

        # Extract URL patterns
        url_patterns = self._extract_url_patterns(content)

        return {
            'views': views,
            'url_patterns': url_patterns,
        }

    def _extract_class_views(self, content: str, file_path: str) -> List[DjangoViewInfo]:
        """Extract class-based views."""
        views = []

        for match in self.VIEW_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip() for b in bases_str.split(',')]

            # Check if this is a Django view
            view_type = self._classify_view(bases)
            if not view_type:
                continue

            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body = self._extract_class_body(content, match.end())

            # Extract attributes
            attrs = dict(self.ATTR_PATTERN.findall(class_body))

            # Determine HTTP methods from class methods
            methods = []
            for m in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'list', 'create', 'retrieve', 'update', 'destroy']:
                if re.search(rf'^\s{{4}}(?:async\s+)?def\s+{m}\s*\(', class_body, re.MULTILINE):
                    methods.append(m.upper())

            # Extract actions for viewsets
            actions = []
            action_matches = re.findall(r'@action\s*\([^)]*\)\s*\n\s*(?:async\s+)?def\s+(\w+)', class_body)
            actions = action_matches

            # Extract mixins
            mixins = [b for b in bases if b.endswith('Mixin') or b in DJANGO_VIEW_MIXINS]

            # Extract permission and authentication classes
            permission_classes = self._extract_list_attr(attrs.get('permission_classes', ''))
            authentication_classes = self._extract_list_attr(attrs.get('authentication_classes', ''))

            view = DjangoViewInfo(
                name=class_name,
                view_type=view_type,
                file=file_path,
                methods=methods,
                mixins=mixins,
                base_classes=bases,
                template_name=self._extract_string_value(attrs.get('template_name', '')),
                model=attrs.get('model', '').strip(),
                queryset=attrs.get('queryset', '').strip() or None,
                serializer_class=attrs.get('serializer_class', '').strip() or None,
                permission_classes=permission_classes,
                authentication_classes=authentication_classes,
                actions=actions,
                line_number=line_number,
            )
            views.append(view)

        return views

    def _extract_function_views(self, content: str, file_path: str) -> List[DjangoViewInfo]:
        """Extract function-based views (decorated functions)."""
        views = []

        for match in self.FBV_DECORATOR_PATTERN.finditer(content):
            decorator = match.group(1)
            decorator_args = match.group(2) or ""
            is_async = match.group(3) is not None
            func_name = match.group(4)

            methods = ['GET']
            if decorator == 'api_view':
                methods = re.findall(r"['\"](\w+)['\"]", decorator_args)
                methods = [m.upper() for m in methods] if methods else ['GET']
            elif decorator == 'require_http_methods':
                methods = re.findall(r"['\"](\w+)['\"]", decorator_args)
                methods = [m.upper() for m in methods]
            elif decorator == 'require_POST':
                methods = ['POST']
            elif decorator == 'require_GET':
                methods = ['GET']

            # Collect all decorators for this function
            decorators = [decorator]
            pre_content = content[:match.start()]
            # Look for decorator lines just before
            decorator_lines = re.findall(r'@(\w+(?:\.\w+)*)', pre_content[-500:] if len(pre_content) > 500 else pre_content)

            view = DjangoViewInfo(
                name=func_name,
                view_type='function' if decorator != 'api_view' else 'apiview',
                file=file_path,
                methods=methods,
                decorators=decorators,
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            )
            views.append(view)

        return views

    def _extract_url_patterns(self, content: str) -> List[DjangoURLPatternInfo]:
        """Extract URL patterns from urlconf."""
        patterns = []

        # Extract include patterns
        for match in self.INCLUDE_PATTERN.finditer(content):
            patterns.append(DjangoURLPatternInfo(
                path=match.group(1),
                view='include',
                name=None,
                pattern_type='path',
                is_include=True,
                include_module=match.group(2).strip().strip("'\""),
                namespace=match.group(3),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract path/re_path/url patterns
        for match in self.PATH_PATTERN.finditer(content):
            path_str = match.group(1)
            view_str = match.group(2).strip()
            name = match.group(3)

            # Skip if this is an include (already captured above)
            if 'include(' in view_str:
                continue

            # Determine pattern type
            line = content[max(0, content.rfind('\n', 0, match.start())):match.start()]
            pattern_type = 'path'
            if 're_path' in line or 'url(' in line:
                pattern_type = 're_path'

            patterns.append(DjangoURLPatternInfo(
                path=path_str,
                view=view_str,
                name=name,
                pattern_type=pattern_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return patterns

    def _classify_view(self, bases: List[str]) -> Optional[str]:
        """Classify the type of view from its base classes."""
        for base in bases:
            clean = base.split('.')[-1].strip()
            if clean in ('ViewSet', 'ModelViewSet', 'ReadOnlyModelViewSet', 'GenericViewSet'):
                return 'viewset'
            if clean in ('APIView', 'GenericAPIView') or clean.endswith('APIView'):
                return 'apiview'
            if clean in ('View', 'TemplateView', 'RedirectView'):
                return 'class'
            if clean in DJANGO_VIEW_BASES:
                return 'generic'
            if clean in DJANGO_VIEW_MIXINS:
                continue  # Mixins alone don't make a view
        return None

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

    def _extract_list_attr(self, value: str) -> List[str]:
        """Extract a list attribute value like [IsAuthenticated, AllowAny]."""
        items = re.findall(r'(\w+)', value)
        return [i for i in items if i[0].isupper()]

    def _extract_string_value(self, value: str) -> Optional[str]:
        """Extract a string value from attribute."""
        match = re.search(r"['\"]([^'\"]+)['\"]", value)
        return match.group(1) if match else None
