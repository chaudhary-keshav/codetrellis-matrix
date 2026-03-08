"""
Spring Framework Event Extractor v1.0

Extracts Spring event publishing and listening patterns.

Part of CodeTrellis v4.94 - Spring Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringEventInfo:
    """An ApplicationEvent subclass."""
    name: str
    extends: str = "ApplicationEvent"
    fields: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringEventListenerInfo:
    """An @EventListener method."""
    method_name: str
    event_type: str = ""
    condition: str = ""
    is_async: bool = False
    is_transactional: bool = False
    phase: str = ""  # BEFORE_COMMIT, AFTER_COMMIT, AFTER_ROLLBACK, AFTER_COMPLETION
    target_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringEventPublisherInfo:
    """ApplicationEventPublisher usage."""
    publisher_field: str = ""
    published_events: List[str] = field(default_factory=list)
    target_class: str = ""
    file: str = ""
    line_number: int = 0


class SpringEventExtractor:
    """Extracts Spring event patterns."""

    EVENT_CLASS_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+(ApplicationEvent|AbstractApplicationEvent|\w*Event)',
        re.MULTILINE
    )

    EVENT_LISTENER_PATTERN = re.compile(
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'@(EventListener|TransactionalEventListener)'
        r'(?:\(\s*(?:condition\s*=\s*"([^"]*)")?\s*'
        r'(?:phase\s*=\s*TransactionPhase\.(\w+))?\s*\))?\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?(?:void\s+)?(\w+)\s*\(\s*([\w<>,?]+)',
        re.MULTILINE
    )

    PUBLISHER_PATTERN = re.compile(
        r'(?:private|protected)?\s*(?:final\s+)?ApplicationEventPublisher\s+(\w+)',
        re.MULTILINE
    )

    PUBLISH_EVENT_PATTERN = re.compile(
        r'(\w+)\.publishEvent\(\s*new\s+(\w+)',
        re.MULTILINE
    )

    ASYNC_PATTERN = re.compile(r'@Async\b')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring event patterns."""
        result: Dict[str, Any] = {
            'events': [],
            'listeners': [],
            'publishers': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Event classes
        for match in self.EVENT_CLASS_PATTERN.finditer(content):
            result['events'].append(SpringEventInfo(
                name=match.group(1),
                extends=match.group(2),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Event listeners
        for match in self.EVENT_LISTENER_PATTERN.finditer(content):
            preceding = match.group(1) or ""
            listener_type = match.group(2)
            condition = match.group(3) or ""
            phase = match.group(4) or ""
            method_name = match.group(5)
            event_type = match.group(6)

            is_async = bool(self.ASYNC_PATTERN.search(preceding))
            is_transactional = listener_type == 'TransactionalEventListener'

            result['listeners'].append(SpringEventListenerInfo(
                method_name=method_name,
                event_type=event_type,
                condition=condition,
                is_async=is_async,
                is_transactional=is_transactional,
                phase=phase,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Publishers
        for match in self.PUBLISHER_PATTERN.finditer(content):
            field_name = match.group(1)
            published = [m.group(2) for m in self.PUBLISH_EVENT_PATTERN.finditer(content)
                        if m.group(1) == field_name]
            result['publishers'].append(SpringEventPublisherInfo(
                publisher_field=field_name,
                published_events=published,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
