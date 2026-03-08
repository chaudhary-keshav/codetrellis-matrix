"""
Express.js Error Handler Extractor - Extracts error handling patterns.

Supports:
- Custom error handler middleware (err, req, res, next)
- Error classes extending Error
- try/catch patterns in async handlers
- next(err) error forwarding
- HTTP error response patterns (res.status(4xx/5xx))
- express-async-errors usage
- Error handling middleware ordering
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExpressErrorHandlerInfo:
    """A single error handler definition."""
    name: str
    file: str = ""
    line_number: int = 0
    handler_type: str = ""  # global, route, async-wrapper, class
    handles_status_codes: List[int] = field(default_factory=list)
    has_logging: bool = False
    has_next_call: bool = False
    is_async: bool = False
    sends_json: bool = False
    sends_html: bool = False


@dataclass
class ExpressCustomErrorInfo:
    """A custom error class definition."""
    name: str
    file: str = ""
    line_number: int = 0
    extends: str = "Error"
    status_code: int = 0
    has_message: bool = False
    has_code: bool = False


@dataclass
class ExpressErrorSummary:
    """Summary of error handling in the project."""
    total_error_handlers: int = 0
    total_custom_errors: int = 0
    has_global_error_handler: bool = False
    has_not_found_handler: bool = False
    has_async_error_handling: bool = False
    has_express_async_errors: bool = False
    uses_next_error: bool = False
    error_response_format: str = ""  # json, html, mixed


# Error handler signature: (err, req, res, next)
ERROR_HANDLER_PATTERN = re.compile(
    r'(?:const|let|var|function)\s+(\w+)\s*=?\s*(?:async\s+)?(?:function\s*)?\('
    r'\s*(?:err|error)\s*,\s*(?:req|request)\s*,\s*(?:res|response)\s*,\s*next\s*\)'
)

# Inline error handler in app.use()
INLINE_ERROR_HANDLER_PATTERN = re.compile(
    r'\.use\s*\(\s*(?:async\s+)?(?:function\s*)?(?:\w+\s*)?\('
    r'\s*(?:err|error)\s*,\s*(?:req|request)\s*,\s*(?:res|response)\s*,\s*next\s*\)'
)

# Custom error class
ERROR_CLASS_PATTERN = re.compile(
    r'class\s+(\w+)\s+extends\s+(\w*Error\w*)'
)

# next(err) forwarding
NEXT_ERROR_PATTERN = re.compile(
    r'next\s*\(\s*(?:err|error|new\s+\w*Error|new\s+Error)'
)

# res.status(4xx/5xx)
STATUS_CODE_PATTERN = re.compile(
    r'\.status\s*\(\s*(\d{3})\s*\)'
)


class ExpressErrorExtractor:
    """Extracts Express.js error handling information from source code."""

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract error handling information from Express.js source code."""
        error_handlers: List[ExpressErrorHandlerInfo] = []
        custom_errors: List[ExpressCustomErrorInfo] = []
        lines = content.split('\n')

        has_async_errors_import = 'express-async-errors' in content
        uses_next_error = bool(NEXT_ERROR_PATTERN.search(content))

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Named error handler function
            handler_match = ERROR_HANDLER_PATTERN.search(stripped)
            if handler_match:
                name = handler_match.group(1)
                # Look ahead for body content
                body = self._extract_body(lines, i - 1)
                status_codes = [int(m) for m in STATUS_CODE_PATTERN.findall(body)]

                error_handlers.append(ExpressErrorHandlerInfo(
                    name=name,
                    file=file_path,
                    line_number=i,
                    handler_type='global' if self._is_global_handler(lines, i - 1) else 'route',
                    handles_status_codes=status_codes,
                    has_logging=self._has_logging(body),
                    has_next_call='next(' in body,
                    is_async='async' in stripped,
                    sends_json='.json(' in body,
                    sends_html='.render(' in body or '.send(' in body,
                ))

            # Inline error handler in app.use()
            if INLINE_ERROR_HANDLER_PATTERN.search(stripped):
                body = self._extract_body(lines, i - 1)
                status_codes = [int(m) for m in STATUS_CODE_PATTERN.findall(body)]

                error_handlers.append(ExpressErrorHandlerInfo(
                    name='<inline>',
                    file=file_path,
                    line_number=i,
                    handler_type='global',
                    handles_status_codes=status_codes,
                    has_logging=self._has_logging(body),
                    has_next_call='next(' in body,
                    is_async='async' in stripped,
                    sends_json='.json(' in body,
                    sends_html='.render(' in body or '.send(' in body,
                ))

            # Custom error classes
            class_match = ERROR_CLASS_PATTERN.search(stripped)
            if class_match:
                name = class_match.group(1)
                extends = class_match.group(2)
                body = self._extract_body(lines, i - 1)

                status_code = 0
                sc_match = re.search(r'this\.(?:statusCode|status)\s*=\s*(\d{3})', body)
                if sc_match:
                    status_code = int(sc_match.group(1))

                custom_errors.append(ExpressCustomErrorInfo(
                    name=name,
                    file=file_path,
                    line_number=i,
                    extends=extends,
                    status_code=status_code,
                    has_message='this.message' in body or 'super(' in body,
                    has_code='this.code' in body or 'this.errorCode' in body,
                ))

        # Build summary
        summary = self._build_summary(
            error_handlers, custom_errors, has_async_errors_import, uses_next_error
        )

        return {
            "error_handlers": error_handlers,
            "custom_errors": custom_errors,
            "summary": summary,
        }

    def _extract_body(self, lines: List[str], start_idx: int, max_lines: int = 30) -> str:
        """Extract function body starting from a line."""
        body_lines = []
        depth = 0
        started = False
        for j in range(start_idx, min(start_idx + max_lines, len(lines))):
            line = lines[j]
            body_lines.append(line)
            depth += line.count('{') - line.count('}')
            if '{' in line:
                started = True
            if started and depth <= 0:
                break
        return '\n'.join(body_lines)

    def _is_global_handler(self, lines: List[str], idx: int) -> bool:
        """Check if error handler is used globally (registered via app.use)."""
        # Look backwards for app.use registration
        for j in range(max(0, idx - 5), min(idx + 5, len(lines))):
            if '.use(' in lines[j]:
                return True
        return False

    def _has_logging(self, body: str) -> bool:
        """Check if error handler includes logging."""
        logging_patterns = ['console.error', 'console.log', 'logger.', 'log.error', 'winston.', 'pino.']
        return any(p in body for p in logging_patterns)

    def _build_summary(
        self,
        handlers: List[ExpressErrorHandlerInfo],
        custom_errors: List[ExpressCustomErrorInfo],
        has_async_errors: bool,
        uses_next_error: bool,
    ) -> ExpressErrorSummary:
        """Build error handling summary."""
        summary = ExpressErrorSummary()
        summary.total_error_handlers = len(handlers)
        summary.total_custom_errors = len(custom_errors)
        summary.has_global_error_handler = any(h.handler_type == 'global' for h in handlers)
        summary.has_not_found_handler = any(
            404 in h.handles_status_codes for h in handlers
        )
        summary.has_async_error_handling = has_async_errors or any(h.is_async for h in handlers)
        summary.has_express_async_errors = has_async_errors
        summary.uses_next_error = uses_next_error

        json_count = sum(1 for h in handlers if h.sends_json)
        html_count = sum(1 for h in handlers if h.sends_html)
        if json_count > 0 and html_count > 0:
            summary.error_response_format = 'mixed'
        elif json_count > 0:
            summary.error_response_format = 'json'
        elif html_count > 0:
            summary.error_response_format = 'html'

        return summary
