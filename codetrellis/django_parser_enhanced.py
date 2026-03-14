"""
EnhancedDjangoParser v1.0 - Comprehensive Django parser using all extractors.

This parser integrates all Django extractors to provide complete parsing of
Django application files. It runs as a supplementary layer on top of the
Python parser, extracting Django-specific semantics.

Supports:
- Django 1.x (url(), FBVs, old-style middleware, South migrations)
- Django 2.x (path(), re_path(), new-style middleware, ASGI prep)
- Django 3.x (ASGI, async views, JSONField, PathConverter)
- Django 4.x (async ORM, simplified timezone, Redis cache, async middleware)
- Django 5.x (GeneratedField, field groups, facet filters, db_default)

Django-specific extraction:
- Models: fields, relationships, Meta, managers, abstract/proxy
- Views: CBVs (all generics), FBVs, ViewSets (DRF), APIViews
- URLs: path(), re_path(), include(), namespaces
- Middleware: old-style, new-style, function-based, async
- Forms: Form, ModelForm, FormSets, clean methods, widgets
- Admin: ModelAdmin, inlines, list_display, filters, actions
- Signals: pre/post_save, pre/post_delete, custom signals
- Serializers (DRF): Serializer, ModelSerializer, nested, validators
- Settings: INSTALLED_APPS, DATABASES, REST_FRAMEWORK, MIDDLEWARE

Framework detection (30+ Django ecosystem patterns):
- Core: django, django.db, django.views
- DRF: rest_framework, serializers, viewsets, routers
- Auth: allauth, oauth2_provider, guardian, django-axes
- Celery: celery, django-celery-beat, django-celery-results
- Channels: channels, daphne, channel layers
- Storage: django-storages, whitenoise
- Search: django-elasticsearch-dsl, django-haystack
- Admin: django-grappelli, django-import-export
- API Docs: drf-yasg, drf-spectacular
- Testing: pytest-django, factory-boy, faker

Part of CodeTrellis v4.33 - Django Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Django extractors
from .extractors.django import (
    DjangoModelExtractor, DjangoModelInfo, DjangoFieldInfo, DjangoRelationshipInfo,
    DjangoViewExtractor, DjangoViewInfo, DjangoURLPatternInfo,
    DjangoMiddlewareExtractor, DjangoMiddlewareInfo,
    DjangoFormExtractor, DjangoFormInfo,
    DjangoAdminExtractor, DjangoAdminInfo,
    DjangoSignalExtractor, DjangoSignalInfo,
    DjangoSerializerExtractor, DjangoSerializerInfo,
    DjangoAPIExtractor, DjangoProjectInfo,
)


@dataclass
class DjangoParseResult:
    """Complete parse result for a Django file."""
    file_path: str
    file_type: str = "module"  # model, view, url, middleware, form, admin, signal, serializer, settings, migration, test, management, template_tag

    # Models
    models: List[DjangoModelInfo] = field(default_factory=list)

    # Views
    views: List[DjangoViewInfo] = field(default_factory=list)

    # URL patterns
    url_patterns: List[DjangoURLPatternInfo] = field(default_factory=list)

    # Middleware
    middleware: List[DjangoMiddlewareInfo] = field(default_factory=list)
    middleware_config: List[str] = field(default_factory=list)

    # Forms
    forms: List[DjangoFormInfo] = field(default_factory=list)

    # Admin
    admin_classes: List[DjangoAdminInfo] = field(default_factory=list)
    admin_registrations: List[Dict[str, Any]] = field(default_factory=list)

    # Signals
    signal_connections: List[DjangoSignalInfo] = field(default_factory=list)
    custom_signals: List[Any] = field(default_factory=list)

    # Serializers (DRF)
    serializers: List[DjangoSerializerInfo] = field(default_factory=list)

    # Project config
    project_info: Optional[DjangoProjectInfo] = None

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    django_version: str = ""
    is_drf: bool = False
    total_models: int = 0
    total_views: int = 0
    total_urls: int = 0


class EnhancedDjangoParser:
    """
    Enhanced Django parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the Python parser when Django
    framework is detected. It extracts Django-specific semantics that
    the language parser cannot capture.

    Framework detection supports 30+ Django ecosystem libraries.
    """

    # Django ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Django ───────────────────────────────────────────
        'django': re.compile(
            r'from\s+django\s+import|import\s+django|'
            r'from\s+django\.\w+|django\.conf\.settings',
            re.MULTILINE
        ),
        'django.db': re.compile(
            r'from\s+django\.db\s+import|from\s+django\.db\.models',
            re.MULTILINE
        ),
        'django.views': re.compile(
            r'from\s+django\.views|from\s+django\.views\.generic',
            re.MULTILINE
        ),
        'django.forms': re.compile(
            r'from\s+django\s+import\s+forms|from\s+django\.forms',
            re.MULTILINE
        ),
        'django.admin': re.compile(
            r'from\s+django\.contrib\s+import\s+admin|from\s+django\.contrib\.admin',
            re.MULTILINE
        ),

        # ── Django REST Framework ─────────────────────────────────
        'rest_framework': re.compile(
            r'from\s+rest_framework|import\s+rest_framework',
            re.MULTILINE
        ),
        'drf.serializers': re.compile(
            r'from\s+rest_framework\.serializers|from\s+rest_framework\s+import\s+serializers',
            re.MULTILINE
        ),
        'drf.viewsets': re.compile(
            r'from\s+rest_framework\.viewsets|from\s+rest_framework\s+import\s+viewsets',
            re.MULTILINE
        ),
        'drf.routers': re.compile(
            r'from\s+rest_framework\.routers|from\s+rest_framework\s+import\s+routers',
            re.MULTILINE
        ),
        'drf.permissions': re.compile(
            r'from\s+rest_framework\.permissions|from\s+rest_framework\s+import\s+permissions',
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'allauth': re.compile(
            r'from\s+allauth|import\s+allauth|["\']allauth',
            re.MULTILINE
        ),
        'oauth2_provider': re.compile(
            r'from\s+oauth2_provider|["\']oauth2_provider',
            re.MULTILINE
        ),
        'guardian': re.compile(
            r'from\s+guardian|["\']guardian',
            re.MULTILINE
        ),

        # ── Celery ────────────────────────────────────────────────
        'celery': re.compile(
            r'from\s+celery\s+import|import\s+celery|'
            r'@\w+\.task|@shared_task',
            re.MULTILINE
        ),
        'django_celery_beat': re.compile(
            r'from\s+django_celery_beat|["\']django_celery_beat',
            re.MULTILINE
        ),

        # ── Channels ─────────────────────────────────────────────
        'channels': re.compile(
            r'from\s+channels|import\s+channels|'
            r'ASGI_APPLICATION|CHANNEL_LAYERS',
            re.MULTILINE
        ),

        # ── Storage ──────────────────────────────────────────────
        'storages': re.compile(
            r'from\s+storages|["\']storages',
            re.MULTILINE
        ),
        'whitenoise': re.compile(
            r'from\s+whitenoise|["\']whitenoise',
            re.MULTILINE
        ),

        # ── API Documentation ────────────────────────────────────
        'drf_yasg': re.compile(
            r'from\s+drf_yasg|["\']drf_yasg',
            re.MULTILINE
        ),
        'drf_spectacular': re.compile(
            r'from\s+drf_spectacular|["\']drf_spectacular',
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'pytest_django': re.compile(
            r'import\s+pytest|@pytest\.mark\.django_db|'
            r'from\s+django\.test\s+import',
            re.MULTILINE
        ),
        'factory_boy': re.compile(
            r'from\s+factory|import\s+factory',
            re.MULTILINE
        ),

        # ── Admin Extensions ─────────────────────────────────────
        'grappelli': re.compile(
            r'from\s+grappelli|["\']grappelli',
            re.MULTILINE
        ),
        'import_export': re.compile(
            r'from\s+import_export|["\']import_export',
            re.MULTILINE
        ),

        # ── Search ───────────────────────────────────────────────
        'elasticsearch_dsl': re.compile(
            r'from\s+django_elasticsearch_dsl|["\']django_elasticsearch_dsl',
            re.MULTILINE
        ),
        'haystack': re.compile(
            r'from\s+haystack|["\']haystack',
            re.MULTILINE
        ),

        # ── CORS / Security ──────────────────────────────────────
        'corsheaders': re.compile(
            r'from\s+corsheaders|["\']corsheaders',
            re.MULTILINE
        ),

        # ── Caching ──────────────────────────────────────────────
        'django_redis': re.compile(
            r'from\s+django_redis|["\']django_redis',
            re.MULTILINE
        ),

        # ── Debug ────────────────────────────────────────────────
        'debug_toolbar': re.compile(
            r'from\s+debug_toolbar|["\']debug_toolbar',
            re.MULTILINE
        ),
    }

    # Django version detection from features
    DJANGO_VERSION_FEATURES = {
        'GeneratedField': '5.0',
        'db_default': '5.0',
        'aiter': '4.1',
        'async def': '4.1',  # async views
        'JSONField': '3.1',
        'ASGI_APPLICATION': '3.0',
        'path(': '2.0',
        're_path(': '2.0',
        'url(': '1.0',
    }

    def __init__(self):
        """Initialize the parser with all Django extractors."""
        self.model_extractor = DjangoModelExtractor()
        self.view_extractor = DjangoViewExtractor()
        self.middleware_extractor = DjangoMiddlewareExtractor()
        self.form_extractor = DjangoFormExtractor()
        self.admin_extractor = DjangoAdminExtractor()
        self.signal_extractor = DjangoSignalExtractor()
        self.serializer_extractor = DjangoSerializerExtractor()
        self.api_extractor = DjangoAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> DjangoParseResult:
        """
        Parse Django source code and extract all Django-specific information.

        This should be called AFTER the Python parser has run, when
        Django framework is detected. It extracts Django-specific semantics.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            DjangoParseResult with all extracted Django information
        """
        result = DjangoParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Check if DRF is present
        result.is_drf = any(f.startswith('rest_framework') or f.startswith('drf') for f in result.detected_frameworks)

        # ── Models ───────────────────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        if isinstance(model_result, list):
            result.models = model_result
        else:
            result.models = model_result.get('models', [])
        result.total_models = len(result.models)

        # ── Views ────────────────────────────────────────────────
        view_result = self.view_extractor.extract(content, file_path)
        result.views = view_result.get('views', [])
        result.url_patterns = view_result.get('url_patterns', [])
        result.total_views = len(result.views)
        result.total_urls = len(result.url_patterns)

        # ── Middleware ───────────────────────────────────────────
        mw_result = self.middleware_extractor.extract(content, file_path)
        result.middleware = mw_result.get('middleware', [])
        result.middleware_config = mw_result.get('middleware_config', [])

        # ── Forms ────────────────────────────────────────────────
        form_result = self.form_extractor.extract(content, file_path)
        result.forms = form_result.get('forms', [])

        # ── Admin ────────────────────────────────────────────────
        admin_result = self.admin_extractor.extract(content, file_path)
        result.admin_classes = admin_result.get('admin_classes', [])
        result.admin_registrations = admin_result.get('registrations', [])

        # ── Signals ──────────────────────────────────────────────
        signal_result = self.signal_extractor.extract(content, file_path)
        result.signal_connections = signal_result.get('signal_connections', [])
        result.custom_signals = signal_result.get('custom_signals', [])

        # ── Serializers (DRF) ────────────────────────────────────
        if result.is_drf or 'serializers' in content:
            ser_result = self.serializer_extractor.extract(content, file_path)
            result.serializers = ser_result.get('serializers', [])

        # ── Project config (settings files) ──────────────────────
        if result.file_type == 'settings':
            api_result = self.api_extractor.extract(content, file_path)
            result.project_info = api_result.get('project_info')

        # ── Version detection ────────────────────────────────────
        result.django_version = self._detect_django_version(content)

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Django file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # By filename conventions
        if basename.startswith('models') or basename == 'models.py':
            return 'model'
        if basename.startswith('views') or basename == 'views.py':
            return 'view'
        if basename.startswith('urls') or basename == 'urls.py':
            return 'url'
        if basename.startswith('forms') or basename == 'forms.py':
            return 'form'
        if basename.startswith('admin') or basename == 'admin.py':
            return 'admin'
        if basename.startswith('serializers') or basename == 'serializers.py':
            return 'serializer'
        if basename.startswith('signals') or basename == 'signals.py':
            return 'signal'
        if basename.startswith('middleware') or basename == 'middleware.py':
            return 'middleware'
        if 'settings' in basename:
            return 'settings'
        if basename.startswith('test') or basename.startswith('conftest'):
            return 'test'
        if 'migration' in normalized:
            return 'migration'
        if 'management/commands' in normalized:
            return 'management'
        if 'templatetags' in normalized:
            return 'template_tag'

        # By directory conventions
        if '/models/' in normalized:
            return 'model'
        if '/views/' in normalized:
            return 'view'
        if '/serializers/' in normalized:
            return 'serializer'
        if '/forms/' in normalized:
            return 'form'
        if '/admin/' in normalized:
            return 'admin'

        # By content
        if 'class Meta:' in content and ('models.Model' in content or 'models.CharField' in content):
            return 'model'
        if 'urlpatterns' in content:
            return 'url'
        if 'admin.site.register' in content or '@admin.register' in content:
            return 'admin'
        if 'INSTALLED_APPS' in content:
            return 'settings'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Django ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_django_version(self, content: str) -> str:
        """
        Detect the minimum Django version required by the file.

        Returns version string (e.g., '5.0', '4.1', '3.0').
        """
        max_version = '0.0'

        for feature, version in self.DJANGO_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_django_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file is a Django-specific file worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file contains Django-specific patterns
        """
        # Direct Django imports
        if re.search(r'from\s+django\s+import|from\s+django\.\w+', content):
            return True

        # DRF imports
        if re.search(r'from\s+rest_framework', content):
            return True

        # Django model patterns
        if re.search(r'class\s+\w+\s*\(\s*(?:models\.Model|admin\.ModelAdmin|forms\.(?:Model)?Form)', content):
            return True

        # Django URL patterns
        if 'urlpatterns' in content:
            return True

        # Django settings
        if 'INSTALLED_APPS' in content or 'DATABASES' in content:
            return True

        # Django file path conventions
        normalized = file_path.replace('\\', '/').lower()
        django_paths = ['/models/', '/views/', '/urls/', '/admin/', '/forms/',
                        '/serializers/', '/signals/', '/middleware/',
                        '/management/commands/', '/templatetags/', '/migrations/']
        if any(p in normalized for p in django_paths):
            return True

        return False

    def to_codetrellis_format(self, result: DjangoParseResult) -> str:
        """
        Convert parse result to CodeTrellis compressed format.

        Args:
            result: DjangoParseResult from parsing

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # File header
        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")

        if result.detected_frameworks:
            lines.append(f"[DJANGO_ECOSYSTEM:{','.join(result.detected_frameworks)}]")

        if result.django_version:
            lines.append(f"[DJANGO_VERSION:>={result.django_version}]")

        lines.append("")

        # Models section
        if result.models:
            lines.append("=== DJANGO_MODELS ===")
            for m in result.models:
                fields_str = ", ".join(f"{f.name}:{f.field_type}" for f in m.fields[:10])
                rels = ", ".join(f"{r.name}->{r.related_model}" for r in m.relationships)
                meta = ""
                if m.meta:
                    meta_parts = []
                    if m.meta.ordering:
                        meta_parts.append(f"ordering={m.meta.ordering}")
                    if m.meta.unique_together:
                        meta_parts.append(f"unique_together={m.meta.unique_together}")
                    meta = f"|Meta({','.join(meta_parts)})" if meta_parts else ""
                abstract = "|abstract" if m.is_abstract else ""
                proxy = "|proxy" if m.is_proxy else ""
                lines.append(f"  {m.name}({','.join(m.bases)}){abstract}{proxy}: {fields_str}")
                if rels:
                    lines.append(f"    rels: {rels}")
                if meta:
                    lines.append(f"    {meta}")
            lines.append("")

        # Views section
        if result.views:
            lines.append("=== DJANGO_VIEWS ===")
            for v in result.views:
                methods_str = ",".join(v.methods) if v.methods else ""
                template = f"|tpl:{v.template_name}" if v.template_name else ""
                model = f"|model:{v.model}" if v.model else ""
                async_str = "|async" if v.is_async else ""
                lines.append(f"  {v.name}[{v.view_type}]({methods_str}){template}{model}{async_str}")
            lines.append("")

        # URL patterns
        if result.url_patterns:
            lines.append("=== DJANGO_URLS ===")
            for u in result.url_patterns:
                if u.is_include:
                    lines.append(f"  {u.path} → include({u.include_module}){f'|ns:{u.namespace}' if u.namespace else ''}")
                else:
                    name = f"|name:{u.name}" if u.name else ""
                    lines.append(f"  {u.pattern_type}('{u.path}') → {u.view}{name}")
            lines.append("")

        # Middleware
        if result.middleware:
            lines.append("=== DJANGO_MIDDLEWARE ===")
            for mw in result.middleware:
                hooks = ",".join(mw.hooks) if mw.hooks else ""
                async_str = "|async" if mw.is_async else ""
                lines.append(f"  {mw.name}[{mw.middleware_type}]({hooks}){async_str}")
            lines.append("")

        # Forms
        if result.forms:
            lines.append("=== DJANGO_FORMS ===")
            for f in result.forms:
                model = f"|model:{f.model}" if f.model else ""
                field_count = len(f.fields)
                clean_count = len(f.clean_methods)
                lines.append(f"  {f.name}[{f.form_type}]{model}|fields:{field_count}|validators:{clean_count}")
            lines.append("")

        # Admin
        if result.admin_classes:
            lines.append("=== DJANGO_ADMIN ===")
            for a in result.admin_classes:
                model = f"|model:{a.model}" if a.model else ""
                display = f"|list_display:{','.join(a.list_display[:5])}" if a.list_display else ""
                filters = f"|filters:{','.join(a.list_filter[:5])}" if a.list_filter else ""
                lines.append(f"  {a.name}{model}{display}{filters}")
            lines.append("")

        # Signals
        if result.signal_connections:
            lines.append("=== DJANGO_SIGNALS ===")
            for s in result.signal_connections:
                sender = f"|sender:{s.sender}" if s.sender else ""
                lines.append(f"  @{s.name} → {s.receiver_name}{sender}")
            lines.append("")

        # Serializers (DRF)
        if result.serializers:
            lines.append("=== DRF_SERIALIZERS ===")
            for s in result.serializers:
                model = f"|model:{s.model}" if s.model else ""
                field_count = len(s.fields)
                meta_fields = f"|fields:{','.join(s.meta_fields[:8])}" if s.meta_fields else ""
                nested = f"|nested:{','.join(s.nested_serializers)}" if s.nested_serializers else ""
                lines.append(f"  {s.name}[{s.serializer_type}]{model}{meta_fields}{nested}|field_count:{field_count}")
            lines.append("")

        # Settings / Project info
        if result.project_info:
            p = result.project_info
            lines.append("=== DJANGO_SETTINGS ===")
            if p.project_name:
                lines.append(f"  project: {p.project_name}")
            if p.databases:
                lines.append(f"  databases: {p.databases}")
            if p.uses_drf:
                lines.append("  DRF: enabled")
            if p.uses_celery:
                lines.append("  Celery: enabled")
            if p.uses_channels:
                lines.append("  Channels: enabled")
            if p.is_async:
                lines.append("  ASGI: enabled")
            if p.installed_apps:
                third_party = [a for a in p.installed_apps if not a.startswith('django.')]
                if third_party:
                    lines.append(f"  third_party_apps: {','.join(third_party[:15])}")
            lines.append("")

        return '\n'.join(lines)
