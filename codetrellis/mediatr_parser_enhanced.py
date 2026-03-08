"""
EnhancedMediatRParser v1.0 - MediatR CQRS pattern parser.

Supports MediatR 8.x through 12.x.

Part of CodeTrellis v4.96 - .NET Framework Enhanced Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .extractors.mediatr import (
    MediatRHandlerExtractor,
    MediatRRequestInfo, MediatRHandlerInfo, MediatRNotificationInfo,
    MediatRBehaviorInfo, MediatRStreamRequestInfo,
)


@dataclass
class MediatRParseResult:
    """Complete parse result for a MediatR file."""
    file_path: str
    file_type: str = "unknown"  # request, handler, notification, behavior, validator

    requests: List[MediatRRequestInfo] = field(default_factory=list)
    handlers: List[MediatRHandlerInfo] = field(default_factory=list)
    notifications: List[MediatRNotificationInfo] = field(default_factory=list)
    notification_handlers: List[Dict] = field(default_factory=list)
    behaviors: List[MediatRBehaviorInfo] = field(default_factory=list)
    stream_requests: List[MediatRStreamRequestInfo] = field(default_factory=list)
    validators: List[Dict] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    mediatr_version: str = ""
    total_requests: int = 0
    total_handlers: int = 0
    total_notifications: int = 0
    has_validation_pipeline: bool = False
    has_cqrs_separation: bool = False  # Commands and queries in separate dirs


class EnhancedMediatRParser:
    """Enhanced per-file MediatR parser."""

    FRAMEWORK_PATTERNS = {
        'mediatr': re.compile(r'using\s+MediatR\b', re.MULTILINE),
        'mediatr-extensions': re.compile(r'using\s+MediatR\.Extensions\b', re.MULTILINE),
        'fluentvalidation': re.compile(r'using\s+FluentValidation\b', re.MULTILINE),
    }

    VERSION_FEATURES = {
        'IStreamRequest': '10.0',
        'IStreamRequestHandler': '10.0',
        'ISender': '12.0',
        'IPublisher': '12.0',
        'IPipelineBehavior': '8.0',
        'IRequestPreProcessor': '8.0',
        'IRequestPostProcessor': '8.0',
    }

    def __init__(self):
        self.handler_extractor = MediatRHandlerExtractor()

    def parse(self, content: str, file_path: str = "") -> MediatRParseResult:
        result = MediatRParseResult(file_path=file_path)
        if not content or not content.strip():
            return result

        result.file_type = self._classify_file(file_path, content)
        result.detected_frameworks = self._detect_frameworks(content)

        ext_result = self.handler_extractor.extract(content, file_path)
        result.requests = ext_result.get('requests', [])
        result.handlers = ext_result.get('handlers', [])
        result.notifications = ext_result.get('notifications', [])
        result.notification_handlers = ext_result.get('notification_handlers', [])
        result.behaviors = ext_result.get('behaviors', [])
        result.stream_requests = ext_result.get('stream_requests', [])
        result.validators = ext_result.get('validators', [])

        result.total_requests = len(result.requests)
        result.total_handlers = len(result.handlers)
        result.total_notifications = len(result.notifications)
        result.has_validation_pipeline = any(b.purpose == 'validation' for b in result.behaviors)

        # CQRS detection
        norm = file_path.replace('\\', '/').lower()
        if '/commands/' in norm or '/queries/' in norm:
            result.has_cqrs_separation = True

        result.mediatr_version = self._detect_version(content)
        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""
        if 'handler' in basename:
            return 'handler'
        if 'validator' in basename:
            return 'validator'
        if 'behavior' in basename or 'behaviour' in basename:
            return 'behavior'
        if 'notification' in basename or 'event' in basename:
            return 'notification'
        if 'command' in basename or 'query' in basename or 'request' in basename:
            return 'request'
        if 'IRequestHandler' in content or 'INotificationHandler' in content:
            return 'handler'
        if 'IRequest' in content or 'INotification' in content:
            return 'request'
        if 'IPipelineBehavior' in content:
            return 'behavior'
        return 'unknown'

    def _detect_frameworks(self, content: str) -> List[str]:
        return [fw for fw, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        max_v = '0.0'
        for feat, ver in self.VERSION_FEATURES.items():
            if feat in content:
                parts_f = [int(x) for x in ver.split('.')]
                parts_m = [int(x) for x in max_v.split('.')]
                if parts_f > parts_m:
                    max_v = ver
        return max_v if max_v != '0.0' else ''

    def is_mediatr_file(self, content: str, file_path: str = "") -> bool:
        if re.search(r'using\s+MediatR\b', content):
            return True
        mediatr_types = ['IRequest', 'IRequestHandler', 'INotification', 'INotificationHandler',
                         'IPipelineBehavior', 'IMediator', 'ISender', 'IStreamRequest']
        return any(t in content for t in mediatr_types)
