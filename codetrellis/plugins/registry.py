"""
CodeTrellis Plugin System - Plugin Registry
====================================

The PluginRegistry manages all registered plugins and provides
methods for plugin discovery, registration, and orchestration.

Features:
- Register language and framework plugins
- Auto-detect project frameworks
- Coordinate extraction across plugins
- Manage plugin dependencies
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
import logging

from .base import (
    ILanguagePlugin,
    IFrameworkPlugin,
    IExtractor,
    PluginMetadata,
    PluginCapability,
    PluginConfig,
    ExtractorResult,
)


logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all CodeTrellis plugins.

    The registry manages:
    - Language plugins (TypeScript, Python, etc.)
    - Framework plugins (Angular, NestJS, React, etc.)
    - Extractor instances
    - Plugin dependencies

    Usage:
        registry = PluginRegistry()
        registry.register_language_plugin(TypeScriptPlugin())
        registry.register_framework_plugin(AngularPlugin())

        # Auto-detect and scan
        plugins = registry.detect_frameworks(project_path)
        results = registry.scan_project(project_path)
    """

    def __init__(self):
        self._language_plugins: Dict[str, ILanguagePlugin] = {}
        self._framework_plugins: Dict[str, IFrameworkPlugin] = {}
        self._extractors: Dict[str, IExtractor] = {}
        self._plugin_configs: Dict[str, PluginConfig] = {}

    # =========================================================================
    # Registration
    # =========================================================================

    def register_language_plugin(self, plugin: ILanguagePlugin) -> None:
        """
        Register a language plugin.

        Args:
            plugin: The language plugin instance to register
        """
        name = plugin.metadata.name
        if name in self._language_plugins:
            logger.warning(f"Language plugin '{name}' already registered, overwriting")

        self._language_plugins[name] = plugin
        logger.info(f"Registered language plugin: {name} v{plugin.metadata.version}")

        # Register extractors from this plugin
        for extractor_cls in plugin.get_extractors():
            self._register_extractor(extractor_cls)

    def register_framework_plugin(self, plugin: IFrameworkPlugin) -> None:
        """
        Register a framework plugin.

        Args:
            plugin: The framework plugin instance to register

        Raises:
            ValueError: If required language plugin is not registered
        """
        name = plugin.metadata.name

        # Check language plugin dependency
        lang_plugin = plugin.language_plugin
        if lang_plugin and lang_plugin not in self._language_plugins:
            raise ValueError(
                f"Framework plugin '{name}' requires language plugin '{lang_plugin}' "
                f"which is not registered. Register the language plugin first."
            )

        if name in self._framework_plugins:
            logger.warning(f"Framework plugin '{name}' already registered, overwriting")

        self._framework_plugins[name] = plugin
        logger.info(f"Registered framework plugin: {name} v{plugin.metadata.version}")

        # Register extractors from this plugin
        for extractor_cls in plugin.get_extractors():
            self._register_extractor(extractor_cls)

    def _register_extractor(self, extractor_cls: Type[IExtractor]) -> None:
        """Register an extractor class"""
        try:
            extractor = extractor_cls()
            self._extractors[extractor.name] = extractor
            logger.debug(f"Registered extractor: {extractor.name}")
        except Exception as e:
            logger.error(f"Failed to instantiate extractor {extractor_cls}: {e}")

    def configure_plugin(self, plugin_name: str, config: PluginConfig) -> None:
        """
        Configure a plugin.

        Args:
            plugin_name: Name of the plugin to configure
            config: Configuration to apply
        """
        self._plugin_configs[plugin_name] = config

    # =========================================================================
    # Discovery
    # =========================================================================

    def detect_frameworks(self, project_path: Path) -> List[IFrameworkPlugin]:
        """
        Auto-detect which frameworks a project uses.

        Args:
            project_path: Path to the project root

        Returns:
            List of detected framework plugins
        """
        detected = []

        for name, plugin in self._framework_plugins.items():
            config = self._plugin_configs.get(name, PluginConfig())
            if not config.enabled:
                continue

            try:
                if plugin.detect_project(project_path):
                    detected.append(plugin)
                    logger.info(f"Detected framework: {name}")
            except Exception as e:
                logger.error(f"Error detecting framework {name}: {e}")

        return detected

    def get_plugin(self, name: str) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
        """Get a plugin by name"""
        if name in self._language_plugins:
            return self._language_plugins[name]
        if name in self._framework_plugins:
            return self._framework_plugins[name]
        return None

    def get_language_plugin(self, name: str) -> Optional[ILanguagePlugin]:
        """Get a language plugin by name"""
        return self._language_plugins.get(name)

    def get_framework_plugin(self, name: str) -> Optional[IFrameworkPlugin]:
        """Get a framework plugin by name"""
        return self._framework_plugins.get(name)

    def get_extractor(self, name: str) -> Optional[IExtractor]:
        """Get an extractor by name"""
        return self._extractors.get(name)

    def list_plugins(self) -> Dict[str, List[PluginMetadata]]:
        """
        List all registered plugins.

        Returns:
            Dictionary with 'language' and 'framework' keys
        """
        return {
            'language': [p.metadata for p in self._language_plugins.values()],
            'framework': [p.metadata for p in self._framework_plugins.values()],
        }

    def list_extractors(self) -> List[str]:
        """List all registered extractor names"""
        return list(self._extractors.keys())

    def get_extractors_by_capability(
        self,
        capability: PluginCapability
    ) -> List[IExtractor]:
        """
        Get all extractors that have a specific capability.

        Args:
            capability: The capability to filter by

        Returns:
            List of extractors with that capability
        """
        return [
            e for e in self._extractors.values()
            if capability in e.capabilities
        ]

    # =========================================================================
    # Scanning
    # =========================================================================

    def scan_project(
        self,
        project_path: Path,
        plugins: List[str] = None
    ) -> Dict[str, List[ExtractorResult]]:
        """
        Scan a project using registered plugins.

        Args:
            project_path: Path to the project root
            plugins: Optional list of plugin names to use (auto-detect if None)

        Returns:
            Dictionary mapping section names to extraction results
        """
        results: Dict[str, List[ExtractorResult]] = {}

        # Determine which plugins to use
        if plugins:
            active_plugins = [
                self._framework_plugins[name]
                for name in plugins
                if name in self._framework_plugins
            ]
        else:
            active_plugins = self.detect_frameworks(project_path)

        if not active_plugins:
            logger.warning("No framework plugins detected for project")
            return results

        # Collect all file patterns
        all_patterns = set()
        for plugin in active_plugins:
            all_patterns.update(plugin.get_file_patterns())

        # Scan files
        for pattern in all_patterns:
            for file_path in project_path.rglob(pattern):
                # Skip common exclusions
                if self._should_skip(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8')

                    # Run applicable extractors
                    for extractor in self._extractors.values():
                        if extractor.can_extract(file_path, content):
                            result = extractor.extract(file_path, content)

                            # Group by extractor name (section)
                            section = extractor.name
                            if section not in results:
                                results[section] = []
                            results[section].append(result)

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        return results

    def scan_file(
        self,
        file_path: Path,
        extractors: List[str] = None
    ) -> List[ExtractorResult]:
        """
        Scan a single file.

        Args:
            file_path: Path to the file
            extractors: Optional list of extractor names to use

        Returns:
            List of extraction results
        """
        results = []

        if not file_path.exists():
            return results

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return results

        # Determine which extractors to use
        if extractors:
            active_extractors = [
                self._extractors[name]
                for name in extractors
                if name in self._extractors
            ]
        else:
            active_extractors = list(self._extractors.values())

        for extractor in active_extractors:
            if extractor.can_extract(file_path, content):
                try:
                    result = extractor.extract(file_path, content)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in extractor {extractor.name}: {e}")

        return results

    def _should_skip(self, file_path: Path) -> bool:
        """Check if a file should be skipped"""
        skip_dirs = {'node_modules', 'dist', 'build', '.git', '__pycache__', '.venv', 'venv'}
        skip_patterns = {'.spec.ts', '.test.ts', '.spec.js', '.test.js', '_test.py', '_spec.py'}

        # Check directory exclusions
        for part in file_path.parts:
            if part in skip_dirs:
                return True

        # Check file pattern exclusions
        file_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in file_str:
                return True

        return False

    # =========================================================================
    # Output
    # =========================================================================

    def get_output_sections(self) -> List[str]:
        """
        Get all output section names from registered plugins.

        Returns:
            List of section names
        """
        sections = set()

        for plugin in self._framework_plugins.values():
            sections.update(plugin.get_output_sections())

        return sorted(sections)

    def format_results(
        self,
        results: Dict[str, List[ExtractorResult]]
    ) -> str:
        """
        Format extraction results as CodeTrellis output.

        Args:
            results: Dictionary of extraction results

        Returns:
            Formatted CodeTrellis string
        """
        lines = []

        for section, section_results in sorted(results.items()):
            if not section_results:
                continue

            lines.append(f"\n[{section.upper()}]")

            for result in section_results:
                if result.success and result.data:
                    lines.append(result.to_codetrellis_format())

        return "\n".join(lines)


# Global registry instance
_global_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)"""
    global _global_registry
    _global_registry = None
