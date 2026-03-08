"""
PostCSS Syntax Extractor for CodeTrellis

Extracts custom syntax/parser/stringifier usage in PostCSS pipelines.

Supports:
- postcss-scss — Parse SCSS without compiling
- postcss-less — Parse Less without compiling
- postcss-html — Parse CSS in HTML/Vue/Svelte/PHP files
- postcss-markdown — Parse CSS in Markdown files
- postcss-jsx — Parse CSS-in-JS (styled-components, emotion)
- postcss-styled-syntax — Parse tagged template literals
- postcss-syntax — Auto-detect syntax
- sugarss — Indent-based CSS syntax (like Stylus/Sass)
- postcss-safe-parser — Fault-tolerant CSS parser
- postcss-comment — Enable // inline comments

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PostCSSSyntaxInfo:
    """Information about a PostCSS custom syntax."""
    name: str                       # Syntax name
    package_name: str = ""          # npm package name
    syntax_type: str = ""           # parser, stringifier, syntax (combined)
    languages: List[str] = field(default_factory=list)  # Languages it handles
    file: str = ""
    line_number: int = 0


# Known syntaxes/parsers
KNOWN_SYNTAXES: Dict[str, Dict[str, Any]] = {
    'postcss-scss': {
        'type': 'syntax',
        'languages': ['scss'],
        'desc': 'SCSS syntax (no compilation)',
    },
    'postcss-less': {
        'type': 'syntax',
        'languages': ['less'],
        'desc': 'Less syntax (no compilation)',
    },
    'postcss-html': {
        'type': 'syntax',
        'languages': ['html', 'vue', 'svelte', 'php'],
        'desc': 'HTML embedded CSS',
    },
    'postcss-markdown': {
        'type': 'syntax',
        'languages': ['markdown'],
        'desc': 'Markdown embedded CSS',
    },
    'postcss-jsx': {
        'type': 'syntax',
        'languages': ['jsx', 'tsx'],
        'desc': 'CSS-in-JS parsing',
    },
    'postcss-styled-syntax': {
        'type': 'syntax',
        'languages': ['jsx', 'tsx', 'js', 'ts'],
        'desc': 'Tagged template literal CSS',
    },
    'postcss-syntax': {
        'type': 'syntax',
        'languages': ['auto'],
        'desc': 'Auto-detect syntax',
    },
    'sugarss': {
        'type': 'syntax',
        'languages': ['sss'],
        'desc': 'Indent-based CSS syntax',
    },
    'postcss-safe-parser': {
        'type': 'parser',
        'languages': ['css'],
        'desc': 'Fault-tolerant CSS parser',
    },
    'postcss-comment': {
        'type': 'parser',
        'languages': ['css'],
        'desc': 'Inline // comments',
    },
    'postcss-strip-inline-comments': {
        'type': 'parser',
        'languages': ['css'],
        'desc': 'Strip // comments',
    },
    'postcss-styl': {
        'type': 'syntax',
        'languages': ['stylus'],
        'desc': 'Stylus syntax',
    },
    'midas': {
        'type': 'stringifier',
        'languages': ['css'],
        'desc': 'Syntax-highlighted CSS output',
    },
}


class PostCSSSyntaxExtractor:
    """
    Extracts PostCSS custom syntax usage.

    Detects:
    - syntax: option in PostCSS config
    - parser: option in PostCSS config
    - stringifier: option in PostCSS config
    - require/import of known syntax packages
    - .sss file extensions (SugarSS)
    """

    # syntax/parser/stringifier option in config
    SYNTAX_OPTION_PATTERN = re.compile(
        r'(?:syntax|parser|stringifier)\s*:\s*(?:require\s*\(\s*)?["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Import/require of known syntax
    IMPORT_SYNTAX_PATTERN = re.compile(
        r"""(?:require|import)\s*[\s(]['"]([^'"]*(?:postcss-(?:scss|less|html|markdown|jsx|styled-syntax|syntax|safe-parser|comment|strip-inline-comments|styl)|sugarss|midas))['"]\s*\)?""",
        re.MULTILINE
    )

    # SugarSS file detection
    SSS_FILE_PATTERN = re.compile(r'\.sss$', re.IGNORECASE)

    def __init__(self):
        """Initialize the syntax extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract PostCSS custom syntax information.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dict with 'syntaxes' list and 'stats' dict.
        """
        syntaxes: List[PostCSSSyntaxInfo] = []
        seen_names: set = set()

        if not content or not content.strip():
            return {"syntaxes": syntaxes, "stats": {}}

        # Extract from config syntax/parser/stringifier options
        for match in self.SYNTAX_OPTION_PATTERN.finditer(content):
            pkg_name = match.group(1)
            if pkg_name not in seen_names:
                seen_names.add(pkg_name)
                known = KNOWN_SYNTAXES.get(pkg_name, {})
                syntaxes.append(PostCSSSyntaxInfo(
                    name=known.get('desc', pkg_name),
                    package_name=pkg_name,
                    syntax_type=known.get('type', 'syntax'),
                    languages=known.get('languages', []),
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract from import/require
        for match in self.IMPORT_SYNTAX_PATTERN.finditer(content):
            pkg_name = match.group(1)
            if pkg_name not in seen_names:
                seen_names.add(pkg_name)
                known = KNOWN_SYNTAXES.get(pkg_name, {})
                syntaxes.append(PostCSSSyntaxInfo(
                    name=known.get('desc', pkg_name),
                    package_name=pkg_name,
                    syntax_type=known.get('type', 'syntax'),
                    languages=known.get('languages', []),
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # SugarSS file detection
        if file_path and self.SSS_FILE_PATTERN.search(file_path):
            if 'sugarss' not in seen_names:
                seen_names.add('sugarss')
                syntaxes.append(PostCSSSyntaxInfo(
                    name='SugarSS indent-based syntax',
                    package_name='sugarss',
                    syntax_type='syntax',
                    languages=['sss'],
                    file=file_path,
                ))

        stats = {
            "total_syntaxes": len(syntaxes),
            "syntax_types": list(set(s.syntax_type for s in syntaxes if s.syntax_type)),
            "languages": list(set(lang for s in syntaxes for lang in s.languages)),
            "has_scss_syntax": any(s.package_name == 'postcss-scss' for s in syntaxes),
            "has_less_syntax": any(s.package_name == 'postcss-less' for s in syntaxes),
            "has_html_syntax": any(s.package_name == 'postcss-html' for s in syntaxes),
            "has_sugarss": any(s.package_name == 'sugarss' for s in syntaxes),
            "has_safe_parser": any(s.package_name == 'postcss-safe-parser' for s in syntaxes),
        }

        return {"syntaxes": syntaxes, "stats": stats}
