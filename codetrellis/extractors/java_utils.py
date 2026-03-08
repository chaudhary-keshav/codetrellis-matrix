"""
Shared utilities for Java framework extractors.

Part of CodeTrellis v4.94 - Java Framework Support
"""

import re


def normalize_java_content(content: str) -> str:
    """Normalize Java source content for regex extraction.

    Strips common leading whitespace from lines so that regex patterns
    that expect annotations at the start of lines will match indented code
    inside classes and methods.

    This is critical because Java code typically has annotations indented
    inside class bodies (e.g., 4 spaces for @GetMapping inside a controller),
    and our regex patterns anchor to line starts.

    Args:
        content: Raw Java source content

    Returns:
        Content with each line's leading whitespace stripped
    """
    if not content:
        return content
    # Strip leading whitespace from each line while preserving blank lines
    lines = content.split('\n')
    normalized = '\n'.join(line.lstrip() for line in lines)
    return normalized
