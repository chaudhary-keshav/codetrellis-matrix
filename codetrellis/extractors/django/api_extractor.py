"""
Django API & Integration Extractor for CodeTrellis.

Detects Django ecosystem: version, installed apps, settings patterns,
third-party integrations (DRF, Celery, Channels, etc.), and project structure.
Supports Django 1.x - 5.x.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoProjectInfo:
    """High-level Django project information."""
    django_version: Optional[str] = None
    drf_version: Optional[str] = None
    project_name: Optional[str] = None
    installed_apps: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    databases: Dict[str, str] = field(default_factory=dict)  # alias -> engine
    auth_backends: List[str] = field(default_factory=list)
    template_engines: List[str] = field(default_factory=list)
    cache_backends: Dict[str, str] = field(default_factory=dict)
    static_url: Optional[str] = None
    media_url: Optional[str] = None
    rest_framework_config: Dict[str, Any] = field(default_factory=dict)
    celery_config: Dict[str, Any] = field(default_factory=dict)
    channels_config: Dict[str, Any] = field(default_factory=dict)
    is_async: bool = False
    uses_drf: bool = False
    uses_celery: bool = False
    uses_channels: bool = False
    uses_graphene: bool = False
    uses_allauth: bool = False
    uses_cors: bool = False
    file: str = ""


# Django ecosystem detection patterns
DJANGO_ECOSYSTEM = {
    'rest_framework': 'DRF',
    'django_filters': 'DRF Filters',
    'corsheaders': 'CORS',
    'allauth': 'AllAuth',
    'celery': 'Celery',
    'channels': 'Channels',
    'graphene_django': 'Graphene',
    'django_extensions': 'Extensions',
    'debug_toolbar': 'Debug Toolbar',
    'storages': 'Storages',
    'import_export': 'Import/Export',
    'mptt': 'MPTT',
    'taggit': 'Taggit',
    'guardian': 'Guardian',
    'simple_history': 'Simple History',
    'oauth2_provider': 'OAuth2',
    'drf_yasg': 'DRF YASG (Swagger)',
    'drf_spectacular': 'DRF Spectacular',
    'silk': 'Silk Profiler',
    'whitenoise': 'WhiteNoise',
    'django_celery_beat': 'Celery Beat',
    'django_celery_results': 'Celery Results',
    'django_redis': 'Redis',
    'cacheops': 'Cacheops',
    'polymorphic': 'Polymorphic',
}


class DjangoAPIExtractor:
    """
    Extracts Django project configuration and integrations.

    Handles:
    - settings.py analysis (INSTALLED_APPS, DATABASES, MIDDLEWARE, etc.)
    - Django version detection from imports and requirements
    - DRF configuration (REST_FRAMEWORK dict)
    - Celery configuration (CELERY_* or app.config)
    - Channels configuration (ASGI_APPLICATION, CHANNEL_LAYERS)
    - Third-party app detection
    - Project structure detection (urls.py, wsgi.py, asgi.py)
    """

    # INSTALLED_APPS pattern
    INSTALLED_APPS_PATTERN = re.compile(
        r'INSTALLED_APPS\s*=\s*[\[\(](.*?)[\]\)]',
        re.DOTALL
    )

    # DATABASES pattern
    DATABASES_PATTERN = re.compile(
        r"DATABASES\s*=\s*\{.*?['\"]default['\"]\s*:\s*\{.*?['\"]ENGINE['\"]\s*:\s*['\"]([^'\"]+)['\"]",
        re.DOTALL
    )

    # REST_FRAMEWORK config
    REST_FRAMEWORK_PATTERN = re.compile(
        r'REST_FRAMEWORK\s*=\s*\{(.*?)\}',
        re.DOTALL
    )

    # Django version from import
    DJANGO_VERSION_IMPORT_PATTERN = re.compile(
        r'django[>=<~!]+(\d+\.\d+(?:\.\d+)?)',
    )

    # ASGI/WSGI detection
    ASGI_PATTERN = re.compile(
        r'ASGI_APPLICATION\s*=\s*["\']([^"\']+)["\']'
    )

    # ROOT_URLCONF
    ROOT_URLCONF_PATTERN = re.compile(
        r'ROOT_URLCONF\s*=\s*["\']([^"\']+)["\']'
    )

    # Celery config
    CELERY_BROKER_PATTERN = re.compile(
        r'(?:CELERY_)?BROKER_URL\s*=\s*["\']([^"\']+)["\']'
    )

    # Channel layers
    CHANNEL_LAYERS_PATTERN = re.compile(
        r'CHANNEL_LAYERS\s*=\s*\{',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the Django API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django project configuration.

        Returns:
            Dict with 'project_info'
        """
        info = DjangoProjectInfo(file=file_path)

        # Extract INSTALLED_APPS
        apps_match = self.INSTALLED_APPS_PATTERN.search(content)
        if apps_match:
            apps_str = apps_match.group(1)
            info.installed_apps = re.findall(r"['\"]([^'\"]+)['\"]", apps_str)

            # Detect ecosystem from installed apps
            for app in info.installed_apps:
                app_base = app.split('.')[0]
                if app_base == 'rest_framework':
                    info.uses_drf = True
                elif app_base in ('django_celery_beat', 'django_celery_results'):
                    info.uses_celery = True
                elif app_base == 'channels':
                    info.uses_channels = True
                elif app_base == 'graphene_django':
                    info.uses_graphene = True
                elif app_base == 'allauth':
                    info.uses_allauth = True
                elif app_base == 'corsheaders':
                    info.uses_cors = True

        # Extract DATABASES
        db_match = self.DATABASES_PATTERN.search(content)
        if db_match:
            engine = db_match.group(1)
            info.databases['default'] = engine.split('.')[-1]

        # Extract REST_FRAMEWORK config
        rf_match = self.REST_FRAMEWORK_PATTERN.search(content)
        if rf_match:
            info.uses_drf = True
            rf_body = rf_match.group(1)
            # Extract key settings
            for key_match in re.finditer(r"['\"]([^'\"]+)['\"]\s*:", rf_body):
                key = key_match.group(1)
                info.rest_framework_config[key] = True

        # Detect ASGI (async)
        if self.ASGI_PATTERN.search(content):
            info.is_async = True

        # Detect ROOT_URLCONF / project name
        urlconf_match = self.ROOT_URLCONF_PATTERN.search(content)
        if urlconf_match:
            info.project_name = urlconf_match.group(1).split('.')[0]

        # Detect Celery
        if self.CELERY_BROKER_PATTERN.search(content):
            info.uses_celery = True

        # Detect Channels
        if self.CHANNEL_LAYERS_PATTERN.search(content):
            info.uses_channels = True

        return {'project_info': info}

    def extract_from_requirements(self, content: str) -> Dict[str, Optional[str]]:
        """
        Extract version info from requirements.txt or pyproject.toml.

        Returns:
            Dict with 'django_version', 'drf_version'
        """
        result = {
            'django_version': None,
            'drf_version': None,
        }

        # Django version
        django_match = re.search(r'[Dd]jango[>=<~!]+(\d+\.\d+(?:\.\d+)?)', content)
        if django_match:
            result['django_version'] = django_match.group(1)

        # DRF version
        drf_match = re.search(r'djangorestframework[>=<~!]+(\d+\.\d+(?:\.\d+)?)', content)
        if drf_match:
            result['drf_version'] = drf_match.group(1)

        return result
