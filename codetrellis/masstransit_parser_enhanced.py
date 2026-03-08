"""
Enhanced MassTransit Parser for CodeTrellis.

Extracts MassTransit-specific concepts: consumers, sagas, message contracts,
bus configurations, middleware/filters, transport settings.

Supports MassTransit 7.x through 8.x.
Part of CodeTrellis v4.96 (Session 76)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetrellis.extractors.masstransit import MassTransitConsumerExtractor


@dataclass
class MassTransitParseResult:
    """Result of MassTransit-enhanced parsing."""
    # Consumers
    consumers: List[Dict[str, Any]] = field(default_factory=list)

    # Sagas
    sagas: List[Dict[str, Any]] = field(default_factory=list)

    # Messages
    messages: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    bus_configs: List[Dict[str, Any]] = field(default_factory=list)

    # Middleware
    middleware: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregates
    total_consumers: int = 0
    total_sagas: int = 0
    total_messages: int = 0

    # Framework metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_version: str = ""
    file_type: str = ""  # consumer, saga, message, configuration, filter


class EnhancedMassTransitParser:
    """Parser for MassTransit concepts in C# files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core
        'masstransit': r'using\s+MassTransit\b',
        'masstransit_definition': r'using\s+MassTransit\.Definition\b',
        'masstransit_saga': r'using\s+MassTransit\.Saga\b',
        'masstransit_courier': r'using\s+MassTransit\.Courier\b',
        'masstransit_mediator': r'using\s+MassTransit\.Mediator\b',
        'masstransit_monitoring': r'using\s+MassTransit\.Monitoring\b',

        # Transports
        'rabbitmq': r'\.UsingRabbitMq\s*\(',
        'azure_service_bus': r'\.UsingAzureServiceBus\s*\(',
        'amazon_sqs': r'\.UsingAmazonSqs\s*\(',
        'kafka': r'\.AddRider\s*\(|\.UsingKafka\b',
        'grpc': r'\.UsingGrpc\s*\(',

        # Patterns
        'consumer': r'\bIConsumer\s*<',
        'saga_state_machine': r'\bMassTransitStateMachine\s*<',
        'request_client': r'\bIRequestClient\s*<',
        'outbox': r'\.AddEntityFrameworkOutbox\b',
        'batch_consumer': r'\bIConsumer\s*<\s*Batch\s*<',

        # Configuration
        'add_masstransit': r'\.AddMassTransit\s*\(',
        'add_consumers': r'\.AddConsumers?\s*\(',
    }

    VERSION_FEATURES: Dict[str, List[str]] = {
        '7.0': ['IConsumer', 'MassTransitStateMachine', 'UsingRabbitMq', 'ConsumerDefinition'],
        '7.3': ['IConsumer', 'BatchConsumer', 'MessageScheduler'],
        '8.0': ['AddMassTransit', 'UsingRabbitMq', 'AddEntityFrameworkOutbox', 'AddConfigureEndpointsCallback'],
        '8.1': ['AddMassTransit', 'Mediator', 'JobConsumer'],
    }

    def __init__(self):
        """Initialize extractors."""
        self.consumer_extractor = MassTransitConsumerExtractor()

    def is_masstransit_file(self, content: str, file_path: str = "") -> bool:
        """Check if file contains MassTransit code."""
        if not content:
            return False
        indicators = [
            r'using\s+MassTransit\b',
            r'\bIConsumer\s*<',
            r'\bMassTransitStateMachine\s*<',
            r'\.AddMassTransit\s*\(',
            r'\.UsingRabbitMq\s*\(',
            r'\.UsingAzureServiceBus\s*\(',
            r'\bIRequestClient\s*<',
            r'\bSagaStateMachineInstance\b',
        ]
        return any(re.search(p, content) for p in indicators)

    def parse(self, content: str, file_path: str = "") -> MassTransitParseResult:
        """Parse MassTransit concepts from C# file."""
        result = MassTransitParseResult()

        if not content or not self.is_masstransit_file(content, file_path):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_version = self._detect_version(content)
        result.file_type = self._classify_file(content, file_path)

        # Extract
        data = self.consumer_extractor.extract(content, file_path)

        result.consumers = [self._consumer_to_dict(c) for c in data.get('consumers', [])]
        result.sagas = [self._saga_to_dict(s) for s in data.get('sagas', [])]
        result.messages = [self._message_to_dict(m) for m in data.get('messages', [])]
        result.bus_configs = [self._bus_to_dict(b) for b in data.get('bus_configs', [])]
        result.middleware = [self._mw_to_dict(m) for m in data.get('middleware', [])]

        # Aggregates
        result.total_consumers = len(result.consumers)
        result.total_sagas = len(result.sagas)
        result.total_messages = len(result.messages)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect MassTransit-related frameworks."""
        found = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if re.search(pattern, content):
                found.append(name)
        return found

    def _detect_version(self, content: str) -> str:
        """Detect MassTransit version from usage patterns."""
        if re.search(r'\.AddMassTransit\s*\(', content):
            if re.search(r'\.AddEntityFrameworkOutbox\b', content):
                return "8.0"
            return "8.0"
        return "7.0"

    def _classify_file(self, content: str, file_path: str) -> str:
        """Classify file type."""
        if re.search(r'\bIConsumer\s*<', content):
            return "consumer"
        if re.search(r'\bMassTransitStateMachine\s*<|SagaStateMachineInstance', content):
            return "saga"
        if re.search(r'Command\b|Event\b|Message\b', content) and re.search(r'(?:record|class)\s+\w+(?:Command|Event|Message)', content):
            return "message"
        if re.search(r'\.AddMassTransit\s*\(|\.UsingRabbitMq\s*\(', content):
            return "configuration"
        if re.search(r'I(?:Consume|Send|Publish)Filter', content):
            return "filter"
        return "usage"

    def _consumer_to_dict(self, c) -> Dict[str, Any]:
        return {
            'name': c.name, 'message_type': c.message_type,
            'consumer_type': c.consumer_type, 'has_definition': c.has_definition,
            'file': c.file, 'line': c.line_number,
        }

    def _saga_to_dict(self, s) -> Dict[str, Any]:
        return {
            'name': s.name, 'saga_type': s.saga_type, 'state_type': s.state_type,
            'events': s.events, 'states': s.states,
            'file': s.file, 'line': s.line_number,
        }

    def _message_to_dict(self, m) -> Dict[str, Any]:
        return {
            'name': m.name, 'message_kind': m.message_kind,
            'file': m.file, 'line': m.line_number,
        }

    def _bus_to_dict(self, b) -> Dict[str, Any]:
        return {
            'transport': b.transport, 'has_retry': b.has_retry,
            'has_circuit_breaker': b.has_circuit_breaker,
            'has_outbox': b.has_outbox,
            'file': b.file, 'line': b.line_number,
        }

    def _mw_to_dict(self, m) -> Dict[str, Any]:
        return {
            'name': m.name, 'filter_type': m.filter_type,
            'file': m.file, 'line': m.line_number,
        }
