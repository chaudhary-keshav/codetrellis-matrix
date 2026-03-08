"""
CodeTrellis Error Extractor
====================

Extracts error handling patterns from TypeScript/Angular files.

Features:
- try/catch blocks with error types
- Error class definitions
- HTTP error handling (catchError, throwError)
- Custom error handlers
- Error boundaries (Angular ErrorHandler)

Output format:
    [ERROR_HANDLING]
    file.ts
      try-catch: handleApiCall→HttpErrorResponse
      error-class: CustomApiError extends Error
      http-error: catchError→handleError
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class TryCatchBlock:
    """Information about a try-catch block"""
    method_name: str
    error_type: Optional[str] = None
    error_variable: str = "error"
    has_finally: bool = False
    rethrows: bool = False

    def to_codetrellis_format(self) -> str:
        result = f"try-catch:{self.method_name}"
        if self.error_type:
            result += f"→{self.error_type}"
        if self.has_finally:
            result += "|finally"
        if self.rethrows:
            result += "|rethrows"
        return result


@dataclass
class ErrorClass:
    """Information about a custom error class"""
    name: str
    extends: str = "Error"
    properties: List[str] = field(default_factory=list)

    def to_codetrellis_format(self) -> str:
        result = f"error-class:{self.name}"
        if self.extends != "Error":
            result += f" extends {self.extends}"
        if self.properties:
            result += f"|props:{','.join(self.properties)}"
        return result


@dataclass
class HttpErrorHandler:
    """Information about HTTP error handling (RxJS patterns)"""
    operator: str  # catchError, throwError, retry, etc.
    handler_method: Optional[str] = None
    error_type: Optional[str] = None

    def to_codetrellis_format(self) -> str:
        result = f"http-error:{self.operator}"
        if self.handler_method:
            result += f"→{self.handler_method}"
        if self.error_type:
            result += f"|type:{self.error_type}"
        return result


@dataclass
class ErrorBoundary:
    """Information about Angular ErrorHandler implementation"""
    class_name: str
    handles_types: List[str] = field(default_factory=list)
    logs_to: Optional[str] = None  # console, service, etc.

    def to_codetrellis_format(self) -> str:
        result = f"error-boundary:{self.class_name}"
        if self.handles_types:
            result += f"|handles:{','.join(self.handles_types)}"
        if self.logs_to:
            result += f"|logs:{self.logs_to}"
        return result


@dataclass
class ErrorFileInfo:
    """All error handling information for a single file"""
    file_path: str
    try_catch_blocks: List[TryCatchBlock] = field(default_factory=list)
    error_classes: List[ErrorClass] = field(default_factory=list)
    http_error_handlers: List[HttpErrorHandler] = field(default_factory=list)
    error_boundaries: List[ErrorBoundary] = field(default_factory=list)

    def has_error_handling(self) -> bool:
        return (
            len(self.try_catch_blocks) > 0 or
            len(self.error_classes) > 0 or
            len(self.http_error_handlers) > 0 or
            len(self.error_boundaries) > 0
        )

    def to_codetrellis_format(self) -> str:
        lines = [self.file_path]

        for block in self.try_catch_blocks:
            lines.append(f"  {block.to_codetrellis_format()}")

        for error_class in self.error_classes:
            lines.append(f"  {error_class.to_codetrellis_format()}")

        for handler in self.http_error_handlers:
            lines.append(f"  {handler.to_codetrellis_format()}")

        for boundary in self.error_boundaries:
            lines.append(f"  {boundary.to_codetrellis_format()}")

        return "\n".join(lines)


class ErrorExtractor:
    """
    Extracts error handling patterns from TypeScript/Angular files.

    Usage:
        extractor = ErrorExtractor()
        file_info = extractor.extract(content, file_path)
        print(file_info.to_codetrellis_format())
    """

    # Pattern for try-catch blocks
    TRY_CATCH_PATTERN = re.compile(
        r'(?P<method>\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{[^{}]*'
        r'try\s*\{',
        re.MULTILINE | re.DOTALL
    )

    # Pattern for catch clause with optional type
    CATCH_PATTERN = re.compile(
        r'catch\s*\(\s*(?P<var>\w+)(?:\s*:\s*(?P<type>\w+))?\s*\)',
        re.MULTILINE
    )

    # Pattern for finally block
    FINALLY_PATTERN = re.compile(r'\}\s*finally\s*\{', re.MULTILINE)

    # Pattern for throw/rethrow
    RETHROW_PATTERN = re.compile(r'throw\s+(?P<var>\w+)\s*;', re.MULTILINE)

    # Pattern for error class definitions
    ERROR_CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(?P<name>\w+Error)\s+extends\s+(?P<extends>\w+)',
        re.MULTILINE
    )

    # Pattern for RxJS catchError
    CATCH_ERROR_PATTERN = re.compile(
        r'catchError\s*\(\s*(?:'
        r'(?P<method>this\.[\w.]+|\w+)|'  # Method reference
        r'\(\s*(?P<err>\w+)(?:\s*:\s*(?P<type>\w+))?\s*\)\s*=>'  # Arrow function
        r')',
        re.MULTILINE
    )

    # Pattern for throwError
    THROW_ERROR_PATTERN = re.compile(
        r'throwError\s*\(\s*\(\)\s*=>\s*(?:new\s+)?(?P<type>\w+)',
        re.MULTILINE
    )

    # Pattern for retry operators
    RETRY_PATTERN = re.compile(
        r'(?P<op>retry|retryWhen)\s*\(\s*(?P<count>\d+)?',
        re.MULTILINE
    )

    # Pattern for ErrorHandler implementation
    ERROR_HANDLER_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(?P<name>\w+)\s+implements\s+ErrorHandler',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> ErrorFileInfo:
        """
        Extract all error handling patterns from file content.

        Args:
            content: File content to parse
            file_path: Path to the file (for reporting)

        Returns:
            ErrorFileInfo with all extracted patterns
        """
        file_info = ErrorFileInfo(file_path=file_path)

        # Extract try-catch blocks
        file_info.try_catch_blocks = self._extract_try_catch(content)

        # Extract custom error classes
        file_info.error_classes = self._extract_error_classes(content)

        # Extract HTTP error handlers
        file_info.http_error_handlers = self._extract_http_error_handlers(content)

        # Extract error boundaries
        file_info.error_boundaries = self._extract_error_boundaries(content)

        return file_info

    def _extract_try_catch(self, content: str) -> List[TryCatchBlock]:
        """Extract try-catch blocks with method context"""
        blocks = []

        # Find all methods that contain try blocks
        # Simplified approach: find method-like patterns with try inside
        method_pattern = re.compile(
            r'(?:async\s+)?(?P<method>\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|,\s]+)?\s*\{',
            re.MULTILINE
        )

        for method_match in method_pattern.finditer(content):
            method_name = method_match.group('method')
            method_start = method_match.start()

            # Find the method body by brace matching
            method_body = self._extract_brace_content(content, method_match.end() - 1)
            if not method_body:
                continue

            # Check if this method has a try block
            if 'try' not in method_body:
                continue

            # Find catch clause
            catch_match = self.CATCH_PATTERN.search(method_body)
            if not catch_match:
                continue

            error_var = catch_match.group('var')
            error_type = catch_match.group('type')

            # Check for finally
            has_finally = bool(self.FINALLY_PATTERN.search(method_body))

            # Check for rethrow
            rethrows = bool(re.search(rf'throw\s+{error_var}\s*;', method_body))

            blocks.append(TryCatchBlock(
                method_name=method_name,
                error_type=error_type,
                error_variable=error_var,
                has_finally=has_finally,
                rethrows=rethrows
            ))

        return blocks

    def _extract_error_classes(self, content: str) -> List[ErrorClass]:
        """Extract custom error class definitions"""
        classes = []

        for match in self.ERROR_CLASS_PATTERN.finditer(content):
            name = match.group('name')
            extends = match.group('extends')

            # Try to extract properties from the class body
            class_body = self._extract_brace_content(content, match.end())
            properties = []

            if class_body:
                # Look for constructor parameters or property declarations
                prop_pattern = re.compile(
                    r'(?:public|private|protected|readonly)\s+(\w+)\s*[:\=]',
                    re.MULTILINE
                )
                for prop_match in prop_pattern.finditer(class_body):
                    prop_name = prop_match.group(1)
                    if prop_name not in ['constructor']:
                        properties.append(prop_name)

            classes.append(ErrorClass(
                name=name,
                extends=extends,
                properties=properties
            ))

        return classes

    def _extract_http_error_handlers(self, content: str) -> List[HttpErrorHandler]:
        """Extract RxJS error handling patterns"""
        handlers = []

        # Extract catchError calls
        for match in self.CATCH_ERROR_PATTERN.finditer(content):
            method = match.group('method')
            error_type = match.group('type')

            handler_method = None
            if method:
                # Clean up method reference (this.handleError -> handleError)
                handler_method = method.replace('this.', '')

            handlers.append(HttpErrorHandler(
                operator='catchError',
                handler_method=handler_method,
                error_type=error_type
            ))

        # Extract throwError calls
        for match in self.THROW_ERROR_PATTERN.finditer(content):
            error_type = match.group('type')
            handlers.append(HttpErrorHandler(
                operator='throwError',
                error_type=error_type
            ))

        # Extract retry patterns
        for match in self.RETRY_PATTERN.finditer(content):
            op = match.group('op')
            count = match.group('count')
            handlers.append(HttpErrorHandler(
                operator=op,
                handler_method=f"count:{count}" if count else None
            ))

        return handlers

    def _extract_error_boundaries(self, content: str) -> List[ErrorBoundary]:
        """Extract Angular ErrorHandler implementations"""
        boundaries = []

        for match in self.ERROR_HANDLER_PATTERN.finditer(content):
            class_name = match.group('name')

            # Extract the class body
            class_body = self._extract_brace_content(content, match.end())
            if not class_body:
                boundaries.append(ErrorBoundary(class_name=class_name))
                continue

            # Check what error types are handled
            handles_types = []
            instanceof_pattern = re.compile(r'instanceof\s+(\w+Error)', re.MULTILINE)
            for type_match in instanceof_pattern.finditer(class_body):
                handles_types.append(type_match.group(1))

            # Check logging destination
            logs_to = None
            if 'console.error' in class_body:
                logs_to = 'console'
            elif 'this.logger' in class_body or 'logService' in class_body.lower():
                logs_to = 'service'
            elif 'Sentry' in class_body or 'sentry' in class_body:
                logs_to = 'sentry'

            boundaries.append(ErrorBoundary(
                class_name=class_name,
                handles_types=handles_types,
                logs_to=logs_to
            ))

        return boundaries

    def _extract_brace_content(self, content: str, start_index: int) -> Optional[str]:
        """Extract content within braces using brace matching"""
        # Find opening brace
        brace_start = content.find('{', start_index)
        if brace_start == -1:
            return None

        depth = 1
        i = brace_start + 1
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
            i += 1

        if depth == 0:
            return content[brace_start + 1:i - 1]
        return None


def extract_errors(file_path: Path) -> Optional[ErrorFileInfo]:
    """
    Convenience function to extract errors from a file.

    Args:
        file_path: Path to the TypeScript file

    Returns:
        ErrorFileInfo or None if no error handling found
    """
    if not file_path.exists():
        return None

    content = file_path.read_text(encoding='utf-8')
    extractor = ErrorExtractor()
    file_info = extractor.extract(content, str(file_path))

    if file_info.has_error_handling():
        return file_info
    return None


def extract_project_errors(project_path: Path) -> List[ErrorFileInfo]:
    """
    Extract error handling patterns from all TypeScript files in a project.

    Args:
        project_path: Root path of the project

    Returns:
        List of ErrorFileInfo for files with error handling
    """
    results = []
    extractor = ErrorExtractor()

    for ts_file in project_path.rglob('*.ts'):
        # Skip node_modules and test files
        if 'node_modules' in str(ts_file):
            continue
        if '.spec.ts' in str(ts_file) or '.test.ts' in str(ts_file):
            continue

        try:
            content = ts_file.read_text(encoding='utf-8')
            file_info = extractor.extract(content, str(ts_file))

            if file_info.has_error_handling():
                results.append(file_info)
        except Exception:
            # Skip files that can't be read
            continue

    return results
