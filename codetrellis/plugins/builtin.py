"""
CodeTrellis Built-in Plugins
=====================

Contains built-in plugins for common languages and frameworks.

Built-in Language Plugins:
- TypeScriptPlugin: TypeScript/JavaScript support

Built-in Framework Plugins:
- AngularPlugin: Angular 17+ support
- NestJSPlugin: NestJS backend support (planned)
"""

from pathlib import Path
from typing import List, Type
import json

from .base import (
    BaseLanguagePlugin,
    BaseFrameworkPlugin,
    IExtractor,
    PluginMetadata,
    PluginCapability,
    PluginType,
)


# =============================================================================
# TypeScript Language Plugin
# =============================================================================

class TypeScriptPlugin(BaseLanguagePlugin):
    """
    Built-in TypeScript/JavaScript language plugin.

    Provides basic TypeScript parsing and extraction capabilities.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name='typescript',
            version='1.0.0',
            description='TypeScript/JavaScript language support',
            author='CodeTrellis Team',
            plugin_type=PluginType.LANGUAGE,
            capabilities=[
                PluginCapability.INTERFACES,
                PluginCapability.TYPES,
                PluginCapability.CLASSES,
                PluginCapability.FUNCTIONS,
                PluginCapability.ENUMS,
            ],
            file_extensions=['.ts', '.tsx', '.js', '.jsx'],
        )

    @property
    def file_extensions(self) -> List[str]:
        return ['.ts', '.tsx', '.js', '.jsx']

    def parse(self, file_path: Path, content: str) -> dict:
        """Parse TypeScript file (basic parsing, not full AST)"""
        return {
            'file_path': str(file_path),
            'content': content,
            'size': len(content),
            'lines': content.count('\n') + 1,
        }

    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get TypeScript extractors"""
        # These are imported dynamically to avoid circular imports
        return []


# =============================================================================
# Angular Framework Plugin
# =============================================================================

class AngularPlugin(BaseFrameworkPlugin):
    """
    Built-in Angular framework plugin.

    Supports Angular 17+ with:
    - Standalone components
    - Signals and computed
    - NgRx SignalStore
    - Angular routes
    - HttpClient API calls
    - Socket.IO WebSocket patterns
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name='angular',
            version='1.0.0',
            description='Angular 17+ framework support',
            author='CodeTrellis Team',
            plugin_type=PluginType.FRAMEWORK,
            capabilities=[
                PluginCapability.COMPONENTS,
                PluginCapability.SERVICES,
                PluginCapability.STORES,
                PluginCapability.ROUTES,
                PluginCapability.HTTP_API,
                PluginCapability.WEBSOCKET,
                PluginCapability.INTERFACES,
                PluginCapability.TYPES,
            ],
            dependencies=['typescript'],
            file_extensions=['.ts', '.html'],
            config_files=['angular.json', 'angular-cli.json'],
        )

    @property
    def language_plugin(self) -> str:
        return 'typescript'

    def detect_project(self, project_path: Path) -> bool:
        """Detect if project is an Angular project"""
        # Check for angular.json
        if (project_path / 'angular.json').exists():
            return True

        # Check for @angular/core in package.json
        return self._check_package_json_dependency(project_path, '@angular/core')

    def get_file_patterns(self) -> List[str]:
        """Get glob patterns for Angular files"""
        return [
            '*.component.ts',
            '*.service.ts',
            '*.store.ts',
            '*.routes.ts',
            'app.routes.ts',
            '*.module.ts',
            '*.directive.ts',
            '*.pipe.ts',
            '*.guard.ts',
            '*.resolver.ts',
            '*.interceptor.ts',
            '*.model.ts',
            '*.interface.ts',
            '*.types.ts',
        ]

    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get Angular-specific extractors"""
        # These would be the actual extractor classes
        # Returning empty list - extractors are managed by scanner.py
        return []

    def get_output_sections(self) -> List[str]:
        """Get output section names"""
        return [
            'COMPONENTS',
            'ANGULAR_SERVICES',
            'STORES',
            'ROUTES',
            'HTTP_API',
            'WEBSOCKET_EVENTS',
            'INTERFACES',
            'TYPES',
        ]

    def get_angular_version(self, project_path: Path) -> str:
        """Get Angular version from package.json"""
        package_json = project_path / 'package.json'
        if not package_json.exists():
            return 'unknown'

        try:
            data = json.loads(package_json.read_text())
            deps = data.get('dependencies', {})
            version = deps.get('@angular/core', 'unknown')
            # Clean up version string (remove ^ or ~)
            return version.lstrip('^~')
        except Exception:
            return 'unknown'


# =============================================================================
# NestJS Framework Plugin (Skeleton)
# =============================================================================

class NestJSPlugin(BaseFrameworkPlugin):
    """
    Built-in NestJS framework plugin.

    Supports NestJS with:
    - Controllers with decorators
    - Services with @Injectable
    - Modules
    - DTOs with class-validator
    - Schemas (Mongoose)
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name='nestjs',
            version='0.1.0',  # Not fully implemented yet
            description='NestJS backend framework support',
            author='CodeTrellis Team',
            plugin_type=PluginType.FRAMEWORK,
            capabilities=[
                PluginCapability.CLASSES,
                PluginCapability.SERVICES,
                PluginCapability.MODULES,
                PluginCapability.HTTP_API,
                PluginCapability.WEBSOCKET,
                PluginCapability.INTERFACES,
            ],
            dependencies=['typescript'],
            file_extensions=['.ts'],
            config_files=['nest-cli.json'],
        )

    @property
    def language_plugin(self) -> str:
        return 'typescript'

    def detect_project(self, project_path: Path) -> bool:
        """Detect if project is a NestJS project"""
        # Check for nest-cli.json
        if (project_path / 'nest-cli.json').exists():
            return True

        # Check for @nestjs/core in package.json
        return self._check_package_json_dependency(project_path, '@nestjs/core')

    def get_file_patterns(self) -> List[str]:
        """Get glob patterns for NestJS files"""
        return [
            '*.controller.ts',
            '*.service.ts',
            '*.module.ts',
            '*.dto.ts',
            '*.schema.ts',
            '*.entity.ts',
            '*.gateway.ts',
            '*.guard.ts',
            '*.interceptor.ts',
            '*.pipe.ts',
            '*.filter.ts',
        ]

    def get_extractors(self) -> List[Type[IExtractor]]:
        """Get NestJS-specific extractors"""
        return []

    def get_output_sections(self) -> List[str]:
        """Get output section names"""
        return [
            'SCHEMAS',
            'DTOS',
            'CONTROLLERS',
            'SERVICES',
            'MODULES',
            'GATEWAYS',
        ]


# =============================================================================
# Plugin Lists
# =============================================================================

# List of built-in language plugin classes
BUILTIN_LANGUAGE_PLUGINS: List[Type[BaseLanguagePlugin]] = [
    TypeScriptPlugin,
]

# List of built-in framework plugin classes
BUILTIN_FRAMEWORK_PLUGINS: List[Type[BaseFrameworkPlugin]] = [
    AngularPlugin,
    NestJSPlugin,
]
