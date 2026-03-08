"""
PostCSS Config Extractor for CodeTrellis

Extracts PostCSS configuration from various config file formats.

Supports:
- postcss.config.js / postcss.config.cjs / postcss.config.mjs
- postcss.config.ts / postcss.config.cts / postcss.config.mts
- .postcssrc / .postcssrc.js / .postcssrc.cjs / .postcssrc.json / .postcssrc.yaml
- package.json "postcss" field
- Vite / webpack / Rollup / Parcel PostCSS config integration
- Programmatic PostCSS usage (postcss([plugins]).process())

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PostCSSConfigPluginEntry:
    """A plugin entry in a PostCSS configuration."""
    name: str
    has_options: bool = False
    options_keys: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PostCSSConfigInfo:
    """Information about a PostCSS configuration file."""
    file: str = ""
    config_format: str = ""       # js, cjs, mjs, ts, json, yaml, package.json
    module_format: str = ""        # commonjs, esm
    plugin_entries: List[PostCSSConfigPluginEntry] = field(default_factory=list)
    has_env_branching: bool = False  # process.env.NODE_ENV checks
    has_source_maps: bool = False
    has_syntax_option: bool = False
    syntax_value: str = ""
    has_parser_option: bool = False
    parser_value: str = ""
    has_stringifier_option: bool = False
    stringifier_value: str = ""
    has_from_to: bool = False      # from/to file paths
    build_tool: str = ""            # vite, webpack, rollup, parcel, next, nuxt, etc.
    line_number: int = 0


class PostCSSConfigExtractor:
    """
    Extracts PostCSS configuration details.

    Detects:
    - Config file format (JS/TS/JSON/YAML/package.json)
    - Module format (CommonJS module.exports vs ESM export default)
    - Plugin list with options
    - Syntax/parser/stringifier options
    - Environment branching (dev vs prod configs)
    - Build tool integration (Vite, webpack, etc.)
    """

    # module.exports = { ... }
    CJS_EXPORT = re.compile(
        r'module\.exports\s*=',
        re.MULTILINE
    )

    # export default { ... }
    ESM_EXPORT = re.compile(
        r'export\s+default',
        re.MULTILINE
    )

    # plugins array/object
    PLUGINS_SECTION = re.compile(
        r'plugins\s*[:\s]\s*[\[{]',
        re.MULTILINE
    )

    # Environment branching
    ENV_BRANCHING = re.compile(
        r'process\.env\.NODE_ENV|ctx\.env|env\s*===?\s*["\']production["\']',
        re.MULTILINE
    )

    # Source maps
    SOURCE_MAPS = re.compile(
        r'map\s*:\s*(?:true|inline|{)',
        re.MULTILINE
    )

    # syntax option
    SYNTAX_OPTION = re.compile(
        r'syntax\s*:\s*["\']?(\S+?)["\']?\s*[,}\n]',
        re.MULTILINE
    )

    # parser option
    PARSER_OPTION = re.compile(
        r'parser\s*:\s*["\']?(\S+?)["\']?\s*[,}\n]',
        re.MULTILINE
    )

    # stringifier option
    STRINGIFIER_OPTION = re.compile(
        r'stringifier\s*:\s*["\']?(\S+?)["\']?\s*[,}\n]',
        re.MULTILINE
    )

    # from/to paths
    FROM_TO = re.compile(
        r'(?:from|to)\s*:\s*["\']',
        re.MULTILINE
    )

    # Build tool detection patterns
    BUILD_TOOL_PATTERNS = {
        'vite': re.compile(r'vite|defineConfig', re.MULTILINE | re.IGNORECASE),
        'webpack': re.compile(r'webpack|postcss-loader', re.MULTILINE | re.IGNORECASE),
        'rollup': re.compile(r'rollup|rollup-plugin-postcss', re.MULTILINE | re.IGNORECASE),
        'parcel': re.compile(r'parcel', re.MULTILINE | re.IGNORECASE),
        'next': re.compile(r'next\.config|@next/', re.MULTILINE | re.IGNORECASE),
        'nuxt': re.compile(r'nuxt\.config|@nuxt/', re.MULTILINE | re.IGNORECASE),
        'gatsby': re.compile(r'gatsby-config|gatsby-node', re.MULTILINE | re.IGNORECASE),
        'remix': re.compile(r'remix\.config', re.MULTILINE | re.IGNORECASE),
        'astro': re.compile(r'astro\.config', re.MULTILINE | re.IGNORECASE),
        'svelte': re.compile(r'svelte\.config|svelte-preprocess', re.MULTILINE | re.IGNORECASE),
    }

    # Plugin entry in config: key: value or 'plugin-name'
    PLUGIN_ENTRY_PATTERN = re.compile(
        r"""['"]([a-z@][a-z0-9_./@-]*)['"]""",
        re.MULTILINE | re.IGNORECASE
    )

    # Config file names
    CONFIG_FILE_NAMES = {
        'postcss.config.js', 'postcss.config.cjs', 'postcss.config.mjs',
        'postcss.config.ts', 'postcss.config.cts', 'postcss.config.mts',
        '.postcssrc', '.postcssrc.js', '.postcssrc.cjs', '.postcssrc.mjs',
        '.postcssrc.json', '.postcssrc.yaml', '.postcssrc.yml',
    }

    def __init__(self):
        """Initialize the config extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract PostCSS configuration details.

        Args:
            content: Config file content.
            file_path: Path to config file.

        Returns:
            Dict with 'configs' list and 'stats' dict.
        """
        configs: List[PostCSSConfigInfo] = []

        if not content or not content.strip():
            return {"configs": configs, "stats": {}}

        fname = file_path.split('/')[-1] if file_path else ''

        # Only process relevant files
        if not self._is_postcss_config_file(fname, content):
            return {"configs": configs, "stats": {}}

        config = PostCSSConfigInfo(file=file_path)

        # Detect config format
        config.config_format = self._detect_config_format(fname)

        # Detect module format
        if self.CJS_EXPORT.search(content):
            config.module_format = 'commonjs'
        elif self.ESM_EXPORT.search(content):
            config.module_format = 'esm'

        # Environment branching
        config.has_env_branching = bool(self.ENV_BRANCHING.search(content))

        # Source maps
        config.has_source_maps = bool(self.SOURCE_MAPS.search(content))

        # Syntax option
        syntax_match = self.SYNTAX_OPTION.search(content)
        if syntax_match:
            config.has_syntax_option = True
            config.syntax_value = syntax_match.group(1).strip("'\"")

        # Parser option
        parser_match = self.PARSER_OPTION.search(content)
        if parser_match:
            config.has_parser_option = True
            config.parser_value = parser_match.group(1).strip("'\"")

        # Stringifier option
        stringifier_match = self.STRINGIFIER_OPTION.search(content)
        if stringifier_match:
            config.has_stringifier_option = True
            config.stringifier_value = stringifier_match.group(1).strip("'\"")

        # from/to
        config.has_from_to = bool(self.FROM_TO.search(content))

        # Build tool
        for tool_name, pattern in self.BUILD_TOOL_PATTERNS.items():
            if pattern.search(content):
                config.build_tool = tool_name
                break

        # Extract plugin entries
        for match in self.PLUGIN_ENTRY_PATTERN.finditer(content):
            entry_name = match.group(1)
            if entry_name in ('postcss', 'plugins', 'true', 'false', 'null',
                             'undefined', 'default', 'production', 'development'):
                continue
            line_number = content[:match.start()].count('\n') + 1
            entry = PostCSSConfigPluginEntry(
                name=entry_name,
                line_number=line_number,
            )
            config.plugin_entries.append(entry)

        configs.append(config)

        stats = {
            "total_configs": len(configs),
            "config_format": config.config_format,
            "module_format": config.module_format,
            "has_env_branching": config.has_env_branching,
            "has_custom_syntax": config.has_syntax_option or config.has_parser_option,
            "build_tool": config.build_tool,
            "plugin_count": len(config.plugin_entries),
        }

        return {"configs": configs, "stats": stats}

    def _is_postcss_config_file(self, fname: str, content: str) -> bool:
        """Check if file is a PostCSS config file."""
        if fname in self.CONFIG_FILE_NAMES:
            return True
        if fname == 'package.json' and '"postcss"' in content:
            return True
        return False

    def _detect_config_format(self, fname: str) -> str:
        """Detect config format from filename."""
        if fname.endswith('.ts') or fname.endswith('.cts') or fname.endswith('.mts'):
            return 'typescript'
        if fname.endswith('.mjs'):
            return 'esm_js'
        if fname.endswith('.cjs'):
            return 'commonjs_js'
        if fname.endswith('.json'):
            return 'json'
        if fname.endswith('.yaml') or fname.endswith('.yml'):
            return 'yaml'
        if fname == 'package.json':
            return 'package_json'
        return 'javascript'
