"""
Less Import Extractor for CodeTrellis

Extracts Less @import statements with all import options.

Supports:
- @import "file.less";
- @import (reference) "file.less";   — import for reference only, don't output
- @import (inline) "file.css";       — include file inline, don't process
- @import (less) "file.css";         — treat file as Less regardless of extension
- @import (css) "file.less";         — output as CSS @import
- @import (multiple) "file.less";    — allow importing same file multiple times
- @import (optional) "file.less";    — continue if file not found
- @import (once) "file.less";        — default behavior, import only once
- Combined options: @import (reference, optional) "file.less";
- URL imports: @import url("file.less");
- Variable interpolation in imports: @import "@{theme}/base.less";
- Media query imports: @import "file.less" screen;

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class LessImportInfo:
    """Information about a Less @import statement."""
    path: str
    options: List[str] = field(default_factory=list)  # reference, inline, less, css, multiple, optional, once
    is_reference: bool = False     # (reference) — don't output
    is_inline: bool = False        # (inline) — include raw
    is_css: bool = False           # (css) — output as CSS @import
    is_less: bool = False          # (less) — force Less processing
    is_optional: bool = False      # (optional) — no error if missing
    is_multiple: bool = False      # (multiple) — allow re-import
    is_url: bool = False           # url() syntax
    has_interpolation: bool = False  # @{var} in path
    media_query: str = ""          # optional media query
    file: str = ""
    line_number: int = 0


class LessImportExtractor:
    """
    Extracts Less @import statements with all import options.

    Less supports 7 import options that control how imported files are processed:
    reference, inline, less, css, multiple, optional, once.
    """

    # @import with options: @import (option1, option2) "path";
    IMPORT_WITH_OPTIONS = re.compile(
        r'@import\s+\(([^)]+)\)\s+["\']([^"\']+)["\']\s*([^;]*)\s*;',
        re.MULTILINE
    )

    # @import without options: @import "path";
    IMPORT_SIMPLE = re.compile(
        r'@import\s+["\']([^"\']+)["\']\s*([^;]*)\s*;',
        re.MULTILINE
    )

    # @import url(): @import url("path");
    IMPORT_URL = re.compile(
        r'@import\s+url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)\s*([^;]*)\s*;',
        re.MULTILINE
    )

    # Interpolation pattern
    INTERPOLATION_PATTERN = re.compile(r'@\{[\w-]+\}')

    # Valid import options
    VALID_OPTIONS = {'reference', 'inline', 'less', 'css', 'multiple', 'optional', 'once'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Less @import statements.

        Returns dict with 'imports', 'stats' keys.
        """
        if not content or not content.strip():
            return {'imports': [], 'stats': {}}

        clean = self._strip_comments(content)
        imports = self._extract_imports(clean, file_path)

        stats = {
            'total_imports': len(imports),
            'reference_imports': sum(1 for i in imports if i.is_reference),
            'inline_imports': sum(1 for i in imports if i.is_inline),
            'css_imports': sum(1 for i in imports if i.is_css),
            'less_imports': sum(1 for i in imports if i.is_less),
            'optional_imports': sum(1 for i in imports if i.is_optional),
            'multiple_imports': sum(1 for i in imports if i.is_multiple),
            'url_imports': sum(1 for i in imports if i.is_url),
            'interpolated_imports': sum(1 for i in imports if i.has_interpolation),
            'has_import_options': any(i.options for i in imports),
        }

        return {'imports': imports, 'stats': stats}

    def _strip_comments(self, content: str) -> str:
        """Strip comments preserving line structure."""
        result = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_imports(self, content: str, file_path: str) -> List[LessImportInfo]:
        """Extract all @import statements."""
        imports: List[LessImportInfo] = []
        seen_positions: set = set()  # Avoid duplicates from overlapping patterns

        # 1. @import with options
        for match in self.IMPORT_WITH_OPTIONS.finditer(content):
            pos = match.start()
            if pos in seen_positions:
                continue
            seen_positions.add(pos)

            options_str = match.group(1)
            path = match.group(2)
            media = match.group(3).strip()
            line_num = content[:pos].count('\n') + 1

            options = [o.strip().lower() for o in options_str.split(',') if o.strip()]

            imports.append(LessImportInfo(
                path=path,
                options=options,
                is_reference='reference' in options,
                is_inline='inline' in options,
                is_css='css' in options,
                is_less='less' in options,
                is_optional='optional' in options,
                is_multiple='multiple' in options,
                is_url=False,
                has_interpolation=bool(self.INTERPOLATION_PATTERN.search(path)),
                media_query=media[:50],
                file=file_path,
                line_number=line_num,
            ))

        # 2. @import url()
        for match in self.IMPORT_URL.finditer(content):
            pos = match.start()
            if pos in seen_positions:
                continue
            seen_positions.add(pos)

            path = match.group(1)
            media = match.group(2).strip()
            line_num = content[:pos].count('\n') + 1

            imports.append(LessImportInfo(
                path=path,
                is_url=True,
                has_interpolation=bool(self.INTERPOLATION_PATTERN.search(path)),
                media_query=media[:50],
                file=file_path,
                line_number=line_num,
            ))

        # 3. Simple @import
        for match in self.IMPORT_SIMPLE.finditer(content):
            pos = match.start()
            if pos in seen_positions:
                continue
            # Check not already captured by options pattern
            before = content[max(0, pos - 3):pos + 10]
            if '(' in content[pos + 7:pos + 30] and ')' in content[pos + 7:pos + 50]:
                # Likely an options import already captured
                if any(abs(p - pos) < 5 for p in seen_positions):
                    continue
            seen_positions.add(pos)

            path = match.group(1)
            media = match.group(2).strip()
            line_num = content[:pos].count('\n') + 1

            # Detect if this is a CSS import (non-Less)
            is_css = path.endswith('.css') and not path.endswith('.less')

            imports.append(LessImportInfo(
                path=path,
                is_css=is_css,
                is_url=False,
                has_interpolation=bool(self.INTERPOLATION_PATTERN.search(path)),
                media_query=media[:50],
                file=file_path,
                line_number=line_num,
            ))

        return imports
