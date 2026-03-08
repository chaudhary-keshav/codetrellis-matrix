"""
SWR Middleware Extractor for CodeTrellis

Extracts SWR middleware patterns:
- Built-in middleware: serialize, immutable
- Custom middleware functions (v1+)
- Middleware composition via use option
- Logger middleware patterns
- Middleware chain detection

Supports:
- swr v1.x (middleware API introduced)
- swr v2.x (middleware improvements)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SWRMiddlewareInfo:
    """Information about SWR middleware usage."""
    name: str
    file: str = ""
    line_number: int = 0
    middleware_type: str = ""  # built-in, custom, logger, serialize
    is_exported: bool = False


class SWRMiddlewareExtractor:
    """
    Extracts SWR middleware patterns from source code.

    Detects:
    - Middleware function definitions
    - use option in SWR hooks and SWRConfig
    - Built-in middleware (serialize, immutable)
    - Logger/debugging middleware
    """

    # Middleware definition pattern
    MIDDLEWARE_DEF_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w+)\s*'
        r'(?::\s*\w+\s*)?=?\s*\(\s*useSWRNext\s*\)',
        re.MULTILINE
    )

    # Alternative middleware pattern (returns function)
    MIDDLEWARE_RETURN_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w+)\s*'
        r'(?::\s*Middleware\s*)?=?\s*\(\s*(?:useSWRNext|hook)\s*\)\s*=>\s*'
        r'\(\s*key\s*,\s*fetcher\s*,\s*config\s*\)',
        re.MULTILINE
    )

    # use option in SWR
    USE_OPTION_PATTERN = re.compile(
        r'\buse\s*:\s*\[([^\]]*)\]',
        re.MULTILINE
    )

    # serialize middleware
    SERIALIZE_PATTERN = re.compile(
        r"from\s+['\"]swr/(?:serialize|_internal)['\"].*\bserialize\b|"
        r"\bserialize\b.*middleware",
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all SWR middleware patterns from source code."""
        result: Dict[str, Any] = {
            'middlewares': [],
        }

        # Extract middleware definitions
        for match in self.MIDDLEWARE_DEF_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()] or 'export' in match.group(0)

            middleware_type = "custom"
            if 'log' in name.lower() or 'debug' in name.lower():
                middleware_type = "logger"

            result['middlewares'].append(SWRMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                middleware_type=middleware_type,
                is_exported=is_exported,
            ))

        # Extract from alternative pattern
        for match in self.MIDDLEWARE_RETURN_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start()] or 'export' in match.group(0)

            # Skip if already found
            existing = [m.name for m in result['middlewares'] if isinstance(m, SWRMiddlewareInfo)]
            if name in existing:
                continue

            result['middlewares'].append(SWRMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                middleware_type="custom",
                is_exported=is_exported,
            ))

        # Detect use option middleware references
        for match in self.USE_OPTION_PATTERN.finditer(content):
            names = match.group(1).strip()
            if names:
                for mw_name in re.findall(r'\b(\w+)\b', names):
                    line_num = content[:match.start()].count('\n') + 1
                    existing = [m.name for m in result['middlewares'] if isinstance(m, SWRMiddlewareInfo)]
                    if mw_name not in existing and mw_name not in ('true', 'false', 'null', 'undefined'):
                        result['middlewares'].append(SWRMiddlewareInfo(
                            name=mw_name,
                            file=file_path,
                            line_number=line_num,
                            middleware_type="reference",
                        ))

        return result
