"""
JSDoc Extractor for TypeScript/JavaScript

Extracts JSDoc documentation comments from source files including:
- @description / main description
- @param tags with types and descriptions
- @returns / @return tags
- @example code blocks
- @deprecated notices
- @see references
- @throws / @exception
- Custom tags (@internal, @public, @private)

Part of CodeTrellis v2.0 - Phase 2 Context Enrichment
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class JSDocParam:
    """Represents a @param tag"""
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    optional: bool = False
    default: Optional[str] = None


@dataclass
class JSDocTag:
    """Represents a generic JSDoc tag"""
    tag: str
    value: str


@dataclass
class JSDocComment:
    """Represents a complete JSDoc comment block"""
    description: Optional[str] = None
    params: List[JSDocParam] = field(default_factory=list)
    returns: Optional[str] = None
    return_type: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    deprecated: Optional[str] = None
    see: List[str] = field(default_factory=list)
    throws: List[str] = field(default_factory=list)
    tags: List[JSDocTag] = field(default_factory=list)
    target_name: Optional[str] = None  # Name of function/class/interface this documents
    target_type: Optional[str] = None  # 'function', 'class', 'interface', 'method', etc.
    line_number: int = 0


@dataclass
class JSDocFileInfo:
    """JSDoc information for an entire file"""
    file_path: str
    comments: List[JSDocComment] = field(default_factory=list)
    file_description: Optional[str] = None  # Top-level file description

    def to_dict(self) -> Dict[str, Any]:
        return {
            'filePath': self.file_path,
            'fileDescription': self.file_description,
            'comments': [
                {
                    'targetName': c.target_name,
                    'targetType': c.target_type,
                    'description': c.description,
                    'params': [
                        {
                            'name': p.name,
                            'type': p.type,
                            'description': p.description,
                            'optional': p.optional,
                        }
                        for p in c.params
                    ],
                    'returns': c.returns,
                    'returnType': c.return_type,
                    'examples': c.examples,
                    'deprecated': c.deprecated,
                    'lineNumber': c.line_number,
                }
                for c in self.comments
            ],
            'stats': {
                'totalComments': len(self.comments),
                'documentedFunctions': len([c for c in self.comments if c.target_type == 'function']),
                'documentedClasses': len([c for c in self.comments if c.target_type == 'class']),
                'documentedMethods': len([c for c in self.comments if c.target_type == 'method']),
            }
        }


class JSDocExtractor:
    """
    Extracts JSDoc comments from TypeScript/JavaScript files.

    Example:
        extractor = JSDocExtractor()
        result = extractor.extract(content)
        for comment in result.comments:
            print(f"{comment.target_name}: {comment.description}")
    """

    # Pattern to match JSDoc comment blocks
    JSDOC_PATTERN = re.compile(
        r'/\*\*\s*\n([\s\S]*?)\*/',
        re.MULTILINE
    )

    # Pattern to match @param tags
    PARAM_PATTERN = re.compile(
        r'@param\s*(?:\{([^}]+)\})?\s*(\[)?(\w+)(?:\])?(?:\s*[-–—]\s*|\s+)?(.*)?',
        re.IGNORECASE
    )

    # Pattern to match @returns/@return tags
    RETURNS_PATTERN = re.compile(
        r'@returns?\s*(?:\{([^}]+)\})?\s*(.*)?',
        re.IGNORECASE
    )

    # Pattern to match @example tags
    EXAMPLE_PATTERN = re.compile(
        r'@example\s*([\s\S]*?)(?=@\w+|$)',
        re.IGNORECASE
    )

    # Pattern to match @deprecated tags
    DEPRECATED_PATTERN = re.compile(
        r'@deprecated\s*(.*)?',
        re.IGNORECASE
    )

    # Pattern to match @see tags
    SEE_PATTERN = re.compile(
        r'@see\s+(.*)',
        re.IGNORECASE
    )

    # Pattern to match @throws/@exception tags
    THROWS_PATTERN = re.compile(
        r'@(?:throws|exception)\s*(?:\{([^}]+)\})?\s*(.*)?',
        re.IGNORECASE
    )

    # Pattern to find what the JSDoc documents (function, class, etc.)
    TARGET_PATTERNS = {
        'function': re.compile(
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
            re.IGNORECASE
        ),
        'class': re.compile(
            r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)',
            re.IGNORECASE
        ),
        'interface': re.compile(
            r'(?:export\s+)?interface\s+(\w+)',
            re.IGNORECASE
        ),
        'type': re.compile(
            r'(?:export\s+)?type\s+(\w+)',
            re.IGNORECASE
        ),
        'const': re.compile(
            r'(?:export\s+)?const\s+(\w+)',
            re.IGNORECASE
        ),
        'method': re.compile(
            r'(?:public|private|protected|async|static|\s)*(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
            re.IGNORECASE
        ),
        'property': re.compile(
            r'(?:readonly\s+)?(\w+)\s*[?!]?\s*[:=]',
            re.IGNORECASE
        ),
    }

    def __init__(self):
        self.file_path = ""

    def extract(self, content: str, file_path: str = "") -> JSDocFileInfo:
        """
        Extract all JSDoc comments from file content.

        Args:
            content: File content to parse
            file_path: Path to the file (for reporting)

        Returns:
            JSDocFileInfo with all extracted comments
        """
        self.file_path = file_path
        result = JSDocFileInfo(file_path=file_path)

        # Find all JSDoc blocks
        lines = content.split('\n')

        for match in self.JSDOC_PATTERN.finditer(content):
            jsdoc_content = match.group(1)
            jsdoc_end = match.end()

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Parse the JSDoc block
            comment = self._parse_jsdoc_block(jsdoc_content, line_number)

            # Find what this JSDoc documents (look at code after the comment)
            following_code = content[jsdoc_end:jsdoc_end + 500]
            target_name, target_type = self._find_target(following_code)

            comment.target_name = target_name
            comment.target_type = target_type

            # Check if this is a file-level description (at top of file, no target)
            if line_number <= 5 and not target_name and comment.description:
                result.file_description = comment.description
            else:
                result.comments.append(comment)

        return result

    def _parse_jsdoc_block(self, content: str, line_number: int) -> JSDocComment:
        """Parse a single JSDoc comment block"""
        comment = JSDocComment(line_number=line_number)

        # Clean up the content (remove leading asterisks)
        lines = []
        for line in content.split('\n'):
            line = re.sub(r'^\s*\*\s?', '', line)
            lines.append(line)

        clean_content = '\n'.join(lines).strip()

        # Extract description (text before first @tag)
        desc_match = re.match(r'^([^@]+)', clean_content, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
            # Clean up multi-line descriptions
            description = ' '.join(description.split())
            if description:
                comment.description = description

        # Extract @param tags
        for match in self.PARAM_PATTERN.finditer(clean_content):
            param = JSDocParam(
                name=match.group(3),
                type=match.group(1),
                description=match.group(4).strip() if match.group(4) else None,
                optional=bool(match.group(2)),
            )
            comment.params.append(param)

        # Extract @returns
        returns_match = self.RETURNS_PATTERN.search(clean_content)
        if returns_match:
            comment.return_type = returns_match.group(1)
            comment.returns = returns_match.group(2).strip() if returns_match.group(2) else None

        # Extract @example
        for match in self.EXAMPLE_PATTERN.finditer(clean_content):
            example = match.group(1).strip()
            if example:
                comment.examples.append(example)

        # Extract @deprecated
        deprecated_match = self.DEPRECATED_PATTERN.search(clean_content)
        if deprecated_match:
            comment.deprecated = deprecated_match.group(1).strip() if deprecated_match.group(1) else "Deprecated"

        # Extract @see
        for match in self.SEE_PATTERN.finditer(clean_content):
            comment.see.append(match.group(1).strip())

        # Extract @throws
        for match in self.THROWS_PATTERN.finditer(clean_content):
            throw_type = match.group(1) or ''
            throw_desc = match.group(2).strip() if match.group(2) else ''
            throws_str = f"{throw_type}: {throw_desc}" if throw_type else throw_desc
            if throws_str:
                comment.throws.append(throws_str)

        return comment

    def _find_target(self, following_code: str) -> tuple:
        """Find the name and type of what this JSDoc documents"""
        # Skip whitespace and get first meaningful line
        following_code = following_code.strip()

        # Try each target pattern
        for target_type, pattern in self.TARGET_PATTERNS.items():
            match = pattern.match(following_code)
            if match:
                return match.group(1), target_type

        return None, None

    def extract_file(self, file_path: str) -> JSDocFileInfo:
        """
        Extract JSDoc from a file path.

        Args:
            file_path: Path to the TypeScript/JavaScript file

        Returns:
            JSDocFileInfo with extracted documentation
        """
        path = Path(file_path)
        if not path.exists():
            return JSDocFileInfo(file_path=file_path)

        content = path.read_text(encoding='utf-8', errors='ignore')
        return self.extract(content, file_path)


# Convenience function
def extract_jsdoc(content: str, file_path: str = "") -> JSDocFileInfo:
    """
    Extract JSDoc comments from content.

    Args:
        content: Source code content
        file_path: Optional file path for reporting

    Returns:
        JSDocFileInfo with all extracted comments
    """
    extractor = JSDocExtractor()
    return extractor.extract(content, file_path)
