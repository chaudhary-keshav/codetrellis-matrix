"""
CodeTrellis Error Handling Module
==========================

Standardized error codes and exception classes for CodeTrellis.
Implements recommendations from Report 2 Section 6.4 and Issue 3.6.

Version: 4.1.0
Created: 2 February 2026
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime


# Configure module logger
logger = logging.getLogger(__name__)


class CodeTrellisErrorCode(Enum):
    """
    Standardized error codes for CodeTrellis operations.

    Error code format: EXXX where X is a digit
    Categories:
        E0XX - General errors
        E1XX - File/IO errors
        E2XX - Parse errors
        E3XX - Extraction errors
        E4XX - Compression errors
        E5XX - LSP errors
        E6XX - Plugin errors
        E7XX - Validation errors
    """
    # General errors (E0XX)
    UNKNOWN = "E000"
    CONFIGURATION_ERROR = "E001"
    INITIALIZATION_ERROR = "E002"

    # File/IO errors (E1XX)
    FILE_NOT_FOUND = "E100"
    FILE_READ_ERROR = "E101"
    FILE_WRITE_ERROR = "E102"
    DIRECTORY_NOT_FOUND = "E103"
    PERMISSION_DENIED = "E104"
    ENCODING_ERROR = "E105"

    # Parse errors (E2XX)
    PARSE_ERROR = "E200"
    SYNTAX_ERROR = "E201"
    INVALID_STRUCTURE = "E202"
    UNSUPPORTED_FORMAT = "E203"

    # Extraction errors (E3XX)
    EXTRACTION_FAILED = "E300"
    EXTRACTOR_NOT_FOUND = "E301"
    PARTIAL_EXTRACTION = "E302"
    TIMEOUT_ERROR = "E303"

    # Compression errors (E4XX)
    COMPRESSION_ERROR = "E400"
    TOKEN_BUDGET_EXCEEDED = "E401"
    INVALID_TIER = "E402"

    # LSP errors (E5XX)
    LSP_UNAVAILABLE = "E500"
    LSP_CONNECTION_FAILED = "E501"
    LSP_TIMEOUT = "E502"
    NODE_NOT_FOUND = "E503"

    # Plugin errors (E6XX)
    PLUGIN_LOAD_ERROR = "E600"
    PLUGIN_NOT_FOUND = "E601"
    PLUGIN_VALIDATION_FAILED = "E602"

    # Validation errors (E7XX)
    VALIDATION_ERROR = "E700"
    SCHEMA_MISMATCH = "E701"
    REQUIRED_FIELD_MISSING = "E702"


class CodeTrellisError(Exception):
    """
    Base exception class for all CodeTrellis errors.

    Provides consistent error formatting with:
    - Error code for programmatic handling
    - Human-readable message
    - Optional context dictionary for debugging
    - Timestamp for logging

    Example:
        >>> raise CodeTrellisError(
        ...     code=CodeTrellisErrorCode.FILE_NOT_FOUND,
        ...     message="Could not find file",
        ...     context={"path": "/path/to/file.ts"}
        ... )
        CodeTrellisError: [E100] Could not find file (path: /path/to/file.ts)
    """

    def __init__(
        self,
        code: CodeTrellisErrorCode,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.code = code
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()

        # Build full error message
        full_message = f"[{code.value}] {message}"
        if context:
            context_str = ", ".join(f"{k}: {v}" for k, v in context.items())
            full_message += f" ({context_str})"

        super().__init__(full_message)

        # Log the error
        logger.error(f"{full_message}", exc_info=cause is not None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "code": self.code.value,
            "code_name": self.code.name,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None
        }


# Specific exception classes for common error types

class FileError(CodeTrellisError):
    """Raised for file-related errors."""

    def __init__(self, message: str, path: str, **kwargs):
        super().__init__(
            code=CodeTrellisErrorCode.FILE_NOT_FOUND,
            message=message,
            context={"path": path, **kwargs}
        )


class ParseError(CodeTrellisError):
    """Raised when parsing fails."""

    def __init__(self, message: str, file_path: str, line: Optional[int] = None, **kwargs):
        context = {"file_path": file_path}
        if line is not None:
            context["line"] = line
        context.update(kwargs)
        super().__init__(
            code=CodeTrellisErrorCode.PARSE_ERROR,
            message=message,
            context=context
        )


class ExtractionError(CodeTrellisError):
    """Raised when extraction fails."""

    def __init__(self, message: str, extractor_name: str, file_path: str, **kwargs):
        super().__init__(
            code=CodeTrellisErrorCode.EXTRACTION_FAILED,
            message=message,
            context={"extractor": extractor_name, "file_path": file_path, **kwargs}
        )


class CompressionError(CodeTrellisError):
    """Raised when compression fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            code=CodeTrellisErrorCode.COMPRESSION_ERROR,
            message=message,
            context=kwargs
        )


