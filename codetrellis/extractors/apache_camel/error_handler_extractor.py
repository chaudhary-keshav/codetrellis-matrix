"""
Apache Camel Error Handler Extractor - Extracts error handling configuration.

Extracts:
- Error handler types (DefaultErrorHandler, DeadLetterChannel, NoErrorHandler)
- Exception clauses (onException)
- Retry policies (maximumRedeliveries, redeliveryDelay, backOffMultiplier)
- Dead letter channel configuration
- On completion handlers
- Transaction error handlers
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CamelErrorHandlerInfo:
    """Information about error handler configuration."""
    handler_type: str = ""  # default, deadLetterChannel, noErrorHandler, transactionErrorHandler
    dead_letter_uri: str = ""
    max_redeliveries: int = 0
    redelivery_delay: int = 0
    back_off_multiplier: float = 0.0
    retry_while: str = ""
    use_original_message: bool = False
    log_name: str = ""
    line_number: int = 0


@dataclass
class CamelExceptionClauseInfo:
    """Information about an onException clause."""
    exception_types: List[str] = field(default_factory=list)
    handled: bool = False
    continued: bool = False
    to_endpoint: str = ""
    max_redeliveries: int = 0
    redelivery_delay: int = 0
    retry_while: str = ""
    use_original_message: bool = False
    log_message: str = ""
    on_redelivery_processor: str = ""
    line_number: int = 0


class CamelErrorHandlerExtractor:
    """Extracts error handling configuration."""

    # Error handler definitions
    ERROR_HANDLER_PATTERN = re.compile(
        r'errorHandler\s*\(\s*'
        r'(?:deadLetterChannel\s*\(\s*["\']([^"\']+)["\']\)|'
        r'defaultErrorHandler\s*\(\s*\)|'
        r'noErrorHandler\s*\(\s*\)|'
        r'transactionErrorHandler\s*\(\s*\))',
        re.MULTILINE
    )

    # Dead letter channel
    DEAD_LETTER_PATTERN = re.compile(
        r'deadLetterChannel\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # onException clause
    ON_EXCEPTION_PATTERN = re.compile(
        r'onException\s*\(\s*([\w.,\s]+)\.class',
        re.DOTALL
    )

    # Handled
    HANDLED_PATTERN = re.compile(
        r'\.handled\s*\(\s*(true|false|constant\(["\']true["\']\))',
        re.MULTILINE
    )

    # Continued
    CONTINUED_PATTERN = re.compile(
        r'\.continued\s*\(\s*(true|false)',
        re.MULTILINE
    )

    # Maximum redeliveries
    MAX_REDELIVERIES_PATTERN = re.compile(
        r'\.maximumRedeliveries\s*\(\s*(\d+)',
        re.MULTILINE
    )

    # Redelivery delay
    REDELIVERY_DELAY_PATTERN = re.compile(
        r'\.redeliveryDelay\s*\(\s*(\d+)',
        re.MULTILINE
    )

    # Back off multiplier
    BACK_OFF_PATTERN = re.compile(
        r'\.backOffMultiplier\s*\(\s*(\d+\.?\d*)',
        re.MULTILINE
    )

    # Retry while
    RETRY_WHILE_PATTERN = re.compile(
        r'\.retryWhile\s*\(\s*(?:simple\(["\']([^"\']+)["\']\)|method\((\w+))',
        re.MULTILINE
    )

    # Use original message
    USE_ORIGINAL_PATTERN = re.compile(
        r'\.useOriginalMessage\s*\(',
        re.MULTILINE
    )

    # onException to endpoint
    EXCEPTION_TO_PATTERN = re.compile(
        r'onException.*?\.to\s*\(\s*["\']([^"\']+)["\']',
        re.DOTALL
    )

    # onCompletion
    ON_COMPLETION_PATTERN = re.compile(
        r'\.onCompletion\s*\(\s*\)',
        re.MULTILINE
    )

    ON_COMPLETION_ONLY_PATTERN = re.compile(
        r'\.onCompletionOnly\s*\(\s*\)',
        re.MULTILINE
    )

    ON_FAILURE_ONLY_PATTERN = re.compile(
        r'\.onFailureOnly\s*\(\s*\)',
        re.MULTILINE
    )

    # onRedelivery processor
    ON_REDELIVERY_PATTERN = re.compile(
        r'\.onRedelivery\s*\(\s*(?:new\s+)?(\w+)',
        re.MULTILINE
    )

    # Log exhausted message
    LOG_EXHAUSTED_PATTERN = re.compile(
        r'\.logExhausted(?:MessageHistory)?\s*\(\s*(true|false)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract error handling configuration."""
        error_handlers: List[CamelErrorHandlerInfo] = []
        exception_clauses: List[CamelExceptionClauseInfo] = []
        has_on_completion = False

        if not content or not content.strip():
            return {
                'error_handlers': error_handlers,
                'exception_clauses': exception_clauses,
                'has_on_completion': has_on_completion,
            }

        # Error handlers
        for match in self.ERROR_HANDLER_PATTERN.finditer(content):
            handler = CamelErrorHandlerInfo(
                line_number=content[:match.start()].count('\n') + 1,
            )
            full = match.group(0)
            if 'deadLetterChannel' in full:
                handler.handler_type = "deadLetterChannel"
                handler.dead_letter_uri = match.group(1) or ""
            elif 'noErrorHandler' in full:
                handler.handler_type = "noErrorHandler"
            elif 'transactionErrorHandler' in full:
                handler.handler_type = "transactionErrorHandler"
            else:
                handler.handler_type = "default"

            # Look for retry config after handler
            following = content[match.end():match.end() + 500]
            mr = self.MAX_REDELIVERIES_PATTERN.search(following)
            if mr:
                handler.max_redeliveries = int(mr.group(1))
            rd = self.REDELIVERY_DELAY_PATTERN.search(following)
            if rd:
                handler.redelivery_delay = int(rd.group(1))
            bo = self.BACK_OFF_PATTERN.search(following)
            if bo:
                handler.back_off_multiplier = float(bo.group(1))

            error_handlers.append(handler)

        # Dead letter channels (standalone)
        for match in self.DEAD_LETTER_PATTERN.finditer(content):
            if not any(eh.dead_letter_uri == match.group(1) for eh in error_handlers):
                handler = CamelErrorHandlerInfo(
                    handler_type="deadLetterChannel",
                    dead_letter_uri=match.group(1),
                    line_number=content[:match.start()].count('\n') + 1,
                )
                error_handlers.append(handler)

        # Exception clauses
        for match in self.ON_EXCEPTION_PATTERN.finditer(content):
            clause = CamelExceptionClauseInfo(
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Parse exception types
            exc_str = match.group(1)
            clause.exception_types = [e.strip() for e in exc_str.split(',') if e.strip()]

            # Look at following context for configuration
            following = content[match.end():match.end() + 800]

            handled = self.HANDLED_PATTERN.search(following)
            if handled:
                clause.handled = 'true' in handled.group(1)

            continued = self.CONTINUED_PATTERN.search(following)
            if continued:
                clause.continued = continued.group(1) == 'true'

            mr = self.MAX_REDELIVERIES_PATTERN.search(following)
            if mr:
                clause.max_redeliveries = int(mr.group(1))

            rd = self.REDELIVERY_DELAY_PATTERN.search(following)
            if rd:
                clause.redelivery_delay = int(rd.group(1))

            uo = self.USE_ORIGINAL_PATTERN.search(following)
            if uo:
                clause.use_original_message = True

            orr = self.ON_REDELIVERY_PATTERN.search(following)
            if orr:
                clause.on_redelivery_processor = orr.group(1)

            exception_clauses.append(clause)

        # onCompletion
        has_on_completion = bool(
            self.ON_COMPLETION_PATTERN.search(content) or
            self.ON_COMPLETION_ONLY_PATTERN.search(content) or
            self.ON_FAILURE_ONLY_PATTERN.search(content)
        )

        return {
            'error_handlers': error_handlers,
            'exception_clauses': exception_clauses,
            'has_on_completion': has_on_completion,
        }
