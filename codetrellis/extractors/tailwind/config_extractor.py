"""
Tailwind CSS Config Extractor v1.0

Extracts Tailwind configuration from tailwind.config.js/ts/mjs/cjs files
and CSS-first configuration (v4).

Supports:
- tailwind.config.js / tailwind.config.ts / tailwind.config.mjs / tailwind.config.cjs
- content paths, theme overrides, plugins, presets, darkMode configuration
- v4 CSS-first config (@config, @source, @theme, @plugin directives)
- PostCSS config detection

Part of CodeTrellis v4.35 - Tailwind CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TailwindConfigInfo:
    """Information about a Tailwind configuration file."""
    config_file: str = ""
    version_detected: str = ""  # v1, v2, v3, v4
    dark_mode: str = ""  # media, class, selector, false
    prefix: str = ""
    important: str = ""  # true, selector, false
    content_paths: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    presets: List[str] = field(default_factory=list)
    theme_keys_extended: List[str] = field(default_factory=list)
    theme_keys_overridden: List[str] = field(default_factory=list)
    has_typescript: bool = False
    has_esm: bool = False
    is_v4_css_config: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindContentPathInfo:
    """Information about content path configuration."""
    path: str = ""
    is_glob: bool = False
    file_extensions: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class TailwindPluginConfigInfo:
    """Information about a Tailwind plugin in config."""
    name: str = ""
    is_official: bool = False
    has_config: bool = False
    config_options: Dict[str, Any] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


class TailwindConfigExtractor:
    """
    Extracts configuration from Tailwind config files.

    Detects:
    - Dark mode configuration (media, class, selector)
    - Content paths for JIT purging
    - Theme extensions and overrides
    - Plugin registrations
    - Prefix and important settings
    - Version detection (v1-v4 patterns)
    - TypeScript config (satisfies Config)
    - ESM config (export default)
    - v4 CSS-first config (PostCSS-native)

    Official Tailwind plugins:
    - @tailwindcss/typography
    - @tailwindcss/forms
    - @tailwindcss/aspect-ratio
    - @tailwindcss/container-queries
    - @tailwindcss/line-clamp (deprecated in v3.3)
    """

    OFFICIAL_PLUGINS = {
        '@tailwindcss/typography', '@tailwindcss/forms',
        '@tailwindcss/aspect-ratio', '@tailwindcss/container-queries',
        '@tailwindcss/line-clamp', 'tailwindcss-animate',
        '@tailwindcss/nesting', '@tailwindcss/oxide',
    }

    # darkMode detection
    DARK_MODE_PATTERN = re.compile(
        r'darkMode\s*:\s*(?:["\'](\w+)["\']|\[?\s*["\'](\w+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?\]?)',
        re.MULTILINE
    )

    # content paths
    CONTENT_PATTERN = re.compile(
        r'content\s*:\s*\[([^\]]+)\]',
        re.MULTILINE | re.DOTALL
    )

    # theme.extend keys
    THEME_EXTEND_PATTERN = re.compile(
        r'theme\s*:\s*\{[^}]*?extend\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # theme direct keys (overrides)
    THEME_OVERRIDE_PATTERN = re.compile(
        r'theme\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # plugins array
    PLUGINS_PATTERN = re.compile(
        r'plugins\s*:\s*\[([^\]]*(?:\([^)]*\)[^\]]*)*)\]',
        re.MULTILINE | re.DOTALL
    )

    # prefix
    PREFIX_PATTERN = re.compile(
        r'prefix\s*:\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    # important
    IMPORTANT_PATTERN = re.compile(
        r'important\s*:\s*(?:true|["\']([^"\']+)["\'])',
        re.MULTILINE
    )

    # presets
    PRESETS_PATTERN = re.compile(
        r'presets\s*:\s*\[([^\]]+)\]',
        re.MULTILINE | re.DOTALL
    )

    # require() or import patterns for plugins
    REQUIRE_PATTERN = re.compile(
        r'require\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    IMPORT_PATTERN = re.compile(
        r'import\s+\w+\s+from\s+["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # ESM export
    ESM_EXPORT_PATTERN = re.compile(
        r'export\s+default\s+(?:\{|defineConfig)',
        re.MULTILINE
    )

    # TypeScript satisfies
    TS_SATISFIES_PATTERN = re.compile(
        r'satisfies\s+Config',
        re.MULTILINE
    )

    # v4 CSS-first detection: @import "tailwindcss"
    V4_CSS_IMPORT_PATTERN = re.compile(
        r'@import\s+["\']tailwindcss["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Tailwind configuration from content.

        Args:
            content: Config file content (JS/TS/CSS).
            file_path: Path to the config file.

        Returns:
            Dict with extracted config info.
        """
        result: Dict[str, Any] = {
            'config': None,
            'content_paths': [],
            'plugins': [],
            'stats': {},
        }

        if not content or not content.strip():
            return result

        is_css_file = file_path.lower().endswith('.css')

        if is_css_file:
            # v4 CSS-first config
            config = self._extract_css_config(content, file_path)
        else:
            # Traditional JS/TS config
            config = self._extract_js_config(content, file_path)

        result['config'] = config
        result['content_paths'] = self._extract_content_paths(content, file_path)
        result['plugins'] = self._extract_plugins(content, file_path)

        result['stats'] = {
            'version_detected': config.version_detected if config else '',
            'has_dark_mode': bool(config and config.dark_mode),
            'has_prefix': bool(config and config.prefix),
            'plugin_count': len(result['plugins']),
            'content_path_count': len(result['content_paths']),
        }

        return result

    def _extract_js_config(self, content: str, file_path: str) -> TailwindConfigInfo:
        """Extract config from JS/TS config file."""
        config = TailwindConfigInfo(
            config_file=file_path.split('/')[-1] if file_path else '',
            file=file_path,
            line_number=1,
        )

        # Detect TypeScript
        config.has_typescript = bool(self.TS_SATISFIES_PATTERN.search(content))

        # Detect ESM
        config.has_esm = bool(self.ESM_EXPORT_PATTERN.search(content))

        # Dark mode
        dm_match = self.DARK_MODE_PATTERN.search(content)
        if dm_match:
            config.dark_mode = dm_match.group(1) or dm_match.group(2) or ''

        # Prefix
        prefix_match = self.PREFIX_PATTERN.search(content)
        if prefix_match:
            config.prefix = prefix_match.group(1)

        # Important
        imp_match = self.IMPORTANT_PATTERN.search(content)
        if imp_match:
            config.important = imp_match.group(1) or 'true'

        # Content paths
        content_match = self.CONTENT_PATTERN.search(content)
        if content_match:
            paths_str = content_match.group(1)
            paths = re.findall(r'["\']([^"\']+)["\']', paths_str)
            config.content_paths = paths

        # Theme extend keys
        extend_match = self.THEME_EXTEND_PATTERN.search(content)
        if extend_match:
            body = extend_match.group(1)
            keys = re.findall(r'(\w+)\s*:', body)
            config.theme_keys_extended = [k for k in keys if k not in ('extend',)]

        # Plugins
        plugins_match = self.PLUGINS_PATTERN.search(content)
        if plugins_match:
            plugins_str = plugins_match.group(1)
            # Extract require() calls
            for m in self.REQUIRE_PATTERN.finditer(plugins_str):
                config.plugins.append(m.group(1))
            # Extract direct references
            for m in self.IMPORT_PATTERN.finditer(content):
                pkg = m.group(1)
                if 'tailwind' in pkg.lower() or pkg in self.OFFICIAL_PLUGINS:
                    if pkg not in config.plugins:
                        config.plugins.append(pkg)

        # Presets
        presets_match = self.PRESETS_PATTERN.search(content)
        if presets_match:
            config.presets = re.findall(r'["\']([^"\']+)["\']', presets_match.group(1))

        # Version detection
        config.version_detected = self._detect_version(content, config)

        return config

    def _extract_css_config(self, content: str, file_path: str) -> TailwindConfigInfo:
        """Extract config from CSS-first config (v4)."""
        config = TailwindConfigInfo(
            config_file=file_path.split('/')[-1] if file_path else '',
            file=file_path,
            line_number=1,
            is_v4_css_config=True,
            version_detected='v4',
        )

        # @import "tailwindcss"
        if self.V4_CSS_IMPORT_PATTERN.search(content):
            config.is_v4_css_config = True

        return config

    def _extract_content_paths(self, content: str, file_path: str) -> List[TailwindContentPathInfo]:
        """Extract content path configurations."""
        results: List[TailwindContentPathInfo] = []

        content_match = self.CONTENT_PATTERN.search(content)
        if content_match:
            paths_str = content_match.group(1)
            line_num = content[:content_match.start()].count('\n') + 1
            paths = re.findall(r'["\']([^"\']+)["\']', paths_str)

            for p in paths:
                is_glob = '*' in p or '{' in p
                exts = re.findall(r'\.([\w]+)', p) if is_glob else []
                results.append(TailwindContentPathInfo(
                    path=p,
                    is_glob=is_glob,
                    file_extensions=exts,
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _extract_plugins(self, content: str, file_path: str) -> List[TailwindPluginConfigInfo]:
        """Extract plugin configurations."""
        results: List[TailwindPluginConfigInfo] = []
        seen: set = set()

        # From require() calls
        for m in self.REQUIRE_PATTERN.finditer(content):
            pkg = m.group(1)
            if pkg not in seen:
                seen.add(pkg)
                line_num = content[:m.start()].count('\n') + 1
                results.append(TailwindPluginConfigInfo(
                    name=pkg,
                    is_official=pkg in self.OFFICIAL_PLUGINS,
                    file=file_path,
                    line_number=line_num,
                ))

        # From imports
        for m in self.IMPORT_PATTERN.finditer(content):
            pkg = m.group(1)
            if pkg not in seen and ('tailwind' in pkg.lower() or pkg in self.OFFICIAL_PLUGINS):
                seen.add(pkg)
                line_num = content[:m.start()].count('\n') + 1
                results.append(TailwindPluginConfigInfo(
                    name=pkg,
                    is_official=pkg in self.OFFICIAL_PLUGINS,
                    file=file_path,
                    line_number=line_num,
                ))

        return results

    def _detect_version(self, content: str, config: TailwindConfigInfo) -> str:
        """Detect Tailwind CSS version from config patterns."""
        # v4: CSS-first config
        if config.is_v4_css_config:
            return 'v4'

        # v3: content array (replaces purge)
        if 'content:' in content or 'content :' in content:
            return 'v3'

        # v2: purge array, darkMode, JIT mode
        if 'purge:' in content or 'purge :' in content:
            if 'mode: \'jit\'' in content or "mode: 'jit'" in content:
                return 'v2-jit'
            return 'v2'

        # v1: no purge, basic config
        if 'variants:' in content or 'variants :' in content:
            return 'v1'

        return 'v3'  # Default assumption
