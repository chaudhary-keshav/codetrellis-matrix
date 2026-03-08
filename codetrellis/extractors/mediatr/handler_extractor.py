"""
MediatR Handler & Request Extractor.

Extracts requests, handlers, notifications, pipeline behaviors, and stream requests.

Supports MediatR 8.x through 12.x:
- IRequest<TResponse> / IRequest (void)
- IRequestHandler<TRequest, TResponse>
- INotification / INotificationHandler
- IPipelineBehavior<TRequest, TResponse>
- IStreamRequest<TResponse> / IStreamRequestHandler (MediatR 10+)
- ISender / IPublisher (MediatR 12+)

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MediatRRequestInfo:
    """Information about a MediatR request (command/query)."""
    name: str = ""
    response_type: str = ""     # TResponse or void
    kind: str = ""              # command, query (inferred from name/convention)
    properties: List[Dict[str, str]] = field(default_factory=list)
    is_record: bool = False
    validator: str = ""         # Associated FluentValidation validator
    file: str = ""
    line_number: int = 0


@dataclass
class MediatRHandlerInfo:
    """Information about a MediatR request handler."""
    name: str = ""
    request_type: str = ""
    response_type: str = ""
    is_async: bool = True
    file: str = ""
    line_number: int = 0


@dataclass
class MediatRNotificationInfo:
    """Information about a MediatR notification."""
    name: str = ""
    handlers: List[str] = field(default_factory=list)
    is_record: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MediatRBehaviorInfo:
    """Information about a MediatR pipeline behavior."""
    name: str = ""
    request_constraint: str = ""  # Generic constraint type
    purpose: str = ""             # validation, logging, transaction, caching, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class MediatRStreamRequestInfo:
    """Information about a MediatR stream request (MediatR 10+)."""
    name: str = ""
    response_type: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0


class MediatRHandlerExtractor:
    """Extracts MediatR requests, handlers, notifications, and behaviors."""

    # IRequest<T> / IRequest
    REQUEST_PATTERN = re.compile(
        r'(?:public\s+)?(?:record|class)\s+(\w+)\s*(?:\([^)]*\))?\s*:\s*IRequest\s*(?:<\s*(\w+(?:<[^>]+>)?)\s*>)?',
        re.MULTILINE
    )

    # IRequestHandler<TRequest, TResponse>
    HANDLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IRequestHandler\s*<\s*(\w+)\s*(?:,\s*(\w+(?:<[^>]+>)?)\s*)?>',
        re.MULTILINE
    )

    # INotification
    NOTIFICATION_PATTERN = re.compile(
        r'(?:public\s+)?(?:record|class)\s+(\w+)\s*(?:\([^)]*\))?\s*:\s*INotification\b',
        re.MULTILINE
    )

    # INotificationHandler<T>
    NOTIFICATION_HANDLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*INotificationHandler\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # IPipelineBehavior<TRequest, TResponse>
    BEHAVIOR_PATTERN = re.compile(
        r'class\s+(\w+)\s*(?:<[^>]+>)?\s*:\s*IPipelineBehavior\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # IStreamRequest<T> (MediatR 10+)
    STREAM_REQUEST_PATTERN = re.compile(
        r'(?:public\s+)?(?:record|class)\s+(\w+)\s*(?:\([^)]*\))?\s*:\s*IStreamRequest\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # IStreamRequestHandler<TRequest, TResponse>
    STREAM_HANDLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IStreamRequestHandler\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # ISender usage (MediatR 12+)
    SENDER_PATTERN = re.compile(r'ISender\s+\w+|IMediator\s+\w+', re.MULTILINE)

    # AbstractValidator<T> (FluentValidation integration)
    VALIDATOR_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*AbstractValidator\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Property in record/class
    PROPERTY_PATTERN = re.compile(
        r'public\s+(?:required\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\{[^}]*get',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract MediatR requests, handlers, notifications, and behaviors."""
        result = {
            'requests': [],
            'handlers': [],
            'notifications': [],
            'notification_handlers': [],
            'behaviors': [],
            'stream_requests': [],
            'validators': [],
        }

        if not content or not content.strip():
            return result

        # Requests
        for match in self.REQUEST_PATTERN.finditer(content):
            name = match.group(1)
            response = match.group(2) or "Unit"
            line = content[:match.start()].count('\n') + 1

            # Classify as command/query
            kind = "command"
            name_lower = name.lower()
            if 'query' in name_lower or 'get' in name_lower or 'list' in name_lower or 'find' in name_lower:
                kind = "query"

            is_record = 'record' in content[max(0, match.start() - 20):match.start() + 10]

            result['requests'].append(MediatRRequestInfo(
                name=name,
                response_type=response,
                kind=kind,
                is_record=is_record,
                file=file_path,
                line_number=line,
            ))

        # Handlers
        for match in self.HANDLER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['handlers'].append(MediatRHandlerInfo(
                name=match.group(1),
                request_type=match.group(2),
                response_type=match.group(3) or "Unit",
                file=file_path,
                line_number=line,
            ))

        # Notifications
        for match in self.NOTIFICATION_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            is_record = 'record' in content[max(0, match.start() - 20):match.start() + 10]
            result['notifications'].append(MediatRNotificationInfo(
                name=match.group(1),
                is_record=is_record,
                file=file_path,
                line_number=line,
            ))

        # Notification handlers
        for match in self.NOTIFICATION_HANDLER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['notification_handlers'].append({
                'handler': match.group(1),
                'notification': match.group(2),
                'file': file_path,
                'line': line,
            })

        # Pipeline behaviors
        for match in self.BEHAVIOR_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Infer purpose
            purpose = ""
            name_lower = name.lower()
            if 'validation' in name_lower or 'validator' in name_lower:
                purpose = "validation"
            elif 'log' in name_lower:
                purpose = "logging"
            elif 'transaction' in name_lower or 'uow' in name_lower:
                purpose = "transaction"
            elif 'cache' in name_lower:
                purpose = "caching"
            elif 'auth' in name_lower:
                purpose = "authorization"
            elif 'performance' in name_lower or 'timing' in name_lower:
                purpose = "performance"
            elif 'exception' in name_lower or 'error' in name_lower:
                purpose = "error_handling"

            result['behaviors'].append(MediatRBehaviorInfo(
                name=name,
                request_constraint=match.group(2),
                purpose=purpose,
                file=file_path,
                line_number=line,
            ))

        # Stream requests (MediatR 10+)
        for match in self.STREAM_REQUEST_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['stream_requests'].append(MediatRStreamRequestInfo(
                name=match.group(1),
                response_type=match.group(2),
                file=file_path,
                line_number=line,
            ))

        # Validators
        for match in self.VALIDATOR_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['validators'].append({
                'validator': match.group(1),
                'validated_type': match.group(2),
                'file': file_path,
                'line': line,
            })

        return result
