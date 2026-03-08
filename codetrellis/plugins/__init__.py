"""
CodeTrellis Plugin System - Base Module
================================

This module defines the plugin architecture for CodeTrellis v3.0.

The plugin system allows CodeTrellis to support multiple frameworks and languages
through a standardized interface. Each plugin provides:

1. File pattern detection (what files to scan)
2. Framework detection (is this project using the framework?)
3. Extractors (specialized extraction logic)
4. Output formatters (framework-specific output sections)

Architecture:
    PluginRegistry
        └── IFrameworkPlugin (interface)
                ├── AngularPlugin (built-in)
                ├── NestJSPlugin (built-in)
                ├── ReactPlugin (community)
                └── ... (extensible)

Usage:
    from codetrellis.plugins import PluginRegistry, AngularPlugin

    registry = PluginRegistry()
    registry.register(AngularPlugin())

    # Auto-detect and scan
    results = registry.scan_project(project_path)
"""

from .base import (
    ILanguagePlugin,
    IFrameworkPlugin,
    IExtractor,
    PluginMetadata,
    ExtractorResult,
    PluginCapability,
)
from .registry import PluginRegistry
from .discovery import discover_plugins, load_plugin, load_builtin_plugins

__all__ = [
    # Interfaces
    'ILanguagePlugin',
    'IFrameworkPlugin',
    'IExtractor',
    # Data classes
    'PluginMetadata',
    'ExtractorResult',
    'PluginCapability',
    # Registry
    'PluginRegistry',
    # Discovery
    'discover_plugins',
    'load_plugin',
    'load_builtin_plugins',
]