class LSPError(CodeTrellisError):
    """Raised for LSP-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            code=CodeTrellisErrorCode.LSP_UNAVAILABLE,
            message=message,
            context=kwargs
        )


class ValidationError(CodeTrellisError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = kwargs
        if field:
            context["field"] = field
        super().__init__(
            code=CodeTrellisErrorCode.VALIDATION_ERROR,
            message=message,
            context=context
        )


@dataclass
class ExtractorResult:
    """
    Result wrapper for extractor operations with error isolation.

    Implements Report 2 Section 3.6 recommendation for resilient extraction.
    Extractors should return this instead of raising exceptions.

    Example:
        >>> result = ExtractorResult.success(
        ...     extractor_name="InterfaceExtractor",
        ...     file_path="/path/to/file.ts",
        ...     data={"interfaces": [...]}
        ... )
        >>> if not result.success:
        ...     logger.warning(f"Extraction failed: {result.errors}")
    """
    extractor_name: str
    file_path: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @classmethod
    def success(cls, extractor_name: str, file_path: str, data: Dict[str, Any]) -> 'ExtractorResult':
        """Create a successful extraction result."""
        return cls(
            extractor_name=extractor_name,
            file_path=file_path,
            success=True,
            data=data
        )

    @classmethod
    def failure(cls, extractor_name: str, file_path: str, error: str) -> 'ExtractorResult':
        """Create a failed extraction result."""
        return cls(
            extractor_name=extractor_name,
            file_path=file_path,
            success=False,
            errors=[error]
        )

    @classmethod
    def partial(cls, extractor_name: str, file_path: str, data: Dict[str, Any], warnings: list) -> 'ExtractorResult':
        """Create a partial extraction result with warnings."""
        return cls(
            extractor_name=extractor_name,
            file_path=file_path,
            success=True,
            data=data,
            warnings=warnings
        )


def resilient_extract(extractor_name: str):
    """
    Decorator for resilient extraction with error isolation.

    Wraps extractor methods to catch exceptions and return ExtractorResult
    instead of propagating errors.

    Usage:
        @resilient_extract("InterfaceExtractor")
        def extract(self, content: str, file_path: str) -> ExtractorResult:
            # extraction logic
            return ExtractorResult.success(...)
    """
    def decorator(func):
        def wrapper(self, content: str, file_path: str, *args, **kwargs):
            try:
                result = func(self, content, file_path, *args, **kwargs)
                # If function returns ExtractorResult, use it directly
                if isinstance(result, ExtractorResult):
                    return result
                # Otherwise wrap the result
                return ExtractorResult.success(
                    extractor_name=extractor_name,
                    file_path=file_path,
                    data=result if isinstance(result, dict) else {"result": result}
                )
            except Exception as e:
                logger.warning(f"Extraction failed for {file_path} in {extractor_name}: {e}")
                return ExtractorResult.failure(
                    extractor_name=extractor_name,
                    file_path=file_path,
                    error=str(e)
                )
        return wrapper
    return decorator


class ErrorCollector:
    """
    Collects errors during extraction without stopping the process.

    Useful for batch operations where you want to continue processing
    even if some files fail.

    Example:
        >>> collector = ErrorCollector()
        >>> for file in files:
        ...     try:
        ...         process(file)
        ...     except Exception as e:
        ...         collector.add(file, e)
        >>> if collector.has_errors:
        ...     print(collector.summary())
    """

    def __init__(self):
        self.errors: list[tuple[str, str, Exception]] = []
        self.warnings: list[tuple[str, str]] = []

    def add_error(self, file_path: str, operation: str, error: Exception):
        """Add an error to the collection."""
        self.errors.append((file_path, operation, error))
        logger.error(f"Error in {operation} for {file_path}: {error}")

    def add_warning(self, file_path: str, message: str):
        """Add a warning to the collection."""
        self.warnings.append((file_path, message))
        logger.warning(f"Warning for {file_path}: {message}")

    @property
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were collected."""
        return len(self.warnings) > 0

    def summary(self) -> str:
        """Generate a summary of all collected errors and warnings."""
        lines = []

        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for file_path, operation, error in self.errors:
                lines.append(f"  - {file_path} ({operation}): {error}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for file_path, message in self.warnings:
                lines.append(f"  - {file_path}: {message}")

        return "\n".join(lines) if lines else "No errors or warnings"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {"file": f, "operation": o, "message": str(e)}
                for f, o, e in self.errors
            ],
            "warnings": [
                {"file": f, "message": m}
                for f, m in self.warnings
            ]
        }
