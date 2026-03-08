"""
Django Middleware Extractor for CodeTrellis.

Extracts Django middleware classes and their lifecycle hooks.
Supports Django 1.x (old-style) and 2.x+ (new-style) middleware.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoMiddlewareInfo:
    """Information about a Django middleware."""
    name: str
    middleware_type: str  # new_style, old_style, function_based
    file: str = ""
    hooks: List[str] = field(default_factory=list)
    # process_request, process_response, process_view, process_exception,
    # process_template_response, __call__
    base_classes: List[str] = field(default_factory=list)
    is_async: bool = False
    has_sync_to_async: bool = False
    has_async_to_sync: bool = False
    line_number: int = 0


# Known Django middleware
BUILTIN_MIDDLEWARE = {
    'SecurityMiddleware', 'SessionMiddleware', 'CommonMiddleware',
    'CsrfViewMiddleware', 'AuthenticationMiddleware', 'MessageMiddleware',
    'XFrameOptionsMiddleware', 'LocaleMiddleware', 'GZipMiddleware',
    'ConditionalGetMiddleware', 'CacheMiddleware', 'FetchFromCacheMiddleware',
    'UpdateCacheMiddleware', 'CurrentSiteMiddleware', 'BrokenLinkEmailsMiddleware',
}

# Middleware hooks (old-style)
OLD_STYLE_HOOKS = {
    'process_request', 'process_response', 'process_view',
    'process_exception', 'process_template_response',
}

# New-style hooks
NEW_STYLE_HOOKS = {'__call__', '__init__'}


class DjangoMiddlewareExtractor:
    """
    Extracts Django middleware definitions.

    Handles:
    - New-style middleware (Django 2.0+): __init__ + __call__
    - Old-style middleware: MiddlewareMixin subclass with process_* hooks
    - Function-based middleware (def middleware(get_response):)
    - Async middleware (Django 4.1+)
    - MIDDLEWARE setting detection
    """

    # Class-based middleware
    MIDDLEWARE_CLASS_PATTERN = re.compile(
        r'^class\s+(\w+(?:Middleware\w*)?)\s*\(\s*([^)]*)\s*\)\s*:',
        re.MULTILINE
    )

    # Function-based middleware
    FUNC_MIDDLEWARE_PATTERN = re.compile(
        r'^(async\s+)?def\s+(\w+)\s*\(\s*get_response\s*\)',
        re.MULTILINE
    )

    # MIDDLEWARE setting
    MIDDLEWARE_SETTING_PATTERN = re.compile(
        r'MIDDLEWARE\s*=\s*\[([^\]]+)\]',
        re.DOTALL
    )

    # Hook methods
    HOOK_PATTERN = re.compile(
        r'^\s{4}(async\s+)?def\s+(process_request|process_response|process_view|process_exception|process_template_response|__call__|__init__)\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Django middleware extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django middleware definitions.

        Returns:
            Dict with 'middleware' and 'middleware_config'
        """
        middleware = []

        # Extract class-based middleware
        middleware.extend(self._extract_class_middleware(content, file_path))

        # Extract function-based middleware
        middleware.extend(self._extract_function_middleware(content, file_path))

        # Extract MIDDLEWARE setting
        middleware_config = self._extract_middleware_setting(content)

        return {
            'middleware': middleware,
            'middleware_config': middleware_config,
        }

    def _extract_class_middleware(self, content: str, file_path: str) -> List[DjangoMiddlewareInfo]:
        """Extract class-based middleware."""
        result = []

        for match in self.MIDDLEWARE_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip() for b in bases_str.split(',') if b.strip()]

            # Classify: is this actually middleware?
            is_middleware = (
                'Middleware' in class_name
                or any('MiddlewareMixin' in b for b in bases)
                or any(b.strip() in BUILTIN_MIDDLEWARE for b in bases)
            )

            if not is_middleware:
                # Check for get_response in __init__ (new-style pattern)
                class_body = self._extract_class_body(content, match.end())
                if 'get_response' not in class_body:
                    continue

            class_body = self._extract_class_body(content, match.end())

            # Detect hooks
            hooks = []
            is_async = False
            for hook_match in self.HOOK_PATTERN.finditer(class_body):
                if hook_match.group(1):  # async
                    is_async = True
                hooks.append(hook_match.group(2))

            # Determine middleware type
            is_old_style = bool(set(hooks) & OLD_STYLE_HOOKS - {'__call__', '__init__'})
            middleware_type = 'old_style' if is_old_style else 'new_style'

            # Check for async utilities
            has_sync_to_async = 'sync_to_async' in class_body
            has_async_to_sync = 'async_to_sync' in class_body

            result.append(DjangoMiddlewareInfo(
                name=class_name,
                middleware_type=middleware_type,
                file=file_path,
                hooks=hooks,
                base_classes=bases,
                is_async=is_async,
                has_sync_to_async=has_sync_to_async,
                has_async_to_sync=has_async_to_sync,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result

    def _extract_function_middleware(self, content: str, file_path: str) -> List[DjangoMiddlewareInfo]:
        """Extract function-based middleware."""
        result = []

        for match in self.FUNC_MIDDLEWARE_PATTERN.finditer(content):
            is_async = match.group(1) is not None
            func_name = match.group(2)

            result.append(DjangoMiddlewareInfo(
                name=func_name,
                middleware_type='function_based',
                file=file_path,
                hooks=['__call__'],
                is_async=is_async,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result

    def _extract_middleware_setting(self, content: str) -> List[str]:
        """Extract MIDDLEWARE setting from settings file."""
        match = self.MIDDLEWARE_SETTING_PATTERN.search(content)
        if not match:
            return []

        middleware_str = match.group(1)
        return [
            m.strip().strip("'\"")
            for m in middleware_str.split(',')
            if m.strip() and m.strip().strip("'\"")
        ]

    def _extract_class_body(self, content: str, class_end: int) -> str:
        """Extract class body using indentation."""
        lines = content.split('\n')
        start_line = content[:class_end].count('\n')
        body_lines = []

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent < 4 and line.strip():
                break
            body_lines.append(line)

        return '\n'.join(body_lines)
