"""
CodeTrellis Plugin System - Plugin Discovery
=====================================

Provides plugin discovery and loading capabilities.

Features:
- Discover plugins from installed packages (entry points)
- Load plugins from local directories
- Plugin validation
- Dependency resolution

Usage:
    from codetrellis.plugins import discover_plugins, load_plugin

    # Discover all installed plugins
    plugins = discover_plugins()

    # Load a specific plugin
    plugin = load_plugin('codetrellis-plugin-react')
"""

import importlib
import importlib.metadata
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .base import (
    ILanguagePlugin,
    IFrameworkPlugin,
    PluginMetadata,
    BaseLanguagePlugin,
    BaseFrameworkPlugin,
)


logger = logging.getLogger(__name__)

# Entry point group names for plugin discovery
LANGUAGE_PLUGIN_EP = 'codetrellis.plugins.language'
FRAMEWORK_PLUGIN_EP = 'codetrellis.plugins.framework'


def discover_plugins() -> Dict[str, List[Union[ILanguagePlugin, IFrameworkPlugin]]]:
    """
    Discover all installed CodeTrellis plugins.

    Looks for plugins registered via Python entry points:
    - codetrellis.plugins.language: Language plugins
    - codetrellis.plugins.framework: Framework plugins

    Returns:
        Dictionary with 'language' and 'framework' keys containing plugin instances
    """
    result = {
        'language': [],
        'framework': [],
    }

    # Discover language plugins
    try:
        for ep in importlib.metadata.entry_points(group=LANGUAGE_PLUGIN_EP):
            try:
                plugin_cls = ep.load()
                plugin = _instantiate_plugin(plugin_cls)
                if plugin and _validate_language_plugin(plugin):
                    result['language'].append(plugin)
                    logger.info(f"Discovered language plugin: {ep.name}")
            except Exception as e:
                logger.error(f"Failed to load language plugin {ep.name}: {e}")
    except Exception as e:
        logger.debug(f"No language plugins found: {e}")

    # Discover framework plugins
    try:
        for ep in importlib.metadata.entry_points(group=FRAMEWORK_PLUGIN_EP):
            try:
                plugin_cls = ep.load()
                plugin = _instantiate_plugin(plugin_cls)
                if plugin and _validate_framework_plugin(plugin):
                    result['framework'].append(plugin)
                    logger.info(f"Discovered framework plugin: {ep.name}")
            except Exception as e:
                logger.error(f"Failed to load framework plugin {ep.name}: {e}")
    except Exception as e:
        logger.debug(f"No framework plugins found: {e}")

    return result


def load_plugin(
    name_or_path: str
) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
    """
    Load a specific plugin by name or path.

    Args:
        name_or_path: Plugin package name or path to plugin module

    Returns:
        Plugin instance or None if not found/invalid
    """
    # Check if it's a path
    if '/' in name_or_path or '\\' in name_or_path:
        return _load_plugin_from_path(Path(name_or_path))

    # Try to load as installed package
    return _load_plugin_from_package(name_or_path)


def load_builtin_plugins() -> Dict[str, List[Any]]:
    """
    Load built-in CodeTrellis plugins.

    Returns:
        Dictionary with loaded built-in plugins
    """
    from .builtin import BUILTIN_LANGUAGE_PLUGINS, BUILTIN_FRAMEWORK_PLUGINS

    return {
        'language': [p() for p in BUILTIN_LANGUAGE_PLUGINS],
        'framework': [p() for p in BUILTIN_FRAMEWORK_PLUGINS],
    }


def _load_plugin_from_package(
    package_name: str
) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
    """Load a plugin from an installed package"""
    try:
        # Standard plugin module structure
        module = importlib.import_module(f"{package_name}.plugin")

        # Look for standard plugin classes
        for attr_name in ['Plugin', 'LanguagePlugin', 'FrameworkPlugin']:
            if hasattr(module, attr_name):
                plugin_cls = getattr(module, attr_name)
                return _instantiate_plugin(plugin_cls)

        logger.error(f"No plugin class found in {package_name}")
        return None

    except ImportError as e:
        logger.error(f"Failed to import plugin {package_name}: {e}")
        return None


def _load_plugin_from_path(
    path: Path
) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
    """Load a plugin from a local path"""
    if not path.exists():
        logger.error(f"Plugin path does not exist: {path}")
        return None

    if path.is_file():
        # Load single file plugin
        return _load_plugin_from_file(path)

    if path.is_dir():
        # Look for plugin.py in directory
        plugin_file = path / 'plugin.py'
        if plugin_file.exists():
            return _load_plugin_from_file(plugin_file)

        # Look for __init__.py
        init_file = path / '__init__.py'
        if init_file.exists():
            return _load_plugin_from_file(init_file)

    logger.error(f"Could not find plugin at {path}")
    return None


def _load_plugin_from_file(
    file_path: Path
) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
    """Load a plugin from a Python file"""
    import sys
    import importlib.util

    try:
        # Create a unique module name
        module_name = f"codetrellis_plugin_{file_path.stem}_{id(file_path)}"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Look for plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type):
                if issubclass(attr, (BaseLanguagePlugin, BaseFrameworkPlugin)):
                    if attr not in (BaseLanguagePlugin, BaseFrameworkPlugin):
                        return _instantiate_plugin(attr)

        return None

    except Exception as e:
        logger.error(f"Failed to load plugin from {file_path}: {e}")
        return None


def _instantiate_plugin(
    plugin_cls: Type
) -> Optional[Union[ILanguagePlugin, IFrameworkPlugin]]:
    """Safely instantiate a plugin class"""
    try:
        return plugin_cls()
    except Exception as e:
        logger.error(f"Failed to instantiate plugin {plugin_cls}: {e}")
        return None


def _validate_language_plugin(plugin: Any) -> bool:
    """Validate that a plugin implements ILanguagePlugin correctly"""
    required_attrs = ['metadata', 'file_extensions', 'can_parse', 'parse', 'get_extractors']

    for attr in required_attrs:
        if not hasattr(plugin, attr):
            logger.error(f"Language plugin missing required attribute: {attr}")
            return False

    # Validate metadata
    if not isinstance(plugin.metadata, PluginMetadata):
        logger.error("Language plugin metadata is not a PluginMetadata instance")
        return False

    return True


def _validate_framework_plugin(plugin: Any) -> bool:
    """Validate that a plugin implements IFrameworkPlugin correctly"""
    required_attrs = [
        'metadata', 'language_plugin', 'detect_project',
        'get_file_patterns', 'get_extractors', 'get_output_sections'
    ]

    for attr in required_attrs:
        if not hasattr(plugin, attr):
            logger.error(f"Framework plugin missing required attribute: {attr}")
            return False

    # Validate metadata
    if not isinstance(plugin.metadata, PluginMetadata):
        logger.error("Framework plugin metadata is not a PluginMetadata instance")
        return False

    return True


def get_plugin_info(plugin: Union[ILanguagePlugin, IFrameworkPlugin]) -> Dict[str, Any]:
    """
    Get detailed information about a plugin.

    Args:
        plugin: The plugin instance

    Returns:
        Dictionary with plugin information
    """
    info = plugin.metadata.to_dict()

    if hasattr(plugin, 'get_extractors'):
        extractors = plugin.get_extractors()
        info['extractors'] = [
            e().name if callable(e) else e.name
            for e in extractors
        ]

    if hasattr(plugin, 'get_file_patterns'):
        info['file_patterns'] = plugin.get_file_patterns()

    if hasattr(plugin, 'get_output_sections'):
        info['output_sections'] = plugin.get_output_sections()

    return info
