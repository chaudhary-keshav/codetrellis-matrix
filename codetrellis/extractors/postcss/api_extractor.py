"""
PostCSS API Extractor for CodeTrellis

Extracts PostCSS JavaScript API usage patterns.

Supports:
- postcss() processor creation
- postcss.plugin() registration (v1-v7 legacy API)
- Plugin class pattern (v8+ modern API)
- AST node creation: postcss.decl(), postcss.rule(), postcss.atRule(), postcss.comment(), postcss.root()
- Walker methods: walkRules, walkDecls, walkAtRules, walkComments, walk
- Container API: append, prepend, insertBefore, insertAfter, removeChild, replaceWith
- Result API: result.css, result.map, result.messages, result.warnings()
- LazyResult / .process() / .then() / async/await usage
- Source map handling: inline, prev, annotation
- Input API: postcss.parse(), input.css, input.from

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PostCSSApiUsage:
    """Information about a PostCSS JavaScript API usage."""
    api_name: str                   # API name
    api_category: str = ""          # processor, plugin, node, walker, container, result, parse
    pattern: str = ""               # Usage pattern description
    is_legacy: bool = False         # Uses deprecated/legacy API
    postcss_version: str = ""       # Version indicator
    file: str = ""
    line_number: int = 0


class PostCSSApiExtractor:
    """
    Extracts PostCSS JavaScript API usage.

    Detects:
    - Processor creation: postcss([plugins]).process()
    - Plugin definition: postcss.plugin() (v7-) or class-based (v8+)
    - AST creation: postcss.decl(), postcss.rule(), etc.
    - AST traversal: walkRules(), walkDecls(), etc.
    - Container manipulation: append(), prepend(), insertBefore(), etc.
    - Result handling: result.css, result.map, result.warnings()
    - Parsing: postcss.parse(), postcss.stringify()
    """

    # Core processor
    PROCESSOR_PATTERN = re.compile(
        r'postcss\s*\(', re.MULTILINE
    )

    # Legacy plugin API (v7 and earlier)
    LEGACY_PLUGIN_PATTERN = re.compile(
        r'postcss\.plugin\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Modern plugin (v8+ class/object pattern)
    MODERN_PLUGIN_PATTERN = re.compile(
        r"""(?:module\.exports\s*=|export\s+(?:default|const\s+\w+\s*=))\s*\(\s*(?:opts|options)?\s*(?:=\s*\{[^}]*\})?\s*\)\s*=>\s*\{?\s*return\s*\{?\s*postcssPlugin\s*:\s*["\']([^"\']+)["\']""",
        re.MULTILINE | re.DOTALL
    )

    # postcssPlugin property (v8 plugin identifier)
    POSTCSS_PLUGIN_PROP = re.compile(
        r'postcssPlugin\s*:\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # .process() call
    PROCESS_PATTERN = re.compile(
        r'\.process\s*\(\s*(?:css|source|input|content|code|src)',
        re.MULTILINE
    )

    # AST node creation
    NODE_CREATION_PATTERNS = {
        'decl': re.compile(r'postcss\.decl\s*\(', re.MULTILINE),
        'rule': re.compile(r'postcss\.rule\s*\(', re.MULTILINE),
        'atRule': re.compile(r'postcss\.atRule\s*\(', re.MULTILINE),
        'comment': re.compile(r'postcss\.comment\s*\(', re.MULTILINE),
        'root': re.compile(r'postcss\.root\s*\(', re.MULTILINE),
        'document': re.compile(r'postcss\.document\s*\(', re.MULTILINE),
    }

    # Walker methods
    WALKER_PATTERNS = {
        'walk': re.compile(r'\.walk\s*\(\s*(?:node|n)\s*=>', re.MULTILINE),
        'walkRules': re.compile(r'\.walkRules\s*\(', re.MULTILINE),
        'walkDecls': re.compile(r'\.walkDecls\s*\(', re.MULTILINE),
        'walkAtRules': re.compile(r'\.walkAtRules\s*\(', re.MULTILINE),
        'walkComments': re.compile(r'\.walkComments\s*\(', re.MULTILINE),
    }

    # Container manipulation
    CONTAINER_PATTERNS = {
        'append': re.compile(r'\.append\s*\(\s*(?:postcss\.)', re.MULTILINE),
        'prepend': re.compile(r'\.prepend\s*\(\s*(?:postcss\.)', re.MULTILINE),
        'insertBefore': re.compile(r'\.insertBefore\s*\(', re.MULTILINE),
        'insertAfter': re.compile(r'\.insertAfter\s*\(', re.MULTILINE),
        'removeChild': re.compile(r'\.removeChild\s*\(', re.MULTILINE),
        'replaceWith': re.compile(r'\.replaceWith\s*\(', re.MULTILINE),
        'remove': re.compile(r'(?:node|decl|rule|atrule)\.remove\s*\(', re.MULTILINE),
        'clone': re.compile(r'\.clone\s*\(\s*(?:\{|$)', re.MULTILINE),
        'cloneBefore': re.compile(r'\.cloneBefore\s*\(', re.MULTILINE),
        'cloneAfter': re.compile(r'\.cloneAfter\s*\(', re.MULTILINE),
    }

    # Result API
    RESULT_PATTERNS = {
        'result.css': re.compile(r'result\.css\b', re.MULTILINE),
        'result.map': re.compile(r'result\.map\b', re.MULTILINE),
        'result.messages': re.compile(r'result\.messages\b', re.MULTILINE),
        'result.warnings': re.compile(r'result\.warnings\s*\(', re.MULTILINE),
        'result.root': re.compile(r'result\.root\b', re.MULTILINE),
    }

    # Parse API
    PARSE_PATTERN = re.compile(r'postcss\.parse\s*\(', re.MULTILINE)
    STRINGIFY_PATTERN = re.compile(r'postcss\.stringify\s*\(', re.MULTILINE)

    # Async patterns
    ASYNC_PATTERN = re.compile(
        r'(?:await\s+(?:\w+\.)?process|\.process\s*\([^)]*\)\s*\.then)',
        re.MULTILINE
    )

    # Source map options
    SOURCEMAP_PATTERN = re.compile(
        r'(?:map|sourceMap)\s*:\s*(?:\{[^}]*\}|true|false|["\']inline["\'])',
        re.MULTILINE
    )

    # Once/OnceExit (v8 plugin hooks)
    PLUGIN_HOOKS = {
        'Once': re.compile(r'\bOnce\s*\(', re.MULTILINE),
        'OnceExit': re.compile(r'\bOnceExit\s*\(', re.MULTILINE),
        'Root': re.compile(r'\bRoot\s*\(', re.MULTILINE),
        'RootExit': re.compile(r'\bRootExit\s*\(', re.MULTILINE),
        'Rule': re.compile(r'\bRule\s*\(\s*(?:rule|node)', re.MULTILINE),
        'RuleExit': re.compile(r'\bRuleExit\s*\(', re.MULTILINE),
        'Declaration': re.compile(r'\bDeclaration\s*\(\s*(?:decl|node)', re.MULTILINE),
        'DeclarationExit': re.compile(r'\bDeclarationExit\s*\(', re.MULTILINE),
        'AtRule': re.compile(r'\bAtRule\s*\(\s*(?:atRule|node)', re.MULTILINE),
        'AtRuleExit': re.compile(r'\bAtRuleExit\s*\(', re.MULTILINE),
        'Comment': re.compile(r'\bComment\s*\(\s*(?:comment|node)', re.MULTILINE),
        'CommentExit': re.compile(r'\bCommentExit\s*\(', re.MULTILINE),
    }

    def __init__(self):
        """Initialize the API extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract PostCSS JavaScript API usage.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dict with 'api_usages' list and 'stats' dict.
        """
        usages: List[PostCSSApiUsage] = []

        if not content or not content.strip():
            return {"api_usages": usages, "stats": {}}

        # Processor creation
        for match in self.PROCESSOR_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='postcss()',
                api_category='processor',
                pattern='Processor creation',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Legacy plugin API
        for match in self.LEGACY_PLUGIN_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name=f'postcss.plugin("{match.group(1)}")',
                api_category='plugin',
                pattern='Legacy plugin definition (v7-)',
                is_legacy=True,
                postcss_version='<=7',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Modern plugin (postcssPlugin property)
        for match in self.POSTCSS_PLUGIN_PROP.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name=f'postcssPlugin: "{match.group(1)}"',
                api_category='plugin',
                pattern='Modern plugin definition (v8+)',
                postcss_version='>=8',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # .process() call
        for match in self.PROCESS_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='.process()',
                api_category='processor',
                pattern='CSS processing',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Node creation
        for name, pattern in self.NODE_CREATION_PATTERNS.items():
            for match in pattern.finditer(content):
                usages.append(PostCSSApiUsage(
                    api_name=f'postcss.{name}()',
                    api_category='node',
                    pattern=f'AST node creation: {name}',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Walker methods
        for name, pattern in self.WALKER_PATTERNS.items():
            for match in pattern.finditer(content):
                usages.append(PostCSSApiUsage(
                    api_name=f'.{name}()',
                    api_category='walker',
                    pattern=f'AST traversal: {name}',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Container manipulation
        for name, pattern in self.CONTAINER_PATTERNS.items():
            for match in pattern.finditer(content):
                usages.append(PostCSSApiUsage(
                    api_name=f'.{name}()',
                    api_category='container',
                    pattern=f'AST manipulation: {name}',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Result API
        for name, pattern in self.RESULT_PATTERNS.items():
            for match in pattern.finditer(content):
                usages.append(PostCSSApiUsage(
                    api_name=name,
                    api_category='result',
                    pattern=f'Result access: {name}',
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Parse/stringify
        for match in self.PARSE_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='postcss.parse()',
                api_category='parse',
                pattern='CSS parsing',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))
        for match in self.STRINGIFY_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='postcss.stringify()',
                api_category='parse',
                pattern='CSS stringification',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Async
        for match in self.ASYNC_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='async process()',
                api_category='processor',
                pattern='Async CSS processing',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Source maps
        for match in self.SOURCEMAP_PATTERN.finditer(content):
            usages.append(PostCSSApiUsage(
                api_name='source map config',
                api_category='processor',
                pattern='Source map configuration',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Plugin hooks (v8)
        detected_hooks: set = set()
        for name, pattern in self.PLUGIN_HOOKS.items():
            for match in pattern.finditer(content):
                if name not in detected_hooks:
                    detected_hooks.add(name)
                    usages.append(PostCSSApiUsage(
                        api_name=f'{name}()',
                        api_category='plugin',
                        pattern=f'v8 plugin hook: {name}',
                        postcss_version='>=8',
                        file=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                    ))

        # Determine version indicators
        has_legacy_plugin = any(u.is_legacy for u in usages)
        has_v8_hooks = bool(detected_hooks)
        has_postcss_plugin_prop = any('postcssPlugin' in u.api_name for u in usages)

        stats = {
            "total_api_usages": len(usages),
            "categories": list(set(u.api_category for u in usages if u.api_category)),
            "has_processor": any(u.api_category == 'processor' for u in usages),
            "has_plugin_def": any(u.api_category == 'plugin' for u in usages),
            "has_ast_creation": any(u.api_category == 'node' for u in usages),
            "has_walkers": any(u.api_category == 'walker' for u in usages),
            "has_container_api": any(u.api_category == 'container' for u in usages),
            "has_result_api": any(u.api_category == 'result' for u in usages),
            "has_parse_api": any(u.api_category == 'parse' for u in usages),
            "has_legacy_plugin": has_legacy_plugin,
            "has_v8_hooks": has_v8_hooks,
            "has_v8_plugin": has_postcss_plugin_prop,
            "has_async": any(u.pattern == 'Async CSS processing' for u in usages),
            "has_source_maps": any(u.pattern == 'Source map configuration' for u in usages),
            "detected_hooks": sorted(detected_hooks),
            "inferred_version": (
                ">=8" if has_v8_hooks or has_postcss_plugin_prop
                else "<=7" if has_legacy_plugin
                else "unknown"
            ),
        }

        return {"api_usages": usages, "stats": stats}
