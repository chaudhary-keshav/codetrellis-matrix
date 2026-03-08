"""
MassTransit Consumer/Saga Extractor.

Extracts consumers, sagas, message contracts, bus configurations,
middleware/filters, and transport settings.

Supports MassTransit 7.x through 8.x.
Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MassTransitConsumerInfo:
    """Information about a MassTransit consumer."""
    name: str = ""
    message_type: str = ""
    consumer_type: str = ""  # consumer, consumer-definition, batch-consumer
    has_definition: bool = False
    retry_policy: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class MassTransitSagaInfo:
    """Information about a MassTransit saga."""
    name: str = ""
    saga_type: str = ""  # state-machine, consumer-saga, saga-definition
    state_type: str = ""
    events: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)
    correlation_id_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class MassTransitMessageInfo:
    """Information about a message contract."""
    name: str = ""
    message_kind: str = ""  # command, event, request, response
    namespace: str = ""
    properties: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MassTransitBusConfigInfo:
    """Bus configuration information."""
    transport: str = ""  # rabbitmq, azure-service-bus, amazon-sqs, in-memory, kafka, grpc
    has_retry: bool = False
    has_circuit_breaker: bool = False
    has_rate_limiter: bool = False
    has_outbox: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class MassTransitMiddlewareInfo:
    """Middleware/filter information."""
    name: str = ""
    filter_type: str = ""  # consume, send, publish, execute
    file: str = ""
    line_number: int = 0


class MassTransitConsumerExtractor:
    """Extracts MassTransit consumers, sagas, and configurations."""

    # IConsumer<TMessage>
    CONSUMER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IConsumer\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # IConsumerDefinition<TConsumer>
    CONSUMER_DEFINITION_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*ConsumerDefinition\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Batch consumer IConsumer<Batch<TMessage>>
    BATCH_CONSUMER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IConsumer\s*<\s*Batch\s*<\s*(\w+)\s*>\s*>',
        re.MULTILINE
    )

    # MassTransitStateMachine<TState>
    STATE_MACHINE_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*MassTransitStateMachine\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # ISaga, ISagaVersion
    SAGA_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*(SagaStateMachineInstance|ISaga|ISagaVersion)\b',
        re.MULTILINE
    )

    # Event<T> declaration in state machine
    EVENT_PATTERN = re.compile(
        r'Event\s*<\s*(\w+)\s*>\s+(\w+)\s*{',
        re.MULTILINE
    )

    # State declaration
    STATE_PATTERN = re.compile(
        r'State\s+(\w+)\s*{',
        re.MULTILINE
    )

    # Transport patterns
    TRANSPORT_PATTERNS = {
        'rabbitmq': re.compile(r'\.UsingRabbitMq\s*\(', re.MULTILINE),
        'azure-service-bus': re.compile(r'\.UsingAzureServiceBus\s*\(', re.MULTILINE),
        'amazon-sqs': re.compile(r'\.UsingAmazonSqs\s*\(', re.MULTILINE),
        'in-memory': re.compile(r'\.UsingInMemory\s*\(', re.MULTILINE),
        'kafka': re.compile(r'\.UsingKafka\s*\(|\.AddRider\s*\(', re.MULTILINE),
        'grpc': re.compile(r'\.UsingGrpc\s*\(', re.MULTILINE),
    }

    # Retry config
    RETRY_PATTERN = re.compile(
        r'\.UseMessageRetry\s*\(\s*r\s*=>\s*r\.(\w+)',
        re.MULTILINE
    )

    # Circuit breaker
    CIRCUIT_BREAKER_PATTERN = re.compile(
        r'\.UseCircuitBreaker\s*\(',
        re.MULTILINE
    )

    # Rate limiter
    RATE_LIMITER_PATTERN = re.compile(
        r'\.UseRateLimit\w*\s*\(',
        re.MULTILINE
    )

    # Outbox
    OUTBOX_PATTERN = re.compile(
        r'\.AddEntityFrameworkOutbox\s*<|\.UseInMemoryOutbox\s*\(',
        re.MULTILINE
    )

    # Middleware / filters
    FILTER_PATTERN = re.compile(
        r'class\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*I(Consume|Send|Publish|Execute)Filter\b',
        re.MULTILINE
    )

    # AddMassTransit
    ADD_MASSTRANSIT_PATTERN = re.compile(
        r'\.AddMassTransit\s*\(',
        re.MULTILINE
    )

    # Message contract interface pattern
    MESSAGE_INTERFACE_PATTERN = re.compile(
        r'(?:public\s+)?interface\s+(\w+)\s*(?::\s*(?:CorrelatedBy<[^>]*>))?\s*\{([^}]*)\}',
        re.DOTALL | re.MULTILINE
    )

    # Message record/class (command/event naming)
    MESSAGE_CLASS_PATTERN = re.compile(
        r'(?:public\s+)?(?:record|class)\s+(\w+(?:Command|Event|Request|Response|Message))\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract MassTransit consumers, sagas, and configurations."""
        result: Dict[str, Any] = {
            'consumers': [],
            'sagas': [],
            'messages': [],
            'bus_configs': [],
            'middleware': [],
        }

        if not content or not content.strip():
            return result

        # Batch consumers (before regular to avoid double counting)
        batch_names = set()
        for match in self.BATCH_CONSUMER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            batch_names.add(match.group(1))
            result['consumers'].append(MassTransitConsumerInfo(
                name=match.group(1),
                message_type=match.group(2),
                consumer_type="batch-consumer",
                file=file_path,
                line_number=line,
            ))

        # Regular consumers
        for match in self.CONSUMER_PATTERN.finditer(content):
            if match.group(1) in batch_names:
                continue
            line = content[:match.start()].count('\n') + 1
            result['consumers'].append(MassTransitConsumerInfo(
                name=match.group(1),
                message_type=match.group(2),
                consumer_type="consumer",
                file=file_path,
                line_number=line,
            ))

        # Consumer definitions
        for match in self.CONSUMER_DEFINITION_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['consumers'].append(MassTransitConsumerInfo(
                name=match.group(1),
                message_type=match.group(2),
                consumer_type="consumer-definition",
                has_definition=True,
                file=file_path,
                line_number=line,
            ))

        # State machines
        for match in self.STATE_MACHINE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            events = [e.group(2) for e in self.EVENT_PATTERN.finditer(content)]
            states = [s.group(1) for s in self.STATE_PATTERN.finditer(content)]
            result['sagas'].append(MassTransitSagaInfo(
                name=match.group(1),
                saga_type="state-machine",
                state_type=match.group(2),
                events=events[:20],
                states=states[:20],
                file=file_path,
                line_number=line,
            ))

        # Simple sagas
        for match in self.SAGA_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['sagas'].append(MassTransitSagaInfo(
                name=match.group(1),
                saga_type="consumer-saga" if match.group(2) == "ISaga" else "saga-instance",
                file=file_path,
                line_number=line,
            ))

        # Message contracts
        for match in self.MESSAGE_CLASS_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            kind = "command"
            if 'Event' in name:
                kind = "event"
            elif 'Request' in name:
                kind = "request"
            elif 'Response' in name:
                kind = "response"
            result['messages'].append(MassTransitMessageInfo(
                name=name,
                message_kind=kind,
                file=file_path,
                line_number=line,
            ))

        # Bus configuration
        for transport, pattern in self.TRANSPORT_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line = content[:match.start()].count('\n') + 1
                has_retry = bool(self.RETRY_PATTERN.search(content))
                has_cb = bool(self.CIRCUIT_BREAKER_PATTERN.search(content))
                has_rl = bool(self.RATE_LIMITER_PATTERN.search(content))
                has_outbox = bool(self.OUTBOX_PATTERN.search(content))
                result['bus_configs'].append(MassTransitBusConfigInfo(
                    transport=transport,
                    has_retry=has_retry,
                    has_circuit_breaker=has_cb,
                    has_rate_limiter=has_rl,
                    has_outbox=has_outbox,
                    file=file_path,
                    line_number=line,
                ))

        # Middleware/filters
        for match in self.FILTER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['middleware'].append(MassTransitMiddlewareInfo(
                name=match.group(1),
                filter_type=match.group(2).lower(),
                file=file_path,
                line_number=line,
            ))

        return result
